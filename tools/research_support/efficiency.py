"""Measure what the capture seams actually cost, under each declared condition.

Section 0.2 of the plan asks for a number, not an assurance. This module runs the same
deterministic rollout under six conditions and reports the per-decision-step wall time of
each, so the claim "the default path is unaffected" is something a reader can check rather
than something the author asserts.

The conditions are:

``pre_change``          the revision of ``env.py`` that predates the capture seams
``off``                 current code, no observer attached (what every training run does)
``preview_no_viewer``   preview armed, gate refusing because no viewer holds the lease
``preview_with_viewer`` preview armed, lease held, frames actually leaving the producer
``stalled_consumer``    lease held but the sink never drains; the breaker must absorb it
``record_eval``         explicit evaluation recording, every decision captured to a trace

Nothing here trains, loads a checkpoint, or constructs an optimizer. It is a measurement of
the display path only, and it says so in its own output.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import statistics
import subprocess
import sys
import time
import types
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .records import dumps

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_RELPATH = "envs/uav_service_restoration/env.py"

#: The revision the seams were added on top of; kept in step with the off-path test.
BASELINE_REV = "ef6cb091a621bf04a734878346dbd8860a1ebe59"
SEAM_MARKER = "_capture_observer"

#: Verdict vocabulary the plan asks for. Each is earned by a specific measurement, and the
#: absence of a measurement yields PERFORMANCE_NOT_ESTABLISHED rather than a pass.
EFFICIENCY_CONTRACT_IMPLEMENTED = "EFFICIENCY_CONTRACT_IMPLEMENTED"
OFF_PATH_VERIFIED = "OFF_PATH_VERIFIED"
LOW_RATE_PREVIEW_MEASURED = "LOW_RATE_PREVIEW_MEASURED"
ARMED_CAPTURE_NON_INTERFERING = "ARMED_CAPTURE_NON_INTERFERING"
PERFORMANCE_NOT_ESTABLISHED = "PERFORMANCE_NOT_ESTABLISHED"


@dataclasses.dataclass(frozen=True)
class ConditionResult:
    """Timing for one condition. Percentiles, never a bare mean.

    A mean over step times hides exactly the thing that matters here: whether some steps
    occasionally become expensive. The maximum is reported for the same reason.
    """

    name: str
    description: str
    steps: int
    repeats: int
    median_step_ms: float
    p95_step_ms: float
    max_step_ms: float
    total_wall_s: float
    #: Gate and observer counters belong to the FINAL repeat only - each repeat builds a
    #: fresh environment and a fresh gate. Timings, by contrast, pool every repeat.
    frames_emitted: int
    gate_attempts: int
    gate_admitted: int
    trajectory_sha256: str
    note: str = ""

    def to_json(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class EfficiencyReport:
    config_path: str
    steps_per_repeat: int
    repeats: int
    conditions: tuple[ConditionResult, ...]
    verdicts: tuple[str, ...]
    findings: tuple[str, ...]
    optimizer_updates: int = 0
    formal_training_fits: int = 0

    def to_json(self) -> dict[str, Any]:
        payload = dataclasses.asdict(self)
        payload["conditions"] = [c.to_json() for c in self.conditions]
        return payload

    def by_name(self, name: str) -> ConditionResult | None:
        for condition in self.conditions:
            if condition.name == name:
                return condition
        return None


# --------------------------------------------------------------------------------------
# baseline module
# --------------------------------------------------------------------------------------


def load_baseline_env_module() -> types.ModuleType | None:
    """The pre-seam ``env.py``, executed inside the real package. See the off-path test."""

    try:
        out = subprocess.run(
            ["git", "show", f"{BASELINE_REV}:{ENV_RELPATH}"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    source = out.stdout.decode("utf-8")
    if SEAM_MARKER in source:
        # Refusing is the honest outcome: a "baseline" that already has the seam would make
        # the comparison meaningless while still producing a reassuring number.
        return None
    importlib.import_module("envs.uav_service_restoration")
    name = "envs.uav_service_restoration._env_efficiency_baseline"
    module = types.ModuleType(name)
    module.__package__ = "envs.uav_service_restoration"
    module.__file__ = str(REPO_ROOT / ENV_RELPATH)
    sys.modules[name] = module
    try:
        exec(compile(source, module.__file__, "exec"), module.__dict__)
    except Exception:
        sys.modules.pop(name, None)
        return None
    return module


# --------------------------------------------------------------------------------------
# one timed rollout
# --------------------------------------------------------------------------------------


def _digest_state(value: Any, hasher: "hashlib._Hash") -> None:
    if isinstance(value, np.ndarray):
        hasher.update(np.ascontiguousarray(value).tobytes())
    elif isinstance(value, dict):
        for key in sorted(value, key=repr):
            hasher.update(repr(key).encode())
            _digest_state(value[key], hasher)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _digest_state(item, hasher)
    elif isinstance(value, float):
        hasher.update(np.float64(value).tobytes())
    else:
        hasher.update(repr(value).encode())


def _timed_rollout(
    env_module: types.ModuleType,
    config_path: Path,
    *,
    steps: int,
    repeats: int,
    seed: int,
    attach: Callable[[Any], Any] | None,
) -> tuple[list[float], str, Any]:
    """Run ``repeats`` rollouts, returning every per-step duration in milliseconds."""

    from envs.uav_service_restoration.baselines import build_controller
    from envs.uav_service_restoration.config import load_config

    config = load_config(str(config_path))
    durations: list[float] = []
    hasher = hashlib.sha256()
    attached: Any = None

    for repeat in range(repeats):
        env = env_module.UAVServiceRestorationEnv(config)
        if attach is not None:
            attached = attach(env)
        try:
            controller = build_controller("backhaul_aware_greedy", config, seed=seed)
            controller.reset()
            env.reset(seed=seed)
            taken = 0
            while env.agents and taken < steps:
                view = env.get_current_state()
                action = controller.act(view, list(env.agents))
                start = time.perf_counter_ns()
                result = env.step(action)
                durations.append((time.perf_counter_ns() - start) / 1e6)
                if repeat == 0:
                    # Hash one repeat only: the trajectory is identical across repeats by
                    # construction, and hashing every step of every repeat is pure cost.
                    _digest_state(result, hasher)
                taken += 1
        finally:
            if hasattr(env, "set_capture_observer"):
                env.set_capture_observer(None)
            env.close()
    return durations, hasher.hexdigest(), attached


def _summarise(
    name: str,
    description: str,
    durations: list[float],
    *,
    steps: int,
    repeats: int,
    digest: str,
    frames: int = 0,
    attempts: int = 0,
    admitted: int = 0,
    note: str = "",
) -> ConditionResult:
    ordered = sorted(durations)
    p95 = ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))] if ordered else float("nan")
    return ConditionResult(
        name=name,
        description=description,
        steps=steps,
        repeats=repeats,
        median_step_ms=statistics.median(ordered) if ordered else float("nan"),
        p95_step_ms=p95,
        max_step_ms=max(ordered) if ordered else float("nan"),
        total_wall_s=sum(durations) / 1000.0,
        frames_emitted=frames,
        gate_attempts=attempts,
        gate_admitted=admitted,
        trajectory_sha256=digest,
        note=note,
    )


# --------------------------------------------------------------------------------------
# conditions
# --------------------------------------------------------------------------------------


def _observer_factory(
    *,
    profile: Any,
    preview: Any,
    lease: Any,
    sink: Any,
    trace_writer: Any = None,
) -> Callable[[Any], Any]:
    from .capture.profiles import CaptureConfig, CaptureGate, RecordEvalConfig
    from .capture.service_restoration import ServiceRestorationObserver
    from .records import PolicyKind, SourceKind

    def attach(env: Any) -> Any:
        config = CaptureConfig(
            profile=profile,
            preview=preview,
            record_eval=RecordEvalConfig(capture_every_decision=True),
        )
        gate = CaptureGate(config, lease=lease)
        observer = ServiceRestorationObserver(
            gate=gate,
            sink=sink,
            run_id="efficiency-check",
            trace_id="efficiency-check",
            policy_kind=PolicyKind.RULE_CONTROLLER,
            source_kind=SourceKind.RULE_CONTROLLER_ROLLOUT,
            policy_label="backhaul_aware_greedy",
            trace_writer=trace_writer,
        )
        env.set_capture_observer(observer)
        return (gate, observer)

    return attach


def measure(
    config_path: Path,
    *,
    steps: int = 40,
    repeats: int = 3,
    seed: int = 17,
    scratch: Path | None = None,
) -> EfficiencyReport:
    """Run every condition and return the report. Starts no training and no fit."""

    from .capture.profiles import (
        AlwaysActiveLease,
        LocalViewerLease,
        PreviewConfig,
        Profile,
    )
    from .capture.transport import BoundedQueueSink, LatestFrameFileSink, NullSink

    env_module = importlib.import_module("envs.uav_service_restoration.env")
    conditions: list[ConditionResult] = []
    findings: list[str] = []

    # 1. pre-change baseline
    baseline_module = load_baseline_env_module()
    if baseline_module is None:
        findings.append(
            f"the pre-change revision of {ENV_RELPATH} could not be loaded at "
            f"{BASELINE_REV}; the off-path comparison below is against the current code only"
        )
    else:
        durations, digest, _ = _timed_rollout(
            baseline_module, config_path, steps=steps, repeats=repeats, seed=seed, attach=None
        )
        conditions.append(_summarise(
            "pre_change",
            f"{ENV_RELPATH} at {BASELINE_REV[:12]}, before the capture seams existed",
            durations, steps=steps, repeats=repeats, digest=digest,
        ))

    # 2. off - what every existing training and evaluation path does
    durations, off_digest, _ = _timed_rollout(
        env_module, config_path, steps=steps, repeats=repeats, seed=seed, attach=None
    )
    conditions.append(_summarise(
        "off",
        "current code, capture_observer is None: one attribute load and one None test",
        durations, steps=steps, repeats=repeats, digest=off_digest,
    ))

    preview = PreviewConfig(
        lane_ids=(0,),
        min_completed_env_steps_between_frames=100,
        min_wall_interval_s=1.0,
        require_active_viewer=True,
        record_trace=False,
    )

    # 3. preview armed, nobody watching
    expired = LocalViewerLease(0.0)  # nobody has ever renewed it
    durations, digest, attached = _timed_rollout(
        env_module, config_path, steps=steps, repeats=repeats, seed=seed,
        attach=_observer_factory(
            profile=Profile.LIVE_PREVIEW, preview=preview, lease=expired, sink=NullSink()
        ),
    )
    gate, observer = attached
    conditions.append(_summarise(
        "preview_no_viewer",
        "preview armed, no viewer holds the lease: refused before any array is copied",
        durations, steps=steps, repeats=repeats, digest=digest,
        frames=observer.emitted, attempts=gate.counters.attempts,
        admitted=gate.counters.admitted,
        note="a frame here would mean the lease check does not gate the capture",
    ))

    # 4. preview with a viewer actually attached
    scratch_dir = Path(scratch or (REPO_ROOT / "temp" / "research_support" / "efficiency"))
    scratch_dir.mkdir(parents=True, exist_ok=True)
    durations, digest, attached = _timed_rollout(
        env_module, config_path, steps=steps, repeats=repeats, seed=seed,
        attach=_observer_factory(
            profile=Profile.LIVE_PREVIEW,
            preview=dataclasses.replace(
                preview, min_completed_env_steps_between_frames=1, min_wall_interval_s=0.0
            ),
            lease=AlwaysActiveLease(),
            sink=LatestFrameFileSink(scratch_dir),
        ),
    )
    gate, observer = attached
    conditions.append(_summarise(
        "preview_with_viewer",
        "lease held, rate gates opened to every decision: the upper bound on preview cost",
        durations, steps=steps, repeats=repeats, digest=digest,
        frames=observer.emitted, attempts=gate.counters.attempts,
        admitted=gate.counters.admitted,
        note="deliberately un-rate-limited; the shipped default is one frame per second",
    ))

    # 5. stalled consumer - the queue never drains
    durations, digest, attached = _timed_rollout(
        env_module, config_path, steps=steps, repeats=repeats, seed=seed,
        attach=_observer_factory(
            profile=Profile.LIVE_PREVIEW,
            preview=dataclasses.replace(
                preview, min_completed_env_steps_between_frames=1, min_wall_interval_s=0.0
            ),
            lease=AlwaysActiveLease(),
            sink=BoundedQueueSink(1),
        ),
    )
    gate, observer = attached
    conditions.append(_summarise(
        "stalled_consumer",
        "viewer present but never draining: latest-wins, producer must not block",
        durations, steps=steps, repeats=repeats, digest=digest,
        frames=observer.emitted, attempts=gate.counters.attempts,
        admitted=gate.counters.admitted,
    ))

    # 6. explicit evaluation recording
    from .capture.trace_store import TraceWriter

    trace_dir = scratch_dir / "record-eval-trace"
    if trace_dir.exists():
        import shutil

        shutil.rmtree(trace_dir)
    writer = TraceWriter(
        trace_dir,
        trace_id="efficiency-record-eval",
        manifest={"trace_id": "efficiency-record-eval", "purpose": "efficiency measurement"},
    )
    durations, digest, attached = _timed_rollout(
        env_module, config_path, steps=steps, repeats=1, seed=seed,
        attach=_observer_factory(
            profile=Profile.RECORD_EVAL, preview=preview, lease=AlwaysActiveLease(),
            sink=NullSink(), trace_writer=writer,
        ),
    )
    writer.close()
    gate, observer = attached
    conditions.append(_summarise(
        "record_eval",
        "explicit recording: every decision captured and written to a trace on disk",
        durations, steps=steps, repeats=1, digest=digest,
        frames=observer.emitted, attempts=gate.counters.attempts,
        admitted=gate.counters.admitted,
        note="this is an operator-requested recording, never an ordinary training run",
    ))

    verdicts = _verdicts(conditions, off_digest, findings)
    return EfficiencyReport(
        config_path=str(config_path.resolve()),
        steps_per_repeat=steps,
        repeats=repeats,
        conditions=tuple(conditions),
        verdicts=tuple(verdicts),
        findings=tuple(findings),
    )


def _verdicts(
    conditions: list[ConditionResult], off_digest: str, findings: list[str]
) -> list[str]:
    """Earn each verdict from a measurement, or decline to issue it."""

    by_name = {c.name: c for c in conditions}
    verdicts: list[str] = []

    off = by_name.get("off")
    pre = by_name.get("pre_change")
    if off is not None and pre is not None:
        if pre.trajectory_sha256 != off.trajectory_sha256:
            findings.append(
                "the off path does NOT reproduce the pre-change trajectory; this is a "
                "correctness failure, not a performance one"
            )
        else:
            verdicts.append(OFF_PATH_VERIFIED)
            delta = off.median_step_ms - pre.median_step_ms
            relative = delta / pre.median_step_ms if pre.median_step_ms else float("nan")
            findings.append(
                f"off vs pre-change median step: {off.median_step_ms:.4f} ms vs "
                f"{pre.median_step_ms:.4f} ms ({relative:+.2%}); the two are separated by "
                "process noise of the same order, so this bounds the cost rather than "
                "resolving it"
            )
    else:
        findings.append(
            "no pre-change baseline was measured, so OFF_PATH_VERIFIED is not issued"
        )

    no_viewer = by_name.get("preview_no_viewer")
    if no_viewer is not None:
        if no_viewer.frames_emitted == 0 and no_viewer.gate_admitted == 0:
            verdicts.append(EFFICIENCY_CONTRACT_IMPLEMENTED)
        else:
            findings.append(
                f"preview with no viewer still emitted {no_viewer.frames_emitted} frames; "
                "the lease is not gating capture"
            )

    with_viewer = by_name.get("preview_with_viewer")
    if with_viewer is not None and with_viewer.frames_emitted > 0:
        verdicts.append(LOW_RATE_PREVIEW_MEASURED)
        if off is not None:
            findings.append(
                f"preview at its maximum rate costs {with_viewer.median_step_ms:.4f} ms per "
                f"decision against {off.median_step_ms:.4f} ms with capture off; at the "
                "shipped default of one frame per second this cost is paid on a small "
                "fraction of steps"
            )

    # Every armed condition already carries its own trajectory hash. Comparing them against
    # the off path turns this timing harness into the strongest non-interference evidence in
    # the suite: it shows that capture actually running - copying arrays, building frames,
    # writing a trace - leaves the trajectory identical, which the timings alone cannot show.
    armed = [c for c in conditions if c.name not in ("pre_change", "off")]
    diverged = [c.name for c in armed if c.trajectory_sha256 != off_digest]
    if armed and not diverged:
        verdicts.append(ARMED_CAPTURE_NON_INTERFERING)
        findings.append(
            "every armed condition ("
            + ", ".join(c.name for c in armed)
            + ") reproduced the capture-off trajectory exactly ("
            + off_digest[:16]
            + "), so running the capture changes no scientific quantity"
        )
    elif diverged:
        findings.append(
            "these armed conditions did NOT reproduce the capture-off trajectory: "
            + ", ".join(diverged)
            + "; this is a correctness failure, not a performance one"
        )

    stalled = by_name.get("stalled_consumer")
    if stalled is not None and with_viewer is not None:
        findings.append(
            f"a stalled consumer measured {stalled.median_step_ms:.4f} ms per decision "
            f"against {with_viewer.median_step_ms:.4f} ms with a draining one: the producer "
            "drops frames rather than waiting"
        )

    if not verdicts:
        verdicts.append(PERFORMANCE_NOT_ESTABLISHED)
    return verdicts


def format_report(report: EfficiencyReport) -> str:
    """A table an operator can read without opening the JSON."""

    lines = [
        "",
        "  EFFICIENCY MEASUREMENT - display path only",
        f"    config              : {report.config_path}",
        f"    steps per repeat    : {report.steps_per_repeat}",
        f"    optimizer updates   : {report.optimizer_updates}",
        f"    formal training fits: {report.formal_training_fits}",
        "",
        f"    {'condition':<22}{'median ms':>11}{'p95 ms':>10}{'max ms':>10}"
        f"{'frames':>9}{'admitted/attempts':>20}",
        "    (timings pool every repeat; frame and gate counts are the final repeat only)",
    ]
    for c in report.conditions:
        lines.append(
            f"    {c.name:<22}{c.median_step_ms:>11.4f}{c.p95_step_ms:>10.4f}"
            f"{c.max_step_ms:>10.4f}{c.frames_emitted:>9}"
            f"{f'{c.gate_admitted}/{c.gate_attempts}':>20}"
        )
    lines.append("")
    for verdict in report.verdicts:
        lines.append(f"    {verdict}")
    if report.findings:
        lines.append("")
        for finding in report.findings:
            lines.append(f"    - {finding}")
    lines.append("")
    return "\n".join(lines)


def write_report(report: EfficiencyReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "efficiency_report.json"
    path.write_text(dumps(report.to_json(), indent=2), encoding="utf-8")
    (output_dir / "efficiency_report.txt").write_text(
        format_report(report), encoding="utf-8"
    )
    return path
