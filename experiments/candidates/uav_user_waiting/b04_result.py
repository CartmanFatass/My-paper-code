"""Compact B04 publication from pinned complete worker/reader JSON, without replay."""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time


SOURCE = 'dd3b2577d407b57a3b76ea4ba95b6ead4349d0d4'


def pinned(path, digest):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('changed complete B04 input')
    return json.loads(data), len(data)


def terminal(path, source, admission):
    value = json.loads(Path(path).read_text())
    assert value['sha'] == admission['sha'] == source
    assert value['direction'] == admission['direction'] == 'uav_user_waiting'
    assert value['node'] == 'wsl_4070' and value['record_consistency']['state'] == 'consistent'
    assert value['execution']['state'] == 'exited' and value['execution']['exit_code'] == 0
    assert value['execution']['exit_witness']['state'] == 'valid'
    assert value['execution']['runner']['recorded_identity']['pid'] == admission['child_pid']
    assert value['execution']['supervisor']['recorded_identity']['pid'] == admission['parent_pid']
    return value


def extrema(values):
    values = list(values)
    return dict(n=len(values), total=sum(values), minimum=min(values) if values else None,
                maximum=max(values) if values else None, mean=sum(values) / len(values) if values else None)


def compact_verification(row):
    result = {key: value for key, value in row.items()
              if key not in ('union_slots', 'settled_burden_errors')}
    anchors = row['settled_burden_errors']
    result['settled_burden_anchors'] = len(anchors)
    result['anchors_with_any_burden_difference'] = sum(item['differing_users'] > 0 for item in anchors)
    result['maximum_anchor_burden_error'] = max((item['max_absolute_error'] for item in anchors), default=0)
    slots = row['union_slots']
    executed = [slot for slot in slots if slot['timely']]
    result['union'] = dict(completed=len(slots), timely=len(executed),
        pool_sizes=extrema(slot['pool_size'] for slot in slots),
        feasible_sizes=extrema(slot['feasible_candidates'] for slot in slots),
        complete_changes={key: sum(slot[key] for slot in slots) for key in
                          ('filter_changes', 'U_differs_S', 'K_differs_M', 'selected_forecast_differs_M')},
        timely_changes={key: sum(slot[key] for slot in executed) for key in
                        ('filter_changes', 'U_differs_S', 'K_differs_M', 'selected_forecast_differs_M')},
        selected_model_service_margin=extrema(slot['selected_service_margin'] for slot in slots),
        selected_model_floor_violations=sum(slot['selected_service_margin'] < 0 for slot in slots),
        executed_native_minus_model_service=extrema(slot['actual_minus_modeled_service_total'] for slot in executed),
        executed_native_minus_model_floor=extrema(
            slot['actual_delivered_service_total'] - slot['floor_total'] for slot in executed),
        executed_native_below_model_floor=sum(
            slot['actual_delivered_service_total'] < slot['floor_total'] for slot in executed),
        same_state_q2_differences={left + '-' + right: extrema(
            slot['q2'][left] - slot['q2'][right] for slot in slots)
            for left, right in (('k', 'm'), ('k', 'u'), ('u', 's'))},
        scope='modeled same-state alternatives; actual delivered service only for executed choice, no counterfactual native M')
    return result


def extract(summary, reading, worker_status, reader_status, summary_sha256, reading_sha256):
    started, cpu_started = time.perf_counter(), time.process_time()
    s, summary_bytes = pinned(summary, summary_sha256)
    r, reading_bytes = pinned(reading, reading_sha256)
    assert s['status'] == 'COMPLETE' and r['status'] == 'VERIFIED_COMPLETE'
    assert s['launch_sha'] == r['worker_launch_sha'] == SOURCE
    assert r['worker_summary']['sha256'] == summary_sha256 and r['paired'] == s['paired']
    assert s['counts'] == dict(constructors=1, explicit_resets=256, native_step_calls=65536,
        team_steps=65536, complete_episodes=256, fit_started=0, optimizer_steps=0)
    expected = {(arm, seed) for arm in ('M', 'S', 'U', 'K') for seed in range(29426000, 29426064)}
    assert len(s['rows']) == len(r['rows']) == 256
    assert {(row['arm'], row['seed']) for row in s['rows']} == expected
    assert [(row['arm'], row['seed']) for row in s['rows']] == [
        (row['arm'], row['seed']) for row in r['rows']]
    assert sum(row['verified_steps'] for row in r['rows']) == 65536
    assert r['counts']['verified_raw_files'] == len(s['artifacts']) == 256
    assert r['counts']['verified_raw_bytes'] == sum(item['bytes'] for item in s['artifacts'])
    scalar_rows = [{key: value for key, value in row.items()
                   if not isinstance(value, (list, dict)) or key in ('raw', 'controller_counts', 'decision_counts')}
                  for row in s['rows']]
    per_user = [{key: row[key] for key in ('arm', 'seed', 'per_user_mean_age', 'worst_users',
                                         'per_user_gaps', 'per_window_coverage')} for row in s['rows']]
    worker_cpu = s['resources']['process_user_seconds'] + s['resources']['process_system_seconds']
    reader_cpu = r['resources']['process_user_seconds'] + r['resources']['process_system_seconds']
    worker_native = terminal(worker_status, SOURCE, s['admission'])
    reader_native = terminal(reader_status, r['reader_launch_sha'], r['admission'])
    assert r['worker_summary']['path'] == worker_native['output_root'] + '/summary.json'
    result = dict(object=s['object'], status=r['status'], launch_sha=SOURCE,
        summary=dict(node='wsl_4070', path=r['worker_summary']['path'],
                     bytes=summary_bytes, sha256=summary_sha256),
        full_reading=dict(node='wsl_4070', path=reader_native['output_root'] + '/reading.json',
                          bytes=reading_bytes, sha256=reading_sha256),
        retention='One canonical node copy of full summary, full reading and raw arrays; compact Git records contain all worlds, paired endpoints and per-user gap/age vectors.',
        counts=s['counts'], fixed_policy_evaluation_counts=s['fixed_policy_evaluation_counts'],
        exposure=dict(new_episodes=256, new_native_steps=65536, scientific_fits=0, optimizer_updates=0,
                      correctness_episodes=4, correctness_native_steps=32, correctness_fits=0),
        config=s['config'], paired=s['paired'], rows=scalar_rows, per_user=per_user,
        verification_counts=r['counts'], verification_scope=r['scope'],
        verification_rows=[compact_verification(row) for row in r['rows']],
        worker_resources=s['resources'], reader_resources=r['resources'],
        measured_cost=dict(worker_lifetime_cpu_seconds=worker_cpu, reader_lifetime_cpu_seconds=reader_cpu,
                           combined_cpu_seconds=worker_cpu + reader_cpu, scope='fixture separately charged; no sum-of-peaks memory claim'),
        raw_artifacts=s['artifacts'],
        worker_native_status=worker_native, reader_native_status=reader_native)
    result['extraction_resources'] = dict(wall_seconds=time.perf_counter() - started,
        cpu_seconds=time.process_time() - cpu_started, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scope='local JSON-only publication extraction; no new policy/radio/native/optimizer calls')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('summary', 'reading', 'worker-status', 'reader-status', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--summary-sha256', required=True)
    parser.add_argument('--reading-sha256', required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError('compact result already exists')
    result = extract(args.summary, args.reading, args.worker_status, args.reader_status,
                     args.summary_sha256, args.reading_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, separators=(',', ':'), allow_nan=False) + '\n')
    print(json.dumps(dict(path=str(args.out), bytes=args.out.stat().st_size,
                         sha256=hashlib.sha256(args.out.read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
