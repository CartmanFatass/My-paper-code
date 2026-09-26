"""Provisional B06 confirmation shell over the frozen B05 learning engine."""

import argparse
import hashlib
import json
import sys
from math import sqrt
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.hmasd_admission import require_admission
from scripts import run_skill_drift_unknown_law_b05 as b05


OBJECT = "unknown_joint_law_b06_confirmation"
STAGE = "confirmation"
SEEDS = (95201, 95202, 95203, 95204, 95205)
SELECTION_SHA256 = "ca32b21255d9bc60efb2c17fb1a7757d506d7fcaa49594db9a5ed9e3d3bd16e5"
PRIMARY_REFERENCE = "fingerprint_full"
SECONDARY_REFERENCE = "fingerprint_recent"
PRIMARY_ENDPOINT = "first64"
SCALE_THRESHOLD = 0.005
T95_DF4 = 2.7764451051977987


def _task_value_series(comparisons_by_seed, endpoint, reference):
    import numpy as np

    expected_seeds = set(SEEDS)
    actual_seeds = [int(row["seed"]) for row in comparisons_by_seed]
    if len(actual_seeds) != len(set(actual_seeds)) or set(actual_seeds) != expected_seeds:
        raise ValueError("confirmation comparisons must cover the five fixed seeds exactly")
    by_seed = {int(row["seed"]): row for row in comparisons_by_seed}
    contrast = f"response_minus_{reference}"
    values = np.array(
        [
            by_seed[seed]["by_endpoint"][endpoint][contrast][
                "task_value_difference"
            ]
            for seed in SEEDS
        ],
        dtype=np.float64,
    )
    if values.shape != (5,) or not np.isfinite(values).all():
        raise ValueError("confirmation paired values must be five finite numbers")
    return values


def _descriptive(values):
    import numpy as np

    values = np.asarray(values, dtype=np.float64)
    return {
        "paired_values": values.tolist(),
        "mean": float(values.mean()),
        "sample_sd": float(values.std(ddof=1)),
    }


def reduce_confirmation(comparisons_by_seed):
    """Reduce five independent block contrasts without another model/evaluator call."""
    primary_values = _task_value_series(
        comparisons_by_seed, PRIMARY_ENDPOINT, PRIMARY_REFERENCE
    )
    primary = _descriptive(primary_values)
    half_width = T95_DF4 * primary["sample_sd"] / sqrt(len(SEEDS))
    lower = primary["mean"] - half_width
    upper = primary["mean"] + half_width
    scale_flag = primary["mean"] >= SCALE_THRESHOLD
    interval_flag = lower > 0.0
    primary.update(
        endpoint=PRIMARY_ENDPOINT,
        contrast=f"response_minus_{PRIMARY_REFERENCE}",
        independent_unit="fresh block",
        degrees_of_freedom=4,
        critical_value=T95_DF4,
        t95_interval=[float(lower), float(upper)],
        scale_threshold=SCALE_THRESHOLD,
        scale_flag=bool(scale_flag),
        interval_lower_above_zero=bool(interval_flag),
        proposed_support=bool(scale_flag and interval_flag),
        small_n_assumption=(
            "Two-sided Student-t interval over five independent block differences; "
            "assumes their population is approximately normal and is not distribution-free."
        ),
    )

    secondary = {}
    for endpoint in ("first64", "full", "late64"):
        for reference in (PRIMARY_REFERENCE, SECONDARY_REFERENCE):
            if endpoint == PRIMARY_ENDPOINT and reference == PRIMARY_REFERENCE:
                continue
            key = f"{endpoint}__response_minus_{reference}"
            secondary[key] = {
                "endpoint": endpoint,
                "contrast": f"response_minus_{reference}",
                **_descriptive(
                    _task_value_series(comparisons_by_seed, endpoint, reference)
                ),
                "role": "descriptive_only",
            }
    return {
        "primary": primary,
        "secondary": secondary,
        "secondary_cannot_replace_primary": True,
    }


def _fixed_selection_bytes(path):
    selection_bytes = Path(path).read_bytes()
    digest = hashlib.sha256(selection_bytes).hexdigest()
    if digest != SELECTION_SHA256:
        raise ValueError(
            f"selection digest mismatch: expected {SELECTION_SHA256}, got {digest}"
        )
    return selection_bytes


def _append_confirmation_reduction(out):
    summary_path = Path(out) / "summary.json"
    summary = json.loads(summary_path.read_bytes())
    reduction = reduce_confirmation(summary["comparisons_by_seed"])
    summary["confirmation_reduction"] = reduction
    summary["proposed_support"] = reduction["primary"]["proposed_support"]
    summary["inference_label"] = "small_n_parametric_paired_block_interval"
    summary.update(b05.resource_fields())
    b05.write_json(summary_path, summary)
    return summary


def _mark_reduction_failure(out, error):
    summary_path = Path(out) / "summary.json"
    try:
        summary = json.loads(summary_path.read_bytes())
    except (OSError, ValueError):
        return
    summary.update(
        status="TECHNICAL_FAILURE",
        reduction_error_type=type(error).__name__,
        reduction_error=str(error),
        **b05.resource_fields(),
    )
    b05.write_json(summary_path, summary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    args = parser.parse_args(argv)
    if tuple(args.seeds) != SEEDS:
        parser.error("seeds/order must equal the prospective B06 declaration")
    try:
        _fixed_selection_bytes(args.selection)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    admission = require_admission(
        __file__, direction="skill_teammate_drift_learning"
    )
    if args.launch_sha != admission["sha"]:
        parser.error("launch-sha must equal admitted source SHA")

    engine_args = SimpleNamespace(
        stage="heldout",
        seeds=list(SEEDS),
        launch_sha=args.launch_sha,
        out=args.out,
        selection=args.selection,
        selection_sha256=SELECTION_SHA256,
    )
    b05.run_stage(
        engine_args,
        admission,
        result_object=OBJECT,
        result_stage=STAGE,
        batch_metadata={
            "schema": "b06-confirmation-v1",
            "fixed_seeds": list(SEEDS),
            "selection_sha256": SELECTION_SHA256,
            "learning_engine": "unknown_law_b05",
            "primary_endpoint": PRIMARY_ENDPOINT,
            "primary_contrast": f"response_minus_{PRIMARY_REFERENCE}",
            "secondary_reference": SECONDARY_REFERENCE,
            "scale_threshold": SCALE_THRESHOLD,
            "t_interval": "two-sided Student-t 95%, df=4",
        },
    )
    try:
        _append_confirmation_reduction(args.out)
    except BaseException as error:
        _mark_reduction_failure(args.out, error)
        raise


if __name__ == "__main__":
    main()
