"""Parse NITE STOT classification cells into (category, target-organ) pairs.

NITE cells look like:  "Category 1 (liver, blood system)\nCategory 3 (narcotic effects)"
Organ lists can wrap across lines, carry trailing commas, and contain nested
parentheses ("hair (alopecia)", "reproductive organs (female)"), so a balanced
parenthesis scan is used rather than a line-oriented split.
"""
import re

CAT_MARK = re.compile(r'Category\s+([123])')

def _split_organs(s):
    """Split an organ list on commas that are not inside parentheses."""
    out, depth, buf = [], 0, ""
    for ch in s:
        if ch == '(': depth += 1; buf += ch
        elif ch == ')': depth -= 1; buf += ch
        elif ch == ',' and depth == 0:
            if buf.strip(): out.append(buf.strip())
            buf = ""
        else: buf += ch
    if buf.strip(): out.append(buf.strip())
    return out

def parse_cell(cell):
    """Return [{category, organs:[...]}] for one classification cell."""
    if not cell: return []
    txt = re.sub(r'\s+', ' ', str(cell)).strip()
    out = []
    for m in CAT_MARK.finditer(txt):
        cat = m.group(1)
        i = m.end()
        # skip spaces; an organ list, if present, starts at the next '('
        j = i
        while j < len(txt) and txt[j] == ' ': j += 1
        organs = []
        if j < len(txt) and txt[j] == '(':
            depth, k = 0, j
            while k < len(txt):
                if txt[k] == '(': depth += 1
                elif txt[k] == ')':
                    depth -= 1
                    if depth == 0: break
                k += 1
            if depth == 0:                      # balanced close found
                organs = _split_organs(txt[j+1:k])
        out.append({"category": cat, "organs": organs})
    return out

if __name__ == "__main__":
    import pandas as pd, collections
    st = pd.read_csv("/home/user/v028/work/nite_stot_all_rows.csv", dtype=str).fillna("")
    terms = collections.Counter(); blocks_n = 0; no_organ = 0
    for _, r in st.iterrows():
        for b in parse_cell(r.classification):
            blocks_n += 1
            if not b["organs"]: no_organ += 1
            for o in b["organs"]: terms[o.lower()] += 1
    print("category blocks parsed:", blocks_n, "| with no organ list:", no_organ)
    print("distinct organ terms:", len(terms))
    blood = {t: n for t, n in terms.items() if re.search(r'blood|h(?:a)?emato|marrow|spleen|lymph|reticuloend', t)}
    print("\nblood / haematopoietic-related terms:")
    for t, n in sorted(blood.items(), key=lambda x: -x[1]): print(f"  {n:5d}  {t}")
