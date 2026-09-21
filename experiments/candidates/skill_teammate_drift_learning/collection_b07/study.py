"""B07 own-collection factorial on the B05 unknown-law terminal host."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any

import numpy as np

from experiments.candidates.skill_teammate_drift_learning.unknown_law_b05.learning import (
    COOPERATIVE,
    OUTCOMES,
    SAFE,
    DecisionLearner,
    SharedLawLearner,
    Spec,
)
from experiments.candidates.skill_teammate_drift_learning.unknown_law_b05 import study as b05


OBJECT = "STDL_COLLECTION_B07"
SOURCE = b05.SOURCE
TARGET = b05.TARGET
SAFE_REWARD_MEAN = b05.SAFE_REWARD_MEAN
RESPONSE_TRUTH = b05.RESPONSE_TRUTH
ENDPOINT_WINDOW = 64


@dataclass(frozen=True)
class Config:
    source_macros: int = 2048
    target_macros: int = 256
    contexts: int = 4
    skill_ticks: int = 3
    epsilon: float = 0.20

    @property
    def total_macros(self) -> int:
        return self.source_macros + self.target_macros


@dataclass(frozen=True)
class Branch:
    id: str
    learner: str
    collector: str
    spec: Spec


RESPONSE_SPEC = Spec("response_all", "response", 2.0)
FULL_SPEC = Spec("fingerprint_full", "hybrid", 2.0)
BRANCHES = (
    Branch("R_U", "response", "uniform", RESPONSE_SPEC),
    Branch("F_U", "full_hybrid", "uniform", FULL_SPEC),
    Branch("R_E", "response", "epsilon_greedy", RESPONSE_SPEC),
    Branch("F_E", "full_hybrid", "epsilon_greedy", FULL_SPEC),
)


def validate_config(config: Config) -> None:
    b05.validate_config(config)
    if config.epsilon != 0.20:
        raise ValueError("B07 fixes epsilon at 0.20")


def cooperative_propensity(greedy_action, epsilon: float):
    """Probability of COOPERATIVE under binary epsilon-greedy collection."""
    if not np.isfinite(epsilon) or not 0.0 <= epsilon <= 1.0:
        raise ValueError("epsilon must lie in [0, 1]")
    greedy = np.asarray(greedy_action)
    if not np.isin(greedy, (SAFE, COOPERATIVE)).all():
        raise ValueError("greedy action must be binary")
    result = epsilon / 2.0 + (1.0 - epsilon) * greedy.astype(np.float64)
    return float(result) if result.ndim == 0 else result


def action_from_uniform(uniform: float, cooperative_probability: float) -> int:
    if not 0.0 <= uniform < 1.0:
        raise ValueError("uniform must lie in [0, 1)")
    if not 0.0 <= cooperative_probability <= 1.0:
        raise ValueError("cooperative_probability must lie in [0, 1]")
    # Keep the B05 addressed draw convention: uniform collection uses u >= .5.
    return int(uniform >= 1.0 - cooperative_probability)


def exact_policy_readouts(
    predictions: np.ndarray,
    exact_values: np.ndarray,
    actual_cooperative_probability: float,
    epsilon: float,
) -> dict[str, float | int]:
    """Three distinct exact policy reductions from one pre-update Q/truth table."""
    predictions = np.asarray(predictions, dtype=np.float64)
    truth = np.asarray(exact_values, dtype=np.float64)
    if predictions.shape != (2,) or truth.shape != (2,):
        raise ValueError("predictions and exact_values must have shape (2,)")
    if not np.isfinite(predictions).all() or not np.isfinite(truth).all():
        raise ValueError("policy readout inputs must be finite")
    greedy = int(predictions[COOPERATIVE] > predictions[SAFE])
    matched_probability = cooperative_propensity(greedy, epsilon)
    return {
        "greedy_action": greedy,
        "matched_epsilon_cooperative_probability": matched_probability,
        "greedy_expected_return": float(truth[greedy]),
        "matched_epsilon_expected_return": float(
            (1.0 - matched_probability) * truth[SAFE]
            + matched_probability * truth[COOPERATIVE]
        ),
        "actual_collector_expected_return": float(
            (1.0 - actual_cooperative_probability) * truth[SAFE]
            + actual_cooperative_probability * truth[COOPERATIVE]
        ),
    }


def _target_slices(config: Config) -> dict[str, tuple[int, int]]:
    start, stop = config.source_macros, config.total_macros
    width = min(ENDPOINT_WINDOW, config.target_macros)
    return {
        "first64": (start, start + width),
        "full": (start, stop),
        "late64": (stop - width, stop),
    }


def _prefix(prefix: str, arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {f"{prefix}{key}": value.copy() for key, value in arrays.items()}


def _longest_safe_streak(actions: np.ndarray) -> int:
    longest = current = 0
    for action in actions:
        if int(action) == SAFE:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _endpoint(
    trajectory: dict[str, np.ndarray], start: int, stop: int
) -> dict[str, Any]:
    result = {"panel_count": int(stop - start)}
    for key in (
        "greedy_expected_return",
        "matched_epsilon_expected_return",
        "actual_collector_expected_return",
    ):
        values = trajectory[key][start:stop]
        result[f"mean_{key}"] = float(values.mean())
        result[f"cumulative_{key}"] = float(values.sum())
    result.update(
        mean_sampled_return=float(trajectory["reward"][start:stop].mean()),
        sampled_return_sum=int(trajectory["reward"][start:stop].sum()),
        cooperative_collection_count=int(
            trajectory["collection_action"][start:stop].sum()
        ),
        greedy_cooperative_count=int(trajectory["greedy_action"][start:stop].sum()),
        collection_action_counts=np.bincount(
            trajectory["collection_action"][start:stop], minlength=2
        ).astype(int).tolist(),
        greedy_action_counts=np.bincount(
            trajectory["greedy_action"][start:stop], minlength=2
        ).astype(int).tolist(),
    )
    optimal = trajectory["exact_values"][start:stop].max(axis=1)
    for key in (
        "greedy_expected_return",
        "matched_epsilon_expected_return",
        "actual_collector_expected_return",
    ):
        result[f"mean_{key.removesuffix('_expected_return')}_regret"] = float(
            np.mean(optimal - trajectory[key][start:stop])
        )
    return result


def reduce_branch_summaries(branches: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Form B07 task contrasts from already reduced branch summaries."""
    if set(branches) != {branch.id for branch in BRANCHES}:
        raise ValueError("branch summaries must cover R_U, F_U, R_E, and F_E")
    by_endpoint = {}
    for endpoint in ("first64", "full", "late64"):
        rows = {
            branch: branches[branch]["target_by_endpoint"][endpoint]
            for branch in branches
        }
        e_gap = (
            rows["R_E"]["mean_actual_collector_expected_return"]
            - rows["F_E"]["mean_actual_collector_expected_return"]
        )
        matched_e_gap = (
            rows["R_E"]["mean_matched_epsilon_expected_return"]
            - rows["F_E"]["mean_matched_epsilon_expected_return"]
        )
        matched_u_gap = (
            rows["R_U"]["mean_matched_epsilon_expected_return"]
            - rows["F_U"]["mean_matched_epsilon_expected_return"]
        )
        by_endpoint[endpoint] = {
            "primary_executed_e_response_minus_full": float(e_gap),
            "matched_e_response_minus_full": float(matched_e_gap),
            "matched_u_response_minus_full": float(matched_u_gap),
            "matched_feedback_interaction": float(matched_e_gap - matched_u_gap),
            "uniform_actual_response_minus_full": float(
                rows["R_U"]["mean_actual_collector_expected_return"]
                - rows["F_U"]["mean_actual_collector_expected_return"]
            ),
            "sampled_e_response_minus_full": float(
                rows["R_E"]["mean_sampled_return"]
                - rows["F_E"]["mean_sampled_return"]
            ),
            "u_matched_readout_is_executed_return": False,
        }
    return {
        "primary_endpoint": "full",
        "by_endpoint": by_endpoint,
        "interaction_definition": "(R_E-F_E)-(R_U-F_U) on matched-epsilon exact values",
    }


def _target_context_diagnostics(
    trajectory: dict[str, np.ndarray], config: Config, response_branch: bool
) -> dict[str, Any]:
    target = np.arange(config.source_macros, config.total_macros)
    result = {}
    for context in range(config.contexts):
        rows = target[trajectory["context"][target] == context]
        optimal = trajectory["exact_values"][rows].max(axis=1)
        greedy_loss = optimal - trajectory["greedy_expected_return"][rows]
        actual_loss = optimal - trajectory["actual_collector_expected_return"][rows]
        entry = {
            "visits": int(len(rows)),
            "cooperative_collection_count": int(
                trajectory["collection_action"][rows].sum()
            ),
            "greedy_cooperative_count": int(trajectory["greedy_action"][rows].sum()),
            "longest_context_visit_greedy_safe_streak": _longest_safe_streak(
                trajectory["greedy_action"][rows]
            ),
            "greedy_mistake_cost_sum": float(greedy_loss.sum()),
            "actual_policy_regret_sum": float(actual_loss.sum()),
            "mean_absolute_p11_error": float(
                np.abs(trajectory["p11_error"][rows]).mean()
            ),
            "mean_absolute_safe_error": float(
                np.abs(trajectory["safe_prediction_error"][rows]).mean()
            ),
            "law_count_before_first_target_visit": int(
                trajectory["law_counts_before"][rows[0]]
            ),
            "law_count_after_last_target_visit": int(
                trajectory["law_counts_after"][rows[-1]]
            ),
        }
        if response_branch:
            entry["mean_absolute_response_error"] = float(
                np.abs(trajectory["response_prediction_error"][rows]).mean()
            )
            entry["mean_absolute_law_value_error"] = float(
                np.abs(trajectory["law_prediction_error"][rows]).mean()
            )
        result[str(context)] = entry
    return result


def run_block(config: Config, seed: int) -> dict[str, Any]:
    """Execute all four B07 branches with independent histories and shared potentials."""
    validate_config(config)
    if not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")
    schedule = b05._schedule(config)
    slots = b05._rng_slots(config, int(seed))
    truth_by_version = np.stack((slots["source_law"], slots["target_law"]))
    count = config.total_macros

    common = {key: value.copy() for key, value in schedule.items()}
    common.update(
        source_law=slots["source_law"].copy(),
        target_law=slots["target_law"].copy(),
        collector_uniform=slots["collector_uniform"].copy(),
        outcome_uniform=slots["outcome_uniform"].copy(),
        completion_tick_slots=slots["completion_tick_slots"].copy(),
        reward_uniform_slots=slots["reward_uniform_slots"].copy(),
    )

    learners = {}
    trajectories = {}
    initial_states = {}
    source_states = {}
    branch_wall = {}
    for branch in BRANCHES:
        law = SharedLawLearner(config.contexts)
        decision = DecisionLearner(branch.spec, config.contexts)
        learners[branch.id] = (law, decision)
        initial_states[branch.id] = (law.export_state(), decision.export_state())
        branch_wall[branch.id] = 0.0
        arrays = {
            "macro_index": np.arange(count, dtype=np.int32),
            "phase": schedule["phase"].copy(),
            "phase_index": schedule["phase_index"].copy(),
            "version": schedule["version"].copy(),
            "context": schedule["context"].copy(),
            "key": schedule["key"].copy(),
            "age": schedule["age"].copy(),
            "raw_predictions": np.empty((count, 2), dtype=np.float64),
            "clipped_predictions": np.empty((count, 2), dtype=np.float64),
            "greedy_action": np.empty(count, dtype=np.int8),
            "collection_propensity": np.empty(count, dtype=np.float64),
            "collection_action": np.empty(count, dtype=np.int8),
            "outcome": np.empty(count, dtype=np.int8),
            "terminal_outcome": np.empty((count, 2), dtype=np.int8),
            "reward": np.empty(count, dtype=np.int8),
            "reward_probability": np.empty(count, dtype=np.float64),
            "estimated_law": np.empty((count, OUTCOMES), dtype=np.float64),
            "law_prior_center": np.empty((count, OUTCOMES), dtype=np.float64),
            "law_counts_before": np.empty(count, dtype=np.int32),
            "law_counts_after": np.empty(count, dtype=np.int32),
            "decision_updates_before": np.empty(count, dtype=np.int32),
            "regression_solves_before": np.empty(count, dtype=np.int32),
            "pre_positions": np.empty((count, config.skill_ticks, 2), dtype=np.int8),
            "primitive_actions": np.empty((count, config.skill_ticks, 2), dtype=np.int8),
            "post_positions": np.empty((count, config.skill_ticks, 2), dtype=np.int8),
            "exact_values": np.empty((count, 2), dtype=np.float64),
            "greedy_expected_return": np.empty(count, dtype=np.float64),
            "matched_epsilon_expected_return": np.empty(count, dtype=np.float64),
            "actual_collector_expected_return": np.empty(count, dtype=np.float64),
            "matched_epsilon_propensity": np.empty(count, dtype=np.float64),
            "greedy_regret": np.empty(count, dtype=np.float64),
            "matched_epsilon_regret": np.empty(count, dtype=np.float64),
            "actual_collector_regret": np.empty(count, dtype=np.float64),
            "law_l1_error": np.empty(count, dtype=np.float64),
            "p11_error": np.empty(count, dtype=np.float64),
            "safe_prediction_error": np.empty(count, dtype=np.float64),
        }
        if branch.learner == "response":
            arrays.update(
                response_means=np.empty((count, OUTCOMES), dtype=np.float64),
                response_prediction_error=np.empty(count, dtype=np.float64),
                law_prediction_error=np.empty(count, dtype=np.float64),
            )
        trajectories[branch.id] = arrays

    for index in range(count):
        version = int(schedule["version"][index])
        context = int(schedule["context"][index])
        true_law = truth_by_version[version, context]
        for branch in BRANCHES:
            started = perf_counter()
            law, decision = learners[branch.id]
            if index == config.source_macros:
                law.activate_version(TARGET)
            estimated_law = law.predict(version=version, context=context)
            law_count_before = law.count(version=version, context=context)
            raw = decision.predict(
                version=version, context=context, estimated_law=estimated_law
            )
            clipped = np.clip(raw, 0.0, 1.0)
            greedy = int(clipped[COOPERATIVE] > clipped[SAFE])
            if schedule["phase"][index] == SOURCE or branch.collector == "uniform":
                propensity = 0.5
            else:
                propensity = cooperative_propensity(greedy, config.epsilon)
            action = action_from_uniform(
                float(slots["collector_uniform"][index]), propensity
            )
            outcome = (
                0
                if action == SAFE
                else b05._sample_outcome(
                    true_law, float(slots["outcome_uniform"][index])
                )
            )
            transition = b05.simulate_terminal_macro(
                action=action,
                outcome=outcome,
                completion_ticks=slots["completion_tick_slots"][index],
                skill_ticks=config.skill_ticks,
            )
            reward_probability = (
                SAFE_REWARD_MEAN if action == SAFE else float(RESPONSE_TRUTH[outcome])
            )
            reward = int(
                slots["reward_uniform_slots"][index, action, outcome]
                < reward_probability
            )

            # Evaluator truth and all three reductions are formed after prediction/action.
            exact = b05._exact_values(true_law)
            readout = exact_policy_readouts(
                clipped, exact, propensity, config.epsilon
            )
            optimal = float(exact.max())
            trajectory = trajectories[branch.id]
            trajectory["raw_predictions"][index] = raw
            trajectory["clipped_predictions"][index] = clipped
            trajectory["greedy_action"][index] = greedy
            trajectory["collection_propensity"][index] = propensity
            trajectory["collection_action"][index] = action
            trajectory["outcome"][index] = outcome
            trajectory["terminal_outcome"][index] = transition["terminal_outcome"]
            trajectory["reward"][index] = reward
            trajectory["reward_probability"][index] = reward_probability
            trajectory["estimated_law"][index] = estimated_law
            trajectory["law_prior_center"][index] = law.prior_center(version)
            trajectory["law_counts_before"][index] = law_count_before
            trajectory["decision_updates_before"][index] = (
                decision.safe_updates + decision.cooperative_updates
            )
            trajectory["regression_solves_before"][index] = decision.solve_calls
            trajectory["pre_positions"][index] = transition["pre_positions"]
            trajectory["primitive_actions"][index] = transition["primitive_actions"]
            trajectory["post_positions"][index] = transition["post_positions"]
            trajectory["exact_values"][index] = exact
            trajectory["greedy_expected_return"][index] = readout[
                "greedy_expected_return"
            ]
            trajectory["matched_epsilon_expected_return"][index] = readout[
                "matched_epsilon_expected_return"
            ]
            trajectory["actual_collector_expected_return"][index] = readout[
                "actual_collector_expected_return"
            ]
            trajectory["matched_epsilon_propensity"][index] = readout[
                "matched_epsilon_cooperative_probability"
            ]
            trajectory["greedy_regret"][index] = (
                optimal - readout["greedy_expected_return"]
            )
            trajectory["matched_epsilon_regret"][index] = (
                optimal - readout["matched_epsilon_expected_return"]
            )
            trajectory["actual_collector_regret"][index] = (
                optimal - readout["actual_collector_expected_return"]
            )
            trajectory["law_l1_error"][index] = np.abs(
                estimated_law - true_law
            ).sum()
            trajectory["p11_error"][index] = estimated_law[3] - true_law[3]
            trajectory["safe_prediction_error"][index] = clipped[SAFE] - SAFE_REWARD_MEAN
            if branch.learner == "response":
                response_means = decision.response_means()
                trajectory["response_means"][index] = response_means
                trajectory["response_prediction_error"][index] = float(
                    estimated_law @ (response_means - RESPONSE_TRUTH)
                )
                trajectory["law_prediction_error"][index] = float(
                    (estimated_law - true_law) @ RESPONSE_TRUTH
                )

            law.observe(
                action=action, version=version, context=context, outcome=outcome
            )
            decision.observe(
                macro_index=index,
                action=action,
                version=version,
                context=context,
                estimated_law=estimated_law,
                outcome=outcome,
                reward=reward,
            )
            trajectory["law_counts_after"][index] = law.count(
                version=version, context=context
            )
            branch_wall[branch.id] += perf_counter() - started
            if index + 1 == config.source_macros:
                source_states[branch.id] = (
                    law.export_state(),
                    decision.export_state(),
                )

    if len(source_states) != len(BRANCHES):
        raise RuntimeError("source states were not captured")

    slices = _target_slices(config)
    branch_results = {}
    for branch in BRANCHES:
        law, decision = learners[branch.id]
        trajectory = trajectories[branch.id]
        initial_law, initial_decision = initial_states[branch.id]
        source_law, source_decision = source_states[branch.id]
        final_law, final_decision = law.export_state(), decision.export_state()
        state = {}
        state.update(_prefix("initial_law_", initial_law))
        state.update(_prefix("source_law_", source_law))
        state.update(_prefix("final_law_", final_law))
        state.update(_prefix("initial_decision_", initial_decision))
        state.update(_prefix("source_decision_", source_decision))
        state.update(_prefix("final_decision_", final_decision))
        target_endpoints = {
            name: _endpoint(trajectory, start, stop)
            for name, (start, stop) in slices.items()
        }
        summary = {
            "branch": branch.id,
            "learner": branch.learner,
            "collector": branch.collector,
            "spec": asdict(branch.spec),
            "target_by_endpoint": target_endpoints,
            "target_context_diagnostics": _target_context_diagnostics(
                trajectory, config, branch.learner == "response"
            ),
            "counts": {
                "actual_macros": count,
                "primitive_ticks": count * config.skill_ticks,
                "sampled_reward_labels": count,
                "decision_observations": decision.safe_updates
                + decision.cooperative_updates,
                "law_posterior_updates": law.updates,
                "safe_posterior_updates": decision.safe_updates,
                "cooperative_observations": decision.cooperative_updates,
                "regression_solves": decision.solve_calls,
                "q_truth_panels": count,
                "scalar_policy_values": count * 3,
                "evaluation_environment_ticks": 0,
                "evaluation_reward_draws": 0,
            },
            "law_initial_to_source_l2_movement": float(
                np.linalg.norm(
                    source_law["estimated_law"].reshape(-1)
                    - initial_law["estimated_law"].reshape(-1)
                )
            ),
            "law_source_to_final_l2_movement": float(
                np.linalg.norm(
                    final_law["estimated_law"].reshape(-1)
                    - source_law["estimated_law"].reshape(-1)
                )
            ),
            "decision_initial_to_source_l2_movement": float(
                np.linalg.norm(
                    source_decision["estimate"] - initial_decision["estimate"]
                )
            ),
            "decision_source_to_final_l2_movement": float(
                np.linalg.norm(
                    final_decision["estimate"] - source_decision["estimate"]
                )
            ),
            "compute_wall_seconds": float(branch_wall[branch.id]),
            "compute_wall_scope": (
                "branch law/decision prediction, collection, evaluator reductions, and updates"
            ),
            "matched_epsilon_readout_role": (
                "off_collector" if branch.collector == "uniform" else "executed_policy"
            ),
        }
        branch_results[branch.id] = {
            "summary": summary,
            "trajectory": trajectory,
            "state": state,
        }

    reductions = reduce_branch_summaries(
        {branch: result["summary"] for branch, result in branch_results.items()}
    )
    summary = {
        "object": OBJECT,
        "status": "COMPLETE",
        "seed": int(seed),
        "config": asdict(config),
        "branches": [branch.id for branch in BRANCHES],
        "counts": {
            "decision_fits": 4,
            "law_fits": 4,
            "actual_macros": count * 4,
            "duplicated_source_macros": config.source_macros * 4,
            "primitive_ticks": count * 4 * config.skill_ticks,
            "sampled_reward_labels": count * 4,
            "q_truth_panels": count * 4,
            "scalar_policy_values": count * 4 * 3,
            "evaluation_environment_ticks": 0,
            "evaluation_reward_draws": 0,
            "gradient_optimizer_calls": 0,
        },
        "reductions": reductions,
    }
    for array in common.values():
        if array.dtype == object:
            raise RuntimeError("common output contains object dtype")
    for result in branch_results.values():
        if any(value.dtype == object for value in result["trajectory"].values()):
            raise RuntimeError("branch trajectory contains object dtype")
        if any(value.dtype == object for value in result["state"].values()):
            raise RuntimeError("branch state contains object dtype")
    return {"summary": summary, "common": common, "branches": branch_results}
