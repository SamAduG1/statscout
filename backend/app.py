"""
StatScout Flask API Server
Serves player prop data and analytics to the frontend
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
from datetime import datetime, timedelta
import random

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

# Initialize background scheduler for automated updates
from scheduler import init_scheduler
scheduler = init_scheduler()

# Cache for odds data (optimized to conserve API quota)
odds_cache = {
    "data": {},
    "last_updated": None
}

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
            print(f"[SUCCESS] Cached {len(parsed_props)} odds from {len(set(p['bookmaker'] for p in parsed_props))} bookmakers")
            print(f"[INFO] Next refresh after: {(now + timedelta(seconds=CACHE_DURATION)).strftime('%I:%M %p')}")
        else:
            print(f"[WARNING] Could not fetch odds: {response.get('error')}")
    elif cache_expired and not is_active_hours():
        print(f"[INFO] Cache expired but outside active hours ({ACTIVE_HOURS_START}:00-{ACTIVE_HOURS_END}:00). Using stale cache.")
    else:
        cache_age = (now - odds_cache["last_updated"]).total_seconds() / 3600 if odds_cache["last_updated"] else 0
        print(f"[INFO] Using cached odds (age: {cache_age:.1f} hours)")

    return odds_cache["data"]

# Verify database connection on startup
try:
    player_count = len(loader.get_player_names())
    print(f"[SUCCESS] Database connected successfully - {player_count} players loaded")
except Exception as e:
    print(f"[ERROR] Error connecting to database: {e}")

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


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        player_count = len(loader.get_player_names())
    except:
        player_count = 0

    return jsonify({
        "status": "healthy",
        "message": "StatScout API is running",
        "players_loaded": player_count
    })


@app.route('/api/players', methods=['GET'])
def get_all_players():
    """Get all available player props"""
    
    # Get query parameters for filtering
    team_filter = request.args.get('team', 'all')
    stat_filter = request.args.get('stat', 'all')
    
    try:
        players_list = []
        player_id = 1

        # Get all players from CSV
        player_names = loader.get_player_names()

        # Get list of all teams for opponent selection
        all_teams = loader.get_teams()

        # CRITICAL PERFORMANCE FIX: Pre-fetch injuries ONCE for the entire request
        # This prevents calling ESPN API hundreds of times (one per player+stat combination)!
        injury_tracker.get_all_injuries()

        # Cache game info by team to avoid repeated lookups
        team_game_cache = {}

        for player_name in player_names:
            player_info = loader.get_player_info(player_name)
            
            if not player_info:
                continue
            
            team = player_info["team"]
            
            # Team filter
            if team_filter != 'all' and team != team_filter:
                continue
            
            # Get all available stats for this player
            all_stats = loader.get_all_available_stats(player_name)
            
            # Process each stat type
            for stat_type, stat_values in all_stats.items():
                # Format stat type for display
                if stat_type == 'three_pm':
                    display_stat_type = '3PM'
                elif len(stat_type) <= 3:
                    display_stat_type = stat_type.upper()
                else:
                    display_stat_type = stat_type.title()
                
                # Stat filter
                if stat_filter != 'all' and display_stat_type.lower() != stat_filter.lower():
                    continue
                
                if len(stat_values) < 5:  # Need at least 5 games
                    continue

                # Calculate average
                avg_stat = sum(stat_values) / len(stat_values)

                # Try to get real betting lines from odds API
                cached_odds = get_cached_odds()
                odds_key = f"{player_name}_{display_stat_type}"

                bookmaker_lines = []
                is_real_line = False

                if odds_key in cached_odds:
                    # Use real betting lines from multiple bookmakers
                    bookmaker_lines = cached_odds[odds_key]
                    # Use the first bookmaker's line as the primary line
                    line = bookmaker_lines[0]["line"] if bookmaker_lines else STAT_LINES.get(display_stat_type, lambda x: round(x - 0.5, 1))(avg_stat)
                    is_real_line = True if bookmaker_lines else False
                else:
                    # Fallback to calculated line based on average
                    line = STAT_LINES.get(display_stat_type, lambda x: round(x - 0.5, 1))(avg_stat)
                    is_real_line = False

                # Get real game matchup from schedule (cached by team)
                if team not in team_game_cache:
                    team_game_cache[team] = schedule_fetcher.get_player_next_game(team)

                next_game = team_game_cache[team]

                if next_game:
                    # Use real game data
                    opponent = next_game['opponent']
                    is_home = next_game['is_home']
                    game_date = next_game['game_date']
                    game_time = next_game['game_time']
                    opponent_rank = random.randint(5, 25)  # Still mock for now
                else:
                    # No game found in betting lines - show placeholder
                    opponent = "TBD"
                    opponent_rank = random.randint(5, 25)
                    is_home = True
                    game_date = "TBD"
                    game_time = "TBD"

                # Calculate all analytics
                # TEMPORARY: Skip teammate boost to reduce memory usage on free tier
                # TODO: Re-enable after optimizing or upgrading to paid tier
                analysis = calc.analyze_player_prop(
                    player_name=player_name,
                    team=team,
                    stat_type=display_stat_type,
                    player_stats=stat_values,
                    line=line,
                    opponent=opponent,
                    opponent_rank=opponent_rank,
                    is_home=is_home,
                    db_loader=None  # Temporarily disabled for memory
                )

                # Calculate home/away location split
                split_data = loader.get_home_away_splits(player_name, display_stat_type)
                location_split = calc.analyze_location_split(split_data, is_home) if split_data else {"has_data": False}

                # Format for frontend
                player_prop = {
                    "id": player_id,
                    "name": player_name,
                    "team": team,
                    "teamColor": TEAM_COLORS.get(team, "#000000"),
                    "position": player_info["position"],
                    "statType": display_stat_type,
                    "line": line,
                    "isRealLine": is_real_line,  # Flag if line is from real odds API
                    "bookmakerLines": bookmaker_lines,  # All available bookmaker lines
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
                    "avgMinutes": player_info.get("avg_minutes", 0),
                    "locationSplit": location_split  # Home/Away performance split
                }
                
                players_list.append(player_prop)
                player_id += 1

        # Get injury status for all players in batch
        all_player_names = list(set([p["name"] for p in players_list]))
        injury_statuses = injury_tracker.get_batch_status(all_player_names)

        # Add injury status to each player
        for player in players_list:
            player_status = injury_statuses.get(player["name"], {"status": "ACTIVE", "source": "default"})
            player["injuryStatus"] = player_status["status"]
            player["injurySource"] = player_status.get("source", "default")

        return jsonify({
            "success": True,
            "count": len(players_list),
            "players": players_list
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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
            if len(stat_values) < 5:
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
            
            # Get player info
            player_info = loader.get_player_info(player_name)
            if not player_info:
                return jsonify({"success": False, "error": "Player not found"}), 404
            
            # Get all available stats
            all_stats = loader.get_all_available_stats(player_name)
            
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
            
            # Get opponent info (use defaults or from request)
            all_teams = loader.get_teams()
            opponents = [t for t in all_teams if t != player_info["team"]]
            opponent = data.get('opponent', random.choice(opponents) if opponents else "OPP")
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

        # Get all available props by calling the get_all_players logic
        # This reuses the same data pipeline as the /api/players endpoint
        all_props = []

        # Helper function for case and accent-insensitive name matching
        import unicodedata
        def normalize_name(name):
            """Remove accents and convert to lowercase for comparison"""
            # Remove accents (é -> e, ñ -> n, etc.)
            nfd = unicodedata.normalize('NFD', name)
            without_accents = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
            return without_accents.lower().strip()

        # Normalize banned player names for comparison
        normalized_banned = [normalize_name(p) for p in banned_players]

        player_names = loader.get_player_names()

        # Pre-fetch injuries once for performance
        injury_tracker.get_all_injuries()

        # Cache game info by team
        team_game_cache = {}

        for player_name in player_names:
            # Check if player is banned (case and accent insensitive)
            if normalize_name(player_name) in normalized_banned:
                continue  # Skip banned players
            player_info = loader.get_player_info(player_name)

            if not player_info:
                continue

            team = player_info["team"]
            all_stats = loader.get_all_available_stats(player_name)

            # Process each stat type
            for stat_type, stat_values in all_stats.items():
                # Format stat type for display
                if stat_type == 'three_pm':
                    display_stat_type = '3PM'
                elif len(stat_type) <= 3:
                    display_stat_type = stat_type.upper()
                else:
                    display_stat_type = stat_type.title()

                if len(stat_values) < 5:
                    continue

                avg_stat = sum(stat_values) / len(stat_values)

                # Get real betting lines
                cached_odds = get_cached_odds()
                odds_key = f"{player_name}_{display_stat_type}"

                # Try to use real odds, fallback to calculated lines
                line = None
                odds = -110  # Default odds

                if odds_key in cached_odds and cached_odds[odds_key]:
                    # Use real betting lines from bookmaker
                    bookmaker_lines = cached_odds[odds_key]
                    if bookmaker_lines:
                        first_bookmaker = bookmaker_lines[0]
                        line = first_bookmaker.get("line")
                        odds = first_bookmaker.get("over_odds", -110)

                # Fallback to calculated line if no real odds
                if line is None:
                    line = STAT_LINES.get(display_stat_type, lambda x: round(x - 0.5, 1))(avg_stat)

                # Get game matchup
                if team not in team_game_cache:
                    team_game_cache[team] = schedule_fetcher.get_player_next_game(team)

                next_game = team_game_cache[team]
                if not next_game:
                    continue  # Skip props without scheduled games

                opponent = next_game['opponent']
                is_home = next_game['is_home']

                # Calculate trust score using full analysis
                analysis = calc.analyze_player_prop(
                    player_name=player_name,
                    team=team,
                    stat_type=display_stat_type,
                    player_stats=stat_values,
                    line=line,
                    opponent=opponent,
                    opponent_rank=15,  # Default middle-of-pack
                    is_home=is_home,
                    db_loader=loader
                )

                # Check injury status - skip injured/questionable players
                injury_status = injury_tracker.get_player_status(player_name)
                if injury_status:
                    status = injury_status.get('status', '')
                    # Skip OUT and QUESTIONABLE players from parlays
                    if status in ['OUT', 'QUESTIONABLE', 'DOUBTFUL']:
                        continue  # Don't include injured players in parlay pool

                # Add to available props for parlay building
                all_props.append({
                    'player_name': player_name,
                    'team': team,
                    'opponent': opponent,
                    'stat_type': display_stat_type,
                    'line': line,
                    'odds': odds,
                    'trust_score': analysis['trust_score'],
                    'is_home': is_home
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


if __name__ == '__main__':
    print("[INFO] Starting StatScout API Server...")
    print("[INFO] API available at: http://localhost:5000")
    print("[INFO] Health check: http://localhost:5000/api/health")
    print("[INFO] All players: http://localhost:5000/api/players")
    app.run(debug=True, port=5000)