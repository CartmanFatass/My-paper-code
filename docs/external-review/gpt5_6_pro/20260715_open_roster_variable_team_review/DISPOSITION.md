# GPT-5.6 Pro Variable-Team / Open-Roster Disposition

Date: 2026-07-15

Source model: GPT-5.6 Pro (`Pro` web conversation), two user-returned responses

Reviewed repository anchor named by the responses: `aggressive@ffa18c3`

Controller state at disposition: `aggressive@c6d02e3` plus the tracked current-work update

Raw evidence:

- `GPT5_6_PRO_RESPONSE_RAW_1.md`
- `GPT5_6_PRO_RESPONSE_RAW_2.md`

Related claim: whether variable team membership and variable skill lifetime can
be combined without abandoning MAT-style autoregressive coordination or causing
combinatorial computation.

## Verdict

- **Accept** open-roster control as a distinct, promising architecture axis.
  The strongest causal object is not variable `N` alone, but the separation of
  membership transitions from surviving agents' skill renewal.
- **Accept** the distinction among cross-episode variable `N`, temporary
  availability, and true within-episode join/leave. They have different hidden
  state, GAE, buffer, and lifetime semantics.
- **Accept with modification** a mask-aware, set-equivariant high-level policy
  with active-only autoregressive KEEP/SET decoding. Sampling and replay must
  store the active set, membership epoch, external order, and actual prefix.
  This remains MAT-style token PPO; it does not inherit the full fixed-team MAT
  theorem automatically.
- **Accept** `initial SET` for joiners, membership-censored termination for
  leavers, and uninterrupted hidden/skill/age state for surviving members.
- **Accept** the prohibition on team-size, join, survival, or benchmark-specific
  intrinsic rewards.
- **Modify** the proposed initial architecture. Use padded storage and a
  mask-aware set representation first. Do not commit yet to sparse graph plus
  inducing slots, fixed `M=8`, a low-critic rewrite, or any quoted capacity and
  performance thresholds; those are unregistered candidates, not evidence.
- **Defer** learned admission/membership selection. The first open-roster edge
  uses exogenous availability/membership. If membership later becomes a policy
  action, it requires its own likelihood, slow-clock credit, and resource
  constraint; it cannot be represented as an environment mask.
- **Reject** replacing the active native-HMASD toy objective with `R39-OR0` or
  an immediate S7 wiring/320K run. The responses used an older repository
  anchor, conflict with the active R39 identifier, and do not close the already
  localized native joint-credit boundary.
- **Defer** any novelty claim for `Membership-Aware Asynchronous Skill SMDP`
  until a dedicated literature boundary and causal result exist.

## Accepted Sequence

1. Complete the current fixed-`N` native-HMASD toy anchor with the original
   coordinator likelihood and native team/agent high-level credit.
2. If that anchor passes, add the smallest exogenous active-mask/set-roster arm
   on the same toy and exercise permutation, padding, and replay invariance as
   part of that evidence-bearing run rather than a separate audit workflow.
3. Test cross-episode variable `N`, then within-episode membership censoring.
4. Only after those edges work, compare full refresh, shared/fixed lifetime, and
   per-agent KEEP/SET under the same dynamic-roster contract.
5. Move to S7 only after the corresponding toy gate, preserving the user's
   toy-first iteration requirement.

This review therefore changes the future research map, but it does not replace
the immediate action in `memory/CURRENT_WORK.md` and does not register a new
formal experiment.
