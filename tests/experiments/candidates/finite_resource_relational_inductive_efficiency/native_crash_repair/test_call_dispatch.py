"""Standalone, non-learning check of call boundaries seen in two crash cores.

This is a runtime discriminator, not a reproducer of the complete RL program.
Run under an external 120-second bound. It never loads the project native ABI.
"""

import argparse
from dataclasses import dataclass
from enum import Enum
import json
import sys
import time


class Field(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True, slots=True)
class Record:
    index: int

    def validate(self):
        if type(self.index) is not int or not 0 <= self.index < 16:
            raise AssertionError("record changed across a Python call")
        return self.index


def check_calls(iterations):
    records = tuple(Record(i) for i in range(16))
    fields = tuple(Field)
    total = 0
    for i in range(iterations):
        total += records[i % 16].validate()
        if tuple(field.value for field in fields) != ("left", "right"):
            raise AssertionError("Enum getter/generator output changed")
    whole, tail = divmod(iterations, 16)
    expected = whole * 120 + tail * (tail - 1) // 2
    if total != expected:
        raise AssertionError((total, expected))
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=2_000_000)
    args = parser.parse_args()
    if args.iterations <= 0:
        parser.error("iterations must be positive")
    for stage in ("stdlib", "numpy_imported", "torch_imported"):
        if stage == "numpy_imported":
            import numpy  # noqa: F401 -- the import is the diagnostic condition
        elif stage == "torch_imported":
            import torch
            torch.set_num_threads(1)
        print(json.dumps({"stage": stage, "state": "started"}), flush=True)
        started = time.perf_counter()
        total = check_calls(args.iterations)
        print(json.dumps({
            "stage": stage, "state": "passed", "iterations": args.iterations,
            "checksum": total, "wall_seconds": time.perf_counter() - started,
            "python": sys.version, "trace_active": sys.gettrace() is not None,
            "profile_active": sys.getprofile() is not None,
            "learning_steps": 0, "project_native_calls": 0,
        }), flush=True)


if __name__ == "__main__":
    main()
