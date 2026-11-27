"""Audit Long et al. CSVs (SMILES,Y). Keep source labels, flag structure leakage.
Requires RDKit. No model training; source-negative is not verified occupational negative."""
import argparse,csv,json,hashlib
from collections import Counter,defaultdict
from pathlib import Path
from rdkit import Chem
def main():
 p=argparse.ArgumentParser();p.add_argument('--train',type=Path,required=True);p.add_argument('--test',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 rows=[];files={};groups=defaultdict(list)
 for split,path in [('train',a.train),('test',a.test)]:
  files[split]={'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  with path.open(encoding='utf-8-sig',newline='') as f:
   reader=csv.DictReader(f)
   if not {'SMILES','Y'}<=set(reader.fieldnames or []):raise ValueError('Expected SMILES and Y columns')
   for n,r in enumerate(reader,1):
    s=r['SMILES'].strip();y=r['Y'].strip();m=Chem.MolFromSmiles(s) if s else None
    z=dict(source_split=split,source_row=n,original_smiles=s,source_label=y,canonical_smiles='',structure_group='',status='eligible_source_label',note='')
    if m is None:z['status']='invalid_structure'
    elif len(Chem.GetMolFrags(m))!=1:z['status']='multicomponent_review'
    elif not any(at.GetAtomicNum()==6 for at in m.GetAtoms()):z['status']='noncarbon_review'
    elif y not in {'0','1'}:z['status']='invalid_label'
    else:
     z['canonical_smiles']=Chem.MolToSmiles(m,isomericSmiles=True)
     z['structure_group']=Chem.MolToSmiles(m,isomericSmiles=False)
     groups[z['structure_group']].append(z)
    rows.append(z)
 for g,records in groups.items():
  labels={r['source_label'] for r in records};splits={r['source_split'] for r in records}
  if len(labels)>1:
   for r in records:r['status']='conflicting_source_labels'
  elif len(splits)>1:
   for r in records:r['status']='cross_split_overlap_review'
  else:
   seen=set()
   for r in records:
    if r['canonical_smiles'] in seen:r['status']='exact_duplicate'
    seen.add(r['canonical_smiles'])
 with (a.out/'long_structure_audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 good=[r for r in rows if r['status']=='eligible_source_label']
 with (a.out/'long_source_label_candidates.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(good)
 summary={'sources':files,'input_rows':len(rows),'status_counts':dict(Counter(r['status'] for r in rows)),'eligible_source_labels':dict(Counter(r['source_label'] for r in good)),'eligible_unique_groups':len({r['structure_group'] for r in good}),'note':'No dose, duration, route or verified occupational negative is inferred. Salt/tautomer/metabolite equivalence needs further audit.'}
 (a.out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
