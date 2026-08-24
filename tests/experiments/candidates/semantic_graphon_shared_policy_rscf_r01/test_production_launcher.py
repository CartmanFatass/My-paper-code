from __future__ import annotations

import inspect
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.native_contract import (
    make_test_actor_parameters,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.native_loader import (
    native_factual_trajectory,
)

from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_launcher import (
    ContinuationLaunchInputs,
    ProductionPanelLauncher,
    _preflight_service_graph,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_runner import (
    ProductionIdentity,
    ProductionSeedEngine,
    _ArmState,
    _uniform_grid,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.contracts import TestIdentity as RSCFTestIdentity
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.policy import (
    ACTOR_PARAMETER_SHAPES,
    CRITIC_PARAMETER_SHAPES,
    RSCFActor,
    TerminalCritic,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.runner import RSCFGateBRunner
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.training import make_projected_adam
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary import (
    BlindedSeedFrontier,
    IntegrityError,
    LeaseValidationError,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.continuation_lineage import (
    AuthenticatedContinuationCut,
    ContinuationIdentity,
    ContinuationLineage,
    canonical_json_bytes,
    canonical_sha256,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.contracts import (
    RESERVED_SCIENTIFIC_NAMESPACE,
)


def test_vectorized_test_only_coordinate_tapes_are_deterministic_bounded_and_roster_separated() -> None:
    kwargs = dict(
        key=0x544553545F4F4E4C,
        kind=4,
        phase=1,
        roster=9,
        update=0,
        episode_indices=np.arange(32, dtype=np.uint64)[:, None, None],
        slot_indices=np.arange(12, dtype=np.uint64)[None, :, None],
        sender_indices=np.arange(21, dtype=np.uint64)[None, None, :],
        receiver_indices=np.zeros((1, 1, 1), dtype=np.uint64),
    )
    first = _uniform_grid(**kwargs)
    second = _uniform_grid(**kwargs)
    changed_roster = _uniform_grid(**{**kwargs, "roster": 15})
    assert first.shape == (32, 12, 21)
    assert first.dtype == np.float32
    assert np.array_equal(first, second)
    assert not np.array_equal(first, changed_roster)
    assert np.all((first >= 0.0) & (first < 1.0))


def test_sealed_test_service_graph_proves_lease_first_order_without_production_objects() -> None:
    assert _preflight_service_graph() == (
        "lease_validated",
        "master_created",
        "coordinates_bound",
        "parameters_initialized",
        "lifecycle_bound",
        "engine_bound",
    )


def _test_only_launcher_with_lease(*, valid_until: datetime) -> ProductionPanelLauncher:
    launcher = ProductionPanelLauncher.__new__(ProductionPanelLauncher)
    launcher.lease = SimpleNamespace(
        valid_until=valid_until,
        lease_path=Path("TEST_ONLY_ROOT_LEASE.json"),
        lease_payload_sha256="a" * 64,
        lease_lineage_id="TEST_ONLY_LINEAGE",
        source_binding=SimpleNamespace(digest="b" * 64),
    )
    return launcher


def test_production_finalization_rejects_expired_root_lease_before_revalidation() -> None:
    launcher = _test_only_launcher_with_lease(
        valid_until=datetime.now(timezone.utc) - timedelta(seconds=1)
    )
    with pytest.raises(IntegrityError, match="expired before seed evaluation"):
        launcher._require_current_root_lease("seed evaluation")


def test_production_finalization_rejects_suspended_root_lease(monkeypatch) -> None:
    import experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_launcher as launcher_module
    launcher = _test_only_launcher_with_lease(
        valid_until=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    def suspended(*_args, **_kwargs):
        raise LeaseValidationError("lease field state differs from the accepted mode-one envelope")

    monkeypatch.setattr(launcher_module, "validate_root_lease", suspended)
    with pytest.raises(IntegrityError, match="not current before family analysis"):
        launcher._require_current_root_lease("family analysis")


def test_production_seed_publication_is_fenced_after_evaluation_returns(monkeypatch) -> None:
    launcher = ProductionPanelLauncher.__new__(ProductionPanelLauncher)
    events = []

    class TestOnlyEngine:
        def finish_seed_evaluation(self):
            events.append("evaluation_returned")
            return object()

        def publish_evaluated_seed(self, _evaluated):
            events.append("sealed_publication")
            return object()

    def suspend_at_publication(stage):
        events.append(f"lease:{stage}")
        if stage == "sealed per-seed publication":
            raise IntegrityError("TEST-only suspended lease")

    monkeypatch.setattr(launcher, "_require_current_root_lease", suspend_at_publication)
    with pytest.raises(IntegrityError, match="suspended lease"):
        launcher._finish_seed_under_current_lease(TestOnlyEngine())
    assert events == [
        "lease:seed evaluation",
        "evaluation_returned",
        "lease:sealed per-seed publication",
    ]


def test_production_run_revalidates_lease_at_every_finalization_boundary() -> None:
    finish_source = inspect.getsource(ProductionPanelLauncher._finish_seed_under_current_lease)
    run_source = inspect.getsource(ProductionPanelLauncher.run)
    for stage in (
        "seed evaluation",
        "sealed per-seed publication",
        "post-sealed-seed continuation",
    ):
        assert f'_require_current_root_lease("{stage}")' in finish_source
    for stage in (
        "family analysis",
        "post-family-analysis continuation",
        "complete-panel publication",
        "post-complete-panel publication",
    ):
        assert f'_require_current_root_lease("{stage}")' in run_source
    assert "finish_seed()" not in finish_source + run_source


def test_production_engine_carries_arm_state_and_uses_native_hot_path_without_test_identity() -> None:
    init_source = inspect.getsource(ProductionSeedEngine.__init__)
    update_source = inspect.getsource(ProductionSeedEngine.run_update)
    trace_source = inspect.getsource(ProductionSeedEngine._trace_batches)
    evaluation_source = inspect.getsource(ProductionSeedEngine._evaluation_accumulators)
    finish_evaluation_source = inspect.getsource(ProductionSeedEngine.finish_seed_evaluation)
    publish_source = inspect.getsource(ProductionSeedEngine.publish_evaluated_seed)
    assert "TestIdentity" not in init_source
    assert "make_test" not in init_source + update_source + trace_source + evaluation_source
    assert "self._arms" in init_source and "self._arms" in update_source
    assert "native_factual_trajectory" in trace_source
    assert "native_factual_trajectory" in evaluation_source
    assert "native_shadow_trajectory" in evaluation_source
    assert "native_full_suffix" not in trace_source  # suffix calls stay in the accepted runner helper
    assert "verify_reverse_order=False" in update_source
    assert "install_sealed_seed_result" not in finish_evaluation_source
    assert "install_sealed_seed_result" in publish_source


def test_production_tape_builder_feeds_native_v4_fp32_with_test_only_dependency_double() -> None:
    class TestOnlyCoordinates:
        @staticmethod
        def _seed_secret(_index: int) -> bytes:
            return b"TEST_ONLY_COORDINATE_KEY_000000"[:32]

        def uniform_grid(
            self,
            *,
            seed_block_index: int,
            phase: str,
            roster_size: int,
            update_index: int,
            random_variable_kind: str,
            episode_indices: np.ndarray,
            slot_indices: np.ndarray,
            sender_indices: np.ndarray,
            receiver_indices: np.ndarray,
        ) -> np.ndarray:
            del seed_block_index
            kinds = {
                "event_time": 1,
                "detection_uniform": 2,
                "base_uniform": 3,
                "action_uniform": 4,
                "uplink_uniform": 5,
            }
            return _uniform_grid(
                0x544553545F4F4E4C,
                kind=kinds[random_variable_kind],
                phase=1 if phase == "TRAINING" else 2,
                roster=roster_size,
                update=update_index,
                episode_indices=episode_indices,
                slot_indices=slot_indices,
                sender_indices=sender_indices,
                receiver_indices=receiver_indices,
            )

        @staticmethod
        def event_times(*, episode_index: int, basin: int, **_kwargs):
            base = (episode_index + 2 * basin) % 6
            return (base, (base + 2) % 8, (base + 5) % 8)

    engine = ProductionSeedEngine.__new__(ProductionSeedEngine)
    engine.coordinates = TestOnlyCoordinates()
    engine.seed_block_index = 0
    batch = engine._episode_batch(
        roster=9,
        update=0,
        episode_offset=0,
        phase="TRAINING",
        schedule=None,
    )
    trajectory = native_factual_trajectory(batch, make_test_actor_parameters())
    assert batch.n_agents.tolist() == [9] * 32
    assert trajectory.active.tolist() == [True] * 32
    assert trajectory.terminal_return.shape == (32,)
    assert np.isfinite(trajectory.terminal_return).all()


def test_one_production_orchestration_update_runs_with_test_only_identity_and_coordinates() -> None:
    class TestOnlyCoordinates:
        manifest_sha256 = "a" * 64

        @staticmethod
        def _seed_secret(_index: int) -> bytes:
            return b"TEST_ONLY_ORCHESTRATION_KEY_000"[:32]

        def origin(self, *, seed_block_index, update_index, roster_size, pair_index, side, role_index):
            del seed_block_index
            base = (5 * pair_index + 3 * role_index + update_index + 2) % 12
            local = (pair_index + side + role_index + update_index) % (roster_size // 3)
            return SimpleNamespace(
                base_slot=base,
                selected_slot=base if side == 0 else 11 - base,
                role_local_index=local,
                address_sha256=f"{pair_index:02x}{side:02x}{role_index:02x}".ljust(64, "0"),
            )

        def uniform_grid(self, *, seed_block_index, phase, roster_size, update_index, random_variable_kind, episode_indices, slot_indices, sender_indices, receiver_indices):
            del seed_block_index
            kinds = {"event_time": 1, "detection_uniform": 2, "base_uniform": 3, "action_uniform": 4, "uplink_uniform": 5}
            return _uniform_grid(
                0x544553545F4F4E4C,
                kind=kinds[random_variable_kind], phase=1 if phase == "TRAINING" else 2,
                roster=roster_size, update=update_index,
                episode_indices=episode_indices, slot_indices=slot_indices,
                sender_indices=sender_indices, receiver_indices=receiver_indices,
            )

        @staticmethod
        def event_times(*, episode_index: int, basin: int, **_kwargs):
            base = (episode_index + 2 * basin) % 6
            return (base, (base + 2) % 8, (base + 5) % 8)

    def parameters(shapes, phase):
        result = {}
        cursor = phase * 101
        for name, shape in shapes.items():
            count = math.prod(shape)
            values = torch.arange(cursor, cursor + count, dtype=torch.float32)
            result[name] = (0.015 * torch.sin(values * 0.017 + phase)).reshape(shape).contiguous()
            cursor += count
        return result

    actor_parameters = parameters(ACTOR_PARAMETER_SHAPES, 1)
    critic_parameters = parameters(CRITIC_PARAMETER_SHAPES, 2)
    helper = RSCFGateBRunner(
        RSCFTestIdentity("CASE_SERVICE"),
        actor_parameters=actor_parameters,
        critic_parameters=critic_parameters,
        width=32,
    )
    engine = ProductionSeedEngine.__new__(ProductionSeedEngine)
    engine.coordinates = TestOnlyCoordinates()
    engine.seed_block_index = 0
    engine.identity = SimpleNamespace(namespace="TEST_ONLY|SGSP-RSCF-SERVICE")
    engine._helper = helper
    engine.native_identity = helper.native_identity
    engine._arms = {}
    for arm in ("PHY-TRUST", "EDGE-FLEX"):
        actor = RSCFActor(actor_parameters)
        critic = TerminalCritic(critic_parameters)
        engine._arms[arm] = _ArmState(actor, critic, make_projected_adam(actor, critic))
    engine.completed_updates = 0
    engine._rolling_origin_digest = "0" * 64
    engine._update_receipts = []
    receipt = engine.run_update(0)
    assert receipt.structural_valid
    assert receipt.q_entry_count == 1280
    assert receipt.alternative_count == 896
    assert receipt.batch_roster_order == (9, 15) * 32
    assert engine.completed_updates == 1


def test_injected_test_only_launcher_reaches_import_and_exactly_one_lineage_edge(monkeypatch) -> None:
    source_a, source_b = "a" * 64, "b" * 64
    master_digest, coordinates_digest = "c" * 64, "d" * 64
    lease_lineage = "SGSP-RG2Z-RSCF-R01-LINEAGE-TEST_ONLY-LAUNCHER"
    predecessor_identity = ProductionIdentity(
        RESERVED_SCIENTIFIC_NAMESPACE,
        lease_lineage,
        master_digest,
        coordinates_digest,
        source_a,
    )
    state_bytes = b"TEST_ONLY_ALREADY_AUTHENTICATED_RESUME_STATE"
    frontier_core = {
        "seed_block_index": 0,
        "generation": 154,
        "completed_updates": 154,
        "completed_origin_count": 154 * 384,
        "completed_origin_set_sha256": "e" * 64,
        "coordinate_manifest_sha256": coordinates_digest,
        "source_binding_sha256": source_a,
        "evaluable": False,
    }
    frontier_payload = {"kind": "BLINDED_NON_EVALUABLE_SEED_FRONTIER", **frontier_core}
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
        lease_lineage_id=lease_lineage,
        predecessor_production_identity_sha256=predecessor_identity.digest,
        predecessor_source_binding_sha256=source_a,
        predecessor_master_commitment_sha256=master_digest,
        predecessor_coordinate_manifest_sha256=coordinates_digest,
        cut_seed_block_index=0,
        cut_frontier_sha256=digests["frontier"],
        cut_resume_commit_sha256=digests["commit"],
        cut_resume_metadata_sha256=digests["metadata"],
        cut_resume_state_sha256=digests["state"],
        continuation_source_binding_sha256=source_b,
    )
    continuation_identity = ContinuationIdentity.bind(lineage)
    predecessor_lease = SimpleNamespace(
        test_only=True, lease_lineage_id=lease_lineage,
        source_binding=SimpleNamespace(digest=source_a),
    )
    continuation_lease = SimpleNamespace(
        test_only=True, lease_lineage_id=lease_lineage,
        source_binding=SimpleNamespace(digest=source_b),
        valid_until=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    inputs = ContinuationLaunchInputs(
        predecessor_lease, continuation_lease, lineage,
        continuation_identity, cut, predecessor_identity,
    )
    with pytest.raises(IntegrityError, match="exact owner-authenticated"):
        ProductionPanelLauncher.for_continuation(inputs)

    events: list[str] = []
    master = SimpleNamespace(commitment_sha256=master_digest)
    coordinates = SimpleNamespace(
        manifest_sha256=coordinates_digest,
        namespace=RESERVED_SCIENTIFIC_NAMESPACE,
    )

    class TestLifecycle:
        def __init__(self, provenance):
            self.source_epoch_provenance = provenance
            self.root = Path("TEST_ONLY_NO_IO")
            self.frontiers = []
            self.resume_generations = []

        def _provenance_fields(self):
            return {
                "continuation_identity_sha256": continuation_identity.digest,
                "lineage_sha256": lineage.digest,
                "predecessor_source_binding_sha256": source_a,
                "cut_generation": 154,
            }

        def latest_resume_frontier(self, seed):
            return BlindedSeedFrontier(**frontier_core) if seed == 0 else None

        def write_frontier(self, frontier):
            self.frontiers.append(frontier)

        def write_resume_state(self, seed, generation, data, frontier):
            assert seed == 0 and data == b"TEST_ONLY_B_RESUME"
            assert frontier.generation == generation
            self.resume_generations.append(generation)

        def install_complete_result(self, *_args, **kwargs):
            assert len(kwargs["checkpoints"]) == len(kwargs["seed_results"]) == 24
            return "9" * 64

    lifecycle_holder = {}

    def resume_master(*args):
        assert args == (predecessor_lease, continuation_lease, lineage, continuation_identity)
        events.append("resume_empirical_master_through_lineage")
        return master

    def coordinate_factory(lease, observed_master):
        assert lease is continuation_lease and observed_master is master
        events.append("coordinates_bound")
        return coordinates

    def lifecycle_factory(lease, observed_coordinates, *, source_epoch_provenance):
        assert lease is continuation_lease and observed_coordinates is coordinates
        events.append("source_epoch_lifecycle_bound")
        lifecycle_holder["value"] = TestLifecycle(source_epoch_provenance)
        return lifecycle_holder["value"]

    launcher = ProductionPanelLauncher.for_sealed_test_continuation(
        inputs,
        resume_master=resume_master,
        coordinate_factory=coordinate_factory,
        lifecycle_factory=lifecycle_factory,
    )

    class FakeEngine:
        def __init__(self, *_args, seed_block_index, **_kwargs):
            assert seed_block_index == 0
            self.completed_updates = 0
            self.imported = False

        def import_continuation_state(self, observed_cut, observed_predecessor):
            assert observed_cut is cut and observed_predecessor is predecessor_identity
            self.completed_updates = 154
            self.imported = True
            events.append("cut_imported")

        def restore_resume_state(self, _data):
            raise AssertionError("A state must use explicit continuation import")

        def run_update(self, index):
            assert self.imported and index == self.completed_updates
            self.completed_updates += 1
            return SimpleNamespace(structural_valid=True, audit_failures=())

        def frontier(self, generation):
            return BlindedSeedFrontier(
                0, generation, self.completed_updates, self.completed_updates * 384,
                f"{generation:064x}"[-64:], coordinates_digest, source_b,
                **lifecycle_holder["value"]._provenance_fields(),
            )

        @staticmethod
        def serialize_resume_state():
            return b"TEST_ONLY_B_RESUME"

    class FakeResult:
        def __init__(self, seed):
            self.seed_block_index = seed
            self.quantity_vector = SimpleNamespace(values={})
            self.evaluation_panel = SimpleNamespace(digest="6" * 64)
            self.audit_certificate = SimpleNamespace(digest="7" * 64)
            self.checkpoint = SimpleNamespace(seed_block_index=seed)
            self.sealed_ref = SimpleNamespace(seed_block_index=seed)

    import experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_runner as runner_module
    import experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_launcher as launcher_module

    monkeypatch.setattr(runner_module, "ProductionSeedEngine", FakeEngine)
    monkeypatch.setattr(
        runner_module,
        "analyze_complete_production_family",
        lambda _results: SimpleNamespace(
            schema_version="TEST_ONLY", namespace=RESERVED_SCIENTIFIC_NAMESPACE,
            support_formula_set_sha256="8" * 64, intervals={}, predicates=(),
            result_branch=SimpleNamespace(value="TEST_ONLY"), additional_labels=(),
            failed_predicates=(), structural_failures=(), digest="5" * 64,
        ),
    )
    monkeypatch.setattr(launcher_module, "_working_set_bytes", lambda: None)
    monkeypatch.setattr(launcher_module, "system_available_memory_bytes", lambda: 1 << 40)
    monkeypatch.setattr(launcher, "_require_current_root_lease", lambda _stage: None)
    monkeypatch.setattr(
        launcher, "_load_finished_seed",
        lambda seed: None if seed == 0 else FakeResult(seed),
    )
    monkeypatch.setattr(
        launcher, "_finish_seed_under_current_lease", lambda _engine: FakeResult(0)
    )
    lineage_calls = 0
    ordinary_calls = 0
    original_lineage = BlindedSeedFrontier.require_lineage_successor_of
    original_ordinary = BlindedSeedFrontier.require_successor_of

    def count_lineage(self, previous, **kwargs):
        nonlocal lineage_calls
        lineage_calls += 1
        return original_lineage(self, previous, **kwargs)

    def count_ordinary(self, previous):
        nonlocal ordinary_calls
        ordinary_calls += 1
        return original_ordinary(self, previous)

    monkeypatch.setattr(BlindedSeedFrontier, "require_lineage_successor_of", count_lineage)
    monkeypatch.setattr(BlindedSeedFrontier, "require_successor_of", count_ordinary)
    result = launcher.run()
    assert result["complete_result_sha256"] == "9" * 64
    assert events == [
        "resume_empirical_master_through_lineage",
        "coordinates_bound",
        "source_epoch_lifecycle_bound",
        "cut_imported",
    ]
    assert lineage_calls == 1
    assert ordinary_calls == 357
    assert lifecycle_holder["value"].resume_generations == list(range(155, 513))
