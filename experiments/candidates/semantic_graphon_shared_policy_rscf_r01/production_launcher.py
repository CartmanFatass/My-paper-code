"""Exact one-worker launcher for the frozen SGSP RSCF-r01 complete panel."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import torch

from envs.native.production_backend import (
    RIDGEGATE_2Z_FULL_ENVIRONMENT,
    require_cpp_batched_production,
)

from .production_boundary import (
    MINIMUM_AVAILABLE_MEMORY_BYTES,
    MINIMUM_SYSTEM_RESERVE_BYTES,
    RSS_CEILING_BYTES,
    BlindedSeedFrontier,
    EmpiricalCoordinateAdapter,
    IntegrityError,
    ProductionLifecycleStore,
    ValidatedRootLease,
    canonical_json_bytes,
    mint_or_resume_empirical_master,
    resume_empirical_master_through_lineage,
    validate_root_lease,
    _working_set_bytes,
)
from .production_runner import (
    ProductionAuditCertificate,
    ProductionEvaluationCell,
    ProductionEvaluationPanel,
    ProductionIdentity,
)
from .continuation_lineage import (
    AuthenticatedContinuationCut,
    ContinuationIdentity,
    ContinuationLineage,
    ContinuationLineageError,
    OwnerAuthenticatedContinuationCut,
    source_epoch_provenance,
)


LAUNCHER_SCHEMA = "SGSP_RSCF_R01_ONE_WORKER_COMPLETE_PANEL_LAUNCHER_V1"


@dataclass(frozen=True)
class ContinuationLaunchInputs:
    predecessor_lease: Any
    continuation_lease: Any
    lineage: ContinuationLineage
    continuation_identity: ContinuationIdentity
    cut: AuthenticatedContinuationCut | OwnerAuthenticatedContinuationCut
    predecessor_identity: ProductionIdentity


def system_available_memory_bytes() -> int:
    """Read current whole-system available physical memory on Windows."""

    import ctypes

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(status)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MEMORYSTATUSEX)]
    kernel32.GlobalMemoryStatusEx.restype = ctypes.c_int
    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError(ctypes.get_last_error(), "GlobalMemoryStatusEx failed")
    return int(status.ullAvailPhys)


def _analysis_payload(analysis: Any) -> dict[str, Any]:
    return {
        "schema_version": analysis.schema_version,
        "namespace": analysis.namespace,
        "support_formula_set_sha256": analysis.support_formula_set_sha256,
        "intervals": {name: asdict(value) for name, value in sorted(analysis.intervals.items())},
        "predicates": [asdict(value) for value in analysis.predicates],
        "result_branch": analysis.result_branch.value,
        "additional_labels": list(analysis.additional_labels),
        "failed_predicates": list(analysis.failed_predicates),
        "structural_failures": list(analysis.structural_failures),
        "analysis_sha256": analysis.digest,
    }


class ProductionPanelLauncher:
    """Run or atomically resume the indivisible 24-seed panel."""

    def __init__(self, lease: ValidatedRootLease) -> None:
        self.lease = lease
        self.master = mint_or_resume_empirical_master(lease)
        self.coordinates = EmpiricalCoordinateAdapter(lease, self.master)
        self.lifecycle = ProductionLifecycleStore(lease, self.coordinates)
        self.continuation_inputs: ContinuationLaunchInputs | None = None
        self._authenticated_cut_frontier: Any | None = None

    @classmethod
    def _wire_continuation(
        cls,
        inputs: ContinuationLaunchInputs,
        *,
        resume_master: Callable[..., Any],
        coordinate_factory: Callable[[Any, Any], Any],
        lifecycle_factory: Callable[..., Any],
        require_production_types: bool,
    ) -> "ProductionPanelLauncher":
        if require_production_types:
            if (
                type(inputs.predecessor_lease) is not ValidatedRootLease
                or type(inputs.continuation_lease) is not ValidatedRootLease
                or type(inputs.cut) is not OwnerAuthenticatedContinuationCut
            ):
                raise IntegrityError("production continuation requires exact owner-authenticated inputs")
        else:
            if (
                type(inputs.cut) is not AuthenticatedContinuationCut
                or inputs.cut.test_only_marker != "TEST_ONLY_SYNTHETIC_GENERATION154"
                or getattr(inputs.predecessor_lease, "test_only", None) is not True
                or getattr(inputs.continuation_lease, "test_only", None) is not True
            ):
                raise IntegrityError("sealed continuation wiring accepts TEST-only injected inputs")
        try:
            inputs.continuation_identity.require_exact_lineage(inputs.lineage)
            cut_frontier = inputs.cut.authenticate(inputs.lineage)
        except ContinuationLineageError as exc:
            raise IntegrityError(str(exc)) from exc
        if (
            inputs.predecessor_identity.digest
            != inputs.lineage.predecessor_production_identity_sha256
            or inputs.predecessor_lease.lease_lineage_id != inputs.lineage.lease_lineage_id
            or inputs.continuation_lease.lease_lineage_id != inputs.lineage.lease_lineage_id
            or inputs.predecessor_lease.source_binding.digest
            != inputs.lineage.predecessor_source_binding_sha256
            or inputs.continuation_lease.source_binding.digest
            != inputs.lineage.continuation_source_binding_sha256
        ):
            raise IntegrityError("continuation launcher inputs differ from the A-to-B lineage")
        master = resume_master(
            inputs.predecessor_lease,
            inputs.continuation_lease,
            inputs.lineage,
            inputs.continuation_identity,
        )
        if master.commitment_sha256 != inputs.lineage.predecessor_master_commitment_sha256:
            raise IntegrityError("continuation launcher master commitment changed")
        coordinates = coordinate_factory(inputs.continuation_lease, master)
        if coordinates.manifest_sha256 != inputs.lineage.predecessor_coordinate_manifest_sha256:
            raise IntegrityError("continuation launcher coordinate manifest changed")
        provenance = source_epoch_provenance(inputs.lineage, inputs.continuation_identity)
        lifecycle = lifecycle_factory(
            inputs.continuation_lease,
            coordinates,
            source_epoch_provenance=provenance,
        )
        launcher = cls.__new__(cls)
        launcher.lease = inputs.continuation_lease
        launcher.master = master
        launcher.coordinates = coordinates
        launcher.lifecycle = lifecycle
        launcher.continuation_inputs = inputs
        launcher._authenticated_cut_frontier = cut_frontier
        return launcher

    @classmethod
    def for_continuation(
        cls, inputs: ContinuationLaunchInputs
    ) -> "ProductionPanelLauncher":
        """Activate B only from exact owner-authorized production objects."""

        return cls._wire_continuation(
            inputs,
            resume_master=resume_empirical_master_through_lineage,
            coordinate_factory=EmpiricalCoordinateAdapter,
            lifecycle_factory=ProductionLifecycleStore,
            require_production_types=True,
        )

    @classmethod
    def for_sealed_test_continuation(
        cls,
        inputs: ContinuationLaunchInputs,
        *,
        resume_master: Callable[..., Any],
        coordinate_factory: Callable[[Any, Any], Any],
        lifecycle_factory: Callable[..., Any],
    ) -> "ProductionPanelLauncher":
        """Reach the same wiring using injected TEST-only objects and no paths."""

        return cls._wire_continuation(
            inputs,
            resume_master=resume_master,
            coordinate_factory=coordinate_factory,
            lifecycle_factory=lifecycle_factory,
            require_production_types=False,
        )

    def _load_finished_seed(self, seed_block_index: int):
        from .production_runner import (
            ProductionSeedQuantityVector,
            ProductionSeedResult,
            require_complete_seed_provenance,
        )
        sealed_path = self.lifecycle.root / "sealed" / f"SB{seed_block_index:02d}.bin"
        if not sealed_path.exists():
            return None
        reference = self.lifecycle.read_sealed_seed_result_ref(
            seed_block_index, self.master
        )
        payload = self.lifecycle.read_sealed_seed_result(reference, self.master)
        if (
            set(payload) != {
                "schema", "namespace", "seed_block_index", "audit_certificate",
                "evaluation_panel", "quantity_vector",
            }
            or payload.get("schema") != "SGSP_RSCF_R01_SEALED_SEED_RESULT_V1"
            or payload.get("namespace") != self.coordinates.namespace
            or payload.get("seed_block_index") != seed_block_index
        ):
            raise IntegrityError("finished seed sealed payload identity changed")
        certificate = ProductionAuditCertificate(**payload["audit_certificate"])
        panel_data = payload["evaluation_panel"]
        panel = ProductionEvaluationPanel(
            namespace=panel_data["namespace"],
            seed_block_id=panel_data["seed_block_id"],
            checkpoint_sha256=panel_data["checkpoint_sha256"],
            audit_certificate_sha256=panel_data["audit_certificate_sha256"],
            cells=tuple(ProductionEvaluationCell(**item) for item in panel_data["cells"]),
            schema_version=panel_data["schema_version"],
            continuation_identity_sha256=panel_data.get("continuation_identity_sha256"),
            lineage_sha256=panel_data.get("lineage_sha256"),
            source_epoch_provenance=panel_data.get("source_epoch_provenance"),
        )
        vector = ProductionSeedQuantityVector(**payload["quantity_vector"])
        checkpoint = self.lifecycle.read_update512_checkpoint_ref(seed_block_index)
        result = ProductionSeedResult(
            seed_block_index, checkpoint, certificate, panel, vector, reference
        )
        require_complete_seed_provenance(
            seed_block_index=seed_block_index,
            checkpoint=checkpoint,
            certificate=certificate,
            panel=panel,
            vector=vector,
            sealed_ref=reference,
            expected_source_epoch_provenance=self.lifecycle.source_epoch_provenance,
        )
        return result

    def _require_current_root_lease(self, stage: str) -> None:
        """Fail closed if the exact Root authorization is no longer current."""

        now = datetime.now(timezone.utc)
        if now >= self.lease.valid_until:
            raise IntegrityError(f"Root lease expired before {stage}")
        try:
            current = validate_root_lease(
                self.lease.lease_path,
                now_utc=now,
                available_memory_bytes=None,
                load_native=False,
                require_full_projection=False,
            )
        except (OSError, ValueError) as exc:
            raise IntegrityError(f"Root lease is not current before {stage}: {exc}") from exc
        if (
            current.lease_payload_sha256 != self.lease.lease_payload_sha256
            or current.lease_lineage_id != self.lease.lease_lineage_id
            or current.source_binding.digest != self.lease.source_binding.digest
        ):
            raise IntegrityError(f"Root lease authority changed before {stage}")

    def _finish_seed_under_current_lease(self, engine: Any):
        """Keep evaluation and persistent seed publication on separate lease edges."""

        self._require_current_root_lease("seed evaluation")
        evaluated = engine.finish_seed_evaluation()
        # Evaluation has returned but no sealed per-seed result exists yet.
        self._require_current_root_lease("sealed per-seed publication")
        seed_result = engine.publish_evaluated_seed(evaluated)
        self._require_current_root_lease("post-sealed-seed continuation")
        return seed_result

    def run(self) -> dict[str, Any]:
        from .production_runner import ProductionSeedEngine, analyze_complete_production_family

        results = []
        for seed_block_index in range(24):
            finished = self._load_finished_seed(seed_block_index)
            if finished is not None:
                results.append(finished)
                continue
            continuation = self.continuation_inputs
            engine = ProductionSeedEngine(
                self.lease, self.master, self.coordinates, self.lifecycle,
                seed_block_index=seed_block_index,
                continuation_lineage=(None if continuation is None else continuation.lineage),
                continuation_identity=(
                    None if continuation is None else continuation.continuation_identity
                ),
            )
            prior_frontier = self.lifecycle.latest_resume_frontier(seed_block_index)
            lineage_predecessor_frontier = None
            previous_b_frontier = None
            if prior_frontier is not None:
                if (
                    continuation is not None
                    and seed_block_index == continuation.lineage.cut_seed_block_index
                    and prior_frontier.generation == continuation.lineage.cut_generation
                    and prior_frontier.source_binding_sha256
                    == continuation.lineage.predecessor_source_binding_sha256
                ):
                    expected_predecessor = BlindedSeedFrontier(
                        **dict(self._authenticated_cut_frontier)
                    )
                    if prior_frontier != expected_predecessor:
                        raise IntegrityError("retained predecessor frontier differs from owner cut bytes")
                    engine.import_continuation_state(
                        continuation.cut, continuation.predecessor_identity
                    )
                    lineage_predecessor_frontier = prior_frontier
                else:
                    engine.restore_resume_state(
                        self.lifecycle.read_resume_state(seed_block_index, prior_frontier)
                    )
                    previous_b_frontier = prior_frontier
                if engine.completed_updates != prior_frontier.completed_updates:
                    raise IntegrityError("resumed engine/frontier update mismatch")
            elif (
                continuation is not None
                and seed_block_index == continuation.lineage.cut_seed_block_index
            ):
                raise IntegrityError("owner-authorized predecessor cut is absent from the retained root")
            for update_index in range(engine.completed_updates, 512):
                receipt = engine.run_update(update_index)
                if not receipt.structural_valid:
                    self.lifecycle.write_nonvalue_conformance_diagnostic(
                        receipt.nonvalue_diagnostic(
                            seed_block_index=seed_block_index,
                            completed_updates=engine.completed_updates,
                        )
                    )
                    raise IntegrityError(
                        f"production update {update_index} failed structural audits: {receipt.audit_failures}"
                    )
                frontier = engine.frontier(update_index + 1)
                if lineage_predecessor_frontier is not None:
                    frontier.require_lineage_successor_of(
                        lineage_predecessor_frontier,
                        continuation_identity_sha256=continuation.continuation_identity.digest,
                        lineage_sha256=continuation.lineage.digest,
                        predecessor_source_binding_sha256=(
                            continuation.lineage.predecessor_source_binding_sha256
                        ),
                    )
                    lineage_predecessor_frontier = None
                elif previous_b_frontier is not None:
                    frontier.require_successor_of(previous_b_frontier)
                self.lifecycle.write_frontier(frontier)
                self.lifecycle.write_resume_state(
                    seed_block_index, update_index + 1,
                    engine.serialize_resume_state(), frontier,
                )
                previous_b_frontier = frontier
                if datetime.now(timezone.utc) >= self.lease.valid_until:
                    raise IntegrityError("Root lease expired after an atomic resume frontier")
                rss = _working_set_bytes()
                if rss is not None and rss > RSS_CEILING_BYTES:
                    raise IntegrityError("process RSS exceeded the Root lease ceiling after an atomic resume frontier")
                if system_available_memory_bytes() < MINIMUM_SYSTEM_RESERVE_BYTES:
                    raise IntegrityError("whole-system reserve fell below 4 GiB after an atomic resume frontier")
            results.append(self._finish_seed_under_current_lease(engine))
        self._require_current_root_lease("family analysis")
        analysis = analyze_complete_production_family(results)
        self._require_current_root_lease("post-family-analysis continuation")
        complete_payload = {
            "kind": "ATOMIC_COMPLETE_24_SEED_PANEL",
            "science_revision": "SGSP-RG2Z-RSCF-SCIENCE-20260821-01",
            "seed_rows": [
                {
                    "seed_block_index": item.seed_block_index,
                    "quantities": dict(item.quantity_vector.values),
                    "evaluation_panel_sha256": item.evaluation_panel.digest,
                    "audit_certificate_sha256": item.audit_certificate.digest,
                }
                for item in sorted(results, key=lambda item: item.seed_block_index)
            ],
            "analysis": _analysis_payload(analysis),
        }
        self._require_current_root_lease("complete-panel publication")
        result_sha256 = self.lifecycle.install_complete_result(
            complete_payload,
            checkpoints=[item.checkpoint for item in results],
            seed_results=[item.sealed_ref for item in results],
            master=self.master,
        )
        self._require_current_root_lease("post-complete-panel publication")
        return {
            "schema": LAUNCHER_SCHEMA,
            "complete_result_sha256": result_sha256,
            "complete_result_path": str(
                self.lifecycle.root / "complete" / "SGSP_RG2Z_RSCF_R01_PANEL.json"
            ),
            "seed_blocks": 24,
            "updates_per_seed": 512,
            "outer_workers": 1,
            "width": 32,
            "partial_evaluable": False,
        }


def sealed_test_service_graph(
    *,
    admit: Callable[[], object],
    master: Callable[[object], object],
    coordinates: Callable[[object, object], object],
    initializer: Callable[[object, object, object], object],
    lifecycle: Callable[[object, object], object],
    engine: Callable[[object, object, object, object, object], object],
) -> tuple[str, ...]:
    """Exercise ordering with TEST doubles only; no production class is used."""

    events: list[str] = []
    admitted = admit(); events.append("lease_validated")
    bound_master = master(admitted); events.append("master_created")
    plan = coordinates(admitted, bound_master); events.append("coordinates_bound")
    parameters = initializer(admitted, bound_master, plan); events.append("parameters_initialized")
    store = lifecycle(admitted, plan); events.append("lifecycle_bound")
    engine(admitted, bound_master, plan, parameters, store); events.append("engine_bound")
    return tuple(events)


def _preflight_service_graph() -> tuple[str, ...]:
    class Double:
        pass
    return sealed_test_service_graph(
        admit=Double,
        master=lambda _: Double(),
        coordinates=lambda _a, _b: Double(),
        initializer=lambda _a, _b, _c: Double(),
        lifecycle=lambda _a, _b: Double(),
        engine=lambda _a, _b, _c, _d, _e: Double(),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SGSP RSCF-r01 one-worker production launcher")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lease", type=Path)
    group.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--preflight-root", type=Path)
    parser.add_argument("--preflight-artifact", type=Path)
    args = parser.parse_args(argv)
    if args.preflight_only:
        if args.preflight_root is None or args.preflight_artifact is None:
            parser.error("--preflight-only requires --preflight-root and --preflight-artifact")
        from .production_preflight import (
            install_extended_preflight_artifact,
            run_extended_test_preflight,
        )
        report = run_extended_test_preflight(args.preflight_root, _preflight_service_graph)
        artifact_path, artifact_file_sha = install_extended_preflight_artifact(
            report, args.preflight_artifact
        )
        output = {
            **report,
            "production_preflight_artifact_path": str(artifact_path),
            "production_preflight_artifact_file_sha256": artifact_file_sha,
        }
        print(canonical_json_bytes(output).decode("ascii"))
        return 0
    if args.preflight_root is not None or args.preflight_artifact is not None:
        parser.error("TEST-only preflight arguments cannot accompany --lease")
    available = system_available_memory_bytes()
    require_cpp_batched_production(
        RIDGEGATE_2Z_FULL_ENVIRONMENT,
        backend="cpp",
        batch_width=32,
    )
    lease = validate_root_lease(
        args.lease, now_utc=datetime.now(timezone.utc),
        available_memory_bytes=available, load_native=True,
    )
    # No master/coordinate/model/output exists before the preceding line.
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    result = ProductionPanelLauncher(lease).run()
    print(canonical_json_bytes(result).decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
