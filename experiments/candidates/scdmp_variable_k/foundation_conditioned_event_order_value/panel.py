"""Fixed global FCEOV panel, sliced into bounded native batches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

import torch

from .contracts import (
    CANDIDATE_ACTIONS,
    FAILURE_LABELS,
    GRAPHS,
    HORIZON_TICKS,
    PANEL_FULL_SLICE_TAPES as SLICE_TAPE_COUNT,
    PANEL_MAX_NATIVE_WIDTH as SLICE_MAX_WIDTH,
    PANEL_SLICE_COUNT as SLICE_COUNT,
    PANEL_WIDTH as GLOBAL_PANEL_WIDTH,
    PanelCell,
    TAPE_COUNT as GLOBAL_TAPE_COUNT,
)
from .foundation import FrozenFoundation, lexicographic_argmax
from .host_bridge import (
    HostBridgeError, HostOutput, NativeBatch, RenewalLane, ResetLane, fixed_resets,
    validate_native_reset_outputs, validate_native_transition, validate_terminal_endpoints,
)
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
            isinstance(self.tape, bool) or not isinstance(self.tape, int)
            or isinstance(self.tick, bool) or not isinstance(self.tick, int)
            or not 0 <= self.tape < GLOBAL_TAPE_COUNT
            or not 0 <= self.tick < HORIZON_TICKS
        ):
            raise PanelContractError("tape address is outside the registered global inventory")
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
        if (
            isinstance(self.tape, bool) or not isinstance(self.tape, int)
            or not 0 <= self.tape < GLOBAL_TAPE_COUNT
        ):
            raise PanelContractError("global tape index differs")
        for component in COMPONENTS:
            values = self.component(component)
            if len(values) != HORIZON_TICKS:
                raise PanelContractError("disturbance tape is incomplete")
            magnitude = MAGNITUDES[component]
            if any(value not in (-magnitude, magnitude) for value in values):
                raise PanelContractError("disturbance value differs from the registered support")


@dataclass(frozen=True, slots=True)
class PanelLane:
    lane: int
    tape: int
    graph: str
    action_name: str
    action_index: int


@dataclass(frozen=True, slots=True)
class PanelSlice:
    index: int
    start_tape: int
    tape_count: int
    lanes: tuple[PanelLane, ...]

    @property
    def width(self) -> int:
        return len(self.lanes)


def build_panel_inventory() -> tuple[PanelLane, ...]:
    rows = []
    for tape in range(GLOBAL_TAPE_COUNT):
        for graph in GRAPHS:
            for name, action in CANDIDATE_ACTIONS.items():
                rows.append(PanelLane(len(rows), tape, graph, name, action))
    if len(rows) != GLOBAL_PANEL_WIDTH:
        raise RuntimeError("FCEOV global panel inventory width differs")
    return tuple(rows)


def build_panel_slices() -> tuple[PanelSlice, ...]:
    inventory = build_panel_inventory()
    cells_per_tape = len(GRAPHS) * len(CANDIDATE_ACTIONS)
    rows = []
    for index, start_tape in enumerate(range(0, GLOBAL_TAPE_COUNT, SLICE_TAPE_COUNT)):
        tape_count = min(SLICE_TAPE_COUNT, GLOBAL_TAPE_COUNT - start_tape)
        lane_start = start_tape * cells_per_tape
        lane_stop = lane_start + tape_count * cells_per_tape
        rows.append(PanelSlice(index, start_tape, tape_count, inventory[lane_start:lane_stop]))
    result = tuple(rows)
    if len(result) != SLICE_COUNT:
        raise RuntimeError("FCEOV slice count differs")
    return result


def validate_panel_slices(slices: Sequence[PanelSlice]) -> bool:
    rows = tuple(slices)
    if any(not isinstance(row, PanelSlice) for row in rows):
        raise PanelContractError("slice inventory must contain PanelSlice values")
    if rows != build_panel_slices():
        raise PanelContractError("slice inventory order or bounds differ")
    if any(row.width > SLICE_MAX_WIDTH for row in rows):
        raise PanelContractError("slice exceeds the native width ceiling")
    return True


def _registered_slice(value: PanelSlice) -> PanelSlice:
    if not isinstance(value, PanelSlice):
        raise PanelContractError("native panel execution requires a PanelSlice")
    slices = build_panel_slices()
    if isinstance(value.index, bool) or not isinstance(value.index, int) or not 0 <= value.index < len(slices):
        raise PanelContractError("slice index is outside the registered inventory")
    if value != slices[value.index]:
        raise PanelContractError("slice bounds, lanes, or order differ")
    return value


def materialize_disturbance_tapes(
    source: AddressRNG,
    *,
    start_tape: int = 0,
    tape_count: int = GLOBAL_TAPE_COUNT,
) -> tuple[DisturbanceTape, ...]:
    """Materialize a contiguous range while retaining global tape addresses."""

    if (
        isinstance(start_tape, bool) or not isinstance(start_tape, int)
        or isinstance(tape_count, bool) or not isinstance(tape_count, int)
        or start_tape < 0 or tape_count <= 0 or start_tape + tape_count > GLOBAL_TAPE_COUNT
    ):
        raise PanelContractError("disturbance tape range is outside the global inventory")
    rows = []
    for tape in range(start_tape, start_tape + tape_count):
        values: dict[str, tuple[float, ...]] = {}
        for component in COMPONENTS:
            magnitude = MAGNITUDES[component]
            values[component] = tuple(
                magnitude
                if source.uniforms("assay-disturbance", (tape, tick, component), 1)[0] >= 0.5
                else -magnitude
                for tick in range(HORIZON_TICKS)
            )
        rows.append(DisturbanceTape(tape, values["eta_v"], values["eta_y"], values["eta_omega"]))
    return tuple(rows)


def _validate_lane_types(rows: Sequence[PanelLane]) -> None:
    for row in rows:
        if not isinstance(row, PanelLane):
            raise PanelContractError("panel inventory must contain PanelLane values")
        if (
            isinstance(row.lane, bool) or not isinstance(row.lane, int)
            or isinstance(row.tape, bool) or not isinstance(row.tape, int)
            or isinstance(row.action_index, bool) or not isinstance(row.action_index, int)
        ):
            raise PanelContractError("panel inventory indices must be integers")


def validate_slice_tape_pairing(panel_slice: PanelSlice) -> bool:
    selected = _registered_slice(panel_slice)
    rows = selected.lanes
    _validate_lane_types(rows)
    for tape in range(selected.start_tape, selected.start_tape + selected.tape_count):
        tape_rows = tuple(row for row in rows if row.tape == tape)
        if len(tape_rows) != 6 or {row.graph for row in tape_rows} != set(GRAPHS):
            raise PanelContractError("each global tape must populate all six graph/action cells")
        for graph in GRAPHS:
            if {row.action_name for row in tape_rows if row.graph == graph} != set(CANDIDATE_ACTIONS):
                raise PanelContractError("a global tape is not shared across all candidate actions")
    return True


def validate_tape_pairing(inventory: Sequence[PanelLane]) -> bool:
    rows = tuple(inventory)
    _validate_lane_types(rows)
    if rows != build_panel_inventory():
        raise PanelContractError("global panel inventory order or contents differ")
    for panel_slice in build_panel_slices():
        validate_slice_tape_pairing(panel_slice)
    return True


def build_native_resets(panel_slice: PanelSlice) -> tuple[ResetLane, ...]:
    selected = _registered_slice(panel_slice)
    validate_slice_tape_pairing(selected)
    hr, rh = fixed_resets()
    result = tuple(hr if lane.graph == "HR" else rh for lane in selected.lanes)
    if len(result) != selected.width:
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


def execute_native_panel_slice(
    foundation: FrozenFoundation,
    tapes: Sequence[DisturbanceTape],
    panel_slice: PanelSlice,
) -> tuple[PanelCell, ...]:
    """Own one bounded native session and return that slice's complete terminal cells."""

    selected = _registered_slice(panel_slice)
    resets = build_native_resets(selected)
    with NativeBatch(resets) as session:
        return _execute_bound_session(session, foundation, tapes, selected, resets)


def preflight_native_panel_slice(panel_slice: PanelSlice) -> int:
    """Open, validate, and close one exact prospective bounded native session."""

    selected = _registered_slice(panel_slice)
    resets = build_native_resets(selected)
    with NativeBatch(resets) as session:
        try:
            validate_native_reset_outputs(
                resets, tuple(session.initial), width=selected.width,
                context=f"panel slice {selected.index} preflight",
            )
        except HostBridgeError as error:
            raise PanelContractError(str(error)) from error
    return selected.width


def preflight_native_panel_widths() -> tuple[int, ...]:
    """Validate all 24 native slice shapes without executing a mission."""

    return tuple(preflight_native_panel_slice(panel_slice) for panel_slice in build_panel_slices())


def _test_only_execute_panel_session(
    session: NativePanelSession,
    foundation: FrozenFoundation,
    tapes: Sequence[DisturbanceTape],
    panel_slice: PanelSlice,
) -> tuple[PanelCell, ...]:
    """Exercise one slice with a duck session; never a result route."""

    selected = _registered_slice(panel_slice)
    return _execute_bound_session(session, foundation, tapes, selected, build_native_resets(selected))


def _validate_slice_tapes(tapes: Sequence[DisturbanceTape], selected: PanelSlice) -> tuple[DisturbanceTape, ...]:
    rows = tuple(tapes)
    expected = tuple(range(selected.start_tape, selected.start_tape + selected.tape_count))
    if len(rows) != selected.tape_count or tuple(row.tape for row in rows) != expected:
        raise PanelContractError("slice disturbance tape inventory differs")
    for tape in rows:
        tape.validate()
    return rows


def _execute_bound_session(
    session: NativePanelSession,
    foundation: FrozenFoundation,
    tapes: Sequence[DisturbanceTape],
    panel_slice: PanelSlice,
    resets: Sequence[ResetLane],
) -> tuple[PanelCell, ...]:
    selected = _registered_slice(panel_slice)
    tape_rows = _validate_slice_tapes(tapes, selected)
    tapes_by_id = {row.tape: row for row in tape_rows}
    width = selected.width
    try:
        validate_native_reset_outputs(
            tuple(resets), tuple(session.initial), width=width, context=f"panel slice {selected.index}"
        )
    except HostBridgeError as error:
        raise PanelContractError(str(error)) from error
    foundation.validate_immutable()
    outputs = session.renew(tuple(
        _renewal_row(lane.action_index, tapes_by_id[lane.tape], 0, active=True)
        for lane in selected.lanes
    ))
    try:
        validate_native_transition(
            tuple(session.initial), tuple(outputs), width=width, context=f"panel slice {selected.index}"
        )
    except HostBridgeError as error:
        raise PanelContractError(str(error)) from error
    query_count = 0
    query_ceiling = width * 27
    while any(row.active for row in outputs):
        active = tuple(index for index, row in enumerate(outputs) if row.active)
        observations = torch.tensor(
            tuple(outputs[index].observation for index in active), dtype=torch.float32
        )
        with torch.no_grad():
            action_tensor = lexicographic_argmax(foundation(observations))
        if action_tensor.shape != (len(active),):
            raise PanelContractError("foundation action batch differs from active lanes")
        actions = action_tensor.tolist()
        query_count += len(active)
        if query_count > query_ceiling:
            raise PanelContractError("assay foundation-query ceiling exceeded")
        by_lane = dict(zip(active, actions))
        if len(by_lane) != len(active):
            raise PanelContractError("foundation action batch differs from active lanes")
        rows = tuple(
            _renewal_row(
                by_lane.get(index, 0), tapes_by_id[lane.tape], outputs[index].tick,
                active=index in by_lane,
            )
            for index, lane in enumerate(selected.lanes)
        )
        following = session.renew(rows)
        try:
            validate_native_transition(
                tuple(outputs), tuple(following), width=width, context=f"panel slice {selected.index}"
            )
        except HostBridgeError as error:
            raise PanelContractError(str(error)) from error
        outputs = following
    foundation.validate_immutable()
    try:
        validate_terminal_endpoints(tuple(outputs), context=f"panel slice {selected.index}")
    except HostBridgeError as error:
        raise PanelContractError(str(error)) from error
    cells = tuple(
        PanelCell(
            lane.tape, lane.graph, lane.action_name, lane.action_index, output.terminal,
            output.safe_dock, output.dock_tick,
            tuple(label for label in FAILURE_LABELS if bool(getattr(output, label))),
        )
        for lane, output in zip(selected.lanes, outputs)
    )
    validate_panel_slice_cells(cells, selected)
    return cells


def validate_panel_slice_cells(
    cells: Sequence[PanelCell], panel_slice: PanelSlice,
) -> bool:
    """Validate one complete terminal slice loaded from execution or resume."""

    selected = _registered_slice(panel_slice)
    rows = tuple(cells)
    if any(not isinstance(row, PanelCell) for row in rows):
        raise PanelContractError("panel slice must contain PanelCell values")
    expected = tuple(
        (lane.tape, lane.graph, lane.action_name, lane.action_index)
        for lane in selected.lanes
    )
    observed = tuple((row.tape, row.graph, row.action_name, row.action_index) for row in rows)
    if observed != expected:
        raise PanelContractError("panel slice cell order, identity, or completeness differs")
    for row in rows:
        if row.terminal is not True or not isinstance(row.safe_dock, bool):
            raise PanelContractError("panel slice terminal flags differ")
        if not isinstance(row.failures, tuple):
            raise PanelContractError("panel slice failure labels must be a tuple")
        if (
            len(set(row.failures)) != len(row.failures)
            or any(label not in FAILURE_LABELS for label in row.failures)
            or row.failures != tuple(label for label in FAILURE_LABELS if label in row.failures)
        ):
            raise PanelContractError("panel slice failure labels differ")
        if row.safe_dock:
            if (
                isinstance(row.dock_tick, bool) or not isinstance(row.dock_tick, int)
                or not 1 <= row.dock_tick <= HORIZON_TICKS or row.failures
            ):
                raise PanelContractError("safe panel slice endpoint is incoherent")
        elif row.dock_tick is not None:
            raise PanelContractError("unsafe panel slice endpoint is incoherent")
    return True


def validate_complete_panel_cells(cells: Sequence[PanelCell]) -> bool:
    rows = tuple(cells)
    if len(rows) != GLOBAL_PANEL_WIDTH:
        raise PanelContractError("global panel cell order, identity, or completeness differs")
    lane_start = 0
    for panel_slice in build_panel_slices():
        lane_stop = lane_start + panel_slice.width
        validate_panel_slice_cells(rows[lane_start:lane_stop], panel_slice)
        lane_start = lane_stop
    return True


def aggregate_panel_slices(slices: Sequence[Sequence[PanelCell]]) -> tuple[PanelCell, ...]:
    """Flatten and validate all slices; perform no inference and publish nothing."""

    rows = tuple(tuple(item) for item in slices)
    expected_slices = build_panel_slices()
    if len(rows) != SLICE_COUNT:
        raise PanelContractError("global panel slice count differs")
    for cells, panel_slice in zip(rows, expected_slices):
        validate_panel_slice_cells(cells, panel_slice)
    result = tuple(cell for cells in rows for cell in cells)
    validate_complete_panel_cells(result)
    return result


if GLOBAL_PANEL_WIDTH != 3_372:
    raise RuntimeError("FCEOV global panel width drifted")
if tuple(row.width for row in build_panel_slices()) != (SLICE_MAX_WIDTH,) * 23 + (60,):
    raise RuntimeError("FCEOV native slice widths drifted")


__all__ = [
    "COMPONENTS", "DisturbanceTape", "GLOBAL_PANEL_WIDTH", "GLOBAL_TAPE_COUNT",
    "NativePanelSession", "PanelContractError", "PanelLane", "PanelSlice", "SLICE_COUNT",
    "SLICE_MAX_WIDTH", "SLICE_TAPE_COUNT", "TapeAddress", "aggregate_panel_slices",
    "build_native_resets", "build_panel_inventory", "build_panel_slices",
    "execute_native_panel_slice", "materialize_disturbance_tapes", "mission_utility",
    "preflight_native_panel_slice", "preflight_native_panel_widths", "validate_complete_panel_cells",
    "validate_panel_slice_cells", "validate_panel_slices", "validate_slice_tape_pairing",
    "validate_tape_pairing",
]
