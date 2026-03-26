"""
One-off script to backfill October 2025 MLB postseason (playoff) game logs.
Only fetches Wild Card / ALDS / NLDS / ALCS / NLCS / World Series game types.
Skips regular season (already in DB). insert_games deduplicates by date.

Run locally:
  cd backend
  python backfill_mlb_postseason.py
"""

import time
from dotenv import load_dotenv
load_dotenv()

from models import get_engine, get_session, MLBPlayer, MLBPlayerGame
from populate_mlb_players import _get, insert_games, SEASON

POSTSEASON_GAME_TYPES = ["F", "D", "L", "W"]  # Wild Card, DS, LCS, World Series


def get_postseason_splits(player_id, group):
    splits = []
    seen_dates = set()
    for game_type in POSTSEASON_GAME_TYPES:
        try:
            data = _get(f"people/{player_id}/stats", {
                "stats": "gameLog",
                "season": SEASON,
                "group": group,
                "gameType": game_type,
            })
            stats_list = data.get("stats", [])
            if not stats_list:
                continue
            for split in stats_list[0].get("splits", []):
                d = split.get("date", "")
                if d and d not in seen_dates:
                    seen_dates.add(d)
                    splits.append(split)
        except Exception as e:
            print(f"    [warn] {game_type}: {e}")
    return sorted(splits, key=lambda s: s.get("date", ""))


def main():
    engine = get_engine()
    session = get_session(engine)

    try:
        players = session.query(MLBPlayer).all()
        print(f"Checking {len(players)} players for 2025 postseason games...")

        total_new = 0
        for i, player in enumerate(players, 1):
            group = "pitching" if player.is_pitcher else "hitting"
            try:
                splits = get_postseason_splits(player.id, group)
                if not splits:
                    print(f"  [{i:4d}/{len(players)}] {player.name} - no postseason")
                    time.sleep(0.05)
                    continue

                n = insert_games(session, player, splits)
                session.commit()
                total_new += n
                print(f"  [{i:4d}/{len(players)}] {player.name} ({player.team}) +{n} postseason games")
            except Exception as e:
                print(f"  [{i:4d}/{len(players)}] [ERROR] {player.name}: {e}")
                session.rollback()
            time.sleep(0.15)

        print(f"\nDone. {total_new} new postseason game rows added.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
