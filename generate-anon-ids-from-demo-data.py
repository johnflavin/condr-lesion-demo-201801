subj_index = 1

def find_t1_his(session_uri):
    if session_uri in t1_his_map:
        return t1_his_map[session_uri]

    r = s.get(session_uri + '/resources/HOF_QC/files/sfind_4dfp.txt')
    if not r.ok:
        print "No HOF_QC for " + session_uri
        t1_his_map[session_uri] = ''
        return ''
    sfind = r.text
    scan_ids = []
    scan_cats = []
    scan_libids = []
    for line in sfind.split('\n'):
        if line.startswith('scan_id'):
            scan_ids = line.lstrip('scan_id=(').rstrip(')').split()
        if line.startswith('scan_cat'):
            scan_cats = line.lstrip('scan_cat=(').rstrip(')').split()
        if line.startswith('scan_libid'):
            scan_libids = line.lstrip('scan_libid=(').rstrip(')').split()
    t1_his = ','.join([scan_id for idx, scan_id in enumerate(scan_ids) if scan_cats[idx] == 't1_hi' and scan_libids[idx] == 'T1hi'])
    t1_his_map[session_uri] = t1_his
    return t1_his


subj_map = {}
sess_map = {}
lesion_map = {}
t1_his_map = {}
for subject in merge.subject:

    if subject not in subj_map:
        subj_map[subject] = 'S' + str(subj_index).zfill(3)
        subj_index += 1
    new_subject = subj_map[subject]

    sess_index = 1
    for session in merge[merge.subject == subject].session:
        if session not in sess_map:
            sess_map[session] = new_subject + '_E' + str(sess_index).zfill(2)
            sess_index += 1
        new_session = sess_map[session]

        lesion_index = 1
        for lesion in merge[merge.session == session].lesion:
            if lesion not in lesion_map:
                lesion_map[lesion] = new_session + '_L' + str(lesion_index).zfill(2)
                lesion_index += 1
            new_lesion = lesion_map[lesion]

    for gk_session in merge[merge.subject == subject].gk_session:
        if gk_session == 'preop':
            continue
        if gk_session not in sess_map:
            sess_map[gk_session] = new_subject + '_E' + str(sess_index).zfill(2)
            sess_index += 1

merge['new_subject'] = merge.apply(lambda row: subj_map[row['subject']], axis=1)
merge['new_session'] = merge.apply(lambda row: sess_map[row['session']], axis=1)
merge['new_gk_session'] = merge.apply(lambda row: sess_map[row['gk_session']] if row['gk_session'] != 'preop' else sess_map[row['session']], axis=1)
merge['new_lesion'] = merge.apply(lambda row: lesion_map[row['lesion']], axis=1)

session_url_template = 'https://cnda.wustl.edu/data/projects/CONDR_METS/subjects/{}/experiments/{}'
merge['session_uri'] = merge.apply(lambda row: session_url_template.format(row['subject'], row['session']), axis=1)
merge['t1_hi_scans'] = merge.apply(lambda row: find_t1_his(row['session_uri']), axis=1)


not_merged = pd.DataFrame(temp)
not_merged['new_subject'] = not_merged.apply(lambda row: subj_map.get(row['subject'], ''), axis=1)
not_merged['new_session'] = not_merged.apply(lambda row: sess_map.get(row['session'], ''), axis=1)
not_merged['new_gk_session'] = not_merged.apply(lambda row: sess_map.get(row['gk_session'], '') if row['gk_session'] != 'preop' else sess_map.get(row['session'], ''), axis=1)
not_merged = not_merged[not_merged.new_subject != '']
not_merged = not_merged[not_merged.new_session != '']
not_merged = not_merged[not_merged.new_gk_session != '']