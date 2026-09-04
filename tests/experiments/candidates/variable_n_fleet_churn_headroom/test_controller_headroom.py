from __future__ import annotations

from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import sys
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
    aggregate_worlds,
    classify_means,
    native_fixture_bytes,
    prospective_cost,
    regenerate_r02_world,
)
from experiments.candidates.variable_n_fleet_churn_headroom.native_backend import (
    _analysis_binary_path,
    _linux_build_command,
    build_analysis_backend,
    select_top_k_fixture,
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
    assert world["search_storage"]["max_current_frontier_capacity"] == 1
    assert world["search_storage"]["max_next_selector_capacity"] == 1
    assert world["search_storage"]["max_live_nodes_high_water"] <= 3
    assert world["validity"]["selector_conformance"] is True
    assert world["resources"]["peak_rss_bytes"] > 0
    for decision in world["bcrh_decisions"]:
        assert len(decision["candidate_records"]) == decision["candidate_count"]
        assert all(record["exact_match"] for record in decision["candidate_records"])
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
        "validity": {"complete": True, "complete_except_resource": True},
    }
    native = {
        "search_storage": {
            "conservative_fixed_storage_allowance_bytes": 1,
            "max_total_owned_bytes_high_water": 1,
        }
    }
    clock = iter((0.0, 0.0, 60.0, 60.0, 60.0))
    monkeypatch.setattr(runner.time, "perf_counter", lambda: next(clock))
    monkeypatch.setattr(runner, "run_headroom_fixture", lambda *_args: native)
    monkeypatch.setattr(runner, "summarize_world", lambda *_args: world)
    monkeypatch.setattr(runner, "peak_rss_bytes", lambda: 1)
    summary = runner.run(
        SimpleNamespace(
            toy=True,
            seed=1,
            beam_width=1,
            max_wall_seconds=59.0,
            launch_sha="toy",
            preflight_receipt="toy",
            capacity_pilot=False,
        )
    )
    assert summary["completed_worlds"] == 1
    assert summary["result"] == {"branch": "INCOMPLETE"}


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="historical R09 interactive cross-check is MSVC-only",
)
def test_epoch_zero_failed_service_tie_uses_native_lexicographic_command(
    toy_summary: dict[str, object],
) -> None:
    fixture = deterministic_general_episode(1)
    with NativeInteractiveBatch((fixture,)) as batch:
        facts = batch.bcrh(include_candidate_records=True)[0]
    key = lambda command: tuple(255 if value is None else value for value in command)
    expected = min((record["command"] for record in facts["candidate_records"]), key=key)
    beam_first = toy_summary["worlds"][0]["trajectories"][  # type: ignore[index]
        "ORACLE_BEAM_FAIL60_K1024_MEMBOUND"
    ][0]
    assert tuple(beam_first) == tuple(expected)


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="historical R09 interactive cross-check is MSVC-only",
)
def test_bcrh_path_matches_unchanged_interactive_native_api(
    toy_summary: dict[str, object],
) -> None:
    fixture = deterministic_general_episode(1)
    commands = []
    candidate_counts = []
    candidate_records = []
    with NativeInteractiveBatch((fixture,)) as batch:
        endpoint_after_epoch_two = None
        terminal = None
        for epoch in range(6):
            facts = batch.bcrh(include_candidate_records=True)[0]
            commands.append(facts["scorer_command"])
            candidate_counts.append(facts["candidate_count"])
            candidate_records.append(facts["candidate_records"])
            terminal = batch.step((facts["scorer_command"],))[0]
            if epoch == 2:
                endpoint_after_epoch_two = terminal["fail_endpoint"]
    world = toy_summary["worlds"][0]  # type: ignore[index]
    assert world["trajectories"]["BCRH"] == [list(command) for command in commands]
    assert [row["candidate_count"] for row in world["bcrh_decisions"]] == candidate_counts
    for actual, expected in zip(world["bcrh_decisions"], candidate_records):
        projected = tuple(
            {
                "command": tuple(record["command"]),
                "exact_match": record["exact_match"],
            }
            for record in actual["candidate_records"]
        )
        assert projected == expected
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
    cost = prospective_cost(1024, 16)
    assert cost["beam_expansions_per_world_upper_bound"] == 4_018_089
    assert cost["beam_expansions_total_upper_bound"] == 64_289_424
    assert cost["beam_native_ticks_total_upper_bound"] == 1_285_788_480
    assert cost["persistent_native_ticks_total_upper_bound"] == 1_882_560
    assert cost["bcrh_decision_calls"] == 96
    assert cost["bcrh_scored_candidates_upper_bound"] == 188_256
    assert cost["result_blind_projected_wall_seconds"] == 723.80
    assert cost["projection_within_wall_cap"] is True


@pytest.mark.parametrize(
    ("aggregate_l", "zone_l", "expected"),
    [
        (Fraction(1, 10), {1: Fraction(1, 10), 2: Fraction(1, 5)}, "MB1024-A"),
        (Fraction(1, 10), {1: Fraction(1, 10), 2: Fraction(9, 100)}, "MB1024-D"),
        (Fraction(9, 100), {1: Fraction(1, 5), 2: Fraction(1, 5)}, "MB1024-D"),
    ],
)
def test_ordered_branch_arithmetic(
    aggregate_l: Fraction,
    zone_l: dict[int, Fraction],
    expected: str,
) -> None:
    assert classify_means(aggregate_l, zone_l)[0] == expected


@pytest.mark.parametrize(
    ("inventory", "width"),
    [
        (((1, (4,)), (9, (3,)), (5, (2,)), (7, (1,))), 3),
        (((5, (3,)), (5, (1,)), (5, (2,)), (4, (0,))), 3),
        (((5, (1, 2, 9)), (5, (1, 2, 3)), (5, (1, 3, 0))), 2),
        (((10, (0,)), (9, (1,)), (1, (2,)), (8, (3,))), 2),
    ],
)
def test_native_fixed_selector_matches_materialize_and_sort(
    inventory: tuple[tuple[int, tuple[int, ...]], ...], width: int
) -> None:
    prefix_size = len(inventory[0][1])
    selected, _ = select_top_k_fixture(inventory, width, prefix_size)
    expected = tuple(
        sorted(
            range(len(inventory)),
            key=lambda index: (-inventory[index][0], inventory[index][1]),
        )[:width]
    )
    assert selected == expected


def test_native_fixed_selector_replaces_repeatedly_after_saturation() -> None:
    inventory = tuple((score, (10 - score,)) for score in range(1, 11))
    selected, replacements = select_top_k_fixture(inventory, 3, 1)
    assert selected == (9, 8, 7)
    assert replacements == 7


def test_aggregate_refuses_nonregression_failure() -> None:
    worlds = []
    for zone in (1, 2):
        for row in range(8):
            worlds.append(
                {
                    "zone": zone,
                    "row": row,
                    "L": {"numerator": 1, "denominator": 10},
                    "U": {"numerator": 1, "denominator": 2},
                    "validity": {"complete": True},
                }
            )
    worlds[0]["validity"]["complete"] = False
    assert aggregate_worlds(worlds) == {
        "branch": "MB1024-INCOMPLETE",
        "reason": "missing_or_invalid_world",
    }


def test_resource_rule_requires_positive_os_rss_and_strict_2_gib_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    native = {
        "search_storage": {
            "conservative_fixed_storage_allowance_bytes": 4096,
            "max_total_owned_bytes_high_water": 8192,
        }
    }
    monkeypatch.setattr(runner, "peak_rss_bytes", lambda: 100_000)
    assert runner._resource_facts(native, 1.0)["strictly_below_2_gib"] is True
    monkeypatch.setattr(runner, "peak_rss_bytes", lambda: 0)
    assert runner._resource_facts(native, 1.0)["strictly_below_2_gib"] is False
    monkeypatch.setattr(runner, "peak_rss_bytes", lambda: 2 * 1024**3)
    assert runner._resource_facts(native, 1.0)["strictly_below_2_gib"] is False


def test_analysis_binary_and_linux_build_command_are_platform_exact() -> None:
    assert _analysis_binary_path("win32").suffix == ".dll"
    linux_binary = _analysis_binary_path("linux")
    assert linux_binary.suffix == ".so"
    command = _linux_build_command(linux_binary, compiler="g++")
    repository_root = Path(__file__).resolve().parents[4]
    assert command == (
        "g++",
        "-std=c++20",
        "-O2",
        "-fPIC",
        "-shared",
        "-fno-fast-math",
        "-ffp-contract=off",
        f"-I{repository_root / 'experiments/candidates/variable_n_fleet_churn_headroom/native'}",
        str(
            repository_root
            / "experiments/candidates/variable_n_fleet_churn_headroom/native/headroom_backend.cpp"
        ),
        "-o",
        str(linux_binary),
    )


def test_linux_peak_rss_uses_kib_to_byte_units(monkeypatch: pytest.MonkeyPatch) -> None:
    class Usage:
        ru_maxrss = 12_345

    class Resource:
        RUSAGE_SELF = object()

        @staticmethod
        def getrusage(who: object) -> Usage:
            assert who is Resource.RUSAGE_SELF
            return Usage()

    monkeypatch.setattr(runner.sys, "platform", "linux")
    monkeypatch.setitem(sys.modules, "resource", Resource)
    assert runner.peak_rss_bytes() == 12_345 * 1024


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux native load check")
def test_linux_shared_object_loads_exact_native_selector() -> None:
    assert build_analysis_backend().suffix == ".so"
    selected, replacements = select_top_k_fixture(
        ((1, (3,)), (5, (2,)), (4, (1,)), (6, (0,))), 2, 1
    )
    assert selected == (3, 1)
    assert replacements > 0
