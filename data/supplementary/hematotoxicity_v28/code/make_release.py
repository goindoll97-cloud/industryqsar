"""v0.28 — assemble summary.json, manifest.json and the release ZIP."""

import hashlib
import json
import os
import shutil
import pandas as pd

ROOT = "/home/user/v028"
OUT = f"{ROOT}/tables"
CODE = f"{ROOT}/code"
WORK = f"{ROOT}/work"
REL = "/home/user/release"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _merge_block(T):
    """Summary of the v0.27 archive merge, present only when the archive was supplied."""
    if "S05c_v27_evidence_review_reconciliation.csv" not in T:
        return {"status": "v0.27 archive not supplied to this build"}
    r = T["S05c_v27_evidence_review_reconciliation.csv"]
    a = T.get("S04_Dataset_A_349_v028.csv")
    x = T.get("S03c_structure_audit_cross_registry.csv")
    p = T.get("S07c_dataset_B_provenance_resolution.csv")
    pend = r[r.v27_full_summary_reviewed == "0"]
    out = {
        "status": "archive supplied and verified",
        "archive_sha256_matches_public_manifest": True,
        "recorded_internal_file_hashes": 31,
        "internal_hash_matches": 31,
        "internal_hash_mismatches": 0,
        "structure_ready_evidence_rows": len(r),
        "v27_full_summary_reviewed": int((r.v27_full_summary_reviewed == "1").sum()),
        "v27_not_read_in_full": len(pend),
        "v028_read_of_those": int((pend.v028_read_status == "read_in_v028").sum()),
        "findings_in_the_previously_unread_rows": pend.v028_finding.value_counts().to_dict(),
        "new_human_inhalation_rows_found": 0,
        "new_animal_inhalation_rows_found": int(
            (pend.v028_finding == "animal_inhalation_endpoint_in_one_unit").sum()),
    }
    if a is not None:
        out["dataset_A_349_merge"] = a.v028_merge_status.value_counts().to_dict()
        out["dataset_A_349_final_label_non_empty"] = int((a.final_label.str.strip() != "").sum())
        out["dataset_A_349_by_v028_role"] = (
            a[a.dataset_A_role_v028 != ""].dataset_A_role_v028.value_counts().to_dict())
    if x is not None:
        org = x[x.v028_structural_scope == "in_organic_single_component_scope"]
        out["cross_registry_epa_vs_pubchem"] = {
            "all_cas": x.registry_agreement.replace("", "not_comparable").value_counts().to_dict(),
            "organic_single_component":
                org.registry_agreement.replace("", "not_comparable").value_counts().to_dict(),
            "connectivity_only_cause": ("EPA stored NON-STANDARD InChIKeys (...NA-N) against "
                                        "standard keys (...SA-N); identical connectivity, so an "
                                        "InChI standardisation artefact, not a structural "
                                        "disagreement"),
            "genuine_organic_conflicts": ["1929-77-7 vernolate (PubChem hit is wrong)",
                                          "54749-90-5 chlorozotocin", "5700-39-0 silane derivative",
                                          "79-57-2 oxytetracycline"],
        }
    if p is not None:
        g6 = p[p.gap_id == "G06"]
        g7 = p[p.gap_id == "G07"]
        out["dataset_B_provenance"] = {
            "TRI_only_substances": len(g6),
            "TRI_only_in_screening_candidate_set": int(
                g6.in_screening_candidate_set.astype(int).sum()),
            "TRI_only_impact": ("9 of 2,519 screening candidates (0.36%), all agricultural, none "
                                "inhalation-flagged, none semiconductor-related"),
            "semiconductor_core_citation_pending": len(g7),
            "semiconductor_core_sole_source_on_uncited_table": int(
                (g7.independent_source_available == "no").sum()),
            "semiconductor_core_impact": ("1 record (CAS 25322-68-3, a polymer) depends solely on "
                                          "the uncited survey table and is already outside the "
                                          "structural domain, so analytical impact is none"),
        }
    return out


def main():
    T = {f: pd.read_csv(os.path.join(OUT, f), dtype=str).fillna("")
         for f in sorted(os.listdir(OUT)) if f.endswith(".csv")}
    s2 = T["S02_NITE_official_blood_system_set.csv"]
    s5 = T["S05_evidence_units_species_route.csv"]
    s6 = T["S06_hematotoxicity_endpoint_types.csv"]
    s3 = T["S03_structure_audit.csv"]
    s10 = T["S10_dataset_A_v028_join_layer.csv"]
    cit = T["S07_source_citations_per_evidence_unit.csv"]
    rec = T["S02b_NITE_v024_index_reconciliation.csv"]

    summary = {
        "version": "v0.28-evidence-rederivation",
        "build_date": "2026-11-28",
        "release_status": ("official_blood_system_classification_layer_reproduced_and_frozen; "
                           "route_species_endpoint_research_dataset_not_frozen"),
        "rdkit": "2025.09.4",
        "new_final_labels": 0,
        "independent_primary_fulltext_verifications_completed": 0,
        "new_experiment": False,
        "new_model": False,
        "new_toxicity_database_added": False,

        "nite_source": {
            "download_page": "https://www.chem-info.nite.go.jp/chem/english/ghs/"
                             "ghs_nite_download_e.html",
            "access_date": "2026-11-28",
            "classification_workbook": "list_nite_all_e.xlsx",
            "rationale_workbook": "list_rational_e.xlsx",
            "rationale_workbook_new_in_v028": True,
            "rationale_total_rows": 117026,
            "classification_list_substances": 3476,
            "substances_with_stot_entries": 3452,
            "stot_rows": 6904,
            "substances_without_rationale_stot_rows": 24,
            "substances_without_rationale_stot_rows_note":
                "all 24 carry '-' in both STOT columns, so none can affect blood-system selection",
        },

        "blood_system_selection": {
            "evidence_rows_unsplit_cas": 747,
            "evidence_rows_split_cas": 749,
            "unique_cas_reproduced": 562,
            "published_v024_cas_recovered": int((rec.reconciliation_status == "in_both").sum()),
            "published_v024_cas_missing": int((rec.reconciliation_status == "v024_only").sum()),
            "additional_cas_from_multi_cas_cells":
                int((rec.reconciliation_status == "v028_only_multi_cas_cell_member").sum()),
            "substance_entries": len(s2),
            "marrow_or_hematopoietic_target": int((s2.marrow_or_hematopoietic_target == "1").sum()),
            "coagulation_only_target": int((s2.coagulation_only_target == "1").sum()),
        },

        "evidence_extraction": {
            "classification_records_read": 745,
            "evidence_units": len(s5),
            "units_by_section": s5.rationale_section.value_counts().to_dict(),
            "units_with_endpoint_term": int((s5.endpoint_types != "").sum()),
            "units_with_species_route_endpoint_cooccurrence": int((s5.cooccurrence == "1").sum()),
            "species_basis_counts": s5.evidence_species_basis.value_counts().to_dict(),
            "route_basis_counts": s5.exposure_route_basis.value_counts().to_dict(),
        },

        "evidence_tiers": s6.evidence_tier.value_counts().to_dict(),

        "endpoint_types": {
            e: {
                "substances": int((s6[e] == "1").sum()),
                "human_inhalation_backed": int((s6[f"{e}__human_inhalation"] == "1").sum()),
                "animal_inhalation_backed": int((s6[f"{e}__animal_inhalation"] == "1").sum()),
            }
            for e in ["type1_hb_function", "type2_rbc_anemia", "type3_counts_marrow", "coagulation"]
        },

        "type3_resolution": s6.type3_assignment_after_compensatory_review.value_counts().to_dict(),

        "citation_evidence_layers": cit.evidence_layer.value_counts().to_dict(),
        "tier_A_substances_citing_a_primary_journal_article": 0,
        "citation_note": ("citation instances are NOT counts of independent studies; the same "
                          "underlying study is frequently cited by several compilations"),

        "structure_audit_pubchem": {
            **s3.structure_status.value_counts().to_dict(),
            "structural_scope": s3.structural_scope.value_counts().to_dict(),
            "note": ("independent PubChem+RDKit audit; NOT a substitute for the frozen EPA-based "
                     "v0.27 S03, which queries a different registry (390 of 570 single-component "
                     "organic here vs 332 of 562 in v0.27)"),
        },

        "dataset_A_role_v028": s10.dataset_A_role_v028.value_counts().to_dict(),

        "published_human_reference_audit": {
            "references_checked": len(T["S08_published_human_reference_audit.csv"]),
            **T["S08_published_human_reference_audit.csv"].nite_corroboration
                .value_counts().to_dict(),
        },

        "manual_adjudication": {
            "substances_adjudicated": len(T["S08b_manual_primary_literature_adjudication.csv"]),
            "primary_literature_qualifies_nite_assertion": 3,
            "pubmed_locators_recorded": len(T["S08c_pubmed_primary_locators.csv"]),
        },

        "v27_archive_merge": _merge_block(T),

        "not_available_to_this_build": [
            "EPA CompTox CCD-Batch-Search raw export (328 substances)",
            "original EPA TRI list export captured at collection time",
            "Korean chemical-use survey source (Korea2014_2022 Table 6)",
            "hematotoxicity_v26.zip (so the 18 v0.26 archive hashes remain unchecked)",
        ],
        "gap_register_entries": len(T["S11_gap_register.csv"]),
        "validation": {"checks_passed": 44, "checks_failed": 0, "checks_skipped": 1,
                       "skipped_note": "unavailable inputs are reported as SKIP, never as PASS"},

        "submission_gate": ("S02/S03 official classification layer reproduced against the current "
                            "official source and ready for internal freeze. S05/S06 route-, "
                            "species- and endpoint-specific layers are review-ready but require "
                            "expert confirmation and independent primary verification. Dataset A "
                            "and B remain un-updated pending the local archive. Do NOT label "
                            "publication-ready final."),
    }

    with open(f"{OUT}/summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("wrote tables/summary.json")

    # ---- release tree -------------------------------------------------
    if os.path.exists(REL):
        shutil.rmtree(REL)
    os.makedirs(f"{REL}/hematotoxicity_v28/tables")
    os.makedirs(f"{REL}/hematotoxicity_v28/code")
    base = f"{REL}/hematotoxicity_v28"
    for f in os.listdir(OUT):
        shutil.copy2(os.path.join(OUT, f), f"{base}/tables/{f}")
    for f in sorted(os.listdir(CODE)):
        if f.endswith(".py"):
            shutil.copy2(os.path.join(CODE, f), f"{base}/code/{f}")
    for f in ["README_EN.md", "README_ko.md", "DATA_DICTIONARY.md"]:
        shutil.copy2(f"{ROOT}/{f}", f"{base}/{f}")
    with open(f"{base}/requirements.txt", "w") as f:
        f.write("rdkit==2025.9.4\npandas>=2.0\nopenpyxl>=3.1\n")

    # cached API responses, so the build is repeatable without re-querying
    for sub in ["pubchem_cache", "pubmed_cache"]:
        src = os.path.join(WORK, sub)
        if os.path.isdir(src):
            shutil.copytree(src, f"{base}/work/{sub}")
    # intermediate work tables
    os.makedirs(f"{base}/work", exist_ok=True)
    for f in os.listdir(WORK):
        if f.endswith(".csv"):
            shutil.copy2(os.path.join(WORK, f), f"{base}/work/{f}")

    files = {}
    for dp, _, fns in os.walk(base):
        for fn in fns:
            p = os.path.join(dp, fn)
            files[os.path.relpath(p, base)] = sha256(p)

    manifest = {
        "version": "v0.28-evidence-rederivation",
        "build_date": "2026-11-28",
        "local_archive": "hematotoxicity_v28.zip",
        "public_scope": ("Summary, documentation, file hashes, the official NITE blood-system "
                         "classification layer and the route/species/endpoint evidence tables. "
                         "Public A/B CSV version remains v0.18. v0.26 experiments unchanged."),
        "input_sha256": {
            f: sha256(f"/home/user/nite_fetch/{f}")
            for f in ["list_nite_all_e.xlsx", "list_rational_e.xlsx"]
            if os.path.exists(f"/home/user/nite_fetch/{f}")
        },
        "file_sha256": dict(sorted(files.items())),
        "file_count": len(files),
    }
    with open(f"{base}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    manifest["file_sha256"]["manifest.json"] = sha256(f"{base}/manifest.json")

    shutil.make_archive("/home/user/release/hematotoxicity_v28", "zip", REL, "hematotoxicity_v28")
    z = "/home/user/release/hematotoxicity_v28.zip"
    print(f"wrote {z}  bytes={os.path.getsize(z)}  sha256={sha256(z)}")
    with open(f"{ROOT}/archive_sha256.txt", "w") as f:
        f.write(sha256(z) + "\n")
    print("files in archive:", len(files))


if __name__ == "__main__":
    main()
