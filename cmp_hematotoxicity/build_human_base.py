"""Recreate the human-label candidate inventory from original local files.
No animal data, no negative toxicity labels, no molecular identity inference.
"""
import argparse, hashlib, json
from pathlib import Path
import pandas as pd

TERMS = ["Leukopenia","Lymphopenia","Neutropenia","Agranulocytosis","Thrombocytopenia","Pancytopenia","Myelosuppression","Bone marrow failure","Aplastic anaemia","Haematotoxicity","Bone marrow depression"]
COLS = ["label","cid","stereo","cui","type","pt_cui","term"]
EXPECTED = {
"sider_meddra_all_label_se.tsv.gz":"4ae1cbe7f7edd7e572f31bbec5761d10f01d500851260ea8e39cddf60da52643",
"sider_drug_names.tsv":"6427a3e3202c71a81dff97092957aacf0700b9c01f34b07e452a1ec47c92b007",
"sider_drug_atc.tsv":"b457e124cc13c482bbe3afcf76c43bd53764c14d40da563785e20146c2e0f229",
"iris_simple_list_alpha.xlsx":"b23ac69359c515e69c23266eabd9ebeb4eec25f2c7b6cb89f5badd7c66844a6a"}
def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()
def joined(s):
    return "; ".join(sorted(set(s.dropna())))
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--raw",type=Path,required=True)
    a.add_argument("--out",type=Path,default=Path("data/private/cmp_hematotoxicity/human_base_v1"))
    args=a.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    hashes={n:sha(args.raw/n) for n in EXPECTED}
    if hashes!=EXPECTED:
        raise ValueError("Source snapshot differs from v1; preserve it under a new version.")
    names=pd.read_csv(args.raw/"sider_drug_names.tsv",sep="\t",names=["cid","name"],dtype=str)
    atc=pd.read_csv(args.raw/"sider_drug_atc.tsv",sep="\t",names=["cid","atc"],dtype=str)
    frames=[]; n=0
    for chunk in pd.read_csv(args.raw/"sider_meddra_all_label_se.tsv.gz",sep="\t",names=COLS,dtype=str,chunksize=250000):
        n+=len(chunk)
        frames.append(chunk[chunk.type.eq("PT") & chunk.term.str.casefold().isin({x.casefold() for x in TERMS})])
    ev=pd.concat(frames,ignore_index=True).drop_duplicates()
    agg=ev.groupby("cid").agg(terms=("term",joined),label_documents=("label","nunique"))
    inv=names.merge(agg,on="cid",how="left").merge(atc.groupby("cid").atc.agg(joined),on="cid",how="left")
    inv["evidence_status"]=inv.terms.notna().map({True:"reported_selected_PT",False:"unreported_selected_PT"})
    iris=pd.read_excel(args.raw/"iris_simple_list_alpha.xlsx")
    selected=iris[iris["Critical Effect Systems"].str.contains("hematolog",case=False,na=False)]
    ev.to_csv(args.out/"sider_selected_pt_evidence.csv",index=False)
    inv.to_csv(args.out/"sider_human_candidate_inventory.csv",index=False)
    selected.to_csv(args.out/"iris_hematologic_candidates.csv",index=False)
    summary={"version":"1.0","raw_sha256":hashes,"sider_raw_rows":n,"evidence_rows":len(ev),"inventory_rows":len(inv),"status_counts":inv.evidence_status.value_counts().to_dict(),"iris_rows":len(iris),"iris_selected":len(selected),"confirmed_negative_count":0}
    (args.out/"manifest.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":
    main()
