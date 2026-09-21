"""B05 correlated terminal host and common prequential block execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any, Iterable

import numpy as np

from .learning import (
    COOPERATIVE,
    OUTCOMES,
    SAFE,
    DecisionLearner,
    SharedLawLearner,
    Spec,
    development_specs,
)


OBJECT = "STDL_UNKNOWN_LAW_B05"
SOURCE = 0
TARGET = 1
SAFE_REWARD_MEAN = 0.60
LOW_COOPERATIVE_REWARD_MEAN = 0.05
HIGH_COOPERATIVE_REWARD_MEAN = 0.95
ENDPOINT_WINDOW = 64
P11_VALUES = np.array([0.35, 0.55, 0.65, 0.85], dtype=np.float64)
RESPONSE_TRUTH = np.array([0.05, 0.05, 0.05, 0.95], dtype=np.float64)


@dataclass(frozen=True)
class Config:
    source_macros: int = 2048
    target_macros: int = 256
    contexts: int = 4
    skill_ticks: int = 3

    @property
    def total_macros(self) -> int:
        return self.source_macros + self.target_macros


def validate_config(config: Config) -> None:
    if config.source_macros <= 0 or config.target_macros <= 0:
        raise ValueError("source_macros and target_macros must be positive")
    if config.contexts != 4:
        raise ValueError("B05 fixes exactly four public contexts")
    if config.skill_ticks != 3:
        raise ValueError("B05 fixes the three-tick terminal skill")
    if config.source_macros % config.contexts or config.target_macros % config.contexts:
        raise ValueError("source and target horizons must be divisible by contexts")


def _validate_specs(specs: Iterable[Spec]) -> list[Spec]:
    result = list(specs)
    if not result:
        raise ValueError("specs must be nonempty")
    if any(not isinstance(spec, Spec) for spec in result):
        raise TypeError("every setting must be a Spec")
    ids = [spec.id for spec in result]
    if len(ids) != len(set(ids)):
        raise ValueError("spec ids must be unique")
    return result


def _law_table(rng: np.random.Generator, contexts: int) -> np.ndarray:
    p11 = rng.permutation(P11_VALUES)
    law = np.empty((contexts, OUTCOMES), dtype=np.float64)
    for context in range(contexts):
        law[context, :3] = (1.0 - p11[context]) * rng.dirichlet(np.ones(3))
        law[context, 3] = p11[context]
    return law


def _schedule(config: Config) -> dict[str, np.ndarray]:
    phase = np.concatenate(
        (
            np.full(config.source_macros, SOURCE, dtype=np.int8),
            np.full(config.target_macros, TARGET, dtype=np.int8),
        )
    )
    phase_index = np.concatenate(
        (
            np.arange(config.source_macros, dtype=np.int32),
            np.arange(config.target_macros, dtype=np.int32),
        )
    )
    context = (phase_index % config.contexts).astype(np.int8)
    version = phase.copy()
    key = (version * config.contexts + context).astype(np.int8)
    age = (phase_index // config.contexts).astype(np.int32)
    return {
        "phase": phase,
        "phase_index": phase_index,
        "context": context,
        "version": version,
        "key": key,
        "age": age,
        "public_key": np.column_stack((version, context)).astype(np.int8),
    }


def _rng_slots(config: Config, seed: int) -> dict[str, np.ndarray]:
    roots = np.random.SeedSequence(int(seed)).spawn(6)
    source_rng, target_rng, collector_rng, outcome_rng, completion_rng, reward_rng = (
        np.random.default_rng(root) for root in roots
    )
    return {
        "source_law": _law_table(source_rng, config.contexts),
        "target_law": _law_table(target_rng, config.contexts),
        "collector_uniform": collector_rng.random(config.total_macros),
        "outcome_uniform": outcome_rng.random(config.total_macros),
        "completion_tick_slots": completion_rng.integers(
            1,
            config.skill_ticks + 1,
            size=(config.total_macros, 2),
            dtype=np.int8,
        ),
        # Addressed by macro, action, and sampled joint outcome.
        "reward_uniform_slots": reward_rng.random(
            (config.total_macros, 2, OUTCOMES)
        ),
    }


def _sample_outcome(law: np.ndarray, uniform: float) -> int:
    outcome = int(np.searchsorted(np.cumsum(law), uniform, side="right"))
    return min(outcome, OUTCOMES - 1)


def _outcome_bits(outcome: int) -> np.ndarray:
    if not 0 <= outcome < OUTCOMES:
        raise ValueError("outcome must be in 0..3")
    return np.array([outcome // 2, outcome % 2], dtype=np.int8)


def simulate_terminal_macro(
    *, action: int, outcome: int, completion_ticks: np.ndarray, skill_ticks: int = 3
) -> dict[str, np.ndarray]:
    """Realize a terminal pair with uniform completion ticks and physical holds."""
    if action not in (SAFE, COOPERATIVE):
        raise ValueError("invalid action")
    ticks = np.asarray(completion_ticks, dtype=np.int8)
    if ticks.shape != (2,) or np.any(ticks < 1) or np.any(ticks > skill_ticks):
        raise ValueError("completion_ticks must contain two valid tick indices")
    terminal = np.zeros(2, dtype=np.int8) if action == SAFE else _outcome_bits(outcome)
    pre = np.empty((skill_ticks, 2), dtype=np.int8)
    primitive = np.zeros((skill_ticks, 2), dtype=np.int8)
    post = np.empty((skill_ticks, 2), dtype=np.int8)
    position = np.zeros(2, dtype=np.int8)
    for tick in range(skill_ticks):
        pre[tick] = position
        for agent in range(2):
            if terminal[agent] and tick + 1 == int(ticks[agent]):
                primitive[tick, agent] = 1
                position[agent] = 1
        post[tick] = position
    return {
        "pre_positions": pre,
        "primitive_actions": primitive,
        "post_positions": post,
        "terminal_outcome": terminal,
    }


def _exact_values(true_law: np.ndarray) -> np.ndarray:
    return np.array(
        [SAFE_REWARD_MEAN, float(true_law @ RESPONSE_TRUTH)], dtype=np.float64
    )


def _endpoint_metrics(
    curves: dict[str, np.ndarray], start: int, stop: int
) -> dict[str, Any]:
    return {
        "panel_count": int(stop - start),
        "mean_regret": float(np.mean(curves["regret"][start:stop])),
        "cumulative_regret": float(np.sum(curves["regret"][start:stop])),
        "mean_expected_return": float(
            np.mean(curves["expected_return"][start:stop])
        ),
        "mean_value_mae": float(np.mean(curves["value_mae"][start:stop])),
        "sign_mistakes": int(np.sum(curves["sign_mistake"][start:stop])),
        "action_counts": np.bincount(
            curves["greedy_action"][start:stop], minlength=2
        ).astype(int).tolist(),
    }


def _diagnostic_endpoint(
    *, regret: np.ndarray, expected_return: np.ndarray, sign: np.ndarray, start: int, stop: int
) -> dict[str, Any]:
    return {
        "panel_count": int(stop - start),
        "mean_regret": float(np.mean(regret[start:stop])),
        "cumulative_regret": float(np.sum(regret[start:stop])),
        "mean_expected_return": float(np.mean(expected_return[start:stop])),
        "sign_mistakes": int(np.sum(sign[start:stop])),
    }


def _target_slices(config: Config) -> dict[str, tuple[int, int]]:
    start, stop = config.source_macros, config.total_macros
    width = min(ENDPOINT_WINDOW, config.target_macros)
    return {
        "first64": (start, start + width),
        "full": (start, stop),
        "late64": (stop - width, stop),
    }


def run_block(config: Config, seed: int, specs: Iterable[Spec]) -> dict[str, Any]:
    """Collect one block and train every setting in lockstep on identical data."""
    validate_config(config)
    if not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")
    settings = _validate_specs(specs)
    schedule = _schedule(config)
    slots = _rng_slots(config, int(seed))
    truth_by_version = np.stack((slots["source_law"], slots["target_law"]))
    count = config.total_macros

    law_learner = SharedLawLearner(config.contexts)
    law_wall = 0.0
    law_initial = law_learner.estimate_vector()
    law_source: np.ndarray | None = None
    learners = {spec.id: DecisionLearner(spec, config.contexts) for spec in settings}
    initial_estimates = {
        spec.id: learners[spec.id].estimate_vector() for spec in settings
    }
    source_estimates: dict[str, np.ndarray] = {}
    fit_wall = {spec.id: 0.0 for spec in settings}

    common = {key: value.copy() for key, value in schedule.items()}
    common.update(
        macro_index=np.arange(count, dtype=np.int32),
        source_law=slots["source_law"].copy(),
        target_law=slots["target_law"].copy(),
        collector_uniform=slots["collector_uniform"].copy(),
        outcome_uniform=slots["outcome_uniform"].copy(),
        completion_tick_slots=slots["completion_tick_slots"].copy(),
        reward_uniform_slots=slots["reward_uniform_slots"].copy(),
        collection_action=np.empty(count, dtype=np.int8),
        outcome=np.empty(count, dtype=np.int8),
        terminal_outcome=np.empty((count, 2), dtype=np.int8),
        reward=np.empty(count, dtype=np.int8),
        reward_probability=np.empty(count, dtype=np.float64),
        estimated_law=np.empty((count, OUTCOMES), dtype=np.float64),
        law_counts_before=np.empty(count, dtype=np.int32),
        law_prior_center=np.empty((count, OUTCOMES), dtype=np.float64),
        true_law=np.empty((count, OUTCOMES), dtype=np.float64),
        pre_positions=np.empty((count, config.skill_ticks, 2), dtype=np.int8),
        primitive_actions=np.empty((count, config.skill_ticks, 2), dtype=np.int8),
        post_positions=np.empty((count, config.skill_ticks, 2), dtype=np.int8),
        exact_values=np.empty((count, 2), dtype=np.float64),
        law_l1_error=np.empty(count, dtype=np.float64),
        known_response_predictions=np.empty((count, 2), dtype=np.float64),
        known_response_greedy_action=np.empty(count, dtype=np.int8),
        known_response_expected_return=np.empty(count, dtype=np.float64),
        known_response_regret=np.empty(count, dtype=np.float64),
        known_response_sign_mistake=np.empty(count, dtype=np.int8),
    )
    fit_curves: dict[str, dict[str, np.ndarray]] = {}
    for spec in settings:
        curves = {
            "raw_predictions": np.empty((count, 2), dtype=np.float64),
            "clipped_predictions": np.empty((count, 2), dtype=np.float64),
            "greedy_action": np.empty(count, dtype=np.int8),
            "exact_values": common["exact_values"],
            "expected_return": np.empty(count, dtype=np.float64),
            "regret": np.empty(count, dtype=np.float64),
            "value_mae": np.empty(count, dtype=np.float64),
            "sign_mistake": np.empty(count, dtype=np.int8),
            "updates_before_panel": np.empty(count, dtype=np.int32),
            "regression_solves_before_panel": np.empty(count, dtype=np.int32),
            "window_records_before_panel": np.empty(count, dtype=np.int32),
        }
        if spec.family == "response_all":
            curves.update(
                response_means=np.empty((count, OUTCOMES), dtype=np.float64),
                response_prediction_error=np.empty(count, dtype=np.float64),
                law_prediction_error=np.empty(count, dtype=np.float64),
                cooperative_prediction_error=np.empty(count, dtype=np.float64),
            )
        fit_curves[spec.id] = curves

    for index in range(count):
        version = int(schedule["version"][index])
        context = int(schedule["context"][index])
        law_started = perf_counter()
        if index == config.source_macros:
            law_learner.activate_version(TARGET)
        estimated_law = law_learner.predict(version=version, context=context)
        law_count = law_learner.count(version=version, context=context)
        law_wall += perf_counter() - law_started

        # Every member expires and predicts before any member receives this outcome.
        for spec in settings:
            learner = learners[spec.id]
            started = perf_counter()
            learner.expire_before(index)
            raw = learner.predict(
                version=version, context=context, estimated_law=estimated_law
            )
            response_means = (
                learner.response_means()
                if spec.family == "response_all"
                else None
            )
            fit_wall[spec.id] += perf_counter() - started
            curves = fit_curves[spec.id]
            curves["raw_predictions"][index] = raw
            curves["clipped_predictions"][index] = np.clip(raw, 0.0, 1.0)
            curves["updates_before_panel"][index] = (
                learner.safe_updates + learner.cooperative_updates
            )
            curves["regression_solves_before_panel"][index] = learner.solve_calls
            curves["window_records_before_panel"][index] = len(learner.window)
            if response_means is not None:
                curves["response_means"][index] = response_means

        action = int(slots["collector_uniform"][index] >= 0.5)
        true_law = truth_by_version[version, context]
        outcome = (
            0
            if action == SAFE
            else _sample_outcome(true_law, float(slots["outcome_uniform"][index]))
        )
        transition = simulate_terminal_macro(
            action=action,
            outcome=outcome,
            completion_ticks=slots["completion_tick_slots"][index],
            skill_ticks=config.skill_ticks,
        )
        reward_probability = (
            SAFE_REWARD_MEAN if action == SAFE else float(RESPONSE_TRUTH[outcome])
        )
        reward_uniform = float(slots["reward_uniform_slots"][index, action, outcome])
        reward = int(reward_uniform < reward_probability)

        # Evaluator truth is used only after all pre-outcome predictions are fixed.
        exact = _exact_values(true_law)
        optimal = float(np.max(exact))
        optimal_action = int(exact[COOPERATIVE] > exact[SAFE])
        common["collection_action"][index] = action
        common["outcome"][index] = outcome
        common["terminal_outcome"][index] = transition["terminal_outcome"]
        common["reward"][index] = reward
        common["reward_probability"][index] = reward_probability
        common["estimated_law"][index] = estimated_law
        common["law_counts_before"][index] = law_count
        common["law_prior_center"][index] = law_learner.prior_center(version)
        common["true_law"][index] = true_law
        common["pre_positions"][index] = transition["pre_positions"]
        common["primitive_actions"][index] = transition["primitive_actions"]
        common["post_positions"][index] = transition["post_positions"]
        common["exact_values"][index] = exact
        common["law_l1_error"][index] = np.abs(estimated_law - true_law).sum()

        diagnostic_prediction = np.array(
            [SAFE_REWARD_MEAN, float(estimated_law @ RESPONSE_TRUTH)]
        )
        diagnostic_action = int(
            diagnostic_prediction[COOPERATIVE] > diagnostic_prediction[SAFE]
        )
        common["known_response_predictions"][index] = diagnostic_prediction
        common["known_response_greedy_action"][index] = diagnostic_action
        common["known_response_expected_return"][index] = exact[diagnostic_action]
        common["known_response_regret"][index] = optimal - exact[diagnostic_action]
        common["known_response_sign_mistake"][index] = (
            diagnostic_action != optimal_action
        )

        for spec in settings:
            curves = fit_curves[spec.id]
            clipped = curves["clipped_predictions"][index]
            greedy = int(clipped[COOPERATIVE] > clipped[SAFE])
            curves["greedy_action"][index] = greedy
            curves["expected_return"][index] = exact[greedy]
            curves["regret"][index] = optimal - exact[greedy]
            curves["value_mae"][index] = np.abs(clipped - exact).mean()
            curves["sign_mistake"][index] = greedy != optimal_action
            if spec.family == "response_all":
                means = curves["response_means"][index]
                response_error = float(estimated_law @ (means - RESPONSE_TRUTH))
                law_error = float((estimated_law - true_law) @ RESPONSE_TRUTH)
                curves["response_prediction_error"][index] = response_error
                curves["law_prediction_error"][index] = law_error
                curves["cooperative_prediction_error"][index] = (
                    curves["raw_predictions"][index, COOPERATIVE] - exact[COOPERATIVE]
                )

        # Observation begins only after every prediction and evaluator panel is recorded.
        law_started = perf_counter()
        law_learner.observe(
            action=action, version=version, context=context, outcome=outcome
        )
        law_wall += perf_counter() - law_started
        for spec in settings:
            learner = learners[spec.id]
            started = perf_counter()
            learner.observe(
                macro_index=index,
                action=action,
                version=version,
                context=context,
                estimated_law=estimated_law,
                outcome=outcome,
                reward=reward,
            )
            fit_wall[spec.id] += perf_counter() - started

        if index + 1 == config.source_macros:
            law_source = law_learner.estimate_vector()
            source_estimates = {
                spec.id: learners[spec.id].estimate_vector() for spec in settings
            }

    if law_source is None or len(source_estimates) != len(settings):
        raise RuntimeError("source boundary was not captured")

    slices = _target_slices(config)
    target_start = config.source_macros
    common_counts = {
        "source_macros": config.source_macros,
        "target_macros": config.target_macros,
        "total_macros": count,
        "primitive_ticks": count * config.skill_ticks,
        "sampled_reward_labels": count,
        "collection_action_counts": np.bincount(
            common["collection_action"], minlength=2
        ).astype(int).tolist(),
        "source_collection_action_counts": np.bincount(
            common["collection_action"][:target_start], minlength=2
        ).astype(int).tolist(),
        "target_collection_action_counts": np.bincount(
            common["collection_action"][target_start:], minlength=2
        ).astype(int).tolist(),
        "law_posterior_updates": law_learner.updates,
        "law_fits": 1,
        "decision_fits": len(settings),
        "evaluation_panels": count * len(settings),
        "known_response_diagnostic_panels": count,
        "evaluation_reward_draws": 0,
        "evaluation_learner_updates": 0,
    }
    law_final = law_learner.estimate_vector()
    law_diagnostic: dict[str, Any] = {
        "all_mean_l1_error": float(np.mean(common["law_l1_error"])),
        "target_by_endpoint": {},
        "compute_wall_seconds": float(law_wall),
        "compute_wall_scope": "shared-law activate, predict, count, and observe only",
        "initial_to_source_l2_movement": float(np.linalg.norm(law_source - law_initial)),
        "source_to_final_l2_movement": float(np.linalg.norm(law_final - law_source)),
        "initial_to_final_l2_movement": float(np.linalg.norm(law_final - law_initial)),
    }
    known_response: dict[str, Any] = {"target_by_endpoint": {}}
    for name, (start, stop) in slices.items():
        law_diagnostic["target_by_endpoint"][name] = {
            "panel_count": int(stop - start),
            "mean_l1_error": float(np.mean(common["law_l1_error"][start:stop])),
        }
        known_response["target_by_endpoint"][name] = _diagnostic_endpoint(
            regret=common["known_response_regret"],
            expected_return=common["known_response_expected_return"],
            sign=common["known_response_sign_mistake"],
            start=start,
            stop=stop,
        )

    fits: dict[str, dict[str, Any]] = {}
    for spec in settings:
        learner = learners[spec.id]
        final_estimate = learner.estimate_vector()
        curves = fit_curves[spec.id]
        endpoint_summary = {
            name: _endpoint_metrics(curves, start, stop)
            for name, (start, stop) in slices.items()
        }
        state = learner.export_state()
        state.update(
            initial_estimate=initial_estimates[spec.id].copy(),
            source_estimate=source_estimates[spec.id].copy(),
            final_estimate=final_estimate.copy(),
        )
        cooperative_posterior_updates = (
            learner.cooperative_updates
            if spec.family == "response_all" or spec.representation == "cell"
            else 0
        )
        regression_statistic_updates = (
            learner.cooperative_updates
            if spec.representation in ("law", "hybrid")
            else 0
        )
        fit_summary = {
            "spec": asdict(spec),
            "spec_id": spec.id,
            "target_by_endpoint": endpoint_summary,
            "full_target_cumulative_regret": endpoint_summary["full"][
                "cumulative_regret"
            ],
            "initial_to_source_l2_movement": float(
                np.linalg.norm(source_estimates[spec.id] - initial_estimates[spec.id])
            ),
            "source_to_final_l2_movement": float(
                np.linalg.norm(final_estimate - source_estimates[spec.id])
            ),
            "initial_to_final_l2_movement": float(
                np.linalg.norm(final_estimate - initial_estimates[spec.id])
            ),
            "safe_posterior_updates": learner.safe_updates,
            "cooperative_observations": learner.cooperative_updates,
            "cooperative_posterior_updates": cooperative_posterior_updates,
            "regression_statistic_updates": regression_statistic_updates,
            "posterior_updates": learner.safe_updates + cooperative_posterior_updates,
            "learner_observations": learner.safe_updates + learner.cooperative_updates,
            "regression_solves": learner.solve_calls,
            "expiration_recomputations": learner.expiration_recomputations,
            "compute_wall_seconds": float(fit_wall[spec.id]),
            "compute_wall_scope": "learner expiry, prediction, and observation only",
        }
        fits[spec.id] = {"summary": fit_summary, "curves": curves, "state": state}

    law_state = law_learner.export_state()
    law_state.update(
        initial_estimate=law_initial.copy(),
        source_estimate=law_source.copy(),
        final_estimate=law_final.copy(),
    )
    common["law_initial_estimate"] = law_initial.copy()
    common["law_source_estimate"] = law_source.copy()
    common["law_final_estimate"] = law_final.copy()
    common["law_final_counts"] = law_state["counts"]
    common["law_prior_centers"] = law_state["prior_centers"]
    summary = {
        "object": OBJECT,
        "status": "COMPLETE",
        "seed": int(seed),
        "config": asdict(config),
        "spec_ids": [spec.id for spec in settings],
        "counts": common_counts,
        "law_diagnostic": law_diagnostic,
        "known_response_diagnostic": known_response,
    }
    if any(array.dtype == object for array in common.values()):
        raise RuntimeError("common output contains an object array")
    for fit in fits.values():
        if any(array.dtype == object for array in fit["curves"].values()):
            raise RuntimeError("fit curves contain an object array")
        if any(array.dtype == object for array in fit["state"].values()):
            raise RuntimeError("fit state contains an object array")
    return {"summary": summary, "common": common, "fits": fits}
