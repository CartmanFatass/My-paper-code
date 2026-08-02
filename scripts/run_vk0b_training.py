"""V-K0B training launcher: resolved-runtime preflight, then one training run.

Contract: `docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md` (VK-D8,
VK-D10, A-VK-D8) and the two frozen rulings named there (ruling
`docs/external-review/rounds/20260801_variable_k_algorithm_direction/
21_PRO_OPEN_RAW.md` EVIDENCE_DESIGN "Training contract"; conformance round
`docs/external-review/rounds/20260801_vk0_design_conformance/21_PRO_OPEN_RAW.md`
VK-D8, and `22_PRO_CONVERGENCE.md` clarification 1).

Before the first environment step, this writes and validates the RESOLVED
runtime values against the frozen VK-D8 expectations and refuses, named, on
any mismatch. It then launches the registered training entry point
(`python -m ha_ctse_process.train`) as a subprocess with the seed and output
root plumbed the way `train.py`'s own argparse genuinely accepts them --
`--seed` and `--log_dir` -- read directly from that module's `parse_args`
rather than assumed. `train.py` does not copy numeric fields (`num_envs`,
`rollout_length`, `total_timesteps`, `skill_interval`, `high_controller`)
from the config module onto the run; `apply_standalone_overrides` only ever
reads them from argparse, so every one of those frozen values is passed as an
explicit CLI flag too (verified against a prior real run's own
`run_manifest.json` under
`logs/nonformal_d7_2b_toy_learned_keep_20260725_40708a0_directstate_pm1/`,
which shows exactly this: `total_timesteps=128000` on the command line even
though the config module itself says `640_000`). No derived config module is
generated -- train.py genuinely supports passing every frozen value as a CLI
flag, so that is the route taken.

After training exits, this appends the actual final-checkpoint identity, the
run manifest's own SHA-256, and a fail-closed audit of the complete
`actual_exposure` block that `train.py`'s `run_manifest.json` now carries
(contract: `docs/research/designs/VK0B_RERUN_EXPOSURE_DECISION_LEDGER.md`
W6-D2, A-W6-5, amended by
`docs/external-review/rounds/20260801_vk0b_rerun_exposure_conformance/
21_PRO_OPEN_RAW.md` section 4). Every mandatory exposure key must be present
with an admissible source label and a value of the right type; for a
scientific run (not `--nonscientific`) the frozen identical-contract
identities (A-W6-2) are checked too. Any violation -- missing field,
inadmissible source, wrong-typed value, or a mismatched identity, however
honestly the deviation was recorded -- sets `exposure_audit=FAILED` in the
launcher manifest and the script exits nonzero. Recording a deviation does
not make it admissible.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from ha_ctse_process.standalone_agent import FixedSkillPrimitivePolicy

CONTRACT_ID = "VK0_TOY_RENEWAL_URGENCY"
TRACE_SCHEMA_VERSION = "vk0b-1"

# 2026080101..2026080106 inclusive (VK-D7, EVIDENCE_DESIGN "training seeds").
SCIENTIFIC_SEEDS = tuple(range(2026080101, 2026080107))

# A-VK-D8 / EVIDENCE_DESIGN "Training contract": the frozen resolved values a
# scientific run must match exactly before the first environment step.
EXPECTED_SCENARIO = "two_timescale_role_free_actions"
EXPECTED_CONTROLLER = "r30_fixed_clock_ar_edit"
EXPECTED_K0 = 5
EXPECTED_N_AGENTS = 2
EXPECTED_N_SKILLS = 4
EXPECTED_NUM_ENVS = 16
EXPECTED_ROLLOUT_LENGTH = 40
EXPECTED_TOTAL_TIMESTEPS = 640_000
EXPECTED_DEVICE = "cpu"

FINAL_CHECKPOINT_NAME = "standalone_process_core_final.pt"

# Every intrinsic/shaping switch VK-D8 requires disabled, and the value that
# means "disabled" for that field -- read directly from
# `config_d7_2b_toy_learned_keep.py`'s own "External reward only" block, not
# duplicated as a separate assumption.
INTRINSIC_SHAPING_OFF = {
    "process_reward_injection": "none",
    "outcome_residual_injection": "none",
    "topology_role_injection": "none",
    "topology_potential_injection": "none",
    "skill_effect_reward_injection": "none",
    "skill_force_reward_injection": "none",
    "use_process_reward_for_discoverer": False,
    "disable_discriminator_training": True,
    "disable_discriminator_rewards": True,
    "lambda_D": 0.0,
    "lambda_d": 0.0,
    "enable_prototype_disc_reward": False,
    "enable_team_transition_reward": False,
    "enable_team_disc_reward": False,
    "enable_assignment_actionability_reward": False,
    "skill_effect_reward_on": False,
    "enable_skill_forcing_reward": False,
    "p2_recovery_credit_reward_on": False,
    "use_topology_potential_shaping": False,
    "alice_bob_semantic_reward_enabled": False,
    "transition_skill_reward_coef": 0.0,
}

# A-W6-5: the frozen schema tag the training-side `actual_exposure` block
# must carry, and the exact admissible evidence-source labels for every
# entry inside it. `config`/`nominal`/`expected`/`derived_from_budget` are
# named inadmissible by the same ruling.
ACTUAL_EXPOSURE_SCHEMA = "vk0b-exposure-1"
ADMISSIBLE_EXPOSURE_SOURCES = frozenset(
    {
        "runtime_counter",
        "training_accumulator",
        "optimizer_state",
        "checkpoint_optimizer_absence",
    }
)

# Mandatory `actual_exposure` keys, grouped by the value type each one's
# `{"value": ..., "source": ...}` entry must carry (W6-D1 realization,
# amended A-W6-1..A-W6-3 in the conformance round named in the module
# docstring).
EXPOSURE_INT_KEYS = (
    "environment_interactions",
    "completed_outer_updates",
    "high_optimizer_steps_shared",
    "high_actor_optimizer_steps",
    "high_value_optimizer_steps",
    "high_actor_parameter_count_expected",
    "high_actor_parameter_count_with_step_state",
    "high_value_parameter_count_expected",
    "high_value_parameter_count_with_step_state",
    "high_optimizer_step_min",
    "high_optimizer_step_max",
    "high_check_sequences_completed",
    "high_check_sequences_failed_or_skipped",
    "agent_tokens_keep",
    "agent_tokens_set",
    "high_epoch_passes_attempted",
    "high_epoch_passes_stepped",
    "high_epoch_passes_skipped",
    "high_epoch_passes_aborted",
    "low_level_optimizer_steps",
)
EXPOSURE_BOOL_KEYS = ("high_optimizer_parameter_coverage_ok",)
# key -> the single admissible string value (A-W6-1: shared-optimizer
# semantics are frozen text, not a free-form label).
EXPOSURE_STRING_KEYS = {"high_optimizer_semantics": "SHARED_ACTOR_VALUE_OPTIMIZER"}
EXPOSURE_LIST_KEYS = ("high_epoch_pass_skip_reasons", "high_epoch_pass_abort_reasons")

MANDATORY_EXPOSURE_KEYS = (
    EXPOSURE_INT_KEYS + EXPOSURE_BOOL_KEYS + tuple(EXPOSURE_STRING_KEYS) + EXPOSURE_LIST_KEYS
)


class Vk0bPreflightError(Exception):
    """A resolved runtime value did not match its frozen VK-D8 expectation,
    or the seed/`--nonscientific` combination is not admissible. Raised
    before any environment step; the run must not be launched."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def action_table_hash() -> str:
    policy = FixedSkillPrimitivePolicy(4, 2, "continuous")
    table = policy.action_table.detach().cpu().numpy().astype(np.float64)
    return _sha256_bytes(np.ascontiguousarray(table).tobytes())


def resolve_manifest(config, args: argparse.Namespace) -> dict:
    """The RESOLVED values, loaded from the config module -- never
    hard-coded expectations substituted for what the module actually says."""
    intrinsic_shaping_resolved = {
        name: getattr(config, name, None) for name in INTRINSIC_SHAPING_OFF
    }
    resolved = {
        "scenario": str(config.scenario),
        "controller": str(config.high_controller),
        "k0": {
            "skill_interval": int(config.skill_interval),
            "r39_toy_k0": int(config.r39_toy_k0),
        },
        "n_agents": int(config.n_agents),
        "n_skills": int(config.n_z),
        "action_table_hash": action_table_hash(),
        "direct_state_context_mode": {
            "r39_toy_direct_state_context": bool(config.r39_toy_direct_state_context),
            "r30_bridge_context_mode": str(config.r30_bridge_context_mode),
            "team_bridge_type": str(config.team_bridge_type),
        },
        "num_envs": int(config.num_envs),
        "rollout_length": int(config.rollout_length),
        "total_timesteps": int(config.total_timesteps),
        "high_ppo_epochs": int(config.r30_high_ppo_epochs),
        "high_learning_rate": float(config.lr_coordinator),
        "low_optimizer_absence": {
            "use_recurrent_low_level": bool(config.use_recurrent_low_level),
            "low_level_architecture": str(config.low_level_architecture),
            "r39_toy_fixed_skill_primitives": bool(config.r39_toy_fixed_skill_primitives),
        },
        "intrinsic_shaping_disabled": intrinsic_shaping_resolved,
        "device": EXPECTED_DEVICE,
        "training_seed": int(args.seed),
        "output_root": str(args.output_root),
        "config_module": str(args.config),
        "contract_id": CONTRACT_ID,
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "nonscientific": bool(args.nonscientific),
    }
    return resolved


def _config_only_fields(resolved: dict) -> dict:
    """The subset of `resolved` that defines `resolved_config_hash` -- the
    config's own identity, not the per-run seed/output-root/nonscientific
    flags A-VK-D8 already tracks as separate identity components."""
    return {
        key: resolved[key]
        for key in (
            "scenario",
            "controller",
            "k0",
            "n_agents",
            "n_skills",
            "action_table_hash",
            "direct_state_context_mode",
            "num_envs",
            "rollout_length",
            "total_timesteps",
            "high_ppo_epochs",
            "high_learning_rate",
            "low_optimizer_absence",
            "intrinsic_shaping_disabled",
            "device",
        )
    }


def resolved_config_hash(resolved: dict) -> str:
    canonical = json.dumps(_config_only_fields(resolved), sort_keys=True, separators=(",", ":"))
    return _sha256_bytes(canonical.encode("utf-8"))


def validate_resolved(resolved: dict, seed: int, nonscientific: bool) -> list[str]:
    """Every frozen VK-D8 expectation, checked by name. Returns the list of
    named violations (empty means the preflight passes)."""
    violations: list[str] = []

    def check(name: str, actual, expected) -> None:
        if actual != expected:
            violations.append(f"{name}: expected {expected!r}, got {actual!r}")

    check("scenario", resolved["scenario"], EXPECTED_SCENARIO)
    check("controller", resolved["controller"], EXPECTED_CONTROLLER)
    check("k0.skill_interval", resolved["k0"]["skill_interval"], EXPECTED_K0)
    check("k0.r39_toy_k0", resolved["k0"]["r39_toy_k0"], EXPECTED_K0)
    check("n_agents", resolved["n_agents"], EXPECTED_N_AGENTS)
    check("n_skills", resolved["n_skills"], EXPECTED_N_SKILLS)
    check("num_envs", resolved["num_envs"], EXPECTED_NUM_ENVS)
    check("rollout_length", resolved["rollout_length"], EXPECTED_ROLLOUT_LENGTH)
    check("total_timesteps", resolved["total_timesteps"], EXPECTED_TOTAL_TIMESTEPS)
    check("device", resolved["device"], EXPECTED_DEVICE)
    check(
        "low_optimizer_absence.use_recurrent_low_level",
        resolved["low_optimizer_absence"]["use_recurrent_low_level"],
        False,
    )
    check(
        "low_optimizer_absence.r39_toy_fixed_skill_primitives",
        resolved["low_optimizer_absence"]["r39_toy_fixed_skill_primitives"],
        True,
    )
    for field_name, expected in INTRINSIC_SHAPING_OFF.items():
        check(
            f"intrinsic_shaping_disabled.{field_name}",
            resolved["intrinsic_shaping_disabled"][field_name],
            expected,
        )

    if nonscientific:
        if int(seed) in SCIENTIFIC_SEEDS:
            violations.append(
                f"--nonscientific requires a seed outside {SCIENTIFIC_SEEDS}; got {seed}"
            )
    else:
        if int(seed) not in SCIENTIFIC_SEEDS:
            violations.append(
                f"seed {seed} is not one of the six scientific seeds {SCIENTIFIC_SEEDS}; "
                "pass --nonscientific for a microbenchmark seed"
            )
    return violations


def validate_actual_exposure_block(run_manifest: dict) -> list[str]:
    """A-W6-5 structural audit of `run_manifest["actual_exposure"]`: schema
    tag, every mandatory key present with the right type (string/list keys as
    plain values, int/bool keys as `{"value", "source"}` entries), every
    source label admissible, every value the right type. Returns the named
    violation list (empty means the block is structurally complete)."""
    violations: list[str] = []
    block = run_manifest.get("actual_exposure")
    if not isinstance(block, dict):
        return [f"actual_exposure: missing or not an object (got {block!r})"]

    schema = block.get("actual_exposure_schema")
    if schema != ACTUAL_EXPOSURE_SCHEMA:
        violations.append(
            f"actual_exposure_schema: expected {ACTUAL_EXPOSURE_SCHEMA!r}, got {schema!r}"
        )

    for key in MANDATORY_EXPOSURE_KEYS:
        if key not in block:
            violations.append(f"actual_exposure.{key}: missing")
            continue
        raw = block[key]
        if key in EXPOSURE_STRING_KEYS:
            expected_value = EXPOSURE_STRING_KEYS[key]
            if raw != expected_value:
                violations.append(
                    f"actual_exposure.{key}: expected {expected_value!r}, got {raw!r}"
                )
            continue
        if key in EXPOSURE_LIST_KEYS:
            if not isinstance(raw, list):
                violations.append(f"actual_exposure.{key}: expected list, got {raw!r}")
            continue
        entry = raw
        if not isinstance(entry, dict) or "value" not in entry or "source" not in entry:
            violations.append(f"actual_exposure.{key}: not a {{value, source}} entry: {entry!r}")
            continue
        value = entry["value"]
        source = entry["source"]
        if source not in ADMISSIBLE_EXPOSURE_SOURCES:
            violations.append(f"actual_exposure.{key}.source: inadmissible label {source!r}")
        if key in EXPOSURE_INT_KEYS:
            if not isinstance(value, int) or isinstance(value, bool):
                violations.append(f"actual_exposure.{key}.value: expected int, got {value!r}")
        elif key in EXPOSURE_BOOL_KEYS:
            if not isinstance(value, bool):
                violations.append(f"actual_exposure.{key}.value: expected bool, got {value!r}")
    return violations


def validate_identical_contract_identities(block: dict) -> list[str]:
    """A-W6-2 exact-exposure identities for the identical-contract scientific
    rerun: `block` is `run_manifest["actual_exposure"]`. Any nonzero skipped
    or aborted high pass -- however honestly recorded -- is a violation; the
    same for any other mismatched identity. Called only for scientific runs
    (`--nonscientific` runs are microbenchmarks, not the frozen contract)."""
    violations: list[str] = []

    def value_of(key: str):
        entry = block.get(key)
        return entry.get("value") if isinstance(entry, dict) else None

    exact_identities = (
        ("environment_interactions", 640_000),
        ("completed_outer_updates", 1000),
        ("high_epoch_passes_attempted", 3000),
        ("high_epoch_passes_stepped", 3000),
        ("high_epoch_passes_skipped", 0),
        ("high_epoch_passes_aborted", 0),
        ("high_optimizer_steps_shared", 3000),
        ("low_level_optimizer_steps", 0),
    )
    for key, expected in exact_identities:
        actual = value_of(key)
        if actual != expected:
            violations.append(
                f"actual_exposure.{key}.value: expected {expected!r}, got {actual!r} "
                "(identical-contract identity, A-W6-2)"
            )

    coverage_ok = value_of("high_optimizer_parameter_coverage_ok")
    if coverage_ok is not True:
        violations.append(
            "actual_exposure.high_optimizer_parameter_coverage_ok.value: expected True, "
            f"got {coverage_ok!r} (identical-contract identity, A-W6-1)"
        )

    keep = value_of("agent_tokens_keep")
    set_ = value_of("agent_tokens_set")
    completed = value_of("high_check_sequences_completed")
    if not (isinstance(keep, int) and isinstance(set_, int) and isinstance(completed, int)):
        violations.append(
            "actual_exposure.agent_tokens_keep/agent_tokens_set/high_check_sequences_completed: "
            "not all present as int values; cannot verify KEEP+SET == 2*completed "
            "(identical-contract identity, A-W6-3)"
        )
    elif keep + set_ != 2 * completed:
        violations.append(
            f"actual_exposure.agent_tokens_keep+agent_tokens_set: expected {2 * completed} "
            f"(2 * high_check_sequences_completed={completed}), got {keep + set_} "
            "(identical-contract identity, A-W6-3)"
        )
    return violations


def audit_actual_exposure(run_manifest: dict, scientific: bool) -> tuple[str, list[str]]:
    """The complete A-W6-5 post-training audit: structural completeness
    always, plus the A-W6-2 identical-contract identities for scientific
    runs. Returns `(exposure_audit, violations)` where `exposure_audit` is
    `"PASSED"` or `"FAILED"`."""
    violations = validate_actual_exposure_block(run_manifest)
    block = run_manifest.get("actual_exposure")
    if scientific and isinstance(block, dict):
        violations = violations + validate_identical_contract_identities(block)
    status = "FAILED" if violations else "PASSED"
    return status, violations


def build_train_command(python: str, args: argparse.Namespace, config_intrinsic_check: dict) -> list[str]:
    del config_intrinsic_check  # documented in the module docstring, not re-derived here
    return [
        python,
        "-B",
        "-m",
        "ha_ctse_process.train",
        "--mode",
        "train",
        "--config",
        str(args.config),
        "--scenario",
        EXPECTED_SCENARIO,
        "--high_controller",
        EXPECTED_CONTROLLER,
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


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def build_training_result(
    output_root: Path, command: list[str], returncode: int, nonscientific: bool
) -> dict:
    """Everything that happens after the training subprocess exits: locate
    `run_manifest.json` and the final checkpoint, hash both, run the A-W6-5
    `actual_exposure` audit (structural always, identical-contract identities
    for scientific runs), and delete nonscientific checkpoints. Takes a
    concrete `output_root` and `returncode` rather than reaching into
    `subprocess` itself, so it is callable directly against a fixture
    directory with no real training involved."""
    training_result: dict = {"command": command, "returncode": returncode}
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
            run_manifest, scientific=not nonscientific
        )
        training_result["exposure_audit"] = status
        training_result["exposure_audit_violations"] = exposure_violations

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
    config = importlib.import_module(args.config).Config()
    resolved = resolve_manifest(config, args)
    cfg_hash = resolved_config_hash(resolved)
    violations = validate_resolved(resolved, args.seed, args.nonscientific)

    manifest_path = Path(args.output_root) / "vk0b_preflight_manifest.json"
    manifest = {
        "contract_id": CONTRACT_ID,
        "trace_schema_version": TRACE_SCHEMA_VERSION,
        "resolved": resolved,
        "resolved_config_hash": cfg_hash,
        "nonscientific": bool(args.nonscientific),
        "preflight_passed": len(violations) == 0,
        "preflight_violations": violations,
    }
    atomic_write_json(manifest_path, manifest)

    if violations:
        raise Vk0bPreflightError(
            "V-K0B resolved-runtime preflight refused before any environment step: "
            + "; ".join(violations)
        )

    command = build_train_command(args.python, args, INTRINSIC_SHAPING_OFF)
    manifest["training"] = {"command": command}
    atomic_write_json(manifest_path, manifest)

    completed = subprocess.run(command, cwd=str(PROJECT_ROOT))
    returncode = int(completed.returncode)

    output_root = Path(args.output_root)
    training_result = build_training_result(
        output_root=output_root,
        command=command,
        returncode=returncode,
        nonscientific=bool(args.nonscientific),
    )

    manifest["training"] = training_result
    atomic_write_json(manifest_path, manifest)

    print(f"VK0B_PREFLIGHT_PASSED={manifest['preflight_passed']}")
    print(f"VK0B_TRAIN_RETURNCODE={returncode}")
    print(f"VK0B_MANIFEST={manifest_path}")
    if "checkpoint_sha256" in training_result:
        print(f"VK0B_CHECKPOINT_SHA256={training_result['checkpoint_sha256']}")
    if "exposure_audit" in training_result:
        print(f"VK0B_EXPOSURE_AUDIT={training_result['exposure_audit']}")

    exit_code = returncode
    if returncode == 0 and training_result.get("exposure_audit") == "FAILED":
        exit_code = 1
    return exit_code


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-root", dest="output_root", required=True)
    parser.add_argument("--config", default="config_d7_2b_toy_learned_keep")
    parser.add_argument(
        "--nonscientific",
        action="store_true",
        help="Timing microbenchmark: requires a seed outside the six scientific "
        "seeds, marks the manifest nonscientific, and deletes the checkpoint(s) "
        "after training (A-VK-D8).",
    )
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    try:
        returncode = run(args)
    except Vk0bPreflightError as exc:
        print(f"VK0B_PREFLIGHT_REFUSED={exc}")
        raise SystemExit(1) from exc
    raise SystemExit(returncode)


if __name__ == "__main__":
    main()
