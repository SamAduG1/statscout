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

# Soccer match cache - one entry per league
SOCCER_CACHE_DURATION = 6 * 60 * 60  # 6 hours
SOCCER_CACHE_FILES = {
    "pl":     "/tmp/statscout_soccer_pl_cache.json",
    "laliga": "/tmp/statscout_soccer_laliga_cache.json",
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
CACHE_DURATION = 4 * 60 * 60  # 4 hours (was 30 minutes)
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


@app.route('/api/debug/odds-sports', methods=['GET'])
def debug_odds_sports():
    """List all sport keys available on the current Odds API plan."""
    import requests as _req
    key = os.getenv('ODDS_API_KEY', '').strip()
    if not key:
        return jsonify({"error": "ODDS_API_KEY not set"}), 500
    r = _req.get("https://api.the-odds-api.com/v4/sports",
                 params={"apiKey": key}, timeout=10)
    return jsonify(r.json()), r.status_code


@app.route('/api/debug/soccer-fetch', methods=['GET'])
def debug_soccer_fetch():
    """Run soccer fetch synchronously and return diagnostics."""
    import requests as _req, time as _time
    league = request.args.get('league', 'pl')
    result = {"league": league, "steps": []}
    t0 = _time.time()

    # Step 1: football-data.org
    fd_key = os.getenv('FOOTBALL_DATA_KEY', '').strip()
    result["fd_key_set"] = bool(fd_key)
    from soccer_fetcher import COMPETITIONS, SEASON
    conf = COMPETITIONS.get(league, COMPETITIONS["pl"])
    try:
        r = _req.get(
            f"https://api.football-data.org/v4/competitions/{conf['fd_code']}/matches",
            headers={"X-Auth-Token": fd_key},
            params={"season": SEASON, "status": "FINISHED"},
            timeout=15,
        )
        result["steps"].append({
            "step": "football-data.org",
            "status": r.status_code,
            "matches": len(r.json().get("matches", [])) if r.status_code == 200 else None,
            "elapsed": round(_time.time() - t0, 2),
        })
    except Exception as e:
        result["steps"].append({"step": "football-data.org", "error": str(e), "elapsed": round(_time.time() - t0, 2)})

    # Step 2: Odds API
    odds_key = os.getenv('ODDS_API_KEY', '').strip()
    result["odds_key_set"] = bool(odds_key)
    t1 = _time.time()
    try:
        r2 = _req.get(
            f"https://api.the-odds-api.com/v4/sports/{conf['odds_sport']}/odds",
            params={"apiKey": odds_key, "markets": "totals",
                    "regions": conf["regions"], "oddsFormat": "american"},
            timeout=10,
        )
        result["steps"].append({
            "step": "odds-api",
            "status": r2.status_code,
            "remaining": r2.headers.get("x-requests-remaining"),
            "events": len(r2.json()) if r2.status_code == 200 else None,
            "error": r2.json() if r2.status_code != 200 else None,
            "elapsed": round(_time.time() - t1, 2),
        })
    except Exception as e:
        result["steps"].append({"step": "odds-api", "error": str(e), "elapsed": round(_time.time() - t1, 2)})

    return jsonify(result)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "StatScout API is running",
        "players_loaded": players_cache["data"]["count"] if players_cache["data"] else 0,
        "soccer_pl_loaded": soccer_caches["pl"]["data"]["count"] if soccer_caches["pl"]["data"] else 0,
        "soccer_laliga_loaded": soccer_caches["laliga"]["data"]["count"] if soccer_caches["laliga"]["data"] else 0,
    })


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


# Start background cache builds after all routes are defined
_build_players_cache_background()
_build_soccer_cache_background('pl')  # La Liga loads lazily on first request

if __name__ == '__main__':
    print("[INFO] Starting StatScout API Server...")
    print("[INFO] API available at: http://localhost:5000")
    print("[INFO] Health check: http://localhost:5000/api/health")
    print("[INFO] All players: http://localhost:5000/api/players")
    app.run(debug=True, port=5000)