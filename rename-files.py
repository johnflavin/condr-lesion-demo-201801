import os
import pandas as pd


df = pd.read_csv('demo_data_with_anon_ids.csv')

data_dir = os.path.join(os.getcwd(), "data")

for index, subject, session, gk_session, gk_targ, roidir, lesion, new_subject, new_session, new_gk_session, new_lesion, session_uri, t1_hi_scans in df.itertuples():
    print "---------"
    print "subject {}\nsession {}\ngk_session {}\ngk_targ {}\nroidir {}\nlesion {}\nnew_subject {}\nnew_session {}\nnew_gk_session {}\nnew_lesion {}\nsession_uri {}\nt1_hi_scans {}".format(subject, session, gk_session, gk_targ, roidir, lesion, new_subject, new_session, new_gk_session, new_lesion, session_uri, t1_hi_scans)

    subject_dir = os.path.join(data_dir, new_subject)
    if not os.path.exists(subject_dir):
        print "Subject dir does not exist. Skipping."
        continue

    session_dir = os.path.join(subject_dir, new_session)
    if not os.path.exists(session_dir):
        print "Session dir does not exist. Skipping."
        continue

    # rename scan
    scan_dir = os.path.join(session_dir, "scan")
    try:
        scan_files = os.listdir(scan_dir)
    except:
        print "Could not list scan files in directory {}. Skipping.".format(scan_dir)
        continue

    if len(scan_files) != 1:
        print "Expected one scan file but got multiple. Skipping."
        continue
    scan_file = scan_files[0]
    new_scan_file = scan_file.replace(session, new_session)

    print "Renaming scan {} to {}.".format(os.path.join(scan_dir, scan_file), os.path.join(scan_dir, new_scan_file))
    try:
        os.rename(os.path.join(scan_dir, scan_file), os.path.join(scan_dir, new_scan_file))
    except:
        print "A problem happened. Skipping."
        continue

    # move and rename lesion masks
    lesion_dir = os.path.join(session_dir, "lesions")
    lesion_resource_dir = os.path.join(lesion_dir, session, "resources", roidir, "files")
    lesion_file = "{}.nii".format(lesion)
    new_lesion_file = "{}.nii".format(new_lesion)

    print "Moving lesion mask {} to {}.".format(os.path.join(lesion_resource_dir, lesion_file), os.path.join(lesion_dir, new_lesion_file))
    try:
        os.rename(os.path.join(lesion_resource_dir, lesion_file), os.path.join(lesion_dir, new_lesion_file))
    except:
        print "A problem happened. Skipping."
        continue


    print "Done"

print "All Done"
