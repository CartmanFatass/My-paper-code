# Mechanical intake record — 20260730_d7_s_source_assignment_correction

Transport: `project_manager_direct`. No transport delegate.

## Boundary

```text
repository    CartmanFatass/My-paper-code
branch        untied-k
round         20260730_d7_s_source_assignment_correction
stage_commit  9cb7974563cb7de3371b1d22f3691fc00e02744d
question      docs/external-review/rounds/20260730_d7_s_source_assignment_correction/20_PRO_OPEN_QUESTION.md
reviewer      open_divergent (registration_status=registered)
conversation  6a63979e-35d8-83e8-8da7-10de59a5fdeb
```

## Preflight

`ROUND_PREFLIGHT_READY` on the first attempt, `allow_list_count=8`,
`archive_build=REVIEW_EVIDENCE_ARCHIVE_READY`. The two standing contracts were
allow-listed from the start this time — the round-7 failure is not repeated.

## Transport

1. The existing tab wedged for the **third** time this session (45 s
   `document_idle` timeouts on `find` and `screenshot`, surviving a navigate and
   two waits). Bounded replacement applied; the new tab rendered immediately.
   Exactly one tab holds the conversation.
2. **Fence-absence check: `find` gave a wrong answer and was not trusted.** Asked
   for a message containing `9cb79745`, it returned one "matching element" whose
   quoted text reads `round=20260729_d7_s` — round 7's fence — and rationalized a
   connection through the phrase "zero-compute source-assignment correction"
   appearing in Pro's ruling. `find` is semantic, not exact, and is unsound for
   proving a string absent.
3. Re-checked deterministically through the conversation API, counting exact
   substring hits across every user turn:

   ```text
   user_turns=34  exact_fence_hits=0
   ```

   Only then was submission authorized.
4. Clipboard loaded from `10_FENCE.txt` with `-Encoding UTF8`:
   `exact_match=True`, `len=399`, `ascii_only=True`.
5. Pasted with `ctrl+v`. Screenshot confirmed all seven lines present exactly
   once, `round=20260730_...`, model selector on `Pro`.
6. Submitted **once**.

## Send verification — measured, not reasoned

- Fence present as a **user turn** with `stage_commit=9cb79745...`.
- Composer empty (`Follow up` placeholder).
- `Pro thinking` visible, `Stop answering` active.

`Answer now` was visible and was **not** clicked.

## Capture

Generation completed after `Worked for 8m 27s`. The answer node was located
through the conversation API first — walking the child chain from the fence to the
longest assistant `text` node, `d196a64d-b0b4-43d3-9daa-3747bf121bdf`, 21990
chars — which fixed *which* turn to capture before any click.

The tab wedged a **fourth** time mid-capture (45 s timeout on `scroll`). The
ruling was never at risk: it is server-side and its node id was already known.
Bounded replacement applied; the new tab rendered at the bottom of the answer.

The first `Copy response` click did not land — the sentinel survived:

```text
still_sentinel=True  clip_len=29
```

Retried after a body click to take focus:

```text
still_sentinel=False  clip_len=22936  has_title=True  has_final=True  has_b1=True
```

Archived via `UTF8Encoding($false)`: `written_len=22936`,
`exact_roundtrip=True`, `bom_free=True`.

**The sentinel earned its keep twice now.** In both rounds the first copy click
silently failed, and in both the naive check would have passed on stale content —
round 7 on the fence, this round on the sentinel itself had I only tested for
non-emptiness.

## Status

`CLOSED`. Ruling archived byte-exact; reconciliation written in
`30_PM_SCIENTIFIC_RECONCILIATION.md`.

Verdict: **FREEZE AFTER MODIFICATION**; repair scope **(b1) plus a universal
final injectivity assertion, not (b2)**; the conformance suite must be frozen
before the repair and demonstrate red-to-green.

## Note for later rounds

Two capture-time traps have now each cost a cycle and both share a shape — a
check that can pass on the wrong thing:

- the **fence contains the stage_commit**, so `clipboard.Contains(commit)` cannot
  distinguish a captured ruling from the fence you just sent (round 7);
- **`find` matches semantically**, so it can report a hit for a string that does
  not occur (this round).

Both are defeated the same way: assert something the wrong answer cannot satisfy
— a length and a title, or an exact substring count from the API.
