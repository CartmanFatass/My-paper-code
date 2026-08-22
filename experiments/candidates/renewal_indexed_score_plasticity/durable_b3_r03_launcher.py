"""Lease-bound adapter for the shared HMASD long-effect control plane."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Direct script execution places only this candidate directory on sys.path.
# Add the immutable repository root before importing the shared control plane.
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.hmasd_control_plane import long_effect

DIRECTION = "renewal_indexed_score_plasticity"
STAGE = "RISP-B3-TRG-R03-FULL-PANEL"
REVISION = "RISP-B3-TRG-SCIENCE-20260815-03"
CERTIFICATE_SCHEMA = "RISP-B3-TRG-R03-PREACTIVITY-CERTIFICATE-20260815-03"
CERTIFICATE_SHA256 = "94ead8d7fc2652c50ab745d84467ec942bd04a89d56f1ea4eacbaad120638221"
SCIENCE_CARD_SHA256 = "11f0fca9ac767dfc4c519aa8b2307795124929ffecc69f13286b8dbff3915778"
PRO_CLOSED_SHA256 = "9fccfcf84e92b1bf47ca4b6d8d4fe2e6899bb429b2bf907e96661ab51d977fa4"
PORTFOLIO_SHA256 = "286d2e78da46b0218dca8465e2f2d63951f58fccd0bf6d634acf112330e11625"
COORDINATE_SCHEMA = "RISP-B3-TRG-R03-LAZY-SHAKE256-PREFIX-20260815-01"
COORDINATE_ROOT = "5e823ac4fd4d14ebcd0f7293f69e61696d6cb8f57b56d98bd1cdd94e0602ed3a"
EXPECTED_COMMAND = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe "
    "experiments/candidates/renewal_indexed_score_plasticity/run_b3_r03_resume.py "
    "--slice-wall-seconds 13800 --rss-limit-bytes 1073741824"
)
ROOT_LEASE_PATH = Path("C:/Projects/HMASD/temp/leases/RISP_B3_R03_ROOT_PRODUCTION_LEASE_POST_RECON_20260820.json")
ROOT_LEASE_SHA256 = "a7f6e7f3944caf2c577907ba830786977a88224cec67122fc84ff29476f3e1fd"
EXPECTED_SOURCE_SHA256 = {
    "experiments/candidates/renewal_indexed_score_plasticity/b3_r03_experiment.py": "bc355fa1364304ac417a1a083805b75bc533aa544b11108804ab8445177cb5c6",
    "experiments/candidates/renewal_indexed_score_plasticity/b3_r03_resume.py": "0676836be7dc59af159e4638550b136553270d3cd00f4df50976f978c321354e",
    "experiments/candidates/renewal_indexed_score_plasticity/run_b3_r03_resume.py": "1282756644e5fb27064b8512e407402c1e5fbab4623011da6ae48dd27aa7f0e7",
    "tests/experiments/candidates/renewal_indexed_score_plasticity/test_b3_r03.py": "6b56bbca99906397e76278931f1193831e8cf413522083b3f39a417abe966c26",
    "experiments/candidates/renewal_indexed_score_plasticity/b2_r02_experiment.py:interval_and_atomic_helpers_only": "6879c5f46cd7f64d3716e0ab34fce792674e467433b4283b9a47dcab0a907920",
}


def _repository_root() -> Path:
    return REPOSITORY_ROOT


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError(f"object required: {path}")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _same_path(left: Path | str, right: Path | str) -> bool:
    return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(str(Path(right).resolve()))


def _parse_lease_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise RuntimeError(f"lease {field} must be an offset-aware timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError(f"lease {field} is invalid") from error
    if parsed.tzinfo is None:
        raise RuntimeError(f"lease {field} must be offset-aware")
    return parsed.astimezone(timezone.utc)


def _validate_hash_binding(path_value: Any, digest_value: Any, expected_digest: str, label: str) -> Path:
    if not isinstance(path_value, str) or digest_value != expected_digest:
        raise RuntimeError(f"accepted {label} binding mismatch")
    path = Path(path_value).resolve(strict=True)
    if _sha256_file(path) != expected_digest:
        raise RuntimeError(f"accepted {label} source hash mismatch")
    return path


def _validate_lease(lease_path: Path, *, now: datetime | None = None) -> dict[str, Any]:
    """Recompute the complete accepted production binding from one Root lease."""
    repository = _repository_root().resolve(strict=True)
    lease_path = lease_path.resolve(strict=True)
    if not _same_path(lease_path, ROOT_LEASE_PATH):
        raise RuntimeError("lease path is not the exact Root lease path")
    lease_digest = _sha256_file(lease_path)
    if lease_digest != ROOT_LEASE_SHA256:
        raise RuntimeError("exact Root lease hash mismatch")
    lease = _load(lease_path)
    if lease.get("direction") != DIRECTION or lease.get("revision") != REVISION:
        raise RuntimeError("lease direction/revision mismatch")
    if lease.get("production_authorized") is not True:
        raise RuntimeError("lease does not authorize production")
    if lease.get("max_workers") != 1 or lease.get("cpu_cores") != 1 or lease.get("gpu_count") != 0:
        raise RuntimeError("lease resource binding mismatch")
    if lease.get("peak_rss_cap_bytes") != 1 << 30 or lease.get("slice_wall_seconds_max") != 13800:
        raise RuntimeError("lease slice/RSS binding mismatch")
    if lease.get("authorized_seeds") != list(range(16)):
        raise RuntimeError("lease seed binding mismatch")
    issued_at = _parse_lease_time(lease.get("issued_at", lease.get("issued_at_utc")), "issued_at")
    expiry_value = lease.get("not_after", lease.get("not_after_utc"))
    not_after = _parse_lease_time(expiry_value, "not_after")
    checked_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if not issued_at <= checked_at <= not_after:
        raise RuntimeError("lease is not currently valid")
    if checked_at + timedelta(seconds=13800) > not_after:
        raise RuntimeError("lease validity does not cover the complete frozen slice")
    if lease.get("production_command") != EXPECTED_COMMAND:
        raise RuntimeError("lease production command mismatch")
    command = shlex.split(EXPECTED_COMMAND, posix=True)
    if len(command) != 6:
        raise RuntimeError("internal frozen command shape mismatch")
    certificate_path = Path(str(lease.get("preactivity_certificate", ""))).resolve(strict=True)
    if lease.get("preactivity_certificate_sha256") != CERTIFICATE_SHA256:
        raise RuntimeError("lease certificate hash binding mismatch")
    if _sha256_file(certificate_path) != CERTIFICATE_SHA256:
        raise RuntimeError("accepted preactivity certificate hash mismatch")
    certificate = _load(certificate_path)
    if certificate.get("schema") != CERTIFICATE_SCHEMA or certificate.get("science_revision") != REVISION:
        raise RuntimeError("accepted certificate identity mismatch")
    if certificate.get("technical_acceptance") is not True or certificate.get("scientific_activity_started") is not False:
        raise RuntimeError("accepted certificate activity/acceptance mismatch")
    if certificate.get("coordinate_schema") != COORDINATE_SCHEMA or certificate.get("coordinate_root") != COORDINATE_ROOT:
        raise RuntimeError("accepted coordinate binding mismatch")
    science_card = _validate_hash_binding(certificate.get("science_card"), certificate.get("science_card_sha256"), SCIENCE_CARD_SHA256, "science card")
    pro_closed_intake = _validate_hash_binding(certificate.get("external_pro_closed_intake"), certificate.get("external_pro_closed_intake_sha256"), PRO_CLOSED_SHA256, "External Pro intake")
    portfolio_authorization = _validate_hash_binding(certificate.get("portfolio_authorization"), certificate.get("portfolio_authorization_sha256"), PORTFOLIO_SHA256, "portfolio authorization")
    if certificate.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("accepted R03 source manifest mismatch")
    source_paths: list[str] = []
    for labelled_path, expected_digest in EXPECTED_SOURCE_SHA256.items():
        source_path = repository / labelled_path.split(":", 1)[0]
        if not source_path.is_file() or _sha256_file(source_path) != expected_digest:
            raise RuntimeError(f"accepted R03 source hash mismatch: {labelled_path}")
        source_paths.append(str(source_path))
    production = certificate.get("production")
    paths = certificate.get("paths")
    if not isinstance(production, dict) or not isinstance(paths, dict):
        raise RuntimeError("accepted certificate production/path binding missing")
    if production.get("working_directory") is None or not _same_path(production["working_directory"], repository):
        raise RuntimeError("accepted repository root mismatch")
    if production.get("command") != EXPECTED_COMMAND:
        raise RuntimeError("accepted certificate production command mismatch")
    if production.get("slice_wall_seconds") != 13800 or production.get("rss_limit_bytes") != 1 << 30:
        raise RuntimeError("accepted certificate resource binding mismatch")
    interpreter = Path(str(production.get("interpreter", ""))).resolve(strict=True)
    runner = (repository / command[1]).resolve(strict=True)
    expected_runner = repository / "experiments/candidates/renewal_indexed_score_plasticity/run_b3_r03_resume.py"
    if not _same_path(command[0], interpreter) or not _same_path(runner, expected_runner):
        raise RuntimeError("accepted interpreter/runner binding mismatch")
    if not _same_path(sys.executable, interpreter):
        raise RuntimeError("launcher must run under the accepted production interpreter")
    frontier = Path(str(lease.get("frontier", ""))).resolve()
    result_root = Path(str(lease.get("result_root", ""))).resolve()
    result = Path(str(paths.get("result", ""))).resolve()
    if not _same_path(frontier, paths.get("frontier", "")) or not _same_path(result_root, paths.get("result_root", "")):
        raise RuntimeError("lease frontier/result-root binding mismatch")
    expected_base = repository / "experiments/candidates/renewal_indexed_score_plasticity"
    if not _same_path(certificate_path, expected_base / "RISP_B3_R03_PREACTIVITY_CERTIFICATE_20260815_03.json"):
        raise RuntimeError("lease certificate path mismatch")
    if not _same_path(frontier, expected_base / "RISP_B3_R03_RESUME_20260815_03"):
        raise RuntimeError("lease frontier path mismatch")
    if not _same_path(result_root, expected_base / "RISP_B3_R03_RESULTS_20260815_03"):
        raise RuntimeError("lease result-root path mismatch")
    if result.parent != result_root or result.name != "RISP_B3_R03_20260815_03.json":
        raise RuntimeError("accepted result path mismatch")
    bound_command = [str(interpreter), str(runner), *command[2:]]
    return {
        "direction": DIRECTION, "revision": REVISION, "repository_root": str(repository),
        "lease_path": str(lease_path), "lease_sha256": lease_digest,
        "certificate_path": str(certificate_path), "certificate_sha256": CERTIFICATE_SHA256,
        "science_card_path": str(science_card), "external_pro_closed_intake_path": str(pro_closed_intake),
        "portfolio_authorization_path": str(portfolio_authorization), "source_paths": source_paths,
        "frontier_path": str(frontier), "result_root": str(result_root), "result_path": str(result),
        "receipt_directory": str(frontier / "slice_receipts"), "command": bound_command,
        "command_sha256": hashlib.sha256(_json_bytes({"command": bound_command})).hexdigest(),
        "lease_not_after": expiry_value,
    }


def _validate_control_root(run_root: Path, binding: dict[str, Any]) -> None:
    protected_paths = [Path(binding[key]) for key in ("frontier_path", "result_root", "certificate_path", "result_path")]
    if any(run_root == path or run_root in path.parents or path in run_root.parents for path in protected_paths):
        raise RuntimeError("runtime control root must be separate from scientific paths")


def _long_effect_spec(binding: dict[str, Any]) -> dict[str, Any]:
    """Build the sole shared-control-plane input from the frozen binding."""
    experiment_id = str(uuid.uuid4())
    input_refs = [
        {"name": "root_lease", "path": binding["lease_path"]},
        {"name": "preactivity_certificate", "path": binding["certificate_path"]},
        {"name": "science_card", "path": binding["science_card_path"]},
        {"name": "external_pro_closed_intake", "path": binding["external_pro_closed_intake_path"]},
        {"name": "portfolio_authorization", "path": binding["portfolio_authorization_path"]},
        {"name": "resume_frontier", "path": binding["frontier_path"]},
    ]
    input_refs.extend({"name": f"accepted_source_{index}", "path": path} for index, path in enumerate(binding["source_paths"], start=1))
    return {
        "schema": long_effect.SPEC_SCHEMA, "experiment_id": experiment_id,
        "component": "risp_b3_r03_durable_launcher", "working_directory": binding["repository_root"],
        "argv": binding["command"], "input_refs": input_refs,
        "output_refs": [
            {"name": "resume_frontier", "path": binding["frontier_path"]},
            {"name": "complete_result_root", "path": binding["result_root"]},
            {"name": "complete_result", "path": binding["result_path"]},
            {"name": "slice_receipts", "path": binding["receipt_directory"]},
        ],
        "metadata": {"direction_id": DIRECTION, "stage": STAGE, "effect_id": None},
    }


def _launch(args: argparse.Namespace) -> int:
    binding = _validate_lease(args.lease)
    run_root = args.run_root.resolve()
    _validate_control_root(run_root, binding)
    run_root.parent.mkdir(parents=True, exist_ok=True)
    terminal = long_effect.run_long_effect(_long_effect_spec(binding), run_root)
    exit_code = terminal.get("exit_code")
    return exit_code if isinstance(exit_code, int) else 1


def _observe(args: argparse.Namespace) -> int:
    print(json.dumps(long_effect.observe_long_effect(args.run_root.resolve()), sort_keys=True))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    launch = commands.add_parser("launch")
    launch.add_argument("--lease", required=True, type=Path)
    launch.add_argument("--run-root", required=True, type=Path)
    observe = commands.add_parser("observe")
    observe.add_argument("--run-root", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "launch":
        return _launch(args)
    if args.mode == "observe":
        return _observe(args)
    raise RuntimeError(f"unsupported launcher mode: {args.mode}")


if __name__ == "__main__":
    raise SystemExit(main())
