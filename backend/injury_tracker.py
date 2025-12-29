"""
Injury and Player Status Tracker
Uses NBA API to track inactive players and player status
"""
from datetime import datetime, timedelta
from nba_api.stats.endpoints import LeagueGameFinder
from nba_api.stats.static import players as nba_players
import time

class InjuryTracker:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = timedelta(hours=1)  # Refresh every hour
        self.last_fetch = None

    def get_inactive_players_for_today(self):
        """
        Get list of inactive players for today's games
        Returns dict: {player_name: {"status": "OUT", "last_updated": datetime}}

        NOTE: This method is disabled by default to avoid slow API calls on every request.
        Use refresh_nba_data() explicitly to fetch inactive player data.
        """
        # Check cache
        if self.cache and self.last_fetch:
            if datetime.now() - self.last_fetch < self.cache_timeout:
                return self.cache

        # Return empty dict by default - use manual overrides or call refresh explicitly
        return {}

    def is_player_inactive(self, player_name):
        """
        Check if a specific player is inactive
        Returns: {"is_inactive": bool, "status": str or None}
        """
        inactive_players = self.get_inactive_players_for_today()

        if player_name in inactive_players:
            return {
                "is_inactive": True,
                "status": inactive_players[player_name]["status"]
            }

        return {
            "is_inactive": False,
            "status": None
        }

    def get_player_status_batch(self, player_names):
        """
        Get status for multiple players at once
        Returns dict: {player_name: {"is_inactive": bool, "status": str or None}}
        """
        inactive_players = self.get_inactive_players_for_today()

        results = {}
        for player_name in player_names:
            if player_name in inactive_players:
                results[player_name] = {
                    "is_inactive": True,
                    "status": inactive_players[player_name]["status"]
                }
            else:
                results[player_name] = {
                    "is_inactive": False,
                    "status": "ACTIVE"
                }

        return results

    def clear_cache(self):
        """Clear the injury cache (for testing or manual refresh)"""
        self.cache = {}
        self.last_fetch = None


# Manual override system for testing/demo purposes
class ManualInjuryOverride:
    """
    Allows manual setting of player injury status
    Useful for testing and demos until we have a better data source
    """
    def __init__(self):
        self.overrides = {}

    def set_status(self, player_name, status):
        """
        Manually set a player's injury status
        status options: "OUT", "QUESTIONABLE", "PROBABLE", "DOUBTFUL", "ACTIVE"
        """
        valid_statuses = ["OUT", "QUESTIONABLE", "PROBABLE", "DOUBTFUL", "ACTIVE"]
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")

        self.overrides[player_name] = {
            "status": status,
            "last_updated": datetime.now()
        }

    def get_status(self, player_name):
        """Get manually set status for a player"""
        if player_name in self.overrides:
            return self.overrides[player_name]
        return None

    def clear_override(self, player_name):
        """Remove manual override for a player"""
        if player_name in self.overrides:
            del self.overrides[player_name]

    def clear_all(self):
        """Clear all manual overrides"""
        self.overrides = {}


# Combined tracker that uses both NBA API and manual overrides
class CombinedInjuryTracker:
    """
    Combines NBA API inactive data with manual overrides
    Manual overrides take precedence
    """
    def __init__(self):
        self.nba_tracker = InjuryTracker()
        self.manual_override = ManualInjuryOverride()

    def get_player_status(self, player_name):
        """
        Get player status with manual override taking precedence
        Returns: {"status": str, "source": str}
        """
        # Check manual override first
        override = self.manual_override.get_status(player_name)
        if override:
            return {
                "status": override["status"],
                "source": "manual",
                "last_updated": override["last_updated"].isoformat()
            }

        # Check NBA API
        nba_status = self.nba_tracker.is_player_inactive(player_name)
        if nba_status["is_inactive"]:
            return {
                "status": nba_status["status"],
                "source": "nba_api",
                "last_updated": datetime.now().isoformat()
            }

        # Default to ACTIVE
        return {
            "status": "ACTIVE",
            "source": "default",
            "last_updated": datetime.now().isoformat()
        }

    def get_batch_status(self, player_names):
        """Get status for multiple players"""
        results = {}
        for player_name in player_names:
            results[player_name] = self.get_player_status(player_name)
        return results

    def set_manual_status(self, player_name, status):
        """Manually set a player's status (for testing/demo)"""
        self.manual_override.set_status(player_name, status)

    def clear_manual_status(self, player_name):
        """Clear manual override for a player"""
        self.manual_override.clear_override(player_name)

    def refresh_nba_data(self):
        """
        Force refresh of NBA API data
        This will actually fetch from NBA API, so it may take some time
        """
        self.nba_tracker.clear_cache()

        # Fetch inactive players from NBA API
        try:
            from nba_api.stats.endpoints import LeagueGameFinder
            from nba_api.stats.endpoints import BoxScoreSummaryV3

            today = datetime.now().strftime('%Y-%m-%d')

            # Find games for today
            game_finder = LeagueGameFinder(
                date_from_nullable=today,
                date_to_nullable=today,
                league_id_nullable='00'
            )

            games_df = game_finder.get_data_frames()[0]

            if games_df.empty:
                print(f"No games found for {today}")
                return {}

            # Get unique game IDs
            game_ids = games_df['GAME_ID'].unique()
            print(f"Found {len(game_ids)} games for {today}")

            inactive_players = {}

            # For each game, get inactive players
            for game_id in game_ids:
                try:
                    time.sleep(0.6)  # Rate limiting

                    summary = BoxScoreSummaryV3(game_id=game_id)
                    inactive_df = summary.inactive_players.get_data_frame()

                    if not inactive_df.empty:
                        for _, player in inactive_df.iterrows():
                            player_name = f"{player['FIRST_NAME']} {player['FAMILY_NAME']}"
                            inactive_players[player_name] = {
                                "status": "OUT",
                                "last_updated": datetime.now(),
                                "game_id": game_id
                            }
                except Exception as e:
                    # Game hasn't started yet or other error
                    print(f"Could not get inactive players for game {game_id}: {e}")
                    continue

            # Update cache
            self.nba_tracker.cache = inactive_players
            self.nba_tracker.last_fetch = datetime.now()

            return inactive_players

        except Exception as e:
            print(f"Error fetching inactive players: {e}")
            return {}
