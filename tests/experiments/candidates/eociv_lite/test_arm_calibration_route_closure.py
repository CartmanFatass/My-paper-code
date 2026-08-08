from __future__ import annotations

import dataclasses
import random
from fractions import Fraction
from pathlib import Path

import pytest

from experiments.candidates.eociv_lite import arm_calibration_route_closure as eociv


def test_actual_run_closes_exactly_five_intervention_checks() -> None:
    report = eociv.run_unit_closure()

    assert report["terminal"] == "PASS_INTERVENTION_CLOSURE"
    assert report["actual_instance_status"] == "ACTUAL_BINDING_NOT_ESTABLISHED"
    assert report["closures"] == {
        "payload_pair_byte_closure": True,
        "always_real_pre_sampling_equivalence": True,
        "exhaustive_arm_mapping": True,
        "zero_jacobian_and_pre_actuation": True,
        "outcome_sealed_null_conformance": True,
    }


def test_trigger_cluster_clock_is_complete_exact_and_immutable() -> None:
    config = eociv.build_unit_config()

    assert config.horizon == 8 == len(config.clocks)
    assert [clock.opportunity for clock in config.clocks] == list(range(8))
    assert [clock.physical_tick for clock in config.clocks] == [10, 13, 16, 19, 22, 25, 28, 31]
    assert {clock.trigger_id for clock in config.clocks} == {config.trigger_id}
    assert {clock.cluster_id for clock in config.clocks} == {config.cluster_id}
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.clocks[0].opportunity = 9  # type: ignore[misc]


def test_calibration_chooses_most_open_feasible_threshold_and_freezes_q_from_d_cal() -> None:
    config = eociv.build_unit_config()
    threshold = eociv.calibration_threshold(config)
    q = eociv.frozen_q(config)

    assert threshold == Fraction(1, 4)
    assert eociv.derive_q_from_calibration(config, threshold) == q
    assert q == {"route-a": Fraction(1, 4), "route-b": Fraction(1, 4)}
    assert eociv.run_unit_closure(config)["learned_open_sequences"] == {
        "route-a": (False, True, True, True),
        "route-b": (False, True, True, True),
    }

    changed_policy = dataclasses.replace(
        config,
        pools=tuple(
            dataclasses.replace(pool, sample_ids=("different-policy",))
            if pool.name == "D_policy"
            else pool
            for pool in config.pools
        ),
    )
    assert eociv.frozen_q(changed_policy) == q
    assert eociv.derive_q_from_calibration(changed_policy, threshold) == q


def test_control_kernel_is_target_independent_and_matches_frozen_run_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    config = eociv.build_unit_config()

    def forbidden_global_rng() -> float:
        raise AssertionError("global RNG must not be read")

    monkeypatch.setattr(random, "random", forbidden_global_rng)
    decisions = tuple(eociv.control_open(config, "route-a", opportunity) for opportunity in range(4))
    assert decisions == (False, True, True, True)
    with pytest.raises(eociv.ClosureError, match="unsupported control opportunity"):
        eociv.control_open(config, "unknown", 0)


def test_sham_score_has_exact_support_and_no_missingness() -> None:
    config = eociv.build_unit_config()
    for cell in ("route-a", "route-b"):
        rows = tuple(row for row in config.calibration_rows if row.cell == cell)
        values = tuple(eociv.sham_score(config, cell, opportunity) for opportunity in range(4))
        assert sorted(values) == sorted(row.score for row in rows)
        assert all(isinstance(value, Fraction) for value in values)


def test_score_and_payload_label_mutations_cannot_reach_control_or_sham() -> None:
    config = eociv.build_unit_config()
    before_control = tuple(eociv.control_open(config, "route-a", index) for index in range(4))
    before_sham = tuple(eociv.sham_score(config, "route-a", index) for index in range(4))
    mutated = dataclasses.replace(
        config,
        calibration_rows=tuple(
            dataclasses.replace(row, score=Fraction(1) - row.score, payload_label=99)
            for row in config.calibration_rows
        ),
    )

    assert tuple(eociv.control_open(mutated, "route-a", index) for index in range(4)) == before_control
    assert tuple(eociv.sham_score(mutated, "route-a", index) for index in range(4)) == before_sham
    original_d_l = tuple(eociv.learned_open(row.score, Fraction(1, 4)) for row in config.calibration_rows[:4])
    mutated_d_l = tuple(eociv.learned_open(row.score, Fraction(1, 4)) for row in mutated.calibration_rows[:4])
    assert original_d_l != mutated_d_l


def test_four_ancestry_pools_have_no_shared_root_or_sample() -> None:
    config = eociv.build_unit_config()
    roots = [pool.ancestry_root for pool in config.pools]
    samples = [sample for pool in config.pools for sample in pool.sample_ids]

    assert [pool.name for pool in config.pools] == ["D_fit", "D_cal", "D_policy", "D_focal"]
    assert len(set(roots)) == 4
    assert len(set(samples)) == len(samples)


def test_payload_pair_masked_writes_are_byte_identical_and_real_bytes_survive() -> None:
    config = eociv.build_unit_config()
    cell = eociv.support_cell(config, "route-a")
    masked = [eociv.actuate(config, "LS", True, cell.cell, body, False, True) for body in config.legal_payloads]
    traces = [eociv.receiver_trace(item.payload, cell.envelope, cell.cost) for item in masked]

    assert masked[0].payload == masked[1].payload == cell.native_neutral
    assert traces[0] == traces[1]
    for body in config.legal_payloads:
        assert eociv.actuate(config, "LS", True, cell.cell, body, True, False).payload == body


def test_lr_cr_are_identical_before_sampling_and_mismatch_is_detected() -> None:
    config = eociv.build_unit_config()

    assert eociv.always_real_equivalent(config, config.legal_payloads[0], config.legal_payloads[0])
    assert not eociv.always_real_equivalent(config, config.legal_payloads[0], config.legal_payloads[1])


@pytest.mark.parametrize("arm", eociv.ARMS)
def test_g_zero_suppresses_every_arm(arm: str) -> None:
    config = eociv.build_unit_config()
    result = eociv.actuate(config, arm, False, "route-a", b"body", True, True)

    assert (result.route, result.payload, result.decision_source) == ("SUPPRESSED", b"", "G=0")


@pytest.mark.parametrize("arm", eociv.ARMS)
def test_unsupported_g_one_is_hard_open_for_every_arm(arm: str) -> None:
    config = eociv.build_unit_config()
    result = eociv.actuate(config, arm, True, "critical-no-neutral", b"registered", False, False)

    assert (result.route, result.payload, result.decision_source) == ("REAL", b"registered", "HARD_OPEN")


def test_ls_reads_only_d_l_cs_only_d_c_and_controls_are_always_real() -> None:
    config = eociv.build_unit_config()
    body = b"registered"

    for d_l in (False, True):
        for d_c in (False, True):
            ls = eociv.actuate(config, "LS", True, "route-a", body, d_l, d_c)
            cs = eociv.actuate(config, "CS", True, "route-a", body, d_l, d_c)
            lr = eociv.actuate(config, "LR", True, "route-a", body, d_l, d_c)
            cr = eociv.actuate(config, "CR", True, "route-a", body, d_l, d_c)
            assert (ls.route == "REAL") == d_l
            assert (cs.route == "REAL") == d_c
            assert lr.route == cr.route == "REAL"


@pytest.mark.parametrize("field", eociv.PROHIBITED_SELECTOR_FIELDS)
def test_every_prohibited_mutation_fail_closes_all_three_path_families(field: str) -> None:
    config = eociv.build_unit_config()
    raw = {name: 0 for name in eociv.W_MINUS_FIELDS}
    attempt = {field: "attempt"}

    with pytest.raises(eociv.ClosureError, match="outside W_minus"):
        eociv.selector_view({**raw, **attempt})
    for probe in (
        lambda: eociv.support_cell(config, "route-a", attempt),
        lambda: eociv.control_open(config, "route-a", 0, attempt),
        lambda: eociv.sham_score(config, "route-a", 0, attempt),
    ):
        with pytest.raises(eociv.ClosureError, match="prohibited source"):
            probe()


def test_combined_three_family_mutation_result_is_terminal_bearing() -> None:
    report = eociv.run_unit_closure()

    assert report["forbidden_source_terminal"] == "PASS_THREE_FAMILY_CLOSURE"
    assert set(report["mutations"]) == set(eociv.PROHIBITED_SELECTOR_FIELDS)
    assert all(set(families.values()) == {"FAIL_CLOSED"} for families in report["mutations"].values())


def test_w_minus_is_complete_and_rejects_missing_input() -> None:
    raw = {name: 0 for name in eociv.W_MINUS_FIELDS}
    assert tuple(name for name, _ in eociv.selector_view(raw)) == eociv.W_MINUS_FIELDS
    raw.pop("owner_epoch")
    with pytest.raises(eociv.ClosureError, match="incomplete W_minus"):
        eociv.selector_view(raw)


def test_gradient_and_pre_actuation_route_graphs_have_no_bypass() -> None:
    config = eociv.build_unit_config()
    eociv.validate_config(config)

    assert not eociv._reachable(config.parameter_routes, "theta_valve", "team_loss")
    assert not eociv._reachable(config.parameter_routes, "kappa_c", "team_loss")
    assert not eociv._reachable(config.parameter_routes, "theta_backbone", "valve_loss")
    assert not eociv._reachable(config.recurrent_routes, "body", "selector")
    assert eociv._reachable(config.recurrent_routes, "body", "receiver_recurrence")
    assert eociv.route_closure_closed(config)


@pytest.mark.parametrize(
    ("source", "sink"),
    (("theta_valve", "team_loss"), ("kappa_c", "team_loss"), ("theta_backbone", "valve_loss")),
)
def test_each_gradient_bypass_fails_closed(source: str, sink: str) -> None:
    config = eociv.build_unit_config()
    bypass = dataclasses.replace(config, parameter_routes=config.parameter_routes + ((source, sink),))

    assert not eociv.route_closure_closed(bypass)
    with pytest.raises(eociv.ClosureError, match="route bypass"):
        eociv.validate_config(bypass)


@pytest.mark.parametrize(
    "extra_edges",
    (
        (("body", "selector"),),
        (("body", "receiver_recurrence"),),
        (("body", "alternate"), ("alternate", "receiver_recurrence")),
    ),
)
def test_each_body_pre_actuation_bypass_fails_closed(extra_edges: tuple[tuple[str, str], ...]) -> None:
    config = eociv.build_unit_config()
    bypass = dataclasses.replace(config, recurrent_routes=config.recurrent_routes + extra_edges)

    assert not eociv.route_closure_closed(bypass)
    with pytest.raises(eociv.ClosureError, match="route bypass"):
        eociv.validate_config(bypass)


def test_clock_monotonicity_and_declared_run_law_fail_closed() -> None:
    config = eociv.build_unit_config()
    nonmonotonic = dataclasses.replace(
        config,
        clocks=(config.clocks[0], dataclasses.replace(config.clocks[1], physical_tick=10), *config.clocks[2:]),
    )
    bad_run = dataclasses.replace(
        config,
        clocks=(dataclasses.replace(config.clocks[0], close_run_position=2), *config.clocks[1:]),
    )

    for malformed in (nonmonotonic, bad_run):
        assert not eociv.clock_run_law_closed(malformed)
        with pytest.raises(eociv.ClosureError, match="clock or run law"):
            eociv.validate_config(malformed)


def test_critical_edge_must_be_on_every_live_path_for_hard_open() -> None:
    config = eociv.build_unit_config()
    edge = config.critical_graph[0]
    missing_edge = dataclasses.replace(
        config,
        critical_graph=(dataclasses.replace(
            edge, live_paths=((('coordinator', 'relay', 4), ('relay', 'receiver', 5)),)
        ),),
    )
    late_edge = dataclasses.replace(
        config,
        critical_graph=(dataclasses.replace(
            edge, live_paths=((('coordinator', 'receiver', edge.deadline),),)
        ),),
    )

    assert eociv.critical_paths_closed(config)
    for malformed in (missing_edge, late_edge):
        assert not eociv.critical_paths_closed(malformed)
        with pytest.raises(eociv.ClosureError, match="every live path"):
            eociv.run_unit_closure(malformed)
        with pytest.raises(eociv.ClosureError, match="without HARD_OPEN"):
            eociv.actuate(malformed, "LS", True, "critical-no-neutral", b"body", False, False)


def test_overlap_illegal_neutral_and_unfrozen_calibration_fail_closed() -> None:
    config = eociv.build_unit_config()
    overlap = dataclasses.replace(
        config,
        pools=(config.pools[0], dataclasses.replace(config.pools[1], ancestry_root=config.pools[0].ancestry_root), *config.pools[2:]),
    )
    illegal_neutral = dataclasses.replace(
        config,
        support_cells=(dataclasses.replace(config.support_cells[0], native_neutral=None), *config.support_cells[1:]),
    )
    no_grid = dataclasses.replace(config, threshold_grid=(Fraction(0),))

    with pytest.raises(eociv.ClosureError, match="not disjoint"):
        eociv.validate_config(overlap)
    with pytest.raises(eociv.ClosureError, match="illegal missing native neutral"):
        eociv.validate_config(illegal_neutral)
    with pytest.raises(eociv.ClosureError, match="no feasible"):
        eociv.validate_config(no_grid)


def test_selector_recurrence_reset_is_cluster_scoped_and_deterministic() -> None:
    assert eociv.reset_selector_state("cluster-a") == ("cluster-a", (0, 0))
    assert eociv.reset_selector_state("cluster-b") == ("cluster-b", (0, 0))


def test_report_is_byte_stable_and_states_only_intervention_nonclaims() -> None:
    first = eociv.canonical_report_bytes()
    second = eociv.canonical_report_bytes()

    assert first == second
    assert b'"threshold":"1/4"' in first
    assert b'"utility or return"' in first
    assert b'"PASS_INTERVENTION_CLOSURE"' in first


def test_bounded_scan_finds_no_default_runtime_consumer_and_only_opt_in_script() -> None:
    root = Path(__file__).resolve().parents[4]
    needles = ("eociv_lite", "arm_calibration_route_closure")
    for top in ("ha_ctse_process", "envs"):
        for path in (root / top).rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert not any(needle in text for needle in needles), path

    script_consumers = []
    for path in (root / "scripts").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "arm_calibration_route_closure" not in text, path
            if "eociv_lite" in text:
                script_consumers.append(path.relative_to(root).as_posix())
    assert script_consumers == [
        "scripts/run_eociv_b1_real_valve_learning.py",
        "scripts/run_eociv_b2_payload_content_learnability.py",
    ]


def test_report_records_actual_binding_gap_without_scientific_failure() -> None:
    report = eociv.run_unit_closure()

    assert report["actual_instance_status"] == "ACTUAL_BINDING_NOT_ESTABLISHED"
    assert report["bounded_direct_consumer_scan"] == {
        "roots": ("ha_ctse_process", "envs", "scripts"),
        "result": "NO_DIRECT_PRODUCTION_CONSUMER_REFERENCE",
    }
    assert b"ABSENT_ACTIVE_EOCIV_OBJECTS" not in eociv.canonical_report_bytes()
    assert "outcome-bearing trial" in report["future_explorer_choice"]
    assert report["non_claims"] == (
        "targeting value",
        "generic masking value",
        "semantic staleness",
        "utility or return",
    )
