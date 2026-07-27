# Mechanical intake record — Stage B round two

```text
round          = 20260727_d7_s_stage_b_fingerprint_closure
stage_commit   = 8cb5a232c2928aa8d6c5c173557da96c2038a329
branch         = untied-k
reviewer       = open_divergent (registered), conversation 6a63979e-35d8-83e8-8da7-10de59a5fdeb
transport      = project_manager_direct
preflight      = ROUND_PREFLIGHT_READY, allow_list_count=10
reasoning_time = 12m 56s, as reported by the page
raw            = 21_PRO_OPEN_RAW.md, 16362 chars
raw_sha256     = E45BA632532D22248FE9E043A8936D4929E0594DB2B560937A0B3CA5A8DA5E5E
```

## Send verification

Mechanical, not inferred: before pasting, the conversation contained two
`CURRENT_REVIEW_ASSIGNMENT` turns and none naming this round. After one click of
send, the composer was **empty** and the fence appeared as a user turn carrying
all six identity fields. Generation was then active (`Pro thinking`, live
`Stop answering`).

`Answer now` was visible for the whole 12m 56s and was never clicked.

## Two transport failures, both caught by a check rather than by luck

**The tab wedged twice**, both times while rendering a large answer: every
script-injecting operation timed out and survived a reload. Recovered by the
documented replacement path — two reload-and-wait attempts, then close and
recreate. Exactly one tab held the conversation at each finish. The replacement
tab rendered immediately on both occasions, which is the same signature the
skill records.

**The first two capture attempts archived the wrong text.**

1. Clicking the copy control without first giving the page focus did not fire at
   all. The clipboard still held the fence from the send step, so a 397-char
   "ruling" was written to `21_PRO_OPEN_RAW.md`. Caught by asserting the capture
   contains the verdict string; the file was deleted, not amended.
2. Re-resolving the control by reference then copied the **previous round's**
   ruling (`4b9977b5`, `MISMATCH`) — ChatGPT virtualizes the transcript, so the
   only rendered `Copy response` belonged to the first assistant turn. Caught by
   asserting the capture carries this round's `stage_commit`.

Fixed by scrolling the last turn's action row into view, clicking the page body
once to take focus, then clicking copy. A sentinel value was written to the
clipboard before each attempt, which is what distinguished "the copy did not
fire" from "the read is stale" — without it both failures look identical.

**Rule this produced:** a capture is not archived until it has been asserted to
carry the round's own `stage_commit`. Length and non-emptiness prove nothing; the
first bad capture was non-empty and the second was 18322 characters of a real
ruling for a different round.

## Fidelity

Captured through the page's own `Copy response`, never transcription. The
archive preserves 27 markdown headings and 70 backticks, so it is source
markdown rather than rendered page text — the failure mode that cost an earlier
archive. Written UTF-8 without BOM and re-read byte-exact.
