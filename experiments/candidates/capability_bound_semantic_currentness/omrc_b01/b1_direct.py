"""INCOMPLETE_NOT_RUN: direct publication candidate retained for scope review.

This is an offline subset, not an accepted runner. It has no learner invocation,
checkpoint replay, complete audit/exposure projection, or resource publication.
No r05 calculation or runtime validation has been performed on this candidate.
"""

import json
import time
from pathlib import Path

from .b1_descriptive import compute_b1_descriptive_curves
from .b1_metrics_rehydrate import rehydrate_b1_metrics
from .b1_metrics_training_assembly import (
    _merge_training_group,
    reconstruct_raw_competence_from_tables,
)
from .b1_policy_records import (
    build_complete_policy_curves,
    build_literal_null_manifest_fields,
    build_policy_support_signature_counts,
)


def publish_offline_subset(input_root: Path, output_root: Path, launch_sha: str):
    """Inspectably wire existing quantities; output is incomplete engineering data."""
    started = time.perf_counter()
    groups = []
    for slot in sorted((input_root / "workers").iterdir()):
        groups.append([
            json.loads(path.read_text(encoding="utf-8"))["raw_evidence"]
            for path in sorted(slot.glob("slice-*/result.json"))
        ])
    replay = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((input_root / "policy-replay").glob("*/result.json"))
    ]
    # The original input identity is passed through; no hash is reconstructed.
    shared = rehydrate_b1_metrics(
        groups, attempt_id=groups[0][0]["attempt_id"],
        literal_binding_spec_sha256=replay[0]["literal_binding_spec_sha256"],
    ).canonical_shared_tables
    tables = {name: shared[name] for name in (
        "tape_transitions", "evaluator_decision_truth", "motif_twin_index",
        "support_signature_counts", "motif_pair_support_counts",
    )}
    tables["policy_decisions"] = [
        row for packet in replay for row in packet["policy_decisions"]
    ]
    tables["per_tape_curves"] = build_complete_policy_curves(tables["policy_decisions"])
    tables["policy_support_signature_counts"] = build_policy_support_signature_counts(
        tables["policy_decisions"], tables["evaluator_decision_truth"],
    )
    merged = [
        _merge_training_group(group, (group[0]["seed"], group[0]["arm"]), test_only=False)
        for group in groups
    ]
    for name in ("training_decisions", "training_episodes", "optimizer_steps"):
        tables[name] = [row for records in merged for row in getattr(records, name)]
    tables["raw_competence"] = reconstruct_raw_competence_from_tables(tables, test_only=False)
    descriptive = compute_b1_descriptive_curves(
        per_tape_curves=tables["per_tape_curves"], policy_decisions=tables["policy_decisions"],
        training_episodes=tables["training_episodes"], optimizer_steps=tables["optimizer_steps"],
        raw_competence=tables["raw_competence"],
    )
    output_root.mkdir(parents=True)
    for name, rows in tables.items():
        with (output_root / f"{name}.jsonl").open("w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, allow_nan=False) + "\n")
    summary = {
        "status": "INCOMPLETE_NOT_RUN", "evidence_role": "ENGINEERING_ONLY",
        "launch_sha": launch_sha, "input_root": str(input_root),
        "input_attempt_id": groups[0][0]["attempt_id"],
        "literal_binding_spec_sha256": replay[0]["literal_binding_spec_sha256"],
        "descriptive": descriptive, **build_literal_null_manifest_fields(),
        "resources_status": "resources_unmeasured", "peak_rss_bytes": None,
        "scratch_high_water_bytes": None, "durable_high_water_bytes": None,
        "wall_seconds": time.perf_counter() - started,
        "missing_tables": ["resource_admissions", "telemetry", "audits"],
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, allow_nan=False, indent=2) + "\n", encoding="utf-8",
    )
    return summary
