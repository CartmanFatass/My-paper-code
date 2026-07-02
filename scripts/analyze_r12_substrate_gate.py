from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ha_ctse_process.substrate_gate import (
    auc_binary,
    choose_cluster_count,
    deterministic_kmeans,
    discrete_membership_auc,
    dwell_lengths,
    dwell_pass,
    mutual_information_discrete,
    outcome_pass,
    parse_vector_field,
    role_label_validity,
    role_pass,
    transition_diag_mass,
)


def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        raise ValueError(f"missing required artifact: {path.name}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def _float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    raw = row.get(key, "")
    if raw == "":
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if np.isfinite(value) else default


def _int(row: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, default)))
    except (TypeError, ValueError):
        return default


def _block_shuffle(values: np.ndarray, *, block_size: int = 3, seed: int = 17) -> np.ndarray:
    values = np.asarray(values)
    if values.size == 0:
        return values.copy()
    block_size = max(int(block_size), 1)
    blocks = [values[start : start + block_size] for start in range(0, values.size, block_size)]
    order = np.arange(len(blocks))
    rng = np.random.default_rng(seed)
    rng.shuffle(order)
    return np.concatenate([blocks[int(idx)] for idx in order])


def _binary_target(step_rows: list[dict[str, str]], fields: list[str]) -> tuple[np.ndarray, str]:
    if "coverage_positive_step" in fields:
        values = [_int(row, "coverage_positive_step") for row in step_rows]
        return np.asarray(values, dtype=np.int64), "coverage_positive_step"
    if "zero_throughput_step" in fields:
        values = [1 - _int(row, "zero_throughput_step") for row in step_rows]
        return np.asarray(values, dtype=np.int64), "zero_throughput_step_inverted"
    if "throughput_gt5_step" in fields:
        values = [_int(row, "throughput_gt5_step") for row in step_rows]
        return np.asarray(values, dtype=np.int64), "throughput_gt5_step"
    return np.zeros(len(step_rows), dtype=np.int64), "missing"


def _target_stats(target: np.ndarray, target_field: str) -> dict:
    values = np.asarray(target, dtype=np.int64).reshape(-1)
    unique, counts = np.unique(values, return_counts=True) if values.size else ([], [])
    count_items = {
        str(int(label)): int(count) for label, count in zip(unique, counts)
    }
    fraction_items = {
        str(int(label)): float(count / values.size) if values.size else 0.0
        for label, count in zip(unique, counts)
    }
    valid_labels = set(count_items) <= {"0", "1"}
    target_valid = bool(
        target_field != "missing"
        and values.size > 0
        and valid_labels
        and count_items.get("0", 0) > 0
        and count_items.get("1", 0) > 0
    )
    return {
        "target_valid": target_valid,
        "target_class_counts": count_items,
        "target_class_fractions": fraction_items,
    }


def _outcome_report(
    target: np.ndarray,
    target_field: str,
    omega_score: np.ndarray,
    compact_score: np.ndarray,
) -> dict:
    target_report = _target_stats(target, target_field)
    if not bool(target_report["target_valid"]):
        report = {
            "pass": False,
            "auc": 0.5,
            "baseline_auc": 0.5,
            "margin": 0.0,
            "floor_ok": False,
            "margin_ok": False,
        }
    else:
        report = outcome_pass(
            auc=auc_binary(target, omega_score),
            baseline_auc=auc_binary(target, compact_score),
        )
    report.update(target_report)
    report["target_field"] = target_field
    report["baseline_field"] = "compact_norm"
    return report


def _available_role_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if _float(row, "role_available", 0.0) > 0.0]


def _step_key(row: dict[str, str]) -> tuple[str, int, int]:
    return (
        str(row.get("checkpoint", "")),
        _int(row, "episode"),
        _int(row, "step"),
    )


def _compact_matrix(step_rows: list[dict[str, str]]) -> tuple[np.ndarray, list[int]]:
    vectors: list[np.ndarray] = []
    indices: list[int] = []
    expected_dim: int | None = None
    for idx, row in enumerate(step_rows):
        vector = parse_vector_field(row.get("compact_json", ""))
        if vector.size == 0:
            continue
        if expected_dim is None:
            expected_dim = int(vector.size)
        if int(vector.size) != expected_dim:
            continue
        vectors.append(vector)
        indices.append(idx)
    if not vectors:
        return np.empty((0, 0), dtype=np.float64), []
    return np.vstack(vectors).astype(np.float64), indices


def _membership_gate_report(
    *,
    name: str,
    step_rows: list[dict[str, str]],
    step_fields: list[str],
    role_rows: list[dict[str, str]],
    memberships: np.ndarray,
    row_indices: list[int] | None = None,
    baseline_score: np.ndarray | None = None,
) -> dict:
    if row_indices is None:
        row_indices = list(range(len(step_rows)))
    selected_steps = [step_rows[idx] for idx in row_indices]
    selected_memberships = np.asarray(memberships, dtype=np.int64).reshape(-1)
    if len(selected_steps) != selected_memberships.size:
        raise ValueError(f"{name}: selected steps and memberships length mismatch")

    dwell = dwell_lengths(selected_memberships)
    transition_diag = transition_diag_mass(selected_memberships)
    null_transition_diag = transition_diag_mass(_block_shuffle(selected_memberships))
    dwell_report = dwell_pass(
        median_dwell=float(np.median(dwell)) if dwell.size else 0.0,
        transition_diag=transition_diag,
        null_transition_diag=null_transition_diag,
    )

    target, target_field = _binary_target(selected_steps, step_fields)
    target_report = _target_stats(target, target_field)
    membership_auc = discrete_membership_auc(target, selected_memberships)
    if baseline_score is None:
        baseline = np.asarray([_float(row, "compact_norm") for row in selected_steps], dtype=np.float64)
    else:
        baseline = np.asarray(baseline_score, dtype=np.float64).reshape(-1)
        if baseline.shape[0] != len(selected_steps):
            raise ValueError(f"{name}: baseline and selected steps length mismatch")
    if bool(target_report["target_valid"]) and bool(membership_auc["target_valid"]):
        outcome_report = outcome_pass(
            auc=float(membership_auc["auc"]),
            baseline_auc=auc_binary(target, baseline),
        )
    else:
        outcome_report = {
            "pass": False,
            "auc": 0.5,
            "baseline_auc": 0.5,
            "margin": 0.0,
            "floor_ok": False,
            "margin_ok": False,
        }
    outcome_report.update(target_report)
    outcome_report["target_field"] = target_field
    outcome_report["baseline_field"] = "compact_norm"
    outcome_report["best_label"] = int(membership_auc["best_label"])
    outcome_report["best_orientation"] = int(membership_auc["best_orientation"])

    key_to_membership = {
        _step_key(row): int(label)
        for row, label in zip(selected_steps, selected_memberships)
    }
    available_roles = [
        row
        for row in _available_role_rows(role_rows)
        if _step_key(row) in key_to_membership
    ]
    role_labels = np.asarray([_int(row, "role_label") for row in available_roles], dtype=np.int64)
    role_memberships = np.asarray(
        [key_to_membership[_step_key(row)] for row in available_roles],
        dtype=np.int64,
    )
    role_validity = role_label_validity(role_labels)
    role_validity["total_role_rows"] = len(role_rows)
    role_validity["available_role_rows"] = len(available_roles)

    mi = mutual_information_discrete(role_memberships, role_labels)
    rng = np.random.default_rng(23)
    perm_mi = []
    for _ in range(64):
        permuted = role_labels.copy()
        rng.shuffle(permuted)
        perm_mi.append(mutual_information_discrete(role_memberships, permuted))
    perm_mi_arr = np.asarray(perm_mi, dtype=np.float64)
    role_report = role_pass(
        role_valid=bool(role_validity["valid"]),
        mi=mi,
        perm_mean=float(np.mean(perm_mi_arr)) if perm_mi_arr.size else 0.0,
        perm_std=float(np.std(perm_mi_arr)) if perm_mi_arr.size else 0.0,
        stability=transition_diag,
        perm_stability=null_transition_diag,
    )

    return {
        "available": True,
        "n_steps": len(selected_steps),
        "n_unique_memberships": int(np.unique(selected_memberships).size),
        "g_dwell": dwell_report,
        "g_outcome": outcome_report,
        "g_role_validity": role_validity,
        "g_role": role_report,
        "gate_pass": bool(
            dwell_report["pass"] and outcome_report["pass"] and role_report["pass"]
        ),
    }


def analyze(dump_dir: Path, *, require_role_label_variance: bool) -> dict:
    step_rows, step_fields = _read_csv(dump_dir / "substrate_steps.csv")
    role_rows, _ = _read_csv(dump_dir / "substrate_roles.csv")

    omega_memberships = np.asarray([_int(row, "omega_argmax") for row in step_rows], dtype=np.int64)
    omega_report = _membership_gate_report(
        name="omega",
        step_rows=step_rows,
        step_fields=step_fields,
        role_rows=role_rows,
        memberships=omega_memberships,
    )
    if require_role_label_variance and not bool(omega_report["g_role_validity"]["valid"]):
        raise ValueError(f"invalid G-ROLE labels: {omega_report['g_role_validity']}")

    compact_values, compact_indices = _compact_matrix(step_rows)
    if compact_values.shape[0] >= 2:
        selected_omega = omega_memberships[np.asarray(compact_indices, dtype=np.int64)]
        compact_k = choose_cluster_count(
            n_rows=compact_values.shape[0],
            omega_labels=selected_omega,
        )
        compact_labels = deterministic_kmeans(compact_values, k=compact_k)
        compact_report = _membership_gate_report(
            name="compact_cluster",
            step_rows=step_rows,
            step_fields=step_fields,
            role_rows=role_rows,
            memberships=compact_labels,
            row_indices=compact_indices,
        )
    else:
        compact_report = {
            "available": False,
            "reason": "missing_or_insufficient_compact_json",
            "n_steps": int(compact_values.shape[0]),
            "gate_pass": False,
        }

    if bool(omega_report["gate_pass"]):
        fallback_decision = "omega_pass"
    elif bool(compact_report.get("gate_pass", False)):
        fallback_decision = "use_compact_cluster"
    elif bool(compact_report.get("available", False)):
        fallback_decision = "compact_cluster_failed_retrain_or_handcrafted_next"
    else:
        fallback_decision = "compact_unavailable_export_or_rerun_required"

    return {
        "dump_dir": str(dump_dir),
        "rows": {
            "steps": len(step_rows),
            "roles": len(role_rows),
            "roles_available": int(omega_report["g_role_validity"]["available_role_rows"]),
        },
        "g_dwell": omega_report["g_dwell"],
        "g_outcome": omega_report["g_outcome"],
        "g_role_validity": omega_report["g_role_validity"],
        "g_role": omega_report["g_role"],
        "gate_pass": bool(omega_report["gate_pass"]),
        "membership_reports": {
            "omega": omega_report,
            "compact_cluster": compact_report,
        },
        "compact_cluster": compact_report,
        "fallback_decision": fallback_decision,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R12 substrate-gate dump artifacts.")
    parser.add_argument("--dump_dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--require_role_label_variance", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        report = analyze(
            Path(args.dump_dir),
            require_role_label_variance=bool(args.require_role_label_variance),
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, allow_nan=False, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        "r12_substrate_gate "
        f"pass={int(report['gate_pass'])} "
        f"dwell={int(report['g_dwell']['pass'])} "
        f"outcome={int(report['g_outcome']['pass'])} "
        f"role={int(report['g_role']['pass'])} "
        f"output={output}"
    )


if __name__ == "__main__":
    main()
