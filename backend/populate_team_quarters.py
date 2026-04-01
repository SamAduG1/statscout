"""
Populate team_games table with quarter-by-quarter scores using ESPN's
unofficial scoreboard API (no API key required, complete data for all games).

Iterates each date of the 2025-26 NBA season, fetches linescores from ESPN,
then updates existing TeamGame rows in-place.

Run locally:
  cd backend
  python populate_team_quarters.py

Takes ~3-5 minutes (~170 date calls at 0.3s each).
Rows that already have q1_points are skipped unless --force is passed.
Safe to re-run.
"""

import time
import sys
import io
import argparse
import requests
from datetime import date, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from models import get_engine, get_session, TeamGame

# 2025-26 regular season
SEASON_START = date(2025, 10, 22)
SEASON_END   = date(2026, 4, 14)   # approximate end of regular season

SLEEP_BETWEEN_CALLS = 0.35   # seconds — ESPN has no rate limit but be polite

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

# ESPN team abbreviations that differ from NBA standard
ESPN_TO_NBA = {
    "GS":   "GSW",
    "NY":   "NYK",
    "SA":   "SAS",
    "NO":   "NOP",
    "WSH":  "WAS",
    "UTAH": "UTA",
    "PHO":  "PHX",   # ESPN occasionally uses PHO instead of PHX
}


def norm(abbr: str) -> str:
    """Normalize an ESPN abbreviation to the NBA abbreviation we store."""
    return ESPN_TO_NBA.get(abbr.upper(), abbr.upper())


def fetch_espn_games(game_date: date) -> list:
    """
    Returns a list of completed-game dicts for the given date:
      {home_team, away_team, home_scores, away_scores}
    home_scores / away_scores are per-period integer lists (4 items normally, 5+ with OT).
    Returns [] on error or no games.
    """
    date_str = game_date.strftime("%Y%m%d")
    try:
        r = requests.get(ESPN_URL, params={"dates": date_str, "limit": 20}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  [ESPN ERROR] {game_date}: {e}")
        return []

    results = []
    for event in data.get("events", []):
        competition = event.get("competitions", [{}])[0]

        # Only process completed games (skip live / not started)
        status = competition.get("status", {}).get("type", {})
        if not status.get("completed", False):
            continue

        competitors = competition.get("competitors", [])
        if len(competitors) != 2:
            continue

        game = {}
        for comp in competitors:
            abbr = norm(comp.get("team", {}).get("abbreviation", ""))
            linescores = comp.get("linescores", [])
            scores = []
            for ls in linescores:
                v = ls.get("value")
                if v is not None:
                    scores.append(int(v))

            if comp.get("homeAway") == "home":
                game["home_team"]   = abbr
                game["home_scores"] = scores
            else:
                game["away_team"]   = abbr
                game["away_scores"] = scores

        if "home_team" in game and "away_team" in game:
            results.append(game)

    return results


def main():
    parser = argparse.ArgumentParser(description="Populate quarter scores from ESPN")
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite rows that already have quarter data"
    )
    args = parser.parse_args()

    engine = get_engine()
    session = get_session(engine)

    today    = date.today()
    end_date = min(SEASON_END, today)

    total_rows    = session.query(TeamGame).count()
    already_done  = session.query(TeamGame).filter(TeamGame.q1_points != None).count()
    print(f"TeamGame rows in DB: {total_rows} total, {already_done} already have quarter data")
    print(f"Scanning {SEASON_START} to {end_date}...\n")

    updated         = 0
    skipped_done    = 0
    skipped_missing = 0
    dates_with_games = 0
    current_date    = SEASON_START

    while current_date <= end_date:
        games = fetch_espn_games(current_date)

        if games:
            dates_with_games += 1
            for game in games:
                h_scores = game["home_scores"]
                a_scores = game["away_scores"]

                # Need at least 4 quarters of data
                if len(h_scores) < 4 or len(a_scores) < 4:
                    continue

                h_ot = sum(h_scores[4:]) if len(h_scores) > 4 else 0
                a_ot = sum(a_scores[4:]) if len(a_scores) > 4 else 0

                for team, scores, ot in [
                    (game["home_team"], h_scores, h_ot),
                    (game["away_team"], a_scores, a_ot),
                ]:
                    row = session.query(TeamGame).filter_by(
                        team=team, date=current_date
                    ).first()

                    if row is None:
                        skipped_missing += 1
                        continue

                    if row.q1_points is not None and not args.force:
                        skipped_done += 1
                        continue

                    row.q1_points = scores[0]
                    row.q2_points = scores[1]
                    row.q3_points = scores[2]
                    row.q4_points = scores[3]
                    row.ot_points = ot
                    updated += 1

            session.commit()

        time.sleep(SLEEP_BETWEEN_CALLS)
        current_date += timedelta(days=1)

    session.close()

    print(f"\nDone.")
    print(f"  Dates with completed NBA games : {dates_with_games}")
    print(f"  TeamGame rows updated          : {updated}")
    print(f"  Skipped (already had data)     : {skipped_done}")
    print(f"  Skipped (no matching DB row)   : {skipped_missing}")
    print()
    if skipped_missing > 0:
        print("NOTE: 'No matching DB row' means those games aren't in the team_games table yet.")
        print("  Run populate_team_quarters.py --nba-seed first if this is a fresh DB.")


if __name__ == '__main__':
    main()
