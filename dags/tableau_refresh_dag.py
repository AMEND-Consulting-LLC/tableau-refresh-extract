import json
from datetime import datetime, timedelta

from airflow.decorators import dag, task # DAG and task decorators for interfacing with the TaskFlow API
from airflow.models import Variable

import tableauserverclient as tsc
import pandas as pd
import tableau_utils as tu

args = {'pattern': "Financial Statements - Sandbox"}

@dag(
    schedule_interval='@once',
    start_date=datetime(2020,1,1),
    catchup=False,
    tags=['tableau'],
    default_args = args)
def tableau_refresh():
    """
    ### Basic ETL Dag
    Kicks off refresh extract.
    """
    site_id = Variable.get('TABLEAU_SITE_ID')
    token_name = Variable.get('TABLEAU_TOKEN_NAME')
    token_value = Variable.get('TABLEAU_TOKEN_VALUE')
    server_name = Variable.get('TABLEAU_SERVER_NAME')

    @task()
    def update_tableau(**kwargs):
        """
        #### Update Tableau
        Finds list of dashboards and kicks off the updats.
        """
        pattern = "Financial Statements - Sandbox"
        df = tu.retreive_workbook_list(pattern,server_name,token_name,token_value,site_id)
        #job_ids = tu.update_all_workbooks(df,server_name,token_name,token_value,site_id)
        job_is = [1]
        return job_ids

    @task() # multiple_outputs=True unrolls dictionaries into separate XCom values
    def check_job(job_ids: list):
        """
        #### checks if job is complete
        """
        tu.await_by_group(job_ids,server_name,token_name,token_value,site_id)
        return 1


    job_ids = update_tableau()
    order_summary = check_job(job_ids)

tableau_refresh = tableau_refresh()