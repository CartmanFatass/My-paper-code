"""One-shot runner for the source-free VSP03-A1 boundary confirmation audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.vsp_03.event_certified_boundary_confirmation import (  # noqa: E402
    publish_registered_audit_once,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Reserve and run the zero-runtime VSP03-A1 audit. This revision has "
            "no authenticated target-negative causal event source, so it must "
            "fail closed without lookup activity."
        )
    )
    parser.add_argument("--output", required=True, help="new one-shot A1 JSON artifact")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = publish_registered_audit_once(args.output)
    except (FileExistsError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from exc
    payload = result.to_dict()
    print(json.dumps({
        "lookup_evaluations": payload["activity"]["lookup_evaluations"],
        "output": str(Path(args.output)),
        "terminal_branch": payload["terminal_branch"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
