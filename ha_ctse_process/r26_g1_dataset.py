"""Frozen individual-skill behavior-window dataset utilities for R26-G1a."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


class G1DataError(ValueError):
    """Dataset contract failure with machine-readable audit context."""

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        source: Path | str | None = None,
        rows: list[dict[str, object]] | None = None,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.source = None if source is None else str(source)
        self.rows = [] if rows is None else rows

    def as_dict(self) -> dict[str, object]:
        return {
            "type": type(self).__name__,
            "message": str(self),
            "field": self.field,
            "source": self.source,
            "rows": self.rows,
        }


@dataclass(frozen=True)
class G1WindowBatch:
    label: np.ndarray
    post_action: np.ndarray
    post_effect: np.ndarray
    pre_action: np.ndarray
    pre_effect: np.ndarray
    pre_valid: np.ndarray
    prior_context: np.ndarray
    reset_id: np.ndarray
    reset_seed: np.ndarray
    episode_id: np.ndarray
    env_id: np.ndarray
    agent_id: np.ndarray
    duration_idx: np.ndarray
    segment_length: np.ndarray
    checkpoint_id: np.ndarray
    checkpoint_update: np.ndarray

    def take(self, indices: np.ndarray) -> "G1WindowBatch":
        idx = np.asarray(indices, dtype=np.int64)
        return G1WindowBatch(
            **{field: np.asarray(getattr(self, field))[idx] for field in FIELDS}
        )


@dataclass(frozen=True)
class SplitIndices:
    train: np.ndarray
    validation: np.ndarray
    test: np.ndarray
    train_reset_ids: np.ndarray
    validation_reset_ids: np.ndarray
    test_reset_ids: np.ndarray


FIELDS = tuple(G1WindowBatch.__dataclass_fields__)
FLOAT_FIELDS = (
    "post_action",
    "post_effect",
    "pre_action",
    "pre_effect",
    "pre_valid",
    "prior_context",
)
INT_FIELDS = (
    "label",
    "reset_id",
    "reset_seed",
    "episode_id",
    "env_id",
    "agent_id",
    "duration_idx",
    "segment_length",
    "checkpoint_update",
)


def window_summary(rows: np.ndarray, feature_dim: int) -> np.ndarray:
    matrix = np.asarray(rows, dtype=np.float32).reshape(-1, int(feature_dim))
    if matrix.shape[0] == 0:
        return np.zeros(int(feature_dim) * 4, dtype=np.float32)
    delta = matrix[-1] - matrix[0]
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    span = matrix.max(axis=0) - matrix.min(axis=0)
    return np.concatenate([delta, mean, std, span]).astype(np.float32, copy=False)


def one_hot(index: int, size: int) -> np.ndarray:
    values = np.zeros(max(int(size), 1), dtype=np.float32)
    values[int(np.clip(index, 0, values.size - 1))] = 1.0
    return values


def build_prior_context(
    *,
    focal_agent: int,
    n_agents: int,
    duration_idx: int,
    n_durations: int,
    previous_skill: int,
    n_skills: int,
    previous_age: int,
    team_code: int,
    num_team_codes: int,
    teammate_roster: np.ndarray,
    assignment_obs: np.ndarray,
    omega: np.ndarray,
    pre_action: np.ndarray,
    pre_effect: np.ndarray,
    pre_valid: bool,
) -> np.ndarray:
    roster = np.asarray(teammate_roster, dtype=np.int64).reshape(-1)
    teammate_parts = [
        one_hot(int(skill), n_skills)
        for agent, skill in enumerate(roster)
        if int(agent) != int(focal_agent)
    ]
    parts = [
        one_hot(focal_agent, n_agents),
        one_hot(duration_idx, n_durations),
        one_hot(previous_skill, n_skills),
        np.asarray([float(previous_age)], dtype=np.float32),
        one_hot(team_code, num_team_codes),
        *teammate_parts,
        np.asarray(assignment_obs, dtype=np.float32).reshape(-1),
        np.asarray(omega, dtype=np.float32).reshape(-1),
        np.asarray(pre_action, dtype=np.float32).reshape(-1),
        np.asarray(pre_effect, dtype=np.float32).reshape(-1),
        np.asarray([float(bool(pre_valid))], dtype=np.float32),
    ]
    result = np.concatenate(parts).astype(np.float32, copy=False)
    if not np.isfinite(result).all():
        raise ValueError("prior_context contains non-finite values")
    return result


def _row_identities(
    batch: G1WindowBatch,
    row_indices: np.ndarray,
) -> list[dict[str, object]]:
    identity_fields = (
        "reset_id",
        "reset_seed",
        "episode_id",
        "env_id",
        "agent_id",
        "checkpoint_id",
        "checkpoint_update",
    )
    arrays = {
        field: np.asarray(getattr(batch, field)).reshape(-1) for field in identity_fields
    }
    rows: list[dict[str, object]] = []
    for row_index in np.asarray(row_indices, dtype=np.int64).reshape(-1):
        row: dict[str, object] = {"row_index": int(row_index)}
        for field, values in arrays.items():
            if 0 <= int(row_index) < values.size:
                value = values[int(row_index)]
                row[field] = str(value) if field == "checkpoint_id" else int(value)
        rows.append(row)
    return rows


def _validate(
    batch: G1WindowBatch,
    *,
    source: Path | str | None = None,
) -> G1WindowBatch:
    arrays = {field: np.asarray(getattr(batch, field)) for field in FIELDS}
    label = arrays["label"].reshape(-1)
    n_rows = int(label.shape[0])
    for field, array in arrays.items():
        if array.ndim == 0:
            raise G1DataError(
                f"{field} must have a row dimension", field=field, source=source
            )
        if int(array.shape[0]) != n_rows:
            raise G1DataError(
                f"{field} has {array.shape[0]} rows, expected {n_rows}",
                field=field,
                source=source,
            )

    for field in FLOAT_FIELDS:
        finite = np.isfinite(np.asarray(arrays[field], dtype=np.float32))
        if not finite.all():
            bad_rows = np.unique(np.argwhere(~finite)[:, 0]).astype(np.int64)
            raise G1DataError(
                f"{field} contains non-finite values at rows {bad_rows.tolist()}",
                field=field,
                source=source,
                rows=_row_identities(batch, bad_rows),
            )

    values: dict[str, np.ndarray] = {}
    for field in FIELDS:
        array = arrays[field]
        if field in FLOAT_FIELDS:
            array = np.asarray(array, dtype=np.float32)
        elif field in INT_FIELDS:
            array = np.asarray(array, dtype=np.int64)
        else:
            array = np.asarray(array, dtype=np.str_)
        if field in INT_FIELDS or field in ("pre_valid", "checkpoint_id"):
            array = array.reshape(-1)
        values[field] = array
    return G1WindowBatch(**values)


def write_g1_window_shard(path: Path, batch: G1WindowBatch) -> None:
    output_path = Path(path)
    validated = _validate(batch, source=output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path, **{field: getattr(validated, field) for field in FIELDS}
    )


def read_g1_window_shards(root: Path) -> G1WindowBatch:
    input_root = Path(root)
    paths = sorted(input_root.glob("*.npz"))
    if not paths:
        raise FileNotFoundError(f"no R26-G1a window shards found under {input_root}")

    chunks: dict[str, list[np.ndarray]] = {field: [] for field in FIELDS}
    for path in paths:
        with np.load(path, allow_pickle=False) as data:
            missing = [field for field in FIELDS if field not in data]
            if missing:
                raise G1DataError(f"{path} missing fields: {missing}", source=path)
            shard = _validate(
                G1WindowBatch(**{field: np.asarray(data[field]) for field in FIELDS}),
                source=path,
            )
            for field in FIELDS:
                chunks[field].append(np.asarray(getattr(shard, field)))
    concatenated = {
        field: np.concatenate(chunks[field], axis=0) for field in FIELDS
    }
    return _validate(G1WindowBatch(**concatenated), source=input_root)


def sample_g1_rows(batch: G1WindowBatch, max_rows: int, seed: int) -> G1WindowBatch:
    validated = _validate(batch)
    n_rows = int(validated.label.shape[0])
    if int(max_rows) <= 0 or n_rows <= int(max_rows):
        return validated
    rng = np.random.default_rng(int(seed))
    indices = np.sort(rng.choice(n_rows, size=int(max_rows), replace=False))
    return validated.take(indices)


def grouped_reset_split(batch: G1WindowBatch, seed: int) -> SplitIndices:
    validated = _validate(batch)
    reset_ids = np.unique(validated.reset_id.astype(np.int64))
    if reset_ids.size < 5:
        raise ValueError("at least five reset groups are required")
    shuffled = reset_ids.copy()
    np.random.default_rng(int(seed)).shuffle(shuffled)
    n_test = max(1, int(np.floor(0.2 * shuffled.size)))
    n_valid = max(1, int(np.floor(0.2 * shuffled.size)))
    test_ids = np.sort(shuffled[:n_test])
    valid_ids = np.sort(shuffled[n_test : n_test + n_valid])
    train_ids = np.sort(shuffled[n_test + n_valid :])
    return SplitIndices(
        train=np.flatnonzero(np.isin(validated.reset_id, train_ids)),
        validation=np.flatnonzero(np.isin(validated.reset_id, valid_ids)),
        test=np.flatnonzero(np.isin(validated.reset_id, test_ids)),
        train_reset_ids=train_ids,
        validation_reset_ids=valid_ids,
        test_reset_ids=test_ids,
    )
