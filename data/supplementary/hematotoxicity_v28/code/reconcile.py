import openpyxl, pandas as pd, sys
clf = sys.argv[1]; stot_csv = sys.argv[2]
wb = openpyxl.load_workbook(clf, read_only=True, data_only=True)
ws = wb["Latest GHS clasification"]
it = ws.iter_rows(min_row=1, values_only=True); hdr = list(next(it))
H = {h: i for i, h in enumerate(hdr)}
rows = []
for r in it:
    rows.append({"cas": r[H["CAS"]], "name": r[H["Substance Name"]], "id": r[H["ID"]],
                 "SE": r[H["Specific target organ toxicity - Single exposure"]],
                 "RE": r[H["Specific target organ toxicity - Repeated exposure"]],
                 "url": r[H["Detail (NITE HP URL)"]]})
wb.close()
cl = pd.DataFrame(rows)
st = pd.read_csv(stot_csv, dtype=str)
print("classification list substances:", len(cl), "unique CAS:", cl.cas.nunique(), "unique ID:", cl.id.nunique())
print("rationale STOT substances:", st.substance_id.nunique())
only_cl = set(cl.id) - set(st.substance_id)
only_st = set(st.substance_id) - set(cl.id)
print("in classification list but NO rationale STOT rows:", len(only_cl))
print("in rationale but not classification list:", len(only_st))
sub = cl[cl.id.isin(only_cl)][["cas","name","SE","RE"]]
print(sub.to_string(index=False, max_colwidth=58))
cl.to_csv("/home/user/v028/work/nite_classification_list_3476.csv", index=False)
