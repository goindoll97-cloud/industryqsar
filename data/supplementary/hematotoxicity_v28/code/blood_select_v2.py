import pandas as pd, re, sys
sys.path.insert(0, "/home/user/v028/code")
from parse_targets import parse_cell

BLOOD_CORE  = {"blood system", "blood", "hematopoietic system", "bone marrow", "hematopoietic organ"}
COAGULATION = {"blood coagulation system"}
LYMPHOID    = {"spleen", "lymph node", "lymphatic system", "reticuloendothelial system"}
VASCULAR    = {"blood vessels"}
MARROW      = {"bone marrow", "hematopoietic system", "hematopoietic organ"}

st = pd.read_csv("/home/user/v028/work/nite_stot_all_rows.csv", dtype=str).fillna("")
rows = []
for _, r in st.iterrows():
    b12 = [b for b in parse_cell(r.classification) if b["category"] in ("1", "2")]
    organs = {o.lower() for b in b12 for o in b["organs"]}
    core, coag = organs & BLOOD_CORE, organs & COAGULATION
    if not (core or coag): continue
    cats = sorted({b["category"] for b in b12
                   if {o.lower() for o in b["organs"]} & (BLOOD_CORE | COAGULATION)})
    for cas in [c.strip() for c in str(r.cas).split(",")] or [""]:
        rows.append({
            "cas": cas, "substance_id": r.substance_id, "cas_cell": r.cas, "name": r["name"],
            "hazard_class": "STOT-SE" if "Single" in r.hazard_class else "STOT-RE",
            "blood_categories": "+".join(cats),
            "blood_core_terms": "; ".join(sorted(core)),
            "coagulation_only": int(bool(coag) and not core),
            "marrow_or_hematopoietic": int(bool(organs & MARROW)),
            "lymphoid_terms": "; ".join(sorted(organs & LYMPHOID)),
            "vascular_terms": "; ".join(sorted(organs & VASCULAR)),
            "all_target_organs": "; ".join(sorted(organs)),
            "classification_raw": re.sub(r'\s+', ' ', r.classification).strip(),
            "year": r.year, "rationale": r.rationale})
b = pd.DataFrame(rows)
b = b[b.cas != ""]
pub = pd.read_csv("/home/user/industryqsar/data/supplementary/hematotoxicity_v24_nite/nite_blood_public_index.csv", dtype=str)
print("=== v0.28 rule: core blood OR coagulation, Cat1/2, multi-CAS cells split ===")
print("rows:", len(b), "| unique CAS:", b.cas.nunique())
print("published v0.24 index CAS:", pub.CAS.nunique())
pc, nc = set(pub.CAS), set(b.cas)
print("intersection:", len(pc & nc), "| only v0.24:", sorted(pc - nc), "| only v0.28:", sorted(nc - pc))
print("\ncoagulation-ONLY CAS (no blood/marrow/haematopoietic target):", b[b.coagulation_only == 1].cas.nunique())
for _, r in b[b.coagulation_only == 1].drop_duplicates("cas").iterrows():
    print(f"   {r.cas:14s} {r['name'][:62]}")
print("\ncore-blood CAS (excluding coagulation-only):", b[b.coagulation_only == 0].cas.nunique())
print("rows excluding coagulation-only:", (b.coagulation_only == 0).sum())
print("\nCAS whose STOT row also names a lymphoid organ:", b[b.lymphoid_terms != ""].cas.nunique())
b.to_csv("/home/user/v028/work/nite_blood_rows_v028.csv", index=False)
