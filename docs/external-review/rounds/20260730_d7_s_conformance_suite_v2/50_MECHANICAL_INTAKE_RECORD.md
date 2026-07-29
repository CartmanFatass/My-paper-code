# Mechanical intake record — 20260730_d7_s_conformance_suite_v2

Transport: `project_manager_direct`. No transport delegate.

## Boundary

```text
repository    CartmanFatass/My-paper-code
branch        untied-k
round         20260730_d7_s_conformance_suite_v2
stage_commit  34f148e47b6779065246f5bc0caafe4dbbb8bf4c
question      docs/external-review/rounds/20260730_d7_s_conformance_suite_v2/20_PRO_OPEN_QUESTION.md
reviewer      open_divergent (registration_status=registered)
conversation  6a63979e-35d8-83e8-8da7-10de59a5fdeb
```

## Preflight

`ROUND_PREFLIGHT_READY` first attempt, `allow_list_count=8`,
`archive_build=REVIEW_EVIDENCE_ARCHIVE_READY`.

## Transport

1. Existing tab reused.
2. First API call returned `TypeError: Failed to fetch` — the page had lost its
   session context. Re-navigated; the same call then succeeded. **Not** treated as
   evidence about the fence either way.
3. Fence absence proved through the conversation API, never `find`:

   ```text
   user_turns=36  exact_fence_hits=0
   ```

4. Clipboard loaded from `10_FENCE.txt`: `exact_match=True`, `len=383`,
   `ascii_only=True`.
5. **The first `ctrl+v` did not land** — the composer still showed its
   placeholder. Detected by screenshot rather than assumed from the tool result,
   which reported the keypress as successful. Clicked the composer, waited, and
   pasted again; the second attempt landed.
6. Screenshot confirmed all seven lines present exactly once,
   `round=20260730_d7_s_conformance_suite_v2`, model on `Pro`.
7. Submitted **once**.

> A failed paste is the mirror of the failed copies in rounds 7 and 9: the tool
> reports the gesture, not its effect. Nothing was submitted while the composer
> was empty, so there was never a duplicate risk — but "the keypress succeeded"
> is not "the text is in the composer".

## Send verification — measured, not reasoned

- Fence present as a **user turn** with `stage_commit=34f148e4...`.
- Composer empty (`Follow up` placeholder).
- `Pro thinking` visible, `Stop answering` active.

## What is under review

The **amended** conformance suite and baseline v2 (`4 failed, 3 passed,
14 xfailed`), addressing all five blocking issues from the previous round.

The question additionally puts up for ruling the one amendment that could not be
made honestly: **P6e asserts production integration by grepping `step_once`'s
source text.** That passes on a comment and fails if the repair integrates by a
different route — which is the realization freedom Pro explicitly granted. It is
the same defect class the previous round rejected, so it is flagged rather than
presented as equivalent to the others.

## Status

`AWAITING RESPONSE`. `21_PRO_OPEN_RAW.md` does not exist yet and no
reconciliation may be written until it does.
