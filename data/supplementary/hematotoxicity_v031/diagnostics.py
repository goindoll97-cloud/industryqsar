"""Matched-pool diagnostic of training fit, compound-out and group-out retrieval."""
import numpy as np

METHODS = ('resubstitution', 'leave_one_compound_out', 'leave_one_group_out')
METRICS = ('recall_credit_top5', 'recall_credit_top10', 'ef_top5', 'ef_top10', 'rank_fraction', 'tie_n')


def run_diagnostics(km, kh, h, ar, groups, nu, weight, out, scores, rank_stats, write, get_cas, models):
    n = len(ar)
    a = np.arange(n)
    b = np.arange(n, len(km))
    rows = []
    for method in METHODS:
        folds = [a] if method == 'resubstitution' else ([np.array([i]) for i in a] if method == 'leave_one_compound_out' else groups)
        for fold, held in enumerate(folds, 1):
            train = a if method == 'resubstitution' else np.setdiff1d(a, held)
            if method != 'resubstitution' and np.intersect1d(train, held).size:
                raise ValueError('Holdout leakage')
            query = np.concatenate((held, b))
            pred = scores(km, kh, train, query, nu, weight)
            for model, v in pred.items():
                for j, i in enumerate(held):
                    # Exactly one reference + the same B pool in every method.
                    matched = np.concatenate(([v[j]], v[len(held):]))
                    score = float(v[j])
                    rows.append({'method': method, 'model': model, 'fold': fold,
                                 'CAS': get_cas(ar[i]), 'chemical': ar[i].get('chemical', ''),
                                 'train_n': len(train), 'reference_in_train': int(i in train),
                                 'max_train_tanimoto': float(km[i, train].max()),
                                 'HT_hits': int(h[i].sum()), 'score': score,
                                 'ocsvm_inlier': '' if model == 'max_tanimoto' else int(score >= 0),
                                 **rank_stats(matched, 0)})
    def aggregate(sub):
        return {'reference_n': len(sub), **{k: float(np.mean([r[k] for r in sub])) for k in METRICS},
                'ocsvm_inlier_fraction': '' if sub[0]['model'] == 'max_tanimoto' else float(np.mean([r['ocsvm_inlier'] for r in sub]))}
    summary = []
    by_ht = []
    for method in METHODS:
        for model in models:
            sub = [r for r in rows if r['method'] == method and r['model'] == model]
            if len(sub) != n or len({r['CAS'] for r in sub}) != n:
                raise ValueError('Each reference must appear once per method/model')
            summary.append({'method': method, 'model': model, **aggregate(sub)})
            for label, block in [('all_zero', [r for r in sub if r['HT_hits'] == 0]), ('has_alert', [r for r in sub if r['HT_hits'] > 0])]:
                if block:
                    by_ht.append({'method': method, 'model': model, 'HT_stratum': label, **aggregate(block)})
    write(out / 'diagnostic_summary.csv', summary)
    write(out / 'diagnostic_predictions.csv', rows)
    write(out / 'diagnostic_by_ht.csv', by_ht)
    print('\nDiagnostic: one A reference + fixed B pool (matched across methods)')
    for r in summary:
        print(f"{r['method']:24s} {r['model']:18s} R@10%={r['recall_credit_top10']:.4f} EF@10%={r['ef_top10']:.3f}")
    return {'version': 'v0.33', 'methods': list(METHODS), 'pool': 'one evaluated A + all B in every method',
            'inlier_rule': 'OCSVM decision >= 0; diagnostic only, not toxicity sensitivity',
            'resubstitution_limit': 'A is both fitted and scored; optimistic; max Tanimoto self-match trivial',
            'group_comparison': 'diagnostic group ranks use one A + B; original retrieval_metrics uses held group + B',
            'hyperparameters': 'unchanged; no tuning', 'rows': len(rows)}
