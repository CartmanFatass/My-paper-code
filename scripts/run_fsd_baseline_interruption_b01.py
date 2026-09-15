"""FSD baseline x interruption B01: FLAT / D1280 / I1280 fits with three panels, and the readout.

Every fit runs the frozen collector loop for 15 rollouts and evaluates the same 32-world panel
after rollouts 5, 10 and 15 from one evaluator, inside the RNG-preserving wrapper. FLAT is the
private-actor flat reduction of the same HMASD stack: the ordinary `off` configuration with the
hmasd.baselines "mappo" switch applied (Portfolio decision 2026-09-15, option S: four blocks).
Ordinary wall plans are not deadlines. No retry, extra endpoint, tuning or successor fit.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import torch

import run_fsd_uav_individual_renewal_b01 as shared
from hmasd.baselines import apply_algorithm_config

OBJECT_ID = "FSD_BASELINE_INTERRUPTION_B01"
CARD = ("docs/research/candidates/flexible_skill_duration/"
        "FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md")
BLOCKS = {772203: 782203, 772303: 782303, 772403: 782403, 772503: 782503}
ARMS = {"FLAT": ("FLAT", None), "D1280": ("D0", 1280), "I1280": ("I", 1280)}
ROLLOUTS = 15
PANEL_ROLLOUTS = (5, 10, 15)
WALL_PLANS = {"FLAT": 1600., "D1280": 1800., "I1280": 4000.}
PRIMARY, PRIMARY_MEI = "SI1280", .05
CONTRASTS = {"SI1280": {"I1280": 1., "D1280": -1.}, "GAP_D": {"D1280": 1., "FLAT": -1.}, "GAP_I": {"I1280": 1., "FLAT": -1.}}
CONTRAST_MEANING = {
    "SI1280": "high-batch renewal simple effect; primary at rollout 15",
    "GAP_D": "untuned cross-information package gap D1280 minus FLAT; not section 11.7 headroom",
    "GAP_I": "untuned cross-information package gap I1280 minus FLAT; not section 11.7 headroom"}
# Configuration fields that differ between arms by design; any other difference invalidates a contrast.
PLANNED_CONFIG_DIFFERENCES = frozenset({
    "interruption_cost_c", "coordinator_batch_size", "n_Z", "n_z", "k", "policy_interruption_mode",
    "interruption_delta", "interruption_cost_c_Z", "skill_cap_k_max", "team_cap_k_Z", "age_feature",
    "lambda_D", "lambda_d", "lambda_h", "high_level_buffer_size", "high_level_batch_size", "use_process_exploration"})
FLAT_ONLY_ZERO = ("coordinator", "team_discriminator", "individual_discriminator")
FLAT_K = 10  # identical recurrent chunk length and skill period to the D arms; one constant skill
T975 = {1: 12.7062, 2: 4.3027, 3: 3.1824, 4: 2.7764, 5: 2.5706, 6: 2.4469, 7: 2.3646, 8: 2.3060}


def make_config(arm, envs, seed):
    renewal, batch = ARMS[arm]
    if arm == "FLAT":
        # Ordinary `off` route, then the flat switch: constant single skill with the switch-selected long k,
        # no coordinator/discriminator training, private recurrent actor and central-state critic.
        config = shared.e0._make_config("off", seed, len(envs), shared.HORIZON, shared.HORIZON, shared.N_UAVS,
                                        shared.N_USERS, shared.ROLLOUTS, envs[0].state_dim, envs[0].obs_dim)
        config.n_Z = config.n_z = 6  # the switch below fixes both to 1; start from the ordinary value
        config = apply_algorithm_config(config, "mappo")
        # DM deviation from the Portfolio decision's "switch-selected long k" (recorded on the card, returned
        # to the node): the switch's k = rollout_length + 1 does run (the sampler falls back to one
        # full-rollout chunk, hmasd/utils.py get_discoverer_sampler), but config.k is also the truncated-BPTT
        # chunk length of the recurrent actor and critic (hmasd/agent.py update_discoverer_from_rollout), so
        # the long k would train FLAT through 500-step chunks against the D arms' 10-step chunks and confound
        # the architecture contrast with the gradient-truncation law. k = 10 keeps the optimizer law identical;
        # with one constant skill the ten-step re-assignment is degenerate (the coordinator is still
        # forward-called, never updated). The switch computed the high-level buffer fields at its own k;
        # they are inert (nothing is collected into that buffer) and listed as planned differences.
        config.k = FLAT_K
        return config
    return shared.make_config(renewal, envs, seed, coordinator_batch_size=batch)


def renewal_metrics(agent):
    """D2 renewal metrics where the arm has them; the FLAT arm runs the `off` route and has none."""
    if getattr(agent, "d2_metrics", None) is None:
        return {"d2_metrics": None, "segments": None}
    return shared.renewal_metrics(agent)


def build_learner(arm, summary, out, training_seed):
    shared.check_deadline(summary, "learner setup")
    torch.set_num_threads(4)
    shared.seed_rng(training_seed)
    envs = shared.e0._make_envs(shared.TRAIN_LANES, training_seed, shared.N_UAVS, shared.N_USERS, shared.HORIZON)
    config = make_config(arm, envs, training_seed)
    summary["learner_config"] = shared.config_snapshot(config)
    agent = shared.HMASDAgent(config, log_dir=str(out / "learner_logs"), device=torch.device("cpu"))
    summary["counts"]["model_constructions"] += 1
    summary["counts"]["training_starts"] += 1
    theta0 = shared.e0._capture_theta0(agent)
    summary["initial_parameter_norms"] = shared.measured({k: v["norm"] for k, v in theta0.items()}, "initial parameters")
    counters = shared.optimizer_counters(agent)
    summary["optimizer_present"] = {k: v is not None for k, v in counters.items()}
    shared.publish(out, summary, "learner constructed")
    return envs, agent, theta0, counters


def collect_training(envs, agent, theta0, counters, summary, out, *, rollouts, panel=None):
    """The frozen B01 collector loop with the rollout count as a parameter and a post-rollout panel hook."""
    lanes, horizon, n_uavs = shared.TRAIN_LANES, shared.HORIZON, shared.N_UAVS
    states, observations = shared.e0._reset_all(envs)
    shared.require_finite((states, observations), "training reset inputs")
    env_steps, dones = np.zeros(lanes, dtype=int), np.zeros(lanes, dtype=bool)
    agent.train(True)
    for rollout in range(rollouts):
        before = shared.optimizer_counts(counters)
        row = {"rollout_index": rollout, "transitions": 0, "stored_transitions": 0,
               "completed_episodes": 0, "stored_batches": 0, "updated": False,
               "return_sums": [0.] * lanes, "episode_returns_U": None,
               "optimizer_calls_before": before}
        summary["training_rows"].append(row)
        returns = np.zeros(lanes, dtype=np.float64)
        for t in range(horizon):
            shared.check_deadline(summary, "training collection")
            actions, _, data = agent.step(states, observations, env_steps, dones,
                                         deterministic=False, return_step_data=True, build_infos=False)
            summary["counts"]["training_agent_step_batches"] += 1
            shared.require_finite(actions, "training actions")
            shared.require_finite(data, "sampled step data")
            next_states, next_observations = [], []
            rewards, next_dones = np.zeros(lanes, dtype=np.float64), np.zeros(lanes, dtype=bool)
            for lane, env in enumerate(envs):
                obs, reward, term, trunc, info = env.step(actions[lane])
                summary["counts"]["training_transitions"] += 1
                row["transitions"] += 1
                next_dones[lane] = bool(term or trunc)
                row["completed_episodes"] += int(next_dones[lane])
                summary["counts"]["training_episodes"] += int(next_dones[lane])
                shared.require_finite(reward, "training scalar reward")
                rewards[lane] = reward  # Never multiply learner rewards by the reporting factor.
                returns[lane] += reward
                row["return_sums"] = returns.tolist()
                next_states.append(np.asarray(info["next_state"], dtype=np.float64))
                next_observations.append(np.asarray(obs, dtype=np.float32))
            next_states, next_observations = np.stack(next_states), np.stack(next_observations)
            shared.require_finite((next_states, next_observations), "training next inputs")
            agent.store_transition_batch(states=states, next_states=next_states.copy(), observations=observations,
                next_observations=next_observations.copy(), actions=actions, rewards=rewards, dones=next_dones,
                infos_batch=None, rollout_step_idx=t, step_data=data)
            row["stored_transitions"] += lanes
            row["stored_batches"] += 1
            summary["counts"]["stored_training_transitions"] += lanes
            # Storage already owns terminal next values; both subsequent inputs must be fresh.
            for lane, env in enumerate(envs):
                if next_dones[lane]:
                    reset_obs, reset_info = env.reset()
                    next_observations[lane] = np.asarray(reset_obs, dtype=np.float32)
                    next_states[lane] = np.asarray(reset_info["state"], dtype=np.float64)
                    shared.require_finite((next_states[lane], next_observations[lane]), "training reset inputs")
                    agent.reset_env_state(lane)
                    env_steps[lane] = 0
                else:
                    env_steps[lane] += 1
            states, observations, dones = next_states, next_observations, next_dones
        if not dones.all() or row["completed_episodes"] != lanes:
            raise ValueError("training rollout does not contain the required full terminal episodes")
        row["episode_returns_U"] = shared.measured(returns, "training returns")
        shared.publish(out, summary, f"rollout {rollout} collected")
        # All lanes are terminal. Zero bootstrap requires no extra action/skill sampling.
        try:
            losses = agent.update(last_values=np.zeros((lanes, n_uavs), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=horizon, last_state=states.copy(), last_observations=observations.copy())
            summary["counts"]["update_stages"] += 1
            row["updated"] = True
            row["losses"] = shared.measured(losses, "update losses")
        finally:
            summary["optimizer_calls"] = shared.optimizer_counts(counters)
            row["optimizer_calls_total"] = summary["optimizer_calls"].copy()
            row["optimizer_calls_delta"] = {k: v - before[k] for k, v in summary["optimizer_calls"].items()}
        row.update(renewal_metrics(agent))  # Per-rollout metrics, before ordinary clear.
        row["relative_initialization_displacement"] = shared.measured(shared.e0._exposure_line(agent, theta0), "learner parameters")
        with (out / "training.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
        shared.publish(out, summary, f"rollout {rollout} updated")
        agent.clear_buffers()
        shared.check_deadline(summary, "buffer clear")
        if panel is not None and rollout + 1 in PANEL_ROLLOUTS:
            panel(rollout + 1)


class Evaluator(shared.e0.Evaluator):
    """One evaluator per fit; its panel environments are rebuilt from the same seeds for every panel."""

    def __init__(self, arm, out, evaluation_seed):
        self.lanes = shared.EVAL_LANES
        self.envs = shared.e0._make_envs(shared.EVAL_LANES, evaluation_seed, shared.N_UAVS, shared.N_USERS, shared.HORIZON)
        self.config = make_config(arm, self.envs, evaluation_seed)
        self.agent = shared.HMASDAgent(self.config, log_dir=str(out / "evaluation_logs"), device=torch.device("cpu"))
        self.agent.train(False)


def build_evaluator(arm, summary, out, evaluation_seed):
    with shared.e0._preserve_rng():
        shared.check_deadline(summary, "evaluator construction")
        shared.seed_rng(evaluation_seed)
        evaluator = Evaluator(arm, out, evaluation_seed)
        summary["counts"]["model_constructions"] += 1
        summary["evaluation_config"] = shared.config_snapshot(evaluator.config)
        shared.publish(out, summary, "evaluator constructed")
    return evaluator


def evaluate_panel(learner, evaluator, summary, out, rollouts_completed):
    lanes, horizon = shared.EVAL_LANES, shared.HORIZON
    with shared.e0._preserve_rng():
        shared.check_deadline(summary, f"panel {rollouts_completed}")
        shared.seed_rng(summary["evaluation_seed"])
        evaluator.envs = shared.e0._make_envs(lanes, summary["evaluation_seed"], shared.N_UAVS, shared.N_USERS, horizon)
        evaluator.agent.clear_buffers()
        evaluator._sync(learner)
        counters = shared.optimizer_counters(evaluator.agent)
        result = {"status": "incomplete", "panel_rollouts": rollouts_completed,
                  "after_update": summary["counts"]["update_stages"],
                  "episode_ids": list(range(lanes)), "lane_seeds": summary["evaluation_lane_seeds"],
                  "steps_per_lane": [0] * lanes, "completed_episodes": 0,
                  "return_sums_U": [0.] * lanes, "returns_U": None, "native_scores_J": None}
        summary["panels"].append(result)
        states, observations = shared.e0._reset_all(evaluator.envs)
        shared.require_finite((states, observations), "evaluation reset inputs")
        steps, dones = np.zeros(lanes, dtype=int), np.zeros(lanes, dtype=bool)
        returns = np.zeros(lanes, dtype=np.float64)
        components = {k: np.zeros(lanes, dtype=np.float64) for k in shared.COMPONENTS}
        try:
            with torch.no_grad():
                for t in range(horizon):
                    shared.check_deadline(summary, f"panel {rollouts_completed} evaluation")
                    actions, _, data = evaluator.agent.step(states, observations, steps, dones,
                                                            deterministic=True, return_step_data=True, build_infos=False)
                    summary["counts"]["evaluation_agent_step_batches"] += 1
                    shared.require_finite(actions, "evaluation actions")
                    shared.require_finite(data, "evaluation sampled data")
                    for lane, env in enumerate(evaluator.envs):
                        obs, reward, term, trunc, info = env.step(actions[lane])
                        summary["counts"]["evaluation_steps"] += 1
                        result["steps_per_lane"][lane] += 1
                        dones[lane] = bool(term or trunc)
                        result["completed_episodes"] += int(dones[lane])
                        summary["counts"]["evaluation_episodes"] += int(dones[lane])
                        shared.require_finite(reward, "evaluation scalar reward")
                        returns[lane] += reward
                        result["return_sums_U"] = returns.tolist()
                        values = {k: info["reward_components"]["reward_info"][k] for k in shared.COMPONENTS}
                        shared.require_finite(values, "native reward components")
                        for key, value in values.items():
                            components[key][lane] += value
                        states[lane] = np.asarray(info["next_state"], dtype=np.float64)
                        observations[lane] = np.asarray(obs, dtype=np.float32)
                        shared.require_finite((states[lane], observations[lane]), "evaluation next inputs")
                    result["component_sums"] = {k: v.tolist() for k, v in components.items()}
                    steps += 1
                    if dones.any() and (t != horizon - 1 or not dones.all()):
                        raise ValueError("evaluation has an unexpected terminal boundary")
            if not dones.all():
                raise ValueError("evaluation missing terminal episodes")
            result.update(renewal_metrics(evaluator.agent))
            result["returns_U"] = shared.measured(returns, "primary scalar returns")
            result["native_scores_J"] = shared.measured(shared.N_UAVS * returns / horizon, "primary native scores")
            result["component_means"] = shared.measured({k: v / horizon for k, v in components.items()}, "native components")
            result["status"] = "complete"
        finally:
            result["evaluator_optimizer_calls"] = shared.optimizer_counts(counters)
            if rollouts_completed == ROLLOUTS:
                summary["evaluation"] = result
                summary["evaluation_optimizer_calls"] = result["evaluator_optimizer_calls"]
        shared.publish(out, summary, f"panel {rollouts_completed}")


def run_fit(arm, seed, out):
    renewal, batch = ARMS[arm]
    evaluation_seed = BLOCKS[seed]
    summary = shared.base_summary(renewal, training_seed=seed, evaluation_seed=evaluation_seed,
                                  object_id=OBJECT_ID, card=CARD, caps=None)
    summary.update(factorial_arm=arm, block_seed=seed, ordinary_wall_plan_seconds=WALL_PLANS[arm],
                   cost_law="15 * sum_rollout ceil(valid_joint_rows / coordinator_batch_size); FLAT 0",
                   coordinator_batch_size=batch, rollouts=ROLLOUTS, panel_rollouts=list(PANEL_ROLLOUTS), panels=[])
    out.mkdir(parents=True, exist_ok=True)
    try:
        shared.write_json(out / "manifest.json", {k: v for k, v in summary.items()
                          if k not in ("status", "failure", "training_rows", "evaluation", "counts", "panels")})
        shared.publish(out, summary, "setup")
        envs, learner, theta0, counters = build_learner(arm, summary, out, seed)
        evaluator = build_evaluator(arm, summary, out, evaluation_seed)
        collect_training(envs, learner, theta0, counters, summary, out, rollouts=ROLLOUTS,
                         panel=lambda completed: evaluate_panel(learner, evaluator, summary, out, completed))
        summary["status"] = "complete"
        try:
            if shared.sys.platform == "win32":
                import psutil
                summary["peak_rss_bytes"] = int(psutil.Process().memory_info().peak_wset)
            else:
                import resource
                summary["peak_rss_bytes"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss *
                                                (1 if shared.sys.platform == "darwin" else 1024))
        except (ImportError, OSError):
            summary["peak_rss_bytes"] = None
        shared.publish(out, summary, "final")
    except Exception as exc:
        summary["status"], summary["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
        shared.write_json(out / "summary.json", summary)
    print(json.dumps({"arm": arm, "seed": seed, "status": summary["status"], "failure": summary["failure"]}))
    return 0 if summary["status"] == "complete" else 1


def arm_panels(summary):
    """Read a complete fit's three panels; failures limit its dependent contrasts only."""
    seed, arm = summary["block_seed"], summary["factorial_arm"]
    renewal, batch = ARMS[arm]
    evaluation_seed = BLOCKS[seed]
    lanes, horizon = shared.EVAL_LANES, shared.HORIZON
    if (summary["object_id"] != OBJECT_ID or summary["card"] != CARD or summary["arm"] != renewal
            or summary["status"] != "complete" or summary["training_seed"] != seed
            or summary["evaluation_seed"] != evaluation_seed or summary["rollouts"] != ROLLOUTS
            or summary["panel_rollouts"] != list(PANEL_ROLLOUTS)):
        raise ValueError("incomplete or wrong arm/block/object")
    counts = summary["counts"]
    expected_counts = {
        "model_constructions": 2, "training_starts": 1, "checkpoint_loads": 0,
        "training_transitions": shared.TRAIN_LANES * horizon * ROLLOUTS,
        "stored_training_transitions": shared.TRAIN_LANES * horizon * ROLLOUTS,
        "training_episodes": shared.TRAIN_LANES * ROLLOUTS, "update_stages": ROLLOUTS,
        "training_agent_step_batches": horizon * ROLLOUTS,
        "evaluation_steps": lanes * horizon * len(PANEL_ROLLOUTS),
        "evaluation_agent_step_batches": horizon * len(PANEL_ROLLOUTS),
        "evaluation_episodes": lanes * len(PANEL_ROLLOUTS)}
    if any(counts[k] != v for k, v in expected_counts.items()):
        raise ValueError("incomplete training/panel exposure")
    rows = summary["training_rows"]
    if (len(rows) != ROLLOUTS or [r["rollout_index"] for r in rows] != list(range(ROLLOUTS))
            or not all(r["updated"] for r in rows)
            or any(summary["optimizer_calls"][k] <= 0 for k in ("discoverer_actor", "discoverer_critic"))):
        raise ValueError("missing learner updates")
    if arm == "FLAT":
        if any(summary["optimizer_calls"][k] != 0 for k in FLAT_ONLY_ZERO):
            raise ValueError("FLAT trained a coordinator or discriminator")
    elif summary["optimizer_calls"]["coordinator"] <= 0:
        raise ValueError("renewal arm without coordinator updates")
    for key, count, phase_seed in (("learner_config", shared.TRAIN_LANES, seed),
                                   ("evaluation_config", lanes, evaluation_seed)):
        config = summary[key]
        expected = {"n_agents": shared.N_UAVS, "n_users": shared.N_USERS, "num_envs": count,
                    "rollout_length": horizon, "seed": phase_seed}
        if arm == "FLAT":
            expected.update(policy_interruption_mode="off", n_Z=1, n_z=1, k=FLAT_K,
                            lambda_D=0., lambda_d=0., lambda_h=0., use_process_exploration=False)
        else:
            expected.update(policy_interruption_mode="d2", interruption_cost_c_Z="Infinity", interruption_delta=1,
                            age_feature="off", n_Z=6, n_z=6, k=10, skill_cap_k_max=10, team_cap_k_Z=10,
                            coordinator_batch_size=batch, interruption_cost_c=.25 if renewal == "I" else "Infinity")
        if any(config.get(k) != v for k, v in expected.items()):
            raise ValueError("arm construction mismatch: " + key)
    if (summary["training_lane_seeds"] != list(range(seed, seed + shared.TRAIN_LANES))
            or summary["evaluation_lane_seeds"] != list(range(evaluation_seed, evaluation_seed + lanes))
            or [p["panel_rollouts"] for p in summary["panels"]] != list(PANEL_ROLLOUTS)):
        raise ValueError("wrong lane seeds or panel schedule")
    scores = {}
    for panel in summary["panels"]:
        if (panel["status"] != "complete" or panel["after_update"] != panel["panel_rollouts"]
                or panel["episode_ids"] != list(range(lanes)) or panel["lane_seeds"] != summary["evaluation_lane_seeds"]
                or panel["steps_per_lane"] != [horizon] * lanes or panel["completed_episodes"] != lanes
                or any(panel["evaluator_optimizer_calls"].values())):
            raise ValueError(f"wrong panel {panel['panel_rollouts']}")
        values = np.asarray(panel["native_scores_J"], dtype=np.float64)
        returns = np.asarray(panel["returns_U"], dtype=np.float64)
        if values.shape != (lanes,) or returns.shape != values.shape:
            raise ValueError("missing primary values")
        shared.require_finite((values, returns), "panel primary")
        if not np.allclose(returns * shared.N_UAVS / horizon, values, rtol=1e-9, atol=1e-9):
            raise ValueError("native return scaling mismatch")
        scores[panel["panel_rollouts"]] = values
    return scores


def block_statistics(values, planned):
    count = len(values)
    mean = float(np.mean(values)) if count else None
    sd = float(np.std(values, ddof=1)) if count >= 2 else None
    se = sd / math.sqrt(count) if sd is not None else None
    half = T975[count - 1] * se if se is not None and count - 1 in T975 else None
    return {"available_training_blocks": count, "planned_training_blocks": planned, "mean": mean,
            "sample_sd": sd, "se": se,
            "working_model_95pct_interval": [mean - half, mean + half] if half is not None else None,
            "working_model": f"iid-normal block contrasts; Student-t df={count - 1}; assumptions uncheckable at small n, "
                             "coverage not established"}


def comparable_view(summary):
    common = {k: summary[k] for k in ("host", "device", "torch_threads", "learner_precision",
                                      "reward_return_precision", "native_score_factor", "rollouts", "panel_rollouts",
                                      "launch_sha")}
    for phase in ("learner_config", "evaluation_config"):
        common[phase] = {k: v for k, v in summary[phase].items() if k not in PLANNED_CONFIG_DIFFERENCES}
    return common


def assemble_blocks(summaries, historical_si1280_5=()):
    supplied = {}
    for summary in summaries:
        key = (summary["block_seed"], summary["factorial_arm"])
        if key[0] not in BLOCKS or key[1] not in ARMS or key in supplied:
            raise ValueError("unselected or duplicate original arm/block")
        supplied[key] = summary
    blocks = []
    values = {name: {r: [] for r in PANEL_ROLLOUTS} for name in CONTRASTS}
    for seed in BLOCKS:
        panels, failures, rows = {}, {}, {}
        for arm in ARMS:
            result = supplied.get((seed, arm))
            if result is None:
                failures[arm] = "not supplied"
                continue
            try:
                panels[arm] = arm_panels(result)
                rows[arm] = {"J_by_rollout": {str(r): float(v.mean()) for r, v in panels[arm].items()},
                             "endpoint_scores_J": panels[arm][ROLLOUTS].tolist(), "launch_sha": result["launch_sha"],
                             "counts": result["counts"], "optimizer_calls": result["optimizer_calls"],
                             "wall_seconds_before_publication": result.get("wall_seconds_before_publication"),
                             "peak_rss_bytes": result.get("peak_rss_bytes")}
            except (KeyError, TypeError, ValueError) as exc:
                failures[arm] = str(exc)
        contrasts = {}
        for name, weights in CONTRASTS.items():
            if not all(arm in panels for arm in weights):
                contrasts[name] = {"status": "incomplete", "missing_operands": [a for a in weights if a not in panels]}
                continue
            views = [comparable_view(supplied[(seed, arm)]) for arm in weights]
            if any(other != views[0] for other in views[1:]):
                contrasts[name] = {"status": "incomplete", "failure": "unplanned comparator difference"}
                continue
            contrasts[name] = {"status": "complete", "by_rollout": {}}
            for r in PANEL_ROLLOUTS:
                differences = sum(weight * panels[arm][r] for arm, weight in weights.items())
                value = float(differences.mean())
                contrasts[name]["by_rollout"][str(r)] = {
                    "value": value, "conditional_episode_sd": float(differences.std(ddof=1)),
                    "conditional_episode_se": float(differences.std(ddof=1) / math.sqrt(shared.EVAL_LANES))}
                values[name][r].append(value)
        blocks.append({"training_seed": seed, "evaluation_seed": BLOCKS[seed], "arms": rows,
                       "missing_or_invalid_arms": failures, "contrasts": contrasts})
    planned = len(BLOCKS)
    aggregate = {name: {str(r): block_statistics(values[name][r], planned) for r in PANEL_ROLLOUTS}
                 for name in CONTRASTS}
    primary = dict(aggregate[PRIMARY][str(ROLLOUTS)], name=f"{PRIMARY}_{ROLLOUTS}", mei_J=PRIMARY_MEI)
    mean, interval = primary["mean"], primary["working_model_95pct_interval"]
    # Importance and uncertainty are reported separately (Portfolio decision 2026-09-15).
    primary["importance_reading"] = (None if mean is None else "locally_substantial_positive" if mean > PRIMARY_MEI
                                     else "adverse" if mean < -PRIMARY_MEI else "small_signed")
    primary["uncertainty_reading"] = (None if interval is None else "interval_excludes_zero"
                                      if interval[0] > 0 or interval[1] < 0 else "interval_includes_zero")
    primary["interval_inside_mei"] = (None if interval is None
                                      else bool(-PRIMARY_MEI < interval[0] and interval[1] < PRIMARY_MEI))
    historical = [float(v) for v in historical_si1280_5]
    new_values = values[PRIMARY][PANEL_ROLLOUTS[0]]
    pooled = block_statistics(new_values + historical, planned + len(historical))
    pooled.update(name=f"{PRIMARY}_{PANEL_ROLLOUTS[0]}_accumulated",
                  new_blocks=block_statistics(new_values, planned),
                  historical_blocks=block_statistics(historical, len(historical)),
                  note="explicitly outcome-informed descriptive accumulation of the rollout-5 primary over the new "
                       "blocks and the completed factorial's two blocks; the five-rollout prefix, evaluation and "
                       "seed semantics are inherited unchanged; not prospective independent confirmation")
    complete = all(s["available_training_blocks"] == planned for by_r in aggregate.values() for s in by_r.values())
    return {"object_id": OBJECT_ID, "card": CARD, "launch_sha": shared.e0._git("rev-parse", "HEAD"),
            "status": "complete" if complete else "incomplete", "blocks": blocks, "contrasts": aggregate,
            "primary": primary, "rollout5_accumulation": pooled, "contrast_meaning": CONTRAST_MEANING,
            "interpretation_limit": "Independent training blocks only; panel worlds are nested endpoint conditions; "
                                    "no equivalence, no selection among panels, no extension without a new decision."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(ARMS), required=True)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--output-root", type=Path, required=True)
    reduce = sub.add_parser("reduce")
    reduce.add_argument("--summaries", type=Path, nargs="+", required=True)
    reduce.add_argument("--historical-factorial-summary", type=Path,
                        help="RESULT_SUMMARY.json of FSD_INTERRUPTION_BATCH_B01 for the rollout-5 pooled replication")
    reduce.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "fit":
        return run_fit(args.arm, args.seed, args.output_root.resolve())
    historical = []
    if args.historical_factorial_summary is not None:
        old = json.loads(args.historical_factorial_summary.read_text(encoding="utf-8"))
        if old.get("object_id") != "FSD_INTERRUPTION_BATCH_B01":
            raise ValueError("historical summary is not the completed factorial")
        historical = [block["contrasts"]["SI1280"]["value"] for block in old["blocks"]
                      if block["contrasts"]["SI1280"].get("status") == "complete"]
    result = assemble_blocks([json.loads(p.read_text(encoding="utf-8")) for p in args.summaries], historical)
    result["input_summaries"] = [str(p) for p in args.summaries]
    result["historical_factorial_summary"] = (str(args.historical_factorial_summary)
                                              if args.historical_factorial_summary else None)
    args.output_root.mkdir(parents=True, exist_ok=True)
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({"status": result["status"], "primary": result["primary"]}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
