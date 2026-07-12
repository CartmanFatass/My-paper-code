"""Validate and summarize the quarantined eight-reset R27-G2 wiring pilot."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "EXP-20260712-r27-g2-forced-z-trajectory-effect"
RUN_KIND = "wiring_pilot"
CHECKPOINT_ID = "arm0_final"
CHECKPOINT_UPDATE = 32
CHECKPOINT_FILE = "standalone_process_core_final.pt"
RESET_IDS = tuple(range(8))
PREFIX_STEPS = (50, 150, 250, 50, 150, 250, 50, 150)
PREFIX_POLICY_SEEDS = tuple(27100 + reset_id for reset_id in RESET_IDS)
BRANCH_COUNT = 55
BRANCH_STEPS = 50
ENVIRONMENT_STEPS_BY_RESET = tuple(
    prefix_steps + BRANCH_COUNT * (prefix_steps + BRANCH_STEPS)
    for prefix_steps in PREFIX_STEPS
)
ENVIRONMENT_STEPS_TOTAL = sum(ENVIRONMENT_STEPS_BY_RESET)
VALID_STATES = {"WIRING_PASS", "INCOMPLETE", "INVALID", "crash"}
PILOT_CONTRACT: dict[str, Any] = {
    "experiment_id": EXPERIMENT_ID,
    "run_kind": RUN_KIND,
    "scientific_status": "NOT_EVALUATED",
    "eligible_for_scientific_gate": False,
    "checkpoint_ids": [CHECKPOINT_ID],
    "checkpoint_update": CHECKPOINT_UPDATE,
    "reset_ids": list(RESET_IDS),
    "reset_seeds": [reset_id + 1 for reset_id in RESET_IDS],
    "prefix_policy_seeds": list(PREFIX_POLICY_SEEDS),
    "prefix_steps": list(PREFIX_STEPS),
    "branches_per_reset": BRANCH_COUNT,
    "branch_steps": BRANCH_STEPS,
    "environment_steps": ENVIRONMENT_STEPS_TOTAL,
}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_status(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        values[key] = value
    return values


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _json_from_output(output: str) -> dict[str, Any]:
    for line in reversed(output.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            return value
    raise ValueError("reset validator did not emit a JSON object")


def _expected_manifest_values(reset_id: int) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "reset_id": reset_id,
        "reset_seed": reset_id + 1,
        "prefix_policy_seed": PREFIX_POLICY_SEEDS[reset_id],
        "prefix_steps": PREFIX_STEPS[reset_id],
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_update": CHECKPOINT_UPDATE,
        "checkpoint_file_nonempty": True,
        "device": "cuda",
        "branch_count": BRANCH_COUNT,
        "branch_steps": BRANCH_STEPS,
        "environment_steps": ENVIRONMENT_STEPS_BY_RESET[reset_id],
    }


def _markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# R27-G2 Eight-reset Wiring Pilot",
        "",
        f"- State: `{summary['state']}`",
        "- Scientific status: `NOT_EVALUATED`",
        "- Eligible for the decision-grade gate: `false`",
        f"- Checkpoint: `{CHECKPOINT_ID}`",
        f"- Validated resets: {summary['validated_resets']}/8",
        f"- OK / EXCLUDED / INVALID: {summary['ok_resets']} / "
        f"{summary['excluded_resets']} / {summary['invalid_resets']}",
        f"- Environment steps: {summary['environment_steps_observed']} / "
        f"{ENVIRONMENT_STEPS_TOTAL}",
        "",
        "This report is wiring, parity, artifact, and timing evidence only. It "
        "does not run or report Gate A/B/C and must never be pooled into the "
        "decision-grade 64-reset support.",
    ]
    issues = summary.get("issues", [])
    if issues:
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- {issue}" for issue in issues)
    lines.append("")
    return "\n".join(lines)


def summarize(
    run_root: Path,
    *,
    audit_script: Path,
    python_bin: str,
) -> tuple[dict[str, Any], str]:
    crash_issues: list[str] = []
    invalid_issues: list[str] = []
    incomplete_issues: list[str] = []
    validation_log: list[str] = []
    validated_resets = 0
    observed_steps = 0
    status_counts = {"OK": 0, "EXCLUDED": 0, "INVALID": 0}

    contract_path = run_root / "pilot_contract.json"
    try:
        contract = _read_json(contract_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        invalid_issues.append(f"pilot contract unreadable: {error}")
    else:
        if contract != PILOT_CONTRACT:
            invalid_issues.append("pilot_contract.json does not match the frozen pilot contract")

    checkpoint_dirs = sorted(
        path.name for path in run_root.glob("arm0_*") if path.is_dir()
    )
    if checkpoint_dirs != [CHECKPOINT_ID]:
        invalid_issues.append("pilot checkpoint inventory must contain only arm0_final")

    reset_root = run_root / CHECKPOINT_ID / "resets"
    expected_reset_dirs = [reset_root / f"reset_{reset_id:02d}" for reset_id in RESET_IDS]
    found_reset_dirs = sorted(path for path in reset_root.glob("reset_*") if path.is_dir())
    if found_reset_dirs != expected_reset_dirs:
        invalid_issues.append("pilot reset directory inventory must be exactly reset_00..07")
    expected_manifests = [
        reset_dir / "reset_manifest.json" for reset_dir in expected_reset_dirs
    ]
    found_manifests = sorted(reset_root.glob("reset_*/reset_manifest.json"))
    if found_manifests != expected_manifests:
        invalid_issues.append(
            "pilot reset manifest inventory must be exactly arm0_final/reset_00..07"
        )

    for reset_id, manifest_path in zip(RESET_IDS, expected_manifests):
        output_dir = manifest_path.parent
        runner_status_path = output_dir / "runner_status.txt"
        if not runner_status_path.is_file():
            crash_issues.append(f"reset {reset_id} is missing runner_status.txt")
            continue
        runner_status = _read_status(runner_status_path)
        if runner_status.get("state") != "succeeded":
            reason = runner_status.get("reason", "unknown")
            issue = (
                f"reset {reset_id} worker state={runner_status.get('state')} "
                f"reason={reason}"
            )
            if reason == "output_validation_failed":
                invalid_issues.append(issue)
            else:
                crash_issues.append(issue)
            continue
        if not manifest_path.is_file():
            crash_issues.append(f"reset {reset_id} is missing reset_manifest.json")
            continue
        try:
            manifest = _read_json(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            invalid_issues.append(f"reset {reset_id} manifest unreadable: {error}")
            continue

        for key, expected in _expected_manifest_values(reset_id).items():
            actual = manifest.get(key)
            if actual != expected:
                invalid_issues.append(
                    f"reset {reset_id} manifest {key}={actual!r}, expected {expected!r}"
                )
        checkpoint_path = str(manifest.get("checkpoint_path", ""))
        if Path(checkpoint_path).name != CHECKPOINT_FILE:
            invalid_issues.append(
                f"reset {reset_id} checkpoint path is not the registered final checkpoint"
            )

        status = str(manifest.get("status", ""))
        if status not in status_counts:
            invalid_issues.append(f"reset {reset_id} has unknown status {status!r}")
        else:
            status_counts[status] += 1
        if status == "INVALID":
            invalid_issues.append(f"reset {reset_id} is scientifically INVALID")
        elif status == "EXCLUDED":
            incomplete_issues.append(f"reset {reset_id} was validly EXCLUDED")

        if status in {"OK", "EXCLUDED"}:
            for key in (
                "calibration_complete",
                "module_state_equal",
                "value_norm_state_equal",
                "loaded_value_norm_equal",
            ):
                if manifest.get(key) is not True:
                    invalid_issues.append(f"reset {reset_id} failed {key}")
            if status == "OK":
                if manifest.get("reference_act_low_parity_complete") is not True:
                    invalid_issues.append(
                        f"reset {reset_id} failed reference_act_low_parity_complete"
                    )
                try:
                    parity_error = float(
                        manifest.get(
                            "reference_act_low_parity_max_abs_error", float("inf")
                        )
                    )
                except (TypeError, ValueError):
                    parity_error = float("inf")
                if parity_error > 1e-6:
                    invalid_issues.append(
                        f"reset {reset_id} reference act_low parity exceeds 1e-6"
                    )
            artifact_name = str(manifest.get("artifact", ""))
            if artifact_name != f"reset_{reset_id:04d}.npz":
                invalid_issues.append(
                    f"reset {reset_id} artifact name mismatch: {artifact_name!r}"
                )
            else:
                artifact_path = output_dir / artifact_name
                if not artifact_path.is_file() or artifact_path.stat().st_size <= 0:
                    invalid_issues.append(
                        f"reset {reset_id} artifact is missing or empty"
                    )

        command = [
            python_bin,
            str(audit_script),
            "validate-reset",
            "--manifest",
            str(manifest_path),
            "--checkpoint-id",
            CHECKPOINT_ID,
            "--reset-id",
            str(reset_id),
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        validation_log.extend(
            [
                f"=== reset {reset_id} ===",
                completed.stdout.rstrip(),
                completed.stderr.rstrip(),
            ]
        )
        if completed.returncode != 0:
            invalid_issues.append(
                f"reset {reset_id} fresh validate-reset failed with exit "
                f"{completed.returncode}"
            )
            continue
        try:
            validation = _json_from_output(completed.stdout)
        except (ValueError, json.JSONDecodeError) as error:
            invalid_issues.append(f"reset {reset_id} validator output invalid: {error}")
            continue
        if validation.get("valid") is not True or validation.get(
            "scientific_status"
        ) != status:
            invalid_issues.append(f"reset {reset_id} validator result mismatch")
            continue
        validated_resets += 1
        try:
            observed_steps += int(manifest.get("environment_steps", 0))
        except (TypeError, ValueError):
            invalid_issues.append(f"reset {reset_id} environment_steps is not an integer")

    if crash_issues:
        state = "crash"
    elif invalid_issues:
        state = "INVALID"
    elif incomplete_issues:
        state = "INCOMPLETE"
    elif validated_resets == len(RESET_IDS) and observed_steps == ENVIRONMENT_STEPS_TOTAL:
        state = "WIRING_PASS"
    else:
        state = "INVALID"
        invalid_issues.append("pilot evidence did not meet the exact 8-reset/83,600-step contract")

    issues = crash_issues + invalid_issues + incomplete_issues
    summary: dict[str, Any] = {
        "state": state,
        "run_kind": RUN_KIND,
        "experiment_id": EXPERIMENT_ID,
        "scientific_status": "NOT_EVALUATED",
        "eligible_for_scientific_gate": False,
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_update": CHECKPOINT_UPDATE,
        "reset_ids": list(RESET_IDS),
        "reset_seeds": [reset_id + 1 for reset_id in RESET_IDS],
        "prefix_policy_seeds": list(PREFIX_POLICY_SEEDS),
        "prefix_steps": list(PREFIX_STEPS),
        "branches_per_reset": BRANCH_COUNT,
        "branch_steps": BRANCH_STEPS,
        "expected_resets": len(RESET_IDS),
        "validated_resets": validated_resets,
        "ok_resets": status_counts["OK"],
        "excluded_resets": status_counts["EXCLUDED"],
        "invalid_resets": status_counts["INVALID"],
        "environment_steps_expected": ENVIRONMENT_STEPS_TOTAL,
        "environment_steps_observed": observed_steps,
        "gate_a": "NOT_RUN",
        "gate_b": "NOT_RUN",
        "gate_c": "NOT_RUN",
        "issues": issues,
    }
    if state not in VALID_STATES:
        raise AssertionError(f"unexpected pilot state: {state}")
    return summary, "\n".join(line for line in validation_log if line) + "\n"


def write_outputs(run_root: Path, summary: dict[str, Any], validation_log: str) -> None:
    _atomic_write(
        run_root / "pilot_summary.json",
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
    )
    _atomic_write(run_root / "pilot_summary.md", _markdown(summary))
    _atomic_write(run_root / "pilot_validation_output.log", validation_log)
    status_lines = [
        f"state={summary['state']}",
        "scientific_status=NOT_EVALUATED",
        "eligible_for_scientific_gate=false",
        f"checkpoint_id={CHECKPOINT_ID}",
        f"expected_resets={len(RESET_IDS)}",
        f"validated_resets={summary['validated_resets']}",
        f"ok_resets={summary['ok_resets']}",
        f"excluded_resets={summary['excluded_resets']}",
        f"invalid_resets={summary['invalid_resets']}",
        f"environment_steps={summary['environment_steps_observed']}",
    ]
    _atomic_write(run_root / "pilot_status.txt", "\n".join(status_lines) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the quarantined R27-G2 eight-reset wiring pilot"
    )
    parser.add_argument("--run-root", required=True)
    parser.add_argument(
        "--audit-script",
        default=str(ROOT / "scripts" / "audit_r27_forced_trajectory_effect.py"),
    )
    parser.add_argument("--python-bin", default=sys.executable)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_root = Path(args.run_root)
    summary, validation_log = summarize(
        run_root,
        audit_script=Path(args.audit_script),
        python_bin=str(args.python_bin),
    )
    write_outputs(run_root, summary, validation_log)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return {
        "WIRING_PASS": 0,
        "INCOMPLETE": 3,
        "INVALID": 4,
        "crash": 5,
    }[str(summary["state"])]


if __name__ == "__main__":
    raise SystemExit(main())
