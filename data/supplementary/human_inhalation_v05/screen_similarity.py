"""Positive-reference retrieval only: no calibrated hazard probability or validated cutoff."""
import argparse,csv,pathlib
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
p=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--input',type=pathlib.Path,required=True,help='CSV with Chemical and SMILES columns');ap.add_argument('--reference',type=pathlib.Path,default=p/'hematotoxicity_dataset.csv');ap.add_argument('--out',type=pathlib.Path,default=p/'similarity_screen.csv');a=ap.parse_args()
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
g=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)
refs=[]
for r in read(a.reference):
 if r['Label']!='1':continue
 m=Chem.MolFromSmiles(r['SMILES']);assert m is not None;refs.append((r,g.GetFingerprint(m),Chem.MolToSmiles(m)))
assert refs,'No positive references'
a.out.parent.mkdir(parents=True,exist_ok=True)
fields=['Chemical','SMILES','status','nearest_positive_similarity','rank','reference_chemical','reference_CAS_RN','Tanimoto','reference_endpoint','reference_source']
with a.out.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for r in read(a.input):
  row={k:r[k] for k in ['Chemical','SMILES']};m=Chem.MolFromSmiles(r['SMILES'])
  if m is None or len(Chem.GetMolFrags(m))!=1 or not any(atom.GetAtomicNum()==6 for atom in m.GetAtoms()):w.writerow({**row,'status':'invalid_or_outside_organic_structure_scope'});continue
  fp=g.GetFingerprint(m);canonical=Chem.MolToSmiles(m);matches=sorted([(DataStructs.TanimotoSimilarity(fp,x),ref) for ref,x,s in refs if s!=canonical],key=lambda x:-x[0]);status='known_positive_excluded_self; unvalidated_AD' if any(s==canonical for _,_,s in refs) else 'unvalidated_AD'
  if not matches:w.writerow({**row,'status':status});continue
  for i,(score,ref) in enumerate(matches[:5],1):w.writerow({**row,'status':status,'nearest_positive_similarity':round(matches[0][0],6),'rank':i,'reference_chemical':ref['Chemical'],'reference_CAS_RN':ref['CAS_RN'],'Tanimoto':round(score,6),'reference_endpoint':ref['Endpoint'],'reference_source':ref['Reference']})
print(a.out)
