"""Operator-only verification and activation of managed bindings."""

from __future__ import annotations

from .binding_store import BindingError, BindingStore
from .command_gateway import CommandGateway, CommandGatewayError
from .mailbox_store import MailboxStore
from .managed_context import build_bootstrap_text, record_context_injection
from .managed_models import BindingState, ManagedIntentKind
from .managed_turns import ManagedTurns
from .observer_evidence import ObserverEvidenceError, load_completed_final_item
from .scheduler_leases import SchedulerLeases
from .semantic_bridge import ManagedActorSnapshot, SemanticBridge, SemanticBridgeError
from .semantic_scanner import SemanticScanner
from .wake_batches import WakeBatchStore
from .wake_recovery import WakeRecovery
from .wake_scheduler import WakeScheduler


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

    async def submit_verification(
        self,
        binding_id: str,
        snapshot: ManagedActorSnapshot,
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
        return submitted

    def complete_activation(self, binding_id: str, *, raw_message_seq: int) -> dict[str, object]:
        binding = self.bindings.get(binding_id)
        if binding is None or not binding.thread_id:
            raise ManagedRuntimeError("binding has no thread")
        try:
            observed = load_completed_final_item(self.bindings.store, raw_message_seq)
        except ObserverEvidenceError as exc:
            raise ManagedRuntimeError(str(exc)) from exc
        if observed["thread_id"] != binding.thread_id:
            raise ManagedRuntimeError("completed item is not on the bound thread")
        intent = self.bindings.store.connection.execute(
            """SELECT * FROM managed_turn_intents
            WHERE binding_id = ? AND intent_kind IN ('BOOTSTRAP', 'IDENTITY_VERIFICATION')
            ORDER BY prepared_at DESC""",
            (binding_id,),
        ).fetchone()
        if intent is None or str(intent["app_server_turn_id"] or "") != str(observed["turn_id"]):
            raise ManagedRuntimeError("completed item does not match the verification turn")
        if str(intent["submission_state"]) == "INCIDENT":
            raise ManagedRuntimeError("verification turn is in INCIDENT; operator recovery required")
        if intent["submission_state"] != "COMPLETED":
            self.turns.record_completion(str(intent["turn_intent_id"]), "completed")
        try:
            applied = self.gateway.ingest_final_item(raw_message_seq=raw_message_seq)
        except CommandGatewayError as exc:
            raise ManagedRuntimeError(str(exc)) from exc
        try:
            activated = self.bindings.activate(binding_id)
        except (BindingError, SemanticBridgeError) as exc:
            current = self.bindings.get(binding_id)
            if current is not None and current.binding_state is not BindingState.REVOKED:
                try:
                    self.bindings.suspend(binding_id)
                except BindingError:
                    pass
            raise ManagedRuntimeError(str(exc)) from exc
        return {"binding_id": activated.binding_id, "state": activated.binding_state.value, "command": applied}

    def _latest_completed_seq(self, thread_id: str, turn_id: str) -> int | None:
        rows = self.bindings.store.connection.execute(
            """SELECT raw_message_seq FROM raw_messages
            WHERE direction = 'stdout' AND thread_id = ? AND turn_id = ?
              AND method = 'item/completed'
            ORDER BY raw_message_seq DESC""",
            (thread_id, turn_id),
        ).fetchall()
        for row in rows:
            try:
                load_completed_final_item(self.bindings.store, int(row[0]))
            except ObserverEvidenceError:
                continue
            return int(row[0])
        return None

    async def verify_and_activate(
        self,
        binding_id: str,
        snapshot: ManagedActorSnapshot,
        *,
        raw_message_seq: int | None = None,
    ) -> dict[str, object]:
        submitted = await self.submit_verification(binding_id, snapshot)
        turn_id = str(submitted.get("app_server_turn_id") or "")
        binding = self.bindings.get(binding_id)
        if binding is None or not binding.thread_id:
            raise ManagedRuntimeError("binding has no thread")
        seq = raw_message_seq if raw_message_seq is not None else self._latest_completed_seq(binding.thread_id, turn_id)
        if seq is None:
            raise ManagedRuntimeError("no recorded completed agentMessage")
        return self.complete_activation(binding_id, raw_message_seq=seq)

    def scheduler(self, mailbox: MailboxStore, *, instance_id: str = "scheduler") -> WakeScheduler:
        batches = WakeBatchStore(self.bindings.store, mailbox)
        leases = SchedulerLeases(self.bindings.store)
        return WakeScheduler(
            self.bindings,
            mailbox,
            batches,
            leases,
            WakeRecovery(
                self.bindings,
                mailbox,
                batches,
                self.turns.client,
                leases,
                instance_id,
                bridge=self.bridge,
            ),
            SemanticScanner(mailbox, self.bridge),
            self.bridge,
            self.turns.client,
            instance_id=instance_id,
        )

    async def scheduler_once(self, mailbox: MailboxStore, *, instance_id: str = "scheduler") -> dict[str, object]:
        return await self.scheduler(mailbox, instance_id=instance_id).once()
