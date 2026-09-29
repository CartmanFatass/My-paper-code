#!/usr/bin/env python3
"""Complete native reconstruction and proportional B02 candidate verification."""

import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time

for _name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_name] = '1'
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_radio_activation.b01.read import (
    assert_close, observed_rows, radio, verify_episode as verify_retained,
)
from experiments.candidates.uav_radio_activation.b01.protocol import ALL_ON, HORIZON, N, encode_map
from experiments.candidates.uav_radio_activation.b02 import protocol as p
from experiments.candidates.uav_radio_activation.b02.study import (
    ARMS, ARM_ORDERS, SEED, WORLDS, block_positions, episode_metrics,
    file_identity, paired_reading, write_json,
)


def aggregate(values):
    return dict(count=len(values), mean=float(np.mean(values)) if len(values) else None,
                max_abs=float(np.max(np.abs(values))) if len(values) else None)


def choice_from_matrix(scores, current_mask, proposal_q, exhaustive):
    """Independent reading of the frozen comparison and deterministic tie order."""
    requested = []

    def key(pair):
        q, mask = pair
        score = scores[q, mask]
        if not np.isfinite(score).all():
            raise AssertionError('search decision used an uncompleted score')
        return (float(score[0]), float(score[1]), q == proposal_q,
                int(mask).bit_count(), -mask, -q)

    def choose(pairs):
        requested.extend(pairs)
        return sorted(pairs, key=key)[-1]

    first_q, _ = choose([(q, current_mask) for q in range(27)])
    first = choose([(first_q, mask) for mask in range(1, 32)])
    _, first_mask = choose([(proposal_q, mask) for mask in range(1, 32)])
    second = choose([(q, first_mask) for q in range(27)])
    sequential = max((first, second), key=key)
    selected = (max(((q, mask) for q in range(27) for mask in range(1, 32)), key=key)
                if exhaustive else sequential)
    return selected, sequential, list(dict.fromkeys(requested))


def _scores_at(trajectory, sites, mask):
    values = []
    for positions in trajectory:
        _, _, metrics = radio(positions, sites, mask)
        values.append((metrics['J'], metrics['served'], metrics['quality']))
    return np.asarray(values)


def verify_episode(row, raw, *, verify_observations=True):
    arm, steps = row['arm'], int(raw['completed_steps'])
    if steps != row['steps'] or steps != raw['commands'].shape[0]:
        raise AssertionError('incomplete raw cannot support a complete endpoint')
    expected_c = np.ones(steps, dtype=bool) if arm == 'R' else (np.arange(steps) % 4 == 0) & (np.arange(steps) + 4 < steps)
    np.testing.assert_array_equal(raw['c_called'], expected_c)
    np.testing.assert_array_equal(raw['c_decision'], expected_c & (np.arange(steps) % 4 == 0))
    if verify_observations:
        terminal_obs = observed_rows(raw['positions'][-1], raw['true_sites'], int(raw['mask'][-1]), steps)
        terminal_obs[:, -1] = 1.0
        assert_close(raw['observations'][-1], terminal_obs, 1e-6)
    if arm == 'R':
        np.testing.assert_array_equal(raw['commands'], raw['proposals'])
        result = verify_retained(dict(row, arm='E'), raw, verify_observations=verify_observations)
        result['arm'] = 'R'
        result['candidate_physics_scope'] = 'all retained R/B01 mask scores'
        for key, value in episode_metrics(raw, steps, arm).items():
            assert_close(value, row[key], 1e-12)
        return result

    if raw['map_packet'].tobytes() != encode_map(raw['true_sites']):
        raise AssertionError('map binding mismatch')
    rng = np.random.RandomState(row['seed'])
    initial = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)] for _ in range(N)])
    sites = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(50)])
    np.testing.assert_array_equal(initial, raw['positions'][0])
    np.testing.assert_array_equal(sites, raw['true_sites'])
    assert_close(raw['positions'][1:], np.clip(raw['positions'][:-1] + raw['commands'] * 30, p.LOW, p.HIGH), 0)
    controllers = [LocalController(history=False) for _ in range(N)]
    proposals = np.zeros((N, 3))
    pairs = None
    max_j_error = max_sinr_error = max_obs_error = 0.0
    current_mask = ALL_ON
    actual = None
    report_age = []
    origin = None
    rounds = int(raw['round_count'])
    if rounds != steps // 4 - 1:
        raise AssertionError('incorrect proposal exposure')
    for tick in range(steps):
        if int(raw['mask'][tick]) != current_mask:
            raise AssertionError('mask arrived early or was held incorrectly')
        if origin is not None:
            report_age.append(tick - origin)
        if verify_observations:
            expected_obs = observed_rows(raw['positions'][tick], sites, current_mask, tick)
            expected_obs[:, -1] = tick / steps
            assert_close(raw['observations'][tick], expected_obs, 1e-6)
            max_obs_error = max(max_obs_error, float(np.max(np.abs(raw['observations'][tick] - expected_obs))))
        if expected_c[tick]:
            pairs = [controller.act(raw['observations'][tick, i], tick) for i, controller in enumerate(controllers)]
            proposals = np.array([pair[0] for pair in pairs])
        np.testing.assert_array_equal(proposals, raw['proposals'][tick])
        for key in ('fallback', 'selected_index'):
            np.testing.assert_array_equal([pair[1][key] for pair in pairs], raw[key][tick])
        obs = raw['observations'][tick]
        np.testing.assert_array_equal(raw['n_current'][tick], (obs[:, 3:63].reshape(N, 20, 3)[:, :, 2] > 0).sum(axis=1))
        np.testing.assert_array_equal(raw['n_visible_peers'][tick], (obs[:, 63:103].reshape(N, 10, 4)[:, :, 3] > 0).sum(axis=1))
        if tick == 0:
            actual = proposals.copy()
        np.testing.assert_array_equal(actual, raw['commands'][tick])
        sinr, connected, metrics = radio(raw['positions'][tick + 1], sites, current_mask)
        assert_close(raw['sinr'][tick], sinr)
        np.testing.assert_array_equal(raw['connections'][tick], connected)
        assert_close([raw['reward'][tick], raw['served'][tick], raw['quality'][tick]],
                     [metrics['J'], metrics['served'], metrics['quality']], 1e-12)
        max_j_error = max(max_j_error, abs(float(raw['reward'][tick]) - metrics['J']))
        finite = np.isfinite(sinr)
        max_sinr_error = max(max_sinr_error, float(np.max(np.abs(raw['sinr'][tick][finite] - sinr[finite]))))
        if (tick + 1) % 4 == 0 and tick // 4 < rounds:
            index = tick // 4
            current_mask = int(raw['applied_mask'][index])
            actual = raw['commitments'][index]
            if raw['timely'][index]:
                origin = int(raw['round_tick'][index])
    for key, value in row['controller_counts'].items():
        if sum(c.counters[key] for c in controllers) != value:
            raise AssertionError(f'C counter mismatch: {key}')
    np.testing.assert_array_equal(raw['controller_counts'], [row['controller_counts'][str(k)] for k in raw['controller_counter_keys']])

    quantized_sites = p.decode_map(raw['map_packet'].tobytes())
    forecast_errors = {str(i): [] for i in range(5, 9)}
    j_errors = {str(i): [] for i in range(5, 9)}
    shadow_j_gaps, shadow_service_gaps = [], []
    shadow_command_changes = shadow_displacement_changes = silent_coupled_choices = 0
    physics_pairs = 0
    for index in range(rounds):
        tick = 4 * index
        member = index % N
        if raw['round_tick'][index] != tick:
            raise AssertionError('wrong report clock')
        actual = raw['commands'][tick]
        proposal = raw['proposals'][tick]
        proposal_q = p.command_index(proposal[member])
        packets = tuple(x.tobytes() for x in raw['report_packets'][index])
        report_sent = bool(raw['report_packets'][index].any())
        if report_sent:
            if packets != p.encode_reports(raw['observations'][tick, :, :3], actual, proposal, tick):
                raise AssertionError('reports did not encode actual commands and C proposal')
            position, actual_wire, proposed_wire = p.decode_reports(packets, tick)
            prefix_end = block_positions(position, actual_wire)[-1]
            forecast = np.array([block_positions(prefix_end, np.array([
                COMMANDS[q] if i == member else proposed_wire[i] for i in range(N)])) for q in range(27)])
            if np.isfinite(raw['forecast'][index]).any():
                assert_close(raw['forecast'][index], forecast, 0)
        scores = raw['candidate_scores'][index]
        plans = int(raw['candidate_plans'][index])
        order = [tuple(int(v) for v in pair) for pair in raw['candidate_order'][index, :plans]]
        if len(set(order)) != plans or np.count_nonzero(np.isfinite(scores[:, :, 0])) != plans:
            raise AssertionError('candidate score/work identity mismatch')
        if raw['scheduler_wall'][index] + 1e-12 < raw['c_wall'][tick] or raw['scheduler_cpu'][index] + 1e-12 < raw['c_cpu'][tick]:
            raise AssertionError('S/T deadline omitted C proposal work')
        if raw['timely'][index]:
            selected, sequential, sequential_order = choice_from_matrix(scores, int(raw['mask'][tick]), proposal_q, arm == 'T')
            expected_order = [(q, mask) for q in range(27) for mask in range(1, 32)] if arm == 'T' else sequential_order
            if order != expected_order:
                raise AssertionError('search enumeration or both-order baseline changed')
            if raw['state_reductions'][index] != 4 * plans or raw['geometry_snapshots'][index] != 108 or raw['prefix_ticks'][index] != 4:
                raise AssertionError('wrong completed search work or geometry reuse')
            if raw['candidate_requests'][index] != (837 if arm == 'T' else 116):
                raise AssertionError('wrong candidate request count')
            mask, received_member, q = p.decode_command(raw['command_packets'][index].tobytes(), tick)
            if (q, mask) != selected or received_member != member or q != raw['selected_q'][index] or mask != raw['selected_mask'][index]:
                raise AssertionError('matrix selection and command receipt disagree')
            expected_commands = proposal.copy()
            expected_commands[member] = COMMANDS[q]
            np.testing.assert_array_equal(raw['commitments'][index], expected_commands)
            if raw['applied_mask'][index] != mask or raw['round_bytes'][index] != 136 or raw['scheduler_wall'][index] > p.DEADLINE_SECONDS:
                raise AssertionError('late or incorrectly bound commitment')
            if arm == 'T':
                np.testing.assert_array_equal(raw['sequential_pair'][index], sequential)
                assert_close(raw['sequential_score'][index], scores[sequential], 0)
                shadow_j_gaps.append(float(scores[selected][0] - scores[sequential][0]))
                shadow_service_gaps.append(float(scores[selected][1] - scores[sequential][1]))
                shadow_command_changes += int(selected != sequential)
                sequential_commands = proposal.copy()
                sequential_commands[member] = COMMANDS[sequential[0]]
                alternative_path = block_positions(raw['positions'][tick + 4], sequential_commands)
                shadow_displacement_changes += int(np.any(alternative_path[:, member] != raw['positions'][tick + 5:tick + 9, member]))
                silent_coupled_choices += int(not (int(raw['mask'][tick]) & (1 << member))
                    and not (sequential[1] & (1 << member)) and bool(mask & (1 << member))
                    and q != proposal_q and scores[selected][0] > scores[sequential][0])
            # Selected/proposal/current/round-index sentinel is fixed before outcome exposure.
            subset = {(proposal_q, 31), (proposal_q, int(raw['mask'][tick])), selected,
                      sequential, (index % 27, 1 + index % 31)}
            for check_q, check_mask in sorted(subset):
                if np.isfinite(scores[check_q, check_mask]).all():
                    values = _scores_at(forecast[check_q], quantized_sites, check_mask)
                    assert_close(scores[check_q, check_mask], values.mean(axis=0), 1e-12)
                    physics_pairs += 1
            selected_states = _scores_at(forecast[q], quantized_sites, mask)
            for slot, offset in enumerate(range(5, 9)):
                forecast_errors[str(offset)].extend(np.linalg.norm(forecast[q, slot] - raw['positions'][tick + offset], axis=-1).tolist())
                j_errors[str(offset)].append(float(raw['reward'][tick + offset - 1] - selected_states[slot, 0]))
        else:
            if raw['selected_q'][index] != -1 or raw['selected_mask'][index] != -1 or raw['command_packets'][index].any():
                raise AssertionError('late result kept a winner or command')
            if raw['applied_mask'][index] != raw['mask'][tick]:
                raise AssertionError('late result changed mask')
            np.testing.assert_array_equal(raw['commitments'][index], actual)
            if raw['round_bytes'][index] != (120 if report_sent else 0):
                raise AssertionError('wrong late-round traffic')
    for key, value in episode_metrics(raw, steps, arm).items():
        assert_close(value, row[key], 1e-12)
    return dict(arm=arm, seed=row['seed'], verified_steps=steps,
                max_native_J_error=max_j_error, max_native_sinr_error=max_sinr_error,
                max_observation_error=max_obs_error, candidate_physics_pairs=physics_pairs,
                candidate_physics_scope='predeclared subset; full matrix selection and full native endpoint',
                forecast_position_error_m={key: aggregate(values) for key, values in forecast_errors.items()},
                actual_minus_predicted_J={key: aggregate(values) for key, values in j_errors.items()},
                report_age_ticks=aggregate(report_age), T_same_input_J_minus_S=aggregate(shadow_j_gaps),
                T_same_input_service_minus_S=aggregate(shadow_service_gaps),
                T_same_input_pair_changes=shadow_command_changes,
                T_same_input_executed_displacement_changes=shadow_displacement_changes,
                T_silent_move_reactivate_strict_advantages=silent_coupled_choices)


def read_result(out):
    started, cpu_started = time.perf_counter(), time.process_time()
    out = Path(out)
    summary = json.loads((out / 'summary.json').read_text())
    if summary['status'] != 'COMPLETE' or not summary['scientific_invocation']:
        raise ValueError('no complete fixed scientific panel to interpret')
    seeds = list(range(SEED, SEED + WORLDS))
    if summary['config']['seeds'] != seeds or summary['config']['horizon'] != HORIZON or summary['config']['arms'] != list(ARMS):
        raise AssertionError('changed panel')
    expected = dict(constructors=1, explicit_resets=192, native_step_calls=49152,
                    team_steps=49152, complete_episodes=192, fit_started=0, optimizer_steps=0)
    if summary['counts'] != expected:
        raise AssertionError('wrong scientific exposure')
    if json.loads((out / 'config.json').read_text()) != summary['config']:
        raise AssertionError('config differs from summary')
    if sorted(summary['artifacts'], key=lambda item: item['path']) != sorted([row['raw'] for row in summary['rows']], key=lambda item: item['path']):
        raise AssertionError('raw manifest differs from complete rows')
    expected_order = [(arm, seed) for i, seed in enumerate(seeds) for arm in ARM_ORDERS[i % 6]]
    if [(r['arm'], r['seed']) for r in summary['rows']] != expected_order:
        raise AssertionError('wrong interleaving or completeness')
    if json.loads((out / 'process-exit.json').read_text())['exit_code'] != 0:
        raise AssertionError('native process did not exit successfully')
    rows, worlds = [], {}
    total_bytes = 0
    for row in summary['rows']:
        path = Path(row['raw']['path'])
        identity = file_identity(path)
        if identity != row['raw']:
            raise AssertionError('raw identity mismatch')
        total_bytes += identity['bytes']
        with np.load(path, allow_pickle=False) as raw:
            world = (raw['true_sites'], raw['positions'][0])
            if row['seed'] in worlds:
                for left, right in zip(world, worlds[row['seed']]):
                    np.testing.assert_array_equal(left, right)
            else:
                worlds[row['seed']] = tuple(x.copy() for x in world)
            rows.append(verify_episode(row, raw))
        print(json.dumps(dict(verified=len(rows), arm=row['arm'], seed=row['seed'])), flush=True)
    paired = paired_reading(summary['rows'], seeds)
    if paired != summary['paired']:
        raise AssertionError('paired reading differs from summary')
    result = dict(status='VERIFIED_COMPLETE', launch_sha=summary['launch_sha'],
                  summary_sha256=file_identity(out / 'summary.json')['sha256'],
                  verified_raw_files=len(rows), verified_raw_bytes=total_bytes, rows=rows, paired=paired,
                  scope='all native endpoints/C/commitments; selected fixed candidate subset; zero new environment steps/fits',
                  wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu_started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(out / 'reading.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    read_result(parser.parse_args().out)
