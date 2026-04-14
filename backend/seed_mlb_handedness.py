"""
One-time script: adds the `bats` column to mlb_players and backfills
batter/pitcher handedness from the MLB Stats API.

Run once from the backend directory:
  cd backend
  python seed_mlb_handedness.py

Safe to re-run - skips players that already have a bats value set.
"""

import time
import requests
from sqlalchemy import text

from dotenv import load_dotenv
load_dotenv()

from models import get_engine, get_session, MLBPlayer

MLB_STATS_BASE = "https://statsapi.mlb.com/api"


def ensure_column(engine):
    with engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE mlb_players ADD COLUMN IF NOT EXISTS bats VARCHAR"
        ))
        conn.commit()
    print("Column `bats` ensured on mlb_players.")


def fetch_bats(player_id):
    """Fetch a player's bat side (L/R/S) from the MLB Stats API people endpoint."""
    try:
        r = requests.get(
            f"{MLB_STATS_BASE}/v1/people/{player_id}",
            params={"fields": "people,batSide,code"},
            timeout=10,
        )
        r.raise_for_status()
        people = r.json().get("people", [{}])
        return people[0].get("batSide", {}).get("code") if people else None
    except Exception as e:
        print(f"  [warn] player {player_id}: {e}")
        return None


def main():
    engine = get_engine()
    ensure_column(engine)
    session = get_session(engine)

    try:
        players = session.query(MLBPlayer).filter(MLBPlayer.bats.is_(None)).all()
        print(f"Backfilling handedness for {len(players)} players...")

        updated = 0
        for i, p in enumerate(players, 1):
            bats = fetch_bats(p.id)
            if bats:
                p.bats = bats
                updated += 1
            if i % 20 == 0:
                session.commit()
                print(f"  {i}/{len(players)} processed ({updated} updated)")
            time.sleep(0.15)

        session.commit()
        print(f"\nDone. {updated}/{len(players)} players updated with handedness.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
