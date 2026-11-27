"""Integrity audit for provisional supplementary evidence; does not validate toxicity."""
import csv, hashlib, json
from pathlib import Path
from collections import Counter
root=Path(__file__).resolve().parent
meta=json.loads((root/'metadata.json').read_text(encoding='utf-8'))
def read(name):
    with (root/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))
def check(ok,message):
    if not ok:
        raise ValueError(message)
for entry in meta['files']:
    b=(root/entry['path']).read_bytes()
    sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()
    check(sha==entry['git_blob_sha1'],f"Hash mismatch: {entry['path']}")
    check(len(read(entry['path']))==entry['rows'],f"Row count mismatch: {entry['path']}")
e=read('human_inhalation_study_evidence.csv')
by={r['evidence_id']:r for r in e}
check(len(by)==49,'Duplicate evidence ID')
check(all(r['species']=='human' and r['route'] in ('inhalation','occupational_airborne') and not r['training_label'] for r in e),'Scope or label mismatch')
check(read('hematologic_cancer_evidence.csv')==[r for r in e if r['endpoint_class']=='cancer'],'Cancer subset mismatch')
check(Counter(r['effect'] for r in e if r['endpoint_class']=='hematology')==meta['counts']['hematology_effect'],'Effect counts mismatch')
loc=read('source_context_index.csv')
expected={i for r in e for i in r['record_ids'].split(';') if i}
check(len(loc)==len(expected) and {r['record_id'] for r in loc}==expected,'Locator coverage mismatch')
for r in loc:
    check(set(r['evidence_ids'].split(';'))=={x['evidence_id'] for x in e if r['record_id'] in x['record_ids'].split(';')},'Locator evidence mismatch')
    check(all(by[i]['source_url']==r['pdf_url'] for i in r['evidence_ids'].split(';')),'Locator URL mismatch')
ident={r['chemical_name']:(r['cas_rn'],r['smiles_input']) for r in read('chemical_identity.csv')}
check(len(ident)==21 and all(ident[r['chemical_name']]==(r['cas_rn'],r['smiles_input']) for r in e),'Identity mismatch')
summ=read('chemical_evidence_summary.csv')
for r in summ:
    ids=r['evidence_ids'].split(';')
    check(set(ids)=={x['evidence_id'] for x in e if x['chemical_name']==r['chemical_name']} and not r['training_label'],'Summary mismatch')
check(not read('training_labels_pending.csv'),'Unexpected training labels')
check(read('route_uncertain_excluded.csv')[0]['evidence_id'] not in by,'Excluded row leaked')
print('PASS: hashes, counts, scope, joins and blank labels. Scientific adjudication pending.')
