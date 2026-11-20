#!/usr/bin/env python3
"""Extract candidate HUMAN acute toxicity endpoints from KOSHA MSDS section 11.

This deliberately extracts reported strings, NOT independently verified test data
or official designation status. Only route-coded records K040202/204/206 are used.
"""
from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET

ITEM_CODES = {
    "K040202": ("oral", "LD50"),
    "K040204": ("dermal", "LD50"),
    "K040206": ("inhalation", "LC50"),
}
VALUE_RE = re.compile(
    r"\b(?P<metric>LD\s*50|LC\s*50)\b\s*"
    r"(?P<op><=|>=|≤|≥|<|>|=)?\s*"
    r"(?P<value>\d+(?:,\d{3})*(?:\.\d+)?(?:e[+-]?\d+)?)\s*"
    r"(?P<unit>mg\s*/\s*kg|mg\s*/\s*l|mg\s*/\s*m3|ppm)\b",
    re.IGNORECASE,
)
DURATION_RE = re.compile(r"(?P<hours>\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hour|hours|시간)\b", re.IGNORECASE)
SPECIES_RE = re.compile(r"실험종\s*:\s*(?P<species>[A-Za-z가-힣]+)")
SOURCE_RE = re.compile(r"(?:※\s*)?출처\s*:\s*(?P<source>[^|;\n]{1,120})", re.IGNORECASE)
GUIDELINE_RE = re.compile(r"OECD\s*TG\s*\d+[A-Za-z]?", re.IGNORECASE)
COLUMNS = [
    "cas", "chem_id", "msds_code", "route", "expected_metric",
    "raw_detail", "extraction_status", "extraction_note", "reported_metric", "qualifier",
    "value", "unit", "species_as_written", "duration_hours",
    "exposure_form", "reported_source", "test_guideline",
    "oral_ld50_300_relation_preliminary", "evidence_verification",
]


def canonical_text(value: str) -> str:
    # Some MSDS XML uses &amp;gt; so ElementTree alone leaves literal &gt;.
    return unicodedata.normalize("NFKC", html.unescape(value or "")).strip()


def parse_section11(xml_bytes: bytes, cas: str, chem_id: str = "") -> list[dict[str, str]]:
    """Read human toxicity endpoint fields by MSDS item codes, fail closed."""
    root = ET.fromstring(xml_bytes)
    items = [x for x in root.iter() if x.tag.rsplit("}", 1)[-1] == "item"]
    rows = []
    for item in items:
        cells = {child.tag.rsplit("}", 1)[-1]: (child.text or "") for child in item}
        code = cells.get("msdsItemCode", "").strip()
        if code not in ITEM_CODES:
            continue
        route, metric = ITEM_CODES[code]
        raw = canonical_text(cells.get("itemDetail", ""))
        record = dict.fromkeys(COLUMNS, "")
        record.update({
            "cas": cas, "chem_id": chem_id, "msds_code": code,
            "route": route, "expected_metric": metric,
            "raw_detail": raw, "evidence_verification": "MSDS_REPORTED_NOT_INDEPENDENTLY_VERIFIED",
            "oral_ld50_300_relation_preliminary": "not_assessed",
        })
        if not raw or raw in {"자료없음", "자료 없음", "-", "N/A"}:
            record["extraction_status"] = "no_reported_value"
            rows.append(record)
            continue
        matches = [m for m in VALUE_RE.finditer(raw)
                   if re.sub(r"\s+", "", m.group("metric")).upper() == metric]
        if not matches:
            # E.g. LD50 50~300 mg/kg can be a hazard-class range rather than
            # one measured LD50. Do not turn it into a single experimental value.
            is_range = bool(re.search(
                r"\bLD\s*50\s*\d+(?:\.\d+)?\s*[-~–]\s*\d+(?:\.\d+)?\s*mg\s*/\s*kg",
                raw, flags=re.IGNORECASE))
            record["extraction_status"] = ("manual_review_range_not_single_value" if is_range
                                           else "manual_review_unrecognized_format")
            record["extraction_note"] = "do_not_infer_experimental_ld50_from_range" if is_range else ""
            rows.append(record)
            continue
        if len(matches) > 1:
            # Korean MSDS often repeats exactly the same number in explanatory
            # parentheses. Only collapse numerically identical repeats;
            # genuinely different measurements remain flagged for manual review.
            unique = {(m.group("op") or "=", float(m.group("value").replace(",", "")),
                       re.sub(r"\s+", "", m.group("unit")).lower()) for m in matches}
            if len(unique) != 1:
                record["extraction_status"] = "manual_review_multiple_values"
                rows.append(record)
                continue
            record["extraction_note"] = "repeated_identical_value_in_text"
        m = matches[0]
        normalized_unit = re.sub(r"\s+", "", m.group("unit")).lower()
        qualifier = m.group("op") or "="
        if qualifier == "≤": qualifier = "<="
        if qualifier == "≥": qualifier = ">="
        numeric = float(m.group("value").replace(",", ""))
        species = SPECIES_RE.search(raw)
        source = SOURCE_RE.search(raw)
        guideline = GUIDELINE_RE.search(raw)
        duration = DURATION_RE.search(raw)
        exposure_form = next((x for x in ("증기", "가스", "분진", "미스트", "에어로졸")
                              if x in raw), "")
        record.update({
            "extraction_status": "parsed_unverified",
            "reported_metric": metric, "qualifier": qualifier,
            "value": str(int(numeric)) if numeric.is_integer() else str(numeric),
            "unit": normalized_unit,
            "species_as_written": species.group("species") if species else "",
            "duration_hours": duration.group("hours") if duration else "",
            "exposure_form": exposure_form,
            "reported_source": source.group("source").strip() if source else "",
            "test_guideline": guideline.group(0) if guideline else "",
        })
        if route == "oral" and metric == "LD50" and normalized_unit == "mg/kg" and numeric > 0:
            if qualifier in ("<", "<=", "=") and numeric <= 300:
                record["oral_ld50_300_relation_preliminary"] = "meets_numeric_criterion"
            elif qualifier in (">", ">=", "=") and numeric > 300:
                record["oral_ld50_300_relation_preliminary"] = "above_numeric_criterion"
            else:
                record["oral_ld50_300_relation_preliminary"] = "ambiguous"
        rows.append(record)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for row in rows:
            # Protect spreadsheet users against formula injection from MSDS text.
            w.writerow({k: ("'" + v if v != "=" and v.lstrip().startswith(("=", "+", "-", "@")) else v)
                        for k, v in row.items()})


def export_from_folder(out: Path, search_rows: list[dict]) -> int:
    """Build structured candidates from newly downloaded raw XML without fresh API calls."""
    rows = []
    for i, item in enumerate(search_rows, 1):
        p = out / "raw_xml" / f"{i:03d}_section11.xml"
        if p.exists():
            rows.extend(parse_section11(p.read_bytes(),
                                        item["queried_cas"], item.get("selected_chem_id", "")))
    write_csv(out / "human_acute_endpoints.csv", rows)
    return len(rows)


def main() -> None:
    p = argparse.ArgumentParser(description="Parse KOSHA section 11 XML: human endpoints only")
    p.add_argument("--xml", type=Path, required=True,
                   help="Existing raw_xml/001_section11.xml")
    p.add_argument("--cas", required=True)
    p.add_argument("--chem-id", default="")
    p.add_argument("--out", type=Path, default=Path("outputs/human_acute_endpoints.csv"))
    args = p.parse_args()
    rows = parse_section11(args.xml.read_bytes(), args.cas, args.chem_id)
    write_csv(args.out, rows)
    print(f"Saved {len(rows)} human acute endpoint records: {args.out}")


if __name__ == "__main__":
    main()
