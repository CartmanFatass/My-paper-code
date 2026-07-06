# R12 Substrate Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a diagnostic-only Round 12 substrate gate that proves whether OPT `omega_t / c_t` is a valid interaction-situation substrate before any new HA-CTSE reward, hazard, SEF/DADS, target-situation, or co-edit mechanism is implemented.

**Architecture:** Add a small pure-analysis module for pre-registered gate math, a checkpoint-grid exporter that replays stored HA-CTSE checkpoints and dumps `omega/c/role/mode` rows, and offline scripts that compute CSV triage plus G-DWELL/G-OUTCOME/G-ROLE. The exporter must force diagnostic topology-role counterfactual computation directly through `TopologyRoleExtractor`; it must not rely on `use_topology_role_probe` being enabled in training.

**Tech Stack:** Python 3.10, PyTorch, NumPy, existing `ha_ctse_process.train` / `eval_checkpoints` utilities, CSV/JSON artifacts, pytest.

---

## File Structure

- Create `ha_ctse_process/substrate_gate.py`
  - Pure functions and dataclasses for dwell statistics, AUC, role-label validity, permutation/null baselines, and final gate decision.
  - No environment, no PyTorch model loading, no reward logic.

- Create `ha_ctse_process/export_substrate_gate.py`
  - CLI module runnable with `python -m ha_ctse_process.export_substrate_gate`.
  - Loads a checkpoint grid, replays deterministic eval episodes, computes OPT compact context and aggregation weights, and writes dump CSVs.
  - Directly instantiates `TopologyRoleExtractor` to force diagnostic counterfactual role labels.

- Create `scripts/analyze_r12_csv_triage.py`
  - Reads existing `metrics/train_updates.csv` files and reports OPT collapse/uniformity indicators before new export work.

- Create `scripts/analyze_r12_substrate_gate.py`
  - Reads exporter artifacts and computes G-DWELL/G-OUTCOME/G-ROLE using `ha_ctse_process.substrate_gate`.

- Create `scripts/run_r12_substrate_gate_local.ps1`
  - One-key local Windows runner for smoke export + analyzer over a chosen checkpoint directory.

- Create `tests/test_r12_substrate_gate.py`
  - Unit tests for the silent-error cases and threshold logic.

- Modify `memory/ExpRecord.md`
  - Fill concrete commands under `EXP-20260702-substrate-gate` after scripts exist.

- Modify `memory/ATTENTION_POINTER.md`
  - Point active next action to the exact runner/analyzer once implemented.

---

### Task 1: Pure Gate Math

**Files:**
- Create: `ha_ctse_process/substrate_gate.py`
- Test: `tests/test_r12_substrate_gate.py`

- [ ] **Step 1: Write failing tests for the gate rules**

Create `tests/test_r12_substrate_gate.py` with:

```python
import numpy as np

from ha_ctse_process.substrate_gate import (
    auc_binary,
    dwell_lengths,
    dwell_pass,
    outcome_pass,
    role_label_validity,
    role_pass,
    transition_diag_mass,
)


def test_role_validity_rejects_all_zero_labels():
    labels = np.zeros(32, dtype=np.int64)
    report = role_label_validity(labels)
    assert report["valid"] is False
    assert report["variance"] == 0.0
    assert report["max_label_fraction"] == 1.0


def test_role_validity_accepts_non_degenerate_labels():
    labels = np.asarray([0, 1, 1, 2, 2, 3, 3, 3], dtype=np.int64)
    report = role_label_validity(labels)
    assert report["valid"] is True
    assert report["variance"] > 0.0
    assert report["max_label_fraction"] < 0.95


def test_dwell_pass_requires_three_intervals_and_diag_margin():
    memberships = np.asarray([1, 1, 1, 2, 2, 2, 2, 1, 1, 1], dtype=np.int64)
    lengths = dwell_lengths(memberships)
    assert np.median(lengths) == 3.0
    assert transition_diag_mass(memberships) > 0.5
    assert dwell_pass(
        median_dwell=3.0,
        transition_diag=0.72,
        null_transition_diag=0.40,
    )["pass"] is True
    assert dwell_pass(
        median_dwell=2.0,
        transition_diag=0.90,
        null_transition_diag=0.40,
    )["pass"] is False
    assert dwell_pass(
        median_dwell=3.0,
        transition_diag=0.55,
        null_transition_diag=0.40,
    )["pass"] is False


def test_outcome_auc_gate_requires_baseline_margin():
    assert outcome_pass(auc=0.66, baseline_auc=0.59)["pass"] is True
    assert outcome_pass(auc=0.62, baseline_auc=0.60)["pass"] is False
    assert outcome_pass(auc=0.58, baseline_auc=0.40)["pass"] is False


def test_auc_binary_handles_ties_and_direction():
    y_true = np.asarray([0, 0, 1, 1], dtype=np.int64)
    scores = np.asarray([0.1, 0.2, 0.8, 0.9], dtype=np.float64)
    assert auc_binary(y_true, scores) == 1.0
    tied = np.asarray([0.5, 0.5, 0.5, 0.5], dtype=np.float64)
    assert auc_binary(y_true, tied) == 0.5


def test_role_pass_uses_permutation_margin_and_validity():
    invalid = role_pass(
        role_valid=False,
        mi=1.0,
        perm_mean=0.0,
        perm_std=0.0,
        stability=1.0,
        perm_stability=0.0,
    )
    assert invalid["pass"] is False
    valid = role_pass(
        role_valid=True,
        mi=0.16,
        perm_mean=0.05,
        perm_std=0.02,
        stability=0.45,
        perm_stability=0.30,
    )
    assert valid["pass"] is True
```

- [ ] **Step 2: Run tests and verify they fail because the module does not exist**

Run:

```powershell
python -m pytest tests\test_r12_substrate_gate.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'ha_ctse_process.substrate_gate'
```

- [ ] **Step 3: Implement the pure gate module**

Create `ha_ctse_process/substrate_gate.py`:

```python
"""Round-12 OPT substrate-gate analysis utilities.

This module is intentionally pure: no env stepping, no model loading, no reward
injection.  It exists so the R12 substrate decision can be tested without
changing HA-CTSE training behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class SubstrateThresholds:
    dwell_min_intervals: float = 3.0
    dwell_diag_margin: float = 0.20
    outcome_auc_floor: float = 0.60
    outcome_auc_margin: float = 0.05
    role_max_label_fraction: float = 0.95
    role_mi_std_margin: float = 2.0
    role_stability_margin: float = 0.10


def _finite_array(values: Iterable[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=np.float64)
    arr = arr.reshape(-1)
    return arr[np.isfinite(arr)]


def dwell_lengths(memberships: Iterable[int] | np.ndarray) -> np.ndarray:
    values = np.asarray(memberships, dtype=np.int64).reshape(-1)
    if values.size == 0:
        return np.zeros(0, dtype=np.float64)
    lengths: list[int] = []
    current = int(values[0])
    run = 1
    for item in values[1:]:
        item = int(item)
        if item == current:
            run += 1
        else:
            lengths.append(run)
            current = item
            run = 1
    lengths.append(run)
    return np.asarray(lengths, dtype=np.float64)


def transition_diag_mass(memberships: Iterable[int] | np.ndarray) -> float:
    values = np.asarray(memberships, dtype=np.int64).reshape(-1)
    if values.size <= 1:
        return 0.0
    return float(np.mean(values[1:] == values[:-1]))


def dwell_pass(
    median_dwell: float,
    transition_diag: float,
    null_transition_diag: float,
    thresholds: SubstrateThresholds | None = None,
) -> dict[str, float | bool]:
    thresholds = thresholds or SubstrateThresholds()
    diag_margin = float(transition_diag - null_transition_diag)
    passed = (
        float(median_dwell) >= thresholds.dwell_min_intervals
        and diag_margin >= thresholds.dwell_diag_margin
    )
    return {
        "pass": bool(passed),
        "median_dwell": float(median_dwell),
        "transition_diag": float(transition_diag),
        "null_transition_diag": float(null_transition_diag),
        "diag_margin": diag_margin,
    }


def auc_binary(y_true: Iterable[int] | np.ndarray, scores: Iterable[float] | np.ndarray) -> float:
    y = np.asarray(y_true, dtype=np.int64).reshape(-1)
    s = np.asarray(scores, dtype=np.float64).reshape(-1)
    mask = np.isfinite(s)
    y = y[mask]
    s = s[mask]
    if y.size == 0 or np.unique(y).size < 2:
        return 0.5
    pos = s[y > 0]
    neg = s[y <= 0]
    if pos.size == 0 or neg.size == 0:
        return 0.5
    wins = 0.0
    total = float(pos.size * neg.size)
    for value in pos:
        wins += float(np.sum(value > neg))
        wins += 0.5 * float(np.sum(value == neg))
    return float(wins / total)


def outcome_pass(
    auc: float,
    baseline_auc: float,
    thresholds: SubstrateThresholds | None = None,
) -> dict[str, float | bool]:
    thresholds = thresholds or SubstrateThresholds()
    required = max(thresholds.outcome_auc_floor, float(baseline_auc) + thresholds.outcome_auc_margin)
    passed = float(auc) >= required
    return {
        "pass": bool(passed),
        "auc": float(auc),
        "baseline_auc": float(baseline_auc),
        "required_auc": float(required),
        "auc_margin": float(auc - baseline_auc),
    }


def role_label_validity(
    labels: Iterable[int] | np.ndarray,
    thresholds: SubstrateThresholds | None = None,
) -> dict[str, float | bool]:
    thresholds = thresholds or SubstrateThresholds()
    arr = np.asarray(labels, dtype=np.int64).reshape(-1)
    if arr.size == 0:
        return {
            "valid": False,
            "variance": 0.0,
            "max_label_fraction": 1.0,
            "n": 0.0,
        }
    variance = float(np.var(arr.astype(np.float64)))
    _, counts = np.unique(arr, return_counts=True)
    max_fraction = float(np.max(counts) / arr.size)
    return {
        "valid": bool(variance > 0.0 and max_fraction < thresholds.role_max_label_fraction),
        "variance": variance,
        "max_label_fraction": max_fraction,
        "n": float(arr.size),
    }


def mutual_information_discrete(x: Iterable[int] | np.ndarray, y: Iterable[int] | np.ndarray) -> float:
    x_arr = np.asarray(x, dtype=np.int64).reshape(-1)
    y_arr = np.asarray(y, dtype=np.int64).reshape(-1)
    n = min(x_arr.size, y_arr.size)
    if n == 0:
        return 0.0
    x_arr = x_arr[:n]
    y_arr = y_arr[:n]
    x_values, x_inv = np.unique(x_arr, return_inverse=True)
    y_values, y_inv = np.unique(y_arr, return_inverse=True)
    joint = np.zeros((x_values.size, y_values.size), dtype=np.float64)
    for xi, yi in zip(x_inv, y_inv):
        joint[int(xi), int(yi)] += 1.0
    joint /= max(float(n), 1.0)
    px = joint.sum(axis=1, keepdims=True)
    py = joint.sum(axis=0, keepdims=True)
    expected = px @ py
    mask = joint > 0.0
    return float(np.sum(joint[mask] * np.log(joint[mask] / expected[mask])))


def role_pass(
    role_valid: bool,
    mi: float,
    perm_mean: float,
    perm_std: float,
    stability: float,
    perm_stability: float,
    thresholds: SubstrateThresholds | None = None,
) -> dict[str, float | bool]:
    thresholds = thresholds or SubstrateThresholds()
    mi_required = float(perm_mean) + thresholds.role_mi_std_margin * float(perm_std)
    stability_required = float(perm_stability) + thresholds.role_stability_margin
    passed = bool(role_valid and float(mi) >= mi_required and float(stability) >= stability_required)
    return {
        "pass": passed,
        "role_valid": bool(role_valid),
        "mi": float(mi),
        "perm_mean": float(perm_mean),
        "perm_std": float(perm_std),
        "mi_required": float(mi_required),
        "stability": float(stability),
        "perm_stability": float(perm_stability),
        "stability_required": float(stability_required),
    }
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```powershell
python -m pytest tests\test_r12_substrate_gate.py -q
```

Expected:

```text
6 passed
```

---

### Task 2: Existing-CSV OPT Triage

**Files:**
- Create: `scripts/analyze_r12_csv_triage.py`
- Modify: `tests/test_r12_substrate_gate.py`

- [ ] **Step 1: Add a test for CSV triage behavior**

Append to `tests/test_r12_substrate_gate.py`:

```python
import csv
import json
import subprocess
import sys
from pathlib import Path


def test_csv_triage_script_reports_missing_and_present_fields(tmp_path):
    metrics_dir = tmp_path / "run_a" / "metrics"
    metrics_dir.mkdir(parents=True)
    csv_path = metrics_dir / "train_updates.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "total_steps",
                "opt_aggregation_entropy",
                "opt_cd_loss",
                "opt_cmi_loss",
                "compact_norm_mean",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "total_steps": 1,
                "opt_aggregation_entropy": 1.2,
                "opt_cd_loss": 0.1,
                "opt_cmi_loss": 0.2,
                "compact_norm_mean": 3.0,
            }
        )
    out_path = tmp_path / "triage.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/analyze_r12_csv_triage.py",
            "--root",
            str(tmp_path),
            "--output",
            str(out_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "r12_csv_triage runs=1" in result.stdout
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["runs"][0]["rows"] == 1
    assert payload["runs"][0]["missing_fields"] == []
```

- [ ] **Step 2: Run the test and verify it fails because the script does not exist**

Run:

```powershell
python -m pytest tests\test_r12_substrate_gate.py::test_csv_triage_script_reports_missing_and_present_fields -q
```

Expected:

```text
CalledProcessError
```

- [ ] **Step 3: Implement the triage script**

Create `scripts/analyze_r12_csv_triage.py`:

```python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


FIELDS = (
    "opt_aggregation_entropy",
    "opt_cd_loss",
    "opt_cmi_loss",
    "compact_norm_mean",
)


def _to_float(value: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if np.isfinite(out) else float("nan")


def summarize_csv(path: Path) -> dict:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    summary = {
        "path": str(path),
        "rows": len(rows),
        "missing_fields": [field for field in FIELDS if field not in (rows[0].keys() if rows else [])],
        "fields": {},
    }
    for field in FIELDS:
        values = np.asarray([_to_float(row.get(field, "")) for row in rows], dtype=np.float64)
        values = values[np.isfinite(values)]
        summary["fields"][field] = {
            "count": int(values.size),
            "mean": float(np.mean(values)) if values.size else 0.0,
            "std": float(np.std(values)) if values.size else 0.0,
            "min": float(np.min(values)) if values.size else 0.0,
            "max": float(np.max(values)) if values.size else 0.0,
            "last": float(values[-1]) if values.size else 0.0,
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Round-12 zero-new-run OPT CSV triage.")
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(args.root)
    paths = sorted(root.glob("**/metrics/train_updates.csv"))
    runs = [summarize_csv(path) for path in paths]
    payload = {"root": str(root), "runs": runs}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"r12_csv_triage runs={len(runs)} output={output}")
    for run in runs:
        entropy = run["fields"]["opt_aggregation_entropy"]["last"]
        compact = run["fields"]["compact_norm_mean"]["last"]
        print(f"  {run['path']} rows={run['rows']} entropy_last={entropy:.6f} compact_norm_last={compact:.6f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the targeted test**

Run:

```powershell
python -m pytest tests\test_r12_substrate_gate.py::test_csv_triage_script_reports_missing_and_present_fields -q
```

Expected:

```text
1 passed
```

---

### Task 3: Diagnostic-Only Checkpoint-Grid Exporter

**Files:**
- Create: `ha_ctse_process/export_substrate_gate.py`
- Modify: `tests/test_r12_substrate_gate.py`

- [ ] **Step 1: Add smoke assertions for exporter CLI help**

Append to `tests/test_r12_substrate_gate.py`:

```python
def test_exporter_cli_help_runs():
    result = subprocess.run(
        [sys.executable, "-m", "ha_ctse_process.export_substrate_gate", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--checkpoint_dir" in result.stdout
    assert "--dump_interval" in result.stdout
    assert "--require_role_label_variance" in result.stdout
```

- [ ] **Step 2: Run the new test and verify it fails because the exporter does not exist**

Run:

```powershell
python -m pytest tests\test_r12_substrate_gate.py::test_exporter_cli_help_runs -q
```

Expected:

```text
No module named ha_ctse_process.export_substrate_gate
```

- [ ] **Step 3: Implement the exporter skeleton with real CLI and checkpoint discovery**

Create `ha_ctse_process/export_substrate_gate.py` with the following structure. Keep it diagnostic-only; do not call any training update, optimizer step, or reward composer.

```python
"""Diagnostic-only Round-12 substrate gate exporter.

This replays stored HA-CTSE checkpoints and dumps OPT situation traces.  It is
not part of training and intentionally forces topology-role counterfactual
labels through TopologyRoleExtractor instead of relying on training-time probe
flags.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import torch

from ha_ctse_process.plotting import extract_uav_metrics
from ha_ctse_process.standalone_agent import SegmentManager
from ha_ctse_process.topology_role import TOPOLOGY_ROLE_NAMES, TopologyRoleExtractor
from ha_ctse_process.train import (
    apply_checkpoint_structure,
    apply_standalone_overrides,
    create_agent,
    create_env,
    load_checkpoint,
    load_checkpoint_metadata,
    load_config,
)


STEP_FIELDS = (
    "checkpoint",
    "update_idx",
    "total_steps",
    "episode",
    "step",
    "reward_so_far",
    "omega_argmax",
    "omega_entropy",
    "compact_norm",
    "delta_omega_l1",
    "coverage_positive_step",
    "coverage_eq1_step",
    "zero_throughput_step",
    "throughput_gt5_step",
    "backhaul_connected_step",
    "throughput",
    "coverage",
)


ROLE_FIELDS = (
    "checkpoint",
    "update_idx",
    "total_steps",
    "episode",
    "step",
    "agent_id",
    "omega_argmax",
    "role_label",
    "role_available",
    "role_name",
    "role_score_idle",
    "role_score_relay",
    "role_score_service",
    "role_score_relay_service",
)


def _append_csv(path: Path, row: dict[str, Any], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})


def _checkpoint_update(path: Path) -> int | None:
    match = re.search(r"standalone_process_core_update_(\\d+)\\.pt$", path.name)
    return int(match.group(1)) if match else None


def _parse_updates(text: str) -> tuple[set[int], bool] | None:
    text = str(text or "").strip()
    if not text:
        return None
    updates: set[int] = set()
    final = False
    for chunk in text.replace(";", ",").split(","):
        token = chunk.strip().lower()
        if not token:
            continue
        if token == "final":
            final = True
        else:
            updates.add(int(token))
    return updates, final


def discover_checkpoints(checkpoint_dir: Path, updates: str, update_stride: int, no_final: bool) -> list[Path]:
    update_paths = sorted(
        checkpoint_dir.glob("standalone_process_core_update_*.pt"),
        key=lambda path: _checkpoint_update(path) or -1,
    )
    final_path = checkpoint_dir / "standalone_process_core_final.pt"
    update_filter = _parse_updates(updates)
    selected: list[Path] = []
    if update_filter is not None:
        requested, want_final = update_filter
        selected.extend(path for path in update_paths if _checkpoint_update(path) in requested)
        if want_final and final_path.exists():
            selected.append(final_path)
    else:
        stride = int(update_stride)
        selected.extend(path for path in update_paths if stride <= 0 or ((_checkpoint_update(path) or 0) % stride == 0))
        if final_path.exists() and not no_final:
            selected.append(final_path)
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in selected:
        resolved = path.resolve()
        if resolved not in seen:
            deduped.append(path)
            seen.add(resolved)
    return deduped


def _episode_mode(step_metrics: dict[str, float]) -> dict[str, float]:
    throughput = float(step_metrics.get("throughput", 0.0))
    coverage = float(step_metrics.get("coverage", step_metrics.get("coverage_ratio", 0.0)))
    return {
        "coverage_positive_step": 1.0 if coverage > 1e-6 else 0.0,
        "coverage_eq1_step": 1.0 if coverage >= 0.999 else 0.0,
        "zero_throughput_step": 1.0 if throughput <= 1e-6 else 0.0,
        "throughput_gt5_step": 1.0 if throughput > 5.0 else 0.0,
        "backhaul_connected_step": float(step_metrics.get("backhaul_connected_flag", 0.0)),
        "throughput": throughput,
        "coverage": coverage,
    }


def _role_rows(
    extractor: TopologyRoleExtractor,
    checkpoint: str,
    update_idx: int,
    total_steps: int,
    episode: int,
    step: int,
    omega_argmax: int,
    info: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for agent_id in range(extractor.n_agents):
        segment = SimpleNamespace(
            state_info_seq=[dict(info or {})],
            reward_info_seq=[dict(info or {})],
            agent_id=agent_id,
            length=1,
        )
        sample = extractor.extract(segment)
        scores = np.asarray(sample.role_scores, dtype=np.float64).reshape(-1)
        rows.append(
            {
                "checkpoint": checkpoint,
                "update_idx": int(update_idx),
                "total_steps": int(total_steps),
                "episode": int(episode),
                "step": int(step),
                "agent_id": int(agent_id),
                "omega_argmax": int(omega_argmax),
                "role_label": int(sample.label),
                "role_available": 1.0 if sample.available else 0.0,
                "role_name": TOPOLOGY_ROLE_NAMES[int(sample.label)],
                "role_score_idle": float(scores[0]) if scores.size > 0 else 0.0,
                "role_score_relay": float(scores[1]) if scores.size > 1 else 0.0,
                "role_score_service": float(scores[2]) if scores.size > 2 else 0.0,
                "role_score_relay_service": float(scores[3]) if scores.size > 3 else 0.0,
            }
        )
    return rows


def export_checkpoint(config, args: argparse.Namespace, checkpoint_path: Path) -> None:
    metadata = load_checkpoint_metadata(str(checkpoint_path))
    apply_checkpoint_structure(config, args, metadata)
    env = create_env(config, config.scenario, int(args.seed), rank=0, scale_mode="eval")
    try:
        obs, info = env.reset(seed=int(args.seed))
        state_dim = int(np.asarray(info.get("state"), dtype=np.float32).reshape(-1).size)
        agent = create_agent(config, args, env, num_envs=1, state_dim=state_dim)
    finally:
        env.close()
    total_steps, update_idx = load_checkpoint(str(checkpoint_path), agent, load_optimizers=False)
    env = create_env(config, config.scenario, int(args.seed) + 100000, rank=0, scale_mode="eval")
    extractor = TopologyRoleExtractor(
        n_agents=int(agent.n_agents),
        min_score=float(getattr(config, "topology_role_min_score", 1e-6)),
    )
    step_path = Path(args.log_dir) / "substrate_steps.csv"
    role_path = Path(args.log_dir) / "substrate_roles.csv"
    try:
        for episode in range(int(args.eval_episodes)):
            obs, info = env.reset(seed=int(args.seed) + 100000 + episode)
            state = info.get("state")
            agent.reset_env_state(0)
            agent.segments = SegmentManager(agent.num_envs, agent.n_agents)
            reward_so_far = 0.0
            prev_omega: np.ndarray | None = None
            for step in range(int(args.eval_max_steps)):
                agent.maybe_assign_skills(
                    obs,
                    state=state,
                    step=step,
                    k=int(args.skill_interval),
                    env_id=0,
                    deterministic=True,
                )
                if step % int(args.dump_interval) == 0:
                    state_t = torch.as_tensor(np.asarray(state, dtype=np.float32).reshape(1, -1), device=agent.device)
                    joint_t = torch.as_tensor(np.asarray(obs, dtype=np.float32).reshape(1, agent.n_agents, agent.obs_dim), device=agent.device)
                    with torch.no_grad():
                        compact, _cd, _cmi, weights, entropy = agent.compact(state_t, joint_t)
                    omega = weights.detach().cpu().numpy().reshape(-1)
                    compact_np = compact.detach().cpu().numpy().reshape(-1)
                    delta = 0.0 if prev_omega is None else float(np.sum(np.abs(omega - prev_omega)))
                    prev_omega = omega.copy()
                    step_metrics = extract_uav_metrics(info if isinstance(info, dict) else {})
                    mode = _episode_mode(step_metrics)
                    omega_argmax = int(np.argmax(omega)) if omega.size else 0
                    row = {
                        "checkpoint": checkpoint_path.name,
                        "update_idx": int(update_idx),
                        "total_steps": int(total_steps),
                        "episode": int(episode),
                        "step": int(step),
                        "reward_so_far": float(reward_so_far),
                        "omega_argmax": omega_argmax,
                        "omega_entropy": float(entropy.detach().cpu().numpy().reshape(-1)[0]),
                        "compact_norm": float(np.linalg.norm(compact_np)),
                        "delta_omega_l1": delta,
                        **mode,
                    }
                    _append_csv(step_path, row, STEP_FIELDS)
                    for role_row in _role_rows(
                        extractor,
                        checkpoint_path.name,
                        int(update_idx),
                        int(total_steps),
                        int(episode),
                        int(step),
                        omega_argmax,
                        info if isinstance(info, dict) else {},
                    ):
                        _append_csv(role_path, role_row, ROLE_FIELDS)
                actions, _, _ = agent.act_low(obs, env_id=0, deterministic=True, state=state)
                obs, reward, terminated, truncated, info = env.step(actions)
                state = info.get("next_state", state)
                reward_so_far += float(reward)
                if bool(terminated or truncated):
                    break
    finally:
        env.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export R12 substrate-gate diagnostic rows.")
    parser.add_argument("--checkpoint_dir", required=True)
    parser.add_argument("--log_dir", required=True)
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--preset", default="")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--n_agents", type=int, default=0)
    parser.add_argument("--skill_interval", type=int, default=10)
    parser.add_argument("--skill_lifetime_candidates", default="")
    parser.add_argument("--updates", default="20,40,60,final")
    parser.add_argument("--update_stride", type=int, default=20)
    parser.add_argument("--no_final", action="store_true")
    parser.add_argument("--eval_episodes", type=int, default=4)
    parser.add_argument("--eval_max_steps", type=int, default=500)
    parser.add_argument("--dump_interval", type=int, default=10)
    parser.add_argument("--require_role_label_variance", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if int(args.dump_interval) <= 0:
        raise ValueError("--dump_interval must be positive")
    log_dir = Path(args.log_dir)
    if args.overwrite:
        for name in ("substrate_steps.csv", "substrate_roles.csv"):
            path = log_dir / name
            if path.exists():
                path.unlink()
    config = load_config(args.config, args.preset or None)
    config.scenario = args.scenario
    apply_standalone_overrides(config, args)
    checkpoints = discover_checkpoints(
        Path(args.checkpoint_dir),
        updates=str(args.updates),
        update_stride=int(args.update_stride),
        no_final=bool(args.no_final),
    )
    if not checkpoints:
        raise FileNotFoundError(f"No checkpoints selected from {args.checkpoint_dir}")
    for checkpoint in checkpoints:
        print(f"r12_export checkpoint={checkpoint}")
        export_checkpoint(config, args, checkpoint)
    print(f"r12_export_done checkpoints={len(checkpoints)} log_dir={log_dir}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run exporter CLI help test**

Run:

```powershell
python -m pytest tests\test_r12_substrate_gate.py::test_exporter_cli_help_runs -q
```

Expected:

```text
1 passed
```

---

### Task 4: Offline Substrate Analyzer

**Files:**
- Create: `scripts/analyze_r12_substrate_gate.py`
- Modify: `tests/test_r12_substrate_gate.py`

- [ ] **Step 1: Add a test that analyzer refuses all-zero role labels**

Append to `tests/test_r12_substrate_gate.py`:

```python
def test_substrate_analyzer_fails_on_all_zero_role_labels(tmp_path):
    import csv

    dump_dir = tmp_path / "dump"
    dump_dir.mkdir()
    with (dump_dir / "substrate_steps.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "checkpoint",
                "episode",
                "step",
                "omega_argmax",
                "coverage_positive_step",
                "zero_throughput_step",
                "compact_norm",
            ],
        )
        writer.writeheader()
        for step, omega in enumerate([0, 0, 0, 1, 1, 1]):
            writer.writerow(
                {
                    "checkpoint": "ckpt.pt",
                    "episode": 0,
                    "step": step,
                    "omega_argmax": omega,
                    "coverage_positive_step": 1 if step >= 3 else 0,
                    "zero_throughput_step": 0 if step >= 3 else 1,
                    "compact_norm": 1.0,
                }
            )
    with (dump_dir / "substrate_roles.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["checkpoint", "episode", "step", "agent_id", "omega_argmax", "role_label", "role_available"],
        )
        writer.writeheader()
        for step, omega in enumerate([0, 0, 0, 1, 1, 1]):
            for agent_id in range(3):
                writer.writerow(
                    {
                        "checkpoint": "ckpt.pt",
                        "episode": 0,
                        "step": step,
                        "agent_id": agent_id,
                        "omega_argmax": omega,
                        "role_label": 0,
                        "role_available": 1,
                    }
                )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/analyze_r12_substrate_gate.py",
            "--dump_dir",
            str(dump_dir),
            "--output",
            str(tmp_path / "report.json"),
            "--require_role_label_variance",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "invalid G-ROLE labels" in result.stderr
```

- [ ] **Step 2: Run the test and verify it fails because analyzer does not exist**

Run:

```powershell
python -m pytest tests\test_r12_substrate_gate.py::test_substrate_analyzer_fails_on_all_zero_role_labels -q
```

Expected:

```text
assert 2 == ...
```

- [ ] **Step 3: Implement the analyzer**

Create `scripts/analyze_r12_substrate_gate.py`:

```python
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

from ha_ctse_process.substrate_gate import (
    SubstrateThresholds,
    auc_binary,
    dwell_lengths,
    dwell_pass,
    mutual_information_discrete,
    outcome_pass,
    role_label_validity,
    role_pass,
    transition_diag_mass,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        value = float(row.get(key, default))
    except (TypeError, ValueError):
        return default
    return value if np.isfinite(value) else default


def _int(row: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, default)))
    except (TypeError, ValueError):
        return default


def _block_shuffle(values: np.ndarray, block: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    block = max(int(block), 1)
    chunks = [values[start : start + block] for start in range(0, values.size, block)]
    order = np.arange(len(chunks))
    rng.shuffle(order)
    return np.concatenate([chunks[int(idx)] for idx in order]) if chunks else values.copy()


def analyze(dump_dir: Path, require_role_label_variance: bool) -> dict:
    step_rows = _read_csv(dump_dir / "substrate_steps.csv")
    role_rows = _read_csv(dump_dir / "substrate_roles.csv")
    memberships = np.asarray([_int(row, "omega_argmax") for row in step_rows], dtype=np.int64)
    dwell = dwell_lengths(memberships)
    diag = transition_diag_mass(memberships)
    null = transition_diag_mass(_block_shuffle(memberships, block=3, seed=17))
    dwell_report = dwell_pass(
        median_dwell=float(np.median(dwell)) if dwell.size else 0.0,
        transition_diag=diag,
        null_transition_diag=null,
    )

    outcome_target = np.asarray([_float(row, "coverage_positive_step") for row in step_rows], dtype=np.int64)
    omega_score = memberships.astype(np.float64)
    compact_score = np.asarray([_float(row, "compact_norm") for row in step_rows], dtype=np.float64)
    outcome_auc = auc_binary(outcome_target, omega_score)
    baseline_auc = auc_binary(outcome_target, compact_score)
    outcome_report = outcome_pass(outcome_auc, baseline_auc)

    role_labels = np.asarray([_int(row, "role_label") for row in role_rows if _float(row, "role_available") > 0.0], dtype=np.int64)
    role_omega = np.asarray([_int(row, "omega_argmax") for row in role_rows if _float(row, "role_available") > 0.0], dtype=np.int64)
    validity = role_label_validity(role_labels)
    if require_role_label_variance and not bool(validity["valid"]):
        raise ValueError(f"invalid G-ROLE labels: {validity}")
    mi = mutual_information_discrete(role_omega, role_labels)
    rng = np.random.default_rng(23)
    perm_mis = []
    for _ in range(64):
        permuted = role_labels.copy()
        rng.shuffle(permuted)
        perm_mis.append(mutual_information_discrete(role_omega, permuted))
    perm = np.asarray(perm_mis, dtype=np.float64)
    role_report = role_pass(
        role_valid=bool(validity["valid"]),
        mi=mi,
        perm_mean=float(np.mean(perm)) if perm.size else 0.0,
        perm_std=float(np.std(perm)) if perm.size else 0.0,
        stability=diag,
        perm_stability=null,
    )

    return {
        "dump_dir": str(dump_dir),
        "rows": {"steps": len(step_rows), "roles": len(role_rows)},
        "g_dwell": dwell_report,
        "g_outcome": outcome_report,
        "g_role_validity": validity,
        "g_role": role_report,
        "gate_pass": bool(dwell_report["pass"] and outcome_report["pass"] and role_report["pass"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze R12 substrate-gate dump artifacts.")
    parser.add_argument("--dump_dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--require_role_label_variance", action="store_true")
    args = parser.parse_args()
    try:
        report = analyze(Path(args.dump_dir), bool(args.require_role_label_variance))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
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
```

- [ ] **Step 4: Run analyzer tests**

Run:

```powershell
python -m pytest tests\test_r12_substrate_gate.py::test_substrate_analyzer_fails_on_all_zero_role_labels -q
```

Expected:

```text
1 passed
```

---

### Task 5: One-Key Local Runner

**Files:**
- Create: `scripts/run_r12_substrate_gate_local.ps1`

- [ ] **Step 1: Create the PowerShell runner**

Create `scripts/run_r12_substrate_gate_local.ps1`:

```powershell
param(
  [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
  [string]$CheckpointDir = "logs\ha_ctse_process_s7s1_short_reward_pure_32env_seed1_1280k",
  [string]$LogDir = "logs\r12_substrate_gate_local",
  [string]$Updates = "20,40,60,final",
  [int]$EvalEpisodes = 4,
  [int]$EvalMaxSteps = 500,
  [int]$DumpInterval = 10,
  [string]$Device = "cpu",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$commands = @(
  @(
    $Python, "-m", "ha_ctse_process.export_substrate_gate",
    "--checkpoint_dir", $CheckpointDir,
    "--log_dir", $LogDir,
    "--config", "ha_ctse_process.config",
    "--scenario", "energy",
    "--preset", "S7-S1",
    "--seed", "1",
    "--n_agents", "6",
    "--skill_interval", "10",
    "--updates", $Updates,
    "--eval_episodes", "$EvalEpisodes",
    "--eval_max_steps", "$EvalMaxSteps",
    "--dump_interval", "$DumpInterval",
    "--device", $Device,
    "--require_role_label_variance",
    "--overwrite"
  ),
  @(
    $Python, "scripts/analyze_r12_substrate_gate.py",
    "--dump_dir", $LogDir,
    "--output", (Join-Path $LogDir "substrate_gate_report.json"),
    "--require_role_label_variance"
  )
)

Write-Host "R12 substrate gate local runner"
Write-Host "  checkpoint_dir: $CheckpointDir"
Write-Host "  log_dir:        $LogDir"
Write-Host "  updates:        $Updates"
Write-Host "  eval_episodes:  $EvalEpisodes"
Write-Host "  eval_max_steps: $EvalMaxSteps"
Write-Host "  dump_interval:  $DumpInterval"
Write-Host "  device:         $Device"

foreach ($cmd in $commands) {
  $line = ($cmd | ForEach-Object {
    if ($_ -match "\s") { '"' + $_ + '"' } else { $_ }
  }) -join " "
  Write-Host ""
  Write-Host $line
  if (-not $DryRun) {
    & $cmd[0] @($cmd[1..($cmd.Count - 1)])
  }
}
```

- [ ] **Step 2: Dry-run the runner**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_substrate_gate_local.ps1 `
  -DryRun
```

Expected:

```text
R12 substrate gate local runner
python.exe -m ha_ctse_process.export_substrate_gate ...
python.exe scripts/analyze_r12_substrate_gate.py ...
```

---

### Task 6: Smoke Export on a Tiny Checkpoint

**Files:**
- No new files.

- [ ] **Step 1: Compile new Python files**

Run:

```powershell
python -m py_compile `
  ha_ctse_process\substrate_gate.py `
  ha_ctse_process\export_substrate_gate.py `
  scripts\analyze_r12_csv_triage.py `
  scripts\analyze_r12_substrate_gate.py
```

Expected:

```text
No output and exit code 0.
```

- [ ] **Step 2: Create a tiny local checkpoint**

Run:

```powershell
python -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --num_envs 1 `
  --collector_backend sync `
  --rollout_length 16 `
  --skill_interval 4 `
  --skill_lifetime_candidates 1,2 `
  --total_timesteps 32 `
  --eval_interval 0 `
  --save_interval 1 `
  --checkpoint_keep_last 4 `
  --device cpu `
  --log_dir logs\r12_substrate_gate_smoke_train
```

Expected:

```text
Training exits successfully and writes standalone_process_core_update_*.pt.
```

- [ ] **Step 3: Export substrate rows from the tiny checkpoint**

Run:

```powershell
python -m ha_ctse_process.export_substrate_gate `
  --checkpoint_dir logs\r12_substrate_gate_smoke_train `
  --log_dir logs\r12_substrate_gate_smoke_dump `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --seed 1 `
  --n_agents 6 `
  --skill_interval 4 `
  --skill_lifetime_candidates 1,2 `
  --updates final `
  --eval_episodes 1 `
  --eval_max_steps 16 `
  --dump_interval 4 `
  --device cpu `
  --overwrite
```

Expected:

```text
r12_export_done checkpoints=1 log_dir=logs\r12_substrate_gate_smoke_dump
```

- [ ] **Step 4: Analyze the tiny dump without requiring role variance**

Run:

```powershell
python scripts\analyze_r12_substrate_gate.py `
  --dump_dir logs\r12_substrate_gate_smoke_dump `
  --output logs\r12_substrate_gate_smoke_dump\substrate_gate_report.json
```

Expected:

```text
r12_substrate_gate pass=...
```

The tiny smoke is not expected to pass the scientific gate. It only verifies artifact shape.

---

### Task 7: Memory Sync After Implementation

**Files:**
- Modify: `memory/ExpRecord.md`
- Modify: `memory/ATTENTION_POINTER.md`
- Modify only if algorithm meaning changes: `memory/ALGORITHM_PRINCIPLES.md`
- Modify only if stage status changes: `memory/IMPLEMENTATION_PLAN.md`

- [ ] **Step 1: Fill concrete commands in `EXP-20260702-substrate-gate`**

Replace the `Command/script` block in `memory/ExpRecord.md` for `EXP-20260702-substrate-gate` with:

```text
Command/script:

```powershell
# 1. Zero-new-run triage.
python scripts\analyze_r12_csv_triage.py `
  --root logs `
  --output logs\r12_substrate_gate_local\csv_triage.json

# 2. Dry-run checkpoint-grid exporter.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_substrate_gate_local.ps1 `
  -CheckpointDir logs\ha_ctse_process_s7s1_short_reward_pure_32env_seed1_1280k `
  -LogDir logs\r12_substrate_gate_local `
  -Updates 20,40,60,final `
  -EvalEpisodes 4 `
  -EvalMaxSteps 500 `
  -DumpInterval 10 `
  -Device cpu `
  -DryRun

# 3. Actual diagnostic export + gate analyzer.
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_substrate_gate_local.ps1 `
  -CheckpointDir logs\ha_ctse_process_s7s1_short_reward_pure_32env_seed1_1280k `
  -LogDir logs\r12_substrate_gate_local `
  -Updates 20,40,60,final `
  -EvalEpisodes 4 `
  -EvalMaxSteps 500 `
  -DumpInterval 10 `
  -Device cpu
```
```

- [ ] **Step 2: Update `memory/ATTENTION_POINTER.md`**

Add this to `Last Update Notes`:

```text
2026-07-02 (R12 substrate-gate exporter/analyzer implemented): Added pure gate
math, CSV triage, checkpoint-grid eval-only exporter, substrate analyzer, and
local runner. Next action is to run `scripts/run_r12_substrate_gate_local.ps1`
on a real checkpoint directory and read `substrate_gate_report.json`; do not
implement reward/hazard/SEF until G-DWELL/G-OUTCOME/valid G-ROLE are read.
```

- [ ] **Step 3: Run final verification**

Run:

```powershell
python -m pytest tests\test_r12_substrate_gate.py -q
python -m py_compile `
  ha_ctse_process\substrate_gate.py `
  ha_ctse_process\export_substrate_gate.py `
  scripts\analyze_r12_csv_triage.py `
  scripts\analyze_r12_substrate_gate.py
```

Expected:

```text
All tests pass. py_compile exits with code 0.
```

---

## Self-Review

Spec coverage:

- G-ROLE trap is handled by direct `TopologyRoleExtractor` usage in the exporter and the analyzer's `role_label_validity()` hard check.
- Checkpoint grid is handled by `--updates 20,40,60,final` plus `discover_checkpoints()`.
- Pre-registered thresholds are encoded in `SubstrateThresholds` and written in `ExpRecord.md`.
- The missing ExpRecord entry already exists and Task 7 fills concrete commands after implementation.
- No reward path is touched.

Placeholder scan:

- No task depends on an unspecified module name.
- All created files have exact paths.
- All commands are concrete.

Type consistency:

- `omega_argmax` is the discrete membership used by dwell, outcome, and role MI.
- `role_label` is per-agent and comes from `TopologyRoleExtractor.extract()`.
- Analyzer input file names match exporter output file names: `substrate_steps.csv` and `substrate_roles.csv`.

Plan complete and saved to `docs/superpowers/plans/2026-07-02-r12-substrate-gate.md`.
