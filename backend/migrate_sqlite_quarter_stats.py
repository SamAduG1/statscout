"""
Database Migration: Add Quarter-by-Quarter Stats to SQLite Games Table
Adds columns for Q1-Q4 points, rebounds, and assists
"""

from sqlalchemy import create_engine, text
import os

def run_migration():
    """Add quarter stat columns to games table (SQLite version)"""

    # Use SQLite for local development
    db_path = 'sqlite:///statscout.db'

    print("=" * 60)
    print("MIGRATION: Adding Quarter Stats to SQLite Games Table")
    print("=" * 60)

    engine = create_engine(db_path)

    # For SQLite, we need to check if columns exist first
    new_columns = [
        ('q1_points', 'INTEGER'),
        ('q2_points', 'INTEGER'),
        ('q3_points', 'INTEGER'),
        ('q4_points', 'INTEGER'),
        ('q1_rebounds', 'INTEGER'),
        ('q2_rebounds', 'INTEGER'),
        ('q3_rebounds', 'INTEGER'),
        ('q4_rebounds', 'INTEGER'),
        ('q1_assists', 'INTEGER'),
        ('q2_assists', 'INTEGER'),
        ('q3_assists', 'INTEGER'),
        ('q4_assists', 'INTEGER'),
    ]

    try:
        with engine.connect() as conn:
            # Get existing columns
            result = conn.execute(text("PRAGMA table_info(games)"))
            existing_columns = {row[1] for row in result}
            print(f"\nExisting columns: {len(existing_columns)}")

            print("\n[1/2] Adding quarter stat columns...")

            added_count = 0
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    stmt = f"ALTER TABLE games ADD COLUMN {col_name} {col_type}"
                    print(f"  Adding {col_name}...")
                    conn.execute(text(stmt))
                    conn.commit()
                    added_count += 1
                else:
                    print(f"  {col_name} already exists, skipping")

            print(f"\n[2/2] Verifying columns...")
            result = conn.execute(text("PRAGMA table_info(games)"))
            columns = [row[1] for row in result if row[1].startswith('q')]
            print(f"  Found {len(columns)} quarter stat columns:")
            for col in columns:
                print(f"    - {col}")

            print("\n" + "=" * 60)
            print(f"MIGRATION COMPLETE! Added {added_count} new columns.")
            print("=" * 60)

    except Exception as e:
        print(f"\nERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\nThis will add quarter-by-quarter stat columns to your SQLite games table.")
    print("Existing data will NOT be affected (new columns are nullable).\n")

    run_migration()
