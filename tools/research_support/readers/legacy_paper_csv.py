"""Reader for the legacy ``paper_eval_episodes_step_*.csv`` evaluation rows.

Why this reader is not simply a call into ``tools/analysis/paper_experiment_report.py``:
that reporter is the historical producer of published numbers and must keep behaving
exactly as it does, but two of its behaviours are unsafe to build new analysis on.

1. ``_summarize_per_seed`` coerces every metric column with
   ``pd.to_numeric(..., errors="coerce").dropna()``.  A cell holding ``"n/a"``, an error
   string, or a stray unit therefore **disappears**: the mean is computed over fewer
   episodes than the group contains and nothing in the output says so.
2. For a single episode in a seed, or a single seed in a group, it reports ``std = 0.0``
   and ``ci95 = 0.0``.  Zero dispersion is a measurement; "one observation carries no
   dispersion estimate" is an absence.  A plotted error bar of zero claims a precision the
   data never supported.

This reader therefore reproduces the legacy arithmetic *and* records what the legacy path
drops.  ``coverage["legacy_reproduction"]`` carries, per group and metric:

* ``mean`` / ``min`` / ``max`` / ``episode_count`` - identical to the legacy columns;
* ``legacy_std`` / ``legacy_ci95`` - the exact legacy values, including the ``0.0`` that a
  single observation produces, so an existing table can still be reproduced;
* ``std`` / ``ci95`` - the same quantities as :class:`Measured`, **absent** with
  ``NOT_APPLICABLE`` when ``n == 1``;
* ``n_invalid_dropped`` / ``n_missing_dropped`` - how many cells the coercion removed.

Identity follows the legacy rules exactly (seed from a ``seed_<n>`` path part, ``eval_step``
from the file name, ``checkpoint`` defaulted to ``step_<eval_step>``) because those rules
define what the historical rows *mean*.  They are recorded as filename-derived, lower
confidence evidence, never as recorded fields.  A duplicated episode identity is refused:
the same episode entering a mean twice would silently move a published number.

Static only: ``pandas.read_csv`` and nothing else.  No agent import, no checkpoint.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from tools.research_support.readers import (
    FIELD_ALGORITHM,
    FIELD_ARTIFACT_LOCATIONS,
    FIELD_CHECKPOINT_IDENTITY,
    FIELD_CHECKPOINT_SELECTION,
    FIELD_COMPLETION_STATUS,
    FIELD_EVALUATION_SEED,
    FIELD_EVALUATION_WORLD,
    FIELD_REWARD_DEFINITION,
    FIELD_STATISTICAL_UNIT,
    FIELD_TERMINATION_DECLARED,
    FIELD_TERMINATION_OBSERVED,
    FIELD_TRAINING_EXPOSURE,
    FIELD_TRAINING_SEED,
    EpisodeIdentityError,
    ReadResult,
    UnsupportedSourceError,
    boundary_measures,
    boundary_semantics,
    default_run_id,
    ensure_identity_fields,
    joined_locations,
    register_source,
)
from tools.research_support.records import (
    AggregationLevel,
    Measured,
    MetricRecord,
    Phase,
    RunRecord,
    Validity,
    XKind,
)

#: Reserved helper columns this reader adds to the frame; never treated as metrics.
_RESERVED = ("__source_file__", "__source_row__")

#: Columns that carry identity or bookkeeping rather than a measurement.
_NON_METRIC = (
    "preset",
    "scenario_label",
    "checkpoint",
    "eval_step",
    "run_seed",
    "seed",
    "episode",
    "episode_id",
    "source_file",
) + _RESERVED

_STEP_PATTERN = re.compile(r"paper_eval_episodes_step_(\d+)\.csv$")


def _plain(value: Any) -> Any:
    """Plain-Python scalar for a JSON-able coverage report."""

    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return str(value)


def _infer_seed(path: Path) -> Any:
    """Legacy seed inference: the first ``seed_<n>`` path part, else ``""``.

    Copied deliberately rather than imported: the legacy reporter is frozen, and this is the
    documented lower-confidence mapping that gives the historical rows their meaning.
    """

    for part in Path(path).parts:
        if part.startswith("seed_"):
            try:
                return int(part.split("_", 1)[1])
            except ValueError:
                return part
    return ""


def _absent_uncertainty(n: int, what: str) -> Measured:
    """``NOT_APPLICABLE`` dispersion for a single observation."""

    return Measured.absent(
        Validity.NOT_APPLICABLE,
        f"n={n}: a {what} does not exist for a single observation; the legacy reporter "
        "prints 0.0 here, which is a precision claim the data does not support",
    )


class LegacyPaperCsvReader:
    """Reads ``paper_eval_episodes_step_*.csv`` trees into episode-level metric records."""

    name = "legacy_paper_csv"
    version = "1"

    GLOB = "paper_eval_episodes_step_*.csv"

    # Detection -----------------------------------------------------------------------

    def detect(self, root: Path) -> bool:
        """True only when at least one file with the named legacy pattern exists."""

        root = Path(root)
        if not root.is_dir():
            return False
        for _ in root.rglob(self.GLOB):
            return True
        return False

    # Reading -------------------------------------------------------------------------

    def read(self, root: Path) -> ReadResult:
        root = Path(root)
        result = ReadResult()
        result.coverage.update(
            {
                "reader": self.name,
                "reader_version": self.version,
                "root": str(root),
                "glob": self.GLOB,
            }
        )
        run = RunRecord(run_id=default_run_id(self.name, root), reader=self.name, reader_version=self.version)

        files = sorted(root.rglob(self.GLOB))
        if not files:
            raise UnsupportedSourceError(
                f"{root} holds no {self.GLOB}; this reader requires the named legacy artifact"
            )

        frames: list[pd.DataFrame] = []
        filename_derived: set[str] = set()
        for path in files:
            digest = register_source(run, path)
            try:
                frame = pd.read_csv(path, dtype=str, keep_default_na=True)
            except (OSError, UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
                message = f"{path}: unreadable CSV: {error}"
                result.errors.append(message)
                result.note_file(path, "unsupported", detail=str(error), digest=digest)
                continue
            if frame.empty:
                result.note_file(path, "skipped", detail="no data rows", rows=0, digest=digest)
                result.warnings.append(f"{path}: no data rows")
                continue

            frame = frame.copy()
            frame["__source_file__"] = str(path)
            frame["__source_row__"] = np.arange(len(frame), dtype=np.int64)

            # Legacy identity completion, in the legacy order.
            if "seed" not in frame.columns:
                frame["seed"] = _infer_seed(path)
                filename_derived.add("seed")
            if "run_seed" not in frame.columns:
                inferred = _infer_seed(path)
                frame["run_seed"] = inferred if inferred != "" else frame["seed"]
                filename_derived.add("run_seed")
            if "eval_step" not in frame.columns:
                match = _STEP_PATTERN.search(path.name)
                if match is None:
                    detail = "cannot infer eval_step from the file name and no eval_step column"
                    result.errors.append(f"{path}: {detail}")
                    result.note_file(path, "unsupported", detail=detail, rows=len(frame), digest=digest)
                    continue
                frame["eval_step"] = int(match.group(1))
                filename_derived.add("eval_step")
            if "checkpoint" not in frame.columns:
                frame["checkpoint"] = "step_" + frame["eval_step"].astype(str)
                filename_derived.add("checkpoint")

            result.note_file(path, "parsed", rows=len(frame), digest=digest)
            frames.append(frame)

        if not frames:
            result.errors.append(f"{root}: every {self.GLOB} file was unreadable or empty")
            result.coverage["rows_parsed"] = 0
            self._finish_run_record(run, result, root, group_columns=[], filename_derived=filename_derived)
            result.run_records.append(run)
            return result

        episodes = pd.concat(frames, ignore_index=True)
        result.coverage["rows_parsed"] = int(len(episodes))
        result.coverage["files_parsed"] = len(frames)
        result.coverage["files_total"] = len(files)
        result.coverage["filename_derived_identity"] = sorted(filename_derived)

        group_columns = [c for c in ("preset", "scenario_label") if c in episodes.columns]
        if not group_columns:
            raise EpisodeIdentityError(
                f"{root}: paper episode rows require preset or scenario_label to identify a "
                "method; refusing to read rows whose method is unknown"
            )
        episode_column = self._require_episode_identity(episodes, group_columns, root)
        result.coverage["group_columns"] = group_columns
        result.coverage["episode_column"] = episode_column
        identity_columns = [*group_columns, "checkpoint", "eval_step", "run_seed", "seed", episode_column]
        result.coverage["identity_columns"] = identity_columns

        metric_columns, non_numeric = self._classify_columns(episodes)
        result.coverage["metric_columns"] = metric_columns
        result.coverage["non_numeric_columns"] = non_numeric
        if non_numeric:
            result.warnings.append(
                "columns with no numeric cell are reported as non-numeric metadata rather "
                f"than as all-invalid metrics: {non_numeric}"
            )

        method_labels = sorted(
            {"|".join(str(row[c]) for c in group_columns) for _, row in episodes[group_columns].iterrows()}
        )
        result.coverage["method_labels"] = method_labels

        self._emit_metric_records(
            result,
            run,
            episodes,
            group_columns=group_columns,
            episode_column=episode_column,
            metric_columns=metric_columns,
        )
        result.coverage["legacy_reproduction"] = self._legacy_reproduction(
            episodes, group_columns=group_columns, metric_columns=metric_columns
        )
        result.coverage["invalid_value_counts"] = {
            metric: int(
                (
                    pd.to_numeric(episodes[metric], errors="coerce").isna()
                    & ~episodes[metric].isna()
                ).sum()
            )
            for metric in metric_columns
        }

        self._finish_run_record(
            run,
            result,
            root,
            group_columns=group_columns,
            filename_derived=filename_derived,
            episodes=episodes,
            method_labels=method_labels,
        )
        result.run_records.append(run)
        result.coverage["metric_record_count"] = len(result.metric_records)
        return result

    # Identity ------------------------------------------------------------------------

    def _require_episode_identity(
        self, frame: pd.DataFrame, group_columns: list[str], root: Path
    ) -> str:
        """Legacy identity requirement, refusing instead of silently aggregating."""

        episode_column = (
            "episode_id"
            if "episode_id" in frame.columns
            else "episode"
            if "episode" in frame.columns
            else None
        )
        if episode_column is None:
            raise EpisodeIdentityError(
                f"{root}: paper episode rows require episode or episode_id"
            )
        required = [*group_columns, "checkpoint", "eval_step", "run_seed", "seed", episode_column]
        missing = [column for column in required if column not in frame.columns]
        if missing:
            raise EpisodeIdentityError(f"{root}: paper episode rows are missing identifiers: {missing}")
        blank = [
            column
            for column in required
            if frame[column].isna().any() or (frame[column].astype(str).str.strip() == "").any()
        ]
        if blank:
            raise EpisodeIdentityError(
                f"{root}: paper episode identifiers contain missing values: {blank}"
            )
        duplicated = frame.duplicated(required, keep=False)
        if bool(duplicated.any()):
            sample = frame.loc[duplicated, required].head(3).to_dict("records")
            raise EpisodeIdentityError(
                f"{root}: duplicate paper episode identities: {sample}; the same episode "
                "would be counted twice in a mean"
            )
        return episode_column

    def _classify_columns(self, frame: pd.DataFrame) -> tuple[list[str], list[str]]:
        """Split candidate metric columns from columns that hold no numeric cell at all."""

        metrics: list[str] = []
        non_numeric: list[str] = []
        for column in frame.columns:
            if column in _NON_METRIC:
                continue
            numeric = pd.to_numeric(frame[column], errors="coerce")
            if int(numeric.notna().sum()) == 0:
                non_numeric.append(str(column))
            else:
                metrics.append(str(column))
        return metrics, non_numeric

    # Records -------------------------------------------------------------------------

    def _emit_metric_records(
        self,
        result: ReadResult,
        run: RunRecord,
        frame: pd.DataFrame,
        *,
        group_columns: list[str],
        episode_column: str,
        metric_columns: list[str],
    ) -> None:
        """One episode-level record per (row, metric), with its exact source location."""

        for _, row in frame.iterrows():
            method_id = "|".join(str(row[column]) for column in group_columns)
            eval_step_raw = row["eval_step"]
            try:
                x_value: float | int | None = int(str(eval_step_raw))
            except (TypeError, ValueError):
                x_value = None
                run.warnings.append(f"eval_step {eval_step_raw!r} is not an integer step")
            source_file = str(row["__source_file__"])
            source_row = int(row["__source_row__"])
            for metric in metric_columns:
                raw = row[metric]
                measured = self._measure(raw, metric)
                result.metric_records.append(
                    MetricRecord(
                        run_id=run.run_id,
                        method_id=method_id,
                        metric_name=str(metric),
                        value=measured,
                        x_kind=XKind.CHECKPOINT_STEP,
                        x_value=x_value,
                        phase=Phase.EVALUATION,
                        aggregation_level=AggregationLevel.EPISODE,
                        training_replicate_id=f"run_seed={row['run_seed']}",
                        checkpoint_id=str(row["checkpoint"]),
                        world_id=None,
                        episode_id=str(row[episode_column]),
                        definition_id=f"{self.name}:{metric}",
                        source_path=source_file,
                        source_row_or_key=f"row={source_row};column={metric}",
                    )
                )

    def _measure(self, raw: Any, metric: str) -> Measured:
        """Distinguish an empty cell, a non-numeric cell and a measured number."""

        if raw is None or (isinstance(raw, float) and np.isnan(raw)):
            return Measured.not_recorded(f"empty_cell:{metric}")
        text = str(raw).strip()
        if not text:
            return Measured.not_recorded(f"empty_cell:{metric}")
        number = pd.to_numeric(pd.Series([text]), errors="coerce").iloc[0]
        if pd.isna(number):
            return Measured.invalid(f"not_numeric:{text!r}")
        value = float(number)
        if not np.isfinite(value):
            return Measured.invalid("non_finite")
        return Measured.ok(value)

    # Legacy reproduction -------------------------------------------------------------

    def _legacy_reproduction(
        self,
        frame: pd.DataFrame,
        *,
        group_columns: list[str],
        metric_columns: list[str],
    ) -> dict[str, Any]:
        """Reproduce both legacy summary levels, with honest uncertainty beside them."""

        seed_group_columns = [*group_columns, "checkpoint", "eval_step", "run_seed"]
        per_seed_rows: list[dict[str, Any]] = []
        per_seed_frame_rows: list[dict[str, Any]] = []
        for group_key, group in frame.groupby(seed_group_columns, dropna=False):
            if not isinstance(group_key, tuple):
                group_key = (group_key,)
            base = {column: _plain(value) for column, value in zip(seed_group_columns, group_key)}
            for metric in metric_columns:
                raw = group[metric]
                numeric = pd.to_numeric(raw, errors="coerce")
                values = numeric.dropna()
                n_missing = int(raw.isna().sum())
                n_invalid = int((numeric.isna() & ~raw.isna()).sum())
                if values.empty:
                    # The legacy path skips such a group entirely; record the skip.
                    per_seed_rows.append(
                        {
                            **base,
                            "metric": metric,
                            "episode_count": 0,
                            "mean": None,
                            "min": None,
                            "max": None,
                            "legacy_std": None,
                            "legacy_ci95": None,
                            "std": Measured.absent(
                                Validity.MISSING_ARTIFACT,
                                "no numeric episode value in this group",
                            ).to_json(),
                            "ci95": Measured.absent(
                                Validity.MISSING_ARTIFACT,
                                "no numeric episode value in this group",
                            ).to_json(),
                            "n_invalid_dropped": n_invalid,
                            "n_missing_dropped": n_missing,
                            "legacy_row_emitted": False,
                        }
                    )
                    continue
                count = int(len(values))
                legacy_std = float(values.std(ddof=1)) if count > 1 else 0.0
                legacy_ci95 = 1.96 * legacy_std / np.sqrt(count) if count > 1 else 0.0
                mean = float(values.mean())
                per_seed_rows.append(
                    {
                        **base,
                        "metric": metric,
                        "episode_count": count,
                        "mean": mean,
                        "min": float(values.min()),
                        "max": float(values.max()),
                        "legacy_std": legacy_std,
                        "legacy_ci95": float(legacy_ci95),
                        "std": (
                            Measured.ok(legacy_std).to_json()
                            if count > 1
                            else _absent_uncertainty(count, "standard deviation").to_json()
                        ),
                        "ci95": (
                            Measured.ok(float(legacy_ci95)).to_json()
                            if count > 1
                            else _absent_uncertainty(count, "confidence interval").to_json()
                        ),
                        "n_invalid_dropped": n_invalid,
                        "n_missing_dropped": n_missing,
                        "legacy_row_emitted": True,
                    }
                )
                per_seed_frame_rows.append(
                    {
                        **base,
                        "metric": metric,
                        "episode_count": count,
                        "mean": mean,
                        "n_invalid_dropped": n_invalid,
                        "n_missing_dropped": n_missing,
                    }
                )

        overall_rows: list[dict[str, Any]] = []
        if per_seed_frame_rows:
            per_seed = pd.DataFrame(per_seed_frame_rows)
            aggregate_columns = [*group_columns, "checkpoint", "eval_step", "metric"]
            for group_key, group in per_seed.groupby(aggregate_columns, dropna=False):
                if not isinstance(group_key, tuple):
                    group_key = (group_key,)
                means = group["mean"].to_numpy(dtype=float)
                counts = group["episode_count"].to_numpy(dtype=int)
                n_seeds = int(len(means))
                legacy_std = float(np.std(means, ddof=1)) if n_seeds > 1 else 0.0
                legacy_ci95 = 1.96 * legacy_std / np.sqrt(n_seeds) if n_seeds > 1 else 0.0
                overall_rows.append(
                    {
                        **{
                            column: _plain(value)
                            for column, value in zip(aggregate_columns, group_key)
                        },
                        "n_seeds": n_seeds,
                        "episode_count": int(np.sum(counts)),
                        "episodes_per_seed_min": int(np.min(counts)),
                        "episodes_per_seed_max": int(np.max(counts)),
                        "mean": float(np.mean(means)),
                        "min": float(np.min(means)),
                        "max": float(np.max(means)),
                        "legacy_std": legacy_std,
                        "legacy_ci95": float(legacy_ci95),
                        "std": (
                            Measured.ok(legacy_std).to_json()
                            if n_seeds > 1
                            else _absent_uncertainty(n_seeds, "across-seed standard deviation").to_json()
                        ),
                        "ci95": (
                            Measured.ok(float(legacy_ci95)).to_json()
                            if n_seeds > 1
                            else _absent_uncertainty(
                                n_seeds, "across-seed confidence interval"
                            ).to_json()
                        ),
                        "n_invalid_dropped": int(group["n_invalid_dropped"].sum()),
                        "n_missing_dropped": int(group["n_missing_dropped"].sum()),
                    }
                )

        return {
            "note": (
                "mean/min/max/episode_count and legacy_std/legacy_ci95 reproduce "
                "tools/analysis/paper_experiment_report.py exactly, including its 0.0 for a "
                "single observation; std/ci95 report the same quantity as an explicit "
                "absence when n == 1, and n_invalid_dropped counts the cells that "
                "pd.to_numeric(errors='coerce').dropna() removed without saying so"
            ),
            "per_seed": per_seed_rows,
            "overall": overall_rows,
        }

    # Run record ----------------------------------------------------------------------

    def _finish_run_record(
        self,
        run: RunRecord,
        result: ReadResult,
        root: Path,
        *,
        group_columns: list[str],
        filename_derived: set[str],
        episodes: pd.DataFrame | None = None,
        method_labels: list[str] | None = None,
    ) -> None:
        """Fill the Section 4.1 fields this family can and cannot evidence."""

        if run.source_paths:
            run.set(
                FIELD_ARTIFACT_LOCATIONS,
                Measured.ok(joined_locations(run.source_paths)),
                evidence=f"{self.name}:file_glob",
            )
        if episodes is not None and method_labels is not None:
            if len(method_labels) == 1:
                run.set(
                    FIELD_ALGORITHM,
                    Measured.ok(method_labels[0]),
                    evidence=f"csv_columns:{group_columns}",
                )
            else:
                run.set(
                    FIELD_ALGORITHM,
                    Measured.unknown(
                        f"root holds {len(method_labels)} distinct method labels: {method_labels}; "
                        "it does not identify one algorithm"
                    ),
                    evidence=f"csv_columns:{group_columns}",
                )
                run.warnings.append(
                    "more than one method label under one root: compare per method, not per root"
                )

            checkpoints = sorted({str(value) for value in episodes["checkpoint"]})
            run.set(
                FIELD_CHECKPOINT_IDENTITY,
                Measured.ok(checkpoints[0])
                if len(checkpoints) == 1
                else Measured.unknown(f"multiple checkpoints in one root: {checkpoints}"),
                evidence="csv_column:checkpoint"
                + (";filename_derived" if "checkpoint" in filename_derived else ""),
            )
            run.set(
                FIELD_CHECKPOINT_SELECTION,
                Measured.unknown(
                    "no checkpoint-selection rule is recorded; eval_step identifies which "
                    "checkpoint was evaluated, not why it was chosen"
                ),
                evidence="not_recorded",
            )
            steps = pd.to_numeric(episodes["eval_step"], errors="coerce").dropna()
            if not steps.empty:
                run.set(
                    FIELD_TRAINING_EXPOSURE,
                    Measured.ok(int(steps.max()), unit="training_team_step"),
                    evidence=(
                        "filename_derived_lower_confidence:paper_eval_episodes_step_<n>.csv"
                        if "eval_step" in filename_derived
                        else "csv_column:eval_step"
                    ),
                )
            run_seeds = sorted({str(value) for value in episodes["run_seed"]})
            eval_seeds = sorted({str(value) for value in episodes["seed"]})
            run.set(
                FIELD_TRAINING_SEED,
                Measured.ok(run_seeds[0])
                if len(run_seeds) == 1
                else Measured.ok("|".join(run_seeds)),
                evidence="csv_column:run_seed"
                + (";filename_derived" if "run_seed" in filename_derived else ""),
            )
            run.set(
                FIELD_EVALUATION_SEED,
                Measured.ok(eval_seeds[0])
                if len(eval_seeds) == 1
                else Measured.ok("|".join(eval_seeds)),
                evidence="csv_column:seed"
                + (";filename_derived" if "seed" in filename_derived else ""),
            )
            if "reward" in episodes.columns:
                run.set(
                    FIELD_REWARD_DEFINITION,
                    Measured.not_recorded(
                        "a 'reward' column exists but its definition, unit and scale are not "
                        "recorded anywhere in the CSV family"
                    ),
                    evidence="csv_column:reward(definition absent)",
                )

        declared, observed = boundary_measures(boundary_semantics({}))
        run.set(FIELD_TERMINATION_DECLARED, declared, evidence="not_recorded:legacy_csv")
        run.set(FIELD_TERMINATION_OBSERVED, observed, evidence="unverified:legacy_csv")
        run.set(
            FIELD_EVALUATION_WORLD,
            Measured.not_recorded(
                "legacy paper rows carry no exogenous-world identity (no dataset hash, no "
                "event realisation, no initial-world configuration): pairing_unverified"
            ),
            evidence="not_recorded:legacy_csv",
        )
        run.set(
            FIELD_COMPLETION_STATUS,
            Measured.unknown(
                "the CSV family records no completion status; a truncated evaluation block "
                "looks exactly like a complete one"
            ),
            evidence="not_recorded:legacy_csv",
        )
        run.set(
            FIELD_STATISTICAL_UNIT,
            Measured.ok(
                "evaluation_episode_of_one_training_replicate;independent_unit=run_seed"
            ),
            evidence="csv_columns:run_seed,episode",
        )
        ensure_identity_fields(
            run,
            reason="not_recorded_in_legacy_paper_csv_family",
            evidence="absent:legacy_paper_csv",
        )
        run.coverage = {"reader": self.name, "reader_version": self.version}
        run.errors.extend(result.errors)
        for warning in result.warnings:
            if warning not in run.warnings:
                run.warnings.append(warning)
