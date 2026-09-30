"""Fixed collection and compact records; evaluator truth never enters actors."""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import LocalController
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from .controller import MotionController

SEEDS = tuple(range(29401000, 29401032))
ARMS = ('C', 'V', 'R')
ORDERS = (('C', 'V', 'R'), ('C', 'R', 'V'), ('V', 'C', 'R'),
          ('V', 'R', 'C'), ('R', 'C', 'V'), ('R', 'V', 'C'))
HORIZON = 256
DIRECTION = 'uav_local_peer_forecast'
ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATHS = (
    'experiments/candidates/uav_local_peer_forecast/__init__.py',
    'experiments/candidates/uav_local_peer_forecast/controller.py',
    'experiments/candidates/uav_local_peer_forecast/study.py',
    'experiments/candidates/uav_local_peer_forecast/reader.py',
    'experiments/candidates/uav_local_peer_forecast/run.py',
    'experiments/candidates/uav_local_history/b01/controller.py',
    'experiments/candidates/ucope/uav_motion_prefix_b01/environment.py',
    'envs/pettingzoo/uav_env.py', 'envs/pettingzoo/uav_radio.py',
    'envs/pettingzoo/env_adapter.py',
)
FROZEN_BLOBS = {
    'experiments/candidates/uav_local_history/b01/controller.py': '9c98f540f74e4d4605dce84a797e6b932cd9cb50',
    'experiments/candidates/ucope/uav_motion_prefix_b01/environment.py': '4b59281bfb76245dd3283fe860327e35463c2b26',
    'envs/pettingzoo/uav_env.py': '1e67c3a56fc1824db968485366dadcc54c7d8125',
    'envs/pettingzoo/uav_radio.py': 'cf7cdbf3562e78e41bc06d32f733e806d7190313',
    'envs/pettingzoo/env_adapter.py': '58da35c3263e00319d90b93169a6d14b0f7e5bda',
}


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    os.replace(temporary, path)


def identity(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest())


def source_binding(sha):
    if len(sha) != 40 or any(c not in '0123456789abcdef' for c in sha):
        raise ValueError('launch SHA must be a full lowercase revision')
    manifest = []
    for relative in SOURCE_PATHS:
        path = ROOT / relative
        recorded = subprocess.check_output(['git', 'show', f'{sha}:{relative}'], cwd=ROOT)
        if path.read_bytes() != recorded:
            raise RuntimeError(f'working source differs from launch source: {relative}')
        blob = hashlib.sha1(b'blob ' + str(len(recorded)).encode() + b'\0' + recorded).hexdigest()
        if relative in FROZEN_BLOBS and blob != FROZEN_BLOBS[relative]:
            raise RuntimeError(f'frozen shared source changed: {relative}')
        item = identity(path)
        item.update(path=relative, git_blob=blob)
        manifest.append(item)
    return manifest


def resources(wall_started, cpu_started):
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return dict(wall_seconds=time.perf_counter() - wall_started,
                process_cpu_seconds=time.process_time() - cpu_started,
                peak_rss_kib=int(usage.ru_maxrss), peak_rss_scope='process lifetime Linux',
                input_blocks=int(usage.ru_inblock), output_blocks=int(usage.ru_oublock))


def collect_episode(env, arm, seed, out, counts, *, horizon=HORIZON):
    """Only called by admitted runner or bounded non-native correctness fixtures."""
    wall, cpu = time.perf_counter(), time.process_time()
    counts['started_episodes'] += 1
    counts['explicit_resets'] += 1
    obs, info = env.reset(seed=seed)
    state = info['state_info']
    users = np.array(state['user_positions'], dtype=np.float64, copy=True)
    initial = np.array(state['uav_positions'], dtype=np.float64, copy=True)
    actors = [LocalController(history=False) if arm == 'C' else MotionController(arm)
              for _ in range(5)]
    raw = dict(observations=[np.array(obs, copy=True)], positions=[initial],
               commands=[], reward=[], agent_rewards=[], served=[], quality=[],
               connections=[], native_sinr=[], selected_index=[], fallback=[], nav_before=[],
               nav_after=[], n=[], p=[], m=[], matches=[], delta=[], gate_counts=[],
               scores=[], candidate_service=[])
    actor_cpu = actor_wall = 0.
    try:
        for t in range(horizon):
            if np.asarray(obs).shape != (5, 104) or not np.isfinite(obs).all():
                raise ValueError('invalid five-row local interface')
            if not np.array_equal(np.asarray(obs)[:, 103], np.full(5, t / 256)):
                raise ValueError('observation clock differs')
            before = [-1 if a._nav_index is None else a._nav_index for a in actors]
            commands, diagnostics = [], []
            w, c = time.perf_counter(), time.process_time()
            try:
                for i, actor in enumerate(actors):
                    ingests, decisions = actor.counters['ingests'], actor.counters['decisions']
                    try:
                        command, diag = actor.act(np.array(obs[i], copy=True), t)
                        commands.append(command)
                        diagnostics.append(diag)
                    finally:
                        counts['actor_ingests'] += actor.counters['ingests']-ingests
                        counts['rankings'] += actor.counters['decisions']-decisions
            finally:
                actor_wall += time.perf_counter() - w
                actor_cpu += time.process_time() - c
            commands = np.asarray(commands, dtype=np.float32)
            if commands.shape != (5, 3) or not np.isin(commands, (-1, 0, 1)).all():
                raise ValueError('invalid primitive commands')
            raw['commands'].append(commands)
            raw['nav_before'].append(before)
            raw['nav_after'].append([a._nav_index for a in actors])
            for name in ('selected_index', 'fallback'):
                raw[name].append([d[name] for d in diagnostics])
            raw['n'].append([d['n_current'] for d in diagnostics])
            raw['p'].append([d['n_visible_peers'] for d in diagnostics])
            matches = np.full((5, 4), -1, dtype=np.int64)
            delta = np.zeros((5, 4, 3))
            gates = np.zeros((5, 4), dtype=np.int64)
            for i, d in enumerate(diagnostics):
                if arm != 'C':
                    p = d['n_visible_peers']
                    matches[i, :p], delta[i, :p], gates[i, :p] = d['matches'], d['delta'], d['gate_counts']
            raw['matches'].append(matches)
            raw['delta'].append(delta)
            raw['gate_counts'].append(gates)
            raw['m'].append(np.any(delta != 0, axis=-1).sum(axis=1))
            if t % 4 == 0:
                raw['scores'].append([d['scores'] for d in diagnostics])
                raw['candidate_service'].append([d['served_candidates'] for d in diagnostics])
            counts['native_steps_attempted'] = counts.get('native_steps_attempted', 0)+1
            obs, _, terminated, truncated, info = env.step(commands.copy())
            counts['native_steps'] += 1
            if bool(terminated or truncated) != (t + 1 == horizon):
                raise RuntimeError('unexpected native termination/truncation')
            global_info = info['infos_dict']['uav_0']['global']
            connections = np.array(global_info['connections'], dtype=bool, copy=True)
            sinr = np.array(global_info['sinr_matrix'], dtype=np.float64, copy=True)
            served = int(global_info['served_users'])
            quality = np.clip((sinr[connections] - 3.) / 30., 0., 1.).sum() / max(served, 1)
            rewards = [float(info['rewards_dict'][f'uav_{i}']) for i in range(5)]
            reward = sum(rewards)
            if served != int(connections.sum()) or not np.isclose(
                    reward, .7 * served / 50 + .3 * quality, rtol=0, atol=1e-12):
                raise RuntimeError('native endpoint telemetry inconsistent')
            raw['observations'].append(np.array(obs, copy=True))
            raw['positions'].append(np.array(info['state_info']['uav_positions'], copy=True))
            for name, value in dict(reward=reward, agent_rewards=rewards, served=served,
                                    quality=quality, connections=connections, native_sinr=sinr).items():
                raw[name].append(value)
    finally:
        # Preserve partial native/actor data and counts on failure, without a success row.
        arrays = {key: np.asarray(value) for key, value in raw.items()}
        keys = sorted(set().union(*(a.counters for a in actors)))
        arrays.update(users=users, arm=np.array(arm), seed=np.array(seed),
                      counter_keys=np.array(keys),
                      counters=np.array([[a.counters.get(k, 0) for k in keys] for a in actors]))
        arrays.update(actor_cpu_seconds=np.array(actor_cpu), actor_wall_seconds=np.array(actor_wall))
        path = Path(out) / 'raw' / f'{arm}_{seed}.npz'
        np.savez_compressed(path, **arrays)
    counts['complete_episodes'] += 1
    return dict(arm=arm, seed=seed, steps=horizon, raw=identity(path),
                actor_cpu_seconds=actor_cpu, actor_wall_seconds=actor_wall,
                telemetry=resources(wall, cpu),
                controller_counts={k: int(arrays['counters'][:, j].sum()) for j, k in enumerate(keys)})
