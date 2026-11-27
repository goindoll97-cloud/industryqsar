"""Recover local evidence from available ZIP archives, without assigning labels.
Python 3.10+; install pymupdf. No network access or uploads.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone

import fitz

STEMS = (
    "atsdr_profile_collection", "human_inhalation_collection",
    "hematotoxicity_experiment_pilot", "tri_chip_hematotoxicity_v210",
    "inhalation_screen_v1", "hematotoxicity_hazard_v3",
)
PATTERNS = {
    "blood": r"hematolog\w*|haematolog\w*|hematotox\w*|haematotox\w*|hematopoi\w*|haematopoi\w*|hemoglobin|haemoglobin|hematocrit|haematocrit|erythrocyt\w*|red blood cells?|\bRBCs?\b|an[ae]emi\w*|reticulocyt\w*|hemoly\w*|haemoly\w*|white blood cells?|\bWBCs?\b|leukocyt\w*|leukopen\w*|lymphocyt\w*|neutrophil\w*|neutropen\w*|eosinophil\w*|platelets?|thrombocyt\w*|bone marrow|pancytopen\w*|methemoglobin|methaemoglobin|carboxyhemoglobin|carboxyhaemoglobin",
    "cancer": r"leuk[ae]mi\w*|lymphoma\w*|multiple myeloma|myelodysplas\w*|lymphohematopoietic|lymphohaematopoietic|hematologic malignan\w*|haematologic malignan\w*",
    "human": r"\bhumans?\b|\bworkers?\b|\bpatients?\b|\bvolunteers?\b|\bparticipants?\b|\bmen\b|\bwomen\b|\bemployees?\b|occupational|epidemiolog\w*",
    "inhalation": r"inhal\w*|breathing.zone|airborne|vapou?r\w*|workroom air|ambient air|air concentrations?|concentrations? in air",
    "air_indirect": r"\bppm\b|mg\s*/\s*m[³3]|personal air|dust|fumes?",
    "animal": r"\brats?\b|\bmice\b|\bmouse\b|\brabbits?\b|\bdogs?\b|\bhamsters?\b|\banimals?\b|guinea pigs?",
    "other_route": r"\bdermal\b|\bskin\b|\boral\b|gavage|ingest\w*|intravenous|intraperitoneal",
    "effect": r"\b(?:increased|decreased|elevated|reduced|significant changes|significant increase|significant decrease|observed effects|developed|diagnosed)\b",
    "no_effect": r"no significant|no statistically significant|no hematolog|within normal limits|no (?:treatment.related |exposure.related )?(?:changes|effects|differences)|not significantly",
    "gap": r"no (?:human |animal |epidemiological )?studies (?:were |have been )?(?:located|identified|available|found)|no data|not examined|not evaluated",
}
RX = {k: re.compile(v, re.I) for k, v in PATTERNS.items()}
CAS = re.compile(r"(?<!\d)\d{2,7}-\d{2}-\d(?!\d)")
KEEP = {".csv", ".tsv", ".xlsx", ".xls", ".json", ".jsonl", ".xml", ".txt", ".md", ".py", ".ris", ".nbib", ".html", ".htm", ".parquet", ".bib"}
FIELDS = ["archive", "member", "pdf_sha256", "page", "line", "endpoint_cue",
          "human_cue", "inhalation_cue", "air_indirect_cue", "animal_cue",
          "other_route_cue", "effect_cue", "no_effect_cue", "data_gap_cue",
          "priority", "cas_mentions_unverified", "context", "review_status"]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def file_digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def csv_open(path, fields):
    f = path.open("w", encoding="utf-8-sig", newline="")
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    return f, w

def norm(s):
    return re.sub(r"\s+", " ", s).strip()

def cue(name, text):
    return int(bool(RX[name].search(text)))

def classify(line, context, wider):
    endpoint = ";".join(k for k in ("blood", "cancer") if cue(k, line))
    if not endpoint:
        return None
    h, i, air = (cue(k, wider) for k in ("human", "inhalation", "air_indirect"))
    priority = ("P1_human_inhalation_cues" if h and i else
                "P2_human_air_indirect_cues" if h and air else
                "P3_human_route_unclear" if h else
                "P4_no_human_cue")
    return dict(endpoint_cue=endpoint, human_cue=h, inhalation_cue=i,
                air_indirect_cue=air, animal_cue=cue("animal", wider),
                other_route_cue=cue("other_route", wider),
                effect_cue=cue("effect", context), no_effect_cue=cue("no_effect", context),
                data_gap_cue=cue("gap", context), priority=priority,
                cas_mentions_unverified=";".join(sorted(set(CAS.findall(wider)))),
                context=context, review_status="pending")

def scan_pdf(data, archive, member, emit):
    sha = digest(data)
    blank = 0
    hits = 0
    with fitz.open(stream=data, filetype="pdf") as doc:
        pages = len(doc)
        # Adjacent lines provide context across page boundaries.
        def read_page(i):
            return doc[i].get_text(sort=True).splitlines() if 0 <= i < pages else []
        prev, current = [], read_page(0)
        for p in range(pages):
            nxt = read_page(p + 1)
            if not norm(" ".join(current)):
                blank += 1
            combined = prev + current + nxt
            for j, line in enumerate(current):
                k = len(prev) + j
                context = norm(" ".join(combined[max(0, k-5):k+7]))
                wider = norm(" ".join(combined[max(0, k-35):k+36]))
                item = classify(line, context, wider)
                if item:
                    emit(dict(archive=archive, member=member, pdf_sha256=sha,
                              page=p+1, line=j+1, **item))
                    hits += 1
            prev, current = current, nxt
    return pages, blank, hits

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path.cwd(),
                    help="Folder containing the original ZIP archives")
    ap.add_argument("--archives", nargs="+", type=Path,
                    help="Optional explicit paths to ZIP archives")
    ap.add_argument("--out", type=Path, default=Path("recovered_inhalation_review"))
    args = ap.parse_args()
    inputs = args.archives or sorted(p for p in args.input.glob("*.zip")
                                    if any(p.name.startswith(s) for s in STEMS))
    if not inputs:
        ap.error("No matching ZIP archives found. Use --input or --archives.")
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        ap.error("Output folder is not empty; choose a new --out folder.")
    out.mkdir(parents=True, exist_ok=True)
    (out / "source_tables").mkdir()
    counts = Counter()
    manifest = []
    source_archives = []
    errors = []
    seen_pdf = {}
    handles = []
    try:
        for name in ("all_pdf_candidates.csv", "human_inhalation_priority.csv",
                     "hematologic_cancer_candidates.csv"):
            handles.append(csv_open(out / name, FIELDS))
        def emit(row):
            handles[0][1].writerow(row)
            counts["all_candidate_rows"] += 1
            counts[row["priority"]] += 1
            if row["priority"].startswith(("P1", "P2")):
                handles[1][1].writerow(row)
                counts["human_air_priority_rows"] += 1
            if "cancer" in row["endpoint_cue"]:
                handles[2][1].writerow(row)
                counts["cancer_candidate_rows"] += 1

        def walk(z, archive, prefix="", depth=0):
            for info in z.infolist():
                if info.is_dir():
                    continue
                member = prefix + info.filename
                ext = PurePosixPath(info.filename).suffix.lower()
                rec = dict(archive=archive, member=member, size=info.file_size,
                           sha256="", status="", saved_as="", pages="",
                           blank_text_pages="", candidate_rows="")
                try:
                    if ext not in KEEP and ext not in {".pdf", ".zip"}:
                        rec["status"] = "not_processed_extension"
                        continue
                    data = z.read(info)
                    sha = digest(data)
                    rec["sha256"] = sha
                    if ext == ".pdf":
                        if sha in seen_pdf:
                            rec["status"] = "duplicate_pdf"
                            rec["saved_as"] = seen_pdf[sha]
                        else:
                            pages, blank, hits = scan_pdf(data, archive, member, emit)
                            seen_pdf[sha] = archive + "::" + member
                            rec.update(status="pdf_scanned", pages=pages,
                                       blank_text_pages=blank, candidate_rows=hits)
                            counts["pdf_scanned"] += 1
                            counts["pdf_pages"] += pages
                            counts["blank_text_pages"] += blank
                            if counts["pdf_scanned"] % 10 == 0:
                                print("PDF scanned:", counts["pdf_scanned"], flush=True)
                    elif ext == ".zip":
                        if depth >= 2:
                            rec["status"] = "nested_depth_limit"
                        else:
                            with zipfile.ZipFile(io.BytesIO(data)) as nested:
                                walk(nested, archive, member+"::", depth+1)
                            rec["status"] = "nested_zip_scanned"
                    else:
                        # Copy all source tables / citation records without changing data.
                        # Hash-based path prevents unsafe archive paths and name collisions.
                        basename = re.sub(r"[^A-Za-z0-9._-]", "_",
                                          PurePosixPath(info.filename).name)[:100]
                        target = out / "source_tables" / (sha[:16]+"_"+basename)
                        if not target.exists():
                            target.write_bytes(data)
                        rec.update(status="source_preserved",
                                   saved_as=target.relative_to(out).as_posix())
                        counts["source_file_records"] += 1
                except Exception as e:
                    rec["status"] = "error"
                    errors.append(dict(archive=archive, member=member, error=str(e)))
                finally:
                    manifest.append(rec)

        for p in inputs:
            print("Reading:", p.name, flush=True)
            try:
                source_archives.append(dict(name=p.name, size=p.stat().st_size,
                                            sha256=file_digest(p)))
                with zipfile.ZipFile(p) as z:
                    walk(z, p.name)
            except Exception as e:
                errors.append(dict(archive=p.name, member="", error=str(e)))
    finally:
        for f, w in handles:
            f.close()
    mf, mw = csv_open(out / "source_manifest.csv",
        ["archive","member","size","sha256","status","saved_as","pages",
         "blank_text_pages","candidate_rows"])
    with mf:
        mw.writerows(manifest)
    ef, ew = csv_open(out / "errors.csv", ["archive","member","error"])
    with ef:
        ew.writerows(errors)
    meta = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                pymupdf_version=fitz.VersionBind, input_archives=source_archives,
                counts=dict(counts), error_count=len(errors),
                scope="Candidate retrieval only. Human and inhalation cues are not confirmed routes or species. All PDF endpoint hits retained. No final labels.",
                missing_stems=[s for s in STEMS if not any(p.name.startswith(s) for p in inputs)],
                output_file_sha256={p.relative_to(out).as_posix():file_digest(p)
                                    for p in sorted(out.rglob("*")) if p.is_file()})
    (out / "summary.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    package = out.with_suffix(".zip")
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(out.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(out).as_posix())
    print(json.dumps(meta["counts"], indent=2))
    print("Errors:", len(errors), "| Result:", package)
    if errors:
        print("Check errors.csv before interpreting completeness.", file=sys.stderr)

if __name__ == "__main__":
    main()
