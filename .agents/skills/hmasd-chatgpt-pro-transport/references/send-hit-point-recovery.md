# Recover an ineffective or uncertain send

One accepted submission per question is the limit. Failed clicks do not consume a question and
do not authorise a new conversation. Preserve the exact message, the conversation and every
attempt fact.

1. After an error or ineffective click, read fresh state on the exact conversation: submitted
   user messages, active generation, composer text and the current Send control. An error
   string, stale DOM, URL alone or missing cached node cannot prove non-acceptance.
2. If the exact message is already submitted, observe its response. Do not click Send. If the
   evidence is uncertain, keep submission stopped and reconcile through a fresh read or one
   recovered tab at the same URL; report `SEND_UNCERTAIN` with what remains to reconcile.
3. If fresh loaded evidence shows no submitted message, no generation and the unchanged
   composer payload, one immediate retry is allowed on the freshly identified enabled Send
   control. Count every click, including the ineffective one. Never guess coordinates or
   repeat a broken locator.
4. After a second proven ineffective click, repair the interaction surface: reacquire the DOM
   or recover one tab at the bound URL; recheck login, model, conversation, messages and
   payload. Fresh evidence of non-acceptance plus a concrete changed interaction permits one
   further submission of the same payload in this pass.
5. If that fails, return the concrete evidence and the external prerequisite or engineering
   fix to the DM. Do not spin on clicks.

Missing login, a changed conversation, the wrong model, a mismatched payload, unresolved
acceptance or a possibly active generation prohibits submission. A human-required login, a
CAPTCHA or an inaccessible provider is reported plainly; it is a transport fact, not a reason to
change the question or the direction's plan.
