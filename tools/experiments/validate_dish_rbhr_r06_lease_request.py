from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_e2b import validate_prepared_lease_request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--acceptance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    payload = validate_prepared_lease_request(arguments.repository_root, arguments.request, arguments.acceptance)
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    arguments.output.parent.mkdir(parents=True, exist_ok=True); arguments.output.write_bytes(encoded)
    print(json.dumps({"output": str(arguments.output), "sha256": hashlib.sha256(encoded).hexdigest(), **payload}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
