"""Scan cached ATSDR PDFs including pages outside hematology extraction. Requires PyMuPDF. No downloads or automated cancer labels."""
import argparse,csv,json,re,hashlib
from pathlib import Path
CANCER=re.compile(r'\b(?:leuk[ae]?mi\w*|leukaemi\w*|lymphom\w*|myeloma\w*|myelodysplas\w*|lympho[- ]?hemato\w*|lympho[- ]?haemato\w*|lymphatic (?:cancer|tumou?rs?)|hematopoietic (?:cancer|tumou?rs?|neoplasms?))\b',re.I)
def main():
 import fitz
 p=argparse.ArgumentParser();p.add_argument('candidates',type=Path);p.add_argument('--collection-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 with a.candidates.open(encoding='utf-8-sig',newline='') as f: docs=sorted({(r['profile'],r['pdf_url'],r['file'].replace('\\','/')) for r in csv.DictReader(f)})
 hits=[];audit=[];root=a.collection_root.resolve()
 for profile,url,rel in docs:
  path=(root/rel).resolve();entry=dict(profile=profile,pdf_url=url,file=rel,status='pending',pages=0,hit_count=0,sha256='',error='')
  try:
   if not path.is_relative_to(root):raise ValueError('file outside collection root')
   if not path.is_file():raise FileNotFoundError(rel)
   entry['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
   with fitz.open(path) as pdf:
    entry['pages']=len(pdf);empty=0
    for i,page in enumerate(pdf,1):
     lines=page.get_text(sort=True).splitlines();empty+=not bool(''.join(lines).strip())
     for j,line in enumerate(lines):
      if CANCER.search(line):
       hits.append(dict(profile=profile,pdf_url=url,file=rel,page=i,line=j+1,context=' '.join(lines[max(0,j-4):j+7]),matched_terms=';'.join(sorted(set(m.group(0).lower() for m in CANCER.finditer(line)))),review_status='pending',cancer_label=''));entry['hit_count']+=1
    entry['status']='partial_no_text' if empty else 'scanned';entry['error']=f'{empty} pages with no extractable text' if empty else ''
  except Exception as e:entry['status']='failed';entry['error']=str(e)
  audit.append(entry)
 for name,rows,cols in [('full_pdf_cancer_candidates.csv',hits,['profile','pdf_url','file','page','line','context','matched_terms','review_status','cancer_label']),('pdf_scan_audit.csv',audit,['profile','pdf_url','file','status','pages','hit_count','sha256','error'])]:
  with (a.out/name).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
 summary={'expected_documents':len(docs),'scanned':sum(r['status']=='scanned' for r in audit),'partial':sum(r['status']=='partial_no_text' for r in audit),'failed':sum(r['status']=='failed' for r in audit),'candidate_hits':len(hits),'final_labels':0};(a.out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
 if summary['scanned']==0 and summary['partial']==0:raise SystemExit(2)
if __name__=='__main__':main()
