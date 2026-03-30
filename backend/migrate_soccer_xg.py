"""
One-off migration: add xG and xA columns to soccer_player_games table,
then backfill from Understat for all existing players.

Run locally:
  cd backend
  python migrate_soccer_xg.py

Safe to re-run — skips players whose xG is already populated.
Takes ~15-20 min due to Understat rate limits.
"""

import time
import json
import re
import requests
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from models import get_engine, get_session, SoccerPlayer, SoccerPlayerGame

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
UNDERSTAT_BASE = "https://understat.com"


def _make_session(seed_url):
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    s.get(seed_url, timeout=15)
    return s


def _extract_json(html, var_name):
    pattern = rf"var {var_name}\s*=\s*JSON\.parse\('(.+?)'\);"
    m = re.search(pattern, html)
    if not m:
        return None
    raw = m.group(1).encode('utf-8').decode('unicode_escape')
    return json.loads(raw)


def fetch_player_matches(understat_id, session_req):
    url = f"{UNDERSTAT_BASE}/player/{understat_id}"
    try:
        r = session_req.get(url, timeout=15)
        data = _extract_json(r.text, "matchesData")
        return data or []
    except Exception as e:
        print(f"    [warn] fetch failed: {e}")
        return []


def main():
    engine = get_engine()

    # Add columns if they don't exist
    with engine.connect() as conn:
        for col, coltype in [("xG", "FLOAT"), ("xA", "FLOAT")]:
            try:
                conn.execute(text(f"ALTER TABLE soccer_player_games ADD COLUMN IF NOT EXISTS \"{col}\" {coltype}"))
                conn.commit()
                print(f"Added column {col}")
            except Exception as e:
                print(f"Column {col} already exists or error: {e}")

    session = get_session(engine)
    players = session.query(SoccerPlayer).all()
    print(f"\nBackfilling xG/xA for {len(players)} players...")

    req_session = None
    updated = 0

    for i, player in enumerate(players, 1):
        if not player.understat_id:
            continue

        # Check if any games already have xG filled
        sample = (
            session.query(SoccerPlayerGame)
            .filter_by(player_id=player.id)
            .filter(SoccerPlayerGame.xG.isnot(None))
            .first()
        )
        if sample:
            print(f"  [{i:4d}/{len(players)}] {player.name} - already has xG, skipping")
            continue

        games = session.query(SoccerPlayerGame).filter_by(player_id=player.id).all()
        if not games:
            continue

        # Build date->game map
        game_map = {g.match_date.isoformat(): g for g in games}

        if req_session is None:
            req_session = _make_session(f"{UNDERSTAT_BASE}/player/{player.understat_id}")
            time.sleep(1)

        matches = fetch_player_matches(player.understat_id, req_session)
        time.sleep(0.5)

        filled = 0
        for m in matches:
            d = m.get("date", "")[:10]
            if d not in game_map:
                continue
            g = game_map[d]
            try:
                g.xG = float(m.get("xG", 0) or 0)
            except (ValueError, TypeError):
                g.xG = None
            try:
                g.xA = float(m.get("xA", 0) or 0)
            except (ValueError, TypeError):
                g.xA = None
            filled += 1

        session.commit()
        updated += 1
        print(f"  [{i:4d}/{len(players)}] {player.name} - filled {filled} rows")

    session.close()
    print(f"\nDone. {updated} players backfilled.")


if __name__ == "__main__":
    main()
