# v0.28 — Data dictionary

Version: `v0.28-evidence-rederivation`
Build date: 2026-11-28
RDKit: 2025.09.4 · pandas: 3.0.5 · Python: 3.13

## 0. Conventions

| Convention | Meaning |
|---|---|
| Empty string | Not reported in the source. Never imputed, never replaced by a default. |
| `not_specified` | The source text exists but does not state the attribute. |
| `*_pending_*`, `*_hold_*` | An open decision, not a negative finding. |
| `review_state = extracted_pending_expert_confirmation` | Produced by automated extraction from verbatim text. **Not** a reviewed record. |
| `review_state = manually_adjudicated_in_v028` | Read and judged by a human reviewer in this build; reasoning recorded. |
| `final_label` | Confirmed hematotoxicity label. **Empty in every row of this release.** |
| Units | Exposure concentrations are quoted verbatim from the source (ppm, mg/m³, mg/kg/day). No unit conversion is performed. `ppm` is ambiguous in the source: see `exposure_route_basis = oral_dietary_concentration_inferred`. |

**Absence of toxicity data is never encoded as a negative label.** No substance in this release is marked non-hematotoxic.

---

## 1. S01_source_register.csv

One row per data source actually read by this build.

| Column | Type | Description |
|---|---|---|
| `source_id` | string | Stable key referenced by `S01_input_manifest.csv` |
| `organisation` | string | Publishing body |
| `dataset` | string | Dataset or file name as published |
| `url` | string | Official access URL |
| `file` | string | Local file name |
| `access_date` | date | ISO date the file was retrieved |
| `role` | string | What the source is used for in this study |
| `notes` | string | Record counts and caveats |

## 2. S01_input_manifest.csv

| Column | Type | Description |
|---|---|---|
| `file` | string | Input file name |
| `location` | string | Where it came from (official download / public repository) |
| `bytes` | integer | File size |
| `sha256` | string | SHA-256 of the exact bytes read |
| `access_date` | date | Retrieval date |
| `source_id` | string | Foreign key to `S01_source_register.csv` |

## 3. S02_NITE_official_blood_system_set.csv — 566 rows

One row per NITE substance entry carrying a blood-system STOT classification.

| Column | Type | Description |
|---|---|---|
| `nite_substance_id` | string | Official NITE substance ID (e.g. `m-nite-71-43-2`) |
| `cas` | string | CAS number(s); `; `-separated where NITE records more than one |
| `substance_name` | string | Substance name as published by NITE |
| `stot_classes` | string | `STOT-SE`, `STOT-RE`, or both |
| `blood_system_categories` | string | GHS category/categories (1, 2) carrying the blood-system target |
| `blood_system_target_terms` | string | The blood-system target organ terms NITE names: `blood`, `blood system`, `bone marrow`, `hematopoietic system`, `hematopoietic organ` |
| `marrow_or_hematopoietic_target` | 0/1 | Target is bone marrow, hematopoietic system or hematopoietic organ |
| `coagulation_only_target` | 0/1 | The only blood-related target is `blood coagulation system` (rule R02) |
| `nite_classification_years` | string | NITE fiscal year(s) of classification |
| `nite_detail_url` | string | Official NITE detail page |

## 4. S02b_NITE_v024_index_reconciliation.csv — 570 rows

Reconciliation of this re-derivation against the published v0.24 562-CAS index.

| Column | Type | Description |
|---|---|---|
| `cas` | string | CAS number |
| `nite_substance_id`, `substance_name` | string | Empty when the CAS is in the v0.24 index only |
| `in_v028_rederivation` | 0/1 | Present in this build |
| `in_published_v024_index` | 0/1 | Present in the published v0.24 index |
| `reconciliation_status` | enum | `in_both` (562) · `v028_only_multi_cas_cell_member` (4, members of NITE cells holding two CAS numbers) · `v024_only` (0) |

## 5. S03_structure_audit.csv — 570 rows

Independent PubChem + RDKit structure audit, one row per CAS.

| Column | Type | Description |
|---|---|---|
| `substance_id`, `nite_name`, `cas` | string | Identity |
| `pubchem_cid`, `pubchem_title` | string | PubChem record |
| `smiles` | string | SMILES as returned by PubChem PUG-REST |
| `pubchem_inchikey` | string | Registry InChIKey |
| `recomputed_inchikey` | string | InChIKey recomputed from the SMILES with RDKit 2025.09.4 |
| `formula`, `mw` | string | Molecular formula, molecular weight |
| `n_fragments` | integer | Disconnected components in the SMILES |
| `structure_status` | enum | `ok_single_organic` (390) · `inorganic_or_no_carbon` (118) · `multicomponent` (52) · `not_found` (9) · `unparsable` (1) · also defined: `connectivity_only`, `key_mismatch`, `no_cas` |
| `structural_scope` | enum | `in_organic_single_component_scope` (390) · `outside_organic_structural_domain` (170) · `structure_unresolved_hold` (10) |
| `exclusion_reason` | string | Why a substance falls outside scope |
| `structure_note` | string | Free-text detail |

> **Not a replacement for the frozen EPA-based S03 of v0.27.** This audit queries PubChem, a different registry from EPA CompTox, so the counts are not comparable (390 of 570 here versus 332 of 562 in v0.27). The EPA-based audit remains the structural audit of record. See gap `G08`.

## 6. S04_NITE_classification_records_with_rationale.csv — 749 rows

One row per (substance × STOT-SE/RE) blood-system classification record, with the **verbatim** official rationale.

| Column | Type | Description |
|---|---|---|
| `nite_substance_id`, `cas`, `substance_name` | string | Identity |
| `stot_class` | enum | `STOT-SE` or `STOT-RE` |
| `blood_system_categories` | string | Category carrying the blood-system target |
| `blood_system_target_terms` | string | Blood-system target organ terms |
| `coagulation_only_target`, `marrow_or_hematopoietic_target` | 0/1 | See S02 |
| `lymphoid_target_terms` | string | Co-listed spleen / lymph node / lymphatic / reticuloendothelial targets (recorded, **not** treated as blood-system targets — rule R03) |
| `all_stot_target_organs` | string | Every target organ in the Category 1/2 classification |
| `nite_classification_verbatim` | string | The classification cell exactly as published |
| `nite_classification_year` | string | NITE fiscal year |
| `nite_rationale_verbatim` | string | **The complete official "Rationale for the classification" text.** Median length 1,204 characters; maximum 8,024 |

## 7. S05_evidence_units_species_route.csv — 3,634 rows

**STEP 3 deliverable.** One row per evidence unit (segment) of a rationale.

| Column | Type | Description |
|---|---|---|
| `substance_id`, `cas`, `substance_name`, `stot_class` | string | Identity |
| `rationale_section` | enum | `rationale` (172, the classifier's own reasoning — excluded from evidence tiering) · `evidence` (778, a numbered `[Evidence Data]` item) · `narrative` (2,684, a sentence of an unstructured rationale) |
| `evidence_unit_id` | string | `R`, `E<n>` or `S<n>` within the record |
| `evidence_species_basis` | enum | `human` (643) · `animal` (1,236) · `mixed_human_and_animal_in_segment` (162) · `not_specified` (1,593) |
| `human_cues` | string | Which human-subject cue types matched: `human`, `worker`, `patient_case`, `volunteer`, `epidemiology`, `person_narrative`, `accidental` |
| `animal_species` | string | Test species named. Reagent contexts ("anti-sheep red blood cell antibody") are stripped before matching |
| `exposure_route_basis` | enum | `inhalation` (263) · `oral` (892) · `dermal` (51) · `injection` (22) · `in_vitro` (2) · `read_across` (6) · `mixed_route_in_segment` (120) · `route_not_specified_air_unit_only` (55) · `oral_dietary_concentration_inferred` (1) · `route_not_specified` (2,222) |
| `route_cues` | string | Which route cues matched |
| `strong_inhalation_wording` | 0/1 | An explicit inhalation word is present (not merely a ppm/mg/m³ unit) |
| `endpoint_types` | string | `; `-separated: `type1_hb_function`, `type2_rbc_anemia`, `type3_counts_marrow`, `coagulation` |
| `endpoint_terms` | string | `<type>:<term>` pairs that matched, e.g. `type1_hb_function:methemoglobin` |
| `compensatory_cues` | string | Regenerative-response wording: `reticulocytosis`, `extramedullary`, `erythroid_hyperplasia`, `splenic_erythropoiesis`, `compensatory_wording` |
| `negation_cues` | string | `not_observed`, `not_adopted`, `no_data` — the unit may state an **absence** of effect |
| `context_cues` | string | `has_noael_loael`, `has_concentration`, `has_duration`, `guideline_study`, `statistics` |
| `cooccurrence` | 0/1 | Endpoint **and** resolved species **and** resolved route in this same unit (623 units) |
| `evidence_unit_verbatim` | string | The exact source text the assignments were made from |
| `review_state` | string | `extracted_pending_expert_confirmation` |

### Route semantics — the critical distinction

`exposure_route_basis = inhalation` means **an inhalation word and the hematotoxicity endpoint appear in the same evidence unit**. It does *not* mean inhalation is mentioned somewhere in the rationale. Two further values exist because the source is ambiguous:

- `route_not_specified_air_unit_only` — exposure given only as ppm or mg/m³ with no inhalation word. Weaker than a stated route. Benzene's human occupational hematopoietic evidence sits here.
- `oral_dietary_concentration_inferred` — ppm appears together with feeding/diet wording. NITE uses ppm for **dietary** concentration in feeding studies; reading it as airborne would misattribute feeding studies to inhalation.

## 8. S05b_species_route_crosstab.csv — 32 rows

`evidence_species_basis` × `exposure_route_basis` × `evidence_units`.

## 9. S06_hematotoxicity_endpoint_types.csv — 566 rows

**STEP 4 deliverable.** One row per substance.

| Column | Type | Description |
|---|---|---|
| `substance_id`, `cas`, `substance_name` | string | Identity |
| `evidence_tier` | enum | Highest tier reached — see below |
| `all_tiers_present` | string | Every tier the substance's units reach |
| `n_segments`, `n_segments_with_endpoint` | integer | Unit counts |
| `human_segments`, `animal_segments` | integer | Units by species basis |
| `animal_species_named`, `routes_observed`, `human_cue_types` | string | Unioned across units |
| `type1_hb_function` | 0/1 | Methemoglobin, carboxyhemoglobin, sulfhemoglobin, cyanosis wording (163 substances) |
| `type2_rbc_anemia` | 0/1 | Hemolysis, anemia, RBC/Hb/Hct decrease, Heinz bodies, RBC morphology (376) |
| `type3_counts_marrow` | 0/1 | Blood cell count change, marrow or hematopoietic injury (268) |
| `coagulation` | 0/1 | Prothrombin/APTT, coagulation, fibrinogen, hemorrhage (88) |
| `<type>__human_inhalation` | 0/1 | That endpoint type is backed by a human + inhalation unit |
| `<type>__animal_inhalation` | 0/1 | That endpoint type is backed by an animal + inhalation unit |
| `type3_marrow_term_present` | 0/1 | A marrow/hematopoietic term occurs in a Type 3 unit |
| `type3_direct_marrow_wording` | 0/1 | A marrow term occurs in a unit carrying **no** compensatory cue |
| `type3_compensatory_wording` | 0/1 | A Type 3 unit carries compensatory wording |
| `type3_resolution`, `type3_assignment_after_compensatory_review` | enum | See below |
| `type2_hemolytic_wording` | 0/1 | Explicit hemolysis/hemolytic anemia wording |
| `negation_in_endpoint_segments` | integer | Endpoint units that also carry a negation cue — read before use |
| `has_noael_loael`, `has_quantified_exposure` | 0/1 | Dose-response context available |
| `review_state` | string | `extracted_pending_expert_confirmation` |

### Evidence tiers

| Tier | Definition | Substances |
|---|---|---|
| `A_human_inhalation` | human + explicit inhalation + endpoint in one unit | 11 |
| `B_human_inhalation_likely` | human (or mixed) + endpoint, exposure airborne-unit-only or inhalation named with another route | 29 |
| `C_human_route_unclear` | human + endpoint, route unresolved | 143 |
| `D_animal_inhalation` | animal + explicit inhalation + endpoint | 47 |
| `E_animal_other_route` | animal + oral/dermal/injection + endpoint | 168 |
| `F_endpoint_only` | endpoint present, species or route unresolved | 99 |
| `G_no_endpoint_text` | official blood-system classification, no endpoint term in the text | 69 |

Tiers describe **evidence text**, not toxicity. Tier A does not make a substance a verified human inhalation hematotoxicant.

### Type 3 resolution (rule R08)

Type 3 spans *both* peripheral blood-cell-count change *and* marrow/hematopoietic injury. These are separated because a marrow signal can be a **compensatory** response to peripheral red-cell destruction rather than direct marrow injury.

| Value | Meaning | Substances |
|---|---|---|
| `not_assigned_no_type3_wording` | No Type 3 term | 298 |
| `type3_marrow_injury_supported` | Marrow term in a unit with no compensatory cue | 149 |
| `type3_peripheral_counts_only` | Count change only; no marrow/hematopoietic term | 96 |
| `type3_marrow_signal_compensatory_only` | Marrow term appears **only** alongside compensatory wording → marrow injury withheld | 23 |

## 10. S06b_endpoint_type_summary.csv — 4 rows

`endpoint_type` · `substances_with_endpoint_text` · `human_inhalation_backed` · `animal_inhalation_backed`.

## 11. S07_source_citations_per_evidence_unit.csv — 3,007 rows

**Deliverable 5.** One row per (evidence unit × recognised cited source).

| Column | Type | Description |
|---|---|---|
| `substance_id`, `cas_all`, `name`, `hazard_class`, `unit_id` | string | Identity of the citing unit |
| `segment_species_basis`, `segment_route_basis`, `segment_endpoint_types` | string | What the citing unit asserts |
| `source_name` | string | Normalised source, e.g. `ACGIH documentation`, `IPCS CICAD` |
| `evidence_layer` | enum | `primary_test_report` (249) · `authoritative_review` (1,375) · `national_assessment` (691) · `secondary_database` (161) · `other_unclassified` (531) |
| `source_identifier` | string | Numeric identifier where present (NTP TR number, EHC/CICAD number, OECD TG number) |
| `citation_verbatim` | string | The parenthetical citation text as published |

> **Citation counts are not counts of independent studies.** The same underlying study is frequently cited by several compilations. Do not sum them as independent evidence.

## 12. S07b_cited_source_register.csv — 29 rows

`source_name` · `evidence_layer` · `citation_instances` · `substances`.

## 13. S08_published_human_reference_audit.csv — 28 rows

**Deliverable 4.** Each published v0.18 Dataset A human reference against the official NITE classification.

| Column | Type | Description |
|---|---|---|
| `reference_id`, `chemical`, `CAS`, `SMILES`, `InChIKey` | string | As published in v0.18 |
| `Evidence_level` | enum | v0.18 level: `1_core` (9) · `2_extended` (7) · `3_uncertain` (12) |
| `endpoint_class`, `endpoint_reported`, `route_basis` | string | v0.18 assignment |
| `reference_use` | enum | `provisional_primary_pool` (16) · `sensitivity_only` (12) |
| `toxicity_source_urls`, `limitations` | string | As published |
| `nite_substance_id` | string | Matched NITE entry; empty when the substance has **no** official NITE blood-system classification |
| `evidence_tier`, `all_tiers_present` | string | v0.28 tier |
| `nite_blood_target_terms`, `hazard_classes` | string | Official classification |
| `nite_corroboration` | enum | `corroborated_human_inhalation` · `corroborated_human_inhalation_likely` · `corroborated_human_route_unclear` · `official_blood_classification_animal_or_unresolved_basis` · `not_in_NITE_blood_system_set` |
| `type1_hb_function` … `coagulation` | 0/1 | NITE-text endpoint types |

## 14. S08b_manual_primary_literature_adjudication.csv — 5 rows

**Human-reviewed records.** Selected tier-A substances adjudicated against located primary literature.

| Column | Type | Description |
|---|---|---|
| `cas`, `substance_name` | string | Identity |
| `v028_tier` | string | Tier before adjudication |
| `nite_assertion` | string | What the NITE rationale asserts, with its cited source |
| `endpoint_type` | string | Hematotoxicity type concerned |
| `primary_literature_located` | string | PMIDs and titles found |
| `reviewer_judgement` | enum | The adjudication outcome |
| `reviewer_note` | string | Reasoning, including why a claim was qualified |
| `recommended_role` | string | Proposed Dataset A role |
| `remaining_work` | string | What verification is still outstanding |
| `review_state` | string | `manually_adjudicated_in_v028` |
| `new_final_label` | string | Empty in every row |

## 15. S08c_pubmed_primary_locators.csv — 48 rows

Candidate primary references located in PubMed. Columns: `cas`, `substance_name`, `query`, `pubmed_total_hits`, `pmid`, `title`, `journal`, `year`, `doi`, `abstract_present`, `abstract_excerpt`, `verification_state` (`located_not_verified`), `open_questions`.

**A located reference is not a verified reference.** No full text was adjudicated.

## 16. S09_inclusion_exclusion_hold_rules.csv — 11 rows

`rule_id` (R01–R11) · `scope` · `criterion` · `decision` · `rationale`.

## 17. S10_dataset_A_v028_join_layer.csv — 566 rows

**Join layer, not a replacement Dataset A.** Merge onto the local Dataset A on `cas`.

| Column | Type | Description |
|---|---|---|
| `substance_id`, `cas`, `substance_name` | string | Join keys |
| `dataset_A_role_v028` | enum | See below |
| `evidence_tier`, `all_tiers_present` | string | From S06 |
| `final_label` | string | **Empty in all 566 rows** |
| `verification_state` | string | `no_independent_primary_verification_in_v028` |
| `label_note` | string | What the record does and does not establish |
| `smiles`, `pubchem_inchikey`, `recomputed_inchikey`, `formula` | string | From S03 |
| `structure_status`, `structural_scope`, `exclusion_reason` | string | From S03 |
| endpoint and Type 3 columns | — | From S06 |

| `dataset_A_role_v028` | Substances |
|---|---|
| `official_hazard_reference_outside_structural_domain` | 170 |
| `official_hazard_reference_animal_non_inhalation` | 140 |
| `official_hazard_reference_species_route_unresolved` | 73 |
| `hold_human_evidence_route_unclear` | 72 |
| `animal_inhalation_support_provisional` | 39 |
| `official_hazard_reference_no_endpoint_in_text` | 27 |
| `human_occupational_extended_candidate_pending_verification` | 22 |
| `hold_structure_unresolved` | 10 |
| `human_inhalation_candidate_pending_primary_verification` | 8 |
| `coagulation_endpoint_outside_type1_3` | 5 |

## 18. S11_gap_register.csv — 12 rows

`gap_id` (G01–G12) · `protocol_step` · `item` · `status` · `consequence` · `resolution`.

Every protocol step this build could not complete is recorded here with the reason. No step is reported complete on missing data.

## 19. output_manifest.json

`version` and `table_sha256` (SHA-256 of all 18 CSV outputs).
