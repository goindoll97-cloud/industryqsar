"""Unit tests for EPA QSAR evidence + RDKit analogue separation; entirely synthetic."""
import csv
import json
from pathlib import Path
import sys

import pytest
pytest.importorskip("rdkit")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qsar_candidate_screen import (molecule, load_structures, load_test_predictions,
                                  value_as_mgkg, run)


def test_molecular_scope():
    assert molecule("c1ccccc1")[1] == "valid_single_component_organic"
    assert molecule("[Na+].[Cl-]")[1] == "multi_component_or_salt_requires_review"
    assert molecule("C[O-]")[1] == "charged_species_requires_review"
    assert molecule("[Fe]")[1] == "inorganic_no_carbon_outside_pilot_scope"
    assert molecule("not_a_smiles")[1] == "rdkit_parse_failed"


def test_epa_test_minus_log_molkg_conversion_and_ad(tmp_path):
    f = tmp_path / "epa_test.csv"
    f.write_text("cas,ld50_value,ld50_unit,ad_status,model_name\n"
                 "108-88-3,3,-log10(mol/kg),inside,EPA_TEST_5.1.2_consensus\n",
                 encoding="utf-8")
    p = load_test_predictions(f)["108-88-3"]
    assert p["unit"] == "-log10(mol/kg)"
    assert 90 < value_as_mgkg(p, 92.14) < 95


def test_e2e_registry_reference_and_candidate_are_distinct(tmp_path):
    reg = tmp_path / "registry.csv"
    reg.write_text("cas,유해성물질\n71-43-2,인체급성유해성물질\n",
                   encoding="utf-8-sig")
    epa = tmp_path / "epa.csv"
    epa.write_text("CASRN,QSAR_READY_SMILES,DTXSID\n"
                   "71-43-2,c1ccccc1,DTXSID-REF\n"
                   "108-88-3,Cc1ccccc1,DTXSID-CAND\n"
                   "67-64-1,CC(C)=O,DTXSID-OTHER\n"
                   "7647-14-5,[Na+].[Cl-],DTXSID-SALT\n", encoding="utf-8-sig")
    pred = tmp_path / "pred.csv"
    pred.write_text("cas,ld50_value,ld50_unit,ad_status,model_name\n"
                    "108-88-3,3,-log10(mol/kg),inside,EPA_TEST_5.1.2_consensus\n"
                    "67-64-1,120,mg/kg,outside,EPA_TEST_5.1.2_consensus\n", encoding="utf-8")
    summary = run(epa, reg, pred, tmp_path / "result")
    assert summary["registered_reference_structures_available"] == 1
    assert summary["candidate_structures_usable_not_in_supplied_snapshot"] == 2
    with (tmp_path / "result" / "qsar_candidates.csv").open(encoding="utf-8-sig") as f:
        rows = {r["cas"]: r for r in csv.DictReader(f)}
    assert "71-43-2" not in rows
    assert rows["108-88-3"]["nearest_reference_cas"] == "71-43-2"
    assert rows["108-88-3"]["review_tier"] == "P1_QSAR_ORAL_SIGNAL_REPORTED_INSIDE_AD"
    assert rows["108-88-3"]["epa_test_threshold_relation"] == "meets"
    assert rows["67-64-1"]["review_tier"] == "P2_QSAR_SIGNAL_AD_UNCERTAIN"
    assert "qsar_applicability_domain_not_confirmed_inside" in rows["67-64-1"]["quality_flags"]
    assert all(r["legal_designation_determined"] == "false" for r in rows.values())
    with (tmp_path / "result" / "structure_manual_review.csv").open(encoding="utf-8-sig") as f:
        rejected = list(csv.DictReader(f))
    assert rejected[0]["cas"] == "7647-14-5"
    assert rejected[0]["reason"] == "multi_component_or_salt_requires_review"


def test_identical_smiles_different_cas_requires_identifier_review(tmp_path):
    reg = tmp_path / "registry.csv"
    reg.write_text("cas\n71-43-2\n", encoding="utf-8")
    epa = tmp_path / "epa.csv"
    epa.write_text("CASRN,SMILES\n71-43-2,c1ccccc1\n108-88-3,c1ccccc1\n", encoding="utf-8")
    summary = run(epa, reg, None, tmp_path / "out")
    with (tmp_path / "out" / "qsar_candidates.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["review_tier"] == "IDENTIFIER_REVIEW_FIRST"
    assert summary["external_qsar_predictions_loaded"] == 0


def test_conflicting_smiles_same_cas_does_not_choose_first(tmp_path):
    p = tmp_path / "epa.csv"
    p.write_text("cas,smiles\n71-43-2,c1ccccc1\n71-43-2,CCO\n", encoding="utf-8")
    structures, audit = load_structures(p)
    assert audit["conflicting_cas"] == 1
    assert structures["71-43-2"]["mol"] is None
    assert structures["71-43-2"]["status"] == "conflicting_structures_same_cas"


def test_mixed_registry_must_not_be_accepted(tmp_path):
    reg = tmp_path / "reg.csv"
    reg.write_text("cas,유해성물질\n71-43-2,인체만성유해성물질\n", encoding="utf-8")
    epa = tmp_path / "epa.csv"
    epa.write_text("cas,smiles\n71-43-2,c1ccccc1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="인체급성 이외"):
        run(epa, reg, None, tmp_path / "result")



def test_domestic_candidate_allowlist_and_kosha_discordance(tmp_path):
    registry = tmp_path / "ref.csv"
    registry.write_text("cas,유해성물질\n71-43-2,인체급성유해성물질\n", encoding="utf-8")
    structs = tmp_path / "structures.csv"
    structs.write_text(
        "CASRN,SMILES,DTXSID\n"
        "71-43-2,c1ccccc1,ref\n"
        "108-88-3,Cc1ccccc1,candidate\n"
        "67-64-1,CC(C)=O,irrelevant\n", encoding="utf-8")
    domestic = tmp_path / "domestic.csv"
    domestic.write_text("cas\n108-88-3\n75-09-2\n", encoding="utf-8")
    predictions = tmp_path / "test.csv"
    predictions.write_text(
        "cas,ld50_value,ld50_unit,ad_status,model_name\n"
        "108-88-3,100,mg/kg,inside,EPA_TEST_demo\n", encoding="utf-8")
    kosha = tmp_path / "kosha.csv"
    kosha.write_text(
        "cas,route,extraction_status,reported_metric,qualifier,value,unit,species_as_written,reported_source\n"
        "108-88-3,oral,parsed_unverified,LD50,=,900,mg/kg,Rat,MSDS_reference_unverified\n",
        encoding="utf-8")
    summary = run(structs, registry, predictions, tmp_path / "result", domestic, kosha)
    assert summary["candidate_universe_provided"] is True
    assert summary["domestic_candidate_universe_missing_from_epa_export"] == 1
    assert summary["qsar_kosha_numeric_disagreement_count"] == 1
    with (tmp_path / "result/qsar_candidates.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["cas"] == "108-88-3"
    assert rows[0]["qsar_msds_numeric_agreement"] == "disagree"
    assert rows[0]["kosha_oral_numeric_relation_reported"] == "above"
    assert rows[0]["review_tier"] == "P1_QSAR_ORAL_SIGNAL_REPORTED_INSIDE_AD"
    assert "qsar_msds_numeric_discordance_sources_not_independent" in rows[0]["quality_flags"]
    with (tmp_path / "result/candidate_structure_missing.csv").open(encoding="utf-8-sig") as f:
        missing = list(csv.DictReader(f))
    assert missing[0]["cas"] == "75-09-2"
    with (tmp_path / "result/evidence_manual_review.csv").open(encoding="utf-8-sig") as f:
        manual = list(csv.DictReader(f))
    assert len(manual) == 1


def test_kosha_msds_without_qsar_is_unverified_review_signal(tmp_path):
    r = tmp_path / "r.csv"
    r.write_text("cas\n71-43-2\n", encoding="utf-8")
    s = tmp_path / "s.csv"
    s.write_text("cas,smiles\n71-43-2,c1ccccc1\n108-88-3,Cc1ccccc1\n", encoding="utf-8")
    k = tmp_path / "k.csv"
    k.write_text(
        "cas,route,extraction_status,reported_metric,qualifier,value,unit,species_as_written,reported_source\n"
        "108-88-3,oral,parsed_unverified,LD50,<,200,mg/kg,Rat,source_only\n",
        encoding="utf-8")
    run(s, r, None, tmp_path / "out", None, k)
    with (tmp_path / "out/qsar_candidates.csv").open(encoding="utf-8-sig") as f:
        row = next(csv.DictReader(f))
    assert row["review_tier"] == "P2_KOSHA_REPORTED_ORAL_SIGNAL_UNVERIFIED"
    assert row["epa_test_threshold_relation"] == "not_available"


def test_raw_vs_qsar_ready_salt_change_requires_manual_review(tmp_path):
    p = tmp_path / "epa.csv"
    p.write_text(
        "CASRN,QSAR_READY_SMILES,SMILES,DTXSID\n"
        "71-43-2,c1ccccc1,c1ccccc1,ref\n"
        "108-88-3,CCN,CCN.Cl,changed\n", encoding="utf-8")
    structs, audit = load_structures(p)
    assert structs["71-43-2"]["status"] == "valid_single_component_organic"
    assert structs["108-88-3"]["status"] == "epa_structure_standardization_difference_requires_review"
    assert structs["108-88-3"]["mol"] is None
