"""
MLB Trust Score Backtest v2 - with Statcast modifiers + cross-season validation
================================================================================
Two modes:

  Within-season (default):
    For each player-game in a single season, predict using only games before
    that date. Tests the formula on the same season it was trained on.

  Cross-season (--cross-season):
    Use ALL 2025 games as prior history, predict each 2026 game.
    This mirrors how the site actually works early in the 2026 season -
    the realistic production scenario.

Optionally fetches Statcast data (barrel%, hard-hit%, K%, BABIP) from
Baseball Savant + MLB Stats API to test the new modifiers' weight calibration.

Usage:
  cd backend
  python backtest_mlb_trust_v2.py                          # within-season, all markets
  python backtest_mlb_trust_v2.py --cross-season           # 2025 prior -> 2026 outcomes
  python backtest_mlb_trust_v2.py --market hits --sweep    # sweep BABIP/hard-hit multipliers
  python backtest_mlb_trust_v2.py --statcast               # fetch Statcast (adds ~30s)
  python backtest_mlb_trust_v2.py --season 2025 --market home_runs

Output:
  - Calibration table (trust bucket vs actual hit rate)
  - Brier score and log-loss per model
  - Discrimination test (monotone ordering)
  - Factor analysis (incremental gain from each new modifier)
"""

import argparse
import io
import csv
import math
import time
from collections import defaultdict

import requests
from dotenv import load_dotenv
load_dotenv()

from models import get_engine, get_session, MLBPlayer, MLBPlayerGame

MLB_STATS_BASE = "https://statsapi.mlb.com/api/v1"
SAVANT_CSV_URL = (
    "https://baseballsavant.mlb.com/leaderboard/statcast"
    "?type=batter&year={year}&position=&team=&min=10&csv=true"
)

MARKETS = {
    # key: (column_attr, lines_to_test, player_type)
    "hits":        ("hits",        [0.5, 1.5],      "batter"),
    "home_runs":   ("home_runs",   [0.5],            "batter"),
    "total_bases": ("total_bases", [1.5, 2.5],       "batter"),
    "rbi":         ("rbi",         [0.5],            "batter"),
    "runs":        ("runs",        [0.5],            "batter"),
    "strikeouts":  ("strikeouts",  [3.5, 4.5, 5.5], "pitcher"),
}

# ---------------------------------------------------------------------------
# Trust modifiers (mirrors frontend formula exactly)
# ---------------------------------------------------------------------------

def compute_base_trust(vals, line):
    """Core: hr^1.5 * 100 + consistency + recent form + sample size. Returns None if < 5 games."""
    vals = [v for v in vals if v is not None]
    if len(vals) < 5:
        return None, None

    hr = sum(1 for v in vals if v > line) / len(vals)
    score = math.pow(hr, 1.5) * 100

    # Consistency (CV-based, max +5 pts after backtest softening)
    mean = sum(vals) / len(vals)
    std  = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
    cv   = std / mean if mean > 0 else 2.0
    score += max(0, 1 - min(cv, 2) / 2) * 5

    # Recent form vs overall (max +-5 pts after backtest softening)
    last5     = vals[-5:]
    recent_hr = sum(1 for v in last5 if v > line) / len(last5)
    score    += max(-5, min(5, (recent_hr - hr) * 20))

    # Sample size (max +8 pts)
    n = len(vals)
    sample_bonus = 8 if n >= 20 else (5 if n >= 10 else 2)
    score += sample_bonus

    return round(min(max(score, 0), 100)), round(hr * 100, 1)


def get_era_mod(era):
    """Pitcher ERA vs starter → +-6 pts."""
    if era is None:
        return 0
    return max(-6, min(6, (era - 4.20) * 2.5))


def get_opp_team_era_mod(opp_team_era):
    """Batter: opp team ERA vs league avg → +-7 pts."""
    if opp_team_era is None:
        return 0
    return max(-7, min(7, (opp_team_era - 4.15) * 3.5))


def get_kpct_mod(kpct, market):
    """Batter K% vs league avg (~22%): higher K% = less consistent hitter → +-5 pts."""
    if kpct is None or market == 'hr':
        return 0
    return max(-5, min(5, (22 - kpct) * 0.25))


def get_babip_mod(babip, market, multiplier=-20):
    """BABIP regression: high BABIP above .300 suggests coming down. Hits market only."""
    if babip is None or market != 'hits':
        return 0
    return max(-4, min(4, (babip - 0.300) * multiplier))


def get_barrel_mod(barrel_pct, market, multiplier=0.6):
    """Barrel rate: HR power signal. HR and TB markets only."""
    if barrel_pct is None or market not in ('hr', 'tb'):
        return 0
    return max(-6, min(6, (barrel_pct - 7) * multiplier))


def get_hard_hit_mod(hard_hit_pct, market, multiplier=0.2):
    """Hard-hit rate: consistent contact quality. Not used for RBI/Runs."""
    if hard_hit_pct is None or market in ('rbi', 'runs'):
        return 0
    return max(-4, min(4, (hard_hit_pct - 38) * multiplier))


# ---------------------------------------------------------------------------
# Statcast data fetching
# ---------------------------------------------------------------------------

def fetch_savant_statcast(year):
    """Fetch barrel%, hard-hit% from Baseball Savant bulk CSV. Returns {player_id: dict}."""
    url = SAVANT_CSV_URL.format(year=year)
    print(f"  [Savant] Fetching {year} Statcast data...", flush=True)
    try:
        r = requests.get(url, timeout=60, headers={"User-Agent": "StatScout/1.0"})
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        result = {}
        for row in reader:
            pid_str = row.get("player_id", "").strip()
            if not pid_str:
                continue
            try:
                pid = int(pid_str)
            except ValueError:
                continue
            try:
                barrel = float(row.get("barrel_batted_rate", "") or 0)
                hard_hit = float(row.get("hard_hit_percent", "") or 0)
            except (ValueError, TypeError):
                continue
            result[pid] = {"barrelPct": barrel, "hardHitPct": hard_hit}
        print(f"  [Savant] {len(result)} batter records loaded")
        return result
    except Exception as e:
        print(f"  [Savant] Failed: {e}")
        return {}


def fetch_advanced_stats(player_ids, year):
    """Fetch K%, BABIP from MLB Stats API in batches of 100. Returns {player_id: dict}."""
    print(f"  [MLB API] Fetching {year} K%/BABIP for {len(player_ids)} players...", flush=True)
    result = {}
    batch_size = 100
    ids_list = list(player_ids)
    for i in range(0, len(ids_list), batch_size):
        batch = ids_list[i:i + batch_size]
        try:
            r = requests.get(
                f"{MLB_STATS_BASE}/people",
                params={
                    "personIds": ",".join(str(x) for x in batch),
                    "hydrate": f"stats(group=hitting,type=season,season={year})",
                },
                timeout=30,
            )
            r.raise_for_status()
            for p in r.json().get("people", []):
                pid = p.get("id")
                stats_groups = p.get("stats", [])
                if not stats_groups:
                    continue
                for sg in stats_groups:
                    splits = sg.get("splits", [])
                    if not splits:
                        continue
                    stat = splits[0].get("stat", {})
                    try:
                        pas   = float(stat.get("plateAppearances") or 0)
                        ks    = float(stat.get("strikeOuts") or 0)
                        babip = stat.get("babip")
                        entry = {}
                        if pas > 0:
                            entry["kPct"] = round(ks / pas * 100, 1)
                        if babip is not None:
                            entry["babip"] = round(float(babip), 3)
                        if entry:
                            result[pid] = entry
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            print(f"  [MLB API] Batch {i}: {e}")
        time.sleep(0.2)
    print(f"  [MLB API] {len(result)} players with K%/BABIP")
    return result


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

def build_models(statcast_by_pid, adv_by_pid, babip_mult, barrel_mult, hard_hit_mult):
    """
    Returns ordered list of (model_name, compute_fn) where compute_fn(prior_vals, line,
    player_id, market) -> trust_score_or_None.
    """

    def model_base(prior_vals, line, pid, market):
        score, _ = compute_base_trust(prior_vals, line)
        return score

    def model_base_statcast(prior_vals, line, pid, market):
        score, _ = compute_base_trust(prior_vals, line)
        if score is None:
            return None
        sc = statcast_by_pid.get(pid, {})
        adv = adv_by_pid.get(pid, {})
        score += get_kpct_mod(adv.get("kPct"), market)
        score += get_babip_mod(adv.get("babip"), market, babip_mult)
        score += get_barrel_mod(sc.get("barrelPct"), market, barrel_mult)
        score += get_hard_hit_mod(sc.get("hardHitPct"), market, hard_hit_mult)
        return round(min(max(score, 0), 100))

    models = [("base", model_base)]
    if statcast_by_pid or adv_by_pid:
        models.append((
            f"base+statcast(babip={babip_mult},barrel={barrel_mult},hh={hard_hit_mult})",
            model_base_statcast,
        ))
    return models


# ---------------------------------------------------------------------------
# Backtest runners
# ---------------------------------------------------------------------------

def bucket(trust):
    if trust < 30: return "00-29"
    if trust < 40: return "30-39"
    if trust < 50: return "40-49"
    if trust < 60: return "50-59"
    if trust < 70: return "60-69"
    if trust < 80: return "70-79"
    if trust < 90: return "80-89"
    return "90-99"


def brier_score(predictions, actuals):
    if not predictions:
        return None
    return sum((p / 100 - a) ** 2 for p, a in zip(predictions, actuals)) / len(predictions)


def log_loss(predictions, actuals):
    if not predictions:
        return None
    eps = 1e-7
    return -sum(
        a * math.log(max(p / 100, eps)) + (1 - a) * math.log(max(1 - p / 100, eps))
        for p, a in zip(predictions, actuals)
    ) / len(predictions)


def run_within_season(session, market_key, line, season_filter, min_prior,
                      model_fns, is_pitcher):
    """Standard within-season backtest: predict game N from games 0..N-1."""
    col, _, _ = MARKETS[market_key]
    players = session.query(MLBPlayer).filter_by(is_pitcher=is_pitcher).all()
    results = {m: defaultdict(lambda: {"trust_scores": [], "actuals": []})
               for m, _ in model_fns}
    total_games = 0

    for player in players:
        q = session.query(MLBPlayerGame).filter_by(player_id=player.id)
        if season_filter:
            q = q.filter(MLBPlayerGame.season == season_filter)
        games = q.order_by(MLBPlayerGame.game_date.asc()).all()
        if len(games) < min_prior + 1:
            continue

        for i in range(min_prior, len(games)):
            prior_vals = [getattr(g, col) for g in games[:i]]
            actual_val = getattr(games[i], col)
            if actual_val is None:
                continue
            actual_hit = 1 if actual_val > line else 0
            total_games += 1

            for model_name, compute_fn in model_fns:
                t = compute_fn(prior_vals, line, player.id, market_key)
                if t is not None:
                    results[model_name][bucket(t)]["trust_scores"].append(t)
                    results[model_name][bucket(t)]["actuals"].append(actual_hit)

    return results, total_games


def run_cross_season(session, market_key, line, prior_season, pred_season,
                     min_prior, model_fns, is_pitcher):
    """
    Cross-season: use all prior_season games as prior history, predict pred_season games.
    Simulates using 2025 history to predict 2026 outcomes.
    """
    col, _, _ = MARKETS[market_key]
    players = session.query(MLBPlayer).filter_by(is_pitcher=is_pitcher).all()
    results = {m: defaultdict(lambda: {"trust_scores": [], "actuals": []})
               for m, _ in model_fns}
    total_games = 0
    players_used = 0

    for player in players:
        prior_games = (
            session.query(MLBPlayerGame)
            .filter_by(player_id=player.id, season=str(prior_season))
            .order_by(MLBPlayerGame.game_date.asc())
            .all()
        )
        pred_games = (
            session.query(MLBPlayerGame)
            .filter_by(player_id=player.id, season=str(pred_season))
            .order_by(MLBPlayerGame.game_date.asc())
            .all()
        )

        if len(prior_games) < min_prior or not pred_games:
            continue

        prior_vals = [getattr(g, col) for g in prior_games]
        players_used += 1

        for pg in pred_games:
            actual_val = getattr(pg, col)
            if actual_val is None:
                continue
            actual_hit = 1 if actual_val > line else 0
            total_games += 1

            for model_name, compute_fn in model_fns:
                t = compute_fn(prior_vals, line, player.id, market_key)
                if t is not None:
                    results[model_name][bucket(t)]["trust_scores"].append(t)
                    results[model_name][bucket(t)]["actuals"].append(actual_hit)

    print(f"  [Cross-season {prior_season}->{pred_season}] {players_used} players, "
          f"{total_games} game-predictions")
    return results, total_games


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

BUCKETS = ["00-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-99"]


def print_results(results, model_fns, market_key, line, total_games, mode_label):
    print(f"\n{'='*80}")
    print(f"  Market: {market_key} > {line}   Mode: {mode_label}   "
          f"({total_games:,} game-predictions)")
    print(f"{'='*80}")

    for model_name, _ in model_fns:
        data = results[model_name]
        all_trust   = [t for b in BUCKETS for t in data[b]["trust_scores"]]
        all_actuals = [a for b in BUCKETS for a in data[b]["actuals"]]

        if not all_trust:
            print(f"\n  Model: {model_name} - no predictions")
            continue

        bs          = brier_score(all_trust, all_actuals)
        ll          = log_loss(all_trust, all_actuals)
        overall_hit = sum(all_actuals) / len(all_actuals) * 100

        print(f"\n  Model: {model_name}")
        print(f"  Brier={bs:.4f}  LogLoss={ll:.4f}  "
              f"Overall actual hit rate: {overall_hit:.1f}%  N={len(all_trust):,}")
        print(f"  {'Bucket':<10} {'N':>6} {'Avg Trust':>10} {'Actual%':>9} {'Diff':>7} {'Signal'}")
        print(f"  {'-'*55}")

        monotone = True
        prev_ar = None
        for b in BUCKETS:
            bd = data[b]
            n  = len(bd["actuals"])
            if n < 10:
                continue
            avg_trust   = sum(bd["trust_scores"]) / n
            actual_rate = sum(bd["actuals"]) / n * 100
            diff        = actual_rate - avg_trust
            signal      = ("OVER  " if diff > 5 else
                           "UNDER " if diff < -5 else
                           "OK    ")
            print(f"  {b:<10} {n:>6,} {avg_trust:>10.1f} {actual_rate:>9.1f} "
                  f"{diff:>+7.1f} {signal}")
            if prev_ar is not None and actual_rate < prev_ar - 2:
                monotone = False
            prev_ar = actual_rate

        print(f"  Discrimination (higher trust = higher hit rate): "
              f"{'YES' if monotone else 'NO - weights need adjustment'}")


def print_factor_comparison(all_results, market_key, line):
    """Show incremental gain from each model vs base."""
    print(f"\n  -- Factor gain summary for {market_key} > {line} --")
    base_brier = None
    for model_name, data in all_results.items():
        all_trust   = [t for b in BUCKETS for t in data[b]["trust_scores"]]
        all_actuals = [a for b in BUCKETS for a in data[b]["actuals"]]
        if not all_trust:
            continue
        bs = brier_score(all_trust, all_actuals)
        if base_brier is None:
            base_brier = bs
            print(f"  {model_name:<55} Brier={bs:.4f}  (baseline)")
        else:
            delta = base_brier - bs  # positive = improvement
            sign = "+" if delta >= 0 else ""
            print(f"  {model_name:<55} Brier={bs:.4f}  delta={sign}{delta:.4f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--market",    choices=list(MARKETS.keys()), default=None)
    parser.add_argument("--line",      type=float, default=None)
    parser.add_argument("--season",    default="2025",
                        help="Season for within-season mode (default 2025)")
    parser.add_argument("--min-prior", type=int, default=15,
                        help="Min prior games needed (default 15)")
    parser.add_argument("--cross-season", action="store_true",
                        help="Use 2025 as prior, validate on 2026 outcomes")
    parser.add_argument("--statcast", action="store_true",
                        help="Fetch Statcast data from Baseball Savant + MLB Stats API")
    parser.add_argument("--sweep", action="store_true",
                        help="Sweep BABIP/hard-hit multiplier variants (requires --statcast)")
    args = parser.parse_args()

    engine  = get_engine()
    session = get_session(engine)

    # Fetch Statcast data (optional)
    statcast_by_pid = {}
    adv_by_pid      = {}
    if args.statcast:
        stat_year = 2025 if args.cross_season else int(args.season)
        statcast_by_pid = fetch_savant_statcast(stat_year)

        # Collect all batter IDs
        batter_ids = {
            p.id for p in session.query(MLBPlayer).filter_by(is_pitcher=False).all()
        }
        adv_by_pid = fetch_advanced_stats(batter_ids, stat_year)

    # Weight configurations to test
    if args.sweep and args.statcast:
        weight_configs = [
            (-20, 0.6, 0.2),   # current (v1)
            (-30, 0.7, 0.25),  # stronger BABIP + barrel
            (-40, 0.8, 0.3),   # strong (v2)
            (-50, 1.0, 0.35),  # aggressive
        ]
    else:
        weight_configs = [(-20, 0.6, 0.2)]  # current weights only

    markets_to_test = (
        [(args.market, [args.line] if args.line else MARKETS[args.market][1])]
        if args.market
        else [(k, MARKETS[k][1]) for k in MARKETS]
    )

    try:
        for market_key, lines in markets_to_test:
            _, _, player_type = MARKETS[market_key]
            is_pitcher = (player_type == "pitcher")

            for line in lines:
                all_model_results = {}

                for babip_m, barrel_m, hh_m in weight_configs:
                    model_fns = build_models(
                        statcast_by_pid, adv_by_pid,
                        babip_m, barrel_m, hh_m,
                    )

                    if args.cross_season:
                        mode_label = "cross-season 2025->2026"
                        results, total = run_cross_season(
                            session, market_key, line,
                            prior_season=2025, pred_season=2026,
                            min_prior=args.min_prior,
                            model_fns=model_fns,
                            is_pitcher=is_pitcher,
                        )
                    else:
                        mode_label = f"within-season {args.season}"
                        results, total = run_within_season(
                            session, market_key, line,
                            season_filter=args.season,
                            min_prior=args.min_prior,
                            model_fns=model_fns,
                            is_pitcher=is_pitcher,
                        )

                    print_results(results, model_fns, market_key, line, total, mode_label)
                    for model_name, _ in model_fns:
                        all_model_results[model_name] = results[model_name]

                if len(all_model_results) > 1:
                    print_factor_comparison(all_model_results, market_key, line)

        print("\n\nDONE.")
        print("  Brier score: lower = better (0 = perfect, 0.25 = random coin flip)")
        print("  LogLoss:     lower = better")
        print("  Diff:        Actual% - Avg Trust%. OVER = trust underestimates real rate.")
        print("  Signal OK:   within +-5 pts of actual. OVER/UNDER = miscalibrated.")

    finally:
        session.close()


if __name__ == "__main__":
    main()
