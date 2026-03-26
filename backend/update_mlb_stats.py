"""
Incremental update script for MLB player stats.
Run after each game day (or daily) to add new game rows.
Only fetches games newer than each player's last recorded game date.

Usage:
  cd backend
  python update_mlb_stats.py             # all players
  python update_mlb_stats.py --days 3    # players with no update in last 3 days
"""

import time
import argparse
import requests
from datetime import date, timedelta

from dotenv import load_dotenv
load_dotenv()

from models import get_engine, get_session, MLBPlayer, MLBPlayerGame
from populate_mlb_players import get_game_log, insert_games, upsert_player, get_all_teams, get_roster, SEASON, PITCHER_POSITIONS

# Current season for updates (2026 once that season starts)
UPDATE_SEASON = 2026


def get_last_game_date(session, player_id):
    row = (
        session.query(MLBPlayerGame.game_date)
        .filter_by(player_id=player_id)
        .order_by(MLBPlayerGame.game_date.desc())
        .first()
    )
    return row[0] if row else None


def update_player(session, player, season):
    group = "pitching" if player.is_pitcher else "hitting"
    try:
        splits = get_game_log(player.id, group, include_postseason=False)
        # Filter splits to only new games
        last_date = get_last_game_date(session, player.id)
        if last_date:
            splits = [s for s in splits if s.get("date", "") > str(last_date)]

        if not splits:
            return 0

        n = insert_games(session, player, splits)
        session.commit()
        return n
    except Exception as e:
        print(f"  [ERROR] {player.name}: {e}")
        session.rollback()
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=None,
                        help="Only update players not updated in last N days")
    args = parser.parse_args()

    engine = get_engine()
    session = get_session(engine)

    try:
        query = session.query(MLBPlayer)
        if args.days:
            cutoff = date.today() - timedelta(days=args.days)
            query = query.filter(MLBPlayer.last_updated < cutoff)

        players = query.all()
        print(f"Updating {len(players)} players for {UPDATE_SEASON} season...")

        total_new = 0
        for i, player in enumerate(players, 1):
            n = update_player(session, player, UPDATE_SEASON)
            if n > 0:
                player.last_updated = date.today()
                session.commit()
                print(f"  [{i:4d}/{len(players)}] {player.name} ({player.team}) +{n} games")
            else:
                print(f"  [{i:4d}/{len(players)}] {player.name} - no new games")
            total_new += n
            time.sleep(0.2)

        print(f"\nDone. {total_new} new game rows added.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
