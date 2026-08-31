"""Fixed width-144 FCEOV panel inventory and native-batch execution seam."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

import torch

from .contracts import (
    CANDIDATE_ACTIONS,
    FAILURE_LABELS,
    GRAPHS,
    HORIZON_TICKS,
    PANEL_WIDTH,
    PanelCell,
    TAPE_COUNT,
)
from .foundation import FrozenFoundation, lexicographic_argmax
from .host_bridge import (
    HostBridgeError, HostOutput, NativeBatch, RenewalLane, validate_native_reset_outputs,
    validate_native_transition, validate_terminal_endpoints,
)
from .host_bridge import ResetLane, fixed_resets
from .rng import AddressRNG


class PanelContractError(ValueError):
    pass


COMPONENTS = ("eta_v", "eta_y", "eta_omega")
MAGNITUDES = {"eta_v": 0.003, "eta_y": 0.002, "eta_omega": 0.004}


@dataclass(frozen=True, slots=True)
class TapeAddress:
    tape: int
    tick: int
    component: str

    def validate(self) -> None:
        if (
            isinstance(self.tape, bool)
            or not isinstance(self.tape, int)
            or isinstance(self.tick, bool)
            or not isinstance(self.tick, int)
            or not 0 <= self.tape < TAPE_COUNT
            or not 0 <= self.tick < HORIZON_TICKS
        ):
            raise PanelContractError("tape address is outside the registered inventory")
        if self.component not in COMPONENTS:
            raise PanelContractError("tape component is unregistered")


@dataclass(frozen=True, slots=True)
class DisturbanceTape:
    tape: int
    eta_v: tuple[float, ...]
    eta_y: tuple[float, ...]
    eta_omega: tuple[float, ...]

    def component(self, name: str) -> tuple[float, ...]:
        if name not in COMPONENTS:
            raise PanelContractError("tape component is unregistered")
        return getattr(self, name)

    def validate(self) -> None:
        if isinstance(self.tape, bool) or not isinstance(self.tape, int) or not 0 <= self.tape < TAPE_COUNT:
            raise PanelContractError("tape index differs")
        for component in COMPONENTS:
            values = self.component(component)
            if len(values) != HORIZON_TICKS:
                raise PanelContractError("disturbance tape is incomplete")
            magnitude = MAGNITUDES[component]
            if any(value not in (-magnitude, magnitude) for value in values):
                raise PanelContractError("disturbance value differs from the registered support")


def materialize_disturbance_tapes(source: AddressRNG) -> tuple[DisturbanceTape, ...]:
    rows = []
    for tape in range(TAPE_COUNT):
        values: dict[str, tuple[float, ...]] = {}
        for component in COMPONENTS:
            magnitude = MAGNITUDES[component]
            values[component] = tuple(
                magnitude if source.uniforms("assay-disturbance", (tape, tick, component), 1)[0] >= 0.5 else -magnitude
                for tick in range(HORIZON_TICKS)
            )
        rows.append(DisturbanceTape(tape, values["eta_v"], values["eta_y"], values["eta_omega"]))
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class PanelLane:
    lane: int
    tape: int
    graph: str
    action_name: str
    action_index: int


def build_panel_inventory() -> tuple[PanelLane, ...]:
    rows = []
    for tape in range(TAPE_COUNT):
        for graph in GRAPHS:
            for name, action in CANDIDATE_ACTIONS.items():
                rows.append(PanelLane(len(rows), tape, graph, name, action))
    if len(rows) != PANEL_WIDTH:
        raise RuntimeError("FCEOV panel inventory width differs")
    return tuple(rows)


def validate_tape_pairing(inventory: Sequence[PanelLane]) -> bool:
    rows = tuple(inventory)
    for row in rows:
        if not isinstance(row, PanelLane):
            raise PanelContractError("panel inventory must contain PanelLane values")
        if (
            isinstance(row.lane, bool)
            or not isinstance(row.lane, int)
            or isinstance(row.tape, bool)
            or not isinstance(row.tape, int)
            or isinstance(row.action_index, bool)
            or not isinstance(row.action_index, int)
        ):
            raise PanelContractError("panel inventory indices must be integers")
    if rows != build_panel_inventory():
        raise PanelContractError("panel inventory order or contents differ")
    for tape in range(TAPE_COUNT):
        tape_rows = tuple(row for row in rows if row.tape == tape)
        if len(tape_rows) != 6 or {row.graph for row in tape_rows} != set(GRAPHS):
            raise PanelContractError("each tape must populate all six graph/action cells")
        for graph in GRAPHS:
            if {row.action_name for row in tape_rows if row.graph == graph} != set(CANDIDATE_ACTIONS):
                raise PanelContractError("a tape is not shared across all candidate actions")
    return True


def build_native_resets(inventory: Sequence[PanelLane] | None = None) -> tuple[ResetLane, ...]:
    lanes = build_panel_inventory() if inventory is None else tuple(inventory)
    validate_tape_pairing(lanes)
    hr, rh = fixed_resets()
    result = tuple(hr if lane.graph == "HR" else rh for lane in lanes)
    if len(result) != PANEL_WIDTH:
        raise RuntimeError("native reset inventory width differs")
    return result


def mission_utility(*, safe_dock: bool, dock_tick: int | None) -> float:
    if not safe_dock:
        if dock_tick is not None:
            raise PanelContractError("nonsafe mission cannot carry a dock tick")
        return 0.0
    if isinstance(dock_tick, bool) or not isinstance(dock_tick, int) or not 1 <= dock_tick <= HORIZON_TICKS:
        raise PanelContractError("safe dock tick is outside the mission")
    return 1.0 - dock_tick / HORIZON_TICKS


@runtime_checkable
class NativePanelSession(Protocol):
    initial: tuple[HostOutput, ...]
    @property
    def active_lanes(self) -> tuple[int, ...]: ...
    def renew(self, rows: Sequence[RenewalLane]) -> tuple[HostOutput, ...]: ...
    def close(self) -> None: ...


def _renewal_row(action: int, tape: DisturbanceTape, start: int, *, active: bool) -> RenewalLane:
    def segment(component: str) -> tuple[float, ...]:
        values = tape.component(component)
        return tuple(values[min(start + offset, HORIZON_TICKS - 1)] for offset in range(13))
    return RenewalLane(action, segment("eta_v"), segment("eta_y"), segment("eta_omega"), active)


def execute_native_panel(
    foundation: FrozenFoundation,
    tapes: Sequence[DisturbanceTape],
) -> tuple[PanelCell, ...]:
    """Create and own the exact native width-144 HR/RH session.

    This callable is intentionally absent from the implementation-phase CLI.
    A later result operation may call it only after its own scientific freeze.
    """

    lanes = build_panel_inventory()
    resets = build_native_resets(lanes)
    with NativeBatch(resets) as session:
        return _execute_bound_session(session, foundation, tapes, lanes, resets)


def preflight_native_panel_session() -> int:
    """Open, validate, and close the exact prospective width-144 native session."""

    resets = build_native_resets()
    with NativeBatch(resets) as session:
        try:
            validate_native_reset_outputs(
                resets, tuple(session.initial), width=PANEL_WIDTH, context="panel preflight"
            )
        except HostBridgeError as error:
            raise PanelContractError(str(error)) from error
    return PANEL_WIDTH


def _test_only_execute_panel_session(
    session: NativePanelSession,
    foundation: FrozenFoundation,
    tapes: Sequence[DisturbanceTape],
) -> tuple[PanelCell, ...]:
    """Exercise panel mechanics with a duck session; never a result route."""

    lanes = build_panel_inventory()
    return _execute_bound_session(session, foundation, tapes, lanes, build_native_resets(lanes))


def _execute_bound_session(
    session: NativePanelSession,
    foundation: FrozenFoundation,
    tapes: Sequence[DisturbanceTape],
    lanes: Sequence[PanelLane],
    resets: Sequence[ResetLane],
) -> tuple[PanelCell, ...]:
    """Execute only a session whose production owner supplied exact resets."""

    lanes = tuple(lanes)
    validate_tape_pairing(lanes)
    tape_rows = tuple(tapes)
    if len(tape_rows) != TAPE_COUNT or tuple(row.tape for row in tape_rows) != tuple(range(TAPE_COUNT)):
        raise PanelContractError("disturbance tape inventory differs")
    for tape in tape_rows:
        tape.validate()
    try:
        validate_native_reset_outputs(
            tuple(resets), tuple(session.initial), width=PANEL_WIDTH, context="panel"
        )
    except HostBridgeError as error:
        raise PanelContractError(str(error)) from error
    foundation.validate_immutable()
    outputs = session.renew(
        tuple(_renewal_row(lane.action_index, tape_rows[lane.tape], 0, active=True) for lane in lanes)
    )
    previous = session.initial
    try:
        validate_native_transition(tuple(previous), tuple(outputs), width=PANEL_WIDTH, context="panel")
    except HostBridgeError as error:
        raise PanelContractError(str(error)) from error
    query_count = 0
    while any(row.active for row in outputs):
        active = tuple(index for index, row in enumerate(outputs) if row.active)
        observations = torch.tensor(tuple(outputs[index].observation for index in active), dtype=torch.float32)
        with torch.no_grad():
            action_tensor = lexicographic_argmax(foundation(observations))
        if action_tensor.shape != (len(active),):
            raise PanelContractError("foundation action batch differs from active lanes")
        actions = action_tensor.tolist()
        query_count += len(active)
        if query_count > 144 * 27:
            raise PanelContractError("assay foundation-query ceiling exceeded")
        by_lane = dict(zip(active, actions))
        if len(by_lane) != len(active):
            raise PanelContractError("foundation action batch differs from active lanes")
        rows = tuple(
            _renewal_row(
                by_lane.get(index, 0),
                tape_rows[lane.tape],
                outputs[index].tick,
                active=index in by_lane,
            )
            for index, lane in enumerate(lanes)
        )
        following = session.renew(rows)
        try:
            validate_native_transition(tuple(outputs), tuple(following), width=PANEL_WIDTH, context="panel")
        except HostBridgeError as error:
            raise PanelContractError(str(error)) from error
        previous, outputs = outputs, following
    foundation.validate_immutable()
    if query_count > 144 * 27:
        raise PanelContractError("assay foundation-query ceiling exceeded")
    try:
        validate_terminal_endpoints(tuple(outputs), context="panel")
    except HostBridgeError as error:
        raise PanelContractError(str(error)) from error
    cells = []
    for lane, output in zip(lanes, outputs):
        failures = tuple(label for label in FAILURE_LABELS if bool(getattr(output, label)))
        cells.append(PanelCell(
            lane.tape, lane.graph, lane.action_name, lane.action_index, output.terminal,
            output.safe_dock, output.dock_tick, failures,
        ))
    if any(not row.terminal for row in cells):
        raise PanelContractError("partial panel cannot become an analysis input")
    return tuple(cells)


__all__ = [
    "COMPONENTS", "DisturbanceTape", "NativePanelSession", "PanelContractError", "PanelLane",
    "TapeAddress", "build_native_resets", "build_panel_inventory", "execute_native_panel", "materialize_disturbance_tapes",
    "preflight_native_panel_session",
    "mission_utility", "validate_tape_pairing",
]
