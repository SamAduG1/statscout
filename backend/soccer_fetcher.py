"""
StatScout Soccer Fetcher
- Upcoming EPL fixtures + over/under odds: The Odds API (soccer_epl)
- Historical hit rates + team goal averages: football-data.org (season 2024, free tier)
"""

import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SEASON = 2024  # 2024-25 season

# Maps Odds API team name variants to football-data.org full names.
# Used to cross-reference upcoming fixture names with historical stats.
ODDS_TO_FD = {
    "Arsenal": "Arsenal FC",
    "Aston Villa": "Aston Villa FC",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford FC",
    "Brighton": "Brighton & Hove Albion FC",
    "Brighton and Hove Albion": "Brighton & Hove Albion FC",
    "Chelsea": "Chelsea FC",
    "Crystal Palace": "Crystal Palace FC",
    "Everton": "Everton FC",
    "Fulham": "Fulham FC",
    "Ipswich": "Ipswich Town FC",
    "Ipswich Town": "Ipswich Town FC",
    "Leicester": "Leicester City FC",
    "Leicester City": "Leicester City FC",
    "Liverpool": "Liverpool FC",
    "Manchester City": "Manchester City FC",
    "Manchester United": "Manchester United FC",
    "Newcastle": "Newcastle United FC",
    "Newcastle United": "Newcastle United FC",
    "Nottingham Forest": "Nottingham Forest FC",
    "Southampton": "Southampton FC",
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
        """Get all completed 2024-25 PL matches (1 football-data.org call)."""
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

    # ── Match card builder ────────────────────────────────────────────────────

    @staticmethod
    def _avg(lst, key):
        return round(sum(g[key] for g in lst) / len(lst), 1) if lst else 0.0

    @staticmethod
    def _pct(lst, key):
        return round(sum(1 for g in lst if g[key]) / len(lst) * 100) if lst else None

    @staticmethod
    def _over_pct(lst, line):
        return round(sum(1 for g in lst if g["total"] > line) / len(lst) * 100) if lst else None

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

        home_avg = self._avg(home_h, "scored")
        away_avg = self._avg(away_a, "scored")
        expected = round(home_avg + away_avg, 1)

        line, over_o, under_o, bookmaker = self._parse_odds_event(event)

        relevant = home_h + away_a
        over_rate = self._over_pct(relevant, line)
        btts_rate = self._pct(relevant, "btts")

        # Parse ISO datetime from Odds API e.g. "2026-03-04T13:00:00Z"
        commence = event.get("commence_time", "")
        try:
            dt = datetime.fromisoformat(commence.replace('Z', '+00:00'))
            game_date = dt.strftime("%b %d")
            game_time = dt.strftime("%I:%M %p").lstrip("0")
        except Exception:
            game_date = commence[:10] if commence else "TBD"
            game_time = "TBD"

        return {
            "id": event.get("id", ""),
            "homeTeam": home_name,
            "awayTeam": away_name,
            "homeTeamLogo": "",
            "awayTeamLogo": "",
            "gameDate": game_date,
            "gameTime": game_time,
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
        }

    # ── Main entry point ──────────────────────────────────────────────────────

    def fetch_all(self):
        """
        Fetch everything and return structured match data.
        API calls: 1 football-data.org (historical) + 1 Odds API (fixtures + odds)
        """
        print("[SOCCER] Fetching 2024-25 historical results for hit rates...")
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
        matches.sort(key=lambda m: m["gameDate"])

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
