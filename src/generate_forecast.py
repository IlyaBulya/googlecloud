import json
from datetime import datetime
from pathlib import Path
from typing import Any

from google.cloud import bigquery

from src.config import Config
from src.utils import ensure_directory


def load_team_stats(config: Config) -> dict[str, dict[str, Any]]:
    table_name = config.team_stats_table_name or "team_stats"
    dataset_table = f"{config.project_id}.{config.bigquery_dataset}.{table_name}"
    client = bigquery.Client(project=config.project_id)
    query = f"SELECT team_abbrev, games_played, wins, losses, goals_for, goals_against, avg_goals_for, avg_goals_against, win_rate, home_games, home_wins, home_win_rate, away_games, away_wins, away_win_rate FROM `{dataset_table}`"
    results = client.query(query).result()

    stats: dict[str, dict[str, Any]] = {}
    for row in results:
        if not row.team_abbrev:
            continue
        stats[row.team_abbrev] = {
            "games_played": row.games_played or 0,
            "wins": row.wins or 0,
            "losses": row.losses or 0,
            "goals_for": float(row.goals_for or 0),
            "goals_against": float(row.goals_against or 0),
            "avg_goals_for": float(row.avg_goals_for or 0),
            "avg_goals_against": float(row.avg_goals_against or 0),
            "win_rate": float(row.win_rate or 0),
            "home_games": row.home_games or 0,
            "home_wins": row.home_wins or 0,
            "home_win_rate": float(row.home_win_rate or 0),
            "away_games": row.away_games or 0,
            "away_wins": row.away_wins or 0,
            "away_win_rate": float(row.away_win_rate or 0),
        }
    return stats


def read_upcoming_games(upcoming_path: str) -> list[dict[str, Any]]:
    path = Path(upcoming_path)
    if not path.exists():
        raise FileNotFoundError(f"Upcoming games file not found: {upcoming_path}")

    games = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if not line:
                continue
            games.append(json.loads(line))
    return games


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_forecast_strength(team_stats: dict[str, Any], league_avg_goals: float, home: bool) -> float:
    if not team_stats:
        return 0.5

    win_rate = safe_float(team_stats.get("win_rate"), 0.5)
    home_win_rate = safe_float(team_stats.get("home_win_rate"), 0.5) if home else safe_float(team_stats.get("away_win_rate"), 0.5)
    avg_goals_for = safe_float(team_stats.get("avg_goals_for"), league_avg_goals)
    normalized_goals = avg_goals_for / league_avg_goals if league_avg_goals > 0 else 1.0
    bonus = 0.03 if home else 0.0
    return 0.60 * win_rate + 0.25 * home_win_rate + 0.15 * normalized_goals + bonus


def generate_forecast(config: Config, upcoming_games_path: str) -> str:
    team_stats = load_team_stats(config)
    upcoming_games = read_upcoming_games(upcoming_games_path)

    total_goals = 0.0
    total_games = 0
    for stats in team_stats.values():
        total_goals += safe_float(stats.get("goals_for"))
        total_games += stats.get("games_played", 0)

    league_avg_goals = total_goals / total_games if total_games else 1.0

    forecasts = []
    for game in upcoming_games:
        home_abbrev = game.get("home_team_abbrev")
        away_abbrev = game.get("away_team_abbrev")
        home_stats = team_stats.get(home_abbrev, {})
        away_stats = team_stats.get(away_abbrev, {})

        home_strength = compute_forecast_strength(home_stats, league_avg_goals, home=True)
        away_strength = compute_forecast_strength(away_stats, league_avg_goals, home=False)
        total_strength = home_strength + away_strength or 1.0

        home_probability = home_strength / total_strength
        away_probability = away_strength / total_strength
        predicted_winner = home_abbrev if home_probability >= away_probability else away_abbrev
        predicted_winner_name = game.get("home_team_name") if predicted_winner == home_abbrev else game.get("away_team_name")
        confidence = max(home_probability, away_probability)

        forecasts.append({
            "game_id": game.get("game_id"),
            "game_date": game.get("game_date"),
            "start_time_utc": game.get("start_time_utc"),
            "away_team_abbrev": away_abbrev,
            "home_team_abbrev": home_abbrev,
            "away_team_name": game.get("away_team_name"),
            "home_team_name": game.get("home_team_name"),
            "predicted_winner": predicted_winner,
            "predicted_winner_name": predicted_winner_name,
            "home_probability": round(home_probability, 2),
            "away_probability": round(away_probability, 2),
            "confidence": round(confidence, 2),
            "home_win_rate": round(safe_float(home_stats.get("home_win_rate"), 0.5), 2),
            "away_win_rate": round(safe_float(away_stats.get("away_win_rate"), 0.5), 2),
        })

    output_dir = Path(config.forecast_output_dir or "frontend/public/data")
    ensure_directory(str(output_dir))
    output_path = output_dir / (config.forecast_json_name or "forecast.json")

    summary = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "historical_range": {
            "start_date": config.start_date,
            "end_date": config.end_date,
        },
        "upcoming_date": config.upcoming_date,
        "summary": {
            "games_analyzed": len(upcoming_games),
            "teams_analyzed": len(team_stats),
            "upcoming_games": len(upcoming_games),
            "avg_goals_per_game": round(league_avg_goals, 2),
        },
        "games": forecasts,
    }

    with open(output_path, "w", encoding="utf-8") as writer:
        json.dump(summary, writer, indent=2, ensure_ascii=False)

    return str(output_path)
