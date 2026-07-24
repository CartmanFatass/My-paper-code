# Handoff

Date: 2026-07-24
Branch: `untied-k`
Successor orchestrator: Fable, fresh conversation
Reason: user pause immediately before the first `hmasd-implementer` spawn

Read `AGENTS.md`, then this file, then `docs/project/CURRENT_WORK.md`.

## Terminal state

No process is running. No formal or nonformal compute was launched. Everything
is committed and pushed to `origin/untied-k`; `aggressive` stays untouched at
`4af01cd`.

## What this session completed

1. **Bootstrap round reconciled** — `8a7a2a6`. Pro's verdict is adopted in
   `docs/external-review/rounds/20260724_untied_k_direction_bootstrap/30_PM_CODE_SIDE_RECONCILIATION.md`:
   per-agent variable period is a conditional P1 candidate only; the root
   cause is action authority and credit factorization; periodic sampled `Z`
   is replaced by deterministic read-time context `C` in the primary
   candidate; G20 continues, broadened.
2. **Timing–credit identifiability derivation** — `36ed97f`, at
   `docs/research/cdc/EVIDENCE_NOTES/20260724_TIMING_CREDIT_IDENTIFIABILITY_G20_DERIVATION.md`.
   Branch `NO_SCHEDULE_INFORMATION_CHANGE`: schedules only rescale one shared
   scalar contrast, so `k -> k_i` alone is formally excluded per Pro's
   pre-registered mapping. P2 is eligible for an implementation proposal;
   P1 stays gated on heterogeneous tempo.
3. **P2 design frozen** —
   `docs/research/designs/ACTIVE_SET_CENTERED_COUNTERFACTUAL_RESIDUAL_G20.md`:
   exactly centered observation-only pre-tanh residual over the active set,
   plus member-resolved leave-one-out counterfactual advantage
   `[time,batch,member]` from a slow action-critic. Screen mirrors the G19
   protocol and thresholds with fresh seeds (2619000–2739000 block). No
   projection, Adam everywhere, base policy file untouched.

## Exact next action

Spawn `hmasd-implementer` (synchronous, watch the first lap) with the bounded
assignment: build exactly
`ha_ctse_process/centered_residual_g20.py`,
`scripts/screen_centered_counterfactual_residual_g20.py`,
`tests/ha_ctse_process_centered_residual_g20_test.py`
against the frozen design, template `anchored_residual_g19.py`, focused tests
plus the G19 suite as shared-surface guard, no Git, no screen execution. The
spawn was fully prepared this session but interrupted by the user pause — it
has NOT run. After it: `hmasd-verifier` fresh check, one `hmasd-reviewer`
advisory (new protected credit semantics), PM acceptance and commit, then
`hmasd-experiment-operator` executes the bounded screen. Stages 2, 4 and 5 of
the cycle are still unexercised.

## Execution mode

```text
execution_mode=authorized
autonomous_research_grant=ACTIVE_TEN_ITERATION_TOY_FIRST_UAV_PROMOTION_CHAIN
grant_extension_20260724=user_plus_12_iterations
iterations_remaining=20
grant_unit=completed_workflow_cycle
intermediate_authorization_prompts=forbidden
```

Reconciliation, derivation and design consumed zero iterations; the bounded
screen consumes zero as well. Only a formal run consumes one.

## Continuity

`CURRENT_WORK.md` carries the full boundary keys (`untied_k_*`, `g20_*`).
Setup for a fresh clone: `git config core.hooksPath .githooks`. Known open
items 1–3 from the previous handoff (grant-renewal brief template, untracked
third-party skill pack, deferred UAV G1 formal run on `aggressive`) are
unchanged and still open.
