from __future__ import annotations

from .config import CANDIDATE, REVISION
from .lifecycle import Lifecycle


def incomplete(lifecycle: Lifecycle, reason: str, partial: dict[str, object],
    static: dict[str, object], resources: dict[str, object] | None) -> dict[str, object]:
    return {"artifact_kind": "SCDMP_B2_V2_RESULT", "candidate": CANDIDATE,
            "revision": REVISION, "complete": False,
            "scientific_activity_started": lifecycle.scientific_activity_started,
            "question_relevant_output_exists": False, "reason": reason,
            "lifecycle": lifecycle.facts(), "static_conformance": static,
            "partial": partial, "resources": resources,
            "scientific_interpretation": None}


def complete(lifecycle: Lifecycle, static: dict[str, object], seeds: list[dict[str, object]],
    inference: dict[str, object], resources: dict[str, object], ledger: dict[str, int],
    sidecar: str) -> dict[str, object]:
    return {"artifact_kind": "SCDMP_B2_V2_RESULT", "candidate": CANDIDATE,
            "revision": REVISION, "complete": True, "scientific_activity_started": True,
            "question_relevant_output_exists": True, "lifecycle": lifecycle.facts(),
            "static_conformance": static, "seeds": seeds, "inference": inference,
            "resources": resources, "analytic_environment_ledger": ledger,
            "activity_sidecar": sidecar, "anomalies": [],
            "scientific_interpretation": None,
            "interpretation_owner": "EM_semigroup_consistent_duration_model_policy"}
