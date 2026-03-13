# StatScout

**Live site:** [statscout.vercel.app](https://statscout.vercel.app)

A multi-sport analytics platform that aggregates historical performance data and live betting lines to generate hit rates, trust scores, and prop recommendations across NBA, Premier League, La Liga, Bundesliga, Serie A, and Ligue 1.

---

## What it does

Most prop tools show you a line and a hit rate. StatScout goes further:

- **Adjustable line slider:** drag the O/U line and hit rate recalculates instantly from raw game arrays, no server round-trip
- **Trust score (0-100):** a weighted formula combining hit rate, sample size, line deviation from expected, recent trend, and bookmaker consensus. Condenses the analysis into a single number
- **Parlay builder:** add NBA player props and soccer match/player legs to a shared sidebar. Combined odds and confidence calculated live
- **AI parlay generator:** selects high-trust legs automatically and explains the reasoning
- **Soccer win probability:** Poisson distribution model computing home/draw/away probabilities from expected goals

---

## Sports covered

### NBA
Props: Points, Rebounds, Assists, Steals, Blocks, 3PM, PRA, PA, PR, RA

- Hit rates from historical game logs (PostgreSQL)
- Live bookmaker lines via The Odds API
- Quarter breakdown and team performance insights
- Player detail modal with trend chart

### Soccer (Premier League, La Liga, Bundesliga, Serie A, Ligue 1)

**Match Totals:**
- O/U goals line with live Over%, BTTS%, expected total, avg goals
- Win probability: Poisson model (home/draw/away) as stacked bar
- Team goal props: per-team scoring line slider
- Trust score: 5-factor weighted formula

**Player Props:**
- Markets: Goals O/U, Shots O/U, Assists O/U, Score or Assist O/U, GK Clean Sheet
- Per-player adjustable line slider, hit rate computed live from stored arrays
- Bar graph showing last 15 games (green = hit, red = miss)
- Filters by market, team, position

---

## Tech stack

| Layer | Technology | Host |
|---|---|---|
| Frontend | React (Vite), Tailwind CSS | Vercel |
| Backend | Flask (Python), Gunicorn | Render |
| Database | PostgreSQL (serverless) | Neon Tech |

---

## Architecture highlights

### Caching strategy that survives cold starts
Render's free tier spins down after 15 minutes of inactivity. A naive implementation would force every cold-start user to wait 30+ seconds for data. StatScout uses a layered cache:

1. In-memory dict (instant, lives for worker lifetime)
2. `/tmp` JSON file (survives worker restarts, loaded at startup)
3. Background thread rebuild (never blocks the request)
4. UptimeRobot pings `/api/health` every 5 min to keep the service warm

Result: users always get a response immediately, even on cold starts.

### Trust score formula (NBA)
Rather than showing raw hit rate alone (which can be misleading with small samples or lucky streaks), each prop gets a 0-100 trust score:

```
Trust = (hitRate * 0.30) + (sampleSizeScore * 0.20) + (lineDeviationScore * 0.25) + (recentTrendScore * 0.15) + (bookmakerConsensusScore * 0.10)
```

Human-readable labels: "Strong lean" / "Leaning over" / "I like these odds" / "Slight edge" / "Proceed with caution" / "Taking a longshot"

### Soccer win probability (Poisson model)
For each fixture, expected home and away goals are derived from venue-specific historical averages. The Poisson distribution is then summed over 0-8 goals per team to compute P(home win), P(draw), P(away win):

```python
for h in range(9):
    for a in range(9):
        p = poisson(lambda_home, h) * poisson(lambda_away, a)
        if h > a: home_prob += p
        elif h == a: draw_prob += p
        else: away_prob += p
```

### Data integrity: catching mid-game stat corruption
Early on, the NBA update script would run during live games, insert interim stats, then never update them (existing rows were silently skipped). This corrupted hit rates for dozens of players, some by 20+ points in the wrong direction.

Fix: the update script now re-fetches and corrects any game from the last 3 days on every run, treating recent rows as potentially stale. A one-off correction script fixed 216 bad rows across the historical data.

### Soccer player data pipeline
Player prop data comes from Understat's internal API (session-based scraping, no auth required with polite usage). The pipeline:

1. Visit league/player page to obtain session cookies
2. Call `getLeagueData/{league}/{season}` for player roster
3. Call `getPlayerData/{id}` per player for match-by-match stats
4. Incremental weekly updates, only fetches games since last known date per player

Current database: ~1,100 soccer players, ~25,000+ game rows across 5 leagues.

---

## Data sources

| Source | Data |
|---|---|
| NBA API (nba_api) | Player game logs |
| The Odds API | Live betting lines (NBA + soccer) |
| football-data.org | Historical soccer match results |
| Understat.com | Soccer player per-match stats |

---

## Running locally

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # add your API keys
python app.py

# Frontend
cd frontend
npm install
npm run dev
```

Required env vars: `DATABASE_URL`, `ODDS_API_KEY`, `FOOTBALL_DATA_KEY`
