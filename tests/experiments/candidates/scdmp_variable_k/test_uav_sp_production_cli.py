from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value import production
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.lease import (
    EVALUATE_PHASE,
    TRAIN_PHASE,
    accepted_construction_binding,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.runner import (
    EvaluationPhaseResult,
    TrainingPhaseResult,
)


NOW = datetime(2026, 8, 20, 12, tzinfo=timezone.utc)


def _paths(tmp_path: Path) -> dict[str, Path]:
    root = tmp_path / "result"
    return {
        "lease": tmp_path / "lease.json",
        "root": root,
        "result": root / "RESULT.json",
        "identity": root / "RUN_IDENTITY.json",
        "completion": root / "CHECKPOINT_COMPLETION.json",
        "acceptance": root / "CM_ACCEPTANCE.json",
        "train_terminal": root / "TRAIN_TERMINAL.json",
        "evaluate_terminal": root / "EVALUATE_TERMINAL.json",
    }


def _lease(paths: dict[str, Path], *, phase: str) -> dict[str, object]:
    binding = accepted_construction_binding()
    return {
        "schema": "synthetic",
        "lease_id": f"SYNTHETIC-{phase}",
        "activity_authorized": True,
        "stage": "synthetic",
        "card_revision": binding["card_revision"],
        "card_sha256": binding["card_sha256"],
        "component": binding["component"],
        "abi_version": 2,
        "coordinate_plan_digest": "1" * 64,
        "construction_binding": binding,
        "complete_panel_only": True,
        "prohibitions": [],
        "issued_at": "2026-08-20T00:00:00+00:00",
        "expires_at": "2026-08-21T00:00:00+00:00",
        "resources": {
            "cpu_only": True,
            "gpu_count": 0,
            "independent_workers": 1,
            "ram_gib": 8,
            "scratch_gib": 1,
            "durable_artifacts_gib": 1,
            "torch_threads": 1,
        },
        "empirical_source_manifest_sha256": "2" * 64,
        "phase": phase,
        "paths": {
            "result_root": str(paths["root"].resolve()),
            "result_path": str(paths["result"].resolve()),
            "train_terminal_path": str(paths["train_terminal"].resolve()),
            "evaluation_terminal_path": str(paths["evaluate_terminal"].resolve()),
            "run_identity_path": str(paths["identity"].resolve()),
            "completion_inventory_path": str(paths["completion"].resolve()),
            "cm_acceptance_path": str(paths["acceptance"].resolve()),
        },
        "execution": {"synthetic": True},
        "occupied_digest_registry": None,
    }


def _write_lease(paths: dict[str, Path], *, phase: str) -> dict[str, object]:
    value = _lease(paths, phase=phase)
    paths["lease"].write_text(json.dumps(value), encoding="utf-8")
    return value


def _kwargs(paths: dict[str, Path], *, phase: str) -> dict[str, object]:
    return {
        "phase": phase,
        "lease_path": paths["lease"].resolve(),
        "result_root": paths["root"].resolve(),
        "result_path": paths["result"].resolve(),
        "run_identity_path": paths["identity"].resolve(),
        "checkpoint_completion_path": paths["completion"].resolve(),
        "cm_acceptance_path": paths["acceptance"].resolve(),
        "train_terminal_record": paths["train_terminal"].resolve(),
        "evaluate_terminal_record": paths["evaluate_terminal"].resolve(),
        "now": NOW,
    }


def _patch_read_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(production, "validate_lease_envelope", lambda lease, now: None)
    monkeypatch.setattr(production, "_validate_source_binding", lambda lease: None)
    monkeypatch.setattr(production, "_configure_cpu_runtime", lambda: None)


def test_feature_detection_requires_both_phase_apis_and_never_uses_legacy() -> None:
    legacy = SimpleNamespace(run_empirical_panel=lambda **kwargs: None)
    with pytest.raises(production.ProductionCLIError, match="legacy"):
        production.resolve_two_phase_runner_api(legacy)
    module = SimpleNamespace(run_training_phase=lambda **kwargs: None, run_evaluation_phase=lambda **kwargs: None)
    api = production.resolve_two_phase_runner_api(module)
    assert api.train is module.run_training_phase
    assert api.evaluate is module.run_evaluation_phase


def test_preflight_is_read_only_and_does_not_call_native_or_phase_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _paths(tmp_path)
    _write_lease(paths, phase=TRAIN_PHASE)
    _patch_read_only(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(production, "build_training_services", lambda **kwargs: calls.append("train-service") or object())
    monkeypatch.setattr(production, "build_evaluation_services", lambda **kwargs: calls.append("eval-service") or object())
    monkeypatch.setattr(production, "resolve_two_phase_runner_api", lambda: production.TwoPhaseRunnerAPI(lambda **k: None, lambda **k: None))
    monkeypatch.setattr(production, "_prevalidate_native", lambda *a, **k: (_ for _ in ()).throw(AssertionError("native")))
    receipt = production.execute(**_kwargs(paths, phase=production.PREFLIGHT_PHASE))
    assert receipt["materialized"] is False and receipt["native_guard_called"] is False
    assert calls == ["train-service", "eval-service"]
    assert not paths["root"].exists()


def test_train_phase_stops_at_unaccepted_54_slot_inventory_and_runner_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _paths(tmp_path)
    _write_lease(paths, phase=TRAIN_PHASE)
    _patch_read_only(monkeypatch)
    monkeypatch.setattr(production, "_prevalidate_native", lambda *a, **k: (lambda **kw: {}))
    service = object()
    monkeypatch.setattr(production, "build_training_services", lambda **kwargs: service)
    monkeypatch.setattr(production.os, "urandom", lambda n: bytes(range(n)))

    def train(*, lease, now, services, run_identity_path, completion_inventory_path,
              train_terminal_path, cached_native_guard, occupied_identity_digests,
              master_source, source_manifest_path=None):
        assert services is service and not paths["root"].exists()
        assert master_source(32) == bytes(range(32))
        paths["root"].mkdir()
        run_identity_path.write_text("identity", encoding="ascii")
        completion_inventory_path.write_text("completion", encoding="ascii")
        train_terminal_path.write_text("runner-owned", encoding="ascii")
        return TrainingPhaseResult("a" * 64, "b" * 64, 54, False, False)

    monkeypatch.setattr(production, "resolve_two_phase_runner_api", lambda: production.TwoPhaseRunnerAPI(train, lambda **k: None))
    receipt = production.execute(**_kwargs(paths, phase=TRAIN_PHASE))
    assert receipt == {
        "phase": TRAIN_PHASE,
        "checkpoint_count": 54,
        "evaluation_started": False,
        "result_published": False,
        "cm_acceptance_created_by_operator": False,
    }
    assert paths["train_terminal"].read_text() == "runner-owned"
    assert not paths["acceptance"].exists() and not paths["result"].exists()


def test_evaluate_requires_external_acceptance_and_never_exposes_training_callbacks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _paths(tmp_path)
    _write_lease(paths, phase=EVALUATE_PHASE)
    paths["root"].mkdir()
    for key in ("identity", "completion", "acceptance", "train_terminal"):
        paths[key].write_text(key, encoding="ascii")
    _patch_read_only(monkeypatch)
    monkeypatch.setattr(production, "_prevalidate_native", lambda *a, **k: (lambda **kw: {}))
    service = object()
    monkeypatch.setattr(production, "build_evaluation_services", lambda **kwargs: service)

    def evaluate(*, lease, now, services, run_identity_path, completion_inventory_path,
                 cm_acceptance_path, result_path, evaluation_terminal_path,
                 cached_native_guard, validity, source_manifest_path=None):
        assert services is service and cm_acceptance_path.is_file()
        result_path.write_bytes(b"{}")
        evaluation_terminal_path.write_text("runner-owned", encoding="ascii")
        publication = {"path": str(result_path), "complete_atomic_panel": True}
        return EvaluationPhaseResult("a" * 64, "b" * 64, publication)

    monkeypatch.setattr(production, "resolve_two_phase_runner_api", lambda: production.TwoPhaseRunnerAPI(lambda **k: None, evaluate))
    receipt = production.execute(**_kwargs(paths, phase=EVALUATE_PHASE))
    assert receipt["complete_atomic_panel"] is True
    assert paths["evaluate_terminal"].read_text() == "runner-owned"


def test_training_adapter_keeps_runner_record_digest_distinct_but_master_bound(
    tmp_path: Path,
) -> None:
    paths = _paths(tmp_path)
    lease = _lease(paths, phase=TRAIN_PHASE)
    paths["root"].mkdir()
    public = {"master_digest": "3" * 64}
    raw = json.dumps(public, sort_keys=True).encode("ascii")
    paths["identity"].write_bytes(raw)
    runner_digest = hashlib.sha256(raw).hexdigest()
    adapter = production._TrainingServiceAdapter(
        result_root=paths["root"].resolve(),
        run_identity_path=paths["identity"].resolve(),
        lease=lease,
    )
    adapter._bind(runner_digest)
    internal = adapter._service._run_identity
    assert internal.master_digest == "3" * 64
    assert internal.run_identity_digest != runner_digest
    assert adapter._runner_identity_digest == runner_digest
    with pytest.raises(production.ProductionCLIError, match="digest differs"):
        adapter._bind("4" * 64)


def test_phase_and_absolute_path_must_match_exact_lease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _paths(tmp_path)
    _write_lease(paths, phase=TRAIN_PHASE)
    _patch_read_only(monkeypatch)
    with pytest.raises(production.ProductionCLIError, match="command phase differs"):
        production.prepare_execution(**_kwargs(paths, phase=EVALUATE_PHASE))
    bad = _kwargs(paths, phase=TRAIN_PHASE)
    bad["result_root"] = Path("relative")
    with pytest.raises(production.ProductionCLIError, match="explicit absolute"):
        production.prepare_execution(**bad)


def test_forward_slash_lease_paths_equal_canonical_windows_cli_paths_without_relaxation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _paths(tmp_path)
    value = _lease(paths, phase=TRAIN_PHASE)
    bound = value["paths"]
    assert isinstance(bound, dict)
    value["paths"] = {
        field: Path(raw).as_posix() for field, raw in bound.items()
    }
    paths["lease"].write_text(json.dumps(value), encoding="utf-8")
    _patch_read_only(monkeypatch)

    prepared = production.prepare_execution(**_kwargs(paths, phase=TRAIN_PHASE))
    assert prepared.paths.result_root == paths["root"].resolve()
    assert prepared.paths.result_path == paths["result"].resolve()

    extended = dict(value)
    extended["paths"] = {
        field: "\\\\?\\" + str(Path(raw).resolve())
        for field, raw in value["paths"].items()
    }
    paths["lease"].write_text(json.dumps(extended), encoding="utf-8")
    extended_prepared = production.prepare_execution(**_kwargs(paths, phase=TRAIN_PHASE))
    assert extended_prepared.paths.result_path == paths["result"].resolve()

    changed = dict(value)
    changed_paths = dict(value["paths"])
    changed_paths["result_path"] = (paths["root"] / "WRONG.json").as_posix()
    changed["paths"] = changed_paths
    paths["lease"].write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(production.ProductionCLIError, match="differ from the exact lease"):
        production.prepare_execution(**_kwargs(paths, phase=TRAIN_PHASE))

    changed_paths["result_path"] = "relative/RESULT.json"
    paths["lease"].write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(production.ProductionCLIError, match="must be absolute"):
        production.prepare_execution(**_kwargs(paths, phase=TRAIN_PHASE))
