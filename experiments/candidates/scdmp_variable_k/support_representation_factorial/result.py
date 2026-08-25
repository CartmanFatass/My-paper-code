from __future__ import annotations

import math

import numpy as np

from .config import (
    CANDIDATE,
    PROSPECTIVE_COST,
    RESULT_OBJECT,
    REVISION,
    static_contract,
)


def _json_safe(value: object, path: str = "$") -> tuple[object, list[str]]:
    nonfinite: list[str] = []
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, child in value.items():
            converted, paths = _json_safe(child, f"{path}.{key}")
            result[str(key)] = converted
            nonfinite.extend(paths)
        return result, nonfinite
    if isinstance(value, (list, tuple)):
        result = []
        for index, child in enumerate(value):
            converted, paths = _json_safe(child, f"{path}[{index}]")
            result.append(converted)
            nonfinite.extend(paths)
        return result, nonfinite
    if isinstance(value, (np.floating, float)):
        converted = float(value)
        if not math.isfinite(converted):
            return None, [path]
        return converted, nonfinite
    if isinstance(value, np.integer):
        return int(value), nonfinite
    if isinstance(value, np.bool_):
        return bool(value), nonfinite
    return value, nonfinite


def complete_packet(
    *,
    master_hex: str,
    manifest: dict[str, object],
    cell_packets: list[dict[str, object]],
    inference: dict[str, object],
    count_accounting: dict[str, object],
    lifecycle: dict[str, object],
    frontier_path: str,
    activity_sidecar: str,
    implementation_facts: dict[str, object],
) -> dict[str, object]:
    if len(cell_packets) != 40 \
            or inference.get("partial_inspection_permitted") is not False:
        raise ValueError("SRF r03 result requires one complete atomic 40-checkpoint panel")
    safe_packets, packet_nonfinite = _json_safe(cell_packets, "$.cell_packets")
    safe_inference, inference_nonfinite = _json_safe(inference, "$.inference")
    return {
        "artifact_kind": "SCDMP_TBOV_SRF_R03_COMPLETE_FACTORIAL_RESULT",
        "candidate": CANDIDATE,
        "result_object": RESULT_OBJECT,
        "revision": REVISION,
        "complete": True,
        "question_relevant_output_exists": True,
        "scientific_activity_started": True,
        "partial_inspection_permitted": False,
        "master_M_hex_revealed_only_in_complete_result": master_hex,
        "manifest": manifest,
        "cell_packets": safe_packets,
        "inference": safe_inference,
        "nonfinite_paths": packet_nonfinite + inference_nonfinite,
        "selected_branch": inference["branch"],
        "competence_modifier": inference["competence_modifier"],
        "claim_ceiling": (
            "Exact fixed-four-carrier direct checkpoint task only: ten fresh paired seeds, "
            "600 AdamW steps, the frozen 0.65 untouched-fit-support rule, and the simultaneous "
            "three-effect family may support only a finite-package support, representation, "
            "or interaction change with the valid four-cell competence vector."
        ),
        "does_not_authorize": [
            "order treatment", "relation assay", "Stage B", "another budget",
            "second surface", "UAV work",
        ],
        "strongest_alternative": (
            "finite-package support/scaler geometry and representation-specific parameter, "
            "curvature, clipping, and AdamW-history differences"
        ),
        "static_contract": static_contract(),
        "count_accounting": count_accounting,
        "prospective_cost": dict(PROSPECTIVE_COST),
        "implementation_facts": implementation_facts,
        "lifecycle": lifecycle,
        "retained_frontier": frontier_path,
        "activity_sidecar": activity_sidecar,
        "stage_b": None,
        "stage_b_implemented_or_executed": False,
    }
