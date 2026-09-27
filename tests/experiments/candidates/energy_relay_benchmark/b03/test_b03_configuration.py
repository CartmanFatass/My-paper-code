"""B03 configuration: the declared GAS flags, the diff against B02 SET, B02 unchanged, runner."""

from __future__ import annotations

import hashlib
import json

import pytest

from experiments.candidates.energy_relay_benchmark.b02 import configuration as c2
from experiments.candidates.energy_relay_benchmark.b03 import configuration as c3
from scripts import run_energy_relay_benchmark_b03 as entry

# sha256 of json.dumps(c2.config_dict(make_b02_config(production_spec(925031))), sort_keys=True),
# computed from b02/configuration.py before the B03 change.
B02_CONFIG_DICT_SHA256 = "1085d3bc0fc138e01ee2f642027f49aa0f539b3ffa37e327d58f09a4498161ce"
# config_dict(T) vs config_dict(B02 SET) at the same seed, "gas" record aside: [SET, T].
T_VERSUS_SET = {
    "algorithm": ["mappo", "hmasd"], "baseline_algorithm": ["mappo", "hmasd"],
    "collects_high_level_samples": [False, None], "disable_high_level_training": [True, False],
    "lambda_h": [0.0, 0.01], "n_z": [1, 9], "ordinary_completed_segments": [False, True],
}


@pytest.fixture(scope="module")
def production():
    return c3.make_b03_config(c3.production_spec(26092711))


def test_declared_gas_configuration(production):
    c = production
    assert (c.seed, c.num_envs, c.rollout_length, c.episode_length, c.max_steps) == \
        (26092711, 2, 3000, 3000, 3000)
    assert (c.n_agents, c.obs_dim, c.state_dim, c.action_dim) == (8, 365, 306, 4)
    assert c.algorithm == "hmasd" and c.baseline_algorithm == "hmasd"
    assert (c.n_Z, c.n_z, c.k) == (1, 9, 10)
    assert (c.lambda_h, c.lambda_D, c.lambda_d, c.lambda_return, c.lambda_e) == \
        (0.01, 0.0, 0.0, 2.0, 1.0)
    assert c.ordinary_completed_segments is True and c.use_central_snapshot_in_flat_actor is True
    assert c.disable_high_level_training is False
    assert c.disable_discriminator_training is True and c.disable_discriminator_rewards is True
    assert not c.use_obsnorm and not c.use_statenorm
    assert c.high_level_buffer_size == 600 and c.total_timesteps == 1_200_000
    assert c.lr_coordinator == 1e-4 and c.policy_interruption_mode == "off"
    assert c3.actor_input_width(c) == 365 + 306 + 8 * 365 + 8 + 6 == 3605
    assert c3.central_input_width(c) == 306 + 18 + 1 + 8 * 365 + 8 == 3253
    assert c3.snapshot_width(c) == 306 + 18 + 8 == 332


def test_config_dict_versus_b02_set(production):
    t = c3.config_dict(production)
    s = c2.config_dict(c2.make_b02_config(c2.B02Spec(seed=26092711)))
    json.dumps(t, allow_nan=False)
    assert set(t) == set(s) | {"gas"} and t["gas"] == c3.GAS_RECORD
    diff = {key: [s[key], t[key]] for key in s if s[key] != t[key]}
    assert diff == T_VERSUS_SET


def test_b02_config_dict_is_unchanged():
    record = c2.config_dict(c2.make_b02_config(c2.production_spec(c2.TRAINING_SEED)))
    digest = hashlib.sha256(json.dumps(record, sort_keys=True, allow_nan=False).encode()).hexdigest()
    assert digest == B02_CONFIG_DICT_SHA256, json.dumps(record, sort_keys=True)


def test_seeds_and_exposure():
    assert c3.TRAINING_SEEDS == (26092711, 26092731, 925031) == entry.TRAINING_SEEDS
    for seed in c3.TRAINING_SEEDS:
        spec = c3.production_spec(seed)
        assert spec.transitions == 1_200_000 and c3.checkpoint_rollouts(spec) == \
            (34, 67, 100, 134, 167, 200)
    with pytest.raises(ValueError, match="unplanned"):
        c3.production_spec(915031)


def test_runner_arguments():
    args = entry.parse_args(["train", "--seed", "26092711", "--launch-sha", "s", "--out", "o",
                             "--resume-from", "ckpt/c03", "--resume-source-sha", "abc"])
    assert args.seed == 26092711 and str(args.resume_from) == "ckpt/c03"
    for bad in (["train", "--seed", "925030", "--launch-sha", "s", "--out", "o"],
                ["train", "--seed", "26092711", "--launch-sha", "s", "--out", "o",
                 "--resume-source-sha", "abc"],
                ["evaluate-checkpoint", "--checkpoint", "c", "--out", "o", "--launch-sha", "s"]):
        with pytest.raises(SystemExit):
            entry.parse_args(bad)


def test_runner_calls_b03_training_after_admission(tmp_path, monkeypatch):
    from experiments.candidates.energy_relay_benchmark.b03 import training as tr3
    from scripts import hmasd_admission

    order = []
    monkeypatch.setattr(hmasd_admission, "require_admission",
                        lambda *args, **kwargs: order.append("admission") or {"sha": "s"})
    monkeypatch.setattr(tr3, "run_training", lambda **kwargs: order.append(kwargs) or {})
    entry.main(["train", "--seed", "26092731", "--launch-sha", "s", "--out", str(tmp_path / "o"),
                "--device", "cpu"])
    assert order[0] == "admission"
    call = order[1]
    assert call["spec"] == c3.production_spec(26092731) and call["resume_from"] is None
    with pytest.raises(RuntimeError, match="admission"):
        entry.main(["train", "--seed", "26092731", "--launch-sha", "other", "--out",
                    str(tmp_path / "o")])
