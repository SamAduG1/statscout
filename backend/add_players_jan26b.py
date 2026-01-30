"""Add more players"""
import os
os.environ['DATABASE_URL'] = r'postgresql://postgres.tqyzxwogjhehjcwhxnre:Softwareidk5852!@aws-1-us-east-2.pooler.supabase.com:6543/postgres'

from models import get_engine, get_session, Player, Game
from nba_stats_fetcher import NBAStatsFetcher
from datetime import datetime
import time

engine = get_engine()
session = get_session(engine)
fetcher = NBAStatsFetcher()

# First, let's search for Cedric Coward in the NBA API
print("=" * 60)
print("SEARCHING FOR CEDRIC COWARD")
print("=" * 60)

# Search all players for "Coward" or "Cedric"
for player in fetcher.all_players:
    name = player['full_name'].lower()
    if 'coward' in name or 'cedric' in name:
        print(f"Found: {player['full_name']} - ID: {player['id']}")

# Also search for similar names
print("\nSearching for MEM rookies/recent players...")
for player in fetcher.all_players:
    name = player['full_name'].lower()
    # Search for any name starting with 'c' that might be similar
    if player.get('is_active', False) and ('ced' in name or 'cow' in name):
        print(f"Found: {player['full_name']} - ID: {player['id']}")

# Players to add
new_players = [
    {"name": "Vince Williams Jr.", "team": "MEM", "position": "SG"},
    {"name": "Jake LaRavia", "team": "LAL", "position": "SF"},
    {"name": "GG Jackson II", "team": "MEM", "position": "PF"},
    {"name": "Cedric Coward", "team": "MEM", "position": "G"},  # Try anyway
]

print("\n" + "=" * 60)
print("ADDING NEW PLAYERS")
print("=" * 60)

for p in new_players:
    print(f"\n[INFO] Adding {p['name']} ({p['team']})...")

    # Check if already exists
    existing = session.query(Player).filter_by(name=p['name']).first()
    if existing:
        print(f"  Already exists with ID {existing.id}")
        continue

    # Fetch games
    time.sleep(0.6)
    games = fetcher.fetch_player_season(p['name'], p['team'], p['position'], '2025-26')

    if not games:
        print(f"  No games found from NBA API")
        continue

    print(f"  Found {len(games)} games")

    # Create player
    player = Player(name=p['name'], team=p['team'], position=p['position'])
    session.add(player)
    session.flush()
    print(f"  Created player with ID {player.id}")

    # Add games
    for g in games:
        game_date = datetime.strptime(g['date'], '%Y-%m-%d').date()
        new_game = Game(
            player_id=player.id,
            date=game_date,
            opponent=g['opponent'],
            is_home=g['is_home'],
            points=g['points'],
            rebounds=g['rebounds'],
            assists=g['assists'],
            steals=g['steals'],
            blocks=g['blocks'],
            three_pm=g['three_pm'],
            minutes=g.get('minutes')
        )
        session.add(new_game)

    session.commit()
    print(f"  Added {len(games)} games")

session.close()
print("\nDone!")
