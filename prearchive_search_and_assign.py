
"""
   Utility to search the PreArchive queue of your XNAT instance, to allow an
   administrator to assign sessions to a project.  Based on code provided by
   GitHub user cathat00.

"""



import    xnat
import   numpy as np
import  pandas as pd



with xnat.connect('https://fmrif-xnat.nimh.nih.gov', user='xnat_admin_user') as session:
# enter password for admin user when prompted.

   # Without the project='Unassigned' arguement to this function, this would normally
   # return all sessions in PreArchive, i.e. including those already assigned to a 
   # project.
   prearchive_sessions_unassigned = session.prearchive.sessions(project='Unassigned')

   # read in CSV with session IDs
   session_ids = pd.read_csv('Path_to_CSV_of_needed_session_IDs.csv', skipinitialspace=True)

   found_session_counter = 0

   for each_session in prearchive_sessions_unassigned:

      try:
         first_scan     = list(each_session.scans.values())[0]
         dcm_session_id = first_scan.dicom_dump(fields=['AccessionNumber'])[0]['value']

         # Now iterate through list of sessions IDs to do 'soft matching'
         for each_id in session_ids['label']:

            if ((each_id in (str(each_session))) and (each_id == dcm_session_id)):
               print("*** Found %s in %s !!! ***" % (str(each_id), str(each_session)))
               # can execute project assignment here, with something like:
               # each_session.move('ID of destination project here')
               found_session_counter += 1
            else:
               # print("%s not found in %s" % (each_id, str(each_session)))
               pass
      except xnat.exceptions.XNATResponseError:
         pass

   print ("Number of sessions found and assigned to project is %d" % found_session_counter)

   session.disconnect()

