# Mechanical intake record — contract-grill design round

```text
round=20260725_contract_grill_design
stage_commit=a859bc4ac535fc91d5e618b2934d83e189051336
branch=untied-k
fence_sent=once
continuation_sent=once (11_CONTINUATION_1.txt)
generation_time=10m 27s
answer_now_clicked=never
raw=21_PRO_OPEN_RAW.md
archive_fidelity=DEGRADED -- see below
```

## Transport history

This round took four transport attempts and two operator recoveries. Recorded in
full because the failure modes are reusable, not because the round was unusual.

1. Fence composed from the committed artifact, clipboard-verified, pasted once,
   confirmed as exactly one new user turn. **Never resubmitted thereafter.**
2. Generation errored three times with a generic ChatGPT failure and a `Retry`
   control; each retry resumed generation. After the third, the tab wedged into a
   persistent `document_idle` timeout across every read tool and survived a full
   reload. Reported as a blocker; the user cleared the tab manually.
3. On resume, the fence was still the last turn with **no assistant answer** and
   no retry affordance — the generation had died on a delivery timeout. A second
   exchanger correctly refused to use `Edit message`, which would have
   functionally duplicated the assignment, and stopped rather than improvising.
4. The user approved one short continuation that deliberately does not restate
   the assignment. It was sent once; generation ran 10m 27s and completed.

At no point was a second fence sent. The accepted fence remains the only copy of
the assignment in the reviewer's context.

## Archive fidelity — degraded, and why

**The raw archive is rendered text, not the message source.** Verified by
comparison against the previous round, which was captured with the page's
`Copy response` control:

| Round | markdown headings | bold markers |
|---|---:|---:|
| `20260725_g20r2_prefreeze_grill` (Copy response) | 48 | 26 |
| this round | **0** | **0** |

The content is semantically complete — 33,935 bytes, all sections present, ending
at the ruling's true final line — but every structural marker is gone.

Cause: the skill specified completion detection, sanity checks and a
byte-equality reread, but **never specified how to capture the text**. Three
transport passes therefore improvised three different captures, each corrupt in a
different way: a coordinate click that silently did nothing and left stale
clipboard content reading as success; a retype that differed at byte 47; and a
`ConvertFrom-Json` round trip that turned em dashes into mojibake. This round's
pass fell back to `get_page_text`, which is rendered output — and a byte-equality
reread of a file against itself cannot detect that.

`Copy response` is now the specified method in the skill.

## Open transport finding, unresolved

Clicking `Copy response` **by element `ref` reports success while writing nothing
to the clipboard** — observed twice here, verified against a pre-set sentinel.
The clipboard write appears to need a real user gesture on a focused document.
The one capture that did work used a coordinate click located from a screenshot.

Also: `find` returns the `Response actions` control for whichever assistant turn
is currently rendered. Before scrolling to the true end of the answer, it
resolved to a *different, earlier* response in this same conversation. A capture
taken at that point would have archived the wrong message entirely while passing
every check the skill then had.

Both are now written into the skill. Neither has been re-validated end to end.

## Consequence for reconciliation

The ruling's content is usable and reconciliation may proceed on it. The archive
is **not** byte-exact and must not be cited as such. If a byte-faithful record is
needed later, re-capture with `Copy response` from the live conversation while it
remains available.
