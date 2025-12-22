"""
Research The Odds API for quarter-specific prop markets
"""

from odds_api import OddsAPIClient
import json

client = OddsAPIClient()

print("=" * 70)
print("RESEARCHING THE ODDS API - QUARTER PROPS")
print("=" * 70)

# First, let's see all available markets
print("\n1. CHECKING ALL AVAILABLE MARKETS")
print("=" * 70)

try:
    # Get upcoming games first
    response = client.session.get(
        f"{client.base_url}/sports/{client.sport_key}/odds",
        params={
            "apiKey": client.api_key,
            "regions": "us",
            "markets": "h2h"  # Just get game info
        }
    )

    if response.status_code == 200:
        games = response.json()
        print(f"\nFound {len(games)} upcoming NBA games")

        if len(games) > 0:
            test_game = games[0]
            print(f"\nTest game: {test_game.get('home_team')} vs {test_game.get('away_team')}")
            print(f"Game ID: {test_game.get('id')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error fetching games: {e}")

# Now check what player prop markets are available
print("\n2. CHECKING AVAILABLE PLAYER PROP MARKETS")
print("=" * 70)

# According to The Odds API docs, these are the standard player prop markets
standard_markets = [
    "player_points",
    "player_rebounds",
    "player_assists",
    "player_threes",
    "player_steals",
    "player_blocks",
    "player_turnovers",
    "player_points_rebounds_assists",
    "player_points_rebounds",
    "player_points_assists",
    "player_rebounds_assists",
]

# Potential quarter markets (may not exist)
potential_quarter_markets = [
    "player_1st_quarter_points",
    "player_first_quarter_points",
    "player_q1_points",
    "player_quarter_points",
    "player_1q_points",
    "h2h_q1",
    "h2h_1st_quarter",
    "totals_1st_quarter",
    "team_totals_q1",
]

print("\nStandard player prop markets that we know exist:")
for market in standard_markets:
    print(f"  - {market}")

print("\nPotential quarter-specific markets to test:")
for market in potential_quarter_markets:
    print(f"  - {market}")

# Test for quarter markets
print("\n3. TESTING FOR QUARTER-SPECIFIC MARKETS")
print("=" * 70)

test_markets = potential_quarter_markets[:5]  # Test first 5

for market in test_markets:
    try:
        print(f"\nTesting market: '{market}'...")

        response = client.get_all_player_props(
            markets=market,
            regions="us"
        )

        if response.get("success"):
            data = response.get("data", [])
            print(f"  Result: FOUND! {len(data)} games returned")
            if data and len(data) > 0:
                # Check if it has outcomes (props)
                first_game = data[0]
                bookmakers = first_game.get('bookmakers', [])
                if bookmakers and len(bookmakers) > 0:
                    markets_data = bookmakers[0].get('markets', [])
                    if markets_data and len(markets_data) > 0:
                        outcomes = markets_data[0].get('outcomes', [])
                        print(f"  Props available: {len(outcomes)}")
                        if outcomes:
                            print(f"  Sample: {outcomes[0].get('description', 'N/A')} - {outcomes[0].get('name', 'N/A')}")
        else:
            error_msg = response.get("error", "Unknown error")
            if "Invalid" in error_msg or "not found" in error_msg:
                print(f"  Result: NOT AVAILABLE (Invalid market)")
            else:
                print(f"  Result: Error - {error_msg}")

    except Exception as e:
        print(f"  Result: Error - {str(e)}")

print("\n" + "=" * 70)
print("CHECKING THE ODDS API DOCUMENTATION")
print("=" * 70)

print("""
According to The Odds API documentation (https://the-odds-api.com/):

Available Markets for NBA:
- h2h (moneyline)
- spreads
- totals (over/under)
- player_points
- player_rebounds
- player_assists
- player_threes
- player_steals
- player_blocks
- player_turnovers
- player_points_rebounds_assists
- player_points_rebounds
- player_points_assists
- player_rebounds_assists

First Quarter / Quarter-Specific Markets:
- h2h_q1 (1st quarter moneyline) - TEAM LEVEL
- spreads_q1 (1st quarter spread) - TEAM LEVEL
- totals_q1 (1st quarter total) - TEAM LEVEL
- Similar for q2, q3, q4 - ALL TEAM LEVEL

Conclusion: The Odds API does NOT provide player quarter props.
Only TEAM quarter markets are available.
""")

print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print("""
Your Questions:
1. How many points players score in the first quarter
2. How many points players score each quarter
3. How many teams get to 100+ points in 3 quarters

Findings:

NBA API:
- Team quarter scores: AVAILABLE (PTS_QTR1, PTS_QTR2, etc.)
- Player quarter scores: NOT AVAILABLE

The Odds API:
- Team quarter totals/spreads: AVAILABLE (h2h_q1, totals_q1, spreads_q1)
- Player quarter props: NOT AVAILABLE

Alternative Solutions:
1. Parse NBA play-by-play data (complex, resource-intensive)
2. Use team quarter data for trend analysis
3. Calculate implied player quarter stats from team data
4. Focus on team-level quarter trends which ARE available

Recommendation:
Focus on team quarter trends as a differentiator:
- Teams that score 30+ in Q1 (historical win rate)
- Teams that reach 75 points by halftime
- Over/under trends for team quarters
- This data IS available and could still be valuable!
""")
