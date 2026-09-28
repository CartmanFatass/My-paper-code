"""B01 checks: joint rolling planner and readiness runner on the self-contained fixture."""

from __future__ import annotations

import ast
import importlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from envs.uav_service_restoration.adapter import make_parallel_env
from envs.uav_service_restoration.baselines import BackhaulAwareGreedyController
from envs.uav_service_restoration.config import load_config
from envs.uav_service_restoration.evaluation import rollout_controller
from experiments.candidates.uav_restoration_readiness.b01.joint_planner import (
    STAY,
    JointRollingLPController,
    _unit_towards,
)

ROOT = Path(__file__).resolve().parents[5]
FIXTURE = ROOT / "configs" / "uav_service_restoration" / "smoke_fixture.json"
RUNNER = (
    ROOT / "experiments" / "candidates" / "uav_restoration_readiness" / "b01" / "run_readiness.py"
)
SEED = 3


@pytest.fixture(scope="module")
def config():
    return load_config(str(FIXTURE))


@pytest.fixture(scope="module")
def guarded_rollout(config):
    """(a)+(b): one full rollout with privileged diagnostics forbidden inside act()."""

    env = make_parallel_env(config, seed=SEED)
    planner = JointRollingLPController(config)
    original_act = planner.act
    state = {"in_act": False, "privileged_calls_in_act": 0}
    original_privileged = env.get_privileged_diagnostics

    def forbidden_privileged():
        if state["in_act"]:
            state["privileged_calls_in_act"] += 1
            raise AssertionError("planner read get_privileged_diagnostics()")
        return original_privileged()

    def guarded_act(view, agents):
        state["in_act"] = True
        try:
            return original_act(view, agents)
        finally:
            state["in_act"] = False

    env.get_privileged_diagnostics = forbidden_privileged
    planner.act = guarded_act
    record = rollout_controller(env, planner, seed=SEED)
    return record, planner, state


def test_planner_full_episode_finite_and_view_only(guarded_rollout, config):
    record, planner, state = guarded_rollout
    satisfaction = record["references"]["controller_satisfaction"]
    assert math.isfinite(satisfaction) and 0.0 <= satisfaction <= 1.0 + 1e-9
    assert record["controller"]["name"] == "joint_rolling_lp"
    assert state["privileged_calls_in_act"] == 0
    assert len(planner.step_diagnostics) == int(config.n_decision_steps)
    planned = [item for item in planner.step_diagnostics if item["status"] == "planned"]
    assert planned, "the fixture's site failure should give the planner something to do"
    assert all(item["n_lp_failures"] == 0 for item in planned)
    assert all(item["n_lp_solves"] >= 1 for item in planned)


def test_planner_deterministic(guarded_rollout, config):
    _, first, _ = guarded_rollout
    env = make_parallel_env(config, seed=SEED)
    second = JointRollingLPController(config)
    rollout_controller(env, second, seed=SEED)
    targets_first = [item["chosen_targets"] for item in first.step_diagnostics]
    targets_second = [item["chosen_targets"] for item in second.step_diagnostics]
    assert targets_first == targets_second
    values_first = [item["best_value_mbps"] for item in first.step_diagnostics]
    values_second = [item["best_value_mbps"] for item in second.step_diagnostics]
    assert values_first == values_second


def test_k1_search_never_below_greedy_start_and_start_is_greedy(config):
    """(d) K=1: best LP value >= the greedy assignment's LP value at every planned step;
    the start is checked independently against the unmodified greedy's actions."""

    env = make_parallel_env(config, seed=SEED)
    planner = JointRollingLPController(config, top_k=1)
    greedy = BackhaulAwareGreedyController(config)
    planner.reset()
    env.reset(seed=SEED)
    n_planned = 0
    while env.agents:
        view = env.get_current_state()
        agents = list(env.agents)
        greedy_actions = greedy.act(view, agents)
        actions = planner.act(view, agents)
        item = planner.step_diagnostics[-1]
        positions = np.asarray(view["uav_positions"], dtype=np.float64)
        demand_xy = np.asarray(view["demand_point_positions"], dtype=np.float64)
        if item["status"] == "planned":
            n_planned += 1
            for index, agent in enumerate(agents):
                expected = _unit_towards(positions[index, :2], demand_xy[item["start_targets"][index]])
                np.testing.assert_allclose(greedy_actions[agent][:2], expected, atol=1e-6)
            # Independent re-evaluation of the greedy start's LP value.
            start_value, reason = planner.evaluate_assignment(
                view, tuple(item["start_targets"]), item["altitude_m"]
            )
            assert reason == "ok"
            assert start_value == pytest.approx(item["start_value_mbps"], rel=1e-9, abs=1e-9)
            assert item["best_value_mbps"] >= start_value
            assert len(item["candidate_slots"]) == 1
            assert all(t == STAY or t in item["candidate_slots"] or t in item["start_targets"]
                       for t in item["chosen_targets"])
        else:
            for agent in agents:
                assert not np.any(greedy_actions[agent])
                assert not np.any(actions[agent])
        env.step(actions)
    assert n_planned > 0


def _run(tmp_path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), "--config", str(FIXTURE), *extra],
        cwd=str(ROOT), capture_output=True, text=True, timeout=600,
    )


def test_runner_end_to_end_two_seeds(tmp_path):
    """(e) three default controllers x 2 seeds; paired fields and aggregate shape."""

    episodes = tmp_path / "episodes.json"
    episodes.write_text(json.dumps({"episode_seeds": [11, 12]}), encoding="utf-8")
    out = tmp_path / "out"
    completed = _run(tmp_path, "--episodes-file", str(episodes), "--out", str(out),
                     "--no-admission")
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["admission"] == "skipped (fixture test)"
    assert summary["data_status"] == "NOT_REAL_DATA"
    assert summary["information_condition"] == "central_delayed_telemetry"
    assert set(summary["controllers"]) == {"static_uav", "backhaul_aware_greedy",
                                           "joint_rolling_lp"}
    paired = summary["paired_differences"]
    for key in ("joint_rolling_lp_minus_backhaul_aware_greedy",
                "backhaul_aware_greedy_minus_static_uav"):
        for metric in ("controller_satisfaction", "fraction_of_lost_service_restored"):
            entry = paired[key][metric]
            for field in ("mean", "se", "n", "n_positive", "n_negative"):
                assert field in entry
            assert entry["n"] == 2
    assert len(summary["per_episode_wall"]) == 6
    for field in ("git_head", "interpreter", "arguments", "start_utc", "end_utc",
                  "config_sha256", "episodes_file_sha256"):
        assert summary[field]

    # Aggregate shape and values equal evaluate_baselines._aggregate on the same records.
    scripts_dir = str(ROOT / "scripts" / "uav_service_restoration")
    sys.path.insert(0, scripts_dir)
    try:
        evaluate_baselines = importlib.import_module("evaluate_baselines")
    finally:
        sys.path.remove(scripts_dir)
    for name, aggregate in summary["controllers"].items():
        records = []
        for seed in (11, 12):
            episode = json.loads(
                (out / "episodes" / name / f"{seed}.json").read_text(encoding="utf-8")
            )
            assert episode["wall_s"] > 0.0
            assert len(episode["uav_positions_per_decision_start"]) == 60
            record = episode["record"]
            # JSON stores NaN as null; the reference aggregator expects floats.
            if record["recovery"].get("fraction_of_lost_service_restored") is None:
                record["recovery"]["fraction_of_lost_service_restored"] = float("nan")
            records.append(record)
        reference = json.loads(json.dumps(evaluate_baselines._aggregate(records)))
        ours = {key: value for key, value in aggregate.items() if key != "episode_seeds"}
        assert set(ours) == set(reference)
        for key, value in reference.items():
            if isinstance(value, float):
                assert ours[key] == pytest.approx(value, rel=1e-12, abs=1e-12)
            else:
                assert ours[key] == value
    planner_episode = json.loads(
        (out / "episodes" / "joint_rolling_lp" / "11.json").read_text(encoding="utf-8")
    )
    assert planner_episode["planner"]["n_lp_solves_total"] > 0
    assert len(planner_episode["planner"]["step_diagnostics"]) == 60

    # Rerun into the same --out without --force is refused.
    again = _run(tmp_path, "--episodes-file", str(episodes), "--out", str(out),
                 "--no-admission")
    assert again.returncode == 2


def test_ideal_mode_requires_rationale(tmp_path):
    """(f)"""

    episodes = tmp_path / "episodes.json"
    episodes.write_text("[1]", encoding="utf-8")
    completed = _run(tmp_path, "--episodes-file", str(episodes), "--out",
                     str(tmp_path / "out"), "--no-admission",
                     "--information-mode", "ideal_full_current_demand")
    assert completed.returncode == 2
    assert "diagnostic-rationale" in completed.stderr
    assert not (tmp_path / "out").exists()


def test_no_admission_refused_for_non_fixture_config(tmp_path):
    episodes = tmp_path / "episodes.json"
    episodes.write_text("[1]", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(RUNNER), "--config",
         str(ROOT / "configs" / "uav_service_restoration" / "milan_site_outage.json"),
         "--episodes-file", str(episodes), "--out", str(tmp_path / "out"), "--no-admission"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=120,
    )
    assert completed.returncode == 2
    assert not (tmp_path / "out").exists()


def test_runner_carries_exactly_one_literal_admission_call():
    source = RUNNER.read_text(encoding="utf-8")
    assert 'require_admission(__file__, direction="uav_restoration_readiness")' in source
    tree = ast.parse(source)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", getattr(node.func, "attr", None)) == "require_admission"
    ]
    assert len(calls) == 1
    call = calls[0]
    assert isinstance(call.args[0], ast.Name) and call.args[0].id == "__file__"
    keywords = {keyword.arg: keyword.value for keyword in call.keywords}
    assert isinstance(keywords["direction"], ast.Constant)
    assert keywords["direction"].value == "uav_restoration_readiness"


def test_runner_passes_launcher_guard_contract():
    hmasd_launch = importlib.import_module("scripts.hmasd_launch")
    hmasd_launch._validate_guard_contract(RUNNER, "uav_restoration_readiness")
    with pytest.raises(hmasd_launch.LaunchRefusal):
        hmasd_launch._validate_guard_contract(RUNNER, "some_other_direction")


def test_wall_budget_stop_writes_well_formed_summary(tmp_path):
    episodes = tmp_path / "episodes.json"
    episodes.write_text("[1, 2]", encoding="utf-8")
    out = tmp_path / "out"
    completed = _run(tmp_path, "--episodes-file", str(episodes), "--out", str(out),
                     "--no-admission", "--max-wall-s", "0.000001")
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["stopped_by_wall_budget"] is True
    assert len(summary["episodes_not_started"]) == 6
    assert summary["per_episode_wall"] == []
    for aggregate in summary["controllers"].values():
        assert aggregate["n_episodes"] == 0
    for pair in summary["paired_differences"].values():
        for entry in pair.values():
            assert entry["n"] == 0 and entry["mean"] is None and entry["se"] is None


def test_idle_fallback_never_lowers_lp_value_and_occurs(guarded_rollout):
    """DM revision: (i) the idle fallback never lowers the per-step LP value (beyond the
    ascent's tie tolerance, and never below the greedy start); (ii) it occurs on the fixture."""

    _, planner, _ = guarded_rollout
    planned = [item for item in planner.step_diagnostics if item["status"] == "planned"]
    rel_tol = planner.parameters["value_rel_tol"]
    for item in planned:
        before = item["value_before_fallback_mbps"]
        after = item["value_after_fallback_mbps"]
        assert after == item["best_value_mbps"]
        assert after >= before - rel_tol * max(1.0, abs(before))
        assert after >= item["start_value_mbps"]
        assert item["n_fallback"] == len(item["fallback_uavs"]) <= item["n_zero_marginal_stay"]
        for uav in item["fallback_uavs"]:
            assert item["ascent_targets"][uav] == STAY
            assert item["chosen_targets"][uav] == item["start_targets"][uav]
            others = [t for i, t in enumerate(item["chosen_targets"]) if i != uav]
            assert item["chosen_targets"][uav] not in others
    assert sum(item["n_fallback"] for item in planned) >= 1
