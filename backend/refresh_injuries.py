"""
Manually refresh injury data
"""
from espn_injury_tracker import ESPNInjuryTracker

print("=" * 60)
print("MANUAL INJURY DATA REFRESH")
print("=" * 60)

tracker = ESPNInjuryTracker()
tracker.clear_cache()
print("\nCache cleared, fetching fresh data...")

injuries = tracker.get_all_injuries()

print(f"\n{'=' * 60}")
print(f"Total injuries found: {len(injuries)}")
print(f"{'=' * 60}")

print("\nKey injuries to verify:")
key_players = ['Domantas Sabonis', 'Zach LaVine', 'Anthony Davis', 'Brandon Williams']
for name in key_players:
    status = tracker.get_player_status(name)
    if status:
        print(f"  {name}: {status['status']} ({status['team']}) - {status['injury']}")
    else:
        print(f"  {name}: ACTIVE (No injury report)")

print("\n" + "=" * 60)
print("REFRESH COMPLETE")
print("=" * 60)
