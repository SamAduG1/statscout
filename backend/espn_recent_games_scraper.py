"""
ESPN Recent Games Scraper
Supplements nba_api by scraping very recent games (last 30 days) from ESPN
Used as a fallback when nba_api data lags behind
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional


class ESPNRecentGamesScraper:
    """Scrape recent NBA games from ESPN to supplement nba_api data"""

    def __init__(self):
        """Initialize the scraper"""
        self.base_url = "https://www.espn.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # ESPN team ID mappings
        self.team_ids = {
            'LAL': 13, 'GSW': 9, 'BOS': 2, 'MIL': 15, 'DAL': 6, 'DEN': 7,
            'PHX': 21, 'PHI': 20, 'MIA': 14, 'CHI': 4, 'BKN': 17, 'MIN': 16,
            'SAC': 23, 'POR': 22, 'LAC': 12, 'UTA': 26, 'MEM': 29, 'NOP': 3,
            'SAS': 24, 'HOU': 10, 'OKC': 25, 'ATL': 1, 'CLE': 5, 'IND': 11,
            'DET': 8, 'TOR': 28, 'WAS': 27, 'CHA': 30, 'ORL': 19, 'NYK': 18
        }

    def get_player_recent_games(
        self,
        player_name: str,
        team: str,
        days_back: int = 30
    ) -> List[Dict]:
        """
        Fetch recent games for a player from ESPN

        Args:
            player_name: Player's full name
            team: Team abbreviation (e.g., 'LAL')
            days_back: How many days back to look (default 30)

        Returns:
            List of game dictionaries with stats
        """
        print(f"[ESPN] Fetching recent games for {player_name} ({team})")

        # For now, return empty list - we'll implement full scraping if needed
        # This is a placeholder to get the structure in place
        # Full implementation would require:
        # 1. ESPN player ID lookup
        # 2. Parse ESPN game log page
        # 3. Extract box score data

        return []

    def get_team_recent_games(
        self,
        team: str,
        days_back: int = 30
    ) -> List[Dict]:
        """
        Get recent games for a team to find player stats

        Args:
            team: Team abbreviation
            days_back: Days to look back

        Returns:
            List of game data with box scores
        """
        if team not in self.team_ids:
            print(f"[ESPN] Unknown team: {team}")
            return []

        team_id = self.team_ids[team]
        games = []

        try:
            # Get team schedule
            url = f"{self.base_url}/nba/team/schedule/_/name/{team.lower()}/id/{team_id}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                print(f"[ESPN] Failed to fetch schedule for {team}")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')

            # Parse schedule table for recent games
            # This would need full implementation based on ESPN's HTML structure

            print(f"[ESPN] Found {len(games)} recent games for {team}")
            return games

        except Exception as e:
            print(f"[ESPN] Error fetching team games: {e}")
            return []


# For future implementation - ESPN API approach (faster than scraping)
class ESPNAPIClient:
    """
    Alternative: Use ESPN's unofficial API endpoints
    These are more reliable than scraping HTML
    """

    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

    def get_scoreboard(self, date_str: str) -> Dict:
        """
        Get scoreboard for a specific date

        Args:
            date_str: Date in YYYYMMDD format

        Returns:
            Scoreboard data with games
        """
        try:
            url = f"{self.base_url}/scoreboard?dates={date_str}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                return response.json()
            return {}

        except Exception as e:
            print(f"[ESPN API] Error: {e}")
            return {}

    def get_recent_scoreboards(self, days_back: int = 7) -> List[Dict]:
        """Get scoreboards for last N days"""
        scoreboards = []
        today = datetime.now()

        for i in range(days_back):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y%m%d")

            scoreboard = self.get_scoreboard(date_str)
            if scoreboard and 'events' in scoreboard:
                scoreboards.append({
                    'date': date_str,
                    'games': scoreboard['events']
                })

            time.sleep(0.5)  # Rate limiting

        return scoreboards


    def get_game_box_score(self, game_id: str) -> Dict:
        """
        Get detailed box score for a specific game

        Args:
            game_id: ESPN game ID

        Returns:
            Box score data
        """
        try:
            url = f"{self.base_url}/summary?event={game_id}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                return response.json()
            return {}

        except Exception as e:
            print(f"[ESPN API] Error fetching box score: {e}")
            return {}

    def get_player_stats_from_date(self, date_str: str) -> List[Dict]:
        """
        Get all player stats from games on a specific date

        Args:
            date_str: Date in YYYYMMDD format

        Returns:
            List of player game stats
        """
        try:
            # First get the scoreboard to find games
            scoreboard = self.get_scoreboard(date_str)

            if not scoreboard or 'events' not in scoreboard:
                return []

            all_player_stats = []
            games = scoreboard['events']

            print(f"[ESPN] Fetching box scores for {len(games)} games on {date_str}...")

            for event in games:
                game_id = event.get('id', '')
                if not game_id:
                    continue

                # Get detailed box score
                box_score = self.get_game_box_score(game_id)
                time.sleep(0.5)  # Rate limiting

                if not box_score:
                    continue

                # Extract player stats from box score
                box_score_data = box_score.get('boxscore', {})
                players = box_score_data.get('players', [])

                # Find opponent teams from header
                header = box_score.get('header', {})
                competitions = header.get('competitions', [{}])
                if not competitions:
                    continue

                competitors = competitions[0].get('competitors', [])
                home_team = next((c['team']['abbreviation'] for c in competitors if c.get('homeAway') == 'home'), '')
                away_team = next((c['team']['abbreviation'] for c in competitors if c.get('homeAway') == 'away'), '')

                for team_data in players:
                    team = team_data.get('team', {})
                    team_abbrev = team.get('abbreviation', '')

                    is_home = team_abbrev == home_team
                    opponent = away_team if is_home else home_team

                    # Get the statistics section
                    statistics = team_data.get('statistics', [])
                    if not statistics:
                        continue

                    stat_section = statistics[0]  # First section has the player stats

                    # Get stat labels to map indices
                    labels = stat_section.get('labels', [])
                    # Create index map
                    label_map = {label: idx for idx, label in enumerate(labels)}

                    # Get indices for our stats
                    pts_idx = label_map.get('PTS', 1)
                    reb_idx = label_map.get('REB', 5)
                    ast_idx = label_map.get('AST', 6)
                    stl_idx = label_map.get('STL', 8)
                    blk_idx = label_map.get('BLK', 9)
                    three_pt_idx = label_map.get('3PT', 3)

                    # Parse each player
                    athletes = stat_section.get('athletes', [])

                    for athlete_data in athletes:
                        athlete = athlete_data.get('athlete', {})
                        player_name = athlete.get('displayName', '')

                        # Skip if player didn't play
                        if athlete_data.get('didNotPlay'):
                            continue

                        # Get the stats array
                        stats = athlete_data.get('stats', [])
                        if not stats:
                            continue

                        # ESPN stats format: ['MIN', 'PTS', 'FG', '3PT', 'FT', 'REB', 'AST', 'TO', 'STL', 'BLK', ...]
                        try:
                            points = int(stats[pts_idx]) if pts_idx < len(stats) and stats[pts_idx] != '--' else 0
                            rebounds = int(stats[reb_idx]) if reb_idx < len(stats) and stats[reb_idx] != '--' else 0
                            assists = int(stats[ast_idx]) if ast_idx < len(stats) and stats[ast_idx] != '--' else 0
                            steals = int(stats[stl_idx]) if stl_idx < len(stats) and stats[stl_idx] != '--' else 0
                            blocks = int(stats[blk_idx]) if blk_idx < len(stats) and stats[blk_idx] != '--' else 0

                            # 3PM - extract from 3PT stat (format: "made-attempted")
                            three_pm = 0
                            if three_pt_idx < len(stats) and stats[three_pt_idx] != '--':
                                three_pt_str = str(stats[three_pt_idx])
                                if '-' in three_pt_str:
                                    three_pm = int(three_pt_str.split('-')[0])

                        except (ValueError, IndexError) as e:
                            print(f"[ESPN] Error parsing stats for {player_name}: {e}")
                            continue

                        # Only add if player actually played
                        if points > 0 or rebounds > 0 or assists > 0:
                            all_player_stats.append({
                                'player_name': player_name,
                                'team': team_abbrev,
                                'date': datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d"),
                                'opponent': opponent,
                                'is_home': is_home,
                                'points': points,
                                'rebounds': rebounds,
                                'assists': assists,
                                'steals': steals,
                                'blocks': blocks,
                                'three_pm': three_pm
                            })

            return all_player_stats

        except Exception as e:
            print(f"[ESPN API] Error parsing games: {e}")
            import traceback
            traceback.print_exc()
            return []


if __name__ == "__main__":
    # Test ESPN API
    print("Testing ESPN API...")
    api = ESPNAPIClient()

    # Get today's games
    today = datetime.now().strftime("%Y%m%d")
    scoreboard = api.get_scoreboard(today)

    if scoreboard and 'events' in scoreboard:
        print(f"\n[OK] Found {len(scoreboard['events'])} games for {today}")
        for event in scoreboard['events'][:3]:
            home = event['competitions'][0]['competitors'][0]['team']['abbreviation']
            away = event['competitions'][0]['competitors'][1]['team']['abbreviation']
            print(f"  {away} @ {home}")
    else:
        print("[WARN] No games found")

    # Test recent scoreboards
    print("\n\nTesting recent scoreboards (last 7 days)...")
    recent = api.get_recent_scoreboards(days_back=7)
    print(f"[OK] Retrieved {len(recent)} days of scoreboards")
    for sb in recent:
        print(f"  {sb['date']}: {len(sb['games'])} games")

    # Test player stats extraction
    print("\n\nTesting player stats extraction...")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    player_stats = api.get_player_stats_from_date(yesterday)
    print(f"[OK] Found {len(player_stats)} player performances from {yesterday}")
    if player_stats:
        print("\nSample player stats (first 10):")
        for stat in player_stats[:10]:
            print(f"  {stat['player_name']} ({stat['team']}): {stat['points']} pts, {stat['rebounds']} reb, {stat['assists']} ast")
