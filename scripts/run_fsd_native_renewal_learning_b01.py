"""Fresh C/H native-renewal learning B01; G is the public, untrained reference.

Launch only under the existing supervisor with a complete-command OS timeout:
900 s C/H, 60 s G, starting before interpreter/import and ending after publication.
The cooperative clock cannot interrupt an individual optimizer update. No retries.
"""
import time

PROCESS_START = time.perf_counter()  # Includes subsequent heavy imports.

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

from envs.relay_corridor.adapter import RelayCorridorAdapter
from envs.relay_corridor.config import proposal_config
from envs.relay_corridor.hmasd_driver import build_corridor_learner_config
from envs.relay_corridor.references import GreedyOnPublicState
from hmasd.agent import HMASDAgent
import run_flexible_skill_duration_e0 as e0
from run_flexible_skill_duration_e2 import CorridorEvaluator
from run_flexible_skill_duration_e3 import arm_parameters, peak_rss_bytes

OBJECT_ID = "FSD_NATIVE_RENEWAL_LEARNING_B01"
CARD = "docs/research/candidates/flexible_skill_duration/" + OBJECT_ID + "_SCIENCE_CARD_20260908.md"
SEED, EVAL_MASTER, ROLLOUTS, TRAIN_LANES, EVAL_LANES = 770203, 770204, 5, 16, 32
CAPS = {"C": 900., "H": 900., "G": 60.}
NETWORKS = ("coordinator", "discoverer_actor", "discoverer_critic",
            "team_discriminator", "individual_discriminator")


def check_deadline(start, policy, stage):
    if time.perf_counter() - start >= CAPS[policy]:
        raise TimeoutError(f"{policy} complete-command cap at {stage}")


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


def applied_mask(policy, internal, host, env_steps):
    public = host.change_flag[:, host.region_of_agent].astype(bool)
    return np.array(np.where(np.asarray(env_steps)[:, None] > 0, public, internal)
                    if policy == "H" else internal, dtype=bool, copy=True)


def base_summary(policy, corridor, launch_sha, *, training_seed=SEED,
                 evaluation_master=EVAL_MASTER, object_id=OBJECT_ID, card=CARD):
    return {
        "object_id": object_id, "card": card, "policy": policy, "launch_sha": launch_sha,
        "seed": None if policy == "G" else training_seed, "training_master": training_seed,
        "evaluation_master": evaluation_master, "episode_ids": list(range(EVAL_LANES)),
        "host": json.loads(json.dumps(corridor.parameter_record())),
        "device": "cpu", "torch_threads": torch.get_num_threads(),
        "learner_precision": None if policy == "G" else "float32",
        "host_reward_return_precision": "float64", "learner_config": None,
        "status": "incomplete", "failure": None, "training_rows": [], "evaluation": None,
        "counts": dict.fromkeys(("model_constructions", "training_starts", "checkpoint_loads",
                                 "training_host_steps", "training_transitions", "training_episodes",
                                 "update_stages", "training_agent_step_batches", "scoring_steps",
                                 "evaluation_episodes", "evaluation_agent_step_batches",
                                 "greedy_act_batches", "agent_observations"), 0),
        "optimizer_calls": dict.fromkeys(NETWORKS, 0), "initial_parameter_norms": {},
        "cap_seconds": CAPS[policy], "summed_panel_cap_seconds": 1860,
        "external_complete_command_wall_seconds": None,
    }


def write_summary(out, summary):
    temporary = out / "summary.partial.json"
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
        stream.write("\n")
    temporary.replace(out / "summary.json")


def publish(out, summary, start, stage):
    check_deadline(start, summary["policy"], stage + ":publication")
    summary["last_completed_boundary"] = stage
    summary["wall_seconds_before_publication"] = time.perf_counter() - start
    write_summary(out, summary)
    check_deadline(start, summary["policy"], stage + ":published")


def build_learner(corridor, out, summary, start, *, training_seed=SEED):
    policy = summary["policy"]
    check_deadline(start, policy, "setup")
    torch.set_num_threads(4)
    random.seed(training_seed)
    np.random.seed(training_seed)
    torch.manual_seed(training_seed)
    adapter = RelayCorridorAdapter(corridor, num_envs=TRAIN_LANES, master_seed=training_seed,
                                  episode_ids=list(range(TRAIN_LANES)), squeeze_batch=False)
    overrides = arm_parameters("large", "d2")
    config = build_corridor_learner_config(
        corridor, adapter, mode="d2", num_envs=TRAIN_LANES, rollout_length=corridor.horizon,
        k=overrides["skill_cap_k_max"], seed=training_seed, overrides=overrides)
    summary["learner_config"] = {key: getattr(config, key) for key in e0.CONFIG_DUMP_FIELDS
                                 if hasattr(config, key)}
    check_deadline(start, policy, "learner construction")
    agent = HMASDAgent(config, device=torch.device("cpu"), log_dir=str(out / "learner_logs"))
    summary["counts"]["model_constructions"] += 1
    summary["counts"]["training_starts"] += 1
    check_deadline(start, policy, "learner constructed")
    theta0 = e0._capture_theta0(agent)
    norms = {name: value["norm"] for name, value in theta0.items()}
    require_finite(norms, "initial parameters")
    summary["initial_parameter_norms"] = norms
    counters = {name: e0._StepCounter(getattr(agent, name + "_optimizer")) for name in NETWORKS}
    return adapter, agent, overrides, theta0, counters


def segment_summary(lengths):
    array = np.asarray(lengths, dtype=np.int64)
    return {"count": int(array.size), "total_length": int(array.sum()),
            "min": int(array.min()) if array.size else None,
            "max": int(array.max()) if array.size else None,
            "mean": float(array.mean()) if array.size else None}


def collect_training(policy, adapter, agent, summary, theta0, counters, out, start):
    lanes, n, horizon = adapter.num_envs, adapter.n_agents, adapter.config.horizon
    observations, info = adapter.reset()
    observations = np.asarray(observations, dtype=np.float32)
    states = np.asarray(info["state"], dtype=np.float64)
    env_steps, dones = np.zeros(lanes, dtype=int), np.zeros(lanes, dtype=bool)
    agent.train(True)
    for rollout in range(ROLLOUTS):
        row = {"rollout_index": rollout, "episode_ids": list(adapter.episode_ids()),
               "steps_per_lane": 0, "transitions": 0, "completed_episodes": 0,
               "native_return_partial_sums": [0.] * lanes, "native_return": None,
               "internal_renew": 0, "applied_renew": 0, "updated": False}
        summary["training_rows"].append(row)
        reward_sums = np.zeros(lanes, dtype=np.float64)
        before = {name: counter.count for name, counter in counters.items()}
        for t in range(horizon):
            check_deadline(start, policy, "collection")
            actions, _, step_data = agent.step(states, observations, env_steps, dones,
                                               deterministic=False, return_step_data=True,
                                               build_infos=False)
            summary["counts"]["training_agent_step_batches"] += 1
            require_finite(actions, "learner actions")
            require_finite(step_data, "sampled step data")
            internal = np.array(step_data["d2_sampled_mask"], dtype=bool, copy=True)
            applied = applied_mask(policy, internal, adapter.host, env_steps)
            next_obs, _, terminated, truncated, info = adapter.step(actions, renew_mask=applied)
            summary["counts"]["training_host_steps"] += lanes
            summary["counts"]["agent_observations"] += lanes * n
            next_obs = np.asarray(next_obs, dtype=np.float32)
            next_states = np.asarray(info["state"], dtype=np.float64)
            rewards = np.asarray(info["shared_reward"], dtype=np.float64).reshape(lanes)
            require_finite(rewards, "training native reward")
            next_dones = np.broadcast_to(np.asarray(terminated) | np.asarray(truncated), (lanes,)).copy()
            agent.store_transition_batch(
                states=states, next_states=next_states.copy(), observations=observations,
                next_observations=next_obs.copy(), actions=actions, rewards=rewards,
                dones=next_dones, infos_batch=None, rollout_step_idx=t, step_data=step_data)
            row["steps_per_lane"] += 1
            row["transitions"] += lanes
            summary["counts"]["training_transitions"] += lanes
            row["internal_renew"] += int(internal.sum())
            row["applied_renew"] += int(np.asarray(info["renew_mask"]).sum())
            reward_sums += rewards
            row["native_return_partial_sums"] = reward_sums.tolist()
            # The fixed batched host terminates all lanes together at H.
            if next_dones.any():
                row["completed_episodes"] += int(next_dones.sum())
                summary["counts"]["training_episodes"] += int(next_dones.sum())
                adapter.advance_episode_ids()
                next_obs, reset_info = adapter.reset()
                next_obs = np.asarray(next_obs, dtype=np.float32)
                next_states = np.asarray(reset_info["state"], dtype=np.float64)
                for lane in np.flatnonzero(next_dones):
                    agent.reset_env_state(int(lane))
                env_steps[:] = 0
            else:
                env_steps += 1
            states, observations, dones = next_states, next_obs, next_dones
            publish(out, summary, start, f"rollout {rollout} stored batch {t + 1}")
        row["native_return"] = (reward_sums / horizon).tolist()
        check_deadline(start, policy, "update")
        update_info = agent.update(steps_in_buffer=horizon,
                                  last_values=np.zeros((lanes, n), dtype=np.float32),
                                  dones=dones.copy(), last_state=states.copy(),
                                  last_observations=observations.copy())
        summary["counts"]["update_stages"] += 1
        row["updated"] = True
        row["optimizer_calls_total"] = {name: counter.count for name, counter in counters.items()}
        row["optimizer_calls_delta"] = {name: counter.count - before[name] for name, counter in counters.items()}
        summary["optimizer_calls"] = row["optimizer_calls_total"].copy()
        metrics = agent.get_d2_metrics()
        require_finite(metrics, "D2 metrics")
        row["d2_metrics"] = metrics
        row["segments"] = {kind: segment_summary(agent.d2_metrics["segment_lengths_" + kind])
                           for kind in ("agent", "team")}
        exposure = e0._exposure_line(agent, theta0)
        require_finite(exposure, "learner parameters")
        require_finite(update_info, "update output")
        row["relative_initialization_displacement"] = exposure
        publish(out, summary, start, f"rollout {rollout} updated")
        agent.clear_buffers()
        check_deadline(start, policy, "update/clear")


def evaluate(policy, adapter, controller, summary, out, start, reset_lanes=None):
    lanes, n, horizon = adapter.num_envs, adapter.n_agents, adapter.config.horizon
    result = {"status": "incomplete", "episode_ids": list(adapter.episode_ids()),
              "steps_per_lane": 0, "valid_reward_steps_per_lane": 0, "completed_episodes": 0}
    summary["evaluation"] = result
    sums = {key: np.zeros((2, lanes), dtype=np.float64 if key == "return" else np.int64)
            for key in ("return", "eligible", "wrong", "internal_renew", "applied_renew")}
    try:
        check_deadline(start, policy, "evaluation setup")
        observations, info = adapter.reset()
        states = np.asarray(info["state"], dtype=np.float64)
        observations = np.asarray(observations, dtype=np.float32)
        env_steps, dones = np.zeros(lanes, dtype=int), np.zeros(lanes, dtype=bool)
        if policy == "G":
            controller.reset(adapter.host)
        else:
            controller.train(False)
            reset_lanes()
        with torch.no_grad():
            for t in range(horizon):
                check_deadline(start, policy, "evaluation")
                if policy == "G":
                    roles, applied = controller.act(adapter.host, t)
                    summary["counts"]["greedy_act_batches"] += 1
                    actions, internal = np.eye(adapter.config.n_roles, dtype=np.float32)[roles], None
                else:
                    actions, _, data = controller.step(states, observations, env_steps, dones,
                                                       deterministic=True, return_step_data=True,
                                                       build_infos=False)
                    summary["counts"]["evaluation_agent_step_batches"] += 1
                    require_finite(actions, "evaluation actions")
                    internal = np.array(data["d2_sampled_mask"], dtype=bool, copy=True)
                    applied = applied_mask(policy, internal, adapter.host, env_steps)
                observations, _, term, trunc, info = adapter.step(actions, renew_mask=applied)
                result["steps_per_lane"] += 1
                summary["counts"]["scoring_steps"] += lanes
                summary["counts"]["agent_observations"] += lanes * n
                dones = np.broadcast_to(np.asarray(term) | np.asarray(trunc), (lanes,)).copy()
                result["completed_episodes"] += int(dones.sum())
                summary["counts"]["evaluation_episodes"] += int(dones.sum())
                rewards = np.asarray(info["shared_reward"], dtype=np.float64).reshape(lanes)
                require_finite(rewards, "evaluation native reward")
                renew = np.asarray(info["renew_mask"], dtype=bool)
                eligible = ~renew & np.asarray(info["lease_fresh"], dtype=bool)
                wrong = eligible & ~np.asarray(info["role_correct"], dtype=bool)
                values = {"return": rewards, "eligible": eligible.sum(1), "wrong": wrong.sum(1),
                          "applied_renew": renew.sum(1)}
                if internal is not None:
                    values["internal_renew"] = internal.sum(1)
                for key, value in values.items():
                    sums[key][0] += value
                    if t > 0:
                        sums[key][1] += value
                result["valid_reward_steps_per_lane"] += 1
                result["partial_sums"] = {key: value.tolist() for key, value in sums.items()
                                          if not (key == "internal_renew" and policy == "G")}
                states = np.asarray(info["state"], dtype=np.float64)
                observations = np.asarray(observations, dtype=np.float32)
                env_steps += 1
                publish(out, summary, start, f"evaluation batch {t + 1}")
        if result["completed_episodes"] != lanes:
            raise ValueError("evaluation has missing terminal episodes")
        result["status"] = "complete"
    finally:
        complete = result["status"] == "complete"
        for i, (suffix, denominator) in enumerate((("full", horizon), ("post", horizon - 1))):
            result["return_" + suffix] = (sums["return"][i] / denominator).tolist() if complete else None
            for key in ("eligible", "wrong", "internal_renew", "applied_renew"):
                result[key + "_" + suffix] = None if key == "internal_renew" and policy == "G" else sums[key][i].tolist()
            wrong, eligible = sums["wrong"][i], sums["eligible"][i]
            result["wrong_rate_" + suffix] = [float(w / e) if e else None for w, e in zip(wrong, eligible)]
            result["role_loss_" + suffix] = (adapter.config.delta * wrong / (denominator * n)).tolist() if complete else None
            w, e = int(wrong.sum()), int(eligible.sum())
            result["pooled_" + suffix] = {"wrong": w, "eligible": e, "wrong_rate": w / e if e else None}


def final_evaluation(policy, corridor, learner, overrides, summary, out, start, *,
                     training_seed=SEED, evaluation_master=EVAL_MASTER):
    # Construction, synchronization, lane reset AND scoring are all isolated.
    with e0._preserve_rng():
        check_deadline(start, policy, "evaluator construction")
        evaluator = CorridorEvaluator(corridor, overrides, chunk=EVAL_LANES,
                                      master_seed=evaluation_master, log_dir=out / "evaluation_logs", seed=training_seed)
        summary["counts"]["model_constructions"] += 1
        check_deadline(start, policy, "evaluator constructed")
        evaluator._sync(learner)
        counters = {name: e0._StepCounter(getattr(evaluator.agent, name + "_optimizer")) for name in NETWORKS}
        publish(out, summary, start, "evaluator synchronized")
        try:
            evaluate(policy, evaluator.adapter, evaluator.agent, summary, out, start, evaluator._reset_lanes)
        finally:
            summary["evaluation_optimizer_calls"] = {name: counter.count for name, counter in counters.items()}
        check_deadline(start, policy, "evaluation completed")


def paired_statistics(a, b):
    differences = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    return {"differences": differences.tolist(), "mean": float(differences.mean()),
            "stderr": float(differences.std(ddof=1) / np.sqrt(differences.size))}


def completed_arm(summary, policy):
    if summary["policy"] != policy or summary["status"] != "complete":
        raise ValueError(f"{policy} arm incomplete")
    counts, evaluation = summary["counts"], summary["evaluation"]
    horizon = summary["host"]["H"]
    if policy != "G" and (counts["update_stages"] != ROLLOUTS or
                          counts["training_transitions"] != ROLLOUTS * TRAIN_LANES * horizon or
                          len(summary["training_rows"]) != ROLLOUTS or
                          not all(row["updated"] for row in summary["training_rows"])):
        raise ValueError(f"{policy} missing required learning")
    if (evaluation["status"] != "complete" or evaluation["episode_ids"] != list(range(EVAL_LANES))
            or evaluation["valid_reward_steps_per_lane"] != horizon
            or evaluation["completed_episodes"] != EVAL_LANES):
        raise ValueError(f"{policy} missing endpoint")
    for suffix in ("full", "post"):
        values = np.asarray(evaluation["return_" + suffix], dtype=np.float64)
        if values.shape != (EVAL_LANES,) or not np.isfinite(values).all():
            raise ValueError(f"{policy} damaged primary returns")


def summarize_panel(h, c, g=None):
    for name, arm in (("H", h), ("C", c)):
        completed_arm(arm, name)
    for key in ("object_id", "seed", "training_master", "evaluation_master", "host", "episode_ids",
                "learner_config", "device", "torch_threads", "learner_precision"):
        if h[key] != c[key]:
            raise ValueError(f"learned pair mismatch: {key}")
    paired = {"h_minus_c_" + suffix: paired_statistics(h["evaluation"]["return_" + suffix],
                                                      c["evaluation"]["return_" + suffix])
              for suffix in ("full", "post")}
    result = {"status": "complete", "independent_training_pairs": 1, "paired": paired,
              "reference_status": "incomplete", "reference_failure": "G unavailable"}
    if g is not None:
        try:
            completed_arm(g, "G")
            for key in ("object_id", "evaluation_master", "host", "episode_ids"):
                if h[key] != g[key]:
                    raise ValueError(f"reference mismatch: {key}")
            for suffix in ("full", "post"):
                for name, arm in (("h", h), ("c", c)):
                    paired[f"g_minus_{name}_{suffix}"] = paired_statistics(
                        g["evaluation"]["return_" + suffix], arm["evaluation"]["return_" + suffix])
                residual = np.asarray(paired["g_minus_h_" + suffix]["differences"]) - np.asarray(h["evaluation"]["role_loss_" + suffix])
                result["g_minus_h_less_h_role_loss_" + suffix] = {"values": residual.tolist(), "mean": float(residual.mean())}
            result["reference_status"], result["reference_failure"] = "complete", None
        except (KeyError, TypeError, ValueError) as exc:
            result["reference_failure"] = str(exc)
    mean = paired["h_minus_c_full"]["mean"]
    result["card_reading"] = "above_mei" if mean > .01 else "opposite_sign" if mean < -.01 else "small_or_resolution_limited"
    return result


def main(argv=None, *, training_seed=SEED, evaluation_master=EVAL_MASTER,
         object_id=OBJECT_ID, card=CARD):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=("G", "C", "H"), required=True)
    parser.add_argument("--seed", type=int, choices=(training_seed,), required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--c-summary", type=Path)
    parser.add_argument("--g-summary", type=Path)
    args = parser.parse_args(argv)
    if args.policy != "H" and (args.c_summary or args.g_summary):
        parser.error("only H reads existing comparison summaries")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    corridor = proposal_config("large")
    summary = base_summary(args.policy, corridor, args.launch_sha, training_seed=args.seed,
                           evaluation_master=evaluation_master, object_id=object_id, card=card)
    try:
        publish(out, summary, PROCESS_START, "setup")
        if args.policy == "G":
            adapter = RelayCorridorAdapter(corridor, num_envs=EVAL_LANES, master_seed=evaluation_master,
                                          episode_ids=list(range(EVAL_LANES)), squeeze_batch=False)
            evaluate("G", adapter, GreedyOnPublicState(), summary, out, PROCESS_START)
        else:
            adapter, learner, overrides, theta0, counters = build_learner(
                corridor, out, summary, PROCESS_START, training_seed=args.seed)
            publish(out, summary, PROCESS_START, "learner constructed")
            collect_training(args.policy, adapter, learner, summary, theta0, counters, out, PROCESS_START)
            final_evaluation(args.policy, corridor, learner, overrides, summary, out, PROCESS_START,
                             training_seed=args.seed, evaluation_master=evaluation_master)
        summary["status"] = "complete"
        if args.policy == "H":
            g, reference_failure = None, None
            try:
                if args.g_summary:
                    g = json.loads(args.g_summary.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                reference_failure = str(exc)
            try:
                c = json.loads(args.c_summary.read_text(encoding="utf-8")) if args.c_summary else None
                if c is None:
                    raise ValueError("C unavailable")
                summary["panel"] = summarize_panel(summary, c, g)
                if reference_failure:
                    summary["panel"]["reference_failure"] = reference_failure
            except (OSError, KeyError, TypeError, ValueError) as exc:
                summary["panel"] = {"status": "incomplete", "failure": str(exc)}
            summary["comparison_inputs"] = {"C": str(args.c_summary), "G": str(args.g_summary)}
        try:
            if sys.platform == "win32":
                rss = peak_rss_bytes()
            else:
                import resource
                rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024))
            summary["peak_rss_bytes"] = rss
        except (ImportError, OSError):
            summary["peak_rss_bytes"] = None
        publish(out, summary, PROCESS_START, "final")
    except Exception as exc:
        summary["status"], summary["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
        summary.pop("panel", None)
        # Failure publication retains measured boundaries; it does not extend the cap.
        summary["wall_seconds_before_publication"] = time.perf_counter() - PROCESS_START
        write_summary(out, summary)
    success = summary["status"] == "complete" and summary.get("panel", {}).get("status", "complete") == "complete"
    print(json.dumps({"status": summary["status"], "failure": summary["failure"],
                      "wall_seconds_after_publication": time.perf_counter() - PROCESS_START}))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
