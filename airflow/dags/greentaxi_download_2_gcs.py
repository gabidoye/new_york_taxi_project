#from aifc import Aifc_read
import os
import logging
import pyarrow.csv as pv
import pyarrow.parquet as pq
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "dataengineering-bizzy")
BUCKET = os.environ.get("GCP_GCS_BUCKET", "dtc_data_lake_dataengineering-bizzy")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'taxi_rides_ny')

Airflow_Home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
url_prefix = 'https://s3.amazonaws.com/nyc-tlc/trip+data'
url_template = url_prefix + '/green_tripdata_{{ execution_date.strftime(\'%Y-%m\') }}.csv'
output_file_template= Airflow_Home +'/output_{{ execution_date.strftime(\'%Y-%m\') }}.csv'
parquet_file = 'output_{{ execution_date.strftime(\'%Y-%m\') }}.parquet'
#parquet_file = Airflow_Home +'/output_*.parquet'



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
    "green_taxi_download_ingest_2_gcs_dag", 
    catchup=True,
    schedule_interval="0 6 2 * *",
    start_date= datetime(2019, 1, 1),
    end_date = datetime(2020,12,31),
    max_active_runs= 3

)

with load_workflow:

    curl_green= BashOperator(
        task_id='download_file_url',
        bash_command=f'curl -sSL {url_template} > {output_file_template}'
    )
    
    format_to_parquet_task = PythonOperator(
        task_id="format_2_parquet_task",
        python_callable=format_2_parquet,
        op_kwargs={
            "src_file": f"{output_file_template}",
        },
    )

    local_to_gcs_green = PythonOperator(
        task_id="local_to_gcs_green",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw/greentaxi/{parquet_file}",
            "local_file": f"{Airflow_Home}/{parquet_file}",
        },
        
    )

    bigquery_external_table_green = BigQueryCreateExternalTableOperator(
        task_id="bigquery_external_table_green",
        table_resource={
            "tableReference": {
                "projectId": PROJECT_ID,
                "datasetId": BIGQUERY_DATASET,
                "tableId": "external_table",
            },
            "externalDataConfiguration": {
                "sourceFormat": "PARQUET",
                "sourceUris": [f"gs://{BUCKET}/raw/greentaxi/{parquet_file}"],
            },
        },
    )

    cleanup_green= BashOperator(
        task_id='cleanup_csv',
        bash_command=f'rm {output_file_template}'
    )




curl_green >> format_to_parquet_task >> local_to_gcs_green >> bigquery_external_table_green >> cleanup_green 