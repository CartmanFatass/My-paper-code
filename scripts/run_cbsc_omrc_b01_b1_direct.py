"""INCOMPLETE_NOT_RUN scope-review candidate; not admitted for execution."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_direct import (
    publish_offline_subset,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    args = parser.parse_args()
    publish_offline_subset(args.input_root, args.output_root, args.launch_sha)


if __name__ == "__main__":
    main()
