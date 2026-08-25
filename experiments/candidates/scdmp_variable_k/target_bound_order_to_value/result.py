from __future__ import annotations

import math

import numpy as np

from .config import CANDIDATE, PROSPECTIVE_COST, REVISION, static_contract


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


def complete_packet(*, master_hex: str, manifest: dict[str, object],
                    seed_results: list[dict[str, object]], inference: dict[str, object],
                    lifecycle: dict[str, object], frontier_path: str,
                    activity_sidecar: str, anomalies: list[dict[str, object]],
                    implementation_facts: dict[str, object]) -> dict[str, object]:
    if len(seed_results) != 10 or inference.get("partial_selection_permitted") is not False:
        raise ValueError("r07 Stage-A result must contain one complete atomic ten-seed panel")
    safe_seed_results, seed_nonfinite = _json_safe(seed_results, "$.seed_results")
    safe_inference, inference_nonfinite = _json_safe(inference, "$.inference")
    return {
        "artifact_kind": "SCDMP_TBOV_R07_COMPLETE_STAGE_A_RESULT",
        "candidate": CANDIDATE,
        "revision": REVISION,
        "stage": "STAGE_A_ONLY",
        "complete": True,
        "question_relevant_output_exists": True,
        "scientific_activity_started": True,
        "partial_selection_permitted": False,
        "master_M_hex_revealed_only_in_complete_result": master_hex,
        "manifest": manifest,
        "seed_results": safe_seed_results,
        "inference": safe_inference,
        "nonfinite_paths": seed_nonfinite + inference_nonfinite,
        "selected_branch": inference["branch"],
        "static_contract": static_contract(),
        "prospective_cost": dict(PROSPECTIVE_COST),
        "implementation_facts": implementation_facts,
        "lifecycle": lifecycle,
        "retained_frontier": frontier_path,
        "activity_sidecar": activity_sidecar,
        "anomalies": anomalies,
        "stage_b": None,
        "stage_b_implemented_or_executed": False,
    }
