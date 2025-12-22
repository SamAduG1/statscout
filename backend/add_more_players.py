"""
Add top players from each team to expand coverage for betting analysis
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

# Top players to add (3-4 per team, focusing on fantasy/betting relevance)
NEW_PLAYERS = [
    # Atlanta Hawks
    {"name": "Dejounte Murray", "team": "ATL", "position": "PG"},
    {"name": "Clint Capela", "team": "ATL", "position": "C"},

    # Brooklyn Nets
    {"name": "Mikal Bridges", "team": "BKN", "position": "SF"},
    {"name": "Nic Claxton", "team": "BKN", "position": "C"},

    # Boston Celtics
    {"name": "Jayson Tatum", "team": "BOS", "position": "SF"},
    {"name": "Kristaps Porziņģis", "team": "BOS", "position": "C"},
    {"name": "Derrick White", "team": "BOS", "position": "PG"},

    # Charlotte Hornets
    {"name": "Miles Bridges", "team": "CHA", "position": "SF"},
    {"name": "Mark Williams", "team": "CHA", "position": "C"},

    # Chicago Bulls
    {"name": "Zach LaVine", "team": "CHI", "position": "SG"},
    {"name": "Nikola Vučević", "team": "CHI", "position": "C"},
    {"name": "Coby White", "team": "CHI", "position": "PG"},

    # Cleveland Cavaliers
    {"name": "Donovan Mitchell", "team": "CLE", "position": "SG"},
    {"name": "Jarrett Allen", "team": "CLE", "position": "C"},
    {"name": "Caris LeVert", "team": "CLE", "position": "SG"},

    # Dallas Mavericks
    {"name": "Luka Dončić", "team": "DAL", "position": "PG"},
    {"name": "Kyrie Irving", "team": "DAL", "position": "PG"},
    {"name": "Daniel Gafford", "team": "DAL", "position": "C"},

    # Denver Nuggets
    {"name": "Nikola Jokić", "team": "DEN", "position": "C"},
    {"name": "Jamal Murray", "team": "DEN", "position": "PG"},
    {"name": "Michael Porter Jr.", "team": "DEN", "position": "SF"},

    # Detroit Pistons
    {"name": "Jaden Ivey", "team": "DET", "position": "SG"},
    {"name": "Tobias Harris", "team": "DET", "position": "PF"},

    # Golden State Warriors
    {"name": "Stephen Curry", "team": "GSW", "position": "PG"},
    {"name": "Draymond Green", "team": "GSW", "position": "PF"},
    {"name": "Jonathan Kuminga", "team": "GSW", "position": "SF"},

    # Houston Rockets
    {"name": "Alperen Şengün", "team": "HOU", "position": "C"},
    {"name": "Fred VanVleet", "team": "HOU", "position": "PG"},
    {"name": "Dillon Brooks", "team": "HOU", "position": "SF"},

    # Indiana Pacers
    {"name": "Pascal Siakam", "team": "IND", "position": "PF"},
    {"name": "Myles Turner", "team": "IND", "position": "C"},
    {"name": "Benedict Mathurin", "team": "IND", "position": "SG"},

    # LA Clippers
    {"name": "James Harden", "team": "LAC", "position": "PG"},
    {"name": "Kawhi Leonard", "team": "LAC", "position": "SF"},
    {"name": "Ivica Zubac", "team": "LAC", "position": "C"},

    # Los Angeles Lakers
    {"name": "Anthony Davis", "team": "LAL", "position": "C"},
    {"name": "Austin Reaves", "team": "LAL", "position": "SG"},
    {"name": "Rui Hachimura", "team": "LAL", "position": "PF"},

    # Memphis Grizzlies
    {"name": "Desmond Bane", "team": "MEM", "position": "SG"},
    {"name": "Jaren Jackson Jr.", "team": "MEM", "position": "PF"},
    {"name": "Marcus Smart", "team": "MEM", "position": "PG"},

    # Miami Heat
    {"name": "Bam Adebayo", "team": "MIA", "position": "C"},
    {"name": "Tyler Herro", "team": "MIA", "position": "SG"},
    {"name": "Terry Rozier", "team": "MIA", "position": "PG"},

    # Milwaukee Bucks
    {"name": "Damian Lillard", "team": "MIL", "position": "PG"},
    {"name": "Brook Lopez", "team": "MIL", "position": "C"},
    {"name": "Bobby Portis", "team": "MIL", "position": "PF"},

    # Minnesota Timberwolves
    {"name": "Rudy Gobert", "team": "MIN", "position": "C"},
    {"name": "Mike Conley", "team": "MIN", "position": "PG"},
    {"name": "Naz Reid", "team": "MIN", "position": "C"},

    # New Orleans Pelicans
    {"name": "Zion Williamson", "team": "NOP", "position": "PF"},
    {"name": "CJ McCollum", "team": "NOP", "position": "SG"},
    {"name": "Herbert Jones", "team": "NOP", "position": "SF"},

    # New York Knicks
    {"name": "Karl-Anthony Towns", "team": "NYK", "position": "C"},
    {"name": "OG Anunoby", "team": "NYK", "position": "SF"},
    {"name": "Josh Hart", "team": "NYK", "position": "SG"},

    # Oklahoma City Thunder
    {"name": "Shai Gilgeous-Alexander", "team": "OKC", "position": "PG"},
    {"name": "Chet Holmgren", "team": "OKC", "position": "C"},
    {"name": "Jalen Williams", "team": "OKC", "position": "SF"},

    # Orlando Magic
    {"name": "Franz Wagner", "team": "ORL", "position": "SF"},
    {"name": "Wendell Carter Jr.", "team": "ORL", "position": "C"},
    {"name": "Jalen Suggs", "team": "ORL", "position": "SG"},

    # Philadelphia 76ers
    {"name": "Joel Embiid", "team": "PHI", "position": "C"},
    {"name": "Tyrese Maxey", "team": "PHI", "position": "PG"},
    {"name": "Paul George", "team": "PHI", "position": "SF"},

    # Phoenix Suns
    {"name": "Devin Booker", "team": "PHX", "position": "SG"},
    {"name": "Jusuf Nurkić", "team": "PHX", "position": "C"},
    {"name": "Bradley Beal", "team": "PHX", "position": "SG"},

    # Portland Trail Blazers
    {"name": "Shaedon Sharpe", "team": "POR", "position": "SG"},
    {"name": "Jerami Grant", "team": "POR", "position": "PF"},
    {"name": "Deandre Ayton", "team": "POR", "position": "C"},

    # Sacramento Kings
    {"name": "Domantas Sabonis", "team": "SAC", "position": "C"},
    {"name": "Keegan Murray", "team": "SAC", "position": "SF"},
    {"name": "DeMar DeRozan", "team": "SAC", "position": "SF"},

    # San Antonio Spurs
    {"name": "Chris Paul", "team": "SAS", "position": "PG"},
    {"name": "Keldon Johnson", "team": "SAS", "position": "SF"},
    {"name": "Jeremy Sochan", "team": "SAS", "position": "PF"},

    # Toronto Raptors
    {"name": "Scottie Barnes", "team": "TOR", "position": "SF"},
    {"name": "RJ Barrett", "team": "TOR", "position": "SG"},
    {"name": "Jakob Poeltl", "team": "TOR", "position": "C"},

    # Utah Jazz
    {"name": "Lauri Markkanen", "team": "UTA", "position": "PF"},
    {"name": "Walker Kessler", "team": "UTA", "position": "C"},
    {"name": "Collin Sexton", "team": "UTA", "position": "PG"},

    # Washington Wizards (no new additions - limited data)
]


def add_new_players_to_db():
    """Fetch and add new players to database"""

    print("=" * 60)
    print(f"ADDING {len(NEW_PLAYERS)} NEW PLAYERS")
    print("=" * 60)

    engine = get_engine()
    session = get_session(engine)
    fetcher = NBAStatsFetcher()

    try:
        players_added = 0
        games_added = 0

        for idx, player_info in enumerate(NEW_PLAYERS, 1):
            player_name = player_info['name']
            team = player_info['team']
            position = player_info['position']

            print(f"\n[{idx}/{len(NEW_PLAYERS)}] Processing {player_name} ({team})...")

            # Check if player already exists
            existing = session.query(Player).filter_by(name=player_name).first()
            if existing:
                print(f"  [SKIP] {player_name} already in database")
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
                continue

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Players added: {players_added}")
        print(f"Games added: {games_added}")

        # Get totals
        total_players = session.query(Player).count()
        total_games = session.query(Game).count()
        print(f"Total players in database: {total_players}")
        print(f"Total games in database: {total_games}")
        print("=" * 60)

    finally:
        session.close()


if __name__ == "__main__":
    add_new_players_to_db()
