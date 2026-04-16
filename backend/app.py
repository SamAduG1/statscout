"""
StatScout Flask API Server
Serves player prop data and analytics to the frontend
Includes halftime betting projections and live stat tracking
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from calculator import StatScoutCalculator
from db_loader import DatabaseLoader as DataLoader
from odds_api import OddsAPIClient
from nba_schedule_fetcher import NBAScheduleFetcher
from team_quarter_analytics import TeamQuarterAnalytics
from espn_injury_tracker import ESPNInjuryTracker
from parlay_builder import ParlayBuilder
from soccer_fetcher import SoccerFetcher
from mlb_fetcher import mlb_fetcher_instance
from datetime import datetime, timedelta
import random
import json
import os

CACHE_FILE = "/tmp/statscout_players_cache.json"

def _save_cache_to_disk(data):
    """Persist cache to /tmp so worker restarts load it instantly"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[CACHE] Failed to persist to disk: {e}")

def _load_cache_from_disk():
    """Load cache from /tmp if available - survives gunicorn worker restarts"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
            if data.get('count', 0) > 0:
                print(f"[CACHE] Loaded from disk ({data['count']} props)")
                return data
    except Exception as e:
        print(f"[CACHE] Failed to load from disk: {e}")
    return None

def _save_specific_cache(path, data):
    try:
        with open(path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[CACHE] Failed to persist {path}: {e}")

def _load_specific_cache(path):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            if data.get('count', 0) >= 0:
                return data
    except Exception as e:
        print(f"[CACHE] Failed to load {path}: {e}")
    return None

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize injury tracker first (needed by calculator)
injury_tracker = ESPNInjuryTracker()

# Initialize calculator with injury tracker, data loader, odds API client, schedule fetcher, and quarter analytics
calc = StatScoutCalculator(injury_tracker=injury_tracker)
loader = DataLoader()
odds_client = OddsAPIClient()
schedule_fetcher = NBAScheduleFetcher()
quarter_analytics = TeamQuarterAnalytics()
parlay_builder = ParlayBuilder()
soccer_fetcher_instance = SoccerFetcher()

# Initialize background scheduler for automated updates
from scheduler import init_scheduler
scheduler = init_scheduler()

# Cache for odds data (optimized to conserve API quota)
ODDS_CACHE_FILE = "/tmp/statscout_odds_cache.json"
_odds_disk = _load_specific_cache(ODDS_CACHE_FILE)
odds_cache = {
    "data": _odds_disk.get("data", {}) if _odds_disk else {},
    "last_updated": datetime.fromisoformat(_odds_disk["ts"]) if _odds_disk and "ts" in _odds_disk else None,
}

# Cache for players response (prevents Render 30s proxy timeout)
# Load from disk immediately - survives gunicorn worker restarts within the same deploy
_disk_cache = _load_cache_from_disk()
players_cache = {
    "data": _disk_cache,
    "last_updated": datetime.now() if _disk_cache else None,
    "building": False
}
PLAYERS_CACHE_DURATION = 30 * 60  # 30 minutes

# MLB team season stats cache (pitching ERA + batting K/game per team)
# Refreshed every 6h alongside the game card cache.
_mlb_team_stats = {"data": {}, "last_updated": None}

def _get_mlb_team_stats():
    """Return cached team stats, refreshing if older than 6 hours."""
    now = datetime.now()
    if (_mlb_team_stats["last_updated"] is None or
            (now - _mlb_team_stats["last_updated"]).total_seconds() > 6 * 3600):
        try:
            data = mlb_fetcher_instance.get_team_season_stats()
            if data:
                _mlb_team_stats["data"] = data
                _mlb_team_stats["last_updated"] = now
                print(f"[MLB] Team season stats refreshed ({len(data)} teams)")
        except Exception as e:
            print(f"[MLB] Team stats refresh failed: {e}")
    return _mlb_team_stats["data"]

# MLB match cache
MLB_CACHE_FILE = "/tmp/statscout_mlb_cache.json"
MLB_CACHE_DURATION = 6 * 60 * 60  # 6 hours
_mlb_cache_disk = _load_specific_cache(MLB_CACHE_FILE)
mlb_cache = {"data": _mlb_cache_disk, "last_updated": datetime.now() if _mlb_cache_disk else None, "building": False}

# Soccer match cache - one entry per league
SOCCER_CACHE_DURATION = 24 * 60 * 60  # 24 hours (conserves Odds API quota)
SOCCER_CACHE_FILES = {
    "pl":         "/tmp/statscout_soccer_pl_v2_cache.json",
    "laliga":     "/tmp/statscout_soccer_laliga_v2_cache.json",
    "bundesliga": "/tmp/statscout_soccer_bundesliga_v2_cache.json",
    "seriea":     "/tmp/statscout_soccer_seriea_v2_cache.json",
    "ligue1":     "/tmp/statscout_soccer_ligue1_v2_cache.json",
}
def _init_soccer_cache(league):
    disk = _load_specific_cache(SOCCER_CACHE_FILES[league])
    return {"data": disk, "last_updated": datetime.now() if disk else None, "building": False}

soccer_caches = {league: _init_soccer_cache(league) for league in SOCCER_CACHE_FILES}

# Cache for raw stat values per player - used by /api/calculate to avoid DB queries
stats_cache = {}  # {player_name: {stat_type: [values...]}}


def _compute_players_data(team_filter='all', stat_filter='all', skip_injuries=False, skip_odds=False, _loader=None):
    """
    Core computation for player props - separated from request handling
    so it can be called from both the route and background threads.
    Pass _loader to use a thread-local loader instead of the global one.
    Returns the response dict (not a Flask response object).
    """
    local_loader = _loader if _loader is not None else loader
    players_list = []
    player_id = 1

    # Bulk load all players + stats in 2 DB queries (vs ~1944 with per-player queries)
    if team_filter == 'all' and stat_filter == 'all':
        bulk = local_loader.get_all_players_bulk()
        player_info_map = {p['name']: p for p in bulk['players']}
        all_stats_map = bulk['stats']
        all_dates_map = bulk.get('game_dates', {})
        stats_cache.update(all_stats_map)
        player_names = list(player_info_map.keys())
        all_teams = list(set(p['team'] for p in bulk['players']))
    else:
        player_info_map = None
        all_stats_map = None
        all_dates_map = {}
        player_names = local_loader.get_player_names()
        all_teams = local_loader.get_teams()

    if not skip_injuries:
        injury_tracker.get_all_injuries()
    team_game_cache = {}

    for player_name in player_names:
        if player_info_map is not None:
            player_info = player_info_map.get(player_name)
            all_stats = all_stats_map.get(player_name, {})
        else:
            player_info = local_loader.get_player_info(player_name)
            all_stats = local_loader.get_all_available_stats(player_name)
        if not player_info:
            continue
        team = player_info["team"]
        if team_filter != 'all' and team != team_filter:
            continue
        all_dates = all_dates_map.get(player_name, [])
        for stat_type, stat_values in all_stats.items():
            if stat_type == 'three_pm':
                display_stat_type = '3PM'
            elif len(stat_type) <= 3:
                display_stat_type = stat_type.upper()
            else:
                display_stat_type = stat_type.title()
            if stat_filter != 'all' and display_stat_type.lower() != stat_filter.lower():
                continue
            if len(stat_values) < 3:
                continue
            avg_stat = sum(stat_values) / len(stat_values)
            cached_odds = None if skip_odds else get_cached_odds()
            odds_key = f"{player_name}_{display_stat_type}"
            bookmaker_lines = []
            is_real_line = False
            if cached_odds and odds_key in cached_odds:
                bookmaker_lines = cached_odds[odds_key]
                line = bookmaker_lines[0]["line"] if bookmaker_lines else STAT_LINES.get(display_stat_type, lambda x: round(x - 0.5, 1))(avg_stat)
                is_real_line = True if bookmaker_lines else False
            else:
                line = STAT_LINES.get(display_stat_type, lambda x: round(x - 0.5, 1))(avg_stat)
            if team not in team_game_cache:
                team_game_cache[team] = schedule_fetcher.get_player_next_game(team)
            next_game = team_game_cache[team]
            if next_game:
                opponent = next_game['opponent']
                is_home = next_game['is_home']
                game_date = next_game['game_date']
                game_time = next_game['game_time']
                opponent_rank = random.randint(5, 25)
            else:
                opponent = "TBD"
                opponent_rank = random.randint(5, 25)
                is_home = True
                game_date = "TBD"
                game_time = "TBD"
            analysis = calc.analyze_player_prop(
                player_name=player_name,
                team=team,
                stat_type=display_stat_type,
                player_stats=stat_values,
                line=line,
                opponent=opponent,
                opponent_rank=opponent_rank,
                is_home=is_home,
                db_loader=None
            )
            player_prop = {
                "id": player_id,
                "name": player_name,
                "team": team,
                "teamColor": TEAM_COLORS.get(team, "#000000"),
                "position": player_info["position"],
                "statType": display_stat_type,
                "line": line,
                "isRealLine": is_real_line,
                "bookmakerLines": bookmaker_lines,
                "hitRate": analysis["hit_rate"],
                "season_hits": analysis.get("season_hits"),
                "total_games": analysis.get("total_games"),
                "recent_hit_rate": analysis.get("recent_hit_rate"),
                "recent_hits": analysis.get("recent_hits"),
                "recent_total": analysis.get("recent_total"),
                "trustScore": analysis["trust_score"],
                "lastGames": analysis["last_games"],
                "last5Games": analysis["last_5_games"],
                "last15Games": analysis["last_15_games"],
                "lastGamesDates": all_dates[-10:] if len(all_dates) >= 10 else all_dates,
                "last5GamesDates": all_dates[-5:] if len(all_dates) >= 5 else all_dates,
                "last15GamesDates": all_dates[-15:] if len(all_dates) >= 15 else all_dates,
                "recentForm": analysis["recent_form"],
                "opponent": opponent,
                "opponentRank": opponent_rank,
                "opponentDefStat": get_opponent_def_stat(display_stat_type),
                "gameDate": game_date,
                "gameTime": game_time,
                "isHome": is_home,
                "avgLastN": analysis["avg_last_10"],
                "streak": analysis["streak"],
                "streakType": analysis["streak_type"],
                "avgMinutes": player_info.get("avg_minutes", 0)
            }
            players_list.append(player_prop)
            player_id += 1

    all_player_names = list(set([p["name"] for p in players_list]))
    if not skip_injuries:
        injury_statuses = injury_tracker.get_batch_status(all_player_names)
        for player in players_list:
            player_status = injury_statuses.get(player["name"], {"status": "ACTIVE", "source": "default"})
            player["injuryStatus"] = player_status["status"]
            player["injurySource"] = player_status.get("source", "default")
    else:
        for player in players_list:
            player["injuryStatus"] = "ACTIVE"
            player["injurySource"] = "default"

    return {
        "success": True,
        "count": len(players_list),
        "players": players_list
    }


def _build_players_cache_background():
    """Pre-warm players cache in background thread after startup"""
    import threading
    import time as _time

    def _run():
        players_cache["building"] = True

        # Each background build gets its own fresh loader to avoid sharing the global
        # session with request-handling threads (SQLAlchemy sessions are not thread-safe)
        _fresh_loader = DataLoader()

        # Phase 1: Fast build without injuries (~10-15s) - saves to disk before Render's
        # rolling deploy kills the pre-swap worker (~60s window)
        print("[CACHE] Phase 1: Building props (no injuries)...")
        for attempt in range(1, 4):
            try:
                data = _compute_players_data(skip_injuries=True, skip_odds=True, _loader=_fresh_loader)
                if data["count"] > 0:
                    players_cache["data"] = data
                    players_cache["last_updated"] = datetime.now()
                    _save_cache_to_disk(data)
                    print(f"[CACHE] Phase 1 complete ({data['count']} props, odds+injuries pending)")
                    break
                else:
                    print(f"[CACHE] Phase 1 attempt {attempt}: 0 props returned")
            except Exception as e:
                print(f"[CACHE] Phase 1 attempt {attempt} failed: {e}")
                # Recreate loader on failure in case the session is corrupt
                try:
                    _fresh_loader.session.close()
                except:
                    pass
                _fresh_loader = DataLoader()
            if attempt < 3:
                _time.sleep(10)

        players_cache["building"] = False

        # Phase 2: Refresh with real injury data (~60-90s) - runs after Phase 1 is saved
        if players_cache["data"] is not None:
            print("[CACHE] Phase 2: Fetching injury data...")
            try:
                data = _compute_players_data(skip_injuries=False, _loader=_fresh_loader)
                if data["count"] > 0:
                    players_cache["data"] = data
                    players_cache["last_updated"] = datetime.now()
                    _save_cache_to_disk(data)
                    print(f"[CACHE] Phase 2 complete (injuries updated)")
            except Exception as e:
                print(f"[CACHE] Phase 2 (injuries) failed: {e}")

        # Clean up the thread-local loader
        try:
            _fresh_loader.session.close()
        except:
            pass

    threading.Thread(target=_run, daemon=True).start()


def _build_soccer_cache_background(league='pl'):
    """Build soccer match cache for a league in a background thread."""
    import threading, time as _time
    cache = soccer_caches[league]

    def _run():
        cache["building"] = True
        for attempt in range(1, 4):
            try:
                data = soccer_fetcher_instance.fetch_all(competition=league)
                cache["data"] = data
                cache["last_updated"] = datetime.now()
                _save_specific_cache(SOCCER_CACHE_FILES[league], data)
                print(f"[SOCCER] {league} cache built ({data['count']} matches)")
                break
            except Exception as e:
                print(f"[SOCCER] {league} build attempt {attempt} failed: {e}")
                if attempt < 3:
                    _time.sleep(15)
        cache["building"] = False

    threading.Thread(target=_run, daemon=True).start()


# Cache configuration (in seconds)
CACHE_DURATION = 12 * 60 * 60  # 12 hours (conserves Odds API quota)
ACTIVE_HOURS_START = 6  # 6 AM
ACTIVE_HOURS_END = 23   # 11 PM

def is_active_hours():
    """Check if current time is during active hours (when odds should refresh)"""
    now = datetime.now()
    current_hour = now.hour
    return ACTIVE_HOURS_START <= current_hour < ACTIVE_HOURS_END

def get_cached_odds():
    """
    Get odds from cache or fetch new ones

    Optimization features:
    - 4-hour cache duration (reduced from 30 min)
    - Only refreshes during active hours (6 AM - 11 PM)
    - Saves ~75% of API requests
    """
    now = datetime.now()

    # Check if cache is expired
    cache_expired = (odds_cache["last_updated"] is None or
                     (now - odds_cache["last_updated"]).total_seconds() > CACHE_DURATION)

    # Only fetch if cache is expired AND we're in active hours
    # This prevents unnecessary API calls during late night/early morning
    if cache_expired and is_active_hours():
        print("[INFO] Fetching fresh odds from API...")
        print(f"[INFO] Cache age: {(now - odds_cache['last_updated']).total_seconds() / 3600:.1f} hours" if odds_cache["last_updated"] else "[INFO] First fetch")

        response = odds_client.get_all_player_props(
            markets="player_points,player_rebounds,player_assists,player_threes,player_steals,player_blocks"
        )

        if response.get("success"):
            parsed_props = odds_client.parse_player_props(response)

            # Store in cache by player name and stat type (with all bookmakers)
            odds_cache["data"] = {}
            for prop in parsed_props:
                key = f"{prop['player_name']}_{prop['stat_type']}"

                # Group by player+stat, keeping all bookmakers
                if key not in odds_cache["data"]:
                    odds_cache["data"][key] = []

                odds_cache["data"][key].append({
                    "bookmaker": prop["bookmaker"],
                    "line": prop["line"],
                    "over_odds": prop.get("over_odds"),
                    "under_odds": prop.get("under_odds")
                })

            odds_cache["last_updated"] = now
            _save_specific_cache(ODDS_CACHE_FILE, {"data": odds_cache["data"], "ts": now.isoformat()})
            print(f"[SUCCESS] Cached {len(parsed_props)} odds from {len(set(p['bookmaker'] for p in parsed_props))} bookmakers")
            print(f"[INFO] Next refresh after: {(now + timedelta(seconds=CACHE_DURATION)).strftime('%I:%M %p')}")
        else:
            print(f"[WARNING] Could not fetch odds: {response.get('error')}")
    elif cache_expired and not is_active_hours():
        pass  # Outside active hours - silently use stale cache (logged by caller if needed)
    else:
        pass  # Cache is fresh, no need to log every call

    return odds_cache["data"]

# DB connection verified async via background cache builder (avoids gunicorn worker timeout)

# Team color mapping (for frontend display)
TEAM_COLORS = {
    "LAL": "#552583", "GSW": "#1D428A", "BOS": "#007A33", "MIL": "#00471B",
    "DAL": "#00538C", "DEN": "#0E2240", "PHX": "#E56020", "PHI": "#006BB6",
    "MIA": "#98002E", "CHI": "#CE1141", "BKN": "#000000", "MIN": "#0C2340",
    "SAC": "#5A2D81", "POR": "#E03A3E", "LAC": "#C8102E", "UTA": "#002B5C",
    "MEM": "#5D76A9", "NOP": "#0C2340", "SAS": "#C4CED4", "HOU": "#CE1141",
    "OKC": "#007AC1", "ATL": "#E03A3E", "CLE": "#860038", "IND": "#002D62",
    "DET": "#C8102E", "TOR": "#CE1141", "WAS": "#002B5C", "CHA": "#1D1160",
    "ORL": "#0077C0", "NYK": "#006BB6"
}

# Betting lines for each stat type (these would come from an API in production)
STAT_LINES = {
    "Points": lambda avg: round(avg * 2) / 2,  # Round to nearest .5
    "Rebounds": lambda avg: round(avg * 2) / 2,
    "Assists": lambda avg: round(avg * 2) / 2,
    "Steals": lambda avg: round(avg * 2) / 2,
    "Blocks": lambda avg: round(avg * 2) / 2,
    "3PM": lambda avg: round(avg * 2) / 2,
    "PRA": lambda avg: round(avg * 2) / 2,  # Points + Rebounds + Assists
    "PA": lambda avg: round(avg * 2) / 2,   # Points + Assists
    "PR": lambda avg: round(avg * 2) / 2,   # Points + Rebounds
    "RA": lambda avg: round(avg * 2) / 2    # Rebounds + Assists
}

# Map stat names to CSV columns
STAT_COLUMN_MAP = {
    "Points": "points",
    "Rebounds": "rebounds",
    "Assists": "assists",
    "Steals": "steals",
    "Blocks": "blocks",
    "3PM": "three_pm"
}


def generate_game_info():
    """Generate mock game date/time"""
    base_date = datetime.now()
    game_date = base_date + timedelta(days=random.randint(0, 2))
    hours = [19, 19.5, 20, 20.5, 21]  # 7PM, 7:30PM, 8PM, etc.
    game_hour = random.choice(hours)
    
    hour = int(game_hour)
    minute = 30 if (game_hour % 1) else 0
    
    date_str = game_date.strftime("%b %d, %Y")
    time_str = f"{hour}:{minute:02d} PM"
    
    return date_str, time_str


def get_opponent_def_stat(stat_type: str) -> str:
    """Generate opponent defensive stat string"""
    if stat_type == "Points":
        return f"{random.randint(105, 120)}.{random.randint(0, 9)} PPG"
    elif stat_type == "Rebounds":
        return f"{random.randint(40, 50)}.{random.randint(0, 9)} RPG"
    elif stat_type == "Assists":
        return f"{random.randint(20, 28)}.{random.randint(0, 9)} APG"
    elif stat_type == "3PM":
        return f"{random.randint(10, 15)}.{random.randint(0, 9)} 3PM"
    else:
        return f"{random.randint(30, 60)}.{random.randint(0, 9)} Total"


@app.route('/api/odds/status', methods=['GET'])
def odds_status():
    """Check odds API status and cache info"""
    usage = odds_client.check_usage()

    now = datetime.now()
    cache_age_hours = None
    next_refresh = None

    if odds_cache["last_updated"]:
        cache_age_hours = (now - odds_cache["last_updated"]).total_seconds() / 3600
        next_refresh_time = odds_cache["last_updated"] + timedelta(seconds=CACHE_DURATION)
        next_refresh = next_refresh_time.isoformat()

    return jsonify({
        "success": True,
        "api_status": usage,
        "cache": {
            "props_cached": len(odds_cache["data"]),
            "last_updated": odds_cache["last_updated"].isoformat() if odds_cache["last_updated"] else None,
            "cache_age_hours": round(cache_age_hours, 2) if cache_age_hours else None,
            "next_refresh": next_refresh,
            "cache_duration_hours": CACHE_DURATION / 3600,
            "active_hours": f"{ACTIVE_HOURS_START}:00 - {ACTIVE_HOURS_END}:00",
            "is_active_hours": is_active_hours()
        }
    })


@app.route('/api/odds/refresh', methods=['POST'])
def refresh_odds():
    """Force refresh odds cache"""
    odds_cache["last_updated"] = None  # Invalidate cache
    cached_odds = get_cached_odds()
    
    return jsonify({
        "success": True,
        "message": "Odds cache refreshed",
        "props_cached": len(cached_odds)
    })


SOCCER_PLAYERS_CACHE_DURATION = 12 * 60 * 60  # 12 hours

# Understat team name -> Odds API team name (for fixture matching)
UNDERSTAT_TO_ODDS_PL = {
    "Manchester City":        "Manchester City",
    "Arsenal":                "Arsenal",
    "Liverpool":              "Liverpool",
    "Chelsea":                "Chelsea",
    "Tottenham":              "Tottenham Hotspur",
    "Aston Villa":            "Aston Villa",
    "Newcastle United":       "Newcastle United",
    "Manchester United":      "Manchester United",
    "West Ham":               "West Ham United",
    "Brighton":               "Brighton and Hove Albion",
    "Wolverhampton Wanderers":"Wolves",
    "Fulham":                 "Fulham",
    "Bournemouth":            "Bournemouth",
    "Nottingham Forest":      "Nottingham Forest",
    "Crystal Palace":         "Crystal Palace",
    "Brentford":              "Brentford",
    "Everton":                "Everton",
    "Leicester":              "Leicester City",
    "Ipswich":                "Ipswich Town",
    "Southampton":            "Southampton",
    "Leeds":                  "Leeds United",
    "Burnley":                "Burnley",
    "Sunderland":             "Sunderland",
}

UNDERSTAT_TO_ODDS_LALIGA = {
    "Barcelona":              "Barcelona",
    "Real Madrid":            "Real Madrid",
    "Atletico Madrid":        "Atletico Madrid",
    "Athletic Club":          "Athletic Club Bilbao",
    "Real Sociedad":          "Real Sociedad",
    "Villarreal":             "Villarreal",
    "Real Betis":             "Real Betis",
    "Valencia":               "Valencia",
    "Sevilla":                "Sevilla",
    "Osasuna":                "Osasuna",
    "Celta Vigo":             "Celta Vigo",
    "Getafe":                 "Getafe",
    "Espanyol":               "Espanyol",
    "Mallorca":               "Mallorca",
    "Las Palmas":             "Las Palmas",
    "Rayo Vallecano":         "Rayo Vallecano",
    "Alaves":                 "Alaves",
    "Leganes":                "Leganes",
    "Real Valladolid":        "Valladolid",
    "Real Oviedo":            "Oviedo",
    "Levante":                "Levante UD",
    "Elche":                  "Elche CF",
}

UNDERSTAT_TO_ODDS_BUNDESLIGA = {
    "Bayern Munich":          "Bayern Munich",
    "Borussia Dortmund":      "Borussia Dortmund",
    "Bayer Leverkusen":       "Bayer Leverkusen",
    "RasenBallsport Leipzig": "RB Leipzig",
    "Eintracht Frankfurt":    "Eintracht Frankfurt",
    "VfB Stuttgart":          "VfB Stuttgart",
    "Wolfsburg":              "VfL Wolfsburg",
    "Freiburg":               "SC Freiburg",
    "Borussia M.Gladbach":    "Borussia Monchengladbach",
    "Augsburg":               "Augsburg",
    "FC Heidenheim":          "1. FC Heidenheim",
    "Werder Bremen":          "Werder Bremen",
    "Mainz 05":               "FSV Mainz 05",
    "Hoffenheim":             "TSG Hoffenheim",
    "Union Berlin":           "Union Berlin",
    "St. Pauli":              "FC St. Pauli",
    "Hamburger SV":           "Hamburger SV",
    "FC Cologne":             "1. FC Köln",
}

UNDERSTAT_TO_ODDS_SERIEA = {
    "Juventus":               "Juventus",
    "Inter":                  "Inter Milan",
    "AC Milan":               "AC Milan",
    "Roma":                   "AS Roma",
    "Napoli":                 "Napoli",
    "Lazio":                  "Lazio",
    "Fiorentina":             "Fiorentina",
    "Atalanta":               "Atalanta BC",
    "Bologna":                "Bologna",
    "Torino":                 "Torino",
    "Udinese":                "Udinese",
    "Genoa":                  "Genoa",
    "Cagliari":               "Cagliari",
    "Lecce":                  "Lecce",
    "Verona":                 "Hellas Verona",
    "Parma Calcio 1913":      "Parma",
    "Como":                   "Como",
    "Cremonese":              "Cremonese",
    "Pisa":                   "Pisa",
    "Sassuolo":               "Sassuolo",
}

UNDERSTAT_TO_ODDS_LIGUE1 = {
    "Paris Saint Germain":    "Paris Saint Germain",
    "Monaco":                 "AS Monaco",
    "Marseille":              "Marseille",
    "Lyon":                   "Lyon",
    "Lille":                  "Lille",
    "Nice":                   "Nice",
    "Lens":                   "RC Lens",
    "Rennes":                 "Rennes",
    "Strasbourg":             "Strasbourg",
    "Nantes":                 "Nantes",
    "Toulouse":               "Toulouse",
    "Brest":                  "Brest",
    "Le Havre":               "Le Havre",
    "Auxerre":                "Auxerre",
    "Angers":                 "Angers",
    "Metz":                   "Metz",
    "Lorient":                "Lorient",
    "Paris FC":               "Paris FC",
}

LEAGUE_MAPPINGS = {
    "pl":         UNDERSTAT_TO_ODDS_PL,
    "laliga":     UNDERSTAT_TO_ODDS_LALIGA,
    "bundesliga": UNDERSTAT_TO_ODDS_BUNDESLIGA,
    "seriea":     UNDERSTAT_TO_ODDS_SERIEA,
    "ligue1":     UNDERSTAT_TO_ODDS_LIGUE1,
}


def _compute_soccer_players(league, home_team_odds, away_team_odds):
    """
    Compute player props for both teams in a fixture.
    home_team_odds / away_team_odds are the Odds API team names.
    Returns dict with players list and hit rates per market.
    """
    from models import get_engine, get_session, SoccerPlayer, SoccerPlayerGame
    from soccer_fetcher import _norm

    mapping = LEAGUE_MAPPINGS.get(league, UNDERSTAT_TO_ODDS_PL)
    # Reverse the mapping: Odds API name -> Understat name
    odds_to_understat = {v.lower(): k for k, v in mapping.items()}

    def resolve(odds_name):
        return odds_to_understat.get(_norm(odds_name).lower(), odds_name)

    home_us = resolve(home_team_odds)
    away_us = resolve(away_team_odds)

    engine = get_engine()
    session = get_session(engine)

    def hit_rate(values, line):
        if not values:
            return None
        return round(sum(1 for v in values if v > line) / len(values) * 100)

    def safe_avg(arr):
        return round(sum(arr) / len(arr), 2) if arr else None

    def venue_split(gs, venue_val):
        gs_v = [g for g in gs if g.venue == venue_val]
        if not gs_v:
            return None
        return {
            "goals":   safe_avg([g.goals for g in gs_v]),
            "shots":   safe_avg([g.shots for g in gs_v]),
            "assists": safe_avg([g.assists for g in gs_v]),
            "games":   len(gs_v),
        }

    def opp_def_vs_position(opp_team_us, position, league_code):
        """
        How many goals / shots do players of 'position' avg per game against opp_team_us?
        Queries all players in the league who have faced this opponent.
        Returns dict {avg_goals, avg_shots, sample_size} or None if <5 games found.
        """
        try:
            rows = (
                session.query(SoccerPlayerGame)
                .join(SoccerPlayer, SoccerPlayer.id == SoccerPlayerGame.player_id)
                .filter(
                    SoccerPlayer.league == league_code,
                    SoccerPlayer.position == position,
                    SoccerPlayerGame.opponent.ilike(f"%{opp_team_us}%"),
                    SoccerPlayerGame.minutes_played > 0,
                )
                .all()
            )
            if len(rows) < 5:
                return None
            avg_g = round(sum(r.goals for r in rows) / len(rows), 2)
            avg_s = round(sum(r.shots for r in rows) / len(rows), 2)
            return {"avgGoals": avg_g, "avgShots": avg_s, "sampleSize": len(rows)}
        except Exception:
            return None

    try:
        players_out = []
        for team_odds, team_us, side in [
            (home_team_odds, home_us, "home"),
            (away_team_odds, away_us, "away"),
        ]:
            opp_us   = away_us   if side == "home" else home_us
            opp_odds = away_team_odds if side == "home" else home_team_odds

            # Try exact match, then case-insensitive fallback
            players = session.query(SoccerPlayer).filter(
                SoccerPlayer.league == league,
                SoccerPlayer.team_name == team_us,
            ).all()
            if not players:
                players = session.query(SoccerPlayer).filter(
                    SoccerPlayer.league == league,
                    SoccerPlayer.team_name.ilike(team_us),
                ).all()

            for p in players:
                all_games = (
                    session.query(SoccerPlayerGame)
                    .filter_by(player_id=p.id)
                    .order_by(SoccerPlayerGame.match_date.asc())
                    .all()
                )
                games_prev = [g for g in all_games if g.season == '2024' and g.minutes_played > 0]
                games_curr = [g for g in all_games if g.season == '2025' and g.minutes_played > 0]
                active = games_curr  # current season for display/splits
                if len(active) < 3 and len(games_prev) < 3:
                    continue
                if not active:
                    active = games_prev

                goals   = [g.goals for g in active]
                shots   = [g.shots for g in active]
                assists = [g.assists for g in active]
                ga      = [g.goals + g.assists for g in active]
                mins    = [g.minutes_played for g in active]

                # xG and xA arrays (current season, filtering None)
                xg_curr  = [g.xG for g in games_curr if g.xG is not None]
                xa_curr  = [g.xA for g in games_curr if g.xA is not None]
                xg_prev  = [g.xG for g in games_prev if g.xG is not None]
                xa_prev  = [g.xA for g in games_prev if g.xA is not None]

                # H2H: games against tonight's opponent
                h2h = [g for g in active if opp_us.lower() in (g.opponent or "").lower()]

                game_log = [
                    {
                        "date":          g.match_date.isoformat(),
                        "opponent":      g.opponent,
                        "venue":         g.venue,
                        "goals":         g.goals,
                        "shots":         g.shots,
                        "assists":       g.assists,
                        "minutesPlayed": g.minutes_played,
                        "xG":            g.xG,
                        "xA":            g.xA,
                    }
                    for g in active[-15:]
                ]
                h2h_log = [
                    {
                        "date":          g.match_date.isoformat(),
                        "opponent":      g.opponent,
                        "venue":         g.venue,
                        "goals":         g.goals,
                        "shots":         g.shots,
                        "assists":       g.assists,
                        "minutesPlayed": g.minutes_played,
                    }
                    for g in h2h[-8:]
                ]

                player_dict = {
                    "id":           p.id,
                    "understatId":  p.understat_id,
                    "name":         p.name,
                    "team":         team_odds,
                    "teamSide":     side,
                    "position":     p.position,
                    "gamesPlayed":  len(active),
                    "gamesCurr":    len(games_curr),
                    "avgMinutes":   round(sum(mins) / len(mins), 1) if mins else 0,
                    "opponent":     opp_odds,
                    # Goals
                    "goals_over05":   hit_rate(goals, 0.5),
                    "goals_over15":   hit_rate(goals, 1.5),
                    # Shots
                    "shots_over15":   hit_rate(shots, 1.5),
                    "shots_over25":   hit_rate(shots, 2.5),
                    # Assists
                    "assists_over05": hit_rate(assists, 0.5),
                    # Score or Assist
                    "ga_over05":      hit_rate(ga, 0.5),
                    "ga_over15":      hit_rate(ga, 1.5),
                    # GK
                    "cleanSheet": None,
                    "gcArr": [],
                    # Raw arrays (current season, last 15 games oldest first)
                    "goalsArr":   goals[-15:],
                    "shotsArr":   shots[-15:],
                    "assistsArr": assists[-15:],
                    "gaArr":      ga[-15:],
                    # xG/xA arrays for blended trust (current + prior season)
                    "xgArr":      xg_curr[-15:],
                    "xaArr":      xa_curr[-15:],
                    "xgArrPrev":  xg_prev,
                    "xaArrPrev":  xa_prev,
                    "goalsPrev":  [g.goals for g in games_prev],
                    "shotsPrev":  [g.shots for g in games_prev],
                    "assistsPrev":[g.assists for g in games_prev],
                    # Detail data
                    "gameLog":    game_log,
                    "h2hGames":   h2h_log,
                    "homeSplit":  venue_split(active, "home"),
                    "awaySplit":  venue_split(active, "away"),
                }

                # Opponent defense vs this player's position
                player_dict["oppDefense"] = opp_def_vs_position(opp_us, p.position, league)

                # GK: clean sheet % + goals conceded array
                if p.position == "GK":
                    gk_conceded = [g.goals_conceded for g in active if g.goals_conceded is not None]
                    if gk_conceded:
                        player_dict["cleanSheet"] = round(
                            sum(1 for v in gk_conceded if v == 0) / len(gk_conceded) * 100
                        )
                        player_dict["gcArr"] = gk_conceded[-15:]

                players_out.append(player_dict)

        players_out.sort(key=lambda p: (-p["gamesPlayed"], p["name"]))
        return {
            "success":  True,
            "league":   league,
            "homeTeam": home_team_odds,
            "awayTeam": away_team_odds,
            "count":    len(players_out),
            "players":  players_out,
        }
    finally:
        session.close()


SOCCER_ALL_PLAYERS_CACHE_FILES = {
    lg: f"/tmp/ssp_all_{lg}_v1.json" for lg in LEAGUE_MAPPINGS
}
SOCCER_ALL_PLAYERS_CACHE_DURATION = 12 * 60 * 60  # 12 hours

_soccer_all_players_caches = {lg: None for lg in LEAGUE_MAPPINGS}


def _compute_soccer_players_all(league):
    """
    Compute player props for ALL players in a league — no fixture required.
    Like /api/mlb/players/all: returns every player with their season arrays,
    hit rates, and avg stats. No oppDefense (no opponent context).
    Cached per league.
    """
    from models import get_engine, get_session, SoccerPlayer, SoccerPlayerGame

    engine = get_engine()
    session = get_session(engine)

    mapping = LEAGUE_MAPPINGS.get(league, UNDERSTAT_TO_ODDS_PL)
    # understat_name -> odds_name
    us_to_odds = {k: v for k, v in mapping.items()}

    def hit_rate(values, line):
        if not values:
            return None
        return round(sum(1 for v in values if v > line) / len(values) * 100)

    def safe_avg(arr):
        return round(sum(arr) / len(arr), 2) if arr else None

    def venue_split(gs, venue_val):
        gs_v = [g for g in gs if g.venue == venue_val]
        if not gs_v:
            return None
        return {
            "goals":   safe_avg([g.goals for g in gs_v]),
            "shots":   safe_avg([g.shots for g in gs_v]),
            "assists": safe_avg([g.assists for g in gs_v]),
            "games":   len(gs_v),
        }

    try:
        all_players = session.query(SoccerPlayer).filter_by(league=league).all()
        players_out = []

        for p in all_players:
            all_games = (
                session.query(SoccerPlayerGame)
                .filter_by(player_id=p.id)
                .order_by(SoccerPlayerGame.match_date.asc())
                .all()
            )
            games_prev = [g for g in all_games if g.season == '2024' and g.minutes_played > 0]
            games_curr = [g for g in all_games if g.season == '2025' and g.minutes_played > 0]
            active = games_curr
            if len(active) < 3 and len(games_prev) < 3:
                continue
            if not active:
                active = games_prev

            goals   = [g.goals for g in active]
            shots   = [g.shots for g in active]
            assists = [g.assists for g in active]
            ga      = [g.goals + g.assists for g in active]
            mins    = [g.minutes_played for g in active]

            xg_curr = [g.xG for g in games_curr if g.xG is not None]
            xa_curr = [g.xA for g in games_curr if g.xA is not None]
            xg_prev = [g.xG for g in games_prev if g.xG is not None]
            xa_prev = [g.xA for g in games_prev if g.xA is not None]

            # Odds API team name for display
            team_odds = us_to_odds.get(p.team_name, p.team_name)

            player_dict = {
                "id":           p.id,
                "understatId":  p.understat_id,
                "name":         p.name,
                "team":         team_odds,
                "teamUs":       p.team_name,
                "position":     p.position,
                "gamesPlayed":  len(active),
                "gamesCurr":    len(games_curr),
                "avgMinutes":   round(sum(mins) / len(mins), 1) if mins else 0,
                "goals_over05":   hit_rate(goals, 0.5),
                "goals_over15":   hit_rate(goals, 1.5),
                "shots_over15":   hit_rate(shots, 1.5),
                "shots_over25":   hit_rate(shots, 2.5),
                "assists_over05": hit_rate(assists, 0.5),
                "ga_over05":      hit_rate(ga, 0.5),
                "ga_over15":      hit_rate(ga, 1.5),
                "cleanSheet": None,
                "gcArr": [],
                "goalsArr":   goals[-15:],
                "shotsArr":   shots[-15:],
                "assistsArr": assists[-15:],
                "gaArr":      ga[-15:],
                "xgArr":      xg_curr[-15:],
                "xaArr":      xa_curr[-15:],
                "xgArrPrev":  xg_prev,
                "xaArrPrev":  xa_prev,
                "goalsPrev":  [g.goals for g in games_prev],
                "shotsPrev":  [g.shots for g in games_prev],
                "assistsPrev":[g.assists for g in games_prev],
                "gameLog":    [
                    {
                        "date":          g.match_date.isoformat(),
                        "opponent":      g.opponent,
                        "venue":         g.venue,
                        "goals":         g.goals,
                        "shots":         g.shots,
                        "assists":       g.assists,
                        "minutesPlayed": g.minutes_played,
                        "xG":            g.xG,
                        "xA":            g.xA,
                    }
                    for g in active[-15:]
                ],
                "h2hGames":   [],
                "homeSplit":  venue_split(active, "home"),
                "awaySplit":  venue_split(active, "away"),
                "oppDefense": None,  # requires opponent context; filled in by fixture view
            }

            if p.position == "GK":
                gk_conceded = [g.goals_conceded for g in active if g.goals_conceded is not None]
                if gk_conceded:
                    player_dict["cleanSheet"] = round(
                        sum(1 for v in gk_conceded if v == 0) / len(gk_conceded) * 100
                    )
                    player_dict["gcArr"] = gk_conceded[-15:]

            players_out.append(player_dict)

        players_out.sort(key=lambda pl: (-pl["gamesPlayed"], pl["name"]))
        return {
            "success": True,
            "league":  league,
            "count":   len(players_out),
            "players": players_out,
        }
    finally:
        session.close()


def _build_soccer_all_players_cache_background(league):
    import threading, time as _time
    def _run():
        for attempt in range(1, 4):
            try:
                data = _compute_soccer_players_all(league)
                data['ts'] = datetime.now().isoformat()
                _soccer_all_players_caches[league] = data
                if data['count'] > 0:
                    _save_specific_cache(SOCCER_ALL_PLAYERS_CACHE_FILES[league], data)
                    print(f"[SOCCER PLAYERS ALL] {league}: {data['count']} players cached")
                break
            except Exception as e:
                print(f"[SOCCER PLAYERS ALL] {league} attempt {attempt} failed: {e}")
                if attempt < 3:
                    _time.sleep(15)
    threading.Thread(target=_run, daemon=True).start()


@app.route('/api/soccer/players/all', methods=['GET'])
def get_soccer_players_all():
    """
    Return props for ALL players in a league — no fixture required. Cached 12h.
    Query params: league=pl|laliga|bundesliga|seriea|ligue1
    """
    league = request.args.get('league', 'pl')
    if league not in LEAGUE_MAPPINGS:
        return jsonify({"error": "Unknown league"}), 400

    # In-memory first
    cached = _soccer_all_players_caches.get(league)
    if cached and cached.get('count', 0) > 0:
        ts = cached.get('ts')
        if ts:
            age = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
            if age < SOCCER_ALL_PLAYERS_CACHE_DURATION:
                return jsonify(cached)

    # Disk fallback
    disk = _load_specific_cache(SOCCER_ALL_PLAYERS_CACHE_FILES.get(league, ''))
    if disk and disk.get('count', 0) > 0:
        ts = disk.get('ts')
        if ts:
            age = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
            if age < SOCCER_ALL_PLAYERS_CACHE_DURATION:
                _soccer_all_players_caches[league] = disk
                return jsonify(disk)

    # Build in background, return empty for now
    _build_soccer_all_players_cache_background(league)
    return jsonify({"success": True, "league": league, "count": 0, "players": []})


@app.route('/api/soccer/players', methods=['GET'])
def get_soccer_players():
    """
    Get player props for an upcoming fixture.
    Query params: league=pl|laliga, home_team=..., away_team=...
    (home_team / away_team must match Odds API team names from /api/soccer/matches)
    """
    league     = request.args.get('league', 'pl')
    home_team  = request.args.get('home_team', '').strip()
    away_team  = request.args.get('away_team', '').strip()

    if not home_team or not away_team:
        return jsonify({"error": "home_team and away_team are required"}), 400

    safe = lambda s: s.replace(' ', '_').replace('/', '-')
    cache_key = f"/tmp/ssp_v2_{league}_{safe(home_team)}_{safe(away_team)}.json"

    cached = _load_specific_cache(cache_key)
    if cached:
        ts = cached.get('ts')
        if ts:
            age = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
            if age < SOCCER_PLAYERS_CACHE_DURATION and cached.get('count', 0) > 0:
                return jsonify(cached)

    try:
        data = _compute_soccer_players(league, home_team, away_team)
        data['ts'] = datetime.now().isoformat()
        if data['count'] > 0:
            _save_specific_cache(cache_key, data)
        return jsonify(data)
    except Exception as e:
        print(f"[SOCCER PLAYERS] Error: {e}")
        return jsonify({"success": False, "error": str(e), "count": 0, "players": []}), 500


MLB_PLAYERS_CACHE_DURATION = 6 * 60 * 60  # 6 hours (matches MLB game cache TTL)


def _compute_mlb_players(home_team_odds, away_team_odds):
    """
    Query DB for players on both teams and build props arrays + detail data.
    home_team_odds / away_team_odds are Odds API team names (same as game cards).
    """
    from models import get_engine, get_session, MLBPlayer, MLBPlayerGame
    from mlb_fetcher import ODDS_TO_MLB

    home_mlb = ODDS_TO_MLB.get(home_team_odds, home_team_odds)
    away_mlb = ODDS_TO_MLB.get(away_team_odds, away_team_odds)

    engine = get_engine()
    session = get_session(engine)

    def safe_avg(arr):
        return round(sum(arr) / len(arr), 2) if arr else None

    def batter_splits(gs):
        if not gs:
            return None
        return {
            "hits":       safe_avg([g.hits for g in gs if g.hits is not None]),
            "homeRuns":   safe_avg([g.home_runs for g in gs if g.home_runs is not None]),
            "rbi":        safe_avg([g.rbi for g in gs if g.rbi is not None]),
            "totalBases": safe_avg([g.total_bases for g in gs if g.total_bases is not None]),
            "games":      len(gs),
        }

    # Fetch team season stats for defense modifiers (cached, refreshes every 6h)
    team_season_stats = _get_mlb_team_stats()

    # Fetch MLB injury data (2h cache via ESPN tracker)
    try:
        mlb_injuries = injury_tracker.get_mlb_injuries()
    except Exception:
        mlb_injuries = {}

    try:
        players_out = []
        for team_odds, team_mlb, side in [
            (home_team_odds, home_mlb, "home"),
            (away_team_odds, away_mlb, "away"),
        ]:
            opp_mlb  = away_mlb  if side == "home" else home_mlb
            opp_odds = away_team_odds if side == "home" else home_team_odds

            # Opposing team defense stats for trust modifiers
            opp_stats      = team_season_stats.get(opp_mlb, {})
            opp_team_era   = opp_stats.get("era")        # for batters: opp pitching ERA
            opp_lineup_kpg = opp_stats.get("kPerGame")   # for pitchers: how often opp lineup Ks
            # Own team run environment — for RBI/Runs market reliability
            own_stats         = team_season_stats.get(team_mlb, {})
            team_runs_per_game = own_stats.get("runsPerGame")

            players = session.query(MLBPlayer).filter(MLBPlayer.team == team_mlb).all()
            if not players:
                players = session.query(MLBPlayer).filter(MLBPlayer.team.ilike(team_mlb)).all()

            for p in players:
                all_games = (
                    session.query(MLBPlayerGame)
                    .filter_by(player_id=p.id)
                    .order_by(MLBPlayerGame.game_date.asc())
                    .all()
                )
                if len(all_games) < 5:
                    continue

                recent = all_games[-20:]
                h2h = [g for g in all_games if opp_mlb.lower() in (g.opponent or "").lower()]

                if p.is_pitcher:
                    ks   = [g.strikeouts for g in recent if g.strikeouts is not None]
                    outs = [g.outs_recorded for g in recent if g.outs_recorded is not None]
                    if len(ks) < 5:
                        continue

                    home_g = [g for g in all_games if g.is_home and g.strikeouts is not None]
                    away_g = [g for g in all_games if not g.is_home and g.strikeouts is not None]

                    game_log = [
                        {
                            "date":           g.game_date.isoformat(),
                            "opponent":       g.opponent,
                            "isHome":         g.is_home,
                            "strikeouts":     g.strikeouts,
                            "inningsPitched": g.innings_pitched,
                            "earnedRuns":     g.earned_runs,
                            "hitsAllowed":    g.hits_allowed,
                        }
                        for g in all_games[-15:]
                    ]
                    h2h_log = [
                        {
                            "date":           g.game_date.isoformat(),
                            "opponent":       g.opponent,
                            "isHome":         g.is_home,
                            "strikeouts":     g.strikeouts,
                            "inningsPitched": g.innings_pitched,
                            "earnedRuns":     g.earned_runs,
                        }
                        for g in h2h[-8:]
                    ]

                    player_dict = {
                        "id":          p.id,
                        "name":        p.name,
                        "team":        team_odds,
                        "teamSide":    side,
                        "position":    p.position,
                        "isPitcher":   True,
                        "gamesPlayed": len(all_games),
                        "opponent":      opp_odds,
                        "strikeoutsArr": ks,
                        "outsArr":       outs,
                        "avgKs":         safe_avg(ks),
                        "homeAvgKs":     safe_avg([g.strikeouts for g in home_g]),
                        "awayAvgKs":     safe_avg([g.strikeouts for g in away_g]),
                        "homeGames":     len(home_g),
                        "awayGames":     len(away_g),
                        "gameLog":       game_log,
                        "h2hGames":      h2h_log,
                        # Opposing lineup K/game — pitchers want lineups that strike out a lot
                        "oppLineupKPG":  opp_lineup_kpg,
                        "injuryStatus":  mlb_injuries.get(p.name, {}).get("status", "ACTIVE"),
                        "injuryDetail":  mlb_injuries.get(p.name, {}).get("injury"),
                    }

                else:
                    hits = [g.hits for g in recent if g.hits is not None]
                    hrs  = [g.home_runs for g in recent if g.home_runs is not None]
                    rbi  = [g.rbi for g in recent if g.rbi is not None]
                    runs = [g.runs for g in recent if g.runs is not None]
                    tb   = [g.total_bases for g in recent if g.total_bases is not None]
                    hrr  = [
                        (g.hits or 0) + (g.runs or 0) + (g.rbi or 0)
                        for g in recent
                        if g.hits is not None and g.runs is not None and g.rbi is not None
                    ]
                    if len(hits) < 5:
                        continue

                    home_g = [g for g in all_games if g.is_home and g.hits is not None]
                    away_g = [g for g in all_games if not g.is_home and g.hits is not None]

                    game_log = [
                        {
                            "date":       g.game_date.isoformat(),
                            "opponent":   g.opponent,
                            "isHome":     g.is_home,
                            "hits":       g.hits,
                            "homeRuns":   g.home_runs,
                            "rbi":        g.rbi,
                            "runs":       g.runs,
                            "totalBases": g.total_bases,
                            "atBats":     g.at_bats,
                        }
                        for g in all_games[-15:]
                    ]
                    h2h_log = [
                        {
                            "date":       g.game_date.isoformat(),
                            "opponent":   g.opponent,
                            "isHome":     g.is_home,
                            "hits":       g.hits,
                            "homeRuns":   g.home_runs,
                            "rbi":        g.rbi,
                            "totalBases": g.total_bases,
                            "atBats":     g.at_bats,
                        }
                        for g in h2h[-8:]
                    ]

                    player_dict = {
                        "id":          p.id,
                        "name":        p.name,
                        "team":        team_odds,
                        "teamSide":    side,
                        "position":    p.position,
                        "isPitcher":   False,
                        "gamesPlayed": len(all_games),
                        "opponent":    opp_odds,
                        "hitsArr":       hits,
                        "homeRunsArr":   hrs,
                        "rbiArr":        rbi,
                        "runsArr":       runs,
                        "totalBasesArr": tb,
                        "hrrArr":        hrr,
                        "avgHits":       safe_avg(hits),
                        "avgTB":         safe_avg(tb),
                        "homeSplit":     batter_splits(home_g),
                        "awaySplit":     batter_splits(away_g),
                        "homeGames":     len(home_g),
                        "awayGames":     len(away_g),
                        "gameLog":       game_log,
                        "h2hGames":      h2h_log,
                        # Opposing team pitching ERA — batters face easier matchup vs high ERA staff
                        "oppTeamEra":      opp_team_era,
                        # Own team run environment — higher = more RBI/Runs opportunities
                        "teamRunsPerGame": team_runs_per_game,
                        # Batter handedness for platoon splits (L/R/S)
                        "bats":            p.bats,
                        "injuryStatus":    mlb_injuries.get(p.name, {}).get("status", "ACTIVE"),
                        "injuryDetail":    mlb_injuries.get(p.name, {}).get("injury"),
                    }

                players_out.append(player_dict)

        players_out.sort(key=lambda p: (-p["gamesPlayed"], p["name"]))
        return {
            "success":  True,
            "homeTeam": home_team_odds,
            "awayTeam": away_team_odds,
            "count":    len(players_out),
            "players":  players_out,
        }
    finally:
        session.close()


def _compute_all_mlb_players():
    """
    Build props arrays for every MLB player in the DB regardless of today's schedule.
    No opponent/teamSide context — h2hGames omitted. Used for the all-players view.
    """
    from models import get_engine, get_session, MLBPlayer, MLBPlayerGame
    from mlb_fetcher import ODDS_TO_MLB

    # Reverse map: MLB Stats API name -> Odds API name
    MLB_TO_ODDS = {v: k for k, v in ODDS_TO_MLB.items()}

    engine = get_engine()
    session = get_session(engine)

    def safe_avg(arr):
        return round(sum(arr) / len(arr), 2) if arr else None

    def batter_splits(gs):
        if not gs:
            return None
        return {
            "hits":       safe_avg([g.hits for g in gs if g.hits is not None]),
            "homeRuns":   safe_avg([g.home_runs for g in gs if g.home_runs is not None]),
            "rbi":        safe_avg([g.rbi for g in gs if g.rbi is not None]),
            "totalBases": safe_avg([g.total_bases for g in gs if g.total_bases is not None]),
            "games":      len(gs),
        }

    # Fetch MLB injury data (2h cache)
    try:
        mlb_injuries_all = injury_tracker.get_mlb_injuries()
    except Exception:
        mlb_injuries_all = {}

    # Fetch today's probable pitchers once for all players
    try:
        probable_pitchers = mlb_fetcher_instance.get_probable_pitchers_with_stats()
        print(f"[MLB ALL] Got {len(probable_pitchers)} probable pitchers")
    except Exception as e:
        print(f"[MLB ALL] Probable pitcher fetch failed: {e}")
        probable_pitchers = {}

    # Build MLB-name keyed lookup for quick access
    # probable_pitchers is keyed by MLB full team name already

    try:
        all_players = session.query(MLBPlayer).all()
        players_out = []

        for p in all_players:
            all_games = (
                session.query(MLBPlayerGame)
                .filter_by(player_id=p.id)
                .order_by(MLBPlayerGame.game_date.asc())
                .all()
            )

            games_2025 = [g for g in all_games if g.season == '2025']
            games_2026 = [g for g in all_games if g.season == '2026']

            # Need at least 5 games combined to show a player
            if len(games_2025) + len(games_2026) < 5:
                continue

            # Use last 20 games across both seasons for display/splits
            recent = all_games[-20:]
            team_odds = MLB_TO_ODDS.get(p.team, p.team)

            if p.is_pitcher:
                ks_2025 = [g.strikeouts for g in games_2025 if g.strikeouts is not None]
                ks_2026 = [g.strikeouts for g in games_2026 if g.strikeouts is not None]
                ks_recent = [g.strikeouts for g in recent if g.strikeouts is not None]
                outs = [g.outs_recorded for g in recent if g.outs_recorded is not None]

                if len(ks_2025) + len(ks_2026) < 5:
                    continue

                home_g = [g for g in all_games if g.is_home and g.strikeouts is not None]
                away_g = [g for g in all_games if not g.is_home and g.strikeouts is not None]

                game_log = [
                    {
                        "date":           g.game_date.isoformat(),
                        "opponent":       g.opponent,
                        "isHome":         g.is_home,
                        "strikeouts":     g.strikeouts,
                        "inningsPitched": g.innings_pitched,
                        "earnedRuns":     g.earned_runs,
                        "hitsAllowed":    g.hits_allowed,
                    }
                    for g in all_games[-15:]
                ]

                players_out.append({
                    "id":              p.id,
                    "name":            p.name,
                    "team":            team_odds,
                    "teamDbName":      p.team,
                    "position":        p.position,
                    "isPitcher":       True,
                    "gamesPlayed":     len(all_games),
                    "games2026":       len(games_2026),
                    "strikeoutsArr":   ks_recent,
                    "strikeoutsArr2025": ks_2025,
                    "strikeoutsArr2026": ks_2026,
                    "outsArr":         outs,
                    "avgKs":           safe_avg(ks_recent),
                    "homeAvgKs":       safe_avg([g.strikeouts for g in home_g]),
                    "awayAvgKs":       safe_avg([g.strikeouts for g in away_g]),
                    "homeGames":       len(home_g),
                    "awayGames":       len(away_g),
                    "gameLog":         game_log,
                    "h2hGames":        [],
                    "injuryStatus":    mlb_injuries_all.get(p.name, {}).get("status", "ACTIVE"),
                    "injuryDetail":    mlb_injuries_all.get(p.name, {}).get("injury"),
                })

            else:
                def batter_arr(gs, field):
                    return [getattr(g, field) for g in gs if getattr(g, field) is not None]

                hits_2025 = batter_arr(games_2025, 'hits')
                hits_2026 = batter_arr(games_2026, 'hits')
                hits_recent = batter_arr(recent, 'hits')

                if len(hits_2025) + len(hits_2026) < 5:
                    continue

                hrs_2025  = batter_arr(games_2025, 'home_runs')
                hrs_2026  = batter_arr(games_2026, 'home_runs')
                rbi_2025  = batter_arr(games_2025, 'rbi')
                rbi_2026  = batter_arr(games_2026, 'rbi')
                runs_2025 = batter_arr(games_2025, 'runs')
                runs_2026 = batter_arr(games_2026, 'runs')
                tb_2025   = batter_arr(games_2025, 'total_bases')
                tb_2026   = batter_arr(games_2026, 'total_bases')

                hrr_recent = [
                    (g.hits or 0) + (g.runs or 0) + (g.rbi or 0)
                    for g in recent
                    if g.hits is not None and g.runs is not None and g.rbi is not None
                ]
                hrr_2025 = [
                    (g.hits or 0) + (g.runs or 0) + (g.rbi or 0)
                    for g in games_2025
                    if g.hits is not None and g.runs is not None and g.rbi is not None
                ]
                hrr_2026 = [
                    (g.hits or 0) + (g.runs or 0) + (g.rbi or 0)
                    for g in games_2026
                    if g.hits is not None and g.runs is not None and g.rbi is not None
                ]

                home_g = [g for g in all_games if g.is_home and g.hits is not None]
                away_g = [g for g in all_games if not g.is_home and g.hits is not None]

                game_log = [
                    {
                        "date":       g.game_date.isoformat(),
                        "opponent":   g.opponent,
                        "isHome":     g.is_home,
                        "hits":       g.hits,
                        "homeRuns":   g.home_runs,
                        "rbi":        g.rbi,
                        "runs":       g.runs,
                        "totalBases": g.total_bases,
                        "atBats":     g.at_bats,
                    }
                    for g in all_games[-15:]
                ]

                players_out.append({
                    "id":            p.id,
                    "name":          p.name,
                    "team":              team_odds,
                    "teamDbName":        p.team,
                    "position":          p.position,
                    "isPitcher":         False,
                    "gamesPlayed":       len(all_games),
                    "games2026":         len(games_2026),
                    "hitsArr":           hits_recent,
                    "hitsArr2025":       hits_2025,
                    "hitsArr2026":       hits_2026,
                    "homeRunsArr":       [g.home_runs for g in recent if g.home_runs is not None],
                    "homeRunsArr2025":   hrs_2025,
                    "homeRunsArr2026":   hrs_2026,
                    "rbiArr":            [g.rbi for g in recent if g.rbi is not None],
                    "rbiArr2025":        rbi_2025,
                    "rbiArr2026":        rbi_2026,
                    "runsArr":           [g.runs for g in recent if g.runs is not None],
                    "runsArr2025":       runs_2025,
                    "runsArr2026":       runs_2026,
                    "totalBasesArr":     [g.total_bases for g in recent if g.total_bases is not None],
                    "totalBasesArr2025": tb_2025,
                    "totalBasesArr2026": tb_2026,
                    "hrrArr":            hrr_recent,
                    "hrrArr2025":        hrr_2025,
                    "hrrArr2026":        hrr_2026,
                    "avgHits":           safe_avg(hits_recent),
                    "avgTB":             safe_avg([g.total_bases for g in recent if g.total_bases is not None]),
                    "homeSplit":         batter_splits(home_g),
                    "awaySplit":         batter_splits(away_g),
                    "homeGames":         len(home_g),
                    "awayGames":         len(away_g),
                    "gameLog":           game_log,
                    "h2hGames":          [],
                    # Batter handedness for platoon splits (L/R/S)
                    "bats":              p.bats,
                    "injuryStatus":      mlb_injuries_all.get(p.name, {}).get("status", "ACTIVE"),
                    "injuryDetail":      mlb_injuries_all.get(p.name, {}).get("injury"),
                })

        players_out.sort(key=lambda p: (-p["gamesPlayed"], p["name"]))
        return {"success": True, "count": len(players_out), "players": players_out}
    finally:
        session.close()


MLB_ALL_PLAYERS_CACHE_FILE = "/tmp/mlbp_all.json"


@app.route('/api/mlb/players/all', methods=['GET'])
def get_all_mlb_players():
    """Return props for every MLB player in DB (no matchup required). Cached 6h."""
    cached = _load_specific_cache(MLB_ALL_PLAYERS_CACHE_FILE)
    if cached:
        ts = cached.get('ts')
        if ts:
            age = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
            if age < MLB_PLAYERS_CACHE_DURATION and cached.get('count', 0) > 0:
                return jsonify(cached)
    try:
        data = _compute_all_mlb_players()
        data['ts'] = datetime.now().isoformat()
        if data['count'] > 0:
            _save_specific_cache(MLB_ALL_PLAYERS_CACHE_FILE, data)
        return jsonify(data)
    except Exception as e:
        print(f"[MLB ALL PLAYERS] Error: {e}")
        return jsonify({"success": False, "error": str(e), "count": 0, "players": []})


@app.route('/api/admin/refresh-mlb-cache', methods=['POST'])
def refresh_mlb_cache():
    """Delete stale MLB player cache files then rebuild async in background.
    Called by GitHub Action after update_mlb_stats.py runs.
    Protected by ADMIN_SECRET env var.
    """
    import os, glob, threading
    secret = request.headers.get('X-Admin-Secret', '')
    expected = os.getenv('ADMIN_SECRET', '')
    if not expected or secret != expected:
        return jsonify({"error": "Unauthorized"}), 401

    removed = []
    for path in glob.glob('/tmp/mlbp_*.json'):
        try:
            os.remove(path)
            removed.append(path)
        except Exception:
            pass

    print(f"[ADMIN] MLB cache cleared: {removed}")

    # Rebuild all-players cache in background so it's ready before next user request
    def _rebuild():
        try:
            print("[ADMIN] Rebuilding MLB all-players cache...")
            data = _compute_all_mlb_players()
            data['ts'] = datetime.now().isoformat()
            if data['count'] > 0:
                _save_specific_cache(MLB_ALL_PLAYERS_CACHE_FILE, data)
            print(f"[ADMIN] MLB cache rebuilt ({data['count']} players)")
        except Exception as e:
            print(f"[ADMIN] Cache rebuild failed: {e}")

    threading.Thread(target=_rebuild, daemon=True).start()
    return jsonify({"success": True, "cleared": len(removed), "rebuilding": True})


@app.route('/api/mlb/players', methods=['GET'])
def get_mlb_players():
    """
    Get MLB player props for an upcoming game.
    Query params: home_team=..., away_team=... (Odds API team names from /api/mlb/games)
    """
    home_team = request.args.get('home_team', '').strip()
    away_team = request.args.get('away_team', '').strip()

    if not home_team or not away_team:
        return jsonify({"error": "home_team and away_team are required"}), 400

    safe = lambda s: s.replace(' ', '_').replace('/', '-')
    cache_key = f"/tmp/mlbp_{safe(home_team)}_{safe(away_team)}.json"

    cached = _load_specific_cache(cache_key)
    if cached:
        ts = cached.get('ts')
        if ts:
            age = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
            if age < MLB_PLAYERS_CACHE_DURATION and cached.get('count', 0) > 0:
                return jsonify(cached)

    try:
        data = _compute_mlb_players(home_team, away_team)
        data['ts'] = datetime.now().isoformat()
        if data['count'] > 0:
            _save_specific_cache(cache_key, data)
        return jsonify(data)
    except Exception as e:
        print(f"[MLB PLAYERS] Error: {e}")
        return jsonify({"success": False, "error": str(e), "count": 0, "players": []})


@app.route('/api/mlb/players/today', methods=['GET'])
def get_mlb_players_today():
    """
    Get MLB player props for ALL games today.
    Returns a flat array of all players tagged with matchup field.
    Cached for MLB_PLAYERS_CACHE_DURATION. No params required.
    """
    TODAY_CACHE_FILE = "/tmp/mlbp_today.json"
    cached = _load_specific_cache(TODAY_CACHE_FILE)
    if cached:
        ts = cached.get('ts')
        if ts:
            age = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
            if age < MLB_PLAYERS_CACHE_DURATION and cached.get('count', 0) > 0:
                return jsonify(cached)

    # Get today's games from mlb_cache
    games = []
    if mlb_cache["data"] and mlb_cache["data"].get("games"):
        games = mlb_cache["data"]["games"]
    if not games:
        return jsonify({"success": True, "count": 0, "players": [], "matchups": []})

    safe = lambda s: s.replace(' ', '_').replace('/', '-')
    all_players = []
    matchups = []

    for game in games:
        home_team = game.get("homeTeam", "")
        away_team = game.get("awayTeam", "")
        if not home_team or not away_team:
            continue

        matchup_label = f"{away_team} @ {home_team}"
        matchups.append({"key": f"{home_team}__{away_team}", "label": matchup_label, "homeTeam": home_team, "awayTeam": away_team})

        # Use existing per-game cache if fresh
        cache_key = f"/tmp/mlbp_{safe(home_team)}_{safe(away_team)}.json"
        per_game_cached = _load_specific_cache(cache_key)
        players = None
        if per_game_cached:
            ts = per_game_cached.get('ts')
            if ts:
                age = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
                if age < MLB_PLAYERS_CACHE_DURATION and per_game_cached.get('count', 0) > 0:
                    players = per_game_cached.get('players', [])

        if players is None:
            try:
                data = _compute_mlb_players(home_team, away_team)
                data['ts'] = datetime.now().isoformat()
                if data['count'] > 0:
                    _save_specific_cache(cache_key, data)
                players = data.get('players', [])
            except Exception as e:
                print(f"[MLB TODAY] Error for {home_team} vs {away_team}: {e}")
                players = []

        # Tag each player with their matchup
        for p in players:
            p['matchupKey'] = f"{home_team}__{away_team}"
            p['matchupLabel'] = matchup_label
        all_players.extend(players)

    result = {
        "success": True,
        "count": len(all_players),
        "players": all_players,
        "matchups": matchups,
        "ts": datetime.now().isoformat(),
    }
    if len(all_players) > 0:
        _save_specific_cache(TODAY_CACHE_FILE, result)
    return jsonify(result)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "StatScout API is running",
        "players_loaded": players_cache["data"]["count"] if players_cache["data"] else 0,
        **{f"soccer_{lg}_loaded": soccer_caches[lg]["data"]["count"] if soccer_caches[lg]["data"] else 0
           for lg in soccer_caches},
        "mlb_loaded": mlb_cache["data"]["count"] if mlb_cache["data"] else 0,
    })


def _build_mlb_cache_background():
    """Build MLB game card cache, then pre-warm today's player props cache."""
    import threading, time as _time
    def _run():
        mlb_cache["building"] = True
        for attempt in range(1, 4):
            try:
                cards = mlb_fetcher_instance.fetch_all()
                data = {"success": True, "count": len(cards), "games": cards}
                mlb_cache["data"] = data
                mlb_cache["last_updated"] = datetime.now()
                _save_specific_cache(MLB_CACHE_FILE, data)
                print(f"[MLB] Cache built ({len(cards)} games)")
                break
            except Exception as e:
                print(f"[MLB] Build attempt {attempt} failed: {e}")
                if attempt < 3:
                    _time.sleep(15)
        mlb_cache["building"] = False

        # Pre-warm all-players cache
        try:
            cached = _load_specific_cache(MLB_ALL_PLAYERS_CACHE_FILE)
            needs_rebuild = True
            if cached:
                ts = cached.get('ts')
                if ts:
                    age = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
                    if age < MLB_PLAYERS_CACHE_DURATION and cached.get('count', 0) > 0:
                        needs_rebuild = False
            if needs_rebuild:
                print("[MLB] Building all-players cache...")
                data = _compute_all_mlb_players()
                data['ts'] = datetime.now().isoformat()
                if data['count'] > 0:
                    _save_specific_cache(MLB_ALL_PLAYERS_CACHE_FILE, data)
                print(f"[MLB] All-players cache ready ({data['count']} players)")
        except Exception as e:
            print(f"[MLB] All-players pre-warm failed: {e}")

        # Pre-warm today's player props so first user request is instant
        if mlb_cache["data"] and mlb_cache["data"].get("games"):
            print("[MLB] Pre-warming today's player props cache...")
            try:
                safe = lambda s: s.replace(' ', '_').replace('/', '-')
                TODAY_CACHE_FILE = "/tmp/mlbp_today.json"
                all_players = []
                matchups = []
                for game in mlb_cache["data"]["games"]:
                    home_team = game.get("homeTeam", "")
                    away_team = game.get("awayTeam", "")
                    if not home_team or not away_team:
                        continue
                    matchup_label = f"{away_team} @ {home_team}"
                    matchups.append({"key": f"{home_team}__{away_team}", "label": matchup_label, "homeTeam": home_team, "awayTeam": away_team})
                    cache_key = f"/tmp/mlbp_{safe(home_team)}_{safe(away_team)}.json"
                    per_game_cached = _load_specific_cache(cache_key)
                    players = None
                    if per_game_cached:
                        ts = per_game_cached.get('ts')
                        if ts:
                            age = (datetime.now() - datetime.fromisoformat(ts)).total_seconds()
                            if age < MLB_PLAYERS_CACHE_DURATION and per_game_cached.get('count', 0) > 0:
                                players = per_game_cached.get('players', [])
                    if players is None:
                        try:
                            data = _compute_mlb_players(home_team, away_team)
                            data['ts'] = datetime.now().isoformat()
                            if data['count'] > 0:
                                _save_specific_cache(cache_key, data)
                            players = data.get('players', [])
                        except Exception as e:
                            print(f"[MLB TODAY] Pre-warm error for {home_team} vs {away_team}: {e}")
                            players = []
                    for p in players:
                        p['matchupKey'] = f"{home_team}__{away_team}"
                        p['matchupLabel'] = matchup_label
                    all_players.extend(players)
                result = {"success": True, "count": len(all_players), "players": all_players, "matchups": matchups, "ts": datetime.now().isoformat()}
                if len(all_players) > 0:
                    _save_specific_cache(TODAY_CACHE_FILE, result)
                print(f"[MLB] Today's props cache ready ({len(all_players)} players across {len(matchups)} games)")
            except Exception as e:
                print(f"[MLB] Pre-warm failed: {e}")

    threading.Thread(target=_run, daemon=True).start()


@app.route('/api/mlb/games', methods=['GET'])
def get_mlb_games():
    """Get upcoming MLB games with run totals, moneylines, run lines, and historical over rates."""
    now = datetime.now()
    if mlb_cache["data"] is not None and mlb_cache["last_updated"] and mlb_cache["data"].get("count", 0) > 0:
        age = (now - mlb_cache["last_updated"]).total_seconds()
        if age < MLB_CACHE_DURATION:
            print(f"[MLB] Serving from cache (age: {age:.0f}s)")
            return jsonify(mlb_cache["data"])
    disk = _load_specific_cache(MLB_CACHE_FILE)
    if disk and disk.get("count", 0) > 0:
        mlb_cache["data"] = disk
        mlb_cache["last_updated"] = datetime.now()
        print(f"[MLB] Loaded from disk ({disk['count']} games)")
        return jsonify(disk)
    if not mlb_cache["building"]:
        _build_mlb_cache_background()
    return jsonify({"success": True, "count": 0, "games": []})


@app.route('/api/soccer/matches', methods=['GET'])
def get_soccer_matches():
    """Get upcoming soccer matches with over/under odds and hit rates. ?league=pl|laliga"""
    league = request.args.get('league', 'pl')
    if league not in soccer_caches:
        return jsonify({"error": "Unknown league"}), 400
    cache = soccer_caches[league]
    now = datetime.now()
    if cache["data"] is not None and cache["last_updated"] and cache["data"].get("count", 0) > 0:
        age = (now - cache["last_updated"]).total_seconds()
        if age < SOCCER_CACHE_DURATION:
            print(f"[SOCCER] {league} serving from cache (age: {age:.0f}s)")
            return jsonify(cache["data"])
    # Cache miss or empty — try disk
    disk = _load_specific_cache(SOCCER_CACHE_FILES[league])
    if disk and disk.get("count", 0) > 0:
        cache["data"] = disk
        cache["last_updated"] = datetime.now()
        print(f"[SOCCER] {league} loaded from disk ({disk['count']} matches)")
        return jsonify(disk)
    # Nothing on disk — trigger rebuild
    if not cache["building"]:
        _build_soccer_cache_background(league)
    return jsonify({"success": True, "count": 0, "matches": []})


@app.route('/api/players', methods=['GET'])
def get_all_players():
    """Get all available player props"""

    # Get query parameters for filtering
    team_filter = request.args.get('team', 'all')
    stat_filter = request.args.get('stat', 'all')

    # Serve from cache for unfiltered requests (avoids Render 30s proxy timeout)
    now = datetime.now()
    if team_filter == 'all' and stat_filter == 'all':
        if players_cache["data"] is not None:
            cache_age = (now - players_cache["last_updated"]).total_seconds() if players_cache["last_updated"] else None
            if cache_age is not None and cache_age < PLAYERS_CACHE_DURATION:
                print(f"[CACHE] Serving players from cache (age: {cache_age:.0f}s)")
                return jsonify(players_cache["data"])
        else:
            # Cache empty in this process - another process may have written to disk already
            disk_data = _load_cache_from_disk()
            if disk_data:
                players_cache["data"] = disk_data
                players_cache["last_updated"] = datetime.now()
                print(f"[CACHE] Loaded from disk on request ({disk_data['count']} props)")
                return jsonify(disk_data)
            # Disk also empty - trigger rebuild or wait
            if not players_cache["building"]:
                print("[CACHE] Cache empty on request - triggering rebuild in worker process")
                _build_players_cache_background()
            else:
                print("[CACHE] Cache not ready yet, build in progress")
            return jsonify({"success": True, "count": 0, "players": []})

    try:
        response_data = _compute_players_data(team_filter, stat_filter)

        # Store in cache for unfiltered requests (only when we have actual data)
        if team_filter == 'all' and stat_filter == 'all' and response_data["count"] > 0:
            players_cache["data"] = response_data
            players_cache["last_updated"] = datetime.now()
            print(f"[CACHE] Players cache updated ({response_data['count']} props)")

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/players/refresh', methods=['POST'])
def refresh_players_cache():
    """Force refresh the players cache in the background"""
    import threading

    def _refresh():
        _fresh_loader = DataLoader()
        try:
            print("[CACHE] Background refresh started...")
            data = _compute_players_data(_loader=_fresh_loader)
            if data["count"] > 0:
                players_cache["data"] = data
                players_cache["last_updated"] = datetime.now()
                print(f"[CACHE] Refresh complete ({data['count']} props)")
            else:
                print("[CACHE] Refresh returned 0 props, cache not updated")
        except Exception as e:
            print(f"[CACHE] Background refresh error: {e}")
        finally:
            try:
                _fresh_loader.session.close()
            except:
                pass

    threading.Thread(target=_refresh, daemon=True).start()
    return jsonify({"success": True, "message": "Cache refresh triggered"})


@app.route('/api/admin/db-status', methods=['GET'])
def admin_db_status():
    """Show most recent game date and total game count in the DB"""
    try:
        from models import get_session as _gs, Game as _Game
        from sqlalchemy import func as _func
        session = _gs(loader.engine)
        latest = session.query(_func.max(_Game.date)).scalar()
        total = session.query(_func.count(_Game.id)).scalar()
        session.close()
        return jsonify({
            "success": True,
            "latest_game_date": str(latest) if latest else None,
            "total_games": total
        })
    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@app.route('/api/admin/test-espn', methods=['GET'])
def admin_test_espn():
    """Test ESPN scraper for a single date - use ?date=YYYYMMDD or defaults to yesterday"""
    try:
        from espn_recent_games_scraper import ESPNAPIClient as _ESPN
        from models import get_session as _gs
        from update_stats import _build_player_name_map, _lookup_player
        date_str = request.args.get('date', (datetime.now() - timedelta(days=1)).strftime('%Y%m%d'))
        client = _ESPN()
        stats = client.get_player_stats_from_date(date_str)
        session = _gs(loader.engine)
        name_map = _build_player_name_map(session)
        matched = 0
        unmatched = []
        for s in stats:
            p = _lookup_player(name_map, s['player_name'])
            if p:
                matched += 1
            else:
                unmatched.append(s['player_name'])
        session.close()
        return jsonify({
            "success": True,
            "date": date_str,
            "espn_players_found": len(stats),
            "matched_in_db": matched,
            "unmatched_sample": unmatched[:20],
            "sample_stats": stats[:5]
        })
    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@app.route('/api/admin/update-stats', methods=['POST'])
def admin_update_stats():
    """Trigger ESPN recent-games update in background (fetches last 90 days)"""
    import threading
    from models import get_session as _get_session

    def _run_update():
        try:
            from update_stats import add_espn_recent_games
            session = _get_session(loader.engine)
            added = add_espn_recent_games(session, days_back=90)
            session.close()
            print(f"[UPDATE] ESPN update complete: {added} new games added")
            # Wipe disk cache too so worker doesn't re-serve stale data
            try:
                import os as _os
                if _os.path.exists(CACHE_FILE):
                    _os.remove(CACHE_FILE)
            except Exception:
                pass
            players_cache["data"] = None
            players_cache["last_updated"] = None
            _build_players_cache_background()
        except Exception as e:
            import traceback
            print(f"[UPDATE] ESPN update failed: {e}")
            traceback.print_exc()

    threading.Thread(target=_run_update, daemon=True).start()
    return jsonify({"success": True, "message": "Stats update triggered (last 90 days from ESPN)"})


@app.route('/api/player/<player_name>', methods=['GET'])
def get_player(player_name):
    """Get specific player's props"""
    
    try:
        player_info = loader.get_player_info(player_name)
        
        if not player_info:
            return jsonify({"success": False, "error": "Player not found"}), 404
        
        # Get all available stats for this player
        all_stats = loader.get_all_available_stats(player_name)
        
        props = []
        
        all_teams = loader.get_teams()
        opponents = [t for t in all_teams if t != player_info["team"]]
        
        for stat_type, stat_values in all_stats.items():
            if len(stat_values) < 3:
                continue

            display_stat_type = stat_type.upper() if len(stat_type) <= 3 else stat_type.title()
            avg_stat = sum(stat_values) / len(stat_values)
            line = STAT_LINES.get(display_stat_type, lambda x: round(x - 0.5, 1))(avg_stat)
            
            opponent = random.choice(opponents) if opponents else "OPP"
            
            analysis = calc.analyze_player_prop(
                player_name=player_name,
                team=player_info["team"],
                stat_type=display_stat_type,
                player_stats=stat_values,
                line=line,
                opponent=opponent,
                opponent_rank=random.randint(5, 25),
                is_home=random.choice([True, False]),
                db_loader=loader
            )
            
            props.append(analysis)
        
        return jsonify({
            "success": True,
            "player": player_name,
            "props": props
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/calculate', methods=['POST'])
def calculate_custom():
    """Calculate trust score for custom input or adjusted line"""
    
    data = request.json
    
    # Check if it's a request to recalculate with a different line
    if 'player_name' in data and 'stat_type' in data and 'custom_line' in data:
        try:
            player_name = data['player_name']
            stat_type = data['stat_type']
            custom_line = float(data['custom_line'])
            
            # Use stats_cache if available (avoids DB queries, makes response instant)
            if player_name in stats_cache and players_cache["data"]:
                all_stats = stats_cache[player_name]
                player_info = next(
                    ({"team": p["team"], "position": p["position"]}
                     for p in players_cache["data"]["players"]
                     if p["name"] == player_name),
                    None
                )
            else:
                try:
                    player_info = loader.get_player_info(player_name)
                    all_stats = loader.get_all_available_stats(player_name)
                except Exception as db_err:
                    print(f"[CALCULATE] DB fallback failed: {db_err}, using players_cache")
                    # Last resort: extract from players_cache (last 15 games only)
                    player_info = None
                    all_stats = {}
                    if players_cache["data"]:
                        for p in players_cache["data"]["players"]:
                            if p["name"] == player_name:
                                if player_info is None:
                                    player_info = {"team": p["team"], "position": p["position"]}
                                if p["statType"] == data['stat_type']:
                                    all_stats = {data['stat_type'].lower(): p.get("last15Games", p.get("lastGames", []))}
                                    break

            if not player_info:
                return jsonify({"success": False, "error": "Player not found"}), 404

            # Map display stat type back to internal stat type
            stat_type_lower = stat_type.lower()

            # Special case for 3PM -> three_pm
            if stat_type == '3PM' or stat_type_lower == '3pm':
                stat_type_internal = 'three_pm'
            else:
                stat_type_internal = stat_type_lower

            # Find matching stat in all_stats
            matched_stat = None
            for key in all_stats.keys():
                if key.lower() == stat_type_internal or key.lower() == stat_type_lower:
                    matched_stat = key
                    break
            
            if not matched_stat:
                return jsonify({"success": False, "error": f"Stat type {stat_type} not available for {player_name}"}), 404
            
            stat_values = all_stats[matched_stat]
            
            # Get opponent info from request (frontend always sends these)
            opponent = data.get('opponent', "OPP")
            opponent_rank = data.get('opponent_rank', random.randint(5, 25))
            is_home = data.get('is_home', random.choice([True, False]))
            
            # Calculate with custom line
            analysis = calc.analyze_player_prop(
                player_name=player_name,
                team=player_info["team"],
                stat_type=stat_type,
                player_stats=stat_values,
                line=custom_line,
                opponent=opponent,
                opponent_rank=opponent_rank,
                is_home=is_home,
                db_loader=loader
            )
            
            # Generate game info
            game_date, game_time = generate_game_info()
            
            # Format response
            result = {
                "name": player_name,
                "team": player_info["team"],
                "teamColor": TEAM_COLORS.get(player_info["team"], "#000000"),
                "position": player_info["position"],
                "statType": stat_type,
                "line": custom_line,  # Use the custom line
                "hitRate": analysis["hit_rate"],
                "trustScore": analysis["trust_score"],
                "lastGames": analysis["last_games"],
                "last5Games": analysis["last_5_games"],
                "last15Games": analysis["last_15_games"],
                "recentForm": analysis["recent_form"],
                "opponent": opponent,
                "opponentRank": opponent_rank,
                "opponentDefStat": get_opponent_def_stat(stat_type),
                "gameDate": game_date,
                "gameTime": game_time,
                "isHome": is_home,
                "avgLastN": analysis["avg_last_10"],
                "streak": analysis["streak"],
                "streakType": analysis["streak_type"],
                "season_hits": analysis.get("season_hits"),
                "total_games": analysis.get("total_games"),
                "recent_hit_rate": analysis.get("recent_hit_rate"),
                "recent_hits": analysis.get("recent_hits"),
                "recent_total": analysis.get("recent_total")
            }
            
            return jsonify({
                "success": True,
                "analysis": result
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    # Original functionality for completely custom input
    required_fields = ['player_stats', 'line', 'opponent_rank']
    if not all(field in data for field in required_fields):
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    try:
        analysis = calc.analyze_player_prop(
            player_name=data.get('player_name', 'Unknown'),
            team=data.get('team', 'N/A'),
            stat_type=data.get('stat_type', 'Points'),
            player_stats=data['player_stats'],
            line=data['line'],
            opponent=data.get('opponent', 'N/A'),
            opponent_rank=data['opponent_rank'],
            is_home=data.get('is_home', True),
            db_loader=loader
        )
        
        return jsonify({
            "success": True,
            "analysis": analysis
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/add-player', methods=['POST'])
def add_player():
    """Add a new player to the database"""
    try:
        data = request.json
        player_name = data.get('player_name')

        if not player_name:
            return jsonify({
                "success": False,
                "error": "player_name is required"
            }), 400

        from nba_stats_fetcher import NBAStatsFetcher
        from nba_api.stats.static import players as nba_players
        from models import Player, Game

        # Find player in NBA API
        all_nba_players = nba_players.get_players()
        player_info = [p for p in all_nba_players if p['full_name'].lower() == player_name.lower() and p.get('is_active', True)]

        if not player_info:
            # Try partial match
            player_info = [p for p in all_nba_players if player_name.lower() in p['full_name'].lower() and p.get('is_active', True)]

        if not player_info:
            return jsonify({
                "success": False,
                "error": f"Player '{player_name}' not found in NBA database"
            }), 404

        nba_player = player_info[0]
        full_name = nba_player['full_name']

        # Check if already exists
        from models import get_session, get_engine
        engine = get_engine()
        session = get_session(engine)

        existing = session.query(Player).filter_by(name=full_name).first()
        if existing:
            session.close()
            return jsonify({
                "success": False,
                "error": f"Player '{full_name}' already exists in database"
            }), 400

        # Fetch player details to get position
        from nba_api.stats.endpoints import commonplayerinfo
        import time

        time.sleep(0.6)  # Rate limiting
        player_details = commonplayerinfo.CommonPlayerInfo(player_id=nba_player['id'])
        player_info_df = player_details.get_data_frames()[0]

        # Get position from player info (fallback to 'G' if not available)
        position = player_info_df.iloc[0]['POSITION'] if not player_info_df.empty else 'G'
        if not position or position == '':
            position = 'G'  # Default to Guard

        # Get team abbreviation (will be extracted from games, but needed as fallback)
        team_abbrev = player_info_df.iloc[0]['TEAM_ABBREVIATION'] if not player_info_df.empty else 'UNK'
        if not team_abbrev or team_abbrev == '':
            team_abbrev = 'UNK'

        # Fetch player game data
        fetcher = NBAStatsFetcher()
        games = fetcher.fetch_player_season(full_name, team_abbrev, position, season="2025-26")

        if not games:
            session.close()
            return jsonify({
                "success": False,
                "error": f"No game data found for {full_name}"
            }), 404

        # Add player (use team from actual games data)
        new_player = Player(
            name=full_name,
            team=games[0]['team'],
            position=position
        )
        session.add(new_player)
        session.flush()

        # Add games
        for game in games:
            from datetime import datetime
            new_game = Game(
                player_id=new_player.id,
                date=datetime.strptime(game['date'], '%Y-%m-%d').date(),
                opponent=game['opponent'],
                is_home=bool(game['is_home']),
                points=int(game['points']),
                rebounds=int(game['rebounds']),
                assists=int(game['assists']),
                steals=int(game['steals']),
                blocks=int(game['blocks']),
                three_pm=int(game['three_pm'])
            )
            session.add(new_game)

        session.commit()
        games_added = len(games)
        session.close()

        return jsonify({
            "success": True,
            "message": f"Added {full_name} with {games_added} games"
        })

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/update', methods=['POST'])
def trigger_update():
    """Manually trigger a stats update (runs asynchronously)"""
    import threading

    def run_update():
        """Background thread function to run the update"""
        try:
            from update_stats import update_all_players
            print("\n[INFO] Background update started")
            result = update_all_players()
            print(f"\n[INFO] Background update completed: {result}")
        except Exception as e:
            print(f"\n[ERROR] Background update failed: {e}")
            import traceback
            traceback.print_exc()

    try:
        # Start update in background thread
        update_thread = threading.Thread(target=run_update, daemon=True)
        update_thread.start()

        print("\n[INFO] Update triggered successfully via API (running in background)")

        # Return immediately while update runs in background
        return jsonify({
            "success": True,
            "message": "Stats update started in background. Check server logs for progress.",
            "status": "running"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== INJURY & STATUS ENDPOINTS ==========

@app.route('/api/injuries/player/<player_name>', methods=['GET'])
def get_player_injury_status(player_name):
    """Get injury status for a specific player"""
    try:
        status = injury_tracker.get_player_status(player_name)

        return jsonify({
            "success": True,
            "player": player_name,
            "injury_status": status
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/injuries/batch', methods=['POST'])
def get_batch_injury_status():
    """Get injury status for multiple players at once"""
    try:
        data = request.json
        player_names = data.get('players', [])

        if not player_names:
            return jsonify({
                "success": False,
                "error": "No player names provided"
            }), 400

        statuses = injury_tracker.get_batch_status(player_names)

        return jsonify({
            "success": True,
            "count": len(statuses),
            "statuses": statuses
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/injuries/set', methods=['POST'])
def set_manual_injury_status():
    """Manually set a player's injury status (for testing/demo)"""
    try:
        data = request.json
        player_name = data.get('player')
        status = data.get('status')

        if not player_name or not status:
            return jsonify({
                "success": False,
                "error": "Both 'player' and 'status' are required"
            }), 400

        injury_tracker.set_manual_status(player_name, status)

        return jsonify({
            "success": True,
            "message": f"Set {player_name} status to {status}"
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/injuries/refresh', methods=['POST'])
def refresh_injury_data():
    """Force refresh of NBA injury data"""
    try:
        inactive_players = injury_tracker.refresh_nba_data()

        return jsonify({
            "success": True,
            "message": "Injury data refreshed",
            "inactive_count": len(inactive_players)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== TEAM QUARTER ANALYTICS ENDPOINTS ==========

@app.route('/api/quarters/team/<team_abbr>', methods=['GET'])
def get_team_quarter_stats(team_abbr):
    """Get quarter statistics for a specific team"""
    try:
        season = request.args.get('season', '2025-26')

        # Get quarter averages
        averages = quarter_analytics.get_team_quarter_averages(team_abbr, season)

        if not averages:
            return jsonify({
                "success": False,
                "error": f"No data found for team {team_abbr}"
            }), 404

        # Get win correlation
        correlation = quarter_analytics.get_quarter_win_correlation(team_abbr, season)

        return jsonify({
            "success": True,
            "team": team_abbr,
            "season": season,
            "averages": averages,
            "win_correlation": correlation
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/quarters/matchup', methods=['GET'])
def get_matchup_quarter_analysis():
    """Get quarter analysis for a team vs team matchup"""
    try:
        team1 = request.args.get('team1')
        team2 = request.args.get('team2')
        season = request.args.get('season', '2025-26')

        if not team1 or not team2:
            return jsonify({
                "success": False,
                "error": "Both team1 and team2 parameters are required"
            }), 400

        analysis = quarter_analytics.get_matchup_quarter_analysis(team1, team2, season)

        if not analysis:
            return jsonify({
                "success": False,
                "error": f"No data found for matchup {team1} vs {team2}"
            }), 404

        return jsonify({
            "success": True,
            "matchup": analysis
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== MATCHUP HISTORY ENDPOINTS ==========

@app.route('/api/location-split/<player_name>/<stat_type>/<int:is_home>', methods=['GET'])
def get_location_split(player_name, stat_type, is_home):
    """Get a player's home/away performance split (lazy loaded)"""
    try:
        split_data = loader.get_home_away_splits(player_name, stat_type)

        if split_data is None:
            return jsonify({
                "success": False,
                "error": f"Player '{player_name}' not found"
            }), 404

        location_split = calc.analyze_location_split(split_data, bool(is_home)) if split_data else {"has_data": False}

        return jsonify({
            "success": True,
            "split": location_split
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/half-tendency/<player_name>/<stat_type>', methods=['GET'])
def get_half_tendency(player_name, stat_type):
    """Get a player's first half vs second half tendency"""
    try:
        half_data = loader.get_half_tendency(player_name, stat_type)

        if half_data is None:
            return jsonify({
                "success": False,
                "error": f"Player '{player_name}' not found"
            }), 404

        return jsonify({
            "success": True,
            "tendency": half_data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/live-projection/<player_name>/<stat_type>/<current_stat>', methods=['GET'])
def get_live_projection(player_name, stat_type, current_stat):
    """Get live projection for halftime betting"""
    try:
        # Convert current_stat to float (handles both integers and decimals)
        current_stat = float(current_stat)
        projection = loader.get_live_projection(player_name, stat_type, current_stat, is_halftime=True)

        return jsonify({
            "success": True,
            "projection": projection
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/matchup/<player_name>/<opponent>', methods=['GET'])
def get_player_matchup_history(player_name, opponent):
    """Get a player's performance history against a specific opponent"""
    try:
        matchup_data = loader.get_matchup_history(player_name, opponent)

        if matchup_data is None:
            return jsonify({
                "success": False,
                "error": f"Player '{player_name}' not found"
            }), 404

        return jsonify({
            "success": True,
            "matchup": matchup_data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== PARLAY BUILDER ENDPOINTS ==========

@app.route('/api/parlay/generate', methods=['POST'])
def generate_parlay():
    """Generate parlay suggestions based on user criteria"""
    try:
        data = request.get_json()

        # Get parameters with defaults
        target_odds = data.get('target_odds', 400)
        safety_level = data.get('safety_level', 'moderate')
        game_filter = data.get('game_filter', 'any')
        selected_games = data.get('selected_games', [])
        num_suggestions = data.get('num_suggestions', 3)
        min_legs = data.get('min_legs', 2)
        max_legs = data.get('max_legs', 6)
        banned_players = data.get('banned_players', [])

        # Validate safety level
        if safety_level not in ['conservative', 'moderate', 'aggressive']:
            return jsonify({
                "success": False,
                "error": f"Invalid safety_level: {safety_level}. Must be 'conservative', 'moderate', or 'aggressive'"
            }), 400

        # Validate game filter
        if game_filter not in ['any', 'single', 'specific']:
            return jsonify({
                "success": False,
                "error": f"Invalid game_filter: {game_filter}. Must be 'any', 'single', or 'specific'"
            }), 400

        # Use the already-computed players cache instead of recomputing everything
        cache_data = players_cache.get("data")
        if not cache_data:
            # In-memory cache empty — try disk (same fallback as /api/players)
            disk_data = _load_cache_from_disk()
            if disk_data:
                players_cache["data"] = disk_data
                players_cache["last_updated"] = datetime.now()
                cache_data = disk_data
        if not cache_data:
            return jsonify({
                "success": False,
                "error": "Props data is still loading. Please wait a moment and try again."
            }), 503

        all_props = []

        # Helper function for case and accent-insensitive name matching
        import unicodedata
        def normalize_name(name):
            """Remove accents and convert to lowercase for comparison"""
            nfd = unicodedata.normalize('NFD', name)
            without_accents = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
            return without_accents.lower().strip()

        normalized_banned = [normalize_name(p) for p in banned_players]

        for p in cache_data["players"]:
            # Skip banned players (case and accent insensitive)
            if normalize_name(p["name"]) in normalized_banned:
                continue

            # Skip injured/questionable players
            if p.get("injuryStatus") in ('OUT', 'QUESTIONABLE', 'DOUBTFUL'):
                continue

            # Skip props without a scheduled opponent
            if not p.get("opponent"):
                continue

            # Get best available odds from bookmaker lines
            odds = -110
            if p.get("bookmakerLines"):
                first_bm = p["bookmakerLines"][0]
                odds = first_bm.get("over_odds") or -110

            all_props.append({
                'player_name': p["name"],
                'team': p["team"],
                'opponent': p["opponent"],
                'stat_type': p["statType"],
                'line': p["line"],
                'odds': odds,
                'trust_score': p["trustScore"],
                'is_home': p["isHome"]
            })

        # Generate parlays
        suggestions = parlay_builder.generate_parlay(
            all_props=all_props,
            target_odds=target_odds,
            safety_level=safety_level,
            game_filter=game_filter,
            selected_games=selected_games,
            num_suggestions=num_suggestions,
            min_legs=min_legs,
            max_legs=max_legs
        )

        return jsonify({
            "success": True,
            "suggestions": suggestions,
            "total_props_available": len(all_props)
        })

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# Ensure all DB tables exist (safe - create_all is idempotent)
try:
    from models import get_engine, init_db
    _db_engine = get_engine()
    init_db(_db_engine)
    print("[DB] Tables verified/created")
except Exception as _db_err:
    print(f"[DB] Could not verify tables: {_db_err}")

# Start background cache builds after all routes are defined
_build_players_cache_background()
_build_mlb_cache_background()

# Pre-build all soccer match caches sequentially at startup so they are warm before first visit.
# The _fd_semaphore in soccer_fetcher serializes football-data.org calls anyway, so launching
# them all at once would just queue behind each other — easier to chain them explicitly.
def _build_all_soccer_caches():
    import threading, time as _time
    def _run():
        _time.sleep(10)  # let NBA/MLB builds start first
        for league in ['pl', 'laliga', 'bundesliga', 'seriea', 'ligue1']:
            cache = soccer_caches[league]
            if cache["data"] is not None and cache["data"].get("count", 0) > 0:
                print(f"[SOCCER] {league} already cached, skipping startup build")
                continue
            if not cache["building"]:
                _build_soccer_cache_background(league)
            # Wait for this league to finish before starting the next
            for _ in range(60):
                _time.sleep(2)
                if not cache["building"]:
                    break
    threading.Thread(target=_run, daemon=True).start()

_build_all_soccer_caches()
_build_soccer_all_players_cache_background('pl')  # Soccer all-players; other leagues load lazily


def _schedule_daily_stats_update():
    """
    Run update_stats.py once per day at 09:00 UTC (5 AM ET) in a background thread.
    This ensures mid-game captures (halftime stats locked in) get corrected within 24h
    thanks to the 7-day refresh window in update_stats.py.
    UptimeRobot keeps this process alive 24/7 so the thread reliably fires each day.
    """
    import threading, time as _time
    from datetime import datetime, timezone, timedelta

    def _run():
        TARGET_HOUR_UTC = 9   # 5 AM ET — all overnight games are fully finalized by then
        while True:
            now = datetime.now(timezone.utc)
            next_run = now.replace(hour=TARGET_HOUR_UTC, minute=0, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            sleep_secs = (next_run - now).total_seconds()
            print(f"[STATS] Daily auto-update scheduled for {next_run.strftime('%Y-%m-%d %H:%M UTC')} "
                  f"({sleep_secs / 3600:.1f}h from now)")
            _time.sleep(sleep_secs)
            try:
                print("[STATS] Starting scheduled daily stats update...")
                from update_stats import update_all_players
                result = update_all_players()
                print(f"[STATS] Scheduled update complete — "
                      f"{result.get('new_games', 0)} new games, "
                      f"{result.get('players_updated', 0)} players updated")
            except Exception as _e:
                print(f"[STATS] Scheduled update failed: {_e}")

    threading.Thread(target=_run, daemon=True).start()


_schedule_daily_stats_update()


def _schedule_daily_mlb_update():
    """
    Run update_mlb_stats.py once per day at 10:00 UTC (6 AM ET).
    Staggered 1h after the NBA update to avoid competing for DB connections.
    """
    import threading, time as _time
    from datetime import datetime, timezone, timedelta

    def _run():
        TARGET_HOUR_UTC = 10
        while True:
            now = datetime.now(timezone.utc)
            next_run = now.replace(hour=TARGET_HOUR_UTC, minute=0, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            sleep_secs = (next_run - now).total_seconds()
            print(f"[MLB STATS] Daily auto-update scheduled for "
                  f"{next_run.strftime('%Y-%m-%d %H:%M UTC')} ({sleep_secs/3600:.1f}h from now)")
            _time.sleep(sleep_secs)
            try:
                print("[MLB STATS] Starting scheduled daily MLB stats update...")
                from update_mlb_stats import main as mlb_update_main
                mlb_update_main()
                print("[MLB STATS] Scheduled update complete")
                # Clear per-matchup caches so h2h data reflects new game rows
                import os, glob as _glob
                for path in _glob.glob('/tmp/mlbp_*.json'):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
                print("[MLB STATS] Per-matchup caches cleared")
                # Rebuild MLB caches after update so fresh data is served immediately
                _build_mlb_cache_background()
            except Exception as _e:
                print(f"[MLB STATS] Scheduled update failed: {_e}")

    threading.Thread(target=_run, daemon=True).start()


def _schedule_daily_soccer_cache_refresh():
    """
    Proactively rebuild all soccer match caches at 11:00 UTC (7 AM ET) daily.
    Prevents stale data from sitting until a user happens to request an expired league.
    Uses 5 Odds API calls/day (one per league) — well within free tier limits.
    """
    import threading, time as _time
    from datetime import datetime, timezone, timedelta

    def _run():
        TARGET_HOUR_UTC = 11
        while True:
            now = datetime.now(timezone.utc)
            next_run = now.replace(hour=TARGET_HOUR_UTC, minute=0, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            sleep_secs = (next_run - now).total_seconds()
            print(f"[SOCCER] Daily cache refresh scheduled for "
                  f"{next_run.strftime('%Y-%m-%d %H:%M UTC')} ({sleep_secs/3600:.1f}h from now)")
            _time.sleep(sleep_secs)
            print("[SOCCER] Starting scheduled daily cache refresh for all leagues...")
            for league in ['pl', 'laliga', 'bundesliga', 'seriea', 'ligue1']:
                try:
                    # Force expire the in-memory cache so _build triggers a fresh fetch
                    soccer_caches[league]["last_updated"] = None
                    soccer_caches[league]["data"] = None
                    if not soccer_caches[league]["building"]:
                        _build_soccer_cache_background(league)
                    # Wait up to 120s for each league before moving to next
                    for _ in range(60):
                        _time.sleep(2)
                        if not soccer_caches[league]["building"]:
                            break
                except Exception as _e:
                    print(f"[SOCCER] Refresh failed for {league}: {_e}")
            print("[SOCCER] Daily cache refresh complete")

    threading.Thread(target=_run, daemon=True).start()


def _schedule_weekly_soccer_stats_update():
    """
    Run update_soccer_stats.py once per week, every Monday at 07:00 UTC.
    This catches all weekend gameweek results across all 5 leagues.
    Runs in a daemon background thread so it never blocks requests.
    """
    import threading, time as _time
    from datetime import datetime, timezone, timedelta

    def _run():
        TARGET_WEEKDAY = 0   # Monday
        TARGET_HOUR_UTC = 7
        while True:
            now = datetime.now(timezone.utc)
            # Next Monday at 07:00 UTC
            days_until_monday = (TARGET_WEEKDAY - now.weekday()) % 7
            if days_until_monday == 0 and now.hour >= TARGET_HOUR_UTC:
                days_until_monday = 7  # already past this Monday, wait for next
            next_run = (now + timedelta(days=days_until_monday)).replace(
                hour=TARGET_HOUR_UTC, minute=0, second=0, microsecond=0
            )
            sleep_secs = (next_run - now).total_seconds()
            print(f"[SOCCER STATS] Weekly update scheduled for "
                  f"{next_run.strftime('%Y-%m-%d %H:%M UTC')} ({sleep_secs/3600:.1f}h from now)")
            _time.sleep(sleep_secs)
            try:
                print("[SOCCER STATS] Starting weekly soccer stats update (all leagues)...")
                from update_soccer_stats import main as soccer_update_main
                soccer_update_main()
                print("[SOCCER STATS] Weekly update complete - invalidating player caches")
                # Clear soccer all-players caches so fresh stats are served
                import os as _os
                for league in ['pl', 'laliga', 'bundesliga', 'seriea', 'ligue1']:
                    _soccer_all_players_caches[league] = None
                    cache_file = SOCCER_ALL_PLAYERS_CACHE_FILES.get(league, '')
                    if cache_file and _os.path.exists(cache_file):
                        try:
                            _os.remove(cache_file)
                        except Exception:
                            pass
            except Exception as _e:
                print(f"[SOCCER STATS] Weekly update failed: {_e}")

    threading.Thread(target=_run, daemon=True).start()


def _schedule_weekly_mlb_roster_refresh():
    """
    Refresh all 30 MLB team rosters every Sunday at 08:00 UTC.
    Updates player team assignments for trades, adds new call-ups.
    Lightweight - no game log re-fetch, just roster sync.
    """
    import threading, time as _time
    from datetime import datetime, timezone, timedelta

    def _run():
        TARGET_WEEKDAY = 6   # Sunday
        TARGET_HOUR_UTC = 8
        while True:
            now = datetime.now(timezone.utc)
            days_ahead = (TARGET_WEEKDAY - now.weekday()) % 7
            next_run = now.replace(hour=TARGET_HOUR_UTC, minute=0, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
            if next_run <= now:
                next_run += timedelta(days=7)
            sleep_secs = (next_run - now).total_seconds()
            print(f"[MLB ROSTERS] Weekly refresh scheduled for "
                  f"{next_run.strftime('%Y-%m-%d %H:%M UTC')} ({sleep_secs/3600:.1f}h from now)")
            _time.sleep(sleep_secs)
            try:
                print("[MLB ROSTERS] Starting weekly roster refresh...")
                from models import get_engine, get_session
                from populate_mlb_players import refresh_all_rosters
                engine  = get_engine()
                session = get_session(engine)
                try:
                    refresh_all_rosters(session)
                finally:
                    session.close()
                print("[MLB ROSTERS] Roster refresh complete")
            except Exception as _e:
                print(f"[MLB ROSTERS] Roster refresh failed: {_e}")

    threading.Thread(target=_run, daemon=True).start()


_schedule_daily_mlb_update()
_schedule_daily_soccer_cache_refresh()
_schedule_weekly_soccer_stats_update()
_schedule_weekly_mlb_roster_refresh()

if __name__ == '__main__':
    print("[INFO] Starting StatScout API Server...")
    print("[INFO] API available at: http://localhost:5000")
    print("[INFO] Health check: http://localhost:5000/api/health")
    print("[INFO] All players: http://localhost:5000/api/players")
    app.run(debug=True, port=5000)