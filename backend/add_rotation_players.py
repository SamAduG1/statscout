"""
Add Additional Rotation Players to Database
Expanding coverage with key bench and rotation players for 2025-26 season
"""
import sys
import io
from nba_stats_fetcher import NBAStatsFetcher
from models import get_engine, get_session, Player, Game
from datetime import datetime
import time

# Force UTF-8 output
if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

# Additional rotation players for 2025-26 season
ROTATION_PLAYERS = [
    {"name": "Bogdan Bogdanović", "team": "ATL", "position": "SG"},
    {"name": "Jalen Johnson", "team": "ATL", "position": "PF"},
    {"name": "Onyeka Okongwu", "team": "ATL", "position": "C"},
    {"name": "Kobe Bufkin", "team": "ATL", "position": "PG"},
    {"name": "Jrue Holiday", "team": "BOS", "position": "PG"},
    {"name": "Grant Williams", "team": "BOS", "position": "PF"},
    {"name": "Sam Hauser", "team": "BOS", "position": "SF"},
    {"name": "Luke Kornet", "team": "BOS", "position": "C"},
    {"name": "Ziaire Williams", "team": "BKN", "position": "SF"},
    {"name": "Terance Mann", "team": "BKN", "position": "SG"},
    {"name": "Nic Claxton", "team": "BKN", "position": "C"},
    {"name": "Maxime Raynaud", "team": "BKN", "position": "C"},
    {"name": "Walter Clayton Jr.", "team": "BKN", "position": "PG"},
    {"name": "Tre Mann", "team": "CHA", "position": "PG"},
    {"name": "Mark Williams", "team": "CHA", "position": "C"},
    {"name": "Svi Mykhailiuk", "team": "CHI", "position": "SF"},
    {"name": "Patrick Williams", "team": "CHI", "position": "PF"},
    {"name": "Kevin Huerter", "team": "CLE", "position": "SG"},
    {"name": "Max Strus", "team": "CLE", "position": "SF"},
    {"name": "Lonzo Ball", "team": "CHI", "position": "PG"},
    {"name": "Larry Nance Jr.", "team": "CLE", "position": "PF"},
    {"name": "Jaylon Tyson", "team": "CLE", "position": "SF"},
    {"name": "Caris LeVert", "team": "CLE", "position": "SG"},
    {"name": "Duncan Robinson", "team": "MIA", "position": "SF"},
    {"name": "Ron Holland", "team": "DET", "position": "SF"},
    {"name": "Isaiah Stewart", "team": "DET", "position": "C"},
    {"name": "Isaiah Jackson", "team": "IND", "position": "C"},
    {"name": "Nikola Jović", "team": "MIA", "position": "PF"},
    {"name": "Dru Smith", "team": "MIA", "position": "PG"},
    {"name": "Brook Lopez", "team": "MIL", "position": "C"},
    {"name": "Jordan Clarkson", "team": "UTA", "position": "SG"},
    {"name": "Guerschon Yabusele", "team": "PHI", "position": "PF"},
    {"name": "Malcolm Brogdon", "team": "WAS", "position": "PG"},
    {"name": "Jared McCain", "team": "PHI", "position": "PG"},
    {"name": "Quentin Grimes", "team": "DAL", "position": "SG"},
    {"name": "Trendon Watford", "team": "BKN", "position": "PF"},
    {"name": "Paul Reed", "team": "DET", "position": "C"},
    {"name": "Dennis Schröder", "team": "GSW", "position": "PG"},
    {"name": "Keon Ellis", "team": "SAC", "position": "SG"},
    {"name": "Nique Clifford", "team": "SAC", "position": "SF"},
    {"name": "Brice Sensabaugh", "team": "UTA", "position": "SF"},
    {"name": "P.J. Washington", "team": "DAL", "position": "PF"},
    {"name": "Max Christie", "team": "LAL", "position": "SG"},
    {"name": "Brandon Williams", "team": "POR", "position": "PG"},
    {"name": "Cam Johnson", "team": "BKN", "position": "SF"},
    {"name": "Bruce Brown", "team": "TOR", "position": "SG"},
    {"name": "Brandin Podziemski", "team": "GSW", "position": "SG"},
    {"name": "Jonathan Kuminga", "team": "GSW", "position": "PF"},
    {"name": "Buddy Hield", "team": "GSW", "position": "SG"},
    {"name": "Al Horford", "team": "BOS", "position": "C"},
    {"name": "Tari Eason", "team": "HOU", "position": "SF"},
    {"name": "Chris Paul", "team": "SAS", "position": "PG"},
    {"name": "Marcus Smart", "team": "MEM", "position": "PG"},
    {"name": "Jarred Vanderbilt", "team": "LAL", "position": "PF"},
    {"name": "Cam Spencer", "team": "MEM", "position": "SG"},
    {"name": "Santi Aldama", "team": "MEM", "position": "PF"},
    {"name": "Ty Jerome", "team": "CLE", "position": "PG"},
    {"name": "Mike Conley", "team": "MIN", "position": "PG"},
    {"name": "Cason Wallace", "team": "OKC", "position": "SG"},
    {"name": "Malik Monk", "team": "SAC", "position": "SG"},
    {"name": "Dylan Harper", "team": "BKN", "position": "PG"},
    {"name": "Ace Bailey", "team": "UTA", "position": "SF"},
    {"name": "Corey Kispert", "team": "WAS", "position": "SF"},
    {"name": "Dario Šaric", "team": "DEN", "position": "C"},
    {"name": "VJ Edgecombe", "team": "PHI", "position": "SG"},
    {"name": "Neemias Queta", "team": "BOS", "position": "C"},
    {"name": "Norman Powell", "team": "LAC", "position": "SG"},
    {"name": "Jaime Jaquez Jr.", "team": "MIA", "position": "SF"},
    {"name": "Kel'el Ware", "team": "MIA", "position": "C"},
    {"name": "Davion Mitchell", "team": "TOR", "position": "PG"},
    {"name": "Jordan Walsh", "team": "BOS", "position": "SF"},
]


def add_rotation_players_to_db():
    """Fetch and add rotation players to database"""

    print("=" * 60)
    print(f"ADDING ROTATION PLAYERS ({len(ROTATION_PLAYERS)} PLAYERS)")
    print("=" * 60)

    engine = get_engine()
    session = get_session(engine)
    fetcher = NBAStatsFetcher()

    try:
        players_added = 0
        players_skipped = 0
        players_failed = 0
        games_added = 0

        for idx, player_info in enumerate(ROTATION_PLAYERS, 1):
            player_name = player_info['name']
            team = player_info['team']
            position = player_info['position']

            print(f"\n[{idx}/{len(ROTATION_PLAYERS)}] Processing {player_name} ({team})...")

            # Check if player already exists
            existing = session.query(Player).filter_by(name=player_name).first()
            if existing:
                print(f"  [SKIP] {player_name} already in database")
                players_skipped += 1
                continue

            # Respect API rate limits
            time.sleep(0.6)

            # Fetch player data
            try:
                games = fetcher.fetch_player_season(
                    player_name,
                    team,
                    position,
                    season="2025-26"
                )

                if not games:
                    print(f"  [WARNING] No games found for {player_name}")
                    players_failed += 1
                    continue

                # Create player
                player = Player(name=player_name, team=team, position=position)
                session.add(player)
                session.flush()

                # Add games
                for game in games:
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

                session.commit()
                players_added += 1
                games_added += len(games)

                print(f"  [SUCCESS] Added {player_name} with {len(games)} games")

            except Exception as e:
                print(f"  [ERROR] Failed to fetch {player_name}: {e}")
                session.rollback()
                players_failed += 1
                continue

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✅ Players added: {players_added}")
        print(f"⏭️  Players skipped (already in DB): {players_skipped}")
        print(f"❌ Players failed (no data): {players_failed}")
        print(f"📊 Games added: {games_added}")

        # Get totals
        total_players = session.query(Player).count()
        total_games = session.query(Game).count()
        print(f"\n🏀 Total players in database: {total_players}")
        print(f"🎯 Total games in database: {total_games}")
        print("=" * 60)

    finally:
        session.close()


if __name__ == "__main__":
    add_rotation_players_to_db()
