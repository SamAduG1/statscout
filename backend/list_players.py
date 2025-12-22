from db_loader import DatabaseLoader

loader = DatabaseLoader()
players = loader.get_player_names()

print(f"Total players in database: {len(players)}\n")
print("All players:")
print("=" * 60)
for idx, player in enumerate(players, 1):
    print(f"{idx}. {player}")

loader.close()
