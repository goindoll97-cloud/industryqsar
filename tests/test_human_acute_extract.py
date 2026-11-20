"""Realistic fixtures based on KOSHA section-11 XML field structure (no credentials)."""
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from human_acute_extract import parse_section11, write_csv


SAMPLE = b"""<response><header><resultCode>00</resultCode></header><body><items>
<item><msdsItemCode>K040202</msdsItemCode><msdsItemNameKor>oral</msdsItemNameKor>
<itemDetail>LD50 &amp;gt;2000 mg/kg Rat</itemDetail></item>
<item><msdsItemCode>K040204</msdsItemCode><msdsItemNameKor>dermal</msdsItemNameKor>
<itemDetail>LD50 &amp;gt;8260 mg/kg Rabbit</itemDetail></item>
<item><msdsItemCode>K040206</msdsItemCode><msdsItemNameKor>inhalation</msdsItemNameKor>
<itemDetail>vapor LC50 10000 ppm 7 hr Rat</itemDetail></item>
<item><msdsItemCode>K0420</msdsItemCode><itemDetail>unrelated chronic value</itemDetail></item>
</items></body></response>"""


def test_extract_routed_endpoints_and_preliminary_oral_relation():
    rows = parse_section11(SAMPLE, "71-43-2", "001008")
    assert [r["route"] for r in rows] == ["oral", "dermal", "inhalation"]
    assert rows[0]["value"] == "2000"
    assert rows[0]["qualifier"] == ">"
    assert rows[0]["unit"] == "mg/kg"
    assert rows[0]["oral_ld50_300_relation_preliminary"] == "above_numeric_criterion"
    assert rows[1]["value"] == "8260"
    assert rows[1]["oral_ld50_300_relation_preliminary"] == "not_assessed"
    assert rows[2]["value"] == "10000"
    assert rows[2]["unit"] == "ppm"
    assert rows[2]["duration_hours"] == "7"
    assert rows[2]["oral_ld50_300_relation_preliminary"] == "not_assessed"
    assert all("NOT_INDEPENDENTLY_VERIFIED" in r["evidence_verification"] for r in rows)


def test_missing_data_and_ambiguous_inequality():
    xml = """<response><item><msdsItemCode>K040202</msdsItemCode>
    <itemDetail>LD50 &amp;gt;200 mg/kg</itemDetail></item>
    <item><msdsItemCode>K040204</msdsItemCode><itemDetail>자료없음</itemDetail></item>
    </response>""".encode("utf-8")
    rows = parse_section11(xml, "123-45-6")
    assert rows[0]["oral_ld50_300_relation_preliminary"] == "ambiguous"
    assert rows[1]["extraction_status"] == "no_reported_value"


def test_incomplete_or_multiple_values_fail_closed():
    xml = """<response><item><msdsItemCode>K040202</msdsItemCode>
    <itemDetail>LD50 150 mg/kg; LD50 200 mg/kg</itemDetail></item>
    </response>""".encode("utf-8")
    rows = parse_section11(xml, "123-45-6")
    assert rows[0]["extraction_status"] == "manual_review_multiple_values"
    assert rows[0]["value"] == ""


def test_xml_export_csv(tmp_path):
    rows = parse_section11(SAMPLE, "71-43-2", "001008")
    target = tmp_path / "human_acute_endpoints.csv"
    write_csv(target, rows)
    with target.open(encoding="utf-8-sig") as f:
        result = list(csv.DictReader(f))
    assert len(result) == 3


def test_no_ecotoxicity_section_used():
    xml = """<response><item><msdsItemCode>K040202</msdsItemCode>
    <itemDetail>LD50 250 mg/kg</itemDetail></item>
    <item><msdsItemCode>X_EC50</msdsItemCode>
    <itemDetail>Daphnia EC50 0.01 mg/L</itemDetail></item>
    </response>""".encode("utf-8")
    rows = parse_section11(xml, "123-45-6")
    assert len(rows) == 1
    assert rows[0]["route"] == "oral"
