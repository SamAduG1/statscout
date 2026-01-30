"""Fix duplicates and verify"""
import os
os.environ['DATABASE_URL'] = r'postgresql://postgres.tqyzxwogjhehjcwhxnre:Softwareidk5852!@aws-1-us-east-2.pooler.supabase.com:6543/postgres'

from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

with engine.connect() as conn:
    # Count before
    result = conn.execute(text('SELECT COUNT(*) FROM games'))
    before = result.fetchone()[0]
    print(f'Games before cleanup: {before}')

    # Count duplicates
    result = conn.execute(text('''
        SELECT COUNT(*) FROM (
            SELECT g1.id FROM games g1
            JOIN games g2 ON g1.player_id = g2.player_id
                AND g1.date = g2.date AND g1.id > g2.id
        ) d
    '''))
    dupe_count = result.fetchone()[0]
    print(f'Duplicates found: {dupe_count}')

    if dupe_count > 0:
        # Delete duplicates (keep lowest ID which is usually the first/correct one)
        print('Deleting duplicates...')
        result = conn.execute(text('''
            DELETE FROM games
            WHERE id IN (
                SELECT g1.id FROM games g1
                JOIN games g2 ON g1.player_id = g2.player_id
                    AND g1.date = g2.date AND g1.id > g2.id
            )
        '''))
        deleted = result.rowcount
        conn.commit()
        print(f'Deleted {deleted} duplicate games')

    # Count after
    result = conn.execute(text('SELECT COUNT(*) FROM games'))
    after = result.fetchone()[0]
    print(f'Games after cleanup: {after}')

    # Verify no duplicates
    result = conn.execute(text('''
        SELECT COUNT(*) FROM (
            SELECT g1.id FROM games g1
            JOIN games g2 ON g1.player_id = g2.player_id
                AND g1.date = g2.date AND g1.id > g2.id
        ) d
    '''))
    remaining = result.fetchone()[0]
    print(f'Duplicates remaining: {remaining}')

    # Now normalize all opponent abbreviations in the database
    print()
    print('Normalizing opponent abbreviations...')

    normalizations = [
        ('GS', 'GSW'),
        ('SA', 'SAS'),
        ('NO', 'NOP'),
        ('NY', 'NYK'),
        ('WSH', 'WAS'),
        ('PHO', 'PHX'),
        ('UTAH', 'UTA'),
    ]

    for old, new in normalizations:
        result = conn.execute(text(f"UPDATE games SET opponent = '{new}' WHERE opponent = '{old}'"))
        if result.rowcount > 0:
            print(f'  {old} -> {new}: {result.rowcount} games updated')

    conn.commit()
    print('Normalization complete!')
