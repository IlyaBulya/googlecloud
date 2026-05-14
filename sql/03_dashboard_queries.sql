-- Replace project_id and dataset_id with your values before executing.
-- Total matches by date
SELECT
  game_date,
  COUNT(1) AS total_matches
FROM `project_id.dataset_id.nhl_analytics_games`
GROUP BY game_date
ORDER BY game_date;

-- Average goals per game
SELECT
  game_date,
  AVG(total_goals) AS avg_goals_per_game
FROM `project_id.dataset_id.nhl_analytics_games`
GROUP BY game_date
ORDER BY game_date;

-- Home wins vs away wins
SELECT
  CASE
    WHEN home_score > away_score THEN 'HOME'
    WHEN away_score > home_score THEN 'AWAY'
    ELSE 'TIE/UNKNOWN'
  END AS win_location,
  COUNT(1) AS count_games
FROM `project_id.dataset_id.nhl_analytics_games`
GROUP BY win_location
ORDER BY count_games DESC;

-- Top teams by wins
SELECT
  winner_team_abbrev AS team_abbrev,
  COUNT(1) AS wins
FROM `project_id.dataset_id.nhl_analytics_games`
WHERE winner_team_abbrev IS NOT NULL
GROUP BY winner_team_abbrev
ORDER BY wins DESC
LIMIT 20;

-- Total goals by team
SELECT
  team_abbrev,
  SUM(goals) AS total_goals
FROM (
  SELECT home_team_abbrev AS team_abbrev, home_score AS goals FROM `project_id.dataset_id.nhl_analytics_games`
  UNION ALL
  SELECT away_team_abbrev AS team_abbrev, away_score AS goals FROM `project_id.dataset_id.nhl_analytics_games`
)
GROUP BY team_abbrev
ORDER BY total_goals DESC;

-- Completed vs scheduled games
SELECT
  is_completed,
  COUNT(1) AS game_count
FROM `project_id.dataset_id.nhl_analytics_games`
GROUP BY is_completed
ORDER BY game_count DESC;
