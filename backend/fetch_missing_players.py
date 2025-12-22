"""
Fetch data for players with special characters that were previously missing
"""
import sys
import io
from nba_stats_fetcher import NBAStatsFetcher
import pandas as pd

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Players to fetch
missing_players = [
    {"name": "Luka Dončić", "team": "DAL", "position": "PG"},
    {"name": "Nikola Jokić", "team": "DEN", "position": "C"},
    {"name": "Nikola Vučević", "team": "CHI", "position": "C"},
]

fetcher = NBAStatsFetcher()
all_games = []

print("=" * 60)
print("FETCHING DATA FOR PREVIOUSLY MISSING PLAYERS")
print("=" * 60)

for idx, player in enumerate(missing_players, 1):
    print(f"\n[{idx}/{len(missing_players)}] Processing {player['name']}...")

    games = fetcher.fetch_player_season(
        player['name'],
        player['team'],
        player['position'],
        season="2024-25"
    )

    all_games.extend(games)

    if games:
        print(f"[SUCCESS] Added {len(games)} games for {player['name']}")
    else:
        print(f"[WARNING] No games found for {player['name']}")

# Save to CSV
if all_games:
    df = pd.DataFrame(all_games)
    df = df.sort_values(['player_name', 'date'], ascending=[True, False])

    output_file = "data/missing_players_stats.csv"
    df.to_csv(output_file, index=False)

    print(f"\n{'=' * 60}")
    print(f"[SUCCESS] Saved {len(all_games)} games to {output_file}")
    print(f"{'=' * 60}")
    print(f"\nBreakdown by player:")
    print(df.groupby('player_name').size())
    print(f"\nDate Range: {df['date'].min()} to {df['date'].max()}")
else:
    print("\n[ERROR] No game data collected")
