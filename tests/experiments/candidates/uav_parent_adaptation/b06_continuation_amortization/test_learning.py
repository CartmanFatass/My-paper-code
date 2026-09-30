"""Synthetic correctness only: no paid fitting, native or teacher queries."""
from copy import deepcopy
import gzip
import hashlib
import io
import json

import numpy as np
import pytest

from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization import learning as l


def report():
    p = np.array([[100, 100, 100], [300, 100, 100]] + [[900, 900, 100]] * 6, dtype=float)
    u = np.array([[100, 100]] * 25 + [[200, 100]] * 25, dtype=float)
    r = np.ones(133, dtype=np.float32)
    r[:24] = np.column_stack((p[:, :2] / 1000, (p[:, 2] - 50) / 100)).reshape(-1)
    r[32:132] = (u / 1000).reshape(-1)
    r[-1] = 40 / 500
    return r


def candidate(member=1, site=0, **changes):
    destination = np.array([[100, 100, 50], [300, 100, 50]] + [[900, 900, 100]] * 6, dtype=float)
    c = dict(member=member, site=site, predicted_destination=destination.tolist(), predicted_mask=3,
             duration=20, path=150, predicted_total_J=930, predicted_total_served=9300,
             tail_score=dict(quality=.8, J=2, served=20, energy_penalty=.1))
    c.update(changes)
    return c


STAY = dict(J=2, served=20, quality=.5)


def artifact(beta=None):
    return dict(schema=l.ARTIFACT_SCHEMA, beta=[0.] * 13 if beta is None else beta,
                means=[0.] * 12, scales=[1.] * 12, penalty=.1, feature_names=list(l.FEATURE_NAMES))


def plan(c):
    return dict(initiated=True, selected=c, stay_score=STAY.copy(), member=c['member'], site=c['site'],
                commands=[[0, 0, -1]], duration=c['duration'], tag=f"{c['member']}:{c['site']}")


def bank(cs, *, initiated=True):
    champions = [plan(c) for c in cs]
    original = deepcopy(champions[-1]) if champions else dict(stay_score=STAY.copy(), member=None, site=None)
    original['initiated'] = initiated
    original['tag'] = 'exact-R-physical-plan'
    return dict(champions=champions, original_R=original)


def test_hand_features_independent_geometry():
    r, c = report(), candidate()
    x = l.feature_matrix(r, 1, [c], STAY)
    # Independently decode rounded inputs; explicitly enumerate all user/member distances.
    positions = r[:24].reshape(8, 3).astype(float)
    positions[:, :2] *= 1000
    positions[:, 2] = positions[:, 2] * 100 + 50
    users = np.column_stack((r[32:132].reshape(50, 2).astype(float) * 1000, np.zeros(50)))
    dst = np.array(c['predicted_destination'])
    delta, strict = [], 0
    for user in users:
        before = sum((user[a] - positions[0, a]) ** 2 for a in range(3)) ** .5
        distances = [sum((user[a] - dst[i, a]) ** 2 for a in range(3)) ** .5 for i in (0, 1)]
        delta.append(min(distances) - before)
        strict += distances[1] < distances[0]
    mean = sum(delta) / 50
    sd = (sum((d - mean) ** 2 for d in delta) / 50) ** .5
    expected = [.02, .004, .3, .5, .15, 2/3, .2, strict/50, mean/1000, sd/1000, 1/8, 2/8]
    assert x.dtype == np.float64 and x.shape == (1, 12)
    np.testing.assert_allclose(x[0], expected, rtol=0, atol=1e-15)


def test_strict_nearest_ties_muted_sole_and_empty_sets():
    # Identical arrival coordinates produce exact ties: feature8 is zero.
    c = candidate()
    c['predicted_destination'][1] = c['predicted_destination'][0].copy()
    assert l.feature_matrix(report(), 1, [c], STAY)[0, 7] == 0
    c['predicted_mask'] = 1
    assert l.feature_matrix(report(), 1, [c], STAY)[0, 7] == 0
    c['predicted_mask'] = 2
    x = l.feature_matrix(report(), 0, [c], STAY)[0]
    assert x[6] == 2 and x[7] == 1 and x[10] == 0 and x[11] == 1/8
    c['predicted_mask'] = 0
    x = l.feature_matrix(report(), 0, [c], STAY)[0]
    assert x[6] == 2 and x[7] == 0 and x[8] == x[9] == 0
    assert l.feature_matrix(report(), 1, [], STAY).shape == (0, 12)


def test_distance_pairs_are_reused_for_nearest_features(monkeypatch):
    original = np.linalg.norm
    pairs = []
    def norm(a, *args, **kwargs):
        pairs.append(np.asarray(a).size // 3)
        return original(a, *args, **kwargs)
    monkeypatch.setattr(np.linalg, 'norm', norm)
    l.feature_matrix(report(), 1, [candidate(), candidate(site=1)], STAY)
    assert sum(pairs) == 50 + 2 * (50 * 2 + 1)


@pytest.mark.parametrize('change', [dict(member=8), dict(member=True), dict(site=100),
    dict(duration=11), dict(path=-1), dict(path=np.nan), dict(predicted_mask=256),
    dict(predicted_destination=[[0,0,50]]), dict(predicted_total_J=np.inf)])
def test_feature_invalid_candidate(change):
    with pytest.raises(ValueError):
        l.feature_matrix(report(), 1, [candidate(**change)], STAY)


@pytest.mark.parametrize('mutation', ['shape', 'validity', 'nonfinite', 'bounds', 'dtype'])
def test_feature_invalid_report(mutation):
    r = report()
    if mutation == 'shape': r = r[:-1]
    if mutation == 'validity': r[24] = 0
    if mutation == 'nonfinite': r[80] = np.nan
    if mutation == 'bounds': r[0] = 1.1
    if mutation == 'dtype': r = r.astype(np.float64)
    with pytest.raises(ValueError): l.feature_matrix(r, 1, [candidate()], STAY)


def synthetic_rows():
    rng = np.random.RandomState(172)
    rows = []
    for world, count in zip(l.WORLD_IDS, l.CHAMPION_COUNTS):
        for i in range(count):
            rows.append(dict(world_id=world, branch_id=f'synthetic-{i}', features=rng.normal(size=12).tolist(),
                target=float(rng.normal() + count), source=dict(synthetic=True, target_id=f'{world}:{i}')))
    return dict(rows=rows, manifest=dict(summary=dict(sha256=l.EXPECTED_SUMMARY_SHA256),
        world_ids=list(l.WORLD_IDS), champion_counts=list(l.CHAMPION_COUNTS), feature_names=list(l.FEATURE_NAMES),
        row_count=58, label_kind='paid_complete_model_residual', fixture='synthetic-only'))


def test_equal_world_objective_against_independent_augmented_least_squares(monkeypatch):
    data = synthetic_rows()
    original_solve = np.linalg.solve
    calls = []
    def solve(a, b):
        calls.append((a.copy(), b.copy()))
        assert a.dtype == b.dtype == np.float64
        return original_solve(a, b)
    monkeypatch.setattr(np.linalg, 'solve', solve)
    a = l.fit_rows(data)
    assert len(calls) == 1 and a['penalty'] == .1
    x = np.array([r['features'] for r in data['rows']])
    y = np.array([r['target'] for r in data['rows']])
    w = np.array([1 / (16 * sum(q['world_id'] == r['world_id'] for q in data['rows'])) for r in data['rows']])
    means = sum(w[i] * x[i] for i in range(58))
    scales = np.sqrt(sum(w[i] * (x[i] - means) ** 2 for i in range(58)))
    design = np.column_stack((np.ones(58), (x - means) / scales))
    augmented = np.vstack((np.sqrt(w[:, None]) * design, np.sqrt(.1) * np.eye(13)))
    labels = np.r_[np.sqrt(w) * y, np.zeros(13)]
    independent = np.linalg.lstsq(augmented, labels, rcond=None)[0]
    np.testing.assert_allclose(a['beta'], independent, rtol=1e-13, atol=1e-13)
    np.testing.assert_array_equal(a['means'], means)
    for world in l.WORLD_IDS:
        assert sum(w[i] for i, r in enumerate(data['rows']) if r['world_id'] == world) == 1/16
    objective = sum(w * (design @ independent - y) ** 2) + .1 * sum(independent ** 2)
    assert a['diagnostics']['objective'] == pytest.approx(objective, abs=1e-13)
    assert a['diagnostics']['solve_count'] == 1
    assert a['row_identities'][0]['source'] == data['rows'][0]['source']
    json.dumps(a, allow_nan=False)


def test_identical_columns_exact_zero_and_intercept_is_penalized():
    data = synthetic_rows()
    for row in data['rows']:
        row['features'] = [.1] * 12
        row['target'] = 2.
    a = l.fit_rows(data)
    assert a['means'] == [.1] * 12 and a['scales'] == [1.] * 12
    np.testing.assert_array_equal(a['beta'][1:], np.zeros(12))
    assert a['beta'][0] == pytest.approx(2 / 1.1, abs=1e-15)
    assert a['diagnostics']['constant_columns'] == list(range(12))
    np.testing.assert_array_equal((np.full((58,12), .1) - a['means']) / a['scales'], 0)


@pytest.mark.parametrize('mutation', ['hash','world','row_count','counts','duplicate','source','shape','nan','label'])
def test_fit_fails_closed(mutation):
    d = synthetic_rows()
    if mutation == 'hash': d['manifest']['summary']['sha256'] = 'unbound'
    if mutation == 'world': d['rows'][0]['world_id'] = 77
    if mutation == 'row_count': d['rows'].pop()
    if mutation == 'counts': d['rows'][0]['world_id'] = l.WORLD_IDS[1]
    if mutation == 'duplicate': d['rows'][0]['branch_id'] = d['rows'][1]['branch_id']
    if mutation == 'source': d['rows'][0]['source'] = {}
    if mutation == 'shape': d['rows'][0]['features'].pop()
    if mutation == 'nan': d['rows'][0]['target'] = np.nan
    if mutation == 'label': d['manifest']['label_kind'] = 'native-return'
    with pytest.raises(ValueError): l.fit_rows(d)


@pytest.mark.parametrize('initiated', [True,False])
def test_zero_beta_returns_original_R_exactly_including_decline(initiated):
    b = bank([candidate(predicted_total_J=2000), candidate(site=1, predicted_total_J=100)], initiated=initiated)
    chosen, record = l.choose_plan(artifact(), b, report(), 1)
    assert chosen == b['original_R'] if initiated else chosen is None
    assert record['zero_beta_fallback'] is True
    if chosen:
        chosen['commands'][0][0] = 9
        assert b['original_R']['commands'][0][0] == 0


def test_nonzero_strict_decline_and_positive_selection():
    beta = [0.] * 13
    beta[0] = .25
    b = bank([candidate(predicted_total_J=795)])  # -.25 + .25 exactly zero
    chosen, record = l.choose_plan(artifact(beta), b, report(), 1)
    assert chosen is None and record['predicted_advantages'] == [0.]
    b['champions'][0]['selected']['predicted_total_J'] += 1
    chosen, record = l.choose_plan(artifact(beta), b, report(), 1)
    assert chosen == b['champions'][0] and record['selected_index'] == 0


@pytest.mark.parametrize('field,low,high,winner', [
    ('predicted_total_served', 9300, 9400, 1), ('path',100,150,0),
    ('duration',10,20,0), ('member',1,2,0), ('site',3,4,0)])
def test_tie_order(field,low,high,winner):
    cs = [candidate(**{field:low}), candidate(**{field:high})]
    beta = [.1] + [0.] * 12
    chosen, record = l.choose_plan(artifact(beta), bank(cs), report(), 1)
    assert record['selected_index'] == winner and chosen['selected'] == cs[winner]


@pytest.mark.parametrize('mutation', ['beta','means','scales','nan','penalty','schema'])
def test_choose_invalid_artifact(mutation):
    a = artifact()
    if mutation in ('beta','means'): a[mutation].pop()
    if mutation == 'scales': a['scales'][0] = 0
    if mutation == 'nan': a['beta'][1] = np.nan
    if mutation == 'penalty': a['penalty'] = .1 / 58
    if mutation == 'schema': a['schema'] = 'other'
    with pytest.raises(ValueError): l.choose_plan(a, bank([candidate()]), report(), 1)


@pytest.fixture
def bound_fixture(tmp_path, monkeypatch):
    """A fabricated archive at paid IDs, never the actual source or final panel."""
    raw = tmp_path / 'raw'
    raw.mkdir()
    def ref(name, payload, is_raw=True):
        root = raw if is_raw else tmp_path
        (root / name).write_bytes(payload)
        return dict(path=('raw/' if is_raw else '') + name, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    def npz(**arrays):
        stream = io.BytesIO()
        np.savez_compressed(stream, **arrays)
        return stream.getvalue()
    episodes = []
    for world, count in zip(l.WORLD_IDS, l.CHAMPION_COUNTS):
        reports = np.repeat(report()[None], 46, axis=0)
        reports[:,-1] = np.arange(40,500,10)/500
        report_payload = npz(reports=reports, report_times=np.arange(40,500,10,dtype=np.int64))
        branches, models, traced = [], [], []
        for i in range(count + 1):
            bid = 'stay' if i == 0 else f'm{i}_s0'
            c = None if i == 0 else candidate(member=i)
            summary = dict(total_J=920 + i * 5)
            branches.append(dict(id=bid, stationary_candidate=c, summary=summary))
            models.append(dict(id=bid, summary=summary,
                raw=ref(f'{world}_{bid}.npz', report_payload if i==0 else b'synthetic model bytes'),
                decisions=ref(f'{world}_{bid}.jsonl.gz', gzip.compress(b'{}\n'))))
            traced.append(dict(id=bid, plan=None if i == 0 else plan(c), summary=summary))
        decision = dict(t=40, old_mask=1, option=dict(stay_score=STAY), continuation=dict(branches=traced))
        trace = gzip.compress((json.dumps(decision) + '\n').encode())
        episodes.append(dict(arm='T', world_id=world, raw=ref(f'{world}_native.npz',b'synthetic native bytes'),
            decisions=ref(f'{world}_trace.jsonl.gz', trace), model_branches=models,
            stationary_candidates=ref(f'{world}_candidates.npy',b'synthetic stationary bytes'),
            continuation=dict(candidate_count=count * 100, branches=branches)))
    s = dict(status='complete', config=dict(spec=dict(world_ids=list(l.WORLD_IDS), n=8,horizon=500,
        option_t=40,cadence=10), source_bindings=dict(synthetic='no production source')),
        config_artifact=ref('config.json',b'{}',False), reading=ref('reading.json',b'{}',False), episodes=episodes)
    summary_path = tmp_path / 'summary.json'
    def save():
        payload = json.dumps(s).encode()
        summary_path.write_bytes(payload)
        monkeypatch.setattr(l,'EXPECTED_SUMMARY_SHA256',hashlib.sha256(payload).hexdigest())
    save()
    return summary_path, raw, s, save


def test_extract_preserves_exact_source_and_residual_target(bound_fixture):
    summary_path, raw, s, _ = bound_fixture
    d = l.extract_paid_rows(summary_path,raw)
    assert len(d['rows']) == 58 and d['manifest']['world_ids'] == list(l.WORLD_IDS)
    row = d['rows'][0]
    assert row['target'] == pytest.approx(5/500 - .02)
    assert row['source']['stationary']['stay_score_path'] == 'option.stay_score'
    assert row['source']['report']['reference'] == s['episodes'][0]['model_branches'][0]['raw']
    assert row['source']['target']['kind'] == 'paid_complete_model_residual'
    assert len(d['manifest']['references']) == 2 + sum(3 + 2 * (m+1) for m in l.CHAMPION_COUNTS)
    json.dumps(d, allow_nan=False)


@pytest.mark.parametrize('mutation', ['summary_hash','raw_hash','raw_bytes','path','report_shape',
    'report_dtype','report_time','trace_candidate','branch_target','world','champion_count'])
def test_extract_failclosed(bound_fixture,mutation):
    summary_path, raw, s, save = bound_fixture
    e = s['episodes'][0]
    if mutation == 'summary_hash':
        summary_path.write_bytes(summary_path.read_bytes() + b' ')
    elif mutation == 'raw_hash':
        (raw / e['raw']['path'].split('/')[-1]).write_bytes(b'corrupted')
    elif mutation == 'raw_bytes':
        e['raw']['bytes'] += 1
        save()
    elif mutation == 'path':
        e['raw']['path'] = 'raw/../summary.json'
        save()
    elif mutation.startswith('report_'):
        ref = e['model_branches'][0]['raw']
        path = raw / ref['path'].split('/')[-1]
        with np.load(path) as archive:
            reports, times = archive['reports'], archive['report_times']
        if mutation == 'report_shape': reports = reports[:45]
        if mutation == 'report_dtype': reports = reports.astype(np.float64)
        if mutation == 'report_time': times[0] = 30
        stream = io.BytesIO()
        np.savez_compressed(stream,reports=reports,report_times=times)
        payload = stream.getvalue()
        path.write_bytes(payload)
        ref.update(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
        save()
    elif mutation == 'trace_candidate':
        e['continuation']['branches'][1]['stationary_candidate']['path'] += 1
        save()
    elif mutation == 'branch_target':
        e['continuation']['branches'][1]['summary'] = dict(total_J=1)
        save()
    elif mutation == 'world':
        e['world_id'] = 9
        save()
    elif mutation == 'champion_count':
        e['continuation']['candidate_count'] += 1
        save()
    with pytest.raises(ValueError): l.extract_paid_rows(summary_path,raw)
