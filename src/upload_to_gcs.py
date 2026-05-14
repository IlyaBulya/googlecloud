import os

from google.cloud import storage


def upload_to_gcs(local_file_path: str, bucket_name: str, start_date: str, end_date: str) -> str:
    print(f"Uploading {local_file_path} to GCS bucket {bucket_name}")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    if not bucket.exists():
        raise RuntimeError(f"GCS bucket does not exist: {bucket_name}")

    blob_path = (
        f"raw/nhl_games/start_date={start_date}/end_date={end_date}/"
        f"{os.path.basename(local_file_path)}"
    )
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(local_file_path)
    gcs_uri = f"gs://{bucket_name}/{blob_path}"
    print(f"Uploaded file to {gcs_uri}")
    return gcs_uri
