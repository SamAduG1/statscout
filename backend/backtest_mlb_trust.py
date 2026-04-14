"""
MLB Trust Score Backtest
========================
For every player-game in the DB, computes a retroactive trust score using
only games BEFORE that date, then checks whether the actual game hit the line.

Groups predictions into trust buckets and reports:
  1. Calibration  - does trust 70 actually predict a 70% hit rate?
  2. Discrimination - do high-trust picks outperform low-trust picks?
  3. Factor analysis - how much does each factor add over raw hit rate?
  4. Per-market breakdown

Usage:
  cd backend
  python backtest_mlb_trust.py              # all markets, all seasons
  python backtest_mlb_trust.py --season 2025
  python backtest_mlb_trust.py --market hits --line 0.5
  python backtest_mlb_trust.py --min-prior 20  # require 20 prior games
"""

import argparse
import math
from collections import defaultdict

from dotenv import load_dotenv
load_dotenv()

from models import get_engine, get_session, MLBPlayer, MLBPlayerGame

# ---------------------------------------------------------------------------
# Park factor table (mirrors frontend getMlbParkInfo, batter-run modifier)
# Positive = hitter-friendly, negative = pitcher-friendly
# ---------------------------------------------------------------------------
PARK_FACTORS = {
    # Team abbr: hits modifier (roughly half the HR modifier)
    "COL": 8,   # Coors - massive
    "BOS": 4,   # Fenway
    "CIN": 3,
    "TEX": 3,
    "MIL": 2,
    "PHI": 2,
    "CHC": 1,
    "HOU": 1,
    "LAD": -1,
    "OAK": -2,
    "SAC": -2,  # Athletics (Sacramento)
    "SF":  -2,  # Oracle
    "NYM": -2,
    "MIA": -3,
    "SEA": -3,
    "CLE": -3,
}

TEAM_TO_ABBR = {
    "Colorado Rockies": "COL",
    "Boston Red Sox": "BOS",
    "Cincinnati Reds": "CIN",
    "Texas Rangers": "TEX",
    "Milwaukee Brewers": "MIL",
    "Philadelphia Phillies": "PHI",
    "Chicago Cubs": "CHC",
    "Houston Astros": "HOU",
    "Los Angeles Dodgers": "LAD",
    "Oakland Athletics": "OAK",
    "Sacramento Athletics": "SAC",
    "San Francisco Giants": "SF",
    "New York Mets": "NYM",
    "Miami Marlins": "MIA",
    "Seattle Mariners": "SEA",
    "Cleveland Guardians": "CLE",
}

MARKETS = {
    # key: (column_attr, lines_to_test, player_type)
    "hits":        ("hits",        [0.5, 1.5],       "batter"),
    "home_runs":   ("home_runs",   [0.5],             "batter"),
    "total_bases": ("total_bases", [1.5, 2.5],        "batter"),
    "rbi":         ("rbi",         [0.5],             "batter"),
    "runs":        ("runs",        [0.5],             "batter"),
    "strikeouts":  ("strikeouts",  [3.5, 4.5, 5.5],  "pitcher"),
}

# ---------------------------------------------------------------------------
# Trust score computation (mirrors frontend logic)
# ---------------------------------------------------------------------------

def compute_trust(prior_vals, line, is_home=None, game_is_home=None,
                  team_name=None, use_park=True, use_splits=True):
    """
    Compute a trust score from prior game values.
    Returns (trust_score, hit_rate_pct) or (None, None) if too few games.
    """
    vals = [v for v in prior_vals if v is not None]
    if len(vals) < 5:
        return None, None

    hr = sum(1 for v in vals if v > line) / len(vals)
    score = math.pow(hr, 1.5) * 100

    # Consistency (low variance = more predictable)
    mean = sum(vals) / len(vals)
    std  = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
    cv   = std / mean if mean > 0 else 2.0
    score += max(0, 1 - min(cv, 2) / 2) * 10

    # Recent form (last 5 games vs overall)
    last5     = vals[-5:]
    recent_hr = sum(1 for v in last5 if v > line) / len(last5)
    score    += max(-8, min(8, (recent_hr - hr) * 20))

    # Sample size confidence
    score += min(8, len(vals) / 10)

    # Park factor
    if use_park and team_name:
        abbr = TEAM_TO_ABBR.get(team_name)
        park_mod = PARK_FACTORS.get(abbr, 0)
        score += park_mod

    # Home/away split — compare home-specific vs overall hit rate
    if use_splits and is_home is not None and game_is_home is not None:
        venue_vals = [v for v, h in zip(prior_vals, is_home)
                      if v is not None and h == game_is_home]
        if len(venue_vals) >= 5:
            venue_hr   = sum(1 for v in venue_vals if v > line) / len(venue_vals)
            split_mod  = max(-6, min(6, (venue_hr - hr) * 15))
            score     += split_mod

    return round(min(max(score, 0), 100)), round(hr * 100, 1)


def bucket(trust):
    if trust < 30: return "00-29"
    if trust < 40: return "30-39"
    if trust < 50: return "40-49"
    if trust < 60: return "50-59"
    if trust < 70: return "60-69"
    if trust < 80: return "70-79"
    if trust < 90: return "80-89"
    return "90-99"


# ---------------------------------------------------------------------------
# Brier score and log-loss helpers (lower = better)
# ---------------------------------------------------------------------------

def brier_score(predictions, actuals):
    if not predictions:
        return None
    return sum((p/100 - a) ** 2 for p, a in zip(predictions, actuals)) / len(predictions)


def log_loss(predictions, actuals):
    if not predictions:
        return None
    eps = 1e-7
    return -sum(
        a * math.log(max(p/100, eps)) + (1-a) * math.log(max(1-p/100, eps))
        for p, a in zip(predictions, actuals)
    ) / len(predictions)


# ---------------------------------------------------------------------------
# Main backtest
# ---------------------------------------------------------------------------

def run_backtest(session, market_key, line, season_filter=None, min_prior=15):
    col_name, _, player_type = MARKETS[market_key]
    is_pitcher = (player_type == "pitcher")

    players = session.query(MLBPlayer).filter_by(is_pitcher=is_pitcher).all()

    # Results keyed by (model_name, bucket)
    models = ["base_only", "base+splits", "base+park+splits"]
    results = {m: defaultdict(lambda: {"trust_scores": [], "actuals": []}) for m in models}
    total_games = 0

    for player in players:
        query = session.query(MLBPlayerGame).filter_by(player_id=player.id)
        if season_filter:
            query = query.filter(MLBPlayerGame.season == season_filter)
        games = query.order_by(MLBPlayerGame.game_date.asc()).all()

        if len(games) < min_prior + 1:
            continue

        for i in range(min_prior, len(games)):
            prior_games = games[:i]
            current     = games[i]

            actual_val = getattr(current, col_name)
            if actual_val is None:
                continue

            actual_hit = 1 if actual_val > line else 0
            prior_vals = [getattr(g, col_name) for g in prior_games]
            prior_home = [g.is_home for g in prior_games]

            # Model A: base only (no park, no splits)
            t_base, _ = compute_trust(prior_vals, line,
                                      use_park=False, use_splits=False)

            # Model B: base + home/away splits
            t_splits, _ = compute_trust(prior_vals, line,
                                        is_home=prior_home,
                                        game_is_home=current.is_home,
                                        use_park=False, use_splits=True)

            # Model C: base + splits + park factor
            t_full, _ = compute_trust(prior_vals, line,
                                      is_home=prior_home,
                                      game_is_home=current.is_home,
                                      team_name=player.team,
                                      use_park=True, use_splits=True)

            for model, trust in [("base_only", t_base),
                                  ("base+splits", t_splits),
                                  ("base+park+splits", t_full)]:
                if trust is None:
                    continue
                b = bucket(trust)
                results[model][b]["trust_scores"].append(trust)
                results[model][b]["actuals"].append(actual_hit)

            total_games += 1

    return results, total_games


def print_calibration_table(results, market_key, line, total_games):
    buckets = ["00-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-99"]
    models  = ["base_only", "base+splits", "base+park+splits"]

    print(f"\n{'='*80}")
    print(f"  Market: {market_key} > {line}    ({total_games:,} total game-predictions)")
    print(f"{'='*80}")

    for model in models:
        data = results[model]
        all_trust   = [t for b in buckets for t in data[b]["trust_scores"]]
        all_actuals = [a for b in buckets for a in data[b]["actuals"]]

        bs  = brier_score(all_trust, all_actuals)
        ll  = log_loss(all_trust, all_actuals)
        overall_hit = sum(all_actuals) / len(all_actuals) * 100 if all_actuals else 0

        print(f"\n  Model: {model:<25}  Brier={bs:.4f}  LogLoss={ll:.4f}  "
              f"Overall actual hit rate: {overall_hit:.1f}%")
        print(f"  {'Bucket':<10} {'N':>6} {'Avg Trust':>10} {'Actual %':>10} {'Diff':>8} {'Signal'}")
        print(f"  {'-'*58}")

        for b in buckets:
            bd = data[b]
            n  = len(bd["actuals"])
            if n < 10:
                continue
            avg_trust   = sum(bd["trust_scores"]) / n
            actual_rate = sum(bd["actuals"]) / n * 100
            diff        = actual_rate - avg_trust
            signal      = ("OVER  " if diff >  5 else
                           "UNDER " if diff < -5 else
                           "OK    ")
            print(f"  {b:<10} {n:>6,} {avg_trust:>10.1f} {actual_rate:>10.1f} "
                  f"{diff:>+8.1f} {signal}")

    # Discrimination: does higher trust = higher actual hit rate?
    print(f"\n  -- Discrimination (base+park+splits) --")
    data = results["base+park+splits"]
    prev_actual = None
    monotone = True
    for b in buckets:
        n = len(data[b]["actuals"])
        if n < 10:
            continue
        ar = sum(data[b]["actuals"]) / n * 100
        if prev_actual is not None and ar < prev_actual - 2:
            monotone = False
        prev_actual = ar

    print(f"  Higher trust -> higher actual rate? {'YES' if monotone else 'NOT MONOTONE - weights need adjustment'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--market",  choices=list(MARKETS.keys()), default=None,
                        help="Single market to test (default: all)")
    parser.add_argument("--line",    type=float, default=None,
                        help="Override line for market")
    parser.add_argument("--season",  default=None,
                        help="Filter to one season e.g. 2025")
    parser.add_argument("--min-prior", type=int, default=15,
                        help="Minimum prior games required to include a prediction (default 15)")
    args = parser.parse_args()

    engine  = get_engine()
    session = get_session(engine)

    try:
        markets_to_test = (
            [(args.market, [args.line] if args.line else MARKETS[args.market][1])]
            if args.market
            else [(k, MARKETS[k][1]) for k in MARKETS]
        )

        for market_key, lines in markets_to_test:
            for line in lines:
                results, total = run_backtest(
                    session, market_key, line,
                    season_filter=args.season,
                    min_prior=args.min_prior,
                )
                print_calibration_table(results, market_key, line, total)

        print("\n\nDONE. Key:")
        print("  Brier score: lower = better (perfect = 0, random = 0.25)")
        print("  LogLoss:     lower = better")
        print("  Diff:        Actual% - Avg Trust%. Positive = trust underestimates real rate.")
        print("  Signal OK:   within ±5 pts. OVER/UNDER = miscalibrated bucket.")
        print("  Discrimination: if higher trust buckets don't have higher actual rates,")
        print("                  the trust score isn't adding value over random.")

    finally:
        session.close()


if __name__ == "__main__":
    main()
