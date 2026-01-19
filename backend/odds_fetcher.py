"""
Vegas Odds Fetcher using BALLDONTLIE API
Fetches real-time player prop odds from major sportsbooks
"""

import os
import requests
from datetime import date, datetime
from typing import List, Dict, Optional, Any
import time


class VegasOddsFetcher:
    """Fetch player prop odds from BALLDONTLIE API"""

    def __init__(self, api_key: str = None):
        """
        Initialize the odds fetcher

        Args:
            api_key: BALLDONTLIE API key (if None, uses BALLDONTLIE_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('BALLDONTLIE_API_KEY')
        self.base_url = "https://api.balldontlie.io"
        self.headers = {"Authorization": self.api_key} if self.api_key else {}

        # Rate limiting (free tier: 5 requests/minute)
        self.min_request_interval = 12  # 12 seconds = 5 requests/minute

        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting to stay within API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"  [Rate Limit] Sleeping {sleep_time:.1f}s...")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_todays_games(self) -> List[Dict[str, Any]]:
        """
        Get all NBA games happening today

        Returns:
            List of game dictionaries with id, home_team, visitor_team, etc.
        """
        if not self.api_key:
            print("[ERROR] No BALLDONTLIE_API_KEY found in environment")
            return []

        try:
            self._rate_limit()

            today = date.today().isoformat()
            url = f"{self.base_url}/nba/v1/games"

            response = requests.get(
                url,
                headers=self.headers,
                params={"dates[]": today},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                games = data.get('data', [])
                print(f"[INFO] Found {len(games)} games today ({today})")
                return games
            else:
                print(f"[ERROR] Failed to fetch games: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"[ERROR] Exception fetching games: {e}")
            return []

    def get_player_props_for_game(
        self,
        game_id: int,
        player_name: str = None,
        prop_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get player props for a specific game

        Args:
            game_id: NBA game ID
            player_name: Filter by player name (optional)
            prop_type: Filter by prop type like 'points', 'rebounds', 'assists' (optional)

        Returns:
            List of player prop dictionaries
        """
        if not self.api_key:
            print("[ERROR] No BALLDONTLIE_API_KEY found in environment")
            return []

        try:
            self._rate_limit()

            url = f"{self.base_url}/v2/odds/player_props"

            params = {"game_id": game_id}
            if prop_type:
                params["prop_type"] = prop_type

            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                props = data.get('data', [])

                # Filter by player name if provided
                if player_name:
                    props = [p for p in props if p.get('player', {}).get('name', '').lower() == player_name.lower()]

                print(f"[INFO] Found {len(props)} player props for game {game_id}")
                return props
            else:
                print(f"[ERROR] Failed to fetch props: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"[ERROR] Exception fetching props: {e}")
            return []

    def get_vegas_line_for_player(
        self,
        player_name: str,
        stat_type: str,
        prefer_book: str = "fanduel"
    ) -> Optional[Dict[str, Any]]:
        """
        Get Vegas line for a specific player's stat

        Args:
            player_name: Player's full name (e.g., "LeBron James")
            stat_type: Stat type ('points', 'rebounds', 'assists', 'three_pm')
            prefer_book: Preferred sportsbook (default: 'fanduel')

        Returns:
            Dictionary with line, over_odds, under_odds, and sportsbook
        """
        # Map our stat types to BALLDONTLIE prop types
        stat_map = {
            'points': 'points',
            'rebounds': 'rebounds',
            'assists': 'assists',
            'three_pm': 'threes',
            '3pm': 'threes',
            'steals': 'steals',
            'blocks': 'blocks',
            'pra': 'points_rebounds_assists',
            'pa': 'points_assists',
            'pr': 'points_rebounds'
        }

        prop_type = stat_map.get(stat_type.lower())
        if not prop_type:
            print(f"[WARNING] Unknown stat type: {stat_type}")
            return None

        # Get today's games
        games = self.get_todays_games()
        if not games:
            print(f"[INFO] No games today or couldn't fetch games")
            return None

        # Search through today's games for this player
        for game in games:
            props = self.get_player_props_for_game(
                game['id'],
                player_name=player_name,
                prop_type=prop_type
            )

            if not props:
                continue

            # Try to find preferred sportsbook first
            preferred = [p for p in props if p.get('vendor', '').lower() == prefer_book.lower()]
            if preferred:
                return self._format_prop(preferred[0])

            # Fallback to first available book
            if props:
                return self._format_prop(props[0])

        print(f"[INFO] No Vegas line found for {player_name} {stat_type}")
        return None

    def _format_prop(self, prop: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format raw prop data into clean structure

        Args:
            prop: Raw prop dictionary from API

        Returns:
            Formatted prop with line, odds, and metadata
        """
        market = prop.get('market', {})

        return {
            'line': prop.get('line_value'),
            'over_odds': market.get('over_odds'),
            'under_odds': market.get('under_odds'),
            'sportsbook': prop.get('vendor', 'Unknown'),
            'updated_at': prop.get('updated_at'),
            'prop_type': prop.get('prop_type')
        }


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("VEGAS ODDS FETCHER TEST")
    print("=" * 60)

    fetcher = VegasOddsFetcher()

    # Test 1: Get today's games
    print("\n[TEST 1] Fetching today's games...")
    games = fetcher.get_todays_games()

    if games:
        print(f"\nFound {len(games)} games:")
        for game in games[:3]:  # Show first 3
            home = game.get('home_team', {}).get('full_name', 'Unknown')
            visitor = game.get('visitor_team', {}).get('full_name', 'Unknown')
            print(f"  - Game {game['id']}: {visitor} @ {home}")

        # Test 2: Get props for first game
        if games:
            print(f"\n[TEST 2] Fetching player props for game {games[0]['id']}...")
            props = fetcher.get_player_props_for_game(games[0]['id'])

            if props:
                print(f"\nFound {len(props)} player props:")
                for prop in props[:5]:  # Show first 5
                    player = prop.get('player', {}).get('name', 'Unknown')
                    line = prop.get('line_value')
                    prop_type = prop.get('prop_type')
                    vendor = prop.get('vendor', 'Unknown')
                    print(f"  - {player} {prop_type} {line} ({vendor})")
            else:
                print("No props found (likely game hasn't posted lines yet)")

    else:
        print("\nNo games today or API key not configured")
        print("Set BALLDONTLIE_API_KEY environment variable to test")
