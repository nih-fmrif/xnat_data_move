
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Fri Mar 15 09:40:58 2024
 
@author: zugmana2

Forked on 2024-08-28

roopchansinghv
"""
 
import requests
import sys
import warnings
import getpass
import csv


 
def move_exp_or_subj (id_subject, project_src, project_dest, id_experiment=None, changeprimary=True, label=None):

    if id_experiment is None:
        # just work on subject
        query = f"/data/projects/{project_src}/subjects/{id_subject}/projects/{project_dest}"
    else:
        query = f"/data/projects/{project_src}/subjects/{id_subject}/experiments/{id_experiment}/projects/{project_dest}"

    if changeprimary:
        query = query + "?primary=true"
    if label:
        if query.endswith("true"):
            query = query + f"&label={label}"
        else :
            query = query + f"?label={label}"

    return query
    #PUT - /data/projects/{original-project-id}/subjects/{subject-id | subject-label}/projects/{shared-project-id}



def listsession(session,xnatid = None ,date = None):
    columns = ''.join(('xnat:subjectData/label,',
                       #'xnat:subjectData/ID,',
                       'xnat:mrSessionData/label,',
                       'xnat:mrSessionData/ID,',
                       'xnat:mrSessionData/date,',
                       'xnat:mrSessionData/project,',
                       'URI,',
                       'xnat:mrSessionData/UID'))

    if xnatid == None:
        query = f'{session.base_url}/experiments/?format=json&columns={columns}'
    else:
        query = f'{session.base_url}/subjects/{xnatid}/experiments/?format=json&columns={columns}'
    
    if date == "":
        date = None
    if date:
        query = f'{query}&date={date}'

    print(query)

    try:
        # returns a dictionary with main key: 'ResultSet', and nested dictionary with main key: 'Result'
        result = session.get(query)
    except:
        print("there was an error connecting. please check credentials and if you have access to project")
        sys.exit()

    # data = pd.DataFrame.from_dict(result.json()['ResultSet']['Result'])
    data = result.json()['ResultSet']['Result']

    return data



# Code that gets executed here
user = getpass.getuser()
print ("current user is {}".format(user))
password = getpass.getpass(prompt="Please enter Password : ")
 
xnaturl = 'https://fmrif-xnat.nimh.nih.gov'
# This is the project where the data is currently located
project_src  = "Enter-src-project-ID-here"
# This is the new project where the data will be moved
project_dest = "Enter-dest-project-ID-here"
 
# #read in file with studies to move
# file = open('test3.txt')
# # field[0] is SDAN number, field[1] is MRN, the remaining fields list MR session number
# for line in file:
    # fields = line.strip().split()
    # # Use this line for a subject with one study
    # print("Working on these studies for",fields[0],"/",fields[1],":",fields[2])
    # # Use this line for subject with 2 studies
    # # print("Working on these studies for",fields[0],"/",fields[1],":",fields[2], fields[3])
 
with requests.sessions.Session() as connect:
   
    connect.auth = (user, password)
    connect.xnaturl = xnaturl
    connect.project = project_src
    connect.base_url = f'{xnaturl}/data/projects/{project_src}'

    # test connection
    response = connect.get(connect.base_url)
    if not response.ok:
        warnings.warn("You can't access xnat project {project_src} with the credenctials provided.")
        connect.close()
        sys.exit("Exiting program")

    # allsessions = listsession(connect)

    # print (allsessions)

    # Checking for experiments (sessions?) in a project ...
    connect.base_url = f'{xnaturl}/data/projects/{project_src}/experiments'
    experiments_all_in_proj = connect.get(connect.base_url)

    # print ("\n*** Experiments/Sessions in %s are: %s" % (project_src, str(experiments_all_in_proj.json()['ResultSet']['Result'])))

    # Set of experiments are returned in an 'array of dictionary' structures.  For each experiment/session, the experiment name/label
    # should be the 'label' key in that dictionary, but there doesn't seem to be a 'subject' key, at least not immediately accessible
    for each_session in experiments_all_in_proj.json()['ResultSet']['Result']:
        print ("*** Now handlding session: " + str(each_session['label']) + " done on " + str(each_session['date']))

    # Get subject IDs
# Do not use these
#    scans = allsessions[allsessions['xnat:mrsessiondata/uid'].str.contains('|'.join(instances))]
#    xnatID = scans["xnat:mrsessiondata/subject_id"].unique()
#    xnatID = xnatID[0] # in this case I know it's only one. Could loop through a list.
#    xnatID = scans["xnat:mrsessiondata/subject_id"].unique()
#    xnatID = scans["xnat:mrsessiondata/label"].unique()
#    print ("xnatID=",xnatID)
 
# # Use this: this line assigns SubjectID to xnatID - comes from from first field in text file
    # xnatID = fields[1] # in this case I know it's only one. Could loop through a list.
    # xnatLABEL = fields[1] # in this case I know it's only one. Could loop through a list.
 
# # This now moves pairs of studies, not just moves one study at a time
# # These 2 lines not used - replaced with entries from from fields 1-2 in text file
# #    expID = scans["xnat:mrsessiondata/id"].to_list()
# #    print (expID)
    # for i in range(2,3):
        # print("working on",i)
        # expID = fields[i] # in this case I know it's only one. Could loop through a list.
        # print ("expID", expID)
        # # queryexp = move_exp_or_subj(xnatID, project_src, project_dest, id_experiment=expID, changeprimary=True, label=None)
# 
        # # print(queryexp)

# #    for exp in expID:
        # r = connect.put(f"{xnaturl}{queryexp}")
        # if r.status_code == 200:
            # print("worked - moved " + xnatID + " " + expID + "from project to" + project_dest)
        # else :
            # print("failed - check subject information for" + xnatID + " " + expID)
 
