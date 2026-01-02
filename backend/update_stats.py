"""
Automated Stats Update Script
Fetches new games for existing players and updates the database
Uses hybrid approach: nba_api for historical data + ESPN for recent games
"""
import sys
import io
from datetime import datetime, date, timedelta
from nba_stats_fetcher import NBAStatsFetcher
from espn_recent_games_scraper import ESPNAPIClient
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


def add_espn_recent_games(session, days_back=7):
    """
    Add recent games from ESPN to supplement nba_api data

    Note: Reduced to 7 days to avoid memory issues on free tier

    Args:
        session: Database session
        days_back: How many days to look back (default 7)

    Returns:
        Number of games added from ESPN
    """
    print("\n" + "=" * 60)
    print("ESPN RECENT GAMES SUPPLEMENT")
    print("=" * 60)
    print(f"[INFO] Fetching last {days_back} days of games from ESPN...")

    espn_client = ESPNAPIClient()
    total_added = 0
    games_batch = []
    batch_size = 50  # Commit in smaller batches to reduce memory

    try:
        # Fetch player stats for each day
        today = datetime.now()

        for days_ago in range(days_back):
            date_to_fetch = today - timedelta(days=days_ago)
            date_str = date_to_fetch.strftime("%Y%m%d")

            print(f"\n[INFO] Fetching {date_str}...")

            # Get all player stats from this date
            player_stats = espn_client.get_player_stats_from_date(date_str)

            if not player_stats:
                print(f"  No games found")
                continue

            print(f"  Found {len(player_stats)} player performances")

            # Process each player's stats
            for stat in player_stats:
                try:
                    # Find player in database
                    player = session.query(Player).filter_by(name=stat['player_name']).first()

                    if not player:
                        # Skip players not in our database
                        continue

                    # Check if game already exists
                    game_date = datetime.strptime(stat['date'], '%Y-%m-%d').date()
                    existing = session.query(Game).filter_by(
                        player_id=player.id,
                        date=game_date,
                        opponent=stat['opponent']
                    ).first()

                    if existing:
                        # Game already in database
                        continue

                    # Add new game to batch
                    new_game = Game(
                        player_id=player.id,
                        date=game_date,
                        opponent=stat['opponent'],
                        is_home=bool(stat['is_home']),
                        points=int(stat['points']),
                        rebounds=int(stat['rebounds']),
                        assists=int(stat['assists']),
                        steals=int(stat['steals']),
                        blocks=int(stat['blocks']),
                        three_pm=int(stat['three_pm'])
                    )
                    games_batch.append(new_game)
                    total_added += 1

                    # Commit in batches to reduce memory usage
                    if len(games_batch) >= batch_size:
                        session.bulk_save_objects(games_batch)
                        session.commit()
                        games_batch = []  # Clear batch
                        print(f"  [COMMIT] Saved batch of {batch_size} games")

                except Exception as e:
                    print(f"  [WARNING] Failed to add game for {stat.get('player_name')}: {e}")
                    continue

            # Commit remaining games after each day
            if games_batch:
                session.bulk_save_objects(games_batch)
                session.commit()
                games_batch = []

            # Rate limiting
            time.sleep(0.5)

        # Final commit for any remaining games
        if games_batch:
            session.bulk_save_objects(games_batch)
            session.commit()

        print("\n" + "=" * 60)
        print(f"[SUCCESS] Added {total_added} new games from ESPN")
        print("=" * 60)

        return total_added

    except Exception as e:
        print(f"\n[ERROR] ESPN supplement failed: {e}")
        import traceback
        traceback.print_exc()
        return 0


def update_all_players(season="2025-26", use_espn_supplement=True):
    """Update stats for all players in the database"""

    print("=" * 60)
    print(f"AUTOMATED STATS UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    engine = get_engine()
    session = get_session(engine)
    fetcher = NBAStatsFetcher()

    try:
        # Get player count first
        player_count = session.query(Player).count()
        print(f"\n[INFO] Found {player_count} players in database")

        total_new_games = 0
        players_updated = 0

        # Step 1: Update from NBA API (historical data)
        print("\n" + "=" * 60)
        print("PHASE 1: NBA API UPDATE")
        print("=" * 60)

        # Process players in batches to reduce memory usage
        batch_size = 20
        for batch_start in range(0, player_count, batch_size):
            # Get a batch of players
            players_batch = session.query(Player).offset(batch_start).limit(batch_size).all()

            print(f"\n[BATCH] Processing players {batch_start+1} to {min(batch_start+batch_size, player_count)}")

            for idx, player in enumerate(players_batch, batch_start + 1):
                print(f"\n[{idx}/{player_count}] Processing {player.name}...")

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

            # Clear session after each batch to free memory
            session.expunge_all()
            print(f"[BATCH COMPLETE] Cleared session cache")

        # Step 2: Supplement with ESPN recent games
        espn_games_added = 0
        if use_espn_supplement:
            espn_games_added = add_espn_recent_games(session, days_back=7)
            total_new_games += espn_games_added

        # Summary
        print("\n" + "=" * 60)
        print("FINAL UPDATE SUMMARY")
        print("=" * 60)
        print(f"Players checked: {player_count}")
        print(f"Players with new games (NBA API): {players_updated}")
        print(f"New games from NBA API: {total_new_games - espn_games_added}")
        print(f"New games from ESPN: {espn_games_added}")
        print(f"Total new games added: {total_new_games}")

        # Get updated totals
        total_games = session.query(Game).count()
        print(f"Total games in database: {total_games}")
        print("=" * 60)

        return {
            "success": True,
            "players_checked": player_count,
            "players_updated": players_updated,
            "new_games": total_new_games,
            "espn_games": espn_games_added,
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
