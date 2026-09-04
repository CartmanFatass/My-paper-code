"""Deterministic same-draw reconstruction for the UCOPE root localization audit."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    B1_SEEDS,
    CONTEXTS,
    K_EVAL,
    K_TRAIN,
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import (  # noqa: E402
    root_basis,
    tail_basis,
)
from experiments.candidates.ucope.competence_first_scout_r01.oracle import (  # noqa: E402
    build_oracle,
    direct_probe,
    expected_tail,
    joint_count_probability,
    optimal_tail,
    posterior_short,
)


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


TW = _load("ucope_root_audit_three_witness", "experiments/candidates/ucope/three_witness_hinge_r01/experiment.py")
RC = TW.RC
CR = TW.CR

OBJECT_ID = "UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01"
INPUT_OBJECT_ID = "UCOPE-B-EXPLORE-THREE-WITNESS-HINGE-R01"
INPUT_LAUNCH_SHA = "71f693ae1f1634e3e9c45461cc3c6d61c18394b8"
CARD = "docs/research/candidates/ucope/UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_CARD_20260904.md"
EXPECTED_BYTES = 1_273_684
EXPECTED_SHA256 = "1c8b1d217fc924271da62061f7226642a3d040995aba069cabb5df9ff336b676"
OFFSET = 2_000_000
EPISODES_PER_CONTEXT = 40_960
ARMS = ("DOSE-MATCHED-SINGLE", "THREE-WITNESS")
IMPLICATED = (
    ("ucope-scout-r01-b1-fresh-00", 1),
    ("ucope-scout-r01-b1-fresh-01", 0),
)
FALSE_POSITIVE_CONTEXT = "LINKED-p17_20-c7_50"
PROFITABLE_CONTEXT = "LINKED-p17_20-c9_100"
ABS_TOL = 1e-12
COST_UNIT_SECONDS = 61.827
TOTAL_CAP_SECONDS = 185.481


class ReconstructionFailure(RuntimeError):
    """The carded binding or numerical reconstruction failed."""


def _numpy():
    import numpy

    return numpy


def _torch():
    import torch

    return torch


def project_cost(*, replay_episodes: int = 983_040,
                 replay_transitions: int = 4_915_200,
                 live_exact_root_solves: int = 12,
                 policy_pairs: int = 6) -> dict[str, Any]:
    scale = max(
        replay_episodes / 983_040,
        replay_transitions / 4_915_200,
        live_exact_root_solves / 12,
        policy_pairs / 6,
    )
    projected = round(3.0 * COST_UNIT_SECONDS * scale, 3)
    return {
        "object_id": OBJECT_ID,
        "command": "project-cost",
        "law": ("3 * 61.827 * max(replay_episodes / 983040, "
                "replay_transitions / 4915200, live_exact_root_solves / 12, "
                "policy_pairs / 6)"),
        "inputs": {
            "replay_episodes": replay_episodes,
            "replay_transitions": replay_transitions,
            "live_exact_root_solves": live_exact_root_solves,
            "policy_pairs": policy_pairs,
        },
        "projected_total_seconds": projected,
        "total_machine_time_cap_seconds": TOTAL_CAP_SECONDS,
        "within_cap": projected <= TOTAL_CAP_SECONDS,
    }


def _max_abs(left, right) -> float:
    numpy = _numpy()
    return float(numpy.max(numpy.abs(
        numpy.asarray(left, dtype=numpy.float64)
        - numpy.asarray(right, dtype=numpy.float64))))


def _finite(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return value is not None
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, dict):
        return all(_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite(item) for item in value)
    return True


def bind_retained_summary(path: str | Path, *, expected_bytes: int = EXPECTED_BYTES,
                          expected_sha256: str = EXPECTED_SHA256) -> tuple[dict[str, Any], dict[str, Any]]:
    source = Path(path)
    payload = source.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) != expected_bytes or digest != expected_sha256:
        raise ReconstructionFailure("retained summary byte-count/SHA-256 binding failed")
    value = json.loads(payload.decode("utf-8"))
    return value, {"path": str(source), "bytes": len(payload), "sha256": digest}


def _validate_inventory(retained: dict[str, Any], *, seeds: Sequence[str],
                        episodes_per_context: int, production: bool) -> dict[tuple[str, int], dict[str, Any]]:
    if retained.get("object_id") != INPUT_OBJECT_ID or retained.get("complete") is not True:
        raise ReconstructionFailure("retained object identity/completeness mismatch")
    if production and retained.get("launch_sha") != INPUT_LAUNCH_SHA:
        raise ReconstructionFailure("retained launch SHA mismatch")
    paired = retained.get("paired_rows", {})
    if (paired.get("offset") != OFFSET
            or paired.get("episodes_per_context") != episodes_per_context
            or tuple(paired.get("training_support", ())) != K_TRAIN
            or tuple(paired.get("evaluation_support", ())) != K_EVAL):
        raise ReconstructionFailure("retained draw/support inventory mismatch")
    if tuple(retained.get("arm_order", ())) != ARMS:
        raise ReconstructionFailure("retained arm order mismatch")
    expected = [(seed, fold) for seed in seeds for fold in (0, 1)]
    policies = retained.get("policies")
    if not isinstance(policies, list) or [
            (row.get("seed_id"), row.get("fold_id")) for row in policies] != expected:
        raise ReconstructionFailure("retained policy order/inventory mismatch")
    cells = [context_id(context) for context in CONTEXTS]
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    for row in policies:
        for arm in ARMS:
            item = row.get("arms", {}).get(arm, {})
            if (len(item.get("beta_tail", ())) != 5 or len(item.get("beta_root", ())) != 7
                    or set(item.get("per_context", {})) != set(cells)
                    or not _finite(item)):
                raise ReconstructionFailure("retained live-arm inventory/nonfinite mismatch")
        reference = row.get("exact_reference", {})
        if (len(reference.get("beta_tail", ())) != 5
                or len(reference.get("beta_root", ())) != 7
                or not _finite(reference)):
            raise ReconstructionFailure("retained MSE reference inventory/nonfinite mismatch")
        indexed[(row["seed_id"], int(row["fold_id"]))] = row
    return indexed


def _fp32_scores(beta, bases) -> list[float]:
    torch = _torch()
    vector = torch.tensor(beta, dtype=torch.float32)
    design = torch.tensor(bases, dtype=torch.float32)
    values = (design * vector).sum(dim=-1)
    if not torch.isfinite(values).all().item():
        raise ReconstructionFailure("nonfinite exact-policy score")
    return [float(value) for value in values.tolist()]


def evaluate_exact_policy(beta_root, beta_tail) -> dict[str, Any]:
    """Accepted FP32 basis scores plus the exact rational regret/C_root audit."""
    oracle = build_oracle()
    contexts: dict[str, Any] = {}
    root_actions: dict[str, str] = {}
    all_unique = True
    max_regret = Fraction(0)
    for context in CONTEXTS:
        link, reliability, cost = context
        cell = context_id(context)
        labels = ("PROBE", *(f"IMMEDIATE:{period}" for period in K_EVAL))
        bases = [root_basis(action_probe=True, period=0, cost=float(cost),
                            linked=link == "LINKED", reliability=float(reliability))]
        bases.extend(root_basis(action_probe=False, period=period, cost=float(cost),
                                linked=link == "LINKED", reliability=float(reliability))
                     for period in K_EVAL)
        root_values = _fp32_scores(beta_root, bases)
        root_ranked = sorted((value, -index, label)
                             for index, (label, value) in enumerate(zip(labels, root_values)))
        all_unique &= root_ranked[-1][0] != root_ranked[-2][0]
        selected = root_ranked[-1][2]
        action = "PROBE" if selected == "PROBE" else "IMMEDIATE"
        root_actions[cell] = action
        learned_tail_value = Fraction(0)
        tail_periods: dict[str, int] = {}
        for count in range(7):
            belief = posterior_short(link, reliability, count)
            tail_values = _fp32_scores(beta_tail, [
                tail_basis(belief=float(belief), period=period) for period in K_EVAL])
            ranked = sorted((value, -index, period)
                            for index, (period, value) in enumerate(zip(K_EVAL, tail_values)))
            all_unique &= ranked[-1][0] != ranked[-2][0]
            period = ranked[-1][2]
            tail_periods[str(count)] = period
            mass = (joint_count_probability("SHORT", reliability, count)
                    + joint_count_probability("LONG", reliability, count))
            learned_tail_value += mass * expected_tail(period, belief)
        learned = (learned_tail_value + direct_probe(cost) if selected == "PROBE"
                   else expected_tail(int(selected.split(":")[1]), Fraction(1, 2)))
        optimum = max(oracle[cell]["baseline"], oracle[cell]["probe_value"])
        regret = optimum - learned
        max_regret = max(max_regret, regret)
        contexts[cell] = {
            "root_action": action,
            "root_selected_label": selected,
            "root_score_margin": root_ranked[-1][0] - root_ranked[-2][0],
            "root_scores": dict(zip(labels, root_values)),
            "oracle_action": oracle[cell]["action"],
            "root_action_matches_oracle": action == oracle[cell]["action"],
            "expected_regret": float(regret),
            "tail_periods": tail_periods,
        }
    oracle_match = root_actions == {cell: row["action"] for cell, row in oracle.items()}
    c_root = bool(all_unique and oracle_match and max_regret <= Fraction(1, 50))
    return {
        "all_finite": True,
        "all_unique": bool(all_unique),
        "oracle_root_match": oracle_match,
        "maximum_regret": float(max_regret),
        "c_root": c_root,
        "root_actions": root_actions,
        "named_context_actions": {
            FALSE_POSITIVE_CONTEXT: root_actions[FALSE_POSITIVE_CONTEXT],
            PROFITABLE_CONTEXT: root_actions[PROFITABLE_CONTEXT],
        },
        "contexts": contexts,
    }


def retained_root_score_readout(beta_root) -> dict[str, Any]:
    """Read retained root scores/margins without another live exact-policy evaluation."""
    rows: dict[str, Any] = {}
    for context in CONTEXTS:
        link, reliability, cost = context
        cell = context_id(context)
        labels = ("PROBE", *(f"IMMEDIATE:{period}" for period in K_EVAL))
        bases = [root_basis(action_probe=True, period=0, cost=float(cost),
                            linked=link == "LINKED", reliability=float(reliability))]
        bases.extend(root_basis(action_probe=False, period=period, cost=float(cost),
                                linked=link == "LINKED", reliability=float(reliability))
                     for period in K_EVAL)
        scores = _fp32_scores(beta_root, bases)
        ranked = sorted((value, -index, label)
                        for index, (label, value) in enumerate(zip(labels, scores)))
        rows[cell] = {
            "root_selected_label": ranked[-1][2],
            "root_score_margin": ranked[-1][0] - ranked[-2][0],
            "root_scores": dict(zip(labels, scores)),
        }
    return rows


def finite_target_margins(columns, canonical_labels: Sequence[str], fold_id: int,
                          targets) -> dict[str, Any]:
    numpy = _numpy()
    root_mask = columns["fold"] == fold_id
    contexts = numpy.tile(numpy.asarray(canonical_labels, dtype=object),
                          columns["fold"].size // len(canonical_labels))[root_mask]
    probe = columns["probe"][root_mask]
    periods = columns["period"][root_mask]
    values = numpy.asarray(targets, dtype=numpy.float64)
    rows = {}
    for cell in (context_id(context) for context in CONTEXTS):
        context_mask = contexts == cell
        probe_values = values[context_mask & probe]
        immediate = {
            str(period): float(values[context_mask & ~probe & (periods == period)].mean())
            for period in K_TRAIN
        }
        if not probe_values.size or any(not math.isfinite(value) for value in immediate.values()):
            raise ReconstructionFailure("target-margin group inventory/nonfinite mismatch")
        best_period = max(K_TRAIN, key=lambda period: (immediate[str(period)], -period))
        probe_mean = float(probe_values.mean())
        rows[cell] = {
            "probe_mean_target": probe_mean,
            "immediate_mean_targets": immediate,
            "best_immediate_period": best_period,
            "best_immediate_mean_target": immediate[str(best_period)],
            "probe_minus_best_immediate": probe_mean - immediate[str(best_period)],
        }
    return rows


def apply_result_rule(policies: list[dict[str, Any]], *, reconstruction_passed: bool = True) -> dict[str, Any]:
    if not reconstruction_passed:
        return {"branch": "RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE", "refinement": None}
    index = {(row["seed_id"], row["fold_id"]): row for row in policies}
    target_pipeline = True
    finite_residual = True
    target_crossing = True
    for identity in IMPLICATED:
        row = index[identity]
        treatment = row["arms"]["THREE-WITNESS"]
        comparator = row["arms"]["DOSE-MATCHED-SINGLE"]
        t_exact = treatment["exact_policy"]["root_actions"][FALSE_POSITIVE_CONTEXT]
        c_exact = comparator["exact_policy"]["root_actions"][FALSE_POSITIVE_CONTEXT]
        t_finite = treatment["retained_finite_root"]["root_actions"][FALSE_POSITIVE_CONTEXT]
        target_pipeline &= t_exact == "PROBE" and c_exact == "IMMEDIATE"
        finite_residual &= t_exact == "IMMEDIATE" and c_exact == "IMMEDIATE" and t_finite == "PROBE"
        target_crossing &= (
            treatment["target_margins"][FALSE_POSITIVE_CONTEXT]["probe_minus_best_immediate"] > 0.0
            and comparator["target_margins"][FALSE_POSITIVE_CONTEXT]["probe_minus_best_immediate"] <= 0.0)
    if target_pipeline:
        return {
            "branch": "ROOT_TARGET_PIPELINE_SHIFT_SUPPORTED",
            "refinement": "TARGET_ARRAY_CROSSING" if target_crossing else "EXACT_PROJECTION_CROSSING",
        }
    if finite_residual:
        return {"branch": "FINITE_ROOT_FIT_RESIDUAL_SUPPORTED", "refinement": None}
    return {"branch": "MIXED_ROOT_CAUSE", "refinement": None}


def _admission(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if (value.get("passed") is not True or value.get("physical_floor_pass") is not True
            or value.get("effective_floor_pass") is not True):
        raise ReconstructionFailure("fresh central memory admission failed")
    return value


def _launch_sha() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()


def _peak_rss_bytes() -> int | None:
    try:
        if sys.platform == "win32":
            class Counters(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ]
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if not ctypes.windll.psapi.GetProcessMemoryInfo(
                    handle, ctypes.byref(counters), counters.cb):
                return None
            return int(counters.PeakWorkingSetSize)
        import resource
        value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return value * (1 if sys.platform == "darwin" else 1024)
    except (AttributeError, OSError, ValueError):
        return None


def enforce_wall_cap(started: float, *, production: bool) -> float:
    elapsed = time.perf_counter() - started
    if production and elapsed > TOTAL_CAP_SECONDS:
        raise ReconstructionFailure(
            f"actual wall {elapsed:.6f}s exceeded {TOTAL_CAP_SECONDS:.3f}s cap")
    return elapsed


def reconstruct(retained: dict[str, Any], *, seeds: Sequence[str] = B1_SEEDS,
                episodes_per_context: int = EPISODES_PER_CONTEXT,
                production: bool = True) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    numpy = _numpy()
    indexed = _validate_inventory(
        retained, seeds=seeds, episodes_per_context=episodes_per_context, production=production)
    selection = CR._n_selection()
    old_offset = selection.OFFSET
    selection.OFFSET = OFFSET
    policies: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    try:
        for seed in seeds:
            columns, labels = CR.canonical_order(
                selection.generate_columns(seed, episodes_per_context))
            for fold in (0, 1):
                retained_policy = indexed[(seed, fold)]
                blocks = CR.stage_designs(columns, fold)
                exact_tail = CR.exact_solve(
                    blocks["tail"]["design64"], blocks["tail"]["targets64"])
                tail_error = _max_abs(exact_tail, retained_policy["exact_reference"]["beta_tail"])
                checks.append({"kind": "MSE_EXACT_TAIL", "seed_id": seed, "fold_id": fold,
                               "maximum_absolute_error": tail_error, "passed": tail_error <= ABS_TOL})
                reference_targets = CR.root_targets_fp32(blocks["root"], exact_tail)
                exact_reference_root = CR.exact_solve(
                    blocks["root"]["design64"], reference_targets)
                root_error = _max_abs(
                    exact_reference_root, retained_policy["exact_reference"]["beta_root"])
                checks.append({"kind": "MSE_EXACT_ROOT", "seed_id": seed, "fold_id": fold,
                               "maximum_absolute_error": root_error, "passed": root_error <= ABS_TOL})
                policy = {"seed_id": seed, "fold_id": fold, "arms": {}}
                for arm in ARMS:
                    retained_arm = retained_policy["arms"][arm]
                    beta_tail = retained_arm["beta_tail"]
                    beta_root_retained = retained_arm["beta_root"]
                    targets = CR.root_targets_fp32(blocks["root"], beta_tail)
                    beta_root_exact = CR.exact_solve(blocks["root"]["design64"], targets)
                    residual = _max_abs(beta_root_retained, beta_root_exact)
                    retained_residual = float(retained_arm["d_learned_root"])
                    residual_error = abs(residual - retained_residual)
                    checks.append({
                        "kind": "LIVE_ROOT_DISTANCE", "seed_id": seed, "fold_id": fold,
                        "arm": arm, "recomputed": residual, "retained": retained_residual,
                        "absolute_error": residual_error, "passed": residual_error <= ABS_TOL,
                    })
                    policy["arms"][arm] = {
                        "retained_beta_tail": list(beta_tail),
                        "live_root_target_array_fp32": [float(value) for value in targets],
                        "live_exact_beta_root": [float(value) for value in beta_root_exact],
                        "target_margins": finite_target_margins(columns, labels, fold, targets),
                        "exact_policy": evaluate_exact_policy(beta_root_exact, beta_tail),
                        "retained_finite_root": {
                            "beta_root": list(beta_root_retained),
                            "root_actions": dict(retained_arm["competence"]["root_actions"]),
                            "oracle_root_match": bool(retained_arm["competence"]["oracle_root_match"]),
                            "maximum_regret": float(retained_arm["competence"]["max_regret"]),
                            "c_root": bool(retained_arm["c_root"]),
                            "contexts": retained_arm["per_context"],
                            "named_context_actions": {
                                FALSE_POSITIVE_CONTEXT: retained_arm["per_context"][FALSE_POSITIVE_CONTEXT]["root_action"],
                                PROFITABLE_CONTEXT: retained_arm["per_context"][PROFITABLE_CONTEXT]["root_action"],
                            },
                            "root_score_readout": retained_root_score_readout(beta_root_retained),
                        },
                        "recomputed_d_root": residual,
                        "retained_d_learned_root": retained_residual,
                        "d_root_absolute_error": residual_error,
                    }
                policies.append(policy)
    finally:
        selection.OFFSET = old_offset
    counts = {
        "replayed_environment_episodes": len(seeds) * len(CONTEXTS) * episodes_per_context,
        "replayed_environment_transitions": len(seeds) * len(CONTEXTS) * episodes_per_context * 5,
        "new_unique_draw_keys": 0,
        "new_seed_identities": 0,
        "new_draw_identities": 0,
        "new_independent_sample_units": 0,
        "learner_training_rows": 0,
        "root_blocks_reconstructed": len(seeds) * 2,
        "live_arm_target_arrays_computed": len(seeds) * 2 * len(ARMS),
        "live_arm_exact_root_solves": len(seeds) * 2 * len(ARMS),
        "exact_policy_evaluations": len(seeds) * 2 * len(ARMS),
        "mse_exact_tail_checks": len(seeds) * 2,
        "mse_exact_root_checks": len(seeds) * 2,
        "live_root_distance_checks": len(seeds) * 2 * len(ARMS),
        "optimizer_constructions": 0,
        "optimizer_steps": 0,
        "parameter_updates": 0,
        "fresh_sampled_evaluation_episodes": 0,
    }
    return policies, checks, counts


def run_audit(retained_summary: str | Path, output_root: str | Path,
              admission_receipt: str | Path, *, thread_cap: int = 1,
              argv: Sequence[str] | None = None, expected_bytes: int = EXPECTED_BYTES,
              expected_sha256: str = EXPECTED_SHA256, seeds: Sequence[str] = B1_SEEDS,
              episodes_per_context: int = EPISODES_PER_CONTEXT,
              production: bool = True) -> Path:
    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "summary.json"
    started = time.perf_counter()
    launch_argv = list(argv or sys.argv)
    launch_sha = None
    admission = None
    binding = None
    policies = None
    checks = None
    counts = None
    cost = None
    try:
        launch_sha = _launch_sha()
        if thread_cap != 1:
            raise ReconstructionFailure("audit requires exactly one intra-op thread")
        admission = _admission(admission_receipt)
        retained, binding = bind_retained_summary(
            retained_summary, expected_bytes=expected_bytes, expected_sha256=expected_sha256)
        CR._configure_topology(thread_cap)
        policies, checks, counts = reconstruct(
            retained, seeds=seeds, episodes_per_context=episodes_per_context,
            production=production)
        expected_checks = len(seeds) * 2 * (2 + len(ARMS))
        if len(checks) != expected_checks or not all(row["passed"] for row in checks):
            raise ReconstructionFailure(
                f"one or more of the {expected_checks} numerical reconstruction predicates failed")
        if not _finite(policies) or any(value < 0 for value in counts.values()):
            raise ReconstructionFailure("nonfinite output or invalid count")
        cost = project_cost(
            replay_episodes=counts["replayed_environment_episodes"],
            replay_transitions=counts["replayed_environment_transitions"],
            live_exact_root_solves=counts["live_arm_exact_root_solves"],
            policy_pairs=len(policies),
        )
        if production and (cost["projected_total_seconds"] != TOTAL_CAP_SECONDS
                           or cost["within_cap"] is not True):
            raise ReconstructionFailure("frozen cost projection/cap mismatch")
        summary = {
            "object_id": OBJECT_ID, "evidence_class": "A/RECON", "card": CARD,
            "complete": False, "scientific_polarity": None,
            "launch_sha": launch_sha, "argv": launch_argv,
            "retained_input_binding": binding, "admission": admission,
            "arm_order": list(ARMS), "policy_order": [
                {"seed_id": row["seed_id"], "fold_id": row["fold_id"]} for row in policies],
            "counts": counts,
            "exposure": {
                **counts,
                "parameter_displacement": 0.0,
                "initialization_scale": None,
                "parameters_read_only": True,
            },
            "reconstruction_tolerance": {"absolute": ABS_TOL, "relative": None},
            "reconstruction_checks": checks,
            "policies": policies,
            "projected_cost": cost,
            "resources": {
                "wall_seconds": None, "peak_rss_bytes": None,
                "status": "resources_unmeasured",
            },
        }
        json.dumps(summary, indent=2, sort_keys=True)
        enforce_wall_cap(started, production=production)
        summary["result_rule"] = apply_result_rule(policies)
        summary["complete"] = True
        json.dumps(summary, indent=2, sort_keys=True)
        peak_rss = _peak_rss_bytes()
        summary["resources"] = {
            "wall_seconds": enforce_wall_cap(started, production=production),
            "peak_rss_bytes": peak_rss,
            "status": "measured" if peak_rss is not None else "resources_unmeasured",
        }
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError,
            ReconstructionFailure) as exc:
        peak_rss = _peak_rss_bytes()
        summary = {
            "object_id": OBJECT_ID, "evidence_class": "A/RECON", "complete": False,
            "scientific_polarity": None,
            "launch_sha": launch_sha, "argv": launch_argv,
            "result_rule": {
                "branch": "RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE",
                "refinement": None,
            },
            "failure_type": type(exc).__name__, "failure_reason": str(exc),
            "resources": {"wall_seconds": time.perf_counter() - started,
                          "peak_rss_bytes": peak_rss,
                          "status": "measured" if peak_rss is not None else "resources_unmeasured"},
        }
        if admission is not None:
            summary["admission"] = admission
        if binding is not None:
            summary["retained_input_binding"] = binding
        if counts is not None:
            summary["executed_counts"] = counts
        if checks is not None:
            summary["reconstruction_checks"] = checks
        if cost is not None:
            summary["projected_cost"] = cost
    destination.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return destination
