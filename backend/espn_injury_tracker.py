"""
ESPN Injury Tracker
Fetches injury data from ESPN's public API for NBA, MLB, and soccer.
"""
import requests
from datetime import datetime, timedelta
import time

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"

MLB_TEAMS = {
    'ARI': 29, 'ATL': 15, 'BAL': 1,  'BOS': 2,  'CHC': 16,
    'CWS': 4,  'CIN': 17, 'CLE': 5,  'COL': 27, 'DET': 6,
    'HOU': 18, 'KC':  7,  'LAA': 3,  'LAD': 19, 'MIA': 28,
    'MIL': 8,  'MIN': 9,  'NYM': 21, 'NYY': 10, 'OAK': 11,
    'PHI': 22, 'PIT': 23, 'SD':  25, 'SF':  26, 'SEA': 12,
    'STL': 24, 'TB':  30, 'TEX': 13, 'TOR': 14, 'WSH': 20,
}

# ESPN league codes and team IDs for soccer
SOCCER_LEAGUES = {
    'pl':         ('eng.1', {
        'ARS': 359, 'AVL': 1006, 'BOU': 349, 'BRE': 337, 'BHA': 331,
        'CHE': 363, 'CRY': 384, 'EVE': 368, 'FUL': 370, 'IPS': 382,
        'LEI': 375, 'LIV': 364, 'MCI': 382, 'MUN': 360, 'NEW': 361,
        'NFO': 393, 'SOU': 376, 'TOT': 367, 'WHU': 371, 'WOL': 380,
    }),
    'laliga':     ('esp.1', {}),   # team IDs can be added as needed
    'bundesliga': ('ger.1', {}),
    'seriea':     ('ita.1', {}),
    'ligue1':     ('fra.1', {}),
}


def _normalize_status(raw):
    s = (raw or '').lower()
    if 'out' in s:          return 'OUT'
    if 'questionable' in s: return 'QUESTIONABLE'
    if 'doubtful' in s:     return 'DOUBTFUL'
    if 'day-to-day' in s:   return 'DAY-TO-DAY'
    if 'il-' in s or 'injured list' in s: return 'OUT'
    return raw.upper() if raw else 'UNKNOWN'


def _parse_athletes(athletes, team_abbr):
    """Extract injured players from an ESPN roster athletes list."""
    result = {}
    for athlete in athletes:
        injuries_list = athlete.get('injuries', [])
        if not injuries_list:
            continue
        injury = injuries_list[0]
        name   = athlete.get('displayName', 'Unknown')
        status = _normalize_status(injury.get('status', ''))
        detail = (injury.get('longComment') or injury.get('shortComment') or 'Injury')
        result[name] = {
            'status':       status,
            'team':         team_abbr,
            'injury':       detail,
            'last_updated': datetime.now().isoformat(),
        }
    return result


class ESPNInjuryTracker:
    def __init__(self):
        # NBA
        self.cache = {}
        self.last_fetch = None
        # MLB
        self._mlb_cache = {}
        self._mlb_last_fetch = None
        self.cache_timeout = timedelta(hours=2)
        self.espn_base_url = f"{ESPN_BASE}/basketball/nba/teams"

    def _fetch_sport_injuries(self, sport_path, teams_dict, label):
        """Generic fetcher: sport_path e.g. 'baseball/mlb', teams_dict {abbr: espn_id}."""
        injuries = {}
        for team_abbr, team_id in teams_dict.items():
            try:
                url = f"{ESPN_BASE}/{sport_path}/teams/{team_id}/roster"
                r = requests.get(url, timeout=10)
                if r.status_code != 200:
                    continue
                athletes = r.json().get('athletes', [])
                # Soccer wraps athletes in position groups
                if athletes and isinstance(athletes[0], dict) and 'items' in athletes[0]:
                    flat = []
                    for group in athletes:
                        flat.extend(group.get('items', []))
                    athletes = flat
                injuries.update(_parse_athletes(athletes, team_abbr))
                time.sleep(0.05)
            except Exception as e:
                print(f"  [Injury/{label}] {team_abbr}: {e}")
        return injuries

    def get_all_injuries(self):
        """Fetch NBA injury data (2h cache). Returns {player_name: {...}}."""
        if self.last_fetch and (datetime.now() - self.last_fetch) < self.cache_timeout:
            return self.cache

        print("[Injury Tracker] Fetching NBA injuries from ESPN...")

        nba_teams = {
            'ATL': 1, 'BOS': 2, 'BKN': 17, 'CHA': 30, 'CHI': 4,
            'CLE': 5, 'DAL': 6, 'DEN': 7, 'DET': 8, 'GSW': 9,
            'HOU': 10, 'IND': 11, 'LAC': 12, 'LAL': 13, 'MEM': 29,
            'MIA': 14, 'MIL': 15, 'MIN': 16, 'NOP': 3, 'NYK': 18,
            'OKC': 25, 'ORL': 19, 'PHI': 20, 'PHX': 21, 'POR': 22,
            'SAC': 23, 'SAS': 24, 'TOR': 28, 'UTA': 26, 'WAS': 27,
        }

        injuries = {}
        try:
            injuries = self._fetch_sport_injuries('basketball/nba', nba_teams, 'NBA')
            for name, info in injuries.items():
                print(f"  [Injury] {name} ({info['team']}): {info['status']}")
        except Exception as e:
            print(f"[Injury Tracker] NBA fetch failed: {e}")
            return self.cache if self.cache else {}

        self.cache = injuries
        self.last_fetch = datetime.now()
        print(f"[Injury Tracker] NBA: {len(injuries)} injured players")
        return injuries

    # ------------------------------------------------------------------ MLB --

    def get_mlb_injuries(self):
        """Fetch MLB injury/IL data (2h cache). Returns {player_name: {...}}."""
        if self._mlb_last_fetch and (datetime.now() - self._mlb_last_fetch) < self.cache_timeout:
            return self._mlb_cache

        print("[Injury Tracker] Fetching MLB injuries from ESPN...")
        try:
            injuries = self._fetch_sport_injuries('baseball/mlb', MLB_TEAMS, 'MLB')
            self._mlb_cache = injuries
            self._mlb_last_fetch = datetime.now()
            print(f"[Injury Tracker] MLB: {len(injuries)} players on IL/injured")
            return injuries
        except Exception as e:
            print(f"[Injury Tracker] MLB fetch failed: {e}")
            return self._mlb_cache

    def get_mlb_player_status(self, player_name):
        """Return MLB injury dict for player, or None if active."""
        return self.get_mlb_injuries().get(player_name)

    def get_mlb_batch_status(self, player_names):
        """Return {player_name: status_dict} for a list of MLB players."""
        injuries = self.get_mlb_injuries()
        return {
            name: injuries.get(name, {'status': 'ACTIVE', 'team': None, 'injury': None})
            for name in player_names
        }

    # --------------------------------------------------------------- shared --

    def get_player_status(self, player_name):
        return self.get_all_injuries().get(player_name)

    def get_batch_status(self, player_names):
        injuries = self.get_all_injuries()
        return {
            name: injuries.get(name, {'status': 'ACTIVE', 'team': None, 'injury': None})
            for name in player_names
        }

    def is_player_out(self, player_name):
        status = self.get_player_status(player_name)
        return status['status'] in ['OUT', 'DOUBTFUL'] if status else False

    def clear_cache(self):
        self.cache = {}
        self.last_fetch = None

    def refresh_nba_data(self):
        self.clear_cache()
        return self.get_all_injuries()

    def set_manual_status(self, player_name, status):
        print(f"[Warning] Manual status setting not supported by ESPN tracker")


if __name__ == "__main__":
    # Test the injury tracker
    tracker = ESPNInjuryTracker()

    print("\n" + "=" * 60)
    print("ESPN INJURY TRACKER TEST")
    print("=" * 60)

    injuries = tracker.get_all_injuries()

    print(f"\nTotal injured players: {len(injuries)}")
    print("\nAll current injuries:")
    for player, info in sorted(injuries.items()):
        print(f"  {player:30} ({info['team']:3}) - {info['status']:12} - {info['injury']}")

    # Test specific player
    print("\n" + "=" * 60)
    test_player = "Jalen Brunson"
    status = tracker.get_player_status(test_player)
    if status:
        print(f"{test_player} Status: {status}")
    else:
        print(f"{test_player}: ACTIVE (No injury report)")
