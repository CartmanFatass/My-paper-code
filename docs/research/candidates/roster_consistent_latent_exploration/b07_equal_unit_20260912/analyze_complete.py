"""Reduce the preserved B07 panels only; no model, RNG or native execution."""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = Path("temp/directions/roster_consistent_latent_exploration")
OLD = EXP / "b07-equal-unit-collection/raw"
NEW = EXP / "b07-reference-completion-collection/raw"
learned_bytes = (OLD / "output/learned/summary.json").read_bytes()
assert hashlib.sha256(learned_bytes).hexdigest() == "c6366cdb44ffd30325dba0c1a9164282d5725ab3e6ba59265bb7aefe16c9afbd"
learned = json.loads(learned_bytes)
reference = json.loads((NEW / "output/reference/summary.json").read_text())
partial = json.loads((HERE / "PARTIAL_ANALYSIS.json").read_text())
assert learned["status"] == reference["status"] == "COMPLETE"
assert learned["launch_sha"] == "1652c44ac65ed6e686610c3cfcff67dab1a0fc6b"
assert reference["launch_sha"] == "9eeef867f0adcf6d9a8ca9441781ad4ec2764a30"
for key in ("object", "seed", "root_key_hex", "block_digest_hex", "action_law"):
    assert learned[key] == reference[key]
for key in ("source_sha256", "artifact_sha256", "build_key", "abi", "runtime_abi", "toolchain"):
    assert learned["native"][key] == reference["native"][key]
assert reference["allocations"] == {"models": 0, "training_instances": 0}
assert reference["reference_packed_views"] is False and reference["curves"] == []
assert reference["counts"]["final_episodes"] == 2048
assert all(value == 0 for key, value in reference["counts"].items() if key != "final_episodes")
admission = json.loads((NEW / "output/reference-admission.json").read_text())
assert admission["passed"] and admission["failure_reasons"] == []
assert admission["minimum_available_bytes"] == 4 * 1024**3
assert "learned-summary.json: OK" in (NEW / "supervisor/task.log").read_text()
assert (NEW / "supervisor/exit_code").read_text().strip() == "0"

panels = dict(initial=learned["initialization_panel"], final=learned["scenarios"], reference=reference["scenarios"])
cells = sorted(partial["cells"])
assert all(len(rows) == 2048 and sorted({r["cell"] for r in rows}) == cells for rows in panels.values())
cell_results, differences = {}, {}
for cell in cells:
    groups = {arm: sorted([r for r in rows if r["cell"] == cell], key=lambda r: r["index"])
              for arm, rows in panels.items()}
    assert all([r["index"] for r in rows] == list(range(256)) for rows in groups.values())
    assert all(r["arm"] == "INDEPENDENT-NEAREST" and r["Y"] is None for r in groups["reference"])
    result = {"n_per_panel": 256}
    for metric in ("U", "F", "tau", "Y"):
        values = {arm: np.asarray([r[metric] for r in rows], dtype=np.float64)
                  for arm, rows in groups.items() if metric != "Y" or arm != "reference"}
        upper = 40 if metric == "tau" else 1
        assert all(np.isfinite(v).all() and ((v >= 0) & (v <= upper)).all() for v in values.values())
        record = {arm: float(v.mean()) for arm, v in values.items()}
        record["reference"] = record.get("reference")
        for contrast, arm in (("final_minus_initial", "initial"), ("final_minus_reference", "reference")):
            if arm not in values:
                record[contrast] = None
                continue
            diff = values["final"] - values[arm]
            record[contrast] = float(diff.mean())
            record[contrast + "_conditional_se"] = float(diff.std(ddof=1) / np.sqrt(256))
            differences[(cell, metric, contrast)] = diff
        result[metric] = record
    result["40U"] = {key: value * 40 for key, value in result["U"].items()}
    result["tau40_count"] = {arm: sum(r["tau"] == 40 for r in rows) for arm, rows in groups.items()}
    result["Delta_ref"] = -result["U"]["final_minus_reference"]
    result["G_U"] = -result["U"]["final_minus_initial"]
    published = reference["comparison"]["cells"][cell]
    for key in ("Delta_ref", "G_U"):
        assert abs(result[key] - published[key]) < 1e-14
    for contrast in ("final_minus_initial", "final_minus_reference"):
        for metric in ("U", "F", "tau"):
            assert abs(result[metric][contrast] - published[contrast][metric]) < 1e-14
    for metric in ("U", "F", "tau"):
        assert abs(result[metric]["reference"] - reference["cells"][cell][metric + "_mean"]) < 1e-14
    assert result["tau40_count"]["reference"] == reference["cells"][cell]["tau40_count"]
    cell_results[cell] = result

primary_cells = ["8_to_12.ACTIVE_CONTINUATION", "12_to_8.ACTIVE_CONTINUATION"]
primary = {arm + "_U": float(np.mean([cell_results[c]["U"][arm] for c in primary_cells])) for arm in panels}
for name, contrast in (("Delta_ref", "final_minus_reference"), ("G_U", "final_minus_initial")):
    point = float(np.mean([cell_results[c][name] for c in primary_cells]))
    se = float(np.sqrt(sum(cell_results[c]["U"][contrast + "_conditional_se"] ** 2 for c in primary_cells)) / 2)
    diff = -np.concatenate([differences[(c, "U", contrast)] for c in primary_cells])
    primary.update({name: point, name + "_conditional_se": se,
                    name + "_normal95": [point - 1.96 * se, point + 1.96 * se],
                    name + "_scenario_signs": {"positive": int((diff > 0).sum()), "zero": int((diff == 0).sum()),
                                               "negative": int((diff < 0).sum())}})
    assert abs(point - reference["comparison"]["primary"][name]) < 1e-14
assert abs(primary["Delta_ref_conditional_se"] - reference["comparison"]["primary"]["SE"]) < 1e-14
assert abs(primary["G_U_conditional_se"] - partial["primary"]["G_U_conditional_se"]) < 1e-14
harms = {contrast: {metric: sum(cell_results[c][metric][contrast] > 0 for c in cells) for metric in ("U", "F", "tau")}
         for contrast in ("final_minus_initial", "final_minus_reference")}
assert primary["G_U"] <= 0 and primary["Delta_ref"] <= 0
assert any(harms[c][m] > 0 for c in harms for m in ("F", "tau"))
assert reference["reading"] == ["no positive learning from initialization", "mixed native consequences"]
manifest = []
for path in sorted(NEW.rglob("*")):
    if path.is_file():
        data = path.read_bytes()
        manifest.append({"path": path.relative_to(NEW).as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
result = {
    "status": "COMPLETE_VALID_B_LOCAL_REFERENCE_DEFICIT_NO_POSITIVE_INIT_LEARNING_MIXED",
    "object": learned["object"], "seed": learned["seed"], "independent_training_instances": 1,
    "learned_source_sha": learned["launch_sha"], "reference_source_sha": reference["launch_sha"],
    "learned_input_sha256": hashlib.sha256(learned_bytes).hexdigest(),
    "root_key_hex": learned["root_key_hex"], "block_digest_hex": learned["block_digest_hex"],
    "native_kernel": {k: reference["native"][k] for k in ("source_sha256", "artifact_sha256", "build_key")},
    "reference_counts": reference["counts"], "reference_allocations": reference["allocations"],
    "counts": {"training_episodes": 64000, "init_episodes": 2048, "final_episodes": 2048, "reference_episodes": 2048,
               "completed_episodes": 64000 + 3 * 2048, "completed_native_ticks": (64000 + 3 * 2048) * 64,
               "derivative_traversals": 2000, "nonzero_updates": 1000,
               "failed_reference_unreturned_work": "unknown; physical total includes this in addition to completed counts"},
    "primary_cells": primary_cells, "primary": primary, "MEI_U": .05, "cells": cell_results,
    "harms": harms, "tau40_count": {arm: sum(r["tau"] == 40 for r in rows) for arm, rows in panels.items()},
    "prediction": {"event": "Delta_ref>=.05 and G_U>0", "probability": .25, "occurred": False,
                   "brier": (.25 - 0)**2, "owner": "not taken"},
    "reference_admission": admission, "reference_manifest": manifest,
    "native_wall_s": {"original_chain": 338.90, "reference_completion": 4.53,
                      "combined": 338.90 + 4.53, "failed_and_completed_reference": 2.43 + 4.53},
    "reading": reference["reading"],
    "interpretation_limit": "One fit; scenario intervals conditional on the fitted policies. No stable superiority/degradation, equivalence, joint100 attribution, recovery success, family disposition or successor authorization. Eager reference success does not identify or globally cure the original error."
}
(HERE / "FINAL_ANALYSIS.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in ("status", "primary", "harms", "tau40_count", "counts", "native_wall_s", "prediction")}, indent=2))
