from __future__ import annotations

import asyncio
import json
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.codex_supervisor.helpers import (
    make_observer_config,
    record_completed_agent_item,
    write_fake_codex,
)
from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors, seed_reanchor
from tools.codex_semantic_mvp.actor_registry import release_actor_context
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.command_gateway import CommandGateway, CommandGatewayError
from tools.codex_supervisor.durability.effects import EffectJournal
from tools.codex_supervisor.host_control import _dispatch_mailbox_mutation
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.mailbox_store import MailboxStore
from tools.codex_supervisor.managed_models import (
    BindingState,
    HistoryTrust,
    ThreadOrigin,
)
from tools.codex_supervisor.provisioning import ManagedProvisioner, ProvisioningError
from tools.codex_supervisor.runtime_profiles import CommandKind
from tools.codex_supervisor.scheduler_leases import SchedulerLeases
from tools.codex_supervisor.semantic_scanner import SemanticScanner
from tools.codex_supervisor.transport import AppServerTransport
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.wake_scheduler import WakeScheduler, WakeSchedulerError


def _close_seeded(seeded) -> None:
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def _prepared_wake(seeded, *, key: str, holder: str):
    binding_id = str(seeded["portfolio_binding_id"])
    actor_id = seeded["portfolio"].actor_context_id
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key=key,
        target_actor_context_id=actor_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="wake-subject",
        payload_ref="wake-payload",
    )
    mailbox.mark_eligible(message.message_id)
    batches = WakeBatchStore(seeded["supervisor"], mailbox)
    leases = SchedulerLeases(seeded["supervisor"])
    lease = leases.acquire(binding_id, holder)
    batch = batches.prepare(
        binding_id=binding_id,
        thread_id="thr_port",
        snapshot=seeded["bridge"].snapshot(actor_id),
        messages=[message],
        lease_generation=int(lease["generation"]),
        lease_holder=holder,
    )
    return binding_id, message, batches, leases, lease, batch


def test_guarded_wake_ineligibility_suspends_and_cancels_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        binding_id, message, batches, leases, lease, batch = _prepared_wake(
            seeded, key="review05:f02", holder="review05-f02"
        )
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "f02.err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        from tools.codex_supervisor.durability.session_owner import AppServerSessionOwner

        owner = AppServerSessionOwner.for_client(client, seeded["supervisor"])
        original = owner.submit_wake_batch

        async def release_then_submit(*args, **kwargs):
            release_actor_context(
                seeded["semantic"], seeded["portfolio"].actor_context_id
            )
            return await original(*args, **kwargs)

        monkeypatch.setattr(owner, "submit_wake_batch", release_then_submit)
        scheduler = WakeScheduler(
            seeded["bindings"],
            seeded["mailbox"],
            batches,
            leases,
            WakeRecovery(seeded["bindings"], seeded["mailbox"], batches, client),
            SemanticScanner(seeded["mailbox"], seeded["bridge"]),
            seeded["bridge"],
            client,
            instance_id="review05-f02",
        )
        with pytest.raises(WakeSchedulerError, match="ACTIVE"):
            await scheduler.submit_batch(
                str(batch["wake_batch_id"]),
                lease_generation=int(lease["generation"]),
            )
        assert seeded["bindings"].get(binding_id).binding_state is BindingState.SUSPENDED
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "CANCELLED"
        assert seeded["mailbox"].get(message.message_id).delivery_state.value == "ELIGIBLE"
        assert EffectJournal(seeded["supervisor"].connection).get(
            str(batch["effect_id"])
        ).state == "CANCELLED_BEFORE_WRITE"
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (batch["effect_id"],)
        ).fetchone()[0] == 0
        await transport.stop()
        _close_seeded(seeded)

    asyncio.run(body())


def test_verification_binding_rejects_mailbox_action_before_any_mailbox_effect(
    tmp_path: Path,
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bindings = BindingStore(seeded["supervisor"], seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = bindings.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    bindings.attach_thread_for_tests(binding_id, "thr_verification")
    bindings.mark_verification_required(binding_id)
    payload = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "MAILBOX_ACK",
        "expected": {
            "checkpoint_id": snapshot.checkpoint_id,
            "state_version": snapshot.state_version,
            "epoch_id": snapshot.epoch_id,
            "epoch_revision": snapshot.epoch_revision,
        },
        "payload": {"message_ids": ["msg_never"]},
    }
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_verification",
        turn_id="turn_verification",
        item_id="item_verification",
        text=(
            "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
            + json.dumps(payload)
            + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
        ),
    )
    with pytest.raises(CommandGatewayError, match="VERIFICATION_REQUIRED"):
        CommandGateway(
            bindings, seeded["bridge"], MailboxStore(seeded["supervisor"])
        ).ingest_final_item(raw_message_seq=seq)
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_command_receipts"
    ).fetchone()[0] == 0
    assert bindings.get(binding_id).binding_state is BindingState.VERIFICATION_REQUIRED
    _close_seeded(seeded)


def test_active_binding_flip_between_semantic_guard_and_mailbox_tx_has_zero_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    bindings = seeded["bindings"]
    binding_id = str(seeded["root_binding_id"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    mailbox = seeded["mailbox"]
    message = mailbox.enqueue(
        source_system=MailboxSourceSystem.OPERATOR.value,
        source_event_key="review05:f03-race",
        target_actor_context_id=seeded["root"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="subject",
        payload_ref="payload",
    )
    mailbox.mark_eligible(message.message_id)
    mailbox.mark_batched(message.message_id)
    mailbox.mark_delivered(message.message_id)
    payload = {
        "schema_version": "1.0",
        "packet_kind": "MANAGED_ACTOR_COMMAND",
        "action_kind": "MAILBOX_ACK",
        "expected": {
            "checkpoint_id": snapshot.checkpoint_id,
            "state_version": snapshot.state_version,
            "epoch_id": snapshot.epoch_id,
            "epoch_revision": snapshot.epoch_revision,
        },
        "payload": {"message_ids": [message.message_id]},
    }
    seq = record_completed_agent_item(
        seeded["supervisor"],
        thread_id="thr_root",
        turn_id="turn_f03_race",
        item_id="item_f03_race",
        text=(
            "<HMASD_MANAGED_ACTOR_COMMAND_V1>\n"
            + json.dumps(payload)
            + "\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
        ),
    )
    original_guard = seeded["bridge"].currentness_guard

    @contextmanager
    def flip_before_supervisor_tx(*args, **kwargs):
        with original_guard(*args, **kwargs) as guarded:
            bindings.suspend(binding_id)
            yield guarded

    monkeypatch.setattr(seeded["bridge"], "currentness_guard", flip_before_supervisor_tx)
    with pytest.raises(CommandGatewayError, match="ACTIVE"):
        CommandGateway(bindings, seeded["bridge"], mailbox).ingest_final_item(
            raw_message_seq=seq
        )
    assert mailbox.get(message.message_id).intake_state.value == "NOT_ACKNOWLEDGED"
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_command_receipts WHERE message_id = ?",
        (message.message_id,),
    ).fetchone()[0] == 0
    _close_seeded(seeded)


def test_semantic_scanner_failure_rolls_back_messages_and_cursor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_managed_actors(tmp_path)
    seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    scanner = SemanticScanner(MailboxStore(seeded["supervisor"]), seeded["bridge"])

    def fail_cursor(**_fields):
        raise RuntimeError("scanner failpoint")

    monkeypatch.setattr(scanner, "_write_cursor", fail_cursor)
    with pytest.raises(RuntimeError, match="failpoint"):
        scanner.scan()
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_messages"
    ).fetchone()[0] == 0
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM semantic_scan_cursors"
    ).fetchone()[0] == 0
    _close_seeded(seeded)


def test_mailbox_enqueue_target_flip_after_semantic_snapshot_has_zero_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    target_binding_id = str(seeded["portfolio_binding_id"])
    original_guard = seeded["bridge"].actor_pair_guard

    @contextmanager
    def flip_before_supervisor_tx(*args, **kwargs):
        with original_guard(*args, **kwargs) as pair:
            seeded["bindings"].suspend(target_binding_id)
            yield pair

    monkeypatch.setattr(seeded["bridge"], "actor_pair_guard", flip_before_supervisor_tx)
    request = SimpleNamespace(
        command=CommandKind.MAILBOX_ENQUEUE,
        operator="operator",
        arguments={
            "source_actor_context_id": seeded["root"].actor_context_id,
            "target_actor_context_id": seeded["portfolio"].actor_context_id,
            "message_kind": MailboxMessageKind.ROOT_TO_PORTFOLIO_REVIEW.value,
            "subject_ref": "subject",
            "payload_ref": "payload",
            "priority": 1,
            "source_event_key": "review05:f05",
        },
    )
    with pytest.raises(ValueError, match="ACTIVE"):
        asyncio.run(
            _dispatch_mailbox_mutation(
                request,
                bindings=seeded["bindings"],
                bridge=seeded["bridge"],
                client=object(),
            )
        )
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM mailbox_messages WHERE source_event_key = 'review05:f05'"
    ).fetchone()[0] == 0
    _close_seeded(seeded)


def test_provisioning_drift_cancels_binding_and_effect_before_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bindings = BindingStore(seeded["supervisor"], seeded["bridge"])
    provisioner = ManagedProvisioner(bindings, object())  # type: ignore[arg-type]
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = provisioner.prepare(snapshot, repo_root=tmp_path, operator="operator")
    original = provisioner._assert_provision_fence
    calls = {"count": 0}

    def drift_on_second(binding, *, effect_id=None):
        calls["count"] += 1
        if calls["count"] == 2:
            with seeded["semantic"]._lock, seeded["semantic"].connection:
                seeded["semantic"].connection.execute(
                    "UPDATE workflows SET state_version = state_version + 1 WHERE actor_context_id = ?",
                    (seeded["root"].actor_context_id,),
                )
        return original(binding, effect_id=effect_id)

    monkeypatch.setattr(provisioner, "_assert_provision_fence", drift_on_second)
    with pytest.raises(ProvisioningError, match="currentness"):
        asyncio.run(provisioner.create_fresh_thread(binding_id))
    binding = bindings.get(binding_id)
    assert binding is not None and binding.binding_state is BindingState.REVOKED
    effect = EffectJournal(seeded["supervisor"].connection).get_by_key(
        "thread/start", f"thread/start:{binding_id}"
    )
    assert effect is not None and effect.state == "CANCELLED_BEFORE_WRITE"
    assert seeded["supervisor"].connection.execute(
        "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (effect.effect_id,)
    ).fetchone()[0] == 0
    _close_seeded(seeded)


def test_wake_resume_context_drift_cancels_resume_and_wake_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def body() -> None:
        seeded = seed_active_root_portfolio(tmp_path)
        binding_id, message, batches, leases, _lease, batch = _prepared_wake(
            seeded, key="review05:f07", holder="review05-f07"
        )
        config = make_observer_config(tmp_path)
        transport = AppServerTransport(
            write_fake_codex(tmp_path),
            config,
            tmp_path,
            tmp_path / "f07.err.log",
            extra_env={"FAKE_APP_SERVER_MODE": "handshake_ok"},
            stdin_close_timeout=0.4,
            terminate_timeout=0.4,
        )
        client = AppServerClient(transport, config)
        await transport.start()
        await client.initialize()
        from tools.codex_supervisor.durability.session_owner import AppServerSessionOwner

        owner = AppServerSessionOwner.for_client(client, seeded["supervisor"])
        original = owner.submit_thread_resume

        async def drift_then_submit(*args, **kwargs):
            with seeded["semantic"]._lock, seeded["semantic"].connection:
                seeded["semantic"].connection.execute(
                    "UPDATE workflows SET state_version = state_version + 1 WHERE actor_context_id = ?",
                    (seeded["portfolio"].actor_context_id,),
                )
            return await original(*args, **kwargs)

        monkeypatch.setattr(owner, "submit_thread_resume", drift_then_submit)
        recovery = WakeRecovery(
            seeded["bindings"],
            seeded["mailbox"],
            batches,
            client,
            leases,
            "review05-f07",
            bridge=seeded["bridge"],
        )
        readiness = await recovery.resume_once(
            binding_id, wake_batch_id=str(batch["wake_batch_id"])
        )
        assert readiness.value == "UNKNOWN"
        resume = EffectJournal(seeded["supervisor"].connection).get_by_key(
            "thread/resume", f"thread/resume:thr_port:{batch['wake_batch_id']}"
        )
        assert resume is not None and resume.state == "CANCELLED_BEFORE_WRITE"
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "CANCELLED"
        assert seeded["mailbox"].get(message.message_id).delivery_state.value == "ELIGIBLE"
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (resume.effect_id,)
        ).fetchone()[0] == 0
        await transport.stop()
        _close_seeded(seeded)

    asyncio.run(body())


def test_canary_preflight_rejects_same_or_repo_runtime_before_python(
    repo_root: Path,
    tmp_path: Path,
) -> None:
    script = repo_root / "scripts" / "codex-app-server-observer-canary.ps1"
    missing_python = tmp_path / "python-must-not-run.exe"
    external = Path(os.environ["LOCALAPPDATA"]) / "HMASD" / f"review05-{tmp_path.name}"
    normal = external / "normal"
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(script),
        "-RepoRoot",
        str(repo_root),
        "-PythonExecutable",
        str(missing_python),
        "-RuntimeHome",
        str(normal),
        "-NormalRuntimeHome",
        str(normal),
    ]
    same = subprocess.run(command, text=True, capture_output=True, check=False)
    assert same.returncode != 0
    assert "must differ" in (same.stdout + same.stderr)
    command[command.index(str(normal))] = str(repo_root / "runtime-canary")
    inside = subprocess.run(command, text=True, capture_output=True, check=False)
    assert inside.returncode != 0
    assert "external to the repository" in (inside.stdout + inside.stderr)


def test_canary_stopped_preflight_does_not_launch_python(
    repo_root: Path,
    tmp_path: Path,
) -> None:
    script = repo_root / "scripts" / "codex-app-server-observer-canary.ps1"
    external = Path(os.environ["LOCALAPPDATA"]) / "HMASD" / f"review05-{tmp_path.name}"
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(script),
            "-RepoRoot",
            str(repo_root),
            "-PythonExecutable",
            str(tmp_path / "python-must-not-run.exe"),
            "-RuntimeHome",
            str(external / "canary"),
            "-NormalRuntimeHome",
            str(external / "normal"),
            "-StatusPreflightOnly",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
