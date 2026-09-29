#!/usr/bin/env python3
"""Offline reconstruction of all native and scheduler evidence; no environment steps."""

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

from envs.pettingzoo.uav_radio import (
    free_space_user_path_loss, greedy_connection_assignment, service_metrics,
    user_sinr_from_path_loss,
)
from experiments.candidates.uav_local_history.b01.controller import LocalController
from experiments.candidates.uav_radio_activation.b01.protocol import (
    ALL_ON, HORIZON, HIGH, LOW, N, SEED, WORLDS, decode_command, decode_map,
    decode_reports, encode_map, encode_reports, forecast_positions, mask_array,
)
from experiments.candidates.uav_radio_activation.b01.scheduler import rank
from experiments.candidates.uav_radio_activation.b01.study import (
    ARM_ORDERS, episode_metrics, file_identity, paired_reading, write_json,
)


def assert_close(actual, expected, tolerance=1e-9):
    np.testing.assert_allclose(actual, expected, atol=tolerance, rtol=0)


def radio(positions, sites, mask):
    loss = free_space_user_path_loss(positions, sites)
    sinr = user_sinr_from_path_loss(loss, transmitter_mask=mask_array(int(mask)))
    connections = greedy_connection_assignment(sinr)
    return sinr, connections, service_metrics(sinr, connections)


def observed_rows(positions, sites, mask, tick):
    """Independent scalar A2A arithmetic and observation assembly for this fixed host."""
    active = mask_array(int(mask))
    user_sinr, _, _ = radio(positions, sites, mask)
    rows = np.zeros((N, 104), dtype=np.float32)
    own = positions / (1000, 1000, 100)
    own[:, 2] -= .5
    rows[:, :3] = own
    for i in range(N):
        eligible = sorted((j for j in range(50) if user_sinr[i, j] >= 3),
                          key=lambda j: -user_sinr[i, j])[:20]
        for slot, j in enumerate(eligible):
            rows[i, 3 + 3 * slot:6 + 3 * slot] = (
                *(sites[j] - positions[i, :2]) / 1000,
                np.clip((user_sinr[i, j] + 10) / 50, 0, 1))
        peers = []
        if active[i]:
            for j in range(N):
                if i == j or not active[j]:
                    continue
                distance = max(float(np.linalg.norm(positions[i] - positions[j])), 1e-6)
                rx = 23 - (20 * np.log10(distance) + 20 * np.log10(4 * np.pi / .15))
                interfering = []
                for k in range(N):
                    if k != i and k != j and active[k]:
                        d = max(float(np.linalg.norm(positions[k] - positions[j])), 1e-6)
                        loss = 20 * np.log10(d) + 20 * np.log10(4 * np.pi / .15)
                        interfering.append(10 ** ((23 - loss) / 10))
                total = np.sum(interfering) if interfering else 0
                interference_dbm = 10 * np.log10(total) if total > 0 else -np.inf
                denominator = 10 * np.log10(1e-8 + 10 ** (interference_dbm / 10)) if total > 0 else -80
                value = rx - denominator
                if value >= 3:
                    peers.append((j, value))
        peers.sort(key=lambda pair: -pair[1])
        for slot, (j, value) in enumerate(peers[:10]):
            rows[i, 63 + 4 * slot:67 + 4 * slot] = (
                *((positions[j] - positions[i]) / (1000, 1000, 100)),
                np.clip((value + 10) / 50, 0, 1))
    rows[:, -1] = tick / HORIZON
    return rows


def verify_episode(row, raw, *, verify_observations=True):
    steps = int(raw['completed_steps'])
    if steps != row['steps']:
        raise AssertionError('partial raw cannot support a complete endpoint')
    if raw['map_packet'].tobytes() != encode_map(raw['true_sites']):
        raise AssertionError('provisioned map differs from declared encoding')
    rng = np.random.RandomState(row['seed'])
    initial = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)]
                        for _ in range(N)])
    true_sites = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(50)])
    np.testing.assert_array_equal(raw['positions'][0], initial)
    np.testing.assert_array_equal(raw['true_sites'], true_sites)
    sites = decode_map(raw['map_packet'].tobytes())
    predicted_next = np.clip(raw['positions'][:-1] + raw['commands'] * 30, LOW, HIGH)
    assert_close(raw['positions'][1:], predicted_next, 0)
    controllers = [LocalController(history=False) for _ in range(N)]
    max_j_error = max_sinr_error = max_obs_error = 0.0
    eligible_gained = eligible_lost = connection_changed = 0
    allon_native_j_gaps = []
    for tick in range(steps):
        mask = int(raw['mask'][tick])
        sinr, connections, metrics = radio(raw['positions'][tick + 1], raw['true_sites'], mask)
        assert_close(raw['sinr'][tick], sinr)
        np.testing.assert_array_equal(raw['connections'][tick], connections)
        assert_close([raw['reward'][tick], raw['served'][tick], raw['quality'][tick]],
                     [metrics['J'], metrics['served'], metrics['quality']], 1e-12)
        max_j_error = max(max_j_error, abs(float(raw['reward'][tick]) - float(metrics['J'])))
        finite = np.isfinite(sinr)
        max_sinr_error = max(max_sinr_error, float(np.max(np.abs(raw['sinr'][tick][finite] - sinr[finite]))))
        allsinr, allconnections, allmetrics = radio(raw['positions'][tick + 1], raw['true_sites'], ALL_ON)
        eligible_gained += int(((sinr >= 3) & (allsinr < 3)).sum())
        eligible_lost += int(((sinr < 3) & (allsinr >= 3)).sum())
        connection_changed += int((connections != allconnections).sum())
        allon_native_j_gaps.append(float(metrics['J'] - allmetrics['J']))
        if verify_observations:
            observation = observed_rows(raw['positions'][tick], raw['true_sites'], mask, tick)
            assert_close(raw['observations'][tick], observation, 1e-6)
            max_obs_error = max(max_obs_error, float(np.max(np.abs(raw['observations'][tick] - observation))))
        for i, controller in enumerate(controllers):
            command, diagnostics = controller.act(raw['observations'][tick, i], tick)
            np.testing.assert_array_equal(command, raw['commands'][tick, i])
            for key in ('fallback', 'n_current', 'n_visible_peers', 'selected_index'):
                if diagnostics[key] != raw[key][tick, i]:
                    raise AssertionError(f'C diagnostic mismatch: {key}')

    round_count = int(raw['round_count'])
    if (row['arm'] == 'A' and round_count != 0) or (row['arm'] != 'A' and round_count != (steps + 3) // 4):
        raise AssertionError('wrong scheduler exposure')
    current_mask = ALL_ON
    report_ages = []
    origin = None
    forecast_errors = {str(offset): [] for offset in (2, 3, 4, 5)}
    reward_errors = {str(offset): [] for offset in (2, 3, 4, 5)}
    predicted_gains = []
    for tick in range(steps):
        if raw['mask'][tick] != current_mask:
            raise AssertionError('mask effective before arrival or held for wrong transitions')
        if origin is not None:
            report_ages.append(tick - origin)
        if row['arm'] == 'A' or tick % 4:
            continue
        index = tick // 4
        if raw['round_tick'][index] != tick:
            raise AssertionError('incorrect report clock')
        packets = [x.tobytes() for x in raw['report_packets'][index]]
        if tuple(packets) != encode_reports(raw['observations'][tick, :, :3], raw['commands'][tick], tick):
            raise AssertionError('report contains undeclared state or old command')
        positions, commands = decode_reports(packets, tick)
        forecast, offsets = forecast_positions(positions, commands, tick)
        length = int(raw['forecast_lengths'][index])
        if length:
            assert_close(raw['forecast'][index, :length], forecast, 0)
        plans = int(raw['candidate_plans'][index])
        order = raw['candidate_order'][index, :plans].tolist()
        if len(set(order)) != len(order):
            raise AssertionError('repeated candidate plan')
        for candidate in order:
            states = []
            for predicted in forecast:
                _, _, metrics = radio(predicted, sites, candidate)
                states.append([metrics['J'], metrics['served'], metrics['quality']])
            assert_close(raw['candidate_states'][index, candidate, :len(offsets)], states, 1e-12)
            assert_close(raw['candidate_scores'][index, candidate], np.mean(states, axis=0), 1e-12)
        if raw['timely'][index]:
            if row['arm'] == 'E':
                if order != list(range(1, 32)):
                    raise AssertionError('incomplete exhaustive search applied')
                choice = max(order, key=lambda mask: rank(mask, raw['candidate_scores'][index, mask]))
            else:
                choice = 31
                expected_order = [31]
                while choice.bit_count() > 1:
                    removals = sorted(choice ^ (1 << i) for i in range(N) if choice & (1 << i))
                    expected_order.extend(removals)
                    best = max(removals, key=lambda mask: rank(mask, raw['candidate_scores'][index, mask]))
                    if rank(best, raw['candidate_scores'][index, best]) <= rank(choice, raw['candidate_scores'][index, choice]):
                        break
                    choice = best
                if order != expected_order or plans > 15:
                    raise AssertionError('wrong greedy sequence')
            decoded = decode_command(raw['command_packets'][index].tobytes(), tick)
            if choice != decoded or choice != raw['selected_mask'][index] or raw['applied_mask'][index] != choice:
                raise AssertionError('choice/command/arrival mismatch')
            if raw['scheduler_wall'][index] > .456 + 1e-15:
                raise AssertionError('overdue command applied')
            if raw['round_bytes'][index] != 136 or raw['state_reductions'][index] != plans * len(offsets):
                raise AssertionError('wrong completed round traffic or reductions')
            current_mask = choice
            origin = tick
            gain = raw['candidate_scores'][index, choice, 0] - raw['candidate_scores'][index, 31, 0]
            predicted_gains.append(float(gain))
            for slot, offset in enumerate(offsets):
                if tick + offset > steps:
                    continue
                error = np.linalg.norm(forecast[slot] - raw['positions'][tick + offset], axis=-1)
                forecast_errors[str(offset)].extend(error.tolist())
                reward_errors[str(offset)].append(float(raw['reward'][tick + offset - 1]
                     - raw['candidate_states'][index, choice, slot, 0]))
        else:
            if raw['selected_mask'][index] != -1 or raw['applied_mask'][index] != current_mask:
                raise AssertionError('late result did not retain prior mask')
            if raw['command_packets'][index].any() or raw['round_bytes'][index] != 120:
                raise AssertionError('late command was transmitted')

    metrics = episode_metrics(raw, steps)
    for key, value in metrics.items():
        assert_close(value, row[key], 1e-12)
    for key, value in row['controller_counts'].items():
        if sum(controller.counters[key] for controller in controllers) != value:
            raise AssertionError(f'controller work mismatch: {key}')
    aggregate = lambda values: dict(count=len(values), mean=float(np.mean(values)) if values else None,
                                   max_abs=float(np.max(np.abs(values))) if values else None)
    return dict(arm=row['arm'], seed=row['seed'], verified_steps=steps,
                max_native_J_error=max_j_error, max_native_sinr_error=max_sinr_error,
                max_observation_error=max_obs_error,
                actual_geometry_eligible_gained=eligible_gained,
                actual_geometry_eligible_lost=eligible_lost,
                actual_geometry_connection_bits_changed=connection_changed,
                actual_geometry_J_minus_allon=aggregate(allon_native_j_gaps),
                selected_predicted_J_gain_over_allon=aggregate(predicted_gains),
                forecast_position_error_m={key: aggregate(value) for key, value in forecast_errors.items()},
                actual_minus_predicted_J={key: aggregate(value) for key, value in reward_errors.items()},
                report_age_ticks=aggregate(report_ages))


def read_result(out):
    started = time.perf_counter()
    cpu_started = time.process_time()
    out = Path(out)
    summary = json.loads((out / 'summary.json').read_text())
    if summary['status'] != 'COMPLETE' or not summary['scientific_invocation']:
        raise ValueError('no complete scientific panel to interpret')
    seeds = list(range(SEED, SEED + WORLDS))
    if summary['config']['seeds'] != seeds or summary['config']['horizon'] != HORIZON:
        raise AssertionError('changed fixed evaluation panel')
    counts = summary['counts']
    expected_counts = dict(constructors=1, explicit_resets=192, native_step_calls=49152,
                           team_steps=49152, complete_episodes=192, fit_started=0, optimizer_steps=0)
    if counts != expected_counts:
        raise AssertionError('wrong result exposure')
    if json.loads((out / 'config.json').read_text()) != summary['config']:
        raise AssertionError('runner config differs from compact result')
    if sorted(summary['artifacts'], key=lambda item: item['path']) != sorted(
            [row['raw'] for row in summary['rows']], key=lambda item: item['path']):
        raise AssertionError('raw manifest differs from complete endpoint evidence')
    expected_order = [(arm, seed) for i, seed in enumerate(seeds) for arm in ARM_ORDERS[i % 6]]
    if [(row['arm'], row['seed']) for row in summary['rows']] != expected_order:
        raise AssertionError('unbalanced or reordered execution')
    rows = []
    worlds = {}
    total_bytes = 0
    for row in summary['rows']:
        path = Path(row['raw']['path'])
        actual = file_identity(path)
        if any(actual[key] != row['raw'][key] for key in ('bytes', 'sha256')):
            raise AssertionError('changed raw artifact')
        total_bytes += actual['bytes']
        with np.load(path, allow_pickle=False) as raw:
            world = (raw['true_sites'], raw['positions'][0])
            if row['seed'] in worlds:
                for left, right in zip(world, worlds[row['seed']]):
                    np.testing.assert_array_equal(left, right)
            else:
                worlds[row['seed']] = tuple(value.copy() for value in world)
            rows.append(verify_episode(row, raw))
        print(json.dumps(dict(verified=len(rows), arm=row['arm'], seed=row['seed'])), flush=True)
    result = dict(status='VERIFIED_COMPLETE', launch_sha=summary['launch_sha'],
                  summary_sha256=file_identity(out / 'summary.json')['sha256'],
                  verified_raw_files=len(rows), verified_raw_bytes=total_bytes, rows=rows,
                  paired=paired_reading(summary['rows'], seeds),
                  scope='offline reconstruction, zero new environment steps/fits; geometry comparisons are descriptive, not task counterfactuals',
                  wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu_started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if result['paired'] != summary['paired']:
        raise AssertionError('compact paired reading differs')
    write_json(out / 'reading.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    read_result(args.out)
