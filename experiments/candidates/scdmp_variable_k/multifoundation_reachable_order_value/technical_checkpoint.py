"""Outcome-free full-shape A/RECON checkpoint I/O workload."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable, Mapping

import torch

from .foundation import FoundationActorCritic, materialize_foundation
from .orchestration import (
    AttemptError, _decode_tensor, _read_canonical_json, _tensor_value, atomic_create_json,
)
from .rng import CounterRNG
from .training import ExactAdamW


TECHNICAL_CHECKPOINT_SCHEMA = "SCDMP_MF_RS_MK_B01_A_RECON_CHECKPOINT_SHAPE_V1"


def _source_binding(path: Path) -> dict[str, object]:
    direct = path.read_bytes()
    return {"byte_size": len(direct), "sha256": hashlib.sha256(direct).hexdigest()}


def write_technical_checkpoint_grid(
    root: str | Path,
    *,
    models: Mapping[int, FoundationActorCritic],
    optimizers: Mapping[int, ExactAdamW],
    source_identity_path: str | Path,
    scratch_observer: Callable[[Path], None] | None,
) -> tuple[Path, ...]:
    destination = Path(root)
    source_binding = _source_binding(Path(source_identity_path))
    paths = []
    for seed in (1709, 2903):
        model = models[seed]
        optimizer = optimizers[seed]
        if model.foundation_seed != seed or not optimizer.matches(tuple(model.named_parameters())):
            raise AttemptError("A/RECON technical checkpoint model binding differs")
        base = {
            "schema": TECHNICAL_CHECKPOINT_SCHEMA,
            "source_identity_binding": source_binding,
            "foundation_seed": seed,
            "actual_optimizer_step": optimizer.step_index,
            "parameters": [_tensor_value(name, value) for name, value in model.named_parameters()],
            "optimizer_names": list(optimizer.names),
            "optimizer_first": [
                _tensor_value(name, value) for name, value in zip(optimizer.names, optimizer.first)
            ],
            "optimizer_second": [
                _tensor_value(name, value) for name, value in zip(optimizer.names, optimizer.second)
            ],
            "science_exclusions": ["RUN-01 master", "RUN-01 q", "RUN-01 outcome", "RUN-01 branch"],
        }
        for coordinate in range(161):
            path = destination / str(seed) / f"coordinate-{coordinate:03d}.json"
            atomic_create_json(
                path, {**base, "technical_coordinate": coordinate},
                scratch_observer=scratch_observer,
            )
            paths.append(path)
    return tuple(paths)


def cold_validate_technical_checkpoint_grid(
    paths: tuple[Path, ...], *, source_identity_path: str | Path,
) -> tuple[dict[str, object], ...]:
    expected_paths = tuple(
        path for seed in (1709, 2903) for path in (
            Path(paths[0]).parents[1] / str(seed) / f"coordinate-{coordinate:03d}.json"
            for coordinate in range(161)
        )
    ) if paths else ()
    if len(paths) != 322 or tuple(paths) != expected_paths:
        raise AttemptError("A/RECON technical checkpoint coordinate inventory differs")
    source_binding = _source_binding(Path(source_identity_path))
    inventory = []
    for path in paths:
        value = _read_canonical_json(path)
        seed = int(path.parent.name)
        coordinate = int(path.stem.removeprefix("coordinate-"))
        template = materialize_foundation(CounterRNG(seed))
        optimizer = ExactAdamW(tuple(template.named_parameters()))
        required = {
            "schema", "source_identity_binding", "foundation_seed", "actual_optimizer_step",
            "parameters", "optimizer_names", "optimizer_first", "optimizer_second",
            "science_exclusions", "technical_coordinate",
        }
        if (
            set(value) != required
            or value.get("schema") != TECHNICAL_CHECKPOINT_SCHEMA
            or value.get("source_identity_binding") != source_binding
            or value.get("foundation_seed") != seed
            or value.get("technical_coordinate") != coordinate
            or value.get("optimizer_names") != list(optimizer.names)
        ):
            raise AttemptError("A/RECON technical checkpoint source/coordinate binding differs")
        for key, targets in (
            ("parameters", tuple(template.named_parameters())),
            ("optimizer_first", tuple(zip(optimizer.names, optimizer.first))),
            ("optimizer_second", tuple(zip(optimizer.names, optimizer.second))),
        ):
            rows = value.get(key)
            if not isinstance(rows, list) or len(rows) != len(targets):
                raise AttemptError("A/RECON technical checkpoint tensor inventory differs")
            for row, (name, target) in zip(rows, targets):
                decoded = _decode_tensor(row, expected_name=name, expected_shape=tuple(target.shape))
                if key == "optimizer_second" and bool(torch.any(decoded < 0)):
                    raise AttemptError("A/RECON technical Adam second moment is negative")
        direct_size = path.stat().st_size
        inventory.append({
            "relative_path": path.relative_to(paths[0].parents[1]).as_posix(),
            "direct_size_bytes": direct_size,
        })
    return tuple(inventory)


def inventory_technical_checkpoint_grid(paths: tuple[Path, ...]) -> tuple[dict[str, object], ...]:
    if len(paths) != 322:
        raise AttemptError("A/RECON technical inventory requires 322 files")
    root = paths[0].parents[1]
    rows = []
    for index, path in enumerate(paths):
        seed = 1709 if index < 161 else 2903
        coordinate = index % 161
        expected = root / str(seed) / f"coordinate-{coordinate:03d}.json"
        if path != expected or not path.is_file():
            raise AttemptError("A/RECON technical inventory coordinate differs")
        rows.append({"relative_path": path.relative_to(root).as_posix(),
                     "direct_size_bytes": path.stat().st_size})
    return tuple(rows)


__all__ = [
    "TECHNICAL_CHECKPOINT_SCHEMA", "cold_validate_technical_checkpoint_grid",
    "inventory_technical_checkpoint_grid", "write_technical_checkpoint_grid",
]
