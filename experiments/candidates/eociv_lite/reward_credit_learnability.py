"""EOCIV-B3 matched reward-credit learnability experiment.

The candidate-local experiment holds the B2 content representation and real
sibling execution path fixed while comparing complete-episode Monte-Carlo
credit with normalized terminal GAE.  It is an exploratory B run only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import torch
from torch import nn

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import capability_gate
from experiments.candidates.eociv_lite import payload_content_learnability as b2
from experiments.candidates.eociv_lite import real_valve_learning as b1


TREATMENT = "EOCIV-B3-REWARD-CREDIT-LEARNABILITY"
LEARNERS = ("MC_RETURN", "GAE_NORM")
CHECKPOINTS = ("INIT", "MID", "FINAL")
ACTOR_SEEDS = b1.ACTOR_SEEDS
PROFILES = b1.PROFILES
EVALUATION_ARMS = b2.EVALUATION_ARMS
GAE_LAMBDA = 0.95
NORMALIZATION_EPSILON = 1e-8


@dataclass(frozen=True)
class ExperimentPlan:
    mode: str
    learners: tuple[str, ...]
    actor_seeds: tuple[int, ...]
    profiles: tuple[roster_env.RosterProfile, ...]
    training_episodes_per_profile: int
    mid_update: int
    evaluation_roots_per_checkpoint_profile: int

    @property
    def training_updates_per_actor(self) -> int:
        return len(self.profiles) * self.training_episodes_per_profile

    @property
    def training_episodes(self) -> int:
        return len(self.learners) * len(self.actor_seeds) * self.training_updates_per_actor

    @property
    def training_transitions(self) -> int:
        return self.training_episodes * roster_env.HORIZON

    @property
    def evaluation_episodes(self) -> int:
        return (
            len(self.learners)
            * len(self.actor_seeds)
            * len(CHECKPOINTS)
            * len(self.profiles)
            * self.evaluation_roots_per_checkpoint_profile
            * len(EVALUATION_ARMS)
        )

    @property
    def evaluation_transitions(self) -> int:
        return self.evaluation_episodes * roster_env.HORIZON

    @property
    def maximum_transitions(self) -> int:
        return self.training_transitions + self.evaluation_transitions


FULL_PLAN = ExperimentPlan(
    "full", LEARNERS, ACTOR_SEEDS, PROFILES, 32, 48, 4
)
SMOKE_PLAN = ExperimentPlan(
    "smoke", LEARNERS, ACTOR_SEEDS[:1], PROFILES, 2, 3, 1
)


def plan_for_mode(mode: str) -> ExperimentPlan:
    if mode == "smoke":
        return SMOKE_PLAN
    if mode == "full":
        return FULL_PLAN
    raise ValueError("mode must be 'smoke' or 'full'")


def episode_id(
    stage: str, actor_index: int, profile_index: int, root: int
) -> int:
    bases = {"train": 6_000_000, "INIT": 7_000_000, "MID": 8_000_000, "FINAL": 9_000_000}
    if stage not in bases or min(actor_index, profile_index, root) < 0:
        raise ValueError("unregistered B3 episode-id coordinate")
    # Learner is deliberately absent: MC and GAE see the same registered roots.
    return bases[stage] + actor_index * 100_000 + profile_index * 10_000 + root


def _snapshot(actor: b1.RecurrentActorCritic) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in actor.state_dict().items()
    }


def _actor_from_snapshot(
    seed: int, state: Mapping[str, torch.Tensor]
) -> b1.RecurrentActorCritic:
    actor = b1.RecurrentActorCritic(
        PROFILES[0].member_capacity,
        seed,
        encoder_kind="content_separating",
    )
    actor.load_state_dict(state, strict=True)
    actor.set_capture(False)
    for parameter in actor.parameters():
        parameter.requires_grad_(False)
    return actor


def _mc_value_target_error(
    actor: b1.RecurrentActorCritic, rewards: Sequence[float]
) -> float:
    carry = 0.0
    returns: list[float] = []
    for reward in reversed(tuple(float(value) for value in rewards)):
        carry = reward + b1.GAMMA * carry
        returns.append(carry)
    returns.reverse()
    target = torch.as_tensor(returns, dtype=torch.float32)
    values = torch.stack(actor._values).detach()
    return float(torch.abs(target - values).mean())


def _loss_for_learner(
    actor: b1.RecurrentActorCritic,
    learner: str,
    rewards: Sequence[float],
) -> tuple[torch.Tensor, dict[str, float]]:
    if learner == "MC_RETURN":
        value_target_error = _mc_value_target_error(actor, rewards)
        loss, parts = actor.episode_loss(rewards)
        return loss, {**parts, "value_target_error": value_target_error}
    if learner == "GAE_NORM":
        return actor.episode_loss_gae_norm(
            rewards,
            gae_lambda=GAE_LAMBDA,
            normalization_epsilon=NORMALIZATION_EPSILON,
        )
    raise ValueError("learner must be MC_RETURN or GAE_NORM")


def _train_actor(
    actor: b1.RecurrentActorCritic,
    learner: str,
    actor_index: int,
    plan: ExperimentPlan,
    counts: dict[str, int],
) -> tuple[
    list[dict[str, object]],
    dict[str, int],
    dict[str, dict[str, torch.Tensor]],
]:
    optimizer = torch.optim.Adam(actor.parameters(), lr=b1.ACTOR_LR)
    rows: list[dict[str, object]] = []
    coverage = {"SIGNAL_A": 0, "SIGNAL_B": 0, "NATIVE_NEUTRAL": 0}
    checkpoints = {"INIT": _snapshot(actor)}
    actor.set_capture(True)
    for root in range(plan.training_episodes_per_profile):
        for profile_index, profile in enumerate(plan.profiles):
            registered_id = episode_id("train", actor_index, profile_index, root)
            env = b1._make_env(profile, registered_id)
            runner = art.ArmEpisodeRunner(
                env,
                "LR",
                tape_seed=b1.TAPE_SEED,
                d_learned_fn=lambda _: True,
                body_fn=b2._correct_body,
                policy=actor,
            )
            runner.run_episode()
            optimizer.zero_grad(set_to_none=True)
            loss, parts = _loss_for_learner(actor, learner, env.reward_trace)
            loss.backward()
            grad_norm = float(
                nn.utils.clip_grad_norm_(actor.parameters(), b1.GRAD_NORM_CAP)
            )
            optimizer.step()
            counts["environment_transitions"] += roster_env.HORIZON
            counts["policy_calls"] += roster_env.HORIZON
            counts["actor_critic_optimizer_steps"] += 1
            counts["training_episodes"] += 1
            b2._coverage_add(coverage, env)
            rows.append(
                {
                    "order_index": len(rows),
                    "update": len(rows) + 1,
                    "root": root,
                    "profile": profile.name,
                    "episode_id": registered_id,
                    "action_noise_seed_identity": runner.action_noise_seed_identity,
                    "return": float(sum(env.reward_trace)),
                    "loss": float(loss.detach()),
                    "grad_norm_before_clip": grad_norm,
                    "grad_clip_exceeded": grad_norm > b1.GRAD_NORM_CAP,
                    **parts,
                }
            )
            if len(rows) == plan.mid_update:
                checkpoints["MID"] = _snapshot(actor)
    actor.set_capture(False)
    if len(rows) != plan.training_updates_per_actor:
        raise RuntimeError("B3 actor update count drifted from plan")
    checkpoints["FINAL"] = _snapshot(actor)
    if set(checkpoints) != set(CHECKPOINTS):
        raise RuntimeError("B3 did not freeze all registered checkpoints")
    return rows, coverage, checkpoints


def _noise_tape_digest(capture: b2._CapturePolicy) -> str:
    return b2._array_digest(*(item.noise for item in capture.inputs))


def _lifecycle_signature(runner: art.ArmEpisodeRunner) -> tuple[tuple[object, int], ...]:
    return tuple(
        (record.receipt.opportunity_identity, record.receipt.physical_tick)
        for record in runner.boundary_records
    )


def _evaluate_checkpoint(
    actor: b1.RecurrentActorCritic,
    learner: str,
    checkpoint: str,
    actor_seed: int,
    actor_index: int,
    plan: ExperimentPlan,
    counts: dict[str, int],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    rows: list[dict[str, object]] = []
    coverage = {"SIGNAL_A": 0, "SIGNAL_B": 0, "NATIVE_NEUTRAL": 0}
    for root in range(plan.evaluation_roots_per_checkpoint_profile):
        for profile_index, profile in enumerate(plan.profiles):
            registered_id = episode_id(checkpoint, actor_index, profile_index, root)
            runners: dict[str, art.ArmEpisodeRunner] = {}
            captures: dict[str, b2._CapturePolicy] = {}
            for arm in EVALUATION_ARMS:
                runners[arm], captures[arm] = b2._run_evaluation_arm(
                    actor, profile, registered_id, arm
                )
                counts["environment_transitions"] += roster_env.HORIZON
                counts["policy_calls"] += roster_env.HORIZON
                counts["evaluation_episodes"] += 1
            correct = runners["CORRECT"]
            roots_match = all(
                b1._same_root(correct.env, runners[arm].env)
                for arm in EVALUATION_ARMS[1:]
            )
            noise_digests = {
                arm: _noise_tape_digest(captures[arm]) for arm in EVALUATION_ARMS
            }
            lifecycle_signatures = {
                arm: _lifecycle_signature(runners[arm]) for arm in EVALUATION_ARMS
            }
            routes = {
                arm: tuple(
                    record.actuation_route for record in runners[arm].boundary_records
                )
                for arm in EVALUATION_ARMS
            }
            matching = {
                "same_world_root": roots_match,
                "same_initial_hidden": True,
                "same_lifecycle": len(set(lifecycle_signatures.values())) == 1,
                "same_real_route": len(set(routes.values())) == 1
                and set(next(iter(routes.values()))) == {"REAL"},
                "same_action_noise_tape": len(set(noise_digests.values())) == 1,
            }
            if not all(matching.values()):
                raise RuntimeError(f"B3 evaluation matching failed: {matching}")
            b2._coverage_add(coverage, correct.env)
            arms = {
                arm: b2._arm_record(runners[arm], captures[arm])
                for arm in EVALUATION_ARMS
            }
            correct_return = float(arms["CORRECT"]["episode_return"])
            swapped_return = float(arms["SWAPPED"]["episode_return"])
            neutral_return = float(arms["NATIVE_NEUTRAL"]["episode_return"])
            rows.append(
                {
                    "learner": learner,
                    "checkpoint": checkpoint,
                    "actor_seed": actor_seed,
                    "root": root,
                    "profile": profile.name,
                    "episode_id": registered_id,
                    "matching": matching,
                    "delivered_registered_body_labels": b2._delivered_body_labels(
                        correct.env
                    ),
                    "arms": arms,
                    "correct_minus_swapped": correct_return - swapped_return,
                    "correct_minus_native_neutral": correct_return - neutral_return,
                    "ab_diagnostics": b2._replay_ab_distances(
                        actor, captures["CORRECT"].inputs, correct
                    ),
                }
            )
    return rows, coverage


def _summary(values: Sequence[float]) -> dict[str, object]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        raise RuntimeError("B3 summary requires at least one root")
    return {
        "values": [float(value) for value in values],
        "count": int(array.size),
        "mean": float(array.mean()),
        "population_std": float(array.std(ddof=0)),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def _condition_summaries(
    rows: Sequence[Mapping[str, object]], plan: ExperimentPlan
) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for learner in plan.learners:
        for actor_seed in plan.actor_seeds:
            for profile in plan.profiles:
                checkpoint_means: dict[str, dict[str, float]] = {}
                for checkpoint in CHECKPOINTS:
                    selected = [
                        row
                        for row in rows
                        if row["learner"] == learner
                        and row["actor_seed"] == actor_seed
                        and row["profile"] == profile.name
                        and row["checkpoint"] == checkpoint
                    ]
                    swapped = _summary(
                        [float(row["correct_minus_swapped"]) for row in selected]
                    )
                    neutral = _summary(
                        [
                            float(row["correct_minus_native_neutral"])
                            for row in selected
                        ]
                    )
                    checkpoint_means[checkpoint] = {
                        "correct_minus_swapped": float(swapped["mean"]),
                        "correct_minus_native_neutral": float(neutral["mean"]),
                    }
                    summaries.append(
                        {
                            "learner": learner,
                            "actor_seed": actor_seed,
                            "profile": profile.name,
                            "checkpoint": checkpoint,
                            "correct_minus_swapped": swapped,
                            "correct_minus_native_neutral": neutral,
                        }
                    )
                for checkpoint in ("MID", "FINAL"):
                    summaries.append(
                        {
                            "learner": learner,
                            "actor_seed": actor_seed,
                            "profile": profile.name,
                            "checkpoint_change": f"{checkpoint}_MINUS_INIT",
                            "correct_minus_swapped": checkpoint_means[checkpoint][
                                "correct_minus_swapped"
                            ]
                            - checkpoint_means["INIT"]["correct_minus_swapped"],
                            "correct_minus_native_neutral": checkpoint_means[checkpoint][
                                "correct_minus_native_neutral"
                            ]
                            - checkpoint_means["INIT"][
                                "correct_minus_native_neutral"
                            ],
                        }
                    )
    return summaries


def _training_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    grad_norms = [float(row["grad_norm_before_clip"]) for row in rows]
    clip_count = sum(bool(row["grad_clip_exceeded"]) for row in rows)
    finite_keys = (
        "return",
        "loss",
        "actor_loss",
        "critic_loss",
        "value_target_error",
        "grad_norm_before_clip",
    )
    return {
        "all_finite": all(
            np.isfinite(float(row[key])) for row in rows for key in finite_keys
        ),
        "max_grad_norm_before_clip": max(grad_norms),
        "grad_clip_exceed_count": clip_count,
        "grad_clip_exceed_fraction": clip_count / len(rows),
    }


def run_experiment(mode: str = "smoke") -> dict[str, object]:
    plan = plan_for_mode(mode)
    if FULL_PLAN.training_transitions != 27_648:
        raise RuntimeError("registered B3 training budget drifted")
    if FULL_PLAN.evaluation_transitions != 31_104:
        raise RuntimeError("registered B3 evaluation budget drifted")
    if FULL_PLAN.maximum_transitions != 58_752:
        raise RuntimeError("registered B3 total budget drifted")
    counts = {
        "environment_transitions": 0,
        "policy_calls": 0,
        "actor_critic_optimizer_steps": 0,
        "training_episodes": 0,
        "evaluation_episodes": 0,
    }
    actors: list[dict[str, object]] = []
    evaluations: list[dict[str, object]] = []
    initial_digests: dict[str, dict[str, str]] = {learner: {} for learner in plan.learners}
    training_orders: dict[
        tuple[str, int], list[tuple[int, str, int, int]]
    ] = {}
    for learner in plan.learners:
        for actor_index, actor_seed in enumerate(plan.actor_seeds):
            actor = b1.RecurrentActorCritic(
                PROFILES[0].member_capacity,
                actor_seed,
                encoder_kind="content_separating",
            )
            initial_digests[learner][str(actor_seed)] = b2._state_digest(actor)
            training_rows, training_coverage, snapshots = _train_actor(
                actor, learner, actor_index, plan, counts
            )
            training_orders[(learner, actor_seed)] = [
                (
                    int(row["root"]),
                    str(row["profile"]),
                    int(row["episode_id"]),
                    int(row["action_noise_seed_identity"]),
                )
                for row in training_rows
            ]
            checkpoint_digests: dict[str, str] = {}
            evaluation_coverage: dict[str, dict[str, int]] = {}
            for checkpoint in CHECKPOINTS:
                frozen_actor = _actor_from_snapshot(actor_seed, snapshots[checkpoint])
                checkpoint_digests[checkpoint] = b2._state_digest(frozen_actor)
                checkpoint_rows, coverage = _evaluate_checkpoint(
                    frozen_actor,
                    learner,
                    checkpoint,
                    actor_seed,
                    actor_index,
                    plan,
                    counts,
                )
                evaluations.extend(checkpoint_rows)
                evaluation_coverage[checkpoint] = coverage
            actors.append(
                {
                    "learner": learner,
                    "actor_seed": actor_seed,
                    "initial_state_digest": initial_digests[learner][str(actor_seed)],
                    "checkpoint_state_digests": checkpoint_digests,
                    "training_profile_order": [
                        str(row["profile"]) for row in training_rows
                    ],
                    "training_delivered_body_coverage": training_coverage,
                    "evaluation_delivered_body_coverage": evaluation_coverage,
                    "training": training_rows,
                    "training_summary": _training_summary(training_rows),
                }
            )

    initial_state_equal = all(
        initial_digests["MC_RETURN"][str(seed)]
        == initial_digests["GAE_NORM"][str(seed)]
        for seed in plan.actor_seeds
    )
    training_order_equal = all(
        training_orders[("MC_RETURN", seed)]
        == training_orders[("GAE_NORM", seed)]
        for seed in plan.actor_seeds
    )
    evaluation_coordinates = {
        learner: {
            (
                str(row["checkpoint"]),
                int(row["actor_seed"]),
                str(row["profile"]),
                int(row["root"]),
                int(row["episode_id"]),
            )
            for row in evaluations
            if row["learner"] == learner
        }
        for learner in plan.learners
    }
    matching_proof = {
        "same_initial_state_by_seed": initial_state_equal,
        "same_training_root_profile_episode_noise_order_by_seed": training_order_equal,
        "same_content_separating_architecture": True,
        "same_adam_learning_rate": True,
        "same_gamma_and_grad_cap": True,
        "same_training_budget": True,
        "same_evaluation_roots_between_learners": evaluation_coordinates[
            "MC_RETURN"
        ]
        == evaluation_coordinates["GAE_NORM"],
        "all_evaluation_arm_matching_predicates": all(
            all(bool(value) for value in row["matching"].values())
            for row in evaluations
        ),
    }
    if not all(matching_proof.values()):
        raise RuntimeError(f"B3 learner matching proof failed: {matching_proof}")
    if counts["environment_transitions"] != plan.maximum_transitions:
        raise RuntimeError("actual B3 transitions differ from frozen plan")
    if counts["policy_calls"] != counts["environment_transitions"]:
        raise RuntimeError("B3 requires one policy call per environment transition")
    if counts["actor_critic_optimizer_steps"] != plan.training_episodes:
        raise RuntimeError("actual B3 optimizer steps differ from frozen plan")
    if counts["training_episodes"] != plan.training_episodes:
        raise RuntimeError("actual B3 training episodes differ from frozen plan")
    if counts["evaluation_episodes"] != plan.evaluation_episodes:
        raise RuntimeError("actual B3 evaluation episodes differ from frozen plan")

    return {
        "treatment": TREATMENT,
        "stage": "B_EXPLORATORY_REAL_TOY_EXPERIMENT",
        "mode": mode,
        "scientific_disposition": None,
        "registered_c_outcome_experiment_licensed": capability_gate.REGISTERED_OUTCOME_EXPERIMENT[
            "licensed"
        ],
        "real_implementation": True,
        "real_environment_calls": counts["environment_transitions"] > 0,
        "real_policy_calls": counts["policy_calls"] > 0,
        "real_actor_learner_updates": counts["actor_critic_optimizer_steps"] > 0,
        "real_evaluation_runner_calls": counts["evaluation_episodes"] > 0,
        "configuration": {
            "learners": list(plan.learners),
            "encoder_kind": "content_separating",
            "actor_seeds": list(plan.actor_seeds),
            "profiles": [profile.name for profile in plan.profiles],
            "checkpoints": list(CHECKPOINTS),
            "horizon": roster_env.HORIZON,
            "evaluation_arms": list(EVALUATION_ARMS),
            "actor_lr": b1.ACTOR_LR,
            "gamma": b1.GAMMA,
            "gae_lambda": GAE_LAMBDA,
            "normalization_epsilon": NORMALIZATION_EPSILON,
            "grad_norm_cap": b1.GRAD_NORM_CAP,
            "training_episodes_per_profile": plan.training_episodes_per_profile,
            "mid_update": plan.mid_update,
            "final_update": plan.training_updates_per_actor,
            "evaluation_roots_per_checkpoint_profile": plan.evaluation_roots_per_checkpoint_profile,
            "training_transitions": plan.training_transitions,
            "evaluation_transitions": plan.evaluation_transitions,
            "maximum_transitions": plan.maximum_transitions,
            "k_search": 0,
            "ordinary_external_team_reward_only": True,
            "episode_id_ranges": {
                "train": "6000000 + actor_index*100000 + profile_index*10000 + root",
                "INIT": "7000000 + actor_index*100000 + profile_index*10000 + root",
                "MID": "8000000 + actor_index*100000 + profile_index*10000 + root",
                "FINAL": "9000000 + actor_index*100000 + profile_index*10000 + root",
            },
        },
        "matching_proof": matching_proof,
        "counts": counts,
        "actors": actors,
        "evaluation_rows": evaluations,
        "condition_summaries": _condition_summaries(evaluations, plan),
        "mechanical_status": "MECHANICAL_B3_COMPLETE",
        "interpretation_boundary": (
            "B-level reward-credit learnability diagnostic only; it does not "
            "tune a valve, license C, or establish natural-distribution value, "
            "superiority, promotion, retirement, return, or deployment."
        ),
    }


def write_result(result: Mapping[str, object], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
