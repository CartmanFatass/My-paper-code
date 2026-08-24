from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv import empirical_runner as runner
from experiments.candidates.roster_consistent_latent_exploration_tbcfv import empirical_contract as contract
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_contract import (
    CM_ACCEPTED_BINDING_SCHEMA,
    CM_OWNER,
    EMPIRICAL_OBJECT,
    SYNTHETIC_TEST_IDENTITIES,
    build_preactivity_certificate,
    canonical_json_bytes,
    coordinate_proposal,
    document_sha256,
    materialize_coordinates,
    native_identity_from_observation,
    production_source_paths,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import Snapshot
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import FLEX
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import make_conformance_fixture_model
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.process_workers import make_process_resource_object


def _certificate(tmp_path: Path) -> dict[str, object]:
    del tmp_path
    return _production_certificate()


def _production_certificate() -> dict[str, object]:
    return build_preactivity_certificate(
        source_paths=production_source_paths(),
        native_identity=native_identity_from_observation(runner.native_artifact_identity()),
    )


def _accepted(certificate: dict[str, object]) -> dict[str, object]:
    body = {
        "schema": CM_ACCEPTED_BINDING_SCHEMA,
        "issuer": CM_OWNER,
        "technically_accepted": True,
        "direction_id": certificate["direction_id"],
        "science_revision": certificate["science_revision"],
        "empirical_object": EMPIRICAL_OBJECT,
        "preactivity_certificate_sha256": certificate["certificate_sha256"],
        "source_set_sha256": certificate["source"]["source_set_sha256"],
        "config_sha256": certificate["config"]["config_sha256"],
        "native_identity_sha256": certificate["native"]["native_identity_sha256"],
        "analyzer_sha256": certificate["analyzer"]["analyzer_sha256"],
        "coordinate_proposal_sha256": certificate["coordinate_proposal"]["proposal_sha256"],
        "result_blind": True,
        "scientific_activity_started": False,
    }
    return {**body, "binding_sha256": document_sha256(body)}


def _write(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value))


def test_coordinate_proposal_is_unbound_and_has_exact_pairings() -> None:
    value = coordinate_proposal()
    assert value["materialized"] is False
    assert value["namespace"] is None
    assert value["run_block_identities"] is None
    assert value["numeric_seeds"] is None
    assert value["master"] is None
    assert value["coordinate_rows"] is None
    assert value["random_scientific_state"] is None
    assert value["run_block_count"] == 20
    assert value["pairing"] == {
        "world_and_evaluation_scenarios_shared_across_arms": True,
        "common_initial_tensor_shared_across_arms": True,
        "common_plan_draws_shared_when_semantically_common": True,
        "actor_draws_shared_when_agent_semantics_and_distribution_coincide": True,
        "coherent_fragmented_scenarios_shared_through_intervention": True,
        "unused_draws_have_no_forward_or_score_path": True,
    }


def test_production_process_resource_is_consumed_from_exact_request_lease_paths(
    tmp_path: Path,
) -> None:
    result_root = tmp_path / "result"
    resource = make_process_resource_object(
        canonical_result_root=result_root,
        private_scratch_roots=[tmp_path / f"private_{index}" for index in range(4)],
        source_set_sha256="1" * 64,
        native_binding_sha256="2" * 64,
    )
    authority = SimpleNamespace(
        result_root=result_root.resolve(),
        certificate={
            "source": {"source_set_sha256": "1" * 64},
            "native": {"native_identity_sha256": "2" * 64},
        },
        permit=SimpleNamespace(
            resources={"process_resource": resource},
            paths=dict(resource["paths"]),
        ),
    )
    assert runner._production_process_resource(authority) == resource
    alternate = make_process_resource_object(
        canonical_result_root=result_root,
        private_scratch_roots=[tmp_path / f"alternate_{index}" for index in range(4)],
        source_set_sha256="1" * 64,
        native_binding_sha256="2" * 64,
    )
    authority.permit.resources["process_resource"] = alternate
    with pytest.raises(runner.EmpiricalRunnerError, match="differs from request/lease"):
        runner._production_process_resource(authority)


def test_preactivity_summary_rejects_incomplete_chain_measurement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools.benchmarks import benchmark_rcle_tbcfv_r04_native as benchmark

    certificate = _certificate(tmp_path)
    accepted = _accepted(certificate)
    monkeypatch.setattr(
        runner,
        "require_cpp_batched_production",
        lambda *args, **kwargs: {
            "schema": "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1",
            "component": contract.SHARED_COMPONENT,
            "backend": "cpp",
            "batch_width": 8,
            "full_reset_step_cpp": True,
            "python_fallback": False,
        },
    )
    monkeypatch.setattr(
        runner,
        "native_artifact_identity",
        lambda: {
            "sha256": contract.ACCEPTED_NATIVE_ARTIFACT_SHA256,
            "source_sha256": contract.ACCEPTED_NATIVE_SOURCE_SHA256,
            "build_key": contract.ACCEPTED_NATIVE_BUILD_KEY,
            "runtime_abi": certificate["native"]["runtime_abi"],
            "toolchain": certificate["native"]["toolchain"],
            "abi": {
                "abi_version": 2,
                "fixture_magic": 0x52434C4554424347,
                "fixture_input_size": 224,
                "step_input_size": 64,
                "event_input_size": 64,
                "snapshot_size": 464,
            },
        },
    )
    monkeypatch.setattr(
        benchmark,
        "run_benchmark",
        lambda **kwargs: {"efficiency_review": "COMPLETE", "chain_coverage": {}},
    )
    with pytest.raises(runner.EmpiricalRunnerError, match="chain coverage is incomplete"):
        runner.result_blind_preactivity_summary(
            certificate,
            accepted,
            temp_root=tmp_path / "preflight",
        )


def test_resource_request_is_request_only_and_result_blind(tmp_path: Path) -> None:
    certificate = _certificate(tmp_path)
    result_root = tmp_path / "future_result_root"
    request = runner.make_resource_request(certificate, result_root=result_root)
    assert request["authority"] == "REQUEST_ONLY"
    assert request["lease_issued"] is False
    assert request["activity_authorized"] is False
    assert request["production_launch"] is False
    assert request["component"] == "rcle.tbcfv.r04.full_host"
    assert request["batch_width"] == 8
    assert request["complete_panel_only"] is True
    assert request["result_blind"] is True
    assert request["coordinate_materialization"] == "ONLY_AFTER_ROOT_LEASE_AND_CM_ACCEPTED_BINDING"


def test_synthetic_binding_cannot_enter_production_validator() -> None:
    synthetic = materialize_coordinates(SYNTHETIC_TEST_IDENTITIES[0])
    permit = runner.RootLeasePermit(
        lease_id="SYNTHETIC-TEST-LEASE",
        origin_lease_id="SYNTHETIC-TEST-LEASE",
        predecessor_lease_id=None,
        replacement_index=0,
        lease_lineage=("SYNTHETIC-TEST-LEASE",),
        stage_binding_sha256="3" * 64,
        accepted_binding_sha256="0" * 64,
        preactivity_certificate_sha256="1" * 64,
        coordinate_proposal_sha256="2" * 64,
        issued_at="2026-08-21T00:00:00+00:00",
        expires_at="2026-08-22T00:00:00+00:00",
        paths={},
        resources={},
        fixture_only=True,
    )
    with pytest.raises(PermissionError, match="unvalidated"):
        runner.validate_materialized_binding(
            synthetic,
            permit,
            now=datetime(2026, 8, 21, 1, tzinfo=timezone.utc),
        )


def test_production_parallelism_routes_to_parent_process_integrator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = SimpleNamespace(require_active=lambda **_kwargs: None)
    frontier = SimpleNamespace(root=tmp_path / "frontier")
    frontier.root.mkdir()
    calls: list[int] = []
    monkeypatch.setattr(
        runner,
        "open_frontier",
        lambda *_args, **_kwargs: frontier,
    )
    def process_blocks(_frontier, _authority, *, workers):
        assert _frontier is frontier and _authority is authority
        calls.append(workers)
        raise runner.EmpiricalRunnerError("TEST_PROCESS_DISPATCH_REACHED")

    monkeypatch.setattr(runner, "_execute_process_blocks", process_blocks)
    with pytest.raises(runner.EmpiricalRunnerError, match="TEST_PROCESS_DISPATCH_REACHED"):
        runner.execute_full_panel(
            authority,
            now=datetime(2026, 8, 21, 1, tzinfo=timezone.utc),
            workers=4,
        )
    assert calls == [4]


def test_cli_coordinate_proposal_and_fail_closed_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv.__main__ import main

    assert main(["coordinate-proposal"]) == 0
    emitted = json.loads(capsys.readouterr().out)
    assert emitted == coordinate_proposal()

    missing = tmp_path / "absent.json"
    result = tmp_path / "result"
    code = main(
        [
            "run",
            "--certificate",
            str(missing),
            "--accepted-binding",
            str(missing),
            "--resource-request",
            str(missing),
            "--lease",
            str(missing),
            "--coordinate-binding",
            str(missing),
            "--result-root",
            str(result),
        ]
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert captured.err.startswith("FAIL_CLOSED:")
    assert not result.exists()


def test_cli_preactivity_uses_only_accepted_result_blind_objects(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv.__main__ import main

    certificate = _production_certificate()
    accepted = _accepted(certificate)
    certificate_path = tmp_path / "certificate.json"
    accepted_path = tmp_path / "accepted.json"
    preflight_temp = tmp_path.parents[1] / "rcle_pf"
    _write(certificate_path, certificate)
    _write(accepted_path, accepted)
    assert (
        main(
            [
                "preflight",
                "--certificate",
                str(certificate_path),
                "--accepted-binding",
                str(accepted_path),
                "--temp-root",
                str(preflight_temp),
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "PREACTIVITY_PREFLIGHT"
    assert output["technically_accepted"] is True
    assert output["production_source_set_validated"] is True
    assert output["native_receipt"]["shared_receipt_validated"] is True
    assert output["runner_chain"] == {
        "synthetic_test_only": True,
        "training_cells": 8,
        "training_episodes": 64,
        "forward_backward_completed": True,
        "fixed_norm_update_completed": True,
        "t24_event_transport_seam_completed": True,
        "learned_heldout_consumer_completed": True,
        "scripted_consumers_completed": 3,
        "scientific_output_exposed": False,
    }
    assert output["analyzer_admission"] == {
        "test_records": 20,
        "production_admission_rejected": True,
        "scientific_output_exposed": False,
        "synthetic_72_tail_reducer_completed": True,
    }
    assert all(output["chain_flags"].values())
    assert output["measurements"]["cold_load"]["peak_rss_bytes"] > 0
    assert output["measurements"]["warm_reuse_load"]["peak_rss_bytes"] > 0
    assert output["measurements"]["runner_full_chain"]["cpu_seconds"] >= 0
    assert output["measurements"]["atomic_publish"]["io_write_bytes"] >= 0
    assert output["identity_materialized"] is False
    assert output["coordinate_materialized"] is False
    assert output["scientific_activity_started"] is False
    serialized = json.dumps(output, sort_keys=True)
    for forbidden in ('"branch"', '"gates"', '"bounds"', '"tau"', '"U"', '"F"', '"Y"'):
        assert forbidden not in serialized


def test_cli_preactivity_requires_explicit_temp_root(tmp_path: Path) -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv.__main__ import main

    missing = tmp_path / "missing.json"
    with pytest.raises(SystemExit) as raised:
        main(
            [
                "preflight",
                "--certificate",
                str(missing),
                "--accepted-binding",
                str(missing),
            ]
        )
    assert raised.value.code == 2


def test_public_model_tensor_adapter_excludes_transport_keys() -> None:
    common = dict(
        tick=0,
        terminal=False,
        event_input_required=False,
        claim_required=True,
        roster_event=False,
        new_epoch=False,
        positions=(0, 20, 40, 60, 80, 100),
        angular_ranks=(0, 1, 2, 3, 4, 5),
        previous_displacements=(0, 0, 0, 0, 0, 0),
        newcomers=(False,) * 6,
        current_claims=(-1,) * 6,
        beacon_positions=(0, 20, 40, 60, 80, 100),
        demands=(1, 1, 1, 1, 1, 1),
        last_coverage=(0,) * 6,
        last_u=None,
        last_fragmentation=None,
        accumulated_u=0.0,
        accumulated_post_u=0.0,
        accumulated_fragmentation=0.0,
        tau=None,
        U=None,
        F=None,
        Y=None,
    )
    left = Snapshot(transport_keys=(1, 2, 3, 4, 5, 6), **common)
    right = Snapshot(transport_keys=(101, 202, 303, 404, 505, 606), **common)
    left_tensors = runner._public_tensors(left)
    right_tensors = runner._public_tensors(right)
    assert all(torch.equal(a, b) for a, b in zip(left_tensors, right_tensors))
    assert [tuple(value.shape) for value in left_tensors] == [
        (6, 3),
        (6, 3),
        (4,),
        (6, 5),
        (6, 6, 4),
    ]


def test_fixed_synthetic_microfixture_exercises_exact_update_and_event_seam() -> None:
    rng = runner.SyntheticTestRNG("SYNTHETIC-TEST-RCLE-TBCFV-RUNNER-A")
    model = make_conformance_fixture_model()
    authority_checks: list[str] = []
    baselines, counts = runner.execute_training_update(
        model,
        FLEX,
        rng,
        0,
        torch.zeros(8, dtype=torch.float64),
        authority_check=lambda: authority_checks.append("before-gradient-mutation"),
    )
    assert baselines.shape == (8,)
    assert counts["training_episodes"] == 64
    assert counts["environment_ticks"] == 4_096
    assert counts["candidate_pointer_scores"] == counts["agent_claim_decisions"] * 6
    assert rng.synthetic_test_only is True
    assert authority_checks == ["before-gradient-mutation"]


@pytest.mark.parametrize("arm", runner.LEARNED_PACKAGES)
def test_masked_b8_consumer_matches_scalar_reference_exactly(arm: str) -> None:
    scalar_model = make_conformance_fixture_model()
    batched_model = make_conformance_fixture_model()
    batched_model.load_state_dict(scalar_model.state_dict())
    scalar_rng = runner.SyntheticTestRNG("SYNTHETIC-TEST-RCLE-TBCFV-RUNNER-A")
    batched_rng = runner.SyntheticTestRNG("SYNTHETIC-TEST-RCLE-TBCFV-RUNNER-A")
    cell = runner.TRAINING_CELLS[0]
    coordinates = tuple(runner.EpisodeCoordinate(0, cell, 0, row) for row in range(8))

    scalar = runner._execute_learned_batch_scalar_reference(
        scalar_model, arm, scalar_rng, coordinates, training=True
    )
    batched = runner.execute_learned_batch(
        batched_model, arm, batched_rng, coordinates, training=True
    )

    assert len(scalar) == len(batched) == 8
    for expected, observed in zip(scalar, batched):
        assert (observed.tau, observed.U, observed.F, observed.Y) == (
            expected.tau,
            expected.U,
            expected.F,
            expected.Y,
        )
        assert observed.agent_ticks == expected.agent_ticks
        assert observed.claim_decisions == expected.claim_decisions
        assert len(observed.plan_scores) == len(expected.plan_scores)
        assert len(observed.claim_scores) == len(expected.claim_scores)
        assert all(
            torch.equal(actual, reference)
            for actual, reference in zip(observed.plan_scores, expected.plan_scores)
        )
        assert all(
            torch.equal(actual, reference)
            for actual, reference in zip(observed.claim_scores, expected.claim_scores)
        )


@pytest.mark.parametrize("arm", runner.LEARNED_PACKAGES)
def test_masked_b32_mixed_cells_matches_four_scalar_b8_calls_exactly(arm: str) -> None:
    scalar_model = make_conformance_fixture_model()
    batched_model = make_conformance_fixture_model()
    batched_model.load_state_dict(scalar_model.state_dict())
    scalar_rng = runner.SyntheticTestRNG("SYNTHETIC-TEST-RCLE-TBCFV-RUNNER-A")
    batched_rng = runner.SyntheticTestRNG("SYNTHETIC-TEST-RCLE-TBCFV-RUNNER-A")
    cells = runner.TRAINING_CELLS[:4]
    coordinates = tuple(
        runner.EpisodeCoordinate(0, cell, 0, row) for cell in cells for row in range(8)
    )

    scalar = tuple(
        episode
        for offset in range(0, 32, 8)
        for episode in runner._execute_learned_batch_scalar_reference(
            scalar_model,
            arm,
            scalar_rng,
            coordinates[offset : offset + 8],
            training=True,
        )
    )
    batched = runner.execute_learned_batch(
        batched_model, arm, batched_rng, coordinates, training=True
    )

    for expected, observed in zip(scalar, batched):
        assert (observed.tau, observed.U, observed.F, observed.Y) == (
            expected.tau,
            expected.U,
            expected.F,
            expected.Y,
        )
        assert observed.agent_ticks == expected.agent_ticks
        assert observed.claim_decisions == expected.claim_decisions
        assert all(
            torch.equal(actual, reference)
            for actual, reference in zip(observed.plan_scores, expected.plan_scores)
        )
        assert all(
            torch.equal(actual, reference)
            for actual, reference in zip(observed.claim_scores, expected.claim_scores)
        )


def test_runner_owner_bound_staging_recovers_injected_process_loss(tmp_path: Path) -> None:
    value = runner._synthetic_empirical_frontier_chain(tmp_path)
    assert value == {
        "synthetic_generation_staged": True,
        "injected_process_loss_recovered": True,
        "partial_publication_recovered": True,
        "atomic_generation_published": True,
        "exact_generation_resumed": True,
    }


def _mock_source_repair_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[runner.ProductionAuthority, dict[str, object]]:
    result_root = tmp_path / "repair-result"
    frontier_root = result_root / "frontiers"
    frontier_root.mkdir(parents=True)
    run_identity_path = result_root / "RUN_IDENTITY.json"
    roots = [
        {"block_index": index, "root_digest": f"{index + 1:064x}"}
        for index in range(20)
    ]
    coordinate = {
        "binding_sha256": "4" * 64,
        "master_digest": "5" * 64,
        "stage_binding_sha256": "6" * 64,
        "authority": "RCLE-ORIGIN-LEASE",
        "run_block_roots": roots,
    }
    _write(run_identity_path, coordinate)
    failed_terminal_path = result_root / "FAILED_TERMINAL.json"
    _write(failed_terminal_path, {"test_only": True})
    paths = {
        "result_root": str(result_root.resolve()),
        "frontier_root": str(frontier_root.resolve()),
        "run_identity_path": str(run_identity_path.resolve()),
    }
    old_permit = SimpleNamespace(
        lease_id="RCLE-ORIGIN-LEASE",
        origin_lease_id="RCLE-ORIGIN-LEASE",
        stage_binding_sha256="6" * 64,
        paths=paths,
    )

    class CurrentPermit(SimpleNamespace):
        def require_active(self, *, now: datetime) -> None:
            assert now.tzinfo is not None

        def immutable_frontier_lease_binding(self) -> dict[str, str]:
            return {
                "origin_lease_id": self.origin_lease_id,
                "lease_id": self.origin_lease_id,
                "lease_binding_sha256": self.stage_binding_sha256,
            }

    current_permit = CurrentPermit(
        lease_id="RCLE-REPAIR-LEASE",
        origin_lease_id="RCLE-ORIGIN-LEASE",
        stage_binding_sha256="7" * 64,
        paths=paths,
    )
    certificate = {
        "source": {"source_set_sha256": "8" * 64},
        "config": {"config_sha256": "2" * 64},
        "native": {"native_identity_sha256": "3" * 64},
    }
    accepted = {"binding_sha256": "9" * 64}
    requests = {"paths": paths}
    transition: dict[str, object] = {
        "source_deltas": [{"logical_path": "TEST-BOUND-BY-CONTRACT"}],
        "run_identity": {
            "binding_sha256": "4" * 64,
            "master_digest": "5" * 64,
            "run_block_roots": roots,
        },
        "original": {
            "source_set_sha256": "1" * 64,
            "stage_binding_sha256": "6" * 64,
        },
        "repaired": {
            "source_set_sha256": "8" * 64,
            "stage_binding_sha256": "7" * 64,
        },
        "preserved": {
            "result_root": str(result_root.resolve()),
            "config_sha256": "2" * 64,
            "native_identity_sha256": "3" * 64,
            "coordinate_binding_sha256": "4" * 64,
            "master_digest": "5" * 64,
        },
    }
    monkeypatch.setattr(
        runner,
        "validate_archived_initial_lease_for_source_repair",
        lambda *args, **kwargs: old_permit,
    )
    monkeypatch.setattr(
        runner,
        "validate_frozen_run_identity",
        lambda *args, **kwargs: transition["run_identity"],
    )
    monkeypatch.setattr(
        runner,
        "validate_source_repair_transition",
        lambda *args, **kwargs: transition,
    )
    monkeypatch.setattr(runner, "validate_preactivity_certificate", lambda value: certificate)
    monkeypatch.setattr(
        runner, "validate_accepted_binding", lambda value, cert: accepted
    )
    monkeypatch.setattr(runner, "_validate_live_source_set", lambda cert: None)
    monkeypatch.setattr(
        runner,
        "validate_materialized_binding",
        lambda *args, **kwargs: pytest.fail("source repair rematerialized coordinates"),
    )
    monkeypatch.setattr(
        runner,
        "validate_source_repair_replacement_lease",
        lambda *args, **kwargs: current_permit,
    )
    authority = runner.admit_source_repair(
        predecessor_certificate={"old": "certificate"},
        predecessor_accepted_binding={"old": "binding"},
        predecessor_resource_request=requests,
        predecessor_lease={"old": "lease"},
        certificate=certificate,
        accepted_binding=accepted,
        resource_request=requests,
        lease={"new": "lease"},
        repair_transition=transition,
        run_identity_path=run_identity_path,
        failed_terminal_path=failed_terminal_path,
        result_root=result_root,
        now=datetime.now(timezone.utc),
    )
    return authority, transition


def test_source_repair_admission_preserves_run_identity_and_applies_bridge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    authority, transition = _mock_source_repair_admission(tmp_path, monkeypatch)
    assert authority.coordinate_digest == "4" * 64
    assert authority.master_digest == "5" * 64
    assert authority.coordinate_binding["run_block_roots"] == transition["run_identity"][
        "run_block_roots"
    ]
    assert authority.original_frontier_bindings is not None
    assert authority.original_frontier_bindings.source_manifest_sha256 == "1" * 64
    assert authority.original_frontier_bindings.lease_binding_sha256 == "6" * 64
    assert authority.permit.stage_binding_sha256 == "7" * 64

    observed: dict[str, object] = {}
    sentinel = object()

    def apply_bridge(
        cls: type[runner.AtomicEmpiricalFrontier],
        root: Path,
        original: runner.EmpiricalBindings,
        repaired: runner.EmpiricalBindings,
        **kwargs: object,
    ) -> object:
        observed.update(
            root=Path(root),
            original=original,
            repaired=repaired,
            transition=kwargs["repair_transition"],
        )
        return sentinel

    monkeypatch.setattr(runner, "_live_native_preflight", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        runner.AtomicEmpiricalFrontier,
        "apply_source_repair",
        classmethod(apply_bridge),
    )
    assert runner.open_frontier(authority, now=datetime.now(timezone.utc)) is sentinel
    assert observed["root"] == authority.result_root / "frontiers"
    assert observed["transition"] is transition
    assert observed["original"] == authority.original_frontier_bindings
    repaired = observed["repaired"]
    assert isinstance(repaired, runner.EmpiricalBindings)
    assert repaired.coordinate_digest == authority.coordinate_digest
    assert repaired.lease_binding_sha256 == "7" * 64

    (authority.result_root / "frontiers" / "stage_repairs").mkdir()
    resumed_sentinel = object()

    def resume_repaired(cls: type[runner.AtomicEmpiricalFrontier], *args: object, **kwargs: object) -> object:
        observed["resumed_effective"] = args[1]
        return resumed_sentinel

    monkeypatch.setattr(
        runner.AtomicEmpiricalFrontier,
        "resume",
        classmethod(resume_repaired),
    )
    assert (
        runner.open_frontier(authority, now=datetime.now(timezone.utc))
        is resumed_sentinel
    )
    assert observed["resumed_effective"] == repaired


def test_source_repair_admission_rejects_alternate_result_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    authority, _ = _mock_source_repair_admission(tmp_path, monkeypatch)
    with pytest.raises(runner.EmpiricalRunnerError, match="cannot change the result root"):
        runner.admit_source_repair(
            predecessor_certificate={"old": "certificate"},
            predecessor_accepted_binding={"old": "binding"},
            predecessor_resource_request=authority.resource_request,
            predecessor_lease={"old": "lease"},
            certificate=authority.certificate,
            accepted_binding=authority.accepted_binding,
            resource_request=authority.resource_request,
            lease=authority.lease_document,
            repair_transition=authority.source_repair_transition or {},
            run_identity_path=authority.result_root / "RUN_IDENTITY.json",
            failed_terminal_path=authority.result_root / "FAILED_TERMINAL.json",
            result_root=tmp_path / "alternate-result",
            now=datetime.now(timezone.utc),
        )


def test_cli_repair_resume_requires_complete_explicit_transition_inputs() -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv.__main__ import main

    with pytest.raises(SystemExit) as raised:
        main(["repair-resume"])
    assert raised.value.code == 2
