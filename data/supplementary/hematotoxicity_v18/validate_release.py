"""Validate v0.18 public projection bytes and key counts, not independent chemical identity/toxicity."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
root = Path(__file__).resolve().parent
s = json.loads((root / 'summary.json').read_text(encoding='utf-8'))
def load(name, key):
    p = root / name
    if hashlib.sha256(p.read_bytes()).hexdigest() != s[key]:
        raise ValueError(f'Hash mismatch: {name}')
    with p.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))
a=load('dataset_A_human_inhalation_references.csv','sha256_public_A')
b=load('dataset_B_semiconductor_249.csv','sha256_public_B')
assert len(a)==len(set(r['CAS'] for r in a))==28
assert len(b)==len(set(r['CAS'] for r in b))==249
assert Counter(r['Evidence_level'] for r in a)==s['reference_levels']
assert Counter(r['structure_status'] for r in b)==s['structure_status']
assert Counter(r['screening_role'] for r in b)==s['roles']
assert not any(r['final_label'] for r in a+b)
assert not any(r['priority_score'] for r in b)
ids={r['reference_id'] for r in a}
assert all(not r['matched_reference_id'] or r['matched_reference_id'] in ids for r in b)
print('PASS: public projection integrity; independent evidence and identity validation not implied.')
