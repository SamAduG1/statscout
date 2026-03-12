# -*- coding: utf-8 -*-
"""
One-off script: re-fetches last 14 days of NBA games from the official API
and corrects any rows that were inserted with mid-game (stale) stats.

Run locally:
  cd backend
  python fix_recent_stats.py
"""
import sys, io, time
from datetime import datetime, timedelta, date

from dotenv import load_dotenv
load_dotenv()

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players as nba_players
from models import get_engine, get_session, Player, Game

CUTOFF_DAYS = 14
SEASON = '2025-26'

engine = get_engine()
session = get_session(engine)

cutoff = date.today() - timedelta(days=CUTOFF_DAYS)
print(f'Checking games on or after {cutoff} for correctness...')

db_players = session.query(Player).all()
updated = 0
checked = 0
errors = 0

for player in db_players:
    recent = session.query(Game).filter(
        Game.player_id == player.id,
        Game.date >= cutoff
    ).all()
    if not recent:
        continue

    try:
        matches = nba_players.find_players_by_full_name(player.name)
        if not matches:
            continue
        pid = matches[0]['id']
        time.sleep(0.6)
        log = playergamelog.PlayerGameLog(player_id=pid, season=SEASON)
        df = log.get_data_frames()[0]
    except Exception as e:
        print(f'  [SKIP] {player.name}: {e}')
        errors += 1
        continue

    for game in recent:
        row = df[df['GAME_DATE'].apply(
            lambda d: datetime.strptime(d, '%b %d, %Y').date()
        ) == game.date]
        if row.empty:
            continue
        checked += 1
        r = row.iloc[0]
        api_pts = int(r['PTS'])
        api_reb = int(r['REB'])
        api_ast = int(r['AST'])
        api_stl = int(r['STL'])
        api_blk = int(r['BLK'])
        api_3pm = int(r['FG3M'])

        if (game.points != api_pts or game.rebounds != api_reb or
                game.assists != api_ast or game.steals != api_stl or
                game.blocks != api_blk or game.three_pm != api_3pm):
            print(f'  FIXING {player.name} {game.date}: '
                  f'DB {game.points}/{game.rebounds}/{game.assists} -> '
                  f'API {api_pts}/{api_reb}/{api_ast}')
            game.points   = api_pts
            game.rebounds = api_reb
            game.assists  = api_ast
            game.steals   = api_stl
            game.blocks   = api_blk
            game.three_pm = api_3pm
            updated += 1

session.commit()
session.close()
print(f'\nDone. Checked {checked} recent games, fixed {updated}, errors {errors}.')
