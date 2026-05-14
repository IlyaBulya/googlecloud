import os
from dataclasses import dataclass
from datetime import date
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    project_id: str
    bucket_name: str
    bigquery_dataset: str
    raw_table_name: str
    analytics_table_name: str
    start_date: str
    end_date: str
    upcoming_date: str | None = None
    forecast_output_dir: str | None = None
    forecast_json_name: str | None = None
    team_stats_table_name: str | None = None


def get_env_var(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if value is None or value.strip() == "":
        raise ValueError(f"Missing required environment variable: {key}")
    return value.strip()


def validate_date(value: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid date format for value '{value}'. Use YYYY-MM-DD.") from exc
    return value


def load_config() -> Config:
    config = Config(
        project_id=get_env_var("GCP_PROJECT_ID"),
        bucket_name=get_env_var("GCS_BUCKET_NAME"),
        bigquery_dataset=get_env_var("BIGQUERY_DATASET"),
        raw_table_name=get_env_var("RAW_TABLE_NAME"),
        analytics_table_name=get_env_var("ANALYTICS_TABLE_NAME"),
        start_date=validate_date(get_env_var("START_DATE")),
        end_date=validate_date(get_env_var("END_DATE")),
        upcoming_date=os.getenv("UPCOMING_DATE"),
        forecast_output_dir=os.getenv("FORECAST_OUTPUT_DIR"),
        forecast_json_name=os.getenv("FORECAST_JSON_NAME"),
        team_stats_table_name=os.getenv("TEAM_STATS_TABLE_NAME"),
    )

    if config.start_date > config.end_date:
        raise ValueError("START_DATE must be on or before END_DATE")

    if config.upcoming_date:
        config.upcoming_date = validate_date(config.upcoming_date)

    return config


def load_forecast_config() -> Config:
    config = load_config()
    if not config.upcoming_date:
        raise ValueError("Missing required environment variable: UPCOMING_DATE")
    if not config.forecast_output_dir:
        raise ValueError("Missing required environment variable: FORECAST_OUTPUT_DIR")
    if not config.forecast_json_name:
        raise ValueError("Missing required environment variable: FORECAST_JSON_NAME")
    if not config.team_stats_table_name:
        raise ValueError("Missing required environment variable: TEAM_STATS_TABLE_NAME")
    return config
