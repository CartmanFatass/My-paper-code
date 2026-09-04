#!/usr/bin/env python3
"""Runner for ``UCOPE-B-EXPLORE-ROOT-CONDITIONING-R01``.

Object
------
``UCOPE-B-EXPLORE-ROOT-CONDITIONING-R01``, evidence class ``B/EXPLORE``, frozen by
``docs/research/candidates/ucope/UCOPE_ROOT_CONDITIONING_R01_CARD_20260903.md`` under owner
decision D.16 (2026-09-03), with the branch statistic amended to ``C_root`` before launch by
owner decision D.18 (card section 13).

Question: with the tail stage held fixed, does whitening the root design close the root
learner's gap, and does that reach competence?

One tail per policy -- the competence object's ``WHITENED-10X`` tail, re-trained here and gated
on reproducing that run's recorded coefficients to ``1e-6`` -- shared by three root treatments
at ``n = 81,920`` (163,840 root rows), 3,200 root updates, ``lr 3e-3``, batch 256:

* ``RAW-ROOT-10X``      -- the control: the published raw root path on the whitened tail;
* ``WHITENED-ROOT-10X`` -- the root design whitened from its own training rows only, float64;
* ``EXACT-ROOT-SOLVE``  -- the ceiling: the root normal equations solved exactly on the *same*
  targets, so it inherits the fixed tail's residual by design.

Every data-generation, design, whitening and evaluation path is imported from the competence
object's runner, so there is exactly one implementation of each.
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
from types import SimpleNamespace
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
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.evaluation import (  # noqa: E402
    evaluate_policy,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import (  # noqa: E402
    build_arm,
    tensors_for_record,
)
from experiments.candidates.ucope.competence_first_scout_r01.oracle import (  # noqa: E402
    build_oracle,
    direct_probe,
    expected_tail,
    joint_count_probability,
    optimal_tail,
    posterior_short,
)

COMPETENCE_RUNNER = PROJECT_ROOT / "scripts/run_ucope_competence_whitened_r01.py"


def _competence_runner():
    spec = importlib.util.spec_from_file_location(
        "ucope_competence_whitened_r01", COMPETENCE_RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CR = _competence_runner()
LaunchRefusal = CR.LaunchRefusal

OBJECT_ID = "UCOPE-B-EXPLORE-ROOT-CONDITIONING-R01"
EVIDENCE_CLASS = "B/EXPLORE"
RESULT_FORMAT = "UCOPE_ROOT_CONDITIONING_R01_RUN_RECORD_V1"
CARD = "docs/research/candidates/ucope/UCOPE_ROOT_CONDITIONING_R01_CARD_20260903.md"
COMPETENCE_RECORD = PROJECT_ROOT / (
    "temp/directions/ucope/exp/competence_whitened_r01_20260903/complete/run-record.json")

ARM_ID = CR.ARM_ID
TAIL_ROWS_PER_POLICY = CR.TAIL_ROWS_PER_POLICY
EPISODES_PER_CONTEXT = CR.EPISODES_PER_CONTEXT
TAIL_UPDATES = CR.TAIL_UPDATES
ROOT_UPDATES = CR.ROOT_UPDATES
LEARNING_RATE = CR.LEARNING_RATE
SAMPLED_EVALUATION_EPISODES = CR.SAMPLED_EVALUATION_EPISODES

# Card sections 4, 5, 7 and 13, all fixed before data.
EPS_L = CR.EPS_L
MAJORITY = CR.MAJORITY
TAIL_REPRODUCTION_TOLERANCE = 1e-6
REGRET_GATE = Fraction(1, 50)
AGREEMENT_GATE = Fraction(19, 20)
TARGET_CONTEXT_ID = "LINKED-p17_20-c9_100"

RAW_ROOT = "RAW-ROOT-10X"
WHITENED_ROOT = "WHITENED-ROOT-10X"
EXACT_ROOT = "EXACT-ROOT-SOLVE"

LEDGER = {
    "authority": ["docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#11", CARD],
    "still_gating": [
        "central_4gib_memory_admission",
        "section_4_integrity_items",
        "root_whitening_from_training_rows_only",
        "tail_reproduction_within_1e-6",
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


def _numpy():
    import numpy

    return numpy


def _torch():
    import torch

    return torch


# ---------------------------------------------------------------------------
# The fixed tail stage and its gating reproduction check
# ---------------------------------------------------------------------------


def source_status_record():
    """The competence object's bound inventory, extended with this runner."""
    import hashlib

    record = CR.source_status_record()
    here = Path(__file__).resolve()
    record["files"] = sorted(
        record["files"] + [{
            "path": here.relative_to(PROJECT_ROOT).as_posix(),
            "size_bytes": here.stat().st_size,
            "sha256": CR._sha256_file(here),
        }],
        key=lambda row: row["path"],
    )
    record["aggregate_sha256"] = hashlib.sha256(
        json.dumps(record["files"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--",
             *(row["path"] for row in record["files"])],
            cwd=PROJECT_ROOT, check=True, capture_output=True, text=True,
        ).stdout.splitlines()
        record["porcelain_status"] = status
        record["clean"] = not status
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover
        record["observation_error"] = f"{type(exc).__name__}: {exc}"
    return record


def recorded_tail_vectors(path: Path | None = None) -> dict[tuple[str, int], list[float]]:
    """The competence run's WHITENED-10X tail coefficients, keyed by (seed, fold)."""
    source = Path(path) if path is not None else COMPETENCE_RECORD
    if not source.is_file():
        raise LaunchRefusal(
            f"tail-reproduction reference missing, cannot gate the fixed tail: {source}")
    record = json.loads(source.read_text(encoding="utf-8"))
    if record.get("object_id") != "UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01":
        raise LaunchRefusal("tail-reproduction reference is not the competence run record")
    return {
        (row["seed_id"], int(row["fold_id"])): list(row["arms"]["WHITENED-10X"]["beta_tail"])
        for row in record["policies"]
    }


def train_whitened_tail(*, seed_id: str, fold_id: int, blocks, tail_white, activity):
    """The competence object's WHITENED-10X tail half, re-run here; raw coefficients returned."""
    torch = _torch()
    numpy = _numpy()
    _root_init, tail_model = build_arm(ARM_ID, seed_id, fold_id)
    initial = [float(value) for value in tail_model.state_dict()["beta"].tolist()]
    design = torch.tensor(
        (blocks["tail"]["design64"] @ tail_white["_inverse"].T).astype(numpy.float32),
        dtype=torch.float32)
    with torch.no_grad():
        tail_model.beta.copy_(torch.tensor(
            (tail_white["_factor"].T @ numpy.asarray(initial)).astype(numpy.float32),
            dtype=torch.float32))
    final = CR.train_stage(
        tail_model, blocks["tail"]["x"], design, blocks["tail"]["y"],
        updates=TAIL_UPDATES, activity=activity, prefix="tail")
    recovered = numpy.linalg.solve(tail_white["_factor"].T, numpy.asarray(final))
    return [float(value) for value in recovered], initial


# ---------------------------------------------------------------------------
# The root stage, three treatments of one problem
# ---------------------------------------------------------------------------


def train_root(*, seed_id: str, fold_id: int, blocks, targets, whitened: bool,
               root_white, activity):
    torch = _torch()
    numpy = _numpy()
    root_model, _tail_init = build_arm(ARM_ID, seed_id, fold_id)
    initial = [float(value) for value in root_model.state_dict()["beta"].tolist()]
    if whitened:
        design = torch.tensor(
            (blocks["root"]["design64"] @ root_white["_inverse"].T).astype(numpy.float32),
            dtype=torch.float32)
        with torch.no_grad():
            root_model.beta.copy_(torch.tensor(
                (root_white["_factor"].T @ numpy.asarray(initial)).astype(numpy.float32),
                dtype=torch.float32))
    else:
        design = blocks["root"]["z"]
    final = CR.train_stage(
        root_model, blocks["root"]["x"], design,
        torch.tensor(targets.astype(numpy.float32), dtype=torch.float32),
        updates=ROOT_UPDATES, activity=activity, prefix="root")
    recovered = (
        numpy.linalg.solve(root_white["_factor"].T, numpy.asarray(final))
        if whitened else numpy.asarray(final)
    )
    return [float(value) for value in recovered], initial


# ---------------------------------------------------------------------------
# Predicates and the machine-generated per-context breakdown
# ---------------------------------------------------------------------------


def c_root_pass(item, summary) -> bool:
    """C_even minus its purely tail-determined agreement gate (card section 13).

    The regret gate is evaluated in exact rational arithmetic, exactly as
    ``evaluation.evaluate_policy`` evaluates it for ``C_even``; ``PolicyEvaluation.max_regret``
    is already a float and would lose that exactness.
    """
    return bool(
        item.all_finite
        and item.all_unique
        and item.oracle_root_match
        and summary["max_regret_within_gate"]
    )


def per_context_breakdown(root_model, tail_model):
    """Per-context root action, expected regret and forced-PROBE tail agreement.

    Mirrors ``evaluation.evaluate_policy`` term for term, in the same exact rational
    arithmetic; the competence object had to recompute this after the fact, so it is written
    into the record here. Returns the per-context rows and an exact summary.
    """
    torch = _torch()
    oracle = build_oracle()
    rows = {}
    regrets = []
    agreements = []

    def scores(model, pairs):
        with torch.no_grad():
            values = model(torch.stack([p[0] for p in pairs]), torch.stack([p[1] for p in pairs]))
        return [float(value) for value in values.tolist()]

    for context in CONTEXTS:
        link, p, cost = context
        cell = context_id(context)
        record = SimpleNamespace(link=link, reliability=p, total_cost=cost)
        labels = ("PROBE", *(f"IMMEDIATE:{period}" for period in K_EVAL))
        pairs = [tensors_for_record(record, stage="root", action_probe=True, period=0, belief=0.5)]
        pairs += [
            tensors_for_record(record, stage="root", action_probe=False, period=period, belief=0.5)
            for period in K_EVAL
        ]
        values = scores(root_model, pairs)
        ranked = sorted((value, -index, label)
                        for index, (label, value) in enumerate(zip(labels, values)))
        selected = ranked[-1][2]

        agreement = Fraction(0)
        learned_tail_value = Fraction(0)
        periods = {}
        for count in range(7):
            belief = posterior_short(link, p, count)
            tail_pairs = [
                tensors_for_record(record, stage="tail", action_probe=False, period=period,
                                   belief=float(belief))
                for period in K_EVAL
            ]
            tail_values = scores(tail_model, tail_pairs)
            tail_ranked = sorted((value, -index, period) for index, (period, value)
                                 in enumerate(zip(K_EVAL, tail_values)))
            selected_period = tail_ranked[-1][2]
            periods[str(count)] = int(selected_period)
            mass = (joint_count_probability("SHORT", p, count)
                    + joint_count_probability("LONG", p, count))
            learned_tail_value += mass * expected_tail(selected_period, belief)
            agreement += mass * int(selected_period == optimal_tail(K_EVAL, belief)[0])

        immediate = (expected_tail(int(selected.split(":")[1]), Fraction(1, 2))
                     if selected != "PROBE" else None)
        learned = (learned_tail_value + direct_probe(cost)) if selected == "PROBE" else immediate
        optimum = max(oracle[cell]["baseline"], oracle[cell]["probe_value"])
        regret = optimum - learned
        regrets.append(regret)
        agreements.append(agreement)
        rows[cell] = {
            "root_action": "PROBE" if selected == "PROBE" else "IMMEDIATE",
            "root_selected_label": selected,
            "oracle_action": oracle[cell]["action"],
            "root_action_matches_oracle": (
                ("PROBE" if selected == "PROBE" else "IMMEDIATE") == oracle[cell]["action"]),
            "expected_regret": float(regret),
            "regret_within_gate": regret <= REGRET_GATE,
            "forced_probe_tail_agreement": float(agreement),
            "tail_agreement_within_gate": agreement >= AGREEMENT_GATE,
            "selected_tail_periods": periods,
            "is_target_context": cell == TARGET_CONTEXT_ID,
        }
    cells = list(rows)
    worst_regret = max(range(len(cells)), key=lambda i: regrets[i])
    worst_agreement = min(range(len(cells)), key=lambda i: agreements[i])
    summary = {
        "max_regret": float(max(regrets)),
        "max_regret_within_gate": max(regrets) <= REGRET_GATE,
        "max_regret_context": cells[worst_regret],
        "min_tail_agreement": float(min(agreements)),
        "min_tail_agreement_within_gate": min(agreements) >= AGREEMENT_GATE,
        "min_tail_agreement_context": cells[worst_agreement],
        "contexts_below_agreement_gate": sum(1 for a in agreements if a < AGREEMENT_GATE),
        "contexts_root_action_mismatched": sum(
            1 for row in rows.values() if not row["root_action_matches_oracle"]),
    }
    return rows, summary


# ---------------------------------------------------------------------------
# Reading rule (card section 13), applied verbatim in its stated order
# ---------------------------------------------------------------------------


def apply_reading_rule(policies: list[dict[str, Any]]) -> dict[str, Any]:
    def flags(arm: str):
        return [row["arms"][arm]["c_root_pass"] for row in policies]

    whitened, raw, exact = flags(WHITENED_ROOT), flags(RAW_ROOT), flags(EXACT_ROOT)
    numbers = {
        "branch_statistic": "C_root",
        "majority_threshold": MAJORITY,
        "policies": len(policies),
        "whitened_root_competent": sum(whitened),
        "raw_root_competent": sum(raw),
        "exact_root_competent": sum(exact),
        "whitened_root_all": all(whitened),
        "whitened_root_majority": sum(whitened) >= MAJORITY,
        "exact_root_all": all(exact),
        "whitened_root_flags": whitened, "raw_root_flags": raw, "exact_root_flags": exact,
        "c_even_whitened_root_flags": [
            row["arms"][WHITENED_ROOT]["competence"]["competence_pass"] for row in policies],
        "c_even_raw_root_flags": [
            row["arms"][RAW_ROOT]["competence"]["competence_pass"] for row in policies],
        "c_even_exact_root_flags": [
            row["arms"][EXACT_ROOT]["competence"]["competence_pass"] for row in policies],
    }
    if numbers["whitened_root_all"]:
        return {"branch": "R'-A", "label": "WHITENED_ROOT_COMPETENT", "numbers": numbers}
    if numbers["whitened_root_majority"] and numbers["exact_root_all"]:
        return {"branch": "R'-B", "label": "WHITENED_ROOT_MAJORITY_CEILING_CLEAN", "numbers": numbers}
    if numbers["exact_root_all"] and sum(whitened) < MAJORITY:
        return {"branch": "R'-C", "label": "CEILING_COMPETENT_ROOT_LEARNER_NOT", "numbers": numbers}
    if not numbers["exact_root_all"]:
        return {"branch": "R'-D", "label": "CEILING_NOT_COMPETENT", "numbers": numbers}
    return {"branch": "R'-E", "label": "UNCLEAR", "numbers": numbers}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_object(output_root: str | Path, *, thread_cap: int = 4,
               episodes_per_context: int = EPISODES_PER_CONTEXT,
               competence_record: str | Path | None = None) -> Path:
    numpy = _numpy()
    output = Path(output_root).resolve()
    if output.exists():
        raise LaunchRefusal(f"output root is create-once: {output}")
    attempt_id = uuid.uuid4().hex
    output.mkdir(parents=True)
    staging = output / f".complete-staging-{attempt_id}"
    staging.mkdir()

    admission = CR.admit_memory(output / "preflight.json")
    CR._configure_topology(thread_cap)
    source = source_status_record()
    reference_tails = recorded_tail_vectors(competence_record)
    started = {"wall": time.perf_counter(), "cpu": time.process_time()}
    selection = CR._n_selection()

    try:
        counts = {
            "environment_episodes": 0, "tail_rows": 0, "root_rows": 0,
            "tail_optimizer_updates": 0, "root_optimizer_updates": 0,
            "tail_example_exposures": 0, "root_example_exposures": 0,
            "exact_solves": 0, "exact_policy_evaluations": 0,
            "sampled_evaluation_episodes": 0, "sampled_evaluation_transitions": 0,
            "nonfinite_events": 0, "clipping_events": 0,
        }
        policies: list[dict[str, Any]] = []
        exposure_rows: list[dict[str, Any]] = []
        canonical_labels = None
        for seed in B1_SEEDS:
            columns, canonical_labels = CR.canonical_order(
                selection.generate_columns(seed, episodes_per_context))
            counts["environment_episodes"] += columns["fold"].size
            if int(columns["fold"].sum()) * 2 != columns["fold"].size:
                raise LaunchRefusal("fold balance broken at the fresh index range")
            if int(columns["probe"].sum()) * 2 != columns["probe"].size:
                raise LaunchRefusal("behaviour stratum balance broken at the fresh index range")
            for fold in (0, 1):
                blocks = CR.stage_designs(columns, fold)
                tail_block, root_block = blocks["tail"], blocks["root"]
                counts["tail_rows"] += tail_block["design64"].shape[0]
                counts["root_rows"] += root_block["design64"].shape[0]

                # Launch conditions, before any optimizer exists for this policy.
                tail_white = CR.whitening(tail_block["design64"], stage="tail")
                root_white = CR.whitening(root_block["design64"], stage="root")

                # The fixed tail, re-trained and gated on reproduction (card section 3).
                tail_activity = CR._fresh_activity()
                beta_tail, tail_initial = train_whitened_tail(
                    seed_id=seed, fold_id=fold, blocks=blocks, tail_white=tail_white,
                    activity=tail_activity)
                counts["tail_optimizer_updates"] += TAIL_UPDATES
                counts["tail_example_exposures"] += TAIL_UPDATES * BATCH_SIZE
                counts["nonfinite_events"] += tail_activity["nonfinite_events"]
                counts["clipping_events"] += tail_activity["tail_clipping_events"]
                reference = reference_tails.get((seed, fold))
                if reference is None:
                    raise LaunchRefusal(f"no recorded tail for {seed} fold {fold}")
                reproduction = float(
                    numpy.abs(numpy.asarray(beta_tail) - numpy.asarray(reference)).max())
                if not reproduction <= TAIL_REPRODUCTION_TOLERANCE:
                    raise LaunchRefusal(
                        "tail-reproduction integrity item failed: "
                        f"{seed} fold {fold} max|delta| {reproduction:.6e} > "
                        f"{TAIL_REPRODUCTION_TOLERANCE:.0e}")

                # The exact tail, for d_objective_root only. Never trained, never evaluated.
                beta_tail_star = CR.exact_solve(tail_block["design64"], tail_block["targets64"])
                counts["exact_solves"] += 1

                # One root problem, shared by all three arms: FP32 targets from the fixed tail.
                targets = CR.root_targets_fp32(root_block, beta_tail)
                targets_exact_tail = CR.root_targets_fp64(root_block, beta_tail_star)
                beta_root_star = CR.exact_solve(root_block["design64"], targets)
                beta_root_star_exact_tail = CR.exact_solve(
                    root_block["design64"], targets_exact_tail)
                counts["exact_solves"] += 2
                g_star = CR.gradient_infinity_norm(
                    root_block["design64"], targets, beta_root_star_exact_tail)

                record: dict[str, Any] = {
                    "seed_id": seed, "fold_id": fold,
                    "tail_rows": int(tail_block["design64"].shape[0]),
                    "root_rows": int(root_block["design64"].shape[0]),
                    "whitening": {
                        "tail": {k: v for k, v in tail_white.items() if not k.startswith("_")},
                        "root": {k: v for k, v in root_white.items() if not k.startswith("_")},
                    },
                    "fixed_tail": {
                        "arm": "WHITENED-10X (competence object)",
                        "beta_tail": beta_tail,
                        "beta_tail_initial": tail_initial,
                        "recorded_beta_tail": reference,
                        "reproduction_max_abs_difference": reproduction,
                        "reproduction_tolerance": TAIL_REPRODUCTION_TOLERANCE,
                        "reproduction_pass": True,
                        "activity": tail_activity,
                    },
                    "beta_tail_star": [float(v) for v in beta_tail_star],
                    "beta_root_star": [float(v) for v in beta_root_star],
                    "beta_root_star_exact_tail": [float(v) for v in beta_root_star_exact_tail],
                    "d_objective_root": float(numpy.abs(
                        beta_root_star - beta_root_star_exact_tail).max()),
                    "root_target_learned_vs_exact_tail_max_abs": float(numpy.abs(
                        targets - targets_exact_tail).max()),
                    "eps_L": EPS_L,
                    "g_star_root": g_star,
                    "arms": {},
                }

                for arm_name, whitened in ((RAW_ROOT, False), (WHITENED_ROOT, True)):
                    activity = CR._fresh_activity()
                    started_arm = time.perf_counter()
                    beta_root, root_initial = train_root(
                        seed_id=seed, fold_id=fold, blocks=blocks, targets=targets,
                        whitened=whitened, root_white=root_white, activity=activity)
                    counts["root_optimizer_updates"] += ROOT_UPDATES
                    counts["root_example_exposures"] += ROOT_UPDATES * BATCH_SIZE
                    counts["nonfinite_events"] += activity["nonfinite_events"]
                    counts["clipping_events"] += activity["root_clipping_events"]
                    root_model, tail_model = CR._raw_modules(seed, fold, beta_root, beta_tail)
                    item = evaluate_policy(
                        root_model, tail_model, arm_id=ARM_ID, seed_id=seed, fold_id=fold,
                        root_update=ROOT_UPDATES, sampled_episodes=SAMPLED_EVALUATION_EPISODES)
                    counts["exact_policy_evaluations"] += item.exact_policy_evaluations
                    counts["sampled_evaluation_episodes"] += item.sampled_evaluation_episodes
                    counts["sampled_evaluation_transitions"] += item.sampled_evaluation_transitions
                    vector = numpy.asarray(beta_root)
                    breakdown, summary = per_context_breakdown(root_model, tail_model)
                    if (abs(summary["max_regret"] - item.max_regret) > 1e-12
                            or abs(summary["min_tail_agreement"]
                                   - item.minimum_tail_agreement) > 1e-12):
                        raise LaunchRefusal(
                            "per-context breakdown disagrees with the frozen evaluation")
                    record["arms"][arm_name] = {
                        "beta_root": beta_root, "beta_root_initial": root_initial,
                        "d_learned_root": float(numpy.abs(vector - beta_root_star).max()),
                        "eps_L": EPS_L,
                        "g_learned_root": CR.gradient_infinity_norm(
                            root_block["design64"], targets, vector),
                        "gradient_ratio": (
                            CR.gradient_infinity_norm(root_block["design64"], targets, vector) / g_star
                            if g_star > 0 else None),
                        "competence": CR._competence_record(item),
                        "c_root_pass": c_root_pass(item, summary),
                        "per_context": breakdown, "per_context_summary": summary,
                        "activity": activity,
                        "wall_seconds": time.perf_counter() - started_arm,
                    }
                    exposure_rows.append({
                        "arm": arm_name, "stage": "root", "seed_id": seed, "fold_id": fold,
                        "parameter_displacement_l2": float(numpy.sqrt(
                            ((vector - numpy.asarray(root_initial)) ** 2).sum())),
                        "initialisation_scale_l2": float(numpy.sqrt(
                            (numpy.asarray(root_initial) ** 2).sum())),
                        "max_abs_coordinate_move": float(numpy.abs(
                            vector - numpy.asarray(root_initial)).max()),
                    })

                exact_root_model, exact_tail_model = CR._raw_modules(
                    seed, fold, beta_root_star, beta_tail)
                item = evaluate_policy(
                    exact_root_model, exact_tail_model, arm_id=ARM_ID, seed_id=seed, fold_id=fold,
                    root_update=ROOT_UPDATES, sampled_episodes=SAMPLED_EVALUATION_EPISODES)
                counts["exact_policy_evaluations"] += item.exact_policy_evaluations
                counts["sampled_evaluation_episodes"] += item.sampled_evaluation_episodes
                counts["sampled_evaluation_transitions"] += item.sampled_evaluation_transitions
                exact_breakdown, exact_summary = per_context_breakdown(
                    exact_root_model, exact_tail_model)
                record["arms"][EXACT_ROOT] = {
                    "beta_root": [float(v) for v in beta_root_star],
                    "d_learned_root": 0.0, "eps_L": EPS_L,
                    "g_learned_root": CR.gradient_infinity_norm(
                        root_block["design64"], targets, beta_root_star),
                    "gradient_ratio": (
                        CR.gradient_infinity_norm(root_block["design64"], targets, beta_root_star)
                        / g_star if g_star > 0 else None),
                    "competence": CR._competence_record(item),
                    "c_root_pass": c_root_pass(item, exact_summary),
                    "per_context": exact_breakdown, "per_context_summary": exact_summary,
                    "note": ("outcome-free closed-form ceiling on the same fixed-tail targets; "
                             "no optimizer trajectory, excluded from the exposure line"),
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
                "per-coordinate displacement of the recovered raw root vector from the exact "
                "deterministic root initialisation of the same seed and fold, per arm; the "
                "EXACT-ROOT-SOLVE arm has no optimizer trajectory and is excluded"
            ),
            "learning_rate": LEARNING_RATE, "root_updates": ROOT_UPDATES,
            "raw_per_coordinate_ceiling": ROOT_UPDATES * LEARNING_RATE,
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
            "branch_statistic": "C_root",
            "branch_statistic_definition": (
                "all_scores_finite AND all_choices_unique AND "
                "exact_eight_context_oracle_root_vector AND max_expected_regret <= 1/50"),
            "branch_statistic_amended_by": "owner decision D.18 (card section 13), before launch",
            "tail_rows_per_policy": TAIL_ROWS_PER_POLICY,
            "episodes_per_context": episodes_per_context,
            "index_law": {"offset": selection.OFFSET,
                          "law": "episode index i = OFFSET + j for j = 0 .. m-1",
                          "published_ranges_avoided": ["0..5119", "0..319"],
                          "offset_is_multiple_of_20": selection.OFFSET % 20 == 0},
            "canonical_context_order": canonical_labels,
            "target_context_id": TARGET_CONTEXT_ID,
            "tail_updates": TAIL_UPDATES, "root_updates": ROOT_UPDATES,
            "learning_rate": LEARNING_RATE, "batch_size": BATCH_SIZE,
            "tail_reproduction_tolerance": TAIL_REPRODUCTION_TOLERANCE,
            "tail_reference_record": str(
                Path(competence_record) if competence_record else COMPETENCE_RECORD),
            "admission": admission, "ledger": LEDGER,
            "source_status": source, "execution_topology": CR.topology_record(thread_cap),
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
    run.add_argument("--competence-record", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        path = run_object(args.output_root, thread_cap=args.thread_cap,
                          competence_record=args.competence_record)
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        numbers = record["reading_rule"]["numbers"]
        print(json.dumps({
            "path": str(path), "branch": record["reading_rule"]["branch"],
            "label": record["reading_rule"]["label"],
            "whitened_root_competent": numbers["whitened_root_competent"],
            "raw_root_competent": numbers["raw_root_competent"],
            "exact_root_competent": numbers["exact_root_competent"],
        }, sort_keys=True))
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, LaunchRefusal) as exc:
        print(f"UCOPE root-conditioning object stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
