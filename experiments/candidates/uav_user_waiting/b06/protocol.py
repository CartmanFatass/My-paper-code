"""Fixed B06 identity and byte-bound inputs; no planner truth interface."""

import hashlib
import json
from importlib.metadata import version
from pathlib import Path
import platform
import sys

import numpy as np

from experiments.candidates.uav_user_waiting.b05.protocol import file_identity, write_json

ROOT = Path(__file__).resolve().parents[4]
OBJECT = 'UAV-USER-WAITING-B06'
PROGRAM = 'S_F'
SEED, WORLDS, HORIZON, N, U = 29426000, 64, 256, 5, 50
SEEDS = tuple(range(SEED, SEED + WORLDS))
REFERENCES = ('S:LRS', 'M:LRS', 'U:LRS')
BOOTSTRAP_SEED, BOOTSTRAP_RESAMPLES = 29426998, 10000
T_CRITICAL, ATOL = 1.998340542520741, 1e-12
B04_RESULT = 'runs/uav_user_waiting/b04_service_floor_a01/result.json'
B05_RESULT = 'runs/uav_user_waiting/b05_local_allocation_a02/result.json'
B04_SHA256 = 'ccd52d06fe48c7e3f5315b834cb702e1b22b826df25af68a6e2eeb7e3a09707a'
B05_SHA256 = '5a3fb0e095c9e52a1954ea7b6ebfac561b0aeedd5f8fee4d6df8fe35ea8262f0'
B04_SOURCE = 'dd3b2577d407b57a3b76ea4ba95b6ead4349d0d4'
B05_SOURCE = '4de05b0da41827cf945587003a2476584dac480e'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def baseline_directory(output):
    """Declared external staging, anchored to the kernel's canonical output.

    A snapshot relocates source arguments, while --out remains under the
    author checkout. No baseline payload is copied into the source snapshot.
    """
    output = Path(output)
    require(output.is_absolute() and output.parent.name == 'uav_user_waiting' and
            output.parent.parent.name == 'runs', 'canonical absolute direction output required')
    return output.parents[2] / 'temp/directions/uav_user_waiting/b06/baseline_s'


def relative_identity(path, root=ROOT):
    path, root = Path(path), Path(root)
    identity = file_identity(path)
    return dict(path=str(path.relative_to(root)), bytes=identity['bytes'], sha256=identity['sha256'])


def _bound_json(relative, digest, root):
    path = Path(root) / relative
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == digest, 'baseline result hash mismatch: ' + relative)
    return json.loads(data), dict(path=relative, bytes=len(data), sha256=digest)


def load_baselines(baseline_s, *, root=ROOT, verify_staging=True):
    """Only immutable metadata/bytes; never recompute an old outcome or policy."""
    baseline_s = Path(baseline_s).resolve(strict=True)
    b04, id04 = _bound_json(B04_RESULT, B04_SHA256, root)
    b05, id05 = _bound_json(B05_RESULT, B05_SHA256, root)
    require(b04['status'] == b05['status'] == 'VERIFIED_COMPLETE', 'incomplete bound baseline')
    require(b04['launch_sha'] == B04_SOURCE and b05['launch_sha'] == B05_SOURCE,
            'wrong frozen baseline source')
    originals = {row['seed']: row for row in b04['rows'] if row['arm'] == 'S'}
    require(len(originals) == WORLDS and set(originals) == set(SEEDS), 'S source panel differs')
    fair = {}
    for row in b05['rows']:
        if row['package'] in REFERENCES:
            key = (row['package'], row['seed'])
            require(key not in fair, 'duplicate fair reference')
            shared = b05['path_records'][f"{row['program']}:{row['seed']}"]['shared']
            fair[key] = dict(row, inherited=shared['inherited'])
    require(set(fair) == {(package, seed) for package in REFERENCES for seed in SEEDS},
            'fair reference panel differs')
    staged = {}
    for seed in SEEDS:
        expected = originals[seed]['raw']
        name = f'S_{seed}.npz'
        require(Path(expected['path']).name == name, 'baseline raw name differs')
        path = baseline_s / name
        identity = dict(path=str(path), canonical_path=expected['path'],
                        bytes=expected['bytes'], sha256=expected['sha256'])
        if verify_staging:
            actual = file_identity(path)
            require(all(actual[key] == identity[key] for key in ('bytes', 'sha256')),
                    'staged baseline mismatch: ' + name)
        staged[seed] = identity
    bindings = []
    for expected in b04['config']['source_identities']:
        name = expected['path']
        if not name.startswith(('experiments/', 'envs/')):
            continue  # Current launch controls are recorded, not frozen scientific inputs.
        actual = relative_identity(Path(root) / name, root)
        require(all(actual[key] == expected[key] for key in ('bytes', 'sha256')),
                'frozen B04 scientific dependency changed: ' + name)
        bindings.append(actual)
    for expected in b05['config']['source_identities']:
        name = expected['relative_path']
        actual = relative_identity(Path(root) / name, root)
        require(all(actual[key] == expected[key] for key in ('bytes', 'sha256')),
                'frozen B05 allocation/reader dependency changed: ' + name)
        bindings.append(actual)
    metadata = dict(b04_result=id04, b05_result=id05, b04_source=B04_SOURCE, b05_source=B05_SOURCE,
                    b04_runtime=b04.get('runtime'), b05_runtime=b05.get('runtime'),
                    baseline_s_dir=str(baseline_s), baseline_s=[staged[seed] for seed in SEEDS],
                    frozen_scientific_bindings=bindings)
    return originals, fair, staged, metadata


def load_raw(identity, fields=None):
    """Hash and decompress the same open descriptor; outputs never use pickle."""
    with Path(identity['path']).open('rb') as stream:
        digest, size = hashlib.sha256(), 0
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
        require(size == identity['bytes'] and digest.hexdigest() == identity['sha256'],
                'raw identity mismatch: ' + identity['path'])
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as archive:
            names = archive.files if fields is None else fields
            return {name: archive[name].copy() for name in names}


def source_identities(root=ROOT):
    paths = sorted((Path(root) / 'experiments/candidates/uav_user_waiting/b06').glob('*.py'))
    paths += [Path(root) / '.codex/hmasd-compute.toml', Path(root) / 'scripts/hmasd_admission.py']
    return [relative_identity(path, root) for path in paths]


def frozen_config(launch_sha, metadata, *, root=ROOT):
    return dict(object=OBJECT, launch_sha=launch_sha, program=PROGRAM, law='LRS',
        seeds=list(SEEDS), seed_order='ascending', references=list(REFERENCES), horizon=HORIZON,
        nodes=N, users=U, capacity=10, min_sinr=3., planned_fits=0, planned_targets=0,
        planned_optimizer_updates=0, planned_episodes=WORLDS, planned_native_steps=WORLDS * HORIZON,
        native_pilot_episodes=0, new_baseline_trajectories=0,
        delivery_ticks=2, hold_ticks=4, round_bytes=141, map_bytes=400,
        transmission_seconds=.564, deadline_seconds=1.436,
        search='S two coordinate orders; 116 pre-cache requests; rotating member; unchanged current C',
        model='exact B05 local LRS; own int64[5,50] timestamps; all global history and native ties from grants',
        information='rounded registered map and decoded reports/executed ledger only; no evaluator truth or grant ACK',
        native='unchanged greedy measurement collector; no grant feedback; LRS outcome from saved SINR',
        dtype='float64 radio/forecast; float32 native commands/observation; int64 modeled ages/timestamps',
        primary='S_F:LRS-S:LRS mean episode maximum unserved gap; negative is favorable',
        scope='adaptively reused development worlds; descriptive paired uncertainty; no confirmation',
        activation='first executed command OR transmitter mask divergence while saved S histories coincide',
        bootstrap=dict(seed=BOOTSTRAP_SEED, resamples=BOOTSTRAP_RESAMPLES,
                       metrics=['max_unserved_gap', 'F_user', 'mean_served']),
        t_critical=T_CRITICAL, floating_atol=ATOL,
        runtime=dict(python=platform.python_version(), numpy=np.__version__, torch=version('torch'),
                     byteorder=sys.byteorder, platform=platform.platform()),
        upper_work=dict(candidate_requests=475136, candidate_fleet_ticks=1885696,
                        prefix_fleet_ticks=8192, settlement_fleet_ticks=16384,
                        manager_fleet_ticks=1910272, local_lrs_row_selections=9551360,
                        candidate_geometry_snapshots=438912, worker_c_calls=20480,
                        reader_c_calls=40960, future_c_calls=0),
        physics_check_reports=[0, 60, 124, 248],
        reader='all native/LRS outcomes and local-state/key/search arithmetic; each winner and fixed-report all-candidate physics/priority',
        baseline=metadata, source_identities=source_identities(root))
