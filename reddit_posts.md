# Reddit Post Drafts
# Use these after MLB is live (~mid-April). Pick the sub, swap in a real current example.

---

## r/sportsbook — lead with a real prop call

**Title:** Built a free prop analytics tool that scores each bet 0-100. Here's tonight's top NBA hits

**Body:**
I've been building StatScout for the past few months and finally think it's ready to share properly. It's a free web tool that pulls historical game logs and live bookmaker lines to compute hit rates and a "trust score" for player props.

The trust score weights 5 factors: hit rate, sample size, how far the line is from the expected value, recent trend (last 5 vs last 20 games), and bookmaker consensus across sportsbooks. The idea is that a 70% hit rate on 8 games means something very different from 70% on 40 games.

**Tonight I'd highlight:**
[INSERT: 2-3 real examples from the site on actual upcoming games. E.g. "Jayson Tatum, PRA Over 42.5, 74% hit rate, trust score 81 (Strong lean). Line is 3.1 points below his venue-adjusted expected total."]

The site also covers Premier League, La Liga, Bundesliga, Serie A, and Ligue 1 for soccer match totals and player props. Just added MLB for the season opener.

Link: [statscout.vercel.app](https://statscout.vercel.app)

Not a tout, not selling anything, just wanted to get real feedback from people who actually bet.

---

## r/nba — focus on the tool itself

**Title:** Built a free NBA prop tool with adjustable lines and a trust score. Would love feedback

**Body:**
Hey r/nba. I'm a developer and basketball fan who got tired of prop tools that just show a hit rate with no context. Built StatScout over the past year to give each prop a proper analysis.

What makes it different:
- **Adjustable line slider:** drag the line and the hit rate updates instantly. Useful when you're shopping lines across books
- **Trust score:** single 0-100 number that accounts for sample size, recent trend, and how sharp the bookmakers are on this line
- **Quarter breakdown:** see how a player performs by quarter, useful for first-half and first-quarter props
- **Parlay builder:** add legs and see combined odds + confidence

It covers all major NBA players including role guys who've gotten more run recently (just added Kasparas Jakucionis, Javon Small, Scotty Pippen Jr., etc.).

[statscout.vercel.app](https://statscout.vercel.app)

Completely free, no signup. Runs on Render's free tier so may take a few seconds on first load.

---

## r/PremierLeague / r/soccer — soccer-specific

**Title:** Free tool for PL match analysis. O/U hit rates, win probability, and player props

**Body:**
Built a soccer analytics tool that might be useful for matchday analysis. Covers Premier League, La Liga, Bundesliga, Serie A, and Ligue 1.

For each fixture:
- Over/Under goals hit rate based on this season's results, split by venue (home vs away)
- Adjustable goals line so you can check different totals (2.5, 3, 3.5 etc)
- Win probability using a Poisson model from expected goals
- BTTS% and both teams' average goals scored at home/away
- Team goal props with a slider for each team's scoring line

Also has player props (goals, shots, assists, score or assist, GK clean sheets) sourced from Understat data.

[statscout.vercel.app](https://statscout.vercel.app) - click Soccer tab, then pick your league.

---

## r/webdev or r/learnprogramming — technical story

**Title:** I found 216 corrupted rows in my sports analytics database. Here's how I caught it and fixed it permanently

**Body:**
I've been building StatScout, a sports prop analytics tool, for the past year. Last week a user noticed that Paolo Banchero's PRA showed 9 on March 5th when he'd actually put up 34.

Here's what happened, how I found it, and how I fixed it.

**The bug:**
My NBA update script runs nightly and inserts new game rows. The check was simple: if a row for that player + date already exists, skip it. The problem: the script was sometimes running while games were still live, inserting interim stats (like "5 pts, 3 reb, 1 ast" at halftime), then permanently skipping that row on every future run because it "already existed."

**How widespread was it?**
I wrote a correction script that re-fetched the last 14 days from the official NBA API and compared every row. Found 216 mismatches across ~50 players. Some were bad: Anthony Edwards showing 7 pts when he'd scored 41. Nikola Jokic showing 4 pts when he'd scored 38.

**The fix:**
Two parts:
1. One-off correction script to fix the 216 bad rows
2. The update script now re-fetches and updates any game from the last 3 days on every run, treating recent data as potentially stale

```python
# Before: if existing row found, always skip
if existing:
    continue

# After: if recent game found, re-check the stats
if existing:
    if game_date >= refresh_cutoff:  # last 3 days
        if existing.points != api_pts or existing.rebounds != api_reb:
            existing.points = api_pts
            # ... update all fields
    continue
```

**Lesson:** "insert-only" data pipelines are fragile when your source data can be in a partially-complete state. Always treat recent data as potentially dirty.

The project is open source: [github.com/SamAduG1/statscout](https://github.com/SamAduG1/statscout)

Tech stack: Flask, React, PostgreSQL (Neon), deployed on Render + Vercel.

---

## LinkedIn post (for you to adapt with your own voice + video)

**Draft:**

Over the past year I built StatScout from scratch. It's a multi-sport analytics platform covering NBA player props and soccer match/player analysis across 5 European leagues, with MLB launching just in time for opening day.

Some things I'm proud of technically:

- A caching architecture that keeps a free-tier Flask backend responsive despite Render's cold starts (in-memory + disk persistence + background rebuild)
- A Poisson distribution model for soccer win probability
- Catching and fixing 216 corrupted database rows caused by mid-game stat captures, and the data pipeline change that prevents it going forward
- A trust score formula that weights hit rate, sample size, expected value gap, recent trend, and bookmaker consensus into a single 0-100 confidence number

Stack: Python (Flask), React (Vite), PostgreSQL, deployed on Render and Vercel.

Live at statscout.vercel.app, completely free, no login required.

I'm actively looking for software engineering roles, especially in sports tech, data engineering, or full-stack. Happy to talk through any of the technical decisions. [link to GitHub]

#SoftwareEngineering #Python #React #SportsAnalytics #OpenToWork
