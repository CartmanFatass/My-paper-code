# Mechanical intake record — 20260730_d7_s_conformance_suite_freeze

Transport: `project_manager_direct`. No transport delegate.

## Boundary

```text
repository    CartmanFatass/My-paper-code
branch        untied-k
round         20260730_d7_s_conformance_suite_freeze
stage_commit  ffabb41f83312e8606a99a114c9803404a7735a1
question      docs/external-review/rounds/20260730_d7_s_conformance_suite_freeze/20_PRO_OPEN_QUESTION.md
reviewer      open_divergent (registration_status=registered)
conversation  6a63979e-35d8-83e8-8da7-10de59a5fdeb
```

## Preflight

`ROUND_PREFLIGHT_READY` first attempt, `allow_list_count=8`,
`archive_build=REVIEW_EVIDENCE_ARCHIVE_READY`.

## Transport

1. Existing tab reused — it had **not** wedged this time, so no replacement.
2. Fence-absence checked through the conversation API, **not** `find`:

   ```text
   user_turns=35  exact_fence_hits=0
   ```

   `find` is semantic and returned a wrong answer on this same conversation last
   round; it is no longer used for exact-string absence.
3. Clipboard loaded from `10_FENCE.txt` with `-Encoding UTF8`:
   `exact_match=True`, `len=391`, `ascii_only=True`.
4. Pasted with `ctrl+v`; screenshot confirmed all seven lines present exactly
   once, `round=20260730_d7_s_conformance_suite_freeze`, model on `Pro`.
5. Submitted **once**.

## Send verification — measured, not reasoned

- Fence present as a **user turn** with `stage_commit=ffabb41f...`.
- Composer empty (`Follow up` placeholder).
- `Pro thinking` visible, `Stop answering` active.

## What is under review

The frozen conformance suite (step 1 of Pro's red-to-green procedure) and its
recorded pre-repair baseline (step 2): 6 failed, 4 passed, 4 xfailed across the
six mandatory positive witnesses and eight mandatory paired negatives.

The question puts three of my own unforced choices up for rejection: freezing the
action-provenance interface as contract rather than letting the repair define it;
P5 as a case that must stay green rather than go red-to-green; and N4 built on a
deliberately injective map so a shape-only check cannot detect its violation.

## Status

`AWAITING RESPONSE`. `21_PRO_OPEN_RAW.md` does not exist yet and no
reconciliation may be written until it does.
