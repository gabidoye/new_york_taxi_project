#from aifc import Aifc_read
import os
import logging
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "dataengineering-bizzy")
BUCKET = os.environ.get("GCP_GCS_BUCKET", "dtc_data_lake_dataengineering-bizzy")


Airflow_Home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
url_prefix = 'https://s3.amazonaws.com/nyc-tlc/trip+data'
url_template = url_prefix + '/green_tripdata_{{ execution_date.strftime(\'%Y-%m\') }}.csv'
output_file_template= Airflow_Home +'/output_{{ execution_date.strftime(\'%Y-%m\') }}.csv'
csv_file = 'output_{{ execution_date.strftime(\'%Y-%m\') }}.csv'
clear_file = Airflow_Home +'/output_*.csv'


# NOTE: takes 20 mins, at an upload speed of 800kbps. Faster if your internet has a better upload speed
def upload_to_gcs(bucket, object_name, local_file):
    
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
    "green_taxi_download_csv", 
    catchup=True,
    schedule_interval="0 6 2 * *",
    start_date= datetime(2019, 1, 1),
    end_date = datetime(2020,12,31),
    max_active_runs= 3

)

with load_workflow:

    curl_csv_job= BashOperator(
        task_id='green_csv_file_url',
        bash_command=f'curl -sSL {url_template} > {output_file_template}'
    )

    local_to_gcs_job = PythonOperator(
        task_id="green_csv_to_gcs_job",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw_green_csv/{csv_file}",
            "local_file": f"{Airflow_Home}/{csv_file}",
        },
        
    )

    cleanup_job= BashOperator(
        task_id='cleanup_csv',
        bash_command=f'rm {output_file_template}'
    )




curl_csv_job >> local_to_gcs_job >> cleanup_job