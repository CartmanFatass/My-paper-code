"""Admitted single B05 purchase or complete same-source saved-trace reader."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time
import traceback

OPERATION_START = time.monotonic()
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))


def terminate(signum, _frame):
    """Route catchable supervisor stops through evidence and descendant cleanup."""
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


def resource_request(out):
    from scripts.hmasd_resource_preflight import capture_snapshot, assess_memory_floor
    snapshot = capture_snapshot()
    assessment = assess_memory_floor(snapshot)
    available_disk = shutil.disk_usage(out).free
    memory, disk = 8 * 1024**3, 12 * 1024**3
    result = {'snapshot': snapshot, 'shared_floor_assessment': assessment,
              'requested_memory_bytes': memory, 'requested_disk_free_bytes': disk,
              'disk_free_bytes': available_disk}
    if (any(assessment.get(key) is None or assessment[key] < memory
            for key in ('available_physical_bytes', 'effective_available_bytes'))
            or available_disk < disk):
        raise RuntimeError('selected8GiB RAM/12GiB free disk admission failed: ' + json.dumps(result))
    return result


def runtime():
    import platform
    import numpy as np
    import torch
    from experiments.candidates.uav_decision_generalization.b05_request_schedule import contract as c
    if (platform.system() != 'Linux' or
            (platform.python_version(), np.__version__, torch.__version__) != c.RUNTIME_VERSIONS):
        raise RuntimeError('selected Linux Python/NumPy/Torch runtime required: ' + repr(c.RUNTIME_VERSIONS))
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    return {'python': platform.python_version(), 'python_executable': sys.executable,
            'node': c.RESULT_NODE, 'numpy': np.__version__,
            'torch': torch.__version__, 'device': 'cpu', 'torch_threads': 4,
            'torch_interop_threads': 1, 'blas_threads': 1, 'GPU_seconds': 0,
            'unique_evidence_forecast_gib': [4, 8], 'additional_peak_forecast_gib': [6, 10],
            'cpu_forecast_hours': [20, 50], 'unmeasured_runtime_throughput': True}


def main(argv=None):
    args = parser().parse_args(argv)
    if args.seed != 109259999:
        raise ValueError('literal fixed study master required')
    if ((args.worker_input is None) != (args.worker_input_sha256 is None)
            or (args.mode == 'reader') != (args.worker_input is not None)):
        raise ValueError('reader requires exactly one bound completed worker locator')
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
    from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
    from experiments.candidates.uav_decision_generalization.b05_request_schedule import bindings as b, contract as c
    from experiments.candidates.uav_decision_generalization.b05_request_schedule.costs import Meter
    meter = None
    try:
        prior = e.bound_json(args.budget_ledger, args.budget_ledger_sha256)
        b.bind_prior(prior, mode=args.mode)
        meter = Meter(prior, OPERATION_START)
        meter.check()
        study = e.bound_json(args.study_input, args.study_input_sha256)
        sources = b.source_manifest(root)
        context = b.study_context(study, sources)
        if json.loads((out / 'launch-manifest.json').read_bytes())['node'] != c.RESULT_NODE:
            raise ValueError('admitted node differs from the fixed study node')
        config = {'schema': 1, 'object': 'B05_request_schedule', 'mode': args.mode,
                  'seed': args.seed, 'launch_sha': args.launch_sha, 'admission': admission,
                  'contract': c.frozen_contract(), 'source_sha256': sources,
                  'source_identity': context['source_identity'],
                  'study_input': e.identity(args.study_input), 'budget_ledger': e.identity(args.budget_ledger)}
        context.update(meter=meter, config=config)
        if args.mode == 'reader':
            context.update(b.worker_context(e.bound_json(args.worker_input, args.worker_input_sha256), config))
            b.bind_prior(prior, context['worker_summary'])
            config['worker_input'] = e.identity(args.worker_input)
        config.update(resource_request=resource_request(out), runtime=runtime())
        e.write_json(out / 'config.json', config)
        if args.mode == 'worker':
            from experiments.candidates.uav_decision_generalization.b05_request_schedule.worker import run
        else:
            from experiments.candidates.uav_decision_generalization.b05_request_schedule.reader import run
        run(root, out, args, context)
        meter.check()
        summary = json.loads((out / 'summary.json').read_bytes())
        summary['cost'] = meter.report()
        if args.mode == 'worker':
            summary['checked_exposures'] = b.validate_worker_counts(summary)
        e.write_json(out / 'summary.json', summary)
    except BaseException as exc:
        summary = json.loads((out / 'summary.json').read_bytes()) if (out / 'summary.json').exists() else {}
        summary.update(object='B05_request_schedule', status='FAILED', mode=args.mode,
                       launch_sha=args.launch_sha,
                       error={'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()},
                       cost=meter.report() if meter is not None else {'unmeasured_input_failure': True})
        e.write_json(out / 'summary.json', summary)
        raise


if __name__ == '__main__':
    main()
