"""
Add specific players to the database
"""
from nba_stats_fetcher import NBAStatsFetcher
from models import get_engine, init_db, get_session, Player, Game
from nba_api.stats.static import players as nba_players
import time

# List of players to add (name, team, position)
# Team and position will be fetched from NBA API
players_to_add = [
    "Sam Merrill"
]

print("=" * 60)
print("ADDING SPECIFIC PLAYERS TO DATABASE")
print("=" * 60)

# Initialize fetcher and database
fetcher = NBAStatsFetcher()
engine = get_engine()
init_db(engine)
session = get_session(engine)

# Get all NBA players
all_nba_players = nba_players.get_players()

# Add each player
for player_name in players_to_add:
    print(f"\nSearching for {player_name}...")

    # Find player in NBA API (active players only)
    player_info = [p for p in all_nba_players if p['full_name'].lower() == player_name.lower() and p.get('is_active', True)]

    if not player_info:
        # Try partial match (active players only)
        player_info = [p for p in all_nba_players if player_name.lower() in p['full_name'].lower() and p.get('is_active', True)]

    if not player_info:
        print(f"  ERROR: Player '{player_name}' not found in NBA database")
        continue

    # Use first match
    nba_player = player_info[0]
    player_id = nba_player['id']
    full_name = nba_player['full_name']

    print(f"  Found: {full_name} (ID: {player_id})")

    # Check if player already exists
    existing = session.query(Player).filter(Player.name == full_name).first()
    if existing:
        print(f"  Player already in database (Team: {existing.team}, Pos: {existing.position})")
        continue

    try:
        # Fetch game logs for 2025-26 season
        # We'll use a placeholder for team/position and update after fetching
        time.sleep(0.6)  # Rate limiting

        from nba_api.stats.endpoints import playergamelog
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season="2025-26")
        games_df = gamelog.get_data_frames()[0]

        if games_df.empty:
            print(f"  WARNING: No games found for {full_name} in 2025-26 season")
            continue

        # Get team and position from most recent game
        latest_game = games_df.iloc[0]
        team_abbr = latest_game['MATCHUP'].split()[0]  # e.g., "LAL vs. GSW" -> "LAL"

        # Try to infer position (default to F if unknown)
        position = "F"  # Default

        # Create player
        new_player = Player(
            name=full_name,
            team=team_abbr,
            position=position
        )
        session.add(new_player)
        session.flush()  # Get the player ID

        # Add games
        games_added = 0
        for _, game_row in games_df.iterrows():
            # Parse matchup to determine home/away and opponent
            matchup = game_row['MATCHUP']
            is_home = 'vs.' in matchup
            opponent = matchup.split()[-1]  # Get opponent team

            # Parse date string to Date object
            from datetime import datetime
            game_date = datetime.strptime(game_row['GAME_DATE'], '%b %d, %Y').date()

            # Parse minutes (can be a string like "32:15" or just a number)
            minutes_raw = game_row.get('MIN', 0)
            if isinstance(minutes_raw, str) and ':' in minutes_raw:
                # Format is "MM:SS", convert to decimal minutes
                parts = minutes_raw.split(':')
                minutes_played = float(parts[0]) + (float(parts[1]) / 60) if len(parts) == 2 else 0.0
            else:
                minutes_played = float(minutes_raw) if minutes_raw else 0.0

            game = Game(
                player_id=new_player.id,
                date=game_date,
                opponent=opponent,
                is_home=is_home,
                points=int(game_row.get('PTS', 0) or 0),
                rebounds=int(game_row.get('REB', 0) or 0),
                assists=int(game_row.get('AST', 0) or 0),
                steals=int(game_row.get('STL', 0) or 0),
                blocks=int(game_row.get('BLK', 0) or 0),
                three_pm=int(game_row.get('FG3M', 0) or 0),
                minutes=minutes_played
            )
            session.add(game)
            games_added += 1

        session.commit()
        print(f"  SUCCESS: Added {full_name} ({team_abbr}) with {games_added} games")

    except Exception as e:
        session.rollback()
        print(f"  ERROR: Could not add {full_name} - {e}")

session.close()

print("\n" + "=" * 60)
print("COMPLETE")
print("=" * 60)
