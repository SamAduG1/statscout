"""
StatScout MLB Fetcher
- Upcoming games + odds (h2h, totals, spreads): The Odds API
- Historical 2025 season results + team run averages: MLB Stats API (free, official)
- Statcast metrics (barrel rate, hard-hit rate, xBA, K%): Baseball Savant (free CSV)
"""

import io
import csv
import requests
import os
import statistics
from datetime import date as _date
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
MLB_STATS_BASE = "https://statsapi.mlb.com/api/v1"
ODDS_BASE = "https://api.the-odds-api.com/v4"
SEASON = 2025  # 2025 MLB regular season for historical data
CURRENT_SEASON = 2026  # Active season for probable pitcher stats

# Odds API team name -> MLB Stats API full name (for any mismatches)
ODDS_TO_MLB = {
    "Arizona Diamondbacks": "Arizona Diamondbacks",
    "Atlanta Braves": "Atlanta Braves",
    "Baltimore Orioles": "Baltimore Orioles",
    "Boston Red Sox": "Boston Red Sox",
    "Chicago Cubs": "Chicago Cubs",
    "Chicago White Sox": "Chicago White Sox",
    "Cincinnati Reds": "Cincinnati Reds",
    "Cleveland Guardians": "Cleveland Guardians",
    "Colorado Rockies": "Colorado Rockies",
    "Detroit Tigers": "Detroit Tigers",
    "Houston Astros": "Houston Astros",
    "Kansas City Royals": "Kansas City Royals",
    "Los Angeles Angels": "Los Angeles Angels",
    "Los Angeles Dodgers": "Los Angeles Dodgers",
    "Miami Marlins": "Miami Marlins",
    "Milwaukee Brewers": "Milwaukee Brewers",
    "Minnesota Twins": "Minnesota Twins",
    "New York Mets": "New York Mets",
    "New York Yankees": "New York Yankees",
    "Oakland Athletics": "Oakland Athletics",
    "Philadelphia Phillies": "Philadelphia Phillies",
    "Pittsburgh Pirates": "Pittsburgh Pirates",
    "San Diego Padres": "San Diego Padres",
    "San Francisco Giants": "San Francisco Giants",
    "Seattle Mariners": "Seattle Mariners",
    "St. Louis Cardinals": "St. Louis Cardinals",
    "Tampa Bay Rays": "Tampa Bay Rays",
    "Texas Rangers": "Texas Rangers",
    "Toronto Blue Jays": "Toronto Blue Jays",
    "Washington Nationals": "Washington Nationals",
    # Athletics dropped their city name after relocating to Sacramento in 2025;
    # both MLB Stats API and the Odds API now use the bare "Athletics" name.
    "Athletics": "Athletics",
    # Older/alternate name variants some sportsbook feeds may still send
    "Oakland Athletics": "Athletics",
    "Sacramento Athletics": "Athletics",
}


class MLBFetcher:

    def get_historical_results(self):
        """Fetch all 2025 MLB regular season finished games with scores."""
        r = requests.get(
            f"{MLB_STATS_BASE}/schedule",
            params={
                "sportId": 1,
                "season": SEASON,
                "gameType": "R",
                "startDate": f"{SEASON}-03-27",
                "endDate": f"{SEASON}-09-28",
                "fields": "dates,date,games,status,abstractGameState,teams,home,away,team,name,score",
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        games = []
        for date_entry in data.get("dates", []):
            for game in date_entry.get("games", []):
                if game.get("status", {}).get("abstractGameState") != "Final":
                    continue
                home = game["teams"]["home"]
                away = game["teams"]["away"]
                hs = home.get("score")
                as_ = away.get("score")
                if hs is None or as_ is None:
                    continue
                games.append({
                    "home_team": home["team"]["name"],
                    "away_team": away["team"]["name"],
                    "home_score": int(hs),
                    "away_score": int(as_),
                })
        return games

    def build_team_stats(self, games):
        """Build per-team home/away run averages from historical games."""
        stats = {}

        for g in games:
            home = g["home_team"]
            away = g["away_team"]
            hs = g["home_score"]
            as_ = g["away_score"]

            for team in [home, away]:
                if team not in stats:
                    stats[team] = {
                        "home_scored": [], "home_allowed": [], "home_totals": [],
                        "away_scored": [], "away_allowed": [], "away_totals": [],
                    }

            stats[home]["home_scored"].append(hs)
            stats[home]["home_allowed"].append(as_)
            stats[home]["home_totals"].append(hs + as_)

            stats[away]["away_scored"].append(as_)
            stats[away]["away_allowed"].append(hs)
            stats[away]["away_totals"].append(hs + as_)

        return stats

    def get_todays_opponent_map(self, date_str=None):
        """
        Fetch today's MLB schedule directly (not via mlb_cache/Odds API) and return
        team -> opponent team name mapping, keyed by MLB Stats API full team names.

        Used so opponent identification doesn't depend on the Odds-API-backed game
        card cache being warm — it survives a cold start on the game data side.

        Returns dict: { "New York Yankees": "Detroit Tigers", "Detroit Tigers": "New York Yankees", ... }
        """
        if date_str is None:
            date_str = _date.today().isoformat()

        try:
            r = requests.get(
                f"{MLB_STATS_BASE}/schedule",
                params={
                    "sportId": 1,
                    "date": date_str,
                    "gameType": "R,F,D,L,W",
                    "fields": "dates,games,teams,home,away,team,name",
                },
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[MLB] Opponent map schedule fetch failed: {e}")
            return {}

        opponent_map = {}
        for date_entry in data.get("dates", []):
            for game in date_entry.get("games", []):
                home_name = game["teams"]["home"]["team"]["name"]
                away_name = game["teams"]["away"]["team"]["name"]
                opponent_map[home_name] = away_name
                opponent_map[away_name] = home_name
        return opponent_map

    def get_probable_pitchers_with_stats(self, date_str=None):
        """
        Fetch today's probable starters + season ERA/K9/WHIP from MLB Stats API.
        Returns dict keyed by MLB full team name:
          { "New York Yankees": { "name": "Gerrit Cole", "era": 3.21, "k9": 9.8, "whip": 1.05 }, ... }
        """
        if date_str is None:
            date_str = _date.today().isoformat()

        try:
            r = requests.get(
                f"{MLB_STATS_BASE}/schedule",
                params={
                    "sportId": 1,
                    "date": date_str,
                    "gameType": "R,F,D,L,W",
                    "fields": "dates,games,teams,home,away,team,name,probablePitcher,id,fullName",
                },
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[MLB] Probable pitcher schedule fetch failed: {e}")
            return {}

        # Build team -> pitcher_id map
        team_to_pitcher = {}
        for date_entry in data.get("dates", []):
            for game in date_entry.get("games", []):
                for side in ("home", "away"):
                    t = game["teams"][side]
                    pitcher = t.get("probablePitcher", {})
                    if pitcher.get("id"):
                        team_name = t["team"]["name"]
                        team_to_pitcher[team_name] = {
                            "name": pitcher.get("fullName", "TBD"),
                            "id": pitcher["id"],
                        }

        if not team_to_pitcher:
            return {}

        # Fetch season stats for each pitcher (one call per pitcher)
        result = {}
        for team_name, info in team_to_pitcher.items():
            stats = self._get_pitcher_season_stats(info["id"])
            result[team_name] = {
                "name":      info["name"],
                "era":       stats.get("era"),
                "k9":        stats.get("k9"),
                "whip":      stats.get("whip"),
                "gs":        stats.get("gs", 0),
                "pitchHand": stats.get("pitchHand"),
            }
            print(f"[MLB] Starter {info['name']} ({team_name}): ERA {stats.get('era')}, K/9 {stats.get('k9')}, Hand {stats.get('pitchHand')}")

        return result

    def _get_pitcher_season_stats(self, pitcher_id):
        """
        Fetch a pitcher's current season ERA/K9/WHIP + throwing hand in a single API call.
        Uses the /people/{id} endpoint with hydrations=stats(group=pitching,type=season,season=YEAR).
        """
        try:
            r = requests.get(
                f"{MLB_STATS_BASE}/people/{pitcher_id}",
                params={
                    "hydrations": f"stats(group=pitching,type=season,season={CURRENT_SEASON})",
                    "fields": "people,pitchHand,code,stats,splits,stat,era,strikeoutsPer9Inn,whip,gamesStarted",
                },
                timeout=10,
            )
            r.raise_for_status()
            people = r.json().get("people", [{}])
            person = people[0] if people else {}
            pitch_hand = person.get("pitchHand", {}).get("code")  # "R" or "L"

            # Season stats are hydrated inline on the person object
            stat_groups = person.get("stats", [])
            result = {"pitchHand": pitch_hand}
            for sg in stat_groups:
                splits = sg.get("splits", [])
                if splits:
                    s = splits[0].get("stat", {})
                    # Use None instead of 0.0 for missing/zero stats so callers
                    # can distinguish "no data" from a genuine value. A 0.00 ERA
                    # fed into the trust modifier is treated as peak performance
                    # and applies the maximum negative adjustment to opposing
                    # batters — wrong for pitchers who simply haven't started yet.
                    def _stat(val, ndigits):
                        try:
                            f = float(val)
                            return round(f, ndigits) if f > 0 else None
                        except (TypeError, ValueError):
                            return None

                    result.update({
                        "era":  _stat(s.get("era"),                 2),
                        "k9":   _stat(s.get("strikeoutsPer9Inn"),   1),
                        "whip": _stat(s.get("whip"),                2),
                        "gs":   int(s.get("gamesStarted", 0) or 0),
                    })
                    break
            return result
        except Exception:
            return {"pitchHand": None}

    def get_upcoming_odds(self):
        """Fetch upcoming MLB games with h2h, totals, and run line from Odds API."""
        r = requests.get(
            f"{ODDS_BASE}/sports/baseball_mlb/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "us",
                "markets": "h2h,totals,spreads",
                "oddsFormat": "american",
                "dateFormat": "iso",
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()

    def _avg(self, arr):
        return round(sum(arr) / len(arr), 2) if arr else None

    def _to_prob(self, odds):
        if odds is None:
            return None
        if odds > 0:
            return 100 / (odds + 100)
        return abs(odds) / (abs(odds) + 100)

    def _compute_trust(self, totals, ou_line, expected, over_odds, under_odds):
        if not totals or ou_line is None or len(totals) < 10:
            return None

        score = 0.0

        # Baseline: having 80+ games of data is already meaningful in baseball
        # (162-game season means our samples are inherently large)
        baseline = min(len(totals) / 160.0, 1.0) * 15
        score += baseline

        # Factor 1: Over hit rate (25%)
        # Baseball lines are set near 50/50 — even 55% is a real edge.
        # Use 5x multiplier so 55% deviation = 0.5 score (vs 2x in soccer)
        over_rate = sum(1 for t in totals if t > ou_line) / len(totals)
        hit_score = min(abs(over_rate - 0.5) * 5, 1.0)
        score += hit_score * 25

        # Factor 2: Expected vs line gap (25%)
        # Baseball gaps are naturally smaller — 1.5 run gap = full score
        if expected is not None:
            gap_score = min(abs(expected - ou_line) / 1.5, 1.0)
            score += gap_score * 25

        # Factor 3: Odds market lean (20%)
        # Same 5x multiplier — bookmakers are efficient in MLB
        op = self._to_prob(over_odds)
        up = self._to_prob(under_odds)
        if op and up:
            lean = min(abs(op - 0.5) * 5, 1.0)
            score += lean * 20

        # Factor 4: Consistency — baseball std of 3.5 runs is completely normal
        # Use /8 so std=3.5 gives 0.56, std=2 gives 0.75, std=5+ gives 0.37
        if len(totals) >= 2:
            std = statistics.stdev(totals)
            consistency = max(0.0, 1.0 - std / 8.0)
            score += consistency * 15

        return round(min(score, 100))

    def build_game_cards(self, upcoming_odds, team_stats, probable_pitchers=None):
        if probable_pitchers is None:
            probable_pitchers = {}
        cards = []

        for game in upcoming_odds:
            odds_home = game.get("home_team", "")
            odds_away = game.get("away_team", "")

            # Map Odds API names to MLB Stats API names
            home_name = ODDS_TO_MLB.get(odds_home, odds_home)
            away_name = ODDS_TO_MLB.get(odds_away, odds_away)

            # Extract markets from first available bookmaker
            h2h_home = h2h_away = None
            ou_line = over_odds = under_odds = None
            run_line = run_line_odds_home = run_line_odds_away = None

            for bk in game.get("bookmakers", []):
                for market in bk.get("markets", []):
                    mk = market["key"]
                    outcomes = market.get("outcomes", [])
                    if mk == "h2h" and h2h_home is None:
                        for o in outcomes:
                            if o["name"] == odds_home:
                                h2h_home = o["price"]
                            elif o["name"] == odds_away:
                                h2h_away = o["price"]
                    elif mk == "totals" and ou_line is None:
                        for o in outcomes:
                            ou_line = ou_line or o.get("point")
                            if o["name"] == "Over":
                                over_odds = o["price"]
                            elif o["name"] == "Under":
                                under_odds = o["price"]
                    elif mk == "spreads" and run_line is None:
                        for o in outcomes:
                            if o["name"] == odds_home:
                                run_line = o.get("point")
                                run_line_odds_home = o["price"]
                            elif o["name"] == odds_away:
                                run_line_odds_away = o["price"]
                if h2h_home and ou_line and run_line:
                    break

            # Get team stats
            hs = team_stats.get(home_name, {})
            as_ = team_stats.get(away_name, {})

            home_h_scored = hs.get("home_scored", [])
            home_h_allowed = hs.get("home_allowed", [])
            away_a_scored = as_.get("away_scored", [])
            away_a_allowed = as_.get("away_allowed", [])

            # Expected run total via attack/defense blend
            expected_total = None
            if home_h_scored and away_a_allowed and away_a_scored and home_h_allowed:
                exp_home = (self._avg(home_h_scored) + self._avg(away_a_allowed)) / 2
                exp_away = (self._avg(away_a_scored) + self._avg(home_h_allowed)) / 2
                expected_total = round(exp_home + exp_away, 1)

            # Combined run totals for over rate + trust
            combined = home_h_scored + away_a_scored  # same-venue game totals
            # Use actual game totals (home + away per game) for over rate
            home_totals = hs.get("home_totals", [])
            away_totals = as_.get("away_totals", [])
            all_totals = home_totals + away_totals

            over_rate = None
            if all_totals and ou_line:
                over_rate = round(sum(1 for t in all_totals if t > ou_line) / len(all_totals) * 100)

            trust_score = self._compute_trust(all_totals, ou_line, expected_total, over_odds, under_odds)

            # Win probability from moneyline implied odds
            home_win_prob = away_win_prob = None
            hp = self._to_prob(h2h_home)
            ap = self._to_prob(h2h_away)
            if hp and ap:
                total_p = hp + ap
                home_win_prob = round(hp / total_p * 100)
                away_win_prob = round(ap / total_p * 100)

            # Probable pitchers (keyed by MLB full name via ODDS_TO_MLB)
            home_mlb_name = ODDS_TO_MLB.get(odds_home, odds_home)
            away_mlb_name = ODDS_TO_MLB.get(odds_away, odds_away)
            home_starter = probable_pitchers.get(home_mlb_name)
            away_starter = probable_pitchers.get(away_mlb_name)

            cards.append({
                "homeTeam": odds_home,
                "awayTeam": odds_away,
                "commenceTime": game.get("commence_time"),
                "homeProbablePitcher": home_starter,
                "awayProbablePitcher": away_starter,
                "homeMoneyline": h2h_home,
                "awayMoneyline": h2h_away,
                "runLine": run_line,
                "runLineOddsHome": run_line_odds_home,
                "runLineOddsAway": run_line_odds_away,
                "ouLine": ou_line,
                "overOdds": over_odds,
                "underOdds": under_odds,
                "overRate": over_rate,
                "expectedTotal": expected_total,
                "homeAvgRuns": self._avg(home_h_scored),
                "awayAvgRuns": self._avg(away_a_scored),
                "homeAvgAllowed": self._avg(home_h_allowed),
                "awayAvgAllowed": self._avg(away_a_allowed),
                "homeWinProb": home_win_prob,
                "awayWinProb": away_win_prob,
                "sampleSize": len(all_totals),
                "trustScore": trust_score,
                "runTotals": all_totals[-30:],
            })

        return cards

    def get_team_season_stats(self):
        """Fetch current-season team pitching ERA, batting K/game, and runs/game.

        Returns dict keyed by full team name (MLB Stats API format):
            {
                "Houston Astros": {"era": 3.82, "kPerGame": 9.1, "runsPerGame": 5.1},
                ...
            }
        Used to compute opposing-team defense modifiers in trust score:
          - For batters:  higher opp ERA        = weaker pitching  = easier matchup
          - For pitchers: higher opp K/G        = lineup strikes out more = easier
          - For RBI/Runs: higher own team RPG   = more run-scoring context = easier
        """
        result = {}
        try:
            r = requests.get(f"{MLB_STATS_BASE}/teams/stats", params={
                "stats": "season", "group": "pitching",
                "season": CURRENT_SEASON, "sportId": 1,
            }, timeout=20)
            r.raise_for_status()
            for split in r.json().get("stats", [{}])[0].get("splits", []):
                name = split.get("team", {}).get("name")
                era  = split.get("stat", {}).get("era")
                if name and era is not None:
                    result.setdefault(name, {})["era"] = float(era)
        except Exception as e:
            print(f"[MLB] Team pitching stats unavailable: {e}")

        try:
            r2 = requests.get(f"{MLB_STATS_BASE}/teams/stats", params={
                "stats": "season", "group": "hitting",
                "season": CURRENT_SEASON, "sportId": 1,
            }, timeout=20)
            r2.raise_for_status()
            for split in r2.json().get("stats", [{}])[0].get("splits", []):
                name       = split.get("team", {}).get("name")
                stat       = split.get("stat", {})
                strikeouts = stat.get("strikeOuts")
                runs       = stat.get("runs")
                games      = stat.get("gamesPlayed")
                if name and games:
                    if strikeouts:
                        result.setdefault(name, {})["kPerGame"] = round(
                            float(strikeouts) / float(games), 2
                        )
                    if runs:
                        result.setdefault(name, {})["runsPerGame"] = round(
                            float(runs) / float(games), 2
                        )
        except Exception as e:
            print(f"[MLB] Team batting stats unavailable: {e}")

        return result

    def get_player_advanced_stats(self, player_ids):
        """
        Fetch per-player K%, BB%, BABIP from MLB Stats API for a list of player IDs.
        Uses the bulk /people endpoint (one call, up to 100 IDs at a time).

        Returns dict keyed by player_id (int):
            {
                630105: {"kPct": 22.4, "bbPct": 8.1, "babip": 0.312},
                ...
            }
        """
        result = {}
        # Chunk into batches of 100 (API limit)
        ids = list(player_ids)
        for i in range(0, len(ids), 100):
            batch = ids[i:i+100]
            try:
                r = requests.get(
                    f"{MLB_STATS_BASE}/people",
                    params={
                        "personIds": ",".join(str(x) for x in batch),
                        "hydrate": f"stats(group=hitting,type=season,season={CURRENT_SEASON})",
                    },
                    timeout=20,
                )
                r.raise_for_status()
                for person in r.json().get("people", []):
                    pid  = person.get("id")
                    stat = {}
                    for sg in person.get("stats", []):
                        splits = sg.get("splits", [])
                        if splits:
                            stat = splits[0].get("stat", {})
                            break
                    if pid and stat:
                        pas   = float(stat.get("plateAppearances") or 0)
                        ks    = float(stat.get("strikeOuts") or 0)
                        bbs   = float(stat.get("baseOnBalls") or 0)
                        babip = stat.get("babip")
                        entry = {}
                        if pas > 0:
                            entry["kPct"]  = round(ks  / pas * 100, 1)
                            entry["bbPct"] = round(bbs / pas * 100, 1)
                        if babip is not None:
                            entry["babip"] = round(float(babip), 3)
                        if entry:
                            result[pid] = entry
            except Exception as e:
                print(f"[MLB] Player advanced stats batch failed: {e}")
        return result

    def get_savant_statcast(self, season=None):
        """
        Fetch Statcast leaderboard from Baseball Savant as a bulk CSV.
        Returns dict keyed by player_id (int):
            {
                630105: {
                    "barrelPct":  8.2,   # % of batted balls with optimal EV+LA
                    "hardHitPct": 44.1,  # % batted balls >= 95 mph EV
                    "xba":        0.271, # expected batting average
                    "exitVelo":   91.3,  # avg exit velocity (mph)
                },
                ...
            }
        Covers all batters with >= 10 PA. One HTTP call for all 30 teams.
        """
        yr = season or CURRENT_SEASON
        result = {}
        url = (
            "https://baseballsavant.mlb.com/leaderboard/statcast"
            f"?type=batter&year={yr}&position=&team=&min=10&csv=true"
        )
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": "StatScout/1.0"})
            r.raise_for_status()
            reader = csv.DictReader(io.StringIO(r.text))
            for row in reader:
                try:
                    pid = int(row.get("player_id") or row.get("batter") or 0)
                    if not pid:
                        continue
                    entry = {}
                    for col, key, cast in [
                        ("barrel_batted_rate", "barrelPct",  float),
                        ("hard_hit_percent",   "hardHitPct", float),
                        ("xba",                "xba",        float),
                        ("launch_speed",       "exitVelo",   float),
                    ]:
                        val = row.get(col, "").strip()
                        if val:
                            try:
                                entry[key] = round(cast(val), 3)
                            except ValueError:
                                pass
                    if entry:
                        result[pid] = entry
                except Exception:
                    continue
            print(f"[Savant] Loaded Statcast data for {len(result)} batters (season {yr})")
        except Exception as e:
            print(f"[Savant] Statcast CSV fetch failed: {e}")
        return result

    def fetch_all(self):
        """Main entry: returns list of MLB game cards."""
        try:
            print("[MLB] Fetching 2025 historical results from MLB Stats API...")
            games = self.get_historical_results()
            print(f"[MLB] {len(games)} historical games")
            team_stats = self.build_team_stats(games)
        except Exception as e:
            print(f"[MLB] Historical stats unavailable ({e}), continuing with odds only")
            team_stats = {}

        try:
            print("[MLB] Fetching upcoming odds from The Odds API...")
            upcoming = self.get_upcoming_odds()
            print(f"[MLB] {len(upcoming)} upcoming games from Odds API")
        except Exception as e:
            print(f"[MLB] Odds unavailable: {e}")
            return []

        try:
            print("[MLB] Fetching probable pitchers...")
            probable_pitchers = self.get_probable_pitchers_with_stats()
            print(f"[MLB] {len(probable_pitchers)} probable pitchers found")
        except Exception as e:
            print(f"[MLB] Probable pitcher fetch failed: {e}")
            probable_pitchers = {}

        cards = self.build_game_cards(upcoming, team_stats, probable_pitchers)
        print(f"[MLB] Built {len(cards)} game cards")
        return cards


mlb_fetcher_instance = MLBFetcher()
