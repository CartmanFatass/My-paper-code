"""Non-card conformance fixtures; no seed18 models or A02 result probes."""

import json
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration.tbcfv_a02 import study as a
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import make_conformance_fixture_model


def test_baseline_recurrence_and_unavailable():
    means = [0.1 + index / 20 for index in range(8)]
    curves = [{"update": update, "per_cell": [{"cell": cell, "Y_mean": means[index]}
               for index, cell in enumerate(a.TRAINING_CELLS)]} for update in range(200)]
    actual = a.reconstruct_baseline({"curves": curves})
    expected = torch.tensor(means, dtype=torch.float64) * (1 - 0.95 ** 200)
    torch.testing.assert_close(actual, expected)
    assert a.reconstruct_baseline({"curves": curves[:-1]}) is None


def test_projection_and_undefined_zero_readings():
    model = make_conformance_fixture_model()
    names, parameters = zip(*model.named_parameters())
    values = [torch.ones_like(p) if index % 2 else None for index, p in enumerate(parameters)]
    measured = a.projection(names, values)
    flat = a.vector(values, parameters)
    assert sum(p.numel() for p in parameters) == 26161
    assert sum(v * v for v in measured["groups"].values()) == pytest.approx(float(flat.square().sum()))
    assert set(a.group_name(name) for name in names) == set(a.GROUPS)
    assert measured["tensors"][names[0]]["gradient_state"] == "no_graph"
    zero = torch.zeros(5, dtype=torch.float64)
    reading = a.allocation(zero, zero, zero, 0)
    assert reading["r_A"] is reading["r_P"] is reading["manager_actor_cosine"] is None


def test_real_host_capture_gradients_and_publication(tmp_path):
    torch.set_num_threads(1)
    rng = a.host.SyntheticTestRNG()
    coords = tuple(a.host.EpisodeCoordinate(0, a.TRAINING_CELLS[0], 7, row) for row in range(8))
    model = make_conformance_fixture_model()
    before = {name: value.clone() for name, value in model.state_dict().items()}
    points = []
    observed = a.host.execute_learned_batch(model, a.C1P1, rng, coords, training=True,
        claim_observer=lambda c, s, p: a.capture_inputs(points, c, s, p))
    # Repeat eight non-card graph rows to exercise the exact balanced loss shape;
    # this fixture is not 64 independent episodes or a result probe.
    c = a.measure_gradients(model, list(observed) * 8, torch.zeros(8, dtype=torch.float64), False)
    assert c["derivative_evaluations"] == 3
    assert c["original"]["additivity_pass"]
    assert c["original"]["projections"]["actor"]["tensors"]["common_update_final.weight"]["gradient_state"] == "no_graph"
    assert len(points) == 16
    assert {point["tick"] for point in points} == set(a.TICKS)
    assert {point["public_member_index"] for point in points} == {0, 5}
    assert all(not point["z"].requires_grad for point in points)
    flex = a.host.execute_learned_batch(model, a.FLEX, rng, coords, training=True)
    assert [item.Y for item in observed] == [item.Y for item in flex]
    f = a.measure_gradients(model, list(flex) * 8, torch.full((8,), 0.2, dtype=torch.float64), True)
    assert f["derivative_evaluations"] == 5
    assert f["original"]["additivity_pass"]
    assert f["original"]["projections"]["actor"]["tensors"]["common_update_final.weight"]["gradient_state"] == "nonzero"
    assert f["original"]["projections"]["actor"]["tensors"]["common_update_hidden.weight"]["gradient_state"] == "zero"
    assert f["cells"][0]["Y_std"] == pytest.approx(torch.tensor([v.Y for v in flex], dtype=torch.float64).std(correction=0).item())
    assert all(torch.equal(before[name], value) for name, value in model.state_dict().items())
    assert all(parameter.grad is None for parameter in model.parameters())
    p0 = a.conditional_probabilities(model, points)
    with torch.no_grad():
        model.pointer_first.weight[0, 73] += 0.1
    p1 = a.conditional_probabilities(model, points)
    assert not torch.equal(p0, p1)
    for point in points:
        point["block"] = 19001
    report = a.probability_report({"init": p0, "C1P1-final": p0, "FLEX-final": p1}, points)
    assert report[0]["TV"]["C1P1-final_vs_init"]["max"] == 0
    assert report[0]["TV"]["FLEX-final_vs_init"]["mean"] > 0
    payload = {"fixture": "synthetic16episodes_8derivatives", "measurements": [c, f], "probabilities": report}
    a.write_summary(tmp_path, payload)
    loaded = json.loads((tmp_path / "summary.json").read_text())
    assert loaded == payload
    torch.save({"points": points, "probabilities": p0}, tmp_path / "fixed_inputs.pt")
    restored = torch.load(tmp_path / "fixed_inputs.pt", weights_only=True)
    torch.testing.assert_close(restored["probabilities"], p0)


def test_arm_domain_defaults_and_pairing(monkeypatch):
    seen = []
    monkeypatch.setattr(a.host, "native_semantic_uniform_words", lambda key, rows, binding:
                        seen.append(rows) or tuple(1 for _ in rows))
    rng = object.__new__(a.host.SemanticRNG)
    rng._key, rng._native_binding, rng.block_index = b"fixture", None, 19001
    rows = tuple(a.host._address(19001, arm_only_variable=arm, draw_kind="fixture", draw_index=0)
                 for arm in ("", "FLEX", "renamed"))
    rng.arm_only_domain = None
    rng.uniform_many(rows)
    assert seen[-1] == rows
    rng.arm_only_domain = a.PURPOSE
    rng.uniform_many(rows)
    assert [row["arm_only_variable"] for row in seen[-1]] == ["", a.PURPOSE, a.PURPOSE]
    assert seen[-1][1] == seen[-1][2]
    assert rows[1]["arm_only_variable"] == "FLEX"


def test_missing_baseline_is_explicit():
    model = make_conformance_fixture_model()
    p = next(model.parameters())
    rows = [SimpleNamespace(Y=0.3, plan_scores=(p.sum(),), claim_scores=(p.square().sum(),)) for _ in range(64)]
    measured = a.measure_gradients(model, rows, None, True)
    assert "original" not in measured
    assert measured["original_baseline_available"] is False
    assert measured["zero_baseline"]["additivity_pass"]
    assert measured["derivative_evaluations"] == 3
    assert all(row["baseline"] is None for row in measured["cells"])


def test_partial_derivative_counts(monkeypatch):
    model = make_conformance_fixture_model()
    p = next(model.parameters())
    rows = [SimpleNamespace(Y=0.3, plan_scores=(p.sum(),), claim_scores=(p.square().sum(),)) for _ in range(64)]
    original_grad = torch.autograd.grad
    calls = []

    def interrupt_third(*args, **kwargs):
        calls.append(1)
        if len(calls) == 3:
            raise TimeoutError("synthetic interruption")
        return original_grad(*args, **kwargs)

    monkeypatch.setattr(torch.autograd, "grad", interrupt_third)
    progress = {"counts": {"derivative_evaluations": 0, "derivative_attempts": 0}}
    with pytest.raises(TimeoutError):
        a.measure_gradients(model, rows, torch.zeros(8, dtype=torch.float64), True, progress)
    assert progress["counts"]["derivative_evaluations"] == 2
    assert progress["counts"]["derivative_attempts"] == 3
    assert progress["in_flight"] == "derivative_3"
