"""T-W macro-step contracts: per-step regression pins, menus, executor, decoders, floors, fits, CLI.

Every world used here is outside the declared dev (1000-1031) and hold-out (2000-2031) panels;
the fits are technical checks (2 lanes x 50 macro steps x 1 rollout, hidden 32), not fits.
"""
from __future__ import annotations

import ast
from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.coupled_host_joint_skills_stage1 import macro_runner as MR
from experiments.candidates.coupled_host_joint_skills_stage1 import runner
from experiments.candidates.coupled_host_joint_skills_stage1.adapter import (
    MACRO_HORIZON, OBS_DIM, PANEL_WORLD_SET, STATE_DIM, ContractError, MacroContractAdapter,
    decode_offset, decode_target, goto_actions, macro_training_world_seed, make_envs, make_macro_envs,
)
from experiments.candidates.coupled_host_joint_skills_stage1.configuration import (
    ACTION_HEAD_KEYS, DEFAULT_SPEC, SEEDS, MacroFitSpec, config_dict, is_declared_fit_spec,
    is_declared_macro_spec, make_config, make_macro_config,
)
from experiments.candidates.coupled_host_joint_skills_stage1.host import make_host
from experiments.candidates.coupled_host_joint_skills_stage1.menus import (
    MENU_WIDTH, MenuError, MenuProvider, check_menu, compute_menu, load_or_build_menu, menu_path,
)
from experiments.candidates.coupled_host_joint_skills_stage1.planner import closed_loop_execute

WORLD = 9111
TINY = dict(train_lanes=2, eval_lanes=1, rollouts=1, panels=(0, 1), hidden_size=32, n_heads=2, n_layers=1,
            ppo_epochs=1, sequence_batch_size=64, coordinator_batch_size=64, torch_threads=1,
            dev_worlds=(9113,), holdout_worlds=(9114,), probe_panel_worlds=(9115,), probe_rollouts=1)
PACKAGE = Path(runner.__file__).resolve().parent


@pytest.fixture(scope="module")
def menu_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("menus")


def tiny_spec(contract, **overrides):
    return MacroFitSpec(contract=contract, **{**TINY, **overrides})


# ------------------------------------------------------------------------------ per-step regression

#: sha256 of each per-step object's source segment at the pre-T-W commit (5259ed8c4 lineage);
#: T-W is additive, so none of them may change.
PER_STEP_SOURCE_PINS = {
    "adapter.py": {
        "training_world_seed": "c36c1c62ea71b406", "contract_reward_check": "cf2bf64b571fc835",
        "ContractCountAdapter": "e46b84aed01fd816", "make_envs": "7acddd7b1d4383a0"},
    "runner.py": {
        "seed_rng": "cc29070b9971126d", "preserve_rng": "19b27567e9064b1d", "digest_agent": "16ed5336a73951af",
        "reset_all": "75c81d57adb883db", "save_checkpoint": "59a507b213fce08d",
        "check_spec_worlds": "dbbc49aac034a34c", "WorldTracker": "5937c0306ecd9fb8",
        "run_panel": "ae06ac77bcdb433b", "evaluate_panels": "3bffe359ecddbf23",
        "terminal_facts": "905c6535a0fdb293", "build_matching_table": "a8cfc420f70b3eb5",
        "run_fit": "6cd20dec0d8916d0", "write_probe": "84373df7240865aa"},
    "configuration.py": {
        # is_declared_fit_spec re-pinned 2026-09-29 for b02 SET-V-b (B02_BOUNDED_HEAD_SPEC accepted as
        # declared; the b01 specs unchanged); pre-T-W digest was a414b828ef5416b9.
        "is_declared_fit_spec": "92a12b01cd48ab67", "matching_table": "6aca04173d7beb3c"},
    "models.py": {"StateSetEncoder": "f0d959152e09f744", "SetActorBase": "69f53dbba0d0c35f",
                  "build_agent": "d4b4f8944318b9de", "assert_route": "65d1c2bc862c9ba5",
                  "strict_sync": "8b7cbfea16663859"},
}
#: sha256 of json.dumps(config_dict(make_config(arm, ..., DEFAULT_SPEC)) minus the four action-head
#: keys, sort_keys=True, default=str), equal to the pre-T-W config_dict.
PER_STEP_CONFIG_PINS = {"H": "4ca691ef25e752f6fb2de59e99de4509ce104d1e19a15fa4ece56de93e31ec40",
                        "SET": "5bc96dcb9137effaca88416d4da72650ff0d2ec8fa57cce51382a2965023792a"}
ARGS_HEAD_DEFAULTS = {"continuous_action_distribution": "gaussian", "continuous_logstd_init": 0.0,
                      "continuous_logstd_min": -20.0, "continuous_logstd_max": 2.0}


def test_per_step_objects_are_source_identical_to_b01():
    for filename, pins in PER_STEP_SOURCE_PINS.items():
        text = (PACKAGE / filename).read_text(encoding="utf-8")
        tree = ast.parse(text)
        segments = {node.name: ast.get_source_segment(text, node) for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        for name, pin in pins.items():
            digest = hashlib.sha256(segments[name].encode("utf-8")).hexdigest()
            assert digest.startswith(pin), f"{filename}:{name} changed"


def test_per_step_config_is_b01_plus_default_action_head_keys():
    envs = make_envs(1, [WORLD])
    assert asdict(DEFAULT_SPEC)["continuous_action_distribution"] == "gaussian"
    assert is_declared_fit_spec(DEFAULT_SPEC)
    for arm in ("H", "SET"):
        values = config_dict(make_config(arm, envs, SEEDS[arm][0], DEFAULT_SPEC))
        head = {key: values.pop(key) for key in ACTION_HEAD_KEYS}
        assert head == ARGS_HEAD_DEFAULTS
        digest = hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()
        assert digest == PER_STEP_CONFIG_PINS[arm], arm


def _head_class(agent):
    return agent.skill_discoverer.actor.act.action_out


def test_action_head_pass_through_for_both_arms(tmp_path):
    from experiments.candidates.coupled_host_joint_skills_stage1.macro_models import build_macro_agent
    from experiments.candidates.coupled_host_joint_skills_stage1.models import build_agent

    envs = make_envs(1, [WORLD])
    bounded = dict(continuous_action_distribution="tanh_gaussian", continuous_logstd_init=-1.0,
                   continuous_logstd_min=-5.0, continuous_logstd_max=0.0)
    spec = replace(DEFAULT_SPEC, **{k: v for k, v in TINY.items() if k not in ("dev_worlds", "holdout_worlds",
                                                                                 "probe_panel_worlds")})
    macro_envs = make_macro_envs(1, [WORLD], "target")
    for arm in ("H", "SET"):
        default = build_agent(make_config(arm, envs, SEEDS[arm][0], spec), str(tmp_path / f"d{arm}"))
        assert type(_head_class(default)).__name__ == "DiagGaussian"
        config = make_config(arm, envs, SEEDS[arm][0], replace(spec, **bounded))
        for key, value in bounded.items():
            assert getattr(config, key) == value
        agent = build_agent(config, str(tmp_path / f"b{arm}"))
        head = _head_class(agent)
        assert type(head).__name__ == "TanhDiagGaussian"
        assert (head.logstd_init, head.logstd_min, head.logstd_max) == (-1.0, -5.0, 0.0)
        macro = build_macro_agent(make_macro_config(arm, macro_envs, SEEDS[arm][0],
                                                    tiny_spec("target", **bounded)), str(tmp_path / f"m{arm}"))
        assert type(_head_class(macro)).__name__ == "TanhDiagGaussian"
        assert (_head_class(macro).logstd_min, _head_class(macro).logstd_max) == (-5.0, 0.0)
    assert is_declared_macro_spec(MacroFitSpec(contract="target", **bounded))
    with pytest.raises(ValueError):
        make_config("H", envs, SEEDS["H"][0], replace(spec, continuous_action_distribution="beta"))


# ------------------------------------------------------------------------------ menus


def test_menu_is_deterministic_cached_and_checked(menu_dir, tmp_path):
    menu, digest, source = load_or_build_menu(WORLD, 5000, menu_dir)
    again, digest_again, source_again = load_or_build_menu(WORLD, 5000, menu_dir)
    assert (source, source_again) == ("computed", "loaded") and digest == digest_again and menu == again
    fresh, fresh_digest, _ = load_or_build_menu(WORLD, 5000, tmp_path / "other")
    assert fresh_digest == digest
    host = make_host(WORLD)
    np.testing.assert_array_equal(menu["initial_positions_xyz"], host.uav_positions)
    positions = np.asarray(menu["positions_xyz"])
    np.testing.assert_array_equal(menu["anchors_xyz"], positions[menu["m_permutation"]])
    assert set(menu["role_types"]) <= {"service", "relay", "above_bs"} and len(menu["roles"]) == 6
    assert menu["role_source"].startswith(("generator:", "flat_result_incumbent"))
    # Same layout as run_gate's relay search; the M assignment is closed_loop_execute's permutation.
    reference = closed_loop_execute(make_host(WORLD), menu["positions_xyz"])
    assert reference["target_permutation"] == menu["m_permutation"]
    tampered = dict(menu, m_permutation=[0, 0, 1, 2, 3, 4])
    with pytest.raises(MenuError):
        check_menu(tampered, WORLD, 5000)
    with pytest.raises(MenuError):
        check_menu(menu, WORLD + 1, 5000)
    path = menu_path(menu_dir, WORLD, 5000)
    assert path.exists() and path.parent.name == "5000"


# ------------------------------------------------------------------------------ executor and adapter


def test_planner_slots_reproduce_closed_loop_execute_bitwise(menu_dir):
    provider = MenuProvider(menu_dir, 5000)
    menu = provider(WORLD)
    reference = closed_loop_execute(make_host(WORLD), menu["positions_xyz"])
    for contract, action in (("slot", np.asarray(menu["m_permutation"])), ("offset", np.zeros((6, 3)))):
        env = make_macro_envs(1, [WORLD], contract, provider)[0]
        env.reset(seed=WORLD)
        series = {key: [] for key in ("contract_reward", "coverage_backhauled", "frontend_capacity_with_path_mbps")}

        def hook(contract_values, snapshot):
            for key in series:
                series[key].append(float(contract_values[key]))

        done, macro_steps = False, 0
        while not done:
            _obs, _reward, done, _trunc, info = env.step(action, on_host_step=hook)
            macro_steps += 1
        assert macro_steps == MACRO_HORIZON == 50
        for key, values in series.items():
            assert values == reference["series"][key], (contract, key)
        np.testing.assert_array_equal(env.host.uav_positions, reference["final_positions_xyz"])
        assert info["episode_counters"]["target_changes"] == 0


def test_goto_actions_match_the_planner_rule():
    rng = np.random.default_rng(0)
    positions = rng.uniform(0, 5000, (6, 3))
    targets = positions.copy()
    targets[0] += [10.0, 0.0, 0.0]          # inside one stride: exact landing
    targets[1] += [3000.0, 400.0, 20.0]     # far: unit direction
    actions = goto_actions(positions, targets, 30.0)
    np.testing.assert_allclose(actions[0], [10.0 / 30.0, 0.0, 0.0])
    assert math.isclose(np.linalg.norm(actions[1]), 1.0, rel_tol=1e-12)
    np.testing.assert_array_equal(actions[2:], 0.0)


def test_macro_adapter_widths_rewards_and_readers(menu_dir):
    provider = MenuProvider(menu_dir, 5000)
    for contract, obs_dim, state_dim in (("target", OBS_DIM, STATE_DIM),
                                         ("slot", OBS_DIM + MENU_WIDTH, STATE_DIM + MENU_WIDTH),
                                         ("offset", OBS_DIM, STATE_DIM)):
        env = make_macro_envs(1, [WORLD], contract, provider)[0]
        assert (env.obs_dim, env.state_dim) == (obs_dim, state_dim)
        assert env.action_space_type == ("discrete" if contract == "slot" else "continuous")
        obs, info = env.reset(seed=WORLD)
        assert obs.shape == (6, obs_dim) and info["state"].shape == (state_dim,)
        base_obs, base_info = env.base.reset(seed=WORLD)
        env.reset(seed=WORLD)
        np.testing.assert_array_equal(obs[:, :OBS_DIM], base_obs)
        np.testing.assert_array_equal(info["state"][:STATE_DIM], base_info["state"])
        if contract == "slot":
            block = info["state"][STATE_DIM:]
            np.testing.assert_array_equal(obs[3, OBS_DIM:], block)
            rows = block.reshape(6, 6)
            np.testing.assert_allclose(rows[:, 3:].sum(axis=1), 1.0)
    # Reward: the mean of the ten per-step scalars; readers fed at every host step.
    env = make_macro_envs(1, [WORLD], "slot", provider)[0]
    twin = make_envs(1, [WORLD])[0]
    env.reset(seed=WORLD)
    twin.reset(seed=WORLD)
    tracker = runner.WorldTracker(env, WORLD)
    slots = np.zeros(6, dtype=np.int64)
    _obs, reward, done, _trunc, info = env.step(slots, on_host_step=tracker.update)
    targets = np.repeat(np.asarray(provider(WORLD)["positions_xyz"])[:1], 6, axis=0)
    scalars = []
    for _ in range(10):
        _o, scalar, _t, _tr, _i = twin.step(goto_actions(twin.host.uav_positions.copy(), targets, 30.0))
        scalars.append(scalar)
    assert reward == pytest.approx(np.mean(scalars), abs=1e-15) and not done
    assert tracker.steps == 10 and info["host_steps"] == 10
    assert env.counters.values["slot_conflicts"] == 5
    env.step(np.arange(6), on_host_step=tracker.update)
    assert env.counters.values["slot_switches"] == 5
    with pytest.raises(ContractError):
        env.step(np.full(6, 6))
    with pytest.raises(ContractError):
        env.step(np.zeros((6, 3)))


def test_decoders_are_bounded():
    raw = np.array([[-50.0, 50.0, 0.0], [0.0, 0.0, 50.0], [3.0, -3.0, -3.0]])
    target = decode_target(raw, 5000.0)
    assert np.all(target[:, :2] >= 0) and np.all(target[:, :2] <= 5000)
    assert np.all(target[:, 2] >= 50) and np.all(target[:, 2] <= 150)
    np.testing.assert_allclose(decode_target(np.zeros((1, 3)), 5000.0), [[2500.0, 2500.0, 100.0]])
    np.testing.assert_allclose(decode_target(np.array([[-1.0, 1.0, 0.0]]), 5000.0, squash="none"),
                               [[0.0, 5000.0, 100.0]])
    for squash, sample in (("tanh", np.random.default_rng(1).normal(0, 3, (500, 3))),
                           ("none", np.random.default_rng(1).uniform(-1, 1, (500, 3)))):
        offset = decode_offset(sample, squash)
        assert np.all(np.linalg.norm(offset[:, :2], axis=1) <= 300.0 + 1e-9)
        assert np.all(np.abs(offset[:, 2]) <= 50.0 + 1e-9)
    np.testing.assert_array_equal(decode_offset(np.zeros((2, 3))), 0.0)
    with pytest.raises(ContractError):
        decode_target(np.array([[1.5, 0.0, 0.0]]), 5000.0, squash="none")


def test_macro_training_worlds_are_a_shared_720_set_outside_panels():
    worlds = {macro_training_world_seed(lane, episode) for lane in range(16) for episode in range(45)}
    assert len(worlds) == 720 and not worlds & PANEL_WORLD_SET
    assert macro_training_world_seed(0, 0) == 300000 and macro_training_world_seed(15, 44) == 740015
    with pytest.raises(ValueError):
        macro_training_world_seed(100, 0)


# ------------------------------------------------------------------------------ floors


def test_floors_run_full_episodes_with_counters(menu_dir):
    provider = MenuProvider(menu_dir, 5000)
    rows = {floor: MR.run_floor_world(floor, WORLD, 5000, provider) for floor in MR.FLOORS}
    for floor, row in rows.items():
        assert row["steps"] == 500 and row["macro_counters"]["team_decisions"] == 50, floor
        for key in runner.READER_KEYS:
            assert key in row
    assert rows["planner-slots"]["macro_counters"]["slot_conflicts"] == 0
    assert rows["planner-slots"]["macro_counters"]["slot_switches"] == 0
    assert rows["sticky-random-slot"]["macro_counters"]["slot_switches"] == 0
    assert rows["random-slot"]["macro_counters"]["slot_switches"] > 0
    assert rows["nearest-unclaimed-slot"]["macro_counters"]["slot_conflicts"] == 0
    assert rows["random-target"]["macro_counters"]["target_change_rate"] == 1.0
    held = MR.run_floor_world("nearest-unclaimed-slot", WORLD, 5000, provider, "first_macro_step")
    assert held["macro_counters"]["slot_switches"] == 0
    # Permutation floors: conflict-free, held for the episode, no target changes.
    for floor in MR.PERMUTATION_FLOORS:
        counters = rows[floor]["macro_counters"]
        assert counters["slot_conflicts"] == 0 and counters["slot_switches"] == 0, floor
        assert counters["target_changes"] == 0 and counters["slot_conflicts_per_team_decision"] == 0.0, floor
        assert sorted(rows[floor]["held_slots"]) == list(range(6)), floor
    assert rows["identity-permutation-slots"]["held_slots"] == list(range(6))
    permutation = rows["held-random-permutation-slots"]["held_slots"]
    assert permutation == np.random.default_rng([WORLD, 2]).permutation(6).tolist()
    again = MR.run_floor_world("held-random-permutation-slots", WORLD, 5000, provider)
    assert again["held_slots"] == permutation
    assert again["coverage_backhauled_mean_all"] == rows["held-random-permutation-slots"]["coverage_backhauled_mean_all"]
    other = MR.run_floor_world("held-random-permutation-slots", WORLD + 1, 5000, provider)["held_slots"]
    assert other == np.random.default_rng([WORLD + 1, 2]).permutation(6).tolist()
    assert "held_slots" not in rows["planner-slots"]
    # The [world, 1] stream of the random floors is unchanged by the [world, 2] permutation stream.
    sticky = MR.FloorPolicy("sticky-random-slot", make_macro_envs(1, [WORLD], "slot", provider)[0], WORLD)
    sticky.env.reset(seed=WORLD)
    sticky.step()
    np.testing.assert_array_equal(sticky.held, np.random.default_rng([WORLD, 1]).integers(0, 6, 6))
    sticky.env.close()
    reference = closed_loop_execute(make_host(WORLD), provider(WORLD)["positions_xyz"])
    assert rows["planner-slots"]["coverage_backhauled_mean_all"] == reference["coverage_backhauled_mean_all"]
    assert rows["planner-slots"]["r_mean_all"] == reference["contract_reward_mean_all"]


def test_floor_cli_smoke_refuses_panels_and_skips_admission(tmp_path, monkeypatch, menu_dir):
    monkeypatch.setattr(runner, "require_admission",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("admission called")))
    temp_out = runner.ROOT / "temp" / "never-created-by-this-test"
    outside = runner.ROOT / "docs" / "never-created-by-this-test"
    refused = (
        ["--worlds", "1000", "--out", str(temp_out), "--menu-dir", str(menu_dir)],   # panel world
        ["--worlds", str(WORLD), "--out", str(outside), "--menu-dir", str(menu_dir)],  # out outside temp/
        ["--worlds", str(WORLD), "--out", str(temp_out)],  # default menu dir is under runs/
        ["--worlds", str(WORLD), "--out", str(temp_out), "--menu-dir", str(menu_dir), "--arm", "H"],
    )
    for extra in refused:
        with pytest.raises(SystemExit):
            runner.main(["--floor", "planner-slots", "--launch-sha", "s", "--area-size", "5000",
                         "--smoke-no-admission", *extra])
        assert not temp_out.exists() and not outside.exists()
    out = Path(str(tmp_path)).resolve()
    if (runner.ROOT / "temp").resolve() not in out.parents:
        pytest.skip("pytest basetemp outside this checkout's temp/")
    code = runner.main(["--floor", "random-slot", "--worlds", str(WORLD), "--launch-sha", "s", "--out",
                        str(out / "floor"), "--area-size", "5000", "--smoke-no-admission",
                        "--menu-dir", str(menu_dir)])
    summary = json.loads((out / "floor" / "summary.json").read_text())
    assert code == 0 and summary["status"] == "complete" and summary["training_fits_performed"] == 0
    assert summary["per_world"][0]["steps"] == 500 and summary["macro_counters"]["episodes"] == 1
    for floor in MR.PERMUTATION_FLOORS:
        code = runner.main(["--floor", floor, "--worlds", f"{WORLD}-{WORLD + 1}", "--launch-sha", "s", "--out",
                            str(out / floor), "--area-size", "5000", "--smoke-no-admission",
                            "--menu-dir", str(menu_dir)])
        summary = json.loads((out / floor / "summary.json").read_text())
        assert code == 0 and summary["status"] == "complete" and summary["contract"] == "slot", floor
        assert summary["macro_counters"]["episodes"] == 2 and summary["macro_counters"]["team_decisions"] == 100
        assert summary["macro_counters"]["slot_conflicts"] == 0 and summary["macro_counters"]["slot_switches"] == 0
        assert summary["macro_counters"]["target_changes"] == 0
        assert all(sorted(w["held_slots"]) == list(range(6)) for w in summary["per_world"])
        assert ("[world, 2]" in summary["rng"]) == (floor == "held-random-permutation-slots")


# ------------------------------------------------------------------------------ fits


@pytest.mark.parametrize("contract, arm", [("slot", "H"), ("slot", "SET"), ("target", "H"),
                                           ("target", "SET"), ("offset", "H")])
def test_tiny_macro_fit_updates_and_evaluates(tmp_path, menu_dir, contract, arm):
    out = tmp_path / f"{contract}_{arm}"
    code = MR.run_macro_fit(out, arm, SEEDS[arm][0], "technical", {"sha": "technical"}, tiny_spec(contract),
                            menu_dir)
    assert code == 0, (out / "error.txt").read_text() if (out / "error.txt").exists() else ""
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and result["contract"] == contract
    assert result["counts"] == {"training_team_steps": 1000, "training_macro_steps": 100,
                                "stored_team_steps": 100, "training_episodes": 2, "updates": 1,
                                "evaluation_team_steps": 2000, "evaluation_macro_steps": 200,
                                "evaluation_episodes": 4}
    config = json.loads((out / "config.json").read_text())["config"]
    assert config["k"] == 1 and config["rollout_length"] == 50 and config["macro_contract"] == contract
    for key, value in ARGS_HEAD_DEFAULTS.items():
        assert config[key] == value
    assert config["action_space_type"] == ("discrete" if contract == "slot" else "continuous")
    rows = [json.loads(line) for line in (out / "training.jsonl").read_text().splitlines()]
    row = rows[0]
    assert row["world_seeds"] == [300000, 300001]
    assert row["macro_counters"]["team_decisions"] == 100 and row["macro_counters"]["episodes"] == 2
    if arm == "H":
        labels = row["labels"]
        assert labels["label_team_decisions"] == 100 and sum(labels["agent_distinct_labels_histogram"]) == 100
        assert sum(labels["agent_label_counts"]) == 600 and sum(labels["team_label_counts"]) == 100
        assert labels["team_label_episodes"] == 2
        assert 1.0 <= labels["agent_distinct_labels_per_team_decision_mean"] <= 6.0
        assert 0.0 <= labels["agent_label_entropy_bits_per_team_decision_mean"] <= math.log2(6) + 1e-12
        assert set(result["label_reader_definitions"]) >= set(labels)
        d2 = row["d2_metrics"]
        assert d2["team_decisions"] == d2["decision_steps"] == d2["steps"] == 100
        assert d2["sampled_total"] == 600
        assert d2["cause_counts"] == {"reset": 2, "team_gap": 0, "team_cap": 98, "gap": 0, "cap": 0}
        for name in ("coordinator", "team_discriminator", "individual_discriminator",
                     "coordinator.state_embedding", "team_discriminator.state_encoder"):
            assert result["parameter_motion"][name]["delta_l2"] > 0, name
    else:
        assert "labels" not in row and result["label_reader_definitions"] is None
        assert result["parameter_motion"]["discoverer_actor.base"]["delta_l2"] > 0
        assert result["optimizer_calls"]["coordinator"] == 0
    panels = {p["file"]: p for p in result["panels"]}
    assert sorted(panels) == ["panel_00_dev_deterministic.json", "panel_01_dev_deterministic.json",
                              "panel_01_holdout_deterministic.json", "panel_01_holdout_sampled.json"]
    for name in panels:
        panel = json.loads((out / name).read_text())
        world = panel["per_world"][0]
        assert world["steps"] == 500 and panel["macro_steps"] == 50 and panel["steps"] == 500
        assert world["macro_counters"]["team_decisions"] == 50
        for key in runner.READER_KEYS:
            assert key in world
        if arm == "H":
            labels = panel["labels"]
            assert labels["d2_team_causes"] == {"reset": 1, "team_cap": 49, "other": 0}
            assert labels["label_team_decisions"] == 50 and sum(labels["agent_distinct_labels_histogram"]) == 50
            assert 1.0 <= labels["agent_distinct_labels_per_team_decision_mean"] <= 6.0
            assert 0.0 <= labels["agent_label_entropy_bits_per_team_decision_mean"] <= math.log2(6) + 1e-12
            assert labels["team_label_episodes"] == 1
            assert 1.0 <= labels["team_distinct_labels_per_episode_mean"] <= 6.0
            assert labels["team_label_entropy_bits_per_episode_mean"] == pytest.approx(
                labels["team_label_entropy_bits"])  # one world = one episode
        else:
            assert "labels" not in panel
    table = json.loads((out / "matching_table.json").read_text())
    assert table["team_decisions_per_rollout_H"] == 100 and table["action_contract"]["contract"] == contract
    if contract == "target":  # free destinations: no menu is read
        assert result["menus"]["worlds"] == {}
    else:
        assert set(result["menus"]["worlds"]) == {"300000", "300001", "310000", "310001", "9113", "9114"}
        assert all(len(r["sha256"]) == 64 for r in result["menus"]["worlds"].values())
    from experiments.candidates.coupled_host_joint_skills_stage1.macro_models import build_macro_agent

    state = torch.load(out / result["checkpoints"][-1]["path"], weights_only=False)
    reader = build_macro_agent(make_macro_config(arm, make_macro_envs(1, [WORLD], contract, MenuProvider(
        menu_dir, 5000)), SEEDS[arm][0], tiny_spec(contract)), str(tmp_path / "reader"))
    for name, module in runner.model_modules(reader).items():
        module.load_state_dict(state["modules"][name], strict=True)


def test_bounded_head_target_fit_and_macro_probe(tmp_path, menu_dir):
    spec = tiny_spec("target", continuous_action_distribution="tanh_gaussian", continuous_logstd_init=-1.0,
                     continuous_logstd_min=-5.0, continuous_logstd_max=0.0)
    out = tmp_path / "probe"
    assert MR.run_macro_fit(out, "SET", SEEDS["SET"][0], "t", {"sha": "t"}, spec, menu_dir, probe=True) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["probe"] and result["panels"] == [] and not list(out.glob("panel_*.json"))
    probe = json.loads((out / "timing_probe.json").read_text())
    for key in ("env", "policy", "store", "update"):
        assert probe["ms_per_macro_step"][key] > 0
    assert probe["ms_per_host_step"]["env"] > 0 and probe["host_steps"] == 1000 and probe["macro_steps"] == 100
    assert probe["projection"]["fit_cpu_seconds"] > 0
    table = json.loads((out / "matching_table.json").read_text())
    assert table["action_contract"]["squash"] == "none"
    assert table["action_contract"]["action_head"]["continuous_action_distribution"] == "tanh_gaussian"


def test_macro_spec_guards_and_cli_dispatch(tmp_path, monkeypatch):
    assert is_declared_macro_spec(MacroFitSpec(contract="slot"))
    assert not is_declared_macro_spec(MacroFitSpec(contract="slot", area_size=6000))
    assert not is_declared_fit_spec(MacroFitSpec(contract="slot"))
    with pytest.raises(ValueError, match="panel"):
        MR.check_macro_spec_worlds(tiny_spec("slot", dev_worlds=(1000,)))
    MR.check_macro_spec_worlds(MacroFitSpec(contract="target"))
    seen = {}
    monkeypatch.setattr(runner, "require_admission", lambda *a, **k: {"sha": "abc"})
    monkeypatch.setattr(MR, "run_macro_fit", lambda out, arm, seed, sha, admission, spec, menu_dir, probe=False:
                        seen.update(arm=arm, spec=spec, probe=probe, menu_dir=menu_dir) or 0)
    assert runner.main(["--arm", "H", "--seed", str(SEEDS["H"][0]), "--launch-sha", "abc", "--out",
                        str(tmp_path / "x"), "--area-size", "5000", "--contract", "slot", "--probe",
                        "--continuous-action-distribution", "tanh_gaussian"]) == 0
    assert seen["spec"] == MacroFitSpec(contract="slot", continuous_action_distribution="tanh_gaussian")
    assert seen["probe"] and seen["arm"] == "H"
    # Head flags in --contract step are accepted since b02 SET-V-b (DM edit 2026-09-29); a head that is
    # not the declared b02 spec is a technical per-step spec (covered in test_contract_runner.py).
    for bad in (["--contract", "slot", "--area-size", "6000"],
                ["--contract", "target", "--area-size", "5000", "--smoke-no-admission"]):
        with pytest.raises(SystemExit):
            runner.main(["--arm", "H", "--seed", str(SEEDS["H"][0]), "--launch-sha", "abc", "--out",
                         str(tmp_path / "y"), *bad])


def test_macro_modules_keep_torch_out_of_menus_and_adapter():
    import subprocess
    import sys

    code = ("import sys; import experiments.candidates.coupled_host_joint_skills_stage1.menus; "
            "import experiments.candidates.coupled_host_joint_skills_stage1.adapter; "
            "print('torch' in sys.modules)")
    result = subprocess.run([sys.executable, "-c", code], cwd=runner.ROOT, capture_output=True, text=True,
                            check=True)
    assert result.stdout.strip() == "False"


def test_discrete_slot_log_probs_round_trip_through_the_buffer(tmp_path, menu_dir):
    """The core's Discrete path: stored int64 slots and log-probs recompute exactly (H actor)."""
    from experiments.candidates.coupled_host_joint_skills_stage1.macro_models import build_macro_agent

    spec = tiny_spec("slot")
    torch.manual_seed(0)
    envs = MR._make_envs(spec, [WORLD, WORLD + 1], MenuProvider(menu_dir, 5000))
    agent = build_macro_agent(make_macro_config("H", envs, SEEDS["H"][0], spec), str(tmp_path / "logs"))
    states, observations = runner.reset_all(envs, [WORLD, WORLD + 1])
    steps, dones = np.zeros(2, dtype=int), np.zeros(2, dtype=bool)
    for t in range(3):
        actions, _, data = agent.step(states, observations, steps, dones, deterministic=False,
                                      return_step_data=True, build_infos=False)
        assert actions.shape == (2, 6) and actions.dtype == np.int64
        results = [env.step(actions[lane]) for lane, env in enumerate(envs)]
        next_states = np.stack([r[4]["next_state"] for r in results])
        next_observations = np.stack([r[0] for r in results])
        agent.store_transition_batch(states=states, next_states=next_states.copy(), observations=observations,
                                     next_observations=next_observations.copy(), actions=actions,
                                     rewards=np.array([r[1] for r in results]), dones=np.zeros(2, dtype=bool),
                                     infos_batch=None, rollout_step_idx=t, step_data=data)
        states, observations = next_states, next_observations
        steps += 1
    buffer = agent.rollout_buffer
    obs = torch.as_tensor(buffer.obs[:3].reshape(-1, buffer.obs.shape[-1]))
    hidden = torch.as_tensor(buffer.gru_hidden_states[:3].reshape(-1, buffer.gru_hidden_states.shape[-1]))
    slots = torch.as_tensor(buffer.actions[:3].reshape(-1, 1))
    skills = torch.as_tensor(buffer.agent_skills[:3].reshape(-1))
    with torch.no_grad():
        log_probs, entropy = agent.skill_discoverer.actor.evaluate_actions(
            obs, hidden, slots, torch.ones(obs.shape[0], 1), skills)
    assert buffer.actions.dtype == np.int64
    torch.testing.assert_close(log_probs.reshape(-1), torch.as_tensor(buffer.log_probs[:3].reshape(-1)),
                               rtol=0, atol=1e-6)
    assert float(entropy) == pytest.approx(math.log(6), abs=1e-3)


def test_label_reader_counts_distinct_labels_and_entropy_per_team_decision():
    reader = MR.LabelReader(6, 6, lanes=2)
    reader.update(np.array([[0, 0, 0, 0, 0, 0], [0, 1, 2, 3, 4, 5]]), np.array([2, 3]))
    reader.update(np.array([[0, 0, 0, 1, 1, 1], [5, 5, 5, 5, 5, 4]]), np.array([2, 4]))
    with pytest.raises(ValueError):
        reader.summary()
    reader.end_episodes()
    out = reader.summary(pooled=True)
    assert out["label_team_decisions"] == 4
    assert out["agent_distinct_labels_histogram"] == [1, 2, 0, 0, 0, 1]
    assert out["agent_distinct_labels_per_team_decision_mean"] == pytest.approx((1 + 6 + 2 + 2) / 4)
    h51 = -(5 / 6) * math.log2(5 / 6) - (1 / 6) * math.log2(1 / 6)
    assert out["agent_label_entropy_bits_per_team_decision_mean"] == pytest.approx((0 + math.log2(6) + 1 + h51) / 4)
    assert out["team_label_episodes"] == 2
    assert out["team_distinct_labels_per_episode_mean"] == pytest.approx((1 + 2) / 2)
    assert out["team_label_entropy_bits_per_episode_mean"] == pytest.approx((0 + 1) / 2)
    assert out["agent_label_counts"] == [10, 4, 1, 1, 2, 6] and out["team_label_counts"] == [0, 0, 2, 1, 1, 0]
    assert set(out) <= set(MR.LABEL_READER_DEFINITIONS)
    with pytest.raises(ValueError):
        reader.update(np.full((2, 6), 6), np.zeros(2))
