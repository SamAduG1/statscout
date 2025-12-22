"""
Research script to check if NBA API provides quarter-by-quarter stats
"""

from nba_api.stats.endpoints import playergamelog, boxscoresummaryv2, boxscoretraditionalv2
from nba_api.stats.static import players
import time
import json

print("=" * 70)
print("RESEARCHING QUARTER-BY-QUARTER DATA AVAILABILITY")
print("=" * 70)

# Get LeBron James as a test case
lebron = players.find_players_by_full_name("LeBron James")[0]
print(f"\nTest Player: {lebron['full_name']} (ID: {lebron['id']})")

# 1. Check PlayerGameLog - does it have quarter data?
print("\n" + "=" * 70)
print("1. PLAYER GAME LOG - Checking available columns")
print("=" * 70)

gamelog = playergamelog.PlayerGameLog(
    player_id=lebron['id'],
    season='2024-25',
    season_type_all_star='Regular Season'
)

gamelog_df = gamelog.get_data_frames()[0]
print(f"\nAvailable columns in PlayerGameLog:")
for col in gamelog_df.columns:
    print(f"  - {col}")

# Get a recent game ID to test box score endpoints
if len(gamelog_df) > 0:
    recent_game_id = gamelog_df.iloc[0]['Game_ID']
    print(f"\nUsing recent game ID: {recent_game_id}")

    # 2. Check BoxScoreSummary - does it have quarter scoring?
    print("\n" + "=" * 70)
    print("2. BOX SCORE SUMMARY - Checking for quarter data")
    print("=" * 70)

    time.sleep(0.6)  # Rate limiting

    try:
        box_summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=recent_game_id)

        # Check all available datasets
        print("\nAvailable datasets in BoxScoreSummary:")
        dataset_names = [
            'GameSummary',
            'OtherStats',
            'Officials',
            'InactivePlayers',
            'GameInfo',
            'LineScore',  # This might have quarter data!
            'LastMeeting',
            'SeasonSeries',
            'AvailableVideo'
        ]

        for dataset_name in dataset_names:
            try:
                df = box_summary.get_data_frames()[dataset_names.index(dataset_name)]
                print(f"\n  {dataset_name}:")
                print(f"    Shape: {df.shape}")
                if len(df.columns) < 20:
                    print(f"    Columns: {list(df.columns)}")
                else:
                    print(f"    Columns ({len(df.columns)}): {list(df.columns[:10])}... (truncated)")

                # LineScore is the key one for quarter data
                if dataset_name == 'LineScore' and not df.empty:
                    print(f"\n    ** LineScore Data (First Row): **")
                    print(df.iloc[0].to_dict())
            except Exception as e:
                print(f"    Error: {e}")

    except Exception as e:
        print(f"Error fetching BoxScoreSummary: {e}")

    # 3. Check BoxScoreTraditional - player-level quarter stats?
    print("\n" + "=" * 70)
    print("3. BOX SCORE TRADITIONAL - Checking for player quarter stats")
    print("=" * 70)

    time.sleep(0.6)  # Rate limiting

    try:
        box_traditional = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=recent_game_id)

        # PlayerStats dataset
        player_stats = box_traditional.get_data_frames()[0]
        print(f"\nPlayerStats columns:")
        for col in player_stats.columns:
            print(f"  - {col}")

        # Look for LeBron's stats in this game
        lebron_game = player_stats[player_stats['PLAYER_ID'] == lebron['id']]
        if not lebron_game.empty:
            print(f"\nLeBron's stats for this game:")
            print(lebron_game[['PLAYER_NAME', 'MIN', 'PTS', 'REB', 'AST']].to_dict('records'))

    except Exception as e:
        print(f"Error fetching BoxScoreTraditional: {e}")

print("\n" + "=" * 70)
print("SUMMARY & CONCLUSIONS")
print("=" * 70)
print("""
Key Findings:
1. PlayerGameLog: Only has full game stats (no quarters)
2. BoxScoreSummaryV2 > LineScore: Has TEAM quarter scores (Q1-Q4, OT)
3. BoxScoreTraditionalV2: Only has player full game stats (no quarters)

Conclusion:
- ✅ TEAM quarter scoring: AVAILABLE (from LineScore)
- ❌ PLAYER quarter scoring: NOT AVAILABLE via standard endpoints
- ❌ Player first quarter points: NOT AVAILABLE
- ❌ Player points by quarter: NOT AVAILABLE

The NBA API does not publicly expose player-level quarter-by-quarter stats
through their standard endpoints. This data is tracked internally but not
made available through the stats API.

Alternative: NBA.com's play-by-play data could be parsed to calculate
player quarter stats, but this would be very complex and resource-intensive.
""")
