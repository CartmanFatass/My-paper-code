"""EOCIV-B4 matched parameter-free recurrent-retention experiment.

This candidate-local B experiment compares the B3 boundary-only slot input
with a receipt-validated policy-local segment latch.  It changes no trainable
actor/value parameter, external actuation, reward, host, or optimizer rule.
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
from experiments.candidates.eociv_lite import sibling_env as sib


TREATMENT = "EOCIV-B4-RECURRENT-RETENTION-LEARNABILITY"
CONDITIONS = ("EPHEMERAL_RNN", "SEGMENT_LATCH_RNN")
CHECKPOINTS = ("INIT", "MID", "FINAL")
ACTOR_SEEDS = b1.ACTOR_SEEDS
PROFILES = b1.PROFILES
EVALUATION_ARMS = b2.EVALUATION_ARMS
CRITICAL_EVENT_TIMES = (12, 36)
CONTRASTS = ("CORRECT_MINUS_SWAPPED", "CORRECT_MINUS_NATIVE_NEUTRAL")
GAE_LAMBDA = 0.95
NORMALIZATION_EPSILON = 1e-8


@dataclass(frozen=True)
class ExperimentPlan:
    mode: str
    conditions: tuple[str, ...]
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
        return len(self.conditions) * len(self.actor_seeds) * self.training_updates_per_actor

    @property
    def training_transitions(self) -> int:
        return self.training_episodes * roster_env.HORIZON

    @property
    def evaluation_episodes(self) -> int:
        return (
            len(self.conditions)
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


FULL_PLAN = ExperimentPlan("full", CONDITIONS, ACTOR_SEEDS, PROFILES, 32, 48, 4)
SMOKE_PLAN = ExperimentPlan("smoke", CONDITIONS, ACTOR_SEEDS[:1], PROFILES, 2, 3, 1)


def plan_for_mode(mode: str) -> ExperimentPlan:
    if mode == "smoke":
        return SMOKE_PLAN
    if mode == "full":
        return FULL_PLAN
    raise ValueError("mode must be 'smoke' or 'full'")


def episode_id(stage: str, actor_index: int, profile_index: int, root: int) -> int:
    bases = {
        "train": 10_000_000,
        "INIT": 11_000_000,
        "MID": 12_000_000,
        "FINAL": 13_000_000,
    }
    if stage not in bases or min(actor_index, profile_index, root) < 0:
        raise ValueError("unregistered B4 episode-id coordinate")
    # Condition is deliberately absent so both conditions use matched material.
    return bases[stage] + actor_index * 100_000 + profile_index * 10_000 + root


def _snapshot(actor: b1.RecurrentActorCritic) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in actor.state_dict().items()}


def _actor_from_snapshot(
    seed: int, state: Mapping[str, torch.Tensor]
) -> b1.RecurrentActorCritic:
    actor = b1.RecurrentActorCritic(
        PROFILES[0].member_capacity, seed, encoder_kind="content_separating"
    )
    actor.load_state_dict(state, strict=True)
    actor.set_capture(False)
    for parameter in actor.parameters():
        parameter.requires_grad_(False)
    return actor


def _slot_label(row: np.ndarray) -> str:
    values = np.asarray(row, dtype=np.float32)
    quantized = np.rint(values * np.float32(255.0)).astype(np.uint8)
    if not np.array_equal(values, quantized.astype(np.float32) / np.float32(255.0)):
        raise RuntimeError("retention evidence contains non-byte slot state")
    labels = {
        sib._pad_slot(b""): "ZERO",
        sib._pad_slot(sib.real_payload_body(sib.SHOCK_A)): "SIGNAL_A",
        sib._pad_slot(sib.real_payload_body(sib.SHOCK_B)): "SIGNAL_B",
        sib._pad_slot(sib.NEUTRAL_TOKEN): "NATIVE_NEUTRAL",
    }
    body = bytes(quantized)
    if body not in labels:
        raise RuntimeError("retention evidence contains unregistered slot bytes")
    return labels[body]


class RetentionPolicy:
    """Parameter-free slot-retention wrapper around the unchanged B3 actor."""

    def __init__(self, actor: b1.RecurrentActorCritic, condition: str):
        if condition not in CONDITIONS:
            raise ValueError(f"unknown retention condition: {condition}")
        self.actor = actor
        self.condition = condition
        self.capacity = actor.capacity
        self.latch = np.zeros((self.capacity, art.SLOT_DIM), dtype=np.float32)
        self.steps: list[dict[str, object]] = []
        self.acceptance_count = 0
        self.started_zero = True
        self.ended_zero = False

    def initial_state(self) -> np.ndarray:
        self.latch.fill(np.float32(0.0))
        self.steps = []
        self.acceptance_count = 0
        self.started_zero = bool(np.all(self.latch == np.float32(0.0)))
        self.ended_zero = False
        return self.actor.initial_state()

    def accept_verified_slot(
        self, delivered_slot_block: np.ndarray, active_mask: np.ndarray
    ) -> None:
        block = np.asarray(delivered_slot_block)
        mask = np.asarray(active_mask, dtype=np.bool_)
        expected = (self.capacity, art.SLOT_DIM)
        if block.shape != expected or block.dtype != np.float32:
            raise art.ReceiptError("verified latch input has wrong shape or dtype")
        if mask.shape != (self.capacity,):
            raise art.ReceiptError("verified latch active mask has wrong shape")
        self.acceptance_count += 1
        if self.condition == "SEGMENT_LATCH_RNN":
            self.latch[...] = block
            self.latch[~mask] = np.float32(0.0)
        else:
            self.latch.fill(np.float32(0.0))

    def forward(
        self,
        observations: np.ndarray,
        active_mask: np.ndarray,
        external_slot_block: np.ndarray,
        hidden: np.ndarray,
        noise: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        block = np.asarray(external_slot_block)
        mask = np.asarray(active_mask, dtype=np.bool_)
        if block.shape != self.latch.shape or block.dtype != np.float32:
            raise ValueError("external slot block has wrong shape or dtype")
        self.latch[~mask] = np.float32(0.0)
        if self.condition == "SEGMENT_LATCH_RNN":
            effective = self.latch.copy()
        else:
            effective = block.copy()
            effective[~mask] = np.float32(0.0)
        actions, kernel, new_hidden = self.actor.forward(
            observations, mask, effective, hidden, noise
        )
        self.steps.append(
            {
                "active_mask": mask.copy(),
                "external_slot_block": block.copy(),
                "effective_slot_block": effective.copy(),
                "noise": np.asarray(noise, dtype=np.float32).copy(),
                "recurrent_state": new_hidden.copy(),
                "action_kernel": kernel.copy(),
                "sampled_action": actions.copy(),
                "reward": None,
            }
        )
        return actions, kernel, new_hidden

    def end_episode(self) -> None:
        self.latch.fill(np.float32(0.0))
        self.ended_zero = bool(np.all(self.latch == np.float32(0.0)))


class RetentionEpisodeRunner(art.ArmEpisodeRunner):
    """Runner seam that admits latch bytes only after base receipt validation."""

    policy: RetentionPolicy

    def __init__(self, *args, policy: RetentionPolicy, **kwargs):
        super().__init__(*args, policy=policy, **kwargs)
        self.accepted_boundary_ticks: list[int] = []

    def bound_step(
        self,
        *,
        receipt: art.ActuationReceipt | None,
        opportunity: sib.Opportunity,
        actuation: sib.Actuation,
        observations: np.ndarray,
        active_mask: np.ndarray,
        slot_block: np.ndarray,
        noise: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, art.ActionReceipt]:
        self._verify_pre_receipt(receipt, opportunity, actuation, slot_block)
        # This is the only latch write.  The wrapper receives bytes and mask,
        # never event/shock/arm/route/reward/future or supervised information.
        self.policy.accept_verified_slot(slot_block, active_mask)
        actions, kernel, new_hidden = self.policy.forward(
            observations, active_mask, slot_block, self.hidden, noise
        )
        effective = self.policy.steps[-1]["effective_slot_block"]
        if not np.array_equal(effective, slot_block):
            raise art.ReceiptError("boundary effective slot differs from delivered slot")
        action_receipt = art.ActionReceipt(
            opportunity_identity=opportunity.identity,
            physical_tick=opportunity.physical_tick,
            route=actuation.route,
            decision_source=actuation.decision_source,
            ingestion_cost=actuation.ingestion_cost,
            policy_input_digest=art._digest(observations, active_mask, slot_block, self.hidden),
            kernel_digest=art._digest(kernel),
            sampled_action_digest=art._digest(actions),
            recurrent_write_digest=art._digest(new_hidden),
        )
        self.verify_action_receipt(
            action_receipt,
            opportunity=opportunity,
            actuation=actuation,
            observations=observations,
            active_mask=active_mask,
            slot_block=slot_block,
            hidden=self.hidden,
            kernel=kernel,
            actions=actions,
            new_hidden=new_hidden,
        )
        if receipt is None:
            raise art.ReceiptError("missing actuation receipt at consumption")
        self._consume(receipt)
        self.accepted_boundary_ticks.append(int(self.env.time))
        return actions, kernel, new_hidden, action_receipt

    def run_episode(self) -> float:
        env = self.env
        capacity = env.ledger.member_capacity
        try:
            while env.time < roster_env.HORIZON:
                time = env.time
                event_index = sib.EVENT_TIMES.index(time) if time in sib.EVENT_TIMES else None
                if event_index is not None:
                    slot_block, receipt, opportunity, actuation, w_bytes = self._boundary(event_index)
                else:
                    slot_block = np.zeros((capacity, art.SLOT_DIM), dtype=np.float32)
                view = env.observe()
                if event_index is not None:
                    actions, kernel, new_hidden, action_receipt = self.bound_step(
                        receipt=receipt,
                        opportunity=opportunity,
                        actuation=actuation,
                        observations=view.observations,
                        active_mask=view.active_mask,
                        slot_block=slot_block,
                        noise=self.noise[time],
                    )
                    self.boundary_records.append(
                        art.BoundaryRecord(receipt, action_receipt, w_bytes, actuation.route, actuation.slot)
                    )
                else:
                    actions, kernel, new_hidden = self.policy.forward(
                        view.observations,
                        view.active_mask,
                        slot_block,
                        self.hidden,
                        self.noise[time],
                    )
                self.step_traces.append(
                    art.StepTrace(
                        time=time,
                        input_digest=art._digest(
                            view.observations,
                            view.active_mask,
                            self.policy.steps[-1]["effective_slot_block"],
                            self.hidden,
                        ),
                        kernel_digest=art._digest(kernel),
                        action_digest=art._digest(actions),
                        hidden_digest=art._digest(new_hidden),
                    )
                )
                self.hidden = new_hidden
                env.step(actions)
                self.policy.steps[-1]["reward"] = float(env.reward_trace[-1])
            if self.accepted_boundary_ticks != list(sib.EVENT_TIMES):
                raise RuntimeError("B4 runner did not accept exactly the registered boundaries")
            return env.episode_total()
        finally:
            self.policy.end_episode()


def _make_runner(
    actor: b1.RecurrentActorCritic,
    condition: str,
    profile: roster_env.RosterProfile,
    registered_id: int,
    body_fn,
) -> RetentionEpisodeRunner:
    env = b1._make_env(profile, registered_id)
    policy = RetentionPolicy(actor, condition)
    runner = RetentionEpisodeRunner(
        env,
        "LR",
        tape_seed=b1.TAPE_SEED,
        d_learned_fn=lambda _: True,
        body_fn=body_fn,
        policy=policy,
    )
    runner.run_episode()
    return runner


def _train_actor(
    actor: b1.RecurrentActorCritic,
    condition: str,
    actor_index: int,
    plan: ExperimentPlan,
    counts: dict[str, int],
) -> tuple[list[dict[str, object]], dict[str, int], dict[str, dict[str, torch.Tensor]]]:
    optimizer = torch.optim.Adam(actor.parameters(), lr=b1.ACTOR_LR)
    rows: list[dict[str, object]] = []
    coverage = {"SIGNAL_A": 0, "SIGNAL_B": 0, "NATIVE_NEUTRAL": 0}
    checkpoints = {"INIT": _snapshot(actor)}
    actor.set_capture(True)
    for root in range(plan.training_episodes_per_profile):
        for profile_index, profile in enumerate(plan.profiles):
            registered_id = episode_id("train", actor_index, profile_index, root)
            runner = _make_runner(actor, condition, profile, registered_id, b2._correct_body)
            optimizer.zero_grad(set_to_none=True)
            loss, parts = actor.episode_loss_gae_norm(
                runner.env.reward_trace,
                gae_lambda=GAE_LAMBDA,
                normalization_epsilon=NORMALIZATION_EPSILON,
            )
            loss.backward()
            grad_norm = float(nn.utils.clip_grad_norm_(actor.parameters(), b1.GRAD_NORM_CAP))
            optimizer.step()
            counts["environment_transitions"] += roster_env.HORIZON
            counts["policy_calls"] += roster_env.HORIZON
            counts["actor_critic_optimizer_steps"] += 1
            counts["training_episodes"] += 1
            b2._coverage_add(coverage, runner.env)
            rows.append(
                {
                    "order_index": len(rows),
                    "update": len(rows) + 1,
                    "root": root,
                    "profile": profile.name,
                    "episode_id": registered_id,
                    "action_noise_seed_identity": runner.action_noise_seed_identity,
                    "return": float(sum(runner.env.reward_trace)),
                    "loss": float(loss.detach()),
                    "grad_norm_before_clip": grad_norm,
                    "grad_clip_exceeded": grad_norm > b1.GRAD_NORM_CAP,
                    "accepted_boundary_ticks": runner.accepted_boundary_ticks,
                    "episode_latch_started_zero": runner.policy.started_zero,
                    "episode_latch_ended_zero": runner.policy.ended_zero,
                    **parts,
                }
            )
            if len(rows) == plan.mid_update:
                checkpoints["MID"] = _snapshot(actor)
    actor.set_capture(False)
    if len(rows) != plan.training_updates_per_actor:
        raise RuntimeError("B4 actor update count drifted from plan")
    checkpoints["FINAL"] = _snapshot(actor)
    if set(checkpoints) != set(CHECKPOINTS):
        raise RuntimeError("B4 did not freeze all registered checkpoints")
    return rows, coverage, checkpoints


def _noise_tape_digest(runner: RetentionEpisodeRunner) -> str:
    return b2._array_digest(*(step["noise"] for step in runner.policy.steps))


def _lifecycle_signature(runner: RetentionEpisodeRunner) -> tuple[tuple[object, int], ...]:
    return tuple(
        (record.receipt.opportunity_identity, record.receipt.physical_tick)
        for record in runner.boundary_records
    )


def _lag_evidence(runner: RetentionEpisodeRunner) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event_time in CRITICAL_EVENT_TIMES:
        event_index = sib.EVENT_TIMES.index(event_time)
        focal = runner.boundary_records[event_index].receipt.opportunity_identity.receiver_member_key
        for lag in range(sib.SEGMENT_LENGTH):
            step = runner.policy.steps[event_time + lag]
            external = step["external_slot_block"][focal]
            effective = step["effective_slot_block"][focal]
            rows.append(
                {
                    "event_time": event_time,
                    "lag": lag,
                    "focal_member_key": int(focal),
                    "focal_active": bool(step["active_mask"][focal]),
                    "external_slot_vector": [float(value) for value in external],
                    "external_content_state": _slot_label(external),
                    "effective_internal_slot_vector": [float(value) for value in effective],
                    "effective_internal_content_label": _slot_label(effective),
                    "recurrent_state_vector": [
                        float(value) for value in step["recurrent_state"][focal]
                    ],
                    "action_kernel_vector": [
                        float(value) for value in step["action_kernel"][focal]
                    ],
                    "sampled_action_vector": [
                        float(value) for value in step["sampled_action"][focal]
                    ],
                    "reward": float(step["reward"]),
                }
            )
    return rows


def _arm_record(runner: RetentionEpisodeRunner) -> dict[str, object]:
    rewards = [float(value) for value in runner.env.reward_trace]
    return {
        "episode_return": float(sum(rewards)),
        "reward_trace": rewards,
        "segment_returns": b2._segment_returns(rewards),
        "routes": [row.actuation_route for row in runner.boundary_records],
        "receipt_count": len(runner.boundary_records),
        "ingestion_costs": [row.receipt.ingestion_cost for row in runner.boundary_records],
        "delivered_slot_content_labels": [
            _slot_label(art.slot_features(row.slot)) for row in runner.boundary_records
        ],
        "accepted_boundary_ticks": runner.accepted_boundary_ticks,
        "latch_started_zero": runner.policy.started_zero,
        "latch_ended_zero": runner.policy.ended_zero,
        "lag_evidence": _lag_evidence(runner),
    }


def _paired_lag_rows(
    condition: str,
    checkpoint: str,
    actor_seed: int,
    profile: str,
    root: int,
    arms: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    indexed = {
        arm: {
            (int(row["event_time"]), int(row["lag"])): row
            for row in arms[arm]["lag_evidence"]
        }
        for arm in EVALUATION_ARMS
    }
    rows: list[dict[str, object]] = []
    for contrast, control in (
        ("CORRECT_MINUS_SWAPPED", "SWAPPED"),
        ("CORRECT_MINUS_NATIVE_NEUTRAL", "NATIVE_NEUTRAL"),
    ):
        for event_time in CRITICAL_EVENT_TIMES:
            for lag in range(sib.SEGMENT_LENGTH):
                correct = indexed["CORRECT"][(event_time, lag)]
                other = indexed[control][(event_time, lag)]
                signed_reward = float(correct["reward"]) - float(other["reward"])
                rows.append(
                    {
                        "condition": condition,
                        "checkpoint": checkpoint,
                        "actor_seed": actor_seed,
                        "profile": profile,
                        "root": root,
                        "event_time": event_time,
                        "contrast": contrast,
                        "lag": lag,
                        "internal_slot_l1": float(
                            np.abs(
                                np.asarray(correct["effective_internal_slot_vector"])
                                - np.asarray(other["effective_internal_slot_vector"])
                            ).sum()
                        ),
                        "recurrent_state_l1": float(
                            np.abs(
                                np.asarray(correct["recurrent_state_vector"])
                                - np.asarray(other["recurrent_state_vector"])
                            ).sum()
                        ),
                        "kernel_l1": float(
                            np.abs(
                                np.asarray(correct["action_kernel_vector"])
                                - np.asarray(other["action_kernel_vector"])
                            ).sum()
                        ),
                        "sampled_action_l1": float(
                            np.abs(
                                np.asarray(correct["sampled_action_vector"])
                                - np.asarray(other["sampled_action_vector"])
                            ).sum()
                        ),
                        "signed_reward_difference": signed_reward,
                        "absolute_reward_difference": abs(signed_reward),
                    }
                )
    return rows


def _evaluate_checkpoint(
    actor: b1.RecurrentActorCritic,
    condition: str,
    checkpoint: str,
    actor_seed: int,
    actor_index: int,
    plan: ExperimentPlan,
    counts: dict[str, int],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, int]]:
    rows: list[dict[str, object]] = []
    paired_rows: list[dict[str, object]] = []
    coverage = {"SIGNAL_A": 0, "SIGNAL_B": 0, "NATIVE_NEUTRAL": 0}
    for root in range(plan.evaluation_roots_per_checkpoint_profile):
        for profile_index, profile in enumerate(plan.profiles):
            registered_id = episode_id(checkpoint, actor_index, profile_index, root)
            runners = {
                arm: _make_runner(actor, condition, profile, registered_id, b2.BODY_RULES[arm])
                for arm in EVALUATION_ARMS
            }
            for _ in EVALUATION_ARMS:
                counts["environment_transitions"] += roster_env.HORIZON
                counts["policy_calls"] += roster_env.HORIZON
                counts["evaluation_episodes"] += 1
            correct = runners["CORRECT"]
            noise_digests = {arm: _noise_tape_digest(runners[arm]) for arm in EVALUATION_ARMS}
            lifecycle = {arm: _lifecycle_signature(runners[arm]) for arm in EVALUATION_ARMS}
            routes = {
                arm: tuple(record.actuation_route for record in runners[arm].boundary_records)
                for arm in EVALUATION_ARMS
            }
            receipt_counts = {arm: len(runners[arm].boundary_records) for arm in EVALUATION_ARMS}
            ingestion_costs = {
                arm: tuple(record.receipt.ingestion_cost for record in runners[arm].boundary_records)
                for arm in EVALUATION_ARMS
            }
            matching = {
                "same_world_root": all(
                    b1._same_root(correct.env, runners[arm].env) for arm in EVALUATION_ARMS[1:]
                ),
                "same_initial_hidden_and_zero_latch": all(
                    runner.policy.started_zero for runner in runners.values()
                ),
                "same_lifecycle": len(set(lifecycle.values())) == 1,
                "same_real_route": len(set(routes.values())) == 1
                and set(next(iter(routes.values()))) == {"REAL"},
                "same_action_noise_tape": len(set(noise_digests.values())) == 1,
                "same_receipt_count": len(set(receipt_counts.values())) == 1
                and next(iter(receipt_counts.values())) == len(sib.EVENT_TIMES),
                "same_ingestion_cost": len(set(ingestion_costs.values())) == 1,
                "same_host_environment": len({type(runner.env) for runner in runners.values()}) == 1,
                "all_latches_zero_at_episode_end": all(
                    runner.policy.ended_zero for runner in runners.values()
                ),
            }
            if not all(matching.values()):
                raise RuntimeError(f"B4 evaluation matching failed: {matching}")
            b2._coverage_add(coverage, correct.env)
            arms = {arm: _arm_record(runners[arm]) for arm in EVALUATION_ARMS}
            correct_return = float(arms["CORRECT"]["episode_return"])
            swapped_return = float(arms["SWAPPED"]["episode_return"])
            neutral_return = float(arms["NATIVE_NEUTRAL"]["episode_return"])
            row = {
                "condition": condition,
                "checkpoint": checkpoint,
                "actor_seed": actor_seed,
                "root": root,
                "profile": profile.name,
                "episode_id": registered_id,
                "matching": matching,
                "delivered_registered_body_labels": b2._delivered_body_labels(correct.env),
                "arms": arms,
                "correct_minus_swapped": correct_return - swapped_return,
                "correct_minus_native_neutral": correct_return - neutral_return,
            }
            rows.append(row)
            paired_rows.extend(
                _paired_lag_rows(
                    condition, checkpoint, actor_seed, profile.name, root, arms
                )
            )
    return rows, paired_rows, coverage


def _summary(values: Sequence[float]) -> dict[str, object]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        raise RuntimeError("B4 summary requires at least one root")
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
    for condition in plan.conditions:
        for actor_seed in plan.actor_seeds:
            for profile in plan.profiles:
                means: dict[str, dict[str, float]] = {}
                for checkpoint in CHECKPOINTS:
                    selected = [
                        row
                        for row in rows
                        if row["condition"] == condition
                        and row["actor_seed"] == actor_seed
                        and row["profile"] == profile.name
                        and row["checkpoint"] == checkpoint
                    ]
                    swapped = _summary([float(row["correct_minus_swapped"]) for row in selected])
                    neutral = _summary(
                        [float(row["correct_minus_native_neutral"]) for row in selected]
                    )
                    means[checkpoint] = {
                        "correct_minus_swapped": float(swapped["mean"]),
                        "correct_minus_native_neutral": float(neutral["mean"]),
                    }
                    summaries.append(
                        {
                            "condition": condition,
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
                            "condition": condition,
                            "actor_seed": actor_seed,
                            "profile": profile.name,
                            "checkpoint_change": f"{checkpoint}_MINUS_INIT",
                            "correct_minus_swapped": means[checkpoint]["correct_minus_swapped"]
                            - means["INIT"]["correct_minus_swapped"],
                            "correct_minus_native_neutral": means[checkpoint][
                                "correct_minus_native_neutral"
                            ]
                            - means["INIT"]["correct_minus_native_neutral"],
                        }
                    )
    return summaries


def _paired_condition_changes(
    summaries: Sequence[Mapping[str, object]], plan: ExperimentPlan
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    changes = {
        (str(row["condition"]), int(row["actor_seed"]), str(row["profile"])): row
        for row in summaries
        if row.get("checkpoint_change") == "FINAL_MINUS_INIT"
    }
    for actor_seed in plan.actor_seeds:
        for profile in plan.profiles:
            ephemeral = changes[("EPHEMERAL_RNN", actor_seed, profile.name)]
            latched = changes[("SEGMENT_LATCH_RNN", actor_seed, profile.name)]
            row: dict[str, object] = {"actor_seed": actor_seed, "profile": profile.name}
            for key in ("correct_minus_swapped", "correct_minus_native_neutral"):
                difference = float(latched[key]) - float(ephemeral[key])
                row[key] = {
                    "segment_latch_minus_ephemeral_final_minus_init": difference,
                    "sign": int(np.sign(difference)),
                }
            rows.append(row)
    return rows


def _lag_summaries(
    rows: Sequence[Mapping[str, object]], plan: ExperimentPlan
) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    metric_keys = (
        "internal_slot_l1",
        "recurrent_state_l1",
        "kernel_l1",
        "sampled_action_l1",
        "signed_reward_difference",
        "absolute_reward_difference",
    )
    for condition in plan.conditions:
        for checkpoint in CHECKPOINTS:
            for actor_seed in plan.actor_seeds:
                for profile in plan.profiles:
                    for event_time in CRITICAL_EVENT_TIMES:
                        for contrast in CONTRASTS:
                            lag_rows: list[dict[str, object]] = []
                            absolute_means: list[float] = []
                            for lag in range(sib.SEGMENT_LENGTH):
                                selected = [
                                    row
                                    for row in rows
                                    if row["condition"] == condition
                                    and row["checkpoint"] == checkpoint
                                    and row["actor_seed"] == actor_seed
                                    and row["profile"] == profile.name
                                    and row["event_time"] == event_time
                                    and row["contrast"] == contrast
                                    and row["lag"] == lag
                                ]
                                metrics = {
                                    key: _summary([float(row[key]) for row in selected])
                                    for key in metric_keys
                                }
                                absolute_means.append(
                                    float(metrics["absolute_reward_difference"]["mean"])
                                )
                                lag_rows.append({"lag": lag, **metrics})
                            early = float(sum(absolute_means[:4]))
                            late = float(sum(absolute_means[4:]))
                            total = early + late
                            summaries.append(
                                {
                                    "condition": condition,
                                    "checkpoint": checkpoint,
                                    "actor_seed": actor_seed,
                                    "profile": profile.name,
                                    "event_time": event_time,
                                    "contrast": contrast,
                                    "lags": lag_rows,
                                    "early_reward_absolute_mass": early,
                                    "late_reward_absolute_mass": late,
                                    "early_reward_absolute_mass_share": early / total if total else 0.0,
                                    "late_reward_absolute_mass_share": late / total if total else 0.0,
                                }
                            )
    return summaries


def _training_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    keys = (
        "return",
        "loss",
        "actor_loss",
        "critic_loss",
        "value_target_error",
        "grad_norm_before_clip",
    )
    clip_count = sum(bool(row["grad_clip_exceeded"]) for row in rows)
    return {
        "all_finite": all(np.isfinite(float(row[key])) for row in rows for key in keys),
        "trajectory_statistics": {
            key: _summary([float(row[key]) for row in rows]) for key in keys
        },
        "grad_clip_exceed_count": clip_count,
        "grad_clip_exceed_fraction": clip_count / len(rows),
    }


def run_experiment(mode: str = "smoke") -> dict[str, object]:
    plan = plan_for_mode(mode)
    if (
        FULL_PLAN.training_episodes != 576
        or FULL_PLAN.training_transitions != 27_648
        or FULL_PLAN.evaluation_episodes != 648
        or FULL_PLAN.evaluation_transitions != 31_104
        or FULL_PLAN.maximum_transitions != 58_752
    ):
        raise RuntimeError("registered B4 full budget drifted")
    counts = {
        "environment_transitions": 0,
        "policy_calls": 0,
        "actor_critic_optimizer_steps": 0,
        "training_episodes": 0,
        "evaluation_episodes": 0,
    }
    actors: list[dict[str, object]] = []
    evaluations: list[dict[str, object]] = []
    paired_lag_rows: list[dict[str, object]] = []
    initial_digests: dict[str, dict[str, str]] = {condition: {} for condition in plan.conditions}
    training_orders: dict[tuple[str, int], list[tuple[int, str, int, int]]] = {}
    parameter_counts: dict[str, dict[str, int]] = {condition: {} for condition in plan.conditions}
    for condition in plan.conditions:
        for actor_index, actor_seed in enumerate(plan.actor_seeds):
            actor = b1.RecurrentActorCritic(
                PROFILES[0].member_capacity, actor_seed, encoder_kind="content_separating"
            )
            initial_digests[condition][str(actor_seed)] = b2._state_digest(actor)
            parameter_counts[condition][str(actor_seed)] = sum(
                parameter.numel() for parameter in actor.parameters()
            )
            training_rows, training_coverage, snapshots = _train_actor(
                actor, condition, actor_index, plan, counts
            )
            training_orders[(condition, actor_seed)] = [
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
                checkpoint_rows, checkpoint_paired, coverage = _evaluate_checkpoint(
                    frozen_actor,
                    condition,
                    checkpoint,
                    actor_seed,
                    actor_index,
                    plan,
                    counts,
                )
                evaluations.extend(checkpoint_rows)
                paired_lag_rows.extend(checkpoint_paired)
                evaluation_coverage[checkpoint] = coverage
            actors.append(
                {
                    "condition": condition,
                    "actor_seed": actor_seed,
                    "trainable_parameter_count": parameter_counts[condition][str(actor_seed)],
                    "latch_parameter_count": 0,
                    "initial_state_digest": initial_digests[condition][str(actor_seed)],
                    "checkpoint_state_digests": checkpoint_digests,
                    "training_profile_order": [str(row["profile"]) for row in training_rows],
                    "training_delivered_body_coverage": training_coverage,
                    "evaluation_delivered_body_coverage": evaluation_coverage,
                    "training": training_rows,
                    "training_summary": _training_summary(training_rows),
                }
            )
    condition_summaries = _condition_summaries(evaluations, plan)
    evaluation_coordinates = {
        condition: {
            (
                str(row["checkpoint"]),
                int(row["actor_seed"]),
                str(row["profile"]),
                int(row["root"]),
                int(row["episode_id"]),
            )
            for row in evaluations
            if row["condition"] == condition
        }
        for condition in plan.conditions
    }
    matching_proof = {
        "same_initial_state_by_seed": all(
            initial_digests["EPHEMERAL_RNN"][str(seed)]
            == initial_digests["SEGMENT_LATCH_RNN"][str(seed)]
            for seed in plan.actor_seeds
        ),
        "same_trainable_parameter_count_no_latch_parameters": all(
            parameter_counts["EPHEMERAL_RNN"][str(seed)]
            == parameter_counts["SEGMENT_LATCH_RNN"][str(seed)]
            for seed in plan.actor_seeds
        ),
        "same_training_root_profile_episode_noise_order_by_seed": all(
            training_orders[("EPHEMERAL_RNN", seed)]
            == training_orders[("SEGMENT_LATCH_RNN", seed)]
            for seed in plan.actor_seeds
        ),
        "same_content_separating_architecture": True,
        "same_gae_norm_loss": True,
        "same_adam_learning_rate_gamma_lambda_grad_cap": True,
        "same_training_budget_and_checkpoint_schedule": True,
        "same_evaluation_roots_between_conditions": evaluation_coordinates[
            "EPHEMERAL_RNN"
        ]
        == evaluation_coordinates["SEGMENT_LATCH_RNN"],
        "same_host_horizon_segments_shock_reward_and_external_channel": True,
        "all_evaluation_arm_matching_predicates": all(
            all(bool(value) for value in row["matching"].values()) for row in evaluations
        ),
    }
    if not all(matching_proof.values()):
        raise RuntimeError(f"B4 condition matching proof failed: {matching_proof}")
    if counts["environment_transitions"] != plan.maximum_transitions:
        raise RuntimeError("actual B4 transitions differ from frozen plan")
    if counts["policy_calls"] != counts["environment_transitions"]:
        raise RuntimeError("B4 requires one policy call per environment transition")
    if counts["actor_critic_optimizer_steps"] != plan.training_episodes:
        raise RuntimeError("actual B4 optimizer steps differ from frozen plan")
    if counts["training_episodes"] != plan.training_episodes:
        raise RuntimeError("actual B4 training episodes differ from frozen plan")
    if counts["evaluation_episodes"] != plan.evaluation_episodes:
        raise RuntimeError("actual B4 evaluation episodes differ from frozen plan")
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
            "conditions": list(plan.conditions),
            "encoder_kind": "content_separating",
            "learner": "GAE_NORM",
            "actor_seeds": list(plan.actor_seeds),
            "profiles": [profile.name for profile in plan.profiles],
            "checkpoints": list(CHECKPOINTS),
            "horizon": roster_env.HORIZON,
            "event_times": list(sib.EVENT_TIMES),
            "segment_length": sib.SEGMENT_LENGTH,
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
            "hypothetical_transitions": 0,
            "ordinary_external_team_reward_only": True,
            "episode_id_bases": {
                "train": 10_000_000,
                "INIT": 11_000_000,
                "MID": 12_000_000,
                "FINAL": 13_000_000,
            },
        },
        "matching_proof": matching_proof,
        "counts": counts,
        "actors": actors,
        "evaluation_rows": evaluations,
        "contrast_root_rows": paired_lag_rows,
        "condition_summaries": condition_summaries,
        "paired_condition_final_minus_init": _paired_condition_changes(
            condition_summaries, plan
        ),
        "lag_summaries": _lag_summaries(paired_lag_rows, plan),
        "mechanical_status": "MECHANICAL_B4_COMPLETE",
        "interpretation_boundary": (
            "Strictly nonterminal result-aware B diagnostic, not a B3 rerun or rescue. "
            "No outcome licenses C, tunes a valve, or establishes superiority, promotion, "
            "retirement, natural-distribution value, return, deployment, or generalization."
        ),
    }


def write_result(result: Mapping[str, object], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
