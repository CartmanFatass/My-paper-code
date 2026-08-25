"""Native-only empirical services for the frozen TBCC revision-02 object.

This module is deliberately an adapter rather than an owner.  A caller must
first supply a sealed Root-lease authority, exact empirical bindings and an
external 32-byte master.  Only then can the adapter touch a model, the shared
native guard, or a native session.  The module creates no operating-system
entropy, files, identities, coordinates, checkpoints, or public results.

The training collector requires the ABI-v2 per-hold primitive reward trace.
It never reconstructs a plant transition or reward in Python.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
from typing import Callable, Final, Iterable, Mapping, Protocol, Sequence

import torch

from .artifacts import (
    EmpiricalBindings,
    Stage1bOpportunityExecutionPermit,
    validate_stage1b_opportunity_execution_permit,
)
from .config import (
    COMPONENT,
    FORMATION_ROTATE,
    HOOK_HANDOFF,
    HOST,
    HORIZON_TICKS,
    NATIVE_ABI_VERSION,
)
from .empirical_contract import CARD_REVISION, PANEL_COUNTS, canonical_digest
from .evaluation import (
    CONTROLLERS,
    EPISODES_PER_REGIME,
    REGIMES,
    AcceptedControllerBinding,
    EpisodeEndpoint,
    EvaluationScenario,
)
from .host_types import HostOutput, RenewalLane, ResetLane
from .lease import ActivityPermit
from .lifecycle import validate_opportunity_execution_permit
from .model import (
    FoundationActorCritic,
    LearnedOrderArm,
    OrderActorCritic,
    TiedReversedController,
    clone_frozen_foundation_actor,
    lexicographic_argmax,
)
from .opportunity import (
    DisturbanceTape,
    OpportunityExecutionPermit,
    OpportunityState,
    PairOpportunityMetrics,
    run_complete_pair,
)
from .rng import AddressRNG, for_domain, master_digest, raw_u64, uniform24, uniform53, validate_external_master
from .source_manifest import (
    ACCEPTED_NATIVE_ARTIFACT_SHA256,
    ACCEPTED_NATIVE_BUILD_KEY,
    ACCEPTED_NATIVE_SOURCE_SHA256,
    stable_native_binding,
)
from .training import (
    DurationCorrectPPOTrainer,
    FrozenUpdateBatch,
    TrainingUpdateReceipt,
    freeze_update_batch,
    registered_episode_schedule,
    sample_actions_from_source,
)


SERVICE_SCHEMA: Final[str] = "SCDMP_TBCC_R02_NATIVE_PRODUCTION_SERVICES_V1"
FOUNDATION_TRAINING_WIDTH: Final[int] = 12
ORDER_TRAINING_WIDTH: Final[int] = 12
EVALUATION_WIDTH: Final[int] = 120
OPPORTUNITY_WIDTH: Final[int] = 144
ACCEPTED_SERVICE_WIDTHS: Final[tuple[int, ...]] = (12, 120, 144)
TARGET_K: Final[tuple[int, int]] = (7, 13)
SWITCH_REGIMES: Final[tuple[str, str]] = ("7-to-13", "13-to-7")
_AUTHORITY_SEAL: Final[object] = object()


class ProductionServiceContractError(RuntimeError):
    """A service input or native result differs from the frozen object."""


def _hex(value: object, field: str, *, test_only: bool = False) -> str:
    if test_only:
        prefix = "TEST_ONLY_FAKE_SHA256:"
        if not isinstance(value, str) or not value.startswith(prefix):
            raise ProductionServiceContractError(f"{field} must be explicitly TEST_ONLY")
        tail = value[len(prefix) :]
    else:
        if not isinstance(value, str):
            raise ProductionServiceContractError(f"{field} must be a SHA-256 digest")
        tail = value
    if len(tail) != 64:
        raise ProductionServiceContractError(f"{field} must be a SHA-256 digest")
    try:
        int(tail, 16)
    except ValueError as error:
        raise ProductionServiceContractError(f"{field} must be a SHA-256 digest") from error
    return str(value)


def _fake_digest(label: str) -> str:
    return "TEST_ONLY_FAKE_SHA256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


@dataclass(frozen=True, repr=False)
class ServiceAuthority:
    """Sealed, exact-lineage authority checked before any empirical access."""

    source_manifest_sha256: str
    lineage_digest: str
    coordinate_manifest_sha256: str
    coordinate_proposal_digest: str
    native_binding_sha256: str
    native_source_sha256: str
    native_build_key: str
    native_artifact_sha256: str
    master_sha256: str
    authorization_sha256: str
    test_only: bool
    expires_at: datetime | None
    _seal: object | None = None

    def require(self, *, now: datetime | None = None) -> None:
        if self._seal is not _AUTHORITY_SEAL:
            raise ProductionServiceContractError("sealed service authority is required")
        if self.test_only:
            for field in (
                "source_manifest_sha256",
                "lineage_digest",
                "coordinate_manifest_sha256",
                "coordinate_proposal_digest",
                "native_binding_sha256",
                "master_sha256",
                "authorization_sha256",
            ):
                _hex(getattr(self, field), field, test_only=True)
            if self.expires_at is not None:
                raise ProductionServiceContractError("TEST_ONLY authority cannot carry a live expiry")
        else:
            for field in (
                "source_manifest_sha256",
                "lineage_digest",
                "coordinate_manifest_sha256",
                "coordinate_proposal_digest",
                "native_binding_sha256",
                "master_sha256",
                "authorization_sha256",
            ):
                _hex(getattr(self, field), field)
            if self.expires_at is None:
                raise ProductionServiceContractError("production authority requires lease expiry")
            checked = now if now is not None else datetime.now(self.expires_at.tzinfo)
            if checked.tzinfo is None or checked >= self.expires_at:
                raise ProductionServiceContractError("service authority is expired")
        if (
            self.native_source_sha256 != ACCEPTED_NATIVE_SOURCE_SHA256
            or self.native_build_key != ACCEPTED_NATIVE_BUILD_KEY
            or self.native_artifact_sha256 != ACCEPTED_NATIVE_ARTIFACT_SHA256
        ):
            raise ProductionServiceContractError("service native source/build/artifact binding differs")

    # These methods implement the model/training/evaluation authority protocols.
    def require_model_materialization(
        self, *, card_revision: str, replicate: int, arm: str, initialization_source: object
    ) -> None:
        self.require()
        _require_revision_replicate_arm(card_revision, replicate, arm)
        if initialization_source is None:
            raise ProductionServiceContractError("initialization source is absent")

    def require_foundation_clone(
        self, *, card_revision: str, replicate: int, arm: str, foundation_digest: str
    ) -> None:
        self.require()
        _require_revision_replicate_arm(card_revision, replicate, arm, foundation=False)
        _hex(foundation_digest, "foundation_digest")

    def require_training_update(
        self, *, card_revision: str, replicate: int, arm: str, update: int, schedule: object
    ) -> None:
        self.require()
        _require_revision_replicate_arm(card_revision, replicate, arm)
        if schedule != registered_episode_schedule(arm):
            raise ProductionServiceContractError("training schedule differs from revision 02")
        limit = 160 if arm == "FOUNDATION" else 96
        if isinstance(update, bool) or not isinstance(update, int) or not 1 <= update <= limit:
            raise ProductionServiceContractError("training update is outside the frozen budget")

    def require_checkpoint_restore(
        self, *, card_revision: str, replicate: int, arm: str, completed_updates: int
    ) -> None:
        self.require()
        _require_revision_replicate_arm(card_revision, replicate, arm)
        limit = 160 if arm == "FOUNDATION" else 96
        if isinstance(completed_updates, bool) or not 0 <= completed_updates <= limit:
            raise ProductionServiceContractError("checkpoint frontier is outside the frozen budget")

    def require_evaluation_authority(self, *, stage: str, replicate: int) -> None:
        self.require()
        if stage not in ("foundation-competence", "final") or replicate not in range(24):
            raise ProductionServiceContractError("evaluation stage or replicate differs")


def _require_revision_replicate_arm(
    revision: str, replicate: int, arm: str, *, foundation: bool = True
) -> None:
    allowed = ("FOUNDATION", "TREAT", "FREE", "SET") if foundation else ("TREAT", "FREE", "SET")
    if revision != CARD_REVISION or replicate not in range(24) or arm not in allowed:
        raise ProductionServiceContractError("model/training authority binding differs")


def issue_service_authority(
    *,
    activity_permit: ActivityPermit,
    bindings: EmpiricalBindings,
    native_binding: Mapping[str, object],
    master_sha256: str,
) -> ServiceAuthority:
    """Bind an already-issued Root lease without touching the master or native host."""

    if not isinstance(activity_permit, ActivityPermit):
        raise TypeError("production service authority requires an exact Root activity permit")
    activity_permit.require_active()
    if not isinstance(bindings, EmpiricalBindings) or bindings.test_only:
        raise ProductionServiceContractError("production service requires sealed non-TEST bindings")
    bindings.validate()
    binding_payload = bindings.payload()
    exact_binding_payload = {
        "revision": CARD_REVISION,
        "source_manifest_sha256": bindings.source_manifest_sha256,
        "coordinate_manifest_sha256": bindings.coordinate_manifest_sha256,
        "native_abi": NATIVE_ABI_VERSION,
        "native_source_sha256": ACCEPTED_NATIVE_SOURCE_SHA256,
        "native_build_key": ACCEPTED_NATIVE_BUILD_KEY,
        "native_artifact_sha256": ACCEPTED_NATIVE_ARTIFACT_SHA256,
    }
    if any(binding_payload.get(field) != expected for field, expected in exact_binding_payload.items()):
        raise ProductionServiceContractError("empirical bindings do not cite the accepted ABI/source/artifact")
    stable = stable_native_binding(native_binding)
    native_sha = canonical_digest(stable)
    if (
        activity_permit.source_manifest_sha256 != bindings.source_manifest_sha256
        or activity_permit.native_binding_sha256 != native_sha
        or bindings.coordinate_manifest_sha256 == bindings.source_manifest_sha256
    ):
        raise ProductionServiceContractError("lease/source/native/coordinate lineage differs")
    exact = {
        "component": COMPONENT,
        "host": HOST,
        "abi_version": NATIVE_ABI_VERSION,
        "source_sha256": ACCEPTED_NATIVE_SOURCE_SHA256,
        "build_key": ACCEPTED_NATIVE_BUILD_KEY,
        "artifact_sha256": ACCEPTED_NATIVE_ARTIFACT_SHA256,
        "full_reset_step_cpp": True,
        "python_fallback": False,
    }
    if any(stable.get(field) != expected for field, expected in exact.items()):
        raise ProductionServiceContractError("candidate native binding differs from accepted exact host")
    value = ServiceAuthority(
        source_manifest_sha256=bindings.source_manifest_sha256,
        lineage_digest=bindings.lineage_digest,
        coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
        coordinate_proposal_digest=activity_permit.coordinate_proposal_digest,
        native_binding_sha256=native_sha,
        native_source_sha256=ACCEPTED_NATIVE_SOURCE_SHA256,
        native_build_key=ACCEPTED_NATIVE_BUILD_KEY,
        native_artifact_sha256=ACCEPTED_NATIVE_ARTIFACT_SHA256,
        master_sha256=_hex(master_sha256, "master_sha256"),
        authorization_sha256=bindings.authorization_sha256,
        test_only=False,
        expires_at=activity_permit.expires_at,
        _seal=_AUTHORITY_SEAL,
    )
    value.require()
    return value


def test_only_service_authority(master: bytes, *, token: str = "fixture") -> ServiceAuthority:
    """Issue a conspicuously fake authority for bounded mechanics tests only."""

    checked = validate_external_master(master)
    value = ServiceAuthority(
        source_manifest_sha256=_fake_digest(f"{token}:source"),
        lineage_digest=_fake_digest(f"{token}:lineage"),
        coordinate_manifest_sha256=_fake_digest(f"{token}:coordinate"),
        coordinate_proposal_digest=_fake_digest(f"{token}:proposal"),
        native_binding_sha256=_fake_digest(f"{token}:native"),
        native_source_sha256=ACCEPTED_NATIVE_SOURCE_SHA256,
        native_build_key=ACCEPTED_NATIVE_BUILD_KEY,
        native_artifact_sha256=ACCEPTED_NATIVE_ARTIFACT_SHA256,
        master_sha256=_fake_digest(master_digest(checked)),
        authorization_sha256=_fake_digest(f"{token}:authority"),
        test_only=True,
        expires_at=None,
        _seal=_AUTHORITY_SEAL,
    )
    value.require()
    return value


class NativeSession(Protocol):
    initial: tuple[HostOutput, ...]

    def renew(self, rows: Iterable[RenewalLane]) -> tuple[HostOutput, ...]: ...

    def close(self) -> None: ...


NativeSessionFactory = Callable[[Iterable[ResetLane]], NativeSession]
SharedGuard = Callable[..., Mapping[str, object]]


class BoundAddressSource:
    """Exact HMAC address adapter for initialization, actions and minibatches."""

    def __init__(self, master: bytes) -> None:
        self._master = validate_external_master(master)

    def initialization_uniforms(
        self, *, replicate: int, arm: str, tensor_name: str, count: int
    ) -> Sequence[float]:
        if count < 1:
            raise ProductionServiceContractError("initialization tensor must be nonempty")
        domain = "foundation-initialization" if arm == "FOUNDATION" else "adapter-initialization"
        return tuple(
            uniform24(
                self._master,
                replicate,
                domain,
                **(
                    {"tensor_group": tensor_name, "flat_index": index}
                    if arm == "FOUNDATION"
                    else {"arm": arm, "tensor_group": tensor_name, "flat_index": index}
                ),
            )
            for index in range(count)
        )

    def action_uniform(
        self, *, replicate: int, domain: str, update: int, episode_slot: int, renewal: int
    ) -> float:
        if domain not in ("FOUNDATION", "ORDER_SHARED"):
            raise ProductionServiceContractError("categorical address domain differs")
        return uniform24(
            self._master,
            replicate,
            "categorical-uniforms",
            stage="foundation-training" if domain == "FOUNDATION" else "adapter-training",
            arm=domain,
            update=update,
            episode=episode_slot,
            renewal=renewal,
        )

    def permutation_indices(
        self, *, replicate: int, arm: str, update: int, epoch: int, count: int
    ) -> Sequence[int]:
        if epoch not in range(3) or count < 4:
            raise ProductionServiceContractError("minibatch address differs")
        rng = for_domain(self._master, replicate, "minibatch-permutations")
        return rng.permutation(
            count,
            "stage",
            "foundation-training" if arm == "FOUNDATION" else "adapter-training",
            "arm",
            arm,
            "update",
            update,
            "epoch",
            epoch,
        )

    def initial_draws(
        self, *, replicate: int, domain: str, address: Mapping[str, object]
    ) -> tuple[float, float, float]:
        values = []
        for component in ("initial-v", "initial-y", "initial-phi"):
            fields = dict(address)
            fields["component"] = component
            values.append(uniform53(self._master, replicate, domain, **fields))
        return (0.03 * values[0], 0.02 * values[1] - 0.01, 0.02 * values[2] - 0.01)

    def disturbance(
        self,
        *,
        replicate: int,
        stage: str,
        arm: str,
        regime: str,
        episode: int,
        tick: int,
        component: str,
    ) -> float:
        magnitudes = {"eta-v": 0.003, "eta-y": 0.002, "eta-omega": 0.004}
        try:
            magnitude = magnitudes[component]
        except KeyError as error:
            raise ProductionServiceContractError("disturbance component differs") from error
        bit = raw_u64(
            self._master,
            replicate,
            "disturbances",
            stage=stage,
            arm=arm,
            regime=regime,
            episode=episode,
            tick=tick,
            component=component,
        ) & 1
        return magnitude if bit else -magnitude

    def rank(self, *, replicate: int, domain: str, rows: Sequence[Mapping[str, object]]) -> tuple[int, ...]:
        keyed = []
        for index, fields in enumerate(rows):
            keyed.append((raw_u64(self._master, replicate, domain, **dict(fields)), index))
        return tuple(index for _, index in sorted(keyed))


@dataclass(frozen=True)
class TrainingServiceOutput:
    frozen_batch: FrozenUpdateBatch
    update_receipt: TrainingUpdateReceipt
    checkpoint_payload: Mapping[str, object]
    native_receipt: Mapping[str, object]
    episode_count: int = 12
    native_width: int = 12
    question_relevant_output: bool = False


def _events(q: int) -> tuple[int, int]:
    if q == 1:
        return (HOOK_HANDOFF, FORMATION_ROTATE)
    if q == 0:
        return (FORMATION_ROTATE, HOOK_HANDOFF)
    raise ProductionServiceContractError("support graph q must be binary")


def _regime_schedule(regime: str, switch_tick: int = 0) -> tuple[int, int | None, int | None]:
    if regime.startswith("fixed-"):
        value = int(regime.split("-", 1)[1])
        return value, None, None
    if regime == "7-to-13":
        return 7, 13, switch_tick
    if regime == "13-to-7":
        return 13, 7, switch_tick
    raise ProductionServiceContractError("external-k regime differs")


def _window(values: Sequence[float], tick: int) -> tuple[float, ...]:
    selected = tuple(values[tick : tick + 13])
    if not selected:
        raise ProductionServiceContractError("active disturbance offset lies outside the horizon")
    return selected + (selected[-1],) * (13 - len(selected))


class NativeProductionServices:
    """Concrete, native-only services bound to one master and sealed authority."""

    def __init__(
        self,
        *,
        authority: ServiceAuthority,
        master: bytes,
        shared_guard: SharedGuard | None = None,
        session_factory: NativeSessionFactory | None = None,
    ) -> None:
        # Authority validation is intentionally first.
        if not isinstance(authority, ServiceAuthority):
            raise TypeError("sealed service authority is required")
        authority.require()
        checked_master = validate_external_master(master)
        observed_master = master_digest(checked_master)
        expected = authority.master_sha256
        if authority.test_only:
            if expected != _fake_digest(observed_master):
                raise ProductionServiceContractError("TEST_ONLY master differs from sealed authority")
        elif expected != observed_master:
            raise ProductionServiceContractError("external master differs from sealed authority")
        self.authority = authority
        self.addresses = BoundAddressSource(checked_master)
        if shared_guard is None:
            from envs.native.production_backend import require_cpp_batched_production

            shared_guard = require_cpp_batched_production
        if session_factory is None:
            from .native_backend import NativeBatch

            session_factory = NativeBatch
        self._shared_guard = shared_guard
        self._session_factory = session_factory
        self._guard_receipts: dict[int, dict[str, object]] = {}

    def _guard(self, width: int) -> dict[str, object]:
        self.authority.require()
        if width not in ACCEPTED_SERVICE_WIDTHS:
            raise ProductionServiceContractError("service width is not admitted")
        if torch.get_num_threads() != 1:
            raise ProductionServiceContractError("each production worker requires exactly one Torch thread")
        if width in self._guard_receipts:
            return dict(self._guard_receipts[width])
        receipt = dict(
            self._shared_guard(COMPONENT, backend="cpp", batch_width=width, build_root=None)
        )
        native = receipt.get("native")
        if (
            receipt.get("component") != COMPONENT
            or receipt.get("backend") != "cpp"
            or receipt.get("batch_width") != width
            or receipt.get("full_reset_step_cpp") is not True
            or receipt.get("python_fallback") is not False
            or not isinstance(native, Mapping)
            or native.get("artifact_sha256") != self.authority.native_artifact_sha256
        ):
            raise ProductionServiceContractError("live shared C++ guard differs from authority")
        self._guard_receipts[width] = dict(receipt)
        return dict(receipt)

    def materialize_foundation(self, *, replicate: int) -> FoundationActorCritic:
        self._guard(FOUNDATION_TRAINING_WIDTH)
        return FoundationActorCritic(
            permit=self.authority,
            replicate=replicate,
            initialization_source=self.addresses,
        )

    def materialize_order_arm(
        self, *, foundation: FoundationActorCritic, arm: str | LearnedOrderArm
    ) -> OrderActorCritic:
        self._guard(ORDER_TRAINING_WIDTH)
        learned = arm if isinstance(arm, LearnedOrderArm) else LearnedOrderArm(str(arm))
        frozen = clone_frozen_foundation_actor(foundation, permit=self.authority, arm=learned)
        return OrderActorCritic(
            learned,
            frozen_foundation=frozen,
            permit=self.authority,
            initialization_source=self.addresses,
        )

    def _training_reset(self, *, replicate: int, arm: str, update: int, slot: object) -> ResetLane:
        domain = "foundation-training-state" if arm == "FOUNDATION" else "adapter-training-state"
        address = (
            {"update": update, "episode": slot.index}
            if arm == "FOUNDATION"
            else {"arm": "ORDER_SHARED", "update": update, "episode": slot.index}
        )
        initial_v, initial_y, initial_phi = self.addresses.initial_draws(
            replicate=replicate, domain=domain, address=address
        )
        return ResetLane(
            middle_events=_events(slot.q),
            k_initial=slot.k,
            initial_v=initial_v,
            initial_y=initial_y,
            initial_phi=initial_phi,
        )

    def _training_disturbances(
        self, *, replicate: int, arm: str, update: int, episode: int
    ) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
        stage = "foundation-training" if arm == "FOUNDATION" else "adapter-training"
        shared_arm = "FOUNDATION" if arm == "FOUNDATION" else "ORDER_SHARED"
        regime = f"update-{update}"
        return tuple(
            tuple(
                self.addresses.disturbance(
                    replicate=replicate,
                    stage=stage,
                    arm=shared_arm,
                    regime=regime,
                    episode=episode,
                    tick=tick,
                    component=component,
                )
                for tick in range(HORIZON_TICKS)
            )
            for component in ("eta-v", "eta-y", "eta-omega")
        )  # type: ignore[return-value]

    def collect_and_train_update(
        self,
        *,
        trainer: DurationCorrectPPOTrainer,
        update: int,
    ) -> TrainingServiceOutput:
        """Collect exactly 12 complete native episodes and apply one PPO update."""

        native_receipt = self._guard(FOUNDATION_TRAINING_WIDTH)
        model = trainer.model
        arm = "FOUNDATION" if isinstance(model, FoundationActorCritic) else model.arm.value
        replicate = model.replicate
        if trainer.permit is not self.authority:
            raise ProductionServiceContractError("trainer is not bound to this sealed authority")
        schedule = registered_episode_schedule(arm)
        resets = tuple(
            self._training_reset(replicate=replicate, arm=arm, update=update, slot=slot)
            for slot in schedule
        )
        tapes = tuple(
            self._training_disturbances(
                replicate=replicate, arm=arm, update=update, episode=slot.index
            )
            for slot in schedule
        )
        per_episode: list[list[tuple[torch.Tensor, int, int, tuple[float, ...], bool]]] = [
            [] for _ in schedule
        ]
        renewals = [0] * len(schedule)
        session = self._session_factory(resets)
        try:
            outputs = tuple(session.initial)
            if len(outputs) != FOUNDATION_TRAINING_WIDTH or any(not value.active for value in outputs):
                raise ProductionServiceContractError("training native reset width/activity differs")
            while any(value.active for value in outputs):
                active = tuple(index for index, value in enumerate(outputs) if value.active)
                observations = torch.tensor(
                    tuple(outputs[index].observation for index in active), dtype=torch.float32
                )
                announced = torch.tensor(
                    tuple(outputs[index].next_k for index in active), dtype=torch.int64
                )
                with torch.no_grad():
                    if isinstance(model, FoundationActorCritic):
                        logits = model(observations).logits
                    else:
                        physical_q = torch.tensor(
                            tuple(float(schedule[index].q) for index in active), dtype=torch.float32
                        )
                        logits = model(observations, physical_q, announced).logits
                selected: dict[int, int] = {}
                for row_index, lane in enumerate(active):
                    selected[lane] = int(
                        sample_actions_from_source(
                            logits[row_index : row_index + 1],
                            source=self.addresses,
                            replicate=replicate,
                            arm=arm,
                            update=update,
                            episode_slot=schedule[lane].index,
                            renewal_indices=(renewals[lane],),
                        )[0]
                    )
                rows = []
                before = outputs
                for lane, output in enumerate(outputs):
                    eta_v, eta_y, eta_omega = tapes[lane]
                    if output.active:
                        rows.append(
                            RenewalLane(
                                action=selected[lane],
                                eta_v=_window(eta_v, output.tick),
                                eta_y=_window(eta_y, output.tick),
                                eta_omega=_window(eta_omega, output.tick),
                            )
                        )
                    else:
                        tick = min(output.tick, HORIZON_TICKS - 1)
                        rows.append(
                            RenewalLane(
                                action=0,
                                eta_v=_window(eta_v, tick),
                                eta_y=_window(eta_y, tick),
                                eta_omega=_window(eta_omega, tick),
                                active=False,
                            )
                        )
                outputs = tuple(session.renew(rows))
                if len(outputs) != FOUNDATION_TRAINING_WIDTH:
                    raise ProductionServiceContractError("training native renewal width differs")
                for lane in active:
                    after = outputs[lane]
                    reward_count = getattr(after, "last_hold_reward_count", None)
                    reward_trace = getattr(after, "last_hold_rewards", None)
                    if reward_count is None or reward_trace is None:
                        raise ProductionServiceContractError(
                            "native ABI lacks the required per-hold primitive reward trace"
                        )
                    if (
                        isinstance(reward_count, bool)
                        or not isinstance(reward_count, int)
                        or reward_count != after.ticks_advanced
                    ):
                        raise ProductionServiceContractError("native primitive reward count differs")
                    full_trace = tuple(float(value) for value in reward_trace)
                    if len(full_trace) != 13 or any(value != 0.0 for value in full_trace[reward_count:]):
                        raise ProductionServiceContractError("native primitive reward tail is not canonical zero")
                    trace = full_trace[:reward_count]
                    if len(trace) != after.ticks_advanced or not trace or any(
                        not math.isfinite(value) for value in trace
                    ):
                        raise ProductionServiceContractError("native primitive reward trace differs")
                    delta = after.cumulative_reward - before[lane].cumulative_reward
                    if not math.isclose(math.fsum(trace), delta, rel_tol=0.0, abs_tol=2e-12):
                        raise ProductionServiceContractError("native reward trace does not sum to hold reward")
                    per_episode[lane].append(
                        (
                            torch.tensor(before[lane].observation, dtype=torch.float32),
                            before[lane].next_k,
                            selected[lane],
                            trace,
                            after.active,
                        )
                    )
                    renewals[lane] += 1
                for old, new in zip(before, outputs):
                    if not old.active and new != old:
                        raise ProductionServiceContractError("masked training lane advanced")
                if sum(renewals) > FOUNDATION_TRAINING_WIDTH * HORIZON_TICKS:
                    raise ProductionServiceContractError("training native session did not terminate")
            if any(not value.terminal for value in outputs):
                raise ProductionServiceContractError("training episode inventory is nonterminal")
        finally:
            session.close()

        flattened = tuple(row for episode in per_episode for row in episode)
        offsets = [0]
        for episode in per_episode:
            if not episode:
                raise ProductionServiceContractError("training episode contains no renewal")
            offsets.append(offsets[-1] + len(episode))
        observation = torch.stack(tuple(row[0] for row in flattened))
        announced_k = torch.tensor(tuple(row[1] for row in flattened), dtype=torch.int64)
        actions = torch.tensor(tuple(row[2] for row in flattened), dtype=torch.int64)
        rewards = tuple(row[3] for row in flattened)
        nonterminal = torch.tensor(tuple(row[4] for row in flattened), dtype=torch.bool)
        physical_q = None
        if arm != "FOUNDATION":
            physical_q = torch.tensor(
                tuple(
                    float(slot.q)
                    for slot, episode in zip(schedule, per_episode)
                    for _ in episode
                ),
                dtype=torch.float32,
            )
        frozen = freeze_update_batch(
            model,
            replicate=replicate,
            update=update,
            observation=observation,
            physical_q=physical_q,
            announced_k=announced_k,
            actions=actions,
            primitive_rewards=rewards,
            nonterminal=nonterminal,
            episode_offsets=offsets,
        )
        receipt = trainer.train_update(frozen, permutations=self.addresses)
        checkpoint = trainer.checkpoint_payload(completed_updates=update)
        return TrainingServiceOutput(frozen, receipt, checkpoint, native_receipt)

    def evaluation_scenarios(self, *, replicate: int, stage: str) -> tuple[EvaluationScenario, ...]:
        self.authority.require_evaluation_authority(stage=stage, replicate=replicate)
        scenarios: list[EvaluationScenario] = []
        for regime in REGIMES:
            setup_rows = tuple(
                {
                    "stage": stage,
                    "arm": "PAIRED",
                    "regime": regime,
                    "episode": index,
                }
                for index in range(EPISODES_PER_REGIME)
            )
            setup_rank = self.addresses.rank(
                replicate=replicate, domain="setup-order", rows=setup_rows
            )
            graph_by_index = {
                index: "HR" if rank < 60 else "RH"
                for rank, index in enumerate(setup_rank)
            }
            switch_by_index = {index: 0 for index in range(EPISODES_PER_REGIME)}
            if regime in SWITCH_REGIMES:
                for order in ("HR", "RH"):
                    indices = tuple(
                        index for index in range(EPISODES_PER_REGIME) if graph_by_index[index] == order
                    )
                    rows = tuple(
                        {
                            "stage": stage,
                            "arm": "PAIRED",
                            "regime": regime,
                            "episode": index,
                        }
                        for index in indices
                    )
                    ranked_local = self.addresses.rank(
                        replicate=replicate, domain="switch-time", rows=rows
                    )
                    for local_rank, row_index in enumerate(ranked_local):
                        switch_by_index[indices[row_index]] = 91 if local_rank < 30 else 273
            for index in range(EPISODES_PER_REGIME):
                payload = {
                    "stage": stage,
                    "replicate": replicate,
                    "regime": regime,
                    "episode": index,
                    "graph_order": graph_by_index[index],
                    "switch_tick": switch_by_index[index],
                    "coordinate_manifest_sha256": self.authority.coordinate_manifest_sha256,
                }
                digest = hashlib.sha256(
                    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
                ).hexdigest()
                scenarios.append(
                    EvaluationScenario(
                        regime=regime,
                        scenario_index=index,
                        graph_order=graph_by_index[index],
                        switch_tick=switch_by_index[index],
                        scenario_digest=digest,
                    )
                )
        return tuple(scenarios)

    def evaluation_adapter(
        self, *, stage: str, replicate: int, scenarios: Sequence[EvaluationScenario]
    ) -> "NativeEvaluationAdapter":
        self.authority.require_evaluation_authority(stage=stage, replicate=replicate)
        return NativeEvaluationAdapter(self, stage=stage, replicate=replicate, scenarios=scenarios)

    def opportunity_tapes(
        self, *, replicate: int, k: int, state_index: int
    ) -> tuple[DisturbanceTape, ...]:
        if k not in TARGET_K or state_index not in range(16):
            raise ProductionServiceContractError("opportunity tape slot differs")
        result = []
        for tape in range(4):
            rows = {component: [] for component in ("eta-v", "eta-y", "eta-omega")}
            for tick in range(HORIZON_TICKS):
                for component, magnitude in (
                    ("eta-v", 0.003), ("eta-y", 0.002), ("eta-omega", 0.004)
                ):
                    bit = raw_u64(
                        self.addresses._master,
                        replicate,
                        "opportunity-disturbance-tape",
                        k=k,
                        state=state_index,
                        tape=tape,
                        tick=tick,
                        component=component,
                    ) & 1
                    rows[component].append(magnitude if bit else -magnitude)
            address = (
                f"opportunity-disturbance-tape/{replicate}/{k}/{state_index}/{tape}/"
                f"{self.authority.coordinate_manifest_sha256}"
            )
            result.append(
                DisturbanceTape(
                    address=address,
                    eta_v=tuple(rows["eta-v"]),
                    eta_y=tuple(rows["eta-y"]),
                    eta_omega=tuple(rows["eta-omega"]),
                )
            )
        return tuple(result)

    def run_opportunity_pair(
        self,
        *,
        replicate: int,
        k: int,
        state_index: int,
        permit: OpportunityExecutionPermit | Stage1bOpportunityExecutionPermit,
        foundation: FoundationActorCritic,
    ) -> PairOpportunityMetrics:
        if not isinstance(foundation, FoundationActorCritic) or foundation.replicate != replicate:
            raise ProductionServiceContractError("opportunity foundation belongs to a different replicate")
        if self.authority.test_only:
            if isinstance(permit, Stage1bOpportunityExecutionPermit):
                raise ProductionServiceContractError("TEST_ONLY service cannot consume a production Stage-1b permit")
            validate_opportunity_execution_permit(permit)
        else:
            if not isinstance(permit, Stage1bOpportunityExecutionPermit):
                raise ProductionServiceContractError("production service requires the sealed Stage-1b permit")
            validate_stage1b_opportunity_execution_permit(permit)
            if (
                permit.lineage_digest != self.authority.lineage_digest
                or permit.coordinate_manifest_sha256 != self.authority.coordinate_manifest_sha256
            ):
                raise ProductionServiceContractError("Stage-1b permit differs from service lineage")
        self._guard(OPPORTUNITY_WIDTH)
        initial_v, initial_y, initial_phi = self.addresses.initial_draws(
            replicate=replicate,
            domain="opportunity-state",
            address={"k": k, "state": state_index},
        )
        state = OpportunityState(replicate, k, state_index, initial_v, initial_y, initial_phi)
        tapes = self.opportunity_tapes(replicate=replicate, k=k, state_index=state_index)

        def frozen_policy(observations: tuple[tuple[float, ...], ...]) -> Sequence[Sequence[float]]:
            value = torch.tensor(observations, dtype=torch.float32)
            with torch.no_grad():
                return foundation.actor(value).cpu().tolist()

        return run_complete_pair(
            state,
            tapes,
            permit=permit,
            foundation=frozen_policy,
            session_factory=self._session_factory,
        )


class NativeEvaluationAdapter:
    """Lazy width-120 regime cache implementing AcceptedNativeEvaluationService."""

    def __init__(
        self,
        services: NativeProductionServices,
        *,
        stage: str,
        replicate: int,
        scenarios: Sequence[EvaluationScenario],
    ) -> None:
        self._services = services
        self._stage = stage
        self._replicate = replicate
        self._scenarios = tuple(scenarios)
        self._slots = {(row.regime, row.scenario_index): row for row in self._scenarios}
        if len(self._slots) != 720:
            raise ProductionServiceContractError("evaluation adapter requires the complete 720-scenario plan")
        self._cache: dict[tuple[str, str], dict[int, EpisodeEndpoint]] = {}

    def evaluate_scenario(
        self,
        *,
        binding: AcceptedControllerBinding,
        replicate: int,
        controller: str,
        scenario: EvaluationScenario,
    ) -> EpisodeEndpoint:
        binding.validate()
        if replicate != self._replicate or scenario != self._slots.get((scenario.regime, scenario.scenario_index)):
            raise ProductionServiceContractError("evaluation request differs from bound scenario inventory")
        allowed = ("FOUNDATION",) if self._stage == "foundation-competence" else CONTROLLERS
        if controller not in allowed or binding.controller != controller:
            raise ProductionServiceContractError("evaluation controller differs from stage inventory")
        key = (controller, scenario.regime)
        if key not in self._cache:
            self._cache[key] = self._run_regime(binding, controller, scenario.regime)
        return self._cache[key][scenario.scenario_index]

    def _run_regime(
        self, binding: AcceptedControllerBinding, controller: str, regime: str
    ) -> dict[int, EpisodeEndpoint]:
        self._services._guard(EVALUATION_WIDTH)
        scenarios = tuple(self._slots[(regime, index)] for index in range(EPISODES_PER_REGIME))
        resets = []
        tapes = []
        for scenario in scenarios:
            q = 1 if scenario.graph_order == "HR" else 0
            initial_v, initial_y, initial_phi = self._services.addresses.initial_draws(
                replicate=self._replicate,
                domain=("foundation-competence-state" if self._stage == "foundation-competence" else "final-evaluation-state"),
                address=(
                    {"regime": regime, "episode": scenario.scenario_index}
                    if self._stage == "foundation-competence"
                    else {"controller": "PAIRED", "regime": regime, "episode": scenario.scenario_index}
                ),
            )
            initial_k, after_k, switch_tick = _regime_schedule(regime, scenario.switch_tick)
            resets.append(
                ResetLane(
                    middle_events=_events(q),
                    k_initial=initial_k,
                    k_after=after_k,
                    switch_tick=switch_tick,
                    initial_v=initial_v,
                    initial_y=initial_y,
                    initial_phi=initial_phi,
                )
            )
            tapes.append(
                tuple(
                    tuple(
                        self._services.addresses.disturbance(
                            replicate=self._replicate,
                            stage=self._stage,
                            arm="PAIRED",
                            regime=regime,
                            episode=scenario.scenario_index,
                            tick=tick,
                            component=component,
                        )
                        for tick in range(HORIZON_TICKS)
                    )
                    for component in ("eta-v", "eta-y", "eta-omega")
                )
            )
        session = self._services._session_factory(resets)
        try:
            outputs = tuple(session.initial)
            if len(outputs) != EVALUATION_WIDTH:
                raise ProductionServiceContractError("evaluation native reset width differs")
            queries = [0] * EVALUATION_WIDTH
            while any(value.active for value in outputs):
                active = tuple(index for index, value in enumerate(outputs) if value.active)
                observations = torch.tensor(
                    tuple(outputs[index].observation for index in active), dtype=torch.float32
                )
                announced = torch.tensor(tuple(outputs[index].next_k for index in active), dtype=torch.int64)
                physical = torch.tensor(
                    tuple(1.0 if scenarios[index].graph_order == "HR" else 0.0 for index in active),
                    dtype=torch.float32,
                )
                with torch.no_grad():
                    model = binding.model
                    if controller == "FOUNDATION":
                        if not isinstance(model, FoundationActorCritic):
                            raise ProductionServiceContractError("foundation evaluation model type differs")
                        logits = model(observations).logits
                    elif controller == "REVERSED":
                        if isinstance(model, TiedReversedController):
                            reversed_model = model
                        elif isinstance(model, OrderActorCritic):
                            reversed_model = TiedReversedController(model)
                        else:
                            raise ProductionServiceContractError("REVERSED evaluation model type differs")
                        logits = reversed_model(observations, physical, announced).logits
                    else:
                        if not isinstance(model, OrderActorCritic) or model.arm.value != controller:
                            raise ProductionServiceContractError("order evaluation model type or arm differs")
                        logits = model(observations, physical, announced).logits
                    actions = lexicographic_argmax(logits).cpu().tolist()
                chosen = dict(zip(active, (int(value) for value in actions)))
                before = outputs
                rows = []
                for lane, output in enumerate(outputs):
                    eta_v, eta_y, eta_omega = tapes[lane]
                    if output.active:
                        rows.append(
                            RenewalLane(
                                action=chosen[lane],
                                eta_v=_window(eta_v, output.tick),
                                eta_y=_window(eta_y, output.tick),
                                eta_omega=_window(eta_omega, output.tick),
                            )
                        )
                        queries[lane] += 1
                    else:
                        tick = min(output.tick, HORIZON_TICKS - 1)
                        rows.append(
                            RenewalLane(
                                action=0,
                                eta_v=_window(eta_v, tick),
                                eta_y=_window(eta_y, tick),
                                eta_omega=_window(eta_omega, tick),
                                active=False,
                            )
                        )
                outputs = tuple(session.renew(rows))
                for old, new in zip(before, outputs):
                    if not old.active and new != old:
                        raise ProductionServiceContractError("masked evaluation lane advanced")
                if sum(queries) > EVALUATION_WIDTH * HORIZON_TICKS:
                    raise ProductionServiceContractError("evaluation native session did not terminate")
            if any(not value.terminal for value in outputs):
                raise ProductionServiceContractError("evaluation inventory contains a nonterminal lane")
            result = {}
            for scenario, output in zip(scenarios, outputs):
                result[scenario.scenario_index] = EpisodeEndpoint(
                    replicate=self._replicate,
                    controller=controller,
                    scenario=scenario,
                    safe_dock=output.safe_dock,
                    timeout=output.timeout,
                    cable_overload=output.cable_overload,
                    gantry_contact=output.gantry_contact,
                    attitude_loss=output.attitude_loss,
                    formation_loss=output.formation_loss,
                    dock_tick=output.dock_tick,
                    active_energy_sum=output.cumulative_energy,
                    active_ticks=output.energy_ticks,
                    post_absorption_policy_queries=0,
                )
                result[scenario.scenario_index].validate()
            return result
        finally:
            session.close()


def production_service_contract() -> dict[str, object]:
    """Return the exact complete plan without materializing an empirical object."""

    return {
        "schema": SERVICE_SCHEMA,
        "card_revision": CARD_REVISION,
        "component": COMPONENT,
        "host": HOST,
        "native_abi": NATIVE_ABI_VERSION,
        "native_only": True,
        "python_plant_or_reward_fallback": False,
        "widths": {
            "foundation_training": FOUNDATION_TRAINING_WIDTH,
            "order_training": ORDER_TRAINING_WIDTH,
            "foundation_competence": EVALUATION_WIDTH,
            "final_evaluation": EVALUATION_WIDTH,
            "opportunity": OPPORTUNITY_WIDTH,
        },
        "training": {
            "foundation_updates_per_replicate": 160,
            "order_updates_per_arm": 96,
            "episodes_per_update": 12,
            "train_k": (5, 11),
            "optimizer_steps_per_update": 12,
            "primitive_reward_trace_required": True,
        },
        "evaluation": {
            "regimes": REGIMES,
            "controllers": CONTROLLERS,
            "episodes_per_regime": 120,
            "fixed_graph_balance": (60, 60),
            "switch_graph_time_balance": (30, 30, 30, 30),
            "deterministic_lexicographic_argmax": True,
        },
        "opportunity": {
            "k": TARGET_K,
            "states_per_k": 16,
            "graphs": 2,
            "actions": 18,
            "common_tapes": 4,
            "rollouts_per_pair": 144,
        },
        "counts": dict(PANEL_COUNTS),
        "outputs": "in_memory_only",
        "question_relevant_output": False,
    }


__all__ = [
    "ACCEPTED_SERVICE_WIDTHS",
    "BoundAddressSource",
    "NativeEvaluationAdapter",
    "NativeProductionServices",
    "ProductionServiceContractError",
    "SERVICE_SCHEMA",
    "ServiceAuthority",
    "TrainingServiceOutput",
    "issue_service_authority",
    "production_service_contract",
    "test_only_service_authority",
]
