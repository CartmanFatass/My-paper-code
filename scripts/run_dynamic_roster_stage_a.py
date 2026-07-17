"""Run the no-learning Stage A carrier for the F0/F1 dynamic-roster testbed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.dynamic_roster_testbed import (  # noqa: E402
    evaluate_stage_a,
    json_ready,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=256)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = evaluate_stage_a(args.episodes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(json_ready(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(json_ready(result), sort_keys=True))
    return 0 if result["implementation_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
