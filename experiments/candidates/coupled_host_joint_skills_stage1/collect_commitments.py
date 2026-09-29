"""P3 commitment table for coupled_host_joint_skills_stage1 b01 (T4, disposition item 5).

One final H checkpoint -> one table of ten-step commitments, at frozen weights and normalisers
with zero optimizer steps.

Construction.  The agent is rebuilt through ``configuration.make_config`` + ``models.build_agent``
(arm H, the fit's spec) and loaded strictly from the checkpoint's ``modules`` / ``normalizers``
(keys, shapes and a bitwise round trip checked; normalisers restored by the fresh instance's
attribute types and compared as ``jsonable(vars(norm))``), then ``train(False)``.  Every
optimizer ``step`` is replaced by a refusal and post-step hooks count calls (must stay zero);
the parameter/normaliser digest (``runner.digest_agent``) is equal before and after.  The
collection runs inside ``runner.preserve_rng`` and records the global RNG digest before/after.

Worlds.  The fit's own training-world law continued after the fit: collection rollout ``r``,
lane ``l`` runs world ``training_world_seed(seed, l, spec.rollouts + 1 + r)`` (episodes 46..61
for the declared 45-rollout fit; never a panel world).  Actions are sampled
(``deterministic=False``), as in training.  Sampling RNG: ``runner.seed_rng(s_r)`` at the start
of rollout ``r`` with ``s_r = int.from_bytes(sha256(f"{seed}:t4-collect:rollout{r}")[:8],
"big") % 2**31`` (T4 rule; not a scientific choice).

Unit.  At every d2 team decision (cause reset at t = 0, team_cap at t = 10, 20, ..., 490; any
other cause is an error) one row: world/lane/rollout/episode/t0, the pre-commitment state (133)
and observation rows (6 x 90), ``team_label``, ``agent_labels[6]``, pre-commitment roles from
``env.snapshot()`` at t0 (routed; relay = interior node of another UAV's BS path; users served;
``relay_matrix[i, j]`` = UAV i is an interior node of UAV j's BS path), the pre-commitment
``C_bh`` and ``S/D`` (computed from the host state at t0 with the host's own formula; for
t0 > 0 cross-checked against the previous step's contract readers), then the segment's policy
actions and executed (unit-ball clipped, the host rule) actions, the ten time-aligned contract
rewards (team r), C_bh and S/D per step, and ``segment_mean_r``.  Asserted: exactly 50
commitments per lane-episode; both label vectors re-read every step and equal within a segment.

Structural zero check (reported in ``meta.json``; the reader copies it).  On up to 200 stored
pre-commitment rows of rollout 0 (evenly spaced), the actor path
(``HMASDAgent._batched_select_action``) is run with identical state, observations, individual
labels and pre-commitment actor hidden state and every other team label; the executed action
must not change (deterministic and sampled at a fixed torch seed).  Code fact: in arm H the
actor is ``SkillDiscoverer.forward(observation, agent_skill, hidden_state, compact_context=None,
central_input=None)``; the team label reaches only the critic (``get_value``).  A control
(changing agent 0's individual label) reports that the check is not vacuous.

Launch.  ``require_admission`` exactly once in ``main()``; ``--smoke-no-admission`` only for
engineering smokes (non-panel worlds, ``--out`` under ``temp/``; the spec is then read from the
checkpoint's config).  Under a ``--snapshot`` launch pass ``--checkpoint`` relative to the
checkout (``runs/...``): it resolves against the checkout that holds ``runs/``, not the source
worktree; its sha256 is recorded.
"""
from __future__ import annotations

import time
PROCESS_START = time.perf_counter()

import argparse
from dataclasses import asdict, replace
import hashlib
import json
import math
import os
from pathlib import Path
import random
import resource
import sys
import traceback

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from experiments.candidates.coupled_host_joint_skills_stage1 import runner
from experiments.candidates.coupled_host_joint_skills_stage1.adapter import (
    N_UAVS, OBS_DIM, PANEL_WORLD_SET, STATE_DIM, training_world_seed,
)
from experiments.candidates.coupled_host_joint_skills_stage1.configuration import (
    DEFAULT_SPEC, DIRECTION, SEEDS, config_dict, make_config,
)
from scripts.hmasd_admission import require_admission

SCHEMA = 1
K = 10
N_LABELS = 6
TEAM_CAUSE_RESET = 1
TEAM_CAUSE_CAP = 3
DECLARED_ROLLOUTS = 16
DECLARED_LANES = 16
STRUCTURAL_ROWS = 200
STRUCTURAL_TORCH_SEED = 20260929
CLIP_EVENT_TOL = 1e-9  # host.CLIP_EVENT_TOL
PRE_COMMITMENT_TOL = 1e-12
SNAPSHOT_PARENT = "hmasd-launch-sources"
#: Config fields that may differ between the fit's config and the collection config only
#: because the number of lanes differs (smoke only; the declared collection uses the fit's 16).
LANE_DEPENDENT_FIELDS = frozenset({"num_envs", "batch_size", "discriminator_batch_size",
                                   "high_level_batch_size", "high_level_buffer_size",
                                   "num_mini_batch"})


# ------------------------------------------------------------------------------ paths / rng


def canonical_data_root(path):
    """Map a ``--snapshot`` source worktree (``<checkout>/.git/hmasd-launch-sources/<id>``) to the
    checkout holding ``runs/``; any other path is returned unchanged."""
    path = Path(path)
    parts = path.parts
    for index in range(len(parts) - 2):
        if parts[index] == ".git" and parts[index + 1] == SNAPSHOT_PARENT:
            return Path(*parts[:index])
    return path


DATA_ROOT = canonical_data_root(ROOT)


def resolve_input(path):
    """Relative inputs resolve against the checkout holding ``runs/``; absolute paths inside a
    snapshot worktree are mapped back to that checkout."""
    path = Path(path)
    if not path.is_absolute():
        return (DATA_ROOT / path).resolve()
    parts = path.parts
    for index in range(len(parts) - 3):
        if parts[index] == ".git" and parts[index + 1] == SNAPSHOT_PARENT:
            return Path(*parts[:index], *parts[index + 3:]).resolve()
    return path.resolve()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collection_rng_seed(fit_seed, rollout):
    digest = hashlib.sha256(f"{int(fit_seed)}:t4-collect:rollout{int(rollout)}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % 2 ** 31


def rng_digest():
    """Digest of the Python, NumPy and torch global streams (B11's record)."""
    digest = hashlib.sha256()
    digest.update(repr(random.getstate()).encode("utf-8"))
    state = np.random.get_state()
    digest.update(str(state[0]).encode("utf-8"))
    digest.update(np.ascontiguousarray(state[1]).tobytes())
    digest.update(str(state[2:]).encode("utf-8"))
    digest.update(torch.get_rng_state().numpy().tobytes())
    return digest.hexdigest()


def collection_episode_offset(spec):
    return int(spec.rollouts) + 1


def collection_worlds(seed, spec, rollouts, lanes):
    """``worlds[r][l]`` of collection rollout r, lane l (training-world law continued)."""
    offset = collection_episode_offset(spec)
    worlds = [[training_world_seed(int(seed), lane, offset + r) for lane in range(int(lanes))]
              for r in range(int(rollouts))]
    flat = [w for row in worlds for w in row]
    if set(flat) & PANEL_WORLD_SET:
        raise AssertionError("a collection world falls inside a declared panel")
    if len(set(flat)) != len(flat):
        raise AssertionError("collection worlds are not distinct")
    return worlds


# ------------------------------------------------------------------------------ agent load


def forbid_optimizer_steps(agent):
    """Every optimizer ``step`` raises (b05/B12 protection); returns the restore list."""
    restore = []
    for name in runner.OPTIMIZERS:
        optimizer = getattr(agent, name + "_optimizer", None)
        if optimizer is None:
            continue
        original = optimizer.step

        def refuse(*args, _name=name, **kwargs):
            raise RuntimeError(f"the commitment collection took an optimizer step on {_name}")

        optimizer.step = refuse
        restore.append((optimizer, original))
    return restore


def _restore_normalizer(norm, saved, name):
    fresh = vars(norm)
    if set(fresh) != set(saved):
        raise ValueError(f"{name} attributes differ from the checkpoint: {sorted(set(fresh) ^ set(saved))}")
    for key, value in saved.items():
        current = fresh[key]
        if isinstance(current, np.ndarray):
            restored = np.asarray(value, dtype=current.dtype).reshape(current.shape)
        elif isinstance(current, (bool, np.bool_)):
            restored = bool(value)
        elif isinstance(current, (int, np.integer)) and not isinstance(value, float):
            restored = type(current)(value)
        elif isinstance(current, (float, np.floating, int, np.integer)):
            restored = float(value)
        else:
            raise TypeError(f"{name}.{key} has an unsupported type {type(current).__name__}")
        setattr(norm, key, restored)


def spec_from_checkpoint_config(config, area_size):
    """Technical spec for a smoke checkpoint (the declared run always uses the declared spec)."""
    lanes = int(config["num_envs"])
    horizon = int(config["episode_length"])
    rollouts = int(config["total_timesteps"]) // (lanes * horizon)
    return replace(DEFAULT_SPEC, train_lanes=lanes, rollouts=rollouts, horizon=horizon,
                   hidden_size=int(config["hidden_size"]), n_heads=int(config["n_heads"]),
                   n_layers=int(config["n_encoder_layers"]), ppo_epochs=int(config["ppo_epochs"]),
                   sequence_batch_size=int(config["sequence_batch_size"]),
                   coordinator_batch_size=int(config["coordinator_batch_size"]),
                   area_size=int(area_size))


def load_checkpoint_agent(checkpoint, seed, spec, envs, log_dir):
    """Rebuild arm H through the direction factory and load ``checkpoint`` strictly."""
    from experiments.candidates.coupled_host_joint_skills_stage1.models import assert_route, build_agent

    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if payload.get("schema") != 1 or payload.get("direction") != DIRECTION:
        raise ValueError("not a coupled_host_joint_skills_stage1 schema-1 checkpoint")
    saved_config = payload["config"]
    if saved_config.get("contract_arm") != "H":
        raise ValueError("the P3 collection reads arm H checkpoints only")
    if int(payload["rollout"]) != int(spec.rollouts):
        raise ValueError(f"checkpoint rollout {payload['rollout']} is not the final rollout {spec.rollouts}")
    if int(saved_config["seed"]) != int(seed):
        raise ValueError(f"checkpoint seed {saved_config['seed']} != --seed {seed}")
    fit_like = make_config("H", [envs[0]] * int(saved_config["num_envs"]), seed, spec)
    if runner.jsonable(config_dict(fit_like)) != saved_config:
        differing = sorted(k for k, v in runner.jsonable(config_dict(fit_like)).items() if saved_config.get(k) != v)
        raise ValueError(f"the rebuilt fit config differs from the checkpoint's: {differing}")
    config = make_config("H", envs, seed, spec)
    collection_dict = runner.jsonable(config_dict(config))
    excused = sorted(k for k, v in collection_dict.items() if saved_config.get(k) != v)
    if set(excused) - LANE_DEPENDENT_FIELDS:
        raise ValueError(f"collection config differs beyond lane-dependent fields: {excused}")
    agent = build_agent(config, str(log_dir))
    modules = runner.model_modules(agent)
    if set(modules) != set(payload["modules"]):
        raise ValueError(f"module set differs: {sorted(modules)} vs {sorted(payload['modules'])}")
    for name, module in modules.items():
        source = payload["modules"][name]
        target = module.state_dict()
        if target.keys() != source.keys():
            raise ValueError(f"{name} state keys differ from the checkpoint")
        shapes = {k: (tuple(target[k].shape), tuple(source[k].shape)) for k in target
                  if target[k].shape != source[k].shape}
        if shapes:
            raise ValueError(f"{name} state shapes differ from the checkpoint: {shapes}")
        module.load_state_dict(source, strict=True)
    for name in runner.NORMALIZERS:
        saved = payload["normalizers"].get(name)
        norm = getattr(agent, name, None)
        if (saved is None) != (norm is None):
            raise ValueError(f"normaliser {name} presence differs from the checkpoint")
        if norm is not None:
            _restore_normalizer(norm, saved, name)
    agent.train(False)
    for lane in range(len(envs)):
        agent.reset_env_state(lane)
    assert_route(agent, "H")
    # Faithful load: bitwise round trip of every tensor and of the normaliser records.
    mismatched = [f"{name}.{key}" for name, module in modules.items()
                  for key, value in module.state_dict().items()
                  if not torch.equal(value.detach().cpu(), payload["modules"][name][key].detach().cpu())]
    norm_mismatch = [name for name in runner.NORMALIZERS if getattr(agent, name, None) is not None
                     and runner.jsonable(vars(getattr(agent, name))) != payload["normalizers"][name]]
    if mismatched or norm_mismatch:
        raise ValueError(f"checkpoint did not load faithfully: {mismatched[:5]} {norm_mismatch}")
    facts = {"checkpoint_rollout": int(payload["rollout"]),
             "checkpoint_launch_sha": payload.get("launch_sha"),
             "fit_config_equal": True,
             "collection_config_fields_excused_by_lanes": excused,
             "faithful_load": {"tensors_bitwise_equal": True, "normalizers_equal": True,
                               "normalizers_present": [n for n in runner.NORMALIZERS
                                                       if payload["normalizers"].get(n) is not None]},
             "route": assert_route(agent, "H")}
    return agent, config, facts


# ------------------------------------------------------------------------------ host readers


def pre_commitment_terms(host):
    """C_bh and S/D of the host's current state with ``CoupledRelayHost._compute_reward``'s
    formula (read-only: ``_compute_uav_frontend_capacity`` reads ``sinr_matrix`` only)."""
    backhauled, frontend = 0, 0.0
    for i in range(int(host.n_uavs)):
        users = np.flatnonzero(host.connections[i]).tolist()
        if not users:
            continue
        if i in host.routing_paths:
            backhauled += len(users)
            frontend += float(host._compute_uav_frontend_capacity(i, users))
    return backhauled / float(host.n_users), frontend / float(host.contract_denominator_bps)


def roles_from_snapshot(snap, n_uavs=N_UAVS):
    """routed[i], relay[i], serving[i], relay_matrix[i, j] (i interior on j's BS path)."""
    connections = np.asarray(snap["connections"], dtype=bool)
    routed = np.zeros(n_uavs, dtype=bool)
    relay_matrix = np.zeros((n_uavs, n_uavs), dtype=bool)
    for j, path in snap["routing_paths"].items():
        j = int(j)
        if path[0] != ("uav", j) or path[-1][0] != "ground_bs":
            raise AssertionError(f"unexpected routing path {path!r}")
        if not 0 <= len(path) - 2 <= 3:
            raise AssertionError(f"path with {len(path) - 2} relays exceeds max_hops = 3")
        routed[j] = True
        for node_type, node in path[1:-1]:
            if node_type != "uav" or int(node) == j:
                raise AssertionError(f"unexpected interior node in {path!r}")
            relay_matrix[int(node), j] = True
    relay = relay_matrix.any(axis=1)
    serving = connections.sum(axis=1).astype(np.int16)
    return routed, relay, serving, relay_matrix


def executed_actions(actions):
    """The host's unit-ball clip (``host.CoupledRelayHost.step``) applied to a copy."""
    actions = np.asarray(actions, dtype=np.float64)
    norms = np.linalg.norm(actions, axis=-1, keepdims=True)
    clipped = np.where(norms > 1.0, actions / np.maximum(norms, 1e-300), actions)
    events = int(np.sum(norms[..., 0] > 1.0 + CLIP_EVENT_TOL))
    return clipped, events


# ------------------------------------------------------------------------------ table


def allocate_table(n_rows, horizon_steps=K, hidden=None, structural=0):
    table = {
        "world": np.zeros(n_rows, np.int64), "lane": np.zeros(n_rows, np.int16),
        "rollout": np.zeros(n_rows, np.int16), "episode": np.zeros(n_rows, np.int16),
        "t0": np.zeros(n_rows, np.int16),
        "state": np.zeros((n_rows, STATE_DIM), np.float32),
        "observations": np.zeros((n_rows, N_UAVS, OBS_DIM), np.float32),
        "team_label": np.full(n_rows, -1, np.int8),
        "agent_labels": np.full((n_rows, N_UAVS), -1, np.int8),
        "routed": np.zeros((n_rows, N_UAVS), bool), "relay": np.zeros((n_rows, N_UAVS), bool),
        "serving": np.zeros((n_rows, N_UAVS), np.int16),
        "relay_matrix": np.zeros((n_rows, N_UAVS, N_UAVS), bool),
        "n_routed": np.zeros(n_rows, np.int8),
        "c_bh_t0": np.zeros(n_rows, np.float64), "sd_t0": np.zeros(n_rows, np.float64),
        "actions": np.zeros((n_rows, horizon_steps, N_UAVS, 3), np.float32),
        "executed_actions": np.zeros((n_rows, horizon_steps, N_UAVS, 3), np.float32),
        "rewards": np.full((n_rows, horizon_steps), np.nan, np.float64),
        "c_bh": np.full((n_rows, horizon_steps), np.nan, np.float64),
        "sd": np.full((n_rows, horizon_steps), np.nan, np.float64),
        "segment_mean_r": np.full(n_rows, np.nan, np.float64),
    }
    if structural:
        table["structural_row"] = np.full(structural, -1, np.int64)
        table["structural_actor_hidden"] = np.zeros((structural, N_UAVS, int(hidden)), np.float32)
    return table


def structural_rows(lanes, per_episode, count=STRUCTURAL_ROWS):
    """Evenly spaced row indices of rollout 0 (rows 0 .. lanes * per_episode - 1)."""
    total = int(lanes) * int(per_episode)
    return np.unique(np.round(np.linspace(0, total - 1, min(int(count), total))).astype(np.int64))


def collect_rollout(agent, envs, worlds, rollout, episode, horizon, table, row_base, timing,
                    structural_index=None):
    """One sampled training-law rollout (one episode per lane); fills ``table`` rows
    ``row_base + lane * (horizon // K) + t0 // K``.  Returns per-rollout facts."""
    lanes = len(envs)
    per_episode = horizon // K
    if horizon % K:
        raise ValueError("horizon must be a multiple of the ten-step cap")
    structural_pos = {} if structural_index is None else {int(r): p for p, r in enumerate(structural_index)}
    for lane in range(lanes):
        agent.reset_env_state(lane)
    agent.reset_d2_metrics()
    states, observations = runner.reset_all(envs, worlds)
    steps = np.zeros(lanes, dtype=int)
    dones = np.zeros(lanes, dtype=bool)
    rows = np.full(lanes, -1, dtype=np.int64)
    held_team = np.full(lanes, -1, dtype=np.int64)
    held_agents = np.full((lanes, N_UAVS), -1, dtype=np.int64)
    prev_contract = [None] * lanes
    counts = {"team_steps": 0, "commitments": 0, "clip_events": 0, "reset": 0, "team_cap": 0}
    for t in range(horizon):
        tick = time.perf_counter()
        actions, _, data = agent.step(states, observations, steps, dones, deterministic=False,
                                      return_step_data=True, build_infos=False)
        timing["policy_seconds"] += time.perf_counter() - tick
        tick = time.perf_counter()
        runner.finite(actions, "collection actions")
        if actions.shape != (lanes, N_UAVS, 3):
            raise ValueError("collection action roster mismatch")
        team = np.asarray(data["team_skills"], dtype=np.int64).reshape(-1)
        agents = np.asarray(data["agent_skills"], dtype=np.int64)
        team_cause = np.asarray(data["d2_team_cause"], dtype=np.int64).reshape(-1)
        agent_cause = np.asarray(data["d2_agent_cause"], dtype=np.int64)
        sampled = np.asarray(data["d2_sampled_mask"], dtype=bool)
        decision = t % K == 0
        expected = TEAM_CAUSE_RESET if t == 0 else (TEAM_CAUSE_CAP if decision else 0)
        if not np.all(team_cause == expected):
            raise AssertionError(f"t={t}: d2 team causes {team_cause.tolist()} != {expected}")
        if not np.all(agent_cause == expected) or not np.all(sampled == decision):
            raise AssertionError(f"t={t}: d2 agent causes/sampling are not six-agent synchronised")
        if decision:
            counts["reset" if t == 0 else "team_cap"] += lanes
            if np.any((team < 0) | (team >= N_LABELS)) or np.any((agents < 0) | (agents >= N_LABELS)):
                raise AssertionError("label outside [0, 6)")
            held_team[:], held_agents[:] = team, agents
            for lane, env in enumerate(envs):
                row = row_base + lane * per_episode + t // K
                if table["team_label"][row] != -1:
                    raise AssertionError(f"row {row} written twice")
                rows[lane] = row
                snap = env.snapshot()
                routed, relay, serving, relay_matrix = roles_from_snapshot(snap)
                c_bh0, sd0 = pre_commitment_terms(env.host)
                if t > 0:
                    previous = prev_contract[lane]
                    if not (abs(previous["coverage_backhauled"] - c_bh0) <= PRE_COMMITMENT_TOL
                            and abs(previous["throughput_term"] - sd0) <= PRE_COMMITMENT_TOL):
                        raise AssertionError(f"pre-commitment C_bh/S-D at t0={t} disagree with the previous step")
                table["world"][row] = worlds[lane]
                table["lane"][row] = lane
                table["rollout"][row] = rollout
                table["episode"][row] = episode
                table["t0"][row] = t
                table["state"][row] = states[lane]
                table["observations"][row] = observations[lane]
                table["team_label"][row] = team[lane]
                table["agent_labels"][row] = agents[lane]
                table["routed"][row], table["relay"][row] = routed, relay
                table["serving"][row], table["relay_matrix"][row] = serving, relay_matrix
                table["n_routed"][row] = int(routed.sum())
                table["c_bh_t0"][row], table["sd_t0"][row] = c_bh0, sd0
                position = structural_pos.get(int(row))
                if position is not None:
                    table["structural_row"][position] = row
                    table["structural_actor_hidden"][position] = agent.prev_actor_hidden_np[lane]
                counts["commitments"] += 1
        elif not (np.array_equal(team, held_team) and np.array_equal(agents, held_agents)):
            raise AssertionError(f"t={t}: labels changed inside a ten-step commitment")
        timing["tracking_seconds"] += time.perf_counter() - tick
        tick = time.perf_counter()
        results = [env.step(actions[lane]) for lane, env in enumerate(envs)]
        timing["env_seconds"] += time.perf_counter() - tick
        tick = time.perf_counter()
        offset = t % K
        for lane, (obs, reward, term, trunc, info) in enumerate(results):
            if trunc:
                raise ValueError("the host contract never truncates")
            contract = info["contract"]
            clipped, events = executed_actions(actions[lane])
            if events != int(contract["action_clip_events"]):
                raise AssertionError("the clip rule disagrees with the host's clip events")
            row = rows[lane]
            table["actions"][row, offset] = actions[lane]
            table["executed_actions"][row, offset] = clipped
            table["rewards"][row, offset] = contract["contract_reward"]
            table["c_bh"][row, offset] = contract["coverage_backhauled"]
            table["sd"][row, offset] = contract["throughput_term"]
            prev_contract[lane] = contract
            states[lane] = info["next_state"]
            observations[lane] = obs
            dones[lane] = bool(term or trunc)
            counts["team_steps"] += 1
            counts["clip_events"] += events
        steps += 1
        if dones.any() and (t != horizon - 1 or not dones.all()):
            raise ValueError("unexpected collection terminal boundary")
        timing["tracking_seconds"] += time.perf_counter() - tick
    if not dones.all():
        raise ValueError("collection rollout missing its terminal boundary")
    d2 = agent.get_d2_metrics()
    causes = d2["cause_counts"]
    if (causes["reset"] != counts["reset"] or causes["team_cap"] != counts["team_cap"]
            or causes["gap"] or causes["cap"] or causes["team_gap"]):
        raise AssertionError(f"d2 metrics disagree with the collection's cause tallies: {causes}")
    block = slice(row_base, row_base + lanes * per_episode)
    if np.any(table["team_label"][block] < 0) or not np.all(np.isfinite(table["rewards"][block])):
        raise AssertionError("a lane-episode does not hold exactly 50 complete commitments")
    for lane in range(lanes):
        lane_rows = table["t0"][row_base + lane * per_episode: row_base + (lane + 1) * per_episode]
        if not np.array_equal(lane_rows, np.arange(0, horizon, K)):
            raise AssertionError("commitment starts are not 0, 10, ..., 490")
    table["segment_mean_r"][block] = table["rewards"][block].mean(axis=1)
    return counts


def structural_zero_check(agent, table, n_Z, lanes):
    """Team-label change with individual labels, state, observations and actor hidden fixed."""
    idx = table["structural_row"]
    if np.any(idx < 0):
        raise AssertionError("structural rows were not all recorded")
    saved = {name: getattr(agent, name).copy() for name in
             ("actor_hidden_np", "critic_hidden_np", "prev_actor_hidden_np", "prev_critic_hidden_np",
              "_hidden_state_array_valid")}

    def run(states, observations, agent_labels, team, hidden, deterministic):
        m = states.shape[0]
        agent.actor_hidden_np[:m] = hidden
        agent.critic_hidden_np[:m] = 0.0
        agent._hidden_state_array_valid[:m] = True
        with runner.preserve_rng():
            torch.manual_seed(STRUCTURAL_TORCH_SEED)
            actions, _, _ = agent._batched_select_action(states, observations, agent_labels, team,
                                                         np.zeros(m, dtype=bool), deterministic)
        return np.asarray(actions, dtype=np.float64)

    team_diff = {"deterministic": 0.0, "sampled": 0.0}
    control_diff = 0.0
    try:
        with torch.no_grad():
            for start in range(0, idx.size, int(lanes)):
                chunk = idx[start:start + int(lanes)]
                states = table["state"][chunk].astype(np.float32)
                obs = table["observations"][chunk].astype(np.float32)
                labels = table["agent_labels"][chunk].astype(np.int64)
                team = table["team_label"][chunk].astype(np.int64)
                hidden = table["structural_actor_hidden"][start:start + chunk.size]
                for mode, deterministic in (("deterministic", True), ("sampled", False)):
                    base = run(states, obs, labels, team, hidden, deterministic)
                    for shift in range(1, int(n_Z)):
                        other = run(states, obs, labels, (team + shift) % int(n_Z), hidden, deterministic)
                        team_diff[mode] = max(team_diff[mode], float(np.max(np.abs(other - base))))
                    if deterministic:
                        changed = labels.copy()
                        changed[:, 0] = (changed[:, 0] + 1) % N_LABELS
                        control = run(states, obs, changed, team, hidden, True)
                        control_diff = max(control_diff, float(np.max(np.abs(control - base))))
    finally:
        for name, value in saved.items():
            getattr(agent, name)[...] = value
    result = {"rows": int(idx.size), "row_source": "evenly spaced rows of collection rollout 0",
              "team_labels_tried": "every other team label (n_Z - 1 per row)",
              "max_abs_action_difference": team_diff,
              "control_individual_label_change_max_abs_difference": control_diff,
              "torch_seed": STRUCTURAL_TORCH_SEED,
              "code_fact": ("arm H actor = SkillDiscoverer.forward(observation, agent_skill, hidden_state, "
                            "compact_context=None, central_input=None) (hmasd/networks.py 1801-1809; "
                            "hmasd/agent.py _batched_select_action); the team label enters only "
                            "skill_discoverer.get_value (critic)"),
              "team_label_reaches_actor": False}
    result["passed"] = bool(team_diff["deterministic"] == 0.0 and team_diff["sampled"] == 0.0)
    if not result["passed"]:
        raise AssertionError(f"a team-label change moved the executed action: {team_diff}")
    return result


# ------------------------------------------------------------------------------ run


def run_collection(checkpoint, seed, spec, out, *, rollouts=DECLARED_ROLLOUTS, lanes=DECLARED_LANES,
                   launch_sha=None, admission=None, smoke=False):
    from experiments.candidates.coupled_host_joint_skills_stage1.adapter import make_envs

    out = Path(out)
    if (out / "summary.json").exists():
        raise ValueError("existing summary; reconcile the original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started, cpu0 = time.perf_counter(), runner.cpu_seconds()
    checkpoint = Path(checkpoint)
    summary = {"schema": SCHEMA, "direction": DIRECTION, "kind": "p3_commitment_collection",
               "status": "initializing", "failure": None, "seed": int(seed), "launch_sha": launch_sha,
               "admission": admission, "smoke": bool(smoke), "checkpoint": str(checkpoint),
               "rollouts": int(rollouts), "lanes": int(lanes)}

    def publish(boundary):
        summary["last_boundary"] = boundary
        summary["wall_seconds"] = time.perf_counter() - PROCESS_START
        runner.write_json(out / "summary.json", summary)
        print(json.dumps({"boundary": boundary, "wall_seconds": round(summary["wall_seconds"], 2)}), flush=True)

    publish("admitted")
    envs, agent, hooks, restore = [], None, [], []
    try:
        summary["checkpoint_sha256"] = file_sha256(checkpoint)
        summary["checkpoint_bytes"] = checkpoint.stat().st_size
        fit_summary = checkpoint.parent / "summary.json"
        if fit_summary.is_file():
            recorded = {c["path"]: c for c in json.loads(fit_summary.read_text()).get("checkpoints", [])}
            entry = recorded.get(checkpoint.name)
            summary["checkpoint_matches_fit_summary"] = (None if entry is None
                                                         else entry["sha256"] == summary["checkpoint_sha256"])
            if entry is not None and not summary["checkpoint_matches_fit_summary"]:
                raise ValueError("checkpoint sha256 differs from the fit's summary record")
        horizon = int(spec.horizon)
        per_episode = horizon // K
        worlds = collection_worlds(seed, spec, rollouts, lanes)
        summary["worlds"] = worlds
        summary["episode_offset"] = collection_episode_offset(spec)
        torch.set_num_threads(int(spec.torch_threads))
        rng_before = rng_digest()
        with runner.preserve_rng():
            envs = make_envs(int(lanes), worlds[0], horizon, spec.area_size)
            agent, config, load_facts = load_checkpoint_agent(checkpoint, seed, spec, envs,
                                                               out / "collection_logs")
            summary["load"] = load_facts
            summary["config"] = config_dict(config)
            restore = forbid_optimizer_steps(agent)
            calls, hooks = runner.optimizer_counts(agent)
            digest_before = runner.digest_agent(agent)
            structural = structural_rows(lanes, per_episode)
            table = allocate_table(int(rollouts) * int(lanes) * per_episode, hidden=int(config.gru_hidden_size),
                                   structural=structural.size)
            timing = {"policy_seconds": 0.0, "env_seconds": 0.0, "tracking_seconds": 0.0}
            rollout_rows, structural_result = [], None
            with torch.no_grad():
                for r in range(int(rollouts)):
                    rollout_wall, rollout_cpu = time.perf_counter(), runner.cpu_seconds()
                    rng_seed = collection_rng_seed(seed, r)
                    runner.seed_rng(rng_seed)
                    counts = collect_rollout(agent, envs, worlds[r], r, summary["episode_offset"] + r, horizon,
                                             table, r * int(lanes) * per_episode, timing,
                                             structural_index=structural if r == 0 else None)
                    rollout_rows.append({"rollout": r, "rng_seed": rng_seed, "worlds": worlds[r], **counts,
                                         "wall_seconds": time.perf_counter() - rollout_wall,
                                         "cpu_seconds": runner.cpu_seconds() - rollout_cpu})
                    if r == 0:
                        structural_result = structural_zero_check(agent, table, int(config.n_Z), lanes)
                        summary["structural_zero_check"] = structural_result
                    summary["rollouts_done"] = r + 1
                    publish(f"collection rollout {r} complete")
            digest_after = runner.digest_agent(agent)
        rng_after = rng_digest()
        if any(calls.values()) or digest_after != digest_before:
            raise ValueError("the collection moved a parameter or normaliser or took an optimizer step")
        if rng_after != rng_before:
            raise ValueError("the collection did not restore the global random streams")
        n_rows = table["segment_mean_r"].size
        if not np.all(np.isfinite(table["segment_mean_r"])) or np.any(table["team_label"] < 0):
            raise AssertionError("incomplete commitment table")
        team_steps = sum(row["team_steps"] for row in rollout_rows)
        table_path = out / "commitments.npz"
        partial = out / "commitments.partial.npz"
        np.savez_compressed(partial, **table)
        partial.replace(table_path)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        meta = {
            "schema": SCHEMA, "direction": DIRECTION, "kind": "p3_commitment_table",
            "table": table_path.name, "table_sha256": file_sha256(table_path), "rows": int(n_rows),
            "columns": {name: {"dtype": str(value.dtype), "shape": list(value.shape)} for name, value in table.items()},
            "column_notes": {
                "episode": "training-world-law episode index (spec.rollouts + 1 + rollout)",
                "relay_matrix": "[i, j] = UAV i is an interior node of UAV j's BS path at t0",
                "relay": "any(relay_matrix[i, :])", "serving": "users associated with UAV i at t0",
                "c_bh_t0/sd_t0": "pre-commitment C_bh and S/D of the host state at t0",
                "actions": "policy output; executed_actions = the host's unit-ball clip of it",
                "rewards": "contract team r of steps t0..t0+9 (time-aligned); segment_mean_r = their mean",
                "structural_row": "rows whose pre-commitment actor hidden is stored for the structural check"},
            "checkpoint": str(checkpoint), "checkpoint_sha256": summary["checkpoint_sha256"],
            "checkpoint_rollout": load_facts["checkpoint_rollout"],
            "checkpoint_launch_sha": load_facts["checkpoint_launch_sha"],
            "fit_seed": int(seed), "spec": asdict(spec), "smoke": bool(smoke), "launch_sha": launch_sha,
            "world_law": "training_world_seed(seed, lane, spec.rollouts + 1 + r)",
            "worlds": worlds, "per_rollout": rollout_rows,
            "counters": {"team_steps": team_steps, "commitments": int(n_rows),
                         "lane_episodes": int(rollouts) * int(lanes),
                         "commitments_per_lane_episode": per_episode,
                         "clip_events": sum(row["clip_events"] for row in rollout_rows)},
            "frozen": {"digest_before": digest_before, "digest_after": digest_after,
                       "optimizer_calls": dict(calls), "optimizer_steps_refused": True,
                       "rng_digest_before": rng_before, "rng_digest_after": rng_after},
            "load": load_facts, "structural_zero_check": structural_result,
            "timing": {**timing, "ms_per_team_step": {
                key.replace("_seconds", ""): 1000.0 * value / team_steps for key, value in timing.items()},
                "ms_per_team_step_total": 1000.0 * sum(timing.values()) / team_steps},
            "resources": {"wall_seconds": time.perf_counter() - started,
                          "cpu_seconds": runner.cpu_seconds() - cpu0,
                          "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
                          "peak_rss_kib": usage.ru_maxrss, "rss_scope": "RUSAGE_SELF"},
        }
        runner.write_json(out / "meta.json", meta)
        summary.update(status="complete", table=table_path.name, table_sha256=meta["table_sha256"],
                       rows=int(n_rows), counters=meta["counters"], timing=meta["timing"])
        return_code = 0
    except Exception as exc:
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        for hook in hooks:
            hook.remove()
        for optimizer, original in restore:
            optimizer.step = original
        for env in envs:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {"wall_seconds": time.perf_counter() - started,
                                "command_wall_seconds": time.perf_counter() - PROCESS_START,
                                "cpu_seconds": runner.cpu_seconds() - cpu0,
                                "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
                                "peak_rss_kib": usage.ru_maxrss, "rss_scope": "RUSAGE_SELF"}
        publish(summary["status"])
    return return_code


def smoke_refusal(worlds, out):
    flat = [w for row in worlds for w in row]
    panel = sorted(set(flat) & PANEL_WORLD_SET)
    if panel:
        return f"--smoke-no-admission refuses declared panel worlds {panel}"
    temp_root = (ROOT / "temp").resolve()
    resolved = Path(out).resolve()
    if resolved != temp_root and temp_root not in resolved.parents:
        return f"--smoke-no-admission needs --out under {temp_root}"
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", type=Path, required=True,
                        help="final H checkpoint (relative paths resolve against the checkout holding runs/)")
    parser.add_argument("--seed", type=int, required=True, help="the fit seed of the checkpoint")
    parser.add_argument("--area-size", type=int, choices=(5000, 6000), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rollouts", type=int, default=DECLARED_ROLLOUTS)
    parser.add_argument("--lanes", type=int, default=DECLARED_LANES)
    parser.add_argument("--launch-sha", default=None, help="required unless --smoke-no-admission")
    parser.add_argument("--smoke-no-admission", action="store_true",
                        help="engineering smoke only: non-panel worlds, --out under temp/, spec read from the checkpoint")
    args = parser.parse_args(argv)
    if args.rollouts <= 0 or not 0 < args.lanes < 100:
        parser.error("rollouts must be positive and lanes in [1, 99]")
    if args.smoke_no_admission:
        checkpoint = resolve_input(args.checkpoint)
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        spec = spec_from_checkpoint_config(payload["config"], args.area_size)
        del payload
        refusal = smoke_refusal(collection_worlds(args.seed, spec, args.rollouts, args.lanes), args.out)
        if refusal:
            print(f"error: {refusal}", file=sys.stderr)
            return 2
        admission = "skipped (engineering smoke: non-panel worlds, temp output)"
        launch_sha = args.launch_sha or "smoke"
    else:
        if args.seed not in SEEDS["H"]:
            parser.error("--seed is not a declared H fit seed")
        if args.launch_sha is None:
            parser.error("--launch-sha is required for an admitted collection")
        if (args.rollouts, args.lanes) != (DECLARED_ROLLOUTS, DECLARED_LANES):
            parser.error("the admitted collection is 16 rollouts x 16 lanes")
        admission = dict(require_admission(__file__, direction="coupled_host_joint_skills_stage1"))
        if args.launch_sha != admission["sha"]:
            raise ValueError("launch SHA disagrees with admission")
        launch_sha = args.launch_sha
        checkpoint = resolve_input(args.checkpoint)
        spec = replace(DEFAULT_SPEC, area_size=int(args.area_size))
    return run_collection(checkpoint, args.seed, spec, args.out, rollouts=args.rollouts, lanes=args.lanes,
                          launch_sha=launch_sha, admission=admission, smoke=args.smoke_no_admission)


if __name__ == "__main__":
    raise SystemExit(main())
