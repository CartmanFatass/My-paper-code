# Disposition: PASS_FULL_WORKFLOW_SMOKE

## Accepted verdict

The convergent reviewer returned `PASS_FULL_WORKFLOW_SMOKE`. The current direct
external-review workflow is cleared for the next tracked scientific round.
This disposition is transport-only and has no algorithm, implementation, or
experiment authority.

## Verified path

- Code Implementation Manager route self-test: callback received; route stayed
  `gpt-5.6-sol / ultra` before and after delivery.
- Experiment Monitor route self-test: its archived registered task was restored
  in place, callback received, and route stayed `gpt-5.6-luna / medium`.
- Gemini divergent: the registered Antigravity Gemini 3.1 Pro (High) conversation
  read the allowlisted local files and returned a validated exact raw.
- Open divergent: the registered GPT-5.6 Pro browser conversation read the
  pinned Git evidence and returned a validated exact raw.
- Convergent: the registered GPT-5.6 Pro browser conversation read both raws and
  reconciliation, returned `PASS_FULL_WORKFLOW_SMOKE`, and its Exchange sent the
  unique terminal callback.
- All persistent Codex deliveries preserved their pre-send `hostId`, task ID,
  model, and thinking values. The controller route also remained unchanged.
- The convergent heartbeat was deleted after callback; no review heartbeat from
  this round remains.

## Repairs retained

1. All tracked Gemini launchers permanently include the explicitly approved
   `--dangerously-skip-permissions` flag while retaining plan mode, sandbox mode,
   the registered conversation, and manifest scope.
2. A visible Pro `立即回答` control is a waiting state handled by the owning
   Exchange heartbeat, not a terminal failure and never a control to click.
3. Required response fields come only from the question at the assigned commit.
4. Gemini recovery validates a satisfactory existing raw and returns it
   idempotently instead of resubmitting or overwriting it.
5. Registered persistent routes have a communication-only self-test that does
   not start role work or create a heartbeat.

## Remaining non-blocking risks

- `--dangerously-skip-permissions` relies on sandbox, manifest instructions and
  reviewer compliance rather than a machine-enforced per-path allowlist.
- Callback and heartbeat deletion are live tool evidence rather than permanent
  round artifacts; this smoke verified them directly at terminal closure.

No further transport smoke is required before the next tracked scientific
review round.
