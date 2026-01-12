"""
StatScout Database Data Loader
Handles loading and processing player data from SQLite database
"""

from models import get_engine, get_session, Player, Game
from sqlalchemy import func, text
from typing import Dict, List, Any


class DatabaseLoader:
    """Load and process player statistics from database"""

    def __init__(self):
        """Initialize the database loader"""
        self.engine = get_engine()
        self.session = get_session(self.engine)

    def _ensure_session(self):
        """Ensure session is valid, rollback if needed"""
        try:
            # Test if session is still valid
            self.session.execute(text("SELECT 1"))
        except Exception as e:
            print(f"[WARNING] Session invalid, rolling back: {e}")
            try:
                self.session.rollback()
            except:
                pass
            # Create new session if rollback fails
            try:
                self.session.close()
                self.session = get_session(self.engine)
            except:
                pass

    def get_player_names(self) -> List[str]:
        """Get list of all unique player names"""
        self._ensure_session()
        try:
            players = self.session.query(Player.name).order_by(Player.name).all()
            return [p.name for p in players]
        except Exception as e:
            print(f"[ERROR] Failed to get player names: {e}")
            self.session.rollback()
            return []
    
    def get_teams(self) -> List[str]:
        """Get list of all unique teams"""
        self._ensure_session()
        try:
            teams = self.session.query(Player.team).distinct().order_by(Player.team).all()
            return [t.team for t in teams]
        except Exception as e:
            print(f"[ERROR] Failed to get teams: {e}")
            self.session.rollback()
            return []

    def get_player_info(self, player_name: str) -> Dict[str, Any]:
        """
        Get basic info about a player

        Args:
            player_name: Player's name

        Returns:
            Dictionary with player info
        """
        self._ensure_session()
        try:
            player = self.session.query(Player).filter(Player.name == player_name).first()

            if not player:
                return None

            game_count = self.session.query(Game).filter(Game.player_id == player.id).count()

            # Calculate average minutes per game
            avg_minutes_result = self.session.query(func.avg(Game.minutes)).filter(
                Game.player_id == player.id,
                Game.minutes.isnot(None)
            ).scalar()

            avg_minutes = round(avg_minutes_result, 1) if avg_minutes_result else 0.0

            return {
                "name": player.name,
                "team": player.team,
                "position": player.position,
                "games_played": game_count,
                "avg_minutes": avg_minutes
            }
        except Exception as e:
            print(f"[ERROR] Failed to get player info for {player_name}: {e}")
            self.session.rollback()
            return None
    
    def get_player_stat_history(
        self, 
        player_name: str, 
        stat_column: str, 
        num_games: int = None
    ) -> List[float]:
        """
        Get a player's stat history
        
        Args:
            player_name: Player's name
            stat_column: Stat column name (e.g., 'points', 'rebounds')
            num_games: Number of recent games to return (None = all games)
            
        Returns:
            List of stat values (oldest to newest)
        """
        player = self.session.query(Player).filter(Player.name == player_name).first()
        
        if not player:
            return []
        
        # Query games ordered by date
        query = self.session.query(Game).filter(
            Game.player_id == player.id
        ).order_by(Game.date)
        
        games = query.all()
        
        # Extract the stat values
        stat_values = [getattr(game, stat_column) for game in games]
        
        # Return last N games if specified
        if num_games:
            stat_values = stat_values[-num_games:]
        
        return stat_values
    
    def get_combined_stat_history(
        self,
        player_name: str,
        stat_columns: List[str],
        num_games: int = None
    ) -> List[float]:
        """
        Get combined stat history (e.g., points + rebounds + assists)
        
        Args:
            player_name: Player's name
            stat_columns: List of stat columns to combine
            num_games: Number of recent games
            
        Returns:
            List of combined stat values
        """
        player = self.session.query(Player).filter(Player.name == player_name).first()
        
        if not player:
            return []
        
        # Query games ordered by date
        query = self.session.query(Game).filter(
            Game.player_id == player.id
        ).order_by(Game.date)
        
        games = query.all()
        
        # Sum the specified columns for each game
        combined = []
        for game in games:
            total = sum(getattr(game, col) for col in stat_columns)
            combined.append(total)
        
        if num_games:
            combined = combined[-num_games:]
        
        return combined
    
    def get_all_available_stats(self, player_name: str) -> Dict[str, List[float]]:
        """
        Get all stat types available for a player

        Args:
            player_name: Player's name

        Returns:
            Dictionary mapping stat names to value lists
        """
        player = self.session.query(Player).filter(Player.name == player_name).first()

        if not player:
            return {}

        # Query all games for this player
        games = self.session.query(Game).filter(
            Game.player_id == player.id
        ).order_by(Game.date).all()

        stats_dict = {}

        # Individual stats
        stat_columns = ['points', 'rebounds', 'assists', 'steals', 'blocks', 'three_pm']

        for col in stat_columns:
            stats_dict[col] = [getattr(game, col) for game in games]

        # Combined stats
        stats_dict['PRA'] = [game.points + game.rebounds + game.assists for game in games]
        stats_dict['PA'] = [game.points + game.assists for game in games]
        stats_dict['PR'] = [game.points + game.rebounds for game in games]
        stats_dict['RA'] = [game.rebounds + game.assists for game in games]

        return stats_dict

    def get_matchup_history(self, player_name: str, opponent: str) -> Dict[str, Any]:
        """
        Get a player's performance history against a specific opponent

        Args:
            player_name: Player's name
            opponent: Opponent team abbreviation

        Returns:
            Dictionary with matchup stats and game history
        """
        player = self.session.query(Player).filter(Player.name == player_name).first()

        if not player:
            return None

        # Get all games against this opponent
        games = self.session.query(Game).filter(
            Game.player_id == player.id,
            Game.opponent == opponent
        ).order_by(Game.date).all()

        if not games:
            return {
                "player": player_name,
                "opponent": opponent,
                "games_played": 0,
                "games": [],
                "averages": {}
            }

        # Calculate averages
        total_points = sum(g.points for g in games)
        total_rebounds = sum(g.rebounds for g in games)
        total_assists = sum(g.assists for g in games)
        total_steals = sum(g.steals for g in games)
        total_blocks = sum(g.blocks for g in games)
        total_three_pm = sum(g.three_pm for g in games)

        games_count = len(games)

        # Build game history
        game_history = []
        for game in games:
            game_history.append({
                "date": game.date.strftime('%Y-%m-%d'),
                "is_home": game.is_home,
                "points": game.points,
                "rebounds": game.rebounds,
                "assists": game.assists,
                "steals": game.steals,
                "blocks": game.blocks,
                "three_pm": game.three_pm,
                "minutes": game.minutes,
                "PRA": game.points + game.rebounds + game.assists
            })

        return {
            "player": player_name,
            "opponent": opponent,
            "games_played": games_count,
            "games": game_history,
            "averages": {
                "points": round(total_points / games_count, 1),
                "rebounds": round(total_rebounds / games_count, 1),
                "assists": round(total_assists / games_count, 1),
                "steals": round(total_steals / games_count, 1),
                "blocks": round(total_blocks / games_count, 1),
                "three_pm": round(total_three_pm / games_count, 1),
                "PRA": round((total_points + total_rebounds + total_assists) / games_count, 1)
            }
        }

    def get_home_away_splits(self, player_name: str, stat_type: str = 'points', min_games: int = 3) -> Dict[str, Any]:
        """
        Calculate home vs away performance splits for a player

        Args:
            player_name: Player's name
            stat_type: Stat to analyze ('points', 'rebounds', 'assists', etc.)
            min_games: Minimum games required for each split (default 3)

        Returns:
            Dictionary with home/away averages and counts
        """
        player = self.session.query(Player).filter(Player.name == player_name).first()

        if not player:
            return None

        # Get all games
        all_games = self.session.query(Game).filter(Game.player_id == player.id).all()

        if not all_games:
            return {
                "has_split": False,
                "home_games": 0,
                "away_games": 0
            }

        # Separate home and away games
        home_games = [g for g in all_games if g.is_home]
        away_games = [g for g in all_games if not g.is_home]

        # Check minimum game requirement
        if len(home_games) < min_games or len(away_games) < min_games:
            return {
                "has_split": False,
                "home_games": len(home_games),
                "away_games": len(away_games),
                "min_required": min_games
            }

        # Map stat type to game attribute
        stat_map = {
            'points': 'points',
            'rebounds': 'rebounds',
            'assists': 'assists',
            'steals': 'steals',
            'blocks': 'blocks',
            'three_pm': 'three_pm',
            '3pm': 'three_pm'
        }

        stat_attr = stat_map.get(stat_type.lower(), 'points')

        # Calculate averages
        home_values = [getattr(g, stat_attr) for g in home_games]
        away_values = [getattr(g, stat_attr) for g in away_games]

        home_avg = sum(home_values) / len(home_values)
        away_avg = sum(away_values) / len(away_values)
        difference = home_avg - away_avg

        return {
            "has_split": True,
            "home_games": len(home_games),
            "away_games": len(away_games),
            "home_avg": round(home_avg, 1),
            "away_avg": round(away_avg, 1),
            "difference": round(difference, 1),
            "better_at_home": difference > 0
        }

    def get_rest_days(self, player_name: str, upcoming_game_date: str = None) -> Dict[str, Any]:
        """
        Calculate rest days before the upcoming game

        Args:
            player_name: Player's name
            upcoming_game_date: Date of upcoming game (YYYY-MM-DD format). If None, uses today.

        Returns:
            Dictionary with rest_days, last_game_date, and is_back_to_back
        """
        from datetime import datetime, timedelta

        player = self.session.query(Player).filter(Player.name == player_name).first()

        if not player:
            return None

        # Get all games sorted by date (most recent first)
        games = self.session.query(Game).filter(
            Game.player_id == player.id
        ).order_by(Game.date.desc()).all()

        if not games:
            return {
                "rest_days": None,
                "last_game_date": None,
                "is_back_to_back": False
            }

        # Get the most recent game date
        last_game = games[0]
        last_game_date = last_game.date

        # Determine upcoming game date
        if upcoming_game_date:
            if isinstance(upcoming_game_date, str):
                upcoming_date = datetime.strptime(upcoming_game_date, '%Y-%m-%d').date()
            else:
                upcoming_date = upcoming_game_date
        else:
            upcoming_date = datetime.now().date()

        # Calculate rest days
        rest_days = (upcoming_date - last_game_date).days - 1  # -1 because game day doesn't count as rest

        # Back-to-back if 0 rest days (games on consecutive days)
        is_back_to_back = rest_days == 0

        return {
            "rest_days": rest_days,
            "last_game_date": str(last_game_date),
            "is_back_to_back": is_back_to_back
        }

    def get_usage_trend(self, player_name: str, stat_type: str = 'points', recent_n: int = 5, baseline_n: int = 15) -> Dict[str, Any]:
        """
        Calculate if a player's usage is trending up or down

        Compares recent N games to baseline average to detect role changes

        Args:
            player_name: Player's name
            stat_type: Stat to analyze ('points', 'rebounds', etc.)
            recent_n: Number of recent games to compare (default 5)
            baseline_n: Number of games for baseline (default 15)

        Returns:
            Dictionary with trend direction, percentages, and significance
        """
        player = self.session.query(Player).filter(Player.name == player_name).first()

        if not player:
            return None

        # Get all games sorted by date (oldest first for proper baseline)
        all_games = self.session.query(Game).filter(
            Game.player_id == player.id
        ).order_by(Game.date.asc()).all()

        if len(all_games) < baseline_n:
            return {
                "has_trend": False,
                "reason": f"Not enough games (need {baseline_n}, have {len(all_games)})"
            }

        # Map stat type to game attribute
        stat_map = {
            'points': 'points',
            'rebounds': 'rebounds',
            'assists': 'assists',
            'steals': 'steals',
            'blocks': 'blocks',
            'three_pm': 'three_pm',
            '3pm': 'three_pm'
        }

        stat_attr = stat_map.get(stat_type.lower(), 'points')

        # Get recent games and baseline games
        recent_games = all_games[-recent_n:]
        baseline_games = all_games[-baseline_n:-recent_n] if len(all_games) > baseline_n else all_games[:-recent_n]

        if not baseline_games:
            # If not enough for split, use all except recent as baseline
            baseline_games = all_games[:-recent_n]

        if not baseline_games:
            return {
                "has_trend": False,
                "reason": "Not enough games for baseline comparison"
            }

        # Calculate averages
        recent_avg = sum(getattr(g, stat_attr) for g in recent_games) / len(recent_games)
        baseline_avg = sum(getattr(g, stat_attr) for g in baseline_games) / len(baseline_games)

        # Calculate percentage change
        if baseline_avg > 0:
            pct_change = ((recent_avg - baseline_avg) / baseline_avg) * 100
        else:
            pct_change = 0

        # Determine if trend is significant (> 15% change)
        is_significant = abs(pct_change) >= 15

        trend_direction = "up" if pct_change > 0 else "down" if pct_change < 0 else "stable"

        return {
            "has_trend": True,
            "trend_direction": trend_direction,
            "recent_avg": round(recent_avg, 1),
            "baseline_avg": round(baseline_avg, 1),
            "pct_change": round(pct_change, 1),
            "is_significant": is_significant,
            "recent_games": recent_n,
            "baseline_games": len(baseline_games)
        }

    def close(self):
        """Close the database session"""
        self.session.close()


# Example usage
if __name__ == "__main__":
    loader = DatabaseLoader()
    
    try:
        print("=== Database Loader Test ===\n")
        
        print("📋 Available Players:")
        players = loader.get_player_names()
        for player in players[:5]:  # Show first 5
            info = loader.get_player_info(player)
            print(f"  {player} ({info['team']}, {info['position']}) - {info['games_played']} games")
        print(f"  ... and {len(players) - 5} more players\n")
        
        print("🏀 LeBron James Stats:")
        lebron_points = loader.get_player_stat_history("LeBron James", "points", num_games=10)
        print(f"  Last 10 games (Points): {lebron_points}")
        
        lebron_pra = loader.get_combined_stat_history("LeBron James", ["points", "rebounds", "assists"], num_games=10)
        print(f"  Last 10 games (P+R+A): {lebron_pra}")
        
        print("\n✅ Database loader working correctly!")
        
    finally:
        loader.close()