#!/usr/bin/env python3
"""Prepare EPA CompTox batch CAS list from Korean acute registry and optional candidate universe.

No online calls. Preserves registry positive-vs-candidate population role.
Neither negative class nor official non-designation is inferred.
"""
import argparse
import csv
from pathlib import Path

from regulatory_screen import normalize_cas, valid_cas


def get_cas_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rdr = csv.DictReader(stream)
        cols = rdr.fieldnames or []
        cas_key = next((s for s in cols if s.strip().lower().replace("_", "").replace(" ", "") in
                        ("cas", "casrn", "casno")), None)
        if not cas_key:
            raise ValueError(f"CAS 열을 찾을 수 없습니다: {path}")
        result = []
        for row in rdr:
            cas = normalize_cas(row.get(cas_key, ""))
            if cas and valid_cas(cas):
                result.append(cas)
        return sorted(set(result))


def build(registry: Path, candidates: Path | None, out: Path):
    references = set(get_cas_csv(registry))
    pool = set(get_cas_csv(candidates)) if candidates else set()
    if not references:
        raise ValueError("CAS가 있는 인체급성 지정 참조물질이 없습니다.")
    combined = sorted(references | pool)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(combined) + "\n", encoding="utf-8")
    manifest = out.with_name(out.stem + "_roles.csv")
    with manifest.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["cas", "input_role", "regulatory_status_assumed"])
        writer.writeheader()
        for cas in combined:
            writer.writerow({
                "cas": cas,
                "input_role": "korean_acute_registry_reference" if cas in references
                              else "candidate_universe_user_supplied",
                "regulatory_status_assumed": "none",
            })
    return {"cas_for_epa_batch": len(combined), "acute_registry_references": len(references),
            "candidate_universe_additional_cas": len(pool - references),
            "paste_list": str(out), "role_manifest": str(manifest)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--candidates", type=Path, help="Optional Korean industrial CAS universe CSV")
    p.add_argument("--out", type=Path, default=Path("data/private/epa_batch_cas.txt"))
    args = p.parse_args()
    try:
        print(build(args.registry, args.candidates, args.out))
    except (OSError, ValueError) as exc:
        p.error(str(exc))


if __name__ == "__main__":
    main()
