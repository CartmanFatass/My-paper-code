"""One world = one serial deterministic episode under the parametrised return shield.

B07 ``evaluate_world`` hard-codes B06 ``apply_feedback`` and an HMASD evaluator, so it cannot
take the parametrised shield or the heuristic; this module keeps its step contract:
controller reset before ``env.reset(seed)``, proposal from the legal observation, shield modes
carried across steps (all False at world start), env stepped with the submitted action, B04
``metric_row`` check on every step, stop at native termination/truncation.  Equivalence with
B07 at production margins is pinned by test.

Each world builds its own evaluator exactly as B07 ``evaluate_panel`` does for its first world
(``seed_everything(policy_seed)`` -> ``HMASDAgent`` -> ``_sync_agent`` -> ``train(False)`` and the
episode inside the same ``preserved_rng`` block), so a world's result does not depend on which
process or in which order it runs.
"""

from __future__ import annotations

import copy
import multiprocessing
import resource
import tempfile
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import (
    NativeSpec,
    _sync_agent,
    _terminal_kind,
    initialization_fingerprint,
    make_config,
    make_env,
    optimizer_steps,
    preserved_rng,
    seed_everything,
    sha256_file,
)
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS, metric_row
from experiments.candidates.uav_service_auxiliary.b06.native import (
    _normalizer_snapshot,
    _same_snapshot,
)
from hmasd.agent import HMASDAgent

from .feedback import N_UAVS, FeedbackParams, apply_feedback_params
from .heuristic import CONTROLLER_INFORMATION, HeuristicParams, LayoutHeuristic, UnobservedRegime
from .observation import S7S2_LAYOUT, own_energy

DOCK_REQUEST_THRESHOLD = 0.5  # env ``dock_request_threshold``
QOS = TRACE_FIELDS.index("qos_satisfaction_ratio")
THROUGHPUT = TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")
CHARGER_INPUT = TRACE_FIELDS.index("step_charger_input_wh")
BATTERY_MIN = TRACE_FIELDS.index("battery_min_ratio")


def make_eval_config(horizon: int, policy_seed: int):
    """One-lane S7-S2 evaluator config (B01 ``make_config``) with the fixed native contract."""
    spec = NativeSpec(seed=int(policy_seed), lanes=1, rollouts=1,
                      rollout_length=int(horizon), episode_length=int(horizon))
    config = make_config(spec)
    if (
        config.n_agents != N_UAVS or config.obs_dim != 365 or config.action_dim != 4
        or config.k != 10 or config.lambda_return != 2.0 or config.lambda_e != 1.0
        or config.battery_capacity_wh != 160.0 or config.use_obsnorm or config.use_statenorm
        or config.num_envs != 1 or config.episode_length != int(horizon)
        or config.max_steps != int(horizon)
    ):
        raise ValueError("B01 evaluation config violates the fixed S7-S2 native contract")
    return config


class PolicyController:
    """Deterministic HMASD evaluator, called exactly as B07 ``evaluate_world`` calls it."""

    def __init__(self, evaluator: HMASDAgent):
        self.evaluator = evaluator

    def reset(self) -> None:
        self.evaluator.reset_env_state(0)

    def propose(self, observations, state, step, previous_done, modes):
        actions, _, _ = self.evaluator.step(
            state[None], observations[None], np.asarray([step]), previous_done,
            deterministic=True, return_step_data=True, build_infos=False,
        )
        return np.asarray(actions[0], dtype=np.float32)


PLAN_SOURCE = "env-ground-truth"


def central_plan_inputs(env) -> dict[str, np.ndarray]:
    """Ground-truth user/BS xy from the raw environment (central-information reference)."""
    raw = getattr(env, "env", env)
    return {"users_xy": np.asarray(raw.user_positions, dtype=np.float64)[:, :2].copy(),
            "bs_xy": np.asarray(raw.ground_bs_positions, dtype=np.float64)[:, :2].copy()}


class HeuristicController:
    """Layout heuristic: legal observation + prior shield modes every step; in ``central``
    mode ground-truth user/BS xy from ``env`` at replan steps only."""

    def __init__(self, params: HeuristicParams, env=None):
        if params.information == "central" and env is None:
            raise ValueError("central heuristic needs the environment for plan inputs")
        self.heuristic = LayoutHeuristic(params)
        self.env = env
        self.plan_input_steps: list[int] = []
        self.search_replan_steps: list[int] = []

    def reset(self) -> None:
        self.heuristic.reset()
        self.plan_input_steps = []
        self.search_replan_steps = []

    def propose(self, observations, state, step, previous_done, modes):
        plan_inputs = None
        replans = self.heuristic.replans_next()
        if self.heuristic.params.information == "central" and replans:
            plan_inputs = central_plan_inputs(self.env)
            self.plan_input_steps.append(int(step))
        actions = self.heuristic.act(observations, modes, plan_inputs)
        if replans and self.heuristic.last_plan["search"]:
            self.search_replan_steps.append(int(step))
        return actions


def raw_guard_env(env):
    """The wrapped environment object that carries the backhaul action-guard counters."""
    raw = env
    while not hasattr(raw, "backhaul_guard_checked_actions"):
        if not hasattr(raw, "env"):
            raise AttributeError("no wrapped env exposes backhaul_guard_checked_actions")
        raw = raw.env
    return raw


def guard_counters(env) -> tuple[int, int]:
    """(checked, blocked) guard actions of the step just taken.

    ``UAVRoutedRelayEnv.step`` resets both counters to 0 at the start of every step
    (routed_core.py), so they are per-step counts; the row reports their episode sums.
    """
    raw = raw_guard_env(env)
    return int(raw.backhaul_guard_checked_actions), int(raw.backhaul_guard_blocked_actions)


def _spells(values: np.ndarray) -> np.ndarray:
    """Lengths of maximal True runs along axis 0 for every column (right-censored included)."""
    lengths = []
    for column in np.asarray(values, dtype=bool).T:
        padded = np.concatenate(([False], column, [False])).astype(np.int8)
        changes = np.diff(padded)
        lengths.extend((np.flatnonzero(changes == -1) - np.flatnonzero(changes == 1)).tolist())
    return np.asarray(lengths, dtype=np.int64)


def _mean_or_none(values: np.ndarray):
    return float(values.mean()) if values.size else None


def world_row(seed: int, rewards: np.ndarray, metrics: np.ndarray, ends: np.ndarray,
              steps: dict[str, np.ndarray], *, time_step_s: float) -> dict[str, Any]:
    """B04 ``metric_row`` aggregates plus the B01 mode/phase/charging/guard readings.

    Phase split of team QoS/step (boundaries from the step index t):
    pre_entry t < first_entry_step (all steps when no UAV ever enters F mode),
    entry_to_input first_entry_step <= t < first_input_step (to the end when there is never
    charger input; empty when no entry), post_input t >= first_input_step (empty when never).
    When charger input precedes the first entry (the policy can dock on its own dock bit),
    ``input_before_entry`` is True and pre_entry/post_input overlap as defined.
    """
    length = int(len(rewards))
    qos = metrics[:, QOS]
    mode, charging = steps["mode"], steps["charging"]
    waiting = steps["waiting_steps"] > 0
    entries = np.flatnonzero(steps["entered"].any(axis=1))
    inputs = np.flatnonzero(metrics[:, CHARGER_INPUT] > 0.0)
    first_entry = int(entries[0]) if entries.size else None
    first_input = int(inputs[0]) if inputs.size else None
    index = np.arange(length)
    entry_bound = length if first_entry is None else first_entry
    input_bound = length if first_input is None else first_input
    pre_entry = qos[index < entry_bound]
    entry_to_input = (qos[(index >= first_entry) & (index < input_bound)]
                      if first_entry is not None else qos[:0])
    post_input = qos[index >= input_bound]
    spells = _spells(charging)
    row: dict[str, Any] = {
        "seed": int(seed),
        "actual_length": length,
        "terminal_type": _terminal_kind(bool(ends[-1, 0]), bool(ends[-1, 1])),
        "raw_native_J": float(rewards.sum()),
        "native_J_per_step": float(rewards.mean()),
        "episode_minimum_battery_ratio": float(metrics[:, BATTERY_MIN].min()),
    }
    for column, field in enumerate(TRACE_FIELDS):
        row[f"{field}_sum"] = float(metrics[:, column].sum())
        row[f"{field}_per_step"] = float(metrics[:, column].mean())
    row.update(
        cumulative_qos=float(qos.sum()),
        qos_per_step=float(qos.mean()),
        delivered_megabits=float(metrics[:, THROUGHPUT].sum() * time_step_s),
        mode_uav_step_fraction=float(mode.sum() / (N_UAVS * length)),
        first_entry_step=first_entry,
        first_input_step=first_input,
        input_before_entry=bool(first_input is not None
                                and (first_entry is None or first_input < first_entry)),
        steps_pre_entry=int(pre_entry.size),
        steps_entry_to_input=int(entry_to_input.size),
        steps_post_input=int(post_input.size),
        qos_per_step_pre_entry=_mean_or_none(pre_entry),
        qos_per_step_entry_to_input=_mean_or_none(entry_to_input),
        qos_per_step_post_input=_mean_or_none(post_input),
        charger_input_wh=float(metrics[:, CHARGER_INPUT].sum()),
        charging_uav_steps=int(charging.sum()),
        charging_spell_count=int(spells.size),
        one_tick_spell_count=int(np.count_nonzero(spells == 1)),
        one_tick_spell_share=(float(np.mean(spells == 1)) if spells.size else None),
        wait_ticks_total=int(waiting.sum()),
        zero_service=bool(np.all(qos == 0.0)),
        min_decoded_battery=float(steps["battery"].min()),
        feedback_mode_uav_steps=int(mode.sum()),
        feedback_entry_count=int(steps["entered"].sum()),
        feedback_exit_count=int(steps["exited"].sum()),
        dock_bit_uav_steps=int(steps["dock_bit"].sum()),
        guard_checked_actions=int(steps["guard_checked"].sum()),
        guard_blocked_actions=int(steps["guard_blocked"].sum()),
    )
    return row


def evaluate_world(controller, env, config, seed: int, params: FeedbackParams, *,
                   progress: Callable[[int], None] | None = None):
    """Run one deterministic episode; returns (row, per-step arrays)."""
    controller.reset()
    observations, info = env.reset(seed=int(seed))
    observations = np.asarray(observations, dtype=np.float32)
    state = np.asarray(info["state"], dtype=np.float32)
    previous_done = np.ones(1, dtype=bool)
    modes = np.zeros(N_UAVS, dtype=bool)
    rewards, metrics, ends = [], [], []
    keys = ("mode", "entered", "exited", "charging", "waiting_steps", "battery", "dock_bit",
            "guard_checked", "guard_blocked")
    steps: dict[str, list] = {key: [] for key in keys}
    layout = replace(S7S2_LAYOUT, max_steps=int(config.max_steps))  # waiting = steps/max_steps
    for step in range(int(config.episode_length)):
        proposed = controller.propose(observations, state, step, previous_done, modes.copy())
        decision = apply_feedback_params(observations, proposed, modes, params)
        modes = decision.modes
        submitted = decision.submitted_actions
        next_obs, reward, terminated, truncated, next_info = env.step(submitted)
        checked, blocked = guard_counters(env)
        metrics.append(metric_row(reward, next_info["reward_info"]))
        rewards.append(float(reward))
        ends.append((bool(terminated), bool(truncated)))
        next_obs = np.asarray(next_obs, dtype=np.float32)
        own = own_energy(next_obs, layout)
        steps["mode"].append(modes.copy())
        steps["entered"].append(decision.entered)
        steps["exited"].append(decision.exited)
        steps["charging"].append(own["charging"])
        steps["waiting_steps"].append(own["waiting_steps"])
        steps["battery"].append(own["battery"])
        steps["dock_bit"].append(submitted[:, 3] > DOCK_REQUEST_THRESHOLD)
        steps["guard_checked"].append(checked)
        steps["guard_blocked"].append(blocked)
        if progress is not None:
            progress(1)
        observations = next_obs
        state = np.asarray(next_info["next_state"], dtype=np.float32)
        previous_done[:] = terminated or truncated
        if previous_done[0]:
            break
    if not previous_done[0]:
        raise RuntimeError("B01 evaluation did not reach native termination/truncation")
    reward_array = np.asarray(rewards, dtype=np.float64)
    metric_array = np.asarray(metrics, dtype=np.float64)
    end_array = np.asarray(ends, dtype=bool)
    step_arrays = {key: np.asarray(value) for key, value in steps.items()}
    step_arrays["guard_checked"] = step_arrays["guard_checked"].astype(np.int64)
    step_arrays["guard_blocked"] = step_arrays["guard_blocked"].astype(np.int64)
    row = world_row(seed, reward_array, metric_array, end_array, step_arrays,
                    time_step_s=float(config.time_step))
    step_arrays.update(reward=reward_array, metrics=metric_array, ends=end_array)
    return row, step_arrays


@dataclass(frozen=True)
class WorldTask:
    """Picklable description of one world evaluation (spawn workers rebuild everything)."""

    controller: str
    seed: int
    params: FeedbackParams
    horizon: int
    policy_seed: int
    threads: int
    device: str = "cpu"
    checkpoint: str | None = None
    expected_checkpoint_sha256: str | None = None
    expected_policy_fingerprint: str | None = None
    heuristic: HeuristicParams | None = None
    log_dir: str | None = None


def load_policy(task: WorldTask, config, device: torch.device, log_dir: str):
    if task.checkpoint is None:
        raise ValueError("controller N requires a checkpoint")
    checkpoint_sha = sha256_file(Path(task.checkpoint))
    if task.expected_checkpoint_sha256 is not None and checkpoint_sha != task.expected_checkpoint_sha256:
        raise ValueError(f"checkpoint sha256 {checkpoint_sha} != expected")
    seed_everything(int(task.policy_seed), device)
    agent = HMASDAgent(config, log_dir=log_dir, device=device)
    agent.load_model(task.checkpoint)
    agent.train(False)
    fingerprint = initialization_fingerprint(agent)
    if task.expected_policy_fingerprint is not None and fingerprint != task.expected_policy_fingerprint:
        raise ValueError(f"restored policy fingerprint {fingerprint} != expected")
    return agent, {"checkpoint_sha256": checkpoint_sha, "policy_fingerprint": fingerprint}


def evaluate_task(task: WorldTask) -> dict[str, Any]:
    """Module-level worker: one world, fully rebuilt from the task (picklable)."""
    started = time.perf_counter()
    torch.set_num_threads(int(task.threads))
    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError("B01 requires Torch FP32 default dtype")
    device = torch.device(task.device)
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    config = make_eval_config(task.horizon, task.policy_seed)
    identity: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="b01-agent-logs-", dir=task.log_dir) as log_dir:
        env = make_env(config, task.seed)
        try:
            if task.controller == "N":
                agent, identity = load_policy(task, config, device, log_dir)
                before = (initialization_fingerprint(agent), optimizer_steps(agent),
                          _normalizer_snapshot(agent))
                with preserved_rng():
                    seed_everything(int(task.policy_seed), device)
                    evaluator = HMASDAgent(copy.deepcopy(config), log_dir=log_dir, device=device)
                    _sync_agent(agent, evaluator)
                    evaluator.train(False)
                    evaluator_before = (initialization_fingerprint(evaluator),
                                        optimizer_steps(evaluator),
                                        _normalizer_snapshot(evaluator))
                    if evaluator_before[0] != before[0]:
                        raise RuntimeError("evaluator policy differs from restored checkpoint")
                    row, arrays = evaluate_world(PolicyController(evaluator), env, config,
                                                 task.seed, task.params)
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
                row["controller_information"] = "legal-observation"
                row["failed"] = False
            elif task.controller.startswith("H"):
                if task.heuristic is None:
                    raise ValueError("heuristic controller requires HeuristicParams")
                controller = HeuristicController(task.heuristic, env)
                labels = dict(
                    controller_information=CONTROLLER_INFORMATION[task.heuristic.information],
                    plan_source=(PLAN_SOURCE if task.heuristic.information == "central"
                                 else "legal-observation"),
                )
                try:
                    row, arrays = evaluate_world(controller, env, config, task.seed, task.params)
                except UnobservedRegime as exc:
                    # Recorded, never silently skipped: the world is marked failed.
                    row, arrays = {"seed": int(task.seed), "failed": True,
                                   "failure": f"UnobservedRegime: {exc}", **labels}, {}
                else:
                    row.update(
                        failed=False, **labels,
                        plan_input_steps=len(controller.plan_input_steps),
                        search_replans=len(controller.search_replan_steps),
                        replans=-(-row["actual_length"] // task.heuristic.replan_period),
                    )
            else:
                raise ValueError(f"unknown controller {task.controller!r}")
        finally:
            env.close()
    row.update(controller=task.controller, enter_margin=task.params.enter_margin,
               exit_margin=task.params.exit_margin,
               wall_seconds=time.perf_counter() - started,
               worker_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    return {"row": row, "arrays": arrays, "identity": identity}


def run_tasks(tasks: Iterable[WorldTask], workers: int, *,
              on_result: Callable[[dict[str, Any]], None] | None = None) -> list[dict[str, Any]]:
    """Evaluate worlds serially (workers <= 1) or in spawn processes; ordered by seed."""
    tasks = list(tasks)
    results = []
    if int(workers) <= 1 or len(tasks) <= 1:
        for task in tasks:
            result = evaluate_task(task)
            results.append(result)
            if on_result is not None:
                on_result(result)
    else:
        context = multiprocessing.get_context("spawn")
        with context.Pool(processes=min(int(workers), len(tasks))) as pool:
            for result in pool.imap(evaluate_task, tasks, chunksize=1):
                results.append(result)
                if on_result is not None:
                    on_result(result)
    return sorted(results, key=lambda item: item["row"]["seed"])


def trace_arrays(results: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    """float32 per-step arrays per world for ``traces/<panel>.npz``."""
    arrays: dict[str, np.ndarray] = {}
    for index, result in enumerate(results):
        prefix = f"world_{index}_"
        data = result["arrays"]
        if result["row"].get("failed"):
            arrays[prefix + "seed"] = np.asarray(result["row"]["seed"], dtype=np.int64)
            arrays[prefix + "failed"] = np.asarray(True)
            continue
        arrays[prefix + "seed"] = np.asarray(result["row"]["seed"], dtype=np.int64)
        arrays[prefix + "reward"] = data["reward"].astype(np.float32)
        arrays[prefix + "qos"] = data["metrics"][:, QOS].astype(np.float32)
        for key in ("mode", "charging", "waiting_steps", "battery", "dock_bit"):
            arrays[prefix + key] = data[key].astype(np.float32)
    return arrays


PHASE_SPLIT_KEYS = ("qos_per_step_pre_entry", "qos_per_step_entry_to_input",
                    "qos_per_step_post_input")


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Means over completed worlds of every numeric world field (None values excluded and
    counted; phase-split QoS always carries its ``observed_`` count).  Failed worlds are
    listed and excluded from every mean."""
    skip = {"seed", "enter_margin", "exit_margin", "worker_peak_rss_kib", "plan_input_steps",
            "replans", "width", "matched_pair_id"}
    failed = [row for row in rows if row.get("failed")]
    completed = [row for row in rows if not row.get("failed")]
    result: dict[str, Any] = {"worlds": len(rows), "completed_worlds": len(completed),
                              "failed_worlds": [row["seed"] for row in failed]}
    if not completed:
        return result
    rows = completed
    for key, value in rows[0].items():
        if key in skip or isinstance(value, (str, bool)):
            continue
        if not (value is None or isinstance(value, (int, float))):
            continue
        values = [row[key] for row in rows if row[key] is not None]
        result[f"mean_{key}"] = float(np.mean(values)) if values else None
        if len(values) != len(rows) or key in PHASE_SPLIT_KEYS:
            result[f"observed_{key}"] = len(values)
    result.update(
        input_before_entry_worlds=sum(row["input_before_entry"] for row in rows),
        zero_service_worlds=sum(row["zero_service"] for row in rows),
        minimum_episode_battery_ratio=min(row["episode_minimum_battery_ratio"] for row in rows),
        actual_transitions=sum(row["actual_length"] for row in rows),
        terminal_types={kind: sum(row["terminal_type"] == kind for row in rows)
                        for kind in sorted({row["terminal_type"] for row in rows})},
    )
    return result
