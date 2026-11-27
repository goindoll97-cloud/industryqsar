# Data dictionary (English)

All tables are UTF-8 CSV; missing information is an empty string or an explicit original note such as “not reported in excerpt”. Values are preserved from the local v0.2 archive. Do not interpret blanks as zero. The study table is **provisional**, not a completed training set.

## Study-level evidence, cancer subset and excluded records

The same schema applies to `human_inhalation_study_evidence.csv`, `hematologic_cancer_evidence.csv` (subset) and `route_uncertain_excluded.csv`.

| Field | Definition |
|---|---|
| chemical_name | Curated substance name |
| citation | Author/year citation as recorded; may combine publications or related cohorts |
| record_ids | Semicolon-separated one-based original candidate CSV row IDs, excluding header; blank for external articles |
| source_url | ATSDR PDF or selected primary article URL |
| source_pages | One-based PDF page indices, not necessarily printed page numbers; semicolon-separated |
| species | human |
| route | inhalation; occupational_airborne (airborne occupational candidate, not necessarily exclusive inhalation); mixed_route_uncertain (excluded) |
| concentration | Original curated exposure text; may be TWA, range, cumulative exposure (ppm-years), or unreported; not a standardized numeric concentration |
| duration | Original curated exposure duration text; may contain employment duration or latency; do not treat latency as duration |
| endpoint | Observed/assessed hematologic endpoint or cancer outcome |
| effect | Provisional observation category, not a substance-level label |
| review_note | Limitations, confounding, attribution, related cohorts or verification needs |
| source_level | ATSDR_context (secondary profile context), external_article (selected article) |
| endpoint_class | hematology or cancer (includes MDS as hematologic neoplasm evidence) |
| evidence_id | Stable record key H001–H050; H018 is excluded |
| cas_rn | Candidate CAS Registry Number, not registry-verified |
| smiles_input | Candidate input SMILES; not an independently validated canonical structure |
| identity_status | candidate_identity_not_registry_verified |
| review_status | context_or_article_review_pending_final_adjudication |
| training_label | Empty until final adjudication |

Effect values: **adverse_signal** = provisional adverse observation; **change_signal** = observed change with adversity or causality not resolved; **no_effect_at_condition** = no observed adverse effect under the stated conditions/endpoints, not a chemical-level negative; **uncertain** = unresolved evidence; **association_signal** = hematologic neoplasm association, separate from noncancer hematology.

## Chemical identity and summary

`chemical_identity.csv`: chemical_name, cas_rn, smiles_input as defined above.

`chemical_evidence_summary.csv`: chemical_name, cas_rn, smiles_input, identity_status as above; hematology_records (number of included hematology rows); adverse_signal, change_signal, conditional_no_effect, uncertain (counts of corresponding hematology effect values); cancer_records (included cancer rows); cancer_association_records (cancer association signals); provisional_status (positive_candidate if any adverse_signal; change_or_uncertain if no adverse signal but change/uncertain; conditional_no_effect_only otherwise if hematology rows exist; no_hematology_review if none); training_label (blank); evidence_ids (semicolon-separated included IDs). These are descriptive counts, not independent study counts or weights.

## Source index and selected references

`source_context_index.csv`: record_id (original one-based row ID), profile (original ATSDR profile title), pdf_url (official source PDF), file (original relative cached filename, not included), page (one-based PDF page), line (one-based extracted text line), evidence_ids (linked included evidence IDs). Source excerpts were deliberately removed. Excluded H018 references records 287/288 also linked to included rows; exclusion remains traceable in the excluded table.

`primary_reference_signals.csv`: chemical_name, cas_rn, smiles_input, species, route, endpoint_class, reference (citation), source_url, interpretation (curated reference note), concentration, training_label (blank). Three selected references overlap existing records and must not be treated as extra independent observations.

`training_labels_pending.csv`: cas_rn, canonical_smiles (validated structure required), label (adjudicated binary class only if supported), adjudicated_evidence_ids (source evidence IDs), reviewer, review_date (ISO 8601 date). Header only.

## Metadata

`metadata.json` documents scope, provenance, assembly date, limitations, counts and normalized Git blob checksums. The original source collection date, PDF revision and individual review timestamps are not established in the archive and are not fabricated.
