"""Fully synthetic QA of A/B/C evidence layer comparison."""
import csv
import io
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qsar_ablation import run


def test_evidence_ablation_distinguishes_added_support_from_accuracy(tmp_path):
    input_file = tmp_path / "candidates.csv"
    input_file.write_text(
        "cas,epa_test_threshold_relation,epa_test_ad_reported,structural_similarity_signal,"
        "kosha_oral_numeric_relation_reported,qsar_msds_numeric_agreement\n"
        "71-43-2,meets,inside,not_high_similarity,above,disagree\n"
        "108-88-3,above,inside,high_similarity_review_only,not_reported,not_assessable\n"
        "67-64-1,not_available,not_provided,not_high_similarity,meets,not_assessable\n"
        "75-09-2,above,inside,not_high_similarity,above,agree\n",
        encoding="utf-8",
    )
    summary = run(input_file, tmp_path / "out")
    assert summary["candidates"] == 4
    assert summary["review_signal_counts"] == {
        "A_qsar_only_review": 1,
        "B_qsar_plus_structure_review": 2,
        "C_plus_kosha_reported_review": 3,
    }
    assert summary["newly_flagged_by_structure_B_minus_A"] == 1
    assert summary["newly_flagged_by_msds_C_minus_B"] == 1
    assert summary["no_ground_truth_accuracy_metrics_computed"] is True
    with (tmp_path / "out/method_ablation_comparison.csv").open(encoding="utf-8-sig") as f:
        data = {r["cas"]: r for r in csv.DictReader(f)}
    assert data["71-43-2"]["method_c_qsar_structure_msds"] == "qsar_msds_numeric_disagreement_review"
    assert data["108-88-3"]["method_b_qsar_plus_structure"] == "analogue_hypothesis_no_ld50_inference"
    assert data["67-64-1"]["method_c_qsar_structure_msds"] == "msds_reported_oral_signal_unverified"
    assert data["75-09-2"]["a_review_signal"] == "false"
