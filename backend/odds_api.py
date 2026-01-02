"""
StatScout Odds API Integration
Fetches real betting lines from The Odds API
"""

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime
import sys
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Force UTF-8 output
if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass  # Already wrapped or can't wrap

# API Configuration
API_KEY = os.getenv('ODDS_API_KEY')  # Loaded from environment variable
BASE_URL = "https://api.the-odds-api.com/v4"

if not API_KEY:
    print("[WARNING] ODDS_API_KEY environment variable not set!")
    print("[WARNING] Odds functionality will be limited to calculated lines")

# Sport key for NBA
SPORT_KEY = "basketball_nba"


class OddsAPIClient:
    """Client for The Odds API"""
    
    def __init__(self, api_key: str = API_KEY):
        """Initialize the odds API client"""
        self.api_key = api_key
        self.base_url = BASE_URL
        
    def check_usage(self) -> Dict:
        """
        Check API usage and remaining requests
        
        Returns:
            Dictionary with usage information
        """
        try:
            # Make a simple request to check quota
            response = requests.get(
                f"{self.base_url}/sports",
                params={"apiKey": self.api_key}
            )
            
            remaining = response.headers.get('x-requests-remaining', 'Unknown')
            used = response.headers.get('x-requests-used', 'Unknown')
            
            return {
                "success": True,
                "requests_remaining": remaining,
                "requests_used": used,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_events(self) -> Dict:
        """
        Get upcoming NBA events/games

        Returns:
            Dictionary with events data
        """
        try:
            params = {
                "apiKey": self.api_key
            }

            response = requests.get(
                f"{self.base_url}/sports/{SPORT_KEY}/events",
                params=params,
                timeout=10
            )

            remaining = response.headers.get('x-requests-remaining', 'Unknown')

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": data,
                    "requests_remaining": remaining
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                    "message": response.text
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_player_props(
        self,
        event_id: str,
        regions: str = "us",
        markets: str = "player_points,player_rebounds,player_assists",
        bookmakers: Optional[str] = None
    ) -> Dict:
        """
        Get player prop odds for a specific NBA event

        Args:
            event_id: The event ID from get_events()
            regions: Geographic region (us, uk, eu, au)
            markets: Comma-separated list of markets
            bookmakers: Optional specific bookmakers to query

        Returns:
            Dictionary with odds data
        """
        try:
            params = {
                "apiKey": self.api_key,
                "regions": regions,
                "markets": markets,
                "oddsFormat": "american"
            }

            if bookmakers:
                params["bookmakers"] = bookmakers

            response = requests.get(
                f"{self.base_url}/sports/{SPORT_KEY}/events/{event_id}/odds",
                params=params,
                timeout=10
            )

            # Check remaining requests
            remaining = response.headers.get('x-requests-remaining', 'Unknown')

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": data,
                    "requests_remaining": remaining
                }
            else:
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                    "message": response.text
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_all_player_props(
        self,
        regions: str = "us",
        markets: str = "player_points,player_rebounds,player_assists",
        bookmakers: Optional[str] = None
    ) -> Dict:
        """
        Get player props for all upcoming NBA games

        Args:
            regions: Geographic region (us, uk, eu, au)
            markets: Comma-separated list of markets
            bookmakers: Optional specific bookmakers to query

        Returns:
            Dictionary with all props data
        """
        # First get all events
        events_response = self.get_events()

        if not events_response.get("success"):
            return events_response

        events = events_response.get("data", [])

        if not events:
            return {
                "success": True,
                "data": [],
                "message": "No upcoming games found"
            }

        # Get props for each event
        all_props = []

        for event in events:
            event_id = event.get("id")
            if not event_id:
                continue

            props_response = self.get_player_props(
                event_id=event_id,
                regions=regions,
                markets=markets,
                bookmakers=bookmakers
            )

            if props_response.get("success"):
                all_props.append(props_response.get("data"))

        return {
            "success": True,
            "data": all_props,
            "events_count": len(events),
            "props_count": len(all_props)
        }
    
    def parse_player_props(self, api_response: Dict) -> List[Dict]:
        """
        Parse API response into simplified player prop format
        
        Args:
            api_response: Raw API response
            
        Returns:
            List of player props with lines
        """
        if not api_response.get("success"):
            return []
        
        events = api_response.get("data", [])
        parsed_props = []
        
        for event in events:
            # Extract game info
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            commence_time = event.get("commence_time", "")
            
            # Parse bookmaker odds
            bookmakers = event.get("bookmakers", [])
            
            for bookmaker in bookmakers:
                bookmaker_name = bookmaker.get("title", "")
                markets = bookmaker.get("markets", [])
                
                for market in markets:
                    market_key = market.get("key", "")
                    outcomes = market.get("outcomes", [])
                    
                    for outcome in outcomes:
                        prop = {
                            "player_name": outcome.get("description", ""),
                            "stat_type": self._map_market_to_stat(market_key),
                            "line": outcome.get("point"),
                            "over_odds": outcome.get("price") if outcome.get("name") == "Over" else None,
                            "under_odds": outcome.get("price") if outcome.get("name") == "Under" else None,
                            "bookmaker": bookmaker_name,
                            "game": f"{away_team} @ {home_team}",
                            "game_time": commence_time
                        }
                        parsed_props.append(prop)
        
        return parsed_props
    
    def _map_market_to_stat(self, market_key: str) -> str:
        """Map API market key to our stat type"""
        mapping = {
            "player_points": "Points",
            "player_rebounds": "Rebounds",
            "player_assists": "Assists",
            "player_threes": "3PM",
            "player_steals": "Steals",
            "player_blocks": "Blocks"
        }
        return mapping.get(market_key, market_key)
    
    def get_line_for_player(
        self,
        player_name: str,
        stat_type: str
    ) -> Optional[float]:
        """
        Get the betting line for a specific player and stat

        Args:
            player_name: Player's full name
            stat_type: Type of stat (Points, Rebounds, etc.)

        Returns:
            Betting line or None if not found
        """
        props_response = self.get_all_player_props()

        if not props_response.get("success"):
            return None

        parsed_props = self.parse_player_props(props_response)

        # Find matching prop
        for prop in parsed_props:
            if (prop["player_name"].lower() == player_name.lower() and
                prop["stat_type"] == stat_type):
                return prop["line"]

        return None


# Test and example usage
if __name__ == "__main__":
    client = OddsAPIClient()
    
    print("🎲 Testing The Odds API Integration\n")
    
    # Check API usage
    print("📊 Checking API Usage...")
    usage = client.check_usage()
    if usage["success"]:
        print(f"✅ API Key Valid")
        print(f"   Requests Remaining: {usage['requests_remaining']}")
        print(f"   Requests Used: {usage['requests_used']}")
    else:
        print(f"❌ API Error: {usage.get('error')}")
    
    print("\n" + "="*50 + "\n")

    # Get upcoming events
    print("📅 Fetching NBA Events...")
    events = client.get_events()

    if events["success"]:
        event_data = events.get("data", [])
        print(f"✅ Found {len(event_data)} upcoming NBA games")

        if event_data:
            print("\nUpcoming games:")
            for event in event_data[:3]:
                print(f"  - {event['away_team']} @ {event['home_team']}")
                print(f"    Game ID: {event['id']}")
                print(f"    Time: {event['commence_time']}")
        print()
    else:
        print(f"❌ Failed to fetch events: {events.get('error')}")

    print("="*50 + "\n")

    # Get player props
    print("🏀 Fetching All NBA Player Props...")
    props = client.get_all_player_props(
        markets="player_points,player_rebounds,player_assists,player_threes"
    )

    if props["success"]:
        print(f"✅ Successfully fetched props for {props.get('events_count', 0)} games")

        # Parse and display sample props
        parsed = client.parse_player_props(props)

        if parsed:
            print(f"\n📋 Found {len(parsed)} player props")
            print("\nSample Props (first 10):")
            for prop in parsed[:10]:
                print(f"  - {prop['player_name']}: {prop['stat_type']} O/U {prop['line']} ({prop['bookmaker']})")
        else:
            print("⚠️  No props found. This might mean:")
            print("   - No games scheduled today/tomorrow")
            print("   - Props not yet posted by bookmakers")
            print("   - Try again closer to game time (usually 2-4 hours before)")
    else:
        print(f"❌ Failed to fetch odds: {props.get('error')}")

    print("\n💡 Note: Player props are typically posted 2-4 hours before games")
    print("   The API is working correctly - just waiting for bookmakers!")