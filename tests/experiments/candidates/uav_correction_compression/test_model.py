import hashlib
import io

import numpy as np
import pytest
import torch

from experiments.candidates.uav_message_content.b05 import model as retained
from experiments.candidates.uav_correction_compression import model, study


def save_bytes(state):
    stream = io.BytesIO()
    torch.save(state, stream)
    return stream.getvalue()


@pytest.fixture
def bound_inputs(monkeypatch, tmp_path):
    torch.set_num_threads(1)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(87)
        parent, critic = retained.BaseActor(), retained.BaseCritic()
        parent_state = dict(actor=parent.state_dict(), critic=critic.state_dict(), arm="B", master=19451,
                            input_size=171, critic_size=451,
                            inherited_sha256=retained.SOURCE_INHERITED_SHA256)
        content = save_bytes(parent_state)
        digest = hashlib.sha256(content).hexdigest()
        monkeypatch.setattr(retained, "SOURCE_SHA256", digest)
        inputs = dict(parent=dict(sha256=digest, bytes=len(content)), assets=[], horizon=256,
                      worlds=[dict(world=w, scene_seed=1980002000+w, channel_seed=1980007000+w,
                                   motion_seed=1980003000+w) for w in range(32)])
        endpoint_contents = {}
        for master in (19701, 19702, 19703):
            endpoint, endpoint_critic = retained.Actor(), retained.Critic()
            endpoint.base.load_state_dict(parent.state_dict())
            with torch.no_grad():
                endpoint.residual_output.bias.copy_(torch.tensor([.8, -.4, .2]))
                endpoint.residual_output.weight.fill_(.002)
            state = dict(actor=endpoint.state_dict(), critic=endpoint_critic.state_dict(), arm="D",
                         master=master, input_size=186, critic_size=526, inherited_sha256=digest,
                         correction_bound=.10, source_sha="synthetic-source")
            data = save_bytes(state)
            constant64 = [.0123456789123, -.024567891234, .033456789123]
            asset = dict(master=master, endpoint=f"D{master}", constant=f"C{master}",
                         source_sha="synthetic-source", constant_float64=constant64,
                         constant_float32=np.asarray(constant64, dtype=np.float32).astype(float).tolist(),
                         checkpoint=dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
                                         staged_name=f"D{master}.pt"),
                         final_tensor_sha256=dict(
                             base_actor=model.group_hash(state["actor"], "base."),
                             residual_hidden=model.group_hash(state["actor"], "residual_hidden."),
                             residual_output=model.group_hash(state["actor"], "residual_output."),
                             critic_old=model.group_hash(state["critic"], "network."),
                             critic_forecast=model.group_hash(state["critic"], "forecast_projection.")))
            inputs["assets"].append(asset)
            endpoint_contents[asset["endpoint"]] = data
            (tmp_path / asset["checkpoint"]["staged_name"]).write_bytes(data)
        path = tmp_path / "parent.pt"
        path.write_bytes(content)
    monkeypatch.setattr(study, "load_inputs", lambda: inputs)
    return content, inputs, endpoint_contents, path, tmp_path


def test_constant_omits_residual_and_uses_exact_bound_value(bound_inputs, monkeypatch):
    content, inputs, endpoints, _, _ = bound_inputs
    programs = model.load_programs(content, inputs, endpoints)
    x, hidden = torch.randn(1, 5, 186), torch.randn(1, 5, 64)
    for asset in inputs["assets"]:
        actor = programs[asset["constant"]]
        assert not any("residual" in name for name, _ in actor.named_modules())
        assert not any(p.requires_grad for p in actor.parameters())
        actual = actor.components(x, hidden)
        expected = actor.base(x[..., :171], hidden)
        assert all(torch.equal(a, b) for a, b in zip(actual[1:4], (*expected[1:], expected[0])))
        assert torch.equal(actual[4], torch.tensor(asset["constant_float32"]).expand_as(actual[4]))
        assert torch.equal(actual[0], expected[0] + actual[4])
        assert torch.equal(actor.log_std, programs["B40"].log_std)
        changed = x.clone()
        changed[..., 171:] = 100
        assert all(torch.equal(a, b) for a, b in zip(actual, actor.components(changed, hidden)))
    # Construct constant directly while residual constructor is forbidden.
    monkeypatch.setattr(retained, "Actor", lambda: pytest.fail("constant constructed residual"))
    model.ConstantActor(programs["B40"], model.bound_constant(inputs["assets"][0])).components(x, hidden)
    for changes in ({"constant_float32": [0, 0, 0]}, {"constant_float64": [1, 0, 0]}):
        with pytest.raises(ValueError, match="constant"):
            model.bound_constant(dict(inputs["assets"][0], **changes))


@pytest.mark.parametrize("field,value", [("arm", "K"), ("master", 19702), ("input_size", 171),
    ("critic_size", 451), ("inherited_sha256", "wrong"), ("correction_bound", .2),
    ("source_sha", "wrong")])
def test_endpoint_metadata(bound_inputs, field, value):
    content, inputs, endpoints, _, _ = bound_inputs
    parent, _ = retained.load_base(content, inputs["parent"]["sha256"])
    asset = inputs["assets"][0]
    state = torch.load(io.BytesIO(endpoints[asset["endpoint"]]), weights_only=True)
    state[field] = value
    data = save_bytes(state)
    altered = dict(asset, checkpoint=dict(asset["checkpoint"], sha256=hashlib.sha256(data).hexdigest()))
    with pytest.raises(ValueError, match="metadata"):
        model.validate_endpoint(data, altered, parent)


def test_endpoint_digest_tensors_base_and_hashes(bound_inputs):
    content, inputs, endpoints, _, _ = bound_inputs
    parent, _ = retained.load_base(content, inputs["parent"]["sha256"])
    asset = inputs["assets"][0]
    data = endpoints[asset["endpoint"]]
    with pytest.raises(ValueError, match="digest"):
        model.validate_endpoint(data + b"x", asset, parent)
    for mutation, match in ((lambda s: s["actor"].pop("residual_output.bias"), "keys"),
        (lambda s: s["actor"]["base.log_std"].add_(.01), "frozen base"),
        (lambda s: s["actor"]["residual_output.bias"].fill_(float("nan")), "contract"),
        (lambda s: s["critic"].__setitem__("network.0.bias", torch.zeros(128, dtype=torch.float64)), "contract"),
        (lambda s: s["actor"]["residual_output.bias"].add_(.01), "group hashes")):
        state = torch.load(io.BytesIO(data), weights_only=True)
        mutation(state)
        altered = save_bytes(state)
        spec = dict(asset, checkpoint=dict(asset["checkpoint"], sha256=hashlib.sha256(altered).hexdigest()))
        with pytest.raises(ValueError, match=match):
            model.validate_endpoint(altered, spec, parent)


def test_global_rng_frozen_and_timer_identity(bound_inputs):
    content, inputs, endpoints, _, _ = bound_inputs
    before = torch.random.get_rng_state()
    programs = model.load_programs(content, inputs, endpoints)
    assert torch.equal(before, torch.random.get_rng_state())
    x, h = torch.randn(1, 5, 186), torch.zeros(1, 5, 64)
    for arm, actor in programs.items():
        assert not any(p.requires_grad for p in actor.parameters())
        initial = model.state_hashes(actor)
        timer = model.TimedActor(actor)
        if arm == "B40":
            actual, expected = timer(x[..., :171], h), actor(x[..., :171], h)
        else:
            actual, expected = timer.components(x, h), actor.components(x, h)
        assert all(torch.equal(a, b) for a, b in zip(actual, expected))
        assert timer.timing["calls"] == 1
        assert timer.timing["wall_ns"] > 0 and timer.timing["process_cpu_ns"] > 0
        assert model.state_hashes(actor) == initial
