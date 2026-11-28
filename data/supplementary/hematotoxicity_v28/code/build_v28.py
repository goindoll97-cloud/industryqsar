"""
v0.28 — build the supplementary tables for the hematotoxicity screening study.

Run order
---------
    python3 -I extract_stot.py        <list_rational_e.xlsx>  work/nite_stot_all_rows.csv
    python3 -I reconcile.py           <list_nite_all_e.xlsx>  work/nite_stot_all_rows.csv
    python3 -I blood_select_v2.py
    python3 -I run_extract.py
    python3 -I aggregate_evidence.py
    python3 -I extract_citations.py
    python3 -I resolve_structures.py
    python3 -I build_v28.py                       <-- this script
    python3 -I validate_v28.py

Scope and honesty constraints
-----------------------------
* This build regenerates, from the current official NITE bulk download, the
  layers that depend only on public inputs: the official blood-system
  classification set (S1-S3), the route/species evidence classification (S5),
  the endpoint-type classification (S6), the selection rules (S9) and the
  source register.
* It CANNOT regenerate Dataset A (349 records), Dataset B (8,110 records) or the
  screening candidate set (2,519 records): those tables exist only in the local
  hematotoxicity_v27_supplement.zip, which was not available to this build.
  For those, the build emits a JOIN LAYER keyed on CAS plus an explicit gap
  register, so the layer can be merged into the local tables without guessing
  their contents.
* No row in any output sets a confirmed positive hematotoxicity label. New
  final labels in this build: 0. Independent primary-source verifications
  completed in this build: 0.
"""

import hashlib
import json
import os
import re
import shutil
import pandas as pd

WORK = "/home/user/v028/work"
OUT = "/home/user/v028/tables"
CODE = "/home/user/v028/code"
RAW = "/home/user/nite_fetch"

NITE_DOWNLOAD_PAGE = "https://www.chem-info.nite.go.jp/chem/english/ghs/ghs_nite_download_e.html"
ACCESS_DATE = "2026-11-28"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def w(df, name):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    df.to_csv(p, index=False)
    print(f"  {name:52s} rows={len(df):6d} cols={len(df.columns):3d}")
    return p


def main():
    os.makedirs(OUT, exist_ok=True)

    # ---------------------------------------------------------------- S1
    # Source register and input manifest.
    src = pd.DataFrame([
        dict(source_id="NITE-GHS-CLASS", organisation="NITE (Japan)",
             dataset="Latest GHS classification list (list_nite_all_e.xlsx)",
             url=NITE_DOWNLOAD_PAGE, file="list_nite_all_e.xlsx",
             access_date=ACCESS_DATE, role="official GHS hazard classification per substance",
             notes="3,476 substance entries; 3,435 distinct CAS cells; STOT-SE/RE columns carry "
                   "target organs in parentheses"),
        dict(source_id="NITE-GHS-RATIONALE", organisation="NITE (Japan)",
             dataset="Latest rationale list (list_rational_e.xlsx)",
             url=NITE_DOWNLOAD_PAGE, file="list_rational_e.xlsx",
             access_date=ACCESS_DATE,
             role="verbatim 'Rationale for the classification' per substance x hazard class",
             notes="117,026 rows; 6,904 STOT rows covering 3,452 substances. NOT part of the "
                   "v0.24-v0.27 input manifest; first used in v0.28"),
        dict(source_id="PUBCHEM-PUGREST", organisation="NCBI PubChem",
             dataset="PUG-REST compound property service",
             url="https://pubchem.ncbi.nlm.nih.gov/rest/pug", file="work/pubchem_cache/*.json",
             access_date=ACCESS_DATE, role="chemical identity and structure by CAS",
             notes="responses cached verbatim for reproducibility; InChIKey independently "
                   "recomputed with RDKit"),
        dict(source_id="REPO-NITE-V024-INDEX", organisation="this study (public repository)",
             dataset="nite_blood_public_index.csv (v0.24)",
             url="https://github.com/goindoll97-cloud/industryqsar/blob/main/data/supplementary/"
                 "hematotoxicity_v24_nite/nite_blood_public_index.csv",
             file="nite_blood_public_index.csv", access_date=ACCESS_DATE,
             role="published 562-CAS official blood-system candidate index; reconciliation target",
             notes="used only to verify that the v0.28 re-derivation reproduces the published set"),
        dict(source_id="REPO-DATASET-A-V018", organisation="this study (public repository)",
             dataset="dataset_A_human_inhalation_references.csv (v0.18)",
             url="https://github.com/goindoll97-cloud/industryqsar/blob/main/data/supplementary/"
                 "hematotoxicity_v18/dataset_A_human_inhalation_references.csv",
             file="dataset_A_human_inhalation_references.csv", access_date=ACCESS_DATE,
             role="published human reference set (28 records) used for the STEP 5 audit",
             notes="v0.18 is the latest PUBLIC A/B release; the v0.27 Dataset A (349 records) "
                   "was not available to this build"),
    ])
    w(src, "S01_source_register.csv")

    manifest = []
    for f in ["list_nite_all_e.xlsx", "list_rational_e.xlsx"]:
        p = os.path.join(RAW, f)
        if os.path.exists(p):
            manifest.append(dict(file=f, location="official download (NITE)",
                                 bytes=os.path.getsize(p), sha256=sha256(p),
                                 access_date=ACCESS_DATE, source_id="NITE-GHS-CLASS"
                                 if "all" in f else "NITE-GHS-RATIONALE"))
    for f, sid in [("nite_blood_public_index.csv", "REPO-NITE-V024-INDEX")]:
        p = ("/home/user/industryqsar/data/supplementary/hematotoxicity_v24_nite/" + f)
        if os.path.exists(p):
            manifest.append(dict(file=f, location="public repository (v0.24)",
                                 bytes=os.path.getsize(p), sha256=sha256(p),
                                 access_date=ACCESS_DATE, source_id=sid))
    p = ("/home/user/industryqsar/data/supplementary/hematotoxicity_v18/"
         "dataset_A_human_inhalation_references.csv")
    if os.path.exists(p):
        manifest.append(dict(file="dataset_A_human_inhalation_references.csv",
                             location="public repository (v0.18)", bytes=os.path.getsize(p),
                             sha256=sha256(p), access_date=ACCESS_DATE,
                             source_id="REPO-DATASET-A-V018"))
    w(pd.DataFrame(manifest), "S01_input_manifest.csv")

    # ---------------------------------------------------------------- S2
    roles = pd.read_csv(f"{WORK}/nite_substance_evidence_roles.csv", dtype=str).fillna("")
    blood = pd.read_csv(f"{WORK}/nite_blood_rows_v028.csv", dtype=str).fillna("")

    s2 = roles[["substance_id", "cas_all", "name", "hazard_classes", "nite_blood_categories",
                "nite_blood_target_terms", "nite_marrow_or_hematopoietic_target",
                "nite_coagulation_only", "classification_years"]].copy()
    s2.columns = ["nite_substance_id", "cas", "substance_name", "stot_classes",
                  "blood_system_categories", "blood_system_target_terms",
                  "marrow_or_hematopoietic_target", "coagulation_only_target",
                  "nite_classification_years"]
    s2["nite_detail_url"] = s2.nite_substance_id.apply(
        lambda i: f"https://www.chem-info.nite.go.jp/chem/english/ghs/{i}e.html")
    s2 = s2.sort_values("substance_name")
    w(s2, "S02_NITE_official_blood_system_set.csv")

    # Reconciliation against the published v0.24 index.
    pub = pd.read_csv("/home/user/industryqsar/data/supplementary/hematotoxicity_v24_nite/"
                      "nite_blood_public_index.csv", dtype=str).fillna("")
    exp = []
    for _, x in roles.iterrows():
        for c in [y.strip() for y in x.cas_all.split(";") if y.strip()]:
            exp.append(dict(cas=c, nite_substance_id=x.substance_id, substance_name=x["name"],
                            coagulation_only_target=x.nite_coagulation_only,
                            marrow_or_hematopoietic_target=x.nite_marrow_or_hematopoietic_target))
    newset = pd.DataFrame(exp)
    rec = newset.merge(pub[["CAS"]].assign(in_published_v024_index="1"),
                       left_on="cas", right_on="CAS", how="outer").fillna("")
    rec["in_v028_rederivation"] = (rec.nite_substance_id != "").astype(int).astype(str)
    rec["in_published_v024_index"] = rec.in_published_v024_index.replace("", "0")
    rec["reconciliation_status"] = rec.apply(
        lambda r: "in_both" if r.in_v028_rederivation == "1" and r.in_published_v024_index == "1"
        else ("v028_only_multi_cas_cell_member" if r.in_v028_rederivation == "1"
              else "v024_only"), axis=1)
    rec = rec.drop(columns=["CAS"]).sort_values(["reconciliation_status", "cas"])
    w(rec, "S02b_NITE_v024_index_reconciliation.csv")

    # ---------------------------------------------------------------- S3
    sp = f"{WORK}/nite_structure_audit_v028.csv"
    if os.path.exists(sp):
        s3 = pd.read_csv(sp, dtype=str).fillna("")
        IN_SCOPE = {"ok_single_organic", "connectivity_only"}
        s3["structural_scope"] = s3.structure_status.apply(
            lambda v: "in_organic_single_component_scope" if v in IN_SCOPE
            else ("outside_organic_structural_domain"
                  if v in ("inorganic_or_no_carbon", "multicomponent")
                  else "structure_unresolved_hold"))
        s3["exclusion_reason"] = s3.apply(
            lambda r: "" if r.structural_scope == "in_organic_single_component_scope"
            else {"inorganic_or_no_carbon": "no carbon atom; outside organic structural domain",
                  "multicomponent": "disconnected multi-component SMILES (salt or mixture)",
                  "unparsable": "RDKit could not parse the retrieved SMILES",
                  "not_found": "no PubChem record for this CAS",
                  "no_cas": "NITE entry carries no registry-format CAS",
                  "key_mismatch": "recomputed InChIKey disagrees with registry InChIKey",
                  }.get(r.structure_status, r.structure_status), axis=1)
        w(s3, "S03_structure_audit.csv")
    else:
        s3 = None
        print("  !! S03 skipped: structure audit not available")

    # ---------------------------------------------------------------- S4
    # NITE official classification records with verbatim rationale.
    s4 = blood[["substance_id", "cas", "name", "hazard_class", "blood_categories",
                "blood_core_terms", "coagulation_only", "marrow_or_hematopoietic",
                "lymphoid_terms", "all_target_organs", "classification_raw", "year",
                "rationale"]].copy()
    s4.columns = ["nite_substance_id", "cas", "substance_name", "stot_class",
                  "blood_system_categories", "blood_system_target_terms",
                  "coagulation_only_target", "marrow_or_hematopoietic_target",
                  "lymphoid_target_terms", "all_stot_target_organs",
                  "nite_classification_verbatim", "nite_classification_year",
                  "nite_rationale_verbatim"]
    w(s4.sort_values(["substance_name", "stot_class"]),
      "S04_NITE_classification_records_with_rationale.csv")

    # ---------------------------------------------------------------- S5
    segs = pd.read_csv(f"{WORK}/nite_evidence_segments.csv", dtype=str).fillna("")
    s5 = segs.rename(columns={
        "cas_all": "cas", "name": "substance_name", "hazard_class": "stot_class",
        "section": "rationale_section", "unit_id": "evidence_unit_id",
        "species_basis": "evidence_species_basis", "route_basis": "exposure_route_basis",
        "segment_text": "evidence_unit_verbatim"})
    w(s5, "S05_evidence_units_species_route.csv")

    s5sum = (s5.groupby(["evidence_species_basis", "exposure_route_basis"])
               .size().reset_index(name="evidence_units")
               .sort_values("evidence_units", ascending=False))
    w(s5sum, "S05b_species_route_crosstab.csv")

    # ---------------------------------------------------------------- S6
    ET = ["type1_hb_function", "type2_rbc_anemia", "type3_counts_marrow", "coagulation"]
    keep = (["substance_id", "cas_all", "name", "evidence_tier", "all_tiers_present",
             "nite_blood_target_terms", "nite_marrow_or_hematopoietic_target",
             "nite_coagulation_only", "hazard_classes", "classification_years",
             "n_segments", "n_segments_with_endpoint", "human_segments", "animal_segments",
             "animal_species_named", "routes_observed", "human_cue_types"]
            + ET + [f"{e}__human_inhalation" for e in ET] + [f"{e}__animal_inhalation" for e in ET]
            + ["type3_marrow_term_present", "type3_direct_marrow_wording",
               "type3_compensatory_wording", "type3_resolution",
               "type2_hemolytic_wording", "compensatory_vs_direct_note",
               "negation_in_endpoint_segments", "has_noael_loael",
               "has_quantified_exposure", "review_state"])
    s6 = roles[[c for c in keep if c in roles.columns]].copy()
    s6 = s6.rename(columns={"cas_all": "cas", "name": "substance_name"})
    # Protocol requirement: a Type 3 signal supported only by compensatory
    # erythropoiesis wording is not direct marrow toxicity.
    # Carried through from the aggregation step (rule R08). Four-way outcome:
    #   not_assigned_no_type3_wording          no Type 3 term in the rationale
    #   type3_peripheral_counts_only           peripheral count change only, no
    #                                          marrow/haematopoietic term
    #   type3_marrow_injury_supported          marrow term in a segment with no
    #                                          compensatory cue
    #   type3_marrow_signal_compensatory_only  marrow term appears only alongside
    #                                          compensatory wording -> withheld
    s6["type3_assignment_after_compensatory_review"] = s6["type3_resolution"]
    w(s6, "S06_hematotoxicity_endpoint_types.csv")

    rows = []
    for e in ET:
        rows.append(dict(endpoint_type=e,
                         substances_with_endpoint_text=int((s6[e] == "1").sum()),
                         human_inhalation_backed=int((s6[f"{e}__human_inhalation"] == "1").sum()),
                         animal_inhalation_backed=int((s6[f"{e}__animal_inhalation"] == "1").sum())))
    w(pd.DataFrame(rows), "S06b_endpoint_type_summary.csv")

    # ---------------------------------------------------------------- S7/S8
    cit = pd.read_csv(f"{WORK}/nite_source_citations.csv", dtype=str).fillna("")
    w(cit, "S07_source_citations_per_evidence_unit.csv")
    reg = pd.read_csv(f"{WORK}/nite_source_register.csv", dtype=str).fillna("")
    w(reg, "S07b_cited_source_register.csv")

    # STEP 5 audit: published human references vs. official NITE classification.
    a18 = pd.read_csv("/home/user/industryqsar/data/supplementary/hematotoxicity_v18/"
                      "dataset_A_human_inhalation_references.csv", dtype=str).fillna("")
    au = a18.merge(newset, left_on="CAS", right_on="cas", how="left").fillna("")
    au = au.merge(roles[["substance_id", "evidence_tier", "all_tiers_present",
                         "nite_blood_target_terms", "hazard_classes"] + ET],
                  left_on="nite_substance_id", right_on="substance_id", how="left").fillna("")
    au["nite_corroboration"] = au.apply(
        lambda r: "not_in_NITE_blood_system_set" if r.evidence_tier == ""
        else ("corroborated_human_inhalation" if r.evidence_tier == "A_human_inhalation"
              else "corroborated_human_inhalation_likely" if r.evidence_tier == "B_human_inhalation_likely"
              else "corroborated_human_route_unclear" if r.evidence_tier == "C_human_route_unclear"
              else "official_blood_classification_animal_or_unresolved_basis"), axis=1)
    au = au[["reference_id", "chemical", "CAS", "SMILES", "InChIKey", "Evidence_level",
             "endpoint_class", "endpoint_reported", "route_basis", "reference_use",
             "toxicity_source_urls", "limitations", "nite_substance_id", "evidence_tier",
             "all_tiers_present", "nite_blood_target_terms", "hazard_classes",
             "nite_corroboration"] + ET]
    w(au, "S08_published_human_reference_audit.csv")

    # ---------------------------------------------------------------- S9
    rules = pd.DataFrame([
        dict(rule_id="R01", scope="official hazard reference",
             criterion="NITE Japan-GHS STOT-SE or STOT-RE Category 1 or 2 naming blood, blood "
                       "system, bone marrow, hematopoietic system or hematopoietic organ as a "
                       "target organ",
             decision="include as official_hematotoxic_hazard_reference",
             rationale="official government hazard classification; route- and species-agnostic"),
        dict(rule_id="R02", scope="official hazard reference",
             criterion="only 'blood coagulation system' is named among blood-related targets",
             decision="separate as coagulation_endpoint_outside_type1_3",
             rationale="haemostatic toxicity is mechanistically distinct from haemoglobin "
                       "dysfunction, erythrocyte damage and marrow/count suppression, and is "
                       "outside the Type 1-3 framework of this study"),
        dict(rule_id="R03", scope="official hazard reference",
             criterion="only a lymphoid organ (spleen, lymph node, lymphatic or "
                       "reticuloendothelial system) or 'blood vessels' is named",
             decision="exclude from the blood-system set",
             rationale="lymphoid and vascular targets are not erythroid/myeloid endpoints; "
                       "'blood vessels' is a vascular, not a haematological, target"),
        dict(rule_id="R04", scope="evidence species",
             criterion="a human subject term and a hematotoxicity endpoint term occur in the "
                       "same evidence unit",
             decision="assign human evidence basis for that unit",
             rationale="species must be attributed per evidence unit; human and animal findings "
                       "routinely appear in adjacent sentences of one rationale"),
        dict(rule_id="R05", scope="exposure route",
             criterion="an explicit inhalation word occurs in the same evidence unit as the "
                       "endpoint",
             decision="assign inhalation route basis",
             rationale="route mention anywhere in the rationale is not evidence that the "
                       "hematotoxic finding came from an inhalation study"),
        dict(rule_id="R06", scope="exposure route",
             criterion="exposure is quantified only as ppm or mg/m3 with no explicit inhalation "
                       "word, and no feeding/diet wording is present",
             decision="assign route_not_specified_air_unit_only (not inhalation)",
             rationale="an airborne concentration unit alone is weaker than a stated route"),
        dict(rule_id="R07", scope="exposure route",
             criterion="dose is given in ppm together with feeding, diet, fed or chow wording",
             decision="assign oral_dietary_concentration_inferred",
             rationale="NITE uses ppm for dietary concentration in feeding studies; reading it "
                       "as an airborne concentration misattributes feeding studies to inhalation"),
        dict(rule_id="R08", scope="endpoint type",
             criterion="a Type 3 term is present but every supporting unit carries only "
                       "compensatory wording (reticulocytosis, extramedullary haematopoiesis, "
                       "erythroid hyperplasia) with no direct marrow-injury wording",
             decision="withhold Type 3; retain Type 2",
             rationale="regenerative erythropoiesis secondary to peripheral red-cell "
                       "destruction is not direct bone-marrow toxicity"),
        dict(rule_id="R09", scope="structural domain",
             criterion="no carbon atom, or a disconnected multi-component SMILES",
             decision="retain in the source population; exclude from organic structure-based "
                       "screening",
             rationale="the screening method is defined on single-component organic molecules"),
        dict(rule_id="R10", scope="analysis-grade reference",
             criterion="a human- or animal-route-specific or mechanism-specific claim is to be "
                       "used as an analysis reference",
             decision="require independent primary-source verification before use",
             rationale="NITE rationale text cites authoritative secondary compilations rather "
                       "than primary studies for the great majority of blood-system entries, so "
                       "it establishes official classification but not primary verification"),
        dict(rule_id="R11", scope="labelling",
             criterion="any substance in this build",
             decision="no confirmed positive hematotoxicity label is assigned",
             rationale="absence of toxicity data is not evidence of absence; no independent "
                       "primary verification was completed in v0.28"),
    ])
    w(rules, "S09_inclusion_exclusion_hold_rules.csv")

    # ---------------------------------------------------------------- join layer
    if s3 is not None:
        st = s3.groupby("substance_id").agg(
            structure_status=("structure_status", "first"),
            structural_scope=("structural_scope", "first"),
            smiles=("smiles", "first"), pubchem_inchikey=("pubchem_inchikey", "first"),
            recomputed_inchikey=("recomputed_inchikey", "first"),
            formula=("formula", "first"), exclusion_reason=("exclusion_reason", "first")
        ).reset_index()
    else:
        st = pd.DataFrame(columns=["substance_id", "structure_status", "structural_scope",
                                   "smiles", "pubchem_inchikey", "recomputed_inchikey",
                                   "formula", "exclusion_reason"])

    layer = roles.merge(st, on="substance_id", how="left").fillna("")

    def assign_role(r):
        if r.nite_coagulation_only == "1":
            return "coagulation_endpoint_outside_type1_3"
        if r.structural_scope == "outside_organic_structural_domain":
            return "official_hazard_reference_outside_structural_domain"
        if r.structural_scope == "structure_unresolved_hold":
            return "hold_structure_unresolved"
        return {
            "A_human_inhalation": "human_inhalation_candidate_pending_primary_verification",
            "B_human_inhalation_likely": "human_occupational_extended_candidate_pending_verification",
            "C_human_route_unclear": "hold_human_evidence_route_unclear",
            "D_animal_inhalation": "animal_inhalation_support_provisional",
            "E_animal_other_route": "official_hazard_reference_animal_non_inhalation",
            "F_endpoint_only": "official_hazard_reference_species_route_unresolved",
            "G_no_endpoint_text": "official_hazard_reference_no_endpoint_in_text",
        }.get(r.evidence_tier, "hold_unclassified")

    layer["dataset_A_role_v028"] = layer.apply(assign_role, axis=1)
    layer["final_label"] = ""
    layer["verification_state"] = "no_independent_primary_verification_in_v028"
    layer["label_note"] = ("official NITE blood-system hazard classification reproduced from the "
                           "current official bulk download; evidence species, route and endpoint "
                           "type extracted from verbatim rationale text; NOT a confirmed positive "
                           "hematotoxicity label")
    cols = (["substance_id", "cas_all", "name", "dataset_A_role_v028", "evidence_tier",
             "all_tiers_present", "final_label", "verification_state",
             "nite_blood_target_terms", "nite_marrow_or_hematopoietic_target",
             "nite_coagulation_only", "hazard_classes", "classification_years"]
            + ET + ["type3_assignment_after_compensatory_review"] if False else None)
    layer = layer.merge(s6[["substance_id", "type3_assignment_after_compensatory_review"]],
                        on="substance_id", how="left").fillna("")
    layer = layer.rename(columns={"cas_all": "cas", "name": "substance_name"})
    w(layer, "S10_dataset_A_v028_join_layer.csv")

    print("\n=== Dataset A role assignment (v0.28 join layer) ===")
    print(layer.dataset_A_role_v028.value_counts().to_string())
    return layer


if __name__ == "__main__":
    main()
