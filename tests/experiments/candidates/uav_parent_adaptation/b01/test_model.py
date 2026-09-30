import copy
import hashlib
import io
from pathlib import Path

import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01 import model as cadc
from experiments.candidates.uav_message_content.b06.update import optimizers_for, update_motion
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import recurrent_outputs
from experiments.candidates.uav_parent_adaptation.b01 import model

SHA = "a" * 40


@pytest.fixture
def parents(tmp_path):
    actor, critic = model.build_c(29811)
    initial = model.save_checkpoint(tmp_path / "c_initial.pt", actor, critic, lineage=1,
                                    stage="C", endpoint="initial", master=29811, launch_sha=SHA)
    # Deliberately distinguish the final endpoint from initialization without a fit.
    with torch.no_grad():
        actor.mean.bias.add_(.02)
        critic.network[0].bias.add_(.03)
    c = model.save_checkpoint(tmp_path / "c.pt", actor, critic, lineage=1, stage="C",
                              endpoint="final", master=29811, launch_sha=SHA)
    c_bytes = (tmp_path / "c.pt").read_bytes()
    b_actor, b_critic = model.build_b(29812, c_bytes, c, lineage=1, launch_sha=SHA)
    b = model.save_checkpoint(tmp_path / "b.pt", b_actor, b_critic, lineage=1, stage="B",
                              endpoint="final", master=29812, launch_sha=SHA, parent=c)
    return dict(initial=initial, c=c, c_bytes=c_bytes, c_actor=actor, c_critic=critic,
                b=b, b_bytes=(tmp_path / "b.pt").read_bytes(), b_actor=b_actor, b_critic=b_critic)


def test_exact_structural_zero_and_other_tensor_retention(parents):
    for group, before, after, columns in (
            ("actor", parents["c_actor"], parents["b_actor"], model.SCALAR_ACTOR_COLUMNS),
            ("critic", parents["c_critic"], parents["b_critic"], model.SCALAR_CRITIC_COLUMNS)):
        selected = {"encoder.raw.weight", "encoder.hidden.weight"} if group == "actor" else {"network.0.weight"}
        for key, tensor in before.state_dict().items():
            expected = tensor.clone()
            if key in selected:
                assert torch.count_nonzero(tensor[:, columns]) > 0
                expected[:, columns] = 0
            assert torch.equal(after.state_dict()[key], expected)
    x = torch.randn(3, 5, 171, generator=torch.Generator().manual_seed(1))
    x[..., model.SCALAR_ACTOR_COLUMNS] = 0
    h = torch.zeros(1, 5, 64)
    for old, new in zip(parents["c_actor"](x, h), parents["b_actor"](x, h)):
        assert torch.equal(old, new)
    cx = torch.randn(3, 451, generator=torch.Generator().manual_seed(2))
    cx[..., model.SCALAR_CRITIC_COLUMNS] = 0
    assert torch.equal(parents["c_critic"](cx), parents["b_critic"](cx))


@pytest.mark.parametrize("arm", ["K", "D"])
def test_zero_correction_same_noise_and_bound(parents, arm):
    actor, critic = model.build_adaptation(29813, arm, parents["b_bytes"], parents["b"],
                                         lineage=1, launch_sha=SHA)
    rng = torch.Generator().manual_seed(4)
    x = torch.randn(4, 5, 186, generator=rng)
    h = torch.randn(1, 5, 64, generator=rng)
    mean, recurrent, next_h, base_mean, correction = actor.components(x, h)
    old_mean, old_recurrent, old_h = parents["b_actor"](x[..., :171], h)
    assert torch.equal(mean, old_mean) and torch.equal(base_mean, old_mean)
    assert torch.equal(recurrent, old_recurrent) and torch.equal(next_h, old_h)
    assert torch.count_nonzero(correction) == 0
    eligible = torch.ones(5, dtype=torch.bool)
    a, send = cadc.sample_actions(actor, mean[0], recurrent[0], eligible, 0,
                                 torch.Generator().manual_seed(8), None)
    p, old_send = cadc.sample_actions(parents["b_actor"], old_mean[0], old_recurrent[0],
                                     eligible, 0, torch.Generator().manual_seed(8), None)
    assert torch.equal(a, p) and torch.equal(send, old_send)
    cx = torch.randn(4, 526, generator=rng)
    assert torch.equal(critic(cx), parents["b_critic"](cx[..., :451]))
    assert all(not p.requires_grad for p in actor.base.parameters())
    with torch.no_grad():
        if arm == "K":
            actor.b.copy_(torch.tensor([2., -1., .5]))
        else:
            actor.residual_output.bias.copy_(torch.tensor([2., -1., .5]))
    active, _, _, active_base, correction = actor.components(x, h)
    assert torch.equal(active_base, base_mean)
    assert torch.all(correction.abs() <= .10)
    assert torch.all((active.tanh() - base_mean.tanh()).abs() <= .1000001)
    assert torch.allclose(correction, .10 * torch.tensor([2., -1., .5]).tanh().expand_as(correction))


def test_constructor_rng_isolation_critic_first_and_independent_roots(parents):
    torch.manual_seed(91)
    global_state = torch.random.get_rng_state().clone()
    motion = torch.Generator().manual_seed(2981300021)
    motion_state = motion.get_state().clone()
    roots = [model.build_c(master)[0] for master in (29811, 29821, 29831)]
    expected_c, _ = cadc.build_arm(29811, "RR")
    assert all(torch.equal(t, expected_c.state_dict()[k]) for k, t in roots[0].state_dict().items())
    assert all(not torch.equal(roots[i].mean.weight, roots[j].mean.weight)
               for i, j in ((0, 1), (0, 2), (1, 2)))
    k, kc = model.build_adaptation(29813, "K", parents["b_bytes"], parents["b"], lineage=1, launch_sha=SHA)
    d, dc = model.build_adaptation(29813, "D", parents["b_bytes"], parents["b"], lineage=1, launch_sha=SHA)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(2981300011)
        expected_critic = model.Critic()
        expected_d = model.ResidualActor()
    assert torch.equal(d.residual_hidden.weight, expected_d.residual_hidden.weight)
    assert torch.equal(expected_critic.forecast_projection.weight, dc.forecast_projection.weight)
    for key in kc.state_dict():
        assert torch.equal(kc.state_dict()[key], dc.state_dict()[key])
    for key in k.base.state_dict():
        assert torch.equal(k.base.state_dict()[key], d.base.state_dict()[key])
    assert torch.equal(torch.random.get_rng_state(), global_state)
    assert torch.equal(motion.get_state(), motion_state)
    assert torch.equal(torch.randn(9, generator=motion),
                       torch.randn(9, generator=torch.Generator().manual_seed(2981300021)))
    assert model.snapshot(k, kc)["calibration"].numel() == 3
    assert sum(model.snapshot(d, dc)[key].numel() for key in ("residual_hidden", "residual_output")) == 16259


@pytest.mark.parametrize("field,value", [
    ("lineage", 2), ("lineage", True), ("master", 29821), ("stage", "B"),
    ("endpoint", "initial"), ("launch_sha", "b" * 40), ("direction", "other"),
    ("schema", "other"), ("input_size", 186), ("critic_size", 526),
    ("original_c_source", "b" * 40), ("original_b_source", "b" * 40),
    ("inherited_sha256", "b" * 64), ("sha256", "b" * 64), ("bytes", 1),
])
def test_independent_expected_binding_rejects_wrong_identity(parents, field, value):
    binding = copy.deepcopy(parents["c"])
    binding[field] = value
    with pytest.raises(ValueError):
        model.read_checkpoint(parents["c_bytes"], binding, lineage=1, stage="C", endpoint="final", launch_sha=SHA)


def _serialized(state, binding):
    buffer = io.BytesIO()
    torch.save(state, buffer)
    content = buffer.getvalue()
    binding = copy.deepcopy(binding)
    binding["sha256"] = hashlib.sha256(content).hexdigest()
    binding["bytes"] = len(content)
    return content, binding


@pytest.mark.parametrize("kind", ["key", "shape", "dtype", "nan", "inf", "tensor_hash", "metadata"])
def test_rejects_malformed_tensors_even_with_updated_file_digest(parents, kind):
    state = model.read_checkpoint(parents["c_bytes"], parents["c"], lineage=1, stage="C", endpoint="final", launch_sha=SHA)
    binding = copy.deepcopy(parents["c"])
    if kind == "key":
        del state["actor"]["mean.bias"]
    elif kind == "shape":
        state["actor"]["mean.bias"] = torch.zeros(4)
        binding["tensors"]["actor"] = model.state_tensor_bindings(state["actor"])
    elif kind == "dtype":
        state["actor"]["mean.bias"] = state["actor"]["mean.bias"].double()
    elif kind in ("nan", "inf"):
        state["actor"]["mean.bias"][0] = float(kind)
    elif kind == "tensor_hash":
        binding["tensors"]["actor"]["mean.bias"]["sha256"] = "b" * 64
    else:
        state["master"] = 29821
    content, binding = _serialized(state, binding)
    with pytest.raises(ValueError):
        model.read_checkpoint(content, binding, lineage=1, stage="C", endpoint="final", launch_sha=SHA)


def test_wrong_parent_stage_lineage_source_and_master_rejected(parents, tmp_path):
    for key, value in (("stage", "K"), ("lineage", 2), ("launch_sha", "b" * 40), ("endpoint", "initial")):
        bad = copy.deepcopy(parents["b"])
        bad["parent"][key] = value
        with pytest.raises(ValueError):
            model.build_adaptation(29813, "K", parents["b_bytes"], bad, lineage=1, launch_sha=SHA)
    with pytest.raises(ValueError):
        model.build_b(29822, parents["c_bytes"], parents["c"], lineage=1, launch_sha=SHA)
    with pytest.raises(ValueError):
        model.build_adaptation(29813, "K", parents["c_bytes"], parents["c"], lineage=1, launch_sha=SHA)
    with pytest.raises(ValueError):
        model.save_checkpoint(tmp_path / "bad.pt", parents["b_actor"], parents["b_critic"],
                              lineage=1, stage="B", endpoint="final", master=29812, launch_sha=SHA)
    assert not (tmp_path / "bad.pt").exists()


@pytest.mark.parametrize("stage,endpoint", [("C", "initial"), ("B", "final"), ("K", "final"), ("D", "final")])
def test_evaluation_restores_exact_saved_tensors_and_is_frozen(parents, tmp_path, stage, endpoint):
    if stage == "C":
        binding = parents["initial"]
    elif stage == "B":
        binding = parents["b"]
    else:
        actor, critic = model.build_adaptation(29813, stage, parents["b_bytes"], parents["b"], lineage=1, launch_sha=SHA)
        with torch.no_grad():
            if stage == "K":
                actor.b.fill_(.7)
            else:
                actor.residual_output.bias.fill_(.8)
            critic.forecast_projection.weight.fill_(.001)
            # Prove evaluation never repeats parent structural-zero construction.
            actor.base.encoder.raw.weight[:, model.SCALAR_ACTOR_COLUMNS] = .123
        binding = model.save_checkpoint(tmp_path / (stage + ".pt"), actor, critic, lineage=1, stage=stage,
                                        endpoint=endpoint, master=29813, launch_sha=SHA, parent=parents["b"])
    content = Path(binding["path"]).read_bytes()
    state = model.read_checkpoint(content, binding, lineage=1, stage=stage, endpoint=endpoint, launch_sha=SHA)
    actor, critic = model.load_evaluation(content, binding, lineage=1, stage=stage, endpoint=endpoint, launch_sha=SHA)
    before = model.snapshot(actor, critic)
    for group, module in (("actor", actor), ("critic", critic)):
        assert not module.training
        assert all(not p.requires_grad for p in module.parameters())
        assert all(torch.equal(value, state[group][key]) for key, value in module.state_dict().items())
    width = 171 if stage in ("C", "B") else 186
    x = torch.randn(2, 5, width)
    h = torch.zeros(1, 5, 64)
    actor(x, h)
    critic(torch.randn(2, 451 if width == 171 else 526))
    assert all(torch.equal(value, model.snapshot(actor, critic)[key]) for key, value in before.items())
    assert all(p.grad is None for p in actor.parameters())


def test_reader_validates_without_constructors_or_rng_use(parents, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("checkpoint validation constructed a model")

    monkeypatch.setattr(model, "_construct", forbidden)
    before = torch.random.get_rng_state().clone()
    state = model.read_checkpoint(parents["b_bytes"], parents["b"], lineage=1,
                                  stage="B", endpoint="final", launch_sha=SHA)
    assert state["master"] == 29812
    assert torch.equal(before, torch.random.get_rng_state())


def test_save_rejects_wrong_model_dtype_and_nonfinite_before_writing(parents, tmp_path):
    for kind in ("dtype", "nonfinite", "wrong_arm"):
        actor, critic = model.build_c(29811)
        if kind == "dtype":
            actor.double()
        elif kind == "nonfinite":
            with torch.no_grad():
                actor.mean.bias[0] = float("nan")
        else:
            actor = model.CalibrationActor()
        destination = tmp_path / (kind + ".pt")
        with pytest.raises(ValueError):
            model.save_checkpoint(destination, actor, critic, lineage=1, stage="C",
                                  endpoint="initial", master=29811, launch_sha=SHA)
        assert not destination.exists()


def _episodes(actor):
    rng = torch.Generator().manual_seed(109)
    episodes = []
    for episode in range(2):
        x = torch.randn(32, 5, 186, generator=rng) * .1
        x[..., 171:] = 0
        h, last = torch.zeros(1, 5, 64), torch.zeros(5, 3)
        hidden, pre_tanh, logps = [], [], []
        for t in range(32):
            x[t, :, 104:107] = last
            hidden.append(h[0].clone())
            with torch.no_grad():
                mean, _, h = actor(x[t:t + 1], h)
                u = mean[0] + torch.randn(5, 3, generator=rng) * .2
                logp, _ = model.motion_terms(actor, mean[0], u)
            pre_tanh.append(u)
            logps.append(logp)
            last = u.tanh()
        cx = torch.randn(32, 526, generator=rng) * .1
        cx[..., 451:] = 0
        episodes.append(dict(obs=x, hidden=torch.stack(hidden), critic=cx, u=torch.stack(pre_tanh),
                             logp=torch.stack(logps), value=torch.zeros(32),
                             reward=torch.linspace(.05, .25, 32) + episode * .01))
    return episodes


@pytest.mark.parametrize("arm", ["K", "D"])
def test_inherited_update_moves_correction_and_critic_with_frozen_parent(parents, arm):
    actor, critic = model.build_adaptation(29813, arm, parents["b_bytes"], parents["b"], lineage=1, launch_sha=SHA)
    episodes = _episodes(actor)
    replay, _ = recurrent_outputs(actor, {key: torch.stack([ep[key] for ep in episodes]) for key in ("obs", "hidden")}, 32)
    replay_logp, _ = model.motion_terms(actor, replay, torch.stack([ep["u"] for ep in episodes]))
    assert torch.allclose(replay_logp, torch.stack([ep["logp"] for ep in episodes]), atol=2e-6, rtol=2e-6)
    initial = model.snapshot(actor, critic)
    actor_opt, critic_opt = optimizers_for(actor, critic)
    assert actor_opt.param_groups[0]["lr"] == (3e-3 if arm == "K" else 3e-4)
    counts, records = {}, []
    update_motion(actor, critic, actor_opt, critic_opt, episodes, counts, lambda: None, records.append)
    movement = model.exposure(initial, actor, critic)
    assert movement["base_actor"]["displacement"] == 0
    assert movement["calibration" if arm == "K" else "residual_output"]["displacement"] > 0
    assert movement["critic_old"]["displacement"] > 0
    assert movement["critic_forecast"]["displacement"] == 0
    assert all(p.grad is None for p in actor.base.parameters())
    assert counts["actor_optimizer_steps"] == counts["critic_optimizer_steps"] == 4
    assert len(records) == 4
