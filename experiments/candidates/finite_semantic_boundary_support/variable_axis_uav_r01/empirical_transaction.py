from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .empirical_contract import OUTPUT_ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Exact FSBS R01 registered empirical transaction"
    )
    parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[4]
    output_root = repo / OUTPUT_ROOT
    if not output_root.is_dir() or not (output_root / "manifest.json").is_file():
        print("registered empirical transaction not released", file=sys.stderr)
        return 7
    print(
        "registered empirical transaction not released: immutable Operator manifest "
        "has not been validated by this prelaunch-only entrypoint",
        file=sys.stderr,
    )
    return 7


if __name__ == "__main__":
    raise SystemExit(main())
