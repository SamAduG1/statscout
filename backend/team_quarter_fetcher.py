"""
Team Quarter Data Fetcher
Fetches quarter-by-quarter scoring data for all NBA teams from the 2025-26 season
"""

from nba_api.stats.endpoints import leaguegamefinder, boxscoresummaryv2
from nba_api.stats.static import teams as nba_teams
from models import TeamGame, get_engine, get_session, init_db
from datetime import datetime
import time


class TeamQuarterFetcher:
    """Fetches and stores team quarter-by-quarter data"""

    def __init__(self, season="2025-26"):
        self.season = season
        self.engine = get_engine()
        init_db(self.engine)  # Ensure tables exist
        self.session = get_session(self.engine)

    def fetch_all_teams_quarter_data(self):
        """Fetch quarter data for all 30 NBA teams"""

        all_teams = nba_teams.get_teams()
        print(f"\n[INFO] Fetching quarter data for {len(all_teams)} NBA teams...")
        print(f"[INFO] Season: {self.season}")

        total_games_added = 0

        for idx, team_data in enumerate(all_teams, 1):
            team_abbr = team_data['abbreviation']
            team_name = team_data['full_name']
            team_id = team_data['id']

            print(f"\n[{idx}/{len(all_teams)}] Processing {team_name} ({team_abbr})...")

            try:
                games_added = self.fetch_team_quarter_data(team_id, team_abbr, team_name)
                total_games_added += games_added

                # Rate limiting - be nice to NBA API
                if idx < len(all_teams):
                    time.sleep(0.6)

            except Exception as e:
                print(f"[ERROR] Failed to fetch data for {team_name}: {e}")
                continue

        print(f"\n[SUCCESS] Completed! Total games added: {total_games_added}")
        return total_games_added

    def fetch_team_quarter_data(self, team_id, team_abbr, team_name):
        """Fetch quarter data for a specific team"""

        # Find all games for this team in the season
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team_id,
            season_nullable=self.season,
            season_type_nullable='Regular Season'
        )

        games_df = gamefinder.get_data_frames()[0]

        if len(games_df) == 0:
            print(f"  No games found for {team_name}")
            return 0

        print(f"  Found {len(games_df)} games")

        games_added = 0

        for idx, game_row in games_df.iterrows():
            game_id = game_row['GAME_ID']

            # Check if we already have this game
            existing = self.session.query(TeamGame).filter_by(
                game_id=f"{game_id}_{team_abbr}"
            ).first()

            if existing:
                continue  # Skip if already in database

            # Fetch quarter data for this game
            try:
                quarter_data = self.fetch_game_quarter_data(game_id, team_abbr, game_row)

                if quarter_data:
                    # Create TeamGame record
                    team_game = TeamGame(**quarter_data)
                    self.session.add(team_game)
                    games_added += 1

                    # Commit every 10 games
                    if games_added % 10 == 0:
                        self.session.commit()

                # Rate limiting
                time.sleep(0.6)

            except Exception as e:
                print(f"    Error fetching game {game_id}: {e}")
                continue

        # Final commit
        self.session.commit()
        print(f"  Added {games_added} new games to database")

        return games_added

    def fetch_game_quarter_data(self, game_id, team_abbr, game_row):
        """Fetch quarter-by-quarter data for a specific game"""

        try:
            # Fetch box score summary
            box_summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id)
            line_score_df = box_summary.line_score.get_data_frame()

            if line_score_df.empty:
                return None

            # Find this team's row
            team_row = line_score_df[line_score_df['TEAM_ABBREVIATION'] == team_abbr]

            if team_row.empty:
                return None

            team_row = team_row.iloc[0]

            # Find opponent's row
            opponent_row = line_score_df[line_score_df['TEAM_ABBREVIATION'] != team_abbr]
            if opponent_row.empty:
                return None

            opponent_row = opponent_row.iloc[0]
            opponent_abbr = opponent_row['TEAM_ABBREVIATION']

            # Extract quarter data
            q1 = team_row['PTS_QTR1']
            q2 = team_row['PTS_QTR2']
            q3 = team_row['PTS_QTR3']
            q4 = team_row['PTS_QTR4']

            # Handle None values for future games
            if q1 is None or q2 is None or q3 is None or q4 is None:
                return None  # Skip games without complete quarter data

            # Calculate overtime points
            ot_points = 0
            if team_row['PTS_OT1'] is not None:
                ot_points += team_row['PTS_OT1']

            # Determine home/away
            matchup = game_row['MATCHUP']
            is_home = 'vs.' in matchup

            # Determine win/loss
            won = game_row['WL'] == 'W'

            # Parse date
            date_str = game_row['GAME_DATE']
            game_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Get total points
            total_points = team_row['PTS']
            opponent_points = opponent_row['PTS']

            return {
                'game_id': f"{game_id}_{team_abbr}",  # Unique per team
                'team': team_abbr,
                'opponent': opponent_abbr,
                'date': game_date,
                'is_home': is_home,
                'season': self.season,
                'q1_points': int(q1),
                'q2_points': int(q2),
                'q3_points': int(q3),
                'q4_points': int(q4),
                'ot_points': int(ot_points),
                'total_points': int(total_points),
                'opponent_points': int(opponent_points),
                'won': won
            }

        except Exception as e:
            print(f"    Error parsing game data: {e}")
            return None

    def close(self):
        """Close database session"""
        self.session.close()


if __name__ == "__main__":
    print("=" * 70)
    print("TEAM QUARTER DATA FETCHER - 2025-26 SEASON")
    print("=" * 70)

    fetcher = TeamQuarterFetcher(season="2025-26")

    try:
        total_games = fetcher.fetch_all_teams_quarter_data()
        print(f"\n[COMPLETE] Successfully added {total_games} team games to database!")

    except KeyboardInterrupt:
        print("\n[STOPPED] Process interrupted by user")

    finally:
        fetcher.close()
        print("\n[INFO] Database connection closed")
