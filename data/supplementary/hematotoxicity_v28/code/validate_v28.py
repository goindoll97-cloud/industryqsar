"""
v0.28 — integrity and consistency checks for the supplementary tables.

Checks are assertions about the data this build actually produced. A failing
check is printed as FAIL and the script exits non-zero. Checks that cannot be
evaluated because an input is unavailable are reported as SKIP, never as PASS.
"""

import hashlib
import json
import os
import sys
import pandas as pd

OUT = "/home/user/v028/tables"
results = []


def check(name, condition, detail=""):
    state = "PASS" if condition else "FAIL"
    results.append((state, name, detail))
    print(f"  [{state}] {name}" + (f"  — {detail}" if detail else ""))
    return condition


def skip(name, detail):
    results.append(("SKIP", name, detail))
    print(f"  [SKIP] {name}  — {detail}")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    T = {}
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".csv"):
            T[f] = pd.read_csv(os.path.join(OUT, f), dtype=str).fillna("")

    print("\n--- table presence and row counts ---")
    expected = {
        "S01_source_register.csv": 5,
        "S01_input_manifest.csv": None,
        "S02_NITE_official_blood_system_set.csv": 566,
        "S02b_NITE_v024_index_reconciliation.csv": 570,
        "S03_structure_audit.csv": 570,
        "S04_NITE_classification_records_with_rationale.csv": 749,
        "S05_evidence_units_species_route.csv": 3634,
        "S06_hematotoxicity_endpoint_types.csv": 566,
        "S07_source_citations_per_evidence_unit.csv": None,
        "S08_published_human_reference_audit.csv": 28,
        "S08b_manual_primary_literature_adjudication.csv": 5,
        "S09_inclusion_exclusion_hold_rules.csv": 11,
        "S10_dataset_A_v028_join_layer.csv": 566,
        "S11_gap_register.csv": 18,
        "S03d_G14_structure_hold_adjudication.csv": 40,
        "S03e_structure_ready_reference_set.csv": 369,
        "S06c_endpoint_type_reference_counts.csv": 4,
        # Produced only when the v0.27 local archive is supplied.
        "S05c_v27_evidence_review_reconciliation.csv": 417,
        "S04_Dataset_A_349_v028.csv": 349,
        "S03c_structure_audit_cross_registry.csv": 570,
        "S07c_dataset_B_provenance_resolution.csv": 32,
    }
    for f, n in expected.items():
        if f not in T:
            check(f"{f} present", False, "missing")
        elif n is None:
            check(f"{f} present and non-empty", len(T[f]) > 0, f"rows={len(T[f])}")
        else:
            check(f"{f} row count == {n}", len(T[f]) == n, f"rows={len(T[f])}")

    print("\n--- official NITE blood-system reproduction ---")
    if "S02b_NITE_v024_index_reconciliation.csv" in T:
        r = T["S02b_NITE_v024_index_reconciliation.csv"]
        v024_only = (r.reconciliation_status == "v024_only").sum()
        both = (r.reconciliation_status == "in_both").sum()
        check("every published v0.24 CAS recovered by the v0.28 re-derivation",
              v024_only == 0, f"v024_only={v024_only}, in_both={both}")
        check("published v0.24 index size reproduced (562 CAS)", both == 562, f"in_both={both}")

    if "S02_NITE_official_blood_system_set.csv" in T:
        s2 = T["S02_NITE_official_blood_system_set.csv"]
        marrow = (s2.marrow_or_hematopoietic_target == "1").sum()
        check("marrow/haematopoietic target count == 60 (matches v0.24-v0.27 record)",
              marrow == 60, f"count={marrow}")
        coag = (s2.coagulation_only_target == "1").sum()
        check("coagulation-only substances isolated == 5", coag == 5, f"count={coag}")

    print("\n--- evidence extraction consistency ---")
    if "S05_evidence_units_species_route.csv" in T and "S04_NITE_classification_records_with_rationale.csv" in T:
        s5, s4 = T["S05_evidence_units_species_route.csv"], T["S04_NITE_classification_records_with_rationale.csv"]
        u5 = s5.groupby(["substance_id", "stot_class"]).ngroups
        u4 = s4.groupby(["nite_substance_id", "stot_class"]).ngroups
        check("every classification record yielded >=1 evidence unit", u5 == u4,
              f"segmented={u5}, records={u4}")
        check("no evidence unit has empty verbatim text",
              (s5.evidence_unit_verbatim.str.strip() == "").sum() == 0)
        bad_route = set(s5.exposure_route_basis) - {
            "inhalation", "oral", "dermal", "injection", "in_vitro", "read_across",
            "mixed_route_in_segment", "route_not_specified",
            "route_not_specified_air_unit_only", "oral_dietary_concentration_inferred"}
        check("exposure_route_basis uses only defined values", not bad_route, str(bad_route))
        bad_sp = set(s5.evidence_species_basis) - {
            "human", "animal", "mixed_human_and_animal_in_segment", "not_specified"}
        check("evidence_species_basis uses only defined values", not bad_sp, str(bad_sp))

    print("\n--- endpoint-type rules ---")
    if "S06_hematotoxicity_endpoint_types.csv" in T:
        s6 = T["S06_hematotoxicity_endpoint_types.csv"]
        # Rule R08: a marrow signal supported only by compensatory wording is
        # withheld from "marrow injury". Such a row must not also carry the
        # direct-marrow flag, which is set only for a compensatory-cue-free segment.
        bad = s6[(s6.type3_assignment_after_compensatory_review ==
                  "type3_marrow_signal_compensatory_only")
                 & (s6.type3_direct_marrow_wording == "1")]
        check("R08 consistent: compensatory-only marrow signal never flagged as direct marrow",
              len(bad) == 0, f"violations={len(bad)}")
        # Every substance falls in exactly one of the four Type 3 outcomes, and
        # the three assigned outcomes must sum to the Type 3 term count.
        vc = s6.type3_assignment_after_compensatory_review.value_counts()
        t3_any = (s6.type3_counts_marrow == "1").sum()
        assigned = (vc.get("type3_marrow_injury_supported", 0)
                    + vc.get("type3_peripheral_counts_only", 0)
                    + vc.get("type3_marrow_signal_compensatory_only", 0))
        check("Type 3 outcomes partition the substances with Type 3 wording",
              assigned == t3_any, f"assigned={assigned}, type3_any={t3_any}")
        check("Type 3 outcomes cover every substance",
              int(vc.sum()) == len(s6), f"covered={int(vc.sum())} of {len(s6)}")
        # A peripheral-counts-only outcome must have no marrow term at all.
        bad2 = s6[(s6.type3_assignment_after_compensatory_review == "type3_peripheral_counts_only")
                  & (s6.type3_marrow_term_present == "1")]
        check("peripheral-counts-only substances carry no marrow/haematopoietic term",
              len(bad2) == 0, f"violations={len(bad2)}")

    print("\n--- labelling discipline ---")
    if "S10_dataset_A_v028_join_layer.csv" in T:
        s10 = T["S10_dataset_A_v028_join_layer.csv"]
        check("no confirmed positive label is set anywhere in the join layer",
              (s10.final_label.str.strip() != "").sum() == 0)
        check("every record carries a verification_state",
              (s10.verification_state.str.strip() == "").sum() == 0)
    if "S08b_manual_primary_literature_adjudication.csv" in T:
        a = T["S08b_manual_primary_literature_adjudication.csv"]
        check("no new final label from manual adjudication",
              (a.new_final_label.str.strip() != "").sum() == 0)

    print("\n--- structure audit ---")
    if "S03_structure_audit.csv" in T:
        s3 = T["S03_structure_audit.csv"]
        inscope = (s3.structural_scope == "in_organic_single_component_scope").sum()
        check("structural scope assigned for every row",
              (s3.structural_scope.str.strip() == "").sum() == 0,
              f"in_organic_single_component_scope={inscope}")
        # Where both keys exist and status is ok, they must agree exactly.
        ok = s3[(s3.structure_status == "ok_single_organic")
                & (s3.pubchem_inchikey != "") & (s3.recomputed_inchikey != "")]
        mism = (ok.pubchem_inchikey != ok.recomputed_inchikey).sum()
        check("recomputed InChIKey agrees with registry key for ok_single_organic rows",
              mism == 0, f"mismatches={mism} of {len(ok)}")

    print("\n--- v0.27 archive merge (only when the archive is supplied) ---")
    if "S05c_v27_evidence_review_reconciliation.csv" in T:
        r = T["S05c_v27_evidence_review_reconciliation.csv"]
        full = (r.v27_full_summary_reviewed == "1").sum()
        check("v0.27 full-summary-reviewed row count reproduced == 94", full == 94,
              f"count={full}")
        pend = r[r.v27_full_summary_reviewed == "0"]
        check("previously un-read row count reproduced == 323", len(pend) == 323,
              f"count={len(pend)}")
        read = (pend.v028_read_status == "read_in_v028").sum()
        check("every previously un-read row was matched and read by v0.28",
              read == len(pend), f"read={read} of {len(pend)}")
        check("no previously un-read row yields a human inhalation endpoint unit",
              (pend.v028_finding == "human_inhalation_endpoint_in_one_unit").sum() == 0,
              f"count={(pend.v028_finding == 'human_inhalation_endpoint_in_one_unit').sum()}")
    else:
        skip("v0.27 evidence review reconciliation", "v0.27 archive not supplied")

    if "S04_Dataset_A_349_v028.csv" in T:
        a = T["S04_Dataset_A_349_v028.csv"]
        check("merged Dataset A preserves the v0.27 empty final_label",
              (a.final_label.str.strip() != "").sum() == 0,
              f"non-empty={(a.final_label.str.strip() != '').sum()}")
        matched = (a.v028_merge_status == "matched_to_v028_official_set").sum()
        check("Dataset A merge coverage recorded for every record",
              (a.v028_merge_status.str.strip() == "").sum() == 0,
              f"matched={matched} of {len(a)}")

    if "S03c_structure_audit_cross_registry.csv" in T:
        x = T["S03c_structure_audit_cross_registry.csv"]
        # Every connectivity-only case must agree on the first InChIKey block.
        cm = x[x.registry_agreement == "connectivity_match_only"]
        bad = cm[cm.apply(lambda r: r.EPA_InChIKey.split("-")[0]
                          != r.v028_recomputed_inchikey.split("-")[0], axis=1)]
        check("connectivity-only cases agree on the InChIKey connectivity block",
              len(bad) == 0, f"violations={len(bad)} of {len(cm)}")
        conf = (x.registry_agreement == "key_conflict").sum()
        check("cross-registry key conflicts enumerated", conf > 0, f"conflicts={conf}")

    print("\n--- G14 structure-hold adjudication ---")
    if "S03d_G14_structure_hold_adjudication.csv" in T:
        g = T["S03d_G14_structure_hold_adjudication.csv"]
        rel = g[g.g14_decision == "release_hold_standardisation_artifact"]
        check("every released hold has an identical InChIKey skeleton block",
              (rel.skeleton_blocks_identical == "1").all(), f"released={len(rel)}")
        check("every released hold has an identical remaining-layers hash",
              (rel.layers_hash_identical == "1").all())
        check("every released hold has identical protonation",
              (rel.protonation_identical == "1").all())
        check("every released hold is EPA non-standard 'N' vs standard 'S'",
              ((rel.epa_key_flag == "N") & (rel.computed_key_flag == "S")).all())
        check("every released hold has an independent standard InChIKey recomputed",
              (rel.v28_independent_standard_InChIKey.str.strip() != "").all())
        # Rule R09 must be re-applied after any key reconciliation: a salt or
        # hydrate stays outside the structural domain however cleanly its keys
        # reconcile. Omitting this wrongly released 2 substances in the first run.
        check("no released hold is multicomponent (rule R09 re-applied)",
              (rel.n_fragments.astype(int) <= 1).all(),
              f"multicomponent among released="
              f"{(rel.n_fragments.astype(int) > 1).sum()}")
        check("every released hold contains carbon",
              (rel.has_carbon == "1").all())
        mc = g[g.g14_decision == "retain_hold_multicomponent_outside_structural_domain"]
        check("multicomponent holds retained == 2 (matches the v0.29 independent audit)",
              len(mc) == 2, f"count={len(mc)}")
        # A hold may be retained for either of two independent reasons: the keys
        # differ on a layer that matters, or the substance is outside the
        # structural domain even though its keys reconcile.
        ret = g[g.g14_decision != "release_hold_standardisation_artifact"]
        def retained_ok(r):
            key_differs = ((r.layers_hash_identical != "1")
                           or (r.protonation_identical != "1")
                           or (r.skeleton_blocks_identical != "1"))
            out_of_scope = (int(r.n_fragments or 0) > 1) or (r.has_carbon != "1")
            return key_differs or out_of_scope
        check("every retained hold differs on a meaningful key layer OR is out of scope",
              all(retained_ok(r) for _, r in ret.iterrows()), f"retained={len(ret)}")
        check("retained holds carry a reason naming the key layer or the scope rule",
              ret.g14_reason.str.strip().ne("").all())

    if "S03e_structure_ready_reference_set.csv" in T:
        e = T["S03e_structure_ready_reference_set.csv"]
        n_rel = int((e.g14_released == "1").sum())
        n_prior = int((e.structure_ready_v27 == "1").sum())
        check("structure-ready set == prior 332 plus the 37 released",
              len(e) == 369 and n_prior == 332 and n_rel == 37,
              f"total={len(e)}, prior={n_prior}, released={n_rel}")
        check("no released substance was already structure-ready",
              ((e.g14_released == "1") & (e.structure_ready_v27 == "1")).sum() == 0)
        check("every structure-ready reference carries a SMILES",
              (e.EPA_SMILES.str.strip() == "").sum() == 0,
              f"missing={(e.EPA_SMILES.str.strip() == '').sum()}")
        check("no confirmed positive label in the structure-ready reference set",
              (e.final_label.str.strip() != "").sum() == 0)

    if "S06c_endpoint_type_reference_counts.csv" in T:
        c = T["S06c_endpoint_type_reference_counts.csv"].set_index("endpoint_type")
        check("per-type reference counts increased only by the release",
              all(int(c.loc[k, "references_v28_after_G14_release"])
                  - int(c.loc[k, "references_v27_structure_ready"])
                  == int(c.loc[k, "gained"]) for k in c.index))
        check("Type 2 is the largest per-type reference set",
              int(c.loc["type2_rbc_anemia", "references_v28_after_G14_release"]) == 282,
              f"Type2={c.loc['type2_rbc_anemia', 'references_v28_after_G14_release']}")

    print("\n--- inputs that were NOT available (reported, never passed) ---")
    for item, path in [
        ("hematotoxicity_v27_supplement.zip", "/root/.claude/uploads/b34344cd-b845-515b-afd5-81a94c1c489e/a9dae0f1-hematotoxicity_v27_supplement.zip"),
        ("EPA CompTox CCD-Batch-Search raw export", "/home/user/CCD-Batch-Search.csv"),
    ]:
        if os.path.exists(path):
            check(f"{item} present", True, sha256(path)[:16])
        else:
            skip(f"{item} check", "file not provided to this build")

    print("\n--- output hashes ---")
    hashes = {f: sha256(os.path.join(OUT, f)) for f in sorted(os.listdir(OUT))
              if f.endswith(".csv")}
    with open(os.path.join(OUT, "output_manifest.json"), "w") as fh:
        json.dump({"version": "v0.28-evidence-rederivation",
                   "table_sha256": hashes}, fh, indent=2)
    print(f"  wrote output_manifest.json with {len(hashes)} table hashes")

    n_fail = sum(1 for s, _, _ in results if s == "FAIL")
    n_skip = sum(1 for s, _, _ in results if s == "SKIP")
    n_pass = sum(1 for s, _, _ in results if s == "PASS")
    print(f"\n=== {n_pass} passed, {n_fail} failed, {n_skip} skipped ===")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
