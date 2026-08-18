"""Operator-explicit managed thread provisioning. No automatic retry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .binding_store import BindingError, BindingStore
from .client import AppServerClient, AppServerRpcError, RetryRequired
from .managed_models import HistoryTrust, ThreadOrigin
from .semantic_bridge import ManagedActorSnapshot
from .transport import TransportClosed

THREAD_NAMES = {
    "OPERATIONAL_ROOT": "HMASD Managed Operational Root",
    "PORTFOLIO": "HMASD Managed Portfolio",
}

MEMORY_MODE_METHOD = "thread/memoryMode/set"


def memory_mode_method_supported(schema_blob: str) -> bool:
    return MEMORY_MODE_METHOD in schema_blob


class ProvisioningError(RuntimeError):
    """Raised when thread creation or memory verification cannot complete."""


class ManagedProvisioner:
    def __init__(self, bindings: BindingStore, client: AppServerClient | None = None) -> None:
        self.bindings = bindings
        self.client = client

    def prepare(
        self,
        snapshot: ManagedActorSnapshot,
        *,
        repo_root: Path,
        operator: str,
        thread_origin: ThreadOrigin = ThreadOrigin.NEW,
        history_trust: HistoryTrust = HistoryTrust.FRESH,
    ) -> str:
        return self.bindings.prepare_binding(
            snapshot,
            repo_root=str(Path(repo_root)),
            thread_cwd=str(Path(repo_root)),
            created_by_operator=operator,
            thread_origin=thread_origin,
            history_trust=history_trust,
        )

    def confirm_global_memory_disabled(self, binding_id: str, *, operator: str) -> None:
        if not operator:
            raise ProvisioningError("operator identity is required")
        self.bindings.confirm_global_memory_disabled(binding_id, operator=operator)

    async def apply_memory_policy(self, binding_id: str, *, schema_blob: str, operator: str) -> None:
        if memory_mode_method_supported(schema_blob):
            if self.client is None:
                raise ProvisioningError("client required for memory-mode API")
            binding = self.bindings.get(binding_id)
            if binding is None or not binding.thread_id:
                raise ProvisioningError("binding has no thread")
            try:
                await self.client.request(MEMORY_MODE_METHOD, {"threadId": binding.thread_id, "mode": "disabled"})
            except (RetryRequired, AppServerRpcError, TransportClosed) as exc:
                raise ProvisioningError("memory-mode request was not confirmed") from exc
            with self.bindings.store._lock, self.bindings.store.connection:
                self.bindings.store.connection.execute(
                    "UPDATE managed_actor_bindings SET memory_policy_state = ? WHERE binding_id = ?",
                    ("DISABLED_BY_THREAD_API", binding_id),
                )
            return
        self.confirm_global_memory_disabled(binding_id, operator=operator)

    async def create_fresh_thread(self, binding_id: str) -> str:
        if self.client is None:
            raise ProvisioningError("client required to create a thread")
        binding = self.bindings.get(binding_id)
        if binding is None:
            raise BindingError(f"unknown binding: {binding_id}")
        if binding.binding_state.value != "PREPARED":
            raise ProvisioningError("binding is not PREPARED")
        params: dict[str, Any] = {
            "cwd": binding.thread_cwd,
            "ephemeral": False,
            "approvalPolicy": "never",
            "sandbox": "read-only",
        }
        try:
            response = await self.client.request("thread/start", params)
        except RetryRequired as exc:
            self.bindings._record_event(binding_id, "THREAD_START_UNCERTAIN", {"reason": "overload"})
            raise ProvisioningError("thread/start uncertain; do not retry automatically") from exc
        except (AppServerRpcError, TransportClosed) as exc:
            self.bindings._record_event(binding_id, "THREAD_START_UNCERTAIN", {"reason": type(exc).__name__})
            raise ProvisioningError("thread/start uncertain; do not retry automatically") from exc
        result = response.get("result") if isinstance(response.get("result"), dict) else {}
        thread = result.get("thread") if isinstance(result.get("thread"), dict) else {}
        thread_id = str(thread.get("id") or "")
        if not thread_id:
            self.bindings._record_event(binding_id, "THREAD_START_UNCERTAIN", {"reason": "missing_id"})
            raise ProvisioningError("thread/start returned no thread id")
        self.bindings.attach_thread(binding_id, thread_id)
        if self.client is not None:
            try:
                await self.client.request(
                    "thread/name/set",
                    {"threadId": thread_id, "name": THREAD_NAMES.get(binding.actor_kind.value, "HMASD Managed Actor")},
                )
            except (AppServerRpcError, RetryRequired, TransportClosed):
                pass
            read = await self.client.read_thread(thread_id)
            read_thread = read.get("thread") if isinstance(read.get("thread"), dict) else {}
            if str(read_thread.get("id") or "") != thread_id:
                raise ProvisioningError("thread/read did not return the created thread")
        return thread_id

    async def adopt_existing_thread(
        self,
        snapshot: ManagedActorSnapshot,
        *,
        thread_id: str,
        repo_root: Path,
        operator: str,
        allow_existing_history: bool,
        confirm_history_nonauthoritative: bool,
    ) -> str:
        if not allow_existing_history or not confirm_history_nonauthoritative:
            raise ProvisioningError("adoption requires explicit history flags")
        if self.client is None:
            raise ProvisioningError("client required to adopt a thread")
        read = await self.client.read_thread(thread_id, include_turns=False)
        thread = read.get("thread") if isinstance(read.get("thread"), dict) else {}
        status = thread.get("status")
        status_type = status.get("type") if isinstance(status, dict) else status
        if status_type == "active":
            raise ProvisioningError("cannot adopt an in-progress thread")
        binding_id = self.prepare(
            snapshot,
            repo_root=repo_root,
            operator=operator,
            thread_origin=ThreadOrigin.ADOPTED_EXISTING,
            history_trust=HistoryTrust.LEGACY_UNTRUSTED_HISTORY,
        )
        try:
            await self.client.request("thread/resume", {"threadId": thread_id})
        except (RetryRequired, AppServerRpcError, TransportClosed) as exc:
            self.bindings._record_event(binding_id, "THREAD_RESUME_UNCERTAIN", {"reason": type(exc).__name__})
            raise ProvisioningError("thread/resume uncertain; do not retry automatically") from exc
        self.bindings.attach_thread(binding_id, thread_id)
        return binding_id
