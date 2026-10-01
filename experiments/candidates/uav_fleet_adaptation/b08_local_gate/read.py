"""Complete scalar/policy/label/fit reading, with no native steps or refits."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    __package__ = 'experiments.candidates.uav_fleet_adaptation.b08_local_gate'
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[name] = '1'

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import checked_path, load_parent
from .audit import audit_episode, audit_pair, equal, require
from .contract import FITTED, FROZEN, HELPER_PARENTS, NEURAL, OBJECT, array_digest, source_identities
from .fit import audit_ridge
from .reading import comparisons
from .study import costs, load_raw, validate_counts


def _read_all(batch, out, actor, protocol, report, progress):
    """One streaming pass. Explicit synthetic fixtures can exercise this core."""
    counts = report['actual']
    rows = batch['rows']
    expected = [('acquisition', 'P0_R', world, None, branch, protocol.force_tick(wi))
                for wi, world in enumerate(protocol.training_worlds) for branch in protocol.branches(wi)]
    expected += [('evaluation', program, world, tape, None, None)
                 for wi, world in enumerate(protocol.worlds) for program, tape in protocol.episode_order(wi)]
    require([(row['kind'], row['program'], row['world'], row['tape'], row['branch'], row['force_tick'])
             for row in rows] == expected, 'exact execution order and population')
    policy_sha = state_digest(actor.state_dict())
    require(batch['initial_parent_state_sha256'] == policy_sha == batch['final_parent_state_sha256'], 'frozen parent identity')
    episode_log = checked_path(out, batch['episode_log']['path'], batch['episode_log'])
    with episode_log.open(encoding='utf-8') as stream:
        logged = [json.loads(line) for line in stream]
    require(logged == rows, 'complete durable episode log')
    dataset = load_raw(checked_path(out, batch['dataset']['path'], batch['dataset']))
    require(set(dataset) == {'RAW', 'HIDDEN', 'targets', 'worlds', 'force_ticks'}, 'one common complete dataset')
    n = len(protocol.training_worlds)
    equal(dataset['worlds'], np.asarray(protocol.training_worlds, dtype=np.int64), 'ascending training worlds')
    equal(dataset['force_ticks'], [protocol.force_tick(i) for i in range(n)], 'balanced force clocks')
    for name, width in (('RAW', 125), ('HIDDEN', 253)):
        require(dataset[name].shape == (n, width) and dataset[name].dtype == np.float64
                and np.isfinite(dataset[name]).all(), 'finite complete ' + name + ' dataset')
    require(dataset['targets'].shape == (n,) and dataset['targets'].dtype == np.float64
            and np.isfinite(dataset['targets']).all(), 'all paid targets retained')
    equal(dataset['HIDDEN'][:, :125], dataset['RAW'], 'identical RAW information in HIDDEN')
    y = dataset['targets']
    label_diagnostics = dict(rows=n, positive=int(np.count_nonzero(y > 0)), negative=int(np.count_nonzero(y < 0)),
                             zero=int(np.count_nonzero(y == 0)), mean=float(y.mean()), sd=float(y.std()),
                             min=float(y.min()), max=float(y.max()))
    require(batch['label_diagnostics'] == label_diagnostics, 'all target signs and zeros retained')
    require([fit['name'] for fit in batch['fits']] == list(FITTED), 'exact two fit order')
    gates = {}
    for fit in batch['fits']:
        name = fit['name']
        params = load_raw(checked_path(out, fit['artifact']['path'], fit['artifact']))
        require(fit['feature_sha256'] == array_digest(dataset[name])
                and fit['target_sha256'] == array_digest(dataset['targets']), 'fit uses common acquisition only')
        audit = audit_ridge(dataset[name], dataset['targets'], params)
        for key, value in audit.items():
            if isinstance(value, (float, list)):
                equal(fit[key], value, 'fit complete diagnostics ' + key, tolerance=1e-12)
            else:
                require(fit[key] == value, 'fit complete diagnostics ' + key)
        equal(fit['movement_from_zero_coefficients'], np.linalg.norm(params['coefficients']), 'ridge coefficient movement')
        equal(fit['intercept_from_zero'], params['intercept'], 'ridge intercept movement')
        equal(fit['nonzero_coefficients'], np.count_nonzero(params['coefficients']), 'ridge changed coefficients')
        require(fit['fits'] == 1 and fit['optimizer_steps'] == 0 and fit['refits'] == 0, 'one solve per fixed gate')
        gates[name] = params
        report['fit_audits'][name] = audit
    branch_data = {}
    reconstructed_policies, pair_records = [], []
    max_errors = dict(radio=0., observation=0., reward=0., prediction=0.)
    for i, row in enumerate(rows):
        parent, gate = row['program'].split('_', 1)
        require(row['parent'] == parent and row['gate'] == gate, 'program/parent/gate metadata')
        require(row['policy_sha256'] == (policy_sha if parent in NEURAL else None), 'per-episode policy source')
        if row['kind'] == 'acquisition':
            motion_root, gate_root = protocol.training_motion_root, protocol.training_gate_root
            identifier = f"acquisition_w{row['world']}_{row['branch']}"
        else:
            motion_root = None if parent == 'C' else protocol.evaluation_motion_roots[row['tape']]
            gate_root = protocol.evaluation_gate_roots[row['tape']] if gate == 'R' else None
            identifier = f"evaluation_{row['program']}_w{row['world']}_t{row['tape']}"
        require(row['motion_root'] == motion_root and row['gate_root'] == gate_root
                and row['id'] == identifier and row['raw']['path'] == 'raw/' + identifier + '.npz', 'private domains/raw identity')
        raw = load_raw(checked_path(out, row['raw']['path'], row['raw']))
        equal(raw['initial_generation'], 2 + i * (protocol.horizon + 1), 'one reused environment and reset per episode')
        record, features = audit_episode(raw, row, protocol, actor if parent in NEURAL else None,
                                         params=gates.get(gate), counts=counts, inflight=report['inflight'])
        reconstructed_policies.append(dict(parent=parent, policy_counts=record['policy_counts']))
        # Preserve the completed episode's paid replay before a subsequent
        # pair/label assertion can fail. audit_episode has cleared inflight.
        report['policy_costs'] = costs(reconstructed_policies, {})
        for key, value in record['max_abs_errors'].items():
            max_errors[key] = max(max_errors[key], value)
        if row['kind'] == 'acquisition':
            branch_data[row['branch']] = (raw, row, features)
            if len(branch_data) == 2:
                off, off_row, f_off = branch_data['OFF']
                on, on_row, f_on = branch_data['ON']
                x, y = audit_pair(off, on, off_row, on_row, protocol, f_off, f_on)
                index = len(pair_records)
                equal(dataset['targets'][index], y, 'saved full native label')
                for name in FITTED:
                    equal(dataset[name][index], x[name], 'saved common pre-force feature ' + name)
                pair = dict(world=row['world'], force_tick=off_row['force_tick'], OFF=off_row['id'], ON=on_row['id'],
                            J_OFF=off_row['J'], J_ON=on_row['J'], target=y,
                            RAW_sha256=array_digest(x['RAW']), HIDDEN_sha256=array_digest(x['HIDDEN']))
                require(batch['pairs'][index] == pair, 'complete pair ledger')
                pair_records.append(pair)
                counts['paired_labels'] = len(pair_records)
                branch_data.clear()
        report['max_abs_errors'] = max_errors
        progress(dict(kind='complete_scalar_policy_episode', id=row['id'], completed=i + 1, total=len(rows)))
    require(len(pair_records) == n and not branch_data, 'all paired labels read')
    require(report['policy_costs']['all_policy'] == batch['costs']['all_policy'], 'complete actual replay policy counts')
    require(batch['costs'] == costs(rows, batch['actual']), 'worker cost reduction')
    validate_counts(batch['actual'], batch['costs'], protocol)
    result = comparisons(rows, protocol)
    require(result == batch['comparisons'], 'complete 16-level/37-contrast statistics and signed adverse worlds')
    expected_cost = protocol.expected()
    require(counts['saved_episodes'] == expected_cost['complete_episodes']
            and counts['saved_native_ticks'] == expected_cost['native_steps']
            and counts['scalar_states'] == expected_cost['native_steps'] + expected_cost['mask_installs'] + expected_cost['explicit_resets']
            and counts['policy_requests'] == expected_cost['motion_requests']
            and counts['gate_requests'] == expected_cost['gate_opportunities']
            and counts['native_steps'] == counts['optimizer_steps'] == counts['refits'] == 0, 'complete reader exposure')
    report.update(comparisons_verified=dict(levels=len(result['levels']), contrasts=len(result['contrasts']),
                                           worlds=len(protocol.worlds), bootstrap=result['bootstrap']),
                  dataset_targets_sha256=array_digest(dataset['targets']),
                  native_sinr_tolerance=1e-10, observation_absolute_tolerance=1e-7, reward_absolute_tolerance=2e-13,
                  tolerance_scope='Scalar versus vector FP64 rounding and FP32 observation rounding only; discrete assignments, '
                                  'threshold eligibility, sampled categories, navigation, masks and gates match exactly.')
    return result


def _publication(batch, reading, out):
    metrics = ('J', 'mean_served', 'mean_sinr_quality', 'service_p10', 'min_served', 'zero_service_steps',
               'zero_service_episode', 'longest_zero_service_streak', 'active_transmitter_fraction', 'off_fraction')
    comp = batch['comparisons']
    return dict(object=OBJECT, state='COMPLETE_READ', launch_sha=batch['launch_sha'],
                evidence={name: file_identity(out / name) for name in ('summary.json', 'reading.json', 'config.json', 'episodes.jsonl')},
                actual=batch['actual'], costs=batch['costs'], reader_actual=reading['actual'],
                label_diagnostics=batch['label_diagnostics'], uncertainty=comp['uncertainty'],
                worlds=comp['worlds'],
                levels={program: {metric: values[metric] for metric in metrics} for program, values in comp['levels'].items()},
                contrasts={program: {metric: values[metric] for metric in metrics} for program, values in comp['contrasts'].items()},
                adverses=comp['adverses'],
                resources=dict(worker_wall_seconds=batch['worker_wall_seconds'], worker_cpu_seconds=batch['worker_cpu_seconds'],
                               worker_process_high_water_rss_kib=batch['worker_max_rss_kib'],
                               reader_wall_seconds=reading['wall_seconds'], reader_cpu_seconds=reading['cpu_seconds'],
                               chain_process_high_water_rss_kib=reading['process_high_water_rss_kib'],
                               scope='Single sequential worker/reader process. High-water RSS includes earlier worker allocations; '
                                     'not independent reader peak or physical deployment latency.'))


def read_result(out, repo):
    wall, cpu = time.perf_counter(), time.process_time()
    out, repo = Path(out).resolve(), Path(repo).resolve()
    # A process exit or observer loss never authorizes a duplicate replay.
    with (out / 'reader-start.json').open('x', encoding='utf-8') as stream:
        json.dump(dict(pid=os.getpid(), start_utc=datetime.now(timezone.utc).isoformat()), stream)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    report = dict(object=OBJECT, status='INCOMPLETE', actual=dict(native_steps=0, optimizer_steps=0, refits=0),
                  fit_audits={}, inflight={}, policy_costs={},
                  scope='One full scalar saved-state and original policy replay; every acquired pair and both fixed ridge normal equations; '
                        'no environment construction, native step, new label, fit or gradient optimizer update.')

    def progress(value=None):
        if value is not None:
            report['progress'] = value
        report.update(wall_seconds=time.perf_counter() - wall, cpu_seconds=time.process_time() - cpu,
                      process_high_water_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        write_json(out / 'reading-progress.json', {key: report.get(key) for key in
                                                  ('status', 'actual', 'progress', 'wall_seconds', 'cpu_seconds')})

    try:
        batch = json.loads((out / 'summary.json').read_text())
        require(batch['state'] == 'COMPLETE' and batch['object'] == OBJECT
                and batch['scientific_execution'] is True and batch['protocol'] == FROZEN.to_dict(), 'fixed complete production result')
        require(batch['admission']['sha'] == batch['launch_sha'], 'accepted input source identity')
        require(batch['sources'] == source_identities(repo), 'worker and reader exact executable identities')
        config = json.loads((out / 'config.json').read_text())
        config_keys = ('object', 'scientific_execution', 'launch_sha', 'protocol', 'expected', 'sources', 'runtime', 'parent')
        require(config == {key: batch[key] for key in config_keys}, 'frozen complete configuration')
        actor, parent = load_parent(batch['parent']['path'])
        require(parent == batch['parent'], 'exact original consumed P0')
        report['summary'] = file_identity(out / 'summary.json')
        _read_all(batch, out, actor, FROZEN, report, progress)
        require(state_digest(actor.state_dict()) == parent['state_sha256'], 'reader did not mutate parent')
        report.update(status='VERIFIED', finish_utc=datetime.now(timezone.utc).isoformat())
    except BaseException:
        report.update(status='FAILED', failure=traceback.format_exc(), interrupted_call_work_may_be_unmeasured=True)
        if report['inflight'].get('policy_agents'):
            report['interrupted_episode_policy_counts'] = sum_counts(report['inflight']['policy_agents'])
        raise
    finally:
        progress()
        write_json(out / 'reading.json', report)
    write_json(out / 'publication.json', _publication(batch, report, out))
    return report


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--launch-sha', required=True)
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args(argv)
    if args.seed != 29832000:
        parser.error('B08 complete reader has one fixed population')
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction='uav_fleet_adaptation')
    if admission['sha'] != args.launch_sha:
        raise RuntimeError('reader source differs from accepted admission')
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    return read_result(args.out, ROOT)


if __name__ == '__main__':
    if main()['status'] != 'VERIFIED':
        raise SystemExit(1)
