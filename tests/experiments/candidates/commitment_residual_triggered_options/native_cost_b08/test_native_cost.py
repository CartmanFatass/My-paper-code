"""Synthetic algebra/readout/clock fixtures; no host, predictor or real gate run."""
import inspect
import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.commitment_residual_triggered_options.native_cost_b08 import experiment as e


def test_masked_cost_gradient_equal_rows_detached_labels():
    logits = torch.tensor([[.3, -.8, 999., -4.], [.4, .1, -.3, 999.]], requires_grad=True)
    labels = torch.tensor([[.04, .01, 999., float("nan")], [.04, .01, -.02, 999.]], requires_grad=True)
    legal = torch.tensor([[True, True, False, False], [True, True, True, False]])
    loss = e.expected_native_cost_loss(logits, labels, legal)
    loss.backward()
    expected_loss, expected_grad = 0., torch.zeros_like(logits)
    for i, n in enumerate((2, 3)):
        p = torch.exp(logits.detach()[i, :n] - logits.detach()[i, :n].max())
        p = p / p.sum()
        c = (labels.detach()[i, :n].max() - labels.detach()[i, :n]) / .01
        row_loss = (p*c).sum()
        expected_loss += row_loss / 2
        expected_grad[i, :n] = p * (c-row_loss) / 2
    torch.testing.assert_close(loss, expected_loss)
    torch.testing.assert_close(logits.grad, expected_grad)
    assert torch.equal(logits.grad[~legal], torch.zeros(3))
    assert labels.grad is None


def test_stable_large_logits_and_single_legal_action():
    logits = torch.tensor([[10000., 10000., float("nan")], [-10000., 99., 5.]], requires_grad=True)
    legal = torch.tensor([[True, True, False], [True, False, False]])
    labels = torch.tensor([[.01, 0., float("nan")], [.04, .05, .06]])
    loss = e.expected_native_cost_loss(logits, labels, legal)
    assert loss.item() == pytest.approx(.25)
    loss.backward()
    assert torch.isfinite(logits.grad).all()
    assert torch.count_nonzero(logits.grad[1]) == 0


def panel():
    return [{"row_key": f"synthetic/{i}", "material_side": "KEEP" if i < 8 else "REPLAN",
             "legal_mask": [True, True] + [False]*6, "g16": [0., -.016] + [None]*6}
            for i in range(16)]


def readout(error_rows=()):
    logits = np.zeros((16, 8), dtype=np.float32)
    logits[:, 2:] = 1000.  # illegal logits must never win
    logits[list(error_rows), 1] = 1.
    return e.raw.score_readout(panel(), logits)


def test_legal_printed_ties_and_competence_boundaries():
    perfect = readout()
    assert all(r["selected_action_index"] == 0 for r in perfect["rows"])
    competent = readout([0, 1, 8, 9])
    assert competent["competent"]
    assert competent["equal_side_regret"] == pytest.approx(.004)
    assert not readout([0, 1, 2, 8, 9])["competent"]


def contrasts(short=(.004, .004, .004), long=(.004, .004, .004)):
    return {b: {name: {"delta_regret": d, "comparison_trustworthy": True}
                for name, d in zip(("new_RAW", "new_DERANGED", "historical_B04_RAW"), values)}
            for b, values in (("SHORT", short), ("LONG", long))}


@pytest.mark.parametrize("reference", ["new_RAW", "new_DERANGED", "historical_B04_RAW"])
def test_each_primary_contrast_is_required_and_strict(reference):
    values = contrasts()
    values["SHORT"][reference]["delta_regret"] = .0025
    result = e.result_reading(values, True)
    assert result["alignment_by_endpoint"] == {"SHORT": False, "LONG": True}
    values["SHORT"][reference]["delta_regret"] = np.nextafter(.0025, np.inf)
    assert e.result_reading(values, True)["alignment_by_endpoint"]["SHORT"]


def test_historical_floor_and_weak_new_raw_cannot_be_rescued():
    result = e.result_reading(contrasts(long=(.004, .004, .002)), True)
    assert result["qualifying_endpoints"] == ["SHORT"]
    weak = e.result_reading(contrasts(), False)
    assert weak["qualifying_endpoints"] == []
    assert weak["reading"] == "WEAK_NEW_RAW_LONG_DIAGNOSTICS_ONLY"
    unknown = e.result_reading(contrasts(), None)
    assert unknown["reading"] == "PRIMARY_COMPARISON_LIMITED"
    assert unknown["new_raw_long_competent"] is None
    assert unknown["alignment_by_endpoint"] == {"SHORT": None, "LONG": None}


def test_mixed_budget_preserves_losses_and_no_best_endpoint():
    result = e.result_reading(contrasts(long=(-.004, .001, -.0001)), True)
    assert result["mixed_budget"] and result["short_signal_lost_at_long"]
    assert result["qualifying_endpoints"] == ["SHORT"]
    assert [r["delta"] for r in result["opposite_sign_or_adverse_contrasts"]] == [-.004, -.0001]
    assert result["opposite_sign_or_adverse_contrasts"][0]["material"]
    assert e.result_reading(contrasts(), True)["reading"] == "ALIGNMENT_AT_BOTH_OBSERVED_BUDGETS"
    assert e.result_reading(contrasts((.001, .001, .001), (.001, .001, .001)), True)["reading"] == "NO_SPECIFIED_ALIGNMENT_SIGNAL"


def test_paired_native_gains_include_losses_and_historical_labels():
    comparison = e.paired_contrast(readout([0, 1, 8, 9]), readout([2, 10]))
    assert comparison["gain_rows"] == 4 and comparison["loss_rows"] == 2
    assert comparison["delta_regret"] == pytest.approx(.002)
    assert comparison["paired_native_gain_sum"] == pytest.approx(.032)
    assert comparison["comparison_trustworthy"]
    prior = readout([0])
    prior["rows"][0]["g16"][1] -= .01
    assert not e.paired_contrast(prior, readout())["comparison_trustworthy"]
    prior["rows"][0]["legal_mask"][2] = True
    with pytest.raises(ValueError, match="support"):
        e.paired_contrast(prior, readout())
    values = contrasts()
    values["SHORT"]["historical_B04_RAW"]["comparison_trustworthy"] = False
    limited = e.result_reading(values, True)
    assert limited["reading"] == "PRIMARY_COMPARISON_LIMITED"
    assert limited["alignment_by_endpoint"] == {"SHORT": None, "LONG": True}


def test_complete_and_accrued_accounting_includes_shared_publication(monkeypatch):
    clock = [100.]
    monkeypatch.setattr(e.time, "perf_counter", lambda: clock[0])
    budget = e.WallBudget(0.)
    for arm, seconds in zip(e.ARMS, (20., 30., 40.)):
        with budget.arm(arm):
            clock[0] += seconds
            budget.check()
    clock[0] += 50.  # shared checking/publication
    budget.check()
    result = e.complete_accounting(240., budget.arm_seconds)
    assert result["shared_overhead_seconds"] == 150.
    assert list(result["charged_seconds_by_arm"].values()) == [170., 180., 190.]
    assert result["summed_invocation_wall_seconds"] == 240.
    clock[0] = 1260.  # shared1170 + DERANGED40 breaches1200 despite shared<1500
    with pytest.raises(TimeoutError, match="B08"):
        budget.check()
    assert e.complete_accounting(1501., dict.fromkeys(e.ARMS, 400.))["shared_cap_breached"]


def test_loss_loop_preserves_b04_update_semantics():
    old, new = inspect.getsource(e.b04.train_path), inspect.getsource(e.train_path)
    def update_body(s):
        s = s[s.index("    order ="):s.index("        if update in trace_updates:")]
        s = s.replace('        if all(parameter.grad is None for parameter in model.parameters()):\n'
                      '            raise RuntimeError("B08 gate loss reached no model parameter gradients")\n', "")
        return s.replace("check_wall(started, time.perf_counter() - arm_started)", "monitor()").replace(
            "base.legal_masked_mse", "expected_native_cost_loss").replace("RAW gate", "B08 gate")
    assert update_body(old) == update_body(new)


def test_readout_publication_and_terminal_accounting(tmp_path):
    history = {"representations": {a: {b: readout([0, 1, 8, 9]) for b in e.ENDPOINTS} for a in e.ARMS}}
    predictions, exposures = {}, {}
    for arm in e.ARMS:
        vector = np.zeros((16, 8), dtype=np.float32)
        if arm != e.TRUE:
            vector[[0, 1, 8, 9], 1] = 1.
        predictions[arm] = {update: vector.copy() for update in e.ENDPOINTS.values()}
        exposures[arm] = [{"update": u, "processed_examples": u*32} for u in e.ENDPOINTS.values()]
    budget = e.WallBudget(e.time.perf_counter())
    summary = e.score_summary(panel(), predictions, exposures, history, budget)
    assert summary["result_reading"]["qualifying_endpoints"] == ["SHORT", "LONG"]
    assert set(summary["contrasts"]["LONG"]) == {"new_RAW", "new_DERANGED", "historical_B04_RAW"}
    assert summary["historical_representations"] == history["representations"]
    summary["cost_law"] = {"arm_training_evaluation_scoring_seconds": dict(zip(e.ARMS, (10., 20., 30.)))}
    e.raw.publish_summary(tmp_path, summary)
    original = (tmp_path / "summary.json").read_bytes()
    e.publish_complete_accounting(tmp_path, 200.)
    assert (tmp_path / "summary.json").read_bytes() == original
    loaded = json.loads(original)
    assert len(loaded["representations"][e.TRUE]["SHORT"]["rows"]) == 16
    assert "logits" in loaded["representations"][e.TRUE]["SHORT"]["rows"][0]
    accounting = json.loads((tmp_path / "complete_accounting.json").read_text())
    assert accounting["charged_seconds_by_arm"][e.RAW] == 150.


def test_run_assembly_three_paths_before_any_readout(tmp_path, monkeypatch):
    # All host/learner/forward entry points replaced: exercise assembly and publication only.
    rows = tuple(SimpleNamespace(key=SimpleNamespace(text=r["row_key"], primitive_time=0),
                 legal_mask=np.array(r["legal_mask"]), g16=np.array(r["g16"], dtype=float)) for r in panel())
    metadata = {r["row_key"]: {"side": r["material_side"]} for r in panel()}
    monkeypatch.setattr(e.b04, "prepare", lambda *a: (rows, rows, None, metadata, {}, {}))
    packets = {s: {a: SimpleNamespace(require_rows=lambda r: None) for a in e.ARMS} for s in ("TRAIN", "EVALUATION")}
    monkeypatch.setattr(e.b04, "packet_sets", lambda *a: (packets, {"TRAIN": []}))
    monkeypatch.setattr(e.b04, "exposure_counts", lambda *a: {})
    stages = []
    def train(*args, **kwargs):
        stages.append(kwargs["representation"])
        assert kwargs["seed"] == 0 and kwargs["final_update"] == 258 and kwargs["batch_size"] == 32
        return {}, [{"update": u} for u in e.ENDPOINTS.values()], .0, {}
    def forward(*args):
        assert stages[:3] == list(e.ARMS)
        stages.append("forward")
        return {u: np.zeros((16, 8), dtype=np.float32) for u in e.ENDPOINTS.values()}
    monkeypatch.setattr(e, "train_path", train)
    monkeypatch.setattr(e.raw, "forward_snapshots", forward)
    monkeypatch.setattr(e.base, "current_launch_sha", lambda: "engineering-fixture")
    prior = tmp_path / "historical.json"
    prior.write_text(json.dumps({"representations": {a: {b: readout() for b in e.ENDPOINTS} for a in e.ARMS}}))
    output = tmp_path / "output"
    result = e.run_experiment(output, historical_summary=prior, argv=["fixture"], execution_node="fixture",
                              started=e.time.perf_counter())
    assert stages == list(e.ARMS) + ["forward"]*3
    assert result["work_counts"]["processed_examples"] == 24768
    assert (output / "summary.json").is_file()
    assert "inner_prepublication_wall_seconds" in result["resources"]


def test_adverse_and_mixed_reading_requires_individual_contrast_trust():
    values = contrasts(short=(.004, .004, -.004))
    values["SHORT"]["historical_B04_RAW"]["comparison_trustworthy"] = False
    result = e.result_reading(values, True)
    assert result["alignment_by_endpoint"] == {"SHORT": None, "LONG": True}
    assert result["opposite_sign_or_adverse_contrasts"] == []
    assert not result["mixed_budget"]
    assert values["SHORT"]["historical_B04_RAW"]["delta_regret"] == -.004

    # One independently trustworthy loss still matters at an otherwise limited endpoint.
    values["SHORT"]["new_RAW"]["delta_regret"] = -.003
    result = e.result_reading(values, True)
    assert result["alignment_by_endpoint"] == {"SHORT": None, "LONG": True}
    assert result["opposite_sign_or_adverse_contrasts"] == [
        {"endpoint": "SHORT", "reference": "new_RAW", "delta": -.003, "material": True}]
    assert result["mixed_budget"]
    assert values["SHORT"]["historical_B04_RAW"]["delta_regret"] == -.004


@pytest.fixture
def stationary_training(monkeypatch):
    """Connected equal-cost logits; real Adam on a tiny synthetic module, no host/model package."""
    state = SimpleNamespace(steps=0, gradients=[], model=None)

    class TinyGate(torch.nn.Module):
        def __init__(self, unused_rng):
            super().__init__()
            self.logits = torch.nn.Parameter(torch.arange(1., 9.))
            state.model = self

        def forward(self, histories, lengths, packet):
            return self.logits.unsqueeze(0).expand(len(lengths), -1)

    def collate(rows, packets, indices):
        n = len(indices)
        return (torch.zeros(n, 1, 42), torch.ones(n, dtype=torch.int64),
                torch.zeros(n, 52), torch.ones(n, 8, dtype=torch.bool), torch.ones(n, 8))

    original_step = torch.optim.Adam.step
    def step(optimizer, *args, **kwargs):
        state.gradients.append(state.model.logits.grad.detach().clone())
        result = original_step(optimizer, *args, **kwargs)
        state.steps += 1
        return result

    monkeypatch.setattr(e.base, "CommonHistoryGate", TinyGate)
    monkeypatch.setattr(e.base, "counter_rng_for_namespace", lambda *args: None)
    monkeypatch.setattr(e.base, "_collate", collate)
    monkeypatch.setattr(torch.optim.Adam, "step", step)
    state.run = lambda: e.train_path((None, None), SimpleNamespace(values=None), seed=0,
        final_update=2, trace_updates=(1, 2), batch_size=2, monitor=lambda: None, representation=e.RAW)
    return state


def test_finite_zero_movement_emitted_after_connected_adam_updates(stationary_training):
    state = stationary_training
    snapshots, exposures, _, scales = state.run()
    assert state.steps == 2 and len(state.gradients) == 2
    assert all(torch.equal(g, torch.zeros(8)) for g in state.gradients)
    assert state.model.logits.grad is not None
    assert scales["initial_parameter_l2"] > 0
    assert set(snapshots) == {1, 2}
    for update, line in enumerate(exposures, start=1):
        assert line["update"] == update and line["processed_examples"] == update*2
        assert line["parameter_displacement_l2_over_initial_l2"] == 0.
        assert line["parameter_displacement_linf_over_initial_linf"] == 0.
        assert line["last_batch_expected_native_cost_loss"] == 0.
        assert torch.equal(snapshots[update].logits, torch.arange(1., 9.))


@pytest.mark.parametrize("fault,message,expected_steps", [
    ("loss", "loss became nonfinite", 0),
    ("gradient", "gradient became nonfinite", 0),
    ("parameter", "parameter became nonfinite", 1),
    ("movement", "movement became nonfinite", 1),
    ("disconnected", "no model parameter gradients", 0),
    ("detached", "does not require grad", 0),
])
def test_training_integrity_failures_remain_detected(stationary_training, monkeypatch, fault, message, expected_steps):
    state = stationary_training
    original_loss = e.expected_native_cost_loss
    if fault == "loss":
        monkeypatch.setattr(e, "expected_native_cost_loss", lambda *a: original_loss(*a)*float("nan"))
    elif fault == "gradient":
        def loss(*args):
            args[0].register_hook(lambda g: torch.full_like(g, float("nan")))
            return original_loss(*args)
        monkeypatch.setattr(e, "expected_native_cost_loss", loss)
    elif fault == "parameter":
        original_step = torch.optim.Adam.step
        def step(*args, **kwargs):
            result = original_step(*args, **kwargs)
            with torch.no_grad():
                state.model.logits[0] = float("nan")
            return result
        monkeypatch.setattr(torch.optim.Adam, "step", step)
    elif fault == "movement":
        monkeypatch.setattr(e.base, "_movement", lambda *a: {"synthetic_displacement": float("nan")})
    elif fault == "disconnected":
        monkeypatch.setattr(e, "expected_native_cost_loss", lambda *a: torch.tensor(0., requires_grad=True))
    else:
        monkeypatch.setattr(e, "expected_native_cost_loss", lambda *a: original_loss(*a).detach())
    with pytest.raises(RuntimeError, match=message):
        state.run()
    assert state.steps == expected_steps
