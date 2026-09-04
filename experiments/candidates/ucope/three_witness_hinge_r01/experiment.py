"""Two-arm implementation of UCOPE-B-EXPLORE-THREE-WITNESS-HINGE-R01.

Generation, design construction, whitening, initialization, cyclic batches, root training and
evaluation are imported from the accepted UCOPE chain.  This module owns only the signed hinge,
the paired two-arm loop, the frozen reading rule and the compact result record.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from fractions import Fraction
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    B1_SEEDS,
    BATCH_SIZE,
    CONTEXTS,
    K_EVAL,
    K_TRAIN,
    context_id,
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


def _load(name: str, relative: str):
    path = PROJECT_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


RC = _load("ucope_three_witness_root", "scripts/run_ucope_root_conditioning_r01.py")
CR = RC.CR
TM = _load("ucope_three_witness_predecessor", "scripts/run_ucope_tail_margin_remedies_r01.py")
LaunchRefusal = CR.LaunchRefusal

OBJECT_ID = "UCOPE-B-EXPLORE-THREE-WITNESS-HINGE-R01"
EVIDENCE_CLASS = "B/EXPLORE"
CARD = "docs/research/candidates/ucope/UCOPE_THREE_WITNESS_HINGE_R01_CARD_20260904.md"
RESULT_FORMAT = "UCOPE_THREE_WITNESS_HINGE_R01_SUMMARY_V1"
OFFSET = 2_000_000
EPISODES_PER_CONTEXT = 40_960
TAIL_UPDATES = 1_600
ROOT_UPDATES = 3_200
SAMPLED_EVALUATION_EPISODES = CR.SAMPLED_EVALUATION_EPISODES
LEARNING_RATE = CR.LEARNING_RATE
ARM_ID = CR.ARM_ID
BETA_STAR = CR.BETA_STAR
EPS_L = CR.EPS_L
MARGIN = 0.024022
AGREEMENT_GATE = Fraction(19, 20)
WITNESS_PAIRS = ((1, 5), (3, 7), (5, 9))
HELD_OUT_PAIRS = ((2, 4), (4, 6), (6, 8))
ARMS = {
    "DOSE-MATCHED-SINGLE": (((5, 9), 3.0),),
    "THREE-WITNESS": (((1, 5), 1.0), ((3, 7), 1.0), ((5, 9), 1.0)),
}
NEIGHBOUR_SECONDS = 61.827
ALLOWANCE = 3.0
ARM_CAP_SECONDS = 600.0


def _numpy():
    import numpy

    return numpy


def _torch():
    import torch

    return torch


def project_cost(*, environment_episodes: int = 983_040,
                 optimizer_updates: int = 28_800, policies: int = 6) -> dict[str, Any]:
    """The carded prospective cost law, emitted without generating or learning."""
    scale = max(environment_episodes / 983_040, optimizer_updates / 28_800, policies / 6)
    seconds = round(ALLOWANCE * NEIGHBOUR_SECONDS * scale, 3)
    return {
        "object_id": OBJECT_ID,
        "command": "project-cost",
        "law": ("3 * 61.827 * max(environment_episodes / 983040, "
                "optimizer_updates / 28800, policies / 6)"),
        "inputs_per_arm": {
            "environment_episodes": environment_episodes,
            "optimizer_updates": optimizer_updates,
            "policies": policies,
        },
        "projected_arm_seconds": seconds,
        "machine_time_cap_seconds_per_arm": ARM_CAP_SECONDS,
        "within_cap": seconds <= ARM_CAP_SECONDS,
    }


def signed_witness_designs(beliefs, pairs: Iterable[tuple[int, int]] = WITNESS_PAIRS):
    """Return oracle-signed odd-support direction rows, one matrix per witness pair."""
    numpy = _numpy()
    star = numpy.asarray(BETA_STAR, dtype=numpy.float64)
    result = {}
    for first, second in pairs:
        if first not in K_TRAIN or second not in K_TRAIN:
            raise LaunchRefusal("every hinge witness must lie in K_train")
        raw = numpy.stack([
            numpy.asarray(tail_basis(belief=float(b), period=first), dtype=numpy.float64)
            - numpy.asarray(tail_basis(belief=float(b), period=second), dtype=numpy.float64)
            for b in beliefs
        ])
        oracle = raw @ star
        if numpy.any(oracle == 0.0):
            raise LaunchRefusal("an oracle witness gap is zero")
        result[(first, second)] = raw * numpy.sign(oracle)[:, None]
    return result


def _hinge_loss(beta, designs, arm_spec):
    torch = _torch()
    loss = beta.sum() * 0.0
    for pair, weight in arm_spec:
        signed_gap = (designs[pair] * beta).sum(dim=-1)
        loss = loss + weight * torch.clamp(MARGIN - signed_gap, min=0.0).mean()
    return loss


def _step(scorer, optimizer, x, z, targets, activity, hinge_designs, arm_spec):
    torch = _torch()
    optimizer.zero_grad(set_to_none=True)
    prediction = scorer(x, z)
    loss = torch.nn.functional.mse_loss(prediction, targets)
    loss = loss + _hinge_loss(scorer.beta, hinge_designs, arm_spec)
    if not torch.isfinite(loss).item():
        activity["nonfinite_events"] += 1
        raise ValueError("nonfinite tail loss")
    loss.backward()
    norm = float(torch.nn.utils.clip_grad_norm_(scorer.parameters(), 1.0).item())
    if not math.isfinite(norm):
        activity["nonfinite_events"] += 1
        raise ValueError("nonfinite tail gradient")
    activity["tail_gradient_norm_sum"] += norm
    activity["tail_gradient_norm_max"] = max(activity["tail_gradient_norm_max"], norm)
    activity["tail_clipping_events"] += int(norm > 1.0)
    optimizer.step()
    if any(p.dtype != torch.float32 or not torch.isfinite(p).all().item()
           for p in scorer.parameters()):
        activity["nonfinite_events"] += 1
        raise ValueError("nonfinite/non-FP32 tail parameter")


def train_tail(*, seed_id: str, fold_id: int, blocks, white, signed_designs,
               arm_spec, updates: int, activity):
    """The frozen whitened tail path with only its additive signed hinge changed."""
    numpy, torch = _numpy(), _torch()
    _root, model = build_arm(ARM_ID, seed_id, fold_id)
    initial = numpy.asarray(model.state_dict()["beta"].tolist(), dtype=numpy.float64)
    design = torch.tensor(
        (blocks["tail"]["design64"] @ white["_inverse"].T).astype(numpy.float32))
    transformed = {
        pair: torch.tensor((rows @ white["_inverse"].T).astype(numpy.float32))
        for pair, rows in signed_designs.items()
    }
    with torch.no_grad():
        model.beta.copy_(torch.tensor((white["_factor"].T @ initial).astype(numpy.float32)))
    optimizer = optimizer_for(model, LEARNING_RATE)
    count = design.shape[0]
    for update in range(updates):
        indices = torch.tensor(CR._cyclic_indices(count, update, BATCH_SIZE), dtype=torch.int64)
        batch_hinges = {pair: rows[indices] for pair, rows in transformed.items()}
        _step(model, optimizer, blocks["tail"]["x"][indices], design[indices],
              blocks["tail"]["y"][indices], activity, batch_hinges, arm_spec)
    final = numpy.asarray(model.state_dict()["beta"].tolist(), dtype=numpy.float64)
    recovered = numpy.linalg.solve(white["_factor"].T, final)
    return [float(v) for v in recovered], [float(v) for v in initial]


def train_root(*, seed_id: str, fold_id: int, blocks, targets, white,
               updates: int, activity):
    """The frozen whitened root path with a toy-size update seam for the smoke test."""
    numpy, torch = _numpy(), _torch()
    model, _tail = build_arm(ARM_ID, seed_id, fold_id)
    initial = numpy.asarray(model.state_dict()["beta"].tolist(), dtype=numpy.float64)
    design = torch.tensor(
        (blocks["root"]["design64"] @ white["_inverse"].T).astype(numpy.float32))
    with torch.no_grad():
        model.beta.copy_(torch.tensor((white["_factor"].T @ initial).astype(numpy.float32)))
    final = CR.train_stage(
        model, blocks["root"]["x"], design,
        torch.tensor(targets.astype(numpy.float32), dtype=torch.float32),
        updates=updates, activity=activity, prefix="root")
    recovered = numpy.linalg.solve(white["_factor"].T, numpy.asarray(final))
    return [float(v) for v in recovered], [float(v) for v in initial]


def witness_record(beta, signed_designs, arm_spec) -> dict[str, Any]:
    numpy = _numpy()
    vector = numpy.asarray(beta, dtype=numpy.float64)
    weights = dict(arm_spec)
    result = {}
    for pair in weights:
        gaps = signed_designs[pair] @ vector
        key = f"{pair[0]}_{pair[1]}"
        result[key] = {
            "pair": list(pair),
            "weight": weights[pair],
            "rows": int(gaps.size),
            "active_rows": int((gaps < MARGIN).sum()),
            "activation_fraction": float((gaps < MARGIN).mean()),
            "minimum_final_signed_margin": float(gaps.min()),
            "mean_final_signed_margin": float(gaps.mean()),
            "maximum_final_signed_margin": float(gaps.max()),
        }
    return result


def evaluation_gap_record(beta) -> list[dict[str, Any]]:
    """Signed learned and oracle gaps for all three held-out directions at all beliefs."""
    numpy = _numpy()
    vector = numpy.asarray(beta, dtype=numpy.float64)
    star = numpy.asarray(BETA_STAR, dtype=numpy.float64)
    rows = []
    for context in CONTEXTS:
        link, reliability, _cost = context
        for count in range(7):
            belief = posterior_short(link, reliability, count)
            for first, second in HELD_OUT_PAIRS:
                direction = (
                    numpy.asarray(tail_basis(belief=float(belief), period=first))
                    - numpy.asarray(tail_basis(belief=float(belief), period=second)))
                oracle_raw = float(direction @ star)
                sign = 1.0 if oracle_raw > 0.0 else -1.0
                rows.append({
                    "context_id": context_id(context), "count": count,
                    "belief": float(belief), "pair": [first, second],
                    "oracle_sign": int(sign),
                    "oracle_signed_gap": sign * oracle_raw,
                    "learned_signed_gap": sign * float(direction @ vector),
                })
    return rows


def _evaluate(seed, fold, beta_root, beta_tail, root_update, sampled_episodes):
    root, tail = CR._raw_modules(seed, fold, beta_root, beta_tail)
    item = evaluate_policy(root, tail, arm_id=ARM_ID, seed_id=seed, fold_id=fold,
                           root_update=root_update, sampled_episodes=sampled_episodes)
    breakdown, summary = RC.per_context_breakdown(root, tail)
    return item, breakdown, summary


def _policy_id(row: dict[str, Any]) -> str:
    return f"{row['seed_id']}|fold-{row['fold_id']}"


def apply_reading_rule(policies: list[dict[str, Any]]) -> dict[str, Any]:
    treatment, comparator = "THREE-WITNESS", "DOSE-MATCHED-SINGLE"
    passing = {
        arm: {_policy_id(row) for row in policies if row["arms"][arm]["agreement_within_gate"]}
        for arm in ARMS
    }
    nt, nc = len(passing[treatment]), len(passing[comparator])
    c_even = {
        arm: sum(row["arms"][arm]["competence"]["competence_pass"] for row in policies)
        for arm in ARMS
    }
    numbers = {
        "P_T": sorted(passing[treatment]), "P_C": sorted(passing[comparator]),
        "N_T": nt, "N_C": nc, "N_T_minus_N_C": nt - nc,
        "P_C_subseteq_P_T": passing[comparator] <= passing[treatment],
        "c_even_counts": c_even,
        "c_even_flags": {arm: [row["arms"][arm]["competence"]["competence_pass"]
                              for row in policies] for arm in ARMS},
        "agreement_flags": {arm: [row["arms"][arm]["agreement_within_gate"]
                                   for row in policies] for arm in ARMS},
        "agreement_gate": float(AGREEMENT_GATE),
    }
    if nt == 6 and nc < 6 and c_even[treatment] == 6:
        branch, label = "TW-A", "COVERAGE_CLOSES_COMPETENCE"
    elif nt == 6 and nc < 6 and c_even[treatment] < 6:
        branch, label = "TW-B", "COVERAGE_CLOSES_TAIL_ONLY"
    elif nt == 6 and nc == 6:
        branch, label = "TW-C", "DOSE_SUFFICIENT"
    elif nt > nc and nt < 6 and passing[comparator] <= passing[treatment]:
        branch, label = "TW-D", "COVERAGE_PARTIAL"
    elif passing[treatment] == passing[comparator] and nt < 6:
        branch, label = "TW-E", "NO_COVERAGE_GAIN"
    else:
        branch, label = "TW-F", "TRADEOFF_OR_UNCLEAR"
    return {"branch": branch, "label": label, "numbers": numbers}


def _peak_rss_bytes() -> int | None:
    """OS process peak working set; outcome-blind and read once after the work."""
    try:
        if sys.platform == "win32":
            class Counters(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
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


def _launch_sha() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()


def _read_admission(path: str | Path) -> dict[str, Any]:
    """Read the fresh central receipt supplied by launch orchestration."""
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if (value.get("passed") is not True or value.get("physical_floor_pass") is not True
            or value.get("effective_floor_pass") is not True):
        raise LaunchRefusal("the supplied central memory admission did not pass")
    return value


def run_object(output_root: str | Path, *, admission_receipt: str | Path,
               seeds: Sequence[str] = B1_SEEDS,
               folds: Sequence[int] = (0, 1), episodes_per_context: int = EPISODES_PER_CONTEXT,
               tail_updates: int = TAIL_UPDATES, root_updates: int = ROOT_UPDATES,
               sampled_episodes: int = SAMPLED_EVALUATION_EPISODES,
               thread_cap: int = 1, require_full_seeds: bool = True,
               argv: Sequence[str] | None = None) -> Path:
    """Run comparator then treatment on shared rows and write exactly one summary."""
    numpy = _numpy()
    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=True)
    admission = _read_admission(admission_receipt)
    if thread_cap != 1:
        raise LaunchRefusal("this object requires exactly one intra-op thread")
    if require_full_seeds and tuple(seeds) != tuple(B1_SEEDS):
        raise LaunchRefusal("production seed sequence must equal the frozen B1_SEEDS")
    CR._configure_topology(thread_cap)
    started = time.perf_counter()
    selection = CR._n_selection()
    old_offset = selection.OFFSET
    selection.OFFSET = OFFSET
    counts = {
        "environment_episodes": 0, "environment_transitions": 0,
        "tail_optimizer_updates": 0, "root_optimizer_updates": 0,
        "tail_example_exposures": 0, "root_example_exposures": 0,
        "exact_policy_evaluations": 0, "sampled_evaluation_episodes": 0,
        "sampled_evaluation_transitions": 0,
    }
    policies, exposure_rows = [], []
    arm_wall = {arm: 0.0 for arm in ARMS}
    generation_wall = 0.0
    try:
        for seed in seeds:
            generation_started = time.perf_counter()
            columns, _labels = CR.canonical_order(
                selection.generate_columns(seed, episodes_per_context))
            generation_wall += time.perf_counter() - generation_started
            counts["environment_episodes"] += int(columns["fold"].size)
            # The generator alternates equally between 8-transition PROBE episodes and
            # 2-transition IMMEDIATE episodes: (8 + 2) / 2 = 5 transitions per episode.
            counts["environment_transitions"] += 5 * int(columns["fold"].size)
            for fold in folds:
                blocks = CR.stage_designs(columns, fold)
                tail_white = CR.whitening(blocks["tail"]["design64"], stage="tail")
                root_white = CR.whitening(blocks["root"]["design64"], stage="root")
                beta_tail_star = CR.exact_solve(
                    blocks["tail"]["design64"], blocks["tail"]["targets64"])
                exact_targets = CR.root_targets_fp32(blocks["root"], beta_tail_star)
                beta_root_star = CR.exact_solve(blocks["root"]["design64"], exact_targets)
                signed = signed_witness_designs(blocks["tail"]["design64"][:, 1])
                policy = {"seed_id": seed, "fold_id": int(fold), "arms": {}}
                for arm, arm_spec in ARMS.items():
                    activity = CR._fresh_activity()
                    arm_started = time.perf_counter()
                    beta_tail, tail_initial = train_tail(
                        seed_id=seed, fold_id=fold, blocks=blocks, white=tail_white,
                        signed_designs=signed, arm_spec=arm_spec, updates=tail_updates,
                        activity=activity)
                    targets = CR.root_targets_fp32(blocks["root"], beta_tail)
                    beta_root_target = CR.exact_solve(blocks["root"]["design64"], targets)
                    beta_root, root_initial = train_root(
                        seed_id=seed, fold_id=fold, blocks=blocks, targets=targets,
                        white=root_white, updates=root_updates, activity=activity)
                    item, breakdown, evaluation = _evaluate(
                        seed, fold, beta_root, beta_tail, root_updates, sampled_episodes)
                    elapsed = time.perf_counter() - arm_started
                    arm_wall[arm] += elapsed
                    counts["tail_optimizer_updates"] += tail_updates
                    counts["root_optimizer_updates"] += root_updates
                    counts["tail_example_exposures"] += tail_updates * BATCH_SIZE
                    counts["root_example_exposures"] += root_updates * BATCH_SIZE
                    counts["exact_policy_evaluations"] += item.exact_policy_evaluations
                    counts["sampled_evaluation_episodes"] += item.sampled_evaluation_episodes
                    counts["sampled_evaluation_transitions"] += item.sampled_evaluation_transitions
                    tail_vector, root_vector = numpy.asarray(beta_tail), numpy.asarray(beta_root)
                    policy["arms"][arm] = {
                        "beta_tail": beta_tail, "beta_root": beta_root,
                        "initial_beta_tail": tail_initial, "initial_beta_root": root_initial,
                        "agreement_within_gate": bool(evaluation["min_tail_agreement_within_gate"]),
                        "competence": CR._competence_record(item),
                        "c_root": RC.c_root_pass(item, evaluation),
                        "per_context": breakdown, "per_context_summary": evaluation,
                        "evaluation_gaps": evaluation_gap_record(beta_tail),
                        "witnesses": witness_record(beta_tail, signed, arm_spec),
                        "training_mse": TM.value_bias(blocks, beta_tail, beta_tail_star),
                        "d_learned_tail": float(numpy.abs(tail_vector - beta_tail_star).max()),
                        "d_learned_root": float(numpy.abs(root_vector - beta_root_target).max()),
                        "d_objective": float(numpy.abs(
                            beta_tail_star - numpy.asarray(BETA_STAR)).max()),
                        "activity": activity, "wall_seconds": elapsed,
                    }
                    for stage, final, initial in (
                        ("tail", tail_vector, numpy.asarray(tail_initial)),
                        ("root", root_vector, numpy.asarray(root_initial)),
                    ):
                        displacement = float(numpy.linalg.norm(final - initial))
                        scale = float(numpy.linalg.norm(initial))
                        exposure_rows.append({
                            "arm": arm, "seed_id": seed, "fold_id": int(fold), "stage": stage,
                            "raw_coordinate_displacement_l2": displacement,
                            "initialisation_scale_l2": scale,
                            "displacement_to_initialisation_scale": displacement / scale,
                            "maximum_absolute_coordinate_move": float(
                                numpy.abs(final - initial).max()),
                        })
                exact_item, exact_breakdown, exact_evaluation = _evaluate(
                    seed, fold, beta_root_star, beta_tail_star, root_updates, sampled_episodes)
                counts["exact_policy_evaluations"] += exact_item.exact_policy_evaluations
                counts["sampled_evaluation_episodes"] += exact_item.sampled_evaluation_episodes
                counts["sampled_evaluation_transitions"] += exact_item.sampled_evaluation_transitions
                policy["exact_reference"] = {
                    "beta_tail": [float(v) for v in beta_tail_star],
                    "beta_root": [float(v) for v in beta_root_star],
                    "competence": CR._competence_record(exact_item),
                    "agreement_within_gate": bool(
                        exact_evaluation["min_tail_agreement_within_gate"]),
                    "c_root": RC.c_root_pass(exact_item, exact_evaluation),
                    "per_context": exact_breakdown, "per_context_summary": exact_evaluation,
                    "evaluation_gaps": evaluation_gap_record(beta_tail_star),
                    "note": "paired MSE exact solve on the same rows; reference, not an arm",
                }
                policies.append(policy)
    finally:
        selection.OFFSET = old_offset

    if any(value <= 0 for value in counts.values()):
        raise LaunchRefusal("required environment, update, or evaluation count is zero")
    if any(row["maximum_absolute_coordinate_move"] <= 0.0 for row in exposure_rows):
        raise LaunchRefusal("an optimized policy reports zero raw-coordinate movement")
    reading = apply_reading_rule(policies)
    measured_cost = {}
    policies_per_arm = len(policies)
    updates_per_arm = policies_per_arm * (tail_updates + root_updates)
    for arm in ARMS:
        charged_wall = generation_wall + arm_wall[arm]
        measured_cost[arm] = {
            "shared_generation_wall_seconds_charged_in_full": generation_wall,
            "arm_learning_and_evaluation_wall_seconds": arm_wall[arm],
            "charged_wall_seconds": charged_wall,
            "wall_seconds_per_policy": charged_wall / policies_per_arm,
            "wall_seconds_per_optimizer_update": charged_wall / updates_per_arm,
        }
    peak_rss = _peak_rss_bytes()
    summary = {
        "format": RESULT_FORMAT, "object_id": OBJECT_ID, "evidence_class": EVIDENCE_CLASS,
        "card": CARD, "complete": True, "launch_sha": _launch_sha(),
        "argv": list(sys.argv if argv is None else argv),
        "arm_order": list(ARMS),
        "arms": {arm: [{"pair": list(pair), "weight": weight}
                       for pair, weight in spec] for arm, spec in ARMS.items()},
        "paired_rows": {"offset": OFFSET, "episodes_per_context": episodes_per_context,
                        "training_support": list(K_TRAIN), "evaluation_support": list(K_EVAL)},
        "hyperparameters": {"margin": MARGIN, "learning_rate": LEARNING_RATE,
                            "batch_size": BATCH_SIZE, "tail_updates": tail_updates,
                            "root_updates": root_updates},
        "admission": admission, "counts": counts, "policies": policies,
        "reading_rule": reading,
        "exposure_line": {
            "statement": ("recovered raw-coordinate L2 displacement divided by the deterministic "
                          "initial raw-coordinate L2 scale, per arm, policy and stage"),
            "rows": exposure_rows,
        },
        "prospective_cost": project_cost(
            environment_episodes=len(seeds) * episodes_per_context * len(CONTEXTS),
            optimizer_updates=policies_per_arm * (tail_updates + root_updates),
            policies=policies_per_arm),
        "measured_cost": measured_cost,
        "resources": {"wall_seconds": time.perf_counter() - started,
                      "peak_rss_bytes": peak_rss,
                      "status": "measured" if peak_rss is not None else "resources_unmeasured"},
    }
    destination = output / "summary.json"
    destination.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return destination
