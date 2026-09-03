#!/usr/bin/env python3
"""Runner for ``UCOPE-A-TRAINING-TARGET-DIAGNOSTIC-R01``.

Object
------
``UCOPE-A-TRAINING-TARGET-DIAGNOSTIC-R01``, evidence class ``A/RECON`` (diagnostic).
Frozen by ``docs/research/candidates/ucope/UCOPE_TRAINING_TARGET_DIAGNOSTIC_R01_CARD_20260902.md``,
written 2026-09-02 and run 2026-09-03 after the owner's prediction was recorded.

Question: why does the learned Bellman coefficient vector settle far from the optimum its own
basis represents exactly, and why does an order-of-magnitude change of schedule not move it?

The card's four measurements, implemented exactly as written there:

* ``X1`` the tail objective's exact optimum and the learner's stationarity;
* ``X2`` the root target package rebuilt three ways;
* ``X4`` fold coupling;
* ``X3`` optimization versus objective, run only when X1 calls for it.

This object is outcome-free: no scientific arm is trained at ladder scale, no polarity is
produced, no published record is altered. It reads freshly generated populations from the frozen
host and the final parameters in the published R02 checkpoints, which is what
``ladder.validate_complete`` already reads.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fractions import Fraction  # noqa: E402

from experiments.candidates.ucope.competence_first_scout_r01.checkpoint import (  # noqa: E402
    load_checkpoint,
    restore_checkpoint,
)
from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    B1_SEEDS,
    CONTEXTS,
    K_EVAL,
    K_TRAIN,
    ScoutConfig,
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.host import (  # noqa: E402
    generate_population,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import (  # noqa: E402
    root_basis,
    tail_basis,
    tensors_for_record,
)
from experiments.candidates.ucope.competence_first_scout_r01.oracle import (  # noqa: E402
    build_oracle,
    expected_tail,
)
from experiments.candidates.ucope.competence_first_scout_r01.training import (  # noqa: E402
    _canonical_rows,
    _cyclic_batch,
    _step,
    _tail_batch,
)

OBJECT_ID = "UCOPE-A-TRAINING-TARGET-DIAGNOSTIC-R01"
EVIDENCE_CLASS = "A/RECON"
RESULT_FORMAT = "UCOPE_TRAINING_TARGET_DIAGNOSTIC_R01_RECORD_V1"
CARD = "docs/research/candidates/ucope/UCOPE_TRAINING_TARGET_DIAGNOSTIC_R01_CARD_20260902.md"
RESOURCE_PREFLIGHT = PROJECT_ROOT / "scripts/hmasd_resource_preflight.py"
MINIMUM_MEMORY_BYTES = 4 * 1024**3

# The analytic optimum the instrumentation check verified lies exactly in the frozen 5-term basis.
BETA_STAR = (0.31, 0.60, 1.35, -1.08, -0.891)
# Thresholds frozen in card section 4. They are not arguments.
EPSILON = 0.10
GRADIENT_RATIO = 10.0
# Published run whose final parameters the diagnostic reads.
PUBLISHED_RUN = PROJECT_ROOT / "temp/directions/ucope/exp/exposure_ladder_r02_rung2_20260902/complete"
LADDER_ARMS = ("FT-XF-FLEX", "FT-XF-BC")
# The reading rule's beta comparison is defined only for the arm whose trained model IS the
# 5-term linear function; FT-XF-FLEX carries a paired residual and is reported descriptively.
LINEAR_ARM = "FT-XF-BC"


class DiagnosticRefusal(RuntimeError):
    """Raised before stateful work when a launch condition fails."""


def _numpy():
    import numpy

    return numpy


def _torch():
    import torch

    return torch


def admit_memory(receipt: str | Path) -> dict[str, Any]:
    """Central 4 GiB physical + effective admission. A launch condition; it refuses."""
    path = Path(receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, str(RESOURCE_PREFLIGHT), "admit-memory", "--out", str(path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not path.is_file():
        raise DiagnosticRefusal(
            f"central 4 GiB memory admission failed rc={completed.returncode}: {completed.stderr.strip()}"
        )
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or value.get("passed") is not True
        or value.get("physical_floor_pass") is not True
        or value.get("effective_floor_pass") is not True
        or int(value.get("available_physical_bytes", 0)) < MINIMUM_MEMORY_BYTES
        or int(value.get("effective_available_bytes", 0)) < MINIMUM_MEMORY_BYTES
    ):
        raise DiagnosticRefusal("central 4 GiB memory admission refused the launch")
    return value


def _configure_topology(thread_cap: int) -> None:
    torch = _torch()
    if type(thread_cap) is not int or not 1 <= thread_cap <= 16:
        raise DiagnosticRefusal("thread cap must be an integer between 1 and 16")
    torch.set_num_threads(thread_cap)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)


def topology_record(thread_cap: int) -> dict[str, Any]:
    torch = _torch()
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "torch_intraop_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
        "thread_cap_requested": thread_cap,
        "deterministic_algorithms": True,
        "executable": sys.executable,
    }


# ---------------------------------------------------------------------------
# Shared linear algebra
# ---------------------------------------------------------------------------


def _solve(design, targets):
    """Exact least-squares solution of the normal equations, in float64."""
    numpy = _numpy()
    design = numpy.asarray(design, dtype=numpy.float64)
    targets = numpy.asarray(targets, dtype=numpy.float64)
    beta, _residuals, _rank, _sv = numpy.linalg.lstsq(design, targets, rcond=None)
    return beta


def _gram_spectrum(design):
    numpy = _numpy()
    design = numpy.asarray(design, dtype=numpy.float64)
    gram = design.T @ design / design.shape[0]
    eigenvalues = numpy.linalg.eigvalsh(gram)
    smallest = float(eigenvalues.min())
    largest = float(eigenvalues.max())
    return {
        "gram_condition_number": largest / smallest if smallest > 0 else None,
        "gram_smallest_eigenvalue": smallest,
        "gram_largest_eigenvalue": largest,
    }


def _mse_gradient_infinity_norm(design, targets, beta):
    """Infinity norm of the full-data gradient of the frozen MSE objective at beta."""
    numpy = _numpy()
    design = numpy.asarray(design, dtype=numpy.float64)
    targets = numpy.asarray(targets, dtype=numpy.float64)
    beta = numpy.asarray(beta, dtype=numpy.float64)
    residual = design @ beta - targets
    gradient = 2.0 * (design.T @ residual) / design.shape[0]
    return float(numpy.abs(gradient).max())


def _tail_design(rows):
    design = [tail_basis(belief=float(row.belief_short), period=row.behavior_period) for row in rows]
    targets = [float(row.tail_return) for row in rows]
    return design, targets


def _root_design(rows):
    design = []
    for row in rows:
        probe = row.behavior_action == "PROBE"
        design.append(
            root_basis(
                action_probe=probe,
                period=0 if probe else row.behavior_period,
                cost=float(row.total_cost),
                linked=row.link == "LINKED",
                reliability=float(row.reliability),
            )
        )
    return design


# ---------------------------------------------------------------------------
# Tail value sources for X2
# ---------------------------------------------------------------------------


def _oracle_tail_value() -> Any:
    cache: dict[tuple[Fraction, int], float] = {}

    def value(belief: Fraction, period: int) -> float:
        key = (belief, period)
        if key not in cache:
            cache[key] = float(expected_tail(period, belief))
        return cache[key]

    return value


def _linear_tail_value(beta) -> Any:
    cache: dict[tuple[Fraction, int], float] = {}

    def value(belief: Fraction, period: int) -> float:
        key = (belief, period)
        if key not in cache:
            basis = tail_basis(belief=float(belief), period=period)
            cache[key] = float(sum(coefficient * element for coefficient, element in zip(beta, basis)))
        return cache[key]

    return value


def _module_tail_value(module) -> Any:
    torch = _torch()

    def value_batch(records_periods):
        pairs = [
            tensors_for_record(record, stage="tail", action_probe=False, period=period, belief=float(belief))
            for record, belief, period in records_periods
        ]
        x = torch.stack([pair[0] for pair in pairs])
        z = torch.stack([pair[1] for pair in pairs])
        with torch.no_grad():
            return [float(item) for item in module(x, z).tolist()]

    return value_batch


def _root_targets_from_tail(rows, *, tail_value=None, tail_batch=None):
    """Exactly the frozen target package: probe_primitive + max over K_TRAIN of Q_tail."""
    targets = []
    if tail_batch is not None:
        requests = []
        index_map = []
        for index, row in enumerate(rows):
            if row.behavior_action == "IMMEDIATE":
                continue
            for period in K_TRAIN:
                requests.append((row, row.belief_short, period))
                index_map.append(index)
        values = tail_batch(requests) if requests else []
        best: dict[int, float] = {}
        for position, index in enumerate(index_map):
            value = values[position]
            if index not in best or value > best[index]:
                best[index] = value
        for index, row in enumerate(rows):
            if row.behavior_action == "IMMEDIATE":
                targets.append(float(row.tail_return))
            else:
                targets.append(float(row.probe_primitive) + best[index])
        return targets
    for row in rows:
        if row.behavior_action == "IMMEDIATE":
            targets.append(float(row.tail_return))
        else:
            targets.append(
                float(row.probe_primitive)
                + max(tail_value(row.belief_short, period) for period in K_TRAIN)
            )
    return targets


def _implied_root_actions(beta_root) -> dict[str, str]:
    """Rank PROBE against IMMEDIATE:k over K_eval exactly as evaluate_policy does."""
    actions = {}
    for context in CONTEXTS:
        link, reliability, cost = context
        labels = ("PROBE", *(f"IMMEDIATE:{period}" for period in K_EVAL))
        bases = [root_basis(action_probe=True, period=0, cost=float(cost), linked=link == "LINKED", reliability=float(reliability))]
        bases += [
            root_basis(action_probe=False, period=period, cost=float(cost), linked=link == "LINKED", reliability=float(reliability))
            for period in K_EVAL
        ]
        values = [sum(coefficient * element for coefficient, element in zip(beta_root, basis)) for basis in bases]
        ranked = sorted((value, -index, label) for index, (label, value) in enumerate(zip(labels, values)))
        selected = ranked[-1][2]
        actions[context_id(context)] = "PROBE" if selected == "PROBE" else "IMMEDIATE"
    return actions


def oracle_root_actions() -> dict[str, str]:
    return {cell: row["action"] for cell, row in build_oracle().items()}


# ---------------------------------------------------------------------------
# Published parameters
# ---------------------------------------------------------------------------


def published_policies(run_root: Path, config: ScoutConfig):
    """Final tail models of the published run, per arm/seed/fold. Validator-readable fields."""
    policies = {}
    for arm in LADDER_ARMS:
        for seed in config.seed_ids:
            for fold in (0, 1):
                path = (
                    run_root / "checkpoints" / arm / seed / f"fold-{fold}"
                    / f"root-{config.root_updates:04d}.pt"
                )
                if not path.is_file():
                    raise DiagnosticRefusal(f"published checkpoint missing: {path}")
                payload = load_checkpoint(path)
                policies[(arm, seed, fold)] = payload
    return policies


# ---------------------------------------------------------------------------
# X1, X2, X3, X4
# ---------------------------------------------------------------------------


def measurement_x1(populations, policies, config: ScoutConfig) -> dict[str, Any]:
    numpy = _numpy()
    rows_out = []
    for seed in config.seed_ids:
        population = populations[seed]
        for fold in (0, 1):
            tail_rows = _canonical_rows(population, fold=fold, tail=True)
            design, targets = _tail_design(tail_rows)
            beta_tail_star = _solve(design, targets)
            spectrum = _gram_spectrum(design)
            record = {
                "seed_id": seed,
                "fold_id": fold,
                "tail_rows": len(tail_rows),
                "beta_tail_star": [float(value) for value in beta_tail_star],
                "beta_star": list(BETA_STAR),
                "d_objective": float(numpy.abs(beta_tail_star - numpy.asarray(BETA_STAR)).max()),
                "g_star": _mse_gradient_infinity_norm(design, targets, BETA_STAR),
                "g_at_beta_tail_star": _mse_gradient_infinity_norm(design, targets, beta_tail_star),
                "published": {},
            }
            record.update(spectrum)
            for arm in LADDER_ARMS:
                payload = policies[(arm, seed, fold)]
                beta_published = [float(value) for value in payload["tail_state"]["beta"].tolist()]
                record["published"][arm] = {
                    "beta_published": beta_published,
                    "d_learned": float(
                        numpy.abs(numpy.asarray(beta_published) - beta_tail_star).max()
                    ),
                    "d_from_beta_star": float(
                        numpy.abs(numpy.asarray(beta_published) - numpy.asarray(BETA_STAR)).max()
                    ),
                    "g_learned": _mse_gradient_infinity_norm(design, targets, beta_published),
                    "model_is_exactly_the_linear_basis": arm == LINEAR_ARM,
                }
            rows_out.append(record)
    return {
        "statement": (
            "exact least-squares optimum of the frozen tail objective on the realized design, the "
            "Gram spectrum of that design, and the full-data gradient of the same objective at "
            "beta*, at that optimum, and at each published final tail beta"
        ),
        "epsilon": EPSILON,
        "gradient_ratio_threshold": GRADIENT_RATIO,
        "linear_arm": LINEAR_ARM,
        "rows": rows_out,
    }


def measurement_x2(populations, policies, config: ScoutConfig) -> dict[str, Any]:
    oracle_vector = oracle_root_actions()
    rows_out = []
    for seed in config.seed_ids:
        population = populations[seed]
        for fold in (0, 1):
            root_rows = _canonical_rows(population, fold=fold, tail=False)
            tail_rows = _canonical_rows(population, fold=fold, tail=True)
            design = _root_design(root_rows)
            tail_design, tail_targets = _tail_design(tail_rows)
            beta_tail_star = _solve(tail_design, tail_targets)
            sources: dict[str, Any] = {
                "a_oracle_tail": _root_targets_from_tail(root_rows, tail_value=_oracle_tail_value()),
                "b_beta_tail_star": _root_targets_from_tail(
                    root_rows, tail_value=_linear_tail_value(beta_tail_star)
                ),
            }
            for arm in LADDER_ARMS:
                payload = policies[(arm, seed, fold)]
                _root_model, tail_model, _ro, _to = restore_checkpoint(payload)
                sources[f"c_published_{arm}"] = _root_targets_from_tail(
                    root_rows, tail_batch=_module_tail_value(tail_model)
                )
            record = {"seed_id": seed, "fold_id": fold, "root_rows": len(root_rows), "sources": {}}
            for name, targets in sources.items():
                beta_root = _solve(design, targets)
                actions = _implied_root_actions(beta_root)
                record["sources"][name] = {
                    "beta_root_star": [float(value) for value in beta_root],
                    "implied_root_actions": actions,
                    "matches_oracle_root_vector": actions == oracle_vector,
                    "probe_contexts": sorted(cell for cell, action in actions.items() if action == "PROBE"),
                }
            rows_out.append(record)
    return {
        "statement": (
            "the frozen root target package rebuilt from the oracle tail, from the tail objective's "
            "own optimum, and from each published tail, each solved exactly and read for its "
            "implied root action vector"
        ),
        "oracle_root_actions": oracle_vector,
        "rows": rows_out,
    }


def measurement_x4(populations, config: ScoutConfig) -> dict[str, Any]:
    numpy = _numpy()
    rows_out = []
    for seed in config.seed_ids:
        population = populations[seed]
        for fold in (0, 1):
            own = _canonical_rows(population, fold=fold, tail=True)  # rows the tail trains on
            other = _canonical_rows(population, fold=1 - fold, tail=True)  # the root's own fold
            beta_own = _solve(*_tail_design(own))
            beta_other = _solve(*_tail_design(other))
            rows_out.append({
                "seed_id": seed,
                "fold_id": fold,
                "tail_training_fold": 1 - fold,
                "beta_on_tail_training_fold": [float(value) for value in beta_own],
                "beta_on_root_fold": [float(value) for value in beta_other],
                "max_abs_difference": float(numpy.abs(beta_own - beta_other).max()),
            })
    return {
        "statement": (
            "the tail objective's exact optimum recomputed on the fold the tail trains on and on "
            "the fold the root trains on, to size the fold-coupling channel"
        ),
        "rows": rows_out,
    }


def measurement_x3(populations, policies, config: ScoutConfig, *, seed: str, fold: int, arm: str) -> dict[str, Any]:
    """Continue the frozen tail loop with the published optimizer state for 10x the rung budget."""
    numpy = _numpy()
    population = populations[seed]
    tail_rows = _canonical_rows(population, fold=fold, tail=True)
    design, targets = _tail_design(tail_rows)
    beta_tail_star = _solve(design, targets)
    payload = policies[(arm, seed, fold)]
    _root_model, tail_model, _root_optimizer, tail_optimizer = restore_checkpoint(payload)
    start_updates = int(payload["tail_updates"])
    extra = 10 * config.tail_updates
    activity = {
        "tail_gradient_norm_sum": 0.0,
        "tail_gradient_norm_max": 0.0,
        "tail_clipping_events": 0,
        "nonfinite_events": 0,
    }
    beta_before = [float(value) for value in tail_model.state_dict()["beta"].tolist()]
    started = time.perf_counter()
    for offset in range(extra):
        batch = _cyclic_batch(tail_rows, start_updates + offset, config.batch_size)
        x, z, y = _tail_batch(batch)
        _step(tail_model, tail_optimizer, x, z, y, activity, "tail")
    elapsed = time.perf_counter() - started
    beta_after = [float(value) for value in tail_model.state_dict()["beta"].tolist()]
    return {
        "statement": (
            "the frozen tail step loop continued from the published parameters and optimizer state "
            "for ten times the rung-2 tail budget, against the exact least-squares solve"
        ),
        "arm_id": arm,
        "seed_id": seed,
        "fold_id": fold,
        "start_tail_updates": start_updates,
        "extra_tail_updates": extra,
        "wall_seconds": elapsed,
        "beta_before": beta_before,
        "beta_after": beta_after,
        "beta_tail_star": [float(value) for value in beta_tail_star],
        "d_before": float(numpy.abs(numpy.asarray(beta_before) - beta_tail_star).max()),
        "d_after": float(numpy.abs(numpy.asarray(beta_after) - beta_tail_star).max()),
        "g_before": _mse_gradient_infinity_norm(design, targets, beta_before),
        "g_after": _mse_gradient_infinity_norm(design, targets, beta_after),
        "g_at_beta_tail_star": _mse_gradient_infinity_norm(design, targets, beta_tail_star),
        "clipping_events": activity["tail_clipping_events"],
        "nonfinite_events": activity["nonfinite_events"],
    }


# ---------------------------------------------------------------------------
# Reading rule (card section 4), applied verbatim
# ---------------------------------------------------------------------------


def apply_reading_rule(x1: dict[str, Any], x2: dict[str, Any]) -> dict[str, Any]:
    numbers: dict[str, Any] = {}
    d_objective = max(row["d_objective"] for row in x1["rows"])
    numbers["max_d_objective"] = d_objective
    numbers["max_d_learned_linear_arm"] = max(
        row["published"][LINEAR_ARM]["d_learned"] for row in x1["rows"]
    )
    numbers["max_g_star"] = max(row["g_star"] for row in x1["rows"])
    numbers["min_g_learned_linear_arm"] = min(
        row["published"][LINEAR_ARM]["g_learned"] for row in x1["rows"]
    )
    numbers["gradient_ratios_linear_arm"] = [
        row["published"][LINEAR_ARM]["g_learned"] / row["g_star"] if row["g_star"] > 0 else None
        for row in x1["rows"]
    ]
    oracle_a = [row["sources"]["a_oracle_tail"]["matches_oracle_root_vector"] for row in x2["rows"]]
    oracle_b = [row["sources"]["b_beta_tail_star"]["matches_oracle_root_vector"] for row in x2["rows"]]
    published_c = {
        arm: [row["sources"][f"c_published_{arm}"]["matches_oracle_root_vector"] for row in x2["rows"]]
        for arm in LADDER_ARMS
    }
    numbers["x2_oracle_tail_matches"] = oracle_a
    numbers["x2_beta_tail_star_matches"] = oracle_b
    numbers["x2_published_matches"] = published_c

    # D4 first: the root re-solve with the exact oracle tail.
    if not all(oracle_a):
        return {"branch": "D4", "label": "TARGET_PACKAGE_CEILING", "numbers": numbers}
    if d_objective > EPSILON:
        return {"branch": "D1", "label": "OBJECTIVE_FIXED_POINT_DIFFERS", "numbers": numbers}
    ratios = [value for value in numbers["gradient_ratios_linear_arm"] if value is not None]
    if (
        numbers["max_d_learned_linear_arm"] > EPSILON
        and ratios
        and all(value > GRADIENT_RATIO for value in ratios)
    ):
        return {"branch": "D2", "label": "OPTIMIZATION_SHORTFALL", "numbers": numbers}
    if numbers["max_d_learned_linear_arm"] <= EPSILON and all(oracle_b) and not all(published_c[LINEAR_ARM]):
        return {"branch": "D3", "label": "TAIL_CONVERGED_ROOT_INHERITS", "numbers": numbers}
    return {"branch": "D5", "label": "NONE_OF_THESE", "numbers": numbers}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_diagnostic(output_root: str | Path, *, thread_cap: int = 4) -> Path:
    output = Path(output_root).resolve()
    if output.exists():
        raise DiagnosticRefusal(f"output root is create-once: {output}")
    output.mkdir(parents=True)
    admission = admit_memory(output / "preflight.json")
    _configure_topology(thread_cap)

    config = ScoutConfig.ladder_rung_2()
    started = {"wall": time.perf_counter(), "cpu": time.process_time()}
    policies = published_policies(PUBLISHED_RUN, config)
    populations = {seed: generate_population(config, seed) for seed in config.seed_ids}

    x1 = measurement_x1(populations, policies, config)
    x2 = measurement_x2(populations, policies, config)
    x4 = measurement_x4(populations, config)
    reading = apply_reading_rule(x1, x2)

    # X3 runs only when X1 calls for it: the objective's optimum is beta* and the linear arm's
    # published parameters are far from it while its gradient is far from stationary.
    ratios = [value for value in reading["numbers"]["gradient_ratios_linear_arm"] if value is not None]
    x3_triggered = bool(
        reading["numbers"]["max_d_objective"] <= EPSILON
        and reading["numbers"]["max_d_learned_linear_arm"] > EPSILON
        and ratios
        and all(value > GRADIENT_RATIO for value in ratios)
    )
    x3 = None
    if x3_triggered:
        worst = max(
            x1["rows"], key=lambda row: row["published"][LINEAR_ARM]["d_learned"]
        )
        x3 = measurement_x3(
            populations, policies, config,
            seed=worst["seed_id"], fold=worst["fold_id"], arm=LINEAR_ARM,
        )

    record = {
        "format": RESULT_FORMAT,
        "schema_version": 1,
        "object_id": OBJECT_ID,
        "evidence_class": EVIDENCE_CLASS,
        "card": CARD,
        "published_run_read": str(PUBLISHED_RUN.relative_to(PROJECT_ROOT).as_posix()),
        "admission": admission,
        "execution_topology": topology_record(thread_cap),
        "config": config.to_dict(),
        "x1": x1,
        "x2": x2,
        "x3": x3,
        "x3_triggered": x3_triggered,
        "x4": x4,
        "reading_rule": reading,
        "wall_seconds": time.perf_counter() - started["wall"],
        "cpu_seconds": time.process_time() - started["cpu"],
    }
    destination = output / "diagnostic.json"
    destination.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return destination


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", allow_abbrev=False)
    run.add_argument("--output-root", required=True)
    run.add_argument("--thread-cap", type=int, default=4)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "run":
            path = run_diagnostic(args.output_root, thread_cap=args.thread_cap)
            record = json.loads(Path(path).read_text(encoding="utf-8"))
            print(json.dumps({
                "path": str(path),
                "branch": record["reading_rule"]["branch"],
                "label": record["reading_rule"]["label"],
                "x3_triggered": record["x3_triggered"],
            }, sort_keys=True))
        else:
            raise AssertionError("unreachable")
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, DiagnosticRefusal) as exc:
        print(f"UCOPE training-target diagnostic stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
