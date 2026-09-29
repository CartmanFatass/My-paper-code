"""One admitted cell-1 fit (arm H or SET) of coupled_host_joint_skills_stage1 b01 and its panels.

Adapted from ``experiments/candidates/agent_count_generalization/runner.py``.  Differences:
the scenario-2 contract adapter and the b01 host in place of S1 lanes; arm H on the fixed-cap
d2 route; explicit per-episode training worlds; dev panels (deterministic) after rollouts
0/15/30/45 and hold-out panels (deterministic and sampled) after the final rollout; contract
readers per world; per-fit CPU/RSS metering; the ``--probe`` timing mode.

T-W: ``--contract target|slot|offset`` dispatches to ``macro_runner.run_macro_fit`` (macro-step
action contracts) and ``--floor NAME --worlds ...`` to ``macro_runner.run_floor`` (zero-fit
floors); admission stays in ``main`` for every mode.  The default ``--contract step`` is the b01
path, unchanged.
"""
from __future__ import annotations

import time
PROCESS_START = time.perf_counter()

import argparse
import contextlib
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

from experiments.candidates.coupled_host_joint_skills_stage1.adapter import (
    PANEL_WORLD_SET, training_world_seed,
)
from experiments.candidates.coupled_host_joint_skills_stage1.configuration import (
    DEFAULT_SPEC, DIRECTION, PAIRS, SEEDS, config_dict, is_declared_fit_spec, make_config,
    matching_table,
)
from scripts.hmasd_admission import require_admission

OPTIMIZERS = ("coordinator", "discoverer_actor", "discoverer_critic",
              "team_discriminator", "individual_discriminator")
NORMALIZERS = ("obs_norm", "state_norm", "value_norm_coordinator", "value_norm_discoverer")
FINAL_WINDOW = 100
D2_FORBIDDEN_CAUSES = ("gap", "team_gap", "cap")
D2_CAUSE_RESET = 1


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.generic):
        return jsonable(value.item())
    if torch.is_tensor(value):
        return jsonable(value.detach().cpu().numpy())
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value


def write_json(path, value):
    encoded = json.dumps(jsonable(value), indent=2, allow_nan=False) + "\n"
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_text(encoded, encoding="utf-8")
    partial.replace(path)


def finite(value, label):
    if isinstance(value, dict):
        for k, v in value.items():
            finite(v, f"{label}.{k}")
    elif isinstance(value, (tuple, list)):
        for v in value:
            finite(v, label)
    elif torch.is_tensor(value):
        if not bool(torch.isfinite(value).all()):
            raise ValueError(f"nonfinite {label}")
    elif isinstance(value, (np.ndarray, float, np.number)) and not np.isfinite(value).all():
        raise ValueError(f"nonfinite {label}")


def seed_rng(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


@contextlib.contextmanager
def preserve_rng():
    py, np_state, torch_state = random.getstate(), np.random.get_state(), torch.get_rng_state()
    try:
        yield
    finally:
        random.setstate(py)
        np.random.set_state(np_state)
        torch.set_rng_state(torch_state)


def proc_memory():
    """Current and peak resident set of this process (``/proc/self/status``, KiB)."""
    result = {"VmRSS_kib": None, "VmHWM_kib": None}
    try:
        with open("/proc/self/status", encoding="ascii") as stream:
            for line in stream:
                key = line.split(":", 1)[0]
                if key in ("VmRSS", "VmHWM"):
                    result[f"{key}_kib"] = int(line.split()[1])
    except OSError:
        pass
    return result


def cpu_seconds():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return float(usage.ru_utime + usage.ru_stime)


def model_modules(agent):
    return {name: module for name in ("skill_coordinator", "skill_discoverer",
                                      "team_discriminator", "individual_discriminator")
            if (module := getattr(agent, name, None)) is not None}


def motion_modules(agent):
    result = {"coordinator": agent.skill_coordinator,
              "discoverer_actor": agent.skill_discoverer.actor,
              "discoverer_critic": agent.skill_discoverer.critic}
    for name in ("team_discriminator", "individual_discriminator"):
        module = getattr(agent, name, None)
        if module is not None:
            result[name] = module
    for root_name, module in list(result.items()):
        for name, child in module.named_modules():
            if name and type(child).__name__ in {"StateSetEncoder", "SetActorBase"}:
                result[f"{root_name}.{name}"] = child
    return result


def capture_parameters(agent):
    return {name: {k: p.detach().cpu().clone() for k, p in module.named_parameters()}
            for name, module in motion_modules(agent).items()}


def parameter_motion(agent, initial):
    result = {}
    for name, module in motion_modules(agent).items():
        numerator, denominator = 0.0, 0.0
        for key, p in module.named_parameters():
            p0 = initial[name][key].double()
            delta = p.detach().cpu().double() - p0
            numerator += float(delta.square().sum())
            denominator += float(p0.square().sum())
        result[name] = {"delta_l2": numerator ** .5,
                        "relative_l2": (numerator / denominator) ** .5 if denominator else None}
    return result


def digest_agent(agent):
    digest = hashlib.sha256()
    for module_name, module in model_modules(agent).items():
        for key, value in module.state_dict().items():
            array = value.detach().cpu().contiguous().numpy()
            digest.update(f"{module_name}.{key}|{array.dtype}|{array.shape}".encode())
            digest.update(array.tobytes())
    for name in NORMALIZERS:
        norm = getattr(agent, name, None)
        if norm is not None:
            digest.update(json.dumps(jsonable(vars(norm)), sort_keys=True, allow_nan=False).encode())
    return digest.hexdigest()


def optimizer_counts(agent):
    counts = {name: 0 for name in OPTIMIZERS}
    handles = []
    for name in OPTIMIZERS:
        optimizer = getattr(agent, name + "_optimizer", None)
        if optimizer is not None:
            def count_step(_optimizer, _args, _kwargs, key=name):
                counts[key] += 1
            handles.append(optimizer.register_step_post_hook(count_step))
    return counts, handles


def reset_all(envs, seeds):
    if len(seeds) != len(envs):
        raise ValueError("one explicit world seed per lane is required")
    pairs = [env.reset(seed=int(seed)) for env, seed in zip(envs, seeds)]
    return (np.stack([info["state"] for obs, info in pairs]),
            np.stack([obs for obs, info in pairs]))


def save_checkpoint(agent, out, rollout, config, sha):
    path = out / f"checkpoint_{rollout:02d}.pt"
    payload = {
        "schema": 1, "direction": DIRECTION, "launch_sha": sha, "rollout": rollout,
        "config": jsonable(config_dict(config)),
        "modules": {name: module.state_dict() for name, module in model_modules(agent).items()},
        "normalizers": {name: jsonable(vars(norm)) if (norm := getattr(agent, name, None)) is not None
                        else None for name in NORMALIZERS},
        "usage": "Evaluation weights; load through the direction's models.build_agent + strict_sync; "
                 "no training resume contract or optimizer restoration.",
    }
    partial = path.with_suffix(".pt.partial")
    torch.save(payload, partial)
    partial.replace(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": path.name, "sha256": digest.hexdigest(), "bytes": path.stat().st_size}


def check_spec_worlds(spec, seeds=None):
    """Panel worlds only in the declared fit spec; training worlds never in a panel."""
    used = set(spec.dev_worlds) | set(spec.holdout_worlds) | set(spec.probe_panel_worlds)
    if not is_declared_fit_spec(spec) and used & PANEL_WORLD_SET:
        raise ValueError("a non-declared (technical) spec must not touch the dev/hold-out panel worlds")
    for name in ("dev_worlds", "holdout_worlds", "probe_panel_worlds"):
        worlds = tuple(getattr(spec, name))
        if not worlds or len(set(worlds)) != len(worlds):
            raise ValueError(f"{name} must be a non-empty list of distinct worlds")
        if len(worlds) % spec.eval_lanes:
            raise ValueError(f"{name} must fill whole evaluation chunks of {spec.eval_lanes} lanes")
    for seed in seeds or ():
        for lane in range(spec.train_lanes):
            for episode in range(max(spec.rollouts, spec.probe_rollouts) + 1):
                training_world_seed(seed, lane, episode)


def entropy_bits(counts):
    counts = np.asarray(counts, dtype=float)
    total = counts.sum()
    if total <= 0:
        return None
    p = counts[counts > 0] / total
    return float(-(p * np.log2(p)).sum())


# ------------------------------------------------------------------------------ panel readers


class WorldTracker:
    """Per-world contract readers for one 500-step panel episode."""

    def __init__(self, env, world_seed):
        # Import here: planner.py is shared with the gate references (one far-cluster rule).
        from experiments.candidates.coupled_host_joint_skills_stage1.planner import cluster_layout

        host = env.host
        layout = cluster_layout(host)
        self.world_seed = int(world_seed)
        self.n_uavs = int(host.n_uavs)
        self.far_members = np.asarray(layout["membership"]) == int(layout["far_cluster"])
        self.layout = {
            "centres_xy": np.asarray(layout["centres"], dtype=float).tolist(),
            "centre_source": layout["centre_source"],
            "centre_distance_to_bs_m": np.asarray(layout["centre_distance_to_bs_m"], dtype=float).tolist(),
            "far_cluster": int(layout["far_cluster"]),
            "far_cluster_size": int(self.far_members.sum()),
        }
        snap = env.snapshot()
        self.initial_positions = snap["uav_positions"].tolist()
        self.prev_assign = self._assignment(snap["connections"])
        self.prev_routed = set(snap["routing_paths"])
        self.prev_backhauled = self._backhauled(snap["connections"], snap["routing_paths"])
        self.series = {"contract_reward": [], "coverage_backhauled": [],
                       "frontend_capacity_with_path_mbps": [], "far_cluster_backhauled_share": []}
        self.association_changes = []
        self.uav_backhaul_losses = 0
        self.user_backhaul_losses = 0
        self.clip_events = 0
        self.relay_hist = np.zeros(4, dtype=np.int64)  # relays per routed UAV-step: 0..3
        self.links_total = 0
        self.routed_uav_steps = 0
        self.relay_steps_by_agent = np.zeros(self.n_uavs, dtype=np.int64)
        self.far_a2a_user_steps = 0
        self.far_backhauled_user_steps = 0
        self.steps = 0

    @staticmethod
    def _assignment(connections):
        connections = np.asarray(connections, dtype=bool)
        if np.any(connections.sum(axis=0) > 1):
            raise AssertionError("a user is associated with more than one UAV")
        return np.where(connections.any(axis=0), connections.argmax(axis=0), -1)

    def _backhauled(self, connections, routing_paths):
        routed = np.zeros(self.n_uavs, dtype=bool)
        for i in routing_paths:
            routed[int(i)] = True
        return np.any(np.asarray(connections, dtype=bool) & routed[:, None], axis=0)

    def update(self, contract, snap):
        connections = snap["connections"]
        paths = snap["routing_paths"]
        assign = self._assignment(connections)
        backhauled = self._backhauled(connections, paths)
        routed = set(paths)
        self.association_changes.append(int(np.sum(assign != self.prev_assign)))
        self.uav_backhaul_losses += len(self.prev_routed - routed)
        self.user_backhaul_losses += int(np.sum(self.prev_backhauled & ~backhauled))
        self.clip_events += int(contract["action_clip_events"])
        relayed_uav = np.zeros(self.n_uavs, dtype=bool)
        relays_now = set()
        for i, path in paths.items():
            if path[0] != ("uav", int(i)) or path[-1][0] != "ground_bs":
                raise AssertionError(f"unexpected routing path {path!r}")
            n_relays = len(path) - 2
            if not 0 <= n_relays <= 3:
                raise AssertionError(f"path with {n_relays} relays exceeds max_hops = 3")
            self.relay_hist[n_relays] += 1
            self.links_total += len(path) - 1
            self.routed_uav_steps += 1
            relayed_uav[int(i)] = n_relays > 0
            for node_type, node in path[1:-1]:
                if node_type != "uav":
                    raise AssertionError(f"non-UAV interior node in {path!r}")
                relays_now.add(int(node))
        for j in relays_now:
            self.relay_steps_by_agent[j] += 1
        far_bh = backhauled & self.far_members
        far_a2a = far_bh & (assign >= 0) & relayed_uav[np.maximum(assign, 0)]
        self.far_backhauled_user_steps += int(far_bh.sum())
        self.far_a2a_user_steps += int(far_a2a.sum())
        for key in ("contract_reward", "coverage_backhauled", "frontend_capacity_with_path_mbps"):
            self.series[key].append(float(contract[key]))
        self.series["far_cluster_backhauled_share"].append(
            float(far_bh.sum()) / float(max(1, self.far_members.sum())))
        self.prev_assign, self.prev_routed, self.prev_backhauled = assign, routed, backhauled
        self.steps += 1

    def summary(self):
        out = {"world_seed": self.world_seed, "steps": self.steps, "clusters": self.layout,
               "initial_positions_xyz": self.initial_positions}
        for key, values in self.series.items():
            array = np.asarray(values, dtype=float)
            out[f"{key}_mean_all"] = float(array.mean())
            out[f"{key}_mean_final100"] = float(array[-FINAL_WINDOW:].mean())
            out[f"{key}_final"] = float(array[-1])
        out["r_mean_all"] = out["contract_reward_mean_all"]
        out["r_mean_final100"] = out["contract_reward_mean_final100"]
        far_steps = max(1, int(self.far_members.sum())) * self.steps
        out["far_cluster_a2a_path_user_steps"] = int(self.far_a2a_user_steps)
        out["far_cluster_a2a_path_user_time_share"] = self.far_a2a_user_steps / far_steps
        out["far_cluster_backhauled_user_steps"] = int(self.far_backhauled_user_steps)
        out["relay_hops"] = {
            "relays_per_routed_uav_step_hist": self.relay_hist.tolist(),
            "links_per_routed_uav_step_mean": (self.links_total / self.routed_uav_steps
                                               if self.routed_uav_steps else None),
            "routed_uavs_per_step_mean": self.routed_uav_steps / max(1, self.steps),
        }
        out["relay_position_share_by_agent"] = (self.relay_steps_by_agent / max(1, self.steps)).tolist()
        out["association_changes_per_step_mean"] = float(np.mean(self.association_changes))
        out["association_changes_total"] = int(np.sum(self.association_changes))
        out["uav_backhaul_loss_events"] = int(self.uav_backhaul_losses)
        out["user_backhaul_loss_events"] = int(self.user_backhaul_losses)
        out["action_clip_events"] = int(self.clip_events)
        return out


READER_KEYS = ("r_mean_all", "r_mean_final100", "coverage_backhauled_mean_all",
               "coverage_backhauled_mean_final100", "coverage_backhauled_final",
               "frontend_capacity_with_path_mbps_mean_all", "far_cluster_backhauled_share_mean_all",
               "far_cluster_backhauled_share_final", "far_cluster_a2a_path_user_time_share",
               "association_changes_per_step_mean", "uav_backhaul_loss_events",
               "user_backhaul_loss_events", "action_clip_events")


def run_panel(learner, arm, seed, worlds, deterministic, spec, counters, record_memory=None,
              log_name="evaluation"):
    """Run one frozen evaluation over ``worlds`` (chunks of ``spec.eval_lanes``); return the row."""
    from experiments.candidates.coupled_host_joint_skills_stage1.adapter import make_envs
    from experiments.candidates.coupled_host_joint_skills_stage1.models import build_agent, strict_sync

    worlds = [int(w) for w in worlds]
    lanes = int(spec.eval_lanes)
    chunks = [worlds[i:i + lanes] for i in range(0, len(worlds), lanes)]
    rng_seed = worlds[0] + 51
    learner_before = digest_agent(learner)
    row = {"worlds": worlds, "deterministic": bool(deterministic), "rng_seed": rng_seed,
           "steps": 0, "episodes": 0, "per_world": []}
    target, envs, hooks = None, [], []
    started = time.perf_counter()
    try:
        with preserve_rng():
            seed_rng(rng_seed)
            envs = make_envs(len(chunks[0]), chunks[0], spec.horizon, spec.area_size)
            config = make_config(arm, envs, seed, spec)
            memory_before = proc_memory()
            target = build_agent(config, str(counters["log_root"] / "evaluation_logs" / log_name))
            strict_sync(target, learner)
            target.train(False)
            memory_after = proc_memory()
            if record_memory is not None:
                record_memory({"before_target_build": memory_before, "after_target_build": memory_after})
            calls, hooks = optimizer_counts(target)
            before = digest_agent(target)
            label_counts = np.zeros(int(config.n_z), dtype=np.int64)
            team_counts = np.zeros(int(config.n_Z), dtype=np.int64)
            per_agent_counts = np.zeros((6, int(config.n_z)), dtype=np.int64)
            d2_causes = {"reset": 0, "team_cap": 0, "other": 0}
            for chunk_index, chunk in enumerate(chunks):
                if chunk_index:
                    for env in envs:
                        env.close()
                    envs = make_envs(len(chunk), chunk, spec.horizon, spec.area_size)
                for lane in range(lanes):
                    target.reset_env_state(lane)
                states, observations = reset_all(envs, chunk)
                trackers = [WorldTracker(env, world) for env, world in zip(envs, chunk)]
                steps = np.zeros(lanes, dtype=int)
                dones = np.zeros(lanes, dtype=bool)
                with torch.no_grad():
                    for t in range(spec.horizon):
                        actions, _, data = target.step(states, observations, steps, dones,
                            deterministic=bool(deterministic), return_step_data=True, build_infos=False)
                        finite(actions, "evaluation actions")
                        if actions.shape != (lanes, 6, 3):
                            raise ValueError("evaluation action roster mismatch")
                        if arm == "H":
                            agent_skills = np.asarray(data["agent_skills"], dtype=np.int64)
                            team_skills = np.asarray(data["team_skills"], dtype=np.int64).reshape(-1)
                            for lane in range(lanes):
                                np.add.at(label_counts, agent_skills[lane], 1)
                                np.add.at(per_agent_counts, (np.arange(6), agent_skills[lane]), 1)
                                team_counts[team_skills[lane]] += 1
                            team_cause = np.asarray(data["d2_team_cause"], dtype=np.int64).reshape(-1)
                            if t == 0 and not np.all(team_cause == D2_CAUSE_RESET):
                                raise AssertionError("evaluation episode did not start with a d2 reset")
                            d2_causes["reset"] += int(np.sum(team_cause == D2_CAUSE_RESET))
                            d2_causes["team_cap"] += int(np.sum(team_cause == 3))
                            d2_causes["other"] += int(np.sum((team_cause != 0) & (team_cause != 1)
                                                             & (team_cause != 3)))
                            agent_cause = np.asarray(data["d2_agent_cause"], dtype=np.int64)
                            if np.any((agent_cause == 4) | (agent_cause == 5) | (team_cause == 2)[:, None]):
                                raise AssertionError("d2 evaluation produced a gap/cap interruption")
                        for lane, env in enumerate(envs):
                            obs, reward, term, trunc, info = env.step(actions[lane])
                            trackers[lane].update(info["contract"], env.snapshot())
                            states[lane] = info["next_state"]
                            observations[lane] = obs
                            dones[lane] = bool(term or trunc)
                            if trunc:
                                raise ValueError("the host contract never truncates")
                            row["steps"] += 1
                            counters["evaluation_team_steps"] += 1
                            row["episodes"] += int(dones[lane])
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("evaluation missing terminal boundary")
                row["per_world"].extend(tracker.summary() for tracker in trackers)
            if any(calls.values()) or digest_agent(target) != before:
                raise ValueError("evaluation modified parameters or normalizers")
            counters["evaluation_episodes"] += row["episodes"]
            row["means"] = {key: float(np.mean([w[key] for w in row["per_world"]])) for key in READER_KEYS}
            row["relay_position_share_by_agent_mean"] = np.mean(
                [w["relay_position_share_by_agent"] for w in row["per_world"]], axis=0).tolist()
            if arm == "H":
                row["labels"] = {
                    "agent_label_counts": label_counts.tolist(),
                    "agent_label_entropy_bits": entropy_bits(label_counts),
                    "team_label_counts": team_counts.tolist(),
                    "team_label_entropy_bits": entropy_bits(team_counts),
                    "per_agent_label_entropy_bits": [entropy_bits(c) for c in per_agent_counts],
                    "d2_team_causes": d2_causes,
                }
            row.update(optimizer_calls=calls.copy(), frozen_weights_and_normalizers=True,
                       config=config_dict(config))
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        del target
    if digest_agent(learner) != learner_before:
        raise ValueError("evaluator modified learner weights or normalizers")
    row["wall_seconds"] = time.perf_counter() - started
    return row


def evaluate_panels(learner, arm, seed, rollout, out, summary, spec, publish, final):
    runs = [("dev", spec.dev_worlds, True)]
    if final:
        runs += [("holdout", spec.holdout_worlds, True), ("holdout", spec.holdout_worlds, False)]
    for kind, worlds, deterministic in runs:
        mode = "deterministic" if deterministic else "sampled"
        name = f"panel_{rollout:02d}_{kind}_{mode}.json"
        header = {"after_rollout": rollout,
                  "training_team_steps": rollout * spec.train_lanes * spec.horizon,
                  "kind": kind, "mode": mode, "status": "running", "file": name}
        summary["panels"].append(header)
        publish(f"evaluation {rollout} {kind} {mode} starting")
        try:
            row = run_panel(learner, arm, seed, worlds, deterministic, spec, summary["counts_ref"],
                            record_memory=lambda m: summary["memory"]["evaluation_overlap"].append(
                                {"after_rollout": rollout, "kind": kind, "mode": mode, **m}),
                            log_name=f"r{rollout:02d}_{kind}_{mode}")
        except Exception as exc:
            header.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            write_json(out / name, header)
            raise
        header.update(status="complete", means=row["means"])
        write_json(out / name, {**header, **row})
        publish(f"evaluation {rollout} {kind} {mode} complete")


# ------------------------------------------------------------------------------ fit


def terminal_facts(agent, arm, horizon):
    """How the collected rollout presents the step-500 boundary to ``agent.update`` (facts)."""
    buffer = agent.rollout_buffer
    data = buffer._get_full_rollout_data()
    facts = {"low_level_dones_last_step_all_true": bool(np.all(data["dones"][horizon - 1])),
             "low_level_dones_before_last_any": bool(np.any(data["dones"][:horizon - 1]))}
    if arm == "H":
        team_valid = buffer.d2_team_valid[:horizon]
        team_terminal = buffer.d2_team_terminal[:horizon]
        agent_valid = buffer.d2_agent_valid[:horizon]
        agent_terminal = buffer.d2_agent_terminal[:horizon]
        last_team_terminal, last_agent_terminal = [], []
        for env_idx in range(team_valid.shape[1]):
            rows = np.flatnonzero(team_valid[:, env_idx])
            last_team_terminal.append(bool(team_terminal[rows[-1], env_idx]) if rows.size else None)
            for agent_idx in range(agent_valid.shape[2]):
                rows = np.flatnonzero(agent_valid[:, env_idx, agent_idx])
                last_agent_terminal.append(bool(agent_terminal[rows[-1], env_idx, agent_idx])
                                           if rows.size else None)
        open_team = [int(seg["start"]) for seg in agent.d2_open_team_segments.values()
                     if int(seg["start"]) >= 0]
        open_agent = [int(s) for seg in agent.d2_open_agent_segments.values()
                      for s in np.asarray(seg["start"]).reshape(-1) if int(s) >= 0]
        facts.update({
            "d2_team_rows": int(team_valid.sum()),
            "d2_team_rows_terminal": int((team_valid & team_terminal).sum()),
            "d2_last_team_row_terminal_all": all(v is True for v in last_team_terminal),
            "d2_last_agent_row_terminal_all": all(v is True for v in last_agent_terminal),
            "d2_open_segments_before_update": len(open_team) + len(open_agent),
        })
    else:
        facts["high_level_valid_rows"] = int(np.sum(data["high_level_valid_mask"][:horizon]))
        facts["disable_high_level_training"] = bool(getattr(agent.config, "disable_high_level_training", False))
    return facts


def build_matching_table(arm, seed, envs, spec, learner, config, log_dir):
    """Both arms' configs and agents at this spec (other arm built under preserved RNG)."""
    from experiments.candidates.coupled_host_joint_skills_stage1.models import build_agent

    other_arm = "SET" if arm == "H" else "H"
    pair = next(p for p in PAIRS if seed in p)
    other_seed = pair[1] if arm == "H" else pair[0]
    with preserve_rng():
        # Full-lane config for the table's config columns; the agent that supplies parameter
        # counts and route attributes (independent of num_envs) is built on one lane so its
        # rollout buffers do not inflate the fit's peak RSS.
        other_config = make_config(other_arm, envs, other_seed, spec)
        count_config = make_config(other_arm, envs[:1], other_seed, spec)
        other_agent = build_agent(count_config, str(log_dir))
    configs = {arm: config, other_arm: other_config}
    agents = {arm: learner, other_arm: other_agent}
    table = matching_table(configs["H"], configs["SET"], agents, spec)
    table["parameter_count_note"] = f"{other_arm} counts from a one-lane build of the same recipe"
    del other_agent
    return table


def run_fit(out, arm, seed, launch_sha, admission, spec=DEFAULT_SPEC, probe=False):
    from experiments.candidates.coupled_host_joint_skills_stage1.adapter import make_envs
    from experiments.candidates.coupled_host_joint_skills_stage1.models import build_agent, route_facts

    out = Path(out)
    if (out / "summary.json").exists():
        raise ValueError("existing scientific summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    cpu_start = cpu_seconds()
    rollouts = int(spec.probe_rollouts if probe else spec.rollouts)
    counts = {"training_team_steps": 0, "stored_team_steps": 0, "training_episodes": 0, "updates": 0,
              "evaluation_team_steps": 0, "evaluation_episodes": 0, "log_root": out}
    summary = {"schema": 1, "direction": DIRECTION, "arm": arm, "seed": seed,
               "launch_sha": launch_sha, "admission": admission, "probe": bool(probe),
               "status": "initializing", "fit_started": False, "failure": None,
               "spec": asdict(spec), "rollouts_run": rollouts, "panels": [], "checkpoints": [],
               "counts": counts, "counts_ref": counts,
               "memory": {"evaluation_overlap": [], "start": proc_memory()},
               "reward_units": {"training": "adapter scalar = contract team r / 6",
                                "readings": "team per-step r = 0.5 * (C_bh + S/D)"},
               "runtime": {"python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
                           "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
                           "thread_environment": {name: os.environ[name] for name in
                              ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")}}}

    def publish(boundary):
        summary["last_boundary"] = boundary
        summary["wall_seconds"] = time.perf_counter() - PROCESS_START
        public = {k: v for k, v in summary.items() if k != "counts_ref"}
        public["counts"] = {k: v for k, v in counts.items() if k != "log_root"}
        write_json(out / "summary.json", public)
        print(json.dumps({"boundary": boundary, "wall_seconds": round(summary["wall_seconds"], 2)}), flush=True)

    publish("admitted")
    envs, agent, hooks = [], None, []
    timing_rows = []
    try:
        if arm not in SEEDS:
            raise ValueError(f"unknown arm {arm}")
        check_spec_worlds(spec, [seed])
        torch.set_num_threads(spec.torch_threads)
        seed_rng(seed)
        episodes = np.zeros(spec.train_lanes, dtype=int)
        lane_worlds = [training_world_seed(seed, lane, 0) for lane in range(spec.train_lanes)]
        envs = make_envs(spec.train_lanes, lane_worlds, spec.horizon, spec.area_size)
        config = make_config(arm, envs, seed, spec)
        summary["config"] = config_dict(config)
        write_json(out / "config.json", {"launch_sha": launch_sha, "spec": asdict(spec), "config": summary["config"]})
        agent = build_agent(config, str(out / "learner_logs"))
        summary["route"] = route_facts(agent)
        calls, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = calls
        summary["parameter_counts"] = {name: sum(p.numel() for p in module.parameters())
                                       for name, module in model_modules(agent).items()}
        initial = capture_parameters(agent)
        summary["initial_parameter_digest"] = digest_agent(agent)
        memory_before_table = proc_memory()
        table = build_matching_table(arm, seed, envs, spec, agent, config, out / "matching_table_logs")
        summary["memory"]["matching_table_build"] = {"before": memory_before_table, "after": proc_memory()}
        write_json(out / "matching_table.json", table)
        print(json.dumps({"matching_table": str(out / "matching_table.json"),
                          "differing_config_fields": sorted(table["differing_config_fields"])}), flush=True)
        if digest_agent(agent) != summary["initial_parameter_digest"]:
            raise AssertionError("building the matching table changed the learner")
        agent.train(True)
        if not probe and 0 in spec.panels:
            summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
            evaluate_panels(agent, arm, seed, 0, out, summary, spec, publish, final=rollouts == 0)
        states, observations = reset_all(envs, lane_worlds)
        steps = np.zeros(spec.train_lanes, dtype=int)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"] = "training"
        summary["fit_started"] = True
        summary["training_started_wall"] = time.perf_counter() - PROCESS_START
        publish("training starts")
        for rollout in range(1, rollouts + 1):
            rollout_start = time.perf_counter()
            rollout_cpu = cpu_seconds()
            before = calls.copy()
            if arm == "H":
                agent.reset_d2_metrics()
            world_seeds = [training_world_seed(seed, lane, int(episodes[lane])) for lane in range(spec.train_lanes)]
            returns = np.zeros(spec.train_lanes)
            c_bh_sum = np.zeros(spec.train_lanes)
            clip_events = 0
            policy_s = env_s = store_s = 0.0
            for t in range(spec.horizon):
                tick = time.perf_counter()
                actions, _, data = agent.step(states, observations, steps, dones,
                    deterministic=False, return_step_data=True, build_infos=False)
                policy_s += time.perf_counter() - tick
                finite(actions, "training actions")
                finite(data, "training step data")
                if actions.shape != (spec.train_lanes, 6, 3):
                    raise ValueError("training action roster mismatch")
                actions_before = actions.copy()
                next_states, next_observations = [], []
                rewards = np.zeros(spec.train_lanes)
                next_dones = np.zeros(spec.train_lanes, dtype=bool)
                tick = time.perf_counter()
                for lane, env in enumerate(envs):
                    obs, reward, term, trunc, info = env.step(actions[lane])
                    if trunc:
                        raise ValueError("the host contract never truncates")
                    contract = info["contract"]
                    next_states.append(info["next_state"])
                    next_observations.append(obs)
                    rewards[lane] = reward
                    next_dones[lane] = bool(term or trunc)
                    returns[lane] += reward
                    c_bh_sum[lane] += contract["coverage_backhauled"]
                    clip_events += contract["action_clip_events"]
                    counts["training_team_steps"] += 1
                    counts["training_episodes"] += int(next_dones[lane])
                env_s += time.perf_counter() - tick
                if not np.array_equal(actions, actions_before):
                    raise AssertionError("the host clip mutated the stored actions")
                next_states, next_observations = np.stack(next_states), np.stack(next_observations)
                finite((next_states, next_observations, rewards), "training transition")
                tick = time.perf_counter()
                agent.store_transition_batch(states=states, next_states=next_states.copy(),
                    observations=observations, next_observations=next_observations.copy(),
                    actions=actions, rewards=rewards, dones=next_dones, infos_batch=None,
                    rollout_step_idx=t, step_data=data)
                store_s += time.perf_counter() - tick
                counts["stored_team_steps"] += spec.train_lanes
                # Store the real terminal successor before constructing reset inputs.
                tick = time.perf_counter()
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        episodes[lane] += 1
                        obs, info = env.reset(seed=training_world_seed(seed, lane, int(episodes[lane])))
                        next_states[lane], next_observations[lane] = info["state"], obs
                        agent.reset_env_state(lane)
                        steps[lane] = 0
                    else:
                        steps[lane] += 1
                env_s += time.perf_counter() - tick
                states, observations, dones = next_states, next_observations, next_dones
                if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                    raise ValueError("unexpected training terminal boundary")
            if not dones.all():
                raise ValueError("training rollout missing full episodes")
            collection_s = time.perf_counter() - rollout_start
            facts = terminal_facts(agent, arm, spec.horizon)
            summary["terminal_facts"] = facts
            publish(f"rollout {rollout} collected")
            tick = time.perf_counter()
            losses = agent.update(last_values=np.zeros((spec.train_lanes, 6), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon, last_state=states.copy(),
                last_observations=observations.copy())
            update_s = time.perf_counter() - tick
            finite(losses, "training losses")
            counts["updates"] += 1
            d2 = None
            if arm == "H":
                d2 = agent.get_d2_metrics()
                bad = {name: d2["cause_counts"][name] for name in D2_FORBIDDEN_CAUSES if d2["cause_counts"][name]}
                if bad:
                    raise AssertionError(f"d2 produced interruption causes {bad}")
                # Six agents synchronised: every decision is a team decision re-sampling all six.
                if (d2["team_decisions"] != d2["decision_steps"]
                        or d2["sampled_total"] != 6 * d2["decision_steps"]
                        or d2["decision_steps"] * 10 != d2["steps"]):
                    raise AssertionError(f"d2 decisions are not six-agent synchronised: {d2}")
            motion = parameter_motion(agent, initial)
            timing = {"collection_seconds": collection_s, "update_seconds": update_s,
                      "policy_seconds": policy_s, "env_seconds": env_s, "store_seconds": store_s,
                      "cpu_seconds": cpu_seconds() - rollout_cpu,
                      "wall_seconds": time.perf_counter() - rollout_start}
            timing_rows.append(timing)
            row = {"rollout": rollout, "team_steps": counts["training_team_steps"],
                   "world_seeds": world_seeds,
                   "training_scalar_returns": returns.tolist(),
                   "training_team_r_mean": (6.0 * returns / spec.horizon).tolist(),
                   "training_c_bh_mean": (c_bh_sum / spec.horizon).tolist(),
                   "action_clip_events": int(clip_events),
                   "losses": jsonable(losses), "d2_metrics": jsonable(d2),
                   "terminal_facts": facts,
                   "optimizer_delta": {name: calls[name] - before[name] for name in calls},
                   "optimizer_total": calls.copy(), "parameter_motion": motion,
                   "timing": timing, "memory": proc_memory(),
                   "rollout_wall_seconds": timing["wall_seconds"]}
            with (out / "training.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            summary["parameter_motion"] = motion
            summary["last_training_row"] = {k: row[k] for k in ("rollout", "team_steps", "timing",
                                                                "optimizer_total", "action_clip_events")}
            agent.clear_buffers()
            publish(f"rollout {rollout} updated")
            if not probe and rollout in spec.panels:
                summary["checkpoints"].append(save_checkpoint(agent, out, rollout, config, launch_sha))
                evaluate_panels(agent, arm, seed, rollout, out, summary, spec, publish,
                                final=rollout == rollouts)
        expected = rollouts * spec.train_lanes * spec.horizon
        if counts["training_team_steps"] != expected or counts["stored_team_steps"] != expected:
            raise ValueError("training exposure incomplete")
        required = ("discoverer_actor", "discoverer_critic") + (
            ("coordinator", "team_discriminator", "individual_discriminator") if arm == "H" else ())
        for name in required:
            if calls[name] <= 0 or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"required learner module did not update: {name}")
        for name, motion in summary["parameter_motion"].items():
            if "." in name and not (arm == "SET" and name.startswith("coordinator.")) and motion["delta_l2"] <= 0:
                raise ValueError(f"new encoder did not update: {name}")
        if arm == "SET" and any(calls[name] for name in ("coordinator", "team_discriminator", "individual_discriminator")):
            raise ValueError("SET unexpectedly updated skill modules")
        if probe:
            summary["probe_result"] = write_probe(out, arm, seed, agent, spec, timing_rows, summary, publish)
        summary["status"] = "complete"
        summary["final_parameter_digest"] = digest_agent(agent)
        return_code = 0
    except Exception as exc:
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {"wall_seconds_in_run_fit": time.perf_counter() - started,
                                "command_wall_seconds": time.perf_counter() - PROCESS_START,
                                "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
                                "cpu_seconds_in_run_fit": cpu_seconds() - cpu_start,
                                "peak_rss_kib": usage.ru_maxrss, "proc_memory_end": proc_memory(),
                                "rss_scope": "scientific process Linux RUSAGE_SELF",
                                "resources_unmeasured": ["peak_scratch_bytes"]}
        publish(summary["status"])
    return return_code


def write_probe(out, arm, seed, agent, spec, timing_rows, summary, publish):
    """Time one panel-sized frozen evaluation; write ``timing_probe.json`` (no scores)."""
    publish("probe panel timing starts")
    scratch_counts = {"evaluation_team_steps": 0, "evaluation_episodes": 0, "log_root": out}
    overlap = []
    cpu0, wall0 = cpu_seconds(), time.perf_counter()
    row = run_panel(agent, arm, seed, spec.probe_panel_worlds, True, spec, scratch_counts,
                    record_memory=overlap.append, log_name="probe_timing")
    panel_wall, panel_cpu = time.perf_counter() - wall0, cpu_seconds() - cpu0
    del row  # timing only: no panel score is kept or written
    collection = [r["collection_seconds"] for r in timing_rows]
    update = [r["update_seconds"] for r in timing_rows]
    wall = [r["wall_seconds"] for r in timing_rows]
    cpu = [r["cpu_seconds"] for r in timing_rows]
    per_world = panel_wall / len(spec.probe_panel_worlds)
    per_world_cpu = panel_cpu / len(spec.probe_panel_worlds)
    panel_world_runs = len(spec.panels) * len(spec.dev_worlds) + 2 * len(spec.holdout_worlds)
    train_steps = spec.train_lanes * spec.horizon * len(timing_rows)
    probe = {
        "schema": 1, "direction": DIRECTION, "arm": arm, "seed": seed,
        "probe_rollouts": len(timing_rows), "team_steps": train_steps,
        "seconds_per_rollout": {"collection": float(np.mean(collection)), "update": float(np.mean(update)),
                                "wall": float(np.mean(wall)), "cpu": float(np.mean(cpu))},
        "per_rollout": timing_rows,
        "ms_per_team_step": {
            "env": 1000.0 * sum(r["env_seconds"] for r in timing_rows) / train_steps,
            "policy": 1000.0 * sum(r["policy_seconds"] for r in timing_rows) / train_steps,
            "store": 1000.0 * sum(r["store_seconds"] for r in timing_rows) / train_steps,
            "update": 1000.0 * sum(update) / train_steps,
        },
        "panel_run": {"worlds": list(spec.probe_panel_worlds), "deterministic": True,
                      "wall_seconds": panel_wall, "cpu_seconds": panel_cpu,
                      "scores": "not recorded (timing only)"},
        "wall_cpu_ratio_training": float(sum(cpu) / sum(wall)) if sum(wall) else None,
        "projection": {
            "rollouts": spec.rollouts,
            "training_wall_seconds": spec.rollouts * float(np.mean(wall)),
            "training_cpu_seconds": spec.rollouts * float(np.mean(cpu)),
            "panel_world_episodes": panel_world_runs,
            "panel_wall_seconds": panel_world_runs * per_world,
            "panel_cpu_seconds": panel_world_runs * per_world_cpu,
        },
        "memory": {"peak_rss_kib_process": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   "evaluation_overlap": overlap, "now": proc_memory()},
        "note": "projection = declared rollouts x mean probe rollout + declared panel episodes x probe per-world "
                "panel time; checkpoints and the B12 reader are not included",
    }
    probe["projection"]["fit_wall_seconds"] = (probe["projection"]["training_wall_seconds"]
                                               + probe["projection"]["panel_wall_seconds"])
    probe["projection"]["fit_cpu_seconds"] = (probe["projection"]["training_cpu_seconds"]
                                              + probe["projection"]["panel_cpu_seconds"])
    write_json(out / "timing_probe.json", probe)
    publish("probe panel timing complete")
    return {"timing_probe": "timing_probe.json",
            "projected_fit_wall_seconds": probe["projection"]["fit_wall_seconds"],
            "projected_fit_cpu_seconds": probe["projection"]["fit_cpu_seconds"]}


MACRO_CHOICES = ("target", "slot", "offset")
FLOOR_CHOICES = ("random-target", "random-slot", "sticky-random-slot", "nearest-unclaimed-slot",
                 "planner-slots", "identity-permutation-slots", "held-random-permutation-slots")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=tuple(SEEDS), help="learner arm (required for a fit)")
    parser.add_argument("--seed", type=int, help="fit seed (required for a fit)")
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--area-size", type=int, choices=(5000, 6000), required=True)
    parser.add_argument("--probe", action="store_true",
                        help="3 training rollouts + one timed panel-sized run; writes timing_probe.json")
    parser.add_argument("--contract", choices=("step",) + MACRO_CHOICES, default="step",
                        help="step = the b01 per-step fit (default, unchanged); target/slot/offset = "
                             "the T-W macro-step fit (macro_runner.py; area 5000 only)")
    parser.add_argument("--floor", choices=FLOOR_CHOICES,
                        help="T-W zero-fit floor (no learner, no --arm/--seed) over --worlds")
    parser.add_argument("--worlds", nargs="+", help="floor worlds: integers and inclusive ranges a-b")
    parser.add_argument("--nearest-cadence", choices=("every_macro_step", "first_macro_step"),
                        default="every_macro_step", help="nearest-unclaimed-slot re-choice cadence")
    parser.add_argument("--menu-dir", type=Path,
                        default=ROOT / "runs" / DIRECTION / "menus",
                        help="planner menu cache root (<menu-dir>/<area>/<world>.json)")
    parser.add_argument("--smoke-no-admission", action="store_true",
                        help="engineering smoke of a floor only: non-panel worlds and --out under temp/")
    parser.add_argument("--continuous-action-distribution", choices=("gaussian", "tanh_gaussian"),
                        help="fits only: continuous action head (default gaussian; b02 SET-V-b uses "
                             "tanh_gaussian with init -1, min -5, max 0)")
    parser.add_argument("--continuous-logstd-init", type=float, help="fits only (default 0.0)")
    parser.add_argument("--continuous-logstd-min", type=float, help="fits only (default -20.0)")
    parser.add_argument("--continuous-logstd-max", type=float, help="fits only (default 2.0)")
    args = parser.parse_args(argv)
    head = {key: getattr(args, key) for key in ("continuous_action_distribution", "continuous_logstd_init",
                                                "continuous_logstd_min", "continuous_logstd_max")
            if getattr(args, key) is not None}
    if head and args.floor is not None:
        parser.error("the action-head options apply to fits only")
    worlds = None
    if args.floor is None:
        if args.arm is None or args.seed is None:
            parser.error("a fit needs --arm and --seed")
        if args.seed not in SEEDS[args.arm]:
            parser.error("arm/seed is outside the prospective six-fit batch")
        if args.smoke_no_admission:
            parser.error("--smoke-no-admission applies to floors only")
        if args.worlds:
            parser.error("--worlds applies to floors only")
    else:
        if args.arm is not None or args.seed is not None or args.probe or args.contract != "step":
            parser.error("a floor takes no --arm/--seed/--probe/--contract")
        if not args.worlds:
            parser.error("a floor needs --worlds")
        from experiments.candidates.coupled_host_joint_skills_stage1.run_gate import parse_worlds
        try:
            worlds = parse_worlds(args.worlds)
        except ValueError as exc:
            parser.error(str(exc))
    if (args.contract != "step" or args.floor is not None) and args.area_size != 5000:
        parser.error("macro fits and floors run at area 5000 (menus and sealed references are 5 km)")
    if args.smoke_no_admission:
        from experiments.candidates.coupled_host_joint_skills_stage1.macro_runner import smoke_refusal
        refusal = smoke_refusal(worlds, args.out, args.menu_dir)
        if refusal:
            parser.error(refusal)
        admission = {"sha": args.launch_sha, "status": "skipped (engineering smoke: non-panel worlds, temp output)"}
    else:
        admission = require_admission(__file__, direction="coupled_host_joint_skills_stage1")
        if args.launch_sha != admission["sha"]:
            raise ValueError("launch SHA disagrees with admission")
    if args.floor is not None:
        from experiments.candidates.coupled_host_joint_skills_stage1.macro_runner import run_floor
        return run_floor(args.out, args.floor, worlds, args.area_size, args.menu_dir, args.launch_sha,
                         dict(admission), args.nearest_cadence)
    if args.contract != "step":
        from experiments.candidates.coupled_host_joint_skills_stage1.configuration import MacroFitSpec
        from experiments.candidates.coupled_host_joint_skills_stage1.macro_runner import run_macro_fit
        spec = MacroFitSpec(contract=args.contract, **head)
        return run_macro_fit(args.out, args.arm, args.seed, args.launch_sha, dict(admission), spec,
                             args.menu_dir, probe=args.probe)
    spec = replace(DEFAULT_SPEC, area_size=int(args.area_size), **head)
    return run_fit(args.out, args.arm, args.seed, args.launch_sha, dict(admission), spec, probe=args.probe)


if __name__ == "__main__":
    raise SystemExit(main())
