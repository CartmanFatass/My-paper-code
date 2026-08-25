"""Fresh r06 binding to retained create-only lifecycle semantics."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_lifecycle import (
    BINDING_COMPONENTS as R05_BINDING_COMPONENTS,
    ProductionLifecycleError,
    run_real_byte_lifecycle_seam as _retained_real_byte_seam,
    append_generation as _append_generation,
)
from .production_contract import TestAuthority


BINDING_COMPONENTS = tuple(
    "evaluation_population_frontier" if name == "accepted_tape_frontier" else name
    for name in R05_BINDING_COMPONENTS
)


def run_r06_real_byte_lifecycle_seam(
    root: Path,
    component_bytes: Mapping[str, bytes],
    authority: TestAuthority,
) -> dict[str, object]:
    authority.require_test_only()
    if tuple(sorted(component_bytes)) != tuple(sorted(BINDING_COMPONENTS)):
        raise ProductionLifecycleError("r06 lifecycle component inventory differs")
    retained = {
        ("accepted_tape_frontier" if name == "evaluation_population_frontier" else name): payload
        for name, payload in component_bytes.items()
    }
    result = _retained_real_byte_seam(root, retained)
    remapped = {
        ("evaluation_population_frontier" if name == "accepted_tape_frontier" else name): digest
        for name, digest in result["component_sha256"].items()
    }
    return {
        **result,
        "schema": "DISH_RBHR_R06_REAL_BYTE_LIFECYCLE_SEAM_V1",
        "component_sha256": remapped,
        "fresh_r06_identity": False,
        "r06_checkpoint_created": False,
        "r06_activity": False,
    }


def lifecycle_binding_manifest() -> dict[str, object]:
    encoded = ("\n".join(BINDING_COMPONENTS) + "\n").encode("ascii")
    return {
        "schema": "DISH_RBHR_R06_LIFECYCLE_BINDING_MANIFEST_V1",
        "component_count": len(BINDING_COMPONENTS),
        "components": list(BINDING_COMPONENTS),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "create_only": True,
        "same_identity_resume": True,
        "test_only": True,
    }


def open_production_lifecycle(root: Path, *, identity_sha256: str, components: Mapping[str, str]) -> dict[str, object]:
    if len(identity_sha256) != 64 or tuple(sorted(components)) != tuple(sorted(BINDING_COMPONENTS)):
        raise ProductionLifecycleError("production lifecycle identity/components differ")
    retained = {
        ("accepted_tape_frontier" if name == "evaluation_population_frontier" else name): digest
        for name, digest in components.items()
    }
    return _append_generation(root, job_id=identity_sha256, generation=0, parent_sha256=None, components=retained)


def resume_full_panel(
    root: Path, *, identity_sha256: str, generation: int,
    parent_sha256: str, components: Mapping[str, str],
) -> dict[str, object]:
    if generation <= 0:
        raise ProductionLifecycleError("resume generation must be positive")
    retained = {
        ("accepted_tape_frontier" if name == "evaluation_population_frontier" else name): digest
        for name, digest in components.items()
    }
    return _append_generation(root, job_id=identity_sha256, generation=generation, parent_sha256=parent_sha256, components=retained)


__all__ = [
    "BINDING_COMPONENTS", "ProductionLifecycleError", "lifecycle_binding_manifest",
    "open_production_lifecycle", "resume_full_panel", "run_r06_real_byte_lifecycle_seam",
]
