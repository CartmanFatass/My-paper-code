"""Injected actual-path adapter for the committed VNFC host constructors.

Imports of the committed native/fixture/observation implementation belong in
the formal composition root.  This module is testable with inert fakes and does
not import or call the native host on import.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
import importlib
from typing import Callable, Mapping, Protocol, Sequence

from .fixtures import (
    ActualPathFixturePlan,
    FixtureError,
    HostCall,
    expected_host_call_ledger,
    fresh_cell_identity,
    validate_host_call_ledger,
)
from .model import PublicObservation


class AdapterError(RuntimeError):
    pass


class NativeBatch(Protocol):
    def reset(self, fixtures: Sequence[object]) -> Sequence[object]: ...
    def bcrh(self, observations: Sequence[object]) -> Sequence[Sequence[int | None]]: ...
    def step(self, commands: Sequence[Sequence[int | None]]) -> Sequence[object]: ...

    def close(self) -> None: ...


class ObservationConstructor(Protocol):
    def __call__(self, native_row: object) -> Mapping[str, object]: ...


@dataclass(frozen=True)
class CommittedObservationRow:
    trace: Mapping[str, object]
    fixture: object
    failed_rank: int


@dataclass(frozen=True)
class CommittedComponents:
    general_agent_state: Callable[..., object]
    episode_fixture: Callable[..., object]
    native_interactive_batch: Callable[[Sequence[object]], object]
    model_inputs: Callable[[Mapping[str, object], object, int], Sequence[object]]


class CommittedNativeBridge:
    """Exact lazy bridge over the committed interactive reset/BCRH/step API."""

    def __init__(self, components: CommittedComponents) -> None:
        self._components = components
        self._batch: object | None = None
        self._fixtures: tuple[object, ...] = ()
        self._failed: tuple[int, ...] = ()

    def reset(self, fixtures: Sequence[object]) -> tuple[CommittedObservationRow, ...]:
        if self._batch is not None:
            self.close()
        self._fixtures = tuple(fixtures)
        if len(self._fixtures) != 8:
            raise AdapterError("committed interactive reset requires exact width eight")
        self._batch = self._components.native_interactive_batch(self._fixtures)
        initial = tuple(getattr(self._batch, "initial"))
        if len(initial) != 8:
            raise AdapterError("committed interactive initial width differs")
        self._failed = tuple(int(row["failed_rank"]) for row in initial)
        rows = tuple(row["next_observation"] for row in initial)
        if any(row is None for row in rows):
            raise AdapterError("committed reset returned a terminal row")
        return tuple(CommittedObservationRow(row, fixture, failed) for row, fixture, failed in zip(rows, self._fixtures, self._failed))  # type: ignore[arg-type]

    def bcrh(self, observations: Sequence[object]) -> tuple[tuple[int | None, ...], ...]:
        if self._batch is None or len(tuple(observations)) != 8:
            raise AdapterError("committed BCRH call is outside one live width-eight batch")
        decisions = tuple(getattr(self._batch, "bcrh")(include_candidate_records=False))
        if len(decisions) != 8:
            raise AdapterError("committed BCRH width differs")
        if any(not row["scorer_checker_equal"] or not row["independent_enumerator_equal"] for row in decisions):
            raise AdapterError("committed BCRH scorer/checker identity differs")
        return tuple(tuple(row["scorer_command"]) for row in decisions)  # type: ignore[arg-type]

    def step(self, commands: Sequence[Sequence[int | None]]) -> tuple[CommittedObservationRow, ...]:
        if self._batch is None:
            raise AdapterError("committed step has no live reset batch")
        rows = tuple(getattr(self._batch, "step")(tuple(tuple(row) for row in commands)))
        if len(rows) != 8 or any(row["next_observation"] is None for row in rows):
            raise AdapterError("committed one-step output is terminal or wrong width")
        return tuple(
            CommittedObservationRow(row["next_observation"], fixture, failed)
            for row, fixture, failed in zip(rows, self._fixtures, self._failed)
        )

    def close(self) -> None:
        if self._batch is not None:
            getattr(self._batch, "close")()
            self._batch = None
            self._fixtures = ()
            self._failed = ()


def _tolist(value: object) -> object:
    current = value
    if callable(getattr(current, "detach", None)):
        current = current.detach()
    if callable(getattr(current, "cpu", None)):
        current = current.cpu()
    if callable(getattr(current, "tolist", None)):
        return current.tolist()
    return current


def committed_observation_constructor(
    row: object, components: CommittedComponents
) -> Mapping[str, object]:
    if not isinstance(row, CommittedObservationRow):
        raise AdapterError("committed observation row wrapper differs")
    inputs = tuple(components.model_inputs(row.trace, row.fixture, row.failed_rank))
    if len(inputs) != 6:
        raise AdapterError("committed _model_inputs tensor inventory differs")
    agents, zones, globals_, legal, fixed, _legacy_opaque = (_tolist(value) for value in inputs)
    agents = agents[0]  # type: ignore[index]
    zones = zones[0]  # type: ignore[index]
    globals_ = globals_[0]  # type: ignore[index]
    legal = legal[0]  # type: ignore[index]
    fixed = fixed[0]  # type: ignore[index]
    epoch = int(row.trace["epoch"])
    presented = tuple(rank for rank in getattr(row.fixture, "post_presentations")[epoch] if rank != row.failed_rank)
    fixed_rows = tuple(None if int(value) < 0 else int(value) for value in fixed)  # type: ignore[arg-type]
    return {
        "entity_handles": presented,
        "agents": agents,
        "zones": zones,
        "global_row": globals_,
        "legal": legal,
        "fixed_occupant_rows": fixed_rows,
        "physical_token_states": tuple(int(value) for value in row.trace["token_state"]),  # type: ignore[arg-type]
    }


def load_committed_components(
    import_module: Callable[[str], object] = importlib.import_module,
) -> CommittedComponents:
    """Resolve exact committed callables lazily; importing this module is inert."""
    fixtures = import_module("experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures")
    native = import_module("experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend")
    training = import_module("experiments.candidates.variable_n_fleet_churn_bpcr_r09.empirical_training")
    values = (
        getattr(fixtures, "GeneralAgentState", None),
        getattr(fixtures, "EpisodeFixture", None),
        getattr(native, "NativeInteractiveBatch", None),
        getattr(training, "_model_inputs", None),
    )
    if any(not callable(value) for value in values):
        raise AdapterError("exact committed fixture/native/_model_inputs callable is absent")
    return CommittedComponents(*values)  # type: ignore[arg-type]


def load_committed_adapter(
    import_module: Callable[[str], object] = importlib.import_module,
) -> "R02ActualPathAdapter":
    components = load_committed_components(import_module)
    bridge = CommittedNativeBridge(components)
    return R02ActualPathAdapter(
        general_agent_state=components.general_agent_state,
        episode_fixture=components.episode_fixture,
        native=bridge,
        observation_constructor=lambda row: committed_observation_constructor(row, components),
    )


class R02ActualPathAdapter:
    def __init__(
        self,
        *,
        general_agent_state: Callable[..., object],
        episode_fixture: Callable[..., object],
        native: NativeBatch,
        observation_constructor: ObservationConstructor,
    ) -> None:
        self._general_agent_state = general_agent_state
        self._episode_fixture = episode_fixture
        self._native = native
        self._observation_constructor = observation_constructor
        self._ledger: list[HostCall] = []

    def _record(self, plan: ActualPathFixturePlan, family: str, operation: str) -> None:
        self._ledger.append(HostCall(len(self._ledger) + 1, plan.roster_size, plan.failed_zone, family, operation))

    def _fixture(self, plan: ActualPathFixturePlan, presentation: tuple[int, ...], ranks: Mapping[int, int]) -> object:
        agents = tuple(
            self._general_agent_state(entity, ranks[entity], fast, radio)
            for entity, fast, radio in plan.entity_rows
        )
        full_pre_loss = presentation + (plan.failed_entity,)
        if len(full_pre_loss) != plan.roster_size + 1 or len(set(full_pre_loss)) != plan.roster_size + 1:
            raise AdapterError("full pre-loss presentation must add the failed entity exactly once")
        return self._episode_fixture(
            plan.failed_zone,
            agents,
            plan.demand_1,
            plan.demand_2,
            plan.blocked_1,
            plan.blocked_2,
            plan.post_commands,
            (full_pre_loss,) * 6,
        )

    @staticmethod
    def _require_width_eight(rows: Sequence[object], context: str) -> tuple[object, ...]:
        materialized = tuple(rows)
        if len(materialized) != 8:
            raise AdapterError(f"{context} must preserve native batch width eight")
        for offset in range(0, 8, 2):
            if materialized[offset] != materialized[offset + 1]:
                raise AdapterError(f"{context} duplicate pair differs before de-duplication")
        return materialized

    def public_observation(self, native_row: object, ranks: Mapping[int, int]) -> PublicObservation:
        raw = self._observation_constructor(native_row)
        required = {"entity_handles", "agents", "zones", "global_row", "legal", "fixed_occupant_rows", "physical_token_states"}
        if set(raw) != required:
            raise AdapterError("committed observation constructor schema differs")
        handles = tuple(int(value) for value in raw["entity_handles"])  # type: ignore[arg-type]
        if set(handles) != set(ranks):
            raise AdapterError("public observation active handles differ from fresh sidecar")
        fixed_rows = tuple(raw["fixed_occupant_rows"])  # type: ignore[arg-type]
        if len(fixed_rows) != 4:
            raise AdapterError("fixed occupant row vector differs")
        fixed_handles = tuple(None if row is None else handles[int(row)] for row in fixed_rows)
        observation = PublicObservation(
            entity_handles=handles,
            agents=tuple(tuple(float(value) for value in row) for row in raw["agents"]),  # type: ignore[arg-type]
            zones=tuple(tuple(float(value) for value in row) for row in raw["zones"]),  # type: ignore[arg-type]
            global_row=tuple(float(value) for value in raw["global_row"]),  # type: ignore[arg-type]
            legal=tuple(tuple(bool(value) for value in row) for row in raw["legal"]),  # type: ignore[arg-type]
            opaque_ranks=tuple(ranks[handle] for handle in handles),
            fixed_occupants=fixed_handles,  # type: ignore[arg-type]
        )
        observation.validate()
        return observation

    def construct_cell(self, plans: Sequence[ActualPathFixturePlan]) -> Mapping[str, object]:
        materialized = tuple(plans)
        if len(materialized) != 3 or {row.state_kind for row in materialized} != {"t0", "later_fixed_or_acquiring", "diagnostic_null_tie"}:
            raise AdapterError("cell requires the exact three state plans")
        key = {(row.roster_size, row.failed_zone) for row in materialized}
        if len(key) != 1:
            raise AdapterError("cell plans disagree on N/failed-zone")
        n, zone = next(iter(key))
        identity = fresh_cell_identity(n, zone)
        ranks = dict(identity.opaque_rank_by_entity)
        presentations = dict(identity.presentations)
        non_diag = next(row for row in materialized if row.state_kind == "t0")
        diag = next(row for row in materialized if row.state_kind == "diagnostic_null_tie")
        ordered_names = non_diag.native_batch_presentations
        non_diag_fixtures = self._require_width_eight(
            tuple(self._fixture(non_diag, presentations[name], ranks) for name in ordered_names),
            "non-diagnostic fixture batch",
        )
        reset_rows = self._require_width_eight(self._native.reset(non_diag_fixtures), "non-diagnostic reset")
        self._record(non_diag, "t0_and_later", "reset")
        commands = self._require_width_eight(self._native.bcrh(reset_rows), "BCRH command")
        self._record(non_diag, "t0_and_later", "bcrh")
        step_rows = self._require_width_eight(self._native.step(commands), "non-diagnostic step")
        self._record(non_diag, "t0_and_later", "step")
        diag_fixtures = self._require_width_eight(
            tuple(self._fixture(diag, presentations[name], ranks) for name in ordered_names),
            "diagnostic fixture batch",
        )
        diag_rows = self._require_width_eight(self._native.reset(diag_fixtures), "diagnostic reset")
        self._record(diag, "diagnostic", "reset")
        if not all(any(int(value) in (1, 2) for value in self._observation_constructor(row)["physical_token_states"]) for row in step_rows):  # type: ignore[arg-type]
            raise AdapterError("later state lacks a fixed or acquiring physical token")
        for row in diag_rows:
            raw = self._observation_constructor(row)
            legal = tuple(tuple(bool(value) for value in agent) for agent in raw["legal"])  # type: ignore[arg-type]
            if max(sum(int(agent[token]) for agent in legal) for token in range(4)) < 2:
                raise AdapterError("diagnostic state lacks null-plus-two-agent support")
        return {
            "roster_size": n,
            "failed_zone": zone,
            "fresh_identity": identity,
            "t0": tuple(self.public_observation(row, {handle: rank for handle, rank in ranks.items() if handle != diag.failed_entity}) for row in reset_rows),
            "later_fixed_or_acquiring": tuple(self.public_observation(row, {handle: rank for handle, rank in ranks.items() if handle != diag.failed_entity}) for row in step_rows),
            "diagnostic_null_tie": tuple(self.public_observation(row, {handle: rank for handle, rank in ranks.items() if handle != diag.failed_entity}) for row in diag_rows),
        }

    def host_call_ledger(self) -> tuple[Mapping[str, object], ...]:
        return tuple(asdict(row) for row in self._ledger)

    def require_complete_host_call_ledger(self) -> tuple[Mapping[str, object], ...]:
        rows = self.host_call_ledger()
        validate_host_call_ledger(rows)
        return rows

    def close(self) -> None:
        self._native.close()


def expected_adapter_ledger() -> tuple[Mapping[str, object], ...]:
    return tuple(asdict(row) for row in expected_host_call_ledger())
