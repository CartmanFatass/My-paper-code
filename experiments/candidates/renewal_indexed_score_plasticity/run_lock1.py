"""Runner for the exact deterministic RISP-B1 revision-07 Lock-1 certificate."""

from __future__ import annotations

import json
from pathlib import Path

from lock1_certificate import SCHEMA, write_artifact


def main() -> None:
    artifact = Path(__file__).with_name("RISP_B1_LOCK1_20260813_07.json")
    result = write_artifact(artifact)
    summary = {
        "schema": SCHEMA,
        "certificate_result": result["certificate_result"],
        "all_required_structural_fixtures_passed": result["all_required_structural_fixtures_passed"],
        "registered_stochastic_object_created": result["registered_stochastic_object_created"],
        "scientific_activity_started": result["scientific_activity_started"],
        "artifact": str(artifact.resolve()),
        "anomalies": result["anomalies"],
    }
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
