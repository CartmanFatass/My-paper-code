"""Run the clean-process dynamic-roster direct-access qualification."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import time
import traceback
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from ha_ctse_process.dynamic_roster_clean_process_testbed import (
    PROCESS_CHANNEL_FIELDS,
    audit_clean_process_contract,
    make_clean_process_dynamic_roster_ledger,
    make_clean_process_environment,
)
from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    EVALUATION_LEDGER_SEED,
    HORIZON,
    MAX_LIFECYCLES,
    constructive_actions,
)
from scripts.run_dynamic_roster_stage_b import (
    FORMAL_EVAL_EPISODES,
    FORMAL_NUM_ENVS,
    FORMAL_UPDATES,
    run_stage_b,
)
from ha_ctse_process.dynamic_roster_direct import json_ready


RANDOM_CONTROL_SEED = 117_057


def _write_status(path: Path, **fields: Any) -> None:
    fields = {
        **fields,
        "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    path.write_text(
        "".join(f"{key}={value}\n" for key, value in fields.items()),
        encoding="utf-8",
    )


def _random_action_table(episode_id: int) -> np.ndarray:
    rng = np.random.default_rng(
        np.random.SeedSequence([RANDOM_CONTROL_SEED, int(episode_id), 0])
    )
    return rng.integers(
        0,
        ACTION_COUNT,
        size=(HORIZON, MAX_LIFECYCLES),
        dtype=np.int64,
    )


def _control_outcomes(episode_ids: tuple[int, ...]) -> dict[str, Any]:
    constructive_rows: list[tuple[float, float, float]] = []
    random_rows: list[tuple[float, float, float]] = []
    for episode_id in episode_ids:
        ledger = make_clean_process_dynamic_roster_ledger(
            episode_id, master_seed=EVALUATION_LEDGER_SEED
        )
        environment = make_clean_process_environment(ledger)
        for _ in range(HORIZON):
            view = environment.observe()
            environment.step(constructive_actions(environment, view))
        outcome = environment.outcome()
        constructive_rows.append(
            (outcome.persistent_score, outcome.short_score, outcome.utility)
        )

        random_environment = make_clean_process_environment(ledger)
        table = _random_action_table(episode_id)
        for time_index in range(HORIZON):
            view = random_environment.observe()
            random_environment.step(
                {key: int(table[time_index, key]) for key in view.active_keys}
            )
        outcome = random_environment.outcome()
        random_rows.append(
            (outcome.persistent_score, outcome.short_score, outcome.utility)
        )

    constructive = np.asarray(constructive_rows, dtype=np.float64)
    random = np.asarray(random_rows, dtype=np.float64)
    return {
        "episode_ids": list(episode_ids),
        "constructive": {
            "persistent": constructive[:, 0].tolist(),
            "short": constructive[:, 1].tolist(),
            "utility": constructive[:, 2].tolist(),
            "persistent_min": float(constructive[:, 0].min()),
            "short_min": float(constructive[:, 1].min()),
            "utility_min": float(constructive[:, 2].min()),
        },
        "uniform_random": {
            "persistent": random[:, 0].tolist(),
            "short": random[:, 1].tolist(),
            "utility": random[:, 2].tolist(),
            "positive_utility_fraction": float(np.mean(random[:, 2] > 0.0)),
            "utility_mean": float(random[:, 2].mean()),
        },
    }


def run_clean_process_qualification(
    *,
    output_root: Path,
    device_name: str,
    num_envs: int,
    updates: int,
    eval_episodes: int,
    smoke: bool,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    result_dir = output_root / "result"
    result_dir.mkdir(parents=True, exist_ok=True)
    status_path = output_root / "runner_status.txt"

    wall_start = time.perf_counter()
    _write_status(status_path, state="running", phase="carrier_controls")
    controls_start = time.perf_counter()
    control_episode_ids = tuple(range(8 if smoke else eval_episodes))
    controls = _control_outcomes(control_episode_ids)
    carrier_audit = audit_clean_process_contract()
    controls_seconds = time.perf_counter() - controls_start

    constructive = controls["constructive"]
    random = controls["uniform_random"]
    carrier_pass = bool(
        constructive["persistent_min"] >= 0.95
        and constructive["short_min"] >= 0.95
        and constructive["utility_min"] >= 0.95
        and random["positive_utility_fraction"] >= 0.20
        and random["utility_mean"] < 0.55
        and all(carrier_audit.values())
    )

    direct: dict[str, Any] | None = None
    direct_seconds = 0.0
    if smoke or carrier_pass:
        direct_start = time.perf_counter()
        direct = run_stage_b(
            output_root=output_root,
            device_name=device_name,
            num_envs=num_envs,
            updates=updates,
            eval_episodes=eval_episodes,
            smoke=smoke,
            ledger_factory=make_clean_process_dynamic_roster_ledger,
            environment_factory=make_clean_process_environment,
        )
        direct_seconds = time.perf_counter() - direct_start

    process_contract_valid = bool(
        all(carrier_audit.values())
        and list(PROCESS_CHANNEL_FIELDS)
        == ["actuator_position", "actuator_velocity"]
    )
    implementation_valid = bool(
        process_contract_valid
        and (
            direct is None
            or (
                direct["implementation_valid"]
                and int(direct["counts"]["skill_updates"]) == 0
                and int(direct["counts"]["high_updates"]) == 0
                and int(direct["counts"]["intrinsic_reward_reads"]) == 0
            )
        )
    )
    if smoke:
        status = "SMOKE_COMPLETE" if implementation_valid else "SMOKE_INVALID"
    elif not implementation_valid:
        status = "INVALID_CLEAN_CARRIER_IMPLEMENTATION"
    elif not carrier_pass:
        status = "RETIRE_CLEAN_CARRIER_CALIBRATION"
    elif direct is not None and bool(direct["direct_access_pass"]):
        status = "PASS_CLEAN_CARRIER_DIRECT_ACCESS"
    else:
        status = "NO_ACCESS_CLEAN_CARRIER_DIRECT"

    result = {
        "schema_version": 1,
        "stage": "clean_process_dynamic_roster_direct_access",
        "status": status,
        "implementation_valid": implementation_valid,
        "carrier_pass": carrier_pass if not smoke else None,
        "direct_access_pass": (
            None if direct is None else direct["direct_access_pass"]
        ),
        "carrier_audit": carrier_audit,
        "process_channel": {
            "fields": list(PROCESS_CHANNEL_FIELDS),
            "input_to_actor": False,
            "input_to_critic": False,
            "input_to_reward": False,
            "input_to_gae_or_ppo": False,
        },
        "controls": controls,
        "direct": direct,
        "contract": {
            "num_envs": num_envs,
            "horizon": HORIZON,
            "outer_updates": updates,
            "planned_environment_transitions": num_envs * HORIZON * updates,
            "environment_transitions": (
                0 if direct is None else direct["counts"]["environment_steps"]
            ),
            "ppo_passes_per_update": 4,
            "planned_optimizer_steps": updates * 4,
            "optimizer_steps": (
                0 if direct is None else direct["counts"]["optimizer_steps"]
            ),
            "evaluation_episodes_per_mode": eval_episodes,
            "random_control_seed": RANDOM_CONTROL_SEED,
            "new_carrier_not_iteration5_spatial": True,
        },
        "thresholds": {
            "constructive_persistent_short_utility_min": 0.95,
            "random_positive_utility_fraction_min": 0.20,
            "random_utility_mean_exclusive_max": 0.55,
            **({} if direct is None else direct["thresholds"]),
        },
        "wall_seconds": {
            "carrier_controls": controls_seconds,
            "direct_core": direct_seconds,
            "total": time.perf_counter() - wall_start,
        },
        "authoritative_status_source": str(status_path),
        "next_action": (
            "submit the accepted terminal evidence for tracked external review"
            if status == "PASS_CLEAN_CARRIER_DIRECT_ACCESS"
            else "apply the registered terminal branch without rescue"
        ),
    }
    result_path = result_dir / "clean_process_direct_access.json"
    result_path.write_text(
        json.dumps(json_ready(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_status(
        status_path,
        state="complete",
        phase="terminal",
        status=status,
        update=updates,
        updates_total=updates,
        environment_steps=(
            0 if direct is None else direct["counts"]["environment_steps"]
        ),
        optimizer_steps=(
            0 if direct is None else direct["counts"]["optimizer_steps"]
        ),
        result=result_path,
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--num-envs", type=int, default=FORMAL_NUM_ENVS)
    parser.add_argument("--updates", type=int, default=FORMAL_UPDATES)
    parser.add_argument("--eval-episodes", type=int, default=FORMAL_EVAL_EPISODES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status_path = args.output_root / "runner_status.txt"
    try:
        result = run_clean_process_qualification(
            output_root=args.output_root,
            device_name=args.device,
            num_envs=args.num_envs,
            updates=args.updates,
            eval_episodes=args.eval_episodes,
            smoke=args.smoke,
        )
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "implementation_valid": result["implementation_valid"],
                    "result": str(
                        args.output_root
                        / "result"
                        / "clean_process_direct_access.json"
                    ),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        args.output_root.mkdir(parents=True, exist_ok=True)
        (args.output_root / "runner_stderr.log").write_text(
            traceback.format_exc(), encoding="utf-8"
        )
        _write_status(
            status_path,
            state="failed",
            phase="runner",
            error=f"{type(exc).__name__}: {exc}",
        )
        raise


if __name__ == "__main__":
    sys.exit(main())
