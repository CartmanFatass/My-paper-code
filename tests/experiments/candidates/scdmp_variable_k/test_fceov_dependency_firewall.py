from __future__ import annotations

import ast
import importlib
from pathlib import Path

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    contracts,
)


PACKAGE_ROOT = Path(
    "experiments/candidates/scdmp_variable_k/foundation_conditioned_event_order_value"
)
EXPECTED_MODULES = {
    "__init__",
    "__main__",
    "contracts",
    "rng",
    "foundation",
    "training",
    "host_bridge",
    "panel",
    "clock_controls",
    "analysis",
    "lifecycle",
    "artifacts",
    "source_manifest",
    "runner",
}
EXPECTED_LEGACY_IMPORTS = {
    "target_bound_competent_controller_order_value.config:ACTIONS,FORMATION_ROTATE,HOOK_HANDOFF",
    "target_bound_competent_controller_order_value.host_types:HostOutput,RenewalLane,ResetLane",
    "target_bound_competent_controller_order_value.native_backend:NativeBatch,test_only_primitive,test_only_setup_composition",
}


def _trees():
    return {
        path.stem: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for path in PACKAGE_ROOT.glob("*.py")
    }


def test_owned_surface_is_exactly_fourteen_modules_and_main_import_is_inert():
    assert {path.stem for path in PACKAGE_ROOT.glob("*.py")} == EXPECTED_MODULES
    module = importlib.import_module(
        "experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value.__main__"
    )
    assert callable(module.main)


def test_ast_legacy_imports_equal_the_direct_manifest_allowlist():
    by_module: dict[str, set[str]] = {}
    for tree in _trees().values():
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            if node.module.startswith("target_bound_competent_controller_order_value"):
                by_module.setdefault(node.module, set()).update(alias.name for alias in node.names)

    actual = {f"{module}:{','.join(sorted(names))}" for module, names in by_module.items()}

    manifest = contracts.Manifest()
    assert actual == EXPECTED_LEGACY_IMPORTS
    assert set(manifest.allowed_dependencies) == actual
    assert tuple(manifest.source_modules) == tuple(
        "__init__ __main__ contracts rng foundation training host_bridge panel "
        "clock_controls analysis lifecycle artifacts source_manifest runner".split()
    )


def test_old_selector_production_lifecycle_rng_result_and_gate_modules_are_firewalled():
    forbidden_fragments = {
        ".opportunity",
        ".production",
        ".production_services",
        ".lifecycle",
        ".rng",
        ".result",
        ".lease",
        ".empirical_contract",
        ".evaluation",
        ".inference",
        ".runner",
        ".artifacts",
        ".source_manifest",
    }
    legacy_imports = []
    for tree in _trees().values():
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(
                "target_bound_competent_controller_order_value"
            ):
                legacy_imports.append(node.module)
            elif isinstance(node, ast.Import):
                legacy_imports.extend(
                    alias.name
                    for alias in node.names
                    if "target_bound_competent_controller_order_value" in alias.name
                )
    assert all(not any(fragment in module for fragment in forbidden_fragments) for module in legacy_imports)
    assert set(contracts.Manifest().forbidden_dependencies) >= {
        f"target_bound_competent_controller_order_value{fragment}"
        for fragment in forbidden_fragments
    }


def test_hash_primitives_are_rng_only_and_no_auth_identity_lease_or_approval_gate_exists():
    banned_identifiers = {
        "approval",
        "authorization",
        "authorize",
        "credential",
        "digest",
        "identity",
        "lease",
        "permit",
    }
    for module, tree in _trees().items():
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        if module == "rng":
            assert {"hashlib", "hmac"} <= imports
        else:
            assert not {"hashlib", "hmac", "secrets", "uuid"} & imports

        identifiers = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                identifiers.add(node.name.lower())
            elif isinstance(node, ast.arg):
                identifiers.add(node.arg.lower())
            elif isinstance(node, ast.Name):
                identifiers.add(node.id.lower())
        assert not banned_identifiers & identifiers
