from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import tools.codex_supervisor.host_control as host_control_module
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.host_control import (
    CONTROL_REQUEST_SCHEMA,
    CONTROL_RESPONSE_SCHEMA,
    HostControlChannel,
    HostControlConflictError,
    HostControlRequest,
    HostControlResponse,
    HostControlValidationError,
    parse_request,
)
from tools.codex_supervisor.runtime_profiles import (
    CommandKind,
    ProfileError,
    RuntimeProfile,
    require_command_allowed,
)
from tools.codex_supervisor.provisioning import ManagedProvisioner
from tools.codex_supervisor.store import ObserverStore
from tools.codex_semantic_mvp.store import SemanticStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request(request_id: str, command: CommandKind = CommandKind.STATUS, **arguments: object):
    return HostControlRequest(
        schema=CONTROL_REQUEST_SCHEMA,
        request_id=request_id,
        created_at=_now(),
        operator="operator:test",
        command=command,
        arguments=arguments,
    )


def _response(request_id: str) -> HostControlResponse:
    return HostControlResponse(
        schema=CONTROL_RESPONSE_SCHEMA,
        request_id=request_id,
        status="OK",
        payload={"ready": True},
        error=None,
        completed_at=_now(),
    )


def _channel(
    control_home: Path,
    *,
    profile: RuntimeProfile = RuntimeProfile.OBSERVER,
    repo_root: Path | None = None,
    semantic_state_path: Path | None = None,
    **kwargs: object,
) -> HostControlChannel:
    base = control_home.parent if control_home.name == "control" else control_home
    canonical_repo = repo_root or base / "repo"
    canonical_repo.mkdir(parents=True, exist_ok=True)
    if profile is not RuntimeProfile.OBSERVER and semantic_state_path is None:
        semantic_state_path = base / "semantic.sqlite3"
        semantic = SemanticStore(semantic_state_path).initialize()
        semantic.close()
    return HostControlChannel(
        control_home,
        profile=profile,
        repo_root=canonical_repo,
        semantic_state_path=semantic_state_path,
        **kwargs,
    )


def test_duplicate_request_returns_existing_response(tmp_path: Path) -> None:
    channel = _channel(tmp_path)
    request = _request("req-1")
    channel.submit(request)
    channel.write_response(_response("req-1"))
    assert channel.submit(request).request_id == "req-1"
    response = channel.response("req-1")
    assert response is not None and response.status == "OK"


def test_duplicate_request_conflict_is_rejected(tmp_path: Path) -> None:
    channel = _channel(tmp_path)
    channel.submit(_request("req-1"))
    conflict = _request("req-1", CommandKind.INSPECT, thread_id="thr-x")
    with pytest.raises(HostControlConflictError):
        channel.submit(conflict)
    assert list(channel.rejected.glob("req-1.conflict.*.json"))


def test_observer_profile_rejects_managed_turn(tmp_path: Path) -> None:
    request = _request(
        "req-managed",
        CommandKind.MANAGED_TURN,
        binding_id="binding-x",
        text="test",
    )
    with pytest.raises(ProfileError):
        require_command_allowed(RuntimeProfile.OBSERVER, request.command)


def test_channel_configuration_fail_closes_semantic_state_authority(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    external_state = tmp_path / "semantic.sqlite3"
    external_semantic = SemanticStore(external_state).initialize()
    external_semantic.close()
    resident_state = repo / "semantic.sqlite3"
    resident_semantic = SemanticStore(resident_state).initialize()
    resident_semantic.close()

    with pytest.raises(HostControlValidationError, match="requires"):
        HostControlChannel(
            tmp_path / "missing",
            profile=RuntimeProfile.MANAGED_MANUAL,
            repo_root=repo,
        )
    with pytest.raises(HostControlValidationError, match="existing regular file"):
        HostControlChannel(
            tmp_path / "missing-file",
            profile=RuntimeProfile.MANAGED_MANUAL,
            repo_root=repo,
            semantic_state_path=tmp_path / "absent.sqlite3",
        )
    with pytest.raises(HostControlValidationError, match="external"):
        HostControlChannel(
            tmp_path / "resident",
            profile=RuntimeProfile.MAILBOX_MANUAL,
            repo_root=repo,
            semantic_state_path=resident_state,
        )
    with pytest.raises(HostControlValidationError, match="forbids"):
        HostControlChannel(
            tmp_path / "observer-state",
            profile=RuntimeProfile.OBSERVER,
            repo_root=repo,
            semantic_state_path=external_state,
        )

    channel = HostControlChannel(
        tmp_path / "valid",
        profile=RuntimeProfile.SINGLE_WAKE,
        repo_root=repo,
        semantic_state_path=external_state,
    )
    assert channel.repo_root == repo.resolve()
    assert channel.semantic_state_path == external_state.resolve()


def test_claim_is_atomic_and_retains_durable_request(tmp_path: Path) -> None:
    channel = _channel(tmp_path)
    request = _request("req-claim")
    channel.submit(request)
    assert channel.claim_next() == request
    assert channel.claim_next() is None
    assert (channel.processing / "req-claim.json").exists()


def test_malformed_and_stale_requests_move_to_rejected(tmp_path: Path) -> None:
    channel = _channel(tmp_path, max_request_age_seconds=1)
    (channel.inbox / "malformed.json").write_text("{", encoding="utf-8")
    stale = replace(
        _request("stale"),
        created_at=(datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
    )
    channel.submit(stale)
    assert channel.claim_next() is None
    assert (channel.rejected / "malformed.json").exists()
    assert (channel.rejected / "stale.json").exists()


def test_request_parser_rejects_extra_fields_and_unsafe_ids() -> None:
    payload = _request("req-safe").to_dict()
    payload["extra"] = True
    with pytest.raises(HostControlValidationError):
        parse_request(payload)
    with pytest.raises(HostControlValidationError):
        _request("../escape")


def test_stop_claim_priority_ignores_filename_order_and_leaves_later_mutation_unclaimed(
    tmp_path: Path,
) -> None:
    async def body() -> None:
        channel = _channel(
            tmp_path / "control",
            profile=RuntimeProfile.MANAGED_MANUAL,
            poll_interval_seconds=0.01,
        )
        channel.submit(_request("z-stop", CommandKind.STOP))
        channel.submit(
            _request(
                "a-later-mutation",
                CommandKind.MANAGED_TURN,
                snapshot={},
                binding_id="binding-x",
                text="must not run",
            )
        )
        store = ObserverStore(tmp_path / "runtime")
        service = SimpleNamespace(store=store, run_id="run-1", client=object(), transport=None, _stopped=False)
        stop_event = asyncio.Event()
        await channel.serve(
            profile=RuntimeProfile.MANAGED_MANUAL,
            service=service,
            stop_event=stop_event,
        )
        response = channel.response("z-stop")
        assert response is not None and response.status == "OK"
        assert stop_event.is_set()
        assert (channel.inbox / "a-later-mutation.json").exists()
        assert channel.response("a-later-mutation") is None
        store.close()

    asyncio.run(body())


def test_stop_published_during_mutation_claim_preempts_and_requeues_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    channel = _channel(tmp_path / "control", profile=RuntimeProfile.MANAGED_MANUAL)
    mutation = _request(
        "a-mutation",
        CommandKind.MANAGED_TURN,
        snapshot={},
        binding_id="binding-x",
        text="must remain unclaimed",
    )
    stop = _request("z-stop", CommandKind.STOP)
    channel.submit(mutation)
    original_replace = host_control_module.os.replace
    injected = False

    def replace_with_stop(source: object, destination: object) -> None:
        nonlocal injected
        if (
            not injected
            and Path(source) == channel.inbox / "a-mutation.json"
            and Path(destination) == channel.processing / "a-mutation.json"
        ):
            injected = True
            channel.submit(stop)
        original_replace(source, destination)

    monkeypatch.setattr(host_control_module.os, "replace", replace_with_stop)

    assert channel.claim_next() == stop
    assert injected
    assert (channel.processing / "z-stop.json").exists()
    assert (channel.inbox / "a-mutation.json").exists()
    assert not (channel.processing / "a-mutation.json").exists()


@pytest.mark.parametrize("invalid_stop", ["malformed", "stale"])
def test_invalid_stop_published_during_mutation_claim_does_not_fence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid_stop: str,
) -> None:
    channel = _channel(
        tmp_path / "control",
        profile=RuntimeProfile.MANAGED_MANUAL,
        max_request_age_seconds=1,
    )
    mutation = _request(
        "a-mutation",
        CommandKind.MANAGED_TURN,
        snapshot={},
        binding_id="binding-x",
        text="must be claimed",
    )
    channel.submit(mutation)
    original_replace = host_control_module.os.replace
    injected = False

    def replace_with_invalid_stop(source: object, destination: object) -> None:
        nonlocal injected
        if (
            not injected
            and Path(source) == channel.inbox / "a-mutation.json"
            and Path(destination) == channel.processing / "a-mutation.json"
        ):
            injected = True
            stop = _request("z-stop", CommandKind.STOP)
            if invalid_stop == "stale":
                stop = replace(
                    stop,
                    created_at=(
                        datetime.now(timezone.utc) - timedelta(minutes=5)
                    ).isoformat(),
                )
                channel.submit(stop)
            else:
                payload = stop.to_dict()
                payload["unexpected"] = True
                (channel.inbox / "z-stop.json").write_text(
                    json.dumps(payload), encoding="utf-8"
                )
        original_replace(source, destination)

    monkeypatch.setattr(
        host_control_module.os,
        "replace",
        replace_with_invalid_stop,
    )

    assert channel.claim_next() == mutation
    assert injected
    assert (channel.processing / "a-mutation.json").exists()
    assert not (channel.inbox / "z-stop.json").exists()
    assert (channel.rejected / "z-stop.json").exists()


def test_single_wake_is_typed_not_implemented_and_does_not_arm(tmp_path: Path) -> None:
    async def body() -> None:
        channel = _channel(tmp_path / "control", profile=RuntimeProfile.SINGLE_WAKE)
        store = ObserverStore(tmp_path / "runtime")
        service = SimpleNamespace(store=store, run_id="run-1", client=object(), transport=None, _stopped=False)
        response = await channel.dispatch(
            _request("arm", CommandKind.ARM_SINGLE_WAKE),
            profile=RuntimeProfile.SINGLE_WAKE,
            service=service,
            stop_event=asyncio.Event(),
        )
        assert response.status == "NOT_IMPLEMENTED"
        assert response.payload == {"armed": False, "implemented": False}
        store.close()

    asyncio.run(body())


def test_status_distinguishes_host_and_app_server_child_processes(
    tmp_path: Path,
) -> None:
    async def body() -> None:
        channel = _channel(tmp_path / "control")
        store = ObserverStore(tmp_path / "runtime")
        service = SimpleNamespace(
            store=store,
            run_id="run-status",
            transport=SimpleNamespace(process_id=8123),
            _stopped=False,
        )
        response = await channel.dispatch(
            _request("status"),
            profile=RuntimeProfile.OBSERVER,
            service=service,
            stop_event=asyncio.Event(),
        )
        assert response.payload["host_process_id"] == host_control_module.os.getpid()
        assert response.payload["app_server_child_process_id"] == 8123
        assert "process_id" not in response.payload
        store.close()

    asyncio.run(body())


def test_response_json_is_strict_and_atomic(tmp_path: Path) -> None:
    channel = _channel(tmp_path)
    channel.submit(_request("response"))
    channel.write_response(_response("response"))
    payload = json.loads((channel.outbox / "response.json").read_text(encoding="utf-8"))
    assert set(payload) == {
        "schema",
        "request_id",
        "status",
        "payload",
        "error",
        "completed_at",
    }


def test_restart_does_not_resend_claimed_mutation(tmp_path: Path) -> None:
    first = _channel(tmp_path / "control", profile=RuntimeProfile.MANAGED_MANUAL)
    first.submit(
        _request(
            "claimed-turn",
            CommandKind.MANAGED_TURN,
            snapshot={},
            binding_id="binding-x",
            text="must not resend",
        )
    )
    assert first.claim_next() is not None

    async def body() -> None:
        restarted = _channel(tmp_path / "control", profile=RuntimeProfile.MANAGED_MANUAL)
        store = ObserverStore(tmp_path / "runtime")
        service = SimpleNamespace(
            store=store,
            run_id="run-restarted",
            client=object(),
            transport=None,
            _stopped=False,
        )
        stop_event = asyncio.Event()
        task = asyncio.create_task(
            restarted.serve(
                profile=RuntimeProfile.MANAGED_MANUAL,
                service=service,
                stop_event=stop_event,
            )
        )
        for _ in range(100):
            response = restarted.response("claimed-turn")
            if response is not None:
                break
            await asyncio.sleep(0.01)
        else:
            raise AssertionError("restarted host did not reconcile claimed request")
        stop_event.set()
        await task
        assert response.status == "SUBMISSION_UNCERTAIN"
        assert response.payload["recovered_processing_request"] is True
        store.close()

    asyncio.run(body())


@pytest.mark.parametrize(
    ("selector", "response_key", "expected_type"),
    [
        ({"thread_id": "thr-none"}, "thread", dict),
        ({"binding_id": "bind-none"}, "binding", list),
        ({"target_actor_context_id": "actor-none"}, "mailbox", list),
        ({"wake_batch_id": "wake-none"}, "wake", list),
    ],
)
def test_inspect_selectors_return_json_payloads(
    tmp_path: Path,
    selector: dict[str, object],
    response_key: str,
    expected_type: type,
) -> None:
    async def body() -> None:
        channel = _channel(tmp_path / "control")
        store = ObserverStore(tmp_path / "runtime")
        service = SimpleNamespace(store=store, run_id="run-inspect", transport=None, _stopped=False)
        response = await channel.dispatch(
            _request("inspect", CommandKind.INSPECT, **selector),
            profile=RuntimeProfile.OBSERVER,
            service=service,
            stop_event=asyncio.Event(),
        )
        assert response.status == "OK"
        assert isinstance(response.payload[response_key], expected_type)
        store.close()

    asyncio.run(body())


def test_managed_create_derives_snapshot_from_actor_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_managed_actors(tmp_path)

    async def fake_create(self, binding_id: str) -> str:
        return "thr-derived"

    monkeypatch.setattr(ManagedProvisioner, "create_fresh_thread", fake_create)

    async def body() -> None:
        channel = _channel(
            tmp_path / "control",
            profile=RuntimeProfile.MANAGED_MANUAL,
            semantic_state_path=tmp_path / "semantic.sqlite3",
        )
        service = SimpleNamespace(
            store=seeded["supervisor"],
            run_id="run-managed",
            client=object(),
            transport=None,
            _stopped=False,
        )
        root = seeded["root"]
        response = await channel.dispatch(
            _request(
                "create-derived",
                CommandKind.MANAGED_CREATE,
                actor_context_id=root.actor_context_id,
                confirm_global_memory_disabled=True,
            ),
            profile=RuntimeProfile.MANAGED_MANUAL,
            service=service,
            stop_event=asyncio.Event(),
        )
        binding = BindingStore(seeded["supervisor"]).get(str(response.payload["binding_id"]))
        assert binding is not None
        assert binding.actor_context_id == root.actor_context_id
        assert binding.actor_kind.value == "OPERATIONAL_ROOT"

    try:
        asyncio.run(body())
    finally:
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()


def test_managed_contract_rejects_caller_snapshot_and_nonmanaged_actor(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)

    async def body() -> None:
        channel = _channel(
            tmp_path / "control",
            profile=RuntimeProfile.MANAGED_MANUAL,
            semantic_state_path=tmp_path / "semantic.sqlite3",
        )
        service = SimpleNamespace(
            store=seeded["supervisor"], run_id="run", client=object(), transport=None, _stopped=False
        )
        root = seeded["root"]
        with pytest.raises(HostControlValidationError, match="snapshot"):
            await channel.dispatch(
                _request(
                    "caller-snapshot",
                    CommandKind.MANAGED_CREATE,
                    actor_context_id=root.actor_context_id,
                    confirm_global_memory_disabled=True,
                    snapshot={"capsule_text": "caller-controlled"},
                ),
                profile=RuntimeProfile.MANAGED_MANUAL,
                service=service,
                stop_event=asyncio.Event(),
            )
        with pytest.raises(HostControlValidationError, match="only OPERATIONAL_ROOT"):
            await channel.dispatch(
                _request(
                    "em-create",
                    CommandKind.MANAGED_CREATE,
                    actor_context_id=seeded["em"].actor_context_id,
                    confirm_global_memory_disabled=True,
                ),
                profile=RuntimeProfile.MANAGED_MANUAL,
                service=service,
                stop_event=asyncio.Event(),
            )

    try:
        asyncio.run(body())
    finally:
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()


@pytest.mark.parametrize("extra_field", ["semantic_state", "repo_root"])
def test_managed_request_cannot_select_launch_authority(
    tmp_path: Path,
    extra_field: str,
) -> None:
    seeded = seed_managed_actors(tmp_path)

    async def body() -> None:
        channel = _channel(
            tmp_path / "control",
            profile=RuntimeProfile.MANAGED_MANUAL,
            semantic_state_path=tmp_path / "semantic.sqlite3",
        )
        service = SimpleNamespace(
            store=seeded["supervisor"],
            run_id="run",
            client=object(),
            transport=None,
            _stopped=False,
        )
        arguments: dict[str, object] = {
            "actor_context_id": seeded["root"].actor_context_id,
            "confirm_global_memory_disabled": True,
            extra_field: str(tmp_path / "caller-selected"),
        }
        with pytest.raises(HostControlValidationError, match="extra"):
            await channel.dispatch(
                _request("caller-authority", CommandKind.MANAGED_CREATE, **arguments),
                profile=RuntimeProfile.MANAGED_MANUAL,
                service=service,
                stop_event=asyncio.Event(),
            )

    try:
        asyncio.run(body())
    finally:
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()


def test_binding_commands_fail_closed_for_unknown_and_mismatched_binding(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    bindings = BindingStore(seeded["supervisor"], seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = ManagedProvisioner(bindings).prepare(
        snapshot, repo_root=tmp_path / "repo", operator="operator:test"
    )
    seeded["supervisor"].connection.execute(
        "UPDATE managed_actor_bindings SET semantic_scope_key = 'spoofed' WHERE binding_id = ?",
        (binding_id,),
    )
    seeded["supervisor"].connection.commit()

    async def body() -> None:
        channel = _channel(
            tmp_path / "control",
            profile=RuntimeProfile.MAILBOX_MANUAL,
            semantic_state_path=tmp_path / "semantic.sqlite3",
        )
        service = SimpleNamespace(
            store=seeded["supervisor"], run_id="run", client=object(), transport=None, _stopped=False
        )
        for request_id, candidate in (("unknown", "bind-unknown"), ("mismatch", binding_id)):
            with pytest.raises(HostControlValidationError):
                await channel.dispatch(
                    _request(
                        request_id,
                        CommandKind.MANAGED_SUSPEND,
                        binding_id=candidate,
                    ),
                    profile=RuntimeProfile.MAILBOX_MANUAL,
                    service=service,
                    stop_event=asyncio.Event(),
                )

    try:
        asyncio.run(body())
    finally:
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()


def test_root_to_portfolio_canary_contract_derives_bindings_and_is_acl_eligible(
    tmp_path: Path,
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    bindings = seeded["bindings"]
    mailbox = seeded["mailbox"]

    async def body() -> None:
        channel = _channel(
            tmp_path / "control",
            profile=RuntimeProfile.MAILBOX_MANUAL,
            semantic_state_path=tmp_path / "semantic.sqlite3",
        )
        service = SimpleNamespace(
            store=seeded["supervisor"], run_id="run", client=object(), transport=None, _stopped=False
        )
        response = await channel.dispatch(
            _request(
                "mail-derived",
                CommandKind.MAILBOX_ENQUEUE,
                source_actor_context_id=seeded["root"].actor_context_id,
                target_actor_context_id=seeded["portfolio"].actor_context_id,
                message_kind="ROOT_TO_PORTFOLIO_REVIEW",
                subject_ref="subject",
                payload_ref="payload",
                priority=20,
            ),
            profile=RuntimeProfile.MAILBOX_MANUAL,
            service=service,
            stop_event=asyncio.Event(),
        )
        message = response.payload["message"]
        assert response.status == "OK"
        assert message["source_system"] == "MANAGED_ACTOR"
        assert message["message_kind"] == "ROOT_TO_PORTFOLIO_REVIEW"
        assert message["sender_actor_context_id"] == seeded["root"].actor_context_id
        assert message["target_actor_context_id"] == seeded["portfolio"].actor_context_id
        root_binding = bindings.binding_for_actor(seeded["root"].actor_context_id)
        portfolio_binding = bindings.binding_for_actor(
            seeded["portfolio"].actor_context_id
        )
        assert root_binding is not None
        assert portfolio_binding is not None
        eligible = mailbox.select_eligible(
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            target_kind=portfolio_binding.actor_kind.value,
            target_binding_state=portfolio_binding.binding_state.value,
            sender_kind_for={
                seeded["root"].actor_context_id: root_binding.actor_kind.value
            },
        )
        assert [item.message_id for item in eligible] == [message["message_id"]]

    try:
        asyncio.run(body())
    finally:
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()


@pytest.mark.parametrize(
    ("command", "profile", "expected_status"),
    [
        (CommandKind.STOP, RuntimeProfile.OBSERVER, "SUBMISSION_UNCERTAIN"),
        (CommandKind.MAILBOX_LIST, RuntimeProfile.MAILBOX_MANUAL, "OK"),
    ],
)
def test_restart_replay_fence_is_exact(
    tmp_path: Path,
    command: CommandKind,
    profile: RuntimeProfile,
    expected_status: str,
) -> None:
    control_home = tmp_path / command.value.lower()
    first = _channel(control_home, profile=profile)
    first.submit(_request("recovered", command))
    assert first.claim_next() is not None
    if command is CommandKind.STOP:
        first.submit(_request("after-stop", CommandKind.STATUS))

    async def body() -> None:
        restarted = _channel(
            control_home,
            profile=profile,
            poll_interval_seconds=0.01,
        )
        store = ObserverStore(tmp_path / f"runtime-{command.value.lower()}")
        service = SimpleNamespace(
            store=store, run_id="new-run", client=object(), transport=None, _stopped=False
        )
        stop_event = asyncio.Event()
        task = asyncio.create_task(
            restarted.serve(profile=profile, service=service, stop_event=stop_event)
        )
        for _ in range(100):
            response = restarted.response("recovered")
            if response is not None:
                break
            await asyncio.sleep(0.01)
        else:
            raise AssertionError("recovered request produced no response")
        assert response.status == expected_status
        if command is CommandKind.STOP:
            assert stop_event.is_set()
        else:
            assert not stop_event.is_set()
            assert not task.done()
            stop_event.set()
        await task
        if command is CommandKind.STOP:
            assert restarted.response("after-stop") is None
        store.close()

    asyncio.run(body())


def test_recovered_stop_preempts_recovered_read_and_mutation(tmp_path: Path) -> None:
    control_home = tmp_path / "recovered-stop-priority"
    first = _channel(control_home, profile=RuntimeProfile.MANAGED_MANUAL)
    requests = (
        _request("a-read", CommandKind.STATUS),
        _request(
            "b-mutation",
            CommandKind.MANAGED_TURN,
            binding_id="binding-never-dispatched",
            text="must not dispatch",
        ),
        _request("z-stop", CommandKind.STOP),
    )
    for request in requests:
        first.submit(request)
        (first.inbox / f"{request.request_id}.json").replace(
            first.processing / f"{request.request_id}.json"
        )

    async def body() -> None:
        restarted = _channel(control_home, profile=RuntimeProfile.MANAGED_MANUAL)
        store = ObserverStore(tmp_path / "runtime-recovered-priority")
        service = SimpleNamespace(
            store=store,
            run_id="run-recovered-priority",
            client=object(),
            transport=None,
            _stopped=False,
        )
        stop_event = asyncio.Event()
        await restarted.serve(
            profile=RuntimeProfile.MANAGED_MANUAL,
            service=service,
            stop_event=stop_event,
        )
        assert stop_event.is_set()
        stop_response = restarted.response("z-stop")
        assert stop_response is not None
        assert stop_response.status == "SUBMISSION_UNCERTAIN"
        assert restarted.response("a-read") is None
        assert restarted.response("b-mutation") is None
        store.close()

    asyncio.run(body())


def test_invalid_recovered_stop_is_rejected_without_suppressing_valid_read(
    tmp_path: Path,
) -> None:
    control_home = tmp_path / "invalid-recovered-stop"
    first = _channel(control_home, profile=RuntimeProfile.OBSERVER)
    read = _request("b-read", CommandKind.STATUS)
    first.submit(read)
    (first.inbox / "b-read.json").replace(first.processing / "b-read.json")
    invalid = _request("a-invalid-stop", CommandKind.STOP).to_dict()
    del invalid["operator"]
    (first.processing / "a-invalid-stop.json").write_text(
        json.dumps(invalid), encoding="utf-8"
    )

    async def body() -> None:
        restarted = _channel(
            control_home,
            profile=RuntimeProfile.OBSERVER,
            poll_interval_seconds=0.01,
        )
        store = ObserverStore(tmp_path / "runtime-invalid-recovered-stop")
        service = SimpleNamespace(
            store=store,
            run_id="run-invalid-stop",
            client=object(),
            transport=None,
            _stopped=False,
        )
        stop_event = asyncio.Event()
        task = asyncio.create_task(
            restarted.serve(
                profile=RuntimeProfile.OBSERVER,
                service=service,
                stop_event=stop_event,
            )
        )
        for _ in range(100):
            response = restarted.response("b-read")
            if response is not None:
                break
            await asyncio.sleep(0.01)
        else:
            raise AssertionError("valid recovered read was suppressed")
        assert response.status == "OK"
        assert list(restarted.rejected.glob("a-invalid-stop.json"))
        assert not stop_event.is_set()
        stop_event.set()
        await task
        store.close()

    asyncio.run(body())
