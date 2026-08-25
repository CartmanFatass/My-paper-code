"""Read-only Stage-1 status/proof entry for VSP06-B2R2.

The only command runs synthetic structural checks and reports reserved-path
absence.  This script has no canonical preparation, selector, verifier,
manifest, environment, learner, full, result, or readiness-output command.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.vsp_06_mssr import (  # noqa: E402
    vsp06_b2r2_authenticated_partner_recall_credit_efficiency as experiment,
)
from experiments.candidates.vsp_06_mssr import (  # noqa: E402
    vsp06_b2r2_independent_exact_manifest_verifier as independent,
)
from experiments.candidates.vsp_06_mssr import (  # noqa: E402
    vsp06_b2r2_source_bound_symmetry_guaranteed_exact_feasibility as generator,
)


def _dependency_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _envelope(emission: generator.SyntheticEmission) -> dict[str, Any]:
    return {
        "tuple": dict(emission.tuple_value),
        "tuple_sha256": emission.tuple_sha256,
        "bucket": emission.bucket,
        "split": emission.split,
        "cell_index": emission.cell_index,
        "block_start": emission.block_start,
        "block_stop": emission.block_stop,
    }


def stage1_status() -> dict[str, Any]:
    contract = experiment.stage1_contract()
    proof = generator.stage1_structural_proof()
    emissions = []
    for cell_index, split in enumerate(("train", "calibration", "evaluation")):
        template = generator.synthetic_tuple_template(f"status_{split}")
        emissions.append(
            _envelope(generator.emit_synthetic_cell(template, generator.emission_request(cell_index, split)))
        )
    verification = independent.stage1_verification_report(proof, emissions)
    reserved_absence = {
        path: not (PROJECT_ROOT / Path(path)).exists()
        for path in contract["reserved_canonical_paths"]
    }
    dependency_facts = {
        "python_required": "3.11",
        "python_observed": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "ortools_required": "9.12.4544",
        "ortools_observed": _dependency_version("ortools"),
        "torch_required": "2.7.0",
        "torch_device_required": "cpu",
        "torch_observed_distribution": _dependency_version("torch"),
        "canonical_readiness_assessed": False,
    }
    return {
        "status": generator.SYNTHETIC_STATUS,
        "stage": 1,
        "contract": contract,
        "structural_proof": proof,
        "independent_verification": verification,
        "dependency_facts_separate_from_canonical_readiness": dependency_facts,
        "reserved_path_absence": reserved_absence,
        "all_reserved_paths_absent": all(reserved_absence.values()),
        "canonical_actions_available": False,
        "result_claim": None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", nargs="?", choices=("stage1-status",), default="stage1-status"
    )
    parser.parse_args(argv)
    print(json.dumps(stage1_status(), sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
