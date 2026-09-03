"""M1 first-action census and M2 cable-parameter sweep, A/RECON only.

No learner is trained, no optimizer step is taken, no action is chosen from an
outcome, and nothing here writes into any result-bearing root.  The six twin
states and the two update-160 foundation checkpoints are read from the accepted,
published base-run root; the quarantined `…-RUN-01` root is never opened.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Callable, Final, Sequence

import torch

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.contracts import (
    STATE_SPECS, TRAINING_SEEDS, build_run_manifest,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.foundation import (
    ImmutableBatchedFoundationPolicy, freeze_foundation_actor,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_backend import (
    NativeSession, _state_from_bytes,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_state import (
    DisturbanceHold,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.orchestration import (
    load_foundation_checkpoint,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.rng import (
    CounterRNG,
)


class CensusError(RuntimeError):
    pass


GRAPHS: Final[tuple[str, str]] = ("HR", "RH")
ACTION_COUNT: Final[int] = 18
HORIZON: Final[int] = 364
# The base run's frozen development map selected these in all twelve crossed
# units (result document §7).  They are read from the published action map, not
# assumed; this is only the expected value used to check it.
EXPECTED_MATCHED: Final[dict[str, int]] = {"HR": 10, "RH": 12}

# A diagnostic RNG domain that appears in no production stream.  The production
# domains are `source-disturbance-sign`, `development-disturbance-sign`,
# `heldout-disturbance-sign`, `source-reset`, `foundation-initialization`,
# `foundation-training`, `foundation-action-sampling`, `a-recon-*`.
DIAGNOSTIC_DOMAIN: Final[str] = "graded-order-value-diagnostic-r01-disturbance-sign"
DIAGNOSTIC_TAPES: Final[int] = 4
_MAGNITUDES: Final[tuple[float, float, float]] = (0.003, 0.002, 0.004)


@dataclass(frozen=True, slots=True)
class CensusCell:
    state_id: str
    k: int
    stratum: str
    graph: str
    action: int
    tape: int
    foundation_seed: int
    absorbing_transition: int | None
    constraint_fired: str | None
    inside_forced_hold: bool | None
    utility: float
    safe_dock: bool
    dock_tick: int | None
    timeout: bool
    max_z_terminal: float
    z_terminal: tuple[float, float, float, float]
    phi_first_tick: float
    lateral_error_first_tick: float
    transitions: int
    policy_queries: int
    cumulative_reward: float


def diagnostic_tape(state_id: str, seed: int, tape: int) -> tuple[DisturbanceHold, ...]:
    """64 hold rows in a domain disjoint from every production stream."""

    source = CounterRNG(seed)
    rows = []
    for hold in range(64):
        channels = []
        for channel, magnitude in enumerate(_MAGNITUDES):
            channels.append(tuple(
                magnitude if source.bernoulli(
                    0.5, domain=DIAGNOSTIC_DOMAIN,
                    address=(state_id, tape, hold, tick, channel),
                ) else -magnitude
                for tick in range(13)
            ))
        rows.append(DisturbanceHold(*channels))
    return tuple(rows)


def _y_ref(x: float) -> float:
    import math

    # Exact transcription of mf_rs_native.cpp:121-124.  Used only to report the
    # lateral error the tension term reads; it is never a control input.
    if 8.0 <= x < 16.0:
        return 0.18 * math.sin(math.pi * (x - 8.0) / 8.0)
    return 0.0


def _constraint(output) -> str | None:
    for label in ("cable_overload", "gantry_contact", "attitude_loss", "formation_loss"):
        if bool(getattr(output, label)):
            return label
    return None


def _state_payload(value: dict[str, object], graph: str) -> bytes:
    key = "hr_state_b64" if graph == "HR" else "rh_state_b64"
    return base64.b64decode(str(value[key]))


def load_twins(result_root: Path) -> dict[str, dict[str, object]]:
    twins: dict[str, dict[str, object]] = {}
    for spec in STATE_SPECS:
        path = result_root / "source-states" / f"{spec.cell}.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("state_id") != spec.cell or int(value.get("k")) != spec.k:
            raise CensusError(f"published twin artifact differs for {spec.cell}")
        twins[spec.cell] = value
    return twins


def load_policies(result_root: Path) -> dict[int, ImmutableBatchedFoundationPolicy]:
    """Load both update-160 foundations from the accepted published root."""

    run_manifest = build_run_manifest((result_root / "run-master.bin").read_bytes())
    published = json.loads((result_root / "manifest.json").read_text(encoding="utf-8"))
    if published["run_manifest"]["master_commitment"] != run_manifest.master_commitment:
        raise CensusError("published manifest does not bind the published master")
    policies = {}
    for seed in TRAINING_SEEDS:
        path = result_root / "foundations" / str(seed) / "checkpoints" / "update-160.json"
        model, _optimizer = load_foundation_checkpoint(
            path, expected_seed=seed, run_manifest=run_manifest,
        )
        policies[seed] = ImmutableBatchedFoundationPolicy(freeze_foundation_actor(model))
    return policies


def run_mission(
    *,
    payload: bytes,
    forced_action: int,
    k: int,
    tape: tuple[DisturbanceHold, ...],
    policy: ImmutableBatchedFoundationPolicy,
) -> dict[str, object]:
    """One lane: force `forced_action` for the first hold, then the foundation."""

    session = NativeSession.from_state_bytes((payload,))
    state_before = _state_from_bytes(payload)
    phi_first = float(state_before.phi)
    error_first = float(state_before.y) - _y_ref(float(state_before.x))
    tick_before = int(session.outputs[0].tick)
    outputs = session.step((forced_action,), (tape[0],))
    transitions = int(outputs[0].ticks_advanced)
    policy_queries = 0
    renewal = 1
    forced_hold_transitions = transitions
    absorbed_in_hold = bool(outputs[0].terminal)
    while not outputs[0].terminal:
        if renewal >= len(tape):
            raise CensusError("diagnostic tape exhausted before termination")
        selected = policy((outputs[0].observation,))
        policy_queries += 1
        outputs = session.step((selected[0],), (tape[renewal],))
        transitions += int(outputs[0].ticks_advanced)
        renewal += 1
    output = outputs[0]
    terminal_state = _state_from_bytes(session.state_bytes()[0])
    z = tuple(float(value) for value in terminal_state.z)
    failure = _constraint(output)
    absorbing = tick_before + transitions if failure is not None else None
    return {
        "absorbing_transition": absorbing,
        "absorbing_transition_within_mission": transitions if failure is not None else None,
        "constraint_fired": failure,
        "inside_forced_hold": absorbed_in_hold if failure is not None else None,
        "forced_hold_transitions": forced_hold_transitions,
        "utility": (
            (1.0 - int(output.dock_tick) / HORIZON) if bool(output.safe_dock) else 0.0
        ),
        "safe_dock": bool(output.safe_dock),
        "dock_tick": int(output.dock_tick) if bool(output.safe_dock) else None,
        "timeout": bool(output.timeout),
        "max_z_terminal": max(z),
        "z_terminal": z,
        "phi_first_tick": phi_first,
        "lateral_error_first_tick": error_first,
        "transitions": transitions,
        "policy_queries": policy_queries,
        "cumulative_reward": float(output.cumulative_reward),
    }


def census(
    *,
    twins: dict[str, dict[str, object]],
    policies: dict[int, ImmutableBatchedFoundationPolicy],
    actions: Sequence[int] = tuple(range(ACTION_COUNT)),
    tapes: int = DIAGNOSTIC_TAPES,
    progress: Callable[[str], None] | None = None,
) -> list[CensusCell]:
    """M1: every state x graph x action x tape on whichever library is bound."""

    rows: list[CensusCell] = []
    for spec in STATE_SPECS:
        value = twins[spec.cell]
        policy = policies[spec.source_seed]
        for graph in GRAPHS:
            payload = _state_payload(value, graph)
            for action in actions:
                for tape_index in range(tapes):
                    tape = diagnostic_tape(spec.cell, spec.source_seed, tape_index)
                    observed = run_mission(
                        payload=payload, forced_action=action, k=spec.k,
                        tape=tape, policy=policy,
                    )
                    rows.append(CensusCell(
                        state_id=spec.cell, k=spec.k, stratum=spec.stratum, graph=graph,
                        action=action, tape=tape_index, foundation_seed=spec.source_seed,
                        absorbing_transition=observed["absorbing_transition_within_mission"],
                        constraint_fired=observed["constraint_fired"],
                        inside_forced_hold=observed["inside_forced_hold"],
                        utility=observed["utility"], safe_dock=observed["safe_dock"],
                        dock_tick=observed["dock_tick"], timeout=observed["timeout"],
                        max_z_terminal=observed["max_z_terminal"],
                        z_terminal=observed["z_terminal"],
                        phi_first_tick=observed["phi_first_tick"],
                        lateral_error_first_tick=observed["lateral_error_first_tick"],
                        transitions=observed["transitions"],
                        policy_queries=observed["policy_queries"],
                        cumulative_reward=observed["cumulative_reward"],
                    ))
        if progress is not None:
            progress(f"census {spec.cell}")
    return rows


def census_fingerprint(rows: Sequence[CensusCell]) -> str:
    """Canonical digest of the whole census, for the bit-identity check."""

    import hashlib

    payload = json.dumps(
        [asdict(row) for row in rows], sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sweep_point(
    *,
    twins: dict[str, dict[str, object]],
    policies: dict[int, ImmutableBatchedFoundationPolicy],
    matched: dict[str, int],
    tapes: int = DIAGNOSTIC_TAPES,
) -> dict[str, object]:
    """M2 at one grid point: matched and swapped arms only, 96 missions."""

    swapped = {"HR": matched["RH"], "RH": matched["HR"]}
    cells: list[dict[str, object]] = []
    for spec in STATE_SPECS:
        value = twins[spec.cell]
        policy = policies[spec.source_seed]
        for graph in GRAPHS:
            payload = _state_payload(value, graph)
            for arm, action in (("MATCHED", matched[graph]), ("SWAPPED", swapped[graph])):
                for tape_index in range(tapes):
                    tape = diagnostic_tape(spec.cell, spec.source_seed, tape_index)
                    observed = run_mission(
                        payload=payload, forced_action=action, k=spec.k,
                        tape=tape, policy=policy,
                    )
                    cells.append({
                        "state_id": spec.cell, "k": spec.k, "graph": graph, "arm": arm,
                        "action": action, "tape": tape_index,
                        "utility": observed["utility"], "safe_dock": observed["safe_dock"],
                        "constraint_fired": observed["constraint_fired"],
                        "absorbing_transition": observed["absorbing_transition_within_mission"],
                        "inside_forced_hold": observed["inside_forced_hold"],
                        "survives_forced_hold": observed["inside_forced_hold"] is not True,
                    })
    return {"cells": cells, **summarize_point(cells)}


def summarize_point(cells: Sequence[dict[str, object]]) -> dict[str, object]:
    """M, X, M - X and the tape-invariant survival / dock counts of twelve cells."""

    by_cell: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for row in cells:
        by_cell.setdefault((row["state_id"], row["graph"], row["arm"]), []).append(row)
    matched_by_state: dict[str, dict[str, float]] = {}
    swapped_by_state: dict[str, dict[str, float]] = {}
    survival_cells = 0
    matched_dock_cells = 0
    swapped_absorb_cable_cells = 0
    for (state_id, graph, arm), rows in sorted(by_cell.items()):
        utilities = [float(row["utility"]) for row in rows]
        mean = sum(utilities) / len(utilities)
        target = matched_by_state if arm == "MATCHED" else swapped_by_state
        target.setdefault(state_id, {})[graph] = mean
        if arm == "SWAPPED":
            if all(row["survives_forced_hold"] for row in rows):
                survival_cells += 1
            if all(
                row["constraint_fired"] == "cable_overload" and row["inside_forced_hold"] is True
                for row in rows
            ):
                swapped_absorb_cable_cells += 1
        else:
            if all(row["safe_dock"] for row in rows):
                matched_dock_cells += 1
    states = sorted(matched_by_state)
    m_values = []
    x_values = []
    for state_id in states:
        # M pairs each graph with its matched action; X is the same two actions
        # with the association reversed, which on one lane each is the SWAPPED
        # arm.  Both are the parent card's 0.5 * [HR + RH] averages.
        m_values.append(0.5 * (matched_by_state[state_id]["HR"] + matched_by_state[state_id]["RH"]))
        x_values.append(0.5 * (swapped_by_state[state_id]["HR"] + swapped_by_state[state_id]["RH"]))
    mean_m = sum(m_values) / len(m_values)
    mean_x = sum(x_values) / len(x_values)
    return {
        "M": mean_m,
        "X": mean_x,
        "M_minus_X": mean_m - mean_x,
        "M_by_state": dict(zip(states, m_values, strict=True)),
        "X_by_state": dict(zip(states, x_values, strict=True)),
        "swapped_survival_cells": survival_cells,
        "matched_dock_cells": matched_dock_cells,
        "swapped_cable_absorption_cells": swapped_absorb_cable_cells,
    }


def set_threads(count: int = 1) -> None:
    torch.set_num_threads(int(count))


__all__ = [
    "ACTION_COUNT", "CensusCell", "CensusError", "DIAGNOSTIC_DOMAIN", "DIAGNOSTIC_TAPES",
    "EXPECTED_MATCHED", "GRAPHS", "census", "census_fingerprint", "diagnostic_tape",
    "load_policies", "load_twins", "run_mission", "set_threads", "summarize_point",
    "sweep_point",
]
