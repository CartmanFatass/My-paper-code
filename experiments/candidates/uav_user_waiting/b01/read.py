#!/usr/bin/env python3
"""Complete saved-data verification and paired reading, with zero native steps."""

import argparse
import json
import os
from pathlib import Path
import resource
import sys
import time

for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_key] = '1'
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b01.read import assert_close, radio
from experiments.candidates.uav_radio_activation.b03 import protocol as p
from experiments.candidates.uav_registered_service.b01.read import (
    load_episode, verify_periodic, compare_metrics,
)
from experiments.candidates.uav_service_age.b01 import read as age_reader
from experiments.candidates.uav_user_waiting.b01.metrics import paired_reading
from experiments.candidates.uav_user_waiting.b01.study import (
    ARMS, ARM_ORDERS, SEED, WORLDS, episode_metrics,
    frozen_config, file_identity, write_json,
)


def native_key(pair, scores, proposal_q):
    q, mask = pair
    return (float(scores[pair][0]), float(scores[pair][1]), int(q == proposal_q),
            int(mask).bit_count(), -mask, -q)


def search_from_records(keys, current_mask, proposal_q):
    """Independent ordered enumeration; retain the four actually visited sets."""
    stages = []

    def choose(pairs):
        pairs = list(pairs)
        stages.append(pairs)
        for pair in pairs:
            if not np.isfinite(keys[pair][:8]).all():
                raise AssertionError('choice read an uncompleted burden key')
        return max(pairs, key=lambda pair: tuple(keys[pair][:8]))

    q, _ = choose((q, current_mask) for q in range(27))
    first = choose((q, mask) for mask in range(1, 32))
    _, mask = choose((proposal_q, mask) for mask in range(1, 32))
    second = choose((q, mask) for q in range(27))
    selected = max((first, second), key=lambda pair: tuple(keys[pair][:8]))
    return selected, stages, [first, second]


def sensitivity(raw, index, stages, final_pair, selected, proposal_q):
    """Same-set ranking changes only; no unvisited path or native counterfactual."""
    scores = raw['candidate_scores'][index]
    burdens = raw['burden_candidate_endpoint_burden'][index]
    settled = raw['burden_snapshot_burden'][index]
    prefix_last = raw['prefix_last'][index]
    length = int(raw['forecast_lengths'][index])
    ages = sorted(set(prefix_last.tolist()))
    keys = raw['ordering_keys'][index]

    def r_key(pair):
        return tuple(keys[pair][:8])

    def without_settled(pair):
        predicted = burdens[pair] - settled
        return (-int(predicted.max()), -int(predicted.sum())) + native_key(pair, scores, proposal_q)

    def oldest(pair):
        contacts = raw['candidate_contacts'][index][pair][:length].any(axis=0)
        counts = tuple(int(contacts[prefix_last == age].sum()) for age in ages)
        return counts + native_key(pair, scores, proposal_q)

    unique = list(dict.fromkeys(pair for stage in stages for pair in stage))
    values = {}
    for label, key in (('without_settled', without_settled), ('oldest', oldest)):
        stage_diff = [max(stage, key=r_key) != max(stage, key=key) for stage in stages]
        finalist = max(final_pair, key=key)
        union_best = max(unique, key=key)
        values[label] = dict(stage_differences=stage_diff,
                             final_two_difference=finalist != selected,
                             visited_union_difference=union_best != selected,
                             finalist=list(finalist), visited_union_best=list(union_best))
    return dict(tick=int(raw['round_tick'][index]), selected=list(selected), **values)


def verify_r_history(row, raw):
    steps = row['steps']
    sites = p.decode_map(raw['map_packet'].tobytes())
    anchors, last, windows = {}, np.full(50, -1, dtype=np.int64), np.zeros((4, 50), bool)
    burden = np.zeros(50, dtype=np.int64)
    predicted, valid = np.zeros((steps, 50), bool), np.zeros(steps, bool)
    cursor, position, start = 0, None, None
    physics_pairs, rankings, burden_errors = 0, [], []

    def settle(stop):
        nonlocal cursor, position
        while cursor < stop:
            origin = anchors.get(cursor, position)
            assert origin is not None, 'settlement without a lawful anchor'
            position = np.clip(origin + 30 * raw['commands'][cursor], p.LOW, p.HIGH)
            _, connected, _ = radio(position, sites, int(raw['mask'][cursor]))
            served = connected.any(axis=0)
            predicted[cursor], valid[cursor] = served, True
            last[served] = cursor
            windows[cursor // 64] |= served
            # Independent recurrence: R's history/copy/update methods are never called.
            for user in range(50):
                burden[user] += cursor - int(last[user])
            cursor += 1
        if stop in anchors:
            position = anchors[stop].copy()

    for index, tick in enumerate(range(0, steps, 4)):
        get = lambda name: raw['burden_' + name][index]
        length, member = min(4, steps - tick - 2), index % 5
        proposal_q = p.command_index(raw['proposals'][tick, member])
        current_mask = int(raw['mask'][tick])
        assert raw['history_before'][index] == cursor
        sent = bool(raw['report_packets'][index].any())
        decoded = actual_wire = proposed = None
        if sent:
            packets = tuple(packet.tobytes() for packet in raw['report_packets'][index])
            assert packets == p.encode_reports(raw['observations'][tick, :, :3],
                                                raw['commands'][tick], raw['proposals'][tick], tick)
            decoded, actual_wire, proposed = p.decode_reports(packets, tick)
        if raw['decoded_anchor'][index]:
            assert sent
            np.testing.assert_array_equal(get('decoded_positions'), decoded)
            np.testing.assert_array_equal(get('decoded_proposals'), proposed)
            anchors[tick] = decoded.copy()
            if start is None:
                start, cursor, position = tick, tick, decoded.copy()
        after = int(raw['history_after'][index])
        assert cursor <= after <= tick
        assert raw['history_reductions'][index] == after - cursor
        settle(after)
        assert raw['history_start'][index] == (-1 if start is None else start)
        assert bool(get('burden_unknown')) == (start is not None and start > 0)
        np.testing.assert_array_equal(raw['window_valid'][index],
                                      np.arange(4) * 64 >= (256 if start is None else start))
        np.testing.assert_array_equal(raw['unknown_age'][index],
                                      (last == -1) & (start is not None and start > 0))
        if raw['snapshot_valid'][index]:
            assert after == tick and raw['decoded_anchor'][index]
            np.testing.assert_array_equal(raw['snapshot_last'][index], last)
            np.testing.assert_array_equal(raw['snapshot_windows'][index], windows)
            np.testing.assert_array_equal(get('snapshot_burden'), burden)
            if start == 0:
                actual_burden = raw['actual_ages'][:tick].sum(axis=0, dtype=np.int64)
                delta = burden - actual_burden
                burden_errors.append(dict(tick=tick, differing_users=int(np.count_nonzero(delta)),
                                          max_absolute_error=int(np.abs(delta).max())))
        else:
            assert np.all(get('snapshot_burden') == -2)
        prefix_last, prefix_windows, prefix_burden = last.copy(), windows.copy(), burden.copy()
        prefix_position = None if decoded is None else decoded.copy()
        prefix_ticks = int(raw['prefix_ticks'][index])
        assert 0 <= prefix_ticks <= 2
        if prefix_ticks:
            assert raw['snapshot_valid'][index]
            for offset in range(prefix_ticks):
                at = tick + offset
                prefix_position = np.clip(prefix_position + actual_wire * 30, p.LOW, p.HIGH)
                _, connected, _ = radio(prefix_position, sites, current_mask)
                served = connected.any(axis=0)
                np.testing.assert_array_equal(get('prefix_contacts')[offset], served)
                prefix_last[served] = at
                prefix_windows[at // 64] |= served
                prefix_burden += at - prefix_last
        assert not get('prefix_contacts')[prefix_ticks:].any()
        count = int(raw['candidate_plans'][index])
        order = [tuple(map(int, pair)) for pair in raw['candidate_order'][index, :count]]
        scores, keys = raw['candidate_scores'][index], raw['ordering_keys'][index]
        assert len(set(order)) == count == np.isfinite(scores[:, :, 0]).sum()
        requests = int(get('request_count'))
        assert requests == raw['candidate_requests'][index]
        request_pairs = [tuple(map(int, pair)) for pair in get('request_pairs')[:requests]]
        assert np.all(get('request_pairs')[requests:] == -1)
        assert all(0 <= q < 27 and 1 <= mask <= 31 for q, mask in request_pairs)
        assert requests == raw['candidate_cache_hits'][index] + raw['candidate_uncached_requests'][index]
        assert raw['interrupted_candidate_requests'][index] == raw['candidate_uncached_requests'][index] - count
        assert order == list(dict.fromkeys(pair for pair in request_pairs if np.isfinite(scores[pair][0])))
        assert raw['forecast_lengths'][index] == length
        assert np.isnan(raw['forecast'][index, :, length:]).all()
        if raw['prefix_valid'][index]:
            assert prefix_ticks == 2 and raw['snapshot_valid'][index]
            np.testing.assert_array_equal(raw['prefix_last'][index], prefix_last)
            np.testing.assert_array_equal(raw['prefix_windows'][index], prefix_windows)
            np.testing.assert_array_equal(get('prefix_burden'), prefix_burden)
            assert raw['key_length'][index] == 8
            trajectories = []
            for q in range(27):
                commands = proposed.copy()
                commands[member] = COMMANDS[q]
                point, trajectory = prefix_position.copy(), []
                for _ in range(length):
                    point = np.clip(point + 30 * commands, p.LOW, p.HIGH)
                    trajectory.append(point.copy())
                trajectories.append(trajectory)
            forecasts = np.array(trajectories)
            if np.isfinite(raw['forecast'][index, :, :length]).any():
                assert_close(raw['forecast'][index, :, :length], forecasts, 0)
            else:
                assert not order
            for q, mask in order:
                contacts = raw['candidate_contacts'][index, q, mask, :length]
                assert not raw['candidate_contacts'][index, q, mask, length:].any()
                private_last, private_burden = prefix_last.copy(), prefix_burden.copy()
                for offset, served in enumerate(contacts):
                    at = tick + 2 + offset
                    private_last[served] = at
                    private_burden += at - private_last
                np.testing.assert_array_equal(get('candidate_endpoint_last')[q, mask], private_last)
                np.testing.assert_array_equal(get('candidate_endpoint_burden')[q, mask], private_burden)
                expected = (-int(private_burden.max()), -int(private_burden.sum())) + native_key((q, mask), scores, proposal_q)
                assert_close(keys[q, mask, :8], expected, 0)
                assert np.isnan(keys[q, mask, 8:]).all()
                assert_close(scores[q, mask, 1], contacts.sum(axis=1).mean(), 1e-12)
                assert_close(scores[q, mask, 0], .7 * scores[q, mask, 1] / 50 + .3 * scores[q, mask, 2], 1e-12)
            subset = set(order) if tick in (0, 60, 124, 252) else set()
            if raw['timely'][index]:
                subset.add((int(raw['selected_q'][index]), int(raw['selected_mask'][index])))
            for q, mask in sorted(subset):
                values = []
                for slot, point in enumerate(forecasts[q]):
                    _, connected, metrics = radio(point, sites, mask)
                    np.testing.assert_array_equal(raw['candidate_contacts'][index, q, mask, slot], connected.any(axis=0))
                    values.append((metrics['J'], metrics['served'], metrics['quality']))
                assert_close(scores[q, mask], np.mean(values, axis=0), 1e-12)
                physics_pairs += 1
        else:
            assert not order and raw['key_length'][index] == 0
            assert np.all(get('prefix_burden') == -2)
        # Sentinel bytes are evidence that an uncompleted candidate was not used.
        unscored = ~np.isfinite(scores[:, :, 0])
        assert np.all(get('candidate_endpoint_burden')[unscored] == -2)
        assert np.all(get('candidate_endpoint_last')[unscored] == -2)
        assert np.isnan(keys[unscored]).all()
        if raw['timely'][index]:
            selected, stages, finalists = search_from_records(keys, current_mask, proposal_q)
            assert selected == (raw['selected_q'][index], raw['selected_mask'][index])
            assert request_pairs == [pair for stage in stages for pair in stage]
            assert order == list(dict.fromkeys(request_pairs))
            q, mask = selected
            commands = proposed.copy()
            commands[member] = COMMANDS[q]
            np.testing.assert_array_equal(raw['commitments'][index], commands)
            np.testing.assert_array_equal(raw['sequential_pair'][index], selected)
            assert_close(raw['sequential_score'][index], scores[selected], 0)
            assert p.decode_command(raw['command_packets'][index].tobytes(), tick) == (mask, member, q)
            assert raw['applied_mask'][index] == mask and raw['round_bytes'][index] == 136
            assert raw['scheduler_wall'][index] <= p.DEADLINE_SECONDS
            assert requests == 116
            assert raw['state_reductions'][index] == length * count
            assert raw['geometry_snapshots'][index] == 27 * length
            assert raw['fallback_reason'][index] == ''
            rankings.append(sensitivity(raw, index, stages, finalists, selected, proposal_q))
        else:
            np.testing.assert_array_equal(raw['commitments'][index], raw['commands'][tick])
            assert raw['applied_mask'][index] == current_mask
            assert raw['selected_q'][index] == raw['selected_mask'][index] == -1
            assert not raw['command_packets'][index].any()
            assert raw['round_bytes'][index] == (120 if sent else 0)
        assert raw['scheduler_wall'][index] + 1e-12 >= raw['c_wall'][tick]
        assert raw['scheduler_cpu'][index] + 1e-12 >= raw['c_cpu'][tick]
        for unit in ('wall', 'cpu'):
            values = [raw[name + '_' + unit][index] for name in ('history', 'prefix', 'candidate')]
            assert all(np.isfinite(value) and value >= 0 for value in values)
            assert sum(values) <= raw['scheduler_' + unit][index] + 1e-9
        assert bool(raw['actual_timeout'][index]) == (raw['scheduler_wall'][index] > p.DEADLINE_SECONDS)
    before = cursor
    if start is not None:
        settle(steps)
    assert raw['terminal_history_reductions'] == cursor - before
    assert raw['terminal_history_start'] == (-1 if start is None else start)
    assert bool(raw['terminal_history_complete']) == (start is not None and cursor == steps)
    assert bool(raw['terminal_burden_unknown']) == (start is not None and start > 0)
    np.testing.assert_array_equal(raw['model_valid'], valid)
    np.testing.assert_array_equal(raw['model_contacts'], predicted)
    np.testing.assert_array_equal(raw['terminal_last'], last)
    np.testing.assert_array_equal(raw['terminal_windows'], windows)
    np.testing.assert_array_equal(raw['terminal_burden'], burden)
    return dict(verified_model_transitions=int(valid.sum()), candidate_physics_pairs=physics_pairs,
                rankings=rankings,
                settled_burden_errors=burden_errors,
                terminal_model_minus_actual_burden=(burden - raw['actual_ages'].sum(axis=0, dtype=np.int64)).tolist() if start == 0 else None,
                candidate_physics_scope='all selected pairs; all evaluated pairs at reports0/60/124/252; every completed candidate burden/key',
                kernel_scope='shared native radio; independent integer burden/history/key recurrence')


def verify_episode(row, raw, *, verify_observations=True):
    assert str(raw['program']) == row['arm'] and int(raw['world_seed']) == row['seed']
    if row['arm'] == 'R':
        result = age_reader.verify_native(row, raw, verify_observations=verify_observations)
        result.update(verify_r_history(row, raw))
        verify_periodic(row, raw)
        age_reader.verify_age(row, raw)
    else:
        result = age_reader.verify_episode(row, raw, verify_observations=verify_observations)
    # Check the primary endpoint directly from the independently verified age array.
    user_means = raw['actual_ages'].sum(axis=0, dtype=np.int64) / row['steps']
    assert_close(row['F_user'], user_means.max(), 0)
    assert_close(row['per_user_mean_age'], user_means, 0)
    for key, value in episode_metrics(raw, row['steps'], row['arm']).items():
        compare_metrics(value, row[key])
    result.update(arm=row['arm'], seed=row['seed'])
    return result


def summarize_rankings(rows):
    R = [row for row in rows if row['arm'] == 'R']
    results = {}
    for label in ('without_settled', 'oldest'):
        worlds = []
        for row in R:
            ranks = [slot[label] for slot in row['rankings']]
            worlds.append(dict(seed=row['seed'], timely_slots=len(ranks),
                               stage_differences=sum(sum(x['stage_differences']) for x in ranks),
                               slots_any_stage_difference=sum(any(x['stage_differences']) for x in ranks),
                               final_two_differences=sum(x['final_two_difference'] for x in ranks),
                               visited_union_differences=sum(x['visited_union_difference'] for x in ranks)))
        results[label] = dict(worlds=worlds, **{
            key: sum(world[key] for world in worlds)
            for key in ('timely_slots', 'stage_differences', 'slots_any_stage_difference',
                        'final_two_differences', 'visited_union_differences')})
    results['scope'] = 'same R-visited sets only; altered paths and complete outcomes unmeasured'
    return results


def read_result(out):
    started, cpu_started = time.perf_counter(), time.process_time()
    out = Path(out)
    summary = json.loads((out / 'summary.json').read_text())
    assert summary['status'] == 'COMPLETE' and summary['scientific_invocation']
    config = json.loads((out / 'config.json').read_text())
    assert summary['config'] == config == frozen_config(summary['launch_sha'])
    seeds = list(range(SEED, SEED + WORLDS))
    expected_counts = dict(constructors=1, explicit_resets=256, native_step_calls=65536,
                           team_steps=65536, complete_episodes=256, fit_started=0, optimizer_steps=0)
    assert summary['counts'] == expected_counts
    assert summary['fixed_policy_evaluation_counts'] == dict(episodes=256, transitions=65536,
                                                            optimizer_updates=0, parameter_updates=0)
    assert [(row['arm'], row['seed']) for row in summary['rows']] == [
        (arm, seed) for index, seed in enumerate(seeds) for arm in ARM_ORDERS[index % 8]]
    assert sorted(summary['artifacts'], key=lambda x: x['path']) == sorted(
        [row['raw'] for row in summary['rows']], key=lambda x: x['path'])
    assert json.loads((out / 'process-exit.json').read_text())['exit_code'] == 0
    rows, worlds, total_bytes = [], {}, 0
    for row in summary['rows']:
        path = Path(row['raw']['path'])
        identity = file_identity(path)
        assert identity == row['raw'], f'raw identity mismatch: {path}'
        total_bytes += identity['bytes']
        raw = load_episode(path)
        world = raw['true_sites'], raw['positions'][0]
        if row['seed'] in worlds:
            for left, right in zip(world, worlds[row['seed']]):
                np.testing.assert_array_equal(left, right)
        else:
            worlds[row['seed']] = tuple(x.copy() for x in world)
        rows.append(verify_episode(row, raw))
        del raw
        print(json.dumps(dict(verified=len(rows), arm=row['arm'], seed=row['seed'])), flush=True)
    paired = paired_reading(summary['rows'], seeds, ARMS)
    assert paired == summary['paired']
    result = dict(status='VERIFIED_COMPLETE', launch_sha=summary['launch_sha'],
                  summary_sha256=file_identity(out / 'summary.json')['sha256'],
                  verified_raw_files=len(rows), verified_raw_bytes=total_bytes,
                  rows=rows, paired=paired, ranking_sensitivity=summarize_rankings(rows),
                  scope='all fixed256 native/C/age/periodic/history records; R burden/key arithmetic; inherited O/W/M reader; declared physical subset; zero native steps/fits',
                  wall_seconds=time.perf_counter() - started,
                  cpu_seconds=time.process_time() - cpu_started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  rss_scope='reader lifetime peak; Linux KiB')
    write_json(out / 'reading.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    return read_result(parser.parse_args(argv).out)


if __name__ == '__main__':
    main()
