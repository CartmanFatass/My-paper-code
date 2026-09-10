"""B05 binding checks: stub every scientific state constructor and operation."""
import importlib.util
import inspect
import json
from pathlib import Path

import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import environment, learner, policy
from experiments.candidates.vsp_c1.native_hold_value_b01 import critic, study

OBJECT = "VSPC1-NATIVE-HOLD-VALUE-B05"
CARD = "docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B05_SCIENCE_CARD_20260908.md"


def load_cli():
    path = Path(__file__).resolve().parents[5] / "scripts/run_vspc1_native_hold_value_b05.py"
    spec = importlib.util.spec_from_file_location("vspc1_b05_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_binding_and_unchanged_defaults(monkeypatch, tmp_path):
    cli = load_cli()
    monkeypatch.setattr(torch, "set_num_threads", lambda n: None)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: None)
    calls = []
    def run(config, out, start, **identity):
        calls.append((config, out, start, identity))
        return dict(mode="BINDING_STUB", status="COMPLETE")
    monkeypatch.setattr(study, "run_pair", run)
    assert cli.main(["--seed", "8301", "--out", str(tmp_path)]) == 0
    config, out, start, identity = calls[0]
    assert config == study.Config(seed=8301)
    assert out == tmp_path and start == cli.WHOLE_START
    assert identity == dict(object_id=OBJECT, card=CARD, normalize_value=True, second_mlp_width=133, extra_init_seed=830100012)
    assert study.Config().seed == 8101 and study.Config.engineering().seed == 9001
    assert study.checkpoint_identity(study.Config(), "MLP-V", "sha")["object"] == study.OBJECT


@pytest.mark.parametrize("args", [["--seed", "8202"], ["--seed", "8301", "--width", "133"], ["--seed", "8101"], ["--seed", "8102"], ["--seed", "8201"], ["--seed", "9001"],
                                  ["--seed", "8301", "--engineering-fixture"]])
def test_wrong_binding_rejected_before_scientific_state(monkeypatch, tmp_path, args):
    cli = load_cli()
    def forbidden(*args, **kwargs):
        pytest.fail("invalid CLI reached scientific state")
    monkeypatch.setattr(torch, "set_num_threads", forbidden)
    monkeypatch.setattr(study, "run_pair", forbidden)
    monkeypatch.setattr(policy, "templates", forbidden)
    with pytest.raises(SystemExit) as error:
        cli.main(args + ["--out", str(tmp_path)])
    assert error.value.code == 2


def test_full_fixed_schedule_seed_domains_and_publication_with_stubs(monkeypatch, tmp_path):
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
        assert options == dict(second_mlp_width=133, extra_init_seed=830100012)
        pair = (FakeModel(), FakeModel())
        pair[1].count = 34817 if arm == "GATED-V" else 34827
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
        if arm == "H":
            assert moments is None
        else:
            previous = moments_by_arm.setdefault(arm, moments)
            assert previous is moments
            expected_updates = metadata["episode"] // 2 if metadata["phase"] == "train" else 256
            assert moments.updates == expected_updates and moments.n == 512 * expected_updates
        assert horizon == 256
        phase, arm, e = metadata["phase"], metadata["arm"], metadata["episode"]
        assert metadata["pair_master"] == 8301
        if phase == "eval" and arm != "H":
            assert sum(a is actor for a in fits) == 256
        if arm == "H":
            assert actor is value is velocity is duration is None
            assert env is constructors[1][1]
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
    result = study.run_pair(study.Config(seed=8301), tmp_path, 0., clock=lambda: 0.,
                            factory=factory, object_id=OBJECT, card=CARD, normalize_value=True, second_mlp_width=133, extra_init_seed=830100012)
    assert result["status"] == "COMPLETE" and result["publication_readback"] == "complete"
    assert result["object"] == OBJECT and result["card"] == CARD
    assert result["seed"] == 8301 and result["configuration"] == dict(study.asdict(study.Config(seed=8301)), value_normalization="cumulative_population_fp32", entropy_coef=.01, second_mlp_width=133, extra_initialization_seed=830100012)
    assert result["seeds"] == dict(extra_initialization=830100012, initialization=830100011, train_velocity=830100021,
        train_duration=830100022, constructor_reset=830101000, train_reset_start=830101000,
        eval_reset_start=830102000, eval_velocity_start=830103000, eval_duration_start=830104000)
    assert template_seeds == [8301]
    assert len(copies) == 2 and copies[0][0] is copies[1][0]
    assert copies[0][2][0] is not copies[1][2][0]
    assert [seed for seed, env in constructors] == [830101000, 830101000]
    assert len(calls) == 1120 and len(fits) == 512
    assert result["counts"]["team_steps"] == 286720
    assert result["counts"]["optimizer_steps"] == 2048
    assert result["counts"]["eval_episodes"] == 96
    assert result["counts"]["constructor_resets"] == 2
    assert result["primary"]["complete"] and result["primary"]["hover_complete"]
    assert result["primary"]["reading"] == "UP"
    for arm in (*study.ARMS, "H"):
        expected_phases = (("eval", 32),) if arm == "H" else (("train", 512), ("eval", 32))
        for phase, n in expected_phases:
            selected = [c for c in calls if c[:2] == (arm, phase)]
            assert [c[2] for c in selected] == list(range(n))
            for _, _, e, reset, vrng, drng, actor in selected:
                assert reset == 830100000 + (1000 if phase == "train" else 2000) + e
                if arm != "H":
                    assert vrng.seed == 830100000 + (21 if phase == "train" else 3000 + e)
                    assert drng.seed == 830100000 + (22 if phase == "train" else 4000 + e)
    train = {arm: [c for c in calls if c[:2] == (arm, "train")] for arm in study.ARMS}
    for index in (4, 5):
        assert train["GATED-V"][0][index] is train["GATED-V"][-1][index]
        assert train["GATED-V"][0][index] is not train["MLP-V"][0][index]
    assert len(generators) == 132 and len({id(r) for r in generators}) == 132
    assert json.loads((tmp_path / "summary.json").read_text())["primary"] == result["primary"]
    for arm in study.ARMS:
        saved = torch.load(tmp_path / f"final_{arm}.pt", weights_only=True)
        assert saved["object"] == OBJECT and saved["arm"] == arm and saved["seed"] == 8301
        assert saved["configuration"] == result["configuration"]
        assert saved["critic_parameter_count"] == (34817 if arm == "GATED-V" else 34827)
        assert saved["critic_architecture"] == ("136->128->128->1 + 128x5 hold gate" if arm == "GATED-V" else "136->128->133->1")
        for key in ("critic_parameter_count", "critic_architecture"):
            assert result["arms"][arm][key] == saved[key]
        assert saved["launch_sha"] == result["launch_sha"]
    assert study.OBJECT == "VSPC1-NATIVE-HOLD-VALUE-B01"
    assert study.CARD.endswith("VSPC1_NATIVE_HOLD_VALUE_B01_SCIENCE_CARD_20260908.md")

    assert moments_by_arm["GATED-V"] is not moments_by_arm["MLP-V"]
    assert moments_by_arm["GATED-V"].mean * 2 == moments_by_arm["MLP-V"].mean
    for arm in study.ARMS:
        info = result["arms"][arm]
        state = info["value_moments"]
        assert state["n"] == 131072 and state["updates"] == 256
        assert state == info["moments_before_evaluation"] == info["moments_after_evaluation"]
        assert torch.load(tmp_path / f"final_{arm}.pt", weights_only=True)["value_moments"] == state
    assert result["arms"]["MLP-V"]["moments_after_hover"] == result["arms"]["MLP-V"]["value_moments"]
    rows = [json.loads(line) for line in (tmp_path / "rollouts.jsonl").read_text().splitlines()]
    assert len(rows) == 512
    for i, row in enumerate(rows):
        assert row["value_moments"]["updates"] == i % 256 + 1
        assert row["value_moments"]["n"] == 512 * (i % 256 + 1)
        assert row["value_loss_units"] == "normalized_squared"
