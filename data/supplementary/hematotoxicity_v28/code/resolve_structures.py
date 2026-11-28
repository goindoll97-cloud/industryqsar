"""
v0.28 — resolve chemical identity / structure for the NITE blood-system CAS set.

Uses PubChem PUG-REST by CAS registry number, then recomputes the InChIKey with
RDKit from the returned isomeric SMILES so that the registry key and the
recomputed key can be compared independently (protocol requirement:
"EPA 또는 PubChem 등록 InChIKey와 재계산 결과").

Structure status assigned per substance:
  ok_single_organic      one parsable organic component, keys agree
  key_mismatch           RDKit-recomputed InChIKey differs from PubChem's
  connectivity_only      first InChIKey block agrees, stereo/protonation differs
  multicomponent         SMILES contains more than one disconnected fragment
                         (salt / mixture) -> out of single-component scope
  inorganic_or_no_carbon no carbon atom -> outside organic structural domain
  unparsable             RDKit cannot parse the returned SMILES
  not_found              PubChem has no record for this CAS
  no_cas                 NITE row carries no usable CAS

Caching: every HTTP response is written to work/pubchem_cache/ so the run is
repeatable without re-querying, and the cache is part of the reproducibility
record.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

CACHE = "/home/user/v028/work/pubchem_cache"
BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
# PubChem PUG-REST property names. The service now returns "SMILES" and
# "ConnectivitySMILES"; the older "IsomericSMILES"/"CanonicalSMILES" names are
# still accepted in the request but the RESPONSE uses the current names, so
# every consumer below must read the current names first.
PROPS = "SMILES,ConnectivitySMILES,InChIKey,InChI,MolecularFormula,MolecularWeight,Title"
SMILES_FIELDS = ("SMILES", "IsomericSMILES", "ConnectivitySMILES", "CanonicalSMILES")
# PubChem asks automated clients to stay at or below 5 requests/second.
SLEEP = 0.22


def _get(url, cache_key):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, cache_key + ".json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    rec = {"url": url}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "hematotox-screening-research/0.28"})
        with urllib.request.urlopen(req, timeout=60) as r:
            rec["status"] = r.status
            rec["body"] = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        rec["status"] = e.code
        rec["body"] = e.read().decode("utf-8", "replace")[:2000]
    except Exception as e:                                  # network / timeout
        rec["status"] = -1
        rec["body"] = f"{type(e).__name__}: {e}"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f)
    time.sleep(SLEEP)
    return rec


def lookup_cas(cas):
    """Return (properties dict or None, raw status) for one CAS via PubChem."""
    safe = urllib.parse.quote(cas)
    key = "cas_" + re.sub(r'[^0-9A-Za-z-]', '_', cas)
    url = f"{BASE}/compound/name/{safe}/property/{PROPS}/JSON"
    rec = _get(url, key)
    if rec.get("status") != 200:
        return None, rec.get("status")
    try:
        props = json.loads(rec["body"])["PropertyTable"]["Properties"]
    except Exception:
        return None, "parse_error"
    return (props[0] if props else None), 200


def audit(cas, props):
    """Classify structure status and recompute the InChIKey with RDKit."""
    from rdkit import Chem
    from rdkit.Chem import inchi as rdinchi
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")

    out = {"pubchem_cid": "", "pubchem_title": "", "smiles": "", "pubchem_inchikey": "",
           "recomputed_inchikey": "", "formula": "", "mw": "", "n_fragments": "",
           "structure_status": "", "structure_note": ""}
    if props is None:
        out["structure_status"] = "not_found"
        return out
    out["pubchem_cid"] = props.get("CID", "")
    out["pubchem_title"] = props.get("Title", "")
    out["pubchem_inchikey"] = props.get("InChIKey", "") or ""
    out["formula"] = props.get("MolecularFormula", "")
    out["mw"] = props.get("MolecularWeight", "")
    smi = next((props[f] for f in SMILES_FIELDS if props.get(f)), "")
    out["smiles"] = smi
    if not smi:
        out["structure_status"] = "unparsable"
        out["structure_note"] = "no SMILES returned"
        return out

    m = Chem.MolFromSmiles(smi)
    if m is None:
        out["structure_status"] = "unparsable"
        out["structure_note"] = "RDKit could not parse the PubChem SMILES"
        return out

    frags = Chem.GetMolFrags(m, asMols=False)
    out["n_fragments"] = len(frags)
    try:
        out["recomputed_inchikey"] = rdinchi.MolToInchiKey(m) or ""
    except Exception as e:
        out["structure_note"] = f"InChIKey recomputation failed: {type(e).__name__}"

    has_c = any(a.GetSymbol() == "C" for a in m.GetAtoms())
    if not has_c:
        out["structure_status"] = "inorganic_or_no_carbon"
        return out
    if len(frags) > 1:
        out["structure_status"] = "multicomponent"
        out["structure_note"] = f"{len(frags)} disconnected fragments (salt/mixture)"
        return out

    pk, rk = out["pubchem_inchikey"], out["recomputed_inchikey"]
    if pk and rk and pk == rk:
        out["structure_status"] = "ok_single_organic"
    elif pk and rk and pk.split("-")[0] == rk.split("-")[0]:
        out["structure_status"] = "connectivity_only"
        out["structure_note"] = "first InChIKey block agrees; stereo/protonation layer differs"
    elif pk and rk:
        out["structure_status"] = "key_mismatch"
        out["structure_note"] = f"PubChem {pk} vs recomputed {rk}"
    else:
        out["structure_status"] = "ok_single_organic" if rk else "unparsable"
        out["structure_note"] = out["structure_note"] or "registry key unavailable for comparison"
    return out


def main():
    import pandas as pd
    roles = pd.read_csv("/home/user/v028/work/nite_substance_evidence_roles.csv", dtype=str).fillna("")
    rows = []
    cas_list = []
    for _, r in roles.iterrows():
        for c in [x.strip() for x in r.cas_all.split(";") if x.strip()]:
            cas_list.append((r.substance_id, r["name"], c))
    print("CAS to resolve:", len(cas_list))
    for i, (sid, name, cas) in enumerate(cas_list, 1):
        if not re.match(r'^\d{2,7}-\d{2}-\d$', cas):
            rows.append({"substance_id": sid, "nite_name": name, "cas": cas,
                         "structure_status": "no_cas", "structure_note": "CAS not in registry format"})
            continue
        props, status = lookup_cas(cas)
        a = audit(cas, props)
        if a["structure_status"] == "not_found":
            a["structure_note"] = f"PubChem lookup status {status}"
        rows.append({"substance_id": sid, "nite_name": name, "cas": cas, **a})
        if i % 50 == 0:
            print(f"  {i}/{len(cas_list)}", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv("/home/user/v028/work/nite_structure_audit_v028.csv", index=False)
    print("\n=== structure status ===")
    print(out.structure_status.value_counts().to_string())
    print("\nwrote nite_structure_audit_v028.csv")


if __name__ == "__main__":
    main()
