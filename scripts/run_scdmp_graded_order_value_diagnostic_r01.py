"""CLI for SCDMP-A-GRADED-ORDER-VALUE-DIAGNOSTIC-R01 (A/RECON, host diagnostic).

Order of effects, exactly as the card freezes it:

  1. fresh 4 GiB physical/effective admission, before any measurement;
  2. build the diagnostic translation unit and verify, bit for bit, that it
     reproduces the frozen library over the whole M1 census at (0.88, 0.25);
     a mismatch stops the object and produces no reading;
  3. M1 census on the frozen library;
  4. M2 sweep on the diagnostic library.

No learner is trained, no optimizer step is taken, no result-bearing root is
written, and the quarantined `…-RUN-01` root is never opened.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import time


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.scdmp_variable_k.graded_order_value_diagnostic_r01 import census
from experiments.candidates.scdmp_variable_k.graded_order_value_diagnostic_r01 import (
    diagnostic_library as diaglib,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import (
    native_backend,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.preflight import (
    preflight_run,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.source_identity import (
    compute_source_identity,
)


OBJECT_ID = "SCDMP-A-GRADED-ORDER-VALUE-DIAGNOSTIC-R01"
QUARANTINED_ROOT_NAME = "SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01"
TAU_LEAK_GRID = (0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.00)
Z_LIMIT_GRID = (0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60)


def _write(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-run-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args(argv)

    base = Path(args.base_run_root).resolve(strict=True)
    if QUARANTINED_ROOT_NAME == base.name:
        parser.error("the quarantined named run is not an admissible base-run root")
    out = Path(args.output_root).resolve(strict=False)
    out.mkdir(parents=True, exist_ok=True)
    if not 1 <= int(args.threads) <= 4:
        parser.error("threads must be in [1, 4]")
    census.set_threads(int(args.threads))
    started = time.perf_counter()

    # 1. admission, before any measurement
    admission = preflight_run(args.receipt, command_runner=subprocess.run)
    print(json.dumps({
        "stage": "admission", "object_id": OBJECT_ID,
        "receipt": str(admission.path),
        "available_physical_bytes": admission.available_physical_bytes,
        "effective_available_bytes": admission.effective_available_bytes,
        "passed": admission.passed,
    }, sort_keys=True), flush=True)

    twins = census.load_twins(base)
    policies = census.load_policies(base)
    action_map = json.loads(
        (base / "development-action-map.json").read_text(encoding="utf-8")
    )
    matched = {}
    for graph in census.GRAPHS:
        key = "hr_action" if graph == "HR" else "rh_action"
        values = {int(unit[key]) for unit in action_map["units"]}
        if len(values) != 1:
            raise SystemExit(f"published action map is not constant for {graph}: {sorted(values)}")
        matched[graph] = values.pop()
    if matched != census.EXPECTED_MATCHED:
        raise SystemExit(f"published matched pair differs: {matched}")

    # 2. diagnostic library, then the bit-identity check over the whole census
    native_abi = native_backend.native_abi_identity()
    library, build_record = diaglib.build_diagnostic_library(out / "diagnostic-native")
    frozen_census = census.census(twins=twins, policies=policies)
    frozen_fingerprint = census.census_fingerprint(frozen_census)
    with diaglib.use_library(library):
        diaglib.set_cable_parameters(
            library, tau_leak=diaglib.FROZEN_TAU_LEAK, z_limit=diaglib.FROZEN_Z_LIMIT,
        )
        identity_census = census.census(twins=twins, policies=policies)
    identity_fingerprint = census.census_fingerprint(identity_census)
    identical = frozen_fingerprint == identity_fingerprint and all(
        asdict(left) == asdict(right)
        for left, right in zip(frozen_census, identity_census, strict=True)
    )
    identity = {
        "object_id": OBJECT_ID,
        "schema": "SCDMP_GOVD_R01_BIT_IDENTITY_V1",
        "checked_at_row": {"tau_leak": diaglib.FROZEN_TAU_LEAK, "z_limit": diaglib.FROZEN_Z_LIMIT},
        "census_cells": len(frozen_census),
        "frozen_library_census_sha256": frozen_fingerprint,
        "diagnostic_library_census_sha256": identity_fingerprint,
        "bit_identical": bool(identical),
        "frozen_native_abi": native_abi,
        "diagnostic_build": build_record,
    }
    _write(out / "bit-identity-check.json", identity)
    print(json.dumps({
        "stage": "bit_identity", "bit_identical": bool(identical),
        "census_cells": len(frozen_census),
        "frozen_library_census_sha256": frozen_fingerprint,
        "diagnostic_library_census_sha256": identity_fingerprint,
    }, sort_keys=True), flush=True)
    if not identical:
        _write(out / "stopped-no-reading.json", {
            "object_id": OBJECT_ID,
            "reason": "diagnostic library did not reproduce the frozen library bit for bit",
            "scientific_polarity": None,
        })
        print(json.dumps({"stage": "stop", "reason": "bit_identity_failed"}, sort_keys=True))
        return 3

    # 3. M1 census (frozen library) -- published only after the identity check
    _write(out / "m1-census.json", {
        "object_id": OBJECT_ID,
        "schema": "SCDMP_GOVD_R01_M1_CENSUS_V1",
        "library": "frozen",
        "diagnostic_rng_domain": census.DIAGNOSTIC_DOMAIN,
        "tapes": census.DIAGNOSTIC_TAPES,
        "matched_actions": matched,
        "census_sha256": frozen_fingerprint,
        "cells": [asdict(row) for row in frozen_census],
    })
    print(json.dumps({"stage": "m1", "cells": len(frozen_census)}, sort_keys=True), flush=True)

    # 4. M2 sweep on the diagnostic library
    points = []
    with diaglib.use_library(library):
        for tau_leak in TAU_LEAK_GRID:
            for z_limit in Z_LIMIT_GRID:
                diaglib.set_cable_parameters(library, tau_leak=tau_leak, z_limit=z_limit)
                observed = census.sweep_point(
                    twins=twins, policies=policies, matched=matched,
                )
                points.append({
                    "tau_leak": tau_leak, "z_limit": z_limit,
                    "frozen_row": tau_leak == diaglib.FROZEN_TAU_LEAK
                    and z_limit == diaglib.FROZEN_Z_LIMIT,
                    **{key: value for key, value in observed.items() if key != "cells"},
                    "cells": observed["cells"],
                })
                print(json.dumps({
                    "stage": "m2", "tau_leak": tau_leak, "z_limit": z_limit,
                    "swapped_survival_cells": observed["swapped_survival_cells"],
                    "matched_dock_cells": observed["matched_dock_cells"],
                    "M_minus_X": observed["M_minus_X"],
                }, sort_keys=True), flush=True)
        diaglib.set_cable_parameters(
            library, tau_leak=diaglib.FROZEN_TAU_LEAK, z_limit=diaglib.FROZEN_Z_LIMIT,
        )
    _write(out / "m2-sweep.json", {
        "object_id": OBJECT_ID,
        "schema": "SCDMP_GOVD_R01_M2_SWEEP_V1",
        "library": "diagnostic",
        "tau_leak_grid": list(TAU_LEAK_GRID),
        "z_limit_grid": list(Z_LIMIT_GRID),
        "matched_actions": matched,
        "points": points,
    })

    source_identity = compute_source_identity()
    summary = {
        "object_id": OBJECT_ID,
        "schema": "SCDMP_GOVD_R01_SUMMARY_V1",
        "evidence_class": "A/RECON",
        "scientific_polarity": None,
        "order_value_polarity": None,
        "base_run_root": str(base),
        "output_root": str(out),
        "admission": {
            "receipt": str(admission.path),
            "available_physical_bytes": admission.available_physical_bytes,
            "effective_available_bytes": admission.effective_available_bytes,
            "passed": admission.passed,
        },
        "bit_identical_at_frozen_row": True,
        "m1_cells": len(frozen_census),
        "m2_points": len(points),
        "m2_missions": sum(len(point["cells"]) for point in points),
        "matched_actions": matched,
        "torch_intraop_threads": int(args.threads),
        "wall_seconds": time.perf_counter() - started,
        "source_identity_sha256": source_identity["owned_tree_aggregate_sha256"],
        "assigned_base_commit": source_identity["assigned_base_commit"],
        "owned_tree_git_diff_sha256": source_identity["git_diff_sha256"],
        "frozen_native_abi": native_abi,
    }
    _write(out / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
