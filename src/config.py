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
    )

    if config.start_date > config.end_date:
        raise ValueError("START_DATE must be on or before END_DATE")

    return config
