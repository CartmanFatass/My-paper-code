"""Admission-guarded fixed 32-world, 96-episode, zero-fit entry point."""
import argparse
import os
from pathlib import Path
import sys
import time

PROCESS_WALL_STARTED = time.perf_counter()
PROCESS_CPU_STARTED = time.process_time()
# Must precede numpy/environment imports; no process pools or Torch fitting.
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
             'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS'):
    os.environ[_key] = '1'

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def prepare_output(out):
    """The launcher owns the root; refuse only existing scientific outputs."""
    scientific = ('config.json', 'worker-status.json', 'reader-status.json', 'reading.json',
                  'summary.json', 'terminal-status.json')
    if any((out/name).exists() for name in scientific) or (
            (out/'raw').exists() and any((out/'raw').iterdir())):
        raise FileExistsError('scientific output exists; no overwrite or automatic retry')
    out.mkdir(parents=True, exist_ok=True)
    (out/'raw').mkdir(exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=29401000, help='fixed panel first seed (29401000)')
    parser.add_argument('--launch-sha', required=True)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.seed != 29401000:
        parser.error('this fixed study requires seeds 29401000..29401031')
    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction='uav_local_peer_forecast')
    if admission['sha'] != args.launch_sha:
        raise ValueError('launch SHA differs from admission')
    import_wall, import_cpu = time.perf_counter(), time.process_time()
    from experiments.candidates.uav_local_peer_forecast.study import (
        source_binding, write_json, identity, resources, make_real, collect_episode,
        SEEDS, ARMS, ORDERS, HORIZON, DIRECTION,
    )
    import_seconds = dict(wall_seconds=time.perf_counter()-import_wall,
                          process_cpu_seconds=time.process_time()-import_cpu,
                          scope='study/numpy imports; native factory imports counted separately')
    wall, cpu = PROCESS_WALL_STARTED, PROCESS_CPU_STARTED
    manifest = source_binding(args.launch_sha)
    prepare_output(args.out)
    config = dict(direction=DIRECTION, launch_sha=args.launch_sha, seeds=list(SEEDS),
                  arms=list(ARMS), orders=[list(o) for o in ORDERS], horizon=HORIZON,
                  started_fits=0, optimizer_calls=0, training_labels=0,
                  actor_contract='copied local FP32[104] row and primitive clock only',
                  workers=1, cpu_threads=1, torch_fit=False,
                  source_manifest=manifest,
                  scientific_import_telemetry=import_seconds,
                  declared_counts=dict(episodes=96, native_steps=24576, ingests=122880,
                                       rankings=30720, model_ticks=3317760,
                                       worker_power_ceiling=82663475,
                                       reader_score_requests=51200, reader_model_ticks=5529600,
                                       reader_power_ceiling=82663200))
    write_json(args.out/'config.json', config)
    counts = dict(started_fits=0, optimizer_calls=0, training_labels=0,
                  constructors_started=0, constructors_complete=0, explicit_resets=0,
                  started_episodes=0, complete_episodes=0, native_steps=0,
                  native_steps_attempted=0,
                  actor_ingests=0, rankings=0)
    episodes, env, worker_complete = [], None, False

    def status(state, error=None):
        raw = [identity(p) for p in sorted((args.out/'raw').glob('*.npz'))]
        value = dict(status=state, launch_sha=args.launch_sha, counts=counts.copy(),
                     episodes=episodes, raw=raw, config=identity(args.out/'config.json'),
                     error=error, telemetry=resources(wall, cpu))
        write_json(args.out/'worker-status.json', value)
        return value

    status('running')
    try:
        counts['constructors_started'] += 1
        factory_wall, factory_cpu = time.perf_counter(), time.process_time()
        env = make_real(args.seed)
        counts['constructors_complete'] += 1
        factory_telemetry = dict(wall_seconds=time.perf_counter()-factory_wall,
                                process_cpu_seconds=time.process_time()-factory_cpu,
                                scope='native factory imports, construction and unscored reset')
        # The all-on source binding is complemented by runtime configuration checks.
        base = env.env
        if (base.n_uavs, base.n_users, base.max_steps, base.area_size,
                base.height_range, base.max_speed, base.time_step, base.tx_power,
                base.noise_power, base.min_sinr, base.max_connections,
                base.carrier_frequency) != (5, 50, 256, 1000, (50, 150), 30, 1., 23, -80, 3, 10, 2e9):
            raise ValueError('native physical configuration differs')
        if (base.channel_model != 'free_space' or base.use_shadowing or base.use_fdma
                or base.paper_reward or base.enable_transmitter_mask
                or not base.transmitter_mask.all()):
            raise ValueError('requires unmasked all-on free-space base J')
        for j, seed in enumerate(SEEDS):
            for arm in ORDERS[j % 6]:
                episodes.append(collect_episode(env, arm, seed, args.out, counts))
                status('running')
        expected = dict(complete_episodes=96, native_steps=24576, actor_ingests=122880, rankings=30720)
        if any(counts[k] != v for k, v in expected.items()):
            raise ValueError('complete worker counts differ')
        totals = {}
        for episode in episodes:
            for key, value in episode['controller_counts'].items():
                totals[key] = totals.get(key, 0)+value
        if totals['model_ticks'] != 3317760 or totals['shadow_decisions']:
            raise ValueError('worker model ticks or online shadows differ')
        native_slots = (counts['native_steps']+counts['explicit_resets']+1)*275
        power_slots = totals['link_evaluations']+native_slots
        if power_slots > 82663475:
            raise ValueError('worker power ceiling exceeded')
        status('complete')
        worker_complete = True
        from experiments.candidates.uav_local_peer_forecast.reader import read_panel, new_progress
        reader_wall, reader_cpu = time.perf_counter(), time.process_time()
        reader_progress = new_progress()
        try:
            reading = read_panel(args.out, config, episodes, progress=reader_progress)
            write_json(args.out/'reading.json', reading)
            write_json(args.out/'reader-status.json', dict(status='complete',
                       progress=reader_progress, reading=identity(args.out/'reading.json'),
                       telemetry=resources(reader_wall, reader_cpu)))
        except BaseException as exc:
            reader_progress['status'] = 'incomplete'
            write_json(args.out/'reader-status.json', dict(status='failed',
                       progress=reader_progress, error=f'{type(exc).__name__}: {exc}',
                       telemetry=resources(reader_wall, reader_cpu)))
            raise
        summary = dict(status='complete', launch_sha=args.launch_sha, primary=reading['primary'],
                       counts=counts, controller_counts=totals, native_dense_power_slots=native_slots,
                       native_nonself_physical_links=(counts['native_steps']+counts['explicit_resets']+1)*270,
                       worker_power_slots=power_slots,
                       contrasts=reading['contrasts'],
                       per_world=[dict(arm=r['arm'], seed=r['seed'], **r['endpoint']) for r in reading['rows']],
                       forecast_errors=reading['forecast_errors'], reader_counts=reading['counts'],
                       reader_power_slots=reading['power_slots'], reader_telemetry=reading['telemetry'],
                       actor_cpu_seconds=sum(e['actor_cpu_seconds'] for e in episodes),
                       actor_wall_seconds=sum(e['actor_wall_seconds'] for e in episodes),
                       worker_telemetry=__import__('json').loads((args.out/'worker-status.json').read_text())['telemetry'],
                       complete_process_telemetry=resources(wall, cpu),
                       scientific_import_telemetry=import_seconds, factory_telemetry=factory_telemetry,
                       raw_location=str((args.out/'raw').resolve()),
                       raw_bytes=sum(e['raw']['bytes'] for e in episodes),
                       config=identity(args.out/'config.json'), reading=identity(args.out/'reading.json'),
                       worker_status=identity(args.out/'worker-status.json'),
                       reader_status=identity(args.out/'reader-status.json'))
        write_json(args.out/'summary.json', summary)
        write_json(args.out/'terminal-status.json', dict(status='complete', summary=identity(args.out/'summary.json'),
                                                       telemetry=resources(wall, cpu)))
    except BaseException as exc:
        if not worker_complete:
            status('failed', f'{type(exc).__name__}: {exc}')
        write_json(args.out/'terminal-status.json', dict(status='failed',
                   error=f'{type(exc).__name__}: {exc}', counts=counts, telemetry=resources(wall, cpu)))
        raise
    finally:
        if env is not None:
            env.close()


if __name__ == '__main__':
    main()
