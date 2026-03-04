# StatScout — Codebase Reference

This document describes every file that **must exist** in the project, what it does, and
why removing it breaks the app. Keep this updated whenever you add or restructure files.

---

## ⚠️ DO NOT DELETE — Backend Core Files

These files are directly imported by `app.py` or by each other. Deleting any of them
crashes the backend on startup or silently breaks a feature.

### `backend/app.py`
The Flask web server. Every API route lives here (`/api/players`, `/api/calculate`,
`/api/admin/update-stats`, etc.). Imports **all** of the modules below.

### `backend/models.py`
SQLAlchemy ORM models (`Player`, `Game`, `TeamGame`) and the `get_engine()` /
`get_session()` helpers. Every file that touches the database imports from here.

### `backend/db_loader.py`
`DatabaseLoader` class. Loads all player + game data from the DB in bulk (2 queries
instead of ~2000). Used by `app.py` for the cache build. Contains `get_all_players_bulk()`
which returns players, stats, and game dates in one shot.

### `backend/calculator.py`
`StatScoutCalculator` class. Takes raw game stats and a betting line and computes:
hit rate, trust score, recent form, streak, opponent difficulty, and the full
`analyze_player_prop()` result that every player card is built from.

### `backend/espn_recent_games_scraper.py`
`ESPNAPIClient` class. Fetches NBA scoreboards and box scores from ESPN's unofficial
API (`site.api.espn.com`). Used by `update_stats.py` to pull recent game data.
**This file was accidentally deleted in Feb 2026 — restoring it required git archaeology.
Do not delete it again.**

### `backend/nba_stats_fetcher.py`
`NBAStatsFetcher` class. Pulls historical season game logs from the official NBA stats
API (`nba_api` library). Used by `update_stats.py` for full-season refreshes.
**Also accidentally deleted in Feb 2026 alongside the above. Same warning applies.**

### `backend/update_stats.py`
Orchestrates database updates. Contains:
- `add_espn_recent_games(session, days_back)` — fetches the last N days from ESPN and
  inserts any new games. Called by the Refresh Stats button (`/api/admin/update-stats`).
- `update_all_players()` — full season sync via nba_api. Called by the daily scheduler.
- `_build_player_name_map()` / `_lookup_player()` — fuzzy name matching so ESPN names
  like "PJ Washington" map correctly to nba_api names like "P.J. Washington".

### `backend/espn_injury_tracker.py`
`ESPNInjuryTracker` class. Scrapes injury status for all NBA players from ESPN.
Used during Phase 2 of the cache build to tag each player prop with their injury status
(ACTIVE, QUESTIONABLE, OUT, etc.).

### `backend/nba_schedule_fetcher.py`
`NBAScheduleFetcher` class. Fetches the upcoming NBA schedule from ESPN's API and
returns each team's next game (opponent, home/away, date/time). Used to populate the
opponent and game date fields on every player card. Caches results for 1 hour.

### `backend/odds_api.py`
`OddsAPIClient` class. Connects to The Odds API to fetch real bookmaker lines for NBA
player props. Lines are cached for 4 hours to conserve API quota. If no real line is
available, a calculated line is used as a fallback.

### `backend/scheduler.py`
`init_scheduler()` function. Sets up an APScheduler background job that runs
`update_all_players()` every day at 8 AM to keep stats current automatically.

### `backend/team_quarter_analytics.py`
`TeamQuarterAnalytics` class. Calculates quarter-by-quarter scoring averages,
win correlations, and head-to-head matchup breakdowns. Powers the
`/api/quarters/matchup` endpoint.

### `backend/parlay_builder.py`
`ParlayBuilder` class. Calculates combined parlay odds and trust scores for multi-leg
bets. Used by the Parlay Builder view in the frontend.

### `backend/config.py`
App-level configuration constants (environment detection, feature flags). Imported
by several modules.

---

## ⚠️ DO NOT DELETE — Backend Support Files

### `backend/requirements.txt`
Python dependency list. Render installs from this on every deploy. If it's missing or
incomplete, the build fails.

Key dependencies and why they're needed:
| Package | Purpose |
|---|---|
| `flask` + `flask-cors` | Web framework + cross-origin requests from Vercel frontend |
| `sqlalchemy` | ORM for PostgreSQL queries |
| `psycopg2-binary` | PostgreSQL driver |
| `nba_api` | Official NBA stats data source |
| `requests` | HTTP calls to ESPN API and The Odds API |
| `beautifulsoup4` | HTML parsing in ESPN injury tracker |
| `apscheduler` | Daily 8 AM scheduled stats update |
| `gunicorn` | Production WSGI server on Render |
| `python-dotenv` | Loads `.env` file for local development |

### `backend/render.yaml`
Render deployment config (build command, environment). Note: the **start command** must
also be set directly in the Render dashboard:
```
gunicorn app:app --timeout 120 --workers 1
```
The `--timeout 120` is critical — without it gunicorn kills workers after 30s,
which is too short for the DB connection on cold start.

---

## ⚠️ DO NOT DELETE — Frontend Core Files

### `frontend/src/App.jsx`
The entire frontend application. Contains every React component:
- `PlayerCard` — the main prop card with line adjuster and bar chart
- `PlayerDetailModal` — the expanded view with line chart, bar chart, and game log
- `handleLineAdjust` — recalculates hit rate/trust score when user changes the line
- `handleRefreshStats` — calls `/api/admin/update-stats` to trigger an ESPN backfill
- Filter/sort/search logic, Parlay Builder, dark mode

### `frontend/src/main.jsx`
React entry point. Mounts `App` into the DOM.

### `frontend/index.html`
HTML shell that Vite builds into.

### `frontend/package.json`
Node dependencies. Key ones:
| Package | Purpose |
|---|---|
| `react` + `react-dom` | UI framework |
| `recharts` | Line chart and bar chart in the player detail modal |
| `lucide-react` | All icons (TrendingUp, RefreshCw, Moon, etc.) |
| `tailwindcss` | Utility CSS classes |

### `frontend/vite.config.js`
Build config. Sets up the dev server proxy and the production build output.

### `frontend/tailwind.config.js`
Enables Tailwind's dark mode (`class` strategy) and scans `src/` for class names.

---

## Utility / Migration Files (Safe to Delete After Use)

These are one-off scripts. They are **not imported** by anything and can be removed
once their job is done — but keep them until you're sure you won't need them again.

| File | Purpose |
|---|---|
| `backend/export_db.py` | Exports players + games from Supabase to a JSON file |
| `backend/import_db.py` | Imports that JSON into Neon PostgreSQL |
| `backend/db_export.json` | The exported data snapshot (large file) |

---

## How the Key Systems Connect

```
Browser (Vercel)
    │
    ├── GET /api/players ──────► app.py
    │                               │
    │                         players_cache (in-memory + /tmp disk)
    │                               │ (cache miss)
    │                         _compute_players_data()
    │                               ├── db_loader.py      (bulk DB read)
    │                               ├── calculator.py     (hit rate, trust score)
    │                               ├── nba_schedule_fetcher.py (next game)
    │                               ├── espn_injury_tracker.py  (injury status)
    │                               └── odds_api.py             (real lines)
    │
    ├── POST /api/calculate ───► app.py → calculator.py
    │                            (recalculates for a custom line the user typed)
    │
    └── POST /api/admin/update-stats ──► update_stats.py
                                            ├── espn_recent_games_scraper.py
                                            │   (fetches box scores from ESPN)
                                            └── writes new Game rows to DB
                                                then invalidates cache → rebuild
```

---

## Environment Variables

Set these in Render (backend) and Vercel (frontend):

| Variable | Where | Value |
|---|---|---|
| `DATABASE_URL` | Render | Neon PostgreSQL connection string (port 6543, transaction pooler) |
| `ODDS_API_KEY` | Render | API key from the-odds-api.com |
| `VITE_API_BASE_URL` | Vercel | `https://statscout-backend.onrender.com` |

---

## Cache Architecture (Why the App Doesn't Time Out)

Render's free tier proxy kills requests after 30s. Loading all 300+ players takes
longer than that. The solution:

1. On startup, `_build_players_cache_background()` runs in a **background thread**
   using a **fresh `DataLoader` instance** (not the shared global — SQLAlchemy sessions
   are not thread-safe).
2. **Phase 1** (no injuries/odds, ~15s): builds a fast initial cache, saves to
   `/tmp/statscout_players_cache.json`.
3. **Phase 2** (~90s): rebuilds with real injury data and bookmaker odds.
4. Every `/api/players` request is served from the in-memory cache instantly.
5. If the worker process restarts, it loads the disk cache on the first request
   rather than waiting for a full rebuild.
