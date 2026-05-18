import traceback

from flask import Request, jsonify

from src.config import load_config
from src.extract_nhl_data import extract_nhl_data
from src.load_to_bigquery import load_jsonl_to_bigquery
from src.upload_to_gcs import upload_to_gcs


def run_scheduled_pipeline(request: Request):
    """Cloud Function entrypoint for scheduled NHL pipeline runs."""
    if request.method != "POST":
        return jsonify({"status": "error", "message": "Only POST requests are allowed."}), 405

    try:
        config = load_config()

        local_file_path, extracted_rows = extract_nhl_data(
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

        return jsonify(
            {
                "status": "success",
                "local_file": local_file_path,
                "gcs_uri": gcs_uri,
                "bigquery_table": f"{config.project_id}.{config.bigquery_dataset}.{config.raw_table_name}",
                "extracted_rows": extracted_rows,
                "loaded_rows": loaded_rows,
            }
        )
    except Exception as exc:
        message = str(exc) or "An unexpected error occurred."
        traceback.print_exc()
        return jsonify({"status": "error", "message": message}), 500
