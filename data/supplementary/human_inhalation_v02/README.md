# Supplementary evidence data: human inhalation hematotoxicity, v0.2

**Provisional evidence release — not a validated QSAR training dataset.** Research 2, IndustryQSAR. Assembled 2026-11-27.

This release preserves the existing human in-vivo inhalation and occupational airborne evidence observations across all concentrations and durations. It is intended as a traceable draft for future manuscript supplementary data. Occupational airborne exposure may coexist with other routes; exclusive attribution, confounding and individual chemical identity must be adjudicated before model use. Animal, in-vitro-only and non-inhalation evidence is outside the current scope.

| File | Records |
|---|---:|
| [human_inhalation_study_evidence.csv](human_inhalation_study_evidence.csv) | 49 |
| [chemical_identity.csv](chemical_identity.csv) | 21 |
| [chemical_evidence_summary.csv](chemical_evidence_summary.csv) | 21 |
| [hematologic_cancer_evidence.csv](hematologic_cancer_evidence.csv) | 4 (subset of 49) |
| [route_uncertain_excluded.csv](route_uncertain_excluded.csv) | 1 |
| [source_context_index.csv](source_context_index.csv) | 90 source locators |
| [primary_reference_signals.csv](primary_reference_signals.csv) | 3 (overlap existing evidence) |
| [training_labels_pending.csv](training_labels_pending.csv) | 0 |
| [metadata.json](metadata.json) | Provenance and integrity |
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | Field definitions and interpretation |

The 49 observations include 45 hematology observations and 4 neoplasm associations. They are not 49 independent studies. Conditional non-effects are not confirmed chemical negatives; cancer associations are not noncancer training labels. All training labels are blank. The 949-row keyword queue has only been partially adjudicated. See the [research protocol](../../../docs/hematotoxicity_research_protocol_ko.md) and [v0.2 evidence audit](../../../docs/human_inhalation_evidence_v02_ko.md).

## Integrity and reproducibility

Run from the repository root: `python data/supplementary/human_inhalation_v02/validate_release.py`. This checks file hashes, row counts, joins and empty labels, not scientific accuracy. The normalized original seven CSV tables and derived source locator table were matched to the original archive at publication. Full reconstruction from primary sources requires the locally retained original archive, extraction inputs and PDFs. Metadata provides the original archive and input hashes. No verbatim source passages or full PDF texts are published; the local queue and original builder are not included in this release. Source citations and original source rights must be respected.

For a future paper cite this dataset version, the immutable Git commit, and the individual source studies. This is not a DOI deposit or peer-reviewed data release. Final publication should include adjudicated evidence, verified structures, reviewer/date, full source bibliography/versions and independent validation. Preserve this v0.2 directory as a snapshot; place subsequent data releases in a new version directory.
