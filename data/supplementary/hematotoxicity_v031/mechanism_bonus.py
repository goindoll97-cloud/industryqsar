"""Exploratory positive-only reference retrieval with nonnegative HT alert bonus."""
import numpy as np

BONUSES = (0.10, 0.25)
NEW_MODELS = ('ht_alert_only', 'tanimoto_bonus_010', 'tanimoto_bonus_025')
METHODS = ('resubstitution', 'leave_one_compound_out', 'leave_one_group_out')
METRICS = ('recall_credit_top5', 'recall_credit_top10', 'ef_top5', 'ef_top10', 'rank_fraction', 'tie_n')


def extra_scores(base, alert):
    base = np.asarray(base, dtype=float)
    alert = np.asarray(alert, dtype=float)
    if base.shape != alert.shape or not np.isin(alert, [0, 1]).all():
        raise ValueError('Invalid alert vector')
    result = {NEW_MODELS[0]: alert}
    for name, bonus in zip(NEW_MODELS[1:], BONUSES):
        value = base + bonus * alert
        if not np.array_equal(value[alert == 0], base[alert == 0]) or np.any(value < base):
            raise ValueError('Bonus invariant violated')
        result[name] = value
    return result


def run_bonus(km, kh, h, ar, br, groups, nu, weight, out, scores, rank_stats, write, get_cas, models, feature_ids):
    n = len(ar)
    a = np.arange(n)
    b = np.arange(n, n + len(br))
    alert = np.any(h != 0, axis=1).astype(int)
    rows = []
    model_names = tuple(models) + NEW_MODELS
    for method in METHODS:
        folds = [a] if method == 'resubstitution' else ([np.array([i]) for i in a] if method == 'leave_one_compound_out' else groups)
        for fold, held in enumerate(folds, 1):
            train = a if method == 'resubstitution' else np.setdiff1d(a, held)
            if method != 'resubstitution' and np.intersect1d(train, held).size:
                raise ValueError('Holdout leakage')
            query = np.concatenate((held, b))
            pred = scores(km, kh, train, query, nu, weight)
            pred.update(extra_scores(pred['max_tanimoto'], alert[query]))
            for model, v in pred.items():
                for j, i in enumerate(held):
                    matched = np.concatenate(([v[j]], v[len(held):]))
                    baseline = np.concatenate(([pred['max_tanimoto'][j]], pred['max_tanimoto'][len(held):]))
                    stats = rank_stats(matched, 0)
                    rows.append({'method': method, 'model': model, 'fold': fold, 'CAS': get_cas(ar[i]),
                                 'chemical': ar[i].get('chemical', ''), 'train_n': len(train),
                                 'reference_in_train': int(i in train), 'HT_hits': int(h[i].sum()),
                                 'HT_alert': int(alert[i]), 'base_tanimoto': float(pred['max_tanimoto'][j]),
                                 'score': float(v[j]), 'rank_gain_vs_tanimoto': rank_stats(baseline, 0)['rank_mid'] - stats['rank_mid'], **stats})
    def aggregate(sub):
        return {'reference_n': len(sub), **{k: float(np.mean([r[k] for r in sub])) for k in METRICS},
                'mean_rank_gain_vs_tanimoto': float(np.mean([r['rank_gain_vs_tanimoto'] for r in sub]))}
    summary, strata = [], []
    for method in METHODS:
        for model in model_names:
            sub = [r for r in rows if r['method'] == method and r['model'] == model]
            if len(sub) != n or len({r['CAS'] for r in sub}) != n:
                raise ValueError('Expected one record per reference per model/method')
            summary.append({'method': method, 'model': model, **aggregate(sub)})
            for label, flag in [('all_zero', 0), ('has_alert', 1)]:
                block = [r for r in sub if r['HT_alert'] == flag]
                if block:
                    strata.append({'method': method, 'model': model, 'HT_stratum': label, **aggregate(block)})
    pred = scores(km, kh, a, b, nu, weight)
    pred.update(extra_scores(pred['max_tanimoto'], alert[b]))
    ranks = []
    for model, v in pred.items():
        for j in np.argsort(-np.round(v, 10), kind='stable'):
            i = b[j]
            stats = rank_stats(v, j)
            ranks.append({'model': model, 'CAS': get_cas(br[j]), 'chemical': br[j].get('chemical', ''),
                          'process': br[j].get('process', ''), 'HT_alert': int(alert[i]),
                          'HT_features': ';'.join(f for f, hit in zip(feature_ids, h[i]) if hit),
                          'base_tanimoto': float(pred['max_tanimoto'][j]), 'score': float(v[j]),
                          'rank_gain_vs_tanimoto': rank_stats(pred['max_tanimoto'], j)['rank_mid'] - stats['rank_mid'], **stats})
    coverage = []
    for name, idx in [('A', a), ('B', b)]:
        for f, col in zip(feature_ids, h.T):
            coverage.append({'dataset': name, 'feature': f, 'n': len(idx), 'hits': int(col[idx].sum()), 'fraction': float(col[idx].mean())})
        coverage.append({'dataset': name, 'feature': 'any_alert', 'n': len(idx), 'hits': int(alert[idx].sum()), 'fraction': float(alert[idx].mean())})
    for filename, data in [('bonus_summary.csv', summary), ('bonus_predictions.csv', rows), ('bonus_by_ht.csv', strata),
                           ('bonus_candidate_ranking.csv', ranks), ('bonus_feature_coverage.csv', coverage)]:
        write(out / filename, data)
    print('\nMechanism bonus: matched pool; fixed settings, not optimized')
    for r in summary:
        if r['method'] != 'resubstitution':
            print(f"{r['method']:24s} {r['model']:20s} R@10%={r['recall_credit_top10']:.4f} EF@10%={r['ef_top10']:.3f}")
    return {'version': 'v0.34', 'formula': 'max_train_morgan_tanimoto + bonus * any_HT_alert',
            'bonuses': list(BONUSES), 'primary_exploratory_bonus': BONUSES[0], 'sensitivity_bonus': BONUSES[1],
            'alert_only_control': True, 'no_double_counting': 'binary union, not alert count',
            'pool': 'one evaluated A + all B in every method', 'methods': list(METHODS), 'models': list(model_names),
            'rows': len(rows), 'limitations': ['Heuristic ranking, not a learned toxicity model or probability; scores may exceed 1',
            'No-alert raw score unchanged; relative ranks can fall', 'Literature-derived alerts may overlap reference evidence; no independent validation',
            'Resubstitution has self-match; not independent', 'No parameter selection on these pilot results for final testing']}
