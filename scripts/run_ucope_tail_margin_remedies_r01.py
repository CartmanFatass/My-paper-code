#!/usr/bin/env python3
"""Runner for ``UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01``.

Object
------
Part 2 of ``docs/research/candidates/ucope/UCOPE_TAIL_MARGIN_R01_CARD_20260903.md`` (sections 8
to 12), registered and predicted under owner decision D.20 (2026-09-03).

Question: the held-out tail decision fails only in the ``(LINKED, p = 17/20)`` belief stratum,
where the true top-two gap is ``0.008007``. Which remedy moves the learner's projection back
inside it?

Three arms, three seeds, both group-disjoint folds, the frozen ``FT-XF-BC`` arm, the whitened
tail treatment, the root stage held at ``WHITENED-ROOT-10X``, and a **fresh disjoint index
offset** ``2,000,000``:

* ``LARGER-N``     -- ``n = 163,840`` tail rows per policy, the 10x budget (1,600 tail updates);
* ``BUDGET-100X``  -- ``n = 81,920``, 16,000 tail updates (ten times the ten-fold budget);
* ``MARGIN-AWARE`` -- ``n = 81,920``, the 10x budget, plus a hinge on the **training-support**
  ``(5, 9)`` gap at the training beliefs. By the card's section 6 identity
  ``z(b,6) - z(b,8) == (z(b,5) - z(b,9)) / 2`` the hinge controls the held-out ``(6,8)`` margin
  exactly, at a factor of two, **without any held-out period entering training**.

Every generation, design, whitening and evaluation path is imported from the competence and
root-conditioning runners, so there is one implementation of each.
"""

from __future__ import annotations

import argparse
import contextlib
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
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
    K_EVAL,
    K_TRAIN,
)
from experiments.candidates.ucope.competence_first_scout_r01.evaluation import (  # noqa: E402
    evaluate_policy,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import (  # noqa: E402
    build_arm,
    optimizer_for,
    tail_basis,
)
from experiments.candidates.ucope.competence_first_scout_r01.oracle import (  # noqa: E402
    posterior_short,
)

ROOT_RUNNER = PROJECT_ROOT / "scripts/run_ucope_root_conditioning_r01.py"


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RC = _module("ucope_root_conditioning_r01", ROOT_RUNNER)
CR = RC.CR
LaunchRefusal = CR.LaunchRefusal

OBJECT_ID = "UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01"
EVIDENCE_CLASS = "B/EXPLORE"
RESULT_FORMAT = "UCOPE_TAIL_MARGIN_REMEDIES_R01_RUN_RECORD_V1"
CARD = "docs/research/candidates/ucope/UCOPE_TAIL_MARGIN_R01_CARD_20260903.md"

ARM_ID = CR.ARM_ID
LEARNING_RATE = CR.LEARNING_RATE
ROOT_UPDATES = CR.ROOT_UPDATES
SAMPLED_EVALUATION_EPISODES = CR.SAMPLED_EVALUATION_EPISODES
BETA_STAR = CR.BETA_STAR
EPS_L = CR.EPS_L
MAJORITY = CR.MAJORITY
AGREEMENT_GATE = Fraction(19, 20)

# Card section 8, all fixed before data.
REMEDIES_OFFSET = 2_000_000
HINGE_MARGIN = 0.024022
HINGE_WEIGHT = 1.0
HINGE_WITNESS_PAIR = (5, 9)          # K_train only; the (6,8) held-out pair never enters training
TARGET_STRATUM_CONTEXT = ("LINKED", Fraction(17, 20))
HELD_OUT_DECISION_PAIR = (6, 8)      # evaluation-side only
BASELINE_COUNT0_GAPS = (-0.000333, -0.006212, 0.023598, 0.011790, -0.009773, 0.007736)
BASELINE_AGREEMENT_COUNT = 3

ARMS: dict[str, dict[str, Any]] = {
    "LARGER-N": {"episodes_per_context": 81_920, "tail_updates": 1_600, "hinge": False},
    "BUDGET-100X": {"episodes_per_context": 40_960, "tail_updates": 16_000, "hinge": False},
    "MARGIN-AWARE": {"episodes_per_context": 40_960, "tail_updates": 1_600, "hinge": True},
}
LARGEST_EPISODES_PER_CONTEXT = max(row["episodes_per_context"] for row in ARMS.values())

LEDGER = {
    "authority": ["docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#11", CARD],
    "still_gating": [
        "central_4gib_memory_admission",
        "section_4_integrity_items",
        "odd_training_even_held_out_separation",
        "whitening_from_training_rows_only_per_stage",
        "fresh_counter_addressed_index_law_offset_2000000",
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


def _numpy():
    import numpy

    return numpy


def _torch():
    import torch

    return torch


# ---------------------------------------------------------------------------
# The training-support hinge
# ---------------------------------------------------------------------------


def hinge_directions(beliefs):
    """Rows of ``z(b, 5) - z(b, 9)``: the K_train witness of the held-out (6, 8) direction.

    Both periods are in ``K_TRAIN``. No held-out period is ever evaluated here; the frozen
    odd-training / even-held-out separation is preserved by construction.
    """
    numpy = _numpy()
    first, second = HINGE_WITNESS_PAIR
    if first not in K_TRAIN or second not in K_TRAIN:
        raise LaunchRefusal("hinge witness pair must lie inside K_TRAIN")
    rows = [
        numpy.asarray(tail_basis(belief=float(value), period=first), dtype=numpy.float64)
        - numpy.asarray(tail_basis(belief=float(value), period=second), dtype=numpy.float64)
        for value in beliefs
    ]
    return numpy.stack(rows, axis=0)


def _hinge_loss(hinge_batch, beta):
    torch = _torch()
    return torch.clamp(HINGE_MARGIN - (hinge_batch * beta).sum(dim=-1), min=0.0).mean()


def step_with_hinge(scorer, optimizer, x, z, targets, activity, prefix, hinge_batch=None):
    """``training._step`` with an optional additive hinge; identical when the hinge is absent."""
    import math

    torch = _torch()
    optimizer.zero_grad(set_to_none=True)
    prediction = scorer(x, z)
    loss = torch.nn.functional.mse_loss(prediction, targets)
    if hinge_batch is not None:
        loss = loss + HINGE_WEIGHT * _hinge_loss(hinge_batch, scorer.beta)
    if not torch.isfinite(loss).item():
        activity["nonfinite_events"] += 1
        raise ValueError("nonfinite training loss")
    loss.backward()
    norm = torch.nn.utils.clip_grad_norm_(scorer.parameters(), 1.0)
    norm_value = float(norm.item())
    if not math.isfinite(norm_value):
        activity["nonfinite_events"] += 1
        raise ValueError("nonfinite gradient norm")
    activity[f"{prefix}_gradient_norm_sum"] += norm_value
    activity[f"{prefix}_gradient_norm_max"] = max(activity[f"{prefix}_gradient_norm_max"], norm_value)
    activity[f"{prefix}_clipping_events"] += int(norm_value > 1.0)
    optimizer.step()
    for parameter in scorer.parameters():
        if parameter.dtype != torch.float32 or not torch.isfinite(parameter).all().item():
            activity["nonfinite_events"] += 1
            raise ValueError("nonfinite/non-FP32 parameter after update")


def train_tail(*, seed_id: str, fold_id: int, blocks, white, updates: int,
               hinge_design=None, activity):
    """The whitened tail, optionally with the training-support hinge; raw coefficients out."""
    torch = _torch()
    numpy = _numpy()
    _root_init, model = build_arm(ARM_ID, seed_id, fold_id)
    initial = [float(value) for value in model.state_dict()["beta"].tolist()]
    design = torch.tensor(
        (blocks["tail"]["design64"] @ white["_inverse"].T).astype(numpy.float32),
        dtype=torch.float32)
    hinge = None
    if hinge_design is not None:
        # The hinge lives in the same coordinates as the parameters being optimised.
        hinge = torch.tensor(
            (hinge_design @ white["_inverse"].T).astype(numpy.float32), dtype=torch.float32)
    with torch.no_grad():
        model.beta.copy_(torch.tensor(
            (white["_factor"].T @ numpy.asarray(initial)).astype(numpy.float32),
            dtype=torch.float32))
    optimizer = optimizer_for(model, LEARNING_RATE)
    count = design.shape[0]
    for update in range(updates):
        indices = torch.tensor(
            CR._cyclic_indices(count, update, BATCH_SIZE), dtype=torch.int64)
        step_with_hinge(
            model, optimizer, blocks["tail"]["x"][indices], design[indices],
            blocks["tail"]["y"][indices], activity, "tail",
            hinge_batch=None if hinge is None else hinge[indices])
    final = [float(value) for value in model.state_dict()["beta"].tolist()]
    recovered = numpy.linalg.solve(white["_factor"].T, numpy.asarray(final))
    return [float(value) for value in recovered], initial


# ---------------------------------------------------------------------------
# Margin bookkeeping
# ---------------------------------------------------------------------------


def target_stratum_beliefs():
    link, reliability = TARGET_STRATUM_CONTEXT
    return [posterior_short(link, reliability, count) for count in range(7)]


def held_out_gap(belief, beta) -> float:
    """The (6, 8) top-two gap at a belief; linear in beta, so exact."""
    numpy = _numpy()
    top, competitor = HELD_OUT_DECISION_PAIR
    difference = (numpy.asarray(tail_basis(belief=float(belief), period=top))
                  - numpy.asarray(tail_basis(belief=float(belief), period=competitor)))
    return float(difference @ numpy.asarray(beta, dtype=numpy.float64))


def margin_record(beta) -> dict[str, Any]:
    """Per-count (6,8) gaps in the target stratum, and the projection of the error."""
    numpy = _numpy()
    star = numpy.asarray(BETA_STAR, dtype=numpy.float64)
    vector = numpy.asarray(beta, dtype=numpy.float64)
    rows = {}
    for count, belief in enumerate(target_stratum_beliefs()):
        truth_gap = held_out_gap(belief, star)
        gap = held_out_gap(belief, vector)
        rows[str(count)] = {
            "belief": float(belief),
            "truth_gap": truth_gap,
            "gap": gap,
            "projection": gap - truth_gap,
            "flipped": gap < 0.0,
        }
    return {
        "count0_gap": rows["0"]["gap"],
        "count0_projection": rows["0"]["projection"],
        "count0_truth_gap": rows["0"]["truth_gap"],
        "counts_flipped": [int(key) for key, row in rows.items() if row["flipped"]],
        "cells": rows,
    }


def value_bias(blocks, beta, beta_star_policy) -> dict[str, Any]:
    """Training-set fit cost of a remedy, and the held-out value error against beta*."""
    numpy = _numpy()
    design, targets = blocks["tail"]["design64"], blocks["tail"]["targets64"]

    def mse(vector):
        residual = design @ numpy.asarray(vector, dtype=numpy.float64) - targets
        return float((residual ** 2).mean())

    star = numpy.asarray(BETA_STAR, dtype=numpy.float64)
    vector = numpy.asarray(beta, dtype=numpy.float64)
    errors = []
    for context in CONTEXTS:
        link, reliability, _cost = context
        for count in range(7):
            belief = posterior_short(link, reliability, count)
            for period in K_EVAL:
                basis = numpy.asarray(tail_basis(belief=float(belief), period=period))
                errors.append(abs(float(basis @ (vector - star))))
    arm_mse, exact_mse = mse(beta), mse(beta_star_policy)
    return {
        "tail_train_mse": arm_mse,
        "tail_train_mse_at_exact_solve": exact_mse,
        "excess_train_mse_over_exact_solve": arm_mse - exact_mse,
        "excess_train_mse_ratio": (arm_mse / exact_mse) if exact_mse > 0 else None,
        "max_abs_held_out_value_error_vs_beta_star": max(errors),
    }


# ---------------------------------------------------------------------------
# Reading rule (card section 9), applied verbatim in its stated order
# ---------------------------------------------------------------------------


def apply_reading_rule(policies: list[dict[str, Any]]) -> dict[str, Any]:
    names = list(ARMS)
    agreement = {
        name: [row["arms"][name]["agreement_within_gate"] for row in policies] for name in names
    }
    counts = {name: sum(agreement[name]) for name in names}
    gaps = {name: [row["arms"][name]["margin"]["count0_gap"] for row in policies]
            for name in names}
    negative = [index for index, value in enumerate(BASELINE_COUNT0_GAPS) if value < 0.0]
    positive = [index for index, value in enumerate(BASELINE_COUNT0_GAPS) if value >= 0.0]
    strict = {
        name: (bool(negative)
               and all(gaps[name][index] > 0.0 for index in negative)
               and all(gaps[name][index] > 0.0 for index in positive))
        for name in names
    }
    any_improvement = {
        name: any(gaps[name][index] > 0.0 for index in negative) for name in names
    }
    numbers = {
        "branch_statistic": "min_forced_PROBE_tail_agreement >= 19/20",
        "agreement_gate": float(AGREEMENT_GATE),
        "majority_threshold": MAJORITY,
        "baseline_agreement_count": BASELINE_AGREEMENT_COUNT,
        "baseline_count0_gaps": list(BASELINE_COUNT0_GAPS),
        "policies": len(policies),
        "agreement_flags": agreement,
        "agreement_counts": counts,
        "count0_gaps": gaps,
        "baseline_negative_policy_indices": negative,
        "strictly_improves_margin": strict,
        "any_negative_baseline_turned_positive": any_improvement,
        "c_even_counts": {
            name: sum(row["arms"][name]["competence"]["competence_pass"] for row in policies)
            for name in names
        },
        "c_even_flags": {
            name: [row["arms"][name]["competence"]["competence_pass"] for row in policies]
            for name in names
        },
    }
    all_six = [name for name in names if counts[name] == len(policies)]
    if all_six:
        return {"branch": "M-A", "label": "MARGIN_CLOSED", "arms_at_all_six": all_six,
                "numbers": numbers}
    majority = [name for name in names if counts[name] >= MAJORITY]
    if majority:
        return {"branch": "M-B", "label": "MARGIN_MAJORITY", "arms_at_majority": majority,
                "numbers": numbers}
    improving = [name for name in names if strict[name]]
    if improving:
        return {"branch": "M-C", "label": "MARGIN_MOVED_NOT_CLOSED",
                "arms_improving": improving, "numbers": numbers}
    if (max(counts.values()) <= BASELINE_AGREEMENT_COUNT
            and not any(any_improvement.values())):
        return {"branch": "M-D", "label": "MARGIN_UNMOVED", "numbers": numbers}
    return {"branch": "M-E", "label": "UNCLEAR", "numbers": numbers}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _prefix(columns, episodes_per_context: int):
    width = len(CONTEXTS)
    limit = episodes_per_context * width
    return {name: value[:limit] for name, value in columns.items()}


def run_object(output_root: str | Path, *, thread_cap: int = 4,
               largest_episodes_per_context: int = LARGEST_EPISODES_PER_CONTEXT,
               arms: dict[str, dict[str, Any]] | None = None) -> Path:
    numpy = _numpy()
    torch = _torch()
    output = Path(output_root).resolve()
    if output.exists():
        raise LaunchRefusal(f"output root is create-once: {output}")
    attempt_id = uuid.uuid4().hex
    output.mkdir(parents=True)
    staging = output / f".complete-staging-{attempt_id}"
    staging.mkdir()

    admission = CR.admit_memory(output / "preflight.json")
    CR._configure_topology(thread_cap)
    source = RC.source_status_record()
    started = {"wall": time.perf_counter(), "cpu": time.process_time()}
    selection = CR._n_selection()
    if REMEDIES_OFFSET % 20 != 0 or REMEDIES_OFFSET <= 1_000_000 + largest_episodes_per_context:
        raise LaunchRefusal("the fresh offset must be a disjoint multiple of 20")
    selection.OFFSET = REMEDIES_OFFSET
    plan = dict(ARMS if arms is None else arms)

    try:
        counts = {
            "environment_episodes": 0, "tail_rows": 0, "root_rows": 0,
            "tail_optimizer_updates": 0, "root_optimizer_updates": 0,
            "tail_example_exposures": 0, "root_example_exposures": 0,
            "exact_solves": 0, "exact_policy_evaluations": 0,
            "sampled_evaluation_episodes": 0, "sampled_evaluation_transitions": 0,
            "hinge_rows_built": 0, "nonfinite_events": 0, "clipping_events": 0,
        }
        policies: list[dict[str, Any]] = []
        exposure_rows: list[dict[str, Any]] = []
        for seed in B1_SEEDS:
            columns, _labels = CR.canonical_order(
                selection.generate_columns(seed, largest_episodes_per_context))
            counts["environment_episodes"] += columns["fold"].size
            if int(columns["fold"].sum()) * 2 != columns["fold"].size:
                raise LaunchRefusal("fold balance broken at the fresh index range")
            if int(columns["probe"].sum()) * 2 != columns["probe"].size:
                raise LaunchRefusal("behaviour stratum balance broken at the fresh index range")
            for fold in (0, 1):
                record: dict[str, Any] = {
                    "seed_id": seed, "fold_id": fold, "arms": {}, "reference": {},
                }
                for arm_name, plan_row in plan.items():
                    subset = _prefix(columns, plan_row["episodes_per_context"])
                    blocks = CR.stage_designs(subset, fold)
                    tail_block, root_block = blocks["tail"], blocks["root"]
                    tail_white = CR.whitening(tail_block["design64"], stage="tail")
                    root_white = CR.whitening(root_block["design64"], stage="root")
                    beta_tail_star = CR.exact_solve(
                        tail_block["design64"], tail_block["targets64"])
                    counts["exact_solves"] += 1
                    counts["tail_rows"] += tail_block["design64"].shape[0]
                    counts["root_rows"] += root_block["design64"].shape[0]

                    hinge_design = None
                    if plan_row["hinge"]:
                        hinge_design = hinge_directions(
                            subset["belief"][(subset["fold"] == (1 - fold)) & subset["probe"]])
                        counts["hinge_rows_built"] += hinge_design.shape[0]

                    activity = CR._fresh_activity()
                    started_arm = time.perf_counter()
                    beta_tail, tail_initial = train_tail(
                        seed_id=seed, fold_id=fold, blocks=blocks, white=tail_white,
                        updates=plan_row["tail_updates"], hinge_design=hinge_design,
                        activity=activity)
                    counts["tail_optimizer_updates"] += plan_row["tail_updates"]
                    counts["tail_example_exposures"] += plan_row["tail_updates"] * BATCH_SIZE

                    targets = CR.root_targets_fp32(root_block, beta_tail)
                    beta_root_star = CR.exact_solve(root_block["design64"], targets)
                    counts["exact_solves"] += 1
                    beta_root, root_initial = RC.train_root(
                        seed_id=seed, fold_id=fold, blocks=blocks, targets=targets,
                        whitened=True, root_white=root_white, activity=activity)
                    counts["root_optimizer_updates"] += ROOT_UPDATES
                    counts["root_example_exposures"] += ROOT_UPDATES * BATCH_SIZE
                    counts["nonfinite_events"] += activity["nonfinite_events"]
                    counts["clipping_events"] += (
                        activity["tail_clipping_events"] + activity["root_clipping_events"])

                    root_model, tail_model = CR._raw_modules(seed, fold, beta_root, beta_tail)
                    item = evaluate_policy(
                        root_model, tail_model, arm_id=ARM_ID, seed_id=seed, fold_id=fold,
                        root_update=ROOT_UPDATES,
                        sampled_episodes=SAMPLED_EVALUATION_EPISODES)
                    counts["exact_policy_evaluations"] += item.exact_policy_evaluations
                    counts["sampled_evaluation_episodes"] += item.sampled_evaluation_episodes
                    counts["sampled_evaluation_transitions"] += item.sampled_evaluation_transitions
                    breakdown, summary = RC.per_context_breakdown(root_model, tail_model)
                    if (abs(summary["max_regret"] - item.max_regret) > 1e-12
                            or abs(summary["min_tail_agreement"]
                                   - item.minimum_tail_agreement) > 1e-12):
                        raise LaunchRefusal(
                            "per-context breakdown disagrees with the frozen evaluation")

                    tail_vector = numpy.asarray(beta_tail)
                    record["arms"][arm_name] = {
                        "episodes_per_context": plan_row["episodes_per_context"],
                        "tail_rows": int(tail_block["design64"].shape[0]),
                        "root_rows": int(root_block["design64"].shape[0]),
                        "tail_updates": plan_row["tail_updates"],
                        "root_updates": ROOT_UPDATES,
                        "hinge": bool(plan_row["hinge"]),
                        "hinge_margin": HINGE_MARGIN if plan_row["hinge"] else None,
                        "hinge_weight": HINGE_WEIGHT if plan_row["hinge"] else None,
                        "hinge_witness_pair": list(HINGE_WITNESS_PAIR) if plan_row["hinge"] else None,
                        "whitening": {
                            "tail": {k: v for k, v in tail_white.items() if not k.startswith("_")},
                            "root": {k: v for k, v in root_white.items() if not k.startswith("_")},
                        },
                        "beta_tail": beta_tail, "beta_root": beta_root,
                        "beta_tail_star": [float(v) for v in beta_tail_star],
                        "d_learned_tail": float(numpy.abs(tail_vector - beta_tail_star).max()),
                        "d_learned_root": float(
                            numpy.abs(numpy.asarray(beta_root) - beta_root_star).max()),
                        "d_objective": float(
                            numpy.abs(beta_tail_star - numpy.asarray(BETA_STAR)).max()),
                        "eps_L": EPS_L,
                        "competence": CR._competence_record(item),
                        "c_root_pass": RC.c_root_pass(item, summary),
                        "agreement_within_gate": bool(summary["min_tail_agreement_within_gate"]),
                        "margin": margin_record(beta_tail),
                        "value_bias": value_bias(blocks, beta_tail, beta_tail_star),
                        "per_context": breakdown, "per_context_summary": summary,
                        "activity": activity,
                        "wall_seconds": time.perf_counter() - started_arm,
                    }
                    record["reference"][arm_name] = {
                        "note": ("the exact tail solve on this arm's own rows; a reference, not "
                                 "an arm, and not part of the reading rule"),
                        "margin": margin_record(beta_tail_star),
                    }
                    for stage, final, initial in (
                        ("tail", tail_vector, numpy.asarray(tail_initial)),
                        ("root", numpy.asarray(beta_root), numpy.asarray(root_initial)),
                    ):
                        exposure_rows.append({
                            "arm": arm_name, "stage": stage, "seed_id": seed, "fold_id": fold,
                            "parameter_displacement_l2": float(
                                numpy.sqrt(((final - initial) ** 2).sum())),
                            "initialisation_scale_l2": float(numpy.sqrt((initial ** 2).sum())),
                            "max_abs_coordinate_move": float(numpy.abs(final - initial).max()),
                        })
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
                "per-coordinate displacement of the recovered raw Bellman vectors from the exact "
                "deterministic initialisation of the same seed and fold, per arm and stage"),
            "learning_rate": LEARNING_RATE, "root_updates": ROOT_UPDATES,
            "rows": exposure_rows,
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
            "arms": {name: dict(row) for name, row in plan.items()},
            "index_law": {
                "offset": REMEDIES_OFFSET,
                "law": "episode index i = OFFSET + j for j = 0 .. m-1",
                "published_ranges_avoided": [
                    "0..5119", "0..319", "1000000..1081919"],
                "offset_is_multiple_of_20": REMEDIES_OFFSET % 20 == 0,
            },
            "odd_training_even_held_out_separation": {
                "training_support": list(K_TRAIN),
                "held_out_support": list(K_EVAL),
                "hinge_witness_pair": list(HINGE_WITNESS_PAIR),
                "hinge_witness_inside_training_support": all(
                    period in K_TRAIN for period in HINGE_WITNESS_PAIR),
                "held_out_periods_used_in_training": [],
            },
            "hinge_margin": HINGE_MARGIN, "hinge_weight": HINGE_WEIGHT,
            "learning_rate": LEARNING_RATE, "batch_size": BATCH_SIZE,
            "beta_star": list(BETA_STAR), "agreement_gate": float(AGREEMENT_GATE),
            "admission": admission, "ledger": LEDGER,
            "source_status": source,
            "execution_topology": CR.topology_record(thread_cap),
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
    finally:
        selection.OFFSET = 1_000_000


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
        reading = record["reading_rule"]
        print(json.dumps({
            "path": str(path), "branch": reading["branch"], "label": reading["label"],
            "agreement_counts": reading["numbers"]["agreement_counts"],
            "c_even_counts": reading["numbers"]["c_even_counts"],
        }, sort_keys=True))
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, LaunchRefusal) as exc:
        print(f"UCOPE tail-margin remedies stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
