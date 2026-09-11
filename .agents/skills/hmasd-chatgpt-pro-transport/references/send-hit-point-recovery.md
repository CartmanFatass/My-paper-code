# Send hit-point mismatch recovery

### Locator hit-point mismatch recovery

A locator result is not, by itself, proof that its rendered hit point is clickable. The
observed failure mode is an exact Send prompt locator with `matchCount=1`,
`visibleCount=1`, and `disabled=false`, followed by a force-click error such as
`No element found at point … waiting on click for selector`. Treat that combination
as a locator coordinate offset, not as `SEND_FAILED_PRE_SEND` and not as evidence
that a submission occurred.

Before making any classification, take fresh DOM state using the current browser
API. Select the exact visible Send prompt node from that fresh DOM; do not guess
coordinates or reuse a stale node. A single DOM-node click is
permitted only when all of the following are true: the URL is unchanged from the
pre-send observation, no visible user-message node exists for the exact prompt, and
fresh locator diagnostics still prove that this exact Send control is enabled and
visible. This DOM-node click replaces the failed locator click; it is the one Send
attempt and is recorded as `SEND_ATTEMPTED`.

Immediately after the DOM-node click, re-verify the concrete `/c/<uuid>` URL (and the
bound conversation when one already exists), the exact visible user-message node and
its exact prompt text, and every expected attachment/file group and recorded hash. If
that evidence is complete, record `SEND_CONFIRMED`. If the URL or user-node evidence
is ambiguous at any point, record terminal `SEND_UNCERTAIN`; do not retry. If the
post-click snapshot is unambiguously unchanged with no user node, record
`SEND_FAILED_PRE_SEND` and stop. Never perform blind coordinate retries, a second
DOM-node click, or any retry after `SEND_UNCERTAIN`.
