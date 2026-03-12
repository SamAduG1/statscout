# StatScout — Project Overview

Sports analytics and player props tool. Aggregates historical performance data and live betting lines to generate hit rates, trust scores, and prop recommendations across NBA and soccer (Premier League, La Liga).

---

## Tech Stack

| Layer | Technology | Host |
|---|---|---|
| Frontend | React (Vite), Tailwind CSS | Vercel |
| Backend | Flask (Python), Gunicorn | Render (free tier) |
| Database | PostgreSQL (serverless) | Neon Tech |
| Version control | Git | GitHub |

### Key env vars
| Variable | Used by | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | Frontend (Vercel) | Points to Render backend |
| `DATABASE_URL` | Backend (Render) | Neon PostgreSQL connection string |
| `ODDS_API_KEY` | Backend | The Odds API — NBA + soccer lines |
| `FOOTBALL_DATA_KEY` | Backend | football-data.org — soccer historical results |

---

## Architecture

### Backend (`backend/`)
- `app.py` — Flask app, all routes, cache management
- `models.py` — SQLAlchemy ORM: Player, Game, TeamGame, SoccerPlayer, SoccerPlayerGame
- `soccer_fetcher.py` — Fetches upcoming fixtures + historical match results + O/U odds
- `db_loader.py` — NBA player/game data loader
- `calculator.py` — NBA prop hit rate calculations
- `odds_api.py` — The Odds API client (NBA + soccer)
- `populate_soccer_players.py` — One-off bulk seed script (local only, never deployed)
- `update_soccer_stats.py` — Weekly incremental update script (local only)

### Frontend (`frontend/src/App.jsx`)
Single-file React monolith (~3500 lines). No component split yet (planned when a 3rd sport is added and route-based nav is introduced).

### Caching strategy
- NBA props: in-memory dict + `/tmp` JSON file, background thread rebuild, 6hr TTL
- Soccer match totals: same pattern, per-league cache, 6hr TTL
- Soccer player props: per-fixture `/tmp` JSON file, 12hr TTL
- All caches survive gunicorn worker restarts via disk persistence
- UptimeRobot pings `/api/health` every 5 min to keep Render service warm

---

## Features

### NBA Props
- Player props: Points, Rebounds, Assists, Steals, Blocks, 3PM, PRA, PA, PR, RA
- Hit rates computed from historical game logs (Neon DB)
- Live bookmaker lines via The Odds API (DraftKings, FanDuel, etc.)
- Adjustable line slider — hit rate updates live from raw game arrays
- Trust score (0-100): weighted formula using hit rate, sample size, line deviation, recent trend, bookmaker consensus
- Human-readable trust labels: "Strong lean" / "Leaning over" / "I like these odds" / "Slight edge" / "Proceed with caution" / "Taking a longshot"
- Quarter breakdown: per-quarter stats (Q1-Q4 points, rebounds, assists)
- Quarter Performance Insights: team-level scoring patterns
- Player detail modal: full game log, trend chart
- Custom Parlay Builder: add props, see combined odds + confidence
- AI parlay generator

### Soccer — Match Totals
- Leagues: Premier League, La Liga
- Per-fixture: O/U goals line (adjustable), Over%, BTTS%, expected total, avg goals home/away
- Win probability: Poisson model (home%, draw%, away%) shown as stacked bar
- Trust score: 5-factor weighted (over hit rate, expected vs line gap, odds lean, consistency, sample size)
- Team goal props: per-team scoring line slider (O/U 0.5-3.5)
- Parlay integration: add Over/Under legs to shared parlay sidebar
- Local timezone display, American odds format

### Soccer — Player Props (Phase 2)
- Leagues: Premier League (La Liga seed pending)
- Fixture selector: pick any upcoming match
- Markets: Goals O/U, Shots O/U, Assists O/U, Score or Assist O/U, GK Clean Sheet %
- Adjustable line slider per card — hit rate recomputes live
- Bar graph: last 10 games shown as green (hit) / red (miss) squares
- Filters: market tab, team filter (Both / Home / Away), sorted by hit rate
- Position filtering: GK tab shows goalkeepers only; other tabs hide GKs

---

## Data Sources

### NBA
| Source | Data | Notes |
|---|---|---|
| Neon DB | Player game logs | Populated via `update_stats.py` |
| The Odds API | Live betting lines | 500 free requests/month |

### Soccer — Match Level
| Source | Data | Notes |
|---|---|---|
| football-data.org | Historical PL + La Liga match results | Free tier, 10 req/min, no daily cap |
| The Odds API | Upcoming fixtures + O/U totals | PL uses `us` region; La Liga uses `uk,eu` |

### Soccer — Player Level
| Source | Data | Notes |
|---|---|---|
| Understat.com | Goals, shots, assists, key passes, xG per player per match | Session-based scraping; `getLeagueData` + `getPlayerData` endpoints; no auth required but needs cookie from page visit first |

**Known gaps:**
- Shots on target (SOT): NOT in Understat per-match data
- GK saves: NOT in Understat data
- Corner kicks: match-level only, no player-level market
- La Liga player data: not yet seeded (run `python populate_soccer_players.py --league laliga`)

**Planned data source for SOT + saves:** Sofascore internal API (`api.sofascore.com`) — covers both stats for PL and La Liga, no auth required with polite usage

---

## Database Schema

### NBA
```
players           id, name, team, position
games             id, player_id, date, opponent, is_home, points, rebounds, assists,
                  steals, blocks, three_pm, minutes, q1-q4 per stat
team_games        id, game_id, team, opponent, date, is_home, season, q1-q4 points, totals
```

### Soccer
```
soccer_players    id, understat_id (unique), name, team_name, league, position, last_updated
soccer_player_games  id, player_id, match_date, opponent, venue, goals, shots,
                     shots_on_target (always 0 — no source yet), assists, key_passes,
                     minutes_played, goals_conceded (GK only), season
```

---

## Data Pipeline

### NBA (automated)
- `update_stats.py` — pulls game logs from NBA API, updates Neon DB
- Runs on a schedule (or manually when needed)

### Soccer Match Totals (automated on Render)
- `soccer_fetcher.py` fetches from football-data.org + The Odds API on first request after cache expiry
- 6hr cache, no cron needed

### Soccer Player Props (manual — local only)
- **One-off seed:** `python populate_soccer_players.py --league pl` (~13 min, 518 players, 9075 game rows)
- **Weekly update:** `python update_soccer_stats.py --league pl` (run after each gameweek, typically Monday)
- Both scripts read `DATABASE_URL` from `backend/.env`
- Neither is deployed to Render — DB is updated locally, Render reads from Neon

---

## Deployment

### Render (backend)
- Start command (set in Render dashboard, NOT render.yaml): `gunicorn app:app --timeout 120 --workers 1`
- `--timeout 120` required to avoid worker kill during DB connect
- Free tier sleeps after 15 min inactivity; UptimeRobot keeps it warm
- All env vars set in Render dashboard: `DATABASE_URL`, `ODDS_API_KEY`, `FOOTBALL_DATA_KEY`

### Vercel (frontend)
- Auto-deploys on push to `master`
- Env var: `VITE_API_BASE_URL` = Render backend URL

---

## Roadmap

### Near term
- [ ] Sofascore integration: SOT + GK saves data for player props
- [ ] Corner props on match cards (match-level, not player-level)
- [ ] La Liga player props seed + weekly update
- [ ] Soccer player props parlay integration

### Future
- [ ] Route-based nav migration (needed when 3rd sport added — tabs don't scale past 3)
- [ ] Soccer player props: xG-based trust score
- [ ] Soccer player props: home/away split stats
- [ ] H2H matchup history (needs 2+ seasons of data, revisit 2026-27)
- [ ] Mobile app

---

## Code Style Rules
- No em dashes or en dashes in JSX text — use plain hyphen or colon
- The `--` null fallback in JSX (`{val ?? '--'}`) is the only exception
- Dark mode is default; all new components must support `dark:` variants
- All new cards use `border-l-[3px] border-l-blue-500` signature accent
- Hit rate color: green-500 (>=70%), blue-500 (55-69%), red-400 (<55%)
- Trust color: green-500 (>=80), amber-500 (70-79), yellow-500 (60-69), red-500 (<60)
