from __future__ import annotations

from dataclasses import replace
import inspect
import pytest

from ha_ctse_process.dynamic_roster_opportunity_audit import (
    ACTION_SEED,
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    EVALUATION_TASK_SEED,
    EXPECTED_SHORT_REQUIREMENT,
    FRONTIER_STREAM_ID,
    HORIZON,
    OPPORTUNITY_FRONTIER_SEED,
    OPPORTUNITY_STREAM_ID,
    SHORT_STREAK_TARGET,
    SHORT_WINDOW,
    classify_short_contributions,
    make_tiny_authority_ledger,
    replay_behavior_arm,
    simulate_frontier_action_plan,
    solve_frontier_hindsight_bruteforce,
    solve_frontier_hindsight_episode,
)
from scripts.run_clean_process_opportunity_authority_audit import (
    DEFAULT_LATEST,
    DEFAULT_SOURCE_RESULT,
    DEFAULT_UPDATE_ZERO,
    run_opportunity_authority_audit,
)


def test_read_only_opportunity_authority_and_use_audit_contract(tmp_path) -> None:
    tiny = make_tiny_authority_ledger()
    dynamic = solve_frontier_hindsight_episode(tiny)
    brute = solve_frontier_hindsight_bruteforce(tiny)
    assert dynamic.outcome_pairs == brute.outcome_pairs
    assert dynamic.outcome_pairs

    illegal_plan = [
        {0: 0, 1: 0},
        {0: 1},
        {0: 0},
        {1: 0},
    ]
    with pytest.raises(ValueError, match="non-frontier"):
        simulate_frontier_action_plan(tiny, illegal_plan)

    poisoned = replace(
        tiny,
        frontiers=(tiny.frontiers[0], (0,), *tiny.frontiers[2:]),
    )
    assert poisoned.frontiers != tiny.frontiers
    assert "ledger" not in inspect.signature(replay_behavior_arm).parameters

    unique = classify_short_contributions(
        [
            {"wave_index": 0, "time": 2, "owner": 0, "class": "PREWAVE_SHORT"},
            {
                "wave_index": 0,
                "time": 3,
                "owner": 1,
                "class": "POSTWAVE_MULTIOWNER_LATER",
            },
        ]
    )
    assert unique["valid"]
    duplicated = classify_short_contributions(
        [
            {"wave_index": 0, "time": 2, "owner": 0, "class": "PREWAVE_SHORT"},
            {
                "wave_index": 0,
                "time": 2,
                "owner": 0,
                "class": "POSTWAVE_SINGLETON",
            },
        ]
    )
    assert not duplicated["valid"]

    result = run_opportunity_authority_audit(
        output_root=tmp_path / "opportunity-audit-smoke",
        source_result=DEFAULT_SOURCE_RESULT,
        update_zero=DEFAULT_UPDATE_ZERO,
        latest=DEFAULT_LATEST,
        device="cpu",
        batch_size=1,
        smoke=True,
        smoke_episodes=1,
    )
    assert result["status"] == "SMOKE_COMPLETE"
    assert result["formal_evidence"] is False
    assert result["implementation_valid"] is True, result["audit"]
    assert all(result["reproduction"][arm]["valid"] for arm in result["reproduction"])
    assert result["audit"]["tiny_dp_bruteforce_equal"]
    assert result["audit"]["full_step_constructive_reproduced"]
    assert result["audit"]["frontier_action_constraint"]
    assert result["audit"]["primitive_action_identity"]
    assert result["audit"]["future_ledger_solver_only"]
    assert result["audit"]["unique_contribution_classification"]
    assert result["audit"]["zero_optimizer_steps"]
    assert result["audit"]["zero_parameter_drift"]
    assert result["working_vs_initial"]["optimizer_steps"] == 0
    assert result["working_vs_initial"]["high_tensor_drift"] == 0.0
    assert result["working_vs_initial"]["row_count"] > 0
    for arm in ("learned", "frozen", "oracle"):
        replay = result["behavior_use"][arm]
        assert replay["optimizer_steps"] == 0
        assert replay["high_tensor_drift"] == 0.0
        trace = replay["traces"][0]
        assert trace["classification_valid"]
        assert sum(trace["contribution_counts"].values()) == pytest.approx(
            replay["short"][0] * EXPECTED_SHORT_REQUIREMENT
        )

    contract = result["contract"]
    assert contract["episode_ids"] == [0]
    assert contract["horizon"] == HORIZON == 80
    assert contract["short_window"] == SHORT_WINDOW == 4
    assert contract["short_streak_target"] == SHORT_STREAK_TARGET == 2
    assert contract["short_required_total"] == EXPECTED_SHORT_REQUIREMENT == 24
    assert contract["seeds"] == {
        "evaluation_task": EVALUATION_TASK_SEED,
        "opportunity_frontier": OPPORTUNITY_FRONTIER_SEED,
        "opportunity_stream": OPPORTUNITY_STREAM_ID,
        "frontier_stream": FRONTIER_STREAM_ID,
        "action": ACTION_SEED,
        "bootstrap": BOOTSTRAP_SEED,
    }
    assert EVALUATION_TASK_SEED == 97_057
    assert OPPORTUNITY_FRONTIER_SEED == 77_057
    assert OPPORTUNITY_STREAM_ID == 0
    assert FRONTIER_STREAM_ID == 1
    assert ACTION_SEED == 87_057
    assert BOOTSTRAP_SEED == 107_057
    assert contract["bootstrap_resamples"] == BOOTSTRAP_REPETITIONS == 10_000
    assert contract["optimizer_steps"] == {"high": 0, "low": 0}
    assert result["runner_selects_successor"] is False
    assert (
        tmp_path
        / "opportunity-audit-smoke"
        / "result"
        / "clean_supplied_executor_opportunity_authority_audit.json"
    ).is_file()
    assert (
        tmp_path / "opportunity-audit-smoke" / "runner_status.txt"
    ).is_file()
