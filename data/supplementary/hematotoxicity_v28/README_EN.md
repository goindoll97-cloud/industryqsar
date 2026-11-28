# v0.28 — Official hazard-classification evidence re-derivation

**Status: not a final submission version.** The official NITE blood-system
classification layer is reproduced and frozen. The route-specific, species-specific
and endpoint-specific research dataset is **not** frozen. New confirmed positive
hematotoxicity labels in this release: **0**. Independent primary-source
verifications completed: **0**.

Study: *Official Hazard Classification-Based Screening of Potential Hematotoxicants
Using Molecular Structural Characteristics: Application to Semiconductor
Manufacturing Chemicals*

---

## 1. What changed in v0.28

v0.27 left 323 of 417 structure-ready NITE evidence rows without a full reading of
the official classification rationale, because the rationale text had been
available only as per-substance detail pages.

v0.28 found that NITE publishes the complete rationale in bulk. The official
download page offers a second workbook, **`list_rational_e.xlsx`**, which was not
part of the v0.24–v0.27 input manifest. It contains the verbatim
*"Rationale for the classification"* for every substance × hazard class —
117,026 rows, of which 6,904 are STOT entries.

Consequently v0.28 does not review a 323-row subset. It re-derives and reads the
rationale for **all 749 blood-system classification records**, segmented into
**3,634 individual evidence units**, each retained with its verbatim source text.

## 2. Reproduction of the published classification set

The v0.28 re-derivation, run against the official download retrieved 2026-11-28,
reproduces the published v0.24–v0.27 snapshot:

| Quantity | v0.24–v0.27 record | v0.28 re-derivation | Agreement |
|---|---:|---:|---|
| Blood-system STOT evidence rows | 747 | 747 | exact |
| Unique CAS | 562 | 562 recovered, 0 missing | exact |
| Marrow / hematopoietic target | 60 | 60 | exact |
| STOT-SE only / RE only / both | 73 / 310 / 179 | 74 / 307 / 179 | ±3 |
| Category 1 involved / Category 2 only | 377 / 185 | 376 / 184 | ±1 |

The selection rule that reproduces the published 562 exactly is: STOT-SE or
STOT-RE **Category 1 or 2** naming `blood`, `blood system`, `bone marrow`,
`hematopoietic system`, `hematopoietic organ` **or** `blood coagulation system`
as a target organ, counting CAS cells unsplit.

### Three findings that affect the published set

1. **5 of the 562 are coagulation-only.** Estrone, 2,4-di-tert-butylphenol,
   chlormadinone acetate, 4-sec-butyl-2,6-di-tert-butylphenol and indanofan have
   `blood coagulation system` as their *only* blood-related STOT target.
   Haemostatic toxicity lies outside this study's Type 1–3 framework, and for the
   two steroid hormones the effect is prothrombotic — mechanistically opposite to
   hematotoxicity. v0.28 separates them under rule R02 (gap `G12`).

2. **Two substances were dropped by the v0.24 pipeline** because NITE records two
   CAS numbers in one cell: **Thiouracil** (141-90-2 / 80275-68-9) and
   6-acetyl-1,1,2,4,4,7-hexamethyltetralin (21145-77-7 / 1506-02-1). Thiouracil is
   a blood-system **STOT-RE Category 1** entry, and thiouracils are an established
   cause of agranulocytosis, so the omission is material (gap `G11`).

3. **NITE dataset drift.** The current download holds 3,452 substances with STOT
   entries against 3,476 recorded at v0.24. All 24 substances without rationale
   STOT rows carry `-` in both STOT columns, so none can affect blood-system
   selection.

## 3. Method: evidence units, not whole-cell keywords

A NITE rationale routinely reports human occupational data, animal inhalation data
and animal oral data in consecutive sentences of one cell. Whole-cell keyword
matching therefore cannot answer either question the protocol asks: *which species
produced the finding*, and *was the finding produced by an inhalation study*.

Every assignment in v0.28 is made at the level of a single evidence unit — a
numbered `[Evidence Data]` item for FY2018–FY2023 entries (172 records), or a
sentence for the unstructured narrative format (573 records) — and the verbatim
unit text is retained alongside the assignment.

The route vocabulary distinguishes three cases that a naive reading conflates:

| Value | Meaning |
|---|---|
| `inhalation` | An explicit inhalation word and the endpoint occur in the **same** unit |
| `route_not_specified_air_unit_only` | Exposure given only as ppm or mg/m³, no inhalation word |
| `oral_dietary_concentration_inferred` | ppm appears with feeding/diet wording |

The third case matters: **NITE uses ppm for dietary concentration in feeding
studies.** Before this was handled, feeding studies dosed in dietary ppm were read
as inhalation studies. Correcting it moved 218 evidence units into the oral route
and removed 155 spurious airborne-exposure signals.

The method is deliberately **conservative** — it under-calls rather than
over-calls. Benzene is the documented example: its human occupational
hematopoietic evidence is reported with ppm values but without the word
"inhalation", so it falls in tier B, not tier A (gap `G09`).

## 4. Results

### Evidence tiers (566 substances)

| Tier | Substances |
|---|---:|
| `A_human_inhalation` — human + explicit inhalation + endpoint in one unit | 11 |
| `B_human_inhalation_likely` | 29 |
| `C_human_route_unclear` | 143 |
| `D_animal_inhalation` | 47 |
| `E_animal_other_route` | 168 |
| `F_endpoint_only` | 99 |
| `G_no_endpoint_text` | 69 |

### Hematotoxicity types (STEP 4)

| Type | Substances | Human-inhalation backed | Animal-inhalation backed |
|---|---:|---:|---:|
| Type 1 — haemoglobin functional impairment | 163 | 7 | 27 |
| Type 2 — erythrocyte damage / anaemia | 376 | 6 | 52 |
| Type 3 — cell counts / marrow and haematopoietic injury | 268 | 2 | 30 |
| Coagulation (separate fourth class) | 88 | 1 | 8 |

### Type 3 separated from compensatory response (rule R08)

The protocol requires that direct marrow injury be distinguished from
regenerative erythropoiesis secondary to peripheral red-cell destruction:

| Outcome | Substances |
|---|---:|
| `type3_marrow_injury_supported` — marrow term in a unit with no compensatory cue | 149 |
| `type3_peripheral_counts_only` — count change only, no marrow term | 96 |
| `type3_marrow_signal_compensatory_only` — **marrow injury withheld** | 23 |

Diuron illustrates the distinction. Its NITE rationale reports sulfhemoglobin
formation, decreased RBC and Hb, increased reticulocytes, Heinz bodies, splenic
extramedullary haematopoiesis and "reactive" marrow haematopoiesis — an oxidative
haemolytic anaemia with a compensatory response, not primary marrow toxicity.

### The decisive methodological finding for STEP 5

Of 3,007 citation instances in the blood-system rationales, only **249** point to a
primary test report (an NTP technical report or an OECD TG study). The remainder
cite authoritative secondary compilations (ACGIH, DFG MAK/DFGOT, PATTY, IPCS
CICAD/EHC, EU-RAR, ATSDR, IARC) or Japanese national assessments.

**Not one of the 11 tier-A human-inhalation substances cites a primary journal
article.**

A NITE blood-system classification therefore establishes **official hazard
classification and its stated basis**, but it does **not** constitute
primary-source verification of human inhalation hematotoxicity. This is the
evidentiary justification for keeping *official hematotoxic hazard reference* and
*human inhalation core* as separate roles (gap `G05`).

## 5. Audit of the published human reference set

All 28 published v0.18 Dataset A human references were checked against the official
classification (`S08_published_human_reference_audit.csv`).

**Independently corroborated** — naphthalene and methanethiol reach tier A;
benzene and 2-bromopropane reach tier B, the latter corroborating its reported
pancytopenia and marrow hypoplasia.

**Single-source support, to be disclosed** — four references have **no** official
NITE blood-system classification at all, three of them at the highest `1_core`
level: 4-bromo-2-fluoroaniline, 5-amino-2-(trifluoromethyl)pyridine,
dichloromethane, and 2-ethoxyethyl acetate (`2_extended`). They rest solely on the
primary case reports already recorded in v0.18.

## 6. Manual adjudication: five tier-A substances against primary literature

Primary literature was located in PubMed and read for five tier-A substances
(`S08b`). In **three of five cases the primary literature qualifies what the NITE
summary asserts** — which is the point of the exercise:

| Substance | Judgement |
|---|---|
| **2-Ethoxyethanol** (110-80-5) | Human occupational haematological evidence is genuine, but an intervention study achieved improvement by **adding rubber gloves**, implying substantial dermal contribution; the bone-marrow report concerns lithographers exposed to glycol ethers *and* other solvents. → occupational-extended, not inhalation core |
| **1,2-Dichloropropane** (78-87-5) | Human reports concern **mixed consumer products** (stain removers, rubber cement) and the clearest acute case is oral ingestion; clean inhalation data are animal. NITE's "chronic inhalation causes haemolytic anaemia" is not reproducible as a single-substance human inhalation finding. → retain the existing `3_uncertain / sensitivity_only` assignment |
| **Lindane** (58-89-9) | Human marrow toxicity is well documented and supported by in vitro human progenitor assays, but the route in the primary case literature is predominantly **dermal** (topical scabicide) or systemic poisoning, not occupational inhalation |
| **o-Toluidine** (95-53-4) | Type 1 mechanism strongly supported in humans, but chiefly through **prilocaine** metabolism (o-toluidine is the drug metabolite), i.e. systemic drug exposure. The occupational 20/81 observation traces to DFG MAK documentation from 1992, not retrieved |
| **Nitrogen monoxide** (10102-43-9) | Route and endpoint well supported, but the accessible primary literature is overwhelmingly **therapeutic** inhaled nitric oxide in neonates and ARDS patients, not occupational exposure |

New human-inhalation candidates surfaced by the official rationale but **not** in
the existing 16-substance human set include 2-ethoxyethanol, nitrogen monoxide,
o-toluidine, m-aminophenol, p-nitrochlorobenzene and lindane. Several are
industrially significant; nitrogen monoxide and nitrous oxide are semiconductor
process gases. None is promoted to a confirmed label here.

## 7. What this build could not do

Recorded in full in `S11_gap_register.csv` (12 entries). The principal limits:

- **`hematotoxicity_v27_supplement.zip` was not available.** Dataset A (349
  records), Dataset B (8,110) and the screening candidate set (2,519) therefore
  **could not be regenerated or updated in place**. v0.28 supplies a CAS-keyed
  join layer (`S10`) instead of a replacement Dataset A, so the new evidence can
  be merged into the local tables without guessing their contents.
- **The 94-reviewed / 323-pending row mapping could not be recovered**, as it lives
  in that ZIP. v0.28 read all 749 records instead, which supersedes the subset but
  leaves the row-level mapping to the prior flags open.
- **No full-text primary verification was completed** for any substance.
- **The PubChem structure audit is not a substitute** for the frozen EPA-based S03.
  It queries a different registry, so the counts differ (390 single-component
  organic of 570 CAS here, versus 332 of 562 in v0.27) and must not be conflated.
- **STEP 6 remains open**: the EPA TRI listing version and per-substance listing
  basis (28 substances), exact citations for 4 of the 249 semiconductor-core
  records, and the EPA CompTox CCD-Batch-Search raw export.

## 8. Files to supply to close the gaps

1. `hematotoxicity_v27_supplement.zip` — closes `G01`, `G02`, `G03`
2. EPA CompTox **CCD-Batch-Search** raw CSV for the 328 newly queried substances — `G08`
3. The original **EPA TRI** list export captured at collection time — `G06`
4. The **chemical-use survey** source document for the 4 semiconductor-core records — `G07`

## 9. Reproduction

```bash
pip install "rdkit==2025.9.4" pandas openpyxl
```

Download the two official workbooks from
<https://www.chem-info.nite.go.jp/chem/english/ghs/ghs_nite_download_e.html>
(`list_nite_all_e.xlsx`, `list_rational_e.xlsx`), then:

```bash
python3 -I code/extract_stot.py        <path>/list_rational_e.xlsx  work/nite_stot_all_rows.csv
python3 -I code/reconcile.py           <path>/list_nite_all_e.xlsx  work/nite_stot_all_rows.csv
python3 -I code/blood_select_v2.py
python3 -I code/run_extract.py
python3 -I code/aggregate_evidence.py
python3 -I code/extract_citations.py
python3 -I code/resolve_structures.py
python3 -I code/build_v28.py
python3 -I code/manual_review_v28.py
python3 -I code/validate_v28.py
```

`validate_v28.py` runs 31 assertions, including the exact reproduction of the
published 562-CAS set and the 60-substance marrow count, the Type 3 partition, and
the requirement that no confirmed positive label is set anywhere. Unavailable
inputs are reported as `SKIP`, never as `PASS`.

PubChem and PubMed responses are cached verbatim under `work/pubchem_cache/` and
`work/pubmed_cache/`, so the run is repeatable without re-querying.

## 10. Standing constraints

- No new model was developed or run. No experiment was executed.
- No new toxicity database was added. `list_rational_e.xlsx` is a second file from
  the NITE source already in the protocol, not a new source.
- Animal and human hematotoxicity are never merged into one positive label.
- Absence of toxicity data is never encoded as a negative label.
- No substance is marked as a confirmed positive hematotoxicant.
- Target-organ classification, observed indicator and mechanism of action are kept
  as separate fields and are not treated as equivalent.
- The v0.26 pilot results and the v0.18 public A/B CSVs are unchanged.
