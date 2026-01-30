"""
Add New Players - January 2026
Additional role players and rookies
"""
import sys
import io
import os
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

# Set Supabase DATABASE_URL for production database
os.environ['DATABASE_URL'] = 'postgresql://postgres.tqyzxwogjhehjcwhxnre:Softwareidk5852!@aws-1-us-east-2.pooler.supabase.com:6543/postgres'

# New players to add - January 2026
NEW_PLAYERS = [
    # New York Knicks
    {"name": "Miles McBride", "team": "NYK", "position": "PG"},
    {"name": "Landry Shamet", "team": "NYK", "position": "SG"},

    # Atlanta Hawks
    {"name": "Luke Kennard", "team": "ATL", "position": "SG"},

    # Oklahoma City Thunder
    {"name": "Aaron Wiggins", "team": "OKC", "position": "SG"},
    {"name": "Jaylin Williams", "team": "OKC", "position": "PF"},

    # Cleveland Cavaliers
    {"name": "Craig Porter Jr.", "team": "CLE", "position": "PG"},

    # Los Angeles Clippers
    {"name": "Nicolas Batum", "team": "LAC", "position": "PF"},
    {"name": "Jordan Miller", "team": "LAC", "position": "SF"},
    {"name": "Yanic Konan Niederhauser", "team": "LAC", "position": "C"},
    {"name": "Kobe Sanders", "team": "LAC", "position": "SG"},

    # Washington Wizards
    {"name": "Cam Whitmore", "team": "WAS", "position": "SF"},
    {"name": "Will Riley", "team": "WAS", "position": "SG"},

    # Dallas Mavericks
    {"name": "Dwight Powell", "team": "DAL", "position": "C"},
    {"name": "Jaden Hardy", "team": "DAL", "position": "SG"},

    # Utah Jazz
    {"name": "Cody Williams", "team": "UTA", "position": "SF"},

    # San Antonio Spurs (Dylan Harper - listed as Nets but playing for Spurs)
    {"name": "Dylan Harper", "team": "SAS", "position": "PG"},

    # Indiana Pacers
    {"name": "Johnny Furphy", "team": "IND", "position": "SF"},
    {"name": "Jarace Walker", "team": "IND", "position": "PF"},

    # Phoenix Suns
    {"name": "Grayson Allen", "team": "PHX", "position": "SG"},
    {"name": "Jordan Goodwin", "team": "PHX", "position": "PG"},

    # Brooklyn Nets
    {"name": "Drake Powell", "team": "BKN", "position": "SF"},

    # Boston Celtics
    {"name": "Luka Garza", "team": "BOS", "position": "C"},

    # Detroit Pistons
    {"name": "Javonte Green", "team": "DET", "position": "SF"},
    {"name": "Daniss Jenkins", "team": "DET", "position": "PG"},

    # Miami Heat
    {"name": "Pelle Larsson", "team": "MIA", "position": "SG"},
    {"name": "Simone Fontecchio", "team": "MIA", "position": "SF"},

    # Golden State Warriors
    {"name": "DeAnthony Melton", "team": "GSW", "position": "SG"},
    {"name": "Gary Payton II", "team": "GSW", "position": "PG"},
]


def add_new_players():
    """Add new players to the database"""

    print("=" * 60)
    print("ADDING NEW PLAYERS - JANUARY 2026")
    print("=" * 60)

    fetcher = NBAStatsFetcher()
    engine = get_engine()
    session = get_session(engine)

    added_count = 0
    skipped_count = 0
    failed_count = 0

    for player_info in NEW_PLAYERS:
        player_name = player_info["name"]
        team = player_info["team"]
        position = player_info["position"]

        # Check if player already exists
        existing = session.query(Player).filter_by(name=player_name).first()
        if existing:
            print(f"  [SKIP] {player_name} already exists (team: {existing.team})")
            skipped_count += 1
            continue

        print(f"\n[FETCHING] {player_name} ({team})...")

        try:
            # Fetch player data from NBA API
            games_data = fetcher.fetch_player_season(player_name, team, position)

            if games_data:
                # Create player record
                player = Player(name=player_name, team=team, position=position)
                session.add(player)
                session.flush()  # Get the player ID

                # Add games
                for game_data in games_data:
                    # Convert date string to Python date object
                    date_str = game_data['date']
                    if isinstance(date_str, str):
                        game_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        game_date = date_str

                    game = Game(
                        player_id=player.id,
                        date=game_date,
                        opponent=game_data['opponent'],
                        is_home=game_data['is_home'],
                        points=game_data['points'],
                        rebounds=game_data['rebounds'],
                        assists=game_data['assists'],
                        steals=game_data['steals'],
                        blocks=game_data['blocks'],
                        three_pm=game_data['three_pm'],
                        minutes=game_data['minutes']
                    )
                    session.add(game)

                session.commit()
                print(f"  [OK] Added {player_name} with {len(games_data)} games")
                added_count += 1
            else:
                print(f"  [WARN] No games found for {player_name}")
                # Still add the player with no games
                player = Player(name=player_name, team=team, position=position)
                session.add(player)
                session.commit()
                print(f"  [OK] Added {player_name} (no games yet)")
                added_count += 1

        except Exception as e:
            print(f"  [ERROR] Failed to add {player_name}: {e}")
            session.rollback()
            failed_count += 1

        # Rate limiting
        time.sleep(0.6)

    print("\n" + "=" * 60)
    print(f"SUMMARY: Added {added_count}, Skipped {skipped_count}, Failed {failed_count}")
    print("=" * 60)

    session.close()


if __name__ == "__main__":
    add_new_players()
