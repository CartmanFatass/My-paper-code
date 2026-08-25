# External Review Transport Self-Test

## Purpose

Validate the current five-stage HMASD external-review transport and state
machine end to end. This round tests repository access, role separation,
single-dispatch behavior, raw archival, controller synthesis, and convergent
handoff. It does not review an algorithm, change the research portfolio, or
authorize implementation or experiments.

## Stages

1. Gemini returns one divergent workflow risk and one simplification.
2. Open Pro independently returns one divergent workflow risk and one
   simplification.
3. The controller compares the two archived raws.
4. Convergent Pro decides whether the transport evidence demonstrates a healthy
   workflow or identifies one concrete blocker.
5. The controller records a test-only disposition.

## Deadline

Each external role has a hard deadline of two hours after its verified single
dispatch. A timed-out or post-dispatch blocked role is not resubmitted in this
round.

## Success Criteria

- all three reviewers use their registered role-specific session;
- each external stage has `dispatch_count=1` exactly;
- both Pro stages verify the visible `Pro` setting;
- every response is archived before interpretation;
- each raw matches the captured completed response exactly;
- the state closes once at controller disposition;
- no model override, alternate session, retry, regenerate, heartbeat, sleep, or
  cross-task Pro relay is used.

## Scientific Boundary

All returned content is workflow-test evidence only. It cannot promote, retire,
or modify any HMASD algorithm or experiment.
