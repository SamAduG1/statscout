"""
StatScout Soccer Fetcher
- Upcoming EPL fixtures + over/under odds: The Odds API (soccer_epl)
- Historical hit rates + team goal averages: API-Football (season 2024, free tier)
API-Football free tier only covers up to season 2024 (2024-25 season).
"""

import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

LEAGUE_ID = 39
SEASON = 2024
SEASON_FROM = "2024-08-01"
SEASON_TO = "2025-05-31"

# Maps both API-Football and Odds API name variants to API-Football team IDs.
# Used to cross-reference Odds API fixture names with historical stats.
PL_TEAM_IDS = {
    "Arsenal": 42,
    "Aston Villa": 66,
    "Bournemouth": 35,
    "Brentford": 55,
    "Brighton": 51,
    "Brighton and Hove Albion": 51,
    "Chelsea": 49,
    "Crystal Palace": 52,
    "Everton": 45,
    "Fulham": 36,
    "Ipswich": 57,
    "Leicester": 46,
    "Liverpool": 40,
    "Manchester City": 50,
    "Manchester United": 33,
    "Newcastle": 34,
    "Newcastle United": 34,
    "Nottingham Forest": 65,
    "Southampton": 41,
    "Tottenham": 47,
    "Tottenham Hotspur": 47,
    "West Ham": 48,
    "West Ham United": 48,
    "Wolves": 39,
    "Wolverhampton Wanderers": 39,
}


class SoccerFetcher:
    AF_BASE = "https://v3.football.api-sports.io"

    def __init__(self):
        self.api_key = (os.getenv('API_FOOTBALL_KEY') or '').strip()
        self.odds_key = (os.getenv('ODDS_API_KEY') or '').strip()
        self.af_headers = {"x-apisports-key": self.api_key}

        if not self.api_key:
            print("[SOCCER] WARNING: API_FOOTBALL_KEY not set")
        if not self.odds_key:
            print("[SOCCER] WARNING: ODDS_API_KEY not set")

    # ── API-Football ──────────────────────────────────────────────────────────

    def _af_get(self, endpoint, params):
        """GET from API-Football, return response array."""
        r = requests.get(f"{self.AF_BASE}/{endpoint}",
                         headers=self.af_headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        remaining = r.headers.get('x-ratelimit-requests-remaining', '?')
        print(f"[SOCCER] API-Football /{endpoint} — {remaining} requests remaining today")
        errors = data.get('errors', [])
        if errors:
            raise RuntimeError(f"API-Football error: {errors}")
        return data.get("response", [])

    def get_historical_results(self):
        """Get all completed 2024-25 PL matches (1 API-Football call)."""
        return self._af_get("fixtures", {
            "league": LEAGUE_ID,
            "season": SEASON,
            "status": "FT",
            "from": SEASON_FROM,
            "to": SEASON_TO,
        })

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
        {team_id: {"home": [...], "away": [...], "all": [...]}}
        where each entry = {scored, conceded, total, btts}
        """
        stats = {}
        for match in results:
            hg = match["goals"]["home"]
            ag = match["goals"]["away"]
            if hg is None or ag is None:
                continue
            total = hg + ag
            btts = hg > 0 and ag > 0
            for tid, scored, conceded, loc in [
                (match["teams"]["home"]["id"], hg, ag, "home"),
                (match["teams"]["away"]["id"], ag, hg, "away"),
            ]:
                if tid not in stats:
                    stats[tid] = {"home": [], "away": [], "all": []}
                entry = {"scored": scored, "conceded": conceded,
                         "total": total, "btts": btts}
                stats[tid][loc].append(entry)
                stats[tid]["all"].append(entry)
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
        home_id = PL_TEAM_IDS.get(home_name)
        away_id = PL_TEAM_IDS.get(away_name)

        home_h = team_stats.get(home_id, {}).get("home", []) if home_id else []
        away_a = team_stats.get(away_id, {}).get("away", []) if away_id else []

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
            "homeTeamLogo": "",   # Odds API doesn't provide logos
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
        API calls: 1 API-Football (historical) + 1 Odds API (fixtures + odds)
        """
        print("[SOCCER] Fetching 2024-25 historical results for hit rates...")
        results = self.get_historical_results()     # 1 API-Football call
        team_stats = self._build_team_stats(results)
        print(f"[SOCCER] Loaded stats for {len(team_stats)} teams "
              f"from {len(results)} historical matches")

        print("[SOCCER] Fetching upcoming EPL fixtures and odds...")
        epl_events = self.get_epl_odds()            # 1 Odds API call

        matches = [self._build_match_card(ev, team_stats) for ev in epl_events]
        # Sort by game date
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
