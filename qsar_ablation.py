#!/usr/bin/env python3
"""A/B/C evidence-layer comparison for a pre-existing QSAR candidate-screen CSV.

Compares review *flags*, not sensitivity, false-safe rates, legal designation,
or independent predictive accuracy. No additional model fitting or network calls.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

FIELDS = [
    "cas", "method_a_qsar_only", "method_b_qsar_plus_structure",
    "method_c_qsar_structure_msds", "a_review_signal", "b_review_signal",
    "c_review_signal", "qsar_ad", "qsar_oral_relation",
    "similarity_signal", "kosha_reported_oral_relation",
    "qsar_msds_disagreement", "evidence_caveat",
]


def read_rows(path: Path):
    raw = path.read_bytes().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(raw, newline="")))
    needed = {"cas", "epa_test_threshold_relation", "epa_test_ad_reported",
              "structural_similarity_signal"}
    available = set(rows[0]) if rows else set()
    if needed - available:
        raise ValueError("QSAR 후보결과 필수 열 누락: " + ", ".join(sorted(needed - available)))
    return rows


def classify(r: dict):
    rel = r.get("epa_test_threshold_relation", "")
    ad = r.get("epa_test_ad_reported", "")
    similarity = r.get("structural_similarity_signal", "")
    msds_rel = r.get("kosha_oral_numeric_relation_reported", "not_reported")
    disagreement = r.get("qsar_msds_numeric_agreement", "") == "disagree"

    # A: Only the pre-trained EPA TEST rat oral LD50 QSAR evidence.
    if rel == "meets" and ad == "inside":
        a = "qsar_oral_threshold_signal_inside_reported_ad"
    elif rel == "meets":
        a = "qsar_oral_threshold_signal_ad_unconfirmed"
    elif rel in ("above",):
        a = "no_positive_oral_qsar_signal_not_safe"
    else:
        a = "qsar_not_evaluable"
    a_review = rel == "meets"

    # B: add chemical-structure analogue hypotheses, but never infer LD50.
    b = a
    b_review = a_review
    if similarity == "identical_structure_review":
        b = "structure_identifier_review"
        b_review = True
    elif not a_review and similarity == "high_similarity_review_only":
        b = "analogue_hypothesis_no_ld50_inference"
        b_review = True

    # C: add KOSHA MSDS reports. These may share a source with TEST training.
    c = b
    c_review = b_review
    if disagreement:
        c = "qsar_msds_numeric_disagreement_review"
        c_review = True
    elif msds_rel == "meets" and not b_review:
        c = "msds_reported_oral_signal_unverified"
        c_review = True

    return {
        "cas": r["cas"], "method_a_qsar_only": a,
        "method_b_qsar_plus_structure": b, "method_c_qsar_structure_msds": c,
        "a_review_signal": str(a_review).lower(),
        "b_review_signal": str(b_review).lower(),
        "c_review_signal": str(c_review).lower(),
        "qsar_ad": ad, "qsar_oral_relation": rel,
        "similarity_signal": similarity,
        "kosha_reported_oral_relation": msds_rel,
        "qsar_msds_disagreement": str(disagreement).lower(),
        "evidence_caveat": "flags_only_not_validated_hazard_classifier",
    }


def run(path: Path, out: Path):
    candidates = read_rows(path)
    outcomes = [classify(r) for r in candidates]
    out.mkdir(parents=True, exist_ok=True)
    with (out / "method_ablation_comparison.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(outcomes)
    counts = {
        "A_qsar_only_review": sum(r["a_review_signal"] == "true" for r in outcomes),
        "B_qsar_plus_structure_review": sum(r["b_review_signal"] == "true" for r in outcomes),
        "C_plus_kosha_reported_review": sum(r["c_review_signal"] == "true" for r in outcomes),
    }
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidates": len(outcomes), "review_signal_counts": counts,
        "newly_flagged_by_structure_B_minus_A": sum(r["b_review_signal"] == "true" and
                                                      r["a_review_signal"] == "false" for r in outcomes),
        "newly_flagged_by_msds_C_minus_B": sum(r["c_review_signal"] == "true" and
                                                 r["b_review_signal"] == "false" for r in outcomes),
        "qsar_msds_numeric_disagreements": sum(r["qsar_msds_disagreement"] == "true" for r in outcomes),
        "method_c_reason_counts": dict(Counter(r["method_c_qsar_structure_msds"] for r in outcomes)),
        "no_ground_truth_accuracy_metrics_computed": True,
        "note": "A/B/C compares evidence-layer screening queues, not sensitivity, precision, classification accuracy, or legally non-designated status. An independent experimental LD50 reference and no-leakage evaluation are required for claims about predictive performance.",
    }
    (out / "method_ablation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"candidates": len(outcomes), **counts}, ensure_ascii=False, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description="Compare QSAR-only vs QSAR+RDKit vs QSAR+RDKit+KOSHA review flags")
    parser.add_argument("--screen", type=Path, required=True, help="qsar_candidates.csv")
    parser.add_argument("--out", type=Path, default=Path("outputs/qsar_ablation"))
    args = parser.parse_args()
    try:
        run(args.screen, args.out)
    except (OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
