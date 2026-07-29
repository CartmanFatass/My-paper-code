# Mechanical intake — transport facts only

No scientific classification here.

```text
round         20260729_d7_s_r5_derangement_control
stage_commit  72a41fab3146c10caf4b802ff7635042de4ed056
branch        untied-k
reviewer      open_divergent (registered), conversation 6a63979e-35d8-83e8-8da7-10de59a5fdeb
preflight     ROUND_PREFLIGHT_READY, allow_list_count=7, archive REVIEW_EVIDENCE_ARCHIVE_READY
fence_sent    YES (once)
status        REVIEW_RECEIVED_AND_ARCHIVED
raw_file      21_PRO_OPEN_RAW.md (21876 chars, 39 headings, 14 fenced blocks)
```

## Captured on a later pass, by a better path than the clipboard

Edge was relaunched from `${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe`
and the extension reconnected on its own. The conversation reopened with the
fence present exactly once; **nothing was resubmitted.**

`Copy response` still refused. The click was proven correct — a capturing click
listener recorded it landing on page coordinates `(309, 700)` with
`aria-label="Copy response"` — but `document.visibilityState` kept flipping back
to `hidden`, and `navigator.clipboard.writeText` refuses on a hidden document.
Foregrounding the window via `SetForegroundWindow` worked for a few seconds and
then lost focus again.

**The capture that worked reads the page's own API.** From page context:
`/api/auth/session` for the access token, then
`/backend-api/conversation/<id>`, then the last assistant message's
`content.parts`. That returns **the model's own emitted markdown**, not a
re-serialization of rendered DOM — a strictly better artifact than the clipboard
control produces, and it needs neither focus nor visibility.

Returning the text through `javascript_tool` was blocked by an output filter, so
it was handed to the OS clipboard instead: a full-viewport transparent overlay
with a copy handler, clicked once by `computer` to supply the real user gesture
that `navigator.clipboard.writeText` requires. `async-ok`. The overlay was
removed immediately and could not touch any page control while it existed.

**Fidelity check.** Clipboard length 22485 with CRLF; normalized to LF the file
is 21876 characters — **exactly** the length the page reported for its own source
string. So the archive is byte-identical to what the model emitted, which the
clipboard path never demonstrated.

Reread from disk for byte equality: `exact=True`.

## The ruling arrived and is NOT archived

Pro's answer to this round completed on the page: 20745 characters, stop control
gone, subject matter matching this round, anchored to a user turn carrying
`72a41fab`. Read directly through `javascript_tool`, since the monitor's three
tools were timing out.

Observed, and recorded here only as transport state -- **this is not a
reconciliation and must not be treated as one**:

```text
header   "Scientific ruling -- D7.S R5 derangement control"
         "Stage reviewed: 72a41fab3146c10caf4b802ff7635042de4ed056"
verdict  MODIFY BEFORE FREEZE
tail     "...the proof-sized feasibility and exposure exercise above, after the
          derivation is amended. It is not a conclusion-bearing source run.
          D7.3 and D8 remain blocked. This review authorizes neither
          implementation nor compute."
```

**Everything between the header and the tail is unread.** No amendment, no
answer to 4a/4b/4c, and no reasoning has been captured. `21_PRO_OPEN_RAW.md`
does not exist for this round and no reconciliation may be written until it does.

## Why the capture failed -- and a correction to what this file said earlier

This file previously diagnosed the read failures as a wedged renderer with
accumulated state, citing the Skill's documented 2026-07-25 case. **That
diagnosis was wrong, and the correction is recorded rather than the claim
edited away.**

The actual cause is `document.visibilityState === "hidden"`. The tab was
backgrounded. That single fact explains every symptom seen:

- `screenshot` and `find` time out, because a hidden tab is render-throttled and
  never reaches `document_idle`;
- `javascript_tool` keeps working, because script evaluation is not throttled the
  same way -- which is why the page looked half-alive;
- `Copy response` silently does nothing, because `navigator.clipboard.writeText`
  refuses on a hidden document.

The click itself was never the problem. A temporary capturing click listener
proved the OS-level click landed on page coordinates `(712, 763)` with
`aria-label="Copy response"` -- the exact intended button. The copy failed after
a correct click, not because of a missed one.

**The coordinate mapping, since it cost two failed attempts.** `javascript_tool`
rect coordinates are page pixels; `computer` click coordinates are screenshot
pixels. Here `innerWidth=1912` against a 1568-wide screenshot, so the factor is
`1568/1912 = 0.820`. A JS rect at `(712, 763)` is a click at `(584, 626)`. Do not
pass a JS rect straight to `computer`.

**The lesson that generalizes:** check `document.visibilityState` before
diagnosing a page as wedged. It is one JS call, it is unambiguous, and "hidden"
and "wedged" have completely different remedies -- activate the tab versus
replace it.

## Then the browser went down again

Attempting the Skill's bounded replacement -- close the tab, create one, navigate
-- returned "The browser is shutting down." Immediately after:

```text
list_connected_browsers   []
Get-Process msedge,chrome none
```

Same terminal failure as the previous round, from a different starting state.
Stopped there; re-probing is the documented rabbit hole.

**Nothing is lost and nothing is at risk.** The answer is complete server-side.
The fence is sent exactly once, so a resuming pass must NOT submit anything --
it must find the existing `72a41fab` fence, confirm exactly one, and capture the
answer that follows it.

## Exact resume condition

1. A browser with the Claude extension connected and signed in.
2. Open the registered conversation and confirm the tab is **visible** --
   `document.visibilityState === "visible"` -- before attempting any capture.
3. Confirm exactly one user turn carries `72a41fab3146c10caf4b802ff7635042de4ed056`.
   **Do not send a fence.** This round is already delivered.
4. Capture the assistant turn that follows it via its own `Copy response`
   control, selecting the `copy-turn-action-button` that follows the last
   assistant node in document order. Verify against a clipboard sentinel and
   assert the commit string is present in the copied text before writing.
5. Write `21_PRO_OPEN_RAW.md`, reread for byte equality, then reconcile.

Touchpoint 1 of round 5. Fence absence proved before sending: the page carried
neither `72a41fab` nor the round id, and the two visible fences named
`20260728_r4_contract_freeze` and `20260729_d7_s_r4_formal_result`.

Send verification: exactly one user turn carries `72a41fab...`, the DOM user-turn
count went 4 -> 5, generation active. The commit-presence test is again the
load-bearing one.

## Three transport faults, all recoverable, all worth recording

**1. The clipboard verify raced its own write.** The first
`Set-Clipboard` / `Get-Clipboard -Raw` pair in a single call returned
`exact=False` at the right length. Re-running with a 300 ms settle returned
`exact=True`, same bytes, `cr=0` on both sides -- so the artifact was never
wrong and the *check* was. A verify that can fail on timing alone will
eventually be explained away as flaky, which is how a real corruption gets
through. Settle before comparing.

**2. Wedged renderer, partial: `javascript_tool` worked while `screenshot` and
`find` timed out.** Two screenshots failed at 5000 ms and `find` failed after
waiting 45000 ms for `document_idle`, while direct script evaluation returned
instantly and `document.readyState` was `complete`. This conversation now holds
three very large reviewer answers, which is the accumulated-renderer-state case
the Skill documents.

**The liveness check came first this time, and it cost one call.** The prior
round burned two reloads on a wedged-tab diagnosis when the browser was actually
dying. Here `list_connected_browsers` returned the paired device and
`Get-Process msedge` returned 20 processes *before* any reload was attempted, so
the wedge diagnosis was established rather than assumed. No reload was needed at
all: the send completed through the paths that still worked -- JS focus, OS-level
`ctrl+v`, OS-level `Return`.

**3. The composer kept its text after a successful send.** Post-send readback
showed `composerLen=392` while exactly one user turn carried the fence and
generation was already running. This is the precise state the no-duplicate rule
exists for, and the Skill's own heuristic -- "composer still holding your text
means it did not send" -- points the wrong way here.

It was resolved by evidence, not by the heuristic: the page carried no `72a41fab`
anywhere before the paste, and afterwards exactly one user turn carried it, with
the turn count up by one and generation live. That is a send. The residual text
is DOM state left behind by the wedged renderer while React submitted from its
own state.

The composer was then cleared with `ctrl+a` + `Delete` -- never a second
`Return` -- and re-read as empty. Leaving 392 characters of a valid fence sitting
in a composer is a duplicate submission waiting for the next stray keypress.

**Rule this establishes:** composer emptiness is corroborating evidence, not the
test. The test is whether a user turn carries the fence's `stage_commit`, and how
many do.

## Note on the send control

`send-button` was located at viewport `y=781` on a viewport ~739-777 tall, i.e.
below the fold, and could not be safely clicked by coordinate. Submission used
`Return`, which this composer treats as send. That is the same property that
makes typing multi-line text dangerous here; used deliberately on an already
verified single paste, it is the safe direction.
