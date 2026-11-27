"""Broad candidate screening; no automatic toxicity labels. Python >=3.9."""
import argparse, csv, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path
PAT={
 'human':r'\b(?:humans?|workers?|patients?|volunteers?|subjects?|employees?|men|women|occupational)\b',
 'animal':r'\b(?:rats?|mice|mouse|rabbits?|dogs?|hamsters?|animals?|monkeys?|guinea pigs?|rodents?)\b',
 'inhalation':r'\binhal\w*|\bairborne\b',
 'oral':r'\b(?:oral(?:ly)?|gavage|ingestion|drinking water|dietary|feed)\b',
 'dermal':r'\b(?:dermal(?:ly)?|cutaneous|skin exposure)\b',
 'injection':r'\b(?:intravenous|intraperitoneal|subcutaneous|injection)\b',
 'rbc':r'\b(?:erythrocyt\w*|red blood cells?|RBCs?|hemoglobin|haemoglobin|hematocrit|haematocrit|anemi\w*|anaemi\w*|reticulocyt\w*|hemoly\w*|haemoly\w*)\b',
 'wbc':r'\b(?:white blood cells?|WBCs?|leukocyt\w*|leucocyt\w*|leukopen\w*|lymphocyt\w*|lymphopen\w*|neutrophil\w*|neutropen\w*|granulocyt\w*|agranulocyt\w*)\b',
 'platelet':r'\b(?:platelets?|thrombocyt\w*)\b',
 'marrow':r'\b(?:bone marrow|pancytopen\w*|hem[ao]topoie\w*|haematopoie\w*|hemopoie\w*|myelosuppress\w*|aplastic an[ae]emi\w*)\b',
 'methemoglobin':r'\b(?:methemoglobin\w*|methaemoglobin\w*)\b',
 'cancer':r'\b(?:leuk[ae]?mi\w*|leukaemi\w*|lymphom\w*|myeloma\w*|myelodysplas\w*|lympho[- ]?hemato\w*|lympho[- ]?haemato\w*|AML|CLL|CML|NHL)\b',
 'genotoxicity':r'\b(?:genotox\w*|chromosom\w* aberration\w*|micronucle\w*|DNA damage|mutagen\w*)\b',
 'change':r'\b(?:increas\w*|decreas\w*|elevat\w*|reduc\w*|induc\w*|atrophy|hypoplasia|hemoly\w*|haemoly\w*|suppression)\b',
 'no_effect':r'\b(?:no significant|no statistically significant|no hematolog\w*|no treatment[- ]related|no effects?|no changes?|not significantly|within normal limits)\b',
 'gap':r'\b(?:no data|not examined|not evaluated|no (?:human |animal |epidemiological )?studies (?:were |have been )?(?:located|identified|available|found))\b',
 'duration':r'\b(?:\d+(?:[.,]\d+)?\s*(?:hours?|days?|weeks?|months?|years?|h/day|d/week)|acute|chronic|subchronic|subacute|intermediate)\b',
 'dose':r'\b\d+(?:[.,]\d+)?\s*(?:ppm|ppb|mg\s*/\s*(?:kg|m[³3])|µg\s*/\s*m[³3])\b',
}
RX={k:re.compile(v,re.I) for k,v in PAT.items()}
CANCER_ACRONYM=re.compile(r'\bALL\b')
END=['rbc','wbc','platelet','marrow','methemoglobin']
ROUTES=['inhalation','oral','dermal','injection']
REQUIRED={'profile','profile_url','pdf_url','file','page','line','heading_match','context'}
def flags(s):
 f={k:int(bool(v.search(s))) for k,v in RX.items()};f['cancer']=int(f['cancer'] or bool(CANCER_ACRONYM.search(s)));return f
def save(path,rows,fields):
 with path.open('w',encoding='utf-8-sig',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--prior',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 with a.input.open(encoding='utf-8-sig',newline='') as h:
  reader=csv.DictReader(h);assert REQUIRED<=set(reader.fieldnames or []), 'missing source fields';rows=list(reader)
 old=set()
 if a.prior:
  with a.prior.open(encoding='utf-8-sig',newline='') as h:old={int(r['record_id']) for r in csv.DictReader(h)}
 seen=set();allrows=[];unique=[];stats=defaultdict(Counter)
 for i,r in enumerate(rows,1):
  s=' '.join(r['context'].split());f=flags(s);key=(r['profile'],r['pdf_url'],s);dup=key in seen;seen.add(key)
  e=';'.join(k for k in END if f[k]);routes=';'.join(k for k in ROUTES if f[k]);species='mixed' if f['human'] and f['animal'] else 'human' if f['human'] else 'animal' if f['animal'] else 'unknown'
  tier='1_cancer_mention' if f['cancer'] else '2_specific_endpoint_change_or_noeffect' if e and (f['change'] or f['no_effect']) else '3_specific_endpoint' if e else '4_general_context'
  z={**r,'record_id':i,'previous_priority':int(i in old),'duplicate_context':int(dup),'review_tier':tier,'species_cue':species,'route_cues':routes,'endpoint_cues':e,**{k+'_cue':v for k,v in f.items()},'review_status':'pending','training_label':''};allrows.append(z)
  if not dup:
   unique.append(z);stats[r['profile']][tier]+=1
 fields=list(allrows[0]);save(a.out/'all_candidates.csv',allrows,fields);save(a.out/'unique_review_queue.csv',sorted(unique,key=lambda r:(r['review_tier'],not r['previous_priority'],r['profile'],int(r['page']),int(r['line']))),fields)
 cancer=[r for r in unique if r['cancer_cue']];save(a.out/'cancer_mentions_existing_context.csv',cancer,fields)
 groups=defaultdict(list)
 for r in unique:groups[(r['profile'],r['pdf_url'],r['page'])].append(r)
 blocks=[]
 for (profile,url,page),g in sorted(groups.items()):
  parts=[]
  for r in sorted(g,key=lambda r:int(r['line'])):
   if not parts or int(r['line'])-int(parts[-1][-1]['line'])>7:parts.append([])
   parts[-1].append(r)
  for part in parts:
   blocks.append(dict(block_id=len(blocks)+1,profile=profile,pdf_url=url,page=page,start_line=part[0]['line'],end_line=part[-1]['line'],record_ids=';'.join(str(r['record_id']) for r in part),records=len(part),cancer_mention=int(any(r['cancer_cue'] for r in part)),previous_priority=int(any(r['previous_priority'] for r in part)),review_tier=min(r['review_tier'] for r in part),review_status='pending'))
 save(a.out/'review_blocks.csv',blocks,list(blocks[0]));tiers=sorted({r['review_tier'] for r in unique});save(a.out/'profile_summary.csv',[{'profile':k,'total_unique':sum(v.values()),**v} for k,v in sorted(stats.items())],['profile','total_unique',*tiers])
 summary={'input_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),'input_records':len(rows),'profiles':len(stats),'unique_contexts':len(unique),'exact_duplicates':len(rows)-len(unique),'previous_priority_retained':sum(r['previous_priority'] for r in allrows),'previous_priority_unique':sum(r['previous_priority'] for r in unique),'new_unique_relative_to_prior':sum(not r['previous_priority'] for r in unique),'tiers':dict(Counter(r['review_tier'] for r in unique)),'species_cues':dict(Counter(r['species_cue'] for r in unique)),'route_cue_counts':{k:sum(r[k+'_cue'] for r in unique) for k in ROUTES},'duration_cues':sum(r['duration_cue'] for r in unique),'dose_cues':sum(r['dose_cue'] for r in unique),'cancer_mentions':len(cancer),'cancer_profiles':len({r['profile'] for r in cancer}),'review_blocks':len(blocks),'cancer_blocks':sum(r['cancer_mention'] for r in blocks),'final_training_labels':0,'note':'Keyword flags only; cancer mentions limited to pre-extracted hematology contexts. No study-level adjudication.'};(a.out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
