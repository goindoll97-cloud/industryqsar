"""
v0.28 — source-citation register from NITE blood-system rationale text.

Why this matters for STEP 5
---------------------------
The protocol requires that any analysis-grade human- or animal-route-specific
reference be traced to its primary study. NITE rationale text, however, almost
never cites a primary journal article: it cites authoritative secondary
compilations (EHC, CICAD, IARC, ATSDR, EU-RAR, DFGOT, ACGIH, PATTY, HSDB) or
Japanese national assessments (NITE/CERI/NEDO Initial Risk Assessment Report,
Ministry of the Environment risk assessments). A small number of entries cite a
primary test report directly (NTP TR numbers, OECD TG study descriptions).

Consequently a NITE rationale establishes the OFFICIAL CLASSIFICATION and its
stated basis, but it does not by itself constitute primary-source verification.
Each citation is therefore tagged by evidence layer:

  primary_test_report      a specific study report identifiable from the text
                           (NTP TR number; an OECD TG + GLP study description)
  authoritative_review     international/regional secondary compilation
  national_assessment      Japanese government assessment report
  secondary_database       compiled database entry (HSDB, GESTIS, ChemIDplus)
  other / unclassified     citation form not recognised

Because the same underlying study is frequently cited by several compilations,
citation counts here MUST NOT be treated as counts of independent studies.
"""

import pandas as pd
import re
from collections import Counter

# Ordered: the first pattern that matches a citation string wins.
SOURCE_PATTERNS = [
    ("NTP technical report",          "primary_test_report",   r'\bNTP\s*TR[-\s]?(\d+)\b'),
    ("NTP (other)",                   "primary_test_report",   r'\bNTP\b'),
    ("OECD test guideline study",     "primary_test_report",   r'\bOECD\s*TG\s*(\d+)\b'),
    ("IARC monograph",                "authoritative_review",  r'\bIARC\b'),
    ("IPCS EHC",                      "authoritative_review",  r'\bEHC\s*(\d+)\b'),
    ("IPCS CICAD",                    "authoritative_review",  r'\bCICAD\s*(\d+)\b'),
    ("IPCS PIM",                      "authoritative_review",  r'\bPIM\s*(\d+)\b'),
    ("IPCS (other)",                  "authoritative_review",  r'\bIPCS\b'),
    ("EU risk assessment report",     "authoritative_review",  r'\bEU[-\s]?RAR\b'),
    ("EU CLH / CLP",                  "authoritative_review",  r'\bEU\s*CLH\b|\bCLP\b'),
    ("ECHA",                          "authoritative_review",  r'\bECHA\b'),
    ("ATSDR toxicological profile",   "authoritative_review",  r'\bATSDR\b'),
    ("ACGIH documentation",           "authoritative_review",  r'\bACGIH\b'),
    ("DFG MAK / DFGOT",               "authoritative_review",  r'\bDFGOT\b|\bDFG\s*MAK\b|\bDFG\b'),
    ("PATTY",                         "authoritative_review",  r'\bPATTY\b'),
    ("AICIS / NICNAS (Australia)",    "authoritative_review",  r'\bAICIS\b|\bNICNAS\b|\bIMAP\b|\bPEC\b'),
    ("OECD SIDS / SIAR",              "authoritative_review",  r'\bSIAR\b|\bSIDS\b'),
    ("WHO / JECFA / JMPR",            "authoritative_review",  r'\bJECFA\b|\bJMPR\b|\bWHO\b'),
    ("US EPA assessment",             "authoritative_review",  r'\bUS\s*EPA\b|\bIRIS\b'),
    ("NITE/CERI/NEDO initial risk assessment",
                                      "national_assessment",   r'Initial Risk Assessment Report'),
    ("CERI/NITE hazard assessment",   "national_assessment",   r'Hazard Assessment Report'),
    ("Japan Ministry of the Environment",
                                      "national_assessment",   r'Ministry of the Environment'),
    ("Food Safety Commission of Japan",
                                      "national_assessment",   r'Food Safety Commission of Japan'),
    ("Japan Society for Occupational Health",
                                      "national_assessment",   r'Japan Society for Occupational Health'),
    ("Japanese government GHS result", "national_assessment",  r'GHS classification result'),
    ("HSDB",                          "secondary_database",    r'\bHSDB\b'),
    ("GESTIS",                        "secondary_database",    r'\bGESTIS\b'),
    ("ChemIDplus / other database",   "secondary_database",    r'\bChemIDplus\b|\bRTECS\b|\bTOXNET\b'),
]

# Citation-looking parenthetical groups, e.g. "(EHC 150 (1993))" or
# "(DFGOT vol. 11 (1998), EU-RAR (2003))".
YEAR = re.compile(r'\b(19|20)\d{2}\b')


def iter_citation_strings(text):
    """Yield parenthetical spans that look like source citations."""
    depth, start = 0, None
    for i, ch in enumerate(text):
        if ch == '(':
            if depth == 0:
                start = i
            depth += 1
        elif ch == ')':
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    span = text[start + 1:i]
                    if YEAR.search(span) or re.search(r'\b(?:NTP|OECD|ACGIH|HSDB|IARC|EHC|CICAD)\b',
                                                      span, re.IGNORECASE):
                        yield span
                    start = None


def classify_citation(span):
    """Return [(source_name, evidence_layer, identifier)] for one citation span.

    A span frequently bundles several sources ("DFGOT vol. 11 (1998), EU-RAR
    (2003)"). Every recognised source in the span is returned, rather than
    splitting the span on commas first: comma-splitting fragments multi-part
    publisher names ("Initial Risk Assessment Report (NITE, CERI, NEDO)") into
    unclassifiable pieces.
    """
    found, seen = [], set()
    for name, layer, pat in SOURCE_PATTERNS:
        m = re.search(pat, span, re.IGNORECASE)
        if m and name not in seen:
            seen.add(name)
            found.append((name, layer, m.group(1) if m.lastindex else ""))
    return found or [("unclassified_citation", "other_unclassified", "")]


def main():
    segs = pd.read_csv("/home/user/v028/work/nite_evidence_segments.csv", dtype=str).fillna("")
    rows = []
    for _, r in segs.iterrows():
        for span in iter_citation_strings(r.segment_text):
            p = span.strip()
            if p:
                for name, layer, ident in classify_citation(p):
                    rows.append({
                        "substance_id": r.substance_id, "cas_all": r.cas_all, "name": r["name"],
                        "hazard_class": r.hazard_class, "unit_id": r.unit_id,
                        "segment_species_basis": r.species_basis,
                        "segment_route_basis": r.route_basis,
                        "segment_endpoint_types": r.endpoint_types,
                        "source_name": name, "evidence_layer": layer,
                        "source_identifier": ident,
                        "citation_verbatim": p[:300],
                    })
    c = pd.DataFrame(rows).drop_duplicates(
        subset=["substance_id", "hazard_class", "unit_id", "citation_verbatim", "source_name"])
    c.to_csv("/home/user/v028/work/nite_source_citations.csv", index=False)

    print("citation instances extracted:", len(c))
    print("substances with >=1 citation:", c.substance_id.nunique())
    print("\n=== evidence layer of cited sources ===")
    print(c.evidence_layer.value_counts().to_string())
    print("\n=== source register (top 30 by citation instances) ===")
    reg = (c.groupby(["source_name", "evidence_layer"])
             .agg(citation_instances=("substance_id", "size"),
                  substances=("substance_id", "nunique")).reset_index()
             .sort_values("citation_instances", ascending=False))
    print(reg.head(30).to_string(index=False))
    reg.to_csv("/home/user/v028/work/nite_source_register.csv", index=False)

    print("\n=== citations attached to a HUMAN + INHALATION + endpoint segment ===")
    hi = c[(c.segment_species_basis == "human") & (c.segment_route_basis == "inhalation")
           & (c.segment_endpoint_types != "")]
    print(hi[["name", "cas_all", "source_name", "evidence_layer", "citation_verbatim"]]
          .to_string(index=False, max_colwidth=46))

    print("\n=== substances whose blood-system rationale cites a PRIMARY test report ===")
    pr = c[c.evidence_layer == "primary_test_report"]
    print("substances:", pr.substance_id.nunique(), "| instances:", len(pr))
    print(pr.groupby("source_name").size().to_string())


if __name__ == "__main__":
    main()
