from pathlib import Path

import pytest

from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingError, BindingStore
from tools.codex_supervisor.command_protocol import extract_managed_command
from tools.codex_supervisor.managed_models import HistoryTrust, MemoryPolicyState, ThreadOrigin
from tools.codex_supervisor.provisioning import ManagedProvisioner, memory_mode_method_supported


def test_host_schema_has_no_memory_mode_method() -> None:
    assert memory_mode_method_supported("") is False
    assert memory_mode_method_supported("thread/start") is False
    assert memory_mode_method_supported("thread/memoryMode/set") is True


def test_operator_confirmation_required(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = store.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    store.attach_thread(binding_id, "thr_mem")
    store.mark_verification_required(binding_id)
    provisioner = ManagedProvisioner(store)
    provisioner.confirm_global_memory_disabled(binding_id, operator="operator")
    assert store.get(binding_id).memory_policy_state is MemoryPolicyState.OPERATOR_CONFIRMED_GLOBAL_DISABLED
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_model_envelope_cannot_set_memory_policy(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = store.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    text = """<HMASD_MANAGED_ACTOR_COMMAND_V1>
{"schema_version":"1.0","packet_kind":"MANAGED_ACTOR_COMMAND","action_kind":"NO_CONTROL_ACTION","payload":{}}
</HMASD_MANAGED_ACTOR_COMMAND_V1>"""
    command = extract_managed_command(text)
    assert command is not None
    assert store.get(binding_id).memory_policy_state is MemoryPolicyState.UNVERIFIED
    store.attach_thread(binding_id, "thr_x")
    store.mark_verification_required(binding_id)
    with pytest.raises(BindingError, match="memory policy"):
        store.activate(binding_id)
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
