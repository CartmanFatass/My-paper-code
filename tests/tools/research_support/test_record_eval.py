"""Tests for the trusted-checkpoint evaluation recorder.

The properties under test are the refusals, because they are what makes a recorded
checkpoint evaluation evidence rather than an illustration:

* every declared input is resolved before anything executes, and a missing one is named;
* an unknown route lists the routes that exist instead of guessing one;
* a payload the route's declared loader does not describe is refused with the keys it
  actually carries, and **no** second loader family, fixture or substitute policy runs;
* the recorded checkpoint identity is the artifact's real hash, and identity the payload
  does not carry is recorded as absent rather than as zero;
* the manifest states that one invocation of many episodes is one evaluation with one
  independent replicate.

The end-to-end cases replace the route's environment and the declared policy builder with
minimal fakes, so the orchestration - announcement, real trace writer, manifest, eval mode,
summary - is exercised without a trained model. Everything up to and including the loader
boundary is tested against real ``torch.save`` payloads.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import torch

from tools.research_support import record_eval as module
from tools.research_support.cli import CliError, build_parser
from tools.research_support.records import Validity, file_hash


# --------------------------------------------------------------------------------------
# Fixtures and fakes
# --------------------------------------------------------------------------------------


def _valid_payload(**overrides: Any) -> dict[str, Any]:
    """A payload carrying exactly the keys the declared process-core loader needs."""

    payload: dict[str, Any] = {
        "algorithm": "ha_ctse_process_standalone",
        "checkpoint_schema_version": 2,
        "high": {"weight": torch.zeros(2, 2)},
        "low": {"weight": torch.zeros(2, 2)},
        "process": {"weight": torch.zeros(2, 2)},
        "config_name": "ha_ctse_process.config",
        "n_agents": 3,
        "skill_interval": 10,
        "total_steps": 4096,
        "update_idx": 8,
    }
    payload.update(overrides)
    return payload


def _write_checkpoint(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    return path


def _write_episodes(path: Path, entries: Any) -> Path:
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def _args(tmp_path: Path, **overrides: Any):
    """Parse a real record-eval command line so the test uses the shipped parser."""

    values = {
        "route": "service-restoration",
        "checkpoint": str(tmp_path / "checkpoint.pt"),
        "config": str(tmp_path / "env.json"),
        "episodes-file": str(tmp_path / "episodes.json"),
        "trace-output": str(tmp_path / "trace"),
    }
    values.update({key.replace("_", "-"): value for key, value in overrides.items()})
    argv = ["record-eval"]
    for key, value in values.items():
        argv.extend([f"--{key}", str(value)])
    return build_parser().parse_args(argv)


def _complete_inputs(tmp_path: Path, *, payload: dict[str, Any] | None = None) -> None:
    _write_checkpoint(tmp_path / "checkpoint.pt", payload if payload is not None else _valid_payload())
    (tmp_path / "env.json").write_text("{}", encoding="utf-8")
    _write_episodes(
        tmp_path / "episodes.json",
        [{"episode_id": "e0", "seed": 11}, {"episode_id": "e1", "seed": 12}],
    )


class _FakeObserver:
    def __init__(self) -> None:
        self.emitted = 0
        self.finished_with: Any = None

    def finish(self, *, state: Any) -> None:
        self.finished_with = state


class _FakeEnv:
    """Minimal array-adapter contract: reset -> (obs, info), step -> 5-tuple."""

    def __init__(self, *, episode_length: int = 3) -> None:
        self.n_uavs = 3
        self.state_dim = 4
        self.obs_dim = 2
        self.action_dim = 2
        self.episode_length = episode_length
        self.reset_seeds: list[int] = []
        self.closed = False
        self._step = 0

    def reset(self, seed: int | None = None):
        self.reset_seeds.append(int(seed))
        self._step = 0
        return "obs", {"state": "state"}

    def step(self, actions: Any):
        self._step += 1
        truncated = self._step >= self.episode_length
        return "obs", 0.0, False, truncated, {"next_state": "state"}

    def close(self) -> None:
        self.closed = True


class _FakePolicy:
    """Stands in for a loaded checkpoint; records that it was driven forward only."""

    def __init__(self) -> None:
        self.module = torch.nn.Linear(2, 2)
        self.resets = 0
        self.acts = 0
        self.notes = 0
        self.grad_enabled_during_act: list[bool] = []

    def modules(self) -> list[Any]:
        return [self.module]

    def reset(self) -> None:
        self.resets += 1

    def act(self, observations: Any, *, state: Any, step: int) -> Any:
        self.acts += 1
        self.grad_enabled_during_act.append(torch.is_grad_enabled())
        return [0.0, 0.0]

    def note_step(self, *, reward: Any, observations: Any, state: Any, done: bool) -> None:
        self.notes += 1


@pytest.fixture()
def fake_route(monkeypatch: pytest.MonkeyPatch):
    """Replace the route's environment/observer and the declared policy builder."""

    env = _FakeEnv()
    observer = _FakeObserver()
    policy = _FakePolicy()
    built: dict[str, Any] = {}

    def setup(config_path: Path) -> module.RouteSetup:
        built["config_path"] = config_path

        def build(*, seed: int, **provenance: Any) -> module.RouteRuntime:
            built["provenance"] = provenance
            built["seed"] = seed
            return module.RouteRuntime(env=env, observer=observer, close=env.close)

        return module.RouteSetup(
            environment_id="fake_env_v0", manifest_extra={"preset_name": "fake"}, build=build
        )

    def build_policy(**kwargs: Any) -> _FakePolicy:
        built["policy_kwargs"] = kwargs
        return policy

    monkeypatch.setitem(module.ROUTE_SETUPS, "service-restoration", setup)
    monkeypatch.setitem(module.POLICY_BUILDERS, "service-restoration", build_policy)
    return {"env": env, "observer": observer, "policy": policy, "built": built}


@pytest.fixture()
def refusing_route(monkeypatch: pytest.MonkeyPatch):
    """Make any attempt to construct an environment or a policy a test failure."""

    def refuse(*args: Any, **kwargs: Any):
        raise AssertionError("record-eval executed something after a refusal")

    for route in module.SUPPORTED_ROUTES:
        monkeypatch.setitem(module.ROUTE_SETUPS, route, refuse)
        monkeypatch.setitem(module.POLICY_BUILDERS, route, refuse)


# --------------------------------------------------------------------------------------
# Input resolution
# --------------------------------------------------------------------------------------


def test_unknown_route_names_the_supported_routes(tmp_path: Path, refusing_route: None) -> None:
    _complete_inputs(tmp_path)
    args = _args(tmp_path, route="uav-swarm-v9")
    with pytest.raises(CliError) as error:
        module.record_eval(args)
    message = str(error.value)
    assert "uav-swarm-v9" in message
    for route in module.SUPPORTED_ROUTES:
        assert route in message


def test_missing_checkpoint_names_the_path(tmp_path: Path, refusing_route: None) -> None:
    _complete_inputs(tmp_path)
    missing = tmp_path / "nowhere" / "final.pt"
    with pytest.raises(CliError) as error:
        module.record_eval(_args(tmp_path, checkpoint=str(missing)))
    message = str(error.value)
    assert str(missing.resolve()) in message
    assert "checkpoint" in message


def test_missing_config_is_refused(tmp_path: Path, refusing_route: None) -> None:
    _complete_inputs(tmp_path)
    (tmp_path / "env.json").unlink()
    with pytest.raises(CliError) as error:
        module.record_eval(_args(tmp_path))
    assert "configuration file does not exist" in str(error.value)


def test_missing_episodes_file_is_refused(tmp_path: Path, refusing_route: None) -> None:
    _complete_inputs(tmp_path)
    (tmp_path / "episodes.json").unlink()
    with pytest.raises(CliError) as error:
        module.record_eval(_args(tmp_path))
    assert "episodes file does not exist" in str(error.value)


def test_empty_episodes_file_is_refused(tmp_path: Path, refusing_route: None) -> None:
    _complete_inputs(tmp_path)
    (tmp_path / "episodes.json").write_text("   \n", encoding="utf-8")
    with pytest.raises(CliError) as error:
        module.record_eval(_args(tmp_path))
    assert "empty" in str(error.value)


def test_episode_list_with_no_entries_is_refused(tmp_path: Path) -> None:
    path = _write_episodes(tmp_path / "episodes.json", {"episodes": []})
    with pytest.raises(CliError) as error:
        module.load_episode_specs(path)
    assert "declares no episodes" in str(error.value)


def test_unparseable_episodes_file_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "episodes.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(CliError) as error:
        module.load_episode_specs(path)
    assert "not valid JSON" in str(error.value)


def test_episode_without_a_seed_is_refused(tmp_path: Path) -> None:
    path = _write_episodes(tmp_path / "episodes.json", [{"episode_id": "e0"}])
    with pytest.raises(CliError) as error:
        module.load_episode_specs(path)
    assert "no 'seed'" in str(error.value)


def test_episode_specs_accept_list_object_and_jsonl(tmp_path: Path) -> None:
    entries = [{"episode_id": "e0", "seed": 5, "max_steps": 2}, {"id": "e1", "seed": 6}]
    from_list = module.load_episode_specs(_write_episodes(tmp_path / "a.json", entries))
    from_object = module.load_episode_specs(
        _write_episodes(tmp_path / "b.json", {"episodes": entries})
    )
    lines = tmp_path / "c.jsonl"
    lines.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8")
    from_jsonl = module.load_episode_specs(lines)

    assert from_list == from_object == from_jsonl
    assert [spec.episode_id for spec in from_list] == ["e0", "e1"]
    assert [spec.seed for spec in from_list] == [5, 6]
    assert from_list[0].max_steps == 2
    assert from_list[1].max_steps is None
    assert all(spec.episode_id_source == "declared" for spec in from_list)


def test_a_bare_seed_list_is_read_and_its_labels_are_marked_derived(tmp_path: Path) -> None:
    """The seed-list form the rest of this CLI reads stays usable, and says so."""

    from_list = module.load_episode_specs(_write_episodes(tmp_path / "a.json", [7, 9]))
    from_object = module.load_episode_specs(
        _write_episodes(tmp_path / "b.json", {"episode_seeds": [7, 9]})
    )
    from_seeds = module.load_episode_specs(
        _write_episodes(tmp_path / "c.json", {"seeds": [7, 9]})
    )

    assert from_list == from_object == from_seeds
    assert [spec.seed for spec in from_list] == [7, 9]
    assert [spec.episode_id for spec in from_list] == ["seed-7", "seed-9"]
    assert all(spec.episode_id_source == "derived_from_seed" for spec in from_list)


def test_per_episode_config_overrides_are_refused_not_silently_ignored(tmp_path: Path) -> None:
    """One invocation builds one environment; an override that did nothing would lie."""

    path = _write_episodes(
        tmp_path / "episodes.json",
        [{"episode_id": "e0", "seed": 5, "config_overrides": {"n_uavs": 9}}],
    )
    with pytest.raises(CliError) as error:
        module.load_episode_specs(path)
    message = str(error.value)
    assert "config_overrides" in message
    assert "e0" in message
    assert "one record-eval per configuration" in message


# --------------------------------------------------------------------------------------
# The declared loader boundary
# --------------------------------------------------------------------------------------


def test_payload_of_another_family_is_refused_with_the_keys_found(
    tmp_path: Path, refusing_route: None
) -> None:
    _complete_inputs(tmp_path)
    _write_checkpoint(
        tmp_path / "checkpoint.pt",
        {"skill_coordinator": {}, "skill_discoverer": {}, "coordinator_optimizer": {}},
    )
    with pytest.raises(CliError) as error:
        module.record_eval(_args(tmp_path))
    message = str(error.value)
    # The keys actually present are named, so the operator can see which family this is.
    assert "skill_coordinator" in message
    assert "skill_discoverer" in message
    # The keys the declared loader wanted, and the fact that nothing else was tried.
    assert "algorithm" in message
    assert module.PROCESS_CORE_FAMILY.loader in message
    assert "no second loader family" in message
    # Nothing was executed and no output directory was created.
    assert not (tmp_path / "trace").exists()


def test_wrong_algorithm_fingerprint_is_refused(tmp_path: Path) -> None:
    payload = _valid_payload(algorithm="some_other_learner")
    with pytest.raises(CliError) as error:
        module.require_family(payload, module.PROCESS_CORE_FAMILY, Path("c.pt"))
    message = str(error.value)
    assert "'some_other_learner'" in message
    assert "missing keys: none" in message


def test_non_mapping_payload_is_refused(tmp_path: Path, refusing_route: None) -> None:
    _complete_inputs(tmp_path)
    torch.save([1, 2, 3], tmp_path / "checkpoint.pt")
    with pytest.raises(CliError) as error:
        module.record_eval(_args(tmp_path))
    assert "not the mapping the declared loader" in str(error.value)


def test_every_route_declares_exactly_one_loader() -> None:
    assert set(module.ROUTE_CHECKPOINT_FAMILY) == set(module.ROUTE_SETUPS)
    assert set(module.ROUTE_CHECKPOINT_FAMILY) == set(module.POLICY_BUILDERS)
    for family in module.ROUTE_CHECKPOINT_FAMILY.values():
        assert isinstance(family, module.CheckpointFamily)
        assert "algorithm" in family.required_keys


# --------------------------------------------------------------------------------------
# Checkpoint identity
# --------------------------------------------------------------------------------------


def test_checkpoint_identity_hash_matches_file_hash(tmp_path: Path) -> None:
    path = _write_checkpoint(tmp_path / "checkpoint.pt", _valid_payload())
    identity = module.checkpoint_identity(path, _valid_payload())
    assert identity.sha256 == file_hash(str(path))
    assert identity.size_bytes == path.stat().st_size
    assert identity.mtime_utc.endswith("+00:00")
    assert identity.fields["global_step"].value == 4096
    assert identity.fields["global_step"].source == "total_steps"
    assert identity.sha256 in identity.label


def test_absent_identity_is_recorded_absent_not_zero(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload.pop("total_steps")
    payload.pop("update_idx")
    payload["preset"] = None
    path = _write_checkpoint(tmp_path / "checkpoint.pt", payload)
    identity = module.checkpoint_identity(path, payload)

    for name in ("global_step", "update_index", "episode"):
        measured = identity.fields[name]
        assert measured.value is None
        assert measured.validity is Validity.NOT_RECORDED
        assert measured.reason
    # A payload key recorded as null is a missing artifact, not an unrecorded field.
    identity_with_null = module.checkpoint_identity(path, {**payload, "config_name": None})
    assert identity_with_null.fields["config_name"].validity is Validity.MISSING_ARTIFACT


def test_policy_kind_follows_the_recorded_step_count(tmp_path: Path) -> None:
    path = _write_checkpoint(tmp_path / "checkpoint.pt", _valid_payload())
    trained = module.policy_kind_for(module.checkpoint_identity(path, _valid_payload()))
    untrained = module.policy_kind_for(
        module.checkpoint_identity(path, _valid_payload(total_steps=0))
    )
    unrecorded_payload = _valid_payload()
    unrecorded_payload.pop("total_steps")
    unknown = module.policy_kind_for(module.checkpoint_identity(path, unrecorded_payload))

    assert trained.value == "trained_checkpoint"
    assert untrained.value == "untrained_checkpoint"
    assert unknown.value == "unknown"


# --------------------------------------------------------------------------------------
# Orchestration and manifest
# --------------------------------------------------------------------------------------


def _read_manifest(trace_dir: Path) -> dict[str, Any]:
    return json.loads((trace_dir / "trace_manifest.json").read_text(encoding="utf-8"))


def test_manifest_records_one_independent_replicate(
    tmp_path: Path, fake_route: dict[str, Any]
) -> None:
    _complete_inputs(tmp_path)
    assert module.record_eval(_args(tmp_path)) == 0
    manifest = _read_manifest(tmp_path / "trace")

    assert manifest["independent_replicates"] == 1
    assert manifest["statistical_unit"] == "one checkpoint evaluation"
    assert manifest["n_selected_episodes"] == 2
    assert manifest["optimizer_updates"] == 0
    assert manifest["formal_training_fits"] == 0
    assert manifest["optimizer_objects_constructed_here"] == 0
    assert manifest["source_kind"] == "checkpoint_evaluation"
    assert manifest["policy_kind"] == "trained_checkpoint"
    assert manifest["checkpoint_loader"]["loader"] == module.PROCESS_CORE_FAMILY.loader
    assert manifest["checkpoint_loader"]["fallback_families_tried"] == 0
    assert manifest["checkpoint"]["sha256"] == file_hash(str(tmp_path / "checkpoint.pt"))
    assert [episode["seed"] for episode in manifest["episodes"]] == [11, 12]
    assert all(episode["episode_id_source"] == "declared" for episode in manifest["episodes"])


def test_rollout_is_forward_only_and_reports_its_scope(
    tmp_path: Path, fake_route: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    _complete_inputs(tmp_path)
    assert module.record_eval(_args(tmp_path)) == 0
    captured = capsys.readouterr()
    policy: _FakePolicy = fake_route["policy"]
    env: _FakeEnv = fake_route["env"]

    # Declared seeds drove the episodes; the command invented none.
    assert env.reset_seeds == [11, 12]
    assert policy.resets == 2
    assert policy.acts == 6
    assert policy.notes == 6
    # Forward only: gradients were off and the module was put in eval mode.
    assert policy.grad_enabled_during_act == [False] * 6
    assert policy.module.training is False
    assert env.closed is True
    assert fake_route["observer"].finished_with is not None

    assert "EXECUTION SCOPE" in captured.err
    assert "optimizer updates   : 0" in captured.err
    assert "formal training fits: 0" in captured.err
    assert "capture profile     : record_eval" in captured.err
    assert "episodes evaluated     : 2" in captured.out
    assert "decision steps         : 6" in captured.out
    assert "frames written         : 0" in captured.out
    assert "frames refused, by reason:" in captured.out
    assert str(tmp_path / "trace") in captured.out


def test_declared_episode_step_cap_is_honoured(
    tmp_path: Path, fake_route: dict[str, Any]
) -> None:
    _complete_inputs(tmp_path)
    _write_episodes(tmp_path / "episodes.json", [{"episode_id": "short", "seed": 3, "max_steps": 1}])
    assert module.record_eval(_args(tmp_path)) == 0
    assert fake_route["policy"].acts == 1


def test_observers_receive_the_checkpoint_provenance(
    tmp_path: Path, fake_route: dict[str, Any]
) -> None:
    _complete_inputs(tmp_path)
    module.record_eval(_args(tmp_path))
    provenance = fake_route["built"]["provenance"]
    identity = provenance["identity"]

    assert provenance["policy_kind"].value == "trained_checkpoint"
    assert identity.sha256 == file_hash(str(tmp_path / "checkpoint.pt"))
    observer_kwargs = module._observer_kwargs(
        gate=None, sink=None, writer=None, trace_id=provenance["trace_id"],
        identity=identity, policy_kind=provenance["policy_kind"],
    )
    assert observer_kwargs["source_kind"].value == "checkpoint_evaluation"
    assert observer_kwargs["checkpoint_identity"] == identity.label


def test_the_real_route_observers_accept_the_checkpoint_provenance(tmp_path: Path) -> None:
    """Guards the wiring without an environment: the shipped observers take these kwargs."""

    from tools.research_support.capture.legacy_uav import LegacyRelayObserver
    from tools.research_support.capture.profiles import CaptureConfig, CaptureGate, Profile
    from tools.research_support.capture.service_restoration import ServiceRestorationObserver
    from tools.research_support.capture.transport import NullSink

    path = _write_checkpoint(tmp_path / "checkpoint.pt", _valid_payload())
    identity = module.checkpoint_identity(path, _valid_payload())
    gate = CaptureGate(CaptureConfig(profile=Profile.RECORD_EVAL))
    provenance = module._observer_kwargs(
        gate=gate, sink=NullSink(), writer=None, trace_id="t",
        identity=identity, policy_kind=module.policy_kind_for(identity),
    )
    assert ServiceRestorationObserver(**provenance).emitted == 0
    assert LegacyRelayObserver(scenario="base", **provenance).emitted == 0


def test_a_non_empty_trace_directory_is_never_overwritten(
    tmp_path: Path, fake_route: dict[str, Any]
) -> None:
    _complete_inputs(tmp_path)
    existing = tmp_path / "trace"
    existing.mkdir()
    (existing / "trace_manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(CliError) as error:
        module.record_eval(_args(tmp_path))
    assert "non-empty directory" in str(error.value)
    assert (existing / "trace_manifest.json").read_text(encoding="utf-8") == "{}"


# --------------------------------------------------------------------------------------
# The real route, without a trained model
# --------------------------------------------------------------------------------------


_SMOKE_CONFIG = Path(__file__).resolve().parents[3] / "configs/uav_service_restoration/smoke_fixture.json"


@pytest.fixture()
def real_runtime():
    """The shipped service-restoration environment with the shipped observer attached."""

    if not _SMOKE_CONFIG.is_file():
        pytest.skip(f"environment configuration not present in this checkout: {_SMOKE_CONFIG}")
    from tools.research_support.capture.profiles import CaptureConfig, CaptureGate, Profile
    from tools.research_support.capture.transport import NullSink

    setup = module._setup_service_restoration(_SMOKE_CONFIG)
    identity = module.CheckpointIdentity(
        path=Path("unwritten/final.pt"), sha256="sha256:0", size_bytes=1,
        mtime_utc="1970-01-01T00:00:00+00:00", fields={},
    )
    runtime = setup.build(
        seed=3,
        gate=CaptureGate(CaptureConfig(profile=Profile.RECORD_EVAL)),
        sink=NullSink(),
        writer=None,
        trace_id="real",
        identity=identity,
        policy_kind=module.policy_kind_for(identity),
    )
    try:
        yield setup, runtime
    finally:
        runtime.close()


def test_the_real_route_attaches_the_shipped_observer(real_runtime) -> None:
    setup, runtime = real_runtime
    assert setup.environment_id == "uav_service_restoration_v0"
    assert runtime.env.env.capture_observer is runtime.observer
    # The dimensions the declared agent builder reads are all present on the adapter.
    for name in ("n_uavs", "obs_dim", "action_dim", "state_dim"):
        assert int(getattr(runtime.env, name)) > 0


def test_a_checkpoint_for_another_fleet_size_is_refused(real_runtime, tmp_path: Path) -> None:
    _setup, runtime = real_runtime
    payload = _valid_payload(n_agents=int(runtime.env.n_uavs) + 7)
    with pytest.raises(CliError) as error:
        module._build_process_core_policy(
            payload=payload,
            checkpoint_path=_write_checkpoint(tmp_path / "checkpoint.pt", payload),
            env=runtime.env,
            device="cpu",
        )
    message = str(error.value)
    assert f"n_agents={payload['n_agents']}" in message
    assert "does not reshape a checkpoint" in message


def test_a_mismatched_state_dict_is_refused_not_partially_loaded(
    real_runtime, tmp_path: Path
) -> None:
    """The declared loader loads strictly; a partial fit is a refusal, not a warm start."""

    _setup, runtime = real_runtime
    payload = _valid_payload(n_agents=int(runtime.env.n_uavs))
    with pytest.raises(CliError) as error:
        module._build_process_core_policy(
            payload=payload,
            checkpoint_path=_write_checkpoint(tmp_path / "checkpoint.pt", payload),
            env=runtime.env,
            device="cpu",
        )
    message = str(error.value)
    assert "state_dict" in message
    assert "second loader family" in message


def test_the_cli_subcommand_reaches_this_module(tmp_path: Path, refusing_route: None) -> None:
    """The lazily imported name in cli.cmd_record_eval resolves, and CliError exits 2."""

    from tools.research_support import cli

    _complete_inputs(tmp_path)
    (tmp_path / "checkpoint.pt").unlink()
    argv = [
        "record-eval",
        "--route", "service-restoration",
        "--checkpoint", str(tmp_path / "checkpoint.pt"),
        "--config", str(tmp_path / "env.json"),
        "--episodes-file", str(tmp_path / "episodes.json"),
        "--trace-output", str(tmp_path / "trace"),
    ]
    assert cli.main(argv) == 2
    assert not (tmp_path / "trace").exists()
