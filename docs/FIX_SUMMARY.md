# NHL API Extraction Fix Summary

## Problem
The pipeline was returning **0 results** when extracting NHL game data.

## Root Cause
The NHL API response structure uses a `gameWeek` array, but the extraction code was looking for a `dates` array. Additionally, field names were incorrect:

**What the code expected:**
- `/schedule/{date}` response with `dates` array
- Game ID field: `gamePk`
- Start time field: `startTime`

**What the actual API returns:**
- `/schedule/{date}` response with `gameWeek` array
- Game ID field: `id`
- Start time field: `startTimeUTC`
- Team data under `homeTeam` and `awayTeam` (not nested under `teams`)

## Solution
Updated `src/extract_nhl_data.py` to:

1. **Parse correct response structure:**
   ```python
   for day_block in schedule_response.get("gameWeek", []):
       for game in day_block.get("games", []):
           # Parse each game
   ```

2. **Use correct field names:**
   - `game.get("id")` instead of `game.get("gamePk")`
   - `game.get("startTimeUTC")` instead of `game.get("startTime")`
   - `home_team.get("abbrev")` from `game.get("homeTeam", {})`

3. **Add robustness:**
   - Exponential backoff retry logic (3 retries by default)
   - Proper error handling for transient API failures
   - Date range validation within response parsing

## Results
- **Before:** 0 games extracted
- **After:** 50 games extracted over 3 days (Jan 10-12, 2025)
- Sample output shows all fields correctly populated:
  ```json
  {
    "game_id": 2024020664,
    "game_date": "2025-01-10",
    "season": 20242025,
    "venue": "Little Caesars Arena",
    "home_team_abbrev": "DET",
    "away_team_abbrev": "CHI",
    "start_time_utc": "2025-01-11T00:00:00Z",
    ...
  }
  ```

## Testing
Use the included test script to verify extraction locally:
```bash
python test_extraction.py --date 2025-01-15
```

This shows:
- Number of games returned
- Sample game structure (debugging gameWeek vs dates issue)
- Whether the API is responding correctly

## Key Lesson
When working with external APIs, always validate:
1. Response structure (array names, nesting)
2. Field names and types
3. Use HTTP client libraries with retry logic for resilience
4. Add diagnostic logging to identify parsing issues quickly
