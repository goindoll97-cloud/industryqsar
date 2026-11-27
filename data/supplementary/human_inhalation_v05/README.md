# Human inhalation hematotoxicity v0.5 — experimental pilot

This is a frozen, executable pilot, NOT a publication-validated binary hazard dataset. Target: human in vivo inhalation or documented occupational airborne exposure, with no concentration or duration restriction. Animal and oral-only studies do not supply labels. Existing v0.2–v0.4 source evidence remains unchanged.

## Files
- hematotoxicity_dataset.csv: 10 main observations (5 positive, 5 conditional no-effect).
- hematotoxicity_core.csv: 7 (2 positive, 5 conditional no-effect); excludes functional hemoglobin positives.
- hematotoxicity_sensitivity.csv: 20 (11 positive, 9 conditional no-effect); includes weaker/conflicting evidence and potential mixed-route contributions. Not a strictly confirmed inhalation-only set. Nested, not independent.
- label_decisions.csv: short source-specific label rationale and tier.
- all_chemical_registry.csv: 60 identities; non-main labels blank.
- cancer_reference_evidence.csv: separate 5 observations, 4 chemicals; not independently held out when structures overlap.
- metadata.json: version, provenance, hashes, software and limitations.
- run_pilot.py, screen_similarity.py: tested baseline and positive-reference retrieval.
- pilot_main, pilot_core, pilot_sensitivity: actual metrics.

The dataset has six fields: Chemical, CAS_RN, SMILES, Label, Endpoint, Reference. Only SMILES and Label enter models. 1 denotes observed effects/associations; 0 denotes conditional no-effect of measured blood indices, NOT confirmed hazard absence. Unknown is never negative. In particular 0 records may not have assessed functional hemoglobin effects. No universal negative label is available. The pilot main set includes different types of hematological endpoints. CAS identity verification is incomplete, although RDKit parsing/canonicalization and duplicate checks passed. Source support can be agency summaries or primary abstracts rather than full papers.

Run in this directory:

```bash
python -m pip install rdkit numpy scikit-learn
python run_pilot.py --out pilot_main
python run_pilot.py --dataset hematotoxicity_core.csv --out pilot_core
python run_pilot.py --dataset hematotoxicity_sensitivity.csv --out pilot_sensitivity
python screen_similarity.py --input candidate_smiles.csv --out similarity_screen.csv
```

The screening input needs Chemical and SMILES columns. It returns up to five positive references by Tanimoto; no calibrated AD, toxicity probability or safe/unsafe classification. The pilot uses fixed models, no tuning and leave-one-molecule-out; varying fold prevalence distorts pooled rank scores and the small selected sample cannot establish generalization. Main balanced accuracy: Tanimoto 0.30, LR 0.30, RF 0.10. No external validation. Do not deploy for safety decisions.

Full local downloadable ZIP contains source snapshots, assembly code, prediction records and smoke test output. The public GitHub files above are identical to their local counterparts (blob hashes in metadata). Remaining ATSDR queue was not fully adjudicated; selected contexts yielded new ethylene glycol and 1,1-dichloroethene evidence, plus targeted external research. No claim of complete or final scientific adjudication.
