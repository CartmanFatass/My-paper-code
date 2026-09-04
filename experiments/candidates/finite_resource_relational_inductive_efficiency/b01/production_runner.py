"""Pure formal full-512 planning boundary; this module performs no launch effects."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

from .contract import B01ContractError, validate_formal_source_gate, validate_manifest


_CAPACITY = 4
_BLOCKERS = [
    "FRESH_PER_WORKER_MEMORY_ADMISSION_NOT_YET_EXECUTED",
    "NATIVE_BUILD_LOAD_NOT_YET_EXECUTED",
    "FULL_512_TRAIN_EVAL_VALIDATION_NOT_YET_EXECUTED",
    "CREATE_ONCE_PANEL_PUBLICATION_NOT_YET_EXECUTED",
]


def _admission_namespace(manifest: Mapping[str, Any]) -> Path:
    output_root = Path(manifest["roots"]["output"]).resolve(strict=False)
    run_parent = output_root.parent
    return run_parent.with_name(run_parent.name + ".FRRIE_B01_ADMISSION").resolve(
        strict=False
    )


def _validate_run_parent(
    manifest: Mapping[str, Any], source_gate: Mapping[str, Any],
) -> Path:
    run_parent = Path(manifest["roots"]["output"]).resolve(strict=False).parent
    repository = Path(source_gate["repository"]).resolve(strict=False)
    anchor = Path(run_parent.anchor).resolve(strict=False)
    if (
        not run_parent.name or run_parent == anchor
        or repository == run_parent or repository.is_relative_to(run_parent)
    ):
        raise B01ContractError("formal production unsafe broad run parent")
    return run_parent


def _task(
    manifest: Mapping[str, Any], source_gate: Mapping[str, Any], seed_label: str,
) -> dict[str, Any]:
    roots = {name: Path(value).resolve(strict=False) for name, value in manifest["roots"].items()}
    output = (roots["output"] / seed_label).resolve(strict=False)
    checkpoint = (roots["checkpoint"] / seed_label).resolve(strict=False)
    scratch = (roots["scratch"] / seed_label).resolve(strict=False)
    locators = {
        "output": str(output),
        "checkpoint": str(checkpoint),
        "scratch": str(scratch),
        "planned_future_admission_receipt": str(
            (_admission_namespace(manifest) / f"{seed_label}.json").resolve(strict=False)
        ),
        "creating": str((roots["output"] / f"{seed_label}.creating").resolve(strict=False)),
        "incomplete": str((roots["output"] / f"{seed_label}.incomplete").resolve(strict=False)),
        "quarantine": str((roots["output"] / f"{seed_label}.quarantine").resolve(strict=False)),
    }
    repository = Path(source_gate["repository"]).resolve(strict=False)
    admission_argv = [
        str(Path(sys.executable).resolve(strict=True)),
        str((repository / "scripts" / "hmasd_resource_preflight.py").resolve(strict=True)),
        "admit-memory", "--out", locators["planned_future_admission_receipt"],
    ]
    return {
        "schema": "FRRIE_B01_PLANNED_FORMAL_SEED_WORKER_V1",
        "seed_label": seed_label,
        "planned_identity": {
            "label": f"FRRIE-B01-FORMAL-{manifest['phase']}-{seed_label}",
            "authoritative": False, "actual_invocation_id": None,
            "future_worker_must_mint_and_bind_actual_id": True,
        },
        "operation": "FULL_512_TRAIN_EVAL_VALIDATE_PUBLISH",
        "locators": locators,
        "worker_local_fresh_admission_required": True,
        "fresh_admission_argv": admission_argv,
        "future_execution_requires_shell_false": True,
        "fresh_admission_order_contract": {
            "sequence": [
                "WORKER_START", "FRESH_ADMIT_MEMORY_RECEIPT",
                "NO_INTERVENING_EFFECT", "FIRST_FUTURE_RUNTIME_OR_EFFECT",
            ],
            "precedes": [
                "NATIVE_BUILD_LOAD", "RNG_MASTER_CREATE",
                "PAIRED_MODEL_OPTIMIZER_CREATE_OR_RESTORE", "ROOT_OR_RESULT_CREATE",
                "CHECKPOINT_WRITE_OR_RESTORE",
            ],
        },
        "receipt_exists_or_was_read": False,
        "launch_capable": False,
        "result_bearing": False,
        "effect_count": 0,
    }


def _validate_plan(plan: Any, manifest: Mapping[str, Any]) -> dict[str, Any]:
    fields = {
        "schema", "phase", "manifest_code_revision", "source_gate", "seed_order",
        "capacity", "planned_worker_count", "workers", "admission_namespace", "launch_capable",
        "production_token_minted", "result_bearing", "effect_count",
        "residual_downstream_blockers",
    }
    if not isinstance(plan, Mapping) or set(plan) != fields:
        raise B01ContractError("formal production plan fields differ")
    value = dict(plan)
    seed_order = list(manifest["execution_labels"])
    if (
        value["schema"] != "FRRIE_B01_FORMAL_PRODUCTION_PLAN_V1"
        or value["phase"] != manifest["phase"]
        or value["manifest_code_revision"] != manifest["code_revision"]
        or value["seed_order"] != seed_order
        or value["capacity"] != _CAPACITY
        or value["planned_worker_count"] != len(seed_order)
        or value["planned_worker_count"] > value["capacity"]
        or value["admission_namespace"] != {
            "path": str(_admission_namespace(manifest)),
            "created_by_plan": False,
            "later_lifecycle_owns_cleanup_or_archive": True,
            "ownership_scope": "ONLY_THIS_EXACT_ADMISSION_NAMESPACE",
        }
        or value["launch_capable"] is not False
        or value["production_token_minted"] is not False
        or value["result_bearing"] is not False
        or value["effect_count"] != 0
        or value["residual_downstream_blockers"] != _BLOCKERS
        or not isinstance(value["source_gate"], Mapping)
        or value["source_gate"].get("complete") is not True
    ):
        raise B01ContractError("formal production plan identity/claim ceiling differs")
    if not isinstance(value["workers"], list) or len(value["workers"]) != len(seed_order):
        raise B01ContractError("formal production worker inventory differs")

    roots = {name: Path(path).resolve(strict=False) for name, path in manifest["roots"].items()}
    run_parent = _validate_run_parent(manifest, value["source_gate"])
    admission_namespace = _admission_namespace(manifest)
    planned_receipts = [
        admission_namespace / f"{seed_label}.json" for seed_label in seed_order
    ]
    if any(path.exists() for path in planned_receipts):
        raise B01ContractError("formal production planned admission receipt is not fresh")
    if (
        admission_namespace.parent != run_parent.parent
        or admission_namespace.is_relative_to(run_parent)
        or admission_namespace.exists()
    ):
        raise B01ContractError("formal production admission namespace is not fresh/outside run")
    seen: set[Path] = set()
    task_fields = {
        "schema", "seed_label", "planned_identity", "operation", "locators",
        "worker_local_fresh_admission_required", "fresh_admission_argv",
        "future_execution_requires_shell_false", "fresh_admission_order_contract",
        "receipt_exists_or_was_read",
        "launch_capable", "result_bearing", "effect_count",
    }
    locator_fields = {
        "output", "checkpoint", "scratch", "planned_future_admission_receipt",
        "creating", "incomplete", "quarantine",
    }
    for seed_label, worker in zip(seed_order, value["workers"]):
        if not isinstance(worker, Mapping) or set(worker) != task_fields:
            raise B01ContractError("formal production worker fields differ")
        expected = _task(manifest, value["source_gate"], seed_label)
        if dict(worker) != expected or set(worker["locators"]) != locator_fields:
            raise B01ContractError("formal production worker derivation differs")
        for name, literal in worker["locators"].items():
            path = Path(literal)
            root_name = "checkpoint" if name == "checkpoint" else "scratch" if name == "scratch" else "output"
            contained = (
                path.is_relative_to(admission_namespace)
                if name == "planned_future_admission_receipt"
                else path.is_relative_to(roots[root_name])
            )
            if (
                not path.is_absolute() or not contained
                or path in seen or path.exists()
            ):
                raise B01ContractError("formal production derived locator is not fresh/distinct")
            seen.add(path)
    return value


def construct_formal_production_plan(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate actual source state and return a deterministic zero-effect plan."""

    source_gate = validate_formal_source_gate(manifest)
    manifest0 = validate_manifest(manifest)
    _validate_run_parent(manifest0, source_gate)
    seed_order = list(manifest0["execution_labels"])
    plan = {
        "schema": "FRRIE_B01_FORMAL_PRODUCTION_PLAN_V1",
        "phase": manifest0["phase"],
        "manifest_code_revision": manifest0["code_revision"],
        "source_gate": source_gate,
        "seed_order": seed_order,
        "capacity": _CAPACITY,
        "planned_worker_count": len(seed_order),
        "workers": [
            _task(manifest0, source_gate, seed_label) for seed_label in seed_order
        ],
        "admission_namespace": {
            "path": str(_admission_namespace(manifest0)),
            "created_by_plan": False,
            "later_lifecycle_owns_cleanup_or_archive": True,
            "ownership_scope": "ONLY_THIS_EXACT_ADMISSION_NAMESPACE",
        },
        "launch_capable": False,
        "production_token_minted": False,
        "result_bearing": False,
        "effect_count": 0,
        "residual_downstream_blockers": list(_BLOCKERS),
    }
    return _validate_plan(plan, manifest0)
