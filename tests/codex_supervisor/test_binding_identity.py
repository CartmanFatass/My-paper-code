from pathlib import Path

import pytest

from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingError, BindingStore
from tools.codex_supervisor.managed_models import HistoryTrust, ThreadOrigin


def test_one_thread_one_binding_and_kind_isolation(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    root = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    portfolio = seeded["bridge"].snapshot(seeded["portfolio"].actor_context_id)
    root_id = store.prepare_binding(
        root,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    port_id = store.prepare_binding(
        portfolio,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    store.attach_thread_for_tests(root_id, "thr_shared")
    with pytest.raises(BindingError, match="already bound"):
        store.attach_thread_for_tests(port_id, "thr_shared")
    store.attach_thread_for_tests(port_id, "thr_portfolio")
    assert store.binding_for_thread("thr_shared").actor_kind.value == "OPERATIONAL_ROOT"
    assert store.binding_for_thread("thr_portfolio").actor_kind.value == "PORTFOLIO"
    assert store.binding_for_thread("thr_shared").actor_context_id != store.binding_for_thread("thr_portfolio").actor_context_id
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()
