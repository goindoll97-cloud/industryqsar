"""
v0.28 — merge the v0.27 local archive with the v0.28 full-text evidence reading.

Closes gaps G01, G02, G03 and supports G06/G07/G08.

Inputs (passed as arguments, never imported):
    1. the extracted v0.27 supplement directory
    2. the v0.28 tables directory

Outputs, written into the v0.28 tables directory:
    S05c_v27_evidence_review_reconciliation.csv
        all 417 structure-ready evidence rows, carrying the v0.27 review_depth
        and decision beside the v0.28 full-text species / route / endpoint
        reading. This is the direct answer to "what is in the 323 rows that
        v0.27 had not read".
    S04_Dataset_A_349_v028.csv
        the v0.27 Dataset A with the v0.28 evidence layer merged on CAS.
    S03c_structure_audit_cross_registry.csv
        the v0.27 EPA-based audit beside the v0.28 PubChem-based audit, per CAS.
"""

import os
import re
import sys
import pandas as pd

V27 = sys.argv[1]
TAB = sys.argv[2]
T27 = os.path.join(V27, "tables")

HC = {"Specific target organ toxicity - Single exposure": "STOT-SE",
      "Specific target organ toxicity - Repeated exposure": "STOT-RE"}

# The 323 rows v0.27 had not read in full: everything except the three
# full-summary review depths.
FULL_REVIEWED = {"NITE_summary_review_v25", "NITE_summary_review_v26", "NITE_full_summary_v27"}


def main():
    rev = pd.read_csv(f"{T27}/S05_NITE_evidence_review_417.csv", dtype=str).fillna("")
    rev["stot_class"] = rev.hazard_class.map(HC)
    rev["v27_full_summary_reviewed"] = rev.review_depth.isin(FULL_REVIEWED).astype(int)

    # v0.28 per-(CAS, STOT class) full-text reading, aggregated from the units.
    segs = pd.read_csv(f"{TAB}/S05_evidence_units_species_route.csv", dtype=str).fillna("")
    segs["stot_class"] = segs.stot_class
    ev = segs[segs.rationale_section != "rationale"].copy()
    exp = []
    for _, r in ev.iterrows():
        for c in [x.strip() for x in str(r.cas).split(";") if x.strip()]:
            exp.append({**r.to_dict(), "cas1": c})
    ev = pd.DataFrame(exp)

    def agg(g):
        endp = g[g.endpoint_types != ""]
        hum_inh = endp[(endp.evidence_species_basis == "human")
                       & (endp.exposure_route_basis == "inhalation")]
        ani_inh = endp[(endp.evidence_species_basis == "animal")
                       & (endp.exposure_route_basis == "inhalation")]
        types = sorted({t for s in endp.endpoint_types for t in s.split("; ") if t})
        return pd.Series({
            "v028_evidence_units": len(g),
            "v028_units_with_endpoint": len(endp),
            "v028_endpoint_types": "; ".join(types),
            "v028_species_observed": "; ".join(sorted(set(endp.evidence_species_basis)) or []),
            "v028_routes_observed": "; ".join(sorted(set(endp.exposure_route_basis)) or []),
            "v028_animal_species": "; ".join(sorted({s for v in endp.animal_species
                                                     for s in v.split("; ") if s})),
            "v028_human_inhalation_endpoint_unit": int(len(hum_inh) > 0),
            "v028_animal_inhalation_endpoint_unit": int(len(ani_inh) > 0),
            "v028_negation_in_endpoint_units": int((endp.negation_cues != "").sum()),
            "v028_compensatory_units": int((endp.compensatory_cues != "").sum()),
            "v028_has_noael_loael": int(endp.context_cues.str.contains(
                "has_noael_loael", regex=False).any()),
            "v028_has_quantified_exposure": int(endp.context_cues.str.contains(
                "has_concentration", regex=False).any()),
        })

    v28 = ev.groupby(["cas1", "stot_class"]).apply(agg, include_groups=False).reset_index()

    m = rev.merge(v28, left_on=["CAS", "stot_class"], right_on=["cas1", "stot_class"],
                  how="left").fillna("")
    m["v028_read_status"] = m.v028_evidence_units.apply(
        lambda v: "read_in_v028" if str(v) not in ("", "0") else "not_matched_in_v028")

    # What the v0.28 reading found in each row, in protocol terms.
    def finding(r):
        if r.v028_read_status != "read_in_v028":
            return "not_matched"
        if str(r.v028_units_with_endpoint) in ("", "0"):
            return "no_endpoint_term_in_rationale_text"
        if r.v028_human_inhalation_endpoint_unit == 1:
            return "human_inhalation_endpoint_in_one_unit"
        if r.v028_animal_inhalation_endpoint_unit == 1:
            return "animal_inhalation_endpoint_in_one_unit"
        if "human" in str(r.v028_species_observed):
            return "human_endpoint_route_not_isolated"
        if "animal" in str(r.v028_species_observed):
            return "animal_endpoint_other_or_unresolved_route"
        return "endpoint_without_resolved_species"

    m["v028_finding"] = m.apply(finding, axis=1)
    keep = ["evidence_id", "CAS", "chemical", "source_id", "classification_year", "hazard_class",
            "stot_class", "blood_category", "auto_review_bucket", "review_depth",
            "v27_full_summary_reviewed", "review_decision", "species_reviewed", "route_reviewed",
            "endpoint_reviewed", "observed_effect", "primary_study_verified",
            "final_inhalation_label", "v028_read_status", "v028_finding"] + list(v28.columns[2:])
    out = m[[c for c in keep if c in m.columns]]
    out.to_csv(f"{TAB}/S05c_v27_evidence_review_reconciliation.csv", index=False)
    print(f"  S05c_v27_evidence_review_reconciliation.csv  rows={len(out)}")

    pending = out[out.v27_full_summary_reviewed == 0]
    print(f"\n=== the {len(pending)} rows v0.27 had NOT read in full: what v0.28 found ===")
    print(pending.v028_finding.value_counts().to_string())
    print(f"\n  matched and read by v0.28: "
          f"{(pending.v028_read_status == 'read_in_v028').sum()} of {len(pending)}")
    print("\n=== by prior automatic bucket ===")
    print(pd.crosstab(pending.auto_review_bucket, pending.v028_finding).to_string())

    # ---------------- Dataset A merge (G01) ----------------
    a = pd.read_csv(f"{T27}/S04_Dataset_A_349.csv", dtype=str).fillna("")
    layer = pd.read_csv(f"{TAB}/S10_dataset_A_v028_join_layer.csv", dtype=str).fillna("")
    lex = []
    for _, r in layer.iterrows():
        for c in [x.strip() for x in str(r.cas).split(";") if x.strip()]:
            lex.append({**r.to_dict(), "cas1": c})
    L = pd.DataFrame(lex).drop_duplicates("cas1")
    cols = ["cas1", "dataset_A_role_v028", "evidence_tier", "all_tiers_present",
            "type1_hb_function", "type2_rbc_anemia", "type3_counts_marrow", "coagulation",
            "type3_assignment_after_compensatory_review", "nite_coagulation_only",
            "structure_status", "structural_scope", "smiles", "pubchem_inchikey",
            "recomputed_inchikey", "verification_state"]
    L = L[[c for c in cols if c in L.columns]].rename(columns={
        "smiles": "v028_pubchem_smiles", "pubchem_inchikey": "v028_pubchem_inchikey",
        "recomputed_inchikey": "v028_recomputed_inchikey",
        "structure_status": "v028_structure_status",
        "structural_scope": "v028_structural_scope",
        "verification_state": "v028_verification_state"})
    am = a.merge(L, left_on="CAS", right_on="cas1", how="left").drop(columns=["cas1"]).fillna("")
    am["v028_merge_status"] = am.dataset_A_role_v028.apply(
        lambda v: "matched_to_v028_official_set" if v else "no_v028_official_blood_system_entry")
    # Labelling discipline is preserved: the v0.27 final_label column is untouched.
    am.to_csv(f"{TAB}/S04_Dataset_A_349_v028.csv", index=False)
    print(f"\n  S04_Dataset_A_349_v028.csv  rows={len(am)} cols={len(am.columns)}")
    print("\n=== Dataset A 349: merge coverage ===")
    print(am.v028_merge_status.value_counts().to_string())
    print("\n=== Dataset A 349 x v0.28 role ===")
    print(am[am.dataset_A_role_v028 != ""].dataset_A_role_v028.value_counts().to_string())
    print("\n=== v0.27 final_label preserved ===")
    print(f"  non-empty final_label in merged Dataset A: "
          f"{(am.final_label.str.strip() != '').sum()}")

    # ---------------- structure audit cross-registry (G08) ----------------
    s3_27 = pd.read_csv(f"{T27}/S03_structure_audit_562.csv", dtype=str).fillna("")
    s3_28 = pd.read_csv(f"{TAB}/S03_structure_audit.csv", dtype=str).fillna("")
    x = s3_27.merge(s3_28[["cas", "structure_status", "structural_scope", "pubchem_inchikey",
                           "recomputed_inchikey", "smiles", "pubchem_cid"]],
                    left_on="CAS", right_on="cas", how="outer").fillna("")
    x["registry_agreement"] = x.apply(
        lambda r: "" if not (r.EPA_InChIKey and r.recomputed_inchikey)
        else ("exact_key_match" if r.EPA_InChIKey == r.recomputed_inchikey
              else "connectivity_match_only"
              if r.EPA_InChIKey.split("-")[0] == r.recomputed_inchikey.split("-")[0]
              else "key_conflict"), axis=1)
    x = x.rename(columns={"structure_status": "v028_structure_status",
                          "structural_scope": "v028_structural_scope",
                          "pubchem_inchikey": "v028_pubchem_inchikey",
                          "recomputed_inchikey": "v028_recomputed_inchikey",
                          "smiles": "v028_smiles", "pubchem_cid": "v028_pubchem_cid"})
    x.to_csv(f"{TAB}/S03c_structure_audit_cross_registry.csv", index=False)
    print(f"\n  S03c_structure_audit_cross_registry.csv  rows={len(x)}")
    print("\n=== EPA (v0.27) vs PubChem (v0.28) InChIKey agreement ===")
    print(x.registry_agreement.replace("", "not_comparable").value_counts().to_string())
    print("\n=== v0.27 scope_status x v0.28 structural_scope ===")
    print(pd.crosstab(x.scope_status.replace("", "<absent>"),
                      x.v028_structural_scope.replace("", "<absent>")).to_string())


if __name__ == "__main__":
    main()
