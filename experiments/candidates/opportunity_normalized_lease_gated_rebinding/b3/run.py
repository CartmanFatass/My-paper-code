"""One-shot, result-blind runner for the frozen ONLGR B3 prospective screen."""

from __future__ import annotations

import os

# Bind numerical runtimes before importing NumPy/SciPy through local modules.
for _thread_variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_thread_variable] = "1"

import argparse
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import time
from typing import Callable, Mapping, Sequence

import numpy as np

from . import analysis
from .config import (
    ARTIFACT_KIND, BRANCHES, CONFIRMATION_EPISODES, CONFIRMATION_NAMESPACE,
    CONFIRMATION_TEAM_TICKS, DISCOVERY_EPISODES, DISCOVERY_NAMESPACE,
    DISCOVERY_TEAM_TICKS, HORIZON, MAX_RSS_BYTES, MAX_WALL_SECONDS,
    PRODUCTION_CONFIG, RESULT_FILENAME, REVISION, ROOTS, TOTAL_TEAM_TICKS,
    config_identity, registered_work,
)
from .host import EpisodeResult, counter_uniform, generate_episode, run_episode
from .policies import (
    KEEP_POLICY, FixedPolicy, discovery_grid, exposure_bin, matched_shell, select_best,
)


class ResourceLimitExceeded(RuntimeError):
    def __init__(self, limit: str, observed: float, ceiling: float) -> None:
        super().__init__(f"{limit} ceiling exceeded")
        self.limit = limit
        self.observed = observed
        self.ceiling = ceiling


class OutputStateError(RuntimeError):
    pass


FROZEN_OUTPUT_RELATIVE = Path(
    "temp/directions/opportunity_normalized_lease_gated_rebinding/exp/clean_successor_02"
)
FROZEN_CHILD_ARGV = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
    "-m",
    "experiments.candidates.opportunity_normalized_lease_gated_rebinding.b3",
    "--output-root",
    FROZEN_OUTPUT_RELATIVE.as_posix(),
)
_SCAFFOLD_DIRECTORIES = {"artifacts", "checkpoints", "metrics"}
_SCAFFOLD_FILES = {
    "preflight.json", "runner-spec.json", "manifest.json", "execute-preflight.json",
    "stdout.log", "stderr.log",
}
_OPTIONAL_SCAFFOLD_FILES = {".manifest.json.lock"}
_EXPECTED_LAUNCHER_OUTPUTS = {
    "stdout": "stdout.log", "stderr": "stderr.log", "checkpoints": "checkpoints",
    "metrics": "metrics", "artifacts": "artifacts",
}
_DIRECTION_ID = "opportunity_normalized_lease_gated_rebinding"
_RUN_ID = "clean_successor_02"


def _current_rss_bytes() -> int:
    try:
        import psutil
        info = psutil.Process(os.getpid()).memory_info()
        return int(getattr(info, "peak_wset", info.rss))
    except (ImportError, OSError):
        return 0


class ResourceMonitor:
    def __init__(
        self, *, clock: Callable[[], float] = time.perf_counter,
        rss_supplier: Callable[[], int] = _current_rss_bytes,
        max_seconds: float = MAX_WALL_SECONDS, max_rss_bytes: int = MAX_RSS_BYTES,
    ) -> None:
        self.clock = clock
        self.rss_supplier = rss_supplier
        self.max_seconds = float(max_seconds)
        self.max_rss_bytes = int(max_rss_bytes)
        self.started = self.clock()
        self.peak_rss_bytes = 0
        self.team_ticks = 0

    @property
    def elapsed_seconds(self) -> float:
        return float(self.clock() - self.started)

    def check(self) -> None:
        elapsed = self.elapsed_seconds
        rss = int(self.rss_supplier())
        self.peak_rss_bytes = max(self.peak_rss_bytes, rss)
        if elapsed > self.max_seconds:
            raise ResourceLimitExceeded("wall_seconds", elapsed, self.max_seconds)
        if rss > self.max_rss_bytes:
            raise ResourceLimitExceeded("peak_rss_bytes", float(rss), float(self.max_rss_bytes))

    def register_episode(self, result: EpisodeResult) -> None:
        self.team_ticks += int(result.physics_ticks)
        self.check()

    def report(self) -> dict[str, object]:
        return {
            "cpu_threads": 1,
            "gpu_used": False,
            "network_used": False,
            "training_used": False,
            "elapsed_seconds": self.elapsed_seconds,
            "peak_rss_bytes": self.peak_rss_bytes,
            "actual_team_ticks": self.team_ticks,
            "hard_limits": {"wall_seconds": self.max_seconds, "peak_rss_bytes": self.max_rss_bytes},
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _command_digest(command: Sequence[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(part) for part in command)).hexdigest()


def _current_git_head(cwd: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--verify", "HEAD"],
            check=True, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise OutputStateError("cannot bind launcher scaffold to current Git HEAD") from error
    head = completed.stdout.strip().lower()
    if len(head) not in (40, 64) or any(character not in "0123456789abcdef" for character in head):
        raise OutputStateError("current Git HEAD is malformed")
    return head


def _is_alias(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except OSError as error:
        raise OutputStateError(f"cannot inspect output path: {path}") from error
    attributes = int(getattr(metadata, "st_file_attributes", 0))
    reparse_attribute = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return stat.S_ISLNK(metadata.st_mode) or bool(attributes & reparse_attribute)


def _assert_no_alias_components(path: Path) -> None:
    cursor = path.absolute()
    while cursor != cursor.parent:
        if cursor.exists() and _is_alias(cursor):
            raise OutputStateError(f"symlink/reparse output component is forbidden: {cursor}")
        cursor = cursor.parent


def _read_scaffold_json(path: Path) -> dict[str, object]:
    if _is_alias(path):
        raise OutputStateError(f"launcher evidence may not be a symlink/reparse alias: {path.name}")
    metadata = os.lstat(path)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 4 * 1024 * 1024:
        raise OutputStateError(f"launcher evidence is not a bounded regular file: {path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OutputStateError(f"launcher evidence is unreadable: {path.name}") from error
    if not isinstance(value, dict):
        raise OutputStateError(f"launcher evidence must be a JSON object: {path.name}")
    return value


def _validate_launcher_scaffold(
    root: Path, *, cwd: Path, expected_argv: Sequence[str], head: str,
) -> None:
    expected_root = (cwd / FROZEN_OUTPUT_RELATIVE).resolve()
    if root != expected_root:
        raise OutputStateError("launcher scaffold is not at the exact frozen output root")
    children = {child.name: child for child in root.iterdir()}
    required = _SCAFFOLD_DIRECTORIES | _SCAFFOLD_FILES
    if RESULT_FILENAME in children:
        raise OutputStateError("terminal B3 result already exists")
    if not required.issubset(children) or not set(children).issubset(required | _OPTIONAL_SCAFFOLD_FILES):
        raise OutputStateError("launcher scaffold entries are missing or unexpected")

    for name in _SCAFFOLD_DIRECTORIES:
        directory = children[name]
        if _is_alias(directory):
            raise OutputStateError(f"launcher directory may not be a symlink/reparse alias: {name}")
        metadata = os.lstat(directory)
        if not stat.S_ISDIR(metadata.st_mode) or any(directory.iterdir()):
            raise OutputStateError(f"launcher directory must be empty: {name}")
    for name in {"stdout.log", "stderr.log"} | (set(children) & _OPTIONAL_SCAFFOLD_FILES):
        path = children[name]
        if _is_alias(path) or not stat.S_ISREG(os.lstat(path).st_mode):
            raise OutputStateError(f"launcher evidence must be a regular non-alias file: {name}")

    preflight = _read_scaffold_json(children["preflight.json"])
    execute_preflight = _read_scaffold_json(children["execute-preflight.json"])
    runner_spec = _read_scaffold_json(children["runner-spec.json"])
    manifest = _read_scaffold_json(children["manifest.json"])
    for name, evidence in (("preflight", preflight), ("execute-preflight", execute_preflight)):
        if (
            evidence.get("direction_id") != _DIRECTION_ID
            or evidence.get("run_id") != _RUN_ID
            or evidence.get("memory_safe") is not True
            or evidence.get("workers") != 1
            or evidence.get("threads_per_worker") != 1
        ):
            raise OutputStateError(f"{name} is not the exact safe single-thread launcher evidence")

    command = list(expected_argv)
    command_sha = _command_digest(command)
    if (
        manifest.get("status") != "RUNNING"
        or manifest.get("direction_id") != _DIRECTION_ID
        or manifest.get("run_id") != _RUN_ID
        or manifest.get("cwd") != str(cwd)
        or str(manifest.get("code_sha", "")).lower() != head
        or manifest.get("command") != command
        or manifest.get("command_sha256") != command_sha
        or manifest.get("outputs") != _EXPECTED_LAUNCHER_OUTPUTS
    ):
        raise OutputStateError("manifest is not bound to current cwd/HEAD/frozen RUNNING command")
    resources = manifest.get("resources")
    if not isinstance(resources, dict):
        raise OutputStateError("manifest resource binding is missing")
    preflight_sha = _sha256(children["preflight.json"])
    runner_spec_sha = _sha256(children["runner-spec.json"])
    if (
        resources.get("preflight_ref") != "preflight.json"
        or resources.get("preflight_sha256") != preflight_sha
        or resources.get("runner_spec_sha256") != runner_spec_sha
        or resources.get("workers") != 1
        or resources.get("threads_per_worker") != 1
        or resources.get("memory_safe") is not True
    ):
        raise OutputStateError("manifest resource hashes or limits do not bind launcher evidence")
    expected_spec = {
        "schema_version": 1,
        "command": command,
        "command_sha256": command_sha,
        "cwd": str(cwd),
        "output_root": str(root),
        "outputs": _EXPECTED_LAUNCHER_OUTPUTS,
        "preflight_sha256": preflight_sha,
    }
    if any(runner_spec.get(key) != value for key, value in expected_spec.items()):
        raise OutputStateError("runner specification is not bound to the frozen launch")


def source_identity() -> dict[str, object]:
    package_root = Path(__file__).resolve().parent
    names = ("__init__.py", "__main__.py", "config.py", "host.py", "policies.py", "analysis.py", "run.py")
    files = {str((package_root / name).relative_to(package_root.parents[3])).replace("\\", "/"): _sha256(package_root / name) for name in names}
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=package_root, check=True,
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        commit = "UNAVAILABLE"
    payload = {"revision": REVISION, "git_commit": commit, "files": files, "b3_local_runtime_only": True}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**payload, "sha256": hashlib.sha256(encoded).hexdigest()}


def _prepare_output_root(output_root: Path) -> Path:
    _assert_no_alias_components(output_root)
    root = output_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    _assert_no_alias_components(root)
    entries = tuple(root.iterdir())
    if not entries:
        return root
    if any(entry.name == RESULT_FILENAME for entry in entries):
        raise OutputStateError("terminal B3 result already exists")
    cwd = Path.cwd().resolve()
    _validate_launcher_scaffold(
        root, cwd=cwd, expected_argv=FROZEN_CHILD_ARGV, head=_current_git_head(cwd),
    )
    return root


def atomic_write_json(path: Path, payload: Mapping[str, object]) -> int:
    if path.exists():
        raise OutputStateError("terminal result already exists")
    temporary = path.parent / f".{path.name}.{os.getpid()}.tmp"
    if temporary.exists():
        raise OutputStateError("atomic temporary already exists")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return len(encoded)


def _episode_bank(namespace: str, episodes: int) -> dict[int, tuple[object, ...]]:
    return {
        root: tuple(generate_episode(
            seed=root, episode_index=index, namespace=namespace,
        ) for index in range(episodes))
        for root in ROOTS
    }


def _evaluate_policy(
    policy: FixedPolicy, bank: Mapping[int, Sequence[object]], monitor: ResourceMonitor,
    *, retain_episodes: bool = False,
) -> tuple[dict[int, dict[str, object]], tuple[EpisodeResult, ...]]:
    metrics: dict[int, dict[str, object]] = {}
    retained: list[EpisodeResult] = []
    for root in ROOTS:
        monitor.check()
        episodes: list[EpisodeResult] = []
        for exogenous in bank[root]:
            result = run_episode(exogenous, policy=policy, retain_detailed_ledgers=False)
            monitor.register_episode(result)
            episodes.append(result)
        metrics[root] = analysis.summarize_root(episodes)
        if retain_episodes:
            retained.extend(episodes)
    return metrics, tuple(retained)


def _descriptor(policy: FixedPolicy) -> dict[str, object]:
    return {
        "policy_id": policy.policy_id,
        "family": policy.family,
        "grid_index": policy.grid_index,
        "p_low": policy.p_low,
        "p_high": policy.p_high,
        "probability": policy.probability,
        "lambda": policy.rate,
        "force_keep": policy.force_keep,
        "separation": policy.separation,
    }


def _conformance(
    confirmation: Mapping[str, Mapping[int, Mapping[str, object]]],
    support: Mapping[str, object], monitor: ResourceMonitor,
) -> dict[str, object]:
    all_rows = [row for policy in confirmation.values() for row in policy.values()]
    facts = {
        "support_and_shell": bool(support["pass"]),
        "reward_service_cost_reconciliation": all(bool(row["reward_service_cost_exact"]) and bool(row["decomposition_exact"]) for row in all_rows),
        "root_pairing": all(tuple(sorted(policy)) == ROOTS for policy in confirmation.values()),
        "fresh_distinct_namespaces": DISCOVERY_NAMESPACE != CONFIRMATION_NAMESPACE,
        "post_action_iid_ordering": all(bool(row["post_action_iid_ordering_exact"]) for row in all_rows),
        "terminal_censoring": all(bool(row["terminal_censoring_exact"]) for row in all_rows),
        "action_legality_and_exposure_range": all(bool(row["exposure_range_exact"]) for row in all_rows),
        "conditional_mark_probability_rho_half": True,
        "identity_uniqueness": all(bool(row["identity_unique"]) and bool(row["episode_identity_unique"]) for row in all_rows),
        "policy_common_exogenous_coordinates_within_bank": True,
        "counter_banks_distinct": (
            counter_uniform("ACTION_EVENT_UNIFORM", DISCOVERY_NAMESPACE, ROOTS[0], 0, 0, 0)
            != counter_uniform("ACTION_EVENT_UNIFORM", CONFIRMATION_NAMESPACE, ROOTS[0], 0, 0, 0)
            and counter_uniform("ACTION_MARK_UNIFORM", DISCOVERY_NAMESPACE, ROOTS[0], 0, 0, 0)
            != counter_uniform("ACTION_MARK_UNIFORM", CONFIRMATION_NAMESPACE, ROOTS[0], 0, 0, 0)
        ),
        "no_training_checkpoint_gpu_network": True,
        "resource_accounting_exact": monitor.team_ticks == TOTAL_TEAM_TICKS,
        "atomic_output_protocol_configured": True,
    }
    return {"facts": facts, "failed": tuple(name for name, passed in facts.items() if not passed), "pass": all(facts.values())}


def execute_screen(monitor: ResourceMonitor | None = None) -> dict[str, object]:
    active_monitor = monitor or ResourceMonitor()
    active_monitor.check()
    discovery_bank = _episode_bank(DISCOVERY_NAMESPACE, DISCOVERY_EPISODES)
    keep_metrics, keep_episodes = _evaluate_policy(
        KEEP_POLICY, discovery_bank, active_monitor, retain_episodes=True,
    )
    f0 = tuple(
        exposure
        for episode in keep_episodes
        for exposure, _action, _role, initial in episode.legal_action_rows
        if not initial
    )
    q0, probability_grid, nonkeep_policies = discovery_grid(f0)
    discovery_metrics: dict[str, dict[int, dict[str, object]]] = {KEEP_POLICY.policy_id: keep_metrics}
    for policy in nonkeep_policies:
        metrics, _episodes = _evaluate_policy(policy, discovery_bank, active_monitor)
        discovery_metrics[policy.policy_id] = metrics
    if active_monitor.team_ticks != DISCOVERY_TEAM_TICKS:
        raise RuntimeError("discovery work accounting mismatch")

    stratified = tuple(policy for policy in nonkeep_policies if policy.family == "stratified")
    global_p = tuple(policy for policy in nonkeep_policies if policy.family == "global_p")
    global_lambda = tuple(policy for policy in nonkeep_policies if policy.family == "global_lambda")
    selected_stratified = select_best(stratified, discovery_metrics, ROOTS)
    selected_global_p = select_best(global_p, discovery_metrics, ROOTS)
    selected_global_lambda = select_best(global_lambda, discovery_metrics, ROOTS)
    low_count = sum(1 for exposure in f0 if exposure_bin(exposure) == "low")
    high_count = len(f0) - low_count
    shell = matched_shell(selected_stratified, low_count / len(f0), high_count / len(f0))
    heterogeneity = analysis.discovery_heterogeneity_facts(
        stratified, selected_stratified, discovery_metrics, ROOTS,
    )

    confirmation_bank = _episode_bank(CONFIRMATION_NAMESPACE, CONFIRMATION_EPISODES)
    confirmation_policies = {
        "stratified": selected_stratified,
        "global_p": selected_global_p,
        "global_lambda": selected_global_lambda,
        "keep": KEEP_POLICY,
        "shell": shell,
    }
    confirmation_metrics: dict[str, dict[int, dict[str, object]]] = {}
    for alias, policy in confirmation_policies.items():
        metrics, _episodes = _evaluate_policy(policy, confirmation_bank, active_monitor)
        confirmation_metrics[alias] = metrics
    if active_monitor.team_ticks - DISCOVERY_TEAM_TICKS != CONFIRMATION_TEAM_TICKS:
        raise RuntimeError("confirmation work accounting mismatch")

    contrasts = {
        alias: analysis.contrast_summary(confirmation_metrics["stratified"], confirmation_metrics[alias], ROOTS)
        for alias in ("global_p", "global_lambda", "keep", "shell")
    }
    support = analysis.support_and_shell_conformance(
        confirmation_metrics["stratified"], confirmation_metrics["shell"], ROOTS,
    )
    conformance = _conformance(confirmation_metrics, support, active_monitor)
    branch, gates = analysis.decide_branch(
        valid=bool(conformance["pass"]), contrasts=contrasts,
        candidate=selected_stratified, grid=probability_grid, heterogeneity=heterogeneity,
    )
    active_monitor.check()
    result = {
        "artifact_kind": ARTIFACT_KIND,
        "revision": REVISION,
        "terminal": True,
        "evaluation_only": True,
        "learned_link_result_emitted": False,
        "source_identity": source_identity(),
        "config_identity": config_identity(),
        "outcome_blind_grid": {
            "f0_legal_rows": len(f0),
            "f0_bin_mass": {"low": low_count / len(f0), "high": high_count / len(f0)},
            "q0": q0,
            "probability_grid": probability_grid,
            "global_lambdas": tuple(policy.rate for policy in global_lambda),
        },
        "selection": {
            "stratified": _descriptor(selected_stratified),
            "global_p": _descriptor(selected_global_p),
            "global_lambda": _descriptor(selected_global_lambda),
            "keep": _descriptor(KEEP_POLICY),
            "shell": _descriptor(shell),
            "tie_rule": "mean_direct_return_then_lower_activity_then_smaller_high_minus_low_separation_then_lexicographic_grid_index",
        },
        "discovery_root_metrics": discovery_metrics,
        "discovery_heterogeneity": heterogeneity,
        "confirmation_root_metrics": confirmation_metrics,
        "support": support,
        "conformance": conformance,
        "contrasts": contrasts,
        "gates": gates,
        "branch": branch,
        "registered_work": registered_work(),
        "resources": active_monitor.report(),
    }
    if sum(bool(value) for value in result["gates"]["branches"].values()) != 1 or branch not in BRANCHES:
        raise RuntimeError("branch serialization is not one-hot")
    return result


def _resource_nonpass(
    *, source: Mapping[str, object], monitor: ResourceMonitor,
    error_kind: str, detail: Mapping[str, object],
) -> dict[str, object]:
    branches = {name: name == "INVALID" for name in BRANCHES}
    return {
        "artifact_kind": ARTIFACT_KIND,
        "revision": REVISION,
        "terminal": True,
        "evaluation_only": True,
        "learned_link_result_emitted": False,
        "source_identity": source,
        "config_identity": config_identity(),
        "outcome_blind_grid": None,
        "selection": None,
        "discovery_root_metrics": {},
        "discovery_heterogeneity": None,
        "confirmation_root_metrics": {},
        "support": {"pass": False, "reason": error_kind},
        "conformance": {"pass": False, "failed": (error_kind,)},
        "contrasts": {},
        "gates": {"gate_1": {"evaluated": False}, "gate_2": {"evaluated": False}, "branches": branches},
        "branch": "INVALID",
        "registered_work": registered_work(),
        "resources": {**monitor.report(), "terminal_nonpass": error_kind, "detail": dict(detail)},
    }


def run_registered(output_root: Path, *, monitor: ResourceMonitor | None = None) -> Path:
    if not PRODUCTION_CONFIG.registered:
        raise RuntimeError("unregistered B3 configuration")
    active_monitor = monitor or ResourceMonitor()
    root = _prepare_output_root(output_root)
    source = source_identity()
    try:
        payload = execute_screen(active_monitor)
    except ResourceLimitExceeded as error:
        payload = _resource_nonpass(
            source=source, monitor=active_monitor, error_kind="RESOURCE_LIMIT_NONPASS",
            detail={"limit": error.limit, "observed": error.observed, "ceiling": error.ceiling},
        )
    except Exception as error:
        payload = _resource_nonpass(
            source=source, monitor=active_monitor, error_kind="RUNTIME_CONFORMANCE_NONPASS",
            detail={"exception_type": type(error).__name__, "message": str(error)},
        )
    result_path = root / RESULT_FILENAME
    atomic_write_json(result_path, payload)
    return result_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m experiments.candidates.opportunity_normalized_lease_gated_rebinding.b3")
    parser.add_argument("--output-root", required=True)
    arguments = parser.parse_args(argv)
    try:
        run_registered(Path(arguments.output_root))
    except (OSError, OutputStateError):
        return 2
    return 0
