"""Run the clean supplied-executor F1 high-path G0 package."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import time
import traceback
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch

from ha_ctse_process.dynamic_roster_supplied_executor import (
    ACTION_SEED,
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    EVALUATION_TASK_SEED,
    FORMAL_EVAL_EPISODES,
    FORMAL_HIGH_OPTIMIZER_STEPS,
    FORMAL_HORIZON,
    FORMAL_NUM_ENVS,
    FORMAL_TRANSITIONS,
    FORMAL_UPDATES,
    FRONTIER_STREAM_ID,
    MODEL_SEED,
    OPPORTUNITY_FRONTIER_SEED,
    OPPORTUNITY_STREAM_ID,
    PPO_PASSES_PER_UPDATE,
    TRAIN_TASK_SEED,
    run_clean_supplied_executor_high_path,
)


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _write_status(path: Path, **fields: Any) -> None:
    value = {
        **fields,
        "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    _atomic_text(path, "".join(f"{key}={item}\n" for key, item in value.items()))


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_text(
        path,
        json.dumps(dict(value), ensure_ascii=False, indent=2, allow_nan=False),
    )


def _dry_result() -> dict[str, Any]:
    valid = bool(
        FORMAL_NUM_ENVS == 16
        and FORMAL_HORIZON == 80
        and FORMAL_UPDATES == 250
        and FORMAL_TRANSITIONS == 320_000
        and PPO_PASSES_PER_UPDATE == 4
        and FORMAL_HIGH_OPTIMIZER_STEPS == 1_000
        and FORMAL_EVAL_EPISODES == 256
        and BOOTSTRAP_REPETITIONS == 10_000
        and MODEL_SEED == 57_057
        and TRAIN_TASK_SEED == 67_057
        and OPPORTUNITY_FRONTIER_SEED == 77_057
        and OPPORTUNITY_STREAM_ID == 0
        and FRONTIER_STREAM_ID == 1
        and ACTION_SEED == 87_057
        and EVALUATION_TASK_SEED == 97_057
        and BOOTSTRAP_SEED == 107_057
    )
    return {
        "schema_version": 1,
        "status": "DRY_VALID" if valid else "DRY_INVALID",
        "formal_evidence": False,
        "implementation_valid": valid,
        "counts": {
            "environment_transitions": 0,
            "high_optimizer_steps": 0,
            "low_optimizer_steps": 0,
        },
        "formal_contract": {
            "num_envs": FORMAL_NUM_ENVS,
            "horizon": FORMAL_HORIZON,
            "updates": FORMAL_UPDATES,
            "environment_transitions": FORMAL_TRANSITIONS,
            "ppo_passes_per_update": PPO_PASSES_PER_UPDATE,
            "high_optimizer_steps": FORMAL_HIGH_OPTIMIZER_STEPS,
            "low_optimizer_steps": 0,
            "evaluation_episodes_per_arm": FORMAL_EVAL_EPISODES,
            "bootstrap_resamples": BOOTSTRAP_REPETITIONS,
        },
        "runner_selects_successor": False,
    }


def run_supplied_executor_qualification(
    *,
    output_root: Path,
    device_name: str,
    num_envs: int,
    updates: int,
    eval_episodes: int,
    smoke: bool,
    dry_validate: bool = False,
    resume_from: Path | None = None,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    status_path = output_root / "runner_status.txt"
    result_path = (
        output_root / "result" / "clean_supplied_executor_high_path_g0.json"
    )
    checkpoint_path = output_root / "checkpoints" / "latest_high_only.pt"
    update_zero_path = output_root / "checkpoints" / "update_000_high.pt"
    started = time.perf_counter()
    _write_status(
        status_path,
        state="running",
        phase="dry_validation" if dry_validate else "m0_training_evaluation",
        formal_evidence=not smoke and not dry_validate,
        num_envs=num_envs,
        updates=updates,
        eval_episodes=eval_episodes,
        result=result_path,
        checkpoint=checkpoint_path,
    )
    if dry_validate:
        result = _dry_result()
    else:
        resume_payload = (
            None
            if resume_from is None
            else torch.load(resume_from, map_location=device_name, weights_only=False)
        )
        result = run_clean_supplied_executor_high_path(
            device=device_name,
            num_envs=int(num_envs),
            updates=int(updates),
            eval_episodes=int(eval_episodes),
            smoke=bool(smoke),
            checkpoint_path=checkpoint_path,
            update_zero_path=update_zero_path,
            resume_payload=resume_payload,
        )
    result["authoritative_status_source"] = str(status_path)
    result["result_path"] = str(result_path)
    result["checkpoint_path"] = (
        None if dry_validate else str(checkpoint_path)
    )
    result["wall_seconds"] = time.perf_counter() - started
    _write_json(result_path, result)
    actual = dict(result.get("contract", {}).get("actual", {}))
    _write_status(
        status_path,
        state="complete",
        phase="terminal",
        status=result["status"],
        formal_evidence=result["formal_evidence"],
        implementation_valid=result["implementation_valid"],
        environment_transitions=actual.get("environment_transitions", 0),
        high_optimizer_steps=actual.get("high_optimizer_steps", 0),
        low_optimizer_steps=0,
        result=result_path,
        checkpoint=("none" if dry_validate else checkpoint_path),
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--dry-validate", action="store_true")
    parser.add_argument("--num-envs", type=int)
    parser.add_argument("--updates", type=int)
    parser.add_argument("--eval-episodes", type=int)
    parser.add_argument("--resume-from", type=Path)
    args = parser.parse_args()
    args.num_envs = (
        int(args.num_envs)
        if args.num_envs is not None
        else (2 if args.smoke else FORMAL_NUM_ENVS)
    )
    args.updates = (
        int(args.updates)
        if args.updates is not None
        else (1 if args.smoke else FORMAL_UPDATES)
    )
    args.eval_episodes = (
        int(args.eval_episodes)
        if args.eval_episodes is not None
        else (4 if args.smoke else FORMAL_EVAL_EPISODES)
    )
    return args


def main() -> int:
    args = parse_args()
    status_path = args.output_root.resolve() / "runner_status.txt"
    error_path = args.output_root.resolve() / "runner_stderr.log"
    try:
        result = run_supplied_executor_qualification(
            output_root=args.output_root,
            device_name=args.device,
            num_envs=args.num_envs,
            updates=args.updates,
            eval_episodes=args.eval_episodes,
            smoke=args.smoke,
            dry_validate=args.dry_validate,
            resume_from=args.resume_from,
        )
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "formal_evidence": result["formal_evidence"],
                    "implementation_valid": result["implementation_valid"],
                    "result": result["result_path"],
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        _atomic_text(error_path, traceback.format_exc())
        _write_status(
            status_path,
            state="failed",
            phase="runner",
            error=f"{type(exc).__name__}: {exc}",
            result=(
                args.output_root.resolve()
                / "result"
                / "clean_supplied_executor_high_path_g0.json"
            ),
        )
        raise


if __name__ == "__main__":
    sys.exit(main())
