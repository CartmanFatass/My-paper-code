"""Post-hoc descriptive B02 reading only; no host, policy or optimizer calls."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def stats(values):
    values = np.asarray(values, dtype=np.float64)
    return {"n": len(values), "mean": float(values.mean()),
            "min": float(values.min()), "max": float(values.max())} if len(values) else None


def read(out):
    verified = json.loads((out / "reading.json").read_text())
    manifest = out / "manifest.json"
    if (verified["status"] != "verified" or verified["native_steps_checked"] != 672000
            or hashlib.sha256(manifest.read_bytes()).hexdigest() != verified["manifest_sha256"]):
        raise ValueError("complete frozen verification is required before descriptive reading")
    rows = json.loads((out / "perworld.json").read_text())
    panels, tails = {}, []
    for arm in ("L0", "L1", "A", "R50"):
        panel = [row for row in rows if row["arm"] == arm]
        probabilities, target_probabilities, requests, executed, all_seen = [], [], [], [], []
        eligible_count = 0
        for row in panel:
            path = out / row["raw_path"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != row["raw_sha256"]:
                raise ValueError("raw trace identity differs")
            with np.load(path, allow_pickle=False) as raw:
                eligible = raw["plan_eligible"].astype(bool)
                requested = raw["plan_requested"]
                effective = raw["plan_executed"]
                eligible_count += int(eligible.sum())
                requests.extend(map(int, requested))
                executed.extend(map(int, effective))
                if arm in ("L0", "L1"):
                    probabilities.extend(raw["plan_service_probability"][eligible])
                    target_probabilities.extend(raw["plan_selected_conditional_target_probability"][effective > 0])
                first_seen = raw["sense_first_seen_step"]
                all_seen.append(int(first_seen.max()) if np.all(first_seen >= 0) else None)
                reserve = raw["battery"] <= .10
                tails.append({"arm": arm, "seed": row["seed"],
                              "persistent_reserve_uavs_last300": int(np.all(reserve[-300:], axis=0).sum()),
                              "reserve_uav_step_fraction_last300": float(reserve[-300:].mean()),
                              "final_reserve_uavs": int(reserve[-1].sum()),
                              "minimum_battery": float(raw["battery"].min())})
        panels[arm] = {"eligible_plans": eligible_count,
                       "requested_histogram": dict(sorted(Counter(requests).items())),
                       "executed_histogram": dict(sorted(Counter(executed).items())),
                       "eligible_service_probability": stats(probabilities),
                       "executed_target_conditional_probability": stats(target_probabilities),
                       "all_users_first_seen_step": dict(zip(map(str, [r["seed"] for r in panel]), all_seen))}
    exposure_path = out / "training/exposure.jsonl"
    expected = json.loads(manifest.read_text())["artifacts"]["training/exposure.jsonl"]
    if hashlib.sha256(exposure_path.read_bytes()).hexdigest() != expected["sha256"]:
        raise ValueError("training exposure identity differs")
    exposure = [json.loads(line) for line in exposure_path.read_text().splitlines()]
    blocks = []
    for start in range(0, 16000, 4000):
        block = exposure[start:start + 4000]
        eligible = [row for row in block if row["eligible"]]
        blocks.append({"macros": [start + 1, start + 4000], "eligible": len(eligible),
                       "eligible_service": sum(row["requested"] == 0 for row in eligible),
                       "all_service": sum(row["requested"] == 0 for row in block),
                       "eligible_service_probability": stats([row["service_probability"] for row in eligible]),
                       "eligible_target_entropy": stats([row["target_entropy"] for row in eligible])})
    return {"status": "descriptive_posthoc", "new_native_steps": 0,
            "source_sha": verified["source_sha"], "manifest_sha256": verified["manifest_sha256"],
            "panels": panels, "risk_tails": tails, "training_blocks": blocks}


if __name__ == "__main__":
    print(json.dumps(read(Path(sys.argv[1])), sort_keys=True, allow_nan=False))
