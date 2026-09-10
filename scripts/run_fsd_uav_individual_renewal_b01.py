"""Fixed UAV B01 I/authentic-D0 pair; no empirical invocation during source checks.

The later supervisor must enforce complete-command timeouts of D0 3600s and
I 18000s, from adjacent admission through final publication. No retry or resume.
"""
import time

PROCESS_START = time.perf_counter()

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import run_flexible_skill_duration_e0 as e0
from hmasd.agent import HMASDAgent

OBJECT_ID = "FSD_UAV_INDIVIDUAL_RENEWAL_B01"
CARD = "docs/research/candidates/flexible_skill_duration/" + OBJECT_ID + "_SCIENCE_CARD_20260908.md"
TRAIN_SEED, EVAL_SEED = 770503, 780503
TRAIN_LANES, EVAL_LANES, HORIZON, ROLLOUTS = 16, 32, 500, 5
N_UAVS, N_USERS = 6, 50
CAPS = {"D0": 3600., "I": 18000.}
NETWORKS = ("coordinator", "discoverer_actor", "discoverer_critic",
            "team_discriminator", "individual_discriminator")
COMPONENTS = ("coverage_reward", "quality_reward", "energy_penalty", "total_reward")


def seed_rng(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def require_finite(value, label):
    if isinstance(value, dict):
        for key, item in value.items():
            require_finite(item, f"{label}.{key}")
    elif isinstance(value, (list, tuple)):
        for item in value:
            require_finite(item, label)
    elif isinstance(value, torch.Tensor):
        if not torch.isfinite(value).all():
            raise ValueError(f"nonfinite {label}")
    elif isinstance(value, (np.ndarray, float, np.number)):
        if not np.isfinite(value).all():
            raise ValueError(f"nonfinite {label}")


def measured(value, label):
    require_finite(value, label)
    return e0._jsonable(value)


def check_deadline(summary, stage):
    if time.perf_counter() - PROCESS_START >= CAPS[summary["arm"]]:
        raise TimeoutError(f"complete-command cap at {stage}")


def write_json(path, value):
    # Scientific values must be finite before conversion of NumPy scalars/arrays.
    value = measured(value, path.name)
    temporary = path.with_suffix(".partial.json")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
    temporary.replace(path)


def publish(out, summary, stage):
    check_deadline(summary, stage)
    summary["last_completed_boundary"] = stage
    summary["wall_seconds_before_publication"] = time.perf_counter() - PROCESS_START
    write_json(out / "summary.json", summary)
    check_deadline(summary, stage + ":published")


def make_config(arm, envs, seed):
    # E0 provides the ordinary config. Apply I's cost before either model exists.
    config = e0._make_config("D0", seed, len(envs), HORIZON, HORIZON, N_UAVS,
                             N_USERS, ROLLOUTS, envs[0].state_dim, envs[0].obs_dim)
    config.interruption_cost_c = .25 if arm == "I" else float("inf")
    config.n_Z = config.n_z = 6
    return config


def config_snapshot(config):
    values = {key: getattr(config, key) for key in e0.CONFIG_DUMP_FIELDS if hasattr(config, key)}
    for key in ("interruption_cost_c", "interruption_cost_c_Z"):
        if values[key] == float("inf"):
            values[key] = "Infinity"
    return measured(values, "configuration snapshot")


def optimizer_counters(agent):
    return {name: e0._StepCounter(optimizer) if optimizer is not None else None
            for name in NETWORKS for optimizer in (getattr(agent, name + "_optimizer", None),)}


def optimizer_counts(counters):
    return {name: counter.count if counter is not None else 0 for name, counter in counters.items()}


def renewal_metrics(agent):
    result = {"d2_metrics": measured(agent.get_d2_metrics(), "D2 metrics"), "segments": {}}
    for kind in ("agent", "team"):
        lengths = np.asarray(agent.d2_metrics["segment_lengths_" + kind], dtype=np.int64)
        result["segments"][kind] = {
            "count": int(lengths.size), "total_length": int(lengths.sum()),
            "min": int(lengths.min()) if lengths.size else None,
            "max": int(lengths.max()) if lengths.size else None,
            "mean": float(lengths.mean()) if lengths.size else None}
    return result


def base_summary(arm, *, training_seed=TRAIN_SEED, evaluation_seed=EVAL_SEED, object_id=OBJECT_ID, card=CARD):
    return {
        "object_id": object_id, "card": card, "arm": arm, "launch_sha": e0._git("rev-parse", "HEAD"),
        "training_seed": training_seed, "evaluation_seed": evaluation_seed,
        "training_lane_seeds": list(range(training_seed, training_seed + TRAIN_LANES)),
        "evaluation_lane_seeds": list(range(evaluation_seed, evaluation_seed + EVAL_LANES)),
        "host": {"class": "envs.pettingzoo.scenario1.UAVBaseStationEnv", "n_uavs": N_UAVS,
                 "n_users": N_USERS, "horizon": HORIZON, "user_distribution": "uniform",
                 "channel_model": "free_space"},
        "device": "cpu", "torch_threads": 4, "learner_precision": "float32",
        "reward_return_precision": "float64", "native_score_factor": N_UAVS / HORIZON,
        "cap_seconds": CAPS[arm], "summed_pair_cap_seconds": sum(CAPS.values()),
        "status": "incomplete", "failure": None, "learner_config": None,
        "evaluation_config": None, "training_rows": [], "evaluation": None,
        "initial_parameter_norms": {}, "optimizer_calls": dict.fromkeys(NETWORKS, 0),
        "counts": dict.fromkeys(("model_constructions", "training_starts", "checkpoint_loads",
                                 "training_transitions", "stored_training_transitions", "training_episodes",
                                 "update_stages", "training_agent_step_batches", "evaluation_steps",
                                 "evaluation_episodes", "evaluation_agent_step_batches"), 0)}


def build_learner(summary, out, *, training_seed=TRAIN_SEED):
    check_deadline(summary, "learner setup")
    torch.set_num_threads(4)
    seed_rng(training_seed)
    envs = e0._make_envs(TRAIN_LANES, training_seed, N_UAVS, N_USERS, HORIZON)
    config = make_config(summary["arm"], envs, training_seed)
    summary["learner_config"] = config_snapshot(config)
    agent = HMASDAgent(config, log_dir=str(out / "learner_logs"), device=torch.device("cpu"))
    summary["counts"]["model_constructions"] += 1
    summary["counts"]["training_starts"] += 1
    theta0 = e0._capture_theta0(agent)
    summary["initial_parameter_norms"] = measured({k: v["norm"] for k, v in theta0.items()}, "initial parameters")
    counters = optimizer_counters(agent)
    summary["optimizer_present"] = {k: v is not None for k, v in counters.items()}
    publish(out, summary, "learner constructed")
    return envs, agent, theta0, counters


def collect_training(envs, agent, theta0, counters, summary, out):
    states, observations = e0._reset_all(envs)
    require_finite((states, observations), "training reset inputs")
    env_steps, dones = np.zeros(TRAIN_LANES, dtype=int), np.zeros(TRAIN_LANES, dtype=bool)
    agent.train(True)
    for rollout in range(ROLLOUTS):
        before = optimizer_counts(counters)
        row = {"rollout_index": rollout, "transitions": 0, "stored_transitions": 0,
               "completed_episodes": 0, "stored_batches": 0, "updated": False,
               "return_sums": [0.] * TRAIN_LANES, "episode_returns_U": None,
               "optimizer_calls_before": before}
        summary["training_rows"].append(row)
        returns = np.zeros(TRAIN_LANES, dtype=np.float64)
        for t in range(HORIZON):
            check_deadline(summary, "training collection")
            actions, _, data = agent.step(states, observations, env_steps, dones,
                                         deterministic=False, return_step_data=True, build_infos=False)
            summary["counts"]["training_agent_step_batches"] += 1
            require_finite(actions, "training actions")
            require_finite(data, "sampled step data")
            next_states, next_observations = [], []
            rewards, next_dones = np.zeros(TRAIN_LANES, dtype=np.float64), np.zeros(TRAIN_LANES, dtype=bool)
            for lane, env in enumerate(envs):
                obs, reward, term, trunc, info = env.step(actions[lane])
                summary["counts"]["training_transitions"] += 1
                row["transitions"] += 1
                next_dones[lane] = bool(term or trunc)
                row["completed_episodes"] += int(next_dones[lane])
                summary["counts"]["training_episodes"] += int(next_dones[lane])
                require_finite(reward, "training scalar reward")
                rewards[lane] = reward  # Never multiply learner rewards by the reporting factor.
                returns[lane] += reward
                row["return_sums"] = returns.tolist()
                next_states.append(np.asarray(info["next_state"], dtype=np.float64))
                next_observations.append(np.asarray(obs, dtype=np.float32))
            next_states, next_observations = np.stack(next_states), np.stack(next_observations)
            require_finite((next_states, next_observations), "training next inputs")
            agent.store_transition_batch(states=states, next_states=next_states.copy(), observations=observations,
                next_observations=next_observations.copy(), actions=actions, rewards=rewards, dones=next_dones,
                infos_batch=None, rollout_step_idx=t, step_data=data)
            row["stored_transitions"] += TRAIN_LANES
            row["stored_batches"] += 1
            summary["counts"]["stored_training_transitions"] += TRAIN_LANES
            # Storage already owns terminal next values; both subsequent inputs must be fresh.
            for lane, env in enumerate(envs):
                if next_dones[lane]:
                    reset_obs, reset_info = env.reset()
                    next_observations[lane] = np.asarray(reset_obs, dtype=np.float32)
                    next_states[lane] = np.asarray(reset_info["state"], dtype=np.float64)
                    require_finite((next_states[lane], next_observations[lane]), "training reset inputs")
                    agent.reset_env_state(lane)
                    env_steps[lane] = 0
                else:
                    env_steps[lane] += 1
            states, observations, dones = next_states, next_observations, next_dones
        if not dones.all() or row["completed_episodes"] != TRAIN_LANES:
            raise ValueError("training rollout does not contain the required full terminal episodes")
        row["episode_returns_U"] = measured(returns, "training returns")
        publish(out, summary, f"rollout {rollout} collected")
        # All lanes are terminal. Zero bootstrap requires no extra action/skill sampling.
        try:
            losses = agent.update(last_values=np.zeros((TRAIN_LANES, N_UAVS), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=HORIZON, last_state=states.copy(), last_observations=observations.copy())
            summary["counts"]["update_stages"] += 1
            row["updated"] = True
            row["losses"] = measured(losses, "update losses")
        finally:
            summary["optimizer_calls"] = optimizer_counts(counters)
            row["optimizer_calls_total"] = summary["optimizer_calls"].copy()
            row["optimizer_calls_delta"] = {k: v - before[k] for k, v in summary["optimizer_calls"].items()}
        row.update(renewal_metrics(agent))  # Per-rollout metrics, before ordinary clear.
        row["relative_initialization_displacement"] = measured(e0._exposure_line(agent, theta0), "learner parameters")
        with (out / "training.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
        publish(out, summary, f"rollout {rollout} updated")
        agent.clear_buffers()
        check_deadline(summary, "buffer clear")


class Evaluator(e0.Evaluator):
    """Reuse E0's active-module/normalizer synchronization, with our arm builder."""

    def __init__(self, arm, out, *, evaluation_seed=EVAL_SEED):
        self.lanes = EVAL_LANES
        self.envs = e0._make_envs(EVAL_LANES, evaluation_seed, N_UAVS, N_USERS, HORIZON)
        self.config = make_config(arm, self.envs, evaluation_seed)
        self.agent = HMASDAgent(self.config, log_dir=str(out / "evaluation_logs"), device=torch.device("cpu"))
        self.agent.train(False)


def final_evaluation(learner, summary, out, *, evaluation_seed=EVAL_SEED):
    with e0._preserve_rng():
        check_deadline(summary, "evaluator construction")
        seed_rng(evaluation_seed)
        evaluator = Evaluator(summary["arm"], out, evaluation_seed=evaluation_seed)
        summary["counts"]["model_constructions"] += 1
        summary["evaluation_config"] = config_snapshot(evaluator.config)
        evaluator.agent.clear_buffers()
        evaluator._sync(learner)
        counters = optimizer_counters(evaluator.agent)
        result = {"status": "incomplete", "after_update": summary["counts"]["update_stages"],
                  "episode_ids": list(range(EVAL_LANES)), "lane_seeds": summary["evaluation_lane_seeds"],
                  "steps_per_lane": [0] * EVAL_LANES, "completed_episodes": 0,
                  "return_sums_U": [0.] * EVAL_LANES, "returns_U": None, "native_scores_J": None}
        summary["evaluation"] = result
        states, observations = e0._reset_all(evaluator.envs)
        require_finite((states, observations), "evaluation reset inputs")
        steps, dones = np.zeros(EVAL_LANES, dtype=int), np.zeros(EVAL_LANES, dtype=bool)
        returns = np.zeros(EVAL_LANES, dtype=np.float64)
        components = {k: np.zeros(EVAL_LANES, dtype=np.float64) for k in COMPONENTS}
        try:
            with torch.no_grad():
                for t in range(HORIZON):
                    check_deadline(summary, "final evaluation")
                    actions, _, data = evaluator.agent.step(states, observations, steps, dones,
                        deterministic=True, return_step_data=True, build_infos=False)
                    summary["counts"]["evaluation_agent_step_batches"] += 1
                    require_finite(actions, "evaluation actions")
                    require_finite(data, "evaluation sampled data")
                    for lane, env in enumerate(evaluator.envs):
                        obs, reward, term, trunc, info = env.step(actions[lane])
                        summary["counts"]["evaluation_steps"] += 1
                        result["steps_per_lane"][lane] += 1
                        dones[lane] = bool(term or trunc)
                        result["completed_episodes"] += int(dones[lane])
                        summary["counts"]["evaluation_episodes"] += int(dones[lane])
                        require_finite(reward, "evaluation scalar reward")
                        returns[lane] += reward
                        result["return_sums_U"] = returns.tolist()
                        values = {k: info["reward_components"]["reward_info"][k] for k in COMPONENTS}
                        require_finite(values, "native reward components")
                        for key, value in values.items():
                            components[key][lane] += value
                        states[lane] = np.asarray(info["next_state"], dtype=np.float64)
                        observations[lane] = np.asarray(obs, dtype=np.float32)
                        require_finite((states[lane], observations[lane]), "evaluation next inputs")
                    result["component_sums"] = {k: v.tolist() for k, v in components.items()}
                    steps += 1
                    if dones.any() and (t != HORIZON - 1 or not dones.all()):
                        raise ValueError("evaluation has an unexpected terminal boundary")
            if not dones.all():
                raise ValueError("evaluation missing terminal episodes")
            result.update(renewal_metrics(evaluator.agent))
            result["returns_U"] = measured(returns, "primary scalar returns")
            result["native_scores_J"] = measured(N_UAVS * returns / HORIZON, "primary native scores")
            result["component_means"] = measured({k: v / HORIZON for k, v in components.items()}, "native components")
            result["status"] = "complete"
        finally:
            summary["evaluation_optimizer_calls"] = optimizer_counts(counters)
        publish(out, summary, "final evaluation")


def assemble_pair(treatment, control, *, training_seed=TRAIN_SEED, evaluation_seed=EVAL_SEED,
                  object_id=OBJECT_ID, card=CARD):
    for name, arm in (("I", treatment), ("D0", control)):
        require_finite(arm, f"{name} companion measurements")
        if arm["arm"] != name or arm["status"] != "complete":
            raise ValueError(f"{name} arm incomplete or wrong identity")
        if (arm["object_id"] != object_id or arm["card"] != card
                or arm["training_seed"] != training_seed or arm["evaluation_seed"] != evaluation_seed):
            raise ValueError(f"{name} object/card/seed mismatch")
        counts, endpoint = arm["counts"], arm["evaluation"]
        if (counts["training_transitions"] != TRAIN_LANES * HORIZON * ROLLOUTS
                or counts["stored_training_transitions"] != counts["training_transitions"]
                or counts["training_episodes"] != TRAIN_LANES * ROLLOUTS or counts["update_stages"] != ROLLOUTS
                or counts["model_constructions"] != 2 or counts["training_starts"] != 1 or counts["checkpoint_loads"] != 0
                or counts["training_agent_step_batches"] != HORIZON * ROLLOUTS
                or len(arm["training_rows"]) != ROLLOUTS or not all(r["updated"] for r in arm["training_rows"])):
            raise ValueError(f"{name} missing required learning")
        if (endpoint["status"] != "complete" or endpoint["after_update"] != ROLLOUTS
                or endpoint["episode_ids"] != list(range(EVAL_LANES))
                or endpoint["lane_seeds"] != list(range(evaluation_seed, evaluation_seed + EVAL_LANES))
                or endpoint["steps_per_lane"] != [HORIZON] * EVAL_LANES
                or endpoint["completed_episodes"] != EVAL_LANES or counts["evaluation_steps"] != EVAL_LANES * HORIZON
                or counts["evaluation_agent_step_batches"] != HORIZON
                or counts["evaluation_episodes"] != EVAL_LANES or any(arm["evaluation_optimizer_calls"].values())):
            raise ValueError(f"{name} missing or wrong endpoint")
        for key in ("returns_U", "native_scores_J"):
            values = np.asarray(endpoint[key], dtype=np.float64)
            if values.shape != (EVAL_LANES,):
                raise ValueError(f"{name} missing primary values")
            require_finite(values, "paired primary")
        if not np.allclose(np.asarray(endpoint["returns_U"]) * N_UAVS / HORIZON,
                           endpoint["native_scores_J"], rtol=1e-9, atol=1e-9):
            raise ValueError(f"{name} primary scaling mismatch")
    for key in ("card", "host", "training_lane_seeds", "evaluation_lane_seeds",
                "device", "torch_threads", "learner_precision", "reward_return_precision", "native_score_factor"):
        if treatment[key] != control[key]:
            raise ValueError(f"pair mismatch: {key}")
    for key, lanes, seed in (("learner_config", TRAIN_LANES, training_seed), ("evaluation_config", EVAL_LANES, evaluation_seed)):
        configs = []
        for name, arm in (("I", treatment), ("D0", control)):
            config = dict(arm[key])
            expected = {"policy_interruption_mode": "d2", "interruption_cost_c": .25 if name == "I" else "Infinity",
                        "interruption_cost_c_Z": "Infinity", "k": 10, "skill_cap_k_max": 10, "team_cap_k_Z": 10,
                        "interruption_delta": 1, "age_feature": "off", "n_Z": 6, "n_z": 6, "n_agents": N_UAVS,
                        "n_users": N_USERS, "num_envs": lanes, "rollout_length": HORIZON, "seed": seed}
            if any(config[k] != v for k, v in expected.items()):
                raise ValueError(f"{name} {key} construction mismatch")
            config.pop("interruption_cost_c")
            configs.append(config)
        if configs[0] != configs[1]:
            raise ValueError(f"pair mismatch: {key}")
    differences = np.asarray(treatment["evaluation"]["native_scores_J"]) - np.asarray(control["evaluation"]["native_scores_J"])
    mean, sd = float(differences.mean()), float(differences.std(ddof=1))
    return {"status": "complete", "independent_training_pairs": 1, "episode_ids": list(range(EVAL_LANES)),
            "i_minus_d0": {"differences": differences.tolist(), "mean": mean, "sample_sd": sd,
                           "conditional_se": sd / np.sqrt(EVAL_LANES)},
            "card_reading": "above_mei" if mean > .01 else "opposite_sign" if mean < -.01 else "small_or_resolution_limited"}


def main(argv=None, *, training_seed=TRAIN_SEED, evaluation_seed=EVAL_SEED, object_id=OBJECT_ID, card=CARD):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=("D0", "I"), required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--d0-summary", type=Path)
    args = parser.parse_args(argv)
    if args.arm == "D0" and args.d0_summary is not None:
        parser.error("only I reads a D0 companion")
    out = args.output_root.resolve()
    out.mkdir(parents=True, exist_ok=True)
    summary = base_summary(args.arm, training_seed=training_seed, evaluation_seed=evaluation_seed,
                           object_id=object_id, card=card)
    try:
        check_deadline(summary, "manifest")
        write_json(out / "manifest.json", {k: v for k, v in summary.items()
                   if k not in ("status", "failure", "training_rows", "evaluation", "counts")})
        publish(out, summary, "setup")
        envs, learner, theta0, counters = build_learner(summary, out, training_seed=training_seed)
        collect_training(envs, learner, theta0, counters, summary, out)
        final_evaluation(learner, summary, out, evaluation_seed=evaluation_seed)
        summary["status"] = "complete"
        if args.arm == "I":
            summary["comparison_input"] = str(args.d0_summary)
            try:
                check_deadline(summary, "pair readout")
                if args.d0_summary is None:
                    raise ValueError("D0 companion unavailable")
                control = json.loads(args.d0_summary.read_text(encoding="utf-8"))
                summary["pair"] = assemble_pair(summary, control, training_seed=training_seed,
                    evaluation_seed=evaluation_seed, object_id=object_id, card=card)
            except (OSError, KeyError, TypeError, ValueError) as exc:
                summary["pair"] = {"status": "incomplete", "failure": str(exc)}
        try:
            if sys.platform == "win32":
                import psutil
                summary["peak_rss_bytes"] = int(psutil.Process().memory_info().peak_wset)
            else:
                import resource
                summary["peak_rss_bytes"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024))
        except (ImportError, OSError):
            summary["peak_rss_bytes"] = None
        publish(out, summary, "final")
    except Exception as exc:
        summary["status"], summary["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
        summary.pop("pair", None)
        # Retain observed partial facts without pretending to finish after the cap.
        write_json(out / "summary.json", summary)
    success = summary["status"] == "complete" and summary.get("pair", {}).get("status", "complete") == "complete"
    print(json.dumps({"status": summary["status"], "failure": summary["failure"], "complete": success}))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
