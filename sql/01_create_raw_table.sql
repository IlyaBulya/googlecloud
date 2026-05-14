-- Replace project_id and dataset_id with your values before executing.
CREATE TABLE IF NOT EXISTS `project_id.dataset_id.nhl_raw_games` (
  game_id INT64,
  game_date DATE,
  season STRING,
  game_type STRING,
  venue STRING,
  home_team_abbrev STRING,
  away_team_abbrev STRING,
  home_team_name STRING,
  away_team_name STRING,
  home_score INT64,
  away_score INT64,
  game_state STRING,
  start_time_utc STRING,
  source_date DATE,
  ingested_at TIMESTAMP
);
