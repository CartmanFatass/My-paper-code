from pathlib import Path

import pytest

from tests.codex_supervisor.mailbox_fixtures import plant_verification_receipt
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingError, BindingStore
from tools.codex_supervisor.managed_models import BindingState, HistoryTrust, MemoryPolicyState, ThreadOrigin


def test_prepare_attach_verify_activate_suspend_revoke(tmp_path: Path) -> None:
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
    assert store.get(binding_id).binding_state is BindingState.PREPARED
    store.attach_thread(binding_id, "thr_root")
    store.mark_verification_required(binding_id)
    with pytest.raises(BindingError, match="memory policy"):
        store.activate(binding_id)
    store.confirm_global_memory_disabled(binding_id, operator="operator")
    plant_verification_receipt(store, binding_id, snapshot, "thr_root")
    active = store.activate(binding_id)
    assert active.binding_state is BindingState.ACTIVE
    assert active.memory_policy_state is MemoryPolicyState.OPERATOR_CONFIRMED_GLOBAL_DISABLED
    store.suspend(binding_id)
    assert store.get(binding_id).binding_state is BindingState.SUSPENDED
    store.revoke(binding_id)
    assert store.get(binding_id).binding_state is BindingState.REVOKED
    assert store.binding_for_actor(snapshot.actor_context_id) is None
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_one_actor_one_live_binding(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    store.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    with pytest.raises(BindingError, match="already has"):
        store.prepare_binding(
            snapshot,
            repo_root=str(tmp_path),
            thread_cwd=str(tmp_path),
            created_by_operator="operator",
            thread_origin=ThreadOrigin.NEW,
            history_trust=HistoryTrust.FRESH,
        )
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
