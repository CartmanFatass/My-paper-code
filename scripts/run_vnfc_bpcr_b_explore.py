"""Readiness/runtime contract for VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R01.

This Class-B object uses revision-09 only as engineering substrate.  It does
not call the old full panel, exact reducer, CUT arm, frontier, or atomic result
publication.  The current substrate cannot construct the PS-B0 diagnostic
null/tie state without ambiguity, so runtime is fail-closed REPAIR_REQUIRED.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import copy
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence

import numpy as np
import torch

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import (
    native_build_key,
    native_source_sha256,
    require_cpp_batched_backend,
    run_native_fixture_batch,
)
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.empirical_training import _model_inputs, _normal_source_shape, make_optimizer
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import BCRHFixture, EpisodeFixture, GeneralAgentState
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.production import require_native_production
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.rng import address
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.services import _draw_below, _shuffle
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.torch_models import DirectSetAR, MAPR4, direct_parameter_shapes, mapr_parameter_shapes, materialize_external_initialization
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.training import frozen_minibatches, gae_terminal, normalize_advantages, ppo_loss


RUN_REVISION = "VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R01"
RUN_NAMESPACE = RUN_REVISION
IMPLEMENTATION_READY = False
IMPLEMENTATION_BLOCKER = (
    "R01 is not implementation-ready: the source-bound PS-B0 actual-path adapter is absent; "
    "complete measured external telemetry has not been demonstrated; shadow recovery is directly "
    "observed only on the shadow host and remains an equivalence-bounded inference for the primary host"
)
DEBUG_STAGE = "B0-DEBUG"
PRIMARY_STAGE = "B1-B3-PRIMARY"
OPTIONAL_STAGE = "B4-B5-OPTIONAL"
DEBUG_SEED = 2026090101
PRIMARY_SEEDS = (2026090111, 2026090121, 2026090131)
OPTIONAL_SEEDS = (2026090141, 2026090151)
OPTIONAL_REASONS = ("training_variance", "technical_issue")
ARMS = ("MAPR", "DIRECT")
ROSTERS = (3, 5, 7)
ZONES = (1, 2)
STATE_KINDS = ("t0", "later_fixed_or_acquiring", "diagnostic_null_tie")
PRESENTATIONS = ("canonical", "reverse", "cyclic", "seed_fixed_random")
CHECKPOINTS = ("initial", "final")
GIB = 1024**3
MINIMUM_AVAILABLE_BYTES = 4 * GIB
PREFLIGHT_FRESH_SECONDS = 300
TELEMETRY_SCHEMA = "VNFC_BPCR_BEXP_R01_EXTERNAL_TELEMETRY_V1"
SHADOW_SCHEMA = "VNFC_BPCR_BEXP_R01_DETERMINISTIC_SHADOW_TELEMETRY_V1"
REQUIRED_TELEMETRY_FIELDS = frozenset({
    "telemetry_schema", "telemetry_terminal",
    "stage_wall_seconds", "end_to_end_wall_seconds", "stage_cpu_seconds",
    "end_to_end_cpu_seconds", "process_tree_peak_rss_bytes",
    "available_physical_bytes", "effective_available_bytes",
    "native_integrated_ticks", "scientific_work_transitions_per_second",
    "worker_count", "threads_per_worker", "scratch_peak_bytes",
    "durable_peak_bytes", "io_read_bytes", "io_write_bytes",
    "parameter_count_by_arm", "forward_calls_by_arm", "backward_calls_by_arm",
    "flop_exposure_by_arm", "primary_host_calls", "shadow_host_calls",
    "total_host_call_multiplier",
})

_ACTUAL_SOURCE_PATHS = (
    "scripts/run_vnfc_bpcr_b_explore.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/contracts.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/empirical_contract.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/empirical_training.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/fixtures.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/models.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native_backend.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/numeric.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/production.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/rng.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/services.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/torch_models.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/training.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_backend.cpp",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_checker.hpp",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp",
    "experiments/candidates/variable_n_fleet_churn_b_explore/__init__.py",
    "experiments/candidates/variable_n_fleet_churn_b_explore/native_backend.py",
    "experiments/candidates/variable_n_fleet_churn_b_explore/native/telemetry_backend.cpp",
    "docs/research/candidates/variable_n_fleet_churn/VNFC_UAV_BOUNDED_POST_CHURN_RECOVERY_SCIENCE_CARD.md",
    "docs/research/candidates/variable_n_fleet_churn/VNFC_TARGET_EXCLUSIVE_POST_CHURN_RECOVERY_SCIENCE_CARD.md",
)

FORBIDDEN_N7_CONTROL_SURFACES = (
    "n7_tuning_callback", "checkpoint_selector", "seed_selector",
    "heldout_adaptation_callback",
)
OBSERVATION_SCHEMA = {
    "return_and_recovery": (
        "J_ext", "R_fail_60", "U_total", "U_intact", "final_minus_initial",
        "paired_mapr_minus_direct", "paired_mapr_minus_bcrh",
        "failed_zone_first_service_seconds", "failed_zone_reacquisition_seconds",
        "failed_zone_zero_service_seconds_0_60", "zone", "seed", "world",
    ),
    "validity": (
        "mapr_relabel_mismatch_count", "direct_relabel_mismatch_count",
        "hard_safety_valid", "exclusivity_valid", "termination_valid", "finite_values",
        "action_sensitivity", "direct_residual_total_variation",
        "direct_physical_command_change", "bcrh_candidate_count",
        "bcrh_scorer_checker_equal", "bcrh_independent_enumerator_equal", "bcrh_hard_valid",
    ),
    "optimization": (
        "actor_loss", "critic_loss", "entropy_loss", "total_loss",
        "advantage_variance", "return_variance", "preclip_gradient_norm",
        "policy_entropy", "nonfinite_update_count", "parameter_count",
        "forward_call_count", "backward_call_count",
    ),
}


class BExploreContractError(RuntimeError):
    pass


class TelemetrySink(Protocol):
    schema: str
    fields: Sequence[str]

    def emit(self, payload: Mapping[str, object]) -> None: ...


@dataclass(frozen=True)
class BExploreRunConfig:
    stage: str
    seed: int
    updates: int
    optional_reason: str | None = None
    optional_reason_scope: str | None = None

    def validate(self) -> None:
        if self.stage == DEBUG_STAGE:
            expected_seeds, expected_updates = (DEBUG_SEED,), 8
            if self.optional_reason is not None or self.optional_reason_scope is not None:
                raise BExploreContractError("DEBUG does not accept an optional-seed reason")
        elif self.stage == PRIMARY_STAGE:
            expected_seeds, expected_updates = PRIMARY_SEEDS, 64
            if self.optional_reason is not None or self.optional_reason_scope is not None:
                raise BExploreContractError("PRIMARY does not accept an optional-seed reason")
        elif self.stage == OPTIONAL_STAGE:
            expected_seeds, expected_updates = OPTIONAL_SEEDS, 64
            if self.optional_reason not in OPTIONAL_REASONS:
                raise BExploreContractError("OPTIONAL requires training_variance or technical_issue")
            scope = "N3_N5_TRAINING_ONLY" if self.optional_reason == "training_variance" else "TECHNICAL_PRE_N7"
            if self.optional_reason_scope != scope:
                raise BExploreContractError("OPTIONAL reason scope must be non-N7 and reason-specific")
        else:
            raise BExploreContractError("unknown BEXP R01 stage")
        if self.seed not in expected_seeds or self.updates != expected_updates:
            raise BExploreContractError("stage seed/update budget differs from BEXP R01")

    @property
    def namespace(self) -> str:
        self.validate()
        return f"{RUN_NAMESPACE}/{self.stage}/{self.seed}"


def derive_seed_master(config: BExploreRunConfig) -> dict[str, object]:
    """Derive the only permitted master; there is no external-master seam."""
    config.validate()
    label = b"HMASD/VNFC-BPCR-BEXP-R01/SEED-MASTER/SHA256/v1\0"
    master = hashlib.sha256(label + config.seed.to_bytes(8, "big", signed=False)).digest()
    return {
        "derivation": "SHA-256(label || uint64_be(exact_seed))",
        "label_sha256": hashlib.sha256(label).hexdigest(), "seed": config.seed,
        "master": master, "master_digest": hashlib.sha256(master).hexdigest(),
        "external_master_override": False,
    }


def expected_counts(config: BExploreRunConfig) -> dict[str, int]:
    config.validate()
    learned_checkpoints = 1 if config.stage == DEBUG_STAGE else 2
    episodes = config.updates * 16
    transitions = config.updates * 96
    steps = config.updates * 16
    learned_eval = 6 * 8 * learned_checkpoints * 2
    return {
        "episodes_per_arm_per_update": 16,
        "joint_transitions_per_arm_per_update": 96,
        "optimizer_steps_per_arm_per_update": 16,
        "training_episodes_per_arm": episodes,
        "joint_transitions_per_arm": transitions,
        "optimizer_steps_per_arm": steps,
        "training_episodes_total": 2 * episodes,
        "joint_transitions_total": 2 * transitions,
        "optimizer_steps_total": 2 * steps,
        "learned_evaluation_rollouts": learned_eval,
        "bcrh_evaluation_rollouts": 16,
        "evaluation_rollouts_total": learned_eval + 16,
        "ps_b0_state_comparisons_not_rollouts": 288,
    }


def sequence_counts() -> dict[str, dict[str, int]]:
    debug = expected_counts(BExploreRunConfig(DEBUG_STAGE, DEBUG_SEED, 8))
    one_primary = expected_counts(BExploreRunConfig(PRIMARY_STAGE, PRIMARY_SEEDS[0], 64))
    one_optional = expected_counts(BExploreRunConfig(OPTIONAL_STAGE, OPTIONAL_SEEDS[0], 64, "training_variance", "N3_N5_TRAINING_ONLY"))
    keys = ("training_episodes_total", "joint_transitions_total", "optimizer_steps_total", "evaluation_rollouts_total")
    primary = {key: one_primary[key] * 3 for key in keys}
    optional = {key: one_optional[key] * 2 for key in keys}
    debug_selected = {key: debug[key] for key in keys}
    return {
        "debug": debug_selected, "primary_three_seeds": primary, "optional_two_seeds": optional,
        "maximum": {key: debug_selected[key] + primary[key] + optional[key] for key in keys},
    }


def evaluation_plan(config: BExploreRunConfig) -> dict[str, object]:
    config.validate()
    checkpoints = ("final",) if config.stage == DEBUG_STAGE else CHECKPOINTS
    learned = tuple(
        {"roster_size": n, "failed_zone": zone, "world_row": row, "checkpoint": checkpoint, "arm": arm}
        for n in ROSTERS for zone in ZONES for row in range(8)
        for checkpoint in checkpoints for arm in ARMS
    )
    bcrh = tuple(
        {"roster_size": 7, "failed_zone": zone, "world_row": row, "arm": "BCRH", "include_candidate_records": False}
        for zone in ZONES for row in range(8)
    )
    if len(learned) != expected_counts(config)["learned_evaluation_rollouts"]:
        raise AssertionError("BEXP R01 evaluation allocation differs")
    return {
        "learned": learned, "bcrh": bcrh,
        "common_worlds_across_arms_and_checkpoints": True,
        "training_world_namespace": f"{config.namespace}/TRAIN-N3-N5",
        "evaluation_train_support_namespace": f"{config.namespace}/EVAL-N3-N5",
        "heldout_n7_world_namespace": f"{config.namespace}/HELDOUT-N7-UNOPENED",
        "n7_namespace_disjoint_from_training": True,
        "freeze_before_n7": ("training", "adaptation", "checkpoint_schedule", "seed_count_choice"),
        "forbidden_n7_control_surfaces": FORBIDDEN_N7_CONTROL_SURFACES,
        "fresh_relabel_each_learned_decision": True,
        "required_relabel_mismatch_count": {"MAPR": 0, "DIRECT": 0},
    }


@dataclass(frozen=True, repr=False)
class _SeedRNG:
    master: bytes

    def word(self, coordinate: object, *, now: object) -> int:
        del now
        return int.from_bytes(hmac.new(self.master, coordinate.encode(), hashlib.sha256).digest()[:8], "big")  # type: ignore[attr-defined]

    def normal_array(self, shape: tuple[int, ...], builder: object, *, now: object) -> np.ndarray:
        count = math.prod(shape); values = []; scale = float(1 << 64)
        for pair in range((count + 1) // 2):
            u1 = (self.word(builder(2 * pair), now=now) + .5) / scale  # type: ignore[operator]
            u2 = (self.word(builder(2 * pair + 1), now=now) + .5) / scale  # type: ignore[operator]
            radius = math.sqrt(-2 * math.log(u1)); angle = 2 * math.pi * u2
            values.extend((radius * math.cos(angle), radius * math.sin(angle)))
        return np.asarray(values[:count], dtype=np.float64).reshape(shape)


def _build_world(rng: _SeedRNG, config: BExploreRunConfig, *, purpose: str, roster_size: int, failed_zone: int, row: int, now: datetime) -> EpisodeFixture:
    if roster_size not in ROSTERS or failed_zone not in ZONES:
        raise BExploreContractError("BEXP world cell differs")
    common: dict[str, object] = {"replicate_role": "BPCR-REP-00", "purpose": f"{config.namespace}/{purpose}", "roster_size": roster_size, "failed_zone": failed_zone, "update_or_panel_row": row, "episode_row": row, "physical_time": 0}
    domain = "training/world" if purpose == "training" else "conclusion/world"
    base = {**common, "domain": domain}
    selected = _shuffle(tuple(range(1, 9)), rng, base, now)[:roster_size + 1]  # type: ignore[arg-type]
    order = _shuffle(selected, rng, {**base, "purpose": f"{config.namespace}/{purpose}/opaque-rank"}, now)  # type: ignore[arg-type]
    opaque = {rank: index + 1 for index, rank in enumerate(order)}
    types = ((1, 1, 2), (2, 0, 2), (3, 1, 1), (4, 0, 1), (5, 1, 2), (6, 0, 2), (7, 1, 1), (8, 0, 1))
    typed = {rank: (fast, radio) for rank, fast, radio in types}
    agents = tuple(GeneralAgentState(rank, opaque[rank], *typed[rank]) for rank in selected)
    q1: list[int] = []; q2: list[int] = []; h1: list[int] = []; h2: list[int] = []; states: list[int] = []
    for axis in range(4):
        value, _ = _draw_below(rng, 2, {**base, "purpose": f"{config.namespace}/{purpose}/initial-{axis}"}, 0, now)  # type: ignore[arg-type]
        states.append(value)
    for epoch in range(12):
        q1.append(states[0] + 1); q2.append(states[1] + 1); h1.append(states[2]); h2.append(states[3])
        if epoch < 11:
            for axis in range(4):
                obstruction = axis >= 2; numerators = ((8, 2), (3, 7)) if not obstruction else ((4, 1), (2, 3)); denominator = 10 if not obstruction else 5
                draw, _ = _draw_below(rng, denominator, {**base, "purpose": f"{config.namespace}/{purpose}/transition-{axis}", "physical_time": -100 + 20 * epoch}, 0, now)  # type: ignore[arg-type]
                states[axis] = 0 if draw < numerators[states[axis]][0] else 1
    presentation_domain = "training/presentation" if purpose == "training" else "conclusion/presentation"
    presentations = tuple(_shuffle(selected, rng, {**common, "domain": presentation_domain, "purpose": f"{config.namespace}/{purpose}/presentation", "physical_time": 20 * epoch}, now) for epoch in range(6))  # type: ignore[arg-type]
    fixture = EpisodeFixture(failed_zone, agents, tuple(q1), tuple(q2), tuple(h1), tuple(h2), ((None, None, None, None),) * 6, presentations)
    fixture.validate(); return fixture


def _initialize_learners(config: BExploreRunConfig, rng: _SeedRNG, now: datetime) -> dict[str, object]:
    base: dict[str, tuple[str, object]] = {}; residual: dict[str, tuple[str, object]] = {}
    for name, shape in mapr_parameter_shapes().items():
        if len(shape) != 2:
            continue
        builder = lambda draw, n=name: address(replicate_role="BPCR-REP-00", domain="model-initialization/base", purpose=f"{config.namespace}/{n}", roster_size=3, failed_zone=1, update_or_panel_row=0, episode_row=0, physical_time=0, draw=draw)
        base[name] = ("model-initialization/base", rng.normal_array(_normal_source_shape(shape), builder, now=now))
    for name in ("residual.0.weight", "residual.1.weight"):
        shape = direct_parameter_shapes()[name]
        builder = lambda draw, n=name: address(replicate_role="BPCR-REP-00", domain="model-initialization/direct-residual", purpose=f"{config.namespace}/{n}", roster_size=3, failed_zone=1, update_or_panel_row=0, episode_row=0, physical_time=0, draw=draw)
        residual[name] = ("model-initialization/direct-residual", rng.normal_array(_normal_source_shape(shape), builder, now=now))
    mapr_parameters, direct_parameters = materialize_external_initialization(base, residual)
    if not all(torch.equal(mapr_parameters[name], direct_parameters["base." + name]) for name in mapr_parameters):
        raise BExploreContractError("MAPR/DIRECT homologous base initialization differs")
    if torch.count_nonzero(direct_parameters["residual.out.weight"]) or torch.count_nonzero(direct_parameters["residual.out.bias"]):
        raise BExploreContractError("DIRECT initial containing residual output differs")
    mapr = MAPR4(mapr_parameters); direct = DirectSetAR(direct_parameters)
    return {"models": {"MAPR": mapr, "DIRECT": direct}, "optimizers": {"MAPR": make_optimizer(mapr), "DIRECT": make_optimizer(direct)}}


def _validate_model_output(output: Mapping[str, object], *, context: str) -> None:
    required = {"command", "log_probability", "token_entropies", "value", "token_probabilities"}
    if not required <= set(output):
        raise BExploreContractError(f"{context}: learned output tensor inventory differs")
    for name in required:
        value = output[name]
        if not isinstance(value, torch.Tensor) or not bool(torch.isfinite(value).all()):
            raise BExploreContractError(f"{context}: nonfinite learned {name}")
    probabilities = output["token_probabilities"]
    if bool((probabilities < 0).any()) or bool((probabilities > 1).any()):  # type: ignore[operator]
        raise BExploreContractError(f"{context}: action probability is outside [0,1]")
    sums = probabilities.sum(-1)  # type: ignore[union-attr]
    if not bool(torch.allclose(sums, torch.ones_like(sums), rtol=1e-12, atol=1e-12)):
        raise BExploreContractError(f"{context}: action probability mass differs")


def _train_one_update(config: BExploreRunConfig, rng: _SeedRNG, model: MAPR4 | DirectSetAR, optimizer: torch.optim.AdamW, arm: str, update: int, now: datetime) -> dict[str, object]:
    fixtures = tuple(_build_world(rng, config, purpose="training", roster_size=n, failed_zone=zone, row=update * 16 + n_index * 8 + (zone - 1) * 4 + row, now=now) for n_index, n in enumerate((3, 5)) for zone in ZONES for row in range(4))
    from experiments.candidates.variable_n_fleet_churn_b_explore import PairedPrimaryShadowBatch
    records: list[dict[str, object]] = []; terminals: list[Mapping[str, object]] = []; shadow_receipts = []; action_forwards = 0
    for n in (3, 5):
        group = tuple(fixture for fixture in fixtures if len(fixture.agents) == n + 1)
        if len(group) != 8:
            raise BExploreContractError("training native batch width differs")
        with PairedPrimaryShadowBatch(group) as batch:
            observations = tuple(row["next_observation"] for row in batch.initial); failed = tuple(row["failed_rank"] for row in batch.initial); episodes = [[] for _ in group]
            for epoch in range(6):
                inputs = [_model_inputs(observation, fixture, failed_rank) for observation, fixture, failed_rank in zip(observations, group, failed)]
                stacked = tuple(torch.cat([row[index] for row in inputs], 0) for index in range(6)); uniforms = []
                for fixture_index, fixture in enumerate(group):
                    uniforms.append([(rng.word(address(replicate_role="BPCR-REP-00", domain="training/action", purpose=f"{config.namespace}/{arm}", roster_size=n, failed_zone=fixture.failed_zone, update_or_panel_row=update, episode_row=fixture_index, physical_time=20 * epoch, draw=token), now=now) + .5) / float(1 << 64) for token in range(4)])
                output = model(*stacked, torch.tensor(uniforms, dtype=torch.float64)); action_forwards += 1
                _validate_model_output(output, context=f"training/{arm}/update{update}/action/epoch{epoch}")
                relative = output["command"].detach(); commands = []
                for index, (fixture, failed_rank) in enumerate(zip(group, failed)):
                    presented = tuple(rank for rank in fixture.post_presentations[epoch] if rank != failed_rank)
                    command = tuple(None if int(choice) == n else presented[int(choice)] for choice in relative[index]); commands.append(command if fixture.failed_zone == 1 else (command[2], command[3], command[0], command[1]))
                    episodes[index].append({"inputs": tuple(value[index:index + 1] for value in stacked), "command": relative[index:index + 1], "old_logp": output["log_probability"][index].detach(), "old_value": output["value"][index].detach(), "variable": torch.tensor([int(value < 0) for value in stacked[4][index]], dtype=torch.float64)})
                paired = batch.step(commands); rows = paired["primary_rows"]; shadow_rows = paired["shadow_rows"]
                observations = tuple(row["next_observation"] for row in rows)
            terminals.extend(rows); records.extend(record for episode in episodes for record in episode)
            shadow_receipts.append(build_shadow_receipt(f"{config.namespace}/TRAIN/{arm}/u{update}/N{n}", batch.receipt, shadow_rows))
    validated_endpoint_rows = _validate_host_endpoint_rows(terminals, context=f"training/{arm}/update{update}")
    objectives = torch.tensor([.5 * (row["fail_endpoint"][0] / row["fail_endpoint"][1]) + .5 * (row["total_endpoint"][0] / row["total_endpoint"][1]) for row in terminals], dtype=torch.float64)  # type: ignore[index,operator]
    old_values = torch.stack([row["old_value"] for row in records]).reshape(16, 6)  # type: ignore[list-item]
    advantages, returns = gae_terminal(old_values, objectives); advantages = normalize_advantages(advantages).reshape(96); returns = returns.reshape(96); old_logp = torch.stack([row["old_logp"] for row in records])  # type: ignore[list-item]
    if any(not bool(torch.isfinite(value).all()) for value in (objectives, old_values, advantages, returns, old_logp)):
        raise BExploreContractError("nonfinite objective/value/advantage/return training tensor")
    metrics = []; steps = 0; optimizer_forwards = 0; backwards = 0
    for epoch in range(4):
        permutation = _shuffle(tuple(range(96)), rng, {"replicate_role": "BPCR-REP-00", "domain": "training/minibatch-permutation", "purpose": f"{config.namespace}/{arm}", "roster_size": 3, "failed_zone": 1, "update_or_panel_row": update, "episode_row": epoch, "physical_time": 0}, now)
        for minibatch in frozen_minibatches(permutation):
            outputs = [model(*records[index]["inputs"], None, records[index]["command"]) for index in minibatch]  # type: ignore[arg-type]
            optimizer_forwards += len(outputs)
            for item_index, output in zip(minibatch, outputs):
                _validate_model_output(output, context=f"training/{arm}/update{update}/optimizer/record{item_index}")
            ix = torch.tensor(minibatch); variable = torch.stack([records[index]["variable"] for index in minibatch])  # type: ignore[list-item]
            loss = ppo_loss(torch.cat([row["log_probability"] for row in outputs]), old_logp[ix], advantages[ix], torch.cat([row["value"] for row in outputs]), returns[ix], torch.cat([row["token_entropies"] for row in outputs]), variable)
            if not all(torch.isfinite(value) for value in loss.values()):
                raise BExploreContractError("nonfinite PPO loss")
            optimizer.zero_grad(set_to_none=True); loss["total"].backward(); backwards += 1
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), .5); optimizer.step(); steps += 1
            if not torch.isfinite(grad_norm) or any(not bool(torch.isfinite(parameter).all()) for parameter in model.parameters()):
                raise BExploreContractError("nonfinite gradient/parameter update")
            metrics.append({"actor_loss": float(loss["actor"].detach()), "critic_loss": float(loss["value"].detach()), "entropy_loss": float(loss["entropy"].detach()), "total_loss": float(loss["total"].detach()), "preclip_gradient_norm": float(grad_norm), "policy_entropy": float(loss["entropy"].detach())})
    if steps != 16:
        raise BExploreContractError("optimizer steps per update differ")
    if action_forwards != 12 or optimizer_forwards != 384 or backwards != 16:
        raise BExploreContractError("per-update forward/backward exposure differs")
    return {"episodes": 16, "joint_transitions": 96, "optimizer_steps": steps, "training_action_forward_calls": action_forwards, "optimizer_forward_calls": optimizer_forwards, "backward_calls": backwards, "finite_values": validated_endpoint_rows == 16 and action_forwards + optimizer_forwards == 396, "training_J_ext": tuple(float(value) for value in objectives), "return_variance": float(torch.var(objectives, unbiased=False)), "advantage_variance": float(torch.var(advantages, unbiased=False)), "loss_rows": tuple(metrics), "shadow_receipts": tuple(shadow_receipts), "nonfinite_update_count": 0}


def _train_learners(config: BExploreRunConfig, rng: _SeedRNG, learners: Mapping[str, object], now: datetime) -> dict[str, object]:
    output = {}
    for arm in ARMS:
        rows = tuple(_train_one_update(config, rng, learners["models"][arm], learners["optimizers"][arm], arm, update, now) for update in range(config.updates))  # type: ignore[index,arg-type]
        output[arm] = {"updates": len(rows), "episodes": sum(int(row["episodes"]) for row in rows), "joint_transitions": sum(int(row["joint_transitions"]) for row in rows), "optimizer_steps": sum(int(row["optimizer_steps"]) for row in rows), "parameter_count": sum(parameter.numel() for parameter in learners["models"][arm].parameters()), "training_action_forward_calls": sum(int(row["training_action_forward_calls"]) for row in rows), "optimizer_forward_calls": sum(int(row["optimizer_forward_calls"]) for row in rows), "backward_calls": sum(int(row["backward_calls"]) for row in rows), "finite_values": all(bool(row["finite_values"]) for row in rows), "nonfinite_update_count": sum(int(row["nonfinite_update_count"]) for row in rows), "updates_telemetry": rows}  # type: ignore[index]
    counts = expected_counts(config)
    if any(output[arm]["episodes"] != counts["training_episodes_per_arm"] or output[arm]["joint_transitions"] != counts["joint_transitions_per_arm"] or output[arm]["optimizer_steps"] != counts["optimizer_steps_per_arm"] for arm in ARMS):
        raise BExploreContractError("exact per-arm training counts differ")
    return output


def _physical_command(relative: Sequence[object], fixture: EpisodeFixture, failed_rank: int, epoch: int) -> tuple[int | None, ...]:
    active = len(fixture.agents) - 1; presented = tuple(rank for rank in fixture.post_presentations[epoch] if rank != failed_rank)
    command = tuple(None if int(choice) == active else presented[int(choice)] for choice in relative)
    return command if fixture.failed_zone == 1 else (command[2], command[3], command[0], command[1])


def _validate_host_endpoint_rows(rows: Sequence[Mapping[str, object]], *, context: str) -> int:
    for row in rows:
        for field in ("fail_endpoint", "total_endpoint", "intact_endpoint"):
            value = row.get(field)
            if not isinstance(value, Sequence) or len(value) != 2 or not all(isinstance(item, int) and not isinstance(item, bool) for item in value) or value[1] <= 0:
                raise BExploreContractError(f"{context}: host endpoint value differs")
    return len(rows)


def _permuted_inputs(inputs: tuple[torch.Tensor, ...], permutation: Sequence[int]) -> tuple[torch.Tensor, ...]:
    agents, zones, globals_, legal, fixed, opaque = inputs; p = tuple(permutation); inverse = {old: new for new, old in enumerate(p)}; remapped = fixed.clone()
    for token in range(4):
        if int(fixed[0, token]) >= 0:
            remapped[0, token] = inverse[int(fixed[0, token])]
    return agents[:, p], zones, globals_, legal[:, p], remapped, opaque[:, p]


@dataclass(frozen=True)
class _HeldoutFreezeToken:
    namespace: str
    digest: str


def _freeze_before_n7(config: BExploreRunConfig, training: Mapping[str, object], checkpoints: Mapping[str, object], gate: Mapping[str, object]) -> _HeldoutFreezeToken:
    material = {"namespace": config.namespace, "training_counts": {arm: {key: training[arm][key] for key in ("updates", "episodes", "joint_transitions", "optimizer_steps")} for arm in ARMS}, "checkpoint_digests": {arm: {kind: checkpoints[arm][kind]["sha256"] for kind in CHECKPOINTS} for arm in ARMS}, "gate": dict(gate), "n7_opened": False}
    return _HeldoutFreezeToken(config.namespace, _canonical_digest(material))


def _fresh_relabel_permutation(rng: _SeedRNG, config: BExploreRunConfig, arm: str, checkpoint: str, fixture: EpisodeFixture, world_row: int, epoch: int, now: datetime) -> tuple[int, ...]:
    active = len(fixture.agents) - 1
    return _shuffle(tuple(range(active)), rng, {"replicate_role": "BPCR-REP-00", "domain": "conclusion/presentation", "purpose": f"{config.namespace}/{checkpoint}/{arm}/fresh-relabel", "roster_size": active, "failed_zone": fixture.failed_zone, "update_or_panel_row": world_row, "episode_row": world_row, "physical_time": 20 * epoch}, now)


def _evaluate_learned_batch(config: BExploreRunConfig, rng: _SeedRNG, token: _HeldoutFreezeToken, fixtures: Sequence[EpisodeFixture], model: MAPR4 | DirectSetAR, arm: str, checkpoint: str, cell: str, world_rows: Sequence[int], now: datetime) -> dict[str, object]:
    if token.namespace != config.namespace or len(fixtures) != 8 or len(world_rows) != 8:
        raise BExploreContractError("held-out freeze token/evaluation native batch differs")
    from experiments.candidates.variable_n_fleet_churn_b_explore import PairedPrimaryShadowBatch
    batch = PairedPrimaryShadowBatch(fixtures)
    mismatch = 0; sensitivity = tuple(batch.sensitivity()) if cell.startswith("N7") else (); rows: tuple[dict[str, object], ...] = (); residual_rows = []; policy_forwards = 0; diagnostic_forwards = 0
    zero = copy.deepcopy(model) if arm == "DIRECT" else None
    if zero is not None:
        with torch.no_grad():
            zero.p("residual.out.weight").zero_(); zero.p("residual.out.bias").zero_()
    try:
        observations = tuple(row["next_observation"] for row in batch.initial); failed = tuple(row["failed_rank"] for row in batch.initial)
        for epoch in range(6):
            inputs = [_model_inputs(observation, fixture, failed_rank) for observation, fixture, failed_rank in zip(observations, fixtures, failed)]
            stacked = tuple(torch.cat([row[index] for row in inputs], 0) for index in range(6))
            with torch.no_grad():
                output = model(*stacked); policy_forwards += 1
                _validate_model_output(output, context=f"evaluation/{cell}/{checkpoint}/{arm}/policy/epoch{epoch}")
                if zero is not None:
                    ablated = zero(*stacked, forced_commands=output["command"], _evaluation_support_valid_forcing=True); zero_free = zero(*stacked)
                    diagnostic_forwards += 2
                    _validate_model_output(ablated, context=f"evaluation/{cell}/{checkpoint}/{arm}/ablation/epoch{epoch}")
                    _validate_model_output(zero_free, context=f"evaluation/{cell}/{checkpoint}/{arm}/zero-free/epoch{epoch}")
                    tv = .5 * torch.abs(output["token_probabilities"] - ablated["token_probabilities"]).sum(2).max(1).values
                    residual_rows.extend({"boundary": epoch, "world_row": world_rows[index], "total_variation": float(tv[index]), "physical_command_change": not torch.equal(output["command"][index], zero_free["command"][index])} for index in range(8))
            commands = tuple(_physical_command(output["command"][index], fixture, int(failed[index]), epoch) for index, fixture in enumerate(fixtures))
            for index, fixture in enumerate(fixtures):
                permutation = _fresh_relabel_permutation(rng, config, arm, checkpoint, fixture, int(world_rows[index]), epoch, now)
                with torch.no_grad():
                    permuted_output = model(*_permuted_inputs(inputs[index], permutation)); diagnostic_forwards += 1
                    _validate_model_output(permuted_output, context=f"evaluation/{cell}/{checkpoint}/{arm}/relabel/world{index}/epoch{epoch}")
                    permuted = permuted_output["command"][0]
                mapped = tuple(len(permutation) if int(choice) == len(permutation) else permutation[int(choice)] for choice in permuted)
                mismatch += int(tuple(int(choice) for choice in output["command"][index]) != mapped)
            paired = batch.step(commands); rows = paired["primary_rows"]; shadow_rows = paired["shadow_rows"]
            observations = tuple(row["next_observation"] for row in rows)
        receipt = build_shadow_receipt(f"{config.namespace}/{cell}/{checkpoint}/{arm}", batch.receipt, shadow_rows)
        validated_endpoint_rows = _validate_host_endpoint_rows(rows, context=f"evaluation/{cell}/{checkpoint}/{arm}")
        expected_diagnostic = 60 if arm == "DIRECT" else 48
        if policy_forwards != 6 or diagnostic_forwards != expected_diagnostic:
            raise BExploreContractError("evaluation policy/diagnostic forward exposure differs")
        return {"arm": arm, "checkpoint": checkpoint, "cell": cell, "rollouts": 8, "relabel_mismatch_count": mismatch, "hard_valid": all(row["terminal"] and not row["safety_violation"] and not row["exclusivity_violation"] for row in rows), "finite_values": validated_endpoint_rows == 8 and policy_forwards == 6 and diagnostic_forwards == expected_diagnostic, "evaluation_policy_forward_calls": policy_forwards, "diagnostic_forward_calls": diagnostic_forwards, "action_sensitivity": sensitivity, "action_sensitivity_status": "OBSERVED_TREATMENT_BLIND_N7" if cell.startswith("N7") else "NOT_APPLICABLE_TRAIN_SUPPORT_CELL", "direct_residual_activity": tuple(residual_rows), "endpoints": tuple({key: row[key] for key in ("fail_endpoint", "total_endpoint", "intact_endpoint")} for row in rows), "shadow_receipts": (receipt,)}
    finally:
        batch.close()


def _evaluate_bcrh_batch(config: BExploreRunConfig, token: _HeldoutFreezeToken, fixtures: Sequence[EpisodeFixture], cell: str, world_rows: Sequence[int]) -> dict[str, object]:
    if token.namespace != config.namespace or len(fixtures) != 8 or len(world_rows) != 8:
        raise BExploreContractError("BCRH held-out freeze token/native batch differs")
    from experiments.candidates.variable_n_fleet_churn_b_explore import PairedPrimaryShadowBatch
    batch = PairedPrimaryShadowBatch(fixtures)
    checker_rows = []; rows: tuple[dict[str, object], ...] = ()
    try:
        observations = tuple(row["next_observation"] for row in batch.initial)
        for epoch in range(6):
            decisions = batch.bcrh(include_candidate_records=False)
            if any("candidate_records" in decision for decision in decisions):
                raise BExploreContractError("BCRH no-record evaluation serialized candidate records")
            commands = tuple(decision["scorer_command"] for decision in decisions); paired = batch.step(commands); rows = paired["primary_rows"]; shadow_rows = paired["shadow_rows"]
            checker_rows.extend(decisions)
            observations = tuple(row["next_observation"] for row in rows)
        receipt = build_shadow_receipt(f"{config.namespace}/{cell}/BCRH", batch.receipt, shadow_rows)
        validated_endpoint_rows = _validate_host_endpoint_rows(rows, context=f"evaluation/{cell}/BCRH")
        identified = all(row["scorer_checker_equal"] and row["independent_enumerator_equal"] and 0 < row["candidate_count"] <= 1961 for row in checker_rows)
        return {"arm": "BCRH", "cell": cell, "rollouts": 8, "comparison_status": "IDENTIFIED" if identified else "NONIDENTIFIED", "hard_valid": all(row["terminal"] and not row["safety_violation"] and not row["exclusivity_violation"] for row in rows), "finite_values": validated_endpoint_rows == 8, "evaluation_policy_forward_calls": 0, "diagnostic_forward_calls": 0, "checker_rows": tuple(checker_rows), "endpoints": tuple({key: row[key] for key in ("fail_endpoint", "total_endpoint", "intact_endpoint")} for row in rows), "shadow_receipts": (receipt,)}
    finally:
        batch.close()


def ps_b0_state_descriptors() -> tuple[dict[str, object], ...]:
    rows = tuple(
        {"roster_size": n, "failed_zone": zone, "state_kind": kind}
        for n in ROSTERS for zone in ZONES for kind in STATE_KINDS
    )
    if len(rows) != 18:
        raise AssertionError("PS-B0 descriptor cardinality differs")
    return rows


def ps_b0_expected_addresses() -> frozenset[tuple[object, ...]]:
    return frozenset(
        (row["roster_size"], row["failed_zone"], row["state_kind"], presentation, checkpoint, arm)
        for row in ps_b0_state_descriptors() for presentation in PRESENTATIONS
        for checkpoint in CHECKPOINTS for arm in ARMS
    )


@dataclass(frozen=True)
class PSB0Comparison:
    roster_size: int
    failed_zone: int
    state_kind: str
    presentation: str
    checkpoint: str
    arm: str
    agent_rows_copermuted: bool
    legal_masks_copermuted: bool
    fixed_occupants_copermuted: bool
    opaque_ranks_copermuted: bool
    physical_support_equal: bool
    canonical_physical_command: tuple[int | None, ...]
    inverse_mapped_physical_command: tuple[int | None, ...]
    null_case_present: bool
    fixed_or_acquiring_case_present: bool
    null_action_legal: bool
    legal_agent_candidate_count: int
    opaque_deterministic_tie_ranks_complete: bool

    @property
    def address(self) -> tuple[object, ...]:
        return self.roster_size, self.failed_zone, self.state_kind, self.presentation, self.checkpoint, self.arm


def validate_ps_b0(rows: Sequence[PSB0Comparison]) -> dict[str, object]:
    materialized = tuple(rows)
    if len(materialized) != 288 or {row.address for row in materialized} != ps_b0_expected_addresses():
        raise BExploreContractError("PS-B0 must contain the exact 288 comparison addresses")
    mismatch = {arm: 0 for arm in ARMS}
    for row in materialized:
        structural = (
            row.agent_rows_copermuted and row.legal_masks_copermuted
            and row.fixed_occupants_copermuted and row.opaque_ranks_copermuted
            and row.physical_support_equal
            and row.canonical_physical_command == row.inverse_mapped_physical_command
        )
        if not structural:
            mismatch[row.arm] += 1
    for n in ROSTERS:
        for zone in ZONES:
            cell = tuple(row for row in materialized if row.roster_size == n and row.failed_zone == zone)
            if not any(
                row.state_kind == "diagnostic_null_tie" and row.null_case_present
                and row.null_action_legal and row.legal_agent_candidate_count >= 2
                and row.opaque_deterministic_tie_ranks_complete for row in cell
            ):
                raise BExploreContractError("PS-B0 cell lacks diagnostic support-path coverage")
            if not any(row.state_kind == "later_fixed_or_acquiring" and row.fixed_or_acquiring_case_present for row in cell):
                raise BExploreContractError("PS-B0 cell lacks fixed/acquiring coverage")
    if mismatch != {"MAPR": 0, "DIRECT": 0}:
        raise BExploreContractError("PS-B0 inverse physical-command mismatch")
    return {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_V1", "descriptors": 18, "presentations": 4, "comparisons": 288, "mismatch_by_arm": mismatch, "passed": True}


@dataclass(frozen=True)
class BCRHPrecheckRow:
    failed_zone: int
    obstruction_present: bool
    relay_present: bool
    high_demand: bool
    legal_command: bool
    scorer_checker_equal: bool
    independent_enumerator_equal: bool
    hard_valid: bool
    candidate_count: int
    include_candidate_records: bool = False
    common_host_defect: bool = False

    @property
    def address(self) -> tuple[int, bool, bool]:
        return self.failed_zone, self.obstruction_present, self.relay_present


def validate_bcrh_precheck(rows: Sequence[BCRHPrecheckRow]) -> dict[str, object]:
    materialized = tuple(rows)
    expected = {(zone, obstruction, relay) for zone in ZONES for obstruction in (False, True) for relay in (False, True)}
    if len(materialized) != 8 or {row.address for row in materialized} != expected:
        raise BExploreContractError("BCRH precheck must contain the exact eight corners")
    if any(not row.high_demand or row.include_candidate_records for row in materialized):
        raise BExploreContractError("BCRH precheck must use high demand and no candidate records")
    if any(row.common_host_defect for row in materialized):
        return {"comparison_status": "REPAIR_REQUIRED", "common_host_valid": False, "bcrh_identified": False}
    identified = all(
        row.legal_command and row.scorer_checker_equal and row.independent_enumerator_equal
        and row.hard_valid and 0 < row.candidate_count <= 1961 for row in materialized
    )
    return {"comparison_status": "IDENTIFIED" if identified else "NONIDENTIFIED", "common_host_valid": True, "bcrh_identified": identified}


def clone_checkpoint(model: torch.nn.Module, label: str) -> dict[str, object]:
    if label not in CHECKPOINTS:
        raise BExploreContractError("checkpoint label differs")
    state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
    digest = hashlib.sha256()
    for name in sorted(state):
        value = state[name]
        name_bytes = name.encode("utf-8")
        dtype_bytes = str(value.dtype).encode("ascii")
        shape_bytes = np.asarray(value.shape, dtype=np.int64).tobytes()
        raw = value.contiguous().numpy().tobytes()
        for payload in (name_bytes, dtype_bytes, shape_bytes, raw):
            digest.update(len(payload).to_bytes(8, "big"))
            digest.update(payload)
    return {"label": label, "state": state, "sha256": digest.hexdigest(), "storage_disjoint": True}


def validate_checkpoint_pair(initial: Mapping[str, object], final: Mapping[str, object]) -> None:
    if initial.get("label") != "initial" or final.get("label") != "final" or initial is final:
        raise BExploreContractError("initial/final checkpoint identity differs")
    for checkpoint in (initial, final):
        state = checkpoint.get("state")
        if not isinstance(state, Mapping) or not state or not checkpoint.get("storage_disjoint"):
            raise BExploreContractError("checkpoint state was not independently retained")
    initial_state, final_state = initial["state"], final["state"]
    if set(initial_state) != set(final_state):  # type: ignore[arg-type]
        raise BExploreContractError("initial/final checkpoint parameter inventory differs")
    if any(initial_state[name].data_ptr() == final_state[name].data_ptr() for name in initial_state):  # type: ignore[index,union-attr]
        raise BExploreContractError("initial/final checkpoint tensor storage aliases")


def validate_preflight_receipt(receipt: Mapping[str, object], *, now: datetime) -> dict[str, object]:
    required = {"schema_version", "captured_at", "assessed_at", "minimum_available_bytes", "available_physical_bytes", "effective_available_bytes", "physical_floor_pass", "effective_floor_pass", "passed"}
    if not required <= set(receipt) or receipt.get("schema_version") != 1:
        raise BExploreContractError("4 GiB preflight receipt fields/schema are incomplete")
    if now.tzinfo is None:
        raise BExploreContractError("readiness time must be timezone-aware")
    try:
        captured = datetime.fromisoformat(str(receipt["captured_at"]).replace("Z", "+00:00"))
        assessed = datetime.fromisoformat(str(receipt["assessed_at"]).replace("Z", "+00:00"))
    except ValueError as error:
        raise BExploreContractError("preflight timestamps are invalid") from error
    age = (now.astimezone(timezone.utc) - captured.astimezone(timezone.utc)).total_seconds()
    if age < -5 or age > PREFLIGHT_FRESH_SECONDS or assessed < captured:
        raise BExploreContractError("4 GiB preflight receipt is not fresh")
    physical = int(receipt["available_physical_bytes"]); effective = int(receipt["effective_available_bytes"])
    if receipt.get("minimum_available_bytes") != MINIMUM_AVAILABLE_BYTES or physical < MINIMUM_AVAILABLE_BYTES or effective < MINIMUM_AVAILABLE_BYTES:
        raise BExploreContractError("physical/effective available memory is below 4 GiB")
    if receipt.get("physical_floor_pass") is not True or receipt.get("effective_floor_pass") is not True or receipt.get("passed") is not True:
        raise BExploreContractError("4 GiB preflight did not pass")
    return {"available_physical_bytes": physical, "effective_available_bytes": effective, "age_seconds": age}


def _implementation_hard_fence(preflight_receipt: Mapping[str, object], *, now: datetime) -> dict[str, object]:
    """Validate resource admission first, then reject every executable/publication entry."""
    memory = validate_preflight_receipt(preflight_receipt, now=now)
    if not IMPLEMENTATION_READY:
        raise BExploreContractError(f"REPAIR_REQUIRED: {IMPLEMENTATION_BLOCKER}")
    return memory


def validate_telemetry_sink(sink: object) -> None:
    if getattr(sink, "schema", None) != TELEMETRY_SCHEMA or not callable(getattr(sink, "emit", None)):
        raise BExploreContractError("external telemetry sink/schema is absent")
    if not REQUIRED_TELEMETRY_FIELDS <= set(getattr(sink, "fields", ())):
        raise BExploreContractError("external telemetry sink lacks required performance fields")


def validate_telemetry_payload(payload: Mapping[str, object]) -> None:
    if not REQUIRED_TELEMETRY_FIELDS <= set(payload):
        raise BExploreContractError("scientific result telemetry is incomplete")
    if any(payload[field] is None for field in REQUIRED_TELEMETRY_FIELDS):
        raise BExploreContractError("scientific result telemetry contains unmeasured fields")
    if payload.get("telemetry_schema") != TELEMETRY_SCHEMA or payload.get("telemetry_terminal") is not True:
        raise BExploreContractError("external telemetry terminal/schema differs")
    positive = ("end_to_end_wall_seconds", "end_to_end_cpu_seconds", "process_tree_peak_rss_bytes", "available_physical_bytes", "effective_available_bytes", "native_integrated_ticks", "scientific_work_transitions_per_second", "worker_count", "threads_per_worker")
    if any(not isinstance(payload[field], (int, float)) or isinstance(payload[field], bool) or payload[field] <= 0 for field in positive):
        raise BExploreContractError("external telemetry contains nonpositive measured fields")
    stages = {"source_binding", "training", "evaluation", "serialization"}
    for field in ("stage_wall_seconds", "stage_cpu_seconds"):
        values = payload[field]
        if not isinstance(values, Mapping) or set(values) != stages or any(not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0 for value in values.values()):
            raise BExploreContractError("external stage wall/CPU telemetry differs")
    for field in ("parameter_count_by_arm", "forward_calls_by_arm", "backward_calls_by_arm", "flop_exposure_by_arm"):
        values = payload[field]
        if not isinstance(values, Mapping) or set(values) != set(ARMS) or any(not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0 for value in values.values()):
            raise BExploreContractError("external per-arm exposure telemetry differs")
    for field in ("scratch_peak_bytes", "durable_peak_bytes", "io_read_bytes", "io_write_bytes"):
        if not isinstance(payload[field], int) or isinstance(payload[field], bool) or payload[field] < 0:
            raise BExploreContractError("external storage/I/O telemetry differs")
    primary_calls = payload["primary_host_calls"]; shadow_calls = payload["shadow_host_calls"]
    if not isinstance(primary_calls, int) or isinstance(primary_calls, bool) or primary_calls <= 0 or shadow_calls != primary_calls or payload["total_host_call_multiplier"] != 2.0:
        raise BExploreContractError("shadow host-call overhead telemetry differs")
    if payload["available_physical_bytes"] < MINIMUM_AVAILABLE_BYTES or payload["effective_available_bytes"] < MINIMUM_AVAILABLE_BYTES:
        raise BExploreContractError("telemetry memory headroom is below 4 GiB")


def _validate_telemetry_runtime_binding(payload: Mapping[str, object], terminal: Mapping[str, object]) -> None:
    training = terminal.get("training"); exposure = terminal.get("exposure")
    if not isinstance(training, Mapping) or not isinstance(exposure, Mapping):
        raise BExploreContractError("telemetry binding lacks runtime training/exposure")
    expected_parameters = {arm: training[arm]["parameter_count"] for arm in ARMS}  # type: ignore[index]
    expected_backwards = {arm: exposure["training"][arm]["backward_calls"] for arm in ARMS}  # type: ignore[index]
    expected_forwards = {
        arm: exposure["training"][arm]["action_selection_forward_calls"] + exposure["training"][arm]["optimizer_forward_calls"] + exposure["evaluation"][arm]["policy_forward_calls"] + exposure["evaluation"][arm]["diagnostic_forward_calls"]  # type: ignore[index,operator]
        for arm in ARMS
    }
    if payload.get("parameter_count_by_arm") != expected_parameters or payload.get("backward_calls_by_arm") != expected_backwards or payload.get("forward_calls_by_arm") != expected_forwards:
        raise BExploreContractError("external telemetry/runtime parameter or forward/backward exposure binding differs")


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _validate_runtime_payload_cross_consistency(config: BExploreRunConfig, terminal: Mapping[str, object]) -> None:
    counts = expected_counts(config)
    training = terminal.get("training")
    if not isinstance(training, Mapping) or set(training) != set(ARMS):
        raise BExploreContractError("training arm payload inventory differs")
    training_receipts = []
    for arm in ARMS:
        summary = training[arm]
        required = {"updates", "episodes", "joint_transitions", "optimizer_steps", "parameter_count", "training_action_forward_calls", "optimizer_forward_calls", "backward_calls", "finite_values", "nonfinite_update_count", "updates_telemetry"}
        if not isinstance(summary, Mapping) or set(summary) != required:
            raise BExploreContractError("training summary schema differs")
        expected_summary = {"updates": config.updates, "episodes": counts["training_episodes_per_arm"], "joint_transitions": counts["joint_transitions_per_arm"], "optimizer_steps": counts["optimizer_steps_per_arm"], "training_action_forward_calls": 12 * config.updates, "optimizer_forward_calls": 384 * config.updates, "backward_calls": 16 * config.updates, "nonfinite_update_count": 0}
        if any(summary.get(key) != value for key, value in expected_summary.items()) or summary.get("finite_values") is not True or not isinstance(summary.get("parameter_count"), int) or summary["parameter_count"] <= 0:
            raise BExploreContractError("training summary counts/finiteness differ")
        updates = summary.get("updates_telemetry")
        if not isinstance(updates, Sequence) or len(updates) != config.updates:
            raise BExploreContractError("training update telemetry inventory differs")
        for update in updates:
            required_update = {"episodes", "joint_transitions", "optimizer_steps", "training_action_forward_calls", "optimizer_forward_calls", "backward_calls", "finite_values", "training_J_ext", "return_variance", "advantage_variance", "loss_rows", "shadow_receipts", "nonfinite_update_count"}
            if not isinstance(update, Mapping) or set(update) != required_update or any(update.get(key) != value for key, value in {"episodes": 16, "joint_transitions": 96, "optimizer_steps": 16, "training_action_forward_calls": 12, "optimizer_forward_calls": 384, "backward_calls": 16, "finite_values": True, "nonfinite_update_count": 0}.items()):
                raise BExploreContractError("training update exact counts/finiteness differ")
            if not isinstance(update.get("training_J_ext"), Sequence) or len(update["training_J_ext"]) != 16 or any(not _finite_number(value) for value in update["training_J_ext"]):
                raise BExploreContractError("training per-episode return inventory differs")
            if not _finite_number(update.get("return_variance")) or not _finite_number(update.get("advantage_variance")):
                raise BExploreContractError("training return/advantage variance differs")
            losses = update.get("loss_rows")
            loss_keys = {"actor_loss", "critic_loss", "entropy_loss", "total_loss", "preclip_gradient_norm", "policy_entropy"}
            if not isinstance(losses, Sequence) or len(losses) != 16 or any(not isinstance(row, Mapping) or set(row) != loss_keys or any(not _finite_number(value) for value in row.values()) for row in losses):
                raise BExploreContractError("training optimizer telemetry differs")
            receipts = update.get("shadow_receipts")
            if not isinstance(receipts, Sequence) or len(receipts) != 2:
                raise BExploreContractError("training paired receipt inventory differs")
            training_receipts.extend(receipts)
    evaluation = terminal.get("evaluation")
    if not isinstance(evaluation, Mapping) or set(evaluation) != {"learned", "bcrh", "rollouts", "relabel_mismatch_count"} or evaluation.get("rollouts") != counts["evaluation_rollouts_total"] or evaluation.get("relabel_mismatch_count") != {"MAPR": 0, "DIRECT": 0}:
        raise BExploreContractError("evaluation summary schema/counts differ")
    learned = evaluation.get("learned"); bcrh = evaluation.get("bcrh")
    expected_checkpoints = ("final",) if config.stage == DEBUG_STAGE else CHECKPOINTS
    expected_learned = {(f"N{n}z{zone}", checkpoint, arm) for n in ROSTERS for zone in ZONES for checkpoint in expected_checkpoints for arm in ARMS}
    learned_receipts = []
    if not isinstance(learned, Sequence) or len(learned) != len(expected_learned):
        raise BExploreContractError("learned evaluation group inventory differs")
    addresses = set()
    for row in learned:
        required_row = {"arm", "checkpoint", "cell", "rollouts", "relabel_mismatch_count", "hard_valid", "finite_values", "evaluation_policy_forward_calls", "diagnostic_forward_calls", "action_sensitivity", "action_sensitivity_status", "direct_residual_activity", "endpoints", "shadow_receipts"}
        if not isinstance(row, Mapping) or set(row) != required_row:
            raise BExploreContractError("learned evaluation row schema differs")
        address_ = (row["cell"], row["checkpoint"], row["arm"]); addresses.add(address_)
        direct = row["arm"] == "DIRECT"; n7 = str(row["cell"]).startswith("N7")
        if row.get("rollouts") != 8 or row.get("relabel_mismatch_count") != 0 or row.get("hard_valid") is not True or row.get("finite_values") is not True or row.get("evaluation_policy_forward_calls") != 6 or row.get("diagnostic_forward_calls") != (60 if direct else 48):
            raise BExploreContractError("learned evaluation validity/exposure differs")
        if len(row.get("action_sensitivity", ())) != (8 if n7 else 0) or row.get("action_sensitivity_status") != ("OBSERVED_TREATMENT_BLIND_N7" if n7 else "NOT_APPLICABLE_TRAIN_SUPPORT_CELL"):
            raise BExploreContractError("learned action sensitivity inventory differs")
        if len(row.get("direct_residual_activity", ())) != (48 if direct else 0) or len(row.get("endpoints", ())) != 8 or len(row.get("shadow_receipts", ())) != 1:
            raise BExploreContractError("learned diagnostic/endpoint/receipt inventory differs")
        _validate_host_endpoint_rows(row["endpoints"], context="terminal learned evaluation")  # type: ignore[arg-type]
        learned_receipts.extend(row["shadow_receipts"])
    if addresses != expected_learned:
        raise BExploreContractError("learned evaluation address set differs")
    bcrh_receipts = []
    if not isinstance(bcrh, Sequence) or len(bcrh) != 2:
        raise BExploreContractError("BCRH evaluation group inventory differs")
    for row in bcrh:
        required_row = {"arm", "cell", "rollouts", "comparison_status", "hard_valid", "finite_values", "evaluation_policy_forward_calls", "diagnostic_forward_calls", "checker_rows", "endpoints", "shadow_receipts"}
        if not isinstance(row, Mapping) or set(row) != required_row or row.get("arm") != "BCRH" or row.get("cell") not in ("N7z1", "N7z2") or row.get("rollouts") != 8 or row.get("hard_valid") is not True or row.get("finite_values") is not True or row.get("evaluation_policy_forward_calls") != 0 or row.get("diagnostic_forward_calls") != 0:
            raise BExploreContractError("BCRH evaluation validity/exposure differs")
        if row.get("comparison_status") not in ("IDENTIFIED", "NONIDENTIFIED") or len(row.get("checker_rows", ())) != 48 or len(row.get("endpoints", ())) != 8 or len(row.get("shadow_receipts", ())) != 1:
            raise BExploreContractError("BCRH checker/endpoint/receipt inventory differs")
        _validate_host_endpoint_rows(row["endpoints"], context="terminal BCRH evaluation")  # type: ignore[arg-type]
        bcrh_receipts.extend(row["shadow_receipts"])
    exact_readout = _exploratory_readout(config, evaluation)
    if _canonical_digest(terminal.get("exploratory_readout")) != _canonical_digest(exact_readout):
        raise BExploreContractError("explicit readout does not derive exactly from evaluation rows")
    if _canonical_digest(tuple(terminal.get("shadow_receipts", ()))) != _canonical_digest(tuple(training_receipts + learned_receipts + bcrh_receipts)):
        raise BExploreContractError("terminal paired receipt inventory is not the exact execution inventory")


def validate_runtime_terminal(config: BExploreRunConfig, terminal: Mapping[str, object]) -> None:
    required = {
        "schema", "namespace", "counts", "ps_b0_passed", "learned_relabel_mismatch_count",
        "common_host_hard_valid", "finite_values", "initial_final_checkpoints_retained",
        "n7_controls_frozen_before_open", "source_pre_digest", "source_post_digest",
        "shadow_boundary_exact", "shadow_source_stable", "shadow_influenced_actions",
        "observations_complete", "training_observation_rows", "individual_world_seed_rows",
        "optimization_rows", "bcrh_comparison_status", "shadow_receipts", "training",
        "evaluation", "exploratory_readout", "exposure", "ps_b0_result", "bcrh_precheck_result",
        "checkpoint_artifact",
    }
    if set(terminal) != required or terminal.get("schema") != "VNFC_BPCR_BEXP_R01_RUNTIME_TERMINAL_V1" or terminal.get("namespace") != config.namespace:
        raise BExploreContractError("exact runtime terminal schema/namespace differs")
    counts = expected_counts(config)
    if terminal.get("counts") != counts:
        raise BExploreContractError("exact runtime terminal counts differ")
    truth = ("ps_b0_passed", "common_host_hard_valid", "finite_values", "initial_final_checkpoints_retained", "n7_controls_frozen_before_open", "shadow_boundary_exact", "shadow_source_stable", "observations_complete")
    if any(terminal.get(field) is not True for field in truth):
        raise BExploreContractError("runtime validity/freeze/shadow terminal is incomplete")
    if terminal.get("learned_relabel_mismatch_count") != {"MAPR": 0, "DIRECT": 0}:
        raise BExploreContractError("learned-arm relabel terminal differs")
    if terminal.get("shadow_influenced_actions") is not False or terminal.get("source_pre_digest") != terminal.get("source_post_digest"):
        raise BExploreContractError("source/shadow action fence differs")
    if terminal.get("training_observation_rows") != counts["training_episodes_total"] or terminal.get("individual_world_seed_rows") != counts["evaluation_rollouts_total"] or terminal.get("optimization_rows") != counts["optimizer_steps_total"]:
        raise BExploreContractError("individual observation/exposure retention counts differ")
    if terminal.get("bcrh_comparison_status") not in ("IDENTIFIED", "NONIDENTIFIED"):
        raise BExploreContractError("BCRH comparator terminal differs")
    _validate_runtime_payload_cross_consistency(config, terminal)
    shadow_receipts = terminal.get("shadow_receipts")
    expected_shadow = 4 * config.updates + counts["learned_evaluation_rollouts"] // 8 + counts["bcrh_evaluation_rollouts"] // 8
    if not isinstance(shadow_receipts, Sequence) or len(shadow_receipts) != expected_shadow:
        raise BExploreContractError("actual B shadow receipt inventory differs")
    batch_ids = []
    for receipt in shadow_receipts:
        if not isinstance(receipt, Mapping):
            raise BExploreContractError("actual B shadow receipt row differs")
        validate_shadow_receipt(receipt); batch_ids.append(receipt["batch_id"])
    if len(set(batch_ids)) != len(batch_ids):
        raise BExploreContractError("actual B shadow batch identity repeats")
    readout = terminal.get("exploratory_readout")
    if not isinstance(readout, Mapping) or set(readout) != {"individual_world_seed", "paired_contrasts", "recovery_latency"}:
        raise BExploreContractError("explicit exploratory readout schema differs")
    expected_contrasts = 0 if config.stage == DEBUG_STAGE else 128
    if len(readout["individual_world_seed"]) != counts["evaluation_rollouts_total"] or len(readout["recovery_latency"]) != counts["evaluation_rollouts_total"] or len(readout["paired_contrasts"]) != expected_contrasts:  # type: ignore[arg-type]
        raise BExploreContractError("explicit individual/contrast/recovery readout inventory differs")
    evaluation = terminal.get("evaluation")
    if isinstance(evaluation, Mapping) and "learned" in evaluation:
        n7 = tuple(row for row in evaluation["learned"] if str(row.get("cell", "")).startswith("N7"))  # type: ignore[union-attr]
        if any(row.get("action_sensitivity_status") != "OBSERVED_TREATMENT_BLIND_N7" or len(row.get("action_sensitivity", ())) != 8 for row in n7):
            raise BExploreContractError("treatment-blind N7 action sensitivity is incomplete")
    exposure = terminal.get("exposure")
    learned_groups_per_arm = 6 if config.stage == DEBUG_STAGE else 12
    expected_exposure = {
        "training": {arm: {"action_selection_forward_calls": 12 * config.updates, "optimizer_forward_calls": 384 * config.updates, "backward_calls": 16 * config.updates} for arm in ARMS},
        "evaluation": {"MAPR": {"policy_forward_calls": 6 * learned_groups_per_arm, "diagnostic_forward_calls": 48 * learned_groups_per_arm}, "DIRECT": {"policy_forward_calls": 6 * learned_groups_per_arm, "diagnostic_forward_calls": 60 * learned_groups_per_arm}, "BCRH": {"policy_forward_calls": 0, "diagnostic_forward_calls": 0}},
    }
    if exposure != expected_exposure:
        raise BExploreContractError("exact training/evaluation exposure terminal differs")
    artifact = terminal.get("checkpoint_artifact")
    if not isinstance(artifact, Mapping) or artifact.get("namespace") != config.namespace or artifact.get("schema") != "VNFC_BPCR_BEXP_R01_CHECKPOINT_MANIFEST_V1":
        raise BExploreContractError("durable checkpoint artifact terminal is absent")


def _canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _stable_shadow_identity(identity: Mapping[str, object]) -> dict[str, object]:
    required = {"build_key", "artifact_sha256", "artifact_size", "source_identity", "registered_r09_artifact_sha256", "registered_r09_build_key"}
    if not required <= set(identity):
        raise BExploreContractError("B shadow artifact identity fields are incomplete")
    return {key: identity[key] for key in sorted(required)}


def build_shadow_receipt(batch_id: str, paired_receipt: Mapping[str, object], final_shadow_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Bind the CLEAN paired-seam receipt to eight retained recovery rows."""
    rows = tuple(final_shadow_rows)
    if len(rows) != 8 or any(set(row) != {"interactive", "tick_rows", "receipt"} for row in rows):
        raise BExploreContractError("CLEAN paired final shadow rows differ")
    receipt = {"schema": SHADOW_SCHEMA, "batch_id": batch_id, "paired_receipt": dict(paired_receipt), "episode_recovery": tuple(dict(row["receipt"]) for row in rows), "shadow_influenced_actions": False, "total_host_call_multiplier": 2.0}
    validate_shadow_receipt(receipt)
    return receipt


def validate_shadow_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    if set(receipt) != {"schema", "batch_id", "paired_receipt", "episode_recovery", "shadow_influenced_actions", "total_host_call_multiplier"} or receipt.get("schema") != SHADOW_SCHEMA:
        raise BExploreContractError("paired shadow wrapper receipt schema differs")
    if not isinstance(receipt.get("batch_id"), str) or not receipt["batch_id"] or receipt.get("shadow_influenced_actions") is not False or receipt.get("total_host_call_multiplier") != 2.0:
        raise BExploreContractError("paired shadow batch identity/authority differs")
    paired = receipt.get("paired_receipt")
    paired_keys = {"schema", "input_digest", "action_digest", "width", "main_return_source", "shadow_role", "initial", "source_pre", "source_post", "boundaries"}
    if not isinstance(paired, Mapping) or set(paired) != paired_keys or paired.get("schema") != "VNFC-BEXP-PAIRED-PRIMARY-SHADOW-RECEIPT-v1" or paired.get("width") != 8:
        raise BExploreContractError("CLEAN paired primary/shadow receipt fields differ")
    if paired.get("main_return_source") != "registered_r09_native_interactive_primary" or paired.get("shadow_role") != "telemetry_only_no_action_or_return_authority" or paired.get("source_pre") != paired.get("source_post"):
        raise BExploreContractError("paired primary-return/shadow-source authority differs")
    if any(not _is_sha256(paired.get(field)) for field in ("input_digest", "action_digest")):
        raise BExploreContractError("paired input/action digest differs")
    initial = paired.get("initial")
    if not isinstance(initial, Mapping) or set(initial) != {"primary_full_output_digest", "shadow_full_output_digest", "exact"} or initial.get("exact") is not True or initial.get("primary_full_output_digest") != initial.get("shadow_full_output_digest"):
        raise BExploreContractError("paired reset boundary differs")
    if any(not _is_sha256(initial.get(field)) for field in ("primary_full_output_digest", "shadow_full_output_digest")):
        raise BExploreContractError("paired reset digest differs")
    boundaries = paired.get("boundaries")
    boundary_keys = {"boundary_index", "command_digest", "cumulative_action_digest", "primary_full_output_digest", "shadow_full_output_digest", "exact", "primary_integrated_ticks", "shadow_integrated_ticks", "shadow_ticks_per_session", "shadow_tick_rows_digest", "source_exact_pre_post"}
    if not isinstance(boundaries, Sequence) or len(boundaries) != 6:
        raise BExploreContractError("paired boundary inventory differs")
    for index, row in enumerate(boundaries):
        if not isinstance(row, Mapping) or set(row) != boundary_keys or row.get("boundary_index") != index:
            raise BExploreContractError("paired boundary receipt row differs")
        if row.get("exact") is not True or row.get("source_exact_pre_post") is not True or row.get("primary_full_output_digest") != row.get("shadow_full_output_digest") or row.get("primary_integrated_ticks") != row.get("shadow_integrated_ticks") or tuple(row.get("shadow_ticks_per_session", ())) != (20,) * 8:
            raise BExploreContractError("paired boundary/source/tick equivalence differs")
        if any(not _is_sha256(row.get(field)) for field in ("command_digest", "cumulative_action_digest", "primary_full_output_digest", "shadow_full_output_digest", "shadow_tick_rows_digest")):
            raise BExploreContractError("paired boundary digest differs")
        if len(tuple(row.get("primary_integrated_ticks", ()))) != 8 or any(int(value) <= 0 for value in row["primary_integrated_ticks"]):
            raise BExploreContractError("paired integrated tick rows differ")
    if paired.get("action_digest") != boundaries[-1]["cumulative_action_digest"]:
        raise BExploreContractError("paired cumulative action digest differs")
    recovery = receipt.get("episode_recovery")
    recovery_keys = {"observation_scope", "primary_rollout_applicability", "first_failed_zone_service_time_seconds", "failed_zone_executor_reacquisition_time_seconds", "failed_zone_zero_service_seconds_0_60", "observed_failed_zone_seconds_0_60", "complete_0_60", "raw_tick_rows"}
    if not isinstance(recovery, Sequence) or len(recovery) != 8 or any(not isinstance(row, Mapping) or set(row) != recovery_keys or row.get("observation_scope") != "fresh_b_shadow_direct" for row in recovery):
        raise BExploreContractError("paired recovery telemetry rows differ")
    return {"status": "EQUIVALENT_PAIRED_BATCH_OBSERVED", "main_return_source": paired["main_return_source"], "host_call_multiplier": 2.0}


def _exact_readiness_plan(config: BExploreRunConfig) -> dict[str, object]:
    config.validate(); counts = expected_counts(config)
    return {
        "schema": "VNFC_BPCR_BEXP_R01_READINESS_PLAN_V1", "run_revision": RUN_REVISION,
        "implementation_ready": IMPLEMENTATION_READY, "implementation_blocker": IMPLEMENTATION_BLOCKER,
        "namespace": config.namespace, "config": asdict(config),
        "seed_master": {key: value for key, value in derive_seed_master(config).items() if key != "master"},
        "counts": counts, "evaluation": evaluation_plan(config),
        "ps_b0": {"state_descriptors": ps_b0_state_descriptors(), "presentations": PRESENTATIONS, "checkpoints": CHECKPOINTS, "arms": ARMS, "comparisons": 288, "comparisons_are_rollouts": False},
        "bcrh_precheck": {"corners": 8, "high_demand": True, "include_candidate_records": False, "candidate_ceiling": 1961},
        "checkpoint_retention": {"initial": True, "final": True, "storage_disjoint": True, "durable_create_once_bundle": "CHECKPOINTS.bin", "manifest": "CHECKPOINTS_MANIFEST.json", "no_selection": True},
        "named_output": {"mode": "create_once", "plan": "PLAN.json", "valid_result": "RESULT.json", "incomplete": "INCOMPLETE.json", "checkpoint_bundle": "CHECKPOINTS.bin", "old_c_frontier": False},
        "objective": "J_ext=0.5*R_fail_60+0.5*U_total", "observations": OBSERVATION_SCHEMA,
        "native_admission": {"call": "require_native_production", "batch_width": 8},
        "shadow_telemetry": {
            "schema": SHADOW_SCHEMA,
            "delayed_import_module": "experiments.candidates.variable_n_fleet_churn_b_explore",
            "apis": ("PairedPrimaryShadowBatch", "BNativeTelemetryBatch", "require_boundary_equivalence", "derive_recovery_telemetry"),
            "execution_seam": "PairedPrimaryShadowBatch only; caller supplies fixtures and commands once",
            "same_input_action_each_boundary": True,
            "main_return_source": "R09 NativeInteractiveBatch",
            "may_influence_actions": False,
            "tick_latency": "shadow direct observation; main-host application is equivalence inference",
            "boundary_or_source_drift": "INCOMPLETE",
            "host_call_cost": "one shadow host call per primary host call; approximately 2x total host calls and must be included by external telemetry",
        },
        "telemetry_schema": TELEMETRY_SCHEMA, "required_telemetry_fields": tuple(sorted(REQUIRED_TELEMETRY_FIELDS)),
        "performance_disposition": "REPAIR_REQUIRED", "runtime_ready": False,
        "repair_required": {
            "missing_adapter": "DiagnosticStateAdapter.build_support_path_state(cell, seed)",
            "required_semantics": "construct an actual-path state where null is legal, at least two agent candidates are legal, opaque deterministic tie ranks are complete, and co-permuted rows/legal/fixed/opaque fields preserve identical legal physical support; no equal-logit state is claimed",
        },
    }


def named_output_directory(output_root: Path, config: BExploreRunConfig) -> Path:
    config.validate()
    root = Path(output_root).resolve()
    return root / RUN_REVISION / config.stage / str(config.seed)


def _create_once_json(path: Path, payload: Mapping[str, object]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii") + b"\n"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise BExploreContractError(f"named BEXP output already exists: {path.name}") from error
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    return path


def _create_once_bytes(path: Path, payload: bytes) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise BExploreContractError(f"named BEXP output already exists: {path.name}") from error
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    return path


def _checkpoint_bundle_bytes(checkpoints: Mapping[str, Mapping[str, Mapping[str, object]]]) -> tuple[bytes, dict[str, object]]:
    payload = bytearray(b"VNFC-BEXP-CHECKPOINT-BUNDLE-v1\0")
    contents = []
    identities = {}
    for arm in ARMS:
        if arm not in checkpoints:
            raise BExploreContractError("checkpoint arm inventory differs")
        identities[arm] = {}
        for label in CHECKPOINTS:
            checkpoint = checkpoints[arm].get(label)
            if not isinstance(checkpoint, Mapping):
                raise BExploreContractError("checkpoint label inventory differs")
            state = checkpoint.get("state")
            if not isinstance(state, Mapping) or not state or not _is_sha256(checkpoint.get("sha256")):
                raise BExploreContractError("checkpoint state/digest is incomplete")
            identities[arm][label] = checkpoint["sha256"]
            for name in sorted(state):
                tensor = state[name]
                if not isinstance(name, str) or not isinstance(tensor, torch.Tensor) or not bool(torch.isfinite(tensor).all()):
                    raise BExploreContractError("checkpoint tensor inventory/nonfinite value differs")
                array = tensor.detach().cpu().contiguous().numpy()
                raw = array.tobytes(order="C")
                header = json.dumps({"arm": arm, "checkpoint": label, "name": name, "dtype": str(array.dtype), "shape": list(array.shape), "bytes": len(raw)}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
                payload.extend(len(header).to_bytes(8, "big")); payload.extend(header)
                payload.extend(len(raw).to_bytes(8, "big")); payload.extend(raw)
                contents.append({"arm": arm, "checkpoint": label, "name": name, "dtype": str(array.dtype), "shape": list(array.shape), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return bytes(payload), {"checkpoint_identities": identities, "contents": contents}


def _serialize_checkpoint_bundle_once(output_root: Path, config: BExploreRunConfig, checkpoints: Mapping[str, Mapping[str, Mapping[str, object]]]) -> dict[str, object]:
    """Durably retain both arms' initial/final states without using the old C publication path."""
    bundle, inventory = _checkpoint_bundle_bytes(checkpoints)
    directory = named_output_directory(output_root, config)
    bundle_path = _create_once_bytes(directory / "CHECKPOINTS.bin", bundle)
    manifest = {
        "schema": "VNFC_BPCR_BEXP_R01_CHECKPOINT_MANIFEST_V1",
        "namespace": config.namespace,
        "bundle_filename": bundle_path.name,
        "bundle_sha256": hashlib.sha256(bundle).hexdigest(),
        "bundle_size": len(bundle),
        **inventory,
    }
    try:
        manifest_path = _create_once_json(directory / "CHECKPOINTS_MANIFEST.json", manifest)
    except BaseException:
        try:
            bundle_path.unlink()
        except OSError:
            pass
        raise
    manifest["manifest_filename"] = manifest_path.name
    manifest["manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    return manifest


def validate_checkpoint_artifact(directory: Path, config: BExploreRunConfig, artifact: Mapping[str, object]) -> None:
    required = {"schema", "namespace", "bundle_filename", "bundle_sha256", "bundle_size", "checkpoint_identities", "contents", "manifest_filename", "manifest_sha256"}
    if set(artifact) != required or artifact.get("schema") != "VNFC_BPCR_BEXP_R01_CHECKPOINT_MANIFEST_V1" or artifact.get("namespace") != config.namespace:
        raise BExploreContractError("checkpoint artifact schema/namespace differs")
    if artifact.get("bundle_filename") != "CHECKPOINTS.bin" or artifact.get("manifest_filename") != "CHECKPOINTS_MANIFEST.json" or not _is_sha256(artifact.get("bundle_sha256")) or not _is_sha256(artifact.get("manifest_sha256")):
        raise BExploreContractError("checkpoint artifact filenames/digests differ")
    identities = artifact.get("checkpoint_identities")
    if not isinstance(identities, Mapping) or set(identities) != set(ARMS) or any(not isinstance(identities[arm], Mapping) or set(identities[arm]) != set(CHECKPOINTS) or any(not _is_sha256(identities[arm][label]) for label in CHECKPOINTS) for arm in ARMS):
        raise BExploreContractError("checkpoint artifact identity inventory differs")
    contents = artifact.get("contents")
    if not isinstance(contents, Sequence) or not contents:
        raise BExploreContractError("checkpoint artifact tensor inventory is absent")
    bundle_path = Path(directory) / str(artifact["bundle_filename"]); manifest_path = Path(directory) / str(artifact["manifest_filename"])
    if not bundle_path.is_file() or bundle_path.stat().st_size != artifact.get("bundle_size") or hashlib.sha256(bundle_path.read_bytes()).hexdigest() != artifact.get("bundle_sha256"):
        raise BExploreContractError("durable checkpoint bundle is absent or drifted")
    if not manifest_path.is_file() or hashlib.sha256(manifest_path.read_bytes()).hexdigest() != artifact.get("manifest_sha256"):
        raise BExploreContractError("durable checkpoint manifest is absent or drifted")
    stored = json.loads(manifest_path.read_text("ascii"))
    if stored != {key: artifact[key] for key in artifact if key not in ("manifest_filename", "manifest_sha256")}:
        raise BExploreContractError("durable checkpoint manifest content differs")


def serialize_readiness_plan_once(
    output_root: Path,
    config: BExploreRunConfig,
    *,
    preflight_receipt: Mapping[str, object],
    now: datetime,
    source_identity_provider: Callable[[], Mapping[str, object]] | None = None,
) -> Path:
    _implementation_hard_fence(preflight_receipt, now=now)
    provider = _source_identity if source_identity_provider is None else source_identity_provider
    plan = {**_exact_readiness_plan(config), "source_identity": dict(provider())}
    return _create_once_json(named_output_directory(output_root, config) / "PLAN.json", plan)


def serialize_named_outcome_once(
    output_root: Path,
    config: BExploreRunConfig,
    *,
    raw_output: Mapping[str, object],
    preflight_receipt: Mapping[str, object] | None,
    telemetry_payload: Mapping[str, object] | None,
    now: datetime,
) -> Path:
    """Preserve one valid result or one explicitly uninterpretable raw outcome."""
    if preflight_receipt is None:
        raise BExploreContractError("4 GiB preflight receipt is absent")
    _implementation_hard_fence(preflight_receipt, now=now)
    failures = []
    memory: dict[str, object] | None = None
    try:
        if preflight_receipt is None:
            raise BExploreContractError("fresh 4 GiB preflight terminal is absent")
        memory = validate_preflight_receipt(preflight_receipt, now=now)
    except (BExploreContractError, TypeError, ValueError) as error:
        failures.append(str(error))
    if memory is not None and telemetry_payload is not None:
        if telemetry_payload.get("available_physical_bytes") != memory["available_physical_bytes"] or telemetry_payload.get("effective_available_bytes") != memory["effective_available_bytes"]:
            failures.append("telemetry/preflight memory headroom binding differs")
    try:
        if telemetry_payload is None:
            raise BExploreContractError("external telemetry terminal is absent")
        validate_telemetry_payload(telemetry_payload)
    except (BExploreContractError, TypeError, ValueError) as error:
        failures.append(str(error))
    try:
        validate_runtime_terminal(config, raw_output)
        validate_checkpoint_artifact(named_output_directory(output_root, config), config, raw_output["checkpoint_artifact"])  # type: ignore[arg-type]
        if telemetry_payload is None:
            raise BExploreContractError("external telemetry terminal is absent")
        _validate_telemetry_runtime_binding(telemetry_payload, raw_output)
    except (BExploreContractError, TypeError, ValueError) as error:
        failures.append(str(error))
    valid = not failures
    payload = {
        "schema": "VNFC_BPCR_BEXP_R01_NAMED_OUTCOME_V1",
        "run_revision": RUN_REVISION,
        "namespace": config.namespace,
        "status": "VALID_B_EXPLORE_RESULT" if valid else "INCOMPLETE",
        "scientific_result": valid,
        "raw_output_uninterpreted": None if valid else dict(raw_output),
        "result": dict(raw_output) if valid else None,
        "memory_terminal": memory,
        "telemetry_terminal": dict(telemetry_payload) if telemetry_payload is not None else None,
        "incomplete_reasons": failures,
    }
    directory = named_output_directory(output_root, config)
    claim = _create_once_json(directory / "OUTCOME_CLAIM.json", {"schema": "VNFC_BPCR_BEXP_R01_OUTCOME_CLAIM_V1", "namespace": config.namespace})
    filename = "RESULT.json" if valid else "INCOMPLETE.json"
    try:
        return _create_once_json(directory / filename, payload)
    except BaseException:
        try:
            claim.unlink()
        except OSError:
            pass
        raise


def validate_debug_gate_receipt(receipt: Mapping[str, object], *, source_identity_digest: str) -> None:
    required = {"schema", "run_revision", "debug_seed", "source_identity_digest", "ps_b0_result", "bcrh_result", "performance_telemetry", "result_artifact", "checkpoint_artifact", "common_host_valid", "valid"}
    if set(receipt) != required or receipt.get("schema") != "VNFC_BPCR_BEXP_R01_ARCHIVED_DEBUG_GATE_V1" or receipt.get("run_revision") != RUN_REVISION or receipt.get("debug_seed") != DEBUG_SEED:
        raise BExploreContractError("archived DEBUG gate schema/identity differs")
    if receipt.get("source_identity_digest") != source_identity_digest or receipt.get("common_host_valid") is not True or receipt.get("valid") is not True:
        raise BExploreContractError("archived DEBUG gate source/common-host validity differs")
    ps = receipt.get("ps_b0_result"); bcrh = receipt.get("bcrh_result")
    if not isinstance(ps, Mapping) or ps.get("passed") is not True or ps.get("mismatch_by_arm") != {"MAPR": 0, "DIRECT": 0}:
        raise BExploreContractError("archived DEBUG PS-B0 gate differs")
    if not isinstance(bcrh, Mapping) or bcrh.get("common_host_valid") is not True:
        raise BExploreContractError("archived DEBUG BCRH/common-host gate differs")
    telemetry = receipt.get("performance_telemetry")
    if not isinstance(telemetry, Mapping):
        raise BExploreContractError("archived DEBUG measured performance is absent")
    validate_telemetry_payload(telemetry)
    result_artifact = receipt.get("result_artifact")
    if not isinstance(result_artifact, Mapping) or set(result_artifact) != {"filename", "sha256", "claim_sha256"} or result_artifact.get("filename") != "RESULT.json" or not _is_sha256(result_artifact.get("sha256")) or not _is_sha256(result_artifact.get("claim_sha256")):
        raise BExploreContractError("archived DEBUG result artifact binding differs")
    checkpoint_artifact = receipt.get("checkpoint_artifact")
    if not isinstance(checkpoint_artifact, Mapping) or checkpoint_artifact.get("namespace") != BExploreRunConfig(DEBUG_STAGE, DEBUG_SEED, 8).namespace:
        raise BExploreContractError("archived DEBUG checkpoint artifact binding differs")


def build_debug_gate_receipt(debug_result_path: Path, *, source_identity_digest: str, preflight_receipt: Mapping[str, object], now: datetime) -> dict[str, object]:
    """Build a PRIMARY gate only from the archived create-once VALID DEBUG artifact."""
    _implementation_hard_fence(preflight_receipt, now=now)
    debug_config = BExploreRunConfig(DEBUG_STAGE, DEBUG_SEED, 8)
    result_path = Path(debug_result_path).resolve()
    if result_path.name != "RESULT.json" or tuple(part.lower() for part in result_path.parts[-4:-1]) != (RUN_REVISION.lower(), DEBUG_STAGE.lower(), str(DEBUG_SEED)):
        raise BExploreContractError("DEBUG gate input is not the exact named RESULT path")
    claim_path = result_path.parent / "OUTCOME_CLAIM.json"
    if not result_path.is_file() or not claim_path.is_file():
        raise BExploreContractError("archived create-once DEBUG result/claim is absent")
    payload = json.loads(result_path.read_text("ascii")); claim = json.loads(claim_path.read_text("ascii"))
    if not isinstance(payload, Mapping) or payload.get("schema") != "VNFC_BPCR_BEXP_R01_NAMED_OUTCOME_V1" or payload.get("namespace") != debug_config.namespace or payload.get("status") != "VALID_B_EXPLORE_RESULT" or payload.get("scientific_result") is not True or payload.get("raw_output_uninterpreted") is not None:
        raise BExploreContractError("archived DEBUG artifact is not a VALID named result")
    if claim != {"schema": "VNFC_BPCR_BEXP_R01_OUTCOME_CLAIM_V1", "namespace": debug_config.namespace}:
        raise BExploreContractError("archived DEBUG create-once claim differs")
    debug_terminal = payload.get("result"); performance_telemetry = payload.get("telemetry_terminal")
    if not isinstance(debug_terminal, Mapping) or not isinstance(performance_telemetry, Mapping):
        raise BExploreContractError("archived DEBUG result/telemetry payload is absent")
    validate_runtime_terminal(debug_config, debug_terminal)
    if debug_terminal.get("source_pre_digest") != source_identity_digest or debug_terminal.get("source_post_digest") != source_identity_digest:
        raise BExploreContractError("archived DEBUG result source binding differs")
    ps = debug_terminal.get("ps_b0_result"); bcrh = debug_terminal.get("bcrh_precheck_result")
    if not isinstance(ps, Mapping) or not isinstance(bcrh, Mapping):
        raise BExploreContractError("DEBUG gate results are absent")
    validate_telemetry_payload(performance_telemetry)
    _validate_telemetry_runtime_binding(performance_telemetry, debug_terminal)
    checkpoint_artifact = debug_terminal.get("checkpoint_artifact")
    if not isinstance(checkpoint_artifact, Mapping):
        raise BExploreContractError("archived DEBUG checkpoint artifact is absent")
    validate_checkpoint_artifact(result_path.parent, debug_config, checkpoint_artifact)
    receipt = {"schema": "VNFC_BPCR_BEXP_R01_ARCHIVED_DEBUG_GATE_V1", "run_revision": RUN_REVISION, "debug_seed": DEBUG_SEED, "source_identity_digest": source_identity_digest, "ps_b0_result": dict(ps), "bcrh_result": dict(bcrh), "performance_telemetry": dict(performance_telemetry), "result_artifact": {"filename": result_path.name, "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(), "claim_sha256": hashlib.sha256(claim_path.read_bytes()).hexdigest()}, "checkpoint_artifact": dict(checkpoint_artifact), "common_host_valid": bcrh.get("common_host_valid") is True, "valid": ps.get("passed") is True and bcrh.get("common_host_valid") is True}
    validate_debug_gate_receipt(receipt, source_identity_digest=source_identity_digest)
    return receipt


def assess_pretraining_readiness(
    config: BExploreRunConfig, *, preflight_receipt: Mapping[str, object], telemetry_sink: TelemetrySink,
    now: datetime, source_identity_digest: str,
    native_admission: Callable[..., Mapping[str, object]] = require_native_production,
    archived_debug_result_path: Path | None = None,
) -> dict[str, object]:
    memory = _implementation_hard_fence(preflight_receipt, now=now)
    plan = _exact_readiness_plan(config)
    validate_telemetry_sink(telemetry_sink)
    native = dict(native_admission(batch_width=8))
    if config.stage != DEBUG_STAGE:
        if archived_debug_result_path is None:
            return {**plan, "readiness_status": "REPAIR_REQUIRED", "memory": memory, "native": native, "pretraining_ready": False, "performance_blocker": "archived valid DEBUG gate/performance receipt is absent"}
        debug_gate_receipt = build_debug_gate_receipt(archived_debug_result_path, source_identity_digest=source_identity_digest, preflight_receipt=preflight_receipt, now=now)
        validate_debug_gate_receipt(debug_gate_receipt, source_identity_digest=source_identity_digest)
    else:
        debug_gate_receipt = None
    return {**plan, "readiness_status": "PRETRAIN_READY", "memory": memory, "native": native, "pretraining_ready": True, "performance_disposition": "PILOT_ONLY", "debug_gate_receipt": debug_gate_receipt}


def _construct_ps_b0_actual(config: BExploreRunConfig, diagnostic_state_adapter: object, models_by_checkpoint: Mapping[str, Mapping[str, object]], rng: _SeedRNG) -> tuple[PSB0Comparison, ...]:
    builder = getattr(diagnostic_state_adapter, "build_support_path_state", None)
    compare = getattr(diagnostic_state_adapter, "compare_presentations", None)
    if not callable(builder) or not callable(compare):
        raise BExploreContractError("REPAIR_REQUIRED: actual-path DiagnosticStateAdapter.build_support_path_state/compare_presentations is absent")
    rows = []
    for descriptor in ps_b0_state_descriptors():
        state = builder(dict(descriptor), config.seed)
        for presentation in PRESENTATIONS:
            for checkpoint in CHECKPOINTS:
                for arm in ARMS:
                    rows.append(compare(state, presentation, checkpoint, arm, models_by_checkpoint[checkpoint][arm], rng))
    return tuple(rows)


def _run_bcrh_precheck_actual() -> tuple[BCRHPrecheckRow, ...]:
    fixtures = tuple(BCRHFixture(zone, 2, 2, int(obstruction and zone == 1), int(obstruction and zone == 2), int(relay)) for zone in ZONES for obstruction in (False, True) for relay in (False, True))
    outputs = run_native_fixture_batch(fixtures)
    rows = []
    for fixture, output in zip(fixtures, outputs):
        command = tuple(output["scorer_command"]); used = tuple(value for value in command if value is not None)
        rows.append(BCRHPrecheckRow(fixture.failed_zone, bool(fixture.blocked_1 if fixture.failed_zone == 1 else fixture.blocked_2), bool(fixture.failed_relay_present), True, len(used) == len(set(used)), bool(output["scorer_checker_equal"]), bool(output["independent_enumerator_equal"]), True, int(output["candidate_count"]), False, False))
    return tuple(rows)


def assess_posttraining_debug_gate(config: BExploreRunConfig, *, diagnostic_state_adapter: object | None, models_by_checkpoint: Mapping[str, Mapping[str, object]], rng: _SeedRNG) -> dict[str, object]:
    if config.stage != DEBUG_STAGE:
        raise BExploreContractError("post-training PS-B0 gate belongs only to DEBUG")
    if diagnostic_state_adapter is None:
        return {"status": "REPAIR_REQUIRED", "missing_adapter": "DiagnosticStateAdapter.build_support_path_state/compare_presentations", "runtime_ready": False}
    ps = validate_ps_b0(_construct_ps_b0_actual(config, diagnostic_state_adapter, models_by_checkpoint, rng)); bcrh = validate_bcrh_precheck(_run_bcrh_precheck_actual())
    return {"status": "DEBUG_GATE_PASSED" if bcrh["common_host_valid"] else "REPAIR_REQUIRED", "ps_b0_result": ps, "bcrh_result": bcrh, "runtime_ready": bool(bcrh["common_host_valid"])}


def _source_identity() -> dict[str, object]:
    repo = Path(__file__).resolve().parents[1]; files = []
    for relative in _ACTUAL_SOURCE_PATHS:
        path = repo / relative
        if not path.is_file():
            raise BExploreContractError(f"actual source input is absent: {relative}")
        files.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    library = require_cpp_batched_backend(); artifact = Path(library._name).resolve()
    from experiments.candidates.variable_n_fleet_churn_b_explore import native_artifact_identity as shadow_artifact_identity
    shadow = _stable_shadow_identity(shadow_artifact_identity())
    return {
        "mode": "current_checkout_actual_bytes", "files": tuple(files),
        "native_artifact": {"path": str(artifact), "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(), "size": artifact.stat().st_size, "build_key": native_build_key(), "source_sha256": native_source_sha256()},
        "shadow_native_artifact": shadow,
    }


@dataclass(frozen=True)
class _SourceFence:
    identity: dict[str, object]

    @classmethod
    def capture(cls) -> "_SourceFence":
        return cls(_source_identity())

    def close(self) -> None:
        if _source_identity() != self.identity:
            raise BExploreContractError("BEXP R01 source/native identity drifted during execution")


def _execute_evaluation(config: BExploreRunConfig, rng: _SeedRNG, token: _HeldoutFreezeToken, models_by_checkpoint: Mapping[str, Mapping[str, object]], now: datetime) -> dict[str, object]:
    checkpoints = ("final",) if config.stage == DEBUG_STAGE else CHECKPOINTS
    fixture_cache = {}
    for n in ROSTERS:
        for zone in ZONES:
            purpose = "evaluation-train-support" if n in (3, 5) else "heldout-N7"
            fixture_cache[(n, zone)] = tuple(_build_world(rng, config, purpose=purpose, roster_size=n, failed_zone=zone, row=row, now=now) for row in range(8))
    learned = []
    for n in ROSTERS:
        for zone in ZONES:
            cell = f"N{n}z{zone}"
            for checkpoint in checkpoints:
                for arm in ARMS:
                    learned.append(_evaluate_learned_batch(config, rng, token, fixture_cache[(n, zone)], models_by_checkpoint[checkpoint][arm], arm, checkpoint, cell, tuple(range(8)), now))  # type: ignore[arg-type]
    bcrh = tuple(_evaluate_bcrh_batch(config, token, fixture_cache[(7, zone)], f"N7z{zone}", tuple(range(8))) for zone in ZONES)
    total = sum(int(row["rollouts"]) for row in learned) + sum(int(row["rollouts"]) for row in bcrh)
    if total != expected_counts(config)["evaluation_rollouts_total"]:
        raise BExploreContractError("actual evaluation rollout count differs")
    mismatch = {arm: sum(int(row["relabel_mismatch_count"]) for row in learned if row["arm"] == arm) for arm in ARMS}
    if mismatch != {"MAPR": 0, "DIRECT": 0}:
        raise BExploreContractError("INCOMPLETE: learned-arm actual-path relabel mismatch")
    return {"learned": tuple(learned), "bcrh": bcrh, "rollouts": total, "relabel_mismatch_count": mismatch}


def _endpoint_values(endpoint: Mapping[str, object]) -> dict[str, float]:
    fail = endpoint["fail_endpoint"]; total = endpoint["total_endpoint"]; intact = endpoint["intact_endpoint"]  # type: ignore[assignment]
    values = {"R_fail_60": fail[0] / fail[1], "U_total": total[0] / total[1], "U_intact": intact[0] / intact[1]}  # type: ignore[index,operator]
    values["J_ext"] = .5 * values["R_fail_60"] + .5 * values["U_total"]
    return values


def _exploratory_readout(config: BExploreRunConfig, evaluation: Mapping[str, object]) -> dict[str, object]:
    learned = {}; bcrh = {}; individual = []; recovery = []
    for group in evaluation["learned"]:  # type: ignore[union-attr]
        for world, endpoint in enumerate(group["endpoints"]):
            values = _endpoint_values(endpoint); learned[(group["cell"], group["checkpoint"], group["arm"], world)] = values
            individual.append({"cell": group["cell"], "checkpoint": group["checkpoint"], "arm": group["arm"], "world": world, **values})
        paired_receipt = group["shadow_receipts"][0]
        recovery.extend({"cell": group["cell"], "checkpoint": group["checkpoint"], "arm": group["arm"], "world": world, **row} for world, row in enumerate(paired_receipt["episode_recovery"]))
    for group in evaluation["bcrh"]:  # type: ignore[union-attr]
        for world, endpoint in enumerate(group["endpoints"]):
            values = _endpoint_values(endpoint); bcrh[(group["cell"], world)] = values
            individual.append({"cell": group["cell"], "checkpoint": "fixed", "arm": "BCRH", "world": world, **values})
        paired_receipt = group["shadow_receipts"][0]
        recovery.extend({"cell": group["cell"], "checkpoint": "fixed", "arm": "BCRH", "world": world, **row} for world, row in enumerate(paired_receipt["episode_recovery"]))
    contrasts = []
    if config.stage != DEBUG_STAGE:
        for cell in (f"N{n}z{zone}" for n in ROSTERS for zone in ZONES):
            for arm in ARMS:
                for world in range(8):
                    contrasts.append({"kind": "final_minus_initial", "cell": cell, "arm": arm, "world": world, **{endpoint: learned[(cell, "final", arm, world)][endpoint] - learned[(cell, "initial", arm, world)][endpoint] for endpoint in ("J_ext", "R_fail_60", "U_total", "U_intact")}})
        for cell in ("N7z1", "N7z2"):
            for world in range(8):
                contrasts.append({"kind": "MAPR_minus_DIRECT", "cell": cell, "world": world, **{endpoint: learned[(cell, "final", "MAPR", world)][endpoint] - learned[(cell, "final", "DIRECT", world)][endpoint] for endpoint in ("J_ext", "R_fail_60", "U_total", "U_intact")}})
                contrasts.append({"kind": "MAPR_minus_BCRH", "cell": cell, "world": world, **{endpoint: learned[(cell, "final", "MAPR", world)][endpoint] - bcrh[(cell, world)][endpoint] for endpoint in ("J_ext", "R_fail_60", "U_total", "U_intact")}})
    return {"individual_world_seed": tuple(individual), "paired_contrasts": tuple(contrasts), "recovery_latency": tuple(recovery)}


def _runtime_terminal(config: BExploreRunConfig, training: Mapping[str, object], evaluation: Mapping[str, object], checkpoints: Mapping[str, object], gate: Mapping[str, object], source_digest: str, checkpoint_artifact: Mapping[str, object]) -> dict[str, object]:
    counts = expected_counts(config)
    training_shadow = tuple(receipt for arm in ARMS for update in training[arm]["updates_telemetry"] for receipt in update["shadow_receipts"])  # type: ignore[index]
    evaluation_shadow = tuple(receipt for row in (*evaluation["learned"], *evaluation["bcrh"]) for receipt in row["shadow_receipts"])  # type: ignore[index]
    shadow_receipts = training_shadow + evaluation_shadow
    hard_valid = all(row["hard_valid"] for row in (*evaluation["learned"], *evaluation["bcrh"]))  # type: ignore[index]
    finite_values = all(bool(training[arm]["finite_values"]) and int(training[arm]["nonfinite_update_count"]) == 0 for arm in ARMS) and all(bool(row["finite_values"]) for row in (*evaluation["learned"], *evaluation["bcrh"]))  # type: ignore[index]
    bcrh_status = "IDENTIFIED" if all(row["comparison_status"] == "IDENTIFIED" for row in evaluation["bcrh"]) else "NONIDENTIFIED"  # type: ignore[index]
    exposure = {
        "training": {arm: {"action_selection_forward_calls": training[arm]["training_action_forward_calls"], "optimizer_forward_calls": training[arm]["optimizer_forward_calls"], "backward_calls": training[arm]["backward_calls"]} for arm in ARMS},  # type: ignore[index]
        "evaluation": {arm: {"policy_forward_calls": sum(int(row["evaluation_policy_forward_calls"]) for row in (*evaluation["learned"], *evaluation["bcrh"]) if row["arm"] == arm), "diagnostic_forward_calls": sum(int(row["diagnostic_forward_calls"]) for row in (*evaluation["learned"], *evaluation["bcrh"]) if row["arm"] == arm)} for arm in (*ARMS, "BCRH")},  # type: ignore[index]
    }
    terminal = {
        "schema": "VNFC_BPCR_BEXP_R01_RUNTIME_TERMINAL_V1", "namespace": config.namespace,
        "counts": counts, "ps_b0_passed": gate.get("ps_b0_result", {}).get("passed") is True,
        "learned_relabel_mismatch_count": evaluation["relabel_mismatch_count"],
        "common_host_hard_valid": hard_valid, "finite_values": finite_values,
        "initial_final_checkpoints_retained": all(checkpoints[arm][kind]["storage_disjoint"] for arm in ARMS for kind in CHECKPOINTS) and checkpoint_artifact.get("namespace") == config.namespace,
        "n7_controls_frozen_before_open": True, "source_pre_digest": source_digest, "source_post_digest": source_digest,
        "shadow_boundary_exact": True, "shadow_source_stable": True, "shadow_influenced_actions": False,
        "observations_complete": True, "training_observation_rows": counts["training_episodes_total"],
        "individual_world_seed_rows": counts["evaluation_rollouts_total"], "optimization_rows": counts["optimizer_steps_total"],
        "bcrh_comparison_status": bcrh_status, "shadow_receipts": shadow_receipts,
        "training": training, "evaluation": evaluation, "exploratory_readout": _exploratory_readout(config, evaluation), "exposure": exposure,
        "ps_b0_result": gate.get("ps_b0_result"), "bcrh_precheck_result": gate.get("bcrh_result"), "checkpoint_artifact": dict(checkpoint_artifact),
    }
    validate_runtime_terminal(config, terminal)
    return terminal


def _load_source_bound_diagnostic_adapter() -> object | None:
    """Return only a built-in, source-fenced adapter; none exists in R01 yet."""
    return None


def _run_after_pretraining_readiness(config: BExploreRunConfig, *, now: datetime, fence: _SourceFence, source_digest: str, diagnostic_state_adapter: object | None, archived_debug_gate_receipt: Mapping[str, object] | None, output_root: Path) -> dict[str, object]:
        master = derive_seed_master(config)["master"]; rng = _SeedRNG(master)  # type: ignore[arg-type]
        learners = _initialize_learners(config, rng, now); initial_models = {arm: copy.deepcopy(learners["models"][arm]) for arm in ARMS}  # type: ignore[index]
        checkpoints = {arm: {"initial": clone_checkpoint(learners["models"][arm], "initial")} for arm in ARMS}  # type: ignore[index]
        training = _train_learners(config, rng, learners, now)
        for arm in ARMS:
            checkpoints[arm]["final"] = clone_checkpoint(learners["models"][arm], "final")  # type: ignore[index]
            validate_checkpoint_pair(checkpoints[arm]["initial"], checkpoints[arm]["final"])
        checkpoint_artifact = _serialize_checkpoint_bundle_once(output_root, config, checkpoints)  # type: ignore[arg-type]
        models_by_checkpoint = {"initial": initial_models, "final": learners["models"]}  # type: ignore[index]
        if config.stage == DEBUG_STAGE:
            gate = assess_posttraining_debug_gate(config, diagnostic_state_adapter=diagnostic_state_adapter, models_by_checkpoint=models_by_checkpoint, rng=rng)
            if not gate["runtime_ready"]:
                raise BExploreContractError(f"REPAIR_REQUIRED: {gate.get('missing_adapter', 'post-training DEBUG gate is incomplete')}")
        else:
            if not isinstance(archived_debug_gate_receipt, Mapping):
                raise BExploreContractError("REPAIR_REQUIRED: archived DEBUG gate receipt is absent")
            gate = {"status": "ARCHIVED_DEBUG_GATE_ACCEPTED", "ps_b0_result": archived_debug_gate_receipt.get("ps_b0_result"), "bcrh_result": archived_debug_gate_receipt.get("bcrh_result"), "runtime_ready": True}
        token = _freeze_before_n7(config, training, checkpoints, gate)
        evaluation = _execute_evaluation(config, rng, token, models_by_checkpoint, now)
        fence.close()
        return _runtime_terminal(config, training, evaluation, checkpoints, gate, source_digest, checkpoint_artifact)


def run_b_explore_runtime(
    config: BExploreRunConfig, *, preflight_receipt: Mapping[str, object],
    telemetry_sink: TelemetrySink, now: datetime, output_root: Path,
    native_admission: Callable[..., Mapping[str, object]] = require_native_production,
    archived_debug_result_path: Path | None = None,
) -> dict[str, object]:
    """Execute only when source-bound semantics exist; no caller semantic seam."""
    _implementation_hard_fence(preflight_receipt, now=now)
    previous_threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1); fence = _SourceFence.capture(); source_digest = _canonical_digest(fence.identity)
        readiness = assess_pretraining_readiness(config, preflight_receipt=preflight_receipt, telemetry_sink=telemetry_sink, now=now, source_identity_digest=source_digest, native_admission=native_admission, archived_debug_result_path=archived_debug_result_path)
        if not readiness["pretraining_ready"]:
            raise BExploreContractError(f"REPAIR_REQUIRED: {readiness.get('performance_blocker', 'pretraining readiness failed')}")
        adapter = _load_source_bound_diagnostic_adapter() if config.stage == DEBUG_STAGE else None
        if config.stage == DEBUG_STAGE and adapter is None:
            fence.close()
            raise BExploreContractError("REPAIR_REQUIRED: source-bound actual-path PS-B0 support-state adapter is absent")
        return _run_after_pretraining_readiness(config, now=now, fence=fence, source_digest=source_digest, diagnostic_state_adapter=adapter, archived_debug_gate_receipt=readiness.get("debug_gate_receipt"), output_root=output_root)
    finally:
        torch.set_num_threads(previous_threads)


__all__ = [
    "BExploreContractError", "BExploreRunConfig", "IMPLEMENTATION_BLOCKER", "IMPLEMENTATION_READY",
    "RUN_REVISION", "TELEMETRY_SCHEMA", "assess_pretraining_readiness", "build_debug_gate_receipt",
    "run_b_explore_runtime", "serialize_named_outcome_once",
    "serialize_readiness_plan_once", "validate_preflight_receipt",
]
