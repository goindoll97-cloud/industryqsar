#!/usr/bin/env python3
"""Stage 2: audit KOSHA human-acute evidence and match a user-supplied regulatory snapshot.

No toxicity model training, no MSDS API requests, no automatic legal determination.
Only oral rodent LD50 <= 300 mg/kg is compared quantitatively; dermal and inhalation
are retained as human-health data requiring separate regulatory endpoint checks.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone, date
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile

from pilot import relation

CAS_RE = re.compile(r"^\d{2,7}-\d{2}-\d$")
REGISTRY_CAS_NAMES = ("cas", "cas no", "cas no.", "cas번호", "cas no ", "cas_no", "casrn")
REGISTRY_CLASS_NAMES = ("유해성물질", "유해성물질구분", "classification", "designation_type", "hazard_class", "규제구분")
REGISTRY_ID_NAMES = ("고유번호", "notice_id", "designation_id", "id")
ORAL_SPECIES = {"rat", "mouse", "rodent", "랫드", "마우스", "설치류", "쥐"}
INPUTS = ("kosha_search_results.csv", "human_acute_endpoints.csv")
ENDPOINT_FIELDS = ("cas", "route", "extraction_status", "reported_metric", "qualifier", "value", "unit",
                   "species_as_written", "reported_source", "duration_hours", "raw_detail")
REGISTRY_AUDIT_COLS = [
    "source_row", "source_cas", "normalized_cas", "registry_acute_label",
    "notice_id", "substance_name", "mixture_cutoff_original",
    "cas_matching_status", "user_supplied_scope"
]
SCREEN_COLS = [
    "cas", "kosha_search_status", "designated_acute_registry_status",
    "registry_notice_ids", "registry_scope", "oral_records", "dermal_records",
    "inhalation_records", "oral_numeric_relation", "oral_source_metadata",
    "qsar_numeric_relation", "qsar_ad", "qsar_model",
    "screening_priority", "review_reason", "quality_flags",
    "legal_designation_verified", "model_training_performed",
]
PRIORITY = {
    "reference_listed": "REFERENCE_ALREADY_LISTED",
    "P1_oral_signal": "P1_ORAL_NUMERIC_SIGNAL_REVIEW",
    "P2_discordance": "P2_EVIDENCE_DISCORDANCE_REVIEW",
    "P2_qsar": "P2_QSAR_SIGNAL_REVIEW",
    "P2_unverifiable": "P2_DATA_QUALITY_OR_ENDPOINT_REVIEW",
    "P3_other_routes": "P3_DERMAL_INHALATION_UNASSESSED",
    "P4_oral_above": "P4_ORAL_ONLY_NUMERIC_CRITERION_NOT_MET",
    "P5_no_data": "P5_DATA_GAP",
}


def read_csv_bytes(raw: bytes, required=()) -> list[dict[str, str]]:
    try:
        txt = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        txt = raw.decode("cp949")
    reader = csv.DictReader(io.StringIO(txt, newline=""))
    names = [str(x or "").strip() for x in (reader.fieldnames or [])]
    if not names:
        raise ValueError("CSV 헤더가 없습니다.")
    missing = set(required) - set(names)
    if missing:
        raise ValueError("CSV 필수 열 누락: " + ", ".join(sorted(missing)))
    return [{str(k).strip(): (v or "").strip() for k, v in r.items() if k is not None}
            for r in reader]


def load_batch(batch: Path | None, batch_zip: Path | None):
    if batch_zip:
        with zipfile.ZipFile(batch_zip) as z:
            files = {}
            for name in INPUTS + ("kosha_audit.json",):
                candidates = [x for x in z.infolist()
                              if not x.is_dir() and x.filename.replace("\\", "/").split("/")[-1] == name]
                if len(candidates) > 1:
                    raise ValueError("ZIP 내부 동일 파일명이 중복됩니다: " + name)
                if candidates:
                    f = candidates[0]
                    if f.file_size > 10_000_000:
                        raise ValueError("과도하게 큰 입력 파일: " + name)
                    files[name] = z.read(f)
        missing = [x for x in INPUTS if x not in files]
        if missing:
            raise ValueError("ZIP 입력파일 누락: " + ", ".join(missing))
    else:
        if batch is None:
            raise ValueError("--batch 또는 --batch-zip을 지정하세요.")
        files = {name: (batch / name).read_bytes() for name in INPUTS}
        audit_path = batch / "kosha_audit.json"
        if audit_path.exists():
            files["kosha_audit.json"] = audit_path.read_bytes()
    search = read_csv_bytes(files["kosha_search_results.csv"], ("queried_cas", "search_status"))
    endpoints = read_csv_bytes(files["human_acute_endpoints.csv"], ENDPOINT_FIELDS)
    audit = json.loads(files["kosha_audit.json"].decode("utf-8-sig")) if "kosha_audit.json" in files else None
    return search, endpoints, audit


def normalize_cas(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").strip())


def valid_cas(value: str) -> bool:
    cas = normalize_cas(value)
    if not CAS_RE.fullmatch(cas):
        return False
    head, middle, digit = cas.split("-")
    base = head + middle
    return sum((i + 1) * int(d) for i, d in enumerate(reversed(base))) % 10 == int(digit)


def registry_meta(meta_file: Path) -> dict:
    meta = json.loads(meta_file.read_text(encoding="utf-8-sig"))
    scope = meta.get("coverage")
    if scope not in ("partial", "complete_acute_list"):
        raise ValueError("지정목록 metadata.coverage는 partial 또는 complete_acute_list여야 합니다.")
    url = str(meta.get("source_url", "")).strip()
    provenance = meta.get("provenance_status", "")
    if not url.startswith(("https://", "http://")):
        # A user-uploaded workbook is NOT sufficient to assert official provenance.
        # Allow its preliminary CAS overlap analysis, but keep provenance unresolved.
        if not (url == "" and provenance == "unverified_user_upload"
                and str(meta.get("source_file_name", "")).strip()):
            raise ValueError("공식 출처 URL을 넣거나, 원본 파일명과 provenance_status=unverified_user_upload를 명시하세요.")
    meta["provenance_status"] = ("source_url_user_supplied_unverified" if url else
                                 "unverified_user_upload")
    try:
        date.fromisoformat(meta["snapshot_date"])
    except (KeyError, ValueError, TypeError):
        raise ValueError("metadata.snapshot_date는 YYYY-MM-DD 형식이어야 합니다.") from None
    if type(meta.get("acute_only")) is not bool:
        raise ValueError("metadata.acute_only는 true/false로 명시해야 합니다.")
    return meta


def find_header(row: dict, options) -> str:
    aliases = {re.sub(r"[\s_.]", "", name.lower()) for name in options}
    for key in row:
        if re.sub(r"[\s_.]", "", key.lower()) in aliases:
            return key
    return ""


def is_acute_type(value: str) -> bool:
    s = re.sub(r"\s+", "", value).lower()
    return "인체급성" in s or "humanacute" in s or "acutehuman" in s


def load_registry(path: Path | None, meta_path: Path | None):
    if path is None:
        if meta_path:
            raise ValueError("--registry-meta는 --registry와 함께 사용해야 합니다.")
        return {}, None, {"loaded": False, "status": "not_provided"}
    if meta_path is None:
        raise ValueError("--registry를 지정하면 출처·기준일을 기록한 --registry-meta도 필요합니다.")
    meta = registry_meta(meta_path)
    data = read_csv_bytes(path.read_bytes())
    if not data:
        raise ValueError("지정목록 CSV에 행이 없습니다.")
    cas_col = find_header(data[0], REGISTRY_CAS_NAMES)
    class_col = find_header(data[0], REGISTRY_CLASS_NAMES)
    id_col = find_header(data[0], REGISTRY_ID_NAMES)
    if not cas_col:
        raise ValueError("지정목록에서 CAS 열을 식별하지 못했습니다.")
    if not meta["acute_only"] and not class_col:
        raise ValueError("혼합 지정목록에는 유해성물질 구분 열이 필요합니다.")
    mapped = defaultdict(list)
    ignored_nonacute = 0
    unmapped_acute_rows = 0
    bad_cas = []
    for i, row in enumerate(data, start=2):
        if class_col and not is_acute_type(row.get(class_col, "")):
            ignored_nonacute += 1
            continue
        cas = normalize_cas(row.get(cas_col, ""))
        if not cas:
            # The official inventory may have group entries without a CAS.
            # Never infer that a nonmatched CAS is certainly not covered.
            unmapped_acute_rows += 1
            continue
        if not valid_cas(cas):
            bad_cas.append(f"{i}:{cas[:30]}")
            continue
        mapped[cas].append((row.get(id_col, "") if id_col else "").strip())
    if bad_cas:
        raise ValueError("인체급성 지정목록 CAS 오류. 자동 일치 처리하지 않습니다: " + ", ".join(bad_cas[:8]))
    if not mapped:
        raise ValueError("유효한 인체급성 지정 물질이 없습니다. 목록의 구분명과 범위를 확인하세요.")
    declared_coverage = meta["coverage"]
    meta = dict(meta)
    if unmapped_acute_rows and declared_coverage == "complete_acute_list":
        # CAS-less group entries make an exact-CAS-only registry incomplete.
        meta["coverage"] = "partial"
    diag = {
        "loaded": True,
        "status": "USER_SUPPLIED_SNAPSHOT_UNVERIFIED_COVERAGE",
        "source_url": meta["source_url"], "source_file_name": meta.get("source_file_name", ""),
        "snapshot_date": meta["snapshot_date"],
        "snapshot_date_basis": meta.get("snapshot_date_basis", "user_supplied_not_officially_verified"),
        "provenance_status": meta["provenance_status"],
        "coverage_declared_by_user": declared_coverage,
        "effective_cas_lookup_coverage": meta["coverage"],
        "coverage_downgraded_due_to_casless_groups": meta["coverage"] != declared_coverage,
        "unmapped_acute_rows_no_cas": unmapped_acute_rows,
        "acute_only_declared_by_user": meta["acute_only"],
        "input_rows": len(data), "acute_distinct_cas": len(mapped),
        "nonacute_rows_ignored": ignored_nonacute,
        "duplicate_acute_cas": sum(len(vals) > 1 for vals in mapped.values()),
    }
    return mapped, meta, diag


def load_qsar(path: Path | None) -> dict[str, dict]:
    if path is None:
        return {}
    rows = read_csv_bytes(path.read_bytes(), ("cas", "qsar_oral_ld50", "qsar_ad", "model_name"))
    out = {}
    for row in rows:
        cas = normalize_cas(row["cas"])
        if not valid_cas(cas):
            raise ValueError("QSAR CSV에 잘못된 CAS가 있습니다: " + cas[:30])
        if cas in out:
            raise ValueError("QSAR CSV의 CAS 중복: " + cas)
        out[cas] = row
    return out


def evidence_relation(row: dict) -> tuple[str, list[str]]:
    issues = []
    if row.get("route") != "oral":
        return "not_assessed", issues
    if row.get("extraction_status") != "parsed_unverified":
        return "not_parsed", ["oral_extraction_unverified"]
    if row.get("reported_metric", "").upper() != "LD50" or row.get("unit", "").lower().replace(" ", "") != "mg/kg":
        return "endpoint_unit_mismatch", ["oral_metric_or_unit_mismatch"]
    species = row.get("species_as_written", "").lower().strip()
    if species not in ORAL_SPECIES:
        issues.append("rodent_species_unconfirmed")
    if not row.get("reported_source", "").strip():
        issues.append("original_source_not_identified")
    value = row.get("value", "")
    op = row.get("qualifier", "=")
    if op not in ("=", "<", ">", "<=", ">=", "≤", "≥"):
        return "invalid", issues + ["invalid_inequality"]
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "invalid", issues + ["invalid_numeric_value"]
    if not math.isfinite(v) or v <= 0:
        return "invalid", issues + ["invalid_numeric_value"]
    result = relation(("" if op == "=" else op) + str(v))
    if result not in ("meets", "above"):
        issues.append("uncertain_inequality")
    return result, issues


def classify_registry(cas: str, mapped: dict, meta: dict | None) -> tuple[str, str]:
    if meta is None:
        return "registry_not_provided", ""
    if cas in mapped:
        return "listed_in_supplied_acute_registry", ";".join(sorted(set(x for x in mapped[cas] if x)))
    if meta["coverage"] == "complete_acute_list":
        return "not_found_in_claimed_complete_snapshot", ""
    return "not_found_in_partial_snapshot_unknown", ""


def sort_key(row: dict) -> tuple:
    levels = {"P1_oral_signal": 0, "P2_discordance": 1, "P2_qsar": 2,
              "P2_unverifiable": 3, "P3_other_routes": 4,
              "P4_oral_above": 5, "P5_no_data": 6, "reference_listed": 7}
    return levels.get(row["screening_priority"], 99), row["cas"]


def assess(search: list[dict], endpoints: list[dict], registry, meta, qsar: dict):
    grouped = defaultdict(list)
    for endpoint in endpoints:
        grouped[normalize_cas(endpoint.get("cas", ""))].append(endpoint)
    output = []
    endpoint_qa = []
    seen = set()
    for lookup in search:
        cas = normalize_cas(lookup["queried_cas"])
        duplicate_lookup = cas in seen
        seen.add(cas)
        flags = []
        if not valid_cas(cas):
            flags.append("invalid_cas")
        if duplicate_lookup:
            flags.append("duplicate_cas_in_search")
        status = lookup.get("search_status", "")
        if status != "exact_cas_match":
            flags.append("kosha_cas_match_not_verified")
        matches = grouped.get(cas, [])
        routes = Counter(x.get("route") for x in matches)
        oral = [e for e in matches if e.get("route") == "oral"]
        relations = []
        metadata = []
        for e in matches:
            rel, issues = evidence_relation(e)
            endpoint_qa.append(dict(e, endpoint_numeric_relation=rel,
                                    endpoint_quality_flags=";".join(sorted(set(issues))),
                                    legal_test_evidence_verified="false"))
            if e.get("route") == "oral":
                relations.append(rel)
                metadata.append(e.get("reported_source", ""))
                flags.extend(issues)
        if len(oral) > 1:
            flags.append("multiple_oral_records_check_conflict")
        if not oral:
            flags.append("oral_not_reported")
        if any(e.get("extraction_status") != "parsed_unverified" for e in matches):
            flags.append("unparsed_human_endpoint")
        if any(e.get("route") == "inhalation" and e.get("duration_hours", "") != "4"
               for e in matches):
            flags.append("inhalation_nonfour_hour_or_unknown")
        if any(e.get("route") in ("dermal", "inhalation") for e in matches):
            flags.append("other_routes_extracted_not_regulatorily_assessed")
        reg_status, notice_ids = classify_registry(cas, registry, meta)
        if reg_status == "registry_not_provided":
            flags.append("official_acute_registry_not_provided")
        elif reg_status == "not_found_in_partial_snapshot_unknown":
            flags.append("partial_registry_cannot_establish_absence")
        else:
            flags.append("registry_exact_cas_match_only_verify_group_scope")
        oral_signal = "meets" in relations
        oral_above = bool(oral) and set(relations) == {"above"}
        oral_ambiguous = bool(oral) and not oral_signal and not oral_above
        qs = qsar.get(cas, {})
        qsar_ad = qs.get("qsar_ad", "").lower().strip()
        qsar_raw = qs.get("qsar_oral_ld50", "")
        qsar_result = relation(qsar_raw) if qsar_raw else "not_provided"
        if qs and qsar_ad != "inside":
            flags.append("qsar_ad_not_confirmed_inside")
        qsar_usable = bool(qs) and qsar_ad == "inside" and qsar_result in ("meets", "above")
        disagreement = qsar_usable and (
            (oral_signal and qsar_result == "above") or (oral_above and qsar_result == "meets"))
        if disagreement:
            flags.append("msds_and_qsar_disagree_check_independence")
        if status != "exact_cas_match":
            flags.append("do_not_prioritize_until_cas_verified")
        if reg_status == "listed_in_supplied_acute_registry":
            code = "reference_listed"
        elif status != "exact_cas_match" or not valid_cas(cas):
            code = "P2_unverifiable"
        elif oral_signal:
            code = "P1_oral_signal"
        elif disagreement:
            code = "P2_discordance"
        elif qsar_usable and qsar_result == "meets":
            code = "P2_qsar"
        elif oral_ambiguous or any("not_parsed" == r or "endpoint_unit_mismatch" == r or r == "invalid" for r in relations):
            code = "P2_unverifiable"
        elif routes["dermal"] or routes["inhalation"]:
            code = "P3_other_routes"
        elif oral_above:
            code = "P4_oral_above"
        else:
            code = "P5_no_data"
        if code == "P1_oral_signal" and any(x in flags for x in ("rodent_species_unconfirmed", "original_source_not_identified")):
            flags.append("high_signal_requires_source_species_validation")
        if qs and qsar_raw and qsar_result in ("invalid", "ambiguous"):
            flags.append("qsar_numeric_not_suitable_for_screening")
        output.append({
            "cas": cas,
            "kosha_search_status": status,
            "designated_acute_registry_status": reg_status,
            "registry_notice_ids": notice_ids,
            "registry_scope": meta["coverage"] if meta else "not_provided",
            "oral_records": str(routes["oral"]),
            "dermal_records": str(routes["dermal"]),
            "inhalation_records": str(routes["inhalation"]),
            "oral_numeric_relation": "mixed" if len(set(relations)) > 1 else (relations[0] if relations else "not_reported"),
            "oral_source_metadata": ";".join(sorted(set(s for s in metadata if s))),
            "qsar_numeric_relation": qsar_result,
            "qsar_ad": qsar_ad or "not_provided",
            "qsar_model": qs.get("model_name", ""),
            "screening_priority": code,
            "review_reason": PRIORITY[code],
            "quality_flags": ";".join(sorted(set(flags))),
            "legal_designation_verified": "false",
            "model_training_performed": "false",
        })
    return sorted(output, key=sort_key), endpoint_qa


def registry_row_audit(registry_path: Path, all_screened_cas: set[str]) -> list[dict]:
    """Preserve unmatched group entries for human review and trace matched CAS."""
    rows = read_csv_bytes(registry_path.read_bytes())
    if not rows:
        return []
    cas_col = find_header(rows[0], REGISTRY_CAS_NAMES)
    type_col = find_header(rows[0], REGISTRY_CLASS_NAMES)
    id_col = find_header(rows[0], REGISTRY_ID_NAMES)
    results = []
    for n, record in enumerate(rows, 2):
        if type_col and not is_acute_type(record.get(type_col, "")):
            continue
        cas = normalize_cas(record.get(cas_col, "")) if cas_col else ""
        valid = valid_cas(cas)
        status = ("unmapped_group_or_invalid_cas" if not valid
                  else "cas_matched_to_kosha_batch" if cas in all_screened_cas
                  else "valid_cas_not_in_kosha_batch")
        results.append({
            "source_row": record.get("원본_NO", str(n)),
            "source_cas": record.get("source_cas_as_written", cas),
            "normalized_cas": cas if valid else "",
            "registry_acute_label": record.get(type_col, "") if type_col else "",
            "notice_id": record.get(id_col, "") if id_col else "",
            "substance_name": record.get("국문명", record.get("영문명", "")),
            "mixture_cutoff_original": record.get("유해특성분류 및 혼합물 함량기준(%)", ""),
            "cas_matching_status": status,
            "user_supplied_scope": "unverified_uploaded_registry",
        })
    return results


def safe_cell(key, value):
    txt = str(value) if value is not None else ""
    if (key in ("qualifier",) and txt == "=") or (key == "source_cas" and txt == "-"):
        return txt
    if txt.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + txt
    return txt


def write_csv(path: Path, records: list[dict], columns: list[str]):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            writer.writerow({k: safe_cell(k, row.get(k, "")) for k in columns})


def run(batch: Path | None, batch_zip: Path | None, out: Path,
        registry_path: Path | None, meta_path: Path | None, qsar_path: Path | None):
    search, endpoints, audit = load_batch(batch, batch_zip)
    registry, meta, reg_diag = load_registry(registry_path, meta_path)
    qsar = load_qsar(qsar_path)
    screening, endpoint_qa = assess(search, endpoints, registry, meta, qsar)
    if not screening:
        raise ValueError("KOSHA 검색 대상이 비어 있습니다.")
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "screening_priorities.csv", screening, SCREEN_COLS)
    write_csv(out / "review_queue.csv",
              [r for r in screening if r["screening_priority"] not in ("reference_listed", "P4_oral_above")],
              SCREEN_COLS)
    # A registry-listed compound should not disappear from evidence QA.
    # Reference-list membership and oral toxicity evidence are separate axes.
    write_csv(out / "reference_evidence_audit.csv",
              [r for r in screening if r["designated_acute_registry_status"] == "listed_in_supplied_acute_registry"],
              SCREEN_COLS)
    endpoint_columns = list(dict.fromkeys(list(endpoints[0]) + ["endpoint_numeric_relation", "endpoint_quality_flags", "legal_test_evidence_verified"])) if endpoints else list(ENDPOINT_FIELDS) + ["endpoint_numeric_relation", "endpoint_quality_flags", "legal_test_evidence_verified"]
    write_csv(out / "endpoint_quality_review.csv", endpoint_qa, endpoint_columns)
    write_csv(out / "manual_endpoint_review.csv",
              [r for r in endpoint_qa if r.get("extraction_status", "").startswith("manual_review_")],
              endpoint_columns)
    registry_qa = (registry_row_audit(registry_path, {r["cas"] for r in screening})
                   if registry_path else [])
    if registry_path:
        write_csv(out / "registry_cas_audit.csv", registry_qa, REGISTRY_AUDIT_COLS)
    missing = [x for x in screening if x["designated_acute_registry_status"] == "registry_not_provided"]
    cross_tab: dict[str, dict[str, int]] = {}
    for row in screening:
        key = row["designated_acute_registry_status"]
        rel = row["oral_numeric_relation"]
        cross_tab.setdefault(key, {})
        cross_tab[key][rel] = cross_tab[key].get(rel, 0) + 1
    summary = {
        "research_scope": "human_acute_only; quantitative comparison: rodent oral LD50 <= 300 mg/kg only",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_compounds": len(screening),
        "extracted_human_endpoints": len(endpoint_qa),
        "route_record_counts": dict(Counter(x.get("route", "") for x in endpoint_qa)),
        "extraction_status_counts": dict(Counter(x.get("extraction_status", "") for x in endpoint_qa)),
        "oral_numeric_relation_counts": dict(Counter(x["oral_numeric_relation"] for x in screening)),
        "registry_vs_oral_numeric_relation": cross_tab,
        "registry_listed_evidence_audit_rows": sum(
            x["designated_acute_registry_status"] == "listed_in_supplied_acute_registry" for x in screening),
        "manual_endpoint_review_rows": sum(
            x.get("extraction_status", "").startswith("manual_review_") for x in endpoint_qa),
        "kosha_no_hit_count": sum(x["kosha_search_status"] == "no_hit" for x in screening),
        "priority_counts": dict(Counter(x["screening_priority"] for x in screening)),
        "registry_diagnostics": reg_diag,
        "registry_cas_audit_rows": len(registry_qa),
        "registry_cas_manual_review_rows": sum(
            x["cas_matching_status"] == "unmapped_group_or_invalid_cas" for x in registry_qa),
        "registry_missing_for_all": len(missing) == len(screening),
        "registry_snapshot_is_officially_verified": False,
        "qsar_records_supplied": len(qsar),
        "kosha_source_audit_present": bool(audit),
        "kosha_source_fetched_at_utc": audit.get("fetched_at_utc", "") if audit else "",
        "official_registry_independently_verified": False,
        "official_regulatory_designation_automatically_determined": False,
        "toxicology_experimental_provenance_verified": False,
        "notes": [
            "공식 지정고시 CAS와 명칭, 염류·수화물·혼합물·함량 및 시행일은 별도 검증 필요.",
            "사용자 제공 목록에 CAS가 없다는 사실은 비규제·무해 판정을 의미하지 않음.",
            "경피·흡입 자료는 확보 여부만 표시하며 법적 수치기준은 아직 적용하지 않음.",
            "MSDS LD50은 시험 원출처가 독립 검증되지 않은 참고값.",
            "QSAR가 제공되지 않아도 실행되며 QSAR는 인체급성 경구 LD50만 보조.",
            "미지정 물질을 독성의 음성 정답으로 간주하지 말 것.",
        ],
    }
    (out / "screening_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output_dir": str(out), "input_compounds": len(screening),
                      "priority_counts": summary["priority_counts"],
                      "registry_status": reg_diag["status"]}, ensure_ascii=False, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description="KOSHA human-acute regulatory research prioritization stage 2")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--batch", type=Path, help="Existing outputs/kosha_batch folder")
    group.add_argument("--batch-zip", type=Path, help="Existing kosha_batch.zip, no unpacking needed")
    parser.add_argument("--registry", type=Path, help="Official acute designation CSV snapshot, user supplied")
    parser.add_argument("--registry-meta", type=Path, help="Provenance + scope JSON snapshot metadata")
    parser.add_argument("--qsar", type=Path, help="Optional external oral rat LD50 prediction CSV")
    parser.add_argument("--out", type=Path, default=Path("outputs/regulatory_step2"))
    args = parser.parse_args()
    try:
        run(args.batch, args.batch_zip, args.out, args.registry, args.registry_meta, args.qsar)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
