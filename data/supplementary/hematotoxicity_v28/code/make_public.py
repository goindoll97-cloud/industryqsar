"""
v0.28 — build the public-repository projection.

The repository convention established at v0.24 is that the public repository does
NOT republish the original classification rationale sentences or the full
industrial raw data. This script therefore publishes:

  * summaries, documentation and file hashes
  * a per-substance public index (official classification flags, evidence tier,
    route/species/endpoint flags) with NO verbatim rationale text
  * the aggregate crosstabs, the selection rules and the gap register
  * the audit of the already-public v0.18 human reference set
  * the reproduction code

and withholds the verbatim-text tables (S04, S05, S07) and the full join layer,
which stay in the local archive.
"""

import json
import os
import shutil
import hashlib
import pandas as pd

SRC = "/home/user/v028/tables"
DST = "/home/user/industryqsar/data/supplementary/hematotoxicity_v28"
ROOT = "/home/user/v028"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    os.makedirs(DST, exist_ok=True)
    s2 = pd.read_csv(f"{SRC}/S02_NITE_official_blood_system_set.csv", dtype=str).fillna("")
    s6 = pd.read_csv(f"{SRC}/S06_hematotoxicity_endpoint_types.csv", dtype=str).fillna("")
    s3 = pd.read_csv(f"{SRC}/S03_structure_audit.csv", dtype=str).fillna("")
    s10 = pd.read_csv(f"{SRC}/S10_dataset_A_v028_join_layer.csv", dtype=str).fillna("")

    st = s3.groupby("substance_id").agg(structural_scope=("structural_scope", "first"),
                                        structure_status=("structure_status", "first")).reset_index()

    pub = (s2.merge(s6[["substance_id", "evidence_tier", "all_tiers_present",
                        "type1_hb_function", "type2_rbc_anemia", "type3_counts_marrow",
                        "coagulation", "type1_hb_function__human_inhalation",
                        "type2_rbc_anemia__human_inhalation",
                        "type3_counts_marrow__human_inhalation",
                        "type1_hb_function__animal_inhalation",
                        "type2_rbc_anemia__animal_inhalation",
                        "type3_counts_marrow__animal_inhalation",
                        "type3_assignment_after_compensatory_review",
                        "n_segments", "n_segments_with_endpoint",
                        "negation_in_endpoint_segments", "has_noael_loael",
                        "has_quantified_exposure"]],
                    left_on="nite_substance_id", right_on="substance_id", how="left")
             .merge(st, on="substance_id", how="left")
             .merge(s10[["substance_id", "dataset_A_role_v028", "final_label",
                         "verification_state"]], on="substance_id", how="left")
             .drop(columns=["substance_id"]).fillna(""))
    pub = pub.sort_values(["evidence_tier", "substance_name"])
    pub.to_csv(f"{DST}/nite_evidence_public_index.csv", index=False)
    print(f"  nite_evidence_public_index.csv  rows={len(pub)} cols={len(pub.columns)}")

    # Cross-registry comparison: publish the FINDING (agreement class per CAS and
    # the conflict detail), not the full structure table. Structure identifiers in
    # bulk stay with the local archive, as the public A/B CSV release is v0.18.
    xp = f"{SRC}/S03c_structure_audit_cross_registry.csv"
    if os.path.exists(xp):
        x = pd.read_csv(xp, dtype=str).fillna("")
        red = x[["CAS", "nite_chemical", "registry_status", "scope_status",
                 "v028_structure_status", "v028_structural_scope", "registry_agreement"]].copy()
        # Identity detail only where the registries actually disagree.
        red["epa_inchikey"] = x.apply(
            lambda r: r.EPA_InChIKey if r.registry_agreement in
            ("key_conflict", "connectivity_match_only") else "", axis=1)
        red["v028_recomputed_inchikey"] = x.apply(
            lambda r: r.v028_recomputed_inchikey if r.registry_agreement in
            ("key_conflict", "connectivity_match_only") else "", axis=1)
        red["epa_name"] = x.apply(
            lambda r: r.EPA_name if r.registry_agreement == "key_conflict" else "", axis=1)
        red.to_csv(f"{DST}/S03c_structure_registry_agreement.csv", index=False)
        print(f"  S03c_structure_registry_agreement.csv  rows={len(red)} (reduced projection)")

    # Aggregate / rule / audit tables carry no verbatim rationale text.
    for f in ["S05c_v27_evidence_review_reconciliation.csv",
              "S07c_dataset_B_provenance_resolution.csv",
              "S03d_G14_structure_hold_adjudication.csv",
              "S06c_endpoint_type_reference_counts.csv",
              "S01_source_register.csv", "S01_input_manifest.csv",
              "S02b_NITE_v024_index_reconciliation.csv", "S05b_species_route_crosstab.csv",
              "S06b_endpoint_type_summary.csv", "S07b_cited_source_register.csv",
              "S08_published_human_reference_audit.csv",
              "S08b_manual_primary_literature_adjudication.csv",
              "S08c_pubmed_primary_locators.csv",
              "S09_inclusion_exclusion_hold_rules.csv", "S11_gap_register.csv",
              "summary.json", "output_manifest.json"]:
        shutil.copy2(f"{SRC}/{f}", f"{DST}/{f}")
        print(f"  {f}")

    os.makedirs(f"{DST}/code", exist_ok=True)
    for f in sorted(os.listdir(f"{ROOT}/code")):
        if f.endswith(".py"):
            shutil.copy2(f"{ROOT}/code/{f}", f"{DST}/code/{f}")
    shutil.copy2(f"{ROOT}/DATA_DICTIONARY.md", f"{DST}/DATA_DICTIONARY.md")
    shutil.copy2(f"{ROOT}/README_EN.md", f"{DST}/README_EN.md")

    local_manifest = json.load(open("/home/user/release/hematotoxicity_v28/manifest.json"))
    pubfiles = {}
    for dp, _, fns in os.walk(DST):
        for fn in fns:
            p = os.path.join(dp, fn)
            if fn == "manifest.json":
                continue
            pubfiles[os.path.relpath(p, DST)] = sha256(p)
    manifest = {
        "version": "v0.28-evidence-rederivation",
        "build_date": "2026-11-28",
        "local_archive": "hematotoxicity_v28.zip",
        "archive_sha256": open(f"{ROOT}/archive_sha256.txt").read().strip(),
        "archive_file_count": local_manifest["file_count"],
        "input_sha256": local_manifest["input_sha256"],
        "public_file_sha256": dict(sorted(pubfiles.items())),
        "withheld_from_public_repository": {
            "S04_NITE_classification_records_with_rationale.csv":
                "verbatim official rationale text (749 records)",
            "S05_evidence_units_species_route.csv":
                "verbatim evidence-unit text (3,634 units)",
            "S07_source_citations_per_evidence_unit.csv":
                "verbatim citation text per evidence unit (3,007 rows)",
            "S03_structure_audit.csv": "full per-CAS structure audit (570 rows)",
            "S03c_structure_audit_cross_registry.csv":
                "full cross-registry structure table; a reduced projection carrying the "
                "agreement class per CAS and the conflict detail is published as "
                "S03c_structure_registry_agreement.csv",
            "S06_hematotoxicity_endpoint_types.csv": "full endpoint table (566 rows, 38 columns)",
            "S10_dataset_A_v028_join_layer.csv": "full Dataset A join layer (566 rows, 50 columns)",
            "S04_Dataset_A_349_v028.csv":
                "Dataset A (349 records) merged with the v0.28 layer; the public A/B CSV "
                "release remains v0.18",
            "S03e_structure_ready_reference_set.csv":
                "the 371-substance structure-ready reference set with SMILES and InChIKeys; "
                "bulk structure data stays with the local archive, while the G14 adjudication "
                "(S03d) and the per-type reference counts (S06c) are published",
            "reason": "repository convention since v0.24: the public repository does not "
                      "republish original classification rationale sentences or full raw data. "
                      "All withheld tables are in the local archive and are regenerated by the "
                      "published code from the official NITE download plus the v0.27 archive.",
        },
        "public_scope": "Summaries, documentation, file hashes, the per-substance public index "
                        "and the reproduction code. Public A/B CSV version remains v0.18. "
                        "v0.26 experiments and the v0.24 NITE public index are unchanged.",
    }
    with open(f"{DST}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\n  manifest.json with {len(pubfiles)} public file hashes")
    print(f"  public dir total: {sum(os.path.getsize(os.path.join(dp,fn)) for dp,_,fns in os.walk(DST) for fn in fns)} bytes")


if __name__ == "__main__":
    main()
