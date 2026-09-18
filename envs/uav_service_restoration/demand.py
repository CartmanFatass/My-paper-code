"""Demand sources for ``uav_service_restoration_v0``.

Two implementations, kept explicitly distinct:

``SyntheticFixtureDemandSource``
    A fully self-contained analytic activity field.  ``metadata().is_real_activity_data``
    is ``False`` and ``kind`` is ``"synthetic_fixture"``.  It is never selected as a
    fallback: a real-data configuration that cannot find its dataset raises.

``PreparedDatasetDemandSource``
    A read-only, memory-mapped reader over the prepared cache written by
    :mod:`envs.uav_service_restoration.preprocess_milan`.  ``kind`` comes from the
    cache's own ``metadata.json`` (``"milan_activity"`` for real Milan activity), and
    ``is_real_activity_data`` likewise: this reader will not label a synthetic cache real.

Activity is mapped to a simulated demand rate by

    d_i(t) = alpha * a_i(t) / s_train

with ``alpha = demand_scale_mbps`` (a declared simulation load scale, not measured Mbps)
and ``s_train`` a single reference scale fitted on the training split only.  There is no
per-time-slice renormalisation, so a genuine surge in total load survives the mapping.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .config import SourceConfig, SyntheticFixtureConfig
from .types import DemandFrame, DemandMetadata, EpisodeDescriptor

PREPARED_SCHEMA_VERSION = "uav_service_restoration_v0.prepared_dataset.1"
COMPLETION_MARKER = "_PREPARED_COMPLETE.json"

_REQUIRED_ARRAYS = (
    "timestamps_utc_ms.npy",
    "cell_ids.npy",
    "positions_m.npy",
    "activity.npy",
    "observed_mask.npy",
)


class DemandDataError(RuntimeError):
    """A demand source could not be opened, or its contents failed validation.

    Raised instead of falling back to synthetic data.
    """


class EpisodeSamplingError(RuntimeError):
    """No episode window satisfying the configured requirements exists in this split."""


# --------------------------------------------------------------------------------------
# Shared mapping helpers
# --------------------------------------------------------------------------------------


def reference_scale_from_training(
    activity: np.ndarray,
    observed_mask: np.ndarray,
    quantile: float = 0.95,
) -> float:
    """``s_train``: a fixed quantile of strictly positive observed training activity.

    Zeros are excluded so that a mostly-idle region does not collapse the scale.  The
    rule is fixed here and saved into metadata; it never sees validation or test data.
    """

    values = np.asarray(activity, dtype=np.float64)
    mask = np.asarray(observed_mask, dtype=bool)
    positive = values[mask & (values > 0.0)]
    if positive.size == 0:
        raise DemandDataError(
            "cannot fit a demand reference scale: the training split has no positive "
            "observed activity"
        )
    scale = float(np.quantile(positive, float(quantile)))
    if not math.isfinite(scale) or scale <= 0.0:
        raise DemandDataError(f"fitted reference scale is not usable: {scale!r}")
    return scale


def map_activity_to_demand_mbps(
    activity: np.ndarray, demand_scale_mbps: float, reference_scale: float
) -> np.ndarray:
    """``d = alpha * a / s_train``, elementwise, in float64."""

    if reference_scale <= 0.0:
        raise DemandDataError("reference_scale must be positive")
    return (
        np.asarray(activity, dtype=np.float64)
        * float(demand_scale_mbps)
        / float(reference_scale)
    )


def _sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------------------
# Synthetic fixture
# --------------------------------------------------------------------------------------


class SyntheticFixtureDemandSource:
    """Explicitly non-real analytic activity, reproducible from configuration alone."""

    kind = "synthetic_fixture"

    def __init__(self, source: SourceConfig, origin_m: tuple[float, float] = (0.0, 0.0)) -> None:
        if source.kind != "synthetic_fixture":
            raise DemandDataError(
                f"SyntheticFixtureDemandSource requires source.kind 'synthetic_fixture'; "
                f"got {source.kind!r}"
            )
        self._source = source
        fixture: SyntheticFixtureConfig = source.synthetic_fixture
        self._fixture = fixture
        rows, cols = fixture.grid_shape
        self._n_cells = rows * cols

        xs = origin_m[0] + fixture.origin_offset_m[0] + fixture.cell_spacing_m * np.arange(cols)
        ys = origin_m[1] + fixture.origin_offset_m[1] + fixture.cell_spacing_m * np.arange(rows)
        grid_x, grid_y = np.meshgrid(xs, ys, indexing="xy")
        # Row-major (y outer, x inner) fixed ordering; cell identity never re-sorts.
        self._positions_m = np.stack(
            [grid_y.reshape(-1) * 0.0 + grid_x.reshape(-1), grid_y.reshape(-1)], axis=1
        ).astype(np.float64)
        self._cell_ids = np.arange(self._n_cells, dtype=np.int64)

        self._interval_ms = int(round(fixture.interval_duration_s * 1000.0))
        self._timestamps = fixture.start_utc_ms + self._interval_ms * np.arange(
            fixture.n_intervals, dtype=np.int64
        )
        self._activity = self._build_activity()
        self._observed = np.ones((fixture.n_intervals, self._n_cells), dtype=bool)
        for cell in fixture.unobserved_cells:
            self._observed[:, int(cell)] = False
        for interval in fixture.unobserved_intervals:
            self._observed[int(interval), :] = False

        # The reference scale is fitted on the first half of the trace, which is the
        # fixture's declared training portion.
        self._train_intervals = max(1, fixture.n_intervals // 2)
        if source.reference_scale_override is not None:
            self._reference_scale = float(source.reference_scale_override)
        else:
            self._reference_scale = reference_scale_from_training(
                self._activity[: self._train_intervals],
                self._observed[: self._train_intervals],
            )
        self._dataset_hash = self._compute_hash()

    # -- construction ------------------------------------------------------------------

    def _build_activity(self) -> np.ndarray:
        fixture = self._fixture
        rows, cols = fixture.grid_shape
        n_intervals = fixture.n_intervals
        phase = 2.0 * np.pi * np.arange(n_intervals, dtype=np.float64) / float(n_intervals)
        diurnal = fixture.base_activity + fixture.diurnal_amplitude * np.sin(phase)
        # A fixed, smooth spatial weight: no RNG, so the fixture is byte-reproducible.
        row_index, col_index = np.meshgrid(
            np.arange(rows, dtype=np.float64), np.arange(cols, dtype=np.float64), indexing="ij"
        )
        spatial = 0.6 + 0.4 * np.cos(
            np.pi * row_index / max(rows - 1, 1)
        ) * np.cos(np.pi * col_index / max(cols - 1, 1))
        spatial = spatial.reshape(-1)
        activity = diurnal[:, None] * spatial[None, :]

        hotspot_row, hotspot_col = fixture.hotspot_cell
        hotspot_index = hotspot_row * cols + hotspot_col
        window = slice(fixture.hotspot_start_interval, fixture.hotspot_end_interval)
        activity[window, hotspot_index] *= float(fixture.hotspot_gain)
        return np.ascontiguousarray(activity, dtype=np.float64)

    def _compute_hash(self) -> str:
        digest = hashlib.sha256()
        digest.update(PREPARED_SCHEMA_VERSION.encode("ascii"))
        digest.update(b"synthetic_fixture")
        digest.update(np.ascontiguousarray(self._timestamps).tobytes())
        digest.update(np.ascontiguousarray(self._activity).tobytes())
        digest.update(np.ascontiguousarray(self._observed).tobytes())
        digest.update(np.ascontiguousarray(self._positions_m).tobytes())
        return digest.hexdigest()

    # -- DemandSource interface ---------------------------------------------------------

    def metadata(self) -> DemandMetadata:
        return DemandMetadata(
            kind=self.kind,
            schema_version=PREPARED_SCHEMA_VERSION,
            is_real_activity_data=False,
            description=(
                "Self-contained analytic activity fixture. NOT real data: no Telecom "
                "Italia record, no measured traffic, no population count."
            ),
            dataset_hash=self._dataset_hash,
            source_url=None,
            license_note="Authored for this repository; no external data licence applies.",
            activity_field="synthetic_analytic",
            demand_scale_mbps=float(self._source.demand_scale_mbps),
            activity_reference_scale=float(self._reference_scale),
            interval_duration_s=float(self._fixture.interval_duration_s),
            extra={
                "grid_shape": list(self._fixture.grid_shape),
                "train_intervals": int(self._train_intervals),
                "reference_scale_rule": "quantile(positive training activity, 0.95)",
            },
        )

    def cell_positions_m(self) -> np.ndarray:
        return self._positions_m.copy()

    def cell_ids(self) -> np.ndarray:
        return self._cell_ids.copy()

    def n_cells(self) -> int:
        return int(self._n_cells)

    def reference_scale(self) -> float:
        return float(self._reference_scale)

    def split_interval_range(self, split: str) -> tuple[int, int]:
        """Half-open interval index range of a split.

        The fixture splits by position in its own trace: the first half is ``train``, the
        second half is ``validation``/``test``.  The reference scale is fitted on the
        training half only.
        """

        fixture = self._fixture
        if split == "train":
            return 0, self._train_intervals
        if split in ("validation", "test"):
            return self._train_intervals, fixture.n_intervals
        raise EpisodeSamplingError(
            f"unknown split {split!r}; expected train, validation or test"
        )

    def sample_episode(
        self,
        split: str,
        rng: np.random.Generator,
        *,
        duration_s: float | None = None,
        history_intervals: int = 1,
        require_fully_observed: bool | None = None,
    ) -> EpisodeDescriptor:
        first, last = self.split_interval_range(split)
        duration_ms = (
            int(round(float(duration_s) * 1000.0))
            if duration_s is not None
            else self._interval_ms
        )
        needed = max(1, int(math.ceil(duration_ms / self._interval_ms)))
        history = max(0, int(history_intervals))
        require = (
            self._source.require_fully_observed_episodes
            if require_fully_observed is None
            else bool(require_fully_observed)
        )
        # History may reach back before the split boundary only for the training split,
        # which begins the trace; otherwise the window plus its history stays inside the
        # split so validation and test episodes never read training intervals and vice
        # versa.
        earliest_start = first + history if first > 0 else first
        latest_start = last - needed
        candidates: list[int] = []
        for start in range(max(earliest_start, history), latest_start + 1):
            window = slice(start - history, start + needed)
            if require and not bool(self._observed[window].all()):
                continue
            candidates.append(int(start))
        if not candidates:
            raise EpisodeSamplingError(
                f"fixture split {split!r} has no window of {needed} intervals with "
                f"{history} intervals of history"
                + (" that is fully observed" if require else "")
            )
        choice = int(candidates[int(rng.integers(0, len(candidates)))])
        start_ms = int(self._timestamps[choice])
        history_ms = int(self._timestamps[choice - history]) if history else start_ms
        return EpisodeDescriptor(
            episode_id=f"fixture-{split}-{choice}",
            split=split,
            region_id=self._source.region_id,
            start_utc_ms=start_ms,
            end_utc_ms=start_ms + needed * self._interval_ms,
            history_start_utc_ms=history_ms,
            dataset_hash=self._dataset_hash,
        )

    def read_interval(
        self, episode: EpisodeDescriptor, timestamp_utc_ms: int
    ) -> DemandFrame:
        if episode.dataset_hash != self._dataset_hash:
            raise DemandDataError(
                "episode descriptor was produced against a different dataset content hash"
            )
        timestamp = int(timestamp_utc_ms)
        if not episode.contains(timestamp):
            raise DemandDataError(
                f"timestamp {timestamp} is outside episode "
                f"[{episode.history_start_utc_ms}, {episode.end_utc_ms})"
            )
        index = int((timestamp - int(self._timestamps[0])) // self._interval_ms)
        if not 0 <= index < self._timestamps.shape[0]:
            raise DemandDataError(
                f"timestamp {timestamp} falls outside the fixture trace; no wrap-around "
                "is performed"
            )
        interval_start = int(self._timestamps[index])
        activity = self._activity[index].copy()
        observed = self._observed[index].copy()
        demand = map_activity_to_demand_mbps(
            activity, self._source.demand_scale_mbps, self._reference_scale
        )
        demand = np.where(observed, demand, 0.0)
        return DemandFrame(
            interval_start_utc_ms=interval_start,
            interval_end_utc_ms=interval_start + self._interval_ms,
            cell_ids=self._cell_ids.copy(),
            activity=activity,
            demand_mbps=demand,
            observed_mask=observed,
        )


# --------------------------------------------------------------------------------------
# Prepared read-only dataset (the Milan route)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _PreparedArrays:
    timestamps_utc_ms: np.ndarray
    cell_ids: np.ndarray
    positions_m: np.ndarray
    activity: np.ndarray
    observed_mask: np.ndarray


class PreparedDatasetDemandSource:
    """Read-only reader over a prepared activity cache.

    The arrays are memory-mapped: ``reset``/``step`` never re-parse raw files.  The
    cache's declared SHA-256 hashes are verified on open, so a same-named file from a
    different dataset version cannot be silently substituted.
    """

    def __init__(
        self,
        source: SourceConfig,
        *,
        dataset_root: str | Path | None = None,
        verify_hashes: bool = True,
    ) -> None:
        if source.kind not in ("milan_activity", "prepared_dataset"):
            raise DemandDataError(
                "PreparedDatasetDemandSource requires source.kind 'milan_activity' or "
                f"'prepared_dataset'; got {source.kind!r}"
            )
        root_value = dataset_root if dataset_root is not None else source.dataset_root
        if not root_value:
            raise DemandDataError(
                "a real-data configuration requires an explicit dataset_root; there is "
                "no synthetic fallback"
            )
        root = Path(root_value)
        if not root.is_dir():
            raise DemandDataError(
                f"dataset_root does not exist: {root}. Run "
                "scripts/uav_service_restoration/prepare_milan.py first; a fixture is "
                "not a substitute."
            )
        self._root = root
        self._source = source
        self._metadata_payload = self._load_metadata(root)
        if verify_hashes:
            self._verify_file_hashes()
        self._arrays = self._open_arrays(root)
        self._splits = self._load_splits(root)
        self._validate_consistency()

        declared_kind = str(self._metadata_payload.get("kind", ""))
        if source.kind == "milan_activity" and declared_kind != "milan_activity":
            raise DemandDataError(
                "source.kind is 'milan_activity' but the prepared cache declares "
                f"kind={declared_kind!r}; synthetic data is never presented as real"
            )
        self._kind = declared_kind or source.kind
        self._is_real = bool(self._metadata_payload.get("is_real_activity_data", False))
        if source.kind == "milan_activity" and not self._is_real:
            raise DemandDataError(
                "source.kind is 'milan_activity' but the prepared cache is not marked as "
                "real activity data"
            )

        self._interval_ms = int(self._metadata_payload["interval_duration_ms"])
        self._dataset_hash = str(self._metadata_payload["content_sha256"])
        if source.reference_scale_override is not None:
            self._reference_scale = float(source.reference_scale_override)
        else:
            self._reference_scale = float(self._metadata_payload["activity_reference_scale"])
        if self._reference_scale <= 0.0:
            raise DemandDataError("prepared cache declares a non-positive reference scale")

    # -- opening -----------------------------------------------------------------------

    @staticmethod
    def _load_metadata(root: Path) -> dict[str, Any]:
        marker = root / COMPLETION_MARKER
        if not marker.is_file():
            raise DemandDataError(
                f"{root} has no {COMPLETION_MARKER}: the cache is incomplete or still "
                "being written"
            )
        path = root / "metadata.json"
        if not path.is_file():
            raise DemandDataError(f"{root} has no metadata.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != PREPARED_SCHEMA_VERSION:
            raise DemandDataError(
                f"prepared cache schema_version {payload.get('schema_version')!r} does not "
                f"match reader version {PREPARED_SCHEMA_VERSION!r}"
            )
        required = (
            "kind",
            "is_real_activity_data",
            "interval_duration_ms",
            "content_sha256",
            "activity_reference_scale",
            "activity_field",
            "file_sha256",
            "crs",
            "region_selection_rule",
            "missing_data_policy",
            "aggregation_rule",
        )
        missing = [key for key in required if key not in payload]
        if missing:
            raise DemandDataError(f"metadata.json is missing required keys: {missing}")
        return payload

    def _verify_file_hashes(self) -> None:
        declared = self._metadata_payload.get("file_sha256", {})
        if not isinstance(declared, dict) or not declared:
            raise DemandDataError("metadata.json file_sha256 must be a non-empty object")
        for name in _REQUIRED_ARRAYS:
            if name not in declared:
                raise DemandDataError(f"metadata.json file_sha256 is missing {name!r}")
        for name, want in sorted(declared.items()):
            path = self._root / name
            if not path.is_file():
                raise DemandDataError(f"prepared cache is missing declared file {name!r}")
            got = _sha256_of_file(path)
            if got != want:
                raise DemandDataError(
                    f"prepared cache file {name!r} hash mismatch: declared {want}, found "
                    f"{got}. The cache was modified or a different version was substituted."
                )

    @staticmethod
    def _open_arrays(root: Path) -> _PreparedArrays:
        def _load(name: str) -> np.ndarray:
            path = root / name
            if not path.is_file():
                raise DemandDataError(f"prepared cache is missing {name}")
            return np.load(path, mmap_mode="r", allow_pickle=False)

        return _PreparedArrays(
            timestamps_utc_ms=_load("timestamps_utc_ms.npy"),
            cell_ids=_load("cell_ids.npy"),
            positions_m=_load("positions_m.npy"),
            activity=_load("activity.npy"),
            observed_mask=_load("observed_mask.npy"),
        )

    @staticmethod
    def _load_splits(root: Path) -> dict[str, list[str]]:
        path = root / "splits.json"
        if not path.is_file():
            raise DemandDataError(f"prepared cache is missing splits.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        splits = payload.get("splits")
        if not isinstance(splits, dict) or not splits:
            raise DemandDataError("splits.json must contain a non-empty 'splits' object")
        seen: dict[str, str] = {}
        for split, dates in splits.items():
            if not isinstance(dates, list):
                raise DemandDataError(f"splits.json split {split!r} must map to a list of dates")
            for date in dates:
                if date in seen:
                    raise DemandDataError(
                        f"splits.json date {date!r} appears in both {seen[date]!r} and "
                        f"{split!r}; splits must not overlap"
                    )
                seen[str(date)] = split
        return {str(split): [str(date) for date in dates] for split, dates in splits.items()}

    def _validate_consistency(self) -> None:
        arrays = self._arrays
        if arrays.timestamps_utc_ms.dtype != np.int64:
            raise DemandDataError("timestamps_utc_ms.npy must be int64")
        if arrays.observed_mask.dtype != np.bool_:
            raise DemandDataError("observed_mask.npy must be bool")
        n_intervals = int(arrays.timestamps_utc_ms.shape[0])
        n_cells = int(arrays.cell_ids.shape[0])
        if arrays.activity.shape != (n_intervals, n_cells):
            raise DemandDataError(
                f"activity.npy shape {arrays.activity.shape} does not match "
                f"({n_intervals}, {n_cells})"
            )
        if arrays.observed_mask.shape != (n_intervals, n_cells):
            raise DemandDataError("observed_mask.npy shape does not match activity.npy")
        if arrays.positions_m.shape != (n_cells, 2):
            raise DemandDataError(
                f"positions_m.npy shape {arrays.positions_m.shape} does not match ({n_cells}, 2)"
            )
        if n_intervals < 2:
            raise DemandDataError("prepared cache must contain at least two intervals")
        diffs = np.diff(np.asarray(arrays.timestamps_utc_ms))
        if diffs.size and (diffs <= 0).any():
            raise DemandDataError("timestamps_utc_ms.npy must be strictly increasing")

    # -- DemandSource interface ---------------------------------------------------------

    def metadata(self) -> DemandMetadata:
        payload = self._metadata_payload
        return DemandMetadata(
            kind=self._kind,
            schema_version=PREPARED_SCHEMA_VERSION,
            is_real_activity_data=self._is_real,
            description=str(payload.get("description", "")),
            dataset_hash=self._dataset_hash,
            source_url=payload.get("source_url"),
            license_note=payload.get("license_note"),
            activity_field=str(payload.get("activity_field")),
            demand_scale_mbps=float(self._source.demand_scale_mbps),
            activity_reference_scale=float(self._reference_scale),
            interval_duration_s=float(self._interval_ms) / 1000.0,
            extra={
                "dataset_root": str(self._root),
                "crs": payload.get("crs"),
                "region_selection_rule": payload.get("region_selection_rule"),
                "missing_data_policy": payload.get("missing_data_policy"),
                "aggregation_rule": payload.get("aggregation_rule"),
                "reference_scale_rule": payload.get("reference_scale_rule"),
                "splits": dict(self._splits),
            },
        )

    def cell_positions_m(self) -> np.ndarray:
        return np.asarray(self._arrays.positions_m, dtype=np.float64).copy()

    def cell_ids(self) -> np.ndarray:
        return np.asarray(self._arrays.cell_ids, dtype=np.int64).copy()

    def n_cells(self) -> int:
        return int(self._arrays.cell_ids.shape[0])

    def reference_scale(self) -> float:
        return float(self._reference_scale)

    def quality_report(self) -> dict[str, Any]:
        path = self._root / "quality_report.json"
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def split_interval_indices(self, split: str) -> np.ndarray:
        """Indices of source intervals whose UTC date belongs to ``split``."""

        if split not in self._splits:
            raise EpisodeSamplingError(
                f"unknown split {split!r}; the cache declares {sorted(self._splits)}"
            )
        dates = set(self._splits[split])
        timestamps = np.asarray(self._arrays.timestamps_utc_ms, dtype=np.int64)
        # Integer-only UTC date derivation; the machine's local timezone never enters.
        days = timestamps // 86_400_000
        date_labels = _utc_day_labels(days)
        mask = np.array([label in dates for label in date_labels], dtype=bool)
        return np.flatnonzero(mask)

    def sample_episode(
        self,
        split: str,
        rng: np.random.Generator,
        *,
        duration_s: float | None = None,
        history_intervals: int = 1,
        require_fully_observed: bool | None = None,
    ) -> EpisodeDescriptor:
        indices = self.split_interval_indices(split)
        if indices.size == 0:
            raise EpisodeSamplingError(f"split {split!r} selects no interval in this cache")
        duration_ms = (
            int(round(float(duration_s) * 1000.0))
            if duration_s is not None
            else self._interval_ms
        )
        needed = max(1, int(math.ceil(duration_ms / self._interval_ms)))
        history = max(0, int(history_intervals))
        require = (
            self._source.require_fully_observed_episodes
            if require_fully_observed is None
            else bool(require_fully_observed)
        )

        # Contiguous runs inside the split, so an episode never spans a split boundary.
        runs = _contiguous_runs(indices)
        candidates: list[int] = []
        for run in runs:
            first_start = run[0] + history
            last_start = run[-1] - needed + 1
            for start in range(first_start, last_start + 1):
                window = slice(start - history, start + needed)
                if require and not bool(np.asarray(self._arrays.observed_mask[window]).all()):
                    continue
                candidates.append(int(start))
        if not candidates:
            raise EpisodeSamplingError(
                f"split {split!r} has no window of {needed} intervals with {history} "
                f"intervals of history"
                + (" that is fully observed" if require else "")
                + "; formal evaluation episodes with unresolved missing data are refused"
            )
        choice = int(candidates[int(rng.integers(0, len(candidates)))])
        start_ms = int(self._arrays.timestamps_utc_ms[choice])
        history_ms = int(self._arrays.timestamps_utc_ms[choice - history]) if history else start_ms
        return EpisodeDescriptor(
            episode_id=f"{split}-{start_ms}",
            split=split,
            region_id=self._source.region_id,
            start_utc_ms=start_ms,
            end_utc_ms=start_ms + needed * self._interval_ms,
            history_start_utc_ms=history_ms,
            dataset_hash=self._dataset_hash,
        )

    def read_interval(
        self, episode: EpisodeDescriptor, timestamp_utc_ms: int
    ) -> DemandFrame:
        if episode.dataset_hash != self._dataset_hash:
            raise DemandDataError(
                "episode descriptor was produced against a different dataset content hash"
            )
        timestamp = int(timestamp_utc_ms)
        if not episode.contains(timestamp):
            raise DemandDataError(
                f"timestamp {timestamp} is outside episode "
                f"[{episode.history_start_utc_ms}, {episode.end_utc_ms})"
            )
        timestamps = np.asarray(self._arrays.timestamps_utc_ms, dtype=np.int64)
        index = int(np.searchsorted(timestamps, timestamp, side="right")) - 1
        if index < 0 or index >= timestamps.shape[0]:
            raise DemandDataError(
                f"timestamp {timestamp} is outside the prepared trace; no wrap-around is "
                "performed"
            )
        interval_start = int(timestamps[index])
        if timestamp >= interval_start + self._interval_ms:
            raise DemandDataError(
                f"timestamp {timestamp} falls in a gap between prepared intervals"
            )
        activity = np.asarray(self._arrays.activity[index], dtype=np.float64).copy()
        observed = np.asarray(self._arrays.observed_mask[index], dtype=bool).copy()
        demand = map_activity_to_demand_mbps(
            activity, self._source.demand_scale_mbps, self._reference_scale
        )
        demand = np.where(observed, demand, 0.0)
        return DemandFrame(
            interval_start_utc_ms=interval_start,
            interval_end_utc_ms=interval_start + self._interval_ms,
            cell_ids=self.cell_ids(),
            activity=activity,
            demand_mbps=demand,
            observed_mask=observed,
        )


def _utc_day_labels(days: np.ndarray) -> list[str]:
    """``YYYY-MM-DD`` labels from integer days since the UTC epoch."""

    return [
        np.datetime64(int(day), "D").astype("datetime64[D]").astype(str)
        for day in np.asarray(days, dtype=np.int64)
    ]


def _contiguous_runs(indices: np.ndarray) -> list[list[int]]:
    values = np.asarray(indices, dtype=np.int64)
    if values.size == 0:
        return []
    breaks = np.flatnonzero(np.diff(values) != 1) + 1
    return [list(map(int, chunk)) for chunk in np.split(values, breaks) if chunk.size]


# --------------------------------------------------------------------------------------
# Factory
# --------------------------------------------------------------------------------------


def build_demand_source(
    source: SourceConfig,
    *,
    dataset_root: str | Path | None = None,
    origin_m: tuple[float, float] = (0.0, 0.0),
) -> Any:
    """Construct the demand source named by ``source.kind``.

    A real-data kind whose dataset is missing raises :class:`DemandDataError`.  It never
    degrades to the fixture.
    """

    if source.kind == "synthetic_fixture":
        return SyntheticFixtureDemandSource(source, origin_m=origin_m)
    if source.kind in ("milan_activity", "prepared_dataset"):
        return PreparedDatasetDemandSource(source, dataset_root=dataset_root)
    raise DemandDataError(f"unsupported source kind {source.kind!r}")
