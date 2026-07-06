# R12 Compact-C Fallback Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the diagnostic-only R12 substrate gate so it exports full OPT compact context `c_tau`, clusters it offline, and tests whether `cluster(c_tau)` is a better situation substrate than raw `omega_argmax`.

**Architecture:** Keep the existing reward-free exporter/analyzer split. The exporter writes full vector fields as JSON strings (`compact_json`, `omega_json`) without changing training. The analyzer parses vectors, builds deterministic compact clusters, and computes the same G-DWELL / G-OUTCOME / G-ROLE gates for both raw `omega_argmax` and `compact_cluster`, with an explicit fallback decision.

**Tech Stack:** Python 3.10, NumPy, existing HA-CTSE checkpoint exporter, CSV/JSON artifacts, pytest, PowerShell runner.

---

## File Structure

- Modify `ha_ctse_process/substrate_gate.py`
  - Add pure NumPy helpers for vector parsing, row standardization, deterministic k-means, cluster-count selection, discrete-membership outcome AUC, and reusable gate aggregation.
  - No PyTorch, no env, no reward logic.

- Modify `ha_ctse_process/export_substrate_gate.py`
  - Add `compact_dim`, `compact_json`, `omega_dim`, and `omega_json` to `substrate_steps.csv`.
  - Preserve existing fields and fail on incompatible old CSV headers as it does today.

- Modify `scripts/analyze_r12_substrate_gate.py`
  - Parse compact vectors from `substrate_steps.csv`.
  - Compute `compact_cluster` labels with deterministic k-means.
  - Compute membership gate reports for both `omega` and `compact_cluster`.
  - Keep backward-compatible top-level `g_dwell`, `g_outcome`, `g_role_validity`, `g_role`, and `gate_pass` as omega results.
  - Add `membership_reports`, `compact_cluster`, and `fallback_decision`.

- Modify `tests/test_r12_substrate_gate.py`
  - Add pure utility tests.
  - Extend substrate CSV helpers to optionally write compact vectors.
  - Add analyzer tests proving compact clusters can pass outcome where omega fails, and proving missing compact vectors fail closed for the compact branch.

- Modify `scripts/run_r12_substrate_gate_local.ps1`
  - No required CLI change. It should keep working after exporter/analyzer output schema changes.

- Modify memory files after implementation:
  - `memory/ExpRecord.md`
  - `memory/ATTENTION_POINTER.md`
  - `memory/IMPLEMENTATION_PLAN.md`
  - `memory/cross_validation.md`

---

### Task 1: Pure Compact Vector and Clustering Utilities

**Files:**
- Modify: `ha_ctse_process/substrate_gate.py`
- Modify/Test: `tests/test_r12_substrate_gate.py`

- [ ] **Step 1: Add failing tests for vector parsing and deterministic clustering**

Append these tests near the other pure utility tests in `tests/test_r12_substrate_gate.py`:

```python
def test_parse_vector_field_accepts_json_list_and_rejects_bad_values():
    from ha_ctse_process.substrate_gate import parse_vector_field

    parsed = parse_vector_field("[1.0, 2, -3.5]")
    assert parsed.shape == (3,)
    assert np.allclose(parsed, np.asarray([1.0, 2.0, -3.5]))

    assert parse_vector_field("").size == 0
    assert parse_vector_field("not-json").size == 0
    assert parse_vector_field("[1.0, \"bad\"]").size == 0
    assert parse_vector_field("[1.0, NaN]").size == 0


def test_standardize_rows_centers_and_scales_columns():
    from ha_ctse_process.substrate_gate import standardize_rows

    values = np.asarray([[1.0, 10.0], [2.0, 10.0], [3.0, 10.0]])
    scaled = standardize_rows(values)
    assert scaled.shape == values.shape
    assert abs(float(np.mean(scaled[:, 0]))) < 1e-9
    assert np.isclose(float(np.std(scaled[:, 0])), 1.0)
    assert np.allclose(scaled[:, 1], 0.0)


def test_deterministic_kmeans_splits_two_compact_clouds():
    from ha_ctse_process.substrate_gate import deterministic_kmeans

    values = np.asarray(
        [
            [0.0, 0.0],
            [0.1, 0.0],
            [0.0, 0.1],
            [5.0, 5.0],
            [5.1, 5.0],
            [5.0, 5.1],
        ],
        dtype=np.float64,
    )
    labels_a = deterministic_kmeans(values, k=2, seed=7)
    labels_b = deterministic_kmeans(values, k=2, seed=7)
    assert np.array_equal(labels_a, labels_b)
    assert len(set(labels_a[:3])) == 1
    assert len(set(labels_a[3:])) == 1
    assert labels_a[0] != labels_a[3]


def test_choose_cluster_count_tracks_omega_cardinality_with_bounds():
    from ha_ctse_process.substrate_gate import choose_cluster_count

    assert choose_cluster_count(n_rows=20, omega_labels=np.asarray([0, 0, 1, 1])) == 2
    assert choose_cluster_count(n_rows=20, omega_labels=np.asarray([0, 0, 0])) == 2
    assert choose_cluster_count(n_rows=3, omega_labels=np.asarray([0, 1, 2])) == 3
    assert choose_cluster_count(n_rows=1, omega_labels=np.asarray([0])) == 1
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_substrate_gate.py `
  -q --basetemp .pytest_tmp_r12_compact_plan
```

Expected:

```text
FAILED ... cannot import name 'parse_vector_field'
```

- [ ] **Step 3: Implement vector parsing and k-means helpers**

Add these imports and functions to `ha_ctse_process/substrate_gate.py`:

```python
import json


def parse_vector_field(raw: object) -> np.ndarray:
    """Parse a JSON vector field from substrate_steps.csv."""
    if raw is None:
        return np.asarray([], dtype=np.float64)
    text = str(raw).strip()
    if not text:
        return np.asarray([], dtype=np.float64)
    try:
        payload = json.loads(text)
        values = np.asarray(payload, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError, json.JSONDecodeError):
        return np.asarray([], dtype=np.float64)
    if values.size == 0 or not np.all(np.isfinite(values)):
        return np.asarray([], dtype=np.float64)
    return values


def standardize_rows(values: np.ndarray) -> np.ndarray:
    """Column-standardize a 2-D matrix while keeping constant columns at zero."""
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError("standardize_rows requires a 2-D matrix")
    if matrix.size == 0:
        return matrix.copy()
    mean = np.mean(matrix, axis=0, keepdims=True)
    std = np.std(matrix, axis=0, keepdims=True)
    safe_std = np.where(std > 1e-12, std, 1.0)
    scaled = (matrix - mean) / safe_std
    return np.where(np.isfinite(scaled), scaled, 0.0)


def choose_cluster_count(
    *,
    n_rows: int,
    omega_labels: np.ndarray,
    min_k: int = 2,
    max_k: int = 8,
) -> int:
    """Choose compact-cluster count from omega cardinality, bounded by sample count."""
    rows = max(int(n_rows), 0)
    if rows <= 1:
        return rows
    labels = np.asarray(omega_labels).reshape(-1)
    omega_k = int(np.unique(labels).size) if labels.size else min_k
    k = max(int(min_k), omega_k)
    k = min(k, int(max_k), rows)
    return max(k, 1)


def deterministic_kmeans(
    values: np.ndarray,
    *,
    k: int,
    seed: int = 13,
    max_iter: int = 64,
) -> np.ndarray:
    """Small deterministic NumPy k-means for offline diagnostics."""
    matrix = standardize_rows(values)
    n_rows = matrix.shape[0]
    if n_rows == 0:
        return np.asarray([], dtype=np.int64)
    k = int(max(1, min(int(k), n_rows)))
    if k == 1:
        return np.zeros(n_rows, dtype=np.int64)

    rng = np.random.default_rng(seed)
    first = int(rng.integers(0, n_rows))
    centers = [matrix[first]]
    for _ in range(1, k):
        distances = np.min(
            np.stack([np.sum((matrix - center) ** 2, axis=1) for center in centers], axis=1),
            axis=1,
        )
        next_idx = int(np.argmax(distances))
        centers.append(matrix[next_idx])
    centers_arr = np.asarray(centers, dtype=np.float64)

    labels = np.zeros(n_rows, dtype=np.int64)
    for _ in range(max(int(max_iter), 1)):
        dist = np.stack(
            [np.sum((matrix - center) ** 2, axis=1) for center in centers_arr],
            axis=1,
        )
        new_labels = np.argmin(dist, axis=1).astype(np.int64)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for idx in range(k):
            mask = labels == idx
            if np.any(mask):
                centers_arr[idx] = np.mean(matrix[mask], axis=0)
    return labels
```

- [ ] **Step 4: Run tests and verify Task 1 passes**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_substrate_gate.py `
  -q --basetemp .pytest_tmp_r12_compact_task1
```

Expected:

```text
passed
```

---

### Task 2: Discrete Membership Outcome Scoring

**Files:**
- Modify: `ha_ctse_process/substrate_gate.py`
- Modify/Test: `tests/test_r12_substrate_gate.py`

- [ ] **Step 1: Add failing tests for label-permutation-safe membership AUC**

Append:

```python
def test_discrete_membership_auc_is_label_permutation_safe():
    from ha_ctse_process.substrate_gate import discrete_membership_auc

    target = np.asarray([0, 0, 0, 1, 1, 1], dtype=np.int64)
    labels_a = np.asarray([7, 7, 7, 3, 3, 3], dtype=np.int64)
    labels_b = np.asarray([3, 3, 3, 7, 7, 7], dtype=np.int64)

    report_a = discrete_membership_auc(target, labels_a)
    report_b = discrete_membership_auc(target, labels_b)

    assert report_a["target_valid"] is True
    assert report_a["auc"] == 1.0
    assert report_b["auc"] == 1.0
    assert report_a["best_label"] in {3, 7}
    assert report_b["best_label"] in {3, 7}


def test_discrete_membership_auc_fails_closed_for_single_class_target():
    from ha_ctse_process.substrate_gate import discrete_membership_auc

    target = np.asarray([0, 0, 0], dtype=np.int64)
    labels = np.asarray([0, 1, 1], dtype=np.int64)
    report = discrete_membership_auc(target, labels)
    assert report["target_valid"] is False
    assert report["auc"] == 0.5
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_substrate_gate.py `
  -q --basetemp .pytest_tmp_r12_compact_task2_red
```

Expected:

```text
FAILED ... cannot import name 'discrete_membership_auc'
```

- [ ] **Step 3: Implement `discrete_membership_auc()`**

Add to `ha_ctse_process/substrate_gate.py`:

```python
def discrete_membership_auc(target: np.ndarray, labels: np.ndarray) -> dict[str, float | bool | int]:
    """Best one-vs-rest AUC over discrete membership labels.

    This avoids treating arbitrary cluster IDs as ordered scores.
    """
    y = np.asarray(target).reshape(-1)
    z = np.asarray(labels).reshape(-1)
    n = min(y.shape[0], z.shape[0])
    y = y[:n]
    z = z[:n]
    classes = _unique_in_order(y)
    if n == 0 or len(classes) != 2:
        return {
            "target_valid": False,
            "auc": 0.5,
            "best_label": -1,
            "best_orientation": 1,
        }

    best_auc = 0.5
    best_label = -1
    best_orientation = 1
    for label in _unique_in_order(z):
        score = (z == label).astype(np.float64)
        auc = auc_binary(y, score)
        oriented_auc = max(float(auc), float(1.0 - auc))
        orientation = 1 if auc >= 0.5 else -1
        if oriented_auc > best_auc:
            best_auc = oriented_auc
            try:
                best_label = int(label)
            except (TypeError, ValueError):
                best_label = -1
            best_orientation = orientation

    return {
        "target_valid": True,
        "auc": float(best_auc),
        "best_label": int(best_label),
        "best_orientation": int(best_orientation),
    }
```

- [ ] **Step 4: Run tests and verify Task 2 passes**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_substrate_gate.py `
  -q --basetemp .pytest_tmp_r12_compact_task2
```

Expected:

```text
passed
```

---

### Task 3: Export Full Compact and Omega Vectors

**Files:**
- Modify: `ha_ctse_process/export_substrate_gate.py`
- Modify/Test: `tests/test_r12_substrate_gate.py`

- [ ] **Step 1: Add failing tests for exporter vector serialization**

Append near exporter tests:

```python
def test_exporter_vector_json_is_finite_and_round_trippable():
    from ha_ctse_process.export_substrate_gate import _vector_json
    from ha_ctse_process.substrate_gate import parse_vector_field

    text = _vector_json(np.asarray([1.0, 2.5, -3.0], dtype=np.float64))
    parsed = parse_vector_field(text)
    assert np.allclose(parsed, np.asarray([1.0, 2.5, -3.0]))


def test_exporter_vector_json_rejects_non_finite():
    from ha_ctse_process.export_substrate_gate import _vector_json

    try:
        _vector_json(np.asarray([1.0, np.nan]))
    except ValueError as exc:
        assert "non-finite" in str(exc)
    else:
        raise AssertionError("_vector_json should reject non-finite vectors")
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_substrate_gate.py `
  -q --basetemp .pytest_tmp_r12_compact_task3_red
```

Expected:

```text
FAILED ... cannot import name '_vector_json'
```

- [ ] **Step 3: Add vector fields and serializer to exporter**

In `ha_ctse_process/export_substrate_gate.py`, add `json` import:

```python
import json
```

Extend `STEP_FIELDS` after `compact_norm`:

```python
    "compact_dim",
    "compact_json",
    "omega_dim",
    "omega_json",
```

Add helper near `_append_csv()`:

```python
def _vector_json(values: np.ndarray) -> str:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if not np.all(np.isfinite(array)):
        raise ValueError("cannot serialize non-finite vector")
    return json.dumps([float(v) for v in array], separators=(",", ":"))
```

In `export_checkpoint()`, where the step row is created, add:

```python
                        "compact_dim": int(compact_np.size),
                        "compact_json": _vector_json(compact_np),
                        "omega_dim": int(weights_np.size),
                        "omega_json": _vector_json(weights_np),
```

The resulting row block should contain both old and new fields:

```python
                    row = {
                        **checkpoint_info,
                        "episode": episode,
                        "step": step,
                        "reward_so_far": reward_so_far,
                        "omega_argmax": omega_argmax,
                        "omega_entropy": entropy_value,
                        "compact_norm": compact_norm,
                        "compact_dim": int(compact_np.size),
                        "compact_json": _vector_json(compact_np),
                        "omega_dim": int(weights_np.size),
                        "omega_json": _vector_json(weights_np),
                        "delta_omega_l1": delta,
                        **_mode_flags(metrics),
                    }
```

- [ ] **Step 4: Run tests and compile exporter**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_substrate_gate.py `
  -q --basetemp .pytest_tmp_r12_compact_task3

& "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile ha_ctse_process\export_substrate_gate.py
```

Expected:

```text
passed
py_compile exits with code 0
```

---

### Task 4: Analyze Omega and Compact-Cluster Branches Side by Side

**Files:**
- Modify: `scripts/analyze_r12_substrate_gate.py`
- Modify/Test: `tests/test_r12_substrate_gate.py`

- [ ] **Step 1: Extend substrate test helper to write compact vectors**

Replace `_write_substrate_steps()` in `tests/test_r12_substrate_gate.py` with:

```python
def _write_substrate_steps(path, omega_values, coverage_for_omega=None, compact_for_step=None):
    if coverage_for_omega is None:
        coverage_for_omega = lambda omega: 1 if omega else 0
    if compact_for_step is None:
        compact_for_step = lambda step, omega: [float(omega), 0.0]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "checkpoint",
                "episode",
                "step",
                "omega_argmax",
                "coverage_positive_step",
                "zero_throughput_step",
                "throughput_gt5_step",
                "compact_norm",
                "compact_dim",
                "compact_json",
                "omega_dim",
                "omega_json",
            ],
        )
        writer.writeheader()
        for step, omega in enumerate(omega_values):
            compact = np.asarray(compact_for_step(step, omega), dtype=np.float64).reshape(-1)
            writer.writerow(
                {
                    "checkpoint": "ckpt.pt",
                    "episode": 0,
                    "step": step,
                    "omega_argmax": omega,
                    "coverage_positive_step": coverage_for_omega(omega),
                    "zero_throughput_step": 0 if omega else 1,
                    "throughput_gt5_step": 1 if omega else 0,
                    "compact_norm": float(np.linalg.norm(compact)),
                    "compact_dim": int(compact.size),
                    "compact_json": json.dumps([float(v) for v in compact], separators=(",", ":")),
                    "omega_dim": 2,
                    "omega_json": json.dumps([1.0 - float(omega), float(omega)], separators=(",", ":")),
                }
            )
```

- [ ] **Step 2: Add failing compact fallback analyzer tests**

Append:

```python
def test_substrate_analyzer_reports_compact_cluster_branch(tmp_path):
    dump_dir = tmp_path / "dump"
    dump_dir.mkdir()
    omega_values = [0] * 12

    def compact_for_step(step, _omega):
        return [0.0, 0.0] if step < 6 else [5.0, 5.0]

    def coverage_for_omega(_omega):
        return 0

    _write_substrate_steps(
        dump_dir / "substrate_steps.csv",
        omega_values,
        coverage_for_omega=coverage_for_omega,
        compact_for_step=compact_for_step,
    )

    # Rewrite coverage so it is tied to compact cluster, not omega.
    rows = list(csv.DictReader((dump_dir / "substrate_steps.csv").open("r", encoding="utf-8")))
    with (dump_dir / "substrate_steps.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for idx, row in enumerate(rows):
            row["coverage_positive_step"] = 1 if idx >= 6 else 0
            writer.writerow(row)

    _write_substrate_roles(
        dump_dir / "substrate_roles.csv",
        omega_values,
        lambda _omega, agent_id: int(agent_id),
    )

    out_path = tmp_path / "report.json"
    result = _run_substrate_analyzer(dump_dir, out_path, require_role_label_variance=True)

    assert result.returncode == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert "membership_reports" in payload
    assert set(payload["membership_reports"]) == {"omega", "compact_cluster"}
    assert payload["membership_reports"]["omega"]["g_outcome"]["pass"] is False
    assert payload["membership_reports"]["compact_cluster"]["available"] is True
    assert payload["membership_reports"]["compact_cluster"]["g_outcome"]["pass"] is True
    assert payload["compact_cluster"]["available"] is True


def test_substrate_analyzer_marks_compact_branch_unavailable_without_vectors(tmp_path):
    dump_dir = tmp_path / "dump"
    dump_dir.mkdir()
    omega_values = [0, 0, 0, 1, 1, 1]

    # Old schema: no compact_json column.
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
                "throughput_gt5_step",
                "compact_norm",
            ],
        )
        writer.writeheader()
        for step, omega in enumerate(omega_values):
            writer.writerow(
                {
                    "checkpoint": "ckpt.pt",
                    "episode": 0,
                    "step": step,
                    "omega_argmax": omega,
                    "coverage_positive_step": int(omega),
                    "zero_throughput_step": 1 - int(omega),
                    "throughput_gt5_step": int(omega),
                    "compact_norm": 0.5,
                }
            )
    _write_substrate_roles(
        dump_dir / "substrate_roles.csv",
        omega_values,
        lambda omega, agent_id: int(omega) * 3 + int(agent_id),
    )

    out_path = tmp_path / "report.json"
    result = _run_substrate_analyzer(dump_dir, out_path, require_role_label_variance=True)

    assert result.returncode == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["membership_reports"]["compact_cluster"]["available"] is False
    assert payload["compact_cluster"]["available"] is False
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_substrate_gate.py `
  -q --basetemp .pytest_tmp_r12_compact_task4_red
```

Expected:

```text
FAILED ... 'membership_reports'
```

- [ ] **Step 4: Implement compact branch parsing and membership reports**

In `scripts/analyze_r12_substrate_gate.py`, extend imports:

```python
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
```

Add helpers:

```python
def _step_key(row: dict[str, str]) -> tuple[str, int, int]:
    return (
        str(row.get("checkpoint", "")),
        _int(row, "episode"),
        _int(row, "step"),
    )


def _compact_matrix(step_rows: list[dict[str, str]]) -> tuple[np.ndarray, list[int]]:
    vectors = []
    indices = []
    expected_dim = None
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
    membership_auc = discrete_membership_auc(target, selected_memberships)
    if baseline_score is None:
        baseline = np.asarray([_float(row, "compact_norm") for row in selected_steps], dtype=np.float64)
    else:
        baseline = np.asarray(baseline_score, dtype=np.float64).reshape(-1)[: len(selected_steps)]
    if bool(membership_auc["target_valid"]):
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
    outcome_report.update(_target_stats(target, target_field))
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
```

Then rewrite `analyze()` so it builds both branches:

```python
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
```

- [ ] **Step 5: Update the positive smoke report test expected keys**

In `test_substrate_analyzer_writes_positive_smoke_report`, replace the exact key assertion with:

```python
    assert set(payload) == {
        "dump_dir",
        "rows",
        "g_dwell",
        "g_outcome",
        "g_role_validity",
        "g_role",
        "gate_pass",
        "membership_reports",
        "compact_cluster",
        "fallback_decision",
    }
    assert set(payload["membership_reports"]) == {"omega", "compact_cluster"}
```

- [ ] **Step 6: Run tests and compile analyzer**

Run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_substrate_gate.py `
  -q --basetemp .pytest_tmp_r12_compact_task4

& "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile scripts\analyze_r12_substrate_gate.py
```

Expected:

```text
passed
py_compile exits with code 0
```

---

### Task 5: Runner Compatibility and Real Re-Gate Command

**Files:**
- Modify only if needed: `scripts/run_r12_substrate_gate_local.ps1`
- Test: command-line dry-run and real local dump on available short-duration checkpoints

- [ ] **Step 1: Dry-run existing runner**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_substrate_gate_local.ps1 `
  -CheckpointDir logs\ha_ctse_process_s7s1_duration_short_reward_pure_16env_seed1_1280k `
  -LogDir logs\r12_substrate_gate_local_duration_short_16env_compact `
  -Updates 20,40,60 `
  -EvalEpisodes 4 `
  -EvalMaxSteps 500 `
  -DumpInterval 10 `
  -Device cuda `
  -DryRun
```

Expected:

```text
R12 substrate gate local runner
...
--updates 20,40,60
...
scripts\analyze_r12_substrate_gate.py
```

- [ ] **Step 2: If runner needs no change, document that in memory later**

No code change is required if dry-run prints the exporter/analyzer commands. If PowerShell exits nonzero despite successful analyzer output, fix only the native-command exit-code handling in `scripts/run_r12_substrate_gate_local.ps1`:

```powershell
& $Python @exportArgs
$exportExit = $LASTEXITCODE
if ($exportExit -ne 0) {
  Write-Error "Exporter failed with exit code $exportExit"
  exit $exportExit
}

& $Python @analyzeArgs
$analyzeExit = $LASTEXITCODE
if ($analyzeExit -ne 0) {
  Write-Error "Analyzer failed with exit code $analyzeExit"
  exit $analyzeExit
}
```

- [ ] **Step 3: Run real compact re-gate on the available 16env short checkpoint grid**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_substrate_gate_local.ps1 `
  -CheckpointDir logs\ha_ctse_process_s7s1_duration_short_reward_pure_16env_seed1_1280k `
  -LogDir logs\r12_substrate_gate_local_duration_short_16env_compact `
  -Updates 20,40,60 `
  -EvalEpisodes 4 `
  -EvalMaxSteps 500 `
  -DumpInterval 10 `
  -Device cuda
```

Expected:

```text
r12_export_selected checkpoints=3
r12_substrate_gate pass=...
```

- [ ] **Step 4: Read the compact report**

Run:

```powershell
Get-Content logs\r12_substrate_gate_local_duration_short_16env_compact\substrate_gate_report.json
```

Expected:

```text
"membership_reports": {
  "omega": ...
  "compact_cluster": ...
}
"fallback_decision": ...
```

---

### Task 6: Memory Sync

**Files:**
- Modify: `memory/ExpRecord.md`
- Modify: `memory/ATTENTION_POINTER.md`
- Modify: `memory/IMPLEMENTATION_PLAN.md`
- Modify: `memory/cross_validation.md`
- Modify only if algorithm meaning changes: `memory/ALGORITHM_PRINCIPLES.md`

- [ ] **Step 1: Update `EXP-20260702-substrate-gate` in `memory/ExpRecord.md`**

Append this result block under the experiment's `Result summary` block.  Fill
the right-hand side by copying the exact JSON values from
`substrate_gate_report.json`; do not summarize from memory:

```text
2026-07-02 compact-c fallback gate:
  - Added direct `compact_json` / `omega_json` vector export and offline
    deterministic compact clustering.
  - Re-ran available local checkpoint grid:
    `logs\ha_ctse_process_s7s1_duration_short_reward_pure_16env_seed1_1280k`,
    updates 20, 40, 60.
  - Report:
    `logs\r12_substrate_gate_local_duration_short_16env_compact\substrate_gate_report.json`
  - omega gate:
      G-DWELL = membership_reports.omega.g_dwell.pass
      G-OUTCOME = membership_reports.omega.g_outcome.pass
      G-ROLE = membership_reports.omega.g_role.pass
  - compact_cluster gate:
      available = membership_reports.compact_cluster.available
      G-DWELL = membership_reports.compact_cluster.g_dwell.pass, if available
      G-OUTCOME = membership_reports.compact_cluster.g_outcome.pass, if available
      G-ROLE = membership_reports.compact_cluster.g_role.pass, if available
  - fallback_decision = fallback_decision
```

If the actual report is negative for both omega and compact cluster, set `Next decision` to:

```text
Do not implement downstream Round 12 mechanisms.  Follow the pre-registered
fallback: one offline situation-ness encoder retrain or a hand-crafted topology
situation validation, depending on whether compact vectors show partial
structure.
```

- [ ] **Step 2: Update `memory/ATTENTION_POINTER.md`**

Add a `Last Update Notes` entry:

```text
2026-07-02 (R12 compact-c fallback gate implemented/read): Exporter now writes
full `compact_json` and `omega_json`; analyzer compares `omega` and
`compact_cluster`.  Read `fallback_decision` in
`logs\r12_substrate_gate_local_duration_short_16env_compact\substrate_gate_report.json`
before any hazard/SEF/DADS/target-situation/co-edit work.
```

Update `Active next action` according to the actual report:

```text
If compact_cluster passes:
  use compact clusters as provisional kappa and plan reward-pure
  situation-change hazard.

If compact_cluster fails but is available:
  do one offline situation-ness encoder retrain or validate hand-crafted
  topology situations before more learned-substrate work.

If compact_cluster is unavailable:
  fix export/checkpoint compatibility before drawing a conclusion.
```

- [ ] **Step 3: Update `memory/IMPLEMENTATION_PLAN.md`**

Under `Round 12 Substrate Gate`, append:

```text
R12-0e: compact-c fallback gate.
  Implemented after the first partial real gate showed omega passes G-DWELL and
  G-ROLE but fails G-OUTCOME.  The fallback exports full compact c_tau vectors,
  clusters them offline, and computes the same G-DWELL/G-OUTCOME/G-ROLE gates
  for compact_cluster.
```

- [ ] **Step 4: Update `memory/cross_validation.md`**

Add a Dialogue Log entry:

```text
### 2026-07-02 Codex follow-through: compact-c fallback gate
- Implemented the pre-registered fallback check after omega failed G-OUTCOME:
  full compact vector export, deterministic compact clustering, and side-by-side
  omega vs compact_cluster substrate reports.
- Result path:
  `logs\r12_substrate_gate_local_duration_short_16env_compact\substrate_gate_report.json`
- Decision: copy the exact `fallback_decision` value from the report.
```

- [ ] **Step 5: Run final memory consistency check**

Run:

```powershell
rg -n "compact-c fallback|compact_cluster|fallback_decision|Active next action" `
  memory\ExpRecord.md memory\ATTENTION_POINTER.md memory\IMPLEMENTATION_PLAN.md memory\cross_validation.md
```

Expected:

```text
Each memory file contains the compact fallback status or decision anchor.
```

---

## Final Verification

Run all targeted checks:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\test_r12_substrate_gate.py `
  -q --basetemp .pytest_tmp_r12_compact_verify

& "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile `
  ha_ctse_process\substrate_gate.py `
  ha_ctse_process\export_substrate_gate.py `
  scripts\analyze_r12_substrate_gate.py

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_substrate_gate_local.ps1 `
  -CheckpointDir logs\ha_ctse_process_s7s1_duration_short_reward_pure_16env_seed1_1280k `
  -LogDir logs\r12_substrate_gate_local_duration_short_16env_compact `
  -Updates 20,40,60 `
  -EvalEpisodes 4 `
  -EvalMaxSteps 500 `
  -DumpInterval 10 `
  -Device cuda `
  -DryRun
```

Expected:

```text
pytest passes.
py_compile exits code 0.
Dry-run prints exporter/analyzer commands.
```

Then run the real compact re-gate command from Task 5 Step 3 only if the machine is free.

---

## Self-Review

Spec coverage:

- The plan exports full compact `c_tau` via `compact_json`, not only `compact_norm`.
- The plan clusters compact vectors offline and compares `compact_cluster` against `omega`.
- The plan keeps the path diagnostic-only and explicitly forbids reward/hazard downstream work before the gate read.
- The plan preserves the G-ROLE all-zero trap protection.
- The plan includes memory sync and a real re-gate command using the available 16env checkpoint grid.

Placeholder scan:

- No placeholder markers or unspecified file path remains.
- Result-writing steps use JSON field paths instead of placeholders.

Type consistency:

- `compact_json` and `omega_json` are JSON array strings in `substrate_steps.csv`.
- `compact_cluster` is an integer membership array aligned to selected step rows.
- Role rows are joined to step memberships by `(checkpoint, episode, step)`.
- Existing top-level `g_dwell`, `g_outcome`, `g_role_validity`, `g_role`, and `gate_pass` remain omega-compatible for old readers.

