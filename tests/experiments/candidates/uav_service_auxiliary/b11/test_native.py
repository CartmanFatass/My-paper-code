import copy
import gzip
import json
import os
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.uav_service_auxiliary.b11 import native
from experiments.candidates.uav_service_auxiliary.b11.metrics import suffix_reading
from scripts import run_uav_service_auxiliary_b11 as entry

SOURCE = Path(os.environ.get("HMASD_B11_SOURCE_ROOT",
    "/home/fires/hmasd-artifacts/uav_service_auxiliary/b09_an_925031_a01"))


def test_fixed_binding_and_admission_before_effects(tmp_path, monkeypatch):
    config, evaluation, summary = native.verify_source(SOURCE)
    assert config.num_envs == 2 and evaluation.num_envs == 1
    assert summary["launch_sha"] == native.SOURCE_SHA
    assert native.RULES == ("O", "G")
    assert native.WORLD_SEEDS == tuple(range(954001, 954033))
    assert native.POLICY_SEED == 925031
    from scripts import hmasd_admission
    target = tmp_path / "not-created"
    def reject(*args, **kwargs):
        raise RuntimeError("admission rejected")
    monkeypatch.setattr(hmasd_admission, "require_admission", reject)
    with pytest.raises(RuntimeError, match="admission rejected"):
        entry.main(["--source-root", str(SOURCE), "--out", str(target), "--launch-sha", "fixture"])
    assert not target.exists()


def _snap(rule, selected, margin=-.1):
    return {"rule": rule, "prior_actual_station": [0, -1], "current_target_station": [0, 0],
            "battery_after_consumption": [.3, .2], "raw_margin_before_input": [.1, margin],
            "wait_age_before_selection": [0, 1], "eligible_by_station": {"0": [0, 1]},
            "original_selected": {"0": [1]}, "continuous_selected": {"0": [0]},
            "guard_trigger": {"0": margin < 0}, "actual_selected": {"0": selected}}


def test_prefix_first_actual_difference_and_no_difference(tmp_path):
    fields = ("native_reward", "metrics", "ends", "actions", "physical_post_battery",
              "charger_input_wh", "mode", "entry", "exit", "pre_position_m", "post_position_m",
              "original_action", "submitted_action", "mode_before", "pre_legal_battery",
              "agent_skills", "team_skills", "station_raw_margin_selection")
    arrays = {field: np.zeros((2, 2), dtype=float) for field in fields}
    left, right = tmp_path / "o.npz", tmp_path / "g.npz"
    np.savez_compressed(left, **arrays)
    np.savez_compressed(right, **arrays)
    o = [_snap("O", [1]), _snap("O", [1])]
    g = [_snap("G", [1]), _snap("G", [0], margin=.1)]
    g[1]["guard_trigger"] = {"0": False}
    o[1]["raw_margin_before_input"] = [.1, .1]
    o[1]["guard_trigger"] = {"0": False}
    assert native.verify_prefix(left, right, o, g)["first_differing_allocation_tick"] == 1
    g[1]["actual_selected"] = {"0": [1]}
    assert native.verify_prefix(left, right, o, g)["first_differing_allocation_tick"] is None
    g[0]["raw_margin_before_input"] = [0., -.1]
    with pytest.raises(RuntimeError, match="prefix"):
        native.verify_prefix(left, right, o, g)


def test_suffix_uses_original_interval_starts_and_early_end():
    from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS
    metrics = np.zeros((2, len(TRACE_FIELDS)))
    metrics[:, TRACE_FIELDS.index("qos_satisfaction_ratio")] = [1, 2]
    metrics[:, TRACE_FIELDS.index("return_constraint_cost")] = [.2, .3]
    trace = {"native_reward": np.asarray([3., 4.]), "metrics": metrics,
             "charging_wait_age": np.asarray([[1], [2]]), "charging_eligible": np.asarray([[1], [1]]),
             "charger_input_wh": np.zeros((2, 1)), "station_raw_margin_selection": np.asarray([[-.2], [-.1]])}
    detail = {"station": {"waiting_intervals": [{"start": 0, "stop": 2}],
                          "negative_wait_intervals": [{"start": 0, "stop": 2}]},
              "recovery_opportunity": {"intervals": [{"start_step": 0, "exit_step": 1,
                                                         "qualifying_positive_gain_exit": True}],
                                       "first_qualifying_exit_anchor": {"anchor_step": 0}},
              "service_free_intervals": [{"start": 0, "stop": 2}]}
    row = suffix_reading(trace, detail, 1, time_step_seconds=1.)
    assert row["actual_steps"] == 1 and row["native_J"] == 4
    assert row["native_return_cost"] == .3
    assert row["wait_intervals_crossing_boundary"] == 1
    assert row["recovery_intervals_crossing_boundary"] == 1
    assert row["first_recovery_precedes_allocation_difference"]
    empty = suffix_reading(trace, detail, 2, time_step_seconds=1.)
    assert empty["actual_steps"] == 0 and empty["native_J"] == 0
    assert empty["recovery_intervals_intersecting"] == 0
    assert empty["service_free_intervals_intersecting"] == 0
    detail["recovery_opportunity"]["intervals"][0]["exit_step"] = None
    empty = suffix_reading(trace, detail, 2, time_step_seconds=1.)
    assert empty["recovery_intervals_intersecting"] == 0


def test_physical_cutoff_depletion_events_are_separate_from_censoring():
    from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS
    world = {"terminal_type": "terminated", "actual_length": 3,
             "service_free_intervals": [{"start": 0, "stop": 3, "right_censored": True}],
             "right_censored_service_free_interval": True}
    station = {"waiting_intervals": [{"member": 0, "start": 0, "stop": 3}],
               "negative_wait_intervals": [{"member": 0, "start": 1, "stop": 3}],
               "wait_interval_end_counts": {}, "charging_spell_end_counts": {}}
    opportunity = {"intervals": [{"member": 0, "start_step": 0, "exit_step": None,
                                   "right_censored": True}],
                   "denominators": {"right_censored_intervals": 1}}
    post = np.asarray([[.1, .2], [.019, .1], [0., .1]])
    diagnostics = {"physical_post_battery": post,
                   "charger_input_wh": np.zeros_like(post)}
    metrics = np.zeros((3, len(TRACE_FIELDS)))
    metrics[1, TRACE_FIELDS.index("cutoff_event_count")] = 1
    metrics[2, TRACE_FIELDS.index("depletion_event_count")] = 1
    native._mark_terminal_events(world, station, opportunity, diagnostics, metrics,
                                 cutoff_threshold=.02)
    assert world["safety_events"]["cutoff_event_first_step_by_member"] == [1, None]
    assert world["safety_events"]["depletion_event_first_step_by_member"] == [2, None]
    assert station["waiting_intervals"][0]["cutoff_events_during_wait"] == 1
    assert station["negative_wait_intervals"][0]["depletion_events_during_wait"] == 1
    assert opportunity["intervals"][0]["end_reason"] == "episode_terminated"
    assert opportunity["denominators"]["right_censored_intervals"] == 0
    assert not world["right_censored_service_free_interval"]
    metrics[1, TRACE_FIELDS.index("cutoff_event_count")] = 0
    with pytest.raises(RuntimeError, match="native cutoff_event_count"):
        native._mark_terminal_events(world, station, opportunity, diagnostics, metrics,
                                     cutoff_threshold=.02)


def test_paired_cost_wins_use_lower_direction():
    original = {field: 0.0 for field in native.ENDPOINT_FIELDS}
    original.update(seed=7, zero_service_episode=False, maximum_service_free_interval_steps=2,
                    return_constraint_cost_sum=2.0)
    guard = dict(original)
    guard["return_constraint_cost_sum"] = 1.0
    guard["raw_native_J"] = 1.0
    paired = native.paired_summary([original], [guard])
    assert paired["aggregate"]["return_constraint_cost_sum"]["wins"] == 1
    assert paired["aggregate"]["raw_native_J"]["wins"] == 1
    assert paired["worlds"][0]["effects_G_minus_O"]["return_constraint_cost_sum"] == -1


@pytest.mark.parametrize("device_name", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(
    not torch.cuda.is_available(), reason="CUDA unavailable"))])
def test_tiny_native_closed_loop_writes_complete_and_hashed_raw(tmp_path, device_name):
    _, evaluation, _ = native.verify_source(SOURCE)
    tiny = copy.deepcopy(evaluation)
    tiny.episode_length = tiny.max_steps = 3
    tiny.calculate_and_set_buffer_sizes()
    out = tmp_path / "b11-fixture"
    out.mkdir()
    (out / "launch-manifest.json").write_text("{}")
    result = native.run_native(source_root=SOURCE, out=out, launch_sha="fixture",
                               device_name=device_name, threads=4,
                               _fixture_seeds=(7,), _fixture_config=tiny)
    assert result["status"] == "COMPLETE"
    assert result["counts"]["fits"] == result["counts"]["training_transitions"] == result["counts"]["optimizer_updates"] == 0
    assert result["counts"]["episode_attempts"] == result["counts"]["completed_episodes"] == 2
    assert result["counts"]["evaluation_transitions"] <= 6
    assert result["counts"]["uav_action_rows"] == 8 * result["counts"]["evaluation_transitions"]
    assert len(result["prefixes"]) == len(result["suffixes"]) == 1
    if result["prefixes"][0]["first_differing_allocation_tick"] is None:
        suffix = result["suffixes"][0]
        assert suffix["first_differing_allocation_tick"] is None
        assert suffix["suffix_start"] == result["panels"]["O"]["worlds"][0]["actual_length"]
        assert suffix["O"]["actual_steps"] == suffix["G"]["actual_steps"] == 0
        assert suffix["O"]["recovery_intervals_intersecting"] == 0
        assert suffix["O"]["first_recovery_precedes_allocation_difference"] is None
    assert result["panels"]["O"]["learner_state_immutable"]
    assert result["panels"]["G"]["learner_state_immutable"]
    assert result["torch_threads"] == 4 and result["tf32_disabled"]
    for rule in ("O", "G"):
        world = result["panels"][rule]["worlds"][0]
        assert world["station"]["guard_counts"]["station_ticks"] > 0
        for name in (world["raw_npz"], world["raw_detail"]):
            assert native.sha256_file(out / name) == world["raw_sha256"][name]
        with np.load(out / world["raw_npz"], allow_pickle=False) as trace:
            assert trace["station_raw_margin_selection"].shape == (world["actual_length"], 8)
            assert len(trace["native_reward"]) == len(trace["charger_input_wh"])
        with gzip.open(out / world["raw_detail"], "rt") as handle:
            detail = json.load(handle)
            assert len(detail["station_selection_snapshots"]) == world["actual_length"]
            assert "negative_wait_intervals" in detail["station"]
    assert json.loads((out / "summary.json").read_text())["status"] == "COMPLETE"
    assert json.loads((out / "config.json").read_text())["world_seeds"] == [7]
