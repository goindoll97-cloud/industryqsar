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
         status="RESOLVED_archive_supplied_and_verified",
         consequence="The archive was supplied and verified: its SHA-256 matches the value "
                     "recorded in the public v0.27 manifest, and all 31 recorded internal file "
                     "hashes match. Dataset A (349 records) has been merged with the v0.28 "
                     "evidence layer as S04_Dataset_A_349_v028.csv; 335 of 349 records matched an "
                     "official NITE blood-system entry and 14 did not. The v0.27 final_label "
                     "column is preserved unchanged and remains empty in all 349 records.",
         resolution="closed"),
    dict(gap_id="G02", protocol_step="STEP 1",
         item="v0.27 file hashes (archive and internal files)",
         status="RESOLVED_all_hashes_match",
         consequence="Archive SHA-256 "
                     "52b329610a4e7448aefcd78f3e1f5ec282c01963fd6dc566539a9c172eb57d28 matches "
                     "the public manifest. All 31 recorded internal file hashes match, with no "
                     "mismatch, no missing file and no unrecorded extra file. The 18 v0.26 "
                     "archive hashes remain unchecked because hematotoxicity_v26.zip itself was "
                     "not supplied.",
         resolution="supply hematotoxicity_v26.zip if the v0.26 archive hashes must also be "
                    "re-verified"),
    dict(gap_id="G03", protocol_step="STEP 2",
         item="the 323 evidence rows v0.27 had not read in full",
         status="RESOLVED_all_323_read",
         consequence="The 417 structure-ready rows were recovered from the archive and the "
                     "94-reviewed / 323-pending split reproduced exactly (323 = 295 "
                     "automatic_cues_only + 28 excerpt_screen). All 323 were matched to the "
                     "v0.28 full-text reading and read. The result: 169 animal endpoint with "
                     "other or unresolved route, 89 human endpoint with route not isolated, 44 "
                     "endpoint without resolved species, 19 with no endpoint term at all, and "
                     "only 2 with an animal inhalation endpoint in a single evidence unit. ZERO "
                     "new human inhalation evidence rows. The prior automatic bucketing is "
                     "vindicated: no row bucketed no_inhalation_text_cue became an inhalation "
                     "finding. Recorded in S05c_v27_evidence_review_reconciliation.csv.",
         resolution="closed; the 2 new animal inhalation rows are candidates for the animal "
                    "inhalation support set and need summary-level confirmation"),
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
         status="BOUNDED_negligible_analytical_impact",
         consequence="The historical TRI list export is still missing, and EPA's current "
                     "machine-readable chemical list is served from guideme.epa.gov, which this "
                     "environment does not reach. The gap is now bounded instead: of the 28 "
                     "TRI-only substances only 9 are in the 2,519 screening candidate set, i.e. "
                     "0.36 per cent of it. All 9 are agricultural pesticides or herbicides "
                     "(alachlor, benfluralin, oryzalin, triallate, methyl parathion, dichlorvos, "
                     "propanil, 2,4,6-trichlorophenol, chlorimuron ethyl), none is flagged as a "
                     "TRI inhalation candidate, none carries a human flag, and none is "
                     "semiconductor-related. Recorded in "
                     "S07c_dataset_B_provenance_resolution.csv.",
         resolution="optional: upload the original TRI list export. The residual uncertainty can "
                    "instead be stated quantitatively as affecting 9 of 2,519 candidates, all "
                    "outside the semiconductor-relevant scope"),
    dict(gap_id="G07", protocol_step="STEP 6",
         item="exact citation for 4 of the 249 semiconductor-core records",
         status="BOUNDED_one_record_affected_outside_structural_domain",
         consequence="Of the 4 records whose process evidence is 'usage_survey_citation_pending', "
                     "3 also carry an independent peer-reviewed source (Lim2021, "
                     "doi:10.1007/s13273-021-00139-4; methanol additionally Taiwan2024), so for "
                     "those the pending citation is supplementary rather than load-bearing. Only "
                     "ONE record depends solely on the uncited survey table: CAS 25322-68-3 "
                     "(alpha-hydro-omega-hydroxy polymer), which is already classified "
                     "outside_domain and is therefore excluded from organic structure-based "
                     "screening in any case. Analytical impact: none.",
         resolution="optional: supply the Korean chemical-use survey document and its Table 6 "
                    "page reference, needed only for completeness of the population source "
                    "register"),
    dict(gap_id="G08", protocol_step="STEP 6",
         item="EPA CompTox CCD-Batch-Search raw export for the 328 newly queried substances",
         status="PARTLY_ADDRESSED_cross_registry_comparison_performed",
         consequence="The raw EPA export is still missing, but the archive's EPA-based audit "
                     "(S03_structure_audit_562.csv, carrying EPA_DTXSID, EPA_SMILES and "
                     "EPA_InChIKey) was compared per CAS against the independent PubChem audit in "
                     "S03c_structure_audit_cross_registry.csv. Of 390 single-component organic "
                     "substances, 331 keys match exactly, 42 match on connectivity only, 13 are "
                     "not comparable and 4 conflict. The 42 connectivity-only cases are a "
                     "SYSTEMATIC ARTEFACT, not a structural disagreement: EPA stored "
                     "NON-STANDARD InChIKeys (second block ...NA-N) against standard keys "
                     "(...SA-N), with identical connectivity in every case. Only 4 genuine "
                     "organic identity conflicts remain: CAS 1929-77-7 (vernolate; the PubChem "
                     "hit cid 25246088 is a charged species and is wrong, EPA is correct), "
                     "54749-90-5 (chlorozotocin), 5700-39-0 (tris(2-methoxyethoxy)silane "
                     "derivative) and 79-57-2 (oxytetracycline, likely a tautomer or protonation "
                     "difference). 23 of the 24 overall conflicts are inorganic salts and oxides, "
                     "where InChI conventions differ between registries and which are outside the "
                     "structural domain regardless.",
         resolution="the 42 non-standard-InChI holds can likely be released after confirming the "
                    "InChI standardisation flag; the 4 organic conflicts need manual identity "
                    "confirmation with EPA CompTox as the registry of record"),
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
                     "(R08) withheld Type 3 for 23 substances whose only Type 3 wording was "
                     "regenerative erythropoiesis. CORRECTION: an earlier draft of this entry "
                     "said 27, a stale figure from before the Type 3 logic was split into "
                     "marrow-injury / peripheral-counts-only / compensatory-only; the correct "
                     "count in the 566-substance official set is 23, and 22 within the "
                     "structure-ready subset. 'type3_marrow_injury_supported' (149 of 566) means "
                     "marrow WORDING present with no compensatory cue in the same unit; it is "
                     "NOT a confirmed finding of direct marrow damage.",
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
    dict(gap_id="G13", protocol_step="STEP 2 / STEP 3 outcome",
         item="what the 323 previously un-read evidence rows actually contain",
         status="answered",
         consequence="Reading all 323 in full yields only 2 rows with an animal inhalation "
                     "endpoint in a single evidence unit and ZERO new human inhalation rows. The "
                     "remainder is 169 animal findings by another or unresolved route, 89 human "
                     "findings whose route cannot be isolated, 44 endpoints without a resolved "
                     "species and 19 rows with no endpoint term at all. The practical conclusion "
                     "is that the route-specific evidence in the official NITE blood-system "
                     "rationales was already captured by the v0.25-v0.27 prioritised review; the "
                     "residual 323 rows do not change the route-specific reference sets.",
         resolution="summary-level confirmation of the 2 new animal inhalation rows; no further "
                    "bulk review of this corpus is warranted"),
    dict(gap_id="G14", protocol_step="structural audit",
         item="40 'same_connectivity_only_hold' structure records in the v0.27 audit",
         status="RESOLVED_39_released_1_retained",
         consequence="All 40 holds were adjudicated against the InChIKey structure "
                     "(skeleton-layers-flag-version-protonation). Every one of the 40 shows the "
                     "EPA key carrying the non-standard InChI flag 'N' where the standard key "
                     "carries 'S'. For 39 of them the skeleton block, remaining-layers hash, "
                     "version and protonation are all identical AND an independent standard "
                     "InChIKey recomputed from the EPA SMILES with RDKit 2025.09.4 reproduces "
                     "the standard key exactly. 37 holds met that test AND the structural-scope "
                     "test and were released. 3 are retained: CAS 67375-30-8, a chiral "
                     "pyrethroid whose remaining-layers hash genuinely differs, and "
                     "chlorpheniramine maleate (113-92-8) and cyclophosphamide monohydrate "
                     "(6055-19-2), which are 2-fragment salts/hydrates. CORRECTION: the first "
                     "v0.28 run released 39 because it tested only the InChI standardisation "
                     "question and failed to re-apply rule R09 (single-component organic scope) "
                     "before admitting a substance; the independent v0.29 audit caught this and "
                     "its count of 37 released / 3 retained is correct. Resolving a key "
                     "reconciliation says two keys describe the same substance, not that the "
                     "substance is inside the structural domain. Structure-ready references rise "
                     "from 332 to 369. Per hematotoxicity type: Type 1 116 (+1), Type 2 282 "
                     "(+27), Type 3 182 (+13), coagulation 69 (+8). Two tier-A human-inhalation "
                     "substances enter structural scope for the first time: lindane (58-89-9) "
                     "and 1,2-dichloropropane (78-87-5), both of which carry reviewer caveats "
                     "from S08b and are not thereby promoted to analysis-grade references. The "
                     "37 still need EPA-source, identity and industrial-scope checks before "
                     "final admission. Recorded in S03d_G14_structure_hold_adjudication.csv and "
                     "S03e_structure_ready_reference_set.csv.",
         resolution="the standardisation question is closed; identity and scope confirmation of "
                    "the 37 remains open. Future structural work should compute standard "
                    "InChIKeys throughout and always re-apply the scope test after any key "
                    "reconciliation"),
    dict(gap_id="G15", protocol_step="method development readiness",
         item="supervised QSAR classification is not supportable on this dataset",
         status="documented_constraint",
         consequence="There is no negative class: no substance is labelled non-hematotoxic, and "
                     "the protocol forbids treating absence of toxicity data as a negative. "
                     "There is also no confirmed positive label: final_label is empty in all 349 "
                     "Dataset A records and all 566 official-set records, and verification_state "
                     "is 'no_independent_primary_verification_in_v028' throughout. Human "
                     "inhalation backing is very thin even among structure-ready references "
                     "(Type 1: 4, Type 2: 5, Type 3: 2 substances). A supervised classifier "
                     "therefore has neither a trainable label column nor a basis for AUROC, "
                     "specificity or precision. The public repository additionally carries no "
                     "SMILES or InChIKey in the v0.28 index, so structure-based work requires "
                     "the local archive.",
         resolution="the planned experiment is retrieval-based, not classification-based: "
                    "Recall@Top-1/5/10 per hematotoxicity type with compound-out and "
                    "structural-group-out splits against the same industrial background, using "
                    "maximum Tanimoto similarity as the baseline. That design needs no negative "
                    "class and is now supported by the per-type reference sets in S06c"),
    dict(gap_id="G16", protocol_step="chemical identity",
         item="PubChem lookups selected the first returned record",
         status="known_defect_recorded",
         consequence="resolve_structures.py takes Properties[0] from each PUG-REST response, so "
                     "a CAS with several PubChem hits can resolve to the wrong record. The "
                     "vernolate case (CAS 1929-77-7, cid 25246088, a charged species) is a "
                     "confirmed instance. Flagged by the independent v0.29 audit. The "
                     "PubChem audit is a cross-check only and EPA CompTox is the registry of "
                     "record, so no reference set depends on it, but the 4 organic key "
                     "conflicts must be resolved by hand.",
         resolution="resolve multi-hit CAS by checking CAS synonyms, registry numbers and "
                    "structure identity rather than taking the first hit"),
    dict(gap_id="G17", protocol_step="STEP 5",
         item="methylene bis(thiocyanate) (6317-18-6) human methemoglobinaemia case",
         status="hold_recommended_by_v029_audit",
         consequence="The v0.29 audit found that 4-DMAP, a methaemoglobin-forming antidote, was "
                     "administered before the first MetHb measurement in the primary case, so "
                     "the reported 51 per cent is confounded by treatment. This substance is "
                     "REF007, one of the nine 1_core human references in the published v0.18 "
                     "Dataset A. Separately, the nitrobenzene primary report infers the "
                     "inhalation route from occupational history rather than measurement.",
         resolution="re-adjudicate REF007 before it is used as an analysis-grade human reference; "
                    "record the treatment confounding in its limitations field"),
    dict(gap_id="G18", protocol_step="cross-registry comparison",
         item="the '42 organic connectivity-only' figure was loosely framed",
         status="corrected",
         consequence="An earlier draft described 42 organic connectivity-only cases as a single "
                     "releasable artefact class. The v0.29 audit decomposed them as 38 prior "
                     "holds, 2 already structure-ready and 2 with a CAS mismatch, and warned "
                     "against releasing all 42 as a block. Only the 40 records actually carrying "
                     "the v0.27 same_connectivity_only_hold status were adjudicated, and of "
                     "those 37 were released. No blanket release of 42 was performed.",
         resolution="closed; the adjudicated set is the 40 holds, not the 42 connectivity-only "
                    "comparison rows"),
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
