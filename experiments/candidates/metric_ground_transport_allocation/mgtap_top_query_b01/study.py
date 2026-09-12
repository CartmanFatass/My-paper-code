"""One fresh TOP/DENSE fit pair using the accepted native learner unchanged."""

import json
from pathlib import Path
import subprocess
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    collect_episode, optimizer_for, update,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.ucope.uav_motion_prefix_b01.study import (
    Deadline, clean_json, new_counts, write_summary,
)
from experiments.candidates.metric_ground_transport_allocation.mgtap_top_query_b01.pair import (
    build_top_pair, primary, publish_summary,
)
from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import (
    TOP, DENSE, geometry_snapshot as snapshot, geometry_exposure as exposure,
)


MASTER = 8221
CARD = "docs/research/candidates/metric_ground_transport_allocation/MGTAP_TOP_QUERY_B01_SCIENCE_CARD_20260912.md"
SOURCE_SHA = "2f6f6180e2dea9978e235e11e41446ef78a1bb7e"
HORIZON, TRAIN_EPISODES, EVAL_EPISODES = 256, 512, 32
ARM_CAP, PAIR_CAP = 450.0, 900.0


def binding_errors(rows, arms, seed):
    """Check this fit/endpoint's data binding beyond the accepted score reducer."""
    errors = []
    base = 100000 * seed
    for arm in (TOP, DENSE):
        info = arms.get(arm, {})
        if not info.get("fit_complete") or not info.get("complete"):
            errors.append(f"{arm}: unfinished fit or final panel")
        counts = info.get("counts", {})
        expected = dict(train_episodes=512, train_team_steps=131072,
                        eval_episodes=32, eval_team_steps=8192,
                        team_steps=139264, optimizer_steps=1024, rollouts=256)
        if any(counts.get(key) != value for key, value in expected.items()):
            errors.append(f"{arm}: learner/endpoint counts differ from card")
        for phase, size, reset_offset, duration_offset in (
                ("train", 512, 1000, 4000), ("eval", 32, 2000, 5000)):
            panel = [row for row in rows if row.get("arm") == arm and row.get("phase") == phase]
            if [row.get("episode") for row in panel] != list(range(size)):
                errors.append(f"{arm}/{phase}: incomplete or unordered episode indices")
            for row in panel:
                e = row.get("episode")
                if type(e) is not int:
                    errors.append(f"{arm}/{phase}: noninteger episode")
                    continue
                velocity_seed = base + (21 if phase == "train" else 3000 + e)
                if (row.get("pair_master") != seed or row.get("steps") != 256
                        or row.get("reset_seed") != base + reset_offset + e
                        or row.get("velocity_seed") != velocity_seed
                        or row.get("duration_seed") != base + duration_offset + e):
                    errors.append(f"{arm}/{phase}/{e}: reset/action binding mismatch")
    return errors


def run_pair(seed, output, start, clock=time.monotonic):
    if seed != MASTER:
        raise ValueError(f"the sole allocated master is {MASTER}")
    deadline = Deadline(start, ARM_CAP, PAIR_CAP, clock, first_arm=TOP)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    launch_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[4], text=True).strip()
    rows, limits, arms = [], [], {}
    pair_factory_calls, model_constructions = 0, None
    arm_info = initial = actor = critic = None
    streams = {name: (output / f"{name}.jsonl").open("w", encoding="utf-8")
               for name in ("episodes", "rollouts")}

    def emit_episode(row):
        rows.append(row)
        streams["episodes"].write(json.dumps(clean_json(row, limits), allow_nan=False) + "\n")
        streams["episodes"].flush()

    def emit_diagnostic(_row):
        return None

    try:
        deadline.check()
        pair_factory_calls += 1
        pair = build_top_pair(seed)
        model_constructions = 6  # successful factory: two pairs plus its common template pair
        deadline.check()
        base = 100000 * seed
        for kind in (TOP, DENSE):
            if kind == DENSE:
                boundary = deadline.start_g(DENSE)
                arms[TOP]["elapsed_wall"] = boundary - start
            counts = new_counts(False)
            arm_info = {"fit_complete": False, "complete": False, "counts": counts}
            arms[kind] = arm_info
            initial = None
            actor, critic = pair[kind]
            env = make_real(base + 1000)
            counts["constructors"] += 1
            counts["constructor_resets"] += 1
            deadline.check()
            initial = snapshot(actor, critic)
            optimizer = optimizer_for(actor, critic)
            train_velocity = generator(base + 21)
            for rollout_index in range(256):
                before = counts["optimizer_steps"]
                episodes = []
                for offset in (0, 1):
                    e = 2 * rollout_index + offset
                    episodes.append(collect_episode(
                        env, actor, critic, HORIZON, base + 1000 + e,
                        train_velocity, generator(base + 4000 + e),
                        {"pair_master": seed, "arm": kind, "phase": "train", "episode": e,
                         "velocity_seed": base + 21, "duration_seed": base + 4000 + e},
                        deadline.check, counts, emit_episode, emit_diagnostic, limits,
                        real=True, diagnostics=False, ratio_grouping="agent_compound"))
                records = update(actor, critic, optimizer, episodes, 32, deadline.check, counts,
                                 ratio_grouping="agent_compound", entropy_coef=0.01)
                streams["rollouts"].write(json.dumps({
                    "pair_master": seed, "arm": kind, "rollout": rollout_index,
                    "episodes": 2, "steps": 512, "epochs": records,
                    "optimizer_steps": counts["optimizer_steps"] - before,
                }, allow_nan=False) + "\n")
                streams["rollouts"].flush()
                counts["rollouts"] += 1
                deadline.check()
            arm_info.update(fit_complete=True, training_counts=counts.copy(),
                            exposure=exposure(initial, actor, critic))
            torch.save({"actor": actor.state_dict(), "critic": critic.state_dict(),
                        "arm": kind, "seed": seed}, output / f"final_{kind}.pt")
            for e in range(EVAL_EPISODES):
                collect_episode(
                    env, actor, critic, HORIZON, base + 2000 + e,
                    generator(base + 3000 + e), generator(base + 5000 + e),
                    {"pair_master": seed, "arm": kind, "phase": "eval", "episode": e,
                     "velocity_seed": base + 3000 + e, "duration_seed": base + 5000 + e},
                    deadline.check, counts, emit_episode, emit_diagnostic, limits,
                    real=True, diagnostics=False, ratio_grouping="agent_compound")
            arm_info["complete"] = counts["eval_episodes"] == EVAL_EPISODES
            arm_info["elapsed_wall"] = deadline.check() - deadline.arm_start
    except Exception as error:
        limits.append(f"execution: {type(error).__name__}: {error}")
        if arm_info is not None and initial is not None and "exposure" not in arm_info:
            try:
                arm_info["exposure"] = exposure(initial, actor, critic)
            except Exception as movement_error:
                limits.append(f"partial movement: {type(movement_error).__name__}: {movement_error}")
    finally:
        for stream in streams.values():
            stream.close()
    errors = binding_errors(rows, arms, seed)
    measured = primary(rows)
    if errors:
        measured.update(complete=False, reading="INCOMPLETE")
        measured["TOP_minus_DENSE"].update(complete=False, mean=None, conditional_se=None)
    summary = {
        "mode": "UAV_B_EXPLORE", "object": "MGTAP-TOP-QUERY-B01",
        "card": CARD, "source_base_sha": SOURCE_SHA, "launch_sha": launch_sha, "seed": seed,
        "scientific_invocation": True, "pair_factory_calls": pair_factory_calls,
        "top_level_model_constructions": model_constructions,
        "configuration": {"horizon": HORIZON, "train_episodes": TRAIN_EPISODES,
                          "eval_episodes": EVAL_EPISODES, "chunk": 32,
                          "ratio_grouping": "agent_compound", "entropy_coef": .01,
                          "velocity_mode": "sampled", "dtype": "float32", "device": "cpu",
                          "threads": 1, "arm_cap": ARM_CAP, "pair_cap": PAIR_CAP},
        "world_law": "make_real: reset RandomState(base+2000+e) rebuilds UAV/user positions; free_space, no shadowing",
        "arms": arms, "rows": rows, "primary": measured, "binding_errors": errors,
        "cost_law": "per arm: init + 131072 collection steps + 1024 Adam/recurrent replay + 8192 eval steps + checkpoint/publication/exit",
        "actor_rows_per_fit": 3317760,
        "time_attribution": "TOP receives admission/startup and all template construction through its final panel; DENSE receives the remainder including pair reduction/publication/exit; outer native wall closes the accounting",
        "limits": limits, "status": "COMPLETE" if measured["complete"] and not limits else "INCOMPLETE",
    }
    summary["counts"] = {key: sum(info["counts"][key] for info in arms.values()) for key in new_counts(False)}
    summary["counts"]["partial_episode_steps"] = (summary["counts"]["team_steps"]
                                                   - summary["counts"]["completed_episode_steps"])

    def observe_time():
        now = clock()
        summary["pair_elapsed_wall"] = now - start
        if deadline.arm in arms:
            arms[deadline.arm]["elapsed_wall"] = now - deadline.arm_start
        try:
            deadline.check()
        except TimeoutError as error:
            if str(error) not in limits:
                limits.append(str(error))
            summary["status"] = "CAP_BREACH"
        summary["cap_breach"] = deadline.breach is not None

    observe_time()
    try:
        publish_summary(output / "summary.json", clean_json(summary, limits))
    except Exception as error:
        limits.append(f"publication: {type(error).__name__}: {error}")
        summary["status"] = "PUBLICATION_FAILED"
    observe_time()
    write_summary(output / "summary.json", summary)
    previous_breach = summary["cap_breach"]
    observe_time()
    if summary["cap_breach"] and not previous_breach:
        write_summary(output / "summary.json", summary)
    return summary
