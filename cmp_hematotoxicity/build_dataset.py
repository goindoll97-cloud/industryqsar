"""Build CMP organic candidate inventory.
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

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=ROOT/"data/private/cmp_hematotoxicity")
    a=p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    df=build_candidates(a.out)
    summary={"candidate_names":len(df),"identity_status":df.resolution_status.value_counts().to_dict()}
    (a.out/"build_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
