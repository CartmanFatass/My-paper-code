## Unrecoverable-conversation fallback

If the original conversation cannot be recovered after the supported same-request repair path,
the author DM may use a new conversation only when the old operation is positively verified as
`sendAttempted=false` with no provider pairing or accepted effect. Record the old operation as
`VERIFIED_NONACCEPTANCE / CONVERSATION_UNRECOVERABLE` and preserve its HANDOFF, prompt hash,
idempotency key, tab facts and receipts. Then create a new handoff/conversation and idempotency
key carrying the identical scientific prompt and frozen inputs, bind it as a new operation, and
link both records. This is a recovery rebind, not a resend of an uncertain effect. Never use this
fallback when `sendAttempted=true`, acceptance is unknown, or any provider pairing may exist; in
those cases observe and reconcile the original operation only.

For a failed initial homepage operation with no registry binding, use
`bind_conversation.prepare_unaccepted_first_binding_rebind` with the validated replacement
request and the fresh preserved operation audit. It reserves one deterministic generation,
retains the prior audit in request history, and admits only explicit OWNER_DIRECT recovery with
identical prompt/model/effort. It does not invent or quarantine a conversation UUID. Then use
normal firstBinding and bind only the actual post-Send URL with the same reset evidence.
An existing binding requires its own reconciliation or concrete-context replacement route.
