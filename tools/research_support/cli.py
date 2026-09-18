"""Command line for the research support suite.

Two kinds of subcommand, kept apart on purpose:

* **Reading** commands (``inspect-run``, ``compare``, ``report``, ``replay``, ``export``,
  ``dataset-report``, ``scenario-report``, ``recommend-tests``, ``context-bundle``, and
  ``inspect-env`` without ``--probe``) import no agent class, load no checkpoint, construct
  no environment and start no process. Reading a file never creates an authorization to
  execute one.
* **Executing** commands (``demo``, ``record-eval``, ``inspect-env --probe``,
  ``scenario-report --execute``) print their execution scope, the controller or checkpoint
  identity, the source kind, the output ownership and the optimizer-update count before
  they do anything. The count is zero: nothing here trains.

Ordinary training is unaffected by every command in this file. The capture profile defaults
to ``off``, and an explicitly armed demonstration is a separate process with its own
environment instance.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any, Sequence

from .records import dumps

PROGRAM = "python -m tools.research_support"


# --------------------------------------------------------------------------------------
# Output ownership
# --------------------------------------------------------------------------------------


class CliError(RuntimeError):
    """A user-facing failure. Printed without a traceback, exits non-zero."""


def new_output_dir(path: str | os.PathLike[str], *, allow_existing_empty: bool = True) -> Path:
    """Create an output directory this invocation owns.

    A historical run directory is never overwritten by default: an existing non-empty
    target is refused, and the caller is told to choose a new one.
    """

    target = Path(path)
    if target.exists():
        if not target.is_dir():
            raise CliError(f"output path exists and is not a directory: {target}")
        if any(target.iterdir()) and not allow_existing_empty:
            raise CliError(f"output directory is not empty: {target}")
        if any(target.iterdir()):
            raise CliError(
                f"refusing to write into the non-empty directory {target}; choose a new "
                "output directory so no existing artifact is overwritten"
            )
    target.mkdir(parents=True, exist_ok=True)
    return target


def announce_execution(
    *,
    what: str,
    route: str,
    source_kind: str,
    policy_identity: str,
    output: Path | None,
    optimizer_updates: int = 0,
    extra: Sequence[str] = (),
) -> None:
    """Print the scope of an executing command before it runs anything."""

    lines = [
        "",
        f"  EXECUTION SCOPE: {what}",
        f"    route               : {route}",
        f"    source kind         : {source_kind}",
        f"    policy / controller : {policy_identity}",
        f"    output owned here   : {output if output is not None else 'none (display only)'}",
        f"    optimizer updates   : {optimizer_updates}",
        "    formal training fits: 0",
    ]
    lines.extend(f"    {line}" for line in extra)
    lines.append("")
    print("\n".join(lines), file=sys.stderr)


# --------------------------------------------------------------------------------------
# demo
# --------------------------------------------------------------------------------------


def _build_capture(args: argparse.Namespace, *, record: bool):
    from .capture.profiles import (
        AlwaysActiveLease,
        CaptureConfig,
        CaptureGate,
        PreviewConfig,
        Profile,
        RecordEvalConfig,
    )
    from .capture.transport import LatestFrameFileSink, MappedViewerLease, NullSink

    preview = PreviewConfig(
        lane_ids=(int(args.lane),),
        min_completed_env_steps_between_frames=int(args.min_steps_between_frames),
        min_wall_interval_s=float(args.min_wall_interval),
        max_session_wall_s=float(args.max_session_wall_s),
        require_active_viewer=bool(args.live and not args.no_wait_viewer),
        record_trace=bool(args.trace_output),
        max_frame_bytes=int(args.max_frame_bytes),
        max_output_bytes_per_wall_s=int(args.max_output_bytes_per_wall_s),
    )
    profile = Profile.RECORD_EVAL if record else Profile.LIVE_PREVIEW
    config = CaptureConfig(
        profile=profile,
        preview=preview,
        record_eval=RecordEvalConfig(
            capture_every_decision=True,
            capture_substeps=bool(getattr(args, "capture_substeps", False)),
        ),
    )

    stream_dir = None
    sink: Any = NullSink()
    lease: Any = AlwaysActiveLease()
    if args.live:
        stream_dir = new_output_dir(args.stream_output or _default_stream_dir())
        sink = LatestFrameFileSink(stream_dir)
        if preview.require_active_viewer:
            lease = MappedViewerLease.in_directory(stream_dir, create=True)
    gate = CaptureGate(config, lease=lease)
    return config, gate, sink, stream_dir


def _default_stream_dir() -> Path:
    return Path("temp") / "research_support" / f"stream-{int(time.time())}"


def _trace_writer(args: argparse.Namespace, *, manifest: dict[str, Any]):
    if not args.trace_output:
        return None, None
    from .capture.trace_store import TraceWriter

    directory = new_output_dir(args.trace_output)
    writer = TraceWriter(
        directory,
        trace_id=manifest["trace_id"],
        manifest=manifest,
        chunk_frames=int(args.chunk_frames),
        max_bytes=int(args.max_trace_bytes),
    )
    return writer, directory


def cmd_demo(args: argparse.Namespace) -> int:
    if args.route == "service-restoration":
        return _demo_service_restoration(args)
    if args.route == "legacy-mobile-relay":
        return _demo_legacy(args)
    raise CliError(f"unknown route {args.route!r}")


def _demo_service_restoration(args: argparse.Namespace) -> int:
    from envs.uav_service_restoration.baselines import CONTROLLER_NAMES, build_controller
    from envs.uav_service_restoration.config import load_config
    from envs.uav_service_restoration.env import UAVServiceRestorationEnv

    from .capture.service_restoration import ServiceRestorationObserver
    from .records import PolicyKind, SourceKind, StreamState

    if not args.config:
        raise CliError("--config is required for the service-restoration route")
    args.controller = args.controller or "backhaul_aware_greedy"
    if args.controller not in CONTROLLER_NAMES:
        raise CliError(
            f"unknown controller {args.controller!r}; available: {', '.join(CONTROLLER_NAMES)}"
        )
    config = load_config(args.config)
    trace_id = f"sr-{args.controller}-{args.seed}-{int(time.time())}"
    manifest = {
        "trace_id": trace_id,
        "route": "service-restoration",
        "environment_id": config.environment_id,
        "preset_name": config.preset_name,
        "config_path": str(Path(args.config).resolve()),
        "controller": args.controller,
        "controller_kind": "untuned_diagnostic_rule",
        "seed": int(args.seed),
        "source_kind": SourceKind.RULE_CONTROLLER_ROLLOUT.value,
        "optimizer_updates": 0,
        "is_real_activity_data": None,
    }
    writer, trace_dir = _trace_writer(args, manifest=manifest)
    capture, gate, sink, stream_dir = _build_capture(args, record=bool(args.trace_output))

    announce_execution(
        what="forward-only rule-controller rollout of the service-restoration environment",
        route="service-restoration",
        source_kind="rule_controller_rollout",
        policy_identity=f"{args.controller} (untuned diagnostic rule, no learned parameter)",
        output=trace_dir or stream_dir,
        extra=[
            f"config              : {Path(args.config).resolve()}",
            f"episodes            : {args.episodes}",
            f"capture profile     : {capture.profile.value}",
            f"stream directory    : {stream_dir or 'none'}",
        ],
    )

    observer = ServiceRestorationObserver(
        gate=gate,
        sink=sink,
        run_id=f"demo-{args.controller}",
        trace_id=trace_id,
        policy_kind=PolicyKind.RULE_CONTROLLER,
        source_kind=SourceKind.RULE_CONTROLLER_ROLLOUT,
        policy_label=args.controller,
        trace_writer=writer,
        capture_substeps=bool(getattr(args, "capture_substeps", False)),
    )
    env = UAVServiceRestorationEnv(config)
    env.set_capture_observer(observer)
    controller = build_controller(args.controller, config, seed=int(args.seed))

    server = _maybe_serve(args, stream_dir, title=f"service restoration - {args.controller}")
    try:
        records = []
        for episode in range(int(args.episodes)):
            controller.reset()
            env.reset(seed=int(args.seed) + episode)
            while env.agents:
                view = env.get_current_state()
                env.step(controller.act(view, list(env.agents)))
            records.append(env.episode_summary())
            print(
                f"episode {episode}: {observer.emitted} frames emitted, "
                f"{gate.counters.attempts - gate.counters.admitted} attempts refused by gates",
                file=sys.stderr,
            )
        observer.finish(state=StreamState.ENDED)
        if writer is not None:
            index = writer.close()
            print(f"trace written: {trace_dir} ({index.n_frames} frames, status {index.status})")
        if stream_dir is not None:
            print(f"stream directory: {stream_dir}")
        _print_gate_summary(gate, observer)
        if server is not None:
            _hold_server(server, args)
    finally:
        env.set_capture_observer(None)
        env.close()
        if server is not None:
            server.stop()
    return 0


def _demo_legacy(args: argparse.Namespace) -> int:
    from ha_ctse_process.config import Config
    from ha_ctse_process.env_factory import EnvSpec, make_env

    from .capture.legacy_uav import LegacyCaptureWrapper, LegacyRelayObserver
    from .controllers import build_legacy_controller
    from .records import PolicyKind, SourceKind, StreamState

    demo_config: dict[str, Any] = {}
    if args.config:
        demo_config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        if demo_config.get("route") not in (None, "legacy-mobile-relay"):
            raise CliError(
                f"{args.config} declares route {demo_config.get('route')!r}, not "
                "legacy-mobile-relay"
            )
    overrides = demo_config.get("config_overrides", {})
    scenario = demo_config.get("scenario", "base")
    controller_spec = demo_config.get("controller", {})
    controller_name = args.controller or controller_spec.get("name", "legacy_cluster_coverage")

    config = Config()
    for key, value in overrides.items():
        if not hasattr(config, key):
            raise CliError(
                f"{args.config}: config override {key!r} is not a field of the process-core "
                "Config; refusing to invent one"
            )
        setattr(config, key, value)

    trace_id = f"legacy-{controller_name}-{args.seed}-{int(time.time())}"
    manifest = {
        "trace_id": trace_id,
        "route": "legacy-mobile-relay",
        "scenario": scenario,
        "environment_class": "envs.pettingzoo.relay.forced_relay.UAVForcedRelayEnv",
        "note": (
            "scenario alias 'base' constructs UAVForcedRelayEnv, not routed_core; confirmed "
            "in ha_ctse_process/env_factory.py"
        ),
        "config_overrides": overrides,
        "controller": controller_name,
        "controller_kind": "untuned_diagnostic_rule",
        "seed": int(args.seed),
        "source_kind": SourceKind.RULE_CONTROLLER_ROLLOUT.value,
        "optimizer_updates": 0,
        "known_limitations": demo_config.get("known_limitations", []),
    }
    writer, trace_dir = _trace_writer(args, manifest=manifest)
    capture, gate, sink, stream_dir = _build_capture(args, record=bool(args.trace_output))

    announce_execution(
        what="forward-only rule-controller rollout of the mobile legacy relay environment",
        route="legacy-mobile-relay",
        source_kind="rule_controller_rollout",
        policy_identity=f"{controller_name} (untuned diagnostic rule, no learned parameter)",
        output=trace_dir or stream_dir,
        extra=[
            f"scenario            : {scenario} -> UAVForcedRelayEnv",
            f"config overrides    : {overrides or 'none'}",
            f"episodes            : {args.episodes}",
            f"capture profile     : {capture.profile.value}",
            f"stream directory    : {stream_dir or 'none'}",
        ],
    )

    observer = LegacyRelayObserver(
        gate=gate,
        sink=sink,
        run_id=f"demo-{controller_name}",
        trace_id=trace_id,
        scenario=scenario,
        policy_kind=PolicyKind.RULE_CONTROLLER,
        source_kind=SourceKind.RULE_CONTROLLER_ROLLOUT,
        policy_label=controller_name,
        trace_writer=writer,
    )
    adapter = make_env(config, EnvSpec(scenario=scenario, seed=int(args.seed), rank=0))()
    env = LegacyCaptureWrapper(adapter, observer)
    controller = build_legacy_controller(controller_name, **(controller_spec.get("options") or {}))

    server = _maybe_serve(args, stream_dir, title=f"mobile legacy relay - {controller_name}")
    try:
        for episode in range(int(args.episodes)):
            controller.reset()
            _obs, info = env.reset(seed=int(args.seed) + episode)
            state_info = (info or {}).get("state_info") or {}
            steps = 0
            max_steps = int(args.max_steps or getattr(config, "episode_length", 150))
            while steps < max_steps:
                action = controller.act(
                    state_info, n_uavs=adapter.n_uavs, action_dim=adapter.action_dim
                )
                _obs, _reward, terminated, truncated, info = env.step(action)
                state_info = (info or {}).get("state_info") or {}
                steps += 1
                if bool(terminated) or bool(truncated):
                    break
            print(
                f"episode {episode}: {steps} steps, {observer.emitted} frames emitted",
                file=sys.stderr,
            )
        observer.finish(state=StreamState.ENDED)
        if writer is not None:
            index = writer.close()
            print(f"trace written: {trace_dir} ({index.n_frames} frames, status {index.status})")
        if stream_dir is not None:
            print(f"stream directory: {stream_dir}")
        _print_gate_summary(gate, observer)
        if server is not None:
            _hold_server(server, args)
    finally:
        env.close()
        if server is not None:
            server.stop()
    return 0


def _print_gate_summary(gate: Any, observer: Any) -> None:
    counters = gate.counters.to_json()
    print("capture gate summary (attempts = admitted + every refusal):")
    for name, value in counters.items():
        print(f"  {name:28s} {value}")
    print(f"  frames emitted               {observer.emitted}")


def _maybe_serve(args: argparse.Namespace, stream_dir: Path | None, *, title: str):
    if not args.live or stream_dir is None:
        return None
    from .viewer.server import ViewerConfig, ViewerServer

    server = ViewerServer(
        ViewerConfig(
            stream_dir=stream_dir,
            host=args.host,
            port=int(args.port),
            title=title,
            banner=(
                "SYNTHETIC ENGINEERING DEMONSTRATION - a rule controller on a configured "
                "scenario. Not an algorithm result."
            ),
        )
    ).start()
    print(f"viewer: {server.url}", file=sys.stderr)
    if args.open_browser:
        webbrowser.open(server.url)
    return server


def _hold_server(server: Any, args: argparse.Namespace) -> None:
    hold = float(args.hold_seconds)
    if hold <= 0:
        return
    print(
        f"holding the viewer open for {hold:.0f}s at {server.url} "
        "(the simulation has already finished; this only keeps the page readable)",
        file=sys.stderr,
    )
    try:
        time.sleep(hold)
    except KeyboardInterrupt:
        pass


# --------------------------------------------------------------------------------------
# serve / replay
# --------------------------------------------------------------------------------------


def _parse_labelled(values: Sequence[str] | None, *, what: str) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for index, item in enumerate(values or ()):
        if "=" in item:
            label, _, path = item.partition("=")
        else:
            label, path = f"{what}{index}", item
        resolved = Path(path).resolve()
        if not resolved.is_dir():
            raise CliError(f"{what} directory does not exist: {resolved}")
        out[label] = resolved
    return out


def cmd_serve(args: argparse.Namespace) -> int:
    from .viewer.server import ViewerConfig, ViewerServer

    stream = Path(args.stream).resolve() if args.stream else None
    if stream is not None and not stream.is_dir():
        raise CliError(f"stream directory does not exist: {stream}")
    traces = _parse_labelled(args.trace, what="trace")
    reports = _parse_labelled(args.report, what="report")
    if stream is None and not traces and not reports:
        raise CliError(
            "nothing to serve: pass --stream, --trace and/or --report. This command never "
            "runs a simulator and cannot attach to an uninstrumented process."
        )
    server = ViewerServer(
        ViewerConfig(
            stream_dir=stream,
            traces=traces,
            reports=reports,
            host=args.host,
            port=int(args.port),
            title=args.title,
            banner=args.banner,
        )
    ).start()
    print(f"viewer: {server.url}")
    print("this is a local read-only diagnostic service; it exposes no endpoint that can")
    print("start, stop, reset or step anything. Ctrl-C to stop.")
    if args.open_browser:
        webbrowser.open(server.url)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nstopping the viewer only; nothing else was started by it")
    finally:
        server.stop()
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    from .viewer.server import ViewerConfig, ViewerServer

    traces: dict[str, Path] = {}
    if args.trace:
        traces["trace"] = Path(args.trace).resolve()
    if args.left:
        traces["left"] = Path(args.left).resolve()
    if args.right:
        traces["right"] = Path(args.right).resolve()
    if not traces:
        raise CliError("pass --trace, or --left and --right for a paired comparison")
    for label, path in traces.items():
        if not path.is_dir():
            raise CliError(f"{label} trace directory does not exist: {path}")

    from .capture.trace_store import TraceReader

    for label, path in traces.items():
        result = TraceReader(path).read(limit=1)
        print(f"{label}: {result.trace_id} status={result.status} frames={result.index.n_frames}")
        for problem in result.problems[:5]:
            print(f"  problem: {problem}")
    server = ViewerServer(
        ViewerConfig(
            traces=traces,
            host=args.host,
            port=int(args.port),
            title="replay",
            banner=(
                "RECORDED TRACE - replaying data that was actually recorded. Sparse capture "
                "cannot reconstruct unrecorded actions or topology changes."
            ),
        )
    ).start()
    print(f"viewer: {server.url}")
    if args.open_browser:
        webbrowser.open(server.url)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nstopping the viewer")
    finally:
        server.stop()
    return 0


# --------------------------------------------------------------------------------------
# inspect-env
# --------------------------------------------------------------------------------------


def cmd_inspect_env(args: argparse.Namespace) -> int:
    from .inspect_env import inspect_env, write_env_report

    report = inspect_env(route=args.route, config_path=args.config, probe=bool(args.probe))
    text = dumps(report.to_json(), indent=2)
    if args.output:
        directory = new_output_dir(args.output)
        (directory / "env_report.json").write_text(text, encoding="utf-8")
        write_env_report(report, directory)
        print(f"written: {directory}")
    else:
        print(text)
    return 0


# --------------------------------------------------------------------------------------
# delegating subcommands
# --------------------------------------------------------------------------------------


def _lazy(module: str, attribute: str) -> Any:
    import importlib

    try:
        loaded = importlib.import_module(f".{module}", package=__package__)
    except ImportError as error:
        raise CliError(
            f"the {module} module is not available in this checkout: {error}"
        ) from error
    try:
        return getattr(loaded, attribute)
    except AttributeError as error:
        raise CliError(f"{module}.{attribute} is not implemented") from error


def cmd_inspect_run(args: argparse.Namespace) -> int:
    inspect_run = _lazy("inspect_run", "inspect_run")
    write_run_report = _lazy("inspect_run", "write_run_report")
    report = inspect_run(Path(args.run), reader=args.reader)
    if args.output:
        path = write_run_report(report, new_output_dir(args.output))
        print(f"written: {path}")
    else:
        print(dumps(report.to_json(), indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    ComparisonSpec = _lazy("compare", "ComparisonSpec")
    compare_runs = _lazy("compare", "compare_runs")
    write_comparison_report = _lazy("compare", "write_comparison_report")
    spec = ComparisonSpec.from_file(Path(args.spec))
    report = compare_runs(spec)
    if args.output:
        path = write_comparison_report(report, new_output_dir(args.output))
        print(f"written: {path}")
    else:
        print(dumps(report.to_json(), indent=2))
    if not report.pooling_permitted:
        print(
            "pooling refused: the runs do not share the identities a pooled summary needs",
            file=sys.stderr,
        )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    ReportRequest = _lazy("reports", "ReportRequest")
    build_report = _lazy("reports", "build_report")
    inputs_from_traces = _lazy("report_inputs", "inputs_from_traces")

    spec: dict[str, Any] = {}
    if args.spec:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        if not isinstance(spec, dict):
            raise CliError(f"report spec must be a JSON object: {args.spec}")

    # A trace is read into records here rather than being passed on as a path string: no
    # chart reads a path, so the earlier form produced a report of nothing but holes.
    trace_paths: list[str] = []
    if args.trace:
        trace_paths.append(str(Path(args.trace).resolve()))
    for extra in spec.pop("trace_paths", ()) or ():
        resolved = str(Path(extra).resolve())
        if resolved not in trace_paths:
            trace_paths.append(resolved)

    inputs: dict[str, Any] = {}
    if trace_paths:
        for path in trace_paths:
            if not Path(path).is_dir():
                raise CliError(f"trace directory not found: {path}")
        inputs = inputs_from_traces(trace_paths)
    # The operator's declared spec is authoritative: a key given explicitly wins over the
    # one derived from the trace.
    overridden = sorted(key for key in spec if key in inputs)
    inputs.update(spec)

    output = new_output_dir(args.output)
    result = build_report(
        ReportRequest(
            output_dir=output,
            inputs=inputs,
            charts=tuple(args.charts_list or ()),
            title=args.title,
            provenance_label=args.provenance_label,
        )
    )

    for provenance in inputs.get("trace_provenance", ()) or ():
        print(
            f"trace: {provenance.get('trace_id')} status={provenance.get('status')} "
            f"frames={provenance.get('n_frames')} method={provenance.get('method_id')} "
            f"world={provenance.get('world_id')}"
        )
        if not provenance.get("complete"):
            print("  NOT A COMPLETE RECORDING: panels are drawn from a partial episode")
    if trace_paths:
        derived = list(inputs.get("derived_inputs") or ())
        print(f"inputs derived from {len(trace_paths)} trace(s): " + (", ".join(derived) or "none"))
        for key, reason in sorted((inputs.get("absent_inputs") or {}).items()):
            print(f"  absent: {key}: {reason}")
        for note in inputs.get("notes") or ():
            print(f"  note: {note}")
    if overridden:
        print("declared in --spec, overriding the derived value: " + ", ".join(overridden))

    print(f"report: {result.index_path}")
    if result.missing_panels:
        print("panels with no recorded input (named, not substituted):")
        for panel in result.missing_panels:
            print(f"  {panel}")
    return 0


def cmd_recommend_tests(args: argparse.Namespace) -> int:
    recommend_tests = _lazy("recommend_tests", "recommend_tests")
    report = recommend_tests(Path(args.repo), base=args.base, head=args.head)
    print(dumps(report.to_json(), indent=2))
    return 0


def cmd_context_bundle(args: argparse.Namespace) -> int:
    ContextBundleSpec = _lazy("context_bundle", "ContextBundleSpec")
    write_context_bundle = _lazy("context_bundle", "write_context_bundle")
    spec = ContextBundleSpec(
        repo=Path(args.repo),
        base=args.base,
        head=args.head,
        request_scope=args.scope or "",
        test_result_paths=tuple(Path(p) for p in (args.test_result or ())),
    )
    path = write_context_bundle(spec, new_output_dir(args.output))
    print(f"written: {path}")
    print("the bundle is generated locally; nothing sends it anywhere")
    return 0


def cmd_dataset_report(args: argparse.Namespace) -> int:
    dataset_report = _lazy("dataset_report", "dataset_report")
    path = dataset_report(Path(args.dataset), new_output_dir(args.output))
    print(f"written: {path}")
    return 0


def cmd_scenario_report(args: argparse.Namespace) -> int:
    scenario_report = _lazy("scenario_report", "scenario_report")
    path = scenario_report(
        config_path=Path(args.config),
        dataset=Path(args.dataset) if args.dataset else None,
        episodes_file=Path(args.episodes_file) if args.episodes_file else None,
        output_dir=new_output_dir(args.output),
        execute=bool(args.execute),
    )
    print(f"written: {path}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    export_trace = _lazy("export", "export_trace")
    ExportError = _lazy("export", "ExportError")
    try:
        path = export_trace(
            trace_dir=Path(args.trace),
            output=Path(args.output),
            fmt=args.format,
            fps=float(args.fps),
        )
    except ExportError as error:
        # A missing optional encoder is an ordinary, actionable outcome, not a crash.
        raise CliError(str(error)) from error
    print(f"written: {path}")
    return 0


def cmd_efficiency_check(args: argparse.Namespace) -> int:
    measure = _lazy("efficiency", "measure")
    format_report = _lazy("efficiency", "format_report")
    write_report = _lazy("efficiency", "write_report")

    announce_execution(
        what="timing of the capture seams under each declared condition",
        route="service-restoration",
        source_kind="rule_controller_rollout",
        policy_identity="backhaul_aware_greedy (untuned diagnostic rule, no learned parameter)",
        output=Path(args.output) if args.output else None,
        extra=[
            f"config              : {Path(args.config).resolve()}",
            f"steps per repeat    : {args.steps}",
            f"repeats             : {args.repeats}",
            "measures the display path only; starts no training and loads no checkpoint",
        ],
    )
    report = measure(
        Path(args.config), steps=int(args.steps), repeats=int(args.repeats), seed=int(args.seed)
    )
    print(format_report(report))
    if args.output:
        print(f"written: {write_report(report, new_output_dir(args.output))}")
    return 0


def cmd_record_eval(args: argparse.Namespace) -> int:
    record_eval = _lazy("record_eval", "record_eval")
    return int(record_eval(args))


# --------------------------------------------------------------------------------------
# parser
# --------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=(
            "Research support and UAV/UE visualization suite. Reading commands never import "
            "an agent, load a checkpoint or start a process; executing commands print their "
            "scope first and perform zero optimizer updates."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_capture_options(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--lane", type=int, default=0, help="the one lane that is captured")
        sub.add_argument(
            "--min-steps-between-frames",
            type=int,
            default=1,
            help=(
                "completed environment steps between capture attempts. The demonstration "
                "default is 1 because a demo exists to be watched; instrumented training "
                "uses 100 (configs/research_support/viewer_default.json)"
            ),
        )
        sub.add_argument("--min-wall-interval", type=float, default=0.0)
        sub.add_argument("--max-session-wall-s", type=float, default=3600.0)
        sub.add_argument("--max-frame-bytes", type=int, default=4_000_000)
        sub.add_argument("--max-output-bytes-per-wall-s", type=int, default=64_000_000)
        sub.add_argument("--chunk-frames", type=int, default=64)
        sub.add_argument("--max-trace-bytes", type=int, default=256 * 1024 * 1024)
        sub.add_argument(
            "--no-wait-viewer",
            action="store_true",
            help="capture without waiting for a browser (the session's bounds are explicit)",
        )

    def add_server_options(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--host", default="127.0.0.1", help="loopback only")
        sub.add_argument("--port", type=int, default=0, help="0 asks the OS for a free port")
        sub.add_argument("--open-browser", action="store_true")

    # demo -----------------------------------------------------------------------------
    demo = subparsers.add_parser(
        "demo",
        help="explicit bounded forward-only demonstration; ordinary training stays profile=off",
    )
    demo.add_argument("--route", required=True, choices=["service-restoration", "legacy-mobile-relay"])
    demo.add_argument("--config", help="environment config, or a legacy demo config JSON")
    demo.add_argument(
        "--controller",
        default=None,
        help=(
            "route-specific controller name. Defaults per route: "
            "backhaul_aware_greedy (service-restoration), "
            "legacy_cluster_coverage (legacy-mobile-relay)"
        ),
    )
    demo.add_argument("--seed", type=int, default=17)
    demo.add_argument("--episodes", type=int, default=1)
    demo.add_argument("--max-steps", type=int, default=0, help="legacy route step cap")
    demo.add_argument("--trace-output", help="new directory for a recorded trace")
    demo.add_argument("--stream-output", help="new directory for the live stream files")
    demo.add_argument("--live", action="store_true", help="serve a local viewer while running")
    demo.add_argument(
        "--capture-substeps",
        action="store_true",
        help=(
            "retain the LAST substep of each admitted decision interval instead of the "
            "first; still one frame per interval, at the cost of a conversion per substep"
        ),
    )
    demo.add_argument("--hold-seconds", type=float, default=0.0,
                      help="keep the viewer readable after the rollout finishes")
    add_capture_options(demo)
    add_server_options(demo)
    demo.set_defaults(func=cmd_demo)

    # serve ----------------------------------------------------------------------------
    serve = subparsers.add_parser(
        "serve", help="observe an already instrumented stream; this command runs no simulator"
    )
    serve.add_argument("--stream", help="directory holding latest.json from a producer")
    serve.add_argument("--trace", action="append", help="label=path, repeatable")
    serve.add_argument("--report", action="append", help="label=path, repeatable")
    serve.add_argument("--title", default="HMASD research support viewer")
    serve.add_argument("--banner", default="")
    add_server_options(serve)
    serve.set_defaults(func=cmd_serve)

    # replay ---------------------------------------------------------------------------
    replay = subparsers.add_parser("replay", help="replay recorded data, not a checkpoint")
    replay.add_argument("--trace")
    replay.add_argument("--left")
    replay.add_argument("--right")
    replay.add_argument("--view", default="2d", choices=["2d", "3d"])
    replay.add_argument("--alignment", default="simulated-time",
                        choices=["simulated-time", "event"])
    add_server_options(replay)
    replay.set_defaults(func=cmd_replay)

    # inspect-env ----------------------------------------------------------------------
    inspect_env_p = subparsers.add_parser(
        "inspect-env", help="explain a route's effective configuration; --probe constructs it"
    )
    inspect_env_p.add_argument("--route", required=True)
    inspect_env_p.add_argument("--config")
    inspect_env_p.add_argument("--probe", action="store_true",
                               help="explicitly construct the environment in a child process")
    inspect_env_p.add_argument("--output")
    inspect_env_p.set_defaults(func=cmd_inspect_env)

    # inspect-run ----------------------------------------------------------------------
    inspect_run_p = subparsers.add_parser(
        "inspect-run", help="read-only inventory of a known run; no agent import, no checkpoint"
    )
    inspect_run_p.add_argument("--run", required=True)
    inspect_run_p.add_argument("--reader", help="force a specific reader instead of detecting")
    inspect_run_p.add_argument("--output")
    inspect_run_p.set_defaults(func=cmd_inspect_run)

    # compare --------------------------------------------------------------------------
    compare_p = subparsers.add_parser(
        "compare", help="compare declared groups without automatically running them"
    )
    compare_p.add_argument("--spec", required=True)
    compare_p.add_argument("--output")
    compare_p.set_defaults(func=cmd_compare)

    # report ---------------------------------------------------------------------------
    report_p = subparsers.add_parser("report", help="figures and report from existing evidence")
    report_p.add_argument("--spec")
    report_p.add_argument("--trace")
    report_p.add_argument("--charts", dest="charts_list", nargs="*", default=None)
    report_p.add_argument("--title", default="Algorithm capability report")
    report_p.add_argument("--provenance-label", default="")
    report_p.add_argument("--output", required=True)
    report_p.set_defaults(func=cmd_report)

    # record-eval ----------------------------------------------------------------------
    record = subparsers.add_parser(
        "record-eval",
        help="explicit trusted-checkpoint evaluation recording; no loader-family fallback",
    )
    record.add_argument("--route", required=True)
    record.add_argument("--checkpoint", required=True)
    record.add_argument("--config", required=True)
    record.add_argument("--episodes-file", required=True)
    record.add_argument("--trace-output", required=True)
    record.add_argument("--seed", type=int, default=17)
    add_capture_options(record)
    record.set_defaults(func=cmd_record_eval)

    # efficiency-check -------------------------------------------------------------------
    eff = subparsers.add_parser(
        "efficiency-check",
        help="measure what the capture seams cost; starts no training and loads no checkpoint",
    )
    eff.add_argument("--config", required=True)
    eff.add_argument("--steps", type=int, default=40)
    eff.add_argument("--repeats", type=int, default=3)
    eff.add_argument("--seed", type=int, default=17)
    eff.add_argument("--output")
    eff.set_defaults(func=cmd_efficiency_check)

    # export ---------------------------------------------------------------------------
    export_p = subparsers.add_parser("export", help="export a recorded trace")
    export_p.add_argument("--trace", required=True)
    export_p.add_argument("--format", required=True, choices=["html", "png", "gif", "mp4", "json"])
    export_p.add_argument("--output", required=True)
    export_p.add_argument("--fps", type=float, default=8.0)
    export_p.set_defaults(func=cmd_export)

    # dataset-report / scenario-report --------------------------------------------------
    dataset_p = subparsers.add_parser("dataset-report", help="read-only prepared-dataset report")
    dataset_p.add_argument("--dataset", required=True)
    dataset_p.add_argument("--output", required=True)
    dataset_p.set_defaults(func=cmd_dataset_report)

    scenario_p = subparsers.add_parser("scenario-report", help="scenario diagnostics; static by default")
    scenario_p.add_argument("--config", required=True)
    scenario_p.add_argument("--dataset")
    scenario_p.add_argument("--episodes-file")
    scenario_p.add_argument("--output", required=True)
    scenario_p.add_argument("--execute", action="store_true",
                            help="run the declared non-learning diagnostic set")
    scenario_p.set_defaults(func=cmd_scenario_report)

    # recommend-tests / context-bundle ---------------------------------------------------
    tests_p = subparsers.add_parser("recommend-tests", help="change-aware test recommendation")
    tests_p.add_argument("--base", required=True)
    tests_p.add_argument("--head", default="HEAD")
    tests_p.add_argument("--repo", default=".")
    tests_p.set_defaults(func=cmd_recommend_tests)

    bundle_p = subparsers.add_parser("context-bundle", help="English context bundle, generated locally")
    bundle_p.add_argument("--base", required=True)
    bundle_p.add_argument("--head", default="HEAD")
    bundle_p.add_argument("--repo", default=".")
    bundle_p.add_argument("--scope")
    bundle_p.add_argument("--test-result", action="append")
    bundle_p.add_argument("--output", required=True)
    bundle_p.set_defaults(func=cmd_context_bundle)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return int(args.func(args) or 0)
    except CliError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
