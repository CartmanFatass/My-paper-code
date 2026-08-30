from __future__ import annotations

import argparse
import json
import sys
from typing import NoReturn, Sequence

import numpy as np
import scipy

from .contracts import ArrayContract, ComparisonContract, ToleranceContract, compare_artifacts


class CliUsageError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise CliUsageError(message)


def _shape(value: str) -> tuple[int, ...]:
    if value == "scalar":
        return ()
    try:
        dimensions = tuple(int(part) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("shape must be 'scalar' or comma-separated non-negative integers") from exc
    if not dimensions or any(size < 0 for size in dimensions):
        raise argparse.ArgumentTypeError("shape must be 'scalar' or comma-separated non-negative integers")
    return dimensions


def _parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        prog="python -m tools.research.scientific_compute",
        description="Compare two recorded .npy artifacts under an explicit numerical contract.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, parser_class=JsonArgumentParser)
    compare = subparsers.add_parser("compare", help="compare expected and actual .npy artifacts")
    compare.add_argument("--expected", required=True)
    compare.add_argument("--actual", required=True)
    compare.add_argument("--mode", choices=("exact", "approximate"), required=True)
    compare.add_argument("--dtype", required=True, help="required NumPy dtype, including byte order when relevant")
    compare.add_argument("--shape", required=True, type=_shape, help="comma-separated dimensions or 'scalar'")
    compare.add_argument("--order", choices=("C", "F"), required=True)
    compare.add_argument("--nan-policy", choices=("forbid", "equal", "unequal"), required=True)
    compare.add_argument("--inf-policy", choices=("forbid", "equal", "unequal"), required=True)
    compare.add_argument("--signed-zero-policy", choices=("distinguish", "equal"), required=True)
    compare.add_argument("--units", required=True, help="use 'dimensionless' when applicable")
    compare.add_argument("--device", choices=("cpu",), required=True)
    compare.add_argument("--oracle", required=True)
    compare.add_argument("--algorithm", required=True)
    compare.add_argument("--algorithm-version", required=True)
    compare.add_argument("--atol", type=float)
    compare.add_argument("--rtol", type=float)
    compare.add_argument("--tolerance-justification")
    return parser


def _error(kind: str, message: str) -> dict[str, object]:
    return {
        "dependency_versions": {"numpy": np.__version__, "scipy": scipy.__version__},
        "error": {"kind": kind, "message": message},
        "ok": False,
        "schema_version": 1,
        "status": "ERROR",
        "tool": "scientific_compute.compare",
    }


def _build_contract(args: argparse.Namespace) -> ComparisonContract:
    tolerance_arguments = (args.atol, args.rtol, args.tolerance_justification)
    if args.mode == "approximate":
        if any(value is None for value in tolerance_arguments):
            raise ValueError("approximate mode requires --atol, --rtol, and --tolerance-justification")
        tolerance = ToleranceContract(
            atol=args.atol,
            rtol=args.rtol,
            justification=args.tolerance_justification,
        )
    else:
        if any(value is not None for value in tolerance_arguments):
            raise ValueError("exact mode rejects --atol, --rtol, and --tolerance-justification")
        tolerance = None

    array = ArrayContract(
        dtype=args.dtype,
        shape=args.shape,
        order=args.order,
        nan_policy=args.nan_policy,
        inf_policy=args.inf_policy,
        signed_zero_policy=args.signed_zero_policy,
        units=args.units,
        device=args.device,
    )
    return ComparisonContract(
        mode=args.mode,
        array=array,
        oracle=args.oracle,
        algorithm=args.algorithm,
        algorithm_version=args.algorithm_version,
        tolerance=tolerance,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except CliUsageError as exc:
        print(json.dumps(_error("invalid_arguments", str(exc)), allow_nan=False, sort_keys=True))
        return 2
    try:
        contract = _build_contract(args)
    except ValueError as exc:
        print(json.dumps(_error("invalid_contract", str(exc)), allow_nan=False, sort_keys=True))
        return 2

    try:
        result = compare_artifacts(args.expected, args.actual, contract)
    except (OSError, ValueError) as exc:
        print(json.dumps(_error("artifact_unreadable", str(exc)), allow_nan=False, sort_keys=True))
        return 3

    result["dependency_versions"] = {"numpy": np.__version__, "scipy": scipy.__version__}
    print(json.dumps(result, allow_nan=False, separators=(",", ":"), sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
