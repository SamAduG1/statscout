"""
Weekly incremental update script for soccer player stats.
Only fetches new game rows since the last known date per player.
No external dependencies beyond requests (already in requirements.txt).

Run locally after each gameweek (typically Monday).
DATABASE_URL must be set in backend/.env

Usage:
  cd backend
  python update_soccer_stats.py                       # all 5 leagues
  python update_soccer_stats.py --league pl
  python update_soccer_stats.py --league laliga
  python update_soccer_stats.py --league bundesliga
  python update_soccer_stats.py --league seriea
  python update_soccer_stats.py --league ligue1
  python update_soccer_stats.py --player 8260          # single player by understat_id
"""

import time
import argparse
import requests
from datetime import date

from dotenv import load_dotenv
load_dotenv()

from models import get_engine, get_session, SoccerPlayer, SoccerPlayerGame
from populate_soccer_players import (
    UA, SEASON, LEAGUES,
    _norm_position, _current_team, _all_teams,
    upsert_player, insert_matches,
)

UNDERSTAT_BASE = "https://understat.com"


def _make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "X-Requested-With": "XMLHttpRequest",
    })
    return s


def get_last_game_date(session, player_id):
    last = (
        session.query(SoccerPlayerGame)
        .filter_by(player_id=player_id)
        .order_by(SoccerPlayerGame.match_date.desc())
        .first()
    )
    return last.match_date if last else None


def fetch_player_matches_since(s, understat_id, since_date=None):
    """Fetch matches for a player, optionally filtered to after since_date."""
    player_url = f"{UNDERSTAT_BASE}/player/{understat_id}"
    s.headers["Referer"] = player_url
    s.get(player_url, timeout=20)
    time.sleep(0.3)
    r = s.get(f"{UNDERSTAT_BASE}/getPlayerData/{understat_id}", timeout=20)
    r.raise_for_status()
    matches = r.json().get("matches", [])
    # Filter to current season
    matches = [m for m in matches if str(m.get("season", "")) == str(SEASON)]
    if since_date:
        matches = [m for m in matches
                   if (m.get("date") or "")[:10] > since_date.isoformat()]
    return matches


def refresh_league_teams(session, s, league_key):
    """
    Sync current team assignments from Understat league page.
    Players transferred since last run will have their team_name updated.
    """
    league_code = LEAGUES[league_key]
    league_url = f"{UNDERSTAT_BASE}/league/{league_code}/{SEASON}"
    s.headers["Referer"] = league_url
    s.get(league_url, timeout=30)
    r = s.get(f"{UNDERSTAT_BASE}/getLeagueData/{league_code}/{SEASON}", timeout=30)
    r.raise_for_status()
    players_raw = r.json().get("players", [])
    print(f"  League page: {len(players_raw)} players")
    for p in players_raw:
        uid = int(p.get("id", 0))
        if not uid:
            continue
        existing = session.query(SoccerPlayer).filter_by(understat_id=uid).first()
        if existing:
            new_team = _current_team(p.get("team_title", existing.team_name))
            if existing.team_name != new_team:
                print(f"  Transfer: {existing.name} {existing.team_name} -> {new_team}")
                existing.team_name = new_team
    session.commit()


def update_player(session, s, player, verbose=True):
    last_date = get_last_game_date(session, player.id)
    all_teams = _all_teams(player.team_name)  # best effort with current team only
    try:
        matches = fetch_player_matches_since(s, player.understat_id, last_date)
        n = insert_matches(session, player, matches, all_teams)
        if n > 0:
            player.last_updated = date.today()
            session.commit()
            if verbose:
                print(f"  {player.name} ({player.team_name}): +{n} games")
        return n
    except Exception as e:
        session.rollback()
        print(f"  [ERROR] {player.name}: {e}")
        return 0


def update_all(session, s, league_key=None):
    query = session.query(SoccerPlayer)
    if league_key:
        query = query.filter_by(league=league_key)
    players = query.all()
    league_label = league_key or "all leagues"
    print(f"Updating {len(players)} players ({league_label})...")

    total_new = 0
    for i, player in enumerate(players, 1):
        n = update_player(session, s, player)
        total_new += n
        time.sleep(1.2)
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(players)}")

    print(f"Done. {total_new} new game rows added.")


def main(league=None, player_id=None, no_team_refresh=False):
    """Update soccer player stats for one or all leagues.

    Args:
        league: League key (pl/laliga/bundesliga/seriea/ligue1), or None for all.
        player_id: Single player understat_id to update, or None for all.
        no_team_refresh: Skip team assignment refresh (faster).
        When called from CLI, these are parsed from command-line arguments.
    """
    engine = get_engine()
    session = get_session(engine)
    s = _make_session()

    try:
        leagues = [league] if league else list(LEAGUES.keys())

        if player_id:
            player = session.query(SoccerPlayer).filter_by(understat_id=player_id).first()
            if not player:
                print(f"Player {player_id} not found in DB")
                return
            update_player(session, s, player, verbose=True)
            return

        for league_key in leagues:
            print(f"\n=== {LEAGUES[league_key]} ===")
            if not no_team_refresh:
                print("Refreshing team assignments...")
                refresh_league_teams(session, s, league_key)
            update_all(session, s, league_key)
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--league", choices=list(LEAGUES.keys()), default=None)
    parser.add_argument("--player", type=int, default=None,
                        help="Single player understat_id to update")
    parser.add_argument("--no-team-refresh", action="store_true",
                        help="Skip team assignment refresh (faster)")
    args = parser.parse_args()
    main(league=args.league, player_id=args.player, no_team_refresh=args.no_team_refresh)


if __name__ == "__main__":
    main()
