"""CLI lifecycle shell; every production-bearing path is Root-lease gated."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

_TORCH_SINGLE_CPU_CONFIGURED = False


def _configure_single_cpu() -> None:
    global _TORCH_SINGLE_CPU_CONFIGURED
    if _TORCH_SINGLE_CPU_CONFIGURED:
        return
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    _TORCH_SINGLE_CPU_CONFIGURED = True


def _token_digest(token: object) -> str:
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _certificate_command(args: argparse.Namespace) -> int:
    from .certificate import write_certificate
    certificate = write_certificate(args.output)
    print(json.dumps({"revision": certificate["revision"], "passed": certificate["passed"], "output": str(args.output.resolve())}, sort_keys=True))
    return 0 if certificate["passed"] else 2


def _resource_command(args: argparse.Namespace) -> int:
    from .resources import resource_proposal
    proposal = resource_proposal()
    if args.output is None:
        print(json.dumps(proposal, indent=2, sort_keys=True))
    else:
        _write_json_atomic(args.output, proposal)
    return 0


def _gated_inputs(args: argparse.Namespace):
    from .authorization import load_production_permit
    return load_production_permit(args.authorization, args.result_root, args.certificate)


def _lease_binding(authorization: dict[str, object]) -> dict[str, object]:
    from .authorization import ACTION
    from .config import COUNTER_ROOT, DIRECTION, REVISION
    return {
        "lease_token_sha256": _token_digest(authorization["lease_token"]),
        "stage_boundary": authorization["stage_boundary"],
        "direction": DIRECTION, "revision": REVISION, "action": ACTION,
        "result_root": authorization["result_root"],
        "issued_at_utc": authorization["issued_at_utc"],
        "not_after_utc": authorization["not_after_utc"],
        "authorized_seeds_at_initialization": authorization["authorized_seeds"],
        "counter_root": COUNTER_ROOT,
        "device": authorization["device"],
        "certificate_sha256": authorization["certificate_sha256"],
    }


def _init_result_command(args: argparse.Namespace) -> int:
    permit = _gated_inputs(args)
    from .artifacts import create_fresh_result_root
    create_fresh_result_root(args.result_root, permit, args.certificate)
    return 0


def _run_seed_command(args: argparse.Namespace) -> int:
    permit = _gated_inputs(args)
    _configure_single_cpu()
    from .artifacts import validate_certificate_binding, validate_lease_binding, validate_result_root, write_atomic_seed_packet
    from .audits import deterministic_checkpoint_audit, structural_checkpoint_audit
    from .authorization import ACTION, ARMS
    from .config import REVISION, SEEDS
    from .evaluation import evaluate_seed
    from .training import train_complete_pair
    if args.seed not in SEEDS:
        raise ValueError("seed is not in the frozen 24-seed registry")
    permit.require_seed(args.seed)
    validate_result_root(args.result_root)
    validate_certificate_binding(args.result_root, args.certificate)
    validate_lease_binding(args.result_root, permit.payload)
    if (args.result_root / f"seed-{args.seed}").exists():
        raise FileExistsError(f"registered seed may not be replaced: {args.seed}")
    permit.assert_active()
    trained = train_complete_pair(
        permit, args.seed, args.result_root, args.certificate
    )
    models = {"PHY-TRUST": trained.phy_trust, "EDGE-FLEX": trained.edge_flex}
    evaluation = evaluate_seed(permit, args.seed, models, progress_guard=permit.assert_active)
    permit.assert_active()
    packet: dict[str, object] = {
        "revision": REVISION, "action": ACTION, "seed": args.seed, "arms": list(ARMS),
        "training": trained.metadata, "evaluation": evaluation,
        "deterministic_checkpoint_audit": deterministic_checkpoint_audit(models),
        "structural_checkpoint_audit": structural_checkpoint_audit(models),
        "production_lease_token_sha256": _token_digest(permit.payload["lease_token"]),
        "checkpoint_identity": "only_evaluable_state_immediately_after_update_512",
        "worlds_and_agents_are_inferential_replicates": False,
        "seed_is_inferential_unit": True,
        "atomic_payload_complete": True,
    }
    permit.assert_active()
    write_atomic_seed_packet(args.result_root, permit, args.certificate, args.seed, models, packet)
    return 0


def _analyze_command(args: argparse.Namespace) -> int:
    permit = _gated_inputs(args)
    from .artifacts import load_complete_seed_packet, validate_certificate_binding, validate_lease_binding
    from .authorization import ACTION
    from .config import REVISION, SEEDS
    from .statistics import analyze_packets
    if permit.payload["authorized_seeds"] != list(SEEDS):
        raise PermissionError("analysis requires authorization for the exact complete 24-seed panel")
    validate_certificate_binding(args.result_root, args.certificate)
    validate_lease_binding(args.result_root, permit.payload)
    if args.output.exists():
        raise FileExistsError(f"analysis output must be fresh: {args.output}")
    packets = [load_complete_seed_packet(args.result_root, permit, args.certificate, seed) for seed in SEEDS]
    result = analyze_packets(packets)
    result.update({"revision": REVISION, "action": ACTION, "seed_order": list(SEEDS), "complete_panel": True})
    _write_json_atomic(args.output, result)
    return 0 if result["hard_structural_validity"] else 2


def _formal_run_command(args: argparse.Namespace) -> int:
    permit = _gated_inputs(args)
    from .config import SEEDS
    if permit.payload["authorized_seeds"] != list(SEEDS):
        raise PermissionError("formal-run requires the exact complete 24-seed panel")
    _init_result_command(args)
    for seed in SEEDS:
        seed_args = argparse.Namespace(**vars(args))
        seed_args.seed = seed
        if _run_seed_command(seed_args) != 0:
            return 2
    analysis_args = argparse.Namespace(**vars(args))
    analysis_args.output = args.result_root / "analysis.json"
    return _analyze_command(analysis_args)


def _add_gated_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="semantic_graphon_shared_policy_rg2z_r03", description="RG2Z r03 update-512 panel; all production paths fail closed.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    certificate = subparsers.add_parser("certificate", help="static/preactivity audit only")
    certificate.add_argument("--output", type=Path, required=True)
    certificate.set_defaults(handler=_certificate_command)
    resources = subparsers.add_parser("resource-proposal", help="static cost proposal only")
    resources.add_argument("--output", type=Path)
    resources.set_defaults(handler=_resource_command)
    initialize = subparsers.add_parser("init-result", help="create a fresh lease-bound result root")
    _add_gated_arguments(initialize); initialize.set_defaults(handler=_init_result_command)
    run_seed = subparsers.add_parser("run-seed", help="run one exact registered seed")
    _add_gated_arguments(run_seed); run_seed.add_argument("--seed", type=int, required=True); run_seed.set_defaults(handler=_run_seed_command)
    analyze = subparsers.add_parser("analyze", help="analyze all 24 complete atomic packets")
    _add_gated_arguments(analyze); analyze.add_argument("--output", type=Path, required=True); analyze.set_defaults(handler=_analyze_command)
    formal_run = subparsers.add_parser("formal-run", help="fresh complete 24-seed train/evaluate/analyze run")
    _add_gated_arguments(formal_run); formal_run.set_defaults(handler=_formal_run_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, FileExistsError, PermissionError, RuntimeError, ValueError, KeyError, TypeError) as error:
        print(f"FAIL_CLOSED: {error}", file=sys.stderr)
        return 2
