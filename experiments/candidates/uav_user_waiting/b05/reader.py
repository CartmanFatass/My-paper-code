"""Independent complete B05 allocation and endpoint reconstruction.

No producer allocator, endpoint reducer or paired reducer is imported here.
The original reference uses separate row sorting, valid only after checking
that the frozen cochannel radio gives each user at most one eligible UAV.
"""

from collections import Counter
import hashlib
import math
from pathlib import Path
import resource
import time

import numpy as np

from . import protocol as p

ROOT = Path(__file__).resolve().parents[4]


def _bound_identity(path, expected, counts):
    identity = p.file_identity(path, counts)
    if identity['sha256'] != expected['sha256'] or identity['bytes'] != expected['bytes']:
        raise ValueError(f'input identity mismatch: {path}')
    return identity


def read_source(source_run, source_reading, counts, source_root=ROOT):
    """Independently bind source inventory before any allocation reconstruction."""
    source_run = Path(source_run).resolve(strict=True)
    summary_identity = p.file_identity(source_run / 'summary.json', counts)
    if summary_identity['sha256'] != p.SUMMARY_SHA256:
        raise ValueError('original summary hash differs from frozen B04')
    reading_identity = p.file_identity(source_reading, counts)
    if reading_identity['sha256'] != p.READING_SHA256:
        raise ValueError('original reading hash differs from frozen B04')
    summary = p.read_json(source_run / 'summary.json')
    if (summary.get('status') != 'COMPLETE' or summary.get('object') != 'UAV-USER-WAITING-B04'
            or summary.get('launch_sha') != p.SOURCE_SHA):
        raise ValueError('original summary is not the complete frozen B04')
    config = summary['config']
    if (config['launch_sha'] != p.SOURCE_SHA or config['horizon'] != p.HORIZON
            or config['nodes'] != p.N or config['users'] != p.U
            or config['seeds'] != list(p.SEEDS) or config['arms'] != ['M', 'S', 'U', 'K']):
        raise ValueError('original panel or host identity differs')
    source_ids = {row['path']: row for row in config['source_identities']}
    if len(source_ids) != len(config['source_identities']):
        raise ValueError('duplicate original source identity')
    checked_sources = []
    for relative in p.SOURCE_PATHS:
        actual = _bound_identity(Path(source_root) / relative, source_ids[relative], counts)
        checked_sources.append(dict(actual, path=relative))
    rows = [row for row in summary['rows'] if row['arm'] in p.PROGRAMS]
    by = {(row['arm'], row['seed']): row for row in rows}
    expected = {(program, seed) for program in p.PROGRAMS for seed in p.SEEDS}
    if len(rows) != 192 or len(by) != 192 or set(by) != expected:
        raise ValueError('original input inventory is incomplete or duplicated')
    for (program, seed), row in by.items():
        target = source_run / 'raw' / f'{program}_{seed}.npz'
        if Path(row['raw']['path']).resolve(strict=True) != target.resolve(strict=True):
            raise ValueError('original raw path binding differs')
        if row['steps'] != p.HORIZON:
            raise ValueError('original source row is truncated')
    if sum(row['raw']['bytes'] for row in rows) != 262741183:
        raise ValueError('original M/S/U byte inventory differs')
    return by, dict(summary=summary_identity, reading=reading_identity,
                    frozen_source_identities=checked_sources)


def read_raw(source_row, counts):
    """Read only the needed arrays from one hash-bound original NPZ."""
    path = Path(source_row['raw']['path'])
    keys = ('sinr', 'mask', 'connections', 'served', 'quality', 'reward',
            'completed_steps', 'program', 'world_seed', 'training_episode',
            'actual_contacts', 'actual_ages', 'unserved_gap_rows', 'per_user_mean_age')
    digest, size = hashlib.sha256(), 0
    counts['hash_files'] += 1
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
            counts['hash_bytes'] += len(block)
        identity = dict(path=str(path.resolve()), bytes=size, sha256=digest.hexdigest())
        if any(identity[key] != source_row['raw'][key] for key in ('sha256', 'bytes')):
            raise ValueError('original raw input hash/bytes differ')
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as archive:
            raw = {name: archive[name] for name in keys}
    if (raw['completed_steps'].shape != () or int(raw['completed_steps']) != p.HORIZON
            or raw['program'].shape != () or str(raw['program']) != source_row['arm']
            or raw['world_seed'].shape != () or int(raw['world_seed']) != source_row['seed']
            or raw['training_episode'].shape != () or raw['training_episode'].dtype != bool
            or bool(raw['training_episode'])):
        raise ValueError('original raw episode binding differs')
    if raw['sinr'].shape != (p.HORIZON, p.N, p.U) or raw['sinr'].dtype != np.float64:
        raise ValueError('original SINR shape or dtype differs')
    if raw['connections'].shape != raw['sinr'].shape or raw['connections'].dtype != bool:
        raise ValueError('original connection shape or dtype differs')
    if raw['actual_contacts'].shape != (p.HORIZON, p.U) or raw['actual_contacts'].dtype != bool:
        raise ValueError('original contact history shape/type differs')
    if raw['actual_ages'].shape != (p.HORIZON, p.U) or raw['actual_ages'].dtype.kind not in 'iu':
        raise ValueError('original age history shape/type differs')
    if (raw['unserved_gap_rows'].ndim != 2 or raw['unserved_gap_rows'].shape[1] != 6
            or raw['unserved_gap_rows'].dtype.kind not in 'iu'):
        raise ValueError('original gap history shape/type differs')
    if raw['per_user_mean_age'].shape != (p.U,) or not np.isfinite(raw['per_user_mean_age']).all():
        raise ValueError('original per-user age values differ')
    for name in ('served', 'quality', 'reward', 'mask'):
        if raw[name].shape != (p.HORIZON,):
            raise ValueError(f'original {name} shape differs')
    if raw['served'].dtype.kind not in 'iu' or raw['mask'].dtype.kind not in 'iu':
        raise ValueError('original served/mask types differ')
    for name in ('quality', 'reward'):
        if raw[name].dtype != np.float64 or not np.isfinite(raw[name]).all():
            raise ValueError(f'original {name} values differ')
    counts['source_traces'] += 1
    counts['source_raw_bytes_hashed'] += identity['bytes']
    return raw, identity


def reference_allocations(sinr, masks, counts, paid_allocator_cpu=None):
    """Return ORIGINAL/RR/LRS assignment matrices from local, causal inputs."""
    values = np.asarray(sinr)
    horizon, nodes, users = values.shape
    if values.dtype != np.float64 or nodes != 5 or users != 50:
        raise ValueError('reference requires float64 SINR [H,5,50]')
    masks = np.asarray(masks)
    if masks.shape != (horizon,) or masks.dtype.kind not in 'iu':
        raise ValueError('invalid transmitter masks')
    if np.any(masks < 0) or np.any(masks > 31):
        raise ValueError('invalid transmitter mask bits')
    result = np.zeros((3, horizon, nodes, users), dtype=bool)
    eligibility = np.zeros((horizon, nodes, users), dtype=bool)
    cursors = [0] * nodes
    own_last = [[-1] * users for _ in range(nodes)]
    allocator_cpu = [0.0] * 3
    for tick in range(horizon):
        active = np.array([bool(int(masks[tick]) & (1 << i)) for i in range(nodes)])
        if not np.isfinite(values[tick, active]).all():
            raise ValueError('active SINR must be finite')
        if not np.isneginf(values[tick, ~active]).all():
            raise ValueError('inactive SINR must be negative infinity')
        eligible = values[tick] >= 3.0
        counts['threshold_entries'] += nodes * users
        if np.any(eligible.sum(axis=0) > 1):
            raise ValueError('source violates disjoint eligibility')
        eligibility[tick] = eligible
        for node in range(nodes):
            ids = [u for u in range(users) if eligible[node, u]]
            local_sinrs = {u: float(values[tick, node, u]) for u in ids}
            capacity = min(10, len(ids))
            before = time.process_time()
            original = sorted(ids, key=lambda u: (-local_sinrs[u], u))[:capacity]
            elapsed = time.process_time() - before
            allocator_cpu[0] += elapsed
            if paid_allocator_cpu is not None:
                paid_allocator_cpu['ORIGINAL'] += elapsed
            result[0, tick, node, original] = True
            counts['reference_original_row_calls'] += 1
            before = time.process_time()
            # Independent Python ordering of the registered-ID cyclic distance.
            cyclic = sorted(ids, key=lambda u: (u - cursors[node]) % users)[:capacity]
            if cyclic:
                cursors[node] = (cyclic[-1] + 1) % users
            elapsed = time.process_time() - before
            allocator_cpu[1] += elapsed
            if paid_allocator_cpu is not None:
                paid_allocator_cpu['RR'] += elapsed
            result[1, tick, node, cyclic] = True
            counts['rr_row_calls'] += 1
            before = time.process_time()
            recent = sorted(ids, key=lambda u: (own_last[node][u], -local_sinrs[u], u))[:capacity]
            for user in recent:
                own_last[node][user] = tick
            elapsed = time.process_time() - before
            allocator_cpu[2] += elapsed
            if paid_allocator_cpu is not None:
                paid_allocator_cpu['LRS'] += elapsed
            result[2, tick, node, recent] = True
            counts['lrs_row_calls'] += 1
        counts['fleet_allocations'] += 3
        counts['uav_allocation_decisions'] += 3 * nodes
        counts['source_trace_ticks'] += 1
    return result, eligibility, allocator_cpu


def _intervals(absent):
    """Enumerate half-open true intervals using a scalar transition walk."""
    start = None
    result = []
    for tick, value in enumerate(absent):
        if value and start is None:
            start = tick
        elif not value and start is not None:
            result.append((start, tick))
            start = None
    if start is not None:
        result.append((start, len(absent)))
    return result


def reference_outcome(sinr, eligibility, assigned, original, counts):
    """Scalar age/gap accounting and an independent native-quality reduction."""
    values = np.asarray(sinr)
    choice = np.asarray(assigned)
    eligible = np.asarray(eligibility)
    if choice.dtype != bool or eligible.dtype != bool or choice.shape != values.shape:
        raise ValueError('reference outcome shape/dtype mismatch')
    if eligible.shape != values.shape or np.any(choice & ~eligible):
        raise ValueError('ineligible grant')
    if np.any(choice.sum(axis=1) > 1) or np.any(choice.sum(axis=2) > 10):
        raise ValueError('exclusivity or capacity violation')
    if not np.array_equal(choice.sum(axis=2), np.minimum(10, eligible.sum(axis=2))):
        raise ValueError('allocator is not work-conserving')
    horizon, _, users = values.shape
    contacts = choice.any(axis=1)
    possible = eligible.any(axis=1)
    no_link = ~possible
    denied = possible & ~contacts
    changed = contacts ^ np.asarray(original).any(axis=1)
    served = []
    quality = []
    rewards = []
    ages = np.zeros((horizon, users), dtype=np.int64)
    for tick in range(horizon):
        selected = [float(value) for value in values[tick][choice[tick]]]
        n = len(selected)
        # math.fsum and scalar clamping avoid sharing the producer's reducer.
        q = math.fsum(min(1.0, max(0.0, (v - 3.0) / 30.0)) for v in selected) / max(n, 1)
        served.append(n)
        quality.append(q)
        rewards.append(0.7 * n / users + 0.3 * q)
        for user in range(users):
            ages[tick, user] = 0 if contacts[tick, user] else (1 if tick == 0 else ages[tick - 1, user] + 1)
        counts['service_quality_age_reductions'] += 1
        counts['user_tick_age_updates'] += users
    user_rows = []
    all_gaps = []
    for user in range(users):
        gaps = []
        for start, end in _intervals(~contacts[:, user]):
            gap = dict(start=start, end=end, left_censored=start == 0,
                       right_censored=end == horizon,
                       capacity_denied_ticks=int(denied[start:end, user].sum()),
                       no_link_ticks=int(no_link[start:end, user].sum()))
            if gap['capacity_denied_ticks'] + gap['no_link_ticks'] != end - start:
                raise AssertionError('unserved interval partition failed')
            gaps.append(gap)
        all_gaps.extend(gaps)
        user_rows.append(dict(
            user=user, service_count=int(contacts[:, user].sum()),
            mean_age=float(sum(int(v) for v in ages[:, user]) / horizon),
            max_gap=max((g['end'] - g['start'] for g in gaps), default=0),
            terminal_age=int(ages[-1, user]), gaps=gaps,
            capacity_denied_ticks=int(denied[:, user].sum()),
            no_link_ticks=int(no_link[:, user].sum()),
            eligible_ticks=int(possible[:, user].sum()),
            changed_grant_ticks=int(changed[:, user].sum()),
            no_link_intervals=[dict(start=s, end=e, left_censored=s == 0,
                                    right_censored=e == horizon)
                               for s, e in _intervals(no_link[:, user])]))
    flattened = sorted(int(v) for row in ages for v in row)
    index = 0.95 * (len(flattened) - 1)
    lower, upper = math.floor(index), math.ceil(index)
    percentile = flattened[lower] + (index - lower) * (flattened[upper] - flattened[lower])
    age_sum = sum(flattened)
    square_sum = sum(v * v for v in flattened)
    max_mean = max(row['mean_age'] for row in user_rows)
    gap_max = lambda predicate: max((g['end'] - g['start'] for g in all_gaps if predicate(g)), default=0)
    metrics = dict(
        J=math.fsum(rewards) / horizon, return_sum=math.fsum(rewards),
        mean_served=sum(served) / horizon, mean_quality=math.fsum(quality) / horizon,
        min_served=min(served), zero_service_steps=served.count(0),
        F_user=max_mean, max_user_mean_age=max_mean,
        max_unserved_gap=max(row['max_gap'] for row in user_rows),
        mean_user_max_unserved_gap=sum(row['max_gap'] for row in user_rows) / users,
        A=age_sum / (horizon * users), age_sum=age_sum, age_p95=float(percentile),
        terminal_mean_age=sum(row['terminal_age'] for row in user_rows) / users,
        terminal_max_age=max(row['terminal_age'] for row in user_rows),
        never_served=sum(row['service_count'] == 0 for row in user_rows),
        ever_served=sum(row['service_count'] > 0 for row in user_rows),
        left_censored_gaps=sum(g['left_censored'] for g in all_gaps),
        right_censored_gaps=sum(g['right_censored'] for g in all_gaps),
        max_closed_gap=gap_max(lambda g: not g['left_censored'] and not g['right_censored']),
        max_left_censored_gap=gap_max(lambda g: g['left_censored']),
        max_right_censored_gap=gap_max(lambda g: g['right_censored']),
        mean_age_square=square_sum / (horizon * users), age_square_sum=square_sum)
    sorted_service = sorted(served)
    service_index = 0.1 * (horizon - 1)
    service_lo, service_hi = math.floor(service_index), math.ceil(service_index)
    metrics.update(
        F=sum(any(contacts[tick, user] for tick in range(start, min(start + 64, horizon)))
              for start in range(0, horizon, 64) for user in range(users)),
        G=metrics['mean_user_max_unserved_gap'],
        service_p10=float(sorted_service[service_lo] + (service_index - service_lo) *
                          (sorted_service[service_hi] - sorted_service[service_lo])),
        longest_zero_service=max((end - start for start, end in _intervals([v == 0 for v in served])), default=0))
    local_sizes = eligible.sum(axis=2)
    exposure = dict(changed_grant_user_ticks=int(changed.sum()),
                    changed_grant_fleet_ticks=int(changed.any(axis=1).sum()),
                    changed_grant_uav_ticks=int((choice ^ original).any(axis=2).sum()),
                    changed_grant_users=int(changed.any(axis=0).sum()),
                    capacity_denied_user_ticks=int(denied.sum()),
                    no_link_user_ticks=int(no_link.sum()),
                    eligible_user_ticks=int(possible.sum()),
                    capacity_choice_uav_ticks=int((local_sizes > 10).sum()),
                    exact_capacity_uav_ticks=int((local_sizes == 10).sum()),
                    capacity_choice_fleet_ticks=int((local_sizes > 10).any(axis=1).sum()))
    if int((~contacts).sum()) != exposure['capacity_denied_user_ticks'] + exposure['no_link_user_ticks']:
        raise AssertionError('unserved-tick partition failed')
    return dict(metrics=metrics, per_user=user_rows, exposure=exposure,
                worst_users=[row['user'] for row in user_rows if row['mean_age'] == max_mean],
                served=np.array(served), quality=np.array(quality), reward=np.array(rewards),
                contacts=contacts, ages=ages)


def compare_tree(actual, expected, label, discrepancies):
    """Exact structure/integer checks; absolute-only floating tolerance1e-12."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError(f'{label}: dictionary fields differ')
        for key in expected:
            compare_tree(actual[key], expected[key], f'{label}.{key}', discrepancies)
    elif isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
            raise ValueError(f'{label}: sequence length differs')
        for index, (a, e) in enumerate(zip(actual, expected)):
            compare_tree(a, e, f'{label}[{index}]', discrepancies)
    elif isinstance(expected, float):
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            raise ValueError(f'{label}: nonnumeric floating field')
        difference = abs(actual - expected)
        if not math.isfinite(actual) or not math.isfinite(expected) or difference > 1e-12:
            raise ValueError(f'{label}: {actual!r} != {expected!r}')
        discrepancies['max_abs_float_error'] = max(discrepancies.get('max_abs_float_error', 0.0), difference)
        discrepancies['floating_fields_checked'] = discrepancies.get('floating_fields_checked', 0) + 1
    else:
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(f'{label}: {actual!r} != {expected!r}')
        discrepancies['exact_fields_checked'] = discrepancies.get('exact_fields_checked', 0) + 1


def _schema_row(reference, program, law, seed, inherited, horizon):
    """Only format independently reconstructed values into the public schema."""
    values = dict(reference['metrics'], **reference['exposure'])
    users = []
    for row in reference['per_user']:
        users.append(dict(
            user=row['user'], **{key: row[key] for key in p.VECTOR_FIELDS},
            gaps=[[int(gap[key]) for key in p.GAP_COLUMNS] for gap in row['gaps']],
            no_link_intervals=[[int(gap[key]) for key in p.NO_LINK_COLUMNS]
                               for gap in row['no_link_intervals']]))
    return dict(program=program, law=law, package=f'{program}:{law}', seed=seed,
                steps=horizon, complete=True, inherited=inherited, per_user=users,
                **{key: values[key] for key in p.OUTCOME_METRICS})


def _metric(row, key):
    return row['inherited'][key] if key in p.INHERITED_METRICS else row[key]


def _describe(values):
    # Numerical library primitives are shared; grouping, pairing and the reader
    # code are independent of the producer's outcome and paired reducers.
    array = np.asarray(values, dtype=np.float64)
    mean = float(np.mean(array))
    sd = float(np.std(array, ddof=1)) if len(array) > 1 else 0.0
    half_width = p.T_CRITICAL * sd / math.sqrt(len(array))
    return dict(values=array.tolist(), n=len(array), mean=mean, sd=sd,
                descriptive_t95=[mean - half_width, mean + half_width])


def reference_paired(rows, seeds=p.SEEDS):
    by = {(row['package'], row['seed']): row for row in rows}
    expected = {(package, seed) for package in p.PACKAGES for seed in seeds}
    if len(by) != len(rows) or set(by) != expected:
        raise ValueError('independent paired panel is incomplete or duplicated')
    levels = {}
    for package in p.PACKAGES:
        levels[package] = {key: _describe([_metric(by[package, seed], key) for seed in seeds])
                           for key in p.METRICS}
    contrasts = {}
    for index, left in enumerate(p.PACKAGES):
        for right in p.PACKAGES[:index]:
            contrasts[f'{left}-{right}'] = {
                key: _describe([_metric(by[left, seed], key) - _metric(by[right, seed], key)
                                for seed in seeds]) for key in p.METRICS}
    return dict(world_seeds=list(seeds), levels=levels, contrasts=contrasts)


def _check_original_metrics(source_row, reference, discrepancies):
    # The original saved endpoint and the new reconstruction are separate
    # evidence. Compare every common age/gap/native scalar, not only the means.
    original_fields = set(reference['metrics']).intersection(source_row)
    for key in sorted(original_fields):
        compare_tree(source_row[key], reference['metrics'][key], f'B04.{key}', discrepancies)
    if 'per_user_mean_age' in source_row:
        compare_tree(source_row['per_user_mean_age'],
                     [row['mean_age'] for row in reference['per_user']],
                     'B04.per_user_mean_age', discrepancies)
    if 'worst_users' in source_row:
        compare_tree(source_row['worst_users'], reference['worst_users'], 'B04.worst_users', discrepancies)
    if 'per_user_gaps' in source_row:
        gaps = {}
        for group in ('all', 'closed', 'left_censored', 'right_censored'):
            lengths = []
            for row in reference['per_user']:
                chosen = []
                for gap in row['gaps']:
                    included = (group == 'all' or
                                (group == 'closed' and not gap['left_censored'] and not gap['right_censored']) or
                                (group == 'left_censored' and gap['left_censored']) or
                                (group == 'right_censored' and gap['right_censored']))
                    if included:
                        chosen.append(gap['end'] - gap['start'])
                lengths.append(chosen)
            gaps[group] = dict(counts=[len(x) for x in lengths],
                               maxima=[max(x, default=0) for x in lengths],
                               totals=[sum(x) for x in lengths])
        compare_tree(source_row['per_user_gaps'], gaps, 'B04.per_user_gaps', discrepancies)


def verify_trace(raw, source_row, outcome, compact_rows, fair_archive, counts, discrepancies,
                 paid_allocator_cpu=None):
    """Check one complete input and every law without any producer numerics."""
    horizon = len(raw['sinr'])
    program, seed = source_row['arm'], source_row['seed']
    if len(compact_rows) != 3 or len(outcome['rows']) != 3:
        raise ValueError('trace requires exactly three outcome rows')
    compact_by = {row['law']: row for row in compact_rows}
    full_by = {row['law']: row for row in outcome['rows']}
    if set(compact_by) != set(p.LAWS) or set(full_by) != set(p.LAWS):
        raise ValueError('trace laws missing or duplicated')
    assignments, eligibility, cpu = reference_allocations(raw['sinr'], raw['mask'], counts, paid_allocator_cpu)
    if not np.array_equal(assignments[0], raw['connections']):
        raise ValueError('original connection reconstruction differs')
    if fair_archive['contacts'].shape != (2, horizon, p.U) or fair_archive['contacts'].dtype != bool:
        raise ValueError('fair contact stream shape or dtype differs')
    if not np.array_equal(fair_archive['contacts'], assignments[1:].any(axis=2)):
        raise ValueError('fair contact stream differs from independent reconstruction')
    for name, expected in (
        ('laws', np.array(p.LAWS[1:])), ('program', np.array(program)),
        ('seed', np.array(seed)), ('completed_steps', np.array([horizon, horizon])),
        ('source_sha256', np.array(source_row['raw']['sha256'])),
    ):
        if not np.array_equal(fair_archive[name], expected):
            raise ValueError(f'fair contact binding differs: {name}')
    reconstructed_rows = []
    for law_index, law in enumerate(p.LAWS):
        reconstructed = reference_outcome(raw['sinr'], eligibility, assignments[law_index],
                                          assignments[0], counts)
        if not np.array_equal(reconstructed['served'], raw['served']):
            raise ValueError('per-tick served count differs from original')
        if np.any(reconstructed['quality'] - raw['quality'] > p.ATOL):
            raise ValueError('per-tick quality exceeds original ceiling')
        if np.any(reconstructed['reward'] - raw['reward'] > p.ATOL):
            raise ValueError('per-tick J exceeds original ceiling')
        if law == 'ORIGINAL':
            for key in ('quality', 'reward'):
                error = float(np.max(np.abs(reconstructed[key] - raw[key])))
                if error > p.ATOL:
                    raise ValueError(f'original native {key} reconstruction differs')
                field = f'max_original_{key}_error'
                discrepancies[field] = max(discrepancies.get(field, 0.0), error)
            for key, expected in (('actual_contacts', reconstructed['contacts']),
                                  ('actual_ages', reconstructed['ages'])):
                if not np.array_equal(raw[key], expected):
                    raise ValueError(f'original {key} differs')
            gap_rows = np.array([[row['user'], gap['start'], gap['end'], gap['end'] - gap['start'],
                                  int(gap['left_censored']), int(gap['right_censored'])]
                                 for row in reconstructed['per_user'] for gap in row['gaps']], dtype=np.int64).reshape(-1, 6)
            if not np.array_equal(raw['unserved_gap_rows'], gap_rows):
                raise ValueError('original gap endpoints/censoring differ')
            compare_tree(raw['per_user_mean_age'].tolist(),
                         [row['mean_age'] for row in reconstructed['per_user']],
                         'raw.per_user_mean_age', discrepancies)
            _check_original_metrics(source_row, reconstructed, discrepancies)
            counts['original_outcomes'] += 1
        else:
            counts['fair_outcomes'] += 1
        # The producer may retain additional original diagnostics; every retained
        # inherited item must agree with its pinned source rather than a replay.
        supplied_inherited = full_by[law]['inherited']
        for key, value in supplied_inherited.items():
            if key not in source_row:
                raise ValueError(f'inherited field absent from B04: {key}')
            compare_tree(value, source_row[key], f'inherited.{key}', discrepancies)
        if not all(key in supplied_inherited for key in p.INHERITED_METRICS):
            raise ValueError('missing declared inherited metric')
        expected = _schema_row(reconstructed, program, law, seed, supplied_inherited, horizon)
        compare_tree(full_by[law], expected, f'{program}/{seed}/{law}', discrepancies)
        vector_row = {key: value for key, value in expected.items() if key != 'per_user'}
        vector_row['per_user_vectors'] = {key: [row[key] for row in expected['per_user']]
                                         for key in p.VECTOR_FIELDS}
        vector_row['source'] = source_row['raw']
        actual_compact = {key: value for key, value in compact_by[law].items()
                          if key not in ('outcome', 'contacts')}
        compare_tree(actual_compact, vector_row, f'compact/{program}/{seed}/{law}', discrepancies)
        reconstructed_rows.append(vector_row)
    return reconstructed_rows, dict(allocator_cpu_seconds=dict(zip(p.LAWS, cpu)))


def _resources(started):
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return dict(wall_seconds=time.perf_counter() - started,
                process_user_cpu_seconds=usage.ru_utime,
                process_system_cpu_seconds=usage.ru_stime,
                process_cpu_seconds=usage.ru_utime + usage.ru_stime,
                peak_rss_bytes=int(usage.ru_maxrss * 1024),
                scope='whole Linux reader process; allocator timing is replay computation, not live latency')


def _worker_config_check(config, worker_launch_sha, source, counts, discrepancies):
    expected = dict(object=p.OBJECT, launch_sha=worker_launch_sha,
                    seeds=list(p.SEEDS), programs=list(p.PROGRAMS), laws=list(p.LAWS),
                    packages=list(p.PACKAGES), horizon=p.HORIZON, nodes=p.N, users=p.U,
                    capacity=p.CAPACITY, min_sinr=p.MIN_SINR, t_critical=p.T_CRITICAL,
                    atol=p.ATOL, b04_source_sha=p.SOURCE_SHA,
                    gap_columns=list(p.GAP_COLUMNS), no_link_columns=list(p.NO_LINK_COLUMNS))
    for key, value in expected.items():
        compare_tree(config[key], value, f'config.{key}', discrepancies)
    compare_tree(config['b04_summary'], source['summary'], 'config.b04_summary', discrepancies)
    compare_tree(config['b04_reading'], source['reading'], 'config.b04_reading', discrepancies)
    compare_tree(config['expected_counts'], p.expected_counts(), 'config.expected_counts', discrepancies)
    identities = config['source_identities']
    by = {identity['relative_path']: identity for identity in identities}
    if len(by) != len(identities):
        raise ValueError('duplicate producer source identity')
    required = {f'experiments/candidates/uav_user_waiting/b05/{name}.py'
                for name in ('__init__', 'protocol', 'allocation', 'study', 'run')}
    if not required.issubset(by):
        raise ValueError('missing producer executable source binding')
    for relative, identity in by.items():
        if Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError('producer source identity is not a repository path')
        _bound_identity(ROOT / relative, identity, counts)
    bindings = config['source_bindings']
    source_by = {identity['relative_path']: identity for identity in bindings}
    if len(source_by) != len(bindings) or set(source_by) != set(p.SOURCE_PATHS):
        raise ValueError('producer source bindings differ from frozen source proof')
    for identity in source['frozen_source_identities']:
        expected = source_by[identity['path']]
        if any(expected[key] != identity[key] for key in ('sha256', 'bytes')):
            raise ValueError('producer source binding hash/bytes differ')


def read_batch(run, out, launch_sha, worker_launch_sha, worker_summary_sha256,
               *, entry_start=None, admission=None):
    """Complete separately admitted verification, with retained failure prefix."""
    started = time.perf_counter() if entry_start is None else entry_start
    out, run = Path(out), Path(run).resolve(strict=True)
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ('reading.json', 'config.json', 'progress.json')):
        raise FileExistsError(f'independent reading output already exists: {out}')
    counts = Counter({key: 0 for key in p.ZERO_COUNTS})
    paid_allocator_cpu = dict.fromkeys(p.LAWS, 0.0)
    discrepancies = dict(max_abs_float_error=0.0, floating_fields_checked=0, exact_fields_checked=0)
    result = dict(object=p.OBJECT + '-READ', status='INCOMPLETE', launch_sha=launch_sha,
                  worker_launch_sha=worker_launch_sha, rows=[], traces=[], paired=None,
                  counts=counts, discrepancies=discrepancies, failure=None,
                  admission=admission, resources_unmeasured=False,
                  allocator_timing_scope='all measured local selectors, including a failed or partial trace; excludes hashing and outcome reduction',
                  verification_scope='every original/fair grant, service/quality/J tick, user age/gap/censor/exclusion record, inherited value and36paired contrasts; no old C/search/model replay',
                  original_reference='independent per-UAV stable SINR sorting after disjoint-eligibility check')
    current_trace = None
    try:
        worker_identity = p.file_identity(run / 'summary.json', counts)
        if worker_identity['sha256'] != worker_summary_sha256:
            raise ValueError('producer summary differs from explicitly bound SHA256')
        worker = p.read_json(run / 'summary.json')
        if (worker['object'] != p.OBJECT or worker['status'] != 'COMPLETE'
                or worker['launch_sha'] != worker_launch_sha):
            raise ValueError('producer is not the bound complete B05 operation')
        b04_summary = Path(worker['config']['b04_summary']['path'])
        b04_reading = Path(worker['config']['b04_reading']['path'])
        b04_source_root = ROOT
        source_rows, source = read_source(b04_summary.parent, b04_reading, counts, b04_source_root)
        if Path(source['summary']['path']) != Path(b04_summary).resolve(strict=True):
            raise ValueError('source summary path differs from supplied argument')
        _worker_config_check(worker['config'], worker_launch_sha, source, counts, discrepancies)
        config_identity = p.file_identity(run / 'config.json', counts)
        compare_tree(p.read_json(run / 'config.json'), worker['config'], 'producer.config', discrepancies)
        for key, value in p.expected_counts().items():
            compare_tree(worker['counts'][key], value, f'producer.counts.{key}', discrepancies)
        all_rows = worker['rows']
        by = {(row['program'], row['seed'], row['law']): row for row in all_rows}
        expected_keys = {(program, seed, law) for program in p.PROGRAMS for seed in p.SEEDS for law in p.LAWS}
        if len(all_rows) != len(expected_keys) or len(by) != len(expected_keys) or set(by) != expected_keys:
            raise ValueError('producer panel is incomplete or duplicated')
        config = dict(object=p.OBJECT + '-READ', launch_sha=launch_sha,
                      worker_launch_sha=worker_launch_sha, worker_summary=worker_identity,
                      worker_config=config_identity, source=source,
                      seeds=list(p.SEEDS), programs=list(p.PROGRAMS), laws=list(p.LAWS),
                      horizon=p.HORIZON, source_root=str(Path(b04_source_root).resolve(strict=True)),
                      verification_scope=result['verification_scope'])
        result['config'] = config
        p.write_json(out / 'config.json', config)
        for seed in p.SEEDS:
            for program in p.PROGRAMS:
                current_trace = dict(program=program, seed=seed)
                source_row = source_rows[program, seed]
                compact = [by[program, seed, law] for law in p.LAWS]
                raw, raw_identity = read_raw(source_row, counts)
                outcome_path = run / 'outcomes' / f'{program}_{seed}.json'
                contacts_path = run / 'contacts' / f'{program}_{seed}.npz'
                for row in compact:
                    for key, path in (('outcome', outcome_path), ('contacts', contacts_path)):
                        if Path(row[key]['path']).resolve(strict=True) != path.resolve(strict=True):
                            raise ValueError(f'producer {key} path binding differs')
                        compare_tree(row[key], compact[0][key], f'{key}.shared_identity', discrepancies)
                outcome_identity = _bound_identity(outcome_path, compact[0]['outcome'], counts)
                contacts_identity = _bound_identity(contacts_path, compact[0]['contacts'], counts)
                outcome = p.read_json(outcome_path)
                for key, value in (('program', program), ('seed', seed), ('steps', p.HORIZON), ('complete', True)):
                    compare_tree(outcome[key], value, f'outcome.{key}', discrepancies)
                compare_tree(outcome['source'], source_row['raw'], 'outcome.source', discrepancies)
                compare_tree(outcome['contacts'], contacts_identity, 'outcome.contacts', discrepancies)
                compare_tree(outcome['completed_by_law'], dict.fromkeys(p.LAWS, p.HORIZON),
                             'outcome.completed_by_law', discrepancies)
                compare_tree(outcome['gap_columns'], list(p.GAP_COLUMNS), 'outcome.gap_columns', discrepancies)
                compare_tree(outcome['no_link_columns'], list(p.NO_LINK_COLUMNS), 'outcome.no_link_columns', discrepancies)
                with np.load(contacts_path, allow_pickle=False) as archive:
                    required = {'contacts', 'laws', 'program', 'seed', 'completed_steps', 'source_sha256'}
                    if set(archive.files) != required:
                        raise ValueError('fair contact archive fields differ')
                    fair = {key: archive[key] for key in required}
                rows, timing = verify_trace(raw, source_row, outcome, compact, fair, counts, discrepancies,
                                            paid_allocator_cpu)
                result['rows'].extend(rows)
                result['traces'].append(dict(program=program, seed=seed, source=raw_identity,
                                              outcome=outcome_identity, contacts=contacts_identity, **timing))
                counts['complete_traces'] += 1
                p.write_json(out / 'progress.json', dict(current_trace=current_trace, counts=dict(counts),
                                                         resources=_resources(started), discrepancies=discrepancies))
        independently_paired = reference_paired(result['rows'], seeds=p.SEEDS)
        for key in ('world_seeds', 'levels', 'contrasts'):
            compare_tree(worker['paired'][key], independently_paired[key], f'paired.{key}', discrepancies)
        result['paired'] = independently_paired
        traces, laws = len(p.SEEDS) * len(p.PROGRAMS), len(p.LAWS)
        ticks = traces * p.HORIZON
        expected_reader_counts = dict(source_traces=traces, source_trace_ticks=ticks,
            fleet_allocations=laws*ticks, uav_allocation_decisions=laws*p.N*ticks,
            reference_original_row_calls=p.N*ticks, rr_row_calls=p.N*ticks, lrs_row_calls=p.N*ticks,
            service_quality_age_reductions=laws*ticks, user_tick_age_updates=laws*p.U*ticks,
            threshold_entries=p.N*p.U*ticks, original_outcomes=traces, fair_outcomes=2*traces,
            source_raw_bytes_hashed=sum(row['raw']['bytes'] for row in source_rows.values()), complete_traces=traces,
            **{key: 0 for key in p.ZERO_COUNTS})
        for key, value in expected_reader_counts.items():
            if counts[key] != value:
                raise ValueError(f'independent reader count differs: {key}')
        result['status'] = 'COMPLETE'
    except Exception as error:
        result['status'] = 'FAILED'
        result['failure'] = dict(type=type(error).__name__, message=str(error), current_trace=current_trace)
    result['counts'] = dict(counts)
    result['resources'] = _resources(started)
    result['allocator_cpu_seconds'] = paid_allocator_cpu
    p.write_json(out / 'reading.json', result)
    return result
