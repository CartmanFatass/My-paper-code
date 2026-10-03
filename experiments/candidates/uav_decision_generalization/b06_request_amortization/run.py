"""One admitted B06 worker and its complete same-source reader; no retry mode."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

OPERATION_START = time.monotonic()
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))


def terminate(signum, _frame):
    raise SystemExit(128 + signum)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--mode', required=True, choices=('worker', 'reader'))
    result.add_argument('--seed', required=True, type=int)
    result.add_argument('--launch-sha', required=True)
    result.add_argument('--out', required=True, type=Path)
    for name in ('study-input', 'budget-ledger', 'worker-input'):
        result.add_argument('--' + name, type=Path, required=name != 'worker-input')
        result.add_argument('--' + name + '-sha256', required=name != 'worker-input')
    return result


def runtime():
    import platform
    import numpy as np
    import torch
    from experiments.candidates.uav_decision_generalization.b06_request_amortization import contract as c
    if (platform.system() != 'Linux' or
            (platform.python_version(), np.__version__, torch.__version__) != c.RUNTIME_VERSIONS):
        raise RuntimeError('selected Linux Python/NumPy/Torch runtime differs')
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    return {'python': platform.python_version(), 'python_executable': sys.executable,
            'node': c.RESULT_NODE, 'numpy': np.__version__, 'torch': torch.__version__,
            'device': 'cpu', 'torch_threads': 4, 'torch_interop_threads': 1,
            'blas_threads': 1, 'GPU_seconds': 0, 'cpu_forecast_hours': [4, 7],
            'operation_wall_forecast_hours': [5, 9], 'support_forecast_hours': [8, 14],
            'unmeasured_new_runtime_throughput': True}


def disk_roots(source_root, config, context):
    from experiments.candidates.uav_decision_generalization.b06_request_amortization import contract as c
    checkout = Path('/home/fires/hmasd-wsl')
    roots = [Path(source_root),
             checkout / 'runs/uav_decision_generalization' / c.WORKER_TAG,
             checkout / 'runs/uav_decision_generalization' / c.READER_TAG,
             checkout / 'temp/directions/uav_decision_generalization/b06_tests',
             checkout / 'temp/directions/uav_decision_generalization/b06_engineering_receipts',
             checkout / 'temp/directions/uav_decision_generalization/b06_requests',
             checkout / 'experiments/candidates/uav_decision_generalization/b06_request_amortization',
             checkout / 'tests/experiments/candidates/uav_decision_generalization/b06_request_amortization']
    inputs = checkout / 'docs/research/candidates/uav_decision_generalization'
    roots.extend(inputs / name for name in ('B06_STUDY_INPUT.json', 'B06_BUDGET_LEDGER.json',
                                            'B06_WORKER_INPUT.json', 'B06_READER_BUDGET_LEDGER.json'))
    if Path(source_root).parent != checkout / '.git/hmasd-launch-sources':
        raise ValueError('B06 requires its exact owned immutable launch snapshot')
    worker = context.get('worker_config')
    if worker is not None:
        old_source = Path(worker['source_root'])
        if old_source.parent != checkout / '.git/hmasd-launch-sources':
            raise ValueError('original worker snapshot scope differs')
        roots.append(old_source)
    for relative in ('study_input', 'budget_ledger', 'worker_input'):
        if relative in config:
            roots.append(Path(config[relative]['path']))
    return roots


def main(argv=None):
    args = parser().parse_args(argv)
    if args.seed != 109259999:
        raise ValueError('fixed literal study master required')
    if ((args.worker_input is None) != (args.worker_input_sha256 is None)
            or (args.mode == 'reader') != (args.worker_input is not None)):
        raise ValueError('reader requires exactly one original complete worker locator')
    from scripts.hmasd_admission import ENVIRONMENT_KEY, require_admission
    paths = json.loads(os.environ.get(ENVIRONMENT_KEY, '{}'))
    admission = require_admission(__file__, direction='uav_decision_generalization')
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    from experiments.candidates.uav_decision_generalization.b03_joint_window.run import accepted_output
    root, out = accepted_output(args, admission, paths)
    for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
    from experiments.candidates.uav_decision_generalization.b05_request_schedule.run import resource_request
    from experiments.candidates.uav_decision_generalization.b06_request_amortization import bindings as b, contract as c
    from experiments.candidates.uav_decision_generalization.b06_request_amortization.costs import Meter
    meter = None
    try:
        prior = e.bound_json(args.budget_ledger, args.budget_ledger_sha256)
        b.bind_prior(prior, mode=args.mode)
        if out.name != (c.WORKER_TAG if args.mode == 'worker' else c.READER_TAG):
            raise ValueError('one literal worker/reader tag; no replacement attempt')
        study = e.bound_json(args.study_input, args.study_input_sha256)
        sources = b.source_manifest(root)
        context = b.study_context(study, sources)
        if json.loads((out / 'launch-manifest.json').read_bytes())['node'] != c.RESULT_NODE:
            raise ValueError('admitted node differs from fixed local_linux selection')
        config = {'schema': 1, 'object': c.OBJECT, 'mode': args.mode,
                  'seed': args.seed, 'launch_sha': args.launch_sha, 'admission': admission,
                  'source_root': str(root), 'contract': c.frozen_contract(),
                  'source_sha256': sources, 'source_identity': context['source_identity'],
                  'teacher': study['teacher'], 'study_input': e.identity(args.study_input),
                  'budget_ledger': e.identity(args.budget_ledger)}
        if args.mode == 'reader':
            context.update(b.worker_context(e.bound_json(args.worker_input, args.worker_input_sha256), config))
            b.bind_prior(prior, context['worker_summary'])
            config['worker_input'] = e.identity(args.worker_input)
        meter = Meter(prior, OPERATION_START, disk_roots=disk_roots(root, config, context))
        context.update(meter=meter, config=config)
        meter.check()
        meter.check_disk(anticipated_bytes=64 * 1024**2)
        config.update(resource_request=resource_request(out), runtime=runtime())
        e.write_json(out / 'config.json', config)
        if args.mode == 'worker':
            from experiments.candidates.uav_decision_generalization.b06_request_amortization.worker import run
        else:
            from experiments.candidates.uav_decision_generalization.b06_request_amortization.reader import run
        run(root, out, args, context)
        meter.check()
        meter.check_disk(anticipated_bytes=1024**2)
        summary = json.loads((out / 'summary.json').read_bytes())
        summary['cost'] = meter.report()
        if args.mode == 'worker':
            summary['checked_exposures'] = b.validate_worker_counts(summary)
        e.write_json(out / 'summary.json', summary)
    except BaseException as exc:
        if meter is not None:
            meter.begin_finalization()
        summary = json.loads((out / 'summary.json').read_bytes()) if (out / 'summary.json').exists() else {}
        summary.update(object=c.OBJECT, status='FAILED', mode=args.mode,
                       launch_sha=args.launch_sha,
                       error={'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()},
                       cost=meter.report() if meter is not None else {'unmeasured_input_failure': True},
                       purchase_stopped=True, automatic_retry_authorized=False)
        e.write_json(out / 'summary.json', summary)
        raise


if __name__ == '__main__':
    main()
