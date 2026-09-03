#!/usr/bin/env python3
"""Runner for ``UCOPE-B-EXPLORE-PAID-ACQUISITION-B01``.

Object
------
Frozen by ``docs/research/candidates/ucope/UCOPE_PAID_ACQUISITION_B01_CARD_20260903.md`` under
the owner decision on D.22 option (a): open the paid-acquisition object under spec §11.1 with
**competence recorded, not required**.

Question: does the learner pay the probe cost exactly where information is worth buying -- at
``LINKED-p17_20-c9_100``, the unique context whose oracle net acquisition is positive
(``+0.021437``) -- and does the information it buys leave it better off than not having paid?

Branch statistic ``A_paid`` (card section 4) is the frozen ``acquisition_pass`` with its
``competence_pass`` conjunct removed and nothing else changed:

    root_action(TARGET) == "PROBE"
    AND target_delta_acquisition > 0
    AND direct_probe_component < 0
    AND root_action(cell) == "IMMEDIATE" for every other cell

Two arms on the same draw (offset ``2,000,000``, ``m = 40,960``):

* ``MARGIN-AWARE-TREATMENT`` -- the whitened MARGIN-AWARE tail learner exactly as run in the
  remedies object, gated on reproducing its published coefficients to ``1e-6``;
* ``EXACT-REFERENCE``        -- the exact two-stage solve on the same rows.

Every generation, design, whitening, training and evaluation path is imported from the
competence, root-conditioning and remedies runners, so there is one implementation of each.
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
    TARGET_CONTEXT_ID,
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.evaluation import (  # noqa: E402
    audit_policy_choices,
    enforce_conditional_acquisition,
    evaluate_policy,
)
from experiments.candidates.ucope.competence_first_scout_r01.oracle import (  # noqa: E402
    build_oracle,
)

REMEDIES_RUNNER = PROJECT_ROOT / "scripts/run_ucope_tail_margin_remedies_r01.py"


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RM = _module("ucope_tail_margin_remedies_r01", REMEDIES_RUNNER)
RC = RM.RC
CR = RM.CR
LaunchRefusal = CR.LaunchRefusal

OBJECT_ID = "UCOPE-B-EXPLORE-PAID-ACQUISITION-B01"
EVIDENCE_CLASS = "B/EXPLORE"
RESULT_FORMAT = "UCOPE_PAID_ACQUISITION_B01_RUN_RECORD_V1"
CARD = "docs/research/candidates/ucope/UCOPE_PAID_ACQUISITION_B01_CARD_20260903.md"
REMEDIES_RECORD = PROJECT_ROOT / (
    "temp/directions/ucope/exp/tail_margin_remedies_r01_20260903/complete/run-record.json")

# Card section 3 frozen-constants table.
ARM_ID = CR.ARM_ID
TREATMENT = "MARGIN-AWARE-TREATMENT"
REFERENCE = "EXACT-REFERENCE"
DRAW_OFFSET = RM.REMEDIES_OFFSET                     # 2,000,000
EPISODES_PER_CONTEXT = RM.ARMS["MARGIN-AWARE"]["episodes_per_context"]   # 40,960
TAIL_ROWS_PER_POLICY = 2 * EPISODES_PER_CONTEXT      # 81,920
TAIL_UPDATES = RM.ARMS["MARGIN-AWARE"]["tail_updates"]                  # 1,600
ROOT_UPDATES = RM.ROOT_UPDATES                       # 3,200
LEARNING_RATE = RM.LEARNING_RATE                     # 3e-3
HINGE_MARGIN = RM.HINGE_MARGIN                       # 0.024022
HINGE_WEIGHT = RM.HINGE_WEIGHT                       # 1.0
HINGE_WITNESS_PAIR = RM.HINGE_WITNESS_PAIR           # (5, 9)
SAMPLED_EVALUATION_EPISODES = CR.SAMPLED_EVALUATION_EPISODES
BETA_STAR = CR.BETA_STAR
EPS_L = CR.EPS_L
MAJORITY = CR.MAJORITY
POLICIES = 6
THREAD_CAP = 1
TAIL_REPRODUCTION_TOLERANCE = 1e-6
AGREEMENT_GATE = Fraction(19, 20)

LEDGER = {
    "authority": ["docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#11",
                  "docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.1", CARD],
    "still_gating": [
        "central_4gib_memory_admission",
        "section_4_integrity_items",
        "odd_training_even_held_out_separation",
        "whitening_from_training_rows_only_per_stage",
        "counter_addressed_index_law_offset_2000000",
        "tail_reproduction_within_1e-6",
        "section_5_2_nonzero_counts",
        "machine_generated_exposure_line",
        "section_6_2_learner_side_quarantine",
    ],
    "recorded_not_gating": [
        "clean_committed_source_inventory",
        "performance_ready_assessment",
        "execution_topology",
        "resource_telemetry_and_concurrent_load",
        "competence_record_section_11_1",
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
# Provenance and the published reference
# ---------------------------------------------------------------------------


def source_status_record() -> dict[str, Any]:
    """The remedies object's bound inventory, extended with this runner."""
    import hashlib

    record = RM.RC.source_status_record()
    for extra in (REMEDIES_RUNNER, Path(__file__).resolve()):
        if any(row["path"] == extra.relative_to(PROJECT_ROOT).as_posix()
               for row in record["files"]):
            continue
        record["files"].append({
            "path": extra.relative_to(PROJECT_ROOT).as_posix(),
            "size_bytes": extra.stat().st_size,
            "sha256": CR._sha256_file(extra),
        })
    record["files"] = sorted(record["files"], key=lambda row: row["path"])
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


def published_margin_aware(path: Path | None = None) -> dict[tuple[str, int], dict[str, Any]]:
    """The remedies object's MARGIN-AWARE per-policy record, keyed by (seed, fold)."""
    source = Path(path) if path is not None else REMEDIES_RECORD
    if not source.is_file():
        raise LaunchRefusal(
            f"tail-reproduction reference missing, cannot gate the treatment: {source}")
    record = json.loads(source.read_text(encoding="utf-8"))
    if record.get("object_id") != "UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01":
        raise LaunchRefusal("tail-reproduction reference is not the remedies run record")
    published = {}
    for row in record["policies"]:
        arm = row["arms"]["MARGIN-AWARE"]
        published[(row["seed_id"], int(row["fold_id"]))] = {
            "beta_tail": list(arm["beta_tail"]),
            "competence_pass": bool(arm["competence"]["competence_pass"]),
            "agreement_within_gate": bool(arm["agreement_within_gate"]),
            "count0_gap": float(arm["margin"]["count0_gap"]),
        }
    return published


def telemetry_record(concurrent_load: str | None) -> dict[str, Any]:
    """Observational only; never gating, never an admission decision (spec §11.4)."""
    record: dict[str, Any] = {
        "gating": False,
        "concurrent_load_declared": concurrent_load,
        "capture": None,
        "capture_error": None,
    }
    try:
        completed = subprocess.run(
            [sys.executable, str(CR.RESOURCE_PREFLIGHT), "capture"],
            cwd=PROJECT_ROOT, capture_output=True, text=True,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            record["capture"] = json.loads(completed.stdout)
        else:
            record["capture_error"] = (completed.stderr or completed.stdout).strip()[:400]
    except (OSError, ValueError, subprocess.SubprocessError) as exc:  # pragma: no cover
        record["capture_error"] = f"{type(exc).__name__}: {exc}"
    return record


# ---------------------------------------------------------------------------
# A_paid -- the frozen predicate minus its competence conjunct (card section 4)
# ---------------------------------------------------------------------------


def a_paid(audit: dict[str, Any]) -> dict[str, Any]:
    """The four conjuncts, reported separately so a failure names its own cause."""
    actions = audit["root_actions"]
    conjuncts = {
        "pays_at_target": actions[TARGET_CONTEXT_ID] == "PROBE",
        "target_delta_acquisition_positive": audit["target_delta_acquisition"] > 0,
        "direct_probe_component_negative": audit["direct_probe_component"] < 0,
        "refuses_everywhere_else": all(
            action == "IMMEDIATE" for cell, action in actions.items()
            if cell != TARGET_CONTEXT_ID),
    }
    return {
        "conjuncts": conjuncts,
        "a_paid_pass": all(conjuncts.values()),
        "failing_conjuncts": [name for name, value in conjuncts.items() if not value],
    }


def acquisition_measurements(audit: dict[str, Any]) -> dict[str, Any]:
    oracle = build_oracle()[TARGET_CONTEXT_ID]
    delta = float(audit["target_delta_acquisition"])
    baseline = float(oracle["baseline"])
    return {
        "target_delta_acquisition": delta,
        "direct_probe_component": float(audit["direct_probe_component"]),
        "learned_value_at_target": delta + baseline,
        "oracle_baseline_at_target": baseline,
        "oracle_probe_value_at_target": float(oracle["probe_value"]),
        "oracle_net_acquisition_at_target": float(oracle["net_acquisition"]),
        "acquisition_shortfall": float(oracle["net_acquisition"]) - delta,
        "root_actions": dict(audit["root_actions"]),
        "oracle_root_match": bool(audit["oracle_root_match"]),
    }


# ---------------------------------------------------------------------------
# Reading rule (card section 8), applied verbatim in its stated order
# ---------------------------------------------------------------------------


def apply_reading_rule(policies: list[dict[str, Any]]) -> dict[str, Any]:
    treatment = [row["arms"][TREATMENT]["a_paid"]["a_paid_pass"] for row in policies]
    reference = [row["arms"][REFERENCE]["a_paid"]["a_paid_pass"] for row in policies]
    numbers = {
        "branch_statistic": "A_paid",
        "majority_threshold": MAJORITY,
        "policies": len(policies),
        "treatment_flags": treatment, "reference_flags": reference,
        "treatment_count": sum(treatment), "reference_count": sum(reference),
        "treatment_all": all(treatment), "reference_all": all(reference),
        "treatment_majority": sum(treatment) >= MAJORITY,
        "competence_recorded_not_gating": True,
    }
    if numbers["treatment_all"]:
        return {"branch": "PA-A", "label": "PAID_ACQUISITION_POSITIVE", "numbers": numbers}
    if numbers["treatment_majority"] and numbers["reference_all"]:
        return {"branch": "PA-B", "label": "PAID_ACQUISITION_MAJORITY", "numbers": numbers}
    if numbers["reference_all"] and sum(treatment) < MAJORITY:
        return {"branch": "PA-C", "label": "REFERENCE_ONLY", "numbers": numbers}
    if not numbers["reference_all"]:
        return {"branch": "PA-D", "label": "REFERENCE_NOT_POSITIVE", "numbers": numbers}
    return {"branch": "PA-E", "label": "UNCLEAR", "numbers": numbers}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_object(output_root: str | Path, *, thread_cap: int = THREAD_CAP,
               episodes_per_context: int = EPISODES_PER_CONTEXT,
               tail_updates: int = TAIL_UPDATES, root_updates: int = ROOT_UPDATES,
               remedies_record: str | Path | None = None,
               concurrent_load: str | None = None) -> Path:
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
    telemetry = telemetry_record(concurrent_load)
    published = published_margin_aware(remedies_record)
    started = {"wall": time.perf_counter(), "cpu": time.process_time()}
    selection = CR._n_selection()
    selection.OFFSET = DRAW_OFFSET

    try:
        counts = {
            "environment_episodes": 0, "tail_rows": 0, "root_rows": 0,
            "tail_optimizer_updates": 0, "root_optimizer_updates": 0,
            "tail_example_exposures": 0, "root_example_exposures": 0,
            "hinge_rows_built": 0, "exact_solves": 0, "exact_policy_evaluations": 0,
            "sampled_evaluation_episodes": 0, "sampled_evaluation_transitions": 0,
            "acquisition_audits": 0, "nonfinite_events": 0, "clipping_events": 0,
        }
        policies: list[dict[str, Any]] = []
        exposure_rows: list[dict[str, Any]] = []
        evaluations: dict[str, list[Any]] = {TREATMENT: [], REFERENCE: []}

        for seed in B1_SEEDS:
            columns, _labels = CR.canonical_order(
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

                tail_white = CR.whitening(tail_block["design64"], stage="tail")
                root_white = CR.whitening(root_block["design64"], stage="root")
                beta_tail_star = CR.exact_solve(tail_block["design64"], tail_block["targets64"])
                counts["exact_solves"] += 1

                record: dict[str, Any] = {
                    "seed_id": seed, "fold_id": fold,
                    "tail_rows": int(tail_block["design64"].shape[0]),
                    "root_rows": int(root_block["design64"].shape[0]),
                    "whitening": {
                        "tail": {k: v for k, v in tail_white.items() if not k.startswith("_")},
                        "root": {k: v for k, v in root_white.items() if not k.startswith("_")},
                    },
                    "beta_tail_star": [float(v) for v in beta_tail_star],
                    "d_objective": float(
                        numpy.abs(beta_tail_star - numpy.asarray(BETA_STAR)).max()),
                    "eps_L": EPS_L,
                    "arms": {},
                }

                # ---- the treatment: the MARGIN-AWARE learner, gated on reproduction ----
                activity = CR._fresh_activity()
                started_arm = time.perf_counter()
                hinge_design = RM.hinge_directions(
                    columns["belief"][(columns["fold"] == (1 - fold)) & columns["probe"]])
                counts["hinge_rows_built"] += hinge_design.shape[0]
                beta_tail, tail_initial = RM.train_tail(
                    seed_id=seed, fold_id=fold, blocks=blocks, white=tail_white,
                    updates=tail_updates, hinge_design=hinge_design, activity=activity)
                counts["tail_optimizer_updates"] += tail_updates
                counts["tail_example_exposures"] += tail_updates * BATCH_SIZE

                reference_row = published.get((seed, fold))
                if reference_row is None:
                    raise LaunchRefusal(f"no published MARGIN-AWARE tail for {seed} fold {fold}")
                reproduction = float(numpy.abs(
                    numpy.asarray(beta_tail) - numpy.asarray(reference_row["beta_tail"])).max())
                if not reproduction <= TAIL_REPRODUCTION_TOLERANCE:
                    raise LaunchRefusal(
                        "tail-reproduction integrity item failed: "
                        f"{seed} fold {fold} max|delta| {reproduction:.6e} > "
                        f"{TAIL_REPRODUCTION_TOLERANCE:.0e}")

                targets = CR.root_targets_fp32(root_block, beta_tail)
                beta_root_star_treatment = CR.exact_solve(root_block["design64"], targets)
                counts["exact_solves"] += 1
                beta_root, root_initial = RC.train_root(
                    seed_id=seed, fold_id=fold, blocks=blocks, targets=targets,
                    whitened=True, root_white=root_white, activity=activity)
                counts["root_optimizer_updates"] += root_updates
                counts["root_example_exposures"] += root_updates * BATCH_SIZE
                counts["nonfinite_events"] += activity["nonfinite_events"]
                counts["clipping_events"] += (
                    activity["tail_clipping_events"] + activity["root_clipping_events"])

                root_model, tail_model = CR._raw_modules(seed, fold, beta_root, beta_tail)
                item = evaluate_policy(
                    root_model, tail_model, arm_id=ARM_ID, seed_id=seed, fold_id=fold,
                    root_update=root_updates, sampled_episodes=SAMPLED_EVALUATION_EPISODES)
                counts["exact_policy_evaluations"] += item.exact_policy_evaluations
                counts["sampled_evaluation_episodes"] += item.sampled_evaluation_episodes
                counts["sampled_evaluation_transitions"] += item.sampled_evaluation_transitions
                audit = audit_policy_choices(item.root_selected_labels, item.tail_periods)
                counts["acquisition_audits"] += 1
                breakdown, summary = RC.per_context_breakdown(root_model, tail_model)
                evaluations[TREATMENT].append(item)

                record["arms"][TREATMENT] = {
                    "beta_tail": beta_tail, "beta_root": beta_root,
                    "tail_updates": tail_updates, "root_updates": root_updates,
                    "hinge": {"margin": HINGE_MARGIN, "weight": HINGE_WEIGHT,
                              "witness_pair": list(HINGE_WITNESS_PAIR)},
                    "tail_reproduction": {
                        "published_beta_tail": reference_row["beta_tail"],
                        "max_abs_difference": reproduction,
                        "tolerance": TAIL_REPRODUCTION_TOLERANCE,
                        "pass": True,
                        "bitwise_identical": reproduction == 0.0,
                    },
                    "a_paid": a_paid(audit),
                    "acquisition": acquisition_measurements(audit),
                    "d_learned_tail": float(
                        numpy.abs(numpy.asarray(beta_tail) - beta_tail_star).max()),
                    "d_learned_root": float(
                        numpy.abs(numpy.asarray(beta_root) - beta_root_star_treatment).max()),
                    "competence_record": {
                        "gating": False,
                        "recorded_under": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.1",
                        "c_even_pass": bool(item.competence_pass),
                        "agreement_gate_pass": bool(summary["min_tail_agreement_within_gate"]),
                        "minimum_tail_agreement": float(item.minimum_tail_agreement),
                        "max_regret": float(item.max_regret),
                        "all_finite": bool(item.all_finite),
                        "all_unique": bool(item.all_unique),
                        "oracle_root_match": bool(item.oracle_root_match),
                        "margin_count0_gap": RM.margin_record(beta_tail)["count0_gap"],
                        "published_c_even_pass": reference_row["competence_pass"],
                        "published_agreement_gate_pass": reference_row["agreement_within_gate"],
                        "published_count0_gap": reference_row["count0_gap"],
                    },
                    "per_context": breakdown, "per_context_summary": summary,
                    "activity": activity,
                    "wall_seconds": time.perf_counter() - started_arm,
                }
                for stage, final, initial in (
                    ("tail", numpy.asarray(beta_tail), numpy.asarray(tail_initial)),
                    ("root", numpy.asarray(beta_root), numpy.asarray(root_initial)),
                ):
                    exposure_rows.append({
                        "arm": TREATMENT, "stage": stage, "seed_id": seed, "fold_id": fold,
                        "parameter_displacement_l2": float(
                            numpy.sqrt(((final - initial) ** 2).sum())),
                        "initialisation_scale_l2": float(numpy.sqrt((initial ** 2).sum())),
                        "max_abs_coordinate_move": float(numpy.abs(final - initial).max()),
                    })

                # ---- the reference: the exact two-stage solve on the same rows ----
                exact_targets = CR.root_targets_fp64(root_block, beta_tail_star)
                beta_root_reference = CR.exact_solve(root_block["design64"], exact_targets)
                counts["exact_solves"] += 1
                exact_root_model, exact_tail_model = CR._raw_modules(
                    seed, fold, beta_root_reference, beta_tail_star)
                exact_item = evaluate_policy(
                    exact_root_model, exact_tail_model, arm_id=ARM_ID, seed_id=seed,
                    fold_id=fold, root_update=root_updates,
                    sampled_episodes=SAMPLED_EVALUATION_EPISODES)
                counts["exact_policy_evaluations"] += exact_item.exact_policy_evaluations
                counts["sampled_evaluation_episodes"] += exact_item.sampled_evaluation_episodes
                counts["sampled_evaluation_transitions"] += (
                    exact_item.sampled_evaluation_transitions)
                exact_audit = audit_policy_choices(
                    exact_item.root_selected_labels, exact_item.tail_periods)
                counts["acquisition_audits"] += 1
                exact_breakdown, exact_summary = RC.per_context_breakdown(
                    exact_root_model, exact_tail_model)
                evaluations[REFERENCE].append(exact_item)

                record["arms"][REFERENCE] = {
                    "beta_tail": [float(v) for v in beta_tail_star],
                    "beta_root": [float(v) for v in beta_root_reference],
                    "a_paid": a_paid(exact_audit),
                    "acquisition": acquisition_measurements(exact_audit),
                    "d_learned_tail": 0.0, "d_learned_root": 0.0,
                    "competence_record": {
                        "gating": False,
                        "recorded_under": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.1",
                        "c_even_pass": bool(exact_item.competence_pass),
                        "agreement_gate_pass": bool(
                            exact_summary["min_tail_agreement_within_gate"]),
                        "minimum_tail_agreement": float(exact_item.minimum_tail_agreement),
                        "max_regret": float(exact_item.max_regret),
                        "all_finite": bool(exact_item.all_finite),
                        "all_unique": bool(exact_item.all_unique),
                        "oracle_root_match": bool(exact_item.oracle_root_match),
                        "margin_count0_gap": RM.margin_record(beta_tail_star)["count0_gap"],
                    },
                    "per_context": exact_breakdown, "per_context_summary": exact_summary,
                    "note": ("outcome-free closed-form reference on the same rows; no optimizer "
                             "trajectory, excluded from the exposure line"),
                }
                policies.append(record)

        # The frozen conditional predicate, recorded beside A_paid, never gating.
        for arm_name, items in evaluations.items():
            conditioned = enforce_conditional_acquisition(
                tuple(items), final_root_update=root_updates)
            keyed = {(row.seed_id, row.fold_id): row for row in conditioned}
            for row in policies:
                frozen = keyed[(row["seed_id"], row["fold_id"])]
                row["arms"][arm_name]["frozen_conditional_acquisition"] = {
                    "gating": False,
                    "source": "evaluation.enforce_conditional_acquisition",
                    "acquisition_pass": bool(frozen.acquisition_pass),
                    "target_delta_acquisition": frozen.target_delta_acquisition,
                    "direct_probe_component": frozen.direct_probe_component,
                    "suppressed_by_conditional_exposure": (
                        frozen.target_delta_acquisition is None),
                }

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
                "deterministic initialisation of the same seed and fold, for the treatment arm; "
                "EXACT-REFERENCE has no optimizer trajectory and is excluded"),
            "learning_rate": LEARNING_RATE, "tail_updates": tail_updates,
            "root_updates": root_updates,
            "raw_per_coordinate_ceiling_tail": tail_updates * LEARNING_RATE,
            "raw_per_coordinate_ceiling_root": root_updates * LEARNING_RATE,
            "rows": exposure_rows,
            "minimum_max_abs_coordinate_move": min(moves),
            "maximum_max_abs_coordinate_move": max(moves),
            "learner_can_move_in_its_budget": bool(moves) and min(moves) > 0.0,
        }
        if not exposure["learner_can_move_in_its_budget"]:
            raise LaunchRefusal("exposure line reports no parameter movement in the budget")

        oracle = build_oracle()
        reading = apply_reading_rule(policies)
        record = {
            "format": RESULT_FORMAT, "schema_version": 1, "object_id": OBJECT_ID,
            "evidence_class": EVIDENCE_CLASS, "card": CARD, "complete": True,
            "attempt_id": attempt_id, "arm_id": ARM_ID,
            "arms": [TREATMENT, REFERENCE],
            "branch_statistic": "A_paid",
            "branch_statistic_definition": (
                'root_action(TARGET) == "PROBE" AND target_delta_acquisition > 0 AND '
                'direct_probe_component < 0 AND root_action(cell) == "IMMEDIATE" elsewhere'),
            "branch_statistic_relation_to_frozen_predicate": (
                "evaluation.enforce_conditional_acquisition's acquisition_pass with its "
                "competence_pass conjunct removed and nothing else changed (card section 4)"),
            "competence_policy": "recorded, not required (MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.1)",
            "target_context_id": TARGET_CONTEXT_ID,
            "oracle_at_target": {
                "action": oracle[TARGET_CONTEXT_ID]["action"],
                "baseline": float(oracle[TARGET_CONTEXT_ID]["baseline"]),
                "probe_value": float(oracle[TARGET_CONTEXT_ID]["probe_value"]),
                "direct_probe": float(oracle[TARGET_CONTEXT_ID]["direct_probe"]),
                "net_acquisition": float(oracle[TARGET_CONTEXT_ID]["net_acquisition"]),
            },
            "oracle_probe_contexts": [
                context_id(c) for c in CONTEXTS
                if oracle[context_id(c)]["action"] == "PROBE"],
            "index_law": {
                "offset": DRAW_OFFSET,
                "law": "episode index i = OFFSET + j for j = 0 .. m-1",
                "published_ranges_avoided": ["0..5119", "0..319", "1000000..1081919"],
                "offset_is_multiple_of_20": DRAW_OFFSET % 20 == 0,
                "reused_from": "UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01 (card section 5)",
            },
            "odd_training_even_held_out_separation": {
                "training_support": list(K_TRAIN), "held_out_support": list(K_EVAL),
                "hinge_witness_pair": list(HINGE_WITNESS_PAIR),
                "hinge_witness_inside_training_support": all(
                    period in K_TRAIN for period in HINGE_WITNESS_PAIR),
                "held_out_periods_used_in_training": [],
            },
            "episodes_per_context": episodes_per_context,
            "tail_rows_per_policy": 2 * episodes_per_context,
            "tail_updates": tail_updates, "root_updates": root_updates,
            "learning_rate": LEARNING_RATE, "batch_size": BATCH_SIZE,
            "hinge_margin": HINGE_MARGIN, "hinge_weight": HINGE_WEIGHT,
            "eps_L": EPS_L, "majority_threshold": MAJORITY,
            "tail_reproduction_tolerance": TAIL_REPRODUCTION_TOLERANCE,
            "tail_reference_record": str(
                Path(remedies_record) if remedies_record else REMEDIES_RECORD),
            "beta_star": list(BETA_STAR), "agreement_gate": float(AGREEMENT_GATE),
            "admission": admission, "ledger": LEDGER,
            "source_status": source, "resource_telemetry": telemetry,
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
                "no_rerun_with_changes": True,
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
    run.add_argument("--thread-cap", type=int, default=THREAD_CAP)
    run.add_argument("--remedies-record", default=None)
    run.add_argument("--concurrent-load", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        path = run_object(args.output_root, thread_cap=args.thread_cap,
                          remedies_record=args.remedies_record,
                          concurrent_load=args.concurrent_load)
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        reading = record["reading_rule"]
        print(json.dumps({
            "path": str(path), "branch": reading["branch"], "label": reading["label"],
            "treatment_count": reading["numbers"]["treatment_count"],
            "reference_count": reading["numbers"]["reference_count"],
        }, sort_keys=True))
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, LaunchRefusal) as exc:
        print(f"UCOPE paid-acquisition object stopped: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
