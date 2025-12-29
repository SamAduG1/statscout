"""
Search for a player in the NBA API to find the correct ID
"""
from nba_api.stats.static import players as nba_players

# Get all NBA players
all_players = nba_players.get_players()

# Get all active players and print those with special characters
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=== Players with 'Krej' in name ===")
for p in all_players:
    if 'krej' in p['full_name'].lower():
        print(f"  {p['full_name']} (ID: {p['id']}, Active: {p.get('is_active')})")

print("\n=== Players with 'Diabat' in name ===")
for p in all_players:
    if 'diabat' in p['full_name'].lower():
        print(f"  {p['full_name']} (ID: {p['id']}, Active: {p.get('is_active')})")

print("\n=== Players with 'Sala' in name ===")
for p in all_players:
    if 'sala' in p['full_name'].lower() and p.get('is_active'):
        print(f"  {p['full_name']} (ID: {p['id']}, Active: {p.get('is_active')})")

print("\n=== Players with 'Dem' in name ===")
for p in all_players:
    if 'dem' in p['full_name'].lower() and p.get('is_active'):
        print(f"  {p['full_name']} (ID: {p['id']}, Active: {p.get('is_active')})")

print("\n=== Players with 'Bogdan' in name ===")
for p in all_players:
    if 'bogdan' in p['full_name'].lower():
        print(f"  {p['full_name']} (ID: {p['id']}, Active: {p.get('is_active')})")
