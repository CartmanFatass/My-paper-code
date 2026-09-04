"""Deterministic one-pass fixed-behavior fitted-Q training."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping
import gzip
import json

from .checkpoint import checkpoint_payload, load_checkpoint, save_checkpoint
from .contract import BATCH_SIZE, K_TRAIN, SEED_SLOTS, TEST_ONLY_MODE, as_fraction, contexts, default_manifest
from .model import build_shared_model, displayed_belief, feature_vector, validate_shared_model
from .schema import canonical_bytes
from .support import build_fixed_behavior_plan, materialize_fixed_behavior_plan, validate_support


def _torch():
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("training requires PyTorch") from exc
    return torch


def _optimizer(model):
    torch = _torch()
    return torch.optim.AdamW(model.parameters(), lr=3e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-4)


def _context_lookup() -> dict[str, Mapping[str, Any]]:
    from .contract import context_id

    return {context_id(context): context for context in contexts()}


def _load_seed_rows(preflight_path: Path, seed_slot: str, support: Mapping[str, Any]) -> list[dict[str, Any]]:
    root = preflight_path.parent / "materialized"
    if root.is_symlink() or not root.is_dir():
        raise FileNotFoundError(f"materialized root absent or symlinked: {root}")
    cells: list[list[dict[str, Any]]] = []
    manifest = default_manifest(support["mode"], int(support["episodes_per_context"]))
    context_lookup = _context_lookup()
    for cell_id, context in context_lookup.items():
        cell_rows: list[dict[str, Any]] = []
        logical_key = f"{seed_slot}|{cell_id}"
        path = root / support["materialized_files"][logical_key]["filename"]
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError(f"missing materialized dataset: {path}")
        plan = build_fixed_behavior_plan(seed_slot, context, manifest)
        expected_records = materialize_fixed_behavior_plan(plan, context)
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            for expected, line in zip(expected_records, stream):
                row = json.loads(line)
                if row["seed_slot"] != seed_slot or row["context_id"] != cell_id:
                    raise ValueError("materialized row binding mismatch")
                if int(row["period"]) not in K_TRAIN:
                    raise ValueError("held-out period reached training loader")
                if line.rstrip("\n").encode("utf-8") != canonical_bytes(expected.to_dict()):
                    raise ValueError("materialized row differs from fixed plan/counter tape")
                cell_rows.append(row)
            if len(cell_rows) != len(expected_records) or stream.readline():
                raise ValueError("materialized row-count mismatch")
        cells.append(cell_rows)
    size = len(cells[0])
    if any(len(cell_rows) != size for cell_rows in cells):
        raise ValueError("context datasets differ in size")
    # Fixed uniform-population ordering: 32 episode indices x 8 contexts per batch.
    return [cells[cell_index][episode_index] for episode_index in range(size) for cell_index in range(8)]


def _root_target(model, row: Mapping[str, Any], context: Mapping[str, Any]):
    torch = _torch()
    if row["root_action"] == "IMMEDIATE":
        return float(row["tail_return"])
    belief = displayed_belief(row["link"], as_fraction(row["reliability"]), int(row["displayed_short_count"]))
    tail_features = torch.tensor(
        [feature_vector(context, belief_short=belief, action_is_probe=False, period=k) for k in K_TRAIN],
        dtype=torch.float32,
    )
    with torch.no_grad():
        continuation = model.score_tail(tail_features).max()
    ledger = row["primitive_ledger"]
    primitive_total = float(ledger["probe_service"]) + float(ledger["probe_time"]) + float(ledger["probe_energy"])
    return float(primitive_total + continuation.item())


def train_one_seed(
    seed_slot: str,
    preflight_artifact: str | Path,
    checkpoint_path: str | Path,
    *,
    manifest: str | Path | Mapping[str, Any] | None = None,
    resume_from: str | Path | None = None,
    max_batches: int | None = None,
) -> dict[str, Any]:
    """Train exactly one shared checkpoint; ``max_batches`` is a resume-test bound only."""
    if seed_slot not in SEED_SLOTS:
        raise ValueError("unknown seed slot")
    support = validate_support(preflight_artifact, manifest)
    if support["mode"] != TEST_ONLY_MODE:
        raise ValueError("public train_one_seed is TEST_ONLY; use run-belief for PRODUCTION")
    return _train_one_seed_from_validated_support(
        seed_slot,
        preflight_artifact,
        checkpoint_path,
        support_record=support,
        resume_from=resume_from,
        max_batches=max_batches,
    )


def _train_one_seed_from_validated_support(
    seed_slot: str,
    preflight_artifact: str | Path,
    checkpoint_path: str | Path,
    *,
    support_record: Mapping[str, Any],
    rows: list[dict[str, Any]] | None = None,
    resume_from: str | Path | None = None,
    max_batches: int | None = None,
) -> dict[str, Any]:
    """Train from the production orchestrator's once-validated on-disk support."""
    if seed_slot not in SEED_SLOTS:
        raise ValueError("unknown seed slot")
    if not isinstance(support_record, Mapping):
        raise ValueError("validated support record must be a mapping")
    support = dict(support_record)
    destination = Path(checkpoint_path)
    if resume_from is None and destination.exists():
        raise FileExistsError("fresh training refuses an existing checkpoint path")
    if resume_from is not None and Path(resume_from).resolve() != destination.resolve():
        raise ValueError("resume must continue the same single checkpoint path")
    if max_batches is not None:
        if type(max_batches) is not int or max_batches < 0:
            raise ValueError("max_batches must be a nonnegative integer, not bool/coercible text")
        if support["mode"] != "TEST_ONLY":
            raise ValueError("bounded interruption is TEST_ONLY; production is exactly one complete pass")
    torch = _torch()
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)
    model = build_shared_model(seed_slot)
    validate_shared_model(model)
    optimizer = _optimizer(model)
    completed_batches = optimizer_updates = 0
    if resume_from is not None:
        restored = load_checkpoint(resume_from, model, optimizer)
        if (
            restored["seed_slot"] != seed_slot
            or restored["support_record"] != support
            or restored["mode"] != support["mode"] or restored["contract_spec"] != support["contract_spec"]
        ):
            raise ValueError("resume checkpoint binding mismatch")
        completed_batches = restored["completed_batches"]
        optimizer_updates = restored["optimizer_updates"]
    if rows is None:
        rows = _load_seed_rows(Path(preflight_artifact), seed_slot, support)
    total_batches = (len(rows) + BATCH_SIZE - 1) // BATCH_SIZE
    if completed_batches > total_batches:
        raise ValueError("resume cursor exceeds deterministic one-pass batch count")
    if resume_from is not None and restored["total_batches"] != total_batches:
        raise ValueError("resume total-batch structure mismatch")
    if completed_batches == total_batches and resume_from is not None:
        raise ValueError("complete checkpoint cannot be retrained or resaved")
    stop_batch = total_batches if max_batches is None else min(total_batches, completed_batches + int(max_batches))
    context_lookup = _context_lookup()
    model.train()
    payload = None
    for batch_index in range(completed_batches, stop_batch):
        batch = rows[batch_index * BATCH_SIZE : (batch_index + 1) * BATCH_SIZE]
        root_features = []
        root_targets = []
        tail_features = []
        tail_targets = []
        for row in batch:
            context = context_lookup[row["context_id"]]
            if row["root_action"] == "PROBE":
                root_features.append(feature_vector(context, belief_short=Fraction(1, 2), action_is_probe=True, period=0))
                belief = displayed_belief(row["link"], as_fraction(row["reliability"]), int(row["displayed_short_count"]))
                tail_features.append(feature_vector(context, belief_short=belief, action_is_probe=False, period=int(row["period"])))
                tail_targets.append(float(row["tail_return"]))
            elif row["root_action"] == "IMMEDIATE":
                root_features.append(feature_vector(context, belief_short=Fraction(1, 2), action_is_probe=False, period=int(row["period"])))
            else:
                raise ValueError("unknown root action in training row")
            root_targets.append(_root_target(model, row, context))
        optimizer.zero_grad(set_to_none=True)
        root_prediction = model.score_root(torch.tensor(root_features, dtype=torch.float32))
        loss = torch.nn.functional.mse_loss(root_prediction, torch.tensor(root_targets, dtype=torch.float32))
        if tail_features:
            tail_prediction = model.score_tail(torch.tensor(tail_features, dtype=torch.float32))
            loss = loss + torch.nn.functional.mse_loss(tail_prediction, torch.tensor(tail_targets, dtype=torch.float32))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        optimizer_updates += 1
        completed_batches = batch_index + 1
        payload = checkpoint_payload(
            model,
            optimizer,
            seed_slot=seed_slot,
            completed_batches=completed_batches,
            optimizer_updates=optimizer_updates,
            total_batches=total_batches,
            mode=support["mode"],
            contract_spec=support["contract_spec"],
            support_record=support,
        )
        save_checkpoint(checkpoint_path, payload)
    if payload is None:
        payload = checkpoint_payload(
            model,
            optimizer,
            seed_slot=seed_slot,
            completed_batches=completed_batches,
            optimizer_updates=optimizer_updates,
            total_batches=total_batches,
            mode=support["mode"],
            contract_spec=support["contract_spec"],
            support_record=support,
        )
        save_checkpoint(checkpoint_path, payload)
    return {
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_record": {key: payload[key] for key in payload if key not in ("model_state","optimizer_state")},
        "completed_batches": completed_batches,
        "optimizer_updates": optimizer_updates,
        "complete_pass": completed_batches == total_batches,
    }
