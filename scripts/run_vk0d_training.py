"""V-K0D three-arm training launcher: arm identity, A-VD-6 matched-opportunity
verification, resolved-runtime preflight, then one training run.

Contract: `docs/research/designs/VK0D_REALIZATION_DECISION_LEDGER.md`, frozen
amendments A-VD-3 (the three admissible arm identities), A-VD-4 (order-draw
contract and durable order exposure), A-VD-6 (matched model and optimizer
opportunity) and A-VD-7 (the reference arm's exact-digest reproduction gate).

`scripts/run_vk0b_training.py` is a frozen surface cited by past rounds and is
NOT modified. Everything V-K0B already froze -- the scenario/K0/geometry
constants, the six scientific seeds, the intrinsic-shaping off-switch table,
the `vk0b-exposure-1` structural audit and the A-W6-2 identical-contract
identities -- is imported from it, so the two launchers cannot drift apart.
What this module adds is exactly the V-K0D-specific material:

1. `--arm {primary,control,reference}` maps to exactly three config modules,
   and the resolved `(high_controller, r30_training_order_policy)` pair is
   checked against the frozen A-VD-3 table. Any other combination refuses.
2. A-VD-6 pre-launch verification: for the run's seed, all three arms'
   agents are constructed from an identical global RNG state and must agree
   on initial actor bytes, initial value bytes, optimizer parameter
   membership and parameter counts. The hash table lands in the manifest and
   any inequality refuses launch.
3. The post-training exposure audit is extended with the A-VD-4 order-exposure
   block: the canonical arms (REFERENCE, PRIMARY) must show zero order-stream
   consumption, and the CONTROL arm must carry a real schedule digest with
   both orders actually realized.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import random
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.standalone_agent import (
    VK0D_ORDER_STREAM_NONE,
    VK0D_ORDER_STREAM_VERSION,
    StandaloneProcessAgent,
)
from scripts.run_vk0b_training import (
    ADMISSIBLE_EXPOSURE_SOURCES,
    EXPECTED_DEVICE,
    EXPECTED_K0,
    EXPECTED_NUM_ENVS,
    EXPECTED_ROLLOUT_LENGTH,
    EXPECTED_SCENARIO,
    EXPECTED_TOTAL_TIMESTEPS,
    FINAL_CHECKPOINT_NAME,
    INTRINSIC_SHAPING_OFF,
    SCIENTIFIC_SEEDS,
    _config_only_fields,
    _sha256_bytes,
    _sha256_file,
    atomic_write_json,
    resolve_manifest,
    validate_actual_exposure_block,
    validate_identical_contract_identities,
    validate_resolved as validate_vk0b_resolved,
)

CONTRACT_ID = "VK0D_CARRIER_COMPARISON"
TRACE_SCHEMA_VERSION = "vk0d-1"

# A-VD-3, verbatim: three arms, three (config, controller, order policy)
# identities, and nothing else is admissible in a scientific V-K0D run.
ARMS: dict[str, dict[str, str]] = {
    "primary": {
        "config": "config_d7_2b_toy_conjugate_keep",
        "high_controller": "r30_fixed_clock_ar_edit_conjugate",
        "r30_training_order_policy": "canonical",
    },
    "control": {
        "config": "config_d7_2b_toy_randorder_keep",
        "high_controller": "r30_fixed_clock_ar_edit",
        "r30_training_order_policy": "uniform_per_check",
    },
    "reference": {
        "config": "config_d7_2b_toy_learned_keep",
        "high_controller": "r30_fixed_clock_ar_edit",
        "r30_training_order_policy": "canonical",
    },
}

# The arms whose serialization is canonical, i.e. the ones A-VD-7 clause 4
# requires to consume no order-stream draw at all.
CANONICAL_ARMS = frozenset({"primary", "reference"})

ORDER_EXPOSURE_STRING_KEYS = (
    "order_stream_version",
    "r30_training_order_policy",
    "schedule_digest",
)
ORDER_EXPOSURE_INT_KEYS = (
    "completed_canonical_sequences",
    "completed_reversed_sequences",
    "agent0_first_count",
    "agent1_first_count",
    "completed_sequence_total",
)

_EMPTY_SCHEDULE_DIGEST = hashlib.sha256(b"").hexdigest()


class Vk0dPreflightError(Exception):
    """An arm identity, an A-VD-6 matched-opportunity equality, or a resolved
    runtime value failed before any environment step. The run must not be
    launched."""


# ---------------------------------------------------------------------------
# Arm identity (A-VD-3)
# ---------------------------------------------------------------------------


def validate_arm_identity(arm: str, config) -> list[str]:
    """The frozen A-VD-3 combination check. `arm` selects the expected pair;
    the pair is then read off the RESOLVED config module, never assumed from
    the arm name, so a config whose fields were edited out from under the
    launcher is refused rather than silently relabelled."""
    violations: list[str] = []
    if arm not in ARMS:
        return [f"arm: {arm!r} is not one of {sorted(ARMS)}"]
    expected = ARMS[arm]
    for field_name in ("high_controller", "r30_training_order_policy"):
        actual = getattr(config, field_name, None)
        if actual is None:
            violations.append(
                f"config.{field_name}: missing from the resolved config module "
                f"(arm={arm})"
            )
            continue
        if str(actual) != expected[field_name]:
            violations.append(
                f"config.{field_name}: arm {arm!r} requires "
                f"{expected[field_name]!r}, got {str(actual)!r}"
            )
    # The pair as a whole, not only field-by-field: no combination outside the
    # frozen three is a V-K0D arm even if each field is individually legal.
    pair = (
        str(getattr(config, "high_controller", "")),
        str(getattr(config, "r30_training_order_policy", "")),
    )
    admissible = {
        (spec["high_controller"], spec["r30_training_order_policy"])
        for spec in ARMS.values()
    }
    if pair not in admissible:
        violations.append(
            f"(high_controller, r30_training_order_policy)={pair!r} is not one of "
            f"the three frozen A-VD-3 combinations {sorted(admissible)}"
        )
    return violations


# ---------------------------------------------------------------------------
# A-VD-6 matched model and optimizer opportunity
# ---------------------------------------------------------------------------


def canonical_state_digest(state_dict) -> str:
    """SHA-256 binding parameter/buffer name, shape, dtype and exact bytes --
    the same canonical binding A-VD-7 uses for the final-state digests, so a
    launch-time equality and a result-time equality mean the same thing."""
    hasher = hashlib.sha256()
    for name in sorted(state_dict.keys()):
        tensor = state_dict[name]
        hasher.update(name.encode("utf-8"))
        hasher.update(b"|")
        hasher.update(str(tuple(tensor.shape)).encode("utf-8"))
        hasher.update(b"|")
        hasher.update(str(tensor.dtype).encode("utf-8"))
        hasher.update(b"|")
        hasher.update(tensor.detach().cpu().contiguous().numpy().tobytes())
        hasher.update(b"\n")
    return hasher.hexdigest()


def optimizer_parameter_membership(agent: StandaloneProcessAgent) -> list[str]:
    """The shared high optimizer's parameter membership as
    `group/name/shape` strings. Names come from the owning modules'
    `named_parameters()` and are matched by object identity, so a parameter
    that entered the optimizer from a different module -- or did not enter at
    all -- shows up as a difference rather than as an index coincidence."""
    name_by_id: dict[int, str] = {}
    owners = (
        ("high", getattr(agent, "high", None)),
        ("high_value", getattr(agent, "high_value", None)),
        ("compact", getattr(agent, "compact", None)),
        ("bridge", getattr(agent, "bridge", None)),
        ("compact_return_head", getattr(agent, "compact_return_head", None)),
    )
    for prefix, module in owners:
        if module is None:
            continue
        for name, parameter in module.named_parameters():
            name_by_id[id(parameter)] = f"{prefix}.{name}"
    membership: list[str] = []
    for group_index, group in enumerate(agent.high_opt.param_groups):
        for parameter in group["params"]:
            membership.append(
                f"{group_index}/"
                f"{name_by_id.get(id(parameter), '<unmapped>')}/"
                f"{tuple(parameter.shape)}"
            )
    return membership


def build_fresh_agent(config, seed: int) -> StandaloneProcessAgent:
    """A freshly initialized, untrained agent built from an identical global
    RNG state on every call. Every stream that could influence module
    initialization is reseeded here, so a difference between two arms is a
    difference in the arms and not in where the streams happened to be."""
    torch.manual_seed(int(seed))
    np.random.seed(int(seed) % (2**32))
    random.seed(int(seed))
    return StandaloneProcessAgent(
        obs_dim=int(config.obs_dim),
        action_dim=int(config.action_dim),
        n_agents=int(config.n_agents),
        config=config,
        device=EXPECTED_DEVICE,
        action_space_type=str(config.action_space_type),
        num_envs=1,
    )


def arm_initial_identity(arm: str, seed: int) -> dict:
    """The A-VD-6 fingerprint of one arm at initialization."""
    config = importlib.import_module(ARMS[arm]["config"]).Config()
    agent = build_fresh_agent(config, seed)
    return {
        "arm": arm,
        "config_module": ARMS[arm]["config"],
        "high_controller": str(config.high_controller),
        "r30_training_order_policy": str(config.r30_training_order_policy),
        "initial_high_actor_sha256": canonical_state_digest(agent.high.state_dict()),
        "initial_high_value_sha256": canonical_state_digest(
            agent.high_value.state_dict()
        ),
        "optimizer_parameter_membership": optimizer_parameter_membership(agent),
        "parameter_counts": {
            key: int(value) for key, value in agent.parameter_counts().items()
        },
    }


def verify_matched_opportunity(seed: int) -> tuple[dict, list[str]]:
    """A-VD-6, per seed, across all three arms. Returns the hash table for
    the manifest and the named violation list; any inequality means the run
    must not launch, because a comparison between arms that did not start
    from the same model and the same optimizer budget measures the difference
    in their starting points."""
    table = {arm: arm_initial_identity(arm, seed) for arm in sorted(ARMS)}
    violations: list[str] = []
    baseline_arm = "reference"
    baseline = table[baseline_arm]
    for arm in sorted(ARMS):
        if arm == baseline_arm:
            continue
        candidate = table[arm]
        for key in (
            "initial_high_actor_sha256",
            "initial_high_value_sha256",
            "optimizer_parameter_membership",
            "parameter_counts",
        ):
            if candidate[key] != baseline[key]:
                violations.append(
                    f"A-VD-6 seed={seed} arm={arm}: {key} differs from "
                    f"{baseline_arm} ({candidate[key]!r} != {baseline[key]!r})"
                )
    return table, violations


# ---------------------------------------------------------------------------
# Resolved-runtime preflight (VD-7 exposure matching, A-VD-3 identity)
# ---------------------------------------------------------------------------


def resolve_vk0d_manifest(config, args: argparse.Namespace) -> dict:
    """V-K0B's resolved block plus the V-K0D arm identity fields. The order
    policy joins the config-only fields, so `resolved_config_hash`
    distinguishes CONTROL from REFERENCE even though every other resolved
    value is identical between them (VD-6)."""
    resolved = resolve_manifest(config, args)
    resolved["arm"] = str(args.arm)
    resolved["r30_training_order_policy"] = str(config.r30_training_order_policy)
    resolved["contract_id"] = CONTRACT_ID
    resolved["trace_schema_version"] = TRACE_SCHEMA_VERSION
    return resolved


def vk0d_resolved_config_hash(resolved: dict) -> str:
    fields = dict(_config_only_fields(resolved))
    fields["r30_training_order_policy"] = resolved["r30_training_order_policy"]
    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return _sha256_bytes(canonical.encode("utf-8"))


def validate_resolved(
    resolved: dict, seed: int, nonscientific: bool, arm: str
) -> list[str]:
    """Every frozen V-K0B expectation except the single-controller check --
    which V-K0D replaces with the per-arm controller from the A-VD-3 table --
    plus the arm's own controller expectation."""
    violations = [
        violation
        for violation in validate_vk0b_resolved(resolved, seed, nonscientific)
        if not violation.startswith("controller:")
    ]
    expected_controller = ARMS[arm]["high_controller"]
    if resolved["controller"] != expected_controller:
        violations.append(
            f"controller: arm {arm!r} expects {expected_controller!r}, "
            f"got {resolved['controller']!r}"
        )
    expected_policy = ARMS[arm]["r30_training_order_policy"]
    if resolved["r30_training_order_policy"] != expected_policy:
        violations.append(
            f"r30_training_order_policy: arm {arm!r} expects {expected_policy!r}, "
            f"got {resolved['r30_training_order_policy']!r}"
        )
    return violations


# ---------------------------------------------------------------------------
# Post-training order-exposure audit (A-VD-4)
# ---------------------------------------------------------------------------


def validate_order_exposure(block: dict, arm: str) -> list[str]:
    """A-VD-4 durable order exposure, audited off the training-side
    `actual_exposure` block. Structural completeness, the two count
    identities, and the per-arm stream expectation: a canonical arm must show
    no stream identity and no reversed sequence, and the order-randomized arm
    must carry a real schedule digest with both orders actually realized. An
    order-randomized arm whose reversed count is zero is refused -- a
    randomization that never fired is not evidence of randomization."""
    violations: list[str] = []
    if not isinstance(block, dict):
        return [f"actual_exposure: missing or not an object (got {block!r})"]

    for key in ORDER_EXPOSURE_STRING_KEYS:
        if key not in block:
            violations.append(f"actual_exposure.{key}: missing")
        elif not isinstance(block[key], str):
            violations.append(
                f"actual_exposure.{key}: expected str, got {block[key]!r}"
            )
    values: dict[str, int] = {}
    for key in ORDER_EXPOSURE_INT_KEYS:
        if key not in block:
            violations.append(f"actual_exposure.{key}: missing")
            continue
        entry = block[key]
        if not isinstance(entry, dict) or "value" not in entry or "source" not in entry:
            violations.append(
                f"actual_exposure.{key}: not a {{value, source}} entry: {entry!r}"
            )
            continue
        if entry["source"] not in ADMISSIBLE_EXPOSURE_SOURCES:
            violations.append(
                f"actual_exposure.{key}.source: inadmissible label {entry['source']!r}"
            )
        value = entry["value"]
        if not isinstance(value, int) or isinstance(value, bool):
            violations.append(
                f"actual_exposure.{key}.value: expected int, got {value!r}"
            )
            continue
        values[key] = int(value)
    if violations:
        return violations

    total = values["completed_sequence_total"]
    if (
        values["completed_canonical_sequences"] + values["completed_reversed_sequences"]
        != total
    ):
        violations.append(
            "actual_exposure: N01 + N10 != completed_sequence_total "
            f"({values['completed_canonical_sequences']} + "
            f"{values['completed_reversed_sequences']} != {total}) (A-VD-4)"
        )
    if values["agent0_first_count"] + values["agent1_first_count"] != total:
        violations.append(
            "actual_exposure: agent0_first_count + agent1_first_count != "
            f"completed_sequence_total ({values['agent0_first_count']} + "
            f"{values['agent1_first_count']} != {total}) (A-VD-4)"
        )
    if total <= 0:
        violations.append(
            "actual_exposure.completed_sequence_total: no committed high-check "
            "sequence was recorded; the order exposure measures nothing (A-VD-4)"
        )

    expected_policy = ARMS[arm]["r30_training_order_policy"]
    if block["r30_training_order_policy"] != expected_policy:
        violations.append(
            f"actual_exposure.r30_training_order_policy: arm {arm!r} expects "
            f"{expected_policy!r}, got {block['r30_training_order_policy']!r}"
        )

    digest = block["schedule_digest"]
    if len(digest) != 64 or digest == _EMPTY_SCHEDULE_DIGEST:
        violations.append(
            f"actual_exposure.schedule_digest: not a populated SHA-256 digest "
            f"({digest!r}) (A-VD-4)"
        )

    if arm in CANONICAL_ARMS:
        if block["order_stream_version"] != VK0D_ORDER_STREAM_NONE:
            violations.append(
                f"actual_exposure.order_stream_version: canonical arm {arm!r} must "
                f"report {VK0D_ORDER_STREAM_NONE!r}, got "
                f"{block['order_stream_version']!r} (A-VD-7 clause 4)"
            )
        if values["completed_reversed_sequences"] != 0:
            violations.append(
                f"actual_exposure.completed_reversed_sequences: canonical arm "
                f"{arm!r} must be 0, got {values['completed_reversed_sequences']} "
                "(A-VD-7 clause 4)"
            )
    else:
        if block["order_stream_version"] != VK0D_ORDER_STREAM_VERSION:
            violations.append(
                f"actual_exposure.order_stream_version: order-randomized arm "
                f"{arm!r} must report {VK0D_ORDER_STREAM_VERSION!r}, got "
                f"{block['order_stream_version']!r} (A-VD-4)"
            )
        if values["completed_reversed_sequences"] <= 0:
            violations.append(
                "actual_exposure.completed_reversed_sequences: order-randomized "
                f"arm {arm!r} realized no reversed sequence over {total} committed "
                "sequences; the schedule did not fire (A-VD-4)"
            )
        if values["completed_canonical_sequences"] <= 0:
            violations.append(
                "actual_exposure.completed_canonical_sequences: order-randomized "
                f"arm {arm!r} realized no canonical sequence over {total} committed "
                "sequences; the schedule did not fire (A-VD-4)"
            )
    return violations


def audit_actual_exposure(run_manifest: dict, scientific: bool, arm: str) -> tuple[str, list[str]]:
    """The complete post-training audit: V-K0B's structural completeness
    always, V-K0B's A-W6-2 identical-contract identities for scientific runs,
    and the A-VD-4 order-exposure audit always."""
    violations = validate_actual_exposure_block(run_manifest)
    block = run_manifest.get("actual_exposure")
    if scientific and isinstance(block, dict):
        violations = violations + validate_identical_contract_identities(block)
    violations = violations + validate_order_exposure(block, arm)
    status = "FAILED" if violations else "PASSED"
    return status, violations


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------


def build_train_command(python: str, args: argparse.Namespace) -> list[str]:
    spec = ARMS[str(args.arm)]
    return [
        python,
        "-B",
        "-m",
        "ha_ctse_process.train",
        "--mode",
        "train",
        "--config",
        spec["config"],
        "--scenario",
        EXPECTED_SCENARIO,
        "--high_controller",
        spec["high_controller"],
        "--skill_interval",
        str(EXPECTED_K0),
        "--seed",
        str(args.seed),
        "--num_envs",
        str(EXPECTED_NUM_ENVS),
        "--collector_backend",
        "sync",
        "--device",
        EXPECTED_DEVICE,
        "--rollout_length",
        str(EXPECTED_ROLLOUT_LENGTH),
        "--total_timesteps",
        str(EXPECTED_TOTAL_TIMESTEPS),
        "--save_interval",
        "0",
        "--eval_interval",
        "0",
        "--plot_interval",
        "0",
        "--log_dir",
        str(args.output_root),
    ]


def build_training_result(
    output_root: Path,
    command: list[str],
    returncode: int,
    nonscientific: bool,
    arm: str,
) -> dict:
    """Everything after the training subprocess exits: locate and hash the run
    manifest and the final checkpoint, run the extended exposure audit, and
    delete nonscientific checkpoints. Takes concrete values rather than
    reaching into `subprocess`, so it is callable directly against a fixture
    directory with no real training involved."""
    training_result: dict = {"command": command, "returncode": returncode, "arm": arm}
    if returncode != 0:
        training_result["error"] = f"training subprocess exited {returncode}"
        return training_result

    run_manifest_path = output_root / "metadata" / "run_manifest.json"
    final_checkpoint_path = output_root / FINAL_CHECKPOINT_NAME

    if not run_manifest_path.is_file():
        training_result["error"] = f"training exited 0 but {run_manifest_path} is missing"
        training_result["exposure_audit"] = "FAILED"
        training_result["exposure_audit_violations"] = [
            f"run_manifest.json: missing at {run_manifest_path}"
        ]
    else:
        run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
        training_result["run_manifest_path"] = str(run_manifest_path)
        training_result["run_manifest_sha256"] = _sha256_file(run_manifest_path)
        status, exposure_violations = audit_actual_exposure(
            run_manifest, scientific=not nonscientific, arm=arm
        )
        training_result["exposure_audit"] = status
        training_result["exposure_audit_violations"] = exposure_violations
        block = run_manifest.get("actual_exposure")
        if isinstance(block, dict):
            training_result["order_exposure"] = {
                key: block.get(key)
                for key in ORDER_EXPOSURE_STRING_KEYS + ORDER_EXPOSURE_INT_KEYS
            }

    if final_checkpoint_path.is_file():
        training_result["final_checkpoint_path"] = str(final_checkpoint_path)
        training_result["checkpoint_sha256"] = _sha256_file(final_checkpoint_path)
    else:
        training_result["error"] = (
            training_result.get("error", "")
            + f"; training exited 0 but {final_checkpoint_path} is missing"
        ).strip("; ")

    if nonscientific:
        deleted = []
        for checkpoint_file in output_root.glob("standalone_process_core_*.pt"):
            checkpoint_file.unlink()
            deleted.append(str(checkpoint_file))
        training_result["nonscientific_checkpoints_deleted"] = deleted

    return training_result


def run(args: argparse.Namespace) -> int:
    arm = str(args.arm)
    config = importlib.import_module(ARMS[arm]["config"]).Config()
    args.config = ARMS[arm]["config"]

    resolved = resolve_vk0d_manifest(config, args)
    cfg_hash = vk0d_resolved_config_hash(resolved)

    violations = validate_arm_identity(arm, config)
    violations = violations + validate_resolved(
        resolved, args.seed, args.nonscientific, arm
    )
    matched_table, matched_violations = verify_matched_opportunity(int(args.seed))
    violations = violations + matched_violations

    manifest_path = Path(args.output_root) / "vk0d_preflight_manifest.json"
    manifest = {
        "contract_id": CONTRACT_ID,
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "arm": arm,
        "config_module": ARMS[arm]["config"],
        "controller": ARMS[arm]["high_controller"],
        "r30_training_order_policy": ARMS[arm]["r30_training_order_policy"],
        "resolved": resolved,
        "resolved_config_hash": cfg_hash,
        "matched_opportunity_avd6": matched_table,
        "nonscientific": bool(args.nonscientific),
        "preflight_passed": len(violations) == 0,
        "preflight_violations": violations,
    }
    atomic_write_json(manifest_path, manifest)

    if violations:
        raise Vk0dPreflightError(
            "V-K0D preflight refused before any environment step: "
            + "; ".join(violations)
        )

    command = build_train_command(args.python, args)
    manifest["training"] = {"command": command}
    atomic_write_json(manifest_path, manifest)

    completed = subprocess.run(command, cwd=str(PROJECT_ROOT))
    returncode = int(completed.returncode)

    training_result = build_training_result(
        output_root=Path(args.output_root),
        command=command,
        returncode=returncode,
        nonscientific=bool(args.nonscientific),
        arm=arm,
    )
    manifest["training"] = training_result
    atomic_write_json(manifest_path, manifest)

    print(f"VK0D_ARM={arm}")
    print(f"VK0D_PREFLIGHT_PASSED={manifest['preflight_passed']}")
    print(f"VK0D_RESOLVED_CONFIG_HASH={cfg_hash}")
    print(f"VK0D_TRAIN_RETURNCODE={returncode}")
    print(f"VK0D_MANIFEST={manifest_path}")
    if "checkpoint_sha256" in training_result:
        print(f"VK0D_CHECKPOINT_SHA256={training_result['checkpoint_sha256']}")
    if "exposure_audit" in training_result:
        print(f"VK0D_EXPOSURE_AUDIT={training_result['exposure_audit']}")

    exit_code = returncode
    if returncode == 0 and training_result.get("exposure_audit") == "FAILED":
        exit_code = 1
    return exit_code


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=tuple(sorted(ARMS)), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-root", dest="output_root", required=True)
    parser.add_argument(
        "--nonscientific",
        action="store_true",
        help="Timing microbenchmark: requires a seed outside the six scientific "
        f"seeds {SCIENTIFIC_SEEDS}, marks the manifest nonscientific, and deletes "
        "the checkpoint(s) after training.",
    )
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    try:
        returncode = run(args)
    except Vk0dPreflightError as exc:
        print(f"VK0D_PREFLIGHT_REFUSED={exc}")
        raise SystemExit(1) from exc
    raise SystemExit(returncode)


if __name__ == "__main__":
    main()
