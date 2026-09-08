"""One matched GATED-V/MLP-V fit and final sampled endpoints, followed by H."""
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import subprocess
import time

from experiments.candidates.ucope.uav_motion_prefix_b01.study import (
    clean_json, difference_stats, new_counts, write_summary)

OBJECT = "VSPC1-NATIVE-HOLD-VALUE-B01"
CARD = "docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B01_SCIENCE_CARD_20260908.md"
ARMS = ("GATED-V", "MLP-V")


@dataclass
class Config:
    seed: int = 8101
    fixture: bool = False
    horizon: int = 256
    train_episodes: int = 512
    eval_episodes: int = 32
    chunk: int = 32
    arm_cap: float = 1800
    pair_cap: float = 3600
    ratio_grouping: str = "agent_compound"

    @classmethod
    def engineering(cls):
        return cls(9001, True, 8, 2, 2, 8)


class Deadline:
    def __init__(self, start, arm_cap, pair_cap, clock=time.monotonic):
        self.start = self.arm_start = start
        self.arm_cap, self.pair_cap, self.clock = arm_cap, pair_cap, clock
        self.arm = ARMS[0]
        self.breach = None

    def check(self):
        now = self.clock()
        if self.breach is None and (now - self.start > self.pair_cap
                                    or now - self.arm_start > self.arm_cap):
            self.breach = f"{self.arm} deadline exceeded at pair elapsed {now-self.start:.6f}s"
        if self.breach:
            raise TimeoutError(self.breach)
        return now

    def next_arm(self):
        now = self.check()  # Never borrow the second allowance for a first-arm overrun.
        self.arm, self.arm_start = ARMS[1], now


def primary_from_rows(rows, expected, reset_start):
    identities = [(e, reset_start + e) for e in range(expected)]
    values, complete = {}, {}
    for arm in (*ARMS, "H"):
        selected = [r for r in rows if r["arm"] == arm and r["phase"] == "eval"]
        values[arm] = {(r["episode"], r["reset_seed"]): r["J"] for r in selected}
        complete[arm] = (len(selected) == expected and set(values[arm]) == set(identities)
                         and all(math.isfinite(v) for v in values[arm].values()))
    result = {"complete": all(complete[a] for a in ARMS), "hover_complete": complete["H"],
              "J": {a: [v[k] for k in sorted(v)] for a, v in values.items()},
              "identities": {a: [list(k) for k in sorted(v)] for a, v in values.items()},
              "reading": None, "independent_training_pairs": 1}
    for first, second in ((ARMS[0], ARMS[1]), (ARMS[0], "H"), (ARMS[1], "H")):
        valid = complete[first] and complete[second]
        stats = difference_stats(values[first][k] - values[second][k] for k in identities) if valid else difference_stats([])
        stats.update(complete=valid, identities=[list(k) for k in identities] if valid else [])
        result[f"{first}_minus_{second}"] = stats
    if result["complete"]:
        delta = result["GATED-V_minus_MLP-V"]["mean"]
        result["reading"] = "UP" if delta > .01 else "DOWN" if delta < -.01 else "WITHIN"
    return result


def checkpoint_identity(config, arm, sha):
    return dict(object=OBJECT, algorithm=arm, arm=arm, seed=config.seed,
                mode="ENGINEERING_FIXTURE" if config.fixture else "UAV_B_EXPLORE",
                configuration=asdict(config), ratio_grouping="agent_compound", launch_sha=sha)


def run_pair(config, out, start, clock=time.monotonic, factory=None, publish=write_summary):
    import torch
    from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter, make_real
    from experiments.candidates.ucope.uav_motion_prefix_b01.learner import collect_episode, optimizer_for, update
    from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator, snapshot, templates
    from .critic import R_COLUMNS, models, movement

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    deadline = Deadline(start, config.arm_cap, config.pair_cap, clock)
    if factory is None:
        factory = (lambda seed: SyntheticAdapter(seed, config.horizon)) if config.fixture else make_real
    rows, limits, arms = [], [], {}
    b = 100000 * config.seed
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                  cwd=Path(__file__).resolve().parents[4], text=True).strip()
    summary = dict(object=OBJECT, card=CARD, seed=config.seed, launch_sha=sha,
                   mode="ENGINEERING_FIXTURE" if config.fixture else "UAV_B_EXPLORE",
                   configuration=asdict(config), ratio_grouping="agent_compound",
                   arms=arms, limits=limits, status="INCOMPLETE",
                   resources="resources_unmeasured",
                   timing_boundary="in-process through publication/readback; excludes interpreter exit",
                   complete_exit_cap_conformance="unmeasured: use existing supervisor terminal process wall",
                   mlp_start_pair_elapsed=None,
                   rollout_loss_coverage="completed source updates only; partial-update Adam counts are retained",
                   cost_projection={"GATED-V": "init + 131072*c_env_actor + 1024*c_update + 8192*c_eval + publication; gate increment unmeasured",
                                    "MLP-V": "131072*c_env_actor + 1024*c_update + 16384*c_eval + pair publication/readback/exit"},
                   seeds=dict(initialization=b+11, train_velocity=b+21, train_duration=b+22,
                              constructor_reset=b+1000, train_reset_start=b+1000,
                              eval_reset_start=b+2000, eval_velocity_start=b+3000,
                              eval_duration_start=b+4000))
    files = {name: (out / f"{name}.jsonl").open("w", encoding="utf-8") for name in ("episodes", "rollouts")}

    def emit(name, row):
        if name == "episodes":
            rows.append(row)
        files[name].write(json.dumps(clean_json(row, limits), allow_nan=False) + "\n")
        files[name].flush()

    actor = critic = initial = arm_info = None
    try:
        deadline.check()
        common = templates(config.seed)
        for arm in ARMS:
            if arm == ARMS[1]:
                deadline.next_arm()
                summary["mlp_start_pair_elapsed"] = deadline.arm_start - start
            counts = new_counts()
            arm_info = dict(counts=counts, fit_complete=False, complete=False,
                            nonzero_r_rows={"train": 0, "eval": 0},
                            hold_count_coverage="returned complete episodes only", elapsed_wall=None)
            arms[arm] = arm_info
            actor = critic = initial = None
            deadline.check()
            actor, critic = models(common, arm)
            initial = snapshot(actor, critic)
            optimizer = optimizer_for(actor, critic)
            velocity_rng, duration_rng = generator(b+21), generator(b+22)
            deadline.check()
            env = factory(b+1000)
            counts["constructors"] += 1
            counts["constructor_resets"] += 1
            deadline.check()

            def episode(phase, e, model, value_model, vrng, drng, label):
                data = collect_episode(
                    env, model, value_model, config.horizon,
                    b + (1000 if phase == "train" else 2000) + e, vrng, drng,
                    dict(pair_master=config.seed, arm=label, phase=phase, episode=e),
                    deadline.check, counts, lambda row: emit("episodes", row),
                    lambda row: None, limits, real=not config.fixture, diagnostics=False,
                    ratio_grouping="agent_compound")
                if model is not None:
                    arm_info["nonzero_r_rows"][phase] += int((data["critic"][..., R_COLUMNS] != 0).any(-1).sum())
                return data

            for index in range(config.train_episodes // 2):
                before = counts.copy()
                episodes = [episode("train", 2*index+i, actor, critic, velocity_rng, duration_rng, arm) for i in range(2)]
                records = update(actor, critic, optimizer, episodes, config.chunk, deadline.check,
                                 counts, ratio_grouping="agent_compound")
                counts["rollouts"] += 1
                emit("rollouts", dict(arm=arm, pair_master=config.seed, rollout=index,
                                      steps=2*config.horizon, episodes=2, epochs=records,
                                      **{k: counts[k]-before[k] for k in ("optimizer_steps", "velocity_decisions", "duration_decisions", "d4")}))
                deadline.check()
            arm_info["fit_complete"] = True
            arm_info["training_counts"] = counts.copy()
            arm_info["exposure"] = movement(initial, actor, critic)
            deadline.check()
            torch.save(dict(checkpoint_identity(config, arm, sha), actor=actor.state_dict(),
                            critic=critic.state_dict()), out / f"final_{arm}.pt")
            arm_info["checkpoint"] = f"final_{arm}.pt"
            deadline.check()
            before = counts.copy()
            for e in range(config.eval_episodes):
                episode("eval", e, actor, critic, generator(b+3000+e), generator(b+4000+e), arm)
            arm_info["evaluation_counts"] = {k: counts[k]-before[k] for k in counts}
            ec = arm_info["evaluation_counts"]
            arm_info["sampled_d4_frequency"] = ec["d4"] / ec["duration_decisions"]
            arm_info["complete"] = True
            deadline.check()
            if arm == ARMS[1]:
                before = counts.copy()
                try:
                    for e in range(config.eval_episodes):
                        episode("eval", e, None, None, None, None, "H")
                except Exception as error:
                    limits.append(f"H: {type(error).__name__}: {error}")
                    if isinstance(error, TimeoutError):
                        raise
                finally:
                    arm_info["hover_counts"] = {k: counts[k]-before[k] for k in counts}
            arm_info["elapsed_wall"] = deadline.check() - deadline.arm_start
    except Exception as error:
        limits.append(f"execution: {type(error).__name__}: {error}")
        if arm_info is not None:
            if initial is not None:
                arm_info["exposure"] = movement(initial, actor, critic)
            arm_info["elapsed_wall"] = clock() - deadline.arm_start
    finally:
        for stream in files.values():
            stream.close()

    summary["counts"] = {k: sum(a["counts"][k] for a in arms.values()) for k in new_counts()}
    summary["counts"]["partial_episode_steps"] = summary["counts"]["team_steps"] - summary["counts"]["completed_episode_steps"]
    summary["scientific_uav_calls"] = summary["counts"]["scientific_uav_calls"]
    summary["primary"] = primary_from_rows(rows, config.eval_episodes, b+2000)
    summary["status"] = ("COMPLETE" if summary["primary"]["complete"] and summary["primary"]["hover_complete"] and not limits
                         else "PRIMARY_COMPLETE_WITH_LIMITS" if summary["primary"]["complete"] else "INCOMPLETE")

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
        publish(out / "summary.json", summary)
        loaded = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        if loaded["primary"] != clean_json(summary["primary"], limits):
            raise ValueError("primary summary readback mismatch")
        for arm, info in arms.items():
            if "checkpoint" in info:
                saved = torch.load(out / info["checkpoint"], map_location="cpu", weights_only=True)
                if any(saved[k] != v for k, v in checkpoint_identity(config, arm, sha).items()):
                    raise ValueError(f"{arm} checkpoint identity readback mismatch")
        summary["publication_readback"] = "complete"
    except Exception as error:
        limits.append(f"publication/readback: {type(error).__name__}: {error}")
        summary["publication_readback"] = "failed"
        summary["status"] = "PUBLICATION_FAILED"
    observe_time()
    write_summary(out / "summary.json", summary)
    # Serialization is indivisible. Record a late breach; never restart its clock.
    previous = summary["cap_breach"]
    observe_time()
    if summary["cap_breach"] and not previous:
        write_summary(out / "summary.json", summary)
    return clean_json(summary, limits)
