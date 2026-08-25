"""Bounded paired optimisation probe for the RECCT dependency mask.

Sequence 05.  This runs the three registered arms of
``roster_learner_mask`` on the REAL learner: the accepted G40 native-six policy,
its real Adam optimizer, real trajectories collected from
``ContinuousRosterToyBatch``, and G40's own fast-anchor loss.  The only
candidate-local element is the mask applied to ``.grad`` between ``backward()``
and ``optimizer.step()``.

``ha_ctse_process/`` is NOT modified.  The update loop below reproduces
``g40.optimize_common_fast_anchor_update`` term for term, calling G40's own
functions for every component, and inserts exactly one candidate-side operation.
``test_roster_optimization_probe`` pins that reproduction: with arm
``UNCHANGED_LEARNER`` the loop must land bit-identically on the same parameters
as the unmodified G40 routine.  If G40 ever changes, that test fails rather than
this probe silently drifting.

SCOPE LIMIT -- BINDING
----------------------
External ruling ``ENV_CAPABILITY_EXTENSION_REQUIRED`` holds that this
environment does not identify RECCT's mechanism: the optimum is highly
non-unique and a performance difference here "can therefore arise from generic
optimizer regularization rather than the proposed dependency semantics".  Pro
sanctioned this run as "an optimization smoke test or negative control" only.

Accordingly the result of this probe MAY NOT promote the candidate and MAY NOT
eliminate it.  ``ProbeReport.admissible_conclusion`` states that in the payload
itself so a downstream reader cannot pick the numbers up without the boundary.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Sequence

import torch

import ha_ctse_process.continuous_roster_native_six_credit_reduction_g40 as g40

from experiments.candidates.recct_lite import roster_learner_mask as mask

RAW_OUTPUT_BINDING = "recct_lite.roster_optimization_probe.v1"

#: The one sentence that governs every number this module emits.
ADMISSIBLE_CONCLUSION = (
    "EXPLORATORY_OPTIMIZATION_PROBE_ONLY: this environment does not identify "
    "the RECCT mechanism; no promotion and no elimination may be based on "
    "these numbers."
)

_CPU = torch.device("cpu")


@dataclass
class ArmResult:
    arm: str
    initial_utility: float
    final_utility: float
    initial_event_window_utility: float
    final_event_window_utility: float
    mask_retained_fraction: list[float] = field(default_factory=list)
    gradient_norm: list[float] = field(default_factory=list)
    adam_second_moment_norm: list[float] = field(default_factory=list)
    finite: bool = True

    @property
    def utility_change(self) -> float:
        return self.final_utility - self.initial_utility

    @property
    def mean_retained_fraction(self) -> float:
        if not self.mask_retained_fraction:
            return 1.0
        return statistics.fmean(self.mask_retained_fraction)


@dataclass
class ProbeReport:
    arms: dict[str, ArmResult]
    capacity: int
    iterations: int
    ppo_passes: int
    seed: int
    admissible_conclusion: str = ADMISSIBLE_CONCLUSION
    raw_output_binding: str = RAW_OUTPUT_BINDING

    def payload(self) -> dict[str, object]:
        return {
            "raw_output_binding": self.raw_output_binding,
            "admissible_conclusion": self.admissible_conclusion,
            "capacity": self.capacity,
            "iterations": self.iterations,
            "ppo_passes": self.ppo_passes,
            "seed": self.seed,
            "arms": {
                name: {
                    "initial_utility": result.initial_utility,
                    "final_utility": result.final_utility,
                    "utility_change": result.utility_change,
                    "initial_event_window_utility": result.initial_event_window_utility,
                    "final_event_window_utility": result.final_event_window_utility,
                    "mean_retained_fraction": result.mean_retained_fraction,
                    "mean_gradient_norm": (
                        statistics.fmean(result.gradient_norm)
                        if result.gradient_norm
                        else 0.0
                    ),
                    "final_adam_second_moment_norm": (
                        result.adam_second_moment_norm[-1]
                        if result.adam_second_moment_norm
                        else 0.0
                    ),
                    "finite_update": result.finite,
                }
                for name, result in self.arms.items()
            },
        }


def _second_moment_norm(
    optimizer: torch.optim.Optimizer, parameters: Sequence[torch.Tensor]
) -> float:
    total = 0.0
    for parameter in parameters:
        state = optimizer.state.get(parameter)
        if not state:
            continue
        moment = state.get("exp_avg_sq")
        if moment is not None:
            total += float(moment.sum().item())
    return total**0.5


def fast_anchor_update_with_arm(
    model: g40.G40NativeSixPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: g40.AnchoredRosterTrajectory,
    *,
    arm: str,
    ppo_passes: int,
    generator: torch.Generator | None = None,
) -> tuple[list[float], list[float], bool]:
    """G40's fast-anchor update, with the candidate mask on the gradient.

    Mirrors ``g40.optimize_common_fast_anchor_update`` exactly except for the
    single ``mask.apply_arm`` call between ``backward()`` and the step.
    """
    if model.phase != "fast":
        raise RuntimeError("RECCT probe requires the G40 fast phase")
    parameters = model.actor_credit_parameters()
    credit = g40.compute_credit_targets(
        rewards=trajectory.rewards,
        slow_values=trajectory.old_values,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=g40.terminal_mask(trajectory),
    )
    normalized_advantage = g40.normalize_advantage(credit.immediate_advantage)

    retained: list[float] = []
    gradients: list[float] = []
    finite = True
    for pass_index in range(int(ppo_passes)):
        replay = g40.replay_trajectory(model, trajectory, device=_CPU)
        policy = g40._policy_loss_from_normalized_advantage(
            replay, trajectory, normalized_advantage
        )
        immediate = g40.F.mse_loss(
            replay.immediate_baselines, trajectory.rewards.detach()
        )
        loss = (
            policy
            + g40.VALUE_COEFFICIENT * immediate
            - g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()

        decision = mask.apply_arm(
            parameters, arm=arm, optimizer=optimizer, generator=generator
        )
        retained.append(decision.retained_fraction)

        norm = g40._gradient_global_norm(parameters)
        gradients.append(norm)
        finite &= bool(torch.isfinite(loss)) and norm == norm and norm != float("inf")
        g40._optimizer_step(optimizer, parameters)
    return retained, gradients, finite


def _mean_utilities(
    model: g40.G40NativeSixPolicy,
    processes: Sequence[object],
    *,
    action_seed: int,
) -> tuple[float, float]:
    rows, valid = g40.evaluate_model(
        model,
        processes=processes,
        action_seed=int(action_seed),
        process_kind="random",
        deterministic=True,
    )
    if not valid:
        raise RuntimeError("RECCT probe evaluation produced an invalid roster")
    utility = statistics.fmean(float(row["utility"]) for row in rows)
    window = statistics.fmean(
        float(row["minimum_event_window_utility"]) for row in rows
    )
    return utility, window


def run_arm(
    arm: str,
    *,
    capacity: int = 8,
    iterations: int = 4,
    episodes_per_iteration: int = 4,
    ppo_passes: int = 2,
    seed: int = 20_260_805,
) -> ArmResult:
    """One arm, from a shared initialization, on the real toy environment."""
    model = g40.make_model(capacity, initialization_seed=seed)
    optimizer = torch.optim.Adam(
        model.actor_credit_parameters(), lr=g40.LEARNING_RATE
    )
    evaluation = g40.make_process_ledgers(
        replicate=0, capacity=capacity, episode_count=4, formal=False
    )
    generator = torch.Generator(device="cpu").manual_seed(seed)

    initial_utility, initial_window = _mean_utilities(
        model, evaluation, action_seed=seed + 1
    )

    result = ArmResult(
        arm=arm,
        initial_utility=initial_utility,
        final_utility=initial_utility,
        initial_event_window_utility=initial_window,
        final_event_window_utility=initial_window,
    )

    for iteration in range(int(iterations)):
        trajectory = g40.collect_g40_trajectory(
            model,
            episode_ids=range(
                iteration * episodes_per_iteration,
                (iteration + 1) * episodes_per_iteration,
            ),
            ledger_seed=seed + 2,
            action_seed=seed + 3 + iteration,
            device=_CPU,
        )
        retained, gradients, finite = fast_anchor_update_with_arm(
            model,
            optimizer,
            trajectory,
            arm=arm,
            ppo_passes=ppo_passes,
            generator=generator,
        )
        result.mask_retained_fraction.extend(retained)
        result.gradient_norm.extend(gradients)
        result.adam_second_moment_norm.append(
            _second_moment_norm(optimizer, model.actor_credit_parameters())
        )
        result.finite &= finite

    final_utility, final_window = _mean_utilities(
        model, evaluation, action_seed=seed + 1
    )
    result.final_utility = final_utility
    result.final_event_window_utility = final_window
    return result


def run_probe(
    *,
    capacity: int = 8,
    iterations: int = 4,
    episodes_per_iteration: int = 4,
    ppo_passes: int = 2,
    seed: int = 20_260_805,
) -> ProbeReport:
    """All three arms from a shared initialization and shared evaluation set."""
    arms = {
        arm: run_arm(
            arm,
            capacity=capacity,
            iterations=iterations,
            episodes_per_iteration=episodes_per_iteration,
            ppo_passes=ppo_passes,
            seed=seed,
        )
        for arm in mask.ARMS
    }
    return ProbeReport(
        arms=arms,
        capacity=capacity,
        iterations=iterations,
        ppo_passes=ppo_passes,
        seed=seed,
    )


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(run_probe().payload(), indent=2))
