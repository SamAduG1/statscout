"""
Populate team_games table with quarter-by-quarter scores for all 30 NBA teams.
Uses LeagueGameLog to get all 2025-26 games, then BoxScoreSummaryV2 for Q scores.

Run locally:
  cd backend
  python populate_team_quarters.py

Takes ~30-45 min due to NBA API rate limits (one box score call per game).
Already-inserted game_ids are skipped so safe to re-run.
"""

import time
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from nba_api.stats.endpoints import leaguegamelog, boxscoresummaryv2
from models import get_engine, get_session, TeamGame

SEASON = '2025-26'
SLEEP_BETWEEN_CALLS = 0.7  # seconds — stay under NBA API rate limit


def get_all_game_ids(session):
    """Return set of game_ids already in DB."""
    rows = session.query(TeamGame.game_id).all()
    return {r[0] for r in rows}


def fetch_league_games():
    """Fetch all 2025-26 regular season games from NBA API."""
    print("Fetching league game log...")
    log = leaguegamelog.LeagueGameLog(season=SEASON, season_type_all_star='Regular Season')
    df = log.get_data_frames()[0]
    print(f"  {len(df)} team-game rows ({df['GAME_ID'].nunique()} unique games)")
    return df


def fetch_quarter_scores(game_id):
    """
    Return dict keyed by team_id: {q1, q2, q3, q4, ot}
    BoxScoreSummaryV2 line_score gives per-period pts per team.
    """
    summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id)
    line_score = summary.get_data_frames()[5]  # line_score dataframe

    result = {}
    for _, row in line_score.iterrows():
        tid = row['TEAM_ID']
        pts = {}
        for col in line_score.columns:
            if col.startswith('PTS_QTR'):
                q = col.replace('PTS_QTR', '')
                pts[f'q{q}'] = row[col] if row[col] is not None else 0
            elif col == 'PTS_OT1':
                pts['ot'] = row[col] if row[col] is not None else 0
        result[tid] = pts
    return result


def main():
    engine = get_engine()
    session = get_session(engine)

    existing_ids = get_all_game_ids(session)
    print(f"{len(existing_ids)} game rows already in DB, will skip duplicates")

    df = fetch_league_games()

    # Build a map: game_id -> list of team rows
    from collections import defaultdict
    games_map = defaultdict(list)
    for _, row in df.iterrows():
        games_map[row['GAME_ID']].append(row)

    game_ids = sorted(games_map.keys())
    # Only process games where neither team is in DB yet
    new_game_ids = [gid for gid in game_ids if gid not in existing_ids]
    print(f"{len(new_game_ids)} new games to process\n")

    inserted = 0
    errors = 0

    for i, game_id in enumerate(new_game_ids, 1):
        rows = games_map[game_id]
        if len(rows) != 2:
            continue  # skip if not exactly 2 teams (shouldn't happen)

        try:
            time.sleep(SLEEP_BETWEEN_CALLS)
            quarter_scores = fetch_quarter_scores(game_id)
        except Exception as e:
            print(f"  [{i}/{len(new_game_ids)}] {game_id} [ERROR] box score: {e}")
            errors += 1
            time.sleep(2)
            continue

        for row in rows:
            team = row['TEAM_ABBREVIATION']
            opp_row = [r for r in rows if r['TEAM_ABBREVIATION'] != team][0]
            opp = opp_row['TEAM_ABBREVIATION']

            matchup = row['MATCHUP']  # e.g. "BOS vs. MIA" or "BOS @ MIA"
            is_home = 'vs.' in matchup

            game_date = datetime.strptime(row['GAME_DATE'], '%Y-%m-%d').date()
            won = row['WL'] == 'W'
            total_pts = int(row['PTS'])
            opp_pts = int(opp_row['PTS'])

            tid = row['TEAM_ID']
            qs = quarter_scores.get(tid, {})

            tg = TeamGame(
                game_id=game_id,
                team=team,
                opponent=opp,
                date=game_date,
                is_home=is_home,
                season=SEASON,
                q1_points=qs.get('q1'),
                q2_points=qs.get('q2'),
                q3_points=qs.get('q3'),
                q4_points=qs.get('q4'),
                ot_points=qs.get('ot', 0),
                total_points=total_pts,
                opponent_points=opp_pts,
                won=won,
            )
            session.add(tg)
            inserted += 1

        session.commit()

        if i % 20 == 0 or i == len(new_game_ids):
            print(f"  [{i}/{len(new_game_ids)}] {inserted} rows inserted so far...")

    session.close()
    print(f"\nDone. {inserted} rows inserted, {errors} errors.")


if __name__ == '__main__':
    main()
