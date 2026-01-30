"""Fix PostgreSQL sequences for players and games tables"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres.tqyzxwogjhehjcwhxnre:Softwareidk5852!@aws-1-us-east-2.pooler.supabase.com:6543/postgres'

from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

with engine.connect() as conn:
    # Fix players sequence
    print("=" * 40)
    print("FIXING PLAYERS SEQUENCE")
    result = conn.execute(text('SELECT MAX(id) FROM players'))
    max_id = result.fetchone()[0] or 0
    print(f'Max player ID: {max_id}')

    result = conn.execute(text("SELECT last_value FROM players_id_seq"))
    seq_val = result.fetchone()[0]
    print(f'Sequence current value: {seq_val}')

    if max_id > seq_val:
        conn.execute(text(f"SELECT setval('players_id_seq', {max_id})"))
        conn.commit()
        print(f'Sequence reset to: {max_id}')
    else:
        print('Sequence already correct')

    # Fix games sequence
    print("\n" + "=" * 40)
    print("FIXING GAMES SEQUENCE")
    result = conn.execute(text('SELECT MAX(id) FROM games'))
    max_id = result.fetchone()[0] or 0
    print(f'Max game ID: {max_id}')

    result = conn.execute(text("SELECT last_value FROM games_id_seq"))
    seq_val = result.fetchone()[0]
    print(f'Sequence current value: {seq_val}')

    if max_id > seq_val:
        conn.execute(text(f"SELECT setval('games_id_seq', {max_id})"))
        conn.commit()
        print(f'Sequence reset to: {max_id}')
    else:
        print('Sequence already correct')

    print("\n" + "=" * 40)
    print('All sequences fixed!')
