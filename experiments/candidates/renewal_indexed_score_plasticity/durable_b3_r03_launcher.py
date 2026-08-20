"""Lease-bound durable supervisor for the accepted RISP-B3/R03 recovery slice.

The scientific runner is unchanged. This module derives its only production
command from the exact Root lease and accepted preactivity certificate, then
keeps process lifetime and terminal observability outside an ephemeral caller.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA = "RISP-B3-R03-DURABLE-LAUNCH-20260820-02"
DIRECTION = "renewal_indexed_score_plasticity"
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
ROOT_LEASE_PATH = Path("C:/Projects/HMASD/temp/leases/RISP_B3_R03_ROOT_PRODUCTION_LEASE_RENEWAL_20260819.json")
ROOT_LEASE_SHA256 = "de00ed40719f9388971ffe0847ea2650b6f6b3ac7a86a01571f0c1efbffb370c"
EXPECTED_SOURCE_SHA256 = {
    "experiments/candidates/renewal_indexed_score_plasticity/b3_r03_experiment.py": "bc355fa1364304ac417a1a083805b75bc533aa544b11108804ab8445177cb5c6",
    "experiments/candidates/renewal_indexed_score_plasticity/b3_r03_resume.py": "0676836be7dc59af159e4638550b136553270d3cd00f4df50976f978c321354e",
    "experiments/candidates/renewal_indexed_score_plasticity/run_b3_r03_resume.py": "1282756644e5fb27064b8512e407402c1e5fbab4623011da6ae48dd27aa7f0e7",
    "tests/experiments/candidates/renewal_indexed_score_plasticity/test_b3_r03.py": "6b56bbca99906397e76278931f1193831e8cf413522083b3f39a417abe966c26",
    "experiments/candidates/renewal_indexed_score_plasticity/b2_r02_experiment.py:interval_and_atomic_helpers_only": "6879c5f46cd7f64d3716e0ab34fce792674e467433b4283b9a47dcab0a907920",
}

STATE_NAME = "state.json"
TERMINAL_NAME = "terminal.json"
CONFIG_NAME = "launch.json"
CLAIM_NAME = "LAUNCH.claim.json"


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _json_bytes(payload)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary_name = handle.name
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        last_error: OSError | None = None
        for _ in range(100):
            try:
                os.replace(temporary_name, path)
                last_error = None
                break
            except PermissionError as error:
                last_error = error
                time.sleep(0.01)
        if last_error is not None:
            raise last_error
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def _exclusive_write(path: Path, payload: dict[str, Any]) -> None:
    """Publish a one-way record without an overwrite window."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(_json_bytes(payload))
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)


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

    _validate_hash_binding(certificate.get("science_card"), certificate.get("science_card_sha256"), SCIENCE_CARD_SHA256, "science card")
    _validate_hash_binding(certificate.get("external_pro_closed_intake"), certificate.get("external_pro_closed_intake_sha256"), PRO_CLOSED_SHA256, "External Pro intake")
    _validate_hash_binding(certificate.get("portfolio_authorization"), certificate.get("portfolio_authorization_sha256"), PORTFOLIO_SHA256, "portfolio authorization")
    if certificate.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("accepted R03 source manifest mismatch")
    for labelled_path, expected_digest in EXPECTED_SOURCE_SHA256.items():
        source_path = repository / labelled_path.split(":", 1)[0]
        if not source_path.is_file() or _sha256_file(source_path) != expected_digest:
            raise RuntimeError(f"accepted R03 source hash mismatch: {labelled_path}")

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
        "direction": DIRECTION,
        "revision": REVISION,
        "repository_root": str(repository),
        "lease_path": str(lease_path),
        "lease_sha256": lease_digest,
        "certificate_path": str(certificate_path),
        "certificate_sha256": CERTIFICATE_SHA256,
        "frontier_path": str(frontier),
        "result_root": str(result_root),
        "result_path": str(result),
        # The immutable runner publishes slice terminal receipts under the
        # resumable frontier, never beside the complete-only result artifact.
        "receipt_directory": str(frontier / "slice_receipts"),
        "command": bound_command,
        "command_sha256": hashlib.sha256(_json_bytes({"command": bound_command})).hexdigest(),
        "lease_not_after": expiry_value,
    }


def _receipt_names(directory: Path) -> list[str]:
    if not directory.is_dir():
        return []
    # Names only: no partial scientific payload is opened by the supervisor.
    return sorted(path.name for path in directory.glob("*.json") if path.is_file())


def _validate_control_root(run_root: Path, binding: dict[str, Any]) -> None:
    protected_paths = [Path(binding[key]) for key in ("frontier_path", "result_root", "certificate_path", "result_path")]
    if any(run_root == path or run_root in path.parents or path in run_root.parents for path in protected_paths):
        raise RuntimeError("runtime control root must be separate from scientific paths")


def _creation_flags(*, detached: bool) -> int:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    if detached:
        flags |= getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        flags |= getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000)
    return flags


def _hidden_startupinfo() -> Any:
    if os.name != "nt":
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo


def _spawn_detached(command: list[str]) -> subprocess.Popen[bytes]:
    if os.name != "nt":
        raise RuntimeError("the durable RISP launcher requires Windows Job semantics")
    return subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_creation_flags(detached=True),
        startupinfo=_hidden_startupinfo(),
        close_fds=True,
    )


def _assert_detached_supervisor() -> None:
    """Fail before production unless this process is outside every Windows Job."""
    if os.name != "nt":
        raise RuntimeError("the durable RISP launcher requires Windows Job semantics")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    in_job = ctypes.c_int(0)
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    kernel32.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    kernel32.IsProcessInJob.restype = ctypes.c_int
    if not kernel32.IsProcessInJob(kernel32.GetCurrentProcess(), None, ctypes.byref(in_job)):
        raise ctypes.WinError(ctypes.get_last_error())
    if in_job.value:
        raise RuntimeError("supervisor remains in a Windows Job; kill-on-close escape was not established")


def _claim(config: dict[str, Any], run_root: Path) -> None:
    _exclusive_write(run_root / CLAIM_NAME, {
        "schema": SCHEMA,
        "status": "CLAIMED",
        "launch_id": config["launch_id"],
        "supervisor_pid": os.getpid(),
        "claimed_at_unix": time.time(),
    })


def _publish_owner_error(run_root: Path, config: dict[str, Any], error: BaseException) -> None:
    try:
        _exclusive_write(run_root / TERMINAL_NAME, {
            "schema": SCHEMA,
            "status": "SUPERVISOR_ERROR",
            "launch_id": config.get("launch_id"),
            "supervisor_pid": os.getpid(),
            "error_type": type(error).__name__,
            "error": str(error),
            "partial_scientific_values_exposed": False,
        })
    except FileExistsError:
        pass


def _best_effort_state(path: Path, payload: dict[str, Any]) -> None:
    try:
        _atomic_write(path, payload)
    except Exception:
        # State is a replaceable mirror. The immutable claim and terminal
        # records own launch identity and final truth.
        pass


def _supervise(config_path: Path) -> int:
    config_path = config_path.resolve(strict=True)
    config = _load(config_path)
    run_root = Path(str(config.get("run_root", ""))).resolve(strict=True)
    if config_path != run_root / CONFIG_NAME:
        raise RuntimeError("config must be the exact retained launch record")
    if config.get("schema") != SCHEMA:
        raise RuntimeError("launch config schema mismatch")
    try:
        uuid.UUID(str(config.get("launch_id", "")))
    except ValueError as error:
        raise RuntimeError("launch identity is invalid") from error
    if (run_root / CLAIM_NAME).exists():
        raise RuntimeError(f"launch identity already claimed: {config['launch_id']}")
    requested_state = _load(run_root / STATE_NAME)
    if requested_state.get("status") != "LAUNCH_REQUESTED" or requested_state.get("launch_id") != config["launch_id"]:
        raise RuntimeError("launch identity is not in its one-use requested state")
    if (run_root / TERMINAL_NAME).exists():
        raise RuntimeError("launch identity already has a terminal record")

    # The persistent claim sits outside owner error handling. A replay or
    # non-owner cannot mutate active or terminal records.
    try:
        _claim(config, run_root)
    except FileExistsError as error:
        raise RuntimeError(f"launch identity already claimed: {config['launch_id']}") from error

    terminal_published = False
    try:
        binding = _validate_lease(Path(str(config.get("lease_path", ""))))
        if config.get("lease_sha256") != binding["lease_sha256"] or config.get("binding") != binding:
            raise RuntimeError("supervisor lease/config binding mismatch")
        _validate_control_root(run_root, binding)
        _assert_detached_supervisor()

        receipt_directory = Path(binding["receipt_directory"])
        receipt_names_before = _receipt_names(receipt_directory)
        started_at = time.time()
        stdout_path = run_root / "stdout.log"
        stderr_path = run_root / "stderr.log"
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            child = subprocess.Popen(
                binding["command"],
                cwd=binding["repository_root"],
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                creationflags=_creation_flags(detached=False),
                startupinfo=_hidden_startupinfo(),
                close_fds=True,
            )
            _best_effort_state(run_root / STATE_NAME, {
                "schema": SCHEMA,
                "status": "RUNNING",
                "launch_id": config["launch_id"],
                "supervisor_pid": os.getpid(),
                "child_pid": child.pid,
                "started_at_unix": started_at,
                "receipt_names_before": receipt_names_before,
                "command_sha256": binding["command_sha256"],
                "lease_sha256": binding["lease_sha256"],
                "partial_scientific_values_exposed": False,
            })
            exit_code = child.wait()

        receipt_names_after = _receipt_names(receipt_directory)
        terminal = {
            "schema": SCHEMA,
            "status": "EXITED",
            "launch_id": config["launch_id"],
            "supervisor_pid": os.getpid(),
            "child_pid": child.pid,
            "started_at_unix": started_at,
            "ended_at_unix": time.time(),
            "exit_code": exit_code,
            "command_sha256": binding["command_sha256"],
            "lease_sha256": binding["lease_sha256"],
            "receipt_directory": binding["receipt_directory"],
            "receipt_names_before": receipt_names_before,
            "receipt_names_after": receipt_names_after,
            "new_receipt_names": sorted(set(receipt_names_after) - set(receipt_names_before)),
            "stdout_sha256": _sha256_file(stdout_path),
            "stderr_sha256": _sha256_file(stderr_path),
            "partial_scientific_values_exposed": False,
        }
        _exclusive_write(run_root / TERMINAL_NAME, terminal)
        terminal_published = True
        _best_effort_state(run_root / STATE_NAME, {**terminal, "status": "TERMINAL_RECORDED"})
        return exit_code
    except BaseException as error:
        if not terminal_published:
            _publish_owner_error(run_root, config, error)
        raise


def _launch(args: argparse.Namespace) -> int:
    binding = _validate_lease(args.lease)
    run_root = args.run_root.resolve()
    _validate_control_root(run_root, binding)
    run_root.parent.mkdir(parents=True, exist_ok=True)
    try:
        run_root.mkdir()
    except FileExistsError as error:
        raise RuntimeError(f"runtime control root must be fresh: {run_root}") from error

    launch_id = str(uuid.uuid4())
    config = {
        "schema": SCHEMA,
        "launch_id": launch_id,
        "run_root": str(run_root),
        "lease_path": binding["lease_path"],
        "lease_sha256": binding["lease_sha256"],
        "binding": binding,
    }
    config_path = run_root / CONFIG_NAME
    _exclusive_write(config_path, config)
    _exclusive_write(run_root / STATE_NAME, {
        "schema": SCHEMA,
        "status": "LAUNCH_REQUESTED",
        "launch_id": launch_id,
        "lease_sha256": binding["lease_sha256"],
        "command_sha256": binding["command_sha256"],
        "partial_scientific_values_exposed": False,
    })
    try:
        supervisor = _spawn_detached([
            str(Path(sys.executable).resolve()),
            str(Path(__file__).resolve()),
            "supervise",
            "--config",
            str(config_path),
        ])
    except BaseException as error:
        _publish_owner_error(run_root, config, error)
        raise
    print(json.dumps({"run_root": str(run_root), "supervisor_pid": supervisor.pid, "launch_id": launch_id, "status": "LAUNCH_REQUESTED"}, sort_keys=True))
    return 0


def _observe(args: argparse.Namespace) -> int:
    run_root = args.run_root.resolve()
    path = run_root / TERMINAL_NAME if (run_root / TERMINAL_NAME).exists() else run_root / STATE_NAME
    if not path.exists():
        raise RuntimeError(f"no durable state exists: {run_root}")
    print(json.dumps(_load(path), sort_keys=True))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    launch = commands.add_parser("launch")
    launch.add_argument("--lease", required=True, type=Path)
    launch.add_argument("--run-root", required=True, type=Path)
    observe = commands.add_parser("observe")
    observe.add_argument("--run-root", required=True, type=Path)
    supervise = commands.add_parser("supervise")
    supervise.add_argument("--config", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "launch":
        return _launch(args)
    if args.mode == "observe":
        return _observe(args)
    return _supervise(args.config)


if __name__ == "__main__":
    raise SystemExit(main())
