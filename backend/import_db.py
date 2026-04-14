"""
Import data from db_export.json into Neon PostgreSQL.
Run from the backend directory: python import_db.py
"""
import json
import psycopg2
from psycopg2.extras import execute_values

NEON_URL = "postgresql://neondb_owner:npg_dxRS50EMonml@ep-twilight-wind-aeqki84n-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"

print("Loading export file...")
with open("db_export.json", "r") as f:
    data = json.load(f)

players = data["players"]
games = data["games"]
print(f"Loaded {len(players)} players, {len(games)} games")

print("Connecting to Neon...")
conn = psycopg2.connect(NEON_URL)
cur = conn.cursor()

# Create tables
print("Creating tables...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id SERIAL PRIMARY KEY,
        name VARCHAR UNIQUE NOT NULL,
        team VARCHAR NOT NULL,
        position VARCHAR NOT NULL
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS games (
        id SERIAL PRIMARY KEY,
        player_id INTEGER NOT NULL REFERENCES players(id),
        date DATE NOT NULL,
        opponent VARCHAR NOT NULL,
        is_home BOOLEAN NOT NULL,
        points INTEGER NOT NULL,
        rebounds INTEGER NOT NULL,
        assists INTEGER NOT NULL,
        steals INTEGER NOT NULL,
        blocks INTEGER NOT NULL,
        three_pm INTEGER NOT NULL,
        minutes FLOAT,
        q1_points INTEGER,
        q2_points INTEGER,
        q3_points INTEGER,
        q4_points INTEGER,
        q1_rebounds INTEGER,
        q2_rebounds INTEGER,
        q3_rebounds INTEGER,
        q4_rebounds INTEGER,
        q1_assists INTEGER,
        q2_assists INTEGER,
        q3_assists INTEGER,
        q4_assists INTEGER
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS team_games (
        id SERIAL PRIMARY KEY,
        game_id VARCHAR UNIQUE NOT NULL,
        team VARCHAR NOT NULL,
        opponent VARCHAR NOT NULL,
        date DATE NOT NULL,
        is_home BOOLEAN NOT NULL,
        season VARCHAR NOT NULL,
        q1_points INTEGER,
        q2_points INTEGER,
        q3_points INTEGER,
        q4_points INTEGER,
        ot_points INTEGER DEFAULT 0,
        total_points INTEGER NOT NULL,
        opponent_points INTEGER NOT NULL,
        won BOOLEAN NOT NULL
    )
""")
conn.commit()
print("Tables created")

# Import players (preserve original IDs)
print("Importing players...")
execute_values(cur,
    "INSERT INTO players (id, name, team, position) VALUES %s ON CONFLICT DO NOTHING",
    [(p["id"], p["name"], p["team"], p["position"]) for p in players]
)
conn.commit()

# Reset players sequence so future inserts get correct auto-increment IDs
cur.execute("SELECT setval('players_id_seq', (SELECT MAX(id) FROM players))")
conn.commit()
print(f"  Imported {len(players)} players")

# Import games in batches of 1000
print("Importing games...")
batch_size = 1000
total = 0
for i in range(0, len(games), batch_size):
    batch = games[i:i+batch_size]
    execute_values(cur,
        """INSERT INTO games
           (id, player_id, date, opponent, is_home,
            points, rebounds, assists, steals, blocks, three_pm, minutes)
           VALUES %s ON CONFLICT DO NOTHING""",
        [(g["id"], g["player_id"], g["date"], g["opponent"], g["is_home"],
          g["points"], g["rebounds"], g["assists"], g["steals"], g["blocks"],
          g["three_pm"], g.get("minutes")) for g in batch]
    )
    conn.commit()
    total += len(batch)
    print(f"  {total}/{len(games)} games imported...")

# Reset games sequence
cur.execute("SELECT setval('games_id_seq', (SELECT MAX(id) FROM games))")
conn.commit()

# Create indexes for performance
print("Creating indexes...")
cur.execute("CREATE INDEX IF NOT EXISTS idx_players_name ON players(name)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_players_team ON players(team)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_games_player_id ON games(player_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_games_date ON games(date)")
conn.commit()

cur.close()
conn.close()

print(f"\nImport complete!")
print(f"  {len(players)} players, {len(games)} games loaded into Neon")
