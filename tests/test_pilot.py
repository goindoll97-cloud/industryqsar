from pathlib import Path
import csv
import json
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot import parse_ld50, relation, assess, run


def sample(**overrides):
    row = dict(compound_id="x", name="example", cas="123-45-6", substance_type="single",
               designation_status="not_designated", designation_status_source="official_checked_2026",
               msds_oral_ld50_raw="150", msds_basis="experimental", msds_species="rat",
               msds_route="oral", msds_unit="mg/kg", msds_source="source_record",
               qsar_oral_ld50_raw="180", qsar_ad="inside", qsar_source="model")
    row.update(overrides)
    return row


@pytest.mark.parametrize("value,expected", [
    ("300", "meets"), ("300.1", "above"), ("<=300", "meets"),
    ("<300", "meets"), (">300", "above"), (">=300", "ambiguous"),
    ("<1000", "ambiguous"), (">2000", "above"),
    ("100-200", "meets"), ("200-400", "ambiguous"),
    ("", "missing"), ("bad", "invalid"), ("-5", "invalid"),
    ("300 mg/kg", "meets"), ("300 mg/L", "invalid")
])
def test_threshold(value, expected):
    assert relation(value) == expected


def test_existing_data_signal():
    assert assess(sample())["priority_code"] == "review_existing_evidence"


def test_discordance():
    x = assess(sample(msds_oral_ld50_raw="800", qsar_oral_ld50_raw="120"))
    assert x["priority_code"] == "review_discordance"
    assert x["evidence_discordance"] == "true"


def test_qsar_not_trusted_outside_domain():
    x = assess(sample(msds_oral_ld50_raw="", qsar_oral_ld50_raw="90", qsar_ad="outside"))
    assert x["priority_code"] == "review_data_quality"


def test_missing_regulation_source_is_not_non_designated():
    assert assess(sample(designation_status_source=""))["priority_code"] == "verify_designation"


def test_designated_is_excluded():
    assert assess(sample(designation_status="designated"))["priority_code"] == "already_designated"


def test_not_a_rodent_oral_endpoint():
    assert assess(sample(msds_species="fish", qsar_oral_ld50_raw=""))["priority_code"] == "review_data_quality"


def test_example_end_to_end(tmp_path):
    root = Path(__file__).resolve().parents[1]
    run(root / "data/sample_synthetic.csv", tmp_path, demo=True, live_law=False)
    data = list(csv.DictReader((tmp_path / "screening_results.csv").open(encoding="utf-8-sig")))
    info = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert len(data) == 9
    assert info["mode"] == "SYNTHETIC_DEMO_ONLY"
    assert info["annex_threshold_automatically_verified"] is False
    assert (tmp_path / "manual_review.csv").exists()
