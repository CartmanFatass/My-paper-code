# Mechanical intake — 20260725_d7_design_and_prior_art

Transport facts only. No scientific classification.

```text
reviewer=open_divergent
conversation_id=6a63979e-35d8-83e8-8da7-10de59a5fdeb
branch=untied-k
stage_commit=9c63bea797142d2882a99699666532a46c2984b1
transport=project_manager_direct
status=ARCHIVED
raw=21_PRO_OPEN_RAW.md
raw_bytes=26428
raw_headings=43
```

## Submission

Preflight returned `ROUND_PREFLIGHT_READY`, 12 allow-listed evidence paths, all
present at `stage_commit`, archive builder `REVIEW_EVIDENCE_ARCHIVE_READY`.

Fence pasted from `10_FENCE.txt` via clipboard, verified byte-exact and ASCII
before paste, submitted once. Send confirmed mechanically: composer emptied and
the fence appeared as a new user turn. No second fence was submitted at any point.

## Completion

Generation confirmed active by `hmasd-review-monitor` across 80 consecutive
checks showing a live stop control. The monitor then hit 37 consecutive
45-second `document_idle` timeouts and returned `STILL_GENERATING` at ~43
minutes.

**The monitor's inference was wrong and is recorded as a transport lesson.** It
read the timeouts as "definitive evidence" of ongoing generation. A timeout is
absence of information, not evidence of activity. Its 80 stop-control
observations were real evidence; the 37 timeouts were not.

Project Manager subsequently observed, in one fully rendered snapshot, the
assistant turn following the fence with:

- the complete `Response actions` group rendered — copy, ratings, share, retry,
  more, `Sources`;
- **no** active `Stop answering` or `Stop generating` control;
- terminal closing line in this reviewer's standard form: *"This review selects
  and modifies the evidence sequence. It does not authorize implementation, a
  bounded run, or formal compute."*

The response is complete.

## Why the raw is not yet archived

The conversation now holds two very large reviewer answers, and the page no
longer reaches `document_idle`. Script injection times out on nearly every
operation.

```text
RECOVERY_ATTEMPT
attempt=1..5
boundary=screenshot / find / click on tab 507030200
action=reload the registered URL in the same tab, escalating settle time to 20s
outcome=content rendered fully on 1 of ~5 reloads; wedged again within seconds each time
```

One `Copy response` click was attempted by coordinate during a non-rendered
window. **The clipboard sentinel proved it wrote nothing** — clipboard still held
`SENTINEL_D7_ROUND_NOT_YET_CAPTURED_20260725`, length 43. This is the exact
silent-failure mode the capture procedure was written for, and the sentinel
caught it. No archive was written.

The three prohibited capture paths were not used. In particular the response was
**not** transcribed from the screenshot, and `get_page_text` was **not**
substituted — that substitution is what produced a structure-stripped archive on
a previous round.

## Resolution

Recovered on a later attempt. What worked, recorded because the same wedge will
recur as this conversation grows:

1. **A fresh tab, not another reload.** Six reloads of the original tab rendered
   once; a newly created tab on the same conversation rendered immediately. The
   accumulated renderer state, not the conversation size alone, was the problem.
2. **The clipboard write needs the button genuinely active, and the first click
   is unreliable.** Clicks landed on the right control — the screenshot showed
   the `Copy response` tooltip and the button highlighted — while the icon never
   flipped to its copied state and the clipboard stayed at the sentinel through
   two attempts. A third click on the already-hovered button succeeded.

Capture verified: clipboard changed from the sentinel, 26,428 chars, 43 markdown
headings. Written with `.NET WriteAllText` in UTF-8 without BOM; reread compares
byte-equal. Title and `Stage reviewed` field in the raw match this round's
`stage_commit`, so the archived answer is attributable to this fence and not an
earlier turn.

Three prohibited capture paths were not used at any point: no transcription from
the screenshot, no `get_page_text` substitution, no JSON round-trip. The 43
headings confirm markdown structure survived — the corrupted archive this
procedure exists to prevent had zero.

No heartbeat was created for this round; `hmasd-review-monitor` served that role
and has exited. Nothing to delete.

`recovery_exhausted=false` was the correct call — the block was transient.
