# Human hematotoxicity candidate base v1.0 (2026-11-26)

## Scope
Human-first exploratory CMP project. This is an evidence inventory, not a validated human toxicity training set. SIDER records are human drug-label ADR candidates (not adjudicated causal events); IRIS critical-system entries may rely on animal evidence. No confirmed negatives. No inhalation-specific or cancer labels. No animal data in the human training pool. CMP candidates are prediction targets only.

## Sources and citation
- SIDER 4.1 (2015-10-21): https://sideeffects.embl.de/download/ ; Kuhn M, Letunic I, Jensen LJ, Bork P. The SIDER database of drugs and side effects. Nucleic Acids Res. 2016;44(D1):D1075–D1079. doi:10.1093/nar/gkv1075. Source website states CC BY-SA 4.0 except where otherwise noted; verify exceptions, MedDRA terms and label-derived data permissions before redistributing. Do not apply repository code license to third-party data.
- US EPA IRIS: https://iris.epa.gov/AtoZ/alpha/ ; https://www.epa.gov/iris/iris-downloads . User-supplied Excel snapshot, exact original download date unknown; audited 2026-11-26. Preserve source revision field. Critical systems are not necessarily the basis of the inhalation RfC.
- Long et al. (2023), doi:10.1021/acs.jcim.2c01088, supporting XLS: 2,382 rows (759 positive, 1,623 negative). Mixed provenance; comparator only, not human-only training. Keep original files local.
- EPA ToxRefDB v3.0: https://www.epa.gov/comptox-tools/downloadable-computational-toxicology-data . Animal data excluded from current human-only pilot.
- CMP experimental context: doi:10.1016/j.chemosphere.2017.10.138; four tested organic additives (glycine, proline, nicotinic acid, benzotriazole). No verified new organic byproduct structures. Patent evidence is separately recorded in data/cmp_organic_evidence.csv.

## Exact input snapshots
Put user-provided files in data/private/cmp_hematotoxicity/raw/ (not tracked):
- sider_drug_names.tsv
- sider_drug_atc.tsv
- sider_meddra_all_label_se.tsv.gz
- iris_simple_list_alpha.xlsx
SHA-256 fingerprints are embedded in build_human_base.py; a changed snapshot must receive a new version.

## Reproduction
From repo root (Python 3.11+):
```powershell
python -m pip install pandas openpyxl
python cmp_hematotoxicity/build_human_base.py --raw data/private/cmp_hematotoxicity/raw
```
Outputs are local, not public, until redistribution permissions are cleared. Expected counts from inspected v1 files: SIDER 4,753,141 raw label rows, 49,939 distinct selected rows, 1,430 flat STITCH IDs (735 reported, 695 unreported); IRIS 572 input rows, 51 selected rows. Counts represent identifiers/records, not unique validated chemical structures.

## Selection and data dictionary
SIDER: exact case-insensitive MedDRA PT matching of Leukopenia, Lymphopenia, Neutropenia, Agranulocytosis, Thrombocytopenia, Pancytopenia, Myelosuppression, Bone marrow failure, Aplastic anaemia, Haematotoxicity, Bone marrow depression. Deduplicate across all seven input columns, aggregate by flat STITCH ID, retain all ATC codes.
- sider_selected_pt_evidence.csv: label (source label path), cid (flat STITCH ID), stereo (stereospecific STITCH ID), cui (source concept), type (PT), pt_cui (preferred concept), term (preferred term).
- sider_human_candidate_inventory.csv: cid, name, terms (semicolon-separated matched terms), label_documents (distinct source labels), atc (all associated ATC codes), evidence_status (reported_selected_PT / unreported_selected_PT). Missing terms or label count mean no selected report found, not zero toxicity. No numeric Y assigned.
- iris_hematologic_candidates.csv: original IRIS columns unchanged; case-insensitive substring hematolog in Critical Effect Systems. Includes CASRN, revision, RfD, RfC, tumor site; human source and route-specific critical effect need manual verification.
- manifest.json: hashes and output counts.
- CMP inventory: 69 evidence records / 56 names, not necessarily unique structures or site-used substances.

## Before training / supplementary publication
Resolve and validate STITCH/CAS/SMILES, preserve salts and stereo before grouping, inspect mixtures, classify antineoplastics, verify human evidence, adjudicate indications and ADRs, separate unlabeled from verified negatives, deduplicate chemical groups across sources and splits. Use PU learning only with explicit assumptions; do not interpret reported/unreported classification as clinical toxicity probability. Independently validate on industrial human evidence before CMP extrapolation. Archive source-specific licenses and versioned input/output hashes before releasing a supplement. No risk estimates without exposure data.

## Status
Original files and existing extracted CSV headers/counts inspected. New reproduction script is not yet executed in this repository. No final human-only QSAR labels or models have been generated.
