"""One real tiny-host execution of the CF arm: the actual HMASD stack with the central input on.

Two lanes, twenty-step episodes (two ten-step recurrent chunks), the real Scenario 1 environment and
the real agent, through collection, the update and the independent evaluator. The rollout count is
reduced here: 45 and the nine panels are bound in `test_binding.py`. Technical check, no result.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
from hmasd.agent import HMASDAgent  # noqa: E402

shared = b01.shared
ADMISSION = {"sha": "tiny-technical-check", "command_sha256": "x"}
SEED = 772603


@pytest.fixture
def tiny(monkeypatch):
    monkeypatch.setattr(shared, "TRAIN_LANES", 2)
    monkeypatch.setattr(shared, "EVAL_LANES", 2)
    monkeypatch.setattr(shared, "HORIZON", 20)
    monkeypatch.setattr(shared, "PROCESS_START", shared.time.perf_counter())
    monkeypatch.setattr(matched, "ROLLOUTS", 2)
    monkeypatch.setattr(matched, "PANEL_ROLLOUTS", (1, 2))
    monkeypatch.setattr(matched, "CURVE_ROLLOUTS", (1,))


def config_for(arm, multiplier, monkeypatch):
    monkeypatch.setitem(matched.CURRENT, "lr_multiplier", multiplier)
    matched.bind()
    envs = [SimpleNamespace(state_dim=119, obs_dim=104) for _ in range(2)]
    return matched.make_config(arm, envs, SEED)


def test_real_tiny_cf_fit_runs_collection_update_and_evaluator(tmp_path, tiny, monkeypatch):
    out = tmp_path / "CF"
    assert matched.run_fit("CF", SEED, 0, 2.0, out, admission=ADMISSION) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["counts"]["update_stages"] == 2 and summary["counts"]["model_constructions"] == 2
    assert summary["counts"]["training_transitions"] == 2 * 20 * 2
    assert len(summary["panels"]) == 2
    assert all(panel["status"] == "complete" and panel["completed_episodes"] == 2
               for panel in summary["panels"])
    for key in ("learner_config", "evaluation_config"):
        config = summary[key]
        assert config[matched.CF_FLAG] is True
        assert config["policy_interruption_mode"] == "off" and config["n_Z"] == config["n_z"] == 1
        assert config["k"] == 10 and config["state_dim"] == 119 and config["obs_dim"] == 104
    calls = summary["optimizer_calls"]
    assert calls["discoverer_actor"] > 0 and calls["discoverer_critic"] > 0
    assert all(calls[k] == 0 for k in b01.FLAT_ONLY_ZERO)
    assert not any(summary["evaluation_optimizer_calls"].values())
    displacement = summary["training_rows"][-1]["relative_initialization_displacement"]
    assert displacement["discoverer_actor"] > 0 and displacement["discoverer_critic"] > 0
    assert displacement["coordinator"] in (None, 0.)
    assert summary["lr_multiplier"] == 2.0 and summary["stage"] == 0
    assert list(matched.fit_endpoint(summary)) == [1, 2]
    # The multiplier reached the stored configuration exactly once, and only the tuned groups.
    standing = config_for("CF", 1.0, monkeypatch)
    learner = summary["learner_config"]
    assert learner["lr_discoverer_actor"] == 2 * standing.lr_discoverer_actor
    assert learner["lr_discoverer_critic"] == 2 * standing.lr_discoverer_critic
    assert learner["lr_coordinator"] == standing.lr_coordinator
    assert learner["lr_discriminator"] == standing.lr_discriminator


@pytest.mark.parametrize("multiplier", [0.5, 1.0, 2.0])
def test_multiplier_reaches_the_real_optimizer_groups_of_cf_only(tmp_path, tiny, monkeypatch,
                                                                 multiplier):
    standing = config_for("CF", 1.0, monkeypatch)
    base = {"actor": standing.lr_discoverer_actor, "critic": standing.lr_discoverer_critic,
            "coordinator": standing.lr_coordinator, "discriminator": standing.lr_discriminator}
    assert not getattr(standing, "use_lr_decay", False)  # no schedule would rescale these
    config = config_for("CF", multiplier, monkeypatch)
    agent = HMASDAgent(config, log_dir=str(tmp_path / f"cf_{multiplier}"), device=torch.device("cpu"))
    assert [g["lr"] for g in agent.discoverer_actor_optimizer.param_groups] == \
        [base["actor"] * multiplier]
    assert [g["lr"] for g in agent.discoverer_critic_optimizer.param_groups] == \
        [base["critic"] * multiplier]
    # Never-trained groups keep the standing rates; on this route the discriminators have none.
    assert [g["lr"] for g in agent.coordinator_optimizer.param_groups] == [base["coordinator"]]
    assert agent.team_discriminator_optimizer is None
    assert agent.individual_discriminator_optimizer is None
    # The CF actor reads its own observation, the central snapshot and the ego one-hot; only the
    # input projection widens.
    assert agent.skill_discoverer.central_input_dim == 119 + 6 * 104 + 6
    assert agent.skill_discoverer.actor.base.mlp[0].in_features == 104 + 119 + 6 * 104 + 6
    assert agent.skill_discoverer.actor.base.mlp[0].out_features == config.hidden_size
    assert agent.skill_discoverer.critic.base.mlp[0].in_features == 119

    d1280 = config_for("D1280", multiplier, monkeypatch)
    assert (d1280.lr_discoverer_actor, d1280.lr_discoverer_critic) == (base["actor"], base["critic"])
    assert (d1280.lr_coordinator, d1280.lr_discriminator) == (base["coordinator"], base["discriminator"])
    assert not getattr(d1280, matched.CF_FLAG, False)
    standing_agent = HMASDAgent(d1280, log_dir=str(tmp_path / f"d_{multiplier}"),
                                device=torch.device("cpu"))
    assert [g["lr"] for g in standing_agent.discoverer_actor_optimizer.param_groups] == [base["actor"]]
    assert [g["lr"] for g in standing_agent.discoverer_critic_optimizer.param_groups] == [base["critic"]]
    assert standing_agent.skill_discoverer.central_input_dim == 0
    assert standing_agent.skill_discoverer.actor.base.mlp[0].in_features == 104
    assert standing_agent.skill_discoverer.critic.base.mlp[0].in_features == 119
