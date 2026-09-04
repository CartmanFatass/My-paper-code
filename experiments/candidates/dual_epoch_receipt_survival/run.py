"""One full registered train -> final-checkpoint evaluate -> analyze DEARS-B1 flow."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from typing import Any

import torch

from .analysis import analyze_registered, summarize_arm
from .domain import BASE_SEEDS, EXAMPLE_COUNTS, LEARNED_ARMS, RULE_DUAL
from .generator import generate_examples, panel_contract
from .learner import (
    BATCH_SIZE, EPOCHS, GRAD_CLIP, HIDDEN_SIZE, OPTIMIZER, new_model,
    parameter_count, predict_probabilities, train_arm,
)
from .schema import MASK_CONTRACT, TOKEN_SCHEMA, audit_information_partitions
from .verifier import rule_dual, verify_example


ASSIGNMENT_ID = "DEARS-B1-DUAL-VERIFIER-v1"
CANDIDATE = "CAND-DUAL-EPOCH-AUTHENTICATED-RECEIPT-SURVIVAL"
CAPS = {
    "cpu_workers": 1,
    "learned_example_passes": 12_000_000,
    "wall_seconds": 3_600,
    "peak_rss_bytes": 2 * 1024**3,
}
DECLARED_COUNTS = {
    "base_seeds": 10, "learned_arms": 6,
    "superblocks_per_seed": {"train": 576, "validation": 192, "test": 576},
    "examples_per_arm_seed": dict(EXAMPLE_COUNTS),
    "training_epochs": 20,
    "training_example_passes": 11_059_200,
    "validation_plus_test_example_passes": 737_280,
    "total_learned_example_passes": 11_796_480,
    "final_checkpoints": 60,
}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
    os.replace(temporary, path)


class CapMonitor:
    def __init__(self) -> None:
        self.started = time.perf_counter()
        self.peak_rss = 0

    def check(self) -> None:
        elapsed = time.perf_counter() - self.started
        self.peak_rss = max(self.peak_rss, _rss_bytes())
        if elapsed > CAPS["wall_seconds"]:
            raise RuntimeError("registered wall-time cap breached")
        if self.peak_rss > CAPS["peak_rss_bytes"]:
            raise RuntimeError("registered peak-RSS cap breached")

    def usage(self) -> dict[str, object]:
        self.check()
        return {"wall_seconds": time.perf_counter() - self.started, "peak_rss_bytes": self.peak_rss,
                "cpu_workers": torch.get_num_threads()}


def _rss_bytes() -> int:
    """Current process working set without an optional runtime dependency."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        get_current_process = kernel32.GetCurrentProcess
        get_current_process.argtypes = []
        get_current_process.restype = wintypes.HANDLE
        get_process_memory_info = psapi.GetProcessMemoryInfo
        get_process_memory_info.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD,
        ]
        get_process_memory_info.restype = wintypes.BOOL
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        handle = get_current_process()
        if not handle:
            error = ctypes.get_last_error()
            raise OSError(error, "GetCurrentProcess failed")
        if not get_process_memory_info(handle, ctypes.byref(counters), counters.cb):
            error = ctypes.get_last_error()
            raise OSError(error, "GetProcessMemoryInfo failed")
        working_set = int(counters.WorkingSetSize)
        if working_set <= 0:
            raise OSError("GetProcessMemoryInfo returned a nonpositive working set")
        return working_set
    import resource
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if value > 10**8 else value * 1024


def _rule_probabilities(examples: list[object]) -> torch.Tensor:
    result = torch.zeros((len(examples), 3), dtype=torch.float32)
    for index, example in enumerate(examples):
        action = rule_dual(verify_example(example))
        if int(action) != int(example.correct_action):  # type: ignore[attr-defined]
            raise RuntimeError("RULE-DUAL disagrees with a generated unique label")
        result[index, int(action)] = 1.0
    return result


def _preflight() -> dict[str, object]:
    if parameter_count() != 34_995:
        raise RuntimeError(f"capacity drift: {parameter_count()}")
    contracts = {str(seed): panel_contract(seed) for seed in BASE_SEEDS}
    if any(any(value for value in row["split_overlap_counts"].values()) for row in contracts.values()):
        raise RuntimeError("opaque split overlap")
    if DECLARED_COUNTS["total_learned_example_passes"] > CAPS["learned_example_passes"]:
        raise RuntimeError("declared learned-pass cap breach")
    # These ordinary generator/verifier/masking checks all finish before the
    # first optimizer step; their output is engineering provenance, not activity.
    for seed in BASE_SEEDS:
        audits = {}
        for split in ("train", "validation", "test"):
            examples = generate_examples(seed, split)
            _rule_probabilities(examples)
            audits[split] = audit_information_partitions(examples)
        contracts[str(seed)]["information_partition_audits"] = audits
    return contracts


def exercise(*, output_root: Path, result_path: Path) -> dict[str, object]:
    if output_root.exists():
        raise FileExistsError("registered exercise requires a fresh output root")
    if result_path.exists():
        raise FileExistsError("registered result path already exists")
    output_root.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    monitor = CapMonitor()
    split_contracts = _preflight()
    manifest = {
        "artifact_kind": "DEARS_B1_REGISTERED_MANIFEST", "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE, "base_seeds": list(BASE_SEEDS),
        "learned_arms": list(LEARNED_ARMS), "fixed_reference": RULE_DUAL,
        "declared_counts": DECLARED_COUNTS, "caps": CAPS,
        "model": {"input_size": 192, "hidden_size": HIDDEN_SIZE, "layers": 1,
                  "head": "48->3 affine", "parameters": parameter_count(), "dropout": 0.0,
                  "attention": False, "initial_state": "zeros"},
        "training": {"loss": "multiclass_cross_entropy", "optimizer": OPTIMIZER,
                     "batch_size": BATCH_SIZE, "gradient_norm_clip": GRAD_CLIP,
                     "epochs": EPOCHS, "checkpoint_selection": "final epoch 20 only",
                     "evaluation_softmax_temperature": 1.0},
        "token_schema": TOKEN_SCHEMA, "mask_transforms": MASK_CONTRACT,
        "split_contracts_by_seed": split_contracts,
        "single_registered_action": "exercise",
    }
    _write_json(output_root / "manifest.json", manifest)

    seed_rows: list[dict[str, Any]] = []
    total_training_passes = 0
    total_reporting_passes = 0
    activity: dict[str, object] | None = None
    for base_seed in BASE_SEEDS:
        train = generate_examples(base_seed, "train")
        validation = generate_examples(base_seed, "validation")
        test = generate_examples(base_seed, "test")
        # Every generated label is independently checked against the fail-closed decoder.
        _rule_probabilities(train)
        _rule_probabilities(validation)
        rule_test = _rule_probabilities(test)
        row: dict[str, Any] = {"base_seed": base_seed, "training": {}, "validation": {}, "test": {}}
        test_probabilities: dict[str, torch.Tensor] = {}
        for arm in LEARNED_ARMS:
            model = new_model(base_seed)
            report = train_arm(model, train, arm, base_seed, cap_check=monitor.check)
            total_training_passes += report.example_passes
            checkpoint = output_root / "checkpoints" / f"seed_{base_seed}" / f"{arm}.pt"
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            torch.save({"arm": arm, "base_seed": base_seed, "epoch": EPOCHS,
                        "final_checkpoint_only": True, "model_state": model.state_dict()}, checkpoint)
            validation_probs = predict_probabilities(model, validation, arm)
            test_probs = predict_probabilities(model, test, arm)
            total_reporting_passes += len(validation) + len(test)
            row["training"][arm] = report.__dict__
            row["validation"][arm] = summarize_arm(validation, validation_probs)
            row["test"][arm] = summarize_arm(test, test_probs)
            test_probabilities[arm] = test_probs
            monitor.check()
        row["test"][RULE_DUAL] = summarize_arm(test, rule_test)
        if float(row["test"][RULE_DUAL]["W"]) != 1.0:
            raise RuntimeError("RULE-DUAL worst-cell correctness is not one")
        if activity is None:
            first = [index for index, example in enumerate(test) if example.superblock == 0]
            if len(first) != 16:
                raise RuntimeError("first held-out superblock is incomplete")
            activity = {
                "criterion": "all six final checkpoints evaluated the same first complete held-out superblock",
                "reached": True, "base_seed": base_seed, "superblock": 0,
                "paired_examples": [
                    {
                        "core_index": test[index].core_index,
                        "correct_action": test[index].correct_action.name,
                        "refined_cell": test[index].refined_cell,
                        "authentication": test[index].authentication,
                        "authentication_detail": test[index].authentication_detail,
                        "owner_survives": test[index].owner_survives,
                        "owner_detail": test[index].owner_detail,
                        "lease_survives": test[index].lease_survives,
                        "lease_detail": test[index].lease_detail,
                        "split_membership": test[index].split,
                        "opaque_values_disjoint_from_train_validation": True,
                        "action_probabilities_by_arm": {
                            arm: test_probabilities[arm][index].tolist() for arm in LEARNED_ARMS
                        },
                    } for index in first
                ],
            }
            _write_json(output_root / "activity_start.json", activity)
        seed_rows.append(row)
        _write_json(output_root / "seed_results" / f"seed_{base_seed}.json", row)
        monitor.check()

    if activity is None:
        raise RuntimeError("scientific activity-start criterion was not reached")
    if total_training_passes != DECLARED_COUNTS["training_example_passes"]:
        raise RuntimeError("actual training-pass count drift")
    if total_reporting_passes != DECLARED_COUNTS["validation_plus_test_example_passes"]:
        raise RuntimeError("actual reporting-pass count drift")
    analysis = analyze_registered(seed_rows)
    anomalies = []
    if any(analysis["information_ceiling_violation_seed_indices"].values()):
        anomalies.append("information_ceiling_violation")
    result = {
        "artifact_kind": "DEARS_B1_REGISTERED_RESULT", "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE, "scientific_activity": activity,
        "scientific_activity_criterion_reached": True,
        "token_schema": TOKEN_SCHEMA, "mask_transforms_by_arm": MASK_CONTRACT,
        "matched_superblock_contract": {"variants": 16, "paired_across_arms": True,
            "same_examples_and_label_order": True, "science_fields_only_vary_within_variants": True},
        "declared_counts": DECLARED_COUNTS,
        "actual_counts": {"training_example_passes": total_training_passes,
                          "validation_plus_test_example_passes": total_reporting_passes,
                          "total_learned_example_passes": total_training_passes + total_reporting_passes,
                          "final_checkpoints": len(BASE_SEEDS) * len(LEARNED_ARMS),
                          "base_seeds": len(BASE_SEEDS), "learned_arms": len(LEARNED_ARMS),
                          "superblocks_per_arm_seed": {"train": 576, "validation": 192, "test": 576},
                          "examples_per_arm_seed": dict(EXAMPLE_COUNTS)},
        "caps": CAPS, "actual_resource_usage": monitor.usage(),
        "split_domain_checks_by_seed": split_contracts,
        "per_seed": seed_rows, "analysis": analysis, "material_anomalies": anomalies,
        "claim_ceiling": (
            "Constructed one-receipt, two-edge-per-lineage, one-decision binary-content host; trusted updates; "
            "host-oracle authentication; named forgeries; fixed supervised GRU, exact finite panel and held-out domains only."
        ),
    }
    _write_json(output_root / "raw_result.json", result)
    _write_json(result_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    registered = subparsers.add_parser("exercise", help="run the sole full registered DEARS-B1 flow")
    registered.add_argument("--output-root", required=True, type=Path)
    registered.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    value = exercise(output_root=args.output_root.resolve(), result_path=args.result.resolve())
    print(json.dumps({"result": str(args.result.resolve()),
                      "activity_reached": value["scientific_activity_criterion_reached"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
