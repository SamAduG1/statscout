"""
NBA Stats Fetcher
Fetches real historical game data using nba_api (official NBA stats, no auth required)
"""

import sys
import io
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict

# Force UTF-8 output for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class NBAStatsFetcher:
    """Fetch real NBA player game logs using nba_api"""

    def __init__(self):
        """Initialize the NBA stats fetcher"""
        # Cache of all NBA players
        self.all_players = players.get_players()

    def find_player_id(self, player_name: str) -> int:
        """
        Find NBA player ID by name

        Args:
            player_name: Full player name (e.g., "LeBron James")

        Returns:
            Player ID integer, or None if not found
        """
        try:
            # Search for player (case insensitive)
            player_name_lower = player_name.lower()

            for player in self.all_players:
                if player['full_name'].lower() == player_name_lower:
                    print(f"[INFO] Found {player['full_name']} - ID: {player['id']}")
                    return player['id']

            # Try partial match if exact match fails
            for player in self.all_players:
                if player_name_lower in player['full_name'].lower():
                    print(f"[INFO] Found similar: {player['full_name']} - ID: {player['id']}")
                    return player['id']

            print(f"[WARNING] Player '{player_name}' not found")
            return None

        except Exception as e:
            print(f"[ERROR] Error finding player ID: {e}")
            return None

    def get_player_game_logs(
        self,
        player_id: int,
        season: str = "2024-25"
    ) -> pd.DataFrame:
        """
        Get game logs for a player using nba_api

        Args:
            player_id: NBA player ID
            season: Season string (e.g., "2025-26")

        Returns:
            DataFrame with game logs
        """
        try:
            print(f"[INFO] Fetching game logs for player ID {player_id}...")

            # Get player game logs
            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star='Regular Season'
            )

            # Convert to DataFrame
            df = gamelog.get_data_frames()[0]

            if df.empty:
                print(f"[WARNING] No game logs found for player ID {player_id}")
                return pd.DataFrame()

            print(f"[SUCCESS] Retrieved {len(df)} games")
            return df

        except Exception as e:
            print(f"[ERROR] Error fetching game logs: {e}")
            return pd.DataFrame()

    def format_game_for_database(
        self,
        game_row: pd.Series,
        player_name: str,
        team: str,
        position: str
    ) -> Dict:
        """
        Format nba_api game data for our database schema

        Args:
            game_row: Row from nba_api DataFrame
            player_name: Player's name
            team: Player's team abbreviation
            position: Player's position

        Returns:
            Formatted game dictionary
        """
        # Parse matchup to determine home/away and opponent
        matchup = game_row.get('MATCHUP', '')

        # Matchup format: "LAL vs. GSW" (home) or "LAL @ GSW" (away)
        if ' vs. ' in matchup:
            is_home = True
            opponent = matchup.split(' vs. ')[1].strip()
        elif ' @ ' in matchup:
            is_home = False
            opponent = matchup.split(' @ ')[1].strip()
        else:
            is_home = True
            opponent = 'UNK'

        # Parse date (format: "OCT 22, 2024")
        game_date_str = game_row.get('GAME_DATE', '')
        try:
            game_date = datetime.strptime(game_date_str, '%b %d, %Y').strftime('%Y-%m-%d')
        except:
            game_date = game_date_str

        return {
            'player_name': player_name,
            'team': team,
            'position': position,
            'date': game_date,
            'opponent': opponent,
            'is_home': 1 if is_home else 0,
            'points': int(game_row.get('PTS', 0) or 0),
            'rebounds': int(game_row.get('REB', 0) or 0),
            'assists': int(game_row.get('AST', 0) or 0),
            'steals': int(game_row.get('STL', 0) or 0),
            'blocks': int(game_row.get('BLK', 0) or 0),
            'three_pm': int(game_row.get('FG3M', 0) or 0)
        }

    def fetch_player_season(
        self,
        player_name: str,
        team: str,
        position: str,
        season: str = "2025-26"
    ) -> List[Dict]:
        """
        Fetch full season of game logs for a player

        Args:
            player_name: Player's full name
            team: Team abbreviation (ignored - we extract from game data)
            position: Position
            season: Season string (e.g., "2025-26")

        Returns:
            List of formatted game dictionaries
        """
        print(f"\n[INFO] Fetching {season} stats for {player_name}...")

        # Find player ID
        player_id = self.find_player_id(player_name)
        if not player_id:
            return []

        # Respect API rate limits (be nice to NBA servers)
        time.sleep(0.6)

        # Get game logs
        game_logs_df = self.get_player_game_logs(player_id, season)
        if game_logs_df.empty:
            return []

        # Extract current team from most recent game
        if not game_logs_df.empty:
            recent_matchup = game_logs_df.iloc[0]['MATCHUP']
            current_team = recent_matchup.split(' ')[0]
            print(f"[INFO] Current team: {current_team}")
        else:
            current_team = team  # Fallback to provided team

        # Format for our database
        formatted_games = []
        for _, game_row in game_logs_df.iterrows():
            formatted = self.format_game_for_database(game_row, player_name, current_team, position)
            formatted_games.append(formatted)

        return formatted_games


def fetch_all_players_data(output_file: str = "real_player_stats.csv"):
    """
    Fetch real game data for top NBA players from all 30 teams
    """
    # Expanded player list - top 1-2 players from each NBA team
    players_list = [
        # Lakers
        {"name": "LeBron James", "team": "LAL", "position": "SF"},
        {"name": "Anthony Davis", "team": "LAL", "position": "C"},
        {"name": "Austin Reaves", "team": "LAL", "position": "SG"},

        # Warriors
        {"name": "Stephen Curry", "team": "GSW", "position": "PG"},
        {"name": "Andrew Wiggins", "team": "GSW", "position": "SF"},

        # Suns
        {"name": "Kevin Durant", "team": "PHX", "position": "SF"},
        {"name": "Devin Booker", "team": "PHX", "position": "SG"},
        {"name": "Bradley Beal", "team": "PHX", "position": "SG"},

        # Bucks
        {"name": "Giannis Antetokounmpo", "team": "MIL", "position": "PF"},
        {"name": "Damian Lillard", "team": "MIL", "position": "PG"},

        # 76ers
        {"name": "Joel Embiid", "team": "PHI", "position": "C"},
        {"name": "Tyrese Maxey", "team": "PHI", "position": "PG"},

        # Celtics
        {"name": "Jayson Tatum", "team": "BOS", "position": "SF"},
        {"name": "Jaylen Brown", "team": "BOS", "position": "SG"},

        # Mavericks
        {"name": "Luka Dončić", "team": "DAL", "position": "PG"},
        {"name": "Kyrie Irving", "team": "DAL", "position": "PG"},

        # Nuggets
        {"name": "Nikola Jokić", "team": "DEN", "position": "C"},
        {"name": "Jamal Murray", "team": "DEN", "position": "PG"},

        # Thunder
        {"name": "Shai Gilgeous-Alexander", "team": "OKC", "position": "PG"},
        {"name": "Jalen Williams", "team": "OKC", "position": "SF"},

        # Kings
        {"name": "De'Aaron Fox", "team": "SAC", "position": "PG"},
        {"name": "Domantas Sabonis", "team": "SAC", "position": "C"},

        # Cavaliers
        {"name": "Donovan Mitchell", "team": "CLE", "position": "SG"},
        {"name": "Darius Garland", "team": "CLE", "position": "PG"},

        # Clippers
        {"name": "Kawhi Leonard", "team": "LAC", "position": "SF"},
        {"name": "James Harden", "team": "LAC", "position": "PG"},

        # Knicks
        {"name": "Karl-Anthony Towns", "team": "NYK", "position": "C"},
        {"name": "Jalen Brunson", "team": "NYK", "position": "PG"},

        # Grizzlies
        {"name": "Ja Morant", "team": "MEM", "position": "PG"},
        {"name": "Jaren Jackson Jr.", "team": "MEM", "position": "PF"},

        # Hawks
        {"name": "Trae Young", "team": "ATL", "position": "PG"},
        {"name": "Dejounte Murray", "team": "NOP", "position": "PG"},  # Traded to Pelicans

        # Heat
        {"name": "Bam Adebayo", "team": "MIA", "position": "C"},
        {"name": "Tyler Herro", "team": "MIA", "position": "SG"},

        # Timberwolves
        {"name": "Anthony Edwards", "team": "MIN", "position": "SG"},
        {"name": "Rudy Gobert", "team": "MIN", "position": "C"},

        # Pelicans
        {"name": "Zion Williamson", "team": "NOP", "position": "PF"},
        {"name": "Brandon Ingram", "team": "NOP", "position": "SF"},

        # Pacers
        {"name": "Tyrese Haliburton", "team": "IND", "position": "PG"},
        {"name": "Pascal Siakam", "team": "IND", "position": "PF"},

        # Nets
        {"name": "Mikal Bridges", "team": "NYK", "position": "SF"},  # Traded to Knicks
        {"name": "Cam Thomas", "team": "BKN", "position": "SG"},

        # Magic
        {"name": "Paolo Banchero", "team": "ORL", "position": "PF"},
        {"name": "Franz Wagner", "team": "ORL", "position": "SF"},

        # Rockets
        {"name": "Alperen Sengun", "team": "HOU", "position": "C"},
        {"name": "Jalen Green", "team": "HOU", "position": "SG"},

        # Bulls
        {"name": "Zach LaVine", "team": "CHI", "position": "SG"},
        {"name": "Nikola Vučević", "team": "CHI", "position": "C"},

        # Raptors
        {"name": "Scottie Barnes", "team": "TOR", "position": "PF"},
        {"name": "RJ Barrett", "team": "TOR", "position": "SG"},

        # Spurs
        {"name": "Victor Wembanyama", "team": "SAS", "position": "C"},
        {"name": "Devin Vassell", "team": "SAS", "position": "SG"},

        # Trail Blazers
        {"name": "Anfernee Simons", "team": "POR", "position": "PG"},
        {"name": "Jerami Grant", "team": "POR", "position": "PF"},

        # Hornets
        {"name": "LaMelo Ball", "team": "CHA", "position": "PG"},
        {"name": "Brandon Miller", "team": "CHA", "position": "SF"},

        # Pistons
        {"name": "Cade Cunningham", "team": "DET", "position": "PG"},
        {"name": "Jaden Ivey", "team": "DET", "position": "SG"},

        # Wizards
        {"name": "Jordan Poole", "team": "WAS", "position": "PG"},
        {"name": "Kyle Kuzma", "team": "WAS", "position": "PF"},

        # Jazz
        {"name": "Lauri Markkanen", "team": "UTA", "position": "PF"},
        {"name": "Collin Sexton", "team": "UTA", "position": "PG"},
    ]

    fetcher = NBAStatsFetcher()
    all_games = []

    print("=" * 60)
    print("FETCHING REAL NBA GAME DATA FROM 2025-26 SEASON")
    print("=" * 60)

    for idx, player in enumerate(players_list, 1):
        print(f"\n[{idx}/{len(players_list)}] Processing {player['name']}...")

        games = fetcher.fetch_player_season(
            player['name'],
            player['team'],
            player['position'],
            season="2025-26"
        )

        all_games.extend(games)

        # Progress update
        if games:
            print(f"[SUCCESS] Added {len(games)} games for {player['name']}")
        else:
            print(f"[WARNING] No games found for {player['name']}")

        # Be nice to the NBA API (rate limiting)
        time.sleep(0.6)

    # Save to CSV
    if all_games:
        df = pd.DataFrame(all_games)

        # Sort by player name and date
        df = df.sort_values(['player_name', 'date'], ascending=[True, False])

        df.to_csv(output_file, index=False)
        print(f"\n{'=' * 60}")
        print(f"[SUCCESS] Saved {len(all_games)} games to {output_file}")
        print(f"{'=' * 60}")
        print(f"\nBreakdown by player:")
        print(df.groupby('player_name').size().sort_values(ascending=False))
        return df
    else:
        print("\n[ERROR] No game data collected")
        return None


# Test and example usage
if __name__ == "__main__":
    print("NBA Stats Fetcher - Using nba_api")
    print("Fetching real 2025-26 season game logs\n")

    # Fetch all players
    df = fetch_all_players_data("data/real_player_stats.csv")

    if df is not None:
        print("\n" + "=" * 60)
        print("SAMPLE DATA (First 10 games):")
        print("=" * 60)
        print(df.head(10).to_string())
        print(f"\nTotal Games: {len(df)}")
        print(f"Players: {df['player_name'].nunique()}")
        print(f"Date Range: {df['date'].min()} to {df['date'].max()}")
