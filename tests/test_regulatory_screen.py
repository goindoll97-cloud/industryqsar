"""Stage-2 offline tests; all numbers/registry entries here are SYNTHETIC examples."""
from pathlib import Path
import csv
import io
import json
import sys
import zipfile
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regulatory_screen import (
    valid_cas, registry_meta, load_registry, read_csv_bytes, load_batch,
    evidence_relation, assess, run, load_qsar,
)


def search_row(cas, status="exact_cas_match"):
    return {"queried_cas": cas, "search_status": status}


def endpoint(cas="71-43-2", route="oral", value="150", qualifier="=", species="Rat", source="ECHA"):
    return {
        "cas": cas, "route": route, "extraction_status": "parsed_unverified",
        "reported_metric": "LD50" if route != "inhalation" else "LC50",
        "qualifier": qualifier, "value": value,
        "unit": "mg/l" if route == "inhalation" else "mg/kg",
        "species_as_written": species, "reported_source": source,
        "duration_hours": "" if route != "inhalation" else "4",
        "raw_detail": "synthetic example",
    }


def test_cas_validity_and_format():
    assert valid_cas("71-43-2")
    assert valid_cas("108-88-3")
    assert not valid_cas("71-43-3")
    assert not valid_cas("hello")


@pytest.mark.parametrize("value,op,expected", [
    ("150", "=", "meets"), ("300", "<=", "meets"),
    ("300", ">", "above"), ("2000", ">", "above"),
    ("200", ">", "ambiguous"), ("600", "<", "ambiguous"),
])
def test_oral_censoring_logic(value, op, expected):
    rel, _ = evidence_relation(endpoint(value=value, qualifier=op))
    assert rel == expected


def test_species_unknown_does_not_count_as_verified():
    rel, issues = evidence_relation(endpoint(species=""))
    assert rel == "meets"
    assert "rodent_species_unconfirmed" in issues
    outcome, _ = assess([search_row("71-43-2")], [endpoint(species="")], {}, None, {})
    assert outcome[0]["screening_priority"] == "P1_oral_signal"
    assert "high_signal_requires_source_species_validation" in outcome[0]["quality_flags"]
    assert outcome[0]["legal_designation_verified"] == "false"


def test_nonoral_unassessed_and_not_safe():
    rows, qa = assess([search_row("71-43-2")], [endpoint(route="inhalation", value="0.1")], {}, None, {})
    assert rows[0]["screening_priority"] == "P3_other_routes"
    assert rows[0]["oral_numeric_relation"] == "not_reported"
    assert qa[0]["endpoint_numeric_relation"] == "not_assessed"


def test_no_registry_not_mislabelled_as_unregulated():
    rows, _ = assess([search_row("71-43-2")], [endpoint()], {}, None, {})
    assert rows[0]["designated_acute_registry_status"] == "registry_not_provided"
    assert rows[0]["screening_priority"] == "P1_oral_signal"


def test_registry_explicit_match_and_partial_absence():
    reg = {"71-43-2": ["X-01"]}
    partial = {"coverage": "partial"}
    rows, _ = assess([search_row("71-43-2"), search_row("108-88-3")],
                     [endpoint(), endpoint("108-88-3", value="900")],
                     reg, partial, {})
    found = {x["cas"]: x for x in rows}
    assert found["71-43-2"]["screening_priority"] == "reference_listed"
    assert found["71-43-2"]["registry_notice_ids"] == "X-01"
    assert found["108-88-3"]["designated_acute_registry_status"] == "not_found_in_partial_snapshot_unknown"


def test_registry_metadata_required_and_mixed_class_filter(tmp_path):
    registry = tmp_path / "registry.csv"
    registry.write_text(
        "CAS No,유해성물질,고유번호\n71-43-2,인체급성유해성물질,DEMO-001\n"
        "108-88-3,인체만성유해성물질,DEMO-002\n", encoding="utf-8-sig")
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps({
        "coverage": "partial", "source_url": "https://www.law.go.kr/",
        "snapshot_date": "2026-11-20", "acute_only": False,
    }), encoding="utf-8")
    loaded, settings, diag = load_registry(registry, meta)
    assert "71-43-2" in loaded
    assert "108-88-3" not in loaded
    assert diag["nonacute_rows_ignored"] == 1
    with pytest.raises(ValueError, match="--registry-meta"):
        load_registry(registry, None)


def test_invalid_registry_cas_rejected(tmp_path):
    r = tmp_path / "r.csv"
    r.write_text("cas,유해성물질\n71-43-3,인체급성유해성물질\n", encoding="utf-8")
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps({
        "coverage": "partial", "source_url": "https://www.law.go.kr/",
        "snapshot_date": "2026-11-20", "acute_only": False,
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="CAS 오류"):
        load_registry(r, meta)


def test_qsar_conflict_and_ad(tmp_path):
    q = tmp_path / "qsar.csv"
    q.write_text("cas,qsar_oral_ld50,qsar_ad,model_name\n71-43-2,100,inside,CATMoS\n", encoding="utf-8")
    qs = load_qsar(q)
    rows, _ = assess([search_row("71-43-2")], [endpoint(value="800")], {}, None, qs)
    assert rows[0]["screening_priority"] == "P2_discordance"
    assert "msds_and_qsar_disagree_check_independence" in rows[0]["quality_flags"]
    assert rows[0]["qsar_model"] == "CATMoS"


def make_zip(path):
    def csvtext(cols, rows):
        f = io.StringIO()
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)
        return f.getvalue()
    a = csvtext(["queried_cas", "search_status"], [search_row("71-43-2"), search_row("108-88-3")])
    e_rows = [endpoint(), endpoint("108-88-3", value="2000", qualifier=">")]
    e = csvtext(list(e_rows[0]), e_rows)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("kosha_batch/kosha_search_results.csv", a)
        z.writestr("kosha_batch/human_acute_endpoints.csv", e)
        z.writestr("kosha_batch/kosha_audit.json", json.dumps({"fetched_at_utc": "SYNTHETIC"}))


def test_end_to_end_zip_no_api_key_and_reproducible(tmp_path):
    zip_path = tmp_path / "batch.zip"
    make_zip(zip_path)
    summary = run(None, zip_path, tmp_path / "reports", None, None, None)
    assert summary["input_compounds"] == 2
    assert summary["registry_missing_for_all"] is True
    assert summary["priority_counts"]["P1_oral_signal"] == 1
    assert (tmp_path / "reports/review_queue.csv").exists()
    with (tmp_path / "reports/screening_priorities.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert all(row["legal_designation_verified"] == "false" for row in rows)
    assert all(row["model_training_performed"] == "false" for row in rows)


def test_zip_duplicates_rejected(tmp_path):
    p = tmp_path / "dupes.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("a/kosha_search_results.csv", "queried_cas,search_status\n")
        z.writestr("b/kosha_search_results.csv", "queried_cas,search_status\n")
        z.writestr("a/human_acute_endpoints.csv", "cas,route\n")
    with pytest.raises(ValueError, match="중복"):
        load_batch(None, p)


def test_official_group_without_cas_downgrades_complete_claim(tmp_path):
    reg = tmp_path / "official.csv"
    reg.write_text(
        "cas,유해성물질,고유번호\n"
        "71-43-2,인체급성유해성물질,EXAMPLE-1\n"
        ",인체급성유해성물질,EXAMPLE-GROUP\n", encoding="utf-8")
    meta_path = tmp_path / "metadata.json"
    meta_path.write_text(json.dumps({
        "coverage": "complete_acute_list",
        "source_url": "https://www.law.go.kr/",
        "snapshot_date": "2026-11-20",
        "acute_only": False,
    }), encoding="utf-8")
    mapping, meta, diag = load_registry(reg, meta_path)
    assert mapping["71-43-2"] == ["EXAMPLE-1"]
    assert diag["coverage_downgraded_due_to_casless_groups"] is True
    assert diag["unmapped_acute_rows_no_cas"] == 1
    assert meta["coverage"] == "partial"
    result, _ = assess([search_row("108-88-3")], [endpoint(cas="108-88-3")], mapping, meta, {})
    assert result[0]["designated_acute_registry_status"] == "not_found_in_partial_snapshot_unknown"
