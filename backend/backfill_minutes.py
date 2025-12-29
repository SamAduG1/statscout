"""
Backfill minutes data for existing players
"""
from models import get_engine, get_session, Player, Game
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players as nba_players
import time
from datetime import datetime

print("=" * 60)
print("BACKFILLING MINUTES DATA FOR EXISTING PLAYERS")
print("=" * 60)

engine = get_engine()
session = get_session(engine)

# Get all players
all_players = session.query(Player).all()
all_nba_players = nba_players.get_players()

print(f"\nFound {len(all_players)} players in database")

updated_count = 0
skipped_count = 0
error_count = 0

for player in all_players:
    try:
        print(f"\nProcessing {player.name}...")
    except UnicodeEncodeError:
        print(f"\nProcessing player ID {player.id}...")

    # Check if any games already have minutes data
    games_with_minutes = session.query(Game).filter(
        Game.player_id == player.id,
        Game.minutes.isnot(None)
    ).count()

    if games_with_minutes > 0:
        print(f"  Skipping - already has minutes data for {games_with_minutes} games")
        skipped_count += 1
        continue

    try:
        # Find player in NBA API
        nba_player = [p for p in all_nba_players if p['full_name'].lower() == player.name.lower()]
        if not nba_player:
            print(f"  ERROR: Player not found in NBA API")
            error_count += 1
            continue

        player_id = nba_player[0]['id']

        # Rate limiting
        time.sleep(0.6)

        # Fetch game logs for 2025-26 season
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season="2025-26")
        games_df = gamelog.get_data_frames()[0]

        if games_df.empty:
            print(f"  WARNING: No games found in NBA API")
            error_count += 1
            continue

        # Get all games for this player from database
        db_games = session.query(Game).filter(Game.player_id == player.id).order_by(Game.date).all()

        # Match games by date and update minutes
        games_updated = 0
        for db_game in db_games:
            # Find matching game in NBA data
            matching_games = games_df[games_df['GAME_DATE'] == db_game.date.strftime('%b %d, %Y')]

            if not matching_games.empty:
                game_row = matching_games.iloc[0]

                # Parse minutes
                minutes_raw = game_row.get('MIN', 0)
                if isinstance(minutes_raw, str) and ':' in minutes_raw:
                    parts = minutes_raw.split(':')
                    minutes_played = float(parts[0]) + (float(parts[1]) / 60) if len(parts) == 2 else 0.0
                else:
                    minutes_played = float(minutes_raw) if minutes_raw else 0.0

                db_game.minutes = minutes_played
                games_updated += 1

        session.commit()
        print(f"  SUCCESS: Updated {games_updated} games with minutes data")
        updated_count += 1

    except Exception as e:
        session.rollback()
        print(f"  ERROR: {e}")
        error_count += 1

session.close()

print("\n" + "=" * 60)
print(f"BACKFILL COMPLETE")
print(f"  Players updated: {updated_count}")
print(f"  Players skipped: {skipped_count}")
print(f"  Errors: {error_count}")
print("=" * 60)
