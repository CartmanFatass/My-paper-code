from __future__ import annotations

import hashlib
import hmac
import json
import math
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
import torch

import experiments.candidates.scdmp_variable_k.target_bound_order_to_value.checkpoint \
    as checkpoint_module
import experiments.candidates.scdmp_variable_k.target_bound_order_to_value.run as run_module

from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.assay import (
    target_population,
)
from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.checkpoint import (
    ExactAdamW, MinibatchPlan,
)
from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.config import (
    ACTIONS, CANDIDATE, HMAC_SEED_NAMESPACE, MODEL_PARAMETER_COUNT, PHYSICAL_MARGINS, REVISION,
)
from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.corpus import (
    Row, materialize_seed, segment_examples,
)
from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.dgp import (
    lexargmax, order_blind_oracle, rollout, words,
)
from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.inference import (
    complete_inference,
)
from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.frontier import (
    atomic_save as save_frontier, load as load_frontier,
)
from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.model import (
    SegmentModel, model_state_digest,
)
from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.rng import (
    HMACStream, balanced_roster, identity_digests, sample_fresh_master, seed_key,
)
from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.run import (
    _reconcile_installed_result, _validate_lease, static_conformance,
)

SYNTHETIC_MASTER = bytes(range(32))


def test_static_surface_is_exact_stage_a_and_preactivity() -> None:
    value = static_conformance()
    assert value["conforming"] is True
    assert value["scientific_activity_started"] is False
    assert value["heavy_compute_executed"] is False
    assert value["static_contract"]["stage_b_implemented"] is False
    assert value["static_contract"]["hmac_seed_namespace"] \
        == "SCDMP-TBOV-r06/STAGE-A/seed/"
    assert value["static_contract"]["optimizer"]["batch_index"] == "b=n-1 for n=1,...,600"
    assert value["static_contract"]["optimizer"]["checkpoint"] == "theta_600"


def test_hmac_seed_namespace_stream_and_balanced_roster_are_exact() -> None:
    expected_key = hmac.new(
        SYNTHETIC_MASTER, HMAC_SEED_NAMESPACE + (3).to_bytes(4, "big"), hashlib.sha256,
    ).digest()
    assert seed_key(SYNTHETIC_MASTER, 3) == expected_key
    domain = hmac.new(expected_key, b"checkpoint_fit/cells", hashlib.sha256).digest()
    expected_block = hmac.new(domain, (0).to_bytes(8, "big"), hashlib.sha256).digest()
    stream = HMACStream.for_domain(SYNTHETIC_MASTER, 3, "checkpoint_fit/cells")
    assert stream.raw_u64() == int.from_bytes(expected_block[:8], "big")
    assert stream.raw_u64() == int.from_bytes(expected_block[8:16], "big")
    roster = balanced_roster((0, 1, 2), 11, stream)
    counts = {item: roster.count(item) for item in (0, 1, 2)}
    assert max(counts.values()) - min(counts.values()) <= 1
    assert sorted(roster) == sorted(roster.copy())


def test_master_collision_rejection_consumes_next_complete_candidate() -> None:
    first = b"A" * 32
    second = b"B" * 32
    first_panel, _ = identity_digests(first)
    draws = iter((first, second))
    accepted = sample_fresh_master({first_panel}, lambda count: next(draws))
    assert accepted == second


def test_synthetic_corpus_is_reproducible_balanced_and_disjoint_by_domain() -> None:
    first = materialize_seed(SYNTHETIC_MASTER, 0)
    second = materialize_seed(SYNTHETIC_MASTER, 0)
    assert first.block_hashes == second.block_hashes
    assert first.draw_counts == second.draw_counts
    assert len(first.fit) == 4_096 and len(first.fit_support) == 1_024
    assert {k: len(rows) for k, rows in first.targets.items()} == {6: 256, 8: 256, 12: 256}
    fit_cells = [(row.k, row.sigma, row.gamma, row.orientation) for row in first.fit]
    assert len(set(fit_cells)) == 16
    assert len({fit_cells.count(cell) for cell in set(fit_cells)}) == 1
    assert first.block_hashes["checkpoint_fit/state"] \
        != first.block_hashes["fit_support/state"]
    assert all(row.action_index is None for rows in first.targets.values() for row in rows)


def test_word_physics_is_order_changing_and_oracles_tie_lexicographically() -> None:
    state = np.zeros(9, dtype=np.float64)
    state[4] = -0.2
    action = (0, 0, 0, 0)
    forward, reverse = words(6, 1, 1)
    f_out = rollout(state, action, forward)
    r_out = rollout(state, action, reverse)
    assert not np.allclose(f_out.terminal, r_out.terminal)
    assert lexargmax(np.zeros(81)) == 0
    assert order_blind_oracle(np.zeros(81), np.zeros(81)) == 0


def test_segment_row_atom_weights_are_equal_by_row_not_by_atom() -> None:
    state = np.zeros(9, dtype=np.float64)
    rows = [
        Row(0, state, 4, -1, -1, "F", 0),
        Row(1, state, 10, 1, 1, "R", 80),
    ]
    examples = segment_examples(rows)
    assert len(examples.weights) == 10 + 55
    assert np.sum(examples.weights[:10]) == pytest.approx(0.5)
    assert np.sum(examples.weights[10:]) == pytest.approx(0.5)
    assert np.sum(examples.weights) == pytest.approx(1.0)


def test_model_initialization_is_exact_and_padding_has_no_semantic_effect() -> None:
    first_stream = HMACStream.for_domain(SYNTHETIC_MASTER, 0, "checkpoint_init")
    second_stream = HMACStream.for_domain(SYNTHETIC_MASTER, 0, "checkpoint_init")
    first, second = SegmentModel(), SegmentModel()
    first.exact_initialize(first_stream)
    second.exact_initialize(second_stream)
    assert sum(parameter.numel() for parameter in first.parameters()) == MODEL_PARAMETER_COUNT
    assert model_state_digest(first) == model_state_digest(second)
    state = torch.zeros((1, 9), dtype=torch.float32)
    action = torch.zeros((1, 4), dtype=torch.float32)
    short = torch.tensor([[0, 1]], dtype=torch.long)
    padded = torch.tensor([[0, 1, 4, 3]], dtype=torch.long)
    length = torch.tensor([2])
    f_short, g_short = first(state, action, short, length)
    f_padded, g_padded = first(state, action, padded, length)
    assert torch.equal(f_short, f_padded)
    assert torch.equal(g_short, g_padded)


def test_minibatch_plan_separates_one_based_step_from_zero_based_batch() -> None:
    plan = MinibatchPlan(HMACStream.for_domain(SYNTHETIC_MASTER, 0, "checkpoint_minibatch"))
    assert len(plan.rows_for_step(1)) == 256
    assert np.array_equal(plan.rows_for_step(1), plan.permutations[0][:256])
    assert np.array_equal(plan.rows_for_step(592), plan.permutations[36][-256:])
    assert np.array_equal(plan.rows_for_step(593), plan.permutations[37][:256])
    assert np.array_equal(plan.rows_for_step(600), plan.permutations[37][7 * 256:8 * 256])
    with pytest.raises(ValueError):
        plan.rows_for_step(0)


def test_exact_adamw_uses_first_bias_correction_at_n_one() -> None:
    model = SegmentModel()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.fill_(1.0)
    optimizer = ExactAdamW(model)
    for parameter in optimizer.parameters:
        parameter.grad = torch.zeros_like(parameter)
    optimizer.parameters[0].grad.view(-1)[0] = 0.5
    initial = float(optimizer.parameters[0].view(-1)[0])
    norm = optimizer.step(1)
    assert norm == pytest.approx(0.5)
    expected = initial * (1.0 - 3.0e-4 * 1.0e-5) - 3.0e-4 * 0.5 / (0.5 + 1.0e-8)
    assert float(optimizer.parameters[0].view(-1)[0]) == pytest.approx(expected, abs=2e-7)
    assert optimizer.step_number == 1
    with pytest.raises(ValueError):
        optimizer.step(1)


def test_correct_and_reversed_paths_swap_with_presented_twin() -> None:
    stream = HMACStream.for_domain(SYNTHETIC_MASTER, 0, "checkpoint_init")
    model = SegmentModel()
    model.exact_initialize(stream)
    row = Row(0, np.zeros(9, dtype=np.float64), 6, 1, -1, "F", None)
    population = target_population(model, (row,), 6)
    assert np.allclose(population.correct_f[0, 0], population.reversed_f[0, 1])
    assert np.allclose(population.correct_g[0, 0], population.reversed_g[0, 1])
    assert np.allclose(population.reversed_f[0, 0], population.correct_f[0, 1])
    assert np.allclose(population.reversed_g[0, 0], population.correct_g[0, 1])


def _seed_result(seed: int, *, t: float = 1.0, r: float = 1.0, a: float = 2.0,
                 h: float = 1.0, df: float = 0.3, dr: float = 0.3,
                 dq: float = 0.2, competence: bool = True) -> dict[str, object]:
    physical = {}
    for name in PHYSICAL_MARGINS:
        physical[name] = t if name.startswith("T_") else r if name.startswith("R_") else a
    return {
        "seed_index": seed,
        "physical": physical,
        "per_k": {str(k): {"h": h} for k in (6, 8, 12)},
        "pooled": {"dF": df, "dR": dr, "dQ": dq},
        "competence": {
            "fit_support": {"passed": competence},
            "target": {"ratio": 0.1},
            "coordinate_variance": [{"passed": competence}] * 27,
            "action_sensitivity": [{"passed": competence}] * 3,
        },
    }


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"t": 0.0}, "DELETE-FROM-OBJECT--PHYSICAL-OPPORTUNITY-EXCLUDED"),
        ({"t": 0.12}, "PHYSICAL-OPPORTUNITY-INDETERMINATE"),
        ({"h": 0.0}, "STAGE-A-ASSAY-DENOMINATOR-NONIDENTIFICATION"),
        ({"competence": False}, "MODIFY-CHECKPOINT"),
        ({"dq": -0.10}, "ASSAY-ACTION-ADVERSE--DELETE-FROM-OBJECT"),
        ({}, "SELECT-ORDER-TR"),
        ({"dq": 0.0}, "MODIFY-TO-ORDER-Q"),
        ({"df": 0.0}, "ASSAY-NEGATIVE--DELETE-FROM-OBJECT"),
        ({"df": 0.10, "dr": 0.10, "dq": 0.07}, "ASSAY-INDETERMINATE"),
    ],
)
def test_all_nine_first_true_branches(changes: dict[str, object], expected: str) -> None:
    rows = [_seed_result(seed, **changes) for seed in range(10)]
    assert complete_inference(rows)["branch"] == expected


def test_production_lease_must_name_exact_revision_stage_and_result_root(tmp_path: Path) -> None:
    result_root = tmp_path / "result"
    lease = {
        "direction": "semigroup_consistent_duration_model_policy",
        "revision": REVISION,
        "production_authorized": True,
        "authorized_seeds": list(range(10)),
        "max_workers": 1,
        "cpu_cores": 1,
        "gpu_count": 0,
        "not_after_utc": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "result_root": str(result_root),
        "stage_boundary": "complete exact Stage A atomic panel",
    }
    path = tmp_path / "lease.json"
    path.write_text(json.dumps(lease), encoding="utf-8")
    assert _validate_lease(path, result_root)["revision"] == REVISION
    lease["revision"] = "SCDMP-TBOV-SCIENCE-20260815-06"
    path.write_text(json.dumps(lease), encoding="utf-8")
    with pytest.raises(RuntimeError, match="does not authorize exact r07 Stage A"):
        _validate_lease(path, result_root)


def test_stage_a_lease_accepts_explicit_stage_b_prohibition(tmp_path: Path) -> None:
    result_root = tmp_path / "result"
    lease = _lease(result_root)
    lease["stage_boundary"] = (
        "Complete exact r07 Stage A blinded atomic panel only; "
        "Stage B is not authorized."
    )
    path = tmp_path / "lease.json"
    path.write_text(json.dumps(lease), encoding="utf-8")
    assert _validate_lease(path, result_root)["stage_boundary"] == lease["stage_boundary"]


def _lease(result_root: Path) -> dict[str, object]:
    return {
        "direction": "semigroup_consistent_duration_model_policy",
        "revision": REVISION,
        "production_authorized": True,
        "revoked": False,
        "authorized_seeds": list(range(10)),
        "max_workers": 1,
        "cpu_cores": 1,
        "gpu_count": 0,
        "not_after_utc": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "result_root": str(result_root.resolve()),
        "stage_boundary": "complete exact Stage A atomic panel",
    }


def test_revoked_or_expired_lease_fails_closed(tmp_path: Path) -> None:
    result_root = tmp_path / "result"
    path = tmp_path / "lease.json"
    lease = _lease(result_root)
    lease["revoked"] = True
    path.write_text(json.dumps(lease), encoding="utf-8")
    with pytest.raises(RuntimeError, match="does not authorize exact r07 Stage A"):
        _validate_lease(path, result_root)
    lease["revoked"] = False
    lease["not_after_utc"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    path.write_text(json.dumps(lease), encoding="utf-8")
    with pytest.raises(RuntimeError, match="does not authorize exact r07 Stage A"):
        _validate_lease(path, result_root)


def test_checkpoint_calls_lease_guard_before_every_synthetic_logical_step(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(checkpoint_module, "LOGICAL_STEPS", 3)
    monkeypatch.setattr(checkpoint_module, "direct_loss", lambda *args, **kwargs: 0.5)

    class Optimizer:
        step_number = 0

        def zero_grad(self) -> None:
            pass

        def step(self, n: int) -> float:
            self.step_number = n
            return 1.0

    class Plan:
        @staticmethod
        def rows_for_step(n: int) -> int:
            return n

    class Store:
        @staticmethod
        def logical_batch(rows: int) -> int:
            return rows

    checked: list[int] = []
    completed: list[int] = []

    def before_step(n: int) -> None:
        checked.append(n)
        if n == 2:
            raise RuntimeError("synthetic lease revoked")

    optimizer = Optimizer()
    with pytest.raises(RuntimeError, match="synthetic lease revoked"):
        checkpoint_module.train_checkpoint(
            object(), optimizer, Plan(), Store(), np.ones(1), np.float32(1.0),
            before_step=before_step,
            on_step=lambda n, *_args: completed.append(n),
        )
    assert checked == [1, 2]
    assert completed == [1]
    assert optimizer.step_number == 1


def test_production_revocation_preserves_last_complete_synthetic_step(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = (tmp_path / "result" / "result.json").resolve()
    frontier_path = (tmp_path / "frontier.pt").resolve()
    manifest_root = (tmp_path / "manifests").resolve()
    lease_path = (tmp_path / "lease.json").resolve()
    panel_digest, seed_digests = identity_digests(SYNTHETIC_MASTER)
    lifecycle = run_module.Lifecycle()
    lifecycle.begin_panel()
    frontier = {
        "candidate": CANDIDATE, "revision": REVISION, "stage": "STAGE_A_ONLY",
        "partial_selection_permitted": False,
        "master_M_hex_sealed": SYNTHETIC_MASTER.hex(),
        "panel_digest": panel_digest, "seed_digests": list(seed_digests),
        "manifest": {"panel_digest": panel_digest, "seed_digests": list(seed_digests)},
        "next_seed_index": 0, "active_seed": None, "seed_results": [],
        "checkpoint_states": {}, "lifecycle": lifecycle.facts(), "anomalies": [],
        "implementation_facts": {"microbatch_examples": 2_048},
    }
    save_frontier(frontier_path, frontier)
    lease = _lease(output.parent)
    lease_path.write_text(json.dumps(lease), encoding="utf-8")

    class Model:
        completed_step = 0

        def exact_initialize(self, _stream: object) -> None:
            pass

        def load_state_dict(self, state: dict[str, object]) -> None:
            self.completed_step = int(state["completed_step"])

    class Optimizer:
        step_number = 0

        def __init__(self, _model: Model) -> None:
            pass

        def state_dict(self) -> dict[str, object]:
            return {"step_number": self.step_number}

        def load_state_dict(self, state: dict[str, object]) -> None:
            self.step_number = int(state["step_number"])

    def synthetic_train(model: Model, optimizer: Optimizer, _plan: object, _store: object,
                        _scale_f: object, _scale_g: object, *, first_step: int,
                        before_step, on_step, microbatch_examples: int) -> None:
        assert first_step == 1 and microbatch_examples == 2_048
        before_step(1)
        model.completed_step = optimizer.step_number = 1
        on_step(1, model, optimizer, 0.25, 0.5)
        lease["revoked"] = True
        lease_path.write_text(json.dumps(lease), encoding="utf-8")
        before_step(2)

    monkeypatch.setattr(run_module, "materialize_seed", lambda *_args: SimpleNamespace(fit=()))
    monkeypatch.setattr(run_module, "output_scales", lambda _fit: (None, None))
    monkeypatch.setattr(run_module, "HMACStream", SimpleNamespace(for_domain=lambda *_args: object()))
    monkeypatch.setattr(run_module, "SegmentModel", Model)
    monkeypatch.setattr(run_module, "MinibatchPlan", lambda _stream: object())
    monkeypatch.setattr(run_module, "ExactAdamW", Optimizer)
    monkeypatch.setattr(run_module, "SegmentStore", lambda _fit: object())
    monkeypatch.setattr(run_module, "train_checkpoint", synthetic_train)
    monkeypatch.setattr(
        run_module, "model_state",
        lambda model: {"completed_step": model.completed_step},
    )
    monkeypatch.setattr(
        run_module, "sample_fresh_master",
        lambda *_args: pytest.fail("resume sampled a new panel identity"),
    )
    monkeypatch.setattr(
        run_module, "evaluate_seed",
        lambda *_args: pytest.fail("assay ran after lease revocation"),
    )

    with pytest.raises(RuntimeError, match="does not authorize exact r07 Stage A"):
        run_module.production(
            output=output, frontier_path=frontier_path, manifest_root=manifest_root,
            lease_path=lease_path, resume=True,
        )
    retained = load_frontier(frontier_path)
    assert retained["master_M_hex_sealed"] == SYNTHETIC_MASTER.hex()
    assert retained["next_seed_index"] == 0
    assert retained["active_seed"]["next_step"] == 2
    assert retained["active_seed"]["optimizer_state"]["step_number"] == 1
    assert retained["active_seed"]["last_complete_step_facts"]["n"] == 1
    assert not output.exists()

    lease["revoked"] = False
    lease_path.write_text(json.dumps(lease), encoding="utf-8")
    assert _validate_lease(lease_path, output.parent)["revision"] == REVISION


def _synthetic_complete_result(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    output = (tmp_path / "result.json").resolve()
    frontier_path = (tmp_path / "frontier.pt").resolve()
    sidecar_path = Path(str(output) + ".activity.json").resolve()
    panel_digest, seed_digests = identity_digests(SYNTHETIC_MASTER)
    frontier = {
        "candidate": CANDIDATE, "revision": REVISION, "stage": "STAGE_A_ONLY",
        "partial_selection_permitted": False,
        "master_M_hex_sealed": SYNTHETIC_MASTER.hex(),
        "panel_digest": panel_digest, "seed_digests": list(seed_digests),
        "manifest": {"panel_digest": panel_digest, "seed_digests": list(seed_digests)},
        "lifecycle": {"phase": "target_support_and_assay"},
    }
    save_frontier(frontier_path, frontier)
    installed = {
        "artifact_kind": "SCDMP_TBOV_R07_COMPLETE_STAGE_A_RESULT",
        "candidate": CANDIDATE, "revision": REVISION, "stage": "STAGE_A_ONLY",
        "complete": True, "partial_selection_permitted": False,
        "master_M_hex_revealed_only_in_complete_result": SYNTHETIC_MASTER.hex(),
        "manifest": {"panel_digest": panel_digest, "seed_digests": list(seed_digests)},
        "lifecycle": {"phase": "complete"},
        "retained_frontier": str(frontier_path), "activity_sidecar": str(sidecar_path),
        "stage_b": None, "stage_b_implemented_or_executed": False,
    }
    return output, frontier_path, installed


def test_existing_complete_result_reconciles_only_exact_synthetic_frontier(
        tmp_path: Path) -> None:
    output, frontier_path, installed = _synthetic_complete_result(tmp_path)
    assert _reconcile_installed_result(output, frontier_path, installed) == installed
    retained = load_frontier(frontier_path)
    assert retained["final_result"] == str(output)
    assert retained["question_relevant_output_exists"] is True
    assert json.loads(Path(str(output) + ".activity.json").read_text(encoding="utf-8")) \
        ["final_result_installed"] is True


@pytest.mark.parametrize("mismatch", ("panel_digest", "seed_digests", "frontier_path"))
def test_existing_complete_result_identity_mismatch_cannot_update_frontier(
        tmp_path: Path, mismatch: str) -> None:
    output, frontier_path, installed = _synthetic_complete_result(tmp_path)
    if mismatch == "panel_digest":
        installed["manifest"]["panel_digest"] = "wrong-panel"
    elif mismatch == "seed_digests":
        installed["manifest"]["seed_digests"][0] = "wrong-seed"
    else:
        installed["retained_frontier"] = str((tmp_path / "other-frontier.pt").resolve())
    with pytest.raises(RuntimeError, match="result/frontier identity mismatch"):
        _reconcile_installed_result(output, frontier_path, installed)
    retained = load_frontier(frontier_path)
    assert "final_result" not in retained
    assert not Path(str(output) + ".activity.json").exists()
