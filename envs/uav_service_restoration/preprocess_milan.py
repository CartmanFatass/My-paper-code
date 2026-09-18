"""Explicit preprocessing of Telecom Italia Milan activity into a read-only cache.

This module is never imported by :mod:`envs.uav_service_restoration` and is never called
from ``reset``/``step``.  It is a one-off ingestion step run from
``scripts/uav_service_restoration/prepare_milan.py``.

What the raw data is
--------------------
Aggregated *activity* per ``(square_id, time_interval, country_code)``, not GPS traces,
not user counts and not bytes.  Time bins are 10 minutes and the raw time field is a
millisecond UTC timestamp.  v0 uses the **Internet activity column only**; SMS and call
activity are never added to it, because their sum has no defensible interpretation as
bandwidth. [S1, S2]

The column mapping is version specific and is declared in the preprocessing
configuration, not inferred.  Verify it against the documentation and an actual sample of
the version you downloaded before trusting a run.

Aggregation rule
----------------
Country code is a *dimension of the same spatial cell*, not a separate location.  Rows are
summed over country code for each ``(square_id, time_interval)``.  A record is never
counted twice: input files are de-duplicated by content SHA-256, and a repeated
``(square_id, time_interval, country_code)`` key is rejected unless the configuration
declares an auditable duplicate rule.

Missingness
-----------
Four situations are recorded separately and never conflated:

``explicit_zero``      the field is present and equal to zero;
``empty_field``        the field is present but empty;
``missing_row``        the ``(cell, interval)`` pair has no row at all;
``missing_interval``   an entire expected 10-minute interval has no data.

By default a missing value stays *unknown* (``observed_mask=False``).  ``zero_fill`` is
available but must be turned on deliberately and is recorded in the metadata, because
treating absence as zero demand is a claim about the source, not a convenience.

Geography
---------
The grid geometry is read from the Milano Grid GeoJSON and projected to UTM with the
closed-form transverse Mercator series (WGS84).  Latitude and longitude are never
multiplied by a constant, and the grid is never stretched to match any legacy
``area_size``.  The projection, its origin, the region boundary and the cell-id ordering
are all saved.

Output
------
A new directory containing ``metadata.json``, ``splits.json``,
``quality_report.json``, the five ``.npy`` arrays and an atomic completion marker.  An
existing directory is never overwritten.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence
from zoneinfo import ZoneInfo

import numpy as np

from .config import ConfigError, strict_from_mapping
from .demand import COMPLETION_MARKER, PREPARED_SCHEMA_VERSION, reference_scale_from_training

_ROME = ZoneInfo("Europe/Rome")

# WGS84 / UTM constants.
_WGS84_A = 6378137.0
_WGS84_F = 1.0 / 298.257223563
_WGS84_E2 = _WGS84_F * (2.0 - _WGS84_F)
_UTM_K0 = 0.9996
_UTM_FALSE_EASTING = 500000.0

#: Milan lies in UTM zone 32N.  The zone is configured, never guessed at runtime.
DEFAULT_UTM_ZONE = 32

DEFAULT_SOURCE_URL = "https://doi.org/10.1038/sdata.2015.55"
DEFAULT_LICENSE_NOTE = (
    "Data licence is the publisher's and is NOT granted by this repository. Record the "
    "licence of the exact version you downloaded. Code licence and data licence are "
    "separate."
)


class PreprocessError(RuntimeError):
    """Raw data failed validation, or the requested output already exists."""


# --------------------------------------------------------------------------------------
# Projection
# --------------------------------------------------------------------------------------


def utm_zone_central_meridian_deg(zone: int) -> float:
    """Central meridian of a UTM zone, in degrees."""

    return -180.0 + 6.0 * (int(zone) - 1) + 3.0


def wgs84_to_utm(
    latitude_deg: np.ndarray, longitude_deg: np.ndarray, zone: int = DEFAULT_UTM_ZONE
) -> tuple[np.ndarray, np.ndarray]:
    """Forward transverse Mercator (UTM, northern hemisphere), WGS84.

    Snyder's series; sub-millimetre inside the zone at these latitudes.  Returns
    ``(easting_m, northing_m)`` with the standard 500 km false easting and no false
    northing.
    """

    phi = np.deg2rad(np.asarray(latitude_deg, dtype=np.float64))
    lam = np.deg2rad(np.asarray(longitude_deg, dtype=np.float64))
    lam0 = np.deg2rad(utm_zone_central_meridian_deg(zone))

    e2 = _WGS84_E2
    ep2 = e2 / (1.0 - e2)
    sin_phi = np.sin(phi)
    cos_phi = np.cos(phi)
    tan_phi = np.tan(phi)

    n = _WGS84_A / np.sqrt(1.0 - e2 * sin_phi**2)
    t = tan_phi**2
    c = ep2 * cos_phi**2
    a_term = (lam - lam0) * cos_phi

    m = _WGS84_A * (
        (1.0 - e2 / 4.0 - 3.0 * e2**2 / 64.0 - 5.0 * e2**3 / 256.0) * phi
        - (3.0 * e2 / 8.0 + 3.0 * e2**2 / 32.0 + 45.0 * e2**3 / 1024.0) * np.sin(2.0 * phi)
        + (15.0 * e2**2 / 256.0 + 45.0 * e2**3 / 1024.0) * np.sin(4.0 * phi)
        - (35.0 * e2**3 / 3072.0) * np.sin(6.0 * phi)
    )

    easting = (
        _UTM_K0
        * n
        * (
            a_term
            + (1.0 - t + c) * a_term**3 / 6.0
            + (5.0 - 18.0 * t + t**2 + 72.0 * c - 58.0 * ep2) * a_term**5 / 120.0
        )
        + _UTM_FALSE_EASTING
    )
    northing = _UTM_K0 * (
        m
        + n
        * tan_phi
        * (
            a_term**2 / 2.0
            + (5.0 - t + 9.0 * c + 4.0 * c**2) * a_term**4 / 24.0
            + (61.0 - 58.0 * t + t**2 + 600.0 * c - 330.0 * ep2) * a_term**6 / 720.0
        )
    )
    return easting, northing


def utm_to_wgs84(
    easting_m: np.ndarray, northing_m: np.ndarray, zone: int = DEFAULT_UTM_ZONE
) -> tuple[np.ndarray, np.ndarray]:
    """Inverse transverse Mercator, provided so the projection can be round-trip tested."""

    x = np.asarray(easting_m, dtype=np.float64) - _UTM_FALSE_EASTING
    y = np.asarray(northing_m, dtype=np.float64)
    e2 = _WGS84_E2
    ep2 = e2 / (1.0 - e2)
    m = y / _UTM_K0
    mu = m / (_WGS84_A * (1.0 - e2 / 4.0 - 3.0 * e2**2 / 64.0 - 5.0 * e2**3 / 256.0))
    e1 = (1.0 - math.sqrt(1.0 - e2)) / (1.0 + math.sqrt(1.0 - e2))
    phi1 = (
        mu
        + (3.0 * e1 / 2.0 - 27.0 * e1**3 / 32.0) * np.sin(2.0 * mu)
        + (21.0 * e1**2 / 16.0 - 55.0 * e1**4 / 32.0) * np.sin(4.0 * mu)
        + (151.0 * e1**3 / 96.0) * np.sin(6.0 * mu)
        + (1097.0 * e1**4 / 512.0) * np.sin(8.0 * mu)
    )
    sin_phi1 = np.sin(phi1)
    cos_phi1 = np.cos(phi1)
    tan_phi1 = np.tan(phi1)
    c1 = ep2 * cos_phi1**2
    t1 = tan_phi1**2
    n1 = _WGS84_A / np.sqrt(1.0 - e2 * sin_phi1**2)
    r1 = _WGS84_A * (1.0 - e2) / (1.0 - e2 * sin_phi1**2) ** 1.5
    d = x / (n1 * _UTM_K0)

    phi = phi1 - (n1 * tan_phi1 / r1) * (
        d**2 / 2.0
        - (5.0 + 3.0 * t1 + 10.0 * c1 - 4.0 * c1**2 - 9.0 * ep2) * d**4 / 24.0
        + (61.0 + 90.0 * t1 + 298.0 * c1 + 45.0 * t1**2 - 252.0 * ep2 - 3.0 * c1**2)
        * d**6
        / 720.0
    )
    lam = np.deg2rad(utm_zone_central_meridian_deg(zone)) + (
        d
        - (1.0 + 2.0 * t1 + c1) * d**3 / 6.0
        + (5.0 - 2.0 * c1 + 28.0 * t1 - 3.0 * c1**2 + 8.0 * ep2 + 24.0 * t1**2)
        * d**5
        / 120.0
    ) / cos_phi1
    return np.rad2deg(phi), np.rad2deg(lam)


# --------------------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ColumnMapping:
    """Zero-based column positions for the downloaded version.

    Declared, not inferred.  ``n_columns`` is asserted on every row so a shifted schema
    fails loudly instead of silently reading the wrong field.
    """

    n_columns: int = 8
    square_id: int = 0
    time_interval_ms: int = 1
    country_code: int = 2
    internet_activity: int = 7
    delimiter: str = "\t"
    has_header: bool = False

    def validate(self, where: str) -> None:
        indices = {
            "square_id": self.square_id,
            "time_interval_ms": self.time_interval_ms,
            "country_code": self.country_code,
            "internet_activity": self.internet_activity,
        }
        for name, index in indices.items():
            if not 0 <= index < self.n_columns:
                raise ConfigError(f"{where}.{name}={index} is outside n_columns={self.n_columns}")
        if len(set(indices.values())) != len(indices):
            raise ConfigError(f"{where} maps two fields to the same column")
        if self.delimiter not in ("\t", ",", ";", " "):
            raise ConfigError(f"{where}.delimiter {self.delimiter!r} is not supported")


@dataclass(frozen=True)
class RegionSelection:
    """Predetermined geographic selection rule.

    A latitude/longitude bounding box, fixed before any model is fitted and never chosen
    by looking at test-set results or at which algorithm scores best.
    """

    rule: str = "latlon_bbox"
    min_lat_deg: float = 45.44
    max_lat_deg: float = 45.50
    min_lon_deg: float = 9.15
    max_lon_deg: float = 9.23
    max_cells: int = 400

    def validate(self, where: str) -> None:
        if self.rule != "latlon_bbox":
            raise ConfigError(f"{where}.rule must be 'latlon_bbox' in v0")
        if self.max_lat_deg <= self.min_lat_deg or self.max_lon_deg <= self.min_lon_deg:
            raise ConfigError(f"{where} bounding box must be ordered and non-degenerate")
        if self.max_cells < 1:
            raise ConfigError(f"{where}.max_cells must be >= 1")


@dataclass(frozen=True)
class PreprocessConfig:
    """Strict configuration for one ingestion run."""

    utm_zone: int = DEFAULT_UTM_ZONE
    interval_duration_ms: int = 600_000
    activity_field: str = "internet"
    columns: ColumnMapping = field(default_factory=ColumnMapping)
    region: RegionSelection = field(default_factory=RegionSelection)
    duplicate_key_rule: str = "reject"
    missing_value_policy: str = "unknown"
    reference_scale_quantile: float = 0.95
    train_dates: tuple[str, ...] = ()
    validation_dates: tuple[str, ...] = ()
    test_dates: tuple[str, ...] = ()
    dataset_version: str = "unspecified"
    source_url: str = DEFAULT_SOURCE_URL
    license_note: str = DEFAULT_LICENSE_NOTE
    description: str = ""
    max_activity_value: float = 1.0e9

    def validate(self) -> None:
        if self.activity_field != "internet":
            raise ConfigError(
                "activity_field must be 'internet' in v0; activity kinds are never summed"
            )
        if self.interval_duration_ms <= 0:
            raise ConfigError("interval_duration_ms must be positive")
        if self.duplicate_key_rule not in ("reject", "sum_declared", "first_declared"):
            raise ConfigError(
                "duplicate_key_rule must be 'reject', 'sum_declared' or 'first_declared'"
            )
        if self.missing_value_policy not in ("unknown", "zero_fill_declared"):
            raise ConfigError(
                "missing_value_policy must be 'unknown' or 'zero_fill_declared'"
            )
        if not 0.0 < self.reference_scale_quantile < 1.0:
            raise ConfigError("reference_scale_quantile must be in (0, 1)")
        self.columns.validate("columns")
        self.region.validate("region")
        splits = {
            "train": set(self.train_dates),
            "validation": set(self.validation_dates),
            "test": set(self.test_dates),
        }
        if not splits["train"]:
            raise ConfigError("train_dates must not be empty: normalisation is fitted on it")
        names = list(splits)
        for left in range(len(names)):
            for right in range(left + 1, len(names)):
                shared = splits[names[left]] & splits[names[right]]
                if shared:
                    raise ConfigError(
                        f"{names[left]} and {names[right]} dates overlap: {sorted(shared)}"
                    )

    def split_of_date(self, date_label: str) -> str | None:
        if date_label in self.train_dates:
            return "train"
        if date_label in self.validation_dates:
            return "validation"
        if date_label in self.test_dates:
            return "test"
        return None


def load_preprocess_config(path: str | Path) -> PreprocessConfig:
    resolved = Path(path)
    if not resolved.is_file():
        raise ConfigError(f"preprocessing configuration not found: {resolved}")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    config = strict_from_mapping(PreprocessConfig, payload)
    config.validate()
    return config


# --------------------------------------------------------------------------------------
# Grid geometry
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class GridGeometry:
    cell_ids: np.ndarray
    latitude_deg: np.ndarray
    longitude_deg: np.ndarray
    easting_m: np.ndarray
    northing_m: np.ndarray
    source_crs: str


def read_milano_grid(
    path: str | Path,
    *,
    utm_zone: int = DEFAULT_UTM_ZONE,
    cell_id_properties: Sequence[str] = ("cellId", "cell_id", "ID", "id"),
) -> GridGeometry:
    """Read the Milano Grid GeoJSON and project every cell's representative point.

    The representative point is the arithmetic mean of the polygon's exterior-ring
    vertices, with the closing duplicate removed.  Using one aggregated point per grid
    cell is *spatial discretization*, recorded as such.

    The source CRS is read from the document when present.  GeoJSON's default is
    ``urn:ogc:def:crs:OGC::CRS84`` (WGS84 longitude/latitude); anything else is refused
    rather than assumed.
    """

    resolved = Path(path)
    if not resolved.is_file():
        raise PreprocessError(f"grid GeoJSON not found: {resolved}")
    document = json.loads(resolved.read_text(encoding="utf-8"))
    crs = "urn:ogc:def:crs:OGC::CRS84"
    declared = document.get("crs")
    if isinstance(declared, dict):
        name = str(declared.get("properties", {}).get("name", ""))
        if name:
            crs = name
    accepted = {
        "urn:ogc:def:crs:OGC::CRS84",
        "urn:ogc:def:crs:OGC:1.3:CRS84",
        "EPSG:4326",
        "urn:ogc:def:crs:EPSG::4326",
    }
    if crs not in accepted:
        raise PreprocessError(
            f"grid GeoJSON declares CRS {crs!r}; only WGS84 longitude/latitude is "
            "handled. Reproject the grid explicitly rather than assuming."
        )

    features = document.get("features")
    if not isinstance(features, list) or not features:
        raise PreprocessError("grid GeoJSON has no features")

    ids: list[int] = []
    lats: list[float] = []
    lons: list[float] = []
    for index, feature in enumerate(features):
        properties = feature.get("properties") or {}
        cell_id = None
        for key in cell_id_properties:
            if key in properties:
                cell_id = properties[key]
                break
        if cell_id is None:
            raise PreprocessError(
                f"grid feature {index} has no cell id property "
                f"(looked for {list(cell_id_properties)})"
            )
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "Polygon":
            raise PreprocessError(
                f"grid feature {index} geometry type {geometry.get('type')!r} is not a Polygon"
            )
        rings = geometry.get("coordinates") or []
        if not rings or not rings[0]:
            raise PreprocessError(f"grid feature {index} has an empty exterior ring")
        ring = [tuple(map(float, point[:2])) for point in rings[0]]
        if len(ring) > 1 and ring[0] == ring[-1]:
            ring = ring[:-1]
        if not ring:
            raise PreprocessError(f"grid feature {index} exterior ring collapsed")
        lons.append(float(np.mean([point[0] for point in ring])))
        lats.append(float(np.mean([point[1] for point in ring])))
        ids.append(int(cell_id))

    cell_ids = np.asarray(ids, dtype=np.int64)
    if np.unique(cell_ids).shape[0] != cell_ids.shape[0]:
        raise PreprocessError("grid GeoJSON contains duplicate cell ids")
    latitude = np.asarray(lats, dtype=np.float64)
    longitude = np.asarray(lons, dtype=np.float64)
    if not (np.isfinite(latitude).all() and np.isfinite(longitude).all()):
        raise PreprocessError("grid GeoJSON produced non-finite coordinates")
    if (np.abs(latitude) > 90.0).any() or (np.abs(longitude) > 180.0).any():
        raise PreprocessError(
            "grid coordinates are outside valid latitude/longitude ranges; the file may "
            "be projected already, or the axis order may be reversed"
        )
    easting, northing = wgs84_to_utm(latitude, longitude, utm_zone)
    order = np.argsort(cell_ids, kind="stable")
    return GridGeometry(
        cell_ids=cell_ids[order],
        latitude_deg=latitude[order],
        longitude_deg=longitude[order],
        easting_m=easting[order],
        northing_m=northing[order],
        source_crs=crs,
    )


def select_region(
    grid: GridGeometry, region: RegionSelection
) -> tuple[np.ndarray, dict[str, Any]]:
    """Apply the predetermined geographic selection rule.

    Returns the selected indices into ``grid`` plus a record of the rule that produced
    them.
    """

    inside = (
        (grid.latitude_deg >= region.min_lat_deg)
        & (grid.latitude_deg <= region.max_lat_deg)
        & (grid.longitude_deg >= region.min_lon_deg)
        & (grid.longitude_deg <= region.max_lon_deg)
    )
    indices = np.flatnonzero(inside)
    if indices.size == 0:
        raise PreprocessError(
            "the configured region selects no grid cell; check the bounding box against "
            "the grid's actual extent"
        )
    if indices.size > int(region.max_cells):
        raise PreprocessError(
            f"the configured region selects {indices.size} cells, above max_cells="
            f"{region.max_cells}. Shrink the bounding box deliberately; cells are not "
            "silently dropped."
        )
    return indices, {
        "rule": region.rule,
        "min_lat_deg": region.min_lat_deg,
        "max_lat_deg": region.max_lat_deg,
        "min_lon_deg": region.min_lon_deg,
        "max_lon_deg": region.max_lon_deg,
        "n_cells_selected": int(indices.size),
        "selection_basis": (
            "fixed geographic bounding box declared before any model fit; not chosen "
            "from test-set results or algorithm scores"
        ),
    }


# --------------------------------------------------------------------------------------
# Raw activity ingestion
# --------------------------------------------------------------------------------------


def sha256_of_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_date_label(timestamp_utc_ms: int) -> str:
    return datetime.fromtimestamp(int(timestamp_utc_ms) / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%d"
    )


def rome_time_of_day_label(timestamp_utc_ms: int) -> str:
    """``Europe/Rome`` clock label.  The runtime machine's timezone is never consulted."""

    moment = datetime.fromtimestamp(int(timestamp_utc_ms) / 1000.0, tz=timezone.utc)
    return moment.astimezone(_ROME).strftime("%Y-%m-%d %H:%M %Z")


@dataclass
class QualityCounters:
    raw_rows: int = 0
    accepted_rows: int = 0
    rows_outside_region: int = 0
    rows_outside_splits: int = 0
    explicit_zero_values: int = 0
    empty_field_values: int = 0
    duplicate_keys: int = 0
    malformed_rows: int = 0
    country_codes_seen: int = 0
    files_read: int = 0
    duplicate_files_skipped: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "raw_rows": self.raw_rows,
            "accepted_rows": self.accepted_rows,
            "rows_outside_region": self.rows_outside_region,
            "rows_outside_splits": self.rows_outside_splits,
            "explicit_zero_values": self.explicit_zero_values,
            "empty_field_values": self.empty_field_values,
            "duplicate_keys": self.duplicate_keys,
            "malformed_rows": self.malformed_rows,
            "distinct_country_codes": self.country_codes_seen,
            "files_read": self.files_read,
            "duplicate_files_skipped": self.duplicate_files_skipped,
        }


def _missing_intervals_per_date(timestamps: np.ndarray, interval_ms: int) -> np.ndarray:
    """Interval starts absent from a date the input otherwise covers."""

    stamps = np.asarray(timestamps, dtype=np.int64)
    if stamps.size == 0:
        return np.zeros(0, dtype=np.int64)
    day_ms = 86_400_000
    if day_ms % int(interval_ms) != 0:
        # A non-divisor interval has no well-defined per-day grid; fall back to the span.
        expected = np.arange(
            int(stamps[0]), int(stamps[-1]) + int(interval_ms), int(interval_ms), dtype=np.int64
        )
        return np.setdiff1d(expected, stamps)
    per_day = day_ms // int(interval_ms)
    days = np.unique(stamps // day_ms)
    expected = np.concatenate(
        [day * day_ms + int(interval_ms) * np.arange(per_day, dtype=np.int64) for day in days]
    )
    return np.setdiff1d(expected, stamps)


def _iter_rows(path: Path, columns: ColumnMapping) -> Iterator[list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=columns.delimiter)
        if columns.has_header:
            next(reader, None)
        for row in reader:
            if not row or (len(row) == 1 and not row[0].strip()):
                continue
            yield row


def ingest_activity(
    input_paths: Sequence[str | Path],
    grid: GridGeometry,
    config: PreprocessConfig,
) -> dict[str, Any]:
    """Parse, validate and aggregate raw activity rows.

    Returns the aggregated arrays plus a quality record.  Nothing is written here.
    """

    selected_indices, region_record = select_region(grid, config.region)
    selected_ids = grid.cell_ids[selected_indices]
    id_to_slot = {int(cell_id): slot for slot, cell_id in enumerate(selected_ids)}

    counters = QualityCounters()
    seen_hashes: dict[str, str] = {}
    country_codes: set[str] = set()
    # (interval, slot) -> summed activity; a separate set records which keys had any row.
    totals: dict[tuple[int, int], float] = {}
    seen_keys: set[tuple[int, int, str]] = set()
    intervals: set[int] = set()

    for raw_path in input_paths:
        path = Path(raw_path)
        if not path.is_file():
            raise PreprocessError(f"input file not found: {path}")
        digest = sha256_of_file(path)
        if digest in seen_hashes:
            counters.duplicate_files_skipped += 1
            # Identical content would double every activity value; refuse it explicitly.
            raise PreprocessError(
                f"{path.name} has the same SHA-256 as {seen_hashes[digest]}; overlapping "
                "input files would double the activity and are refused"
            )
        seen_hashes[digest] = path.name
        counters.files_read += 1

        for row in _iter_rows(path, config.columns):
            counters.raw_rows += 1
            if len(row) != config.columns.n_columns:
                raise PreprocessError(
                    f"{path.name}: row {counters.raw_rows} has {len(row)} columns, expected "
                    f"{config.columns.n_columns}. The declared column mapping does not "
                    "match this file version."
                )
            try:
                cell_id = int(row[config.columns.square_id].strip())
                timestamp = int(row[config.columns.time_interval_ms].strip())
            except ValueError as error:
                raise PreprocessError(
                    f"{path.name}: row {counters.raw_rows} has a non-integer square id or "
                    f"timestamp ({error})"
                ) from error
            if timestamp < 0:
                raise PreprocessError(
                    f"{path.name}: row {counters.raw_rows} has a negative timestamp"
                )
            if timestamp % config.interval_duration_ms != 0:
                raise PreprocessError(
                    f"{path.name}: timestamp {timestamp} is not a multiple of "
                    f"{config.interval_duration_ms} ms. The time field is probably not in "
                    "milliseconds, or the interval length is wrong."
                )
            country = row[config.columns.country_code].strip()
            country_codes.add(country)

            slot = id_to_slot.get(cell_id)
            if slot is None:
                counters.rows_outside_region += 1
                continue
            date_label = utc_date_label(timestamp)
            if config.split_of_date(date_label) is None:
                counters.rows_outside_splits += 1
                continue

            key = (timestamp, slot, country)
            if key in seen_keys:
                counters.duplicate_keys += 1
                if config.duplicate_key_rule == "reject":
                    raise PreprocessError(
                        f"{path.name}: duplicate (square_id={cell_id}, "
                        f"time_interval={timestamp}, country_code={country}). Set "
                        "duplicate_key_rule deliberately if the source really contains "
                        "repeats; activity is never silently doubled."
                    )
                if config.duplicate_key_rule == "first_declared":
                    continue
            seen_keys.add(key)

            text = row[config.columns.internet_activity].strip()
            if text == "":
                counters.empty_field_values += 1
                # An empty field is unknown, not zero: the key is not recorded as
                # observed unless the policy declares zero filling.
                if config.missing_value_policy == "zero_fill_declared":
                    value = 0.0
                else:
                    intervals.add(timestamp)
                    continue
            else:
                try:
                    value = float(text)
                except ValueError as error:
                    raise PreprocessError(
                        f"{path.name}: row {counters.raw_rows} has a non-numeric activity "
                        f"value {text!r} ({error})"
                    ) from error
            if not math.isfinite(value):
                raise PreprocessError(
                    f"{path.name}: row {counters.raw_rows} activity value is not finite"
                )
            if value < 0.0:
                raise PreprocessError(
                    f"{path.name}: row {counters.raw_rows} activity value {value} is "
                    "negative; activity cannot be negative"
                )
            if value > config.max_activity_value:
                raise PreprocessError(
                    f"{path.name}: row {counters.raw_rows} activity value {value} exceeds "
                    f"max_activity_value={config.max_activity_value}; check the units and "
                    "the column mapping"
                )
            if value == 0.0:
                counters.explicit_zero_values += 1
            counters.accepted_rows += 1
            intervals.add(timestamp)
            # Country code is a dimension of the same cell: sum over it.
            totals[(timestamp, slot)] = totals.get((timestamp, slot), 0.0) + value

    counters.country_codes_seen = len(country_codes)
    if not intervals:
        raise PreprocessError(
            "no row fell inside the configured region and split dates; check the region "
            "bounding box, the split dates and the column mapping"
        )

    timestamps = np.asarray(sorted(intervals), dtype=np.int64)
    # Interval completeness is judged *per UTC date*: for every date the input touches,
    # the complete set of interval starts inside that date is expected.  Judging it over
    # the whole span instead would report every interval of every absent day as missing,
    # which says nothing about the files actually supplied.
    missing_intervals = _missing_intervals_per_date(timestamps, config.interval_duration_ms)
    interval_slot = {int(value): index for index, value in enumerate(timestamps)}

    n_cells = int(selected_ids.shape[0])
    activity = np.zeros((timestamps.shape[0], n_cells), dtype=np.float64)
    observed = np.zeros((timestamps.shape[0], n_cells), dtype=bool)
    for (timestamp, slot), value in totals.items():
        row_index = interval_slot[int(timestamp)]
        activity[row_index, slot] = value
        observed[row_index, slot] = True
    missing_rows = int((~observed).sum())

    positions = np.stack(
        [grid.easting_m[selected_indices], grid.northing_m[selected_indices]], axis=1
    )

    return {
        "timestamps_utc_ms": timestamps,
        "cell_ids": selected_ids.astype(np.int64),
        "positions_utm_m": positions,
        "activity": activity,
        "observed_mask": observed,
        "grid_indices": selected_indices,
        "region_record": region_record,
        "counters": counters,
        "missing_intervals_utc_ms": missing_intervals.astype(np.int64),
        "missing_rows": missing_rows,
        "file_hashes": {name: digest for digest, name in seen_hashes.items()},
        "source_crs": grid.source_crs,
    }


# --------------------------------------------------------------------------------------
# Writing the prepared cache
# --------------------------------------------------------------------------------------


def write_prepared_dataset(
    output_root: str | Path,
    ingested: dict[str, Any],
    config: PreprocessConfig,
    *,
    is_real_activity_data: bool,
    kind: str = "milan_activity",
    local_origin_m: tuple[float, float] | None = None,
) -> dict[str, Any]:
    """Write the read-only cache into a **new** directory, with an atomic marker.

    An existing directory is refused: a cache another process may be reading is never
    overwritten.  The completion marker is written last, so a reader that finds it knows
    every array is complete.
    """

    root = Path(output_root)
    if root.exists():
        raise PreprocessError(
            f"{root} already exists; write into a new directory so a cache in use is "
            "never overwritten"
        )

    timestamps: np.ndarray = ingested["timestamps_utc_ms"]
    activity: np.ndarray = ingested["activity"]
    observed: np.ndarray = ingested["observed_mask"]
    positions_utm: np.ndarray = ingested["positions_utm_m"]
    cell_ids: np.ndarray = ingested["cell_ids"]

    date_labels = np.asarray([utc_date_label(int(value)) for value in timestamps])
    splits: dict[str, list[str]] = {"train": [], "validation": [], "test": []}
    for label in sorted(set(date_labels.tolist())):
        split = config.split_of_date(label)
        if split is not None:
            splits[split].append(label)
    train_mask = np.asarray([config.split_of_date(label) == "train" for label in date_labels])
    if not train_mask.any():
        raise PreprocessError(
            "no interval fell on a configured training date; the reference scale must be "
            "fitted on training data only"
        )
    reference_scale = reference_scale_from_training(
        activity[train_mask], observed[train_mask], config.reference_scale_quantile
    )

    origin = (
        (float(positions_utm[:, 0].min()), float(positions_utm[:, 1].min()))
        if local_origin_m is None
        else (float(local_origin_m[0]), float(local_origin_m[1]))
    )
    positions_local = positions_utm - np.asarray(origin, dtype=np.float64)[None, :]

    root.mkdir(parents=True)
    arrays = {
        "timestamps_utc_ms.npy": timestamps.astype(np.int64),
        "cell_ids.npy": cell_ids.astype(np.int64),
        "positions_m.npy": positions_local.astype(np.float64),
        "activity.npy": activity.astype(np.float64),
        "observed_mask.npy": observed.astype(np.bool_),
    }
    for name, value in arrays.items():
        np.save(root / name, value, allow_pickle=False)

    content = hashlib.sha256()
    content.update(PREPARED_SCHEMA_VERSION.encode("ascii"))
    for name in sorted(arrays):
        content.update(name.encode("ascii"))
        content.update(np.ascontiguousarray(arrays[name]).tobytes())
    content_hash = content.hexdigest()

    counters: QualityCounters = ingested["counters"]
    quality = {
        "counters": counters.as_dict(),
        "aggregated_rows": int(observed.sum()),
        "missing_rows": int(ingested["missing_rows"]),
        "n_missing_intervals": int(len(ingested["missing_intervals_utc_ms"])),
        "missing_intervals_utc_ms_sample": [
            int(value) for value in ingested["missing_intervals_utc_ms"][:200]
        ],
        "missing_interval_rule": (
            "per UTC date: every interval start inside a date the input touches is "
            "expected; the list is truncated to 200 examples and the count is exact"
        ),
        "observed_fraction": float(observed.mean()) if observed.size else 0.0,
        "temporal_coverage": {
            "first_interval_utc_ms": int(timestamps[0]),
            "last_interval_utc_ms": int(timestamps[-1]),
            "first_interval_rome": rome_time_of_day_label(int(timestamps[0])),
            "last_interval_rome": rome_time_of_day_label(int(timestamps[-1])),
            "n_intervals": int(timestamps.shape[0]),
            "n_dates": int(len(set(date_labels.tolist()))),
        },
        "total_activity": float(activity[observed].sum()) if observed.any() else 0.0,
        "n_valid_cells": int(cell_ids.shape[0]),
        "activity_quantiles": {
            "p50": float(np.quantile(activity[observed], 0.5)) if observed.any() else None,
            "p95": float(np.quantile(activity[observed], 0.95)) if observed.any() else None,
            "max": float(activity[observed].max()) if observed.any() else None,
        },
        "outlier_handling": (
            f"values above max_activity_value={config.max_activity_value} are refused, "
            "not clipped"
        ),
        "historical_period_note": (
            "This is a historical observation period. It is not present-day load and must "
            "not be presented as such."
        ),
    }
    (root / "quality_report.json").write_text(
        json.dumps(quality, indent=2, sort_keys=True), encoding="utf-8"
    )
    (root / "splits.json").write_text(
        json.dumps(
            {
                "rule": "complete UTC dates; adjacent windows never span a split boundary",
                "splits": splits,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    file_hashes = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in arrays
    }
    metadata = {
        "schema_version": PREPARED_SCHEMA_VERSION,
        "kind": kind,
        "is_real_activity_data": bool(is_real_activity_data),
        "description": config.description
        or (
            "Aggregated Internet activity per grid cell and 10-minute interval. Activity "
            "is not measured Mbps, not a user count and not individual traffic."
        ),
        "source_url": config.source_url,
        "license_note": config.license_note,
        "dataset_version": config.dataset_version,
        "activity_field": config.activity_field,
        "interval_duration_ms": int(config.interval_duration_ms),
        "aggregation_rule": (
            "sum over country_code for each (square_id, time_interval); country code is a "
            "dimension of the same cell, never a separate location"
        ),
        "duplicate_key_rule": config.duplicate_key_rule,
        "missing_data_policy": config.missing_value_policy,
        "raw_column_mapping": {
            "n_columns": config.columns.n_columns,
            "square_id": config.columns.square_id,
            "time_interval_ms": config.columns.time_interval_ms,
            "country_code": config.columns.country_code,
            "internet_activity": config.columns.internet_activity,
            "delimiter": config.columns.delimiter,
            "has_header": config.columns.has_header,
        },
        "raw_file_sha256": ingested["file_hashes"],
        "crs": {
            "source": ingested["source_crs"],
            "projected": f"UTM zone {config.utm_zone}N (WGS84)",
            "local_origin_utm_m": list(origin),
            "note": (
                "positions_m.npy is metres in the projected frame, shifted by "
                "local_origin_utm_m. Latitude and longitude were never scaled by a "
                "constant."
            ),
        },
        "region_selection_rule": ingested["region_record"],
        "spatial_discretization": (
            "one aggregated demand point per grid cell; the representative point is the "
            "mean of the cell polygon's exterior vertices"
        ),
        "activity_reference_scale": float(reference_scale),
        "reference_scale_rule": (
            f"quantile({config.reference_scale_quantile}) of strictly positive observed "
            "activity on the training dates only"
        ),
        "preprocessing_code_version": PREPARED_SCHEMA_VERSION,
        "content_sha256": content_hash,
        "file_sha256": file_hashes,
        "parameter_summary": {
            "utm_zone": int(config.utm_zone),
            "reference_scale_quantile": float(config.reference_scale_quantile),
            "max_activity_value": float(config.max_activity_value),
        },
    }
    (root / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
    )
    # Written last: its presence certifies that every array above is complete.
    (root / COMPLETION_MARKER).write_text(
        json.dumps(
            {
                "schema_version": PREPARED_SCHEMA_VERSION,
                "content_sha256": content_hash,
                "completed_utc": datetime.now(tz=timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return metadata


def prepare_milan_dataset(
    input_paths: Sequence[str | Path],
    grid_path: str | Path,
    config: PreprocessConfig,
    output_root: str | Path,
    *,
    is_real_activity_data: bool = True,
    kind: str = "milan_activity",
) -> dict[str, Any]:
    """Full ingestion: read grid, parse activity, write a new read-only cache."""

    config.validate()
    grid = read_milano_grid(grid_path, utm_zone=config.utm_zone)
    ingested = ingest_activity(input_paths, grid, config)
    return write_prepared_dataset(
        output_root,
        ingested,
        config,
        is_real_activity_data=is_real_activity_data,
        kind=kind,
    )


def inspect_raw_sample(
    path: str | Path, config: PreprocessConfig, max_rows: int = 2000
) -> dict[str, Any]:
    """Report what a raw file actually contains, without ingesting it.

    Use this to *verify* the declared column mapping, units and country-code semantics
    against the version you downloaded, before running a preparation.
    """

    resolved = Path(path)
    if not resolved.is_file():
        raise PreprocessError(f"input file not found: {resolved}")
    column_counts: dict[int, int] = {}
    timestamps: list[int] = []
    countries: set[str] = set()
    cells: set[int] = set()
    empties = 0
    zeros = 0
    values: list[float] = []
    rows = 0
    for row in _iter_rows(resolved, config.columns):
        rows += 1
        column_counts[len(row)] = column_counts.get(len(row), 0) + 1
        if len(row) != config.columns.n_columns:
            if rows >= max_rows:
                break
            continue
        try:
            timestamps.append(int(row[config.columns.time_interval_ms].strip()))
            cells.add(int(row[config.columns.square_id].strip()))
        except ValueError:
            pass
        countries.add(row[config.columns.country_code].strip())
        text = row[config.columns.internet_activity].strip()
        if text == "":
            empties += 1
        else:
            try:
                value = float(text)
            except ValueError:
                continue
            values.append(value)
            if value == 0.0:
                zeros += 1
        if rows >= max_rows:
            break

    stamps = np.asarray(timestamps, dtype=np.int64) if timestamps else np.zeros(0, dtype=np.int64)
    aligned = (
        bool(np.all(stamps % config.interval_duration_ms == 0)) if stamps.size else False
    )
    return {
        "path": str(resolved),
        "sha256": sha256_of_file(resolved),
        "rows_inspected": rows,
        "column_count_histogram": column_counts,
        "declared_n_columns": config.columns.n_columns,
        "column_count_matches_declared": set(column_counts) == {config.columns.n_columns},
        "distinct_square_ids": len(cells),
        "distinct_country_codes": len(countries),
        "country_code_sample": sorted(countries)[:12],
        "timestamp_min": int(stamps.min()) if stamps.size else None,
        "timestamp_max": int(stamps.max()) if stamps.size else None,
        "timestamp_min_utc": utc_date_label(int(stamps.min())) if stamps.size else None,
        "timestamp_min_rome": rome_time_of_day_label(int(stamps.min())) if stamps.size else None,
        "timestamps_aligned_to_interval": aligned,
        "interval_duration_ms": int(config.interval_duration_ms),
        "empty_activity_fields": empties,
        "explicit_zero_activity_values": zeros,
        "activity_value_stats": (
            {
                "min": float(np.min(values)),
                "median": float(np.median(values)),
                "p95": float(np.quantile(values, 0.95)),
                "max": float(np.max(values)),
            }
            if values
            else None
        ),
        "warning": (
            "These are aggregated ACTIVITY values, not Mbps, not user counts and not "
            "individual traffic. Confirm column semantics against the publisher's "
            "documentation for this exact version."
        ),
    }
