# Pro transport stall repair

Authority: OWNER_DIRECT, 2026-09-11: “解决一下当前的问题 频繁因为pro发送卡住边界 这不正常”.
The owner then explicitly requested corresponding skill, AGENTS and subagent-document
repairs to prevent recurrence; this change implements that request.

## L0 assignment

- Outcome: recover existing failed-effect requests without duplicate accepted Send,
  and stop response/receipt and previous/current-round state confusion.
- Owned surfaces: Transport archive and binding helpers, focused skill tests,
  Transport/Root/DM/Portfolio instructions, AGENTS, Claude transport role and this
  acceptance record. Existing local `.codex/config.toml` changes are outside this assignment.
- Protected behavior: fixed prompt, request ID, provider binding/model, historical
  archives, attempted receipt keys, scientific decisions and experiment budgets.
- Acceptance: regressions reproduce stale-round and short-receipt defects, then
  pass; independent scenarios preserve uncertain-Send safety while giving proven
  nonacceptance a concrete repair path; resume existing pending requests in Transport.
- Non-goals: new scheduler, generic retry framework, new provider conversation,
  empirical allocation, or rewrite of historical raw receipts. Scope additions: none.
- Bound: one local control-plane edit/check/review batch with synthetic tests only;
  no learner imports or experiment runs. Stop submission while acceptance remains
  uncertain; operational recovery stays with the existing Transport task.

## Observed causes

RCLE's exact request had two ineffective clicks at the home page, no conversation
UUID, no submitted user node and no generation. The earlier rule stopped after its
click quota, even though there was no accepted submission. The request remained in
a standalone blocker record with no canonical binding.

FOLR funding had a confirmed current user UUID and pending generation. Old round
send/completion timestamps remained on the reused binding because `old.update`
replaced only selected fields. Current send evidence was valid; stale completion
fields must not classify the new round.

ACVC's complete Git responses existed, but archived short chat links were labeled
as the response. The archive helper explicitly assigned the short receipt path/hash
to response fields and invented caller-direct delivery completion. Historical
sidecars preserve the discrepancy; prospective archivals must use full bytes and
actual receipt routing.

## Validation and application

Baseline independent scenarios reproduced exhausted-click abandonment and terminal
uncertainty wording. Existing concurrent-binding guidance already required servicing
other READY requests while a generation thinks; no new queue mechanism is needed.

Archive regression before the fix: 7 failures, 4 passes. After the fix: 11 passes.
Historical ARCHIVED replay and attempted receipt records remain unchanged.

Independent review additionally exercised contradictory accepted-send evidence and
the first-bind → operational blocker → reconciliation composition. A successful bind
must retain positive acceptance evidence, so a later operational blocker cannot
rearm the request. Actual prebinding clicks, prior blocker notification attempts and
reconciliation evidence carry forward to the bound conversation.

Publication and live recovery results follow below.

Final combined control-plane suite: **132 passed in 3.50s**. Command: `python -m
pytest -q --basetemp temp/tests/transport-repair-root-final-20260911
tests/skills/test_transport_round_reset.py tests/skills/test_transport_send_recovery.py
tests/skills/test_claude_archive_delivery.py tests/skills/hmasd_chatgpt_pro_transport_test.py
tests/skills/hmasd_pro_conversation_binding_test.py`. DM role TOML parses;
`git diff --check` reports no whitespace errors. No scientific execution occurred.
Independent final source/document review: **no material findings remain**; seven
preserved-acceptance counterexamples were independently rejected without mutation.
The same-request RCLE prebinding migration plan conforms to the reviewed contract.

Automatic approval review refused Root's exact scratch cleanup before execution:
`blocked by policy`. Root retains cleanup ownership of the above test directory;
the binder worker retains its reported round-reset/prebinding scratch directories.
No alternate deletion method was attempted. This is a cleanup limitation, not a
transport or scientific blocker.

The old locator test required the literal phrases forbidding any second DOM click
and making uncertainty terminal. Removed that obsolete prose-matching test; the
replacement coverage is executable recovery/receipt tests plus independent
four-scenario review, including uncertain Send and unbound first submission.
