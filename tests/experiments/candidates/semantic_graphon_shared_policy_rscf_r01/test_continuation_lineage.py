from __future__ import annotations

from dataclasses import asdict, replace
import copy
import hashlib
import io
import json
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.continuation_lineage import (
    AuthenticatedContinuationCut,
    ContinuationIdentity,
    ContinuationLineage,
    ContinuationLineageError,
    OwnerAuthenticatedContinuationCut,
    canonical_json_bytes,
    canonical_sha256,
    source_epoch_provenance,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.contracts import (
    RESERVED_SCIENTIFIC_NAMESPACE,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.policy import (
    ACTOR_PARAMETER_SHAPES,
    CRITIC_PARAMETER_SHAPES,
    RSCFActor,
    TerminalCritic,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary import (
    BlindedSeedFrontier,
    BoundEmpiricalMaster,
    IntegrityError,
    NonValueConformanceDiagnostic,
    ProductionLifecycleStore,
    mint_or_resume_empirical_master,
    resume_empirical_master_through_lineage,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_runner import (
    PRODUCTION_RUNNER_SCHEMA,
    ProductionIdentity,
    ProductionAuditCertificate,
    ProductionEvaluationCell,
    ProductionEvaluationPanel,
    ProductionSeedQuantityVector,
    ProductionSeedEngine,
    ProductionUpdateReceipt,
    _ArmState,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_launcher import (
    ProductionPanelLauncher,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.analysis import QUANTITY_NAMES
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.evaluation import (
    INTACT,
    PHY,
    expected_cell_keys,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.training import (
    make_projected_adam,
)


SOURCE_A = "a" * 64
SOURCE_B = "b" * 64
MASTER = "c" * 64
COORDINATES = "d" * 64
LEASE_LINEAGE = "SGSP-RG2Z-RSCF-R01-LINEAGE-TEST_ONLY"


def _state_and_identity():
    actor_parameters = {
        name: torch.zeros(shape, dtype=torch.float32)
        for name, shape in ACTOR_PARAMETER_SHAPES.items()
    }
    critic_parameters = {
        name: torch.zeros(shape, dtype=torch.float32)
        for name, shape in CRITIC_PARAMETER_SHAPES.items()
    }
    predecessor = ProductionIdentity(
        RESERVED_SCIENTIFIC_NAMESPACE,
        LEASE_LINEAGE,
        MASTER,
        COORDINATES,
        SOURCE_A,
    )
    arms = {}
    serialized_arms = {}
    for arm in ("PHY-TRUST", "EDGE-FLEX"):
        actor = RSCFActor(actor_parameters)
        critic = TerminalCritic(critic_parameters)
        optimizer = make_projected_adam(actor, critic)
        arms[arm] = _ArmState(actor, critic, optimizer)
        serialized_arms[arm] = {
            "actor": actor.state_dict(),
            "critic": critic.state_dict(),
            "optimizer": optimizer.state_dict(),
        }
    receipts = [
        asdict(ProductionUpdateReceipt(
            update_index=index,
            selector_sha256=f"{index:064x}"[-64:],
            arm_state_sha256={arm: "1" * 64 for arm in arms},
            optimizer_state_sha256={arm: "2" * 64 for arm in arms},
            q_entry_count=1280,
            alternative_count=896,
            batch_roster_order=(9, 15) * 32,
            structural_valid=True,
            audit_failures=(),
            conformance_leaf_passed={
                f"{arm}:{leaf}": True
                for arm in arms
                for leaf in (
                    "Q_TARGET_DETACHED",
                    "PRIVATE_TARGET_ISOLATED",
                    "TORCH_NATIVE_ACTION_IDENTITY",
                    "TORCH_NATIVE_PROBABILITY_TOLERANCE",
                )
            },
            max_probability_abs_error=0.0,
        ))
        for index in range(154)
    ]
    payload = {
        "schema": PRODUCTION_RUNNER_SCHEMA + "_NON_EVALUABLE_RESUME_V1",
        "production_identity_sha256": predecessor.digest,
        "seed_block_index": 0,
        "completed_updates": 154,
        "rolling_origin_digest": "e" * 64,
        "update_receipts": receipts,
        "arms": serialized_arms,
        "evaluable": False,
    }
    buffer = io.BytesIO()
    torch.save(payload, buffer)
    return buffer.getvalue(), predecessor, actor_parameters, critic_parameters, arms


def _cut_and_lineage(state_bytes: bytes, predecessor: ProductionIdentity):
    frontier_core = {
        "seed_block_index": 0,
        "generation": 154,
        "completed_updates": 154,
        "completed_origin_count": 154 * 384,
        "completed_origin_set_sha256": "e" * 64,
        "coordinate_manifest_sha256": COORDINATES,
        "source_binding_sha256": SOURCE_A,
        "evaluable": False,
    }
    frontier_payload = {
        "kind": "BLINDED_NON_EVALUABLE_SEED_FRONTIER",
        **frontier_core,
    }
    frontier_bytes = canonical_json_bytes({
        "schema": "SGSP_RSCF_R01_PRODUCTION_LIFECYCLE_V1",
        "payload_sha256": canonical_sha256(frontier_payload),
        "payload": frontier_payload,
    })
    state_sha = hashlib.sha256(state_bytes).hexdigest()
    frontier_sha = canonical_sha256(frontier_core)
    metadata_bytes = canonical_json_bytes({
        "kind": "BLINDED_NON_EVALUABLE_RESUME_STATE",
        "seed_block_index": 0,
        "generation": 154,
        "state_sha256": state_sha,
        "byte_count": len(state_bytes),
        "frontier_sha256": frontier_sha,
        "evaluable": False,
    })
    commit_bytes = canonical_json_bytes({
        "kind": "ATOMIC_RESUME_GENERATION_COMMIT",
        "seed_block_index": 0,
        "generation": 154,
        "state_sha256": state_sha,
        "state_name": f"g000154-{state_sha}.pt",
        "metadata_name": f"g000154-{state_sha}.json",
        "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
        "frontier_sha256": frontier_sha,
    })
    cut = AuthenticatedContinuationCut(
        "TEST_ONLY_SYNTHETIC_GENERATION154",
        frontier_bytes,
        metadata_bytes,
        commit_bytes,
        state_bytes,
    )
    digests = cut.byte_digests
    lineage = ContinuationLineage(
        namespace=RESERVED_SCIENTIFIC_NAMESPACE,
        lease_lineage_id=LEASE_LINEAGE,
        predecessor_production_identity_sha256=predecessor.digest,
        predecessor_source_binding_sha256=SOURCE_A,
        predecessor_master_commitment_sha256=MASTER,
        predecessor_coordinate_manifest_sha256=COORDINATES,
        cut_seed_block_index=0,
        cut_frontier_sha256=digests["frontier"],
        cut_resume_commit_sha256=digests["commit"],
        cut_resume_metadata_sha256=digests["metadata"],
        cut_resume_state_sha256=digests["state"],
        continuation_source_binding_sha256=SOURCE_B,
    )
    return cut, lineage, ContinuationIdentity.bind(lineage)


def test_separate_identity_and_exact_synthetic_cut_reject_every_tamper() -> None:
    state, predecessor, *_ = _state_and_identity()
    cut, lineage, continuation = _cut_and_lineage(state, predecessor)
    assert predecessor.source_binding_sha256 != continuation.continuation_source_binding_sha256
    assert predecessor.digest != continuation.digest != lineage.digest
    assert cut.authenticate(lineage)["completed_updates"] == 154
    immutable = (
        cut.frontier_bytes,
        cut.resume_metadata_bytes,
        cut.resume_commit_bytes,
        cut.resume_state_bytes,
    )
    for field in (
        "frontier_bytes", "resume_metadata_bytes", "resume_commit_bytes", "resume_state_bytes"
    ):
        tampered = replace(cut, **{field: getattr(cut, field) + b"x"})
        with pytest.raises(ContinuationLineageError):
            tampered.authenticate(lineage)
    for field in (
        "cut_frontier_sha256", "cut_resume_metadata_sha256",
        "cut_resume_commit_sha256", "cut_resume_state_sha256",
        "predecessor_source_binding_sha256", "continuation_source_binding_sha256",
    ):
        tampered_lineage = replace(lineage, **{field: "f" * 64})
        if field == "continuation_source_binding_sha256":
            with pytest.raises(ContinuationLineageError):
                continuation.require_exact_lineage(tampered_lineage)
        else:
            with pytest.raises(ContinuationLineageError):
                cut.authenticate(tampered_lineage)
    assert immutable == (
        cut.frontier_bytes,
        cut.resume_metadata_bytes,
        cut.resume_commit_bytes,
        cut.resume_state_bytes,
    )
    with pytest.raises(ContinuationLineageError, match="from_owner_authenticated_bytes"):
        OwnerAuthenticatedContinuationCut(
            "9" * 64,
            cut.frontier_bytes,
            cut.resume_metadata_bytes,
            cut.resume_commit_bytes,
            cut.resume_state_bytes,
        )


def test_direct_b_restore_rejects_a_and_lineage_import_is_atomic_and_exact() -> None:
    state, predecessor, actor_parameters, critic_parameters, source_arms = _state_and_identity()
    cut, lineage, continuation = _cut_and_lineage(state, predecessor)
    engine = ProductionSeedEngine.__new__(ProductionSeedEngine)
    engine.seed_block_index = 0
    engine.identity = ProductionIdentity(
        RESERVED_SCIENTIFIC_NAMESPACE, LEASE_LINEAGE, MASTER, COORDINATES, SOURCE_B
    )
    engine.continuation_lineage = lineage
    engine.continuation_identity = continuation
    engine.initialization = SimpleNamespace(
        actor_parameters=actor_parameters, critic_parameters=critic_parameters
    )
    engine._arms = {}
    for arm in source_arms:
        actor = RSCFActor(actor_parameters)
        critic = TerminalCritic(critic_parameters)
        engine._arms[arm] = _ArmState(actor, critic, make_projected_adam(actor, critic))
    engine.completed_updates = 0
    engine._rolling_origin_digest = canonical_sha256([])
    engine._update_receipts = []
    with pytest.raises(IntegrityError, match="resume state identity changed"):
        engine.restore_resume_state(state)
    before = tuple(
        parameter.detach().clone()
        for arm in engine._arms.values()
        for parameter in (*arm.actor.parameters(), *arm.critic.parameters())
    )
    with pytest.raises(IntegrityError):
        engine.import_continuation_state(
            replace(cut, resume_state_bytes=cut.resume_state_bytes + b"x"), predecessor
        )
    after_failed = tuple(
        parameter.detach().clone()
        for arm in engine._arms.values()
        for parameter in (*arm.actor.parameters(), *arm.critic.parameters())
    )
    assert all(torch.equal(left, right) for left, right in zip(before, after_failed))
    engine.import_continuation_state(cut, predecessor)
    assert engine.completed_updates == 154
    assert engine._rolling_origin_digest == "e" * 64
    assert [receipt.update_index for receipt in engine._update_receipts] == list(range(154))
    for arm in source_arms:
        for name, value in source_arms[arm].actor.state_dict().items():
            assert torch.equal(engine._arms[arm].actor.state_dict()[name], value)
        for name, value in source_arms[arm].critic.state_dict().items():
            assert torch.equal(engine._arms[arm].critic.state_dict()[name], value)


def test_test_only_master_continuity_keeps_a_record_byte_immutable(tmp_path) -> None:
    predecessor_lease = SimpleNamespace(
        lease_lineage_id=LEASE_LINEAGE,
        retained_root=tmp_path,
        source_binding=SimpleNamespace(digest=SOURCE_A),
        lease_payload={"master_record_relative_path": "control/master.json"},
        lease_payload_sha256="1" * 64,
    )
    predecessor_master = mint_or_resume_empirical_master(predecessor_lease)
    state, predecessor, *_ = _state_and_identity()
    cut, lineage, _ = _cut_and_lineage(state, predecessor)
    lineage = replace(
        lineage,
        predecessor_master_commitment_sha256=predecessor_master.commitment_sha256,
    )
    continuation = ContinuationIdentity.bind(lineage)
    continuation_lease = SimpleNamespace(
        lease_lineage_id=LEASE_LINEAGE,
        retained_root=tmp_path,
        source_binding=SimpleNamespace(digest=SOURCE_B),
        lease_payload={"master_record_relative_path": "control/master.json"},
        lease_payload_sha256="2" * 64,
    )
    master_path = tmp_path / "control" / "master.json"
    before = master_path.read_bytes()
    with pytest.raises(IntegrityError, match="another lineage or source"):
        mint_or_resume_empirical_master(continuation_lease)
    resumed = resume_empirical_master_through_lineage(
        predecessor_lease, continuation_lease, lineage, continuation
    )
    assert isinstance(resumed, BoundEmpiricalMaster)
    assert resumed.commitment_sha256 == predecessor_master.commitment_sha256
    assert master_path.read_bytes() == before


@pytest.mark.parametrize(
    "failed_leaf",
    (
        "Q_TARGET_DETACHED",
        "PRIVATE_TARGET_ISOLATED",
        "TORCH_NATIVE_ACTION_IDENTITY",
        "TORCH_NATIVE_PROBABILITY_TOLERANCE",
    ),
)
def test_each_nonvalue_leaf_receipt_is_bounded_write_once_and_nonadvancing(
    tmp_path, failed_leaf: str
) -> None:
    lease = SimpleNamespace(
        lease_lineage_id="TEST_ONLY_DIAGNOSTIC",
        retained_root=tmp_path,
        source_binding=SimpleNamespace(digest=SOURCE_B),
    )
    coordinates = SimpleNamespace(
        _lease_lineage_id="TEST_ONLY_DIAGNOSTIC", manifest_sha256=COORDINATES
    )
    store = ProductionLifecycleStore(lease, coordinates)
    identifiers = (
        "Q_TARGET_DETACHED",
        "PRIVATE_TARGET_ISOLATED",
        "TORCH_NATIVE_ACTION_IDENTITY",
        "TORCH_NATIVE_PROBABILITY_TOLERANCE",
    )
    diagnostic = NonValueConformanceDiagnostic(
        seed_block_index=0,
        attempted_update_index=154,
        completed_updates=154,
        leaf_identifiers=identifiers,
        leaf_passed={name: name != failed_leaf for name in identifiers},
        max_probability_abs_error=2.1e-5 if "PROBABILITY" in failed_leaf else 0.0,
    )
    first = store.write_nonvalue_conformance_diagnostic(diagnostic)
    observed = store.read_nonvalue_conformance_diagnostic(0, 154)
    assert observed == diagnostic and len(first) == 64
    assert not (tmp_path / "frontier").exists()
    assert not (tmp_path / "resume").exists()
    assert not (tmp_path / "checkpoint").exists()
    assert not (tmp_path / "sealed").exists()
    assert not (tmp_path / "complete").exists()
    with pytest.raises(Exception):
        store.write_nonvalue_conformance_diagnostic(
            replace(diagnostic, max_probability_abs_error=0.5)
        )


def test_lineage_successor_and_source_epoch_provenance_are_explicit() -> None:
    state, predecessor, *_ = _state_and_identity()
    _cut, lineage, continuation = _cut_and_lineage(state, predecessor)
    old = BlindedSeedFrontier(
        0, 154, 154, 154 * 384, "e" * 64, COORDINATES, SOURCE_A
    )
    new = BlindedSeedFrontier(
        0,
        155,
        155,
        155 * 384,
        "f" * 64,
        COORDINATES,
        SOURCE_B,
        continuation_identity_sha256=continuation.digest,
        lineage_sha256=lineage.digest,
        predecessor_source_binding_sha256=SOURCE_A,
        cut_generation=154,
    )
    with pytest.raises(IntegrityError, match="resume successor"):
        new.require_successor_of(old)
    new.require_lineage_successor_of(
        old,
        continuation_identity_sha256=continuation.digest,
        lineage_sha256=lineage.digest,
        predecessor_source_binding_sha256=SOURCE_A,
    )
    provenance = source_epoch_provenance(lineage, continuation)
    assert provenance["predecessor_last_completed_update_index"] == 153
    assert provenance["continuation_first_attempted_update_index"] == 154
    assert provenance["both_arms_common_cut"] is True
    assert provenance["cut_seed_block_index"] == 0
    assert provenance["cut_frontier_sha256"] == lineage.cut_frontier_sha256
    assert provenance["cut_resume_commit_sha256"] == lineage.cut_resume_commit_sha256
    assert provenance["cut_resume_metadata_sha256"] == lineage.cut_resume_metadata_sha256
    assert provenance["cut_resume_state_sha256"] == lineage.cut_resume_state_sha256


def test_generation156_cleanup_preserves_all_four_predecessor_cut_byte_hashes(tmp_path) -> None:
    state, predecessor, *_ = _state_and_identity()
    cut, lineage, continuation = _cut_and_lineage(state, predecessor)
    commit = json.loads(cut.resume_commit_bytes.decode("ascii"))
    resume_dir = tmp_path / "resume" / "SB00"
    frontier_dir = tmp_path / "frontier" / "SB00"
    resume_dir.mkdir(parents=True)
    frontier_dir.mkdir(parents=True)
    paths = {
        "frontier": frontier_dir / "g000154.json",
        "commit": resume_dir / "g000154.commit",
        "metadata": resume_dir / commit["metadata_name"],
        "state": resume_dir / commit["state_name"],
    }
    for name, payload in (
        ("frontier", cut.frontier_bytes),
        ("commit", cut.resume_commit_bytes),
        ("metadata", cut.resume_metadata_bytes),
        ("state", cut.resume_state_bytes),
    ):
        paths[name].write_bytes(payload)
    before = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    lease = SimpleNamespace(
        lease_lineage_id=LEASE_LINEAGE,
        retained_root=tmp_path,
        source_binding=SimpleNamespace(digest=SOURCE_B),
    )
    coordinates = SimpleNamespace(_lease_lineage_id=LEASE_LINEAGE, manifest_sha256=COORDINATES)
    store = ProductionLifecycleStore(
        lease, coordinates,
        source_epoch_provenance=source_epoch_provenance(lineage, continuation),
    )
    previous = BlindedSeedFrontier(
        0, 154, 154, 154 * 384, "e" * 64, COORDINATES, SOURCE_A
    )
    for generation in (155, 156):
        completed = generation
        frontier = BlindedSeedFrontier(
            0, generation, completed, completed * 384,
            f"{generation:064x}"[-64:], COORDINATES, SOURCE_B,
            **store._provenance_fields(),
        )
        if generation == 155:
            frontier.require_lineage_successor_of(
                previous,
                continuation_identity_sha256=continuation.digest,
                lineage_sha256=lineage.digest,
                predecessor_source_binding_sha256=SOURCE_A,
            )
        else:
            frontier.require_successor_of(previous)
        store.write_frontier(frontier)
        store.write_resume_state(0, generation, f"TEST_ONLY_B_STATE_{generation}".encode(), frontier)
        previous = frontier
    after = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    assert after == before == dict(cut.byte_digests)


def test_continuation_restart_is_digest_stable_and_rejects_every_provenance_cross_tamper(tmp_path) -> None:
    state, predecessor, *_ = _state_and_identity()
    _cut, lineage, continuation = _cut_and_lineage(state, predecessor)
    provenance = source_epoch_provenance(lineage, continuation)

    def build(root, mutate=None, *, tamper_manifest=False):
        lease = SimpleNamespace(
            lease_lineage_id=LEASE_LINEAGE,
            retained_root=root,
            source_binding=SimpleNamespace(digest=SOURCE_B),
        )
        coordinates = SimpleNamespace(
            _lease_lineage_id=LEASE_LINEAGE,
            manifest_sha256=COORDINATES,
            namespace=RESERVED_SCIENTIFIC_NAMESPACE,
        )
        store = ProductionLifecycleStore(
            lease, coordinates, source_epoch_provenance=provenance
        )
        frontier = BlindedSeedFrontier(
            0, 512, 512, 512 * 384, "1" * 64, COORDINATES, SOURCE_B,
            **store._provenance_fields(),
        )
        checkpoint = store.install_update512_checkpoint(
            0, b"TEST_ONLY_UPDATE512_CHECKPOINT", frontier
        )
        certificate = ProductionAuditCertificate(
            RESERVED_SCIENTIFIC_NAMESPACE,
            "SB00",
            True,
            (),
            {"updates": 512},
            continuation_identity_sha256=continuation.digest,
            lineage_sha256=lineage.digest,
            source_epoch_provenance=provenance,
        )
        cells = []
        for index, (roster, arm, condition) in enumerate(sorted(expected_cell_keys())):
            tv_required = arm == PHY and condition == INTACT and roster in (6, 21)
            cells.append(ProductionEvaluationCell(
                roster, arm, condition, 256, 0.0, 0.0, 0.0,
                f"{index + 1:064x}"[-64:], checkpoint.checkpoint_sha256,
                certificate.digest,
                0.0 if tv_required else None,
                0.0 if tv_required else None,
            ))
        panel = ProductionEvaluationPanel(
            RESERVED_SCIENTIFIC_NAMESPACE,
            "SB00",
            checkpoint.checkpoint_sha256,
            certificate.digest,
            tuple(cells),
            continuation_identity_sha256=continuation.digest,
            lineage_sha256=lineage.digest,
            source_epoch_provenance=provenance,
        )
        vector = ProductionSeedQuantityVector(
            RESERVED_SCIENTIFIC_NAMESPACE,
            "SB00",
            panel.digest,
            certificate.digest,
            "2" * 64,
            {name: 0.0 for name in QUANTITY_NAMES},
            continuation_identity_sha256=continuation.digest,
            lineage_sha256=lineage.digest,
            source_epoch_provenance=provenance,
        )
        payload = {
            "schema": "SGSP_RSCF_R01_SEALED_SEED_RESULT_V1",
            "namespace": RESERVED_SCIENTIFIC_NAMESPACE,
            "seed_block_index": 0,
            "audit_certificate": asdict(certificate),
            "evaluation_panel": asdict(panel),
            "quantity_vector": asdict(vector),
        }
        if mutate is not None:
            mutate(payload)
        master = SimpleNamespace(
            lease_lineage_id=LEASE_LINEAGE,
            _secret=b"TEST_ONLY_RESTART_MASTER_KEY_00"[:32],
        )
        reference = store.install_sealed_seed_result(0, payload, master)
        if tamper_manifest:
            manifest_path = root / "sealed" / "SB00.json"
            envelope = json.loads(manifest_path.read_text(encoding="ascii"))
            envelope["payload"]["source_epoch_provenance"]["cut_resume_state_sha256"] = "f" * 64
            envelope["payload_sha256"] = canonical_sha256(envelope["payload"])
            manifest_path.write_bytes(canonical_json_bytes(envelope))
        launcher = ProductionPanelLauncher.__new__(ProductionPanelLauncher)
        launcher.lease = lease
        launcher.master = master
        launcher.coordinates = coordinates
        launcher.lifecycle = store
        launcher.continuation_inputs = None
        launcher._authenticated_cut_frontier = None
        return launcher, certificate, panel, vector, reference

    baseline, certificate, panel, vector, reference = build(tmp_path / "baseline")
    restarted = baseline._load_finished_seed(0)
    assert restarted.audit_certificate.digest == certificate.digest
    assert restarted.evaluation_panel.digest == panel.digest
    assert restarted.quantity_vector.evaluation_panel_sha256 == vector.evaluation_panel_sha256
    assert restarted.sealed_ref == reference
    assert restarted.sealed_ref.source_epoch_provenance == provenance

    def provenance_tamper(component):
        def mutate(payload):
            payload[component]["source_epoch_provenance"]["cut_resume_state_sha256"] = "f" * 64
        return mutate

    def audit_cross_tamper(payload):
        payload["evaluation_panel"]["audit_certificate_sha256"] = "f" * 64
        for cell in payload["evaluation_panel"]["cells"]:
            cell["audit_certificate_sha256"] = "f" * 64

    def panel_cross_tamper(payload):
        payload["quantity_vector"]["evaluation_panel_sha256"] = "f" * 64

    def checkpoint_cross_tamper(payload):
        payload["evaluation_panel"]["checkpoint_sha256"] = "f" * 64
        for cell in payload["evaluation_panel"]["cells"]:
            cell["checkpoint_sha256"] = "f" * 64

    cases = (
        ("certificate_provenance", provenance_tamper("audit_certificate")),
        ("panel_provenance", provenance_tamper("evaluation_panel")),
        ("vector_provenance", provenance_tamper("quantity_vector")),
        ("audit_cross_digest", audit_cross_tamper),
        ("panel_cross_digest", panel_cross_tamper),
        ("checkpoint_cross_digest", checkpoint_cross_tamper),
    )
    for name, mutate in cases:
        launcher, *_ = build(tmp_path / name, mutate)
        with pytest.raises(IntegrityError):
            launcher._load_finished_seed(0)
    manifest_tamper, *_ = build(tmp_path / "sealed_reference_provenance", tamper_manifest=True)
    with pytest.raises(IntegrityError):
        manifest_tamper._load_finished_seed(0)
