"""Canonical-frame evaluation of ``b05_canonical_frame_a01``: one implementation for B, C_SW, C_SW_FULL.

``evaluate_canonical_task`` is B01's ``evaluate_task`` for controller ``L`` (same config, checkpoint
checks, restored learner, evaluator rebuilt inside ``preserved_rng``, stochastic seeding rule,
mutation checks, ``evaluate_world`` step contract) with ``SWController`` in place of
``PolicyController``: at step 0 of the episode ``sw_frame`` picks the G4 element from the
physical reset observation; every ``propose`` feeds the evaluator the canonical observation and
state and returns the physical proposal (``inverse_actions``), so the shield, guard and env stay
physical.  IDENTITY calls ``PolicyController.propose`` on the untouched inputs, so a W,S world is
bitwise the plain B01 path.  ``full_speed`` (C_SW_FULL) rescales the non-zero horizontal
components of the physical proposal to unit norm right before the shield.

Arms: ``B`` (a B05 checkpoint), ``C_SW`` and ``C_SW_FULL`` (the frozen B02 c06, agent.pt sha256
``C06_SHA256``; C_SW_FULL is deterministic on the development worlds only, as declared).  Panel
``<arm>_<cNN>_<mode>_<shield label>``; traces keep B01's ``world_<i>_*`` keys (own_xyz, qos, mode,
...) and add ``proposal`` (physical proposal the shield received), ``submitted`` (post-shield
action), ``proposal_raw`` (C_SW_FULL: the physical policy proposal before rescaling), ``frame``
(D4 value) and ``users_in_access_range_t0``.  Rows add ``arm``, ``frame``, ``spawn_corner`` and
``users_in_access_range_t0`` (read from the raw env right after ``reset``; no draw).
"""

from __future__ import annotations

import copy
import json
import os
import resource
import sys
import tempfile
import time
from contextlib import nullcontext
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import (
    _sync_agent, initialization_fingerprint, make_env, optimizer_steps, preserved_rng,
    seed_everything, sha256_file,
)
from experiments.candidates.uav_service_auxiliary.b06.native import (
    _normalizer_snapshot, _same_snapshot,
)
from experiments.candidates.uav_service_auxiliary.b09.persistence import (
    append_progress, write_summary,
)
from hmasd.agent import HMASDAgent

from ..b01.evaluation import (
    ACTION_MODES, L_CONTROLLER_INFORMATION, SAMPLE_SEED_RULE, TRACE_TIMING, PolicyController,
    WorldTask, aggregate, evaluate_world, learner_eval_config, load_learner_policy,
    make_eval_config, read_learner_record, sample_seed, trace_arrays,
)
from ..b01.feedback import PRODUCTION_PARAMS
from ..b02.checkpoint_eval import HOLDOUT_WORLDS, check_worlds
from ..b02.configuration import OBJECT_ID as B02_OBJECT_ID, PROGRAMME as B02_PROGRAMME
from ..b04.geometry_probe import _users_in_access_range
from ..b04.probe_run import run_pool
from .frame import (
    D4, IDENTITY, adapter_record, canonical_inputs, full_horizontal, physical_actions,
    spawn_corner, sw_frame,
)
from .training import OBJECT_ID as B05_OBJECT_ID, PROGRAMME as B05_PROGRAMME, write_manifest

ARMS = ("B", "C_SW", "C_SW_FULL")
C06_SHA256 = "41aa4ff0be5d55f924d8388af055fb087d76c1f517497e69c26d7962ce041bb3"
C06_FINGERPRINT = "a7c54b470441b8e742459e47a533a41c58534c36288ece0e9eb026a3b544c39c"
STOCHASTIC_DRAW = 0
HORIZON = 3000


class SWController(PolicyController):
    """B01 ``PolicyController`` behind the SW canonical frame (DM4 ``CanonicalController`` pattern)."""

    def __init__(self, evaluator, *, deterministic: bool = True, sample_seed: int | None = None,
                 full_speed: bool = False, frame_rule=sw_frame):
        super().__init__(evaluator, deterministic=deterministic, sample_seed=sample_seed)
        self.full_speed = bool(full_speed)
        self.frame_rule = frame_rule
        self.frame: D4 | None = None
        self.last_raw: np.ndarray | None = None        # physical policy proposal
        self.last_canonical: np.ndarray | None = None  # the evaluator's own (canonical) output

    def reset(self) -> None:
        super().reset()
        self.frame = None
        self.last_raw = self.last_canonical = None

    def propose(self, observations, state, step, previous_done, modes):
        if self.frame is None:
            if int(step) != 0:
                raise RuntimeError("a canonical frame must be chosen at episode reset")
            self.frame = self.frame_rule(observations)
        if self.frame == IDENTITY:
            canonical = super().propose(observations, state, step, previous_done, modes)
            physical = canonical
        else:
            obs_c, state_c = canonical_inputs(observations, state, self.frame)
            canonical = super().propose(obs_c, state_c, step, previous_done, modes)
            physical = physical_actions(canonical, self.frame)
        self.last_canonical, self.last_raw = canonical, physical
        return full_horizontal(physical) if self.full_speed else physical


class AccessRecordingEnv:
    """Pass-through env wrapper; after ``reset`` it reads the users in actual access range at
    t = 0 from the raw env (``max_uav sinr >= min_sinr``, b04 Block 1's count).  No draw."""

    def __init__(self, env):
        self.env = env
        self.users_in_access_range_t0: int | None = None

    def reset(self, *args, **kwargs):
        result = self.env.reset(*args, **kwargs)
        self.users_in_access_range_t0 = _users_in_access_range(self.env.env)
        return result

    def step(self, actions):
        return self.env.step(actions)

    def close(self):
        self.env.close()


class TraceObserver:
    """Per-step physical proposal (what the shield received), submitted action and raw proposal."""

    def __init__(self):
        self.proposal, self.submitted, self.raw = [], [], []

    def attach(self, controller):
        return nullcontext()

    def on_step(self, *, proposal_t, submitted_t, controller, **unused):
        self.proposal.append(np.asarray(proposal_t, dtype=np.float32).copy())
        self.submitted.append(np.asarray(submitted_t, dtype=np.float32).copy())
        self.raw.append(np.asarray(controller.last_raw, dtype=np.float32).copy())

    def as_arrays(self) -> dict[str, np.ndarray]:
        return {"proposal": np.asarray(self.proposal, dtype=np.float32),
                "submitted": np.asarray(self.submitted, dtype=np.float32),
                "proposal_raw": np.asarray(self.raw, dtype=np.float32)}


@dataclass(frozen=True)
class CanonicalTask:
    """Picklable: one world under the SW wrapper (``world`` is B01's controller-L task)."""
    world: WorldTask
    arm: str


def evaluate_canonical_task(task: CanonicalTask) -> dict[str, Any]:
    """Spawn-pool worker: one world, fully rebuilt (B01 ``evaluate_task`` for controller L)."""
    world = task.world
    if task.arm not in ARMS or world.controller != "L":
        raise ValueError(f"canonical evaluation takes arm in {ARMS} and controller L")
    started = time.perf_counter()
    if world.action_mode not in ACTION_MODES:
        raise ValueError(f"action_mode must be one of {ACTION_MODES}")
    stochastic = world.action_mode == "stochastic"
    if stochastic and world.draw is None:
        raise ValueError("stochastic action mode needs a draw index")
    episode_seed = sample_seed(world.policy_seed, world.seed, world.draw) if stochastic else None
    torch.set_num_threads(int(world.threads))
    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError("B05 evaluation requires Torch FP32 default dtype")
    device = torch.device(world.device)
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    config = make_eval_config(world.horizon, world.policy_seed)
    record = read_learner_record(world)
    config = learner_eval_config(config, record)
    observer = TraceObserver()
    full_speed = task.arm == "C_SW_FULL"
    with tempfile.TemporaryDirectory(prefix="b05-agent-logs-", dir=world.log_dir) as log_dir:
        env = AccessRecordingEnv(make_env(config, world.seed))
        try:
            agent, identity = load_learner_policy(world, record, config, device, log_dir)
            before = (initialization_fingerprint(agent), optimizer_steps(agent),
                      _normalizer_snapshot(agent))
            with preserved_rng():
                seed_everything(int(world.policy_seed), device)
                evaluator = HMASDAgent(copy.deepcopy(config), log_dir=log_dir, device=device)
                _sync_agent(agent, evaluator)
                evaluator.train(False)
                evaluator_before = (initialization_fingerprint(evaluator),
                                    optimizer_steps(evaluator), _normalizer_snapshot(evaluator))
                if evaluator_before[0] != before[0]:
                    raise RuntimeError("evaluator policy differs from restored checkpoint")
                controller = SWController(evaluator, deterministic=not stochastic,
                                          sample_seed=episode_seed, full_speed=full_speed)
                row, arrays = evaluate_world(controller, env, config, world.seed, world.params,
                                             observer=observer)
                if (
                    initialization_fingerprint(evaluator) != evaluator_before[0]
                    or optimizer_steps(evaluator) != evaluator_before[1]
                    or not _same_snapshot(_normalizer_snapshot(evaluator), evaluator_before[2])
                ):
                    raise RuntimeError("evaluation mutated evaluator state")
            if (
                initialization_fingerprint(agent) != before[0]
                or optimizer_steps(agent) != before[1]
                or not _same_snapshot(_normalizer_snapshot(agent), before[2])
            ):
                raise RuntimeError("evaluation mutated the restored policy")
            row["controller_information"] = L_CONTROLLER_INFORMATION
            row["failed"] = False
        finally:
            env.close()
    row.update(controller=world.controller, enter_margin=world.params.enter_margin,
               exit_margin=world.params.exit_margin,
               wall_seconds=time.perf_counter() - started,
               worker_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
               action_mode=world.action_mode)
    if stochastic:
        row.update(draw=int(world.draw), sample_seed=episode_seed)
    observed = observer.as_arrays()
    if len(observed["proposal"]) != row["actual_length"]:
        raise RuntimeError("observer and native step counts differ")
    row.update(arm=task.arm, frame=controller.frame.name,
               spawn_corner=spawn_corner(arrays["own_xyz"][0] / float(config.area_size)),
               users_in_access_range_t0=env.users_in_access_range_t0, full_speed=full_speed)
    return {"row": row, "arrays": arrays, "identity": identity, "observation": observed,
            "frame": int(controller.frame.value)}


def canonical_trace_arrays(results: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    """B01 ``trace_arrays`` + ``proposal`` / ``submitted`` / ``frame`` / ``users_in_access_range_t0``
    per world (+ ``proposal_raw`` for C_SW_FULL)."""
    arrays = trace_arrays(results)
    for index, result in enumerate(results):
        prefix = f"world_{index}_"
        if result["row"].get("failed"):
            continue
        observed = result["observation"]
        arrays[prefix + "proposal"] = observed["proposal"]
        arrays[prefix + "submitted"] = observed["submitted"]
        if result["row"].get("full_speed"):
            arrays[prefix + "proposal_raw"] = observed["proposal_raw"]
        arrays[prefix + "frame"] = np.asarray(result["frame"], dtype=np.int8)
        arrays[prefix + "users_in_access_range_t0"] = np.asarray(
            result["row"]["users_in_access_range_t0"], dtype=np.int64)
    return arrays


def read_checkpoint(checkpoint_dir: Path, arm: str) -> dict[str, Any]:
    """record.json of the arm's checkpoint, with the arm's identity checks and the agent.pt digest."""
    checkpoint_dir = Path(checkpoint_dir)
    record = json.loads((checkpoint_dir / "record.json").read_text(encoding="utf-8"))
    if record.get("checkpoint") != checkpoint_dir.name:
        raise ValueError(f"record names {record.get('checkpoint')}, directory is {checkpoint_dir.name}")
    if arm == "B":
        frame = record.get("canonical_frame") or {}
        if (record.get("object_id"), record.get("programme")) != (B05_OBJECT_ID, B05_PROGRAMME) \
                or frame.get("rule") != "sw":
            raise ValueError("arm B evaluates a B05 (SW canonical) training checkpoint only")
    elif arm in ("C_SW", "C_SW_FULL"):
        if ((record.get("object_id"), record.get("programme")) != (B02_OBJECT_ID, B02_PROGRAMME)
                or record.get("checkpoint") != "c06" or record.get("agent_pt_sha256") != C06_SHA256
                or record.get("policy_fingerprint") != C06_FINGERPRINT):
            raise ValueError(f"arm {arm} evaluates the frozen B02 c06 (agent.pt {C06_SHA256[:8]}...) only")
    else:
        raise ValueError(f"unknown arm {arm!r}; expected one of {ARMS}")
    digest = sha256_file(checkpoint_dir / record["agent_pt"])
    if digest != record["agent_pt_sha256"]:
        raise ValueError("agent.pt sha256 differs from record.json")
    return record


def panel_name(arm: str, checkpoint: str, mode: str) -> str:
    return f"{arm}_{checkpoint}_{mode}_{PRODUCTION_PARAMS.label}"


def run_panel(*, arm: str, checkpoint_dir: Path, out: Path, worlds: Iterable[int],
              modes: Iterable[str], final: bool, launch_sha: str, workers: int = 1,
              threads: int = 2, device_name: str = "cpu", horizon: int = HORIZON,
              argv=None) -> dict[str, Any]:
    """One arm x checkpoint on ``worlds`` in ``modes``: ``<out>/{config,summary,manifest}.json``,
    ``progress.jsonl``, ``panels/<name>.json``, ``traces/<name>.npz``.  Hold-out needs ``final``."""
    worlds = tuple(int(w) for w in worlds)
    modes = tuple(modes)
    check_worlds(worlds, final)
    if not modes or len(set(modes)) != len(modes) or any(m not in ACTION_MODES for m in modes):
        raise ValueError(f"modes must be distinct values from {ACTION_MODES}")
    if arm == "C_SW_FULL" and (modes != ("deterministic",) or final):
        raise ValueError("C_SW_FULL is declared on the development worlds, deterministic only")
    if workers < 1 or threads < 1 or workers * threads > (os.cpu_count() or 1):
        raise ValueError("workers x threads must be positive and within os.cpu_count()")
    checkpoint_dir = Path(checkpoint_dir)
    record = read_checkpoint(checkpoint_dir, arm)
    out = Path(out)
    existing = [name for name in ("config.json", "summary.json", "manifest.json", "panels", "traces")
                if (out / name).exists()]
    if existing:
        raise FileExistsError(f"panel output already exists: {out} ({existing})")
    for sub in ("panels", "traces", "logs"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    checkpoint = record["checkpoint"]
    policy_seed = int(record["training_seed"])
    names = {mode: panel_name(arm, checkpoint, mode) for mode in modes}
    started = time.perf_counter()
    frame = adapter_record()
    summary: dict[str, Any] = {
        "object_id": B05_OBJECT_ID, "arm": arm, "status": "INCOMPLETE", "failure": None,
        "launch_sha": launch_sha, "checkpoint": checkpoint,
        "checkpoint_object_id": record["object_id"], "policy_seed": policy_seed,
        "final": bool(final), "worlds": list(worlds), "modes": list(modes),
        "counts": {"episodes_completed": 0, "steps": 0, "panels_completed": 0, "failed_worlds": 0},
        "panels": {}, "artifacts": {}}
    write_summary(out / "config.json", {
        "object_id": B05_OBJECT_ID, "arm": arm, "launch_sha": launch_sha,
        "argv": list(sys.argv if argv is None else argv), "checkpoint_dir": str(checkpoint_dir),
        "record": record, "worlds": list(worlds), "final": bool(final), "modes": list(modes),
        "panel_names": names, "feedback": asdict(PRODUCTION_PARAMS), "horizon": int(horizon),
        "policy_seed": policy_seed, "stochastic_draw": STOCHASTIC_DRAW,
        "sample_seed_rule": SAMPLE_SEED_RULE, "trace_timing": TRACE_TIMING,
        "controller_information": L_CONTROLLER_INFORMATION, "canonical_frame": frame,
        "full_speed": arm == "C_SW_FULL" and ("non-zero physical horizontal proposal rescaled "
                                              "to unit norm before the shield"),
        "device": device_name, "workers": int(workers), "threads": int(threads),
        "os_cpu_count": os.cpu_count()})
    summary["artifacts"]["config.json"] = sha256_file(out / "config.json")
    write_summary(out / "summary.json", summary)
    try:
        for mode in modes:
            name = names[mode]
            draw = STOCHASTIC_DRAW if mode == "stochastic" else None
            panel_started = time.perf_counter()
            tasks = [CanonicalTask(world=WorldTask(
                controller="L", seed=seed, params=PRODUCTION_PARAMS, horizon=int(horizon),
                policy_seed=policy_seed, threads=int(threads), device=device_name,
                checkpoint=str(checkpoint_dir / record["agent_pt"]),
                expected_checkpoint_sha256=record["agent_pt_sha256"],
                expected_policy_fingerprint=record["policy_fingerprint"],
                log_dir=str(out / "logs"), action_mode=mode, draw=draw,
                checkpoint_record=str(checkpoint_dir / "record.json")), arm=arm) for seed in worlds]

            def advance(result, name=name):
                row = result["row"]
                summary["counts"]["episodes_completed"] += 1
                summary["counts"]["steps"] += int(row.get("actual_length", 0))
                summary["counts"]["failed_worlds"] += int(bool(row.get("failed")))
                append_progress(out, {"event": "world_end", "panel": name, "seed": row["seed"],
                                      "frame": row.get("frame"), "failed": bool(row.get("failed"))},
                                dict(summary["counts"]))

            results = sorted(run_pool(evaluate_canonical_task, tasks, workers, advance),
                             key=lambda item: item["row"]["seed"])
            rows = [result["row"] for result in results]
            identities = {json.dumps(result["identity"], sort_keys=True) for result in results}
            panel = {"name": name, "arm": arm, "controller": "L", "checkpoint": checkpoint,
                     "rollout": record["rollout"], "transitions": record["transitions"],
                     "controller_information": L_CONTROLLER_INFORMATION,
                     "canonical_frame": frame, "params": asdict(PRODUCTION_PARAMS),
                     "action_mode": mode, "draw": draw, "policy_seed": policy_seed,
                     "final": bool(final), "worlds": rows, "aggregate": aggregate(rows),
                     "frames": {str(row["seed"]): row["frame"] for row in rows},
                     "failed_worlds": [row["seed"] for row in rows if row.get("failed")],
                     "policy_identity": [json.loads(item) for item in sorted(identities)],
                     "wall_seconds": time.perf_counter() - panel_started}
            if draw is not None:
                panel["sample_seeds"] = {str(row["seed"]): row.get("sample_seed") for row in rows}
            panel_path = out / "panels" / f"{name}.json"
            trace_path = out / "traces" / f"{name}.npz"
            write_summary(panel_path, panel)
            np.savez_compressed(trace_path, **canonical_trace_arrays(results))
            for path in (panel_path, trace_path):
                summary["artifacts"][str(path.relative_to(out))] = sha256_file(path)
            summary["panels"][name] = {key: panel[key] for key in panel if key != "worlds"}
            summary["counts"]["panels_completed"] += 1
            write_summary(out / "summary.json", summary)
        summary["status"] = "COMPLETE"
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        summary.update(wall_seconds=time.perf_counter() - started,
                       peak_rss_kib={"runner": int(own.ru_maxrss),
                                     "largest_worker": int(children.ru_maxrss)})
        write_summary(out / "summary.json", summary)
        try:
            (out / "logs").rmdir()
        except OSError:
            pass
        write_manifest(out, kind=f"panel {arm}", launch_sha=launch_sha, argv=argv,
                       extra={"checkpoint": {"dir": str(checkpoint_dir),
                                             "agent_pt_sha256": record["agent_pt_sha256"],
                                             "policy_fingerprint": record["policy_fingerprint"],
                                             "object_id": record["object_id"]},
                              "holdout": bool(final) and set(worlds) <= set(HOLDOUT_WORLDS)})
