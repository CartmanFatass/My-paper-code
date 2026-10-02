"""Admitted finite SET mean worker or complete independent reader."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import traceback

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from experiments.candidates.uav_decision_generalization.b04_set_mean import contract as c


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


def accepted_output(args, admission, paths):
    from experiments.candidates.uav_decision_generalization.b03_joint_window.run import accepted_output as accepted
    root, out = accepted(args, admission, paths)
    if (out / 'manifest.json').exists() or (out / 'reading.json').exists():
        raise FileExistsError('no repeat of prior B04 output')
    return root, out


def resource_request(out):
    from scripts.hmasd_resource_preflight import capture_snapshot, assess_memory_floor
    snapshot = capture_snapshot()
    assessment = assess_memory_floor(snapshot)
    free = shutil.disk_usage(out).free
    memory, disk = 8 * 1024 ** 3, 4 * 1024 ** 3
    facts = {'snapshot': snapshot, 'shared_floor_assessment': assessment, 'requested_memory_bytes': memory,
             'requested_disk_free_bytes': disk, 'disk_free_bytes': free}
    if any(assessment.get(k) is None or assessment[k] < memory for k in ('available_physical_bytes', 'effective_available_bytes')) or free < disk:
        raise RuntimeError('selected8GiB memory/4GiB free disk not satisfied: ' + json.dumps(facts))
    return facts


def runtime():
    import platform
    from experiments.candidates.uav_decision_generalization.b03_joint_window.run import runtime as inherited
    if platform.python_version() != '3.10.21':
        raise RuntimeError('selected Python3.10.21 runtime required')
    facts = inherited()
    facts.update(python=platform.python_version(), nominal_cpu_forecast_hours=[.5, 1],
                 nominal_unique_evidence_gib=[.3, .6], additional_peak_disk_gib=[2.5, 3])
    return facts


def main(argv=None):
    args = parser().parse_args(argv)
    if args.seed != c.MASTER:
        raise ValueError('fixed inherited master seed required')
    if (args.worker_input is None) != (args.worker_input_sha256 is None) or (args.mode == 'reader') != (args.worker_input is not None):
        raise ValueError('reader requires exactly one bound B04 worker locator')
    from scripts.hmasd_admission import ENVIRONMENT_KEY, require_admission
    paths = json.loads(os.environ.get(ENVIRONMENT_KEY, '{}'))
    admission = require_admission(__file__, direction='uav_decision_generalization')
    root, out = accepted_output(args, admission, paths)
    for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
    from experiments.candidates.uav_decision_generalization.b04_set_mean import bindings as b
    meter = None
    try:
        prior = e.bound_json(args.budget_ledger, args.budget_ledger_sha256)
        meter = e.Meter(prior)
        b.check_counts(meter, args.mode)
        study = e.bound_json(args.study_input, args.study_input_sha256)
        sources = b.source_manifest(root)
        context = b.study_context(study, sources)
        config = {'schema': 1, 'object': c.OBJECT, 'mode': args.mode, 'seed': args.seed, 'launch_sha': args.launch_sha,
                  'admission': admission, 'contract': c.frozen_contract(), 'source_sha256': sources,
                  'study_input': e.identity(args.study_input), 'budget_ledger': e.identity(args.budget_ledger),
                  'ancestor': study['ancestor'], 'baseline_reading': study['baseline_reading'],
                  'retained_baseline_cost': context['baseline_reading']['cost']}
        context.update(meter=meter, config=config, source_sha256=sources)
        if args.mode == 'reader':
            context.update(b.worker_context(e.bound_json(args.worker_input, args.worker_input_sha256), config))
            b.bind_ledger(prior, context['worker_summary'])
            config['worker_input'] = e.identity(args.worker_input)
        config.update(resource_request=resource_request(out), runtime=runtime())
        e.write_json(out / 'config.json', config)
        if args.mode == 'worker':
            from experiments.candidates.uav_decision_generalization.b04_set_mean.worker import run
        else:
            from experiments.candidates.uav_decision_generalization.b04_set_mean.reader import run
        run(root, out, args, context)
    except BaseException as exc:
        summary = json.loads((out / 'summary.json').read_bytes()) if (out / 'summary.json').exists() else {}
        summary.update(object=c.OBJECT, status='FAILED', mode=args.mode, launch_sha=args.launch_sha,
                       error={'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()},
                       cost=meter.report() if meter is not None else {'unmeasured_input_failure': True})
        e.write_json(out / 'summary.json', summary)
        raise


if __name__ == '__main__':
    main()
