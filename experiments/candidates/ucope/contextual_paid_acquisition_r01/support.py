"""Immutable fixed-behavior materialization and support-only preflight."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Mapping
import gzip
import json
import os
import shutil
import tempfile

from .contract import (
    CONTRACT_ID,
    DISPLAYED_COUNT_FLOOR,
    EPISODES_PER_CONTEXT,
    K_TRAIN,
    PROBE_EPISODES,
    PRODUCTION_MODE,
    ROOT_ACTION_FLOOR,
    SCHEMA_VERSION,
    SEED_SLOTS,
    TEST_ONLY_MODE,
    context_id,
    contexts,
    default_manifest,
    load_manifest,
    validate_contract,
)
from .host import EpisodeRecord, simulate_episode, validate_episode_record
from .rng import balanced_binary_assignments
from .schema import FixedBehaviorPlan, PlanEntry, SupportCertificate, canonical_bytes


class SupportError(ValueError):
    pass


def _plan_entries(size: int) -> tuple[PlanEntry, ...]:
    entries = []
    for index in range(size):
        slot = index % 10
        if slot < 5:
            entries.append(PlanEntry(index=index, root_action="PROBE", period=K_TRAIN[slot]))
        else:
            entries.append(PlanEntry(index=index, root_action="IMMEDIATE", period=K_TRAIN[slot - 5]))
    return tuple(entries)


def build_fixed_behavior_plan(
    seed_slot: str,
    context: Mapping[str, Any],
    manifest: str | Path | Mapping[str, Any] | None = None,
) -> FixedBehaviorPlan:
    value = validate_contract(manifest)
    if seed_slot not in SEED_SLOTS:
        raise SupportError("unknown seed slot")
    cell_id = context_id(context)
    if cell_id not in value["context_ids"]:
        raise SupportError("context outside frozen population")
    entries = _plan_entries(int(value["episodes_per_context"]))
    return FixedBehaviorPlan(CONTRACT_ID, seed_slot, cell_id, value["mode"], entries)


build_plan = build_fixed_behavior_plan


def materialize_fixed_behavior_plan(
    plan: FixedBehaviorPlan,
    context: Mapping[str, Any],
) -> tuple[EpisodeRecord, ...]:
    if plan.seed_slot not in SEED_SLOTS or plan.mode not in (PRODUCTION_MODE,TEST_ONLY_MODE):
        raise SupportError("plan seed/mode outside frozen structure")
    validate_contract(default_manifest(plan.mode,len(plan.entries)))
    if plan.contract_id != CONTRACT_ID or plan.context_id != context_id(context) or plan.entries != _plan_entries(len(plan.entries)):
        raise SupportError("plan/context binding mismatch")
    entries_by_slot = {slot: [entry for entry in plan.entries if entry.index % 10 == slot] for slot in range(10)}
    regime_by_index: dict[int, str] = {}
    display_by_index: dict[int, str] = {}
    for slot, entries in entries_by_slot.items():
        assignments = balanced_binary_assignments(len(entries), "regime-rank", plan.seed_slot, slot)
        for entry, is_short in zip(entries, assignments):
            regime_by_index[entry.index] = "SHORT" if is_short else "LONG"
        if context["link"] == "SEVERED":
            for actual_regime in ("SHORT", "LONG"):
                subgroup = [entry for entry in entries if regime_by_index[entry.index] == actual_regime]
                displays = balanced_binary_assignments(
                    len(subgroup), "display-regime-rank", plan.seed_slot, slot, actual_regime
                )
                for entry, is_short in zip(subgroup, displays):
                    display_by_index[entry.index] = "SHORT" if is_short else "LONG"
    return tuple(
        validate_episode_record(simulate_episode(
            plan.seed_slot,
            context,
            entry,
            regime_by_index[entry.index],
            display_by_index.get(entry.index),
        ))
        for entry in plan.entries
    )


materialize_plan = materialize_fixed_behavior_plan


def _support_counts(records: Iterable[EpisodeRecord]) -> dict[str, Any]:
    records = tuple(records)
    root = Counter(record.root_action if record.root_action == "PROBE" else f"IMMEDIATE:{record.period}" for record in records)
    tail = Counter(record.period for record in records if record.root_action == "PROBE")
    regimes = Counter(record.regime for record in records)
    displayed = Counter(record.displayed_short_count for record in records if record.root_action == "PROBE")
    stratified_regimes: dict[str, dict[str, int]] = {}
    severed_joint: dict[str, dict[str, int]] = {}
    for root_action in ("PROBE", "IMMEDIATE"):
        for period in K_TRAIN:
            stratum = f"{root_action}:{period}"
            selected = [record for record in records if record.root_action == root_action and record.period == period]
            if selected:
                stratified_regimes[stratum] = dict(sorted(Counter(record.regime for record in selected).items()))
                severed_joint[stratum] = dict(
                    sorted(Counter(f"{record.regime}|{record.displayed_regime}" for record in selected).items())
                )
    return {
        "episodes": len(records),
        "root": dict(sorted(root.items(), key=lambda item: str(item[0]))),
        "tail_conditional_probe": {str(k): tail[k] for k in K_TRAIN},
        "regimes": dict(sorted(regimes.items())),
        "displayed_short_count": {str(count): displayed[count] for count in range(7)},
        "action_stratified_regimes": stratified_regimes,
        "actual_display_joint": severed_joint,
    }


def _validate_counts(counts: Mapping[str, Any], mode: str) -> None:
    if type(counts["episodes"]) is not int or counts["episodes"] <= 0:
        raise SupportError("episode count must be a positive integer")
    size = counts["episodes"]
    unit = size // 10
    expected_root_keys = {"PROBE", *(f"IMMEDIATE:{period}" for period in K_TRAIN)}
    expected_period_keys = {str(period) for period in K_TRAIN}
    expected_strata = {f"{action}:{period}" for action in ("PROBE", "IMMEDIATE") for period in K_TRAIN}
    if not isinstance(counts["root"], dict) or set(counts["root"]) != expected_root_keys:
        raise SupportError("root support key inventory mismatch")
    if not isinstance(counts["tail_conditional_probe"], dict) or set(counts["tail_conditional_probe"]) != expected_period_keys:
        raise SupportError("tail support key inventory mismatch")
    if not isinstance(counts["regimes"], dict) or set(counts["regimes"]) != {"SHORT", "LONG"}:
        raise SupportError("regime support key inventory mismatch")
    if not isinstance(counts["displayed_short_count"], dict) or set(counts["displayed_short_count"]) != {str(count) for count in range(7)}:
        raise SupportError("displayed-count key inventory mismatch")
    if not isinstance(counts["action_stratified_regimes"], dict) or set(counts["action_stratified_regimes"]) != expected_strata:
        raise SupportError("action-stratified regime inventory mismatch")
    if not isinstance(counts["actual_display_joint"], dict) or set(counts["actual_display_joint"]) != expected_strata:
        raise SupportError("actual/display joint inventory mismatch")
    nested_integer_maps = (counts["root"], counts["tail_conditional_probe"], counts["regimes"], counts["displayed_short_count"])
    if any(type(value) is not int or value < 0 for mapping in nested_integer_maps for value in mapping.values()):
        raise SupportError("support counts must be nonnegative integers")
    for mapping in (*counts["action_stratified_regimes"].values(), *counts["actual_display_joint"].values()):
        if not isinstance(mapping, dict) or any(type(value) is not int or value < 0 for value in mapping.values()):
            raise SupportError("nested support counts must be nonnegative integers")
    if counts["root"].get("PROBE") != 5 * unit:
        raise SupportError("root PROBE count drift")
    for period in K_TRAIN:
        if counts["root"].get(f"IMMEDIATE:{period}") != unit:
            raise SupportError(f"immediate support drift for k={period}")
        if counts["tail_conditional_probe"].get(str(period)) != unit:
            raise SupportError(f"conditional tail support drift for k={period}")
    if counts["regimes"] != {"LONG": size // 2, "SHORT": size // 2}:
        raise SupportError("regime balance drift")
    for stratum, balance in counts["action_stratified_regimes"].items():
        if balance != {"LONG": unit // 2, "SHORT": unit // 2}:
            raise SupportError(f"action-stratified regime balance drift: {stratum}")
    floor = DISPLAYED_COUNT_FLOOR if mode == PRODUCTION_MODE else 1
    if any(int(counts["displayed_short_count"][str(count)]) < floor for count in range(7)):
        raise SupportError("displayed-count floor not met")
    if mode == PRODUCTION_MODE and (size != EPISODES_PER_CONTEXT or unit != ROOT_ACTION_FLOOR):
        raise SupportError("production support size drift")


def validate_support(
    artifact: str | Path | Mapping[str, Any] | SupportCertificate,
    manifest: str | Path | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(artifact, SupportCertificate):
        value = asdict(artifact)
        value["seed_slots"]=list(value["seed_slots"]); value["context_ids"]=list(value["context_ids"])
    elif isinstance(artifact, Mapping):
        value = dict(artifact)
    else:
        with Path(artifact).open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    required = {
        "schema_version", "contract_id", "mode", "episodes_per_context", "seed_slots", "context_ids",
        "materialized_files", "contract_spec", "seed_context_counts", "complete", "optimizer_updates",
    }
    if set(value) != required:
        raise SupportError(f"support key inventory mismatch: {sorted(set(value) ^ required)}")
    if type(value["schema_version"]) is not int or value["schema_version"] != SCHEMA_VERSION or type(value["contract_id"]) is not str or value["contract_id"] != CONTRACT_ID:
        raise SupportError("support contract structure mismatch")
    if type(value["complete"]) is not bool or not value["complete"] or type(value["optimizer_updates"]) is not int or value["optimizer_updates"] != 0:
        raise SupportError("support artifact is partial or contains optimizer updates")
    reconstructed_manifest = {
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "mode": value["mode"],
        "seed_slots": value["seed_slots"],
        "episodes_per_context": value["episodes_per_context"],
        "context_ids": value["context_ids"],
        "contract_spec": value["contract_spec"],
    }
    manifest_value = validate_contract(manifest) if manifest is not None else validate_contract(reconstructed_manifest)
    if reconstructed_manifest != manifest_value: raise SupportError("manifest structure mismatch")
    expected_keys = {f"{seed}|{cell}" for seed in SEED_SLOTS for cell in manifest_value["context_ids"]}
    if not isinstance(value["seed_context_counts"], dict) or set(value["seed_context_counts"]) != expected_keys:
        raise SupportError("seed/context population incomplete")
    if not isinstance(value["materialized_files"], dict) or set(value["materialized_files"]) != expected_keys:
        raise SupportError("materialized file inventory incomplete")
    for logical_key, counts in value["seed_context_counts"].items():
        if not isinstance(counts, dict) or set(counts) != {"episodes", "root", "tail_conditional_probe", "regimes", "displayed_short_count", "action_stratified_regimes", "actual_display_joint"}:
            raise SupportError("support counter schema mismatch")
        _validate_counts(counts, value["mode"])
        unit = value["episodes_per_context"] // 10
        severed = "|SEVERED-" in logical_key
        for joint in counts["actual_display_joint"].values():
            expected_joint = (
                {"LONG|LONG": unit // 4, "LONG|SHORT": unit // 4, "SHORT|LONG": unit // 4, "SHORT|SHORT": unit // 4}
                if severed else {"LONG|LONG": unit // 2, "SHORT|SHORT": unit // 2}
            )
            if joint != expected_joint:
                raise SupportError("actual/display regime joint balance drift")
    if not isinstance(artifact, (Mapping, SupportCertificate)):
        artifact_path = Path(artifact)
        materialized_root = artifact_path.parent / "materialized"
        if materialized_root.is_symlink() or not materialized_root.is_dir():
            raise SupportError("materialized root absent or symlinked")
        observed_files = set()
        regenerated_counts = {}
        context_lookup = {context_id(context): context for context in contexts()}
        for seed_slot in SEED_SLOTS:
          for cell_id in manifest_value["context_ids"]:
            logical_key = f"{seed_slot}|{cell_id}"
            file_record = value["materialized_files"][logical_key]
            if not isinstance(file_record, dict) or set(file_record) != {"filename", "rows"}:
                raise SupportError("materialized file record schema mismatch")
            filename = file_record["filename"]
            if type(filename) is not str or Path(filename).name != filename or not filename.endswith(".jsonl.gz"):
                raise SupportError("unsafe materialized filename")
            path = materialized_root / filename
            if path.is_symlink() or not path.is_file() or path in observed_files or path.parent.resolve() != materialized_root.resolve():
                raise SupportError("materialized file absent or duplicated")
            observed_files.add(path)
            context = context_lookup[cell_id]
            plan = build_fixed_behavior_plan(seed_slot, context, manifest_value)
            expected_records = materialize_fixed_behavior_plan(plan, context)
            observed_records = []
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                for expected_record, line in zip(expected_records, stream):
                    expected_row = canonical_bytes(expected_record.to_dict())
                    if line.rstrip("\n").encode("utf-8") != expected_row:
                        raise SupportError("materialized row differs from fixed plan/counter tape")
                    observed_records.append(expected_record)
                if stream.readline():
                    raise SupportError("materialized file has extra rows")
            rows = len(observed_records)
            if type(file_record["rows"]) is not int or file_record["rows"] != rows or rows != value["episodes_per_context"]:
                raise SupportError("materialized row-count mismatch")
            regenerated_counts[logical_key] = _support_counts(observed_records)
        actual_entries = set(materialized_root.iterdir())
        if actual_entries != observed_files:
            raise SupportError("missing or extra materialized entries")
        if regenerated_counts != value["seed_context_counts"]:
            raise SupportError("regenerated support counters mismatch")
    return value


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(canonical_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def preflight_support(
    manifest: str | Path | Mapping[str, Any],
    output_root: str | Path,
) -> Path:
    """Materialize all data, validate it, then atomically publish one support certificate.

    The output is support-only: no learner is constructed and no oracle values or conclusions are
    serialized. Existing output roots are never appended to or resampled.
    """
    manifest_value = validate_contract(manifest)
    root = Path(output_root)
    if root.exists():
        raise FileExistsError(f"output root must not already exist: {root}")
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{root.name}.staging-", dir=root.parent))
    artifact_path = staging / "support-preflight.json"
    data_root = staging / "materialized"
    data_root.mkdir()
    support_counts: dict[str, Any] = {}
    materialized_files: dict[str, Any] = {}
    try:
        for seed_slot in SEED_SLOTS:
            for context in contexts():
                plan = build_fixed_behavior_plan(seed_slot, context, manifest_value)
                records = materialize_fixed_behavior_plan(plan, context)
                counts = _support_counts(records)
                _validate_counts(counts, manifest_value["mode"])
                key = f"{seed_slot}|{plan.context_id}"
                support_counts[key] = counts
                filename = f"cell-{SEED_SLOTS.index(seed_slot):02d}-{manifest_value['context_ids'].index(plan.context_id):02d}.jsonl.gz"
                path = data_root / filename
                with path.open("wb") as raw:
                    with gzip.GzipFile(filename="", mode="wb", compresslevel=6, fileobj=raw, mtime=0) as stream:
                        for record in records:
                            record_value = record.to_dict()
                            tape_value = {
                                "index": record.index,
                                "regime": record.regime,
                                "actual_marks": record.actual_marks,
                                "displayed_regime": record.displayed_regime,
                                "displayed_marks": record.displayed_marks,
                            }
                            row = canonical_bytes(record_value) + b"\n"
                            stream.write(row)
                materialized_files[key] = {"filename": filename, "rows": len(records)}
        body = {
            "schema_version": SCHEMA_VERSION,
            "contract_id": CONTRACT_ID,
            "mode": manifest_value["mode"],
            "episodes_per_context": manifest_value["episodes_per_context"],
            "seed_slots": list(SEED_SLOTS),
            "context_ids": manifest_value["context_ids"],
            "contract_spec": manifest_value["contract_spec"],
            "materialized_files": materialized_files,
            "seed_context_counts": support_counts,
            "complete": True,
            "optimizer_updates": 0,
        }
        _atomic_json(artifact_path, body)
        validate_support(artifact_path, manifest_value)
        os.replace(staging, root)
        return root / "support-preflight.json"
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
