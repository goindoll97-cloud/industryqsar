import pandas as pd, sys
sys.path.insert(0,"/home/user/v028/code")
from evidence_extract import segment_rationale, classify_segment

b = pd.read_csv("/home/user/v028/work/nite_blood_rows_v028.csv", dtype=str).fillna("")
u = b.drop_duplicates(["substance_id","hazard_class"]).copy()
cas_map = b.groupby("substance_id").cas.apply(lambda s: "; ".join(sorted(set(s)))).to_dict()
out=[]
for _,r in u.iterrows():
    for seg in segment_rationale(r.rationale):
        f = classify_segment(seg["text"])
        out.append({"substance_id": r.substance_id, "cas_all": cas_map.get(r.substance_id,""),
                    "name": r["name"], "hazard_class": r.hazard_class,
                    "blood_categories": r.blood_categories,
                    "blood_core_terms": r.blood_core_terms,
                    "coagulation_only": r.coagulation_only,
                    "marrow_or_hematopoietic": r.marrow_or_hematopoietic,
                    "year": r.year, "section": seg["section"], "unit_id": seg["unit_id"],
                    **f, "segment_text": seg["text"],
                    "review_state": "extracted_pending_expert_confirmation"})
d = pd.DataFrame(out)
d.to_csv("/home/user/v028/work/nite_evidence_segments.csv", index=False)
print("rationale units (substance x SE/RE):", len(u))
print("segments extracted:", len(d))
print("  by section:\n"+d.section.value_counts().to_string())
print("\nsegments with an endpoint term:", (d.endpoint_types!="").sum())
print("segments with species+route+endpoint co-occurrence:", int(d.cooccurrence.sum()))
print("\nspecies_basis:\n"+d.species_basis.value_counts().to_string())
print("\nroute_basis:\n"+d.route_basis.value_counts().to_string())
