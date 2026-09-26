"""B02 configuration invariants: SET switch on B09's native recipe, exposure, cadence."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from experiments.candidates.energy_relay_benchmark.b02 import configuration as cfg


@pytest.fixture(scope="module")
def production_config():
    return cfg.make_b02_config(cfg.production_spec(cfg.TRAINING_SEED))


def test_production_config_is_b09_native_plus_set_switch(production_config):
    c = production_config
    assert (c.seed, c.num_envs, c.rollout_length, c.episode_length, c.max_steps) == \
        (925031, 2, 3000, 3000, 3000)
    assert (c.n_agents, c.obs_dim, c.state_dim, c.action_dim) == (8, 365, 306, 4)
    assert (c.lambda_return, c.lambda_e) == (2.0, 1.0)
    assert not c.use_obsnorm and not c.use_statenorm
    # SET switch (ACG): mappo, k restored to 10, flag on, buffers recomputed for k = 10.
    assert c.algorithm == "mappo" and c.k == 10 and (c.n_Z, c.n_z) == (1, 1)
    assert c.use_central_snapshot_in_flat_actor is True
    assert c.disable_high_level_training and c.disable_discriminator_training
    assert c.disable_discriminator_rewards and c.collects_high_level_samples is False
    assert (c.lambda_D, c.lambda_d, c.lambda_h, c.lambda_cd, c.lambda_mi) == (0.0,) * 5
    assert c.high_level_buffer_size == 2 * (3000 // 10)
    assert c.batch_size == (2 * 3000 // c.num_mini_batch) * 8
    # Forced by HMASDAgent: ordinary segments are refused with disabled high-level training.
    assert c.ordinary_completed_segments is False
    assert cfg.actor_input_width(c) == 365 + 306 + 8 * 365 + 8 == 3599


def test_exposure_is_one_point_two_million(production_config):
    spec = cfg.production_spec(925031)
    assert spec.transitions == 1_200_000 == 200 * 2 * 3000 == cfg.TOTAL_TRANSITIONS
    assert production_config.total_timesteps == 1_200_000
    for change in (dict(rollouts=199), dict(rollout_length=2999), dict(lanes=3),
                   dict(checkpoint_every_transitions=100_000), dict(hidden_size=32)):
        with pytest.raises(ValueError):
            cfg.assert_production(replace(spec, **change))
    with pytest.raises(ValueError, match="unplanned"):
        cfg.production_spec(915031)


def test_checkpoint_cadence():
    spec = cfg.B02Spec()
    assert cfg.checkpoint_rollouts(spec) == (34, 67, 100, 134, 167, 200)
    transitions = [r * spec.transitions_per_rollout for r in cfg.checkpoint_rollouts(spec)]
    assert transitions == [204_000, 402_000, 600_000, 804_000, 1_002_000, 1_200_000]
    assert all(t >= (i + 1) * 200_000 > t - spec.transitions_per_rollout
               for i, t in enumerate(transitions))
    tiny = replace(spec, rollouts=2, rollout_length=60, episode_length=60,
                   checkpoint_every_transitions=120)
    assert cfg.checkpoint_rollouts(tiny) == (1, 2)
    assert cfg.checkpoint_rollouts(replace(tiny, checkpoint_every_transitions=10_000)) == (2,)


def test_config_dict_records_acg_fields_and_is_strict_json(production_config):
    record = cfg.config_dict(production_config)
    assert set(cfg.ACG_FIELDS) <= set(record)
    for key in ("lambda_return", "lambda_e", "total_timesteps", "ordinary_completed_segments",
                "use_central_snapshot_in_flat_actor", "k", "algorithm"):
        assert key in record
    assert record["total_timesteps"] == 1_200_000 and record["k"] == 10
    json.dumps(record, allow_nan=False)
    json.dumps(cfg.spec_record(cfg.B02Spec()), allow_nan=False)
