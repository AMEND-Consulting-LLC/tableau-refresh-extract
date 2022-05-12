import tableauserverclient as tsc
import pandas as pd

def _connection_builder(token_name,token_value,site_id,server):
    """Builds tableau auth and attempts to connect using it."""
    tableau_auth = tsc.PersonalAccessTokenAuth(token_name,token_value,site_id=site_id)
    try:
        with server.auth.sign_in(tableau_auth): 
            # commenting check out until we have better creds
            #all_sites, pagination_item = server.site.get()
            print("Auth passed for {0}".format(token_name))
    except:
        print("Error while authenticating.")
    return tableau_auth

def _connect_server(name):
    """Connect to server and return server object"""
    server = tsc.Server(name, use_server_version=True)
    try:
        s_info = server.server_info.get()
        print("Connected to server")
        #print("\nServer info:")
        #print("\tProduct version: {0}".format(s_info.product_version))
        #print("\tREST API version: {0}".format(s_info.rest_api_version))
        #print("\tBuild number: {0}".format(s_info.build_number))
    except BaseException as e:
        print("Error connecting to server.")
        print(e)
        raise
    return server

def _workbooks_to_update(pattern,server,tableau_auth,req_options = None):
    """Returns list of workbooks using filter options"""
    req_option = tsc.RequestOptions()
    req_option.filter.add(tsc.Filter(tsc.RequestOptions.Field.ProjectName,
                                tsc.RequestOptions.Operator.Equals,
                                pattern))
    
    if(req_options != None):
        print("Using filter overwrite")
        req_option = req_options

    #print("Retrieving workbook list")
    with server.auth.sign_in(tableau_auth):  
        all_workbooks_items, pagination_item = server.workbooks.get(req_option)
    
    #creating holding dataframe
    columns = ['name','wb_id','owner_id','wb_object']
    df = pd.DataFrame(columns=columns)
    for workbook in all_workbooks_items:
        #print(workbook.name, workbook.id)
        #print(workbook.owner_id)
        data = {}
        data['name'] = workbook.name
        data['wb_id'] = workbook.id
        data['owner_id'] = workbook.owner_id
        data['wb_object'] = workbook
        data = pd.DataFrame([data])
        #print(data)
        df = pd.concat([df,data],ignore_index=True)
    print("Retrieved workbooks")
    return df

def _refresh_workbook(workbook_id,server,tableau_auth):
    """Trigger workbook refresh and return job object"""
    job_id = ""
    with server.auth.sign_in(tableau_auth):
        # get the workbook item from the site
        try:
            workbook = server.workbooks.get_by_id(workbook_id)    
            print("Found workbook: {}".format(workbook.name))
        except BaseException as e:
            print("Error finding workbook: {}".format())
            print(e)
            raise

        # call the update method        
        try:
            job = server.workbooks.refresh(workbook)
            print("Job started {}".format(job.id))
            job_id = job.id
        except BaseException as e:
            #consider re writting this error to 
            print("Error executing job", e)
            raise
    return job

def _await_job(job_id,server,tableau_auth,timeout=600):
    """Waits for job to complete and returns job info""" 

    with server.auth.sign_in(tableau_auth):
        try:
            #print(job_id)
            # Waits for job to complete 
            # Finish code code = 1 is error
            jobinfo = server.jobs.wait_for_job(job_id,timeout=timeout)
            #print(jobinfo)
            #print("Job finished with code: {}".format(jobinfo.finish_code))
        except:
            print("Error waiting for response for jobid: {}".format(job_id))
            raise
    return jobinfo

def retreive_workbook_list(pattern,server_name,token_name,token_value,site_id):
    """Retreive list of workbooks"""
    server = _connect_server(server_name)
    auth = _connection_builder(token_name,token_value,site_id,server)
    workbooks_df = _workbooks_to_update(pattern,server,auth)
    return workbooks_df

def update_all_workbooks(workbook_df,server_name,token_name,token_value,site_id,report_job_failure=False):
    """Refresh all workbooks"""
    server = _connect_server(server_name)
    auth = _connection_builder(token_name,token_value,site_id,server)
    job_ids = []

    error_flag = False
    #print(workbook_df.head())
    for index, row in workbook_df.iterrows():
        #print(row)
        try:
            job_id = _refresh_workbook(row.wb_id,server,auth)
            job_ids.append(job_id.id)
            #print(job_ids.id)
        except:
            error_flag = True
            print("Failed to refresh workbook: {0}".format(row.name))
    
    if(error_flag & report_job_failure):
        print("Error detected, failing in style.")
        raise

    print("Num jobs started: {}".format(len(job_ids)))
    return job_ids

def await_by_group(job_ids,server_name,token_name,token_value,site_id,report_job_failure=False):
    """Awaits the completion of all jobs.  Note that this check is sequential as fi-fo queuing."""
    server = _connect_server(server_name)
    auth = _connection_builder(token_name,token_value,site_id,server)
    error_flag = False

    if(len(job_ids) == 0):
        print("No jobs to check, issue may have occured")
        return 1

    for job in job_ids:
        job_id = job
        print("Checking job id: {}".format(job_id))
        try:
            job_details = _await_job(job_id,server,auth,timeout=600)
        except BaseException as e:
            print("Error awaiting job: {}".format(job))
            print(e)
            continue
        print("Job id: {0} completed at: {1} with code {2}".format(job_details.id,
                                            job_details.completed_at,
                                            job_details.finish_code))
        if(job_details.finish_code == 1):
            print("JOB {} FAILED".format(job_details.id))
            error_flag = True
    
    if(error_flag & report_job_failure):
        print("Error detected, failing in style.")
        raise
    return 0
        

