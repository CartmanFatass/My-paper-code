#!/usr/bin/env python3
"""Runner for ``UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01``.

Object
------
``UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01``, evidence class ``B/EXPLORE``, frozen by
``docs/research/candidates/ucope/UCOPE_COMPETENCE_WHITENED_R01_CARD_20260903.md`` under owner
decision D.14 (2026-09-03), with ``n = 81,920`` tail rows per policy fixed in that card's
section 3 before any learner existed.

Question: with conditioning and sample-size variance both handled, does the whitened linear
``FT-XF-BC`` learner reach competence on this host?

Three arms at the ten-fold budget (1,600 tail and 3,200 root updates, ``lr 3e-3``, batch 256),
three seeds, both group-disjoint folds:

* ``WHITENED-10X`` -- both stages whitened from their own training rows only, float64, under
  the same Cholesky contract the conditioning object used;
* ``RAW-10X`` -- the control, identical but unwhitened;
* ``EXACT-SOLVE`` -- the ceiling: both stages solved exactly, no optimizer trajectory.

Rows come from the frozen host at the card's fresh index law, through the *same* generator the
``n`` selection used, so there is exactly one data-generation path.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
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
    CONTEXTS,
    K_TRAIN,
    LADDER_RUNG_1_LEARNING_RATE,
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.evaluation import (  # noqa: E402
    evaluate_policy,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import (  # noqa: E402
    build_arm,
    optimizer_for,
)
from experiments.candidates.ucope.competence_first_scout_r01.training import _step  # noqa: E402

N_SELECTION_SCRIPT = PROJECT_ROOT / "scripts/run_ucope_competence_whitened_n_selection.py"


def _n_selection():
    spec = importlib.util.spec_from_file_location("ucope_competence_n_selection", N_SELECTION_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OBJECT_ID = "UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01"
EVIDENCE_CLASS = "B/EXPLORE"
RESULT_FORMAT = "UCOPE_COMPETENCE_WHITENED_R01_RUN_RECORD_V1"
CARD = "docs/research/candidates/ucope/UCOPE_COMPETENCE_WHITENED_R01_CARD_20260903.md"
RESOURCE_PREFLIGHT = PROJECT_ROOT / "scripts/hmasd_resource_preflight.py"
PACKAGE_ROOT = PROJECT_ROOT / "experiments/candidates/ucope/competence_first_scout_r01"
MINIMUM_MEMORY_BYTES = 4 * 1024**3

ARM_ID = "FT-XF-BC"
# Fixed by card section 3, before any learner ran.
TAIL_ROWS_PER_POLICY = 81_920
EPISODES_PER_CONTEXT = TAIL_ROWS_PER_POLICY // 2
# Ten times the frozen rung-1 budget.
TAIL_UPDATES = 1_600
ROOT_UPDATES = 3_200
LEARNING_RATE = LADDER_RUNG_1_LEARNING_RATE
SAMPLED_EVALUATION_EPISODES = 64
BETA_STAR = (0.31, 0.60, 1.35, -1.08, -0.891)

# Card sections 3, 4 and 7, frozen before data.
EPS_L = 0.10
D_OBJECTIVE_CEILING = 0.10
CHOLESKY_TOLERANCE = 1e-10
MINIMUM_GRAM_EIGENVALUE = 1e-6
MAJORITY = 4

LEDGER = {
    "authority": ["docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#11", CARD],
    "still_gating": [
        "central_4gib_memory_admission",
        "section_4_integrity_items",
        "whitening_from_training_rows_only_per_stage",
        "fresh_counter_addressed_index_law",
        "section_5_2_nonzero_counts",
        "machine_generated_exposure_line",
        "section_6_2_learner_side_quarantine",
    ],
    "recorded_not_gating": [
        "clean_committed_source_inventory",
        "performance_ready_assessment",
        "execution_topology",
        "acquisition_and_count_raw_locks",
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


def admit_memory(receipt: Path) -> dict[str, Any]:
    receipt.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, str(RESOURCE_PREFLIGHT), "admit-memory", "--out", str(receipt)],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if completed.returncode != 0 or not receipt.is_file():
        raise LaunchRefusal(
            f"central 4 GiB memory admission failed rc={completed.returncode}: {completed.stderr.strip()}"
        )
    value = json.loads(receipt.read_text(encoding="utf-8"))
    if (
        value.get("passed") is not True
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
    paths = sorted(PACKAGE_ROOT.glob("*.py")) + [Path(__file__).resolve(), N_SELECTION_SCRIPT]
    files = [
        {"path": path.relative_to(PROJECT_ROOT).as_posix(),
         "size_bytes": path.stat().st_size, "sha256": _sha256_file(path)}
        for path in paths
    ]
    aggregate = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    record: dict[str, Any] = {
        "gating": False,
        "demoted_by": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.4",
        "files": files, "aggregate_sha256": aggregate,
        "git_head": None, "porcelain_status": None, "clean": None, "observation_error": None,
    }
    try:
        record["git_head"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", *(row["path"] for row in files)],
            cwd=PROJECT_ROOT, check=True, capture_output=True, text=True,
        ).stdout.splitlines()
        record["porcelain_status"] = status
        record["clean"] = not status
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover
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
# Designs
# ---------------------------------------------------------------------------


def _cyclic_indices(count: int, update_index: int, batch_size: int) -> list[int]:
    """Exactly the index arithmetic of training._cyclic_batch."""
    start = (update_index * batch_size) % count
    return [(start + offset) % count for offset in range(batch_size)]


def canonical_order(columns):
    """Reorder the generated rows into the frozen canonical order.

    ``training._canonical_rows`` sorts by ``(episode_index, context_id)``; the generator emits
    episode-major in ``CONTEXTS`` declaration order, which is a different permutation inside each
    episode (``c9_100`` precedes ``c7_50`` in the declaration, the reverse of the string order).
    Applying the same permutation here makes the cyclic batch windows the frozen ones.
    """
    numpy = _numpy()
    labels = [context_id(context) for context in CONTEXTS]
    permutation = numpy.asarray(sorted(range(len(labels)), key=lambda index: labels[index]))
    width = len(CONTEXTS)
    episodes = columns["fold"].size // width
    order = (numpy.arange(episodes)[:, None] * width + permutation[None, :]).ravel()
    return {name: value[order] for name, value in columns.items()}, [labels[i] for i in permutation]


def stage_designs(columns, fold_id: int):
    """FP32 feature/basis tensors for both stages of one policy, plus target ingredients."""
    numpy = _numpy()
    torch = _torch()
    fold = columns["fold"]
    probe = columns["probe"]

    tail_mask = (fold == (1 - fold_id)) & probe
    root_mask = fold == fold_id

    def tail_block():
        belief = columns["belief"][tail_mask]
        period = columns["period"][tail_mask].astype(numpy.float64)
        k = period / 9.0
        cost = columns["cost"][tail_mask]
        linked = columns["linked"][tail_mask].astype(numpy.float64)
        rel = columns["reliability"][tail_mask]
        ones = numpy.ones_like(k)
        x = numpy.stack([ones, ones, numpy.zeros_like(k), k, belief, cost, linked, rel, linked * rel], axis=1)
        z = numpy.stack([ones, belief, k, belief * k, k * k], axis=1)
        y = columns["tail_return"][tail_mask]
        return x, z, y, belief, period

    def root_block():
        is_probe = columns["probe"][root_mask].astype(numpy.float64)
        period = columns["period"][root_mask].astype(numpy.float64)
        k = numpy.where(is_probe > 0.0, 0.0, period / 9.0)
        cost = columns["cost"][root_mask]
        linked = columns["linked"][root_mask].astype(numpy.float64)
        rel = columns["reliability"][root_mask]
        ones = numpy.ones_like(k)
        half = numpy.full_like(k, 0.5)
        x = numpy.stack([ones, numpy.zeros_like(k), is_probe, k, half, cost, linked, rel, linked * rel], axis=1)
        z = numpy.stack([
            ones, (1.0 - is_probe) * k, (1.0 - is_probe) * k * k,
            is_probe, is_probe * cost, is_probe * linked, is_probe * linked * rel,
        ], axis=1)
        return x, z, is_probe, columns["belief"][root_mask], columns["probe_primitive"][root_mask], columns["tail_return"][root_mask]

    tx, tz, ty, tbelief, tperiod = tail_block()
    rx, rz, rprobe, rbelief, rprimitive, rreturn = root_block()
    to_tensor = lambda value: torch.tensor(value.astype(numpy.float32), dtype=torch.float32)  # noqa: E731
    return {
        "tail": {"x": to_tensor(tx), "z": to_tensor(tz), "y": to_tensor(ty),
                 "design64": tz, "targets64": ty},
        "root": {"x": to_tensor(rx), "z": to_tensor(rz), "design64": rz,
                 "probe": rprobe.astype(bool), "belief": rbelief,
                 "probe_primitive": rprimitive, "tail_return": rreturn},
    }


def _tail_candidate_bases(block, dtype):
    """tail_basis(belief, period) for every K_TRAIN period, on the root rows."""
    numpy = _numpy()
    belief = block["belief"].astype(dtype)
    stacked = []
    for period in K_TRAIN:
        k = numpy.asarray(period / 9.0, dtype=dtype)
        ones = numpy.ones_like(belief)
        stacked.append(numpy.stack([ones, belief, ones * k, belief * k, ones * k * k], axis=1))
    return stacked


def root_targets_fp64(block, beta_tail):
    """The frozen target package at float64: probe_primitive + max over K_TRAIN of Q_tail.

    This is the arithmetic the outcome-free ``n`` selection used, so the EXACT-SOLVE ceiling is
    computed exactly as the point that fixed ``n`` was.
    """
    numpy = _numpy()
    beta = numpy.asarray(beta_tail, dtype=numpy.float64)
    belief = block["belief"]
    # Term order copied from the n selection's ``_root_targets`` so the ceiling is bit-identical
    # to the arithmetic that fixed ``n``.
    candidates = []
    for period in K_TRAIN:
        k = period / 9.0
        candidates.append(
            beta[0] + beta[1] * belief + beta[2] * k + beta[3] * belief * k + beta[4] * k * k
        )
    best = numpy.max(numpy.stack(candidates, axis=1), axis=1)
    return numpy.where(block["probe"], block["probe_primitive"] + best, block["tail_return"])


def root_targets_fp32(block, beta_tail):
    """The same package through the frozen FP32 scorer arithmetic ``(z * beta).sum(-1)``.

    ``training._root_targets`` materialises the root targets once from the trained tail scorer in
    FP32; the two learner arms use this path so their targets are the frozen ones.
    """
    numpy = _numpy()
    torch = _torch()
    beta = torch.tensor(numpy.asarray(beta_tail, dtype=numpy.float32), dtype=torch.float32)
    values = torch.stack([
        (torch.tensor(basis, dtype=torch.float32) * beta).sum(dim=-1)
        for basis in _tail_candidate_bases(block, numpy.float32)
    ], dim=1)
    best = values.max(dim=1).values.numpy()
    primitive = block["probe_primitive"].astype(numpy.float32)
    return numpy.where(
        block["probe"], primitive + best, block["tail_return"].astype(numpy.float32)
    ).astype(numpy.float64)


def whitening(design64, *, stage: str) -> dict[str, Any]:
    """Cholesky whitening from the training rows only, float64, checked before any step."""
    numpy = _numpy()
    count = design64.shape[0]
    gram = design64.T @ design64 / count
    eigenvalues = numpy.linalg.eigvalsh(gram)
    smallest, largest = float(eigenvalues.min()), float(eigenvalues.max())
    if smallest <= MINIMUM_GRAM_EIGENVALUE:
        raise LaunchRefusal(f"{stage} whitening refused: lambda_min {smallest:.6e}")
    factor = numpy.linalg.cholesky(gram)
    reconstruction = float(numpy.abs(factor @ factor.T - gram).max())
    if not reconstruction <= CHOLESKY_TOLERANCE:
        raise LaunchRefusal(f"{stage} whitening refused: max|LL^T - G| {reconstruction:.6e}")
    return {
        "stage": stage, "rows": int(count), "source": "training_rows_only",
        "gram_smallest_eigenvalue": smallest, "gram_largest_eigenvalue": largest,
        "gram_condition_number": largest / smallest,
        "cholesky_reconstruction_max_abs": reconstruction,
        "cholesky_tolerance": CHOLESKY_TOLERANCE,
        "minimum_gram_eigenvalue": MINIMUM_GRAM_EIGENVALUE,
        "_factor": factor, "_inverse": numpy.linalg.inv(factor),
    }


def exact_solve(design64, targets64):
    numpy = _numpy()
    beta, *_ = numpy.linalg.lstsq(design64, targets64, rcond=None)
    return beta


def gradient_infinity_norm(design64, targets64, beta) -> float:
    numpy = _numpy()
    beta = numpy.asarray(beta, dtype=numpy.float64)
    residual = design64 @ beta - targets64
    return float(numpy.abs(2.0 * (design64.T @ residual) / design64.shape[0]).max())


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def _fresh_activity() -> dict[str, Any]:
    return {
        "root_gradient_norm_sum": 0.0, "root_gradient_norm_max": 0.0, "root_clipping_events": 0,
        "tail_gradient_norm_sum": 0.0, "tail_gradient_norm_max": 0.0, "tail_clipping_events": 0,
        "nonfinite_events": 0,
    }


def train_stage(model, x, z, y, *, updates: int, activity, prefix: str):
    torch = _torch()
    optimizer = optimizer_for(model, LEARNING_RATE)
    count = z.shape[0]
    for update in range(updates):
        indices = torch.tensor(_cyclic_indices(count, update, BATCH_SIZE), dtype=torch.int64)
        _step(model, optimizer, x[indices], z[indices], y[indices], activity, prefix)
    return [float(value) for value in model.state_dict()["beta"].tolist()]


def _raw_modules(seed_id: str, fold_id: int, beta_root, beta_tail):
    torch = _torch()
    numpy = _numpy()
    root, tail = build_arm(ARM_ID, seed_id, fold_id)
    with torch.no_grad():
        root.beta.copy_(torch.tensor(numpy.asarray(beta_root, dtype=numpy.float32), dtype=torch.float32))
        tail.beta.copy_(torch.tensor(numpy.asarray(beta_tail, dtype=numpy.float32), dtype=torch.float32))
    return root, tail


def run_training_arm(*, seed_id: str, fold_id: int, blocks, whitened: bool,
                     tail_white, root_white, activity):
    """Tail then root, both in the arm's coordinate system; parameters returned in raw ones."""
    torch = _torch()
    numpy = _numpy()

    def prepare(block, white):
        if not whitened:
            return block["z"], None
        design = torch.tensor(
            (block["design64"] @ white["_inverse"].T).astype(numpy.float32), dtype=torch.float32
        )
        return design, white

    _root_init, tail_model = build_arm(ARM_ID, seed_id, fold_id)
    tail_initial = [float(v) for v in tail_model.state_dict()["beta"].tolist()]
    tail_design, tail_transform = prepare(blocks["tail"], tail_white)
    if whitened:
        with torch.no_grad():
            tail_model.beta.copy_(torch.tensor(
                (tail_transform["_factor"].T @ numpy.asarray(tail_initial)).astype(numpy.float32),
                dtype=torch.float32))
    tail_final = train_stage(
        tail_model, blocks["tail"]["x"], tail_design, blocks["tail"]["y"],
        updates=TAIL_UPDATES, activity=activity, prefix="tail",
    )
    beta_tail = (
        list(numpy.linalg.solve(tail_transform["_factor"].T, numpy.asarray(tail_final)))
        if whitened else list(tail_final)
    )
    beta_tail = [float(value) for value in beta_tail]

    targets = root_targets_fp32(blocks["root"], beta_tail)
    root_model, _tail_init = build_arm(ARM_ID, seed_id, fold_id)
    root_initial = [float(v) for v in root_model.state_dict()["beta"].tolist()]
    root_design, root_transform = prepare(blocks["root"], root_white)
    if whitened:
        with torch.no_grad():
            root_model.beta.copy_(torch.tensor(
                (root_transform["_factor"].T @ numpy.asarray(root_initial)).astype(numpy.float32),
                dtype=torch.float32))
    root_final = train_stage(
        root_model, blocks["root"]["x"], root_design,
        torch.tensor(targets.astype(numpy.float32), dtype=torch.float32),
        updates=ROOT_UPDATES, activity=activity, prefix="root",
    )
    beta_root = (
        list(numpy.linalg.solve(root_transform["_factor"].T, numpy.asarray(root_final)))
        if whitened else list(root_final)
    )
    beta_root = [float(value) for value in beta_root]
    return {
        "beta_tail": beta_tail, "beta_root": beta_root,
        "beta_tail_initial": tail_initial, "beta_root_initial": root_initial,
        "root_targets": targets,
    }


# ---------------------------------------------------------------------------
# Reading rule (card section 7), applied verbatim in its stated order
# ---------------------------------------------------------------------------


def apply_reading_rule(policies: list[dict[str, Any]]) -> dict[str, Any]:
    def competent(arm: str):
        return [row["arms"][arm]["competence"]["competence_pass"] for row in policies]

    whitened = competent("WHITENED-10X")
    raw = competent("RAW-10X")
    exact = competent("EXACT-SOLVE")
    numbers = {
        "majority_threshold": MAJORITY,
        "policies": len(policies),
        "whitened_competent": sum(whitened),
        "raw_competent": sum(raw),
        "exact_competent": sum(exact),
        "whitened_all": all(whitened),
        "whitened_majority": sum(whitened) >= MAJORITY,
        "exact_all": all(exact),
        "whitened_flags": whitened, "raw_flags": raw, "exact_flags": exact,
    }
    if numbers["whitened_all"]:
        return {"branch": "C-A", "label": "WHITENED_LEARNER_COMPETENT", "numbers": numbers}
    if numbers["whitened_majority"] and numbers["exact_all"]:
        return {"branch": "C-B", "label": "WHITENED_MAJORITY_CEILING_CLEAN", "numbers": numbers}
    if numbers["exact_all"] and sum(whitened) < MAJORITY:
        return {"branch": "C-C", "label": "CEILING_COMPETENT_LEARNER_NOT", "numbers": numbers}
    if not numbers["exact_all"]:
        return {"branch": "C-D", "label": "CEILING_NOT_COMPETENT", "numbers": numbers}
    return {"branch": "C-E", "label": "UNCLEAR", "numbers": numbers}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _competence_record(item) -> dict[str, Any]:
    return {
        "all_finite": bool(item.all_finite),
        "all_unique": bool(item.all_unique),
        "oracle_root_match": bool(item.oracle_root_match),
        "max_regret": float(item.max_regret),
        "minimum_tail_agreement": float(item.minimum_tail_agreement),
        "competence_pass": bool(item.competence_pass),
        "regret_gate": 1 / 50,
        "agreement_gate": 19 / 20,
        "root_actions": dict(item.root_actions),
        "sampled_external_return_sum": float(item.sampled_external_return_sum),
        "sampled_evaluation_episodes": int(item.sampled_evaluation_episodes),
        "sampled_evaluation_transitions": int(item.sampled_evaluation_transitions),
    }


def run_object(output_root: str | Path, *, thread_cap: int = 4,
               episodes_per_context: int = EPISODES_PER_CONTEXT) -> Path:
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
    selection = _n_selection()

    try:
        counts = {
            "environment_episodes": 0, "tail_rows": 0, "root_rows": 0,
            "tail_optimizer_updates": 0, "root_optimizer_updates": 0,
            "tail_example_exposures": 0, "root_example_exposures": 0,
            "exact_solves": 0, "exact_policy_evaluations": 0,
            "sampled_evaluation_episodes": 0, "sampled_evaluation_transitions": 0,
            "nonfinite_events": 0, "clipping_events": 0,
        }
        policies = []
        exposure_rows = []
        canonical_labels = None
        for seed in B1_SEEDS:
            columns, canonical_labels = canonical_order(
                selection.generate_columns(seed, episodes_per_context))
            counts["environment_episodes"] += columns["fold"].size
            if int(columns["fold"].sum()) * 2 != columns["fold"].size:
                raise LaunchRefusal("fold balance broken at the fresh index range")
            if int(columns["probe"].sum()) * 2 != columns["probe"].size:
                raise LaunchRefusal("behaviour stratum balance broken at the fresh index range")
            values, occurrences = numpy.unique(columns["period"], return_counts=True)
            if sorted(int(value) for value in values) != sorted(K_TRAIN):
                raise LaunchRefusal("training period support broken at the fresh index range")
            if len({int(value) for value in occurrences}) != 1:
                raise LaunchRefusal("training period balance broken at the fresh index range")
            for fold in (0, 1):
                blocks = stage_designs(columns, fold)
                tail_block, root_block = blocks["tail"], blocks["root"]
                counts["tail_rows"] += tail_block["design64"].shape[0]
                counts["root_rows"] += root_block["design64"].shape[0]

                # Launch condition: the whitening contract, per stage, before any optimizer.
                tail_white = whitening(tail_block["design64"], stage="tail")
                beta_tail_star = exact_solve(tail_block["design64"], tail_block["targets64"])
                exact_root_targets = root_targets_fp64(root_block, beta_tail_star)
                root_white = whitening(root_block["design64"], stage="root")
                beta_root_star = exact_solve(root_block["design64"], exact_root_targets)
                counts["exact_solves"] += 2

                g_star = gradient_infinity_norm(
                    tail_block["design64"], tail_block["targets64"], BETA_STAR)
                record: dict[str, Any] = {
                    "seed_id": seed, "fold_id": fold,
                    "tail_rows": int(tail_block["design64"].shape[0]),
                    "root_rows": int(root_block["design64"].shape[0]),
                    "whitening": {
                        "tail": {k: v for k, v in tail_white.items() if not k.startswith("_")},
                        "root": {k: v for k, v in root_white.items() if not k.startswith("_")},
                    },
                    "beta_tail_star": [float(v) for v in beta_tail_star],
                    "beta_root_star": [float(v) for v in beta_root_star],
                    "root_target_precision_max_abs_difference": float(numpy.abs(
                        exact_root_targets
                        - root_targets_fp32(root_block, beta_tail_star)).max()),
                    "d_objective": float(numpy.abs(beta_tail_star - numpy.asarray(BETA_STAR)).max()),
                    "d_objective_ceiling": D_OBJECTIVE_CEILING,
                    "g_star": g_star,
                    "g_at_beta_tail_star": gradient_infinity_norm(
                        tail_block["design64"], tail_block["targets64"], beta_tail_star),
                    "arms": {},
                }

                for arm_name, whitened in (("RAW-10X", False), ("WHITENED-10X", True)):
                    activity = _fresh_activity()
                    started_arm = time.perf_counter()
                    outcome = run_training_arm(
                        seed_id=seed, fold_id=fold, blocks=blocks, whitened=whitened,
                        tail_white=tail_white, root_white=root_white, activity=activity,
                    )
                    counts["tail_optimizer_updates"] += TAIL_UPDATES
                    counts["root_optimizer_updates"] += ROOT_UPDATES
                    counts["tail_example_exposures"] += TAIL_UPDATES * BATCH_SIZE
                    counts["root_example_exposures"] += ROOT_UPDATES * BATCH_SIZE
                    counts["nonfinite_events"] += activity["nonfinite_events"]
                    counts["clipping_events"] += (
                        activity["tail_clipping_events"] + activity["root_clipping_events"])
                    root_model, tail_model = _raw_modules(
                        seed, fold, outcome["beta_root"], outcome["beta_tail"])
                    item = evaluate_policy(
                        root_model, tail_model, arm_id=ARM_ID, seed_id=seed, fold_id=fold,
                        root_update=ROOT_UPDATES, sampled_episodes=SAMPLED_EVALUATION_EPISODES)
                    counts["exact_policy_evaluations"] += item.exact_policy_evaluations
                    counts["sampled_evaluation_episodes"] += item.sampled_evaluation_episodes
                    counts["sampled_evaluation_transitions"] += item.sampled_evaluation_transitions
                    tail_vector = numpy.asarray(outcome["beta_tail"])
                    root_vector = numpy.asarray(outcome["beta_root"])
                    record["arms"][arm_name] = {
                        "beta_tail": outcome["beta_tail"], "beta_root": outcome["beta_root"],
                        "d_learned_tail": float(numpy.abs(tail_vector - beta_tail_star).max()),
                        "d_learned_root": float(numpy.abs(root_vector - beta_root_star).max()),
                        "eps_L": EPS_L,
                        "g_learned": gradient_infinity_norm(
                            tail_block["design64"], tail_block["targets64"], tail_vector),
                        "gradient_ratio": (
                            gradient_infinity_norm(
                                tail_block["design64"], tail_block["targets64"], tail_vector) / g_star
                            if g_star > 0 else None),
                        "competence": _competence_record(item),
                        "activity": activity,
                        "wall_seconds": time.perf_counter() - started_arm,
                    }
                    for stage, final, initial in (
                        ("tail", tail_vector, numpy.asarray(outcome["beta_tail_initial"])),
                        ("root", root_vector, numpy.asarray(outcome["beta_root_initial"])),
                    ):
                        exposure_rows.append({
                            "arm": arm_name, "stage": stage, "seed_id": seed, "fold_id": fold,
                            "parameter_displacement_l2": float(numpy.sqrt(((final - initial) ** 2).sum())),
                            "initialisation_scale_l2": float(numpy.sqrt((initial ** 2).sum())),
                            "max_abs_coordinate_move": float(numpy.abs(final - initial).max()),
                        })

                exact_root, exact_tail = _raw_modules(seed, fold, beta_root_star, beta_tail_star)
                item = evaluate_policy(
                    exact_root, exact_tail, arm_id=ARM_ID, seed_id=seed, fold_id=fold,
                    root_update=ROOT_UPDATES, sampled_episodes=SAMPLED_EVALUATION_EPISODES)
                counts["exact_policy_evaluations"] += item.exact_policy_evaluations
                counts["sampled_evaluation_episodes"] += item.sampled_evaluation_episodes
                counts["sampled_evaluation_transitions"] += item.sampled_evaluation_transitions
                record["arms"]["EXACT-SOLVE"] = {
                    "beta_tail": [float(v) for v in beta_tail_star],
                    "beta_root": [float(v) for v in beta_root_star],
                    "d_learned_tail": 0.0, "d_learned_root": 0.0,
                    "g_learned": record["g_at_beta_tail_star"],
                    "gradient_ratio": (record["g_at_beta_tail_star"] / g_star) if g_star > 0 else None,
                    "competence": _competence_record(item),
                    "note": "outcome-free closed-form ceiling; no optimizer trajectory, excluded from the exposure line",
                }
                policies.append(record)

        for name, value in counts.items():
            if name in {"nonfinite_events", "clipping_events"}:
                continue
            if value <= 0:
                raise LaunchRefusal(f"section 5.2 nonzero count violated: {name} = {value}")
        if counts["nonfinite_events"]:
            raise LaunchRefusal("nonfinite event during training")

        moves = [row["max_abs_coordinate_move"] for row in exposure_rows]
        exposure = {
            "statement": (
                "per-coordinate displacement of the recovered Bellman vectors from the exact "
                "deterministic initialisation of the same seed and fold, per arm and stage; the "
                "EXACT-SOLVE arm has no optimizer trajectory and is excluded"
            ),
            "learning_rate": LEARNING_RATE, "tail_updates": TAIL_UPDATES,
            "root_updates": ROOT_UPDATES, "rows": exposure_rows,
            "minimum_max_abs_coordinate_move": min(moves),
            "maximum_max_abs_coordinate_move": max(moves),
            "learner_can_move_in_its_budget": bool(moves) and min(moves) > 0.0,
        }
        if not exposure["learner_can_move_in_its_budget"]:
            raise LaunchRefusal("exposure line reports no parameter movement in the budget")

        reading = apply_reading_rule(policies)
        record = {
            "format": RESULT_FORMAT, "schema_version": 1, "object_id": OBJECT_ID,
            "evidence_class": EVIDENCE_CLASS, "card": CARD, "complete": True,
            "attempt_id": attempt_id, "arm_id": ARM_ID,
            "tail_rows_per_policy": TAIL_ROWS_PER_POLICY,
            "episodes_per_context": episodes_per_context,
            "index_law": {"offset": selection.OFFSET,
                          "law": "episode index i = OFFSET + j for j = 0 .. m-1",
                          "published_ranges_avoided": ["0..5119", "0..319"],
                          "offset_is_multiple_of_20": selection.OFFSET % 20 == 0},
            "canonical_context_order": canonical_labels,
            "tail_updates": TAIL_UPDATES, "root_updates": ROOT_UPDATES,
            "learning_rate": LEARNING_RATE, "batch_size": BATCH_SIZE,
            "beta_star": list(BETA_STAR), "admission": admission, "ledger": LEDGER,
            "source_status": source, "execution_topology": topology_record(thread_cap),
            "counts": counts, "policies": policies, "exposure_line": exposure,
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
            (quarantine / "failure.json").write_text(json.dumps({
                "object_id": OBJECT_ID, "complete": False, "quarantined": True,
                "quarantine_rule": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#6.2",
                "error_type": type(exc).__name__, "error": str(exc),
                "source_status": source,
            }, indent=2, sort_keys=True), encoding="utf-8")
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
        path = run_object(args.output_root, thread_cap=args.thread_cap)
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        print(json.dumps({
            "path": str(path), "branch": record["reading_rule"]["branch"],
            "label": record["reading_rule"]["label"],
            "whitened_competent": record["reading_rule"]["numbers"]["whitened_competent"],
            "exact_competent": record["reading_rule"]["numbers"]["exact_competent"],
            "raw_competent": record["reading_rule"]["numbers"]["raw_competent"],
        }, sort_keys=True))
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, LaunchRefusal) as exc:
        print(f"UCOPE competence object stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
