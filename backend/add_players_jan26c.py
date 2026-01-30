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

# Players to add
new_players = [
    {"name": "Dominick Barlow", "team": "PHI", "position": "PF"},
    {"name": "Jalen Smith", "team": "CHI", "position": "C"},
    {"name": "Steven Adams", "team": "HOU", "position": "C"},
    {"name": "Grant Williams", "team": "CHA", "position": "PF"},
    {"name": "Spencer Jones", "team": "DEN", "position": "SF"},
    {"name": "Zeke Nnaji", "team": "DEN", "position": "PF"},
    {"name": "Jalen Pickett", "team": "DEN", "position": "PG"},
    {"name": "Jonas Valanciunas", "team": "DEN", "position": "C"},
    {"name": "Julian Strawther", "team": "DEN", "position": "SG"},
    {"name": "Nolan Traore", "team": "DEN", "position": "PG"},
    {"name": "Tyrese Martin", "team": "DEN", "position": "SG"},
    {"name": "Jalen Wilson", "team": "DEN", "position": "SF"},
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

session.close()
print("\nDone!")
