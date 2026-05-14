# NHL GCP Pipeline

## Overview

This repository contains a complete batch data engineering project for NHL match analytics on Google Cloud Platform. The pipeline extracts NHL game schedule and score data from a public NHL API, stores raw JSONL files in Google Cloud Storage, loads the raw data into BigQuery, and includes SQL transformations to build analytics-ready tables.

## Problem Statement

NHL game data is updated daily after games are completed. A batch pipeline is ideal for gathering this periodic data, preserving raw event history, and transforming it into analytics-ready tables for reporting and dashboarding.

## Why Batch?

- NHL data changes on a daily cadence rather than continuously in real time.
- Batch extraction is easier to schedule, debug, and replay for historical date ranges.
- The pipeline is reusable for any date range and preserves raw data for auditability.

## Architecture

```
NHL API
  ↓
Python extraction script
  ↓
Google Cloud Storage raw JSONL files
  ↓
BigQuery raw table
  ↓
BigQuery analytics table
  ↓
Looker Studio dashboard
```

## Technologies Used

- Python 3.10+
- requests
- pandas
- python-dotenv
- google-cloud-storage
- google-cloud-bigquery
- Google Cloud Storage
- BigQuery

## Repository Structure

- `README.md` - project overview and reproduction instructions
- `requirements.txt` - Python dependencies
- `.gitignore` - ignored files and directories
- `config.example.env` - example environment configuration
- `src/` - pipeline code
- `sql/` - BigQuery DDL and analytics queries
- `docs/architecture.md` - architecture explanation

## Setup Instructions

1. Clone the repository.
2. Create a Python 3.10+ virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy the example configuration file:

```bash
cp config.example.env .env
```

5. Set up your Google Cloud environment:
   - Enable the BigQuery and Cloud Storage APIs.
   - Authenticate with a service account or `gcloud auth application-default login`.

6. Update `.env` with your project values.

## GCS Bucket Setup

1. Create a bucket in Google Cloud Storage.
2. Make sure the service account used by the pipeline has `roles/storage.objectAdmin` or equivalent permissions on the bucket.
3. Set `GCS_BUCKET_NAME` in `.env`.

## BigQuery Dataset Setup

1. Create a BigQuery dataset in your target project.
2. Grant the service account `roles/bigquery.dataEditor` and `roles/bigquery.jobUser`.
3. Set `BIGQUERY_DATASET` in `.env`.

## Run the Pipeline Locally

```bash
python src/run_pipeline.py
```

This script will:
- Extract NHL data for the configured date range
- Save raw JSONL files locally
- Upload the file to GCS
- Load the file into BigQuery

## Run SQL Transformations

Use the SQL files in the `sql/` directory to create the raw and analytics tables.

```bash
bq query --use_legacy_sql=false < sql/01_create_raw_table.sql
bq query --use_legacy_sql=false < sql/02_create_analytics_table.sql
```

## Dashboard

A Looker Studio dashboard can be built using the analytics table created in BigQuery.

Looker Studio dashboard link: ADD_LINK_HERE

## Security Best Practices

- Do not commit `.env` or service account keys.
- Use IAM least privilege.
- Use service accounts for application access.
- Keep credentials local and private.

## Reliability and Scalability

- The pipeline is rerunnable for any date range.
- Raw data is preserved in GCS as JSONL.
- BigQuery load uses append mode so new data can be added safely.
- Scripts are modular and easy to extend.

## Limitations

- Depends on the availability of the public NHL API.
- This is a batch refresh pipeline, not a real-time stream.
- Data quality depends on the API response schema.

## Submission

- GitHub repo link: ADD_LINK_HERE
- Commit ID: ADD_COMMIT_ID_HERE
- Dashboard link: ADD_LINK_HERE
