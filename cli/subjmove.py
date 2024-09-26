
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

import pandas


 
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



def build_create_subject_in_project_str(subject_id, project_id, label=None):

    query = f"/data/projects/{project_id}/subjects/{subject_id}"

    if label:
        if query.endswith("true"):
            query = query + f"&label={label}"
        else :
            query = query + f"?label={label}"

    return query



# Code execution flow starts here:
 
# Parse 'projects.csv' CSV file to get XNAT host, and source and destination projects
# Right now, the format of this file is just 2 fields per line, akin to a key-value
# setup of a dictionary, but as a CSV.  For now, this file just needs to set 3 pairs
# of values: xnat host, source project for the data being moved, and the destination
# project to where the data will be moved.  Parsing is set up to be case-insensitive,
# and will look for combinations of shorter words, instead of rigidly defined phrases.
# Hopefully, this flexibility will not be abused ... ;)

with open ('projects.csv') as projects_id_file:
   projects_and_host = csv.reader(projects_id_file) # can add delimiter=','
                                                    # but default seems fine.
   for row in projects_and_host:
      if (len(row) > 1):
         # remove white space, if used to improve readability
         this_row_key   = row[0].replace(' ', '')
         this_row_value = row[1].replace(' ', '')

         if (('host' in this_row_key.lower()) and ('xnat' in this_row_key.lower())):
            xnat_url = this_row_value
         if (('proj' in this_row_key.lower()) and (('source' in this_row_key.lower()) or ('src' in this_row_key.lower()))):
            project_src = this_row_value
         if (('proj' in this_row_key.lower()) and ('dest' in this_row_key.lower())):
            project_dest = this_row_value

print ("XNAT host is: " + xnat_url + " src project is: " + project_src + " dest project is: " + project_dest)



# Now, read in list of datasets to be queried for, and manipulated
read_in_data = pandas.read_csv('datasets.csv', skipinitialspace=True)
search_terms = ','.join(read_in_data.columns.values.tolist())  # store column headers so they can be used for queries
                                                               # and matched up with queried searches from database.

# Convert subject ID to string, as in default case, their MRN shows up as an int
# XNAT query returns the subject ID as a string, so make consistent with that.
if ('subject_label' in search_terms):
   read_in_data['subject_label'] = read_in_data['subject_label'].astype(str)

print("Keys queried: " + str(search_terms))
print("Data read in from file are:\n" + str(read_in_data[read_in_data.columns.values.tolist()]))



# Log into XNAT instance
user = getpass.getuser()
print ("current user is {}".format(user))
password = getpass.getpass(prompt="Please enter Password : ")

with requests.sessions.Session() as connect:
   
    connect.auth     = (user, password)
    connect.xnaturl  = xnat_url
    connect.base_url = f'{xnat_url}/data/projects/{project_src}'

    # test connection
    response = connect.get(connect.base_url)
    if not response.ok:
        warnings.warn("You can't access xnat project {project_src} with the credenctials provided.")
        connect.close()
        sys.exit("Exiting program")

    # Checking for experiments (sessions?) in a project ... using search keys specified in 'datasets.csv'
    # file, or other specified file, read in above
    connect.base_url = f'{xnat_url}/data/projects/{project_src}/experiments?columns={search_terms}'
    print ("********* Connecting base search URL is: " + str(connect.base_url))
    project_all_data_src = connect.get(connect.base_url)

    # Set of experiments are returned in an 'array of dictionaries' structure. For each experiment/session,
    # the experiment name/label # should be the 'label' key in that dictionary, and subjects' ID should be
    # available under 'subject_label' key.

    # Read resulting JSON from 'connect' method directly into Pandas data frame.
    project_data_src_df = pandas.DataFrame(project_all_data_src.json()['ResultSet']['Result'])

    # and print the sets of data correspong to the types read in from the dataset CSV file
    print("Data queried from source project are:\n" + str(project_data_src_df[read_in_data.columns.values.tolist()]))

    # Now - repeat above steps, so we can also get a listing of data already in destination project
    connect.base_url = f'{xnat_url}/data/projects/{project_dest}/experiments?columns={search_terms}'
    print ("********* Connecting base search URL is: " + str(connect.base_url))
    project_all_data_dest = connect.get(connect.base_url)

    project_data_dest_df = pandas.DataFrame(project_all_data_dest.json()['ResultSet']['Result'])

    print("Data queried from destination project are:\n" + str(project_data_dest_df[read_in_data.columns.values.tolist()]))

    # So now we have (as data frames):
    #
    # - project_data_src_df  == data frame of data from source project
    #
    # - project_data_dest_df == data frame of data from destination  project
    #
    # - read_in_data         == list of data, read in from file, to be transferred from
    #                           source to destination projects

    # Testing for subject in source project - will eventually have to be done in destination
    # project, as if the subject doesn't exist there, they will get created.  But since all
    # data are in Pandas' DataFrames, the technique for checking should be the same.

    # print("Subjects queried are: " + str(read_in_data['subject_label'].tolist()))

    # print("Subjects in source are: " + str(project_data_src_df['subject_label'].tolist()))

    subjects_in_dest = project_data_dest_df['subject_label'].tolist()
    for subject in read_in_data['subject_label'].tolist():
        if (subject in subjects_in_dest):
            print ("Subject %s already exists in %s project" % (subject, project_dest))
        else:
            print ("Subject %s not in %s project. Needs to be created if moving data." % (subject, project_dest))

            # Build ReST API string to create subject in destination project
            subject_query = build_create_subject_in_project_str(subject, project_dest)
            # print(subject_query)

            # Now, connect to XNAT, and create the subject
            r = connect.put(f"{xnat_url}{subject_query}")
            # print("status code:"+str(r.status_code))

            if r.status_code == 201:
                print("worked - created subject " + subject + " in project " + project_dest)
                subjects_in_dest.append(subject)
            else :
                print("failed - check subject information for subject " + subject)

        # At this point, the subject should be created in the destination project, so
        # we should now be able to move session of data from source to destination.

# # This now moves pairs of studies, not just moves one study at a time
# # These 2 lines not used - replaced with entries from from fields 1-2 in text file
# #    expID = scans["xnat:mrSessionData/id"].to_list()
# #    print (expID)
    # for i in range(2,3):
        # print("working on",i)
        # expID = fields[i] # in this case I know it's only one. Could loop through a list.
        # print ("expID", expID)
        # # queryexp = move_exp_or_subj(xnatID, project_src, project_dest, id_experiment=expID, changeprimary=True, label=None)
# 
        # # print(queryexp)

# #    for exp in expID:
        # r = connect.put(f"{xnat_url}{queryexp}")
        # if r.status_code == 200:
            # print("worked - moved " + xnatID + " " + expID + "from project to" + project_dest)
        # else :
            # print("failed - check subject information for" + xnatID + " " + expID)
 
