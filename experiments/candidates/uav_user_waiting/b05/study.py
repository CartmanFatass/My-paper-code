"""Hash-bound streaming replay; imports only stdlib/NumPy and local allocators."""

import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np

from . import protocol as p
from .allocation import RoundRobin, LeastRecentlyServed

ROOT = Path(__file__).resolve().parents[4]
RAW_FIELDS = ('program', 'world_seed', 'completed_steps', 'sinr', 'connections', 'mask',
              'served', 'quality', 'reward', 'actual_contacts', 'actual_ages',
              'unserved_gap_rows', 'per_user_mean_age')


def counters():
    names = ('source_traces', 'source_ticks', 'original_outcomes', 'fair_outcomes',
             'fleet_allocations', 'uav_allocation_decisions', 'original_kernel_calls',
             'rr_row_selections', 'lrs_row_selections', 'transition_reductions',
             'user_age_updates', 'threshold_scans', 'threshold_entries', 'hash_files',
             'hash_bytes', 'input_hash_files', 'input_hash_bytes', 'raw_files_loaded',
             'raw_array_bytes_loaded', 'contact_bytes_written', 'outcome_bytes_written',
             'contact_values_retained', 'fair_contact_valid_user_ticks')
    return {key: 0 for key in names + p.ZERO_COUNTS}


def _input_identity(path, counts):
    before = counts['hash_bytes']
    try:
        return p.file_identity(path, counts)
    finally:
        counts['input_hash_files'] += 1
        counts['input_hash_bytes'] += counts['hash_bytes'] - before


def validate_inputs(summary_path, reading_path, source_root, counts):
    paths = [Path(value) for value in (summary_path, reading_path, source_root)]
    p.require(all(path.is_absolute() for path in paths), 'absolute frozen input paths required')
    summary_path, reading_path, source_root = (path.resolve(strict=True) for path in paths)
    summary_id, reading_id = (_input_identity(path, counts) for path in (summary_path, reading_path))
    p.require(summary_id['sha256'] == p.SUMMARY_SHA256, 'B04 summary hash mismatch')
    p.require(reading_id['sha256'] == p.READING_SHA256, 'B04 reading hash mismatch')
    summary, reading = p.read_json(summary_path), p.read_json(reading_path)
    p.require(summary['status'] == 'COMPLETE' and summary['scientific_invocation'] is True,
              'B04 worker is not a complete scientific invocation')
    p.require(summary['object'] == 'UAV-USER-WAITING-B04' and summary['launch_sha'] == p.SOURCE_SHA,
              'B04 worker identity mismatch')
    config = summary['config']
    p.require(config['launch_sha'] == p.SOURCE_SHA and config['seeds'] == list(p.SEEDS)
              and config['arms'] == ['M', 'S', 'U', 'K'] and config['horizon'] == p.HORIZON
              and config['nodes'] == p.N and config['users'] == p.U, 'B04 panel contract mismatch')
    p.require(summary['counts'] == dict(constructors=1, explicit_resets=256, native_step_calls=65536,
              team_steps=65536, complete_episodes=256, fit_started=0, optimizer_steps=0), 'B04 counts mismatch')
    p.require(reading['status'] == 'VERIFIED_COMPLETE' and reading['worker_launch_sha'] == p.SOURCE_SHA
              and reading['expected_summary_sha256'] == p.SUMMARY_SHA256
              and reading['worker_summary'] == dict(summary_id, path=str(p.B04_CANONICAL_RUN / 'summary.json')),
              'B04 full-reader binding mismatch')
    expected = {(arm, seed) for seed in p.SEEDS for arm in ('M', 'S', 'U', 'K')}
    rows = summary['rows']
    p.require(len(rows) == 256 and {(row['arm'], row['seed']) for row in rows} == expected,
              'B04 summary rows missing/duplicated')
    p.require(len(reading['rows']) == 256 and {(row['arm'], row['seed']) for row in reading['rows']} == expected
              and reading['counts']['verified_raw_files'] == 256, 'B04 reader coverage mismatch')
    artifacts = summary['artifacts']
    p.require(sorted(artifacts, key=lambda row: row['path']) == sorted([row['raw'] for row in rows], key=lambda row: row['path']),
              'B04 raw artifact membership mismatch')
    by = {}
    for row in rows:
        p.require(row['steps'] == p.HORIZON, 'incomplete B04 episode')
        path = Path(row['raw']['path'])
        member = f"{row['arm']}_{row['seed']}.npz"
        p.require(path.is_absolute() and path == p.B04_CANONICAL_RUN / 'raw' / member,
                  'B04 raw path is not its canonical member')
        by[row['arm'], row['seed']] = dict(row, raw=dict(
            row['raw'], path=str(summary_path.parent / 'raw' / member), canonical_path=str(path)))
    bindings = {item['path']: item for item in config['source_identities']}
    verified = []
    for name in p.SOURCE_PATHS:
        expected_id = bindings[name]
        actual = _input_identity(source_root / name, counts)
        p.require(actual['sha256'] == expected_id['sha256'] and actual['bytes'] == expected_id['bytes'],
                  'frozen source mismatch: ' + name)
        verified.append(dict(actual, relative_path=name))
    return summary_id, reading_id, verified, by, bindings[p.RADIO_PATH]


def load_radio(source_root, binding, counts):
    """Standalone file import from freshly checked bytes, with no package init/cache."""
    path = Path(source_root) / p.RADIO_PATH
    code = path.read_bytes()
    counts['input_hash_files'] += 1
    counts['input_hash_bytes'] += len(code)
    counts['hash_files'] += 1
    counts['hash_bytes'] += len(code)
    p.require(len(code) == binding['bytes'] and hashlib.sha256(code).hexdigest() == binding['sha256'],
              'radio source changed before standalone import')
    spec = importlib.util.spec_from_file_location('_b05_frozen_radio', path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(code, str(path), 'exec'), module.__dict__)
    return module


def load_trace(identity, counts):
    """Hash and read one open file descriptor; never decompress search/history bulk."""
    path = Path(identity['path'])
    digest, size = hashlib.sha256(), 0
    counts['input_hash_files'] += 1
    counts['hash_files'] += 1
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
            counts['input_hash_bytes'] += len(block)
            counts['hash_bytes'] += len(block)
        p.require(size == identity['bytes'] and digest.hexdigest() == identity['sha256'], 'B04 raw hash/size mismatch')
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as saved:
            raw = {name: saved[name].copy() for name in RAW_FIELDS}
    counts['raw_files_loaded'] += 1
    counts['raw_array_bytes_loaded'] += sum(value.nbytes for value in raw.values())
    return raw


def _validate_trace(raw, row, horizon):
    p.require(0 < horizon <= p.HORIZON and raw['sinr'].shape == (horizon, p.N, p.U)
              and raw['sinr'].dtype == np.float64, 'malformed/truncated scored SINR')
    p.require(raw['connections'].shape == (horizon, p.N, p.U) and raw['connections'].dtype == bool,
              'malformed original assignment bits')
    p.require(raw['mask'].shape == (horizon,) and raw['mask'].dtype.kind in 'iu'
              and np.all((raw['mask'] >= 1) & (raw['mask'] <= 31)), 'malformed original masks')
    p.require(raw['program'].shape == () and str(raw['program']) == row['arm']
              and raw['world_seed'].shape == () and int(raw['world_seed']) == row['seed']
              and raw['completed_steps'].shape == () and int(raw['completed_steps']) == horizon
              and row['steps'] == horizon, 'raw member/complete-episode identity mismatch')
    for name in ('served', 'quality', 'reward'):
        p.require(raw[name].shape == (horizon,) and np.isfinite(raw[name]).all(), 'malformed native ' + name)
    p.require(raw['served'].dtype.kind in 'iu' and raw['quality'].dtype == np.float64
              and raw['reward'].dtype == np.float64, 'native service/quality/reward dtype mismatch')
    p.require(raw['actual_contacts'].shape == (horizon, p.U) and raw['actual_contacts'].dtype == bool,
              'malformed native contact history')
    p.require(raw['actual_ages'].shape == (horizon, p.U) and raw['actual_ages'].dtype.kind in 'iu', 'malformed native ages')
    p.require(raw['per_user_mean_age'].shape == (p.U,) and np.isfinite(raw['per_user_mean_age']).all(),
              'malformed native per-user age')
    p.require(raw['unserved_gap_rows'].ndim == 2 and raw['unserved_gap_rows'].shape[1] == 6
              and raw['unserved_gap_rows'].dtype.kind in 'iu', 'malformed native gap history')
    p.require(np.all(np.isfinite(raw['sinr']) | np.isneginf(raw['sinr'])), 'invalid actual SINR values')


def _intervals(absent):
    padded = np.r_[False, absent, False].astype(np.int8)
    starts = np.flatnonzero(np.diff(padded) == 1)
    ends = np.flatnonzero(np.diff(padded) == -1)
    return [(int(start), int(end)) for start, end in zip(starts, ends)]


def outcome(contacts, ages, native, eligible, changed_uav, original, row, law, complete):
    """Evaluator-only outcomes from paid scored transitions; no policy access."""
    steps = len(contacts)
    if not steps:
        return dict(program=row['arm'], law=law, package=f"{row['arm']}:{law}", seed=row['seed'],
                    steps=0, complete=False, per_user=[])
    any_link = eligible.any(axis=1)
    denied, no_link = any_link & ~contacts, ~any_link
    p.require(np.array_equal(denied | no_link, ~contacts) and not (denied & no_link).any(),
              'unserved-tick partition mismatch')
    changed = contacts ^ original[:steps]
    user_rows, maxima = [], []
    all_gaps = []
    for user in range(p.U):
        gaps = []
        for start, end in _intervals(~contacts[:, user]):
            gaps.append([start, end, int(start == 0), int(end == steps),
                         int(denied[start:end, user].sum()), int(no_link[start:end, user].sum())])
        lengths = [end - start for start, end, *_ in gaps]
        maximum = max(lengths, default=0)
        maxima.append(maximum)
        all_gaps.extend(gaps)
        user_rows.append(dict(user=user, service_count=int(contacts[:, user].sum()),
                              mean_age=float(ages[:, user].mean()), max_gap=maximum,
                              terminal_age=int(ages[-1, user]), changed_grant_ticks=int(changed[:, user].sum()),
                              capacity_denied_ticks=int(denied[:, user].sum()), no_link_ticks=int(no_link[:, user].sum()),
                              gaps=gaps, no_link_intervals=[[start, end, int(start == 0), int(end == steps)]
                                  for start, end in _intervals(no_link[:, user])]))
    ever = contacts.any(axis=0)
    served, quality, rewards = native[:, 0], native[:, 1], native[:, 2]
    means = ages.mean(axis=0)
    sizes = eligible.sum(axis=2)
    zero_intervals = _intervals(served == 0)
    inherited = {key: row[key] for key in p.INHERITED_FIELDS if key in row}
    result = dict(program=row['arm'], law=law, package=f"{row['arm']}:{law}", seed=row['seed'],
        steps=steps, complete=bool(complete), per_user=user_rows, inherited=inherited,
        F_user=float(means.max()), max_user_mean_age=float(means.max()),
        A=float(ages.mean()), age_sum=int(ages.sum(dtype=np.int64)),
        mean_age_square=float(np.square(ages.astype(np.int64)).mean()),
        age_square_sum=int(np.square(ages.astype(np.int64)).sum(dtype=np.int64)),
        F=int(sum(contacts[start:start+64].any(axis=0).sum() for start in range(0, steps, 64))),
        J=float(rewards.mean()), return_sum=float(rewards.sum()), mean_served=float(served.mean()),
        mean_quality=float(quality.mean()), min_served=int(served.min()), service_p10=float(np.quantile(served, .1)),
        zero_service_steps=int((served == 0).sum()), longest_zero_service=max((end-start for start, end in zero_intervals), default=0),
        ever_served=int(ever.sum()), never_served=int((~ever).sum()), max_unserved_gap=max(maxima),
        mean_user_max_unserved_gap=float(np.mean(maxima)), G=float(np.mean(maxima)),
        max_closed_gap=max((g[1]-g[0] for g in all_gaps if not g[2] and not g[3]), default=0),
        max_left_censored_gap=max((g[1]-g[0] for g in all_gaps if g[2]), default=0),
        max_right_censored_gap=max((g[1]-g[0] for g in all_gaps if g[3]), default=0),
        left_censored_gaps=sum(g[2] for g in all_gaps), right_censored_gaps=sum(g[3] for g in all_gaps),
        age_p95=float(np.quantile(ages, .95)), terminal_mean_age=float(ages[-1].mean()), terminal_max_age=int(ages[-1].max()),
        changed_grant_user_ticks=int(changed.sum()), changed_grant_fleet_ticks=int(changed.any(axis=1).sum()),
        changed_grant_uav_ticks=int(changed_uav.sum()), capacity_denied_user_ticks=int(denied.sum()),
        no_link_user_ticks=int(no_link.sum()), capacity_choice_uav_ticks=int((sizes > p.CAPACITY).sum()),
        exact_capacity_uav_ticks=int((sizes == p.CAPACITY).sum()))
    return result


def _float_match(actual, expected, discrepancies, label):
    difference = float(np.max(np.abs(np.asarray(actual, np.float64) - np.asarray(expected, np.float64)), initial=0.))
    discrepancies[label] = max(discrepancies.get(label, 0.), difference)
    p.require(np.isfinite(difference) and difference <= p.ATOL, 'baseline numeric mismatch: ' + label)


def produce_trace(raw, source_row, source, out, counts, radio, *, horizon=p.HORIZON):
    """One trace, including partial evidence on failure; small synthetic H is test-only."""
    out = Path(out)
    name = f"{source_row['arm']}_{source_row['seed']}"
    contact_path, outcome_path = out / 'contacts' / (name + '.npz'), out / 'outcomes' / (name + '.json')
    p.require(not contact_path.exists() and not outcome_path.exists(), 'existing trace output; no retry')
    contacts = np.zeros((3, horizon, p.U), bool)
    ages = np.zeros((3, horizon, p.U), np.int16)
    native = np.zeros((3, horizon, 3))
    eligible_history = np.zeros((horizon, p.N, p.U), bool)
    changed_uav = np.zeros((3, horizon, p.N), bool)
    completed = np.zeros(3, np.int64)
    rr, lrs = [RoundRobin() for _ in range(p.N)], [LeastRecentlyServed() for _ in range(p.N)]
    discrepancies = {}
    timing = dict(allocator_wall_seconds=0., allocator_cpu_seconds=0.)
    failure, rows = None, []
    try:
        _validate_trace(raw, source_row, horizon)
        for tick in range(horizon):
            values = raw['sinr'][tick]
            counts['source_ticks'] += 1
            eligible = values >= p.MIN_SINR
            counts['threshold_scans'] += 1
            counts['threshold_entries'] += p.N * p.U
            eligible_history[tick] = eligible
            p.require(np.all(eligible.sum(axis=0) <= 1), 'non-disjoint eligible user sets')
            active = ((int(raw['mask'][tick]) >> np.arange(p.N)) & 1).astype(bool)
            p.require(np.isfinite(values[active]).all() and np.isneginf(values[~active]).all(),
                      'active/inactive SINR source contract mismatch')
            for law_index, law in enumerate(p.LAWS):
                wall, cpu = time.perf_counter(), time.process_time()
                try:
                    counts['fleet_allocations'] += 1
                    if law == 'ORIGINAL':
                        counts['uav_allocation_decisions'] += p.N
                        counts['original_kernel_calls'] += 1
                        counts['threshold_scans'] += 1
                        counts['threshold_entries'] += p.N * p.U
                        assignment = radio.greedy_connection_assignment(values, min_sinr=p.MIN_SINR, max_connections=p.CAPACITY)
                        p.require(assignment.dtype == bool and assignment.shape == (p.N, p.U)
                                  and np.array_equal(assignment, raw['connections'][tick]), 'original allocation bits mismatch')
                    else:
                        assignment = np.zeros((p.N, p.U), bool)
                        states = rr if law == 'RR' else lrs
                        for member in range(p.N):
                            ids = np.flatnonzero(eligible[member])
                            counts['uav_allocation_decisions'] += 1
                            counts['rr_row_selections' if law == 'RR' else 'lrs_row_selections'] += 1
                            selected = states[member].grant(ids, values[member, ids], tick)
                            assignment[member, selected] = True
                    p.require(not (assignment & ~eligible).any() and np.all(assignment.sum(axis=0) <= 1)
                              and np.array_equal(assignment.sum(axis=1), np.minimum(p.CAPACITY, eligible.sum(axis=1))),
                              'work-conservation/capacity/exclusivity violation')
                finally:
                    timing['allocator_wall_seconds'] += time.perf_counter() - wall
                    timing['allocator_cpu_seconds'] += time.process_time() - cpu
                served = int(assignment.sum())
                quality = float(np.clip((values[assignment] - p.MIN_SINR) / 30., 0., 1.).sum() / max(served, 1))
                reward = .7 * served / p.U + .3 * quality
                contacts[law_index, tick] = assignment.any(axis=0)
                prior = np.zeros(p.U, np.int16) if tick == 0 else ages[law_index, tick-1]
                ages[law_index, tick] = np.where(contacts[law_index, tick], 0, prior + 1)
                native[law_index, tick] = served, quality, reward
                changed_uav[law_index, tick] = (assignment ^ raw['connections'][tick]).any(axis=1)
                completed[law_index] = tick + 1
                counts['transition_reductions'] += 1
                counts['user_age_updates'] += p.U
                if law == 'ORIGINAL':
                    p.require(served == int(raw['served'][tick]), 'baseline served-count mismatch')
                    _float_match(quality, raw['quality'][tick], discrepancies, 'native_quality')
                    _float_match(reward, raw['reward'][tick], discrepancies, 'native_J')
                else:
                    p.require(served == native[0, tick, 0], 'fair allocation changed service count')
                    ceiling_error = max(0., quality - native[0, tick, 1], reward - native[0, tick, 2])
                    discrepancies['quality_ceiling'] = max(discrepancies.get('quality_ceiling', 0.), ceiling_error)
                    p.require(ceiling_error <= p.ATOL, 'quality/J ceiling violation')
        rows = [outcome(contacts[i], ages[i], native[i], eligible_history, changed_uav[i], contacts[0],
                        source_row, law, True) for i, law in enumerate(p.LAWS)]
        p.require(np.array_equal(contacts[0], raw['actual_contacts']) and np.array_equal(ages[0], raw['actual_ages']),
                  'baseline contact/age history mismatch')
        gap_rows = np.array([[u['user'], g[0], g[1], g[1]-g[0], g[2], g[3]]
                            for u in rows[0]['per_user'] for g in u['gaps']], np.int64).reshape(-1, 6)
        p.require(np.array_equal(gap_rows, raw['unserved_gap_rows']), 'baseline gap endpoints/censoring mismatch')
        _float_match([u['mean_age'] for u in rows[0]['per_user']], raw['per_user_mean_age'], discrepancies, 'per_user_mean_age')
        for key in p.OUTCOME_METRICS:
            if key in source_row:
                _float_match(rows[0][key], source_row[key], discrepancies, key)
        counts['source_traces'] += 1
        counts['original_outcomes'] += 1
        counts['fair_outcomes'] += 2
    except Exception as exc:
        failure = exc
        if rows:
            for row in rows:
                row['complete'] = False
        else:
            rows = [outcome(contacts[i, :completed[i]], ages[i, :completed[i]], native[i, :completed[i]],
                            eligible_history[:completed[i]], changed_uav[i, :completed[i]], contacts[0], source_row, law, False)
                    for i, law in enumerate(p.LAWS)]
    # Both fair streams only; unused partial rows are explicitly outside completed_steps.
    with contact_path.open('xb') as stream:
        np.savez_compressed(stream, contacts=contacts[1:], laws=np.array(p.LAWS[1:]),
                            program=np.array(source_row['arm']), seed=np.array(source_row['seed']),
                            completed_steps=completed[1:].copy(), source_sha256=np.array(source['sha256']))
    contact_id = p.file_identity(contact_path, counts)
    details = dict(program=source_row['arm'], seed=source_row['seed'], steps=horizon,
                   complete=failure is None, source=source, contacts=contact_id,
                   completed_by_law=dict(zip(p.LAWS, completed.tolist())), gap_columns=list(p.GAP_COLUMNS),
                   no_link_columns=list(p.NO_LINK_COLUMNS), discrepancies=discrepancies, timing=timing, rows=rows)
    if failure is not None:
        details['error'] = dict(type=type(failure).__name__, message=str(failure))
    p.write_json(outcome_path, details)
    outcome_id = p.file_identity(outcome_path, counts)
    counts['contact_bytes_written'] += contact_id['bytes']
    counts['outcome_bytes_written'] += outcome_id['bytes']
    counts['contact_values_retained'] += int(contacts[1:].size)
    counts['fair_contact_valid_user_ticks'] += int(completed[1:].sum()) * p.U
    compact = []
    for row in rows:
        compact.append({key: value for key, value in row.items() if key != 'per_user'})
        compact[-1].update(per_user_vectors={key: [u[key] for u in row['per_user']] for key in p.VECTOR_FIELDS},
                           source=source, outcome=outcome_id, contacts=contact_id)
    if failure is not None:
        failure.b05_paid_prefix = dict(rows=compact, artifacts=[contact_id, outcome_id], details=details)
        raise failure
    return compact, [contact_id, outcome_id], discrepancies, timing


def describe(values):
    values = np.asarray(values, np.float64)
    p.require(values.ndim == 1 and len(values) and np.isfinite(values).all(), 'invalid paired vector')
    mean = float(values.mean())
    sd = float(values.std(ddof=1)) if len(values) > 1 else 0.
    half = p.T_CRITICAL * sd / np.sqrt(len(values))
    return dict(values=values.tolist(), n=len(values), mean=mean, sd=sd,
                descriptive_t95=[mean-half, mean+half])


def paired_reading(rows, seeds=p.SEEDS):
    by = {(row['package'], row['seed']): row for row in rows}
    p.require(len(by) == len(rows) and set(by) == {(package, seed) for package in p.PACKAGES for seed in seeds}
              and all(row['complete'] for row in rows), 'incomplete nine-package paired panel')
    def value(row, metric):
        return row[metric] if metric in p.OUTCOME_METRICS else row['inherited'][metric]
    levels = {package: {metric: describe([value(by[package, seed], metric) for seed in seeds])
                        for metric in p.METRICS} for package in p.PACKAGES}
    contrasts = {f'{left}-{right}': {metric: describe([value(by[left, seed], metric) - value(by[right, seed], metric)
                  for seed in seeds]) for metric in p.METRICS}
                 for index, left in enumerate(p.PACKAGES) for right in p.PACKAGES[:index]}
    return dict(world_seeds=list(seeds), packages=list(p.PACKAGES), metrics=list(p.METRICS),
                t_critical=p.T_CRITICAL, levels=levels, contrasts=contrasts,
                scope='64 reused world clusters; conditional fixed-path development; no fresh confirmation')


def run_batch(out, launch_sha, summary_path, reading_path, source_root, *, entry_start=None, admission=None):
    started = time.perf_counter() if entry_start is None else entry_start
    cpu_started = time.process_time()
    out = Path(out).resolve()
    p.require(all(Path(value).is_absolute() for value in (summary_path, reading_path, source_root)), 'absolute input paths required')
    if any((out / name).exists() for name in ('config.json', 'summary.json', 'contacts', 'outcomes')):
        raise FileExistsError('existing B05 output; no implicit retry/resume')
    out.mkdir(parents=True, exist_ok=True)
    for name in ('contacts', 'outcomes'):
        (out / name).mkdir()
    counts = counters()
    config = dict(object=p.OBJECT, launch_sha=launch_sha, seeds=list(p.SEEDS), programs=list(p.PROGRAMS),
                  laws=list(p.LAWS), packages=list(p.PACKAGES), horizon=p.HORIZON, nodes=p.N, users=p.U,
                  capacity=p.CAPACITY, min_sinr=p.MIN_SINR, t_critical=p.T_CRITICAL, atol=p.ATOL,
                  b04_source_sha=p.SOURCE_SHA, b04_source_root=str(Path(source_root).resolve()),
                  b04_canonical_run=str(p.B04_CANONICAL_RUN),
                  b04_summary=dict(path=str(Path(summary_path).resolve()), sha256=p.SUMMARY_SHA256),
                  b04_reading=dict(path=str(Path(reading_path).resolve()), sha256=p.READING_SHA256),
                  expected_counts=p.expected_counts(), gap_columns=list(p.GAP_COLUMNS), no_link_columns=list(p.NO_LINK_COLUMNS),
                  source_bindings=[], source_identities=[dict(_input_identity(path, counts), relative_path=str(path.relative_to(ROOT)))
                      for path in sorted(Path(__file__).parent.glob('*.py'))])
    result = dict(object=p.OBJECT, status='RUNNING', scientific_invocation=True, launch_sha=launch_sha,
                  admission=admission, config=config, counts=counts, rows=[], partial_rows=[], artifacts=[], sources=[],
                  discrepancies={}, allocation_timing=dict(allocator_wall_seconds=0., allocator_cpu_seconds=0.),
                  runtime=dict(python=platform.python_version(), numpy=np.__version__, host=platform.node(), platform=platform.platform()))
    p.write_json(out / 'config.json', config)
    try:
        summary_id, reading_id, bindings, by, radio_binding = validate_inputs(summary_path, reading_path, source_root, counts)
        config.update(b04_summary=summary_id, b04_reading=reading_id, source_bindings=bindings)
        p.write_json(out / 'config.json', config)
        radio = load_radio(source_root, radio_binding, counts)
        for seed in p.SEEDS:
            for program in p.PROGRAMS:
                source_row = by[program, seed]
                source = source_row['raw']
                raw = load_trace(source, counts)
                result['sources'].append(source)
                rows, artifacts, discrepancies, timing = produce_trace(raw, source_row, source, out, counts, radio)
                result['rows'].extend(rows)
                result['artifacts'].extend(artifacts)
                for key, value in discrepancies.items():
                    result['discrepancies'][key] = max(result['discrepancies'].get(key, 0.), value)
                for key, value in timing.items():
                    result['allocation_timing'][key] += value
                p.write_json(out / 'summary.json', result)
                print(json.dumps(dict(program=program, seed=seed, complete_source_traces=counts['source_traces'],
                                      complete_outcomes=len(result['rows']))), flush=True)
                del raw
        for key, expected in p.expected_counts().items():
            p.require(counts[key] == expected, 'complete allocation count mismatch: ' + key)
        result['paired'] = paired_reading(result['rows'], p.SEEDS)
        result['status'] = 'COMPLETE'
        result['fixed_policy_evaluation_counts'] = dict(new_physical_episodes=0,
            original_reconstructions=counts['original_outcomes'], fair_outcomes=counts['fair_outcomes'],
            native_transitions=0, allocation_transitions=counts['transition_reductions'], optimizer_updates=0, parameter_updates=0)
    except Exception as exc:
        result['status'] = 'INCOMPLETE_TECHNICAL_FAILURE'
        result['error'] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
        paid = getattr(exc, 'b05_paid_prefix', None)
        if paid is not None:
            result['partial_rows'] = paid['rows']
            result['artifacts'].extend(paid['artifacts'])
            for key, value in paid['details']['timing'].items():
                result['allocation_timing'][key] += value
            for key, value in paid['details']['discrepancies'].items():
                result['discrepancies'][key] = max(result['discrepancies'].get(key, 0.), value)
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        result['resources'] = dict(wall_seconds=time.perf_counter()-started, measured_cpu_seconds=time.process_time()-cpu_started,
            process_user_seconds=usage.ru_utime, process_system_seconds=usage.ru_stime, peak_rss_kib=usage.ru_maxrss,
            rss_scope='Linux process lifetime peak in KiB', scope='entry wall and whole process CPU include imports; replay CPU begins at run_batch',
            live_latency_claim=False)
        p.write_json(out / 'summary.json', result)
    return result
