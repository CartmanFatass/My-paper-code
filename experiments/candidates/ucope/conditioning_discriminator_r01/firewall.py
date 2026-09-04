"""Static import and runtime-path firewall for historical UCOPE artifacts."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

FORBIDDEN_IMPORT_PREFIXES = (
    "experiments.candidates.ucope.competence_first_scout_r01",
    "experiments.candidates.ucope.contextual_paid_acquisition_r01",
    "experiments.candidates.ucope.structural_competence",
    "experiments.candidates.ucope.variable_k_paid_probe_r01_r03",
)
FORBIDDEN_RUNTIME_PARTS = (
    "ucope-scout-r01-b1-",
    "ucope/contextual_paid_acquisition",
    "ucope\\contextual_paid_acquisition",
    "ucope-structural-competence",
)


def validate_import_firewall(paths: Iterable[str | Path]) -> dict[str, object]:
    paths = tuple(paths)
    imports = []
    for path_value in paths:
        path = Path(path_value)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module: imports.append(node.module)
    forbidden = [name for name in imports if name.startswith(FORBIDDEN_IMPORT_PREFIXES)]
    if forbidden:
        raise ValueError(f"historical UCOPE import forbidden: {forbidden}")
    return {"source_files": len(paths), "imports_checked": len(imports), "historical_imports": 0}


def validate_runtime_path(path: str | Path) -> Path:
    resolved = Path(path).resolve()
    lowered = str(resolved).lower()
    if any(token in lowered for token in FORBIDDEN_RUNTIME_PARTS):
        raise ValueError("historical UCOPE runtime path is forbidden")
    return resolved


def zero_effect_ledger() -> dict[str, int]:
    return {
        "old_b1_runtime_reads": 0, "old_odd_audit_runtime_reads": 0,
        "consumed_belief_runtime_reads": 0, "structural_runtime_reads": 0,
        "historical_r03_runtime_reads": 0, "acquisition_evaluations": 0,
        "count_raw_effects": 0, "checkpoint_selections": 0,
        "budget_adaptations": 0, "network_provider_effects": 0,
        "portfolio_effects": 0,
    }
