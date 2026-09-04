from __future__ import annotations

from datetime import datetime, timezone
from fractions import Fraction
import json
import time
from types import SimpleNamespace

import pytest

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import (
    deterministic_general_episode,
)
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import (
    NativeInteractiveBatch,
)
from experiments.candidates.variable_n_fleet_churn_headroom.analysis import (
    classify_means,
    native_fixture_bytes,
    prospective_cost,
    regenerate_r02_world,
)
from experiments.candidates.variable_n_fleet_churn_headroom.native_backend import (
    build_analysis_backend,
)
from scripts import run_vnfc_bpcr_r02 as r02
from scripts import run_vnfc_controller_headroom as runner


@pytest.fixture(scope="module")
def toy_summary(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    build_analysis_backend()
    root = tmp_path_factory.mktemp("vnfc-headroom")
    receipt = root / "preflight.json"
    receipt.write_text("{}\n", encoding="utf-8")
    output = root / "result"
    started = time.perf_counter()
    status = runner.main(
        [
            "--output-root", str(output),
            "--preflight-receipt", str(receipt),
            "--launch-sha", "toy-sha",
            "--beam-width", "1",
            "--max-wall-seconds", "59",
            "--toy",
        ]
    )
    elapsed = time.perf_counter() - started
    assert status == 0
    assert elapsed < 60
    return json.loads((output / "summary.json").read_text(encoding="utf-8"))


def test_toy_runner_smoke_and_beam_accounting(toy_summary: dict[str, object]) -> None:
    assert toy_summary["result"]["branch"] == "TOY_COMPLETE"  # type: ignore[index]
    assert toy_summary["completed_worlds"] == 1
    world = toy_summary["worlds"][0]  # type: ignore[index]
    assert world["validity"]["complete"] is True
    for depth in world["beam_depths"]:
        assert depth["expansions"] == depth["legal_commands"]
        assert depth["native_ticks"] == 20 * depth["expansions"]
    assert world["beam_depths"][0]["states_before"] == 1
    assert world["beam_depths"][0]["states_retained"] == 1
    assert toy_summary["measured_cost"]["measurement_source"] == "this_invocation"  # type: ignore[index]
    assert toy_summary["measured_cost"]["measurement_is_result_blind_prelaunch_calibration"] is False  # type: ignore[index]


def test_wall_cap_is_checked_at_the_final_world_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    world = {
        "beam_depths": (),
        "counts": {
            "persist_candidates": 0,
            "persist_native_ticks": 0,
            "bcrh_decision_calls": 0,
            "terminal_completion_native_ticks": 0,
        },
        "bcrh_decisions": (),
        "validity": {"complete": True},
    }
    clock = iter((0.0, 60.0, 60.0))
    monkeypatch.setattr(runner.time, "perf_counter", lambda: next(clock))
    monkeypatch.setattr(runner, "run_headroom_fixture", lambda *_args: {})
    monkeypatch.setattr(runner, "summarize_world", lambda *_args: world)
    summary = runner.run(
        SimpleNamespace(
            toy=True,
            seed=1,
            beam_width=1,
            max_wall_seconds=59.0,
            launch_sha="toy",
            preflight_receipt="toy",
        )
    )
    assert summary["completed_worlds"] == 1
    assert summary["result"] == {"branch": "INCOMPLETE"}


def test_epoch_zero_failed_service_tie_uses_native_lexicographic_command(
    toy_summary: dict[str, object],
) -> None:
    fixture = deterministic_general_episode(1)
    with NativeInteractiveBatch((fixture,)) as batch:
        facts = batch.bcrh(include_candidate_records=True)[0]
    key = lambda command: tuple(255 if value is None else value for value in command)
    expected = min((record["command"] for record in facts["candidate_records"]), key=key)
    beam_first = toy_summary["worlds"][0]["trajectories"]["ORACLE_BEAM_FAIL60"][0]  # type: ignore[index]
    assert tuple(beam_first) == tuple(expected)


def test_bcrh_path_matches_unchanged_interactive_native_api(
    toy_summary: dict[str, object],
) -> None:
    fixture = deterministic_general_episode(1)
    commands = []
    candidate_counts = []
    with NativeInteractiveBatch((fixture,)) as batch:
        endpoint_after_epoch_two = None
        terminal = None
        for epoch in range(6):
            facts = batch.bcrh(include_candidate_records=True)[0]
            commands.append(facts["scorer_command"])
            candidate_counts.append(facts["candidate_count"])
            terminal = batch.step((facts["scorer_command"],))[0]
            if epoch == 2:
                endpoint_after_epoch_two = terminal["fail_endpoint"]
    world = toy_summary["worlds"][0]  # type: ignore[index]
    assert world["trajectories"]["BCRH"] == [list(command) for command in commands]
    assert [row["candidate_count"] for row in world["bcrh_decisions"]] == candidate_counts
    endpoint = world["endpoints"]["BCRH"]
    assert (endpoint["numerator"], endpoint["denominator"]) == tuple(endpoint_after_epoch_two)
    assert terminal["terminal"] is True
    assert terminal["safety_violation"] is False
    assert terminal["exclusivity_violation"] is False


def test_r02_evaluation_source_assigns_heldout_n7_purpose(monkeypatch: pytest.MonkeyPatch) -> None:
    source = r02.install_r02()
    calls = []

    def fake_build_world(_rng, _config, **kwargs):
        calls.append(kwargs)
        return object()

    def fake_learned(*_args, **kwargs):
        return {"rollouts": 8, "arm": kwargs.get("arm", _args[5]), "relabel_mismatch_count": 0}

    monkeypatch.setattr(source, "_build_world", fake_build_world)
    monkeypatch.setattr(source, "_evaluate_learned_batch", fake_learned)
    monkeypatch.setattr(
        source,
        "_evaluate_bcrh_batch",
        lambda *_args, **_kwargs: {"rollouts": 8},
    )
    config = source.BExploreRunConfig(source.PRIMARY_STAGE, 2026090321, 64)
    models = {
        checkpoint: {arm: object() for arm in source.ARMS}
        for checkpoint in source.CHECKPOINTS
    }
    source._execute_evaluation(
        config,
        object(),
        object(),
        models,
        datetime(2026, 9, 4, tzinfo=timezone.utc),
    )
    n7 = [call for call in calls if call["roster_size"] == 7]
    assert len(n7) == 16
    assert {call["purpose"] for call in n7} == {"heldout-N7"}


def test_non_target_heldout_n7_world_is_byte_identical_to_r02_source() -> None:
    generated = regenerate_r02_world(
        seed=2026090321,
        updates=64,
        purpose="heldout-N7",
        roster_size=7,
        failed_zone=2,
        row=3,
    )
    source = r02.install_r02()
    config = source.BExploreRunConfig(source.PRIMARY_STAGE, 2026090321, 64)
    rng = source._SeedRNG(source.derive_seed_master(config)["master"])
    direct = source._build_world(
        rng,
        config,
        purpose="heldout-N7",
        roster_size=7,
        failed_zone=2,
        row=3,
        now=datetime(2026, 9, 4, tzinfo=timezone.utc),
    )
    assert native_fixture_bytes(generated) == native_fixture_bytes(direct)


def test_cost_projection_exactly_matches_card_law() -> None:
    cost = prospective_cost(256, 16)
    assert cost["beam_expansions_per_world_upper_bound"] == 1_005_993
    assert cost["beam_expansions_total_upper_bound"] == 16_095_888
    assert cost["beam_native_ticks_total_upper_bound"] == 321_917_760
    assert cost["persistent_native_ticks_total_upper_bound"] == 1_882_560
    assert cost["bcrh_decision_calls"] == 96
    assert cost["bcrh_scored_candidates_upper_bound"] == 188_256


@pytest.mark.parametrize(
    ("aggregate_l", "aggregate_u", "zone_l", "zone_u", "expected"),
    [
        (Fraction(1, 10), Fraction(1, 2), {1: Fraction(1, 10), 2: Fraction(1, 5)}, {1: Fraction(1, 2), 2: Fraction(1, 2)}, "CH-A"),
        (Fraction(0), Fraction(9, 100), {1: Fraction(0), 2: Fraction(0)}, {1: Fraction(9, 100), 2: Fraction(1, 20)}, "CH-B"),
        (Fraction(1, 20), Fraction(1, 5), {1: Fraction(1, 10), 2: Fraction(0)}, {1: Fraction(1, 2), 2: Fraction(9, 100)}, "CH-C"),
        (Fraction(1, 20), Fraction(1, 5), {1: Fraction(1, 20), 2: Fraction(1, 20)}, {1: Fraction(1, 5), 2: Fraction(1, 5)}, "CH-D"),
    ],
)
def test_ordered_branch_arithmetic(
    aggregate_l: Fraction,
    aggregate_u: Fraction,
    zone_l: dict[int, Fraction],
    zone_u: dict[int, Fraction],
    expected: str,
) -> None:
    assert classify_means(aggregate_l, aggregate_u, zone_l, zone_u)[0] == expected
