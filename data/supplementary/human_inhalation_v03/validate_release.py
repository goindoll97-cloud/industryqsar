"""Verify release structure and review bookkeeping; not scientific adjudication."""
import csv, hashlib, json
from collections import Counter
from pathlib import Path
p=Path(__file__).resolve().parent
m=json.loads((p/'metadata.json').read_text(encoding='utf-8'))
def read(n):
    with (p/n).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def check(ok,msg):
    if not ok:raise ValueError(msg)
for n,v in m['published_files'].items():
    b=(p/n).read_bytes();check(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()==v['git_blob_sha1'],n+' hash mismatch');check(len(read(n))==v['rows'],n+' row count mismatch')
e=read('integrated_evidence.csv');g=read('citation_review_groups.csv');c=read('chemical_inventory.csv');l=read('evidence_overlap_links.csv');v=read('official_v10_evidence.csv')
by={r['evidence_id']:r for r in e};check(len(by)==len(e)==114,'evidence IDs');check({r['evidence_id'] for r in v}=={r['evidence_id'] for r in e if r['source_version']=='official_v10'},'V10 coverage');check(len(c)==len({r['cas_rn'] for r in e})==44,'CAS coverage')
check(Counter(r['review_bucket'] for r in e)==m['review_bucket_rows'],'row buckets');check(Counter(r['review_bucket'] for r in g)==m['review_bucket_groups'],'group buckets')
ids=[]
for r in g:
    group=r['evidence_ids'].split(';');ids+=group;check(len(group)==int(r['source_rows']) and all(by[i]['citation_review_group']==r['citation_review_group'] and by[i]['cas_rn']==r['cas_rn'] for i in group),'group linkage')
check(Counter(ids)==Counter(by.keys()),'group coverage');check(all(by[r['evidence_id_a']]['cas_rn']==by[r['evidence_id_b']]['cas_rn'] for r in l),'overlap CAS')
check(all(not r['training_label'] for r in e+g+c) and not read('training_labels_pending.csv'),'unexpected training label');check(by['H018']['review_bucket']=='excluded' and by['E08']['review_bucket']=='excluded','scope leakage');check(all(r['review_bucket']=='cancer_separate' for r in e if r['endpoint_class']=='cancer'),'cancer leakage')
print('PASS: hashes, row counts, scope buckets, group coverage and blank labels. Scientific adjudication pending.')
