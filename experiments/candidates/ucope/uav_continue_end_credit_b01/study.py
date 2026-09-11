"""One continuous L/F pair, final-only sampled native return comparison."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import statistics
import subprocess
import time
import traceback

from ..uav_motion_prefix_b01.study import Deadline, difference_stats, new_counts, write_summary

CARD = "docs/research/candidates/ucope/UCOPE_UAV_CONTINUE_END_CREDIT_B01_8801_SCIENCE_CARD_20260911.md"
OBJECT = "UCOPE-UAV-CONTINUE-END-CREDIT-B01"
COMPARATOR_SOURCE = "c40a4cd66cacc892d13afd9b277407b6505b8742"


@dataclass
class Config:
    seed: int = 8801
    fixture: bool = False
    horizon: int = 256
    train_episodes: int = 2048
    eval_episodes: int = 64
    chunk: int = 32
    l_cap: float = 1800
    f_cap: float = 1200
    pair_cap: float = 3000


def primary_from_rows(rows, expected):
    values = {arm: {r["episode"]: r["J"] for r in rows
                    if r["arm"] == arm and r["phase"] == "eval"} for arm in ("L", "F")}
    ids = sorted(values["L"].keys() & values["F"].keys())
    differences = [values["L"][e] - values["F"][e] for e in ids]
    result = dict(difference_stats(differences), complete=all(set(v) == set(range(expected))
        for v in values.values()), episode_ids=ids, J=values, selected_contrast="L_minus_F",
        means={a: statistics.mean(v.values()) if v else None for a, v in values.items()},
        positive=sum(x > 0 for x in differences), negative=sum(x < 0 for x in differences),
        zero=sum(x == 0 for x in differences))
    delta = result["mean"]
    result["reading"] = ("UP" if delta > .01 else "DOWN" if delta < -.01 else "WITHIN") if result["complete"] else None
    return result


def run_pair(config, out, start, clock=time.monotonic, factory=None, publish=write_summary):
    import torch
    from ..uav_motion_prefix_b01 import learner, policy
    from ..uav_motion_prefix_b01.environment import SyntheticAdapter, make_real
    from . import credit

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if factory is None:
        factory = (lambda seed: SyntheticAdapter(seed, config.horizon)) if config.fixture else make_real
    deadline = Deadline(start, config.l_cap, config.pair_cap, clock, first_arm="L")
    rows, arms, limits = [], {}, []
    b = 100000 * config.seed
    summary = dict(object=OBJECT, card=CARD, seed=config.seed, configuration=asdict(config),
        launch_sha=subprocess.check_output(["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[4], text=True).strip(),
        comparator_source=COMPARATOR_SOURCE, mode="ENGINEERING_FIXTURE" if config.fixture else "UAV_B_EXPLORE",
        status="INCOMPLETE", arms=arms, limits=limits,
        seeds=dict(initialization=b+11, duration_head=b+12, residual=b+13,
            train_reset_start=b+10000, eval_reset_start=b+20000,
            L_train_velocity=b+41, L_train_duration=b+42, F_train_velocity=b+31, F_train_duration=b+32,
            L_eval_velocity_start=b+72000, L_eval_duration_start=b+82000,
            F_eval_velocity_start=b+32000, F_eval_duration_start=b+42000))
    streams = {name: (out / f"{name}.jsonl").open("w", encoding="utf-8") for name in ("episodes", "rollouts")}

    def emit(name, row):
        if name == "episodes":
            rows.append(row)
        streams[name].write(json.dumps(row, allow_nan=False) + "\n")
        streams[name].flush()

    try:
        deadline.check()
        common = policy.templates(config.seed)
        for arm in ("L", "F"):
            if arm == "F":
                now = deadline.start_g("F")
                arms["L"]["elapsed_wall"] = now-start
                deadline.arm_cap = config.f_cap
            counts = new_counts(renewal=True, short=True)
            counts["duration_credit_rows"] = 0
            info = dict(counts=counts, complete=False, fit_complete=False)
            arms[arm] = info
            actor, critic = policy.arm_copy(common, True, duration_head_seed=b+12, freeze_duration=arm == "F")
            residual = credit.residual_baseline(b+13) if arm == "L" else None
            initial = credit.model_snapshot(actor, critic, residual)
            models = (actor, critic, residual) if residual is not None else (actor, critic)
            info["trainable_parameters"] = sum(p.numel() for model in models for p in model.parameters() if p.requires_grad)
            optimizer = credit.optimizer_for(actor, critic, residual) if residual is not None else learner.optimizer_for(actor, critic)
            train_offset = 40 if arm == "L" else 30
            velocity, duration = policy.generator(b+train_offset+1), policy.generator(b+train_offset+2)
            deadline.check()
            env = factory(b+10000)
            counts["constructors"] += 1
            counts["constructor_resets"] += 1
            try:
                # Both arms share the established primitive collector. Only L training
                # requests detached baseline records; evaluation never calls the residual.
                def episode(phase, e, vrng, drng):
                    return learner.collect_episode(env, actor, critic, config.horizon,
                        b+(10000 if phase == "train" else 20000)+e, vrng, drng,
                        dict(pair_master=config.seed, arm=arm, phase=phase, episode=e,
                             checkpoint=config.train_episodes if phase == "eval" else None),
                        deadline.check, counts, lambda row: emit("episodes", row), lambda row: None, limits,
                        real=not config.fixture, ratio_grouping="agent_compound", renewal=True,
                        duration_support=(1, 2), credit_baseline=residual if phase == "train" else None)

                for roll in range(config.train_episodes // 2):
                    episodes = [episode("train", 2*roll+i, velocity, duration) for i in range(2)]
                    if residual is not None:
                        epochs = credit.update(actor, critic, residual, optimizer, episodes,
                                               config.chunk, deadline.check, counts)
                    else:
                        epochs = learner.update(actor, critic, optimizer, episodes, config.chunk,
                                                deadline.check, counts, ratio_grouping="agent_compound", entropy_coef=0.)
                    counts["rollouts"] += 1
                    emit("rollouts", dict(arm=arm, pair_master=config.seed, rollout=roll,
                        training_episodes=2*(roll+1), optimizer_steps=counts["optimizer_steps"], epochs=epochs))
                info["fit_complete"] = True
                info["exposure"] = credit.movement(initial, actor, critic, residual)
                evaluation_initial = credit.model_snapshot(actor, critic, residual)
                eval_offset = 72000 if arm == "L" else 32000
                for e in range(config.eval_episodes):
                    episode("eval", e, policy.generator(b+eval_offset+e), policy.generator(b+eval_offset+10000+e))
                info["evaluation_parameter_exposure"] = credit.movement(evaluation_initial, actor, critic, residual)
                checkpoint = dict(actor=actor.state_dict(), critic=critic.state_dict(),
                    configuration=asdict(config), counts=counts.copy(), arm=arm, value_moments=None)
                if residual is not None:
                    checkpoint["residual"] = residual.state_dict()
                deadline.check()
                torch.save(checkpoint, out / f"final_{arm}.pt")
                info["complete"] = True
                write_summary(out / f"arm_{arm}.json", info)
                deadline.check()
            finally:
                info["exposure"] = credit.movement(initial, actor, critic, residual)
                info["elapsed_wall"] = clock()-deadline.arm_start
                write_summary(out / f"arm_{arm}.json", info)
    except Exception as error:
        traceback.print_exc()
        limits.append(f"execution: {type(error).__name__}: {error}")
    finally:
        for stream in streams.values():
            stream.close()
    keys = set().union(*(a["counts"] for a in arms.values()))
    summary["counts"] = {key: sum(a["counts"].get(key, 0) for a in arms.values()) for key in sorted(keys)}
    summary["primary"] = primary_from_rows(rows, config.eval_episodes)
    summary["status"] = "COMPLETE" if len(arms) == 2 and all(a["complete"] for a in arms.values()) and summary["primary"]["complete"] and not limits else "INCOMPLETE"

    def record_time():
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

    record_time()
    try:
        publish(out / "summary.json", summary)
    except Exception as error:
        limits.append(f"publication: {type(error).__name__}: {error}")
        summary["status"] = "PUBLICATION_FAILED"
    record_time()
    write_summary(out / "summary.json", summary)
    return summary
