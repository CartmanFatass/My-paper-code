from __future__ import annotations

import base64
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value import production
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.artifacts import (
    AdapterFinalReceipt,
    FinalPanelReceipt,
    FoundationFinalReceipt,
    FoundationGate,
    OpportunityReceipt,
    ResultCode,
    final_panel_barrier_digest,
    foundation_barrier_digest,
    require_foundation_checkpoint_barrier,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.lifecycle import GateOutcome


def _fake(label: str) -> str:
    return "TEST_ONLY_FAKE_SHA256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


class _TestOnlySealer:
    def __init__(self) -> None:
        self.seals = 0
        self.unseals = 0

    def seal(self, master: bytes, *, context: bytes) -> bytes:
        self.seals += 1
        assert context.startswith(b"SCDMP-TBCC-R02-RUN-IDENTITY-SEAL-v1\0")
        return b"TEST_ONLY_SEAL:" + master

    def unseal(self, sealed: bytes, *, context: bytes) -> bytes:
        self.unseals += 1
        assert context.startswith(b"SCDMP-TBCC-R02-RUN-IDENTITY-SEAL-v1\0")
        assert sealed.startswith(b"TEST_ONLY_SEAL:")
        return sealed.removeprefix(b"TEST_ONLY_SEAL:")


def _preactivity_state(tmp_path: Path) -> production.PreactivityState:
    root = tmp_path.resolve()
    paths = {
        "result_root": root,
        "frontier_root": root / "frontiers",
        "source_manifest_path": root / "empirical_source_manifest.json",
        "preactivity_acceptance_path": root / "CM_PREACTIVITY_ACCEPTANCE.json",
        "run_identity_path": root / "RUN_IDENTITY.json",
        "completion_inventory_path": root / "COMPLETION_INVENTORY.json",
        "final_result_path": root / "COMPLETE_ATOMIC_RESULT.json",
        "cm_acceptance_path": root / "CM_TECHNICAL_ACCEPTANCE.json",
    }
    return production.PreactivityState(
        repository_root=root,
        paths=paths,
        source_manifest={},
        source_manifest_sha256="1" * 64,
        preactivity_acceptance={"accepted": True},
        preactivity_acceptance_sha256="2" * 64,
        native_identity={},
        native_binding={},
        native_binding_sha256="3" * 64,
        shared_receipt={},
        shared_receipt_sha256="4" * 64,
        coordinate_proposal={},
        _seal=production._PREACTIVITY_SEAL,
    )


def test_coordinate_binder_draws_one_master_and_publishes_no_words(tmp_path: Path) -> None:
    state = _preactivity_state(tmp_path)
    sealer = _TestOnlySealer()
    calls: list[int] = []

    def source(count: int) -> bytes:
        calls.append(count)
        return bytes(range(32))

    bound = production.bind_coordinates(
        state, master_source=source, master_sealer=sealer
    )
    assert calls == [32]
    assert sealer.seals == 1
    payload = json.loads(bound.path.read_text(encoding="ascii"))
    assert payload["schema"] == production.RUN_IDENTITY_SCHEMA
    assert payload["master_material_exposed"] is False
    assert payload["rng_words_present"] is False
    assert payload["coordinate_binding"]["rng_words_present"] is False
    assert "master" not in payload
    assert "sampled_values" not in json.dumps(payload, sort_keys=True)
    assert base64.b64decode(payload["sealed_master"]["ciphertext"]).startswith(
        b"TEST_ONLY_SEAL:"
    )
    with pytest.raises(production.ProductionContractError, match="already exists"):
        production.bind_coordinates(
            state, master_source=source, master_sealer=sealer
        )
    assert calls == [32]


def test_bound_shared_receipt_digest_survives_load_timing_drift_but_not_native_drift(
    tmp_path: Path,
) -> None:
    frozen = _preactivity_state(tmp_path)
    sealer = _TestOnlySealer()
    production.bind_coordinates(
        frozen,
        master_source=lambda count: bytes(range(count)),
        master_sealer=sealer,
    )
    current = replace(
        frozen,
        shared_receipt={"native": {"load_seconds": 0.125}},
        shared_receipt_sha256="9" * 64,
    )

    class _Permit:
        same_coordinate_repair_lineage = None
        source_manifest_sha256 = current.source_manifest_sha256
        preactivity_acceptance_sha256 = current.preactivity_acceptance_sha256
        native_binding_sha256 = current.native_binding_sha256

    context = production._load_bound_identity(
        current,
        permit=_Permit(),  # type: ignore[arg-type]
        lease_sha256="5" * 64,
        master_sealer=sealer,
    )
    assert sealer.unseals == 1
    assert context.bindings.shared_receipt_sha256 == "4" * 64
    assert context.bindings.coordinate_manifest_sha256 == production.canonical_digest(
        json.loads((tmp_path / "RUN_IDENTITY.json").read_text("ascii"))["coordinate_binding"]
    )

    changed_native = replace(current, native_binding_sha256="6" * 64)
    second_sealer = _TestOnlySealer()
    with pytest.raises(
        production.ProductionContractError,
        match="coordinate/source binding differs",
    ):
        production._load_bound_identity(
            changed_native,
            permit=_Permit(),  # type: ignore[arg-type]
            lease_sha256="5" * 64,
            master_sealer=second_sealer,
        )
    assert second_sealer.unseals == 0


def test_shared_native_semantics_ignore_only_finite_load_seconds() -> None:
    accepted = {
        "artifact_sha256": "a" * 64,
        "source_sha256": "b" * 64,
        "abi_version": 2,
        "python_fallback": False,
        "load_seconds": 0.01,
    }
    receipts = (
        {"native": {**accepted, "load_seconds": 0.02}},
        {"native": {**accepted, "load_seconds": 0.03}},
        {"native": {**accepted, "load_seconds": 0.04}},
    )
    production._validate_shared_native_semantics(receipts, accepted)
    changed = list(receipts)
    changed[1] = {
        "native": {**accepted, "source_sha256": "c" * 64, "load_seconds": 0.03}
    }
    with pytest.raises(production.ProductionContractError, match="semantic binding"):
        production._validate_shared_native_semantics(tuple(changed), accepted)
    malformed = ({"native": {**accepted, "load_seconds": float("nan")}},)
    with pytest.raises(production.ProductionContractError, match="load_seconds"):
        production._validate_shared_native_semantics(malformed, accepted)


def test_source_repaired_identity_requires_exact_successor_lineage_before_unseal(
    tmp_path: Path,
) -> None:
    frozen = _preactivity_state(tmp_path)
    production.bind_coordinates(
        frozen,
        master_source=lambda count: bytes(range(count)),
        master_sealer=_TestOnlySealer(),
    )
    current = replace(
        frozen,
        source_manifest_sha256="a" * 64,
        preactivity_acceptance_sha256="b" * 64,
        shared_receipt_sha256="c" * 64,
    )
    lineage = production.same_coordinate_repair_lineage(current)
    assert lineage["origin_source_manifest_sha256"] == "1" * 64
    assert lineage["origin_preactivity_acceptance_sha256"] == "2" * 64
    assert lineage["frozen_shared_receipt_sha256"] == "4" * 64
    assert lineage["scientific_activity_started"] is False
    assert lineage["master_regenerated"] is False
    assert lineage["coordinate_domains_changed"] is False

    class _Permit:
        source_manifest_sha256 = current.source_manifest_sha256
        preactivity_acceptance_sha256 = current.preactivity_acceptance_sha256
        native_binding_sha256 = current.native_binding_sha256
        same_coordinate_repair_lineage = None

    absent_sealer = _TestOnlySealer()
    with pytest.raises(production.ProductionContractError, match="explicit successor"):
        production._load_bound_identity(
            current,
            permit=_Permit(),  # type: ignore[arg-type]
            lease_sha256="5" * 64,
            master_sealer=absent_sealer,
        )
    assert absent_sealer.unseals == 0

    changed = dict(lineage)
    changed["coordinate_manifest_sha256"] = "d" * 64
    _Permit.same_coordinate_repair_lineage = changed
    changed_sealer = _TestOnlySealer()
    with pytest.raises(production.ProductionContractError, match="lineage differs"):
        production._load_bound_identity(
            current,
            permit=_Permit(),  # type: ignore[arg-type]
            lease_sha256="5" * 64,
            master_sealer=changed_sealer,
        )
    assert changed_sealer.unseals == 0


def test_bad_actual_argv_fails_before_lease_or_master_open(tmp_path: Path) -> None:
    state = _preactivity_state(tmp_path)
    sealer = _TestOnlySealer()
    with pytest.raises(production.ProductionContractError, match="argv"):
        production.run_with_root_lease(
            lease={},
            lease_path=tmp_path / "lease.json",
            actual_argv=["wrong"],
            now=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            preactivity=state,
            shared_guard=lambda *args, **kwargs: {},
            services=object(),
            master_sealer=sealer,
        )
    assert sealer.unseals == 0


def test_identity_free_preflight_checks_all_service_widths_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    manifest_path = root / "empirical_source_manifest.json"
    acceptance_path = root / "CM_PREACTIVITY_ACCEPTANCE.json"
    manifest_path.write_bytes(b"{}")
    acceptance_path.write_bytes(b"{}")
    paths = {
        "result_root": str(root),
        "frontier_root": str(root / "frontiers"),
        "source_manifest_path": str(manifest_path),
        "preactivity_acceptance_path": str(acceptance_path),
        "run_identity_path": str(root / "RUN_IDENTITY.json"),
        "completion_inventory_path": str(root / "COMPLETION_INVENTORY.json"),
        "final_result_path": str(root / "COMPLETE_ATOMIC_RESULT.json"),
        "cm_acceptance_path": str(root / "CM_TECHNICAL_ACCEPTANCE.json"),
    }
    manifest_sha = hashlib.sha256(b"{}").hexdigest()
    widths: list[int] = []
    native = {"artifact_sha256": "a" * 64}

    monkeypatch.setattr(production, "load_and_validate_source_manifest", lambda *args, **kwargs: {})
    monkeypatch.setattr(production, "manifest_digest", lambda value: manifest_sha)
    monkeypatch.setattr(production, "stable_native_binding", lambda value: dict(value))
    monkeypatch.setattr(
        production,
        "validate_preactivity_acceptance",
        lambda value, **kwargs: {"accepted": True},
    )
    monkeypatch.setattr(
        production,
        "coordinate_proposal",
        lambda value: {"source_manifest_sha256": value},
    )
    monkeypatch.setattr(production, "validate_coordinate_proposal", lambda *args, **kwargs: None)

    def guard(*, batch_width: int, **kwargs):
        widths.append(batch_width)
        return {"batch_width": batch_width, "native": native}

    monkeypatch.setattr(production, "require_direction_cpp_batched_production", guard)
    before = sorted(path.name for path in root.iterdir())
    state = production.preflight_only(
        repository_root=root,
        source_manifest_path=manifest_path,
        preactivity_acceptance_path=acceptance_path,
        output_paths=paths,
        native_identity_loader=lambda: native,
        shared_guard=lambda *args, **kwargs: {},
    )
    assert state.preactivity_acceptance == {"accepted": True}
    assert widths == [12, 120, 144]
    assert sorted(path.name for path in root.iterdir()) == before
    assert not (root / "RUN_IDENTITY.json").exists()
    assert not (root / "frontiers").exists()


class _Services:
    def __init__(self, foundation: GateOutcome, opportunity: GateOutcome = GateOutcome.PASS) -> None:
        self.foundation_outcome = foundation
        self.opportunity_outcome = opportunity
        self.calls: list[str] = []

    def foundation_final(self, context: production.RunContext, replicate: int) -> FoundationFinalReceipt:
        self.calls.append(f"foundation:{replicate}")
        return FoundationFinalReceipt(
            replicate=replicate,
            coordinate_manifest_sha256=context.bindings.coordinate_manifest_sha256,
            checkpoint_sha256=_fake(f"foundation-checkpoint:{replicate}"),
            optimizer_state_sha256=_fake(f"foundation-optimizer:{replicate}"),
        )

    def foundation_competence(self, context: production.RunContext, receipts):
        self.calls.append("competence")
        barrier = require_foundation_checkpoint_barrier(receipts, context.bindings)
        return (
            FoundationGate(
                outcome=self.foundation_outcome,
                complete_panel_sha256=_fake("foundation-panel"),
                barrier_sha256=foundation_barrier_digest(barrier),
            ),
            _fake("foundation-inference"),
        )

    def opportunity(self, context: production.RunContext, foundation_gate: FoundationGate):
        self.calls.append("opportunity")
        return (
            OpportunityReceipt(
                outcome=self.opportunity_outcome,
                complete_stage_sha256=_fake("opportunity-panel"),
                foundation_gate_sha256="0" * 64,
            ),
            _fake("opportunity-inference"),
        )

    def adapter_final(self, context, replicate: int, arm: str, adapter_permit):
        self.calls.append(f"adapter:{replicate}:{arm}")
        return AdapterFinalReceipt(
            replicate=replicate,
            arm=arm,
            coordinate_manifest_sha256=context.bindings.coordinate_manifest_sha256,
            checkpoint_sha256=_fake(f"adapter-checkpoint:{replicate}:{arm}"),
            optimizer_state_sha256=_fake(f"adapter-optimizer:{replicate}:{arm}"),
        )

    def final_evaluation(self, context, final_permit, final_barrier):
        self.calls.append("final")
        return (
            FinalPanelReceipt(
                complete_panel_sha256=_fake("final-panel"),
                barrier_sha256=final_panel_barrier_digest(final_barrier),
            ),
            ResultCode.NONIDENTIFIED,
            _fake("final-inference"),
        )


@pytest.mark.parametrize(
    ("foundation", "opportunity", "expected", "forbidden"),
    [
        (GateOutcome.NONPASS, GateOutcome.PASS, "FOUNDATION_ONLY", "opportunity"),
        (GateOutcome.PASS, GateOutcome.NONPASS, "FOUNDATION_AND_OPPORTUNITY", "adapter:0:TREAT"),
        (GateOutcome.PASS, GateOutcome.PASS, "FULL_FIVE_CONTROLLER_PANEL", "never"),
    ],
)
def test_exact_prerequisite_dependent_realized_paths(
    tmp_path: Path,
    foundation: GateOutcome,
    opportunity: GateOutcome,
    expected: str,
    forbidden: str,
) -> None:
    context = production.test_only_run_context(tmp_path, token=expected)
    services = _Services(foundation, opportunity)
    digest = production.execute_realized_path(context, services=services)
    assert len(digest) == 64
    result = json.loads((tmp_path / production.FINAL_RESULT_NAME).read_text("ascii"))
    assert result["realized_path"] == expected
    assert result["partial_values_exposed"] is False
    assert result["interpretation_included"] is False
    assert forbidden not in services.calls
    assert services.calls[:24] == [f"foundation:{value}" for value in range(24)]
    if expected == "FULL_FIVE_CONTROLLER_PANEL":
        assert sum(call.startswith("adapter:") for call in services.calls) == 72
        assert services.calls[-1] == "final"
    resumed = _Services(foundation, opportunity)
    assert production.execute_realized_path(context, services=resumed) == digest
    assert resumed.calls == []


def test_services_feature_detection_has_no_fallback() -> None:
    with pytest.raises(production.ProductionContractError, match="incomplete"):
        production._require_services_api(object())
