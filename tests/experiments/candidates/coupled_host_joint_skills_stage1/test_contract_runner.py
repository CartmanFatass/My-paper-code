"""Cell-1 runner package (T3): adapter, recipes, models, matching table and a technical smoke.

Every world used here is outside the declared dev (1000-1031) and hold-out (2000-2031) panels;
the smoke fits are technical checks (2 lanes x 500 steps x 1 rollout, hidden 32), not fits.
"""
from __future__ import annotations

import ast
from dataclasses import replace
import json
import math
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.coupled_host_joint_skills_stage1 import runner
from experiments.candidates.coupled_host_joint_skills_stage1.adapter import (
    DEV_WORLDS, HOLDOUT_WORLDS, OBS_DIM, PANEL_WORLD_SET, STATE_DIM, ContractCountAdapter,
    ContractError, contract_reward_check, make_envs, training_world_seed,
)
from experiments.candidates.coupled_host_joint_skills_stage1.configuration import (
    DEFAULT_SPEC, PAIRS, SEEDS, FitSpec, is_declared_fit_spec, make_config, matching_table,
)
from experiments.candidates.coupled_host_joint_skills_stage1.models import (
    SET_CONCAT_DIM_AT_256, SetActorBase, StateSetEncoder, assert_route, build_agent, route_facts,
    strict_sync,
)

WORLDS = (9111, 9112)
TINY = replace(DEFAULT_SPEC, train_lanes=2, eval_lanes=1, rollouts=1, panels=(0, 1), hidden_size=32,
               n_heads=2, n_layers=1, ppo_epochs=1, sequence_batch_size=64, coordinator_batch_size=64,
               torch_threads=1, dev_worlds=(9113,), holdout_worlds=(9114,), probe_panel_worlds=(9115,),
               probe_rollouts=1)


def _envs(count=1, worlds=WORLDS):
    return make_envs(count, list(worlds[:count]))


# ------------------------------------------------------------------------------ adapter


def test_adapter_state_layout_scaling_and_validity_bits():
    env = _envs()[0]
    assert isinstance(env, ContractCountAdapter)
    assert (env.n_uavs, env.n_users, env.obs_dim, env.state_dim, env.native_state_dim) == (6, 50, 90, 133, 119)
    obs, info = env.reset(seed=9111)
    assert obs.shape == (6, OBS_DIM) and info["state"].shape == (STATE_DIM,)
    assert info["world_seed"] == 9111 and info["native_state_dim"] == 119
    host = env.host
    for step in range(3):
        state = info["state"] if step == 0 else info["next_state"]
        uav = state[:24].reshape(8, 3)
        np.testing.assert_array_equal(state[24:32], [1, 1, 1, 1, 1, 1, 0, 0])
        np.testing.assert_array_equal(uav[6:], 0.0)
        assert np.all(uav[:6] >= 0.0) and np.all(uav[:6] <= 1.0)
        np.testing.assert_allclose(uav[:6, :2], host.uav_positions[:, :2] / 5000.0, rtol=1e-6)
        np.testing.assert_allclose(uav[:6, 2], (host.uav_positions[:, 2] - 50.0) / 100.0, rtol=1e-6, atol=1e-7)
        np.testing.assert_allclose(state[32:132].reshape(50, 2), host.user_positions / 5000.0, rtol=1e-6)
        assert state[132] == pytest.approx(host.current_step / 500.0)
        # Same information as the native 119-dim state: it is recoverable exactly (up to float32).
        native = host._get_state()
        np.testing.assert_allclose(native[:18].reshape(6, 3)[:, :2], uav[:6, :2] * 5000.0, rtol=1e-6)
        obs, _reward, _term, _trunc, info = env.step(np.random.default_rng(step).uniform(-1, 1, (6, 3)))
        assert obs.shape == (6, OBS_DIM)


def test_reset_requires_an_explicit_world_seed_and_is_deterministic():
    env = _envs()[0]
    with pytest.raises(ContractError):
        env.reset()
    _, first = env.reset(seed=9112)
    env.step(np.zeros((6, 3)))
    _, second = env.reset(seed=9112)
    np.testing.assert_array_equal(first["state"], second["state"])
    with pytest.raises(ContractError):
        make_envs(1, [9112], horizon=20)


def test_reward_identity_on_real_steps_and_tamper_detection():
    env = _envs()[0]
    env.reset(seed=9111)
    rng = np.random.default_rng(3)
    for _ in range(25):
        _obs, reward, _term, _trunc, info = env.step(rng.uniform(-1.5, 1.5, (6, 3)))
        contract = info["contract"]
        assert 6 * reward == pytest.approx(contract["contract_reward"], abs=1e-12)
        assert contract["contract_reward"] == pytest.approx(
            0.5 * (contract["coverage_backhauled"] + contract["throughput_term"]), abs=1e-12)
        assert contract["action_clip_events"] == env.host.reward_info["action_clip_events"]
    reward_info = dict(env.host.reward_info)
    with pytest.raises(ContractError):
        contract_reward_check(reward + 1e-3, reward_info)
    reward_info["contract_reward"] += 1e-3
    with pytest.raises(ContractError):
        contract_reward_check((reward_info["contract_reward"]) / 6, reward_info)


def test_training_world_seeds_avoid_panels_are_shared_by_pairs_and_distinct():
    seen = {}
    for h_seed, set_seed in PAIRS:
        for lane in range(DEFAULT_SPEC.train_lanes):
            for episode in range(DEFAULT_SPEC.rollouts + 1):
                world = training_world_seed(h_seed, lane, episode)
                assert world == training_world_seed(set_seed, lane, episode)
                assert world not in PANEL_WORLD_SET
                assert seen.setdefault(world, (h_seed % 1000, lane, episode)) == (h_seed % 1000, lane, episode)
    assert len(seen) == 3 * 16 * 46
    assert training_world_seed(931201, 0, 0) == 320100
    assert training_world_seed(931201, 15, 44) == 300000 + 20100 + 15 + 440000
    with pytest.raises(ValueError):
        training_world_seed(931201, 100, 0)
    assert DEV_WORLDS == tuple(range(1000, 1032)) and HOLDOUT_WORLDS == tuple(range(2000, 2032))


# ------------------------------------------------------------------------------ recipes / models


def test_config_recipes_and_guards():
    envs = _envs()
    h = make_config("H", envs, SEEDS["H"][0], TINY)
    s = make_config("SET", envs, SEEDS["SET"][0], TINY)
    assert (h.state_dim, h.obs_dim, s.state_dim, s.obs_dim) == (133, 90, 133, 90)
    assert h.policy_interruption_mode == "d2" and s.policy_interruption_mode == "off"
    assert (h.skill_cap_k_max, h.team_cap_k_Z, h.age_feature) == (10, 10, "off")
    assert math.isinf(h.interruption_cost_c) and math.isinf(h.interruption_cost_c_Z)
    assert h.k == s.k == 10 and h.rollout_length == h.episode_length == 500
    assert h.use_horizon_window is False and s.use_central_snapshot_in_flat_actor is True
    assert (h.n_Z, h.n_z, s.n_Z, s.n_z) == (6, 6, 1, 1)
    assert s.disable_high_level_training and not getattr(h, "disable_high_level_training", False)
    with pytest.raises(ValueError):
        make_config("H6", envs, 1, TINY)
    assert DEFAULT_SPEC.horizon == 500 and DEFAULT_SPEC.train_lanes == 16 and DEFAULT_SPEC.rollouts == 45
    assert DEFAULT_SPEC.panels == (0, 15, 30, 45) and DEFAULT_SPEC.hidden_size == 256
    assert SEEDS == {"H": (931201, 931307, 931413), "SET": (932201, 932307, 932413)}
    assert is_declared_fit_spec(DEFAULT_SPEC) and is_declared_fit_spec(replace(DEFAULT_SPEC, area_size=6000))
    assert not is_declared_fit_spec(TINY)


@pytest.mark.parametrize("attribute, value", [
    ("team_cap_k_Z", 12), ("skill_cap_k_max", 5), ("interruption_cost_c", 1.0),
    ("interruption_cost_c_Z", 0.5), ("age_feature", "normalized"), ("policy_interruption_mode", "off"),
])
def test_build_agent_refuses_a_non_declared_h_route(tmp_path, attribute, value):
    config = make_config("H", _envs(), SEEDS["H"][0], TINY)
    setattr(config, attribute, value)
    with pytest.raises(ValueError):
        build_agent(config, str(tmp_path))


def test_models_widths_routes_and_d2_caps_are_asserted(tmp_path):
    envs = _envs()
    spec = replace(TINY, hidden_size=256, n_heads=8, n_layers=2)
    agents = {}
    configs = {}
    for arm in ("H", "SET"):
        configs[arm] = make_config(arm, envs, SEEDS[arm][0], spec)
        agents[arm] = build_agent(configs[arm], str(tmp_path / arm))
    base = agents["SET"].skill_discoverer.actor.base
    assert isinstance(base, SetActorBase)
    assert base.concat_dim == SET_CONCAT_DIM_AT_256 == 693
    assert base.fusion[0].in_features == 693 and base.row_encoder[0].in_features == 90
    assert base.input_dim == 90 + 133 + 6 * 90 + 6
    assert isinstance(agents["H"].skill_coordinator.state_embedding, StateSetEncoder)
    assert isinstance(agents["H"].skill_discoverer.critic.base, StateSetEncoder)
    facts = route_facts(agents["H"])
    assert facts["d2_enabled"] and facts["d2_k_max"] == facts["d2_k_Z"] == 10
    assert math.isinf(facts["d2_cost_c"]) and math.isinf(facts["d2_cost_c_Z"])
    assert facts["d2_age_feature"] == "off" and not facts["use_ha_ctse"]
    assert not route_facts(agents["SET"])["d2_enabled"] and route_facts(agents["SET"])["use_central_snapshot"]
    # theta_0 of the d2 displacement metric matches the substituted coordinator.
    params = list(agents["H"].skill_coordinator.parameters())
    assert [p.shape for p in params] == [p.shape for p in agents["H"].d2_coordinator_theta0]
    agents["H"].d2_k_Z = 11
    with pytest.raises(AssertionError):
        assert_route(agents["H"], "H")
    table = matching_table(configs["H"], configs["SET"], {arm: agents[arm] for arm in ("H", "SET")}, spec)
    for key in ("lanes", "horizon", "rollouts", "exposure_team_steps_per_fit", "observation_encoding",
                "state_encoding", "snapshot_timing", "reward_units", "gamma_gae", "normalisation",
                "learning_rates", "ppo", "batch_units", "optimizer_calls", "parameter_counts",
                "information_entry_points", "reset_bootstrap_rule", "evaluation", "dtype_threads",
                "rng_roles", "final_rule", "equal_update_count", "cost_asymmetry",
                "differing_config_fields", "routes", "pairs_by_position"):
        assert key in table, key
    assert table["parameter_counts"]["SET"]["skill_discoverer.actor.base"] > 0
    assert "policy_interruption_mode" in table["differing_config_fields"]
    json.dumps(runner.jsonable(table), allow_nan=False)


def test_strict_sync_copies_learned_state(tmp_path):
    envs = _envs()
    for arm in ("H", "SET"):
        config = make_config(arm, envs, SEEDS[arm][0], TINY)
        torch.manual_seed(1)
        source = build_agent(config, str(tmp_path / f"{arm}_s"))
        torch.manual_seed(2)
        target = build_agent(config, str(tmp_path / f"{arm}_t"))
        assert runner.digest_agent(source) != runner.digest_agent(target)
        strict_sync(target, source)
        assert runner.digest_agent(source) == runner.digest_agent(target)


# ------------------------------------------------------------------------------ runner


def test_non_declared_spec_is_refused_on_panel_worlds(tmp_path):
    for field, worlds in (("dev_worlds", (1000,)), ("holdout_worlds", (2031,)), ("probe_panel_worlds", (1005,))):
        with pytest.raises(ValueError, match="panel"):
            runner.check_spec_worlds(replace(TINY, **{field: worlds}))
    out = tmp_path / "refused"
    assert runner.run_fit(out, "SET", SEEDS["SET"][0], "t", {"sha": "t"},
                          replace(TINY, dev_worlds=(1000,))) == 1
    result = json.loads((out / "summary.json").read_text())
    assert not result["fit_started"] and "panel" in result["failure"]
    runner.check_spec_worlds(DEFAULT_SPEC, SEEDS["H"] + SEEDS["SET"])


@pytest.mark.parametrize("arm", ["H", "SET"])
def test_tiny_smoke_fit_updates_and_evaluates(tmp_path, arm):
    out = tmp_path / arm
    code = runner.run_fit(out, arm, SEEDS[arm][0], "technical-fixture", {"sha": "technical-fixture"}, TINY)
    assert code == 0, (out / "summary.json").read_text()
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and result["fit_started"]
    assert result["counts"] == {"training_team_steps": 1000, "stored_team_steps": 1000,
                                "training_episodes": 2, "updates": 1,
                                "evaluation_team_steps": 2000, "evaluation_episodes": 4}
    assert result["config"]["obs_dim"] == 90 and result["config"]["state_dim"] == 133
    assert result["initial_parameter_digest"] != result["final_parameter_digest"]
    moved = result["parameter_motion"]
    required = ["discoverer_actor", "discoverer_critic", "discoverer_critic.base"]
    if arm == "H":
        required += ["coordinator", "team_discriminator", "individual_discriminator",
                     "coordinator.state_embedding", "team_discriminator.state_encoder"]
    else:
        required += ["discoverer_actor.base", "discoverer_actor.base.state_encoder"]
    for name in required:
        assert moved[name]["delta_l2"] > 0, name
    if arm == "SET":
        assert result["optimizer_calls"]["coordinator"] == 0
    rows = [json.loads(line) for line in (out / "training.jsonl").read_text().splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["world_seeds"] == [training_world_seed(SEEDS[arm][0], lane, 0) for lane in range(2)]
    facts = row["terminal_facts"]
    assert facts["low_level_dones_last_step_all_true"] and not facts["low_level_dones_before_last_any"]
    if arm == "H":
        assert facts["d2_last_team_row_terminal_all"] and facts["d2_last_agent_row_terminal_all"]
        assert facts["d2_open_segments_before_update"] == 0
        assert facts["d2_team_rows"] == 2 * 50 and facts["d2_team_rows_terminal"] == 2
        causes = row["d2_metrics"]["cause_counts"]
        assert causes == {"reset": 2, "team_gap": 0, "team_cap": 98, "gap": 0, "cap": 0}
        d2 = row["d2_metrics"]
        assert d2["team_decisions"] == d2["decision_steps"] == 100 and d2["sampled_total"] == 600
    else:
        assert facts["disable_high_level_training"] and facts["high_level_valid_rows"] == 0
    panels = {p["file"]: p for p in result["panels"]}
    assert sorted(panels) == ["panel_00_dev_deterministic.json", "panel_01_dev_deterministic.json",
                              "panel_01_holdout_deterministic.json", "panel_01_holdout_sampled.json"]
    for name in panels:
        panel = json.loads((out / name).read_text())
        assert panel["status"] == "complete" and panel["frozen_weights_and_normalizers"]
        assert not any(panel["optimizer_calls"].values())
        world = panel["per_world"][0]
        assert world["world_seed"] in (9113, 9114) and world["steps"] == 500
        assert world["clusters"]["centre_source"] == "generator_replay"
        for key in runner.READER_KEYS:
            assert key in world, key
        assert len(world["relay_position_share_by_agent"]) == 6
        assert sum(world["relay_hops"]["relays_per_routed_uav_step_hist"]) >= 0
        assert ("labels" in panel) == (arm == "H")
        if arm == "H":
            assert panel["labels"]["d2_team_causes"]["other"] == 0
    assert result["memory"]["evaluation_overlap"][0]["after_target_build"]["VmRSS_kib"] > 0
    assert result["resources"]["cpu_seconds_in_run_fit"] > 0
    table = json.loads((out / "matching_table.json").read_text())
    assert set(table["routes"]) == {"H", "SET"}
    assert result["memory"]["matching_table_build"]["after"]["VmRSS_kib"] > 0
    assert (out / "evaluation_logs" / "r01_holdout_sampled").is_dir()
    for checkpoint in result["checkpoints"]:
        state = torch.load(out / checkpoint["path"], weights_only=False)
        assert state["schema"] == 1 and state["direction"] == "coupled_host_joint_skills_stage1"
        config = make_config(arm, _envs(), SEEDS[arm][0], TINY)
        reader = build_agent(config, str(tmp_path / "reader"))
        for name, module in runner.model_modules(reader).items():
            module.load_state_dict(state["modules"][name], strict=True)


def test_probe_writes_timing_without_panel_scores(tmp_path):
    out = tmp_path / "probe"
    assert runner.run_fit(out, "SET", SEEDS["SET"][0], "t", {"sha": "t"}, TINY, probe=True) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and result["probe"] and result["panels"] == []
    assert not list(out.glob("panel_*.json")) and not list(out.glob("checkpoint_*.pt"))
    probe = json.loads((out / "timing_probe.json").read_text())
    for key in ("seconds_per_rollout", "per_rollout", "ms_per_team_step", "panel_run",
                "wall_cpu_ratio_training", "projection", "memory"):
        assert key in probe, key
    for key in ("collection", "update", "wall", "cpu"):
        assert probe["seconds_per_rollout"][key] > 0
    for key in ("env", "policy", "store", "update"):
        assert probe["ms_per_team_step"][key] > 0
    assert probe["panel_run"]["scores"] == "not recorded (timing only)"
    assert probe["projection"]["fit_wall_seconds"] > 0 and probe["projection"]["fit_cpu_seconds"] > 0
    assert probe["memory"]["evaluation_overlap"][0]["before_target_build"]["VmRSS_kib"] > 0
    assert probe["team_steps"] == 1000


def test_cli_checks_admission_before_run(tmp_path, monkeypatch):
    calls = []

    def refuse(*args, **kwargs):
        calls.append(("admission", args, kwargs))
        raise RuntimeError("not admitted")

    monkeypatch.setattr(runner, "require_admission", refuse)
    monkeypatch.setattr(runner, "run_fit", lambda *args, **kwargs: calls.append("scientific effects"))
    out = tmp_path / "never-created"
    with pytest.raises(RuntimeError, match="not admitted"):
        runner.main(["--arm", "H", "--seed", str(SEEDS["H"][0]), "--launch-sha", "t",
                     "--out", str(out), "--area-size", "5000"])
    assert len(calls) == 1 and calls[0][0] == "admission" and not out.exists()
    assert calls[0][2] == {"direction": "coupled_host_joint_skills_stage1"}
    with pytest.raises(SystemExit):
        runner.main(["--arm", "H", "--seed", str(SEEDS["SET"][0]), "--launch-sha", "t",
                     "--out", str(out), "--area-size", "5000"])
    with pytest.raises(SystemExit):
        runner.main(["--arm", "H", "--seed", str(SEEDS["H"][0]), "--launch-sha", "t",
                     "--out", str(out), "--area-size", "7000"])


def test_cli_passes_admitted_spec(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "abc"})

    def fake_run_fit(out, arm, seed, sha, admission, spec, probe=False):
        seen.update(out=out, arm=arm, seed=seed, sha=sha, spec=spec, probe=probe)
        return 0

    monkeypatch.setattr(runner, "run_fit", fake_run_fit)
    assert runner.main(["--arm", "SET", "--seed", str(SEEDS["SET"][1]), "--launch-sha", "abc",
                        "--out", str(tmp_path / "x"), "--area-size", "6000", "--probe"]) == 0
    assert seen["spec"] == replace(DEFAULT_SPEC, area_size=6000) and seen["probe"] is True
    with pytest.raises(ValueError, match="launch SHA"):
        runner.main(["--arm", "SET", "--seed", str(SEEDS["SET"][1]), "--launch-sha", "other",
                     "--out", str(tmp_path / "y"), "--area-size", "5000"])


def test_require_admission_is_called_exactly_once_inside_main():
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert source.count('require_admission(__file__, direction="coupled_host_joint_skills_stage1")') == 1
    tree = ast.parse(source)
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    calls = [node for node in ast.walk(main) if isinstance(node, ast.Call)
             and getattr(node.func, "id", None) == "require_admission"]
    assert len(calls) == 1
    everywhere = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                  and getattr(node.func, "id", None) == "require_admission"]
    assert len(everywhere) == 1


def test_package_import_keeps_torch_out():
    import subprocess
    import sys

    code = ("import sys; import experiments.candidates.coupled_host_joint_skills_stage1.host; "
            "print('torch' in sys.modules)")
    root = Path(runner.__file__).resolve().parents[3]
    result = subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "False"


def test_b02_bounded_head_spec_is_declared_and_parsed_for_per_step_fits(monkeypatch, tmp_path):
    """b02 SET-V-b: the per-step recipe with only the four action-head keys changed is a declared
    spec (may touch the panels); any other head setting is technical; the CLI passes the four
    flags into the per-step FitSpec and still refuses them for floors."""
    from experiments.candidates.coupled_host_joint_skills_stage1.configuration import (
        B02_BOUNDED_HEAD_SPEC,
        apply_action_head,
    )

    assert is_declared_fit_spec(B02_BOUNDED_HEAD_SPEC)
    assert B02_BOUNDED_HEAD_SPEC.continuous_action_distribution == "tanh_gaussian"
    assert (B02_BOUNDED_HEAD_SPEC.continuous_logstd_init, B02_BOUNDED_HEAD_SPEC.continuous_logstd_min,
            B02_BOUNDED_HEAD_SPEC.continuous_logstd_max) == (-1.0, -5.0, 0.0)
    assert not is_declared_fit_spec(replace(DEFAULT_SPEC, continuous_action_distribution="tanh_gaussian"))
    assert not is_declared_fit_spec(replace(B02_BOUNDED_HEAD_SPEC, continuous_logstd_max=0.5))
    assert not is_declared_fit_spec(replace(B02_BOUNDED_HEAD_SPEC, area_size=6000))
    # Only the four head keys differ from the b01 spec.
    from dataclasses import asdict
    diff = {k for k in asdict(DEFAULT_SPEC) if asdict(DEFAULT_SPEC)[k] != asdict(B02_BOUNDED_HEAD_SPEC)[k]}
    assert diff == {"continuous_action_distribution", "continuous_logstd_init",
                    "continuous_logstd_min", "continuous_logstd_max"}

    class Cfg:
        pass

    cfg = Cfg()
    apply_action_head(cfg, B02_BOUNDED_HEAD_SPEC)
    assert (cfg.continuous_action_distribution, cfg.continuous_logstd_init, cfg.continuous_logstd_min,
            cfg.continuous_logstd_max) == ("tanh_gaussian", -1.0, -5.0, 0.0)

    seen = {}

    def fake_run_fit(out, arm, seed, launch_sha, admission, spec, probe=False):
        seen.update(arm=arm, seed=seed, spec=spec)
        return 0

    monkeypatch.setattr(runner, "run_fit", fake_run_fit)
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "deadbeef", "status": "test"})
    out = tmp_path / "fit"
    rc = runner.main(["--arm", "SET", "--seed", "932201", "--launch-sha", "deadbeef", "--area-size", "5000",
                      "--out", str(out), "--continuous-action-distribution", "tanh_gaussian",
                      "--continuous-logstd-init", "-1.0", "--continuous-logstd-min", "-5.0",
                      "--continuous-logstd-max", "0.0"])
    assert rc == 0 and seen["arm"] == "SET" and seen["seed"] == 932201
    assert seen["spec"] == B02_BOUNDED_HEAD_SPEC and is_declared_fit_spec(seen["spec"])
    with pytest.raises(SystemExit):
        runner.main(["--floor", "random-target", "--worlds", "9111", "--launch-sha", "deadbeef",
                     "--out", str(tmp_path / "floor"), "--menu-dir", str(tmp_path / "menus"),
                     "--continuous-action-distribution", "tanh_gaussian"])
