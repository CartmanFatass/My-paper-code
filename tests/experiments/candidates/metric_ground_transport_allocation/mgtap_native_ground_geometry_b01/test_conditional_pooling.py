"""One bounded encoder-only fixture. Do not combine with the old full-policy suite."""

import json
import math

import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import (
    COND, DENSE, make_encoder, parameter_count,
)
from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.conditional_pooling import (
    primary, publish_summary, reading,
)


def fixed_rows():
    rows = torch.zeros(16, 108)
    users = rows[:, 3:63].view(16, 20, 3)
    uavs = rows[:, 63:103].view(16, 10, 4)
    users[1, 0] = torch.tensor([0., 0., .4])  # Visible at zero offset.
    for index in (2, 3, 4, 8, 9, 11, 13, 15):
        users[index, :2] = torch.tensor([[1., 0., .6], [-1., 0., .6]])
    for index in (2, 8, 9, 13, 15):
        uavs[index, 0] = torch.tensor([.7, 0., .1, .5])
    uavs[3, 0] = torch.tensor([-.7, 0., .1, .5])
    for index in (5, 6):
        users[index, 0] = torch.tensor([.4, .2, .4])
        uavs[index, 0] = torch.tensor([.3, .1, .1, .4])
    users[6, 1] = users[6, 0]
    users[7, 0] = torch.tensor([.9, -.5, 0.])
    uavs[7, 0] = torch.tensor([.3, .4, .5, 0.])
    users[8, 19] = users[7, 0]
    uavs[8, 9] = uavs[7, 0]
    users[9, :2] = users[9, :2].flip(0)
    uavs[10, 0] = torch.tensor([0., 0., 0., .4])
    uavs[11, :4] = torch.tensor([[.7, 0., .1, .5], [.1, .2, .1, .4],
                                [-.2, .1, .2, .5], [.1, .3, .1, .6]])
    users[12] = torch.tensor([.2, -.1, .5]).expand(20, 3)
    uavs[12, :4] = uavs[11, :4]
    rows[13, 107] = .5
    users[14, 0] = torch.tensor([.1, .1, .26])
    uavs[15, 1] = uavs[15, 0]
    return rows


def scalar_context(rows):
    """Independent scalar oracle for the supplied sparse row maps, no model."""
    contexts = []
    for row in rows.tolist():
        users = [row[i:i + 3] for i in range(3, 63, 3) if row[i + 2] > 0]
        uavs = [row[i:i + 4] for i in range(63, 103, 4) if row[i + 3] > 0]
        eu = [[math.tanh(x) for x in user] + [0.] * 17 for user in users]
        ev = [[math.tanh(v[0]), math.tanh(v[1]), math.tanh(v[3])]
              + [0.] * 17 + [math.tanh(v[2])] for v in uavs]
        query = [sum(v[d] for v in ev) / len(ev) if ev else 0. for d in range(20)]
        scores = [sum(u[d] * query[d] for d in range(20)) / math.sqrt(20) for u in eu]
        masses = [math.exp(score) for score in scores]
        cu = [len(eu) / 20 * sum(m * u[d] for m, u in zip(masses, eu)) / sum(masses)
              if eu else 0. for d in range(20)]
        cv = [sum(v[d] for v in ev) / 10 for d in range(21)]
        contexts.append(cu + cv)
    return torch.tensor(contexts)


def run_fixture(seed, scratch, summary=None):
    summary = {} if summary is None else summary
    counts = {"standalone_encoders": 0, "encoder_forwards": {COND: 0, DENSE: 0},
              "supplied_loss_backwards": {COND: 0, DENSE: 0}, "fixed_rows_per_forward": 16,
              "synthetic_paired_readouts": 0, "scores_per_arm_per_readout": 32,
              "full_actors": 0, "critics": 0, "checkpoint_loads": 0, "environments": 0,
              "trajectories": 0, "training_steps": 0, "evaluation_steps": 0,
              "optimizer_steps": 0, "profiling": 0, "search": 0}
    summary.update({"status": "FAIL", "seed": seed, "counts": counts,
                    "scientific_invocation": False, "mode": "ENCODER_ONLY_ENGINEERING_FIXTURE"})
    raw_state = {"weight": torch.linspace(-.015, .015, 64 * 108).reshape(64, 108),
                 "bias": torch.linspace(-.01, .01, 64)}
    rng_before = torch.random.get_rng_state().clone()
    encoders = {}
    for arm in (COND, DENSE):
        encoders[arm] = make_encoder(arm, 100000 * seed + 12, raw_state)
        counts["standalone_encoders"] += 1
    assert torch.equal(rng_before, torch.random.get_rng_state())
    assert all(parameter_count(encoder) == 9744 for encoder in encoders.values())
    assert all(parameter_count(encoder) - parameter_count(encoder.raw) == 2768
               for encoder in encoders.values())
    assert all(torch.equal(encoder.raw.weight, raw_state["weight"])
               and torch.equal(encoder.raw.bias, raw_state["bias"])
               and torch.count_nonzero(encoder.context.weight) == 0 for encoder in encoders.values())
    assert all(p.device.type == "cpu" and p.dtype == torch.float32
               for encoder in encoders.values() for p in encoder.parameters())
    assert torch.count_nonzero(encoders[DENSE].hidden.bias) == 0
    assert encoders[DENSE].hidden.weight.shape == (16, 108)
    assert encoders[COND].user_map.weight.shape == (20, 3)
    assert encoders[COND].uav_map.weight.shape == (21, 4)
    contexts = {arm: [] for arm in encoders}
    hooks = [encoder.context.register_forward_pre_hook(
        lambda module, inputs, arm=arm: contexts[arm].append(inputs[0].detach().clone()))
        for arm, encoder in encoders.items()]
    rows = fixed_rows()
    raw = rows @ raw_state["weight"].T + raw_state["bias"]
    forwards = counts["encoder_forwards"]
    backward = counts["supplied_loss_backwards"]

    def forward(arm, inputs):
        forwards[arm] += 1
        return encoders[arm](inputs)

    # Forward 1: prescribed zero projection and supplied identical full raw path.
    initial = {arm: forward(arm, rows) for arm in encoders}
    assert torch.equal(initial[COND], initial[DENSE])
    torch.testing.assert_close(initial[COND], raw, atol=2e-6, rtol=2e-6)
    with torch.no_grad():
        cond = encoders[COND]
        cond.user_map.weight.zero_()
        cond.uav_map.weight.zero_()
        for d in range(3):
            cond.user_map.weight[d, d] = 1.
        cond.uav_map.weight[0, 0] = cond.uav_map.weight[1, 1] = 1.
        cond.uav_map.weight[2, 3] = cond.uav_map.weight[20, 2] = 1.
        cond.context.weight[:41] = torch.eye(41)
        encoders[DENSE].context.weight.fill_(.03)
    # Forward 2: nonzero fixture projections expose the actual pooling computation.
    projected = {arm: forward(arm, rows) for arm in encoders}
    expected_context = scalar_context(rows)
    torch.testing.assert_close(contexts[COND][1], expected_context, atol=2e-6, rtol=2e-6)
    expected_output = raw.clone()
    expected_output[:, :41] += expected_context
    torch.testing.assert_close(projected[COND], expected_output, atol=2e-6, rtol=2e-6)
    assert torch.count_nonzero(contexts[COND][1][[0, 7]]) == 0
    assert contexts[COND][1][1, 2] > 0  # Positive SINR distinguishes padding.
    assert contexts[COND][1][2, 0] > 0 > contexts[COND][1][3, 0]
    assert contexts[COND][1][4, 0] == 0  # No UAV => uniform user weights.
    torch.testing.assert_close(contexts[COND][1][6, :20], 2 * contexts[COND][1][5, :20])
    for index in (8, 9, 13):
        torch.testing.assert_close(contexts[COND][1][index], contexts[COND][1][2])
    assert torch.count_nonzero(contexts[COND][1][10, :20]) == 0
    assert contexts[COND][1][10, 22] > 0
    torch.testing.assert_close(contexts[COND][1][15, :20], contexts[COND][1][2, :20])
    torch.testing.assert_close(contexts[COND][1][15, 20:], 2 * contexts[COND][1][2, 20:])
    assert contexts[DENSE][1].shape == (16, 16)
    # Forward 3: keep row geometry fixed, perturb an existing raw-only component.
    shifted = rows.clone()
    shifted[:, 107] += .2
    shaped = {arm: forward(arm, shifted.reshape(4, 4, 108)) for arm in encoders}
    assert all(output.shape == (4, 4, 64) for output in shaped.values())
    torch.testing.assert_close(contexts[COND][2], contexts[COND][1])
    torch.testing.assert_close(shaped[COND].reshape(16, 64) - projected[COND],
                               .2 * raw_state["weight"][:, 107].expand(16, 64),
                               atol=2e-6, rtol=2e-6)
    assert not torch.equal(contexts[DENSE][2], contexts[DENSE][1])
    # Forward 4 + the only backward per arm: supplied tensor loss, no optimizer.
    gradients = {}
    summary["gradient_norms_at_nonzero_fixture_projection"] = gradients
    for arm, encoder in encoders.items():
        inputs = rows.clone().requires_grad_(True)
        output = forward(arm, inputs)
        loss = (output - torch.linspace(-.2, .3, 64)).square().mean()
        loss.backward()
        backward[arm] += 1
        gradients[arm] = {name: (float(parameter.grad.norm())
                                if parameter.grad is not None and torch.isfinite(parameter.grad).all()
                                else None)
                          for name, parameter in encoder.named_parameters()}
        assert all(parameter.grad is not None and torch.isfinite(parameter.grad).all()
                   and parameter.grad.abs().sum() > 0 for parameter in encoder.parameters())
        assert torch.isfinite(inputs.grad).all() and inputs.grad.abs().sum() > 0
    for hook in hooks:
        hook.remove()
    # Four supplied panels only; each has exactly 32 scores per arm before damage.
    readouts = {}
    summary["synthetic_readouts"] = readouts
    for label, delta in (("above", .02), ("boundary", -.01), ("adverse", -.02), ("damaged", .01)):
        scores = [{"arm": arm, "phase": "eval", "episode": episode, "steps": 256,
                   "J": delta if arm == COND else 0.}
                  for arm in (COND, DENSE) for episode in range(32)]
        if label == "damaged":
            scores[31]["episode"] = 0
            scores[30]["J"] = float("nan")
            scores[29]["steps"] = 255
        counts["synthetic_paired_readouts"] += 1
        result = primary(scores)
        readouts[label] = result
        path = publish_summary(scratch / f"{label}.json", result)
        assert json.loads(path.read_text(encoding="utf-8")) == result
    assert readouts["above"]["reading"] == "COND_ABOVE_MEI"
    assert readouts["boundary"]["reading"] == "INSIDE_MEI"
    assert readouts["adverse"]["reading"] == "COND_ADVERSE"
    assert readouts["damaged"]["reading"] == "INCOMPLETE"
    assert readouts["damaged"]["COND_minus_DENSE"]["mean"] is None
    assert len(readouts["damaged"]["J"][DENSE]) == 32
    assert reading(.01, True) == reading(-.01, True) == "INSIDE_MEI"
    assert readouts["above"]["COND_minus_DENSE"]["differences"] == [.02] * 32
    assert readouts["above"]["COND_minus_DENSE"]["conditional_se"] == 0
    # Source-shape arithmetic only: no actor, critic or helper model is allocated.
    complete_learner_count = 9744 + (2 * 3 * 64 * 64 + 6 * 64) + (64 * 3 + 3) + 3
    complete_learner_count += (136 * 128 + 128) + (128 * 128 + 128) + (128 + 1)
    assert complete_learner_count == 69079
    summary.update({
        "status": "PASS", "seed": seed, "scientific_invocation": False,
        "mode": "ENCODER_ONLY_ENGINEERING_FIXTURE", "dtype": "float32", "device": "cpu",
        "parameters_per_arm": {"encoder_measured": 9744, "branch_measured": 2768,
                               "complete_learner_source_arithmetic_only": complete_learner_count},
        "initial_projection_zero": True, "global_torch_rng_preserved_at_construction": True,
        "gradient_norms_at_nonzero_fixture_projection": gradients,
        "nonzero_projection_is_fixture_only": True, "synthetic_readouts": readouts,
    })
    return summary


def test_conditional_pooling_contracts(tmp_path):
    assert run_fixture(8211, tmp_path)["status"] == "PASS"
