# Human inhalation hematotoxicity — integrated supplementary evidence v0.3

Assembled 2026-11-27. **Provisional evidence registry, not a validated training dataset.** Human in-vivo inhalation is the target; no concentration or duration restriction. Animal, non-inhalation, mixed-route/uncertain attribution, search-only records and out-of-scope structures are retained for audit only, not accepted as training evidence. Occupational airborne evidence may still involve dermal or mixture exposure.

The original official V10 archive contains 64 source records across 40 CAS identities (53 ATSDR, 5 EPA IRIS, 6 OEHHA). All 64 and all 50 v0.2 observations including one excluded row are retained. The 114 rows cover 44 CAS identities, including 23 V10-only, 17 shared and 4 v0.2-only. There are 28 manually proposed citation/cohort links and 92 citation-review groups, **not 92 independent studies**. Grouping preserves distinct exposure arms and source disagreements. Candidate, hold, excluded, data_gap and cancer_separate are review buckets, not labels. Of the 92 groups, 41 are candidates, 34 on hold, 7 excluded, 6 data gaps and 4 cancer-only; 20 CAS identities have at least one candidate group. No final positive or negative labels have been assigned.

The 44 CAS identities include a mixed-xylene record and carbon disulfide retained from the prior scope audit, excluded from the organic QSAR structure set. 43 input structures parse in RDKit 2025.09.4; 42 unique organic candidate structures remain, including 16 new manual SMILES proposals. Chemical identity is not registry-verified. Candidate structures do not imply toxicity or training eligibility.

## Files
- `official_v10_evidence.csv`, `official_v10_chemical_review.csv`: complete V10 tables, normalized serialization, original columns retained.
- `integrated_evidence.csv`: 114 source rows; original status and source location preserved.
- `evidence_overlap_links.csv`: 28 citation/cohort links, including non-grouping links.
- `citation_review_groups.csv`: 92 review units, no claim of independent studies.
- `chemical_inventory.csv`: 44 CAS identities, structure candidates, scope, group counts.
- `training_labels_pending.csv`: header only.
- `metadata.json`, `DATA_DICTIONARY.md`, `validate_release.py`: version, provenance, schema, integrity audit.

V10 dates are source-reported access dates, not independently verified. No original primary full-text adjudication has been added. Missing source dates/route/dose/duration remain blank; the source exposure context may include an RfC/REL, cumulative dose or latency, not measured concentration. Source summaries are not independent replications. Reconcile overlapping cohorts and verify study-level human inhalation, endpoint adversity, confounding and structure identity before training. The original ZIP, inventory and raw PDF excerpts remain local; v0.2 is preserved in its own directory. Cite the immutable Git commit and primary studies when preparing a manuscript; no DOI or blanket third-party license is asserted.

Run `python validate_release.py` in this folder for integrity only. The local downloadable bundle includes the original Python builder; it requires the original V10 and v0.2 source CSVs and RDKit 2025.09.4. Metadata includes raw input SHA-256 and published normalized Git blob SHA-1. The repository does not contain the full original ZIP or source PDFs.
