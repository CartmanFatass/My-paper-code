"""Write the bounded E1 flow-local result-blind audit receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_e1 import (
    run_e1_flow_local_self_audits,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    payload = run_e1_flow_local_self_audits()
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(encoded)
    print(json.dumps({
        "output": str(arguments.output), "sha256": hashlib.sha256(encoded).hexdigest(),
        "all_five_families_flow_local_accepted": payload["all_five_families_flow_local_accepted"],
        "question_relevant_output": payload["question_relevant_output"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
