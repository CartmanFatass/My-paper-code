from __future__ import annotations

import json

import pytest
import torch

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.models import (
    direct_parameter_shapes,
    mapr_parameter_shapes,
)
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.torch_models import DirectSetAR, MAPR4
from experiments.candidates.variable_n_fleet_churn_b_explore import ps_b0


@pytest.fixture(scope="module")
def zero_models() -> dict[str, dict[str, object]]:
    mapr = MAPR4({name: torch.zeros(shape, dtype=torch.float64) for name, shape in mapr_parameter_shapes().items()})
    direct = DirectSetAR({name: torch.zeros(shape, dtype=torch.float64) for name, shape in direct_parameter_shapes().items()})
    return {
        "initial": {"MAPR": mapr, "DIRECT": direct},
        "final": {"MAPR": mapr, "DIRECT": direct},
    }


def test_ps_b0_cardinality_primitives_are_exact() -> None:
    descriptors = ps_b0.state_descriptors()
    addresses = ps_b0.expected_addresses()
    assert len(descriptors) == 18
    assert len({(row["roster_size"], row["failed_zone"], row["state_kind"]) for row in descriptors}) == 18
    assert len(addresses) == 288
    assert {row[0] for row in addresses} == {3, 5, 7}
    assert {row[1] for row in addresses} == {1, 2}
    assert {row[3] for row in addresses} == set(ps_b0.PRESENTATIONS)


def test_actual_native_states_cover_every_cell_and_do_not_fabricate_support() -> None:
    adapter = ps_b0.ActualPathPSB0Adapter()
    states = tuple(adapter.build_support_path_state(row, 2026090101) for row in ps_b0.state_descriptors())
    assert len(states) == 18
    for state in states:
        assert set(state.snapshots) == set(ps_b0.PRESENTATIONS)
        assert len({snapshot.fixture.post_presentations[0] for snapshot in state.snapshots.values()}) == 4
        actual_active_orders = {
            tuple(
                rank for rank in snapshot.fixture.post_presentations[int(snapshot.trace["epoch"])]
                if rank != snapshot.failed_rank
            )
            for snapshot in state.snapshots.values()
        }
        assert len(actual_active_orders) == 4
        assert all(len(order) == state.roster_size for order in actual_active_orders)
        if state.state_kind == "later_fixed_or_acquiring":
            assert state.native_physical_command is not None
            assert all(any(value in (1, 2) for value in snapshot.trace["token_state"]) for snapshot in state.snapshots.values())
            assert all(snapshot.origin == "native_interactive_t0_plus_one_identical_physical_bcrh_command" for snapshot in state.snapshots.values())
        if state.state_kind == "diagnostic_null_tie":
            assert all(
                ps_b0._diagnostic_predecision_support(snapshot)["target_legal_agent_count"] >= 2
                and ps_b0._diagnostic_predecision_support(snapshot)["target_null_legal"]
                for snapshot in state.snapshots.values()
            )
            assert state.native_physical_command is None


def test_full_actual_comparison_inventory_is_serializable_and_exact(zero_models: dict[str, dict[str, object]]) -> None:
    adapter = ps_b0.ActualPathPSB0Adapter()
    rows = ps_b0.build_all_comparisons(zero_models, seed=2026090101, adapter=adapter)
    assert len(rows) == 288
    assert {row.address for row in rows} == ps_b0.expected_addresses()
    for row in rows:
        assert row.agent_rows_copermuted
        assert row.legal_masks_copermuted
        assert row.fixed_occupants_copermuted
        assert row.opaque_ranks_copermuted
        assert row.physical_support_equal
        assert row.canonical_physical_command == row.inverse_mapped_physical_command
        assert row.equal_logit_claim is False
        assert row.canonical_trace["forward_verified_exact"] is True
        assert row.tested_trace["forward_verified_exact"] is True
        assert len(row.canonical_trace["tokens"]) == 4
        assert all("base_logit_binary64" in candidate and "probability_binary64" in candidate for token in row.tested_trace["tokens"] for candidate in token["candidates"])
        aligned = row.score_probability_difference_diagnostics["deterministic_decoder"]
        assert aligned["alignment"] == "physical_token_then_physical_candidate_rank"
        assert len(aligned["tokens"]) == 4
        assert all(
            candidate["support_equal"] and "probability_difference_binary64" in candidate["differences"]
            for token in aligned["tokens"] for candidate in token["candidates_by_physical_rank"]
        )
        if row.state_kind == "diagnostic_null_tie":
            assert row.null_case_present and row.null_action_legal
            assert row.legal_agent_candidate_count >= 2
            assert row.predecision_legal_agent_count == row.legal_agent_candidate_count
            assert row.diagnostic_target_physical_token in (0, 1, 2, 3)
            assert row.tested_trace["diagnostic_predecision_support"]["semantics"].startswith("actual_state_predecision")
            assert row.opaque_deterministic_tie_ranks_complete
        if row.state_kind == "later_fixed_or_acquiring":
            assert row.fixed_or_acquiring_case_present
    encoded = json.dumps(rows[-1].to_dict(), sort_keys=True, allow_nan=False)
    assert "NativeInteractiveBatch" in encoded
    assert "probability_binary64" in encoded
    ledger = adapter.require_complete_host_call_ledger()
    assert ledger["primary_only_host_calls"] == 24
    assert ledger["reset_calls"] == 12
    assert ledger["bcrh_calls"] == 6
    assert ledger["step_calls"] == 6
    assert ledger["batch_widths"] == (8,)
    assert all(row["duplicates_per_surface"] == 2 and row["duplicate_exact_required"] for row in ledger["records"])


def test_bound_source_or_native_drift_fails_closed(monkeypatch: pytest.MonkeyPatch, zero_models: dict[str, dict[str, object]]) -> None:
    adapter = ps_b0.ActualPathPSB0Adapter()
    state = adapter.build_support_path_state(
        {"roster_size": 3, "failed_zone": 1, "state_kind": "diagnostic_null_tie"},
        2026090101,
    )
    original = ps_b0._source_identity
    monkeypatch.setattr(ps_b0, "_source_identity", lambda: {**original(), "deliberate_test_drift": True})
    with pytest.raises(ps_b0.PSB0SourceDriftError, match="drifted"):
        adapter.compare_presentations(
            state, "reverse", "initial", "MAPR", zero_models["initial"]["MAPR"], None
        )


def test_wrong_model_family_is_rejected(zero_models: dict[str, dict[str, object]]) -> None:
    adapter = ps_b0.ActualPathPSB0Adapter()
    state = adapter.build_support_path_state(
        {"roster_size": 3, "failed_zone": 2, "state_kind": "t0"},
        2026090101,
    )
    with pytest.raises(ps_b0.PSB0ConstructionError, match="model class differs"):
        adapter.compare_presentations(
            state, "canonical", "initial", "MAPR", zero_models["initial"]["DIRECT"], None
        )
