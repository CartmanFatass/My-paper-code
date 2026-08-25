"""Synthetic, non-scientific contract tests for the Pro-closed SRF r03 package.

Every fixture here uses test-only bytes and pytest ``tmp_path`` locations.  The
file never references an r07 result identity, observed coordinate, or runtime
counter as a scientific object.
"""

from __future__ import annotations

import copy
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import inspect
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.scdmp_variable_k.support_representation_factorial import (
    accounting,
    config,
    corpus,
    inference,
    model,
    result,
    rng,
    run,
    training,
)
from experiments.candidates.scdmp_variable_k.support_representation_factorial.lifecycle import (
    Lifecycle,
)


SYNTHETIC_MASTER = bytes(range(32))


def _synthetic_packets() -> list[dict[str, object]]:
    """Create non-scientific packet-shaped values for inference-only tests."""
    packets: list[dict[str, object]] = []
    for seed_index in config.SEED_INDICES:
        for cell in config.CELLS:
            packets.append({
                "seed_index": seed_index,
                "cell": cell,
                "evaluation_identity": f"{seed_index:064x}",
                "fit_support": {"E_mean": 1.0, "ratio": 0.5, "passed": True},
                "target": {"E_mean": 1.0, "ratio": 0.5},
                "coordinate_variance": [{"ratio": 1.0, "passed": True}] * 27,
                "action_sensitivity": [{"fraction": 1.0, "passed": True}] * 3,
            })
    return packets


def _synthetic_complete_count_accounting() -> dict[str, object]:
    n10_by_seed_support = {
        f"{seed_index}:{support}": 1_024
        for seed_index in config.SEED_INDICES for support in ("S0", "S1")
    }
    counters = {
        f"{seed_index}:{cell}": accounting.train_cell_examples(1_024)
        for seed_index in config.SEED_INDICES for cell in config.CELLS
    }
    return accounting.complete_count_accounting(n10_by_seed_support, counters)


def _synthetic_lease(tmp_path) -> dict[str, object]:
    return {
        "lease_kind": "SCDMP_TBOV_SRF_R03_ROOT_COMPUTE_LEASE",
        "issued_by": "operational_root", "lease_id": "synthetic-test-only",
        "direction": "semigroup_consistent_duration_model_policy",
        "candidate": config.CANDIDATE, "result_object": config.RESULT_OBJECT,
        "revision": config.REVISION, "production_authorized": True,
        "scientific_activity_authorized": True, "revoked": False,
        "authorized_seeds": list(config.SEED_INDICES), "authorized_cells": list(config.CELLS),
        "max_workers": 1, "cpu_cores": 1, "gpu_count": 0,
        "not_after_utc": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        "result_root": str(tmp_path.resolve()), "stage_boundary": config.RESULT_OBJECT,
        "stage_b_authorized": False,
    }


def _synthetic_complete_reconciliation_shape(tmp_path):
    """An output-created-before-final-frontier-update, entirely synthetic shape."""
    output = (tmp_path / "synthetic-result.json").resolve()
    frontier_path = (tmp_path / "synthetic-frontier.pt").resolve()
    sidecar = Path(str(output) + ".activity.json").resolve()
    retained_lifecycle = Lifecycle()
    retained_lifecycle.begin_panel()
    retained_lifecycle.record("synthetic_retained_frontier_event")
    retained_lifecycle.complete_cell(9, "S1R1")
    installed_lifecycle = Lifecycle.from_facts(retained_lifecycle.facts())
    installed_lifecycle.complete()
    panel_digest, seed_digests = rng.identity_digests(SYNTHETIC_MASTER)
    manifest = {
        "artifact_kind": "SCDMP_TBOV_SRF_R03_CREATE_ONLY_BLINDED_MANIFEST",
        "candidate": config.CANDIDATE,
        "result_object": config.RESULT_OBJECT,
        "revision": config.REVISION,
        "panel_digest": panel_digest,
        "seed_digests": list(seed_digests),
        "per_seed": [{"synthetic": index} for index in config.SEED_INDICES],
    }
    packets = _synthetic_packets()
    checkpoint_states = {}
    for index, (seed_index, cell) in enumerate(
            (pair for pair in ((seed, cell) for seed in config.SEED_INDICES for cell in config.CELLS))):
        state = {"synthetic_parameter": torch.tensor([float(index)], dtype=torch.float32)}
        checkpoint_states[f"{seed_index}:{cell}"] = state
        packets[index]["checkpoint_digest"] = run._checkpoint_state_digest(state)
    complete_inference = inference.complete_inference(packets)
    complete_count_accounting = _synthetic_complete_count_accounting()
    frontier = run._new_frontier(
        SYNTHETIC_MASTER, retained_lifecycle, microbatch_examples=7,
    )
    frontier.update({
        "manifest": manifest,
        "next_packet_index": len(packets),
        "cell_packets": packets,
        "cell_packet_digests": [run._cell_packet_digest(packet) for packet in packets],
        "checkpoint_states": checkpoint_states,
        "training_direct_example_counters": dict(
            complete_count_accounting["validated_executed_training_by_cell"],
        ),
        "inference": complete_inference,
        "active_cell": None,
    })
    run.save_frontier(frontier_path, frontier)
    installed = result.complete_packet(
        master_hex=SYNTHETIC_MASTER.hex(), manifest=manifest, cell_packets=packets,
        inference=complete_inference, count_accounting=complete_count_accounting,
        lifecycle=installed_lifecycle.facts(),
        frontier_path=str(frontier_path), activity_sidecar=str(sidecar),
        implementation_facts=frontier["implementation_facts"],
    )
    output.write_text(json.dumps(installed), encoding="utf-8")
    return output, frontier_path, installed


def _patch_synthetic_count_derivation(monkeypatch, canonical: dict[str, object]) -> None:
    """Keep reconciliation tests identity-free while retaining counter-pair validation."""
    canonical = copy.deepcopy(canonical)
    expected_counters = canonical["validated_executed_training_by_cell"]

    def derive(_master, frontier):
        if frontier.get("training_direct_example_counters") != expected_counters:
            raise RuntimeError("synthetic direct-counter pairing mismatch")
        return canonical

    monkeypatch.setattr(run, "_derive_complete_count_accounting", derive)


def test_r03_static_contract_is_preactivity_only_and_pro_closed() -> None:
    static = run.static_conformance()
    contract = config.static_contract()
    assert static["conforming"] is True
    assert static["scientific_activity_started"] is False
    assert static["question_relevant_output_exists"] is False
    assert static["master_seed_coordinate_scale_or_parameter_materialized"] is False
    assert static["heavy_compute_executed"] is False
    assert contract["stage_b_implemented"] is False
    assert contract["order_or_relation_observable_implemented"] is False
    assert config.RESULT_OBJECT == "SCDMP-TBOV-SRF-R02-FULL-FACTORIAL"
    assert config.REVISION == "SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260820-03"
    assert config.HMAC_SEED_NAMESPACE == b"SCDMP-TBOV-SRF-CHECKPOINT-r02/seed/"
    assert set(contract["composite_sha256"]) == {
        "base_revision_02_card", "revision_03_count_correction", "revision_03_pro_closed_intake",
    }
    assert all(static["checks"][name] is True for name in (
        "base_card_sha256_exact", "count_correction_sha256_exact",
        "pro_closed_intake_sha256_exact", "r03_expected_direct_accounting_exact",
    ))
    assert config.DIRECT_PANEL_EXPECTED_EXAMPLES == 204_697_600
    assert config.PROSPECTIVE_COST["expected_equals_realized_asserted"] is False
    assert config.HISTORICAL_SUPERSEDED_COST == {
        "revision": "SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260819-02",
        "superseded_executed_example_assertion": 224_604_160,
        "active_prospective_cost": False,
    }
    assert static["cost_conformance_fact"]["realized_direct_examples"] is None
    assert static["cost_conformance_fact"]["expectation_is_not_executed_equality"] is True


def test_exact_r03_count_formula_lattice_range_and_representation_pairing() -> None:
    assert accounting.train_cell_examples(0) == 4_945_920
    assert accounting.train_cell_examples(1_024) == 4_992_000
    assert accounting.train_cell_examples(2_048) == 5_038_080
    complete = _synthetic_complete_count_accounting()
    assert complete["sum_n10"] == 20_480
    assert complete["training_direct_examples_actual"] == 199_680_000
    assert complete["direct_panel_actual"] == 204_697_600
    assert complete["direct_panel_formula"] == "202_854_400 + 90*sum_n10"
    assert complete["lattice"] == {
        "base": 202_854_400, "step": 90,
        "sum_n10_min": 0, "sum_n10_max": 40_960,
    }
    assert complete["range"] == [202_854_400, 206_540_800]
    counters = dict(complete["validated_executed_training_by_cell"])
    counters["0:S1R1"] += 1
    with pytest.raises(RuntimeError, match=r"4_945_920 \+ 45\*n10"):
        accounting.complete_count_accounting(
            {f"{seed}:{support}": 1_024 for seed in config.SEED_INDICES
             for support in ("S0", "S1")},
            counters,
        )


def test_synthetic_fixed_bytes_follow_exact_seed_domain_hmac_law() -> None:
    seed_index = 3
    expected_seed = hmac.new(
        SYNTHETIC_MASTER,
        config.HMAC_SEED_NAMESPACE + seed_index.to_bytes(4, "big"),
        hashlib.sha256,
    ).digest()
    assert rng.seed_key(SYNTHETIC_MASTER, seed_index) == expected_seed
    label = "init/R1_context"
    expected_domain = hmac.new(expected_seed, label.encode("utf-8"), hashlib.sha256).digest()
    assert rng.domain_key(expected_seed, label) == expected_domain
    stream = rng.HMACStream.for_domain(SYNTHETIC_MASTER, seed_index, label)
    expected_block = hmac.new(expected_domain, (0).to_bytes(8, "big"), hashlib.sha256).digest()
    assert stream.raw_u64() == int.from_bytes(expected_block[:8], "big")
    assert stream.draw_count == 1
    with pytest.raises(ValueError, match="unregistered"):
        rng.domain_key(expected_seed, "r07/not-an-srf-domain")


def test_synthetic_s0_s1_allocation_and_shared_evaluation_invariants() -> None:
    value = corpus.materialize_seed(SYNTHETIC_MASTER, 0)
    assert set(value.train) == {"S0", "S1"}
    assert len(value.train["S0"]) == len(value.train["S1"]) == config.TRAIN_ROWS
    assert len(value.fit_support) == config.FIT_SUPPORT_ROWS
    assert {k: len(rows) for k, rows in value.targets.items()} == {
        k: config.TARGET_BASE_ROWS for k in config.K_TARGET
    }
    s0_words = Counter((row.k, row.sigma, row.gamma, row.orientation) for row in value.train["S0"])
    assert set(s0_words.values()) == {config.S1_WORD_CELL_ROWS}
    for word_cell in corpus.word_cell_order(config.K_FIT):
        action_counts = Counter(
            row.action_index for row in value.train["S1"]
            if (row.k, row.sigma, row.gamma, row.orientation) == word_cell
        )
        assert len(action_counts) == len(config.ACTIONS)
        assert set(action_counts.values()) <= {3, 4}
        assert sum(count == 4 for count in action_counts.values()) == config.S1_ACTION_EXTRAS
    s1_states = np.asarray([row.state for row in value.train["S1"]])
    for coordinate, (low, high) in enumerate(config.STATE_BOUNDS):
        strata = np.floor(
            (s1_states[:, coordinate] - low) / (high - low) * config.TRAIN_ROWS,
        ).astype(np.int64)
        assert set(strata) == set(range(config.TRAIN_ROWS))
    assert len(value.evaluation_identity) == 64
    assert all(name.startswith("eval/") for name in (
        name for name in value.block_hashes if name.startswith("eval/")
    ))
    assert value.evaluation_identity != value.block_hashes["train/S0/state"]


def test_parameter_specs_gru_equations_and_paired_synthetic_clones() -> None:
    assert config.MODEL_PARAMETER_COUNTS == {"R0": 97_706, "R1": 101_258}
    assert sum(parameter.numel() for parameter in model.SegmentModel("R0").parameters()) == 97_706
    assert sum(parameter.numel() for parameter in model.SegmentModel("R1").parameters()) == 101_258
    source = inspect.getsource(model.SegmentModel.forward)
    for required in (
        "F.silu(F.linear(q0, self.W_c, self.b_c))",
        "torch.sigmoid(",
        "reset * F.linear(hidden, self.W_hn, self.b_hn)",
        "(1.0 - update) * candidate_gate + update * hidden",
        "torch.where(active, candidate, hidden)",
    ):
        assert required in source
    clones, facts = model.initialized_representation_pair(
        rng.HMACStream.for_domain(SYNTHETIC_MASTER, 0, "init/shared"),
        rng.HMACStream.for_domain(SYNTHETIC_MASTER, 0, "init/R0_input"),
        rng.HMACStream.for_domain(SYNTHETIC_MASTER, 0, "init/R1_context"),
        rng.HMACStream.for_domain(SYNTHETIC_MASTER, 0, "init/R1_input"),
    )
    assert facts["support_clone_identity"] == {"R0": True, "R1": True}
    assert model.model_state_digest(clones["S0R0"]) == model.model_state_digest(clones["S1R0"])
    assert model.model_state_digest(clones["S0R1"]) == model.model_state_digest(clones["S1R1"])
    for name, _shape in config.SHARED_MATRIX_SPECS:
        assert torch.equal(getattr(clones["S0R0"], name), getattr(clones["S0R1"], name))
    assert clones["S0R0"].W_ir.shape == (32, 5)
    assert clones["S0R1"].W_ir.shape == (32, 37)
    assert clones["S0R1"].W_c.shape == (32, 14)


def test_minibatch_and_adamw_rules_use_synthetic_only_state() -> None:
    plan = training.MinibatchPlan(
        rng.HMACStream.for_domain(SYNTHETIC_MASTER, 0, "minibatch/S0"),
    )
    first_epoch = [plan.rows_for_step(step) for step in range(1, 17)]
    assert all(len(batch) == config.LOGICAL_BATCH_ROWS for batch in first_epoch)
    assert len(set(np.concatenate(first_epoch).tolist())) == config.TRAIN_ROWS
    assert np.array_equal(plan.rows_for_step(1), plan.rows_for_step(1))
    assert not np.array_equal(plan.rows_for_step(1), plan.rows_for_step(17))

    class SyntheticOptimizerModel:
        representation = "R0"

        def __init__(self) -> None:
            self.parameter = torch.nn.Parameter(torch.tensor([1.0], dtype=torch.float32))

        def ordered_parameters(self):
            return (self.parameter,)

    synthetic = SyntheticOptimizerModel()
    optimizer = training.ExactAdamW(synthetic)  # type: ignore[arg-type]
    synthetic.parameter.grad = torch.tensor([2.0], dtype=torch.float32)
    optimizer.step(1)
    expected = (1.0 * (1.0 - config.ADAMW.learning_rate * config.ADAMW.weight_decay)
                - config.ADAMW.learning_rate / (1.0 + config.ADAMW.epsilon))
    assert optimizer.step_number == 1
    assert float(synthetic.parameter.detach().item()) == pytest.approx(expected, rel=0, abs=1e-7)
    assert float(optimizer.m[0].item()) == pytest.approx(0.1)
    assert float(optimizer.v[0].item()) == pytest.approx(0.001)
    with pytest.raises(ValueError, match="consecutive"):
        optimizer.step(3)


def test_pure_inference_branches_modifiers_and_atomic_result_guard() -> None:
    packets = _synthetic_packets()
    complete = inference.complete_inference(packets)
    count_accounting = _synthetic_complete_count_accounting()
    assert complete["measurement_valid"] is True
    assert complete["branch"] == "NO-USEFUL-FACTOR-EFFECT"
    assert complete["competence_modifier"] == "ALL-CELLS-COMPETENT"
    assert complete["partial_inspection_permitted"] is False
    invalid = inference.complete_inference(packets[:-1])
    assert invalid["branch"] == "FACTORIAL-MEASUREMENT-NONIDENTIFICATION"
    assert invalid["competence_modifier"] == "COMPETENCE-VECTOR-UNAVAILABLE"
    with pytest.raises(ValueError, match="40-checkpoint"):
        result.complete_packet(
            master_hex="00" * 32,
            manifest={}, cell_packets=packets[:-1], inference=complete,
            count_accounting=count_accounting,
            lifecycle={}, frontier_path="synthetic-frontier", activity_sidecar="synthetic-sidecar",
            implementation_facts={},
        )
    packet = result.complete_packet(
        master_hex="00" * 32,
        manifest={}, cell_packets=packets, inference=complete, lifecycle={},
        count_accounting=count_accounting,
        frontier_path="synthetic-frontier", activity_sidecar="synthetic-sidecar",
        implementation_facts={},
    )
    assert packet["complete"] is True
    assert len(packet["cell_packets"]) == 40
    assert packet["count_accounting"] == count_accounting
    assert "count_accounting" not in packet["inference"]
    assert "count_accounting" not in packet["selected_branch"]
    assert "count_accounting" not in packet["competence_modifier"]
    assert all("count" not in cell_packet for cell_packet in packet["cell_packets"])


def test_synthetic_lease_activity_order_and_blinded_frontier_guards(tmp_path) -> None:
    lifecycle = Lifecycle()
    assert lifecycle.facts()["scientific_activity_started"] is False
    lifecycle.begin_panel()
    with pytest.raises(RuntimeError, match="only once"):
        lifecycle.begin_panel()
    lease_path = tmp_path / "synthetic-lease.json"
    lease = _synthetic_lease(tmp_path)
    lease_path.write_text(json.dumps(lease), encoding="utf-8")
    assert run._validate_lease(lease_path, tmp_path)["lease_id"] == "synthetic-test-only"
    frontier = run._new_frontier(SYNTHETIC_MASTER, lifecycle, microbatch_examples=7)
    frontier_path = tmp_path / "synthetic-frontier.pt"
    run.save_frontier(frontier_path, frontier)
    restored = run.load_frontier(frontier_path)
    assert run._validate_frontier_identity(restored) == SYNTHETIC_MASTER
    assert restored["partial_inspection_permitted"] is False
    corrupted = dict(restored)
    corrupted["cell_packets"] = [{
        "seed_index": 0, "cell": "S0R0", "synthetic": "packet",
    }]
    corrupted["cell_packet_digests"] = ["not-a-matching-digest"]
    corrupted["training_direct_example_counters"] = {"0:S0R0": 0}
    corrupted["next_packet_index"] = 1
    with pytest.raises(RuntimeError, match="changed after installation"):
        run._validate_cell_packet_frontier(corrupted)
    corrupted_identity = dict(restored)
    corrupted_identity["panel_digest"] = "0" * 64
    with pytest.raises(RuntimeError, match="identity digests disagree"):
        run._validate_frontier_identity(corrupted_identity)


def test_crashed_crossed_boundary_sidecar_fails_closed_without_new_master(
        monkeypatch, tmp_path) -> None:
    """A synthetic crash after durable crossed-boundary publication is non-resumable."""
    output = (tmp_path / "synthetic-result.json").resolve()
    frontier_path = (tmp_path / "synthetic-frontier.pt").resolve()
    manifest_root = (tmp_path / "synthetic-manifests").resolve()
    lease_path = tmp_path / "synthetic-lease.json"
    lease_path.write_text(json.dumps(_synthetic_lease(tmp_path)), encoding="utf-8")
    sidecar = Path(str(output) + ".activity.json").resolve()
    original_replace = run._atomic_replace_json

    def crash_after_crossed_boundary(path, value) -> None:
        original_replace(path, value)
        lifecycle = value.get("lifecycle") if isinstance(value, dict) else None
        if Path(path).resolve() == sidecar and isinstance(lifecycle, dict) \
                and lifecycle.get("scientific_activity_started") is True:
            raise RuntimeError("synthetic crash after durable crossed-boundary sidecar")

    sampled: list[object] = []

    def must_not_sample(*args, **kwargs):
        sampled.append((args, kwargs))
        pytest.fail("fresh synthetic master sampling occurred after the durable boundary")

    monkeypatch.setattr(run, "_atomic_replace_json", crash_after_crossed_boundary)
    monkeypatch.setattr(run, "sample_fresh_master", must_not_sample)
    with pytest.raises(RuntimeError, match="durable crossed-boundary"):
        run.production(
            output=output, frontier_path=frontier_path, manifest_root=manifest_root,
            lease_path=lease_path, resume=False,
        )
    assert sampled == [] and sidecar.exists() and not frontier_path.exists()
    monkeypatch.setattr(run, "_atomic_replace_json", original_replace)
    with pytest.raises(RuntimeError, match="does not durably prove preactivity"):
        run.production(
            output=output, frontier_path=frontier_path, manifest_root=manifest_root,
            lease_path=lease_path, resume=False,
        )
    assert sampled == []


def test_reconciliation_accepts_only_exact_output_before_final_frontier_update(
        monkeypatch, tmp_path) -> None:
    output, frontier_path, installed = _synthetic_complete_reconciliation_shape(tmp_path)
    _patch_synthetic_count_derivation(monkeypatch, installed["count_accounting"])
    assert run._reconcile_installed_result(output, frontier_path, installed) == installed
    retained = run.load_frontier(frontier_path)
    assert retained["final_result"] == str(output)
    assert retained["question_relevant_output_exists"] is True
    assert json.loads(Path(str(output) + ".activity.json").read_text(encoding="utf-8"))[
        "final_result_installed"
    ] is True


@pytest.mark.parametrize(
    "mismatch",
    (
        "canonical_cell_packet", "inference", "branch", "modifier", "manifest",
        "incomplete_frontier", "active_frontier", "checkpoint_key_set",
        "inserted_retained_event", "reordered_retained_event", "removed_retained_event",
        "duplicate_terminal_completion", "count_formula", "count_counter", "count_pairing",
    ),
)
def test_reconciliation_rejects_synthetic_noncanonical_complete_shapes(
        monkeypatch, tmp_path, mismatch: str) -> None:
    output, frontier_path, installed = _synthetic_complete_reconciliation_shape(tmp_path)
    _patch_synthetic_count_derivation(monkeypatch, installed["count_accounting"])
    frontier = run.load_frontier(frontier_path)
    if mismatch == "canonical_cell_packet":
        installed["cell_packets"][0]["fit_support"]["ratio"] = 0.51
    elif mismatch == "inference":
        installed["inference"] = {"synthetic": "not-the-frontier-inference"}
    elif mismatch == "branch":
        installed["selected_branch"] = "INTERACTION-EFFECT"
    elif mismatch == "modifier":
        installed["competence_modifier"] = "NO-COMPETENT-CELL"
    elif mismatch == "manifest":
        installed["manifest"]["panel_digest"] = "0" * 64
    elif mismatch == "incomplete_frontier":
        frontier["next_packet_index"] = 39
    elif mismatch == "active_frontier":
        frontier["active_cell"] = {"synthetic": "unfinished"}
    elif mismatch == "checkpoint_key_set":
        frontier["checkpoint_states"].pop("0:S0R0")
    elif mismatch == "inserted_retained_event":
        installed["lifecycle"]["events"].insert(1, {
            "event": "synthetic_inserted_event", "utc": "test-only",
        })
    elif mismatch == "reordered_retained_event":
        events = installed["lifecycle"]["events"]
        events[0], events[1] = events[1], events[0]
    elif mismatch == "removed_retained_event":
        installed["lifecycle"]["events"].pop(1)
    elif mismatch == "duplicate_terminal_completion":
        installed["lifecycle"]["events"].append(
            dict(installed["lifecycle"]["events"][-1]),
        )
    elif mismatch == "count_formula":
        installed["count_accounting"]["direct_panel_formula"] = "tampered formula"
    elif mismatch == "count_counter":
        installed["count_accounting"]["direct_panel_actual"] = 0
    else:
        frontier["training_direct_example_counters"]["0:S1R1"] += 1
    run.save_frontier(frontier_path, frontier)
    with pytest.raises(RuntimeError):
        run._reconcile_installed_result(output, frontier_path, installed)
