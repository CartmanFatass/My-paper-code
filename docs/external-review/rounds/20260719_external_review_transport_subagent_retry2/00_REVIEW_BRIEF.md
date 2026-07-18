# External Review Transport Subagent Self-Test Retry 2

## Purpose

Validate the five-stage HMASD external-review workflow after replacing the
stale persistent Gemini Codex Exchange with one depth-one transport subagent.
This is an operational test only; it does not review an algorithm or authorize
implementation or experiments.

## Transport Under Test

- Gemini operator: one `gpt-5.6-terra` subagent at `medium` reasoning.
- Gemini session: existing Antigravity conversation
  `111dc970-bd72-4d67-8d7a-caea65394b78` with Gemini 3.1 Pro (High).
- CLI mode: interactive PTY, with each requested tool inspected individually.
- The transport submits one single-line `@path` document pointer to
  `10_GEMINI_DIVERGENT_QUESTION.md`; all substantive instructions remain in
  tracked files and no multiline prompt is typed into the TUI.
- Exact handoff line:
  `Read @docs/external-review/rounds/20260719_external_review_transport_subagent_retry2/10_GEMINI_DIVERGENT_QUESTION.md and follow it exactly.`
- Only read-only commands confined to the allowlist may be approved once.
- `--dangerously-skip-permissions`, model override, persistent Codex Exchange,
  heartbeat, automation, and duplicate dispatch are forbidden.
- Pro roles retain their registered visible Pro conversations.

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
- no model override, alternate session, retry, regenerate, heartbeat, shell
  sleep, persistent Exchange, or permission bypass is used.

## Scientific Boundary

All returned content is workflow-test evidence only. It cannot promote, retire,
or modify any HMASD algorithm or experiment.
