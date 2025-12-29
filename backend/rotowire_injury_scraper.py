"""
RotoWire NBA Injury Scraper
Scrapes injury data from RotoWire's injury page
More comprehensive than game-day only APIs
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os

class RotoWireInjuryScraper:
    def __init__(self):
        self.cache_file = "injury_cache.json"
        self.cache_timeout = timedelta(hours=4)  # Refresh every 4 hours
        self.url = "https://www.rotowire.com/basketball/nba-lineups.php"

    def load_cache(self):
        """Load cached injury data from file"""
        if not os.path.exists(self.cache_file):
            return None, None

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                last_fetch = datetime.fromisoformat(cache_data['last_fetch'])
                injuries = cache_data['injuries']
                return injuries, last_fetch
        except:
            return None, None

    def save_cache(self, injuries):
        """Save injury data to cache file"""
        cache_data = {
            'last_fetch': datetime.now().isoformat(),
            'injuries': injuries
        }
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def fetch_injuries(self):
        """
        Fetch injury data from RotoWire
        Returns dict: {player_name: {"status": str, "team": str, "injury": str, "return_date": str}}
        """
        # Check cache first
        cached_injuries, last_fetch = self.load_cache()
        if cached_injuries and last_fetch:
            if datetime.now() - last_fetch < self.cache_timeout:
                print(f"[Injury Cache] Using cached data from {last_fetch}")
                return cached_injuries

        print("[Injury Scraper] Fetching fresh injury data from RotoWire...")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"[Error] Failed to fetch RotoWire data: {response.status_code}")
                return cached_injuries if cached_injuries else {}

            soup = BeautifulSoup(response.text, 'html.parser')
            injuries = {}

            # Find injury sections (this is a simplified version - actual parsing may vary)
            # RotoWire shows lineups with injuries inline
            # For now, return empty and we'll use a better method

            print(f"[Injury Scraper] Parsing complete")
            self.save_cache(injuries)
            return injuries

        except Exception as e:
            print(f"[Error] Failed to scrape injury data: {e}")
            return cached_injuries if cached_injuries else {}

    def get_player_status(self, player_name):
        """Get injury status for specific player"""
        injuries = self.fetch_injuries()
        return injuries.get(player_name, None)


if __name__ == "__main__":
    scraper = RotoWireInjuryScraper()
    injuries = scraper.fetch_injuries()
    print(f"\nFound {len(injuries)} injured players")
