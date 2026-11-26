"""Build CMP screening inventory and an independent hematotoxicity benchmark.
Run from repository root: python cmp_hematotoxicity/build_dataset.py
Network required. Raw third-party data stay in ignored data/private.
"""
import argparse
import json
import time
from pathlib import Path
import pandas as pd
import requests
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "cmp_hematotoxicity/data/cmp_organic_evidence.csv"
HF = "maomlab/HematoxLong2023"

def resolve(name, session):
    from urllib.parse import quote
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/" + quote(name, safe="") + "/property/CanonicalSMILES,IsomericSMILES,InChIKey,MolecularWeight/JSON"
    for i in range(3):
        try:
            res = session.get(url, timeout=30)
            if res.status_code == 404:
                return {"resolution_status": "not_found"}
            res.raise_for_status()
            hits = res.json()["PropertyTable"]["Properties"]
            if len(hits) != 1:
                return {"resolution_status": "ambiguous", "candidate_cids": ";".join(str(x["CID"]) for x in hits)}
            p = hits[0]
            return {"resolution_status": "provisional_name_match", "cid": p["CID"], "raw_smiles": p.get("SMILES") or p.get("IsomericSMILES") or p.get("ConnectivitySMILES") or p.get("CanonicalSMILES"), "pubchem_inchikey": p.get("InChIKey"), "identity_source": url}
        except (requests.RequestException, KeyError, ValueError) as exc:
            time.sleep(2 ** i)
    return {"resolution_status": "request_failed"}

def structure(smiles):
    if not isinstance(smiles, str) or not smiles.strip():
        return {}
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return {}
    if len(Chem.GetMolFrags(m)) != 1 or not any(a.GetAtomicNum() == 6 for a in m.GetAtoms()):
        return {"structure_status": "out_of_scope"}
    return {"structure_status": "single_carbon_containing_structure", "canonical_smiles": Chem.MolToSmiles(m), "connectivity_key": Chem.MolToInchiKey(m).split("-")[0], "mw": Descriptors.MolWt(m), "logp": Crippen.MolLogP(m)}

def build_candidates(out):
    evidence = pd.read_csv(SOURCE)
    records = []
    with requests.Session() as session:
        for name, g in evidence.groupby("name", sort=True):
            p = resolve(name, session)
            records.append({"name": name, "source_count": len(g), "source_urls": ";".join(sorted(set(g.source_url))), "site_use_status": "not_verified", "hematotoxicity_status": "not_assessed", "identity_review": "required", **p, **structure(p.get("raw_smiles"))})
            time.sleep(0.25)
    df = pd.DataFrame(records)
    df.to_csv(out / "cmp_candidates.csv", index=False)
    evidence.merge(df, on=["name","site_use_status","hematotoxicity_status"], how="left").to_csv(out / "cmp_evidence_enriched.csv", index=False)
    return df

def build_benchmark(out, local_csv=None):
    if local_csv:
        raw = pd.read_csv(local_csv)
        if "split" not in raw:
            raw["split"] = "unspecified"
    else:
        from datasets import load_dataset
        data = load_dataset(HF, name="HematoxLong2023")
        raw = pd.concat([v.to_pandas().assign(split=k) for k,v in data.items()], ignore_index=True)
    if not {"SMILES", "Y"}.issubset(raw.columns):
        raise ValueError("Expected SMILES and Y; do not infer label semantics.")
    raw.to_csv(out / "hematox_raw.csv", index=False)
    parsed = pd.DataFrame([structure(s) for s in raw.SMILES], index=raw.index)
    df = pd.concat([raw, parsed], axis=1)
    df["Y"] = pd.to_numeric(df.Y, errors="coerce")
    valid = df[df.Y.isin([0,1]) & df.canonical_smiles.notna() & df.connectivity_key.notna()].copy()
    conflicts = valid.groupby("connectivity_key").Y.nunique()
    overlap = valid.groupby("connectivity_key").split.nunique()
    bad = set(conflicts[conflicts>1].index) | set(overlap[overlap>1].index)
    valid["group_conflict_or_split_overlap"] = valid.connectivity_key.isin(bad)
    df.to_csv(out / "hematox_structure_audit.csv", index=False)
    valid.to_csv(out / "hematox_split_conflict_audit.csv", index=False)
    clean = valid[~valid.group_conflict_or_split_overlap].drop_duplicates(["canonical_smiles","Y","split"]).copy()
    clean["endpoint"] = "published_general_hematotoxicity_binary"
    clean["route"] = "unknown"
    clean["source"] = HF
    clean.to_csv(out / "hematox_benchmark.csv", index=False)
    return {"raw_rows":len(raw),"valid_rows":len(valid),"quarantined_groups":len(bad),"clean_rows":len(clean),"counts":clean.groupby(["split","Y"]).size().rename("n").reset_index().to_dict("records")}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=ROOT/"data/private/cmp_hematotoxicity")
    p.add_argument("--local-hematox", type=Path)
    p.add_argument("--only", choices=["all","candidates","benchmark"], default="all")
    a=p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    summary={}
    if a.only in ("all","candidates"):
        df=build_candidates(a.out)
        summary["candidate_names"]=len(df)
        summary["identity_status"]=df.resolution_status.value_counts().to_dict()
    if a.only in ("all","benchmark"):
        summary["benchmark"]=build_benchmark(a.out,a.local_hematox)
    (a.out/"build_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
