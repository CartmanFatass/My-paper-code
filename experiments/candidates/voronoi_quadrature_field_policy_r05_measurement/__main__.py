from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lifecycle import canonical_json_bytes, publish_report
from .measurement import run_measurement


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the bounded VQFP r05 TEST-only measurement")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--temp-root", type=Path)
    args = parser.parse_args()
    value = run_measurement(temp_root=args.temp_root)
    if args.output is not None:
        publish_report(args.output.resolve(), value)
    print(canonical_json_bytes(value).decode("ascii"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

