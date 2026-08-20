from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math

import numpy as np
import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration_cpc.authorization import (
    ProductionPermit, load_production_permit, require_active_permit,
)
from experiments.candidates.roster_consistent_latent_exploration_cpc import artifacts
from experiments.candidates.roster_consistent_latent_exploration_cpc import runner as runner_module
from experiments.candidates.roster_consistent_latent_exploration_cpc.artifacts import (
    create_result_root, load_seed_packet, write_analysis, write_atomic_seed_packet,
)
from experiments.candidates.roster_consistent_latent_exploration_cpc.certificate import build_certificate, write_certificate
from experiments.candidates.roster_consistent_latent_exploration_cpc.config import ARMS, REGISTERED, REVISION, SEEDS
from experiments.candidates.roster_consistent_latent_exploration_cpc.host import (
    EpisodeBatch, RELAY, SENSOR, evaluate_outcomes, scripted_oracle_actions,
)
from experiments.candidates.roster_consistent_latent_exploration_cpc.inference import (
    _analyze_packet_payloads, _strictly_above, _strictly_below, analyze_packets,
)
from experiments.candidates.roster_consistent_latent_exploration_cpc.models import (
    ArmModel, actor_inputs, inverse_cdf, sparsemax,
)
from experiments.candidates.roster_consistent_latent_exploration_cpc.resources import resource_proposal
from experiments.candidates.roster_consistent_latent_exploration_cpc.rng import generator
from experiments.candidates.roster_consistent_latent_exploration_cpc.runner import RuntimeGuard, _rss_bytes
from experiments.candidates.roster_consistent_latent_exploration_cpc.training import (
    CellData, TrainingResult, complete_gradient, normalized_joint_update, rollout,
)


def _batch(n: int = 5, handoff: bool = True, size: int = 4) -> EpisodeBatch:
    base_roles = np.asarray([SENSOR] * ((n + 1) // 2) + [RELAY] * (n // 2), dtype=np.int64)
    roles = np.broadcast_to(base_roles, (size, n)).copy()
    clues = np.ones((size, n), dtype=np.int64)
    replaced = np.zeros((size, n), dtype=bool)
    if handoff:
        replaced[:, 0] = True
        replaced[:, -1] = True
    post_clues = clues.copy(); post_clues[replaced] = 0
    return EpisodeBatch(
        n=n, handoff=handoff, target=np.ones(size, dtype=np.int64),
        initial_roles=roles, initial_clues=clues, post_roles=roles.copy(),
        post_clues=post_clues, replaced=replaced,
    )


def _permit(tmp_path, *, authorized_seeds=SEEDS, memory_mib: int = 2048):
    certificate_path = tmp_path / "certificate.json"
    certificate = write_certificate(certificate_path)
    assert certificate["passed"]
    result_root = tmp_path / "result"
    now = datetime.now(timezone.utc)
    authorization_path = tmp_path / "authorization.json"
    authorization_path.write_text(json.dumps({
        "direction": "roster_consistent_latent_exploration",
        "revision": REVISION,
        "production_authorized": True,
        "result_root": str(result_root.resolve()),
        "max_workers": 1,
        "cpu_cores": 1,
        "gpu_count": 0,
        "memory_mib": memory_mib,
        "lease_token": "deterministic-preactivity-fixture",
        "stage_boundary": "deterministic-fixture-only",
        "issued_at_utc": (now - timedelta(minutes=1)).isoformat(),
        "not_after_utc": (now + timedelta(minutes=10)).isoformat(),
        "authorized_seeds": list(authorized_seeds),
    }), encoding="utf-8")
    permit = load_production_permit(authorization_path, result_root, certificate_path)
    return permit, certificate_path, authorization_path, result_root


def test_exact_preactivity_certificate_passes() -> None:
    certificate = build_certificate()
    assert certificate["passed"], certificate["checks"]
    assert certificate["revision"] == REVISION
    assert certificate["registered_stochastic_object_materialized"] is False
    assert certificate["registered_coordinate_materialized"] is False


def test_model_and_certificate_construction_preserve_torch_rng_state() -> None:
    before_model = torch.random.get_rng_state().clone()
    model = ArmModel()
    assert torch.equal(torch.random.get_rng_state(), before_model)
    assert all(isinstance(module, torch.nn.Linear) for module in (
        model.manager.element1, model.manager.element2, model.manager.macro,
        model.manager.refinement, model.actor.first, model.actor.second, model.actor.head,
    ))

    before_certificate = torch.random.get_rng_state().clone()
    certificate = build_certificate()
    assert certificate["passed"], certificate["checks"]
    assert torch.equal(torch.random.get_rng_state(), before_certificate)


def test_exact_fresh_registry_and_model_shape() -> None:
    assert len(SEEDS) == 16 and SEEDS[0] == 4109 and SEEDS[-1] == 5861
    assert ARMS == ("COARSE-PERSISTENT", "FLEXIBLE-PERSISTENT", "CONTEXT-SHUFFLED-COARSE")
    model = ArmModel()
    assert sum(parameter.numel() for parameter in model.manager.parameters()) == 1524
    assert model.macro_base.numel() + model.residual.numel() == 80
    assert sum(parameter.numel() for parameter in model.actor.parameters()) == 5443
    assert sum(parameter.numel() for parameter in model.parameters()) == 7047
    batch = _batch()
    common = actor_inputs(batch.initial_roles, batch.initial_clues, 0, 5, torch.zeros((4, 8), dtype=torch.float64))
    private = actor_inputs(batch.post_roles, batch.post_clues, 1, 5, torch.zeros((4, 5, 8), dtype=torch.float64))
    assert common.shape == private.shape == (4, 5, 16)


def test_registered_rng_fails_closed_without_permit() -> None:
    with pytest.raises(PermissionError):
        ProductionPermit(object(), None, None, {}, None, {})
    with pytest.raises(PermissionError):
        generator(object(), "fixture")


def test_handwritten_host_oracle_and_fragmentation() -> None:
    for n in (5, 7, 9):
        batch = _batch(n=n, size=1)
        pre, post = scripted_oracle_actions(batch)
        result = evaluate_outcomes(batch, pre, post)
        assert result.value[0] == 1.0 and result.mission[0]
        assert result.fragmentation[0] == 0.0
        holds = np.full((1, n), 2, dtype=np.int64)
        invalid = evaluate_outcomes(batch, holds, holds)
        assert invalid.fragmentation[0] == 1.0


def test_sparse_inverse_cdf_never_selects_zero_mass(tmp_path) -> None:
    permit, _, _, _ = _permit(tmp_path)
    probabilities = torch.tensor([[0.0, 0.25, 0.0, 0.75], [0.5, 0.0, 0.5, 0.0]], dtype=torch.float64)
    draws = inverse_cdf(permit, probabilities, np.asarray([0.0, 0.5]))
    assert draws.tolist() == [1, 2]
    assert torch.all(probabilities[torch.arange(2), draws] > 0)


def test_local_sparsemax_backward_is_zero_on_output_zero_coordinates() -> None:
    logits = torch.tensor([[1.0, 1.0, -2.0]], dtype=torch.float64, requires_grad=True)
    probabilities = sparsemax(logits, dim=-1)
    assert probabilities.tolist() == [[0.5, 0.5, 0.0]]
    probabilities.backward(torch.tensor([[1.0, 3.0, 100.0]], dtype=torch.float64))
    assert logits.grad.tolist() == [[-1.0, 1.0, 0.0]]


def test_active_permit_revalidates_lease_and_exact_certificate_from_disk(tmp_path) -> None:
    permit, certificate_path, authorization_path, _ = _permit(tmp_path)
    require_active_permit(permit)
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    authorization["memory_mib"] = 1024
    authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
    with pytest.raises(PermissionError, match="lease changed"):
        require_active_permit(permit)

    authorization["memory_mib"] = 2048
    authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    certificate["passed"] = False
    certificate_path.write_text(json.dumps(certificate), encoding="utf-8")
    with pytest.raises(RuntimeError, match="preactivity certificate"):
        require_active_permit(permit)


@pytest.mark.parametrize("arm", ARMS)
def test_handwritten_rollout_paths_and_shuffled_derangement(arm: str, tmp_path) -> None:
    permit, _, _, _ = _permit(tmp_path)
    batch = _batch()
    data = CellData(
        batch=batch,
        macro_uniforms=np.asarray([0.1, 0.3, 0.6, 0.9]),
        refinement_uniforms=np.asarray([0.1, 0.3, 0.6, 0.9]),
        action_uniforms=np.full((2, 4, 5), 0.2),
        cyclic_shift=1,
    )
    model = ArmModel()
    result = rollout(permit, model, arm, data)
    assert np.isfinite(result["outcomes"].value).all()
    assert result["score"].shape == (4,)
    (-result["score"].mean()).backward()
    _, gradient, _ = complete_gradient(model)
    assert gradient.numel() == REGISTERED.parameters_per_arm
    if arm == "CONTEXT-SHUFFLED-COARSE":
        assert not np.any(result["source_indices"] == np.arange(4))
    if arm != "FLEXIBLE-PERSISTENT":
        assert model.residual.grad is None
        assert model.manager.refinement.weight.grad is None


def test_complete_tensor_update_has_literal_norm_and_zero_materialization() -> None:
    model = ArmModel()
    first = next(model.parameters())
    first.grad = torch.ones_like(first)
    before = torch.cat([p.detach().reshape(-1) for p in model.parameters()])
    _, raw, registered = complete_gradient(model)
    assert raw.numel() == REGISTERED.parameters_per_arm and registered > 0
    _, _, announced = normalized_joint_update(model)
    after = torch.cat([p.detach().reshape(-1) for p in model.parameters()])
    assert announced == 0.001
    assert float(torch.linalg.vector_norm(after - before)) == pytest.approx(0.001, abs=1e-12)


def _packet(seed: int) -> dict:
    cells = {}
    for n in (5, 7, 9):
        cells[str(n)] = {}
        for handoff in ("no_handoff", "handoff"):
            cells[str(n)][handoff] = {}
            for arm in ARMS:
                sensor_total = ((n + 1) // 2) * 2048
                relay_total = (n // 2) * 2048
                cells[str(n)][handoff][arm] = {
                    "mean_value": 0.5, "mission_success": 0.1, "fragmentation": 0.4,
                    "pre_target_accuracy": 0.5, "post_target_accuracy": 0.5,
                    "pre_validity": 1.0, "post_validity": 1.0, "episodes": 2048,
                    "macro_occupancy": [1024, 1024],
                    "manager_by_clue_majority": [
                        {"majority": "LEFT", "episodes": 1024, "mean_p_macro_1": 0.5},
                        {"majority": "TIE", "episodes": 0, "mean_p_macro_1": 0.0},
                        {"majority": "RIGHT", "episodes": 1024, "mean_p_macro_1": 0.5},
                    ],
                    "source_map_fixed_points": 0 if arm == ARMS[2] else 2048,
                    "role_corridor_histograms": {
                        "PRE": [[sensor_total, 0, 0], [relay_total, 0, 0]],
                        "POST": [[sensor_total, 0, 0], [relay_total, 0, 0]],
                    },
                    "refinement_occupancy": ([256] * 8 if arm == ARMS[1] else [0] * 8),
                    "effective_cardinality": 8 if arm == ARMS[1] else 2,
                }
    return {
        "revision": REVISION, "seed": seed, "arms": list(ARMS),
        "training": {
            "updates_completed": 1000, "training_episodes": 192000,
            "optimizer_steps": 3000,
            "complete_registered_parameter_count_per_arm": REGISTERED.parameters_per_arm,
            "initial_coarse_flexible_action_distributions_bit_identical": True,
            "initial_residual_output_jacobian_nonzero": {arm: True for arm in ARMS},
            "only_evaluable_checkpoint": "immediately_after_update_1000",
            "validation_selection": False, "early_stopping": False, "checkpoint_selection": False,
        },
        "evaluation": {
            "cells": cells,
            "cuts": {
                "PRIVATE-LATENT-CUT": {"mean_value": 0.5, "mission_success": 0.1, "fragmentation": 0.4, "episodes": 2048},
                "TEMPORAL-RESET-CUT": {"mean_value": 0.5, "mission_success": 0.1, "fragmentation": 0.4, "episodes": 2048},
            },
            "ordinary_episodes": 36864, "cut_episodes": 4096,
            "evaluation_updates": 0, "heldout_training_or_adaptation": False,
            "selected_checkpoint": False, "mechanism_index": {"N": 9, "handoff": True},
        },
        "certificate_passed": True, "support_oracles_passed": True,
        "containment_and_strictness_passed": True,
        "source_revision_and_hyperparameters_exact": True,
        "partial_result_interpretation_allowed": False, "atomic_payload_complete": True,
    }


def test_complete_panel_inference_df15_and_exclusive_mechanism_cell() -> None:
    packets = [_packet(seed) for seed in SEEDS]
    for packet in packets:
        packet["evaluation"]["cells"]["9"]["no_handoff"][ARMS[1]]["fragmentation"] = 0.99
    result = _analyze_packet_payloads(packets)
    assert result["complete_panel"] and result["seed_df"] == 15
    assert result["effect_index"] == {"mechanisms": {"N": 9, "handoff": True}}
    assert result["per_seed_effects"]["FRAGMENT"] == [0.0] * 16
    assert result["branch"] == "NO_COARSE_ADVANTAGE"


def test_inference_strict_threshold_and_branch_precedence() -> None:
    for threshold in (0.06, -0.02, -0.06, 0.02, 0.08, 0.04):
        assert not _strictly_above(threshold, threshold)
        assert not _strictly_below(threshold, threshold)
        assert _strictly_above(math.nextafter(threshold, math.inf), threshold)
        assert _strictly_below(math.nextafter(threshold, -math.inf), threshold)

    packets = [_packet(seed) for seed in SEEDS]
    for packet in packets:
        packet["evaluation"]["cells"]["9"]["handoff"][ARMS[0]]["mean_value"] = 0.56
    boundary = _analyze_packet_payloads(packets)
    assert boundary["primary_rectangle"]["VALUE"]["lower"] == pytest.approx(0.06)
    assert boundary["coarse_target_win"] == (boundary["primary_rectangle"]["VALUE"]["lower"] > 0.06)

    above = copy.deepcopy(packets)
    for packet in above:
        packet["evaluation"]["cells"]["9"]["handoff"][ARMS[0]]["mean_value"] = 0.560001
    winning = _analyze_packet_payloads(above)
    assert winning["coarse_target_win"] and winning["branch"] == "COARSE_PACKAGE_ONLY"
    for packet in above:
        for n in (5, 7, 9):
            for handoff in ("no_handoff", "handoff"):
                for arm in ARMS:
                    packet["evaluation"]["cells"][str(n)][handoff][arm]["mission_success"] = 0.0
    precedence = _analyze_packet_payloads(above)
    assert precedence["coarse_target_win"]
    assert precedence["branch"] == "ALL_LEARNED_ZERO_MISSION"


def test_only_heldout_mechanism_cell_and_registered_interventions_define_effects() -> None:
    baseline_packets = [_packet(seed) for seed in SEEDS]
    baseline = _analyze_packet_payloads(baseline_packets)
    changed = copy.deepcopy(baseline_packets)
    for packet in changed:
        for n in (5, 7):
            for handoff in ("no_handoff", "handoff"):
                packet["evaluation"]["cells"][str(n)][handoff][ARMS[0]]["mean_value"] = 0.99
                packet["evaluation"]["cells"][str(n)][handoff][ARMS[1]]["fragmentation"] = 0.99
        packet["evaluation"]["cuts"]["PRIVATE-LATENT-CUT"]["mean_value"] = 0.10
        packet["evaluation"]["cuts"]["TEMPORAL-RESET-CUT"]["mean_value"] = 0.20
    result = _analyze_packet_payloads(changed)
    assert result["effect_index"] == {"mechanisms": {"N": 9, "handoff": True}}
    for effect in ("VALUE", "ROBUST", "FRAGMENT", "CONTEXT"):
        assert result["per_seed_effects"][effect] == baseline["per_seed_effects"][effect]
    assert result["per_seed_effects"]["COMMON"] == pytest.approx([0.4] * 16)
    assert result["per_seed_effects"]["PERSIST"] == pytest.approx([0.3] * 16)


def test_incomplete_panel_exposes_no_partial_values() -> None:
    result = _analyze_packet_payloads([_packet(SEEDS[0])])
    assert result["branch"] == "INVALID_OR_INCOMPLETE"
    assert "per_seed_effects" not in result


def test_protected_analyzer_and_installer_reject_unverified_fabricated_values(tmp_path) -> None:
    permit, certificate_path, _, root = _permit(tmp_path)
    with pytest.raises(PermissionError, match="protected atomic reader"):
        analyze_packets([_packet(seed) for seed in SEEDS], permit, certificate_path)
    create_result_root(permit, root, certificate_path, "deterministic-fixture-only")
    with pytest.raises(PermissionError, match="protected-analyzer result"):
        write_analysis(
            permit, root, certificate_path, root / "analysis.json",
            {"valid_complete": True, "completeness_ok": True},
        )
    assert not (root / "analysis.json").exists()


def test_literal_resource_counts() -> None:
    proposal = resource_proposal()
    assert proposal["training_episodes"] == 3_072_000
    assert proposal["ordinary_evaluation_episodes"] == 589_824
    assert proposal["cut_episodes"] == 65_536
    assert proposal["total_registered_episodes"] == 3_727_360
    assert proposal["total_agent_decisions"] == 46_301_184
    assert proposal["optimizer_steps"] == 48_000


def test_deterministic_three_arm_atomic_frontier(tmp_path) -> None:
    permit, certificate_path, _, root = _permit(tmp_path)
    create_result_root(permit, root, certificate_path, "deterministic-fixture-only")
    packet = _packet(SEEDS[0])
    packet["certificate_sha256"] = hashlib.sha256(certificate_path.read_bytes()).hexdigest()
    packet["stage_boundary"] = "deterministic-fixture-only"
    training = TrainingResult(
        seed=SEEDS[0],
        models={arm: ArmModel() for arm in ARMS},
        baselines={arm: np.zeros(4) for arm in ARMS},
        metadata=copy.deepcopy(packet["training"]),
    )
    destination = write_atomic_seed_packet(permit, root, certificate_path, training, packet)
    assert destination.name == f"seed-{SEEDS[0]}"
    assert load_seed_packet(permit, root, certificate_path, SEEDS[0]).payload == packet
    with pytest.raises(FileExistsError):
        write_atomic_seed_packet(permit, root, certificate_path, training, packet)


def test_atomic_failure_cleanup_restart_and_incomplete_packet_rejection(tmp_path, monkeypatch) -> None:
    permit, certificate_path, _, root = _permit(tmp_path, authorized_seeds=(SEEDS[0],))
    create_result_root(permit, root, certificate_path, "deterministic-fixture-only")
    packet = _packet(SEEDS[0])
    packet["certificate_sha256"] = hashlib.sha256(certificate_path.read_bytes()).hexdigest()
    packet["stage_boundary"] = "deterministic-fixture-only"
    training = TrainingResult(
        seed=SEEDS[0], models={arm: ArmModel() for arm in ARMS},
        baselines={arm: np.zeros(4) for arm in ARMS}, metadata=copy.deepcopy(packet["training"]),
    )
    incomplete = copy.deepcopy(packet)
    incomplete["evaluation"]["cells"]["9"]["handoff"].pop(ARMS[2])
    with pytest.raises(ValueError, match="semantically complete"):
        write_atomic_seed_packet(permit, root, certificate_path, training, incomplete)
    assert not (root / f"seed-{SEEDS[0]}").exists()

    original_save = artifacts.torch.save
    monkeypatch.setattr(artifacts.torch, "save", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("injected")))
    with pytest.raises(OSError, match="injected"):
        write_atomic_seed_packet(permit, root, certificate_path, training, packet)
    assert not (root / f"seed-{SEEDS[0]}").exists()
    assert list(root.glob(f".seed-{SEEDS[0]}.*.tmp")) == []
    monkeypatch.setattr(artifacts.torch, "save", original_save)
    write_atomic_seed_packet(permit, root, certificate_path, training, packet)
    assert load_seed_packet(permit, root, certificate_path, SEEDS[0]).payload == packet


def test_runtime_guard_uses_current_lease_memory_not_historical_peak_or_cumulative_wall(tmp_path, monkeypatch) -> None:
    permit, certificate_path, _, root = _permit(tmp_path, memory_mib=64)
    create_result_root(permit, root, certificate_path, "deterministic-fixture-only")
    runtime_path = root / "RUNTIME.json"
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    runtime["cumulative_active_seconds"] = 100_000.0
    runtime["peak_rss_bytes"] = 10 * 1024**3
    runtime_path.write_text(json.dumps(runtime), encoding="utf-8")
    monkeypatch.setattr(runner_module, "_rss_bytes", lambda: 32 * 1024**2)
    guard = RuntimeGuard(permit, root, certificate_path)
    guard.check()
    monkeypatch.setattr(runner_module, "_rss_bytes", lambda: 65 * 1024**2)
    with pytest.raises(MemoryError, match="active lease memory_mib"):
        guard.check()


def test_bounded_resource_observer_returns_positive_rss() -> None:
    assert _rss_bytes() > 0
