"""Run the sole fixed1e-4 COND/DENSE pair, without selection or checkpoint loading."""

import argparse
import json
from pathlib import Path
import re
import time

import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_fixed_lr_b01 import protocol
from experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01 import study as inherited


CARD = "docs/research/candidates/metric_ground_transport_allocation/MGTAP_FIXED_LR_B01_SCIENCE_CARD_20260914.md"


def run_study(output, launch_sha, *, pair_factory=inherited.build_cond_pair,
              fit_runner=inherited._native_fit, clock=time.monotonic):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    start = clock()
    rows, rollouts, fits, partial_fits, limits = [], [], [], [], []
    primary, current = None, None
    with (output / "episodes.jsonl").open("w", encoding="utf-8") as episode_file, \
            (output / "rollouts.jsonl").open("w", encoding="utf-8") as rollout_file:

        def emit(stream, collection, row):
            collection.append(row)
            stream.write(json.dumps(inherited.clean_json(row, limits), allow_nan=False) + "\n")
            stream.flush()

        try:
            pair = pair_factory(protocol.MASTER)
            for arm in protocol.ARMS:
                current = arm
                fits.append(fit_runner(
                    stage="fixed", master=protocol.MASTER, lr_key="slow", arm=arm,
                    models=pair[arm], output=output, study_start=start, clock=clock,
                    contract=protocol, emit_partial_fit=partial_fits.append,
                    emit_episode=lambda row: emit(episode_file, rows, row),
                    emit_rollout=lambda row: emit(rollout_file, rollouts, row)))
            primary = protocol.primary(rows)
        except Exception as error:
            limits.append(f"execution: {type(error).__name__}: {error}")

    fits = inherited.clean_json(fits, limits)
    limits.extend(inherited._fit_errors(fits))
    for fit in fits:
        limits.extend(f"{fit['arm']}: {item}" for item in fit.get("limits", []))
    complete = len(fits) == 2 and primary is not None and not limits
    summary = {
        "mode": "UAV_B_EXPLORE", "object": protocol.OBJECT, "card": CARD,
        "scientific_invocation": True, "launch_sha": launch_sha,
        "master": protocol.MASTER, "learning_rate": 1e-4,
        "configuration": {
            "arm_order": list(protocol.ARMS), "horizon": 256,
            "train_episodes_per_fit": 256, "final_episodes_per_fit": 32,
            "chunk": 32, "episodes_per_rollout": 2, "epochs": 4,
            "ratio_grouping": "agent_compound", "entropy_coef": .01,
            "gradient_clip": .5, "device": "cpu", "dtype": "float32", "threads": 1,
            "fit_watchdog_seconds": inherited.FIT_CAP,
            "study_watchdog_seconds": inherited.STUDY_CAP,
        },
        "selection_history": "8251 selected both1e-4; positive8252 observed before this object was chosen; no new selection",
        "planned_exposure": protocol.planned_exposure(),
        "fits": fits, "completed_fit_count": len(fits),
        "partial_fits": inherited.clean_json(partial_fits, limits),
        "current_on_failure": current if not complete else None,
        "raw_episode_file": "episodes.jsonl", "raw_episode_rows": len(rows),
        "raw_rollout_file": "rollouts.jsonl", "raw_rollout_rows": len(rollouts),
        "primary": primary,
        "cost_law": "two serial fits; each: init +65536 training ticks +512 Adam calls +8192 final ticks +checkpoint",
        "study_body_wall_before_summary": clock() - start,
        "timing_scope": "study body excludes imports, CLI/thread setup, summary write and exit; fit bodies also exclude pair factory; GNU time measures complete command",
        "limits": limits, "status": "COMPLETE" if complete else "INCOMPLETE",
    }
    inherited._write_json(output / "summary.json", summary, limits)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--master", type=int, default=protocol.MASTER)
    args = parser.parse_args()
    if args.master != protocol.MASTER:
        parser.error("only the carded unscreened master8253 is accepted")
    if not re.fullmatch(r"[0-9a-f]{40}", args.launch_sha):
        parser.error("--launch-sha must be the exact40-character lowercase Git SHA")
    torch.set_num_threads(1)
    summary = run_study(args.out, args.launch_sha)
    print(json.dumps(summary, indent=2, allow_nan=False))
    raise SystemExit(0 if summary["status"] == "COMPLETE" else 1)


if __name__ == "__main__":
    main()
