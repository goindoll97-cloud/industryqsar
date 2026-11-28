"""Exploratory positive-reference retrieval, not a toxicity classifier."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median
from rdkit import Chem, DataStructs, rdBase
from rdkit.Chem import Descriptors, rdFingerprintGenerator

A_FILE = 'dataset_A_inhalation_hematotoxicity_references.csv'
B_FILE = 'screening_candidate_index_v23.csv'
HASHES = {A_FILE: '201aa34c73125fce62b23207a9eda9c819b13b5b5641b7225b343b36920f8161',
          B_FILE: '9ec1a0c730819228f1214ded2947d8d7614b13cb8572fdc8b0a0def0b23a24bf'}
GEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048, includeChirality=False)
ENDPOINTS = ['hemoglobin_function', 'red_cell', 'blood_cell_counts_or_marrow']
CONDITIONS = ['human_only', 'human_plus_animal']


def read(root, name):
    p = root / name
    if hashlib.sha256(p.read_bytes()).hexdigest() != HASHES[name]:
        raise ValueError(f'Wrong v0.23 input bytes: {p}')
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def prepare(r):
    m = Chem.MolFromSmiles(r['SMILES'])
    if m is None or Chem.MolToInchiKey(m) != r['InChIKey'] or len(Chem.GetMolFrags(m)) != 1:
        raise ValueError(f'Structure mismatch: {r["CAS"]}')
    return dict(r, fp=GEN.GetFingerprint(m), conn=r['InChIKey'][:14],
                MW=Descriptors.MolWt(m), logP=Descriptors.MolLogP(m), TPSA=Descriptors.TPSA(m))


def sim(a, b):
    return DataStructs.TanimotoSimilarity(a['fp'], b['fp'])


def groups(refs, cutoff):
    # Single-linkage connected components on the UNION of both reference pools.
    left = set(range(len(refs)))
    result = []
    while left:
        seed = min(left)
        left.remove(seed)
        group = [seed]
        for i in group:
            linked = sorted(j for j in left if refs[i]['conn'] == refs[j]['conn'] or sim(refs[i], refs[j]) >= cutoff)
            left.difference_update(linked)
            group.extend(linked)
        result.append([refs[i] for i in group])
    return result


def pool(refs, condition):
    return [r for r in refs if r['human'] or (condition == 'human_plus_animal' and r['animal'])]


def score(target, refs):
    vals = [(sim(target, r), r['reference_id'], r) for r in refs]
    if not vals:
        raise ValueError('Empty reference pool after holdout')
    vals.sort(key=lambda v: (-v[0], v[1]))
    return vals[0], vals


def write(path, rows):
    if not rows:
        raise ValueError(f'No rows: {path}')
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--core-only', action='store_true', help='Sensitivity: use only 9 core human references')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    a, b = read(args.data, A_FILE), read(args.data, B_FILE)
    if len(a) != 39 or len(b) != 2642 or len({r['CAS'] for r in a}) != 39 or len({r['CAS'] for r in b}) != 2642:
        raise ValueError('Unexpected v0.23 counts')
    refs = []
    for r in a:
        h = r['human_reference_use'] == 'provisional_primary_pool' and (not args.core_only or r['human_evidence_level'] == '1_core')
        v = r['animal_transfer_role'] == 'provisional_animal_reference' and r['animal_identity_status'] == 'EPA_RDKIT_match'
        if h or v:
            refs.append(dict(prepare(r), human=h, animal=v))
    targets = [prepare(r) for r in b if r['v23_analysis_status'] == 'EPA_checked_novel_candidate']
    if len(targets) != 2642 or len({r['InChIKey'] for r in targets}) != len(targets):
        raise ValueError('Candidate count/duplicates')
    if {r['CAS'] for r in a} & {r['CAS'] for r in targets} or {r['InChIKey'][:14] for r in a if r['InChIKey']} & {r['conn'] for r in targets}:
        raise ValueError('A/B overlap')
    # Collapse connectivity variants for retrieval background only; retain all candidate rows in ranking.
    # Use maximum score among variants, so a stereochemical duplicate cannot inflate the denominator.
    cutoff = 0.50
    rows, memberships = [], []
    for split, folds in [('compound_out', [[r] for r in refs]), ('group_out', groups(refs, cutoff))]:
        for fold, held in enumerate(folds, 1):
            ids = {r['reference_id'] for r in held}
            conn = {r['conn'] for r in held}
            remaining = [r for r in refs if r['reference_id'] not in ids and r['conn'] not in conn]
            for r in held:
                memberships.append(dict(split=split, fold=fold, reference_id=r['reference_id'], CAS=r['CAS'], human=r['human'], animal=r['animal']))
            tests = [r for r in held if r['human']]
            if not tests:
                continue
            for condition in CONDITIONS:
                train = pool(remaining, condition)
                background = {}
                for t in targets:
                    s = score(t, train)[0][0]
                    background[t['conn']] = max(s, background.get(t['conn'], -1))
                # All held human references are included in this fold's retrieval pool.
                test_scores = {r['reference_id']: score(r, train)[0] for r in tests}
                n = len(background) + len(tests)
                for r in tests:
                    s, near, _ = test_scores[r['reference_id']]
                    # Worst rank for ties (all other tied entries rank ahead).
                    rank = sum(x >= s for x in background.values()) + sum(x[0] >= s for x in test_scores.values())
                    rows.append(dict(split=split, fold=fold, condition=condition, reference_id=r['reference_id'], CAS=r['CAS'], chemical=r['chemical'], endpoint=r['endpoint_class'], train_n=len(train), similarity=s, nearest_reference=near, rank=rank, pool_n=n, rank_fraction=rank/n, top1pct=int(rank <= math.ceil(n*.01)), top5pct=int(rank <= math.ceil(n*.05)), top10pct=int(rank <= math.ceil(n*.10))))
    metrics = []
    for split in ['compound_out', 'group_out']:
        for condition in CONDITIONS:
            r = [x for x in rows if x['split']==split and x['condition']==condition]
            metrics.append(dict(split=split, condition=condition, human_tests=len(r), mean_similarity=mean(x['similarity'] for x in r), median_rank_fraction=median(x['rank_fraction'] for x in r), recall_top1pct=mean(x['top1pct'] for x in r), recall_top5pct=mean(x['top5pct'] for x in r), recall_top10pct=mean(x['top10pct'] for x in r)))
    ranking = []
    for condition in CONDITIONS:
        train = pool(refs, condition)
        for t in targets:
            (s, near, nearest), vals = score(t, train)
            row = dict(condition=condition, target_id=t['target_id'], CAS=t['CAS'], chemical=t['chemical'], SMILES=t['SMILES'], InChIKey=t['InChIKey'], scope=t['target_scope'], max_similarity=s, nearest_reference=near, nearest_chemical=nearest['chemical'], nearest_human=nearest['human'], nearest_animal=nearest['animal'], MW=t['MW'], logP=t['logP'], TPSA=t['TPSA'], similarity_ge_03=int(s>=.3), similarity_ge_05=int(s>=.5))
            for endpoint in ENDPOINTS:
                eligible = [v[0] for v in vals if (v[2]['human'] and endpoint in v[2]['endpoint_class'].split(';')) or (condition=='human_plus_animal' and v[2]['animal'] and endpoint in v[2]['animal_endpoint_class'].split(';'))]
                row[endpoint+'_max_similarity'] = max(eligible) if eligible else ''
            ranking.append(row)
    ranking.sort(key=lambda r: (r['condition'], -r['max_similarity'], r['target_id']))
    for condition in CONDITIONS:
        rr = [r for r in ranking if r['condition']==condition]
        for i, r in enumerate(rr, 1):
            r['rank'] = i
    coverage = []
    for condition in CONDITIONS:
        for scope in ['ALL'] + sorted({t['target_scope'] for t in targets}):
            rr = [r for r in ranking if r['condition']==condition and (scope=='ALL' or r['scope']==scope)]
            coverage.append(dict(condition=condition, scope=scope, n=len(rr), median_similarity=median(r['max_similarity'] for r in rr), fraction_ge_03=mean(r['similarity_ge_03'] for r in rr), fraction_ge_05=mean(r['similarity_ge_05'] for r in rr)))
    for name, data in [('holdout_predictions.csv',rows),('fold_membership.csv',memberships),('retrieval_metrics.csv',metrics),('candidate_ranking.csv',ranking),('similarity_coverage.csv',coverage)]:
        write(args.out/name, data)
    meta = dict(version='v0.23-pilot1', rdkit=rdBase.rdkitVersion, input_sha256=HASHES, human=sum(r['human'] for r in refs), animal=sum(r['animal'] for r in refs), union=len(refs), candidates=len(targets), background_connectivity_groups=len({t['conn'] for t in targets}), group_cutoff=cutoff, core_only=args.core_only, note='Exploratory internal retrieval, unlabeled background, not independent validation or toxicity probabilities. Similarity thresholds are descriptive, not calibrated AD. Endpoint scores and descriptors are descriptive; overall ranking is unweighted max Tanimoto.')
    (args.out/'run_metadata.json').write_text(json.dumps(meta, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(meta, indent=2))
    for r in metrics:
        print(r)


if __name__ == '__main__':
    main()
