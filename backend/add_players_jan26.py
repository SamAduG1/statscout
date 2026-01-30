"""Add new players and fix Dylan Harper's team"""
import os
os.environ['DATABASE_URL'] = r'postgresql://postgres.tqyzxwogjhehjcwhxnre:Softwareidk5852!@aws-1-us-east-2.pooler.supabase.com:6543/postgres'

from models import get_engine, get_session, Player, Game
from nba_stats_fetcher import NBAStatsFetcher
from datetime import datetime
import time

engine = get_engine()
session = get_session(engine)
fetcher = NBAStatsFetcher()

# Players to add
new_players = [
    {"name": "DeAnthony Melton", "team": "GSW", "position": "SG"},
    {"name": "Will Richard", "team": "GSW", "position": "SG"},
    {"name": "Cole Anthony", "team": "MIL", "position": "PG"},
    {"name": "Scotty Pippen Jr.", "team": "MEM", "position": "PG"},  # Check if this is who they meant
]

print("=" * 60)
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

# Fix Dylan Harper's team
print("\n" + "=" * 60)
print("FIXING DYLAN HARPER'S TEAM")
print("=" * 60)

dylan = session.query(Player).filter_by(name='Dylan Harper').first()
if dylan:
    print(f"Found Dylan Harper - current team: {dylan.team}")
    dylan.team = 'SAS'
    session.commit()
    print(f"Updated team to: SAS")
else:
    print("Dylan Harper not found in database")

session.close()
print("\nDone!")
