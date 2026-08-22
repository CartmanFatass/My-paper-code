"""Fail-closed native-production admission; no reference fallback exists."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from envs.native.production_backend import require_cpp_batched_production

from .contracts import SHARED_COMPONENT
from .native_backend import native_artifact_identity


class ProductionAdmissionError(PermissionError):
    pass


def require_native_production(
    *, batch_width:int,
    shared_guard:Callable[...,Mapping[str,object]]=require_cpp_batched_production,
) -> dict[str,object]:
    """Require the shared declaration and the exact candidate-local artifact."""
    receipt=dict(shared_guard(SHARED_COMPONENT,backend="cpp",batch_width=batch_width,build_root=None))
    expected={"schema":"HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1","component":SHARED_COMPONENT,"backend":"cpp","full_reset_step_cpp":True,"python_fallback":False}
    if any(receipt.get(key)!=value for key,value in expected.items()):raise ProductionAdmissionError("shared native receipt differs from BPCR full-host contract")
    local=native_artifact_identity()
    if (
        not local["full_reset_step_cpp"]
        or not local["bcrh_scorer_checker_cpp"]
        or not local["action_sensitivity_cpp"]
        or local["python_fallback"]
    ):
        raise ProductionAdmissionError("candidate-local native conformance is incomplete")
    return {"schema":"VNFC-BPCR-R09-NATIVE-PRODUCTION-PREFLIGHT-v1","shared":receipt,"local":local,"python_environment_loop":False,"python_action_loop":False,"python_fallback":False}
