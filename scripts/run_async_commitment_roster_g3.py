"""Bounded nonformal runner for the asynchronous roster G3 source gate."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from ha_ctse_process.async_commitment_roster_g3 import (
    evaluate_information_gate,
    validate_information_gate_result,
)


_REPLACE_ATTEMPTS = 100
_REPLACE_DELAY_SECONDS = 0.05


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.parent / f".{path.name}.{os.getpid()}.tmp"
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    for attempt in range(_REPLACE_ATTEMPTS):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt + 1 == _REPLACE_ATTEMPTS:
                raise
            time.sleep(_REPLACE_DELAY_SECONDS)


def run_gate(output_root: Path, *, source_commit: str) -> Path:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("source_commit must be an exact 40-character lowercase hash")
    output_root = Path(output_root)
    if output_root.exists():
        raise FileExistsError("information-gate output root must be fresh")
    output_root.mkdir(parents=True)
    payload = evaluate_information_gate(source_commit=source_commit)
    validate_information_gate_result(payload)
    artifact = output_root / "result.json"
    _atomic_json(artifact, payload)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    artifact = run_gate(args.output_root, source_commit=args.source_commit)
    print(artifact)


if __name__ == "__main__":
    main()
