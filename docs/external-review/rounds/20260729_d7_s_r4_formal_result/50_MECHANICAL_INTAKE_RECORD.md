# Mechanical intake — transport facts only

No scientific classification here.

```text
round         20260729_d7_s_r4_formal_result
stage_commit  3e5624fa908c5fdf33f0fb6e06025f252aeb2f94
branch        untied-k
reviewer      open_divergent (registered), conversation 6a63979e-35d8-83e8-8da7-10de59a5fdeb
preflight     ROUND_PREFLIGHT_READY, allow_list_count=8, archive REVIEW_EVIDENCE_ARCHIVE_READY
fence_sent    YES
status        REVIEW_RECEIVED_AND_ARCHIVED
raw_file      21_PRO_OPEN_RAW.md (20307 chars, markdown preserved, byte-exact reread)
worked_for    9m55s as reported by the page
```

## Capture

Captured through the message's own `Copy response` control, not from rendered
page text, so headings, tables and fenced blocks survive: 40 headings, 14 fenced
blocks, both `5a` and `5b` present, `stage_commit` present in the body.

**The first copy attempt took the wrong message.** A `find` for the copy control
returned the toolbar of the *previous* round's answer; the clipboard came back
37728 chars with no `3e5624fa` in it. Caught by asserting the commit was present
rather than by trusting the click. Resolved by selecting the
`copy-turn-action-button` that follows the last assistant node in document order
-- exactly one does -- and re-copying against a clipboard sentinel to prove the
copy actually happened. 20307 chars, commit present.

A monitor inspection had independently reported the same 37728-char figure and
described the previous round's subject matter while claiming generation had
stopped. That report was wrong on which turn it read, and it was not acted on:
the page was re-read directly and the last assistant turn identified by document
position relative to the fence.

## Submission

Fence delivered once. Sequence, in order:

1. Preflight re-run at `3e5624fa` immediately before the browser session —
   `ROUND_PREFLIGHT_READY`, 8-path allow-list, archive builds.
2. Registry read: `open_divergent`, `registration_status=registered`,
   branch `untied-k`, matching the fence.
3. Registered conversation opened in a single tab. Fence absence proved by
   content, not by assumption: the two visible fences named rounds
   `20260728_r4_materiality_derivation` and `20260728_r4_contract_freeze`;
   `3e5624fa...` and `20260729_d7_s_r4_formal_result` were both absent from the
   page.
4. Clipboard loaded from `10_FENCE.txt` with `-Encoding UTF8`, verified
   byte-exact: 375 chars, `-ceq` True.
5. Pasted with `ctrl+v` — no keystroke composition, so no newline could submit a
   fragment. Composer read back before sending: `CURRENT_REVIEW_ASSIGNMENT`
   present exactly once, with `stage_commit`, `round`, `question` and
   `instruction` all matching.
6. Sent once. Model selector read `Pro`.

**Send verification.** Composer empty afterwards, and **exactly one** user turn
carries `stage_commit=3e5624fa...`. Generation active.

The Skill's user-turn-count+1 test was inconclusive here and was not relied on:
this conversation virtualizes its message list, so the count read 4 both before
and after while an older turn was evicted from the DOM. The content test —
exactly one turn bearing this round's commit — is the stronger check and is what
establishes both that the send happened and that it happened once.

`hmasd-review-monitor` dispatched after send-verification passed.

## Prior pass — transport was blocked, and nothing was sent

An earlier pass reached the composer and stopped. The browser went down
mid-pass: page operations timed out, two reload-and-waits failed, closing the
tab returned "The browser is shutting down", `chrome.exe` was then absent from
every standard install location, and `list_connected_browsers` returned `[]`.
Five recovery attempts, then stop.

**Nothing was submitted in that pass.** The clipboard was loaded and verified,
but the composer was never clicked, nothing was pasted and no send occurred —
every browser call was read-only. That is why this round carries one fence and
not two.

The two reloads spent on a wedged-renderer diagnosis were correct on the
evidence then available; a shutdown only became distinguishable from a wedge
once tab closure was attempted.

That record named `stage_commit=048483a9...`, which was stale — the round was
re-fenced at `3e5624fa` after `ALGORITHM_PRINCIPLES.md` and
`OPEN_REVIEW_PRINCIPLES.md` were added to the allow-list to satisfy preflight.
`3e5624fa` is the delivered commit.
