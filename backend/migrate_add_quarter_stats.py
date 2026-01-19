"""
Database Migration: Add Quarter-by-Quarter Stats to Games Table
Adds columns for Q1-Q4 points, rebounds, and assists
"""

from sqlalchemy import create_engine, text
import os

def run_migration():
    """Add quarter stat columns to games table"""

    # Get Supabase connection from environment or use default
    db_url = os.environ.get('DATABASE_URL',
                           'postgresql://postgres.tqyzxwogjhehjcwhxnre:Softwareidk5852!@aws-1-us-east-2.pooler.supabase.com:6543/postgres')

    print("=" * 60)
    print("MIGRATION: Adding Quarter Stats to Games Table")
    print("=" * 60)

    engine = create_engine(db_url)

    # SQL to add quarter columns
    alter_statements = [
        # Quarter Points
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q1_points INTEGER",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q2_points INTEGER",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q3_points INTEGER",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q4_points INTEGER",

        # Quarter Rebounds
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q1_rebounds INTEGER",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q2_rebounds INTEGER",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q3_rebounds INTEGER",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q4_rebounds INTEGER",

        # Quarter Assists
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q1_assists INTEGER",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q2_assists INTEGER",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q3_assists INTEGER",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS q4_assists INTEGER",
    ]

    try:
        with engine.connect() as conn:
            print("\n[1/2] Adding quarter stat columns...")

            for i, stmt in enumerate(alter_statements, 1):
                print(f"  [{i}/{len(alter_statements)}] {stmt[:50]}...")
                conn.execute(text(stmt))
                conn.commit()

            print("\n[2/2] Verifying columns...")
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'games'
                AND column_name LIKE 'q%'
                ORDER BY column_name
            """))

            columns = [row[0] for row in result]
            print(f"  Found {len(columns)} quarter stat columns:")
            for col in columns:
                print(f"    - {col}")

            print("\n" + "=" * 60)
            print("✅ MIGRATION COMPLETE!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Update nba_stats_fetcher.py to fetch quarter data")
            print("2. Run update_stats.py to populate quarter data")
            print("3. Test the new half/quarter analysis features")

    except Exception as e:
        print(f"\n❌ ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\nThis will add quarter-by-quarter stat columns to your games table.")
    print("Existing data will NOT be affected (new columns are nullable).\n")

    confirm = input("Type 'YES' to proceed: ").strip()

    if confirm.upper() == "YES":
        run_migration()
    else:
        print("\nMigration cancelled.")
