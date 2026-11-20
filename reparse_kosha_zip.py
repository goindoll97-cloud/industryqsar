#!/usr/bin/env python3
"""Reparse an existing KOSHA ZIP's section-11 XML without any API requests.

Preserves original XML and original CSV files, replacing only the human acute
endpoint extraction and its derived audit counters. Does not validate legal
designation or the underlying toxicological study.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import zipfile

from human_acute_extract import parse_section11, write_csv


def repack(src: Path, dst: Path) -> dict:
    if src.resolve() == dst.resolve():
        raise ValueError("원본 ZIP을 덮어쓸 수 없습니다. 다른 --out-zip 경로를 사용하세요.")
    with zipfile.ZipFile(src, "r") as z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        norm = lambda name: name.replace("\\", "/").strip("/")
        paths = [norm(i.filename) for i in infos]
        if len(set(paths)) != len(paths):
            raise ValueError("ZIP 내부 파일 경로가 중복됩니다.")
        def get_basename(filename):
            found = [i for i in infos if paths[infos.index(i)].split("/")[-1] == filename]
            if len(found) != 1:
                raise ValueError("파일 누락 또는 중복: " + filename)
            if found[0].file_size > 10_000_000:
                raise ValueError("입력 CSV 크기 제한 초과")
            return z.read(found[0].filename)
        search = list(csv.DictReader(io.StringIO(
            get_basename("kosha_search_results.csv").decode("utf-8-sig"))))
        if len(search) > 10000:
            raise ValueError("CAS 수가 제한을 초과합니다.")
        audit = json.loads(get_basename("kosha_audit.json").decode("utf-8-sig"))
        rows = []
        missing_section = []
        for index, hit in enumerate(search, start=1):
            target = f"raw_xml/{index:03d}_section11.xml"
            xmlfiles = [i for i in infos if norm(i.filename).endswith(target)]
            if len(xmlfiles) > 1:
                raise ValueError("중복 XML 경로: " + target)
            if not xmlfiles:
                if hit.get("search_status") == "exact_cas_match":
                    missing_section.append(hit.get("queried_cas", ""))
                continue
            xml_info = xmlfiles[0]
            if xml_info.file_size > 5_000_000:
                raise ValueError("XML 크기 제한 초과: " + target)
            rows.extend(parse_section11(
                z.read(xml_info.filename),
                hit["queried_cas"],
                hit.get("selected_chem_id", ""),
            ))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "human_acute_endpoints.csv"
            write_csv(p, rows)
            parsed_csv_bytes = p.read_bytes()
        audit["structured_human_endpoint_rows"] = len(rows)
        audit["human_acute_reparse"] = {
            "method": "existing_xml_without_new_api_requests",
            "reparsed_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_zip_filename": src.name,
            "missing_section11_for_exact_cas": missing_section,
            "extraction_status_counts": {
                state: sum(r["extraction_status"] == state for r in rows)
                for state in sorted(set(r["extraction_status"] for r in rows))
            },
        }
        dst.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as out:
            for info in infos:
                base = norm(info.filename).split("/")[-1]
                if base == "human_acute_endpoints.csv":
                    out.writestr(info.filename, parsed_csv_bytes)
                elif base == "kosha_audit.json":
                    out.writestr(info.filename, json.dumps(
                        audit, ensure_ascii=False, indent=2).encode("utf-8"))
                else:
                    if info.file_size > 20_000_000:
                        raise ValueError("입력 파일이 지나치게 큽니다: " + info.filename)
                    out.writestr(info.filename, z.read(info.filename))
    return {
        "output_zip": str(dst),
        "cas_rows": len(search),
        "structured_endpoint_rows": len(rows),
        "missing_section11_for_exact_cas": missing_section,
        "extraction_status_counts": audit["human_acute_reparse"]["extraction_status_counts"],
        "api_requests_performed": 0,
    }


def main():
    p = argparse.ArgumentParser(description="Reparse previously downloaded KOSHA section 11 XML from ZIP")
    p.add_argument("--batch-zip", type=Path, required=True)
    p.add_argument("--out-zip", type=Path, default=Path("outputs/kosha_pilot20_reparsed.zip"))
    args = p.parse_args()
    try:
        print(json.dumps(repack(args.batch_zip, args.out_zip), ensure_ascii=False, indent=2))
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as e:
        print("ERROR: " + str(e), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
