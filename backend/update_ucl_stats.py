"""
Champions League player stats from ESPN (free, no key).

For every UCL club:
  - big-5 clubs: adds their UCL games to the existing Understat players
    (matched by name within the club; espn_id is stored once matched)
  - other clubs (PSV, Benfica, Galatasaray, ...): creates ESPN-only players
    (league='ucl', understat_id=-espn_id) and also loads their domestic league
    games so samples are comparable to the big-5 Understat history

Rows are tagged in SoccerPlayerGame.competition ('ucl' / 'domestic') so the
domestic-league props keep using Understat rows only (competition IS NULL).
ESPN has no xG/xA/key passes; those stay NULL/0 for ESPN rows.

Usage:
  cd backend
  python update_ucl_stats.py                 # current season (last 3 weeks once data exists)
  python update_ucl_stats.py --full          # re-scan the whole current season
  python update_ucl_stats.py --prev-season   # redo last season's domestic games for
                                             # non-big-5 clubs (runs automatically
                                             # the first time)
"""

import re
import time
import argparse
import difflib
import requests
from datetime import date, timedelta

from dotenv import load_dotenv
load_dotenv()

from models import get_engine, get_session, init_db, SoccerPlayer, SoccerPlayerGame
from soccer_fetcher import _norm, _fuzzy_team_match

ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer"
SEASON = 2026  # 2026-27, same convention as populate_soccer_players.SEASON
UCL_SLUGS = {"uefa.champions", "uefa.champions_qual"}
BIG5_SLUGS = {"eng.1": "pl", "esp.1": "laliga", "ger.1": "bundesliga",
              "ita.1": "seriea", "fra.1": "ligue1"}

# ESPN club name -> Understat team name, where token matching can't tell
ESPN_TO_UNDERSTAT = {
    "Internazionale": "Inter",
    "RB Leipzig": "RasenBallsport Leipzig",
    "Borussia Monchengladbach": "Borussia M.Gladbach",
}

# Manual fixes for players the name matcher gets wrong: espn_id -> understat_id
PLAYER_OVERRIDES = {}


def _get(path, **params):
    for attempt in range(3):
        try:
            r = requests.get(f"{ESPN}/{path}", params=params, timeout=20)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"ESPN request failed: {path} {params}")


def _name_key(name):
    return " ".join(re.sub(r"[^a-z ]", " ", _norm(name).lower().replace("-", " ")).split())


def _norm_position(abbr):
    a = (abbr or "").upper()
    if not a or a == "SUB":
        return None
    if a.startswith("G"):
        return "GK"
    if a.startswith("D") or a.endswith("B") or a.startswith("CD") or a == "SW":
        return "DF"
    if "M" in a:
        return "MF"
    return "FW"


def _minute(clock):
    """"65'" -> 65, "90'+3'" -> 93"""
    nums = [int(n) for n in re.findall(r"\d+", (clock or {}).get("displayValue", ""))]
    return sum(nums[:2]) if nums else None


# ── Team / player resolution ────────────────────────────────────────────────

def resolve_understat_team(espn_name, understat_teams):
    if espn_name in ESPN_TO_UNDERSTAT:
        return ESPN_TO_UNDERSTAT[espn_name]
    by_key = {_name_key(t): t for t in understat_teams}
    if _name_key(espn_name) in by_key:
        return by_key[_name_key(espn_name)]
    return _fuzzy_team_match(espn_name, understat_teams)


def match_player(espn_name, candidates):
    """Find the Understat player for an ESPN name among one club's players.
    Returns None unless exactly one candidate is a confident match."""
    want = _name_key(espn_name)
    want_toks = want.split()
    keyed = [(_name_key(p.name), p) for p in candidates]

    exact = [p for k, p in keyed if k == want]
    if len(exact) == 1:
        return exact[0]

    # "Gabriel" vs "Gabriel Magalhaes", "Vinicius Junior" vs "Vinicius Jose Paixao de Oliveira Junior"
    subset = [p for k, p in keyed
              if set(k.split()) <= set(want_toks) or set(want_toks) <= set(k.split())]
    if len(subset) == 1:
        return subset[0]

    # Same surname + first initial ("Kai Havertz" vs "K. Havertz")
    if len(want_toks) >= 2:
        sur = [p for k, p in keyed
               if k.split() and k.split()[-1] == want_toks[-1] and k[0] == want[0]]
        if len(sur) == 1:
            return sur[0]

    # Surname alone when it's unique in the squad ("Rayan Cherki" vs Understat "Mathis Cherki")
    if len(want_toks) >= 2:
        sur = [p for k, p in keyed if k.split() and k.split()[-1] == want_toks[-1]]
        if len(sur) == 1:
            return sur[0]

    scored = sorted(((difflib.SequenceMatcher(None, want, k).ratio(), p) for k, p in keyed),
                    key=lambda x: -x[0])
    if scored and scored[0][0] >= 0.85 and (len(scored) == 1 or scored[1][0] < scored[0][0] - 0.05):
        return scored[0][1]
    return None


# ── ESPN parsing ────────────────────────────────────────────────────────────

def parse_event(summary, espn_team_id, positions=None):
    """Per-player rows for one team in one completed match."""
    comp = summary["header"]["competitions"][0]
    status = comp["status"]["type"]
    if not status.get("completed"):
        return None
    full = 120 if "AET" in (status.get("detail") or "") or "Pen" in (status.get("detail") or "") else 90
    teams = {c["team"]["id"]: c for c in comp["competitors"]}
    me = teams.get(str(espn_team_id))
    opp = next((c for tid, c in teams.items() if tid != str(espn_team_id)), None)
    if not me or not opp:
        return None

    sub_in, sub_out, sent_off = {}, {}, {}
    for k in summary.get("keyEvents", []):
        kind = k.get("type", {}).get("type", "")
        ids = [p["athlete"]["id"] for p in k.get("participants", []) if p.get("athlete")]
        minute = _minute(k.get("clock"))
        if kind == "substitution" and len(ids) >= 2 and minute is not None:
            sub_in[ids[0]] = minute
            sub_out[ids[1]] = minute
        elif "red" in kind and ids and minute is not None:
            sent_off[ids[0]] = minute

    roster = next((r for r in summary.get("rosters", [])
                   if str(r.get("team", {}).get("id")) == str(espn_team_id)), None)
    if not roster:
        return None

    rows = []
    for p in roster.get("roster", []):
        aid = p["athlete"]["id"]
        if not p.get("starter") and not p.get("subbedIn"):
            continue
        start = 0 if p.get("starter") else sub_in.get(aid)
        if start is None:
            continue
        end = min(x for x in (sub_out.get(aid) if p.get("subbedOut") else None,
                              sent_off.get(aid), full) if x is not None)
        minutes = max(1, min(end, full) - start)
        stats = {s["name"]: s.get("value") or 0 for s in p.get("stats", [])}
        # Squad position first: match-day position is "SUB" for substitutes
        position = ((positions or {}).get(aid)
                    or _norm_position((p.get("position") or {}).get("abbreviation")) or "MF")
        rows.append({
            "espn_id": int(aid),
            "name": p["athlete"]["displayName"],
            "position": position,
            "venue": me.get("homeAway", "home"),
            "opponent": opp["team"]["displayName"],
            "goals": int(stats.get("totalGoals", 0)),
            "shots": int(stats.get("totalShots", 0)),
            "shots_on_target": int(stats.get("shotsOnTarget", 0)),
            "assists": int(stats.get("goalAssists", 0)),
            "minutes": minutes,
            "goals_conceded": int(opp.get("score") or 0) if position == "GK" else None,
        })
    return rows


# ── Ingest ──────────────────────────────────────────────────────────────────

def club_events(espn_team_id, season, big5):
    """Completed events to ingest for a club: UCL always; domestic league for non-big-5."""
    sched = _get(f"all/teams/{espn_team_id}/schedule", season=season)
    events = []
    for e in sched.get("events", []):
        if (e.get("season") or {}).get("year") != season:
            continue
        slug = (e.get("league") or {}).get("slug", "") if isinstance(e.get("league"), dict) else ""
        if slug in UCL_SLUGS:
            comp = "ucl"
        elif not big5 and slug.endswith(".1"):
            comp = "domestic"
        else:
            continue
        status = e["competitions"][0]["status"]["type"]
        if status.get("completed"):
            events.append((e["id"], slug, e["date"][:10], comp))
    return events


def ingest(session, season=SEASON, domestic_only=False, since=None):
    """since: only look at events on/after this ISO date (None = whole season).
    Re-seen events are harmless: rows are skipped per (player, date)."""
    init_db(session.get_bind())  # make sure espn_id / competition columns exist
    clubs = _get("uefa.champions/teams")["sports"][0]["leagues"][0]["teams"]
    understat_teams = sorted({t for (t,) in session.query(SoccerPlayer.team_name)
                              .filter(SoccerPlayer.league != "ucl").distinct()})
    summaries = {}
    totals = {"rows": 0, "matched": 0, "created": 0, "unmatched": []}

    for c in clubs:
        team = c["team"]
        espn_name, espn_tid = team["displayName"], team["id"]

        # Domestic slug decides whether Understat already covers this club
        sched = _get(f"all/teams/{espn_tid}/schedule", season=SEASON)
        slugs = [(e.get("league") or {}).get("slug", "") for e in sched.get("events", [])
                 if isinstance(e.get("league"), dict)]
        dom = next((s for s in slugs if s in BIG5_SLUGS), None)
        big5 = dom is not None

        if big5:
            if domestic_only:
                continue
            team_name = resolve_understat_team(espn_name, understat_teams)
            if not team_name:
                print(f"  [SKIP] {espn_name}: no Understat team match — add to ESPN_TO_UNDERSTAT")
                continue
            league = BIG5_SLUGS[dom]
        else:
            team_name, league = espn_name, "ucl"

        club_players = session.query(SoccerPlayer).filter_by(team_name=team_name).all()
        squad = _get(f"uefa.champions/teams/{espn_tid}/roster").get("athletes", [])
        positions = {a["id"]: _norm_position((a.get("position") or {}).get("abbreviation"))
                     for a in squad}
        events = club_events(espn_tid, season, big5)
        if domestic_only:
            events = [e for e in events if e[3] == "domestic"]

        if since:
            events = [e for e in events if e[2] >= since]

        new_rows = 0
        for event_id, slug, ev_date, comp in events:
            if event_id not in summaries:
                summaries[event_id] = _get(f"{slug}/summary", event=event_id)
                time.sleep(0.2)
            rows = parse_event(summaries[event_id], espn_tid, positions) or []
            for r in rows:
                if domestic_only:
                    # Backfill only ESPN-only players still at this club, so a player who
                    # has since joined a big-5 side doesn't get his old league's games
                    player = next((p for p in club_players
                                   if p.espn_id == r["espn_id"] and p.understat_id < 0), None)
                else:
                    player = resolve_or_create(session, r, club_players, team_name, league, big5, totals)
                if not player:
                    continue
                match_date = date.fromisoformat(ev_date)
                if session.query(SoccerPlayerGame).filter_by(player_id=player.id,
                                                             match_date=match_date).first():
                    continue
                session.add(SoccerPlayerGame(
                    player_id=player.id, match_date=match_date,
                    opponent=r["opponent"], venue=r["venue"],
                    goals=r["goals"], shots=r["shots"], shots_on_target=r["shots_on_target"],
                    assists=r["assists"], key_passes=0, minutes_played=r["minutes"],
                    xG=None, xA=None, goals_conceded=r["goals_conceded"],
                    season=str(season), competition=comp,
                ))
                new_rows += 1
        # ESPN-only players follow the club's current squad (late transfers between
        # non-big-5 clubs); Understat-backed players keep their Understat team
        if not domestic_only:
            moved = (session.query(SoccerPlayer)
                     .filter(SoccerPlayer.espn_id.in_([int(i) for i in positions]),
                             SoccerPlayer.understat_id < 0,
                             SoccerPlayer.team_name != team_name)
                     .update({SoccerPlayer.team_name: team_name, SoccerPlayer.league: league},
                             synchronize_session=False))
            if moved:
                print(f"    {moved} player(s) moved to {team_name}")
        session.commit()
        totals["rows"] += new_rows
        print(f"  {espn_name:<24} -> {team_name:<24} [{league}] {len(events)} new events, {new_rows} rows")

    print(f"\nUCL ingest: {totals['rows']} rows, {totals['matched']} players linked, "
          f"{totals['created']} ESPN-only players created")
    if totals["unmatched"]:
        print(f"Big-5 players with no Understat match (created as ESPN-only, "
              f"add to PLAYER_OVERRIDES if wrong): {len(totals['unmatched'])}")
        for u in totals["unmatched"]:
            print(f"    {u}")
    return totals


def resolve_or_create(session, r, club_players, team_name, league, big5, totals):
    espn_id = r["espn_id"]
    player = session.query(SoccerPlayer).filter_by(espn_id=espn_id).first()
    if player:
        return player

    if big5:
        if espn_id in PLAYER_OVERRIDES:
            player = session.query(SoccerPlayer).filter_by(understat_id=PLAYER_OVERRIDES[espn_id]).first()
        else:
            player = match_player(r["name"], [p for p in club_players if p.espn_id is None])
            if not player:
                # Late transfer Understat hasn't caught up with: name unique across big 5
                same = (session.query(SoccerPlayer)
                        .filter(SoccerPlayer.league != "ucl", SoccerPlayer.espn_id.is_(None),
                                SoccerPlayer.understat_id > 0).all())
                hits = [p for p in same if _name_key(p.name) == _name_key(r["name"])]
                if not hits and len(_name_key(r["name"]).split()) >= 2:
                    # "Jonathan David" vs "Jonathan Christian David"
                    want = set(_name_key(r["name"]).split())
                    hits = [p for p in same if want <= set(_name_key(p.name).split())]
                player = hits[0] if len(hits) == 1 else None
        if player:
            player.espn_id = espn_id
            totals["matched"] += 1
            return player
        totals["unmatched"].append(f"{r['name']} ({team_name}, espn {espn_id})")

    player = session.query(SoccerPlayer).filter_by(understat_id=-espn_id).first()
    if player:
        player.espn_id = espn_id
        return player
    player = SoccerPlayer(
        understat_id=-espn_id, espn_id=espn_id, name=r["name"], team_name=team_name,
        league=league, position=r["position"], last_updated=date.today(),
    )
    session.add(player)
    session.flush()
    club_players.append(player)
    totals["created"] += 1
    return player


def main(prev_season=False, full=False):
    session = get_session(get_engine())
    try:
        print(f"=== Champions League {SEASON}-{(SEASON + 1) % 100:02d} (ESPN) ===")
        have_rows = (session.query(SoccerPlayerGame.id)
                     .filter(SoccerPlayerGame.competition.isnot(None),
                             SoccerPlayerGame.season == str(SEASON)).first())
        # Weekly runs re-scan the last 3 weeks; first run takes the whole season
        since = (date.today() - timedelta(days=21)).isoformat() if have_rows and not full else None
        ingest(session, SEASON, since=since)
        have_prev = (session.query(SoccerPlayerGame.id)
                     .filter(SoccerPlayerGame.competition == "domestic",
                             SoccerPlayerGame.season == str(SEASON - 1)).first())
        if prev_season or not have_prev:
            print(f"\n=== Non-big-5 UCL clubs: {SEASON - 1} domestic backfill ===")
            ingest(session, SEASON - 1, domestic_only=True)
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prev-season", action="store_true")
    parser.add_argument("--full", action="store_true", help="re-scan the whole season")
    args = parser.parse_args()
    main(prev_season=args.prev_season, full=args.full)
