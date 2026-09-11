"""Nonformal conformance fixtures; no seed61 learner or development panel."""
from io import BytesIO
import hashlib
import json
import math
import time

import numpy as np
import torch
import torch.nn.functional as F

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_backend as backend
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_training_engine import (
    ExactPolicyGraph, forecast_target_terms, run_full_4096_dry_update,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy, RecurrentRolloutState, MasterAddressedTrainResetFactory,
    NativePersistentTrainingFlow, build_master_addressed_initial_state,
)
from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02 import study
from scripts.run_dish_forecast_package_b02 import publish


def test_joint_nll_covariance_and_mask_gradient():
    torch.set_num_threads(1)
    mean = torch.zeros(2, 4, 4, requires_grad=True)
    raw = torch.zeros(2, 4, 10, requires_grad=True)
    target = torch.tensor([[1., 2., 3., 4.], [5., 6., 7., 8.]])
    terms = forecast_target_terms(mean, raw, target)
    variance = (math.log(2) + 1e-3) ** 2 + 1e-4
    expected = 0.5 * (target.square().sum(-1) / variance + 4 * math.log(variance) + 4 * math.log(2 * math.pi))
    torch.testing.assert_close(terms, expected)
    mask = torch.tensor([True, False])
    (0.025 * terms[mask].mean()).backward()
    assert torch.isfinite(raw.grad).all() and raw.grad[0].abs().sum() > 0
    assert raw.grad[1].count_nonzero() == 0 and mean.grad[1].count_nonzero() == 0
    assert raw.grad[0, :, [0, 2, 5, 9]].abs().sum() > 0
    raw.grad = None
    mean.grad = None
    terms = forecast_target_terms(mean, raw, target)
    (terms.sum() * 0).backward()
    assert raw.grad.count_nonzero() == 0 and mean.grad.count_nonzero() == 0


def test_genuine_policy_link_and_default_graph():
    torch.set_num_threads(1)
    policies = []
    observation = {"actor": np.full((2, 4, 54), 0.02, np.float32),
                   "owner": np.array([0, 1]), "renew": np.ones(2, bool),
                   "snapshot_payload": np.zeros((2, 18), np.float32), "snapshot_delivery_mask": np.zeros(2, bool)}
    for package in (False, True):
        torch.manual_seed(62001)
        state = RecurrentRolloutState.fresh("STRUCTURED", width=2)
        policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=None, state=state, forecast_package=package)
        rows = policy.step_rows(observation, sampler=None, global_tick=0, deterministic=True)
        with torch.no_grad():
            raw = policy.model.service_q(state.hidden)
        policies.append((policy, rows, raw))
    torch.testing.assert_close(policies[0][2], policies[1][2], rtol=0, atol=0)
    for lane, copy in enumerate((3, 1)):
        np.testing.assert_array_equal(policies[0][1]["service_q"][lane], policies[0][2][lane, copy].double().numpy())
        np.testing.assert_array_equal(policies[1][1]["service_q"][lane], torch.sigmoid(policies[1][2][lane, copy]).double().numpy())
    model = policies[0][0].model
    hidden = torch.full((1, 4, 128), .125)
    assert "prediction_cholesky" not in model.training_heads(hidden)
    assert "prediction_cholesky" in model.training_heads(hidden, forecast_package=True)


def test_real_full_update_uses_raw_bce_and_forecast_gradient(monkeypatch):
    torch.manual_seed(62002)
    observed = []
    raw_heads = []
    genuine_heads = ExactPolicyGraph.training_heads
    def heads(model, hidden, forecast_package=False):
        result = genuine_heads(model, hidden, forecast_package=forecast_package)
        if forecast_package:
            raw_heads.append(result["service_q"].detach().reshape(512, 4, 20).clone())
        return result
    monkeypatch.setattr(ExactPolicyGraph, "training_heads", heads)
    actual = F.binary_cross_entropy_with_logits
    def record(logits, target, *args, **kwargs):
        if logits.shape[-1] == 20:
            observed.append(logits.detach().clone())
        return actual(logits, target, *args, **kwargs)
    monkeypatch.setattr(F, "binary_cross_entropy_with_logits", record)
    progress = {"optimizer_steps": 0}
    result = run_full_4096_dry_update(forecast_package=True, progress=progress,
                                     source_label="B02_NONFORMAL_SYNTHETIC_RULE_FIXTURE")
    assert result["losses_finite"] and result["gradient_norms_finite"]
    assert result["optimizer_steps"] == progress["optimizer_steps"] == 32
    assert len(observed) == 32
    assert len(raw_heads) == 32
    for logits, raw in zip(observed, raw_heads):
        torch.testing.assert_close(logits, raw[:, 1], rtol=0, atol=0)
    saved = torch.load(BytesIO(result["private_checkpoint_bytes"]), map_location="cpu", weights_only=False)
    assert saved["update"] == 1
    # The real optimizer state contains moments for Cholesky: it received the selected NLL gradient.
    model = ExactPolicyGraph()
    model.load_state_dict(saved["model"])
    matrix = [p for name, p in model.named_parameters() if p.ndim >= 2 and "flex_" not in name]
    others = [p for p in model.parameters() if id(p) not in {id(value) for value in matrix}]
    optimizer = torch.optim.AdamW([{"params": matrix}, {"params": others}])
    optimizer.load_state_dict(saved["optimizer"])
    assert optimizer.state[model.prediction_cholesky.weight]["exp_avg"].abs().sum() > 0


def test_ground_library_ordinary_passive_and_real_publication(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    master = hashlib.sha256(b"B02_NONFORMAL_HOST_TEST").digest()
    library = study.load_host(study.HOST)
    reset = MasterAddressedTrainResetFactory(master=master, block=0, arm="STRUCTURED")
    rows = reset.rows(np.zeros(32, np.int64))
    initial = build_master_addressed_initial_state(master=master, block=0, arm="STRUCTURED")
    def forbidden():
        raise AssertionError("explicit ground batch used global literal loader")
    monkeypatch.setattr(backend, "require_cpp_batched_production_backend", forbidden)
    native = backend.native_batch_from_rows(rows, library=library)
    progress = study.new_progress()
    measured = study.TrainingMeasurements(native, progress, time.perf_counter() + 60)
    actions = backend.empty_step_rows(32)
    labels = measured.passive_labels(actions)
    assert labels["target"].shape == (32, 4)
    measured.step(actions)
    measured.reset_selected(np.ones(32, bool), rows)
    prepared = native.prepare_b01_tick()
    native.complete_b01_tick(prepared, actions)
    assert native.library is library and progress["ordinary_training_transitions"] == 32
    assert progress["next_label_steps"] == 32
    # Constructing a genuine flow checks package propagation without a new learner replicate.
    flow = NativePersistentTrainingFlow(native=measured, arm="STRUCTURED", master=master,
                                        block=0, checkpoint_bytes=initial, forecast_package=True)
    assert flow.policy.forecast_package and flow.trainer.forecast_package
    # The real gradient update is exercised above; this isolated receipt drives the reload seam.
    monkeypatch.setattr(flow.trainer, "run_update", lambda *a, **k: {"update": 1})
    flow.apply_update({})
    assert flow.policy.forecast_package
    evaluation = backend.native_batch_from_rows((rows[0],), library=library)
    state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
    policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=initial, state=state, forecast_package=True)
    evaluation._states[0].battery[0] = 0  # Actual native terminal path, nonformal fixture.
    record = {"coordinate": "NONFORMAL"}
    study.evaluate_episode(evaluation, policy, time.perf_counter() + 60, progress, record, horizon=2)
    assert record["completed_ticks"] == 1 and record["complete"]
    assert record["unstepped_zero_service_ticks"] == 1
    assert "battery_exhausted" in record["terminal"]["causes"]
    control = {"status": "COMPLETE", "evaluation_rows": []}
    package = {"status": "COMPLETE", "evaluation_rows": []}
    for index, difference in enumerate((30, -10, 0, 100)):
        left = {**record, "coordinate": str(index), "service_ticks": 100}
        control["evaluation_rows"].append(left)
        package["evaluation_rows"].append({**left, "service_ticks": 100 + difference})
    paired = study.paired_result(control, package)
    assert paired["delta_package"] == 30 and len(paired["paired_rows"]) == 4
    publish(tmp_path, paired)
    assert json.loads((tmp_path / "summary.json").read_text())["delta_package"] == 30
    assert study.paired_result({"status": "INCOMPLETE"}, package)["status"] == "INCOMPLETE_PAIR"
    monkeypatch.undo()
    default = backend.native_batch_from_rows(rows)
    restored = backend.NativeBatch.from_snapshot_bytes(default.snapshot_bytes())
    assert restored.library is None
    ordinary = default.step(actions)
    replayed = restored.step(actions)
    np.testing.assert_array_equal(ordinary["service"], replayed["service"])
    np.testing.assert_array_equal(ordinary["actor"], replayed["actor"])


def test_nonfinite_failure_publishes_partial_observations(tmp_path):
    publish(tmp_path, {"status": "INCOMPLETE", "last_loss": float("nan"),
                       "last_gradient_norm": float("inf"), "optimizer_steps": 3})
    saved = json.loads((tmp_path / "summary.json").read_text())
    assert saved["last_loss"] == "nan" and saved["last_gradient_norm"] == "inf"
    assert saved["optimizer_steps"] == 3
