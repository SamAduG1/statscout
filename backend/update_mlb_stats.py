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
        # Re-process last 3 days to catch stat corrections (e.g. extra innings)
        # plus any genuinely new games
        last_date = get_last_game_date(session, player.id)
        if last_date:
            cutoff = last_date - timedelta(days=3)
            splits = [s for s in splits if s.get("date", "") >= str(cutoff)]

        if not splits:
            return 0

        n = insert_games(session, player, splits)
        session.commit()
        return n
    except Exception as e:
        print(f"  [ERROR] {player.name}: {e}")
        session.rollback()
        return 0


def main(days=None):
    """Update MLB player stats.

    Args:
        days: Only update players not updated in last N days.
              Pass None to update all players.
              When called from CLI, parsed from --days argument.
    """
    # Only parse CLI args when run as a script, not when called programmatically
    if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument("--days", type=int, default=None,
                            help="Only update players not updated in last N days")
        args = parser.parse_args()
        days = args.days

    engine = get_engine()
    session = get_session(engine)

    try:
        query = session.query(MLBPlayer)
        if days:
            cutoff = date.today() - timedelta(days=days)
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
        return total_new
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=None,
                        help="Only update players not updated in last N days")
    args = parser.parse_args()
    main(days=args.days)
