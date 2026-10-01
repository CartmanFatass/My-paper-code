"""Exactly one acquisition, two fixed ridge fits and the complete final panel."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import load_parent
from .audit import audit_pair
from .collect import collect_episode
from .contract import FITTED, FROZEN, HELPER_PARENTS, NEURAL, OBJECT, array_digest, source_identities
from .environment import check_host, make_real
from .fit import fit_ridge
from .reading import comparisons

ROOT = Path(__file__).resolve().parents[4]


def artifact(path, root):
    result = file_identity(path)
    result['path'] = str(Path(path).relative_to(root))
    return result


def load_raw(path):
    with np.load(path, allow_pickle=False) as saved:
        return {key: saved[key] for key in saved.files}


def costs(rows, counts, inflight=None):
    helper = sum_counts(row['policy_counts'] for row in rows if row['parent'] in HELPER_PARENTS)
    full_c = sum_counts(row['policy_counts'] for row in rows if row['parent'] not in HELPER_PARENTS)
    if inflight and inflight.get('policy_agents'):
        pending = sum_counts(inflight['policy_agents'])
        if inflight['parent'] in HELPER_PARENTS:
            helper = sum_counts((helper, pending))
        else:
            full_c = sum_counts((full_c, pending))
    all_policy = sum_counts((helper, full_c))
    links = sum(all_policy.get(key, 0) for key in ('candidate_links', 'setup_links', 'helper_setup_links', 'helper_extreme_links'))
    return dict(helper_programs=helper, C_family_programs=full_c, all_policy=all_policy,
                neural_forward_rows=all_policy.get('neural_rows', 0), controller_power_links=links,
                native_dense_power_slots=counts.get('native_dense_power_slots', 0),
                native_unique_distance_pairs=counts.get('native_unique_distance_pairs', 0),
                mask_refresh_dense_sinr_slots=counts.get('mask_refresh_dense_sinr_slots', 0),
                modeled_power_slots_including_native=links + counts.get('native_dense_power_slots', 0),
                scope='Actual cached policy work. Native dense power slots include one constructor reset, explicit resets '
                      'and native steps; mask refresh reuses distances/power and has separate SINR slots. '
                      'Hdirect includes full MemoC and both T/H vectors on every law call.')


def validate_counts(actual, cost, protocol):
    expected = protocol.expected()
    exact = ('optimizer_steps', 'motion_updates', 'paired_targets', 'acquisition_episodes', 'evaluation_episodes',
             'complete_episodes', 'acquisition_native_steps', 'evaluation_native_steps', 'native_steps', 'native_uav_ticks',
             'explicit_resets', 'constructor_resets', 'native_dense_power_slots', 'mask_installs',
             'mask_refresh_dense_sinr_slots', 'motion_requests', 'gate_opportunities', 'motion_draws', 'gate_draws')
    for key in exact:
        if type(actual.get(key)) is not int or actual[key] != expected[key]:
            raise AssertionError('complete B08 exposure changed: ' + key)
    if actual['fits_started'] != 2 or actual['fits_completed'] != 2:
        raise AssertionError('exactly two fits required')
    for first, second in (('explicit_reset_calls', 'explicit_resets'), ('native_step_calls', 'native_steps'),
                          ('motion_request_calls', 'motion_requests'), ('gate_opportunity_calls', 'gate_opportunities'),
                          ('mask_install_calls', 'mask_installs'), ('constructor_calls', 'constructor_resets')):
        if actual[first] != actual[second]:
            raise AssertionError('incomplete counted call: ' + first)
    if (actual['forced_gate_decisions'] != 2 * len(protocol.training_worlds)
            or actual['native_unique_distance_pairs'] != 260 * (expected['native_steps'] + expected['explicit_resets'] + 1)
            or cost['helper_programs']['requests'] != expected['standalone_helper_requests']
            or cost['C_family_programs']['requests'] != expected['C_family_requests']
            or cost['all_policy']['sampled_draws'] != expected['motion_draws']
            or cost['all_policy']['law_evaluations'] != expected['motion_requests']
            or cost['all_policy']['target_vectors'] != expected['Hdirect_target_vectors']
            or cost['all_policy']['score_tail_evaluations'] != expected['G_score_tail_calls']):
        raise AssertionError('policy/mask/label exact work changed')
    for actual_value, ceiling in ((cost['neural_forward_rows'], 'neural_forward_ceiling'),
                                  (cost['C_family_programs']['trajectories'], 'C_path_ceiling'),
                                  (cost['C_family_programs']['model_ticks'], 'C_model_tick_ceiling')):
        if not 0 <= actual_value <= expected[ceiling]:
            raise AssertionError('memoized work exceeds declared ceiling: ' + ceiling)
    for group, ceiling in (('helper_programs', 'helper_link_ceiling'), ('C_family_programs', 'C_link_ceiling')):
        links = sum(cost[group][key] for key in ('candidate_links', 'setup_links', 'helper_setup_links', 'helper_extreme_links'))
        if links > expected[ceiling]:
            raise AssertionError('modeled links exceed declared ceiling: ' + group)


def _execute(out, actor, env, protocol, batch, publish):
    """Lower-level integration permits explicit small, synthetic correctness fixtures."""
    protocol.validate()
    counts, inflight = batch['actual'], batch['inflight']
    actor_sha = state_digest(actor.state_dict())
    features = {name: [] for name in FITTED}
    targets, pairs = [], []
    with (out / 'episodes.jsonl').open('x', encoding='utf-8') as stream:
        def save_row(row):
            batch['rows'].append(row)
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + '\n')
            stream.flush()

        for wi, world in enumerate(protocol.training_worlds):
            branch_rows, branch_features = {}, {}
            for branch in protocol.branches(wi):
                row, f = collect_episode(env, program='P0_R', world=world, tape=None, actor=actor, out=out,
                                         protocol=protocol, counts=counts, inflight=inflight, policy_sha=actor_sha,
                                         kind='acquisition', branch=branch, force_tick=protocol.force_tick(wi))
                save_row(row)
                branch_rows[branch], branch_features[branch] = row, f
                batch['progress'] = dict(kind='acquisition', world=world, branch=branch, pairs=wi)
                publish()
            off, on = (load_raw(out / branch_rows[branch]['raw']['path']) for branch in ('OFF', 'ON'))
            x, y = audit_pair(off, on, branch_rows['OFF'], branch_rows['ON'], protocol,
                              branch_features['OFF'], branch_features['ON'])
            for name in FITTED:
                features[name].append(x[name])
            targets.append(y)
            pairs.append(dict(world=world, force_tick=protocol.force_tick(wi),
                              OFF=branch_rows['OFF']['id'], ON=branch_rows['ON']['id'],
                              J_OFF=branch_rows['OFF']['J'], J_ON=branch_rows['ON']['J'], target=y,
                              RAW_sha256=array_digest(x['RAW']), HIDDEN_sha256=array_digest(x['HIDDEN'])))
            counts['paired_targets'] += 1
            batch['pairs'] = pairs
            if (wi + 1) % 16 == 0:
                publish(full=True)
        dataset = dict(RAW=np.asarray(features['RAW'], dtype=np.float64), HIDDEN=np.asarray(features['HIDDEN'], dtype=np.float64),
                       targets=np.asarray(targets, dtype=np.float64), worlds=np.asarray(protocol.training_worlds, dtype=np.int64),
                       force_ticks=np.asarray([protocol.force_tick(i) for i in range(len(targets))], dtype=np.int64))
        path = out / 'data' / 'acquisition.npz'
        np.savez_compressed(path, **dataset)
        batch['dataset'] = artifact(path, out)
        batch['label_diagnostics'] = dict(rows=len(targets), positive=int(np.count_nonzero(dataset['targets'] > 0)),
                                        negative=int(np.count_nonzero(dataset['targets'] < 0)), zero=int(np.count_nonzero(dataset['targets'] == 0)),
                                        mean=float(dataset['targets'].mean()), sd=float(dataset['targets'].std()),
                                        min=float(dataset['targets'].min()), max=float(dataset['targets'].max()))
        gates = {}
        for name in FITTED:
            wall, cpu = time.perf_counter(), time.process_time()
            counts['fits_started'] += 1
            batch['progress'] = dict(kind='fit', gate=name)
            publish(full=True)
            params, diagnostics = fit_ridge(dataset[name], dataset['targets'], name=name)
            counts['fits_completed'] += 1
            path = out / 'assets' / (name + '.npz')
            np.savez_compressed(path, **params)
            diagnostics.update(artifact=artifact(path, out), feature_sha256=array_digest(dataset[name]),
                               target_sha256=array_digest(dataset['targets']),
                               movement_from_zero_coefficients=float(np.linalg.norm(params['coefficients'])),
                               intercept_from_zero=float(params['intercept']),
                               nonzero_coefficients=int(np.count_nonzero(params['coefficients'])),
                               wall_seconds=time.perf_counter() - wall, cpu_seconds=time.process_time() - cpu,
                               timing_scope='training-only scaler, one FP64 solve, stationarity diagnostics and artifact serialization')
            batch['fits'].append(diagnostics)
            gates[name] = params
            publish(full=True)
        for wi, world in enumerate(protocol.worlds):
            for program, tape in protocol.episode_order(wi):
                parent, gate = program.split('_', 1)
                row, _ = collect_episode(env, program=program, world=world, tape=tape, actor=actor if parent in NEURAL else None,
                                         out=out, protocol=protocol, counts=counts, inflight=inflight,
                                         policy_sha=actor_sha if parent in NEURAL else None, gate_params=gates.get(gate))
                save_row(row)
                batch['progress'] = dict(kind='evaluation', program=program, world=world, tape=tape)
                publish()
            publish(full=True)
    batch['episode_log'] = artifact(out / 'episodes.jsonl', out)
    if state_digest(actor.state_dict()) != actor_sha:
        raise AssertionError('frozen P0 parameters changed')
    batch['final_parent_state_sha256'] = actor_sha
    batch['costs'] = costs(batch['rows'], counts)
    validate_counts(counts, batch['costs'], protocol)
    batch['comparisons'] = comparisons(batch['rows'], protocol)


def run_batch(out, launch_sha, *, admission, parent_path, entry_start=None, entry_cpu=None):
    if not admission or admission.get('sha') != launch_sha:
        raise ValueError('production requires its accepted exact source')
    protocol = FROZEN
    wall = time.perf_counter() if entry_start is None else entry_start
    cpu = time.process_time() if entry_cpu is None else entry_cpu
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {'launch-status.json', 'launch-manifest.json', 'admission-preflight.json', 'stdout.log', 'stderr.log'}
    if any(path.name not in allowed for path in out.iterdir()):
        raise FileExistsError('scientific output exists; reconcile accepted operation')
    for name in ('raw', 'data', 'assets'):
        (out / name).mkdir()
    counts = {key: 0 for key in ('optimizer_steps', 'motion_updates', 'paired_targets', 'fits_started', 'fits_completed',
                                 'constructor_calls', 'constructor_resets', 'native_dense_power_slots', 'native_unique_distance_pairs')}
    batch = dict(object=OBJECT, state='INCOMPLETE', scientific_execution=True, launch_sha=launch_sha,
                 admission=dict(admission), protocol=protocol.to_dict(), expected=protocol.expected(), actual=counts,
                 start_utc=datetime.now(timezone.utc).isoformat(), rows=[], pairs=[], fits=[], inflight={}, sources={},
                 runtime=dict(python=platform.python_version(), compiler=platform.python_compiler(), numpy=np.__version__,
                              torch=torch.__version__, host=platform.node(), device='cpu', torch_threads=torch.get_num_threads(),
                              torch_interop_threads=torch.get_num_interop_threads(), deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
                              thread_environment={key: os.environ.get(key) for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')}),
                 timing_scope='Runner entry through all worker acquisition, fits, final episodes and summaries; reader follows sequentially. '
                              'Staging, admission and support separate; final summary write is outside its own timestamp.')
    env = None

    def publish(full=False):
        batch.update(worker_wall_seconds=time.perf_counter() - wall, worker_cpu_seconds=time.process_time() - cpu,
                     worker_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        if full:
            write_json(out / 'summary.json', batch)
        write_json(out / 'progress.json', {key: batch.get(key) for key in ('state', 'actual', 'progress', 'worker_wall_seconds', 'worker_cpu_seconds')})

    try:
        batch['sources'] = source_identities(ROOT)
        actor, batch['parent'] = load_parent(parent_path)
        batch['initial_parent_state_sha256'] = state_digest(actor.state_dict())
        write_json(out / 'config.json', {key: batch[key] for key in
                   ('object', 'scientific_execution', 'launch_sha', 'protocol', 'expected', 'sources', 'runtime', 'parent')})
        publish(full=True)
        counts['constructor_calls'] += 1
        env = make_real(protocol.constructor_seed)
        counts['constructor_resets'] += 1
        counts['native_dense_power_slots'] += 275
        counts['native_unique_distance_pairs'] += int(env.env._path_loss_cache_misses)
        batch['host'] = check_host(env)
        _execute(out, actor, env, protocol, batch, publish)
        if file_identity(parent_path)['sha256'] != batch['parent']['sha256']:
            raise AssertionError('consumed P0 artifact changed')
        batch.update(state='COMPLETE', finish_utc=datetime.now(timezone.utc).isoformat())
    except BaseException:
        batch.update(state='FAILED', failure=traceback.format_exc(), finish_utc=datetime.now(timezone.utc).isoformat(),
                     interrupted_call_work_may_be_unmeasured=True)
        batch['costs'] = costs(batch['rows'], counts, batch['inflight'])
        raise
    finally:
        if env is not None:
            env.close()
        publish(full=True)
    return batch
