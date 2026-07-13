#!/usr/bin/env python
"""Analyze the frozen R28-G0 action-process target on R27-G2 shards."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from ha_ctse_process.r27_g2_runtime import configure_deterministic_cuda  # noqa: E402
from ha_ctse_process.r28_g0_target import (  # noqa: E402
    CHECKPOINT_IDS,
    EXPERIMENT_ID,
    REGISTERED_CHECKPOINTS,
    SCIENTIFIC_CONTRACT,
    EvidenceError,
    analyze_dataset,
    build_dataset,
    classify_family,
    jsonable,
    load_actor_base,
    read_checkpoint_shards,
    scorer_payload,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _checkpoint_path(checkpoint_root: Path, checkpoint_id: str) -> Path:
    registered = REGISTERED_CHECKPOINTS[checkpoint_id]["path"]
    suffix = Path(registered)
    if suffix.parts and suffix.parts[0].lower() == "dist":
        suffix = Path(*suffix.parts[1:])
    return checkpoint_root / suffix


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R28-G0 Action-Process Target Calibration",
        "",
        f"- Family status: `{report.get('status')}`",
        f"- Classification: `{report.get('classification')}`",
        f"- R27 run root: `{report.get('r27_run_root')}`",
        f"- Device: `{report.get('device')}`",
        "",
        "## Checkpoints",
        "",
    ]
    for checkpoint in report.get("checkpoints", []):
        reasons = checkpoint.get("reasons") or []
        lines.extend(
            [
                f"### {checkpoint.get('checkpoint_id')}",
                "",
                f"- Status: `{checkpoint.get('status')}`",
                f"- Classification: `{checkpoint.get('classification')}`",
                f"- Reasons: {', '.join(reasons) if reasons else 'none'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "This offline diagnostic performs zero environment steps and zero policy updates. A PASS permits only focused implementation review for a later reward package; it does not authorize reward launch.",
            "",
        ]
    )
    return "\n".join(lines)


def run_analyze(args: argparse.Namespace) -> dict[str, Any]:
    if str(args.device).lower() != "cuda":
        raise EvidenceError("R28-G0 requires DEVICE=cuda; CPU fallback is forbidden")
    configure_deterministic_cuda(args.device)
    r27_run_root = Path(args.r27_run_root)
    checkpoint_root = Path(args.checkpoint_root)
    output_dir = Path(args.output_dir)
    checkpoint_reports: list[dict[str, Any]] = []
    checkpoint_results = []
    for checkpoint_id in CHECKPOINT_IDS:
        checkpoint_path = _checkpoint_path(checkpoint_root, checkpoint_id)
        if not checkpoint_path.is_file() or checkpoint_path.stat().st_size <= 0:
            raise FileNotFoundError(checkpoint_path)
        actor_base = load_actor_base(checkpoint_path, args.device)
        artifacts, manifests, shard_failures = read_checkpoint_shards(
            r27_run_root, checkpoint_id
        )
        if shard_failures:
            checkpoint_report = {
                "checkpoint_id": checkpoint_id,
                "status": "INVALID",
                "classification": "INVALID",
                "reasons": list(shard_failures),
                "support": {},
                "metrics": {},
            }
            checkpoint_reports.append(checkpoint_report)
            continue
        dataset, support, dataset_failures = build_dataset(
            checkpoint_id,
            artifacts,
            manifests,
            actor_base=actor_base,
            device=args.device,
        )
        if dataset_failures or dataset is None:
            checkpoint_report = {
                "checkpoint_id": checkpoint_id,
                "status": "INVALID",
                "classification": "INVALID",
                "reasons": list(dataset_failures),
                "support": support,
                "metrics": {},
            }
            checkpoint_reports.append(checkpoint_report)
            continue
        result = analyze_dataset(dataset, device=args.device)
        checkpoint_results.append(result)
        checkpoint_reports.append(
            {
                "checkpoint_id": checkpoint_id,
                "status": result.status,
                "classification": result.classification,
                "reasons": list(result.reasons),
                "support": result.support,
                "q_full": result.q_full,
                "q_context": result.q_context,
                "q_pre": result.q_pre,
                "metrics": result.metrics,
            }
        )
    if len(checkpoint_results) == 3:
        status, classification = classify_family(checkpoint_results)
    else:
        status, classification = "INVALID", "INVALID"
    report: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "classification": classification,
        "device": str(args.device),
        "r27_run_root": str(r27_run_root),
        "checkpoint_root": str(checkpoint_root),
        "scientific_contract": SCIENTIFIC_CONTRACT,
        "checkpoints": checkpoint_reports,
        "scorer": None,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    if status == "PASS":
        final_result = next(
            item for item in checkpoint_results if item.checkpoint_id == "arm0_final"
        )
        scorer = scorer_payload(final_result)
        scorer_path = output_dir / "r28_g0_scorer_final.pt"
        torch.save(scorer, scorer_path)
        report["scorer"] = str(scorer_path)
    json_path = output_dir / "r28_g0_action_process_target.json"
    md_path = output_dir / "r28_g0_action_process_target.md"
    _write_json(json_path, report)
    md_path.write_text(_markdown(report), encoding="utf-8")
    return {
        "valid": True,
        "scientific_status": status,
        "classification": classification,
        "json": str(json_path),
        "markdown": str(md_path),
        "scorer": report["scorer"],
    }


def run_validate_result(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    json_path = output_dir / "r28_g0_action_process_target.json"
    md_path = output_dir / "r28_g0_action_process_target.md"
    report = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise EvidenceError("R28-G0 report is not a JSON object")
    if md_path.read_text(encoding="utf-8") != _markdown(report):
        raise EvidenceError("R28-G0 Markdown report does not match JSON")
    if report.get("experiment_id") != EXPERIMENT_ID:
        raise EvidenceError("R28-G0 experiment identity mismatch")
    if report.get("scientific_contract") != SCIENTIFIC_CONTRACT:
        raise EvidenceError("R28-G0 scientific contract mismatch")
    status = str(report.get("status"))
    classification = str(report.get("classification"))
    valid_pairs = {
        ("PASS", "PASS_TARGET_NULLS"),
        ("FAIL", "FAIL_TARGET"),
        ("MIXED", "MIXED_TARGET"),
        ("UNDERPOWERED", "UNDERPOWERED"),
        ("INVALID", "INVALID"),
    }
    if (status, classification) not in valid_pairs:
        raise EvidenceError("R28-G0 status/classification pair is invalid")
    checkpoints = report.get("checkpoints")
    if not isinstance(checkpoints, list) or [
        item.get("checkpoint_id") for item in checkpoints if isinstance(item, dict)
    ] != list(CHECKPOINT_IDS):
        raise EvidenceError("R28-G0 checkpoint inventory/order mismatch")
    scorer = report.get("scorer")
    if status == "PASS":
        if not isinstance(scorer, str) or not Path(scorer).is_file():
            raise EvidenceError("R28-G0 PASS is missing final scorer")
    elif scorer not in (None, ""):
        raise EvidenceError("R28-G0 non-PASS must not carry a scorer")
    return {
        "valid": True,
        "scientific_status": status,
        "classification": classification,
        "json": str(json_path),
        "markdown": str(md_path),
        "scorer": scorer,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="R28-G0 offline target calibration")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--r27-run-root", required=True)
    analyze.add_argument("--checkpoint-root", default="dist")
    analyze.add_argument("--output-dir", required=True)
    analyze.add_argument("--device", default="cuda")
    validate = subparsers.add_parser("validate-result")
    validate.add_argument("--output-dir", required=True)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main() -> None:
    args = parse_args()
    if args.command == "analyze":
        result = run_analyze(args)
    else:
        result = run_validate_result(args)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
