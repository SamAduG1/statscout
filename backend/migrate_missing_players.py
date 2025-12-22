"""
Migrate missing players data to SQLite database
"""
import sys
import io
import pandas as pd
from datetime import datetime
from models import get_engine, get_session, init_db, Player, Game

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def migrate_missing_players():
    """Load missing players CSV and migrate to database"""

    print("[INFO] Loading missing players data from CSV...")
    df = pd.read_csv("data/missing_players_stats.csv")
    print(f"[INFO] Loaded {len(df)} games from CSV")

    # Get engine and session
    engine = get_engine()
    init_db(engine)  # Ensure tables exist
    session = get_session(engine)

    try:
        # Get unique players
        unique_players = df[['player_name', 'team', 'position']].drop_duplicates()
        print(f"[INFO] Found {len(unique_players)} unique players")

        # Add/update players
        players_added = 0
        player_map = {}

        for _, row in unique_players.iterrows():
            # Check if player already exists
            existing = session.query(Player).filter_by(name=row['player_name']).first()

            if existing:
                print(f"[INFO] Player {row['player_name']} already exists with ID {existing.id}")
                player_map[row['player_name']] = existing.id
            else:
                player = Player(
                    name=row['player_name'],
                    team=row['team'],
                    position=row['position']
                )
                session.add(player)
                session.flush()  # Get the ID
                player_map[row['player_name']] = player.id
                players_added += 1
                print(f"[INFO] Adding new player: {row['player_name']} (ID: {player.id})")

        session.commit()
        print(f"[SUCCESS] Added {players_added} new players")

        # Add games
        games_added = 0
        for idx, row in df.iterrows():
            # Convert date string to date object
            game_date = datetime.strptime(row['date'], '%Y-%m-%d').date()

            # Check if game already exists
            existing_game = session.query(Game).filter_by(
                player_id=player_map[row['player_name']],
                date=game_date,
                opponent=row['opponent']
            ).first()

            if not existing_game:
                game = Game(
                    player_id=player_map[row['player_name']],
                    date=game_date,
                    opponent=row['opponent'],
                    is_home=bool(row['is_home']),
                    points=int(row['points']),
                    rebounds=int(row['rebounds']),
                    assists=int(row['assists']),
                    steals=int(row['steals']),
                    blocks=int(row['blocks']),
                    three_pm=int(row['three_pm'])
                )
                session.add(game)
                games_added += 1

                # Progress update every 50 games
                if games_added % 50 == 0:
                    print(f"[INFO] Progress: {games_added}/{len(df)} games inserted...")

        session.commit()
        print(f"[SUCCESS] Inserted {games_added} new games")

        # Print summary
        print("\n[SUCCESS] Migration complete!")
        total_players = session.query(Player).count()
        total_games = session.query(Game).count()
        print(f"[INFO] Database now has {total_players} players and {total_games} games")

    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATING MISSING PLAYERS TO DATABASE")
    print("=" * 60)
    migrate_missing_players()
