from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from google.api_core.exceptions import BadRequest


def ensure_dataset(client: bigquery.Client, dataset_id: str) -> None:
    dataset = bigquery.Dataset(client.dataset(dataset_id))
    try:
        client.create_dataset(dataset, exists_ok=True)
        print(f"Verified BigQuery dataset: {dataset_id}")
    except BadRequest as exc:
        raise RuntimeError(f"Failed to create or validate dataset {dataset_id}: {exc}") from exc


def load_jsonl_to_bigquery(
    gcs_uri: str,
    project_id: str,
    dataset_name: str,
    table_name: str,
) -> int:
    client = bigquery.Client(project=project_id)
    ensure_dataset(client, dataset_name)

    table_ref = client.dataset(dataset_name).table(table_name)
    schema = [
        SchemaField("game_id", "INTEGER"),
        SchemaField("game_date", "DATE"),
        SchemaField("season", "STRING"),
        SchemaField("game_type", "STRING"),
        SchemaField("venue", "STRING"),
        SchemaField("home_team_abbrev", "STRING"),
        SchemaField("away_team_abbrev", "STRING"),
        SchemaField("home_team_name", "STRING"),
        SchemaField("away_team_name", "STRING"),
        SchemaField("home_score", "INTEGER"),
        SchemaField("away_score", "INTEGER"),
        SchemaField("game_state", "STRING"),
        SchemaField("start_time_utc", "STRING"),
        SchemaField("source_date", "DATE"),
        SchemaField("ingested_at", "TIMESTAMP"),
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        ignore_unknown_values=True,
    )

    print(f"Loading data from {gcs_uri} into BigQuery table {project_id}.{dataset_name}.{table_name}")
    load_job = client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)
    try:
        load_job.result()
    except BadRequest as exc:
        print(f"BigQuery load job failed: {exc}")
        raise

    loaded_rows = load_job.output_rows or 0
    destination_table = client.get_table(table_ref)
    print(
        f"Loaded {loaded_rows} rows into {destination_table.project}.{destination_table.dataset_id}.{destination_table.table_id}."
    )
    return loaded_rows
