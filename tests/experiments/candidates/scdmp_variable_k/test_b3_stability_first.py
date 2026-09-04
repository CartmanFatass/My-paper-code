from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import torch
import pytest

from experiments.candidates.scdmp_variable_k.b3_stability_first import evaluation
from experiments.candidates.scdmp_variable_k.b3_stability_first import training as training_module
from experiments.candidates.scdmp_variable_k.b3_stability_first.config import (
    ALGORITHM_SEEDS, ARMS, BATCH_NAMESPACE_BASE, CORPUS_NAMESPACE_BASE,
    INITIALIZATION_NAMESPACE_BASE, MICROSTEP_LEDGER, MODEL_PARAMETER_COUNT,
    SCORED_NAMESPACE_BASE, SCORED_REGIMES,
)
from experiments.candidates.scdmp_variable_k.b3_stability_first.corpus import (
    LockedBatchPlan, build_corpus, structural_certificate, support_certificate,
)
from experiments.candidates.scdmp_variable_k.b3_stability_first.frontier import (
    active_seed_snapshot, atomic_save, load,
)
from experiments.candidates.scdmp_variable_k.b3_stability_first.lifecycle import Lifecycle
from experiments.candidates.scdmp_variable_k.b3_stability_first.manifest import complete_coordinate_manifest
from experiments.candidates.scdmp_variable_k.b3_stability_first.model import SCDMPModel
from experiments.candidates.scdmp_variable_k.b3_stability_first.result import invalid_calibration_packet
from experiments.candidates.scdmp_variable_k.b3_stability_first.run import (
    CorpusCache, credit_seed_ledger, execute_update_major_step,
    prepare_preactivity_certificates, prepare_static, production, reconcile_installed_result,
    static_conformance, update_major_dispatch,
)
from experiments.candidates.scdmp_variable_k.b3_stability_first.inference import complete_inference
from experiments.candidates.scdmp_variable_k.b3_stability_first.result import (
    complete_packet, frozen_treatment_configuration,
)
from experiments.candidates.scdmp_variable_k.b3_stability_first.training import (
    diagnostic_values, model_state_digest, summarize_trace,
)


def test_static_contract_and_complete_fresh_namespace_manifest() -> None:
    static = prepare_static()
    assert static["scientific_activity_started"] is False
    assert static["heavy_production_executed"] is False
    assert static_conformance()["conforming"] is True
    manifest = complete_coordinate_manifest()
    assert manifest["seed_order"] == list(range(200, 208))
    assert len(manifest["per_seed"]) == 8
    for seed, row in zip(ALGORITHM_SEEDS, manifest["per_seed"]):
        assert row["rng"]["initialization"] == INITIALIZATION_NAMESPACE_BASE + seed
        assert row["rng"]["batch_order"] == BATCH_NAMESPACE_BASE + seed
        assert row["rng"]["corpus_resets"] == CORPUS_NAMESPACE_BASE + seed
        assert row["rng"]["scored_regimes"]["fixed_4"] == SCORED_NAMESPACE_BASE + 1000 * seed
        assert row["materialization"]["batch"]["row_coordinate_count"] == 320_000
        assert row["predecessor_coordinates_admitted"] is False


def test_fresh_initialization_is_reproducible_and_has_exact_shape() -> None:
    first, second = SCDMPModel(200), SCDMPModel(200)
    assert model_state_digest(first) == model_state_digest(second)
    assert sum(parameter.numel() for parameter in first.parameters()) == MODEL_PARAMETER_COUNT
    assert len(tuple(first.parameters())) == 24
    assert tuple(ARMS) == ("FREE-DIRECT", "SCDMP-CORRECT", "SCDMP-ORDER-SHUFFLE")


def test_random_access_locked_update_zero_is_structurally_stable() -> None:
    corpus = build_corpus(200)
    plan = LockedBatchPlan(corpus, 200)
    first = plan.batch_for_update(0)
    second = plan.batch_for_update(0)
    assert first.update_index == second.update_index == 0
    assert {bank: [row.key for row in rows] for bank, rows in first.rows.items()} == {
        bank: [row.key for row in rows] for bank, rows in second.rows.items()
    }
    assert support_certificate(corpus, first)["conforming"] is True
    assert structural_certificate(corpus)["conforming"] is True


def test_audit_action_schedule_uses_fresh_b3_formula(monkeypatch) -> None:
    observed: list[tuple[int, int, int, int]] = []

    def fake_rollout(state, action, context_word):
        observed.append(action)
        return SimpleNamespace(terminal=state)

    monkeypatch.setattr(evaluation, "rollout_interval", fake_rollout)
    evaluation.audit_instances(201)
    expected_indices = [(43 + 11 * boundary) % 81 for boundary in range(12)]
    expected_actions = [evaluation.joint_action_from_index(index) for index in expected_indices]
    assert observed[:12] == expected_actions
    assert len(observed) == 64 * 12


def test_finite_zero_later_auxiliary_norm_is_retained_not_rejected() -> None:
    values = diagnostic_values(endpoint_norm=0.0, auxiliary_norm=0.0,
                               calibrated_auxiliary=2.0, coefficient=0.125)
    assert values == {"D": 0.0, "P": 0.0, "R": 0.0,
                      "endpoint_auxiliary_cosine": None}
    trace = []
    for update in range(1000):
        trace.append({"update": update, "P": 0.0 if update >= 500 else 1.0,
                      "R": 0.0, "endpoint_auxiliary_cosine": None})
    summary = summarize_trace(trace)
    assert summary["trajectory_length"] == 1000
    assert summary["final_P"] == 0.0
    assert summary["quarters"][2]["median_P"] == 0.0
    assert len(summary["undefined_cosine_updates"]) == 1000


def test_blinded_atomic_frontier_round_trip(tmp_path) -> None:
    path = tmp_path / "frontier.pt"
    value = {"candidate": "SCDMP-B3-STABILITY-FIRST-RELATION-SPECIFICITY",
             "revision": "SCDMP-B3-SCIENCE-20260814-01",
             "partial_selection_permitted": False,
             "tensor": torch.tensor([1.0], dtype=torch.float32)}
    atomic_save(path, value)
    restored = load(path)
    assert restored["partial_selection_permitted"] is False
    assert torch.equal(restored["tensor"], value["tensor"])


def test_update_major_dispatch_and_active_seed_snapshot_are_atomic_and_isolated(tmp_path) -> None:
    dispatch = list(update_major_dispatch(7, 9))
    assert dispatch == [
        (7, tuple((7, arm) for arm in ARMS)),
        (8, tuple((8, arm) for arm in ARMS)),
    ]
    events: list[object] = []
    boundary = execute_update_major_step(
        7, lambda arm: events.append(("step", arm)),
        lambda next_update: events.append(("commit", next_update)) or next_update,
    )
    assert boundary == 8
    assert events == [("step", arm) for arm in ARMS] + [("commit", 8)]
    failed_events: list[object] = []
    def fail_on_correct(arm: str) -> None:
        failed_events.append(("step", arm))
        if arm == "SCDMP-CORRECT":
            raise RuntimeError("synthetic interrupted arm")
    with pytest.raises(RuntimeError, match="synthetic interrupted arm"):
        execute_update_major_step(8, fail_on_correct,
            lambda next_update: failed_events.append(("commit", next_update)))
    assert failed_events == [("step", "FREE-DIRECT"), ("step", "SCDMP-CORRECT")]
    models = {arm: torch.nn.Linear(1, 1, bias=False) for arm in ARMS}
    optimizers = {arm: torch.optim.Adam(models[arm].parameters(), lr=1e-3) for arm in ARMS}
    traces = {arm: [{"update": 0, "arm": arm}] for arm in ARMS}
    losses = {arm: {"endpoint": 1.0, "auxiliary": 2.0} for arm in ARMS}
    for arm in ARMS:
        optimizers[arm].zero_grad(set_to_none=True)
        models[arm](torch.ones(1, 1)).sum().backward()
        optimizers[arm].step()
    snapshot = active_seed_snapshot(algorithm_seed=200, next_update=1,
        models=models, optimizers=optimizers, traces=traces, final_losses=losses,
        fixed_coefficients={arm: 0.25 for arm in ARMS})
    assert snapshot["arm_order"] == list(ARMS)
    assert snapshot["boundary"] == "after_complete_three_arm_update"
    saved_model = snapshot["model_states"][ARMS[0]]["weight"].clone()
    saved_moment = snapshot["optimizer_states"][ARMS[0]]["state"][0]["exp_avg"].clone()
    path = tmp_path / "active-seed.pt"
    atomic_save(path, {"candidate": "SCDMP-B3-STABILITY-FIRST-RELATION-SPECIFICITY",
        "revision": "SCDMP-B3-SCIENCE-20260814-01", "partial_selection_permitted": False,
        "active_seed": snapshot})
    for arm in ARMS:
        optimizers[arm].zero_grad(set_to_none=True)
        (3.0 * models[arm](torch.ones(1, 1))).sum().backward()
        optimizers[arm].step()
    assert torch.equal(snapshot["model_states"][ARMS[0]]["weight"], saved_model)
    assert torch.equal(snapshot["optimizer_states"][ARMS[0]]["state"][0]["exp_avg"], saved_moment)
    restored = load(path)["active_seed"]
    assert restored["next_update"] == 1
    assert torch.equal(restored["optimizer_states"][ARMS[0]]["state"][0]["exp_avg"], saved_moment)


def test_invalid_calibration_terminal_is_complete_and_contains_no_training_panels() -> None:
    calibrations = []
    for seed in ALGORITHM_SEEDS:
        for arm in ARMS:
            invalid = seed == 200 and arm == ARMS[0]
            calibrations.append({"algorithm_seed": seed, "arm": arm, "B_s": 2.0,
                "T_s": 0.5, "A_s_m_cal": None if invalid else 1.0,
                "lambda_s_m": None if invalid else 0.5,
                "calibration_valid": not invalid,
                "calibration_error": "nonfinite auxiliary gradient" if invalid else None})
    lifecycle = Lifecycle(phase="calibration", scientific_activity_started=True,
                          events=[{"event": "scientific_activity_started"}])
    packet = invalid_calibration_packet(lifecycle, static={"conforming": True},
        coordinate_manifest=complete_coordinate_manifest(), calibrations=calibrations,
        resources={"cpu_workers": 1}, frontier_path="frontier.pt",
        activity_sidecar="result.json.activity.json", anomalies=[])
    assert packet["complete"] is True
    assert packet["question_relevant_output_exists"] is True
    assert len(packet["calibration_table"]) == 24
    assert len(packet["invalid_cells"]) == 1
    assert packet["invalid_cells"][0]["finite_facts"]["A_s_m_cal"] is False
    assert packet["training"] is None and packet["checkpoints"] is None
    assert packet["support_panels"] is None and packet["audit_panels"] is None
    assert packet["scored_panels"] is None and packet["inference"] is None
    assert packet["frozen_treatment_configuration"]["training_schedule"] == {
        "major_axis": "update", "updates": 1000, "arm_order": list(ARMS)}
    assert packet["frozen_treatment_configuration"]["calibration_rule"]["dose"] == 0.25
    assert packet["configuration_and_activity_facts"]["repair_reseed_substitution_invoked"] is False


def test_corpus_cache_reuses_identity_and_credits_exact_ledger_once_per_seed() -> None:
    calls: list[int] = []
    def build(seed: int):
        calls.append(seed)
        return SimpleNamespace(seed=seed, microsteps=12_288)
    cache = CorpusCache(build)
    certificates = prepare_preactivity_certificates(
        cache, lambda seed, corpus: {"algorithm_seed": seed, "corpus": corpus,
                                    "conforming": True})
    for phase in ("calibration", "training", "evaluation"):
        for seed, certificate in zip(ALGORITHM_SEEDS, certificates):
            assert cache.get(seed) is certificate["corpus"], phase
    assert calls == list(ALGORITHM_SEEDS)
    assert cache.build_counts == {seed: 1 for seed in ALGORITHM_SEEDS}
    ledger = {name: 0 for name in MICROSTEP_LEDGER}
    for seed in ALGORITHM_SEEDS:
        credit_seed_ledger(ledger, corpus_microsteps=cache.get(seed).microsteps,
            audit_ledger={"common_audit_warmup": 3_072,
                          "audit_target_words": 46_656,
                          "audit_reverse_twins": 46_656},
            scored_steps=138_240)
    assert ledger == MICROSTEP_LEDGER


def test_synthetic_calibration_no_mutation_delivery_and_finite_zero_update(monkeypatch) -> None:
    created = []
    class DummyModel(torch.nn.Module):
        def __init__(self, seed: int) -> None:
            super().__init__()
            self.weight = torch.nn.Parameter(torch.tensor([1.0], dtype=torch.float32))
            created.append(self)
    class DummyPlan:
        def __init__(self, corpus, seed) -> None:
            pass
        def batch_for_update(self, update: int):
            return SimpleNamespace(update_index=update)
    multipliers = {"FREE-DIRECT": 1.0, "SCDMP-CORRECT": 2.0,
                   "SCDMP-ORDER-SHUFFLE": 4.0}
    monkeypatch.setattr(training_module, "SCDMPModel", DummyModel)
    monkeypatch.setattr(training_module, "LockedBatchPlan", DummyPlan)
    monkeypatch.setattr(training_module, "support_certificate",
                        lambda corpus, batch: {"conforming": True})
    monkeypatch.setattr(training_module, "ordered_parameters",
                        lambda model: tuple(model.parameters()))
    monkeypatch.setattr(training_module, "endpoint_loss",
                        lambda model, batch, scales: model.weight.square().sum())
    monkeypatch.setattr(training_module, "auxiliary_loss",
                        lambda model, batch, scales, arm: multipliers[arm] * model.weight.sum())
    lifecycle = Lifecycle()
    corpus = SimpleNamespace(scales=None)
    rows = training_module.calibrate_seed(corpus, 200, lifecycle)
    assert [row["A_s_m_cal"] for row in rows] == [1.0, 2.0, 4.0]
    assert [row["lambda_s_m"] for row in rows] == [0.5, 0.25, 0.125]
    assert all(row["lambda_s_m"] * row["A_s_m_cal"] == row["T_s"] == 0.5 for row in rows)
    assert all(row["model_mutation_during_calibration"] is False for row in rows)
    assert all(torch.equal(model.weight.detach(), torch.tensor([1.0])) for model in created)

    model = DummyModel(200)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3,
                                 betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-5)
    monkeypatch.setattr(training_module, "auxiliary_loss",
                        lambda model, batch, scales, arm: (model.weight * 0.0).sum())
    calibration = {"algorithm_seed": 200, "arm": "FREE-DIRECT",
                   "lambda_s_m": 0.5, "A_s_m_cal": 1.0, "T_s": 0.5}
    trace, _ = training_module.train_update(model, optimizer, corpus, 200,
        "FREE-DIRECT", 17, calibration, DummyPlan(corpus, 200))
    assert calibration["lambda_s_m"] == 0.5
    assert trace["fixed_lambda"] == 0.5
    assert trace["A"] == trace["D"] == trace["P"] == 0.0
    assert trace["endpoint_auxiliary_cosine"] is None
    assert trace["finite_zero_auxiliary_continues"] is True


def _synthetic_seed_packets() -> list[dict[str, object]]:
    packets = []
    arm_values = {
        "FREE-DIRECT": {"Dcorr": .20, "Dwrong": .30, "Epred": .15, "Q": .02},
        "SCDMP-CORRECT": {"Dcorr": .10, "Dwrong": .30, "Epred": .10, "Q": .01},
        "SCDMP-ORDER-SHUFFLE": {"Dcorr": .20, "Dwrong": .10, "Epred": .15, "Q": .02},
    }
    for seed in ALGORITHM_SEEDS:
        arms = {}
        for arm in ARMS:
            real = {**arm_values[arm], "competence_ratio": .5,
                    "oracle_regret_fraction_ge_0_015": .5,
                    "score_range_pass_fraction": 1.0}
            sham = {**real, "Dcorr": .10}
            arms[arm] = {"by_class": {"REAL": real, "SHAM": sham},
                "true_variance_denominators_valid": True, "F_bound_hit_fraction": 0.0,
                "variance_ratios": {"slot1_e": 1.0}}
        scored = []
        for regime in SCORED_REGIMES:
            for arm in ARMS:
                scored.append({"regime": regime, "dynamics_class": "REAL", "arm": arm,
                    "normalized_return": 1.0 if arm == "SCDMP-CORRECT" else .9,
                    "failure": 0})
        packets.append({"algorithm_seed": seed,
            "audit": {"arms": arms,
                "correct_action_disagreement": {"FREE-DIRECT": .5,
                                                  "SCDMP-ORDER-SHUFFLE": .5},
                "support": {"continuous_gate_pass": True, "q_exact_membership_pass": True},
                "physical_order": {"REAL": {"median_max_score_difference_per_step": .03,
                                               "oracle_action_difference_fraction": .3},
                                   "SHAM": {"maximum_absolute_score_difference_per_step": 0.0,
                                            "oracle_actions_identical": True}}},
            "structural_certificate": {"checks": {"action_support": True}},
            "train_support": {arm: {"ratio": .5} for arm in ARMS},
            "training": {"gradient_trace": {arm: [None] * 1000 for arm in ARMS}},
            "scored_episodes": scored,
            "checkpoints": {arm: {} for arm in ARMS}})
    return packets


def test_synthetic_eight_seed_inference_and_successful_packet_share_configuration() -> None:
    seeds = _synthetic_seed_packets()
    inference = complete_inference(seeds)
    assert set(inference["contrasts"]) == {
        "C_FREE", "C_SHUF", "W_SHUF", "P_FREE", "P_SHUF", "A_FREE", "A_SHUF", "ORDER"}
    assert inference["adverse_and_nonharm"]["family_size"] == 24
    calibrations = [{"algorithm_seed": seed, "arm": arm, "calibration_valid": True}
                    for seed in ALGORITHM_SEEDS for arm in ARMS]
    packet = complete_packet(Lifecycle(phase="evaluation", scientific_activity_started=True),
        static={"conforming": True}, coordinate_manifest=complete_coordinate_manifest(),
        calibrations=calibrations, seeds=seeds, inference=inference,
        resources={"cpu_workers": 1}, ledger=dict(MICROSTEP_LEDGER),
        frontier_path="frontier.pt", activity_sidecar="result.json.activity.json",
        anomalies=[])
    assert packet["frozen_treatment_configuration"] == frozen_treatment_configuration()
    assert packet["frozen_treatment_configuration"]["optimizer"]["lr"] == 1e-3
    assert packet["frozen_treatment_configuration"]["calibration_rule"] == {
        "dose": .25, "minimum_auxiliary_to_endpoint_ratio": .01,
        "coefficient_immutable_after_update_zero": True}


def test_resume_reconciles_installed_result_sidecar_and_frontier(tmp_path) -> None:
    output = (tmp_path / "result.json").resolve()
    frontier_path = (tmp_path / "frontier.pt").resolve()
    sidecar = Path(str(output) + ".activity.json")
    base_frontier = {"candidate": "SCDMP-B3-STABILITY-FIRST-RELATION-SPECIFICITY",
        "revision": "SCDMP-B3-SCIENCE-20260814-01", "partial_selection_permitted": False,
        "phase": "evaluation", "lifecycle": {"phase": "evaluation"}}
    atomic_save(frontier_path, base_frontier)
    installed = {"artifact_kind": "SCDMP_B3_COMPLETE_ATOMIC_RESULT",
        "candidate": "SCDMP-B3-STABILITY-FIRST-RELATION-SPECIFICITY",
        "revision": "SCDMP-B3-SCIENCE-20260814-01", "complete": True,
        "question_relevant_output_exists": True,
        "retained_frontier": str(frontier_path), "activity_sidecar": str(sidecar),
        "lifecycle": {"phase": "complete", "scientific_activity_started": True,
                      "question_relevant_output_exists": True, "events": []}}
    output.write_text(json.dumps(installed), encoding="utf-8")
    returned = production(output, frontier_path, resume=True)
    assert returned == installed
    reconciled = load(frontier_path)
    sidecar_value = json.loads(sidecar.read_text(encoding="utf-8"))
    assert reconciled["phase"] == "complete"
    assert reconciled["finalization"]["reconciled"] is True
    assert sidecar_value["final_result_installed"] is True
    assert sidecar_value["frontier_path"] == str(frontier_path)
    reconcile_installed_result(output, frontier_path, installed)
    assert load(frontier_path)["finalization"]["result"] == str(output)
