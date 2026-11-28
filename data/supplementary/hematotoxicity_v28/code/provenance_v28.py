"""
v0.28 — Dataset B provenance resolution for the TRI-only and semiconductor-core gaps.

Addresses gaps G06 (EPA TRI listing version and per-substance listing basis) and
G07 (exact citation for 4 of the 249 semiconductor-core records).

Neither gap can be closed outright: the historical TRI list export captured at
collection time and the Korean chemical-use survey document are not in the
archive, and EPA's current machine-readable TRI chemical list is served from
guideme.epa.gov, which this environment does not reach.

What this script does instead is BOUND each gap - establish how many records in
the actual analysis set depend on the missing provenance, and what those records
are - so the residual uncertainty can be stated quantitatively in the paper
rather than left open-ended.
"""

import os
import sys
import pandas as pd

V27 = sys.argv[1]
TAB = sys.argv[2]
T27 = os.path.join(V27, "tables")


def main():
    tri = pd.read_csv(f"{T27}/S07_TRI_provenance_28.csv", dtype=str).fillna("")
    sem = pd.read_csv(f"{T27}/S07_semiconductor_scope_249.csv", dtype=str).fillna("")
    cand = pd.read_csv(f"{T27}/S08_screening_candidates_2519.csv", dtype=str).fillna("")

    rows = []

    # ---- G06: TRI-only substances -------------------------------------
    in_cand = set(cand.CAS)
    for _, r in tri.iterrows():
        inside = r.CAS in in_cand
        rows.append(dict(
            gap_id="G06", cas=r.CAS, chemical=r.chemical,
            population_role="TRI_only_population_entry",
            in_screening_candidate_set=int(inside),
            analysis_status=r.v26_analysis_status,
            inhalation_candidate=r.tri_inhalation_candidate,
            human_flag=r.tri_human_flag,
            official_evidence_status=r.official_evidence_status,
            missing_provenance="original TRI list version and per-substance listing basis",
            recorded_source_file=r.v27_population_source_file,
            recorded_source_sha256=r.v27_population_source_sha256,
            official_programme_url=r.v27_TRI_program_url,
            independent_source_available="no",
            analytical_impact=("affects a screening candidate" if inside
                               else "no analytical impact: not in the candidate set"),
            resolution_required=("original TRI list export captured at collection time; EPA's "
                                 "current machine-readable list is at guideme.epa.gov"),
        ))

    # ---- G07: semiconductor-core records with a pending citation ------
    pend = sem[sem.process_evidence_level == "usage_survey_citation_pending"]
    for _, r in pend.iterrows():
        ids = [i.strip() for i in str(r.process_source_ids).split(";") if i.strip()]
        other = [i for i in ids if i != "Korea2014_2022"]
        rows.append(dict(
            gap_id="G07", cas=r.CAS, chemical=r.chemical,
            population_role="semiconductor_core_scope_entry",
            in_screening_candidate_set=int(r.CAS in in_cand),
            analysis_status=r.v26_analysis_status,
            inhalation_candidate="", human_flag="",
            official_evidence_status=r.actual_inhalation_exposure,
            missing_provenance="Korea2014_2022 chemical-use survey: formal citation pending",
            recorded_source_file="user-provided Table 6",
            recorded_source_sha256="",
            official_programme_url=r.process_source_urls,
            independent_source_available=("yes: " + "; ".join(other)) if other else "no",
            analytical_impact=(
                "sole source is the uncited survey table" if not other else
                "an independent peer-reviewed source is also recorded, so the pending citation "
                "is supplementary"),
            resolution_required="the Korean chemical-use survey document and its Table 6 page",
        ))

    out = pd.DataFrame(rows)
    out.to_csv(f"{TAB}/S07c_dataset_B_provenance_resolution.csv", index=False)
    print(f"  S07c_dataset_B_provenance_resolution.csv  rows={len(out)}")

    g6 = out[out.gap_id == "G06"]
    print(f"\n=== G06: TRI-only substances ({len(g6)}) ===")
    print(f"  in the 2,519 screening candidate set : {int(g6.in_screening_candidate_set.sum())}")
    print(f"  flagged as TRI inhalation candidates : "
          f"{(g6.inhalation_candidate == 'True').sum()}")
    print(f"  carrying a human flag                : {(g6.human_flag == 'True').sum()}")
    print("  analysis status of those in the candidate set:")
    print(g6[g6.in_screening_candidate_set == 1].chemical.str.title().to_string(index=False))

    g7 = out[out.gap_id == "G07"]
    print(f"\n=== G07: semiconductor-core records with pending citation ({len(g7)}) ===")
    for _, r in g7.iterrows():
        print(f"  CAS {r.cas:13s} {r.chemical[:42]:44s} {r.analysis_status}")
        print(f"      independent source: {r.independent_source_available[:70]}")
    sole = g7[g7.independent_source_available == "no"]
    print(f"\n  records whose SOLE source is the uncited survey table: {len(sole)}")
    if len(sole):
        print("  " + ", ".join(f"{r.cas} ({r.analysis_status})" for _, r in sole.iterrows()))


if __name__ == "__main__":
    main()
