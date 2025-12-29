"""
StatScout Parlay Builder
Generates optimized parlays based on trust scores and target odds
"""
from typing import List, Dict, Any, Optional
import itertools
import random


class ParlayBuilder:
    """Build optimized parlays from available props"""

    def __init__(self):
        # Trust score thresholds for different safety levels
        self.safety_thresholds = {
            "conservative": 70.0,   # 70%+ trust per leg
            "moderate": 60.0,       # 60%+ trust per leg
            "aggressive": 50.0      # 50%+ trust per leg
        }

        # Odds adjustment limits
        self.max_line_adjustment = 3.0  # Max ±3 points/boards/assists
        self.min_odds = -400  # Don't allow odds worse than -400
        self.max_odds = 200   # Don't allow odds better than +200

    def american_to_decimal(self, american_odds: int) -> float:
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1

    def decimal_to_american(self, decimal_odds: float) -> int:
        """Convert decimal odds to American odds"""
        if decimal_odds >= 2.0:
            return int((decimal_odds - 1) * 100)
        else:
            return int(-100 / (decimal_odds - 1))

    def calculate_parlay_odds(self, legs: List[Dict]) -> int:
        """
        Calculate combined parlay odds from individual legs

        Args:
            legs: List of prop dicts, each with 'odds' key (American format)

        Returns:
            Combined American odds for the parlay
        """
        if not legs:
            return 0

        # Convert all to decimal, multiply together
        combined_decimal = 1.0
        for leg in legs:
            decimal = self.american_to_decimal(leg['odds'])
            combined_decimal *= decimal

        # Convert back to American
        return self.decimal_to_american(combined_decimal)

    def calculate_parlay_trust(self, legs: List[Dict], method: str = "average") -> float:
        """
        Calculate overall parlay trust score

        Args:
            legs: List of prop dicts with 'trust_score' key
            method: 'average' (user-friendly) or 'probability' (mathematically accurate)

        Returns:
            Overall trust score (0-100)
        """
        if not legs:
            return 0.0

        if method == "average":
            # Simple average - easier to understand
            return round(sum(leg['trust_score'] for leg in legs) / len(legs), 1)

        elif method == "probability":
            # Probability product - more accurate but depressing
            combined_prob = 1.0
            for leg in legs:
                combined_prob *= (leg['trust_score'] / 100)
            return round(combined_prob * 100, 1)

        return 0.0

    def filter_props_by_trust(
        self,
        props: List[Dict],
        min_trust: float
    ) -> List[Dict]:
        """Filter props by minimum trust score"""
        return [p for p in props if p.get('trust_score', 0) >= min_trust]

    def filter_props_by_game(
        self,
        props: List[Dict],
        game_filter: str,
        selected_games: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Filter props by game selection

        Args:
            props: All available props
            game_filter: 'any', 'single', or 'specific'
            selected_games: List of game IDs (e.g., ['LAL_vs_GSW', 'BOS_vs_MIA'])

        Returns:
            Filtered props
        """
        if game_filter == "any":
            # Remove props from same game (avoid correlation)
            # Group by game, take max 1 per game
            games_seen = set()
            filtered = []
            for prop in props:
                game_id = f"{prop['team']}_vs_{prop['opponent']}"
                if game_id not in games_seen:
                    filtered.append(prop)
                    games_seen.add(game_id)
            return filtered

        elif game_filter == "single":
            # Only props from the same game (SGP)
            if not props:
                return []
            # Group by game, find game with most props
            from collections import defaultdict
            games = defaultdict(list)
            for prop in props:
                game_id = f"{prop['team']}_vs_{prop['opponent']}"
                games[game_id].append(prop)
            # Return props from game with most options
            best_game = max(games.items(), key=lambda x: len(x[1]))
            return best_game[1]

        elif game_filter == "specific" and selected_games:
            # Only props from selected games
            filtered = []
            for prop in props:
                game_id = f"{prop['team']}_vs_{prop['opponent']}"
                if game_id in selected_games:
                    filtered.append(prop)
            return filtered

        return props

    def find_parlay_combinations(
        self,
        props: List[Dict],
        target_odds: int,
        min_legs: int = 2,
        max_legs: int = 6,
        max_combinations: int = 1000
    ) -> List[List[Dict]]:
        """
        Find parlay combinations that hit target odds

        Args:
            props: Available props to choose from
            target_odds: Target American odds (e.g., +400)
            min_legs: Minimum number of props in parlay
            max_legs: Maximum number of props in parlay
            max_combinations: Max combinations to try (performance limit)

        Returns:
            List of valid parlay combinations
        """
        valid_parlays = []
        closest_parlays = []  # Track top 10 closest for fallback

        # More flexible tolerance: ±100 for lower odds, ±200 for higher odds
        tolerance = 100 if target_odds < 500 else 200

        # Try different parlay sizes (start from target, work outward for efficiency)
        # Estimate best leg count based on average odds
        avg_american_odds = sum(p.get('american_odds', -110) for p in props[:10]) / min(10, len(props))
        estimated_legs = max(min_legs, min(max_legs, int(target_odds / max(abs(avg_american_odds) - 100, 50))))

        # Try estimated size first, then expand
        leg_order = [estimated_legs]
        for offset in range(1, max(estimated_legs - min_legs, max_legs - estimated_legs) + 1):
            if estimated_legs - offset >= min_legs:
                leg_order.append(estimated_legs - offset)
            if estimated_legs + offset <= max_legs:
                leg_order.append(estimated_legs + offset)

        for num_legs in leg_order:
            if num_legs < min_legs or num_legs > max_legs:
                continue

            # Early exit if we have enough valid parlays
            if len(valid_parlays) >= 20:
                break

            # Generate combinations - use iterator for memory efficiency
            total_combos = len(list(itertools.combinations(range(len(props)), num_legs)))

            # Limit samples based on leg count to avoid timeout
            sample_limit = min(max_combinations // max(1, num_legs - 2), total_combos)

            if total_combos > sample_limit:
                # Random sampling for large combo sets
                indices_list = random.sample(list(itertools.combinations(range(len(props)), num_legs)), sample_limit)
                combinations = [[props[i] for i in indices] for indices in indices_list]
            else:
                combinations = list(itertools.combinations(props, num_legs))

            # Check each combination
            for combo in combinations:
                combo_list = list(combo)
                parlay_odds = self.calculate_parlay_odds(combo_list)
                odds_distance = abs(parlay_odds - target_odds)

                if odds_distance <= tolerance:
                    valid_parlays.append(combo_list)
                else:
                    # Track closest parlays for fallback (keep only top 10)
                    if len(closest_parlays) < 10:
                        closest_parlays.append((combo_list, odds_distance))
                        closest_parlays.sort(key=lambda x: x[1])
                    elif odds_distance < closest_parlays[-1][1]:
                        closest_parlays[-1] = (combo_list, odds_distance)
                        closest_parlays.sort(key=lambda x: x[1])

        # If no parlays found within tolerance, return closest 5
        if not valid_parlays and closest_parlays:
            valid_parlays = [p[0] for p in closest_parlays[:5]]

        return valid_parlays

    def generate_parlay(
        self,
        all_props: List[Dict],
        target_odds: int = 400,
        safety_level: str = "moderate",
        game_filter: str = "any",
        selected_games: Optional[List[str]] = None,
        num_suggestions: int = 1,
        min_legs: int = 2,
        max_legs: int = 6
    ) -> List[Dict]:
        """
        Generate parlay suggestions

        Args:
            all_props: All available props with odds and trust scores
            target_odds: Target American odds (e.g., +400)
            safety_level: 'conservative', 'moderate', or 'aggressive'
            game_filter: 'any', 'single', or 'specific'
            selected_games: List of game IDs if game_filter='specific'
            num_suggestions: Number of parlay suggestions to return
            min_legs: Minimum number of legs in parlay (default 2)
            max_legs: Maximum number of legs in parlay (default 6)

        Returns:
            List of parlay suggestions, each with legs and metadata
        """
        # Get trust threshold for safety level
        min_trust = self.safety_thresholds.get(safety_level, 60.0)

        # Filter props by trust score
        trusted_props = self.filter_props_by_trust(all_props, min_trust)

        if not trusted_props:
            return [{
                "error": f"No props found with trust score >= {min_trust}%",
                "suggestion": f"Try lowering safety level or adjusting filters"
            }]

        # Filter by game selection
        filtered_props = self.filter_props_by_game(
            trusted_props,
            game_filter,
            selected_games
        )

        if not filtered_props:
            return [{
                "error": "No props found matching game filter",
                "suggestion": "Try different game selection"
            }]

        # Sort props by trust score (descending) for better combinations
        filtered_props.sort(key=lambda x: x.get('trust_score', 0), reverse=True)

        # Find valid parlay combinations
        valid_parlays = self.find_parlay_combinations(
            filtered_props,
            target_odds=target_odds,
            min_legs=min_legs,
            max_legs=max_legs
        )

        if not valid_parlays:
            # Calculate what's needed
            avg_trust = sum(p['trust_score'] for p in filtered_props[:5]) / min(5, len(filtered_props))
            return [{
                "error": f"Could not find parlay matching +{target_odds} odds",
                "suggestion": f"With {safety_level} safety ({min_trust}%+ trust), try lowering target odds or increasing max legs",
                "available_props": len(filtered_props),
                "avg_trust": round(avg_trust, 1)
            }]

        # Sort parlays by average trust score
        valid_parlays.sort(
            key=lambda parlay: self.calculate_parlay_trust(parlay, "average"),
            reverse=True
        )

        # Randomize selection from top parlays to give variety
        # Take from top 50% of parlays to maintain quality but add variety
        selection_pool_size = max(num_suggestions * 3, min(len(valid_parlays), 20))
        selection_pool = valid_parlays[:selection_pool_size]

        # Randomly select from the pool
        if len(selection_pool) > num_suggestions:
            selected_parlays = random.sample(selection_pool, num_suggestions)
        else:
            selected_parlays = selection_pool

        # Build suggestions
        suggestions = []
        for parlay in selected_parlays:
            parlay_odds = self.calculate_parlay_odds(parlay)
            avg_trust = self.calculate_parlay_trust(parlay, "average")
            true_win_rate = self.calculate_parlay_trust(parlay, "probability")

            suggestions.append({
                "legs": parlay,
                "num_legs": len(parlay),
                "parlay_odds": parlay_odds,
                "parlay_odds_display": f"+{parlay_odds}" if parlay_odds > 0 else str(parlay_odds),
                "avg_trust": avg_trust,
                "true_win_rate": true_win_rate,
                "safety_level": safety_level,
                "payout_per_dollar": round(self.american_to_decimal(parlay_odds), 2)
            })

        return suggestions


# Example usage and testing
if __name__ == "__main__":
    # Mock some props for testing
    mock_props = [
        {"player_name": "LeBron James", "stat_type": "Points", "line": 24.5, "odds": -120, "trust_score": 72, "team": "LAL", "opponent": "GSW"},
        {"player_name": "Giannis Antetokounmpo", "stat_type": "Rebounds", "line": 11.5, "odds": -130, "trust_score": 68, "team": "MIL", "opponent": "BKN"},
        {"player_name": "Luka Doncic", "stat_type": "Assists", "line": 8.5, "odds": -115, "trust_score": 65, "team": "DAL", "opponent": "PHX"},
        {"player_name": "Nikola Jokic", "stat_type": "Points", "line": 26.5, "odds": -125, "trust_score": 70, "team": "DEN", "opponent": "LAC"},
        {"player_name": "Stephen Curry", "stat_type": "3PM", "line": 4.5, "odds": -110, "trust_score": 63, "team": "GSW", "opponent": "LAL"},
    ]

    builder = ParlayBuilder()

    print("=" * 60)
    print("PARLAY BUILDER TEST")
    print("=" * 60)

    # Test 1: Generate moderate safety parlay targeting +400
    print("\n[Test 1] Moderate safety, +400 target")
    suggestions = builder.generate_parlay(
        mock_props,
        target_odds=400,
        safety_level="moderate",
        game_filter="any",
        num_suggestions=3
    )

    for i, parlay in enumerate(suggestions, 1):
        if "error" in parlay:
            print(f"\nParlay {i}: {parlay['error']}")
            print(f"  Suggestion: {parlay['suggestion']}")
        else:
            print(f"\nParlay {i}: {parlay['parlay_odds_display']} odds")
            print(f"  Avg Trust: {parlay['avg_trust']}%")
            print(f"  True Win Rate: {parlay['true_win_rate']}%")
            print(f"  Legs ({parlay['num_legs']}):")
            for leg in parlay['legs']:
                print(f"    - {leg['player_name']} {leg['stat_type']} O{leg['line']} ({leg['odds']}) | Trust: {leg['trust_score']}%")

    print("\n" + "=" * 60)
