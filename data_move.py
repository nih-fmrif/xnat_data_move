
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
import logging

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

# Set up logging, instead of using print statements.
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y_%m_%d %H:%M:%S', level=logging.WARNING)
xnat_logger = logging.getLogger(__name__)
 
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

xnat_logger.info("XNAT host: " + xnat_url + "; src project: " + project_src + "; dest project: " + project_dest)



# Now, read in list of datasets to be queried for, and manipulated
data_2_transfer = pandas.read_csv('datasets.csv', skipinitialspace=True)
search_terms    = ','.join(data_2_transfer.columns.values.tolist())  # store column headers so they can be used for queries
                                                                     # and matched up with queried searches from database.

# Convert subject ID to string, as in default case, their MRN shows up as an int,
# while an XNAT query returns the subject ID as a string, so make consistent with
# that.
if ('subject_label' in search_terms):
   data_2_transfer['subject_label'] = data_2_transfer['subject_label'].astype(str)

xnat_logger.debug("Keys queried: " + search_terms)



# Log into XNAT instance
user = getpass.getuser()
xnat_logger.debug("current user is {}".format(user))
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
    # file, or other specified file, read in above. XNAT's ID can be obtained from the experiment/session
    # URI, which can be split across '/', and the last field taken.
    connect.base_url = f'{xnat_url}/data/projects/{project_src}/experiments?columns={search_terms}'
    xnat_logger.debug("********* Connecting base search URL is: " + str(connect.base_url))
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

    # and print the sets of data correspong to the types queried in from src project or read in from the dataset CSV file
    xnat_logger.debug("Data queried from source project are:\n" + str(project_data_src_df[data_2_transfer.columns.values.tolist()]))

    # Now - repeat above steps, so we can also get a listing of data already in destination project
    connect.base_url = f'{xnat_url}/data/projects/{project_dest}/experiments?columns={search_terms}'
    xnat_logger.debug("********* Connecting base search URL is: " + str(connect.base_url))
    project_all_data_dest = connect.get(connect.base_url)

    project_data_dest_df = pandas.DataFrame(project_all_data_dest.json()['ResultSet']['Result'])

    xnat_logger.debug("Data queried from destination project are:\n" + str(project_data_dest_df[data_2_transfer.columns.values.tolist()]))

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

    # If 'date' is one of the search parameters we will be matching on, then convert the source and
    # destination project date formats to 'standard' Pandas datatime.
    if ('date' in search_terms):
        project_data_src_df['date'] = pandas.to_datetime(project_data_src_df['date'], format="%Y-%m-%d")
        data_2_transfer['date']     = pandas.to_datetime(data_2_transfer['date'],     format="%Y%m%d")

    # Instead of iterating over rows in data frame with 'for' loops, use Pandas' 'merge' functions and
    # multiple columns to find matching sessions of data between the list of data being queried versus
    # what's available in source data.

    common_sessions = pandas.merge(project_data_src_df, data_2_transfer,
                                   how='right',
                                   on=['UID', 'subject_label', 'date'])

    # Now, we can just iterate over the found common elements, and move each one, doing one final match
    # on the session/expt 'label' field (based on the MR Accession ID for that session of data). Groups
    # usually have the 'original' Accession ID, and that might get mangled by XNAT when those data were
    # ingested.  So try to do a partial text match, with 'in' vs '==', to allow for this variance.

    for row_index, session_2_move in common_sessions.iterrows():

        # Match on session IDs
        if (str(session_2_move['label_y']).lower() in str(session_2_move['label_x']).lower()):
            xnat_logger.info("Session label %s from data query also matches with session %s in source project. Moving from source to destination." %
                             (str(session_2_move['label_y']), str(session_2_move['label_x'])))

            # Get XNAT session ID, and use that to build string to move with ReST API call
            session_id  = str(session_2_move['URI'].split('/')[-1])
            queryexp    = move_exp_or_subj(session_2_move['subject_label'], project_src, project_dest,
                                           id_experiment=session_id, change_primary=True, label=None)

            xnat_logger.info("Executing ReST call on: " + f"{xnat_url}{queryexp}")

            # Now - actually move your data!
            r = connect.put(f"{xnat_url}{queryexp}")
            if r.status_code == 201:
                xnat_logger.info("worked - moved " + session_2_move['subject_label'] + " " + session_id + " project to" + project_dest)
            else :
                xnat_logger.debug("failed - check subject information for" + session_2_move['subject_label'] + " " + session_id)

        else:
            xnat_logger.debug("Sessions %s and %s have no common elements. Not moving any data." %
                              (str(session_2_move['label_y']), str(session_2_move['label_x'])))

