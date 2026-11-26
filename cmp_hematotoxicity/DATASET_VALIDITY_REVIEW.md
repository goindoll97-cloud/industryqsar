# Dataset validity review — 2026-11-26

Decision: HOLD merge to main. Suitable as exploratory evidence inventory only; not a validated human inhalation hematotoxicity training set.

## Reproduction audit
Four local source SHA-256 values matched build_human_base.py. Independently reran equivalent pandas extraction against uploaded originals: 4,753,141 label rows; 49,939 selected distinct rows (identical to prior evidence CSV); 1,430 named flat STITCH IDs, 735 reported and 695 unreported; all 1,430 have at least one PT record; 51 reported flat IDs have multiple stereospecific IDs. IRIS 572 rows, 51 selected. This is an extraction audit, not validation of clinical causation. Exact GitHub CLI and external API execution not verified.
L01 ATC: 80/84 reported; other IDs 655/1346. L01 exclusion sensitivity analysis is required, not a claim that all other drugs are non-cytotoxic. Three selected PT strings have zero matches (Myelosuppression, Bone marrow failure, Bone marrow depression). Review vocabulary before any revision; retain v1 frozen.

## Primary validity threats
- SIDER raw label extraction is not adjudicated human clinical evidence. Check processed meddra_all_se, indication and frequency/placebo files and original label sections; distinguish clinical vs animal, disease indications, laboratory changes, co-medications. No reported association means unknown, never confirmed negative. No direct concentration or inhalation endpoint. A reported/unreported classifier predicts labeling patterns, not toxicity; PU assumptions must be justified and sensitivity tested.
- IRIS system flags do not identify human-only or route-specific critical studies. Review each original assessment and its primary human studies; extract CAS, study population, route, concentration, duration, endpoint, comparator, effect, uncertainty and citation. Require explicit evaluated no-effect findings with exposure context for negative evidence; no-study is unknown.
- CMP evidence CSV is a preliminary patent/lab inventory, not representative of workplace chemical use. Verify every row with precise claim/example/table locator, resolve structures, distinguish experimental use from enumerated options, record inclusion and search criteria. No verified organic byproducts or workplace concentration.
- Chemical structure AD alone cannot solve biological endpoint/route shift. Independent industrial human validation with matched endpoints, both classes or a defensible positive-only evaluation, no structure/source leakage, and prespecified acceptance criteria is required. Report uncertainty, coverage, abstention and antineoplastic sensitivity. Do not infer cancer, inhalation-specific risk or individual causation.

## Release gates
1. Establish primary endpoint (e.g. observed human leukocyte reduction or clearly defined cytopenia) and keep other endpoints separate. No arbitrary union of effects as clinical truth.
2. Build auditable human industrial evidence table with independent source studies, controls and exposure context; report actual counts and feasibility. If insufficient, stop or narrow claim to ADR transfer feasibility, not human CMP toxicity prediction.
3. Resolve CAS/STITCH/SMILES and duplicate groups before split; preserve stereochemistry. Verify CMP source locators and product SDS if available.
4. Validate study/structure grouping and domain transfer, compare baseline and L01 exclusion, predefine performance and coverage criteria before test access.
5. Reproduce exact pipeline and archive versioned outputs, licenses and hashes. No final dataset release/merge approval until scientific suitability is demonstrated.

## References
OECD (2024), (Q)SAR Assessment Framework, second edition: https://doi.org/10.1787/bbdac345-en
Kuhn et al. (2016), SIDER: https://doi.org/10.1093/nar/gkv1075 ; https://sideeffects.embl.de/download/
EPA IRIS handbook and glossary: https://www.epa.gov/iris/iris-glossary ; https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1017I1X.TXT

No final human toxicity model is approved. Keep PR open for further evidence; main remains unchanged.
