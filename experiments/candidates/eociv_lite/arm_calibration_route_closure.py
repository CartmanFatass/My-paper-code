"""Proof-sized EOCIV-LITE intervention/calibration/route closure.

This isolated rational unit configuration validates whether four-arm treatment
wiring is interpretable.  It does not estimate return or targeting value.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping, Sequence


ARMS = ("LS", "LR", "CS", "CR")
W_MINUS_FIELDS = (
    "lifecycle_receipt",
    "roster_receipt",
    "owner_epoch",
    "pre_body_observation",
    "route_bucket",
    "age_bucket",
    "timing_bucket",
    "envelope_bucket",
    "prior_gate_history",
    "selector_recurrence",
    "calibration_constant",
    "valve_tape",
)
PROHIBITED_SELECTOR_FIELDS = (
    "body",
    "body_metadata",
    "arm_bit",
    "reward",
    "post_reveal_state",
    "fold_outcome",
    "owner_private_proxy",
    "global_rng",
)


class ClosureError(ValueError):
    """The frozen intervention contract is not closed."""


@dataclass(frozen=True)
class PoolManifest:
    name: str
    ancestry_root: str
    sample_ids: tuple[str, ...]


@dataclass(frozen=True)
class SupportCell:
    cell: str
    envelope: str
    cost: int
    native_neutral: bytes | None
    hard_open: bool


@dataclass(frozen=True)
class CalibrationRow:
    sample_id: str
    cell: str
    score: Fraction
    critical: bool
    payload_label: int


@dataclass(frozen=True)
class ControlTape:
    cell: str
    opportunity: int
    tape: Fraction
    sham_score: Fraction


@dataclass(frozen=True)
class OpportunityClock:
    trigger_id: str
    cluster_id: str
    horizon: int
    opportunity: int
    physical_tick: int
    cell: str
    cell_opportunity: int
    declared_control_open: bool
    previous_open: bool
    open_run_position: int
    close_run_position: int


@dataclass(frozen=True)
class CriticalEdge:
    source: str
    sink: str
    information_class: str
    deadline: int
    live_paths: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class UnitConfig:
    trigger_id: str
    cluster_id: str
    horizon: int
    clocks: tuple[OpportunityClock, ...]
    pools: tuple[PoolManifest, ...]
    support_cells: tuple[SupportCell, ...]
    calibration_rows: tuple[CalibrationRow, ...]
    threshold_grid: tuple[Fraction, ...]
    frozen_q_by_cell: tuple[tuple[str, Fraction], ...]
    control_table: tuple[ControlTape, ...]
    critical_graph: tuple[CriticalEdge, ...]
    parameter_routes: tuple[tuple[str, str], ...]
    recurrent_routes: tuple[tuple[str, str], ...]
    legal_payloads: tuple[bytes, bytes]


@dataclass(frozen=True)
class Actuation:
    arm: str
    route: str
    payload: bytes
    decision_source: str


def build_unit_config() -> UnitConfig:
    trigger = "receiver-opportunity-v1"
    cluster = "cluster-rational-00"
    rows = tuple(
        CalibrationRow(
            sample_id=f"cal-{cell}-{index}",
            cell=cell,
            score=score,
            critical=(score == Fraction(3, 4)),
            payload_label=index % 2,
        )
        for cell in ("route-a", "route-b")
        for index, score in enumerate(
            (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4))
        )
    )
    control_table = tuple(
        ControlTape(cell, index, tape, sham)
        for cell, sham_values in (
            ("route-a", (Fraction(1, 2), Fraction(0), Fraction(3, 4), Fraction(1, 4))),
            ("route-b", (Fraction(3, 4), Fraction(1, 4), Fraction(0), Fraction(1, 2))),
        )
        for index, (tape, sham) in enumerate(
            zip((Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)), sham_values)
        )
    )
    clocks = tuple(
        OpportunityClock(trigger, cluster, 8, global_index, 10 + global_index * 3, cell,
                         index, index > 0, index not in (0, 1), index if index else 0,
                         1 if index == 0 else 0)
        for global_index, (cell, index) in enumerate(
            (item.cell, item.opportunity) for item in control_table
        )
    )
    return UnitConfig(
        trigger_id=trigger,
        cluster_id=cluster,
        horizon=8,
        clocks=clocks,
        pools=(
            PoolManifest("D_fit", "ancestor-fit", ("fit-0", "fit-1")),
            PoolManifest("D_cal", "ancestor-cal", tuple(r.sample_id for r in rows)),
            PoolManifest("D_policy", "ancestor-policy", ("policy-0", "policy-1")),
            PoolManifest("D_focal", "ancestor-focal", ("focal-0", "focal-1")),
        ),
        support_cells=(
            SupportCell("route-a", "env-a", 2, b"NATIVE-NEUTRAL-A", False),
            SupportCell("route-b", "env-b", 3, b"NATIVE-NEUTRAL-B", False),
            SupportCell("critical-no-neutral", "env-critical", 5, None, True),
        ),
        calibration_rows=rows,
        threshold_grid=tuple(Fraction(n, 4) for n in range(5)),
        frozen_q_by_cell=tuple(_q_from_rows(rows, Fraction(1, 4)).items()),
        control_table=control_table,
        critical_graph=(
            CriticalEdge(
                "coordinator",
                "receiver",
                "deadline-bearing-intent",
                6,
                (("coordinator", "receiver"),),
            ),
        ),
        parameter_routes=(
            ("theta_valve", "valve_loss"),
            ("kappa_c", "valve_decision"),
            ("theta_backbone", "team_loss"),
        ),
        recurrent_routes=(
            ("W_minus", "selector"),
            ("selector", "actuation"),
            ("body", "actuation"),
            ("actuation", "receiver_recurrence"),
        ),
        legal_payloads=(b"REAL-PAYLOAD-ALPHA", b"REAL-PAYLOAD-OMEGA"),
    )


def _reachable(edges: Sequence[tuple[str, str]], start: str, end: str) -> bool:
    frontier = [start]
    seen: set[str] = set()
    while frontier:
        node = frontier.pop()
        if node == end:
            return True
        if node in seen:
            continue
        seen.add(node)
        frontier.extend(dst for src, dst in edges if src == node)
    return False


def selector_view(raw: Mapping[str, object]) -> tuple[tuple[str, object], ...]:
    extras = set(raw).difference(W_MINUS_FIELDS)
    if extras:
        raise ClosureError(f"selector field outside W_minus: {sorted(extras)!r}")
    missing = set(W_MINUS_FIELDS).difference(raw)
    if missing:
        raise ClosureError(f"incomplete W_minus: {sorted(missing)!r}")
    return tuple((name, raw[name]) for name in W_MINUS_FIELDS)


def calibration_threshold(config: UnitConfig) -> Fraction:
    feasible: list[tuple[int, Fraction]] = []
    for threshold in config.threshold_grid:
        decisions = tuple(row.score >= threshold for row in config.calibration_rows)
        open_count = sum(decisions)
        close_count = len(decisions) - open_count
        critical_close = sum(
            row.critical and not decision
            for row, decision in zip(config.calibration_rows, decisions)
        )
        cell_positive = all(
            any(row.score >= threshold for row in config.calibration_rows if row.cell == cell)
            and any(row.score < threshold for row in config.calibration_rows if row.cell == cell)
            for cell in {row.cell for row in config.calibration_rows}
        )
        if open_count >= 4 and close_count >= 2 and critical_close == 0 and cell_positive:
            feasible.append((open_count, threshold))
    if not feasible:
        raise ClosureError("no feasible predeclared calibration threshold")
    return min(feasible, key=lambda item: (-item[0], item[1]))[1]


def _q_from_rows(rows: Sequence[CalibrationRow], threshold: Fraction) -> dict[str, Fraction]:
    result: dict[str, Fraction] = {}
    for cell in sorted({row.cell for row in rows}):
        cell_rows = tuple(row for row in rows if row.cell == cell)
        result[cell] = Fraction(sum(row.score < threshold for row in cell_rows), len(cell_rows))
    return result


def derive_q_from_calibration(config: UnitConfig, threshold: Fraction) -> dict[str, Fraction]:
    return _q_from_rows(config.calibration_rows, threshold)


def learned_open(score: Fraction, threshold: Fraction) -> bool:
    return score >= threshold


def frozen_q(config: UnitConfig) -> dict[str, Fraction]:
    return dict(config.frozen_q_by_cell)


def _control_row(config: UnitConfig, cell: str, opportunity: int) -> ControlTape:
    matches = tuple(row for row in config.control_table if (row.cell, row.opportunity) == (cell, opportunity))
    if len(matches) != 1:
        raise ClosureError(f"unsupported control opportunity: {cell}/{opportunity}")
    return matches[0]


def control_open(config: UnitConfig, cell: str, opportunity: int) -> bool:
    row = _control_row(config, cell, opportunity)
    return row.tape >= frozen_q(config)[cell]


def sham_score(config: UnitConfig, cell: str, opportunity: int) -> Fraction:
    return _control_row(config, cell, opportunity).sham_score


def support_cell(config: UnitConfig, cell: str) -> SupportCell:
    matches = tuple(item for item in config.support_cells if item.cell == cell)
    if len(matches) != 1:
        raise ClosureError(f"support cell cardinality is not one: {cell}")
    return matches[0]


def actuate(
    config: UnitConfig,
    arm: str,
    lifecycle_eligible: bool,
    cell: str,
    body: bytes,
    d_learned: bool,
    d_control: bool,
) -> Actuation:
    if arm not in ARMS:
        raise ClosureError(f"unknown arm: {arm}")
    if not lifecycle_eligible:
        return Actuation(arm, "SUPPRESSED", b"", "G=0")
    support = support_cell(config, cell)
    if support.native_neutral is None:
        if not support.hard_open or not critical_paths_closed(config):
            raise ClosureError("unsupported neutral without HARD_OPEN")
        return Actuation(arm, "REAL", body, "HARD_OPEN")
    if arm in ("LR", "CR"):
        return Actuation(arm, "REAL", body, "ALWAYS_REAL")
    decision = d_learned if arm == "LS" else d_control
    source = "D_L" if arm == "LS" else "D_C"
    return Actuation(arm, "REAL" if decision else "NEUTRAL", body if decision else support.native_neutral, source)


def _wire(value: object) -> object:
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, bytes):
        return value.decode("ascii")
    if isinstance(value, tuple):
        return [_wire(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _wire(item) for key, item in value.items()}
    return value


def canonical_bytes(value: object) -> bytes:
    return json.dumps(_wire(value), sort_keys=True, separators=(",", ":")).encode("utf-8")


def receiver_trace(payload: bytes, envelope: str, cost: int) -> bytes:
    return canonical_bytes(
        {
            "actor_input": payload,
            "attention_write": (envelope, payload),
            "cache_write": (cost, payload),
            "normalization_write": (len(payload), envelope),
            "critic_write": (payload, cost),
            "auxiliary_write": (envelope, cost),
            "recurrent_write": (payload, envelope, cost),
        }
    )


def pre_sampling_trace(actuation: Actuation, envelope: str, cost: int) -> bytes:
    return receiver_trace(actuation.payload, envelope, cost)


def action_kernel(trace: bytes) -> tuple[Fraction, Fraction]:
    first = Fraction(sum(trace) % 17 + 1, 20)
    return (first, Fraction(1) - first)


def reset_selector_state(cluster_id: str) -> tuple[str, tuple[int, int]]:
    return (cluster_id, (0, 0))


def route_closure_closed(config: UnitConfig) -> bool:
    forbidden = (("theta_valve", "team_loss"), ("kappa_c", "team_loss"),
                 ("theta_backbone", "valve_loss"))
    if any(_reachable(config.parameter_routes, src, dst) for src, dst in forbidden):
        return False
    edges = set(config.recurrent_routes)
    body_targets = {dst for src, dst in edges if src == "body"}
    recurrence_sources = {src for src, dst in edges if dst == "receiver_recurrence"}
    return (
        not _reachable(config.recurrent_routes, "body", "selector")
        and body_targets == {"actuation"}
        and recurrence_sources == {"actuation"}
        and ("actuation", "receiver_recurrence") in edges
    )


def clock_run_law_closed(config: UnitConfig) -> bool:
    if [clock.opportunity for clock in config.clocks] != list(range(config.horizon)):
        return False
    if any(later.physical_tick <= earlier.physical_tick for earlier, later in zip(config.clocks, config.clocks[1:])):
        return False
    for cell in dict(config.frozen_q_by_cell):
        clocks = tuple(clock for clock in config.clocks if clock.cell == cell)
        if [clock.cell_opportunity for clock in clocks] != list(range(4)):
            return False
        previous = False
        open_run = close_run = 0
        for clock in clocks:
            decision = control_open(config, cell, clock.cell_opportunity)
            open_run, close_run = (open_run + 1, 0) if decision else (0, close_run + 1)
            if (clock.declared_control_open, clock.previous_open,
                clock.open_run_position, clock.close_run_position) != (
                    decision, previous, open_run, close_run):
                return False
            previous = decision
    return True


def critical_paths_closed(config: UnitConfig) -> bool:
    if not config.critical_graph:
        return False
    for edge in config.critical_graph:
        if edge.deadline > config.horizon or not edge.live_paths:
            return False
        if any(
            not any((src, dst) == (edge.source, edge.sink) for src, dst in zip(path, path[1:]))
            for path in edge.live_paths
        ):
            return False
    return True


def validate_config(config: UnitConfig) -> None:
    if config.horizon != len(config.clocks):
        raise ClosureError("incomplete opportunity clock")
    if any(clock.trigger_id != config.trigger_id or clock.cluster_id != config.cluster_id for clock in config.clocks):
        raise ClosureError("clock identity drift")
    roots = tuple(pool.ancestry_root for pool in config.pools)
    samples = tuple(sample for pool in config.pools for sample in pool.sample_ids)
    if len(config.pools) != 4 or len(set(roots)) != 4 or len(set(samples)) != len(samples):
        raise ClosureError("ancestry pools are not disjoint")
    if any(cell.native_neutral is None and not cell.hard_open for cell in config.support_cells):
        raise ClosureError("illegal missing native neutral")
    threshold = calibration_threshold(config)
    if derive_q_from_calibration(config, threshold) != frozen_q(config):
        raise ClosureError("frozen q_c drifted from D_cal")
    if not route_closure_closed(config):
        raise ClosureError("gradient or pre-actuation route bypass")
    if not clock_run_law_closed(config):
        raise ClosureError("opportunity clock or run law drift")
    if not critical_paths_closed(config):
        raise ClosureError("critical edge is not on every live path before deadline")


def _payload_pair_closed(config: UnitConfig) -> bool:
    cell = support_cell(config, "route-a")
    masked = tuple(
        actuate(config, "LS", True, cell.cell, body, False, True)
        for body in config.legal_payloads
    )
    traces = tuple(receiver_trace(item.payload, cell.envelope, cell.cost) for item in masked)
    real = actuate(config, "LS", True, cell.cell, config.legal_payloads[0], True, False)
    return traces[0] == traces[1] and real.payload == config.legal_payloads[0]


def always_real_equivalent(config: UnitConfig, lr_body: bytes, cr_body: bytes) -> bool:
    cell = support_cell(config, "route-b")
    lr = actuate(config, "LR", True, cell.cell, lr_body, False, False)
    cr = actuate(config, "CR", True, cell.cell, cr_body, True, True)
    lr_trace = pre_sampling_trace(lr, cell.envelope, cell.cost)
    cr_trace = pre_sampling_trace(cr, cell.envelope, cell.cost)
    return lr_trace == cr_trace and action_kernel(lr_trace) == action_kernel(cr_trace)


def _arm_mapping_closed(config: UnitConfig) -> bool:
    body = config.legal_payloads[0]
    for eligible in (False, True):
        for cell in ("route-a", "critical-no-neutral"):
            for arm in ARMS:
                for d_l in (False, True):
                    for d_c in (False, True):
                        result = actuate(config, arm, eligible, cell, body, d_l, d_c)
                        if not eligible and result.route != "SUPPRESSED":
                            return False
                        if eligible and cell == "critical-no-neutral" and result.decision_source != "HARD_OPEN":
                            return False
                        if eligible and cell == "route-a":
                            expected_real = arm in ("LR", "CR") or (d_l if arm == "LS" else d_c)
                            if (result.route == "REAL") != expected_real:
                                return False
    return True


def _outcome_null_closed(config: UnitConfig, threshold: Fraction, q: Mapping[str, Fraction]) -> bool:
    for cell in q:
        rows = tuple(row for row in config.calibration_rows if row.cell == cell)
        learned = tuple(learned_open(row.score, threshold) for row in rows)
        control = tuple(control_open(config, cell, opportunity) for opportunity in range(4))
        sham = tuple(sham_score(config, cell, opportunity) for opportunity in range(4))
        support = tuple(sorted(row.score for row in rows))
        if learned != control or tuple(sorted(sham)) != support:
            return False
        if sum(control) != 3 or {row.payload_label for row in rows} != {0, 1}:
            return False
    return all(cell.cost > 0 and cell.envelope for cell in config.support_cells)


def _mutation_results() -> dict[str, str]:
    raw = {field: 0 for field in W_MINUS_FIELDS}
    results: dict[str, str] = {}
    for field in PROHIBITED_SELECTOR_FIELDS:
        try:
            selector_view({**raw, field: "attempt"})
        except ClosureError:
            results[field] = "FAIL_CLOSED"
        else:
            results[field] = "LEAKED"
    return results


def run_unit_closure(config: UnitConfig | None = None) -> dict[str, object]:
    config = config or build_unit_config()
    validate_config(config)
    threshold = calibration_threshold(config)
    q = frozen_q(config)
    mutations = _mutation_results()
    closures = {
        "payload_pair_byte_closure": _payload_pair_closed(config),
        "always_real_pre_sampling_equivalence": always_real_equivalent(
            config, config.legal_payloads[0], config.legal_payloads[0]
        ),
        "exhaustive_arm_mapping": _arm_mapping_closed(config),
        "zero_jacobian_and_pre_actuation": route_closure_closed(config),
        "outcome_sealed_null_conformance": _outcome_null_closed(config, threshold, q),
    }
    if not all(closures.values()) or set(mutations.values()) != {"FAIL_CLOSED"}:
        raise ClosureError("deterministic closure failed")
    return {
        "candidate": "CAND-VAP-EOCIV-LITE@adversarial-revision-v8",
        "treatment": "EOCIV-LITE-V8-ARM-CALIBRATION-ROUTE-CLOSURE",
        "terminal": "PASS_INTERVENTION_CLOSURE",
        "actual_instance_status": "ABSENT_ACTIVE_EOCIV_OBJECTS",
        "threshold": threshold,
        "q_c": q,
        "pool_roots": tuple(pool.ancestry_root for pool in config.pools),
        "learned_open_sequences": {
            cell: tuple(
                learned_open(row.score, threshold)
                for row in config.calibration_rows
                if row.cell == cell
            )
            for cell in q
        },
        "control_open_sequences": {
            cell: tuple(control_open(config, cell, opportunity) for opportunity in range(4))
            for cell in q
        },
        "closures": closures,
        "route_predicates": {
            "clock_run_law": clock_run_law_closed(config),
            "critical_all_live_paths": critical_paths_closed(config),
        },
        "mutations": mutations,
        "minimum_actual_objects": (
            "registered lifecycle opportunity clock and W_minus schema",
            "support-native neutral kernel with HARD_OPEN coverage",
            "four disjoint ancestry pools plus frozen critical and route graphs",
        ),
        "future_explorer_choice": (
            "Which active lifecycle opportunity population and support-native neutral "
            "definition should replace the rational unit before any outcome-bearing trial?"
        ),
        "non_claims": (
            "targeting value",
            "generic masking value",
            "semantic staleness",
            "utility or return",
        ),
    }


def canonical_report_bytes() -> bytes:
    return canonical_bytes(run_unit_closure())


if __name__ == "__main__":
    import sys

    sys.stdout.buffer.write(canonical_report_bytes() + b"\n")
