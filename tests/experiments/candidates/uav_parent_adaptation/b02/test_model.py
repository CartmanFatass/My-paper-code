from collections import defaultdict
import copy
import hashlib
import io
from pathlib import Path

import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01 import model as cadc
from experiments.candidates.uav_parent_adaptation.b01 import model as b01
from experiments.candidates.uav_parent_adaptation.b01.update import parent_optimizer, update_parent
from experiments.candidates.uav_parent_adaptation.b02 import model
from experiments.candidates.uav_parent_adaptation.b02.protocol import PARENT_SOURCE, masters

SHA = "a" * 40


@pytest.fixture
def parent(tmp_path):
    actor, critic = b01.build_c(29811)
    c = b01.save_checkpoint(tmp_path / "c.pt", actor, critic, lineage=1, stage="C", endpoint="final",
                             master=29811, launch_sha=PARENT_SOURCE)
    actor, critic = b01.build_b(29812, (tmp_path / "c.pt").read_bytes(), c,
                               lineage=1, launch_sha=PARENT_SOURCE)
    # Trained P may have nonzero formerly structural columns. Preserve them all.
    with torch.no_grad():
        actor.encoder.raw.weight[:, b01.SCALAR_ACTOR_COLUMNS] = .123
        actor.encoder.hidden.weight[:, b01.SCALAR_ACTOR_COLUMNS] = .456
        critic.network[0].weight[:, b01.SCALAR_CRITIC_COLUMNS] = .789
        actor.log_std.copy_(torch.tensor([-.4, -.3, -.2]))
    binding = b01.save_checkpoint(tmp_path / "p.pt", actor, critic, lineage=1, stage="B", endpoint="final",
                                   master=29812, launch_sha=PARENT_SOURCE, parent=c)
    return (tmp_path / "p.pt").read_bytes(), binding, actor, critic


@pytest.fixture
def initial(parent, tmp_path):
    content, binding, _, _ = parent
    actor, critic = model.build_u(29813, content, binding, lineage=1, launch_sha=SHA)
    saved = model.save_checkpoint(tmp_path / "u.pt", actor, critic, lineage=1, endpoint="initial",
                                  master=29813, launch_sha=SHA, parent=binding)
    return (tmp_path / "u.pt").read_bytes(), saved, actor, critic


def test_initial_exact_parent_tensors_trainable_and_group_byte_identity(parent, initial):
    _, parent_binding, p_actor, p_critic = parent
    content, binding, actor, critic = initial
    assert type(actor) is cadc.Actor and type(critic) is cadc.Critic
    assert binding["launch_sha"] == SHA and binding["parent_source"] == PARENT_SOURCE
    assert binding["inherited_sha256"] == parent_binding["sha256"]
    assert binding["parent"] == parent_binding
    for old, new in ((p_actor, actor), (p_critic, critic)):
        assert all(torch.equal(tensor, new.state_dict()[key]) for key, tensor in old.state_dict().items())
        assert all(parameter.requires_grad for parameter in new.parameters())
    assert torch.all(actor.encoder.raw.weight[:, b01.SCALAR_ACTOR_COLUMNS] == .123)
    assert torch.all(actor.encoder.hidden.weight[:, b01.SCALAR_ACTOR_COLUMNS] == .456)
    assert torch.all(critic.network[0].weight[:, b01.SCALAR_CRITIC_COLUMNS] == .789)
    state = model.read_checkpoint(content, binding, lineage=1, endpoint="initial", launch_sha=SHA)
    assert state["stage"] == "U"
    snapshots = model.snapshot(actor, critic)
    assert set(snapshots) == {"actor_encoder", "actor_recurrent", "actor_mean", "actor_log_std", "critic"}
    assert sum(value.numel() for key, value in snapshots.items() if key.startswith("actor_")) == 39942
    assert snapshots["critic"].numel() == 74497
    all_keys = []
    for name, value in snapshots.items():
        assert value.ndim == 1 and value.device.type == "cpu" and value.dtype == torch.float32
        item = binding["parameter_groups"][name]
        assert item["sha256"] == hashlib.sha256(value.numpy().tobytes()).hexdigest()
        assert item["shape"] == [value.numel()] and item["parameters"] == value.numel()
        all_keys.extend(item["keys"])
    expected = [group + "." + key for group in ("actor", "critic") for key in state[group]]
    assert len(all_keys) == len(set(all_keys)) and set(all_keys) == set(expected)
    before = snapshots["actor_mean"].clone()
    with torch.no_grad():
        actor.mean.bias.add_(.01)
    assert torch.equal(snapshots["actor_mean"], before)
    assert model.exposure(snapshots, actor, critic)["actor_mean"]["displacement"] > 0


def test_loading_reading_and_evaluation_rng_isolation(parent, initial, monkeypatch):
    torch.manual_seed(97)
    global_before = torch.random.get_rng_state().clone()
    motion = torch.Generator().manual_seed(2981300021)
    motion_before = motion.get_state().clone()
    model.build_u(29813, parent[0], parent[1], lineage=1, launch_sha=SHA)
    model.load_evaluation(initial[0], initial[1], lineage=1, endpoint="initial", launch_sha=SHA)

    def forbidden(*args, **kwargs):
        raise AssertionError("reader constructed a model")

    monkeypatch.setattr(cadc, "build_arm", forbidden)
    monkeypatch.setattr(b01, "_construct", forbidden)
    monkeypatch.setattr(torch.nn.Linear, "__init__", forbidden)
    state = model.read_checkpoint(initial[0], initial[1], lineage=1, endpoint="initial", launch_sha=SHA)
    group_values = model.state_group_snapshot(state)
    assert all(value.numel() == initial[1]["parameter_groups"][name]["parameters"]
               for name, value in group_values.items())
    assert torch.equal(global_before, torch.random.get_rng_state())
    assert torch.equal(motion_before, motion.get_state())
    assert torch.equal(torch.randn(11, generator=motion),
                       torch.randn(11, generator=torch.Generator().manual_seed(2981300021)))


@pytest.mark.parametrize("endpoint", ["initial", "final"])
def test_roundtrip_frozen_evaluation(parent, initial, tmp_path, endpoint):
    content, binding, actor, critic = initial
    if endpoint == "final":
        with torch.no_grad():
            actor.log_std.add_(.05)
            actor.encoder.raw.weight[:, b01.SCALAR_ACTOR_COLUMNS] = .234
        binding = model.save_checkpoint(tmp_path / "final.pt", actor, critic, lineage=1, endpoint="final",
                                        master=29813, launch_sha=SHA, parent=parent[1])
        content = Path(binding["path"]).read_bytes()
    evaluation_actor, evaluation_critic = model.load_evaluation(content, binding, lineage=1,
                                                               endpoint=endpoint, launch_sha=SHA)
    before = model.snapshot(evaluation_actor, evaluation_critic)
    for original, loaded in ((actor, evaluation_actor), (critic, evaluation_critic)):
        assert all(torch.equal(value, loaded.state_dict()[key]) for key, value in original.state_dict().items())
        assert not loaded.training and all(not p.requires_grad for p in loaded.parameters())
    x, h, cx = torch.ones(2, 5, 171) * .1, torch.zeros(1, 5, 64), torch.ones(2, 451) * .1
    assert all(torch.equal(a, b) for a, b in zip(actor(x, h), evaluation_actor(x, h)))
    assert torch.equal(critic(cx), evaluation_critic(cx))
    assert all(torch.equal(value, model.snapshot(evaluation_actor, evaluation_critic)[key])
               for key, value in before.items())


@pytest.mark.parametrize("field,value", [
    ("schema", "wrong"), ("direction", "wrong"), ("lineage", 2), ("lineage", True),
    ("stage", "B"), ("endpoint", "final"), ("master", 29823), ("input_size", 186),
    ("critic_size", 526), ("launch_sha", "b" * 40), ("parent_source", "b" * 40),
    ("sha256", "b" * 64), ("bytes", 2), ("inherited_sha256", "b" * 64),
])
def test_binding_identity_rejected(initial, field, value):
    binding = copy.deepcopy(initial[1])
    binding[field] = value
    with pytest.raises(ValueError):
        model.read_checkpoint(initial[0], binding, lineage=1, endpoint="initial", launch_sha=SHA)


@pytest.mark.parametrize("field,value", [("launch_sha", SHA), ("stage", "C"), ("lineage", 2), ("endpoint", "initial")])
def test_original_parent_metadata_rejected(parent, initial, field, value):
    parent_binding = copy.deepcopy(parent[1])
    parent_binding[field] = value
    with pytest.raises(ValueError):
        model.build_u(29813, parent[0], parent_binding, lineage=1, launch_sha=SHA)
    u_binding = copy.deepcopy(initial[1])
    u_binding["parent"] = parent_binding
    with pytest.raises(ValueError):
        model.read_checkpoint(initial[0], u_binding, lineage=1, endpoint="initial", launch_sha=SHA)


def _serialized(state, binding):
    stream = io.BytesIO()
    torch.save(state, stream)
    content = stream.getvalue()
    binding = copy.deepcopy(binding)
    binding.update(sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))
    return content, binding


@pytest.mark.parametrize("kind", ["shape", "key", "dtype", "nan", "inf", "tensor_hash", "group_hash", "metadata"])
def test_corrupt_tensor_or_group_identity_rejected_even_with_updated_file_digest(initial, kind):
    state = model.read_checkpoint(initial[0], initial[1], lineage=1, endpoint="initial", launch_sha=SHA)
    binding = copy.deepcopy(initial[1])
    if kind == "shape":
        state["actor"]["mean.bias"] = torch.zeros(4)
        binding["tensors"]["actor"] = model.state_tensor_bindings(state["actor"])
    elif kind == "key":
        del state["actor"]["mean.bias"]
    elif kind == "dtype":
        state["actor"]["mean.bias"] = state["actor"]["mean.bias"].double()
    elif kind in ("nan", "inf"):
        state["actor"]["mean.bias"][0] = float(kind)
    elif kind == "tensor_hash":
        binding["tensors"]["actor"]["mean.bias"]["sha256"] = "b" * 64
    elif kind == "group_hash":
        binding["parameter_groups"]["actor_mean"]["sha256"] = "b" * 64
    else:
        state["parent_source"] = SHA
    content, binding = _serialized(state, binding)
    with pytest.raises(ValueError):
        model.read_checkpoint(content, binding, lineage=1, endpoint="initial", launch_sha=SHA)


def test_altered_parent_bytes_and_inappropriate_initial_save_rejected(parent, initial, tmp_path):
    with pytest.raises(ValueError):
        model.build_u(29813, parent[0][:-1] + b"x", parent[1], lineage=1, launch_sha=SHA)
    with pytest.raises(ValueError):
        model.build_u(29823, parent[0], parent[1], lineage=1, launch_sha=SHA)
    with pytest.raises(ValueError):
        model.build_u(29813, parent[0], parent[1], lineage=1, launch_sha=PARENT_SOURCE)
    with torch.no_grad():
        initial[2].mean.bias.add_(.01)
    with pytest.raises(ValueError, match="initial tensor identity"):
        model.save_checkpoint(tmp_path / "wrong.pt", initial[2], initial[3], lineage=1, endpoint="initial",
                              master=29813, launch_sha=SHA, parent=parent[1])
    assert not (tmp_path / "wrong.pt").exists()


@pytest.mark.parametrize("kind", ["wrong_class", "dtype", "nan"])
def test_invalid_save_rejected_before_writing(parent, initial, tmp_path, kind):
    actor, critic = initial[2:]
    if kind == "wrong_class":
        actor = b01.CalibrationActor()
    elif kind == "dtype":
        actor.double()
    else:
        with torch.no_grad():
            critic.network[0].weight[0, 0] = float("nan")
    path = tmp_path / "bad.pt"
    with pytest.raises(ValueError):
        model.save_checkpoint(path, actor, critic, lineage=1, endpoint="final",
                              master=29813, launch_sha=SHA, parent=parent[1])
    assert not path.exists()


def _episodes(actor):
    rng = torch.Generator().manual_seed(108)
    episodes = []
    for episode in range(2):
        x = torch.randn(32, 5, 171, generator=rng) * .1
        h, last = torch.zeros(1, 5, 64), torch.zeros(5, 3)
        hidden, actions, logps, sends = [], [], [], []
        eligible = torch.ones(32, 5, dtype=torch.bool)
        for t in range(32):
            x[t, :, 104:107] = last
            hidden.append(h[0].clone())
            with torch.no_grad():
                mean, recurrent, h = actor(x[t:t + 1], h)
                u, sent = cadc.sample_actions(actor, mean[0], recurrent[0], eligible[t], t, rng, None)
                logp, _ = cadc.action_terms(actor, mean[0], recurrent[0], u, sent, eligible[t])
            actions.append(u)
            logps.append(logp)
            sends.append(sent)
            last = u.tanh()
        episodes.append(dict(obs=x, hidden=torch.stack(hidden), critic=torch.randn(32, 451, generator=rng) * .1,
                             u=torch.stack(actions), sends=torch.stack(sends), eligible=eligible,
                             logp=torch.stack(logps), value=torch.zeros(32),
                             reward=torch.linspace(.05, .25, 32) + episode * .01))
    return episodes


def test_fresh_joint_optimizer_all_groups_and_variance_train(initial):
    _, _, actor, critic = initial
    optimizer = parent_optimizer(actor, critic)
    assert not optimizer.state
    parameters = optimizer.param_groups[0]["params"]
    assert {id(p) for p in parameters} == {id(p) for p in (*actor.parameters(), *critic.parameters())}
    options = optimizer.param_groups[0]
    assert options["lr"] == 3e-4 and options["betas"] == (.9, .999) and options["eps"] == 1e-8
    assert options["weight_decay"] == 0 and not options["amsgrad"] and not options["foreach"] and not options["fused"]
    before = model.snapshot(actor, critic)
    episodes = _episodes(actor)
    counts, records = defaultdict(int), []
    update_parent(actor, critic, optimizer, episodes, counts, lambda: None, records.append)
    movement = model.exposure(before, actor, critic)
    assert all(group["displacement"] > 0 for group in movement.values())
    assert counts["joint_optimizer_steps"] == counts["actual_adam_calls"] == 4
    assert len(records) == 4
    assert all(parameter.grad is not None for parameter in parameters)
    assert all(torch.isfinite(parameter).all() for parameter in parameters)
