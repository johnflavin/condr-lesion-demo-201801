import os
import re
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
    if filename.endswith(".zip"):
        with zipfile.ZipFile(filename) as z:
            z.extractall()

        os.remove(filename)

s = requests.Session()
s.verify = False
host = 'https://cnda.wustl.edu'
s.auth = (username, password)

df = pd.read_csv('session_data.csv')

root_dir = os.path.join(os.getcwd(), 'data')

print "Beginning directory creation and data download"

# Write header to problem log
with open(os.path.join(root_dir, 'problems.log'), 'w') as f:
    f.write("type,subject,session,gk_session,gk_targ,roidir,new_subject,new_session,new_gk_session\n")

for index, subject,session,gk_session,gk_targ,roidir,new_subject,new_session,new_gk_session in df.itertuples():
    print '----------'
    print "subject {}\nsession {}\ngk_session {}\ngk_targ {}\nroidir {}\nnew_subject {}\nnew_session {}\nnew_gk_session {}\n".format(subject,session,gk_session,gk_targ,roidir,new_subject,new_session,new_gk_session)
    problem_template = "{}," +  "{},{},{},{},{},{},{},{}\n".format(subject,session,gk_session,gk_targ,roidir,new_subject,new_session,new_gk_session)

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
                f.write(problem_template.format("lesion"))
            continue
        print "Done downloading."

    else:
        print "Lesion directory already exists. Not downloading."

    # download scans
    scan_dir = os.path.join(session_dir, 'scan')
    if not os.path.exists(scan_dir):
        os.mkdir(scan_dir)

        os.chdir(scan_dir)

        try:
            print "Downloading metadata for subject {}, session {}, resource HOF_QC".format(subject, session)
            filename = "sfind_4dfp.txt"
            uri = host + '/data/projects/CONDR_METS/subjects/{}/experiments/{}/resources/HOF_QC/files/{}'.format(subject, session, filename)
            r = s.get(uri)
            sfind = r.text
            scan_ids = []
            scan_libids = []
            for line in sfind.split('\n'):
                if line.startswith('scan_id'):
                    scan_ids = line.lstrip('scan_id=(').rstrip(')').split()
                if line.startswith('scan_libid'):
                    scan_libids = line.lstrip('scan_libid=(').rstrip(')').split()

            if str(gk_targ) not in scan_ids:
                raise Exception("Could not find metadata for scan {} in HOF_QC sfind_4dfp.txt".format(gk_targ))

            hof_scan_type = scan_libids[scan_ids.index(str(gk_targ))]

            print "Downloading metadata for subject {}, session {}, resource HOF_reg".format(subject, session)
            uri = host + '/data/projects/CONDR_METS/subjects/{}/experiments/{}/resources/HOF_reg/files'.format(subject, session)

            r = s.get(uri, params={"format": "json"})
            r.raise_for_status()

            results = r.json().get("ResultSet", {}).get("Result", [])
            if len(results) == 0:
                raise Exception("Could not get ResultSet.Result from HOF_reg JSON.")
            gk_targ_4dfp_name_re = re.compile("^{}_{}_{}\.4dfp\.(hdr|ifh|img|img\.rec)$".format(session, gk_targ, hof_scan_type))
            gk_targ_4dfp_files = [result for result in results if gk_targ_4dfp_name_re.match(result.get("Name", ""))]

            if len(gk_targ_4dfp_files) == 0:
                raise Exception("Could not find any 4dfp files in HOF_reg JSON.")
            if len(gk_targ_4dfp_files) < 4:
                raise Exception("Could not find enough 4dfp files in HOF_reg JSON.")

            print "Downloading 4dfp files for subject {}, session {}, scan {}.".format(subject, session, gk_targ)
            for gk_targ_4dfp_file in gk_targ_4dfp_files:
                download(s, host + gk_targ_4dfp_file["URI"], gk_targ_4dfp_file["Name"])

            print "Done downloading "
        except:
            print "There was a problem. Skipping."
            with open(os.path.join(root_dir, 'problems.log'), 'a') as f:
                f.write(problem_template.format("HOF_reg"))


        print "Done downloading."


    else:
        print "Scan directory already exists. Not downloading."

    print "Done"

print "All done."