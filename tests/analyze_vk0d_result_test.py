"""Calibration tests for the V-K0D three-arm carrier-comparison analyzer
(scripts/analyze_vk0d_result.py).

The V-K0D drivers (launcher, training/checkpoint pipeline, conjugacy-gate
script, reference-digest reporter) do not exist yet -- exactly the situation
scripts/analyze_vk0_result.py and scripts/analyze_vk0c_result.py were
developed under. Every fixture here is synthetic, hand-built against the
frozen manifest/witness schema documented in the analyzer's own module
docstring and against A-VD-7 / A-VD-8 (docs/research/designs/
VK0D_REALIZATION_DECISION_LEDGER.md).

Two kinds of fixtures are used:

- Unit-level: a hand-built `bundle` dict fed straight into
  `compute_arm_status`, bypassing file I/O entirely -- used for the arm-
  status vocabulary and its exact LCB95/UCB95 boundary, where the only thing
  under test is the status-selection arithmetic.
- End-to-end: a real manifest.json plus the real witness/exposure/summary
  files it binds, written under a pytest tmp_path and read back through
  `run_analysis` exactly as the CLI would -- used for precedence, locality
  stamping, refusals, and determinism, where the file-loading and hashing
  machinery is itself part of the claim under test.

Each test earns its place by being able to fail: the boundary tests plant a
fixture on each side of the ruled 0.75 LCB/UCB threshold and check the status
flips; the precedence tests plant a violation of exactly one precedence
condition with everything else valid, so only that condition can be
responsible; the watched-red test mutates the analyzer's own inclusive
upper-bound comparison and shows a UCB==0.75 fixture flips from
DECISIVE_COMPETENCE_FAILURE to COMPETENCE_UNRESOLVED under the mutant while
the untouched production module still reports DECISIVE_COMPETENCE_FAILURE.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_SCRIPT_PATH = _ROOT / "scripts" / "analyze_vk0d_result.py"
_SPEC = importlib.util.spec_from_file_location("analyze_vk0d_result", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
M = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(M)

PYTHON = sys.executable
DEFAULT_SEEDS = [str(i) for i in range(1, 7)]


# =============================================================================
# Unit-level fixture builders (no file I/O)
# =============================================================================


def _stats(lcb: float, ucb: float) -> dict:
    return {"point": (lcb + ucb) / 2.0, "lower_95": lcb, "upper_95": ucb, "n": 100}


def make_competence(
    canon_slow=(0.9, 0.95),
    canon_fast=(0.9, 0.95),
    rev_slow=(0.9, 0.95),
    rev_fast=(0.9, 0.95),
) -> dict:
    return {
        "canonical": {"slow_match": _stats(*canon_slow), "fast_match": _stats(*canon_fast)},
        "reversed": {"slow_match": _stats(*rev_slow), "fast_match": _stats(*rev_fast)},
    }


def make_evaluation_summary(row: int = 4, support_pass: bool = True, competence: dict | None = None, reasons=None) -> dict:
    result: dict = {"row": row, "code": f"ROW_{row}"}
    summary: dict = {"result": result}
    if row == 1:
        result["reasons"] = reasons if reasons is not None else ["some arm-specific reason"]
    if row >= 3:
        summary["support_floor"] = {"pass": support_pass}
    if row >= 4:
        summary["competence_floor"] = competence if competence is not None else make_competence()
    return summary


def make_bundle(evaluation_summary: dict, violations=None, gate=None, seeds=None) -> dict:
    return {
        "evaluation_summary": evaluation_summary,
        "gate": gate,
        "seeds": seeds or {},
        "violations": violations or [],
    }


# =============================================================================
# Unit tests: arm-status vocabulary (A-VD-8), including exact 0.75 boundary
# =============================================================================


def test_arm_status_qualified_when_all_four_lcb_strictly_above_floor():
    bundle = make_bundle(make_evaluation_summary(row=4, competence=make_competence()))
    result = M.compute_arm_status("CONTROL", bundle)
    assert result["status"] == M.STATUS_QUALIFIED


def test_arm_status_lcb_exactly_at_boundary_is_not_qualified():
    """LCB95 == 0.75 exactly must NOT satisfy the strict '> 0.75' QUALIFIED
    rule -- and since no UCB95 is <= 0.75 anywhere, the correct label is
    COMPETENCE_UNRESOLVED, not DECISIVE_COMPETENCE_FAILURE."""
    competence = make_competence(canon_slow=(0.75, 0.9))
    bundle = make_bundle(make_evaluation_summary(row=4, competence=competence))
    result = M.compute_arm_status("CONTROL", bundle)
    assert result["status"] == M.STATUS_COMPETENCE_UNRESOLVED


def test_arm_status_ucb_exactly_at_boundary_is_decisive_failure():
    """A-VD-8's inclusive upper-bound rule: UCB95 == 0.75 is decisive, not
    merely unresolved."""
    competence = make_competence(canon_slow=(0.6, 0.75))
    bundle = make_bundle(make_evaluation_summary(row=4, competence=competence))
    result = M.compute_arm_status("CONTROL", bundle)
    assert result["status"] == M.STATUS_DECISIVE_COMPETENCE_FAILURE


def test_arm_status_unresolved_when_neither_qualified_nor_decisive():
    competence = make_competence(
        canon_slow=(0.70, 0.80), canon_fast=(0.70, 0.80), rev_slow=(0.70, 0.80), rev_fast=(0.70, 0.80)
    )
    bundle = make_bundle(make_evaluation_summary(row=4, competence=competence))
    result = M.compute_arm_status("CONTROL", bundle)
    assert result["status"] == M.STATUS_COMPETENCE_UNRESOLVED


def test_arm_status_support_insufficient_from_row_3():
    bundle = make_bundle(make_evaluation_summary(row=3, support_pass=False))
    result = M.compute_arm_status("CONTROL", bundle)
    assert result["status"] == M.STATUS_SUPPORT_INSUFFICIENT


def test_arm_status_invalid_from_accumulated_violation():
    bundle = make_bundle(
        make_evaluation_summary(row=4, competence=make_competence()),
        violations=[{"reason": "synthetic provenance defect", "locality": M.ARM_LOCAL_INVALIDITY}],
    )
    result = M.compute_arm_status("CONTROL", bundle)
    assert result["status"] == M.STATUS_INVALID
    assert "synthetic provenance defect" in result["reasons"]


def test_arm_status_row_2_folds_into_shared_invalidity_via_full_pipeline():
    """Row 2 (source urgency NOT_IDENTIFIED) is not read directly by
    compute_arm_status -- it must first pass through
    _evaluation_summary_pass_through, exercised here directly, matching how
    run_analysis actually assembles violations."""
    bundle = make_bundle(make_evaluation_summary(row=2))
    violations = M._evaluation_summary_pass_through("CONTROL", bundle)
    assert len(violations) == 1
    assert violations[0]["locality"] == M.SHARED_COMPARISON_INVALIDITY


def test_arm_status_row_1_oracle_panel_reason_is_shared_other_reasons_are_arm_local():
    bundle_shared = make_bundle(
        make_evaluation_summary(row=1, reasons=["oracle-panel verdict tuple mismatch: row_count wrong"])
    )
    bundle_local = make_bundle(
        make_evaluation_summary(row=1, reasons=["checkpoint_hash/resolved_config_hash inconsistent for seed 3"])
    )
    v_shared = M._evaluation_summary_pass_through("CONTROL", bundle_shared)
    v_local = M._evaluation_summary_pass_through("CONTROL", bundle_local)
    assert v_shared[0]["locality"] == M.SHARED_COMPARISON_INVALIDITY
    assert v_local[0]["locality"] == M.ARM_LOCAL_INVALIDITY


# =============================================================================
# End-to-end fixture builders (real files under tmp_path)
# =============================================================================


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, obj) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(obj, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(data)
    return data


def _hexdigest_for(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def make_exposure(
    n_canonical: int,
    n_reversed: int,
    total: int,
    committed: str = "digest-1",
    regenerated: str | None = None,
    stream_version: str = M.FROZEN_ORDER_STREAM_VERSION,
) -> dict:
    return {
        "stream_version": stream_version,
        "n_canonical": n_canonical,
        "n_reversed": n_reversed,
        "first_position_counts": {"agent_0": total, "agent_1": 0},
        "committed_schedule_digest": committed,
        "regenerated_schedule_digest": regenerated if regenerated is not None else committed,
        "completed_sequence_total": total,
    }


def make_gate_witness(verdict: str, checkpoint_hash: str | None = None) -> dict:
    witness = {"verdict": verdict, "config_hash": "cfg-hash-abc", "panel_inventory": {"states": 100}}
    if checkpoint_hash is not None:
        witness["checkpoint_hash"] = checkpoint_hash
    return witness


def make_reference_digest_report(
    checkpoint_hash: str,
    digests_match: bool = True,
    semantics_match: bool = True,
    exposure_match: bool = True,
    order_stream_draws_consumed: int = 0,
) -> dict:
    actor = _hexdigest_for(f"actor-{checkpoint_hash}")
    value = _hexdigest_for(f"value-{checkpoint_hash}")
    optim = _hexdigest_for(f"optim-{checkpoint_hash}")
    return {
        "checkpoint_hash": checkpoint_hash,
        "actor_state_dict_sha256": actor,
        "value_state_dict_sha256": value,
        "optimizer_state_sha256": optim,
        "vk0b_actor_state_dict_sha256": actor if digests_match else _hexdigest_for("different-actor"),
        "vk0b_value_state_dict_sha256": value,
        "vk0b_optimizer_state_sha256": optim,
        "semantics_match": semantics_match,
        "exposure_match": exposure_match,
        "order_stream_draws_consumed": order_stream_draws_consumed,
    }


def default_seed_cfg(seed_key: str, arm_name: str) -> dict:
    checkpoint_hash = f"ckpt-{arm_name}-{seed_key}"
    canonical = arm_name in M.CANONICAL_ARMS
    exposure = make_exposure(100, 0, 100) if canonical else make_exposure(50, 50, 100)
    cfg: dict = {"checkpoint_hash": checkpoint_hash, "exposure": exposure, "reference_digest_report": None}
    if arm_name == M.ARM_REFERENCE:
        cfg["reference_digest_report"] = make_reference_digest_report(checkpoint_hash)
    return cfg


def default_arm(arm_name: str, seeds: list[str] = DEFAULT_SEEDS, competence: dict | None = None) -> dict:
    high_controller, order_policy = M.FROZEN_ARM_IDENTITIES[arm_name]
    if arm_name == M.ARM_REFERENCE and competence is None:
        # A-VD-7 condition 5: canonical above 0.75, reversed decisively below.
        competence = make_competence(
            canon_slow=(0.9, 0.95), canon_fast=(0.9, 0.95), rev_slow=(0.4, 0.5), rev_fast=(0.4, 0.5)
        )
    arm: dict = {
        "arm_identity": {
            "high_controller": high_controller,
            "r30_training_order_policy": order_policy,
            "resolved_config_hash": f"resolved-{arm_name}",
        },
        "evaluation_summary": make_evaluation_summary(row=4, competence=competence),
        "gate": None,
        "seeds": {s: default_seed_cfg(s, arm_name) for s in seeds},
    }
    if arm_name == M.ARM_PRIMARY:
        arm["gate"] = {
            "pretraining": make_gate_witness(M.GATE_PASS),
            "negative": make_gate_witness(M.GATE_FAIL),
            "checkpoints": {s: make_gate_witness(M.GATE_PASS, checkpoint_hash=f"ckpt-PRIMARY-{s}") for s in seeds},
        }
    return arm


def write_manifest(tmp_path: Path, primary: dict, control: dict, reference: dict) -> Path:
    root = tmp_path
    arms_out: dict = {}
    for arm_name, arm in ((M.ARM_PRIMARY, primary), (M.ARM_CONTROL, control), (M.ARM_REFERENCE, reference)):
        arm_dir = root / "arms" / arm_name
        eval_path = arm_dir / "evaluation_summary.json"
        eval_bytes = _write(eval_path, arm["evaluation_summary"])
        entry: dict = {
            "arm_identity": arm["arm_identity"],
            "evaluation_summary_path": str(eval_path.relative_to(root)),
            "evaluation_summary_sha256": _sha256(eval_bytes),
            "gate_witness_paths": None,
            "seeds": {},
        }
        if arm["gate"] is not None:
            gate_entry: dict = {"pretraining": None, "negative": None, "checkpoints": {}}
            for slot in ("pretraining", "negative"):
                witness = arm["gate"][slot]
                if witness is None:
                    continue
                p = arm_dir / "gate" / f"{slot}.json"
                b = _write(p, witness)
                gate_entry[slot] = {"path": str(p.relative_to(root)), "sha256": _sha256(b)}
            for seed_key, witness in arm["gate"]["checkpoints"].items():
                p = arm_dir / "gate" / f"checkpoint_{seed_key}.json"
                b = _write(p, witness)
                gate_entry["checkpoints"][seed_key] = {"path": str(p.relative_to(root)), "sha256": _sha256(b)}
            entry["gate_witness_paths"] = gate_entry

        for seed_key, seed_cfg in arm["seeds"].items():
            seed_dir = arm_dir / f"seed_{seed_key}"
            exp_path = seed_dir / "exposure.json"
            exp_bytes = _write(exp_path, seed_cfg["exposure"])
            seed_entry: dict = {
                "checkpoint_hash": seed_cfg["checkpoint_hash"],
                "exposure_path": str(exp_path.relative_to(root)),
                "exposure_sha256": _sha256(exp_bytes),
                "reference_digest_report_path": None,
                "reference_digest_report_sha256": None,
            }
            if seed_cfg["reference_digest_report"] is not None:
                rp = seed_dir / "reference_digest.json"
                rb = _write(rp, seed_cfg["reference_digest_report"])
                seed_entry["reference_digest_report_path"] = str(rp.relative_to(root))
                seed_entry["reference_digest_report_sha256"] = _sha256(rb)
            entry["seeds"][seed_key] = seed_entry

        arms_out[arm_name] = entry

    manifest = {
        "contract_id": M.VK0_CONTRACT_ID,
        "vk0d_schema_version": M.VK0D_SCHEMA_VERSION,
        "arms": arms_out,
    }
    manifest_path = root / "vk0d_input_manifest.json"
    _write(manifest_path, manifest)
    return manifest_path


def default_manifest(tmp_path: Path, **overrides) -> Path:
    """overrides: optional {"PRIMARY": arm_dict, "CONTROL": arm_dict,
    "REFERENCE": arm_dict} to replace one or more default-valid arms wholesale
    before writing."""
    primary = overrides.get(M.ARM_PRIMARY, default_arm(M.ARM_PRIMARY))
    control = overrides.get(M.ARM_CONTROL, default_arm(M.ARM_CONTROL))
    reference = overrides.get(M.ARM_REFERENCE, default_arm(M.ARM_REFERENCE))
    return write_manifest(tmp_path, primary, control, reference)


# =============================================================================
# End-to-end: default manifest is a fully valid, unresolved comparison
# =============================================================================


def test_default_manifest_is_valid_and_reference_conforms(tmp_path):
    result = M.run_analysis(default_manifest(tmp_path))
    assert result["reference_conforms"] is True
    assert result["arms"][M.ARM_PRIMARY]["status"] == M.STATUS_QUALIFIED
    assert result["arms"][M.ARM_CONTROL]["status"] == M.STATUS_QUALIFIED


# =============================================================================
# Precedence branch 1: shared invalidity (launcher corruption)
# =============================================================================


def test_precedence_1_launcher_corruption_sha256_mismatch(tmp_path):
    manifest_path = default_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["arms"][M.ARM_CONTROL]["evaluation_summary_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")

    result = M.run_analysis(manifest_path)
    assert result["comparison"]["code"] == M.COMPARISON_INVALID
    assert result["comparison"]["subcode"] is None
    assert result["arms"][M.ARM_CONTROL]["status"] == M.STATUS_INVALID
    localities = {d["locality"] for d in result["arms"][M.ARM_CONTROL]["invalidity"]}
    assert M.SHARED_COMPARISON_INVALIDITY in localities


# =============================================================================
# Precedence branch 2: reference not reproduced
# =============================================================================


def test_precedence_2_reference_digest_mismatch(tmp_path):
    reference = default_arm(M.ARM_REFERENCE)
    for seed_key in reference["seeds"]:
        reference["seeds"][seed_key]["reference_digest_report"] = make_reference_digest_report(
            reference["seeds"][seed_key]["checkpoint_hash"], digests_match=False
        )
    manifest_path = default_manifest(tmp_path, **{M.ARM_REFERENCE: reference})

    result = M.run_analysis(manifest_path)
    assert result["reference_conforms"] is False
    assert result["comparison"]["code"] == M.COMPARISON_INVALID
    assert result["comparison"]["subcode"] == M.COMPARISON_REFERENCE_SUBCODE


# =============================================================================
# Shared vs arm-local stamping + precedence branch 4
# =============================================================================


def test_shared_vs_arm_local_stamping_primary_gate_fail_control_qualified(tmp_path):
    primary = default_arm(M.ARM_PRIMARY)
    primary["gate"]["pretraining"] = make_gate_witness(M.GATE_FAIL)
    manifest_path = default_manifest(tmp_path, **{M.ARM_PRIMARY: primary})

    result = M.run_analysis(manifest_path)
    assert result["arms"][M.ARM_PRIMARY]["status"] == M.STATUS_INVALID
    localities = {d["locality"] for d in result["arms"][M.ARM_PRIMARY]["invalidity"]}
    assert localities == {M.ARM_LOCAL_INVALIDITY}
    assert result["arms"][M.ARM_CONTROL]["status"] == M.STATUS_QUALIFIED
    # An arm-local PRIMARY invalidity with a validly QUALIFIED CONTROL still
    # yields precedence-4 (A-VD-8 convergence clarification), never
    # precedence-1.
    assert result["comparison"]["code"] == M.COMPARISON_CONTROL_QUALIFIED


# =============================================================================
# Precedence branch 3: support insufficient
# =============================================================================


def test_precedence_3_support_insufficient(tmp_path):
    control = default_arm(M.ARM_CONTROL)
    control["evaluation_summary"] = make_evaluation_summary(row=3, support_pass=False)
    manifest_path = default_manifest(tmp_path, **{M.ARM_CONTROL: control})

    result = M.run_analysis(manifest_path)
    assert result["arms"][M.ARM_CONTROL]["status"] == M.STATUS_SUPPORT_INSUFFICIENT
    assert result["comparison"]["code"] == M.COMPARISON_SUPPORT_INSUFFICIENT


# =============================================================================
# Precedence branch 5: structural correction required
# =============================================================================


def test_precedence_5_structural_correction_required(tmp_path):
    decisive = make_competence(rev_slow=(0.4, 0.5), rev_fast=(0.4, 0.5))
    control = default_arm(M.ARM_CONTROL, competence=decisive)
    control["evaluation_summary"] = make_evaluation_summary(row=4, competence=decisive)
    manifest_path = default_manifest(tmp_path, **{M.ARM_CONTROL: control})

    result = M.run_analysis(manifest_path)
    assert result["arms"][M.ARM_CONTROL]["status"] == M.STATUS_DECISIVE_COMPETENCE_FAILURE
    assert result["arms"][M.ARM_PRIMARY]["status"] == M.STATUS_QUALIFIED
    assert result["comparison"]["code"] == M.COMPARISON_STRUCTURAL_CORRECTION


# =============================================================================
# Precedence branch 6: autoregressive carrier reopened
# =============================================================================


def test_precedence_6_autoregressive_carrier_reopened(tmp_path):
    decisive = make_competence(rev_slow=(0.4, 0.5), rev_fast=(0.4, 0.5))
    primary = default_arm(M.ARM_PRIMARY)
    primary["evaluation_summary"] = make_evaluation_summary(row=4, competence=decisive)
    control = default_arm(M.ARM_CONTROL)
    control["evaluation_summary"] = make_evaluation_summary(row=4, competence=decisive)
    manifest_path = default_manifest(tmp_path, **{M.ARM_PRIMARY: primary, M.ARM_CONTROL: control})

    result = M.run_analysis(manifest_path)
    assert result["arms"][M.ARM_PRIMARY]["status"] == M.STATUS_DECISIVE_COMPETENCE_FAILURE
    assert result["arms"][M.ARM_CONTROL]["status"] == M.STATUS_DECISIVE_COMPETENCE_FAILURE
    assert result["comparison"]["code"] == M.COMPARISON_CARRIER_REOPENED


# =============================================================================
# Precedence branch 7: successor comparison unresolved
# (CONTROL-unresolved + PRIMARY-qualified lands in (7), never (5) -- A-VD-8)
# =============================================================================


def test_precedence_7_control_unresolved_primary_qualified_never_five(tmp_path):
    unresolved = make_competence(
        canon_slow=(0.70, 0.80), canon_fast=(0.70, 0.80), rev_slow=(0.70, 0.80), rev_fast=(0.70, 0.80)
    )
    control = default_arm(M.ARM_CONTROL)
    control["evaluation_summary"] = make_evaluation_summary(row=4, competence=unresolved)
    manifest_path = default_manifest(tmp_path, **{M.ARM_CONTROL: control})

    result = M.run_analysis(manifest_path)
    assert result["arms"][M.ARM_CONTROL]["status"] == M.STATUS_COMPETENCE_UNRESOLVED
    assert result["arms"][M.ARM_PRIMARY]["status"] == M.STATUS_QUALIFIED
    assert result["comparison"]["code"] == M.COMPARISON_UNRESOLVED
    assert result["comparison"]["code"] != M.COMPARISON_STRUCTURAL_CORRECTION


# =============================================================================
# Schedule-digest mismatch (A-VD-4)
# =============================================================================


def test_schedule_digest_mismatch_is_arm_local_invalidity(tmp_path):
    control = default_arm(M.ARM_CONTROL)
    for seed_key, cfg in control["seeds"].items():
        cfg["exposure"] = make_exposure(50, 50, 100, committed="digest-committed", regenerated="digest-regenerated")
    manifest_path = default_manifest(tmp_path, **{M.ARM_CONTROL: control})

    result = M.run_analysis(manifest_path)
    assert result["arms"][M.ARM_CONTROL]["status"] == M.STATUS_INVALID
    reasons = " ".join(result["arms"][M.ARM_CONTROL]["reasons"])
    assert "committed_schedule_digest" in reasons
    localities = {d["locality"] for d in result["arms"][M.ARM_CONTROL]["invalidity"]}
    assert localities == {M.ARM_LOCAL_INVALIDITY}
    # No shared invalidity anywhere -> precedence-1 must not fire.
    assert result["comparison"]["code"] != M.COMPARISON_INVALID


# =============================================================================
# Wrong arm-identity combination refused (no summary written)
# =============================================================================


def test_wrong_arm_identity_combination_is_refused(tmp_path):
    primary = default_arm(M.ARM_PRIMARY)
    # Swap PRIMARY's identity for CONTROL's frozen combination.
    high_controller, order_policy = M.FROZEN_ARM_IDENTITIES[M.ARM_CONTROL]
    primary["arm_identity"]["high_controller"] = high_controller
    primary["arm_identity"]["r30_training_order_policy"] = order_policy
    manifest_path = default_manifest(tmp_path, **{M.ARM_PRIMARY: primary})

    with pytest.raises(M.SchemaValidationError):
        M.run_analysis(manifest_path)


# =============================================================================
# CLI-level: determinism (byte-identical across two fresh processes) and
# recomputability (delete + rerun reproduces identical bytes)
# =============================================================================


def test_cli_determinism_and_recomputability(tmp_path):
    manifest_path = default_manifest(tmp_path)
    out1 = tmp_path / "summary_1.json"
    out2 = tmp_path / "summary_2.json"

    for out_path in (out1, out2):
        proc = subprocess.run(
            [PYTHON, str(_SCRIPT_PATH), "--manifest", str(manifest_path), "--out", str(out_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 0, proc.stderr

    assert out1.read_bytes() == out2.read_bytes()

    # Recomputability: delete and rerun, confirm byte-identical.
    out1.unlink()
    proc = subprocess.run(
        [PYTHON, str(_SCRIPT_PATH), "--manifest", str(manifest_path), "--out", str(out1)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert out1.read_bytes() == out2.read_bytes()


def test_refusal_writes_no_summary(tmp_path):
    primary = default_arm(M.ARM_PRIMARY)
    high_controller, order_policy = M.FROZEN_ARM_IDENTITIES[M.ARM_CONTROL]
    primary["arm_identity"]["high_controller"] = high_controller
    primary["arm_identity"]["r30_training_order_policy"] = order_policy
    manifest_path = default_manifest(tmp_path, **{M.ARM_PRIMARY: primary})
    out_path = tmp_path / "summary.json"

    proc = subprocess.run(
        [PYTHON, str(_SCRIPT_PATH), "--manifest", str(manifest_path), "--out", str(out_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 2
    assert not out_path.exists()


# =============================================================================
# Watched-red: mutate the inclusive upper-bound rule (<=  ->  <)
# =============================================================================


def test_watched_red_inclusive_upper_bound_rule(tmp_path):
    """The DECISIVE_COMPETENCE_FAILURE predicate must use an inclusive '<='
    against the 0.75 floor -- equality is decisive, per A-VD-8. This test
    mutates that one comparison to strict '<' in a scratch copy of the module
    and shows the UCB==0.75 fixture flips from DECISIVE_COMPETENCE_FAILURE to
    COMPETENCE_UNRESOLVED under the mutant, while the untouched production
    module still reports DECISIVE_COMPETENCE_FAILURE."""
    source = _SCRIPT_PATH.read_text(encoding="utf-8")
    needle = "any(u <= COMPETENCE_FLOOR_MIN for u in ucbs)"
    assert source.count(needle) == 1, "expected exactly one inclusive-upper-bound comparison to mutate"
    mutated_source = source.replace(needle, "any(u < COMPETENCE_FLOOR_MIN for u in ucbs)")

    mutant_path = tmp_path / "analyze_vk0d_result_mutant.py"
    mutant_path.write_text(mutated_source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("analyze_vk0d_result_mutant", mutant_path)
    assert spec is not None and spec.loader is not None
    mutant = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mutant)

    competence = make_competence(canon_slow=(0.6, 0.75))
    bundle = make_bundle(make_evaluation_summary(row=4, competence=competence))

    production_result = M.compute_arm_status("CONTROL", bundle)
    assert production_result["status"] == M.STATUS_DECISIVE_COMPETENCE_FAILURE

    mutant_bundle = make_bundle(make_evaluation_summary(row=4, competence=competence))
    mutant_result = mutant.compute_arm_status("CONTROL", mutant_bundle)
    assert mutant_result["status"] == M.STATUS_COMPETENCE_UNRESOLVED

    # Restore-and-confirm: production module (never touched on disk) still
    # reports the frozen, correct verdict.
    production_result_again = M.compute_arm_status("CONTROL", bundle)
    assert production_result_again["status"] == M.STATUS_DECISIVE_COMPETENCE_FAILURE

