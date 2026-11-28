"""
v0.28 — manually adjudicated review records and the gap register.

Everything in this module was read by a human reviewer in this work session and
is recorded with the reasoning. It is deliberately separate from the automated
extraction: automated output carries
review_state="extracted_pending_expert_confirmation", whereas rows here carry
an explicit reviewer judgement and the text that justified it.

Nothing here assigns a confirmed positive hematotoxicity label. Several records
DOWNGRADE or qualify what the NITE rationale asserts.
"""

import pandas as pd

OUT = "/home/user/v028/tables"

# ---------------------------------------------------------------------------
# S08b - manual adjudication of selected human-inhalation candidates against
# located primary literature (PubMed searches recorded in
# work/pubmed_primary_locators.csv).
# ---------------------------------------------------------------------------
ADJUDICATIONS = [
    dict(
        cas="10102-43-9", substance_name="Nitrogen monoxide (nitric oxide)",
        v028_tier="A_human_inhalation",
        nite_assertion="15-minute single inhalation exposure in volunteers; significant increase "
                       "in blood methemoglobin at >=15 ppm (DFGOT 2014)",
        endpoint_type="Type 1 (haemoglobin functional impairment)",
        primary_literature_located="PMID 42128729 (methemoglobin formation reflects systemic NO "
                                   "uptake); PMID 41823202 (methemoglobin and NO2 levels during "
                                   "inhaled NO therapy); PMID 41853735 (transient neonatal "
                                   "cyanosis exacerbated by inhaled NO)",
        reviewer_judgement="route_and_endpoint_supported_but_exposure_context_is_therapeutic",
        reviewer_note="Human inhalation route and the methemoglobin endpoint are well supported, "
                      "and the dose-dependence is established. However the accessible primary "
                      "literature is overwhelmingly THERAPEUTIC inhaled nitric oxide in neonates "
                      "and ARDS patients, not occupational or industrial exposure. The NITE basis "
                      "is a 15 ppm volunteer study reported only through DFGOT secondary "
                      "documentation, which was not retrieved. Mechanistically relevant to "
                      "semiconductor process gases, but the exposure scenario differs from "
                      "workplace inhalation.",
        recommended_role="human_occupational_extended_candidate_pending_verification",
        remaining_work="retrieve DFGOT (2014) nitric oxide documentation and the underlying "
                       "volunteer study; confirm whether any occupational exposure study exists"),
    dict(
        cas="110-80-5", substance_name="2-Ethoxyethanol (ethylene glycol monoethyl ether)",
        v028_tier="A_human_inhalation",
        nite_assertion="multiple reports of occupational inhalation exposure with effects on the "
                       "haemal system and haematopoietic tissue: anaemia, decreased haemoglobin "
                       "and haematocrit, granulocytopenia, myelosuppression (CICAD 67, 2010)",
        endpoint_type="Type 2 (erythrocyte damage / anaemia) + Type 3 (counts / marrow)",
        primary_literature_located="PMID 15540629 (health effects of EGEE exposure in female "
                                   "workers, Ind Health 2004); PMID 26325043 (haematological "
                                   "changes from 2-methoxyethanol and 2-ethoxyethanol, 2015); "
                                   "PMID 17690522 (haematological follow-up of an intervention "
                                   "adding rubber-glove wearing, J Occup Health 2007); "
                                   "PMID 6667035 (bone marrow injury in lithographers exposed to "
                                   "glycol ethers AND organic solvents, 1983)",
        reviewer_judgement="human_evidence_supported_but_dermal_contribution_indicated",
        reviewer_note="Genuine human occupational haematological evidence exists in primary "
                      "journals. Two qualifications are decisive for route attribution: (1) the "
                      "intervention study achieved haematological improvement by adding RUBBER "
                      "GLOVES, which directly implies a substantial dermal exposure contribution; "
                      "(2) the bone-marrow-injury report concerns lithographers exposed to glycol "
                      "ethers together with other organic solvents, so single-substance "
                      "attribution is not possible. This mirrors the existing treatment of "
                      "2-methoxyethanol and 2-ethoxyethyl acetate in this study.",
        recommended_role="human_occupational_extended_candidate_pending_verification",
        remaining_work="full-text review of PMID 15540629 and 26325043 for exposure measurement, "
                       "control group and dermal co-exposure; do NOT promote to human inhalation "
                       "core while the glove-intervention finding stands"),
    dict(
        cas="95-53-4", substance_name="o-Toluidine",
        v028_tier="A_human_inhalation",
        nite_assertion="methemoglobinaemia developed in 20 of 81 workers exposed by repeated "
                       "inhalation at a production factory (DFGOT vol. 3, 1992)",
        endpoint_type="Type 1 (haemoglobin functional impairment)",
        primary_literature_located="PubMed hits for o-toluidine + methemoglobin are dominated by "
                                   "prilocaine / EMLA-induced methaemoglobinaemia, in which "
                                   "o-toluidine is the drug METABOLITE (PMID 23530020, 16723054, "
                                   "14992088, 23859109); no primary occupational inhalation "
                                   "cohort was retrieved",
        endpoint_note="",
        reviewer_judgement="occupational_primary_study_not_located_mechanism_supported",
        reviewer_note="The Type 1 mechanism is strongly supported in humans, but almost entirely "
                      "through pharmaceutical exposure to prilocaine, which is metabolised to "
                      "o-toluidine. That is systemic drug exposure, not inhalation. The "
                      "occupational 20/81 observation traces to DFG MAK documentation from 1992 "
                      "which is not indexed in PubMed and was not retrieved, so the occupational "
                      "inhalation claim remains unverified at primary level.",
        recommended_role="hold_pending_retrieval_of_DFGOT_vol3_1992",
        remaining_work="obtain DFG MAK/DFGOT vol. 3 (1992) o-toluidine documentation and identify "
                       "the underlying factory study"),
    dict(
        cas="78-87-5", substance_name="1,2-Dichloropropane",
        v028_tier="A_human_inhalation",
        nite_assertion="epidemiological findings in humans; chronic inhalation exposure causes "
                       "haemolytic anaemia and liver and renal dysfunction (NITE/CERI/NEDO Initial "
                       "Risk Assessment Report, 2005)",
        endpoint_type="Type 2 (erythrocyte damage / haemolytic anaemia)",
        primary_literature_located="PMID 4063220 (toxicity in man due to stain removers containing "
                                   "1,2-dichloropropane, Br J Ind Med 1985); PMID 37549028 (acute "
                                   "poisoning due to INGESTION of rubber cement, 2023); "
                                   "PMID 23808637 and 21070183 (rat inhalation toxicity and "
                                   "carcinogenicity studies)",
        reviewer_judgement="nite_summary_more_confident_than_primary_literature_supports",
        reviewer_note="The human reports concern exposure to MIXED consumer products (stain "
                      "removers, rubber cement) rather than to the single substance, and the "
                      "clearest acute case is oral ingestion. Clean inhalation data are animal. "
                      "The NITE phrase 'chronic inhalation exposure causes haemolytic anaemia' is "
                      "therefore not reproducible from the accessible primary literature as a "
                      "single-substance human inhalation finding. The existing v0.18 assignment of "
                      "this substance to 3_uncertain / sensitivity_only should be RETAINED.",
        recommended_role="hold_human_evidence_mixed_product_and_route",
        remaining_work="full text of PMID 4063220 for product composition and route; retain as "
                       "sensitivity-only reference"),
    dict(
        cas="58-89-9", substance_name="Lindane (1,2,3,4,5,6-hexachlorocyclohexane)",
        v028_tier="A_human_inhalation",
        nite_assertion="aplastic anaemia and agranulocytosis from chronic inhalation of this "
                       "substance are reported (ACGIH 7th, 2001)",
        endpoint_type="Type 3 (blood cell counts / marrow and haematopoietic injury)",
        primary_literature_located="PMID 1700687 (lindane (Kwell)-induced aplastic anaemia, Arch "
                                   "Intern Med 1990 - TOPICAL scabicide); PMID 7512682 (lindane "
                                   "exposure and aplastic anaemia, Lancet 1994); PMID 1690760 "
                                   "(aplastic anaemia associated with organochlorine pesticide, "
                                   "1990); PMID 7512355 (lindane haematotoxicity confirmed by in "
                                   "vitro tests on human and rat progenitors, 1994); PMID 2454526 "
                                   "(DIC in fatal lindane poisoning)",
        reviewer_judgement="human_type3_evidence_strong_but_route_predominantly_dermal_or_oral",
        reviewer_note="Human marrow toxicity is well documented and is mechanistically supported "
                      "by in vitro human progenitor assays, which is unusually strong corroboration "
                      "for a Type 3 assignment. The exposure route in the primary case literature "
                      "is however predominantly DERMAL (Kwell/scabies treatment) or systemic "
                      "poisoning, not occupational inhalation. The ACGIH 'chronic inhalation' "
                      "wording is a secondary summary and the underlying inhalation study was not "
                      "located.",
        recommended_role="hold_for_inhalation_use_retain_as_human_type3_reference",
        remaining_work="ACGIH 7th edition documentation for the inhalation claim; full text of "
                       "PMID 7512682 and 7512355"),
]

# ---------------------------------------------------------------------------
# S11 - gap register. Work the protocol asks for that this build could NOT do,
# and why. Reported so that no step is recorded as complete on missing data.
# ---------------------------------------------------------------------------
GAPS = [
    dict(gap_id="G01", protocol_step="STEP 1",
         item="hematotoxicity_v27_supplement.zip",
         status="not_available_to_this_build",
         consequence="S04 (Dataset A, 349 records), S07 (Dataset B, 8,110 records) and S08 "
                     "(screening candidates, 2,519 records) could not be regenerated or updated "
                     "in place. v0.28 therefore supplies a CAS-keyed join layer "
                     "(S10_dataset_A_v028_join_layer.csv) instead of a replacement Dataset A.",
         resolution="upload hematotoxicity_v27_supplement.zip, then merge the join layer on CAS"),
    dict(gap_id="G02", protocol_step="STEP 1",
         item="v0.27 file hashes (S01_input_manifest.csv from the local ZIP)",
         status="not_verifiable",
         consequence="The 22 v0.27 output hashes and 18 v0.26 archive hashes recorded in the "
                     "public manifest could not be re-checked, because the files they describe "
                     "are in the un-uploaded ZIP. v0.28 records hashes only for the inputs it "
                     "actually read.",
         resolution="run validate_v28.py against the local ZIP once uploaded"),
    dict(gap_id="G03", protocol_step="STEP 2",
         item="identification of the specific 323 un-reviewed evidence rows",
         status="superseded_by_full_re_derivation",
         consequence="The 94-reviewed / 323-pending split lives in "
                     "S05_NITE_evidence_review_417.csv inside the local ZIP and could not be "
                     "read. Instead of reviewing a subset, v0.28 re-derived and segmented the "
                     "rationale text for ALL 749 blood-system classification records (3,634 "
                     "evidence units), which covers the 417 structure-ready rows and the "
                     "remainder. The row-level mapping to the previous 94/323 labels is still "
                     "open.",
         resolution="join S04/S05 to the local S05_NITE_evidence_review_417.csv on "
                    "(substance_id, stot_class) to recover the prior review-depth flags"),
    dict(gap_id="G04", protocol_step="STEP 5",
         item="independent primary-source verification of analysis-grade references",
         status="partially_started_not_complete",
         consequence="Primary literature was LOCATED for 5 selected substances and adjudicated "
                     "(S08b). No full-text verification of exposure measurement, control group, "
                     "statistical significance or single-substance attribution was completed for "
                     "any substance. Independent primary verifications completed in v0.28: 0. "
                     "New confirmed positive labels: 0.",
         resolution="full-text review per the STEP 5 checklist, recorded one row per study"),
    dict(gap_id="G05", protocol_step="STEP 5",
         item="secondary compilations cited by NITE (ACGIH, DFGOT/DFG MAK, PATTY, CICAD, EU-RAR)",
         status="not_retrieved",
         consequence="For the great majority of blood-system entries NITE cites an authoritative "
                     "secondary compilation rather than a primary study: of 3,007 citation "
                     "instances only 249 point to a primary test report (NTP TR or an OECD TG "
                     "study). None of the 11 tier-A human-inhalation substances cites a primary "
                     "journal article. NITE classification therefore establishes official hazard "
                     "classification, NOT primary verification.",
         resolution="obtain the specific ACGIH / DFGOT / CICAD volumes named in "
                    "S07_source_citations_per_evidence_unit.csv for the substances actually used "
                    "as analysis references"),
    dict(gap_id="G06", protocol_step="STEP 6",
         item="EPA TRI listing version and per-substance listing basis for 28 TRI-only substances",
         status="not_addressed",
         consequence="Requires the local TRI source list captured at collection time; the "
                     "published repository holds only the programme URL.",
         resolution="upload the original TRI list export used at collection time"),
    dict(gap_id="G07", protocol_step="STEP 6",
         item="exact citation for 4 of the 249 semiconductor-core records",
         status="not_addressed",
         consequence="Requires the original chemical-use survey document and page references, "
                     "which are not in the public repository.",
         resolution="upload the chemical-use survey source"),
    dict(gap_id="G08", protocol_step="STEP 6",
         item="EPA CompTox CCD-Batch-Search raw export for the 328 newly queried substances",
         status="still_missing",
         consequence="v0.28 resolved structures independently from PubChem PUG-REST rather than "
                     "from the EPA export. The PubChem-based audit is NOT a substitute for the "
                     "frozen EPA-based S03: it uses a different registry, so counts differ "
                     "(390 single-component organic of 570 CAS here, versus 332 of 562 in the "
                     "EPA-based v0.27 snapshot). The two must not be conflated.",
         resolution="upload the original CCD-Batch-Search CSV; keep the EPA-based S03 as the "
                    "frozen structural audit of record"),
    dict(gap_id="G09", protocol_step="STEP 3",
         item="sentence-level segmentation of narrative (pre-FY2018) rationales",
         status="known_limitation",
         consequence="573 of 745 rationale units are unstructured prose and were segmented into "
                     "sentences. A study description spanning several sentences can have its "
                     "species, route and endpoint split across segments, which makes the "
                     "co-occurrence test CONSERVATIVE: it under-calls rather than over-calls. "
                     "Benzene is a documented example - its human occupational hematopoietic "
                     "evidence is reported with ppm values but without the word inhalation, so it "
                     "lands in tier B rather than tier A.",
         resolution="manual reading of the tier B and tier C units for any substance promoted to "
                    "an analysis-grade reference"),
    dict(gap_id="G10", protocol_step="STEP 4",
         item="mechanism versus observed-indicator distinction",
         status="partially_addressed",
         consequence="Type 1-3 assignments here reflect OBSERVED INDICATORS named in the "
                     "rationale text, not established mechanism of action. Target-organ "
                     "classification, observed indicator and mechanism are kept as separate "
                     "fields and must not be read as equivalent. The compensatory-response rule "
                     "(R08) withheld Type 3 for 27 substances whose only Type 3 wording was "
                     "regenerative erythropoiesis.",
         resolution="expert mechanistic review before the Type 1-3 framework is frozen"),
    dict(gap_id="G11", protocol_step="data provenance",
         item="NITE dataset drift between v0.24 collection and the 2026-11-28 download",
         status="quantified",
         consequence="The current official download yields 3,452 substances with STOT entries "
                     "(6,904 STOT rows), against 3,476 substances / 6,952 rows recorded at v0.24. "
                     "All 24 substances without rationale STOT rows carry '-' in both STOT columns, "
                     "so none can affect blood-system selection. All 562 published v0.24 CAS were "
                     "recovered. Three substances the v0.24 pipeline dropped were recovered: "
                     "Thiouracil (141-90-2 / 80275-68-9) and 6-acetyl-1,1,2,4,4,7-"
                     "hexamethyltetralin (21145-77-7 / 1506-02-1), both of which NITE records with "
                     "two CAS numbers in one cell, plus Chlorotrifluoroethane, whose CAS cell is "
                     "empty.",
         resolution="decide whether to adopt the two recovered multi-CAS substances; Thiouracil is "
                    "a blood-system STOT-RE Category 1 entry and thiouracils are an established "
                    "cause of agranulocytosis, so its omission is material"),
    dict(gap_id="G12", protocol_step="STEP 2 scope",
         item="'blood coagulation system' as a blood-system target organ",
         status="newly_identified_issue",
         consequence="5 of the published 562 CAS (estrone, 2,4-di-tert-butylphenol, chlormadinone "
                     "acetate, 4-sec-butyl-2,6-di-tert-butylphenol, indanofan) have 'blood "
                     "coagulation system' as their ONLY blood-related STOT target. Haemostatic "
                     "toxicity is outside the Type 1-3 framework, and for the two steroid hormones "
                     "the effect is a prothrombotic one, which is mechanistically opposite to "
                     "hematotoxicity. v0.28 separates them under rule R02.",
         resolution="confirm the decision to treat coagulation as a separate endpoint class, or "
                    "exclude these 5 substances from the official hematotoxic reference set"),
]


def main():
    adj = pd.DataFrame(ADJUDICATIONS)
    adj["review_state"] = "manually_adjudicated_in_v028"
    adj["new_final_label"] = ""
    adj.to_csv(f"{OUT}/S08b_manual_primary_literature_adjudication.csv", index=False)
    print(f"  S08b_manual_primary_literature_adjudication.csv       rows={len(adj)}")

    loc = "/home/user/v028/work/pubmed_primary_locators.csv"
    try:
        pm = pd.read_csv(loc, dtype=str).fillna("")
        pm.to_csv(f"{OUT}/S08c_pubmed_primary_locators.csv", index=False)
        print(f"  S08c_pubmed_primary_locators.csv                      rows={len(pm)}")
    except FileNotFoundError:
        print("  !! S08c skipped: pubmed locators not found")

    g = pd.DataFrame(GAPS)
    g.to_csv(f"{OUT}/S11_gap_register.csv", index=False)
    print(f"  S11_gap_register.csv                                  rows={len(g)}")

    print("\n=== reviewer judgements on the 5 adjudicated substances ===")
    for _, r in adj.iterrows():
        print(f"  {r.cas:12s} {r.substance_name[:46]:47s} -> {r.reviewer_judgement}")


if __name__ == "__main__":
    main()
