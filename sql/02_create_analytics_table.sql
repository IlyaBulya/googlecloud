-- Replace project_id and dataset_id with your values before executing.
CREATE OR REPLACE TABLE `project_id.dataset_id.nhl_analytics_games` AS
SELECT
  game_id,
  game_date,
  season,
  game_type,
  home_team_abbrev,
  away_team_abbrev,
  home_score,
  away_score,
  SAFE_CAST(home_score + away_score AS INT64) AS total_goals,
  CASE
    WHEN home_score > away_score THEN home_team_abbrev
    WHEN away_score > home_score THEN away_team_abbrev
    ELSE NULL
  END AS winner_team_abbrev,
  CASE
    WHEN home_score > away_score THEN 'HOME'
    WHEN away_score > home_score THEN 'AWAY'
    ELSE 'TIE/UNKNOWN'
  END AS winner_location,
  CASE
    WHEN LOWER(game_state) IN ('final', 'game over', 'final overtime', 'final shootout') THEN TRUE
    ELSE FALSE
  END AS is_completed,
  ingested_at
FROM `project_id.dataset_id.nhl_raw_games`;
