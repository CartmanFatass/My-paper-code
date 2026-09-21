"""Engineering fixtures for C06 output and accounting; no study score is claimed."""

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.skill_information_refresh.c01.host import DONE
from experiments.candidates.skill_information_refresh.c06 import study
from experiments.candidates.skill_information_refresh.c06.study import (
    Config,
    _contrast,
    _select_threshold,
    _threshold_requests,
    run_study,
)


def tiny_config(**changes):
    values = dict(seed=17, model_seed=10017, horizon=48, batch=2, particles=2,
        selection_episodes=2, eval_episodes=2, thresholds=(-.05, .05))
    values.update(changes)
    return Config(**values)


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_threshold_ties_use_active_first_and_selection_ties_are_prespecified():
    delta = np.array([.1, 0., -.1, 0.])
    active = np.array([False, True, True, False])
    assert _threshold_requests(delta, 0., active).tolist() == [True, True, False, False]

    candidates = [
        dict(threshold=.1, reading=dict(mean_completed_jobs=5.)),
        dict(threshold=-.1, reading=dict(mean_completed_jobs=5.)),
        dict(threshold=.2, reading=dict(mean_completed_jobs=6.)),
        dict(threshold=-.2, reading=dict(mean_completed_jobs=6.)),
    ]
    assert _select_threshold(candidates)["threshold"] == -.2
    candidates[-2]["reading"]["mean_completed_jobs"] = 5.
    candidates[-1]["reading"]["mean_completed_jobs"] = 5.
    assert _select_threshold(candidates)["threshold"] == -.1


def test_complete_fixture_outputs_counts_selection_and_raw_arithmetic(tmp_path):
    out = tmp_path / "complete"
    out.mkdir()
    native = {
        "launch-manifest.json": "manifest\n",
        "admission-preflight.json": "preflight\n",
        "launch-status.json": "status\n",
        "stdout.log": "native stdout\n",
        "stderr.log": "native stderr\n",
        ".hmasd-launch-fixture.tmp": "in-flight native atomic publication\n",
    }
    for name, content in native.items():
        (out / name).write_text(content, encoding="utf-8")
    result = run_study(out, "a" * 40, tiny_config())
    assert result["status"] == "COMPLETE"
    for name, content in native.items():
        assert (out / name).read_text(encoding="utf-8") == content
    counts = result["counts"]
    assert counts["started_fits"] == counts["optimizer_steps"] == 0
    assert counts["train_episodes"] == counts["train_transitions"] == 0
    assert counts["evaluation_optimizer_steps"] == 0
    assert counts["rule_search_arms"] == 4
    assert counts["selection_episodes"] == counts["rule_search_exposure_episodes"] == 8
    assert counts["eval_episodes"] == 6
    assert counts["selection_transitions"] == 8 * 48
    assert counts["eval_transitions"] == 6 * 48
    assert counts["actual_transitions"] == 14 * 48
    assert counts["belief_observation_record_calls"] == (4 + 2) * 2 * 48
    assert counts["belief_observation_rows"] == counts["belief_observation_record_calls"] * 2
    assert counts["belief_packet_update_rows"] > 0
    assert counts["belief_contradiction_rows"] == 0
    assert counts["model_root_decisions"] > 0
    assert counts["model_branch_transitions"] > counts["model_root_decisions"]
    assert counts["eval_model_root_decisions"] > 0
    assert counts["selection_model_root_decisions"] > 0

    assert (out / "updates.jsonl").read_text(encoding="utf-8") == ""
    saved_config = json.loads((out / "config.json").read_text())
    assert saved_config["model_seed"] == 10017
    assert saved_config["source_sha"] == "a" * 40
    assert result["source_sha"] == "a" * 40
    assert len(result["trace_files"]) == 3
    selection = json.loads((out / "selection.json").read_text())
    assert len(selection["candidates"]) == 4
    assert set(selection["selected"]) == {"NEAR_COMMIT", "LONG"}
    assert selection["final_selection"] == "none"
    assert result["final_selection"] == "none"

    rows = read_rows(out / "episodes.jsonl")
    assert len(rows) == 14
    assert all(row["jobs_started"] == 7 and row["packets"] == 12 and row["bytes"] == 96
        for row in rows)
    final_rows = {arm: sorted(
        [row for row in rows if row["phase"] == "eval" and row["arm"] == arm],
        key=lambda row: row["world_id"])
        for arm in ("NEAR_COMMIT", "LONG", "ACTIVE_FIRST")}

    for arm in final_rows:
        trace_names = result["final"][arm]["traces"]
        assert len(trace_names) == 1
        with np.load(out / trace_names[0]) as trace:
            assert trace["world_ids"].tolist() == [0, 1]
            assert trace["own"].shape == (2, 48, 2, 5)
            assert trace["belief_weights"].shape == (2, 48, 22)
            assert trace["diagnostic_physical_payloads"].shape == (2, 48, 2, 5)
            assert np.isfinite(trace["predicted_delta"]).all()
            assert np.all(trace["predicted_delta"][~trace["evaluated"]] == 0)
            for row_index, row in enumerate(final_rows[arm]):
                assert trace["reward"][row_index].sum() == row["completed_jobs"]
                assert trace["completed_jobs"][row_index].sum() == row["completed_jobs"]
                assert trace["conflicts"][row_index].sum() == row["conflicts"]
                assert trace["wait_ticks"][row_index].sum() == row["wait_ticks"]
                assert trace["bypass_jobs"][row_index].sum() == row["bypass_jobs"]
                assert trace["jobs_started"][row_index].sum() == row["jobs_started"]
                assert trace["packets"][row_index].sum() == row["packets"]
                assert trace["sent"][row_index].sum() == row["packets"]
            if arm == "ACTIVE_FIRST":
                assert not trace["evaluated"].any()
                assert not trace["belief_weights"].any()
            else:
                np.testing.assert_allclose(trace["belief_weights"].sum(axis=2), 1.)

    for name, (left, right) in {
            "LONG-NEAR_COMMIT": ("LONG", "NEAR_COMMIT"),
            "LONG-ACTIVE_FIRST": ("LONG", "ACTIVE_FIRST"),
            "NEAR_COMMIT-ACTIVE_FIRST": ("NEAR_COMMIT", "ACTIVE_FIRST")}.items():
        expected = [a["completed_jobs"] - b["completed_jobs"]
            for a, b in zip(final_rows[left], final_rows[right])]
        comparison = result["contrasts"][name]["completed_jobs"]
        assert comparison["per_world_difference"] == expected
        assert comparison["positive"] + comparison["negative"] + comparison["tied"] == 2
        assert comparison["mean"] == pytest.approx(np.mean(expected))
        assert np.isfinite(comparison["conditional_world_se"])

    with pytest.raises(FileExistsError):
        run_study(out, "a" * 40, tiny_config())


def test_exact_value_ties_match_active_first_on_all_optional_slots(tmp_path, monkeypatch):
    def tied_values(record, weights, states, ids, *, counters, **kwargs):
        size = len(ids)
        counters["model_root_decisions"] += size
        return dict(hold=np.zeros(size), send=np.zeros(size), delta=np.zeros(size),
            se=np.zeros(size), particles=2, model_branch_transitions=0,
            model_initialization_worlds=0, synthetic_advance_draws=0,
            synthetic_job_draws=0, end=record.t + 1,
            near_end=np.full((size, 2), record.t + 1),
            opportunity_tick=np.full((size, 2), record.t + 1),
            opportunity_kind=np.full((size, 2), 2),
            near_hold_samples=np.zeros((size, 2)), near_send_samples=np.zeros((size, 2)),
            long_hold_samples=np.zeros((size, 2)), long_send_samples=np.zeros((size, 2)),
            diagnostics={})

    monkeypatch.setattr(study, "paired_values", tied_values)
    out = tmp_path / "ties"
    result = run_study(out, "b" * 40, tiny_config(thresholds=(0.,)))
    active_name = result["final"]["ACTIVE_FIRST"]["traces"][0]
    with np.load(out / active_name) as active_trace:
        active_requests = active_trace["requests"].copy()
        active_sent = active_trace["sent"].copy()
    for arm in ("NEAR_COMMIT", "LONG"):
        with np.load(out / result["final"][arm]["traces"][0]) as trace:
            for tick in range(48):
                sender = tick % 2
                expected_active = trace["own"][:, tick, sender, 0] != DONE
                np.testing.assert_array_equal(
                    trace["requests"][:, tick][trace["evaluated"][:, tick]],
                    expected_active[trace["evaluated"][:, tick]])
            # ACTIVE_FIRST also requests while forced or spent; modeled rules leave
            # those inputs false and rely on the frozen host's forced/spent handling.
            assert np.array_equal(trace["sent"], active_sent)
    assert active_requests.shape == (2, 48)


def test_late_model_failure_preserves_completed_rows_and_partial_work(tmp_path, monkeypatch):
    original = study.paired_values
    long_calls = 0

    def fail_second_long(*args, **kwargs):
        nonlocal long_calls
        result = original(*args, **kwargs)
        if kwargs["phase"] == 21 and kwargs["mode"] == "LONG":
            long_calls += 1
            if long_calls == 2:
                raise RuntimeError("injected late model failure")
        return result

    monkeypatch.setattr(study, "paired_values", fail_second_long)
    out = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="injected late model failure"):
        run_study(out, "c" * 40, tiny_config(thresholds=(0.,)))
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "TECHNICAL_FAILURE"
    assert summary["error"] == {
        "type": "RuntimeError", "message": "injected late model failure"}
    assert summary["counts"]["selection_episodes"] == 4
    assert summary["counts"]["selection_transitions"] == 4 * 48
    assert summary["counts"]["eval_episodes"] == 2
    assert 2 * 48 < summary["counts"]["eval_transitions"] < 4 * 48
    assert summary["counts"]["eval_model_root_decisions"] > 0
    assert summary["counts"]["actual_transitions"] == (
        summary["counts"]["selection_transitions"] + summary["counts"]["eval_transitions"])
    assert len(read_rows(out / "episodes.jsonl")) == 6
    assert any(item["arm"] == "NEAR_COMMIT" and item["complete"]
        for item in summary["trace_files"])
    assert any(item["arm"] == "LONG" and not item["complete"]
        for item in summary["trace_files"])
    for item in summary["trace_files"]:
        assert (out / item["file"]).is_file()
    diagnostics = summary["root_diagnostics"]
    assert 0 < diagnostics["retained"] <= 64
    assert diagnostics["retained"] <= diagnostics["eligible_roots"]
    for item in diagnostics["records"]:
        with np.load(out / item["file"]) as root:
            near = root["near_send_samples"] - root["near_hold_samples"]
            long = root["long_send_samples"] - root["long_hold_samples"]
            assert item["delta_near"] == near.mean()
            assert item["delta_tail"] == (long - near).mean()
            assert root["model_sent"].shape[:2] == (2, 2)
            assert root["model_payloads"].shape[-2:] == (2, 5)
            assert not root["model_sent"][0, :, 0].any()
            assert root["model_sent"][1, :, 0].all()
    assert (out / "updates.jsonl").read_text() == ""


def test_cli_validates_then_refuses_without_admission(tmp_path):
    root = Path(__file__).resolve().parents[5]
    runner = root / "scripts/run_sir_c06.py"
    out = tmp_path / "unadmitted"
    invalid = subprocess.run([sys.executable, str(runner), "--out", str(out),
        "--launch-sha", "a" * 40, "--model-seed", "-1"], cwd=root,
        capture_output=True, text=True, check=False)
    assert invalid.returncode != 0
    assert "seeds must be nonnegative" in invalid.stderr
    assert "missing HMASD admission" not in invalid.stderr
    assert not out.exists()

    refused = subprocess.run([sys.executable, str(runner), "--out", str(out),
        "--launch-sha", "a" * 40], cwd=root,
        capture_output=True, text=True, check=False)
    assert refused.returncode != 0
    assert "missing HMASD admission" in refused.stderr
    assert not out.exists()


def test_config_rejects_invalid_fixed_protocol_values():
    with pytest.raises(ValueError, match="multiple of 48"):
        tiny_config(horizon=47)
    with pytest.raises(ValueError, match="particles"):
        tiny_config(particles=1)
    with pytest.raises(ValueError, match="unique"):
        tiny_config(thresholds=(0., 0.))


def test_contrast_requires_the_same_ordered_world_panel():
    left = [dict(world_id=0, completed_jobs=1, service=.5),
        dict(world_id=1, completed_jobs=2, service=1.)]
    with pytest.raises(ValueError, match="ordered world IDs"):
        _contrast(left, list(reversed(left)))


def test_root_diagnostics_are_order_and_outcome_blind(tmp_path):
    from experiments.candidates.skill_information_refresh.c01.host import CrossingHost, Worlds
    from experiments.candidates.skill_information_refresh.c06.belief import take_local
    host = CrossingHost(Worlds.make(19, 20, (0,), 48))
    record = take_local(host, 0)

    def collect(order, sign):
        roots = study.RootDiagnostics(limit=3)
        for world_id in order:
            samples = np.full((1, 2), sign * world_id)
            values = dict(near_hold_samples=np.zeros((1, 2)), near_send_samples=samples,
                long_hold_samples=np.zeros((1, 2)), long_send_samples=2 * samples,
                near_end=np.full((1, 2), 16), opportunity_tick=np.full((1, 2), 1),
                opportunity_kind=np.full((1, 2), 2), diagnostics={})
            roots.offer(record, (world_id,), values, np.array([True]), np.ones((1, 22)) / 22)
        return roots

    left, right = collect(range(20), 1), collect(reversed(range(20)), -1)
    expected = sorted(study.RootDiagnostics.key(world_id, 0) for world_id in range(20))[:3]
    assert sorted(left.records) == sorted(right.records) == expected
    index = left.save(tmp_path)
    assert index["eligible_roots"] == 20 and index["retained"] == 3
    for row in index["records"]:
        with np.load(tmp_path / row["file"]) as data:
            assert row["delta_tail"] == row["world_id"]
            assert data["root_world_id"] == row["world_id"]
            assert row["half_sample_deltas"]["long"] == [2 * row["world_id"]] * 2
