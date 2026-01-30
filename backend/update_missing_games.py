"""
Update Missing Games - Quick fix for games after Jan 11, 2026
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres.tqyzxwogjhehjcwhxnre:Softwareidk5852!@aws-1-us-east-2.pooler.supabase.com:6543/postgres'

import sys
import io
from datetime import datetime
from nba_stats_fetcher import NBAStatsFetcher
from models import get_engine, get_session, Player, Game
import time

# Force UTF-8 output
if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

def update_all_players():
    """Update stats for all players - adds missing recent games"""

    print("=" * 60)
    print(f"UPDATING ALL PLAYERS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    engine = get_engine()
    session = get_session(engine)
    fetcher = NBAStatsFetcher()

    try:
        players = session.query(Player).all()
        print(f"\nTotal players: {len(players)}")

        total_added = 0

        for idx, player in enumerate(players, 1):
            print(f"\n[{idx}/{len(players)}] {player.name} ({player.team})...")

            try:
                # Get last game date
                last_game = session.query(Game).filter_by(player_id=player.id).order_by(Game.date.desc()).first()
                last_date = last_game.date if last_game else None

                # Fetch from API
                games = fetcher.fetch_player_season(player.name, player.team, player.position, '2025-26')

                if not games:
                    print(f"  No games from API")
                    continue

                # Add only new games
                added = 0
                for g in games:
                    game_date = datetime.strptime(g['date'], '%Y-%m-%d').date()

                    # Skip if we have this game
                    if last_date and game_date <= last_date:
                        continue

                    # Check if exists
                    existing = session.query(Game).filter_by(
                        player_id=player.id,
                        date=game_date
                    ).first()

                    if existing:
                        continue

                    # Add new game
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
                    added += 1

                if added > 0:
                    session.commit()
                    print(f"  Added {added} new games")
                    total_added += added
                else:
                    print(f"  Up to date")

            except Exception as e:
                print(f"  ERROR: {e}")
                session.rollback()
                continue

            # Rate limiting
            time.sleep(0.6)

        print("\n" + "=" * 60)
        print(f"COMPLETE! Added {total_added} new games")
        print("=" * 60)

    finally:
        session.close()


if __name__ == "__main__":
    update_all_players()
