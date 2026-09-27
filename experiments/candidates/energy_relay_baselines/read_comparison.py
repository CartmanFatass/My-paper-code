"""Read two independent SET development fits without joining their training curves.

No simulator calls, new evaluations, checkpoint selection, or hold-out discovery. Input
panels use the benchmark's native fields. Paired SEs are conditional on each fixed policy;
the two training instances remain the units of descriptive seed variation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.energy_relay_benchmark.b01.read_stage1 import (
    J, Q, RISK, gap_block, summarise,
)

OBJECT_ID = "ENERGY-RELAY-BASELINES-B01"
SEEDS = (26092711, 26092731)
WORLDS = tuple(range(955001, 955033))
MODES = ("deterministic", "stochastic")
CHECKPOINTS = {"c00": (0, 0), "c06": (200, 1_200_000)}
PRIMARY_FIELDS = (Q, J, *RISK, "min_decoded_battery")
PHASE_FIELDS = {f"qos_per_step_{phase}": f"steps_{phase}"
                for phase in ("pre_entry", "entry_to_input", "post_input")}
REFERENCE_PATHS = {
    "H_central": ("b01", "grid/panels/H1_e0.00_x0.05.json"),
    "H_local": ("b01", "reference/panels/Hlocal_e0.00_x0.05.json"),
    "N_deterministic": ("b01", "grid/panels/N_e0.00_x0.05.json"),
    "H_spawn": ("refs", "stage0-references/panels/Hspawn_e0.00_x0.05.json"),
    "H_park2": ("refs", "stage0-references/panels/Hpark2_e0.00_x0.05.json"),
}


def read_json(path: Path, sources: dict) -> dict:
    path = Path(path)
    if any("holdout" in part.lower() for part in path.parts):
        raise ValueError("this development reader does not read hold-out paths")
    payload = path.read_bytes()
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    sources[str(path.resolve())] = hashlib.sha256(payload).hexdigest()
    return value


def panel_rows(panel: dict) -> dict[int, dict]:
    rows = panel.get("worlds")
    if not isinstance(rows, list) or len(rows) != len(WORLDS):
        raise ValueError("complete reading requires all 32 development worlds")
    seeds = [row.get("seed") for row in rows]
    if len(set(seeds)) != len(WORLDS) or set(seeds) != set(WORLDS):
        raise ValueError("missing, duplicate, or non-development world")
    for row in rows:
        if row.get("failed"):
            raise ValueError("failed world cannot be silently excluded from the reading")
        length, terminal = row.get("actual_length"), row.get("terminal_type")
        if (type(length) is not int or not 1 <= length <= 3000
                or terminal not in ("terminated", "truncated")
                or (terminal == "truncated" and length != 3000)):
            raise ValueError("invalid native episode length/terminal type for H3000")
        for field in PRIMARY_FIELDS:
            value = row.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"missing or non-finite primary field {field}")
        for field, count_field in PHASE_FIELDS.items():
            if field not in row or count_field not in row:
                raise ValueError(f"missing required phase field {field}/{count_field}")
            count, value = row[count_field], row[field]
            if type(count) is not int or not 0 <= count <= length:
                raise ValueError(f"invalid phase length {count_field}")
            if (value is None) != (count == 0):
                raise ValueError(f"phase absence and step count disagree: {field}")
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                      or not math.isfinite(value)):
                raise ValueError(f"non-finite phase value {field}")
    return {row["seed"]: row for row in rows}


def summarise_rows(rows: dict[int, dict]) -> dict:
    values = list(rows.values())
    result = summarise(values)
    result["actual_transitions"] = sum(row["actual_length"] for row in values)
    result["terminal_types"] = {kind: sum(row["terminal_type"] == kind for row in values)
                                for kind in ("terminated", "truncated")}
    for field, count_field in PHASE_FIELDS.items():
        result[f"observed_{field}"] = sum(row[field] is not None for row in values)
        result[f"total_{count_field}"] = sum(row[count_field] for row in values)
    return result


def training_record(summary: dict) -> int:
    seed = summary.get("seed")
    if summary.get("object_id") != OBJECT_ID or seed not in SEEDS:
        raise ValueError("unplanned training identity")
    if summary.get("status") != "COMPLETE" or summary.get("failure") or summary.get("resume"):
        raise ValueError("complete fresh fits are required; retain failed/recovered attempts separately")
    counts = summary.get("counts", {})
    if (counts.get("rollouts"), counts.get("transitions")) != CHECKPOINTS["c06"]:
        raise ValueError("training exposure differs from the prepared 1.2M recipe")
    records = summary.get("checkpoints", {})
    for name, expected in CHECKPOINTS.items():
        record = records.get(name, {})
        if (record.get("rollout"), record.get("transitions")) != expected:
            raise ValueError(f"missing or mismatched {name} checkpoint exposure")
        if not record.get("policy_fingerprint") or not record.get("agent_pt_sha256"):
            raise ValueError(f"missing {name} policy identity")
    if records["c00"]["policy_fingerprint"] == records["c06"]["policy_fingerprint"]:
        raise ValueError("no measured learner parameter movement")
    steps = summary.get("optimizer_steps", {})
    if any(isinstance(steps.get(k), bool) or not isinstance(steps.get(k), (int, float)) or steps[k] <= 0
           for k in ("low_actor", "low_critic")):
        raise ValueError("low-level optimiser update counts are absent or zero")
    return seed


def validate_learner_panel(panel: dict, summary: dict, checkpoint: str, mode: str) -> None:
    expected_name = f"L_{checkpoint}_{mode}_e0.00_x0.05"
    if (panel.get("name") != expected_name or panel.get("final")
            or panel.get("checkpoint") != checkpoint or panel.get("action_mode") != mode
            or panel.get("draw") != (0 if mode == "stochastic" else None)):
        raise ValueError("wrong checkpoint/mode or non-development panel")
    if panel.get("policy_seed") != summary["seed"]:
        raise ValueError("panel and training seed differ")
    if (panel.get("rollout"), panel.get("transitions")) != CHECKPOINTS[checkpoint]:
        raise ValueError("panel checkpoint exposure differs")
    expected = summary["checkpoints"][checkpoint]
    identities = panel.get("policy_identity")
    if not isinstance(identities, list) or not identities:
        raise ValueError("panel lacks verified checkpoint identity")
    for identity in identities:
        if (identity.get("checkpoint_sha256") != expected["agent_pt_sha256"]
                or identity.get("policy_fingerprint") != expected["policy_fingerprint"]):
            raise ValueError("panel checkpoint identity differs from the training record")


def make_reading(*, train_dirs, eval_dirs, b01: Path, refs: Path) -> dict:
    sources: dict[str, str] = {}
    training = {}
    for root in train_dirs:
        summary = read_json(Path(root) / "summary.json", sources)
        seed = training_record(summary)
        if seed in training:
            raise ValueError("duplicate independent training seed")
        training[seed] = summary
    if set(training) != set(SEEDS):
        raise ValueError("the complete comparison requires both planned training seeds")
    comparators = {}
    roots = {"b01": Path(b01), "refs": Path(refs)}
    for label, (root, relative) in REFERENCE_PATHS.items():
        panel = read_json(roots[root] / relative, sources)
        if panel.get("name") != Path(relative).stem:
            raise ValueError(f"unexpected reference panel: {label}")
        comparators[label] = panel_rows(panel)
    panels, evaluation_records = {}, {}
    for root in eval_dirs:
        for checkpoint in CHECKPOINTS:
            for mode in MODES:
                path = Path(root) / "checkpoint-eval/panels" / f"L_{checkpoint}_{mode}_e0.00_x0.05.json"
                if not path.is_file():
                    continue
                panel = read_json(path, sources)
                seed = panel.get("policy_seed")
                if seed not in training:
                    raise ValueError("unplanned evaluation seed")
                key = (seed, checkpoint, mode)
                if key in panels:
                    raise ValueError("duplicate checkpoint/mode panel")
                validate_learner_panel(panel, training[seed], checkpoint, mode)
                status_key = (seed, checkpoint)
                if status_key not in evaluation_records:
                    status_path = (Path(root) / "checkpoint-eval"
                                   / f"{checkpoint}_deterministic-stochastic/summary.json")
                    status = read_json(status_path, sources)
                    if (status.get("object_id") != OBJECT_ID or status.get("status") != "COMPLETE"
                            or status.get("failure") or status.get("policy_seed") != seed
                            or status.get("checkpoint") != checkpoint or status.get("final")
                            or status.get("worlds") != list(WORLDS) or status.get("modes") != list(MODES)):
                        raise ValueError("evaluation status/identity is not complete and matched")
                    counts = status.get("counts", {})
                    expected_counts = {"episodes_completed": 64, "panels_completed": 2, "failed_worlds": 0,
                                       "new_optimizer_updates": 0}
                    if any(counts.get(k) != v for k, v in expected_counts.items()):
                        raise ValueError("evaluation counts differ from the complete fixed panel")
                    evaluation_records[status_key] = status
                status = evaluation_records[status_key]
                if (status.get("artifacts", {}).get(f"panels/{path.name}")
                        != sources[str(path.resolve())]):
                    raise ValueError("evaluation panel digest differs from its summary")
                panels[key] = panel_rows(panel)
    expected = {(s, c, m) for s in SEEDS for c in CHECKPOINTS for m in MODES}
    if set(panels) != expected:
        raise ValueError(f"incomplete comparison; missing panels {sorted(expected - set(panels))}")
    for (seed, checkpoint), status in evaluation_records.items():
        actual_steps = sum(row["actual_length"] for mode in MODES
                           for row in panels[(seed, checkpoint, mode)].values())
        if status["counts"].get("steps") != actual_steps:
            raise ValueError("evaluation summary steps differ from summed native episode lengths")
    result = {
        "object_id": OBJECT_ID, "status": "COMPLETE_READING", "independent_fresh_training_n": 2,
        "scope": "exploratory; exposed development worlds; no training-population inference",
        "worlds": list(WORLDS), "sources_sha256": sources,
        "comparator_information": {
            "H_local": "planner pooling eight legal observations; not an independent local actor",
            "H_central": "central-information executable heuristic; not an optimal upper bound",
            "N_deterministic": "old 180k no-training-shield HMASD package; unequal exposure",
            "H_spawn": "reset-waypoint package with production shield",
            "H_park2": "two station waypoints on the reset-waypoint background",
            "learner": "recurrent SET; own observation plus central snapshot held for k=10",
        },
        "comparators": {label: summarise_rows(rows) for label, rows in comparators.items()},
        "seeds": {}, "descriptive_seed_spread": {},
        "uncertainty_note": "paired SE is world variation conditional on a fixed trained policy; n=2 seed SD is descriptive, not a test",
    }
    for seed in SEEDS:
        summary = training[seed]
        entry = {"training": {k: summary.get(k) for k in
                              ("launch_sha", "counts", "optimizer_steps", "wall_seconds", "peak_rss_kib", "rss_scope")},
                 "evaluation": {c: {k: evaluation_records[(seed, c)].get(k) for k in
                                     ("launch_sha", "counts", "wall_seconds", "peak_rss_kib")}
                                for c in CHECKPOINTS},
                 "modes": {}}
        for mode in MODES:
            initial, endpoint = (panels[(seed, c, mode)] for c in CHECKPOINTS)
            entry["modes"][mode] = {
                "initial": summarise_rows(initial), "endpoint": summarise_rows(endpoint),
                "endpoint_minus_initial": gap_block(endpoint, initial),
                "endpoint_minus_references": {label: gap_block(endpoint, rows)
                                                for label, rows in comparators.items()},
                "per_world_endpoint_minus_initial": {
                    str(world): {key: endpoint[world][key] - initial[world][key] for key in PRIMARY_FIELDS}
                    for world in WORLDS},
            }
        result["seeds"][str(seed)] = entry
    for mode in MODES:
        result["descriptive_seed_spread"][mode] = {}
        for metric in PRIMARY_FIELDS:
            values = [result["seeds"][str(s)]["modes"][mode]["endpoint"][metric] for s in SEEDS]
            result["descriptive_seed_spread"][mode][metric] = {
                "n": 2, "mean": statistics.mean(values), "sd": statistics.stdev(values),
                "min": min(values), "max": max(values),
            }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, nargs=2, required=True)
    parser.add_argument("--evals", type=Path, nargs="+", required=True)
    parser.add_argument("--b01", type=Path, required=True)
    parser.add_argument("--refs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError(args.out)
    result = make_reading(train_dirs=args.train, eval_dirs=args.evals, b01=args.b01, refs=args.refs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
