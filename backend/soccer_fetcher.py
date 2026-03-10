"""
StatScout Soccer Fetcher
- Upcoming EPL fixtures + over/under odds: The Odds API (soccer_epl)
- Historical hit rates + team goal averages: football-data.org (season 2025, free tier)
"""

import requests
import os
import statistics
from dotenv import load_dotenv

load_dotenv()

SEASON = 2025  # 2025-26 season

# Maps Odds API team name variants to football-data.org full names.
# Used to cross-reference upcoming fixture names with historical stats.
# 2025-26 PL: Burnley, Sunderland, Leeds promoted; Ipswich, Leicester, Southampton relegated.
ODDS_TO_FD = {
    "Arsenal": "Arsenal FC",
    "Aston Villa": "Aston Villa FC",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford FC",
    "Brighton": "Brighton & Hove Albion FC",
    "Brighton and Hove Albion": "Brighton & Hove Albion FC",
    "Burnley": "Burnley FC",
    "Chelsea": "Chelsea FC",
    "Crystal Palace": "Crystal Palace FC",
    "Everton": "Everton FC",
    "Fulham": "Fulham FC",
    "Leeds": "Leeds United FC",
    "Leeds United": "Leeds United FC",
    "Liverpool": "Liverpool FC",
    "Manchester City": "Manchester City FC",
    "Manchester United": "Manchester United FC",
    "Newcastle": "Newcastle United FC",
    "Newcastle United": "Newcastle United FC",
    "Nottingham Forest": "Nottingham Forest FC",
    "Sunderland": "Sunderland AFC",
    "Tottenham": "Tottenham Hotspur FC",
    "Tottenham Hotspur": "Tottenham Hotspur FC",
    "West Ham": "West Ham United FC",
    "West Ham United": "West Ham United FC",
    "Wolves": "Wolverhampton Wanderers FC",
    "Wolverhampton Wanderers": "Wolverhampton Wanderers FC",
}


class SoccerFetcher:
    FD_BASE = "https://api.football-data.org/v4"

    def __init__(self):
        self.fd_key = (os.getenv('FOOTBALL_DATA_KEY') or '').strip()
        self.odds_key = (os.getenv('ODDS_API_KEY') or '').strip()
        self.fd_headers = {"X-Auth-Token": self.fd_key}

        if not self.fd_key:
            print("[SOCCER] WARNING: FOOTBALL_DATA_KEY not set")
        if not self.odds_key:
            print("[SOCCER] WARNING: ODDS_API_KEY not set")

    # ── football-data.org ─────────────────────────────────────────────────────

    def get_historical_results(self):
        """Get all completed 2025-26 PL matches (1 football-data.org call)."""
        r = requests.get(
            f"{self.FD_BASE}/competitions/PL/matches",
            headers=self.fd_headers,
            params={"season": SEASON, "status": "FINISHED"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        matches = data.get("matches", [])
        print(f"[SOCCER] football-data.org — {len(matches)} finished PL matches")
        return matches

    # ── The Odds API ──────────────────────────────────────────────────────────

    def get_epl_odds(self):
        """
        Get upcoming EPL events with totals odds (1 Odds API call).
        Returns raw list of event objects.
        """
        if not self.odds_key:
            return []
        try:
            r = requests.get(
                "https://api.the-odds-api.com/v4/sports/soccer_epl/odds",
                params={
                    "apiKey": self.odds_key,
                    "markets": "totals",
                    "regions": "us",
                    "oddsFormat": "american",
                },
                timeout=10,
            )
            remaining = r.headers.get('x-requests-remaining', '?')
            print(f"[SOCCER] Odds API — {remaining} requests remaining")
            return r.json() if r.status_code == 200 else []
        except Exception as e:
            print(f"[SOCCER] Odds API error: {e}")
            return []

    # ── Stats computation ─────────────────────────────────────────────────────

    def _build_team_stats(self, results):
        """
        From completed results build:
        {fd_team_name: {"home": [...], "away": [...], "all": [...]}}
        where each entry = {scored, conceded, total, btts}
        """
        stats = {}
        for match in results:
            score = match.get("score", {}).get("fullTime", {})
            hg = score.get("home")
            ag = score.get("away")
            if hg is None or ag is None:
                continue
            total = hg + ag
            btts = hg > 0 and ag > 0
            home_name = match["homeTeam"]["name"]
            away_name = match["awayTeam"]["name"]
            for name, scored, conceded, loc in [
                (home_name, hg, ag, "home"),
                (away_name, ag, hg, "away"),
            ]:
                if name not in stats:
                    stats[name] = {"home": [], "away": [], "all": []}
                entry = {"scored": scored, "conceded": conceded,
                         "total": total, "btts": btts}
                stats[name][loc].append(entry)
                stats[name]["all"].append(entry)
        return stats

    # ── Match card helpers ────────────────────────────────────────────────────

    @staticmethod
    def _avg(lst, key):
        """Rounded average for display."""
        return round(sum(g[key] for g in lst) / len(lst), 1) if lst else 0.0

    @staticmethod
    def _avg_raw(lst, key):
        """Unrounded average for internal calculations."""
        return sum(g[key] for g in lst) / len(lst) if lst else 0.0

    @staticmethod
    def _form_avg(lst, key, decay=0.85):
        """
        Exponentially weighted average — most recent games count more.
        The list is assumed to be in chronological order (oldest first),
        as returned by football-data.org. decay=0.85 means a game 5
        matches ago carries ~44% of the weight of the latest game.
        """
        if not lst:
            return 0.0
        total = weight_sum = 0.0
        for i, g in enumerate(reversed(lst)):
            w = decay ** i
            total += g[key] * w
            weight_sum += w
        return total / weight_sum

    @staticmethod
    def _pct(lst, key):
        return round(sum(1 for g in lst if g[key]) / len(lst) * 100) if lst else None

    @staticmethod
    def _over_pct(lst, line):
        return round(sum(1 for g in lst if g["total"] > line) / len(lst) * 100) if lst else None

    @staticmethod
    def _american_to_implied(american_odds):
        """Convert American odds to implied probability (0–1)."""
        if american_odds is None:
            return None
        if american_odds > 0:
            return 100 / (american_odds + 100)
        return abs(american_odds) / (abs(american_odds) + 100)

    def _compute_trust_score(self, over_rate, expected, line, over_o,
                              home_games, away_games, relevant):
        """
        5-factor trust score (0–100). Returns None if < 5 venue games either side.

        Weights:
          30% — Over hit rate (historical tendency)
          25% — Expected vs line gap (model vs bookmaker)
          20% — Odds market lean (bookmaker's own pricing)
          15% — Consistency (std dev of goal totals; lower = more predictable)
          10% — Sample size confidence
        """
        min_games = min(home_games, away_games)
        if min_games < 5:
            return None

        # Factor 1: Over hit rate (30%)
        f_hit = float(over_rate) if over_rate is not None else 50.0

        # Factor 2: Expected vs line gap (25%)
        # ±1.5 goals maps to 0–100; 0 gap = neutral (50)
        gap = expected - line
        f_gap = max(0.0, min(100.0, 50.0 + (gap / 1.5) * 50.0))

        # Factor 3: Odds market lean (20%)
        implied = self._american_to_implied(over_o)
        f_odds = round(implied * 100, 1) if implied is not None else 50.0

        # Factor 4: Consistency — std dev of combined match totals (15%)
        totals = [g["total"] for g in relevant]
        if len(totals) >= 2:
            std_dev = statistics.stdev(totals)
            # std_dev 0.5→100, 1.0→80, 1.5→60, 2.0→40, 2.5→20, 3.0→0
            f_consistency = max(0.0, min(100.0, 100.0 - (std_dev - 0.5) * 40.0))
        else:
            f_consistency = 50.0

        # Factor 5: Sample size confidence (10%)
        # 5 games→40, 10→70, 19+→100
        f_sample = min(100.0, 40.0 + (min_games - 5) / 14.0 * 60.0)

        score = (
            f_hit        * 0.30 +
            f_gap        * 0.25 +
            f_odds       * 0.20 +
            f_consistency * 0.15 +
            f_sample     * 0.10
        )
        return round(score, 1)

    def _parse_odds_event(self, event):
        """Extract totals line and best odds from an Odds API event."""
        line = over_o = under_o = bookmaker = None
        for bm in event.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market["key"] != "totals":
                    continue
                for outcome in market.get("outcomes", []):
                    if outcome["name"] == "Over":
                        line = outcome.get("point")
                        over_o = outcome.get("price")
                    elif outcome["name"] == "Under":
                        under_o = outcome.get("price")
                if line is not None:
                    bookmaker = bm.get("title", "")
                    return line, over_o, under_o, bookmaker
        return 2.5, None, None, None

    def _build_match_card(self, event, team_stats):
        """Build a single match card from an Odds API event + historical stats."""
        home_name = event.get("home_team", "")
        away_name = event.get("away_team", "")

        # Translate Odds API names to football-data.org names for stat lookup
        home_fd = ODDS_TO_FD.get(home_name, home_name)
        away_fd = ODDS_TO_FD.get(away_name, away_name)

        home_h = team_stats.get(home_fd, {}).get("home", [])
        away_a = team_stats.get(away_fd, {}).get("away", [])

        # Per-team scoring averages (for display)
        home_avg = self._avg(home_h, "scored")
        away_avg = self._avg(away_a, "scored")

        # Expected total: blends attack strength + defensive weakness, form-weighted
        # home_goals = form_avg(home scored at home, away conceded away) / 2
        # away_goals = form_avg(away scored away, home conceded at home) / 2
        home_goals = (self._form_avg(home_h, "scored") + self._form_avg(away_a, "conceded")) / 2
        away_goals = (self._form_avg(away_a, "scored") + self._form_avg(home_h, "conceded")) / 2
        expected = round(home_goals + away_goals, 1)
        exp_home = round(home_goals, 2)   # for Poisson win probability in frontend
        exp_away = round(away_goals, 2)

        line, over_o, under_o, bookmaker = self._parse_odds_event(event)

        relevant = home_h + away_a
        over_rate = self._over_pct(relevant, line)
        btts_rate = self._pct(relevant, "btts")
        home_games = len(home_h)
        away_games = len(away_a)

        # Raw arrays for frontend adjustable line slider
        home_goal_totals = [g["total"] for g in home_h]   # match totals in home team's home games
        away_goal_totals = [g["total"] for g in away_a]   # match totals in away team's away games

        # Per-team scoring arrays for team goal props collapsible
        home_team_scored = [g["scored"] for g in home_h]  # home team goals scored at home
        away_team_scored = [g["scored"] for g in away_a]  # away team goals scored away

        trust_score = self._compute_trust_score(
            over_rate, expected, line, over_o, home_games, away_games, relevant
        )

        commence = event.get("commence_time", "")

        return {
            "id": event.get("id", ""),
            "homeTeam": home_name,
            "awayTeam": away_name,
            "homeTeamLogo": "",
            "awayTeamLogo": "",
            "commenceTime": commence,       # raw ISO UTC — frontend converts to local tz
            "venue": "",
            "overUnderLine": line,
            "overOdds": over_o,
            "underOdds": under_o,
            "bookmaker": bookmaker,
            "overHitRate": over_rate,
            "bttsRate": btts_rate,
            "homeAvgGoals": home_avg,
            "awayAvgGoals": away_avg,
            "expectedTotal": expected,
            "homeGames": home_games,
            "awayGames": away_games,
            "expectedHomeGoals": exp_home,  # Poisson lambda for home team
            "expectedAwayGoals": exp_away,  # Poisson lambda for away team
            "trustScore": trust_score,
            "homeGoalTotals": home_goal_totals,
            "awayGoalTotals": away_goal_totals,
            "homeTeamScoredAtHome": home_team_scored,
            "awayTeamScoredAway": away_team_scored,
        }

    # ── Main entry point ──────────────────────────────────────────────────────

    def fetch_all(self):
        """
        Fetch everything and return structured match data.
        API calls: 1 football-data.org (historical) + 1 Odds API (fixtures + odds)
        """
        print("[SOCCER] Fetching 2025-26 historical results for hit rates...")
        try:
            results = self.get_historical_results()
            team_stats = self._build_team_stats(results)
            print(f"[SOCCER] Loaded stats for {len(team_stats)} teams "
                  f"from {len(results)} historical matches")
        except Exception as e:
            print(f"[SOCCER] Historical stats unavailable ({e}), continuing with odds only")
            team_stats = {}

        print("[SOCCER] Fetching upcoming EPL fixtures and odds...")
        epl_events = self.get_epl_odds()

        matches = [self._build_match_card(ev, team_stats) for ev in epl_events]
        matches.sort(key=lambda m: m["commenceTime"])

        print(f"[SOCCER] Built {len(matches)} match cards")
        return {
            "success": True,
            "count": len(matches),
            "matches": matches,
        }


if __name__ == "__main__":
    import json
    result = SoccerFetcher().fetch_all()
    print(json.dumps(result, indent=2))
