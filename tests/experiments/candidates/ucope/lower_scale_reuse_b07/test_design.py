import math

import pytest
import torch

from experiments.candidates.ucope.lower_scale_reuse_b07 import study


def test_validated_pair_has_identical_common_initial_bytes_and_private_states(
    tmp_path, inherited_files
):
    out = tmp_path / "validated"
    out.mkdir()
    rng_before = torch.random.get_rng_state().clone()
    result = study.validate_and_copy_inputs(
        study.Config.engineering(), out, inherited_files
    )
    assert torch.equal(rng_before, torch.random.get_rng_state())
    b_actor, b_critic = result["b_actor"], result["b_critic"]
    g_actor, g_critic = result["g_actor"], result["g_critic"]
    digests = result["provenance"]["common_initial_sha256"]
    assert len(set(digests.values())) == 1
    assert next(b_actor.parameters()).data_ptr() != next(g_actor.parameters()).data_ptr()
    assert next(b_critic.parameters()).data_ptr() != next(g_critic.parameters()).data_ptr()
    torch.testing.assert_close(
        b_actor.log_std, torch.full((3,), math.log(0.5)), rtol=0, atol=0
    )
    torch.testing.assert_close(b_actor.duration.logits, torch.zeros(2), rtol=0, atol=0)
    assert b_actor.log_std.requires_grad and b_actor.duration.logits.requires_grad
    for name, original in result["provenance"]["originals"].items():
        assert result["provenance"]["copies"][name]["sha256"] == original["sha256"]
    assert result["provenance"]["g_optimizer_constructed"] is False


def test_fixed_scope_and_production_input_mapping_reject_overrides(inherited_files):
    for config in (
        study.Config(master=8940),
        study.Config(master=8941, horizon=255),
        study.Config(master=8941, train_episodes=2046),
        study.Config(master=8941, eval_episodes=63),
        study.Config(master=8941, chunk=16),
        study.Config(master=8941, watchdog_seconds=5999),
    ):
        with pytest.raises(ValueError):
            study.require_config(config)
    with pytest.raises(ValueError, match="fixed B07 engineering fixture"):
        study.require_config(study.Config(master=9941, horizon=9, fixture=True))
    with pytest.raises(ValueError, match="cannot be overridden"):
        study.inherited_files(study.Config(master=8941), inherited_files)


def test_all_production_inputs_are_exact_fixed_b06_files_and_hashes():
    for master in study.ALLOWED_MASTERS:
        files = study.inherited_files(study.Config(master=master))
        expected_root = (
            study.REPO / f"runs/ucope/gaussian_scale_initialization_b06_{master}"
        )
        assert files.checkpoint == expected_root / "Ghalf_final.pt"
        assert files.summary == expected_root / "summary.json"
        assert files.source == expected_root / "source.json"
        assert files.checkpoint_sha256 == study.EXPECTED_INPUT_SHA256[master]["checkpoint"]
        assert files.summary_sha256 == study.EXPECTED_INPUT_SHA256[master]["summary"]
        assert files.source_sha256 == study.EXPECTED_INPUT_SHA256[master]["source"]
