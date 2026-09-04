#!/usr/bin/env python3
"""Runner for ``UCOPE-B-EXPLORE-OPTIMISER-CONDITIONING-R01``.

Object
------
``UCOPE-B-EXPLORE-OPTIMISER-CONDITIONING-R01``, evidence class ``B/EXPLORE``, frozen by
``docs/research/candidates/ucope/UCOPE_OPTIMISER_CONDITIONING_R01_CARD_20260903.md`` under owner
decision D.12 (2026-09-03).

Question: on the linear ``FT-XF-BC`` tail objective, does whitening the design close the learner's
gap to its own per-policy optimum, and does the exact solve reach it?

Five arms over the ladder's three seeds and two folds:

* ``RAW-BASE`` -- the published path: raw design, frozen ``_step`` loop, rung-1 budget
  (160 tail updates at ``lr 3e-3``, batch 256) from the frozen initialisation;
* ``WHITENED-BASE`` -- the same loop, budget and initialisation on the whitened design;
* ``EXACT-SOLVE`` -- the float64 normal-equation solution, an outcome-free ceiling;
* ``RAW-10X`` / ``WHITENED-10X`` -- the same two loops continued to 1,600 tail updates.

Whitening is a bijective linear reparameterisation, so the objective's optimum in ``beta`` is
identical in both coordinate systems and ``d_objective`` cannot move; only the optimizer's
trajectory changes. Gradient clipping then acts in the whitened norm, which is recorded.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    B1_SEEDS,
    BATCH_SIZE,
    LADDER_RUNG_1_LEARNING_RATE,
    ScoutConfig,
)
from experiments.candidates.ucope.competence_first_scout_r01.host import (  # noqa: E402
    generate_population,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import (  # noqa: E402
    build_arm,
    optimizer_for,
)
from experiments.candidates.ucope.competence_first_scout_r01.training import (  # noqa: E402
    _canonical_rows,
    _step,
    _tail_batch,
)

OBJECT_ID = "UCOPE-B-EXPLORE-OPTIMISER-CONDITIONING-R01"
EVIDENCE_CLASS = "B/EXPLORE"
RESULT_FORMAT = "UCOPE_OPTIMISER_CONDITIONING_R01_RUN_RECORD_V1"
CARD = "docs/research/candidates/ucope/UCOPE_OPTIMISER_CONDITIONING_R01_CARD_20260903.md"
RESOURCE_PREFLIGHT = PROJECT_ROOT / "scripts/hmasd_resource_preflight.py"
PACKAGE_ROOT = PROJECT_ROOT / "experiments/candidates/ucope/competence_first_scout_r01"
MINIMUM_MEMORY_BYTES = 4 * 1024**3

ARM_ID = "FT-XF-BC"
BASE_UPDATES = 160
EXTENDED_UPDATES = 1_600
LEARNING_RATE = LADDER_RUNG_1_LEARNING_RATE
BETA_STAR = (0.31, 0.60, 1.35, -1.08, -0.891)

# Card section 6, frozen before data.
EPS_L = 0.10
RHO = 5.0
# Card section 3, frozen before data.
CHOLESKY_TOLERANCE = 1e-10
MINIMUM_GRAM_EIGENVALUE = 1e-6

LEDGER = {
    "authority": [
        "docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#11",
        CARD,
    ],
    "still_gating": [
        "central_4gib_memory_admission",
        "section_4_integrity_items",
        "whitening_from_training_rows_only",
        "section_5_2_nonzero_counts",
        "machine_generated_exposure_line",
        "section_6_2_learner_side_quarantine",
    ],
    "recorded_not_gating": [
        "clean_committed_source_inventory",
        "performance_ready_assessment",
        "execution_topology",
        "exact_oracle_competence_predicate",
    ],
}


class LaunchRefusal(RuntimeError):
    """Raised before or during stateful work when a launch condition fails."""


def _numpy():
    import numpy

    return numpy


def _torch():
    import torch

    return torch


# ---------------------------------------------------------------------------
# Launch conditions and provenance
# ---------------------------------------------------------------------------


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
        raise LaunchRefusal(
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
        raise LaunchRefusal("central 4 GiB memory admission refused the launch")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_status_record() -> dict[str, Any]:
    """Bound source inventory, HEAD and working-tree status. Recorded; never refuses."""
    paths = sorted(PACKAGE_ROOT.glob("*.py")) + [Path(__file__).resolve()]
    files = [
        {
            "path": path.relative_to(PROJECT_ROOT).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": _sha256_file(path),
        }
        for path in paths
    ]
    aggregate = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    record: dict[str, Any] = {
        "gating": False,
        "demoted_by": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.4",
        "files": files,
        "aggregate_sha256": aggregate,
        "git_head": None,
        "porcelain_status": None,
        "clean": None,
        "observation_error": None,
    }
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", *(row["path"] for row in files)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        record["git_head"] = head
        record["porcelain_status"] = status
        record["clean"] = not status
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - environment dependent
        record["observation_error"] = f"{type(exc).__name__}: {exc}"
    return record


def _configure_topology(thread_cap: int) -> None:
    torch = _torch()
    if type(thread_cap) is not int or not 1 <= thread_cap <= 16:
        raise LaunchRefusal("thread cap must be an integer between 1 and 16")
    torch.set_num_threads(thread_cap)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)


def topology_record(thread_cap: int) -> dict[str, Any]:
    torch = _torch()
    return {
        "gating": False,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "torch_cuda_available": bool(torch.cuda.is_available()),
        "torch_intraop_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
        "thread_cap_requested": thread_cap,
        "deterministic_algorithms": True,
        "process_count": 1,
        "executable": sys.executable,
        "logical_processors": os.cpu_count(),
    }


# ---------------------------------------------------------------------------
# Design, whitening, exact solve
# ---------------------------------------------------------------------------


def _cyclic_indices(count: int, update_index: int, batch_size: int) -> list[int]:
    """Exactly the index arithmetic of training._cyclic_batch."""
    start = (update_index * batch_size) % count
    return [(start + offset) % count for offset in range(batch_size)]


def policy_design(population, fold_id: int):
    """Full FP32 tensors for one policy's tail rows, in the frozen row order."""
    rows = _canonical_rows(population, fold=fold_id, tail=True)
    x, z, y = _tail_batch(rows)
    return rows, x, z, y


def whitening(design64) -> dict[str, Any]:
    """Cholesky whitening computed from the training rows only, at float64.

    A launch condition (card section 3): the reconstruction and eigenvalue contracts are
    checked before any optimizer step exists.
    """
    numpy = _numpy()
    count = design64.shape[0]
    gram = design64.T @ design64 / count
    eigenvalues = numpy.linalg.eigvalsh(gram)
    smallest = float(eigenvalues.min())
    largest = float(eigenvalues.max())
    if smallest <= MINIMUM_GRAM_EIGENVALUE:
        raise LaunchRefusal(
            f"whitening refused: lambda_min {smallest:.6e} <= {MINIMUM_GRAM_EIGENVALUE:.0e}"
        )
    factor = numpy.linalg.cholesky(gram)
    reconstruction = float(numpy.abs(factor @ factor.T - gram).max())
    if not reconstruction <= CHOLESKY_TOLERANCE:
        raise LaunchRefusal(
            f"whitening refused: max|LL^T - G| {reconstruction:.6e} > {CHOLESKY_TOLERANCE:.0e}"
        )
    inverse = numpy.linalg.inv(factor)
    return {
        "rows": int(count),
        "gram_smallest_eigenvalue": smallest,
        "gram_largest_eigenvalue": largest,
        "gram_condition_number": largest / smallest,
        "cholesky_reconstruction_max_abs": reconstruction,
        "cholesky_tolerance": CHOLESKY_TOLERANCE,
        "minimum_gram_eigenvalue": MINIMUM_GRAM_EIGENVALUE,
        "source": "training_rows_only",
        "_factor": factor,
        "_inverse": inverse,
    }


def exact_solve(design64, targets64):
    numpy = _numpy()
    beta, _residuals, _rank, _sv = numpy.linalg.lstsq(design64, targets64, rcond=None)
    return beta


def gradient_infinity_norm(design64, targets64, beta) -> float:
    numpy = _numpy()
    beta = numpy.asarray(beta, dtype=numpy.float64)
    residual = design64 @ beta - targets64
    return float(numpy.abs(2.0 * (design64.T @ residual) / design64.shape[0]).max())


# ---------------------------------------------------------------------------
# Training arms
# ---------------------------------------------------------------------------


def _fresh_activity() -> dict[str, Any]:
    return {
        "tail_gradient_norm_sum": 0.0,
        "tail_gradient_norm_max": 0.0,
        "tail_clipping_events": 0,
        "nonfinite_events": 0,
    }


def train_arm(*, seed_id: str, fold_id: int, x, z, y, whitened, factor=None, inverse=None):
    """Run the frozen _step loop to EXTENDED_UPDATES, snapshotting at BASE_UPDATES."""
    torch = _torch()
    numpy = _numpy()
    _root, tail = build_arm(ARM_ID, seed_id, fold_id)
    beta_initial = [float(value) for value in tail.state_dict()["beta"].tolist()]
    design = z
    if whitened:
        # z_tilde = z L^-T ; beta_tilde = L^T beta, so the predicted value is unchanged and the
        # arm starts from exactly the same function as the raw arm.
        design = torch.tensor(
            (z.double().numpy() @ inverse.T).astype(numpy.float32), dtype=torch.float32
        )
        with torch.no_grad():
            tail.beta.copy_(
                torch.tensor(
                    (factor.T @ numpy.asarray(beta_initial, dtype=numpy.float64)).astype(numpy.float32),
                    dtype=torch.float32,
                )
            )
    optimizer = optimizer_for(tail, LEARNING_RATE)
    activity = _fresh_activity()
    count = design.shape[0]
    snapshots: dict[int, list[float]] = {}
    started = time.perf_counter()
    for update in range(EXTENDED_UPDATES):
        indices = torch.tensor(_cyclic_indices(count, update, BATCH_SIZE), dtype=torch.int64)
        _step(tail, optimizer, x[indices], design[indices], y[indices], activity, "tail")
        if update + 1 in (BASE_UPDATES, EXTENDED_UPDATES):
            snapshots[update + 1] = [float(value) for value in tail.state_dict()["beta"].tolist()]
    elapsed = time.perf_counter() - started
    recovered = {}
    for budget, beta in snapshots.items():
        if whitened:
            recovered[budget] = [
                float(value)
                for value in numpy.linalg.solve(factor.T, numpy.asarray(beta, dtype=numpy.float64))
            ]
        else:
            recovered[budget] = [float(value) for value in beta]
    return {
        "beta_initial": beta_initial,
        "parameter_snapshots": {str(budget): value for budget, value in snapshots.items()},
        "recovered_beta": {str(budget): value for budget, value in recovered.items()},
        "activity": activity,
        "wall_seconds": elapsed,
        "updates": EXTENDED_UPDATES,
    }


# ---------------------------------------------------------------------------
# Reading rule (card section 6), applied verbatim in its stated order
# ---------------------------------------------------------------------------


def _median(values):
    ordered = sorted(values)
    count = len(ordered)
    middle = count // 2
    return ordered[middle] if count % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def apply_reading_rule(policies: list[dict[str, Any]]) -> dict[str, Any]:
    def gather(arm: str, budget: int):
        return [row["arms"][arm]["d_learned"][str(budget)] for row in policies]

    raw_base = gather("RAW", BASE_UPDATES)
    whitened_base = gather("WHITENED", BASE_UPDATES)
    raw_extended = gather("RAW", EXTENDED_UPDATES)
    whitened_extended = gather("WHITENED", EXTENDED_UPDATES)
    numbers = {
        "eps_L": EPS_L,
        "rho": RHO,
        "d_learned_raw_base": raw_base,
        "d_learned_whitened_base": whitened_base,
        "d_learned_raw_10x": raw_extended,
        "d_learned_whitened_10x": whitened_extended,
        "median_raw_base": _median(raw_base),
        "median_whitened_base": _median(whitened_base),
        "median_reduction_factor": (_median(raw_base) / _median(whitened_base))
        if _median(whitened_base) > 0
        else None,
        "whitened_base_all_below_eps": all(value < EPS_L for value in whitened_base),
        "whitened_10x_all_below_eps": all(value < EPS_L for value in whitened_extended),
        "raw_10x_all_below_eps": all(value < EPS_L for value in raw_extended),
    }
    reduction_met = _median(whitened_base) <= _median(raw_base) / RHO
    numbers["median_reduction_met"] = bool(reduction_met)

    if numbers["whitened_base_all_below_eps"]:
        return {"branch": "O-A", "label": "CONDITIONING_CLOSES_IT", "numbers": numbers}
    if reduction_met and numbers["whitened_10x_all_below_eps"]:
        return {"branch": "O-B", "label": "CONDITIONING_MOSTLY_CLOSES_IT", "numbers": numbers}
    if numbers["raw_10x_all_below_eps"] and not reduction_met:
        return {"branch": "O-C", "label": "BUDGET_CLOSES_IT_NOT_CONDITIONING", "numbers": numbers}
    if not numbers["raw_10x_all_below_eps"] and not numbers["whitened_10x_all_below_eps"]:
        return {"branch": "O-D", "label": "NEITHER_CLOSES_IT", "numbers": numbers}
    return {"branch": "O-E", "label": "UNCLEAR", "numbers": numbers}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_object(output_root: str | Path, *, thread_cap: int = 4) -> Path:
    numpy = _numpy()
    output = Path(output_root).resolve()
    if output.exists():
        raise LaunchRefusal(f"output root is create-once: {output}")
    attempt_id = uuid.uuid4().hex
    output.mkdir(parents=True)
    staging = output / f".complete-staging-{attempt_id}"
    staging.mkdir()

    admission = admit_memory(output / "preflight.json")
    _configure_topology(thread_cap)
    source = source_status_record()
    started = {"wall": time.perf_counter(), "cpu": time.process_time()}

    try:
        config = ScoutConfig.ladder_rung_1()
        if config.tail_updates != BASE_UPDATES or config.learning_rate != LEARNING_RATE:
            raise LaunchRefusal("base budget does not match the frozen rung-1 configuration")
        populations = {seed: generate_population(config, seed) for seed in B1_SEEDS}
        counts = {
            "environment_episodes": 0,
            "tail_rows": 0,
            "tail_optimizer_updates": 0,
            "tail_example_exposures": 0,
            "exact_solves": 0,
            "nonfinite_events": 0,
            "tail_clipping_events": 0,
        }
        for population in populations.values():
            counts["environment_episodes"] += len(population)

        policies = []
        exposure_rows = []
        for seed in B1_SEEDS:
            for fold in (0, 1):
                rows, x, z, y = policy_design(populations[seed], fold)
                design64 = z.double().numpy().astype(numpy.float64)
                targets64 = y.double().numpy().astype(numpy.float64)
                counts["tail_rows"] += len(rows)

                # Launch condition: the whitening contract, before any optimizer exists.
                white = whitening(design64)
                factor = white.pop("_factor")
                inverse = white.pop("_inverse")

                beta_tail_star = exact_solve(design64, targets64)
                counts["exact_solves"] += 1
                g_star = gradient_infinity_norm(design64, targets64, BETA_STAR)

                record: dict[str, Any] = {
                    "seed_id": seed,
                    "fold_id": fold,
                    "tail_rows": len(rows),
                    "whitening": white,
                    "beta_tail_star": [float(value) for value in beta_tail_star],
                    "d_objective": float(
                        numpy.abs(beta_tail_star - numpy.asarray(BETA_STAR)).max()
                    ),
                    "g_star": g_star,
                    "g_at_beta_tail_star": gradient_infinity_norm(design64, targets64, beta_tail_star),
                    "arms": {},
                }
                for arm_name, whitened in (("RAW", False), ("WHITENED", True)):
                    outcome = train_arm(
                        seed_id=seed, fold_id=fold, x=x, z=z, y=y,
                        whitened=whitened, factor=factor, inverse=inverse,
                    )
                    counts["tail_optimizer_updates"] += outcome["updates"]
                    counts["tail_example_exposures"] += outcome["updates"] * BATCH_SIZE
                    counts["nonfinite_events"] += outcome["activity"]["nonfinite_events"]
                    counts["tail_clipping_events"] += outcome["activity"]["tail_clipping_events"]
                    d_learned = {}
                    g_learned = {}
                    for budget, beta in outcome["recovered_beta"].items():
                        vector = numpy.asarray(beta, dtype=numpy.float64)
                        d_learned[budget] = float(numpy.abs(vector - beta_tail_star).max())
                        g_learned[budget] = gradient_infinity_norm(design64, targets64, vector)
                        initial = numpy.asarray(outcome["beta_initial"], dtype=numpy.float64)
                        exposure_rows.append({
                            "arm": f"{arm_name}-{'BASE' if int(budget) == BASE_UPDATES else '10X'}",
                            "seed_id": seed,
                            "fold_id": fold,
                            "tail_updates": int(budget),
                            "parameter_displacement_l2": float(
                                numpy.sqrt(((vector - initial) ** 2).sum())
                            ),
                            "initialisation_scale_l2": float(numpy.sqrt((initial**2).sum())),
                            "max_abs_coordinate_move": float(numpy.abs(vector - initial).max()),
                        })
                    record["arms"][arm_name] = {
                        "beta_initial": outcome["beta_initial"],
                        "recovered_beta": outcome["recovered_beta"],
                        "d_learned": d_learned,
                        "g_learned": g_learned,
                        "gradient_ratio": {
                            budget: (value / g_star if g_star > 0 else None)
                            for budget, value in g_learned.items()
                        },
                        "activity": outcome["activity"],
                        "wall_seconds": outcome["wall_seconds"],
                    }
                record["arms"]["EXACT"] = {
                    "recovered_beta": {"exact": [float(value) for value in beta_tail_star]},
                    "d_learned": {"exact": 0.0},
                    "g_learned": {"exact": record["g_at_beta_tail_star"]},
                    "note": "outcome-free closed-form reference; trains nothing, no optimizer trajectory",
                }
                policies.append(record)

        for name, value in counts.items():
            if name in {"nonfinite_events"}:
                continue
            if value <= 0:
                raise LaunchRefusal(f"section 5.2 nonzero count violated: {name} = {value}")
        if counts["nonfinite_events"]:
            raise LaunchRefusal("nonfinite event during training")

        moves = [row["max_abs_coordinate_move"] for row in exposure_rows]
        exposure = {
            "statement": (
                "per-coordinate displacement of the recovered Bellman vector from the exact "
                "deterministic initialisation of the same seed and fold, per arm and budget; the "
                "EXACT arm has no optimizer trajectory and is excluded"
            ),
            "learning_rate": LEARNING_RATE,
            "base_updates": BASE_UPDATES,
            "extended_updates": EXTENDED_UPDATES,
            "rows": exposure_rows,
            "minimum_max_abs_coordinate_move": min(moves),
            "maximum_max_abs_coordinate_move": max(moves),
            "learner_can_move_in_its_budget": bool(moves) and min(moves) > 0.0,
        }
        if not exposure["learner_can_move_in_its_budget"]:
            raise LaunchRefusal("exposure line reports no parameter movement in the budget")

        reading = apply_reading_rule(policies)
        record = {
            "format": RESULT_FORMAT,
            "schema_version": 1,
            "object_id": OBJECT_ID,
            "evidence_class": EVIDENCE_CLASS,
            "card": CARD,
            "complete": True,
            "attempt_id": attempt_id,
            "arm_id": ARM_ID,
            "base_updates": BASE_UPDATES,
            "extended_updates": EXTENDED_UPDATES,
            "learning_rate": LEARNING_RATE,
            "batch_size": BATCH_SIZE,
            "beta_star": list(BETA_STAR),
            "admission": admission,
            "ledger": LEDGER,
            "source_status": source,
            "execution_topology": topology_record(thread_cap),
            "counts": counts,
            "policies": policies,
            "exposure_line": exposure,
            "reading_rule": reading,
            "wall_seconds": time.perf_counter() - started["wall"],
            "cpu_seconds": time.process_time() - started["cpu"],
        }
        destination = staging / "run-record.json"
        destination.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
        complete = output / "complete"
        os.replace(staging, complete)
        return complete / "run-record.json"
    except BaseException as exc:
        quarantine = output / f"quarantine-{attempt_id}"
        with contextlib.suppress(BaseException):
            quarantine.mkdir(exist_ok=False)
            if staging.exists():
                os.replace(staging, quarantine / "staging")
            (quarantine / "failure.json").write_text(
                json.dumps({
                    "object_id": OBJECT_ID,
                    "complete": False,
                    "quarantined": True,
                    "quarantine_rule": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#6.2",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "source_status": source,
                }, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        raise


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
            path = run_object(args.output_root, thread_cap=args.thread_cap)
            record = json.loads(Path(path).read_text(encoding="utf-8"))
            print(json.dumps({
                "path": str(path),
                "branch": record["reading_rule"]["branch"],
                "label": record["reading_rule"]["label"],
            }, sort_keys=True))
        else:
            raise AssertionError("unreachable")
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, LaunchRefusal) as exc:
        print(f"UCOPE optimiser-conditioning object stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
