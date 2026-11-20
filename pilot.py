#!/usr/bin/env python3
"""Research pilot: acute oral LD50 regulatory screening, not a designation engine."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
import requests

THRESHOLD = 300.0  # mg/kg; rodent acute oral LD50, K-REACH Enforcement Decree Annex 1
LAW_QUERY = "화학물질의 등록 및 평가 등에 관한 법률 시행령"
LAW_SOURCE = "https://www.law.go.kr/법령별표서식/(화학물질의 등록 및 평가 등에 관한 법률 시행령,20260512,별표1)"
REQUIRED = ("compound_id", "name", "cas", "substance_type", "designation_status",
            "designation_status_source", "msds_oral_ld50_raw", "msds_basis",
            "msds_species", "msds_route", "msds_unit", "msds_source",
            "qsar_oral_ld50_raw", "qsar_ad", "qsar_source")
CODE_LABELS = {
    "review_existing_evidence": "1. 기존 시험자료 기준 부합 가능성 검토",
    "review_discordance": "2. 기존 자료와 QSAR 불일치 검토",
    "review_qsar_signal": "3. QSAR 기반 후보 검토",
    "review_data_quality": "4. 자료 품질·적용영역 검토",
    "lower_priority_oral_only": "5. 급성경구 종말점 기준 후순위(안전 판정 아님)",
    "data_gap": "자료 부족",
    "verify_designation": "규제 지정여부 확인 필요",
    "already_designated": "이미 지정됨: 신규 후보 분석 제외",
    "out_of_scope": "분석범위 밖(혼합물 또는 비단일물질)",
}
VALUE = re.compile(r"^\s*(<=|>=|<|>|≤|≥|=)?\s*(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*$")
RANGE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*$")


def parse_ld50(raw: str) -> tuple[float | None, float | None, bool, bool, str]:
    """Return lower/upper bounds, inclusivity, parse status. None denotes infinity."""
    value = (raw or "").strip().replace(",", "")
    if not value:
        return None, None, False, False, "missing"
    value = re.sub(r"\s*mg\s*/\s*kg\s*$", "", value, flags=re.IGNORECASE).strip()
    m = RANGE.fullmatch(value)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        if 0 < lo <= hi and math.isfinite(hi):
            return lo, hi, True, True, "ok"
        return None, None, False, False, "invalid"
    m = VALUE.fullmatch(value)
    if not m:
        return None, None, False, False, "invalid"
    op, txt = m.group(1) or "=", m.group(2)
    n = float(txt)
    if n <= 0 or not math.isfinite(n):
        return None, None, False, False, "invalid"
    if op in ("<", "<=", "≤"):
        return 0, n, False, op != "<", "ok"
    if op in (">", ">=", "≥"):
        return n, None, op != ">", False, "ok"
    return n, n, True, True, "ok"


def relation(raw: str, threshold: float = THRESHOLD) -> str:
    lo, hi, lo_inc, hi_inc, state = parse_ld50(raw)
    if state != "ok":
        return state
    if hi is not None and hi <= threshold:
        return "meets"
    if lo is not None and (lo > threshold or (lo == threshold and not lo_inc)):
        return "above"
    return "ambiguous"


def norm(value: str) -> str:
    return (value or "").strip().lower()


def assess(row: dict[str, str]) -> dict[str, str]:
    out = dict(row)
    issues = []
    kind = norm(row["substance_type"])
    status = norm(row["designation_status"])
    msds_rel = relation(row["msds_oral_ld50_raw"])
    qsar_rel = relation(row["qsar_oral_ld50_raw"])
    if msds_rel == "invalid": issues.append("invalid_msds_ld50")
    if qsar_rel == "invalid": issues.append("invalid_qsar_ld50")
    if status not in ("designated", "not_designated", "unknown"):
        issues.append("invalid_designation_status")
        status = "unknown"
    if status == "not_designated" and not row["designation_status_source"].strip():
        issues.append("designation_status_source_missing")
        status = "unknown"
    if kind != "single":
        issues.append("not_single_substance")
    msds_valid = (msds_rel in ("meets", "above", "ambiguous")
                  and norm(row["msds_basis"]) == "experimental"
                  and norm(row["msds_species"]) in ("rat", "mouse", "rodent", "설치류", "쥐", "랫드", "마우스")
                  and norm(row["msds_route"]) in ("oral", "경구")
                  and norm(row["msds_unit"]).replace(" ", "") == "mg/kg"
                  and bool(row["msds_source"].strip()))
    if msds_rel != "missing" and not msds_valid:
        issues.append("msds_endpoint_or_provenance_unverified")
    qsar_valid = (qsar_rel in ("meets", "above", "ambiguous")
                  and norm(row["qsar_ad"]) == "inside" and bool(row["qsar_source"].strip()))
    if qsar_rel != "missing" and not qsar_valid:
        issues.append("qsar_unverified_or_outside_ad")
    conflicting = (msds_valid and qsar_valid and
                   ((msds_rel == "meets" and qsar_rel == "above") or
                    (msds_rel == "above" and qsar_rel == "meets")))
    if conflicting:
        issues.append("independent_evidence_discordance_check_sources")
    if not row["compound_id"].strip() or not row["cas"].strip():
        issues.append("identifier_missing")
    if kind != "single":
        category = "out_of_scope"
    elif status == "designated":
        category = "already_designated"
    elif status != "not_designated":
        category = "verify_designation"
    elif msds_valid and msds_rel == "meets":
        category = "review_existing_evidence"
    elif conflicting:
        category = "review_discordance"
    elif msds_valid and msds_rel == "above" and qsar_valid and qsar_rel == "meets":
        category = "review_discordance"
    elif qsar_valid and qsar_rel == "meets":
        category = "review_qsar_signal"
    elif any(x in issues for x in ("invalid_msds_ld50", "invalid_qsar_ld50", "msds_endpoint_or_provenance_unverified", "qsar_unverified_or_outside_ad")) or msds_rel == "ambiguous" or qsar_rel == "ambiguous":
        category = "review_data_quality"
    elif msds_valid and msds_rel == "above":
        category = "lower_priority_oral_only"
    else:
        category = "data_gap"
    out.update({"msds_threshold_relation": msds_rel,
                "qsar_threshold_relation": qsar_rel,
                "msds_endpoint_verified_for_pilot": str(bool(msds_valid)).lower(),
                "qsar_ad_supported_for_pilot": str(bool(qsar_valid)).lower(),
                "evidence_discordance": str(bool(conflicting)).lower(),
                "priority_code": category, "priority_label_ko": CODE_LABELS[category],
                "quality_flags": ";".join(sorted(set(issues))),
                "screening_scope": "rodent_acute_oral_ld50_only",
                "legal_threshold_mg_kg": str(THRESHOLD),
                "not_a_regulatory_designation": "true"})
    return out


def fetch_law(outdir: Path) -> dict:
    """Download official law search and body for audit; never claim annex machine validation."""
    oc = os.getenv("LAW_API_OC", "").strip()
    if not oc or oc.upper() in {"YOUR_OC", "YOUR_KEY", "YOUR_API_KEY"}:
        raise RuntimeError("LAW_API_OC 가 .env에 설정되어 있지 않습니다.")
    base = os.getenv("LAW_API_BASE_URL", "https://www.law.go.kr/DRF").rstrip("/")
    if base != "https://www.law.go.kr/DRF":
        raise RuntimeError("파일럿은 공식 HTTPS 법령 API 주소만 허용합니다.")
    def get(path, parameters):
        response = requests.get(base + path, params={"OC": oc, **parameters}, timeout=25,
                                headers={"User-Agent": "industryqsar-research-pilot/0.1"})
        response.raise_for_status()
        data = response.content
        if not data or b"<html" in data[:250].lower():
            raise RuntimeError("법령 API가 XML 대신 HTML/빈 내용을 반환했습니다. 인증과 접근권한을 확인하세요.")
        try:
            tree = ET.fromstring(data)
        except ET.ParseError as e:
            raise RuntimeError("법령 API XML 파싱 실패: 응답 형식 확인 필요") from e
        if any(token in tree.tag.lower() for token in ("error", "err")):
            raise RuntimeError("법령 API 오류 응답: 인증 상태 확인 필요")
        return data, tree
    search_bytes, search_root = get("/lawSearch.do", {"target": "law", "type": "XML", "query": LAW_QUERY, "display": 20})
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "law_search.xml").write_bytes(search_bytes)
    records = []
    for el in search_root.iter():
        fields = {sub.tag.split("}")[-1]: (sub.text or "").strip() for sub in el}
        title = re.sub(r"<[^>]*>", "", fields.get("법령명한글", "")).strip()
        if title == LAW_QUERY:
            records.append(fields)
    if not records:
        raise RuntimeError("API 검색 결과에서 시행령 제목을 정확히 찾지 못했습니다. law_search.xml을 확인하세요.")
    # Preserve metadata for human verification; do not guess latest effective edition.
    selected = sorted(records, key=lambda d: d.get("시행일자", ""), reverse=True)[0]
    law_id = selected.get("법령ID", "")
    if not law_id or not law_id.isdigit():
        raise RuntimeError("법령ID가 없어 원문 조회를 수행할 수 없습니다.")
    detail_bytes, _ = get("/lawService.do", {"target": "law", "type": "XML", "ID": law_id, "BD": "ON"})
    (outdir / "law_detail.xml").write_bytes(detail_bytes)
    metadata = {"query": LAW_QUERY, "exact_title_matched": True,
                "law_id": law_id, "effective_date": selected.get("시행일자", ""),
                "promulgation_date": selected.get("공포일자", ""),
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                "search_raw_file": "law_search.xml", "detail_raw_file": "law_detail.xml",
                "annex_threshold_automatically_verified": False,
                "warning": "API 응답은 법령 원문 기록용. 별표 1 기준 및 적용일은 연구자가 별도 대조해야 함."}
    (outdir / "law_audit.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return metadata


def run(input_path: Path, outdir: Path, demo: bool, live_law: bool) -> None:
    if not demo and "synthetic" in input_path.name.lower():
        raise ValueError("합성 예시는 반드시 --demo 옵션과 함께 실행하세요.")
    outdir.mkdir(parents=True, exist_ok=True)
    audit = None
    if live_law:
        audit = fetch_law(outdir)
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = [x for x in REQUIRED if x not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("필수 CSV 열 누락: " + ", ".join(missing))
        rows = [assess(row) for row in reader]
    if not rows:
        raise ValueError("입력 CSV에 물질 행이 없습니다.")
    # Auditable duplicate warnings without silently collapsing conflicting records.
    counts = {}
    for r in rows:
        cas = r["cas"].strip()
        if cas:
            counts[cas] = counts.get(cas, 0) + 1
    for r in rows:
        if r["cas"].strip() and counts[r["cas"].strip()] > 1:
            r["quality_flags"] += (";" if r["quality_flags"] else "") + "duplicate_cas_review"
    columns = list(rows[0].keys())
    def write_csv(path, dataset):
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(dataset)
    write_csv(outdir / "screening_results.csv", rows)
    write_csv(outdir / "manual_review.csv", [r for r in rows if r["priority_code"] not in ("already_designated", "lower_priority_oral_only")])
    tally = {key: sum(r["priority_code"] == key for r in rows) for key in CODE_LABELS}
    summary = {"mode": "SYNTHETIC_DEMO_ONLY" if demo else "USER_SUPPLIED_INPUT",
               "generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "input_rows": len(rows), "category_counts": tally,
               "endpoint": "rodent acute oral LD50", "threshold_mg_kg": THRESHOLD,
               "legal_basis": "K-REACH Enforcement Decree Annex 1 (acute oral rodent LD50), 2025-08-05 revision",
               "law_source": LAW_SOURCE,
               "live_law_api_fetched": bool(audit),
               "annex_threshold_automatically_verified": False,
               "designation_status_source": "input CSV; NOT obtained from law API",
               "notes": ["규제 지정 판정 결과가 아닌 연구용 평가 우선순위임.",
                         "규제 지정현황은 별도 공식 고시 대조 필요.",
                         "독성자료의 독립성 및 실제 시험 출처를 수동 확인할 것.",
                         "법령 API는 법령 원문 조회만 수행; 물질 지정목록 수집 및 별표 자동해석 미지원."]}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Completed: {len(rows)} records; results: {outdir.resolve()}")
    print(json.dumps(tally, ensure_ascii=False, indent=2))


def main():
    load_dotenv()
    p = argparse.ArgumentParser(description="Acute oral LD50 regulatory prioritization PILOT")
    p.add_argument("--input", default="data/sample_synthetic.csv")
    p.add_argument("--out", default="outputs/pilot")
    p.add_argument("--demo", action="store_true", help="Explicitly mark synthetic demo inputs")
    p.add_argument("--live-law", action="store_true", help="Fetch law API; requires LAW_API_OC in local .env")
    args = p.parse_args()
    try:
        run(Path(args.input), Path(args.out), args.demo, args.live_law)
    except (ValueError, RuntimeError, OSError, requests.RequestException) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
