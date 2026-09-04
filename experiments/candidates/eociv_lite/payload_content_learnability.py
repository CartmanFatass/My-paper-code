"""EOCIV-B2 matched payload-content learnability experiment.

This candidate-local B experiment compares two representations on the same
real sibling roots.  Both actors learn only from ordinary external team reward;
the payload-content labels are used solely to define the legal receiver input.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np
import torch
from torch import nn

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import capability_gate
from experiments.candidates.eociv_lite import real_valve_learning as b1
from experiments.candidates.eociv_lite import sibling_env as sib


TREATMENT = "EOCIV-B2-PAYLOAD-CONTENT-LEARNABILITY"
ENCODER_KINDS = ("raw_byte", "content_separating")
ACTOR_SEEDS = b1.ACTOR_SEEDS
PROFILES = b1.PROFILES
EVALUATION_ARMS = ("CORRECT", "SWAPPED", "NATIVE_NEUTRAL")
TRAIN_EPISODES_PER_PROFILE = 32
EVALUATION_ROOTS_PER_PROFILE = 8


@dataclass(frozen=True)
class ExperimentPlan:
    mode: str
    encoder_kinds: tuple[str, ...]
    actor_seeds: tuple[int, ...]
    profiles: tuple[roster_env.RosterProfile, ...]
    train_episodes_per_profile: int
    evaluation_roots_per_profile: int

    @property
    def training_transitions(self) -> int:
        return (
            len(self.encoder_kinds)
            * len(self.actor_seeds)
            * len(self.profiles)
            * self.train_episodes_per_profile
            * roster_env.HORIZON
        )

    @property
    def evaluation_transitions(self) -> int:
        return (
            len(self.encoder_kinds)
            * len(self.actor_seeds)
            * len(self.profiles)
            * self.evaluation_roots_per_profile
            * len(EVALUATION_ARMS)
            * roster_env.HORIZON
        )

    @property
    def maximum_transitions(self) -> int:
        return self.training_transitions + self.evaluation_transitions

    @property
    def optimizer_steps(self) -> int:
        return (
            len(self.encoder_kinds)
            * len(self.actor_seeds)
            * len(self.profiles)
            * self.train_episodes_per_profile
        )

    @property
    def evaluation_episodes(self) -> int:
        return (
            len(self.encoder_kinds)
            * len(self.actor_seeds)
            * len(self.profiles)
            * self.evaluation_roots_per_profile
            * len(EVALUATION_ARMS)
        )


FULL_PLAN = ExperimentPlan(
    "full",
    ENCODER_KINDS,
    ACTOR_SEEDS,
    PROFILES,
    TRAIN_EPISODES_PER_PROFILE,
    EVALUATION_ROOTS_PER_PROFILE,
)
SMOKE_PLAN = ExperimentPlan(
    "smoke",
    ENCODER_KINDS,
    ACTOR_SEEDS[:1],
    PROFILES,
    1,
    1,
)


def plan_for_mode(mode: str) -> ExperimentPlan:
    if mode == "smoke":
        return SMOKE_PLAN
    if mode == "full":
        return FULL_PLAN
    raise ValueError("mode must be 'smoke' or 'full'")


def episode_id(stage: str, actor_index: int, profile_index: int, root: int) -> int:
    bases = {"train": 4_000_000, "evaluation": 5_000_000}
    if stage not in bases or min(actor_index, profile_index, root) < 0:
        raise ValueError("unregistered B2 episode-id coordinate")
    # Encoder kind is deliberately absent: raw/content see the same roots.
    return bases[stage] + actor_index * 100_000 + profile_index * 10_000 + root


def _correct_body(event_index: int, env: sib.EocivSiblingRosterEnv) -> bytes:
    if sib.CELL_CLASS[event_index] == "NEUTRAL":
        return sib.NEUTRAL_TOKEN
    return env.focal_payload(event_index)


def _swapped_body(event_index: int, env: sib.EocivSiblingRosterEnv) -> bytes:
    body = _correct_body(event_index, env)
    body_a = sib.real_payload_body(sib.SHOCK_A)
    body_b = sib.real_payload_body(sib.SHOCK_B)
    if body == sib.NEUTRAL_TOKEN:
        return sib.NEUTRAL_TOKEN
    if body == body_a:
        return body_b
    if body == body_b:
        return body_a
    raise RuntimeError("critical event body is not exact registered A/B content")


def _native_neutral_body(
    event_index: int, env: sib.EocivSiblingRosterEnv
) -> bytes:
    del event_index, env
    return sib.NEUTRAL_TOKEN


BODY_RULES: Mapping[
    str, Callable[[int, sib.EocivSiblingRosterEnv], bytes]
] = {
    "CORRECT": _correct_body,
    "SWAPPED": _swapped_body,
    "NATIVE_NEUTRAL": _native_neutral_body,
}


@dataclass(frozen=True)
class PolicyInput:
    observations: np.ndarray
    active_mask: np.ndarray
    slot_block: np.ndarray
    noise: np.ndarray


class _CapturePolicy:
    """Transparent actor wrapper retaining the actual evaluation inputs."""

    def __init__(self, actor: b1.RecurrentActorCritic):
        self.actor = actor
        self.inputs: list[PolicyInput] = []

    def initial_state(self) -> np.ndarray:
        self.inputs = []
        return self.actor.initial_state()

    def forward(
        self,
        observations: np.ndarray,
        active_mask: np.ndarray,
        slot_block: np.ndarray,
        hidden: np.ndarray,
        noise: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        self.inputs.append(
            PolicyInput(
                observations.copy(),
                active_mask.copy(),
                slot_block.copy(),
                noise.copy(),
            )
        )
        return self.actor.forward(
            observations, active_mask, slot_block, hidden, noise
        )


def _array_digest(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


def _state_digest(actor: b1.RecurrentActorCritic) -> str:
    digest = hashlib.sha256()
    for name, value in actor.state_dict().items():
        digest.update(name.encode("utf-8"))
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _delivered_body_label(body: bytes) -> str:
    labels = {
        sib.real_payload_body(sib.SHOCK_A): "SIGNAL_A",
        sib.real_payload_body(sib.SHOCK_B): "SIGNAL_B",
        sib.NEUTRAL_TOKEN: "NATIVE_NEUTRAL",
    }
    if body not in labels:
        raise RuntimeError("delivered body is outside the registered B2 alphabet")
    return labels[body]


def _delivered_body_labels(env: sib.EocivSiblingRosterEnv) -> list[str]:
    return [
        _delivered_body_label(_correct_body(event_index, env))
        for event_index in range(len(sib.EVENT_TIMES))
    ]


def _coverage_add(coverage: dict[str, int], env: sib.EocivSiblingRosterEnv) -> None:
    for label in _delivered_body_labels(env):
        coverage[label] += 1


def _train_actor(
    actor: b1.RecurrentActorCritic,
    actor_index: int,
    plan: ExperimentPlan,
    counts: dict[str, int],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    optimizer = torch.optim.Adam(actor.parameters(), lr=b1.ACTOR_LR)
    rows: list[dict[str, object]] = []
    coverage = {"SIGNAL_A": 0, "SIGNAL_B": 0, "NATIVE_NEUTRAL": 0}
    actor.set_capture(True)
    # Root-major order is registered and identical in both encoder conditions.
    for root in range(plan.train_episodes_per_profile):
        for profile_index, profile in enumerate(plan.profiles):
            registered_id = episode_id("train", actor_index, profile_index, root)
            env = b1._make_env(profile, registered_id)
            runner = art.ArmEpisodeRunner(
                env,
                "LR",
                tape_seed=b1.TAPE_SEED,
                d_learned_fn=lambda _: True,
                body_fn=_correct_body,
                policy=actor,
            )
            runner.run_episode()
            optimizer.zero_grad(set_to_none=True)
            loss, parts = actor.episode_loss(env.reward_trace)
            loss.backward()
            grad_norm = float(
                nn.utils.clip_grad_norm_(actor.parameters(), b1.GRAD_NORM_CAP)
            )
            optimizer.step()
            counts["environment_transitions"] += roster_env.HORIZON
            counts["policy_calls"] += roster_env.HORIZON
            counts["actor_critic_optimizer_steps"] += 1
            counts["training_episodes"] += 1
            _coverage_add(coverage, env)
            rows.append(
                {
                    "order_index": len(rows),
                    "root": root,
                    "profile": profile.name,
                    "episode_id": registered_id,
                    "return": float(sum(env.reward_trace)),
                    "loss": float(loss.detach()),
                    "grad_norm_before_clip": grad_norm,
                    **parts,
                }
            )
    actor.set_capture(False)
    for parameter in actor.parameters():
        parameter.requires_grad_(False)
        parameter.grad = None
    return rows, coverage


def _segment_returns(rewards: Sequence[float]) -> list[float]:
    return [
        float(sum(rewards[start : start + sib.SEGMENT_LENGTH]))
        for start in range(0, roster_env.HORIZON, sib.SEGMENT_LENGTH)
    ]


def _input_sequence_digest(inputs: Sequence[PolicyInput]) -> str:
    digest = hashlib.sha256()
    for item in inputs:
        for array in (
            item.observations,
            item.active_mask,
            item.slot_block,
            item.noise,
        ):
            digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


def _replay_ab_distances(
    actor: b1.RecurrentActorCritic,
    inputs: Sequence[PolicyInput],
    runner: art.ArmEpisodeRunner,
) -> list[dict[str, float | int]]:
    if len(inputs) != roster_env.HORIZON:
        raise RuntimeError("evaluation input capture is not one complete episode")
    hidden = actor.initial_state()
    boundaries = {
        event_time: runner.boundary_records[event_index]
        for event_index, event_time in enumerate(sib.EVENT_TIMES)
    }
    rows: list[dict[str, float | int]] = []
    for time, item in enumerate(inputs):
        if time in boundaries:
            record = boundaries[time]
            focal = record.receipt.opportunity_identity.receiver_member_key
            slot_a = item.slot_block.copy()
            slot_b = item.slot_block.copy()
            slot_a[focal] = art.slot_features(
                sib._pad_slot(sib.real_payload_body(sib.SHOCK_A))
            )
            slot_b[focal] = art.slot_features(
                sib._pad_slot(sib.real_payload_body(sib.SHOCK_B))
            )
            action_a, kernel_a, hidden_a = actor.diagnostic_step(
                item.observations,
                item.active_mask,
                slot_a,
                hidden,
                item.noise,
            )
            action_b, kernel_b, hidden_b = actor.diagnostic_step(
                item.observations,
                item.active_mask,
                slot_b,
                hidden,
                item.noise,
            )
            rows.append(
                {
                    "event_index": sib.EVENT_TIMES.index(time),
                    "physical_tick": time,
                    "receiver_member_key": int(focal),
                    "kernel_l1_mean": float(
                        np.abs(kernel_a[focal] - kernel_b[focal]).mean()
                    ),
                    "sampled_action_l1_mean": float(
                        np.abs(action_a[focal] - action_b[focal]).mean()
                    ),
                    "recurrent_state_l1_mean": float(
                        np.abs(hidden_a[focal] - hidden_b[focal]).mean()
                    ),
                }
            )
        _, _, hidden = actor.diagnostic_step(
            item.observations,
            item.active_mask,
            item.slot_block,
            hidden,
            item.noise,
        )
    return rows


def _run_evaluation_arm(
    actor: b1.RecurrentActorCritic,
    profile: roster_env.RosterProfile,
    registered_id: int,
    arm_name: str,
) -> tuple[art.ArmEpisodeRunner, _CapturePolicy]:
    env = b1._make_env(profile, registered_id)
    capture = _CapturePolicy(actor)
    runner = art.ArmEpisodeRunner(
        env,
        "LR",
        tape_seed=b1.TAPE_SEED,
        d_learned_fn=lambda _: True,
        body_fn=BODY_RULES[arm_name],
        policy=capture,
    )
    runner.run_episode()
    return runner, capture


def _arm_record(
    runner: art.ArmEpisodeRunner, capture: _CapturePolicy
) -> dict[str, object]:
    rewards = [float(value) for value in runner.env.reward_trace]
    return {
        "episode_return": float(sum(rewards)),
        "reward_trace": rewards,
        "segment_returns": _segment_returns(rewards),
        "routes": [row.actuation_route for row in runner.boundary_records],
        "kernel_digests": [row.kernel_digest for row in runner.step_traces],
        "sampled_action_digests": [row.action_digest for row in runner.step_traces],
        "recurrent_state_digests": [row.hidden_digest for row in runner.step_traces],
        "input_sequence_digest": _input_sequence_digest(capture.inputs),
    }


def _summary(values: Sequence[float]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        return {"count": 0, "mean": 0.0, "population_std": 0.0}
    return {
        "count": int(array.size),
        "mean": float(array.mean()),
        "population_std": float(array.std(ddof=0)),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def _evaluate_actor(
    initial_actor: b1.RecurrentActorCritic,
    trained_actor: b1.RecurrentActorCritic,
    actor_index: int,
    plan: ExperimentPlan,
    counts: dict[str, int],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    rows: list[dict[str, object]] = []
    coverage = {"SIGNAL_A": 0, "SIGNAL_B": 0, "NATIVE_NEUTRAL": 0}
    for root in range(plan.evaluation_roots_per_profile):
        for profile_index, profile in enumerate(plan.profiles):
            registered_id = episode_id(
                "evaluation", actor_index, profile_index, root
            )
            runners: dict[str, art.ArmEpisodeRunner] = {}
            captures: dict[str, _CapturePolicy] = {}
            for arm_name in EVALUATION_ARMS:
                runners[arm_name], captures[arm_name] = _run_evaluation_arm(
                    trained_actor, profile, registered_id, arm_name
                )
                counts["environment_transitions"] += roster_env.HORIZON
                counts["policy_calls"] += roster_env.HORIZON
                counts["evaluation_episodes"] += 1
            correct = runners["CORRECT"]
            if not all(
                b1._same_root(correct.env, runners[name].env)
                for name in EVALUATION_ARMS[1:]
            ):
                raise RuntimeError("matched evaluation arms do not share root material")
            _coverage_add(coverage, correct.env)
            arms = {
                name: _arm_record(runners[name], captures[name])
                for name in EVALUATION_ARMS
            }
            correct_value = float(arms["CORRECT"]["episode_return"])
            swapped_value = float(arms["SWAPPED"]["episode_return"])
            neutral_value = float(arms["NATIVE_NEUTRAL"]["episode_return"])
            correct_segments = [float(value) for value in arms["CORRECT"]["segment_returns"]]
            swapped_segments = [float(value) for value in arms["SWAPPED"]["segment_returns"]]
            neutral_segments = [
                float(value) for value in arms["NATIVE_NEUTRAL"]["segment_returns"]
            ]
            rows.append(
                {
                    "root": root,
                    "profile": profile.name,
                    "episode_id": registered_id,
                    "delivered_registered_body_labels": _delivered_body_labels(
                        correct.env
                    ),
                    "arms": arms,
                    "correct_minus_swapped": correct_value - swapped_value,
                    "correct_minus_native_neutral": correct_value - neutral_value,
                    "segment_correct_minus_swapped": [
                        left - right
                        for left, right in zip(correct_segments, swapped_segments)
                    ],
                    "segment_correct_minus_native_neutral": [
                        left - right
                        for left, right in zip(correct_segments, neutral_segments)
                    ],
                    "initial_ab_diagnostics": _replay_ab_distances(
                        initial_actor, captures["CORRECT"].inputs, correct
                    ),
                    "trained_ab_diagnostics": _replay_ab_distances(
                        trained_actor, captures["CORRECT"].inputs, correct
                    ),
                }
            )
    return rows, coverage


def _encoder_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    swapped = [float(row["correct_minus_swapped"]) for row in rows]
    neutral = [float(row["correct_minus_native_neutral"]) for row in rows]
    segment_count = roster_env.HORIZON // sib.SEGMENT_LENGTH
    return {
        "correct_minus_swapped": _summary(swapped),
        "correct_minus_native_neutral": _summary(neutral),
        "segment_correct_minus_swapped": [
            {
                "segment_index": segment_index,
                "start_tick": segment_index * sib.SEGMENT_LENGTH,
                "stop_tick": (segment_index + 1) * sib.SEGMENT_LENGTH,
                **_summary(
                    [
                        float(row["segment_correct_minus_swapped"][segment_index])
                        for row in rows
                    ]
                ),
            }
            for segment_index in range(segment_count)
        ],
        "segment_correct_minus_native_neutral": [
            {
                "segment_index": segment_index,
                "start_tick": segment_index * sib.SEGMENT_LENGTH,
                "stop_tick": (segment_index + 1) * sib.SEGMENT_LENGTH,
                **_summary(
                    [
                        float(
                            row["segment_correct_minus_native_neutral"][
                                segment_index
                            ]
                        )
                        for row in rows
                    ]
                ),
            }
            for segment_index in range(segment_count)
        ],
    }


def run_experiment(mode: str = "smoke") -> dict[str, object]:
    plan = plan_for_mode(mode)
    if FULL_PLAN.training_transitions != 27_648:
        raise RuntimeError("registered B2 training budget drifted")
    if FULL_PLAN.evaluation_transitions != 20_736:
        raise RuntimeError("registered B2 evaluation budget drifted")
    counts = {
        "environment_transitions": 0,
        "policy_calls": 0,
        "actor_critic_optimizer_steps": 0,
        "training_episodes": 0,
        "evaluation_episodes": 0,
    }
    encoder_rows: list[dict[str, object]] = []
    all_evaluations: list[dict[str, object]] = []
    initial_digests: dict[str, dict[str, str]] = {}
    for encoder_kind in plan.encoder_kinds:
        initial_digests[encoder_kind] = {}
        for actor_index, actor_seed in enumerate(plan.actor_seeds):
            initial_actor = b1.RecurrentActorCritic(
                PROFILES[0].member_capacity,
                actor_seed,
                encoder_kind=encoder_kind,
            )
            trained_actor = b1.RecurrentActorCritic(
                PROFILES[0].member_capacity,
                actor_seed,
                encoder_kind=encoder_kind,
            )
            initial_digest = _state_digest(initial_actor)
            if initial_digest != _state_digest(trained_actor):
                raise RuntimeError("matched initial actor state drifted")
            initial_digests[encoder_kind][str(actor_seed)] = initial_digest
            for parameter in initial_actor.parameters():
                parameter.requires_grad_(False)
            training_rows, training_body_coverage = _train_actor(
                trained_actor, actor_index, plan, counts
            )
            evaluations, evaluation_body_coverage = _evaluate_actor(
                initial_actor, trained_actor, actor_index, plan, counts
            )
            tagged_evaluations = [
                {
                    "encoder_kind": encoder_kind,
                    "actor_seed": actor_seed,
                    **row,
                }
                for row in evaluations
            ]
            all_evaluations.extend(tagged_evaluations)
            encoder_rows.append(
                {
                    "encoder_kind": encoder_kind,
                    "actor_seed": actor_seed,
                    "initial_state_digest": initial_digest,
                    "trained_state_digest": _state_digest(trained_actor),
                    "training_profile_order": [
                        row["profile"] for row in training_rows
                    ],
                    "training_delivered_body_coverage": training_body_coverage,
                    "evaluation_delivered_body_coverage": evaluation_body_coverage,
                    "training": training_rows,
                    "evaluation_summary": _encoder_summary(evaluations),
                    "instability_diagnostics": {
                        "all_finite": all(
                            np.isfinite(float(row[key]))
                            for row in training_rows
                            for key in (
                                "return",
                                "loss",
                                "actor_loss",
                                "critic_loss",
                                "grad_norm_before_clip",
                            )
                        ),
                        "max_grad_norm_before_clip": max(
                            float(row["grad_norm_before_clip"])
                            for row in training_rows
                        ),
                    },
                }
            )
    if counts["environment_transitions"] != plan.maximum_transitions:
        raise RuntimeError("actual B2 transitions differ from frozen plan")
    if counts["policy_calls"] != counts["environment_transitions"]:
        raise RuntimeError("B2 requires one policy call per environment transition")
    if counts["actor_critic_optimizer_steps"] != plan.optimizer_steps:
        raise RuntimeError("actual B2 optimizer steps differ from frozen plan")
    if counts["evaluation_episodes"] != plan.evaluation_episodes:
        raise RuntimeError("actual B2 evaluation episodes differ from frozen plan")
    for actor_seed in plan.actor_seeds:
        if (
            initial_digests["raw_byte"][str(actor_seed)]
            != initial_digests["content_separating"][str(actor_seed)]
        ):
            raise RuntimeError("encoder conditions do not share matched initialization")
    summaries = {
        encoder: _encoder_summary(
            [row for row in all_evaluations if row["encoder_kind"] == encoder]
        )
        for encoder in plan.encoder_kinds
    }
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
        "real_actor_learner_updates": counts[
            "actor_critic_optimizer_steps"
        ] > 0,
        "real_evaluation_runner_calls": counts["evaluation_episodes"] > 0,
        "configuration": {
            "encoder_kinds": list(plan.encoder_kinds),
            "actor_seeds": list(plan.actor_seeds),
            "profiles": [profile.name for profile in plan.profiles],
            "horizon": roster_env.HORIZON,
            "event_times": list(sib.EVENT_TIMES),
            "evaluation_arms": list(EVALUATION_ARMS),
            "actor_lr": b1.ACTOR_LR,
            "gamma": b1.GAMMA,
            "grad_norm_cap": b1.GRAD_NORM_CAP,
            "train_episodes_per_profile": plan.train_episodes_per_profile,
            "evaluation_roots_per_profile": plan.evaluation_roots_per_profile,
            "training_transitions": plan.training_transitions,
            "evaluation_transitions": plan.evaluation_transitions,
            "maximum_transitions": plan.maximum_transitions,
            "k_search": 0,
            "episode_id_ranges": {
                "train": "4000000 + actor_index*100000 + profile_index*10000 + root",
                "evaluation": "5000000 + actor_index*100000 + profile_index*10000 + root",
            },
            "training_body_rule": "critical actual A/B; neutral registered native-neutral",
            "ordinary_external_team_reward_only": True,
        },
        "counts": counts,
        "actors": encoder_rows,
        "evaluation_rows": all_evaluations,
        "encoder_summaries": summaries,
        "mechanical_status": "MECHANICAL_B2_COMPLETE",
        "interpretation_boundary": (
            "B-level payload-content learnability diagnostic only; it does not "
            "tune or evaluate the valve, rerun B1 arms, license C, or establish "
            "natural-distribution value, superiority, promotion, or retirement."
        ),
    }


def write_result(result: Mapping[str, object], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
