"""
Fix Duplicate Games in Database
Removes duplicate games caused by different team abbreviations between NBA API and ESPN
(e.g., GSW vs GS, SAS vs SA, NOP vs NO)
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres.tqyzxwogjhehjcwhxnre:Softwareidk5852!@aws-1-us-east-2.pooler.supabase.com:6543/postgres'

from sqlalchemy import create_engine, text

def fix_duplicates():
    print("=" * 60)
    print("FIXING DUPLICATE GAMES")
    print("=" * 60)

    engine = create_engine(os.environ['DATABASE_URL'])

    with engine.connect() as conn:
        # Count duplicates before
        result = conn.execute(text('''
            SELECT COUNT(*) FROM (
                SELECT g1.id
                FROM games g1
                JOIN games g2 ON g1.player_id = g2.player_id
                    AND g1.date = g2.date
                    AND g1.id > g2.id
            ) dupes
        '''))
        before_count = result.fetchone()[0]
        print(f"\nDuplicate games found: {before_count}")

        if before_count == 0:
            print("No duplicates to fix!")
            return

        # Delete duplicates (keep the one with lower ID)
        print("\nDeleting duplicates (keeping first entry for each game)...")

        result = conn.execute(text('''
            DELETE FROM games
            WHERE id IN (
                SELECT g1.id
                FROM games g1
                JOIN games g2 ON g1.player_id = g2.player_id
                    AND g1.date = g2.date
                    AND g1.id > g2.id
            )
        '''))

        deleted = result.rowcount
        conn.commit()

        print(f"Deleted {deleted} duplicate games")

        # Verify
        result = conn.execute(text('SELECT COUNT(*) FROM games'))
        total = result.fetchone()[0]
        print(f"\nTotal games remaining: {total}")

        print("\n" + "=" * 60)
        print("DUPLICATE FIX COMPLETE!")
        print("=" * 60)


if __name__ == "__main__":
    fix_duplicates()
