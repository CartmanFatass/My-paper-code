"""Analyze only collected B07 bytes; no model construction, RNG or native execution."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

RAW = Path("temp/directions/roster_consistent_latent_exploration/b07-equal-unit-collection/raw")
OUTPUT = Path(__file__).resolve().parent
learned = json.loads((RAW / "output/learned/summary.json").read_text())
reference = json.loads((RAW / "output/reference/summary.json").read_text())
assert learned["status"] == "COMPLETE" and reference["status"] == "TECHNICAL_STOP"
assert learned["root_key_hex"] == reference["root_key_hex"]
assert learned["block_digest_hex"] == reference["block_digest_hex"]
curves = [json.loads(line) for line in (RAW / "output/learned/completed_blocks.jsonl").read_text().splitlines()]
assert curves == learned["curves"]
assert [curve["update"] for curve in curves] == list(range(1000))
assert all(curve["event_order"] == ["parameter_update", "baseline_update"] for curve in curves)
assert all(curve["nonzero"] and curve["score_channel_derivative_traversals"] == 2 for curve in curves)
initial, final = learned["initialization_panel"], learned["scenarios"]
assert initial == json.loads((RAW / "output/learned/init_scenarios.json").read_text())
cells = sorted({row["cell"] for row in initial})
assert len(cells) == 8
cell_results = {}
all_differences = {}
for cell in cells:
    pair = [sorted([r for r in rows if r["cell"] == cell], key=lambda r: r["index"]) for rows in (initial, final)]
    assert [[r["index"] for r in rows] for rows in pair] == [list(range(256)), list(range(256))]
    result = {"n": 256}
    for key in ("U", "F", "tau", "Y"):
        arrays = [np.array([row[key] for row in rows], dtype=np.float64) for rows in pair]
        assert all(np.isfinite(array).all() for array in arrays)
        upper = 40 if key == "tau" else 1
        assert all(((array >= 0) & (array <= upper)).all() for array in arrays)
        diff = arrays[0] - arrays[1]
        result[key] = {"initial": float(arrays[0].mean()), "final": float(arrays[1].mean()),
                       "initial_minus_final": float(diff.mean()),
                       "conditional_se": float(diff.std(ddof=1) / np.sqrt(256))}
        all_differences[(cell, key)] = diff
    result["initial_tau40"] = sum(row["tau"] == 40 for row in pair[0])
    result["final_tau40"] = sum(row["tau"] == 40 for row in pair[1])
    cell_results[cell] = result
primary_cells = ["8_to_12.ACTIVE_CONTINUATION", "12_to_8.ACTIVE_CONTINUATION"]
g_u = float(np.mean([cell_results[cell]["U"]["initial_minus_final"] for cell in primary_cells]))
se = float(np.sqrt(sum(cell_results[cell]["U"]["conditional_se"] ** 2 for cell in primary_cells)) / 2)
scores = np.concatenate([all_differences[(cell, "U")] for cell in primary_cells])
checkpoint = [torch.load(RAW / ("output/learned/" + name), map_location="cpu", weights_only=True)
              for name in ("initial_parameters.pt", "parameters.pt")]
states = [entry["state_dict"] for entry in checkpoint]
assert list(states[0]) == list(states[1])
vectors = [torch.cat([tensor.reshape(-1) for tensor in state.values()]) for state in states]
assert all(vector.numel() == 26161 and vector.dtype == torch.float64 and torch.isfinite(vector).all() for vector in vectors)
assert all(entry["action_law"] == learned["action_law"] for entry in checkpoint)
assert all(torch.count_nonzero(states[0][key]) == 0 for key in ("pointer_score.weight", "pointer_score.bias"))
displacement = float(torch.linalg.vector_norm(vectors[1] - vectors[0]))
manifest = []
for path in sorted(RAW.rglob("*")):
    if path.is_file():
        value = path.read_bytes()
        manifest.append({"path": str(path.relative_to(RAW)).replace("\\", "/"), "bytes": len(value),
                         "sha256": hashlib.sha256(value).hexdigest()})
result = {
    "status": "PARTIAL_LEARNED_VALID_REFERENCE_PRIMARY_MISSING",
    "source_sha": learned["launch_sha"], "object": learned["object"], "seed": learned["seed"],
    "root_key_hex": learned["root_key_hex"], "block_digest_hex": learned["block_digest_hex"],
    "counts": learned["counts"], "completed_episodes": 64000 + len(initial) + len(final),
    "completed_native_ticks": (64000 + len(initial) + len(final)) * 64,
    "published_reference_rows": len(reference["scenarios"]),
    "unreturned_reference_work": "unknown; zero published rows is not zero native work",
    "cells": cell_results,
    "primary": {"initial_U": float(np.mean([cell_results[c]["U"]["initial"] for c in primary_cells])),
                "final_U": float(np.mean([cell_results[c]["U"]["final"] for c in primary_cells])),
                "Delta_ref": None, "G_U": g_u, "G_U_conditional_se": se,
                "G_U_normal95": [g_u - 1.96 * se, g_u + 1.96 * se],
                "G_U_scenario_signs": {"positive": int((scores > 0).sum()), "zero": int((scores == 0).sum()),
                                       "negative": int((scores < 0).sum())}},
    "final_minus_initial_harms": {key: sum(cell_results[c][key]["initial_minus_final"] < 0 for c in cells)
                                 for key in ("U", "F", "tau")},
    "tau40_count": {"initial": sum(row["tau"] == 40 for row in initial),
                    "final": sum(row["tau"] == 40 for row in final)},
    "parameters": {"scalar_count": 26161, "dtype": "FP64", "all_finite": True,
                   "initial_norm": float(torch.linalg.vector_norm(vectors[0])),
                   "final_displacement": displacement,
                   "displacement_over_initial_norm": displacement / float(torch.linalg.vector_norm(vectors[0]))},
    "curve_totals": {key: sum(row[key] for row in curves) for key in
                    ("training_episodes", "environment_ticks", "agent_ticks", "agent_claim_decisions")},
    "curve_bounds": {key: {"minimum": min(row[key] for row in curves), "maximum": max(row[key] for row in curves)}
                    for key in ("parameter_delta_norm", "measured_parameter_delta_norm",
                                "manager_max_abs_gradient", "claim_max_abs_gradient", "combined_unit_direction_norm")},
    "training_Y_mean_bounds": {"minimum": min(np.mean([c["Y_mean"] for c in row["per_cell"]]) for row in curves),
                                "maximum": max(np.mean([c["Y_mean"] for c in row["per_cell"]]) for row in curves)},
    "reference_stop_reason_raw": reference["stop_reason"],
    "native_wall_s": {"chain": 338.90, "learned": 336.46, "reference_failed": 2.43},
    "remaining_native_total_s": 900 - 338.90,
    "remaining_reference_original_split_s": 15 - 2.43,
    "manifest": manifest,
    "interpretation_limit": "One fit, conditional scenario uncertainty, no reference contrast or complete service result. No root-cause inference from the exception alone."
}
(OUTPUT / "PARTIAL_ANALYSIS.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
print(json.dumps({key: result[key] for key in ("status", "primary", "final_minus_initial_harms", "tau40_count", "parameters",
                                             "completed_episodes", "completed_native_ticks", "curve_totals",
                                             "remaining_native_total_s", "remaining_reference_original_split_s")}, indent=2))
