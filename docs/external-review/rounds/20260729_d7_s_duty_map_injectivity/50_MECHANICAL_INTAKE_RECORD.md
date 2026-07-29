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

## Capture

The tab wedged a **second** time mid-round (45 s `document_idle` timeouts on
`screenshot`, `find` and `get_page_text`, surviving a navigate and two waits).
Bounded replacement applied again; the new tab rendered immediately. Exactly one
tab holds the conversation.

Capture route, in the order attempted:

1. **Conversation API** located the answer node exactly — walked the child chain
   from the fence node `0b3c8d2b-555f-4f86-862b-26cd89d1be91` to the longest
   assistant `text` node, `4f6b9357-db35-484e-9fee-a861d5286331`, 21124 chars,
   head `# Scientific ruling — D7.S duty-map injectivity`. This confirmed *which*
   turn to capture, which is the part that went wrong on an earlier round.
2. `navigator.clipboard.writeText` refused — `Document is not focused`.
3. A focusing click wedged the renderer; tab replaced again.
4. `textarea` + `execCommand('copy')` returned `false` (no user gesture).
5. Returning the text through the JS channel was **blocked by the harness**, both
   raw (`Cookie/query string data` — the `stage_commit=<40-hex>` pattern reads as
   a query string) and base64 (`Base64 encoded data`). That is a deliberate
   safety control on bulk encoded data and was **not** worked around; encoding
   past a filter to move the same bytes is defeating the control, not satisfying
   it.
6. **`Copy response` button**, the Skill's own route: a real UI gesture,
   preserves markdown.

### The verification that mattered

The first `Copy response` click did not land — the clipboard still held the
**fence** from submission. A check for the stage_commit alone would have passed:

```text
clip_len=383  has_commit=True  has_title=False  has_sec9=False
```

**The fence contains the stage_commit, so its presence is not a capture test.**
Retried after setting a sentinel, so a stale clipboard could not masquerade as
success:

```text
still_sentinel=False  clip_len=21923  has_title=True  has_sec9=True
```

Archived to `21_PRO_OPEN_RAW.md` via `UTF8Encoding($false)`:
`written_len=21923`, `exact_roundtrip=True`, `bom_free=True`.

The 21923 (rendered markdown) vs 21124 (API `content.parts`) difference is
expected — the copy path renders LaTeX delimiters differently. Both were checked
to be the same turn by head and tail.

## Status

`CLOSED`. Ruling archived byte-exact; reconciliation written in
`30_PM_SCIENTIFIC_RECONCILIATION.md`.
