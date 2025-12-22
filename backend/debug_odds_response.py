"""Debug script to see raw Odds API response structure"""
import json
from odds_api import OddsAPIClient

client = OddsAPIClient()
response = client.get_all_player_props(markets='player_points')

print('Success:', response.get('success'))
print('Events count:', response.get('events_count'))

# Look at the first event structure
events = response.get('data', [])
if events:
    first_event = events[0]
    print('\n=== FIRST EVENT STRUCTURE ===')
    print(json.dumps(first_event, indent=2))

    # Check if bookmakers exist
    bookmakers = first_event.get('bookmakers', [])
    print(f'\nBookmakers in first event: {len(bookmakers)}')

    if bookmakers:
        first_bookmaker = bookmakers[0]
        print('\n=== FIRST BOOKMAKER ===')
        print(json.dumps(first_bookmaker, indent=2))
