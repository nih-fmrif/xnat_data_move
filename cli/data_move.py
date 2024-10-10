
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


 
def move_exp_or_subj (id_subject, project_src, project_dest, id_experiment=None, change_primary=True, label=None):

    if id_experiment is None:
        # just work on subject
        query = f"/data/projects/{project_src}/subjects/{id_subject}/projects/{project_dest}"
    else:
        query = f"/data/projects/{project_src}/subjects/{id_subject}/experiments/{id_experiment}/projects/{project_dest}"

    if change_primary:
        query = query + "?primary=true"
    if label:
        if query.endswith("true"):
            query = query + f"&label={label}"
        else :
            query = query + f"?label={label}"

    return query



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

print ("XNAT host: " + xnat_url + "; src project: " + project_src + "; dest project: " + project_dest)



# Now, read in list of datasets to be queried for, and manipulated
data_2_transfer = pandas.read_csv('datasets.csv', skipinitialspace=True)
search_terms    = ','.join(data_2_transfer.columns.values.tolist())  # store column headers so they can be used for queries
                                                                     # and matched up with queried searches from database.

# Convert subject ID to string, as in default case, their MRN shows up as an int,
# while an XNAT query returns the subject ID as a string, so make consistent with
# that.
if ('subject_label' in search_terms):
   data_2_transfer['subject_label'] = data_2_transfer['subject_label'].astype(str)

print("Keys queried: " + search_terms)
# print("Data read in from file are:\n" + str(data_2_transfer[data_2_transfer.columns.values.tolist()]))



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
    # file, or other specified file, read in above. Force to return session ID, if not already given.
    src_search_terms = search_terms + ',ID'
    connect.base_url = f'{xnat_url}/data/projects/{project_src}/experiments?columns={src_search_terms}'
    print ("********* Connecting base search URL is: " + str(connect.base_url))
    project_all_data_src = connect.get(connect.base_url)

    # Set of experiments are returned in an 'array of dictionaries' structure. For each experiment/session,
    # the experiment name/label # should be the 'label' key in that dictionary, and subjects' ID should be
    # available under 'subject_label' key.

    # Read resulting JSON from 'connect' method directly into Pandas data frame.
    project_data_src_df = pandas.DataFrame(project_all_data_src.json()['ResultSet']['Result'])

    # # One-off: write data frame to local csv, instead of repeatedly requesting from server
    # project_data_src_df.to_csv('src_sessions.csv')
    #
    # # And then read that data from CSV file back in for testing
    # project_data_src_df = pandas.read_csv('src_sessions.csv', skipinitialspace=True)

    # # and print the sets of data correspong to the types queried in from src project or read in from the dataset CSV file
    # print("Data queried from source project are:\n" + str(project_data_src_df[data_2_transfer.columns.values.tolist()]))

    # Now - repeat above steps, so we can also get a listing of data already in destination project
    connect.base_url = f'{xnat_url}/data/projects/{project_dest}/experiments?columns={search_terms}'
    # print ("********* Connecting base search URL is: " + str(connect.base_url))
    project_all_data_dest = connect.get(connect.base_url)

    project_data_dest_df = pandas.DataFrame(project_all_data_dest.json()['ResultSet']['Result'])

    # print("Data queried from destination project are:\n" + str(project_data_dest_df[data_2_transfer.columns.values.tolist()]))

    # So now we have (as data frames):
    #
    # - project_data_src_df  == data frame of data from source project
    #
    # - project_data_dest_df == data frame of data from destination  project
    #
    # - data_2_transfer      == list of data, read in from file, to be transferred from
    #                           source to destination projects

    # Code up till this point should generalizable and flexible enough for the majority of use
    # cases.  After this point, one should customize, based on CSV column labels.

    # Make sessions labels from source project lower case, and just take the MR accession ID, which
    # can sometimes be joined with '-' to session name modifiers, in case duplicates are found.
    project_data_src_df['label'] = project_data_src_df['label'].str.lower().str.split('-').str[0]

    # No need to create subjects in destination project if they don't already exist - the ReST API
    # move will create the subject. However, the subject will still be 'owned' by the originating /
    # source project, but the moved data set / experiment / session of MR data *** WILL *** belong
    # to the destination project.  This is b/c of XNAT's core data models.

    subjects_in_dest = project_data_dest_df['subject_label'].tolist()

    # Iterate over the sessions to be transferred
    for row_index, session in data_2_transfer.iterrows():

        # print("The label for this session of data is: " + str(session['label']))

        # Now, have to check for existence of session in source project.  Use either session label
        # (usually MR Accession ID), or DICOM session UID for search, and try to do partial string
        # matching

        for src_row_index, src_session in project_data_src_df.iterrows():
            if ((session['label'].lower() in src_session['label']) and
                (session['UID']           == src_session['UID'])   and
                (session['subject_label'] == src_session['subject_label'])):
                # print("Sessions to match: " + str(session) + " *** AND *** " + str(src_session))
                # print("Session to move from source to dest: " + str(project_data_src_df.iloc[src_row_index]))
                print("Matching sessions found with label: " + str(session['label']) + ", subject ID: " +
                      session['subject_label'] + ", and UID: " + session['UID'])

                # # Check if subject already exists in destination project = no longer needed / used!!!
                # if (session['subject_label'] in subjects_in_dest):
                    # print ("Subject %s already exists in %s project" % (str(session['subject_label']), project_dest))
                # # and if not - create:
                # else:
                    # print ("Subject %s not in %s project. Creating to move their data." % (str(session['subject_label']), project_dest))

                    # # Build ReST API string to create subject in destination project
                    # subject_query = build_create_subject_in_project_str(str(session['subject_label']), project_dest)
                    # # print(subject_query)

                    # # Now, connect to XNAT, and create the subject
                    # r = connect.put(f"{xnat_url}{subject_query}")
                    # # print("Subject creation status code: " + str(r.status_code))

                    # if r.status_code == 201:
                        # print("worked - created subject " + str(session['subject_label']) + " in project " + project_dest)
                        # # if subject successfully created in destination project, update list to reflect this
                        # subjects_in_dest.append(session['subject_label'])
                    # else :
                        # print("failed - check subject information for subject " + str(session['subject_label']))

                # Now, should be able to move session data from source to destination:
                session_id  = src_session['ID']
                queryexp    = move_exp_or_subj(session['subject_label'], project_src, project_dest, id_experiment=session_id, change_primary=True, label=None)

                r = connect.put(f"{xnat_url}{queryexp}")
                if r.status_code == 201:
                    print("worked - moved " + session['subject_label'] + " " + session_id + " project to" + project_dest)
                else :
                    print("failed - check subject information for" + session['subject_label'] + " " + session_id)
 
