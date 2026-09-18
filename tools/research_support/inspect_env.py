"""Effective-configuration and environment inspection.

Two clearly separated modes, because they have different costs and different risks:

* **Static** (the default) parses the recorded configuration document and the construction
  code's declared defaults. It imports no environment package, constructs nothing, compiles
  nothing, downloads nothing and starts no process. Every reported value carries its
  provenance: ``recorded``, ``verified_runtime``, ``static_inference`` or ``unknown``.
* **Probe** (``--probe``) constructs the environment **in a child process** so the parent's
  RNG state and global configuration cannot be disturbed, and reports what the constructor
  actually resolved. A probe may take a short bounded fixed-action sequence to observe
  reward and termination behaviour. It never trains.

A dynamically composed Python configuration cannot always be traced safely by reading
source alone, so an override chain that was not observed is reported as ``unknown`` rather
than guessed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .interpreters import scientific_interpreter
from .records import Measured, Validity, dumps, file_hash

#: Interpreter used for a probe. The scientific environment is the one that can import the
#: environment packages; nothing is ever installed into it. Resolved for the running host
#: (see ``interpreters.py``) so a probe from a WSL checkout uses the Linux build rather
#: than reaching across ``/mnt/c`` for a Windows one.
DEFAULT_PROBE_INTERPRETER = scientific_interpreter()

ROUTES = ("service-restoration", "legacy-mobile-relay", "scenario1")


@dataclass
class FieldReport:
    """One configuration value plus where the value came from."""

    name: str
    raw: Any
    effective: Measured
    unit: str | None
    source_file: str | None
    source_key: str | None
    provenance: str  # recorded | verified_runtime | static_inference | unknown

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "raw": self.raw,
            "effective": self.effective.to_json(),
            "unit": self.unit,
            "source_file": self.source_file,
            "source_key": self.source_key,
            "provenance": self.provenance,
        }


@dataclass
class EnvReport:
    route: str
    config_path: str | None
    config_hash: str | None
    static_fields: list[FieldReport] = field(default_factory=list)
    probe: dict[str, Any] | None = None
    probe_status: str = "not_requested"
    capabilities: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": "research_support.env_report.1",
            "route": self.route,
            "config_path": self.config_path,
            "config_hash": self.config_hash,
            "static_fields": [f.to_json() for f in self.static_fields],
            "probe_status": self.probe_status,
            "probe": self.probe,
            "capabilities": self.capabilities,
            "warnings": self.warnings,
            "errors": self.errors,
        }


# --------------------------------------------------------------------------------------
# Static inspection
# --------------------------------------------------------------------------------------


_SR_FIELDS: tuple[tuple[str, str | None], ...] = (
    ("environment_id", None),
    ("preset_name", None),
    ("seed", None),
    ("n_uavs", "count"),
    ("region.min_xy_m", "m"),
    ("region.max_xy_m", "m"),
    ("episode.semantics", None),
    ("episode.duration_s", "s"),
    ("episode.decision_dt_s", "s"),
    ("episode.physics_dt_s", "s"),
    ("episode.quadrature", None),
    ("source.kind", None),
    ("source.demand_scale_mbps", "Mbps"),
    ("source.split", None),
    ("source.max_demand_points", "count"),
    ("observations.mode", None),
    ("observations.telemetry_delay_s", "s"),
    ("observations.telemetry_ttl_s", "s"),
    ("observations.sensing_radius_m", "m"),
    ("reward.reference_scale_mbps", "Mbps"),
    ("reward.reference_dt_s", "s"),
    ("reward.motion_weight", "dimensionless"),
    ("dynamics.max_speed_mps", "m/s"),
    ("dynamics.altitude_range_m", "m"),
    ("scheduler.objective", None),
    ("scheduler.solver_method", None),
    ("network.max_backhaul_hops", "count"),
    ("evaluation.recovery_fraction_rho", "ratio"),
    ("evaluation.recovery_sustain_s", "s"),
)

_LEGACY_FIELDS: tuple[tuple[str, str | None], ...] = (
    ("area_size", "m"),
    ("n_agents", "count"),
    ("n_users", "count"),
    ("n_clusters", "count"),
    ("cluster_std", "m"),
    ("user_distribution", None),
    ("user_movement_model", None),
    ("user_max_speed", "m/s"),
    ("cluster_migration_speed", "m/s"),
    ("uav_init_mode", None),
    ("uav_start_area_size", "m"),
    ("n_ground_bs", "count"),
    ("min_sinr", "dB"),
    ("max_hops", "count"),
    ("max_connections", "count"),
    ("observation_radius", "m"),
    ("height_range", "m"),
    ("max_speed", "m/s"),
    ("time_step", "s"),
    ("episode_length", "steps"),
)


def _dig(payload: Mapping[str, Any], dotted: str) -> tuple[Any, bool]:
    node: Any = payload
    for part in dotted.split("."):
        if isinstance(node, Mapping) and part in node:
            node = node[part]
        else:
            return None, False
    return node, True


def _static_service_restoration(config_path: Path, report: EnvReport) -> None:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    provenance_map = payload.get("parameter_provenance") or {}
    for name, unit in _SR_FIELDS:
        raw, present = _dig(payload, name)
        if present:
            effective = (
                Measured.ok(raw, unit=unit)
                if isinstance(raw, (int, float, str, bool))
                else Measured.ok(json.dumps(raw), unit=unit)
            )
            provenance = "recorded"
        else:
            effective = Measured.unknown(
                "absent from the configuration document; the constructor default applies "
                "but was not observed",
                unit=unit,
            )
            provenance = "static_inference"
        report.static_fields.append(
            FieldReport(
                name=name,
                raw=raw if present else None,
                effective=effective,
                unit=unit,
                source_file=str(config_path),
                source_key=name if present else None,
                provenance=provenance,
            )
        )
    for key, value in provenance_map.items():
        report.warnings.append(f"declared parameter provenance: {key} = {value}")
    if payload.get("source", {}).get("kind") == "synthetic_fixture":
        report.warnings.append(
            "this configuration's demand source is an ANALYTIC FIXTURE: it is not real "
            "activity data, not measured Mbps and not a population count"
        )


def _static_legacy(config_path: Path | None, report: EnvReport) -> None:
    overrides: dict[str, Any] = {}
    if config_path is not None:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        overrides = payload.get("config_overrides", {}) or {}
        for note in payload.get("known_limitations", ()):
            report.warnings.append(f"declared limitation: {note}")
        for key, value in (payload.get("parameter_provenance") or {}).items():
            report.warnings.append(f"declared parameter provenance: {key} = {value}")
    for name, unit in _LEGACY_FIELDS:
        if name in overrides:
            report.static_fields.append(
                FieldReport(
                    name=name,
                    raw=overrides[name],
                    effective=Measured.ok(overrides[name], unit=unit),
                    unit=unit,
                    source_file=str(config_path) if config_path else None,
                    source_key=f"config_overrides.{name}",
                    provenance="recorded",
                )
            )
        else:
            report.static_fields.append(
                FieldReport(
                    name=name,
                    raw=None,
                    effective=Measured.unknown(
                        "not overridden here; the process-core Config default applies and is "
                        "only observable through --probe",
                        unit=unit,
                    ),
                    unit=unit,
                    source_file=None,
                    source_key=None,
                    provenance="unknown",
                )
            )
    report.warnings.append(
        "scenario alias 'base' constructs envs.pettingzoo.relay.forced_relay."
        "UAVForcedRelayEnv, not routed_core; verified in ha_ctse_process/env_factory.py"
    )
    report.warnings.append(
        "on this scenario uav_bs_connections is identically False because the modelled "
        "base-to-UAV SINR is far below min_sinr; see "
        "docs/Claude_docs/findings/2026-09-18-forced-relay-downlink-sinr-and-dead-backhaul-"
        "adjacency.md"
    )


# --------------------------------------------------------------------------------------
# Probe
# --------------------------------------------------------------------------------------

_PROBE_SOURCE = r'''
import json, sys
sys.path.insert(0, {repo!r})
import numpy as np

route = {route!r}
config_path = {config!r}
out = {{"route": route}}

if route == "service-restoration":
    from envs.uav_service_restoration.config import load_config, config_to_dict
    from envs.uav_service_restoration.env import UAVServiceRestorationEnv
    config = load_config(config_path)
    env = UAVServiceRestorationEnv(config)
    out["constructor"] = "envs.uav_service_restoration.env.UAVServiceRestorationEnv"
    out["schema"] = env.schema()
    out["capture_capabilities"] = env.capture_capabilities()
    out["resolved_config"] = config_to_dict(config)
    out["n_agents"] = len(env.possible_agents)
    out["obs_dim"] = env.get_obs_dim()
    out["state_dim"] = env.get_state_dim()
    out["render_modes"] = list(env.metadata.get("render_modes", []))
    obs, info = env.reset(seed=17)
    out["observation_dtype"] = str(np.asarray(next(iter(obs.values()))).dtype)
    out["observation_shape"] = list(np.asarray(next(iter(obs.values()))).shape)
    out["info_keys"] = sorted(next(iter(info.values())).keys())
    # A bounded fixed-action sequence: three zero-action steps to observe reward and
    # boundary behaviour. No optimizer, no gradient, no learning.
    rewards = []
    for _ in range(3):
        if not env.agents:
            break
        actions = {{a: np.zeros(3, dtype=np.float32) for a in env.agents}}
        _o, r, term, trunc, _i = env.step(actions)
        rewards.append(float(next(iter(r.values()))))
    out["fixed_action_rewards"] = rewards
    out["terminated_after_three_steps"] = bool(any(term.values())) if rewards else None
    out["truncated_after_three_steps"] = bool(any(trunc.values())) if rewards else None
    diagnostics = env.get_privileged_diagnostics()
    out["dataset_hash"] = diagnostics.get("dataset_hash")
    out["is_real_activity_data"] = diagnostics["source_metadata"]["is_real_activity_data"]
    out["calibration_summary"] = diagnostics.get("calibration_summary")
    out["physical_time_s"] = env.physical_time_s
    env.close()

elif route in ("legacy-mobile-relay", "scenario1"):
    from ha_ctse_process.config import Config
    from ha_ctse_process.env_factory import EnvSpec, make_env, normalize_scenario
    overrides = {{}}
    scenario = "base" if route == "legacy-mobile-relay" else "base"
    if config_path:
        with open(config_path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
        overrides = document.get("config_overrides", {{}}) or {{}}
        scenario = document.get("scenario", scenario)
    config = Config()
    unknown = [k for k in overrides if not hasattr(config, k)]
    if unknown:
        raise SystemExit("unknown config overrides: " + repr(unknown))
    for key, value in overrides.items():
        setattr(config, key, value)
    out["normalized_scenario"] = normalize_scenario(scenario)
    env = make_env(config, EnvSpec(scenario=scenario, seed=17, rank=0))()
    raw = env.env
    out["constructor"] = type(raw).__module__ + "." + type(raw).__name__
    out["adapter"] = type(env).__module__ + "." + type(env).__name__
    out["render_modes"] = list(getattr(raw, "metadata", {{}}).get("render_modes", []))
    out["n_agents"] = int(env.n_uavs)
    out["obs_dim"] = int(env.obs_dim)
    out["state_dim"] = int(env.state_dim)
    out["action_dim"] = int(env.action_dim)
    for name in ({legacy_names!r}):
        if hasattr(raw, name):
            value = getattr(raw, name)
            try:
                json.dumps(value)
            except TypeError:
                value = repr(value)
            out.setdefault("resolved_config", {{}})[name] = value
    obs, info = env.reset(seed=17)
    out["observation_dtype"] = str(np.asarray(obs).dtype)
    out["observation_shape"] = list(np.asarray(obs).shape)
    state_info = (info or {{}}).get("state_info") or {{}}
    out["state_info_keys"] = sorted(state_info.keys())
    rewards = []
    for _ in range(3):
        _o, r, term, trunc, _i = env.step(np.zeros((env.n_uavs, env.action_dim), dtype=np.float32))
        rewards.append(float(np.asarray(r).reshape(-1)[0]))
    out["fixed_action_rewards"] = rewards
    out["terminated_after_three_steps"] = bool(np.any(term))
    out["truncated_after_three_steps"] = bool(np.any(trunc))
    users = state_info.get("user_positions")
    out["has_mobile_ues"] = bool(getattr(raw, "user_max_speed", 0) and users is not None)
    env.close()
else:
    raise SystemExit("unsupported route: " + route)

out["optimizer_updates"] = 0
sys.stdout.write("<<<PROBE_JSON>>>" + json.dumps(out, default=str))
'''


def run_probe(
    route: str,
    config_path: str | None,
    *,
    interpreter: str | None = None,
    repo_root: str | None = None,
    timeout_s: float = 300.0,
) -> tuple[str, dict[str, Any]]:
    """Construct the environment in a child process and report what it resolved.

    A child process is the containment: the parent's RNG state, imported modules and
    global configuration are untouched whatever the constructor does. Native build
    behaviour is detected rather than triggered silently -- if the route needs a compiled
    extension the child says so in its error text instead of the parent surprising a user
    who asked for an inspection.
    """

    root = repo_root or str(Path(__file__).resolve().parents[2])
    source = _PROBE_SOURCE.format(
        repo=root,
        route=route,
        config=config_path,
        legacy_names=(
            "area_size", "n_uavs", "n_users", "n_clusters", "cluster_std",
            "user_distribution", "user_movement_model", "user_max_speed",
            "cluster_migration_speed", "uav_init_mode", "uav_start_area_size",
            "n_ground_bs", "min_sinr", "max_hops", "max_connections",
            "observation_radius", "max_speed", "time_step", "max_steps",
            "tx_power", "ground_bs_tx_power", "noise_power", "bandwidth", "use_fdma",
        ),
    )
    executable = interpreter or DEFAULT_PROBE_INTERPRETER
    if not Path(executable).exists():
        executable = sys.executable
    try:
        completed = subprocess.run(
            [executable, "-c", source],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except subprocess.TimeoutExpired:
        return "timeout", {"error": f"probe did not finish within {timeout_s} s"}
    marker = "<<<PROBE_JSON>>>"
    if marker in completed.stdout:
        payload = completed.stdout.split(marker, 1)[1]
        try:
            return "ok", json.loads(payload)
        except json.JSONDecodeError as error:
            return "malformed", {"error": str(error), "stdout_tail": payload[-2000:]}
    return "failed", {
        "returncode": completed.returncode,
        "stderr_tail": completed.stderr[-4000:],
        "stdout_tail": completed.stdout[-2000:],
    }


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def inspect_env(
    *,
    route: str,
    config_path: str | None,
    probe: bool = False,
    interpreter: str | None = None,
) -> EnvReport:
    if route not in ROUTES:
        raise ValueError(f"unknown route {route!r}; supported: {', '.join(ROUTES)}")
    resolved = Path(config_path).resolve() if config_path else None
    report = EnvReport(
        route=route,
        config_path=str(resolved) if resolved else None,
        config_hash=file_hash(str(resolved)) if resolved and resolved.is_file() else None,
    )
    if resolved is not None and not resolved.is_file():
        report.errors.append(f"configuration file not found: {resolved}")
        return report

    if route == "service-restoration":
        if resolved is None:
            report.errors.append("--config is required for the service-restoration route")
        else:
            _static_service_restoration(resolved, report)
    else:
        _static_legacy(resolved, report)

    if not probe:
        report.probe_status = "not_requested"
        report.warnings.append(
            "static inspection only: nothing was constructed, imported, compiled or "
            "executed. Use --probe to observe what the constructor actually resolves."
        )
        return report

    status, payload = run_probe(route, str(resolved) if resolved else None, interpreter=interpreter)
    report.probe_status = status
    report.probe = payload
    if status != "ok":
        report.errors.append(f"probe {status}: {payload.get('error') or payload.get('stderr_tail', '')[-400:]}")
        return report

    # Promote observed values over static inference, and say which they are.
    resolved_config = payload.get("resolved_config") or {}
    observed: dict[str, Any] = {}
    _flatten(resolved_config, "", observed)
    for item in report.static_fields:
        if item.name in observed:
            value = observed[item.name]
            if isinstance(value, (int, float, str, bool)):
                item.effective = Measured.ok(value, unit=item.unit)
            else:
                item.effective = Measured.ok(json.dumps(value), unit=item.unit)
            item.provenance = "verified_runtime"
    report.capabilities = payload.get("capture_capabilities") or {}
    if payload.get("render_modes") == []:
        report.warnings.append(
            "the environment advertises no render modes; a runtime viewer is provided by "
            "this suite's capture layer, not by the environment"
        )
    if payload.get("is_real_activity_data") is False:
        report.warnings.append(
            "probe confirms the demand source is NOT real activity data"
        )
    return report


def _flatten(payload: Any, prefix: str, out: dict[str, Any]) -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            out[name] = value
            _flatten(value, name, out)


def write_env_report(report: EnvReport, output_dir: Path) -> Path:
    """Write the JSON report plus a human-readable Markdown summary."""

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "env_report.json").write_text(
        dumps(report.to_json(), indent=2), encoding="utf-8"
    )
    lines = [
        f"# Environment inspection: {report.route}",
        "",
        f"- configuration: `{report.config_path or 'none'}`",
        f"- configuration hash: `{report.config_hash or 'n/a'}`",
        f"- probe: **{report.probe_status}**",
        "",
        "## Effective values",
        "",
        "| field | effective | unit | provenance | source |",
        "|---|---|---|---|---|",
    ]
    for item in report.static_fields:
        effective = item.effective
        value = (
            str(effective.value)
            if effective.validity is Validity.OK
            else f"_{effective.validity.value}: {effective.reason}_"
        )
        lines.append(
            f"| `{item.name}` | {value} | {item.unit or ''} | {item.provenance} | "
            f"{item.source_key or ''} |"
        )
    if report.probe:
        lines += [
            "",
            "## Observed at construction",
            "",
            f"- constructor: `{report.probe.get('constructor')}`",
            f"- agents: {report.probe.get('n_agents')}",
            f"- observation: shape {report.probe.get('observation_shape')} "
            f"dtype {report.probe.get('observation_dtype')}",
            f"- state dim: {report.probe.get('state_dim')}",
            f"- render modes: {report.probe.get('render_modes')}",
            f"- fixed-action rewards (3 zero-action steps): "
            f"{report.probe.get('fixed_action_rewards')}",
            f"- optimizer updates: {report.probe.get('optimizer_updates')}",
        ]
    if report.warnings:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in report.warnings]
    if report.errors:
        lines += ["", "## Errors", ""] + [f"- {e}" for e in report.errors]
    path = output_dir / "env_report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
