"""Frozen B07 panel, lawful interface and immutable reference identities."""

import hashlib
import json
from importlib.metadata import version
from pathlib import Path
import platform
import sys

import numpy as np

from experiments.candidates.uav_user_waiting.b05.protocol import file_identity, write_json
from experiments.candidates.uav_user_waiting.b06.protocol import load_raw, relative_identity, require

ROOT = Path(__file__).resolve().parents[4]
OBJECT, PROGRAM = 'UAV-USER-WAITING-B07', 'C2'
SEED, WORLDS, HORIZON, N, U = 29426000, 64, 256, 5, 50
SEEDS = tuple(range(SEED, SEED + WORLDS))
REFERENCES = ('S_F:LRS', 'S:LRS', 'M:LRS', 'U:LRS')
BOOTSTRAP_SEED, BOOTSTRAP_RESAMPLES = 29426998, 10000
T_CRITICAL, ATOL = 1.998340542520741, 1e-12
B06_RESULT = 'runs/uav_user_waiting/b06_fair_model_a01/result.json'
B06_SHA256 = '9aedf05ccfa2f19677680c62c8258d5dc02b662eefc33f130776da6ad8a4b212'
B06_SOURCE = '69347051d55f31cc8a5c9ed71239aabd5d1d9ee6'
B05_RESULT = 'runs/uav_user_waiting/b05_local_allocation_a02/result.json'
B05_SHA256 = '5a3fb0e095c9e52a1954ea7b6ebfac561b0aeedd5f8fee4d6df8fe35ea8262f0'
B05_SOURCE = '4de05b0da41827cf945587003a2476584dac480e'


def baseline_directory(output):
    output = Path(output)
    require(output.is_absolute() and output.parent.name == 'uav_user_waiting' and
            output.parent.parent.name == 'runs', 'canonical absolute direction output required')
    return output.parents[2] / 'runs/uav_user_waiting/b06_fair_model_a01/raw'


def _bound_json(path, digest):
    data = Path(path).read_bytes()
    require(hashlib.sha256(data).hexdigest() == digest, 'reference hash mismatch: ' + str(path))
    return json.loads(data), dict(path=str(path), bytes=len(data), sha256=digest)


def _relocated_identity(expected, canonical_root):
    original = Path(expected['path'])
    parts = original.parts
    require('runs' in parts, 'reference outside runs')
    relative = Path(*parts[parts.index('runs'):])
    return dict(expected, path=str(Path(canonical_root) / relative), canonical_path=str(original))


def load_baselines(baseline_sf, *, root=ROOT, verify_payloads=True):
    """Read immutable full outcomes; no old allocation, policy or outcome reduction."""
    baseline_sf = Path(baseline_sf).resolve(strict=True)
    canonical_root = baseline_sf.parents[3]
    sf, id06 = _bound_json(Path(root) / B06_RESULT, B06_SHA256)
    old, id05 = _bound_json(Path(root) / B05_RESULT, B05_SHA256)
    require(sf['status'] == old['status'] == 'VERIFIED_COMPLETE', 'incomplete references')
    require(sf['launch_sha'] == B06_SOURCE and old['launch_sha'] == B05_SOURCE, 'reference source differs')
    originals = {row['seed']: row for row in sf['rows']}
    require(set(originals) == set(SEEDS) and len(sf['rows']) == WORLDS, 'SF panel differs')
    fair, payloads = {}, []
    for row in sf['rows'] + old['rows']:
        if row['package'] not in REFERENCES:
            continue
        key = (row['package'], row['seed'])
        require(key not in fair, 'duplicate reference outcome')
        if row['program'] == 'S_F':
            inherited = row['inherited']
        else:
            inherited = old['path_records'][f"{row['program']}:{row['seed']}"]['shared']['inherited']
        expected = (row['outcome'] if row['program'] == 'S_F' else
                    old['path_records'][f"{row['program']}:{row['seed']}"]['shared']['outcome'])
        identity = _relocated_identity(expected, canonical_root)
        if verify_payloads:
            data, actual = _bound_json(identity['path'], identity['sha256'])
            require(actual['bytes'] == identity['bytes'], 'reference outcome bytes differ')
            if row['program'] != 'S_F':
                matches = [item for item in data['rows'] if item['law'] == 'LRS']
                require(len(matches) == 1, 'missing LRS in old full outcome')
                data = matches[0]
            require(data['package'] == key[0] and data['seed'] == key[1], 'reference outcome identity differs')
            fair[key] = dict(data, inherited=inherited, outcome=identity)
        else:
            fair[key] = dict(row, inherited=inherited, outcome=identity)
        payloads.append(identity)
    require(set(fair) == {(package, seed) for package in REFERENCES for seed in SEEDS}, 'fair panel differs')
    staged = {}
    for seed, row in originals.items():
        expected = row['raw']
        path = baseline_sf / f'S_F_{seed}.npz'
        require(path.name == Path(expected['path']).name, 'SF raw name differs')
        identity = dict(expected, path=str(path), canonical_path=expected['path'])
        if verify_payloads:
            actual = file_identity(path)
            require(all(actual[key] == identity[key] for key in ('bytes', 'sha256')), 'SF raw identity differs')
        staged[seed] = identity
    bindings = {}
    for expected in sf['config']['baseline']['frozen_scientific_bindings'] + sf['config']['source_identities']:
        name = expected['path']
        if not name.startswith(('experiments/', 'envs/')):
            continue
        actual = relative_identity(Path(root) / name, root)
        require(all(actual[key] == expected[key] for key in ('bytes', 'sha256')), 'frozen scientific dependency changed: ' + name)
        bindings[name] = actual
    metadata = dict(b06_result=dict(id06, path=B06_RESULT), b05_result=dict(id05, path=B05_RESULT),
        b06_source=B06_SOURCE, b05_source=B05_SOURCE, baseline_sf_dir=str(baseline_sf),
        baseline_sf=[staged[seed] for seed in SEEDS], reference_outcomes=payloads,
        frozen_scientific_bindings=[bindings[key] for key in sorted(bindings)])
    return originals, fair, staged, metadata


def source_identities(root=ROOT):
    paths = sorted((Path(root) / 'experiments/candidates/uav_user_waiting/b07').glob('*.py'))
    paths += [Path(root) / '.codex/hmasd-compute.toml', Path(root) / 'scripts/hmasd_admission.py']
    return [relative_identity(path, root) for path in paths]


def frozen_config(launch_sha, metadata, *, root=ROOT):
    return dict(object=OBJECT, program=PROGRAM, launch_sha=launch_sha, law='LRS',
        seeds=list(SEEDS), seed_order='ascending', references=list(REFERENCES), horizon=HORIZON,
        nodes=N, users=U, capacity=10, min_sinr=3., planned_fits=0, planned_targets=0,
        planned_optimizer_updates=0, planned_episodes=WORLDS, planned_native_steps=WORLDS*HORIZON,
        native_pilot_episodes=0, new_baseline_trajectories=0, future_c_calls=0,
        delivery_ticks=2, hold_ticks=4, round_bytes=141, map_bytes=400,
        transmission_seconds=.564, deadline_seconds=1.436,
        search='15 one/two-bit masks in integer order; unchanged current C104 proposals/private navigation',
        key=['sum_slot_member_min(10,eligible_count)', 'distinct_eligible_users', '-flips_from_entering_mask', '-mask'],
        model='two clipped entering-command kinematic ticks; L=min(4,H-t-2) current-proposal trajectory; no modeled ages/grants/history',
        information='400B rounded registered map and decoded 5x25B reports only; no grant ACK, age, true sites, seed or future C',
        native='unchanged greedy physical measurement; grant-independent dynamics; offline local LRS from saved native SINR',
        fallback='late whole C+manager round retains BOTH commands and mask; empty delivered command; partial work charged',
        dtype='float64 radio/forecast; float32 native commands/observation; int64 actual LRS timestamps/ages',
        primary='C2:LRS-S_F:LRS mean episode maximum unserved gap; negative favorable',
        activation='first executed command OR mask divergence versus saved SF while histories coincide',
        scope='adaptively reused development worlds; descriptive uncertainty; no confirmation/equivalence/adoption rule',
        bootstrap=dict(seed=BOOTSTRAP_SEED, resamples=BOOTSTRAP_RESAMPLES, metrics=['max_unserved_gap','F_user','mean_served']),
        t_critical=T_CRITICAL, floating_atol=ATOL,
        upper_work=dict(rounds=4096, candidate_requests=61440, candidate_plans=61440,
            candidate_fleet_ticks=243840, candidate_sinr_entries=60960000, geometry_snapshots=16256,
            geometry_link_entries=4064000, prefix_kinematic_ticks=8192, worker_c_calls=20480,
            reader_c_calls=40960, reader_all_candidate_fleet_ticks=243840, native_steps=16384,
            native_lrs_row_selections=81920, native_lrs_user_age_updates=819200),
        reader='all native/report/C/delivery records; independent full15-mask physics each round; native local LRS and all censored gaps; all four immutable reference outcomes',
        runtime=dict(python=platform.python_version(), numpy=np.__version__, torch=version('torch'), byteorder=sys.byteorder, platform=platform.platform()),
        baseline=metadata, source_identities=source_identities(root))
