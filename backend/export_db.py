"""
Export all data from Supabase to a JSON file for migration to Neon.
Run from the backend directory: python export_db.py
"""
import json
import psycopg2

# Direct Supabase connection (runs from local machine, not Render)
SUPABASE_URL = input("Paste your Supabase direct connection string: ").strip()

print("Connecting to Supabase...")
conn = psycopg2.connect(SUPABASE_URL, connect_timeout=30, sslmode='require')
cur = conn.cursor()

# Export players
print("Exporting players...")
cur.execute("SELECT id, name, team, position FROM players ORDER BY id")
players = [
    {"id": row[0], "name": row[1], "team": row[2], "position": row[3]}
    for row in cur.fetchall()
]
print(f"  Found {len(players)} players")

# Export games
print("Exporting games...")
cur.execute("""
    SELECT id, player_id, date, opponent, is_home,
           points, rebounds, assists, steals, blocks, three_pm, minutes
    FROM games ORDER BY id
""")
games = []
for row in cur.fetchall():
    games.append({
        "id": row[0],
        "player_id": row[1],
        "date": str(row[2]),
        "opponent": row[3],
        "is_home": row[4],
        "points": row[5],
        "rebounds": row[6],
        "assists": row[7],
        "steals": row[8],
        "blocks": row[9],
        "three_pm": row[10],
        "minutes": row[11]
    })
print(f"  Found {len(games)} games")

cur.close()
conn.close()

# Save to file
output = {"players": players, "games": games}
with open("db_export.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nExport complete! Saved to backend/db_export.json")
print(f"  {len(players)} players, {len(games)} games")
