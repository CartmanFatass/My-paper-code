"""Record one trusted checkpoint's forward-only evaluation as a trace.

``record-eval`` is the only command in this suite that may execute a trained policy, and only
because the operator named an explicit checkpoint on the command line. What it refuses is the
point of the module:

* **One declared loader per route** (:data:`ROUTE_CHECKPOINT_FAMILY`). A payload the loader
  does not describe is reported with the keys it actually carries and the invocation stops.
  No second loader family, fixture, synthetic rollout, random policy or neighbouring
  checkpoint ever stands in for a declared artifact that is missing or unreadable.
* **Validate first, execute second**, so a missing input costs nothing and is named exactly.
* **Zero optimizer updates**: this module constructs no optimizer and calls no optimizer
  step; the rollout runs under ``torch.no_grad()`` with every loaded module in eval mode. The
  declared agent constructor allocates its own Adam state, which the manifest records rather
  than hides - no update is ever applied to it.
* **One evaluation, not N replicates**: many episodes of one checkpoint are one evaluation,
  and the manifest says so, so a reader cannot count episodes as independent evidence.

Identity the payload does not carry is recorded as absent with a validity reason, never as
``0``. ``torch`` is imported inside the functions that need it, so ``--help`` stays fast and
this module imports in a torch-free context.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .cli import CliError, _build_capture, _print_gate_summary, _trace_writer, announce_execution
from .records import Measured, PolicyKind, SourceKind, StreamState, Validity, file_hash


@dataclass(frozen=True)
class CheckpointFamily:
    """The single checkpoint family a route accepts, and how its payload is recognised.

    ``required_keys`` are the top-level keys the declared loader dereferences plus the
    ``algorithm`` fingerprint its writer stamps. They are checked as plain dictionary
    membership before any module is built, so a wrong-family file is refused by name rather
    than by an opaque shape error inside ``load_state_dict``.
    """

    family_id: str
    loader: str
    builder: str
    evidence: str
    algorithm: str
    required_keys: tuple[str, ...]


#: Written by ``ha_ctse_process.checkpoint_io.checkpoint_payload`` (from ``save_checkpoint``
#: / ``save_training_checkpoint`` in ``standalone_train_runner.py``) and read back for
#: evaluation by ``load_checkpoint(..., load_optimizers=False)``, which its own code calls
#: "evaluation/warm-start only". ``ha_ctse_process/eval_checkpoints.py``
#: ``build_agent_for_checkpoint`` is the existing construct-then-load sequence reused here.
PROCESS_CORE_FAMILY = CheckpointFamily(
    family_id="ha_ctse_process_standalone",
    loader="ha_ctse_process.checkpoint_io.load_checkpoint(load_optimizers=False)",
    builder="ha_ctse_process.standalone_cli.create_agent",
    evidence=(
        "ha_ctse_process/checkpoint_io.py:checkpoint_payload/load_checkpoint; "
        "ha_ctse_process/eval_checkpoints.py:build_agent_for_checkpoint"
    ),
    algorithm="ha_ctse_process_standalone",
    required_keys=(
        "algorithm", "checkpoint_schema_version", "high", "low", "process",
        "config_name", "n_agents", "skill_interval",
    ),
)

#: Both routes this suite constructs are process-core routes: the legacy relay route is
#: ``ha_ctse_process.env_factory`` scenario ``base``, and the service-restoration package
#: names ``standalone_train_runner.py`` as its trainer integration
#: (``envs/uav_service_restoration/README.md``, "Trainer integration"). Each route still
#: declares the family explicitly, so a route with a different learner cannot inherit this.
ROUTE_CHECKPOINT_FAMILY: dict[str, CheckpointFamily] = {
    "service-restoration": PROCESS_CORE_FAMILY,
    "legacy-mobile-relay": PROCESS_CORE_FAMILY,
}

SUPPORTED_ROUTES = tuple(ROUTE_CHECKPOINT_FAMILY)

#: Identity fields, by alias order. A name no alias supplies is recorded absent, not zero.
_IDENTITY_ALIASES: dict[str, tuple[str, ...]] = {
    "global_step": ("global_step", "total_steps"),
    "update_index": ("update_idx",),
    "episode": ("episode", "episode_idx", "episodes_completed"),
    "version": ("checkpoint_schema_version", "version"),
    "algorithm": ("algorithm",),
    "skill_interval": ("skill_interval",),
    "config_name": ("config_name",),
}

_MAX_REPORTED_KEYS = 24


@dataclass(frozen=True)
class EpisodeSpec:
    """One declared evaluation episode. The file, not this module, chooses the seeds."""

    episode_id: str
    seed: int
    max_steps: int | None = None
    config_overrides: Mapping[str, Any] = field(default_factory=dict)
    #: ``declared`` when the file named the episode, ``derived_from_seed`` when the file
    #: used the bare seed-list form the rest of this CLI reads.
    episode_id_source: str = "declared"

    def to_json(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "episode_id_source": self.episode_id_source,
            "seed": int(self.seed),
            "max_steps": None if self.max_steps is None else int(self.max_steps),
            "config_overrides": dict(self.config_overrides),
        }


@dataclass(frozen=True)
class CheckpointIdentity:
    """Everything this invocation knows about the artifact it is about to execute."""

    path: Path
    sha256: str
    size_bytes: int
    mtime_utc: str
    fields: Mapping[str, Measured]

    @property
    def label(self) -> str:
        return f"{self.path.name} {self.sha256}"

    def to_json(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "sha256": self.sha256,
            "size_bytes": int(self.size_bytes),
            "mtime_utc": self.mtime_utc,
            "identity_fields": {k: v.to_json() for k, v in self.fields.items()},
        }


def _require_file(value: Any, *, what: str, flag: str) -> Path:
    if not value:
        raise CliError(f"{flag} is required for record-eval; it names the {what}")
    path = Path(str(value)).expanduser()
    resolved = (path if path.is_absolute() else Path.cwd() / path).resolve()
    if not resolved.exists():
        raise CliError(
            f"{what} does not exist: {resolved} (from {flag} {value!r}); record-eval "
            "substitutes nothing for a declared artifact"
        )
    if not resolved.is_file():
        raise CliError(f"{what} is not a file: {resolved}")
    return resolved


def load_episode_specs(path: Path) -> tuple[EpisodeSpec, ...]:
    """Parse the declared episodes.

    Two forms, because ``--episodes-file`` already means something in this CLI. The rich
    form is a JSON list of episode objects, ``{"episodes": [...]}``, or JSONL. The bare
    form is the seed list that ``scenario-report`` and
    ``scripts/uav_service_restoration/evaluate_baselines.py`` read (a list of integers, or
    ``{"episode_seeds": [...]}`` / ``{"seeds": [...]}``), so the same held-out episode list
    can be replayed here. A bare seed gets a label derived from itself, marked as derived
    rather than presented as an identity the file declared.
    """

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise CliError(f"episodes file is empty: {path}; it must declare at least one episode")
    entries: Any
    if path.suffix.lower() == ".jsonl":
        entries = []
        for number, line in enumerate(text.splitlines(), start=1):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise CliError(f"{path} line {number} is not valid JSON: {error}") from error
    else:
        try:
            entries = json.loads(text)
        except json.JSONDecodeError as error:
            raise CliError(f"{path} is not valid JSON: {error}") from error
        if isinstance(entries, Mapping):
            bare = entries.get("episodes", entries.get("episode_seeds", entries.get("seeds")))
            if bare is None:
                raise CliError(
                    f"{path} is a JSON object without an 'episodes', 'episode_seeds' or "
                    "'seeds' key; declare a list of episode specifications, or use a JSON "
                    "list or a JSONL file"
                )
            entries = bare
        if not isinstance(entries, list):
            raise CliError(f"{path} must hold a list of episode specifications or seeds")

    specs: list[EpisodeSpec] = []
    for index, entry in enumerate(entries):
        if isinstance(entry, int) and not isinstance(entry, bool):
            specs.append(
                EpisodeSpec(
                    episode_id=f"seed-{entry}", seed=int(entry),
                    episode_id_source="derived_from_seed",
                )
            )
            continue
        if not isinstance(entry, Mapping):
            raise CliError(f"{path} entry {index} is not an object or an integer seed: {entry!r}")
        episode_id = entry.get("episode_id", entry.get("id"))
        if episode_id is None:
            raise CliError(f"{path} entry {index} has no 'episode_id'")
        if entry.get("seed") is None:
            raise CliError(
                f"{path} entry {index} ({episode_id}) has no 'seed'; record-eval invents no "
                "seed, because an unrecorded seed is an unreproducible episode"
            )
        overrides = entry.get("config_overrides") or {}
        if not isinstance(overrides, Mapping):
            raise CliError(f"{path} entry {index} has a non-object 'config_overrides'")
        max_steps = entry.get("max_steps")
        specs.append(EpisodeSpec(
            episode_id=str(episode_id),
            seed=int(entry["seed"]),
            max_steps=None if max_steps is None else int(max_steps),
            config_overrides=dict(overrides),
        ))
    if not specs:
        raise CliError(f"{path} declares no episodes; record-eval has nothing to evaluate")
    # One invocation builds one environment for the whole session, so a per-episode config
    # override would be recorded and never applied. Refusing is the only honest option:
    # recording an override that did nothing would misdescribe the evaluated condition.
    overriding = [spec.episode_id for spec in specs if spec.config_overrides]
    if overriding:
        raise CliError(
            f"{path} declares per-episode config_overrides for {', '.join(overriding[:5])}"
            f"{' ...' if len(overriding) > 5 else ''}; record-eval builds one environment "
            "for the whole session and would not apply them. Run one record-eval per "
            "configuration instead, so each trace names the configuration it ran."
        )
    return tuple(specs)


def load_payload(path: Path, family: CheckpointFamily) -> Mapping[str, Any]:
    """Read the checkpoint with the one loader the route declares."""

    import torch

    try:
        # The repo's own loaders read these project-owned artifacts with weights_only=False
        # (ha_ctse_process/checkpoint_io.py:load_checkpoint_metadata) because the payload
        # carries a Config object and NumPy RNG state.
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as error:  # noqa: BLE001 - reported, never retried with another loader
        raise CliError(
            f"{path} could not be read by this route's declared loader ({family.loader}): "
            f"{type(error).__name__}: {error}. No other loader family is tried."
        ) from error
    if not isinstance(payload, Mapping):
        raise CliError(
            f"{path} holds a {type(payload).__name__}, not the mapping the declared loader "
            f"{family.loader} expects. No other loader family is tried."
        )
    return payload


def require_family(payload: Mapping[str, Any], family: CheckpointFamily, path: Path) -> None:
    """Refuse a payload the declared loader does not describe, naming what was found."""

    missing = [key for key in family.required_keys if key not in payload]
    algorithm = payload.get("algorithm")
    if not missing and algorithm == family.algorithm:
        return
    found = sorted(str(key) for key in payload)
    shown = ", ".join(found[:_MAX_REPORTED_KEYS])
    if len(found) > _MAX_REPORTED_KEYS:
        shown += f", ... ({len(found)} keys total)"
    raise CliError(
        f"{path} does not match the loader declared for this route. "
        f"declared loader: {family.loader}; expected family: {family.family_id} "
        f"(algorithm={family.algorithm!r}); algorithm found: {algorithm!r}; "
        f"missing keys: {', '.join(missing) if missing else 'none'}; "
        f"keys found: {shown}. record-eval declares one loader per route and tries no "
        "second loader family, no fixture and no substitute policy."
    )


def checkpoint_identity(path: Path, payload: Mapping[str, Any]) -> CheckpointIdentity:
    """Hash and describe the artifact, recording absent identity as absent."""

    stat = path.stat()
    fields: dict[str, Measured] = {}
    for name, aliases in _IDENTITY_ALIASES.items():
        present = [alias for alias in aliases if alias in payload]
        if not present:
            fields[name] = Measured.absent(
                Validity.NOT_RECORDED, f"absent_in_checkpoint_payload:{'/'.join(aliases)}"
            )
        elif payload[present[0]] is None:
            fields[name] = Measured.absent(
                Validity.MISSING_ARTIFACT, f"recorded_as_null:{present[0]}"
            )
        elif isinstance(payload[present[0]], (bool, int, float, str)):
            fields[name] = Measured.ok(payload[present[0]], source=present[0])
        else:
            fields[name] = Measured.absent(
                Validity.INVALID,
                f"not_scalar:{present[0]}:{type(payload[present[0]]).__name__}",
            )
    return CheckpointIdentity(
        path=path,
        sha256=file_hash(str(path)),
        size_bytes=int(stat.st_size),
        mtime_utc=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        fields=fields,
    )


def policy_kind_for(identity: CheckpointIdentity) -> PolicyKind:
    """Claim "trained" only where the payload records a positive step count."""

    step = identity.fields.get("global_step")
    if step is None or not step.validity.is_value:
        return PolicyKind.UNKNOWN
    try:
        positive = float(step.value) > 0.0  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return PolicyKind.UNKNOWN
    return PolicyKind.TRAINED_CHECKPOINT if positive else PolicyKind.UNTRAINED_CHECKPOINT


@dataclass
class RouteRuntime:
    env: Any
    observer: Any
    close: Callable[[], None]


@dataclass
class RouteSetup:
    """Route facts known before the trace exists, plus the runtime factory."""

    environment_id: str
    manifest_extra: dict[str, Any]
    build: Callable[..., RouteRuntime]


def _observer_kwargs(
    *, gate: Any, sink: Any, writer: Any, trace_id: str,
    identity: CheckpointIdentity, policy_kind: PolicyKind,
) -> dict[str, Any]:
    """Provenance both route observers need: this checkpoint, forward-only."""

    return {
        "gate": gate,
        "sink": sink,
        "run_id": f"record-eval-{identity.path.stem}",
        "trace_id": trace_id,
        "policy_kind": policy_kind,
        "source_kind": SourceKind.CHECKPOINT_EVALUATION,
        "policy_label": identity.label,
        "checkpoint_identity": identity.label,
        "trace_writer": writer,
    }


def _setup_service_restoration(config_path: Path) -> RouteSetup:
    from envs.uav_service_restoration.config import load_config

    config = load_config(str(config_path))

    def build(*, seed: int, **provenance: Any) -> RouteRuntime:
        from envs.uav_service_restoration.adapter import make_array_env

        from .capture.service_restoration import ServiceRestorationObserver

        observer = ServiceRestorationObserver(**_observer_kwargs(**provenance))
        env = make_array_env(config, seed=int(seed))
        env.env.set_capture_observer(observer)

        def close() -> None:
            env.env.set_capture_observer(None)
            env.close()

        return RouteRuntime(env=env, observer=observer, close=close)

    return RouteSetup(
        environment_id=config.environment_id,
        manifest_extra={"preset_name": config.preset_name},
        build=build,
    )


def _setup_legacy_mobile_relay(config_path: Path) -> RouteSetup:
    from ha_ctse_process.config import Config

    document = json.loads(config_path.read_text(encoding="utf-8"))
    if document.get("route") not in (None, "legacy-mobile-relay"):
        raise CliError(
            f"{config_path} declares route {document.get('route')!r}, not legacy-mobile-relay"
        )
    overrides = document.get("config_overrides", {})
    scenario = document.get("scenario", "base")
    config = Config()
    for key, value in overrides.items():
        if not hasattr(config, key):
            raise CliError(
                f"{config_path}: config override {key!r} is not a field of the process-core "
                "Config; refusing to invent one"
            )
        setattr(config, key, value)

    def build(*, seed: int, **provenance: Any) -> RouteRuntime:
        from ha_ctse_process.env_factory import EnvSpec, make_env

        from .capture.legacy_uav import LegacyCaptureWrapper, LegacyRelayObserver

        observer = LegacyRelayObserver(scenario=scenario, **_observer_kwargs(**provenance))
        adapter = make_env(config, EnvSpec(scenario=scenario, seed=int(seed), rank=0))()
        env = LegacyCaptureWrapper(adapter, observer)
        return RouteRuntime(env=env, observer=observer, close=env.close)

    return RouteSetup(
        environment_id="uav_forced_relay_env_v0",
        manifest_extra={"scenario": scenario, "config_overrides": dict(overrides)},
        build=build,
    )


ROUTE_SETUPS: dict[str, Callable[[Path], RouteSetup]] = {
    "service-restoration": _setup_service_restoration,
    "legacy-mobile-relay": _setup_legacy_mobile_relay,
}


class ProcessCorePolicy:
    """Forward-only driver for a process-core checkpoint.

    The call sequence is the repo's own evaluation sequence
    (``ha_ctse_process/standalone_evaluation.py``): skill check, low-level action, step
    bookkeeping. Nothing here re-derives a decision rule and nothing here updates.
    """

    def __init__(self, agent: Any, *, skill_interval: int, label: str) -> None:
        self._agent = agent
        self._k = int(skill_interval)
        self.label = label

    def modules(self) -> list[Any]:
        import torch

        return [v for v in vars(self._agent).values() if isinstance(v, torch.nn.Module)]

    def reset(self) -> None:
        self._agent.reset_env_state(0)

    def act(self, observations: Any, *, state: Any, step: int) -> Any:
        self._agent.maybe_assign_skills(
            observations, state=state, step=int(step), k=self._k, env_id=0, deterministic=True
        )
        actions, _logp, _values = self._agent.act_low(
            observations, env_id=0, deterministic=True, state=state
        )
        return actions

    def note_step(self, *, reward: Any, observations: Any, state: Any, done: bool) -> None:
        self._agent.record_environment_step(
            0, reward=float(reward), next_obs=observations, next_state=state, done=bool(done)
        )


def _build_process_core_policy(
    *, payload: Mapping[str, Any], checkpoint_path: Path, env: Any, device: str
) -> ProcessCorePolicy:
    from ha_ctse_process.checkpoint_io import apply_checkpoint_structure, load_checkpoint
    from ha_ctse_process.standalone_cli import create_agent, load_config

    checkpoint_agents = int(payload["n_agents"])
    env_agents = int(getattr(env, "n_uavs", 0))
    if checkpoint_agents != env_agents:
        raise CliError(
            f"{checkpoint_path} records n_agents={checkpoint_agents} but this route's "
            f"environment has {env_agents} UAVs; record-eval does not reshape a checkpoint"
        )
    # The architecture comes from the checkpoint's own recorded config module and metadata,
    # so what executes is what the artifact declares. A checkpoint whose architecture came
    # from unrecorded command-line overrides is refused by strict state-dict loading rather
    # than approximated.
    args = argparse.Namespace(
        device=device, n_agents=checkpoint_agents, high_controller="", event_architecture_mode=""
    )
    try:
        config = load_config(str(payload["config_name"]), str(payload.get("preset") or "") or None)
        if payload.get("scenario"):
            config.scenario = str(payload["scenario"])
        apply_checkpoint_structure(config, args, dict(payload))
        agent = create_agent(config, args, env, num_envs=1, state_dim=int(env.state_dim))
        load_checkpoint(checkpoint_path, agent, load_optimizers=False)
    except CliError:
        raise
    except Exception as error:  # noqa: BLE001 - reported, never retried with another family
        raise CliError(
            f"this route's declared loader failed on {checkpoint_path}: "
            f"{type(error).__name__}: {error}. record-eval stops here rather than trying a "
            "second loader family or a substitute policy."
        ) from error
    return ProcessCorePolicy(
        agent, skill_interval=int(payload["skill_interval"]), label=checkpoint_path.name
    )


POLICY_BUILDERS: dict[str, Callable[..., Any]] = {
    "service-restoration": _build_process_core_policy,
    "legacy-mobile-relay": _build_process_core_policy,
}


def build_manifest(
    *, trace_id: str, route: str, family: CheckpointFamily, setup: RouteSetup,
    identity: CheckpointIdentity, policy_kind: PolicyKind, config_path: Path,
    episodes_path: Path, episodes: tuple[EpisodeSpec, ...], seed: int, device: str,
) -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "route": route,
        "environment_id": setup.environment_id,
        "config_path": str(config_path),
        "episodes_file": str(episodes_path),
        "seed": int(seed),
        "device": device,
        "source_kind": SourceKind.CHECKPOINT_EVALUATION.value,
        "policy_kind": policy_kind.value,
        "optimizer_updates": 0,
        "formal_training_fits": 0,
        "optimizer_objects_constructed_here": 0,
        "optimizer_note": (
            "the declared agent constructor allocates its own Adam state; record-eval "
            "constructs no optimizer and applies no update to it"
        ),
        "checkpoint": identity.to_json(),
        "checkpoint_loader": {
            "family_id": family.family_id,
            "loader": family.loader,
            "builder": family.builder,
            "evidence": family.evidence,
            "fallback_families_tried": 0,
        },
        "episodes": [spec.to_json() for spec in episodes],
        "n_selected_episodes": len(episodes),
        "statistical_unit": "one checkpoint evaluation",
        "independent_replicates": 1,
        "replicate_note": (
            "every episode here shares one checkpoint from one training fit; more episodes "
            "sharpen this checkpoint's estimate and add no independent replicate"
        ),
        "is_real_activity_data": None,
        **setup.manifest_extra,
    }


def record_eval(args: argparse.Namespace) -> int:
    route = str(args.route)
    family = ROUTE_CHECKPOINT_FAMILY.get(route)
    if family is None:
        raise CliError(
            f"unknown route {route!r}; record-eval supports: {', '.join(SUPPORTED_ROUTES)}"
        )
    checkpoint_path = _require_file(args.checkpoint, what="checkpoint file", flag="--checkpoint")
    config_path = _require_file(args.config, what="configuration file", flag="--config")
    episodes_path = _require_file(args.episodes_file, what="episodes file", flag="--episodes-file")
    episodes = load_episode_specs(episodes_path)

    payload = load_payload(checkpoint_path, family)
    require_family(payload, family, checkpoint_path)
    identity = checkpoint_identity(checkpoint_path, payload)
    policy_kind = policy_kind_for(identity)

    # _build_capture reads the demo's streaming flags, which the record-eval parser does not
    # define. record-eval writes a trace and serves no viewer, so they are set here rather
    # than by widening the shared parser.
    for name, value in (("live", False), ("stream_output", None), ("capture_substeps", False)):
        if not hasattr(args, name):
            setattr(args, name, value)

    setup = ROUTE_SETUPS[route](config_path)
    device = "cpu"
    trace_id = f"record-eval-{route}-{identity.sha256[7:19]}-{int(time.time())}"
    manifest = build_manifest(
        trace_id=trace_id, route=route, family=family, setup=setup, identity=identity,
        policy_kind=policy_kind, config_path=config_path, episodes_path=episodes_path,
        episodes=episodes, seed=int(args.seed), device=device,
    )
    writer, trace_dir = _trace_writer(args, manifest=manifest)
    capture, gate, sink, _stream_dir = _build_capture(args, record=True)

    # Announced before the environment exists, so the scope is printed ahead of everything
    # this invocation executes, not only ahead of the first step.
    announce_execution(
        what="forward-only evaluation of one explicitly named checkpoint",
        route=route,
        source_kind="checkpoint_rollout",
        policy_identity=identity.label,
        output=trace_dir,
        optimizer_updates=0,
        extra=[
            f"checkpoint          : {checkpoint_path}",
            f"declared loader     : {family.loader}",
            f"policy kind         : {policy_kind.value}",
            f"config              : {config_path}",
            f"episodes declared   : {len(episodes)} from {episodes_path}",
            "statistical unit    : one checkpoint evaluation (1 replicate)",
            f"capture profile     : {capture.profile.value}",
        ],
    )
    runtime = setup.build(
        gate=gate, sink=sink, writer=writer, trace_id=trace_id, identity=identity,
        policy_kind=policy_kind, seed=int(args.seed),
    )

    import torch

    decision_steps = 0
    try:
        with torch.no_grad():
            policy = POLICY_BUILDERS[route](
                payload=payload, checkpoint_path=checkpoint_path, env=runtime.env, device=device
            )
            for module in policy.modules():
                module.eval()
            for spec in episodes:
                observations, info = runtime.env.reset(seed=spec.seed)
                state = (info or {}).get("state")
                policy.reset()
                steps = 0
                while spec.max_steps is None or steps < spec.max_steps:
                    actions = policy.act(observations, state=state, step=steps)
                    observations, reward, terminated, truncated, info = runtime.env.step(actions)
                    state = (info or {}).get("next_state", state)
                    steps += 1
                    done = bool(terminated) or bool(truncated)
                    policy.note_step(
                        reward=reward, observations=observations, state=state, done=done
                    )
                    if done:
                        break
                decision_steps += steps
                print(
                    f"episode {spec.episode_id}: {steps} decision steps, "
                    f"{runtime.observer.emitted} frames emitted so far",
                    file=sys.stderr,
                )
        runtime.observer.finish(state=StreamState.ENDED)
        n_frames, status = 0, "not_written"
        if writer is not None:
            index = writer.close()
            n_frames, status = index.n_frames, index.status
        print(f"episodes evaluated     : {len(episodes)}")
        print(f"decision steps         : {decision_steps}")
        print(f"frames written         : {n_frames} (trace status {status})")
        print("frames refused, by reason:")
        for name, value in gate.counters.to_json().items():
            if name.startswith("refused_"):
                print(f"  {name[len('refused_'):]:24s} {value}")
        print(f"trace                  : {trace_dir}")
        _print_gate_summary(gate, runtime.observer)
    finally:
        runtime.close()
    return 0
