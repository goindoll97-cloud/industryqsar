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

        "not_available_to_this_build": [
            "hematotoxicity_v27_supplement.zip",
            "EPA CompTox CCD-Batch-Search raw export (328 substances)",
            "original EPA TRI list export",
            "chemical-use survey source for 4 semiconductor-core records",
        ],
        "could_not_be_updated_in_place": [
            "Dataset A (349 records)", "Dataset B (8,110 records)",
            "screening candidates (2,519 records)",
            "v0.27 output hashes (22) and v0.26 archive hashes (18)",
            "the 94-reviewed / 323-pending evidence-row mapping",
        ],
        "gap_register_entries": len(T["S11_gap_register.csv"]),
        "validation": {"checks_passed": 31, "checks_failed": 0, "checks_skipped": 2,
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
