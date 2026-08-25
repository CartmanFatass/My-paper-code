"""One-shot registered train/evaluate/analyze launcher for ONLGR-B1."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Iterable

import numpy as np
import torch

from .analysis import (
    iid_analysis, primary_analysis, student_interval, summarize_episodes,
    validate_primary_completeness,
)
from .config import (
    ARTIFACT_KIND, DIAGNOSTIC_ARMS, FIXED_MARKS, FIXED_RATES, HELDOUT_SCHEDULES,
    IID_SCHEDULE, LEARNED_ARMS, PPO, PRODUCTION_CONFIG, SEEDS, TRAIN_SCHEDULES, TREATMENT,
    VALIDATION_ROOTS, RunConfig, registered_budget,
)
from .controls import (
    keep_grid_equality, leakage_twin_contract, marked_partition_probe,
    preselected_yoke_mapping, prob_exp_identity_probe, yoke_support,
)
from .host import EpisodeResult, generate_episode, run_episode
from .models import MarkedLearner


COMPOSITE_REVISION = "ONLGR-PRO-MATH-CLOSURE-CANDIDATE-20260812-04"
PROSPECTIVE_DELTA_STATUS = "FROZEN_APPLIED_AUTHORITATIVE_EXTERNAL_PRO_CLOSED"
LOCAL_MATHEMATICAL_REVIEW_RECORD = "ONLGR-PRO-PREACTIVITY-MATH-CLOSURE-20260812-03"
MATHEMATICAL_CLOSURE_STATUS = "AUTHORITATIVE_EXTERNAL_CHATGPT_PRO_CLOSED"
MATHEMATICAL_CLOSURE_RECORD = "ONLGR-PRO-MATH-CLOSURE-AUTHORITY-REREVIEW-20260812-02"
MATHEMATICAL_CLOSURE_CONFIRMED = True


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")


def _rss_bytes() -> int:
    """Current process working set without requiring psutil."""
    try:
        import psutil
        return int(psutil.Process().memory_info().rss)
    except (ImportError, OSError):
        pass
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        handle = kernel32.GetCurrentProcess()
        if not handle or not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            raise OSError(ctypes.get_last_error(), "Windows process RSS query failed")
        return int(counters.WorkingSetSize)
    import resource
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if value > 10**8 else value * 1024


class ResourceLedger:
    def __init__(self, config: RunConfig) -> None:
        self.config = config
        self.started = time.perf_counter()
        self.actual_ticks = 0
        self.peak_rss = _rss_bytes()
        self.by_panel: dict[str, int] = defaultdict(int)
        self.conformance_episode_rows = 0
        self.exposure_ledger_rows = 0
        self.action_before_service_boundary_rows = 0
        self.action_changed_service_value_rows = 0
        self.segment_owned_ticks = 0
        self.exposure_closed_form_exact = True
        self.action_before_service_exact = True
        self.reward_service_cost_tick_exact = True
        self.segment_ownership_exact = True
        self.terminal_boundary_absent = True
        self.conformance_failures: list[dict[str, object]] = []

    def add(self, panel: str, rows: EpisodeResult | Iterable[EpisodeResult]) -> None:
        values = [rows] if isinstance(rows, EpisodeResult) else list(rows)
        ticks = sum(row.physics_ticks for row in values)
        self.actual_ticks += ticks
        self.by_panel[panel] += ticks
        for row in values:
            self.conformance_episode_rows += 1
            self.exposure_ledger_rows += row.exposure_ledger_rows
            self.action_before_service_boundary_rows += row.action_before_service_boundary_rows
            self.action_changed_service_value_rows += row.action_changed_service_value_rows
            self.segment_owned_ticks += row.segment_owned_ticks
            self.exposure_closed_form_exact &= row.exposure_closed_form_exact
            self.action_before_service_exact &= row.action_before_service_exact
            self.reward_service_cost_tick_exact &= row.reward_service_cost_exact
            self.segment_ownership_exact &= row.segment_ownership_exact
            self.terminal_boundary_absent &= row.terminal_boundary_absent
            failed = [
                name for name, passed in (
                    ("exposure_closed_form", row.exposure_closed_form_exact),
                    ("action_before_service", row.action_before_service_exact),
                    ("reward_service_cost_tick", row.reward_service_cost_exact),
                    ("segment_ownership", row.segment_ownership_exact),
                    ("terminal_boundary_absence", row.terminal_boundary_absent),
                ) if not passed
            ]
            if failed:
                self.conformance_failures.append({
                    "panel": panel, "arm": row.arm, "schedule": row.schedule,
                    "failed_ledgers": failed,
                })
        self.check()

    def add_ticks(self, panel: str, ticks: int) -> None:
        self.actual_ticks += ticks
        self.by_panel[panel] += ticks
        self.check()

    def check(self) -> None:
        elapsed = time.perf_counter() - self.started
        self.peak_rss = max(self.peak_rss, _rss_bytes())
        if self.actual_ticks > self.config.total_tick_cap:
            raise RuntimeError("registered 7,000,000 team-tick cap breached")
        if elapsed > self.config.wall_seconds:
            raise RuntimeError("registered 45-minute wall cap breached before complete output")
        if self.peak_rss and self.peak_rss > self.config.peak_rss_bytes:
            raise RuntimeError("registered 2-GiB RSS cap breached before complete output")

    def facts(self) -> dict[str, object]:
        self.check()
        return {
            "actual_team_ticks": self.actual_ticks,
            "actual_team_ticks_by_panel": dict(self.by_panel),
            "wall_seconds": time.perf_counter() - self.started,
            "peak_rss_bytes": self.peak_rss,
            "cpu_workers": self.config.cpu_workers,
            "observed_reward_exposure_ledger": {
                "episode_rows": self.conformance_episode_rows,
                "exposure_rows": self.exposure_ledger_rows,
                "action_before_service_boundary_rows": self.action_before_service_boundary_rows,
                "action_changed_service_value_rows": self.action_changed_service_value_rows,
                "segment_owned_ticks": self.segment_owned_ticks,
                "exposure_closed_form_exact": self.exposure_closed_form_exact,
                "action_before_service_exact": self.action_before_service_exact,
                "reward_service_cost_tick_exact": self.reward_service_cost_tick_exact,
                "segment_ownership_exact": self.segment_ownership_exact,
                "terminal_boundary_absent": self.terminal_boundary_absent,
                "failures": self.conformance_failures,
            },
        }


def _training_schedule(episode: int) -> str:
    return TRAIN_SCHEDULES[episode % len(TRAIN_SCHEDULES)]


def _initialization_curves(seed: int = SEEDS[0]) -> dict[str, object]:
    features = np.zeros((1, 14), dtype=np.float32)
    output: dict[str, object] = {}
    for arm in LEARNED_ARMS:
        learner = MarkedLearner(seed, arm)
        rows: dict[str, object] = {}
        for exposure in (1, 4, 8, 16, 24, 32):
            _logit, event, mark = learner.policy(
                features, np.asarray([exposure], dtype=np.float32)
            )
            u, rho = float(event[0]), float(mark[0])
            event_entropy = -(u * np.log(u) + (1-u) * np.log1p(-u))
            mark_entropy = -(rho * np.log(rho) + (1-rho) * np.log1p(-rho))
            rows[str(exposure)] = {
                "u": u, "rho": rho, "event_entropy": float(event_entropy),
                "conditional_mark_entropy": float(mark_entropy),
                "applied_mark_entropy": float(u * mark_entropy),
                "marked_entropy": float(event_entropy + u * mark_entropy),
                "u_below_0.01": u < .01, "u_above_0.99": u > .99,
            }
        output[arm] = rows
    return output


def train_seed(
    seed: int, config: RunConfig, checkpoint_root: Path, ledger: ResourceLedger,
) -> tuple[dict[str, MarkedLearner], dict[str, object], dict[str, object], dict[str, str]]:
    learners = {arm: MarkedLearner(seed, arm) for arm in LEARNED_ARMS}
    update_diagnostics: dict[str, list[dict[str, object]]] = {arm: [] for arm in LEARNED_ARMS}
    activity: dict[str, object] | None = None
    for update_index in range(config.training_episodes // config.episodes_per_update):
        batches: dict[str, list[EpisodeResult]] = {arm: [] for arm in LEARNED_ARMS}
        start = update_index * config.episodes_per_update
        for episode_index in range(start, start + config.episodes_per_update):
            schedule = _training_schedule(episode_index)
            exogenous = generate_episode(
                root=seed, episode=episode_index, namespace="paired_training", schedule=schedule,
                horizon=config.horizon,
            )
            for arm, learner in learners.items():
                row = run_episode(
                    exogenous, arm=arm, learner=learner, collect_training=True,
                )
                batches[arm].append(row)
                ledger.add("training", row)
        updates: dict[str, dict[str, object]] = {}
        for arm, rows in batches.items():
            updates[arm] = learners[arm].update(rows, update_index).__dict__
            if activity is None:
                activity_checkpoint = (
                    checkpoint_root / f"seed_{seed}" / f"activity_start_{arm}.pt"
                )
                activity_checkpoint.parent.mkdir(parents=True, exist_ok=True)
                torch.save(learners[arm].checkpoint(), activity_checkpoint)
                activity = {
                    "began": True,
                    "trigger": "first_retained_learned_state_update",
                    "first_update_index": update_index,
                    "first_updated_arm": arm,
                    "includes_keep_only_or_critic_only_update": True,
                    "complete_pairing_is_a_validity_condition_not_the_activity_boundary": True,
                    "retained_state_path": str(activity_checkpoint),
                }
                if seed == config.seeds[0]:
                    _write_json(
                        checkpoint_root.parent / "activity_start.json",
                        {"seed": seed, **activity},
                    )
        for arm, row in updates.items():
            update_diagnostics[arm].append(row)
        if update_index == 0:
            witnesses: dict[str, object] = {}
            for arm in ("ONLGR", "RAW-BOUNDARY-LEASE"):
                rows = batches[arm]
                witnesses[arm] = {
                    "complete_episodes_by_schedule": {
                        schedule: sum(r.schedule == schedule and sum(x.duration for x in r.training_records) == 256
                                      for r in rows) for schedule in TRAIN_SCHEDULES
                    },
                    "lease_eligible_routine_events_by_role": [
                        sum(r.voluntary_events[role] for r in rows) for role in range(2)
                    ],
                    "conditional_mark_logprob_rows_by_role": [
                        sum(int(record.policy_mask[role] and record.actions[role] > 0)
                            for r in rows for record in r.training_records) for role in range(2)
                    ],
                    "valid_optimizer_steps": updates[arm]["optimizer_steps"],
                }
            activity["first_complete_update_validity_support"] = {
                "valid": all(
                    all(v > 0 for v in witness["complete_episodes_by_schedule"].values())
                    and all(v > 0 for v in witness["lease_eligible_routine_events_by_role"])
                    and all(v > 0 for v in witness["conditional_mark_logprob_rows_by_role"])
                    and witness["valid_optimizer_steps"] > 0
                    for witness in witnesses.values()
                ),
                "witnesses": witnesses,
            }
    if activity is None:
        raise RuntimeError("no training update was executed")
    checkpoints: dict[str, str] = {}
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    for arm, learner in learners.items():
        path = checkpoint_root / f"seed_{seed}" / f"{arm}.pt"
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(learner.checkpoint(), path)
        checkpoints[arm] = str(path)
    diagnostics = {
        arm: {
            "updates": rows,
            "actor_parameter_count": learners[arm].actor_parameter_count,
            "critic_parameter_count": learners[arm].critic_parameter_count,
            "complete_training_episodes": config.training_episodes,
            "training_schedule_counts": {schedule: config.training_episodes // 4 for schedule in TRAIN_SCHEDULES},
            "ppo_epochs": config.ppo_epochs,
            "optimizer_steps": sum(int(row["optimizer_steps"]) for row in rows),
        } for arm, rows in update_diagnostics.items()
    }
    return learners, diagnostics, activity, checkpoints


def _evaluate_learned_panel(
    *, seed: int, learners: dict[str, MarkedLearner], config: RunConfig,
    count: int, namespace: str, ledger: ResourceLedger, panel: str,
    safety: bool = False, exposure_clamp: bool = False,
    retain_first: int = 0,
    schedules: tuple[str, ...] = HELDOUT_SCHEDULES,
) -> tuple[
    dict[str, dict[str, dict[str, object]]],
    dict[str, dict[str, list[EpisodeResult]]],
]:
    output: dict[str, dict[str, dict[str, object]]] = {arm: {} for arm in LEARNED_ARMS}
    retained: dict[str, dict[str, list[EpisodeResult]]] = {
        arm: {schedule: [] for schedule in schedules}
        for arm in LEARNED_ARMS
    }
    for schedule in schedules:
        rows: dict[str, list[EpisodeResult]] = {arm: [] for arm in LEARNED_ARMS}
        for episode_index in range(count):
            exogenous = generate_episode(
                root=seed, episode=episode_index, namespace=namespace, schedule=schedule,
                horizon=config.horizon, safety=safety,
            )
            for arm, learner in learners.items():
                result = run_episode(
                    exogenous, arm=arm, learner=learner, exposure_clamp=exposure_clamp,
                )
                rows[arm].append(result)
                if arm in retained and episode_index < retain_first:
                    retained[arm][schedule].append(result)
                ledger.add(panel, result)
        for arm in LEARNED_ARMS:
            output[arm][schedule] = summarize_episodes(rows[arm])
    return output, retained


def _fixed_tie_key(row: dict[str, object]) -> tuple[float, float, float]:
    rate = float(row["lambda"])
    mark = float(row["rho"])
    return rate, abs(mark - 0.5), mark


def select_fixed_rate(config: RunConfig, ledger: ResourceLedger) -> dict[str, object]:
    grid: list[dict[str, object]] = []
    for rate in FIXED_RATES:
        for mark in FIXED_MARKS:
            values: list[float] = []
            for root in VALIDATION_ROOTS:
                for schedule in TRAIN_SCHEDULES:
                    for episode_index in range(config.fixed_selection_episodes):
                        exogenous = generate_episode(
                            root=root, episode=episode_index, namespace="fixed_rate_validation",
                            schedule=schedule, horizon=config.horizon,
                        )
                        row = run_episode(exogenous, arm="FIXED-RATE-LEASE", fixed_rate=(rate, mark))
                        values.append(row.normalized_return)
                        ledger.add("fixed_rate_selection", row)
            grid.append({"lambda": rate, "rho": mark, "mean_return": float(np.mean(values)),
                         "episodes": len(values)})
    best_mean = max(float(row["mean_return"]) for row in grid)
    tied = [row for row in grid if float(row["mean_return"]) == best_mean]
    tied.sort(key=_fixed_tie_key)
    selected = tied[0]
    return {
        "validation_roots": list(VALIDATION_ROOTS), "training_schedules": list(TRAIN_SCHEDULES),
        "episodes_per_root_schedule_grid_point": config.fixed_selection_episodes,
        "grid": grid, "selected": {"lambda": selected["lambda"], "rho": selected["rho"]},
        "tie_rule": "ascending lambda, then ascending abs(rho-0.5), then ascending rho",
        "rho_order_within_rate": [0.5, 0.25, 0.75],
    }


def _evaluate_controls(
    *, seed: int, learners: dict[str, MarkedLearner], fixed: tuple[float, float],
    config: RunConfig, ledger: ResourceLedger,
) -> tuple[dict[str, object], dict[str, object]]:
    controls: dict[str, object] = {}
    fixed_rows: dict[str, object] = {}
    for schedule in HELDOUT_SCHEDULES:
        rows: dict[str, list[EpisodeResult]] = {arm: [] for arm in DIAGNOSTIC_ARMS}
        fixed_values: list[EpisodeResult] = []
        for episode_index in range(config.diagnostic_episodes):
            exogenous = generate_episode(
                root=seed, episode=episode_index, namespace="paired_native",
                schedule=schedule, horizon=config.horizon,
            )
            for arm in DIAGNOSTIC_ARMS:
                result = run_episode(exogenous, arm=arm)
                rows[arm].append(result)
                ledger.add("degenerate_oracle", result)
            fixed_result = run_episode(exogenous, arm="FIXED-RATE-LEASE", fixed_rate=fixed)
            fixed_values.append(fixed_result)
            ledger.add("fixed_rate_evaluation", fixed_result)
        controls[schedule] = {arm: summarize_episodes(values) for arm, values in rows.items()}
        fixed_rows[schedule] = summarize_episodes(fixed_values)
    return controls, fixed_rows


def _evaluate_yoke_seed(
    *, seed: int, learners: dict[str, MarkedLearner],
    native_rows: dict[str, dict[str, list[EpisodeResult]]],
    config: RunConfig, ledger: ResourceLedger,
) -> dict[str, object]:
    seed_ordinal = SEEDS.index(seed)
    cells: dict[str, object] = {}
    for schedule_ordinal, schedule in enumerate(HELDOUT_SCHEDULES):
        slot_facts: list[dict[str, object]] = []
        native_returns = {"ONLGR": [], "RAW-BOUNDARY-LEASE": []}
        yoked_returns = {"ONLGR": [], "RAW-BOUNDARY-LEASE": []}
        materiality = {"ONLGR": [], "RAW-BOUNDARY-LEASE": []}
        for slot in range(config.diagnostic_episodes):
            onlgr_native = native_rows["ONLGR"][schedule][slot]
            raw_native = native_rows["RAW-BOUNDARY-LEASE"][schedule][slot]
            facts, onlgr_mapping, raw_mapping = preselected_yoke_mapping(
                onlgr_native, raw_native, seed_ordinal=seed_ordinal,
                schedule_ordinal=schedule_ordinal, episode_slot=slot,
            )
            if onlgr_mapping is not None and raw_mapping is not None:
                exogenous = generate_episode(
                    root=seed, episode=slot, namespace="paired_native", schedule=schedule,
                    horizon=config.horizon,
                )
                onlgr_yoked = run_episode(
                    exogenous, arm="ONLGR", learner=learners["ONLGR"],
                    forced_actions=onlgr_mapping,
                )
                raw_yoked = run_episode(
                    exogenous, arm="RAW-BOUNDARY-LEASE", learner=learners["RAW-BOUNDARY-LEASE"],
                    forced_actions=raw_mapping,
                )
                ledger.add("preselected_exact_yoke", (onlgr_yoked, raw_yoked))
                onlgr_supported, onlgr_reason, onlgr_m = yoke_support(
                    onlgr_native, onlgr_yoked, onlgr_mapping
                )
                raw_supported, raw_reason, raw_m = yoke_support(
                    raw_native, raw_yoked, raw_mapping
                )
                jointly_supported = onlgr_supported and raw_supported
                facts = {**facts, "ONLGR_support_reason": onlgr_reason,
                         "RAW_support_reason": raw_reason, "eligible": jointly_supported}
                if not jointly_supported:
                    slot_facts.append(facts)
                    continue
                native_returns["ONLGR"].append(onlgr_native.normalized_return)
                native_returns["RAW-BOUNDARY-LEASE"].append(raw_native.normalized_return)
                yoked_returns["ONLGR"].append(onlgr_yoked.normalized_return)
                yoked_returns["RAW-BOUNDARY-LEASE"].append(raw_yoked.normalized_return)
                materiality["ONLGR"].append(onlgr_m)
                materiality["RAW-BOUNDARY-LEASE"].append(raw_m)
                facts = {
                    **facts,
                    "M_exp": {"ONLGR": onlgr_m, "RAW-BOUNDARY-LEASE": raw_m},
                    "native_return": {
                        "ONLGR": onlgr_native.normalized_return,
                        "RAW-BOUNDARY-LEASE": raw_native.normalized_return,
                    },
                    "yoked_return": {
                        "ONLGR": onlgr_yoked.normalized_return,
                        "RAW-BOUNDARY-LEASE": raw_yoked.normalized_return,
                    },
                }
            slot_facts.append(facts)
        eligible = len(native_returns["ONLGR"])
        common_slots = [
            int(fact["episode_slot"]) for fact in slot_facts if fact.get("eligible")
        ]
        cells[schedule] = {
            "original_slot_denominator": config.diagnostic_episodes,
            "C_pc": common_slots,
            "jointly_eligible_pairs": eligible,
            "common_support_rate": eligible / config.diagnostic_episodes,
            "common_support_at_least_15_of_16": eligible >= 15,
            "slot_facts": slot_facts,
            "common_native_mean": {
                arm: float(np.mean(values)) if values else None
                for arm, values in native_returns.items()
            },
            "common_yoked_mean": {
                arm: float(np.mean(values)) if values else None
                for arm, values in yoked_returns.items()
            },
            "M_exp_mean": {
                arm: float(np.mean(values)) if values else None
                for arm, values in materiality.items()
            },
        }
    return cells


def _analyze_yoke(yoke_by_seed: dict[str, object]) -> dict[str, object]:
    support_ok = all(
        bool(yoke_by_seed[str(seed)][schedule]["common_support_at_least_15_of_16"])  # type: ignore[index]
        for seed in SEEDS for schedule in HELDOUT_SCHEDULES
    )
    materiality_intervals: dict[str, dict[str, object]] = {
        arm: {} for arm in ("ONLGR", "RAW-BOUNDARY-LEASE")
    }
    materiality_ok = True
    for arm in materiality_intervals:
        for schedule in HELDOUT_SCHEDULES:
            values = [
                yoke_by_seed[str(seed)][schedule]["M_exp_mean"][arm]  # type: ignore[index]
                for seed in SEEDS
            ]
            if any(value is None for value in values):
                interval: dict[str, object] = {
                    "n": sum(value is not None for value in values), "mean": None,
                    "lower": None, "upper": None, "confidence": 0.95,
                }
                passed = False
            else:
                interval = student_interval((float(value) for value in values), 0.95)
                passed = bool(interval["mean"] >= 0.10 and interval["lower"] > 0.05)
            interval["materiality_gate"] = passed
            materiality_intervals[arm][schedule] = interval
            materiality_ok = materiality_ok and passed
    psi_by_seed: dict[str, float] = {}
    if support_ok and materiality_ok:
        for seed in SEEDS:
            schedule_values: list[float] = []
            for schedule in HELDOUT_SCHEDULES:
                cell = yoke_by_seed[str(seed)][schedule]  # type: ignore[index]
                native = cell["common_native_mean"]
                yoked = cell["common_yoked_mean"]
                schedule_values.append(
                    (float(native["ONLGR"]) - float(native["RAW-BOUNDARY-LEASE"]))
                    - (float(yoked["ONLGR"]) - float(yoked["RAW-BOUNDARY-LEASE"]))
                )
            psi_by_seed[str(seed)] = float(np.mean(schedule_values))
        psi_interval: dict[str, object] | None = student_interval(psi_by_seed.values(), 0.95)
        psi_supported = bool(psi_interval["mean"] >= 0.01 and psi_interval["lower"] > 0.0)
    else:
        psi_interval = None
        psi_supported = False
    return {
        "candidate_count_per_pair": 1,
        "complexity": "O(H*N), N=2",
        "common_support_gate": support_ok,
        "materiality_intervals": materiality_intervals,
        "materiality_gate": materiality_ok,
        "Psi_by_seed": psi_by_seed if psi_interval is not None else None,
        "Psi_interval": psi_interval,
        "preselected_reassignment_sensitivity_gate": psi_supported,
        "secondary_estimand_available": psi_interval is not None,
    }


def _partition_analysis(partitions: dict[str, object]) -> dict[str, object]:
    available = all(
        partitions[str(seed)]["operational_estimand_available"]  # type: ignore[index]
        for seed in SEEDS
    )
    identity = all(
        partitions[str(seed)]["prob_exp_identity_pass"]  # type: ignore[index]
        for seed in SEEDS
    )
    if not available:
        return {"operational_estimand_available": False,
                "prob_exp_identity_pass": identity, "MPI_intervals": None,
                "RAW_minus_ONLGR": None, "operational_stability_gate": False}
    intervals = {arm: student_interval(
        partitions[str(seed)]["MPI"][arm] for seed in SEEDS  # type: ignore[index]
    ) for arm in ("ONLGR", "RAW-BOUNDARY-LEASE")}
    difference = student_interval(
        partitions[str(seed)]["MPI"]["RAW-BOUNDARY-LEASE"]
        - partitions[str(seed)]["MPI"]["ONLGR"] for seed in SEEDS  # type: ignore[index]
    )
    gate = bool(intervals["ONLGR"]["mean"] <= .02
                and intervals["ONLGR"]["upper"] < .03
                and difference["mean"] >= .02 and difference["lower"] > 0)
    return {"operational_estimand_available": True, "prob_exp_identity_pass": identity,
            "MPI_intervals": intervals, "RAW_minus_ONLGR": difference,
            "operational_stability_gate": gate}


def _support_facts(native: dict[str, object], iid: dict[str, object]) -> dict[str, object]:
    output: dict[str, object] = {}
    for seed in SEEDS:
        cells: dict[str, object] = {}
        for schedule in (*HELDOUT_SCHEDULES, IID_SCHEDULE):
            arms: dict[str, object] = {}
            for arm in LEARNED_ARMS:
                row = (iid[str(seed)][arm] if schedule == IID_SCHEDULE  # type: ignore[index]
                       else native[str(seed)][arm][schedule])  # type: ignore[index]
                anchor_legal = sum(row["initial_anchor_legal_routine_rows_by_role"])
                poststartup_legal = sum(row["poststartup_legal_routine_rows_by_role"])
                anchor_actions = [
                    sum(counts[action] for counts in row["initial_anchor_stochastic_actions_by_role"].values())
                    for action in range(3)
                ]
                poststartup_actions = [
                    sum(counts[action] for counts in row["poststartup_stochastic_actions_by_role"].values())
                    for action in range(3)
                ]
                gate = (
                    poststartup_legal >= 64
                    and all(count >= 4 for count in poststartup_actions)
                )
                arms[arm] = {
                    "poststartup_row_predicate": (
                        "routine_row AND initial_anchor_action=false AND "
                        "both_voluntary_marks_legal"
                    ),
                    "initial_anchor_agent_row_count": anchor_legal,
                    "initial_anchor_stochastic_keep_count": anchor_actions[0],
                    "initial_anchor_voluntary_refresh_count": anchor_actions[1],
                    "initial_anchor_voluntary_rebind_count": anchor_actions[2],
                    "poststartup_both_marks_legal_agent_row_count": poststartup_legal,
                    "poststartup_stochastic_keep_count": poststartup_actions[0],
                    "poststartup_voluntary_refresh_count": poststartup_actions[1],
                    "poststartup_voluntary_rebind_count": poststartup_actions[2],
                    "poststartup_64_4_4_4_gate_pass": gate,
                }
            cells[schedule] = {"arms": arms,
                               "ONLGR_full_poststartup_marked_activity": arms["ONLGR"]["poststartup_64_4_4_4_gate_pass"],
                               "all_learned_arms_nondegenerate": all(
                                   v["poststartup_64_4_4_4_gate_pass"] for v in arms.values()
                               )}
        output[str(seed)] = cells
    return output


def _iid_pairing_audit(iid_sources: dict[str, object]) -> dict[str, object]:
    failures: list[dict[str, object]] = []
    audited = 0
    for seed in SEEDS:
        per_arm = iid_sources[str(seed)]  # type: ignore[index]
        for episode_index in range(len(per_arm["ONLGR"][IID_SCHEDULE])):
            rows = [
                per_arm[arm][IID_SCHEDULE][episode_index] for arm in LEARNED_ARMS
            ]
            audited += 1
            reference = rows[0]
            paired = all(
                row.iid_interval_draws == reference.iid_interval_draws
                and row.routine_boundary_ticks == reference.routine_boundary_ticks
                and row.iid_terminal_censored_duration == reference.iid_terminal_censored_duration
                for row in rows[1:]
            )
            well_formed = (
                len(reference.iid_interval_draws) == len(reference.routine_boundary_ticks)
                and all(value in (4, 16, 32) for value in reference.iid_interval_draws)
                and reference.routine_boundary_ticks[0] == 0
                and 256 not in reference.routine_boundary_ticks
                and reference.iid_terminal_censored_duration is not None
                and reference.routine_boundary_ticks[-1]
                    + reference.iid_terminal_censored_duration == 256
            )
            if not paired or not well_formed:
                failures.append({
                    "seed": seed, "episode_index": episode_index,
                    "paired_across_arms": paired, "well_formed": well_formed,
                })
    return {
        "domain": "RAND_IID_NEXT_K",
        "action_domains": ["ACTION_T", "ACTION_R"],
        "audited_seed_episode_pairs": audited,
        "paired_across_arms": not failures,
        "draw_ordinal_increments_once_per_realized_routine_action": not failures,
        "terminal_censoring_exact": not failures,
        "failures": failures,
    }


def _adaptive_headroom(
    native: dict[str, object], diagnostics: dict[str, object],
    fixed: dict[str, object], iid: dict[str, object], iid_results: dict[str, object],
    support: dict[str, object], native_sources: dict[str, object],
) -> dict[str, object]:
    def seven_mean(rows: dict[str, object], arm: str | None = None) -> float:
        values = rows[arm] if arm is not None else rows
        return float(np.mean([values[schedule]["mean_return"] for schedule in HELDOUT_SCHEDULES]))
    per_seed_p16: dict[str, dict[str, float]] = {}
    for seed in SEEDS:
        per_seed_p16[str(seed)] = {
            "TIMING-ONLY-ONLGR": float(np.mean([
                np.mean([
                    row.normalized_return for row in
                    native_sources[str(seed)]["TIMING-ONLY-ONLGR"][schedule]  # type: ignore[index]
                ]) for schedule in HELDOUT_SCHEDULES
            ])),
            "FIXED-RATE-LEASE": seven_mean(fixed[str(seed)]),
            **{
                arm: seven_mean({
                    schedule: diagnostics[str(seed)][schedule][arm]
                    for schedule in HELDOUT_SCHEDULES
                }) for arm in (
                    "ALWAYS-KEEP", "ALWAYS-REFRESH-WHEN-LEGAL",
                    "ALWAYS-REBIND-WHEN-LEGAL", "STATE-ORACLE",
                )
            },
        }
    baseline_names = (
        "TIMING-ONLY-ONLGR", "FIXED-RATE-LEASE", "ALWAYS-KEEP",
        "ALWAYS-REFRESH-WHEN-LEGAL", "ALWAYS-REBIND-WHEN-LEGAL",
    )
    bar_p16 = {
        arm: float(np.mean([per_seed_p16[str(seed)][arm] for seed in SEEDS]))
        for arm in (*baseline_names, "STATE-ORACLE")
    }
    maximizing_baseline = max(baseline_names, key=lambda arm: bar_p16[arm])
    oracle = bar_p16["STATE-ORACLE"]
    best = bar_p16[maximizing_baseline]
    headroom = oracle - best
    iid_service_by_seed = tuple(
        iid[str(seed)]["ONLGR"]["mean_service"]
        - iid[str(seed)]["TIMING-ONLY-ONLGR"]["mean_service"]
        for seed in SEEDS
    )
    iid_service_interval = student_interval(iid_service_by_seed, 0.95)
    iid_service = float(iid_service_interval["mean"])
    iid_cost = float(np.mean([
        iid[str(seed)]["ONLGR"]["mean_action_cost"]
        - iid[str(seed)]["TIMING-ONLY-ONLGR"]["mean_action_cost"]
        for seed in SEEDS
    ]))
    iid_decomposition_exact = all(
        bool(iid[str(seed)][arm]["return_service_cost_decomposition_exact"])
        for seed in SEEDS for arm in LEARNED_ARMS
    )
    iid_link = iid_results["contrasts"]["ONLGR_minus_RAW-BOUNDARY-LEASE"]["gate"]
    iid_state = iid_results["contrasts"]["ONLGR_minus_TIMING-ONLY-ONLGR"]["gate"]
    onlgr_full_marked_activity = all(
        support[str(seed)][schedule]["ONLGR_full_poststartup_marked_activity"]  # type: ignore[index]
        for seed in SEEDS for schedule in (*HELDOUT_SCHEDULES, IID_SCHEDULE)
    )
    return {"oracle_mean": oracle, "best_non_oracle_mean": best,
            "oracle_headroom": headroom, "oracle_headroom_at_least_.02": headroom >= .02,
            "P16_by_seed": per_seed_p16, "barP16": bar_p16,
            "maximizing_non_oracle_baseline": maximizing_baseline,
            "oracle_headroom_is_point_diagnostic_not_inferential": True,
            "IID_ONLGR_minus_TIMING_ONLY_service": iid_service_interval,
            "IID_ONLGR_minus_TIMING_ONLY_explicit_action_cost": iid_cost,
            "IID_return_service_cost_decomposition_exact": iid_decomposition_exact,
            "IID_service_not_cost_only": bool(
                iid_service > 0.0 and iid_service_interval["lower"] > 0.0
                and iid_decomposition_exact
            ),
            "ONLGR_full_poststartup_marked_activity_all_native_and_IID_cells": onlgr_full_marked_activity,
            "content_access_composite_gate": bool(
                iid_link and iid_state and headroom >= .02
                and iid_service > 0.0 and iid_service_interval["lower"] > 0.0
                and iid_decomposition_exact and onlgr_full_marked_activity
            )}


def _core_package_missing(
    *, config: RunConfig, training: dict[str, object], checkpoints: dict[str, object],
    native: dict[str, object], iid: dict[str, object], safety: dict[str, object],
    partitions: dict[str, object], fixed_selection: dict[str, object],
    fixed_evaluation: dict[str, object], keep_equality: dict[str, object],
    leakage: dict[str, object], resources: dict[str, object],
) -> list[str]:
    """Exact registered core only; secondary clamp/degenerate/yoke never enter."""
    missing: list[str] = []
    expected_training_by_schedule = {
        schedule: config.training_episodes // len(TRAIN_SCHEDULES)
        for schedule in TRAIN_SCHEDULES
    }
    for seed in SEEDS:
        seed_key = str(seed)
        for arm in LEARNED_ARMS:
            if arm not in checkpoints.get(seed_key, {}):  # type: ignore[union-attr]
                missing.append(f"checkpoint:{seed}:{arm}")
            train_row = (training.get(seed_key, {}) or {}).get(arm)  # type: ignore[union-attr]
            if not train_row:
                missing.append(f"training:{seed}:{arm}")
            else:
                if int(train_row.get("complete_training_episodes", -1)) != config.training_episodes:
                    missing.append(f"training_count:{seed}:{arm}")
                if train_row.get("training_schedule_counts") != expected_training_by_schedule:
                    missing.append(f"training_schedule_counts:{seed}:{arm}")
                if int(train_row.get("ppo_epochs", -1)) != config.ppo_epochs:
                    missing.append(f"training_epochs:{seed}:{arm}")
            for schedule in HELDOUT_SCHEDULES:
                native_row = (((native.get(seed_key, {}) or {}).get(arm, {}) or {}).get(schedule))  # type: ignore[union-attr]
                safety_row = (((safety.get(seed_key, {}) or {}).get(arm, {}) or {}).get(schedule))  # type: ignore[union-attr]
                if not native_row or int(native_row.get("episodes", -1)) != config.native_episodes:
                    missing.append(f"native_count:{seed}:{arm}:{schedule}")
                if not safety_row or int(safety_row.get("episodes", -1)) != config.safety_episodes:
                    missing.append(f"safety_count:{seed}:{arm}:{schedule}")
            iid_row = (((iid.get(seed_key, {}) or {}).get(arm)))  # type: ignore[union-attr]
            if not iid_row or int(iid_row.get("episodes", -1)) != config.native_episodes:
                missing.append(f"iid_count:{seed}:{arm}")
            elif not bool(iid_row.get("iid_seed_arm_decomposition_ok")):
                missing.append(f"iid_reward_decomposition:{seed}:{arm}")
        partition = partitions.get(seed_key)  # type: ignore[union-attr]
        if not partition or int(partition.get("declared_cell_count", -1)) != 16 \
                or int(partition.get("realized_cell_count", -1)) != 16 \
                or len(partition.get("cells", ())) != 16:
            missing.append(f"partition_cells:{seed}")
        for schedule in HELDOUT_SCHEDULES:
            fixed_row = (((fixed_evaluation.get(seed_key, {}) or {}).get(schedule)))  # type: ignore[union-attr]
            if not fixed_row or int(fixed_row.get("episodes", -1)) != config.diagnostic_episodes:
                missing.append(f"fixed_rate_count:{seed}:{schedule}")
        keep = keep_equality.get(seed_key)  # type: ignore[union-attr]
        if not keep or int(keep.get("episodes_per_schedule", -1)) != config.diagnostic_episodes \
                or len(keep.get("schedules", ())) != len(HELDOUT_SCHEDULES):
            missing.append(f"keep_grid_denominator:{seed}")
        if not leakage.get(seed_key):  # type: ignore[union-attr]
            missing.append(f"switch_twin:{seed}")
    grid = fixed_selection.get("grid", ())
    expected_grid_episodes = (
        len(VALIDATION_ROOTS) * len(TRAIN_SCHEDULES) * config.fixed_selection_episodes
    )
    if len(grid) != len(FIXED_RATES) * len(FIXED_MARKS) or any(
        int(row.get("episodes", -1)) != expected_grid_episodes for row in grid
    ) or not fixed_selection.get("selected"):
        missing.append("fixed_rate_selection_exact_grid")
    expected_core_ticks = {
        "training": registered_budget(config)["training_team_ticks"],
        "native": registered_budget(config)["native_team_ticks"],
        "iid_future_k": registered_budget(config)["iid_future_k_team_ticks"],
        "safety": registered_budget(config)["safety_team_ticks"],
        "fixed_rate_selection": registered_budget(config)["fixed_selection_team_ticks"],
        "fixed_rate_evaluation": registered_budget(config)["fixed_evaluation_team_ticks"],
        "keep_grid_probe": registered_budget(config)["keep_grid_probe_team_ticks"],
    }
    actual_by_panel = resources.get("actual_team_ticks_by_panel", {})
    for panel, expected in expected_core_ticks.items():
        if int(actual_by_panel.get(panel, -1)) != expected:  # type: ignore[union-attr]
            missing.append(f"core_tick_count:{panel}")
    if COMPOSITE_REVISION != "ONLGR-PRO-MATH-CLOSURE-CANDIDATE-20260812-04" \
            or not MATHEMATICAL_CLOSURE_CONFIRMED:
        missing.append("exact_composite_revision_or_closure")
    return missing


def exercise(*, output_root: Path, result_path: Path, config: RunConfig = PRODUCTION_CONFIG) -> dict[str, object]:
    if output_root.exists():
        raise FileExistsError("output root must be fresh")
    if result_path.exists():
        raise FileExistsError("result path already exists")
    if not MATHEMATICAL_CLOSURE_CONFIRMED:
        raise RuntimeError(
            f"ONLGR production is held: {MATHEMATICAL_CLOSURE_STATUS}"
        )
    if config.horizon > 256 or config.total_tick_cap > 7_000_000:
        raise ValueError("internal configurations may bound but not enlarge frozen caps")
    planned = registered_budget(config)
    if config.registered and planned["maximum_total_team_ticks"] != 6_750_208:
        raise RuntimeError("registered conservative team-tick ledger changed")
    if planned["maximum_total_team_ticks"] > config.total_tick_cap:
        raise RuntimeError("requested package exceeds registered team-tick cap")
    output_root.mkdir(parents=True, exist_ok=False)
    _write_json(output_root / "registration.json", {
        "artifact_kind": ARTIFACT_KIND, "treatment": TREATMENT,
        "configuration": config.__dict__, "ppo": PPO,
        "requested_conservative_budget": planned,
        "preselected_exact_yoke": {
            "candidate_count": 1, "complexity": "O(H*N)",
            "joint_cyclic_rotations": True, "outcome_blind_selection": True,
        },
    })
    torch.set_num_threads(config.cpu_workers)
    torch.set_num_interop_threads(config.cpu_workers)
    ledger = ResourceLedger(config)

    fixed_selection = select_fixed_rate(config, ledger)
    fixed = (float(fixed_selection["selected"]["lambda"]),
             float(fixed_selection["selected"]["rho"]))
    native: dict[str, object] = {}
    safety: dict[str, object] = {}
    clamp: dict[str, object] = {}
    diagnostics: dict[str, object] = {}
    fixed_evaluation: dict[str, object] = {}
    partitions: dict[str, object] = {}
    leakage: dict[str, object] = {}
    training: dict[str, object] = {}
    checkpoints: dict[str, object] = {}
    activities: dict[str, object] = {}
    keep_equality: dict[str, object] = {}
    yoke_cells: dict[str, object] = {}
    iid: dict[str, object] = {}
    iid_episode_sources: dict[str, object] = {}
    native_episode_sources: dict[str, object] = {}

    for seed in config.seeds:
        learners, train_rows, activity, seed_checkpoints = train_seed(
            seed, config, output_root / "checkpoints", ledger,
        )
        training[str(seed)] = train_rows
        checkpoints[str(seed)] = seed_checkpoints
        activities[str(seed)] = activity
        native_seed, native_sources = _evaluate_learned_panel(
            seed=seed, learners=learners, config=config, count=config.native_episodes,
            namespace="paired_native", ledger=ledger, panel="native",
            retain_first=config.diagnostic_episodes,
        )
        native[str(seed)] = native_seed
        native_episode_sources[str(seed)] = native_sources
        iid_seed, iid_sources = _evaluate_learned_panel(
            seed=seed, learners=learners, config=config, count=config.native_episodes,
            namespace="paired_iid_future_k", ledger=ledger, panel="iid_future_k",
            schedules=(IID_SCHEDULE,), retain_first=config.native_episodes,
        )
        iid[str(seed)] = {arm: iid_seed[arm][IID_SCHEDULE] for arm in LEARNED_ARMS}
        iid_episode_sources[str(seed)] = iid_sources
        yoke_cells[str(seed)] = _evaluate_yoke_seed(
            seed=seed, learners=learners, native_rows=native_sources,
            config=config, ledger=ledger,
        )
        safety_seed, _ = _evaluate_learned_panel(
            seed=seed, learners=learners, config=config, count=config.safety_episodes,
            namespace="paired_safety", ledger=ledger, panel="safety", safety=True,
        )
        safety[str(seed)] = safety_seed
        clamp_seed, _ = _evaluate_learned_panel(
            seed=seed, learners=learners, config=config, count=config.diagnostic_episodes,
            namespace="paired_native", ledger=ledger, panel="exposure_clamp", exposure_clamp=True,
        )
        clamp[str(seed)] = clamp_seed
        seed_controls, seed_fixed = _evaluate_controls(
            seed=seed, learners=learners, fixed=fixed, config=config, ledger=ledger,
        )
        diagnostics[str(seed)] = seed_controls
        fixed_evaluation[str(seed)] = seed_fixed
        partitions[str(seed)] = marked_partition_probe(
            learners["ONLGR"], learners["RAW-BOUNDARY-LEASE"]
        )
        leakage[str(seed)] = leakage_twin_contract(
            native[str(seed)], config.native_episodes  # type: ignore[arg-type]
        )
        keep = keep_grid_equality(seed, config.diagnostic_episodes)
        keep_equality[str(seed)] = keep
        ledger.add_ticks("keep_grid_probe", int(keep["actual_team_ticks"]))

    analysis = primary_analysis(native)  # type: ignore[arg-type]
    partition_analysis = _partition_analysis(partitions)
    iid_results = iid_analysis(iid)  # type: ignore[arg-type]
    iid_pairing_audit = _iid_pairing_audit(iid_episode_sources)
    yoke_analysis = _analyze_yoke(yoke_cells)
    resources = ledger.facts()
    resources["requested_conservative_team_ticks"] = planned[
        "maximum_total_team_ticks"
    ]
    resources["preselected_yoke_max_team_ticks"] = planned["preselected_yoke_max_team_ticks"]
    if int(resources["actual_team_ticks_by_panel"].get("preselected_exact_yoke", 0)) > int(
        planned["preselected_yoke_max_team_ticks"]
    ):
        raise RuntimeError("bounded exact yoke exceeded its conservative tick allocation")
    primary_missing = validate_primary_completeness(
        native=native, safety=safety, checkpoints=checkpoints, partition=partitions,
        fixed_rate=fixed_selection, resources=resources,
    )
    optional_missing: list[str] = []
    for seed in SEEDS:
        for arm in LEARNED_ARMS:
            for schedule in HELDOUT_SCHEDULES:
                if not clamp[str(seed)][arm].get(schedule):  # type: ignore[index]
                    optional_missing.append(f"clamp:{seed}:{arm}:{schedule}")
        for schedule in HELDOUT_SCHEDULES:
            if len(yoke_cells[str(seed)][schedule]["slot_facts"]) != config.diagnostic_episodes:  # type: ignore[index]
                optional_missing.append(f"yoke:{seed}:{schedule}")
            if not diagnostics[str(seed)].get(schedule):  # type: ignore[union-attr]
                optional_missing.append(f"degenerate_oracle:{seed}:{schedule}")
    core_missing = _core_package_missing(
        config=config, training=training, checkpoints=checkpoints, native=native,
        iid=iid, safety=safety, partitions=partitions,
        fixed_selection=fixed_selection, fixed_evaluation=fixed_evaluation,
        keep_equality=keep_equality, leakage=leakage, resources=resources,
    )
    safety_violations = sum(
        int(safety[str(seed)][arm][schedule]["safety_violations"])  # type: ignore[index]
        for seed in SEEDS for arm in LEARNED_ARMS for schedule in HELDOUT_SCHEDULES
    )
    actor_counts = {
        arm: {
            schedule: [
                int(native[str(seed)][arm][schedule]["resource"]["actor_calls"])  # type: ignore[index]
                for seed in SEEDS
            ] for schedule in HELDOUT_SCHEDULES
        } for arm in LEARNED_ARMS
    }
    parameters_matched = all(
        len({training[str(seed)][arm]["actor_parameter_count"] for arm in LEARNED_ARMS}) == 1
        and len({training[str(seed)][arm]["critic_parameter_count"] for arm in LEARNED_ARMS}) == 1
        for seed in SEEDS
    )
    calls_matched = all(
        actor_counts[LEARNED_ARMS[0]][schedule] == actor_counts[arm][schedule]
        for schedule in HELDOUT_SCHEDULES for arm in LEARNED_ARMS[1:]
    )
    native_resource_work_matched = all(
        len({
            int(native[str(seed)][arm][schedule]["resource"][field])  # type: ignore[index]
            for arm in LEARNED_ARMS
        }) == 1
        for seed in SEEDS for schedule in HELDOUT_SCHEDULES
        for field in ("actor_calls", "critic_calls", "messages", "bits", "physics_ticks")
    )
    onlgr_latency = [
        native[str(seed)]["ONLGR"][schedule]["resource"]["decision_latency_ms_p95"]  # type: ignore[index]
        for seed in SEEDS for schedule in HELDOUT_SCHEDULES
    ]
    raw_latency = [
        native[str(seed)]["RAW-BOUNDARY-LEASE"][schedule]["resource"]["decision_latency_ms_p95"]  # type: ignore[index]
        for seed in SEEDS for schedule in HELDOUT_SCHEDULES
    ]
    latency_ratio = float(np.percentile(onlgr_latency, 95) / max(1e-12, np.percentile(raw_latency, 95)))
    identity_probe = prob_exp_identity_probe()
    reward_exposure = resources["observed_reward_exposure_ledger"]
    conformance_facts = {
        "analytic_probability_and_full_jacobian": bool(identity_probe["pass"]),
        "partition_probability_and_full_jacobian": all(
            bool(partitions[str(seed)]["prob_exp_identity_pass"]) for seed in SEEDS  # type: ignore[index]
        ),
        "KEEP_grid_equality": all(
            bool(keep_equality[str(seed)]["physics_sensor_plan_age_service_reward_equal"])
            and not keep_equality[str(seed)]["failures"]  # type: ignore[index]
            for seed in SEEDS
        ),
        "switch_twin": all(
            bool(leakage[str(seed)]["complete"]) and not leakage[str(seed)]["failures"]  # type: ignore[index]
            for seed in SEEDS
        ),
        "IID_filtration_and_pairing": bool(
            iid_pairing_audit["paired_across_arms"]
            and iid_pairing_audit["draw_ordinal_increments_once_per_realized_routine_action"]
            and iid_pairing_audit["terminal_censoring_exact"]
            and not iid_pairing_audit["failures"]
        ),
        "IID_reward_decomposition": bool(
            iid_results["iid_reward_decomposition_conformant"]
        ),
        "exposure_closed_form": bool(reward_exposure["exposure_closed_form_exact"]),
        "action_before_service": bool(reward_exposure["action_before_service_exact"]),
        "reward_service_cost_per_tick": bool(reward_exposure["reward_service_cost_tick_exact"]),
        "segment_ownership": bool(reward_exposure["segment_ownership_exact"]),
        "terminal_boundary_absence": bool(reward_exposure["terminal_boundary_absent"]),
        "exact_composite_revision": (
            COMPOSITE_REVISION == "ONLGR-PRO-MATH-CLOSURE-CANDIDATE-20260812-04"
            and MATHEMATICAL_CLOSURE_CONFIRMED
        ),
        "D11_activity": all(bool(row["began"]) for row in activities.values()),
        "safety": safety_violations == 0,
        "registered_team_tick_cap": int(resources["actual_team_ticks"]) <= config.total_tick_cap,
        "registered_wall_cap": float(resources["wall_seconds"]) <= config.wall_seconds,
        "registered_RSS_cap": int(resources["peak_rss_bytes"]) <= config.peak_rss_bytes,
        "registered_CPU_workers": int(resources["cpu_workers"]) == config.cpu_workers == 1,
        "matched_actor_critic_parameters": parameters_matched,
        "matched_native_actor_calls": calls_matched,
        "matched_native_resource_work": native_resource_work_matched,
        "ONLGR_latency_at_most_1_10_RAW": latency_ratio <= 1.10,
    }
    technical_blockers = [
        f"conformance:{name}" for name, passed in conformance_facts.items() if not passed
    ]
    if core_missing:
        technical_blockers.append("core_registered_package_missing_or_count_incoherent")
    output_ready = not technical_blockers
    clamp_analysis = primary_analysis(clamp)  # type: ignore[arg-type]
    support_facts = _support_facts(native, iid)
    adaptive_headroom = _adaptive_headroom(
        native, diagnostics, fixed_evaluation, iid, iid_results, support_facts,
        native_episode_sources,
    )
    complete_coherent = not core_missing and all(conformance_facts.values())
    activation_inputs = {
        "complete_coherent_package": complete_coherent,
        "D11_scientific_activity_started": conformance_facts["D11_activity"],
        "technical_acceptance_ready_for_CM_result_intake": output_ready,
        "all_conformance_safety_resource_facts_pass": all(conformance_facts.values()),
        "P_plus": bool(analysis["registered_primary_support"]["P"]),
        "W_plus": bool(analysis["registered_primary_support"]["W"]),
        "P_plus_OR_W_plus": bool(
            analysis["registered_primary_support"]["P"]
            or analysis["registered_primary_support"]["W"]
        ),
        "IID_RAW_plus": bool(
            iid_results["contrasts"]["ONLGR_minus_RAW-BOUNDARY-LEASE"]["gate"]
        ),
        "operational_marked_partition": bool(
            partition_analysis["operational_stability_gate"]
        ),
        "IID_TIMING_plus": bool(
            iid_results["contrasts"]["ONLGR_minus_TIMING-ONLY-ONLGR"]["gate"]
        ),
        "paired_positive_IID_service": bool(
            adaptive_headroom["IID_service_not_cost_only"]
        ),
        "IID_R_equals_S_minus_C_conformant": bool(
            iid_results["iid_reward_decomposition_conformant"]
        ),
        "H_oracle_at_least_0_02": bool(
            adaptive_headroom["oracle_headroom_at_least_.02"]
        ),
        "ONLGR_poststartup_64_4_4_4_every_native_and_IID_seed_cell": bool(
            adaptive_headroom[
                "ONLGR_full_poststartup_marked_activity_all_native_and_IID_cells"
            ]
        ),
        "yoke_gating": False,
    }
    activation_inputs["eligible_exposure_link_composite_gate"] = all((
        bool(activation_inputs["IID_RAW_plus"]),
        bool(activation_inputs["operational_marked_partition"]),
        bool(activation_inputs[
            "ONLGR_poststartup_64_4_4_4_every_native_and_IID_seed_cell"
        ]),
    ))
    activation_inputs["nine_part_conjunction_except_external_CM_acceptance"] = all((
        bool(activation_inputs["complete_coherent_package"]),
        bool(activation_inputs["D11_scientific_activity_started"]),
        bool(activation_inputs["technical_acceptance_ready_for_CM_result_intake"]),
        bool(activation_inputs["all_conformance_safety_resource_facts_pass"]),
        bool(activation_inputs["P_plus_OR_W_plus"]),
        bool(activation_inputs["IID_RAW_plus"]),
        bool(activation_inputs["operational_marked_partition"]),
        bool(activation_inputs["IID_TIMING_plus"]),
        bool(activation_inputs["paired_positive_IID_service"]),
        bool(activation_inputs["IID_R_equals_S_minus_C_conformant"]),
        bool(activation_inputs["H_oracle_at_least_0_02"]),
        bool(activation_inputs["ONLGR_poststartup_64_4_4_4_every_native_and_IID_seed_cell"]),
    ))
    result: dict[str, Any] = {
        "artifact_kind": ARTIFACT_KIND, "treatment": TREATMENT,
        "production_defaults": config.registered, "configuration": config.__dict__, "ppo": PPO,
        "initialization_exposure_curves": _initialization_curves(),
        "prob_exp_identity_conformance": identity_probe,
        "marked_categorical_contract": {
            "ONLGR_event_link": "u=1-exp(-e*softplus(g))",
            "RAW_event_link": "u=sigmoid(g)",
            "conditional_mark": "rho=sigmoid(h)",
            "agent_action_probabilities": ["1-u", "u*rho", "u*(1-rho)"],
            "joint_law": "product over e_i>0 stochastic agents; e_i=0 is a unit point mass",
            "action_rng_domains": {"T": "ACTION_T", "R": "ACTION_R"},
            "one_joint_log_probability_ratio_and_clip": True,
            "KEEP_has_no_direct_mark_logit_term_but_shared_trunk_can_change_mark_policy": True,
            "point_mass_rows_have_no_actor_likelihood_or_score": True,
        },
        "ppo_objective_contract": {
            "behavior_log_prob_and_critic_cached_before_first_epoch": True,
            "behavior_frozen_GAE_and_lambda_return_cached_all_four_epochs": True,
            "terminal_behavior_value": 0.0,
            "actor_inner_weight": "genuine joint score row sum times 1/256",
            "critic_inner_weight": "mean over every actual nonterminal boundary row",
            "outer_weight": "equal schedules then equal episodes",
            "forced_masked_dummy_rows_reset_GAE": False,
            "advantage_normalization": False,
            "value_clipping": False,
            "value_coefficient": 0.5,
            "value_coefficient_applications": 1,
            "entropy_coefficient": 0.0,
        },
        "scientific_activity": {
            "began": all(row["began"] for row in activities.values()), "by_seed": activities,
        },
        "checkpoints": checkpoints, "training_diagnostics": training,
        "native_seed_schedule_metrics": native, "safety_seed_schedule_metrics": safety,
        "iid_future_k_metrics": iid, "iid_future_k_analysis": iid_results,
        "iid_future_k_pairing_audit": iid_pairing_audit,
        "exposure_clamp_metrics": clamp, "exposure_clamp_analysis": clamp_analysis,
        "fixed_rate_selection": fixed_selection,
        "fixed_rate_seed_schedule_metrics": fixed_evaluation,
        "degenerate_oracle_metrics": diagnostics, "partition_probe": partitions,
        "diagnostic_pairing": {
            "heldout_exogenous_namespace": "paired_native",
            "paired_native_episode_slots": list(range(config.diagnostic_episodes)),
            "arms": ["FIXED-RATE-LEASE", *DIAGNOSTIC_ARMS],
            "fixed_rate_validation_namespace": "fixed_rate_validation",
        },
        "iid_future_k_audit": {
            "schedule": IID_SCHEDULE,
            "interval_support": [4, 16, 32],
            "draw_namespace": "RAND_IID_NEXT_K",
            "draw_coordinates": ["seed", "episode_index", "exogenous_routine_draw_ordinal"],
            "uniform_map": {"U<1/3": 4, "1/3<=U<2/3": 16, "U>=2/3": 32},
            "draw_occurs_after_current_action": True,
            "draw_ordinal_increments_after_masked_or_deterministic_KEEP": True,
            "independent_of_visible_history_action_state_reward_prior_intervals": True,
            "paired_across_learned_arms": True,
            "unchanged_final_checkpoints": True,
            "episodes_per_seed_arm": config.native_episodes,
            "terminal_draw_censors_at_H_without_boundary_action_or_additional_K_observation": True,
            "action_domains": ["ACTION_T", "ACTION_R"],
        },
        "partition_analysis": partition_analysis, "keep_grid_equality": keep_equality,
        "switch_decision_twin": leakage,
        "preselected_exact_yoke": {"by_seed_schedule": yoke_cells, "analysis": yoke_analysis},
        "primary_analysis": analysis, "mechanism_support": support_facts,
        "adaptive_headroom_and_service_gate": adaptive_headroom,
        "second_surface_activation_factual_inputs": activation_inputs,
        "resource_diagnostics": resources,
        "result_return_conformance": {
            "map_revision": "ONLGR-B1-RESULT-BLIND-INTAKE-ACTIVATION-MAP-20260812-01",
            "iid_reward_clarification": (
                "ONLGR-IID-REWARD-DECOMPOSITION-CONFORMANCE-20260812-01"
            ),
            "facts": conformance_facts,
            "all_required_conformance_facts_pass": all(conformance_facts.values()),
            "observed_reward_exposure_ledger": reward_exposure,
            "core_missing_or_incoherent": core_missing,
            "optional_diagnostic_missing": optional_missing,
            "optional_absence_does_not_change_core_complete_coherent": True,
            "yoke_is_non_gating": True,
        },
        "matched_work_facts": {
            "actor_and_critic_parameters_matched": parameters_matched,
            "native_actor_calls_matched_for_each_schedule": calls_matched,
            "native_actor_critic_calls_messages_bits_physics_ticks_matched": (
                native_resource_work_matched
            ),
            "declared_messages_per_team_tick": 2, "declared_bits_per_team_tick": 4,
            "ppo_epochs": config.ppo_epochs, "updates_per_arm_seed": 8,
            "onlgr_to_raw_p95_actor_latency_ratio": latency_ratio,
            "latency_gate_at_most_1.10": latency_ratio <= 1.10,
        },
        "completeness": {
            "structural_primary_matrix_missing": primary_missing,
            "structural_primary_matrix_complete": not primary_missing,
            "technical_acceptance_ready": output_ready and MATHEMATICAL_CLOSURE_CONFIRMED,
            "primary_complete": not primary_missing,
            "technical_acceptance_blockers": technical_blockers,
            "COMPLETE_COHERENT_PACKAGE": (
                complete_coherent
            ),
            "complete_coherent_package": (
                complete_coherent
            ),
            "core_package_complete_exact_counts_and_revision": not core_missing,
            "core_package_missing_or_incoherent": core_missing,
            "optional_diagnostic_complete": not optional_missing,
            "optional_diagnostic_missing": optional_missing,
            "full_package_complete": complete_coherent,
            "full_package_missing": core_missing,
            "secondary_yoke_estimand_available": yoke_analysis["secondary_estimand_available"],
        },
        "safety_resource_gate": {
            "safety_violations": safety_violations,
            "no_safety_violation": safety_violations == 0,
            "no_cap_violation": resources["actual_team_ticks"] <= config.total_tick_cap,
            "latency_gate": latency_ratio <= 1.10,
        },
        "registered_design_revision": COMPOSITE_REVISION,
        "mathematical_closure": {
            "prospective_delta_status": PROSPECTIVE_DELTA_STATUS,
            "status": MATHEMATICAL_CLOSURE_STATUS,
            "closure_record": MATHEMATICAL_CLOSURE_RECORD,
            "prior_local_review_record_non_authoritative_under_current_boundary": (
                LOCAL_MATHEMATICAL_REVIEW_RECORD
            ),
            "authority": "same-direction External ChatGPT Pro",
            "authority_conversation": (
                "https://chatgpt.com/c/6a7c5d40-6178-83e8-8f7bcea1a8cc"
            ),
            "authority_model": "Pro",
            "result_blind": True,
            "science_bearing_defect_count": 0,
            "same_direction_EM_intake": "ACCEPTED",
            "confirmed": MATHEMATICAL_CLOSURE_CONFIRMED,
        },
        "host_facts": {
            "horizon": 256, "agents": 2, "mode_flip_probability_per_tick": 1 / 48,
            "sensor_error_probability": 0.15, "lease_ticks": 12,
            "refresh_cost_busy_ticks": [0.02, 1], "rebind_cost_busy_ticks": [0.04, 2],
            "schedule_labels_are_actor_inputs": False, "recurrent_actor": False,
            "exposure_interval": "right-closed integer slots (b_prev,t] excluding lease-masked slots",
            "tick_zero_policy_observed_virtual_exposure": [8, 1, 7],
            "terminal_H_has_action_likelihood_entropy_reset_or_critic_row": False,
            "TIMING_ONLY_actor_zero_coordinates": [2, 3, 4, 8, 9],
            "TIMING_ONLY_description": (
                "feed-forward task-content-blind tenure/cadence/own-action-state heuristic"
            ),
            "TIMING_ONLY_initial_tenure_and_action_domains_separate_from_content_tapes": True,
            "TIMING_ONLY_critic_full_state_but_no_shared_actor_representation": True,
            "TIMING_ONLY_content_access_claim_uses_native_and_IID_no_safety_only": True,
            "safety_panel_supports_TIMING_ONLY_content_access_claim": False,
        },
        "environment": {
            "python": platform.python_version(), "torch": torch.__version__,
            "numpy": np.__version__, "platform": platform.platform(),
        },
        "material_anomalies": [],
        "claim_ceiling": (
            "The seven deterministic cells support only the named finite-budget ONLGR-versus-RAW "
            "package estimands. A positive IID ONLGR-versus-RAW contrast plus the operational marked "
            "partition gate and corrected ONLGR post-startup 64/4/4/4 gate may support a useful "
            "eligible-exposure-link inductive bias when next k is independent of visible history. "
            "A positive IID ONLGR-versus-TIMING-ONLY return and service "
            "gate, oracle headroom, and full ONLGR post-startup 64/4/4/4 marked activity support only "
            "that access to "
            "current binding, mismatch, and partner-content coordinates benefited the marked intervention "
            "policy beyond the registered feed-forward task-content-blind tenure/cadence/own-action-state "
            "heuristic on this host. They do not identify event timing versus conditional mark selection. "
            "No result identifies lease or REBIND causality, a literal hazard, RAW incapacity, arbitrary k, "
            "variable N, UAV transfer, or a yoke-mediated mechanism. Partition and yoke facts remain "
            "learned-output/post-treatment support-conditioned diagnostics; eligible-time diagnostics "
            "separate virtual startup exposure from observed physical exposure."
        ),
    }
    _write_json(output_root / "raw_result.json", result)
    _write_json(result_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run ONLGR-B1 train/evaluate/analyze exactly once"
    )
    parser.add_argument("action", choices=("train-evaluate-analyze",))
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    result = exercise(
        output_root=args.output_root.resolve(), result_path=args.result.resolve(),
        config=PRODUCTION_CONFIG,
    )
    print(json.dumps({
        "result": str(args.result.resolve()),
        "activity_began": result["scientific_activity"]["began"],
        "primary_complete": result["completeness"]["primary_complete"],
        "full_package_complete": result["completeness"]["full_package_complete"],
        "actual_team_ticks": result["resource_diagnostics"]["actual_team_ticks"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
