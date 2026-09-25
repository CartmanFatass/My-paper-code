"""B09 binding and admission before candidate effects."""

import pytest
import torch
from dataclasses import replace

from experiments.candidates.uav_service_auxiliary.b09 import native
from experiments.candidates.uav_service_auxiliary.b01.native import make_config
from scripts import run_uav_service_auxiliary_b09 as entry


def test_fixed_binding():
    spec = native.production_spec(925031)
    config = native.make_b09_config(spec)
    record = native.fixed_config_record(spec, config)
    assert spec.transitions == 180000
    assert spec.lanes == 2 and spec.rollout_length == spec.episode_length == 3000
    assert spec.eval_seeds == () and spec.final_seeds == tuple(range(952001, 952033))
    assert record["primary_seeds"] == list(range(952001, 952033))
    assert record["common_initial_evaluation_episodes"] == 32
    assert record["lane_initial_seeds"] == [925031, 925032]
    assert record["arm_order"] == ["N", "A"]
    assert record["training_feedback"] == {"N": False, "A": True}
    assert record["training_return_coefficient"] == 2.0
    assert config.ordinary_completed_segments
    with pytest.raises(ValueError, match="unplanned"):
        native.production_spec(925032)


def test_real_matched_initialization_includes_rng_buffers_and_normalizers(tmp_path):
    spec = replace(native.B09Spec(), lanes=1, rollouts=1, rollout_length=4,
                   episode_length=4, hidden_size=32, gru_hidden_size=32)
    config = make_config(spec)
    config.ordinary_completed_segments = True
    first, left = native.new_initialized_agent(config, device=torch.device("cpu"),
                                               log_dir=tmp_path / "first")
    second, right = native.new_initialized_agent(config, device=torch.device("cpu"),
                                                 log_dir=tmp_path / "second")
    native.assert_common_initialization(left, right)
    assert left["sha256"] == right["sha256"]
    assert left["components"]["rng_state"] == right["components"]["rng_state"]
    assert first.rollout_buffer.get_sampler_rng_state() == second.rollout_buffer.get_sampler_rng_state()


def test_admission_precedes_candidate_import_and_output(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    target = tmp_path / "never-created"
    def refuse(*args, **kwargs):
        raise RuntimeError("no admission")
    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    with pytest.raises(RuntimeError, match="no admission"):
        entry.main(["--launch-sha", "fixture", "--out", str(target)])
    assert not target.exists()
