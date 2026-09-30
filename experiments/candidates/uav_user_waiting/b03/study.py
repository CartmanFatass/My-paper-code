"""One fixed acquisition realization, two regressions and complete five-arm use."""
import json
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_radio_activation.b01.study import factory, file_identity, write_json
from experiments.candidates.uav_user_waiting.b02.study import source_identities as previous_sources
from experiments.candidates.uav_user_waiting.b01.metrics import METRICS
from experiments.candidates.uav_user_waiting.b02.metrics import EXTRA_METRICS
from experiments.candidates.uav_service_age.b01.metrics import describe
from .collector import ARMS, collect_episode, save_episode
from .data import build_dataset
from .learner import fit_ridge, fit_neural, save_model

ROOT = Path(__file__).resolve().parents[4]
PURE_SEEDS = tuple(range(29423000, 29423096))
PERTURBED_SEEDS = tuple(range(29423100, 29423196))
EVAL_SEEDS = tuple(range(29424000, 29424064))
ARM_ORDERS = tuple(tuple(order[i:] + order[:i])
                   for order in (ARMS, tuple(reversed(ARMS))) for i in range(5))


def perturbations():
    rng = np.random.Generator(np.random.PCG64(29425002))
    return [dict(seed=seed, tick=4 * (63 * j // 96),
                 pair=[int(rng.integers(27)), int(rng.integers(1, 32))])
            for j, seed in enumerate(PERTURBED_SEEDS)]


def frozen_config(launch_sha):
    sources = {row['path']: row for row in previous_sources()}
    for path in sorted(Path(__file__).parent.iterdir()):
        if path.suffix in ('.py', '.json'):
            name = str(path.relative_to(ROOT))
            sources[name] = dict(file_identity(path), path=name)
    return dict(object='UAV-USER-WAITING-B03', launch_sha=launch_sha,
        pure_seeds=list(PURE_SEEDS), perturbed_seeds=list(PERTURBED_SEEDS),
        eval_seeds=list(EVAL_SEEDS), perturbations=perturbations(),
        arms=list(ARMS), arm_orders=[list(order) for order in ARM_ORDERS],
        horizon=256, nodes=5, users=50, planned_fits=2, planned_new_episodes=512,
        planned_new_steps=131072, reused_episodes=64, previously_paid_steps=16384,
        correctness_steps=40, correctness_seed=29425999,
        init_seed=29425000, sample_seed=29425001, bootstrap_seed=29425991,
        bootstrap_samples=10000, feature_dim=805, hidden=[128,128],
        adam_updates=4096, batch_size=256, learning_rate=.001, ridge_lambda=.001,
        weighting='equal eligible episode, equal row within episode; target native suffix increment /256',
        scales='fixed805 dimensions, H256; no fitted scaler',
        deployment='256*unclipped fit output then clip[0,256-t]; terminal0',
        primary='LN-M mean_user_max_unserved_gap; lower favorable',
        experience_use='LN-G0; LN-LR and LR-G0 retain the ordinary fitted alternative',
        fallback='missing complete-origin maximum uses completed M; any whole-round late/incomplete holds old action/mask',
        decision='full M232requests + value two-order116 + explicit M1; elapsed4 maximum increment/value then elapsedage then delivered4 native ties',
        commitment='pre-C t+4 state carries current candidate through t+5 and previous post-C nav; no future C call',
        report_bytes=125, command_bytes=16, recurring_bytes=141, deadline_seconds=1.436,
        source_identities=[sources[key] for key in sorted(sources)])


def paired_reading(rows):
    by = {(r['arm'], r['seed']): r for r in rows}
    if len(rows) != 320 or set(by) != {(a,s) for a in ARMS for s in EVAL_SEEDS}:
        raise ValueError('complete fixed320-episode paired panel required')
    metrics = tuple(dict.fromkeys(METRICS + EXTRA_METRICS +
                    ('value_eligible_rounds','value_executed_rounds','value_pair_changes_from_m',
                     'value_pair_changes_from_visited_zero','value_queries','value_clipped_count')))
    levels = {a:{k:describe([by[a,s][k] for s in EVAL_SEEDS]) for k in metrics} for a in ARMS}
    pairs = [(a,b) for i,a in enumerate(ARMS) for b in ARMS[i+1:]]
    pairs += [(a,b) for a,b in (('LN','M'),('LN','G0'),('LN','LR'),('LR','G0'),('G0','M'),('LN','S'),('LR','S'),('G0','S')) if (a,b) not in pairs]
    contrasts = {a+'-'+b:{k:describe([by[a,s][k]-by[b,s][k] for s in EVAL_SEEDS]) for k in metrics} for a,b in pairs}
    rng = np.random.RandomState(29425991)
    indices = rng.randint(0, 64, size=(10000,64))
    for contrast in contrasts.values():
        for key in ('mean_user_max_unserved_gap','A','F_user','J','mean_served','max_unserved_gap'):
            means = np.asarray(contrast[key]['values'])[indices].mean(axis=1)
            contrast[key]['descriptive_paired_bootstrap95'] = np.quantile(means,[.025,.975]).tolist()
    return dict(levels=levels, contrasts=contrasts, world_seeds=list(EVAL_SEEDS),
                primary='LN-M:mean_user_max_unserved_gap', experience_use='LN-G0:mean_user_max_unserved_gap',
                scope='one acquisition/initialization realization; paired-world variation, no independent-training-population claim')


def run_batch(out, launch_sha, *, entry_start=None, admission=None):
    out = Path(out).resolve()
    if (out/'config.json').exists() or (out/'summary.json').exists():
        raise FileExistsError('no implicit resume or duplicate scientific invocation')
    (out/'raw').mkdir(parents=True, exist_ok=True)
    start, cpu = time.perf_counter() if entry_start is None else entry_start, time.process_time()
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    config = frozen_config(launch_sha)
    write_json(out/'config.json',config)
    counts = dict(constructors=0, explicit_resets=0, native_step_calls=0, team_steps=0,
                  complete_episodes=0, fit_started=0, optimizer_steps=0)
    summary = dict(object=config['object'], status='RUNNING', scientific_invocation=True,
        launch_sha=launch_sha, config=config, admission=admission, counts=counts,
        acquisition_rows=[], evaluation_rows=[], fits={}, phase='acquisition',
        runtime=dict(python=platform.python_version(),numpy=np.__version__,torch=torch.__version__,
                     host=platform.node(),platform=platform.platform()))
    env = None
    try:
        reference = json.loads((Path(__file__).parent/'reused_m.json').read_text())
        for source in reference['sources']:
            if file_identity(Path(source['raw']['path'])) != source['raw']:
                raise ValueError('required reused M raw missing or changed before acquisition')
        env = factory(PURE_SEEDS[0]); counts['constructors'] += 1
        env.env.max_steps = 256
        acquisition = [(s,None) for s in PURE_SEEDS] + [(r['seed'],(r['tick'],r['pair'])) for r in perturbations()]
        for seed, perturbation in acquisition:
            row, raw = collect_episode(env,'M',seed,out,counts,perturbation=perturbation,training=True)
            save_episode(out,row,raw)
            row['perturbation_tick'] = -1 if perturbation is None else perturbation[0]
            summary['acquisition_rows'].append(row)
            write_json(out/'summary.json',summary)
            print(json.dumps(dict(phase='acquisition',seed=seed,episodes=counts['complete_episodes'],steps=counts['team_steps'])),flush=True)
        sources = reference['sources'] + [dict(seed=r['seed'],raw=r['raw'],perturbation_tick=r['perturbation_tick']) for r in summary['acquisition_rows']]
        summary['phase'] = 'data'; write_json(out/'summary.json',summary)
        ds, provenance = build_dataset(sources)
        np.savez_compressed(out/'raw'/'training.npz',**ds)
        summary['training'] = dict(raw=file_identity(out/'raw'/'training.npz'), sources=provenance,
            labels=len(ds['y']), exposed_episodes=256, eligible_episodes=len(np.unique(ds['episode_ids'])))
        models = {}
        for arm, fit in (('LR',fit_ridge),('LN',fit_neural)):
            summary['phase'] = 'fit_'+arm; counts['fit_started'] += 1
            if arm == 'LN': counts['optimizer_steps'] = None
            write_json(out/'summary.json',summary)
            model, stats, trace = fit(ds['X'],ds['y'],ds['episode_ids'])
            save_model(out/'raw'/f'{arm}_model.npz',model)
            np.savez_compressed(out/'raw'/f'{arm}_fit_trace.npz',**trace)
            models[arm] = model
            summary['fits'][arm] = dict(stats=stats,model=file_identity(out/'raw'/f'{arm}_model.npz'),
                                       trace=file_identity(out/'raw'/f'{arm}_fit_trace.npz'))
            if arm == 'LN': counts['optimizer_steps'] = 4096
            write_json(out/'summary.json',summary)
        frozen_hashes = {arm:model.parameter_sha256() for arm,model in models.items()}
        summary['phase'] = 'evaluation'
        for index, seed in enumerate(EVAL_SEEDS):
            for arm in ARM_ORDERS[index % len(ARM_ORDERS)]:
                row, raw = collect_episode(env,arm,seed,out,counts,value=models.get(arm))
                save_episode(out,row,raw)
                summary['evaluation_rows'].append(row)
                write_json(out/'summary.json',summary)
                print(json.dumps(dict(phase='evaluation',arm=arm,seed=seed,episodes=counts['complete_episodes'],steps=counts['team_steps'],gap=row['mean_user_max_unserved_gap'])),flush=True)
        if frozen_hashes != {arm:model.parameter_sha256() for arm,model in models.items()}:
            raise AssertionError('frozen evaluation changed model parameters')
        summary['evaluation_parameter_sha256'] = frozen_hashes
        summary['paired'] = paired_reading(summary['evaluation_rows'])
        summary['status'], summary['phase'] = 'COMPLETE', 'complete'
        summary['fixed_policy_evaluation_counts'] = dict(episodes=320,transitions=81920,optimizer_updates=0,parameter_updates=0)
    except Exception as exc:
        summary['status'] = 'INCOMPLETE_TECHNICAL_FAILURE'
        summary['error'] = dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    finally:
        if env is not None: env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary['resources'] = dict(wall_seconds=time.perf_counter()-start, measured_cpu_seconds=time.process_time()-cpu,
            process_user_seconds=usage.ru_utime,process_system_seconds=usage.ru_stime,peak_rss_kib=usage.ru_maxrss,
            rss_scope='worker lifetime Linux KiB',scope='entry wall includes imports; process CPU includes import/init',
            torch_threads=torch.get_num_threads(),torch_interop_threads=torch.get_num_interop_threads(),
            thread_environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')})
        summary['artifacts'] = [file_identity(p) for p in sorted((out/'raw').iterdir()) if p.is_file()]
        write_json(out/'summary.json',summary)
    return summary
