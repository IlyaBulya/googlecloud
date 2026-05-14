# Architecture

This batch pipeline extracts NHL game data from the public NHL API, stores raw data in Google Cloud Storage, loads it into BigQuery, and transforms it into analytics-ready tables.

## Data Flow

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

## Components

- `src/extract_nhl_data.py`: Extracts schedule and score data from the NHL API for a date range.
- `src/upload_to_gcs.py`: Uploads raw JSONL files to a configured GCS bucket.
- `src/load_to_bigquery.py`: Loads the raw JSONL files from GCS into a BigQuery raw table.
- `sql/01_create_raw_table.sql`: Creates the raw BigQuery schema.
- `sql/02_create_analytics_table.sql`: Creates an analytics-ready table with derived metrics.
- `sql/03_dashboard_queries.sql`: Provides example dashboard queries for Looker Studio.
