"""Tests for the MSSR-D2 P x action support-native value crossover.

Proof-sized and deterministic.  The expensive full crossover (registered
search + all crossed rollouts) runs at most once (the module caches it); the
estimand arithmetic, the memory-mode ops and the executor freeze are
additionally unit-tested without any rollout.
"""

from __future__ import annotations

import functools

import numpy as np
import pytest

from ha_ctse_process.dynamic_roster_testbed import IDLE, PERSIST, SHORT
from ha_ctse_process.variable_roster_event_types import PartnerInteractionHistory

from experiments.candidates.vsp_06_mssr import d2_p_action_value_crossover as d2
from experiments.candidates.vsp_06_mssr.d2_p_action_value_crossover import (
    BOUNDARY_ACTIONS,
    EXECUTOR_SKILL_TO_PRIMITIVE,
    MEMORY_MODES,
    MODE_KEEP_P,
    MODE_P_NULL,
    MODE_REBUILD_P,
    TAU_VALUE,
    TERMINAL_NOT_CLOSED,
    TERMINAL_VALUE_NULL,
    TERMINAL_VALUE_PRESENT,
    cell_return,
    interactions,
    make_memory_mode_preframe,
    proof,
    selector_values,
)
from experiments.candidates.vsp_06_mssr.d1_change_f_matched_pair import (
    FROZEN_SOURCED_PAIR,
)

PAIR = FROZEN_SOURCED_PAIR


@functools.lru_cache(maxsize=1)
def _proof() -> dict:
    return proof()


class _FakeRecord:
    def __init__(self, history):
        self.status = "ACTIVE"
        self.partner_interaction_history = history


class _FakeCore:
    def __init__(self, physical_time, record):
        self.physical_time = physical_time
        self.records = {"0": record}


ROWS = ((0, "2", 0.5), (1, "3", 0.25))


def test_memory_mode_ops_unit_semantics():
    """KEEP_P is the identity; REBUILD_P drops the history object; P_NULL
    zeroes the retained scalar while keeping row provenance.  Each op fires
    only at the registered time and only on the target record."""
    history = PartnerInteractionHistory(current_p=0.4, rows=ROWS)

    record = _FakeRecord(history)
    make_memory_mode_preframe(MODE_KEEP_P, "0", 40)(_FakeCore(40, record))
    assert record.partner_interaction_history is history

    record = _FakeRecord(history)
    make_memory_mode_preframe(MODE_REBUILD_P, "0", 40)(_FakeCore(40, record))
    assert record.partner_interaction_history is None

    record = _FakeRecord(history)
    make_memory_mode_preframe(MODE_P_NULL, "0", 40)(_FakeCore(40, record))
    nulled = record.partner_interaction_history
    assert nulled is not None
    assert nulled.current_p == 0.0
    assert nulled.rows == ROWS

    # Wrong time: untouched.
    record = _FakeRecord(history)
    make_memory_mode_preframe(MODE_P_NULL, "0", 40)(_FakeCore(39, record))
    assert record.partner_interaction_history is history

    # Unknown mode: rejected at construction.
    with pytest.raises(ValueError):
        make_memory_mode_preframe("KEEP", "0", 40)


def test_executor_is_frozen_support_native_and_p_blind():
    """The executor covers the full skill vocabulary with legal primitives,
    matches Pro's registered example mapping, and its driver never reads P."""
    assert set(EXECUTOR_SKILL_TO_PRIMITIVE) == set(BOUNDARY_ACTIONS) == {0, 1, 2}
    assert EXECUTOR_SKILL_TO_PRIMITIVE == {0: IDLE, 1: PERSIST, 2: SHORT}
    assert set(EXECUTOR_SKILL_TO_PRIMITIVE.values()) == {IDLE, PERSIST, SHORT}
    # Structural P-blindness: the rollout driver never touches the P record.
    import inspect

    driver_source = inspect.getsource(d2._drive_with_boundary_action)
    assert "partner_interaction" not in driver_source
    assert "current_p" not in driver_source


def test_interaction_arithmetic():
    """Psi is the P x action interaction; arm-common and action-common effects
    cancel exactly."""
    table = {
        "q_minus_a0": 0.50, "q_minus_a1": 0.70, "q_minus_a2": 0.40,
        "q_plus_a0": 0.55, "q_plus_a1": 0.85, "q_plus_a2": 0.45,
    }
    out = interactions(table)
    assert abs(out["psi_a1_vs_a0"] - 0.10) < 1e-15
    assert abs(out["psi_a2_vs_a0"] - 0.0) < 1e-15
    assert abs(out["arm_main_effect_by_action"]["a0"] - 0.05) < 1e-15
    # A pure arm shift (same delta on every action) gives Psi == 0.
    shifted = {k: v + (0.2 if k.startswith("q_plus") else 0.0)
               for k, v in table.items()}
    base = {k: v for k, v in table.items()}
    base_psi = interactions(base)["psi_a1_vs_a0"]
    assert abs(interactions(shifted)["psi_a1_vs_a0"] - base_psi) < 1e-15


def test_selector_value_arithmetic():
    """The P-aware value averages each arm's selected action; the blind
    benchmark is the best constant action's cross-arm average."""
    table = {
        "q_minus_a0": 0.50, "q_minus_a1": 0.70, "q_minus_a2": 0.40,
        "q_plus_a0": 0.55, "q_plus_a1": 0.45, "q_plus_a2": 0.85,
    }
    selector = {"selected_skill_minus": 1, "selected_skill_plus": 2}
    out = selector_values(table, selector)
    assert abs(out["p_aware_value"] - 0.5 * (0.70 + 0.85)) < 1e-15
    assert abs(out["best_p_blind_value"] - max(
        0.5 * (0.50 + 0.55), 0.5 * (0.70 + 0.45), 0.5 * (0.40 + 0.85)
    )) < 1e-15
    assert abs(
        out["p_aware_margin"] - (out["p_aware_value"] - out["best_p_blind_value"])
    ) < 1e-15


def test_cell_rollout_deterministic_and_boundary_bound():
    """One crossed cell runs end to end: the boundary action commits, the
    support-native return is the terminal utility (rewards are terminal-only,
    so the from-boundary return equals the total return), and an identical
    re-run reproduces it exactly."""
    first = cell_return(
        PAIR, perturbed_arm=False, boundary_action=1, memory_mode=MODE_KEEP_P
    )
    assert first["boundary_committed"]
    assert first["return_from_boundary"] == first["total_return"]
    assert 0.0 <= first["return_from_boundary"] <= 1.0
    second = cell_return(
        PAIR, perturbed_arm=False, boundary_action=1, memory_mode=MODE_KEEP_P
    )
    assert second["return_from_boundary"] == first["return_from_boundary"]
    assert second["total_return"] == first["total_return"]


def test_proof_structure_and_registered_decision_rule():
    """proof() produces the full crossed report: D1 gate first, population
    manifest, a 2x3 Q table per memory mode for the primary cell, KEEP_P
    replication over every other sourced pair, and a terminal that follows the
    registered mechanical decision rule exactly."""
    report = _proof()
    assert report["d1_terminal"].endswith("MATCHED_PAIR_PRESENT")
    assert report["terminal"] in (
        TERMINAL_VALUE_PRESENT, TERMINAL_VALUE_NULL, TERMINAL_NOT_CLOSED
    )
    assert report["terminal"] != TERMINAL_NOT_CLOSED
    assert report["executor"] == {"0": IDLE, "1": PERSIST, "2": SHORT}

    manifest = report["population_manifest"]
    assert manifest["primary"]["base_family"] == PAIR.base_family
    assert manifest["primary"]["physical_time"] == PAIR.physical_time
    assert manifest["sourcing_counts"]["exposure_positive"] == 10
    assert len(manifest["replication"]) == 9

    primary = report["primary"]
    assert set(primary) == set(MEMORY_MODES)
    for mode in MEMORY_MODES:
        cell = primary[mode]
        assert set(cell["q"]) == {
            f"q_{arm}_a{action}"
            for arm in ("minus", "plus")
            for action in BOUNDARY_ACTIONS
        }
        for value in cell["q"].values():
            assert 0.0 <= value <= 1.0
        assert cell["selector"]["memory_mode"] == mode
        if mode == MODE_KEEP_P:
            assert cell["selector"]["p_read_minus"] != cell["selector"]["p_read_plus"]
        else:
            assert cell["selector"]["p_read_minus"] == 0.0
            assert cell["selector"]["p_read_plus"] == 0.0
            # Identical P read on the byte-matched preimage: identical logits,
            # identical selection.
            assert (
                cell["selector"]["first_logits_minus"]
                == cell["selector"]["first_logits_plus"]
            )

    assert len(report["replication"]) == 9

    decision = report["decision_inputs"]
    expected_present = bool(
        decision["max_abs_interaction"] > TAU_VALUE
        or decision["max_selector_margin"] > TAU_VALUE
    )
    assert report["terminal"] == (
        TERMINAL_VALUE_PRESENT if expected_present else TERMINAL_VALUE_NULL
    )

    # The interaction recomputes from the reported Q tables.
    for mode in MEMORY_MODES:
        cell = primary[mode]
        table = cell["q"]
        psi = (table["q_plus_a1"] - table["q_plus_a0"]) - (
            table["q_minus_a1"] - table["q_minus_a0"]
        )
        assert cell["interactions"]["psi_a1_vs_a0"] == psi


def test_structural_pins_matched_future_and_frozen_terminal():
    """STRUCTURAL REGRESSION PINS (reviewer MAJOR F1): the matched
    precommitted future is a design guarantee -- per forced action, the two
    arms' returns must be byte-equal (the population is environment-
    reconverged, partners stay on the base script, the perturbation window is
    pre-boundary, and production reads P nowhere), so every arm main effect,
    every interaction and every selector margin is EXACTLY zero, and the
    terminal is the frozen measured VALUE_NULL.  A nonzero value here means a
    harness regression (perturbation leaking past the boundary, partners
    drifting off the tape, a mis-keyed executor), NOT new science; if a
    Pro-directed design change legitimately moves these, the pins are
    re-frozen with it.  The action channel pins prove the executor is live, so
    the zeros are not vacuous."""
    report = _proof()
    primary = report["primary"]
    for mode in MEMORY_MODES:
        cell = primary[mode]
        table = cell["q"]
        for action in BOUNDARY_ACTIONS:
            assert table[f"q_minus_a{action}"] == table[f"q_plus_a{action}"]
        inter = cell["interactions"]
        assert inter["psi_a1_vs_a0"] == 0.0
        assert inter["psi_a2_vs_a0"] == 0.0
        assert all(
            value == 0.0
            for value in inter["arm_main_effect_by_action"].values()
        )
        assert cell["selector_value"]["p_aware_margin"] == 0.0
    for cell in report["replication"]:
        for action in BOUNDARY_ACTIONS:
            assert cell["q"][f"q_minus_a{action}"] == cell["q"][f"q_plus_a{action}"]
        assert cell["interactions"]["psi_a1_vs_a0"] == 0.0
        assert cell["interactions"]["psi_a2_vs_a0"] == 0.0
    assert report["decision_inputs"]["max_abs_interaction"] == 0.0
    assert report["decision_inputs"]["max_selector_margin"] == 0.0
    assert report["terminal"] == TERMINAL_VALUE_NULL
    # The ACTION channel is live (frozen measured pins; executor works).
    keep = primary["KEEP_P"]["interactions"]["action_effect_minus_arm"]
    assert keep["a1_vs_a0"] == 0.0859375
    assert abs(keep["a2_vs_a0"] - 0.02083333333333326) < 1e-15
    # The interface stays visible where it should: KEEP_P selector logits
    # differ across arms; REBUILD_P/P_NULL logits are byte-identical.
    assert (
        primary["KEEP_P"]["selector"]["first_logits_minus"]
        != primary["KEEP_P"]["selector"]["first_logits_plus"]
    )


def test_scope_states_required_caveats():
    """SCOPE carries the honesty clauses Pro's false-closure list requires."""
    scope = d2.SCOPE.lower()
    assert "selected maximum" in scope
    assert "never reading p" in scope
    assert "terminal utility" in scope
    assert "controlled" in scope
    assert "not a p effect" in scope
    assert "untrained" in scope
    assert "belongs to external pro" in scope
    assert "production execution and replay still call .logits()" in scope
    assert "no cell is selected on downstream return" in scope
    # Terminal vocabulary is Pro's.
    assert TERMINAL_VALUE_PRESENT.endswith("P_ACTION_VALUE_PRESENT")
    assert TERMINAL_VALUE_NULL.endswith("P_INTERFACE_PRESENT_VALUE_NULL")
    assert TERMINAL_NOT_CLOSED.endswith("VALUE_POPULATION_NOT_CLOSED")
