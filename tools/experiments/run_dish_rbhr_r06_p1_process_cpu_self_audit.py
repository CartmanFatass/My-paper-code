from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_p1 import run_p1_process_cpu_self_audit


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repository-root", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); payload = run_p1_process_cpu_self_audit(args.repository_root.resolve())
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_bytes(encoded)
    print(json.dumps({"output": str(args.output), "sha256": hashlib.sha256(encoded).hexdigest(),
                      "checks": payload["checks"], "process_measurement": payload["process_measurement"],
                      "resource_projection": payload["resource_projection"]}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
