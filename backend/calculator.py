"""
StatScout Calculator Module
Handles all calculations for hit rates, trust scores, and player analytics
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


class StatScoutCalculator:
    """Main calculator class for player prop analytics"""

    def __init__(self, injury_tracker=None):
        """
        Initialize the calculator with default weights

        Args:
            injury_tracker: Optional ESPNInjuryTracker instance for teammate injury boosts
        """
        # Original weights (adjusted to make room for teammate boost)
        self.hit_rate_weight = 0.45      # 45% weight for historical hit rate
        self.recent_form_weight = 0.25   # 25% weight for recent performance
        self.opponent_weight = 0.15      # 15% weight for opponent difficulty
        self.teammate_weight = 0.15      # 15% weight for teammate injury boost

        # Injury tracker for detecting out players
        self.injury_tracker = injury_tracker

        # Star player thresholds (points per game to be considered a "star")
        self.star_threshold_ppg = 20.0  # Players averaging 20+ PPG are "stars"

    def calculate_hit_rate(self, player_stats: List[float], line: float) -> float:
        """
        Calculate the percentage of games where player exceeded the line

        Args:
            player_stats: List of player's stat values from recent games
            line: The over/under betting line

        Returns:
            Hit rate as a percentage (0-100)
        """
        if not player_stats or len(player_stats) == 0:
            return 0.0

        hits = sum(1 for stat in player_stats if stat > line)
        hit_rate = (hits / len(player_stats)) * 100
        return round(hit_rate, 1)

    def calculate_recent_hit_rate(self, player_stats: List[float], line: float, recent_n: int = 10) -> Dict[str, Any]:
        """
        Calculate hit rate for the most recent N games

        Args:
            player_stats: List of player's stat values (most recent last)
            line: The over/under betting line
            recent_n: Number of recent games to analyze (default 10)

        Returns:
            Dictionary with recent_hit_rate (percentage), hits, and total games
        """
        if not player_stats or len(player_stats) == 0:
            return {"recent_hit_rate": 0.0, "hits": 0, "total": 0}

        # Get last N games (or all games if less than N)
        recent_games = player_stats[-recent_n:] if len(player_stats) >= recent_n else player_stats

        hits = sum(1 for stat in recent_games if stat > line)
        total = len(recent_games)
        recent_hit_rate = (hits / total) * 100 if total > 0 else 0.0

        return {
            "recent_hit_rate": round(recent_hit_rate, 1),
            "hits": hits,
            "total": total
        }
    
    def calculate_recent_form(self, player_stats: List[float], line: float, recent_n: int = 3) -> float:
        """
        Calculate recent form score based on last N games
        
        Args:
            player_stats: List of player's stat values (most recent last)
            line: The over/under betting line
            recent_n: Number of recent games to consider
            
        Returns:
            Recent form score (0-100)
        """
        if not player_stats or len(player_stats) < recent_n:
            return 50.0  # Neutral score if not enough data
        
        recent_games = player_stats[-recent_n:]  # Last N games
        
        # Calculate average performance vs line in recent games
        avg_recent = np.mean(recent_games)
        diff_from_line = avg_recent - line
        
        # Convert to a 0-100 score
        # If averaging 5+ points over line = 100, 5+ under = 0
        percentage_diff = (diff_from_line / line) * 100
        
        # Map to 0-100 scale with 50 as neutral
        if percentage_diff >= 20:
            score = 100
        elif percentage_diff <= -20:
            score = 0
        else:
            # Linear scale: -20% = 0, 0% = 50, +20% = 100
            score = 50 + (percentage_diff / 20) * 50
        
        return round(max(0, min(100, score)), 1)
    
    def calculate_opponent_difficulty(self, opponent_rank: int, total_teams: int = 30) -> float:
        """
        Calculate opponent difficulty score
        
        Args:
            opponent_rank: Defensive rank of opponent (1 = best defense, 30 = worst)
            total_teams: Total number of teams in league
            
        Returns:
            Opponent difficulty score (0-100, higher = easier matchup)
        """
        if opponent_rank <= 0 or opponent_rank > total_teams:
            return 50.0  # Neutral if invalid rank
        
        # Inverse rank - playing against #30 defense (worst) = 100, #1 defense (best) = 0
        difficulty_score = ((total_teams - opponent_rank) / (total_teams - 1)) * 100
        
        return round(difficulty_score, 1)

    def is_star_player(self, player_stats: List[float], stat_type: str) -> bool:
        """
        Determine if a player is a "star" based on their stats

        Args:
            player_stats: List of player's recent stat values
            stat_type: Type of stat being analyzed (Points, Rebounds, etc.)

        Returns:
            True if player is a star, False otherwise
        """
        if not player_stats or len(player_stats) < 5:
            return False

        avg_stat = np.mean(player_stats[-10:]) if len(player_stats) >= 10 else np.mean(player_stats)

        # For points, use PPG threshold
        if stat_type.lower() == "points":
            return avg_stat >= self.star_threshold_ppg

        # For other stats, use relative thresholds
        # Assists: 7+ APG, Rebounds: 10+ RPG, PRA: 35+
        thresholds = {
            "assists": 7.0,
            "rebounds": 10.0,
            "pra": 35.0,
            "pa": 27.0,
            "pr": 30.0,
        }

        threshold = thresholds.get(stat_type.lower(), float('inf'))
        return avg_stat >= threshold

    def calculate_teammate_boost(
        self,
        player_name: str,
        team: str,
        stat_type: str,
        db_loader=None
    ) -> float:
        """
        Calculate boost to trust score based on injured teammates

        When a star player is out, teammates get a boost because they'll absorb extra usage.
        This was critical in cases like Jalen Brunson out → KAT 40pts, Tyler Kolek 20pts.

        Args:
            player_name: Name of player being analyzed
            team: Player's team abbreviation
            stat_type: Type of stat (Points, Rebounds, Assists, etc.)
            db_loader: DatabaseLoader instance to check teammate stats

        Returns:
            Boost score (0-100), where 0 = no boost, 100 = max boost
        """
        # If no injury tracker or db_loader, can't calculate boost
        if not self.injury_tracker or not db_loader:
            return 50.0  # Neutral score

        try:
            # Get all current injuries
            injuries = self.injury_tracker.get_all_injuries()

            # Find injured teammates on same team
            injured_teammates = []
            for injured_player, injury_info in injuries.items():
                # Skip if it's the player being analyzed
                if injured_player == player_name:
                    continue

                # Check if they're on the same team and actually OUT
                if (injury_info['team'] == team and
                    injury_info['status'] in ['OUT', 'DOUBTFUL']):
                    injured_teammates.append({
                        'name': injured_player,
                        'status': injury_info['status'],
                        'injury': injury_info['injury']
                    })

            # If no injured teammates, return neutral
            if not injured_teammates:
                return 50.0

            # Calculate boost based on injured teammates
            boost_score = 50.0  # Start neutral
            max_boost_per_player = 25.0  # Max +25 points per star player out

            for teammate in injured_teammates:
                # Check if injured teammate is a star
                try:
                    # Get the injured teammate's stats
                    teammate_stats = db_loader.get_player_stat_history(
                        teammate['name'],
                        'points',  # Use points to determine if they're a star
                        num_games=15
                    )

                    if teammate_stats and len(teammate_stats) >= 5:
                        # Check if they're a star scorer
                        if self.is_star_player(teammate_stats, "points"):
                            # Star player is out - boost the trust score
                            if teammate['status'] == 'OUT':
                                boost_score += max_boost_per_player
                            elif teammate['status'] == 'DOUBTFUL':
                                boost_score += max_boost_per_player * 0.5  # Half boost for doubtful

                            print(f"  [Teammate Boost] {teammate['name']} ({teammate['status']}) is out - boosting {player_name}'s trust score")
                except Exception as e:
                    # If we can't get teammate stats, skip them
                    continue

            # Cap boost at 100
            return min(100.0, boost_score)

        except Exception as e:
            print(f"  [Warning] Could not calculate teammate boost: {e}")
            return 50.0  # Neutral on error

    def calculate_trust_score(
        self,
        player_stats: List[float],
        line: float,
        opponent_rank: int,
        is_home: bool = True,
        player_name: str = None,
        team: str = None,
        stat_type: str = "Points",
        db_loader=None
    ) -> float:
        """
        Calculate overall trust score for a player prop

        Args:
            player_stats: List of player's recent stat values
            line: The over/under betting line
            opponent_rank: Defensive rank of opponent
            is_home: Whether player is playing at home
            player_name: Player's name (for teammate boost calculation)
            team: Player's team (for teammate boost calculation)
            stat_type: Type of stat being analyzed (for teammate boost)
            db_loader: DatabaseLoader instance (for teammate boost)

        Returns:
            Trust score (0-100)
        """
        # Calculate component scores
        hit_rate = self.calculate_hit_rate(player_stats, line)
        recent_form = self.calculate_recent_form(player_stats, line)
        opponent_diff = self.calculate_opponent_difficulty(opponent_rank)

        # Calculate teammate injury boost if we have the required info
        teammate_boost = 50.0  # Default neutral
        if player_name and team and self.injury_tracker:
            teammate_boost = self.calculate_teammate_boost(
                player_name, team, stat_type, db_loader
            )

        # Weighted average with teammate boost
        trust_score = (
            (hit_rate * self.hit_rate_weight) +
            (recent_form * self.recent_form_weight) +
            (opponent_diff * self.opponent_weight) +
            (teammate_boost * self.teammate_weight)
        )

        # Home court advantage boost (+5 points if at home)
        if is_home:
            trust_score = min(100, trust_score + 5)

        return round(trust_score, 1)
    
    def detect_streak(self, player_stats: List[float], line: float) -> Dict[str, Any]:
        """
        Detect if player is on a hot or cold streak

        Args:
            player_stats: List of player's recent stat values (most recent last)
            line: The over/under betting line

        Returns:
            Dictionary with streak info: {streak: int, type: 'over'|'under'|None}
        """
        if not player_stats or len(player_stats) < 3:
            return {"streak": 0, "type": None}

        streak = 0
        streak_type = None

        # Check from most recent game backwards
        for stat in reversed(player_stats):
            if stat > line:
                if streak_type is None:
                    streak_type = "over"
                if streak_type == "over":
                    streak += 1
                else:
                    break
            else:
                if streak_type is None:
                    streak_type = "under"
                if streak_type == "under":
                    streak += 1
                else:
                    break

        # Only return streak if 3+ games
        if streak < 3:
            return {"streak": 0, "type": None}

        return {"streak": streak, "type": streak_type}
    
    def analyze_player_prop(
        self,
        player_name: str,
        team: str,
        stat_type: str,
        player_stats: List[float],
        line: float,
        opponent: str,
        opponent_rank: int,
        is_home: bool = True,
        db_loader=None
    ) -> Dict[str, Any]:
        """
        Complete analysis of a player prop

        Args:
            player_name: Player's name
            team: Player's team abbreviation
            stat_type: Type of stat (Points, Rebounds, Assists, etc.)
            player_stats: List of recent stat values
            line: Betting line
            opponent: Opponent team abbreviation
            opponent_rank: Opponent's defensive rank
            is_home: Whether playing at home
            db_loader: DatabaseLoader instance for teammate boost calculation

        Returns:
            Complete analysis dictionary
        """
        hit_rate = self.calculate_hit_rate(player_stats, line)
        recent_hit_rate_info = self.calculate_recent_hit_rate(player_stats, line, recent_n=10)
        trust_score = self.calculate_trust_score(
            player_stats, line, opponent_rank, is_home,
            player_name=player_name, team=team, stat_type=stat_type, db_loader=db_loader
        )
        streak_info = self.detect_streak(player_stats, line)

        # Calculate averages for different time ranges
        avg_last_5 = round(np.mean(player_stats[-5:]), 1) if len(player_stats) >= 5 else None
        avg_last_10 = round(np.mean(player_stats[-10:]), 1) if len(player_stats) >= 10 else None
        avg_last_15 = round(np.mean(player_stats[-15:]), 1) if len(player_stats) >= 15 else None

        # Determine recent form
        if trust_score >= 75:
            recent_form = "hot"
        elif trust_score <= 55:
            recent_form = "cold"
        else:
            recent_form = "neutral"

        # Calculate total games for hit rate context
        total_games = len(player_stats)
        season_hits = int((hit_rate / 100) * total_games) if total_games > 0 else 0

        return {
            "player_name": player_name,
            "team": team,
            "stat_type": stat_type,
            "line": line,
            "hit_rate": hit_rate,
            "season_hits": season_hits,
            "total_games": total_games,
            "recent_hit_rate": recent_hit_rate_info["recent_hit_rate"],
            "recent_hits": recent_hit_rate_info["hits"],
            "recent_total": recent_hit_rate_info["total"],
            "trust_score": trust_score,
            "recent_form": recent_form,
            "opponent": opponent,
            "opponent_rank": opponent_rank,
            "is_home": is_home,
            "avg_last_5": avg_last_5,
            "avg_last_10": avg_last_10,
            "avg_last_15": avg_last_15,
            "streak": streak_info["streak"],
            "streak_type": streak_info["type"],
            "last_games": player_stats[-10:] if len(player_stats) >= 10 else player_stats,
            "last_5_games": player_stats[-5:] if len(player_stats) >= 5 else player_stats,
            "last_15_games": player_stats[-15:] if len(player_stats) >= 15 else player_stats
        }

    def analyze_location_split(self, split_data: Dict[str, Any], is_home: bool, threshold: float = 3.0) -> Dict[str, Any]:
        """
        Analyze home/away split significance

        Args:
            split_data: Split data from db_loader.get_home_away_splits()
            is_home: Is the upcoming game at home?
            threshold: Difference threshold to mark as significant (default 3.0)

        Returns:
            Analysis with warnings and recommendations
        """
        if not split_data or not split_data.get("has_split"):
            return {
                "has_data": False,
                "warning": None
            }

        difference = abs(split_data["difference"])
        is_significant = difference >= threshold

        # Determine if location is favorable or not
        better_at_home = split_data["better_at_home"]
        favorable = (is_home and better_at_home) or (not is_home and not better_at_home)

        warning = None
        if is_significant:
            if favorable:
                warning = f"⭐ Player performs {difference} better in this location"
            else:
                warning = f"⚠️ Player averages {difference} worse in this location"

        return {
            "has_data": True,
            "home_avg": split_data["home_avg"],
            "away_avg": split_data["away_avg"],
            "difference": split_data["difference"],
            "is_significant": is_significant,
            "favorable_location": favorable,
            "warning": warning,
            "home_games": split_data["home_games"],
            "away_games": split_data["away_games"]
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the calculator
    calc = StatScoutCalculator()
    
    # Example: LeBron's last 15 games
    lebron_points = [28, 26, 22, 30, 25, 23, 27, 21, 29, 24, 26, 28, 25, 27, 23]
    line = 24.5
    
    result = calc.analyze_player_prop(
        player_name="LeBron James",
        team="LAL",
        stat_type="Points",
        player_stats=lebron_points,
        line=line,
        opponent="GSW",
        opponent_rank=18,
        is_home=True
    )
    
    print("=== StatScout Analysis ===")
    print(f"Player: {result['player_name']}")
    print(f"Stat: {result['stat_type']} O/U {result['line']}")
    print(f"Hit Rate: {result['hit_rate']}%")
    print(f"Trust Score: {result['trust_score']}")
    print(f"Recent Form: {result['recent_form']}")
    print(f"Avg Last 10: {result['avg_last_10']}")
    if result['streak'] > 0:
        print(f"Streak: {result['streak']} {result['streak_type']}")