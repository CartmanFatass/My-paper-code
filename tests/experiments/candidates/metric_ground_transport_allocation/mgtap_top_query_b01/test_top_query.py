"""One encoder-only TOP contract check; no learner, environment or optimizer."""

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import (
    TOP, DENSE, make_encoder, parameter_count,
)
from experiments.candidates.metric_ground_transport_allocation.mgtap_top_query_b01.pair import (
    primary, publish_summary, reading,
)


def scalar_context(row, mean_query=False):
    """Independent scalar calculation for only the supplied sparse fixture maps."""
    users = [row[i:i + 3] for i in range(3, 63, 3) if row[i + 2] > 0]
    uavs = [row[i:i + 4] for i in range(63, 103, 4) if row[i + 3] > 0]
    eu = [[math.tanh(x) for x in u] + [0.] * 17 for u in users]
    ev = [[math.tanh(v[0]), math.tanh(v[1]), math.tanh(v[3])]
          + [0.] * 17 + [math.tanh(v[2])] for v in uavs]
    q = (ev[0][:20] if ev else [0.] * 20)
    if mean_query and ev:
        q = [sum(v[d] for v in ev) / len(ev) for d in range(20)]
    masses = [math.exp(sum(u[d] * q[d] for d in range(20)) / math.sqrt(20)) for u in eu]
    cu = [len(eu) / 20 * sum(m * u[d] for m, u in zip(masses, eu)) / sum(masses)
          if eu else 0. for d in range(20)]
    return cu + [sum(v[d] for v in ev) / 10 for d in range(21)]


def run_fixture(scratch):
    raw_state = {"weight": torch.linspace(-.015, .015, 64 * 108).reshape(64, 108),
                 "bias": torch.linspace(-.01, .01, 64)}
    rng = torch.random.get_rng_state().clone()
    top, dense = [make_encoder(kind, 822000012, raw_state) for kind in (TOP, DENSE)]
    assert torch.equal(rng, torch.random.get_rng_state())
    assert all(parameter_count(x) == 9744 for x in (top, dense))
    assert all(parameter_count(x) - parameter_count(x.raw) == 2768 for x in (top, dense))
    assert all(torch.count_nonzero(x.context.weight) == 0 for x in (top, dense))
    assert all(p.device.type == "cpu" and p.dtype == torch.float32
               for x in (top, dense) for p in x.parameters())
    rows = torch.zeros(6, 108)
    users = rows[:, 3:63].reshape(6, 20, 3)
    uavs = rows[:, 63:103].reshape(6, 10, 4)
    users[1:5, :2] = torch.tensor([[.8, .1, .7], [-.8, -.1, .6]])
    uavs[2, 0] = torch.tensor([.5, .2, .1, 1.])
    uavs[3, :2] = torch.tensor([[.5, .2, .1, 1.], [-.5, -.2, .2, 1.]])
    uavs[4, :2] = uavs[3, :2].flip(0)  # Clipped SINR ties retain delivered order.
    uavs[5, 0] = uavs[2, 0]
    rows[:, 107] = torch.linspace(0., .5, 6)
    raw = rows @ raw_state["weight"].T + raw_state["bias"]
    initial_top, initial_dense = top(rows), dense(rows)
    assert torch.equal(initial_top, initial_dense)
    torch.testing.assert_close(initial_top, raw, atol=2e-6, rtol=2e-6)
    with torch.no_grad():
        top.user_map.weight.zero_()
        top.uav_map.weight.zero_()
        for d in range(3):
            top.user_map.weight[d, d] = 1.
        top.uav_map.weight[0, 0] = top.uav_map.weight[1, 1] = 1.
        top.uav_map.weight[2, 3] = top.uav_map.weight[20, 2] = 1.
        top.context.weight[:41] = torch.eye(41)
    observed = []
    hook = top.context.register_forward_pre_hook(lambda _m, x: observed.append(x[0].detach().clone()))
    inputs = rows.clone().requires_grad_(True)
    output = top(inputs.reshape(2, 3, 108))
    hook.remove()
    expected = torch.tensor([scalar_context(row) for row in rows.tolist()])
    torch.testing.assert_close(observed[0], expected, atol=2e-6, rtol=2e-6)
    expected_output = raw.clone()
    expected_output[:, :41] += expected
    assert output.shape == (2, 3, 64)
    torch.testing.assert_close(output.reshape(6, 64), expected_output, atol=2e-6, rtol=2e-6)
    assert torch.count_nonzero(observed[0][0]) == 0
    assert torch.count_nonzero(observed[0][5, :20]) == 0
    assert observed[0][5, 40] > 0  # The 21st all-partner component survives.
    torch.testing.assert_close(observed[0][2, :20], observed[0][3, :20])
    torch.testing.assert_close(observed[0][3, 20:], observed[0][4, 20:])
    assert abs(float(observed[0][3, 0] - observed[0][4, 0])) > 1e-4
    mean_context = torch.tensor(scalar_context(rows[3].tolist(), mean_query=True))
    assert abs(float(observed[0][3, 0] - mean_context[0])) > 1e-4
    loss = (output - torch.linspace(-.2, .3, 64)).square().mean()
    loss.backward()
    gradients = {n: float(p.grad.norm()) for n, p in top.named_parameters()}
    assert all(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0
               for p in top.parameters())
    assert torch.isfinite(inputs.grad).all() and inputs.grad.abs().sum() > 0
    readings = {}
    for label, delta in (("above", .02), ("inside", .01), ("adverse", -.02), ("damaged", .02)):
        rows_out = [{"arm": arm, "phase": "eval", "episode": e, "steps": 256,
                     "J": delta if arm == TOP else 0.} for arm in (TOP, DENSE) for e in range(32)]
        if label == "damaged":
            rows_out[31]["episode"] = 0
        result = primary(rows_out)
        path = publish_summary(scratch / (label + ".json"), result)
        assert json.loads(path.read_text(encoding="utf-8")) == result
        readings[label] = result["reading"]
        if label == "damaged":
            assert result["TOP_minus_DENSE"]["mean"] is None
            assert len(result["J"][DENSE]) == 32
    assert readings == {"above": "TOP_ABOVE_MEI", "inside": "INSIDE_MEI",
                        "adverse": "TOP_ADVERSE", "damaged": "INCOMPLETE"}
    assert reading(-.01, True) == "INSIDE_MEI"
    return {"status": "PASS", "scientific_invocation": False,
            "standalone_encoders": 2, "forwards": {TOP: 2, DENSE: 1},
            "supplied_loss_backwards": {TOP: 1, DENSE: 0}, "fixed_rows": 6,
            "full_actors": 0, "critics": 0, "checkpoint_loads": 0, "environments": 0,
            "trajectories": 0, "train_steps": 0, "eval_steps": 0, "optimizer_steps": 0,
            "synthetic_primary_readouts": 4, "gradient_norms": gradients,
            "reading_cases": readings, "global_rng_unchanged_by_construction": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", type=Path, required=True)
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to((ROOT / "temp").resolve())
    assert not scratch.exists()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.set_default_dtype(torch.float32)
    torch.set_default_device("cpu")
    scratch.mkdir(parents=True)
    result = {"status": "FAIL", "scientific_invocation": False}
    try:
        result = run_fixture(scratch)
    finally:
        for name in ("above", "inside", "adverse", "damaged"):
            (scratch / (name + ".json")).unlink(missing_ok=True)
        scratch.rmdir()
        result["scratch_removed"] = not scratch.exists()
        print(json.dumps(result, allow_nan=False))
