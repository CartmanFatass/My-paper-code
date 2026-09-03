"""Create-once publication and strict A/RECON result firewall."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import json
import os
import tempfile

from .checkpoint import expected_policy_activity, validate_checkpoint_inventory
from .contract import ARM_IDS, CONTEXTS, OBJECT_ID, SCHEMA_VERSION, RunBinding, ScoutConfig, context_id, expected_activity_totals, expected_parameter_counts, expected_work
from .evaluation import PolicyEvaluation, validate_policy_evaluation
from .gates import apply_gates

ASSESS_FORMAT = "UCOPE_SCOUT_R01_A_RECON_ASSESS_V1"
SCIENTIFIC_FORMAT = "UCOPE_SCOUT_R01_COMPLETE_RESULT_V1"
INCOMPLETE_FORMAT = "UCOPE_SCOUT_R01_INCOMPLETE_ATTEMPT_V1"
ASSESS_TOP_LEVEL = {
    "format", "schema_version", "mode", "config", "work", "activity", "stage_times",
    "source_refs", "runtime_refs", "run_binding",
}
FORBIDDEN_ASSESS_KEYS = (
    "score", "return", "regret", "agreement", "competence", "acquisition", "polarity",
    "root_vector", "root_actions", "selected", "oracle", "gate", "branch", "count_raw",
)
FORBIDDEN_SOURCE_REFS = (
    "contextual_paid_acquisition_r01", "structural_competence",
    "ucope-contextual-paid-acquisition-r01-production", "ucope-structural-competence",
)
ACTIVITY_FIELDS = {
    "environment_episodes", "environment_transitions", "root_rows", "tail_rows",
    "root_optimizer_updates", "tail_optimizer_updates", "root_example_exposures",
    "tail_example_exposures", "target_refresh_events", "target_refresh_rows",
    "target_materialization_events", "target_materialization_rows", "root_clipping_events",
    "tail_clipping_events", "root_gradient_norm_sum", "tail_gradient_norm_sum",
    "root_gradient_norm_max", "tail_gradient_norm_max", "nonfinite_events",
    "exact_policy_evaluations", "sampled_evaluation_episodes", "parameter_count",
    "sampled_evaluation_transitions",
    "checkpoint_writes", "policies_completed", "per_policy",
}
ASSESS_ACTIVITY_FIELDS = {
    "environment_episodes", "environment_transitions", "root_rows", "tail_rows",
    "root_optimizer_updates", "tail_optimizer_updates", "root_example_exposures",
    "tail_example_exposures", "target_refresh_events", "target_refresh_rows",
    "target_materialization_events", "target_materialization_rows", "nonfinite_events",
    "exact_policy_evaluations", "sampled_evaluation_episodes", "parameter_count",
    "checkpoint_writes", "policies_completed", "per_policy",
}
ASSESS_POLICY_ACTIVITY_FIELDS = (ASSESS_ACTIVITY_FIELDS - {
    "environment_episodes", "environment_transitions", "root_rows", "tail_rows", "parameter_count",
    "checkpoint_writes", "policies_completed", "per_policy",
}) | {"root_inventory", "tail_inventory"}
POLICY_ACTIVITY_FIELDS = ASSESS_POLICY_ACTIVITY_FIELDS | {
    "root_clipping_events", "tail_clipping_events", "root_gradient_norm_sum", "tail_gradient_norm_sum",
    "root_gradient_norm_max", "tail_gradient_norm_max", "sampled_evaluation_transitions",
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"artifact value is not JSON serializable: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def atomic_create_json(path: str | Path, value: Mapping[str, Any]) -> Path:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"artifact is create-once: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(canonical_json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return destination


def publish_incomplete(path: str | Path, *, config: ScoutConfig, run_binding: RunBinding | Mapping[str, Any], reason: str, activity: Mapping[str, Any]) -> Path:
    if not reason:
        raise ValueError("incomplete attempt requires a direct reason")
    value = {
        "format": INCOMPLETE_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "object_id": OBJECT_ID,
        "complete": False,
        "config": config.to_dict(),
        "run_binding": RunBinding.from_value(run_binding, config.mode).to_dict(),
        "reason": reason,
        "activity": dict(activity),
    }
    return atomic_create_json(path, value)


def validate_scientific_artifact(value: Mapping[str, Any], *, artifact_root: str | Path | None = None) -> dict[str, Any]:
    required = {
        "format", "schema_version", "object_id", "complete", "config", "work", "activity",
        "stage_times", "source_refs", "runtime_refs", "run_binding", "checkpoints", "internal_result",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise ValueError("scientific artifact field inventory mismatch")
    config = ScoutConfig.from_dict(value["config"])
    run_binding = RunBinding.from_value(value["run_binding"], config.mode)
    if config.mode not in {"B1", "LADDER1"} or value["format"] != SCIENTIFIC_FORMAT or value["schema_version"] != SCHEMA_VERSION or value["object_id"] != OBJECT_ID or value["complete"] is not True:
        raise ValueError("complete B1 artifact identity mismatch")
    if not isinstance(value["internal_result"], Mapping) or set(value["internal_result"]) != {"support_limited", "support_histograms", "gates", "evaluations"}:
        raise ValueError("complete B1 artifact lacks gate/evaluation evidence")
    validate_checkpoint_inventory(value["checkpoints"], config=config, artifact_root=artifact_root, run_binding=run_binding)
    if not isinstance(value["source_refs"], list) or any(type(path) is not str or any(token in path.lower() for token in FORBIDDEN_SOURCE_REFS) for path in value["source_refs"]):
        raise ValueError("complete B1 artifact source/consumed path fence violated")
    expected_activity = expected_activity_totals(config)
    if value["work"] != expected_work(config):
        raise ValueError("complete B1 work ledger mismatch")
    if not isinstance(value["activity"], Mapping) or set(value["activity"]) != ACTIVITY_FIELDS or any(value["activity"].get(field) != expected for field, expected in expected_activity.items()):
        raise ValueError("complete B1 artifact activity mismatch")
    if value["activity"]["parameter_count"] != expected_parameter_counts():
        raise ValueError("complete B1 parameter-count mismatch")
    _validate_complete_policy_activity(value["activity"], config)
    support_limited = _validate_support_histograms(value["internal_result"], config)
    try:
        evaluations = tuple(PolicyEvaluation(**item) for item in value["internal_result"]["evaluations"])
    except (TypeError, ValueError) as exc:
        raise ValueError("complete B1 evaluation structure mismatch") from exc
    expected_combinations = {(arm, seed, fold, update) for arm in config.arms for seed in config.seed_ids for fold in (0, 1) for update in config.evaluation_root_updates}
    keyed = {(item.arm_id, item.seed_id, item.fold_id, item.root_update): item for item in evaluations}
    if len(evaluations) != len(expected_combinations) or set(keyed) != expected_combinations:
        raise ValueError("complete B1 evaluation inventory mismatch")
    for item in evaluations:
        eligible = bool(
            item.root_update == config.root_updates and not support_limited[item.seed_id]
            and all(keyed[(item.arm_id, item.seed_id, fold, config.root_updates)].competence_pass for fold in (0, 1))
        )
        validate_policy_evaluation(item, config=config, acquisition_eligible=eligible)
    recomputed = apply_gates(
        evaluations,
        seed_ids=config.seed_ids,
        final_root_update=config.root_updates,
        support_limited=support_limited,
        arms=config.arms,
    )
    if value["internal_result"]["gates"] != recomputed:
        raise ValueError("complete B1 gate evidence mismatch")
    return dict(value)


def _validate_support_histograms(internal: Mapping[str, Any], config: ScoutConfig) -> dict[str, bool]:
    limited = internal["support_limited"]
    histograms = internal["support_histograms"]
    cells = {context_id(context) for context in CONTEXTS}
    if not isinstance(limited, Mapping) or set(limited) != set(config.seed_ids) or any(type(value) is not bool for value in limited.values()):
        raise ValueError("support-limited seed ledger mismatch")
    if not isinstance(histograms, Mapping) or set(histograms) != set(config.seed_ids):
        raise ValueError("support histogram seed inventory mismatch")
    for seed in config.seed_ids:
        if set(histograms[seed]) != cells:
            raise ValueError("support histogram context inventory mismatch")
        missing = False
        for cell in cells:
            if set(histograms[seed][cell]) != {"fold-0", "fold-1"}:
                raise ValueError("support histogram fold inventory mismatch")
            for fold in ("fold-0", "fold-1"):
                counts = histograms[seed][cell][fold]
                if not isinstance(counts, list) or len(counts) != 7 or any(type(count) is not int or count < 0 for count in counts) or sum(counts) != config.episodes_per_context // 4:
                    raise ValueError("support histogram count ledger mismatch")
                missing |= any(count == 0 for count in counts)
        if limited[seed] != missing:
            raise ValueError("support-limited flag/histogram mismatch")
    return dict(limited)


def _validate_complete_policy_activity(activity: Mapping[str, Any], config: ScoutConfig) -> None:
    expected_keys = {f"{arm}|{seed}|fold-{fold}" for arm in config.arms for seed in config.seed_ids for fold in (0, 1)}
    per_policy = activity["per_policy"]
    if not isinstance(per_policy, Mapping) or set(per_policy) != expected_keys:
        raise ValueError("per-policy activity inventory mismatch")
    for arm in config.arms:
        for seed in config.seed_ids:
            for fold in (0, 1):
                row = per_policy[f"{arm}|{seed}|fold-{fold}"]
                expected = expected_policy_activity(config, arm, fold, config.root_updates, config.tail_updates)
                if not isinstance(row, Mapping) or set(row) != POLICY_ACTIVITY_FIELDS or any(row.get(field) != item for field, item in expected.items()):
                    raise ValueError("per-policy exact activity mismatch")
                if type(row.get("sampled_evaluation_transitions")) is not int or row["sampled_evaluation_transitions"] <= 0:
                    raise ValueError("per-policy sampled transition ledger mismatch")
                for prefix, updates in (("root", config.root_updates), ("tail", config.tail_updates)):
                    clipping = row.get(f"{prefix}_clipping_events")
                    norm_sum = row.get(f"{prefix}_gradient_norm_sum")
                    norm_max = row.get(f"{prefix}_gradient_norm_max")
                    if type(clipping) is not int or not 0 <= clipping <= updates or not isinstance(norm_sum, (int, float)) or not isinstance(norm_max, (int, float)) or not 0 <= norm_max <= norm_sum:
                        raise ValueError("per-policy gradient/clipping ledger mismatch")
    summed_fields = (
        "root_optimizer_updates", "tail_optimizer_updates", "root_example_exposures", "tail_example_exposures",
        "target_refresh_events", "target_refresh_rows", "target_materialization_events", "target_materialization_rows",
        "root_clipping_events", "tail_clipping_events", "root_gradient_norm_sum", "tail_gradient_norm_sum",
        "nonfinite_events", "exact_policy_evaluations", "sampled_evaluation_episodes", "sampled_evaluation_transitions",
    )
    if any(activity[field] != sum(row[field] for row in per_policy.values()) for field in summed_fields):
        raise ValueError("global/per-policy activity reconciliation mismatch")
    if activity["root_gradient_norm_max"] != max(row["root_gradient_norm_max"] for row in per_policy.values()) or activity["tail_gradient_norm_max"] != max(row["tail_gradient_norm_max"] for row in per_policy.values()):
        raise ValueError("global gradient maximum reconciliation mismatch")


def build_scientific_artifact(result: Any, *, checkpoint_inventory, artifact_root: str | Path | None = None) -> dict[str, Any]:
    config = result.config if isinstance(result.config, ScoutConfig) else ScoutConfig.from_dict(result.config)
    if config.mode not in {"B1", "LADDER1"}:
        raise ValueError("scientific artifact builder accepts only B1 or LADDER1")
    value = {
        "format": SCIENTIFIC_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "object_id": OBJECT_ID,
        "complete": True,
        "config": config.to_dict(),
        "run_binding": result.run_binding.to_dict(),
        "work": dict(result.work),
        "activity": dict(result.activity),
        "stage_times": list(result.stage_times),
        "source_refs": list(result.source_refs),
        "runtime_refs": dict(result.runtime_refs),
        "checkpoints": list(checkpoint_inventory),
        "internal_result": dict(result.internal_result),
    }
    return validate_scientific_artifact(value, artifact_root=artifact_root)


def publish_complete(path: str | Path, value: Mapping[str, Any], *, artifact_root: str | Path | None = None) -> Path:
    destination = Path(path)
    root = destination.parent if artifact_root is None else Path(artifact_root)
    return atomic_create_json(destination, validate_scientific_artifact(value, artifact_root=root))


def validate_complete_tree(value: Mapping[str, Any], *, complete_root: str | Path, run_manifest: Mapping[str, Any] | str | Path | None = None) -> dict[str, Any]:
    root = Path(complete_root)
    validated = validate_scientific_artifact(value, artifact_root=root)
    if run_manifest is None:
        manifest_path = root / "run-manifest.json"
        if not manifest_path.is_file():
            raise ValueError("complete tree lacks the bound run manifest")
        with manifest_path.open("r", encoding="utf-8") as stream:
            manifest = json.load(stream)
    elif isinstance(run_manifest, Mapping):
        manifest = dict(run_manifest)
    else:
        with Path(run_manifest).open("r", encoding="utf-8") as stream:
            manifest = json.load(stream)
    if not isinstance(manifest, Mapping) or manifest.get("object_id") != OBJECT_ID or manifest.get("config") != validated["config"] or manifest.get("run_binding") != validated["run_binding"]:
        raise ValueError("complete artifact/checkpoint/runner-manifest binding mismatch")
    return validated


def publish_assess(path: str | Path, result: Any) -> Path:
    return atomic_create_json(path, sanitize_assess_result(result))


def sanitize_assess_result(result: Any) -> dict[str, Any]:
    """Project an internal workload result onto the only legal A/RECON surface."""
    config = result.config if isinstance(result.config, ScoutConfig) else ScoutConfig.from_dict(result.config)
    if config.mode != "ASSESS":
        raise ValueError("A/RECON sanitizer accepts only ScoutConfig.assess()")
    activity = {key: item for key, item in result.activity.items() if key in ASSESS_ACTIVITY_FIELDS}
    activity["per_policy"] = {
        policy: {key: item for key, item in row.items() if key in ASSESS_POLICY_ACTIVITY_FIELDS}
        for policy, row in result.activity["per_policy"].items()
    }
    value = {
        "format": ASSESS_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "mode": "A/RECON",
        "config": config.to_dict(),
        "run_binding": result.run_binding.to_dict(),
        "work": dict(result.work),
        "activity": activity,
        "stage_times": list(result.stage_times),
        "source_refs": list(result.source_refs),
        "runtime_refs": dict(result.runtime_refs),
    }
    return validate_assess_artifact(value)


def _reject_science_keys(value: Any, *, path: str = "") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in FORBIDDEN_ASSESS_KEYS):
                raise ValueError(f"scientific field forbidden from A/RECON artifact: {path}{key}")
            _reject_science_keys(item, path=f"{path}{key}.")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_science_keys(item, path=f"{path}{index}.")


def validate_assess_artifact(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != ASSESS_TOP_LEVEL:
        raise ValueError("A/RECON artifact top-level whitelist mismatch")
    if value["format"] != ASSESS_FORMAT or value["schema_version"] != SCHEMA_VERSION or value["mode"] != "A/RECON":
        raise ValueError("A/RECON artifact identity mismatch")
    config = ScoutConfig.from_dict(value["config"])
    RunBinding.from_value(value["run_binding"], config.mode)
    if config.mode != "ASSESS":
        raise ValueError("A/RECON artifact must bind the reduced assess configuration")
    if not isinstance(value["work"], Mapping) or not isinstance(value["activity"], Mapping) or set(value["activity"]) != ASSESS_ACTIVITY_FIELDS:
        raise ValueError("A/RECON work/activity whitelist mismatch")
    per_policy = value["activity"].get("per_policy", {})
    if not isinstance(per_policy, Mapping):
        raise ValueError("per-policy activity must be a mapping")
    for activity in per_policy.values():
        if not isinstance(activity, Mapping) or set(activity) != ASSESS_POLICY_ACTIVITY_FIELDS:
            raise ValueError("per-policy activity whitelist mismatch")
    if not isinstance(value["stage_times"], list) or any(not isinstance(item, Mapping) or set(item) - {"stage", "arm_id", "seed_id", "fold_id", "wall_seconds", "cpu_seconds", "resumed_root_updates", "root_updates", "tail_updates"} for item in value["stage_times"]):
        raise ValueError("A/RECON stage-time whitelist mismatch")
    if not isinstance(value["source_refs"], list) or any(type(item) is not str for item in value["source_refs"]):
        raise ValueError("A/RECON source refs must be strings")
    if any(any(token in item.lower() for token in FORBIDDEN_SOURCE_REFS) for item in value["source_refs"]):
        raise ValueError("A/RECON source/consumed path fence violated")
    if not isinstance(value["runtime_refs"], Mapping):
        raise ValueError("A/RECON runtime refs must be a mapping")
    # Config is a frozen input and may name the competence-first object. Everything observed is
    # checked separately so no scientific response can hide under performance/activity fields.
    for field in ("work", "activity", "stage_times", "runtime_refs"):
        _reject_science_keys(value[field], path=f"{field}.")
    canonical_json_bytes(value)
    return dict(value)
