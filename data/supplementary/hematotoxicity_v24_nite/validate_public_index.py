"""Check integrity of the public v0.24 NITE staging index, not toxicity validity."""
import csv
import hashlib
import json
from pathlib import Path

p = Path(__file__).resolve().parent
m = json.loads((p / "manifest.json").read_text(encoding="utf-8"))
f = p / "nite_blood_public_index.csv"
assert hashlib.sha256(f.read_bytes()).hexdigest() == m["public_index"]["sha256"]
with f.open(encoding="utf-8", newline="") as fh:
    rows = list(csv.DictReader(fh))
assert len(rows) == len({r["CAS"] for r in rows}) == 562
for r in rows:
    d = r["CAS"].replace("-", "")
    assert d.isdigit() and sum(i * int(x) for i, x in enumerate(d[-2::-1], 1)) % 10 == int(d[-1])
    for k in ("nite_SE", "nite_RE", "marrow_or_hematopoietic_target", "same_row_human_inhalation_cues", "in_A", "in_B"):
        assert r[k] in ("0", "1")
    assert r["nite_SE"] == "1" or r["nite_RE"] == "1"
new = [r for r in rows if r["in_A"] == "0"]
ready = [r for r in new if r["existing_B_status"] == "EPA_checked_novel_candidate"]
assert len(new) == 537 and len(ready) == 123
assert sum(r["in_B"] == "1" for r in rows) == 234
assert sum(r["marrow_or_hematopoietic_target"] == "1" for r in rows) == 60
assert sum(r["same_row_human_inhalation_cues"] == "1" for r in rows) == 152
assert sum(r["marrow_or_hematopoietic_target"] == "1" or r["same_row_human_inhalation_cues"] == "1" for r in ready) == 63
assert sum(r["nite_SE"] == "1" and r["nite_RE"] == "0" for r in rows) == 73
assert sum(r["nite_SE"] == "0" and r["nite_RE"] == "1" for r in rows) == 310
assert sum(r["nite_SE"] == "1" and r["nite_RE"] == "1" for r in rows) == 179
print("OK: 562 official hazard candidates; no new toxicity label or model validation.")
