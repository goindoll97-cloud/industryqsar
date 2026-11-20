"""No-network regression test for saved KOSHA section-11 archives."""
import csv
import io
import json
import zipfile
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reparse_kosha_zip import repack


def test_reparse_existing_xml_no_network(tmp_path):
    original = tmp_path / "original.zip"
    xml = ("""<response><item><msdsItemCode>K040202</msdsItemCode>
    <itemDetail>LD50 147 mg/kg 실험종 : Rat (랫드 LD50=147mg/kg)</itemDetail>
    </item><item><msdsItemCode>K040204</msdsItemCode>
    <itemDetail>자료없음</itemDetail></item></response>""").encode("utf-8")
    with zipfile.ZipFile(original, "w") as z:
        z.writestr("raw_xml\\001_section11.xml", xml)
        z.writestr("kosha_search_results.csv",
                   "queried_cas,search_status,selected_chem_id\n"
                   "624-18-0,exact_cas_match,111\n"
                   "29664-84-4,no_hit,\n")
        z.writestr("human_acute_endpoints.csv", "cas,value\n624-18-0,\n")
        z.writestr("kosha_audit.json", json.dumps({"structured_human_endpoint_rows": 0}))
        z.writestr("raw_xml\\001_search.xml", "<response/>")
    output = tmp_path / "reparsed.zip"
    result = repack(original, output)
    assert result["api_requests_performed"] == 0
    assert result["structured_endpoint_rows"] == 2
    with zipfile.ZipFile(output) as z:
        data = list(csv.DictReader(io.StringIO(z.read("human_acute_endpoints.csv").decode("utf-8-sig"))))
        assert data[0]["value"] == "147"
        assert data[0]["extraction_note"] == "repeated_identical_value_in_text"
        assert z.read("raw_xml\\001_section11.xml") == xml
        audit = json.loads(z.read("kosha_audit.json").decode("utf-8"))
        assert audit["human_acute_reparse"]["extraction_status_counts"]["parsed_unverified"] == 1
        assert audit["structured_human_endpoint_rows"] == 2


def test_prevent_source_overwrite(tmp_path):
    path = tmp_path / "same.zip"
    with zipfile.ZipFile(path, "w"):
        pass
    with pytest.raises(ValueError, match="덮어"):
        repack(path, path)
