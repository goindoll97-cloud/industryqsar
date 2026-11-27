# Hematotoxicity four-source reference snapshot v0.9

2026-11-27. **Provisional, not a final training dataset.**

Goal: positive-reference structural screening of potential hematotoxic hazards in semiconductor and other industrial organic chemicals. Only human in vivo inhalation evidence may establish main reference eligibility. Mixed/uncertain exposure remains conditional. Hematologic cancer is separate; unverified substances are not negatives.

Four main collection sources: Hua (2021), Long (2023), ATSDR Toxicological Profiles, and PubMed-indexed primary studies (individual citations required). The first two are candidate discovery sources only. PubChem/NIST and industry inventories are auxiliary identity/use sources, not toxicological labels.

Local extraction: 632 + 759 positive records, 13 Long positive parse failures, 251 exact InChIKey overlaps, 1,127 unique candidate structures and 14 conflicting source labels. Of 8,110 industry inventory records, only 108 had SMILES; 21 candidates were matched (8 A1, 11 A2, 2 TRI-only). No new confirmed positive was established. The 10 provisional industrial positives were selected from the 12 inherited v0.8 positives; 23 conditional references and 2 industrial-use holds remain in the 35-row audit. Occupational airborne evidence does not prove exclusive inhalation; full-text adjudication remains incomplete.

## Public files

- provisional_industrial_positive.csv: 10 provisional reference rows, not final training labels.
- reference_industry_audit.csv: 35 prior references with industry and toxicity status.
- prior_v08_evidence_audit.csv: 35 prior evidence decisions and source locators.
- industrial_priority_candidates.csv and industrial_priority_review.csv: 21 candidates and their review status; do not train on source labels.
- prior_hold_candidates.csv: 12 hold/exclusion records.
- cancer_reference_separate.csv: 8 separate association records, not noncancer training labels.
- source_register.csv: four main collection sources.
- summary.json: counts and limitations.

The full local hematotoxicity_four_sources_v09.zip contains the complete 1,127-candidate table, extracted source tables, and integration scripts. They are not republished here pending verification of third-party redistribution terms. Prior releases are retained. No model performance or final exhaustive curation is claimed.
