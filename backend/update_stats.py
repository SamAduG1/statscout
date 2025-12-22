"""
Automated Stats Update Script
Fetches new games for existing players and updates the database
"""
import sys
import io
from datetime import datetime, date
from nba_stats_fetcher import NBAStatsFetcher
from models import get_engine, get_session, Player, Game
import time

# Force UTF-8 output only if not already wrapped
if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass  # Already wrapped or can't wrap


def get_last_game_date(session, player_name):
    """Get the date of the most recent game for a player"""
    player = session.query(Player).filter_by(name=player_name).first()
    if not player:
        return None

    last_game = session.query(Game).filter_by(player_id=player.id).order_by(Game.date.desc()).first()
    return last_game.date if last_game else None


def update_player_stats(session, fetcher, player_name, team, position, season="2025-26"):
    """Fetch and update stats for a single player"""

    # Get last game date from database
    last_date = get_last_game_date(session, player_name)

    print(f"\n[INFO] Updating {player_name}...")
    if last_date:
        print(f"  Last game in DB: {last_date}")
    else:
        print(f"  No games in DB yet")

    # Fetch all games for the season
    games = fetcher.fetch_player_season(player_name, team, position, season)

    if not games:
        print(f"  [WARNING] No games found")
        return 0

    # Get player from database
    player = session.query(Player).filter_by(name=player_name).first()

    if not player:
        # Create new player if doesn't exist
        player = Player(name=player_name, team=team, position=position)
        session.add(player)
        session.flush()
        print(f"  [INFO] Created new player: {player_name}")
    else:
        # Update team in case of trades
        if player.team != team:
            print(f"  [INFO] Team change detected: {player.team} -> {team}")
            player.team = team

    # Filter to only NEW games (after last_date)
    new_games = []
    for game in games:
        game_date = datetime.strptime(game['date'], '%Y-%m-%d').date()

        # Skip if we already have this game
        if last_date and game_date <= last_date:
            continue

        # Check if game already exists (by date and opponent)
        existing = session.query(Game).filter_by(
            player_id=player.id,
            date=game_date,
            opponent=game['opponent']
        ).first()

        if existing:
            continue

        new_games.append(game)

    # Add new games to database
    games_added = 0
    for game in new_games:
        game_date = datetime.strptime(game['date'], '%Y-%m-%d').date()

        new_game = Game(
            player_id=player.id,
            date=game_date,
            opponent=game['opponent'],
            is_home=bool(game['is_home']),
            points=int(game['points']),
            rebounds=int(game['rebounds']),
            assists=int(game['assists']),
            steals=int(game['steals']),
            blocks=int(game['blocks']),
            three_pm=int(game['three_pm'])
        )
        session.add(new_game)
        games_added += 1

    if games_added > 0:
        session.commit()
        print(f"  [SUCCESS] Added {games_added} new games")
    else:
        print(f"  [INFO] No new games to add")

    return games_added


def update_all_players(season="2025-26"):
    """Update stats for all players in the database"""

    print("=" * 60)
    print(f"AUTOMATED STATS UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    engine = get_engine()
    session = get_session(engine)
    fetcher = NBAStatsFetcher()

    try:
        # Get all players from database
        players = session.query(Player).all()

        print(f"\n[INFO] Found {len(players)} players in database")

        total_new_games = 0
        players_updated = 0

        for idx, player in enumerate(players, 1):
            print(f"\n[{idx}/{len(players)}] Processing {player.name}...")

            try:
                # Respect API rate limits
                time.sleep(0.6)

                new_games = update_player_stats(
                    session,
                    fetcher,
                    player.name,
                    player.team,
                    player.position,
                    season
                )

                if new_games > 0:
                    total_new_games += new_games
                    players_updated += 1

            except Exception as e:
                print(f"  [ERROR] Failed to update {player.name}: {e}")
                continue

        # Summary
        print("\n" + "=" * 60)
        print("UPDATE SUMMARY")
        print("=" * 60)
        print(f"Players checked: {len(players)}")
        print(f"Players with new games: {players_updated}")
        print(f"Total new games added: {total_new_games}")

        # Get updated totals
        total_games = session.query(Game).count()
        print(f"Total games in database: {total_games}")
        print("=" * 60)

        return {
            "success": True,
            "players_checked": len(players),
            "players_updated": players_updated,
            "new_games": total_new_games,
            "total_games": total_games
        }

    except Exception as e:
        print(f"\n[ERROR] Update failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        session.close()


if __name__ == "__main__":
    result = update_all_players()

    if not result["success"]:
        sys.exit(1)
