from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import math
import json
import os
from pathlib import Path
import threading
import time

import pytest

from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.evaluation import (
    EpisodeEndpoint,
    aggregate_replicate_endpoints,
    deterministic_lexicographic_argmax,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.frontier import (
    CheckpointCompletion,
    CheckpointReceipt,
    FrontierContractError,
    FrontierSpec,
    frontier_digest,
    _cm_authority,
    cm_create_technical_acceptance,
    require_global_checkpoint_barrier,
    validate_resume_chain,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.inference import (
    VALIDITY_FLAGS,
    complete_inference,
    higher_better_state,
    lower_better_state,
    qualification_state,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.lease import (
    ActivityPermit,
    COORDINATE_PLAN_DIGEST,
    EVALUATE_PHASE,
    EMPIRICAL_STAGE,
    EXECUTION_MODULE,
    LEASE_SCHEMA,
    PROHIBITIONS,
    PYTHON_EXECUTABLE,
    TRAIN_PHASE,
    accepted_construction_binding,
    canonical_absolute_path_key,
    canonical_digest,
    coordinate_proposal,
    path_is_within_root,
    validate_lease,
    validate_lease_envelope,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value import lease as lease_module
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.rng import (
    AddressRNG,
    DOMAIN_LABELS,
    EmpiricalRNG,
    REPLICATE_PREFIX,
    domain_separation_proof,
    replicate_message,
    sample_fresh_master,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.runner import (
    BlindedFrontierHandle,
    RunnerContractError,
    RunnerServices,
    _run_evaluation_with_permit,
    _run_training_with_permit,
    atomic_json_publisher,
    run_training_phase,
    run_empirical_panel,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.support import (
    QUOTIENT_REPRESENTATIVES,
    SupportActionRow,
    expand_quotient_scores,
    exact_max_set,
    support_quotient_certificate,
    support_metrics,
    support_score,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.training import (
    registered_minibatch_plan,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.model import (
    row_major_xavier_from_uniforms,
)


PACKAGE_ROOT = (
    __import__(
        "experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.lease",
        fromlist=["dummy"],
    ).__file__
)


def _lease_and_guard(
    *,
    phase: str = TRAIN_PHASE,
    lease_id: str = "SYNTHETIC-LEASE-FOR-CONTRACT-TEST",
    root: Path | None = None,
) -> tuple[dict[str, object], dict[str, object], datetime]:
    now = datetime(2026, 8, 20, 18, 0, tzinfo=timezone.utc)
    binding = accepted_construction_binding()
    root = (root or Path("C:/Projects/HMASD/.tmp_scdmp_uav_contract_paths")).resolve()
    paths = {
        "result_root": str(root),
        "result_path": str((root / "RESULT.json").resolve()),
        "train_terminal_path": str((root / "TRAIN_TERMINAL.json").resolve()),
        "evaluation_terminal_path": str((root / "EVALUATE_TERMINAL.json").resolve()),
        "run_identity_path": str((root / "RUN_IDENTITY.json").resolve()),
        "completion_inventory_path": str((root / "COMPLETIONS.json").resolve()),
        "cm_acceptance_path": str((root / "CM_ACCEPTANCE.json").resolve()),
    }
    lease = {
        "schema": LEASE_SCHEMA,
        "lease_id": lease_id,
        "activity_authorized": True,
        "stage": EMPIRICAL_STAGE,
        "card_revision": binding["card_revision"],
        "card_sha256": binding["card_sha256"],
        "component": binding["component"],
        "abi_version": 2,
        "coordinate_plan_digest": COORDINATE_PLAN_DIGEST,
        "construction_binding": binding,
        "empirical_source_manifest_sha256": coordinate_proposal()["empirical_source_manifest"]["sha256"],
        "phase": phase,
        "paths": paths,
        "execution": {
            "module": EXECUTION_MODULE,
            "phase": phase,
            "command": [PYTHON_EXECUTABLE, "-m", EXECUTION_MODULE, "--phase", phase],
        },
        "occupied_digest_registry": None,
        "complete_panel_only": True,
        "prohibitions": list(PROHIBITIONS),
        "issued_at": (now - timedelta(hours=1)).isoformat(),
        "expires_at": (now + timedelta(hours=20)).isoformat(),
        "resources": {
            "cpu_only": True,
            "gpu_count": 0,
            "independent_workers": 4,
            "ram_gib": 12,
            "scratch_gib": 6,
            "durable_artifacts_gib": 2,
            "torch_threads": 1,
        },
    }
    guard = {
        "construction_object": binding["construction_object"],
        "component": binding["component"],
        "host": binding["host"],
        "card_revision": binding["card_revision"],
        "full_reset_step_cpp": True,
        "science_card": {"sha256": binding["card_sha256"]},
        "direction_native": {
            "abi_version": 2,
            "native_source_sha256": binding["native_source_sha256"],
            "source_sha256": binding["source_sha256"],
            "build_key": binding["build_key"],
            "artifact_sha256": binding["artifact_sha256"],
            "artifact_size": binding["artifact_size"],
            "abi_sizes": binding["abi_sizes"],
            "binding_kind": "ctypes_cdll",
            "python_fallback": False,
        },
    }
    return lease, guard, now


def _permit(
    *,
    phase: str = TRAIN_PHASE,
    lease_id: str = "SYNTHETIC-SEALED-PERMIT",
    root: Path | None = None,
    source_manifest_sha256: str | None = None,
) -> ActivityPermit:
    root = (root or Path("C:/Projects/HMASD/.tmp_scdmp_uav_contract_paths")).resolve()
    paths = {
        "result_root": str(root),
        "result_path": str((root / "RESULT.json").resolve()),
        "train_terminal_path": str((root / "TRAIN_TERMINAL.json").resolve()),
        "evaluation_terminal_path": str((root / "EVALUATE_TERMINAL.json").resolve()),
        "run_identity_path": str((root / "RUN_IDENTITY.json").resolve()),
        "completion_inventory_path": str((root / "COMPLETIONS.json").resolve()),
        "cm_acceptance_path": str((root / "CM_ACCEPTANCE.json").resolve()),
    }
    return ActivityPermit(
        lease_id=lease_id,
        coordinate_plan_digest=COORDINATE_PLAN_DIGEST,
        workers=4,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        phase=phase,
        paths=paths,
        source_manifest_sha256=source_manifest_sha256 or "1" * 64,
        native_binding_digest="2" * 64,
        card_sha256="3" * 64,
        lease_issued_at="2026-08-20T17:00:00+00:00",
        _validation_seal=lease_module._PERMIT_SEAL,
    )


def test_identity_free_coordinate_proposal_is_exact_and_complete() -> None:
    proposal = coordinate_proposal()
    assert proposal["materialized"] is False
    assert proposal["rng"]["master"] is None
    assert proposal["rng"]["master_digest"] is None
    assert proposal["rng"]["replicate_key_digests"] == []
    assert proposal["rng"]["domain_key_digests"] == []
    assert proposal["rng"]["domains"] == list(DOMAIN_LABELS)
    assert len(proposal["training"]["checkpoint_slots"]) == 54
    assert proposal["evaluation"]["episode_count"] == 51_840
    assert proposal["support"]["shape"] == [18, 2, 72, 2, 27]
    quotient = proposal["support"]["lossless_carrier_permutation_quotient"]
    assert quotient["representatives"] == 10
    assert quotient["maximum_transitions_per_support_boundary"] == 140
    assert quotient["complexity"] == "O(k*10)"
    assert quotient["nested_replanning"] is False
    assert proposal["lease_request"] == {
        "cpu_only": True,
        "gpu_count": 0,
        "max_independent_workers": 4,
        "ram_gib": 12,
        "scratch_gib": 6,
        "durable_artifacts_gib": 2,
        "validity_hours": 36,
        "complete_panel_only": True,
        "stage": EMPIRICAL_STAGE,
    }
    assert canonical_digest(proposal) == COORDINATE_PLAN_DIGEST


def test_hmac_namespace_domains_collision_proof_and_permutation_contract() -> None:
    synthetic_master = bytes(range(32))
    assert replicate_message(3) == REPLICATE_PREFIX + b"\x00\x00\x00\x03"
    proof = domain_separation_proof(synthetic_master)
    assert proof["replicate_messages_injective"] is True
    assert proof["domain_labels_disjoint"] is True
    assert proof["derived_domain_key_digests_unique"] is True
    rng = EmpiricalRNG(synthetic_master, _permit())
    permutation = rng.permutation_indices(3, "FREE", 7, 2, 19)
    assert tuple(sorted(permutation)) == tuple(range(19))
    assert permutation == rng.permutation_indices(3, "FREE", 7, 2, 19)
    assert permutation != rng.permutation_indices(3, "FREE", 7, 3, 19)
    plans = registered_minibatch_plan(
        rng, replicate=3, arm="FREE", update=7, count=19
    )
    assert len(plans) == 4
    assert all(tuple(sorted(plan.permutation)) == tuple(range(19)) for plan in plans)
    assert sorted(rng.training_setup_order_roster(3, 7, 4)) == ["GR"] * 3 + ["RG"] * 3
    orders = rng.evaluation_order_roster(3, "6-to-14")
    switches = rng.evaluation_switch_roster(3, "6-to-14", orders)
    assert {
        (order, tick): sum(o == order and t == tick for o, t in zip(orders, switches))
        for order in ("RG", "GR") for tick in (168, 252)
    } == {("RG", 168): 30, ("RG", 252): 30, ("GR", 168): 30, ("GR", 252): 30}


def test_uint24_action_uniform_max_and_initialization_address_law(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(AddressRNG, "raw_u64", lambda self, *parts, counter=0: (1 << 64) - 1)
    stream = AddressRNG(b"x" * 32)
    assert stream.uint24("address") == (1 << 24) - 1
    assert stream.uniform24("address") == 1.0 - 2.0 ** -24
    assert stream.uniform24("address") < 1.0
    monkeypatch.undo()

    rng = EmpiricalRNG(bytes(range(32)), _permit())
    shared_treat = rng.initialization_uniforms(0, "SHARED", "base.layers.0.weight", True, 8)
    shared_free = rng.initialization_uniforms(0, "SHARED", "base.layers.0.weight", True, 8)
    assert shared_treat == shared_free
    assert all(float(__import__("numpy").float32(value)) == value for value in shared_treat)
    assert tuple(row_major_xavier_from_uniforms(shared_treat, fan_in=2, fan_out=4).shape) == (4, 2)
    residual_free = rng.initialization_uniforms(0, "FREE", "residual.layers.0.weight", False, 8)
    residual_set = rng.initialization_uniforms(0, "SET", "residual.layers.0.weight", False, 8)
    assert residual_free != residual_set
    action_uniform = rng.training_action_uniform(0, 1, 4, 0, 0)
    assert action_uniform <= 1.0 - 2.0 ** -24
    assert action_uniform * (1 << 24) == math.floor(action_uniform * (1 << 24))


def test_master_sampler_rejects_unvalidated_permit_before_source_call() -> None:
    calls = 0

    def forbidden_source(_: int) -> bytes:
        nonlocal calls
        calls += 1
        raise AssertionError("identity source must not be reached")

    forged = ActivityPermit(
        lease_id="forged",
        coordinate_plan_digest=COORDINATE_PLAN_DIGEST,
        workers=1,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    with pytest.raises(Exception, match="not authorized"):
        sample_fresh_master(forged, occupied_digests=(), source=forbidden_source)
    assert calls == 0


def test_lease_binds_exact_source_build_artifact_and_caps() -> None:
    lease, guard, now = _lease_and_guard()
    validate_lease_envelope(lease, now=now)

    guard_calls = 0

    def accepted_guard(*, batch_width: int):
        nonlocal guard_calls
        guard_calls += 1
        assert batch_width == 4
        return guard

    permit = validate_lease(
        lease,
        now=now,
        package_root=Path(PACKAGE_ROOT).resolve().parent,
        native_guard=accepted_guard,
    )
    assert permit.workers == 4 and guard_calls == 1
    tampered = dict(lease)
    tampered["construction_binding"] = dict(accepted_construction_binding())
    tampered["construction_binding"]["artifact_sha256"] = "0" * 64
    with pytest.raises(Exception, match="binding differs"):
        validate_lease_envelope(tampered, now=now)
    over = dict(lease)
    over["resources"] = dict(lease["resources"])
    over["resources"]["independent_workers"] = 5
    with pytest.raises(Exception, match="one to four"):
        validate_lease_envelope(over, now=now)
    low_ram = dict(lease)
    low_ram["resources"] = dict(lease["resources"])
    low_ram["resources"]["ram_gib"] = 7
    with pytest.raises(Exception, match=r"\[8,12\]"):
        validate_lease_envelope(low_ram, now=now)


def test_frontier_schema_is_blinded_create_only_and_resumable_same_coordinate() -> None:
    initial = FrontierSpec(0, "TREAT", COORDINATE_PLAN_DIGEST, 0, None, "CREATED", None, 0)
    second = FrontierSpec(
        0,
        "TREAT",
        COORDINATE_PLAN_DIGEST,
        1,
        frontier_digest(initial),
        "TRAINING",
        None,
        16,
    )
    validate_resume_chain([initial.payload(), second.payload()])
    changed = dict(second.payload())
    changed["arm"] = "FREE"
    with pytest.raises(FrontierContractError, match="changed slot"):
        validate_resume_chain([initial.payload(), changed])


def test_windows_extended_prefix_containment_matches_ordinary_path_and_rejects_escape(tmp_path) -> None:
    root = (tmp_path / "result").resolve()
    checkpoint = (root / "checkpoints" / "slot.bin").resolve()
    completion = (root / "completions" / "slot.json").resolve()
    checkpoint.parent.mkdir(parents=True)
    completion.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"checkpoint")
    completion.write_bytes(b"completion")
    extended_completion = Path("\\\\?\\" + str(completion))
    assert canonical_absolute_path_key(extended_completion) == canonical_absolute_path_key(completion)
    assert path_is_within_root(extended_completion, root)
    sha = __import__("hashlib").sha256
    record = CheckpointCompletion(
        replicate=0,
        arm="TREAT",
        coordinate_digest=COORDINATE_PLAN_DIGEST,
        run_identity_digest="1" * 64,
        checkpoint_path=str(checkpoint),
        checkpoint_digest=sha(b"checkpoint").hexdigest(),
        completion_payload_path=str(extended_completion),
        completion_payload_digest=sha(b"completion").hexdigest(),
    )
    record.validate(result_root=root)
    outside = (tmp_path / "outside.json").resolve()
    outside.write_bytes(b"completion")
    with pytest.raises(FrontierContractError, match="escapes"):
        replace(record, completion_payload_path=str(outside)).validate(result_root=root)
    assert path_is_within_root(Path("Z:/different-drive/file.json"), root) is False


def test_global_barrier_requires_exactly_all_54_final_slots() -> None:
    receipts = [
        CheckpointReceipt(
            replicate,
            arm,
            COORDINATE_PLAN_DIGEST,
            f"{replicate * 3 + index + 1:064x}",
            2_304,
            True,
        )
        for replicate in range(18)
        for index, arm in enumerate(("TREAT", "FREE", "SET"))
    ]
    barrier = require_global_checkpoint_barrier(receipts)
    assert barrier.accepted_slots == 54 and barrier.evaluation_open is True
    with pytest.raises(FrontierContractError, match="exactly 54"):
        require_global_checkpoint_barrier(receipts[:-1])
    premature = list(receipts)
    premature[0] = replace(premature[0], evaluation_observed=True)
    with pytest.raises(FrontierContractError, match="premature"):
        require_global_checkpoint_barrier(premature)


def test_support_score_max_set_and_exact_denominators() -> None:
    assert support_score(
        delta_x=1.08,
        k=6,
        physical_failure=False,
        z_end=0.0,
        phi_end=0.0,
        f_end=0.0,
    ) == pytest.approx(1.0)
    scores = {action: 0.0 for action in range(27)}
    scores[2] = scores[5] = 1.0
    assert exact_max_set(scores) == ((2, 5), 1.0)
    certificate = support_quotient_certificate()
    assert certificate["representative_count"] == 10
    assert certificate["all_27_actions_covered_once"] is True
    assert certificate["permutation_invariant_physics_signature"] is True
    quotient_scores = {representative: float(index) for index, representative in enumerate(QUOTIENT_REPRESENTATIVES)}
    expanded = expand_quotient_scores(quotient_scores)
    assert len(expanded) == 27
    assert expanded[1] == expanded[3] == expanded[9]
    rows = []
    for k in (6, 14):
        for state in range(72):
            digest = f"{k * 100 + state + 1:064x}"
            for history in ("RG", "GR"):
                for representative_index, action in enumerate(QUOTIENT_REPRESENTATIVES):
                    score = float(
                        representative_index if history == "RG" else 9 - representative_index
                    ) / 9.0
                    rows.append(SupportActionRow(0, k, state, history, action, digest, digest, score))
    metrics = support_metrics(rows, replicate=0)
    assert metrics["Q_order"] == 1.0
    assert metrics["D_order"] == 0.0
    assert metrics["D_action"] == 1.0
    assert metrics["Q_order_denominator"] == 144.0
    assert metrics["D_action_denominator"] == 288.0


def _evaluation_rows() -> list[EpisodeEndpoint]:
    rows: list[EpisodeEndpoint] = []
    regimes = ("fixed-4", "fixed-10", "fixed-6", "fixed-14", "6-to-14", "14-to-6")
    for controller in ("TREAT", "FREE", "REVERSED", "SET"):
        for regime_index, regime in enumerate(regimes):
            for scenario in range(120):
                if regime in ("6-to-14", "14-to-6"):
                    event_order = "RG" if scenario < 60 else "GR"
                    switch_tick = 168 if scenario % 60 < 30 else 252
                else:
                    event_order = "RG" if scenario < 60 else "GR"
                    switch_tick = 0
                rows.append(
                    EpisodeEndpoint(
                        replicate=0,
                        controller=controller,
                        regime=regime,
                        scenario_index=scenario,
                        event_order=event_order,
                        switch_tick=switch_tick,
                        scenario_digest=f"{regime_index * 120 + scenario + 1:064x}",
                        safe_delivery=True,
                        physical_failure=False,
                        timeout=False,
                        overload=False,
                        swing=False,
                        formation=False,
                        completion_time_seconds=12.0,
                        active_effort_sum=25.0,
                        active_ticks=100,
                    )
                )
    return rows


def test_argmax_tie_law_and_endpoint_aggregation() -> None:
    logits = [0.0] * 27
    logits[3] = logits[8] = 2.0
    assert deterministic_lexicographic_argmax(logits) == 3
    aggregated = aggregate_replicate_endpoints(_evaluation_rows(), replicate=0)
    treat = aggregated["TREAT"]
    assert treat["P"] == 1.0 and treat["W"] == 1.0
    assert treat["T"] == 12.0 and treat["E"] == 0.25
    assert treat["O"] == treat["G"] == treat["F"] == 0.0
    assert treat["competence"]["pooled"] == 1.0


def _packets(*, treatment_primary: float, support_value: float = 0.5) -> list[dict[str, object]]:
    packets = []
    for replicate in range(18):
        controllers = {}
        for controller in ("TREAT", "FREE", "REVERSED", "SET"):
            primary = treatment_primary if controller == "TREAT" else 0.70
            controllers[controller] = {
                "competence": {
                    "fixed-4/RG": 0.9,
                    "fixed-4/GR": 0.9,
                    "fixed-10/RG": 0.9,
                    "fixed-10/GR": 0.9,
                    "pooled": 0.9,
                },
                "P": primary,
                "W": primary,
                "T": 20.0 if controller == "TREAT" else 21.0,
                "E": 0.20 if controller == "TREAT" else 0.21,
                "O": 0.01 if controller == "TREAT" else 0.015,
                "G": 0.01 if controller == "TREAT" else 0.015,
                "F": 0.01 if controller == "TREAT" else 0.015,
            }
        packets.append(
            {
                "replicate": replicate,
                "controllers": controllers,
                "support": {
                    "Q_order": support_value,
                    "D_order": support_value,
                    "D_action": support_value,
                },
            }
        )
    return packets


def _validity() -> dict[str, bool]:
    return {flag: True for flag in VALIDITY_FLAGS}


def test_inference_exact_families_and_retain_decline_nonidentified_map() -> None:
    retained = complete_inference(_packets(treatment_primary=0.90), validity=_validity())
    assert retained["branch"] == "RETAIN-TAUT-GUST-RISK-TILT"
    assert retained["competence_family"]["members"] == 15
    assert retained["support_action_family"]["members"] == 3
    assert retained["direct_family"]["members"] == 17
    assert retained["routes"]["P"]["state"] == "PASS"

    declined = complete_inference(_packets(treatment_primary=0.50), validity=_validity())
    assert declined["routes"]["P"]["state"] == "EXCLUDED"
    assert declined["routes"]["W"]["state"] == "EXCLUDED"
    assert declined["branch"] == "DECLINE-TAUT-GUST-RISK-TILT"

    nonidentified = complete_inference(
        _packets(treatment_primary=0.50, support_value=0.0), validity=_validity()
    )
    assert nonidentified["branch"] == "DIRECT-UAV-ORDER-VALUE-NONIDENTIFIED"


def test_interval_state_boundary_laws_are_strict() -> None:
    assert qualification_state(0.58, 0.58) == "UNRESOLVED"
    assert higher_better_state({"lower": 0.1, "upper": 0.2}, 0.1) == "UNRESOLVED"
    assert higher_better_state({"lower": 0.0, "upper": 0.1}, 0.1) == "FAIL"
    assert lower_better_state({"lower": 0.0, "upper": 0.04}, 0.04) == "UNRESOLVED"
    assert lower_better_state({"lower": 0.04, "upper": 0.05}, 0.04) == "FAIL"


def test_nonfinite_or_incomplete_evidence_is_invalid_first() -> None:
    packets = _packets(treatment_primary=0.9)
    packets[0]["controllers"]["TREAT"]["P"] = math.nan
    result = complete_inference(packets, validity=_validity())
    assert result["branch"] == "INVALID-EVIDENCE"
    validity = _validity()
    validity["pairing_conformance"] = False
    result = complete_inference(_packets(treatment_primary=0.9), validity=validity)
    assert result["branch"] == "INVALID-EVIDENCE"


def test_runner_without_lease_stops_before_guard_identity_and_all_services() -> None:
    calls: list[str] = []

    def bomb(*args: object, **kwargs: object) -> object:
        calls.append("called")
        raise AssertionError("prelease runner crossed the activity boundary")

    services = RunnerServices(bomb, bomb, bomb, bomb, bomb)
    with pytest.raises(RunnerContractError, match="legacy monolithic"):
        run_empirical_panel(
            lease=None,
            now=datetime.now(timezone.utc),
            services=services,
            validity=_validity(),
            occupied_identity_digests=(),
            native_guard=bomb,
            master_source=bomb,
        )
    assert calls == []


def test_source_manifest_mismatch_precedes_native_guard_and_master_source(tmp_path) -> None:
    lease, _, now = _lease_and_guard()
    live = coordinate_proposal()["empirical_source_manifest"]
    manifest_path = (
        __import__(
            "pathlib", fromlist=["Path"]
        ).Path(PACKAGE_ROOT).resolve().parent / str(live["path"])
    )
    value = json.loads(manifest_path.read_text(encoding="ascii"))
    value["status"] = "FINAL"
    value["files"][0]["sha256"] = "0" * 64
    bad_manifest = tmp_path / "empirical_source_manifest.json"
    bad_manifest.write_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        + b"\n"
    )
    calls: list[str] = []

    def bomb(*args: object, **kwargs: object) -> object:
        calls.append("called")
        raise AssertionError("manifest mismatch must precede native/identity activity")

    with pytest.raises(Exception, match="source digest changed"):
        run_training_phase(
            lease=lease,
            now=now,
            services=bomb,
            run_identity_path=Path(lease["paths"]["run_identity_path"]),
            completion_inventory_path=Path(lease["paths"]["completion_inventory_path"]),
            train_terminal_path=Path(lease["paths"]["train_terminal_path"]),
            cached_native_guard=bomb,
            occupied_identity_digests=(),
            master_source=bomb,
            source_manifest_path=bad_manifest,
        )
    assert calls == []


def test_atomic_json_publisher_never_replaces_racing_target(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "result.json"
    publisher = atomic_json_publisher(target)
    real_link = os.link

    def racing_link(source, destination) -> None:
        target.write_bytes(b"racing-owner")
        real_link(source, destination)

    monkeypatch.setattr(os, "link", racing_link)
    with pytest.raises(RunnerContractError, match="create-only"):
        publisher(_permit(), {"complete_atomic_panel": True})
    assert target.read_bytes() == b"racing-owner"


class _SyntheticMasterSealer:
    def seal(self, master: bytes, *, context: bytes) -> bytes:
        mask = __import__("hashlib").sha256(context).digest()
        return bytes(value ^ mask[index] for index, value in enumerate(master))

    def unseal(self, sealed: bytes, *, context: bytes) -> bytes:
        return self.seal(sealed, context=context)


class _SyntheticTrainingServices:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.lock = threading.Lock()
        self.active = 0
        self.maximum_active = 0
        self.train_calls = 0
        self.evaluation_calls = 0

    def create_or_resume_frontier(self, permit, rng, replicate, arm, run_identity_digest):
        arm_index = {"TREAT": 0, "FREE": 1, "SET": 2}[arm]
        return BlindedFrontierHandle(
            replicate=replicate,
            arm=arm,
            coordinate_digest=permit.coordinate_plan_digest,
            frontier_digest=f"{replicate * 3 + arm_index + 1:064x}",
        )

    def train_slot(self, permit, rng, frontier, run_identity_digest):
        with self.lock:
            self.active += 1
            self.maximum_active = max(self.maximum_active, self.active)
            self.train_calls += 1
        try:
            time.sleep(0.002)
            stem = f"r{frontier.replicate:02d}_{frontier.arm}"
            checkpoint = (self.root / "checkpoints" / f"{stem}.bin").resolve()
            completion = (self.root / "completion_payloads" / f"{stem}.json").resolve()
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            completion.parent.mkdir(parents=True, exist_ok=True)
            checkpoint_bytes = f"synthetic-checkpoint:{stem}".encode("ascii")
            completion_bytes = f"synthetic-completion:{stem}".encode("ascii")
            checkpoint.write_bytes(checkpoint_bytes)
            completion.write_bytes(completion_bytes)
            sha = __import__("hashlib").sha256
            return CheckpointCompletion(
                replicate=frontier.replicate,
                arm=frontier.arm,
                coordinate_digest=permit.coordinate_plan_digest,
                run_identity_digest=run_identity_digest,
                checkpoint_path=str(checkpoint),
                checkpoint_digest=sha(checkpoint_bytes).hexdigest(),
                completion_payload_path=str(completion),
                completion_payload_digest=sha(completion_bytes).hexdigest(),
            )
        finally:
            with self.lock:
                self.active -= 1

    def evaluate_panel(self, *args, **kwargs):
        self.evaluation_calls += 1
        raise AssertionError("TRAIN phase must not evaluate")


def _synthetic_phase_lease(permit: ActivityPermit) -> dict[str, object]:
    return {
        "lease_id": permit.lease_id,
        "issued_at": permit.lease_issued_at,
        "expires_at": permit.expires_at.isoformat(),
        "phase": permit.phase,
        "stage": EMPIRICAL_STAGE,
        "occupied_digest_registry": None,
    }


def test_two_phase_training_persists_one_master_and_resumes_new_lease_id(tmp_path) -> None:
    root = (tmp_path / "run").resolve()
    permit = _permit(root=root, phase=TRAIN_PHASE, lease_id="TRAIN-LEASE-1")
    service = _SyntheticTrainingServices(root)
    source_calls = 0

    def master_source(count: int) -> bytes:
        nonlocal source_calls
        source_calls += 1
        assert count == 32
        return bytes(range(32))

    first = _run_training_with_permit(
        permit=permit,
        lease=_synthetic_phase_lease(permit),
        services=service,
        run_identity_path=Path(permit.paths["run_identity_path"]),
        completion_inventory_path=Path(permit.paths["completion_inventory_path"]),
        train_terminal_path=Path(permit.paths["train_terminal_path"]),
        occupied_identity_digests=(),
        master_source=master_source,
        master_sealer=_SyntheticMasterSealer(),
    )
    assert source_calls == 1
    assert first.completion_count == 54 and first.technically_accepted is False
    assert service.train_calls == 54 and service.evaluation_calls == 0
    assert 1 < service.maximum_active <= 4
    record = json.loads(Path(permit.paths["run_identity_path"]).read_text(encoding="ascii"))
    assert "master" not in record and "sealed_master" in record
    assert len(record["replicate_key_digests"]) == 18
    assert len(record["domain_key_digests"]) == 18
    assert all(len(row) == len(DOMAIN_LABELS) for row in record["domain_key_digests"])

    continuation = _permit(root=root, phase=TRAIN_PHASE, lease_id="TRAIN-LEASE-2")
    second = _run_training_with_permit(
        permit=continuation,
        lease=_synthetic_phase_lease(continuation),
        services=service,
        run_identity_path=Path(continuation.paths["run_identity_path"]),
        completion_inventory_path=Path(continuation.paths["completion_inventory_path"]),
        train_terminal_path=Path(continuation.paths["train_terminal_path"]),
        occupied_identity_digests=(),
        master_source=lambda _: (_ for _ in ()).throw(AssertionError("resume drew a master")),
        master_sealer=_SyntheticMasterSealer(),
    )
    assert second.resumed_run_identity is True
    assert second.run_identity_digest == first.run_identity_digest
    assert source_calls == 1 and service.train_calls == 54


def test_cm_acceptance_is_separate_and_evaluation_rejects_absence(tmp_path) -> None:
    root = (tmp_path / "run").resolve()
    train_permit = _permit(root=root, phase=TRAIN_PHASE, lease_id="TRAIN")
    service = _SyntheticTrainingServices(root)
    trained = _run_training_with_permit(
        permit=train_permit,
        lease=_synthetic_phase_lease(train_permit),
        services=service,
        run_identity_path=Path(train_permit.paths["run_identity_path"]),
        completion_inventory_path=Path(train_permit.paths["completion_inventory_path"]),
        train_terminal_path=Path(train_permit.paths["train_terminal_path"]),
        occupied_identity_digests=(),
        master_source=lambda _: b"a" * 32,
        master_sealer=_SyntheticMasterSealer(),
    )
    eval_permit = _permit(root=root, phase=EVALUATE_PHASE, lease_id="EVAL")
    calls = 0

    class NeverEvaluate:
        def evaluate_panel(self, *args, **kwargs):
            nonlocal calls
            calls += 1
            raise AssertionError

        support_panel = evaluate_panel
        publish_atomic = evaluate_panel

    with pytest.raises(Exception, match="CM acceptance inventory cannot be read"):
        _run_evaluation_with_permit(
            permit=eval_permit,
            lease=_synthetic_phase_lease(eval_permit),
            services=NeverEvaluate(),
            run_identity_path=Path(eval_permit.paths["run_identity_path"]),
            completion_inventory_path=Path(eval_permit.paths["completion_inventory_path"]),
            cm_acceptance_path=Path(eval_permit.paths["cm_acceptance_path"]),
            result_path=Path(eval_permit.paths["result_path"]),
            evaluation_terminal_path=Path(eval_permit.paths["evaluation_terminal_path"]),
            validity=_validity(),
            master_sealer=_SyntheticMasterSealer(),
        )
    assert calls == 0
    cm_create_technical_acceptance(
        authority=_cm_authority("CM_semigroup_consistent_duration_model_policy"),
        completion_inventory_path=Path(train_permit.paths["completion_inventory_path"]),
        acceptance_path=Path(train_permit.paths["cm_acceptance_path"]),
        result_root=root,
        run_identity_digest=trained.run_identity_digest,
        source_manifest_sha256=str(train_permit.source_manifest_sha256),
        payload_validator=lambda completion: completion.validate(result_root=root),
    )
    accepted = json.loads(Path(train_permit.paths["cm_acceptance_path"]).read_text(encoding="ascii"))
    assert accepted["technically_accepted"] is True and len(accepted["receipts"]) == 54


def test_run_identity_rejects_changed_master_source_and_bound_path(tmp_path) -> None:
    root = (tmp_path / "run").resolve()
    permit = _permit(root=root, phase=TRAIN_PHASE, lease_id="TRAIN")
    service = _SyntheticTrainingServices(root)
    _run_training_with_permit(
        permit=permit,
        lease=_synthetic_phase_lease(permit),
        services=service,
        run_identity_path=Path(permit.paths["run_identity_path"]),
        completion_inventory_path=Path(permit.paths["completion_inventory_path"]),
        train_terminal_path=Path(permit.paths["train_terminal_path"]),
        occupied_identity_digests=(),
        master_source=lambda _: b"b" * 32,
        master_sealer=_SyntheticMasterSealer(),
    )
    with pytest.raises(RunnerContractError, match="supplied run_identity_path differs"):
        _run_training_with_permit(
            permit=permit,
            lease=_synthetic_phase_lease(permit),
            services=service,
            run_identity_path=root / "DIFFERENT.json",
            completion_inventory_path=Path(permit.paths["completion_inventory_path"]),
            train_terminal_path=Path(permit.paths["train_terminal_path"]),
            occupied_identity_digests=(),
            master_source=lambda _: b"c" * 32,
            master_sealer=_SyntheticMasterSealer(),
        )
    changed_source = _permit(
        root=root,
        phase=TRAIN_PHASE,
        lease_id="CONTINUATION",
        source_manifest_sha256="9" * 64,
    )
    with pytest.raises(RunnerContractError, match="binding differs"):
        _run_training_with_permit(
            permit=changed_source,
            lease=_synthetic_phase_lease(changed_source),
            services=service,
            run_identity_path=Path(changed_source.paths["run_identity_path"]),
            completion_inventory_path=Path(changed_source.paths["completion_inventory_path"]),
            train_terminal_path=Path(changed_source.paths["train_terminal_path"]),
            occupied_identity_digests=(),
            master_source=lambda _: b"c" * 32,
            master_sealer=_SyntheticMasterSealer(),
        )
    identity_path = Path(permit.paths["run_identity_path"])
    value = json.loads(identity_path.read_text(encoding="ascii"))
    value["master_digest"] = "0" * 64
    identity_path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="ascii"
    )
    with pytest.raises(RunnerContractError, match="master digest changed"):
        _run_training_with_permit(
            permit=permit,
            lease=_synthetic_phase_lease(permit),
            services=service,
            run_identity_path=identity_path,
            completion_inventory_path=Path(permit.paths["completion_inventory_path"]),
            train_terminal_path=Path(permit.paths["train_terminal_path"]),
            occupied_identity_digests=(),
            master_source=lambda _: b"c" * 32,
            master_sealer=_SyntheticMasterSealer(),
        )


def test_public_training_prelease_stops_before_native_master_and_paths(tmp_path) -> None:
    calls: list[str] = []

    def bomb(*args, **kwargs):
        calls.append("called")
        raise AssertionError

    root = (tmp_path / "must-not-exist").resolve()
    with pytest.raises(Exception):
        run_training_phase(
            lease={},
            now=datetime.now(timezone.utc),
            services=bomb,
            run_identity_path=root / "RUN.json",
            completion_inventory_path=root / "COMPLETE.json",
            train_terminal_path=root / "TERMINAL.json",
            cached_native_guard=bomb,
            occupied_identity_digests=(),
            master_source=bomb,
            master_sealer=_SyntheticMasterSealer(),
        )
    assert calls == [] and not root.exists()
