#from aifc import Aifc_read
import os
import logging
import pyarrow.csv as pv
import pyarrow.parquet as pq
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import os
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/Users/gabidoye/Downloads/dataengineering-bizzy-770f13466383.json"

from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator

#GOOGLE_APPLICATION_CREDENTIALS="/Users/gabidoye/Downloads/dataengineering-bizzy-770f13466383.json"
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "dataengineering-bizzy")
BUCKET = os.environ.get("GCP_GCS_BUCKET", "dtc_data_lake_dataengineering-bizzy")
BIGQUERY_DATASET = os.environ.get("FHV_DATASET", 'fhv_trips_data')

Airflow_Home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
url = 'https://s3.amazonaws.com/nyc-tlc/misc/taxi+_zone_lookup.csv'
output_file_template= Airflow_Home +'/taxi+_zone_lookup.csv'
parquet_file = 'taxi+_zone_lookup.parquet'


def format_2_parquet(src_file):
    if not src_file.endswith('.csv'):
        logging.error("Can only accept source files in CSV format, for the moment")
        return
    table = pv.read_csv(src_file)
    pq.write_table(table, src_file.replace('.csv', '.parquet'))

# NOTE: takes 20 mins, at an upload speed of 800kbps. Faster if your internet has a better upload speed
def upload_to_gcs(bucket, object_name, local_file):
    """
    Ref: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python
    :param bucket: GCS bucket name
    :param object_name: target path & file-name
    :param local_file: source path & file-name
    :return:
    """
    # WORKAROUND to prevent timeout for files > 6 MB on 800 kbps upload speed.
    # (Ref: https://github.com/googleapis/python-storage/issues/74)
    storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 5 MB
    storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 5 MB
    # End of Workaround
    client = storage.Client()
    bucket = client.bucket(bucket)

    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_file)



load_workflow= DAG(
    "zone_ingest_2_gcs_dag", 
    catchup=False,
    schedule_interval="0 6 2 * *",
    start_date= datetime(2019, 1, 1)
)

with load_workflow:

    curl_zone_job= BashOperator(
        task_id='zone_file_url',
        bash_command=f'curl -sSLf {url} > {output_file_template}'
    )
    
    format_csv_to_parquet_task = PythonOperator(
        task_id="format_csv_2_parquet_task_zone",
        python_callable=format_2_parquet,
        op_kwargs={
            "src_file": f"{output_file_template}",
        },
    )

    upload_to_gcs_job = PythonOperator(
        task_id="upload_to_gcs_job_zone",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw/zone/{parquet_file}",
            "local_file": f"{Airflow_Home}/{parquet_file}",
        },
        
    )

    cleanup_job= BashOperator(
        task_id='cleanup_csv_zone',
        bash_command=f'rm {output_file_template}'
    )


curl_zone_job >> format_csv_to_parquet_task >> upload_to_gcs_job >> cleanup_job