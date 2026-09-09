"""Full 768-episode schedule using fake models, environments and updates."""
import inspect
import json

import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import environment, learner, policy
from experiments.candidates.vsp_c1.native_hold_value_b01 import critic, study
from .test_binding import OBJECT, CARD


@pytest.mark.parametrize("failure", [None, "H", "MLP-V"])
def test_final_only_isolated_schedule_and_partial_dependencies(monkeypatch, tmp_path, failure):
    calls, generators, constructors, fits, copies, template_seeds = [], [], [], [], [], []
    moments_by_arm = {}
    class FakeRNG:
        def __init__(self, seed):
            self.seed = seed
    class FakeModel:
        duration = object()
        count = 0
        def parameters(self):
            return iter([torch.zeros(self.count)])
        def state_dict(self):
            return {"stub_only": torch.zeros(1)}
    def templates(seed):
        template_seeds.append(seed)
        return object()
    def models(common, arm, **options):
        assert options == dict(second_mlp_width=133, extra_init_seed=860100012, intact_body=True)
        pair = (FakeModel(), FakeModel())
        pair[1].count = 35467 if arm == "GATED-V" else 34827
        copies.append((common, arm, pair))
        return pair
    def generator(seed):
        rng = FakeRNG(seed)
        generators.append(rng)
        return rng
    def factory(seed):
        env = object()
        constructors.append((seed, env))
        return env
    def forbidden(*args, **kwargs):
        pytest.fail("real scientific constructor reached by binding test")
    def collect(env, actor, value, horizon, reset_seed, velocity, duration, metadata,
                check, counts, emit_episode, emit_diagnostic, limits, **options):
        moments = options.pop("value_moments", None)
        assert options == dict(real=True, diagnostics=False, ratio_grouping="agent_compound")
        arm = metadata["arm"]
        if metadata["phase"] == "eval":
            assert metadata["training_episodes"] == (768 if arm != "H" else 0)
            if arm == failure and metadata["episode"] == 12:
                raise RuntimeError("selected stub panel failure")
        index = 0 if arm == "GATED-V" else 1
        assert env is constructors[2*index + (metadata["phase"] == "eval")][1]
        if arm == "H":
            assert moments is None
        else:
            previous = moments_by_arm.setdefault(arm, moments)
            assert previous is moments
            expected_updates = metadata["episode"] // 2 if metadata["phase"] == "train" else 384
            assert moments.updates == expected_updates and moments.n == 512 * expected_updates
        assert horizon == 256
        phase, arm, e = metadata["phase"], metadata["arm"], metadata["episode"]
        assert metadata["pair_master"] == 8601
        if phase == "eval" and arm != "H":
            assert sum(a is actor for a in fits) == 384
        if arm == "H":
            assert actor is value is velocity is duration is None
            assert env is constructors[3][1]
        else:
            assert isinstance(actor, FakeModel) and isinstance(value, FakeModel)
        calls.append((arm, phase, e, reset_seed, velocity, duration, actor))
        counts["explicit_resets"] += 1
        counts["step_calls"] += horizon
        counts["scientific_uav_calls"] += horizon
        counts["team_steps"] += horizon
        counts[phase + "_team_steps"] += horizon
        counts[phase + "_episodes"] += 1
        counts["completed_episode_steps"] += horizon
        if arm != "H":
            counts["duration_decisions"] += 5
        emit_episode(dict(metadata, reset_seed=reset_seed, steps=horizon,
                          J=.02 if arm == "GATED-V" else 0.))
        return {"critic": torch.zeros(horizon, 136), "reward": torch.full((horizon,), 1. if arm == "GATED-V" else 2.)}
    def update(actor, value, optimizer, episodes, chunk, check, counts, **options):
        moments = options.pop("value_moments")
        assert options == dict(ratio_grouping="agent_compound", entropy_coef=.01)
        targets = learner.returns_to_go(torch.stack([ep["reward"] for ep in episodes]))
        moments.update(targets)
        assert chunk == 32 and len(episodes) == 2
        counts["optimizer_steps"] += 4
        fits.append(actor)
        return [dict(epoch=e, loss=0., value_loss_units="normalized_squared") for e in range(4)]
    monkeypatch.setattr(policy, "templates", templates)
    monkeypatch.setattr(policy, "generator", generator)
    monkeypatch.setattr(policy, "snapshot", lambda *args: {})
    monkeypatch.setattr(policy, "Actor", forbidden)
    monkeypatch.setattr(policy, "Critic", forbidden)
    monkeypatch.setattr(critic, "GatedCritic", forbidden)
    monkeypatch.setattr(critic, "models", models)
    monkeypatch.setattr(critic, "movement", lambda *args: {})
    monkeypatch.setattr(environment, "make_real", forbidden)
    monkeypatch.setattr(environment, "SyntheticAdapter", forbidden)
    monkeypatch.setattr(learner, "collect_episode", collect)
    monkeypatch.setattr(learner, "update", update)
    monkeypatch.setattr(learner, "optimizer_for", lambda *args: object())
    defaults = inspect.signature(study.run_pair).parameters
    assert defaults["object_id"].default == study.OBJECT
    assert defaults["card"].default == study.CARD
    result = study.run_pair(study.Config(seed=8601, train_episodes=768), tmp_path, 0., clock=lambda: 0.,
                            factory=factory, object_id=OBJECT, card=CARD, normalize_value=True, second_mlp_width=133, extra_init_seed=860100012, separate_eval=True, intact_body=True)
    if failure:
        assert result["status"] == ("PRIMARY_COMPLETE_WITH_LIMITS" if failure == "H" else "INCOMPLETE")
        assert result["primary"]["complete"] == (failure == "H")
        assert not result["primary"]["hover_complete"]
        assert result["counts"]["optimizer_steps"] == 3072
        assert result["counts"]["constructors"] == 4
        assert result["counts"]["eval_episodes"] == (76 if failure == "H" else 44)
        assert result["publication_readback"] == "complete"
        return
    assert result["evaluation_endpoints"] == [768] and "change" not in result["primary"]
    assert result["status"] == "COMPLETE" and result["publication_readback"] == "complete"
    assert result["object"] == OBJECT and result["card"] == CARD
    assert result["seed"] == 8601 and result["configuration"] == dict(study.asdict(study.Config(seed=8601, train_episodes=768)), value_normalization="cumulative_population_fp32", entropy_coef=.01, second_mlp_width=133, extra_initialization_seed=860100012, intact_body=True)
    assert result["seeds"] == dict(extra_initialization=860100012, initialization=860100011, train_velocity=860100021,
        train_duration=860100022, constructor_reset=860101000, train_reset_start=860101000,
        evaluation_constructor_reset=860102000, eval_reset_start=860102000, eval_velocity_start=860103000, eval_duration_start=860104000)
    assert template_seeds == [8601]
    assert len(copies) == 2 and copies[0][0] is copies[1][0]
    assert copies[0][2][0] is not copies[1][2][0]
    assert [seed for seed, env in constructors] == [860101000, 860102000, 860101000, 860102000]
    assert len(calls) == 1632 and len(fits) == 768
    assert result["counts"]["team_steps"] == 417792
    assert result["counts"]["optimizer_steps"] == 3072
    assert result["counts"]["eval_episodes"] == 96
    assert result["counts"]["constructor_resets"] == 4
    assert result["counts"]["train_team_steps"] == 393216
    assert result["counts"]["eval_team_steps"] == 24576
    assert result["counts"]["rollouts"] == 768
    assert result["cost_projection"] == {
        "GATED-V": "init + 196608*c_env_actor + 1536*c_update + 8192*c_eval + publication; gate increment unmeasured + 384*c_moment_merge(512); normalization overhead unmeasured",
        "MLP-V": "196608*c_env_actor + 1536*c_update + 16384*c_eval + pair publication/readback/exit + 384*c_moment_merge(512); normalization overhead unmeasured"}
    expected_order = [(arm, phase, e) for arm in (*study.ARMS, "H")
                      for phase, n in ((("eval", 32),) if arm == "H" else (("train", 768), ("eval", 32)))
                      for e in range(n)]
    assert [(arm, phase, e) for arm, phase, e, *_ in calls] == expected_order
    assert result["primary"]["complete"] and result["primary"]["hover_complete"]
    assert result["primary"]["reading"] == "UP"
    for arm in (*study.ARMS, "H"):
        expected_phases = (("eval", 32),) if arm == "H" else (("train", 768), ("eval", 32))
        for phase, n in expected_phases:
            selected = [c for c in calls if c[:2] == (arm, phase)]
            assert [c[2] for c in selected] == list(range(n))
            for _, _, e, reset, vrng, drng, actor in selected:
                assert reset == 860100000 + (1000 if phase == "train" else 2000) + e
                if arm != "H":
                    assert vrng.seed == 860100000 + (21 if phase == "train" else 3000 + e)
                    assert drng.seed == 860100000 + (22 if phase == "train" else 4000 + e)
    train = {arm: [c for c in calls if c[:2] == (arm, "train")] for arm in study.ARMS}
    for index in (4, 5):
        assert train["GATED-V"][0][index] is train["GATED-V"][-1][index]
        assert train["GATED-V"][0][index] is not train["MLP-V"][0][index]
    assert len(generators) == 132 and len({id(r) for r in generators}) == 132
    assert json.loads((tmp_path / "summary.json").read_text())["primary"] == result["primary"]
    for arm in study.ARMS:
        saved = torch.load(tmp_path / f"final_{arm}.pt", weights_only=True)
        assert saved["object"] == OBJECT and saved["arm"] == arm and saved["seed"] == 8601
        assert saved["configuration"] == result["configuration"]
        assert saved["training_episodes"] == 768
        assert result["arms"][arm]["training_counts"]["eval_episodes"] == 0
        assert saved["critic_parameter_count"] == (35467 if arm == "GATED-V" else 34827)
        assert saved["critic_architecture"] == ("136->128->133->1 + 128x5 hold gate" if arm == "GATED-V" else "136->128->133->1")
        for key in ("critic_parameter_count", "critic_architecture"):
            assert result["arms"][arm][key] == saved[key]
        assert saved["launch_sha"] == result["launch_sha"]
    assert study.OBJECT == "VSPC1-NATIVE-HOLD-VALUE-B01"
    assert study.CARD.endswith("VSPC1_NATIVE_HOLD_VALUE_B01_SCIENCE_CARD_20260908.md")

    assert moments_by_arm["GATED-V"] is not moments_by_arm["MLP-V"]
    assert moments_by_arm["GATED-V"].mean * 2 == moments_by_arm["MLP-V"].mean
    for arm in study.ARMS:
        info = result["arms"][arm]
        assert info["training_counts"]["optimizer_steps"] == 1536
        assert info["training_counts"]["rollouts"] == 384
        assert info["training_counts"]["train_team_steps"] == 196608
        state = info["value_moments"]
        assert state["n"] == 196608 and state["updates"] == 384
        assert state == info["moments_before_evaluation"] == info["moments_after_evaluation"]
        assert torch.load(tmp_path / f"final_{arm}.pt", weights_only=True)["value_moments"] == state
    assert result["arms"]["MLP-V"]["moments_after_hover"] == result["arms"]["MLP-V"]["value_moments"]
    rows = [json.loads(line) for line in (tmp_path / "rollouts.jsonl").read_text().splitlines()]
    assert len(rows) == 768
    for i, row in enumerate(rows):
        assert row["value_moments"]["updates"] == i % 384 + 1
        assert row["value_moments"]["n"] == 512 * (i % 384 + 1)
        assert row["value_loss_units"] == "normalized_squared"
