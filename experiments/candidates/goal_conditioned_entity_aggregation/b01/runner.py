"""GCEA B01: O/P/E joint learning with one final bounded-execution panel."""
from __future__ import annotations

import sys
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as native
from hmasd.baselines import apply_algorithm_config
from .encoder import OBS_DIM, install_actor_encoder


DIRECTION = "goal_conditioned_entity_aggregation"
OBJECT_ID = "GCEA_B01"
CARD = "docs/research/candidates/goal_conditioned_entity_aggregation/NOTES.md#2026-09-22--b01-prospective-comparison-and-l0"
ARMS = {name: ("D0", 1280) for name in ("O", "P", "E")}
TRAINING_SEED = 922611
EVALUATION_SEED = 923611
BLOCKS = {TRAINING_SEED: EVALUATION_SEED}
ROLLOUTS = 45
PANEL_ROLLOUTS = (45,)
WALL_PLANS = dict.fromkeys(ARMS, 14400.0)
NETWORKS = ("coordinator", "discoverer_actor", "discoverer_critic",
            "team_discriminator", "individual_discriminator")
PLAIN_HMASD_FLAGS = {
    "algorithm": "hmasd",
    "baseline_algorithm": "hmasd",
    "use_horizon_window": False,
    "use_team_bridge": False,
    "use_opt_compact": False,
    "use_compact_in_low_level_actor": False,
    "use_team_code_discriminator": False,
    "discriminator_condition_on_compact": False,
    "discriminator_condition_on_team_code": False,
    "use_process_exploration": False,
    "use_discrete_skill_lifetimes": False,
    "use_process_reward_for_discoverer": False,
    "use_central_snapshot_in_flat_actor": False,
    "disable_high_level_training": False,
    "disable_discriminator_training": False,
    "disable_discriminator_rewards": False,
}
CURRENT = {"arm": None, "admission": None, "summary": None, "learner": None,
           "learner_install": None, "evaluator_install": None,
           "update_seconds": 0.0, "evaluation_seconds": 0.0, "fit_started": None,
           "cpu_started": None, "action_statistics": None}



def _empty_action_statistics():
    return dict(team_steps=0, uav_actions=0, coordinates=0, raw_outside_coordinates=0,
                raw_outside_uav_actions=0, raw_outside_team_steps=0,
                executed_saturated_coordinates=0, executed_saturated_uav_actions=0,
                executed_saturated_team_steps=0, raw_max_abs=0.0, raw_abs_excess_sum=0.0,
                position_observed_coordinates=0, position_absorbed_coordinates=0,
                position_observed_uav_actions=0, position_absorbed_uav_actions=0,
                position_observed_team_steps=0, position_absorbed_team_steps=0,
                position_request_difference_max=0.0)


class BoundedExecutionEnv:
    """Map a separate action copy at the only environment execution boundary.

    Raw policy samples remain the collector/storage/PPO variables. These counters observe
    already-produced samples/positions and make no random draws or actor inputs.
    """

    def __init__(self, env, statistics):
        self.wrapped_env = env
        self.statistics = statistics

    def __getattr__(self, name):
        return getattr(self.wrapped_env, name)

    def reset(self, *args, **kwargs):
        return self.wrapped_env.reset(*args, **kwargs)

    def step(self, actions):
        raw = np.asarray(actions)
        if raw.ndim != 2 or raw.shape != (self.n_uavs, 3) or not np.isfinite(raw).all():
            raise ValueError("bounded execution requires one finite raw 3-vector per UAV")
        executed = np.clip(raw.copy(), -1.0, 1.0)
        # Capture the executed command before a downstream adapter is allowed to touch it.
        observed_execution = executed.copy()
        physical = getattr(self.wrapped_env, "env", None)
        before = getattr(physical, "uav_positions", None)
        intended = None
        if before is not None and hasattr(physical, "max_speed") and hasattr(physical, "time_step"):
            intended = np.asarray(before).copy() + observed_execution * physical.max_speed * physical.time_step
        result = self.wrapped_env.step(executed)
        stats = self.statistics
        outside = np.abs(raw) > 1.0
        saturated = np.abs(observed_execution) >= 1.0
        stats["team_steps"] += 1
        stats["uav_actions"] += raw.shape[0]
        stats["coordinates"] += raw.size
        stats["raw_outside_coordinates"] += int(outside.sum())
        stats["raw_outside_uav_actions"] += int(outside.any(axis=-1).sum())
        stats["raw_outside_team_steps"] += int(outside.any())
        stats["executed_saturated_coordinates"] += int(saturated.sum())
        stats["executed_saturated_uav_actions"] += int(saturated.any(axis=-1).sum())
        stats["executed_saturated_team_steps"] += int(saturated.any())
        stats["raw_max_abs"] = max(stats["raw_max_abs"], float(np.abs(raw).max()))
        stats["raw_abs_excess_sum"] += float(np.maximum(np.abs(raw) - 1.0, 0.0).sum())
        after = getattr(physical, "uav_positions", None)
        if intended is not None and after is not None:
            error = np.abs(np.asarray(after) - intended)
            absorbed = error > 1e-8
            stats["position_observed_coordinates"] += raw.size
            stats["position_absorbed_coordinates"] += int(absorbed.sum())
            stats["position_observed_uav_actions"] += raw.shape[0]
            stats["position_absorbed_uav_actions"] += int(absorbed.any(axis=-1).sum())
            stats["position_observed_team_steps"] += 1
            stats["position_absorbed_team_steps"] += int(absorbed.any())
            stats["position_request_difference_max"] = max(stats["position_request_difference_max"], float(error.max()))
        return result


def make_bounded_envs(count, base_seed, n_uavs, n_users, episode_length):
    if base_seed not in (TRAINING_SEED, EVALUATION_SEED):
        raise ValueError("GCEA B01 only constructs the declared training/evaluation worlds")
    phase = "train" if base_seed == TRAINING_SEED else "evaluation"
    statistics = CURRENT["action_statistics"][phase]
    envs = _ORIGINALS["make_envs"](count, base_seed, n_uavs, n_users, episode_length)
    return [BoundedExecutionEnv(env, statistics) for env in envs]


def plan_guard(arm: str, seed: int) -> None:
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm}")
    if seed != TRAINING_SEED:
        raise SystemExit(f"B01 fixes training seed {TRAINING_SEED}")


def make_config(arm, envs, seed):
    config = _ORIGINALS["make_config"](arm, envs, seed)
    apply_algorithm_config(config, "hmasd")
    for name, value in PLAIN_HMASD_FLAGS.items():
        setattr(config, name, value)
    if getattr(config, "continuous_action_distribution", "gaussian") != "gaussian":
        raise RuntimeError("GCEA B01 retains the original raw Gaussian distribution")
    if (config.policy_interruption_mode != "d2"
            or config.interruption_cost_c != float("inf")
            or config.interruption_cost_c_Z != float("inf")
            or config.k != 10 or config.skill_cap_k_max != 10 or config.team_cap_k_Z != 10
            or config.coordinator_batch_size != 1280 or config.n_Z != 6 or config.n_z != 6):
        raise RuntimeError("GCEA B01 did not construct the standing D1280 full-HMASD configuration")
    return config


def base_summary(*args, **kwargs):
    summary = _ORIGINALS["base_summary"](*args, **kwargs)
    summary.update(
        goal_conditioned_entity_aggregation_object=OBJECT_ID,
        encoder_arm=CURRENT["arm"],
        admission=CURRENT["admission"],
        observation_contract={
            "dimension": OBS_DIM,
            "layout": "self_xyz; 20*(relative_xy,SINR); 10*(relative_xyz,SINR); time",
            "slot_order": "environment SINR rank; rank is not persistent identity",
            "zero_slots": "participate without a truth mask",
        },
        action_execution={"sample_and_score": "original raw Gaussian u", "environment": "clip(u.copy(),-1,1)",
                          "deterministic": "clip(mu,-1,1)", "coordinate_box_not_euclidean_speed_bound": True,
                          "no_new_entropy_or_logstd_rule": True},
        action_statistics=CURRENT["action_statistics"],
        scientific_scope="one training instance per arm; package comparison, no E/L or semantic attribution",
        parameter_counts=None,
        actor_timing=None,
        phase_wall_seconds={"total": 0.0, "collection": 0.0, "update": 0.0,
                            "evaluation": 0.0},
        output_meaning={
            "native_scores_J": "per-world N*scalar episode return/500",
            "coverage_reward": "coverage fraction; multiply by 50 for connected users",
            "quality_reward": "native served-link quality component",
            "energy_penalty": "altitude penalty proxy, not measured battery energy",
            "total_reward": "native per-step global reward component",
        },
        active_plain_hmasd_flags={
            **PLAIN_HMASD_FLAGS,
        },
    )
    CURRENT["summary"] = summary
    return summary


def _timed_update(agent):
    original = agent.update

    def update(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            CURRENT["update_seconds"] += time.perf_counter() - started

    agent.update = update


def _installation_summary(installation):
    return {key: value for key, value in installation.items() if key != "timing"}


def build_learner(arm, summary, out, training_seed):
    shared = native.shared
    shared.check_deadline(summary, "learner setup")
    torch.set_num_threads(4)
    shared.seed_rng(training_seed)
    envs = shared.e0._make_envs(shared.TRAIN_LANES, training_seed, shared.N_UAVS,
                                shared.N_USERS, shared.HORIZON)
    config = make_config(arm, envs, training_seed)
    summary["learner_config"] = shared.config_snapshot(config)
    summary["learner_config"]["continuous_action_distribution"] = getattr(config, "continuous_action_distribution", "gaussian")
    summary["active_plain_hmasd_flags"] = {
        **{name: getattr(config, name) for name in PLAIN_HMASD_FLAGS},
    }
    if any(summary["active_plain_hmasd_flags"][name]
           for name in ("disable_high_level_training", "disable_discriminator_training",
                        "disable_discriminator_rewards")):
        raise RuntimeError("GCEA B01 requires all five ordinary HMASD parameter groups active")
    agent = shared.HMASDAgent(config, log_dir=str(out / "learner_logs"),
                              device=torch.device("cpu"))
    installation = install_actor_encoder(agent, arm)
    _timed_update(agent)
    summary["counts"]["model_constructions"] += 1
    summary["counts"]["training_starts"] += 1
    theta0 = shared.e0._capture_theta0(agent)
    summary["initial_parameter_norms"] = shared.measured(
        {key: value["norm"] for key, value in theta0.items()}, "initial parameters"
    )
    counters = shared.optimizer_counters(agent)
    summary["optimizer_present"] = {key: value is not None for key, value in counters.items()}
    summary["parameter_counts"] = _installation_summary(installation)
    CURRENT["learner"], CURRENT["learner_install"] = agent, installation
    shared.publish(out, summary, "learner constructed")
    return envs, agent, theta0, counters


def build_evaluator(arm, summary, out, evaluation_seed):
    shared = native.shared
    with shared.e0._preserve_rng():
        shared.check_deadline(summary, "evaluator construction")
        shared.seed_rng(evaluation_seed)
        evaluator = native.Evaluator(arm, out, evaluation_seed)
        installation = install_actor_encoder(evaluator.agent, arm)
        summary["counts"]["model_constructions"] += 1
        summary["evaluation_config"] = shared.config_snapshot(evaluator.config)
        CURRENT["evaluator_install"] = installation
        shared.publish(out, summary, "evaluator constructed")
    return evaluator


def collect_training(*args, **kwargs):
    started = time.perf_counter()
    try:
        return _ORIGINALS["collect_training"](*args, **kwargs)
    finally:
        elapsed = time.perf_counter() - started
        summary = args[4]
        collection = elapsed - CURRENT["update_seconds"] - CURRENT["evaluation_seconds"]
        summary["phase_wall_seconds"].update(
            collection=max(0.0, collection), update=CURRENT["update_seconds"],
            evaluation=CURRENT["evaluation_seconds"],
        )


def _add_panel_meaning(panel):
    components = panel.get("component_means")
    scores = panel.get("native_scores_J")
    if not components or scores is None:
        return
    total = np.asarray(components["total_reward"], dtype=np.float64)
    scores_array = np.asarray(scores, dtype=np.float64)
    if not np.allclose(scores_array, total, rtol=1e-7, atol=1e-7):
        raise ValueError("native J does not match the S1 total-reward component")
    coverage = np.asarray(components["coverage_reward"], dtype=np.float64)
    panel["connected_users_mean_per_step"] = (coverage * native.shared.N_USERS).tolist()


def evaluate_panel(*args, **kwargs):
    started = time.perf_counter()
    try:
        result = _ORIGINALS["evaluate_panel"](*args, **kwargs)
    finally:
        CURRENT["evaluation_seconds"] += time.perf_counter() - started
    summary, out = args[2], args[3]
    _add_panel_meaning(summary["panels"][-1])
    summary["phase_wall_seconds"]["evaluation"] = CURRENT["evaluation_seconds"]
    native.shared.publish(out, summary, f"panel {args[4]} interpreted")
    return result


_ORIGINALS = {
    "make_envs": native.shared.e0._make_envs,
    "make_config": native.make_config,
    "base_summary": native.shared.base_summary,
    "build_learner": native.build_learner,
    "build_evaluator": native.build_evaluator,
    "collect_training": native.collect_training,
    "evaluate_panel": native.evaluate_panel,
}


@contextmanager
def scoped_native_bindings():
    saved = {
        "make_envs": native.shared.e0._make_envs,
        "OBJECT_ID": native.OBJECT_ID, "CARD": native.CARD, "BLOCKS": native.BLOCKS,
        "ROLLOUTS": native.ROLLOUTS, "PANEL_ROLLOUTS": native.PANEL_ROLLOUTS,
        "ARMS": native.ARMS, "FLAT_ARM": native.FLAT_ARM, "WALL_PLANS": native.WALL_PLANS,
        "make_config": native.make_config, "build_learner": native.build_learner,
        "build_evaluator": native.build_evaluator, "collect_training": native.collect_training,
        "evaluate_panel": native.evaluate_panel, "base_summary": native.shared.base_summary,
        "shared_ROLLOUTS": native.shared.ROLLOUTS,
    }
    native.shared.e0._make_envs = make_bounded_envs
    native.OBJECT_ID, native.CARD = OBJECT_ID, CARD
    native.BLOCKS, native.ROLLOUTS, native.PANEL_ROLLOUTS = dict(BLOCKS), ROLLOUTS, PANEL_ROLLOUTS
    native.ARMS, native.FLAT_ARM, native.WALL_PLANS = dict(ARMS), None, dict(WALL_PLANS)
    native.shared.ROLLOUTS = ROLLOUTS
    native.make_config, native.build_learner = make_config, build_learner
    native.build_evaluator, native.collect_training = build_evaluator, collect_training
    native.evaluate_panel, native.shared.base_summary = evaluate_panel, base_summary
    try:
        yield
    finally:
        for name in ("OBJECT_ID", "CARD", "BLOCKS", "ROLLOUTS", "PANEL_ROLLOUTS", "ARMS",
                     "FLAT_ARM", "WALL_PLANS", "make_config", "build_learner", "build_evaluator",
                     "collect_training", "evaluate_panel"):
            setattr(native, name, saved[name])
        native.shared.e0._make_envs = saved["make_envs"]
        native.shared.base_summary = saved["base_summary"]
        native.shared.ROLLOUTS = saved["shared_ROLLOUTS"]


def _reset_current(arm, admission):
    CURRENT.update(arm=arm, admission=admission, summary=None, learner=None,
                   learner_install=None, evaluator_install=None, update_seconds=0.0,
                   evaluation_seconds=0.0, fit_started=time.perf_counter(),
                   cpu_started=time.process_time(),
                   action_statistics={"train": _empty_action_statistics(), "evaluation": _empty_action_statistics()})


def _finalize_summary(out: Path) -> None:
    shared, summary = native.shared, CURRENT["summary"]
    if summary is None:
        raise RuntimeError("native runner did not construct a summary")
    learner_install, evaluator_install = CURRENT["learner_install"], CURRENT["evaluator_install"]
    summary["actor_timing"] = {
        "learner": learner_install["timing"].as_dict(),
        "evaluator": evaluator_install["timing"].as_dict(),
    }
    checkpoint = out / "final_checkpoint.pt"
    CURRENT["learner"].save_model(checkpoint)
    total = time.perf_counter() - CURRENT["fit_started"]
    summary["phase_wall_seconds"].update(
        total=total, update=CURRENT["update_seconds"], evaluation=CURRENT["evaluation_seconds"]
    )
    summary["fit_wall_seconds_through_checkpoint"] = total
    summary["fit_cpu_seconds_through_checkpoint"] = time.process_time() - CURRENT["cpu_started"]
    summary["timing_scope"] = (
        "fit body from run_fit entry through final checkpoint serialization; excludes imports, "
        "admission and final summary publication; phase_wall_seconds.total has the same scope; "
        "the launch supervisor supplies full invocation wall time"
    )
    summary["peak_rss_scope"] = (
        "process peak sampled by the inherited native runner before final checkpoint serialization"
    )
    summary["final_checkpoint"] = {
        "path": checkpoint.name,
        "bytes": checkpoint.stat().st_size,
        "construction": "construct the recorded arm, install its encoder, then HMASDAgent.load_model",
    }
    final_displacement = summary["training_rows"][-1]["relative_initialization_displacement"]
    if any(summary["optimizer_calls"].get(name, 0) <= 0 for name in NETWORKS):
        raise ValueError("complete HMASD fit did not update all five parameter groups")
    if any(final_displacement.get(name) is None or final_displacement[name] <= 0 for name in NETWORKS):
        raise ValueError("complete HMASD fit did not move all five parameter groups")
    if any(summary["evaluation_optimizer_calls"].values()):
        raise ValueError("separate evaluator performed an optimizer update")
    fit_endpoint(summary)
    shared.publish(out, summary, "checkpoint and instrumentation finalized")


def run_fit(arm: str, seed: int, out: Path, admission=None) -> int:
    plan_guard(arm, seed)
    _reset_current(arm, admission)
    with scoped_native_bindings():
        result = native.run_fit(arm, seed, out)
        if result == 0:
            try:
                _finalize_summary(out)
            except Exception as exc:
                summary = CURRENT["summary"]
                summary["status"], summary["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
                native.shared.write_json(out / "summary.json", summary)
                return 1
        return result


def fit_endpoint(summary):
    with scoped_native_bindings():
        scores = native.arm_panels(summary)
    if summary.get("goal_conditioned_entity_aggregation_object") != OBJECT_ID:
        raise ValueError("not an GCEA B01 fit")
    if summary.get("encoder_arm") not in ARMS:
        raise ValueError("unknown encoder arm")
    if summary.get("final_checkpoint", {}).get("bytes", 0) <= 0:
        raise ValueError("missing recoverable checkpoint")
    if any(summary["optimizer_calls"].get(name, 0) <= 0 for name in NETWORKS):
        raise ValueError("missing five-group learning")
    if any(summary["evaluation_optimizer_calls"].values()):
        raise ValueError("evaluator updated")
    for panel in summary["panels"]:
        _add_panel_meaning(panel)
    for phase, count_key in (("train", "training_transitions"), ("evaluation", "evaluation_steps")):
        stats = summary["action_statistics"][phase]
        transitions = summary["counts"][count_key]
        if (stats["team_steps"] != transitions or stats["uav_actions"] != transitions * native.shared.N_UAVS
                or stats["coordinates"] != transitions * native.shared.N_UAVS * 3):
            raise ValueError("execution-boundary telemetry and native transition counts disagree")
        stats["position_telemetry"] = "measured" if stats["position_observed_team_steps"] else "unmeasured"
    return scores


def parse_args(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args(argv)


def run_admitted(args, admission):
    plan_guard(args.arm, args.seed)
    if args.launch_sha != admission["sha"]:
        raise SystemExit("--launch-sha must equal the admitted source SHA")
    head = native.shared.e0._git("rev-parse", "HEAD")
    if head and head != admission["sha"]:
        raise SystemExit("runner source HEAD is not the admitted SHA")
    return run_fit(
        args.arm, args.seed, args.output_root.resolve(),
        admission={"sha": admission["sha"], "command_sha256": admission["command_sha256"]},
    )


__all__ = [
    "ARMS", "BLOCKS", "EVALUATION_SEED", "OBJECT_ID", "PANEL_ROLLOUTS", "ROLLOUTS",
    "TRAINING_SEED", "fit_endpoint", "parse_args", "run_admitted", "run_fit",
    "scoped_native_bindings",
]
