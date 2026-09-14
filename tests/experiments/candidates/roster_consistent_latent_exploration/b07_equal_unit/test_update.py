"""Focused tensor/AST contracts; no RCLE model, native rollout or scientific RNG."""
import ast
import io
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration.b07_equal_unit.update import (
    step_from_losses, unit_direction,
)

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "experiments/candidates/roster_consistent_latent_exploration"


class TensorFixture(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.p = torch.nn.Parameter(torch.tensor([.3, -.2], dtype=torch.float64))
        self.shared_alias = self.p
        self.q = torch.nn.Parameter(torch.tensor([.4, .1], dtype=torch.float64))
        self.unused = torch.nn.Parameter(torch.zeros(26157, dtype=torch.float64))


def flat(model):
    return torch.cat([p.detach().reshape(-1) for p in model.parameters()])


def definition(path, name, namespace):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if getattr(n, "name", None) == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name]


@pytest.mark.parametrize("scale", [1e-300, 1.0, 1e300])
def test_scale_safe_complete_direction(scale):
    value = torch.tensor([3 * scale, -4 * scale, 0], dtype=torch.float64)
    torch.testing.assert_close(unit_direction(value), torch.tensor([.6, -.8, 0], dtype=torch.float64))
    assert torch.equal(unit_direction(torch.zeros_like(value)), torch.zeros_like(value))


def test_shared_coordinates_unused_zeros_and_no_factor100():
    model = TensorFixture()
    assert len(tuple(model.parameters())) == 3  # the registered alias is not duplicated
    before = flat(model)
    result = step_from_losses(model.parameters(), 2 * model.p[0] + 4 * model.q[0],
                              model.p[1] - 2 * model.q[0])
    direction = torch.tensor([2 / math.sqrt(20), 1 / math.sqrt(5),
                              4 / math.sqrt(20) - 2 / math.sqrt(5), 0], dtype=torch.float64)
    expected = -.02 * direction / torch.linalg.vector_norm(direction)
    torch.testing.assert_close(flat(model)[:4] - before[:4], expected)
    assert torch.equal(model.unused, before[4:])
    assert result["score_channel_derivative_traversals"] == 2
    assert result["measured_parameter_delta_norm"] == pytest.approx(.02)
    assert all(parameter.grad is None for parameter in model.parameters())
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("case", ["one_zero", "both_zero", "cancel", "near_cancel"])
def test_zero_and_cancellation_keep_exact_algorithm(case):
    model = TensorFixture()
    before = flat(model)
    left = model.p[0]
    right = -model.p[0]
    if case == "one_zero":
        left = model.p[0] * 0
    elif case == "both_zero":
        left, right = model.p[0] * 0, model.p[0] * 0
    elif case == "near_cancel":
        right = right + 1e-12 * model.p[1]
    result = step_from_losses(model.parameters(), left, right)
    if case in ("both_zero", "cancel"):
        assert torch.equal(flat(model), before)
        assert not result["nonzero"]
    else:
        assert result["nonzero"]
        assert float(torch.linalg.vector_norm(flat(model) - before)) == pytest.approx(.02)


def test_two_derivatives_share_graph_then_release_it():
    model = TensorFixture()
    intermediate = (model.p[0] * model.q[0]).square()
    progress = {}
    step_from_losses(model.parameters(), intermediate, 2 * intermediate, progress)
    assert progress["derivative_attempts"] == progress["derivatives_completed"] == 2
    with pytest.raises(RuntimeError, match="backward through the graph a second time"):
        torch.autograd.grad(intermediate, tuple(model.parameters()), allow_unused=True)


@pytest.mark.parametrize("kind", ["loss", "gradient"])
def test_nonfinite_rejection_is_before_any_parameter_step(kind):
    model = TensorFixture()
    if kind == "gradient":
        with torch.no_grad():
            model.p[0] = 0
        left = model.p[0].sqrt()  # finite loss, infinite derivative
    else:
        left = model.p[0] * float("nan")
    before, progress = flat(model), {}
    with pytest.raises(RuntimeError, match="nonfinite"):
        step_from_losses(model.parameters(), left, model.q[0], progress)
    assert torch.equal(flat(model), before)
    assert progress.get("parameter_step_attempts", 0) == 0
    assert progress.get("derivatives_completed", 0) == (2 if kind == "gradient" else 0)


def test_real_update_caller_reductions_two_batches_and_baseline_order():
    model, batches = TensorFixture(), []
    baselines = torch.arange(8, dtype=torch.float64) / 10
    before, old_baselines = flat(model), baselines.clone()

    def execute(model, package, rng, coordinates, training):
        assert torch.equal(flat(model), before)
        assert torch.equal(baselines, old_baselines)
        batches.append(coordinates)
        output = []
        for _, cell, _, _ in coordinates:
            common = model.p[0] * model.q[0]
            output.append(SimpleNamespace(Y=float(cell + 1), U=.2, F=.1, tau=40,
                         plan_scores=[common, model.p[1]],
                         claim_scores=[2 * common, model.q[1]], agent_ticks=512, claim_decisions=128))
        return output

    def score(plan, claims):
        return plan.mean(), claims.mean(), plan.mean() + claims.mean()

    def checked_step(parameters, manager, claim, progress):
        assert torch.equal(baselines, old_baselines)
        return step_from_losses(parameters, manager, claim, progress)

    namespace = {"torch": torch, "step_from_losses": checked_step,
                 "host": SimpleNamespace(TRAINING_CELLS=tuple(range(8)), _mean=lambda x: sum(x) / len(x)),
                 "b03": SimpleNamespace(EpisodeCoordinate=lambda *v: v, FLEX="FLEX",
                                        execute_learned_batch=execute, averaged_episode_score=score)}
    update = definition(SOURCE / "b07_equal_unit/study.py", "training_update", namespace)
    progress = {}
    new_baselines, curve = update(model, SimpleNamespace(block_index=0), 0, baselines, progress)
    assert [len(batch) for batch in batches] == [32, 32]
    assert [sum(c[1] == cell for batch in batches for c in batch) for cell in range(8)] == [8] * 8
    torch.testing.assert_close(new_baselines, .95 * old_baselines + (1 - .95) * torch.arange(1, 9, dtype=torch.float64))
    assert torch.equal(baselines, old_baselines)
    assert curve["event_order"] == ["parameter_update", "baseline_update"]
    assert curve["training_episodes"] == progress["returned_training_episodes"] == 64
    assert curve["score_channel_derivative_traversals"] == 2
    assert progress["parameter_steps_completed"] == progress["baseline_updates_completed"] == 1
    json.dumps(curve, allow_nan=False)


class MemoryPath:
    """Only the output path contract used by the shared runner; no filesystem IO."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

    def __truediv__(self, value):
        return MemoryPath(self.value + "/" + value)

    def mkdir(self, **kwargs):
        pass

    def open(self, *args, **kwargs):
        return io.StringIO()


@pytest.mark.parametrize("mode", ["legacy", "equal_unit", "partial_failure"])
def test_common_runner_publishes_actual_rule_and_counts(mode):
    model, writes, calls = TensorFixture(), {}, []

    def update(*args):
        calls.append(args[-1])
        if mode == "partial_failure":
            args[-1].update(returned_training_episodes=64, derivative_attempts=2, derivatives_completed=1)
            raise RuntimeError("fixture second-derivative interruption")
        return args[3], dict(training_episodes=64, nonzero=True, score_channel_derivative_traversals=2)

    fake_host = SimpleNamespace(seed_root_key=lambda s: b"fixture", flat_parameters=flat,
                               check_wall=lambda *a: None, peak_rss_bytes=lambda: 0,
                               write_json=lambda path, value: writes.update({str(path): json.loads(json.dumps(value))}),
                               ArmWallExpired=type("ArmWallExpired", (Exception,), {}))
    namespace = {"torch": torch, "time": SimpleNamespace(perf_counter=lambda: 1),
                 "traceback": SimpleNamespace(print_exc=lambda: None), "host": fake_host,
                 "SEED": 24, "UPDATES": 200, "OBJECT_ID": "legacy", "LAW": {"nearest_probability": .9},
                 "make_rng": lambda *a, **k: (SimpleNamespace(root_digest="fixture", certificate={"native": {}}), object()),
                 "initialize_model": lambda *a, **k: model, "save_model": lambda *a: None,
                 "b03": SimpleNamespace(training_update=update, panel=lambda *a: [{"fixture": True}],
                                        panel_summary=lambda rows: {}, json=json)}
    run = definition(SOURCE / "b04_nearest_prior/study.py", "run", namespace)
    out = MemoryPath("memory/" + mode)
    result = run("learned", out, "fixture-sha", "fixture-admission", 0, 1,
                 updates=2, equal_unit_update=None if mode == "legacy" else update)
    assert writes[str(out / "summary.json")] == result
    if mode == "legacy":
        assert calls == [100.0, 100.0]
        assert result["actor_score_weight"] == 100
        assert "update_rule" not in result
        assert result["counts"]["backward_step_calls"] == 2
    else:
        assert "actor_score_weight" not in result
        assert "no factor100" in result["update_rule"]
        assert "backward_step_calls" not in result["counts"]
        if mode == "equal_unit":
            assert result["status"] == "COMPLETE"
            assert result["counts"]["score_channel_derivative_traversals"] == 4
            assert result["counts"]["parameter_update_attempts"] == 2
        else:
            assert result["status"] == "TECHNICAL_STOP"
            assert result["counts"]["training_episodes"] == 64
            assert result["counts"]["score_channel_derivative_attempts"] == 2
            assert result["counts"]["score_channel_derivative_traversals"] == 1
            assert result["counts"]["parameter_update_attempts"] == 0
