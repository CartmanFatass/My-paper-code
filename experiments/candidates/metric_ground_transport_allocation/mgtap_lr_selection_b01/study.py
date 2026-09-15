"""Complete serial native runner for MGTAP-LR-SELECTION-B01."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import time

import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01 import protocol
from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.conditional_pooling import (
    build_cond_pair,
)
from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import (
    COND, DENSE, geometry_exposure, geometry_snapshot,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    collect_episode, optimizer_for, update,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.ucope.uav_motion_prefix_b01.study import clean_json, new_counts


CARD = "docs/research/candidates/metric_ground_transport_allocation/MGTAP_LR_SELECTION_B01_SCIENCE_CARD_20260914.md"
FIT_CAP, STUDY_CAP = 1800.0, 14400.0
EXPECTED_COUNTS = {
    "train_episodes": 256, "eval_episodes": 32,
    "train_team_steps": 65536, "eval_team_steps": 8192,
    "team_steps": 73728, "optimizer_steps": 512, "rollouts": 128,
}


class StudyDeadline:
    """The carded ordinary technical watchdogs, without retry or replacement."""

    def __init__(self, study_start, fit_start, clock=time.monotonic):
        self.study_start, self.fit_start, self.clock = study_start, fit_start, clock

    def check(self):
        now = self.clock()
        if now - self.study_start > STUDY_CAP:
            raise TimeoutError("full serial study watchdog exceeded")
        if now - self.fit_start > FIT_CAP:
            raise TimeoutError("fit watchdog exceeded")
        return now


def _write_json(path, value, limits):
    path = Path(path)
    path.write_text(json.dumps(clean_json(value, limits), indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")
    return path


def _optimizer(actor, critic, learning_rate):
    """Reuse accepted Adam construction, changing only the selected LR."""
    optimizer = optimizer_for(actor, critic)
    for group in optimizer.param_groups:
        group["lr"] = learning_rate
    return optimizer


def _native_fit(*, stage, master, lr_key, arm, models, output, emit_episode,
                emit_rollout, study_start, clock=time.monotonic, contract=protocol,
                emit_partial_fit=None):
    """Fit and evaluate one candidate-owned actor/critic/Adam/RNG state."""
    actor, critic = models
    learning_rate = contract.LEARNING_RATES[lr_key]
    fit_start = clock()
    deadline = StudyDeadline(study_start, fit_start, clock)
    counts, limits = new_counts(False), []
    initial, phase = None, "initialization"
    try:
        base = 100000 * master
        env = make_real(base + 1000)
        counts["constructors"] += 1
        counts["constructor_resets"] += 1
        initial = geometry_snapshot(actor, critic)
        optimizer = _optimizer(actor, critic, learning_rate)
        # Equal numeric addresses do not imply shared live RNG state: every fit owns these.
        train_velocity = generator(base + 21)

        def episode(phase, index, velocity_rng, duration_rng):
            address = contract.randomization(master, phase, index)
            metadata = {
                "object": contract.OBJECT, "stage": stage, "pair_master": master,
                "arm": arm, "lr_key": lr_key, "learning_rate": learning_rate,
                "phase": phase, "episode": index,
                "velocity_seed": address["velocity_seed"],
                "duration_seed": address["duration_seed"],
            }
            return collect_episode(
                env, actor, critic, contract.HORIZON, address["reset_seed"],
                velocity_rng, duration_rng, metadata, deadline.check, counts,
                emit_episode, lambda _row: None, limits, real=True, diagnostics=False,
                ratio_grouping="agent_compound")

        phase = "training"
        for rollout_index in range(contract.TRAIN_EPISODES // contract.EPISODES_PER_ROLLOUT):
            before = counts.copy()
            episodes = []
            for offset in range(contract.EPISODES_PER_ROLLOUT):
                index = contract.EPISODES_PER_ROLLOUT * rollout_index + offset
                address = contract.randomization(master, "train", index)
                episodes.append(episode("train", index, train_velocity,
                                        generator(address["duration_seed"])))
            records = update(actor, critic, optimizer, episodes, 32, deadline.check, counts,
                             ratio_grouping="agent_compound", entropy_coef=.01)
            counts["rollouts"] += 1
            emit_rollout({
                "object": contract.OBJECT, "stage": stage, "pair_master": master,
                "arm": arm, "lr_key": lr_key, "learning_rate": learning_rate,
                "rollout": rollout_index, "episodes": 2, "steps": 512,
                "epochs": records,
                "optimizer_steps": counts["optimizer_steps"] - before["optimizer_steps"],
            })
            deadline.check()

        training_counts = counts.copy()
        phase = "evaluation"
        for index in range(contract.EVAL_EPISODES):
            address = contract.randomization(master, "eval", index)
            episode("eval", index, generator(address["velocity_seed"]),
                    generator(address["duration_seed"]))
        deadline.check()
        phase = "checkpoint"
        checkpoint = output / f"{stage}_{lr_key}_{arm}.pt"
        torch.save({
            "object": contract.OBJECT, "stage": stage, "pair_master": master,
            "arm": arm, "lr_key": lr_key, "learning_rate": learning_rate,
            "actor": actor.state_dict(), "critic": critic.state_dict(),
            "optimizer": optimizer.state_dict(),
        }, checkpoint)
        return {
            "stage": stage, "pair_master": master, "arm": arm, "lr_key": lr_key,
            "learning_rate": learning_rate, "fit_complete": True,
            "panel_complete": counts["eval_episodes"] == contract.EVAL_EPISODES,
            "counts": counts, "training_counts": training_counts,
            "exposure": geometry_exposure(initial, actor, critic),
            "checkpoint": checkpoint.name, "fit_body_wall": clock() - fit_start,
            "limits": limits,
        }
    except Exception as error:
        if emit_partial_fit is not None:
            exposure, exposure_error = None, None
            if initial is not None:
                try:
                    exposure = geometry_exposure(initial, actor, critic)
                except Exception as diagnostic_error:
                    exposure_error = f"{type(diagnostic_error).__name__}: {diagnostic_error}"
            emit_partial_fit({
                "stage": stage, "pair_master": master, "arm": arm, "lr_key": lr_key,
                "learning_rate": learning_rate, "fit_complete": False, "phase": phase,
                "counts": counts.copy(), "exposure": exposure,
                "exposure_error": exposure_error,
                "counts_scope": "observed counters; an interrupted primitive may have additional unobserved work",
                "fit_body_wall": clock() - fit_start,
                "limits": limits + [f"{type(error).__name__}: {error}"],
            })
        raise


def _fit_errors(fits):
    errors = []
    for fit in fits:
        counts = fit.get("counts", {})
        if not fit.get("fit_complete") or not fit.get("panel_complete"):
            errors.append(f"{fit.get('stage')}/{fit.get('lr_key')}/{fit.get('arm')}: incomplete fit")
        if any(counts.get(key) != value for key, value in EXPECTED_COUNTS.items()):
            errors.append(f"{fit.get('stage')}/{fit.get('lr_key')}/{fit.get('arm')}: count mismatch")
    return errors


def run_study(output, launch_sha, *, pair_factory=build_cond_pair,
              fit_runner=_native_fit, clock=time.monotonic):
    """Run six selections, persist their choice, then run the fresh holdout pair."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    study_start = clock()
    rows, rollout_rows, fits, limits = [], [], [], []
    selection = primary = selection_hash = None
    current = None
    episode_file = (output / "episodes.jsonl").open("w", encoding="utf-8")
    rollout_file = (output / "rollouts.jsonl").open("w", encoding="utf-8")

    def emit(stream, collection, row):
        collection.append(row)
        stream.write(json.dumps(clean_json(row, limits), allow_nan=False) + "\n")
        stream.flush()

    try:
        # Candidate opportunity order is observable and intentionally fixed.
        for lr_key in protocol.LEARNING_RATES:
            pair = pair_factory(protocol.SELECTION_MASTER)
            for arm in protocol.ARMS:
                current = {"stage": "selection", "lr_key": lr_key, "arm": arm}
                fit = fit_runner(
                    stage="selection", master=protocol.SELECTION_MASTER,
                    lr_key=lr_key, arm=arm, models=pair[arm], output=output,
                    emit_episode=lambda row: emit(episode_file, rows, row),
                    emit_rollout=lambda row: emit(rollout_file, rollout_rows, row),
                    study_start=study_start, clock=clock)
                fits.append(fit)

        selection_rows = [row for row in rows
                          if row.get("stage") == "selection" and row.get("phase") == "eval"]
        selection = protocol.select_learning_rates(selection_rows)
        selection_record = dict(selection)
        selection_record["candidate_fits"] = [{
            "arm": fit["arm"], "lr_key": fit["lr_key"],
            "learning_rate": fit["learning_rate"], "checkpoint": fit["checkpoint"],
            "validation_mean_J": selection["validation_mean_J"][fit["arm"]][fit["lr_key"]],
        } for fit in fits]
        selection_path = _write_json(output / "selection.json", selection_record, limits)
        selection_bytes = selection_path.read_bytes()
        selection_hash = hashlib.sha256(selection_bytes).hexdigest()
        (output / "selection.sha256").write_text(selection_hash + "  selection.json\n",
                                                   encoding="ascii")

        # This is the serial stage fence: no holdout model/state exists before the bytes above.
        holdout_pair = pair_factory(protocol.HOLDOUT_MASTER)
        for arm in protocol.ARMS:
            lr_key = selection["selected_lr_key"][arm]
            current = {"stage": "holdout", "lr_key": lr_key, "arm": arm}
            fit = fit_runner(
                stage="holdout", master=protocol.HOLDOUT_MASTER,
                lr_key=lr_key, arm=arm, models=holdout_pair[arm], output=output,
                emit_episode=lambda row: emit(episode_file, rows, row),
                emit_rollout=lambda row: emit(rollout_file, rollout_rows, row),
                study_start=study_start, clock=clock)
            fits.append(fit)
        holdout_rows = [row for row in rows
                        if row.get("stage") == "holdout" and row.get("phase") == "eval"]
        primary = protocol.holdout_primary(holdout_rows, selection)
    except Exception as error:
        limits.append(f"execution: {type(error).__name__}: {error}")
    finally:
        episode_file.close()
        rollout_file.close()

    errors = _fit_errors(fits)
    limits.extend(message for message in errors if message not in limits)
    complete = (len(fits) == 8 and selection is not None and selection_hash is not None
                and primary is not None and not limits)
    summary = {
        "mode": "UAV_B_EXPLORE", "object": protocol.OBJECT, "card": CARD,
        "scientific_invocation": True, "launch_sha": launch_sha,
        "selection_master": protocol.SELECTION_MASTER,
        "holdout_master": protocol.HOLDOUT_MASTER,
        "configuration": {
            "candidate_order": list(protocol.LEARNING_RATES), "arm_order": list(protocol.ARMS),
            "learning_rates": protocol.LEARNING_RATES, "horizon": protocol.HORIZON,
            "train_episodes_per_fit": protocol.TRAIN_EPISODES,
            "eval_episodes_per_fit": protocol.EVAL_EPISODES, "chunk": 32,
            "episodes_per_rollout": 2, "epochs": 4,
            "ratio_grouping": "agent_compound", "entropy_coef": .01,
            "gradient_clip": .5, "device": "cpu", "dtype": "float32", "threads": 1,
            "fit_watchdog_seconds": FIT_CAP, "study_watchdog_seconds": STUDY_CAP,
        },
        "planned_exposure": protocol.planned_exposure(),
        "fits": fits, "completed_fit_count": len(fits), "current_on_failure": current,
        "raw_episode_file": "episodes.jsonl", "raw_episode_rows": len(rows),
        "raw_rollout_file": "rollouts.jsonl", "raw_rollout_rows": len(rollout_rows),
        "selection_file": "selection.json" if selection is not None else None,
        "selection_sha256": selection_hash, "selection": selection,
        "primary": primary,
        "cost_law": "per fit: init + 65536 training team ticks + 512 Adam calls + 8192 evaluation team ticks + checkpoint; eight fits serial",
        "study_body_wall_before_summary": clock() - study_start,
        "timing_scope": (
            "study_body_wall_before_summary excludes module imports, CLI parsing, Torch thread "
            "setup, final summary write, stdout, and process exit; fit_body_wall excludes its "
            "model-pair factory but includes environment construction, learning, evaluation, and "
            "checkpoint publication; complete command wall is measured by the GNU-time/supervisor "
            "launch envelope"
        ),
        "limits": limits,
        "status": "COMPLETE" if complete else "INCOMPLETE",
    }
    _write_json(output / "summary.json", summary, limits)
    return clean_json(summary, limits)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--selection-master", type=int, default=protocol.SELECTION_MASTER)
    parser.add_argument("--holdout-master", type=int, default=protocol.HOLDOUT_MASTER)
    args = parser.parse_args()
    if args.selection_master != protocol.SELECTION_MASTER or args.holdout_master != protocol.HOLDOUT_MASTER:
        parser.error("only the carded selection/holdout masters are accepted")
    if not re.fullmatch(r"[0-9a-f]{40}", args.launch_sha):
        parser.error("--launch-sha must be the exact 40-character lowercase Git SHA")
    torch.set_num_threads(1)
    summary = run_study(args.out, args.launch_sha)
    print(json.dumps(summary, indent=2, allow_nan=False))
    raise SystemExit(0 if summary["status"] == "COMPLETE" else 1)


if __name__ == "__main__":
    main()
