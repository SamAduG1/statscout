# Team Quarter Analytics Feature - Summary

## Overview
Added team quarter-by-quarter analytics to StatScout, providing insights into team performance by quarter for the 2025-26 NBA season.

## What Was Built

### 1. Database Schema (`models.py`)
**New Model: `TeamGame`**
- Stores team game data with quarter-by-quarter scoring
- Fields:
  - `q1_points`, `q2_points`, `q3_points`, `q4_points` - Quarter scores
  - `ot_points` - Overtime points
  - `total_points`, `opponent_points` - Game totals
  - `won` - Win/loss indicator
  - `is_home`, `date`, `season` - Game metadata

**Calculated Properties:**
- `first_half_points` - Q1 + Q2
- `second_half_points` - Q3 + Q4
- `three_quarter_points` - Q1 + Q2 + Q3
- `reached_100_by_q3` - Boolean if team scored 100+ by Q3

### 2. Data Fetcher (`team_quarter_fetcher.py`)
**TeamQuarterFetcher Class**
- Fetches quarter data for all 30 NBA teams
- Uses NBA API's `BoxScoreSummaryV2` for quarter scores
- Rate-limited to be respectful to NBA API (0.6s delays)
- Stores data in SQLite database
- Season: **2025-26**

**Status:** Running in background (takes ~20-30 minutes for all teams)

### 3. Analytics Calculator (`team_quarter_analytics.py`)
**TeamQuarterAnalytics Class**

**Methods:**
1. `get_team_quarter_averages(team, season)`
   - Returns Q1, Q2, Q3, Q4 averages
   - First half / second half averages
   - Three-quarter average
   - "Reach 100+ by Q3" percentage and count

2. `get_quarter_win_correlation(team, season)`
   - Win percentage when leading after Q1
   - Win percentage when leading at halftime
   - Win percentage when leading after Q3

3. `get_matchup_quarter_analysis(team1, team2, season)`
   - Head-to-head quarter analysis
   - Comparative averages
   - Generated insights

### 4. Backend API Endpoints (`app.py`)

#### GET `/api/quarters/team/<team_abbr>`
Get quarter stats for a specific team.

**Parameters:**
- `season` (optional): Default "2025-26"

**Response:**
```json
{
  "success": true,
  "team": "LAL",
  "season": "2025-26",
  "averages": {
    "q1_avg": 28.5,
    "q2_avg": 27.3,
    "q3_avg": 26.8,
    "q4_avg": 27.1,
    "first_half_avg": 55.8,
    "second_half_avg": 53.9,
    "three_quarter_avg": 82.6,
    "reached_100_by_q3_pct": 44.4
  },
  "win_correlation": {
    "when_leading_after_q1": {
      "record": "15-3",
      "win_pct": 83.3
    }
  }
}
```

#### GET `/api/quarters/matchup`
Get matchup analysis between two teams.

**Parameters:**
- `team1` (required): First team abbreviation
- `team2` (required): Second team abbreviation
- `season` (optional): Default "2025-26"

**Response:**
```json
{
  "success": true,
  "matchup": {
    "matchup": "LAL vs BOS",
    "team1": { ...quarter averages... },
    "team2": { ...quarter averages... },
    "insights": [
      "BOS averages 31.2 pts in Q1 vs LAL's 28.5",
      "BOS reaches 100+ by Q3 in 62% of games"
    ]
  }
}
```

### 5. Frontend Component (`App.jsx`)

**TeamQuarterInsights Component**
- Beautiful card-based UI showing quarter analytics
- Side-by-side team comparison
- Color-coded quarter scores
- Key insights section
- Dark mode support
- Responsive design

**Features:**
- Displays Q1, Q2, Q3, Q4 averages for both teams
- Shows first half vs second half scoring
- Highlights "Reach 100+ by Q3" stat
- Generates and displays insights
- Automatically shows when 2+ teams are in filtered data

**Location:** Appears between "Stats Overview" cards and "Filters" section

## How It Works

1. **Data Collection (Background)**
   - `team_quarter_fetcher.py` runs and fetches all team games
   - For each game, extracts Q1, Q2, Q3, Q4 scores
   - Stores in `team_games` table

2. **Analytics Calculation (On-Demand)**
   - When API endpoint is hit, calculator queries database
   - Computes averages, percentages, correlations
   - Generates insights based on data patterns

3. **Frontend Display (Real-Time)**
   - Component fetches data when teams are present
   - Renders beautiful UI with quarter breakdowns
   - Updates automatically when filters change

## What Users See

### Example: Lakers vs Celtics

```
┌─ Quarter Performance Insights ─────────────────────┐
│                                                     │
│  LAL                          BOS                   │
│  Q1: 28.5  Q2: 27.3           Q1: 31.2  Q2: 29.8   │
│  Q3: 26.8  Q4: 27.1           Q3: 28.5  Q4: 26.1   │
│                                                     │
│  First Half: 55.8 pts         First Half: 61.0 pts │
│  Through 3Q: 82.6 pts         Through 3Q: 89.5 pts │
│  Reach 100+ by Q3: 44.4%      Reach 100+ by Q3: 62%│
│                                                     │
│  🔥 Key Insights:                                   │
│  • BOS averages 31.2 pts in Q1 vs LAL's 28.5       │
│  • BOS reaches 100+ by Q3 in 62% of games          │
│  • LAL is a fast starter (better first half)       │
└─────────────────────────────────────────────────────┘
```

## Files Created/Modified

**Created:**
- `backend/models.py` - Added `TeamGame` model
- `backend/team_quarter_fetcher.py` - Data fetcher
- `backend/team_quarter_analytics.py` - Analytics calculator
- `backend/init_quarter_tables.py` - Table initialization

**Modified:**
- `backend/app.py` - Added quarter API endpoints
- `frontend/src/App.jsx` - Added `TeamQuarterInsights` component

## Next Steps (Once Data Loads)

1. **Test the Feature**
   - Visit your app
   - Quarter insights should appear automatically
   - Try filtering by different teams to see different matchups

2. **Test API Endpoints**
   ```bash
   # Test team stats
   curl http://localhost:5000/api/quarters/team/LAL?season=2025-26

   # Test matchup
   curl "http://localhost:5000/api/quarters/matchup?team1=LAL&team2=BOS&season=2025-26"
   ```

3. **Verify Data**
   ```python
   # Run analytics test
   cd backend
   python team_quarter_analytics.py
   ```

## Why This Is Valuable

This feature provides **unique betting insights** that most sites don't have:

1. **Quarter Prop Context** - Users betting on team quarter totals get historical context
2. **100 by Q3 Tracking** - Directly answers "will team reach 100+ by Q3"
3. **Fast vs Slow Starters** - Identifies teams that perform better in specific halves
4. **Matchup Insights** - Head-to-head quarter performance comparison

## Season Note

Using **2025-26 season** data as requested.
- Current season for analysis
- All endpoints default to "2025-26"
- Data fetcher configured for this season

## Status

✅ Database schema complete
✅ Data fetcher running (in progress)
✅ Analytics calculator complete
✅ Backend API endpoints complete
✅ Frontend UI component complete
⏳ Waiting for data to finish loading (~20-30 min)
⏸️ Testing pending (once data is loaded)

---

**Built by:** Claude Code
**Date:** December 22, 2024
**Season:** 2025-26 NBA
