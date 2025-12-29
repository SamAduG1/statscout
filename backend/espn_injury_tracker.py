"""
ESPN Injury Tracker
Fetches injury data from ESPN's public NBA injury API
More reliable than NBA API for injury status
"""
import requests
from datetime import datetime, timedelta
import time

class ESPNInjuryTracker:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = timedelta(hours=2)  # Refresh every 2 hours
        self.last_fetch = None
        self.espn_base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"

    def get_all_injuries(self):
        """
        Fetch injury data from ESPN team-by-team API
        This queries all 30 NBA teams to get league-wide injuries
        Returns dict: {player_name: {"status": str, "team": str, "injury": str}}
        """
        # Check cache first - CRITICAL: Don't fetch on every call!
        if self.last_fetch is not None:
            time_since_fetch = datetime.now() - self.last_fetch
            if time_since_fetch < self.cache_timeout:
                # Silently use cache - don't spam logs
                return self.cache

        print("[Injury Tracker] Fetching fresh injury data from all 30 NBA teams...")

        # All 30 NBA teams with their ESPN team IDs
        nba_teams = {
            'ATL': 1, 'BOS': 2, 'BKN': 17, 'CHA': 30, 'CHI': 4,
            'CLE': 5, 'DAL': 6, 'DEN': 7, 'DET': 8, 'GSW': 9,
            'HOU': 10, 'IND': 11, 'LAC': 12, 'LAL': 13, 'MEM': 29,
            'MIA': 14, 'MIL': 15, 'MIN': 16, 'NOP': 3, 'NYK': 18,
            'OKC': 25, 'ORL': 19, 'PHI': 20, 'PHX': 21, 'POR': 22,
            'SAC': 23, 'SAS': 24, 'TOR': 28, 'UTA': 26, 'WAS': 27
        }

        injuries = {}

        try:
            # Query each team's roster/injury data
            for team_abbr, team_id in nba_teams.items():
                try:
                    # Use roster endpoint to get all players and their injury status
                    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"
                    response = requests.get(url, timeout=10)

                    if response.status_code != 200:
                        print(f"  [Warning] {team_abbr} API returned {response.status_code}")
                        continue

                    team_data = response.json()

                    # Parse roster for injuries
                    roster = team_data.get('athletes', [])
                    for athlete in roster:
                        # Check if athlete has injury info
                        injuries_list = athlete.get('injuries', [])
                        if injuries_list and len(injuries_list) > 0:
                            # Player is injured - get most recent injury
                            injury = injuries_list[0]

                            player_name = athlete.get('displayName', 'Unknown')
                            status = injury.get('status', 'UNKNOWN')

                            # Normalize status to match our expected values
                            # ESPN uses: "Out", "Day-To-Day", "Questionable", etc.
                            if 'out' in status.lower():
                                status = 'OUT'
                            elif 'questionable' in status.lower():
                                status = 'QUESTIONABLE'
                            elif 'doubtful' in status.lower():
                                status = 'DOUBTFUL'
                            elif 'day-to-day' in status.lower():
                                status = 'DAY-TO-DAY'
                            else:
                                status = status.upper()

                            # Try to get injury type from athlete details (may not be available)
                            injury_type = injury.get('longComment', '') or injury.get('shortComment', '') or 'Injury'

                            injuries[player_name] = {
                                'status': status,
                                'team': team_abbr,
                                'injury': injury_type,
                                'last_updated': datetime.now().isoformat()
                            }
                            print(f"  [Injury] {player_name} ({team_abbr}): {status}")

                    # Small delay to avoid rate limiting
                    time.sleep(0.05)

                except Exception as e:
                    print(f"  [Warning] Error fetching {team_abbr} injuries: {e}")
                    continue  # Skip this team and move to next

        except Exception as e:
            print(f"[Error] Failed to fetch ESPN injury data: {e}")
            return self.cache if self.cache else {}

        # Update cache
        self.cache = injuries
        self.last_fetch = datetime.now()

        print(f"[Injury Tracker] Found {len(injuries)} injured players league-wide")
        return injuries

    def get_player_status(self, player_name):
        """
        Get injury status for a specific player
        Returns dict with status info or None if active
        """
        injuries = self.get_all_injuries()
        return injuries.get(player_name, None)

    def get_batch_status(self, player_names):
        """
        Get injury status for multiple players
        Returns dict: {player_name: status_dict}
        """
        injuries = self.get_all_injuries()

        results = {}
        for player_name in player_names:
            if player_name in injuries:
                results[player_name] = injuries[player_name]
            else:
                results[player_name] = {
                    'status': 'ACTIVE',
                    'team': None,
                    'injury': None
                }

        return results

    def is_player_out(self, player_name):
        """
        Quick check if a player is out
        Returns True if player is OUT, False otherwise
        """
        status = self.get_player_status(player_name)
        if status:
            return status['status'] in ['OUT', 'DOUBTFUL']
        return False

    def clear_cache(self):
        """Force refresh on next call"""
        self.cache = {}
        self.last_fetch = None

    def refresh_nba_data(self):
        """
        Force refresh of injury data (for compatibility with old API)
        """
        self.clear_cache()
        return self.get_all_injuries()

    def set_manual_status(self, player_name, status):
        """
        Placeholder for manual status setting (not supported by ESPN tracker)
        This would require a separate manual override system
        """
        print(f"[Warning] Manual status setting not supported by ESPN tracker")
        print(f"  Player: {player_name}, Status: {status}")
        # Could implement a manual override dict here if needed
        pass


if __name__ == "__main__":
    # Test the injury tracker
    tracker = ESPNInjuryTracker()

    print("\n" + "=" * 60)
    print("ESPN INJURY TRACKER TEST")
    print("=" * 60)

    injuries = tracker.get_all_injuries()

    print(f"\nTotal injured players: {len(injuries)}")
    print("\nAll current injuries:")
    for player, info in sorted(injuries.items()):
        print(f"  {player:30} ({info['team']:3}) - {info['status']:12} - {info['injury']}")

    # Test specific player
    print("\n" + "=" * 60)
    test_player = "Jalen Brunson"
    status = tracker.get_player_status(test_player)
    if status:
        print(f"{test_player} Status: {status}")
    else:
        print(f"{test_player}: ACTIVE (No injury report)")
