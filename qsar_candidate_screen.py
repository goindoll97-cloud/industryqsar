#!/usr/bin/env python3
"""QSAR-focused research screening based on a Korean acute-registry snapshot and EPA data.

No fitted model or online calls. EPA structures support RDKit analogue similarity;
external EPA TEST oral-rat LD50 predictions, if separately provided, are the
QUANTITATIVE QSAR evidence. Similarity is never equated with predicted LD50.

Not found in the supplied registry != officially unregulated or non-toxic.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
import io
import json
import math
from pathlib import Path
import sys

from rdkit import Chem, DataStructs
from rdkit.Chem import Descriptors, rdMolDescriptors, rdFingerprintGenerator

from regulatory_screen import valid_cas, normalize_cas, evidence_relation
from prepare_epa_batch import get_cas_csv
from pilot import relation

MORGAN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
# Deliberately conservative coverage: these are not all structurally representable chemicals.
ORGANIC_ELEMENTS = {"H", "B", "C", "N", "O", "F", "P", "S", "Cl", "Br", "I", "Si"}
STRUCTURE_COLUMNS = {
    "cas": ("cas", "casrn", "cas_no", "cas no"),
    "smiles": ("qsar_ready_smiles", "qsar-ready smiles", "smiles", "canonical_smiles"),
    "dtxsid": ("dtxsid", "dsstox_substance_id"),
}
PRED_COLUMNS = ("cas", "ld50_value", "ld50_unit", "ad_status", "model_name")
CANDIDATE_COLUMNS = (
    "cas", "dtxsid", "smiles_as_exported", "canonical_smiles",
    "nearest_reference_cas", "nearest_reference_tanimoto",
    "n_registry_references_with_structures", "molecular_weight",
    "logp", "tpsa", "hbd", "hba",
    "epa_test_ld50_mg_kg", "epa_test_input_unit", "epa_test_ad_reported",
    "epa_test_model_name", "epa_test_threshold_relation",
    "structural_similarity_signal", "review_tier",
    "quality_flags", "registry_status", "source_boundary",
    "qsar_model_retrained", "legal_designation_determined",
    "candidate_universe_status", "original_smiles_from_epa",
    "kosha_oral_numeric_relation_reported",
    "kosha_oral_records", "kosha_reported_source", "qsar_msds_numeric_agreement",
)
REFERENCE_COLUMNS = ("cas", "registry_match", "structure_usable", "structure_reason",
                     "canonical_smiles", "dtxsid")


def read_csv(path: Path):
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp949")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise ValueError("CSV에 헤더가 없습니다: " + str(path))
    return [{str(k).strip(): (v or "").strip() for k, v in r.items() if k is not None}
            for r in reader]


def col(row: dict, aliases: tuple[str, ...]) -> str:
    normalized = {str(k).lower().replace("-", "").replace("_", "").replace(" ", ""): k for k in row}
    for alias in aliases:
        key = alias.lower().replace("-", "").replace("_", "").replace(" ", "")
        if key in normalized:
            return normalized[key]
    return ""


def load_registry(path: Path) -> set[str]:
    rows = read_csv(path)
    if not rows:
        raise ValueError("등록목록 CSV가 비어 있습니다.")
    cas_key = col(rows[0], STRUCTURE_COLUMNS["cas"])
    if not cas_key:
        raise ValueError("등록목록에 CAS 열이 없습니다.")
    # This workflow requires a prepared ACUTE-ONLY snapshot; not a mixed acute/chronic/eco table.
    # Fail closed when a class column exists and a non-acute entry is included.
    label_key = col(rows[0], ("유해성물질", "hazard_class", "designation_type"))
    registry = set()
    for row in rows:
        label = row.get(label_key, "") if label_key else ""
        if label and "인체급성" not in label and "humanacute" not in label.lower().replace(" ", ""):
            raise ValueError("인체급성 이외의 행이 있습니다. 급성 전용 목록만 입력하세요.")
        cas = normalize_cas(row.get(cas_key, ""))
        if cas and not valid_cas(cas):
            raise ValueError("등록목록의 CAS 검증 실패: " + cas[:50])
        if cas:
            registry.add(cas)
    if not registry:
        raise ValueError("유효한 인체급성 CAS가 없습니다.")
    return registry


def molecule(smiles: str):
    if not smiles:
        return None, "smiles_missing"
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, "rdkit_parse_failed"
    if len(Chem.GetMolFrags(mol)) != 1:
        return None, "multi_component_or_salt_requires_review"
    if not any(a.GetSymbol() == "C" for a in mol.GetAtoms()):
        return None, "inorganic_no_carbon_outside_pilot_scope"
    if any(a.GetSymbol() not in ORGANIC_ELEMENTS for a in mol.GetAtoms()):
        return None, "metal_or_unsupported_element_outside_pilot_scope"
    if Chem.GetFormalCharge(mol) != 0:
        return None, "charged_species_requires_review"
    return mol, "valid_single_component_organic"


def load_structures(path: Path):
    rows = read_csv(path)
    if not rows:
        raise ValueError("EPA 구조 CSV가 비어 있습니다.")
    cas_key = col(rows[0], STRUCTURE_COLUMNS["cas"])
    smiles_key = col(rows[0], STRUCTURE_COLUMNS["smiles"])
    raw_smiles_key = col(rows[0], ("smiles", "canonical_smiles"))
    dtxsid_key = col(rows[0], STRUCTURE_COLUMNS["dtxsid"])
    if not cas_key or not smiles_key:
        raise ValueError("EPA 구조 CSV에 CASRN 또는 SMILES/QSAR_READY_SMILES 열이 필요합니다.")
    loaded = {}
    collisions = set()
    invalid_ids = []
    for row in rows:
        cas = normalize_cas(row.get(cas_key, ""))
        if not valid_cas(cas):
            invalid_ids.append(cas[:50])
            continue
        smi = row.get(smiles_key, "")
        original_smi = row.get(raw_smiles_key, "") if raw_smiles_key else ""
        mol, status = molecule(smi)
        canonical = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True) if mol else ""
        if (mol is not None and original_smi and raw_smiles_key != smiles_key):
            original_mol = Chem.MolFromSmiles(original_smi)
            if original_mol is None or Chem.MolToSmiles(
                    original_mol, canonical=True, isomericSmiles=True) != canonical:
                # Standardization can neutralize/desalt/group individual components.
                # Never silently use a standardized neutral molecule as the actual
                # original CAS substance for structural similarity or molecular weight.
                mol, canonical = None, ""
                status = "epa_structure_standardization_difference_requires_review"
        entry = {"cas": cas, "mol": mol, "canonical": canonical,
                 "status": status, "smiles": smi, "original_smiles": original_smi,
                 "dtxsid": row.get(dtxsid_key, "") if dtxsid_key else ""}
        if cas in loaded:
            prior = loaded[cas]
            if prior["canonical"] != canonical or prior["status"] != status:
                collisions.add(cas)
            continue
        loaded[cas] = entry
    for cas in collisions:
        loaded[cas]["mol"] = None
        loaded[cas]["canonical"] = ""
        loaded[cas]["status"] = "conflicting_structures_same_cas"
    return loaded, {"input_rows": len(rows), "invalid_cas_rows": len(invalid_ids),
                    "conflicting_cas": len(collisions),
                    "accepted_unique_cas": len(loaded)}


def load_test_predictions(path: Path | None) -> dict:
    if path is None:
        return {}
    rows = read_csv(path)
    if not rows:
        raise ValueError("EPA TEST 예측 CSV가 비어 있습니다.")
    missing = set(PRED_COLUMNS) - set(rows[0])
    if missing:
        raise ValueError("EPA TEST 정규화 CSV 필수 열 누락: " + ", ".join(sorted(missing)))
    out = {}
    for row in rows:
        cas = normalize_cas(row["cas"])
        if not valid_cas(cas) or cas in out:
            raise ValueError("EPA TEST CAS 오류/중복: " + cas[:50])
        unit = row["ld50_unit"].strip().lower().replace(" ", "")
        if unit not in ("mg/kg", "-log10(mol/kg)"):
            raise ValueError("단위를 구분하세요: mg/kg 또는 -log10(mol/kg); CAS " + cas)
        ad = row["ad_status"].lower()
        if ad not in ("inside", "outside", "unknown"):
            raise ValueError("AD는 inside/outside/unknown 중 하나입니다. CAS " + cas)
        if not row["model_name"].strip():
            raise ValueError("QSAR 모델명과 버전을 기록하세요: " + cas)
        try:
            v = float(row["ld50_value"])
        except ValueError:
            raise ValueError("QSAR 예측값이 수치가 아닙니다: " + cas) from None
        if not math.isfinite(v) or (unit == "mg/kg" and v <= 0):
            raise ValueError("QSAR 예측값이 유효하지 않습니다: " + cas)
        out[cas] = {"value": v, "unit": unit, "ad": ad, "model": row["model_name"]}
    return out


def load_kosha_oral(path: Path | None) -> dict[str, list[dict]]:
    """Optional report-only overlay: raw KOSHA extraction is not validated experiment."""
    if path is None:
        return {}
    rows = read_csv(path)
    required = {"cas", "route", "extraction_status", "reported_metric",
                "qualifier", "value", "unit", "species_as_written", "reported_source"}
    if not rows or required - set(rows[0]):
        raise ValueError("KOSHA 인체독성 CSV 열 누락: " + ", ".join(sorted(required - set(rows[0]) if rows else required)))
    oral = {}
    for row in rows:
        cas = normalize_cas(row.get("cas", ""))
        if valid_cas(cas) and row["route"].lower() == "oral":
            oral.setdefault(cas, []).append(row)
    return oral


def reported_kosha_signal(records: list[dict]) -> tuple[str, str, list[str]]:
    if not records:
        return "not_reported", "", []
    relations = []
    flags = ["kosha_msds_not_independently_verified"]
    sources = set()
    for record in records:
        signal, problems = evidence_relation(record)
        relations.append(signal)
        flags.extend(problems)
        if record.get("reported_source"):
            sources.add(record["reported_source"])
    distinct = set(relations)
    if len(distinct) > 1 or len(records) > 1:
        flags.append("multiple_kosha_oral_records_review")
    return (next(iter(distinct)) if len(distinct) == 1 else "mixed",
            ";".join(sorted(sources)), flags)


def value_as_mgkg(predict: dict, mw: float):
    if predict["unit"] == "mg/kg":
        return predict["value"]
    # TEST's common output unit: -log10(mol/kg); mg/kg = 10^-p * MW(g/mol) * 1000
    if not 0 < mw < 10000:
        return None
    try:
        converted = 10.0 ** (-predict["value"]) * mw * 1000.0
    except OverflowError:
        return None
    return converted if math.isfinite(converted) and converted > 0 else None


def create_rankings(structures, registry, predictions, candidates=None, kosha_oral=None):
    kosha_oral = kosha_oral or {}
    references = [(cas, entry) for cas, entry in sorted(structures.items())
                  if cas in registry and entry["mol"] is not None]
    refs_fps = [MORGAN.GetFingerprint(entry["mol"]) for _, entry in references]
    reference_coverage = []
    for cas in sorted(registry):
        entry = structures.get(cas)
        reference_coverage.append({
            "cas": cas, "registry_match": "listed_in_supplied_acute_snapshot",
            "structure_usable": "true" if entry and entry["mol"] else "false",
            "structure_reason": (entry["status"] if entry else "not_in_epa_structure_export"),
            "canonical_smiles": (entry["canonical"] if entry else ""),
            "dtxsid": (entry["dtxsid"] if entry else ""),
        })
    candidates, rejected = [], []
    for cas, item in sorted(structures.items()):
        if cas in registry:
            continue
        if candidates is not None and cas not in candidates:
            continue
        if item["mol"] is None:
            rejected.append({"cas": cas, "dtxsid": item["dtxsid"],
                             "smiles": item["smiles"],
                             "original_smiles": item["original_smiles"],
                             "reason": item["status"]})
            continue
        mol = item["mol"]
        best_cas = ""
        similarity = None
        same_structure = False
        if refs_fps:
            scores = DataStructs.BulkTanimotoSimilarity(MORGAN.GetFingerprint(mol), refs_fps)
            top_index = max(range(len(scores)), key=lambda i: scores[i])
            best_cas, ref = references[top_index]
            similarity = scores[top_index]
            same_structure = item["canonical"] == ref["canonical"]
        mw = Descriptors.MolWt(mol)
        predictor = predictions.get(cas)
        k_records = kosha_oral.get(cas, [])
        k_relation, k_source, k_flags = reported_kosha_signal(k_records)
        ld = value_as_mgkg(predictor, mw) if predictor else None
        qrel = relation(str(ld)) if ld is not None else "not_available"
        ad = predictor["ad"] if predictor else "not_provided"
        flags = list(k_flags)
        numeric_agreement = "not_assessable"
        if (predictor and ad == "inside" and qrel in ("meets", "above")
                and k_relation in ("meets", "above")):
            numeric_agreement = "agree" if qrel == k_relation else "disagree"
            if numeric_agreement == "disagree":
                flags.append("qsar_msds_numeric_discordance_sources_not_independent")
        if same_structure:
            flags.append("same_canonical_structure_as_registry_cas_review_identifiers")
        if not refs_fps:
            flags.append("no_reference_structures_available")
        if predictor and predictor["ad"] != "inside":
            flags.append("qsar_applicability_domain_not_confirmed_inside")
        if predictor and ld is None:
            flags.append("qsar_conversion_unavailable")
        if predictor:
            flags.append("qsar_predictions_may_overlap_msds_or_training_data")
        # Similarity is ANALOGUE support only, never an LD50 estimate or model AD.
        structure_signal = ("identical_structure_review" if same_structure
                            else "high_similarity_review_only" if similarity is not None and similarity >= 0.75
                            else "not_high_similarity")
        if same_structure:
            tier = "IDENTIFIER_REVIEW_FIRST"
        elif qrel == "meets" and ad == "inside":
            tier = "P1_QSAR_ORAL_SIGNAL_REPORTED_INSIDE_AD"
        elif qrel == "meets":
            tier = "P2_QSAR_SIGNAL_AD_UNCERTAIN"
        elif k_relation == "meets":
            tier = "P2_KOSHA_REPORTED_ORAL_SIGNAL_UNVERIFIED"
        elif structure_signal == "high_similarity_review_only":
            tier = "P3_ANALOGUE_HYPOTHESIS_NO_LD50_INFERENCE"
        else:
            tier = "P4_NO_CONFIRMED_QSAR_OR_STRUCTURE_SIGNAL_NOT_SAFE"
        candidates.append({
            "cas": cas, "dtxsid": item["dtxsid"],
            "smiles_as_exported": item["smiles"],
            "canonical_smiles": item["canonical"],
            "nearest_reference_cas": best_cas,
            "nearest_reference_tanimoto": f"{similarity:.4f}" if similarity is not None else "",
            "n_registry_references_with_structures": str(len(refs_fps)),
            "molecular_weight": f"{mw:.3f}",
            "logp": f"{Descriptors.MolLogP(mol):.4f}",
            "tpsa": f"{rdMolDescriptors.CalcTPSA(mol):.3f}",
            "hbd": str(rdMolDescriptors.CalcNumHBD(mol)),
            "hba": str(rdMolDescriptors.CalcNumHBA(mol)),
            "epa_test_ld50_mg_kg": f"{ld:.6g}" if ld is not None else "",
            "epa_test_input_unit": predictor["unit"] if predictor else "",
            "epa_test_ad_reported": ad,
            "epa_test_model_name": predictor["model"] if predictor else "",
            "epa_test_threshold_relation": qrel,
            "structural_similarity_signal": structure_signal,
            "review_tier": tier,
            "quality_flags": ";".join(flags),
            "registry_status": "not_in_supplied_acute_snapshot_UNVERIFIED",
            "source_boundary": "EPA_STRUCTURES_AND_TEST_ONLY_NOT_US_REGULATORY_DESIGNATION",
            "qsar_model_retrained": "false",
            "legal_designation_determined": "false",
            "original_smiles_from_epa": item["original_smiles"],
            "candidate_universe_status": ("provided_domestic_candidate_universe"
                                          if candidates is not None else "EPA_EXPORT_ONLY_NOT_DOMESTIC_UNIVERSE"),
            "kosha_oral_numeric_relation_reported": k_relation,
            "kosha_oral_records": str(len(k_records)),
            "kosha_reported_source": k_source,
            "qsar_msds_numeric_agreement": numeric_agreement,
        })
    tier_order = {"IDENTIFIER_REVIEW_FIRST": 0, "P1_QSAR_ORAL_SIGNAL_REPORTED_INSIDE_AD": 1,
                  "P2_QSAR_SIGNAL_AD_UNCERTAIN": 2,
                  "P2_KOSHA_REPORTED_ORAL_SIGNAL_UNVERIFIED": 2,
                  "P3_ANALOGUE_HYPOTHESIS_NO_LD50_INFERENCE": 3,
                  "P4_NO_CONFIRMED_QSAR_OR_STRUCTURE_SIGNAL_NOT_SAFE": 4}
    candidates.sort(key=lambda r: (tier_order[r["review_tier"]], -float(r["nearest_reference_tanimoto"] or 0), r["cas"]))
    return reference_coverage, candidates, rejected


def safe_cell(value):
    text = str(value) if value is not None else ""
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def output_csv(path: Path, data: list[dict], fields):
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in data:
            writer.writerow({k: safe_cell(row.get(k, "")) for k in fields})


def run(structures_path: Path, registry_path: Path, predictions_path: Path | None, out: Path,
        candidates_path: Path | None = None, kosha_endpoints_path: Path | None = None):
    registry = load_registry(registry_path)
    structures, import_audit = load_structures(structures_path)
    predictions = load_test_predictions(predictions_path)
    candidates = set(get_cas_csv(candidates_path)) if candidates_path is not None else None
    if candidates is not None and not candidates:
        raise ValueError("후보집단 CSV에 유효한 CAS가 없습니다.")
    kosha_oral = load_kosha_oral(kosha_endpoints_path)
    refs, candidate_rows, rejected = create_rankings(structures, registry, predictions, candidates, kosha_oral)
    out.mkdir(parents=True, exist_ok=True)
    output_csv(out / "qsar_candidates.csv", candidate_rows, CANDIDATE_COLUMNS)
    output_csv(out / "evidence_manual_review.csv",
               [r for r in candidate_rows if r["qsar_msds_numeric_agreement"] == "disagree"
                or r["review_tier"] in ("IDENTIFIER_REVIEW_FIRST",
                                       "P2_QSAR_SIGNAL_AD_UNCERTAIN",
                                       "P2_KOSHA_REPORTED_ORAL_SIGNAL_UNVERIFIED")],
               CANDIDATE_COLUMNS)
    output_csv(out / "registry_structure_coverage.csv", refs, REFERENCE_COLUMNS)
    if candidates is not None:
        output_csv(out / "candidate_structure_missing.csv",
                   [{"cas": cas, "reason": "not_in_epa_structure_export"}
                    for cas in sorted(candidates - registry - set(structures))],
                   ("cas", "reason"))
    output_csv(out / "structure_manual_review.csv", rejected,
               ("cas", "dtxsid", "smiles", "original_smiles", "reason"))
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "single_component_neutral_organic_rat_oral_ld50",
        "selected_external_source": "US EPA CompTox structures and EPA TEST existing QSAR",
        "domestic_acute_registry_cas_count": len(registry),
        "registered_reference_structures_available": sum(x["structure_usable"] == "true" for x in refs),
        "candidate_structures_usable_not_in_supplied_snapshot": len(candidate_rows),
        "nonreference_structure_manual_review": len(rejected),
        "external_qsar_predictions_loaded": len(predictions),
        "kosha_oral_reported_compounds_loaded": len(kosha_oral),
        "candidate_universe_provided": candidates is not None,
        "domestic_candidate_universe_size": len(candidates - registry) if candidates is not None else None,
        "domestic_candidate_universe_missing_from_epa_export": len(candidates - registry - set(structures)) if candidates is not None else None,
        "qsar_kosha_numeric_disagreement_count": sum(
            x["qsar_msds_numeric_agreement"] == "disagree" for x in candidate_rows),
        "candidate_priority_counts": dict(Counter(x["review_tier"] for x in candidate_rows)),
        "epa_import_audit": import_audit,
        "important_limitations": [
            "Screened candidates are only absent from the user supplied acute registry snapshot; not established as legally unregulated.",
            "EPA CompTox is not a US regulatory designated chemicals list.",
            "RDKit Tanimoto similarity is NOT a QSAR LD50 prediction or an AD determination.",
            "Model AD flags come from the user's TEST report and are not independently validated.",
            "TEST common output of -log10(mol/kg) is converted with RDKit molecular weight; verify structure identity and original TEST units.",
            "Metal salts, multi-component and charged substances are outside this pilot and require a separate chemical approach.",
            "If CompTox original SMILES and QSAR-ready SMILES differ after canonicalization, the structure is excluded for identity review.",
            "A Korean industrial-chemical universe must be separately defined to claim nationwide coverage.",
            "KOSHA MSDS is user-supplied reported evidence, not independently verified experimental toxicity.",
            "Missing EPA structures and excluded metal/salt chemicals must not be labelled nonhazardous.",
            "No binary nonhazard labels, model fitting, toxicology study validation, or legal designation decisions.",
        ],
    }
    (out / "qsar_screen_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(out), "references_with_structures": summary["registered_reference_structures_available"],
                      "candidates": len(candidate_rows), "priority_counts": summary["candidate_priority_counts"]},
                     ensure_ascii=False, indent=2))
    return summary


def main():
    p = argparse.ArgumentParser(description="EPA TEST oral-rat QSAR + RDKit Korean acute-registry analogue screen")
    p.add_argument("--structures", type=Path, required=True, help="EPA CompTox export CSV: cas/CASRN and smiles/QSAR_READY_SMILES")
    p.add_argument("--registry", type=Path, required=True, help="Prepared acute-only Korean registry CSV")
    p.add_argument("--predictions", type=Path, help="Optional manually normalized EPA TEST predictions; must include units and AD")
    p.add_argument("--candidates", type=Path, help="Optional domestic candidate CAS CSV; filters EPA export to Korean candidate universe")
    p.add_argument("--kosha-endpoints", type=Path, help="Optional existing KOSHA human_acute_endpoints.csv; oral evidence overlay only")
    p.add_argument("--out", type=Path, default=Path("outputs/epa_qsar_pilot"))
    args = p.parse_args()
    try:
        run(args.structures, args.registry, args.predictions, args.out, args.candidates, args.kosha_endpoints)
    except (OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
