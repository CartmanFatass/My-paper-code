# Mechanical intake record

Transport facts only. No scientific quality classification is recorded here;
that belongs to `30_PM_SCIENTIFIC_RECONCILIATION.md`.

## Identity

```text
round          = 20260727_d7_s_stage_b_crn_and_user_world
reviewer_key   = open_divergent
conversation   = 6a63979e-35d8-83e8-8da7-10de59a5fdeb
branch         = untied-k
stage_commit   = 4b9977b5c5209138f7c224c6aa1fa04a71ddfbaf
question       = docs/external-review/rounds/20260727_d7_s_stage_b_crn_and_user_world/20_PRO_OPEN_QUESTION.md
raw            = docs/external-review/rounds/20260727_d7_s_stage_b_crn_and_user_world/21_PRO_OPEN_RAW.md
transport       = project_manager_direct
```

## Pre-dispatch gate

`preflight_review_round.ps1` returned `ROUND_PREFLIGHT_READY` at the stage
commit, over an 11-path allow-list, with `archive_build =
REVIEW_EVIDENCE_ARCHIVE_READY`.

The question was amended twice before the gate passed. Both amendments are
recorded because they are transport facts, not edits to a sent artifact — no
fence existed yet:

1. it had **no `## Evidence to read` allow-list**, which the gate refuses; and
2. its Q4 still argued a cost verdict the Project Manager had already withdrawn.

A third amendment disclosed that eight cloud shards were already executing and
bounded what would be read from them before a ruling.

## Fence

Composed as `10_FENCE.txt`, loaded via `Set-Clipboard` with
`$src -ceq (Get-Clipboard -Raw)` returning `True`, pasted with `ctrl+v` in one
operation, never typed.

Absence was **proven before submission**: the conversation held exactly two
`CURRENT_REVIEW_ASSIGNMENT` user turns, both naming round `20260726_d7_s...`.
No fence for this round existed.

Send verified mechanically: composer emptied (`Ask ChatGPT` → `Follow up`), and
the fence appeared as a user turn carrying the correct `stage_commit`, round and
question path. Submitted **once**.

## Wait

`hmasd-review-monitor` was dispatched immediately after send-verification. It
returned `GENERATION_PENDING` after 112 seconds of actual runtime while
reporting "18 minutes elapsed over 12 checks".

**The elapsed figure was not backed by anything.** Its tool grant is
`tabs_context_mcp`, `get_page_text`, `read_page`, `find` — no `computer`, so no
`wait` action, and no Bash, so no `sleep`. It cannot pace itself and can only
poll as fast as tool calls return. Its one substantive observation, that the
`Stop answering` control was active, was independently reconfirmed by the
Project Manager and is the only part relied on.

Pacing moved to a Project-Manager-owned background timer — the heartbeat the
registry sanctions — with the monitor left read-only. Nothing was curtailed:
`Answer now` was visible throughout and was never operated.

## Transport recovery

```text
RECOVERY_ATTEMPT
attempt=1
boundary=find (Stop answering control)
action=retried the same read-only find after a script-injection timeout
outcome=timed out again at 45000ms waiting for document_idle

RECOVERY_ATTEMPT
attempt=2
boundary=script injection on the registered tab
action=reload-and-wait on the same tab, then screenshot
outcome=SUCCEEDED once -- page rendered, response observed complete

RECOVERY_ATTEMPT
attempt=3
boundary=script injection on the registered tab
action=second reload-and-wait, longer wait, then screenshot
outcome=timed out again; wedged-tab condition met (every script-injecting call
        times out and it survives a reload)

RECOVERY_ATTEMPT
attempt=4
boundary=wedged tab
action=closed the wedged tab, created one, navigated to the registered URL
outcome=rendered immediately; content identical to the pre-reload snapshot
```

Exactly **one** tab held the conversation on exit, confirmed by
`tabs_context_mcp`. The replacement granted nothing: no second fence was
submitted and none was needed, the round having already been sent and answered.

## Completion evidence

Two stable observations of the same assistant message, separated by well over
three seconds (spanning the reload attempts above): identical visible text, no
active `Stop generating` / `Stop answering` control, no response error, no
`Retry` or continue-generation control, `Response actions` present. The response
sits after this round's fence.

## Capture

Clipboard marked with a sentinel first. First coordinate click on `Copy
response` **left the sentinel unchanged** — the click landed (hover confirmed
the tooltip and highlight at the same coordinates) but the clipboard write did
not happen. A second click at the identical coordinates succeeded, matching the
documented behaviour.

```text
capture_method   = Copy response control, coordinate click
clipboard_length = 18322
reread_equality  = True
file_bytes       = 18384
```

Written with `[IO.File]::WriteAllText` and UTF-8 without BOM, then reread and
compared with `-ceq`. No transcription, no `get_page_text` fallback, no JSON
round-trip.

Sanity checks before archival: not a progress trace; addresses the numbered asks
(`Q1`×2, `Q2`×5, `Q3`×5, `Q4`×2); carries a disposition token
(`MISMATCH`, `SCIENTIFIC_AMBIGUITY`); names the correct stage commit; size is
plausible for a scoped scientific answer.

## Heartbeat

The Project-Manager-owned timer had already fired and exited before archival; no
heartbeat is armed. Confirmed absent.
