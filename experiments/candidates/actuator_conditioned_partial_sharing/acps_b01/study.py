"""One whole arm per invocation; complete fixed paired endpoint at collection."""
import json
import math
from pathlib import Path
import statistics
import subprocess
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    collect_episode, optimizer_for, update,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.ucope.uav_motion_prefix_b01.study import Deadline, new_counts, write_summary
from .environment import CapabilityAdapter
from .policy import build_arm, movement, parameter_snapshot


MASTER, HORIZON, TRAIN_EPISODES, EVAL_EPISODES = 9101, 256, 512, 32
CARD = "docs/research/candidates/actuator_conditioned_partial_sharing/ACPS_B01_SCIENCE_CARD_20260912.md"


def primary(summaries):
    """The sole final panel, never available-case selection or seed pooling."""
    arms, errors = {}, []
    expected_counts = dict(train_episodes=512, train_team_steps=131072,
                           eval_episodes=32, eval_team_steps=8192,
                           optimizer_steps=1024, rollouts=256)
    for summary in summaries:
        arm = summary.get("arm")
        if arm not in ("ACPS", "SHARED") or arm in arms:
            errors.append("unexpected or duplicate arm")
            continue
        values = [row for row in summary.get("rows", []) if row.get("phase") == "eval"]
        if (summary.get("seed") != MASTER or not summary.get("complete")
                or any(summary.get("counts", {}).get(k) != v for k, v in expected_counts.items())
                or [row.get("episode") for row in values] != list(range(32))):
            errors.append(f"{arm}: incomplete fit or ordered final panel")
        for e, row in enumerate(values):
            if (row.get("reset_seed") != 100000 * MASTER + 2000 + e
                    or row.get("steps") != 256 or row.get("arm") != arm
                    or row.get("pair_master") != MASTER
                    or not isinstance(row.get("J"), (int, float))
                    or not math.isfinite(row["J"])):
                errors.append(f"{arm}/{e}: final binding or primary invalid")
        arms[arm] = [row.get("J") for row in values]
    if set(arms) != {"ACPS", "SHARED"}:
        errors.append("missing arm")
    if errors:
        return dict(complete=False, reading="INCOMPLETE", errors=errors, J=arms)
    differences = [a - b for a, b in zip(arms["ACPS"], arms["SHARED"])]
    mean = statistics.mean(differences)
    sd = statistics.stdev(differences)
    return dict(complete=True, J=arms, differences=differences, mean=mean,
                conditional_sd=sd, conditional_se=sd / math.sqrt(32),
                positive=sum(x > 0 for x in differences), adverse=sum(x < 0 for x in differences),
                reading="ABOVE_MEI" if mean > .01 else "ADVERSE" if mean < -.01 else "INSIDE_MEI")


def run_arm(arm, seed, output, start):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    deadline = Deadline(start, 450., 450., first_arm=arm)
    counts, rows, limits = new_counts(False), [], []
    fit_complete = complete = False
    initial = actor = critic = None
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    base = 100000 * seed
    with (output / "episodes.jsonl").open("w", encoding="utf-8") as episodes_file, \
            (output / "rollouts.jsonl").open("w", encoding="utf-8") as rollout_file:
        def emit(row):
            row["capabilities"] = env.env.capabilities.tolist()
            rows.append(row)
            episodes_file.write(json.dumps(row, allow_nan=False) + "\n")
            episodes_file.flush()

        try:
            deadline.check()
            actor, critic = build_arm(seed, arm)
            initial = parameter_snapshot(actor, critic)
            exposure_line = dict(parameters=initial["total"].numel(),
                                 initialization_norm=float(initial["total"].norm()),
                                 adam_learning_rate=3e-4, planned_adam_calls=1024,
                                 nominal_lr_step_sum=3e-4 * 1024,
                                 note="Nonzero permitted optimizer exposure; actual displacement reported after learning")
            print(json.dumps({"exposure_line": exposure_line}), flush=True)
            optimizer = optimizer_for(actor, critic)
            env = CapabilityAdapter(base + 1000)
            counts["constructors"] += 1
            counts["constructor_resets"] += 1
            velocity = generator(base + 21)
            for r in range(256):
                episodes = []
                for e in (2 * r, 2 * r + 1):
                    episodes.append(collect_episode(
                        env, actor, critic, HORIZON, base + 1000 + e,
                        velocity, generator(base + 4000 + e),
                        dict(pair_master=seed, arm=arm, phase="train", episode=e,
                             velocity_seed=base + 21, duration_seed=base + 4000 + e),
                        deadline.check, counts, emit, lambda row: None, limits,
                        real=True, diagnostics=False, ratio_grouping="agent_compound"))
                epochs = update(actor, critic, optimizer, episodes, 32, deadline.check, counts,
                                ratio_grouping="agent_compound", entropy_coef=.01)
                rollout_file.write(json.dumps(dict(rollout=r, epochs=epochs), allow_nan=False) + "\n")
                rollout_file.flush()
                counts["rollouts"] += 1
            fit_complete = True
            torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(), arm=arm,
                            seed=seed, launch_sha=source), output / "final.pt")
            actor.eval()
            critic.eval()
            for e in range(EVAL_EPISODES):
                collect_episode(
                    env, actor, critic, HORIZON, base + 2000 + e,
                    generator(base + 3000 + e), generator(base + 5000 + e),
                    dict(pair_master=seed, arm=arm, phase="eval", episode=e,
                         velocity_seed=base + 3000 + e, duration_seed=base + 5000 + e),
                    deadline.check, counts, emit, lambda row: None, limits,
                    real=True, diagnostics=False, ratio_grouping="agent_compound")
            complete = True
        except Exception as error:
            limits.append(f"{type(error).__name__}: {error}")
    summary = dict(object="ACPS-B01", card=CARD, arm=arm, seed=seed, launch_sha=source,
                   scientific_invocation=True, fit_complete=fit_complete, complete=complete,
                   counts=counts, rows=rows, limits=limits,
                   configuration=dict(horizon=256, train_episodes=512, final_episodes=32,
                                      dtype="float32", device="cpu", threads=1, arm_cap=450,
                                      actor_input=118, ratio_grouping="agent_compound", entropy_coef=.01),
                   cost_law="admission/import/init + 131072 collection + 1024 Adam/four replay passes + 8192 final + checkpoint/publication/readback/exit",
                   top_level_model_constructions=2 if actor is not None else 0,
                   initial_exposure_line=exposure_line if initial is not None else None,
                   exposure=movement(initial, actor, critic) if initial is not None else None,
                   elapsed_wall=time.monotonic() - start)
    summary["status"] = "COMPLETE" if complete and not limits else "INCOMPLETE"
    write_summary(output / "summary.json", summary)
    # Read the primary consumer's actual serialized endpoint, without re-evaluation.
    published = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    if published["complete"] != complete or published["counts"] != counts:
        raise RuntimeError("summary publication differs from collected endpoint")
    try:
        deadline.check()
    except TimeoutError as error:
        summary["status"] = "CAP_BREACH"
        if str(error) not in limits:
            limits.append(str(error))
    summary["elapsed_wall"] = time.monotonic() - start
    write_summary(output / "summary.json", summary)
    return summary
