from __future__ import annotations

from experiments.candidates.variable_n_fleet_churn_r02 import panel


def test_exact_address_and_primitive_inventory() -> None:
    rows = panel.all_top_rows()
    assert len(rows) == len({row.address for row in rows}) == 304
    assert len(panel.main_rows()) == 288
    assert len(panel.witness_rows()) == 4
    assert len(panel.primitive_rows()) == 12
    assert all(len(row.token_addresses) == 4 for row in rows)
    assert panel.primitive_child_counts() == {
        "token_records": 48,
        "candidate_children": 80,
        "cdf_children": 512,
    }
    assert len(panel.primitive_candidate_addresses()) == 80
    assert len(panel.primitive_cdf_addresses()) == 512


def test_cdf_probe_endpoint_addresses_have_no_placeholders() -> None:
    for candidate_count in (1, 2, 3):
        probes = panel.expected_cdf_probe_names(candidate_count)
        assert len(probes) == 5 * candidate_count + 3
        assert (0, "PRODUCTION_WORD_BELOW") not in probes
        assert (candidate_count, "PRODUCTION_WORD_ABOVE") not in probes
        assert (0, "PRODUCTION_WORD_ABOVE") in probes
        assert (candidate_count, "PRODUCTION_WORD_BELOW") in probes


def test_74_logical_keys_expand_to_292_independent_clones() -> None:
    rows = panel.evaluations()
    keys = {row.comparison_key for row in rows}
    assert len(keys) == 74
    assert len(rows) == 292
    assert len({row.replay_address for row in rows}) == 292
    assert len({row.gradient_address for row in rows}) == 292
    assert len({row.optimizer_address for row in rows}) == 292
    assert sorted(sum(row.comparison_key == key for row in rows) for key in keys) == [2] * 2 + [4] * 72


def test_clone_validation_rejects_sequential_chaining() -> None:
    records = [
        {
            "comparison_key": row.comparison_key,
            "top_address": row.top_address,
            "prestate_digest": "same",
            "source_prestate_digest": "same",
            "clone_ordinal": row.clone_ordinal,
        }
        for row in panel.evaluations()
    ]
    panel.validate_clone_independence(records)
    records[1] = {**records[1], "prestate_digest": "chained"}
    try:
        panel.validate_clone_independence(records)
    except panel.PanelError:
        pass
    else:
        raise AssertionError("sequential presentation chaining was accepted")
