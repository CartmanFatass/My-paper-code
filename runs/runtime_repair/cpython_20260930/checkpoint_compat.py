#!/usr/bin/env python3
"""Synthetic CPU evaluation-checkpoint compatibility, never training or resume.

Root executes with --source-root (the exact dd6 minimal source tree) --out
(a unique directory). Seed701/702/705 are diagnostic fixtures, not science seeds.
Learner creates its normal empty Adam objects; this helper takes zero optimizer
steps. Learner.state() has no optimizer state and cannot establish fit resumption.
Compare content/numerical hashes across runtimes, not torch ZIP file hashes.
"""

import argparse
import faulthandler
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import random
import resource
import sys
import time
import traceback


SOURCE_SHA = 'dd6cdf780031ac42b5b7097b76456f04a89c4b4d'
SOURCE_DIGESTS = {
    'experiments/candidates/uav_service_age/b01/__init__.py': 'a30d900ab2439ea58777f157cd60b4ad3dab5f5c6aa8f13363420a647dc097df',
    'experiments/candidates/uav_service_age/b01/learner.py': '9ad461b2a64d3439cf7004ad656758b02d3579c7c5b57ec127cbfc9db60f7ac8',
    'experiments/candidates/uav_service_age/b01/features.py': '55d2b58377019a2edcd3407639047314db58be2bffcbeac31860bf1ddddb28d2',
    'experiments/candidates/uav_local_history/b01/controller.py': 'b5fdfbfe2718ee693c9ed1d7aeb8bbb6c5c59964ec6c56c5bb35be8b685f23d2',
    'experiments/candidates/uav_radio_activation/b01/__init__.py': 'b0392e94f590eb0fd016ce26529485215b128b9accff9b1dc5fdd6ffd7d11b8a',
    'experiments/candidates/uav_radio_activation/b01/protocol.py': '4976e6739d1e5c919bd298b86091dcf6cf5d62d5c3cc3a7b977fa5b5f0956431',
    'experiments/candidates/uav_radio_activation/b02/__init__.py': '3e9e194f32194488a58d2bee13d5be625f5142b2d4330b76c729809924bf950e',
    'experiments/candidates/uav_radio_activation/b02/protocol.py': 'a1dbec8e5aecead2c702fab54376c95c8b9d1fd134cb0894a3c0eb705ebab69b',
    'experiments/candidates/uav_radio_activation/b03/__init__.py': 'e7f16638203ff2d8d5254017185d2b2133c21fc41b1fef22aa4709cbafc9c350',
    'experiments/candidates/uav_radio_activation/b03/protocol.py': '3561dd0c2ea274a7e24e5a8bc6da3d6ee03b21fcec8768d18adb45b4f524b2c1',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_identity(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest())


def array_identity(np, value):
    array = np.ascontiguousarray(value)
    header = dict(dtype=array.dtype.str, shape=list(array.shape))
    digest = hashlib.sha256(json.dumps(header, sort_keys=True).encode() + b'\0' + array.tobytes())
    return dict(header, sha256=digest.hexdigest())


def same_tensor(torch, before, after, name):
    require(before.dtype == after.dtype and before.shape == after.shape and
            before.device.type == after.device.type == 'cpu' and torch.equal(before, after),
            'Checkpoint tensor mismatch: ' + name)


def no_optimizer_updates(learner):
    require((learner.actor_updates, learner.critic_updates, learner.episodes_updated) == (0, 0, 0),
            'Fixture unexpectedly updated learner counters')
    require(not learner.actor_optimizer.state and not learner.critic_optimizer.state,
            'Fixture unexpectedly acquired optimizer state')
    require(all(parameter.grad is None for network in (learner.actor, learner.critic)
                for parameter in network.parameters()), 'Fixture unexpectedly acquired gradients')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    wall_started, cpu_started = time.monotonic(), time.process_time()
    record = dict(scope='synthetic CPU evaluation checkpoint, not fit resume', source_sha=SOURCE_SHA,
                  environments=0, transitions=0, fits=0, optimizer_steps=0, device='cpu',
                  fixture_seeds=dict(initializer=701, replacement_initializer=702, innovations=705),
                  python=sys.version, platform=platform.platform(), optimize=sys.flags.optimize,
                  pythonoptimize=os.environ.get('PYTHONOPTIMIZE'), allocator=os.environ.get('PYTHONMALLOC'),
                  dev_mode=sys.flags.dev_mode, checks={},
                  checkpoint_scope='Actual Learner.state(); actor/critic weights and scalar counters/digests; no optimizer state')

    def emit(status):
        record.update(status=status, wall_seconds=time.monotonic() - wall_started,
                      cpu_seconds=time.process_time() - cpu_started,
                      peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      rss_scope='Linux process lifetime maximum, KiB')
        temporary = args.out / 'summary.json.tmp'
        temporary.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
        temporary.replace(args.out / 'summary.json')

    with (args.out / 'faulthandler.log').open('w', buffering=1) as faults:
        faulthandler.enable(file=faults, all_threads=True)
        emit('INITIALIZING')
        try:
            sys.dont_write_bytecode = True
            for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
                os.environ[name] = '1'
            record['thread_environment'] = {name: os.environ[name] for name in
                                            ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')}
            record['executable'] = file_identity(sys.executable)
            record['probe'] = file_identity(__file__)
            root = args.source_root.resolve()
            source_ids = []
            for name, expected in SOURCE_DIGESTS.items():
                item = file_identity(root / name)
                require(item['sha256'] == expected, 'Frozen import source mismatch: ' + name)
                source_ids.append(dict(item, relative_path=name))
                for parent in Path(name).parents:
                    initializer = parent / '__init__.py'
                    require(str(initializer) in SOURCE_DIGESTS or not (root / initializer).exists(),
                            'Unexpected eager package initializer: ' + str(initializer))
                    require(not list((root / parent / '__pycache__').glob('*.pyc')),
                            'Source tree contains cached bytecode: ' + str(parent))
            record['verified_import_sources'] = source_ids
            # Do not merge namespace packages with another checkout on sys.path.
            excluded, paths = [], []
            for entry in sys.path:
                directory = Path(entry or os.getcwd()).resolve()
                if directory == root:
                    continue
                if (directory / 'envs').exists() or (directory / 'experiments').exists():
                    excluded.append(str(directory))
                else:
                    paths.append(entry)
            sys.path[:] = [str(root), *paths]
            record['excluded_other_code_roots'] = excluded
            import numpy as np
            import torch
            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)
            features_module = importlib.import_module('experiments.candidates.uav_service_age.b01.features')
            learner_module = importlib.import_module('experiments.candidates.uav_service_age.b01.learner')
            for item in source_ids:
                name = item['relative_path'].removesuffix('.py').replace('/', '.').removesuffix('.__init__')
                require(Path(sys.modules[name].__file__).resolve() == root / item['relative_path'],
                        'Module import escaped frozen root: ' + name)
            require('envs.pettingzoo.uav_env' not in sys.modules, 'Unexpected environment module import')
            record['runtime'] = dict(numpy=np.__version__, torch=torch.__version__,
                torch_build=torch.__config__.show(), torch_threads=torch.get_num_threads(),
                torch_interop_threads=torch.get_num_interop_threads(),
                module_files=[file_identity(path) for path in (np.__file__, torch.__file__, torch._C.__file__,
                    importlib.import_module('numpy.core._multiarray_umath').__file__)])
            spec = features_module.FEATURE_SPEC
            require(spec['dim'] == features_module.FEATURE_DIM == 635 and spec['dtype'] == 'float32',
                    'Frozen FEATURE_SPEC differs from declared635 float32 contract')
            require(sum(field['stop'] - field['start'] for field in spec['fields']) == 635,
                    'Feature specification field dimension mismatch')
            record['feature_spec'] = spec
            record['checks']['frozen_sources_and_feature_spec'] = True
            global_rng_before = torch.get_rng_state().clone()
            first = learner_module.Learner(spec['dim'], seed=701)
            require(torch.equal(global_rng_before, torch.get_rng_state()), 'fork_rng initializer advanced global Torch RNG')
            record['initializers'] = dict(actor=learner_module.parameter_digest(first.actor),
                                         critic=learner_module.parameter_digest(first.critic))
            no_optimizer_updates(first)
            record['innovations'] = {label: array_identity(np, learner_module.innovations(705, training=training))
                                     for label, training in (('train', True), ('eval', False))}
            require(record['innovations']['train'] != record['innovations']['eval'], 'Innovation train/eval fixture streams alias')
            fixture = (((np.arange(64 * spec['dim'], dtype=np.int64).reshape(64, spec['dim']) % 997) - 498)
                       .astype(np.float32) / np.float32(499))
            require(fixture.shape == (64, 635) and bool(np.isfinite(fixture).all()), 'Invalid finite synthetic features')
            record['features'] = array_identity(np, fixture)
            with torch.no_grad():
                head = first.actor[2]
                head.weight.copy_((torch.arange(head.weight.numel(), dtype=torch.float32).reshape_as(head.weight) % 17 - 8) / 512)
                head.bias.copy_(torch.tensor([-.05, .07], dtype=torch.float32))
            record['fixture_edit'] = 'actor final weights=(arange%17-8)/512; bias=[-.05,.07]; direct no_grad, no training'
            probabilities = np.stack([first.probabilities(row) for row in fixture])
            values = first.values(fixture)
            require(bool(np.isfinite(probabilities).all() and np.isfinite(values).all()), 'Nonfinite fixture predictions')
            require(float(np.max(np.abs(probabilities - .5))) > 1e-4, 'Actor head fixture remains vacuous')
            require(learner_module.parameter_digest(first.actor) != record['initializers']['actor'], 'Actor fixture edit did not move weights')
            payload = first.state()
            require(set(payload) == {'actor', 'critic', 'input_dim', 'actor_updates', 'critic_updates',
                                     'episodes_updated', 'actor_sha256', 'critic_sha256'}, 'Unexpected checkpoint payload contract')
            scalar_payload = {key: value for key, value in payload.items() if key not in ('actor', 'critic')}
            checkpoint = args.out / 'evaluation_fixture.pt'
            torch.save(payload, checkpoint)
            record['checkpoint_file'] = file_identity(checkpoint)
            loaded = torch.load(checkpoint, weights_only=True, map_location='cpu')
            require(set(loaded) == set(payload), 'Loaded checkpoint keys mismatch')
            for key, expected in scalar_payload.items():
                require(type(loaded[key]) is type(expected) and loaded[key] == expected,
                        'Loaded checkpoint scalar mismatch: ' + key)
            replacement_rng = torch.get_rng_state().clone()
            restored = learner_module.Learner(spec['dim'], seed=702)
            require(torch.equal(replacement_rng, torch.get_rng_state()), 'Replacement initializer advanced global Torch RNG')
            record['replacement_initializers'] = dict(actor=learner_module.parameter_digest(restored.actor),
                                                       critic=learner_module.parameter_digest(restored.critic))
            require(record['replacement_initializers']['critic'] != record['initializers']['critic'],
                    'Replacement fixture seed did not change critic initialization')
            tensor_ids = {}
            for label in ('actor', 'critic'):
                require(set(loaded[label]) == set(payload[label]), 'Loaded network tensor keys mismatch: ' + label)
                getattr(restored, label).load_state_dict(loaded[label], strict=True)
                for name, expected in payload[label].items():
                    same_tensor(torch, expected, loaded[label][name], label + '/' + name + '/loaded')
                    actual = getattr(restored, label).state_dict()[name]
                    same_tensor(torch, expected, actual, label + '/' + name + '/restored')
                    tensor_ids[label + '/' + name] = array_identity(np, actual.detach().numpy())
            for key in ('input_dim', 'actor_updates', 'critic_updates', 'episodes_updated'):
                setattr(restored, key, loaded[key])
            restored_payload = restored.state()
            require({key: value for key, value in restored_payload.items() if key not in ('actor', 'critic')} == scalar_payload,
                    'Restored scalar/digest payload mismatch')
            restored_probabilities = np.stack([restored.probabilities(row) for row in fixture])
            restored_values = restored.values(fixture)
            require(array_identity(np, probabilities) == array_identity(np, restored_probabilities),
                    'Restored probability dtype/shape/bytes differ')
            require(array_identity(np, values) == array_identity(np, restored_values),
                    'Restored critic value dtype/shape/bytes differ')
            require(record['features'] == array_identity(np, fixture), 'Synthetic input features mutated')
            require(torch.equal(global_rng_before, torch.get_rng_state()), 'Fixture changed global Torch RNG')
            no_optimizer_updates(first)
            no_optimizer_updates(restored)
            record['content'] = dict(scalar_payload=scalar_payload, tensors=tensor_ids,
                probabilities=array_identity(np, probabilities), probabilities_values=probabilities.tolist(),
                critic_values=array_identity(np, values), critic_values_values=values.tolist())
            record['stdlib_random_fixture'] = hashlib.sha256(json.dumps(
                [random.Random(705).getstate()], separators=(',', ':')).encode()).hexdigest()
            record['checks'].update(nonzero_actor_head=True, fork_rng_preserved=True,
                all_loaded_and_restored_tensors_exact=True, scalar_payload_exact=True,
                parameter_digests_exact=True, probabilities_exact=True, critic_values_exact=True,
                zero_gradients_optimizer_states_and_steps=True)
            emit('PASS')
        except BaseException:
            record['exception'] = traceback.format_exc()
            emit('FAIL')
            raise
        finally:
            faulthandler.disable()
    print(json.dumps(dict(status=record['status'], summary=str(args.out / 'summary.json'))), flush=True)


if __name__ == '__main__':
    main()
