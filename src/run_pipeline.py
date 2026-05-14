import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from src.config import load_config
from src.extract_nhl_data import extract_nhl_data
from src.load_to_bigquery import load_jsonl_to_bigquery
from src.upload_to_gcs import upload_to_gcs


def main() -> None:
    config = load_config()
    print("Starting NHL GCP batch pipeline")
    print(f"Date range: {config.start_date} to {config.end_date}")

    local_file_path, row_count = extract_nhl_data(
        config.start_date,
        config.end_date,
    )

    gcs_uri = upload_to_gcs(
        local_file_path,
        config.bucket_name,
        config.start_date,
        config.end_date,
    )

    loaded_rows = load_jsonl_to_bigquery(
        gcs_uri,
        config.project_id,
        config.bigquery_dataset,
        config.raw_table_name,
    )

    print("\nPipeline complete")
    print(f"Local file: {local_file_path}")
    print(f"GCS URI: {gcs_uri}")
    print(f"BigQuery table: {config.project_id}.{config.bigquery_dataset}.{config.raw_table_name}")
    print(f"Extracted rows: {row_count}")
    print(f"Loaded rows: {loaded_rows}")


if __name__ == "__main__":
    main()
