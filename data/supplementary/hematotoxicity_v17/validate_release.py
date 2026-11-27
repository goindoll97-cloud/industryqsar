"""Verify public v0.17 CSV snapshot; does not validate toxicology or chemical identity."""
import csv
import hashlib
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
EXPECTED = {
    'dataset_A_human_inhalation_references.csv': '144950533e9495c53f2d85d7498f4fdaec24b36f8b8ab774c0307d1de7bdb571',
    'dataset_B_semiconductor_249.csv': 'c7fec3e1ae17046a6a89e0da84c1d9d0cbd5ee6b677db2c64c1e25dae92a2abb',
}
def require(condition, message):
    if not condition:
        raise ValueError(message)

def read(name):
    p = ROOT / name
    require(hashlib.sha256(p.read_bytes()).hexdigest() == EXPECTED[name], f'SHA256 mismatch: {name}')
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

A, B = (read(name) for name in EXPECTED)
require(len(A) == len({r['CAS'] for r in A}) == len({r['reference_id'] for r in A}) == 27, 'A counts/duplicates')
require(len(B) == len({r['CAS'] for r in B}) == len({r['target_id'] for r in B}) == 249, 'B counts/duplicates')
require(Counter(r['Evidence_level'] for r in A) == {'1_core': 9, '2_extended': 6, '3_uncertain': 12}, 'A levels')
require(all(r['reference_use'] == ('sensitivity_only' if r['Evidence_level']=='3_uncertain' else 'provisional_primary_pool') for r in A), 'A analysis role')
require(Counter(r['structure_status'] for r in B) == {'provisional_organic_single_component':110,'outside_organic_single_component':84,'unresolved_structure':55}, 'B structure counts')
require(Counter(r['screening_role'] for r in B) == {'candidate_pending_toxicity_and_use_review':99,'reference_overlap_exclude_from_novel_ranking':11,'structure_or_scope_review':139}, 'B roles')
require(sum(r['CDR2024_match']=='yes' for r in B)==213, 'CDR matches')
require(sum(r['actual_inhalation_exposure']=='historical_personal_air_measurement_record' for r in B)==7, 'Historical air records')
require(sum(bool(r['process']) for r in B)==40, 'Reported processes')
require(sum(bool(r['identity_flags']) for r in B)==16, 'Identity flags')
require(not any(r['final_label'] for r in A+B) and not any(r['priority_score'] for r in B), 'Final labels/scores must be empty')
refs={r['reference_id']:r for r in A}
require(sum(bool(r['matched_reference_id']) for r in B)==11, 'Overlap count')
for r in B:
    if r['matched_reference_id']:
        a=refs[r['matched_reference_id']]
        require(a['CAS']==r['CAS'] or a['SMILES']==r['SMILES'], f"Overlap identity mismatch: {r['target_id']}")
print('PASS: public snapshot bytes, counts, roles and reference links; not independent toxicology/identity validation.')
