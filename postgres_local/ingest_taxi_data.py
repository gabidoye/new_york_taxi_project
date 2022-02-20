#!/usr/bin/env python
# coding: utf-8
import pandas as pd
from sqlalchemy import create_engine
from time import time
import os
import argparse

def main(params):
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    database = params.database
    table_name = params.table_name
    url = params.url
    csv_name = 'output.csv'     # download the csv    

    os.system(f"wget {url} -O {csv_name}")

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')

    df_iterator =pd.read_csv(csv_name, iterator=True, chunksize=100000)

    df2=next(df_iterator)

    df2.tpep_pickup_datetime = pd.to_datetime(df2.tpep_pickup_datetime)
    df2.tpep_dropoff_datetime = pd.to_datetime(df2.tpep_dropoff_datetime)

    df2.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace') 

    df2.to_sql(name=table_name, con=engine, if_exists='replace')

    while True:
        t_start = time()
    
        df2 =next(df_iterator)
    
        df2.tpep_pickup_datetime = pd.to_datetime(df2.tpep_pickup_datetime)
        df2.tpep_dropoff_datetime = pd.to_datetime(df2.tpep_dropoff_datetime)
    
        df2.to_sql(name=table_name, con=engine, if_exists='append')
        
        t_end = time()
    
        print('inserted another chunk..., took %.3f second' %(t_end - t_start))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Ingest CSV data  to PostgreSql.')

    parser.add_argument('--user', help= 'username for connecting to postgresDB')
    parser.add_argument('--password', help= 'password for connecting to postgresDB')
    parser.add_argument('--host', help= 'host for postgresDB')
    parser.add_argument('--port', help= 'port to postgresDB')
    parser.add_argument('--database', help= 'DB to connect to in postgres')
    parser.add_argument('--table_name', help= 'name of the table to load')
    parser.add_argument('--url', help= 'username for connecting to postgresDB')
    

    args = parser.parse_args()
    
    main(args)
