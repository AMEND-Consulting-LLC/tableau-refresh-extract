from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable

import tableauserverclient as tsc
import pandas as pd
import tableau_utils as tu

default_args = {
    "owner": "Airflow",
    "depends_on_past": False,
    "start_date": "2020-12-17",
    "email": ["statewide@amendllc.com"],
    "email_on_failure": False,
}

dag = DAG(
    "sss_tableau_refresh",
    default_args=default_args,
    schedule_interval=None,
)

dag.doc_md = """
    ### Basic ETL Dag
    Kicks off refresh extract.
"""

#hard coding for easy setup, could be back migrated to variables if needed

site_id = "statewidesafetysystems"
token_name = "refresh-token-ag"
token_value = "53MOfbqBRxSxCgMCrYWukw==:YE5j6jKyT2l3aI5U7Ud8D4VC32b2Ef2f"
server_name = 'https://10ay.online.tableau.com/'
pattern = "Financial Statements - Sandbox"

def update_tableau():
    """
    #### Update Tableau
    Finds list of dashboards and kicks off the updats.
    """
    df = tu.retreive_workbook_list(pattern,server_name,token_name,token_value,site_id)
    #job_ids = tu.update_all_workbooks(df,server_name,token_name,token_value,site_id)
    job_ids = [1]
    return job_ids

def check_job(**kwargs):
    """
    #### checks if job is complete
    """
    ti = kwargs['ti']
    ls = ti.xcom_pull(task_ids='update_tableau')
    job_ids = ls
    tu.await_by_group(job_ids,server_name,token_name,token_value,site_id)
    return 1

update_tableau = PythonOperator(
    task_id="update_tableau",
    provide_context=True,
    python_callable=update_tableau,
    dag=dag,
)

check_job = PythonOperator(
    task_id="check_job",
    provide_context=True,
    python_callable=check_job,
    dag=dag,
)

update_tableau >> check_job