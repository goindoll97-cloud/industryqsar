import openpyxl, json, csv, re, sys, collections
SRC = sys.argv[1]; OUT = sys.argv[2]
wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
ws = wb["Latest rationale"]
it = ws.iter_rows(min_row=1, values_only=True)
hdr = list(next(it))
H = {h: i for i, h in enumerate(hdr)}
stot = []
hazard_counter = collections.Counter()
total = 0
for r in it:
    total += 1
    hc = r[H["Hazard class"]]
    hazard_counter[hc] += 1
    if hc and str(hc).startswith("Specific target organ toxicity"):
        stot.append({
            "cas": r[H["CAS RN"]], "name": r[H["Substance Name"]],
            "substance_id": r[H["Substance ID"]],
            "hazard_class": hc, "classification": r[H["Classification"]],
            "rationale": r[H["Rationale for the classification"]],
            "year": r[H["Classification year"]],
            "guidance": r[H["GHS Classification Guidance"]],
        })
wb.close()
print("total data rows:", total)
print("STOT rows:", len(stot))
print("hazard classes containing STOT:", {k: v for k, v in hazard_counter.items() if k and "target organ" in str(k)})
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(stot[0].keys()))
    w.writeheader(); w.writerows(stot)
print("wrote", OUT)
