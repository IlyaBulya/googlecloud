# NHL API Extraction Fixes

## Fix #1: Correct gameWeek Structure (Initial Fix)

### Problem
The pipeline was returning **0 results** when extracting NHL game data.

### Root Cause
The NHL API response structure uses a `gameWeek` array, but the extraction code was looking for a `dates` array. Additionally, field names were incorrect.

### Solution
Updated parsing to use `gameWeek` array and correct field names (id, startTimeUTC, etc).

### Results
- Before: 0 games extracted
- After: 50 games extracted over 3 days (Jan 10-12, 2025)

---

## Fix #2: Extract Completed Scores from /score Endpoint (Current Fix)

### Problem
The pipeline was returning **NULL scores** in BigQuery:
```
home_score = NULL
away_score = NULL  
total_goals = NULL
winner_location = TIE/UNKNOWN
```

### Root Cause
The extraction code was using `/schedule/{date}` as primary source, which returns scheduled games WITHOUT scores. The `/score/{date}` endpoint contains actual completed game scores but was never called.

### Solution
Updated `src/extract_nhl_data.py` to:

1. **Primary source:** `/score/{date}` endpoint
   - Contains homeTeam.score and awayTeam.score
   - Returns only games with final results
   - Endpoint: `https://api-web.nhle.com/v1/score/{YYYY-MM-DD}`

2. **Fallback:** `/schedule/{date}` if score endpoint has no games
   - Supports both top-level `games` and `gameWeek[].games` structures
   - Used for upcoming/scheduled games only

3. **Correct field mappings:**
   - Scores: `homeTeam.score`, `awayTeam.score` (numeric)
   - Team names: `commonName.default` or `placeName.default`
   - Game date: parse from `gameDate` field

4. **Deduplication:** Store records in dict by game_id to eliminate duplicate rows

5. **Detailed logging:** Print HTTP status, game count per date

### Results
- **Before:**  
  - 50 games extracted
  - 0% score coverage (all NULL)
  - Mixed scheduled and completed games
  
- **After:**  
  - 25 games extracted (correct unique count)
  - 100% score coverage (all games have scores)
  - Scores verified: DET 5 vs CHI 3, WSH 2 vs MTL 3, CAR 2 vs VAN 0, etc.

### API Response Structure (/score/{date})

```json
{
  "games": [
    {
      "id": 2024020664,
      "gameDate": "2025-01-10T00:00:00Z",
      "startTimeUTC": "2025-01-11T00:00:00Z",
      "gameState": "OFF",
      "season": 20242025,
      "gameType": 2,
      "venue": {"default": "Little Caesars Arena"},
      "homeTeam": {
        "abbrev": "DET",
        "score": 5,
        "commonName": {"default": "Detroit"},
        "placeName": {"default": "Detroit"}
      },
      "awayTeam": {
        "abbrev": "CHI",
        "score": 3,
        "commonName": {"default": "Chicago"},
        "placeName": {"default": "Chicago"}
      }
    }
  ]
}
```

## Testing

### Before (0 scores):
```bash
$ python test_score_extraction.py
Total games: 50
Games with scores: 0
Games without scores: 50
Score coverage: 0.0%
```

### After (100% scores):
```bash
$ python test_score_extraction.py
Total games: 25
Games with scores: 25
Games without scores: 0
Score coverage: 100.0%
```

## Impact on Downstream

### SQL Analytics (`sql/02_create_analytics_table.sql`)
Now returns correct values:
- `total_goals = home_score + away_score` (not NULL)
- `winner_team_abbrev = home_team_abbrev OR away_team_abbrev` (not NULL)
- `winner_location = 'HOME', 'AWAY', or 'TIE'` (not 'UNKNOWN')

### Looker Studio Dashboard
Can now display:
- Actual goals per game
- Win/loss statistics
- Team performance metrics
- Completed vs scheduled games

## Key Lessons

1. **Always check multiple API endpoints:** Different endpoints serve different purposes (schedule vs scores)
2. **Verify response structure:** Document field names and nesting before coding
3. **Deduplicate properly:** Use dict for game_id when combining multiple data sources
4. **Add diagnostic logging:** Print status + counts per request for debugging
5. **100% score coverage is achievable:** Use the right endpoint as primary source
