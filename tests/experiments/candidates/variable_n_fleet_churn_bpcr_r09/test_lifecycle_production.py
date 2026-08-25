from __future__ import annotations

from pathlib import Path

import pytest

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.contracts import SHARED_COMPONENT
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.lifecycle import (
    ConstructionEvidence,
    EvidenceLifecycleError,
)
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.production import (
    ProductionAdmissionError,
    require_native_production,
)


def test_create_only_atomic_lifecycle_and_failure_injection(tmp_path: Path) -> None:
    evidence=ConstructionEvidence(tmp_path/"ok")
    evidence.add_record("fixture",{"schema":"fixture-v1","ok":True},writer="native-conformance")
    manifest=evidence.seal({"card":"a"*64})
    assert manifest.is_file()
    with pytest.raises(EvidenceLifecycleError):evidence.add_record("later",{},writer="wrong")
    with pytest.raises(FileExistsError):ConstructionEvidence(tmp_path/"ok")

    def fail(phase: str) -> None:
        if phase == "write_once:temp_fsynced:manifest": raise RuntimeError("injected")
    partial=ConstructionEvidence(tmp_path/"partial",failure_hook=fail)
    partial.add_record("one",{"x":1},writer="fixture")
    with pytest.raises(RuntimeError):partial.seal({"card":"b"*64})
    assert not (tmp_path/"partial"/"manifest.json").exists()
    assert not tuple((tmp_path/"partial").glob(".manifest.json.*.tmp"))


def test_production_guard_rejects_nonexact_receipt() -> None:
    def bad_guard(*args,**kwargs):
        return {"schema":"HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1","component":SHARED_COMPONENT,"backend":"python","full_reset_step_cpp":False,"python_fallback":True}
    with pytest.raises(ProductionAdmissionError):require_native_production(batch_width=8,shared_guard=bad_guard)


def test_real_shared_guard_binds_general_native_host() -> None:
    receipt=require_native_production(batch_width=32)
    assert receipt["shared"]["component"]==SHARED_COMPONENT
    assert receipt["shared"]["full_reset_step_cpp"]
    assert receipt["local"]["full_reset_step_cpp"]
    assert receipt["local"]["bcrh_scorer_checker_cpp"]
    assert not receipt["python_environment_loop"]
    assert not receipt["python_action_loop"]
    assert not receipt["python_fallback"]
