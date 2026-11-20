"""Synthetic offline checks of the EPA CompTox batch CAS handoff."""
import csv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prepare_epa_batch import build


def test_prepare_batch_preserves_roles_without_negative_labels(tmp_path):
    registry = tmp_path / "r.csv"
    registry.write_text("cas,유해성물질\n71-43-2,인체급성유해성물질\n", encoding="utf-8-sig")
    candidates = tmp_path / "c.csv"
    candidates.write_text("cas\n71-43-2\n108-88-3\n71-43-3\n", encoding="utf-8")
    target = tmp_path / "epa_batch_cas.txt"
    summary = build(registry, candidates, target)
    assert summary["cas_for_epa_batch"] == 2
    assert summary["candidate_universe_additional_cas"] == 1
    assert set(target.read_text().splitlines()) == {"71-43-2", "108-88-3"}
    with (tmp_path / "epa_batch_cas_roles.csv").open(encoding="utf-8-sig") as f:
        rows = {r["cas"]: r for r in csv.DictReader(f)}
    assert rows["71-43-2"]["input_role"] == "korean_acute_registry_reference"
    assert rows["108-88-3"]["input_role"] == "candidate_universe_user_supplied"
    assert all(r["regulatory_status_assumed"] == "none" for r in rows.values())
