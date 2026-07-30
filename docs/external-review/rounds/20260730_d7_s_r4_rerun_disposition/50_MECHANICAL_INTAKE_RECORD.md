# Mechanical intake -- 20260730_d7_s_r4_rerun_disposition

Transport facts only. No scientific classification; that is
`30_PM_SCIENTIFIC_RECONCILIATION.md`.

## Identity

```text
round          20260730_d7_s_r4_rerun_disposition
repository     CartmanFatass/My-paper-code
branch         untied-k
stage_commit   45d876b9a78242c52d59373f5a8700ac1330dbfa
question       docs/external-review/rounds/20260730_d7_s_r4_rerun_disposition/20_PRO_OPEN_QUESTION.md
reviewer       open_divergent (registered), conversation 6a63979e-35d8-83e8-8da7-10de59a5fdeb
transport      project_manager_direct
```

## Pre-dispatch

`preflight_review_round.ps1` returned `ROUND_PREFLIGHT_READY` with
`allow_list_count = 11`, every allow-listed path present at `stage_commit`, and
`archive_build = REVIEW_EVIDENCE_ARCHIVE_READY`.

Fence absence proved from the conversation API, not `find`:
`user_turns=37 exact_fence_hits=0 any_fence_turns=32`. Submission authorized on
`exact_fence_hits=0`.

## Send

Verified mechanically rather than by inference: `user_turns` 37 -> 38,
`exact_fence_hits` 0 -> 1, composer empty, generation active.

```text
RECOVERY_ATTEMPT
attempt=1
boundary=compose the fence via clipboard paste
action=Set-Clipboard from 10_FENCE.txt (exact=True, 383 chars, 0 non-ASCII),
       focused the composer via javascript_tool, pressed OS-level ctrl+v
outcome=composer read back len=0 -- the paste did not land. The registered tab is
        hidden (document.visibilityState=hidden), so the OS-level keypress went
        to whichever window held OS focus. Conversation API confirmed nothing was
        sent: user_turns still 37, exact_fence_hits still 0.

RECOVERY_ATTEMPT
attempt=2
boundary=same
action=document.execCommand('insertText') into the contenteditable composer,
       which generates the input events the composer's state depends on and
       needs no OS focus. No '\n' was delivered as a keypress, so no fragment
       could self-submit.
outcome=composer read back byte-for-byte against 10_FENCE.txt: len=382 (the
        artifact's 383 less its trailing newline), stage_commit_count=1,
        header_count=1, and every identity field present. Submitted once via the
        page's own send-button. Send verification above passed.
```

Both attempts are recorded because the second used a mechanism the Skill does not
list. The Skill's prohibition is on delivering newlines as Enter keypresses and on
composing keystroke-by-keystroke; this satisfies both constraints -- whole text in
one operation, zero Enter keypresses -- and the byte-for-byte read-back against
the committed artifact is stronger evidence than a paste would have produced.

## Wait

No `hmasd-review-monitor` was dispatched and no Monitor was created. The Project
Manager did the waiting in-band, polling at roughly 2-5 minute intervals, which
the Skill permits ("at most one Project-Manager-owned five-minute heartbeat while
pending"). **There is therefore no heartbeat to delete.** Confirmed absent.

Generation ran approximately 50 minutes. `Answer now` was never clicked and no
control that curtails extended thinking was operated.

Two transport observations worth keeping:

- Heavy `await fetch` calls to `/backend-api/conversation/` intermittently
  returned `Failed to fetch` and once timed out `Runtime.evaluate` at 45s, while
  light DOM reads answered instantly throughout. That is background throttling on
  a hidden tab, as the Skill documents, not a dying page. Liveness was confirmed
  by light reads and by an Edge process count of 19.
- The rendered transcript is virtualized. Throughout generation the last
  DOM-visible assistant node was a PREVIOUS round's ruling (15935 chars, "D7.S
  conformance suite v2"). Reading the page tail would have archived the wrong
  round. Completion was judged from the stop control plus message identity.

## Completion evidence

Two snapshots from distinct inspections, 4 seconds apart:

```text
first  {len:21002, hash:1315915032, id:ee8ae2bc-5b0b-452b-a291-a510baa611c5, stop:false, retry:false}
second {len:21002, hash:1315915032, id:ee8ae2bc-5b0b-452b-a291-a510baa611c5, stop:false, retry:false}
stable true
```

Identical length, content hash and message id; no active stop control; no retry
or continue-generation control.

## Capture

Primary path -- the conversation API, returning the model's own emitted markdown
rather than re-serialized DOM. Message id `ee8ae2bc` matches the DOM node
inspected above.

`navigator.clipboard.writeText` refused twice with `NotAllowedError` because
`document.visibilityState` was `hidden` and there was no transient activation. A
`computer` screenshot did not activate the tab. Resolved with the Skill's
prescribed mechanism: a full-viewport transparent overlay carrying the copy
handler, clicked once by `computer` at (784, 386), then removed immediately --
`copyResult=API_WROTE`, `overlay_removed=true`. The overlay could not reach any
page control while it existed.

**Fidelity proof, which the clipboard path alone cannot produce.** The page
reported its own source string as 22675 characters. The clipboard held 23186 raw
with 511 CR bytes; normalized to LF that is exactly 22675. Two independent
measurements of the same text agreeing to the character.

Normalized CRLF to LF before archiving so the archive matches the emitted source
rather than the clipboard's transport encoding.

`archive_pro_response.ps1`:

```json
{
  "status": "ROUND_ARCHIVE_OK",
  "chars": 22675,
  "chars_reread": 22675,
  "exact_equal": true,
  "stage_commit": "45d876b9a78242c52d59373f5a8700ac1330dbfa",
  "first_line": "# Scientific ruling — D7.S R4 rerun disposition",
  "last_line": "**D7.3 and D8 remain blocked. This review authorizes neither a new formal run nor publication of the current R4 branch as a confirmatory result.**"
}
```

The capture carries THIS round's `stage_commit`, opens with its own heading, and
is 22675 characters -- not the 383-character fence, and not a progress trace.

No `22_PROVISIONAL_CAPTURE.txt` was written. The provisional dump exists to
survive a browser death between completion and capture; here the byte-exact
capture succeeded on the first overlay click, so no provisional artifact was
created and none needs deleting.

No evidence-access recovery was required: the reviewer read the repository at
`stage_commit` through the connector and cited specific line ranges from the
allow-listed paths, so no archive upload was needed.

## Terminal order

```text
exact raw -> provenance intake -> (no heartbeat to delete) -> PM reconciliation
```

Archived raw and this record are complete. Reconciliation follows separately.
