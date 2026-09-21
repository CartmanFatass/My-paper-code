"""Engineering fixtures for C07 confirmation; no confirmation score is claimed."""

import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.skill_information_refresh.c07 import confirm
from experiments.candidates.skill_information_refresh.c07.confirm import (
    Config,
    _finite_mean_upper,
    _fixed_reading,
    _paired_contrast,
    run_confirmation,
)


def tiny_config(**changes):
    values = dict(
        world_seeds=(17, 18),
        model_seeds=(10017, 10018),
        phase=3,
        worlds_per_block=2,
        horizon=48,
        batch=2,
        particles=2,
    )
    values.update(changes)
    return Config(**values)


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_complete_fixture_preserves_fixed_program_pairing_counts_and_traces(tmp_path):
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

    result = run_confirmation(out, "a" * 40, tiny_config())
    assert result["status"] == "COMPLETE"
    assert result["program"] == {
        "arms": ["NEAR_COMMIT", "LONG", "ACTIVE_FIRST"],
        "modeled_threshold": 0.0,
        "development_selection": "none",
        "root_diagnostics": "none",
        "continuation": "ACTIVE_FIRST after the paired root intervention",
    }
    for name, content in native.items():
        assert (out / name).read_text(encoding="utf-8") == content
    assert (out / "updates.jsonl").read_text(encoding="utf-8") == ""
    saved = json.loads((out / "config.json").read_text(encoding="utf-8"))
    assert saved["fixed_program"] is True
    assert saved["world_seeds"] == [17, 18]
    assert saved["model_seeds"] == [10017, 10018]

    counts = result["counts"]
    assert counts["started_fits"] == counts["optimizer_steps"] == 0
    assert counts["train_episodes"] == counts["train_transitions"] == 0
    assert counts["selection_episodes"] == counts["rule_search_arms"] == 0
    assert counts["parameter_updates"] == 0
    assert counts["confirmation_episodes"] == 12
    assert counts["actual_transitions"] == 12 * 48
    assert counts["belief_observation_record_calls"] == 4 * 2 * 48
    assert counts["belief_observation_rows"] == 4 * 2 * 48 * 2
    assert counts["model_root_decisions"] > 0
    assert len(result["panels"]) == 6
    assert result["planned_accounting"]["episodes"] == 12
    assert result["planned_accounting"]["actual_transitions"] == 12 * 48
    assert len(result["blocks"]) == 2
    assert all(panel["complete"] and panel["completed_episodes"] == 2
        for panel in result["panels"])
    assert all(panel["wall_seconds"] >= 0 and panel["resources"]["ru_maxrss_child_kib"] > 0
        for panel in result["panels"])
    assert result["resources"]["ru_maxrss_child_kib"] > 0

    rows = read_rows(out / "episodes.jsonl")
    assert len(rows) == 12
    assert {(row["block"], row["world_seed"], row["model_seed"])
        for row in rows} == {(0, 17, 10017), (1, 18, 10018)}
    assert all(row["phase"] == "confirmation" for row in rows)
    assert all(row["jobs_started"] == 7 and row["packets"] == 12 and row["bytes"] == 96
        for row in rows)

    assert len(result["trace_files"]) == 6
    trace_names = [item["file"] for item in result["trace_files"]]
    assert len(set(trace_names)) == 6
    for item in result["trace_files"]:
        assert item["phase"].startswith(f"block{item['block']}_s{item['world_seed']}_m")
        trace_rows = sorted([
            row for row in rows
            if row["block"] == item["block"] and row["arm"] == item["arm"]
        ], key=lambda row: row["world_id"])
        with np.load(out / item["file"]) as trace:
            assert trace["world_ids"].tolist() == [0, 1]
            assert trace["own"].shape == (2, 48, 2, 5)
            for index, row in enumerate(trace_rows):
                assert trace["reward"][index].sum() == row["completed_jobs"]
                assert trace["completed_jobs"][index].sum() == row["completed_jobs"]
                assert trace["conflicts"][index].sum() == row["conflicts"]
                assert trace["wait_ticks"][index].sum() == row["wait_ticks"]
                assert trace["bypass_jobs"][index].sum() == row["bypass_jobs"]
                assert trace["jobs_started"][index].sum() == row["jobs_started"]
                assert trace["packets"][index].sum() == row["packets"]
                assert trace["sent"][index].sum() == row["packets"]

    for block_item in result["contrasts_by_block"]:
        assert block_item["world_seed"] == (17, 18)[block_item["block"]]
        for comparison in block_item["contrasts"].values():
            assert len(comparison["paired_units"]) == 2
            assert len(comparison["completed_jobs"]["per_world_difference"]) == 2
    for name, left, right in confirm.COMPARISONS:
        comparison = result["pooled_contrasts"][name]
        left_rows = [row for row in rows if row["arm"] == left]
        right_rows = [row for row in rows if row["arm"] == right]
        expected = [a["completed_jobs"] - b["completed_jobs"]
            for a, b in zip(left_rows, right_rows)]
        assert comparison["completed_jobs"]["per_world_difference"] == expected
        assert len(comparison["paired_units"]) == 4
        se = np.std(expected, ddof=1) / np.sqrt(4)
        assert comparison["completed_jobs"]["conditional_world_se"] == pytest.approx(se)
        assert comparison["completed_jobs"]["normal_95"]["lower"] == pytest.approx(
            np.mean(expected) - 1.96 * se)

    with pytest.raises(FileExistsError, match="never overwrites"):
        run_confirmation(out, "a" * 40, tiny_config())


def _metric(mean, lower=0.0, upper=0.0):
    return dict(mean=mean, normal_95=dict(lower=lower, upper=upper),
        per_world_difference=[0.] * 1280)


def test_fixed_reading_uses_strict_predeclared_boundaries(monkeypatch):
    blocks = [{
        "NEAR_COMMIT-ACTIVE_FIRST": {"completed_jobs": _metric(.01)},
    } for _ in range(5)]
    pooled = {
        "NEAR_COMMIT-ACTIVE_FIRST": {"completed_jobs": _metric(.1, lower=.051)},
        "LONG-NEAR_COMMIT": {"completed_jobs": _metric(0., upper=.049)},
    }
    reading = _fixed_reading(blocks, pooled)
    assert reading["primary"]["retained"] is True
    assert reading["secondary"]["extra_gain_bounded_below_margin"] is True
    # The normal interval is descriptive, so it cannot veto or grant the sparse bound.
    pooled["LONG-NEAR_COMMIT"]["completed_jobs"]["normal_95"]["upper"] = 14.
    assert _fixed_reading(blocks, pooled)["secondary"]["extra_gain_bounded_below_margin"] is True

    blocks[2]["NEAR_COMMIT-ACTIVE_FIRST"]["completed_jobs"]["mean"] = 0.0
    pooled["NEAR_COMMIT-ACTIVE_FIRST"]["completed_jobs"]["normal_95"]["lower"] = .05
    pooled["LONG-NEAR_COMMIT"]["completed_jobs"]["normal_95"]["upper"] = .05
    monkeypatch.setattr(confirm, "_finite_mean_upper", lambda differences, bound: .05)
    reading = _fixed_reading(blocks, pooled)
    assert reading["primary"]["all_block_means_positive"] is False
    assert reading["primary"]["pooled_lower_exceeds_margin"] is False
    assert reading["primary"]["retained"] is False
    assert reading["secondary"]["extra_gain_bounded_below_margin"] is False


def test_finite_bound_retains_unobserved_tail_and_uses_global_task_bound():
    zero = np.zeros(1280)
    expected = 14 * (1 - .025 ** (1 / 1280))
    assert _finite_mean_upper(zero, 14) == pytest.approx(expected, abs=1e-12)
    assert 0.04 < expected < .05
    sparse = zero.copy()
    sparse[:5] = 2
    direct = 14 - math.exp((5*math.log(12) + 1275*math.log(14) + math.log(.025))/1280)
    assert _finite_mean_upper(sparse, 14) == pytest.approx(direct, abs=1e-12)
    assert _finite_mean_upper(sparse, 14) < .05
    sparse[5] = 2
    assert _finite_mean_upper(sparse, 14) > .05
    sparse[0] = 14
    assert _finite_mean_upper(sparse, 14) == 14
    for invalid in ([], [15], [-15], [float('nan')], [[0, 0]]):
        with pytest.raises(ValueError, match="global bounds"):
            _finite_mean_upper(invalid, 14)


def test_paired_contrast_requires_ordered_block_seed_and_world_identity():
    def row(block, world, world_seed, model_seed):
        return dict(block=block, world_id=world, world_seed=world_seed,
            model_seed=model_seed, completed_jobs=1, service=.5)

    left = [row(0, 0, 17, 10017), row(1, 0, 18, 10018)]
    with pytest.raises(ValueError, match="ordered block/world"):
        _paired_contrast(left, list(reversed(left)))


def test_late_failure_preserves_completed_panel_and_current_trace_work(tmp_path, monkeypatch):
    original = confirm._run_batch
    calls = 0

    def fail_after_second_batch(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 2:
            raise RuntimeError("injected late confirmation failure")
        return result

    monkeypatch.setattr(confirm, "_run_batch", fail_after_second_batch)
    out = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="injected late confirmation failure"):
        run_confirmation(out, "b" * 40,
            tiny_config(world_seeds=(17,), model_seeds=(10017,)))

    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "TECHNICAL_FAILURE"
    assert summary["error"] == {
        "type": "RuntimeError", "message": "injected late confirmation failure"}
    assert len(summary["panels"]) == 2
    assert summary["panels"][0]["complete"] is True
    assert summary["panels"][1]["complete"] is False
    assert summary["counts"]["confirmation_episodes"] == 2
    assert summary["counts"]["actual_transitions"] == 4 * 48
    assert len(read_rows(out / "episodes.jsonl")) == 2
    assert len(summary["trace_files"]) == 2
    assert all((out / item["file"]).is_file() for item in summary["trace_files"])
    assert summary["trace_files"][1]["arm"] == "LONG"
    assert (out / "updates.jsonl").read_text(encoding="utf-8") == ""


def test_cli_validates_exact_interface_then_refuses_without_admission(tmp_path):
    root = Path(__file__).resolve().parents[5]
    runner = root / "scripts/run_sir_c07.py"
    out = tmp_path / "unadmitted"

    invalid = subprocess.run([
        sys.executable, str(runner), "--out", str(out), "--launch-sha", "A" * 40,
    ], cwd=root, capture_output=True, text=True, check=False)
    assert invalid.returncode != 0
    assert "full lowercase Git SHA" in invalid.stderr
    assert "missing HMASD admission" not in invalid.stderr
    assert not out.exists()

    configurable = subprocess.run([
        sys.executable, str(runner), "--out", str(out), "--launch-sha", "a" * 40,
        "--seed", "17",
    ], cwd=root, capture_output=True, text=True, check=False)
    assert configurable.returncode != 0
    assert "unrecognized arguments" in configurable.stderr
    assert "missing HMASD admission" not in configurable.stderr
    assert not out.exists()

    refused = subprocess.run([
        sys.executable, str(runner), "--out", str(out), "--launch-sha", "a" * 40,
    ], cwd=root, capture_output=True, text=True, check=False)
    assert refused.returncode != 0
    assert "missing HMASD admission" in refused.stderr
    assert not out.exists()


def test_config_rejects_invalid_fixture_protocol_values():
    production = Config()
    assert production.world_seeds == tuple(range(73180, 73185))
    assert production.model_seeds == tuple(range(973180, 973185))
    assert (production.phase, production.worlds_per_block, production.horizon,
        production.batch, production.particles) == (30, 256, 96, 16, 32)
    with pytest.raises(ValueError, match="equally sized"):
        tiny_config(model_seeds=(10017,))
    with pytest.raises(ValueError, match="unique"):
        tiny_config(world_seeds=(17, 17))
    with pytest.raises(ValueError, match="multiple of 48"):
        tiny_config(horizon=47)
    with pytest.raises(ValueError, match="particles"):
        tiny_config(particles=1)
    with pytest.raises(ValueError, match="at least two paired worlds"):
        tiny_config(world_seeds=(17,), model_seeds=(10017,), worlds_per_block=1)


def test_output_guard_rejects_non_native_preexisting_content(tmp_path):
    out = tmp_path / "occupied"
    out.mkdir()
    (out / "summary.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="summary.json"):
        run_confirmation(out, "c" * 40, tiny_config())
