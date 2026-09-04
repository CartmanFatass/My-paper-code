"""Readiness/runtime contract for VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R01.

This Class-B object uses revision-09 only as engineering substrate.  It does
not call the old full panel, exact reducer, CUT arm, frontier, or atomic result
publication.  Its public runtime remains fail-closed on per-invocation memory,
prebuilt-native, source, DEBUG-gate, telemetry, and three-artifact contracts.
"""
from __future__ import annotations

import ast
import argparse
from dataclasses import asdict, dataclass
from contextlib import nullcontext
from contextvars import ContextVar
from datetime import datetime, timezone
import copy
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import sys
from typing import Callable, Mapping, Protocol, Sequence

if __name__ == "__main__":
    _cli_repository_root = str(Path(__file__).resolve().parents[1])
    if _cli_repository_root not in sys.path:
        sys.path.insert(0, _cli_repository_root)

import numpy as np
import torch

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import (
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
IMPLEMENTATION_READY = True
IMPLEMENTATION_BLOCKER = None
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
})
PROCESS_TELEMETRY_PROVENANCE_FIELDS = frozenset({
    "performance_evidence", "measurement_source", "measurement_limitations", "sample_interval_seconds", "sample_count",
    "preflight_binding", "stage_observation_count", "cpu_core_equivalents", "host_cpu_occupancy",
    "logical_processor_count", "peak_process_count", "peak_thread_count", "scientific_work_transitions",
    "io_other_bytes", "aggregate_io_bytes",
    "implementation_ready", "performance_readiness", "implementation_blocker", "storage_high_water_disposition",
    "durable_directory_total_bytes", "durable_artifact_inventory", "frozen_native_artifact_inventory",
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
    "experiments/candidates/variable_n_fleet_churn_b_explore/process_telemetry.py",
    "experiments/candidates/variable_n_fleet_churn_b_explore/ps_b0.py",
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


_ACTIVE_DURABLE_RECORDER: ContextVar[object | None] = ContextVar("vnfc_bexp_durable_recorder", default=None)
_ACTIVE_INCOMPLETE_REASON: ContextVar[str | None] = ContextVar("vnfc_bexp_incomplete_reason", default=None)


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
    mismatch = 0; raw_sensitivity = tuple(batch.sensitivity()) if cell.startswith("N7") else (); sensitivity = tuple({"world": int(world_rows[index]), **row} for index, row in enumerate(raw_sensitivity)); rows: tuple[dict[str, object], ...] = (); residual_rows = []; policy_forwards = 0; diagnostic_forwards = 0
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
                    residual_rows.extend({"boundary": epoch, "world_row": world_rows[index], "total_variation": float(tv[index]), "physical_command_change": not torch.equal(output["command"][index], zero_free["command"][index]), "status": "OBSERVED_DIRECT_ABLATION"} for index in range(8))
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
        return {"arm": arm, "checkpoint": checkpoint, "cell": cell, "rollouts": 8, "relabel_mismatch_count": mismatch, "hard_valid": all(row["terminal"] and not row["safety_violation"] and not row["exclusivity_violation"] for row in rows), "finite_values": validated_endpoint_rows == 8 and policy_forwards == 6 and diagnostic_forwards == expected_diagnostic, "evaluation_policy_forward_calls": policy_forwards, "diagnostic_forward_calls": diagnostic_forwards, "action_sensitivity": sensitivity, "action_sensitivity_status": "OBSERVED_TREATMENT_BLIND_N7" if cell.startswith("N7") else "NOT_APPLICABLE_TRAIN_SUPPORT_CELL", "direct_residual_activity": tuple(residual_rows), "direct_residual_activity_status": "OBSERVED_DIRECT_ABLATION" if arm == "DIRECT" else "NOT_APPLICABLE_MAPR", "endpoints": tuple({key: row[key] for key in ("fail_endpoint", "total_endpoint", "intact_endpoint")} for row in rows), "shadow_receipts": (receipt,)}
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


def _require_process_tree_telemetry_sink(sink: object, *, expected_durable_root: Path | None = None) -> None:
    from experiments.candidates.variable_n_fleet_churn_b_explore import process_telemetry
    ProcessTreeTelemetrySink = process_telemetry.ProcessTreeTelemetrySink
    if not isinstance(sink, ProcessTreeTelemetrySink):
        raise BExploreContractError("REPAIR_REQUIRED: concrete outcome-blind ProcessTreeTelemetrySink is required")
    if process_telemetry.IMPLEMENTATION_READY is not True or getattr(sink, "_exact_storage_contract", None) is None:
        raise BExploreContractError("REPAIR_REQUIRED: exact R01 storage telemetry contract is not active")
    if expected_durable_root is not None and Path(getattr(sink, "durable_root")).resolve() != Path(expected_durable_root).resolve():
        raise BExploreContractError("REPAIR_REQUIRED: telemetry durable root differs from the exact named namespace")


def validate_telemetry_payload(payload: Mapping[str, object]) -> None:
    if not REQUIRED_TELEMETRY_FIELDS <= set(payload):
        raise BExploreContractError("scientific result telemetry is incomplete")
    if not PROCESS_TELEMETRY_PROVENANCE_FIELDS <= set(payload):
        raise BExploreContractError("process-tree telemetry provenance/inventory is incomplete")
    if any(payload[field] is None for field in REQUIRED_TELEMETRY_FIELDS):
        raise BExploreContractError("scientific result telemetry contains unmeasured fields")
    if payload.get("telemetry_schema") != TELEMETRY_SCHEMA or payload.get("telemetry_terminal") is not True:
        raise BExploreContractError("external telemetry terminal/schema differs")
    positive = ("end_to_end_wall_seconds", "end_to_end_cpu_seconds", "process_tree_peak_rss_bytes", "available_physical_bytes", "effective_available_bytes", "native_integrated_ticks", "scientific_work_transitions_per_second", "worker_count", "threads_per_worker")
    if any(not isinstance(payload[field], (int, float)) or isinstance(payload[field], bool) or not math.isfinite(float(payload[field])) or payload[field] <= 0 for field in positive):
        raise BExploreContractError("external telemetry contains nonpositive measured fields")
    stages = {"source_binding", "training", "evaluation", "serialization"}
    for field in ("stage_wall_seconds", "stage_cpu_seconds"):
        values = payload[field]
        if not isinstance(values, Mapping) or set(values) != stages or any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) or value < 0 for value in values.values()):
            raise BExploreContractError("external stage wall/CPU telemetry differs")
    for field in ("parameter_count_by_arm", "forward_calls_by_arm", "backward_calls_by_arm", "flop_exposure_by_arm"):
        values = payload[field]
        if not isinstance(values, Mapping) or set(values) != set(ARMS) or any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) or value <= 0 for value in values.values()):
            raise BExploreContractError("external per-arm exposure telemetry differs")
    for field in ("scratch_peak_bytes", "durable_peak_bytes", "io_read_bytes", "io_write_bytes"):
        if not isinstance(payload[field], int) or isinstance(payload[field], bool) or payload[field] < 0:
            raise BExploreContractError("external storage/I/O telemetry differs")
    primary_calls = payload["primary_host_calls"]; shadow_calls = payload["shadow_host_calls"]
    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in (primary_calls, shadow_calls)):
        raise BExploreContractError("operation-resolved host-call telemetry differs")
    if payload["available_physical_bytes"] < MINIMUM_AVAILABLE_BYTES or payload["effective_available_bytes"] < MINIMUM_AVAILABLE_BYTES:
        raise BExploreContractError("telemetry memory headroom is below 4 GiB")
    if payload.get("performance_evidence") is not True or payload.get("measurement_source") != "Windows Toolhelp/Process/PSAPI process-tree sampling" or not isinstance(payload.get("measurement_limitations"), Sequence) or not payload["measurement_limitations"]:
        raise BExploreContractError("process-tree telemetry measurement source/limitations differ")
    if payload.get("implementation_ready") is not True or payload.get("performance_readiness") != "READY" or payload.get("implementation_blocker") is not None or payload.get("storage_high_water_disposition") != "EXACT_R01_MONOTONIC_CREATE_ONLY" or payload.get("scratch_peak_bytes") != 0 or payload.get("durable_peak_bytes") != payload.get("durable_directory_total_bytes"):
        raise BExploreContractError("exact process/storage telemetry readiness differs")
    durable_inventory = payload.get("durable_artifact_inventory")
    if not isinstance(durable_inventory, Sequence) or not durable_inventory or any(not isinstance(row, Mapping) or set(row) != {"relative_path", "size_bytes", "sha256"} or not isinstance(row["relative_path"], str) or not row["relative_path"] or not isinstance(row["size_bytes"], int) or isinstance(row["size_bytes"], bool) or row["size_bytes"] <= 0 or not _is_sha256(row["sha256"]) for row in durable_inventory) or len({row["relative_path"] for row in durable_inventory}) != len(durable_inventory) or sum(row["size_bytes"] for row in durable_inventory) != payload["durable_peak_bytes"]:
        raise BExploreContractError("exact durable artifact inventory/peak binding differs")
    native_inventory = payload.get("frozen_native_artifact_inventory")
    if not isinstance(native_inventory, Sequence) or not native_inventory or any(not isinstance(row, Mapping) or set(row) != {"path", "size_bytes", "sha256"} or not isinstance(row["path"], str) or not row["path"] or not isinstance(row["size_bytes"], int) or isinstance(row["size_bytes"], bool) or row["size_bytes"] <= 0 or not _is_sha256(row["sha256"]) for row in native_inventory):
        raise BExploreContractError("frozen prebuilt native artifact inventory differs")
    for field in ("sample_interval_seconds", "cpu_core_equivalents", "logical_processor_count", "peak_process_count", "peak_thread_count", "sample_count", "scientific_work_transitions"):
        if not _finite_number(payload.get(field)) or payload[field] <= 0:
            raise BExploreContractError("process-tree telemetry sampling/exposure value differs")
    if not _finite_number(payload.get("host_cpu_occupancy")) or not 0 <= payload["host_cpu_occupancy"] <= 1:
        raise BExploreContractError("process-tree host CPU occupancy differs")
    observations = payload.get("stage_observation_count")
    if not isinstance(observations, Mapping) or set(observations) != {"source_binding", "training", "evaluation", "serialization"} or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in observations.values()):
        raise BExploreContractError("process-tree stage observation inventory differs")
    binding = payload.get("preflight_binding")
    binding_keys = {"schema_version", "receipt_sha256", "captured_at", "assessed_at", "age_seconds_at_monitor_start", "available_physical_bytes", "effective_available_bytes"}
    if not isinstance(binding, Mapping) or set(binding) != binding_keys or binding.get("schema_version") != 1 or not _is_sha256(binding.get("receipt_sha256")) or binding.get("available_physical_bytes") != payload["available_physical_bytes"] or binding.get("effective_available_bytes") != payload["effective_available_bytes"] or not _finite_number(binding.get("age_seconds_at_monitor_start")) or not -5 <= binding["age_seconds_at_monitor_start"] <= PREFLIGHT_FRESH_SECONDS:
        raise BExploreContractError("process-tree telemetry preflight binding differs")
    for field in ("io_other_bytes", "aggregate_io_bytes"):
        if not isinstance(payload[field], int) or isinstance(payload[field], bool) or payload[field] < 0:
            raise BExploreContractError("process-tree telemetry extended I/O differs")
    if payload["aggregate_io_bytes"] != payload["io_read_bytes"] + payload["io_write_bytes"] + payload["io_other_bytes"]:
        raise BExploreContractError("process-tree aggregate I/O binding differs")
    expected_throughput = payload["scientific_work_transitions"] / payload["end_to_end_wall_seconds"]
    if not math.isclose(payload["scientific_work_transitions_per_second"], expected_throughput, rel_tol=1e-12, abs_tol=1e-12):
        raise BExploreContractError("process-tree scientific throughput binding differs")


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
    ledger = terminal.get("host_call_ledger")
    if not isinstance(ledger, Mapping) or payload.get("primary_host_calls") != ledger.get("primary_total") or payload.get("shadow_host_calls") != ledger.get("shadow_total"):
        raise BExploreContractError("external telemetry/runtime operation-resolved host-call binding differs")


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
        for update_index, update in enumerate(updates):
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
            expected_ids = {f"{config.namespace}/TRAIN/{arm}/u{update_index}/N3", f"{config.namespace}/TRAIN/{arm}/u{update_index}/N5"}
            if {receipt.get("batch_id") for receipt in receipts if isinstance(receipt, Mapping)} != expected_ids:
                raise BExploreContractError("training paired receipt local owner/address differs")
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
        required_row = {"arm", "checkpoint", "cell", "rollouts", "relabel_mismatch_count", "hard_valid", "finite_values", "evaluation_policy_forward_calls", "diagnostic_forward_calls", "action_sensitivity", "action_sensitivity_status", "direct_residual_activity", "direct_residual_activity_status", "endpoints", "shadow_receipts"}
        if not isinstance(row, Mapping) or set(row) != required_row:
            raise BExploreContractError("learned evaluation row schema differs")
        address_ = (row["cell"], row["checkpoint"], row["arm"]); addresses.add(address_)
        direct = row["arm"] == "DIRECT"; n7 = str(row["cell"]).startswith("N7")
        if row.get("rollouts") != 8 or row.get("relabel_mismatch_count") != 0 or row.get("hard_valid") is not True or row.get("finite_values") is not True or row.get("evaluation_policy_forward_calls") != 6 or row.get("diagnostic_forward_calls") != (60 if direct else 48):
            raise BExploreContractError("learned evaluation validity/exposure differs")
        sensitivity = row.get("action_sensitivity", ())
        sensitivity_keys = {"world", "candidate_count", "min_c60", "max_c60", "sensitive"}
        if len(sensitivity) != (8 if n7 else 0) or row.get("action_sensitivity_status") != ("OBSERVED_TREATMENT_BLIND_N7" if n7 else "NOT_APPLICABLE_TRAIN_SUPPORT_CELL"):
            raise BExploreContractError("learned action sensitivity inventory differs")
        if n7 and (any(not isinstance(item, Mapping) or set(item) != sensitivity_keys or not isinstance(item["world"], int) or item["world"] not in range(8) or not isinstance(item["candidate_count"], int) or not 1 <= item["candidate_count"] <= 1961 or not isinstance(item["min_c60"], int) or not isinstance(item["max_c60"], int) or item["min_c60"] > item["max_c60"] or not isinstance(item["sensitive"], bool) or item["sensitive"] != (item["max_c60"] - item["min_c60"] >= 6) for item in sensitivity) or {item["world"] for item in sensitivity} != set(range(8))):
            raise BExploreContractError("N7 treatment-blind sensitivity schema/world binding differs")
        activity = row.get("direct_residual_activity", ())
        if len(activity) != (48 if direct else 0) or row.get("direct_residual_activity_status") != ("OBSERVED_DIRECT_ABLATION" if direct else "NOT_APPLICABLE_MAPR") or len(row.get("endpoints", ())) != 8 or len(row.get("shadow_receipts", ())) != 1:
            raise BExploreContractError("learned diagnostic/endpoint/receipt inventory differs")
        expected_receipt_id = f"{config.namespace}/{row['cell']}/{row['checkpoint']}/{row['arm']}"
        if not isinstance(row["shadow_receipts"][0], Mapping) or row["shadow_receipts"][0].get("batch_id") != expected_receipt_id:
            raise BExploreContractError("learned paired receipt local owner/address differs")
        activity_keys = {"boundary", "world_row", "total_variation", "physical_command_change", "status"}
        if direct and (any(not isinstance(item, Mapping) or set(item) != activity_keys or item.get("status") != "OBSERVED_DIRECT_ABLATION" or not isinstance(item.get("boundary"), int) or not isinstance(item.get("world_row"), int) or not _finite_number(item.get("total_variation")) or not 0 <= item["total_variation"] <= 1 or not isinstance(item.get("physical_command_change"), bool) for item in activity) or {(item["boundary"], item["world_row"]) for item in activity} != {(boundary, world) for boundary in range(6) for world in range(8)}):
            raise BExploreContractError("DIRECT residual activity schema/address/value differs")
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
        checker_rows = row.get("checker_rows", ())
        if row.get("comparison_status") not in ("IDENTIFIED", "NONIDENTIFIED") or len(checker_rows) != 48 or len(row.get("endpoints", ())) != 8 or len(row.get("shadow_receipts", ())) != 1:
            raise BExploreContractError("BCRH checker/endpoint/receipt inventory differs")
        if not isinstance(row["shadow_receipts"][0], Mapping) or row["shadow_receipts"][0].get("batch_id") != f"{config.namespace}/{row['cell']}/BCRH":
            raise BExploreContractError("BCRH paired receipt local owner/address differs")
        checker_keys = {"candidate_count", "scorer_command", "checker_command", "scorer_checker_equal", "independent_enumerator_equal", "post60_reduced", "floor", "releases", "objective_limbs", "checker_objective_limbs", "candidate_digest", "checker_digest"}
        for item in checker_rows:
            if not isinstance(item, Mapping) or set(item) != checker_keys or not isinstance(item["candidate_count"], int) or not 1 <= item["candidate_count"] <= 1961 or any(not isinstance(item[field], bool) for field in ("scorer_checker_equal", "independent_enumerator_equal", "post60_reduced")) or any(not isinstance(item[field], int) or isinstance(item[field], bool) or item[field] < 0 for field in ("releases", "candidate_digest", "checker_digest")):
                raise BExploreContractError("BCRH checker row schema/value differs")
            if any(not isinstance(item[field], Sequence) or len(item[field]) != length or any(value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0) for value in item[field]) for field, length in (("scorer_command", 4), ("checker_command", 4), ("objective_limbs", 4), ("checker_objective_limbs", 4))):
                raise BExploreContractError("BCRH checker command/objective limb schema differs")
            floor = item["floor"]
            if not isinstance(floor, Sequence) or len(floor) != 2 or any(not isinstance(value, int) or isinstance(value, bool) for value in floor) or floor[1] <= 0:
                raise BExploreContractError("BCRH checker floor schema differs")
        identified = all(item["scorer_checker_equal"] and item["independent_enumerator_equal"] and item["scorer_command"] == item["checker_command"] and item["objective_limbs"] == item["checker_objective_limbs"] and item["candidate_digest"] == item["checker_digest"] for item in checker_rows)
        if row.get("comparison_status") != ("IDENTIFIED" if identified else "NONIDENTIFIED"):
            raise BExploreContractError("BCRH checker agreement/status differs")
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
        "checkpoint_artifact", "ps_b0_artifact", "ps_b0_host_call_ledger", "host_call_ledger", "source_identity",
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
    source_identity = terminal.get("source_identity")
    if terminal.get("shadow_influenced_actions") is not False or terminal.get("source_pre_digest") != terminal.get("source_post_digest") or not isinstance(source_identity, Mapping) or terminal.get("source_pre_digest") != _canonical_digest(source_identity):
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
    if set(batch_ids) != _expected_shadow_batch_ids(config):
        raise BExploreContractError("actual B shadow batch identity inventory differs")
    expected_paired_ledger = _aggregate_host_call_ledger(shadow_receipts)
    if expected_paired_ledger["operations"] != _expected_paired_host_operations(config):
        raise BExploreContractError("stage-exact paired host-call operations differ")
    outer_primary = source_identity.get("native_artifact"); outer_shadow = source_identity.get("shadow_native_artifact")
    if not isinstance(outer_primary, Mapping) or not isinstance(outer_shadow, Mapping): raise BExploreContractError("outer source/native identity differs")
    for receipt in shadow_receipts:
        snapshot = receipt["paired_receipt"]["source_pre"]
        if snapshot["primary_artifact_path"] != outer_primary.get("path") or snapshot["primary_artifact_sha256"] != outer_primary.get("sha256") or snapshot["primary_registered_build_key"] != outer_primary.get("build_key") or snapshot["shadow_artifact_path"] != outer_shadow.get("artifact_path") or snapshot["shadow_artifact_sha256"] != outer_shadow.get("artifact_sha256") or snapshot["shadow_build_key"] != outer_shadow.get("build_key") or snapshot["included_source_identity"] != outer_shadow.get("source_identity"):
            raise BExploreContractError("paired source/native identity does not bind outer source fence")
    ps_ledger = terminal.get("ps_b0_host_call_ledger")
    if terminal.get("host_call_ledger") != _combined_host_call_ledger(config, expected_paired_ledger, ps_ledger if isinstance(ps_ledger, Mapping) else None):
        raise BExploreContractError("aggregate operation-resolved host-call ledger differs")
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
    ps_artifact = terminal.get("ps_b0_artifact")
    if not isinstance(ps_artifact, Mapping) or ps_artifact.get("schema") != "VNFC_BPCR_BEXP_R01_PS_B0_ARTIFACT_IDENTITY_V1" or ps_artifact.get("comparisons") != 288 or ps_artifact.get("primary_only_host_calls") != 24:
        raise BExploreContractError("PS-B0 DEBUG artifact binding is absent")


def _canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _stable_shadow_identity(identity: Mapping[str, object]) -> dict[str, object]:
    required = {"build_key", "artifact_path", "artifact_sha256", "artifact_size", "source_identity", "registered_r09_artifact_path", "registered_r09_artifact_sha256", "registered_r09_build_key"}
    if not required <= set(identity):
        raise BExploreContractError("B shadow artifact identity fields are incomplete")
    return {key: identity[key] for key in sorted(required)}


def build_shadow_receipt(batch_id: str, paired_receipt: Mapping[str, object], final_shadow_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Bind the CLEAN paired-seam receipt to eight retained recovery rows."""
    rows = tuple(final_shadow_rows)
    if len(rows) != 8 or any(set(row) != {"interactive", "tick_rows", "receipt"} for row in rows):
        raise BExploreContractError("CLEAN paired final shadow rows differ")
    receipt = {"schema": SHADOW_SCHEMA, "batch_id": batch_id, "paired_receipt": dict(paired_receipt), "episode_recovery": tuple(dict(row["receipt"]) for row in rows), "shadow_influenced_actions": False}
    validate_shadow_receipt(receipt)
    return receipt


def _validate_paired_source_snapshot(source: object) -> Mapping[str, object]:
    keys = {"included_source_identity", "shadow_build_key", "shadow_embedded_build_key", "shadow_artifact_path", "shadow_artifact_sha256", "primary_artifact_path", "primary_artifact_sha256", "primary_registered_build_key"}
    if not isinstance(source, Mapping) or set(source) != keys:
        raise BExploreContractError("paired source/artifact identity schema differs")
    included = source["included_source_identity"]
    included_keys = {"b_adapter_source_sha256", "included_r09_header_sha256", "transitive_r09_checker_sha256", "registered_r09_source_sha256"}
    if not isinstance(included, Mapping) or set(included) != included_keys or any(not _is_sha256(included[key]) for key in included_keys):
        raise BExploreContractError("paired included-source identity differs")
    for key in ("shadow_build_key", "shadow_embedded_build_key", "shadow_artifact_sha256", "primary_artifact_sha256", "primary_registered_build_key"):
        if not _is_sha256(source[key]): raise BExploreContractError("paired source/artifact digest differs")
    if source["shadow_build_key"] != source["shadow_embedded_build_key"]:
        raise BExploreContractError("paired shadow embedded build binding differs")
    for key in ("shadow_artifact_path", "primary_artifact_path"):
        if not isinstance(source[key], str) or not Path(source[key]).is_absolute(): raise BExploreContractError("paired artifact path is not absolute")
    return source


def _canonical_shadow_batch_kind(batch_id: object) -> str:
    if not isinstance(batch_id, str): raise BExploreContractError("paired shadow batch identity differs")
    parts = batch_id.split("/")
    if len(parts) < 5 or parts[0] != RUN_REVISION or parts[1] not in (DEBUG_STAGE, PRIMARY_STAGE, OPTIONAL_STAGE) or not parts[2].isdigit():
        raise BExploreContractError("paired shadow batch identity is not canonical")
    suffix = parts[3:]
    if len(suffix) == 4 and suffix[0] == "TRAIN" and suffix[1] in ARMS and suffix[2].startswith("u") and suffix[2][1:].isdigit() and suffix[3] in ("N3", "N5"):
        return "training"
    if len(suffix) == 3 and suffix[0] in {f"N{n}z{zone}" for n in ROSTERS for zone in ZONES} and suffix[1] in CHECKPOINTS and suffix[2] in ARMS:
        return "learned"
    if len(suffix) == 2 and suffix[0] in ("N7z1", "N7z2") and suffix[1] == "BCRH": return "bcrh"
    raise BExploreContractError("paired shadow batch identity is not canonical")


def validate_shadow_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    if set(receipt) != {"schema", "batch_id", "paired_receipt", "episode_recovery", "shadow_influenced_actions"} or receipt.get("schema") != SHADOW_SCHEMA:
        raise BExploreContractError("paired shadow wrapper receipt schema differs")
    batch_kind = _canonical_shadow_batch_kind(receipt.get("batch_id"))
    if receipt.get("shadow_influenced_actions") is not False:
        raise BExploreContractError("paired shadow batch identity/authority differs")
    paired = receipt.get("paired_receipt")
    paired_keys = {"schema", "input_digest", "action_digest", "width", "main_return_source", "shadow_role", "authority", "host_call_ledger", "initial", "source_pre", "source_post", "boundaries", "incomplete", "last_failure"}
    if not isinstance(paired, Mapping) or set(paired) != paired_keys or paired.get("schema") != "VNFC-BEXP-PAIRED-PRIMARY-SHADOW-RECEIPT-v1" or paired.get("width") != 8:
        raise BExploreContractError("CLEAN paired primary/shadow receipt fields differ")
    authority = {"scientific_trajectory_source": "registered_r09_native_interactive_primary", "action_source": "single_paired_caller_command_forwarded_unchanged", "scientific_return_source": "registered_r09_native_interactive_primary", "shadow_effect": "read_only_deterministic_replay_telemetry"}
    if paired.get("main_return_source") != "registered_r09_native_interactive_primary" or paired.get("shadow_role") != "telemetry_only_no_action_or_return_authority" or paired.get("authority") != authority or paired.get("source_pre") != paired.get("source_post") or paired.get("incomplete") is not False or paired.get("last_failure") is not None:
        raise BExploreContractError("paired primary-return/shadow-source authority differs")
    _validate_paired_source_snapshot(paired.get("source_pre"))
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
    from experiments.candidates.variable_n_fleet_churn_b_explore import expected_host_call_inventory
    batch_id = str(receipt["batch_id"])
    expected_ledger = expected_host_call_inventory(paired_steps=6, primary_sensitivity_calls=1 if batch_kind == "learned" and "/N7z" in batch_id else 0, primary_bcrh_calls=6 if batch_kind == "bcrh" else 0)
    if paired.get("host_call_ledger") != expected_ledger:
        raise BExploreContractError("operation-resolved paired host-call ledger differs")
    recovery = receipt.get("episode_recovery")
    recovery_keys = {"observation_scope", "primary_rollout_applicability", "first_failed_zone_service_time_seconds", "failed_zone_executor_reacquisition_time_seconds", "failed_zone_zero_service_seconds_0_60", "observed_failed_zone_seconds_0_60", "complete_0_60", "raw_tick_rows"}
    if not isinstance(recovery, Sequence) or len(recovery) != 8 or any(not isinstance(row, Mapping) or set(row) != recovery_keys or row.get("observation_scope") != "fresh_b_shadow_direct" for row in recovery):
        raise BExploreContractError("paired recovery telemetry rows differ")
    from experiments.candidates.variable_n_fleet_churn_b_explore import derive_recovery_telemetry
    tick_keys = {"post_loss_second", "tick_end_second", "integrated_ticks", "zone1_delivery", "zone2_delivery", "failed_zone_delivery", "failed_zone_executor_state_before", "failed_zone_executor_rank_before", "failed_zone_executor_acquisition_elapsed_before", "failed_zone_executor_state_after", "failed_zone_executor_rank_after", "failed_zone_executor_acquisition_elapsed_after", "acquisition_transition"}
    for row in recovery:
        ticks = row["raw_tick_rows"]
        if not isinstance(ticks, Sequence) or len(ticks) != 120 or any(not isinstance(tick, Mapping) or set(tick) != tick_keys for tick in ticks):
            raise BExploreContractError("raw recovery tick inventory/schema differs")
        early = [int(tick["post_loss_second"]) for tick in ticks if 0 <= int(tick["post_loss_second"]) < 60]
        if sorted(early) != list(range(60)) or any(int(tick["tick_end_second"]) != int(tick["post_loss_second"]) + 1 or int(tick["integrated_ticks"]) <= 0 or any(int(tick[field]) < 0 for field in ("zone1_delivery", "zone2_delivery", "failed_zone_delivery", "failed_zone_executor_acquisition_elapsed_before", "failed_zone_executor_acquisition_elapsed_after")) for tick in ticks):
            raise BExploreContractError("raw recovery tick second/domain validity differs")
        derived = derive_recovery_telemetry(ticks)
        if _canonical_digest(derived) != _canonical_digest(row):
            raise BExploreContractError("retained recovery telemetry does not exactly rederive from raw ticks")
    return {"status": "EQUIVALENT_PAIRED_BATCH_OBSERVED", "main_return_source": paired["main_return_source"], "host_call_ledger": paired["host_call_ledger"]}


def _aggregate_host_call_ledger(receipts: Sequence[Mapping[str, object]]) -> dict[str, object]:
    operations = {"primary_reset": 0, "primary_step": 0, "primary_sensitivity": 0, "primary_bcrh": 0, "shadow_reset": 0, "shadow_step": 0, "paired_successful_step": 0}
    for receipt in receipts:
        validate_shadow_receipt(receipt)
        ledger = receipt["paired_receipt"]["host_call_ledger"]  # type: ignore[index]
        operations["primary_reset"] += ledger["primary"]["reset"]  # type: ignore[index,operator]
        operations["primary_step"] += ledger["primary"]["step"]  # type: ignore[index,operator]
        operations["primary_sensitivity"] += ledger["primary"]["sensitivity"]  # type: ignore[index,operator]
        operations["primary_bcrh"] += ledger["primary"]["bcrh"]  # type: ignore[index,operator]
        operations["shadow_reset"] += ledger["shadow"]["reset"]  # type: ignore[index,operator]
        operations["shadow_step"] += ledger["shadow"]["step"]  # type: ignore[index,operator]
        operations["paired_successful_step"] += ledger["paired"]["step"]  # type: ignore[index,operator]
    primary_total = sum(operations[key] for key in ("primary_reset", "primary_step", "primary_sensitivity", "primary_bcrh"))
    shadow_total = sum(operations[key] for key in ("shadow_reset", "shadow_step"))
    return {"schema": "VNFC_BPCR_BEXP_R01_AGGREGATE_HOST_CALL_LEDGER_V1", "batches": len(receipts), "operations": operations, "primary_total": primary_total, "shadow_total": shadow_total, "paired_step_exact": operations["primary_step"] == operations["shadow_step"] == operations["paired_successful_step"]}


def _expected_shadow_batch_ids(config: BExploreRunConfig) -> frozenset[str]:
    training = {f"{config.namespace}/TRAIN/{arm}/u{update}/N{n}" for arm in ARMS for update in range(config.updates) for n in (3, 5)}
    checkpoints = ("final",) if config.stage == DEBUG_STAGE else CHECKPOINTS
    learned = {f"{config.namespace}/N{n}z{zone}/{checkpoint}/{arm}" for n in ROSTERS for zone in ZONES for checkpoint in checkpoints for arm in ARMS}
    bcrh = {f"{config.namespace}/N7z{zone}/BCRH" for zone in ZONES}
    return frozenset(training | learned | bcrh)


def _expected_paired_host_operations(config: BExploreRunConfig) -> dict[str, int]:
    batches = len(_expected_shadow_batch_ids(config))
    return {"primary_reset": batches, "primary_step": 6 * batches, "primary_sensitivity": 4 if config.stage == DEBUG_STAGE else 8, "primary_bcrh": 12, "shadow_reset": batches, "shadow_step": 6 * batches, "paired_successful_step": 6 * batches}


def _validate_ps_b0_host_call_ledger(ledger: Mapping[str, object]) -> None:
    required = {"schema", "records", "primary_only_host_calls", "reset_calls", "bcrh_calls", "step_calls", "batch_widths", "scientific_values_exposed"}
    if set(ledger) != required or ledger.get("schema") != "VNFC_BPCR_BEXP_R01_PS_B0_PRIMARY_HOST_CALL_LEDGER_V1" or ledger.get("primary_only_host_calls") != 24 or ledger.get("reset_calls") != 12 or ledger.get("bcrh_calls") != 6 or ledger.get("step_calls") != 6 or tuple(ledger.get("batch_widths", ())) != (8,) or ledger.get("scientific_values_exposed") is not False:
        raise BExploreContractError("PS-B0 primary-only host-call ledger differs")
    records = ledger.get("records"); keys = {"ordinal", "roster_size", "failed_zone", "state_family", "operation", "batch_width", "unique_presentation_surfaces", "duplicates_per_surface", "duplicate_exact_required", "primary_only", "result_bearing"}
    if not isinstance(records, Sequence) or len(records) != 24 or any(not isinstance(row, Mapping) or set(row) != keys for row in records):
        raise BExploreContractError("PS-B0 primary-only host-call records differ")
    if [row["ordinal"] for row in records] != list(range(1, 25)) or any(row["batch_width"] != 8 or row["unique_presentation_surfaces"] != 4 or row["duplicates_per_surface"] != 2 or row["duplicate_exact_required"] is not True or row["primary_only"] is not True or row["result_bearing"] is not False for row in records):
        raise BExploreContractError("PS-B0 B8 duplicate host-call facts differ")
    actual = {(row["roster_size"], row["failed_zone"], row["state_family"], row["operation"]) for row in records}
    expected = {(n, zone, "t0_and_later", operation) for n in ROSTERS for zone in ZONES for operation in ("reset", "bcrh", "step")} | {(n, zone, "diagnostic", "reset") for n in ROSTERS for zone in ZONES}
    if actual != expected:
        raise BExploreContractError("PS-B0 host-call cell/family/operation inventory differs")


def _combined_host_call_ledger(config: BExploreRunConfig, paired: Mapping[str, object], ps_b0: Mapping[str, object] | None) -> dict[str, object]:
    ps_calls = 0
    if config.stage == DEBUG_STAGE:
        if not isinstance(ps_b0, Mapping):
            raise BExploreContractError("PS-B0 primary-only host-call ledger is absent")
        _validate_ps_b0_host_call_ledger(ps_b0)
        ps_calls = 24
    return {"schema": "VNFC_BPCR_BEXP_R01_COMBINED_HOST_CALL_LEDGER_V1", "paired_primary_shadow": dict(paired), "ps_b0_primary_only": dict(ps_b0) if config.stage == DEBUG_STAGE else None, "primary_total": int(paired["primary_total"]) + ps_calls, "shadow_total": int(paired["shadow_total"]), "ps_b0_included_in_paired_receipts": False}


def _exact_readiness_plan(config: BExploreRunConfig) -> dict[str, object]:
    config.validate(); counts = expected_counts(config)
    conditions = (
        {"condition": "fresh_4gib_preflight", "status": "REQUIRED_AT_ENTRY", "satisfied": False, "evidence": None},
        {"condition": "implementation_ready", "status": "READY_CM_CLEAN", "satisfied": IMPLEMENTATION_READY, "evidence": "independent A-G, thin-CLI, and load-only binding reviews CLEAN; 102 non-result tests passed"},
        {"condition": "source_bound_ps_b0_actual_path_adapter", "status": "READY", "satisfied": True, "evidence": "experiments.candidates.variable_n_fleet_churn_b_explore.ActualPathPSB0Adapter"},
        {"condition": "process_tree_telemetry_sink_api", "status": "READY_PENDING_RUN_MEASUREMENT", "satisfied": True, "evidence": "experiments.candidates.variable_n_fleet_churn_b_explore.process_telemetry.ProcessTreeTelemetrySink"},
        {"condition": "measured_external_process_telemetry", "status": "REPAIR_REQUIRED", "satisfied": False, "evidence": None},
        {"condition": "paired_shadow_boundary_and_source_equivalence", "status": "REQUIRED_DURING_RUNTIME", "satisfied": False, "evidence": None},
        {"condition": "create_once_started_transaction", "status": "REQUIRED_AFTER_ADMISSION_BEFORE_ACTIVITY", "satisfied": False, "evidence": None},
        {"condition": "archived_valid_debug_gate", "status": "NOT_APPLICABLE" if config.stage == DEBUG_STAGE else "REQUIRED_BEFORE_PRIMARY_OR_OPTIONAL", "satisfied": config.stage == DEBUG_STAGE, "evidence": None},
    )
    return {
        "schema": "VNFC_BPCR_BEXP_R01_READINESS_PLAN_V1", "run_revision": RUN_REVISION,
        "implementation_ready": IMPLEMENTATION_READY, "implementation_blocker": IMPLEMENTATION_BLOCKER,
        "readiness_conditions": conditions,
        "namespace": config.namespace, "config": asdict(config),
        "seed_master": {key: value for key, value in derive_seed_master(config).items() if key != "master"},
        "counts": counts, "evaluation": evaluation_plan(config),
        "ps_b0": {"state_descriptors": ps_b0_state_descriptors(), "presentations": PRESENTATIONS, "checkpoints": CHECKPOINTS, "arms": ARMS, "comparisons": 288, "comparisons_are_rollouts": False},
        "bcrh_precheck": {"corners": 8, "high_demand": True, "include_candidate_records": False, "candidate_ceiling": 1961},
        "checkpoint_retention": {"initial": True, "final": True, "storage_disjoint": True, "durable_create_once_bundle": "CHECKPOINTS.bin", "manifest": "CHECKPOINTS_MANIFEST.json", "no_selection": True},
        "named_output": {
            "mode": "three_artifact_create_once",
            "scientific_body": "RESULT_BODY.json",
            "observer_telemetry": "TELEMETRY_TERMINAL.json",
            "valid_claim": "VALID_CLAIM.json",
            "legacy_result_and_outcome_claim": "FORBIDDEN",
            "incomplete": "INCOMPLETE.json",
            "checkpoint_bundle": "CHECKPOINTS.bin",
            "old_c_frontier": False,
        },
        "execution_topology": {
            "mode": "SERIAL_NO_CHILD_PROCESSES",
            "torch_threads": 1,
            "native_artifacts": "prebuilt_and_frozen_before_monitor_start",
            "descendant_processes": "INCOMPLETE",
        },
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
            "host_call_cost": "operation-resolved ledger: paired reset/step plus primary-only sensitivity and BCRH calls; external telemetry must bind exact primary and shadow totals",
        },
        "telemetry_schema": TELEMETRY_SCHEMA, "required_telemetry_fields": tuple(sorted(REQUIRED_TELEMETRY_FIELDS)),
        "performance_disposition": "PILOT_ONLY_PENDING_MEASURED_DEBUG", "runtime_ready": False,
        "repair_required": {
            "missing_adapter": None,
            "remaining": "obtain one admitted measured DEBUG execution before any PRIMARY/OPTIONAL result",
            "required_semantics": "construct an actual-path state where null is legal, at least two agent candidates are legal, opaque deterministic tie ranks are complete, and co-permuted rows/legal/fixed/opaque fields preserve identical legal physical support; no equal-logit state is claimed",
        },
    }


def named_output_directory(output_root: Path, config: BExploreRunConfig) -> Path:
    config.validate()
    root = Path(output_root).resolve()
    return root / RUN_REVISION / config.stage / str(config.seed)


def _source_bytes_identity() -> dict[str, object]:
    repo = Path(__file__).resolve().parents[1]; files = []
    for relative in _ACTUAL_SOURCE_PATHS:
        path = repo / relative
        if not path.is_file():
            raise BExploreContractError(f"actual source input is absent: {relative}")
        files.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"mode": "current_checkout_actual_bytes_pre_native", "files": tuple(files), "digest": _canonical_digest(files)}


def _create_once_json(path: Path, payload: Mapping[str, object]) -> Path:
    path = Path(path)
    recorder = _ACTIVE_DURABLE_RECORDER.get()
    if recorder is not None:
        durable_root = Path(getattr(recorder, "durable_root")).resolve()
        try:
            relative = path.resolve().relative_to(durable_root)
        except ValueError as error:
            raise BExploreContractError("durable create-once target escapes the monitored namespace") from error
        incomplete_reason = _ACTIVE_INCOMPLETE_REASON.get()
        observe = getattr(recorder, "observe_incomplete_create_once" if incomplete_reason is not None else "observe_create_once", None)
        if not callable(observe):
            raise BExploreContractError("exact durable create-once recorder API is absent")
        context = observe(relative, reason=incomplete_reason) if incomplete_reason is not None else observe(relative)
        with context as authorized:
            if Path(authorized).resolve() != path.resolve():
                raise BExploreContractError("durable recorder target identity differs")
            token = _ACTIVE_DURABLE_RECORDER.set(None)
            try:
                return _create_once_json(Path(authorized), payload)
            finally:
                _ACTIVE_DURABLE_RECORDER.reset(token)
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
        raise
    return path


def _create_once_bytes(path: Path, payload: bytes) -> Path:
    path = Path(path)
    recorder = _ACTIVE_DURABLE_RECORDER.get()
    if recorder is not None:
        durable_root = Path(getattr(recorder, "durable_root")).resolve()
        try:
            relative = path.resolve().relative_to(durable_root)
        except ValueError as error:
            raise BExploreContractError("durable create-once target escapes the monitored namespace") from error
        incomplete_reason = _ACTIVE_INCOMPLETE_REASON.get()
        observe = getattr(recorder, "observe_incomplete_create_once" if incomplete_reason is not None else "observe_create_once", None)
        if not callable(observe):
            raise BExploreContractError("exact durable create-once recorder API is absent")
        context = observe(relative, reason=incomplete_reason) if incomplete_reason is not None else observe(relative)
        with context as authorized:
            if Path(authorized).resolve() != path.resolve():
                raise BExploreContractError("durable recorder target identity differs")
            token = _ACTIVE_DURABLE_RECORDER.set(None)
            try:
                return _create_once_bytes(Path(authorized), payload)
            finally:
                _ACTIVE_DURABLE_RECORDER.reset(token)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise BExploreContractError(f"named BEXP output already exists: {path.name}") from error
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    except BaseException:
        raise
    return path


def _create_started_manifest_once(output_root: Path, config: BExploreRunConfig, *, source: Mapping[str, object], memory: Mapping[str, object], now: datetime) -> Path:
    payload = {"schema": "VNFC_BPCR_BEXP_R01_STARTED_V1", "run_revision": RUN_REVISION, "namespace": config.namespace, "stage": config.stage, "seed": config.seed, "started_at": now.astimezone(timezone.utc).isoformat(), "source": dict(source), "memory_admission": dict(memory), "terminal": False}
    return _create_once_json(named_output_directory(output_root, config) / "STARTED.json", payload)


def _validate_started_manifest(directory: Path, config: BExploreRunConfig) -> Mapping[str, object]:
    path = Path(directory) / "STARTED.json"
    if not path.is_file():
        raise BExploreContractError("create-once STARTED manifest is absent")
    payload = json.loads(path.read_text("ascii"))
    if not isinstance(payload, Mapping) or payload.get("schema") != "VNFC_BPCR_BEXP_R01_STARTED_V1" or payload.get("run_revision") != RUN_REVISION or payload.get("namespace") != config.namespace or payload.get("stage") != config.stage or payload.get("seed") != config.seed or payload.get("terminal") is not False:
        raise BExploreContractError("STARTED manifest schema/identity differs")
    return payload


def _quarantine_checkpoint_bytes(checkpoints: Mapping[str, object]) -> tuple[bytes, dict[str, object]]:
    payload = bytearray(b"VNFC-BEXP-QUARANTINE-CHECKPOINTS-v1\0"); contents = []
    for arm in sorted(checkpoints):
        arm_rows = checkpoints[arm]
        if not isinstance(arm_rows, Mapping):
            continue
        for label in sorted(arm_rows):
            checkpoint = arm_rows[label]
            state = checkpoint.get("state") if isinstance(checkpoint, Mapping) else None
            if not isinstance(state, Mapping):
                continue
            for name in sorted(state):
                tensor = state[name]
                if not isinstance(tensor, torch.Tensor):
                    continue
                array = tensor.detach().cpu().contiguous().numpy(); raw = array.tobytes(order="C")
                header_value = {"arm": arm, "checkpoint": label, "name": name, "dtype": str(array.dtype), "shape": list(array.shape), "bytes": len(raw)}
                header = json.dumps(header_value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
                payload.extend(len(header).to_bytes(8, "big")); payload.extend(header); payload.extend(len(raw).to_bytes(8, "big")); payload.extend(raw)
                contents.append({**header_value, "sha256": hashlib.sha256(raw).hexdigest()})
    return bytes(payload), {"schema": "VNFC_BPCR_BEXP_R01_QUARANTINE_CHECKPOINTS_V1", "contents": contents, "quarantine_only": True, "resume_allowed": False, "evaluation_allowed": False, "publication_allowed": False}


def _preserve_quarantine_checkpoints_once(directory: Path, checkpoints: Mapping[str, object]) -> tuple[Path, Path] | None:
    bundle, manifest = _quarantine_checkpoint_bytes(checkpoints)
    if not manifest["contents"]:
        return None
    bundle_path = _create_once_bytes(Path(directory) / "QUARANTINE_CHECKPOINTS.bin", bundle)
    manifest = {**manifest, "bundle_filename": bundle_path.name, "bundle_sha256": hashlib.sha256(bundle).hexdigest(), "bundle_size": len(bundle)}
    manifest_path = _create_once_json(Path(directory) / "QUARANTINE_CHECKPOINTS_MANIFEST.json", manifest)
    return bundle_path, manifest_path


def _artifact_hashes(directory: Path) -> tuple[dict[str, object], ...]:
    return tuple({"filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size": path.stat().st_size} for path in sorted(Path(directory).iterdir()) if path.is_file() and path.name != "INCOMPLETE.json")


def _quarantine_incomplete_once(output_root: Path, config: BExploreRunConfig, *, source: Mapping[str, object], execution_state: Mapping[str, object], error: BaseException) -> Path:
    directory = named_output_directory(output_root, config)
    reason = f"runner_exception:{type(error).__name__}:{error}"
    recorder = _ACTIVE_DURABLE_RECORDER.get()
    if recorder is not None:
        mark = getattr(recorder, "mark_incomplete", None)
        if not callable(mark): raise BExploreContractError("INCOMPLETE recorder transition API is absent")
        mark(reason)
    incomplete_token = _ACTIVE_INCOMPLETE_REASON.set(reason)
    checkpoint_error = None
    try:
        checkpoints = execution_state.get("checkpoints")
        if isinstance(checkpoints, Mapping):
            try:
                _preserve_quarantine_checkpoints_once(directory, checkpoints)
            except BaseException as preserve_error:
                checkpoint_error = {"type": type(preserve_error).__name__, "message": str(preserve_error)}
        payload = {"schema": "VNFC_BPCR_BEXP_R01_QUARANTINED_INCOMPLETE_V1", "run_revision": RUN_REVISION, "namespace": config.namespace, "stage": config.stage, "source": dict(source), "exception": {"type": type(error).__name__, "message": str(error)}, "execution_flags": {key: bool(execution_state.get(key, False)) for key in ("rng_created", "model_created", "native_phase_entered", "checkpoint_created")}, "partial_artifacts": _artifact_hashes(directory), "checkpoint_preservation_error": checkpoint_error, "quarantine_only": True, "resume_allowed": False, "evaluation_allowed": False, "publication_allowed": False, "scientific_result": False, "status": "INCOMPLETE"}
        return _create_once_json(directory / "INCOMPLETE.json", payload)
    finally:
        _ACTIVE_INCOMPLETE_REASON.reset(incomplete_token)


def _observer_incomplete_once(
    publication_root: Path,
    config: BExploreRunConfig,
    *,
    scientific_body: Mapping[str, object],
    scientific_seal: Mapping[str, object],
    failure_stage: str,
    error: BaseException,
) -> Path:
    """Invalidate a post-seal observer transaction without mutating science."""
    if failure_stage not in {"publish", "verify", "emit"}:
        raise BExploreContractError("observer failure stage differs")
    root = Path(publication_root).resolve(); root.mkdir(parents=True, exist_ok=True)
    partial = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "OBSERVER_INCOMPLETE.json":
            payload = path.read_bytes()
            partial.append({"filename": path.name, "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    payload = {
        "schema": "VNFC_BPCR_BEXP_R01_OBSERVER_INCOMPLETE_V1",
        "namespace": config.namespace,
        "status": "OBSERVER_INCOMPLETE",
        "failure_stage": failure_stage,
        "exception": {"type": type(error).__name__, "message": str(error)},
        "scientific_body": dict(scientific_body),
        "scientific_storage_seal": dict(scientific_seal),
        "scientific_storage_seal_sha256": _canonical_digest(scientific_seal),
        "partial_publication_artifacts": tuple(partial),
        "valid_claim_usable": False,
        "observer_emit_completed": False,
        "scientific_result": False,
        "quarantine_only": True,
    }
    return _create_once_json(root / "OBSERVER_INCOMPLETE.json", payload)


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
    manifest_path = _create_once_json(directory / "CHECKPOINTS_MANIFEST.json", manifest)
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


def _serialize_ps_b0_artifact_once(output_root: Path, config: BExploreRunConfig, comparisons: Sequence[object], host_call_ledger: Mapping[str, object]) -> dict[str, object]:
    if config.stage != DEBUG_STAGE or len(comparisons) != 288:
        raise BExploreContractError("PS-B0 artifact belongs to exact DEBUG 288-comparison inventory")
    rows = tuple(row.to_dict() if callable(getattr(row, "to_dict", None)) else asdict(row) for row in comparisons)
    for row in rows:
        diagnostic = row.get("score_probability_difference_diagnostics")
        decoder = diagnostic.get("deterministic_decoder") if isinstance(diagnostic, Mapping) else None
        if not isinstance(decoder, Mapping) or decoder.get("schema") != "VNFC_BPCR_BEXP_R01_PS_B0_ALIGNED_SCORE_PROBABILITY_DIFF_V1" or decoder.get("alignment") != "physical_token_then_physical_candidate_rank" or decoder.get("physical_command_equal") is not True or len(decoder.get("tokens", ())) != 4:
            raise BExploreContractError("PS-B0 aligned score/probability diagnostics differ")
        try:
            maximum = float.fromhex(str(decoder["maximum_absolute_probability_difference_binary64"]))
        except (KeyError, TypeError, ValueError) as error:
            raise BExploreContractError("PS-B0 probability-difference diagnostic is invalid") from error
        if not math.isfinite(maximum) or maximum < 0:
            raise BExploreContractError("PS-B0 probability-difference diagnostic is nonfinite")
        for token in decoder["tokens"]:
            if not isinstance(token, Mapping) or not isinstance(token.get("physical_token"), int) or token["physical_token"] not in range(4) or not isinstance(token.get("candidates_by_physical_rank"), Sequence) or any(candidate.get("support_equal") is not True or candidate.get("opaque_tie_rank_equal") is not True for candidate in token["candidates_by_physical_rank"]):
                raise BExploreContractError("PS-B0 physical-token/candidate alignment differs")
        diagnostic_state = row.get("state_kind") == "diagnostic_null_tie"
        if diagnostic_state != (diagnostic.get("diagnostic_support_semantics") == "actual_state_predecision_target_token") or (diagnostic_state and (row.get("diagnostic_target_physical_token") not in range(4) or not isinstance(row.get("predecision_legal_agent_count"), int) or row["predecision_legal_agent_count"] < 2)) or (not diagnostic_state and row.get("diagnostic_target_physical_token") is not None):
            raise BExploreContractError("PS-B0 diagnostic predecision fields differ")
    _combined_host_call_ledger(config, {"primary_total": 0, "shadow_total": 0}, host_call_ledger)
    payload = {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_ARTIFACT_V1", "namespace": config.namespace, "comparisons": rows, "summary": validate_ps_b0(comparisons), "host_call_ledger": dict(host_call_ledger)}
    path = _create_once_json(named_output_directory(output_root, config) / "PS_B0.json", payload)
    return {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_ARTIFACT_IDENTITY_V1", "namespace": config.namespace, "filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "comparisons": 288, "primary_only_host_calls": 24}


def _serialize_result_body_once(output_root: Path, config: BExploreRunConfig, terminal: Mapping[str, object]) -> dict[str, object]:
    validate_runtime_terminal(config, terminal)
    payload = {"schema": "VNFC_BPCR_BEXP_R01_RESULT_BODY_V1", "namespace": config.namespace, "source_digest": terminal["source_pre_digest"], "runtime_terminal_sha256": _canonical_digest(terminal), "runtime_terminal": dict(terminal), "expected_observer_sidecars": {"telemetry_schema": "VNFC_BPCR_BEXP_R01_TELEMETRY_TERMINAL_V1", "telemetry_filename": "TELEMETRY_TERMINAL.json", "claim_schema": "VNFC_BPCR_BEXP_R01_VALID_CLAIM_V1", "claim_filename": "VALID_CLAIM.json"}, "scientific_result_body_complete": True}
    path = _create_once_json(named_output_directory(output_root, config) / "RESULT_BODY.json", payload)
    return {"schema": "VNFC_BPCR_BEXP_R01_RESULT_BODY_IDENTITY_V1", "namespace": config.namespace, "filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size_bytes": path.stat().st_size, "runtime_terminal_sha256": payload["runtime_terminal_sha256"]}


def _finite_binary64(value: object, *, allow_none: bool = False) -> float | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str):
        raise BExploreContractError("PS-B0 binary64 diagnostic is not a hex string")
    try:
        number = float.fromhex(value)
    except ValueError as error:
        raise BExploreContractError("PS-B0 binary64 diagnostic is invalid") from error
    if not math.isfinite(number) or number.hex() != value:
        raise BExploreContractError("PS-B0 binary64 diagnostic is noncanonical/nonfinite")
    return number


def _validate_serialized_ps_b0_rows(rows: Sequence[object]) -> dict[str, object]:
    from experiments.candidates.variable_n_fleet_churn_b_explore.ps_b0 import PSB0ActualComparison, expected_addresses
    expected_fields = set(PSB0ActualComparison.__dataclass_fields__)
    if len(rows) != 288 or any(not isinstance(row, Mapping) or set(row) != expected_fields for row in rows):
        raise BExploreContractError("PS-B0 serialized row schema/cardinality differs")
    addresses = {(row["roster_size"], row["failed_zone"], row["state_kind"], row["presentation"], row["checkpoint"], row["arm"]) for row in rows}  # type: ignore[index]
    if addresses != expected_addresses():
        raise BExploreContractError("PS-B0 serialized address inventory differs")
    projected = []
    identity_by_checkpoint_arm: dict[tuple[object, object], object] = {}
    source_identity: object | None = None
    structural_fields = ("agent_rows_copermuted", "legal_masks_copermuted", "fixed_occupants_copermuted", "opaque_ranks_copermuted", "physical_support_equal", "opaque_deterministic_tie_ranks_complete")
    score_fields = ("base_logit_binary64", "prefix_conditioned_logit_binary64", "masked_logit_binary64", "probability_binary64")
    for row in rows:
        if any(row[field] is not True for field in structural_fields) or row["equal_logit_claim"] is not False or row["canonical_physical_command"] != row["inverse_mapped_physical_command"]:
            raise BExploreContractError("PS-B0 serialized structural/presentation semantics differ")
        if len(row["canonical_physical_command"]) != 4 or any(value is not None and (isinstance(value, bool) or not isinstance(value, int)) for value in row["canonical_physical_command"]):
            raise BExploreContractError("PS-B0 serialized physical command differs")
        state_key = (row["roster_size"], row["failed_zone"], row["state_kind"])
        if {candidate["presentation"] for candidate in rows if (candidate["roster_size"], candidate["failed_zone"], candidate["state_kind"]) == state_key} != set(PRESENTATIONS):
            raise BExploreContractError("PS-B0 state lacks four unique active presentations")
        diagnostic_state = row["state_kind"] == "diagnostic_null_tie"
        if diagnostic_state:
            if row["null_case_present"] is not True or row["null_action_legal"] is not True or row["legal_agent_candidate_count"] < 2 or row["diagnostic_target_physical_token"] not in range(4) or row["predecision_legal_agent_count"] < 2:
                raise BExploreContractError("PS-B0 serialized diagnostic support-path coverage differs")
        elif row["diagnostic_target_physical_token"] is not None or row["predecision_legal_agent_count"] != 0:
            raise BExploreContractError("PS-B0 non-diagnostic row contains diagnostic fields")
        if row["state_kind"] == "later_fixed_or_acquiring" and row["fixed_or_acquiring_case_present"] is not True:
            raise BExploreContractError("PS-B0 serialized later-state coverage differs")
        diagnostics = row["copermutation_diagnostics"]
        diagnostic_keys = {"agent_rows_by_physical_rank", "legal_masks_by_physical_rank", "fixed_occupants_physical", "opaque_ranks_by_physical_rank", "prefix_conditioned_physical_support", "diagnostic_predecision_target_support"}
        if not isinstance(diagnostics, Mapping) or set(diagnostics) != {"canonical", "tested"} or any(not isinstance(diagnostics[side], Mapping) or set(diagnostics[side]) != diagnostic_keys for side in ("canonical", "tested")) or diagnostics["canonical"] != diagnostics["tested"]:
            raise BExploreContractError("PS-B0 serialized co-permutation diagnostics differ")
        score = row["score_probability_difference_diagnostics"]
        if not isinstance(score, Mapping) or set(score) != {"deterministic_decoder", "diagnostic_support_semantics"} or (score["diagnostic_support_semantics"] == "actual_state_predecision_target_token") != diagnostic_state:
            raise BExploreContractError("PS-B0 serialized diagnostic support binding differs")
        decoder = score["deterministic_decoder"]
        if not isinstance(decoder, Mapping) or set(decoder) != {"schema", "alignment", "tokens", "maximum_absolute_probability_difference_binary64", "physical_command_equal"} or decoder["schema"] != "VNFC_BPCR_BEXP_R01_PS_B0_ALIGNED_SCORE_PROBABILITY_DIFF_V1" or decoder["alignment"] != "physical_token_then_physical_candidate_rank" or decoder["physical_command_equal"] is not True:
            raise BExploreContractError("PS-B0 aligned score/probability schema differs")
        tokens = decoder["tokens"]
        if not isinstance(tokens, Sequence) or len(tokens) != 4 or {token["physical_token"] for token in tokens if isinstance(token, Mapping)} != set(range(4)):
            raise BExploreContractError("PS-B0 aligned physical-token inventory differs")
        canonical_trace = row["canonical_trace"]; tested_trace = row["tested_trace"]
        if not isinstance(canonical_trace, Mapping) or not isinstance(tested_trace, Mapping):
            raise BExploreContractError("PS-B0 trace diagnostics are absent")
        trace_keys = {"origin", "native_epoch", "native_token_state", "native_token_elapsed", "fixed_physical_occupants_model_order", "tokens", "forward_command_rows", "inverse_mapped_physical_command", "forward_verified_exact", "forcing"} | ({"diagnostic_predecision_support"} if diagnostic_state else set())
        if set(canonical_trace) != trace_keys or set(tested_trace) != trace_keys or canonical_trace.get("forward_verified_exact") is not True or tested_trace.get("forward_verified_exact") is not True or canonical_trace.get("forcing") != "deterministic_opaque_tie_decoder" or tested_trace.get("forcing") != "deterministic_opaque_tie_decoder" or canonical_trace.get("inverse_mapped_physical_command") != row["canonical_physical_command"] or tested_trace.get("inverse_mapped_physical_command") != row["inverse_mapped_physical_command"]:
            raise BExploreContractError("PS-B0 trace schema/physical-command binding differs")
        canonical_tokens = {token["physical_token"]: token for token in canonical_trace.get("tokens", ())}
        tested_tokens = {token["physical_token"]: token for token in tested_trace.get("tokens", ())}
        trace_token_keys = {"model_token", "physical_token", "prefix_physical_choices", "candidates", "selected_physical_rank"}
        trace_candidate_keys = {"physical_rank", "available_before", "environment_legal", "masked_support", "base_logit_binary64", "prefix_conditioned_logit_binary64", "masked_logit_binary64", "probability_binary64", "opaque_tie_rank"}
        if set(canonical_tokens) != set(range(4)) or set(tested_tokens) != set(range(4)) or any(set(token) != trace_token_keys or any(set(candidate) != trace_candidate_keys for candidate in token["candidates"]) for token in (*canonical_tokens.values(), *tested_tokens.values())):
            raise BExploreContractError("PS-B0 trace token/candidate schema differs")
        maximum = 0.0
        for token in tokens:
            if not isinstance(token, Mapping) or set(token) != {"physical_token", "canonical_prefix_physical_choices", "tested_prefix_physical_choices", "candidates_by_physical_rank"}:
                raise BExploreContractError("PS-B0 aligned token schema differs")
            physical_token = token["physical_token"]
            canonical_candidates = {candidate["physical_rank"]: candidate for candidate in canonical_tokens.get(physical_token, {}).get("candidates", ())}
            tested_candidates = {candidate["physical_rank"]: candidate for candidate in tested_tokens.get(physical_token, {}).get("candidates", ())}
            candidates = token["candidates_by_physical_rank"]
            if not isinstance(candidates, Sequence) or not candidates or {candidate["physical_rank"] for candidate in candidates} != set(canonical_candidates) or set(canonical_candidates) != set(tested_candidates):
                raise BExploreContractError("PS-B0 aligned candidate inventory differs")
            for candidate in candidates:
                if not isinstance(candidate, Mapping) or set(candidate) != {"physical_rank", "canonical", "tested", "differences", "support_equal", "opaque_tie_rank_equal"} or candidate["support_equal"] is not True or candidate["opaque_tie_rank_equal"] is not True:
                    raise BExploreContractError("PS-B0 aligned candidate schema/support differs")
                rank = candidate["physical_rank"]
                expected_left = {field: canonical_candidates[rank][field] for field in score_fields}; expected_right = {field: tested_candidates[rank][field] for field in score_fields}
                if candidate["canonical"] != expected_left or candidate["tested"] != expected_right:
                    raise BExploreContractError("PS-B0 aligned candidate does not bind serialized traces")
                expected_difference_keys = {field.replace("_binary64", "_difference_binary64") for field in score_fields}
                if not isinstance(candidate["differences"], Mapping) or set(candidate["differences"]) != expected_difference_keys:
                    raise BExploreContractError("PS-B0 aligned difference inventory differs")
                for field in score_fields:
                    left = _finite_binary64(expected_left[field], allow_none=True); right = _finite_binary64(expected_right[field], allow_none=True)
                    difference = candidate["differences"][field.replace("_binary64", "_difference_binary64")]
                    if left is None or right is None:
                        if difference is not None or left is not right:
                            raise BExploreContractError("PS-B0 aligned support/difference differs")
                    else:
                        observed = _finite_binary64(difference)
                        if observed != right - left:
                            raise BExploreContractError("PS-B0 aligned numeric difference differs")
                        if field == "probability_binary64": maximum = max(maximum, abs(observed))
        if _finite_binary64(decoder["maximum_absolute_probability_difference_binary64"]) != maximum:
            raise BExploreContractError("PS-B0 maximum probability difference differs")
        identity_key = (row["checkpoint"], row["arm"]); identity = row["model_identity"]
        if not isinstance(identity, Mapping) or set(identity) != {"arm", "class", "state_sha256", "tensors"} or identity.get("arm") != row["arm"] or not _is_sha256(identity.get("state_sha256")) or not isinstance(identity.get("tensors"), Sequence):
            raise BExploreContractError("PS-B0 model identity differs")
        if identity_key in identity_by_checkpoint_arm and identity_by_checkpoint_arm[identity_key] != identity:
            raise BExploreContractError("PS-B0 model identity drifted across presentations/states")
        identity_by_checkpoint_arm[identity_key] = identity
        if source_identity is not None and row["source_identity"] != source_identity:
            raise BExploreContractError("PS-B0 source identity drifted across comparisons")
        source_identity = row["source_identity"]
        projected.append(PSB0Comparison(
            row["roster_size"], row["failed_zone"], row["state_kind"], row["presentation"], row["checkpoint"], row["arm"],
            row["agent_rows_copermuted"], row["legal_masks_copermuted"], row["fixed_occupants_copermuted"], row["opaque_ranks_copermuted"], row["physical_support_equal"],
            tuple(row["canonical_physical_command"]), tuple(row["inverse_mapped_physical_command"]), row["null_case_present"], row["fixed_or_acquiring_case_present"], row["null_action_legal"], row["legal_agent_candidate_count"], row["opaque_deterministic_tie_ranks_complete"],
        ))
    return validate_ps_b0(tuple(projected))


def _validate_ps_b0_artifact(directory: Path, config: BExploreRunConfig, identity: Mapping[str, object]) -> None:
    required = {"schema", "namespace", "filename", "sha256", "comparisons", "primary_only_host_calls"}
    if set(identity) != required or identity.get("schema") != "VNFC_BPCR_BEXP_R01_PS_B0_ARTIFACT_IDENTITY_V1" or identity.get("namespace") != config.namespace or identity.get("filename") != "PS_B0.json" or identity.get("comparisons") != 288 or identity.get("primary_only_host_calls") != 24 or not _is_sha256(identity.get("sha256")):
        raise BExploreContractError("PS-B0 artifact identity differs")
    path = Path(directory) / "PS_B0.json"
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != identity["sha256"]:
        raise BExploreContractError("PS-B0 create-once artifact is absent or drifted")
    payload = json.loads(path.read_text("ascii"))
    if payload.get("schema") != "VNFC_BPCR_BEXP_R01_PS_B0_ARTIFACT_V1" or payload.get("namespace") != config.namespace or payload.get("host_call_ledger", {}).get("primary_only_host_calls") != 24:
        raise BExploreContractError("PS-B0 artifact content differs")
    _validate_ps_b0_host_call_ledger(payload["host_call_ledger"])
    recomputed = _validate_serialized_ps_b0_rows(payload.get("comparisons", ()))
    if payload.get("summary") != recomputed:
        raise BExploreContractError("PS-B0 serialized summary differs from recomputation")


def _serialize_readiness_plan_once(
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


def validate_debug_gate_receipt(receipt: Mapping[str, object], *, source_identity_digest: str) -> None:
    required = {"schema", "run_revision", "debug_seed", "source_identity_digest", "ps_b0_result", "bcrh_result", "performance_telemetry", "result_artifact", "checkpoint_artifact", "ps_b0_artifact", "common_host_valid", "valid"}
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
    artifact_keys = {
        "result_body_filename", "result_body_sha256", "result_body_size_bytes",
        "telemetry_filename", "telemetry_sha256", "telemetry_size_bytes",
        "valid_claim_filename", "valid_claim_sha256",
    }
    if (
        not isinstance(result_artifact, Mapping)
        or set(result_artifact) != artifact_keys
        or result_artifact.get("result_body_filename") != "RESULT_BODY.json"
        or result_artifact.get("telemetry_filename") != "TELEMETRY_TERMINAL.json"
        or result_artifact.get("valid_claim_filename") != "VALID_CLAIM.json"
        or any(not _is_sha256(result_artifact.get(key)) for key in ("result_body_sha256", "telemetry_sha256", "valid_claim_sha256"))
        or any(isinstance(result_artifact.get(key), bool) or not isinstance(result_artifact.get(key), int) or result_artifact[key] <= 0 for key in ("result_body_size_bytes", "telemetry_size_bytes"))
    ):
        raise BExploreContractError("archived DEBUG three-artifact binding differs")
    checkpoint_artifact = receipt.get("checkpoint_artifact")
    if not isinstance(checkpoint_artifact, Mapping) or checkpoint_artifact.get("namespace") != BExploreRunConfig(DEBUG_STAGE, DEBUG_SEED, 8).namespace:
        raise BExploreContractError("archived DEBUG checkpoint artifact binding differs")
    ps_artifact = receipt.get("ps_b0_artifact")
    if not isinstance(ps_artifact, Mapping) or ps_artifact.get("namespace") != BExploreRunConfig(DEBUG_STAGE, DEBUG_SEED, 8).namespace or ps_artifact.get("comparisons") != 288 or ps_artifact.get("primary_only_host_calls") != 24:
        raise BExploreContractError("archived DEBUG PS-B0 artifact binding differs")


def build_debug_gate_receipt(
    debug_valid_claim_path: Path,
    *,
    debug_scientific_root: Path,
    source_identity_digest: str,
    preflight_receipt: Mapping[str, object],
    now: datetime,
) -> dict[str, object]:
    """Build a gate only from an archived canonical DEBUG three-artifact bundle."""
    _implementation_hard_fence(preflight_receipt, now=now)
    debug_config = BExploreRunConfig(DEBUG_STAGE, DEBUG_SEED, 8)
    claim_path = Path(debug_valid_claim_path).resolve()
    scientific_root = Path(debug_scientific_root).resolve()
    if claim_path.name != "VALID_CLAIM.json" or tuple(scientific_root.parts[-3:]) != (RUN_REVISION, DEBUG_STAGE, str(DEBUG_SEED)):
        raise BExploreContractError("DEBUG gate inputs are not the exact canonical claim/scientific namespace")
    telemetry_path = claim_path.parent / "TELEMETRY_TERMINAL.json"
    result_path = scientific_root / "RESULT_BODY.json"
    publication_files = {path.name for path in claim_path.parent.iterdir() if path.is_file()} if claim_path.parent.is_dir() else set()
    if publication_files != {"TELEMETRY_TERMINAL.json", "VALID_CLAIM.json"} or not result_path.is_file():
        raise BExploreContractError("archived DEBUG three-artifact bundle is absent")
    claim = json.loads(claim_path.read_text("utf-8"))
    telemetry_document = json.loads(telemetry_path.read_text("utf-8"))
    payload = json.loads(result_path.read_text("utf-8"))
    claim_keys = {
        "schema", "namespace", "scientific_body_relative_path", "scientific_body_size_bytes",
        "scientific_body_sha256", "scientific_storage_seal_sha256", "telemetry_relative_path",
        "telemetry_size_bytes", "telemetry_sha256",
    }
    if not isinstance(claim, Mapping) or set(claim) != claim_keys or claim.get("schema") != "VNFC_BPCR_BEXP_R01_VALID_CLAIM_V1" or claim.get("namespace") != debug_config.namespace:
        raise BExploreContractError("archived DEBUG VALID_CLAIM schema/namespace differs")
    result_bytes = result_path.read_bytes(); telemetry_bytes = telemetry_path.read_bytes()
    if claim.get("scientific_body_relative_path") != "RESULT_BODY.json" or claim.get("scientific_body_size_bytes") != len(result_bytes) or claim.get("scientific_body_sha256") != hashlib.sha256(result_bytes).hexdigest():
        raise BExploreContractError("archived DEBUG VALID_CLAIM RESULT_BODY binding differs")
    if claim.get("telemetry_relative_path") != "TELEMETRY_TERMINAL.json" or claim.get("telemetry_size_bytes") != len(telemetry_bytes) or claim.get("telemetry_sha256") != hashlib.sha256(telemetry_bytes).hexdigest():
        raise BExploreContractError("archived DEBUG VALID_CLAIM telemetry binding differs")
    if not isinstance(telemetry_document, Mapping) or set(telemetry_document) != {"schema", "namespace", "scientific_body", "scientific_storage_seal", "telemetry"} or telemetry_document.get("schema") != "VNFC_BPCR_BEXP_R01_TELEMETRY_TERMINAL_V1" or telemetry_document.get("namespace") != debug_config.namespace:
        raise BExploreContractError("archived DEBUG TELEMETRY_TERMINAL schema/namespace differs")
    body_record = telemetry_document.get("scientific_body")
    expected_body_record = {"relative_path": "RESULT_BODY.json", "size_bytes": len(result_bytes), "sha256": hashlib.sha256(result_bytes).hexdigest()}
    if body_record != expected_body_record:
        raise BExploreContractError("archived DEBUG telemetry reverse RESULT_BODY binding differs")
    storage_seal = telemetry_document.get("scientific_storage_seal")
    if not isinstance(storage_seal, Mapping) or storage_seal.get("valid") is not True or claim.get("scientific_storage_seal_sha256") != _canonical_digest(storage_seal):
        raise BExploreContractError("archived DEBUG scientific storage seal binding differs")
    inventory = storage_seal.get("durable_artifact_inventory")
    if not isinstance(inventory, Sequence) or body_record not in inventory:
        raise BExploreContractError("archived DEBUG RESULT_BODY is absent from scientific inventory")
    expected_scientific_files = {"STARTED.json", "CHECKPOINTS.bin", "CHECKPOINTS_MANIFEST.json", "PS_B0.json", "RESULT_BODY.json"}
    if {row.get("relative_path") for row in inventory if isinstance(row, Mapping)} != expected_scientific_files:
        raise BExploreContractError("archived DEBUG scientific success inventory differs or contains an incomplete/legacy marker")
    actual_scientific_files = {path.relative_to(scientific_root).as_posix() for path in scientific_root.rglob("*") if path.is_file()}
    if actual_scientific_files != expected_scientific_files:
        raise BExploreContractError("archived DEBUG scientific namespace contains an unresolved/incomplete artifact")
    if storage_seal.get("storage_high_water_disposition") != "EXACT_R01_MONOTONIC_CREATE_ONLY" or storage_seal.get("directory_inventory") not in ((), []):
        raise BExploreContractError("archived DEBUG scientific storage disposition differs")
    if storage_seal.get("durable_directory_total_bytes") != sum(int(row["size_bytes"]) for row in inventory):
        raise BExploreContractError("archived DEBUG scientific storage total differs")
    for row in inventory:
        if not isinstance(row, Mapping) or set(row) != {"relative_path", "size_bytes", "sha256"}:
            raise BExploreContractError("archived DEBUG scientific inventory schema differs")
        artifact_path = scientific_root / str(row["relative_path"])
        if not artifact_path.is_file() or artifact_path.stat().st_size != row["size_bytes"] or hashlib.sha256(artifact_path.read_bytes()).hexdigest() != row["sha256"]:
            raise BExploreContractError("archived DEBUG scientific artifact inventory drifted")
    _validate_started_manifest(scientific_root, debug_config)
    if not isinstance(payload, Mapping) or payload.get("schema") != "VNFC_BPCR_BEXP_R01_RESULT_BODY_V1" or payload.get("namespace") != debug_config.namespace or payload.get("scientific_result_body_complete") is not True:
        raise BExploreContractError("archived DEBUG RESULT_BODY is not complete")
    debug_terminal = payload.get("runtime_terminal"); performance_telemetry = telemetry_document.get("telemetry")
    if not isinstance(debug_terminal, Mapping) or not isinstance(performance_telemetry, Mapping):
        raise BExploreContractError("archived DEBUG result/telemetry payload is absent")
    validate_runtime_terminal(debug_config, debug_terminal)
    if payload.get("runtime_terminal_sha256") != _canonical_digest(debug_terminal):
        raise BExploreContractError("archived DEBUG RESULT_BODY runtime binding differs")
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
    validate_checkpoint_artifact(scientific_root, debug_config, checkpoint_artifact)
    ps_artifact = debug_terminal.get("ps_b0_artifact")
    if not isinstance(ps_artifact, Mapping):
        raise BExploreContractError("archived DEBUG PS-B0 artifact is absent")
    _validate_ps_b0_artifact(scientific_root, debug_config, ps_artifact)
    receipt = {"schema": "VNFC_BPCR_BEXP_R01_ARCHIVED_DEBUG_GATE_V1", "run_revision": RUN_REVISION, "debug_seed": DEBUG_SEED, "source_identity_digest": source_identity_digest, "ps_b0_result": dict(ps), "bcrh_result": dict(bcrh), "performance_telemetry": dict(performance_telemetry), "result_artifact": {"result_body_filename": result_path.name, "result_body_sha256": hashlib.sha256(result_bytes).hexdigest(), "result_body_size_bytes": len(result_bytes), "telemetry_filename": telemetry_path.name, "telemetry_sha256": hashlib.sha256(telemetry_bytes).hexdigest(), "telemetry_size_bytes": len(telemetry_bytes), "valid_claim_filename": claim_path.name, "valid_claim_sha256": hashlib.sha256(claim_path.read_bytes()).hexdigest()}, "checkpoint_artifact": dict(checkpoint_artifact), "ps_b0_artifact": dict(ps_artifact), "common_host_valid": bcrh.get("common_host_valid") is True, "valid": ps.get("passed") is True and bcrh.get("common_host_valid") is True}
    validate_debug_gate_receipt(receipt, source_identity_digest=source_identity_digest)
    return receipt


def assess_pretraining_readiness(
    config: BExploreRunConfig, *, preflight_receipt: Mapping[str, object], telemetry_sink: TelemetrySink,
    now: datetime, source_identity_digest: str,
    native_admission: Callable[..., Mapping[str, object]] = require_native_production,
    archived_debug_valid_claim_path: Path | None = None,
    archived_debug_scientific_root: Path | None = None,
) -> dict[str, object]:
    memory = _implementation_hard_fence(preflight_receipt, now=now)
    plan = _exact_readiness_plan(config)
    validate_telemetry_sink(telemetry_sink)
    _require_process_tree_telemetry_sink(telemetry_sink)
    native = dict(native_admission(batch_width=8))
    if config.stage != DEBUG_STAGE:
        if archived_debug_valid_claim_path is None or archived_debug_scientific_root is None:
            return {**plan, "readiness_status": "REPAIR_REQUIRED", "memory": memory, "native": native, "pretraining_ready": False, "performance_blocker": "archived valid DEBUG gate/performance receipt is absent"}
        debug_gate_receipt = build_debug_gate_receipt(archived_debug_valid_claim_path, debug_scientific_root=archived_debug_scientific_root, source_identity_digest=source_identity_digest, preflight_receipt=preflight_receipt, now=now)
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
    comparisons = _construct_ps_b0_actual(config, diagnostic_state_adapter, models_by_checkpoint, rng)
    require_ledger = getattr(diagnostic_state_adapter, "require_complete_host_call_ledger", None)
    if not callable(require_ledger):
        raise BExploreContractError("REPAIR_REQUIRED: PS-B0 complete host-call ledger API is absent")
    ps_host_ledger = require_ledger()
    ps = validate_ps_b0(comparisons); bcrh = validate_bcrh_precheck(_run_bcrh_precheck_actual())
    return {"status": "DEBUG_GATE_PASSED" if bcrh["common_host_valid"] else "REPAIR_REQUIRED", "ps_b0_result": ps, "ps_b0_comparisons": comparisons, "ps_b0_host_call_ledger": ps_host_ledger, "bcrh_result": bcrh, "runtime_ready": bool(bcrh["common_host_valid"])}


def _source_identity() -> dict[str, object]:
    files = _source_bytes_identity()["files"]
    library = require_cpp_batched_backend(); artifact = Path(library._name).resolve()
    from experiments.candidates.variable_n_fleet_churn_b_explore import native_backend as b_native
    binding = b_native.active_prebuilt_load_only_binding()
    if not isinstance(binding, Mapping) or artifact != Path(str(binding["primary_artifact_path"])).resolve(): raise BExploreContractError("load-only native binding is absent or differs from loaded primary")
    shadow_artifact_identity = b_native.native_artifact_identity
    shadow = _stable_shadow_identity(shadow_artifact_identity())
    return {
        "mode": "current_checkout_actual_bytes", "files": tuple(files),
        "native_artifact": {"path": str(artifact), "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(), "size": artifact.stat().st_size, "build_key": binding["r09_build_key"], "source_sha256": native_source_sha256()},
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


def _runtime_terminal(config: BExploreRunConfig, training: Mapping[str, object], evaluation: Mapping[str, object], checkpoints: Mapping[str, object], gate: Mapping[str, object], source_identity: Mapping[str, object], checkpoint_artifact: Mapping[str, object], ps_b0_artifact: Mapping[str, object]) -> dict[str, object]:
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
    paired_host_ledger = _aggregate_host_call_ledger(shadow_receipts)
    ps_host_ledger = gate.get("ps_b0_host_call_ledger") if config.stage == DEBUG_STAGE else None
    terminal = {
        "schema": "VNFC_BPCR_BEXP_R01_RUNTIME_TERMINAL_V1", "namespace": config.namespace,
        "counts": counts, "ps_b0_passed": gate.get("ps_b0_result", {}).get("passed") is True,
        "learned_relabel_mismatch_count": evaluation["relabel_mismatch_count"],
        "common_host_hard_valid": hard_valid, "finite_values": finite_values,
        "initial_final_checkpoints_retained": all(checkpoints[arm][kind]["storage_disjoint"] for arm in ARMS for kind in CHECKPOINTS) and checkpoint_artifact.get("namespace") == config.namespace,
        "n7_controls_frozen_before_open": True, "source_identity": dict(source_identity), "source_pre_digest": _canonical_digest(source_identity), "source_post_digest": _canonical_digest(source_identity),
        "shadow_boundary_exact": True, "shadow_source_stable": True, "shadow_influenced_actions": False,
        "observations_complete": True, "training_observation_rows": counts["training_episodes_total"],
        "individual_world_seed_rows": counts["evaluation_rollouts_total"], "optimization_rows": counts["optimizer_steps_total"],
        "bcrh_comparison_status": bcrh_status, "shadow_receipts": shadow_receipts, "ps_b0_host_call_ledger": ps_host_ledger, "host_call_ledger": _combined_host_call_ledger(config, paired_host_ledger, ps_host_ledger if isinstance(ps_host_ledger, Mapping) else None),
        "training": training, "evaluation": evaluation, "exploratory_readout": _exploratory_readout(config, evaluation), "exposure": exposure,
        "ps_b0_result": gate.get("ps_b0_result"), "bcrh_precheck_result": gate.get("bcrh_result"), "checkpoint_artifact": dict(checkpoint_artifact), "ps_b0_artifact": dict(ps_b0_artifact),
    }
    validate_runtime_terminal(config, terminal)
    return terminal


def _scientific_counters_for_telemetry(terminal: Mapping[str, object]) -> tuple[dict[str, object], dict[str, int]]:
    training = terminal["training"]; exposure = terminal["exposure"]; ledger = terminal["host_call_ledger"]  # type: ignore[assignment]
    parameters = {arm: int(training[arm]["parameter_count"]) for arm in ARMS}  # type: ignore[index]
    forwards = {arm: int(exposure["training"][arm]["action_selection_forward_calls"] + exposure["training"][arm]["optimizer_forward_calls"] + exposure["evaluation"][arm]["policy_forward_calls"] + exposure["evaluation"][arm]["diagnostic_forward_calls"]) for arm in ARMS}  # type: ignore[index,operator]
    backwards = {arm: int(exposure["training"][arm]["backward_calls"]) for arm in ARMS}  # type: ignore[index]
    counts = terminal["counts"]  # type: ignore[assignment]
    counters = {
        "native_integrated_ticks": int(ledger["paired_primary_shadow"]["operations"]["paired_successful_step"]) * 8 * 20,  # type: ignore[index]
        "scientific_work_transitions": int(counts["joint_transitions_total"]) + int(counts["evaluation_rollouts_total"]) * 6,  # type: ignore[index]
        "worker_count": 1, "threads_per_worker": 1,
        "parameter_count_by_arm": parameters, "forward_calls_by_arm": forwards, "backward_calls_by_arm": backwards,
        "flop_exposure_by_arm": {arm: 2 * parameters[arm] * forwards[arm] for arm in ARMS},
    }
    host = {"primary_host_calls": int(ledger["primary_total"]), "shadow_host_calls": int(ledger["shadow_total"])}  # type: ignore[index]
    return counters, host


def _incomplete_counter_floor() -> tuple[dict[str, object], dict[str, int]]:
    """Non-interpretable positive schema floor required by incomplete telemetry."""
    counters = {"native_integrated_ticks": 1, "scientific_work_transitions": 1, "worker_count": 1, "threads_per_worker": 1, "parameter_count_by_arm": {arm: 1 for arm in ARMS}, "forward_calls_by_arm": {arm: 1 for arm in ARMS}, "backward_calls_by_arm": {arm: 1 for arm in ARMS}, "flop_exposure_by_arm": {arm: 1 for arm in ARMS}}
    return counters, {"primary_host_calls": 1, "shadow_host_calls": 1}


def _load_source_bound_diagnostic_adapter() -> object | None:
    """Delayed import of the source-fenced built-in actual-path adapter."""
    from experiments.candidates.variable_n_fleet_churn_b_explore import ActualPathPSB0Adapter
    return ActualPathPSB0Adapter()


def _validate_invocation_roots(config: BExploreRunConfig, *, scratch_root: Path, durable_root: Path, publication_root: Path, telemetry_sink: object) -> Path:
    scratch = Path(scratch_root).resolve(); durable = Path(durable_root).resolve(); publication = Path(publication_root).resolve(); roots = (scratch, durable, publication)
    if len(set(roots)) != 3 or any(left in right.parents or right in left.parents for index, left in enumerate(roots) for right in roots[index + 1:]):
        raise BExploreContractError("scratch/durable/publication roots overlap")
    if Path(getattr(telemetry_sink, "scratch_root", "")).resolve() != scratch or Path(getattr(telemetry_sink, "durable_root", "")).resolve() != durable:
        raise BExploreContractError("telemetry sink scratch/durable roots differ from public runtime roots")
    if tuple(durable.parts[-3:]) != (RUN_REVISION, config.stage, str(config.seed)):
        raise BExploreContractError("durable root must end with RUN_REVISION/stage/seed")
    return durable.parents[2]


def _validate_exact_storage_contract_binding(telemetry_sink: object, source_identity: Mapping[str, object]) -> None:
    contract = getattr(telemetry_sink, "_exact_storage_contract", None)
    primary = source_identity.get("native_artifact"); shadow = source_identity.get("shadow_native_artifact")
    if not isinstance(primary, Mapping) or not isinstance(shadow, Mapping):
        raise BExploreContractError("actual loaded native artifact identity is incomplete")
    expected = {str(Path(primary["path"]).resolve()): primary["sha256"], str(Path(shadow["artifact_path"]).resolve()): shadow["artifact_sha256"]}
    if (
        contract is None
        or dict(getattr(contract, "frozen_native_artifacts", {})) != expected
        or getattr(contract, "scratch_not_shared_with_children_or_loaders", None) is not True
        or getattr(contract, "durable_root_is_new_namespace", None) is not True
        or getattr(contract, "durable_writes_use_create_once_recorder_only", None) is not True
        or getattr(contract, "serial_no_child_processes", None) is not True
        or getattr(contract, "source_stage_loads_frozen_native_without_build", None) is not True
    ):
        raise BExploreContractError("ExactStorageContract is not bound to the actual loaded primary/shadow artifacts")


def _require_prebuilt_serial_native_contract(telemetry_sink: object) -> None:
    """Refuse before monitor start unless both content-keyed DLLs already exist."""
    contract = getattr(telemetry_sink, "_exact_storage_contract", None)
    frozen = dict(getattr(contract, "frozen_native_artifacts", {})) if contract is not None else {}
    expected = _current_prebuilt_native_artifacts()
    if frozen != expected:
        raise BExploreContractError("REPAIR_REQUIRED: ExactStorageContract does not name both current prebuilt native artifacts")


def _current_prebuilt_native_artifacts() -> dict[str, str]:
    """Return the installed filesystem-resolved load-only artifact pair."""
    from experiments.candidates.variable_n_fleet_churn_b_explore import native_backend as b_native
    binding = b_native.active_prebuilt_load_only_binding()
    if not isinstance(binding, Mapping): raise BExploreContractError("REPAIR_REQUIRED: prebuilt load-only binding is not installed")
    return {str(Path(str(binding["primary_artifact_path"])).resolve()): str(binding["primary_artifact_sha256"]), str(Path(str(binding["shadow_artifact_path"])).resolve()): str(binding["shadow_artifact_sha256"])}


def _resolve_and_install_prebuilt_load_only_binding() -> Mapping[str, object]:
    from experiments.candidates.variable_n_fleet_churn_b_explore import native_backend as b_native
    return b_native._install_prebuilt_load_only_binding(b_native.resolve_prebuilt_load_only_binding())


def _require_serial_no_child_runner() -> None:
    """Static runner-side proof for the SERIAL_NO_CHILD_PROCESSES topology."""
    tree = ast.parse(Path(__file__).read_text("utf-8"), filename=str(Path(__file__).resolve()))
    forbidden_import_roots = {"subprocess", "multiprocessing", "concurrent"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name.split(".")[0] in forbidden_import_roots for alias in node.names):
            raise BExploreContractError("REPAIR_REQUIRED: runner imports a child-process surface")
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in forbidden_import_roots:
            raise BExploreContractError("REPAIR_REQUIRED: runner imports a child-process surface")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr.lower() in {"popen", "spawn", "fork", "system", "start_process"}:
            raise BExploreContractError("REPAIR_REQUIRED: runner contains a child-process launch surface")


def _exact_argv_contract(
    config: BExploreRunConfig,
    *,
    preflight_receipt: Path,
    scratch_root: Path,
    durable_root: Path,
    publication_root: Path,
) -> dict[str, object]:
    """Exact executable CLI contract; PRIMARY/OPTIONAL are intentionally absent."""
    config.validate()
    if config.stage != DEBUG_STAGE:
        raise BExploreContractError("CLI V1 exposes only canonical DEBUG")
    common = (
        "--stage", config.stage, "--seed", str(config.seed), "--updates", str(config.updates),
        "--preflight-receipt", str(Path(preflight_receipt)),
        "--scratch-root", str(Path(scratch_root)),
        "--durable-root", str(Path(durable_root)),
        "--publication-root", str(Path(publication_root)),
    )
    readiness_argv = ("{python}", "scripts/run_vnfc_bpcr_b_explore.py", "ps-b0-readiness", "--preflight-receipt", str(Path(preflight_receipt)))
    formal_argv = ("{python}", "scripts/run_vnfc_bpcr_b_explore.py", "debug", *common)
    return {
        "schema": "VNFC_BPCR_BEXP_R01_EXECUTABLE_CLI_V1",
        "draft_only": False,
        "executable": True,
        "standalone_ps_b0_then_debug": False,
        "ps_b0_readiness": {"argv": readiness_argv, "construction_only": True, "non_result": True, "formal_checkpoint_gate": False},
        "formal": {"argv": formal_argv, "posttraining_ps_same_invocation": config.stage == DEBUG_STAGE, "scientific_result_capable_only_after_all_runtime_gates": True},
    }


def _run_after_pretraining_readiness(config: BExploreRunConfig, *, now: datetime, fence: _SourceFence, source_digest: str, diagnostic_state_adapter: object | None, archived_debug_gate_receipt: Mapping[str, object] | None, output_root: Path, telemetry_sink: object | None = None, execution_state: dict[str, object] | None = None) -> dict[str, object]:
        state = {} if execution_state is None else execution_state
        stage = getattr(telemetry_sink, "stage", None)
        if not callable(stage):
            stage = lambda name: nullcontext()
        with stage("training"):
            master = derive_seed_master(config)["master"]; rng = _SeedRNG(master); state["rng_created"] = True  # type: ignore[arg-type]
            learners = _initialize_learners(config, rng, now); state["model_created"] = True; initial_models = {arm: copy.deepcopy(learners["models"][arm]) for arm in ARMS}  # type: ignore[index]
            checkpoints = {arm: {"initial": clone_checkpoint(learners["models"][arm], "initial")} for arm in ARMS}; state["checkpoint_created"] = True; state["checkpoints"] = checkpoints  # type: ignore[index]
            state["native_phase_entered"] = True
            training = _train_learners(config, rng, learners, now)
            for arm in ARMS:
                checkpoints[arm]["final"] = clone_checkpoint(learners["models"][arm], "final")  # type: ignore[index]
                validate_checkpoint_pair(checkpoints[arm]["initial"], checkpoints[arm]["final"])
            models_by_checkpoint = {"initial": initial_models, "final": learners["models"]}  # type: ignore[index]
        with stage("evaluation"):
            if config.stage == DEBUG_STAGE:
                gate = assess_posttraining_debug_gate(config, diagnostic_state_adapter=diagnostic_state_adapter, models_by_checkpoint=models_by_checkpoint, rng=rng)
                if not gate["runtime_ready"]:
                    raise BExploreContractError(f"REPAIR_REQUIRED: {gate.get('missing_adapter', 'post-training DEBUG gate is incomplete')}")
            else:
                if not isinstance(archived_debug_gate_receipt, Mapping):
                    raise BExploreContractError("REPAIR_REQUIRED: archived DEBUG gate receipt is absent")
                gate = {"status": "ARCHIVED_DEBUG_GATE_ACCEPTED", "ps_b0_result": archived_debug_gate_receipt.get("ps_b0_result"), "ps_b0_artifact": archived_debug_gate_receipt.get("ps_b0_artifact"), "bcrh_result": archived_debug_gate_receipt.get("bcrh_result"), "runtime_ready": True}
            token = _freeze_before_n7(config, training, checkpoints, gate)
            evaluation = _execute_evaluation(config, rng, token, models_by_checkpoint, now)
            fence.close()
        with stage("serialization"):
            checkpoint_artifact = _serialize_checkpoint_bundle_once(output_root, config, checkpoints)  # type: ignore[arg-type]
            if config.stage == DEBUG_STAGE:
                ps_b0_artifact = _serialize_ps_b0_artifact_once(output_root, config, gate.get("ps_b0_comparisons", ()), gate.get("ps_b0_host_call_ledger", {}))
            else:
                ps_b0_artifact = gate.get("ps_b0_artifact")
                if not isinstance(ps_b0_artifact, Mapping):
                    raise BExploreContractError("REPAIR_REQUIRED: archived DEBUG PS-B0 artifact binding is absent")
            terminal = _runtime_terminal(config, training, evaluation, checkpoints, gate, fence.identity, checkpoint_artifact, ps_b0_artifact)
            result_body = _serialize_result_body_once(output_root, config, terminal)
            return {"runtime_terminal": terminal, "result_body": result_body}


def run_b_explore_runtime(
    config: BExploreRunConfig, *, preflight_receipt: Mapping[str, object],
    telemetry_sink: TelemetrySink, now: datetime, scratch_root: Path, durable_root: Path, publication_root: Path,
    archived_debug_valid_claim_path: Path | None = None,
    archived_debug_scientific_root: Path | None = None,
) -> dict[str, object]:
    """Run the exact three-root transaction; no caller scientific-semantic seam.

    ``scratch_root``, the exact named ``durable_root``, and the fresh
    ``publication_root`` must be pairwise disjoint.  The scientific root seals
    before the observer root receives canonical TELEMETRY_TERMINAL/VALID_CLAIM.
    """
    memory = _implementation_hard_fence(preflight_receipt, now=now)
    output_root = _validate_invocation_roots(config, scratch_root=scratch_root, durable_root=durable_root, publication_root=publication_root, telemetry_sink=telemetry_sink)
    _require_process_tree_telemetry_sink(telemetry_sink, expected_durable_root=durable_root)
    _require_serial_no_child_runner()
    _require_prebuilt_serial_native_contract(telemetry_sink)
    execution_state: dict[str, object] = {"rng_created": False, "model_created": False, "native_phase_entered": False, "checkpoint_created": False}
    previous_threads: int | None = None; source_for_quarantine: Mapping[str, object] = {"mode": "not_captured"}; started = False; monitor_started = False; scientific_finished = False; recorder_token = None
    observer_stage: str | None = None; scientific_seal: Mapping[str, object] | None = None; result_body: Mapping[str, object] | None = None
    try:
        telemetry_sink.start(); monitor_started = True  # type: ignore[attr-defined]
        if callable(getattr(telemetry_sink, "observe_create_once", None)):
            recorder_token = _ACTIVE_DURABLE_RECORDER.set(telemetry_sink)
        with telemetry_sink.stage("source_binding"):  # type: ignore[attr-defined]
            source_pre_native = _source_bytes_identity(); source_for_quarantine = source_pre_native
            _create_started_manifest_once(output_root, config, source=source_pre_native, memory=memory, now=now); started = True
            previous_threads = torch.get_num_threads(); torch.set_num_threads(1)
            execution_state["native_phase_entered"] = True; fence = _SourceFence.capture(); source_for_quarantine = fence.identity; source_digest = _canonical_digest(fence.identity); _validate_exact_storage_contract_binding(telemetry_sink, fence.identity)
            readiness = assess_pretraining_readiness(config, preflight_receipt=preflight_receipt, telemetry_sink=telemetry_sink, now=now, source_identity_digest=source_digest, native_admission=require_native_production, archived_debug_valid_claim_path=archived_debug_valid_claim_path, archived_debug_scientific_root=archived_debug_scientific_root)
            if not readiness["pretraining_ready"]:
                raise BExploreContractError(f"REPAIR_REQUIRED: {readiness.get('performance_blocker', 'pretraining readiness failed')}")
            adapter = _load_source_bound_diagnostic_adapter() if config.stage == DEBUG_STAGE else None
            if config.stage == DEBUG_STAGE and adapter is None:
                fence.close(); raise BExploreContractError("REPAIR_REQUIRED: source-bound actual-path PS-B0 support-state adapter is absent")
        execution = _run_after_pretraining_readiness(config, now=now, fence=fence, source_digest=source_digest, diagnostic_state_adapter=adapter, archived_debug_gate_receipt=readiness.get("debug_gate_receipt"), output_root=output_root, telemetry_sink=telemetry_sink, execution_state=execution_state)
        terminal = execution["runtime_terminal"]; result_body = execution["result_body"]
        scientific_counters, host_calls = _scientific_counters_for_telemetry(terminal)
        telemetry = telemetry_sink.finish(scientific_counters=scientific_counters, host_call_ledger=host_calls)  # type: ignore[attr-defined]
        scientific_finished = True
        if recorder_token is not None:
            _ACTIVE_DURABLE_RECORDER.reset(recorder_token); recorder_token = None
        validate_telemetry_payload(telemetry); _validate_telemetry_runtime_binding(telemetry, terminal)
        scientific_seal = telemetry_sink.verify_storage_seal()  # type: ignore[attr-defined]
        observer_stage = "publish"
        publication_receipt = telemetry_sink.publish_observer_bundle(publication_root, namespace=config.namespace, scientific_body_relative_path="RESULT_BODY.json", publication_root_is_new_namespace=True)  # type: ignore[attr-defined]
        observer_stage = "verify"
        observer_seal = telemetry_sink.verify_observer_publication()  # type: ignore[attr-defined]
        observer_stage = "emit"
        telemetry_sink.emit(telemetry)
        observer_stage = None
        return {"schema": "VNFC_BPCR_BEXP_R01_EXECUTION_RESULT_V1", "namespace": config.namespace, "runtime_terminal": terminal, "result_body": result_body, "telemetry_terminal": telemetry, "publication_receipt": publication_receipt, "scientific_seal": scientific_seal, "observer_seal": observer_seal, "publication_root": str(Path(publication_root).resolve())}
    except BaseException as error:
        quarantine_error: BaseException | None = None
        if started and not scientific_finished:
            try:
                _quarantine_incomplete_once(output_root, config, source=source_for_quarantine, execution_state=execution_state, error=error)
                incomplete_counters, incomplete_host = _incomplete_counter_floor()
                incomplete_telemetry = telemetry_sink.finish_incomplete(scientific_counters=incomplete_counters, host_call_ledger=incomplete_host)  # type: ignore[attr-defined]
                scientific_finished = True
                if recorder_token is not None:
                    _ACTIVE_DURABLE_RECORDER.reset(recorder_token); recorder_token = None
                telemetry_sink.verify_storage_seal()  # type: ignore[attr-defined]
                telemetry_sink.publish_observer_bundle(publication_root, namespace=config.namespace, scientific_body_relative_path="INCOMPLETE.json", publication_root_is_new_namespace=True)  # type: ignore[attr-defined]
                telemetry_sink.verify_observer_publication()  # type: ignore[attr-defined]
            except BaseException as caught_quarantine_error:
                quarantine_error = caught_quarantine_error
        elif scientific_finished and observer_stage is not None and isinstance(result_body, Mapping) and isinstance(scientific_seal, Mapping):
            try:
                _observer_incomplete_once(publication_root, config, scientific_body=result_body, scientific_seal=scientific_seal, failure_stage=observer_stage, error=error)
            except BaseException as caught_quarantine_error:
                quarantine_error = caught_quarantine_error
        if monitor_started and not scientific_finished:
            try:
                telemetry_sink.abort()  # type: ignore[attr-defined]
            except BaseException as abort_error:
                execution_state["telemetry_abort_error"] = {"type": type(abort_error).__name__, "message": str(abort_error)}
        if quarantine_error is not None and callable(getattr(error, "add_note", None)):
            error.add_note(f"INCOMPLETE quarantine publication failure: {type(quarantine_error).__name__}: {quarantine_error}")
        raise
    finally:
        if recorder_token is not None:
            _ACTIVE_DURABLE_RECORDER.reset(recorder_token)
        if previous_threads is not None:
            torch.set_num_threads(previous_threads)


def _read_json_receipt_once(path: Path) -> tuple[Mapping[str, object], str]:
    raw = Path(path).read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BExploreContractError("preflight receipt is not canonical JSON") from error
    if not isinstance(value, Mapping):
        raise BExploreContractError("preflight receipt JSON root is not an object")
    return value, hashlib.sha256(raw).hexdigest()


def _ps_b0_readiness_receipt(preflight: Mapping[str, object], *, receipt_sha256: str, now: datetime) -> dict[str, object]:
    memory = validate_preflight_receipt(preflight, now=now)
    _require_serial_no_child_runner()
    binding = _resolve_and_install_prebuilt_load_only_binding()
    frozen = _current_prebuilt_native_artifacts()
    source = _source_identity()
    from experiments.candidates.variable_n_fleet_churn_b_explore import ActualPathPSB0Adapter
    adapter = ActualPathPSB0Adapter(); states = []
    for descriptor in ps_b0_state_descriptors():
        state = adapter.build_support_path_state(descriptor, DEBUG_SEED)
        states.append({"roster_size": state.roster_size, "failed_zone": state.failed_zone, "state_kind": state.state_kind, "presentations": tuple(sorted(state.snapshots))})
    ledger = adapter.require_complete_host_call_ledger()
    return {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_READINESS_V1", "construction_only": True, "non_result": True, "formal_checkpoint_gate": False, "scientific_result": False, "preflight_receipt_sha256": receipt_sha256, "memory": memory, "load_only_binding_sha256": _canonical_digest(binding), "source_identity_sha256": _canonical_digest(source), "prebuilt_native_artifacts": frozen, "state_descriptors": tuple(states), "state_count": 18, "host_call_ledger": ledger, "side_effects": ("load prebuilt primary/shadow native libraries in-process", "construct and close in-memory native PS-B0 host states"), "forbidden_effects_observed": {"torch_model_initialization": False, "rng_master": False, "optimizer": False, "checkpoint": False, "durable_root": False, "scientific_root": False, "publication_root": False, "terminal_or_result": False}}


def _canonical_json_line(value: Mapping[str, object]) -> str:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n"


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_vnfc_bpcr_b_explore.py")
    commands = parser.add_subparsers(dest="command", required=True)
    readiness = commands.add_parser("ps-b0-readiness")
    readiness.add_argument("--preflight-receipt", type=Path, required=True)
    debug = commands.add_parser("debug")
    debug.add_argument("--stage", required=True); debug.add_argument("--seed", type=int, required=True); debug.add_argument("--updates", type=int, required=True)
    debug.add_argument("--preflight-receipt", type=Path, required=True); debug.add_argument("--scratch-root", type=Path, required=True); debug.add_argument("--durable-root", type=Path, required=True); debug.add_argument("--publication-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_cli_parser(); args = parser.parse_args(argv)
    if args.command == "debug" and (args.stage, args.seed, args.updates) != (DEBUG_STAGE, DEBUG_SEED, 8):
        parser.error("debug requires exactly --stage B0-DEBUG --seed 2026090101 --updates 8")
    try:
        preflight, preflight_sha = _read_json_receipt_once(args.preflight_receipt)
        now = datetime.now(timezone.utc)
        if args.command == "ps-b0-readiness":
            sys.stdout.write(_canonical_json_line(_ps_b0_readiness_receipt(preflight, receipt_sha256=preflight_sha, now=now))); return 0
        config = BExploreRunConfig(DEBUG_STAGE, DEBUG_SEED, 8); config.validate()
        validate_preflight_receipt(preflight, now=now)
        _resolve_and_install_prebuilt_load_only_binding()
        frozen = _current_prebuilt_native_artifacts()
        from experiments.candidates.variable_n_fleet_churn_b_explore.process_telemetry import ExactStorageContract, ProcessTreeTelemetrySink
        storage = ExactStorageContract(frozen_native_artifacts=frozen, scratch_not_shared_with_children_or_loaders=True, durable_root_is_new_namespace=True, durable_writes_use_create_once_recorder_only=True, serial_no_child_processes=True, source_stage_loads_frozen_native_without_build=True)
        sink = ProcessTreeTelemetrySink(preflight_receipt=preflight, scratch_root=args.scratch_root, durable_root=args.durable_root, exact_storage_contract=storage)
        result = run_b_explore_runtime(config, preflight_receipt=preflight, telemetry_sink=sink, now=now, scratch_root=args.scratch_root, durable_root=args.durable_root, publication_root=args.publication_root)
        sys.stdout.write(_canonical_json_line(result)); return 0
    except (RuntimeError, OSError, ValueError) as error:
        sys.stderr.write(_canonical_json_line({"schema": "VNFC_BPCR_BEXP_R01_CLI_ERROR_V1", "error_type": type(error).__name__, "message": str(error)})); return 2


__all__ = [
    "BExploreContractError", "BExploreRunConfig", "IMPLEMENTATION_BLOCKER", "IMPLEMENTATION_READY",
    "RUN_REVISION", "TELEMETRY_SCHEMA", "assess_pretraining_readiness", "build_debug_gate_receipt",
    "run_b_explore_runtime", "validate_preflight_receipt",
]


if __name__ == "__main__":
    raise SystemExit(main())
