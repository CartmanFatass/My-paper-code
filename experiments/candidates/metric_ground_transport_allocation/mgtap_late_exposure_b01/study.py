"""Train both fixed1e-4 arms to512, observe256/512, and read final512 only."""

import argparse
import json
from pathlib import Path
import time

import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_late_exposure_b01 import protocol as p
from experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01 import study as base

CARD = "docs/research/candidates/metric_ground_transport_allocation/MGTAP_LATE_EXPOSURE_B01_SCIENCE_CARD_20260914.md"


def native_fit(arm, models, output, emit_episode, emit_rollout, study_start,
               emit_partial, clock=time.monotonic):
    actor, critic = models
    counts, limits, endpoints = base.new_counts(False), [], []
    start, phase, initial = clock(), "initialization", None
    deadline = base.StudyDeadline(study_start, start, clock)
    try:
        # Training and evaluation own distinct environments; all episode state is reset.
        train_env, eval_env = (base.make_real(100000 * p.MASTER + offset) for offset in (1000, 2000))
        counts["constructors"] += 2
        counts["constructor_resets"] += 2
        initial = base.geometry_snapshot(actor, critic)
        optimizer = base._optimizer(actor, critic, p.LEARNING_RATE)
        train_velocity = base.generator(100000 * p.MASTER + 21)

        def episode(kind, index, endpoint=None):
            address = p.randomization(kind, index)
            metadata = {"object": p.OBJECT, "pair_master": p.MASTER, "arm": arm,
                        "learning_rate": p.LEARNING_RATE, "phase": kind, "episode": index,
                        "velocity_seed": address["velocity_seed"], "duration_seed": address["duration_seed"]}
            if endpoint is not None:
                metadata["train_endpoint"] = endpoint
            return base.collect_episode(
                train_env if kind == "train" else eval_env, actor, critic, p.HORIZON,
                address["reset_seed"], train_velocity if kind == "train" else base.generator(address["velocity_seed"]),
                base.generator(address["duration_seed"]), metadata, deadline.check, counts,
                emit_episode, lambda _row: None, limits, real=True, diagnostics=False,
                ratio_grouping="agent_compound")

        for rollout in range(p.TRAIN_EPISODES // p.EPISODES_PER_ROLLOUT):
            phase = "training"
            episodes = [episode("train", 2 * rollout + offset) for offset in range(2)]
            before = counts["optimizer_steps"]
            records = base.update(actor, critic, optimizer, episodes, 32, deadline.check, counts,
                                  ratio_grouping="agent_compound", entropy_coef=.01)
            counts["rollouts"] += 1
            completed = 2 * (rollout + 1)
            emit_rollout({"object": p.OBJECT, "pair_master": p.MASTER, "arm": arm,
                          "learning_rate": p.LEARNING_RATE, "rollout": rollout,
                          "train_episodes_completed": completed, "episodes": 2, "steps": 512,
                          "epochs": records, "optimizer_steps": counts["optimizer_steps"] - before})
            if completed in p.ENDPOINTS:
                phase = f"evaluation{completed}"
                for index in range(p.EVAL_EPISODES):
                    episode("eval", index, completed)
                phase = f"checkpoint{completed}"
                checkpoint = output / f"{arm}_{completed}.pt"
                torch.save({"object": p.OBJECT, "pair_master": p.MASTER, "arm": arm,
                            "train_endpoint": completed, "learning_rate": p.LEARNING_RATE,
                            "actor": actor.state_dict(), "critic": critic.state_dict(),
                            "optimizer": optimizer.state_dict()}, checkpoint)
                endpoints.append({"train_endpoint": completed, "checkpoint": checkpoint.name,
                                  "counts": counts.copy(), "exposure": base.geometry_exposure(initial, actor, critic)})
            deadline.check()
        return {"arm": arm, "fit_complete": True, "counts": counts,
                "endpoints": endpoints, "exposure": base.geometry_exposure(initial, actor, critic),
                "fit_body_wall": clock() - start, "limits": limits}
    except Exception as error:
        exposure, exposure_error = None, None
        if initial is not None:
            try:
                exposure = base.geometry_exposure(initial, actor, critic)
            except Exception as diagnostic_error:
                exposure_error = f"{type(diagnostic_error).__name__}: {diagnostic_error}"
        emit_partial({"arm": arm, "fit_complete": False, "phase": phase,
                      "counts": counts.copy(), "endpoints": endpoints,
                      "exposure": exposure, "exposure_error": exposure_error,
                      "counts_scope": "observed counters; an interrupted primitive may include unobserved work",
                      "fit_body_wall": clock() - start,
                      "limits": limits + [f"{type(error).__name__}: {error}"]})
        raise


def run_study(output, launch_sha, *, pair_factory=base.build_cond_pair,
              fit_runner=native_fit, clock=time.monotonic):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    start = clock()
    rows, rollouts, fits, partial_fits, limits = [], [], [], [], []
    primary, current = None, None
    with (output / "episodes.jsonl").open("w", encoding="utf-8") as ef, \
            (output / "rollouts.jsonl").open("w", encoding="utf-8") as rf:
        def emit(stream, collection, row):
            collection.append(row)
            stream.write(json.dumps(base.clean_json(row, limits), allow_nan=False) + "\n")
            stream.flush()
        try:
            pair = pair_factory(p.MASTER)
            for arm in p.ARMS:
                current = arm
                fits.append(fit_runner(arm, pair[arm], output,
                                      lambda row: emit(ef, rows, row), lambda row: emit(rf, rollouts, row),
                                      start, partial_fits.append, clock))
            primary = p.primary(rows)
        except Exception as error:
            limits.append(f"execution: {type(error).__name__}: {error}")
    expected = {"train_episodes": 512, "eval_episodes": 64,
                "train_team_steps": 131072, "eval_team_steps": 16384,
                "team_steps": 147456, "optimizer_steps": 1024, "rollouts": 256}
    for fit in fits:
        if (not fit.get("fit_complete") or any(fit.get("counts", {}).get(k) != v for k, v in expected.items())
                or [ep.get("train_endpoint") for ep in fit.get("endpoints", [])] != list(p.ENDPOINTS)):
            limits.append(f"{fit['arm']}: incomplete fit/counts/endpoints")
        limits.extend(f"{fit['arm']}: {item}" for item in fit.get("limits", []))
    summary = base.clean_json({
        "object": p.OBJECT, "card": CARD, "mode": "UAV_B_EXPLORE",
        "scientific_invocation": True, "launch_sha": launch_sha, "master": p.MASTER,
        "configuration": {"arm_order": list(p.ARMS), "learning_rate": p.LEARNING_RATE,
                          "horizon": p.HORIZON, "train_episodes_per_fit": p.TRAIN_EPISODES,
                          "evaluation_endpoints": list(p.ENDPOINTS), "eval_episodes_per_endpoint": p.EVAL_EPISODES,
                          "chunk": 32, "epochs": 4, "episodes_per_rollout": 2,
                          "ratio_grouping": "agent_compound", "entropy_coef": .01,
                          "gradient_clip": .5, "device": "cpu", "dtype": "float32", "threads": 1},
        "selection_history": "8251 selected1e-4;8252 positive/8253 adverse observed before this fixed512 proposal; no new selection",
        "planned_exposure": p.planned_exposure(), "fits": fits, "partial_fits": partial_fits,
        "completed_fit_count": len(fits), "raw_episode_rows": len(rows), "raw_rollout_rows": len(rollouts),
        "primary": primary, "current_on_failure": current,
        "cost_law": "two serial fits; each init +131072 training ticks +1024 Adam +two8192-tick evaluations +two checkpoints",
        "study_body_wall_before_summary": clock() - start,
        "timing_scope": "body excludes imports, CLI/thread setup, final summary write/exit; GNU time covers whole command",
    }, limits)
    complete = len(fits) == 2 and primary is not None and not limits
    summary.update(limits=limits, status="COMPLETE" if complete else "INCOMPLETE",
                   current_on_failure=None if complete else current)
    base._write_json(output / "summary.json", summary, limits)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--master", type=int, default=p.MASTER)
    args = parser.parse_args()
    if args.master != p.MASTER:
        parser.error("only prospective master8254 is selected")
    torch.set_num_threads(1)
    summary = run_study(args.out, args.launch_sha)
    print(json.dumps(summary, indent=2, allow_nan=False))
    raise SystemExit(0 if summary["status"] == "COMPLETE" else 1)


if __name__ == "__main__":
    main()
