import csv, json, re, zipfile, io, hashlib, collections, unicodedata, argparse
from pathlib import Path
from artifact_tool import Blob, SpreadsheetFile

def norm(x): return ' '.join(unicodedata.normalize('NFKC',str(x or '')).split())
def read(p):
    with p.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
def write(p, rows):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)) or ['status']);w.writeheader();w.writerows(rows)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--excel',type=Path,required=True);p.add_argument('--zip',type=Path,required=True);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    z=zipfile.ZipFile(a.zip)
    def zr(n): return list(csv.DictReader(io.StringIO(z.read('official_nite_results/'+n).decode('utf-8-sig'))))
    index=zr('source_index.csv'); details=zr('all_parsed_records.csv'); orig=zr('official_blood_evidence_rows.csv'); fetch=zr('fetch_audit.csv')
    wb=SpreadsheetFile.import_xlsx(Blob.load(str(a.excel))); sh=wb.worksheets.items[0]
    # Exact delivered snapshot: 3476 rows + header. Fail if shape changes.
    mat=sh.get_range('A1:AN3477').values; assert len(mat)==3477 and mat[0][3]=='ID'
    assert mat[0][33]=='Specific target organ toxicity - Single exposure' and mat[0][34]=='Specific target organ toxicity - Repeated exposure'
    excel={norm(r[3]):r for r in mat[1:]}; assert len(excel)==3476
    assert set(excel)=={r['source_id'] for r in index} and len(index)==3476
    assert len(details)==6952 and len({(r['source_id'],r['hazard_class']) for r in details})==6952
    assert len(fetch)==3476 and all(r['status']=='parsed' for r in fetch)
    # Reconcile Excel classification, source IDs and CAS. Explicit category 1/2 target only.
    blood=re.compile(r'\b(?:blood(?!\s+(?:pressure|vessels?|flow|supply|circulation|glucose|sugar))|bone marrow|ha?ematopoie\w*|ha?emopoie\w*|ha?emal system|ha?ematologic\w*|erythrocytes?|red blood cells?)\b',re.I)
    cat=re.compile(r'\bcategory\s*([123])(?!\d)',re.I)
    def bloodcat(s):
        ms=list(cat.finditer(s)); return '; '.join(s[m.start():ms[i+1].start() if i+1<len(ms) else len(s)].strip(' ,;') for i,m in enumerate(ms) if m[1] in ('1','2') and blood.search(s[m.start():ms[i+1].start() if i+1<len(ms) else len(s)]))
    mism=[]; hits=[]
    for r in details:
        x=excel[r['source_id']]; cl=norm(x[33 if 'Single exposure' in r['hazard_class'] else 34]); d=norm(r['classification']); bc=bloodcat(cl)
        if cl!=d or norm(x[0])!=norm(r['CAS_raw']) or bool(bc)!=(r['official_blood_candidate']=='1'):
            mism.append(dict(source_id=r['source_id'],CAS=r['CAS'],chemical=r['chemical'],hazard_class=r['hazard_class'],excel_classification=cl,html_classification=d,excel_CAS=norm(x[0]),html_CAS=r['CAS_raw'],excel_blood_category=bc,html_blood_category=r['blood_category']))
        if bc: hits.append(dict(r,excel_blood_category=bc,excel_classification=cl,excel_html_classification_agrees=int(cl==d),excel_html_CAS_agrees=int(norm(x[0])==norm(r['CAS_raw']))))
    write(a.out/'excel_html_discrepancies.csv',mism);write(a.out/'nite_blood_evidence_rows.csv',hits)
    # Verify cached source hashes; no network required.
    for r in index:
        key=hashlib.sha256(r['url'].encode()).hexdigest(); prefix='official_nite_results/raw_html/'+key
        m=json.loads(z.read(prefix+'.json')); assert m['url']==r['url'] and hashlib.sha256(z.read(prefix+'.html')).hexdigest()==m['sha256']
    A=read(a.base/'dataset_A_inhalation_hematotoxicity_references.csv'); B=read(a.base/'dataset_B_industrial_8110.csv'); P=read(a.base/'screening_candidate_index_v23.csv'); aa={r['CAS']:r for r in A};bb={r['CAS']:r for r in B};assert len(aa)==39 and len(bb)==8110 and len(P)==2642
    g=collections.defaultdict(list)
    for r in hits:
        if r['CAS']:g[r['CAS']].append(r)
    def anyflag(rr,k):return int(any(r[k]=='1' for r in rr))
    def unique(rr,k):return ' | '.join(sorted({r[k] for r in rr if r[k]}))
    out=[]
    for c,rr in sorted(g.items()):
        b=bb.get(c,{});h=aa.get(c,{})
        cls=' '.join(r['excel_blood_category'] for r in rr)
        same=int(any(r['human_text_cue']=='1' and r['inhalation_text_cue']=='1' for r in rr))
        marrow=int(bool(re.search(r'bone marrow|ha?ematopoie|ha?emopoie',cls,re.I)))
        out.append(dict(CAS=c,nite_chemical=unique(rr,'chemical'),nite_source_ids=unique(rr,'source_id'),nite_source_urls=unique(rr,'url'),nite_classification_years=unique(rr,'classification_year'),nite_update=unique(rr,'source_update'),nite_blood_categories=unique(rr,'excel_blood_category'),nite_SE=int(any('Single exposure' in r['hazard_class'] for r in rr)),nite_RE=int(any('Repeated exposure' in r['hazard_class'] for r in rr)),marrow_or_hematopoietic_target=marrow,human_text_cue=anyflag(rr,'human_text_cue'),animal_text_cue=anyflag(rr,'animal_text_cue'),inhalation_text_cue=anyflag(rr,'inhalation_text_cue'),same_row_human_inhalation_cues=same,source_rows=len(rr),in_A=int(c in aa),in_B=int(c in bb),human_evidence_level=h.get('human_evidence_level',''),existing_A_use=h.get('human_reference_use',''),existing_B_status=b.get('v23_analysis_status',''),existing_B_scope=b.get('target_scope',''),existing_SMILES=b.get('SMILES','') or h.get('SMILES',''),existing_InChIKey=b.get('InChIKey','') or h.get('InChIKey',''),official_classification_status='NITE_STOT_blood_target',human_inhalation_status='not_adjudicated',review_priority='1_marrow_and_same_row_cues' if marrow and same else '2_same_row_cues' if same else '3_marrow_target' if marrow else '4_other',decision='review_only_no_label'))
    out.sort(key=lambda r:(r['review_priority'], -int(r['existing_B_status']=='EPA_checked_novel_candidate'),r['CAS']));d={r['CAS']:r for r in out}
    for name, rs in [('nite_blood_candidates_merged.csv',out),('new_NITE_candidates_for_A_review.csv',[r for r in out if not r['in_A']]),('new_NITE_candidates_structure_ready.csv',[r for r in out if not r['in_A'] and r['existing_B_status']=='EPA_checked_novel_candidate']),('unresolved_NITE_CAS.csv',[r for r in hits if not r['CAS']]),('priority_human_inhalation_cues.csv',[r for r in out if r['same_row_human_inhalation_cues'] and not r['in_A']])]:write(a.out/name,rs)
    for name,rs in [('dataset_A_v23_with_NITE_flags.csv',A),('dataset_B_v23_with_NITE_flags.csv',B),('screening_candidate_index_v23_with_NITE_flags.csv',P)]:
        for r in rs:
            m=d.get(r['CAS'],{});r.update(nite_blood_target=int(bool(m)),nite_blood_categories=m.get('nite_blood_categories',''),nite_source_urls=m.get('nite_source_urls',''),nite_review_priority=m.get('review_priority',''),nite_human_inhalation_status='not_adjudicated' if m else 'not_matched_not_negative')
        write(a.out/name,rs)
    new=[r for r in out if not r['in_A']]; ready=[r for r in new if r['existing_B_status']=='EPA_checked_novel_candidate']
    counts=dict(excel_rows=len(excel),detail_pages=len(index),detail_STOT_rows=len(details),excel_html_discrepancies=len(mism),excel_blood_rows=len(hits),html_original_blood_rows=len(orig),blood_unique_source_ids=len({r['source_id'] for r in hits}),valid_single_CAS=len(out),unresolved_rows=sum(not r['CAS'] for r in hits),A_overlap=sum(r['in_A'] for r in out),B_overlap=sum(r['in_B'] for r in out),new_A_review=len(new),new_not_in_B=sum(not r['in_B'] for r in new),new_in_B=sum(r['in_B'] for r in new),new_B_status=dict(collections.Counter(r['existing_B_status'] or 'not_in_B' for r in new)),new_structure_ready=len(ready),SE_only=sum(r['nite_SE'] and not r['nite_RE'] for r in out),RE_only=sum(r['nite_RE'] and not r['nite_SE'] for r in out),SE_and_RE=sum(r['nite_SE'] and r['nite_RE'] for r in out),marrow_or_hematopoietic=sum(r['marrow_or_hematopoietic_target'] for r in out),new_marrow=sum(r['marrow_or_hematopoietic_target'] for r in new),new_ready_marrow=sum(r['marrow_or_hematopoietic_target'] for r in ready),same_row_human_inhalation=sum(r['same_row_human_inhalation_cues'] for r in out),new_same_row_cues=sum(r['same_row_human_inhalation_cues'] for r in new),ready_same_row_cues=sum(r['same_row_human_inhalation_cues'] for r in ready),ready_scope=dict(collections.Counter(r['existing_B_scope'] for r in ready)),A_overlap_levels=dict(collections.Counter(r['human_evidence_level'] for r in out if r['in_A'])),source_hashes={x.name:sha(x) for x in [a.excel,a.zip]},human_primary_count=sum(r['human_reference_use']=='provisional_primary_pool' for r in A),A_count=len(A),B_count=len(B),B_screening_count=len(P),new_labels=0,model_run=False)
    priority=[r for r in ready if r['marrow_or_hematopoietic_target'] or r['same_row_human_inhalation_cues']]
    write(a.out/'priority_structure_ready_review.csv',priority)
    for r in out:
        d=r['CAS'].replace('-',''); assert sum(i*int(x) for i,x in enumerate(d[-2::-1],1))%10==int(d[-1])
    years=[int(y) for r in hits for y in re.findall(r'20\d\d',r['classification_year'])]
    counts.update(priority_structure_ready_union=len(priority),category_1_any=sum(bool(re.search(r'Category 1\b',r['nite_blood_categories'])) for r in out),category_2_only=sum(not bool(re.search(r'Category 1\b',r['nite_blood_categories'])) for r in out),blood_classification_year_range=[min(years),max(years)],scope='official hazard candidate staging; no new human label')
    (a.out/'summary.json').write_text(json.dumps(counts,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(counts,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
