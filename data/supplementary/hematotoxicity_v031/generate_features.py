"""Literature-informed structural proxies; no toxicity labels. RDKit 2025.09.4."""
import argparse, csv, json
from pathlib import Path
from rdkit import Chem, rdBase
from rdkit.Chem import rdFingerprintGenerator
import numpy as np

IDS=[f'HT{i:02d}' for i in range(1,11)]
SMARTS={
 'aniline_anchor':'[c:1]-[N;X3;+0;!$(N-C=O);!$(N-S(=O)=O):2]',
 'nitro_anchor':'[c:1]-[N+](=O)[O-]',
 'egae_alcohol':'[C;X4;!R]-[O;X2]-[CH2]-[CH2]-[OH]',
 'egae_acetate':'[C;X4;!R]-[O;X2]-[CH2]-[CH2]-[O;X2]-[C;X3](=O)-[CH3]',
 'degae_alcohol':'[C;X4;!R]-[O;X2]-[CH2]-[CH2]-[O;X2]-[CH2]-[CH2]-[OH]',
 'phenol_anchor':'[c]-[OH]',
 'alkyl_anchor':'[c]-[C;X4;!R;!$(C-[!#6;!#1])]',
 'oxime':'[C;!a]=[N;!a]-[O;X2]',
 'hydrazine':'[N;X3;+0;!$(N-C=O);!$(N-S(=O)=O)]-[N;X3;+0;!$(N-C=O);!$(N-S(=O)=O)]',
 'alkyl_nitrite':'[C;X4]-[O;X2]-[N;X2]=[O]',
 'p_benzoquinone':'O=[C;R]1-[C;R]=[C;R]-[C;R](=O)-[C;R]=[C;R]-1',
}
Q={k:Chem.MolFromSmarts(v) for k,v in SMARTS.items()}
assert all(Q.values())
def alkyl_size(m, start, blocked):
    seen=set(); stack=[start]
    while stack:
        i=stack.pop()
        if i in seen: continue
        a=m.GetAtomWithIdx(i)
        if a.GetAtomicNum()!=6 or a.GetHybridization()!=Chem.HybridizationType.SP3 or a.IsInRing() or a.GetFormalCharge(): return None
        seen.add(i)
        for n in a.GetNeighbors():
            j=n.GetIdx()
            if j==blocked and i==start: continue
            if j not in seen: stack.append(j)
    return len(seen)
def ring_distance(r,i,j):
    d=abs(r.index(i)-r.index(j));return min(d,len(r)-d)
def features(m):
    h=dict.fromkeys(IDS,0)
    an={x[0] for x in m.GetSubstructMatches(Q['aniline_anchor'])}
    ni={x[0] for x in m.GetSubstructMatches(Q['nitro_anchor'])}
    ph={x[0] for x in m.GetSubstructMatches(Q['phenol_anchor'])}
    alk={x[0] for x in m.GetSubstructMatches(Q['alkyl_anchor'])}
    for r in m.GetRingInfo().AtomRings():
        if len(r)!=6 or not all(m.GetAtomWithIdx(i).GetIsAromatic() and m.GetAtomWithIdx(i).GetAtomicNum()==6 for i in r): continue
        a=len(set(r)&an);n=len(set(r)&ni)
        if a and not n:h['HT01']=1
        if n and not a:h['HT02']=1
        if a and n==1:h['HT03']=1
        if a and n>=2:h['HT04']=1
        oh=list(set(r)&ph)
        if set(r)&alk and any(ring_distance(r,i,j) in (1,3) for z,i in enumerate(oh) for j in oh[z+1:]):h['HT06']=1
    for key in ('egae_alcohol','egae_acetate','degae_alcohol'):
        if any(alkyl_size(m,x[0],x[1]) in (3,4) for x in m.GetSubstructMatches(Q[key])):h['HT05']=1
    for id,key in [('HT07','oxime'),('HT08','hydrazine'),('HT09','alkyl_nitrite'),('HT10','p_benzoquinone')]:h[id]=int(m.HasSubstructMatch(Q[key]))
    return h

def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(path,rows,cols=None):
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols or list(rows[0]));w.writeheader();w.writerows(rows)
def run(a,b,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=False)
    sets={}; fps=[]; vec=[]; keys=[]; ids=[]; audit=[]
    for role,src in [('A',a),('B',b)]:
        rows=read(src); new=[]; cas=set(); conn=set()
        for i,r in enumerate(rows):
            sm=r.get('SMILES') or r.get('canonical_SMILES') or r.get('smiles')
            c=r.get('CAS') or r.get('cas')
            if not c or c in cas:raise ValueError(f'{role} invalid/duplicate CAS {c}')
            m=Chem.MolFromSmiles(sm or '')
            if m is None or len(Chem.GetMolFrags(m))!=1 or not any(a.GetAtomicNum()==6 for a in m.GetAtoms()):raise ValueError(f'{role} invalid/out-of-scope structure {c}')
            ik=Chem.MolToInchiKey(m); key=ik.split('-')[0]
            if not ik:raise ValueError(f'{role} failed InChIKey {c}')
            expected=r.get('InChIKey') or r.get('computed_InChIKey')
            if expected and expected!=ik:raise ValueError(f'{role} registry/computed key mismatch {c}; review before use')
            if key in conn:raise ValueError(f'{role} duplicate connectivity {c}; group or deduplicate before use')
            cas.add(c);conn.add(key)
            f=features(m);n=sum(f[k] for k in IDS[:8]);total=sum(f.values())
            if any(k in r for k in IDS):raise ValueError('Refusing to overwrite existing HT columns')
            new.append({**r,**f,'HT_core_hits':n,'HT_total_hits':total,'HT_all_zero':int(total==0)})
            fps.append(gen.GetFingerprintAsNumPy(m));vec.append(list(f.values()));keys.append(key);ids.append(r.get('chemical_id') or c)
        sets[role]=(new,cas,conn)
    if sets['A'][1]&sets['B'][1] or sets['A'][2]&sets['B'][2]:raise ValueError('A/B overlap; separate references before screening')
    for role,(rows,_,__) in sets.items():
        write(out/f'Dataset_{role}_Features.csv',rows)
        for k in IDS+['HT_all_zero']:
            count=sum(int(r[k]) for r in rows);audit.append({'dataset':role,'feature':k,'n':len(rows),'hits':count,'fraction':round(count/len(rows),6)})
    write(out/'feature_coverage.csv',audit)
    np.savez_compressed(out/'Morgan_HT_features.npz',Morgan=np.array(fps,dtype=np.uint8),HT=np.array(vec,dtype=np.uint8),feature_ids=np.array(IDS),chemical_ids=np.array(ids),connectivity_keys=np.array(keys),dataset=np.array(['A']*len(sets['A'][0])+['B']*len(sets['B'][0])))
    (out/'feature_manifest.json').write_text(json.dumps({'rdkit':rdBase.rdkitVersion,'A':len(sets['A'][0]),'B':len(sets['B'][0]),'HT_features':IDS,'core':IDS[:8],'supplemental':IDS[8:],'status':'exploratory structural proxies, not validated toxicity rules','label_policy':'input preserved, no new labels'},indent=2),encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--a',required=True);p.add_argument('--b',required=True);p.add_argument('--out',required=True);args=p.parse_args();run(args.a,args.b,args.out)
