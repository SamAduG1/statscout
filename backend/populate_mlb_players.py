"""
One-off bulk population script for MLB player stats from MLB Stats API (free, official).
No API key needed. Fetches 2025 regular season game logs for all players on current 40-man rosters.

Run locally ONLY - never deployed to Render.
DATABASE_URL must be set in backend/.env

Usage:
  cd backend
  python populate_mlb_players.py           # all 30 teams
  python populate_mlb_players.py --team 147  # single team by MLB team ID (e.g. 147 = Yankees)

Runtime: ~10-15 min for all 30 teams (~900 players, 1 API call per player).
"""

import sys
import time
import argparse
import requests
from datetime import date, datetime

from dotenv import load_dotenv
load_dotenv()

from models import get_engine, get_session, init_db, MLBPlayer, MLBPlayerGame

MLB_BASE = "https://statsapi.mlb.com/api/v1"
SEASON = 2026
PITCHER_POSITIONS = {"P", "SP", "RP", "TWP"}


def _get(endpoint, params=None, retries=3):
    url = f"{MLB_BASE}/{endpoint}"
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == retries:
                raise
            print(f"    [retry {attempt}] {e}")
            time.sleep(3)


def get_all_teams():
    data = _get("teams", {"sportId": 1, "season": SEASON})
    return [
        {"id": t["id"], "name": t["name"]}
        for t in data.get("teams", [])
        if t.get("sport", {}).get("id") == 1  # MLB only (not minor leagues)
    ]


def get_roster(team_id):
    data = _get(f"teams/{team_id}/roster", {"rosterType": "40Man", "season": SEASON})
    return data.get("roster", [])


def get_game_log(player_id, group, include_postseason=True):
    """Fetch per-game stats. group = 'hitting' or 'pitching'.
    Fetches regular season + postseason (Wild Card, ALDS/NLDS, ALCS/NLCS, World Series).
    """
    splits = []
    seen_dates = set()

    for game_type in (["R", "F", "D", "L", "W"] if include_postseason else ["R"]):
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
            print(f"    [warn] game log ({game_type}) failed: {e}")

    splits.sort(key=lambda s: s.get("date", ""))
    return splits


def upsert_player(session, player_id, name, team, position, is_pitcher, bats=None):
    existing = session.query(MLBPlayer).filter_by(id=player_id).first()
    if existing:
        existing.name = name
        existing.team = team
        existing.position = position
        existing.is_pitcher = is_pitcher
        if bats is not None:
            existing.bats = bats
        existing.last_updated = date.today()
        return existing, False
    player = MLBPlayer(
        id=player_id,
        name=name,
        team=team,
        position=position,
        is_pitcher=is_pitcher,
        bats=bats,
        last_updated=date.today(),
    )
    session.add(player)
    session.flush()
    return player, True


def insert_games(session, player, splits):
    new_count = 0
    for split in splits:
        raw_date = split.get("date", "")
        if not raw_date:
            continue
        try:
            game_date = date.fromisoformat(raw_date)
        except ValueError:
            continue

        is_home = split.get("isHome", True)
        opponent_data = split.get("opponent", {})
        opponent = opponent_data.get("name", "Unknown")
        stat = split.get("stat", {})

        existing = session.query(MLBPlayerGame).filter_by(
            player_id=player.id,
            game_date=game_date,
        ).first()

        if player.is_pitcher:
            ip_str = stat.get("inningsPitched", "0")
            try:
                ip = float(ip_str)
            except (ValueError, TypeError):
                ip = 0.0
            full_innings = int(ip)
            partial = round((ip - full_innings) * 10)
            outs = full_innings * 3 + partial

            if existing:
                existing.strikeouts = stat.get("strikeOuts")
                existing.innings_pitched = ip
                existing.hits_allowed = stat.get("hits")
                existing.earned_runs = stat.get("earnedRuns")
                existing.outs_recorded = outs
            else:
                session.add(MLBPlayerGame(
                    player_id=player.id, game_date=game_date,
                    opponent=opponent, is_home=is_home, season=str(SEASON),
                    strikeouts=stat.get("strikeOuts"), innings_pitched=ip,
                    hits_allowed=stat.get("hits"), earned_runs=stat.get("earnedRuns"),
                    outs_recorded=outs,
                ))
                new_count += 1

        else:
            at_bats = stat.get("atBats")
            plate_apps = stat.get("plateAppearances", 0)
            if not plate_apps:
                continue

            if existing:
                existing.hits = stat.get("hits")
                existing.home_runs = stat.get("homeRuns")
                existing.rbi = stat.get("rbi")
                existing.runs = stat.get("runs")
                existing.total_bases = stat.get("totalBases")
                existing.at_bats = at_bats
                existing.walks = stat.get("baseOnBalls")
            else:
                session.add(MLBPlayerGame(
                    player_id=player.id, game_date=game_date,
                    opponent=opponent, is_home=is_home, season=str(SEASON),
                    hits=stat.get("hits"), home_runs=stat.get("homeRuns"),
                    rbi=stat.get("rbi"), runs=stat.get("runs"),
                    total_bases=stat.get("totalBases"), at_bats=at_bats,
                    walks=stat.get("baseOnBalls"),
                ))
                new_count += 1

    return new_count


def refresh_all_rosters(session):
    """
    Lightweight weekly roster refresh: updates team assignments for traded players.
    Does NOT re-fetch game logs - only updates name/team/position/bats on existing players.
    New players found on a roster are added but without game history (update_mlb_stats fills that).
    """
    teams = get_all_teams()
    updated = added = 0
    for team in teams:
        try:
            roster = get_roster(team["id"])
            for entry in roster:
                person    = entry.get("person", {})
                player_id = person.get("id")
                name      = person.get("fullName", "")
                pos_abbr  = entry.get("position", {}).get("abbreviation", "")
                bats      = person.get("batSide", {}).get("code")
                if not player_id or not name:
                    continue
                is_pitcher = pos_abbr in PITCHER_POSITIONS
                _, is_new = upsert_player(session, player_id, name, team["name"], pos_abbr, is_pitcher, bats=bats)
                if is_new:
                    added += 1
                else:
                    updated += 1
            session.commit()
            time.sleep(0.2)
        except Exception as e:
            session.rollback()
            print(f"  [Roster refresh] {team['name']}: {e}")
    print(f"[Roster refresh] Done - {updated} updated, {added} new players added")
    return updated, added


def process_team(session, team_id, team_name):
    print(f"\n  [{team_name}] fetching 40-man roster...")
    roster = get_roster(team_id)
    print(f"  [{team_name}] {len(roster)} players on roster")

    players_added = players_updated = total_games = errors = 0

    for i, entry in enumerate(roster, 1):
        person = entry.get("person", {})
        player_id = person.get("id")
        name = person.get("fullName", "")
        pos_abbr = entry.get("position", {}).get("abbreviation", "")

        if not player_id or not name:
            continue

        is_pitcher = pos_abbr in PITCHER_POSITIONS
        group = "pitching" if is_pitcher else "hitting"
        bats = person.get("batSide", {}).get("code")  # 'L', 'R', or 'S'

        try:
            player, is_new = upsert_player(session, player_id, name, team_name, pos_abbr, is_pitcher, bats=bats)
            splits = get_game_log(player_id, group)
            n = insert_games(session, player, splits)
            total_games += n

            if is_new:
                players_added += 1
            else:
                players_updated += 1

            status = "NEW" if is_new else "UPD"
            kind = "P" if is_pitcher else "B"
            print(f"    [{i:3d}/{len(roster)}] [{status}][{kind}] {name} ({pos_abbr}) - {n} games")

            session.commit()
            time.sleep(0.25)

        except Exception as e:
            print(f"    [ERROR] {name}: {e}")
            session.rollback()
            errors += 1
            time.sleep(2)

    print(f"  [{team_name}] done: {players_added} added, {players_updated} updated, "
          f"{total_games} game rows, {errors} errors")
    return total_games


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", type=int, default=None,
                        help="MLB team ID to process (omit for all 30 teams)")
    args = parser.parse_args()

    engine = get_engine()
    init_db(engine)
    session = get_session(engine)

    try:
        if args.team:
            teams = [t for t in get_all_teams() if t["id"] == args.team]
            if not teams:
                print(f"Team ID {args.team} not found.")
                sys.exit(1)
        else:
            teams = get_all_teams()

        print(f"Processing {len(teams)} team(s) for {SEASON} season...")
        total = 0
        for team in teams:
            total += process_team(session, team["id"], team["name"])

        print(f"\nDone. {total} total game rows inserted.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
