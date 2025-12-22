"""
Add 2025-26 NBA Starters to Database
Comprehensive list of current starting lineups across all 30 teams
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

# Complete starter list for 2025-26 season
STARTERS_2025 = [
    # Eastern Conference

    # Atlanta Hawks
    {"name": "Dyson Daniels", "team": "ATL", "position": "PG"},
    {"name": "Nickeil Alexander-Walker", "team": "ATL", "position": "SG"},
    {"name": "Zaccharie Risacher", "team": "ATL", "position": "SF"},
    {"name": "Jalen Johnson", "team": "ATL", "position": "PF"},
    {"name": "Onyeka Okongwu", "team": "ATL", "position": "C"},

    # Boston Celtics
    {"name": "Payton Pritchard", "team": "BOS", "position": "PG"},
    {"name": "Derrick White", "team": "BOS", "position": "SG"},
    {"name": "Jaylen Brown", "team": "BOS", "position": "SF"},
    {"name": "Sam Hauser", "team": "BOS", "position": "PF"},
    {"name": "Neemias Queta", "team": "BOS", "position": "C"},

    # Brooklyn Nets
    {"name": "Egor Demin", "team": "BKN", "position": "PG"},
    {"name": "Terance Mann", "team": "BKN", "position": "SG"},
    {"name": "Michael Porter Jr.", "team": "BKN", "position": "SF"},
    {"name": "Ziaire Williams", "team": "BKN", "position": "PF"},
    {"name": "Nicolas Claxton", "team": "BKN", "position": "C"},

    # Charlotte Hornets
    {"name": "LaMelo Ball", "team": "CHA", "position": "PG"},
    {"name": "Brandon Miller", "team": "CHA", "position": "SG"},
    {"name": "Miles Bridges", "team": "CHA", "position": "SF"},
    {"name": "Kon Knueppel", "team": "CHA", "position": "PF"},
    {"name": "Ryan Kalkbrenner", "team": "CHA", "position": "C"},

    # Chicago Bulls
    {"name": "Coby White", "team": "CHI", "position": "PG"},
    {"name": "Matas Buzelis", "team": "CHI", "position": "SG"},
    {"name": "Josh Giddey", "team": "CHI", "position": "SF"},
    {"name": "Nikola Vučević", "team": "CHI", "position": "PF"},
    {"name": "Isaac Okoro", "team": "CHI", "position": "C"},

    # Cleveland Cavaliers
    {"name": "Donovan Mitchell", "team": "CLE", "position": "PG"},
    {"name": "Darius Garland", "team": "CLE", "position": "SG"},
    {"name": "De'Andre Hunter", "team": "CLE", "position": "SF"},
    {"name": "Evan Mobley", "team": "CLE", "position": "PF"},
    {"name": "Jarrett Allen", "team": "CLE", "position": "C"},

    # Detroit Pistons
    {"name": "Cade Cunningham", "team": "DET", "position": "PG"},
    {"name": "Jaden Ivey", "team": "DET", "position": "SG"},
    {"name": "Tobias Harris", "team": "DET", "position": "SF"},
    {"name": "Ausar Thompson", "team": "DET", "position": "PF"},
    {"name": "Jalen Duren", "team": "DET", "position": "C"},

    # Indiana Pacers
    {"name": "Andrew Nembhard", "team": "IND", "position": "PG"},
    {"name": "Bennedict Mathurin", "team": "IND", "position": "SG"},
    {"name": "Pascal Siakam", "team": "IND", "position": "SF"},
    {"name": "Aaron Nesmith", "team": "IND", "position": "PF"},
    {"name": "Isaiah Jackson", "team": "IND", "position": "C"},

    # Miami Heat
    {"name": "Tyler Herro", "team": "MIA", "position": "PG"},
    {"name": "Andrew Wiggins", "team": "MIA", "position": "SG"},
    {"name": "Bam Adebayo", "team": "MIA", "position": "SF"},
    {"name": "Norman Powell", "team": "MIA", "position": "PF"},
    {"name": "Nikola Jović", "team": "MIA", "position": "C"},

    # Milwaukee Bucks
    {"name": "Giannis Antetokounmpo", "team": "MIL", "position": "PG"},
    {"name": "Myles Turner", "team": "MIL", "position": "SG"},
    {"name": "Kevin Porter Jr.", "team": "MIL", "position": "SF"},
    {"name": "AJ Green", "team": "MIL", "position": "PF"},
    {"name": "Gary Trent Jr.", "team": "MIL", "position": "C"},

    # New York Knicks
    {"name": "Jalen Brunson", "team": "NYK", "position": "PG"},
    {"name": "Mikal Bridges", "team": "NYK", "position": "SG"},
    {"name": "OG Anunoby", "team": "NYK", "position": "SF"},
    {"name": "Karl-Anthony Towns", "team": "NYK", "position": "PF"},
    {"name": "Mitchell Robinson", "team": "NYK", "position": "C"},

    # Orlando Magic
    {"name": "Paolo Banchero", "team": "ORL", "position": "PG"},
    {"name": "Franz Wagner", "team": "ORL", "position": "SG"},
    {"name": "Desmond Bane", "team": "ORL", "position": "SF"},
    {"name": "Jalen Suggs", "team": "ORL", "position": "PF"},
    {"name": "Wendell Carter Jr.", "team": "ORL", "position": "C"},

    # Philadelphia 76ers
    {"name": "Tyrese Maxey", "team": "PHI", "position": "PG"},
    {"name": "Paul George", "team": "PHI", "position": "SG"},
    {"name": "VJ Edgecombe", "team": "PHI", "position": "SF"},
    {"name": "Kelly Oubre Jr.", "team": "PHI", "position": "PF"},
    {"name": "Joel Embiid", "team": "PHI", "position": "C"},

    # Toronto Raptors
    {"name": "Immanuel Quickley", "team": "TOR", "position": "PG"},
    {"name": "RJ Barrett", "team": "TOR", "position": "SG"},
    {"name": "Brandon Ingram", "team": "TOR", "position": "SF"},
    {"name": "Scottie Barnes", "team": "TOR", "position": "PF"},
    {"name": "Jakob Poeltl", "team": "TOR", "position": "C"},

    # Washington Wizards
    {"name": "CJ McCollum", "team": "WAS", "position": "PG"},
    {"name": "Khris Middleton", "team": "WAS", "position": "SG"},
    {"name": "Alex Sarr", "team": "WAS", "position": "SF"},
    {"name": "Bub Carrington", "team": "WAS", "position": "PF"},
    {"name": "Kyshawn George", "team": "WAS", "position": "C"},

    # Western Conference

    # Dallas Mavericks
    {"name": "Cooper Flagg", "team": "DAL", "position": "PG"},
    {"name": "D'Angelo Russell", "team": "DAL", "position": "SG"},
    {"name": "Klay Thompson", "team": "DAL", "position": "SF"},
    {"name": "Anthony Davis", "team": "DAL", "position": "PF"},
    {"name": "Dereck Lively II", "team": "DAL", "position": "C"},

    # Denver Nuggets
    {"name": "Jamal Murray", "team": "DEN", "position": "PG"},
    {"name": "Cam Johnson", "team": "DEN", "position": "SG"},
    {"name": "Christian Braun", "team": "DEN", "position": "SF"},
    {"name": "Aaron Gordon", "team": "DEN", "position": "PF"},
    {"name": "Nikola Jokić", "team": "DEN", "position": "C"},

    # Golden State Warriors
    {"name": "Stephen Curry", "team": "GSW", "position": "PG"},
    {"name": "Moses Moody", "team": "GSW", "position": "SG"},
    {"name": "Jimmy Butler", "team": "GSW", "position": "SF"},
    {"name": "Draymond Green", "team": "GSW", "position": "PF"},
    {"name": "Quinten Post", "team": "GSW", "position": "C"},

    # Houston Rockets
    {"name": "Amen Thompson", "team": "HOU", "position": "PG"},
    {"name": "Kevin Durant", "team": "HOU", "position": "SG"},
    {"name": "Jabari Smith Jr.", "team": "HOU", "position": "SF"},
    {"name": "Alperen Şengün", "team": "HOU", "position": "PF"},
    {"name": "Reed Sheppard", "team": "HOU", "position": "C"},

    # LA Clippers
    {"name": "Kawhi Leonard", "team": "LAC", "position": "PG"},
    {"name": "James Harden", "team": "LAC", "position": "SG"},
    {"name": "Bradley Beal", "team": "LAC", "position": "SF"},
    {"name": "Derrick Jones Jr.", "team": "LAC", "position": "PF"},
    {"name": "Ivica Zubac", "team": "LAC", "position": "C"},

    # Los Angeles Lakers
    {"name": "Luka Dončić", "team": "LAL", "position": "PG"},
    {"name": "LeBron James", "team": "LAL", "position": "SG"},
    {"name": "Austin Reaves", "team": "LAL", "position": "SF"},
    {"name": "Rui Hachimura", "team": "LAL", "position": "PF"},
    {"name": "Deandre Ayton", "team": "LAL", "position": "C"},

    # Memphis Grizzlies
    {"name": "Ja Morant", "team": "MEM", "position": "PG"},
    {"name": "Jaylen Wells", "team": "MEM", "position": "SG"},
    {"name": "Jaren Jackson Jr.", "team": "MEM", "position": "SF"},
    {"name": "Zach Edey", "team": "MEM", "position": "PF"},
    {"name": "Kentavious Caldwell-Pope", "team": "MEM", "position": "C"},

    # Minnesota Timberwolves
    {"name": "Anthony Edwards", "team": "MIN", "position": "PG"},
    {"name": "Mike Conley", "team": "MIN", "position": "SG"},
    {"name": "Jaden McDaniels", "team": "MIN", "position": "SF"},
    {"name": "Julius Randle", "team": "MIN", "position": "PF"},
    {"name": "Rudy Gobert", "team": "MIN", "position": "C"},

    # New Orleans Pelicans
    {"name": "Herbert Jones", "team": "NOP", "position": "PG"},
    {"name": "Trey Murphy III", "team": "NOP", "position": "SG"},
    {"name": "Zion Williamson", "team": "NOP", "position": "SF"},
    {"name": "Derik Queen", "team": "NOP", "position": "PF"},
    {"name": "Jeremiah Fears", "team": "NOP", "position": "C"},

    # Oklahoma City Thunder
    {"name": "Shai Gilgeous-Alexander", "team": "OKC", "position": "PG"},
    {"name": "Jalen Williams", "team": "OKC", "position": "SG"},
    {"name": "Chet Holmgren", "team": "OKC", "position": "SF"},
    {"name": "Lu Dort", "team": "OKC", "position": "PF"},
    {"name": "Isaiah Hartenstein", "team": "OKC", "position": "C"},

    # Phoenix Suns
    {"name": "Devin Booker", "team": "PHX", "position": "PG"},
    {"name": "Jalen Green", "team": "PHX", "position": "SG"},
    {"name": "Dillon Brooks", "team": "PHX", "position": "SF"},
    {"name": "Mark Williams", "team": "PHX", "position": "PF"},
    {"name": "Ryan Dunn", "team": "PHX", "position": "C"},

    # Portland Trail Blazers
    {"name": "Deni Avdija", "team": "POR", "position": "PG"},
    {"name": "Shaedon Sharpe", "team": "POR", "position": "SG"},
    {"name": "Jrue Holiday", "team": "POR", "position": "SF"},
    {"name": "Toumani Camara", "team": "POR", "position": "PF"},
    {"name": "Donovan Clingan", "team": "POR", "position": "C"},

    # Sacramento Kings
    {"name": "Zach LaVine", "team": "SAC", "position": "PG"},
    {"name": "DeMar DeRozan", "team": "SAC", "position": "SG"},
    {"name": "Keegan Murray", "team": "SAC", "position": "SF"},
    {"name": "Domantas Sabonis", "team": "SAC", "position": "PF"},
    {"name": "Dennis Schröder", "team": "SAC", "position": "C"},

    # San Antonio Spurs
    {"name": "De'Aaron Fox", "team": "SAS", "position": "PG"},
    {"name": "Stephon Castle", "team": "SAS", "position": "SG"},
    {"name": "Jeremy Sochan", "team": "SAS", "position": "SF"},
    {"name": "Harrison Barnes", "team": "SAS", "position": "PF"},
    {"name": "Victor Wembanyama", "team": "SAS", "position": "C"},

    # Utah Jazz
    {"name": "Lauri Markkanen", "team": "UTA", "position": "PG"},
    {"name": "Ace Bailey", "team": "UTA", "position": "SG"},
    {"name": "Keyonte George", "team": "UTA", "position": "SF"},
    {"name": "Taylor Hendricks", "team": "UTA", "position": "PF"},
    {"name": "Walker Kessler", "team": "UTA", "position": "C"},
]


def add_starters_to_db():
    """Fetch and add 2025-26 starters to database"""

    print("=" * 60)
    print(f"ADDING 2025-26 NBA STARTERS ({len(STARTERS_2025)} PLAYERS)")
    print("=" * 60)

    engine = get_engine()
    session = get_session(engine)
    fetcher = NBAStatsFetcher()

    try:
        players_added = 0
        players_skipped = 0
        players_failed = 0
        games_added = 0

        for idx, player_info in enumerate(STARTERS_2025, 1):
            player_name = player_info['name']
            team = player_info['team']
            position = player_info['position']

            print(f"\n[{idx}/{len(STARTERS_2025)}] Processing {player_name} ({team})...")

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
    add_starters_to_db()
