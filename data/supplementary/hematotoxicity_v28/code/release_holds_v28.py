"""
v0.28 / G14 — adjudicate the v0.27 'same_connectivity_only_hold' structure records.

Hypothesis under test
---------------------
The v0.27 EPA-based structure audit placed 40 substances on hold because the
registry InChIKey and the recomputed InChIKey agreed on connectivity but not in
full. The cross-registry comparison suggested the cause is not structural or
stereochemical ambiguity but an InChI STANDARDISATION difference: EPA stored
NON-STANDARD InChIKeys.

An InChIKey is  AAAAAAAAAAAAAA-BBBBBBBBFV-P  where

    AAAAAAAAAAAAAA   14 chars, skeleton / connectivity hash
    BBBBBBBB          8 chars, hash of the remaining layers (stereo, isotope)
    F                 1 char,  flag: 'S' = standard InChI, 'N' = non-standard
    V                 1 char,  InChI version ('A' = version 1)
    P                 1 char,  protonation

So a pair differing ONLY at position F ('N' vs 'S'), with identical skeleton
block, identical remaining-layers hash, identical version and identical
protonation, describes the SAME structure recorded under a different InChI
standard. Such a hold is an artefact and can be released.

A pair differing in the remaining-layers hash B, or in protonation P, is a
genuine stereochemical / isotopic / protonation difference and the hold must
stand.

Method
------
For every hold the EPA SMILES is re-parsed with RDKit 2025.09.4 and a STANDARD
InChIKey is computed independently. That recomputation, not the stored key, is
the arbiter. Decisions are recorded per substance with the evidence.
"""

import os
import re
import sys
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import inchi as rdinchi

RDLogger.DisableLog("rdApp.*")

V27 = sys.argv[1]
TAB = sys.argv[2]
T27 = os.path.join(V27, "tables")

KEY_RE = re.compile(r'^([A-Z]{14})-([A-Z]{8})([A-Z])([A-Z])-([A-Z])$')


def parse_key(k):
    """Split an InChIKey into (skeleton, layers, flag, version, protonation)."""
    m = KEY_RE.match(str(k).strip())
    return m.groups() if m else None


def main():
    s3 = pd.read_csv(f"{T27}/S03_structure_audit_562.csv", dtype=str).fillna("")
    holds = s3[s3.registry_status == "same_connectivity_only_hold"].copy()
    print(f"v0.27 same_connectivity_only_hold records: {len(holds)}")

    rows = []
    for _, r in holds.iterrows():
        epa_k, comp_k = r.EPA_InChIKey.strip(), r.computed_InChIKey.strip()
        pe, pc = parse_key(epa_k), parse_key(comp_k)

        # Independent recomputation of a STANDARD InChIKey from the EPA SMILES.
        recomp, parse_note = "", ""
        smi = r.EPA_SMILES.strip() or r.canonical_SMILES.strip()
        if smi:
            m = Chem.MolFromSmiles(smi)
            if m is None:
                parse_note = "RDKit could not parse the EPA SMILES"
            else:
                try:
                    recomp = rdinchi.MolToInchiKey(m) or ""
                except Exception as e:
                    parse_note = f"InChIKey recomputation failed: {type(e).__name__}"
        else:
            parse_note = "no SMILES available in the v0.27 audit row"

        pr = parse_key(recomp)

        # Scope test, applied BEFORE the standardisation test.
        #
        # Resolving the InChI standardisation question says the two keys describe
        # the same substance; it does NOT say that substance is inside the
        # study's structural domain. Rule R09 admits only single-component
        # organic molecules, so a salt or hydrate stays out however cleanly its
        # keys reconcile. Omitting this test in the first v0.28 run wrongly
        # released chlorpheniramine maleate and cyclophosphamide monohydrate;
        # the independent v0.29 audit caught it.
        n_frags, has_carbon = 0, False
        if smi:
            mm = Chem.MolFromSmiles(smi)
            if mm is not None:
                n_frags = len(Chem.GetMolFrags(mm))
                has_carbon = any(a.GetSymbol() == "C" for a in mm.GetAtoms())

        # Decision logic.
        decision, reason = "retain_hold_unresolved", ""
        if n_frags > 1:
            decision = "retain_hold_multicomponent_outside_structural_domain"
            reason = (f"SMILES has {n_frags} disconnected fragments (salt or hydrate); rule R09 "
                      f"admits single-component organic molecules only, so the substance stays "
                      f"outside the structural domain regardless of InChI standardisation")
        elif smi and not has_carbon:
            decision = "retain_hold_no_carbon_outside_structural_domain"
            reason = "no carbon atom; outside the organic structural domain (rule R09)"
        elif not (pe and pc):
            reason = "one or both stored keys are not in InChIKey format"
        elif pe[0] != pc[0]:
            decision, reason = ("retain_hold_connectivity_differs",
                                "skeleton blocks differ, so this is not a standardisation issue")
        else:
            same_layers = pe[1] == pc[1]
            same_proton = pe[4] == pc[4]
            same_version = pe[3] == pc[3]
            flag_differs = pe[2] != pc[2]
            epa_nonstandard = pe[2] == "N" and pc[2] == "S"
            if same_layers and same_proton and same_version and flag_differs and epa_nonstandard:
                # Confirm against the independent standard recomputation.
                if pr and recomp == comp_k:
                    decision = "release_hold_standardisation_artifact"
                    reason = ("EPA key carries the non-standard InChI flag 'N' where the standard "
                              "key carries 'S'; skeleton, remaining-layers hash, version and "
                              "protonation are identical, and an independent standard "
                              "recomputation from the EPA SMILES reproduces the standard key "
                              "exactly")
                elif pr and pr[0] == pe[0] and pr[1] == pe[1] and pr[4] == pe[4]:
                    decision = "release_hold_standardisation_artifact"
                    reason = ("EPA key carries the non-standard InChI flag 'N'; independent "
                              "standard recomputation agrees on skeleton, remaining layers and "
                              "protonation")
                else:
                    reason = ("flag difference looks like a standardisation artefact but the "
                              "independent recomputation did not confirm it" +
                              (f"; {parse_note}" if parse_note else ""))
            elif not same_layers:
                decision, reason = ("retain_hold_stereo_or_isotope_differs",
                                    "remaining-layers hash differs: a genuine stereochemical or "
                                    "isotopic difference")
            elif not same_proton:
                decision, reason = ("retain_hold_protonation_differs",
                                    "protonation character differs")
            else:
                reason = "keys differ in a way not covered by the standardisation rule"

        rows.append({
            "CAS": r.CAS, "nite_chemical": r.nite_chemical, "EPA_name": r.EPA_name,
            "EPA_DTXSID": r.EPA_DTXSID, "EPA_SMILES": smi,
            "EPA_InChIKey": epa_k, "v27_computed_InChIKey": comp_k,
            "v28_independent_standard_InChIKey": recomp,
            "epa_key_flag": pe[2] if pe else "", "computed_key_flag": pc[2] if pc else "",
            "n_fragments": n_frags, "has_carbon": int(has_carbon),
            "skeleton_blocks_identical": int(bool(pe and pc and pe[0] == pc[0])),
            "layers_hash_identical": int(bool(pe and pc and pe[1] == pc[1])),
            "protonation_identical": int(bool(pe and pc and pe[4] == pc[4])),
            "v27_registry_status": r.registry_status,
            "v27_scope_status": r.scope_status,
            "g14_decision": decision, "g14_reason": reason,
            "parse_note": parse_note,
            "review_state": "adjudicated_in_v028_G14",
        })

    out = pd.DataFrame(rows).sort_values(["g14_decision", "nite_chemical"])
    out.to_csv(f"{TAB}/S03d_G14_structure_hold_adjudication.csv", index=False)
    print(f"\n  S03d_G14_structure_hold_adjudication.csv  rows={len(out)}")
    print("\n=== G14 decisions ===")
    print(out.g14_decision.value_counts().to_string())
    print("\n=== flag pattern (EPA flag -> computed flag) ===")
    print(out.groupby(["epa_key_flag", "computed_key_flag"]).size().to_string())

    rel = out[out.g14_decision == "release_hold_standardisation_artifact"]
    print(f"\n=== released holds: {len(rel)} ===")
    for _, r in rel.iterrows():
        print(f"  {r.CAS:14s} {r.nite_chemical[:52]:54s} {r.EPA_InChIKey} -> {r.v27_computed_InChIKey}")
    ret = out[out.g14_decision != "release_hold_standardisation_artifact"]
    if len(ret):
        print(f"\n=== holds retained: {len(ret)} ===")
        for _, r in ret.iterrows():
            print(f"  {r.CAS:14s} {r.nite_chemical[:46]:48s} {r.g14_decision}")
            print(f"      {r.g14_reason[:110]}")
    return out


if __name__ == "__main__":
    main()
