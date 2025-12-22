"""
StatScout CSV to Database Migration Script
Loads player data from CSV into SQLite database
"""

import sys
import io
import pandas as pd
from datetime import datetime
from models import get_engine, get_session, init_db, drop_all_tables, Player, Game

# Force UTF-8 output for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def migrate_csv_to_database(csv_path='data/player_stats.csv', reset_db=True):
    """
    Migrate data from CSV to database
    
    Args:
        csv_path: Path to the CSV file
        reset_db: If True, drop and recreate all tables (fresh start)
    """
    print(" Starting CSV to Database Migration...")
    print(f" Reading CSV from: {csv_path}")
    
    # Create engine and initialize database
    engine = get_engine()
    
    if reset_db:
        print("  Resetting database (dropping all existing data)...")
        drop_all_tables(engine)
        init_db(engine)
    else:
        init_db(engine)
    
    session = get_session(engine)
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        print(f" Loaded {len(df)} game records from CSV")
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Get unique players
        unique_players = df[['player_name', 'team', 'position']].drop_duplicates()
        print(f" Found {len(unique_players)} unique players")
        
        # Dictionary to store player_id mapping
        player_map = {}
        
        # Insert players
        print("\n Inserting players into database...")
        for _, row in unique_players.iterrows():
            player = Player(
                name=row['player_name'],
                team=row['team'],
                position=row['position']
            )
            session.add(player)
            session.flush()  # Get the ID without committing
            player_map[row['player_name']] = player.id
            print(f"   {row['player_name']} ({row['team']}, {row['position']})")
        
        session.commit()
        print(f" {len(player_map)} players inserted")
        
        # Insert games
        print("\n Inserting game statistics...")
        games_inserted = 0
        
        for _, row in df.iterrows():
            game = Game(
                player_id=player_map[row['player_name']],
                date=row['date'],
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
            games_inserted += 1
            
            # Commit in batches for better performance
            if games_inserted % 100 == 0:
                session.commit()
                print(f"   {games_inserted} games inserted...")
        
        session.commit()
        print(f" {games_inserted} total games inserted")
        
        # Verify migration
        print("\n Verifying migration...")
        total_players = session.query(Player).count()
        total_games = session.query(Game).count()
        
        print(f"  Players in database: {total_players}")
        print(f"  Games in database: {total_games}")
        
        # Show sample data
        print("\n Sample players:")
        sample_players = session.query(Player).limit(5).all()
        for player in sample_players:
            game_count = session.query(Game).filter(Game.player_id == player.id).count()
            print(f"  - {player.name} ({player.team}): {game_count} games")
        
        print("\n Migration completed successfully!")
        print(f" Database: statscout.db")
        print(f" Total Players: {total_players}")
        print(f" Total Games: {total_games}")
        
        return True
        
    except Exception as e:
        print(f"\n Migration failed: {e}")
        session.rollback()
        return False
        
    finally:
        session.close()


if __name__ == "__main__":
    import os
    
    # Check if CSV exists
    csv_path = 'data/player_stats.csv'
    if not os.path.exists(csv_path):
        print(f" Error: CSV file not found at {csv_path}")
        print("Please make sure the CSV file exists before running migration.")
    else:
        # Run migration
        success = migrate_csv_to_database(csv_path, reset_db=True)
        
        if success:
            print("\n You can now use the database in your application!")
        else:
            print("\n  Migration encountered errors. Please check the output above.")