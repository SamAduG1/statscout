"""
NBA Schedule Fetcher
Gets real upcoming games and matchups from The Odds API
"""
import sys
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import pytz

# Force UTF-8 output
if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

# Import odds API client
from odds_api import OddsAPIClient

# Team name to abbreviation mapping (The Odds API uses full names)
TEAM_ABBREV_MAP = {
    "Los Angeles Lakers": "LAL",
    "Golden State Warriors": "GSW",
    "Boston Celtics": "BOS",
    "Milwaukee Bucks": "MIL",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Phoenix Suns": "PHX",
    "Philadelphia 76ers": "PHI",
    "Miami Heat": "MIA",
    "Chicago Bulls": "CHI",
    "Brooklyn Nets": "BKN",
    "Minnesota Timberwolves": "MIN",
    "Sacramento Kings": "SAC",
    "Portland Trail Blazers": "POR",
    "LA Clippers": "LAC",
    "Los Angeles Clippers": "LAC",  # The Odds API uses full name
    "Utah Jazz": "UTA",
    "Memphis Grizzlies": "MEM",
    "New Orleans Pelicans": "NOP",
    "San Antonio Spurs": "SAS",
    "Houston Rockets": "HOU",
    "Oklahoma City Thunder": "OKC",
    "Atlanta Hawks": "ATL",
    "Cleveland Cavaliers": "CLE",
    "Indiana Pacers": "IND",
    "Detroit Pistons": "DET",
    "Toronto Raptors": "TOR",
    "Washington Wizards": "WAS",
    "Charlotte Hornets": "CHA",
    "Orlando Magic": "ORL",
    "New York Knicks": "NYK"
}


class NBAScheduleFetcher:
    """Fetches upcoming NBA games and schedules using The Odds API"""

    def __init__(self):
        """Initialize the schedule fetcher"""
        self.games_cache = []
        self.cache_timestamp = None
        self.cache_duration = 3600  # Cache for 1 hour
        self.odds_client = OddsAPIClient()

    def _convert_team_name_to_abbrev(self, full_name: str) -> str:
        """Convert full team name to abbreviation"""
        return TEAM_ABBREV_MAP.get(full_name, full_name)

    def get_upcoming_games(self, refresh_cache: bool = False) -> List[Dict]:
        """
        Get upcoming NBA games from The Odds API

        Args:
            refresh_cache: Force refresh the cache

        Returns:
            List of game dictionaries with matchup info
        """
        # Check cache
        current_time = time.time()
        if (not refresh_cache and
            self.cache_timestamp and
            self.games_cache and
            (current_time - self.cache_timestamp) < self.cache_duration):
            return self.games_cache

        try:
            # Get events from The Odds API
            events_response = self.odds_client.get_events()

            if not events_response.get('success'):
                print(f"[ERROR] Failed to fetch events: {events_response.get('error')}")
                return self.games_cache  # Return cached data on error

            events = events_response.get('data', [])
            games = []

            for event in events:
                home_team_full = event.get('home_team', '')
                away_team_full = event.get('away_team', '')

                # Convert to abbreviations
                home_abbrev = self._convert_team_name_to_abbrev(home_team_full)
                away_abbrev = self._convert_team_name_to_abbrev(away_team_full)

                # Parse game time and convert to Eastern Time
                commence_time = event.get('commence_time', '')
                try:
                    game_datetime = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                    # Convert to Eastern Time
                    et_tz = pytz.timezone('America/New_York')
                    game_datetime_et = game_datetime.astimezone(et_tz)
                    game_date_str = game_datetime_et.strftime("%b %d, %Y")
                    game_time_str = game_datetime_et.strftime("%I:%M %p ET")
                except:
                    game_date_str = "TBD"
                    game_time_str = "TBD"

                game_info = {
                    "home_team": home_abbrev,
                    "away_team": away_abbrev,
                    "home_team_full": home_team_full,
                    "away_team_full": away_team_full,
                    "game_date": game_date_str,
                    "game_time": game_time_str,
                    "game_id": event.get('id', ''),
                    "commence_time": commence_time
                }

                games.append(game_info)

            # Sort by commence time
            games.sort(key=lambda x: x.get('commence_time', ''))

            # Update cache
            self.games_cache = games
            self.cache_timestamp = current_time

            return games

        except Exception as e:
            print(f"[ERROR] Failed to fetch upcoming games: {e}")
            return self.games_cache  # Return cached data on error

    def get_player_next_game(self, player_team: str) -> Optional[Dict]:
        """
        Get the next game for a player's team

        Args:
            player_team: Player's team abbreviation (e.g., 'LAL')

        Returns:
            Dictionary with game info or None if no game found
        """
        games = self.get_upcoming_games()

        # Find the next game for this team (games are sorted by time)
        for game in games:
            if game['home_team'] == player_team:
                return {
                    "opponent": game['away_team'],
                    "is_home": True,
                    "game_date": game['game_date'],
                    "game_time": game['game_time']
                }
            elif game['away_team'] == player_team:
                return {
                    "opponent": game['home_team'],
                    "is_home": False,
                    "game_date": game['game_date'],
                    "game_time": game['game_time']
                }

        # No upcoming game found
        return None

    def get_all_teams_with_upcoming_games(self) -> List[str]:
        """
        Get list of all team abbreviations with upcoming games

        Returns:
            List of team abbreviations
        """
        games = self.get_upcoming_games()
        teams = set()

        for game in games:
            teams.add(game['home_team'])
            teams.add(game['away_team'])

        return list(teams)


# Test and example usage
if __name__ == "__main__":
    fetcher = NBAScheduleFetcher()

    print("=" * 60)
    print("NBA SCHEDULE FETCHER - TESTING")
    print("=" * 60)

    # Get upcoming games
    print("\nFetching upcoming games...")
    games = fetcher.get_upcoming_games()

    print(f"\nFound {len(games)} upcoming games:\n")

    for idx, game in enumerate(games, 1):
        print(f"{idx}. {game['away_team']} @ {game['home_team']}")
        print(f"   Time: {game['game_date']} at {game['game_time']}")
        print()

    # Test getting a specific team's next game
    if games:
        test_team = games[0]['home_team']
        print(f"\nTesting: Getting next game for {test_team}...")
        next_game = fetcher.get_player_next_game(test_team)

        if next_game:
            print(f"  Opponent: {next_game['opponent']}")
            print(f"  Home/Away: {'Home' if next_game['is_home'] else 'Away'}")
            print(f"  Date: {next_game['game_date']}")
            print(f"  Time: {next_game['game_time']}")
        else:
            print(f"  No game found for {test_team}")

    # Test Charlotte Hornets specifically
    print("\n\nTesting: Getting next game for Charlotte Hornets (CHA)...")
    cha_game = fetcher.get_player_next_game("CHA")
    if cha_game:
        print(f"  Opponent: {cha_game['opponent']}")
        print(f"  Home/Away: {'Home' if cha_game['is_home'] else 'Away'}")
        print(f"  Date: {cha_game['game_date']}")
        print(f"  Time: {cha_game['game_time']}")
    else:
        print(f"  No upcoming game found for CHA")

    # Get all teams with upcoming games
    teams = fetcher.get_all_teams_with_upcoming_games()
    print(f"\n\nTeams with upcoming games ({len(teams)}):")
    print(", ".join(sorted(teams)))

    print("\n" + "=" * 60)
