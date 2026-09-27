"""Admitted CLI for the fixed 136-world, zero-fit energy relay diagnostic batch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-root", type=Path, required=True,
                        help="immutable external directory containing c00/ and c03/")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    # This import and handshake precede candidate imports, checkpoint reads, and output writes.
    from scripts.hmasd_admission import require_admission

    admitted = require_admission(__file__, direction="energy_relay_diagnostics")
    if args.launch_sha != admitted["sha"]:
        raise ValueError("--launch-sha differs from admitted source SHA")

    from experiments.candidates.energy_relay_diagnostics.b01.study import run_batch

    summary = run_batch(checkpoint_root=args.checkpoint_root, out=args.out,
                        launch_sha=args.launch_sha, workers=args.workers,
                        threads=args.threads)
    return 0 if summary["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
