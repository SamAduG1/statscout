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
        # Trust score weights (must sum to 1.0)
        self.hit_rate_weight = 0.30      # 30% weight for historical hit rate
        self.recent_form_weight = 0.20   # 20% weight for recent performance
        self.opponent_weight = 0.10      # 10% weight for opponent difficulty
        self.teammate_weight = 0.10      # 10% weight for teammate injury boost
        self.rest_weight = 0.15          # 15% weight for rest days (NEW - high impact!)
        self.usage_trend_weight = 0.10   # 10% weight for usage trending (NEW)
        self.consistency_weight = 0.05   # 5% weight for player consistency (NEW)

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
        db_loader=None,
        rest_days: int = None,
        usage_trend_data: Dict[str, Any] = None
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
            db_loader: DatabaseLoader instance (for teammate boost and rest days)
            rest_days: Number of rest days (if None, will calculate from db_loader)
            usage_trend_data: Usage trend data (if None, will calculate from db_loader)

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

        # Calculate rest factor
        rest_score = 50.0  # Default neutral
        if rest_days is not None:
            rest_factor_data = self.calculate_rest_factor(rest_days, rest_days == 0)
            rest_score = rest_factor_data["rest_score"]
        elif db_loader and player_name:
            # Try to get rest days from database
            rest_data = db_loader.get_rest_days(player_name)
            if rest_data and rest_data["rest_days"] is not None:
                rest_factor_data = self.calculate_rest_factor(
                    rest_data["rest_days"],
                    rest_data["is_back_to_back"]
                )
                rest_score = rest_factor_data["rest_score"]

        # Calculate usage trend factor
        usage_score = 50.0  # Default neutral
        if usage_trend_data:
            usage_analysis = self.analyze_usage_trend(usage_trend_data)
            if usage_analysis["has_data"]:
                usage_score = usage_analysis["usage_score"]
        elif db_loader and player_name:
            # Try to get usage trend from database
            trend_data = db_loader.get_usage_trend(player_name, stat_type.lower())
            if trend_data:
                usage_analysis = self.analyze_usage_trend(trend_data)
                if usage_analysis["has_data"]:
                    usage_score = usage_analysis["usage_score"]

        # Calculate consistency factor
        consistency_data = self.calculate_consistency_score(player_stats)
        consistency_score = consistency_data["consistency_score"]

        # Weighted average with all factors
        trust_score = (
            (hit_rate * self.hit_rate_weight) +
            (recent_form * self.recent_form_weight) +
            (opponent_diff * self.opponent_weight) +
            (teammate_boost * self.teammate_weight) +
            (rest_score * self.rest_weight) +
            (usage_score * self.usage_trend_weight) +
            (consistency_score * self.consistency_weight)
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

    def calculate_consistency_score(self, player_stats: List[float]) -> Dict[str, Any]:
        """
        Calculate player consistency score based on standard deviation

        Identifies if a player is reliable (low variance) or volatile (high variance)

        Args:
            player_stats: List of player's recent stat values

        Returns:
            Dictionary with consistency_score (0-100) and classification
        """
        if not player_stats or len(player_stats) < 5:
            return {
                "has_data": False,
                "consistency_score": 50.0,
                "classification": "Unknown"
            }

        # Calculate mean and standard deviation
        mean = np.mean(player_stats)
        std_dev = np.std(player_stats)

        # Calculate coefficient of variation (CV)
        # Lower CV = more consistent
        if mean > 0:
            cv = (std_dev / mean) * 100
        else:
            cv = 100  # Max variance if mean is 0

        # Convert CV to 0-100 consistency score
        # CV < 20% = very consistent (score 90-100)
        # CV 20-40% = consistent (score 70-90)
        # CV 40-60% = average (score 50-70)
        # CV > 60% = volatile (score 0-50)

        if cv <= 20:
            consistency_score = 100 - (cv / 20) * 10  # 90-100
            classification = "Very Consistent"
        elif cv <= 40:
            consistency_score = 90 - ((cv - 20) / 20) * 20  # 70-90
            classification = "Consistent"
        elif cv <= 60:
            consistency_score = 70 - ((cv - 40) / 20) * 20  # 50-70
            classification = "Average"
        else:
            consistency_score = max(0, 50 - ((cv - 60) / 40) * 50)  # 0-50
            classification = "Volatile"

        return {
            "has_data": True,
            "consistency_score": round(consistency_score, 1),
            "coefficient_of_variation": round(cv, 1),
            "std_dev": round(std_dev, 1),
            "mean": round(mean, 1),
            "classification": classification
        }

    def calculate_rest_factor(self, rest_days: int, is_back_to_back: bool) -> Dict[str, Any]:
        """
        Calculate impact of rest days on performance

        Args:
            rest_days: Number of days of rest before game
            is_back_to_back: Whether game is a back-to-back

        Returns:
            Dictionary with rest_score (0-100) and warning if applicable
        """
        warning = None

        # Back-to-back games hurt performance significantly
        if is_back_to_back:
            rest_score = 30.0  # Major penalty
            warning = "⚠️ Back-to-back game - historically 10-15% performance drop"
        # 1 day rest is below optimal
        elif rest_days == 1:
            rest_score = 60.0
            warning = "⚡ Only 1 day rest - slightly below optimal"
        # 2-3 days is optimal
        elif 2 <= rest_days <= 3:
            rest_score = 100.0  # Optimal rest
        # 4-5 days is good
        elif 4 <= rest_days <= 5:
            rest_score = 90.0
        # 6+ days might indicate rust
        elif rest_days >= 6:
            rest_score = 70.0
            warning = "🛑 Extended rest (6+ days) - possible rust factor"
        else:
            rest_score = 50.0  # Default

        return {
            "rest_days": rest_days,
            "is_back_to_back": is_back_to_back,
            "rest_score": rest_score,
            "warning": warning
        }

    def analyze_usage_trend(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze usage trend significance for predictions

        Args:
            trend_data: Trend data from db_loader.get_usage_trend()

        Returns:
            Analysis with adjusted expectations and warnings
        """
        if not trend_data or not trend_data.get("has_trend"):
            return {
                "has_data": False,
                "usage_score": 50.0
            }

        pct_change = trend_data["pct_change"]
        is_significant = trend_data["is_significant"]
        trend_direction = trend_data["trend_direction"]

        # Convert trend to score (0-100)
        # Positive trend (usage up) = higher score
        # Negative trend (usage down) = lower score

        if is_significant:
            if trend_direction == "up":
                # Significant upward trend - boost prediction
                usage_score = 75 + min(25, abs(pct_change) / 2)  # 75-100
                warning = f"📈 Usage trending UP {abs(pct_change):.1f}% - role expanding"
            elif trend_direction == "down":
                # Significant downward trend - penalize prediction
                usage_score = 25 - min(25, abs(pct_change) / 2)  # 0-25
                warning = f"📉 Usage trending DOWN {abs(pct_change):.1f}% - role shrinking"
            else:
                usage_score = 50.0
                warning = None
        else:
            # Not significant - neutral
            usage_score = 50.0 + (pct_change / 2)  # Small adjustment
            warning = None

        return {
            "has_data": True,
            "usage_score": round(max(0, min(100, usage_score)), 1),
            "pct_change": pct_change,
            "is_significant": is_significant,
            "trend_direction": trend_direction,
            "warning": warning,
            "recent_avg": trend_data["recent_avg"],
            "baseline_avg": trend_data["baseline_avg"]
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