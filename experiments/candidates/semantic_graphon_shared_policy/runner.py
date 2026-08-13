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
    print(json.dumps({
        "revision": certificate["revision"], "passed": certificate["passed"],
        "output": str(args.output.resolve()),
    }, sort_keys=True))
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
    from .artifacts import require_exact_certificate
    from .authorization import load_production_permit

    require_exact_certificate(args.certificate)
    return load_production_permit(
        args.authorization, args.result_root, args.certificate,
    )


def _init_result_command(args: argparse.Namespace) -> int:
    permit = _gated_inputs(args)
    authorization = permit.payload
    from .artifacts import create_fresh_result_root

    create_fresh_result_root(args.result_root, args.certificate, {
        "lease_token_sha256": _token_digest(authorization["lease_token"]),
        "stage_boundary": authorization["stage_boundary"],
        "issued_at_utc": authorization["issued_at_utc"],
        "not_after_utc": authorization["not_after_utc"],
        "authorized_seeds": authorization["authorized_seeds"],
        "cumulative_wall_clock_cap_hours": authorization["cumulative_wall_clock_cap_hours"],
    })
    return 0


def _run_seed_command(args: argparse.Namespace) -> int:
    permit = _gated_inputs(args)
    authorization = permit.payload
    _configure_single_cpu()
    from .artifacts import (
        validate_certificate_binding,
        validate_lease_binding,
        validate_result_root,
        write_atomic_seed_packet,
    )
    from .audits import deterministic_checkpoint_dense_audit, structural_checkpoint_audit
    from .config import ARMS, REVISION, SEEDS
    from .evaluation import evaluate_seed
    from .training import train_seed

    if args.seed not in SEEDS:
        raise ValueError("seed is not in the frozen 16-seed registry")
    permit.require_seed(args.seed)
    validate_result_root(args.result_root)
    validate_certificate_binding(args.result_root, args.certificate)
    validate_lease_binding(args.result_root, authorization)
    if (args.result_root / f"seed-{args.seed}").exists():
        raise FileExistsError(f"registered seed may not be replaced: {args.seed}")
    permit.assert_active()
    trained = train_seed(permit, args.seed, progress_guard=permit.assert_active)
    evaluation = evaluate_seed(
        permit, args.seed, trained.models, progress_guard=permit.assert_active,
    )
    permit.assert_active()
    dense_audit = deterministic_checkpoint_dense_audit(trained.models)
    structural_audit = structural_checkpoint_audit(trained.models)
    packet: dict[str, object] = {
        "revision": REVISION,
        "seed": args.seed,
        "arms": list(ARMS),
        "training": trained.metadata,
        "evaluation": evaluation,
        "dense_reference_audit": dense_audit,
        "structural_checkpoint_audit": structural_audit,
        "production_lease_token_sha256": _token_digest(authorization["lease_token"]),
        "checkpoint_identity": "only_evaluable_state_immediately_after_update_480",
        "worlds_and_agents_are_inferential_replicates": False,
        "seed_is_inferential_unit": True,
        "atomic_payload_complete": True,
    }
    permit.assert_active()
    write_atomic_seed_packet(args.result_root, args.seed, trained.models, packet)
    return 0


def _analyze_command(args: argparse.Namespace) -> int:
    permit = _gated_inputs(args)
    from .artifacts import (
        load_complete_seed_packet,
        validate_certificate_binding,
        validate_lease_binding,
    )
    from .config import REVISION, SEEDS
    from .statistics import analyze_packets

    validate_certificate_binding(args.result_root, args.certificate)
    validate_lease_binding(args.result_root, permit.payload)
    if args.output.exists():
        raise FileExistsError(f"analysis output must be fresh: {args.output}")
    packets = [load_complete_seed_packet(args.result_root, seed) for seed in SEEDS]
    result = analyze_packets(packets)
    result.update({"revision": REVISION, "seed_order": list(SEEDS)})
    _write_json_atomic(args.output, result)
    return 0 if result["hard_structural_validity"] else 2


def _formal_run_command(args: argparse.Namespace) -> int:
    """Fresh all-seed production command; unavailable without one full Root lease."""
    permit = _gated_inputs(args)
    from .config import SEEDS

    if permit.payload["authorized_seeds"] != list(SEEDS):
        raise PermissionError(
            "formal-run requires all 16 registered seeds in exact frozen order"
        )
    _init_result_command(args)
    for seed in SEEDS:
        seed_args = argparse.Namespace(**vars(args))
        seed_args.seed = seed
        result = _run_seed_command(seed_args)
        if result != 0:
            return result
    analysis_args = argparse.Namespace(**vars(args))
    analysis_args.output = args.result_root / "analysis.json"
    return _analyze_command(analysis_args)


def _add_gated_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="semantic_graphon_shared_policy",
        description="SGSP B1 rev05; no default action and all stochastic paths fail closed.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    certificate = subparsers.add_parser(
        "certificate", help="static source and hand-written deterministic fixture audit only",
    )
    certificate.add_argument("--output", type=Path, required=True)
    certificate.set_defaults(handler=_certificate_command)

    resources = subparsers.add_parser("resource-proposal", help="static resource projection only")
    resources.add_argument("--output", type=Path)
    resources.set_defaults(handler=_resource_command)

    initialize = subparsers.add_parser("init-result", help="create fresh lease-bound result root")
    _add_gated_arguments(initialize)
    initialize.set_defaults(handler=_init_result_command)

    run_seed = subparsers.add_parser("run-seed", help="formal train/evaluate one registered seed")
    _add_gated_arguments(run_seed)
    run_seed.add_argument("--seed", type=int, required=True)
    run_seed.set_defaults(handler=_run_seed_command)

    analyze = subparsers.add_parser("analyze", help="analyze exactly 16 complete atomic packets")
    _add_gated_arguments(analyze)
    analyze.add_argument("--output", type=Path, required=True)
    analyze.set_defaults(handler=_analyze_command)

    formal_run = subparsers.add_parser(
        "formal-run",
        help="fresh exact 16-seed train/evaluate/analyze run under one Root lease",
    )
    _add_gated_arguments(formal_run)
    formal_run.set_defaults(handler=_formal_run_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, FileExistsError, PermissionError, RuntimeError, ValueError) as error:
        print(f"FAIL_CLOSED: {error}", file=sys.stderr)
        return 2
