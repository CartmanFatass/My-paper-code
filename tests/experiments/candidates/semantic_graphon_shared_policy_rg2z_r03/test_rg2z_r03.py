from __future__ import annotations

import argparse
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest
import torch

from experiments.candidates.semantic_graphon_shared_policy_rg2z_r03.authorization import (
    ACTION,
    load_production_permit,
)
from experiments.candidates.semantic_graphon_shared_policy_rg2z_r03.artifacts import (
    create_fresh_result_root,
    expected_training_metadata,
    load_complete_seed_packet,
    load_training_frontier,
    write_atomic_seed_packet,
    write_training_frontier,
)
from experiments.candidates.semantic_graphon_shared_policy_rg2z_r03.certificate import (
    build_certificate,
    write_certificate,
)
from experiments.candidates.semantic_graphon_shared_policy_rg2z_r03.config import (
    COUNTER_ROOT,
    DEVICE,
    DIRECTION,
    REVISION,
    SEEDS,
)
from experiments.candidates.semantic_graphon_shared_policy_rg2z_r03.policies import (
    ArmModel,
)
from experiments.candidates.semantic_graphon_shared_policy_rg2z_r03.reference import (
    episode_return,
    load_coordinate,
    overflow_before_ack_fixture,
)
from experiments.candidates.semantic_graphon_shared_policy_rg2z_r03.runner import (
    _analyze_command,
)
from experiments.candidates.semantic_graphon_shared_policy_rg2z_r03.resources import (
    resource_proposal,
)
from experiments.candidates.semantic_graphon_shared_policy_rg2z_r03.rng import CounterRNG
from experiments.candidates.semantic_graphon_shared_policy_rg2z_r03.statistics import (
    analyze_packets,
    seed_quantities,
)


ARMS = ("PHY-TRUST", "EDGE-FLEX")


def _synthetic_permit(tmp_path, seed: int = SEEDS[0]):
    certificate_path = tmp_path / "certificate.json"
    certificate = write_certificate(certificate_path)
    assert certificate["passed"] is True
    result_root = tmp_path / "result"
    now = datetime.now(timezone.utc)
    authorization_path = tmp_path / "authorization.json"
    authorization_path.write_text(json.dumps({
        "direction": DIRECTION,
        "revision": REVISION,
        "action": ACTION,
        "production_authorized": True,
        "result_root": str(result_root.resolve()),
        "counter_root": COUNTER_ROOT,
        "device": str(DEVICE),
        "certificate_sha256": hashlib.sha256(certificate_path.read_bytes()).hexdigest(),
        "max_workers": 1,
        "lease_token": "deterministic-synthetic-resume-fixture",
        "stage_boundary": "synthetic-resume-tests-only",
        "issued_at_utc": (now - timedelta(minutes=1)).isoformat(),
        "not_after_utc": (now + timedelta(minutes=10)).isoformat(),
        "authorized_seeds": [seed],
    }), encoding="utf-8")
    permit = load_production_permit(
        authorization_path, result_root, certificate_path
    )
    create_fresh_result_root(result_root, permit, certificate_path)
    return permit, certificate_path, result_root


def _zero_models_and_optimizers():
    models = {arm: ArmModel(arm) for arm in ARMS}
    with torch.no_grad():
        for model in models.values():
            for parameter in model.parameters():
                parameter.zero_()
    optimizers = {
        arm: torch.optim.Adam(
            model.parameters(), lr=3.0e-4, betas=(0.9, 0.999),
            eps=1.0e-8, weight_decay=0.0, foreach=False,
        )
        for arm, model in models.items()
    }
    return models, optimizers


def _panel(mean_return: float, west: float = 0.5, east: float = 0.5) -> dict:
    return {
        "mean_return": mean_return,
        "mean_timely_delivery_by_basin": {"WEST": west, "EAST": east},
        "world_count": 256,
        "task_diagnostics": {},
    }


def _packet(seed: int, *, qualifying: bool = True, answerable: bool = True) -> dict:
    cells: dict[str, dict] = {}
    for n in (6, 9, 15, 21):
        heldout = n in (6, 21)
        edge_return = 0.50
        phy_return = 0.56 if heldout and qualifying else 0.50
        cell = {
            "n": n,
            "world_count": 256,
            "intact": {
                "PHY-TRUST": _panel(
                    phy_return,
                    west=0.45 if heldout and qualifying else 0.40,
                    east=0.45 if heldout and qualifying else 0.40,
                ),
                "EDGE-FLEX": _panel(edge_return, west=0.40, east=0.40),
            },
            "uniform": (
                {"UNIFORM-LEGAL": _panel(0.40)} if n in (9, 15) else {}
            ),
            "rotated": {},
            "shadow": {},
            "registered_support": {
                "basin_count": 2,
                "events_per_basin": 3,
                "public_role_count": 3,
                "agents_per_role": n // 3,
                "balanced_positive_role_support": True,
                "fixed_legal_masks": True,
            },
        }
        if heldout:
            cell["rotated"] = {
                "PHY-TRUST": _panel(0.49 if qualifying else 0.50),
                "EDGE-FLEX": _panel(0.50),
            }
            cell["shadow"] = {
                "PHY-TRUST": {
                    "mean_legal_action_tv": 0.10 if qualifying else 0.0,
                    "mean_tv_support": 0.90 if answerable else 0.08,
                    "history_count": 256 * 12 * n,
                    "shadow_state_propagated": False,
                    "intact_observations_and_incoming_hidden_fixed": True,
                }
            }
        cells[str(n)] = cell
    return {
        "revision": REVISION,
        "action": ACTION,
        "seed": seed,
        "arms": list(ARMS),
        "training": {
            "seed": seed,
            "completed_updates": 512,
            "checkpoint": "immediately_after_update_512",
        },
        "evaluation": {
            "seed": seed,
            "cells": cells,
            "registered_rosters": [6, 9, 15, 21],
            "worlds_per_roster": 256,
            "frozen_checkpoint": "immediately_after_update_512",
            "evaluation_updates": 0,
            "heldout_training_or_adaptation": False,
            "greedy_evaluation": False,
            "stochastic_policy_including_uniform_mixture": True,
            "episode_rows_retained": False,
            "seed_is_inferential_unit": True,
            "arm_independent_world_and_action_coordinates": True,
            "rotated_panels_only_at_heldout_rosters": True,
            "shadow_cut_only_at_heldout_rosters": True,
            "uniform_legal_only_at_training_rosters": True,
        },
        "deterministic_checkpoint_audit": {"passed": True},
        "structural_checkpoint_audit": {"passed": True},
        "production_lease_token_sha256": "1" * 64,
        "checkpoint_identity": "only_evaluable_state_immediately_after_update_512",
        "worlds_and_agents_are_inferential_replicates": False,
        "seed_is_inferential_unit": True,
        "atomic_payload_complete": True,
    }


def test_preactivity_certificate_is_static_and_complete(tmp_path) -> None:
    certificate = build_certificate()
    assert certificate["passed"], certificate["checks"]
    assert len(certificate["checks"]) == 10
    assert certificate["registered_stochastic_object_materialized"] is False
    assert certificate["registered_coordinate_materialized"] is False
    assert certificate["registered_policy_output_materialized"] is False

    path = tmp_path / "certificate.json"
    assert write_certificate(path) == certificate


def test_frozen_registry_model_shape_and_handwritten_fixtures() -> None:
    assert len(SEEDS) == 24 and len(set(SEEDS)) == 24
    assert COUNTER_ROOT.endswith("RIDGEGATE-2Z|blake2b-counter-v1")
    assert sum(parameter.numel() for parameter in ArmModel("PHY-TRUST").parameters()) == 35_513
    assert load_coordinate(2) == pytest.approx(-1.0)
    assert load_coordinate(7) == pytest.approx(1.0)
    assert episode_return(3, 3, 0.0) == pytest.approx(1.0)
    overflow = overflow_before_ack_fixture()
    assert overflow["after_arrival_before_ack"] == (
        "second", "third", "fourth", "arrival",
    )
    assert overflow["after_current_head_ack"] == ("third", "fourth", "arrival")


def test_registered_rng_cannot_be_constructed_without_root_capability() -> None:
    with pytest.raises(PermissionError, match="ProductionPermit"):
        CounterRNG(object())  # type: ignore[arg-type]


def test_resource_arithmetic_is_the_frozen_complete_panel() -> None:
    proposal = resource_proposal()
    assert proposal["unique_training_worlds"] == 786_432
    assert proposal["learned_training_unrolls"] == 1_572_864
    assert proposal["training_transitions"] == 18_874_368
    assert proposal["full_batch_backward_calls"] == 24_576
    assert proposal["total_evaluation_trajectories"] == 86_016
    assert proposal["total_trajectory_transitions"] == 19_906_560
    assert proposal["total_learned_actor_steps"] == 239_984_640
    assert proposal["requested_concurrency"] == 4


def test_exact_18_quantity_family_and_positive_branch() -> None:
    packets = [_packet(seed) for seed in SEEDS]
    assert len(seed_quantities(packets[0])) == 18
    result = analyze_packets(packets)
    assert result["hard_structural_validity"] is True
    assert result["family"]["member_count"] == 18
    assert result["family"]["df"] == 23
    assert result["decision"] == "RETAIN_PHYSICAL_PRIOR_COLDSTART"


def test_nonretention_predicates_and_nonidentification_precedence() -> None:
    nonretaining = analyze_packets([_packet(seed, qualifying=False) for seed in SEEDS])
    assert nonretaining["decision"] == "DO_NOT_RETAIN_FIXED_PRIOR_AS_DEFAULT"
    assert nonretaining["failed_qualification_predicates"] == [
        "HELDOUT_DIRECT_RETURN_NOT_ESTABLISHED",
        "COLDSTART_INTERACTION_NOT_ESTABLISHED",
        "WORST_ZONE_ADVANTAGE_NOT_ESTABLISHED",
        "ACTION_SENSITIVE_ATTRIBUTION_NOT_ESTABLISHED",
        "PRACTICAL_EQUIVALENCE",
    ]

    nonidentified = analyze_packets([
        _packet(seed, qualifying=True, answerable=False) for seed in SEEDS
    ])
    assert nonidentified["decision"] == "NONIDENTIFIED"
    assert nonidentified["failed_answerability_sizes"] == [6, 21]


def test_incomplete_or_reordered_panel_exposes_no_intervals() -> None:
    incomplete = analyze_packets([_packet(SEEDS[0])])
    assert incomplete["hard_structural_validity"] is False
    assert "intervals" not in incomplete

    packets = [_packet(seed) for seed in SEEDS]
    reordered = copy.deepcopy(packets)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    invalid = analyze_packets(reordered)
    assert invalid["hard_structural_validity"] is False
    assert "intervals" not in invalid


def test_nonevaluable_training_frontier_round_trip_restores_both_arms_and_adam(tmp_path) -> None:
    permit, certificate_path, result_root = _synthetic_permit(tmp_path)
    models, optimizers = _zero_models_and_optimizers()
    frontier = write_training_frontier(
        result_root, permit, certificate_path, SEEDS[0], 7, models, optimizers
    )
    assert frontier.name == f".seed-{SEEDS[0]}.training-frontier.pt"
    envelope = torch.load(frontier, map_location="cpu", weights_only=True)
    metadata = envelope["payload"]["metadata"]
    assert metadata["evaluable"] is False
    assert metadata["partial_interpretation_allowed"] is False
    assert metadata["contains_returns"] is False
    assert metadata["contains_evaluation"] is False
    assert metadata["contains_endpoints"] is False
    assert metadata["contains_partial_summaries"] is False

    with torch.no_grad():
        for model in models.values():
            for parameter in model.parameters():
                parameter.fill_(1.0)
    assert load_training_frontier(
        result_root, permit, certificate_path, SEEDS[0], models, optimizers
    ) == 7
    assert all(
        torch.count_nonzero(parameter).item() == 0
        for model in models.values() for parameter in model.parameters()
    )
    assert all(optimizer.state_dict()["state"] == {} for optimizer in optimizers.values())


def test_training_frontier_hashes_adam_scalar_step_state(tmp_path) -> None:
    permit, certificate_path, result_root = _synthetic_permit(tmp_path)
    models, optimizers = _zero_models_and_optimizers()
    for arm in ARMS:
        optimizers[arm].zero_grad(set_to_none=True)
        sum(parameter.sum() for parameter in models[arm].parameters()).backward()
        optimizers[arm].step()
    frontier = write_training_frontier(
        result_root, permit, certificate_path, SEEDS[0], 1, models, optimizers
    )
    assert frontier.is_file()
    envelope = torch.load(frontier, map_location="cpu", weights_only=True)
    for arm in ARMS:
        assert any(
            torch.is_tensor(state.get("step")) and state["step"].ndim == 0
            for state in envelope["payload"]["optimizers"][arm]["state"].values()
        )


def test_training_frontier_tamper_and_wrong_arm_set_fail_closed(tmp_path) -> None:
    permit, certificate_path, result_root = _synthetic_permit(tmp_path)
    models, optimizers = _zero_models_and_optimizers()
    frontier = write_training_frontier(
        result_root, permit, certificate_path, SEEDS[0], 1, models, optimizers
    )
    envelope = torch.load(frontier, map_location="cpu", weights_only=True)
    envelope["payload"]["metadata"]["matched_update"] = 2
    torch.save(envelope, frontier)
    with pytest.raises(RuntimeError, match="digest mismatch"):
        load_training_frontier(
            result_root, permit, certificate_path, SEEDS[0], models, optimizers
        )
    with pytest.raises(ValueError, match="both learned arms"):
        write_training_frontier(
            result_root, permit, certificate_path, SEEDS[0], 2,
            {"PHY-TRUST": models["PHY-TRUST"]}, optimizers,
        )


def test_packet_install_requires_full_statistics_audit_and_then_removes_frontier(tmp_path) -> None:
    permit, certificate_path, result_root = _synthetic_permit(tmp_path)
    models, optimizers = _zero_models_and_optimizers()
    frontier = write_training_frontier(
        result_root, permit, certificate_path, SEEDS[0], 512, models, optimizers
    )
    packet = _packet(SEEDS[0])
    packet["training"] = expected_training_metadata(SEEDS[0])

    failed_audit = copy.deepcopy(packet)
    failed_audit["deterministic_checkpoint_audit"]["passed"] = False
    with pytest.raises(RuntimeError, match="statistics audit"):
        write_atomic_seed_packet(
            result_root, permit, certificate_path, SEEDS[0], models, failed_audit
        )
    assert frontier.exists()
    assert not (result_root / f"seed-{SEEDS[0]}").exists()

    incomplete = copy.deepcopy(packet)
    del incomplete["evaluation"]["cells"]["21"]
    with pytest.raises(RuntimeError, match="statistics audit"):
        write_atomic_seed_packet(
            result_root, permit, certificate_path, SEEDS[0], models, incomplete
        )
    assert frontier.exists()

    write_atomic_seed_packet(
        result_root, permit, certificate_path, SEEDS[0], models, packet
    )
    assert not frontier.exists()
    assert load_complete_seed_packet(
        result_root, permit, certificate_path, SEEDS[0]
    ) == packet


def test_subset_permit_cannot_load_other_seed_or_enter_full_panel_analysis(tmp_path) -> None:
    permit, certificate_path, result_root = _synthetic_permit(tmp_path, SEEDS[0])
    with pytest.raises(PermissionError, match="outside the frozen registered panel"):
        load_complete_seed_packet(
            result_root, permit, certificate_path, SEEDS[1]
        )
    with pytest.raises(PermissionError, match="exact complete 24-seed panel"):
        _analyze_command(argparse.Namespace(
            authorization=permit._path,
            result_root=result_root,
            certificate=certificate_path,
            output=result_root / "analysis.json",
        ))
    assert not (result_root / "analysis.json").exists()
