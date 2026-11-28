"""
v0.28 / G14 — apply the released structure holds and recompute the reference sets.

EPA CompTox is the registry of record for this study, so the structure-ready
reference set is the EPA-based one from the v0.27 audit, plus the holds released
under G14. The PubChem audit remains an independent cross-check only.

Produces:
    S03e_structure_ready_reference_set.csv
        the EPA-based structure-ready set after the G14 release, per substance,
        joined to the v0.28 endpoint-type and route/species classification.
    S06c_endpoint_type_reference_counts.csv
        reference counts per hematotoxicity type, before and after the release,
        which is what the type-specific screening experiment will draw on.
"""

import os
import sys
import pandas as pd

V27 = sys.argv[1]
TAB = sys.argv[2]
T27 = os.path.join(V27, "tables")

ET = [("type1_hb_function", "Type 1 haemoglobin functional impairment"),
      ("type2_rbc_anemia", "Type 2 erythrocyte damage / anaemia"),
      ("type3_counts_marrow", "Type 3 blood cell counts / marrow and haematopoietic injury"),
      ("coagulation", "Coagulation (separate fourth class)")]


def main():
    s3 = pd.read_csv(f"{T27}/S03_structure_audit_562.csv", dtype=str).fillna("")
    g14 = pd.read_csv(f"{TAB}/S03d_G14_structure_hold_adjudication.csv", dtype=str).fillna("")
    roles = pd.read_csv(f"{TAB}/S06_hematotoxicity_endpoint_types.csv", dtype=str).fillna("")
    layer = pd.read_csv(f"{TAB}/S10_dataset_A_v028_join_layer.csv", dtype=str).fillna("")

    released = set(g14[g14.g14_decision == "release_hold_standardisation_artifact"].CAS)
    retained = set(g14[g14.g14_decision != "release_hold_standardisation_artifact"].CAS)

    s3["structure_ready_v27"] = (s3.registry_status == "exact_CAS_full_key_provisional").astype(int)
    s3["g14_released"] = s3.CAS.isin(released).astype(int)
    s3["structure_ready_v28"] = (s3.structure_ready_v27 | s3.g14_released).astype(int)
    s3["g14_status"] = s3.CAS.apply(
        lambda c: "released_standardisation_artifact" if c in released
        else ("retained_genuine_stereo_difference" if c in retained else ""))

    n27 = int(s3.structure_ready_v27.sum())
    n28 = int(s3.structure_ready_v28.sum())
    print(f"structure-ready (EPA registry of record): v0.27 = {n27}  ->  v0.28 = {n28}  "
          f"(+{n28 - n27})")

    # Join the endpoint-type / route classification onto the structure-ready set.
    exp = []
    for _, r in roles.iterrows():
        for c in [x.strip() for x in str(r.cas).split(";") if x.strip()]:
            exp.append({**r.to_dict(), "cas1": c})
    R = pd.DataFrame(exp).drop_duplicates("cas1")

    keep = ["cas1", "substance_name", "evidence_tier", "all_tiers_present",
            "nite_blood_target_terms", "nite_coagulation_only",
            "type3_assignment_after_compensatory_review"] \
        + [e for e, _ in ET] \
        + [f"{e}__human_inhalation" for e, _ in ET] \
        + [f"{e}__animal_inhalation" for e, _ in ET]
    R = R[[c for c in keep if c in R.columns]]

    ready = s3[s3.structure_ready_v28 == 1][
        ["CAS", "nite_chemical", "EPA_DTXSID", "EPA_SMILES", "EPA_InChIKey",
         "canonical_SMILES", "computed_InChIKey", "structure_ready_v27",
         "g14_released", "g14_status", "registry_status"]]
    ref = ready.merge(R, left_on="CAS", right_on="cas1", how="left").drop(
        columns=["cas1"], errors="ignore").fillna("")
    ref = ref.merge(layer[["cas", "dataset_A_role_v028"]].drop_duplicates("cas"),
                    left_on="CAS", right_on="cas", how="left").drop(
        columns=["cas"], errors="ignore").fillna("")
    ref["final_label"] = ""
    ref["verification_state"] = "no_independent_primary_verification_in_v028"
    ref.to_csv(f"{TAB}/S03e_structure_ready_reference_set.csv", index=False)
    print(f"\n  S03e_structure_ready_reference_set.csv  rows={len(ref)}")

    # Per-type reference counts, before and after.
    def counts(df):
        out = {}
        for e, _ in ET:
            if e not in df.columns:
                out[e] = (0, 0, 0)
                continue
            s = df[df[e] == "1"]
            out[e] = (len(s),
                      int((s.get(f"{e}__human_inhalation", pd.Series(dtype=str)) == "1").sum()),
                      int((s.get(f"{e}__animal_inhalation", pd.Series(dtype=str)) == "1").sum()))
        return out

    before = counts(ref[ref.structure_ready_v27 == "1"]) if ref.structure_ready_v27.dtype == object \
        else counts(ref[ref.structure_ready_v27 == 1])
    after = counts(ref)

    rows = []
    for e, label in ET:
        b, a = before[e], after[e]
        rows.append(dict(endpoint_type=e, endpoint_label=label,
                         references_v27_structure_ready=b[0],
                         references_v28_after_G14_release=a[0],
                         gained=a[0] - b[0],
                         human_inhalation_backed=a[1],
                         animal_inhalation_backed=a[2]))
    t3 = ref[ref.type3_counts_marrow == "1"]
    cnt = pd.DataFrame(rows)
    cnt.to_csv(f"{TAB}/S06c_endpoint_type_reference_counts.csv", index=False)
    print(f"  S06c_endpoint_type_reference_counts.csv  rows={len(cnt)}")

    print("\n=== reference counts per hematotoxicity type (structure-ready, EPA registry) ===")
    print(cnt[["endpoint_type", "references_v27_structure_ready",
               "references_v28_after_G14_release", "gained",
               "human_inhalation_backed", "animal_inhalation_backed"]].to_string(index=False))
    print("\n  Type 3 after the compensatory-response rule:")
    print("   " + t3.type3_assignment_after_compensatory_review.value_counts()
          .to_string().replace("\n", "\n   "))

    print("\n=== notable substances the G14 release brings into structural scope ===")
    rel = ref[ref.g14_released == 1]
    for _, r in rel.sort_values("evidence_tier").iterrows():
        types = ",".join(n.split()[1] for e, n in ET if r.get(e) == "1")
        if r.evidence_tier.startswith(("A_", "B_", "D_")) or "type3" in str(r.get(
                "type3_assignment_after_compensatory_review", "")):
            print(f"  {r.CAS:13s} {r.nite_chemical[:46]:48s} {r.evidence_tier:28s} T{types}")
    print(f"\n  total released into scope: {len(rel)}")


if __name__ == "__main__":
    main()
