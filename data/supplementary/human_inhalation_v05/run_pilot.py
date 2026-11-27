"""Fixed, exploratory LOO baselines. No hyperparameter tuning or external validation."""
import csv, json, pathlib, argparse
import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, recall_score, average_precision_score, roc_auc_score, confusion_matrix
from sklearn.model_selection import LeaveOneOut
p=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--dataset',type=pathlib.Path,default=p/'hematotoxicity_dataset.csv');parser.add_argument('--out',type=pathlib.Path,default=p/'pilot_results');args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
with args.dataset.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
g=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048);m=[Chem.MolFromSmiles(r['SMILES']) for r in rows];assert all(m);fps=[g.GetFingerprint(x) for x in m];X=np.array([g.GetFingerprintAsNumPy(x) for x in m]);y=np.array([int(r['Label']) for r in rows]);assert min(np.bincount(y))>=2;assert len({Chem.MolToSmiles(x) for x in m})==len(m)
models={'LR':lambda:LogisticRegression(C=1,class_weight='balanced',max_iter=2000,random_state=42),'RF':lambda:RandomForestClassifier(n_estimators=200,max_features='sqrt',class_weight='balanced',random_state=42,n_jobs=1)}
score={k:np.zeros(len(y)) for k in ['similarity',*models]};pred={k:np.zeros(len(y),dtype=int) for k in score};near=[]
for tr,te in LeaveOneOut().split(X):
 i=int(te[0]);sim=np.array([DataStructs.TanimotoSimilarity(fps[i],fps[j]) for j in tr]);pos=max(sim[y[tr]==1]);neg=max(sim[y[tr]==0]);score['similarity'][i]=(pos-neg+1)/2;pred['similarity'][i]=int(pos>neg);j=int(tr[np.argmax(sim)]);near.append({'Chemical':rows[i]['Chemical'],'nearest_train_chemical':rows[j]['Chemical'],'nearest_similarity':float(max(sim)),'max_positive_similarity':float(pos),'max_negative_similarity':float(neg)})
 for name,make in models.items():
  model=make();model.fit(X[tr],y[tr]);score[name][i]=model.predict_proba(X[te])[0,1];pred[name][i]=int(score[name][i]>=.5)
res=[]
for name,s in score.items():
 tn,fp,fn,tp=confusion_matrix(y,pred[name],labels=[0,1]).ravel();res.append(dict(model=name,n=len(y),positive=int(sum(y)),negative=int(sum(1-y)),balanced_accuracy=float(balanced_accuracy_score(y,pred[name])),recall=float(recall_score(y,pred[name])),FNR=float(fn/(fn+tp)),PR_AUC_AP=float(average_precision_score(y,s)),ROC_AUC=float(roc_auc_score(y,s)),TP=int(tp),FP=int(fp),TN=int(tn),FN=int(fn)))
def write(path,rr):
 with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]),lineterminator='\n');w.writeheader();w.writerows(rr)
write(args.out/'metrics.csv',res);write(args.out/'predictions.csv',[{**r,**{f'{k}_score':float(score[k][i]) for k in score},**{f'{k}_pred':int(pred[k][i]) for k in pred},**near[i]} for i,r in enumerate(rows)]);(args.out/'README.txt').write_text('Leave-one-molecule-out on pilot observation labels. No tuning. 0 labels are conditional. Scores are not probabilities of toxicity or cancer. Small selected sample and near-neighbor effects prevent valid claims of generalization. Similarity ties assigned 0. No external validation.\n');print(json.dumps(res,indent=2))
