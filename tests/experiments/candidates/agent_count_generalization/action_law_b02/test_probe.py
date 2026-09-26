"""Focused B02 engineering checks; all generated data is pytest-owned scratch."""
from dataclasses import replace
import copy
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization import runner
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC as B01_SPEC, make_config
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.action_law_b02 import probe


def _tiny_b01_source(tmp_path: Path, arm: str, seed: int, tag: str):
    fit_spec = replace(
        B01_SPEC,
        horizon=12,
        train_lanes=2,
        eval_lanes=2,
        rollouts=0,
        panels=(),
        hidden_size=16,
        n_heads=2,
        n_layers=1,
        ppo_epochs=1,
        sequence_batch_size=8,
        coordinator_batch_size=8,
        torch_threads=1,
    )
    checkpoint_root = tmp_path / "external"
    tracked_summary_root = tmp_path / "tracked"
    fit_root = checkpoint_root / tag
    fit_root.mkdir(parents=True)
    envs = make_envs(2, seed, 6, 12)
    try:
        config = make_config(arm, envs, seed, fit_spec)
        agent = build_agent(config, str(fit_root / "logs"))
        checkpoint = runner.save_checkpoint(
            agent, fit_root, 45, config, probe.B01_LAUNCH_SHA
        )
    finally:
        for env in envs:
            env.close()
    panels = []
    for n in (4, 6, 8):
        panel_envs = make_envs(2, 982000 + 100 * n, n, 12)
        try:
            panel_config = make_config(arm, panel_envs, seed, fit_spec)
            panels.append({"after_rollout": 45, "test_n": n, "status": "complete",
                           "config": runner.config_dict(panel_config)})
        finally:
            for env in panel_envs:
                env.close()
    summary = {
        "schema": 1,
        "direction": "agent_count_generalization",
        "arm": arm,
        "seed": seed,
        "launch_sha": probe.B01_LAUNCH_SHA,
        "status": "complete",
        "fit_started": True,
        "spec": vars(fit_spec),
        "panels": panels,
        "checkpoints": [checkpoint],
    }
    tracked_fit_root = tracked_summary_root / tag
    tracked_fit_root.mkdir(parents=True)
    runner.write_json(tracked_fit_root / "summary.json", summary)
    # An external summary exists only to reproduce coherent external tampering;
    # the evaluator must never use it as its identity authority.
    runner.write_json(fit_root / "summary.json", summary)
    source = probe.SourcePolicy(arm, seed, tag)
    return (
        probe.load_source_policy(
            checkpoint_root, source, tracked_summary_root=tracked_summary_root
        ),
        fit_spec,
        checkpoint_root,
        tracked_summary_root,
    )


def test_mapping_is_owned_copy_within_range_identity_and_no_rng_draw():
    actions = np.asarray([[[0.25, -1.0, 1.5]]], dtype=np.float32)
    before = actions.copy()
    low = np.full((1, 3), -1.0, dtype=np.float32)
    high = np.full((1, 3), 1.0, dtype=np.float32)
    rng = probe._rng_digest()
    raw = probe.map_actions(actions, low, high, "raw")
    clipped = probe.map_actions(actions, low, high, "clip")
    assert probe._rng_digest() == rng
    np.testing.assert_array_equal(actions, before)
    assert raw is not actions and clipped is not actions
    np.testing.assert_array_equal(raw, actions)
    np.testing.assert_array_equal(clipped, [[[0.25, -1.0, 1.0]]])
    np.testing.assert_array_equal(clipped[..., :2], actions[..., :2])


def test_native_movement_prediction_covers_interior_and_wall_absorption():
    env = make_envs(1, 41, 4, 2)[0]
    try:
        env.reset()
        native = env.env.env
        assert native.uav_positions.dtype == np.float64
        native.uav_positions[:] = np.asarray(
            [[500.0, 500.0, 100.0], [400.0, 400.0, 100.0],
             [300.0, 300.0, 100.0], [200.0, 200.0, 100.0]]
        )
        action = np.zeros((4, 3), dtype=np.float32)
        action[0, 0] = 2.0
        before = native.uav_positions.copy()
        unbounded, predicted = probe._movement_prediction(native, before, action)
        env.step(action)
        np.testing.assert_array_equal(native.uav_positions, predicted)
        assert native.uav_positions[0, 0] - before[0, 0] == 60.0
        np.testing.assert_array_equal(unbounded, predicted)

        env.reset()
        native.uav_positions[0] = [native.area_size, 500.0, 100.0]
        before = native.uav_positions.copy()
        unbounded, predicted = probe._movement_prediction(native, before, action)
        env.step(action)
        assert unbounded[0, 0] == native.area_size + 60.0
        assert predicted[0, 0] == native.area_size
        assert native.uav_positions[0, 0] == before[0, 0]
    finally:
        env.close()


@pytest.mark.parametrize(
    ("arm", "seed", "tag"),
    [("H6", 914201, "s1_count_b01_h6_s914201"),
     ("SET", 915201, "s1_count_b01_set_s915201")],
)
def test_strict_frozen_restoration_and_both_maps_at_all_actual_counts(
    tmp_path, arm, seed, tag
):
    record, _fit_spec, _checkpoint_root, _tracked_root = _tiny_b01_source(
        tmp_path / "inputs", arm, seed, tag
    )
    spec = probe.ProbeSpec(horizon=12, eval_lanes=2, panel_seed_base=982000, torch_threads=1)
    out = tmp_path / "outputs"
    out.mkdir()
    for n in (4, 6, 8):
        rows, traces = {}, {}
        for execution_map in probe.MAPS:
            rows[execution_map], traces[execution_map] = probe.evaluate_map(
                record, n, execution_map, out, spec
            )
            row = rows[execution_map]
            assert row["status"] == "complete"
            assert row["steps"] == 24 and row["episodes"] == 2
            assert row["config"]["k"] == 10 and row["config"]["rollout_length"] == 12
            assert not any(row["optimizer_calls"].values())
            assert row["frozen_weights_and_normalizers"]
            assert row["native_position_dtype"] == "float64"
            assert row["policy_outputs_unchanged_by_mapping"]
            assert row["action_logprobs_unchanged_by_mapping"]
            assert row["diagnostics_consumed_no_global_rng"]
            expected = (
                .7 * np.asarray(row["component_means"]["coverage_reward"])
                + .3 * np.asarray(row["component_means"]["quality_reward"])
                - np.asarray(row["component_means"]["energy_penalty"])
            )
            np.testing.assert_allclose(row["J"], expected, rtol=1e-6, atol=1e-7)
            trace_path = out / row["trace"]["path"]
            assert probe.file_sha256(trace_path) == row["trace"]["sha256"]
            assert row["trace"]["arrays"]["pre_map_actions"]["shape"][0] == 12
            assert row["trace"]["index_semantics"]["base"] == "zero-based"
        pair = probe.compare_maps(rows["raw"], rows["clip"], traces["raw"], traces["clip"])
        assert pair["identical_starts"]["encoded_state"]["exact_identity"]
        assert pair["identical_starts"]["native_position"]["exact_identity"]
        assert len(pair["worlds"]) == 2
        assert pair["trace_index_semantics"]["base"] == "zero-based"


def test_checkpoint_byte_module_and_normalizer_mismatches_fail_closed(tmp_path):
    tag = "s1_count_b01_h6_s914201"
    record, fit_spec, checkpoint_root, tracked_root = _tiny_b01_source(
        tmp_path / "inputs", "H6", 914201, tag
    )

    summary_path = tracked_root / tag / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["checkpoints"][0]["bytes"] += 1
    runner.write_json(summary_path, summary)
    with pytest.raises(ValueError, match="byte-size mismatch"):
        probe.load_source_policy(
            checkpoint_root, probe.SourcePolicy("H6", 914201, tag),
            tracked_summary_root=tracked_root,
        )

    summary["checkpoints"][0] = record["checkpoint_record"]
    runner.write_json(summary_path, summary)
    envs = make_envs(2, 7, 4, 12)
    try:
        config = make_config("H6", envs, 914201, fit_spec)
        target = build_agent(config, str(tmp_path / "target_logs"))
        missing_module = dict(record["payload"])
        missing_module["modules"] = dict(missing_module["modules"])
        missing_module["modules"].pop(next(iter(missing_module["modules"])))
        with pytest.raises(ValueError, match="module set mismatch"):
            probe.restore_checkpoint(target, missing_module)

        bad_normalizer = dict(record["payload"])
        bad_normalizer["normalizers"] = dict(bad_normalizer["normalizers"])
        normalizer = dict(bad_normalizer["normalizers"]["value_norm_discoverer"])
        normalizer["mean"] = [0.0, 1.0]
        bad_normalizer["normalizers"]["value_norm_discoverer"] = normalizer
        with pytest.raises(ValueError, match="shape mismatch"):
            probe.restore_checkpoint(target, bad_normalizer)
    finally:
        for env in envs:
            env.close()


def test_external_summary_and_checkpoint_cannot_rebind_tracked_identity(tmp_path):
    tag = "s1_count_b01_set_s915201"
    record, _fit_spec, checkpoint_root, tracked_root = _tiny_b01_source(
        tmp_path / "inputs", "SET", 915201, tag
    )
    checkpoint = record["checkpoint"]
    checkpoint.write_bytes(checkpoint.read_bytes() + b"tamper")
    external_summary_path = checkpoint_root / tag / "summary.json"
    external = json.loads(external_summary_path.read_text())
    external["checkpoints"][0]["bytes"] = checkpoint.stat().st_size
    external["checkpoints"][0]["sha256"] = probe.file_sha256(checkpoint)
    runner.write_json(external_summary_path, external)

    with pytest.raises(ValueError, match="byte-size mismatch"):
        probe.load_source_policy(
            checkpoint_root, probe.SourcePolicy("SET", 915201, tag),
            tracked_summary_root=tracked_root,
        )


def test_pair_reports_wall_absorption_and_all_native_components():
    pre = np.full((2, 1, 1, 3), 2.0, dtype=np.float32)
    raw_executed = pre.copy()
    clip_executed = np.ones_like(pre)
    positions = np.full((3, 1, 1, 3), 1000.0, dtype=np.float64)
    states = np.zeros((3, 1, 133), dtype=np.float32)
    logprobs = np.zeros((2, 1, 1), dtype=np.float32)
    raw_trace = {
        "pre_map_actions": pre,
        "executed_actions": raw_executed,
        "native_positions": positions,
        "encoded_states": states,
        "action_logprobs": logprobs,
    }
    clip_trace = {**raw_trace, "executed_actions": clip_executed}
    components = {name: [0.5] for name in runner.COMPONENTS}
    base = {"arm": "H6", "seed": 1, "test_n": 4, "world_seeds": [982400],
            "initial_observations_sha256": "same", "model_digest": "same",
            "runtime_seed": 982451, "normalizers": {"value": "same"},
            "J": [0.5], "component_means": components}
    pair = probe.compare_maps(base, {**base, "J": [0.6]}, raw_trace, clip_trace)
    world = pair["worlds"][0]
    assert world["same_start_mapping_changed_steps"]["numerator"] == 2
    assert world["same_start_mapping_changed_same_exact_successor_steps"]["numerator"] == 2
    assert set(world["components"]) == set(runner.COMPONENTS)
    assert not pair["inactive_mapping_all_worlds"]
    assert pair["exact_same_position_trajectory"]
    assert world["first_divergence_step"]["executed_action"]["trace_index_zero_based"] == 0
    assert world["first_divergence_step"]["executed_action"]["index_kind"] == "action_t"
    assert world["first_divergence_step"]["native_position"]["trace_index_zero_based"] is None
    assert pair["trajectory_comparison"]["executed_actions"]["index_base"] == "zero-based"


def _synthetic_identical_pair_inputs():
    trace = {
        "pre_map_actions": np.zeros((2, 1, 1, 3), dtype=np.float32),
        "executed_actions": np.zeros((2, 1, 1, 3), dtype=np.float32),
        "native_positions": np.zeros((3, 1, 1, 3), dtype=np.float64),
        "encoded_states": np.zeros((3, 1, 133), dtype=np.float32),
        "action_logprobs": np.zeros((2, 1, 1), dtype=np.float32),
    }
    components = {name: [0.5] for name in runner.COMPONENTS}
    row = {
        "arm": "H6", "seed": 1, "test_n": 4, "world_seeds": [982400],
        "initial_observations_sha256": "observations", "model_digest": "model",
        "runtime_seed": 982451,
        "normalizers": {"value_norm_discoverer": {"dtype": "float64", "value": 1.0}},
        "J": [0.5], "component_means": components,
    }
    return row, copy.deepcopy(row), trace, {key: value.copy() for key, value in trace.items()}


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("model_digest", "other-model", "models/normalizers"),
        ("normalizers", {"value_norm_discoverer": {"dtype": "float32", "value": 1.0}},
         "normalizer values/types"),
        ("initial_observations_sha256", "other-observations", "identical observations"),
        ("runtime_seed", 982452, "runtime seeds"),
    ],
)
def test_pair_rejects_mismatched_runtime_identity(field, replacement, message):
    raw, clip, raw_trace, clip_trace = _synthetic_identical_pair_inputs()
    clip[field] = replacement
    with pytest.raises(ValueError, match=message):
        probe.compare_maps(raw, clip, raw_trace, clip_trace)


@pytest.mark.parametrize("trace_field", ["native_positions", "encoded_states"])
def test_pair_rejects_mismatched_actual_start(trace_field):
    raw, clip, raw_trace, clip_trace = _synthetic_identical_pair_inputs()
    clip_trace[trace_field][0].flat[0] = 1
    with pytest.raises(ValueError, match="identical actual states"):
        probe.compare_maps(raw, clip, raw_trace, clip_trace)


def test_reduce_complete_36_cells_reports_absolute_changes_and_gap_k():
    raw_values = {
        "H6": {4: .60, 6: .55, 8: .50},
        "SET": {4: .50, 6: .45, 8: .40},
    }
    map_change = {"H6": -.02, "SET": .03}
    cells, pairs = [], []
    for arm, seed, _tag in probe.SOURCE_POLICIES:
        for n in probe.DEFAULT_SPEC.test_ns:
            raw = raw_values[arm][n]
            clipped = raw + map_change[arm]
            for execution_map, value in (("raw", raw), ("clip", clipped)):
                cells.append({
                    "status": "complete", "arm": arm, "seed": seed, "test_n": n,
                    "execution_map": execution_map, "J": [value, value],
                })
            pairs.append({"arm": arm, "seed": seed, "test_n": n,
                          "d_mean": map_change[arm]})
    assert len(cells) == 36 and len(pairs) == 18
    reduced = probe.reduce_results(cells, pairs)
    for n in (4, 6, 8):
        row = reduced["by_n"][str(n)]
        assert row["raw"]["H6_minus_SET"] == pytest.approx(.10)
        assert row["clip"]["H6_minus_SET"] == pytest.approx(.05)
        assert row["arm_clip_minus_raw"]["H6"] == pytest.approx(-.02)
        assert row["arm_clip_minus_raw"]["SET"] == pytest.approx(.03)
        assert row["K_gap_clip_minus_gap_raw"] == pytest.approx(-.05)
    assert reduced["unseen_equal_weight_arm_clip_minus_raw"] == pytest.approx(
        {"H6": -.02, "SET": .03}
    )
    assert reduced["unseen_K_gap_clip_minus_gap_raw"] == pytest.approx(-.05)


def test_failed_cell_is_preserved_and_not_silently_complete(tmp_path, monkeypatch):
    fake_checkpoint = tmp_path / "checkpoint.pt"
    fake_checkpoint.write_bytes(b"fixed")

    def fake_load(_root, source):
        return {"source": source, "checkpoint": fake_checkpoint,
                "summary_path": tmp_path / source.tag / "summary.json",
                "summary_identity": {"sha256": "fixture", "bytes": 0},
                "checkpoint_record": {"bytes": len(b"fixed"), "sha256": probe.file_sha256(fake_checkpoint)},
                "checkpoint_sha256_before": probe.file_sha256(fake_checkpoint)}

    def fake_evaluate(record, n, execution_map, out, spec, step_progress=None):
        if execution_map == "clip":
            step_progress(1, 0)
            raise RuntimeError("injected map failure")
        source = record["source"]
        step_progress(spec.horizon * spec.eval_lanes, spec.eval_lanes)
        result = {
            "status": "complete", "arm": source.arm, "seed": source.seed,
            "source_tag": source.tag, "test_n": n, "execution_map": execution_map,
            "world_seeds": list(range(spec.panel_seed_base + 100 * n,
                                      spec.panel_seed_base + 100 * n + spec.eval_lanes)),
            "steps": spec.horizon * spec.eval_lanes, "episodes": spec.eval_lanes,
            "J": [0.0] * spec.eval_lanes,
            "component_means": {name: [0.0] * spec.eval_lanes for name in runner.COMPONENTS},
            "optimizer_calls": {},
        }
        trace = {
            "pre_map_actions": np.zeros((1, 1, 1, 3), dtype=np.float32),
            "executed_actions": np.zeros((1, 1, 1, 3), dtype=np.float32),
            "native_positions": np.zeros((2, 1, 1, 3), dtype=np.float64),
            "encoded_states": np.zeros((2, 1, 133), dtype=np.float32),
            "action_logprobs": np.zeros((1, 1, 1), dtype=np.float32),
        }
        return result, trace

    monkeypatch.setattr(probe, "load_source_policy", fake_load)
    monkeypatch.setattr(probe, "evaluate_map", fake_evaluate)
    out = tmp_path / "failed"
    assert probe.run_probe(out, tmp_path, "sha", {"sha": "sha"}) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "failed" and "injected map failure" in summary["failure"]
    assert summary["cells"][0]["status"] == "complete"
    assert summary["cells"][1]["status"] == "failed"
    assert summary["cells"][1]["steps"] == 1
    assert summary["cells"][1]["episodes"] == 0
    assert summary["counts"]["evaluation_team_steps"] == 500 * 16 + 1
    assert summary["counts"]["evaluation_episodes"] == 16
    assert (out / "cell_h6_914201_n4_raw.json").exists()
    assert (out / "cell_h6_914201_n4_clip.json").exists()


def test_entry_checks_admission_before_candidate_run_or_output(tmp_path, monkeypatch):
    from scripts import run_agent_count_action_law_probe_b02 as entry

    calls = []

    def refuse(*_args, **_kwargs):
        calls.append("admission")
        raise RuntimeError("not admitted")

    monkeypatch.setattr(entry, "require_admission", refuse)
    out = tmp_path / "never-created"
    with pytest.raises(RuntimeError, match="not admitted"):
        entry.main([
            "--out", str(out), "--launch-sha", "sha",
            "--checkpoint-root", str(tmp_path / "inputs"),
        ], run_fn=lambda *_args, **_kwargs: calls.append("scientific"))
    assert calls == ["admission"]
    assert not out.exists()
