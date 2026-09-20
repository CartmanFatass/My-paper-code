import json

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.gaussian_scale_initialization_b06 import study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def run_fixture(tmp_path, admission, *, factory=None):
    out = tmp_path / "result"
    result = study.run(
        study.Config.engineering(), out, admission, factory=factory
    )
    return result, out


def test_complete_fixture_uses_ordinary_route_and_publishes_reconstructable_endpoints(
    tmp_path, admission
):
    result, out = run_fixture(tmp_path, admission)
    assert result["status"] == "COMPLETE"
    assert result["object"] == study.OBJECT
    assert result["launch_sha"] == admission["sha"]
    assert result["fit_accounting"]["started_fits"] == 2
    assert result["fit_accounting"]["completed_fits"] == 2
    assert result["fit_accounting"]["allocated_fits_complete_batch"] == 6
    assert "execution_authorized" not in result["fit_accounting"]
    assert "separate owner amendment" in (
        result["prepared_execution_exposure"]["preparation_boundary"]
    )
    counts = result["counts"]
    assert counts["train_episodes"] == 8
    assert counts["train_team_steps"] == 64
    assert counts["optimizer_steps"] == 16
    assert counts["final_deployment_eval_episodes"] == 12
    assert counts["final_deployment_eval_team_steps"] == 96
    assert counts["evaluation_optimizer_steps"] == 0
    assert counts["all_team_steps"] == 160

    for arm in study.ARMS:
        record = result["arms"][arm]
        assert record["train_complete"]
        assert record["checkpoint"]["present"] and record["checkpoint"]["sha256"]
        assert record["movement"]["common_actor"]["displacement"] > 0
        assert record["movement"]["critic"]["displacement"] > 0
        assert record["final_log_std"] != record["initial_log_std"]
        early = record["first_256_episode_start_scale"]
        assert early["target_episode_starts"] == 256
        assert early["observed_episode_starts"] == 4
        assert not early["complete"]
        assert len(early["values"]) == 4
        immutable = record["evaluation_immutability"]
        assert immutable["optimizer_steps"] == 0
        assert immutable["parameter_exposure"]["total"]["displacement"] == 0
        assert immutable["training_generators_unchanged"]
        assert record["duration_rng_unchanged"]

    assert result["rng_isolation"]["global_torch_rng_unchanged"]
    assert result["rng_isolation"]["training_velocity_final_states_equal"]
    assert result["rng_isolation"]["training_duration_final_states_equal"]
    assert result["paired_initial_rng"] == {
        "velocity_equal": True,
        "duration_equal": True,
        "objects_independent": True,
    }

    arrays = np.load(out / "evaluation_primitives.npz", allow_pickle=False)
    assert arrays["mode_names"].tolist() == list(study.MODES)
    assert arrays["completed"].all()
    assert arrays["velocity_mask"].all()
    assert not arrays["duration_mask"].any()
    assert not arrays["phase"].any()
    np.testing.assert_allclose(
        arrays["actions"], np.tanh(arrays["latent_u"]), rtol=2e-7, atol=2e-7
    )
    reconstructed = arrays["rewards"].sum(axis=2) / study.Config.engineering().horizon
    for mode_index, mode in enumerate(study.MODES):
        np.testing.assert_allclose(
            reconstructed[:, mode_index], result["panel"]["returns"][mode],
            rtol=1e-6, atol=1e-7,
        )
    for name, first, second in study.CONTRASTS:
        vector = reconstructed[:, study.MODES.index(first)] - reconstructed[:, study.MODES.index(second)]
        np.testing.assert_allclose(
            vector, result["panel"][name]["differences"], rtol=1e-6, atol=1e-7
        )
        assert result["panel"][name]["signs"] == np.sign(vector).astype(int).tolist()
        assert result["panel"][name]["conditional_se"] is not None
        assert result["panel"][name]["complete"]
    assert result["panel"]["primary"] == result["panel"]["Ghalf_mean_minus_G1_mean"]
    assert result["panel"]["complete"]

    eval_rows = [json.loads(line) for line in (out / "eval_episodes.jsonl").read_text().splitlines()]
    assert len(eval_rows) == 12
    assert all(not row["duration_rng_changed"] for row in eval_rows)
    assert all(
        row["velocity_rng_changed"] == row["mode"].endswith("sampled")
        for row in eval_rows
    )
    assert len((out / "train_episodes.jsonl").read_text().splitlines()) == 8
    update_rows = [json.loads(line) for line in (out / "updates.jsonl").read_text().splitlines()]
    assert len(update_rows) == 4
    assert all(len(row["epochs"]) == 4 for row in update_rows)
    assert all("entropy" in epoch for row in update_rows for epoch in row["epochs"])
    scale_rows = [json.loads(line) for line in (out / "scales.jsonl").read_text().splitlines()]
    assert len(scale_rows) == 8
    assert {row["when"] for row in scale_rows} == {"before_collection", "after_update"}

    for arm in study.ARMS:
        payload = torch.load(out / f"{arm}_final.pt", map_location="cpu", weights_only=True)
        assert payload["object"] == study.OBJECT
        assert payload["arm"] == arm and payload["seed"] == 9941
        assert payload["train_episodes"] == 4 and payload["optimizer_steps"] == 8
    assert json.loads((out / "config.json").read_text())["fixture"] is True
    assert json.loads((out / "admission.json").read_text()) == admission
    assert json.loads((out / "summary.json").read_text())["status"] == "COMPLETE"
    assert all(result["artifacts"][name]["present"] for name in (
        "source.json", "train_episodes.jsonl", "eval_episodes.jsonl",
        "updates.jsonl", "scales.jsonl", "evaluation_primitives.npz",
        "G1_final.pt", "Ghalf_final.pt",
    ))


def test_initial_scale_prediction_is_measured_at_episode_start(tmp_path, admission):
    result, _out = run_fixture(tmp_path, admission)
    g1 = result["arms"]["G1"]["first_256_episode_start_scale"]
    half = result["arms"]["Ghalf"]["first_256_episode_start_scale"]
    assert g1["values"][:2] == [1.0, 1.0]
    assert half["values"][:2] == [0.5, 0.5]
    assert g1["mean"] > half["mean"]
    assert "first 256 training episodes" in g1["definition"]


def test_early_scale_window_completes_only_at_256_actual_episode_starts():
    values = [float(index) for index in range(257)]
    before = study._early_scale_summary(values[:255])
    boundary = study._early_scale_summary(values[:256])
    after = study._early_scale_summary(values)
    assert before["observed_episode_starts"] == 255 and not before["complete"]
    assert boundary["observed_episode_starts"] == 256 and boundary["complete"]
    assert after["observed_episode_starts"] == 256 and after["complete"]
    assert after["values"] == boundary["values"]


def test_second_fit_failure_retains_first_checkpoint_and_partial_counters(tmp_path, admission):
    class FailSecondEnvironment(SyntheticAdapter):
        instances = 0

        def __init__(self, seed, horizon):
            super().__init__(seed, horizon)
            type(self).instances += 1
            self.number = type(self).instances

        def step(self, actions):
            if self.number == 2:
                raise RuntimeError("fixture Ghalf failed")
            return super().step(actions)

    result, out = run_fixture(
        tmp_path,
        admission,
        factory=lambda seed: FailSecondEnvironment(seed, 8),
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"] == {"type": "RuntimeError", "message": "fixture Ghalf failed"}
    assert result["fit_accounting"]["started_fits"] == 2
    assert result["fit_accounting"]["completed_fits"] == 1
    assert result["arms"]["G1"]["train_complete"]
    assert not result["arms"]["Ghalf"]["train_complete"]
    assert result["arms"]["G1"]["first_256_episode_start_scale"]["observed_episode_starts"] == 4
    failed_early = result["arms"]["Ghalf"]["first_256_episode_start_scale"]
    assert failed_early["observed_episode_starts"] == 1
    assert failed_early["values"] == [0.5]
    assert not failed_early["complete"]
    assert (out / "G1_final.pt").is_file()
    assert not (out / "Ghalf_final.pt").exists()
    assert result["counts"]["train_episodes"] == 4
    assert result["counts"]["optimizer_steps"] == 8
    assert result["panel"]["returns"] == {mode: [] for mode in study.MODES}
    assert not result["panel"]["complete"]
    assert (out / "summary.json").is_file()
    assert (out / "evaluation_primitives.npz").is_file()
    assert len((out / "train_episodes.jsonl").read_text().splitlines()) == 4


def test_later_evaluation_failure_retains_completed_rows_and_partial_event_counts(
    tmp_path, admission
):
    class FailDuringSecondEvaluationMode(SyntheticAdapter):
        instances = 0

        def __init__(self, seed, horizon):
            super().__init__(seed, horizon)
            type(self).instances += 1
            self.number = type(self).instances
            self.steps = 0

        def step(self, actions):
            self.steps += 1
            if self.number == 4 and self.steps == 3:
                raise RuntimeError("fixture later evaluation failed")
            return super().step(actions)

    result, out = run_fixture(
        tmp_path,
        admission,
        factory=lambda seed: FailDuringSecondEvaluationMode(seed, 8),
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"] == {
        "type": "RuntimeError",
        "message": "fixture later evaluation failed",
    }
    assert result["evaluation_counts"]["G1_sampled"]["eval_episodes"] == 1
    assert result["evaluation_counts"]["G1_sampled"]["eval_team_steps"] == 8
    assert result["evaluation_counts"]["Ghalf_sampled"]["eval_episodes"] == 0
    assert result["evaluation_counts"]["Ghalf_sampled"]["step_calls"] == 3
    assert result["evaluation_counts"]["Ghalf_sampled"]["eval_team_steps"] == 2
    assert result["counts"]["final_deployment_eval_episodes"] == 1
    assert result["counts"]["final_deployment_eval_team_steps"] == 10
    rows = [json.loads(line) for line in (out / "eval_episodes.jsonl").read_text().splitlines()]
    assert [row["mode"] for row in rows] == ["G1_sampled"]
    arrays = np.load(out / "evaluation_primitives.npz", allow_pickle=False)
    assert int(arrays["completed"].sum()) == 1


def test_evaluation_close_failure_retains_complete_exposure(tmp_path, admission):
    class FailFirstEvaluationClose(SyntheticAdapter):
        instances = 0

        def __init__(self, seed, horizon):
            super().__init__(seed, horizon)
            type(self).instances += 1
            self.number = type(self).instances

        def close(self):
            if self.number == 3:
                raise RuntimeError("fixture evaluation close failed")

    result, out = run_fixture(
        tmp_path,
        admission,
        factory=lambda seed: FailFirstEvaluationClose(seed, 8),
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"] == {
        "type": "RuntimeError",
        "message": "fixture evaluation close failed",
    }
    assert result["counts"]["final_deployment_eval_episodes"] == 12
    assert result["counts"]["final_deployment_eval_team_steps"] == 96
    assert len((out / "eval_episodes.jsonl").read_text().splitlines()) == 12


def test_production_environment_override_is_refused_before_output(tmp_path, admission):
    out = tmp_path / "unused"
    with pytest.raises(ValueError, match="cannot be overridden"):
        study.run(
            study.Config(master=8941), out, admission,
            factory=lambda _seed: SyntheticAdapter(1, 8),
        )
    assert not out.exists()
