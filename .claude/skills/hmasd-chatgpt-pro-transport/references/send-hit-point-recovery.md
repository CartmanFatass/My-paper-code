# Recover an ineffective or uncertain send

Recover the same strict Agentify operation, never a new send. Preserve the exact message,
idempotency key, conversation and every attempt fact. No direct Send clicks or fresh operation
may bypass the persisted sendAttempted boundary.

1. After an error or ineffective click, read fresh state on the exact conversation: submitted
   user messages, active generation, composer text and the current Send control. An error
   string, stale DOM, URL alone or missing cached node cannot prove non-acceptance.
2. If the exact message is already submitted, observe its response. Do not click Send. If the
   evidence is uncertain, keep submission stopped and reconcile through a fresh read or one
   recovered tab at the same URL; report `SEND_UNCERTAIN` with what remains to reconcile.
3. Only a persisted sendAttempted=false result permits repair of the reported pre-send
   problem and reuse of review_query for that same operation with its original arguments
   and repaired tab identity. Fresh page appearance alone is not this evidence.
4. If sendAttempted=true, never click Send, even if the composer appears unchanged.
   Observe with wait_response/read_page; the same immutable operation with verifyExisting=true
   may recover native pairing/archive without sending. If its value is unknown, reconcile
   first: verifyExisting can send when the stored flag is false. Never change the operation's
   keys or create another operation to bypass uncertainty.
5. If acceptance remains unresolved, return SEND_UNCERTAIN with the concrete evidence and
   prerequisite or engineering fix to the assigning author. Preserve the operation for
   reconciliation; do not spin on clicks.

Missing login, a changed conversation, the wrong model, a mismatched payload, unresolved
acceptance or a possibly active generation prohibits submission. A human-required login, a
CAPTCHA or an inaccessible provider is reported plainly; it is a transport fact, not a reason to
change the question or the direction's plan.
