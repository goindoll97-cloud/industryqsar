"""
v0.28 — NITE blood-system STOT rationale: evidence-unit extraction.

Purpose
-------
STEP 2-4 of the hematotoxicity screening protocol require that, for every
official NITE blood-system STOT classification, we record:

  * the evidence SPECIES actually responsible for the observation
    (human vs. animal, and which animal species),
  * the actual EXPOSURE ROUTE of the study that produced the observation,
  * the hematotoxicity ENDPOINT TYPE observed.

The central methodological requirement is that these are read at the level of
an individual EVIDENCE UNIT, not at the level of the whole rationale cell.
A single NITE rationale routinely contains human occupational data, animal
inhalation data and animal oral data in consecutive sentences. Whole-cell
keyword matching therefore cannot distinguish

    "hematotoxicity was observed in an inhalation study"          (route evidence)
from
    "inhalation of the vapour causes dizziness ... effects on the
     blood were seen after gavage administration"                 (route mentioned only)

and cannot distinguish human from animal attribution when both appear in the
same paragraph. Everything below operates per segment and keeps the verbatim
segment text so each assignment is auditable.

Segmentation
------------
Two NITE rationale formats exist (see survey: FY2018-FY2023 vs. the rest):

  1. Structured:  "[Rationale for the Classification] ... [Evidence Data] (1) ... (2) ..."
     The bracketed rationale section is the classifier's own reasoning, not a
     study, and is kept separately as `section="rationale"`. Each numbered
     item under [Evidence Data] becomes one evidence unit.

  2. Narrative prose (no markers). Segmented into sentences. Sentences are a
     conservative unit: they under-call multi-sentence study descriptions
     rather than over-call co-occurrence across unrelated studies.

Output is a long table of one row per (substance_id, hazard_class, segment).

IMPORTANT — what this module is and is not
------------------------------------------
This is a structured *extraction* that produces a review-ready worksheet with
verbatim quotes. It is NOT an expert toxicological adjudication, and a row
being populated here does NOT mean the row has been reviewed. Automated output
is marked `review_state="extracted_pending_expert_confirmation"`. Rows a human
has actually read are promoted separately, by substance, in the manual review
table. No label in this module establishes a positive hematotoxicity call.
"""

import re

# --------------------------------------------------------------------------
# Lexicons. Each entry is (label, regex). Regexes are matched case-insensitively
# against a single segment. Word boundaries are used to avoid substring hits
# (e.g. "rat" must not match "generation", "ip" must not match "equipment").
# --------------------------------------------------------------------------

HUMAN_CUES = [
    ("human",            r'\bin humans?\b|\bhumans?\b'),
    ("worker",           r'\bworkers?\b|\boccupational(?:ly)?\b|\bworkplace\b|\bfactory\b|\bworkshop\b'),
    ("patient_case",     r'\bpatients?\b|\bcase report\b|\bpoisoning (?:case|incident)\b|\bautopsy\b|\bfatal(?:ity|ities)?\b'),
    ("volunteer",        r'\bvolunteers?\b'),
    ("epidemiology",     r'\bcross-sectional\b|\bcohort stud\w+\b|\bcase-control\b|\bepidemiolog\w+\b'),
    ("person_narrative", r'\ba (?:woman|man|boy|girl|male|female) (?:who|aged|of)\b|\bchildren\b|\binfants?\b'),
    ("accidental",       r'\baccidental(?:ly)?\b|\bintentional(?:ly)? (?:ingest|inhal)\w*\b|\bsuicid\w+\b'),
]

ANIMAL_SPECIES = [
    ("rat",        r'\brats?\b'),
    ("mouse",      r'\bmice\b|\bmouse\b'),
    ("rabbit",     r'\brabbits?\b'),
    ("dog",        r'\bdogs?\b|\bbeagles?\b'),
    ("guinea_pig", r'\bguinea[- ]pigs?\b'),
    ("monkey",     r'\bmonkeys?\b|\bmacaques?\b|\bprimates?\b'),
    ("hamster",    r'\bhamsters?\b'),
    ("cat",        r'\bcats?\b'),
    ("pig",        r'\bpigs?\b|\bswine\b|\bminipigs?\b'),
    ("sheep",      r'\bsheep\b|\bgoats?\b'),
    ("cattle",     r'\bcattle\b|\bcows?\b|\bcalves\b'),
    ("bird",       r'\bchickens?\b|\bquail\b|\bbirds?\b'),
    ("fish",       r'\bfish\b|\btrout\b|\bcarp\b'),
    ("generic",    r'\b(?:experimental |laboratory )?animals?\b|\brodents?\b'),
]

ROUTE_CUES = [
    ("inhalation", r'\binhalation\b|\binhal(?:ed|ing)\b|\bnose[- ]only\b|\bwhole[- ]body exposure\b'
                   r'|\brespirator\w+ exposure\b|\bvapou?r exposure\b|\baerosol exposure\b'
                   r'|\bmist exposure\b|\bexposure (?:to|by) (?:vapou?r|aerosol|mist|dust|air)\b'
                   r'|\bair(?:borne)? concentration\b|\bmg/m3\b|\bmg/m\^?3\b|\bppm\b'),
    # NOTE on "ppm": NITE uses ppm for airborne concentration in inhalation
    # studies and for DIETARY concentration in feeding studies ("300 ppm in the
    # diet"). The oral lexicon therefore has to capture every feeding wording
    # NITE uses, otherwise a feeding study whose dose is given in ppm is read as
    # an inhalation study. "dosed by feeding" / "fed" are the common forms.
    ("oral",       r'\boral(?:ly)?\b|\bgavage\b|\bdietar\w+\b|\bin the diet\b|\bfeeding (?:stud|test)\w*\b'
                   r'|\bdosed by feeding\b|\bby feeding\b|\bin the feed\b|\badministered in the diet\b'
                   r'|\bfed\b|\bchow\b|\bdiet\b|\bfeeding\b'
                   r'|\bdrinking[- ]water\b|\bingest(?:ion|ed)\b|\bper os\b|\bby mouth\b|\bswallow\w*\b'),
    ("dermal",     r'\bdermal(?:ly)?\b|\bcutaneous\b|\bpercutaneous\b|\btopical(?:ly)?\b'
                   r'|\bskin (?:application|contact|absorption|painting)\b|\bapplied to the skin\b'),
    ("injection",  r'\bintraperitoneal\w*\b|\bi\.p\.\b|\bsubcutaneous\w*\b|\bs\.c\.\b'
                   r'|\bintravenous\w*\b|\bi\.v\.\b|\binject(?:ion|ed)\b|\bintramuscular\w*\b'),
    ("in_vitro",   r'\bin vitro\b|\bcultured? cells?\b|\bcell[- ]free\b|\bhuman (?:blood|erythrocyte) suspension\b'),
    ("read_across",r'\bread[- ]across\b|\banalogu?e\b|\bstructurally similar\b|\bsurrogate substance\b'
                   r'|\bby analogy\b|\bgrouping approach\b'),
]

# Hematotoxicity endpoint types. Type 1-3 follow the protocol; "coagulation"
# is kept as a separate fourth bucket because NITE classifies "blood
# coagulation system" as a target organ and haemostatic effects are outside
# the protocol's Type 1-3 framework.
ENDPOINT_CUES = {
    "type1_hb_function": [
        ("methemoglobin",     r'\bmet[h]?a?emoglobin\w*\b'),
        ("carboxyhemoglobin", r'\bcarboxyh?a?emoglobin\w*\b'),
        ("sulfhemoglobin",    r'\bsulf?h?a?emoglobin\w*\b'),
        ("cyanosis",          r'\bcyanosis\b|\bcyanotic\b'),
    ],
    "type2_rbc_anemia": [
        ("hemolytic_anemia",  r'\bh?a?emolytic an(?:a)?emia\b'),
        ("hemolysis",         r'\bh?a?emolysis\b|\bh?a?emolytic\b|\bh?a?emolyz\w+\b'),
        ("anemia",            r'\ban(?:a)?emia\b|\ban(?:a)?emic\b'),
        ("rbc_decrease",      r'\b(?:decreas\w+|reduc\w+|lower\w*|fall\w*) (?:in )?(?:the )?'
                              r'(?:peripheral )?(?:red blood cell|rbc|erythrocyte)\w*\b'
                              r'|\b(?:red blood cell|rbc|erythrocyte) (?:count )?(?:was |were )?'
                              r'(?:decreas\w+|reduc\w+)\b'),
        ("erythrocyte_damage",r'\berythrocyte\w*\b|\bred blood cells?\b|\brbcs?\b'),
        ("hemoglobin_decrease",r'\b(?:decreas\w+|reduc\w+|lower\w*) (?:in )?(?:the )?h?a?emoglobin\b'
                              r'|\bh?a?emoglobin (?:concentration |content |level )?(?:was |were )?'
                              r'(?:decreas\w+|reduc\w+)\b'),
        ("hematocrit",        r'\bh?a?ematocrit\b|\bpacked cell volume\b|\bpcv\b'),
        ("heinz_body",        r'\bheinz bod\w+\b'),
        ("rbc_morphology",    r'\banisocyt\w+\b|\bpoikilocyt\w+\b|\bspherocyt\w+\b'
                              r'|\bpolychromat\w+ erythrocyte\w*\b|\bbasophilic stippling\b'),
    ],
    "type3_counts_marrow": [
        ("bone_marrow",       r'\bbone marrow\b|\bmyeloid\b|\bmegakaryocyt\w+\b'),
        ("marrow_suppression",r'\bmyelosuppress\w+\b|\bbone marrow (?:suppression|depression|hypoplasia|'
                              r'atrophy|damage|toxicity|failure)\b|\bhypoplas\w+ of the bone marrow\b'),
        ("aplastic_anemia",   r'\baplastic an(?:a)?emia\b'),
        ("pancytopenia",      r'\bpancytopenia\b'),
        ("leukopenia",        r'\bleu[ck]openia\b|\bleu[ck]ocytopenia\b'),
        ("neutropenia",       r'\bneutropenia\b|\bagranulocytosis\b|\bgranulocytopenia\b'),
        ("thrombocytopenia",  r'\bthrombocytopenia\b'),
        ("wbc_decrease",      r'\b(?:decreas\w+|reduc\w+|lower\w*) (?:in )?(?:the )?(?:peripheral )?'
                              r'(?:white blood cell|wbc|leu[ck]ocyte|lymphocyte|neutrophil|granulocyte)\w*\b'
                              r'|\b(?:white blood cell|wbc|leu[ck]ocyte|lymphocyte|neutrophil)\w* '
                              r'(?:count )?(?:was |were )?(?:decreas\w+|reduc\w+)\b'),
        ("platelet_decrease", r'\b(?:decreas\w+|reduc\w+|lower\w*) (?:in )?(?:the )?platelet\w*\b'
                              r'|\bplatelet\w* (?:count )?(?:was |were )?(?:decreas\w+|reduc\w+)\b'),
        ("hematopoietic",     r'\bh?a?ematopoietic\b|\bh?a?emopoietic\b'),
        ("blood_cell_counts", r'\bwhite blood cells?\b|\bwbcs?\b|\bleu[ck]ocytes?\b|\bplatelets?\b'
                              r'|\blymphocyte counts?\b|\bneutrophils?\b|\bgranulocytes?\b'),
    ],
    "coagulation": [
        ("prothrombin",       r'\bprothrombin\b|\bpt\b(?! \d)|\baptt\b|\bactivated partial thromboplastin\b'),
        ("coagulation",       r'\bcoagulat\w+\b|\bclotting\b|\bfibrinogen\b|\banticoagul\w+\b'),
        ("hemorrhage",        r'\bh?a?emorrhag\w+\b|\bbleeding tendenc\w+\b'),
    ],
}

# Markers that an erythroid/haematopoietic finding may be a COMPENSATORY
# response to peripheral red-cell destruction rather than direct marrow injury.
COMPENSATORY_CUES = [
    ("reticulocytosis",            r'\breticulocyt\w+\b'),
    ("extramedullary",             r'\bextramedullary h?a?ematopoiesis\b'),
    ("erythroid_hyperplasia",      r'\berythroid hyperplasia\b|\bhyperplasia of the erythroid\b'),
    ("splenic_erythropoiesis",     r'\bsplenic (?:h?a?ematopoiesis|erythropoiesis)\b'),
    ("compensatory_wording",       r'\bcompensator\w+\b|\bregenerative an(?:a)?emia\b|\bresponsive an(?:a)?emia\b'),
]

# Statements of absence / non-adoption. A segment carrying one of these should
# not be read as positive evidence without a human looking at it.
NEGATION_CUES = [
    ("not_observed",   r'\bnot (?:observ\w+|seen|found|detect\w+|report\w+)\b|\bno (?:effects?|changes?|'
                       r'findings?) (?:on|in|were)\b|\bwere not\b|\bwas not\b'),
    ("not_adopted",    r'\bnot (?:adopt\w+|used as (?:a )?target organ)\b|\bnot classified\b'
                       r'|\bwas excluded\b|\bnot considered\b'),
    ("no_data",        r'\bno data available\b|\binsufficient (?:data|information)\b|\bnot available\b'),
]

# Study-design / dose context, useful for STEP 5 and for judging adequacy.
CONTEXT_CUES = [
    ("has_noael_loael",  r'\bnoael\b|\bloael\b|\bnoel\b|\bloel\b'),
    ("has_concentration",r'\b\d+(?:\.\d+)?\s*(?:ppm|mg/m3|mg/m\^?3|mg/kg(?:/day)?|mg/l|%)\b'),
    ("has_duration",     r'\b\d+[- ](?:day|week|month|year|hour|hr|h)\b|\b(?:chronic|subchronic|acute|'
                         r'single|repeated)[- ](?:exposure|dose|administration)\b'),
    ("guideline_study",  r'\boecd\b|\bntp\b|\bgood laboratory practice\b|\bglp\b|\btr-?\d+\b'),
    ("statistics",       r'\bsignificant\w*\b|\bp\s*[<=]\s*0?\.\d+\b|\bdose[- ]dependent\w*\b'),
]

# --------------------------------------------------------------------------

_SENT_SPLIT = re.compile(r'(?<=[.;])\s+(?=[A-Z("\[]|\d+\s*[-–])')
_ABBREV_FIX = re.compile(r'\b(?:i\.p|i\.v|s\.c|e\.g|i\.e|vol|no|approx|Fig|et al|cf|vs|Dr|Co|Ltd|Inc)\.$',
                         re.IGNORECASE)


# Contexts in which an animal-species word denotes a laboratory REAGENT or an
# assay substrate rather than the species actually dosed. "anti-sheep red blood
# cell antibody" and "sheep erythrocyte haemolysis assay" must not make sheep a
# test species. Removed before species matching.
REAGENT_CONTEXT = re.compile(
    r'anti-?(?:sheep|rabbit|horse|goat|mouse|rat)\b[^.;]{0,40}'
    r'|(?:sheep|horse|rabbit|chicken|guinea[- ]pig)\s+(?:red blood cell|erythrocyte|rbc|serum|'
    r'plasma|albumin|antibod)\w*'
    r'|(?:sheep|rabbit|horse|goat)\s+(?:anti)\w*'
    r'|fetal (?:bovine|calf) serum',
    re.IGNORECASE)


def _match_set(lexicon, text):
    """Return the labels in `lexicon` whose regex matches `text`."""
    out = []
    for label, pat in lexicon:
        if re.search(pat, text, re.IGNORECASE):
            out.append(label)
    return out


def _match_species(text):
    """Match test species after stripping reagent/assay-substrate contexts."""
    return _match_set(ANIMAL_SPECIES, REAGENT_CONTEXT.sub(" ", text))


def split_sentences(text):
    """Conservative sentence split that does not break on common abbreviations."""
    raw = _SENT_SPLIT.split(text)
    out, buf = [], ""
    for s in raw:
        cand = (buf + " " + s).strip() if buf else s.strip()
        if _ABBREV_FIX.search(cand):      # ends on an abbreviation -> keep joining
            buf = cand
            continue
        buf = ""
        if cand:
            out.append(cand)
    if buf:
        out.append(buf)
    return out


def segment_rationale(rationale):
    """
    Split one NITE rationale cell into evidence units.

    Returns a list of dicts: {section, unit_id, text}
      section "rationale"  -> the classifier's own reasoning (not a study)
      section "evidence"   -> a numbered [Evidence Data] item
      section "narrative"  -> a sentence from an unstructured rationale
    """
    text = re.sub(r'\s+', ' ', str(rationale)).strip()
    if not text:
        return []

    units = []
    m_ed = re.search(r'\[\s*Evidence Data\s*\]', text, re.IGNORECASE)
    if m_ed:
        head = text[:m_ed.start()].strip()
        body = text[m_ed.end():].strip()
        head = re.sub(r'^\[\s*Rationale for the Classification\s*\]\s*', '', head,
                      flags=re.IGNORECASE).strip()
        if head:
            units.append({"section": "rationale", "unit_id": "R", "text": head})
        # Numbered items: "(1) ... (2) ..." at the start of an item.
        marks = list(re.finditer(r'\((\d{1,2})\)\s', body))
        if marks:
            if marks[0].start() > 0:
                lead = body[:marks[0].start()].strip()
                if lead:
                    units.append({"section": "evidence", "unit_id": "E0", "text": lead})
            for i, mk in enumerate(marks):
                end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
                seg = body[mk.end():end].strip()
                if seg:
                    units.append({"section": "evidence", "unit_id": f"E{mk.group(1)}", "text": seg})
        elif body:
            units.append({"section": "evidence", "unit_id": "E0", "text": body})
        return units

    # Unstructured rationale -> sentences.
    for i, s in enumerate(split_sentences(text), start=1):
        if len(s) >= 25:                      # drop fragments / stray numbering
            units.append({"section": "narrative", "unit_id": f"S{i}", "text": s})
    return units


def classify_segment(text):
    """Extract species / route / endpoint / qualifier features from one segment."""
    human   = _match_set(HUMAN_CUES, text)
    animals = _match_species(text)
    routes  = _match_set(ROUTE_CUES, text)
    neg     = _match_set(NEGATION_CUES, text)
    comp    = _match_set(COMPENSATORY_CUES, text)
    ctx     = _match_set(CONTEXT_CUES, text)

    endpoints, ep_terms = [], []
    for etype, lex in ENDPOINT_CUES.items():
        hits = _match_set(lex, text)
        if hits:
            endpoints.append(etype)
            ep_terms += [f"{etype}:{h}" for h in hits]

    # "ppm"/"mg/m3" alone is weak inhalation evidence; an explicit inhalation
    # word is required. Without one, the inhalation hit is demoted to
    # "inhalation_unit_only" (a concentration unit, not a stated route), so a
    # feeding study dosed in dietary ppm is never read as an inhalation study.
    strong_inh = bool(re.search(
        r'\binhalation\b|\binhal(?:ed|ing)\b|\bnose[- ]only\b|\bwhole[- ]body exposure\b'
        r'|\bvapou?r exposure\b|\baerosol exposure\b|\bmist exposure\b', text, re.IGNORECASE))
    dietary_ppm = bool(re.search(r'\bppm\b', text, re.IGNORECASE)) and bool(
        re.search(r'\bfeed\w*\b|\bdiet\w*\b|\bfed\b|\bchow\b|\bdrinking[- ]water\b', text, re.IGNORECASE))
    if "inhalation" in routes and not strong_inh:
        routes = [r for r in routes if r != "inhalation"]
        routes.append("dietary_concentration_unit" if dietary_ppm else "inhalation_unit_only")

    # Species attribution for this segment.
    if human and animals:
        species_basis = "mixed_human_and_animal_in_segment"
    elif human:
        species_basis = "human"
    elif animals:
        species_basis = "animal"
    else:
        species_basis = "not_specified"

    # Route attribution for this segment.
    real_routes = [r for r in routes if r not in ("read_across", "in_vitro",
                                                  "inhalation_unit_only", "dietary_concentration_unit")]
    if len(real_routes) > 1:
        route_basis = "mixed_route_in_segment"
    elif len(real_routes) == 1:
        route_basis = real_routes[0]
    elif "in_vitro" in routes:
        route_basis = "in_vitro"
    elif "read_across" in routes:
        route_basis = "read_across"
    elif "dietary_concentration_unit" in routes:
        route_basis = "oral_dietary_concentration_inferred"
    elif "inhalation_unit_only" in routes:
        route_basis = "route_not_specified_air_unit_only"
    else:
        route_basis = "route_not_specified"

    return {
        "species_basis": species_basis,
        "human_cues": "; ".join(human),
        "animal_species": "; ".join(animals),
        "route_basis": route_basis,
        "route_cues": "; ".join(sorted(set(routes))),
        "strong_inhalation_wording": int(strong_inh),
        "endpoint_types": "; ".join(endpoints),
        "endpoint_terms": "; ".join(ep_terms),
        "compensatory_cues": "; ".join(comp),
        "negation_cues": "; ".join(neg),
        "context_cues": "; ".join(ctx),
        # Co-occurrence: an endpoint AND a resolved species AND a resolved route
        # in the SAME segment. This is the only configuration that supports a
        # route- and species-specific evidence statement.
        "cooccurrence": int(bool(endpoints)
                            and species_basis in ("human", "animal")
                            and route_basis in ("inhalation", "oral", "dermal", "injection")),
    }
