import hashlib, json, os, sys
base, man = sys.argv[1], sys.argv[2]
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda: f.read(1<<20), b""): h.update(c)
    return h.hexdigest()
rec = json.load(open(man))["local_file_sha256"]
ok=bad=miss=0; extra=[]
for rel, want in sorted(rec.items()):
    p=os.path.join(base, rel)
    if not os.path.exists(p): print(f"  MISSING  {rel}"); miss+=1; continue
    got=sha(p)
    if got==want: ok+=1
    else: print(f"  MISMATCH {rel}\n           recorded {want}\n           actual   {got}"); bad+=1
for dp,_,fns in os.walk(base):
    for fn in fns:
        rel=os.path.relpath(os.path.join(dp,fn), base)
        if rel not in rec: extra.append(rel)
print(f"\nrecorded files: {len(rec)}  match: {ok}  mismatch: {bad}  missing: {miss}")
if extra: print("files present but not in manifest:", extra)
sys.exit(1 if (bad or miss) else 0)
