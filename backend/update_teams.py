"""
Update team information for players who have been traded or signed
"""
from models import get_engine, get_session, Player
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("UPDATING PLAYER TEAM INFORMATION")
print("=" * 60)

engine = get_engine()
session = get_session(engine)

# Players to update: (name, new_team)
updates = [
    ("Bogdan Bogdanović", "LAC")
]

updated_count = 0
not_found_count = 0

for player_name, new_team in updates:
    player = session.query(Player).filter(Player.name == player_name).first()

    if player:
        old_team = player.team
        player.team = new_team
        print(f"[OK] Updated {player_name}: {old_team} -> {new_team}")
        updated_count += 1
    else:
        print(f"[ERROR] Player not found: {player_name}")
        not_found_count += 1

session.commit()
session.close()

print("\n" + "=" * 60)
print(f"COMPLETE - Updated {updated_count} players")
if not_found_count > 0:
    print(f"WARNING - {not_found_count} players not found in database")
print("=" * 60)
