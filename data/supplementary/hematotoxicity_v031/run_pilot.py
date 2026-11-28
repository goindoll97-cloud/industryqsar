"""Positive-reference retrieval, not binary toxicity classification."""
import argparse, csv, hashlib, json, math, platform, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import sklearn
from sklearn.svm import OneClassSVM
from rdkit import Chem, rdBase
import generate_features as gf
import diagnostics as diag
import mechanism_bonus as mb

ROOT=Path(__file__).resolve().parent
MODELS=('max_tanimoto','ocsvm_morgan','ocsvm_ht','ocsvm_morgan_ht')

def read(p):
    with open(p,encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def write(p,rows):
    if not rows: raise ValueError(f'Empty output: {p}')
    with open(p,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tanimoto(x,y):
    x=x.astype(np.float64);y=y.astype(np.float64);dot=x@y.T
    den=x.sum(1)[:,None]+y.sum(1)[None,:]-dot
    return np.divide(dot,den,out=np.zeros_like(dot),where=den>0)
def structure_groups(s,threshold):
    n=len(s); seen=set(); groups=[]
    for i in range(n):
        if i in seen: continue
        stack=[i];seen.add(i);group=[]
        while stack:
            u=stack.pop();group.append(u)
            for v in np.flatnonzero(s[u]>=threshold):
                if v not in seen: seen.add(v);stack.append(int(v))
        groups.append(np.array(sorted(group),dtype=int))
    return groups

def scores(km,kh,train,query,nu,weight):
    result={'max_tanimoto':km[np.ix_(query,train)].max(1)}
    for name,k in zip(MODELS[1:],(km,kh,(1-weight)*km+weight*kh)):
        svm=OneClassSVM(kernel='precomputed',nu=nu,tol=1e-5)
        svm.fit(k[np.ix_(train,train)])
        if svm.fit_status_!=0: raise RuntimeError(f'{name} failed to converge')
        result[name]=svm.decision_function(k[np.ix_(query,train)]).ravel()
    if any(not np.isfinite(v).all() for v in result.values()):raise ValueError('Nonfinite score')
    return result

def rank_stats(values,i,pcts=(.05,.10)):
    # Quantize to 10 decimal places, then expected recovery under uniform tie-breaking.
    v=np.round(values,10); x=v[i]; lo=int(np.sum(v>x))+1;hi=int(np.sum(v>=x));n=len(v)
    out={'rank_best':lo,'rank_worst':hi,'rank_mid':(lo+hi)/2,'rank_fraction':(lo+hi)/(2*n),'pool_n':n,'tie_n':hi-lo+1}
    for p in pcts:
        k=max(1,math.ceil(p*n));tag=str(int(p*100));r=max(0,min(k-lo+1,hi-lo+1))/(hi-lo+1)
        out[f'k{tag}']=k;out[f'recall_credit_top{tag}']=r;out[f'ef_top{tag}']=r/(k/n)
    return out

def get_cas(r): return (r.get('CAS') or r.get('cas') or '').strip()
def audit(a,b,ae,bp,default):
    ar,br=read(a),read(b)
    if len(ar)<3 or not br:raise ValueError('Need >=3 references and >=1 candidate')
    if any(r.get('final_label','').strip() for r in br):raise ValueError('B must be unlabeled; remove adjudicated records first')
    for name,rows,p in [('A',ar,ae),('B',br,bp)]:
        evidence=read(p); known={get_cas(r) for r in evidence if (r.get('source_url') or r.get('URL') or r.get('url') or '').startswith(('https://','http://')) and (r.get('title') or '').strip()}
        missing={get_cas(r) for r in rows}-known
        if missing:raise ValueError(f'{name}: source title/URL missing for {sorted(missing)}')
    if default and (len(ar),len(br))!=(33,102):raise ValueError('Unexpected bundled dataset size')
    return ar,br

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--a',type=Path);p.add_argument('--b',type=Path);p.add_argument('--a-evidence',type=Path);p.add_argument('--b-provenance',type=Path)
    p.add_argument('--acknowledge-curated',action='store_true',help='External inputs were manually curated; not verified by this script')
    p.add_argument('--diagnostics',action='store_true',help='Compare resubstitution, compound-out and group-out using matched pools');
    p.add_argument('--mechanism-bonus',action='store_true',help='Compare fixed positive alert bonuses and alert-only control');
    p.add_argument('--out',type=Path);p.add_argument('--ht13',action='store_true',help='Exploratory sensitivity only')
    p.add_argument('--nu',type=float,default=.1);p.add_argument('--ht-weight',type=float,default=.5);p.add_argument('--group-threshold',type=float,default=.5)
    args=p.parse_args();custom=[args.a,args.b,args.a_evidence,args.b_provenance]
    if any(custom) and (not all(custom) or not args.acknowledge_curated):p.error('Provide all four external files and --acknowledge-curated')
    if not (0<args.nu<=1 and 0<=args.ht_weight<=1 and 0<args.group_threshold<=1):p.error('Invalid hyperparameters')
    default=not any(custom)
    a,b,ae,bp=custom if not default else [ROOT/x for x in ('Dataset_A_pilot_v031.csv','Dataset_B_pilot_v031.csv','A_evidence_v031.csv','B_provenance_legacy.csv')]
    ar,br=audit(a,b,ae,bp,default);n=len(ar);m=len(br)
    out=args.out or ROOT/'results'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
    gf.run(a,b,out/'features')
    z=np.load(out/'features'/'Morgan_HT_features.npz',allow_pickle=False);x=z['Morgan'];h=z['HT'];feature_ids=z['feature_ids'].tolist()
    assert x.shape==(n+m,2048) and h.shape==(n+m,10)
    if default:
        # Re-run structural unit tests and compare all existing HT values against committed tables.
        for r in read(ROOT/'Descriptor_Validation.csv'):
            assert gf.features(Chem.MolFromSmiles(r['SMILES']))[r['feature']]==int(r['expected']),r
        for role,block in [('A',h[:n]),('B',h[n:])]:
            expected=read(ROOT/f'Dataset_{role}_Features.csv');actual=read(out/'features'/f'Dataset_{role}_Features.csv')
            assert len(expected)==len(actual) and all(get_cas(e)==get_cas(t) and all(int(e[k])==int(t[k]) for k in feature_ids) for e,t in zip(expected,actual))
    if args.ht13:
        rules=read(ROOT/'Marrow_Descriptor_candidates.csv');qs=[Chem.MolFromSmarts(r['smarts']) for r in rules]
        if any(q is None for q in qs):raise ValueError('Invalid candidate SMARTS')
        lookup=dict(zip([r['feature_id'] for r in rules],qs))
        for r in read(ROOT/'Marrow_SMARTS_tests.csv'):
            assert int(Chem.MolFromSmiles(r['SMILES']).HasSubstructMatch(lookup[r['feature_id']]))==int(r['expected']),r
        ext=np.array([[int(Chem.MolFromSmiles(r.get('SMILES') or r.get('canonical_SMILES') or r.get('smiles')).HasSubstructMatch(q)) for q in qs] for r in ar+br],dtype=np.uint8)
        h=np.column_stack((h,ext));feature_ids+=list(lookup)
    np.savez_compressed(out/'model_features.npz',Morgan=x,HT=h,feature_ids=np.array(feature_ids),CAS=np.array([get_cas(r) for r in ar+br]))
    km=tanimoto(x,x[:n]);hf=h.astype(float);ht=hf[:n];dist=hf.sum(1)[:,None]+ht.sum(1)[None,:]-2*(hf@ht.T);kh=np.exp(-dist)
    groups=structure_groups(km[:n,:],args.group_threshold)
    if len(groups)<2 or max(map(len,groups))>n-2:raise ValueError('Insufficient independent structure groups')
    held_rows=[];members=[];bg=np.arange(n,n+m);all_a=np.arange(n)
    for g,hold in enumerate(groups,1):
        train=np.setdiff1d(all_a,hold);query=np.concatenate((hold,bg))
        assert np.max(km[np.ix_(hold,train)])<args.group_threshold
        for i in hold:members.append({'CAS':get_cas(ar[i]),'group':g,'group_size':len(hold)})
        for name,v in scores(km,kh,train,query,args.nu,args.ht_weight).items():
            for j,i in enumerate(hold):held_rows.append({'model':name,'group':g,'CAS':get_cas(ar[i]),'chemical':ar[i].get('chemical',''),'train_n':len(train),'score':float(v[j]),**rank_stats(v,j)})
    metrics=[]
    for name in MODELS:
        r=[v for v in held_rows if v['model']==name]
        metrics.append({'model':name,'held_reference_n':len(r),'group_n':len(groups),**{k:float(np.mean([v[k] for v in r])) for k in ('recall_credit_top5','recall_credit_top10','ef_top5','ef_top10','rank_fraction','tie_n')}})
    ranking=[]
    for name,v in scores(km,kh,all_a,bg,args.nu,args.ht_weight).items():
        for j in np.argsort(-v,kind='stable'):
            r=br[j];ranking.append({'model':name,'CAS':get_cas(r),'chemical':r.get('chemical',''),'process':r.get('process',''),'score':float(v[j]),'HT_hits':int(h[n+j].sum()),'HT_all_zero':int(not h[n+j].any()),**rank_stats(v,j)})
    for filename,rows in [('fold_membership.csv',members),('holdout_predictions.csv',held_rows),('retrieval_metrics.csv',metrics),('candidate_ranking.csv',ranking)]:write(out/filename,rows)
    manifest={'status':'exploratory_retrieval_not_validated_toxicity','input_scope':'bundled_v031_pilot' if default else 'user_curated_external_unverified','A':n,'B':m,'groups':len(groups),'largest_group':max(map(len,groups)),'features':feature_ids,'nu':args.nu,'ht_weight':args.ht_weight,'ht_kernel':'exp(-Hamming_count)','morgan_kernel':'Tanimoto','group_threshold':args.group_threshold,'group_method':'single-linkage Morgan Tanimoto connected components; leave-one-group-out','ranking':'ties rounded to 10 decimals; fractional expected top-k recovery, ceil(p*N); pool held group + unlabeled B','A_all_zero':int(np.sum(h[:n].sum(1)==0)),'B_all_zero':int(np.sum(h[n:].sum(1)==0)),'input_sha256':{str(q):sha(q) for q in (a,b,ae,bp)},'code_sha256':{'run_pilot':sha(__file__),'generate_features':sha(gf.__file__)},'versions':{'python':platform.python_version(),'rdkit':rdBase.rdkitVersion,'numpy':np.__version__,'sklearn':sklearn.__version__},'limitations':['No confirmed negatives, no accuracy/specificity/PPV or probability','B is unlabeled, never fitted','Published feature derivation overlap not ruled out; exploratory only','Do not select final model using this pilot as an independent test','A/B source coverage checked, not independent source verification']}
    if args.diagnostics:
        manifest['diagnostics']=diag.run_diagnostics(km,kh,h,ar,groups,args.nu,args.ht_weight,out,scores,rank_stats,write,get_cas,MODELS)
        manifest['code_sha256']['diagnostics']=sha(diag.__file__)
    if args.mechanism_bonus:
        manifest['mechanism_bonus']=mb.run_bonus(km,kh,h,ar,br,groups,args.nu,args.ht_weight,out,scores,rank_stats,write,get_cas,MODELS,feature_ids)
        manifest['code_sha256']['mechanism_bonus']=sha(mb.__file__)
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Completed: {out.resolve()} | A={n}, B={m}, groups={len(groups)}')
    for r in metrics:print(f"{r['model']:18s} R@5%={r['recall_credit_top5']:.4f} R@10%={r['recall_credit_top10']:.4f}")
if __name__=='__main__':main()
