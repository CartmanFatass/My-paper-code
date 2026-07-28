# Mechanical intake record — transport facts only

```text
round         = 20260728_r4_contract_freeze
reviewer_key  = open_divergent
branch        = untied-k
conversation  = 6a63979e-35d8-83e8-8da7-10de59a5fdeb
stage_commit  = b977e1883c0037e83a39ed46c099ccf6fa2fb7de
question      = 20_PRO_OPEN_QUESTION.md
raw           = 21_PRO_OPEN_RAW.md
transport     = project_manager_direct, claude_in_chrome
touchpoint    = 3 of 3 -- the result submission, which opens the next workflow
```

## Preflight

`ROUND_PREFLIGHT_READY`, seven-path allow-list, fence present,
`archive_build=REVIEW_EVIDENCE_ARCHIVE_READY`.

## Fence

Committed artifact, clipboard round-trip `-ceq` verified, pasted once, submitted
once. Send verified mechanically: composer empty, new user turn carrying every
field, `Stop answering` active. An `Answer now` control was visible and was
**not** operated.

## Transport faults

One wedge, during the wait. Bounded replacement applied directly — reload has now
failed on this conversation in every instance tested and replacement has
succeeded in every instance, so the reload step is deliberately skipped as a
measured-failing action rather than overlooked. Recorded here so the deviation is
auditable. The replacement rendered immediately.

Exactly one tab held the conversation throughout.

## Capture

`Copy response` by coordinate with a clipboard sentinel; captured on the second
click after the neutral-body focus step — the same failure mode and fix as the
previous four rounds.

### Sanity checks, all passed

- carries **this round's own** `stage_commit` `b977e188…`;
- opens `# Scientific ruling — R4 contract completion` and addresses all five
  required sections by name;
- 20914 characters;
- first and last lines match the screen.

### Archival

`.NET WriteAllText` (UTF-8, no BOM) from the clipboard; reread
`EXACT_EQUAL=True` at 20914 characters.

## A limitation of this round's own evidence fence, recorded

The allow-list carried the audit implementation but **not** the focused test
files, the mutation-sweep evidence notes, or the pooler source. Pro therefore
declined to adjudicate the guard-closure and pooler-closure claims the question
asserted, marking them a Project-Manager-owned technical premise to be checked at
the realization gate rather than a scientific fact established by this round.

That is a defect in how I built the fence, not in the ruling: I asserted closure
using evidence the reviewer could not read. Recorded so the next fence carrying a
closure claim includes the artifacts that establish it.

## Preserved as received

LaTeX mangled by transmission; `=` runs and `##` fragments stand where display
math and subscripts were. Preserved exactly. No quantity illegible.

## Heartbeat

None created. Waiting was in-band.
