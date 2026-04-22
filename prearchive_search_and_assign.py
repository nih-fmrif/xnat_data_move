
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

   prearchive_sessions = session.prearchive.sessions()

   for idx,expt in enumerate(prearchive_sessions):
      try:
         # print("session: %s, first scan: %s" % (str(expt), list(expt.scans.values())[0]))
         first_scan = list(expt.scans.values())[0]
         session_id = first_scan.dicom_dump(fields=['AccessionNumber'])[0]['value']
         if (str(session_id) != ''):
            print("session id: %s" % str(session_id))
      except xnat.exceptions.XNATResponseError:
         pass

   session.close()

