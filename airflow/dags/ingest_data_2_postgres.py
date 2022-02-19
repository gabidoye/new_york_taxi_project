#from aifc import Aifc_read
import os
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from ingest_script import ingest_callable

Airflow_Home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
url_prefix = 'https://s3.amazonaws.com/nyc-tlc/trip+data'
url_template= url_prefix + '/yellow_tripdata_2021-01.csv'
#url_template = url_prefix + '/yellow_tripdata_{{ execution_date.strftime(\'%Y-%m\') }}.csv'
output_file_template= Airflow_Home +'/output_{{ execution_date.strftime(\'%Y-%m\') }}.csv'
table_name_template= 'yellow_taxi_{{ execution_date.strftime(\'%Y_%m\') }}'

PG_HOST = os.getenv('PG_HOST')
PG_DATABASE = os.getenv('PG_DATABASE')
PG_USER =os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_PORT=os.getenv('PG_PORT')


load_workflow= DAG(
    "ingest_2_postgres_dag", 
    catchup=True,
    schedule_interval="0 6 2 * *",
    #start_date= datetime(2022, 1, 1),
    start_date=days_ago(1),
    #end_date = datetime(2022,12,31),
    max_active_runs= 3

)

with load_workflow:
    curl_jobs= BashOperator(
        task_id='wget2',
        bash_command=f'curl -sSLf {url_template} > {output_file_template}'
    )

    ingest_jobs = PythonOperator(
        task_id="ingest2",
        python_callable=ingest_callable,
        op_kwargs=dict(
            user=PG_USER,
            password =PG_PASSWORD,
            host =PG_HOST,
            port =PG_PORT,
            db = PG_DATABASE,
            table_name = table_name_template,
            csv_file = output_file_template
        )
    )





curl_jobs >> ingest_jobs