import os
import zipfile
import requests
import pandas as pd
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

username = os.environ['USERNAME']
password = os.environ['PASSWORD']

def download(s, uri, filename):
    with open(filename, 'wb') as f:
        r = s.get(uri, stream=True)
        r.raise_for_status()
        for block in r.iter_content(1024):
            if not block:
                break

            f.write(block)

    with zipfile.ZipFile(filename) as z:
        z.extractall()

    os.remove(filename)

s = requests.Session()
s.verify = False
host = 'https://cnda.wustl.edu'
s.auth = (username, password)

df = pd.read_csv('demo_data_with_anon_ids.csv')

root_dir = os.path.join(os.getcwd(), 'data')

print "Beginning directory creation and data download"

for index, subject, session, gk_session, gk_targ, roidir, lesion, new_subject, new_session, new_gk_session, new_lesion, session_uri, t1_hi_scans in df.itertuples():
    print '----------'
    print "subject {}\nsession {}\ngk_session {}\ngk_targ {}\nroidir {}\nlesion {}\nnew_subject {}\nnew_session {}\nnew_gk_session {}\nnew_lesion {} \nsession_uri {}\nt1_hi_scans {}".format(subject, session, gk_session, gk_targ, roidir, lesion, new_subject, new_session, new_gk_session, new_lesion, session_uri, t1_hi_scans)

    gk_session_to_download = gk_session if gk_session != 'preop' else session

    os.chdir(root_dir)
    subject_dir = os.path.join(root_dir, new_subject)
    if not os.path.exists(subject_dir):
        os.mkdir(subject_dir)
        print "Creating subject directory {}".format(new_subject)
    else:
        print "Subject directory {} already exists".format(new_subject)

    os.chdir(subject_dir)
    session_dir = os.path.join(subject_dir, new_session)
    if not os.path.exists(session_dir):
        os.mkdir(session_dir)
        print "Creating session directory {}".format(new_session)
    else:
        print "Session directory {} already exists".format(new_session)

    os.chdir(session_dir)

    # download lesions
    lesion_dir = os.path.join(session_dir, 'lesions')
    if not os.path.exists(lesion_dir):
        os.mkdir(lesion_dir)

        os.chdir(lesion_dir)
        roi_session = session if roidir[:-2] != 'GK' else gk_session_to_download
        print "Downloading all lesions from subject {}, session {}, resource {}".format(subject, roi_session, roidir)
        uri = host + '/data/projects/CONDR_METS/subjects/{}/experiments/{}/resources/{}/files?format=zip'.format(subject, roi_session, roidir)
        filename = 'lesions.zip'
        try:
            download(s, uri, filename)
        except:
            print "There was a problem. Skipping."
            with open(os.path.join(root_dir, 'problems.log'), 'a') as f:
                f.write("lesion - {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(subject, session, gk_session, gk_targ, roidir, lesion, new_subject, new_session, new_gk_session, new_lesion, session_uri, t1_hi_scans))
            continue
        print "Done downloading."

    else:
        print "Lesion directory already exists. Not downloading."

    # download scans
    scan_dir = os.path.join(session_dir, 'scan')
    if not os.path.exists(scan_dir):
        os.mkdir(scan_dir)

        os.chdir(scan_dir)

        scans_to_try = t1_hi_scans.split(',')
        gk_targ_str = '{}'.format(gk_targ)
        if gk_targ_str not in scans_to_try:
            scans_to_try += [gk_targ_str]
        scans_to_try.reverse()

        filename = 'scans.zip'
        allScansFailed = True
        for scan in scans_to_try:
            try:
                print "Downloading subject {}, session {}, scan {}".format(subject, gk_session_to_download, scan)
                uri = host + '/data/projects/CONDR_METS/subjects/{}/experiments/{}/scans/{}/resources/DICOM/files?format=zip'.format(subject, gk_session_to_download, scan)
                download(s, uri, filename)
                allScansFailed = False
                break
            except:
                print "There was a problem with scan {}.".format(scan)
        if allScansFailed:
            with open(os.path.join(root_dir, 'problems.log'), 'a') as f:
                f.write("scan - {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(subject, session, gk_session, gk_targ, roidir, lesion, new_subject, new_session, new_gk_session, new_lesion, session_uri, t1_hi_scans))

        print "Done downloading."


    else:
        print "Scan directory already exists. Not downloading."

    print "Done"

print "All done."