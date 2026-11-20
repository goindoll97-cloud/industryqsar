#!/usr/bin/env python3
"""KOSHA MSDS API collector: raw evidence, not automatic regulatory designation.

Public Data Portal dataset: 15157612
Search: getChemList001 (CAS searchCnd=1)
Human-health section only: getChemDetail111 (MSDS section 11)

A KOSHA MSDS entry is a REFERENCE source, not evidence of experimental provenance.
All candidate endpoint mentions remain unverified until manually checked.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time
import xml.etree.ElementTree as ET
from urllib.parse import unquote

from dotenv import load_dotenv
import requests

from human_acute_extract import export_from_folder

BASE_URL = "https://apis.data.go.kr/B552468/msdschem1"
SEARCH_PATH = "getChemList001"
DETAIL_PATHS = {"11": "getChemDetail111"}
CAS_PATTERN = re.compile(r"^\d{2,7}-\d{2}-\d$")
ENDPOINT_PATTERN = re.compile(r"(?i)(?:\bLD\s*50\b|\bLC\s*50\b|반수\s*치사|급성\s*독성|피부\s*부식|표적\s*장기\s*독성)")
ID_KEYS = ("chemId", "chemID", "chem_id", "chemicalId", "msdsId", "msdsNo", "chemNo")
CAS_KEYS = ("casNo", "casNO", "cas_no", "casRn", "cas", "casNum", "casNumber")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def flattened_fields(item: ET.Element) -> dict[str, str]:
    """Preserve leaf values only, with explicit tag names for schema audit."""
    data = {}
    for leaf in item.iter():
        if len(leaf):
            continue
        val = (leaf.text or "").strip()
        if not val:
            continue
        k = local_tag(leaf.tag)
        if k in data and data[k] != val:
            data[k] += " | " + val
        else:
            data[k] = val
    return data


def first_field(fields: dict[str, str], names: tuple[str, ...]) -> str:
    normalized = {re.sub(r"[^a-z0-9]", "", k.lower()): v for k, v in fields.items()}
    for name in names:
        key = re.sub(r"[^a-z0-9]", "", name.lower())
        if key in normalized:
            return normalized[key].strip()
    return ""


def xml_items(root: ET.Element) -> list[dict[str, str]]:
    """Generic XML parser for both item and list forms; fail closed on unknown layout."""
    items = [e for e in root.iter() if local_tag(e.tag).lower() == "item"]
    return [flattened_fields(e) for e in items]


def xml_text(root: ET.Element) -> str:
    """Flatten text while preserving section labels; never infer numeric endpoints."""
    chunks = []
    for e in root.iter():
        if len(e):
            continue
        val = " ".join((e.text or "").split())
        if val:
            chunks.append(local_tag(e.tag) + ": " + val)
    return "\n".join(chunks)


def candidate_mentions(text: str, context: int = 120, limit: int = 60) -> list[str]:
    """Extract human-health endpoint mentions for manual review; no numeric toxicity parsing."""
    one_line = re.sub(r"\s+", " ", text)
    out = []
    for match in ENDPOINT_PATTERN.finditer(one_line):
        snippet = one_line[max(0, match.start() - context): match.end() + context]
        if snippet not in out:
            out.append(snippet)
        if len(out) >= limit:
            break
    return out


def error_message(root: ET.Element) -> str | None:
    fields = flattened_fields(root)
    code = first_field(fields, ("resultCode", "returnReasonCode", "errorCode"))
    if code and code not in ("00", "0", "000", "SUCCESS"):
        msg = first_field(fields, ("resultMsg", "returnAuthMsg", "errMsg", "message"))
        return "KOSHA 응답 오류 코드 " + code + (": " + msg[:120] if msg else "")
    top = local_tag(root.tag).lower()
    if top in {"error", "errorresponse"}:
        return "KOSHA API 오류 XML 수신"
    return None


class KoshaClient:
    def __init__(self, key: str, session=None, base_url: str = BASE_URL):
        if not key.strip():
            raise ValueError("KOSHA_MSDS_SERVICE_KEY가 .env에 없습니다.")
        # Accept the encoded or decoded portal key. requests will percent-encode once.
        self.key = unquote(key.strip())
        if base_url.rstrip("/") != BASE_URL:
            raise ValueError("안전상 공식 KOSHA API 기본 URL만 허용합니다.")
        self.session = session or requests.Session()

    def fetch(self, operation: str, params: dict[str, object]) -> tuple[bytes, ET.Element]:
        if operation not in (SEARCH_PATH, *DETAIL_PATHS.values()):
            raise ValueError("허용되지 않은 KOSHA API 경로입니다.")
        try:
            r = self.session.get(
                BASE_URL + "/" + operation,
                params={"serviceKey": self.key, **params},
                headers={"User-Agent": "industryqsar-research-pilot/0.2"},
                timeout=25,
            )
            r.raise_for_status()
        except requests.RequestException as exc:
            # requests errors may contain the full URL with the secret query string.
            raise RuntimeError("KOSHA API 연결 실패: 주소·승인 상태·호출량을 확인하세요. 인증키는 출력하지 않습니다.") from None
        payload = r.content
        if not payload or len(payload) > 5_000_000:
            raise RuntimeError("KOSHA 응답이 비었거나 비정상적으로 큽니다.")
        try:
            root = ET.fromstring(payload)
        except ET.ParseError:
            raise RuntimeError("KOSHA 응답이 유효한 XML이 아닙니다. API 승인 상태를 확인하세요.") from None
        err = error_message(root)
        if err:
            raise RuntimeError(err)
        return payload, root

    def search_cas(self, cas: str, max_hits: int = 10) -> tuple[bytes, list[dict[str, str]]]:
        if not CAS_PATTERN.fullmatch(cas):
            raise ValueError("CAS 형식 오류(예: 71-43-2): " + cas[:40])
        payload, root = self.fetch(SEARCH_PATH, {
            "searchWrd": cas, "searchCnd": "1",
            "numOfRows": max_hits, "pageNo": 1,
        })
        return payload, xml_items(root)

    def detail(self, chem_id: str, section: str, id_param: str) -> tuple[bytes, ET.Element]:
        if section not in DETAIL_PATHS:
            raise ValueError("인체독성 전용 파일럿은 MSDS 11번만 조회합니다.")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", id_param):
            raise ValueError("상세조회 ID 파라미터명이 유효하지 않습니다.")
        if not re.fullmatch(r"[\w-]{1,120}", chem_id):
            raise ValueError("API 물질 ID가 유효하지 않습니다.")
        return self.fetch(DETAIL_PATHS[section], {id_param: chem_id})


def read_cas_csv(path: Path) -> list[str]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        col = next((x for x in (reader.fieldnames or []) if x.strip().lower() in {"cas", "cas_no", "casrn"}), None)
        if col is None:
            raise ValueError("CAS 입력 CSV에 cas 열이 필요합니다.")
        return [row[col].strip() for row in reader if (row.get(col) or "").strip()]


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        # Guard against formulas when opening external MSDS text in Excel.
        for row in rows:
            writer.writerow({k: "'" + str(v) if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v
                             for k, v in row.items()})


def run(cas_values: list[str], out: Path, fetch_details: bool,
        detail_id_param: str, max_cas: int, max_hits: int,
        sleep_seconds: float, client: KoshaClient) -> dict:
    if not 1 <= max_cas <= 100:
        raise ValueError("max-cas는 1~100입니다. 호출량을 통제하기 위해 제한합니다.")
    if not 1 <= max_hits <= 100:
        raise ValueError("max-hits는 1~100입니다.")
    if not 0 <= sleep_seconds <= 30:
        raise ValueError("sleep은 0~30초입니다.")
    chosen = list(dict.fromkeys(cas_values))
    if len(chosen) > max_cas:
        chosen = chosen[:max_cas]
    if not chosen:
        raise ValueError("검색할 CAS가 없습니다.")
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw_xml"
    raw_dir.mkdir(exist_ok=True)
    searches, sections, mentions, templates = [], [], [], []
    for idx, cas in enumerate(chosen, start=1):
        row = {"queried_cas": cas, "search_status": "not_run",
               "n_hits": 0, "n_exact_cas_hits": 0, "selected_chem_id": "",
               "list_fields_json": "", "error": ""}
        try:
            raw, hits = client.search_cas(cas, max_hits=max_hits)
            (raw_dir / f"{idx:03d}_search.xml").write_bytes(raw.replace(client.key.encode(), b"[REDACTED]"))
            row["n_hits"] = len(hits)
            row["list_fields_json"] = json.dumps(hits, ensure_ascii=False)
            exact = [hit for hit in hits if first_field(hit, CAS_KEYS).replace(" ", "") == cas]
            row["n_exact_cas_hits"] = len(exact)
            if len(exact) != 1:
                row["search_status"] = ("no_hit" if not hits else
                                        "no_verifiable_exact_cas" if not exact else
                                        "multiple_exact_cas_hits_review")
            else:
                selected = exact[0]
                chem_id = first_field(selected, ID_KEYS)
                row["selected_chem_id"] = chem_id
                row["search_status"] = "exact_cas_match" if chem_id else "exact_cas_no_recognized_id"
                if fetch_details and chem_id:
                    for section in ("11",):
                        try:
                            payload, root = client.detail(chem_id, section, detail_id_param)
                            filename = f"{idx:03d}_section{section}.xml"
                            (raw_dir / filename).write_bytes(payload.replace(client.key.encode(), b"[REDACTED]"))
                            txt = xml_text(root)
                            sections.append({"queried_cas": cas, "chem_id": chem_id,
                                             "section": section, "raw_file": "raw_xml/" + filename,
                                             "text": txt, "status": "api_returned_unverified"})
                            for s in candidate_mentions(txt):
                                mentions.append({"queried_cas": cas, "chem_id": chem_id,
                                                 "section": section, "mention": s,
                                                 "evidence_status": "UNVERIFIED_TEXT_ONLY"})
                        except (ValueError, RuntimeError) as exc:
                            sections.append({"queried_cas": cas, "chem_id": chem_id,
                                             "section": section, "raw_file": "",
                                             "text": "", "status": "failed: " + str(exc)})
                        if sleep_seconds:
                            time.sleep(sleep_seconds)
        except (ValueError, RuntimeError) as exc:
            row["search_status"] = "failed"
            row["error"] = str(exc)
        searches.append(row)
        # Keep regulatory status unknown and basis blank. These are not invented labels.
        templates.append({
            "compound_id": "CAS_" + cas.replace("-", "_"), "name": "", "cas": cas,
            "substance_type": "single", "designation_status": "unknown",
            "designation_status_source": "", "msds_oral_ld50_raw": "",
            "msds_basis": "", "msds_species": "", "msds_route": "", "msds_unit": "",
            "msds_source": "", "qsar_oral_ld50_raw": "", "qsar_ad": "unknown",
            "qsar_source": "",
        })
        if sleep_seconds:
            time.sleep(sleep_seconds)
    write_csv(out / "kosha_search_results.csv", searches,
              ["queried_cas", "search_status", "n_hits", "n_exact_cas_hits",
               "selected_chem_id", "list_fields_json", "error"])
    write_csv(out / "kosha_sections.csv", sections,
              ["queried_cas", "chem_id", "section", "raw_file", "text", "status"])
    write_csv(out / "kosha_endpoint_mentions.csv", mentions,
              ["queried_cas", "chem_id", "section", "mention", "evidence_status"])
    write_csv(out / "screening_input_template.csv", templates,
              list(templates[0].keys()))
    n_structured_human = export_from_folder(out, searches)
    audit = {
        "source": "KOSHA MSDS Lookup Service (Public Data Portal 15157612)",
        "fetched_at_utc": utc_now(),
        "cas_requested": len(chosen), "exact_unique_cas_matched": sum(x["search_status"] == "exact_cas_match" for x in searches),
        "sections_downloaded": sum(x["status"] == "api_returned_unverified" for x in sections),
        "endpoint_mentions": len(mentions), "structured_human_endpoint_rows": n_structured_human,
        "structured_human_endpoint_file": "human_acute_endpoints.csv",
        "details_requested": fetch_details,
        "search_endpoint": SEARCH_PATH, "detail_endpoints": DETAIL_PATHS,
        "detail_id_parameter_assumption": detail_id_param if fetch_details else None,
        "experimental_provenance_verified": False, "legal_designation_checked": False,
        "notes": [
            "KOSHA 공단 MSDS 정보는 참고용이며 시험자료의 원출처 검증이 필요합니다.",
            "유사명 또는 여러 CAS/물질ID 매칭은 자동 확정하지 않습니다.",
            "LD50, LC50 및 인체급성독성 관련 언급은 원문 후보이며 구조화 독성 수치가 아닙니다.",
            "법정 지정 여부 및 설치류 경구 LD50의 시험종·노출경로·단위 정합성은 별도 검증이 필요합니다.",
            "상세조회 ID 파라미터는 현재 API 명세와 비교 확인하세요.",
        ],
    }
    (out / "kosha_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="KOSHA MSDS CAS API collector (unverified evidence)")
    parser.add_argument("--cas", action="append", default=[], help="Search CAS RN; repeatable")
    parser.add_argument("--cas-csv", type=Path, help="CSV with cas column")
    parser.add_argument("--out", type=Path, default=Path("outputs/kosha_pilot"))
    parser.add_argument("--fetch-details", action="store_true", help="Request human-health MSDS section 11 only (no ecological section 12)")
    parser.add_argument("--detail-id-param", default=os.getenv("KOSHA_MSDS_DETAIL_ID_PARAM", "chemId"),
                        help="Confirm ID parameter in API swagger; default is provisional.")
    parser.add_argument("--max-cas", type=int, default=10)
    parser.add_argument("--max-hits", type=int, default=10)
    parser.add_argument("--sleep", type=float, default=0.5)
    args = parser.parse_args()
    try:
        selected = args.cas + (read_cas_csv(args.cas_csv) if args.cas_csv else [])
        audit = run(selected, args.out, args.fetch_details, args.detail_id_param,
                    args.max_cas, args.max_hits, args.sleep,
                    KoshaClient(os.getenv("KOSHA_MSDS_SERVICE_KEY", "")))
        print(json.dumps(audit, ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
