#!/usr/bin/env python
# coding: utf-8

import os
from time import time
import pandas as pd
from sqlalchemy import create_engine


def ingest_callable(user, password,host, port, db, table_name, csv_file):
    print(table_name, csv_file)

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    engine.connect()

    print('connection established successfully, inserting date...')

    t_start = time()
    df_iterator =pd.read_csv(csv_file, iterator=True, chunksize=100000)

    df2=next(df_iterator)

    df2.tpep_pickup_datetime = pd.to_datetime(df2.tpep_pickup_datetime)
    df2.tpep_dropoff_datetime = pd.to_datetime(df2.tpep_dropoff_datetime)

    df2.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace') 

    df2.to_sql(name=table_name, con=engine, if_exists='append')
    t_end = time()

    while True:
        t_start = time()
    
        df2 =next(df_iterator)
    
        df2.tpep_pickup_datetime = pd.to_datetime(df2.tpep_pickup_datetime)
        df2.tpep_dropoff_datetime = pd.to_datetime(df2.tpep_dropoff_datetime)
    
        df2.to_sql(name=table_name, con=engine, if_exists='append')
        
        t_end = time()
    
        print('inserted fisrt chunk..., took %.3f second' %(t_end - t_start))




