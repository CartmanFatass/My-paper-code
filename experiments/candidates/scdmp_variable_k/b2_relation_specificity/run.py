from __future__ import annotations

import os

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
              "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

from .config import (
    ALGORITHM_SEEDS, ARMS, CANDIDATE, DHOM_FORWARD_TOTAL, FACTOR_TRANSITIONS_PER_PANEL_KIND,
    MICROSTEP_LEDGER, MICROSTEP_TOTAL, MODEL_PARAMETER_COUNT, NUMPY_VERSION,
    OPTIMIZER_UPDATES, ORDERED_PARAMETER_NAMES, PHYSICAL_FULL_JOINT_TOTAL,
    RESOURCES, REVISION, SCORED_REGIMES, TORCH_VERSION, TRAINING_FORWARD_TOTAL,
)


def _atomic_replace(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + f".{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def _write_fresh(path: Path, value: object) -> None:
    resolved = path.resolve()
    if resolved.exists():
        raise FileExistsError(f"refusing to overwrite B2 result: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(resolved) + f".{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())
    os.rename(temporary, resolved)


def static_conformance() -> dict[str, object]:
    checks = {
        "revision_exact": REVISION == "SCDMP-B2-SCIENCE-20260813-02",
        "arms_exact": ARMS == ("FREE-DIRECT", "SCDMP-CORRECT", "SCDMP-ORDER-SHUFFLE"),
        "fresh_seeds_exact": ALGORITHM_SEEDS == tuple(range(100, 108)),
        "ordered_parameters_exact_24": len(ORDERED_PARAMETER_NAMES) == 24 and len(set(ORDERED_PARAMETER_NAMES)) == 24,
        "ledger_exact": MICROSTEP_LEDGER == {"common_training_corpus": 98_304,
            "three_arm_scored": 1_105_920, "common_audit_warmup": 24_576,
            "audit_target_words": 373_248, "audit_reverse_twins": 373_248},
        "ledger_total_exact": sum(MICROSTEP_LEDGER.values()) == MICROSTEP_TOTAL == 1_975_296,
        "training_forwards_exact": TRAINING_FORWARD_TOTAL == 216_024,
        "dhom_forwards_exact": DHOM_FORWARD_TOTAL == 144,
        "resource_envelope_exact": RESOURCES.cpu_workers == 1 and not RESOURCES.gpu_allowed
            and RESOURCES.wall_seconds == 5_400 and RESOURCES.rss_bytes == 2 * 1024**3,
    }
    return {"checks": checks, "conforming": all(checks.values()),
            "science_card": "docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_B2_RELATION_SPECIFICITY_SCIENCE_CARD.md",
            "owner_intake": "docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_B2_V2_CHATGPT_PRO_CLOSED_OWNER_INTAKE.md",
            "production_command_module": "experiments.candidates.scdmp_variable_k.b2_relation_specificity"}


def prepare_static() -> dict[str, object]:
    return {"artifact_kind": "SCDMP_B2_V2_STATIC", "candidate": CANDIDATE, "revision": REVISION,
            "scientific_activity_started": False, "static_conformance": static_conformance(),
            "registered_resources": {"cpu": 1, "gpu": False, "wall_seconds": 5400,
                                     "rss_bytes": 2 * 1024**3}}


def production(output: Path) -> dict[str, object]:
    import numpy as np
    import torch

    from ..rng import require_numpy_version
    from .audit import analyze_audit
    from .corpus import build_corpus, structural_certificate
    from .evaluation import evaluate_scored, serialize_scored
    from .inference import complete_inference
    from .lifecycle import Lifecycle
    from .relations import homogeneous_relation_certificate
    from .resources import ResourceMonitor
    from .result import complete, incomplete
    from .training import checkpoint, train_support_competence, train_three_arms

    output = output.resolve()
    sidecar = Path(str(output) + ".activity.json")
    if output.exists() or sidecar.exists():
        raise FileExistsError("B2 result and activity sidecar targets must both be fresh")
    static = static_conformance()
    partial: dict[str, object] = {"completed_seeds": []}
    lifecycle: Lifecycle
    def persist(facts: dict[str, object]) -> None:
        if facts["scientific_activity_started"]:
            _atomic_replace(sidecar, {"artifact_kind": "SCDMP_B2_V2_ACTIVITY_SIDECAR",
                "candidate": CANDIDATE, "revision": REVISION, "result_path": str(output),
                "lifecycle": facts})
    lifecycle = Lifecycle(persist=persist)
    monitor: ResourceMonitor | None = None
    try:
        if not static["conforming"]:
            raise RuntimeError("B2 static conformance failed")
        require_numpy_version()
        if np.__version__ != NUMPY_VERSION or torch.__version__ != TORCH_VERSION:
            raise RuntimeError(f"version mismatch numpy={np.__version__}, torch={torch.__version__}")
        torch.set_num_threads(1); torch.set_num_interop_threads(1)
        torch.use_deterministic_algorithms(True)
        if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
            raise RuntimeError("B2 one-thread binding failed")
        monitor = ResourceMonitor(); monitor.check()
        seed_packets: list[dict[str, object]] = []
        ledger = {name: 0 for name in MICROSTEP_LEDGER}
        for seed in ALGORITHM_SEEDS:
            corpus = build_corpus(seed)
            structural = structural_certificate(corpus)
            relation = homogeneous_relation_certificate(
                [r for bank in ("C_22", "C_44") for r in corpus.banks[bank]])
            if not structural["conforming"] or not relation["conforming"]:
                raise RuntimeError(f"seed={seed} preactivity structural conformance failed")
            ledger["common_training_corpus"] += corpus.microsteps
            models, training = train_three_arms(corpus, seed, lifecycle, monitor.check)
            train_support = {arm: train_support_competence(models[arm], corpus) for arm in ARMS}
            audit, audit_ledger = analyze_audit(seed, models, corpus, monitor.check)
            for name, count in audit_ledger.items(): ledger[name] += count
            scored, scored_steps = evaluate_scored(seed, models, monitor.check)
            ledger["three_arm_scored"] += scored_steps
            packet = {"algorithm_seed": seed, "scalers": corpus.scales.as_dict(),
                "fit_target_means": {k: float(v) for k, v in corpus.means.items()},
                "structural_certificate": structural, "homogeneous_relation_certificate": relation,
                "training": training, "train_support": train_support, "audit": audit,
                "scored_episodes": serialize_scored(scored),
                "checkpoints": {arm: checkpoint(models[arm]) for arm in ARMS}}
            seed_packets.append(packet)
            partial["completed_seeds"] = [p["algorithm_seed"] for p in seed_packets]
        if ledger != MICROSTEP_LEDGER or sum(ledger.values()) != MICROSTEP_TOTAL:
            raise RuntimeError(f"B2 analytic ledger mismatch: {ledger}")
        if len(seed_packets) != 8 or sum(len(p["scored_episodes"]) for p in seed_packets) != 4_608:
            raise RuntimeError("B2 retained panel denominator mismatch")
        inference = complete_inference(seed_packets)
        resources = monitor.facts()
        resources.update({"numpy_version": np.__version__, "torch_version": torch.__version__,
            "parameter_count_per_arm": MODEL_PARAMETER_COUNT, "arms": 3,
            "updates_per_arm_seed": OPTIMIZER_UPDATES, "training_forwards": TRAINING_FORWARD_TOTAL,
            "dhom_forwards": DHOM_FORWARD_TOTAL, "physical_full_joint_steps": PHYSICAL_FULL_JOINT_TOTAL,
            "target_scalar_agent_factor_transitions": FACTOR_TRANSITIONS_PER_PANEL_KIND,
            "reverse_scalar_agent_factor_transitions": FACTOR_TRANSITIONS_PER_PANEL_KIND})
        lifecycle.complete()
        return complete(lifecycle, static, seed_packets, inference, resources, ledger, str(sidecar))
    except Exception as exc:
        lifecycle.abort(str(exc))
        partial["traceback"] = traceback.format_exc()
        return incomplete(lifecycle, str(exc), partial, static,
                          monitor.snapshot() if monitor is not None else None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Exact SCDMP-B2 revision-02 runner")
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.production and args.output is None:
        parser.error("--production requires --output")
    result = production(args.output) if args.production else prepare_static()  # type: ignore[arg-type]
    if args.output is not None:
        _write_fresh(args.output, result)
        if args.production and result["question_relevant_output_exists"]:
            sidecar = Path(str(args.output.resolve()) + ".activity.json")
            _atomic_replace(sidecar, {"artifact_kind": "SCDMP_B2_V2_ACTIVITY_SIDECAR",
                "candidate": CANDIDATE, "revision": REVISION, "result_path": str(args.output.resolve()),
                "final_result_installed": True, "lifecycle": result["lifecycle"]})
    print(json.dumps({"candidate": CANDIDATE, "revision": REVISION,
        "complete": result.get("complete"), "scientific_activity_started": result.get("scientific_activity_started"),
        "question_relevant_output_exists": result.get("question_relevant_output_exists"),
        "output": str(args.output.resolve()) if args.output else None}, sort_keys=True))
    return 0 if not args.production else (0 if result["question_relevant_output_exists"] else 2)


if __name__ == "__main__":
    raise SystemExit(main())
