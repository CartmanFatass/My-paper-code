from pathlib import Path

from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.mailbox_store import MailboxStore
from tools.codex_supervisor.managed_models import HistoryTrust, ThreadOrigin


def activate_binding(store: BindingStore, snapshot, tmp_path: Path, thread_id: str) -> str:
    binding_id = store.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    store.attach_thread(binding_id, thread_id)
    store.mark_verification_required(binding_id)
    store.confirm_global_memory_disabled(binding_id, operator="operator")
    store.activate(binding_id)
    return binding_id


def seed_active_root_portfolio(tmp_path: Path) -> dict[str, object]:
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    root_snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    port_snapshot = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    seeded["bindings"] = store
    seeded["mailbox"] = MailboxStore(seeded["supervisor"])
    seeded["root_binding_id"] = activate_binding(store, root_snapshot, tmp_path, "thr_root")
    seeded["portfolio_binding_id"] = activate_binding(store, port_snapshot, tmp_path, "thr_port")
    return seeded
