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
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize calculator, data loader, odds API client, and schedule fetcher
calc = StatScoutCalculator()
loader = DataLoader()
odds_client = OddsAPIClient()
schedule_fetcher = NBAScheduleFetcher()

# Initialize background scheduler for automated updates
from scheduler import init_scheduler
scheduler = init_scheduler()

# Cache for odds data (refresh every 30 minutes)
odds_cache = {
    "data": {},
    "last_updated": None
}

def get_cached_odds():
    """Get odds from cache or fetch new ones"""
    now = datetime.now()

    # Check if cache is expired (30 minutes)
    if (odds_cache["last_updated"] is None or
        (now - odds_cache["last_updated"]).seconds > 1800):

        print("[INFO] Fetching fresh odds from API...")
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
        else:
            print(f"[WARNING] Could not fetch odds: {response.get('error')}")

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
    
    return jsonify({
        "success": True,
        "api_status": usage,
        "cache": {
            "props_cached": len(odds_cache["data"]),
            "last_updated": odds_cache["last_updated"].isoformat() if odds_cache["last_updated"] else None
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
                analysis = calc.analyze_player_prop(
                    player_name=player_name,
                    team=team,
                    stat_type=display_stat_type,
                    player_stats=stat_values,
                    line=line,
                    opponent=opponent,
                    opponent_rank=opponent_rank,
                    is_home=is_home
                )
                
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
                    "streakType": analysis["streak_type"]
                }
                
                players_list.append(player_prop)
                player_id += 1
        
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
                is_home=random.choice([True, False])
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
            
            # Find matching stat in all_stats
            matched_stat = None
            for key in all_stats.keys():
                if key.lower() == stat_type_lower or key.upper() == stat_type:
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
                is_home=is_home
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
            is_home=data.get('is_home', True)
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
    """Manually trigger a stats update"""
    try:
        from update_stats import update_all_players

        print("\n[INFO] Manual update triggered via API")
        result = update_all_players()

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("[INFO] Starting StatScout API Server...")
    print("[INFO] API available at: http://localhost:5000")
    print("[INFO] Health check: http://localhost:5000/api/health")
    print("[INFO] All players: http://localhost:5000/api/players")
    app.run(debug=True, port=5000)