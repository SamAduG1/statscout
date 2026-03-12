"""
One-off bulk population script for soccer player stats from Understat.
No external dependencies beyond requests (already in requirements.txt).

Run locally ONLY - never deployed to Render.
DATABASE_URL must be set in backend/.env

Usage:
  cd backend
  python populate_soccer_players.py             # both leagues
  python populate_soccer_players.py --league pl
  python populate_soccer_players.py --league laliga

Understat API (discovered from their JS):
  getLeagueData/{league}/{season}  -> players list + team + position + season totals
  getPlayerData/{player_id}        -> per-match stats (goals, shots, SOT, assists, etc.)
"""

import sys
import time
import argparse
import requests
from datetime import date

from dotenv import load_dotenv
load_dotenv()

from models import get_engine, get_session, SoccerPlayer, SoccerPlayerGame

SEASON = 2025
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

LEAGUES = {
    "pl":     "EPL",
    "laliga": "La_liga",
}

# First char of Understat position string -> our normalized code
POS_MAP = {"G": "GK", "D": "DF", "M": "MF", "F": "FW", "A": "MF", "S": "FW"}


def _norm_position(raw):
    first = (raw or "M").strip()[:1].upper()
    return POS_MAP.get(first, "MF")


def _current_team(team_title):
    """Return most recent team (last in comma-separated list)."""
    parts = [t.strip() for t in team_title.split(",") if t.strip()]
    return parts[-1] if parts else team_title


def _all_teams(team_title):
    """Return set of all teams a player played for (normalized lowercase)."""
    return {t.strip().lower() for t in team_title.split(",") if t.strip()}


def _make_session(referer_url):
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "X-Requested-With": "XMLHttpRequest",
        "Referer": referer_url,
    })
    s.get(referer_url, timeout=30)  # load page to get cookies
    return s


def fetch_league_players(s, league_code):
    url = f"https://understat.com/getLeagueData/{league_code}/{SEASON}"
    r = s.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("players", [])


def fetch_player_matches(s, understat_id, player_page_url):
    """Fetch per-match stats. Requires visiting player page first for cookies."""
    s.get(player_page_url, timeout=20)
    time.sleep(0.3)
    r = s.get(f"https://understat.com/getPlayerData/{understat_id}", timeout=20)
    r.raise_for_status()
    data = r.json()
    matches = data.get("matches", [])
    # Filter to current season only
    return [m for m in matches if str(m.get("season", "")) == str(SEASON)]


def upsert_player(session, understat_id, name, team_name, league, position):
    existing = session.query(SoccerPlayer).filter_by(understat_id=understat_id).first()
    if existing:
        existing.name = name
        existing.team_name = team_name
        existing.league = league
        existing.position = position
        existing.last_updated = date.today()
        return existing, False
    player = SoccerPlayer(
        understat_id=understat_id,
        name=name,
        team_name=team_name,
        league=league,
        position=position,
        last_updated=date.today(),
    )
    session.add(player)
    session.flush()
    return player, True


def insert_matches(session, player, matches, all_teams=None):
    if all_teams is None:
        all_teams = {player.team_name.lower()}
    new_count = 0
    for m in matches:
        raw_date = (m.get("date") or "")[:10]
        if not raw_date:
            continue
        try:
            match_date = date.fromisoformat(raw_date)
        except ValueError:
            continue

        mins = int(m.get("time", 0) or 0)
        if mins == 0:
            continue  # player didn't play

        existing = session.query(SoccerPlayerGame).filter_by(
            player_id=player.id,
            match_date=match_date,
        ).first()
        if existing:
            continue

        # Determine venue: check h_team against all teams the player has played for
        h_team = m.get("h_team", "")
        is_home = h_team.strip().lower() in all_teams
        venue = "home" if is_home else "away"
        opponent = m.get("a_team", "") if is_home else h_team

        # GK clean sheet: goals conceded = opponent goals
        goals_conceded = None
        if player.position == "GK":
            try:
                if is_home:
                    goals_conceded = int(m.get("a_goals", 0) or 0)
                else:
                    goals_conceded = int(m.get("h_goals", 0) or 0)
            except (ValueError, TypeError):
                goals_conceded = None

        game = SoccerPlayerGame(
            player_id=player.id,
            match_date=match_date,
            opponent=opponent,
            venue=venue,
            goals=int(m.get("goals", 0) or 0),
            shots=int(m.get("shots", 0) or 0),
            shots_on_target=0,  # not in match data; update via separate source if needed
            assists=int(m.get("assists", 0) or 0),
            key_passes=int(m.get("key_passes", 0) or 0),
            minutes_played=mins,
            goals_conceded=goals_conceded,
            season=str(SEASON),
        )
        session.add(game)
        new_count += 1
    return new_count


def populate_league(session, league_key):
    league_code = LEAGUES[league_key]
    league_url = f"https://understat.com/league/{league_code}/{SEASON}"
    print(f"\n=== {league_code} season {SEASON} ===")

    s = _make_session(league_url)
    players_raw = fetch_league_players(s, league_code)
    print(f"Found {len(players_raw)} players")

    players_added = 0
    players_updated = 0
    total_games = 0
    errors = 0

    for i, p in enumerate(players_raw, 1):
        understat_id = int(p.get("id", 0))
        name = p.get("player_name", "")
        team_name = _current_team(p.get("team_title", ""))
        all_teams = _all_teams(p.get("team_title", ""))
        position = _norm_position(p.get("position", "M"))

        if not understat_id or not name:
            continue

        try:
            player, is_new = upsert_player(session, understat_id, name, team_name, league_key, position)

            player_page = f"https://understat.com/player/{understat_id}"
            matches = fetch_player_matches(s, understat_id, player_page)
            n = insert_matches(session, player, matches, all_teams)
            total_games += n

            if is_new:
                players_added += 1
            else:
                players_updated += 1

            status = "NEW" if is_new else "UPD"
            print(f"  [{i:3d}/{len(players_raw)}] [{status}] {name} ({team_name}, {position}) - {n} games")

            session.commit()
            time.sleep(1.2)

        except Exception as e:
            print(f"  [ERROR] {name}: {e}")
            session.rollback()
            errors += 1
            time.sleep(3)

    print(f"\n{league_code}: {players_added} added, {players_updated} updated, "
          f"{total_games} game rows, {errors} errors")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--league", choices=["pl", "laliga"], default=None)
    args = parser.parse_args()

    engine = get_engine()
    session = get_session(engine)
    leagues = [args.league] if args.league else ["pl", "laliga"]

    try:
        for league in leagues:
            populate_league(session, league)
    finally:
        session.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
