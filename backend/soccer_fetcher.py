"""
StatScout Soccer Fetcher
- Upcoming fixtures + over/under odds: The Odds API
- Historical hit rates + team goal averages: football-data.org (season 2025, free tier)
- Supported competitions: Premier League (pl), La Liga (laliga)
"""

import requests
import os
import statistics
import threading
import unicodedata
from dotenv import load_dotenv

# Limit concurrent football-data.org calls to 1 to avoid 429s when multiple
# league caches build simultaneously (free tier: 10 req/min)
_fd_semaphore = threading.Semaphore(1)

load_dotenv()

SEASON = 2025  # 2025-26 season


def _norm(name):
    """Strip accents so 'Atlético' and 'Atletico' match."""
    return unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')

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

# La Liga 2025-26 team name mappings (Odds API -> football-data.org).
# All keys are pre-normalized (no accents) — the lookup normalizes before checking.
# 2025-26 promoted: Real Oviedo, Levante UD, Elche CF
LALIGA_ODDS_TO_FD = {
    "Athletic Club": "Athletic Club",
    "Athletic Bilbao": "Athletic Club",
    "Atletico Madrid": "Club Atletico de Madrid",
    "Atletico de Madrid": "Club Atletico de Madrid",
    "Barcelona": "FC Barcelona",
    "Celta Vigo": "RC Celta de Vigo",
    "Deportivo Alaves": "Deportivo Alaves",
    "Alaves": "Deportivo Alaves",
    "Elche CF": "Elche CF",
    "Elche": "Elche CF",
    "Espanyol": "RCD Espanyol de Barcelona",
    "Getafe": "Getafe CF",
    "Girona": "Girona FC",
    "Las Palmas": "UD Las Palmas",
    "Leganes": "CD Leganes",
    "Levante": "Levante UD",
    "Mallorca": "RCD Mallorca",
    "Osasuna": "CA Osasuna",
    "Oviedo": "Real Oviedo",
    "Real Oviedo": "Real Oviedo",
    "Rayo Vallecano": "Rayo Vallecano de Madrid",
    "Real Betis": "Real Betis Balompie",
    "Real Madrid": "Real Madrid CF",
    "Real Sociedad": "Real Sociedad de Futbol",
    "Real Valladolid": "Real Valladolid CF",
    "Valladolid": "Real Valladolid CF",
    "Sevilla": "Sevilla FC",
    "Valencia": "Valencia CF",
    "Villarreal": "Villarreal CF",
}

# Bundesliga 2025-26 (Hamburger SV promoted, Koln/Heidenheim relegated then promoted varies)
BUNDESLIGA_ODDS_TO_FD = {
    "1. FC Heidenheim":           "1. FC Heidenheim 1846",
    "Augsburg":                   "FC Augsburg",
    "Bayer Leverkusen":           "Bayer 04 Leverkusen",
    "Bayern Munich":              "FC Bayern München",
    "Borussia Dortmund":          "Borussia Dortmund",
    "Borussia Monchengladbach":   "Borussia Mönchengladbach",
    "Eintracht Frankfurt":        "Eintracht Frankfurt",
    "FC St. Pauli":               "FC St. Pauli 1910",
    "FSV Mainz 05":               "1. FSV Mainz 05",
    "Hamburger SV":               "Hamburger SV",
    "RB Leipzig":                 "RB Leipzig",
    "SC Freiburg":                "SC Freiburg",
    "TSG Hoffenheim":             "TSG 1899 Hoffenheim",
    "Union Berlin":               "1. FC Union Berlin",
    "VfB Stuttgart":              "VfB Stuttgart",
    "VfL Wolfsburg":              "VfL Wolfsburg",
    "Werder Bremen":              "SV Werder Bremen",
    "1. FC Köln":                 "1. FC Köln",
}

# Serie A 2025-26 (Pisa, Cremonese, Sassuolo promoted)
SERIEA_ODDS_TO_FD = {
    "AC Milan":                   "AC Milan",
    "AS Roma":                    "AS Roma",
    "Atalanta BC":                "Atalanta BC",
    "Bologna":                    "Bologna FC 1909",
    "Cagliari":                   "Cagliari Calcio",
    "Como":                       "Como 1907",
    "Cremonese":                  "US Cremonese",
    "Fiorentina":                 "ACF Fiorentina",
    "Genoa":                      "Genoa CFC",
    "Hellas Verona":              "Hellas Verona FC",
    "Inter Milan":                "FC Internazionale Milano",
    "Juventus":                   "Juventus FC",
    "Lazio":                      "SS Lazio",
    "Lecce":                      "US Lecce",
    "Napoli":                     "SSC Napoli",
    "Parma":                      "Parma Calcio 1913",
    "Pisa":                       "AC Pisa 1909",
    "Sassuolo":                   "US Sassuolo Calcio",
    "Torino":                     "Torino FC",
    "Udinese":                    "Udinese Calcio",
}

# Ligue 1 2025-26 (Paris FC, Angers, Auxerre promoted)
LIGUE1_ODDS_TO_FD = {
    "AS Monaco":                  "AS Monaco FC",
    "Angers":                     "Angers SCO",
    "Auxerre":                    "AJ Auxerre",
    "Brest":                      "Stade Brestois 29",
    "Le Havre":                   "Le Havre AC",
    "Lille":                      "Lille OSC",
    "Lorient":                    "FC Lorient",
    "Lyon":                       "Olympique Lyonnais",
    "Marseille":                  "Olympique de Marseille",
    "Metz":                       "FC Metz",
    "Nantes":                     "FC Nantes",
    "Nice":                       "OGC Nice",
    "Paris FC":                   "Paris FC",
    "Paris Saint Germain":        "Paris Saint-Germain FC",
    "RC Lens":                    "Racing Club de Lens",
    "Rennes":                     "Stade Rennais FC 1901",
    "Strasbourg":                 "RC Strasbourg Alsace",
    "Toulouse":                   "Toulouse FC",
}

COMPETITIONS = {
    "pl": {
        "odds_sport": "soccer_epl",
        "fd_code": "PL",
        "name": "Premier League",
        "odds_to_fd": ODDS_TO_FD,
        "regions": "us",
    },
    "laliga": {
        "odds_sport": "soccer_spain_la_liga",
        "fd_code": "PD",
        "name": "La Liga",
        "odds_to_fd": LALIGA_ODDS_TO_FD,
        "regions": "uk,eu",
    },
    "bundesliga": {
        "odds_sport": "soccer_germany_bundesliga",
        "fd_code": "BL1",
        "name": "Bundesliga",
        "odds_to_fd": BUNDESLIGA_ODDS_TO_FD,
        "regions": "uk,eu",
    },
    "seriea": {
        "odds_sport": "soccer_italy_serie_a",
        "fd_code": "SA",
        "name": "Serie A",
        "odds_to_fd": SERIEA_ODDS_TO_FD,
        "regions": "uk,eu",
    },
    "ligue1": {
        "odds_sport": "soccer_france_ligue_1",
        "fd_code": "FL1",
        "name": "Ligue 1",
        "odds_to_fd": LIGUE1_ODDS_TO_FD,
        "regions": "uk,eu",
    },
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

    def get_historical_results(self, fd_code='PL'):
        """Get all completed 2025-26 matches for a competition (1 football-data.org call)."""
        with _fd_semaphore:
            r = requests.get(
                f"{self.FD_BASE}/competitions/{fd_code}/matches",
                headers=self.fd_headers,
                params={"season": SEASON, "status": "FINISHED"},
                timeout=15,
            )
        r.raise_for_status()
        data = r.json()
        matches = data.get("matches", [])
        print(f"[SOCCER] football-data.org — {len(matches)} finished {fd_code} matches")
        return matches

    # ── The Odds API ──────────────────────────────────────────────────────────

    def get_odds(self, sport_key='soccer_epl', regions='us'):
        """
        Get upcoming events with totals odds for a sport key (1 Odds API call).
        Returns raw list of event objects.
        """
        if not self.odds_key:
            return []
        try:
            r = requests.get(
                f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
                params={
                    "apiKey": self.odds_key,
                    "markets": "totals",
                    "regions": regions,
                    "oddsFormat": "american",
                },
                timeout=10,
            )
            remaining = r.headers.get('x-requests-remaining', '?')
            print(f"[SOCCER] Odds API ({sport_key}) — {remaining} requests remaining")
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
            ht = match.get("score", {}).get("halfTime", {})
            hg_h1 = ht.get("home")
            ag_h1 = ht.get("away")
            h1_total = (hg_h1 + ag_h1) if (hg_h1 is not None and ag_h1 is not None) else None
            home_name = _norm(match["homeTeam"]["name"])
            away_name = _norm(match["awayTeam"]["name"])
            for name, scored, conceded, loc, h1_scored, h1_conceded in [
                (home_name, hg, ag, "home", hg_h1, ag_h1),
                (away_name, ag, hg, "away", ag_h1, hg_h1),
            ]:
                if name not in stats:
                    stats[name] = {"home": [], "away": [], "all": []}
                entry = {"scored": scored, "conceded": conceded,
                         "total": total, "btts": btts,
                         "h1_scored": h1_scored, "h1_conceded": h1_conceded,
                         "h1_total": h1_total}
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

    def _build_match_card(self, event, team_stats, odds_to_fd=None):
        """Build a single match card from an Odds API event + historical stats."""
        if odds_to_fd is None:
            odds_to_fd = ODDS_TO_FD
        home_name = event.get("home_team", "")
        away_name = event.get("away_team", "")

        # Translate Odds API names to football-data.org names for stat lookup.
        # Normalize the Odds API name first (strips accents like Atlético→Atletico)
        # so it matches the unaccented mapping keys, then normalize the result to
        # match the normalized keys in team_stats.
        home_fd = _norm(odds_to_fd.get(_norm(home_name), _norm(home_name)))
        away_fd = _norm(odds_to_fd.get(_norm(away_name), _norm(away_name)))

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

        # First-half: filter to games where halfTime data exists
        home_h_h1 = [g for g in home_h if g.get("h1_scored") is not None and g.get("h1_conceded") is not None]
        away_a_h1 = [g for g in away_a if g.get("h1_scored") is not None and g.get("h1_conceded") is not None]
        h1_home = [g["h1_total"] for g in home_h_h1]
        h1_away = [g["h1_total"] for g in away_a_h1]
        h1_combined = h1_home + h1_away
        h1_over05 = round(sum(1 for t in h1_combined if t > 0.5) / len(h1_combined) * 100) if h1_combined else None
        h1_over15 = round(sum(1 for t in h1_combined if t > 1.5) / len(h1_combined) * 100) if h1_combined else None
        # Form-weighted expected 1H total — same attack/defense blend as full-game formula
        if home_h_h1 and away_a_h1:
            h1_home_goals = (self._form_avg(home_h_h1, "h1_scored") + self._form_avg(away_a_h1, "h1_conceded")) / 2
            h1_away_goals = (self._form_avg(away_a_h1, "h1_scored") + self._form_avg(home_h_h1, "h1_conceded")) / 2
            h1_expected = round(h1_home_goals + h1_away_goals, 1)
        else:
            h1_expected = None
        h1_home_avg = self._avg(home_h_h1, "h1_scored") if home_h_h1 else None
        h1_away_avg = self._avg(away_a_h1, "h1_scored") if away_a_h1 else None

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
            "h1HomeGoalTotals": h1_home,
            "h1AwayGoalTotals": h1_away,
            "h1OverRate05": h1_over05,
            "h1OverRate15": h1_over15,
            "h1Expected": h1_expected,
            "h1HomeAvg": h1_home_avg,
            "h1AwayAvg": h1_away_avg,
        }

    # ── Main entry point ──────────────────────────────────────────────────────

    def fetch_all(self, competition='pl'):
        """
        Fetch everything and return structured match data.
        competition: 'pl' | 'laliga' (default 'pl')
        API calls: 1 football-data.org (historical) + 1 Odds API (fixtures + odds)
        """
        conf = COMPETITIONS.get(competition, COMPETITIONS["pl"])
        label = conf["name"]

        print(f"[SOCCER] Fetching 2025-26 historical results for {label}...")
        try:
            results = self.get_historical_results(fd_code=conf["fd_code"])
            team_stats = self._build_team_stats(results)
            print(f"[SOCCER] Loaded stats for {len(team_stats)} teams "
                  f"from {len(results)} historical matches")
        except Exception as e:
            print(f"[SOCCER] Historical stats unavailable ({e}), continuing with odds only")
            team_stats = {}

        print(f"[SOCCER] Fetching upcoming {label} fixtures and odds...")
        events = self.get_odds(sport_key=conf["odds_sport"], regions=conf["regions"])

        matches = [self._build_match_card(ev, team_stats, conf["odds_to_fd"]) for ev in events]
        matches.sort(key=lambda m: m["commenceTime"])

        print(f"[SOCCER] Built {len(matches)} {label} match cards")
        return {
            "success": True,
            "count": len(matches),
            "matches": matches,
        }


if __name__ == "__main__":
    import json
    import sys
    comp = sys.argv[1] if len(sys.argv) > 1 else "pl"
    result = SoccerFetcher().fetch_all(competition=comp)
    print(json.dumps(result, indent=2))
