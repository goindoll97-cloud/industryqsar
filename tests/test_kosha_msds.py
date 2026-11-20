"""Offline contract tests: no KOSHA credentials or real API calls required."""
import csv
import json
from pathlib import Path
import sys

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kosha_msds import (
    KoshaClient, candidate_mentions, error_message, flattened_fields,
    read_cas_csv, run, xml_items, xml_text,
)
import xml.etree.ElementTree as ET


SEARCH_XML = b"""<response><header><resultCode>00</resultCode></header><body><items>
<item><chemId>111</chemId><casNo>71-43-2</casNo><chemName>benzene</chemName></item>
</items></body></response>"""
SECTION_11 = b"""<response><header><resultCode>00</resultCode></header><body><items>
<item><msdsItemCode>K040202</msdsItemCode><msdsItemNameKor>oral</msdsItemNameKor>
<itemDetail>LD50 930 mg/kg Rat</itemDetail></item>
</items></body></response>"""

class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, search=SEARCH_XML):
        self.calls = []
        self.search = search

    def get(self, url, params, headers, timeout):
        self.calls.append((url, dict(params)))
        if url.endswith("getChemList001"):
            return FakeResponse(self.search)
        if url.endswith("getChemDetail111"):
            return FakeResponse(SECTION_11)
        raise AssertionError("unexpected operation")


def test_list_schema_and_cas_search():
    fake = FakeSession()
    client = KoshaClient("example%2Fencoded", session=fake)
    raw, hits = client.search_cas("71-43-2")
    assert raw == SEARCH_XML
    assert hits[0]["chemId"] == "111"
    assert fake.calls[0][1]["searchCnd"] == "1"
    assert fake.calls[0][1]["serviceKey"] == "example/encoded"


def test_extract_mentions_without_declaring_experimental_values():
    root = ET.fromstring(SECTION_11)
    text = xml_text(root)
    assert "LD50 930 mg/kg" in text
    matches = candidate_mentions(text)
    assert any("LD50" in s for s in matches)
    assert not any("experimental" in s for s in matches)
    assert candidate_mentions("Daphnia magna 48h EC50 12 mg/L") == []


def test_api_error_xml_detected():
    root = ET.fromstring("<response><header><resultCode>30</resultCode><resultMsg>Invalid key</resultMsg></header></response>")
    assert "30" in error_message(root)


def test_end_to_end_search_and_sections_are_unverified(tmp_path):
    fake = FakeSession()
    audit = run(["71-43-2"], tmp_path, True, "chemId", 5, 10, 0, KoshaClient("SECRET123", session=fake))
    assert audit["exact_unique_cas_matched"] == 1
    assert audit["sections_downloaded"] == 1
    assert audit["structured_human_endpoint_rows"] == 1
    assert audit["experimental_provenance_verified"] is False
    assert audit["legal_designation_checked"] is False
    assert len(fake.calls) == 2
    assert fake.calls[1][1]["chemId"] == "111"
    with (tmp_path / "screening_input_template.csv").open(encoding="utf-8-sig") as f:
        row = next(csv.DictReader(f))
    assert row["designation_status"] == "unknown"
    assert row["msds_basis"] == ""
    assert row["msds_oral_ld50_raw"] == ""
    with (tmp_path / "kosha_endpoint_mentions.csv").open(encoding="utf-8-sig") as f:
        mention_rows = list(csv.DictReader(f))
    assert {r["section"] for r in mention_rows} == {"11"}
    with (tmp_path / "human_acute_endpoints.csv").open(encoding="utf-8-sig") as f:
        structured = list(csv.DictReader(f))
    assert len(structured) == 1
    assert structured[0]["route"] == "oral"
    assert structured[0]["value"] == "930"
    assert all(x["evidence_status"] == "UNVERIFIED_TEXT_ONLY" for x in mention_rows)
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert "SECRET123" not in path.read_text(encoding="utf-8-sig")


def test_wrong_cas_result_cannot_be_accepted(tmp_path):
    mismatched = SEARCH_XML.replace(b"71-43-2", b"108-88-3")
    fake = FakeSession(search=mismatched)
    audit = run(["71-43-2"], tmp_path, True, "chemId", 5, 10, 0,
                KoshaClient("dummy", session=fake))
    assert audit["exact_unique_cas_matched"] == 0
    assert len(fake.calls) == 1


def test_missing_recognizable_id_not_automatically_accepted(tmp_path):
    response = SEARCH_XML.replace(b"<chemId>111</chemId>", b"<someUnknownId>111</someUnknownId>")
    fake = FakeSession(search=response)
    audit = run(["71-43-2"], tmp_path, True, "chemId", 5, 10, 0,
                KoshaClient("dummy", session=fake))
    assert audit["sections_downloaded"] == 0


def test_cas_csv_input(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text("cas\n71-43-2\n108-88-3\n", encoding="utf-8")
    assert read_cas_csv(p) == ["71-43-2", "108-88-3"]


def test_reject_wrong_base():
    with pytest.raises(ValueError):
        KoshaClient("abc", base_url="https://example.org")


def test_environmental_section_disallowed():
    client = KoshaClient("dummy", session=FakeSession())
    with pytest.raises(ValueError, match="11번만"):
        client.detail("111", "12", "chemId")
