"""Two private feedback fits, scalar critic-target normalization and native J."""
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import statistics
import subprocess
import time

from ..uav_motion_prefix_b01.study import Deadline, clean_json, difference_stats, new_counts, write_summary

CARD = "docs/research/candidates/ucope/UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_SCIENCE_CARD_20260909.md"
OBJECT = "UCOPE-UAV-FEEDBACK-VALUE-NORMALIZATION-B01"
SELECTOR = "feedback_value_normalization_b01"
COMPARATOR_SOURCE = "52bf50a089d3389d9fada0b531e4f4e56e83f9b8"
LABELS = ("G_normalized", "G_raw", "H")


@dataclass
class Config:
    seed: int = 8501
    fixture: bool = False
    horizon: int = 256
    train_episodes: int = 512
    eval_episodes: int = 32
    chunk: int = 32
    arm_cap: float = 1800
    pair_cap: float = 3600

    @classmethod
    def engineering(cls):
        return cls(seed=9001, fixture=True, horizon=8, train_episodes=2, eval_episodes=2, chunk=8)


def primary_from_rows(rows, expected):
    values = {a: {r["episode"]: r["J"] for r in rows if r["phase"] == "eval" and r["arm"] == a}
              for a in LABELS}
    complete = {a: set(v) == set(range(expected)) and all(math.isfinite(x) for x in v.values())
                for a, v in values.items()}
    result = {"selected_contrast": "G_normalized_minus_G_raw",
              "complete": complete["G_normalized"] and complete["G_raw"],
              "hover_complete": complete["H"], "all_outcomes_complete": all(complete.values()),
              "J": {a: [v[e] for e in sorted(v)] for a, v in values.items()},
              "episode_ids": {a: sorted(v) for a, v in values.items()},
              "arm_means": {a: statistics.mean(v.values()) if v else None for a, v in values.items()}}
    for a, b in (("G_normalized", "G_raw"), ("G_normalized", "H"), ("G_raw", "H")):
        ids = sorted(values[a].keys() & values[b].keys())
        delta = [values[a][i] - values[b][i] for i in ids]
        result[a + "_minus_" + b] = dict(difference_stats(delta), episode_ids=ids,
            complete=complete[a] and complete[b], positive=sum(x > 0 for x in delta),
            negative=sum(x < 0 for x in delta), zero=sum(x == 0 for x in delta))
    delta = result["G_normalized_minus_G_raw"]["mean"]
    result["reading"] = ("UP" if delta > .01 else "DOWN" if delta < -.01 else "WITHIN") if result["complete"] else None
    result["distance_to_lower"] = delta + .01 if result["complete"] else None
    result["distance_to_upper"] = delta - .01 if result["complete"] else None
    return result


def run_pair(config, out, start, clock=time.monotonic, factory=None, publish=write_summary):
    import torch
    from ..uav_motion_prefix_b01.environment import SyntheticAdapter, make_real
    from ..uav_motion_prefix_b01.learner import collect_episode, optimizer_for, update
    from ..uav_motion_prefix_b01.policy import arm_copy, exposure, generator, snapshot, templates
    from .value_normalization import ValueMoments

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if factory is None:
        factory = (lambda seed: SyntheticAdapter(seed, config.horizon)) if config.fixture else make_real
    deadline = Deadline(start, config.arm_cap, config.pair_cap, clock, first_arm="G_normalized")
    rows, limits, arms = [], [], {}
    b = config.seed * 100000
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                  cwd=Path(__file__).resolve().parents[4], text=True).strip()
    summary = dict(object=OBJECT, card=CARD, card_section=7 if config.fixture else 6,
        pair=SELECTOR, mode="ENGINEERING_FIXTURE" if config.fixture else "UAV_B_EXPLORE",
        launch_sha=sha, comparator_source=COMPARATOR_SOURCE, seed=config.seed,
        configuration=asdict(config), status="INCOMPLETE", arms=arms, limits=limits,
        ratio_grouping="agent_compound", entropy_coef=0.,
        seeds=dict(initialization=b+11, train_reset_start=b+1000, eval_reset_start=b+2000,
                   raw_train_velocity=b+21, raw_train_duration=b+22,
                   normalized_train_velocity=b+31, normalized_train_duration=b+32,
                   raw_eval_velocity_start=b+3000, raw_eval_duration_start=b+4000,
                   normalized_eval_velocity_start=b+5000, normalized_eval_duration_start=b+6000),
        value_units=dict(reward="native", stored_baseline="native_return", advantage="standardized_raw_return",
                         normalized_critic="normalized_return", mean="native_return",
                         M2="native_return_squared_sum", scale="native_return"))
    files = {name: (out / (name + ".jsonl")).open("w", encoding="utf-8")
             for name in ("episodes", "rollouts")}

    def emit(name, row):
        if name == "episodes":
            rows.append(row)
        files[name].write(json.dumps(clean_json(row, limits), allow_nan=False) + "\n")
        files[name].flush()

    actor = critic = initial = info = moments = None
    try:
        deadline.check()
        common = templates(config.seed)
        copies = [arm_copy(common, treatment=False) for _ in range(2)]
        for index, arm in enumerate(LABELS[:2]):
            if index:
                deadline.start_g(arm)
            counts = new_counts()
            info = dict(counts=counts, fit_complete=False, complete=False, learning_rate=.0003,
                        value_moments=None, elapsed_wall=None)
            arms[arm] = info
            actor, critic = copies[index]
            initial = snapshot(actor, critic)
            info["trainable_parameters"] = sum(p.numel() for model in (actor, critic) for p in model.parameters())
            moments = ValueMoments() if index == 0 else None
            optimizer = optimizer_for(actor, critic)
            vrng, drng = generator(b+(31 if index == 0 else 21)), generator(b+(32 if index == 0 else 22))
            deadline.check()
            env = factory(b+1000)
            counts["constructors"] += 1
            counts["constructor_resets"] += 1

            def episode(phase, e, label, model, value_model, velocity, duration):
                return collect_episode(env, model, value_model, config.horizon,
                    b+(1000 if phase == "train" else 2000)+e, velocity, duration,
                    dict(pair_master=config.seed, arm=label, phase=phase, episode=e),
                    deadline.check, counts, lambda row: emit("episodes", row), lambda row: None, limits,
                    real=not config.fixture, ratio_grouping="agent_compound", value_moments=moments)

            for roll in range(config.train_episodes // 2):
                before = counts.copy()
                episodes = [episode("train", 2*roll+i, arm, actor, critic, vrng, drng) for i in range(2)]
                epochs = update(actor, critic, optimizer, episodes, config.chunk, deadline.check, counts,
                                ratio_grouping="agent_compound", entropy_coef=0., value_moments=moments)
                counts["rollouts"] += 1
                emit("rollouts", dict(arm=arm, pair_master=config.seed, rollout=roll, steps=2*config.horizon,
                    epochs=epochs, **{key: counts[key]-before[key] for key in
                                     ("optimizer_steps", "velocity_decisions", "duration_decisions", "d4")}))
            info["fit_complete"] = True
            info["training_counts"] = counts.copy()
            info["exposure"] = exposure(initial, actor, critic)
            info["value_moments"] = moments.state() if moments else None
            deadline.check()
            torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(), configuration=asdict(config),
                            arm=arm, value_moments=moments.checkpoint() if moments else None), out / f"final_{arm}.pt")
            final_fit = snapshot(actor, critic)
            before = counts.copy()
            for e in range(config.eval_episodes):
                episode("eval", e, arm, actor, critic, generator(b+(5000 if index == 0 else 3000)+e),
                        generator(b+(6000 if index == 0 else 4000)+e))
            info["evaluation_counts"] = {key: counts[key]-before[key] for key in counts}
            info["evaluation_parameter_exposure"] = exposure(final_fit, actor, critic)
            info["evaluation_value_moments"] = moments.state() if moments else None
            info["complete"] = True
            if index:
                before = counts.copy()
                try:
                    for e in range(config.eval_episodes):
                        episode("eval", e, "H", None, None, None, None)
                finally:
                    info["hover_counts"] = {key: counts[key]-before[key] for key in counts}
            info["elapsed_wall"] = deadline.check()-deadline.arm_start
    except Exception as error:
        limits.append(f"execution: {type(error).__name__}: {error}")
        if info is not None:
            info["value_moments"] = moments.state() if moments else None
            if initial is not None:
                info["exposure"] = exposure(initial, actor, critic)
            info["elapsed_wall"] = clock()-deadline.arm_start
    finally:
        for stream in files.values():
            stream.close()
    summary["counts"] = {key: sum(a["counts"][key] for a in arms.values()) for key in new_counts()}
    summary["counts"]["partial_episode_steps"] = summary["counts"]["team_steps"]-summary["counts"]["completed_episode_steps"]
    summary["scientific_uav_calls"] = summary["counts"]["scientific_uav_calls"]
    summary["primary"] = primary_from_rows(rows, config.eval_episodes)
    summary["status"] = ("COMPLETE" if len(arms) == 2 and all(a["complete"] for a in arms.values())
        and summary["primary"]["all_outcomes_complete"] and not limits else
        "PRIMARY_COMPLETE_WITH_LIMITS" if summary["primary"]["complete"] else "INCOMPLETE")

    def observe_time():
        now = clock()
        summary["pair_elapsed_wall"] = now-start
        if deadline.arm in arms:
            arms[deadline.arm]["elapsed_wall"] = now-deadline.arm_start
        try:
            deadline.check()
        except TimeoutError as error:
            if str(error) not in limits:
                limits.append(str(error))
            summary["status"] = "CAP_BREACH"
        summary["cap_breach"] = deadline.breach is not None

    observe_time()
    try:
        publish(out / "summary.json", summary)
    except Exception as error:
        limits.append(f"pair publication: {type(error).__name__}: {error}")
        summary["status"] = "PUBLICATION_FAILED"
    observe_time()
    write_summary(out / "summary.json", summary)
    previous_breach = summary["cap_breach"]
    observe_time()
    if summary["cap_breach"] and not previous_breach:
        write_summary(out / "summary.json", summary)
    return clean_json(summary, limits)
