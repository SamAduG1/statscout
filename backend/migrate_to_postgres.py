"""
Migrate data from SQLite to PostgreSQL
Run this script after setting up PostgreSQL on Render
"""

import os
import sys
from models import get_engine, get_session, Base, Player, Game, TeamGame
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def migrate_data(sqlite_path='sqlite:///statscout.db', postgres_url=None):
    """
    Migrate all data from SQLite to PostgreSQL

    Args:
        sqlite_path: Path to SQLite database
        postgres_url: PostgreSQL connection URL (from DATABASE_URL env var if not provided)
    """

    # Get PostgreSQL URL from environment if not provided
    if postgres_url is None:
        postgres_url = os.environ.get('DATABASE_URL')
        if not postgres_url:
            print("ERROR: DATABASE_URL environment variable not set")
            print("Set it to your Render PostgreSQL URL")
            return False

    # Fix postgres:// -> postgresql://
    if postgres_url.startswith('postgres://'):
        postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)

    print("=" * 60)
    print("StatScout Database Migration: SQLite → PostgreSQL")
    print("=" * 60)

    try:
        # Connect to SQLite (source)
        print(f"\n[1/5] Connecting to SQLite database...")
        sqlite_engine = create_engine(sqlite_path, echo=False)
        SqliteSession = sessionmaker(bind=sqlite_engine)
        sqlite_session = SqliteSession()

        # Count records in SQLite
        player_count = sqlite_session.query(Player).count()
        game_count = sqlite_session.query(Game).count()
        team_game_count = sqlite_session.query(TeamGame).count()

        print(f"  ✓ Found {player_count} players")
        print(f"  ✓ Found {game_count} games")
        print(f"  ✓ Found {team_game_count} team games")

        if player_count == 0:
            print("\n⚠️  No data found in SQLite database!")
            return False

        # Connect to PostgreSQL (destination)
        print(f"\n[2/5] Connecting to PostgreSQL...")
        postgres_engine = create_engine(postgres_url, echo=False)
        PostgresSession = sessionmaker(bind=postgres_engine)
        postgres_session = PostgresSession()

        print(f"  ✓ Connected to PostgreSQL")

        # Create tables in PostgreSQL
        print(f"\n[3/5] Creating tables in PostgreSQL...")
        Base.metadata.create_all(postgres_engine)
        print(f"  ✓ Tables created")

        # Migrate Players
        print(f"\n[4/5] Migrating players...")
        players = sqlite_session.query(Player).all()

        for i, player in enumerate(players, 1):
            # Create new player object (detached from SQLite session)
            new_player = Player(
                name=player.name,
                team=player.team,
                position=player.position
            )
            postgres_session.add(new_player)

            if i % 50 == 0:
                print(f"  ✓ Migrated {i}/{player_count} players...")

        postgres_session.commit()
        print(f"  ✓ All {player_count} players migrated")

        # Get player ID mapping (SQLite ID -> PostgreSQL ID)
        print(f"\n[5/5] Migrating games...")
        sqlite_players = {p.name: p.id for p in sqlite_session.query(Player).all()}
        postgres_players = {p.name: p.id for p in postgres_session.query(Player).all()}

        # Migrate Games
        games = sqlite_session.query(Game).all()

        for i, game in enumerate(games, 1):
            # Get corresponding PostgreSQL player ID
            player_name = sqlite_session.query(Player).filter(Player.id == game.player_id).first().name
            new_player_id = postgres_players[player_name]

            new_game = Game(
                player_id=new_player_id,
                date=game.date,
                opponent=game.opponent,
                is_home=game.is_home,
                points=game.points,
                rebounds=game.rebounds,
                assists=game.assists,
                steals=game.steals,
                blocks=game.blocks,
                three_pm=game.three_pm,
                minutes=game.minutes
            )
            postgres_session.add(new_game)

            if i % 100 == 0:
                print(f"  ✓ Migrated {i}/{game_count} games...")
                postgres_session.commit()  # Commit in batches

        postgres_session.commit()
        print(f"  ✓ All {game_count} games migrated")

        # Migrate TeamGames
        if team_game_count > 0:
            print(f"\n[6/5] Migrating team games...")
            team_games = sqlite_session.query(TeamGame).all()

            for i, tg in enumerate(team_games, 1):
                new_team_game = TeamGame(
                    game_id=tg.game_id,
                    team=tg.team,
                    opponent=tg.opponent,
                    date=tg.date,
                    is_home=tg.is_home,
                    season=tg.season,
                    q1_points=tg.q1_points,
                    q2_points=tg.q2_points,
                    q3_points=tg.q3_points,
                    q4_points=tg.q4_points,
                    ot_points=tg.ot_points,
                    total_points=tg.total_points,
                    opponent_points=tg.opponent_points,
                    won=tg.won
                )
                postgres_session.add(new_team_game)

                if i % 100 == 0:
                    print(f"  ✓ Migrated {i}/{team_game_count} team games...")
                    postgres_session.commit()

            postgres_session.commit()
            print(f"  ✓ All {team_game_count} team games migrated")

        # Verify migration
        print(f"\n" + "=" * 60)
        print("Verifying migration...")
        print("=" * 60)

        pg_player_count = postgres_session.query(Player).count()
        pg_game_count = postgres_session.query(Game).count()
        pg_team_game_count = postgres_session.query(TeamGame).count()

        print(f"\nPostgreSQL database now contains:")
        print(f"  • {pg_player_count} players (expected {player_count})")
        print(f"  • {pg_game_count} games (expected {game_count})")
        print(f"  • {pg_team_game_count} team games (expected {team_game_count})")

        if pg_player_count == player_count and pg_game_count == game_count:
            print(f"\n✅ Migration completed successfully!")
            print(f"\nNext steps:")
            print(f"1. Set DATABASE_URL environment variable in Render")
            print(f"2. Deploy the updated code")
            print(f"3. Remove statscout.db from git")
            return True
        else:
            print(f"\n⚠️  Migration completed but counts don't match!")
            return False

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        sqlite_session.close()
        postgres_session.close()


if __name__ == "__main__":
    print("\n🔄 Starting database migration...\n")

    # Check for DATABASE_URL
    if not os.environ.get('DATABASE_URL'):
        print("⚠️  DATABASE_URL environment variable not set!")
        print("\nTo run this migration:")
        print("1. Create PostgreSQL database in Render")
        print("2. Copy the Internal Database URL")
        print("3. Run: set DATABASE_URL=<your-postgres-url>")
        print("4. Run: python migrate_to_postgres.py")
        sys.exit(1)

    success = migrate_data()
    sys.exit(0 if success else 1)
