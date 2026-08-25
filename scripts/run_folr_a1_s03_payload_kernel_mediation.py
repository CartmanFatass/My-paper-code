"""CLI wiring for the FOLR A1 deterministic S03 kernel probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.folr_core import registration as reg  # noqa: E402
from experiments.candidates.folr_core import s03_payload_kernel_mediation as probe  # noqa: E402


def _run(arguments: argparse.Namespace) -> int:
    registration = (
        reg.development_registration()
        if arguments.technical_smoke
        else reg.registered_cell()
    )
    artifact = probe.run_probe(
        registration=registration,
        source_commit=arguments.source_commit,
        run_id=arguments.run_id,
        technical_only=bool(arguments.technical_smoke),
    )
    target = probe.write_json(artifact, arguments.output)
    payload = target.read_bytes()
    print(f"decision: {artifact['decision']}")
    print(f"technical_only: {artifact['technical_only']}")
    print(f"scientific_terminal_admitted: {artifact['scientific_terminal_admitted']}")
    print(f"artifact: {target}")
    print(f"sha256: {hashlib.sha256(payload).hexdigest()}")
    # Every frozen decision, including the exact pre-readout prerequisite
    # terminal, is a successfully materialized scientific artifact. Structural
    # or I/O failures still raise and therefore remain nonzero process exits.
    return 0


def _validate(arguments: argparse.Namespace) -> int:
    artifact = probe.load_json(arguments.input)
    result = probe.validate_artifact(artifact)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _analyze(arguments: argparse.Namespace) -> int:
    artifact = probe.load_json(arguments.input)
    analysis = probe.analyze_artifact(artifact)
    print(json.dumps(analysis, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="execute the exact six-kernel probe")
    run.add_argument("--source-commit", required=True)
    run.add_argument("--run-id", required=True)
    run.add_argument("--output", required=True)
    run.add_argument(
        "--technical-smoke",
        action="store_true",
        help=(
            "use DEVELOPMENT_ONLY registration; emitted artifact is technical_only "
            "and cannot be a scientific terminal"
        ),
    )
    run.set_defaults(handler=_run)

    validate = commands.add_parser("validate", help="read-only artifact validation")
    validate.add_argument("--input", required=True)
    validate.set_defaults(handler=_validate)

    analyze = commands.add_parser("analyze", help="read-only TV/decision recomputation")
    analyze.add_argument("--input", required=True)
    analyze.set_defaults(handler=_analyze)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    return int(arguments.handler(arguments))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
