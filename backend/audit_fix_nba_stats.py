"""
Full-season audit and correction of NBA player stats that were captured mid-game.

Fetches final box scores from ESPN for every game date in the DB and corrects
any player-game rows where stats differ from ESPN's final numbers.

Run locally whenever you suspect mid-game captures, or after any manual update run:
  cd backend
  python audit_fix_nba_stats.py

  # Only check the last N days (faster):
  python audit_fix_nba_stats.py --days 7

  # Dry run - show what would be fixed without writing:
  python audit_fix_nba_stats.py --dry-run
"""

import sys
import io
import time
import argparse
import unicodedata
from datetime import date, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import func
from models import get_engine, get_session, Player, Game
from espn_recent_games_scraper import ESPNAPIClient


def ascii_name(name):
    nfkd = unicodedata.normalize('NFKD', name)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).replace('.', '').strip().lower()


def build_name_map(session):
    players = session.query(Player).all()
    name_map = {}
    for p in players:
        name_map[p.name.lower()] = p
        name_map[ascii_name(p.name)] = p
        for suffix in [' Jr.', ' Sr.', ' II', ' III', ' IV']:
            if p.name.endswith(suffix):
                base = p.name[:-len(suffix)].strip()
                name_map[base.lower()] = p
                name_map[ascii_name(base)] = p
    return name_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=None,
                        help='Only audit the last N days (default: full season)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show corrections without writing to DB')
    args = parser.parse_args()

    engine = get_engine()
    session = get_session(engine)
    api = ESPNAPIClient()
    name_map = build_name_map(session)

    # Get all unique game dates in the DB
    cutoff = date(2025, 10, 1)
    if args.days:
        cutoff = date.today() - timedelta(days=args.days)

    dates_in_db = [
        r[0] for r in
        session.query(func.distinct(Game.date))
        .filter(Game.date >= cutoff)
        .order_by(Game.date)
        .all()
    ]

    print(f'Auditing {len(dates_in_db)} game dates from {cutoff} to today'
          f'{" (DRY RUN)" if args.dry_run else ""}...\n')

    total_fixed = 0
    dates_with_fixes = []

    for i, game_date in enumerate(dates_in_db, 1):
        date_str = game_date.strftime('%Y%m%d')
        espn_stats = api.get_player_stats_from_date(date_str)

        if not espn_stats:
            print(f'  [{i:3d}/{len(dates_in_db)}] {game_date} — no ESPN data')
            time.sleep(0.5)
            continue

        fixed_this_date = 0
        for s in espn_stats:
            player = name_map.get(s['player_name'].lower()) or name_map.get(ascii_name(s['player_name']))
            if not player:
                continue
            g = session.query(Game).filter_by(player_id=player.id, date=game_date).first()
            if not g:
                continue
            if (g.points == s['points'] and g.rebounds == s['rebounds']
                    and g.assists == s['assists']):
                continue

            print(f'    FIX {player.name}: '
                  f'{g.points}p/{g.rebounds}r/{g.assists}a -> '
                  f'{s["points"]}p/{s["rebounds"]}r/{s["assists"]}a')

            if not args.dry_run:
                g.points   = s['points']
                g.rebounds = s['rebounds']
                g.assists  = s['assists']
                g.steals   = s['steals']
                g.blocks   = s['blocks']
                g.three_pm = s['three_pm']
            fixed_this_date += 1

        if fixed_this_date > 0 and not args.dry_run:
            session.commit()

        if fixed_this_date > 0:
            dates_with_fixes.append((game_date, fixed_this_date))
            total_fixed += fixed_this_date
            print(f'  [{i:3d}/{len(dates_in_db)}] {game_date} — fixed {fixed_this_date} players')
        else:
            print(f'  [{i:3d}/{len(dates_in_db)}] {game_date} — all correct ({len(espn_stats)} players checked)')

        time.sleep(0.5)

    session.close()

    print(f'\n{"=" * 50}')
    print(f'{"DRY RUN - " if args.dry_run else ""}Audit complete')
    print(f'  Dates checked : {len(dates_in_db)}')
    print(f'  Dates with fixes : {len(dates_with_fixes)}')
    print(f'  Player-games corrected : {total_fixed}')
    if dates_with_fixes:
        print(f'\nAffected dates:')
        for d, n in dates_with_fixes:
            print(f'  {d}: {n} players')


if __name__ == '__main__':
    main()
