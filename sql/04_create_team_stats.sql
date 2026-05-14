-- Replace project_id and dataset_id with your values before executing.
-- This query creates a team-level stats table from the analytics game table.
CREATE OR REPLACE TABLE `project-1e360cf3-1989-48d5-a5a.nhl_pipeline.team_stats` AS
WITH team_games AS (
  SELECT
    home_team_abbrev AS team_abbrev,
    1 AS games_played,
    CASE WHEN winner_team_abbrev = home_team_abbrev THEN 1 ELSE 0 END AS wins,
    CASE WHEN winner_team_abbrev != home_team_abbrev AND winner_team_abbrev IS NOT NULL THEN 1 ELSE 0 END AS losses,
    home_score AS goals_for,
    away_score AS goals_against,
    1 AS home_games,
    CASE WHEN winner_team_abbrev = home_team_abbrev THEN 1 ELSE 0 END AS home_wins,
    0 AS away_games,
    0 AS away_wins
  FROM `project-1e360cf3-1989-48d5-a5a.nhl_pipeline.analytics_nhl_games`
  UNION ALL
  SELECT
    away_team_abbrev AS team_abbrev,
    1 AS games_played,
    CASE WHEN winner_team_abbrev = away_team_abbrev THEN 1 ELSE 0 END AS wins,
    CASE WHEN winner_team_abbrev != away_team_abbrev AND winner_team_abbrev IS NOT NULL THEN 1 ELSE 0 END AS losses,
    away_score AS goals_for,
    home_score AS goals_against,
    0 AS home_games,
    0 AS home_wins,
    1 AS away_games,
    CASE WHEN winner_team_abbrev = away_team_abbrev THEN 1 ELSE 0 END AS away_wins
  FROM `project-1e360cf3-1989-48d5-a5a.nhl_pipeline.analytics_nhl_games`
)
SELECT
  team_abbrev,
  SUM(games_played) AS games_played,
  SUM(wins) AS wins,
  SUM(losses) AS losses,
  SUM(goals_for) AS goals_for,
  SUM(goals_against) AS goals_against,
  SAFE_DIVIDE(SUM(goals_for), SUM(games_played)) AS avg_goals_for,
  SAFE_DIVIDE(SUM(goals_against), SUM(games_played)) AS avg_goals_against,
  SAFE_DIVIDE(SUM(wins), SUM(games_played)) AS win_rate,
  SUM(home_games) AS home_games,
  SUM(home_wins) AS home_wins,
  SAFE_DIVIDE(SUM(home_wins), SUM(home_games)) AS home_win_rate,
  SUM(away_games) AS away_games,
  SUM(away_wins) AS away_wins,
  SAFE_DIVIDE(SUM(away_wins), SUM(away_games)) AS away_win_rate
FROM team_games
GROUP BY team_abbrev
ORDER BY games_played DESC;
