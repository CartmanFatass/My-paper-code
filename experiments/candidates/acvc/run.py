"""Single registered train -> evaluate -> analyze entry point for ACVC-B1."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import time
from typing import Mapping

from .analyze import ArmAccumulator, analyze_registered
from .host import SPLIT_COUNTS, iter_scenes, manifest_balance, run_scene
from .policies import (
    AUTH_PROBE, DET_BOUND, FIXED_ARMS, IGNORE, LEARN_CORRECT, LEARN_PERM,
    LEARNED_ARMS, TabularQLearner, evaluation_tie_rank, fixed_action,
)


ASSIGNMENT_ID = "ACVC-B1-LEARN-CORRECT-v1"
CANDIDATE = "CAND-ACVC-COUNTEREVIDENCE-VETO"
BASE_SEEDS = (11, 23, 37, 53, 71, 89, 107, 127, 149, 173)
CAPS = {
    "cpu_workers": 1,
    "decision_transitions": 5_000_000,
    "wall_seconds": 18 * 60,
    "peak_rss_bytes": int(1.5 * 1024**3),
}
DECLARED_COUNTS = {
    "learned_arm_scenes": 245_760,
    "fixed_policy_test_scenes": 115_200,
    "maximum_decision_transitions": 4_331_520,
    "learned_checkpoints": 20,
    "base_seeds": 10,
}


def _peak_process_rss_bytes() -> int:
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
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        get_current_process = ctypes.windll.kernel32.GetCurrentProcess  # type: ignore[attr-defined]
        get_current_process.restype = ctypes.c_void_p
        get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo  # type: ignore[attr-defined]
        get_process_memory_info.argtypes = (
            ctypes.c_void_p, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD,
        )
        get_process_memory_info.restype = wintypes.BOOL
        if not get_process_memory_info(get_current_process(), ctypes.byref(counters), counters.cb):
            raise OSError("GetProcessMemoryInfo failed")
        return int(counters.PeakWorkingSetSize)
    import resource
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
    temporary.replace(path)


def _check_caps(started: float, transitions: int) -> dict[str, object]:
    usage = {
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": _peak_process_rss_bytes(),
        "decision_transitions": transitions,
        "cpu_workers": 1,
    }
    if usage["wall_seconds"] > CAPS["wall_seconds"]:
        raise RuntimeError("registered wall-time cap breached")
    if usage["peak_rss_bytes"] > CAPS["peak_rss_bytes"]:
        raise RuntimeError("registered peak-RSS cap breached")
    if transitions > CAPS["decision_transitions"]:
        raise RuntimeError("registered transition cap breached")
    return usage


def _train_scene(learner: TabularQLearner, arm: str, scene) -> dict[str, object]:
    return run_scene(
        scene,
        arm=arm,
        selector=lambda state: learner.training_action(state, episode=scene.episode),
        transition_observer=lambda state, action, reward, next_state, scene_done: learner.update(
            state, action, reward, next_state, scene_done
        ),
    )


def exercise(*, output_root: Path, result_path: Path) -> dict[str, object]:
    if output_root.exists():
        raise FileExistsError("registered exercise requires a fresh output root")
    if result_path.exists():
        raise FileExistsError("final result path already exists")
    output_root.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    total_transitions = 0
    total_scenes = 0
    learned_scenes = 0
    fixed_scenes = 0
    learned_by_split = {"train": 0, "validation": 0, "test": 0}
    activity_evidence: dict[str, object] | None = None
    seed_rows: list[dict[str, object]] = []
    manifest = {
        "artifact_kind": "ACVC_B1_REGISTERED_MANIFEST",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "base_seeds": list(BASE_SEEDS),
        "namespaces": {
            "train_world": "100000+s", "train_binding": "200000+s", "learner": "300000+s",
            "validation_world": "400000+s", "validation_binding": "450000+s",
            "test_world": "500000+s", "test_binding": "600000+s", "evaluation_tie_rank": "700000+s",
        },
        "split_counts_per_arm_seed": {
            key: {"episodes": value[0], "event": value[1], "all_clean": value[0] - value[1],
                  "event_cell_repeats": value[2]}
            for key, value in SPLIT_COUNTS.items()
        },
        "declared_counts": DECLARED_COUNTS,
        "caps": CAPS,
        "single_registered_action": "exercise",
    }
    _write_json(output_root / "manifest.json", manifest)

    for base_seed in BASE_SEEDS:
        learners = {
            arm: TabularQLearner(300_000 + base_seed) for arm in LEARNED_ARMS
        }
        for scene in iter_scenes(base_seed, "train"):
            for arm in LEARNED_ARMS:
                row = _train_scene(learners[arm], arm, scene)
                total_transitions += int(row["transitions"])
                total_scenes += 1
                learned_scenes += 1
                learned_by_split["train"] += 1
            if scene.episode % 256 == 0:
                _check_caps(started, total_transitions)
        for arm, learner in learners.items():
            _write_json(
                output_root / "checkpoints" / f"seed_{base_seed}" / f"{arm}.json",
                learner.to_json(),
            )

        tie_rank = evaluation_tie_rank(base_seed)
        validation = {arm: ArmAccumulator() for arm in LEARNED_ARMS}
        for scene in iter_scenes(base_seed, "validation"):
            for arm in LEARNED_ARMS:
                row = run_scene(
                    scene, arm=arm,
                    selector=lambda state, learner=learners[arm]: learner.evaluation_action(state, tie_rank),
                )
                validation[arm].add(row)
                total_transitions += int(row["transitions"])
                total_scenes += 1
                learned_scenes += 1
                learned_by_split["validation"] += 1

        accumulators = {arm: ArmAccumulator() for arm in (*LEARNED_ARMS, *FIXED_ARMS)}
        for scene in iter_scenes(base_seed, "test"):
            paired_rows: dict[str, dict[str, object]] = {}
            for arm in LEARNED_ARMS:
                retain = activity_evidence is None and scene.event
                row = run_scene(
                    scene, arm=arm,
                    selector=lambda state, learner=learners[arm]: learner.evaluation_action(state, tie_rank),
                    retain_rows=retain,
                )
                paired_rows[arm] = row
                accumulators[arm].add(row)
                total_transitions += int(row["transitions"])
                total_scenes += 1
                learned_scenes += 1
                learned_by_split["test"] += 1
            if activity_evidence is None and scene.event:
                activity_evidence = {
                    "criterion": "first complete paired held-out true-event scene from both final checkpoints",
                    "reached": True,
                    "base_seed": base_seed,
                    "test_episode": scene.episode,
                    "arms": {
                        arm: {
                            "scene_reward": paired_rows[arm]["scene_reward"],
                            "target_action_outcome_rows": paired_rows[arm]["target_action_outcome_rows"],
                        }
                        for arm in LEARNED_ARMS
                    },
                }
                _write_json(output_root / "activity_start.json", activity_evidence)
            for arm in FIXED_ARMS:
                row = run_scene(scene, arm=arm, selector=lambda state, arm=arm: fixed_action(arm, state))
                accumulators[arm].add(row)
                total_transitions += int(row["transitions"])
                total_scenes += 1
                fixed_scenes += 1
            if scene.episode % 256 == 0:
                _check_caps(started, total_transitions)
        seed_rows.append({
            "base_seed": base_seed,
            "learner_seed": 300_000 + base_seed,
            "evaluation_tie_rank": [action.value for action in tie_rank],
            "arms": {arm: accumulator.summary() for arm, accumulator in accumulators.items()},
            "diagnostic_validation": {arm: accumulator.summary() for arm, accumulator in validation.items()},
        })
        _check_caps(started, total_transitions)

    if activity_evidence is None:
        raise RuntimeError("scientific activity criterion was not reached")
    actual_usage = _check_caps(started, total_transitions)
    fixed_expected = {
        DET_BOUND: {"mean_event_reward": 3.46, "d_joint_rate": 1.0},
        AUTH_PROBE: {"mean_event_reward": 2.935, "d_joint_rate": 0.125},
        IGNORE: {"mean_event_reward": -7.04},
    }
    if learned_scenes != DECLARED_COUNTS["learned_arm_scenes"]:
        raise RuntimeError(f"learned scene count mismatch: {learned_scenes}")
    if fixed_scenes != DECLARED_COUNTS["fixed_policy_test_scenes"]:
        raise RuntimeError(f"fixed scene count mismatch: {fixed_scenes}")
    fixed_observed_deviations = {
        arm: {
            metric: [float(row["arms"][arm][metric]) - expected for row in seed_rows]  # type: ignore[index]
            for metric, expected in expectations.items()
        }
        for arm, expectations in fixed_expected.items()
    }
    result: dict[str, object] = {
        "artifact_kind": "ACVC_B1_REGISTERED_RESULT",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "scientific_activity": activity_evidence,
        "scientific_activity_criterion_reached": True,
        "declared_counts": DECLARED_COUNTS,
        "actual_counts": {
            "scenes": total_scenes,
            "learned_arm_scenes": learned_scenes,
            "fixed_policy_test_scenes": fixed_scenes,
            "learned_scenes_by_split": learned_by_split,
            "learned_scenes_per_arm_seed": {
                "train": 7_680, "validation": 768, "test": 3_840,
                "train_event": 3_840, "train_all_clean": 3_840,
                "validation_event": 384, "validation_all_clean": 384,
                "test_event": 1_920, "test_all_clean": 1_920,
            },
            "fixed_test_scenes_per_arm_seed": {
                "test": 3_840, "event": 1_920, "all_clean": 1_920,
            },
            "decision_transitions": total_transitions,
            "learned_checkpoints": len(BASE_SEEDS) * len(LEARNED_ARMS),
        },
        "caps": CAPS,
        "actual_resource_usage": actual_usage,
        "per_seed": seed_rows,
        "analysis": analyze_registered(seed_rows),
        "fixed_policy_analytic_references": fixed_expected,
        "fixed_policy_observed_minus_analytic_by_seed": fixed_observed_deviations,
        "fixed_policy_sampling_note": (
            "AUTH-PROBE depends on relative service-order/event-target rank, whose independently shuffled "
            "finite manifest is not fully crossed; ordinary finite-block deviation is not an anomaly."
        ),
        "reporting_only_latent_oracle_mean_event_reward": 3.51,
        "material_anomalies": [],
        "claim_ceiling": (
            "Constructed synchronous four-target host, one truthful fixed certifier, at most one event, "
            "stable IDs/epochs, pre-decision delivery, stated costs, one tabular learner, ten seeds and finite budget only."
        ),
    }
    _write_json(output_root / "raw_result.json", result)
    _write_json(result_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    registered = subparsers.add_parser("exercise", help="run the one full registered ACVC-B1 flow")
    registered.add_argument("--output-root", required=True, type=Path)
    registered.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    result = exercise(output_root=args.output_root.resolve(), result_path=args.result.resolve())
    print(json.dumps({
        "result": str(args.result.resolve()),
        "activity_reached": result["scientific_activity_criterion_reached"],
        "transitions": result["actual_counts"]["decision_transitions"],  # type: ignore[index]
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
