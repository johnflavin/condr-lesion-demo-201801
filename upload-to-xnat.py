import os
import re
import zipfile
import requests
import pandas as pd
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

def download(s, uri, filename):
    with open(filename, 'wb') as f:
        r = s.get(uri, stream=True)
        r.raise_for_status()
        for block in r.iter_content(1024):
            if not block:
                break

            f.write(block)
    if filename.endswith(".zip"):
        with zipfile.ZipFile(filename) as z:
            z.extractall()

        os.remove(filename)

print "Beginning upload to clean XNAT"

s = requests.Session()
s.verify = False
host = 'http://xnat-31.xnat.org'
uri_base = host + '/data/projects/foo'

username = os.environ['USERNAME']
password = os.environ['PASSWORD']
s.auth = (username, password)

print "Attempting to connect to {}".format(host)
r = s.get(host + '/data/JSESSION')
r.raise_for_status()

df = pd.read_csv('session_data.csv')

created = {"subjects": set(), "sessions": set()}

root_dir = os.path.join(os.getcwd(), 'data')
lesion_zip_file_name = "lesions.zip"

# Write header to problem log
for index, subject,session,gk_session,gk_targ,roidir,new_subject,new_session,new_gk_session in df.itertuples():
    print '----------'
    print "subject {}\nsession {}\ngk_session {}\ngk_targ {}\nroidir {}\nnew_subject {}\nnew_session {}\nnew_gk_session {}\n".format(subject,session,gk_session,gk_targ,roidir,new_subject,new_session,new_gk_session)

    if str(new_session) in created["sessions"]:
        print "Already created session {}. Skipping.".format(new_session)
        continue

    os.chdir(root_dir)
    subject_dir = os.path.join(root_dir, new_subject)
    if not os.path.exists(subject_dir):
        print "Subject directory {} does not exist. Skipping.".format(new_subject)
        continue

    os.chdir(subject_dir)
    session_dir = os.path.join(subject_dir, new_session)
    if not os.path.exists(session_dir):
        print "Session directory {} does not exist. Skipping.".format(new_session)
        continue

    os.chdir(session_dir)

    # download lesions
    lesion_dir = os.path.join(session_dir, 'lesions')
    scan_dir = os.path.join(session_dir, 'scan')
    if not os.path.exists(lesion_dir) or not os.path.exists(scan_dir):
        print "{} directory does not exist. Skipping.".format("Lesion" if not os.path.exists(lesion_dir) else "Scan")
        continue

    try:
        lesion_files = os.listdir(lesion_dir)
    except:
        lesion_files = []

    if len(lesion_files) == 0:
        print "No lesion files in lesion directory. Skipping."
        continue

    try:
        scan_files = os.listdir(scan_dir)
    except:
        scan_files = []

    if len(scan_files) == 0:
        print "No lesion files in lesion directory. Skipping."
        continue
    if len(scan_files) > 1:
        print "Found more than one scan file. Expected one. Skipping."
        continue
    scan_file = scan_files[0]

    os.chdir(lesion_dir)
    print "Writing lesion files to zip."
    try:
        with zipfile.ZipFile(lesion_zip_file_name, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for lesion_file in lesion_files:
                z.write(lesion_file)
    except:
        print "There was a problem writing lesion zip. Skipping."
        continue


    # if subject does not exist, make subject
    if str(new_subject) not in created["subjects"]:
        print "Creating subject {}.".format(new_subject)
        r = s.put(uri_base + '/subjects/{}'.format(new_subject))
        if not r.ok:
            print "Failed to create subject {}. Skipping.".format(new_subject)
            continue
        print "Success."
        created["subjects"].add(str(new_subject))

    print "Creating session {}.".format(new_session)
    r = s.put(uri_base + '/subjects/{}/experiments/{}'.format(new_subject, new_session), params={"xsiType":"xnat:mrSessionData"})
    if not r.ok:
        print "Failed to create session {}. Skipping.".format(new_session)
        continue
    print "Success."
    created["sessions"].add(str(new_session))

    print "Creating session resource for lesion files."
    r = s.put(uri_base + '/subjects/{}/experiments/{}/resources/LESION_MASKS'.format(new_subject, new_session))
    if not r.ok:
        print "Failed to create LESION_MASKS session resource. Skipping."
        continue
    print "Success."

    os.chdir(lesion_dir)
    print "Uploading lesion mask files to session resource."
    r = s.put(uri_base + '/subjects/{}/experiments/{}/resources/LESION_MASKS/files'.format(new_subject, new_session), params={"format": "NIFTI", "extract": True}, files={'file': open(lesion_zip_file_name, 'rb')})
    if not r.ok:
        print "Failed to upload lesion mask files to session resource. Skipping."
        continue
    print "Success."

    print "Creating scan {}.".format(gk_targ)
    r = s.put(uri_base + '/subjects/{}/experiments/{}/scans/{}'.format(new_subject, new_session, gk_targ), params={"xsiType":"xnat:mrScanData"})
    if not r.ok:
        print "Failed to create scan {}. Skipping.".format(gk_targ)
        continue
    print "Success."

    print "Creating scan {} NIFTI resource.".format(gk_targ)
    r = s.put(uri_base + '/subjects/{}/experiments/{}/scans/{}/resources/NIFTI'.format(new_subject, new_session, gk_targ))
    if not r.ok:
        print "Failed to create scan {} NIFTI resource. Skipping.".format(gk_targ)
        continue
    print "Success."

    os.chdir(scan_dir)
    print "Uploading scan file to scan resource."
    r = s.put(uri_base + '/subjects/{}/experiments/{}/scans/{}/resources/NIFTI/files/{}'.format(new_subject, new_session, gk_targ, scan_file), params={"format": "NIFTI"}, files={'file': open(scan_file, 'rb')})
    if not r.ok:
        print "Failed to upload scan file to scan resource. Skipping."
        continue
    print "Success."
    print "Done"

print "All done."