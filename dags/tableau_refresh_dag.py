import json
from datetime import datetime, timedelta

from airflow.decorators import dag, task # DAG and task decorators for interfacing with the TaskFlow API
from airflow.models import Variable

import tableauserverclient as tsc
import pandas as pd
import tableau_utils as tu

@dag(
    # This defines how often your DAG will run, or the schedule by which your DAG runs. In this case, this DAG
    # will run every 30 mins
    schedule_interval=timedelta(minutes=30),
    # This DAG is set to run for the first time on January 1, 2021. Best practice is to use a static
    # start_date. Subsequent DAG runs are instantiated based on scheduler_interval
    start_date=datetime(2021, 1, 1),
    # When catchup=False, your DAG will only run for the latest schedule_interval. In this case, this means
    # that tasks will not be run between January 1, 2021 and 30 mins ago. When turned on, this DAG's first
    # run will be for the next 30 mins, per the schedule_interval
    catchup=False,
    tags=['tableau']) # If set, this tag is shown in the DAG view of the Airflow UI
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
    def update_tableau():
        """
        #### Update Tableau
        Finds list of dashboards and kicks off the updats.
        """
        #server = tu._connect_server(server_name)
        #tu._connection_builder(token_name,token_value,site_id,server)
        pattern = "Financial Statements - Sandbox"
        df = tu.retreive_workbook_list(pattern,server_name,token_name,token_value,site_id)
        job_ids = tu.update_all_workbooks(df,server_name,token_name,token_value,site_id)
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