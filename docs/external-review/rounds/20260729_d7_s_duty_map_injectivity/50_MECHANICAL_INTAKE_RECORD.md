# Mechanical intake record — 20260729_d7_s_duty_map_injectivity

Transport: `project_manager_direct`. No transport delegate.

## Boundary

```text
repository    CartmanFatass/My-paper-code
branch        untied-k
round         20260729_d7_s_duty_map_injectivity
stage_commit  db7ad266394657300b2463e78fc8a5bd06c7e0ad
question      docs/external-review/rounds/20260729_d7_s_duty_map_injectivity/20_PRO_OPEN_QUESTION.md
reviewer      open_divergent (registration_status=registered)
conversation  6a63979e-35d8-83e8-8da7-10de59a5fdeb
```

## Preflight

`preflight_review_round.ps1 -Commit db7ad266... -RoundPath ... -Branch untied-k`
returned `ROUND_PREFLIGHT_READY`, `allow_list_count=11`,
`archive_build=REVIEW_EVIDENCE_ARCHIVE_READY`.

**First attempt failed** with `ROUND_PREFLIGHT_FAILED`: the allow-list was
missing the two standing contracts `docs/project/ALGORITHM_PRINCIPLES.md` and
`docs/external-review/OPEN_REVIEW_PRINCIPLES.md`. Both were added, the question
recommitted, and the fence re-cut at the commit carrying the completed
allow-list. The earlier fence naming `1c4510e9...` was never sent.

## Transport

1. `tabs_context_mcp` found one tab already on the registered conversation.
   Reused, not replaced.
2. That tab **wedged**: `find` and `get_page_text` both timed out at 45s waiting
   for `document_idle`, across a navigate and two waits. Reload-and-wait did not
   clear it.
3. Applied the Skill's bounded replacement: closed the wedged tab, created one,
   navigated to the registered URL. It rendered immediately — the documented
   signature (accumulated renderer state, not the conversation). Exactly one tab
   holds the conversation.
4. Fence absence proved on readable history: `find` for `db7ad266` and
   `duty_map_injectivity` returned no match in any message text.
5. Clipboard loaded from `10_FENCE.txt` with `-Encoding UTF8`, verified after a
   400 ms settle: `exact_match=True`, `src_len=clip_len=383`, `ascii_only=True`.
6. Pasted with `ctrl+v` (never `type`, never `form_input`). Screenshot confirmed
   all seven fence lines present exactly once, model selector on `Pro`.
7. Submitted **once**.

## Send verification — measured, not reasoned

- The fence appears as a **user turn** carrying
  `stage_commit=db7ad266394657300b2463e78fc8a5bd06c7e0ad`.
- Composer empty (`Follow up` placeholder).
- `Pro thinking` visible and `Stop answering` active — generation started.

The fence is sent exactly once. A resuming pass **captures**; it does not
resubmit.

## Monitor

`hmasd-review-monitor` (haiku) dispatched immediately after send-verification
passed. It holds no click, type or write tools. Its brief anchors on the
`db7ad266` user turn and instructs it to escalate rather than substitute a turn
if the anchor is not found — the failure mode that produced a wrong report on an
earlier round.

## Status

`AWAITING RESPONSE`. `21_PRO_OPEN_RAW.md` does not exist yet and no
reconciliation may be written until it does.
