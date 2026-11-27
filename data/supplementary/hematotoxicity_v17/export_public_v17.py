"""Export the v0.17 public projection from the full local v0.17 CSV files."""
import argparse
import csv
from pathlib import Path

COLUMNS = {
    "dataset_A_human_inhalation_references.csv": "reference_id chemical CAS SMILES InChIKey Evidence_level endpoint_class endpoint_reported route_basis toxicity_source_urls source_access limitations reference_use final_label".split(),
    "dataset_B_semiconductor_249.csv": "target_id CAS chemical SMILES structure_status process process_source_ids process_evidence_level actual_inhalation_exposure CDR2024_match matched_reference_id hematotoxicity_status identity_flags structure_source screening_role priority_score final_label".split(),
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Full local hematotoxicity_v17 directory")
    parser.add_argument("--output", type=Path, required=True, help="New public projection directory")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output must differ")
    args.output.mkdir(parents=True, exist_ok=True)
    for name, fields in COLUMNS.items():
        with (args.input/name).open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not set(fields).issubset(reader.fieldnames or []):
                raise ValueError(f"Missing columns in {name}")
            rows = list(reader)
        with (args.output/name).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", quoting=csv.QUOTE_ALL, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"{name}: {len(rows)} rows")

if __name__ == "__main__":
    main()
