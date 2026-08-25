"""Resumable result-blind checkpoint-only ONLGR core reevaluation recovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import time
from datetime import datetime
from typing import Any, Mapping

# The recovery is a CPU-only evaluator.  Set the process contract before
# importing numpy/torch so neither library can discover or initialize a GPU.
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import numpy as np
import torch

from .analysis import iid_analysis, primary_analysis, summarize_episodes
from .config import (
    ARTIFACT_KIND, FIXED_MARKS, FIXED_RATES, HELDOUT_SCHEDULES, IID_SCHEDULE,
    LEARNED_ARMS, PPO, PRODUCTION_CONFIG, SEEDS, TRAIN_SCHEDULES, TREATMENT,
    VALIDATION_ROOTS, registered_budget,
)
from .controls import (
    keep_grid_equality, leakage_twin_contract, marked_partition_probe,
    prob_exp_identity_probe,
)
from .host import EpisodeResult, generate_episode, run_episode
from .models import ACTOR_WIDTH, CentralCritic, MarkedActor, initial_event_bias
from .run import (
    COMPOSITE_REVISION, MATHEMATICAL_CLOSURE_CONFIRMED,
    _evaluate_learned_panel, _partition_analysis, _rss_bytes, _support_facts,
    select_fixed_rate,
)


RECOVERY_IDENTITY = "SAME_TREATMENT_CHECKPOINT_ONLY_EVALUATION_REPLAY"
RECOVERY_DECISION = "ONLGR_RESULT_BLIND_CHECKPOINT_ONLY_CORE_REEVALUATION_RECOVERY_DECISION"
RECOVERY_ARTIFACT_KIND = "ONLGR_B1_CHECKPOINT_ONLY_CORE_RECOVERY_RESULT"
RESULT_MAP_REVISION = "ONLGR-B1-RESULT-BLIND-INTAKE-ACTIVATION-MAP-20260812-02"
MARKER_NAME = ".ONLGR_CHECKPOINT_ONLY_CORE_RECOVERY_ONCE.json"
FRONTIER_DIRECTORY = "checkpoint_only_core_frontier_v3"
FRONTIER_REVISION = "ONLGR-CHECKPOINT-ONLY-CORE-ATOMIC-FRONTIER-20260814-03"
PRESERVED_INERT_FRONTIER_DIRECTORIES = ("checkpoint_only_core_frontier_v2",)
SOURCE_IDENTITY_REVISION = "ONLGR-EVALUATOR-SOURCE-IDENTITY-20260814-01"
SOURCE_IDENTITY_FILES = (
    "config.py", "rng.py", "host.py", "models.py", "controls.py",
    "analysis.py", "run.py", "recovery.py",
)
MAX_SLICE_SECONDS = 3 * 60 * 60 + 45 * 60
MAX_RSS_BYTES = 1024**3
ATOMIC_REPLACE_RESERVE_SECONDS = 5.0
FIRST_ATTEMPT_NON_YOKE_TICKS = 6_291_456
FIRST_ATTEMPT_YOKE_MAX_TICKS = 458_752
RECOVERY_INCREMENT_TICKS = 3_112_960
CUMULATIVE_HARD_MAX_TICKS = 9_863_168
EXPECTED_RECOVERY_PANELS = {
    "native": 1_376_256,
    "iid_future_k": 196_608,
    "safety": 688_128,
    "fixed_rate_selection": 393_216,
    "fixed_rate_evaluation": 229_376,
    "keep_grid_probe": 229_376,
}
PRESENT_SAFETY_RESOURCE_CLAIM_GATES = frozenset({
    "safety",
    "matched_actor_critic_parameters",
    "matched_native_actor_calls",
    "matched_native_resource_work",
    "ONLGR_latency_at_most_1_10_RAW",
    "all_atomic_cell_commits_within_process_slice_limit",
    "recovery_RSS_strictly_below_1GiB",
    "recovery_exactly_one_CPU_worker",
    "recovery_no_GPU_use",
})
TECHNICAL_FACT_EXPECTED_POLARITY = {
    "training_or_parameter_update_performed": False,
}


class RecoveryRefused(RuntimeError):
    """Fail-closed recovery precondition or execution-contract failure."""


class RecoverySliceIncomplete(RuntimeError):
    """A bounded process slice ended cleanly at an episode/cell boundary."""


def _enforce_slice_deadline(
    slice_started: float, slice_seconds: float, boundary: str,
) -> None:
    if time.perf_counter() - slice_started >= slice_seconds:
        raise RecoverySliceIncomplete(f"process slice deadline reached at {boundary}")


def _enforce_atomic_replace_window(slice_started: float, slice_seconds: float) -> None:
    if time.perf_counter() - slice_started + ATOMIC_REPLACE_RESERVE_SECONDS >= slice_seconds:
        raise RecoverySliceIncomplete(
            "insufficient requested-slice time remains for atomic replacement"
        )


class FrozenLearner:
    """Inference-only actor/critic facade with no optimizer or training API."""

    def __init__(self, seed: int, arm: str, actor: MarkedActor, critic: CentralCritic) -> None:
        self.seed = seed
        self.arm = arm
        self.actor = actor.eval()
        self.critic = critic.eval()
        for parameter in (*self.actor.parameters(), *self.critic.parameters()):
            parameter.requires_grad_(False)

    @property
    def actor_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.actor.parameters())

    @property
    def critic_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.critic.parameters())

    def policy(
        self, features: np.ndarray, exposure: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        with torch.inference_mode():
            x = torch.as_tensor(features, dtype=torch.float32)
            e = torch.as_tensor(exposure, dtype=torch.float32)
            logits, _mark_logits = self.actor(x)
            event, mark = self.actor.probabilities(x, e)
            return logits.numpy(), event.numpy(), mark.numpy()

    def value(self, features: np.ndarray) -> float:
        with torch.inference_mode():
            x = torch.as_tensor(features, dtype=torch.float32).unsqueeze(0)
            return float(self.critic(x).item())

    def joint_log_probability(
        self, features: np.ndarray, exposure: np.ndarray,
        actions: np.ndarray, policy_mask: np.ndarray,
    ) -> float:
        """Exact inference-only counterpart of MarkedLearner's implementation."""
        with torch.inference_mode():
            x = torch.as_tensor(features, dtype=torch.float32)
            e = torch.as_tensor(exposure, dtype=torch.float32)
            a = torch.as_tensor(actions, dtype=torch.long)
            mask = torch.as_tensor(policy_mask, dtype=torch.bool)
            agent_log = self.actor.categorical_log_probabilities(x, e, a)
            return float(
                torch.where(mask, agent_log, torch.zeros_like(agent_log)).sum().item()
            )


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryRefused(f"cannot load required JSON {path}: {exc}") from exc


def _json_safe(value: object) -> object:
    """Apply the sole authorized repair: encode NaN as unavailable/null."""
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            raise RecoveryRefused("infinite numeric output is not an authorized serialization repair")
    return value


def _atomic_json(
    path: Path, payload: Mapping[str, object], *, before_replace: object | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if before_replace is not None:
        if not callable(before_replace):
            raise TypeError("before_replace must be callable")
        before_replace()
    safe = _json_safe(payload)
    if before_replace is not None:
        before_replace()
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            encoder = json.JSONEncoder(indent=2, sort_keys=True, allow_nan=False)
            for index, chunk in enumerate(encoder.iterencode(safe)):
                stream.write(chunk)
                if before_replace is not None and index % 4096 == 0:
                    if not callable(before_replace):
                        raise TypeError("before_replace must be callable")
                    before_replace()
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if before_replace is not None:
            if not callable(before_replace):
                raise TypeError("before_replace must be callable")
            before_replace()
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class RecoveryLedger:
    """Per-cell ledger without legacy scientific-stop budgets.

    The registered 7M/45-minute/2-GiB facts remain result context, while this
    executor enforces the P0 recovery process envelope after every complete
    episode (the safe interruption boundary).
    """

    def __init__(self, *, slice_started: float, slice_seconds: float) -> None:
        self.started = time.perf_counter()
        self.slice_started = slice_started
        self.slice_seconds = slice_seconds
        self.actual_ticks = 0
        self.peak_rss = _rss_bytes()
        self.by_panel: dict[str, int] = {}
        self.conformance_episode_rows = 0
        self.exposure_ledger_rows = 0
        self.action_before_service_boundary_rows = 0
        self.action_changed_service_value_rows = 0
        self.segment_owned_ticks = 0
        self.exposure_closed_form_exact = True
        self.action_before_service_exact = True
        self.reward_service_cost_tick_exact = True
        self.segment_ownership_exact = True
        self.terminal_boundary_absent = True
        self.conformance_failures: list[dict[str, object]] = []
        self.check()

    def add(self, panel: str, rows: EpisodeResult | list[EpisodeResult]) -> None:
        values = [rows] if isinstance(rows, EpisodeResult) else list(rows)
        ticks = sum(row.physics_ticks for row in values)
        self.actual_ticks += ticks
        self.by_panel[panel] = self.by_panel.get(panel, 0) + ticks
        for row in values:
            self.conformance_episode_rows += 1
            self.exposure_ledger_rows += row.exposure_ledger_rows
            self.action_before_service_boundary_rows += row.action_before_service_boundary_rows
            self.action_changed_service_value_rows += row.action_changed_service_value_rows
            self.segment_owned_ticks += row.segment_owned_ticks
            self.exposure_closed_form_exact &= row.exposure_closed_form_exact
            self.action_before_service_exact &= row.action_before_service_exact
            self.reward_service_cost_tick_exact &= row.reward_service_cost_exact
            self.segment_ownership_exact &= row.segment_ownership_exact
            self.terminal_boundary_absent &= row.terminal_boundary_absent
            failed = [
                name for name, passed in (
                    ("exposure_closed_form", row.exposure_closed_form_exact),
                    ("action_before_service", row.action_before_service_exact),
                    ("reward_service_cost_tick", row.reward_service_cost_exact),
                    ("segment_ownership", row.segment_ownership_exact),
                    ("terminal_boundary_absence", row.terminal_boundary_absent),
                ) if not passed
            ]
            if failed:
                self.conformance_failures.append({
                    "panel": panel, "arm": row.arm, "schedule": row.schedule,
                    "failed_ledgers": failed,
                })
        self.check()

    def add_ticks(self, panel: str, ticks: int) -> None:
        self.actual_ticks += ticks
        self.by_panel[panel] = self.by_panel.get(panel, 0) + ticks
        self.check()

    def check(self) -> None:
        rss = _rss_bytes()
        self.peak_rss = max(self.peak_rss, rss)
        if self.peak_rss >= MAX_RSS_BYTES:
            raise RecoveryRefused("checkpoint-only recovery RSS reached the strict 1-GiB limit")
        _enforce_slice_deadline(
            self.slice_started, self.slice_seconds, "a safe episode boundary",
        )
        if torch.cuda.is_initialized():
            raise RecoveryRefused("GPU initialization is forbidden for checkpoint-only recovery")

    def facts(self) -> dict[str, object]:
        self.check()
        return {
            "actual_team_ticks": self.actual_ticks,
            "actual_team_ticks_by_panel": dict(self.by_panel),
            "worker_wall_seconds": time.perf_counter() - self.started,
            "slice_elapsed_seconds_at_commit": time.perf_counter() - self.slice_started,
            "peak_rss_bytes": self.peak_rss,
            "cpu_workers": 1,
            "observed_reward_exposure_ledger": {
                "episode_rows": self.conformance_episode_rows,
                "exposure_rows": self.exposure_ledger_rows,
                "action_before_service_boundary_rows": self.action_before_service_boundary_rows,
                "action_changed_service_value_rows": self.action_changed_service_value_rows,
                "segment_owned_ticks": self.segment_owned_ticks,
                "exposure_closed_form_exact": self.exposure_closed_form_exact,
                "action_before_service_exact": self.action_before_service_exact,
                "reward_service_cost_tick_exact": self.reward_service_cost_tick_exact,
                "segment_ownership_exact": self.segment_ownership_exact,
                "terminal_boundary_absent": self.terminal_boundary_absent,
                "failures": self.conformance_failures,
            },
        }


def _create_once(path: Path, payload: Mapping[str, object]) -> None:
    encoded = (json.dumps(_json_safe(payload), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise RecoveryRefused(f"exact-once recovery marker already exists: {path}") from exc
    with os.fdopen(fd, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_hash(
    value: object, *, slice_started: float | None = None,
    slice_seconds: float | None = None,
) -> str:
    digest = hashlib.sha256()
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), allow_nan=False)
    if slice_started is not None and slice_seconds is not None:
        _enforce_atomic_replace_window(slice_started, slice_seconds)
    safe = _json_safe(value)
    if slice_started is not None and slice_seconds is not None:
        _enforce_atomic_replace_window(slice_started, slice_seconds)
    for index, chunk in enumerate(encoder.iterencode(safe)):
        digest.update(chunk.encode("utf-8"))
        if index % 4096 == 0 and slice_started is not None and slice_seconds is not None:
            _enforce_atomic_replace_window(slice_started, slice_seconds)
    return digest.hexdigest()


def _source_identity() -> dict[str, object]:
    module_root = Path(__file__).resolve().parent
    files: dict[str, str] = {}
    for name in SOURCE_IDENTITY_FILES:
        path = module_root / name
        if not path.is_file() or path.is_symlink():
            raise RecoveryRefused(f"evaluator source file is absent or linked: {path}")
        files[name] = _sha256(path)
    frozen_contract = {
        "treatment": TREATMENT,
        "composite_revision": COMPOSITE_REVISION,
        "seeds": list(SEEDS),
        "learned_arms": list(LEARNED_ARMS),
        "train_schedules": list(TRAIN_SCHEDULES),
        "heldout_schedules": list(HELDOUT_SCHEDULES),
        "iid_schedule": IID_SCHEDULE,
        "horizon": PRODUCTION_CONFIG.horizon,
        "native_episodes": 32,
        "iid_episodes": 32,
        "safety_episodes": 16,
        "fixed_selection_episodes": PRODUCTION_CONFIG.fixed_selection_episodes,
        "fixed_evaluation_episodes": PRODUCTION_CONFIG.diagnostic_episodes,
        "keep_grid_episodes": 16,
        "fixed_rates": list(FIXED_RATES),
        "fixed_marks": list(FIXED_MARKS),
        "validation_roots": list(VALIDATION_ROOTS),
        "analyzers": [
            "analysis.primary_analysis", "analysis.iid_analysis",
            "analysis.summarize_episodes", "run._partition_analysis",
            "run._support_facts", "recovery._iid_pairing_seed",
        ],
        "iid_reward_decomposition": {
            "definition": "R_IID := S_IID - C_IID",
            "accumulation_dtype": "float64",
            "absolute_tolerance": 1e-12,
            "relative_tolerance": 1e-10,
        },
        "optional_panels_excluded": ["clamp", "oracle", "yoke"],
    }
    return {
        "revision": SOURCE_IDENTITY_REVISION,
        "files": files,
        "frozen_contract": frozen_contract,
        "composite_sha256": _canonical_hash({"files": files, "contract": frozen_contract}),
    }


def _module_digest(learner: FrozenLearner) -> str:
    digest = hashlib.sha256()
    for prefix, module in (("actor", learner.actor), ("critic", learner.critic)):
        for name, tensor in sorted(module.state_dict().items()):
            digest.update(f"{prefix}:{name}:{tensor.dtype}:{tuple(tensor.shape)}".encode())
            digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _expected_registration() -> dict[str, object]:
    config = PRODUCTION_CONFIG
    return json.loads(json.dumps({
        "artifact_kind": ARTIFACT_KIND,
        "treatment": TREATMENT,
        "configuration": config.__dict__,
        "ppo": PPO,
        "requested_conservative_budget": registered_budget(config),
        "preselected_exact_yoke": {
            "candidate_count": 1,
            "complexity": "O(H*N)",
            "joint_cyclic_rotations": True,
            "outcome_blind_selection": True,
        },
    }))


def _validate_original_registration(output_root: Path) -> dict[str, object]:
    registration = _load_json(output_root / "registration.json")
    if registration != _expected_registration():
        raise RecoveryRefused("original registration is not the exact frozen ONLGR registration")
    return registration


def _validate_original_activity(output_root: Path) -> dict[str, object]:
    activity = _load_json(output_root / "activity_start.json")
    required = {
        "seed": SEEDS[0],
        "began": True,
        "trigger": "first_retained_learned_state_update",
        "first_update_index": 0,
        "first_updated_arm": LEARNED_ARMS[0],
    }
    if not isinstance(activity, dict) or any(activity.get(key) != value for key, value in required.items()):
        raise RecoveryRefused("original D11 activity marker is absent or contract-invalid")
    retained = Path(str(activity.get("retained_state_path", "")))
    if not retained.is_absolute():
        retained = (Path.cwd() / retained).resolve()
    expected = (output_root / "checkpoints" / f"seed_{SEEDS[0]}" / f"activity_start_{LEARNED_ARMS[0]}.pt").resolve()
    if retained != expected or not expected.is_file():
        raise RecoveryRefused("original D11 retained-state path is absent or does not match the marker")
    return activity


def _command_path(command: list[str], flag: str, cwd: Path) -> Path | None:
    try:
        value = command[command.index(flag) + 1]
    except (ValueError, IndexError):
        return None
    path = Path(value)
    return (cwd / path).resolve() if not path.is_absolute() else path.resolve()


def _validate_original_terminal(
    terminal_path: Path, output_root: Path, original_result: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    terminal = _load_json(terminal_path)
    if not isinstance(terminal, dict):
        raise RecoveryRefused("original terminal must be a JSON object")
    exit_code = terminal.get("exit_code")
    command = terminal.get("command")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int) or exit_code == 0:
        raise RecoveryRefused("original terminal must record a nonzero integer exit code")
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        raise RecoveryRefused("original terminal command must be an argv string list")
    cwd = Path(str(terminal.get("cwd", ""))).resolve()
    if not cwd.is_dir():
        raise RecoveryRefused("original terminal working directory is absent or invalid")
    command_text = " ".join(command)
    expected_modules = {
        "experiments.candidates.opportunity_normalized_lease_gated_rebinding",
        "experiments.candidates.opportunity_normalized_lease_gated_rebinding.run",
    }
    mandated = Path("C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe").resolve()
    if (len(command) != 8 or Path(command[0]).resolve() != mandated
            or command[1] != "-m" or command[2] not in expected_modules
            or command[3] != "train-evaluate-analyze"
            or "experiments.candidates.opportunity_normalized_lease_gated_rebinding" not in command_text):
        raise RecoveryRefused("original terminal is not for the registered ONLGR production command")
    if _command_path(command, "--output-root", cwd) != output_root:
        raise RecoveryRefused("original terminal output-root does not match the supplied original output")
    if _command_path(command, "--result", cwd) != original_result:
        raise RecoveryRefused("original terminal result path does not match the supplied absent result")
    if bool(terminal.get("process_live", False)):
        raise RecoveryRefused("original terminal reports a live scientific process")
    if terminal.get("scientific_activity_started") not in (True, "unknown"):
        raise RecoveryRefused(
            "original terminal activity observation must be exactly true or unknown; "
            "D11 truth is validated independently from activity_start.json"
        )
    try:
        started = datetime.fromisoformat(str(terminal["started_at"]))
        ended = datetime.fromisoformat(str(terminal["ended_at"]))
    except (KeyError, ValueError) as exc:
        raise RecoveryRefused("original terminal timestamps are absent or invalid") from exc
    if started.tzinfo is None or ended.tzinfo is None or ended <= started:
        raise RecoveryRefused("original terminal timestamps must be ordered and timezone-aware")
    resource_keys = ("wall_seconds", "peak_rss_bytes", "cpu_workers", "actual_team_ticks")
    nested = terminal.get("resources") if isinstance(terminal.get("resources"), dict) else {}
    resources = {
        key: terminal[key] if key in terminal else nested.get(key, "unavailable")
        for key in resource_keys
    }
    resources["observed_process_wall_seconds"] = (ended - started).total_seconds()
    return terminal, resources


def _matching_processes(output_root: Path) -> list[object]:
    if os.name != "nt":
        raise RecoveryRefused("matching-process guard is implemented only for the registered Windows host")
    escaped_root = str(output_root).replace("'", "''")
    script = (
        f"$selfPid={os.getpid()}; "
        "$needle='experiments.candidates.opportunity_normalized_lease_gated_rebinding'; "
        f"$root='{escaped_root}'; "
        "$rows=Get-CimInstance Win32_Process | Where-Object { "
        "$_.ProcessId -ne $selfPid -and $_.Name -match '^python(w)?\\.exe$' -and "
        "$_.CommandLine -and -not $_.CommandLine.Contains('hmasd_run_observed_command.py') -and "
        "$_.CommandLine.Contains($needle) -and $_.CommandLine.Contains($root) }; "
        "if($rows){$rows | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress}else{'[]'}"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, timeout=20, check=False,
    )
    if completed.returncode != 0:
        raise RecoveryRefused(f"cannot establish matching-process guard: {completed.stderr.strip()}")
    decoded = json.loads(completed.stdout.strip() or "[]")
    return [decoded] if isinstance(decoded, dict) else decoded


def _tensor_contract(
    state: object, expected: Mapping[str, torch.Tensor], label: str,
) -> dict[str, torch.Tensor]:
    if not isinstance(state, dict) or set(state) != set(expected):
        raise RecoveryRefused(f"{label} state keys are not exact")
    for key, expected_tensor in expected.items():
        tensor = state[key]
        if (not isinstance(tensor, torch.Tensor) or tensor.shape != expected_tensor.shape
                or tensor.dtype != expected_tensor.dtype or not bool(torch.isfinite(tensor).all())):
            raise RecoveryRefused(f"{label} tensor contract failed: {key}")
    return state


def _load_checkpoint(path: Path, seed: int, arm: str) -> tuple[FrozenLearner, dict[str, object]]:
    if not path.is_file() or path.is_symlink() or path.with_suffix(path.suffix + ".tmp").exists():
        raise RecoveryRefused(f"final checkpoint is absent, linked, or has a temporary sibling: {path}")
    before_hash = _sha256(path)
    try:
        payload = torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:
        raise RecoveryRefused(f"final checkpoint cannot be loaded: {path}: {exc}") from exc
    expected_keys = {
        "treatment_arm", "seed", "actor", "critic", "optimizer",
        "actor_parameter_count", "critic_parameter_count",
    }
    if not isinstance(payload, dict) or set(payload) != expected_keys:
        raise RecoveryRefused(f"checkpoint schema keys are not exact: {path}")
    if payload["treatment_arm"] != arm or payload["seed"] != seed:
        raise RecoveryRefused(f"checkpoint identity mismatch: {path}")
    actor, critic = MarkedActor(arm), CentralCritic()
    actor_state = _tensor_contract(payload["actor"], actor.state_dict(), f"{seed}:{arm}:actor")
    critic_state = _tensor_contract(payload["critic"], critic.state_dict(), f"{seed}:{arm}:critic")
    if payload["actor_parameter_count"] != sum(p.numel() for p in actor.parameters()):
        raise RecoveryRefused(f"actor parameter-count mismatch: {path}")
    if payload["critic_parameter_count"] != sum(p.numel() for p in critic.parameters()):
        raise RecoveryRefused(f"critic parameter-count mismatch: {path}")
    optimizer = payload["optimizer"]
    if not isinstance(optimizer, dict) or set(optimizer) != {"state", "param_groups"}:
        raise RecoveryRefused(f"retained optimizer provenance is contract-invalid: {path}")
    steps = []
    for row in optimizer["state"].values():
        if not isinstance(row, dict) or "step" not in row:
            raise RecoveryRefused(f"retained optimizer step provenance is incomplete: {path}")
        step = row["step"]
        steps.append(int(step.item()) if isinstance(step, torch.Tensor) else int(step))
    if not steps or set(steps) != {32}:
        raise RecoveryRefused(f"checkpoint is not the sole final 32-step learned state: {path}")
    actor.load_state_dict(actor_state, strict=True)
    critic.load_state_dict(critic_state, strict=True)
    learner = FrozenLearner(seed, arm, actor, critic)
    return learner, {
        "path": str(path), "sha256_before": before_hash,
        "treatment_arm": arm, "seed": seed,
        "actor_parameter_count": learner.actor_parameter_count,
        "critic_parameter_count": learner.critic_parameter_count,
        "retained_optimizer_steps": 32,
        "optimizer_loaded_or_constructed_for_recovery": False,
        "parameters_require_grad": False,
        "in_memory_state_sha256_before": _module_digest(learner),
    }


def _load_all_checkpoints(
    output_root: Path,
) -> tuple[dict[str, dict[str, FrozenLearner]], dict[str, dict[str, object]]]:
    checkpoint_root = output_root / "checkpoints"
    expected_paths = {
        (checkpoint_root / f"seed_{seed}" / f"{arm}.pt").resolve()
        for seed in SEEDS for arm in LEARNED_ARMS
    }
    observed_final_paths = {
        path.resolve() for path in checkpoint_root.rglob("*.pt")
        if path.name in {f"{arm}.pt" for arm in LEARNED_ARMS}
    }
    if observed_final_paths != expected_paths:
        raise RecoveryRefused("the 24 sole final checkpoint paths are missing or ambiguous")
    learners: dict[str, dict[str, FrozenLearner]] = {}
    facts: dict[str, dict[str, object]] = {}
    for seed in SEEDS:
        seed_key = str(seed)
        learners[seed_key] = {}
        facts[seed_key] = {}
        for arm in LEARNED_ARMS:
            path = checkpoint_root / f"seed_{seed}" / f"{arm}.pt"
            learner, row = _load_checkpoint(path, seed, arm)
            learners[seed_key][arm] = learner
            facts[seed_key][arm] = row
    return learners, facts


def _first_attempt_yoke_accounting(path: Path | None) -> tuple[int, dict[str, object]]:
    if path is None:
        return FIRST_ATTEMPT_YOKE_MAX_TICKS, {
            "source": "conservative_maximum_due_to_absent_non_outcome_ledger",
            "Y": FIRST_ATTEMPT_YOKE_MAX_TICKS,
        }
    ledger = _load_json(path)
    expected_keys = {"artifact_kind", "preselected_exact_yoke_team_ticks"}
    if not isinstance(ledger, dict) or set(ledger) != expected_keys \
            or ledger.get("artifact_kind") != "ONLGR_NON_OUTCOME_EXECUTION_LEDGER":
        raise RecoveryRefused("first-attempt yoke ledger is not the exact non-outcome schema")
    value = ledger["preselected_exact_yoke_team_ticks"]
    if (isinstance(value, bool) or not isinstance(value, int)
            or not 0 <= value <= FIRST_ATTEMPT_YOKE_MAX_TICKS or value % 512 != 0):
        raise RecoveryRefused("first-attempt non-outcome yoke tick count is outside [0,458752]")
    return value, {"source": str(path), "Y": value, "ledger": ledger}


def _fixed_heldout(
    seed: int, fixed: tuple[float, float], ledger: RecoveryLedger,
) -> dict[str, object]:
    output: dict[str, object] = {}
    for schedule in HELDOUT_SCHEDULES:
        rows: list[EpisodeResult] = []
        for episode_index in range(PRODUCTION_CONFIG.diagnostic_episodes):
            exogenous = generate_episode(
                root=seed, episode=episode_index, namespace="paired_native",
                schedule=schedule, horizon=PRODUCTION_CONFIG.horizon,
            )
            row = run_episode(exogenous, arm="FIXED-RATE-LEASE", fixed_rate=fixed)
            rows.append(row)
            ledger.add("fixed_rate_evaluation", row)
        output[schedule] = summarize_episodes(rows)
    return output


def _analytic_initialization_curves() -> dict[str, object]:
    output: dict[str, object] = {}
    for arm in LEARNED_ARMS:
        g = initial_event_bias(arm)
        rho = 0.5
        rows: dict[str, object] = {}
        for exposure in (1, 4, 8, 16, 24, 32):
            u = (1.0 / (1.0 + math.exp(-g)) if arm == "RAW-BOUNDARY-LEASE"
                 else -math.expm1(-math.log1p(math.exp(g)) * exposure))
            event_entropy = -(u * math.log(u) + (1-u) * math.log1p(-u))
            mark_entropy = math.log(2.0)
            rows[str(exposure)] = {
                "u": u, "rho": rho, "event_entropy": event_entropy,
                "conditional_mark_entropy": mark_entropy,
                "applied_mark_entropy": u * mark_entropy,
                "marked_entropy": event_entropy + u * mark_entropy,
                "u_below_0.01": u < .01, "u_above_0.99": u > .99,
            }
        output[arm] = rows
    return output


def _cap_context() -> dict[str, object]:
    return {
        "registered_7m_tick_cap_pass": False,
        "interpretation": "arm-matched finite-panel recovery observation only",
        "project_facing_without_resource_failure_claim_available": False,
    }


def _attach_cap_context(analysis: dict[str, object]) -> dict[str, object]:
    analysis["recovery_resource_context"] = _cap_context()
    contrasts = analysis.get("paired_contrasts", analysis.get("contrasts", {}))
    if isinstance(contrasts, dict):
        for row in contrasts.values():
            if isinstance(row, dict):
                row["recovery_resource_context"] = _cap_context()
    for key in ("RAW_minus_ONLGR", "MPI_intervals"):
        if isinstance(analysis.get(key), dict):
            analysis[key]["recovery_resource_context"] = _cap_context()  # type: ignore[index]
    return analysis


def _core_missing(
    native: dict[str, object], iid: dict[str, object], safety: dict[str, object],
    partitions: dict[str, object], fixed_selection: dict[str, object],
    fixed_evaluation: dict[str, object], keep: dict[str, object],
    leakage: dict[str, object], resources: dict[str, object],
) -> list[str]:
    missing: list[str] = []
    for seed in SEEDS:
        key = str(seed)
        for arm in LEARNED_ARMS:
            for schedule in HELDOUT_SCHEDULES:
                if int(native.get(key, {}).get(arm, {}).get(schedule, {}).get("episodes", -1)) != 32:  # type: ignore[union-attr]
                    missing.append(f"native:{seed}:{arm}:{schedule}")
                if int(safety.get(key, {}).get(arm, {}).get(schedule, {}).get("episodes", -1)) != 16:  # type: ignore[union-attr]
                    missing.append(f"safety:{seed}:{arm}:{schedule}")
            if int(iid.get(key, {}).get(arm, {}).get("episodes", -1)) != 32:  # type: ignore[union-attr]
                missing.append(f"iid:{seed}:{arm}")
        if len(partitions.get(key, {}).get("cells", ())) != 16:  # type: ignore[union-attr]
            missing.append(f"partition:{seed}")
        for schedule in HELDOUT_SCHEDULES:
            if int(fixed_evaluation.get(key, {}).get(schedule, {}).get("episodes", -1)) != 16:  # type: ignore[union-attr]
                missing.append(f"fixed:{seed}:{schedule}")
        if int(keep.get(key, {}).get("episodes_per_schedule", -1)) != 16:  # type: ignore[union-attr]
            missing.append(f"keep:{seed}")
        if not bool(leakage.get(key, {}).get("complete", False)):  # type: ignore[union-attr]
            missing.append(f"switch_twin:{seed}")
    grid = fixed_selection.get("grid", ())
    if len(grid) != len(FIXED_RATES) * len(FIXED_MARKS) or any(
        int(row.get("episodes", -1)) != len(VALIDATION_ROOTS) * len(TRAIN_SCHEDULES) * 16
        for row in grid
    ):
        missing.append("fixed_rate_validation_grid")
    actual_panels = resources.get("actual_team_ticks_by_panel", {})
    for panel, expected in EXPECTED_RECOVERY_PANELS.items():
        if int(actual_panels.get(panel, -1)) != expected:  # type: ignore[union-attr]
            missing.append(f"recovery_ticks:{panel}")
    if int(resources.get("actual_team_ticks", -1)) != RECOVERY_INCREMENT_TICKS:
        missing.append("recovery_ticks:total")
    return missing


def _checkpoint_hashes(checkpoint_facts: Mapping[str, Mapping[str, object]]) -> dict[str, str]:
    return {
        f"{seed}:{arm}": str(checkpoint_facts[str(seed)][arm]["sha256_before"])
        for seed in SEEDS for arm in LEARNED_ARMS
    }


def _validate_or_create_marker(path: Path, expected: Mapping[str, object]) -> None:
    if path.exists():
        observed = _load_json(path)
        if observed != dict(expected):
            raise RecoveryRefused(
                "historical recovery marker does not exactly match paths, checkpoints, and recovery identity"
            )
        return
    _create_once(path, expected)


def _cell_path(frontier_root: Path, cell_id: str) -> Path:
    readable = cell_id.replace(":", "__")
    if not readable.replace("_", "").replace("-", "").isalnum():
        raise RecoveryRefused(f"unsafe frontier cell identity: {cell_id}")
    return frontier_root / f"{readable}.json"


def _prepare_frontier_root(recovery_output_root: Path) -> Path:
    """Select fresh v3 while preserving, but never traversing, sealed v2 evidence."""
    frontier_root = recovery_output_root / FRONTIER_DIRECTORY
    preserved = {
        recovery_output_root / name for name in PRESERVED_INERT_FRONTIER_DIRECTORIES
    }
    allowed = {frontier_root, *preserved}
    unexpected = {path for path in recovery_output_root.iterdir() if path not in allowed}
    if unexpected:
        raise RecoveryRefused(
            "historical recovery root contains an unexpected entry; all evidence was left untouched"
        )
    for path in preserved:
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise RecoveryRefused(
                "preserved v2 frontier identity is not an exact real directory"
            )
    if frontier_root.is_symlink() or (frontier_root.exists() and not frontier_root.is_dir()):
        raise RecoveryRefused("active v3 frontier is not an exact real directory")
    frontier_root.mkdir(parents=False, exist_ok=True)
    return frontier_root


def _run_or_load_cell(
    *, frontier_root: Path, cell_id: str, marker_sha256: str,
    checkpoint_sha256: Mapping[str, str], source_identity: Mapping[str, object], slice_started: float,
    slice_seconds: float, work: object,
) -> dict[str, object]:
    _enforce_slice_deadline(slice_started, slice_seconds, "a frontier cell boundary")
    path = _cell_path(frontier_root, cell_id)
    if path.exists():
        _enforce_atomic_replace_window(slice_started, slice_seconds)
        payload = _load_json(path)
        required = {
            "artifact_kind", "frontier_revision", "cell_id", "marker_sha256",
            "checkpoint_sha256", "source_identity", "content_sha256", "data", "resources",
        }
        if (not isinstance(payload, dict) or set(payload) != required
                or payload.get("artifact_kind") != "ONLGR_CHECKPOINT_ONLY_CORE_ATOMIC_CELL"
                or payload.get("frontier_revision") != FRONTIER_REVISION
                or payload.get("cell_id") != cell_id
                or payload.get("marker_sha256") != marker_sha256
                or payload.get("checkpoint_sha256") != dict(checkpoint_sha256)
                or payload.get("source_identity") != dict(source_identity)
                or not isinstance(payload.get("data"), dict)
                or not isinstance(payload.get("resources"), dict)
                or payload.get("content_sha256") != _canonical_hash({
                    "data": payload.get("data"), "resources": payload.get("resources"),
                }, slice_started=slice_started, slice_seconds=slice_seconds)):
            raise RecoveryRefused(f"frontier cell is not exact or is identity-incompatible: {path}")
        _enforce_slice_deadline(slice_started, slice_seconds, "an existing-cell reuse boundary")
        return payload
    ledger = RecoveryLedger(slice_started=slice_started, slice_seconds=slice_seconds)
    if not callable(work):
        raise TypeError("frontier work must be callable")
    data = work(ledger)
    ledger.check()
    if not isinstance(data, dict):
        raise RecoveryRefused(f"frontier cell did not produce an object: {cell_id}")
    resources = ledger.facts()
    resources["requested_slice_seconds"] = slice_seconds
    resources["slice_elapsed_seconds_at_commit_conservative_upper_bound"] = slice_seconds
    payload = {
        "artifact_kind": "ONLGR_CHECKPOINT_ONLY_CORE_ATOMIC_CELL",
        "frontier_revision": FRONTIER_REVISION,
        "cell_id": cell_id,
        "marker_sha256": marker_sha256,
        "checkpoint_sha256": dict(checkpoint_sha256),
        "source_identity": dict(source_identity),
        "data": data,
        "resources": resources,
        "content_sha256": _canonical_hash(
            {"data": data, "resources": resources},
            slice_started=slice_started, slice_seconds=slice_seconds,
        ),
    }
    _atomic_json(
        path, payload,
        before_replace=lambda: _enforce_atomic_replace_window(slice_started, slice_seconds),
    )
    _enforce_slice_deadline(slice_started, slice_seconds, "a completed atomic cell commit")
    return payload


def _iid_pairing_seed(
    seed: int, retained: Mapping[str, Mapping[str, list[EpisodeResult]]],
) -> dict[str, object]:
    failures: list[dict[str, object]] = []
    reference_rows = retained["ONLGR"][IID_SCHEDULE]
    for episode_index in range(len(reference_rows)):
        rows = [retained[arm][IID_SCHEDULE][episode_index] for arm in LEARNED_ARMS]
        reference = rows[0]
        paired = all(
            row.iid_interval_draws == reference.iid_interval_draws
            and row.routine_boundary_ticks == reference.routine_boundary_ticks
            and row.iid_terminal_censored_duration == reference.iid_terminal_censored_duration
            for row in rows[1:]
        )
        well_formed = bool(
            len(reference.iid_interval_draws) == len(reference.routine_boundary_ticks)
            and reference.iid_interval_draws
            and all(value in (4, 16, 32) for value in reference.iid_interval_draws)
            and reference.routine_boundary_ticks[0] == 0
            and 256 not in reference.routine_boundary_ticks
            and reference.iid_terminal_censored_duration is not None
            and reference.routine_boundary_ticks[-1]
                + reference.iid_terminal_censored_duration == 256
        )
        if not paired or not well_formed:
            failures.append({
                "seed": seed, "episode_index": episode_index,
                "paired_across_arms": paired, "well_formed": well_formed,
            })
    return {"audited": len(reference_rows), "failures": failures}


def _merge_iid_pairing(cells: Mapping[str, object]) -> dict[str, object]:
    failures = [
        failure
        for seed in SEEDS
        for failure in cells[str(seed)]["failures"]  # type: ignore[index]
    ]
    audited = sum(int(cells[str(seed)]["audited"]) for seed in SEEDS)  # type: ignore[index]
    return {
        "domain": "RAND_IID_NEXT_K",
        "action_domains": ["ACTION_T", "ACTION_R"],
        "audited_seed_episode_pairs": audited,
        "paired_across_arms": not failures,
        "draw_ordinal_increments_once_per_realized_routine_action": not failures,
        "terminal_censoring_exact": not failures,
        "failures": failures,
    }


def _merge_resources(cells: list[dict[str, object]]) -> dict[str, object]:
    panel_ticks: dict[str, int] = {}
    ledger_rows = {
        "episode_rows": 0,
        "exposure_rows": 0,
        "action_before_service_boundary_rows": 0,
        "action_changed_service_value_rows": 0,
        "segment_owned_ticks": 0,
    }
    exact_fields = (
        "exposure_closed_form_exact", "action_before_service_exact",
        "reward_service_cost_tick_exact", "segment_ownership_exact",
        "terminal_boundary_absent",
    )
    exact = {field: True for field in exact_fields}
    failures: list[object] = []
    total_ticks = 0
    peak_rss = 0
    worker_wall = 0.0
    max_slice_elapsed = 0.0
    for cell in cells:
        resources = cell["resources"]
        total_ticks += int(resources["actual_team_ticks"])  # type: ignore[index]
        peak_rss = max(peak_rss, int(resources["peak_rss_bytes"]))  # type: ignore[index]
        worker_wall += float(resources["worker_wall_seconds"])  # type: ignore[index]
        max_slice_elapsed = max(
            max_slice_elapsed,
            float(resources["slice_elapsed_seconds_at_commit_conservative_upper_bound"])  # type: ignore[index]
        )
        for panel, ticks in resources["actual_team_ticks_by_panel"].items():  # type: ignore[index,union-attr]
            panel_ticks[str(panel)] = panel_ticks.get(str(panel), 0) + int(ticks)
        observed = resources["observed_reward_exposure_ledger"]  # type: ignore[index]
        for field in ledger_rows:
            ledger_rows[field] += int(observed[field])  # type: ignore[index]
        for field in exact_fields:
            exact[field] &= bool(observed[field])  # type: ignore[index]
        failures.extend(observed["failures"])  # type: ignore[index]
    return {
        "actual_team_ticks": total_ticks,
        "actual_team_ticks_by_panel": panel_ticks,
        "wall_seconds": worker_wall,
        "worker_wall_seconds_across_atomic_cells": worker_wall,
        "maximum_slice_elapsed_seconds_at_cell_commit_conservative_upper_bound": max_slice_elapsed,
        "peak_rss_bytes": peak_rss,
        "cpu_workers": 1,
        "gpu_used": False,
        "slice_seconds_limit": MAX_SLICE_SECONDS,
        "observed_reward_exposure_ledger": {
            **ledger_rows, **exact, "failures": failures,
        },
    }


def _completion_partition(
    missing: list[str], conformance: Mapping[str, bool],
) -> tuple[bool, dict[str, bool], dict[str, bool]]:
    """Separate package coherence from observed claim eligibility.

    Present safety/resource failures suppress their claims but are themselves
    complete observations.  Missing rows and technical/data incoherence still
    prevent a complete coherent package.
    """
    absent = PRESENT_SAFETY_RESOURCE_CLAIM_GATES - set(conformance)
    if absent:
        raise RecoveryRefused(f"safety/resource claim gate facts are absent: {sorted(absent)}")
    technical = {
        name: bool(value) for name, value in conformance.items()
        if name not in PRESENT_SAFETY_RESOURCE_CLAIM_GATES
    }
    claim_gates = {
        name: bool(conformance[name]) for name in sorted(PRESENT_SAFETY_RESOURCE_CLAIM_GATES)
    }
    technical_matches_expected = all(
        value is TECHNICAL_FACT_EXPECTED_POLARITY.get(name, True)
        for name, value in technical.items()
    )
    return not missing and technical_matches_expected, technical, claim_gates


def _historical_non_gating_process_facts(resources: Mapping[str, object]) -> dict[str, object]:
    aggregate_wall = float(resources["wall_seconds"])
    return {
        "historical_2700s_wall_fence_seconds": 45 * 60,
        "checkpoint_only_core_aggregate_wall_seconds": aggregate_wall,
        "historical_2700s_wall_fence_pass_for_checkpoint_only_core": (
            aggregate_wall <= 45 * 60
        ),
        "historical_2700s_wall_fence_execution_or_completeness_authority": False,
        "historical_exact_once_no_rescue_marker_execution_or_completeness_authority": False,
    }


def recover(
    *, original_output_root: Path, original_result_path: Path,
    original_terminal_path: Path, recovery_output_root: Path,
    recovery_result_path: Path, first_attempt_non_outcome_ledger: Path | None = None,
    slice_seconds: float = MAX_SLICE_SECONDS,
) -> dict[str, object]:
    slice_started = time.perf_counter()
    if not ATOMIC_REPLACE_RESERVE_SECONDS < slice_seconds <= MAX_SLICE_SECONDS:
        raise RecoveryRefused(
            "slice seconds must leave the atomic-replace reserve and be at most "
            f"{MAX_SLICE_SECONDS} seconds"
        )
    original_output_root = original_output_root.resolve()
    original_result_path = original_result_path.resolve()
    original_terminal_path = original_terminal_path.resolve()
    recovery_output_root = recovery_output_root.resolve()
    recovery_result_path = recovery_result_path.resolve()
    marker = original_output_root / MARKER_NAME
    if not original_output_root.is_dir():
        raise RecoveryRefused("original output root is absent")
    if original_result_path.exists() or (original_output_root / "raw_result.json").exists():
        raise RecoveryRefused("an original retained result or raw result exists")
    if recovery_result_path.exists():
        raise RecoveryRefused("retained recovery result already exists and will not be overwritten")
    if recovery_result_path == recovery_output_root:
        raise RecoveryRefused("recovery output root and retained result path must be distinct")
    if recovery_output_root == original_output_root or original_output_root in recovery_output_root.parents:
        raise RecoveryRefused("recovery output must not be inside the original output root")
    if recovery_result_path == original_output_root or original_output_root in recovery_result_path.parents:
        raise RecoveryRefused("retained recovery result must not be inside the original output root")
    if _matching_processes(original_output_root):
        raise RecoveryRefused("a matching original or recovery scientific process is live")
    registration = _validate_original_registration(original_output_root)
    activity = _validate_original_activity(original_output_root)
    terminal, original_resources = _validate_original_terminal(
        original_terminal_path, original_output_root, original_result_path,
    )
    learners, checkpoint_facts = _load_all_checkpoints(original_output_root)
    yoke_ticks, yoke_accounting = _first_attempt_yoke_accounting(
        first_attempt_non_outcome_ledger.resolve() if first_attempt_non_outcome_ledger else None
    )
    cumulative_ticks = FIRST_ATTEMPT_NON_YOKE_TICKS + yoke_ticks + RECOVERY_INCREMENT_TICKS
    checkpoint_hashes = _checkpoint_hashes(checkpoint_facts)
    marker_payload = {
        "artifact_kind": "ONLGR_CHECKPOINT_ONLY_CORE_EXACT_ONCE_MARKER",
        "recovery_identity": RECOVERY_IDENTITY,
        "decision": RECOVERY_DECISION,
        "original_output_root": str(original_output_root),
        "original_result_path": str(original_result_path),
        "original_terminal_path": str(original_terminal_path),
        "recovery_output_root": str(recovery_output_root),
        "recovery_result_path": str(recovery_result_path),
        "checkpoint_sha256": checkpoint_hashes,
        "first_attempt_yoke_accounting": yoke_accounting,
        "exact_recovery_ticks": RECOVERY_INCREMENT_TICKS,
        "cumulative_ticks": cumulative_ticks,
    }
    _validate_or_create_marker(marker, marker_payload)
    if recovery_output_root.exists() and (
        not recovery_output_root.is_dir() or recovery_output_root.is_symlink()
    ):
        raise RecoveryRefused("historical recovery output root is not an exact real directory")
    recovery_output_root.mkdir(parents=True, exist_ok=True)
    frontier_root = _prepare_frontier_root(recovery_output_root)
    marker_hash = _sha256(marker)
    source_identity = _source_identity()
    expected_cell_ids = {"fixed_selection"} | {
        f"{panel}:{seed}"
        for seed in SEEDS
        for panel in ("native", "iid", "safety", "fixed_evaluation", "probes")
    }
    expected_paths = {_cell_path(frontier_root, cell_id) for cell_id in expected_cell_ids}
    expected_names = {path.name for path in expected_paths}
    unexpected = {
        path for path in frontier_root.iterdir()
        if path not in expected_paths and not (
            path.is_file() and path.name.startswith(".") and path.name.endswith(".tmp")
            and any(path.name.startswith(f".{name}.") for name in expected_names)
        )
    }
    if unexpected:
        raise RecoveryRefused("frontier contains unexpected files; historical evidence was left untouched")

    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError as exc:
            raise RecoveryRefused("cannot enforce exactly one torch interop worker") from exc
    if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
        raise RecoveryRefused("cannot enforce exactly one CPU worker")
    torch.set_grad_enabled(False)
    if torch.cuda.is_initialized():
        raise RecoveryRefused("GPU was initialized before checkpoint-only recovery")

    cells: list[dict[str, object]] = []
    fixed_cell = _run_or_load_cell(
        frontier_root=frontier_root, cell_id="fixed_selection",
        marker_sha256=marker_hash, checkpoint_sha256=checkpoint_hashes,
        source_identity=source_identity,
        slice_started=slice_started, slice_seconds=slice_seconds,
        work=lambda ledger: {"fixed_selection": select_fixed_rate(PRODUCTION_CONFIG, ledger)},
    )
    cells.append(fixed_cell)
    fixed_selection = fixed_cell["data"]["fixed_selection"]  # type: ignore[index]
    fixed = (
        float(fixed_selection["selected"]["lambda"]),  # type: ignore[index]
        float(fixed_selection["selected"]["rho"]),  # type: ignore[index]
    )
    native: dict[str, object] = {}
    iid: dict[str, object] = {}
    safety: dict[str, object] = {}
    fixed_evaluation: dict[str, object] = {}
    partitions: dict[str, object] = {}
    keep: dict[str, object] = {}
    leakage: dict[str, object] = {}
    iid_pairing_cells: dict[str, object] = {}
    for seed in SEEDS:
        key = str(seed)
        def native_work(ledger: RecoveryLedger, seed: int = seed, key: str = key) -> dict[str, object]:
            values, _ = _evaluate_learned_panel(
                seed=seed, learners=learners[key], config=PRODUCTION_CONFIG,
                count=32, namespace="paired_native", ledger=ledger, panel="native",
            )
            return {"metrics": values, "switch_twin": leakage_twin_contract(values, 32)}
        native_cell = _run_or_load_cell(
            frontier_root=frontier_root, cell_id=f"native:{seed}",
            marker_sha256=marker_hash, checkpoint_sha256=checkpoint_hashes,
            source_identity=source_identity,
            slice_started=slice_started, slice_seconds=slice_seconds, work=native_work,
        )
        cells.append(native_cell)
        native[key] = native_cell["data"]["metrics"]  # type: ignore[index]
        leakage[key] = native_cell["data"]["switch_twin"]  # type: ignore[index]

        def iid_work(ledger: RecoveryLedger, seed: int = seed, key: str = key) -> dict[str, object]:
            values, retained = _evaluate_learned_panel(
                seed=seed, learners=learners[key], config=PRODUCTION_CONFIG,
                count=32, namespace="paired_iid_future_k", ledger=ledger,
                panel="iid_future_k", schedules=(IID_SCHEDULE,), retain_first=32,
            )
            return {
                "metrics": {arm: values[arm][IID_SCHEDULE] for arm in LEARNED_ARMS},
                "pairing": _iid_pairing_seed(seed, retained),
            }
        iid_cell = _run_or_load_cell(
            frontier_root=frontier_root, cell_id=f"iid:{seed}",
            marker_sha256=marker_hash, checkpoint_sha256=checkpoint_hashes,
            source_identity=source_identity,
            slice_started=slice_started, slice_seconds=slice_seconds, work=iid_work,
        )
        cells.append(iid_cell)
        iid[key] = iid_cell["data"]["metrics"]  # type: ignore[index]
        iid_pairing_cells[key] = iid_cell["data"]["pairing"]  # type: ignore[index]

        def safety_work(ledger: RecoveryLedger, seed: int = seed, key: str = key) -> dict[str, object]:
            values, _ = _evaluate_learned_panel(
                seed=seed, learners=learners[key], config=PRODUCTION_CONFIG,
                count=16, namespace="paired_safety", ledger=ledger,
                panel="safety", safety=True,
            )
            return {"metrics": values}
        safety_cell = _run_or_load_cell(
            frontier_root=frontier_root, cell_id=f"safety:{seed}",
            marker_sha256=marker_hash, checkpoint_sha256=checkpoint_hashes,
            source_identity=source_identity,
            slice_started=slice_started, slice_seconds=slice_seconds, work=safety_work,
        )
        cells.append(safety_cell)
        safety[key] = safety_cell["data"]["metrics"]  # type: ignore[index]

        fixed_cell = _run_or_load_cell(
            frontier_root=frontier_root, cell_id=f"fixed_evaluation:{seed}",
            marker_sha256=marker_hash, checkpoint_sha256=checkpoint_hashes,
            source_identity=source_identity,
            slice_started=slice_started, slice_seconds=slice_seconds,
            work=lambda ledger, seed=seed: {"metrics": _fixed_heldout(seed, fixed, ledger)},
        )
        cells.append(fixed_cell)
        fixed_evaluation[key] = fixed_cell["data"]["metrics"]  # type: ignore[index]

        def probes_work(ledger: RecoveryLedger, seed: int = seed, key: str = key) -> dict[str, object]:
            partition = marked_partition_probe(
                learners[key]["ONLGR"], learners[key]["RAW-BOUNDARY-LEASE"],
            )
            keep_value = keep_grid_equality(seed, 16)
            ledger.add_ticks("keep_grid_probe", int(keep_value["actual_team_ticks"]))
            return {"partition": partition, "keep": keep_value}
        probes_cell = _run_or_load_cell(
            frontier_root=frontier_root, cell_id=f"probes:{seed}",
            marker_sha256=marker_hash, checkpoint_sha256=checkpoint_hashes,
            source_identity=source_identity,
            slice_started=slice_started, slice_seconds=slice_seconds, work=probes_work,
        )
        cells.append(probes_cell)
        partitions[key] = probes_cell["data"]["partition"]  # type: ignore[index]
        keep[key] = probes_cell["data"]["keep"]  # type: ignore[index]

    resources = _merge_resources(cells)
    missing = _core_missing(
        native, iid, safety, partitions, fixed_selection,
        fixed_evaluation, keep, leakage, resources,
    )
    identity = prob_exp_identity_probe()
    partition_analysis = _attach_cap_context(_partition_analysis(partitions))
    primary = _attach_cap_context(primary_analysis(native))  # type: ignore[arg-type]
    iid_result = _attach_cap_context(iid_analysis(iid))  # type: ignore[arg-type]
    support = _support_facts(native, iid)
    iid_pairing = _merge_iid_pairing(iid_pairing_cells)
    safety_violations = sum(
        int(safety[str(seed)][arm][schedule]["safety_violations"])  # type: ignore[index]
        for seed in SEEDS for arm in LEARNED_ARMS for schedule in HELDOUT_SCHEDULES
    )
    actor_counts = {
        arm: {
            schedule: [
                int(native[str(seed)][arm][schedule]["resource"]["actor_calls"])  # type: ignore[index]
                for seed in SEEDS
            ] for schedule in HELDOUT_SCHEDULES
        } for arm in LEARNED_ARMS
    }
    calls_matched = all(
        actor_counts[LEARNED_ARMS[0]][schedule] == actor_counts[arm][schedule]
        for schedule in HELDOUT_SCHEDULES for arm in LEARNED_ARMS[1:]
    )
    native_resource_work_matched = all(
        len({
            int(native[str(seed)][arm][schedule]["resource"][field])  # type: ignore[index]
            for arm in LEARNED_ARMS
        }) == 1
        for seed in SEEDS for schedule in HELDOUT_SCHEDULES
        for field in ("actor_calls", "critic_calls", "messages", "bits", "physics_ticks")
    )
    parameters_matched = all(
        len({checkpoint_facts[str(seed)][arm]["actor_parameter_count"] for arm in LEARNED_ARMS}) == 1
        and len({checkpoint_facts[str(seed)][arm]["critic_parameter_count"] for arm in LEARNED_ARMS}) == 1
        for seed in SEEDS
    )
    onlgr_latency = [
        native[str(seed)]["ONLGR"][schedule]["resource"]["decision_latency_ms_p95"]  # type: ignore[index]
        for seed in SEEDS for schedule in HELDOUT_SCHEDULES
    ]
    raw_latency = [
        native[str(seed)]["RAW-BOUNDARY-LEASE"][schedule]["resource"]["decision_latency_ms_p95"]  # type: ignore[index]
        for seed in SEEDS for schedule in HELDOUT_SCHEDULES
    ]
    latency_ratio = float(
        np.percentile(onlgr_latency, 95) / max(1e-12, np.percentile(raw_latency, 95))
    )
    reward_ledger = resources["observed_reward_exposure_ledger"]
    checkpoint_immutable = True
    for seed in SEEDS:
        for arm in LEARNED_ARMS:
            row = checkpoint_facts[str(seed)][arm]
            path = Path(str(row["path"]))
            row["sha256_after"] = _sha256(path)
            row["in_memory_state_sha256_after"] = _module_digest(learners[str(seed)][arm])
            row["file_immutable"] = row["sha256_before"] == row["sha256_after"]
            row["in_memory_parameters_immutable"] = (
                row["in_memory_state_sha256_before"] == row["in_memory_state_sha256_after"]
            )
            checkpoint_immutable &= bool(row["file_immutable"] and row["in_memory_parameters_immutable"])
    conformance = {
        "exact_composite_revision": (
            COMPOSITE_REVISION == "ONLGR-PRO-MATH-CLOSURE-CANDIDATE-20260812-04"
            and MATHEMATICAL_CLOSURE_CONFIRMED
        ),
        "all_24_sole_final_checkpoints_valid_and_immutable": checkpoint_immutable,
        "no_optimizer_constructed_or_loaded_for_recovery": True,
        "gradient_calculation_disabled": not torch.is_grad_enabled(),
        "training_or_parameter_update_performed": False,
        "analytic_probability_and_full_jacobian": bool(identity["pass"]),
        "partition_probability_and_full_jacobian": all(
            bool(partitions[str(seed)]["prob_exp_identity_pass"]) for seed in SEEDS  # type: ignore[index]
        ),
        "KEEP_grid_equality": all(bool(keep[str(seed)]["physics_sensor_plan_age_service_reward_equal"]) for seed in SEEDS),  # type: ignore[index]
        "switch_twin": all(bool(leakage[str(seed)]["complete"]) for seed in SEEDS),  # type: ignore[index]
        "IID_filtration_and_pairing": bool(
            iid_pairing["paired_across_arms"] and iid_pairing["terminal_censoring_exact"]
            and not iid_pairing["failures"]
        ),
        "IID_reward_decomposition": bool(iid_result["iid_reward_decomposition_conformant"]),
        "exposure_closed_form": bool(reward_ledger["exposure_closed_form_exact"]),  # type: ignore[index]
        "action_before_service": bool(reward_ledger["action_before_service_exact"]),  # type: ignore[index]
        "reward_service_cost_per_tick": bool(reward_ledger["reward_service_cost_tick_exact"]),  # type: ignore[index]
        "segment_ownership": bool(reward_ledger["segment_ownership_exact"]),  # type: ignore[index]
        "terminal_boundary_absence": bool(reward_ledger["terminal_boundary_absent"]),  # type: ignore[index]
        "safety": safety_violations == 0,
        "matched_actor_critic_parameters": parameters_matched,
        "matched_native_actor_calls": calls_matched,
        "matched_native_resource_work": native_resource_work_matched,
        "ONLGR_latency_at_most_1_10_RAW": latency_ratio <= 1.10,
        "mandatory_core_tick_accounting_exact": (
            int(resources["actual_team_ticks"]) == RECOVERY_INCREMENT_TICKS
        ),
        "frontier_evaluator_analyzer_source_identity_exact": (
            _source_identity() == source_identity
        ),
        "all_atomic_cell_commits_within_process_slice_limit": (
            float(resources[
                "maximum_slice_elapsed_seconds_at_cell_commit_conservative_upper_bound"
            ]) <= MAX_SLICE_SECONDS
        ),
        "recovery_RSS_strictly_below_1GiB": int(resources["peak_rss_bytes"]) < MAX_RSS_BYTES,
        "recovery_exactly_one_CPU_worker": int(resources["cpu_workers"]) == 1,
        "recovery_no_GPU_use": resources["gpu_used"] is False,
    }
    complete, technical_coherence, safety_resource_claim_gates = _completion_partition(
        missing, conformance,
    )
    technical_expected_polarity = {
        name: TECHNICAL_FACT_EXPECTED_POLARITY.get(name, True)
        for name in technical_coherence
    }
    technical_coherence_pass = all(
        value is technical_expected_polarity[name]
        for name, value in technical_coherence.items()
    )
    failed_present_claim_gates = [
        name for name, passed in safety_resource_claim_gates.items() if not passed
    ]
    link_gate = bool(
        iid_result["contrasts"]["ONLGR_minus_RAW-BOUNDARY-LEASE"]["gate"]  # type: ignore[index]
        and partition_analysis["operational_stability_gate"]
        and all(
            support[str(seed)][schedule]["ONLGR_full_poststartup_marked_activity"]  # type: ignore[index]
            for seed in SEEDS for schedule in (*HELDOUT_SCHEDULES, IID_SCHEDULE)
        )
    )
    first_attempt_charge = FIRST_ATTEMPT_NON_YOKE_TICKS + yoke_ticks
    cumulative = {
        "first_attempt_non_yoke_ticks": FIRST_ATTEMPT_NON_YOKE_TICKS,
        "first_attempt_yoke_ticks_Y": yoke_ticks,
        "Y_accounting_source": yoke_accounting["source"],
        "Y_is_conservative_maximum": first_attempt_non_outcome_ledger is None,
        "first_attempt_actual_charge": first_attempt_charge,
        "checkpoint_only_core_actual_charge": int(resources["actual_team_ticks"]),
        "cumulative_actual_charge": first_attempt_charge + int(resources["actual_team_ticks"]),
        "historical_fixed_cap": CUMULATIVE_HARD_MAX_TICKS,
        "historical_fixed_cap_execution_or_completeness_authority": False,
        "excess_over_registered_7m": first_attempt_charge + int(resources["actual_team_ticks"]) - 7_000_000,
        "maximum_excess_over_registered_7m": 2_863_168,
        "registered_7m_tick_cap_redefined": False,
        "registered_7m_tick_cap_pass": False,
        "historical_registered_fixed_resource_cap_pass": False,
        "within_resource_cap_claim_available": False,
        **_historical_non_gating_process_facts(resources),
    }
    result: dict[str, object] = {
        "artifact_kind": RECOVERY_ARTIFACT_KIND,
        "treatment": TREATMENT,
        "closed_scientific_object": COMPOSITE_REVISION,
        "recovery_identity": RECOVERY_IDENTITY,
        "historical_exact_once_marker_preserved_and_validated": True,
        "resumable_blinded_atomic_frontier_revision": FRONTIER_REVISION,
        "evaluator_analyzer_source_identity": source_identity,
        "panel_outcomes_inspected_before_recovery": False,
        "new_science_revision": False,
        "training_changed": False,
        "learned_parameters_changed": False,
        "estimands_arms_seeds_schedules_thresholds_changed": False,
        "checkpoint_validation": checkpoint_facts,
        "original_attempt": {
            "registration": registration,
            "scientific_activity": activity,
            "terminal": terminal,
            "resources_from_terminal": original_resources,
            "original_peak_RSS_recording": (
                "unavailable_not_padded"
                if original_resources["peak_rss_bytes"] == "unavailable"
                else "retained_non_outcome_terminal_fact"
            ),
            "retained_result_absent": True,
            "raw_result_absent": True,
            "matching_process_absent": True,
            "first_attempt_evaluation_rows_or_summaries_reused": False,
        },
        "analytic_initialization_exposure_curves": _analytic_initialization_curves(),
        "prob_exp_identity_conformance": identity,
        "native_seed_schedule_metrics": native,
        "iid_future_k_metrics": iid,
        "iid_future_k_analysis": iid_result,
        "iid_future_k_pairing_audit": iid_pairing,
        "safety_seed_schedule_metrics": safety,
        "fixed_rate_selection": fixed_selection,
        "fixed_rate_seed_schedule_metrics": fixed_evaluation,
        "keep_grid_equality": keep,
        "switch_decision_twin": leakage,
        "partition_probe": partitions,
        "partition_analysis": partition_analysis,
        "primary_analysis": primary,
        "mechanism_support": support,
        "matched_work_facts": {
            "actor_and_critic_parameters_matched": parameters_matched,
            "native_actor_calls_matched_for_each_schedule": calls_matched,
            "native_actor_critic_calls_messages_bits_physics_ticks_matched": native_resource_work_matched,
            "onlgr_to_raw_p95_actor_latency_ratio": latency_ratio,
            "latency_gate_at_most_1.10": latency_ratio <= 1.10,
            "declared_messages_per_team_tick": 2,
            "declared_bits_per_team_tick": 4,
        },
        "recovery_resource_diagnostics": resources,
        "cumulative_resource_accounting": cumulative,
        "result_return_conformance": {
            "map_revision": RESULT_MAP_REVISION,
            "facts": conformance,
            "mandatory_technical_data_coherence": technical_coherence,
            "mandatory_technical_data_expected_polarity": technical_expected_polarity,
            "mandatory_technical_data_coherence_pass": technical_coherence_pass,
            "present_safety_resource_claim_gates": safety_resource_claim_gates,
            "failed_present_claim_gates": failed_present_claim_gates,
            "all_safety_resource_claim_gates_pass": not failed_present_claim_gates,
            "core_missing_or_incoherent": missing,
            "complete_coherent_checkpoint_only_core_recovery": complete,
            "serialization_repair": "NaN_to_JSON_null_only",
            "nonlearned_policy_logits": {
                "available": False,
                "serialized_value": None,
                "reason": "not_applicable_to_nonlearned_policy",
            },
        },
        "omitted_or_unavailable_panels": {
            "closed_loop_exposure_clamp": {"available": False, "reason": "prospectively_omitted_recovery_panel"},
            "degenerate_controls": {"available": False, "reason": "prospectively_omitted_recovery_panel"},
            "current_state_oracle": {"available": False, "reason": "prospectively_omitted_recovery_panel"},
            "preselected_exact_yoke": {"available": False, "reason": "prospectively_omitted_recovery_panel"},
            "H_oracle": {"available": False, "value": None, "reason": "current_state_oracle_not_replayed"},
            "content_access_interpretation": {"available": False, "reason": "H_oracle_unavailable"},
            "continuous_two_UAV_second_surface": {"available": False, "reason": "registered_7m_cap_failed_and_H_oracle_unavailable"},
        },
        "activation_factual_inputs": {
            "P_plus_OR_W_plus": bool(
                primary["registered_primary_support"]["P"]  # type: ignore[index]
                or primary["registered_primary_support"]["W"]  # type: ignore[index]
            ),
            "IID_RAW_plus": bool(iid_result["contrasts"]["ONLGR_minus_RAW-BOUNDARY-LEASE"]["gate"]),  # type: ignore[index]
            "operational_marked_partition": bool(partition_analysis["operational_stability_gate"]),
            "eligible_exposure_link_composite_gate": link_gate,
            "IID_TIMING_plus": bool(iid_result["contrasts"]["ONLGR_minus_TIMING-ONLY-ONLGR"]["gate"]),  # type: ignore[index]
            "H_oracle_at_least_0_02": None,
            "content_access_composite_gate": None,
            "registered_7m_tick_cap_pass": False,
            "all_safety_resource_claim_gates_pass": not failed_present_claim_gates,
            "continuous_second_surface_activation_available": False,
        },
        "claim_ceiling": (
            "Recovered contrasts are named arm-matched finite-panel observations under a disclosed "
            "checkpoint-only engineering recovery. The original registered 7M cap permanently fails. "
            "No within-resource-cap or project-facing without-resource-failure claim, "
            "oracle/content-access interpretation, "
            "continuous two-UAV activation, clamp sensitivity, yoke sensitivity, arbitrary-k, "
            "variable-N, UAV-transfer, literal-hazard, lease-causal, or REBIND-causal claim is available."
        ),
        "post_result_same_conversation_Pro_convergence_required": complete,
        "environment": {
            "python": platform.python_version(), "torch": torch.__version__,
            "numpy": np.__version__, "platform": platform.platform(),
        },
        "material_anomalies": [],
        "atomic_result_commit": {
            "requested_slice_seconds": slice_seconds,
            "slice_elapsed_seconds_at_commit_conservative_upper_bound": slice_seconds,
        },
    }
    if not complete:
        raise RecoveryRefused(f"mandatory recovery core is incomplete or nonconformant: {missing or conformance}")
    _enforce_slice_deadline(slice_started, slice_seconds, "atomic result finalization")
    if _source_identity() != source_identity:
        raise RecoveryRefused("evaluator/analyzer source identity changed before finalization")
    _atomic_json(
        recovery_result_path, result,
        before_replace=lambda: _enforce_atomic_replace_window(slice_started, slice_seconds),
    )
    _enforce_slice_deadline(slice_started, slice_seconds, "the completed result commit")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Continue the authorized resumable ONLGR checkpoint-only core reevaluation",
    )
    parser.add_argument("action", choices=("checkpoint-only-core-reevaluate",))
    parser.add_argument("--original-output-root", required=True, type=Path)
    parser.add_argument("--original-result", required=True, type=Path)
    parser.add_argument("--original-terminal", required=True, type=Path)
    parser.add_argument("--recovery-output-root", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--first-attempt-non-outcome-ledger", type=Path)
    parser.add_argument(
        "--slice-seconds", type=float, default=MAX_SLICE_SECONDS,
        help=f"bounded resumable process slice, at most {MAX_SLICE_SECONDS} seconds",
    )
    args = parser.parse_args(argv)
    try:
        result = recover(
            original_output_root=args.original_output_root,
            original_result_path=args.original_result,
            original_terminal_path=args.original_terminal,
            recovery_output_root=args.recovery_output_root,
            recovery_result_path=args.result,
            first_attempt_non_outcome_ledger=args.first_attempt_non_outcome_ledger,
            slice_seconds=args.slice_seconds,
        )
    except RecoverySliceIncomplete:
        # Partial frontier values are intentionally never emitted on stdout.
        return 75
    print(json.dumps({
        "result": str(args.result.resolve()),
        "recovery_identity": result["recovery_identity"],
        "complete_coherent_checkpoint_only_core_recovery": result[
            "result_return_conformance"
        ]["complete_coherent_checkpoint_only_core_recovery"],
        "registered_7m_tick_cap_pass": False,
        "recovery_ticks": result["recovery_resource_diagnostics"]["actual_team_ticks"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
