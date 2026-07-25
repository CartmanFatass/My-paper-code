# Mechanical intake — 20260725_d7_2b_source_persistence_necessity

Transport facts only. No scientific quality classification; that belongs to the
Project Manager's separate reconciliation after exact archival.

```text
round             20260725_d7_2b_source_persistence_necessity
stage_commit      c4c14175184f7fc31d7f15fae4e9d6e97e078bd2
question          docs/external-review/rounds/20260725_d7_2b_source_persistence_necessity/20_PRO_OPEN_QUESTION.md
fence artifact    docs/external-review/rounds/20260725_d7_2b_source_persistence_necessity/10_FENCE.txt
branch            untied-k
reviewer role     OPEN_DIVERGENT  (registry registration_status = registered)
conversation_id   6a63979e-35d8-83e8-8da7-10de59a5fdeb
transport         project_manager_direct
status            WAIT_FOR_RESPONSE
```

## Preflight

`preflight_review_round.ps1 -Commit c4c1417... -RoundPath <round> -Branch untied-k`
returned `ROUND_PREFLIGHT_READY`:

```text
allow_list_count  12
archive_build     REVIEW_EVIDENCE_ARCHIVE_READY
```

One preflight failure was found and fixed before this run: the allow-list was
missing both standing contracts (`docs/project/ALGORITHM_PRINCIPLES.md`,
`docs/external-review/OPEN_REVIEW_PRINCIPLES.md`). The freshness fence names only
the question, so a path outside its allow-list never reaches the reviewer.

## Fence absence, proved before submission

Counted by DOM inspection of `[data-message-author-role="user"]` rather than
inferred:

```text
user_turns        4
assistant_turns   3
fence_blocks      2
rounds_seen       20260725_research_direction_and_ledger
                  20260725_d7_design_and_prior_art
my_fence_present  0
```

**Discrepancy recorded.** `CURRENT_WORK.md` carried
`contract_grill_fence_sent=exactly_once_confirmed_as_a_real_user_turn` for the
retired round `20260725_contract_grill_design`. That fence is **not** in this
conversation — only the two blocks above exist. That round is retired as a
mechanism and nothing depends on its answer, and it creates no duplicate risk for
this round, but the earlier record was wrong.

## Composer verification, before submitting

Fence loaded to the clipboard from the committed artifact, `-Encoding UTF8`,
`byte_identical=True`, `length=635`, `ascii_only=True`. Pasted with `ctrl+v`; never
typed, because a newline in this composer submits.

```text
header_count      1
round_count       1
commit_ok         true
branch_ok         true
repo_ok           true
question_ok       true
instruction_ok    true
```

## Send, verified by measurement

```text
composer_empty    true
user_turns        4 -> 5
my_fence_turns    1
```

## Tab state

A fresh session held **no tab group at all**, so the previously reported wedge of
this conversation did not recur and no wedged tab was inherited. One tab was
created and navigated to the registered URL; it rendered immediately.
`tabs_context_mcp` confirms exactly one tab holds the conversation.

## Recoveries

```text
RECOVERY_ATTEMPT
attempt=1
boundary=hmasd-review-monitor wait task
action=agent terminated early on a transient server-side API error (529 Overloaded)
       while generation was still active; its last observation was `Stop answering`
       present with unchanged visible text. Resumed the same agent from its
       transcript rather than dispatching a second one, so its tab resolution and
       quoted criteria carry over, and instructed it to re-resolve the tab id.
outcome=resumed; still WAIT_FOR_RESPONSE. No submission, no capture, nothing
       archived. The failure was in the waiting agent, not in the round.
```

```text
RECOVERY_ATTEMPT
attempt=2
boundary=screenshot / zoom script injection on the registered tab
action=script injection timed out (5s, then 45s) after the answer completed --
       the documented wedge symptom, on a conversation now holding a fourth
       assistant turn one of which is 20k characters. Reload-and-wait once
       restored it; it wedged again during capture.
outcome=recovered temporarily, then re-wedged. Escalated to attempt 3.

RECOVERY_ATTEMPT
attempt=3
boundary=Copy response click writing nothing to the clipboard
action=three coordinate clicks on the control left the sentinel unchanged, which
       is the documented silent-failure mode -- the tool reports success for the
       click whether or not the clipboard write happens. Per the bounded ladder,
       closed the wedged tab, created one, navigated to the registered URL, and
       re-scrolled to the true end of the answer.
outcome=fresh renderer served the same message id 9e75c58b-1bd2-48b6-a904-d6f4af9cf3d8
       at the same length, and the next click captured. Exactly one tab holds the
       conversation, confirmed by tabs_context_mcp.
```

## Completion evidence

Two stable snapshots from distinct inspections, five seconds apart:

```text
message id     9e75c58b-1bd2-48b6-a904-d6f4af9cf3d8   identical across both
innerText len  20160                                  identical across both
head / tail    identical across both
stop controls  0
retry controls 0
continue / Answer now controls  0
```

The response is attributable to this round's fence rather than an earlier turn: its
own second line reads `**Stage reviewed:** c4c14175184f7fc31d7f15fae4e9d6e97e078bd2`.

`Answer now` was never clicked, and no control that curtails extended thinking was
operated at any point.

## Capture

Captured with the page's own `Copy response` control against a pre-set clipboard
sentinel, then written with `.NET WriteAllText` and reread:

```text
sentinel before      D7_2B_CAPTURE_SENTINEL_20260725_c4c1417
clipboard changed    true
captured length      23437   (markdown source)
rendered innerText   20160   (the 3277 difference is markdown syntax, which is
                              why rendered text is a prohibited capture path)
raw path             21_PRO_OPEN_RAW.md
reread length        23437
byte_equal           true
file bytes           23509   (UTF-8 multibyte)
```

Sanity checks before writing: not a progress trace; addresses the numbered asks
(it opens with an explicit disposition on the retirement); size plausible for a
scoped scientific answer.

## Heartbeat

No Project-Manager-owned heartbeat was created for this round. The wait was done by
`hmasd-review-monitor`, which holds no click, type or write tools. It terminated
once on a transient API error and was resumed from its transcript; it reported
`GENERATION_STOPPED` from a **single** observation after the page wedged, so its
report was treated as unverified and the two-snapshot check was performed directly
by the Project Manager before any capture. Nothing to delete; absence confirmed.

## Terminal

```text
exact raw -> provenance intake -> heartbeat absence confirmed -> PM reconciliation
```

Reconciliation is a separate Project Manager document and is not part of this
transport record.
