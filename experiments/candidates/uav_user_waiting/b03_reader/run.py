#!/usr/bin/env python3
"""Admit the frozen B03 reader with its canonical, digest-bound worker artifact."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PRODUCER_SHA = 'a045bc9b4e3ba9ef211474293c4bc43ad8b16b08'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--generic-summary', type=Path, required=True)
    parser.add_argument('--worker-summary-sha256', required=True)
    parser.add_argument('--launch-sha', required=True)
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args(argv)
    if args.seed != 29423000:
        parser.error('fixed B03 verification identity required')
    if args.generic_summary.name != 'summary.json':
        parser.error('canonical worker summary.json required')
    digest = args.worker_summary_sha256
    if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        parser.error('complete lowercase worker summary SHA256 required')

    from scripts.hmasd_admission import require_admission
    admission = require_admission(__file__, direction='uav_user_waiting')
    if admission['sha'] != args.launch_sha:
        raise RuntimeError('reader adapter admission/source mismatch')
    summary = args.generic_summary.resolve(strict=True)
    # Import only after admission; the frozen reader checks the supplied digest,
    # original producer SHA and every original scientific source before replay.
    from experiments.candidates.uav_user_waiting.b03.read import read_result
    return read_result(
        summary.parent, reading_out=args.out, admission=dict(admission),
        expected_summary_sha256=digest, expected_launch_sha=PRODUCER_SHA,
    )


if __name__ == '__main__':
    if main()['status'] != 'VERIFIED_COMPLETE':
        raise SystemExit(1)
