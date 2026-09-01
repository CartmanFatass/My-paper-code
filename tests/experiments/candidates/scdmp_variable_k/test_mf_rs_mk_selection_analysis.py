from __future__ import annotations

from dataclasses import replace

import pytest

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.analysis import (
    HeldoutCell,
    analyze_heldout_panel,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.artifacts import (
    ActionMapArtifactError,
    HeldoutTapePermit,
    freeze_action_map,
    open_heldout_namespace,
    validate_heldout_permit,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.selection import (
    DevelopmentCell,
    DevelopmentMappingError,
    freeze_development_mapping,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import contracts
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import selection
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import analysis as analysis_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.rng import (
    development_tape_address,
    materialize_disturbance_tape,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_backend import (
    construct_reachable_twins, evaluate_twin_branches,
)


SEEDS = (1709, 2903)
STATE_ROWS = (
    ("k7-early", 7, "early"),
    ("k7-middle", 7, "middle"),
    ("k7-late", 7, "late"),
    ("k13-early", 13, "early"),
    ("k13-middle", 13, "middle"),
    ("k13-late", 13, "late"),
)


class _ZeroPolicy:
    def __init__(self, seed: int) -> None:
        self.foundation_seed = seed

    def __call__(self, observations):
        return (0,) * len(observations)


def test_selection_inventory_is_the_exact_static_contract() -> None:
    assert selection.TRAINING_SEEDS == contracts.TRAINING_SEEDS
    assert selection.STATE_ROWS == tuple(
        (row.cell, row.k, row.stratum) for row in contracts.STATE_SPECS
    )
    assert selection.ACTIONS == tuple(range(len(contracts.ACTION_TABLE)))
    assert selection.DEVELOPMENT_TAPES == contracts.DEVELOPMENT_TAPES

    development_addresses = {
        development_tape_address(state_id, tape)
        for state_id, _k, _stratum in STATE_ROWS for tape in range(8)
    }
    assert len(development_addresses) == 48


def _development_cells() -> tuple[DevelopmentCell, ...]:
    rows = []
    for seed in SEEDS:
        for state_id, k, stratum in STATE_ROWS:
            for tape in range(8):
                for graph in ("HR", "RH"):
                    for action in range(18):
                        preferred = 4 if graph == "HR" else 9
                        dock_tick = 73 if action == preferred else 109 if action == 2 else None
                        safe = dock_tick is not None
                        utility = 1.0 - dock_tick / 364.0 if safe else 0.0
                        rows.append(
                            DevelopmentCell(
                                seed, state_id, k, stratum, tape, graph, action, utility,
                                True, safe, dock_tick, False,
                                () if safe else ("formation_loss",),
                                utility - 0.1, 1.0, 364, 364, 27,
                            )
                        )
    return tuple(rows)


def test_complete_development_panel_freezes_exact_mapping_before_heldout_namespace() -> None:
    mapping = freeze_development_mapping(_development_cells())

    assert len(mapping.units) == 12
    assert mapping.action_for(1709, "k7-early", "HR") == 4
    assert mapping.action_for(1709, "k7-early", "RH") == 9
    assert mapping.common_for(1709, "k7-early") == 2
    assert mapping.heldout_namespace_token == "SCDMP-MF-RS-MK-B01/heldout/RUN-01"
    assert mapping.fceov_rank_diagnostics(1709, "k7-early") == {
        "HR": {0: 3, 10: 11, 12: 13},
        "RH": {0: 3, 10: 11, 12: 13},
    }


def test_development_mapping_rejects_partial_duplicate_and_nonfinite_cells() -> None:
    cells = _development_cells()
    with pytest.raises(DevelopmentMappingError, match="complete"):
        freeze_development_mapping(cells[:-1])
    with pytest.raises(DevelopmentMappingError, match="duplicate"):
        freeze_development_mapping((*cells, cells[0]))
    with pytest.raises(DevelopmentMappingError, match="finite"):
        freeze_development_mapping((replace(cells[0], utility=float("nan")), *cells[1:]))
    with pytest.raises(DevelopmentMappingError, match="native endpoint"):
        freeze_development_mapping((*cells[:4], replace(cells[4], utility=0.5), *cells[5:]))


def test_heldout_namespace_opens_only_after_direct_action_map_freeze(tmp_path) -> None:
    mapping = freeze_development_mapping(_development_cells())
    changed_cells = _development_cells()
    changed_mapping = freeze_development_mapping(
        (*changed_cells[:4], replace(
            changed_cells[4], utility=0.0, safe_dock=False, dock_tick=None,
            failures=("formation_loss",),
        ), *changed_cells[5:])
    )
    assert changed_mapping.serialized_bytes != mapping.serialized_bytes
    assert changed_mapping.heldout_namespace_token == mapping.heldout_namespace_token
    path = tmp_path / "development-action-map.json"
    with pytest.raises(ActionMapArtifactError, match="not frozen"):
        open_heldout_namespace(path, mapping)

    frozen = freeze_action_map(path, mapping)
    namespace = open_heldout_namespace(path, mapping)

    assert frozen == mapping.serialized_bytes
    assert namespace.token == mapping.heldout_namespace_token
    permit = namespace.address("k7-early", 0)
    assert permit.address.namespace.value == "HELDOUT"
    assert permit.address.seed == 1709
    assert permit.address.tape_id == (
        mapping.heldout_namespace_token + "/k7-early/0"
    )
    assert len(permit.rows) == 64
    with pytest.raises(ActionMapArtifactError, match="already exists"):
        freeze_action_map(path, mapping)
    path.write_bytes(b"{}")
    with pytest.raises(ActionMapArtifactError, match="direct bytes"):
        open_heldout_namespace(path, mapping)


def test_heldout_permit_binds_post_freeze_capability_address_and_tape_bytes(tmp_path) -> None:
    mapping = freeze_development_mapping(_development_cells())
    path = tmp_path / "map.json"
    freeze_action_map(path, mapping)
    permit = open_heldout_namespace(path, mapping).address("k7-early", 0)

    assert validate_heldout_permit(permit) == ("k7-early", permit.address, permit.rows)
    development_rows = materialize_disturbance_tape(
        development_tape_address("k7-early", 0)
    )
    assert development_rows != permit.rows
    with pytest.raises(ActionMapArtifactError, match="tape bytes"):
        validate_heldout_permit(replace(permit, rows=development_rows))
    with pytest.raises(ActionMapArtifactError, match="state/address"):
        validate_heldout_permit(replace(permit, state_id="k7-middle"))
    with pytest.raises(ActionMapArtifactError, match="post-freeze permit"):
        validate_heldout_permit(HeldoutTapePermit(
            "k7-early", permit.address, permit.rows, object(),
        ))


def test_heldout_tapes_are_96_state_shared_blocks_and_wrong_state_permit_is_rejected(tmp_path) -> None:
    mapping = freeze_development_mapping(_development_cells())
    path = tmp_path / "map.json"
    freeze_action_map(path, mapping)
    namespace = open_heldout_namespace(path, mapping)
    permits = tuple(
        namespace.address(state_id, tape)
        for state_id, _k, _stratum in STATE_ROWS for tape in range(16)
    )
    assert len({row.address for row in permits}) == 96

    manifest = contracts.build_run_manifest(b"scdmp-b01-test-master-32-bytes!!")
    state = contracts.STATE_SPECS[0]
    twins = construct_reachable_twins(
        run_manifest=manifest, state_spec=state, prefix_policy=_ZeroPolicy(state.source_seed),
    )
    with pytest.raises(ValueError, match="permit state"):
        evaluate_twin_branches(
            twins,
            forced_actions=(10, 12),
            evaluation_address=namespace.address("k7-middle", 0),
            foundation_policy=_ZeroPolicy(1709),
        )


def _heldout_cells(mapping) -> tuple[HeldoutCell, ...]:
    rows = []
    for seed in SEEDS:
        for state_id, k, stratum in STATE_ROWS:
            hr = mapping.action_for(seed, state_id, "HR")
            rh = mapping.action_for(seed, state_id, "RH")
            common = mapping.common_for(seed, state_id)
            for tape in range(16):
                for graph in ("HR", "RH"):
                    actions = {
                        "MATCHED": hr if graph == "HR" else rh,
                        "SWAPPED": rh if graph == "HR" else hr,
                        "COMMON": common,
                    }
                    dock_ticks = {"MATCHED": 36, "SWAPPED": 127, "COMMON": 109}
                    for arm in ("MATCHED", "SWAPPED", "COMMON"):
                        utility = 1.0 - dock_ticks[arm] / 364.0
                        rows.append(
                            HeldoutCell(
                                seed=seed,
                                state_id=state_id,
                                k=k,
                                stratum=stratum,
                                tape=tape,
                                graph=graph,
                                arm=arm,
                                action=actions[arm],
                                utility=utility,
                                terminal=True,
                                safe_dock=True,
                                dock_tick=dock_ticks[arm],
                                timeout=False,
                                failures=(),
                                external_reward=utility - 0.1,
                                energy=1.0,
                                allocated_slots=364,
                                transitions=364,
                                policy_queries=27,
                            )
                        )
    return tuple(rows)


def test_complete_raw_panel_selects_repeatable_signal_and_preserves_tape_units() -> None:
    mapping = freeze_development_mapping(_development_cells())
    analysis = analyze_heldout_panel(mapping, _heldout_cells(mapping))

    assert analysis.branch == "PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL"
    assert len(analysis.raw_cells) == 1_152
    assert len(analysis.tape_units) == 192
    assert all(unit.delta_swap == pytest.approx(91 / 364) for unit in analysis.tape_units)
    assert all(unit.delta_common == pytest.approx(73 / 364) for unit in analysis.tape_units)
    assert dict(analysis.within_state_tape_variance) == pytest.approx({"swap": 0.0, "common": 0.0})
    assert dict(analysis.between_state_variance) == pytest.approx({"swap": 0.0, "common": 0.0})
    assert dict(analysis.between_foundation_dispersion) == pytest.approx({"swap": 0.0, "common": 0.0})
    assert analysis.counts == {
        "raw_cells": 1_152,
        "tape_units": 192,
        "allocated_slots": 1_152 * 364,
        "transitions": 1_152 * 364,
        "policy_queries": 1_152 * 27,
    }


def test_heldout_analysis_rejects_action_work_and_inventory_drift() -> None:
    mapping = freeze_development_mapping(_development_cells())
    cells = _heldout_cells(mapping)
    with pytest.raises(ValueError, match="complete"):
        analyze_heldout_panel(mapping, cells[:-1])
    with pytest.raises(ValueError, match="action"):
        analyze_heldout_panel(mapping, (replace(cells[0], action=17), *cells[1:]))
    with pytest.raises(ValueError, match="work parity"):
        analyze_heldout_panel(mapping, (replace(cells[0], allocated_slots=363), *cells[1:]))
    with pytest.raises(ValueError, match="native endpoint"):
        analyze_heldout_panel(mapping, (replace(cells[0], utility=0.5), *cells[1:]))


def test_branch6_requires_both_seeds_overall_or_both_seeds_in_one_complete_k_stratum() -> None:
    mapping = freeze_development_mapping(_development_cells())
    foundation = {1709: (0.2, 0.1), 2903: (0.2, 0.1)}
    by_k = {
        (1709, 7): (0.2, -0.1), (2903, 7): (0.2, 0.2),
        (1709, 13): (0.2, 0.2), (2903, 13): (0.2, 0.2),
    }
    by_state = {
        (seed, state_id): (0.2, 0.2)
        for seed in SEEDS for state_id, _k, _stratum in STATE_ROWS
    }
    assert analysis_module._branch(foundation, by_k, by_state, mapping) == (
        "FOUNDATION_STATE_OR_SELECTOR_HETEROGENEITY"
    )

    complete_k_bad = dict(by_k)
    complete_k_bad[2903, 7] = (0.2, 0.0)
    assert analysis_module._branch(foundation, complete_k_bad, by_state, mapping) == (
        "GENERIC_ACTION_OR_RECOVERY_EXPLANATION"
    )
