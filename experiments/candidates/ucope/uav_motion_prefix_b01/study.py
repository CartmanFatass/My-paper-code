"""Serial T/G/H study and arithmetic-only endpoint aggregation."""
from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path
import statistics
import subprocess
import time


CARD = "docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md"
B02_CARD = "docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md"
B02_OBJECT = "UCOPE-UAV-MOTION-PREFIX-B02"
B03_CARD = "docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md"
B03_OBJECT = "UCOPE-UAV-MOTION-PREFIX-B03"
B04_CARD = "docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B04_SCIENCE_CARD_20260908.md"
B04_OBJECT = "UCOPE-UAV-MOTION-PREFIX-B04"
RENEWAL_CARD = "docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B01_SCIENCE_CARD_20260908.md"
RENEWAL_OBJECT = "UCOPE-UAV-RENEWAL-COMMITMENT-B01"
RENEWAL_B02_CARD = "docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B02_SCIENCE_CARD_20260908.md"
RENEWAL_B02_OBJECT = "UCOPE-UAV-RENEWAL-COMMITMENT-B02"
RENEWAL_B03_CARD = "docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B03_SCIENCE_CARD_20260908.md"
RENEWAL_B03_OBJECT = "UCOPE-UAV-RENEWAL-COMMITMENT-B03"
FROZEN_CARD = "docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_FROZEN_HEAD_B01_SCIENCE_CARD_20260909.md"
FROZEN_OBJECT = "UCOPE-UAV-RENEWAL-FROZEN-HEAD-B01"
FIXED_CARD = "docs/research/candidates/ucope/UCOPE_UAV_FIXED_RENEWAL_B01_SCIENCE_CARD_20260909.md"
FIXED_OBJECT = "UCOPE-UAV-FIXED-RENEWAL-B01"
FIXED_B02_CARD = "docs/research/candidates/ucope/UCOPE_UAV_FIXED_RENEWAL_B02_SCIENCE_CARD_20260909.md"
FIXED_B02_OBJECT = "UCOPE-UAV-FIXED-RENEWAL-B02"
FIXED_B03_CARD = "docs/research/candidates/ucope/UCOPE_UAV_FIXED_RENEWAL_B03_SCIENCE_CARD_20260909.md"
FIXED_B03_OBJECT = "UCOPE-UAV-FIXED-RENEWAL-B03"
HOVER_CARD = "docs/research/candidates/ucope/UCOPE_UAV_FIXED_RENEWAL_HOVER_B01_SCIENCE_CARD_20260909.md"
HOVER_OBJECT = "UCOPE-UAV-FIXED-RENEWAL-HOVER-B01"


def declared_masters(pair):
    if pair == "p21":
        return (6801, 6802)
    if pair == "p24":
        return (6901, 6902)
    if pair == "b02":
        return (7001, 7002)
    if pair == "b03":
        return (7101,)
    if pair == "b04":
        return (7201,)
    if pair == "renewal_b01":
        return (7301,)
    if pair == "renewal_b02":
        return (7401,)
    if pair == "renewal_b03":
        return (7501,)
    if pair == "renewal_frozen_b01":
        return (7601,)
    if pair == "renewal_fixed_b01":
        return (7701,)
    if pair == "renewal_fixed_b02":
        return (7801,)
    if pair == "renewal_fixed_b03":
        return (8001,)
    if pair == "renewal_hover_b01":
        return (7901,)
    raise ValueError("pair must be p21, p24, b02, b03, b04, renewal_b01, renewal_b02 or renewal_b03 or renewal_frozen_b01 or renewal_fixed_b01 or renewal_fixed_b02 or renewal_fixed_b03 or renewal_hover_b01")


@dataclass
class Config:
    seed: int
    fixture: bool = False
    horizon: int = 256
    train_episodes: int = 512
    eval_episodes: int = 32
    chunk: int = 32
    arm_cap: float = 1800
    pair_cap: float = 3600
    pair: str = "p21"
    ratio_grouping: str = field(init=False)
    entropy_coef: float = field(init=False)
    treatment_duration_mode: str = field(init=False)
    treatment_duration_head_seed: int | None = field(init=False)

    def __post_init__(self):
        self.ratio_grouping = "agent_compound" if self.pair in ("b02", "b03", "b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01") else "joint"
        self.entropy_coef = 0.0 if self.pair in ("b03", "b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01") else 0.01
        self.treatment_duration_mode = "sampled_command" if self.pair in ("b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01") else "independent"
        self.treatment_duration_head_seed = 100000 * self.seed + 12 if self.pair in ("b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01") else None

    @classmethod
    def engineering(cls, seed=9001, pair="p21"):
        return cls(seed, True, 8, 2, 2, 8, pair=pair)


class Deadline:
    def __init__(self, start, arm_cap, pair_cap, clock=time.monotonic, first_arm="T"):
        self.start = self.arm_start = start
        self.clock = clock
        self.arm_cap, self.pair_cap = arm_cap, pair_cap
        self.arm = first_arm
        self.breach = None

    def check(self):
        now = self.clock()
        if self.breach is None and (now - self.start > self.pair_cap
                                    or now - self.arm_start > self.arm_cap):
            self.breach = f"{self.arm} deadline exceeded at pair elapsed {now - self.start:.6f}s"
        if self.breach is not None:
            raise TimeoutError(self.breach)
        return now

    def start_g(self, arm="G"):
        now = self.check()
        self.arm, self.arm_start = arm, now
        return now


def difference_stats(differences):
    differences = list(differences)
    return {"differences": differences,
            "mean": statistics.mean(differences) if differences else None,
            "conditional_se": (statistics.stdev(differences) / math.sqrt(len(differences))
                               if len(differences) > 1 else None)}


def primary_from_rows(rows, expected, renewal=False, frozen=False, fixed=False, hover=False):
    first = "F" if fixed else "T"
    values = {arm: {r["episode"]: r["J"] for r in rows
                    if r["arm"] == arm and r["phase"] == "eval"} for arm in (("T", "F", "G", "H") if frozen else (first, "G", "H"))}
    complete = {arm: set(v) == set(range(expected))
               and all(math.isfinite(x) for x in v.values()) for arm, v in values.items()}
    result = {"complete": complete[first] and complete["G"],
              "hover_complete": complete["H"],
              "J": {arm: [v[e] for e in sorted(v)] for arm, v in values.items()},
              "episode_ids": {arm: sorted(v) for arm, v in values.items()}}
    contrasts = [(first + "_minus_G", first, "G"), ("G_minus_H", "G", "H")]
    if renewal:
        contrasts.append((first + "_minus_H", first, "H"))
        result["arm_means"] = {arm: statistics.mean(v.values()) if v else None
                               for arm, v in values.items()}
    if frozen:
        contrasts.extend((("T_minus_F", "T", "F"), ("F_minus_H", "F", "H")))
        result["secondary_complete"] = complete["T"] and complete["F"]
    for name, first, second in contrasts:
        ids = sorted(values[first].keys() & values[second].keys())
        result[name] = difference_stats(values[first][i] - values[second][i] for i in ids)
        result[name].update(episode_ids=ids, complete=complete[first] and complete[second])
    if hover:
        result.update(selected_contrast="F_minus_H", complete=result["F_minus_H"]["complete"])
    return result


def aggregate(summaries, pair="p21"):
    if pair in ("b03", "b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01"):
        raise ValueError(f"{pair.upper()} has one training pair and no multi-pair aggregate")
    declared = declared_masters(pair)
    if len(summaries) != 2:
        raise ValueError("aggregation takes exactly two pair summaries")
    if len({s["seed"] for s in summaries}) != 2:
        raise ValueError("two independent pair masters are required")
    modes = {s["mode"] for s in summaries}
    if len(modes) != 1:
        raise ValueError("cannot combine synthetic and UAV endpoints")
    if modes == {"UAV_B_EXPLORE"}:
        if {s["seed"] for s in summaries} != set(declared):
            raise ValueError(f"the {pair} UAV joint primary requires masters {declared}")
        for s in summaries:
            if pair == "b02":
                if (s.get("object") != B02_OBJECT or s.get("pair") != "b02"
                        or s.get("declared_masters") != list(declared)
                        or s.get("card") != B02_CARD or s.get("card_section") != 5
                        or s.get("ratio_grouping") != "agent_compound"):
                    raise ValueError("summary B02 objective binding does not match selected pair")
                continue
            # Original P21 summaries predate allocation metadata and remain usable.
            if s.get("pair", "p21") != pair or tuple(s.get("declared_masters", (6801, 6802))) != declared:
                raise ValueError("summary declared pair does not match selected pair")
            if s.get("card", CARD) != CARD or s.get("card_section", 8) != (10 if pair == "p24" else 8):
                raise ValueError("summary card binding does not match selected pair")
    elif modes != {"ENGINEERING_FIXTURE"} or pair != "p21":
        raise ValueError("only the legacy fixture route accepts synthetic summaries")
    pairs = [{"seed": s["seed"], "primary": s["primary"], "limits": s.get("limits", [])}
             for s in summaries]
    complete = all(s["primary"]["complete"] for s in summaries)
    result = {"mode": "AGGREGATE", "input_mode": summaries[0]["mode"], "pairs": pairs,
              "card": CARD, "primary": {"complete": complete},
              "pair": pair if modes == {"UAV_B_EXPLORE"} else "ENGINEERING_FIXTURE",
              "declared_masters": list(declared) if modes == {"UAV_B_EXPLORE"}
                                  else [s["seed"] for s in summaries],
              "card_section": (10 if pair == "p24" else 8) if modes == {"UAV_B_EXPLORE"} else "CODE_SPEC §8"}
    if pair == "b02":
        result.update(object=B02_OBJECT, card=B02_CARD, card_section=5,
                      ratio_grouping="agent_compound")
    if complete:
        endpoints = [s["primary"]["T_minus_G"]["mean"] for s in summaries]
        ses = [s["primary"]["T_minus_G"]["conditional_se"] for s in summaries]
        delta = statistics.mean(endpoints)
        result["primary"].update(pair_means=endpoints, mean=delta,
                                  training_endpoint_sample_sd=statistics.stdev(endpoints),
                                  conditional_se=(math.sqrt(sum(x*x for x in ses))/2
                                                  if all(x is not None for x in ses) else None),
                                  reading="UP" if delta > .01 else "DOWN" if delta < -.01 else "WITHIN")
    else:
        result["primary"]["reading"] = "PARTIAL"
    return result


def clean_json(value, errors):
    if isinstance(value, float) and not math.isfinite(value):
        if "nonfinite output replaced by null" not in errors:
            errors.append("nonfinite output replaced by null")
        return None
    if isinstance(value, dict):
        return {k: clean_json(v, errors) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean_json(v, errors) for v in value]
    return value


def write_summary(path, summary):
    cleaned = clean_json(summary, summary.setdefault("limits", []))
    cleaned["limits"] = summary["limits"]
    Path(path).write_text(json.dumps(cleaned, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def new_counts(renewal=False):
    counts = dict.fromkeys(("train_team_steps", "eval_team_steps", "team_steps", "optimizer_steps",
                          "train_episodes", "eval_episodes", "velocity_decisions", "duration_decisions",
                          "d4", "recurrent_observations", "explicit_resets", "constructor_resets",
                          "constructors", "step_calls", "scientific_uav_calls", "diagnostic_frames",
                          "completed_episode_steps", "rollouts"), 0)
    if renewal:
        events = ("velocity_decisions", "duration_decisions", "d4",
                  "horizon_censored_holds", "suppressed_decisions")
        counts.update(horizon_censored_holds=0, suppressed_decisions=0)
        counts.update({f"{phase}_{key}": 0 for phase in ("train", "eval") for key in events})
    return counts


def run_pair(config, out, start, clock=time.monotonic, factory=None, publish=write_summary):
    # CLI has set numerical thread limits before this function imports Torch/NumPy.
    import torch
    from .environment import SyntheticAdapter, make_real
    from .learner import collect_episode, optimizer_for, update
    from .policy import arm_copy, exposure, generator, snapshot, templates

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fixed = config.pair in ("renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01")
    deadline = Deadline(start, config.arm_cap, config.pair_cap, clock, first_arm="F" if fixed else "T")
    if factory is None:
        factory = ((lambda seed: SyntheticAdapter(seed, config.horizon)) if config.fixture else make_real)
    frozen = config.pair == "renewal_frozen_b01"
    fitted_arms = ("F", "G") if fixed else ("T", "F", "G") if frozen else ("T", "G")
    rows, limits, arms = [], [], {}
    b = 100000 * config.seed
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[4],
                                      text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        sha = None
        limits.append("launch SHA unavailable")
    summary = {"mode": "ENGINEERING_FIXTURE" if config.fixture else "UAV_B_EXPLORE",
               "seed": config.seed, "configuration": asdict(config), "card": CARD, "launch_sha": sha,
               "pair": "ENGINEERING_FIXTURE" if config.fixture else config.pair,
               "declared_masters": [config.seed] if config.fixture else list(declared_masters(config.pair)),
               "card_section": "CODE_SPEC §8" if config.fixture else (10 if config.pair == "p24" else 8),
               "status": "INCOMPLETE", "arms": arms, "limits": limits,
               "cost_projection": "UAV coefficients unmeasured: init + 131072*c_env_actor + "
                                  "1024*c_update + 8192*c_eval + publication; G adds 8192 H steps",
               "seeds": {"initialization": b + 11, "train_velocity": b + 21,
                         "train_duration": b + 22, "train_reset_start": b + 1000,
                         "eval_reset_start": b + 2000, "eval_velocity_start": b + 3000,
                         "eval_duration_start": b + 4000}}
    if config.pair in ("b02", "b03"):
        summary.update(object=B03_OBJECT if config.pair == "b03" else B02_OBJECT,
                       card=B03_CARD if config.pair == "b03" else B02_CARD,
                       ratio_grouping=config.ratio_grouping,
                       card_section="CODE_SPEC §8" if config.fixture else 5)
    if config.pair in ("b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01"):
        summary.update(object=B04_OBJECT, card=B04_CARD, card_section="CODE_SPEC §4" if config.fixture else 5,
                       ratio_grouping=config.ratio_grouping,
                       treatment_duration_mode=config.treatment_duration_mode,
                       treatment_duration_head_seed=config.treatment_duration_head_seed)
    credit_options = {"ratio_grouping": config.ratio_grouping} if config.pair in ("b02", "b03", "b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01") else {}
    update_options = dict(credit_options)
    if config.pair in ("b03", "b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01"):
        summary["entropy_coef"] = config.entropy_coef
        if config.fixture:
            summary["card_section"] = "CODE_SPEC §4"
        update_options["entropy_coef"] = config.entropy_coef
    if config.pair in ("renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01"):
        summary.update(object=RENEWAL_B03_OBJECT if config.pair == "renewal_b03" else
                       RENEWAL_B02_OBJECT if config.pair == "renewal_b02" else RENEWAL_OBJECT,
                       card=RENEWAL_B03_CARD if config.pair == "renewal_b03" else
                       RENEWAL_B02_CARD if config.pair == "renewal_b02" else RENEWAL_CARD,
                       card_section=7 if config.fixture else 5, commitment="own_expiry")
    if frozen or fixed:
        summary.update(object=FIXED_OBJECT if fixed else FROZEN_OBJECT,
                       card=FIXED_CARD if fixed else FROZEN_CARD,
                       frozen_duration_parameters=2242)
        summary["seeds"].update(frozen_train_velocity=b + 31, frozen_train_duration=b + 32,
                                frozen_eval_velocity_start=b + 5000, frozen_eval_duration_start=b + 6000)
        summary["cost_projection"] = ("Per T/F/G arm: initialization + 131072 training steps + "
                                      "1024 updates + 8192 final-policy steps + publication; "
                                      "T/F duration-head work; G adds 8192 H steps. F wall unmeasured.")
        if fixed:
            summary["cost_projection"] = ("Per F/G arm: initialization + 131072 training steps + "
                                          "1024 updates + 8192 final-policy steps + publication; "
                                          "F duration-head work; G adds 8192 H steps.")
    if config.pair == "renewal_fixed_b02":
        summary.update(object=FIXED_B02_OBJECT, card=FIXED_B02_CARD)
    if config.pair == "renewal_fixed_b03":
        summary.update(object=FIXED_B03_OBJECT, card=FIXED_B03_CARD)
    if config.pair == "renewal_hover_b01":
        summary.update(object=HOVER_OBJECT, card=HOVER_CARD)
    collect_options = dict(credit_options)
    if config.pair in ("renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01"):
        collect_options["renewal"] = True
    files = {name: (out / f"{name}.jsonl").open("w", encoding="utf-8")
             for name in ("episodes", "rollouts", "diagnostics")}

    def emit(name, row):
        if name == "episodes":
            rows.append(row)
        files[name].write(json.dumps(clean_json(row, limits), allow_nan=False) + "\n")
        files[name].flush()

    actor = critic = initial = arm_info = None
    g_start = None
    try:
        deadline.check()  # Startup/imports consume the first fitted arm's allowance.
        common = templates(config.seed)
        for arm in fitted_arms:
            if arm != fitted_arms[0]:
                g_start = deadline.start_g(arm) if frozen else deadline.start_g()
            arm_start = start if arm == fitted_arms[0] else g_start
            counts = new_counts(config.pair in ("renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01"))
            arm_info = {"counts": counts, "complete": False, "fit_complete": False,
                        "learning_rate": 3e-4, "entropy_coef": config.entropy_coef,
                        "elapsed_wall": None}
            arms[arm] = arm_info
            actor = critic = initial = None
            deadline.check()
            head_options = {}
            if config.pair in ("b04", "renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01"):
                head_seed = config.treatment_duration_head_seed if arm in ("T", "F") else None
                head_options["duration_head_seed"] = head_seed
                arm_info.update(duration_mode=config.treatment_duration_mode if arm in ("T", "F") else "none",
                                duration_head_seed=head_seed)
            if arm == "F":
                head_options["freeze_duration"] = True
            actor, critic = arm_copy(common, arm in ("T", "F"), **head_options)
            if frozen or fixed:
                parameters = list(actor.parameters()) + list(critic.parameters())
                arm_info.update(total_parameters=sum(p.numel() for p in parameters),
                                trainable_parameters=sum(p.numel() for p in parameters if p.requires_grad),
                                duration_frozen=arm == "F")
            initial = snapshot(actor, critic)
            optimizer = optimizer_for(actor, critic)
            velocity_rng, duration_rng = generator(b + (31 if arm == "F" else 21)), generator(b + (32 if arm == "F" else 22))
            deadline.check()
            env = factory(b + 1000)
            counts["constructors"] += 1
            counts["constructor_resets"] += 1
            deadline.check()

            def episode(phase, e, model, value_model, vrng, drng, label):
                return collect_episode(env, model, value_model, config.horizon,
                                       b + (1000 if phase == "train" else 2000) + e,
                                       vrng, drng, {"pair_master": config.seed, "arm": label,
                                                    "phase": phase, "episode": e},
                                       deadline.check, counts, lambda row: emit("episodes", row),
                                       lambda row: emit("diagnostics", row), limits,
                                       real=not config.fixture, diagnostics=phase == "eval" and label != "H",
                                       **collect_options)

            for rollout_index in range(config.train_episodes // 2):
                before_counts = counts.copy()
                episodes = [episode("train", 2 * rollout_index + i, actor, critic,
                                    velocity_rng, duration_rng, arm) for i in range(2)]
                records = update(actor, critic, optimizer, episodes, config.chunk, deadline.check, counts,
                                 **update_options)
                counts["rollouts"] += 1
                emit("rollouts", {"pair_master": config.seed, "arm": arm, "rollout": rollout_index,
                                   "steps": 2 * config.horizon, "episodes": 2, "epochs": records,
                                   **{key: counts[key] - before_counts[key]
                                      for key in (("optimizer_steps", "velocity_decisions",
                                                   "duration_decisions", "d4")
                                                  + (("horizon_censored_holds", "suppressed_decisions")
                                                     if config.pair in ("renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01") else ()))}})
                deadline.check()
            arm_info["fit_complete"] = True
            arm_info["training_counts"] = counts.copy()
            arm_info["exposure"] = exposure(initial, actor, critic)
            deadline.check()
            torch.save({"actor": actor.state_dict(), "critic": critic.state_dict(),
                        "configuration": asdict(config), "arm": arm}, out / f"final_{arm}.pt")
            deadline.check()
            before_eval = counts.copy()
            for e in range(config.eval_episodes):
                episode("eval", e, actor, critic, generator(b + (5000 if arm == "F" else 3000) + e),
                        generator(b + (6000 if arm == "F" else 4000) + e), arm)
            arm_info["evaluation_counts"] = {key: counts[key] - before_eval[key] for key in counts}
            arm_info["sampled_d4_frequency"] = (arm_info["evaluation_counts"]["d4"] /
                                                 arm_info["evaluation_counts"]["duration_decisions"]
                                                 if arm in ("T", "F") else None)
            deadline.check()
            arm_info["complete"] = True
            if arm == "G":
                before_hover = counts.copy()
                try:
                    for e in range(config.eval_episodes):
                        episode("eval", e, None, None, None, None, "H")
                except Exception as error:
                    limits.append(f"hover: {type(error).__name__}: {error}")
                    if isinstance(error, TimeoutError):
                        raise
                finally:
                    arm_info["hover_counts"] = {key: counts[key] - before_hover[key] for key in counts}
            arm_info["elapsed_wall"] = deadline.check() - arm_start
    except Exception as error:
        limits.append(f"execution: {type(error).__name__}: {error}")
        if arm_info is not None:
            if initial is not None:
                arm_info["exposure"] = exposure(initial, actor, critic)
            arm_info["elapsed_wall"] = clock() - deadline.arm_start
    finally:
        for stream in files.values():
            stream.close()

    summary["counts"] = {key: sum(a["counts"][key] for a in arms.values()) for key in new_counts(config.pair in ("renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01"))}
    summary["counts"]["partial_episode_steps"] = (summary["counts"]["team_steps"]
                                                   - summary["counts"]["completed_episode_steps"])
    summary["scientific_uav_calls"] = summary["counts"]["scientific_uav_calls"]
    summary["primary"] = primary_from_rows(rows, config.eval_episodes, renewal=config.pair in ("renewal_b01", "renewal_b02", "renewal_b03", "renewal_frozen_b01", "renewal_fixed_b01", "renewal_fixed_b02", "renewal_fixed_b03", "renewal_hover_b01"), frozen=frozen, fixed=fixed, hover=config.pair == "renewal_hover_b01")
    summary["diagnostics_complete"] = (summary["counts"]["diagnostic_frames"] ==
                                        len(fitted_arms) * config.eval_episodes * 5 * min(5, config.horizon)
                                        and not any("diagnostic" in x for x in limits))
    summary["status"] = ("COMPLETE" if all(a.get("complete") for a in arms.values())
                         and len(arms) == len(fitted_arms) and summary["primary"]["hover_complete"] and not limits
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
    # A late indivisible publication is observed and recorded, never a clock reset.
    try:
        publish(out / "summary.json", summary)
    except Exception as error:
        limits.append(f"pair publication: {type(error).__name__}: {error}")
        summary["status"] = "PUBLICATION_FAILED"
    observe_time()
    write_summary(out / "summary.json", summary)
    # Check the final timing serialization too. Only corrective reporting can follow a breach.
    previous_breach = summary["cap_breach"]
    observe_time()
    if summary["cap_breach"] and not previous_breach:
        write_summary(out / "summary.json", summary)
    return clean_json(summary, limits)
