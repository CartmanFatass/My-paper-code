"""Operator-explicit managed thread provisioning with at-most-once mutations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .binding_store import BindingError, BindingStore
from .client import AppServerClient
from .durability.outbox import MutationSpec, OperationState
from .durability.session_owner import AppServerSessionOwner, MutationSubmissionResult
from .durability.models import AggregateKind, TransitionCause, TransitionRequest
from .durability.transaction import DurabilityTransaction
from .durability.transitions import TransitionKernel
from .managed_models import BindingState, HistoryTrust, ThreadOrigin
from .semantic_bridge import ManagedActorSnapshot, SemanticBridgeError

MEMORY_MODE_METHOD = "thread/memoryMode/set"


def memory_mode_method_supported(schema_blob: str) -> bool:
    return MEMORY_MODE_METHOD in schema_blob


class ProvisioningError(RuntimeError):
    pass


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

    @staticmethod
    def _trusted_currentness(binding: Any) -> tuple[str | None, int, str | None, int | None]:
        if not binding.prepared_context_trusted:
            raise ProvisioningError("binding has no trusted prepared-context provenance")
        if binding.binding_state is BindingState.ACTIVE:
            if binding.verified_state_version is None:
                raise ProvisioningError("ACTIVE binding has no verified-context provenance")
            return (
                binding.verified_checkpoint_id,
                binding.verified_state_version,
                binding.verified_epoch_id,
                binding.verified_epoch_revision,
            )
        return (
            binding.prepared_checkpoint_id,
            binding.prepared_state_version,
            binding.prepared_epoch_id,
            binding.prepared_epoch_revision,
        )

    def _validate_binding(self, binding: Any, *, require_prepared: bool) -> None:
        currentness = self._trusted_currentness(binding)
        if require_prepared and binding.binding_state is not BindingState.PREPARED:
            raise ProvisioningError("binding is not PREPARED")
        bridge = getattr(self.bindings, "bridge", None)
        if bridge is None:
            return
        try:
            actor = bridge.assert_currentness(
                binding.actor_context_id,
                checkpoint_id=currentness[0],
                state_version=currentness[1],
                epoch_id=currentness[2],
                epoch_revision=currentness[3],
            )
        except SemanticBridgeError as exc:
            raise ProvisioningError(str(exc)) from exc
        if actor.actor_kind != binding.actor_kind.value or actor.scope_key != binding.semantic_scope_key:
            raise ProvisioningError("semantic actor no longer matches binding")

    def _owner(self) -> AppServerSessionOwner:
        if self.client is None:
            raise ProvisioningError("client required for App Server mutation")
        return AppServerSessionOwner.for_client(self.client, self.bindings.store)

    async def _mutate(
        self,
        *,
        dedupe_key: str,
        method: str,
        params: dict[str, object],
        binding_id: str,
        thread_id: str | None,
    ) -> tuple[str, MutationSubmissionResult]:
        owner = self._owner()
        operation = owner.enqueue_mutation(
            MutationSpec(
                dedupe_key=dedupe_key,
                protocol_session_id=owner.protocol_session_id,
                run_id=owner.protocol_session_id,
                method=method,
                params=params,
                target=f"binding:{binding_id}",
                thread_id=thread_id,
                binding_id=binding_id,
            )
        )
        result = await owner.submit(operation.operation_id)
        if result.state is not OperationState.DONE or result.outcome != "OK":
            raise ProvisioningError(f"{method} {result.outcome or result.state.value}; do not retry")
        return operation.operation_id, result

    def _attach_operation_thread(self, binding_id: str, thread_id: str, operation_id: str) -> None:
        binding = self.bindings.get(binding_id)
        if binding is None or binding.binding_state is not BindingState.PREPARED:
            raise ProvisioningError("only a PREPARED binding may attach the observed thread")
        if self.bindings.binding_for_thread(thread_id) is not None:
            raise ProvisioningError("thread is already bound")
        version = int(
            self.bindings.store.connection.execute(
                "SELECT version FROM managed_actor_bindings WHERE binding_id = ?",
                (binding_id,),
            ).fetchone()[0]
            or 0
        )
        with self.bindings.store._lock, DurabilityTransaction(self.bindings.store.connection):
            TransitionKernel(self.bindings.store.connection).apply(
                TransitionRequest(
                    aggregate_kind=AggregateKind.MANAGED_BINDING,
                    aggregate_id=binding_id,
                    expected_state=BindingState.PREPARED.value,
                    expected_version=version,
                    target_state=BindingState.THREAD_CREATED.value,
                    cause_kind=TransitionCause.APP_SERVER_EFFECT,
                    cause_ref=operation_id,
                    field_updates={
                        "thread_id": thread_id,
                        "thread_created_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            )
        self.bindings._record_event(binding_id, "THREAD_ATTACHED", {"thread_id": thread_id})

    async def apply_memory_policy(self, binding_id: str, *, schema_blob: str, operator: str) -> None:
        if not memory_mode_method_supported(schema_blob):
            self.confirm_global_memory_disabled(binding_id, operator=operator)
            return
        binding = self.bindings.get(binding_id)
        if binding is None or not binding.thread_id:
            raise ProvisioningError("binding has no thread")
        self._validate_binding(binding, require_prepared=False)
        await self._mutate(
            dedupe_key=f"memory-mode:{binding_id}:{binding.thread_id}",
            method=MEMORY_MODE_METHOD,
            params={"threadId": binding.thread_id, "mode": "disabled"},
            binding_id=binding_id,
            thread_id=binding.thread_id,
        )
        with self.bindings.store._lock, self.bindings.store.connection:
            self.bindings.store.connection.execute(
                "UPDATE managed_actor_bindings SET memory_policy_state = ? WHERE binding_id = ?",
                ("DISABLED_BY_THREAD_API", binding_id),
            )

    async def create_fresh_thread(self, binding_id: str) -> str:
        binding = self.bindings.get(binding_id)
        if binding is None:
            raise BindingError(f"unknown binding: {binding_id}")
        self._validate_binding(binding, require_prepared=True)
        operation_id, submitted = await self._mutate(
            dedupe_key=f"thread-start:{binding_id}",
            method="thread/start",
            params={"cwd": binding.thread_cwd, "ephemeral": False, "approvalPolicy": "never"},
            binding_id=binding_id,
            thread_id=None,
        )
        response = submitted.response or {}
        result = response.get("result") if isinstance(response.get("result"), dict) else {}
        thread = result.get("thread") if isinstance(result.get("thread"), dict) else {}
        thread_id = str(thread.get("id") or "")
        if not thread_id:
            raise ProvisioningError("thread/start returned no thread id; do not retry")
        self._attach_operation_thread(binding_id, thread_id, operation_id)
        read = await self.client.read_thread(thread_id)  # type: ignore[union-attr]
        observed = read.get("thread") if isinstance(read.get("thread"), dict) else {}
        if str(observed.get("id") or "") != thread_id:
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
        binding = self.bindings.get(binding_id)
        assert binding is not None
        self._validate_binding(binding, require_prepared=True)
        operation_id, _ = await self._mutate(
            dedupe_key=f"thread-resume:{binding_id}:{thread_id}",
            method="thread/resume",
            params={"threadId": thread_id},
            binding_id=binding_id,
            thread_id=thread_id,
        )
        self._attach_operation_thread(binding_id, thread_id, operation_id)
        return binding_id
