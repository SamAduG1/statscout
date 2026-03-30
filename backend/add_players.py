# -*- coding: utf-8 -*-
"""
One-off script: add new/emerging players to the NBA DB.
Run locally: cd backend && python add_players.py
"""
import sys, io, time
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players as nba_players
from models import get_engine, get_session, Player, Game

SEASON = '2025-26'

# (name, team, position)
NEW_PLAYERS = [
    ('Gui Santos',               'GSW', 'F'),
    ("De'Anthony Melton",        'GSW', 'G'),
    ('Jayson Tatum',             'BOS', 'F'),
    ('Baylor Scheierman',        'BOS', 'G'),
    ('Micah Potter',             'IND', 'C'),
    ('Obi Toppin',               'IND', 'F'),
    ('Andre Jackson Jr.',        'MIL', 'G'),
    ('Taurean Prince',           'MIL', 'F'),
    ('Scoot Henderson',          'POR', 'G'),
    ('Ochai Agbaji',             'BKN', 'G'),
    ('Ben Saraf',                'BKN', 'G'),
    ('Devin Carter',             'SAC', 'G'),
    ('Dejounte Murray',          'NOP', 'G'),
    ('Javon Small',              'MEM', 'G'),
    ('Rayan Rupert',             'MEM', 'G'),
    ('Jahmai Mashack',           'MEM', 'G'),
    ('Oliver-Maxence Prosper',   'MEM', 'F'),
    ('Scotty Pippen Jr.',        'MEM', 'G'),
    ('Kasparas Jakucionis',      'MIA', 'G'),
    ('Jericho Sims',             'MIL', 'C'),
    ('Cameron Payne',            'PHI', 'G'),
    ('Jabari Walker',            'PHI', 'F'),
    ('Josh Minott',              'BKN', 'F'),
    ('Ben Sheppard',             'IND', 'G'),
    ('Micah Potter',             'IND', 'C'),
    ('Kobe Brown',               'IND', 'F'),
    ('Leaky Black',              'WAS', 'G'),
    ('Jamir Watkins',            'WAS', 'G'),
    ('Sharife Cooper',           'WAS', 'G'),
]

engine = get_engine()
session = get_session(engine)
added_players = 0
added_games = 0

for name, team, pos in NEW_PLAYERS:
    print(f'\n{name} ({team}, {pos})')

    # Find in NBA API
    matches = nba_players.find_players_by_full_name(name)
    if not matches:
        print(f'  [SKIP] Not found in NBA API')
        continue
    pid = matches[0]['id']

    # Fetch season game log
    try:
        time.sleep(0.8)
        log = playergamelog.PlayerGameLog(player_id=pid, season=SEASON)
        df = log.get_data_frames()[0]
    except Exception as e:
        print(f'  [ERROR] {e}')
        continue

    if df.empty:
        print(f'  [SKIP] No games this season')
        continue

    # Get or create player
    player = session.query(Player).filter_by(name=name).first()
    if not player:
        player = Player(name=name, team=team, position=pos)
        session.add(player)
        session.flush()
        added_players += 1
        print(f'  Created player (id={player.id})')
    else:
        print(f'  Player already exists (id={player.id}), adding missing games')

    # Insert games
    new_games = 0
    for _, row in df.iterrows():
        game_date = datetime.strptime(row['GAME_DATE'], '%b %d, %Y').date()
        existing = session.query(Game).filter_by(player_id=player.id, date=game_date).first()
        if existing:
            continue

        is_home = '@' not in row['MATCHUP']
        opp = row['MATCHUP'].split()[-1]

        game = Game(
            player_id=player.id,
            date=game_date,
            opponent=opp,
            is_home=is_home,
            points=int(row['PTS']),
            rebounds=int(row['REB']),
            assists=int(row['AST']),
            steals=int(row['STL']),
            blocks=int(row['BLK']),
            three_pm=int(row['FG3M']),
        )
        session.add(game)
        new_games += 1

    session.commit()
    added_games += new_games
    print(f'  +{new_games} games ({len(df)} total this season)')

session.close()
print(f'\nDone. Added {added_players} players, {added_games} games.')
