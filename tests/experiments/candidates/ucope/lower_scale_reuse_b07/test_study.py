import hashlib
import json

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.lower_scale_reuse_b07 import study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def run_fixture(tmp_path, admission, inherited_files, *, factory=None):
    out = tmp_path / "result"
    result = study.run(
        study.Config.engineering(), out, admission,
        factory=factory, fixture_files=inherited_files,
    )
    return result, out


def test_complete_fixture_trains_only_b_and_reconstructs_fixed_panel(
    tmp_path, admission, inherited_files
):
    result, out = run_fixture(tmp_path, admission, inherited_files)
    assert result["status"] == "COMPLETE"
    assert result["fit_accounting"] == {
        "new_fit_arm": "Bhalf",
        "allocated_new_fits_this_invocation": 1,
        "allocated_new_fits_complete_batch": 3,
        "started_new_fits": 1,
        "completed_new_fits": 1,
        "inherited_Ghalf_fits_this_invocation": 1,
        "inherited_fits_are_not_new_starts": True,
        "qualification": result["fit_accounting"]["qualification"],
    }
    counts = result["counts"]
    assert counts["new_train_episodes"] == 4
    assert counts["new_train_team_steps"] == 32
    assert counts["new_optimizer_steps"] == 8
    assert counts["final_eval_episodes"] == 12
    assert counts["final_eval_team_steps"] == 96
    assert counts["final_eval_valid_reward_steps"] == 96
    assert counts["evaluation_optimizer_steps"] == 0
    assert counts["new_team_steps"] == 128
    assert result["inherited_exposure"]["new_Ghalf_fits"] == 0
    b = result["new_Bhalf"]
    assert b["train_complete"] and b["checkpoint"]["present"]
    assert b["movement"]["common_actor"]["displacement"] > 0
    assert b["movement"]["critic"]["displacement"] > 0
    assert b["movement"]["gate"]["displacement"] > 0
    assert b["final_log_std"] != b["initial_log_std"]
    assert b["final_gate_logits"] != b["initial_gate_logits"]
    assert b["first_256_episode_start_scale"]["observed_episode_starts"] == 4
    assert not b["first_256_episode_start_scale"]["complete"]
    assert result["rng_isolation"]["global_torch_rng_unchanged"]

    per_mode = counts["per_mode_evaluation"]
    assert per_mode["Bhalf_sampled"]["gate_uniforms_used"] > 0
    assert per_mode["Bhalf_mean"]["gate_uniforms_used"] > 0
    assert per_mode["Bhalf_sampled"]["gaussian_vectors_used"] > 0
    assert per_mode["Bhalf_mean"]["gaussian_vectors_used"] == 0
    assert per_mode["Ghalf_sampled"]["gaussian_vectors_used"] == 3 * 8 * 5
    assert per_mode["Ghalf_mean"]["gaussian_vectors_used"] == 0
    assert per_mode["Ghalf_sampled"]["gate_uniforms_used"] == 0
    assert per_mode["Ghalf_mean"]["gate_uniforms_used"] == 0
    assert all(
        item["optimizer_steps"] == 0 and item["exactly_unchanged"]
        for item in result["evaluation_immutability"].values()
    )

    arrays = np.load(out / "evaluation_primitives.npz", allow_pickle=False)
    assert arrays["mode_names"].tolist() == list(study.MODES)
    assert arrays["completed"].all()
    bs = study.MODES.index("Bhalf_sampled")
    bm = study.MODES.index("Bhalf_mean")
    gs = study.MODES.index("Ghalf_sampled")
    gm = study.MODES.index("Ghalf_mean")
    np.testing.assert_array_equal(arrays["eligibility"][:, bs], arrays["eligibility"][:, bm])
    np.testing.assert_array_equal(arrays["branches"][:, bs], arrays["branches"][:, bm])
    assert not arrays["eligibility"][:, gs].any()
    assert not arrays["eligibility"][:, gm].any()
    assert (arrays["branches"][:, gs] == study.FORCED_FRESH).all()
    assert (arrays["branches"][:, gm] == study.FORCED_FRESH).all()
    for mode_index in (bs, bm):
        assert (arrays["branches"][:, mode_index][~arrays["eligibility"][:, mode_index]]
                == study.FORCED_FRESH).all()
        assert np.isin(
            arrays["branches"][:, mode_index][arrays["eligibility"][:, mode_index]],
            [study.KEEP, study.END],
        ).all()
    np.testing.assert_array_equal(
        arrays["eligibility"][:, bs, 1:], arrays["fresh"][:, bs, :-1]
    )
    np.testing.assert_array_equal(
        arrays["eligibility"][:, bm, 1:], arrays["fresh"][:, bm, :-1]
    )
    fresh_mean = arrays["fresh"][:, bm]
    np.testing.assert_allclose(
        arrays["commands"][:, bm][fresh_mean],
        np.tanh(arrays["means"][:, bm][fresh_mean]),
        rtol=2e-7, atol=2e-7,
    )
    np.testing.assert_allclose(
        arrays["commands"][:, gm], np.tanh(arrays["means"][:, gm]),
        rtol=2e-7, atol=2e-7,
    )

    reconstructed = arrays["rewards"].sum(axis=2) / 8
    for mode_index, mode in enumerate(study.MODES):
        np.testing.assert_allclose(
            reconstructed[:, mode_index], result["panel"]["returns"][mode],
            rtol=1e-7, atol=1e-8,
        )
    for name, first, second in study.CONTRASTS:
        vector = (
            reconstructed[:, study.MODES.index(first)]
            - reconstructed[:, study.MODES.index(second)]
        )
        np.testing.assert_allclose(vector, result["panel"][name]["differences"])
        assert result["panel"][name]["signs"] == np.sign(vector).astype(int).tolist()
        assert result["panel"][name]["complete"]
    assert result["panel"]["primary"] == result["panel"][
        "Bhalf_sampled_minus_Ghalf_mean"
    ]
    assert result["panel"]["complete"]

    for source_name, copy_name in (
        ("checkpoint", "inherited_Ghalf_final.pt"),
        ("summary", "inherited_B06_summary.json"),
        ("source", "inherited_B06_source.json"),
    ):
        original = getattr(inherited_files, source_name)
        assert (out / copy_name).read_bytes() == original.read_bytes()
    checkpoint = torch.load(out / "Bhalf_final.pt", map_location="cpu", weights_only=True)
    assert checkpoint["object"] == study.OBJECT and checkpoint["arm"] == "Bhalf"
    assert checkpoint["optimizer_steps"] == 8
    assert checkpoint["inherited_Ghalf_sha256"] == hashlib.sha256(
        inherited_files.checkpoint.read_bytes()
    ).hexdigest()
    curves = [json.loads(line) for line in (out / "curves.jsonl").read_text().splitlines()]
    assert len(curves) == 4
    assert {row["when"] for row in curves} == {"before_collection", "after_update"}
    train_rows = [
        json.loads(line) for line in (out / "train_episodes.jsonl").read_text().splitlines()
    ]
    assert {row["arm"] for row in train_rows} == {"Bhalf"}
    assert not (out / "Ghalf_final.pt").exists()


def test_rejected_inherited_input_has_zero_fits_and_no_native_effects(
    tmp_path, admission, inherited_files
):
    inherited_files.checkpoint.write_bytes(inherited_files.checkpoint.read_bytes() + b"bad")
    constructor_calls = []
    result, out = run_fixture(
        tmp_path, admission, inherited_files,
        factory=lambda seed: constructor_calls.append(seed),
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"]["message"] == "retained B06 checkpoint SHA256 mismatch"
    assert result["fit_accounting"]["started_new_fits"] == 0
    assert result["fit_accounting"]["completed_new_fits"] == 0
    assert result["fit_accounting"]["inherited_Ghalf_fits_this_invocation"] == 0
    assert result["counts"]["new_train_team_steps"] == 0
    assert result["counts"]["final_eval_team_steps"] == 0
    assert constructor_calls == []
    assert not (out / "Bhalf_final.pt").exists()
    assert json.loads((out / "summary.json").read_text())["status"] == "INCOMPLETE"


def test_training_failure_retains_live_counts_and_one_actual_episode_start(
    tmp_path, admission, inherited_files
):
    class FailTraining(SyntheticAdapter):
        def __init__(self, seed, horizon):
            super().__init__(seed, horizon)
            self.steps = 0

        def step(self, actions):
            self.steps += 1
            if self.steps == 3:
                raise RuntimeError("fixture Bhalf training failed")
            return super().step(actions)

    result, out = run_fixture(
        tmp_path, admission, inherited_files,
        factory=lambda seed: FailTraining(seed, 8),
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"] == {
        "type": "RuntimeError", "message": "fixture Bhalf training failed"
    }
    assert result["fit_accounting"]["started_new_fits"] == 1
    assert result["fit_accounting"]["completed_new_fits"] == 0
    assert result["counts"]["new_train_episodes"] == 0
    assert result["counts"]["new_train_team_steps"] == 2
    early = result["new_Bhalf"]["first_256_episode_start_scale"]
    assert early["observed_episode_starts"] == 1 and not early["complete"]
    assert len((out / "train_episodes.jsonl").read_text().splitlines()) == 0
    assert not (out / "Bhalf_final.pt").exists()


def test_later_eval_failure_retains_complete_row_and_partial_step_counts(
    tmp_path, admission, inherited_files
):
    class FailSecondEvaluationMode(SyntheticAdapter):
        instances = 0

        def __init__(self, seed, horizon):
            super().__init__(seed, horizon)
            type(self).instances += 1
            self.number = type(self).instances
            self.steps = 0

        def step(self, actions):
            self.steps += 1
            if self.number == 3 and self.steps == 3:
                raise RuntimeError("fixture B07 evaluation failed")
            return super().step(actions)

    result, out = run_fixture(
        tmp_path, admission, inherited_files,
        factory=lambda seed: FailSecondEvaluationMode(seed, 8),
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"]["message"] == "fixture B07 evaluation failed"
    assert result["fit_accounting"]["completed_new_fits"] == 1
    assert result["counts"]["final_eval_episodes"] == 1
    assert result["counts"]["final_eval_team_steps"] == 10
    per_mode = result["counts"]["per_mode_evaluation"]
    assert per_mode["Bhalf_sampled"]["team_steps"] == 8
    assert per_mode["Bhalf_mean"]["step_calls"] == 3
    assert per_mode["Bhalf_mean"]["team_steps"] == 2
    rows = [json.loads(line) for line in (out / "eval_episodes.jsonl").read_text().splitlines()]
    assert [row["mode"] for row in rows] == ["Bhalf_sampled"]
    assert not result["panel"]["complete"]
    arrays = np.load(out / "evaluation_primitives.npz", allow_pickle=False)
    assert int(arrays["completed"].sum()) == 10


def test_invalid_eval_reward_counts_returned_transition_but_not_completed_primitive(
    tmp_path, admission, inherited_files
):
    class InvalidSecondEvaluationReward(SyntheticAdapter):
        instances = 0

        def __init__(self, seed, horizon):
            super().__init__(seed, horizon)
            type(self).instances += 1
            self.number = type(self).instances
            self.steps = 0

        def step(self, actions):
            result = super().step(actions)
            self.steps += 1
            if self.number == 2 and self.steps == 2:
                obs, scalar, terminated, truncated, info = result
                first_agent = next(iter(info["rewards_dict"]))
                info["rewards_dict"][first_agent] = float("nan")
                return obs, scalar, terminated, truncated, info
            return result

    result, out = run_fixture(
        tmp_path, admission, inherited_files,
        factory=lambda seed: InvalidSecondEvaluationReward(seed, 8),
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"] == {
        "type": "FloatingPointError", "message": "nonfinite B07 team reward"
    }
    first_mode = result["counts"]["per_mode_evaluation"]["Bhalf_sampled"]
    assert first_mode["step_calls"] == 2
    assert first_mode["team_steps"] == 2
    assert first_mode["valid_reward_steps"] == 1
    assert result["counts"]["final_eval_team_steps"] == 2
    assert result["counts"]["final_eval_valid_reward_steps"] == 1
    assert result["counts"]["final_eval_episodes"] == 0
    arrays = np.load(out / "evaluation_primitives.npz", allow_pickle=False)
    assert int(arrays["completed"].sum()) == 1
    assert len((out / "eval_episodes.jsonl").read_text().splitlines()) == 0


def test_eval_close_failure_retains_complete_exposure(tmp_path, admission, inherited_files):
    class FailFirstEvaluationClose(SyntheticAdapter):
        instances = 0

        def __init__(self, seed, horizon):
            super().__init__(seed, horizon)
            type(self).instances += 1
            self.number = type(self).instances

        def close(self):
            if self.number == 2:
                raise RuntimeError("fixture B07 evaluation close failed")

    result, out = run_fixture(
        tmp_path, admission, inherited_files,
        factory=lambda seed: FailFirstEvaluationClose(seed, 8),
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"]["message"] == (
        "Bhalf_sampled: RuntimeError: fixture B07 evaluation close failed"
    )
    assert result["counts"]["final_eval_episodes"] == 12
    assert result["counts"]["final_eval_team_steps"] == 96
    assert len((out / "eval_episodes.jsonl").read_text().splitlines()) == 12
    assert not result["panel"]["complete"]


def test_watchdog_before_scientific_constructor_reports_zero_new_fit(
    tmp_path, admission, inherited_files
):
    result = study.run(
        study.Config.engineering(), tmp_path / "timed-out", admission,
        start=study.time.monotonic() - 181,
        factory=lambda _seed: (_ for _ in ()).throw(AssertionError("constructor called")),
        fixture_files=inherited_files,
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"]["type"] == "TimeoutError"
    assert result["fit_accounting"]["started_new_fits"] == 0
    assert result["counts"]["new_train_team_steps"] == 0
    assert result["counts"]["final_eval_team_steps"] == 0


def test_production_overrides_are_refused_before_output(tmp_path, admission, inherited_files):
    out = tmp_path / "unused"
    with pytest.raises(ValueError, match="environment cannot be overridden"):
        study.run(
            study.Config(master=8941), out, admission,
            factory=lambda _seed: SyntheticAdapter(1, 8),
        )
    assert not out.exists()
    with pytest.raises(ValueError, match="inherited inputs cannot be overridden"):
        study.run(study.Config(master=8941), out, admission, fixture_files=inherited_files)
    assert not out.exists()
