# External Review Transport Exploration Experience

Status: `CONTROLLER_DIRECT_EXPLORATION`
Browser automation Skill: `DISABLED_USER_DIRECTIVE`
Skill abstraction: forbidden until multiple stable automated cycles and explicit user approval
Stable automated end-to-end cycles: 0

A stable cycle requires all of: no routine human step; exact registered conversation and Pro model; deterministic dispatch; valid immutable submission receipt; natural marked response; two-snapshot stable capture; valid no-clobber raw archive.

## Trial 20260723-T01 — fresh-session BrowserMCP type timeout

- Round: `20260723_decoupled_skill_lifetime_direction`.
- Preconditions observed: canonical validator `READY_TO_SUBMIT`; pushed boundary `REMOTE_EVIDENCE_READY`; dispatch SHA-256 `b509ff783a76f381a4aeef4098a098e5e2253d2b29e0ce5fcee2fa67b84305cb`; question SHA-256 `bb358220131cf87077be68aa29be8d7cbdfc1400b00fcf41c3cd113e13551d43`; registered URL and visible Pro account/model; empty composer.
- Action: one BrowserMCP `browser_type` of the 311-code-unit deterministic dispatch with submission disabled.
- Observation: the tool returned `WebSocket response timeout after 30000ms`.
- Visible side effect: the subsequent read-only snapshot showed the exact dispatch in the composer and no new user turn.
- Durable state: no receipt, no raw response, validator remained `READY_TO_SUBMIT`.
- Human dependency observed: extension disconnect/reconnect and draft clearing were required by the old recovery procedure.
- First failed invariant: the transport could not distinguish action completion from response timeout without human recovery.
- Candidate lesson: separate action acknowledgement from postcondition reconciliation; do not encode a timeout as automatic retry or automatic failure.
- Stable-cycle contribution: 0.

## Trial 20260723-T02 — replacement-process type timeout and reconnect failure

- Round: `20260723_decoupled_skill_lifetime_direction`.
- Preconditions observed: old BrowserMCP tree was terminated only after verifying root PID `4152` was a direct child of `omp.exe` PID `10756`; OMP spawned replacement root PID `24104`; registered page was reconnected; stale exact draft was cleared; fresh snapshot showed an empty composer and visible Pro model.
- Action: one BrowserMCP `browser_type` of the same deterministic dispatch with submission disabled.
- Observation: the tool again returned `WebSocket response timeout after 30000ms`.
- Visible side effect: the subsequent read-only snapshot again showed the exact dispatch in the composer and no new user turn.
- Recovery probe: after verified termination of replacement root PID `24104`, OMP spawned root PID `12032`, but a snapshot returned `No connection to browser extension`.
- Durable state: no receipt, no raw response, validator remained `READY_TO_SUBMIT`.
- Human dependency observed: BrowserMCP server respawn did not reconnect the extension automatically.
- First failed invariant: the registered extension connection is not restart-stable and cannot satisfy a no-human recovery contract.
- Candidate lesson: a viable automated transport must preserve or automatically re-establish the authenticated browser attachment and reconcile exact DOM postconditions after action timeouts.
- Stable-cycle contribution: 0.

## Open exploration constraints

- GPT-5.6 Pro remains the only scientific decision source.
- No local model or agent may substitute for a missing Pro response.
- The canonical round is still unsubmitted: receipt absent, raw absent.
- The disabled BrowserMCP automation Skill must not be invoked.
- `hmasd-review-scout` records trials only; it never operates transport or writes a Skill.

## Trial 20260723-T03 — unauthenticated managed-browser conversation navigation

- Canonical round: `20260723_decoupled_skill_lifetime_direction`.
- Evidence locations: `docs/project/CURRENT_WORK.md:63-74` (round, transport policy, and durable state); Controller tool output for the managed headless-browser navigation and accessibility observation (no persisted tool-output artifact path exists).
- Exact preconditions observed: the Controller attempted the registered conversation URL through the built-in managed headless browser; the transport was required to use an authenticated registered Pro conversation with no routine human step; receipt and raw archive were absent before the probe.
- Action: one attempt to open/navigate to the registered conversation URL in the built-in managed headless browser.
- Observation: the browser opened the URL, but navigation ended at `https://chatgpt.com/`; accessibility observation exposed two `Log in` buttons and no authenticated Pro account.
- Visible side effect: the managed browser displayed the unauthenticated landing state; no message was typed or submitted.
- Durable state: no submission receipt or raw file was created; the canonical round remained `READY_TO_SUBMIT_RECEIPT_ABSENT_RAW_ABSENT_DIRECT_EXPLORATION`.
- First failed invariant: missing authenticated registered conversation context.
- Action indeterminate: no; navigation and accessibility observation were determinate, while authenticated conversation access was unavailable.
- User participation required: no user step occurred during the attempt; establishing the missing authenticated context would require user participation [INFERENCE], so the no-routine-human-step precondition was not met.
- Safe next probe: perform only a read-only authentication/context check before any composer action, and stop if the registered authenticated Pro conversation is not visible.
- Candidate lesson: an isolated unauthenticated managed browser is not a valid external-Pro transport; credentials must not be copied into it.
- Stable-cycle contribution: 0.

## Trial 20260723-T04 — installed-source selected-tab reconnect and snapshot coupling

- Canonical round: `20260723_decoupled_skill_lifetime_direction`.
- Evidence locations: Controller-supplied installed-source facts in this assignment for Edge extension `bjfgambnhccakkhmkepdoekmckoijdlc` version `1.3.4` and the installed MCP server source (no persisted tool-output artifact path was supplied).
- Exact preconditions observed: the versioned Edge extension background and popup sources, plus the installed MCP server source, were available for a bounded source-level transport inspection; the extension's `local:selectedTabId` and the server's `browser_type` path were the relevant paths; no browser/MCP action or round submission was performed.
- Action: one attempt to trace selected-tab reconnect, popup selection, and `browser_type` post-action snapshot behavior across the supplied installed sources.
- Observation: the background source defines `local:selectedTabId`; a one-second interval opens `ws://localhost:9009` when that value names a live tab and no socket exists; socket close clears only the in-memory socket and the interval retries; an invalid tab clears `selectedTabId`. The popup reads the active tab, Connect writes its ID to `local:selectedTabId`, and Disconnect writes `null`. The installed MCP server's `browser_type` first awaits the extension action and then unconditionally captures a full ARIA snapshot; its WebSocket request timeout defaults to 30 seconds.
- Visible side effect: this was source-level only; no browser UI, composer, socket, receipt, or response changed.
- Durable state: no submission receipt or raw file was created; the canonical round remained `READY_TO_SUBMIT_RECEIPT_ABSENT_RAW_ABSENT_DIRECT_EXPLORATION`.
- First failed invariant: once an invalid tab clears `selectedTabId`, the server has no exposed external select-tab message with which to restore that value.
- Action indeterminate: no; the supplied source facts and their control flow were determinate.
- User participation required: no user participation was required for this inspection; restoring a cleared selection through the popup would require user participation [INFERENCE].
- Inference: the exact T01/T02 composer side effects are consistent with a post-action snapshot timeout, because `browser_type` waits for the extension action and then unconditionally performs the full snapshot while the request timeout is 30 seconds.
- Safe next probe: perform only a read-only source or transport check that separates extension-action acknowledgement from optional snapshot capture, without retrying a timed-out mutation.
- Candidate lesson: preserve `selectedTabId` and separate mutation acknowledgement from optional snapshot capture; do not turn this candidate lesson into a workflow rule or Skill.
- Stable-cycle contribution: 0.
