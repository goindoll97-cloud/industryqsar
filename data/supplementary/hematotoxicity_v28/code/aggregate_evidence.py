"""
v0.28 — aggregate NITE rationale evidence segments to per-substance evidence roles.

Produces the STEP 3 (species / exposure route) and STEP 4 (hematotoxicity type)
classification tables from the segment-level extraction.

Evidence tiers (per substance, highest tier reached)
----------------------------------------------------
  A_human_inhalation      a single segment states an explicit inhalation word,
                          a human subject, and a hematotoxicity endpoint
  B_human_inhalation_likely
                          human + hematotoxicity endpoint, with exposure given
                          only as an airborne concentration (ppm / mg/m3) or with
                          inhalation named alongside another route in the same
                          segment -> route is probable but not textually isolated
  C_human_route_unclear   human + hematotoxicity endpoint, route not resolvable
  D_animal_inhalation     animal + explicit inhalation + endpoint
  E_animal_other_route    animal + oral/dermal/injection + endpoint
  F_endpoint_only         endpoint present, species or route unresolved
  G_no_endpoint_text      blood-system STOT classification with no endpoint term
                          recovered from the rationale text

Tiers are EVIDENCE-TEXT tiers, not toxicity labels. Tier A does not make a
substance a verified human inhalation hematotoxicant: the protocol requires
independent primary-source verification before any analysis-grade human or
animal route-specific reference is used. Nothing here sets a positive label.
"""

import pandas as pd
import re

SEG = "/home/user/v028/work/nite_evidence_segments.csv"

ENDPOINT_TYPES = ["type1_hb_function", "type2_rbc_anemia", "type3_counts_marrow", "coagulation"]


def _join_unique(series, sep="; ", limit=None):
    seen, out = set(), []
    for v in series:
        for part in str(v).split("; "):
            p = part.strip()
            if p and p not in seen:
                seen.add(p); out.append(p)
    if limit:
        out = out[:limit]
    return sep.join(out)


def tier_for(seg):
    """Evidence tier contributed by one segment."""
    ep = seg["endpoint_types"] != ""
    sp, rt = seg["species_basis"], seg["route_basis"]
    human = sp == "human"
    mixed = sp == "mixed_human_and_animal_in_segment"
    animal = sp == "animal"
    if not ep:
        return "G_no_endpoint_text"
    if human and rt == "inhalation":
        return "A_human_inhalation"
    if (human or mixed) and rt in ("route_not_specified_air_unit_only", "mixed_route_in_segment"):
        return "B_human_inhalation_likely"
    if human:
        return "C_human_route_unclear"
    if animal and rt == "inhalation":
        return "D_animal_inhalation"
    if animal and rt in ("oral", "dermal", "injection", "oral_dietary_concentration_inferred"):
        return "E_animal_other_route"
    return "F_endpoint_only"


TIER_ORDER = ["A_human_inhalation", "B_human_inhalation_likely", "C_human_route_unclear",
              "D_animal_inhalation", "E_animal_other_route", "F_endpoint_only",
              "G_no_endpoint_text"]


def main():
    d = pd.read_csv(SEG, dtype=str).fillna("")
    # The "[Rationale for the Classification]" section is the classifier's own
    # reasoning, not a study report; exclude it from evidence tiering.
    ev = d[d.section != "rationale"].copy()
    ev["tier"] = ev.apply(tier_for, axis=1)

    rows = []
    for sid, g in ev.groupby("substance_id"):
        tiers_present = [t for t in TIER_ORDER if (g.tier == t).any()]
        best = tiers_present[0] if tiers_present else "G_no_endpoint_text"
        ep_flags = {}
        for et in ENDPOINT_TYPES:
            hit = g[g.endpoint_types.str.contains(et, regex=False)]
            ep_flags[et] = int(len(hit) > 0)
            # route/species backing for this endpoint type specifically
            ep_flags[et + "__human_inhalation"] = int(
                ((hit.species_basis == "human") & (hit.route_basis == "inhalation")).any())
            ep_flags[et + "__animal_inhalation"] = int(
                ((hit.species_basis == "animal") & (hit.route_basis == "inhalation")).any())

        # Type 3 covers BOTH peripheral blood-cell-count change AND marrow /
        # haematopoietic injury. These must be separated, because a marrow or
        # haematopoietic signal can be a compensatory (regenerative) response to
        # peripheral red-cell destruction rather than direct marrow injury.
        #
        #   MARROW_TERMS      wording that names the marrow / haematopoietic
        #                     compartment itself
        #   marrow_clean      a marrow-term segment carrying NO compensatory cue
        #                     -> unambiguous direct marrow injury
        #   marrow_compens    marrow terms appear ONLY in segments that also
        #                     carry compensatory cues -> ambiguous, withhold
        #   peripheral only   Type 3 present but no marrow term at all
        MARROW_TERMS = (r"marrow_suppression|aplastic_anemia|pancytopenia|"
                        r"bone_marrow|hematopoietic")
        t3 = g[g.endpoint_types.str.contains("type3_counts_marrow", regex=False)]
        marrow_any = t3[t3.endpoint_terms.str.contains(MARROW_TERMS, regex=True)]
        marrow_clean = marrow_any[marrow_any.compensatory_cues == ""]
        marrow_direct = marrow_clean                      # kept for the flag below
        compensatory = t3[t3.compensatory_cues != ""]
        t2 = g[g.endpoint_types.str.contains("type2_rbc_anemia", regex=False)]
        hemolytic = t2[t2.endpoint_terms.str.contains("hemolytic_anemia|hemolysis", regex=True)]

        g0 = g.iloc[0]
        rows.append({
            "substance_id": sid,
            "cas_all": g0.cas_all,
            "name": g0["name"],
            "nite_blood_categories": _join_unique(g.blood_categories),
            "nite_blood_target_terms": _join_unique(g.blood_core_terms),
            "nite_marrow_or_hematopoietic_target": g.marrow_or_hematopoietic.max(),
            "nite_coagulation_only": g0.coagulation_only,
            "hazard_classes": _join_unique(g.hazard_class),
            "classification_years": _join_unique(g.year),
            "evidence_tier": best,
            "all_tiers_present": "; ".join(tiers_present),
            "n_segments": len(g),
            "n_segments_with_endpoint": int((g.endpoint_types != "").sum()),
            "human_segments": int((g.species_basis == "human").sum()),
            "animal_segments": int((g.species_basis == "animal").sum()),
            "animal_species_named": _join_unique(g.animal_species),
            "routes_observed": _join_unique(g.route_basis),
            "human_cue_types": _join_unique(g.human_cues),
            **ep_flags,
            "type3_marrow_term_present": int(len(marrow_any) > 0),
            "type3_direct_marrow_wording": int(len(marrow_direct) > 0),
            "type3_compensatory_wording": int(len(compensatory) > 0),
            "type3_resolution": (
                "not_assigned_no_type3_wording" if len(t3) == 0 else
                "type3_marrow_injury_supported" if len(marrow_clean) > 0 else
                "type3_marrow_signal_compensatory_only" if len(marrow_any) > 0 else
                "type3_peripheral_counts_only"),
            "type2_hemolytic_wording": int(len(hemolytic) > 0),
            "compensatory_vs_direct_note": (
                "both_direct_marrow_and_compensatory_wording_present"
                if len(marrow_direct) and len(compensatory) else
                "compensatory_wording_only_no_direct_marrow_wording"
                if len(compensatory) and not len(marrow_direct) else
                "direct_marrow_wording_only" if len(marrow_direct) else ""),
            "negation_in_endpoint_segments": int((g[(g.endpoint_types != "")].negation_cues != "").sum()),
            "has_noael_loael": int(g.context_cues.str.contains("has_noael_loael", regex=False).any()),
            "has_quantified_exposure": int(g.context_cues.str.contains("has_concentration", regex=False).any()),
            "review_state": "extracted_pending_expert_confirmation",
        })

    out = pd.DataFrame(rows).sort_values(["evidence_tier", "name"])
    out.to_csv("/home/user/v028/work/nite_substance_evidence_roles.csv", index=False)

    print("substances aggregated:", len(out))
    print("\n=== evidence tier (highest reached per substance) ===")
    print(out.evidence_tier.value_counts().reindex(TIER_ORDER).dropna().to_string())
    print("\n=== hematotoxicity endpoint types present in rationale text ===")
    for et in ENDPOINT_TYPES:
        print(f"  {et:24s} any={out[et].astype(int).sum():4d}"
              f"   human-inhalation-backed={out[et+'__human_inhalation'].astype(int).sum():3d}"
              f"   animal-inhalation-backed={out[et+'__animal_inhalation'].astype(int).sum():3d}")
    print("\n=== Type 3 resolution (peripheral counts vs. marrow injury vs. compensatory) ===")
    print(out.type3_resolution.value_counts().to_string())
    print("\n=== substances with NO endpoint term recovered from text ===",
          int((out.evidence_tier == "G_no_endpoint_text").sum()))
    return out


if __name__ == "__main__":
    main()
