"""One fixed SET actor BC fit and native closed-loop energy relay comparison.

Only the worker writes full episode arrays. The parent receives compact rows and
loads at most four episode files for each training group. There is no resume path.
"""

from __future__ import annotations

import json
import os
import resource
import stat
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path
from typing import Any

import numpy as np
import torch

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import HeuristicParams
from experiments.candidates.energy_relay_benchmark.b02.configuration import (
    B02Spec, config_dict, make_b02_config,
)
from experiments.candidates.uav_service_auxiliary.b01.native import (
    initialization_fingerprint, optimizer_steps, sha256_file,
)
from experiments.candidates.energy_relay_benchmark.b02.training import new_agent


DIRECTION = "energy_relay_imitation"
HORIZON = 3000
TRAIN_WORLDS = tuple(range(967001, 967033))
EVAL_WORLDS = tuple(range(968001, 968033))
MODEL_SEED = 929031
ORDER_SEED = 929032
EPOCHS = 10
GROUP = 4
CHUNK = 128
WORKERS = 2
ACTION_DIM = 4
N_AGENTS = 8
LAUNCHER_FILES = frozenset({"launch-manifest.json", "launch-status.json",
                            "admission-preflight.json", "stdout.log", "stderr.log",
                            "process-exit.json"})
SCIENTIFIC_OUTPUTS = frozenset({"config.json", "summary.json", "progress.jsonl",
                                "raw", "checkpoints", "logs", "per_world"})
THREAD_ENV = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "NUMEXPR_NUM_THREADS")


def _native_launcher_file(path: Path) -> bool:
    name = path.name
    atomic_temp = (name.startswith(".hmasd-launch-") and name.endswith(".tmp")
                   and len(name) > len(".hmasd-launch-.tmp"))
    if name not in LAUNCHER_FILES and not atomic_temp:
        return False
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        # The launcher may have atomically replaced a listed temp file meanwhile.
        return True
    return stat.S_ISREG(mode)


def validate_worlds() -> None:
    if len(TRAIN_WORLDS) != 32 or len(EVAL_WORLDS) != 32:
        raise ValueError("B01 needs exactly 32 worlds in each distinct set")
    if set(TRAIN_WORLDS) & set(EVAL_WORLDS):
        raise ValueError("demonstration and development worlds overlap")
    if any(957001 <= seed <= 957032 for seed in (*TRAIN_WORLDS, *EVAL_WORLDS)):
        raise ValueError("sealed holdout worlds are forbidden")


def make_config(seed: int = MODEL_SEED, horizon: int = HORIZON):
    spec = B02Spec(seed=int(seed), lanes=1, rollouts=1, rollout_length=int(horizon),
                   episode_length=int(horizon))
    config = make_b02_config(spec)
    if (config.n_agents, config.k, config.n_Z, config.n_z) != (8, 10, 1, 1):
        raise RuntimeError("SET input contract changed")
    if (config.use_obsnorm or config.use_statenorm
            or getattr(config, "central_snapshot_state_affine", None) is not None):
        raise RuntimeError("BC requires raw observations and unscaled central state")
    if config.continuous_action_distribution != "tanh_gaussian":
        raise RuntimeError("BC requires actual bounded tanh Gaussian action")
    if config.lr_discoverer_actor != 1e-4 or config.weight_decay != 0:
        raise RuntimeError("native actor Adam contract changed")
    return config


def _write_json(path: Path, value: Any) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2, allow_nan=False,
                         default=lambda x: x.item() if isinstance(x, np.generic) else _bad_json(x))
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(payload + "\n")
    os.replace(temporary, path)


def _bad_json(value):
    raise TypeError(f"non-compact JSON value: {type(value).__name__}")


def _progress(out: Path, value: dict) -> None:
    with (out / "progress.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")


def _artifact(path: Path, out: Path) -> dict:
    return {"path": path.relative_to(out).as_posix(), "sha256": sha256_file(path),
            "bytes": path.stat().st_size, "allocated_bytes": path.stat().st_blocks * 512}


class TeacherObserver:
    """Copies only the pre-step fields needed for BC and offline replay."""

    def __init__(self):
        self.rows: dict[str, list[np.ndarray]] = {key: [] for key in
            ("observations_t", "state_t", "proposal_t", "submitted_t")}

    def attach(self, _controller):
        from contextlib import nullcontext
        return nullcontext()

    def on_step(self, *, observations_t, state_t, proposal_t, submitted_t, **_unused):
        for key, value in (("observations_t", observations_t), ("state_t", state_t),
                           ("proposal_t", proposal_t), ("submitted_t", submitted_t)):
            self.rows[key].append(np.asarray(value, dtype=np.float32).copy())

    def as_arrays(self):
        return {key: np.asarray(values, dtype=np.float32) for key, values in self.rows.items()}


@dataclass(frozen=True)
class Job:
    panel: str
    seed: int
    checkpoint: str | None = None
    record: str | None = None
    checkpoint_sha256: str | None = None
    policy_fingerprint: str | None = None


def _world(job: Job, out_name: str) -> dict:
    """Spawn worker: complete native episode and its one durable NPZ."""
    if job.seed not in (*TRAIN_WORLDS, *EVAL_WORLDS):
        raise ValueError("world outside fixed B01 panels")
    out = Path(out_name)
    task = ev.WorldTask(
        controller="Hlocal" if job.panel.startswith("teacher") else "L",
        seed=job.seed, params=PRODUCTION_PARAMS, horizon=HORIZON,
        policy_seed=MODEL_SEED, threads=1, device="cpu",
        checkpoint=job.checkpoint, checkpoint_record=job.record,
        expected_checkpoint_sha256=job.checkpoint_sha256,
        expected_policy_fingerprint=job.policy_fingerprint,
        heuristic=HeuristicParams(information="local") if job.panel.startswith("teacher") else None,
        log_dir=str(out / "logs"),
    )
    teacher = job.panel.startswith("teacher")
    result = ev.evaluate_task(task, observer_factory=(lambda _: TeacherObserver()) if teacher else None)
    row = dict(result["row"])
    if row.get("failed") or not 1 <= int(row.get("actual_length", 0)) <= HORIZON:
        row.update(panel=job.panel, failed=True, native_episode_complete=False,
                   failure_stage="native_episode", optimizer_updates=0,
                   failure=row.get("failure") or "incomplete native episode")
        return row
    row.update(panel=job.panel, native_episode_complete=True, optimizer_updates=0)
    relative = Path("raw") / job.panel / f"{job.seed}.npz"
    target = out / relative
    try:
        raw = dict(result["arrays"])
        if teacher:
            raw.update(result["observation"])
        with target.open("xb") as handle:
            np.savez_compressed(handle, **raw)
        row["raw"] = _artifact(target, out)
    except Exception as exc:
        row.update(failed=True, failure_stage="raw_write", raw_complete=False,
                   raw_path=relative.as_posix(),
                   failure=f"{type(exc).__name__}: {exc}")
    return row


def _run_panel(out: Path, jobs: list[Job], summary: dict) -> bool:
    """Never retry a failed world; retain it in the compact panel record."""
    panel = jobs[0].panel
    started = time.perf_counter()
    rows = []
    with ProcessPoolExecutor(max_workers=WORKERS, mp_context=get_context("spawn")) as pool:
        queue = iter(jobs[WORKERS:])
        futures = {}
        submission_failed = False

        def submit(job: Job) -> None:
            nonlocal submission_failed
            try:
                future = pool.submit(_world, job, str(out))
            except BrokenProcessPool as exc:
                submission_failed = True
                failure = {"panel": panel, "seed": job.seed, "stage": "submission",
                           "episode_attempted": False,
                           "error": f"{type(exc).__name__}: {exc}"}
                summary["failures"].append(failure)
                _progress(out, {"event": "submission_failed", "panel": panel, "seed": job.seed})
                _write_json(out / "summary.json", summary)
                return
            futures[future] = job

        for job in jobs[:WORKERS]:
            submit(job)
            if submission_failed:
                break
        failed = submission_failed
        while futures:
            done, _pending = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                job = futures.pop(future)
                try:
                    row = future.result()
                except Exception as exc:
                    row = {"panel": panel, "seed": job.seed, "failed": True,
                           "native_episode_complete": False, "failure_stage": "worker",
                           "failure": f"{type(exc).__name__}: {exc}"}
                counts = summary["counts"]
                if row.get("native_episode_complete"):
                    length = int(row["actual_length"])
                    if not 1 <= length <= HORIZON:
                        raise RuntimeError("worker reported invalid completed native length")
                    counts["environment_transitions"] += length
                    counts["native_episodes_completed"] += 1
                elif row.get("failed"):
                    counts["failed_worlds_unknown_environment_work"] += 1
                if row.get("failed"):
                    summary["counts"]["episodes_failed"] += 1
                    summary["failures"].append(row)
                    failed = True
                    event = "world_failed"
                else:
                    counts["episodes_completed"] += 1
                    event = "world_complete"
                counts["environment_transitions_upper_bound"] = (
                    counts["environment_transitions"]
                    + counts["failed_worlds_unknown_environment_work"] * HORIZON)
                counts["environment_transitions_exact"] = (
                    counts["failed_worlds_unknown_environment_work"] == 0)
                rows.append(row)
                _progress(out, {"event": event, "panel": panel, "seed": job.seed})
                summary["costs"] = _costs(out, summary["started_at_monotonic"])
                _write_json(out / "summary.json", summary)
            if not failed:
                for _ in done:
                    next_job = next(queue, None)
                    if next_job is not None:
                        submit(next_job)
                        if submission_failed:
                            failed = True
                            break
    rows.sort(key=lambda row: row["seed"])
    _write_json(out / "per_world" / f"{panel}.json", rows)
    summary["panels"][panel] = {"planned": len(jobs), "completed": sum(not r.get("failed") for r in rows),
                                "unattempted": len(jobs) - len(rows),
                                "wall_seconds": time.perf_counter() - started, "rows": rows}
    _write_json(out / "summary.json", summary)
    return not failed and not any(row.get("failed") for row in rows)


def _load_episode(path: Path, *, expected_sha256: str | None = None) -> dict[str, np.ndarray]:
    if expected_sha256 is not None and sha256_file(path) != expected_sha256:
        raise ValueError(f"pinned teacher input changed before use: {path}")
    with np.load(path, allow_pickle=False) as data:
        keys = ("observations_t", "state_t", "proposal_t", "submitted_t", "mode")
        result = {key: data[key] for key in keys}
    length = result["observations_t"].shape[0]
    if not (1 <= length <= HORIZON and result["state_t"].shape[0] == length
            and result["proposal_t"].shape == (length, N_AGENTS, ACTION_DIM)
            and result["submitted_t"].shape == (length, N_AGENTS, ACTION_DIM)
            and result["mode"].shape == (length, N_AGENTS)):
        raise ValueError(f"invalid demonstration arrays: {path}")
    if not all(np.isfinite(result[key]).all() for key in keys if key != "mode"):
        raise ValueError(f"nonfinite demonstration: {path}")
    return result


def held_input(episode: dict, start: int, stop: int) -> np.ndarray:
    """Raw SET central block, refresh at steps 0,10,20,..., in ego order."""
    obs, states = episode["observations_t"], episode["state_t"]
    source = (np.arange(start, stop) // 10) * 10
    block = np.concatenate((states[source], obs[source].reshape(stop - start, -1)), axis=-1)
    ego = np.broadcast_to(np.eye(N_AGENTS, dtype=np.float32),
                          (stop - start, N_AGENTS, N_AGENTS))
    return np.concatenate((np.repeat(block[:, None, :], N_AGENTS, axis=1), ego), axis=-1)


def _chunk(group: list[dict], start: int, stop: int, device: torch.device):
    """Time-major sequence, episode-major/agent-minor columns, masked terminal tails."""
    count = len(group)
    n = stop - start
    obs_dim = group[0]["observations_t"].shape[-1]
    central_dim = group[0]["state_t"].shape[-1] + N_AGENTS * obs_dim + N_AGENTS
    obs = np.zeros((n, count, N_AGENTS, obs_dim + central_dim), dtype=np.float32)
    target = np.zeros((n, count, N_AGENTS, ACTION_DIM), dtype=np.float32)
    valid = np.zeros((n, count, N_AGENTS), dtype=np.float32)
    active = np.zeros_like(valid)
    for j, ep in enumerate(group):
        last = min(stop, len(ep["state_t"]))
        if last <= start:
            continue
        m = last - start
        obs[:m, j] = np.concatenate((ep["observations_t"][start:last],
                                     held_input(ep, start, last)), axis=-1)
        target[:m, j] = ep["proposal_t"][start:last]
        valid[:m, j] = 1
        active[:m, j] = ep["mode"][start:last]
    flat = lambda x: torch.as_tensor(x.reshape(n, count * N_AGENTS, -1), device=device)
    return flat(obs), flat(target), flat(valid).squeeze(-1), flat(active).squeeze(-1)


def _actor_forward(actor, obs, hidden, *, reset: bool):
    n, batch = obs.shape[:2]
    masks = torch.ones((n, batch, 1), dtype=torch.float32, device=obs.device)
    if reset:
        masks[0] = 0
    skill = torch.zeros((n, batch), dtype=torch.int64, device=obs.device)
    actions, _logp, hidden = actor(obs, hidden, masks, skill, deterministic=True)
    return actions, hidden


def _initial_hidden(config, count: int, device: torch.device):
    return torch.zeros((count * N_AGENTS, config.hidden_size), device=device)


def _parameters(module) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in module.named_parameters()}


def _unchanged(reference: dict, module, label: str) -> None:
    current = _parameters(module)
    if reference.keys() != current.keys() or any(
        not torch.equal(value, current[name]) for name, value in reference.items()
    ):
        raise RuntimeError(f"BC changed {label}")


def _normalizer_state(agent):
    from experiments.candidates.uav_service_auxiliary.b06.native import _normalizer_snapshot
    return _normalizer_snapshot(agent)


def _save_checkpoint(agent, config, out: Path, name: str, launch_sha: str,
                     updates: int, exposures: int) -> dict:
    root = out / "checkpoints" / name
    root.mkdir()
    path = root / "agent.pt"
    agent.save_model(path)
    record = {"object_id": "ENERGY-RELAY-IMITATION-B01", "programme": "SET-BC-10-epochs",
              "launch_sha": launch_sha, "checkpoint": name, "training_seed": MODEL_SEED,
              "optimizer_updates": updates, "agent_transition_exposures": exposures,
              "policy_fingerprint": initialization_fingerprint(agent),
              "optimizer_steps": optimizer_steps(agent), "config": config_dict(config),
              "agent_pt": "agent.pt", "agent_pt_sha256": sha256_file(path),
              "agent_pt_bytes": path.stat().st_size}
    _write_json(root / "record.json", record)
    return {"record": record, "artifact": _artifact(path, out)}


def _fit(agent, config, out: Path, summary: dict, *, input_root: Path | None = None,
         loss_mask: str = "all", input_hashes: dict | None = None) -> dict:
    """Fixed B01 fit; B02 may reuse it with external inputs and an inactive-only loss.

    The default branch retains B01's exact loss, update and output semantics.
    """
    if loss_mask not in ("all", "shield_inactive"):
        raise ValueError(f"unsupported BC loss mask: {loss_mask}")
    source = out if input_root is None else Path(input_root)
    started = time.perf_counter()
    actor = agent.skill_discoverer.actor
    optimizer = agent.discoverer_actor_optimizer
    if type(optimizer) is not torch.optim.Adam or len(optimizer.param_groups) != 1:
        raise RuntimeError("BC requires the native actor Adam")
    group_params = optimizer.param_groups[0]
    if group_params["lr"] != 1e-4 or group_params["weight_decay"] != 0:
        raise RuntimeError("native Adam hyperparameters differ")
    head_logstd = actor.act.action_out.logstd._bias
    if not any(head_logstd is param for param in group_params["params"]):
        raise RuntimeError("logstd missing from native actor optimizer")
    initial_actor = _parameters(actor)
    initial_critic = _parameters(agent.skill_discoverer.critic)
    initial_coordinator = _parameters(agent.skill_coordinator)
    normalizers = _normalizer_state(agent)
    initial_logstd = head_logstd.detach().clone()
    rng = np.random.default_rng(ORDER_SEED)
    updates = exposures = selected_exposures = skipped_chunks = 0
    loss_sum = 0.0
    device = torch.device(agent.device)
    actor.train(True)
    for epoch in range(EPOCHS):
        order = rng.permutation(TRAIN_WORLDS)
        for group_seeds in order.reshape(-1, GROUP):
            group = [_load_episode(source / "raw" / "teacher_train" / f"{seed}.npz",
                                   expected_sha256=(input_hashes[str(seed)]["sha256"]
                                                    if input_hashes is not None else None))
                     for seed in group_seeds]
            hidden = _initial_hidden(config, GROUP, device)
            for start in range(0, max(len(ep["state_t"]) for ep in group), CHUNK):
                stop = min(start + CHUNK, max(len(ep["state_t"]) for ep in group))
                obs, target, valid, active = _chunk(group, start, stop, device)
                actions, hidden = _actor_forward(actor, obs, hidden, reset=(start == 0))
                if not bool(torch.isfinite(actions).all()):
                    raise RuntimeError("nonfinite bounded action")
                count = int(valid.sum().item())
                if loss_mask == "all":
                    # Keep the frozen B01 arithmetic order on its default route.
                    selected = valid
                    selected_count = count
                    denominator = valid.sum() * ACTION_DIM
                    if denominator <= 0:
                        raise RuntimeError("empty BC chunk")
                    loss = (((actions - target) ** 2) * valid.unsqueeze(-1)).sum() / denominator
                else:
                    exposures += count
                    summary["counts"]["agent_transition_exposures"] = exposures
                    selected = valid * (1.0 - active)
                    selected_count = int(selected.sum().item())
                    selected_exposures += selected_count
                    summary["counts"]["selected_loss_agent_exposures"] = selected_exposures
                    if selected_count == 0:
                        optimizer.zero_grad(set_to_none=True)
                        hidden = hidden.detach()
                        skipped_chunks += 1
                        summary["counts"]["skipped_optimizer_chunks"] = skipped_chunks
                        continue
                    denominator = selected.sum() * ACTION_DIM
                    loss = (((actions - target) ** 2) * selected.unsqueeze(-1)).sum() / denominator
                if not bool(torch.isfinite(loss)):
                    raise RuntimeError("nonfinite BC loss")
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                gradients = [p.grad for p in group_params["params"] if p.grad is not None]
                if not gradients or any(not bool(torch.isfinite(g).all()) for g in gradients):
                    raise RuntimeError("nonfinite BC gradient")
                if head_logstd.grad is not None and torch.count_nonzero(head_logstd.grad):
                    raise RuntimeError("BC action regression reached logstd")
                grad_norm = torch.nn.utils.clip_grad_norm_(group_params["params"], config.max_grad_norm)
                if not bool(torch.isfinite(grad_norm)):
                    raise RuntimeError("nonfinite BC gradient norm")
                optimizer.step()
                if not torch.equal(initial_logstd, head_logstd):
                    raise RuntimeError("BC changed logstd")
                hidden = hidden.detach()
                updates += 1
                if loss_mask == "all":
                    exposures += count
                    summary["counts"]["agent_transition_exposures"] = exposures
                loss_sum += float(loss.item()) * selected_count
                summary["counts"]["optimizer_updates"] = updates
        _progress(out, {"event": "epoch_complete", "epoch": epoch + 1,
                        "updates": updates, "agent_transition_exposures": exposures})
    _unchanged(initial_critic, agent.skill_discoverer.critic, "critic")
    _unchanged(initial_coordinator, agent.skill_coordinator, "coordinator")
    from experiments.candidates.uav_service_auxiliary.b06.native import _same_snapshot
    if not _same_snapshot(_normalizer_state(agent), normalizers):
        raise RuntimeError("BC changed normalizer state")
    final_actor = _parameters(actor)
    movement = float(sum(torch.sum((final_actor[k] - v) ** 2).item()
                         for k, v in initial_actor.items()) ** 0.5)
    if movement <= 0:
        raise RuntimeError("BC actor parameters did not move")
    steps = optimizer_steps(agent)
    if steps["low_actor"] != updates or any(value for name, value in steps.items()
                                             if name != "low_actor"):
        raise RuntimeError(f"BC optimizer steps differ from actor-only exposure: {steps}")
    result = {"epochs": EPOCHS, "updates": updates, "agent_transition_exposures": exposures,
            "wall_seconds": time.perf_counter() - started,
            "actor_parameter_l2_movement": movement, "finite_gradients": True,
            "logstd_unchanged": True, "critic_coordinator_normalizers_unchanged": True}
    if loss_mask == "all":
        result["mean_chunk_loss_weighted_by_valid_agent_steps"] = loss_sum / exposures
    else:
        result.update(loss_mask=loss_mask, selected_loss_agent_exposures=selected_exposures,
                      skipped_optimizer_chunks=skipped_chunks,
                      mean_chunk_loss_weighted_by_selected_agent_steps=(
                          loss_sum / selected_exposures if selected_exposures else None))
    return result


def _replay_checkpoint(out: Path, checkpoint: dict, panel: str, summary: dict,
                       *, input_root: Path | None = None, input_hashes: dict | None = None) -> dict:
    record = checkpoint["record"]
    task = ev.WorldTask(controller="L", seed=EVAL_WORLDS[0], params=PRODUCTION_PARAMS,
                        horizon=HORIZON, policy_seed=MODEL_SEED, threads=1, device="cpu",
                        checkpoint=str(out / "checkpoints" / record["checkpoint"] / "agent.pt"),
                        checkpoint_record=str(out / "checkpoints" / record["checkpoint"] / "record.json"),
                        expected_checkpoint_sha256=record["agent_pt_sha256"],
                        expected_policy_fingerprint=record["policy_fingerprint"])
    cpu_config = ev.learner_eval_config(ev.make_eval_config(HORIZON, MODEL_SEED), record)
    from tempfile import TemporaryDirectory
    from hmasd.agent import HMASDAgent
    source = out if input_root is None else Path(input_root)
    with TemporaryDirectory(dir=out / "logs") as logdir:
        agent, _identity = ev.load_learner_policy(task, record, cpu_config, torch.device("cpu"), logdir)
        actor = agent.skill_discoverer.actor
        actor.eval()
        sums = np.zeros((3, ACTION_DIM), dtype=np.float64)
        counts = np.zeros(3, dtype=np.int64)
        for seed in (TRAIN_WORLDS if panel == "teacher_train" else EVAL_WORLDS):
            ep = _load_episode(source / "raw" / panel / f"{seed}.npz",
                               expected_sha256=(input_hashes[str(seed)]["sha256"]
                                                if input_hashes is not None else None))
            hidden = _initial_hidden(cpu_config, 1, torch.device("cpu"))
            with torch.no_grad():
                for start in range(0, len(ep["state_t"]), CHUNK):
                    stop = min(start + CHUNK, len(ep["state_t"]))
                    obs, target, valid, active = _chunk([ep], start, stop, torch.device("cpu"))
                    action, hidden = _actor_forward(actor, obs, hidden, reset=(start == 0))
                    errors = (action - target).square().cpu().numpy().reshape(stop - start, N_AGENTS, ACTION_DIM)
                    modes = active.cpu().numpy().reshape(stop - start, N_AGENTS).astype(bool)
                    sums[0] += errors.sum(axis=(0, 1), dtype=np.float64)
                    sums[1] += errors[~modes].sum(axis=0, dtype=np.float64)
                    sums[2] += errors[modes].sum(axis=0, dtype=np.float64)
                    counts += (errors.shape[0] * N_AGENTS, int((~modes).sum()), int(modes.sum()))
            summary["counts"]["replay_agent_transitions"] += len(ep["state_t"]) * N_AGENTS
        names = ("overall", "shield_inactive", "shield_active")
        return {name: {"agent_steps": int(counts[i]),
                       "mse": float(sums[i].sum() / (counts[i] * ACTION_DIM)) if counts[i] else None,
                       "per_action_dim_mse": (sums[i] / counts[i]).tolist() if counts[i] else None}
                for i, name in enumerate(names)}


def _paired(summary: dict) -> dict:
    by_panel = {name: {row["seed"]: row for row in info["rows"]}
                for name, info in summary["panels"].items() if name in
                ("teacher_eval", "initial_eval", "final_eval")}
    if any(len(rows) != 32 for rows in by_panel.values()) or len(by_panel) != 3:
        raise RuntimeError("paired readout requires all three complete panels")
    results = []
    for seed in EVAL_WORLDS:
        t, i, f = (by_panel[name][seed] for name in ("teacher_eval", "initial_eval", "final_eval"))
        results.append({"seed": seed,
                        "teacher_qos_per_step": t["qos_per_step"],
                        "initial_qos_per_step": i["qos_per_step"],
                        "final_qos_per_step": f["qos_per_step"],
                        "bc_minus_initial_qos_per_step": f["qos_per_step"] - i["qos_per_step"],
                        "teacher_raw_native_J": t["raw_native_J"],
                        "initial_raw_native_J": i["raw_native_J"],
                        "final_raw_native_J": f["raw_native_J"],
                        "bc_minus_initial_raw_native_J": f["raw_native_J"] - i["raw_native_J"],
                        "bc_minus_initial_min_battery": f["episode_minimum_battery_ratio"]
                        - i["episode_minimum_battery_ratio"],
                        "bc_minus_initial_return_cost_raw": f["return_constraint_cost_raw_sum"]
                        - i["return_constraint_cost_raw_sum"],
                        "bc_minus_initial_cutoff_penalty": f["cutoff_event_penalty_sum"]
                        - i["cutoff_event_penalty_sum"],
                        "bc_minus_initial_depletion_penalty": f["depletion_event_penalty_sum"]
                        - i["depletion_event_penalty_sum"]})
    def stats(key):
        values = np.asarray([row[key] for row in results], dtype=np.float64)
        return {"mean": float(values.mean()), "world_se": float(values.std(ddof=1) / np.sqrt(32)),
                "descriptive_95pct_interval": [float(values.mean() - 1.96 * values.std(ddof=1) / np.sqrt(32)),
                                                 float(values.mean() + 1.96 * values.std(ddof=1) / np.sqrt(32))]}
    return {"worlds": results, "conditional_on_one_training_instance": True,
            "bc_minus_initial_qos_per_step": stats("bc_minus_initial_qos_per_step"),
            "bc_minus_initial_raw_native_J": stats("bc_minus_initial_raw_native_J"),
            "bc_minus_initial_min_battery": stats("bc_minus_initial_min_battery"),
            "bc_minus_initial_return_cost_raw": stats("bc_minus_initial_return_cost_raw"),
            "bc_minus_initial_cutoff_penalty": stats("bc_minus_initial_cutoff_penalty"),
            "bc_minus_initial_depletion_penalty": stats("bc_minus_initial_depletion_penalty"),
            "final_min_battery_lower_tail": sorted(by_panel["final_eval"][s]["episode_minimum_battery_ratio"]
                                                   for s in EVAL_WORLDS)[:8]}


def _costs(out: Path, started: float) -> dict:
    parent = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        allocated = sum(path.stat().st_blocks * 512 for path in out.rglob("*")
                        if stat.S_ISREG(path.stat().st_mode))
    except OSError:
        allocated = None
    return {"wall_seconds": time.perf_counter() - started,
            "parent_peak_rss_kib": parent.ru_maxrss,
            "max_child_peak_rss_kib": children.ru_maxrss,
            "output_allocated_bytes": allocated,
            "resources_unmeasured": allocated is None}


def run_batch(*, out: Path, launch_sha: str, seed: int = MODEL_SEED) -> dict:
    """Sequential fixed protocol; failure records stage/counts and stops."""
    validate_worlds()
    if seed != MODEL_SEED or len(launch_sha) != 40 or any(c not in "0123456789abcdef" for c in launch_sha):
        raise ValueError("B01 requires its declared model seed and full lowercase launch SHA")
    out = Path(out)
    if out.exists():
        if not out.is_dir():
            raise FileExistsError(f"B01 output is not a directory: {out}")
        existing = list(out.iterdir())
        conflicts = [path.name for path in existing
                     if path.name in SCIENTIFIC_OUTPUTS or not _native_launcher_file(path)]
        if conflicts:
            raise FileExistsError(f"B01 output contains prior or unknown content: {sorted(conflicts)}")
    out.mkdir(parents=True, exist_ok=True)
    for name in ("raw", "checkpoints", "logs", "per_world"):
        (out / name).mkdir()
    for name in ("teacher_train", "teacher_eval", "initial_eval", "final_eval"):
        (out / "raw" / name).mkdir()
    started = time.perf_counter()
    summary = {"status": "INCOMPLETE", "launch_sha": launch_sha, "started_at_monotonic": started,
               "counts": {"episodes_planned": 128, "episodes_completed": 0, "episodes_failed": 0,
                          "native_episodes_completed": 0,
                          "environment_transitions": 0,
                          "environment_transitions_upper_bound": 0,
                          "environment_transitions_exact": True,
                          "failed_worlds_unknown_environment_work": 0,
                          "optimizer_updates": 0,
                          "agent_transition_exposures": 0, "replay_agent_transitions": 0,
                          "fits_started": 0},
               "stage": "collection", "failures": [], "panels": {}, "checkpoints": {},
               "costs": {}}
    _write_json(out / "config.json", {"direction": DIRECTION, "launch_sha": launch_sha,
                "model_seed": MODEL_SEED, "order_seed": ORDER_SEED,
                "train_worlds": TRAIN_WORLDS, "eval_worlds": EVAL_WORLDS,
                "horizon": HORIZON, "workers": WORKERS, "threads_per_worker": 1,
                "thread_environment": {name: os.environ.get(name) for name in THREAD_ENV},
                "environment_transition_count_semantics": (
                    "environment_transitions counts known completed native episode steps; "
                    "when failed_worlds_unknown_environment_work > 0 it is a lower bound "
                    "over attempted worlds, with each unknown failed world bounded by HORIZON"),
                "epochs": EPOCHS, "episodes_per_group": GROUP, "tbptt": CHUNK,
                "shield": {"enter": PRODUCTION_PARAMS.enter_margin,
                           "exit": PRODUCTION_PARAMS.exit_margin},
                "teacher": "HeuristicParams(information='local')",
                "target": "teacher pre-shield proposal, all real transitions",
                "action": "R_Actor.forward deterministic tanh Gaussian",
                "fitting_device": "cuda", "evaluation_device": "cpu"})
    _write_json(out / "summary.json", summary)
    try:
        if not _run_panel(out, [Job("teacher_train", s) for s in TRAIN_WORLDS], summary):
            raise RuntimeError("demonstration panel incomplete")
        torch.set_num_threads(1)
        if not torch.cuda.is_available():
            raise RuntimeError("configured CUDA fitting device unavailable")
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        config = make_config()
        device = torch.device("cuda")
        agent, _ = new_agent(config, device=device, log_dir=out / "logs", seed=MODEL_SEED)
        summary["stage"] = "fit"
        summary["checkpoints"]["initial"] = _save_checkpoint(agent, config, out, "initial", launch_sha, 0, 0)
        summary["counts"]["fits_started"] = 1
        _write_json(out / "summary.json", summary)
        summary["fit"] = _fit(agent, config, out, summary)
        summary["checkpoints"]["final"] = _save_checkpoint(
            agent, config, out, "final", launch_sha, summary["counts"]["optimizer_updates"],
            summary["counts"]["agent_transition_exposures"])
        del agent
        torch.cuda.empty_cache()
        summary["stage"] = "evaluation"
        _write_json(out / "summary.json", summary)
        for panel, checkpoint in (("teacher_eval", None), ("initial_eval", "initial"),
                                  ("final_eval", "final")):
            identity = summary["checkpoints"].get(checkpoint, {}).get("record") if checkpoint else None
            jobs = [Job(panel, s,
                        str(out / "checkpoints" / checkpoint / "agent.pt") if checkpoint else None,
                        str(out / "checkpoints" / checkpoint / "record.json") if checkpoint else None,
                        identity["agent_pt_sha256"] if identity else None,
                        identity["policy_fingerprint"] if identity else None)
                    for s in EVAL_WORLDS]
            if not _run_panel(out, jobs, summary):
                raise RuntimeError(f"{panel} incomplete")
        summary["stage"] = "offline_replay"
        for checkpoint in ("initial", "final"):
            for panel in ("teacher_train", "teacher_eval"):
                summary.setdefault("offline_mse", {}).setdefault(checkpoint, {})[panel] = (
                    _replay_checkpoint(out, summary["checkpoints"][checkpoint], panel, summary))
        summary["paired_readout"] = _paired(summary)
        counts = summary["counts"]
        if (counts["episodes_completed"] != 128 or counts["episodes_failed"]
                or counts["environment_transitions"] > 384_000
                or counts["optimizer_updates"] > 1_920
                or counts["agent_transition_exposures"] > 7_680_000
                or counts["replay_agent_transitions"] > 3_072_000):
            raise RuntimeError(f"B01 actual counts violate the fixed budget: {counts}")
        summary["status"] = "COMPLETE"
        summary["stage"] = "complete"
    except Exception as exc:
        summary["status"] = "FAILED"
        summary["failures"].append({"stage": summary["stage"],
                                    "error": f"{type(exc).__name__}: {exc}"})
        _progress(out, {"event": "study_failed", "stage": summary["stage"]})
    summary["costs"] = _costs(out, started)
    summary["costs"]["max_observed_world_worker_peak_rss_kib"] = max(
        (int(row.get("worker_peak_rss_kib", 0)) for panel in summary["panels"].values()
         for row in panel["rows"] if not row.get("failed")), default=None)
    summary.pop("started_at_monotonic")
    _write_json(out / "summary.json", summary)
    return summary
