"""Direct FCEOV preflight with a scientifically held result command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

import torch

from .artifacts import (
    RESUME_WITNESS_SCHEMA, TERMINAL_FACT_SCHEMA, build_run_record, load_checkpoint,
    load_rng_master, observe_resume_equality, restore_checkpoint, write_checkpoint,
    write_foundation_gate, write_resume_witness, write_rng_master,
    write_run_record, write_terminal_fact,
)
from .contracts import CHECKPOINT_UPDATE, RESOURCE_MAXIMA, Disposition, TerminalFact
from .foundation import (
    analyze_competence, execute_native_competence, freeze_foundation, materialize_foundation,
    validate_competence_rng_contract,
)
from .host_bridge import headroom_conformance, verify_public_alias
from .panel import (
    build_native_resets, build_panel_inventory, execute_native_panel,
    materialize_disturbance_tapes, preflight_native_panel_session, validate_tape_pairing,
)
from .rng import AddressRNG, fresh_master
from .source_manifest import load_source_manifest, write_source_manifest
from .training import (
    ExactAdamW, build_training_plan, summarize_resource_usage, train_one_update,
    validate_training_rng_contract,
)


PHASE = "FOUNDATION_AND_2X3"


class PreflightError(RuntimeError):
    pass


class ScientificInferenceHold(RuntimeError):
    """The frozen 24-block Student-t rule lacks required finite-sample coverage."""

    code = "SCIENTIFIC_INFERENCE_HOLD"


def _configure_numerical_runtime() -> None:
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError as error:
        if torch.get_num_interop_threads() != 1:
            raise PreflightError("single-thread Torch inter-op control could not engage") from error
    torch.use_deterministic_algorithms(True)
    if (
        torch.get_num_threads() != 1
        or torch.get_num_interop_threads() != 1
        or not torch.are_deterministic_algorithms_enabled()
    ):
        raise PreflightError("deterministic single-thread Torch runtime controls did not engage")


def run_preflight(*, manifest: str | Path, result_root: str | Path) -> dict[str, object]:
    loaded = load_source_manifest(manifest)
    loaded.validate()
    root = Path(result_root)
    if root.exists():
        raise PreflightError("prospective result-root must not exist; it must be absent and fresh")
    parent = root.parent
    if not parent.exists() or not parent.is_dir():
        raise PreflightError("result-root parent does not exist")
    plan = build_training_plan()
    inventory = build_panel_inventory()
    validate_tape_pairing(inventory)
    resets = build_native_resets(inventory)
    training_rng = validate_training_rng_contract()
    competence_rng = validate_competence_rng_contract()
    alias = verify_public_alias()
    headroom = headroom_conformance()
    native_session_width = preflight_native_panel_session()
    resources = summarize_resource_usage()
    if resources != dict(loaded.resource_maxima):
        raise PreflightError("resource inventory differs from the direct manifest")
    if CHECKPOINT_UPDATE != 160:
        raise PreflightError("sole production checkpoint frontier drifted")
    return {
        "manifest": loaded.to_dict(),
        "training_episodes": len(plan),
        "panel_width": len(inventory),
        "reset_width": len(resets),
        "native_session_width": native_session_width,
        "public_alias": alias[0] == alias[1],
        "headroom": {
            "analytic_matched_load": headroom.analytic_witness.matched_load,
            "analytic_mismatched_load": headroom.analytic_witness.mismatched_load,
            "analytic_common_maximum_load": headroom.analytic_witness.common_maximum_load,
            "native_matched_exposure_zero": headroom.native_matched_exposure_zero,
            "native_mismatched_exposure": headroom.native_mismatched_exposure,
            "native_common_exposure_zero": headroom.native_common_exposure_zero,
        },
        "phase": PHASE,
        "checkpoint_update": CHECKPOINT_UPDATE,
        "resources": resources,
        "training_rng_addresses": training_rng,
        "competence_rng_addresses": competence_rng,
        "result_root_absent": True,
        "resolved_result_root": str(root.resolve()),
        "production_pipeline_implemented": True,
        "production_result_path_implemented": False,
        "result_command_status": "SCIENTIFIC_INFERENCE_HOLD",
        "scientific_inference_hold": True,
    }


def run_result(*, manifest: str | Path, result_root: str | Path) -> TerminalFact:
    """Preflight the exact phase, then stop before every result-bearing effect."""

    run_preflight(manifest=manifest, result_root=result_root)
    raise ScientificInferenceHold(
        "SCIENTIFIC_INFERENCE_HOLD: registered 24-block Student-t bound lacks finite-sample coverage"
    )


def _execute_result_pipeline(
    *, manifest: str | Path, result_root: str | Path
) -> TerminalFact:
    """Internal future pipeline; reruns direct preflight and is unreachable while held."""

    root = Path(result_root)
    report = run_preflight(manifest=manifest, result_root=root)
    if report.get("resources") != dict(RESOURCE_MAXIMA):
        raise PreflightError("internal execution resource report differs after direct preflight")
    _configure_numerical_runtime()
    root.mkdir(parents=False, exist_ok=False)
    write_source_manifest(root / "source-manifest.json")
    generated = fresh_master()
    write_rng_master(root / "rng-master.bin", generated)
    master = load_rng_master(root / "rng-master.bin")
    if master != generated:
        raise PreflightError("persisted RNG master differs immediately after creation")
    del generated
    write_run_record(
        root / "run-record.json",
        build_run_record(),
    )

    source = AddressRNG(master)
    uninterrupted_model = materialize_foundation(source)
    uninterrupted_optimizer = ExactAdamW(tuple(uninterrupted_model.named_parameters()))
    for update in range(1, 161):
        observed = train_one_update(uninterrupted_model, uninterrupted_optimizer, source, update=update)
        if observed.update != update or observed.episodes_complete != 12:
            raise PreflightError("foundation training update did not complete exactly")
    checkpoint_path = root / "foundation.checkpoint.pt"
    write_checkpoint(
        checkpoint_path, uninterrupted_model, uninterrupted_optimizer,
        completed_updates=CHECKPOINT_UPDATE, rng_master=master,
    )

    persisted = load_rng_master(root / "rng-master.bin")
    restored_source = AddressRNG(persisted)
    restored_model = materialize_foundation(restored_source)
    restored_optimizer = ExactAdamW(tuple(restored_model.named_parameters()))
    checkpoint = load_checkpoint(checkpoint_path, restored_model, restored_optimizer)
    restore_checkpoint(checkpoint, restored_model, restored_optimizer)
    witness = observe_resume_equality(
        checkpoint, uninterrupted_model, uninterrupted_optimizer, restored_model,
        restored_optimizer, persisted_master=persisted,
    )
    if witness.schema != RESUME_WITNESS_SCHEMA:
        raise PreflightError("resume witness schema differs")
    write_resume_witness(root / "resume-witness.json", witness)

    frozen = freeze_foundation(restored_model)
    records = execute_native_competence(frozen, restored_source)
    gate = analyze_competence(records)
    write_foundation_gate(root / "foundation-gate.json", gate, records)
    if not gate.passed:
        fact = TerminalFact(
            TERMINAL_FACT_SCHEMA, Disposition.FOUNDATION_NONPASS.value, gate, False,
        )
        write_terminal_fact(root / "terminal-fact.json", fact, competence_records=records)
        return fact

    tapes = materialize_disturbance_tapes(restored_source)
    cells = execute_native_panel(frozen, tapes)
    if len(cells) != 144 or any(not cell.terminal for cell in cells):
        raise PreflightError("raw native panel inventory is incomplete")
    raise ScientificInferenceHold(
        "SCIENTIFIC_INFERENCE_HOLD: raw 144-cell panel completed but registered "
        "24-block Student-t bound lacks finite-sample coverage"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scdmp-fceov")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--result-root", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--phase", choices=(PHASE,))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.preflight_only:
            report = run_preflight(manifest=args.manifest, result_root=args.result_root)
            print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
        else:
            fact = run_result(manifest=args.manifest, result_root=args.result_root)
            print(f"FCEOV terminal disposition: {fact.disposition}")
    except (ValueError, RuntimeError, OSError) as error:
        print(f"FCEOV stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "PHASE", "PreflightError", "ScientificInferenceHold", "main", "run_preflight", "run_result",
]
