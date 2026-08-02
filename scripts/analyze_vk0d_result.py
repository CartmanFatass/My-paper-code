"""Analyze the V-K0D three-arm carrier-comparison result.

Consumes exactly one durable input -- `vk0d_input_manifest.json`, which binds
by SHA-256 and path, per arm (PRIMARY, CONTROL, REFERENCE) and per scientific
seed, every witness the comparison needs -- and recomputes the whole ruled
arm-status / comparison-precedence record solely from those bound files, per:

  docs/research/designs/VK0D_REALIZATION_DECISION_LEDGER.md, amendments
  A-VD-7 (exact digest reference gate) and A-VD-8 (arm statuses, comparison
  precedence, invalidity locality).

The V-K0D drivers (the launcher, the training/checkpoint pipeline, the
conjugacy-gate script, the reference-digest reporter) do not exist yet. This
module is developed and tested against the frozen manifest/witness schema
alone, using synthetic fixtures built by its test suite -- the same house
pattern scripts/analyze_vk0_result.py and scripts/analyze_vk0c_result.py used
before their drivers existed.

The analyzer never guesses: any manifest, witness, or bound-file field that
fails the frozen schema raises SchemaValidationError, and no summary.json is
written. Missing files, unreadable JSON, and structural shape violations are
schema refusals (never a soft warning). A SHA-256 mismatch between a
manifest-declared digest and the actual bytes at that path, a gate verdict
that is not the expected one, an exposure identity that fails A-VD-4, and a
digest-equality mismatch under A-VD-7 are NOT schema refusals -- they are
legitimate, expected findings the ledger requires to surface as INVALID
status (with a SHARED_COMPARISON_INVALIDITY or ARM_LOCAL_INVALIDITY locality
tag), per A-VD-8's convergence clarification.

Manifest schema (this analyzer's own realization binding -- the ledger names
the *fields* the manifest must bind; the exact JSON nesting below is this
implementation's recorded choice, not a ruled quantity):

{
  "contract_id": "VK0_TOY_RENEWAL_URGENCY",
  "vk0d_schema_version": "vk0d-1",
  "arms": {
    "PRIMARY": {
      "arm_identity": {"high_controller": ..., "r30_training_order_policy": ...,
                        "resolved_config_hash": <nonempty str>},
      "evaluation_summary_path": <path>, "evaluation_summary_sha256": <hex>,
      "gate_witness_paths": {                         # PRIMARY only
        "pretraining": {"path": ..., "sha256": ...},
        "checkpoints": {"<seed>": {"path": ..., "sha256": ...}, ...},
        "negative": {"path": ..., "sha256": ...}
      },
      "seeds": {
        "<seed>": {
          "checkpoint_hash": <nonempty str>,
          "exposure_path": <path>, "exposure_sha256": <hex>,
          "reference_digest_report_path": null,        # non-null: REFERENCE only
          "reference_digest_report_sha256": null
        }, ...
      }
    },
    "CONTROL": { same shape, no "gate_witness_paths" },
    "REFERENCE": { same shape, no "gate_witness_paths",
                    reference_digest_report_path/sha256 populated per seed }
  }
}

Every arm's `seeds` key set must be identical (the same scientific-seed
population trains and evaluates all three arms) and exactly the frozen
six-seed count (VD-7 / "Training and evaluation scale").

A SHA-256 mismatch on any manifest-bound file is treated uniformly as
SHARED_COMPARISON_INVALIDITY under the "common launcher" bucket A-VD-8 names
-- the launcher is what stages path+hash pairs, so a byte mismatch there is a
staging-pipeline defect, not a fact about any one arm's science. Gate verdict
failures and reference-digest content mismatches are ARM_LOCAL to the arm
that carries them. This locality assignment is this analyzer's own realization
binding (recorded here and in the implementer's report), grounded directly in
A-VD-8's named examples ("common launcher" vs "PRIMARY gate/checkpoint
failure") since the ledger does not enumerate every mechanical case.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# =============================================================================
# Frozen identity and schema constants
# =============================================================================

VK0_CONTRACT_ID = "VK0_TOY_RENEWAL_URGENCY"
VK0D_SCHEMA_VERSION = "vk0d-1"

ARM_PRIMARY = "PRIMARY"
ARM_CONTROL = "CONTROL"
ARM_REFERENCE = "REFERENCE"
ARM_NAMES = (ARM_PRIMARY, ARM_CONTROL, ARM_REFERENCE)

# A-VD-3 / VD-6: the three, and only three, frozen arm identity combinations,
# keyed positionally by arm name -- PRIMARY must be exactly the conjugate
# encoder trained canonical, never any other combination.
FROZEN_ARM_IDENTITIES: dict[str, tuple[str, str]] = {
    ARM_PRIMARY: ("r30_fixed_clock_ar_edit_conjugate", "canonical"),
    ARM_CONTROL: ("r30_fixed_clock_ar_edit", "uniform_per_check"),
    ARM_REFERENCE: ("r30_fixed_clock_ar_edit", "canonical"),
}

CANONICAL_ARMS = frozenset({ARM_PRIMARY, ARM_REFERENCE})

# VD-7 / "Training and evaluation scale": six frozen scientific seeds.
FROZEN_SEED_COUNT = 6

# VD-3 / A-VD-4: the dedicated order-draw RNG stream identity.
FROZEN_ORDER_STREAM_VERSION = "vk0d-order-1"

# The V-K0B competence floor, reused unchanged (VD-4 / A-VD-8).
COMPETENCE_FLOOR_MIN = 0.75

ORDER_CANONICAL = "canonical"
ORDER_REVERSED = "reversed"
ORDER_CODES = (ORDER_CANONICAL, ORDER_REVERSED)
MATCH_KINDS = ("slow_match", "fast_match")

# A-VD-8 arm-status vocabulary.
STATUS_QUALIFIED = "QUALIFIED"
STATUS_DECISIVE_COMPETENCE_FAILURE = "DECISIVE_COMPETENCE_FAILURE"
STATUS_COMPETENCE_UNRESOLVED = "COMPETENCE_UNRESOLVED"
STATUS_SUPPORT_INSUFFICIENT = "SUPPORT_INSUFFICIENT"
STATUS_INVALID = "INVALID"

# A-VD-8 convergence clarification: invalidity locality vocabulary.
SHARED_COMPARISON_INVALIDITY = "SHARED_COMPARISON_INVALIDITY"
ARM_LOCAL_INVALIDITY = "ARM_LOCAL_INVALIDITY"

# Comparison precedence result codes (A-VD-8).
COMPARISON_INVALID = "INVALID_VK0D_CARRIER_COMPARISON"
COMPARISON_REFERENCE_SUBCODE = "CANONICAL_REFERENCE_NOT_REPRODUCED"
COMPARISON_SUPPORT_INSUFFICIENT = "VK0D_SUPPORT_INSUFFICIENT"
COMPARISON_CONTROL_QUALIFIED = "ORDER_RANDOMIZATION_COMPETENCE_QUALIFIED"
COMPARISON_STRUCTURAL_CORRECTION = "STRUCTURAL_REPRESENTATION_CORRECTION_REQUIRED"
COMPARISON_CARRIER_REOPENED = "AUTOREGRESSIVE_CARRIER_REOPENED"
COMPARISON_UNRESOLVED = "VK0D_SUCCESSOR_COMPARISON_UNRESOLVED"

GATE_PASS = "PASS"
GATE_FAIL = "FAIL"
GATE_VERDICTS = {GATE_PASS, GATE_FAIL}


class SchemaValidationError(ValueError):
    """Raised when the manifest or any file it binds violates the frozen
    V-K0D schema, or when the manifest declares an arm identity outside the
    three frozen combinations. The analyzer refuses to select a result
    rather than guess -- no summary is produced when this is raised."""


# =============================================================================
# Small type predicates
# =============================================================================


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_nonneg_int(value: Any) -> bool:
    return _is_int(value) and value >= 0


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _is_sha256_hex(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float))


# =============================================================================
# I/O
# =============================================================================


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise SchemaValidationError(f"{label}: cannot read {path} ({exc})") from exc


def _load_json_bytes(data: bytes, label: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(f"{label}: invalid JSON ({exc})") from exc


def _load_json_file(path: Path, label: str) -> Any:
    return _load_json_bytes(_read_bytes(path, label), label)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _git_blob_sha1(path: Path) -> str:
    """The exact `git hash-object` algorithm, computed without invoking git
    (subagents never run Git; this replicates the hashing scheme in-process
    against the analyzer's own source bytes)."""
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def _verify_bound_file(
    root: Path, path_field: Any, sha_field: Any, label: str
) -> tuple[bytes, list[dict[str, Any]]]:
    """Loads a manifest-bound file's raw bytes and checks them against the
    manifest's declared SHA-256. A missing/unreadable file or a malformed
    path/hash field is a schema refusal (SchemaValidationError). A hash
    MISMATCH -- the file exists and reads fine, but its bytes are not what
    the manifest committed to -- is a legitimate finding, not a refusal:
    returned as one SHARED_COMPARISON_INVALIDITY reason (the "common
    launcher" bucket, A-VD-8), so the caller can fold it into the arm's
    invalid reasons and still keep processing the rest of the manifest."""
    if not _is_nonempty_str(path_field):
        raise SchemaValidationError(f"{label}: path must be a non-empty str")
    if not _is_sha256_hex(sha_field):
        raise SchemaValidationError(f"{label}: sha256 must be a 64-hex-char str")
    data = _read_bytes(root / path_field, label)
    actual = _sha256_bytes(data)
    violations: list[dict[str, Any]] = []
    if actual != sha_field:
        violations.append(
            {
                "reason": (
                    f"{label}: SHA-256 mismatch -- manifest declares {sha_field} but "
                    f"{path_field} actually hashes to {actual} (common-launcher file binding)"
                ),
                "locality": SHARED_COMPARISON_INVALIDITY,
            }
        )
    return data, violations


# =============================================================================
# Manifest structural validation
# =============================================================================


def validate_manifest_shape(manifest: dict[str, Any]) -> list[str]:
    """Structural validation only (types/keys/shape). Content-level findings
    (SHA-256 mismatches, gate/reference/exposure violations) are computed
    later, once the bound files are loaded, and never raised here."""
    errors: list[str] = []
    if manifest.get("contract_id") != VK0_CONTRACT_ID:
        errors.append("manifest.contract_id must equal the frozen VK0 contract id")
    if manifest.get("vk0d_schema_version") != VK0D_SCHEMA_VERSION:
        errors.append(f"manifest.vk0d_schema_version must equal {VK0D_SCHEMA_VERSION!r}")

    arms = manifest.get("arms")
    if not isinstance(arms, dict) or set(arms.keys()) != set(ARM_NAMES):
        errors.append(f"manifest.arms must be a dict with exactly the keys {sorted(ARM_NAMES)}")
        return errors

    seed_key_sets: dict[str, set[str]] = {}
    for arm_name in ARM_NAMES:
        arm = arms.get(arm_name)
        if not isinstance(arm, dict):
            errors.append(f"manifest.arms.{arm_name} must be a dict")
            continue

        identity = arm.get("arm_identity")
        if not isinstance(identity, dict):
            errors.append(f"manifest.arms.{arm_name}.arm_identity must be a dict")
        else:
            if not _is_nonempty_str(identity.get("high_controller")):
                errors.append(f"manifest.arms.{arm_name}.arm_identity.high_controller must be a non-empty str")
            if not _is_nonempty_str(identity.get("r30_training_order_policy")):
                errors.append(
                    f"manifest.arms.{arm_name}.arm_identity.r30_training_order_policy must be a non-empty str"
                )
            if not _is_nonempty_str(identity.get("resolved_config_hash")):
                errors.append(f"manifest.arms.{arm_name}.arm_identity.resolved_config_hash must be a non-empty str")

        if not _is_nonempty_str(arm.get("evaluation_summary_path")):
            errors.append(f"manifest.arms.{arm_name}.evaluation_summary_path must be a non-empty str")
        if not _is_sha256_hex(arm.get("evaluation_summary_sha256")):
            errors.append(f"manifest.arms.{arm_name}.evaluation_summary_sha256 must be a 64-hex-char str")

        gate = arm.get("gate_witness_paths")
        if arm_name == ARM_PRIMARY:
            if gate is not None and not isinstance(gate, dict):
                errors.append(f"manifest.arms.{arm_name}.gate_witness_paths must be a dict or null when present")
        else:
            if gate is not None:
                errors.append(f"manifest.arms.{arm_name}.gate_witness_paths must be absent/null (PRIMARY only)")

        seeds = arm.get("seeds")
        if not isinstance(seeds, dict) or not seeds:
            errors.append(f"manifest.arms.{arm_name}.seeds must be a non-empty dict keyed by seed")
            continue
        seed_key_sets[arm_name] = set(seeds.keys())
        for seed_key, entry in seeds.items():
            tag = f"manifest.arms.{arm_name}.seeds[{seed_key}]"
            if not isinstance(entry, dict):
                errors.append(f"{tag} must be a dict")
                continue
            if not _is_nonempty_str(entry.get("checkpoint_hash")):
                errors.append(f"{tag}.checkpoint_hash must be a non-empty str")
            if not _is_nonempty_str(entry.get("exposure_path")):
                errors.append(f"{tag}.exposure_path must be a non-empty str")
            if not _is_sha256_hex(entry.get("exposure_sha256")):
                errors.append(f"{tag}.exposure_sha256 must be a 64-hex-char str")

            ref_path = entry.get("reference_digest_report_path")
            ref_sha = entry.get("reference_digest_report_sha256")
            if arm_name == ARM_REFERENCE:
                if not _is_nonempty_str(ref_path) or not _is_sha256_hex(ref_sha):
                    errors.append(
                        f"{tag}.reference_digest_report_path/sha256 must be present and well-formed for REFERENCE"
                    )
            else:
                if ref_path is not None or ref_sha is not None:
                    errors.append(f"{tag}.reference_digest_report_path/sha256 must be null (REFERENCE only)")

    if len(seed_key_sets) == len(ARM_NAMES):
        seed_sets = list(seed_key_sets.values())
        if any(s != seed_sets[0] for s in seed_sets[1:]):
            errors.append("manifest.arms.*.seeds key sets must be identical across all three arms")
        elif len(seed_sets[0]) != FROZEN_SEED_COUNT:
            errors.append(f"manifest.arms.*.seeds must carry exactly {FROZEN_SEED_COUNT} seed(s)")

    return errors


def _check_frozen_arm_identities(manifest: dict[str, Any]) -> list[str]:
    """A-VD-3 / VD-6: the analyzer REFUSES any arm_identity combination other
    than the one frozen combination for that named arm slot."""
    errors: list[str] = []
    arms = manifest.get("arms")
    if not isinstance(arms, dict):
        return errors
    for arm_name in ARM_NAMES:
        arm = arms.get(arm_name)
        if not isinstance(arm, dict):
            continue
        identity = arm.get("arm_identity")
        if not isinstance(identity, dict):
            continue
        actual = (identity.get("high_controller"), identity.get("r30_training_order_policy"))
        expected = FROZEN_ARM_IDENTITIES[arm_name]
        if actual != expected:
            errors.append(
                f"manifest.arms.{arm_name}.arm_identity is {actual!r}, not the frozen "
                f"combination {expected!r} for this arm slot -- refused"
            )
    return errors


# =============================================================================
# Gate witness structural validation (PRIMARY only)
# =============================================================================


def validate_gate_witness_shape(witness: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(witness, dict):
        return [f"{label} must be a dict"]
    if witness.get("verdict") not in GATE_VERDICTS:
        errors.append(f"{label}.verdict must be PASS or FAIL")
    if not _is_nonempty_str(witness.get("config_hash")):
        errors.append(f"{label}.config_hash must be a non-empty str")
    panel_inventory = witness.get("panel_inventory")
    if not isinstance(panel_inventory, (dict, list)) or not panel_inventory:
        errors.append(f"{label}.panel_inventory must be a non-empty dict or list")
    if "checkpoint_hash" in witness and not _is_nonempty_str(witness.get("checkpoint_hash")):
        errors.append(f"{label}.checkpoint_hash must be a non-empty str when present")
    return errors


# =============================================================================
# Reference digest report structural validation (REFERENCE only)
# =============================================================================

_REFERENCE_DIGEST_FIELDS = (
    "actor_state_dict_sha256",
    "value_state_dict_sha256",
    "optimizer_state_sha256",
    "vk0b_actor_state_dict_sha256",
    "vk0b_value_state_dict_sha256",
    "vk0b_optimizer_state_sha256",
)


def validate_reference_digest_report_shape(report: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return [f"{label} must be a dict"]
    for field in _REFERENCE_DIGEST_FIELDS:
        if not _is_sha256_hex(report.get(field)):
            errors.append(f"{label}.{field} must be a 64-hex-char SHA-256 str")
    if not _is_bool(report.get("semantics_match")):
        errors.append(f"{label}.semantics_match must be a bool")
    if not _is_bool(report.get("exposure_match")):
        errors.append(f"{label}.exposure_match must be a bool")
    if not _is_nonneg_int(report.get("order_stream_draws_consumed")):
        errors.append(f"{label}.order_stream_draws_consumed must be a non-negative int")
    if not _is_nonempty_str(report.get("checkpoint_hash")):
        errors.append(f"{label}.checkpoint_hash must be a non-empty str")
    return errors


# =============================================================================
# Order-exposure block structural validation (A-VD-4, all arms)
# =============================================================================


def validate_exposure_block_shape(block: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(block, dict):
        return [f"{label} must be a dict"]
    if not _is_nonempty_str(block.get("stream_version")):
        errors.append(f"{label}.stream_version must be a non-empty str")
    if not _is_nonneg_int(block.get("n_canonical")):
        errors.append(f"{label}.n_canonical must be a non-negative int")
    if not _is_nonneg_int(block.get("n_reversed")):
        errors.append(f"{label}.n_reversed must be a non-negative int")
    first_pos = block.get("first_position_counts")
    if (
        not isinstance(first_pos, dict)
        or set(first_pos.keys()) != {"agent_0", "agent_1"}
        or not all(_is_nonneg_int(v) for v in first_pos.values())
    ):
        errors.append(f"{label}.first_position_counts must be a {{'agent_0','agent_1'}} non-negative int pair")
    if not _is_nonempty_str(block.get("committed_schedule_digest")):
        errors.append(f"{label}.committed_schedule_digest must be a non-empty str")
    if not _is_nonempty_str(block.get("regenerated_schedule_digest")):
        errors.append(f"{label}.regenerated_schedule_digest must be a non-empty str")
    if not _is_nonneg_int(block.get("completed_sequence_total")):
        errors.append(f"{label}.completed_sequence_total must be a non-negative int")
    return errors


# =============================================================================
# Evaluation summary structural validation (the bound V-K0B summary.json)
# =============================================================================


def validate_evaluation_summary_shape(summary: Any, label: str) -> list[str]:
    """Validates only the fields this analyzer actually consumes from the
    frozen V-K0B analyzer's own output schema (scripts/analyze_vk0_result.py
    `run_analysis`): `result.row`, and -- present only once the underlying
    V-K0B row reached that stage -- `support_floor.pass` (row >= 3) and
    `competence_floor[order][match]{lower_95,upper_95}` (row >= 4). Rows 1
    and 2 legitimately carry neither field (the V-K0B analyzer returns
    before computing them), so their absence there is not a violation."""
    errors: list[str] = []
    if not isinstance(summary, dict):
        return [f"{label} must be a dict"]
    result = summary.get("result")
    if not isinstance(result, dict) or not _is_int(result.get("row")) or not (1 <= result.get("row", 0) <= 8):
        errors.append(f"{label}.result.row must be an int in [1, 8]")
        return errors
    row = result["row"]
    if row == 1 and not isinstance(result.get("reasons"), list):
        errors.append(f"{label}.result.reasons must be a list when result.row == 1")

    if row >= 3:
        support = summary.get("support_floor")
        if not isinstance(support, dict) or not _is_bool(support.get("pass")):
            errors.append(f"{label}.support_floor.pass must be a bool when result.row >= 3")

    if row >= 4:
        competence = summary.get("competence_floor")
        if not isinstance(competence, dict):
            errors.append(f"{label}.competence_floor must be a dict when result.row >= 4")
        else:
            for order in ORDER_CODES:
                per_order = competence.get(order)
                if not isinstance(per_order, dict):
                    errors.append(f"{label}.competence_floor.{order} must be a dict")
                    continue
                for match in MATCH_KINDS:
                    stats = per_order.get(match)
                    if (
                        not isinstance(stats, dict)
                        or not _is_finite_number(stats.get("lower_95"))
                        or not _is_finite_number(stats.get("upper_95"))
                    ):
                        errors.append(
                            f"{label}.competence_floor.{order}.{match} must carry finite lower_95/upper_95"
                        )
    return errors


# =============================================================================
# Loading one arm's full bundle
# =============================================================================


def load_arm_bundle(root: Path, arm_name: str, arm_manifest: dict[str, Any]) -> dict[str, Any]:
    """Loads and structurally validates every file one arm's manifest entry
    binds, verifying each SHA-256 along the way. Returns a bundle carrying
    the loaded JSON plus an accumulated `violations` list of
    {"reason", "locality"} dicts for content-level findings (hash mismatches,
    gate verdict failures, exposure identity failures, checkpoint-hash
    cross-references) -- never raised, since these are legitimate results,
    not malformed input."""
    violations: list[dict[str, Any]] = []

    eval_data, eval_violations = _verify_bound_file(
        root,
        arm_manifest.get("evaluation_summary_path"),
        arm_manifest.get("evaluation_summary_sha256"),
        f"arms.{arm_name}.evaluation_summary",
    )
    violations.extend(eval_violations)
    evaluation_summary = _load_json_bytes(eval_data, f"arms.{arm_name}.evaluation_summary")
    shape_errors = validate_evaluation_summary_shape(evaluation_summary, f"arms.{arm_name}.evaluation_summary")
    if shape_errors:
        raise SchemaValidationError("; ".join(shape_errors))

    gate_bundle: dict[str, Any] | None = None
    if arm_name == ARM_PRIMARY:
        gate_paths = arm_manifest.get("gate_witness_paths")
        gate_bundle = {"pretraining": None, "checkpoints": {}, "negative": None}
        if gate_paths is None:
            violations.append(
                {
                    "reason": "PRIMARY gate_witness_paths absent -- the pre-training conjugacy gate was never run",
                    "locality": ARM_LOCAL_INVALIDITY,
                }
            )
        else:
            for slot in ("pretraining", "negative"):
                entry = gate_paths.get(slot)
                if entry is None:
                    violations.append(
                        {
                            "reason": f"PRIMARY gate_witness_paths.{slot} absent -- gate witness never established",
                            "locality": ARM_LOCAL_INVALIDITY,
                        }
                    )
                    continue
                data, v = _verify_bound_file(root, entry.get("path"), entry.get("sha256"), f"gate.{slot}")
                violations.extend(v)
                witness = _load_json_bytes(data, f"gate.{slot}")
                shape = validate_gate_witness_shape(witness, f"gate.{slot}")
                if shape:
                    raise SchemaValidationError("; ".join(shape))
                gate_bundle[slot] = witness

            checkpoints = gate_paths.get("checkpoints")
            if not isinstance(checkpoints, dict):
                raise SchemaValidationError("gate.checkpoints must be a dict keyed by seed")
            seeds_map = arm_manifest.get("seeds", {})
            for seed_key in sorted(seeds_map.keys()):
                entry = checkpoints.get(seed_key)
                if entry is None:
                    violations.append(
                        {
                            "reason": (
                                f"PRIMARY gate.checkpoints[{seed_key}] absent -- the conjugacy gate "
                                "was never rerun on this trained checkpoint"
                            ),
                            "locality": ARM_LOCAL_INVALIDITY,
                        }
                    )
                    continue
                data, v = _verify_bound_file(
                    root, entry.get("path"), entry.get("sha256"), f"gate.checkpoints[{seed_key}]"
                )
                violations.extend(v)
                witness = _load_json_bytes(data, f"gate.checkpoints[{seed_key}]")
                shape = validate_gate_witness_shape(witness, f"gate.checkpoints[{seed_key}]")
                if shape:
                    raise SchemaValidationError("; ".join(shape))
                gate_bundle["checkpoints"][seed_key] = witness

    per_seed: dict[str, dict[str, Any]] = {}
    seeds_map = arm_manifest.get("seeds", {})
    for seed_key in sorted(seeds_map.keys()):
        seed_entry = seeds_map[seed_key]
        seed_bundle: dict[str, Any] = {"checkpoint_hash": seed_entry.get("checkpoint_hash")}

        data, v = _verify_bound_file(
            root, seed_entry.get("exposure_path"), seed_entry.get("exposure_sha256"), f"exposure[{seed_key}]"
        )
        violations.extend(v)
        exposure = _load_json_bytes(data, f"exposure[{seed_key}]")
        shape = validate_exposure_block_shape(exposure, f"exposure[{seed_key}]")
        if shape:
            raise SchemaValidationError("; ".join(shape))
        seed_bundle["exposure"] = exposure

        if arm_name == ARM_REFERENCE:
            data, v = _verify_bound_file(
                root,
                seed_entry.get("reference_digest_report_path"),
                seed_entry.get("reference_digest_report_sha256"),
                f"reference_digest[{seed_key}]",
            )
            violations.extend(v)
            report = _load_json_bytes(data, f"reference_digest[{seed_key}]")
            shape = validate_reference_digest_report_shape(report, f"reference_digest[{seed_key}]")
            if shape:
                raise SchemaValidationError("; ".join(shape))
            seed_bundle["reference_digest_report"] = report

        per_seed[seed_key] = seed_bundle

    return {
        "arm_name": arm_name,
        "evaluation_summary": evaluation_summary,
        "gate": gate_bundle,
        "seeds": per_seed,
        "violations": violations,
    }


# =============================================================================
# Content-level violation checks
# =============================================================================


def _gate_violations(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """A-VD-5: pretraining PASS, every trained-checkpoint rerun PASS, and the
    deliberate negative witness FAIL. Any deviation is arm-local invalidity
    for PRIMARY -- "a trained-checkpoint conjugacy gate failure is arm-local
    invalidity for PRIMARY, not a competence result" (A-VD-8)."""
    gate = bundle["gate"]
    if gate is None:
        return []
    out: list[dict[str, Any]] = []
    pretraining = gate.get("pretraining")
    if pretraining is not None and pretraining.get("verdict") != GATE_PASS:
        out.append(
            {"reason": "PRIMARY pre-training conjugacy gate verdict is FAIL", "locality": ARM_LOCAL_INVALIDITY}
        )
    for seed_key, witness in sorted(gate.get("checkpoints", {}).items()):
        if witness.get("verdict") != GATE_PASS:
            out.append(
                {
                    "reason": f"PRIMARY conjugacy gate rerun on checkpoint seed {seed_key} verdict is FAIL",
                    "locality": ARM_LOCAL_INVALIDITY,
                }
            )
    negative = gate.get("negative")
    if negative is not None and negative.get("verdict") != GATE_FAIL:
        out.append(
            {
                "reason": (
                    "PRIMARY deliberate negative conjugacy witness did not FAIL "
                    f"(verdict={negative.get('verdict')!r}) -- the gate failed to reject a known-bad encoder"
                ),
                "locality": ARM_LOCAL_INVALIDITY,
            }
        )
    return out


def _checkpoint_hash_violations(arm_name: str, bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """"checkpoint" locality category: cross-references the manifest's
    declared per-seed checkpoint_hash against every artifact that echoes
    one (PRIMARY gate-checkpoint witnesses, REFERENCE digest reports)."""
    out: list[dict[str, Any]] = []
    if arm_name == ARM_PRIMARY and bundle["gate"] is not None:
        for seed_key, witness in sorted(bundle["gate"].get("checkpoints", {}).items()):
            declared = bundle["seeds"].get(seed_key, {}).get("checkpoint_hash")
            witnessed = witness.get("checkpoint_hash")
            if witnessed is not None and witnessed != declared:
                out.append(
                    {
                        "reason": (
                            f"PRIMARY gate checkpoint witness for seed {seed_key} carries checkpoint_hash "
                            f"{witnessed!r}, inconsistent with the manifest's {declared!r}"
                        ),
                        "locality": ARM_LOCAL_INVALIDITY,
                    }
                )
    if arm_name == ARM_REFERENCE:
        for seed_key, seed_bundle in sorted(bundle["seeds"].items()):
            report = seed_bundle.get("reference_digest_report")
            declared = seed_bundle.get("checkpoint_hash")
            if report is not None and report.get("checkpoint_hash") != declared:
                out.append(
                    {
                        "reason": (
                            f"REFERENCE digest report for seed {seed_key} carries checkpoint_hash "
                            f"{report.get('checkpoint_hash')!r}, inconsistent with the manifest's {declared!r}"
                        ),
                        "locality": ARM_LOCAL_INVALIDITY,
                    }
                )
    return out


def _exposure_violations(arm_name: str, bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """A-VD-4 order-exposure identities. Stream-version drift is tagged
    SHARED (the "shared exposure instrumentation" bucket, A-VD-8); the
    per-arm-seed count/digest identities are ARM_LOCAL to that arm."""
    out: list[dict[str, Any]] = []
    for seed_key, seed_bundle in sorted(bundle["seeds"].items()):
        exposure = seed_bundle["exposure"]
        tag = f"{arm_name} seed {seed_key} exposure"
        if exposure["stream_version"] != FROZEN_ORDER_STREAM_VERSION:
            out.append(
                {
                    "reason": (
                        f"{tag}: stream_version {exposure['stream_version']!r} != frozen "
                        f"{FROZEN_ORDER_STREAM_VERSION!r}"
                    ),
                    "locality": SHARED_COMPARISON_INVALIDITY,
                }
            )
        n_canonical = exposure["n_canonical"]
        n_reversed = exposure["n_reversed"]
        total = exposure["completed_sequence_total"]
        if n_canonical + n_reversed != total:
            out.append(
                {
                    "reason": f"{tag}: N_canonical+N_reversed ({n_canonical}+{n_reversed}) != completed_sequence_total ({total})",
                    "locality": ARM_LOCAL_INVALIDITY,
                }
            )
        if arm_name in CANONICAL_ARMS:
            if n_reversed != 0:
                out.append(
                    {"reason": f"{tag}: N_reversed={n_reversed} != 0 for a canonical-serialization arm", "locality": ARM_LOCAL_INVALIDITY}
                )
            if n_canonical != total:
                out.append(
                    {
                        "reason": f"{tag}: N_canonical ({n_canonical}) != completed_sequence_total ({total})",
                        "locality": ARM_LOCAL_INVALIDITY,
                    }
                )
        if exposure["committed_schedule_digest"] != exposure["regenerated_schedule_digest"]:
            out.append(
                {
                    "reason": (
                        f"{tag}: committed_schedule_digest {exposure['committed_schedule_digest']!r} != "
                        f"independently regenerated {exposure['regenerated_schedule_digest']!r}"
                    ),
                    "locality": ARM_LOCAL_INVALIDITY,
                }
            )
    return out


def _evaluation_summary_pass_through(arm_name: str, bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Folds an underlying V-K0B row-1/row-2 finding into V-K0D locality.
    Row 2 (source urgency NOT_IDENTIFIED) is about the shared V-K0A panel/
    evaluation bank every arm's V-K0B run reads identically -- SHARED. Row 1
    findings that explicitly implicate the shared oracle-panel authorization
    tuple are SHARED for the same reason; every other row-1 finding (replay
    conformance, checkpoint-hash consistency, per-seed exposure counts) is a
    fact about that one arm's own V-K0B trace and is ARM_LOCAL."""
    summary = bundle["evaluation_summary"]
    row = summary["result"]["row"]
    out: list[dict[str, Any]] = []
    if row == 2:
        out.append(
            {
                "reason": f"{arm_name} evaluation_summary reports V-K0B row 2 (source urgency NOT_IDENTIFIED)",
                "locality": SHARED_COMPARISON_INVALIDITY,
            }
        )
    elif row == 1:
        reasons = summary["result"].get("reasons") or []
        for r in reasons:
            locality = SHARED_COMPARISON_INVALIDITY if "oracle-panel" in str(r) else ARM_LOCAL_INVALIDITY
            out.append({"reason": f"{arm_name} evaluation_summary row 1: {r}", "locality": locality})
        if not reasons:
            out.append(
                {
                    "reason": f"{arm_name} evaluation_summary reports V-K0B row 1 with no reasons recorded",
                    "locality": ARM_LOCAL_INVALIDITY,
                }
            )
    return out


def compute_reference_conforms(bundle: dict[str, Any]) -> tuple[bool, list[str]]:
    """A-VD-7: REFERENCE_CONFORMS iff all five conditions hold for every
    scientific seed. Conditions 1-4 are per-seed (digest equality, semantics/
    exposure match, zero order-stream consumption); condition 5 (canonical
    competence above 0.75, reversed decisively below) is evaluated once at
    the arm level, since the bound evaluation_summary is a single pooled
    result over all seeds -- there is no per-seed competence quantity to
    read (recorded realization binding: the only computable reading of a
    per-seed clause applied to an inherently pooled statistic)."""
    mismatches: list[str] = []
    for seed_key, seed_bundle in sorted(bundle["seeds"].items()):
        report = seed_bundle["reference_digest_report"]
        for own_field, vk0b_field, label in (
            ("actor_state_dict_sha256", "vk0b_actor_state_dict_sha256", "high-actor state_dict"),
            ("value_state_dict_sha256", "vk0b_value_state_dict_sha256", "high-value state_dict"),
            ("optimizer_state_sha256", "vk0b_optimizer_state_sha256", "shared high-optimizer state"),
        ):
            if report[own_field] != report[vk0b_field]:
                mismatches.append(f"seed {seed_key}: {label} SHA-256 does not equal the valid V-K0B digest")
        if not report["semantics_match"]:
            mismatches.append(f"seed {seed_key}: resolved training semantics do not match")
        if not report["exposure_match"]:
            mismatches.append(f"seed {seed_key}: actual exposure does not match")
        if report["order_stream_draws_consumed"] != 0:
            mismatches.append(
                f"seed {seed_key}: canonical path consumed "
                f"{report['order_stream_draws_consumed']} order-stream draw(s), expected 0"
            )

    summary = bundle["evaluation_summary"]
    row = summary["result"]["row"]
    if row < 4:
        mismatches.append(f"evaluation_summary did not reach V-K0B row 4 (row={row}); competence unreadable")
    else:
        competence = summary["competence_floor"]
        canonical_above = (
            competence[ORDER_CANONICAL]["slow_match"]["lower_95"] > COMPETENCE_FLOOR_MIN
            and competence[ORDER_CANONICAL]["fast_match"]["lower_95"] > COMPETENCE_FLOOR_MIN
        )
        reversed_below = (
            competence[ORDER_REVERSED]["slow_match"]["upper_95"] <= COMPETENCE_FLOOR_MIN
            and competence[ORDER_REVERSED]["fast_match"]["upper_95"] <= COMPETENCE_FLOOR_MIN
        )
        if not canonical_above:
            mismatches.append("evaluation_summary does not reproduce canonical competence above 0.75")
        if not reversed_below:
            mismatches.append("evaluation_summary does not reproduce reversed competence decisively below 0.75")

    return (not mismatches, mismatches)


# =============================================================================
# Arm status (A-VD-8)
# =============================================================================


def compute_arm_status(arm_name: str, bundle: dict[str, Any]) -> dict[str, Any]:
    violations = list(bundle["violations"])
    violations.extend(_gate_violations(bundle))
    violations.extend(_checkpoint_hash_violations(arm_name, bundle))
    violations.extend(_exposure_violations(arm_name, bundle))
    violations.extend(_evaluation_summary_pass_through(arm_name, bundle))

    if arm_name == ARM_REFERENCE:
        conforms, mismatches = compute_reference_conforms(bundle)
        if not conforms:
            for m in mismatches:
                violations.append({"reason": f"REFERENCE reference-reproduction: {m}", "locality": ARM_LOCAL_INVALIDITY})

    summary = bundle["evaluation_summary"]
    row = summary["result"]["row"]

    if violations:
        return {
            "status": STATUS_INVALID,
            "reasons": [v["reason"] for v in violations],
            "localities": violations,
            "competence": None,
        }

    if row < 3:
        # Unreachable once evaluation_summary pass-through is folded in above
        # (row 1/2 always produce at least one violation), kept as a
        # fail-closed guard rather than trusting the invariant silently.
        return {
            "status": STATUS_INVALID,
            "reasons": [f"evaluation_summary row {row} is neither row 1 nor row 2 nor >= 3"],
            "localities": [{"reason": f"unexpected row {row}", "locality": ARM_LOCAL_INVALIDITY}],
            "competence": None,
        }

    if not summary["support_floor"]["pass"] or row == 3:
        return {"status": STATUS_SUPPORT_INSUFFICIENT, "reasons": [], "localities": [], "competence": None}

    competence = summary["competence_floor"]
    lcbs = [competence[o][m]["lower_95"] for o in ORDER_CODES for m in MATCH_KINDS]
    ucbs = [competence[o][m]["upper_95"] for o in ORDER_CODES for m in MATCH_KINDS]
    if all(l > COMPETENCE_FLOOR_MIN for l in lcbs):
        status = STATUS_QUALIFIED
    elif any(u <= COMPETENCE_FLOOR_MIN for u in ucbs):
        status = STATUS_DECISIVE_COMPETENCE_FAILURE
    else:
        status = STATUS_COMPETENCE_UNRESOLVED

    return {"status": status, "reasons": [], "localities": [], "competence": competence}


# =============================================================================
# Comparison precedence (A-VD-8)
# =============================================================================


def determine_comparison(
    arm_results: dict[str, dict[str, Any]], reference_conforms: bool
) -> dict[str, Any]:
    all_localities = [
        loc for arm in ARM_NAMES for loc in arm_results[arm]["localities"]
    ]
    any_shared = any(loc["locality"] == SHARED_COMPARISON_INVALIDITY for loc in all_localities)

    if any_shared:
        return {"code": COMPARISON_INVALID, "subcode": None, "row": 1}
    if not reference_conforms:
        return {"code": COMPARISON_INVALID, "subcode": COMPARISON_REFERENCE_SUBCODE, "row": 2}

    primary_status = arm_results[ARM_PRIMARY]["status"]
    control_status = arm_results[ARM_CONTROL]["status"]

    if primary_status == STATUS_SUPPORT_INSUFFICIENT or control_status == STATUS_SUPPORT_INSUFFICIENT:
        return {"code": COMPARISON_SUPPORT_INSUFFICIENT, "subcode": None, "row": 3}
    if control_status == STATUS_QUALIFIED:
        return {"code": COMPARISON_CONTROL_QUALIFIED, "subcode": None, "row": 4}
    if control_status == STATUS_DECISIVE_COMPETENCE_FAILURE and primary_status == STATUS_QUALIFIED:
        return {"code": COMPARISON_STRUCTURAL_CORRECTION, "subcode": None, "row": 5}
    if control_status == STATUS_DECISIVE_COMPETENCE_FAILURE and primary_status == STATUS_DECISIVE_COMPETENCE_FAILURE:
        return {"code": COMPARISON_CARRIER_REOPENED, "subcode": None, "row": 6}
    return {"code": COMPARISON_UNRESOLVED, "subcode": None, "row": 7}


# =============================================================================
# Top-level analysis
# =============================================================================


def run_analysis(manifest_path: str | Path) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    manifest = _load_json_file(manifest_path, "manifest")

    shape_errors = validate_manifest_shape(manifest)
    if shape_errors:
        raise SchemaValidationError("; ".join(shape_errors))
    identity_errors = _check_frozen_arm_identities(manifest)
    if identity_errors:
        raise SchemaValidationError("; ".join(identity_errors))

    root = manifest_path.parent
    bundles = {arm: load_arm_bundle(root, arm, manifest["arms"][arm]) for arm in ARM_NAMES}

    arm_results = {arm: compute_arm_status(arm, bundles[arm]) for arm in ARM_NAMES}
    reference_conforms, reference_mismatches = compute_reference_conforms(bundles[ARM_REFERENCE])
    comparison = determine_comparison(arm_results, reference_conforms)

    result: dict[str, Any] = {
        "contract_id": VK0_CONTRACT_ID,
        "vk0d_schema_version": VK0D_SCHEMA_VERSION,
        "analyzer_git_blob_sha1": _git_blob_sha1(Path(__file__)),
        "arms": {
            arm: {
                "status": arm_results[arm]["status"],
                "reasons": sorted(arm_results[arm]["reasons"]),
                "invalidity": sorted(
                    (
                        {"reason": v["reason"], "locality": v["locality"]}
                        for v in arm_results[arm]["localities"]
                    ),
                    key=lambda d: d["reason"],
                ),
                "competence_floor": arm_results[arm]["competence"],
            }
            for arm in ARM_NAMES
        },
        "reference_conforms": bool(reference_conforms),
        "reference_conformance_reasons": sorted(reference_mismatches),
        "comparison": comparison,
    }
    return result


# =============================================================================
# CLI
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze the V-K0D three-arm carrier-comparison result.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    try:
        summary = run_analysis(args.manifest)
    except SchemaValidationError as exc:
        print(f"VK0D analyzer refuses -- frozen schema violation: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    _write_json(Path(args.out), summary)
    print(
        f"VK0D analysis completed comparison={summary['comparison']['code']} output={args.out}",
        flush=True,
    )


if __name__ == "__main__":
    main()
