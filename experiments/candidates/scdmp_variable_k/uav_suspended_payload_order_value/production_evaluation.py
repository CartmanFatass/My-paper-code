"""Lease-bound native evaluation and support services for revision 02.

The services in this module are deliberately in-memory collectors.  They do
not publish episode rows, support cells, checkpoints, or partial replicate
packets.  The caller supplies the eventual result root and the runner remains
the sole atomic publisher after both complete panels and inference exist.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

import torch

from .config import FIXTURE_NAMESPACE, HORIZON, MAX_QUERIES, EventOrder, FixtureInput, Regime
from .evaluation import (
    CONTROLLERS,
    REGIMES,
    EpisodeEndpoint,
    aggregate_replicate_endpoints,
)
from .frontier import (
    CheckpointReceipt,
    GlobalCheckpointBarrier,
    LEARNED_ARMS,
    require_global_checkpoint_barrier,
)
from .lease import ActivityPermit, COORDINATE_PLAN_DIGEST
from .model import SCDMPUAVActorCritic, lexicographic_argmax
from .native_backend import NATIVE_ABI_VERSION, reset_native_renewal_batch
from .rng import EmpiricalRNG
from .support import (
    HISTORIES,
    QUOTIENT_REPRESENTATIVES,
    SUPPORT_K,
    SupportActionRow,
    support_metrics,
    support_quotient_certificate,
    support_score,
)


_REGIME_ENUM: Final[dict[str, Regime]] = {
    "fixed-4": Regime.FIXED_4,
    "fixed-10": Regime.FIXED_10,
    "fixed-6": Regime.FIXED_6,
    "fixed-14": Regime.FIXED_14,
    "6-to-14": Regime.SWITCH_6_TO_14,
    "14-to-6": Regime.SWITCH_14_TO_6,
}
_EVENT_ENUM: Final[dict[str, EventOrder]] = {"RG": EventOrder.RG, "GR": EventOrder.GR}


class ProductionEvaluationContractError(RuntimeError):
    """A final-checkpoint, native execution, or atomic-panel contract failed."""


@runtime_checkable
class FinalCheckpointModelLoader(Protocol):
    """Adapter supplied by the future training service.

    The loader must reconstruct the exact technically accepted final model for
    the named receipt.  Evaluation never receives an optimizer or a mutable
    training service.
    """

    def load_final_model(
        self,
        *,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        arm: str,
        checkpoint_receipt: CheckpointReceipt,
    ) -> SCDMPUAVActorCritic: ...


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _require_barrier(
    permit: ActivityPermit,
    barrier: GlobalCheckpointBarrier,
) -> None:
    permit.require_active()
    if NATIVE_ABI_VERSION != 2:
        raise ProductionEvaluationContractError("evaluation requires the exact native ABI v2")
    if permit.coordinate_plan_digest != COORDINATE_PLAN_DIGEST:
        raise ProductionEvaluationContractError("activity permit coordinate binding changed")
    if not isinstance(barrier, GlobalCheckpointBarrier):
        raise ProductionEvaluationContractError("the global checkpoint barrier is absent")
    if (
        barrier.coordinate_digest != COORDINATE_PLAN_DIGEST
        or barrier.coordinate_digest != permit.coordinate_plan_digest
        or barrier.accepted_slots != 54
        or barrier.evaluation_open is not True
        or barrier.partial_inspection_permitted is not False
    ):
        raise ProductionEvaluationContractError("the global 54-checkpoint barrier is not open")
    digest = barrier.checkpoint_inventory_digest
    if not isinstance(digest, str) or len(digest) != 64:
        raise ProductionEvaluationContractError("checkpoint inventory digest is malformed")
    try:
        int(digest, 16)
    except ValueError as error:
        raise ProductionEvaluationContractError("checkpoint inventory digest is malformed") from error


def _receipt_map(
    permit: ActivityPermit,
    barrier: GlobalCheckpointBarrier,
    receipts: Sequence[CheckpointReceipt],
) -> dict[tuple[int, str], CheckpointReceipt]:
    _require_barrier(permit, barrier)
    # Recompute the barrier before any checkpoint load.  This also validates
    # every digest, slot, final optimizer step, technical acceptance flag, and
    # the prohibition on premature evaluation observation.
    recomputed = require_global_checkpoint_barrier(receipts)
    if recomputed != barrier:
        raise ProductionEvaluationContractError(
            "checkpoint receipts do not reproduce the supplied global barrier"
        )
    mapped = {(receipt.replicate, receipt.arm): receipt for receipt in receipts}
    if len(mapped) != 54:
        raise ProductionEvaluationContractError("checkpoint receipt inventory is not unique")
    return mapped


def _fixture(
    *,
    order: str,
    regime: str,
    switch_tick: int,
    initial_v: float,
    initial_phi: float,
    eta_v: tuple[float, ...],
    eta_omega: tuple[float, ...],
) -> FixtureInput:
    fixture = FixtureInput(
        namespace=FIXTURE_NAMESPACE,
        event_order=_EVENT_ENUM[order],
        regime=_REGIME_ENUM[regime],
        switch_tick=switch_tick,
        initial_v=initial_v,
        initial_phi=initial_phi,
        # The opaque renewal ABI, unlike the construction full-host ABI, never
        # reads this compatibility field.
        actions=(0,) * MAX_QUERIES,
        eta_v=eta_v,
        eta_omega=eta_omega,
    )
    fixture.validate()
    return fixture


def _evaluation_scenario(
    rng: EmpiricalRNG,
    *,
    replicate: int,
    regime: str,
    scenario: int,
    order: str,
    switch_tick: int,
) -> tuple[FixtureInput, str]:
    initial_v = 0.04 * rng.evaluation_state_uniform(replicate, regime, scenario, "v")
    initial_phi = -0.015 + 0.03 * rng.evaluation_state_uniform(
        replicate, regime, scenario, "phi"
    )
    eta_v = tuple(
        -0.004
        if rng.evaluation_disturbance_bit(replicate, regime, scenario, tick, "eta_v") == 0
        else 0.004
        for tick in range(HORIZON)
    )
    eta_omega = tuple(
        -0.006
        if rng.evaluation_disturbance_bit(
            replicate, regime, scenario, tick, "eta_omega"
        ) == 0
        else 0.006
        for tick in range(HORIZON)
    )
    fixture = _fixture(
        order=order,
        regime=regime,
        switch_tick=switch_tick,
        initial_v=initial_v,
        initial_phi=initial_phi,
        eta_v=eta_v,
        eta_omega=eta_omega,
    )
    digest = _canonical_digest(
        {
            "schema": "SCDMP_UAV_SP_R02_EVALUATION_SCENARIO_V1",
            "replicate": replicate,
            "regime": regime,
            "scenario": scenario,
            "order": order,
            "switch_tick": switch_tick,
            "initial_v": initial_v,
            "initial_phi": initial_phi,
            "eta_v": eta_v,
            "eta_omega": eta_omega,
        }
    )
    return fixture, digest


def _model_digest(model: SCDMPUAVActorCritic) -> str:
    digest = hashlib.sha256(b"SCDMP-UAV-SP-R02-FINAL-MODEL-v1\0")
    for name, tensor in model.state_dict().items():
        if not isinstance(tensor, torch.Tensor):
            raise ProductionEvaluationContractError("final model state contains a non-tensor")
        materialized = tensor.detach().cpu().contiguous()
        encoded_name = name.encode("utf-8")
        digest.update(len(encoded_name).to_bytes(4, "big"))
        digest.update(encoded_name)
        digest.update(str(materialized.dtype).encode("ascii"))
        digest.update(json.dumps(tuple(materialized.shape)).encode("ascii"))
        digest.update(materialized.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _require_final_model(model: object, arm: str) -> SCDMPUAVActorCritic:
    if not isinstance(model, SCDMPUAVActorCritic) or model.arm.value != arm:
        raise ProductionEvaluationContractError("checkpoint loader returned a cross-wired model")
    parameters = tuple(model.parameters())
    if not parameters or any(parameter.device.type != "cpu" for parameter in parameters):
        raise ProductionEvaluationContractError("evaluation models must be CPU resident")
    if any(parameter.dtype != torch.float32 for parameter in parameters):
        raise ProductionEvaluationContractError("evaluation models must remain float32")
    if any(not bool(torch.isfinite(parameter).all()) for parameter in parameters):
        raise ProductionEvaluationContractError("evaluation model contains nonfinite weights")
    buffers = tuple(model.buffers())
    if any(buffer.device.type != "cpu" for buffer in buffers):
        raise ProductionEvaluationContractError("evaluation model buffers must be CPU resident")
    if any(not bool(torch.isfinite(buffer).all()) for buffer in buffers):
        raise ProductionEvaluationContractError("evaluation model contains nonfinite buffers")
    model.eval()
    return model


def _action(
    model: SCDMPUAVActorCritic,
    observation: Sequence[float],
    *,
    true_q: float,
) -> int:
    if len(observation) != 14 or not all(math.isfinite(float(value)) for value in observation):
        raise ProductionEvaluationContractError("native renewal observation is malformed")
    with torch.inference_mode():
        observation_tensor = torch.tensor(
            (tuple(float(value) for value in observation),), dtype=torch.float32, device="cpu"
        )
        q_tensor = torch.tensor((true_q,), dtype=torch.float32, device="cpu")
        output = model(observation_tensor, q_tensor)
        if output.logits.shape != (1, 27) or not bool(torch.isfinite(output.logits).all()):
            raise ProductionEvaluationContractError("final actor emitted invalid logits")
        return int(lexicographic_argmax(output.logits).item())


def _run_evaluation_scenario(
    *,
    replicate: int,
    regime: str,
    scenario: int,
    order: str,
    switch_tick: int,
    scenario_digest: str,
    fixture: FixtureInput,
    models: Mapping[str, SCDMPUAVActorCritic],
) -> tuple[EpisodeEndpoint, ...]:
    """Run four paired native episodes; no partial row escapes on failure."""

    if set(models) != set(LEARNED_ARMS):
        raise ProductionEvaluationContractError("evaluation model inventory differs")
    fixtures = tuple(fixture for _ in CONTROLLERS)
    batch, starts = reset_native_renewal_batch(fixtures)
    current = list(starts)
    terminal: list[object | None] = [None] * len(CONTROLLERS)
    try:
        for _renewal in range(MAX_QUERIES):
            active = batch.active
            if not any(active):
                break
            actions: list[int | None] = []
            for index, controller in enumerate(CONTROLLERS):
                if not active[index]:
                    actions.append(None)
                    continue
                true_q = float(current[index].chronology_q)
                if true_q not in (0.0, 1.0):
                    raise ProductionEvaluationContractError("native chronology bit is not binary")
                if controller == "REVERSED":
                    actor = models["TREAT"]
                    actor_q = 1.0 - true_q
                else:
                    actor = models[controller]
                    actor_q = true_q
                actions.append(_action(actor, current[index].public.vector(), true_q=actor_q))
            transitions = batch.advance(actions)
            if len(transitions) != len(CONTROLLERS):
                raise ProductionEvaluationContractError("native renewal batch width changed")
            for index, transition in enumerate(transitions):
                current[index] = transition
                if transition.terminal and terminal[index] is None:
                    terminal[index] = transition
        if any(batch.active) or any(item is None for item in terminal):
            raise ProductionEvaluationContractError("native episode exceeded the 420-tick horizon")
    finally:
        batch.close()

    rows: list[EpisodeEndpoint] = []
    for controller, item in zip(CONTROLLERS, terminal):
        assert item is not None
        accounting = item.accounting
        active_ticks = int(accounting.integrated_ticks)
        mean_effort = float(accounting.mean_active_effort)
        if not math.isfinite(mean_effort):
            raise ProductionEvaluationContractError("native active effort is nonfinite")
        rows.append(
            EpisodeEndpoint(
                replicate=replicate,
                controller=controller,
                regime=regime,
                scenario_index=scenario,
                event_order=order,
                switch_tick=switch_tick,
                scenario_digest=scenario_digest,
                safe_delivery=bool(item.delivery),
                physical_failure=bool(item.physical_failure),
                timeout=bool(item.timeout),
                overload=bool(item.overload),
                swing=bool(item.swing),
                formation=bool(item.formation),
                completion_time_seconds=float(accounting.completion_time_seconds),
                active_effort_sum=mean_effort * active_ticks,
                active_ticks=active_ticks,
                post_absorption_policy_queries=0,
            )
        )
    for row in rows:
        row.validate()
    return tuple(rows)


def _support_state_and_tape(
    rng: EmpiricalRNG,
    *,
    replicate: int,
    k: int,
    state_index: int,
) -> tuple[float, float, tuple[float, ...], tuple[float, ...], str, str]:
    initial_v = 0.04 * rng.support_state_uniform(replicate, k, state_index, "v")
    initial_phi = -0.015 + 0.03 * rng.support_state_uniform(
        replicate, k, state_index, "phi"
    )
    eta_v_short = tuple(
        -0.004
        if rng.support_disturbance_bit(replicate, k, state_index, tick, "eta_v") == 0
        else 0.004
        for tick in range(k)
    )
    eta_omega_short = tuple(
        -0.006
        if rng.support_disturbance_bit(replicate, k, state_index, tick, "eta_omega") == 0
        else 0.006
        for tick in range(k)
    )
    # The native ABI requires a 420-tick allocation, but support advances only
    # once.  Unread suffix values are fixed, not sampled, and cannot influence
    # the one registered interval.
    eta_v = eta_v_short + (-0.004,) * (HORIZON - k)
    eta_omega = eta_omega_short + (-0.006,) * (HORIZON - k)
    public_digest = _canonical_digest(
        {
            "schema": "SCDMP_UAV_SP_R02_SUPPORT_PUBLIC_STATE_V1",
            "replicate": replicate,
            "k": k,
            "state_index": state_index,
            "initial_v": initial_v,
            "initial_phi": initial_phi,
        }
    )
    disturbance_digest = _canonical_digest(
        {
            "schema": "SCDMP_UAV_SP_R02_SUPPORT_DISTURBANCE_V1",
            "replicate": replicate,
            "k": k,
            "state_index": state_index,
            "eta_v": eta_v_short,
            "eta_omega": eta_omega_short,
        }
    )
    return initial_v, initial_phi, eta_v, eta_omega, public_digest, disturbance_digest


def _run_support_cell(
    rng: EmpiricalRNG,
    *,
    replicate: int,
    k: int,
    state_index: int,
) -> tuple[SupportActionRow, ...]:
    """Run exactly ten native candidate intervals for each of two histories."""

    (
        initial_v,
        initial_phi,
        eta_v,
        eta_omega,
        public_digest,
        disturbance_digest,
    ) = _support_state_and_tape(
        rng, replicate=replicate, k=k, state_index=state_index
    )
    regime = "fixed-6" if k == 6 else "fixed-14"
    rows: list[SupportActionRow] = []
    for history in HISTORIES:
        fixture = _fixture(
            order=history,
            regime=regime,
            switch_tick=0,
            initial_v=initial_v,
            initial_phi=initial_phi,
            eta_v=eta_v,
            eta_omega=eta_omega,
        )
        # One history is one boundary.  The batch width is therefore the exact
        # proven 10-representative candidate ceiling, never 20 or 27.
        batch, starts = reset_native_renewal_batch(
            tuple(fixture for _ in QUOTIENT_REPRESENTATIVES)
        )
        try:
            if len(starts) != 10 or batch.batch_width != 10:
                raise ProductionEvaluationContractError("support candidate width differs from ten")
            transitions = batch.advance(QUOTIENT_REPRESENTATIVES)
            if len(transitions) != 10:
                raise ProductionEvaluationContractError("support native interval inventory changed")
        finally:
            batch.close()
        for action_code, transition in zip(QUOTIENT_REPRESENTATIVES, transitions):
            if transition.realized_duration not in range(1, k + 1):
                raise ProductionEvaluationContractError("support interval duration is invalid")
            rows.append(
                SupportActionRow(
                    replicate=replicate,
                    k=k,
                    state_index=state_index,
                    history=history,
                    action_code=action_code,
                    public_state_digest=public_digest,
                    disturbance_digest=disturbance_digest,
                    score=support_score(
                        # RenewalTransition exposes the controller-facing
                        # normalized observation.  J is defined on physical
                        # state, so invert exactly the registered observation
                        # scales before scoring.
                        delta_x=36.0 * float(transition.public.x),
                        k=k,
                        physical_failure=bool(transition.physical_failure),
                        z_end=0.55 * float(transition.public.z),
                        phi_end=0.48 * float(transition.public.phi),
                        f_end=0.42 * float(transition.public.f),
                    ),
                )
            )
    if len(rows) != 20:
        raise AssertionError("one support state must produce exactly 20 representative rows")
    return tuple(rows)


def _require_quotient_certificate() -> Mapping[str, object]:
    certificate = support_quotient_certificate()
    if (
        certificate.get("registered_action_count") != 27
        or certificate.get("representative_count") != 10
        or tuple(certificate.get("representatives", ())) != QUOTIENT_REPRESENTATIVES
        or certificate.get("all_27_actions_covered_once") is not True
        or certificate.get("permutation_invariant_physics_signature") is not True
        or certificate.get("candidate_trajectory_count") != 10
        or certificate.get("maximum_transitions_per_boundary") != 140
        or certificate.get("complexity") != "O(k*10)"
        or certificate.get("nested_replanning") is not False
    ):
        raise ProductionEvaluationContractError("support quotient certificate failed")
    return certificate


class ProductionEvaluationService:
    """Complete evaluation/support collector for use by ``RunnerServices``."""

    def __init__(
        self,
        *,
        result_root: str | Path,
        model_loader: FinalCheckpointModelLoader,
    ) -> None:
        if not isinstance(model_loader, FinalCheckpointModelLoader):
            raise TypeError("model_loader must implement FinalCheckpointModelLoader")
        root = Path(result_root).expanduser().resolve()
        if root.exists() and not root.is_dir():
            raise ProductionEvaluationContractError("caller-supplied result root is not a directory")
        self._result_root = root
        self._model_loader = model_loader

    @property
    def result_root(self) -> Path:
        return self._result_root

    def _load_replicate_models(
        self,
        *,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        receipts: Mapping[tuple[int, str], CheckpointReceipt],
    ) -> dict[str, SCDMPUAVActorCritic]:
        models: dict[str, SCDMPUAVActorCritic] = {}
        for arm in LEARNED_ARMS:
            receipt = receipts[(replicate, arm)]
            receipt.validate()
            if (receipt.replicate, receipt.arm) != (replicate, arm):
                raise ProductionEvaluationContractError("checkpoint loader slot changed")
            model = self._model_loader.load_final_model(
                permit=permit,
                rng=rng,
                replicate=replicate,
                arm=arm,
                checkpoint_receipt=receipt,
            )
            models[arm] = _require_final_model(model, arm)
        return models

    def _evaluate_replicate(
        self,
        *,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        receipts: Mapping[tuple[int, str], CheckpointReceipt],
    ) -> dict[str, object]:
        permit.require_active()
        models = self._load_replicate_models(
            permit=permit, rng=rng, replicate=replicate, receipts=receipts
        )
        before = {arm: _model_digest(model) for arm, model in models.items()}
        rows: list[EpisodeEndpoint] = []
        for regime in REGIMES:
            permit.require_active()
            orders = rng.evaluation_order_roster(replicate, regime)
            switches = (
                rng.evaluation_switch_roster(replicate, regime, orders)
                if regime in ("6-to-14", "14-to-6")
                else (0,) * 120
            )
            for scenario, (order, switch_tick) in enumerate(zip(orders, switches)):
                permit.require_active()
                fixture, digest = _evaluation_scenario(
                    rng,
                    replicate=replicate,
                    regime=regime,
                    scenario=scenario,
                    order=order,
                    switch_tick=switch_tick,
                )
                rows.extend(
                    _run_evaluation_scenario(
                        replicate=replicate,
                        regime=regime,
                        scenario=scenario,
                        order=order,
                        switch_tick=switch_tick,
                        scenario_digest=digest,
                        fixture=fixture,
                        models=models,
                    )
                )
        after = {arm: _model_digest(model) for arm, model in models.items()}
        if after != before:
            raise ProductionEvaluationContractError("evaluation mutated a final checkpoint model")
        controllers = aggregate_replicate_endpoints(rows, replicate=replicate)
        return {"replicate": replicate, "controllers": controllers}

    def evaluate_panel(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        barrier: GlobalCheckpointBarrier,
        checkpoints: Sequence[CheckpointReceipt],
    ) -> Sequence[Mapping[str, object]]:
        receipts = _receipt_map(permit, barrier, checkpoints)
        # Keep all replicate aggregates private until the complete inventory is
        # constructed.  An exception publishes or returns nothing.
        complete = tuple(
            self._evaluate_replicate(
                permit=permit,
                rng=rng,
                replicate=replicate,
                receipts=receipts,
            )
            for replicate in range(18)
        )
        if len(complete) != 18:
            raise AssertionError("evaluation panel must contain 18 replicates")
        return complete

    def _support_replicate(
        self,
        *,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
    ) -> dict[str, object]:
        permit.require_active()
        rows: list[SupportActionRow] = []
        for k in SUPPORT_K:
            for state_index in range(72):
                permit.require_active()
                rows.extend(
                    _run_support_cell(
                        rng,
                        replicate=replicate,
                        k=k,
                        state_index=state_index,
                    )
                )
        metrics = support_metrics(rows, replicate=replicate)
        return {
            "replicate": replicate,
            "support": {
                "Q_order": metrics["Q_order"],
                "D_order": metrics["D_order"],
                "D_action": metrics["D_action"],
            },
        }

    def support_panel(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        barrier: GlobalCheckpointBarrier,
    ) -> Sequence[Mapping[str, object]]:
        _require_barrier(permit, barrier)
        _require_quotient_certificate()
        complete = tuple(
            self._support_replicate(permit=permit, rng=rng, replicate=replicate)
            for replicate in range(18)
        )
        if len(complete) != 18:
            raise AssertionError("support panel must contain 18 replicates")
        return complete


__all__ = [
    "FinalCheckpointModelLoader",
    "ProductionEvaluationContractError",
    "ProductionEvaluationService",
]
