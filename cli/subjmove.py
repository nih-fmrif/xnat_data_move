
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 15 09:40:58 2024
 
@author: zugmana2
"""
 
import requests
#import pandas as pd
#import json
import sys
#import os
#from downloadtools.utils import simplifystring
from downloadtools.restutilities import listsession
import warnings
import getpass
 
def subjectmove (subjectid,sourceproject,destproject,changeprimary=True,label=None):
    #primary
    query = f"/data/projects/{sourceproject}/subjects/{subjectid}/projects/{destproject}"
    if changeprimary:
        query = query + "?primary=true"
    if label:
        if query.endswith("true"):
            query = query + f"&label={label}"
        else :
            query = query + f"?label={label}"
    return query
    #PUT - /data/projects/{original-project-id}/subjects/{subject-id | subject-label}/projects/{shared-project-id}
def experimentmove (subjectid,experiment_id,sourceproject,destproject,changeprimary=True,label=None):
#def experimentmove (subjectid,subjectlabel,experiment_id,sourceproject,destproject,changeprimary=True,label=None):
 
    #/data/projects/{original-project-id}/subjects/{subject-id | subject-label}/experiments/{experiment-id | experiment-label}/projects/{shared-project-id}
    query = f"/data/projects/{sourceproject}/subjects/{subjectid}/experiments/{experiment_id}/projects/{destproject}"
# these did not work
#    query = f"/data/projects/{sourceproject}/subjects/{subjectid}/experiments/{experiment_id}/projects/{destproject}/subjects/{subjectid}"
#    query = f"/data/projects/{sourceproject}/subjects/{subjectid | subjectlabel}/experiments/{experiment_id}/projects/{destproject}"
 
    if changeprimary:
        query = query + "?primary=true"
    if label:
        if query.endswith("true"):
            query = query + f"&label={label}"
        else :
            query = query + f"?label={label}"
    return query
 
 
user = getpass.getuser()
print ("current user is {}".format(user))
password = getpass.getpass(prompt="Please enter Password : ")
 
xnaturl = https://fmrif-xnat.nimh.nih.gov
#This is the project where the data is currently located
project = "EDB_test"
#This is the new project where the data will be moved
destproject = "EDB-NIMH"
 
# original code
#project = "01-M-0192"
#destproject = "Testtreansfer"
 
#project = "ETPB-lost"
#destproject = "01-M-0192"
 
#read in file with studies to move
file = open('test3.txt')
# field[0] is SDAN number, field[1] is MRN, the remaining fields list MR session number
for line in file:
    fields = line.strip().split()
# Use this line for a subject with one study
    print("Working on these studies for",fields[0],"/",fields[1],":",fields[2])
# Use this line for subject with 2 studies
#    print("Working on these studies for",fields[0],"/",fields[1],":",fields[2], fields[3])
 
with requests.sessions.Session() as connect:
   
    connect.auth = (user, password)
    connect.xnaturl = xnaturl
    connect.project = project
    connect.base_url = f'{xnaturl}/data/projects/{project}'
    # test connection
    response = connect.get(connect.base_url)
    if not response.ok:
        warnings.warn("You can't access xnat project {project} with the credenctials provided.")
        sys.exit("Ending program")
    allsessions = listsession(connect)
    #match by whatever
    #lets say study instance uid
    instances = []
    # Get subject IDs
# Do not use these
#    scans = allsessions[allsessions['xnat:mrsessiondata/uid'].str.contains('|'.join(instances))]
#    xnatID = scans["xnat:mrsessiondata/subject_id"].unique()
#    xnatID = xnatID[0] # in this case I know it's only one. Could loop through a list.
#    xnatID = scans["xnat:mrsessiondata/subject_id"].unique()
#    xnatID = scans["xnat:mrsessiondata/label"].unique()
#    print ("xnatID=",xnatID)
 
# Use this: this line assigns SubjectID to xnatID - comes from from first field in text file
    xnatID = fields[1] # in this case I know it's only one. Could loop through a list.
    xnatLABEL = fields[1] # in this case I know it's only one. Could loop through a list.
 
 
# maybe not needed with list as ID entries - moving data for all dates for a subject?
#    query = subjectmove(xnatID,project,destproject,changeprimary=True,label=None)
#    print(query)
#    r = connect.put(f"{xnaturl}{query}")
#    if r.status_code == 200:
#        print("worked")
#    else :
#        print("fail")
#    # Because of for loop moves all the data in project!!! below is not necessary unless the subject is already shared
#    expID = scans["xnat:mrsessiondata/id"].to_list()
#    print (expID)
#    expID = 'FMRIF_E81411' # in this case I know it's only one. Could loop through a list.
#    print ("expID",expID)
#    for exp in expID:
#        print(exp)
#        queryexp = experimentmove(xnatID,exp,project,destproject,changeprimary=True,label=None)
#        print(queryexp)
#        r = connect.put(f"{xnaturl}{queryexp}")
#        if r.status_code == 200:
#            print("worked")
#        else :
#            print("fail")
 
 
# This now moves pairs of studies, not just moves one study at a time
# These 2 lines not used - replaced with entries from from fields 1-2 in text file
#    expID = scans["xnat:mrsessiondata/id"].to_list()
#    print (expID)
    for i in range(2,3):
        print("working on",i)
        expID = fields[i] # in this case I know it's only one. Could loop through a list.
        print ("expID",expID)
        queryexp = experimentmove(xnatID,expID,project,destproject,changeprimary=True,label=None)
#        queryexp = experimentmove(xnatID,xnatLABEL,expID,project,destproject,changeprimary=True,label=None)
        print(queryexp)
# not needed - pulls all the studies in a project
#    for exp in expID:
        r = connect.put(f"{xnaturl}{queryexp}")
        if r.status_code == 200:
            print("worked - moved " + xnatID + " " + expID + "from project to" + destproject)
        else :
            print("failed - check subject information for" + xnatID + " " + expID)
 
