"""Operator-only verification and activation of managed bindings."""

from __future__ import annotations

from .binding_store import BindingError, BindingStore
from .command_gateway import CommandGateway, CommandGatewayError
from .managed_context import build_bootstrap_text, record_context_injection
from .managed_models import BindingState, HistoryTrust, ManagedIntentKind
from .managed_turns import ManagedTurns
from .semantic_bridge import ManagedActorSnapshot, SemanticBridge, SemanticBridgeError


class ManagedRuntimeError(RuntimeError):
    """Raised when verification cannot activate a binding."""


class ManagedRuntime:
    def __init__(
        self,
        bindings: BindingStore,
        turns: ManagedTurns,
        gateway: CommandGateway,
        bridge: SemanticBridge,
    ) -> None:
        self.bindings = bindings
        self.turns = turns
        self.gateway = gateway
        self.bridge = bridge

    async def verify_and_activate(
        self,
        binding_id: str,
        snapshot: ManagedActorSnapshot,
        *,
        final_item_type: str,
        final_lifecycle: str,
        final_text: str,
        raw_message_seq: int = 1,
    ) -> dict[str, object]:
        binding = self.bindings.get(binding_id)
        if binding is None or not binding.thread_id:
            raise ManagedRuntimeError("binding has no thread")
        if binding.binding_state is BindingState.THREAD_CREATED:
            self.bindings.mark_verification_required(binding_id)
            binding = self.bindings.get(binding_id)
        if binding is None or binding.binding_state is not BindingState.VERIFICATION_REQUIRED:
            raise ManagedRuntimeError("binding is not ready for verification")
        intent_id = self.turns.prepare(
            binding_id,
            intent_kind=ManagedIntentKind.BOOTSTRAP,
            input_ref="bootstrap",
            checkpoint_id=snapshot.checkpoint_id,
            expected_state_version=snapshot.state_version,
            expected_epoch_id=snapshot.epoch_id,
            expected_epoch_revision=snapshot.epoch_revision,
        )
        text = build_bootstrap_text(snapshot, history_trust=binding.history_trust)
        record_context_injection(
            self.bindings.store,
            binding_id=binding_id,
            turn_intent_id=intent_id,
            snapshot=snapshot,
            input_text=text,
        )
        submitted = await self.turns.submit(intent_id, text)
        turn_id = str(submitted.get("app_server_turn_id") or "")
        self.turns.record_completion(intent_id, "completed")
        try:
            applied = self.gateway.ingest_final_item(
                thread_id=binding.thread_id,
                turn_id=turn_id,
                raw_message_seq=raw_message_seq,
                item_type=final_item_type,
                lifecycle=final_lifecycle,
                text=final_text,
            )
        except CommandGatewayError as exc:
            raise ManagedRuntimeError(str(exc)) from exc
        try:
            self.bridge.snapshot(binding.actor_context_id)
            activated = self.bindings.activate(binding_id)
        except (BindingError, SemanticBridgeError) as exc:
            if self.bindings.get(binding_id).binding_state is not BindingState.REVOKED:
                try:
                    self.bindings.suspend(binding_id)
                except BindingError:
                    pass
            raise ManagedRuntimeError(str(exc)) from exc
        return {"binding_id": activated.binding_id, "state": activated.binding_state.value, "command": applied}
