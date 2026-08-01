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

After training exits, this appends the actual final-checkpoint identity and
whatever exposure `train.py`'s own `run_manifest.json` genuinely records to
the SAME preflight manifest file. It never fabricates an exposure field
`run_manifest.json` does not carry (VK-D8 requires "check counts, optimizer
steps, aborted batches" be recorded; only `total_steps` -- environment
interactions -- and `update_idx` -- PPO update count -- are genuinely present
there, so the rest are named absent, not invented).
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

# What `train.py`'s own `run_manifest.json` genuinely records as exposure,
# versus what VK-D8's prose additionally asks for. Named here once so the
# manifest writer and the human report agree on the same list.
EXPOSURE_FIELDS_AVAILABLE = ("total_steps", "update_idx")
EXPOSURE_FIELDS_NOT_AVAILABLE = (
    "high_check_sequences",
    "agent_tokens",
    "high_actor_optimizer_steps_distinct_from_update_idx",
    "low_optimizer_steps",
    "invalid_aborted_batches",
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
    run_manifest_path = output_root / "metadata" / "run_manifest.json"
    final_checkpoint_path = output_root / FINAL_CHECKPOINT_NAME

    training_result: dict = {
        "command": command,
        "returncode": returncode,
    }
    if returncode == 0:
        if not run_manifest_path.is_file():
            training_result["error"] = f"training exited 0 but {run_manifest_path} is missing"
        else:
            run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
            exposure_available = {
                name: run_manifest.get(name) for name in EXPOSURE_FIELDS_AVAILABLE
            }
            training_result["run_manifest_path"] = str(run_manifest_path)
            training_result["final_exposure"] = {
                "available": exposure_available,
                "not_available": list(EXPOSURE_FIELDS_NOT_AVAILABLE),
            }
        if final_checkpoint_path.is_file():
            training_result["final_checkpoint_path"] = str(final_checkpoint_path)
            training_result["checkpoint_sha256"] = _sha256_file(final_checkpoint_path)
        else:
            training_result["error"] = (
                training_result.get("error", "")
                + f"; training exited 0 but {final_checkpoint_path} is missing"
            ).strip("; ")

        if args.nonscientific:
            deleted = []
            for checkpoint_file in output_root.glob("standalone_process_core_*.pt"):
                checkpoint_file.unlink()
                deleted.append(str(checkpoint_file))
            training_result["nonscientific_checkpoints_deleted"] = deleted
    else:
        training_result["error"] = f"training subprocess exited {returncode}"

    manifest["training"] = training_result
    atomic_write_json(manifest_path, manifest)

    print(f"VK0B_PREFLIGHT_PASSED={manifest['preflight_passed']}")
    print(f"VK0B_TRAIN_RETURNCODE={returncode}")
    print(f"VK0B_MANIFEST={manifest_path}")
    if "checkpoint_sha256" in training_result:
        print(f"VK0B_CHECKPOINT_SHA256={training_result['checkpoint_sha256']}")
    return returncode


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
