#!/usr/bin/env python3
"""Outcome-free margin geometry for ``UCOPE-A-TAIL-MARGIN-TARGET-CONTEXT-R01``.

**A/RECON, outcome-free.** Nothing here trains, samples or evaluates anything. It reads only

* the frozen 5-term tail basis and the exact tail value ``beta*``;
* the frozen oracle's beliefs and their probability masses;
* per-policy coefficient vectors already published by the competence object -- its exact tail
  solves ``beta_tail_star`` and its ``WHITENED-10X`` learned tails;

and computes closed-form geometry of the held-out tail decision on ``K_eval = {2,4,6,8}``:

* the **top-two score gap** at each belief and context, at ``beta*``;
* the **flip radius** -- the smallest ``L2`` coefficient perturbation that changes the argmax --
  which for a linear score is ``gap / ||z_top - z_competitor||`` minimised over competitors;
* the **directional derivative** of that gap along the published coefficient error
  ``beta_learned - beta*``, which is exact because the gap is linear in the coefficients;
* the probability mass at risk, i.e. the forced-PROBE tail agreement that a flip costs.

The point of the object is to say *why* ``LINKED-p17_20-c9_100`` is the fragile context, using
only quantities that exist before any remedy is attempted.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    CONTEXTS,
    K_EVAL,
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import (  # noqa: E402
    tail_basis,
)
from experiments.candidates.ucope.competence_first_scout_r01.oracle import (  # noqa: E402
    expected_tail,
    joint_count_probability,
    optimal_tail,
    posterior_short,
)

OBJECT_ID = "UCOPE-A-TAIL-MARGIN-TARGET-CONTEXT-R01"
EVIDENCE_CLASS = "A/RECON"
RECORD_FORMAT = "UCOPE_TAIL_MARGIN_GEOMETRY_R01_V1"
RESOURCE_PREFLIGHT = PROJECT_ROOT / "scripts/hmasd_resource_preflight.py"
MINIMUM_MEMORY_BYTES = 4 * 1024**3
COMPETENCE_RECORD = PROJECT_ROOT / (
    "temp/directions/ucope/exp/competence_whitened_r01_20260903/complete/run-record.json")

BETA_STAR = (0.31, 0.60, 1.35, -1.08, -0.891)
TARGET_CONTEXT_ID = "LINKED-p17_20-c9_100"
AGREEMENT_GATE = Fraction(19, 20)


class RefusedComputation(RuntimeError):
    """Raised before stateful work when a launch condition fails."""


def _numpy():
    import numpy

    return numpy


def admit_memory(receipt: Path) -> dict[str, Any]:
    receipt.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, str(RESOURCE_PREFLIGHT), "admit-memory", "--out", str(receipt)],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if completed.returncode != 0 or not receipt.is_file():
        raise RefusedComputation(
            f"central 4 GiB memory admission failed rc={completed.returncode}")
    value = json.loads(receipt.read_text(encoding="utf-8"))
    if (value.get("passed") is not True
            or int(value.get("available_physical_bytes", 0)) < MINIMUM_MEMORY_BYTES
            or int(value.get("effective_available_bytes", 0)) < MINIMUM_MEMORY_BYTES):
        raise RefusedComputation("central 4 GiB memory admission refused the launch")
    return value


def published_coefficients(path: Path | None = None) -> list[dict[str, Any]]:
    """The competence object's per-policy exact and learned tail vectors."""
    source = Path(path) if path is not None else COMPETENCE_RECORD
    if not source.is_file():
        raise RefusedComputation(f"published competence record missing: {source}")
    record = json.loads(source.read_text(encoding="utf-8"))
    if record.get("object_id") != "UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01":
        raise RefusedComputation("reference is not the competence run record")
    return [
        {
            "seed_id": row["seed_id"],
            "fold_id": int(row["fold_id"]),
            "beta_tail_star": list(row["beta_tail_star"]),
            "beta_tail_whitened_10x": list(row["arms"]["WHITENED-10X"]["beta_tail"]),
            "recorded_minimum_tail_agreement": float(
                row["arms"]["WHITENED-10X"]["competence"]["minimum_tail_agreement"]),
            "recorded_d_learned_tail": float(row["arms"]["WHITENED-10X"]["d_learned_tail"]),
        }
        for row in record["policies"]
    ]


def _basis(belief: float, period: int):
    numpy = _numpy()
    return numpy.asarray(tail_basis(belief=belief, period=period), dtype=numpy.float64)


def belief_grid():
    """Every (context, forced-PROBE belief) cell the agreement gate is a minimum over."""
    for context in CONTEXTS:
        link, p, cost = context
        cell = context_id(context)
        for count in range(7):
            belief = posterior_short(link, p, count)
            mass = (joint_count_probability("SHORT", p, count)
                    + joint_count_probability("LONG", p, count))
            yield cell, context, count, belief, mass


def cell_geometry(belief: Fraction, beta) -> dict[str, Any]:
    """Top-two gap, flip radius and the competitor that binds, for a linear tail score."""
    numpy = _numpy()
    beta = numpy.asarray(beta, dtype=numpy.float64)
    bases = {period: _basis(float(belief), period) for period in K_EVAL}
    scores = {period: float(bases[period] @ beta) for period in K_EVAL}
    ranked = sorted((value, -index, period)
                    for index, (period, value) in enumerate(scores.items()))
    top = ranked[-1][2]
    runner_up = ranked[-2][2]
    gap = scores[top] - scores[runner_up]
    radii = {}
    for period in K_EVAL:
        if period == top:
            continue
        difference = bases[top] - bases[period]
        norm = float(numpy.linalg.norm(difference))
        radii[period] = (scores[top] - scores[period]) / norm if norm > 0 else float("inf")
    binding = min(radii, key=radii.get)
    return {
        "argmax_period": int(top),
        "runner_up_period": int(runner_up),
        "scores": {str(period): scores[period] for period in K_EVAL},
        "top_two_gap": gap,
        "flip_radius_l2": float(radii[binding]),
        "flip_binding_period": int(binding),
        "flip_direction_unit": [
            float(value) for value in
            (bases[binding] - bases[top]) / float(numpy.linalg.norm(bases[binding] - bases[top]))
        ],
    }


def directional_derivative(belief: Fraction, top: int, competitor: int, direction) -> float:
    """d/dt of the (top - competitor) score gap along a unit direction; exact, the gap is linear."""
    numpy = _numpy()
    difference = _basis(float(belief), top) - _basis(float(belief), competitor)
    return float(difference @ numpy.asarray(direction, dtype=numpy.float64))


def held_out_direction_identity() -> dict[str, Any]:
    """Every held-out decision direction is exactly half a training-support one.

    For the frozen basis ``(1, b, k, b*k, k^2)`` with ``k = period/9``, at any belief

        ``z(b, j) - z(b, j+2) == (z(b, j-1) - z(b, j+3)) / 2``

    exactly, because the first two coordinates cancel and the remaining three are affine and
    quadratic in ``k`` with an evenly spaced pair. Each held-out pair ``(j, j+2)`` from
    ``K_eval`` therefore has a ``K_train`` witness ``(j-1, j+3)``: (2,4)->(1,5), (4,6)->(3,7),
    (6,8)->(5,9). This is what lets a margin-aware objective control the held-out margin
    **without training on any held-out period**, which the frozen odd/even separation forbids.
    """
    numpy = _numpy()
    rows = []
    worst = 0.0
    for cell, context, count, belief, mass in belief_grid():
        for first, second in zip(K_EVAL[:-1], K_EVAL[1:]):
            witness = (first - 1, second + 1)
            held_out = _basis(float(belief), first) - _basis(float(belief), second)
            training = (_basis(float(belief), witness[0])
                        - _basis(float(belief), witness[1])) / 2.0
            error = float(numpy.abs(held_out - training).max())
            worst = max(worst, error)
            rows.append({
                "context_id": cell, "count": count, "belief": float(belief),
                "held_out_pair": [int(first), int(second)],
                "training_witness_pair": [int(witness[0]), int(witness[1])],
                "identity_max_abs_error": error,
                "held_out_direction_norm": float(numpy.linalg.norm(held_out)),
                "training_direction_norm": float(numpy.linalg.norm(held_out) * 2.0),
            })
    return {
        "statement": ("z(b, j) - z(b, j+2) == (z(b, j-1) - z(b, j+3)) / 2 for every held-out "
                      "pair and belief; the witness pairs lie entirely in K_train"),
        "held_out_support": list(K_EVAL),
        "witness_pairs": [[int(a - 1), int(b + 1)] for a, b in zip(K_EVAL[:-1], K_EVAL[1:])],
        "maximum_identity_error": worst,
        "cells": rows,
    }


def truth_geometry() -> dict[str, Any]:
    """The geometry at beta*: which cells are tight and how much mass sits on them."""
    numpy = _numpy()
    contexts: dict[str, Any] = {}
    for cell, context, count, belief, mass in belief_grid():
        row = contexts.setdefault(cell, {"cells": {}, "context_id": cell})
        geometry = cell_geometry(belief, BETA_STAR)
        oracle_period = int(optimal_tail(K_EVAL, belief)[0])
        exact_value = float(expected_tail(geometry["argmax_period"], belief))
        row["cells"][str(count)] = {
            "belief": float(belief),
            "mass": float(mass),
            "oracle_period": oracle_period,
            "basis_argmax_period": geometry["argmax_period"],
            "basis_represents_truth": geometry["argmax_period"] == oracle_period,
            "basis_score_vs_expected_tail_max_abs": abs(
                geometry["scores"][str(geometry["argmax_period"])] - exact_value),
            "top_two_gap": geometry["top_two_gap"],
            "flip_radius_l2": geometry["flip_radius_l2"],
            "flip_binding_period": geometry["flip_binding_period"],
            "runner_up_period": geometry["runner_up_period"],
        }
    for cell, row in contexts.items():
        cells = row["cells"]
        tightest = min(cells, key=lambda key: cells[key]["flip_radius_l2"])
        row["minimum_flip_radius_l2"] = cells[tightest]["flip_radius_l2"]
        row["minimum_flip_radius_count"] = int(tightest)
        row["minimum_top_two_gap"] = min(item["top_two_gap"] for item in cells.values())
        row["mass_weighted_flip_radius"] = float(sum(
            item["mass"] * item["flip_radius_l2"] for item in cells.values()))
        row["is_target_context"] = cell == TARGET_CONTEXT_ID
        row["basis_exact_everywhere"] = all(item["basis_represents_truth"] for item in cells.values())
    ranking = sorted(contexts, key=lambda cell: contexts[cell]["minimum_flip_radius_l2"])
    return {
        "contexts": contexts,
        "fragility_ranking": ranking,
        "most_fragile_context": ranking[0],
        "target_context_rank": ranking.index(TARGET_CONTEXT_ID) + 1,
    }


def policy_geometry(policy: dict[str, Any], truth: dict[str, Any]) -> dict[str, Any]:
    """Where each published tail sits relative to the flip radii, and what it costs."""
    numpy = _numpy()
    star = numpy.asarray(BETA_STAR, dtype=numpy.float64)
    result: dict[str, Any] = {
        "seed_id": policy["seed_id"], "fold_id": policy["fold_id"],
        "recorded_minimum_tail_agreement": policy["recorded_minimum_tail_agreement"],
        "recorded_d_learned_tail": policy["recorded_d_learned_tail"],
        "vectors": {},
    }
    for label, key in (("EXACT-SOLVE", "beta_tail_star"),
                       ("WHITENED-10X", "beta_tail_whitened_10x")):
        beta = numpy.asarray(policy[key], dtype=numpy.float64)
        error = beta - star
        error_norm = float(numpy.linalg.norm(error))
        direction = (error / error_norm) if error_norm > 0 else numpy.zeros_like(error)
        contexts: dict[str, Any] = {}
        agreement = Fraction(0)
        total_mass = Fraction(0)
        for cell, context, count, belief, mass in belief_grid():
            entry = contexts.setdefault(cell, {"cells": {}, "flipped_counts": [],
                                               "mass_lost": 0.0})
            truth_cell = truth["contexts"][cell]["cells"][str(count)]
            geometry = cell_geometry(belief, beta)
            flipped = geometry["argmax_period"] != truth_cell["oracle_period"]
            derivative = directional_derivative(
                belief, truth_cell["basis_argmax_period"], truth_cell["flip_binding_period"],
                direction)
            entry["cells"][str(count)] = {
                "selected_period": geometry["argmax_period"],
                "oracle_period": truth_cell["oracle_period"],
                "flipped": flipped,
                "top_two_gap": geometry["top_two_gap"],
                "truth_flip_radius_l2": truth_cell["flip_radius_l2"],
                "coefficient_error_l2": error_norm,
                "error_exceeds_flip_radius": error_norm > truth_cell["flip_radius_l2"],
                "margin_directional_derivative": derivative,
                "predicted_gap_at_error": (
                    truth_cell["top_two_gap"] + derivative * error_norm),
            }
            if flipped:
                entry["flipped_counts"].append(int(count))
                entry["mass_lost"] += float(mass)
            else:
                agreement += mass
            total_mass += mass
        per_context_agreement = {}
        for cell in contexts:
            kept = Fraction(0)
            whole = Fraction(0)
            for other_cell, context, count, belief, mass in belief_grid():
                if other_cell != cell:
                    continue
                whole += mass
                if not contexts[cell]["cells"][str(count)]["flipped"]:
                    kept += mass
            per_context_agreement[cell] = float(kept)
            contexts[cell]["agreement"] = float(kept)
            contexts[cell]["agreement_within_gate"] = kept >= AGREEMENT_GATE
        result["vectors"][label] = {
            "beta": [float(value) for value in beta],
            "coefficient_error_l2": error_norm,
            "coefficient_error_max_abs": float(numpy.abs(error).max()),
            "unit_direction": [float(value) for value in direction],
            "contexts": contexts,
            "minimum_agreement": min(per_context_agreement.values()),
            "minimum_agreement_context": min(per_context_agreement, key=per_context_agreement.get),
            "contexts_below_gate": sum(
                1 for cell in contexts if not contexts[cell]["agreement_within_gate"]),
            "total_flipped_cells": sum(len(row["flipped_counts"]) for row in contexts.values()),
        }
    return result


def run_geometry(output_root: str | Path,
                 competence_record: str | Path | None = None) -> Path:
    output = Path(output_root).resolve()
    if output.exists():
        raise RefusedComputation(f"output root is create-once: {output}")
    output.mkdir(parents=True)
    admission = admit_memory(output / "preflight.json")
    started = {"wall": time.perf_counter(), "cpu": time.process_time()}

    published = published_coefficients(
        Path(competence_record) if competence_record else None)
    truth = truth_geometry()
    policies = [policy_geometry(policy, truth) for policy in published]

    record = {
        "format": RECORD_FORMAT, "schema_version": 1, "object_id": OBJECT_ID,
        "evidence_class": EVIDENCE_CLASS,
        "purpose": ("outcome-free margin geometry of the held-out tail decision; no training, "
                    "no sampling, no evaluation, no learner"),
        "beta_star": list(BETA_STAR),
        "held_out_support": list(K_EVAL),
        "agreement_gate": float(AGREEMENT_GATE),
        "target_context_id": TARGET_CONTEXT_ID,
        "source_of_published_vectors": str(
            Path(competence_record) if competence_record else COMPETENCE_RECORD),
        "admission": admission,
        "truth_geometry": truth,
        "held_out_direction_identity": held_out_direction_identity(),
        "policies": policies,
        "wall_seconds": time.perf_counter() - started["wall"],
        "cpu_seconds": time.process_time() - started["cpu"],
    }
    destination = output / "margin-geometry.json"
    destination.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return destination


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", allow_abbrev=False)
    run.add_argument("--output-root", required=True)
    run.add_argument("--competence-record", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        path = run_geometry(args.output_root, args.competence_record)
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        print(json.dumps({
            "path": str(path),
            "most_fragile_context": record["truth_geometry"]["most_fragile_context"],
            "target_context_rank": record["truth_geometry"]["target_context_rank"],
        }, sort_keys=True))
    except (OSError, ValueError, TypeError, subprocess.SubprocessError,
            RefusedComputation) as exc:
        print(f"UCOPE tail-margin geometry stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
