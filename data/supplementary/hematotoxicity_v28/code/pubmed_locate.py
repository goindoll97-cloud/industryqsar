"""
v0.28 — locate primary literature for selected human-inhalation candidates.

This is a LOCATOR, not a verification. It records candidate primary references
(PMID, title, journal, year) for a small, explicitly chosen set of substances
whose NITE blood-system rationale asserts human inhalation hematotoxicity but
cites only a secondary compilation. Full-text adjudication of each study -
actual human exposure, actual inhalation route, single-substance attribution,
control group, statistical significance, clinical adversity versus biomarker
shift - is NOT performed here and remains open.

Queries and raw responses are cached so the run is reproducible.
"""

import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CACHE = "/home/user/v028/work/pubmed_cache"
SLEEP = 0.40          # NCBI asks unauthenticated clients to stay at <=3 req/s

# Substances selected because v0.28 placed them in evidence tier A
# (human + explicit inhalation + hematotoxicity endpoint in one evidence unit)
# and the cited source is a secondary compilation.
TARGETS = [
    ("10102-43-9", "Nitrogen monoxide",
     '("nitric oxide"[Title] OR "nitrogen monoxide"[Title]) AND '
     '(methemoglobin*[Title/Abstract] OR methaemoglobin*[Title/Abstract]) AND '
     '(inhalation[Title/Abstract] OR inhaled[Title/Abstract] OR volunteer*[Title/Abstract])'),
    ("110-80-5", "2-Ethoxyethanol (ethylene glycol monoethyl ether)",
     '("2-ethoxyethanol"[Title/Abstract] OR "ethylene glycol monoethyl ether"[Title/Abstract]) AND '
     '(anemia[Title/Abstract] OR anaemia[Title/Abstract] OR h*ematolog*[Title/Abstract] OR '
     'hemoglobin[Title/Abstract])'),
    ("95-53-4", "o-Toluidine",
     '("o-toluidine"[Title/Abstract] OR "ortho-toluidine"[Title/Abstract] OR '
     '"2-methylaniline"[Title/Abstract]) AND '
     '(methemoglobin*[Title/Abstract] OR methaemoglobin*[Title/Abstract])'),
    ("78-87-5", "1,2-Dichloropropane",
     '("1,2-dichloropropane"[Title/Abstract] OR "propylene dichloride"[Title/Abstract]) AND '
     '(h*emolytic[Title/Abstract] OR anemia[Title/Abstract] OR anaemia[Title/Abstract] OR '
     'h*ematolog*[Title/Abstract])'),
    ("58-89-9", "Lindane",
     '(lindane[Title/Abstract] OR "hexachlorocyclohexane"[Title/Abstract]) AND '
     '("aplastic anemia"[Title/Abstract] OR "aplastic anaemia"[Title/Abstract] OR '
     'agranulocytosis[Title/Abstract] OR pancytopenia[Title/Abstract])'),
]


def _get(url, key):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, key)
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    req = urllib.request.Request(url, headers={
        "User-Agent": "hematotoxicity-screening-research/0.28"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception as e:
        body = f"<error>{type(e).__name__}: {e}</error>"
    open(p, "w", encoding="utf-8").write(body)
    time.sleep(SLEEP)
    return body


def search(term, retmax=12):
    url = (f"{EUTILS}/esearch.fcgi?db=pubmed&retmode=json&retmax={retmax}"
           f"&term={urllib.parse.quote(term)}")
    key = "s_" + str(abs(hash(term))) + ".json"
    try:
        return json.loads(_get(url, key))["esearchresult"]
    except Exception:
        return {"count": "0", "idlist": []}


def summarise(pmids):
    if not pmids:
        return []
    url = (f"{EUTILS}/efetch.fcgi?db=pubmed&retmode=xml&id={','.join(pmids)}")
    key = "f_" + "_".join(pmids[:3]) + f"_{len(pmids)}.xml"
    xml = _get(url, key)
    out = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return out
    for art in root.iter("PubmedArticle"):
        pmid = art.findtext(".//PMID") or ""
        title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
        journal = art.findtext(".//Journal/ISOAbbreviation") or art.findtext(".//Journal/Title") or ""
        year = (art.findtext(".//JournalIssue/PubDate/Year")
                or art.findtext(".//JournalIssue/PubDate/MedlineDate") or "")
        ab = " ".join("".join(t.itertext()) for t in art.iter("AbstractText"))
        doi = ""
        for aid in art.iter("ArticleId"):
            if aid.get("IdType") == "doi":
                doi = aid.text or ""
        out.append(dict(pmid=pmid, title=title, journal=journal, year=year, doi=doi,
                        abstract_present=int(bool(ab.strip())), abstract_excerpt=ab[:600]))
    return out


def main():
    import pandas as pd
    rows = []
    for cas, name, term in TARGETS:
        res = search(term)
        ids = res.get("idlist", [])
        print(f"\n{'='*92}\n{name}  CAS {cas}\n  hits={res.get('count')}  retrieved={len(ids)}")
        for rec in summarise(ids):
            print(f"   PMID {rec['pmid']:10s} {rec['year']:6s} {rec['journal'][:26]:27s} "
                  f"{rec['title'][:78]}")
            rows.append(dict(cas=cas, substance_name=name, query=term,
                             pubmed_total_hits=res.get("count", ""), **rec,
                             verification_state="located_not_verified",
                             open_questions="actual human exposure; actual inhalation route; "
                                            "single-substance attribution; control group; "
                                            "statistical significance; clinical adversity vs "
                                            "biomarker shift; exposure level and duration"))
    df = pd.DataFrame(rows)
    df.to_csv("/home/user/v028/work/pubmed_primary_locators.csv", index=False)
    print(f"\nwrote pubmed_primary_locators.csv  rows={len(df)}")


if __name__ == "__main__":
    main()
