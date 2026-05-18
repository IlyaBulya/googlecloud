# Cloud Scheduler Setup

This document describes how to deploy a Cloud Function and schedule it with Cloud Scheduler to run the NHL pipeline on a schedule.

## Architecture

- `main.py` exposes a Cloud Function HTTP endpoint: `run_scheduled_pipeline(request)`.
- The function loads config from environment variables using `src/config.py`.
- It runs the same pipeline logic as `src/run_pipeline.py`:
  1. Extract NHL game data for `START_DATE` to `END_DATE`.
  2. Write a local JSONL file to `data/raw`.
  3. Upload the JSONL file to GCS.
  4. Load the JSONL file into BigQuery.
- Cloud Scheduler triggers the Cloud Function via HTTP POST.

## Deploy Cloud Function

Run this command from the repository root:

```bash
gcloud functions deploy run_scheduled_pipeline \
  --entry-point run_scheduled_pipeline \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --region YOUR_REGION \
  --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID,GCS_BUCKET_NAME=YOUR_BUCKET_NAME,BIGQUERY_DATASET=YOUR_DATASET,RAW_TABLE_NAME=YOUR_RAW_TABLE_NAME,START_DATE=YYYY-MM-DD,END_DATE=YYYY-MM-DD
```

If you prefer to keep the function secured and use a service account, omit `--allow-unauthenticated` and configure Cloud Scheduler with an OIDC token.

## Create Cloud Scheduler job

Create a job that posts to the Cloud Function endpoint:

```bash
FUNCTION_URL=$(gcloud functions describe run_scheduled_pipeline --region YOUR_REGION --format='value(httpsTrigger.url)')

gcloud scheduler jobs create http nhl-pipeline-job \
  --schedule="0 6 * * *" \
  --uri="$FUNCTION_URL" \
  --http-method=POST \
  --time-zone="UTC" \
  --headers="Content-Type:application/json"
```

If your function requires authenticated access, add an OIDC token instead:

```bash
gcloud scheduler jobs create http nhl-pipeline-job \
  --schedule="0 6 * * *" \
  --uri="$FUNCTION_URL" \
  --http-method=POST \
  --time-zone="UTC" \
  --oidc-service-account=YOUR_SA@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Test the Cloud Function locally

Install dependencies and run the Functions Framework if needed:

```bash
python3 -m pip install -r requirements.txt
functions-framework --target=run_scheduled_pipeline
```

Then send a POST request:

```bash
curl -X POST http://localhost:8080
```

## Verify GCS and BigQuery updates

- Verify the uploaded JSONL file in GCS:
  - `gs://YOUR_BUCKET_NAME/raw/nhl_games/start_date=START_DATE/end_date=END_DATE/`
- Verify rows in BigQuery:
  - `bq show --format=prettyjson YOUR_PROJECT_ID:YOUR_DATASET.YOUR_RAW_TABLE_NAME`
- Query the raw table to confirm row counts:

```bash
bq query --nouse_legacy_sql '
SELECT COUNT(*) AS row_count
FROM `YOUR_PROJECT_ID.YOUR_DATASET.YOUR_RAW_TABLE_NAME`;
'
```

If the Cloud Function returns `status: success`, it means the pipeline completed and the JSON response contains the local file path, `gcs_uri`, and BigQuery table information.
