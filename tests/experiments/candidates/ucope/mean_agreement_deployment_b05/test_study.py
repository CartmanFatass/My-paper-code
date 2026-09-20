import hashlib
import json

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.mean_agreement_deployment_b05 import study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def run_fixture(tmp_path, archive_factory, admission, *, factory=None):
    archive, digest = archive_factory()
    result = study.run(
        study.Config.engineering(),
        tmp_path / "result",
        admission,
        factory=factory,
        archive_path=archive,
        archive_sha256=digest,
    )
    return result, tmp_path / "result", archive, digest


def test_checkpoint_archive_is_verified_and_metadata_is_strict(archive_factory, monkeypatch):
    config = study.Config.engineering()
    archive, digest = archive_factory()
    payloads, identity = study.load_checkpoint_pair(config, archive, digest)
    assert set(payloads) == {"B", "G"}
    assert identity["sha256"] == digest
    assert identity["in_memory_extraction_only"]
    assert set(identity["members"]) == {"B", "G"}
    assert all(item["sha256"] for item in identity["members"].values())

    called = []
    safe_load = study._safe_torch_load
    monkeypatch.setattr(study, "_safe_torch_load", lambda _data: called.append(True))
    with pytest.raises(ValueError, match="archive SHA256 mismatch"):
        study.load_checkpoint_pair(config, archive, "0" * 64)
    assert called == []
    monkeypatch.setattr(study, "_safe_torch_load", safe_load)

    wrong, wrong_digest = archive_factory(overrides={"B": {"optimizer_steps": 4095}})
    with pytest.raises(ValueError, match="optimizer_steps mismatch"):
        study.load_checkpoint_pair(config, wrong, wrong_digest)

    missing, missing_digest = archive_factory(omit=("G_final.pt",))
    with pytest.raises(ValueError, match="exactly one regular G_final.pt"):
        study.load_checkpoint_pair(config, missing, missing_digest)


def test_complete_fixture_preserves_weights_and_reconstructs_all_contrasts(
    tmp_path, archive_factory, admission
):
    result, out, archive, digest = run_fixture(tmp_path, archive_factory, admission)
    assert result["status"] == "COMPLETE"
    assert result["object"] == study.OBJECT
    assert result["launch_sha"] == admission["sha"]
    assert result["counts"]["new_fits"] == 0
    assert result["counts"]["optimizer_steps"] == 0
    assert result["counts"]["train_episodes"] == 0
    assert result["counts"]["eval_episodes"] == 12
    assert result["counts"]["eval_team_steps"] == 72
    assert result["checkpoint_archive"]["sha256"] == digest
    assert set(result["checkpoint_archive"]["members"]) == {"B", "G"}
    assert result["actor_sources"]["C"] == result["actor_sources"]["B"]
    assert result["actor_sources"]["G_sampled"] == result["actor_sources"]["G_mean"]
    assert result["training_exposure"]["inherited_B04_training_fits_complete_batch"] == 6
    assert result["training_exposure"]["new_fits"] == 0
    assert result["actor_integrity"]
    assert all(
        item["exactly_unchanged"]
        and item["before_sha256"] == item["after_sha256"]
        and item["parameter_l2_movement"] == 0
        and item["optimizer_steps"] == 0
        for item in result["actor_integrity"].values()
    )
    before = result["actor_digests_before"]
    assert before["C"] == before["B"]
    assert before["G_sampled"] == before["G_mean"]

    assert result["panel"]["complete"] and result["panel"]["all_panels_complete"]
    arrays = np.load(out / "primitives.npz", allow_pickle=False)
    assert arrays["arm_names"].tolist() == list(study.ARMS)
    assert arrays["completed"].all()
    assert not arrays["eligibility"][:, 2:].any()
    assert (arrays["branches"][:, 2:] == study.FORCED_FRESH).all()
    assert np.isfinite(arrays["c_d_keep"][:, 0][arrays["eligibility"][:, 0]]).all()
    assert np.isnan(arrays["c_d_keep"][:, 1:]).all()

    reconstructed = arrays["rewards"].sum(axis=2) / study.Config.engineering().horizon
    for arm_index, arm in enumerate(study.ARMS):
        np.testing.assert_allclose(
            reconstructed[:, arm_index], result["panel"]["returns"][arm], rtol=0, atol=0
        )
    for name, first, second in study.CONTRASTS:
        vector = reconstructed[:, study.ARMS.index(first)] - reconstructed[:, study.ARMS.index(second)]
        np.testing.assert_allclose(vector, result["panel"][name]["differences"], rtol=0, atol=0)
        assert result["panel"][name]["signs"] == np.sign(vector).astype(int).tolist()
        assert result["panel"][name]["conditional_se"] is not None
        assert result["panel"][name]["complete"]

    prepared = 3 * 6 * 5 * 3
    assert result["counts"]["gaussian_scalar_slots_prepared"] == prepared
    assert result["counts"]["gate_uniform_slots_prepared"] == 3 * 6 * 5
    assert result["counts"]["gaussian_scalar_draws_used"] < prepared * 3
    assert result["counts"]["gate_uniform_draws_used"] == result["counts"]["per_arm"]["B"]["gate_uniforms_used"]
    assert result["counts"]["per_arm"]["C"]["gate_uniforms_used"] == 0
    assert result["counts"]["per_arm"]["G_mean"]["gaussian_vectors_used"] == 0
    assert result["counts"]["per_arm"]["C"]["c_proxy_decisions"] > 0
    assert result["counts"]["per_arm"]["G_sampled"]["eligibility_decisions"] == 0
    assert result["counts"]["per_arm"]["G_mean"]["eligibility_decisions"] == 0
    assert all(item["environment_constructors"] == 1 for item in result["counts"]["per_arm"].values())

    source = json.loads((out / "source.json").read_text())
    assert source["checkpoint_archive"]["sha256"] == digest
    assert source["checkpoint_archive"]["bytes"] == archive.stat().st_size
    assert set(source["checkpoint_archive"]["members"]) == {"B", "G"}
    assert json.loads((out / "config.json").read_text()) == {
        "master": 9931,
        "horizon": 6,
        "eval_episodes": 3,
        "watchdog_seconds": 180.0,
        "fixture": True,
    }
    assert json.loads((out / "admission.json").read_text()) == admission
    assert len((out / "episodes.jsonl").read_text().splitlines()) == 12
    assert json.loads((out / "summary.json").read_text())["status"] == "COMPLETE"


def test_actor_instances_and_episode_histories_are_independent(archive_factory):
    archive, digest = archive_factory()
    payloads, _identity = study.load_checkpoint_pair(
        study.Config.engineering(), archive, digest
    )
    actors = study.build_frozen_actors(study.Config.engineering().master, payloads)
    assert next(actors["C"].parameters()).data_ptr() != next(actors["B"].parameters()).data_ptr()
    assert next(actors["G_sampled"].parameters()).data_ptr() != next(actors["G_mean"].parameters()).data_ptr()

    class RecordingActor(torch.nn.Module):
        def __init__(self, actor):
            super().__init__()
            self.actor = actor
            self.hidden_inputs = []

        @property
        def log_std(self):
            return self.actor.log_std

        @property
        def duration(self):
            return self.actor.duration

        def forward(self, observations, hidden):
            self.hidden_inputs.append(hidden.detach().clone())
            return self.actor(observations, hidden)

    base = 100000 * study.Config.engineering().master
    gaussian, uniforms = study.episode_slots(base, 0, 6)
    for arm in ("C", "B"):
        recorder = RecordingActor(actors[arm])
        arrays = study._empty_primitives(study.Config.engineering())
        destination = {key: arrays[key][0, study.ARMS.index(arm)] for key in (
            "completed", "rewards", "commands", "means", "eligibility", "branches",
            "fresh", "c_d_keep", "c_d_fresh", "b_keep_probability",
        )}
        counters = dict.fromkeys((
            "environment_constructors", "actor_forward_calls", "recurrent_observations",
            "explicit_resets", "step_calls",
            "team_steps", "eligibility_decisions", "keep_decisions", "end_decisions",
            "forced_fresh_decisions", "fresh_commands", "c_proxy_decisions",
            "gaussian_vectors_used", "gate_uniforms_used",
        ), 0)
        study.deploy_episode(
            SyntheticAdapter(1, 6), recorder, arm, 6, base + 30000,
            gaussian, uniforms, {"arm": arm, "phase": "eval", "episode": 0},
            destination, lambda: None, counters,
        )
        assert torch.count_nonzero(recorder.hidden_inputs[0]) == 0
        assert len(recorder.hidden_inputs) == 6


def test_mid_evaluation_failure_publishes_partial_rows_and_primitives(
    tmp_path, archive_factory, admission
):
    class FailSecondEnvironment(SyntheticAdapter):
        instances = 0

        def __init__(self, seed, horizon):
            super().__init__(seed, horizon)
            type(self).instances += 1
            self.number = type(self).instances
            self.steps = 0

        def step(self, actions):
            self.steps += 1
            if self.number == 2 and self.steps == 2:
                raise RuntimeError("fixture B environment failed")
            return super().step(actions)

    result, out, _archive, _digest = run_fixture(
        tmp_path,
        archive_factory,
        admission,
        factory=lambda seed: FailSecondEnvironment(seed, 6),
    )
    assert result["status"] == "INCOMPLETE"
    assert result["error"] == {"type": "RuntimeError", "message": "fixture B environment failed"}
    assert result["counts"]["eval_episodes"] == 1
    assert 6 < result["counts"]["eval_team_steps"] < 72
    assert result["panel"]["returns"]["C"]
    assert not result["panel"]["complete"]
    assert (out / "summary.json").is_file()
    assert (out / "primitives.npz").is_file()
    arrays = np.load(out / "primitives.npz", allow_pickle=False)
    assert arrays["completed"].sum() == result["counts"]["eval_team_steps"]
    assert np.isfinite(arrays["commands"][:, 1]).any()
    assert len((out / "episodes.jsonl").read_text().splitlines()) == 1


def test_scope_rejects_modified_production_and_fixture_configs(tmp_path, admission):
    for config in (
        study.Config(master=8930),
        study.Config(master=8931, horizon=255),
        study.Config(master=8931, eval_episodes=63),
        study.Config(master=8931, watchdog_seconds=1799),
    ):
        with pytest.raises(ValueError):
            study.require_config(config)
    with pytest.raises(ValueError, match="fixed B05 engineering fixture"):
        study.require_config(study.Config(master=9931, horizon=7, fixture=True))
    with pytest.raises(ValueError, match="cannot be overridden"):
        study.run(
            study.Config(master=8931), tmp_path / "unused", admission,
            factory=lambda _seed: None,
        )
    assert not (tmp_path / "unused").exists()
