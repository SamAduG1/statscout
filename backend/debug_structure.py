"""Debug to understand the data structure"""
from odds_api import OddsAPIClient

client = OddsAPIClient()

# Get events first
events_response = client.get_events()
print('Events response success:', events_response.get('success'))
print('Events count:', len(events_response.get('data', [])))

# Get props for first event
if events_response.get('success') and events_response.get('data'):
    first_event = events_response['data'][0]
    event_id = first_event.get('id')
    print(f'\nGetting props for event: {event_id}')

    props_response = client.get_player_props(event_id=event_id, markets='player_points')
    print('Props response success:', props_response.get('success'))
    if not props_response.get('success'):
        print('Error:', props_response.get('error'))
        print('Message:', props_response.get('message'))

    if props_response.get('success'):
        props_data = props_response.get('data', {})
        print(f'Props data type: {type(props_data)}')
        print(f'Props data keys: {list(props_data.keys()) if isinstance(props_data, dict) else "not a dict"}')

        # Check bookmakers
        bookmakers = props_data.get('bookmakers', []) if isinstance(props_data, dict) else []
        print(f'Bookmakers count: {len(bookmakers)}')

        if bookmakers:
            print(f'First bookmaker: {bookmakers[0].get("title", "?")}')
            markets = bookmakers[0].get('markets', [])
            print(f'Markets in first bookmaker: {len(markets)}')
