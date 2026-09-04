from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_e2a import run_e2a_local_self_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_e2a_local_self_audit(args.repository_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(json.dumps({"accepted": True, "output": str(args.output), "surface_checks": result["surface_checks"]}, sort_keys=True))


if __name__ == "__main__":
    main()
