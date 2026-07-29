# Mechanical intake — transport facts only

No scientific classification here.

```text
round         20260729_d7_s_r5_derangement_control
stage_commit  72a41fab3146c10caf4b802ff7635042de4ed056
branch        untied-k
reviewer      open_divergent (registered), conversation 6a63979e-35d8-83e8-8da7-10de59a5fdeb
preflight     ROUND_PREFLIGHT_READY, allow_list_count=7, archive REVIEW_EVIDENCE_ARCHIVE_READY
fence_sent    YES (once)
status        REVIEW_PENDING
```

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
