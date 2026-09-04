# SCDMP D6 recast convergence intake (2026-09-04)

- Direction: `semigroup_consistent_duration_model_policy`
- Decision tier: direction
- Workflow node: `em:semigroup_consistent_duration_model_policy:convergence`
- Request: `2026-09-04-scdmp-d6-recast-convergence-01`
- Decision authority: `PRO_FINAL`
- Archived response SHA-256:
  `95c60538bdf36b0cd78e68ef91ecd20548b7d68e473c7a5f609d27c3e2b473b7`
- Final decision: `RECAST_D6`
- Decision formed: `true`

## What this intake checked

1. The archived response bytes hash to the caller-supplied SHA-256 above.
2. Transport facts bind the response to the exact request, direction, workflow node and persistent
   convergence key. The provider conversation is
   `6a961753-0424-83e8-848c-dbe2cfe3369c`, the visible model was Pro, the underlying model was
   GPT-5.6 Sol at `5/5`, and the prompt hash equals the authored body hash
   `fdac9faabee0fbc58dc145bdd64c719a5165db26de26a46a83f8dfc81298e893`.
3. Send evidence records one click, exact prompt text, the exact user node and attachment, followed
   by `NATURAL_COMPLETION` and `ARCHIVED`. The response reports that all eight allowlisted paths
   were read at pinned ref `d39757b4b6c6111e90f8ec7025d409217b3596cb`.
4. The response ends with both `DECISION_FORMED=true` and `FINAL_DECISION=RECAST_D6`; it is not a
   connector, evidence or transport blocker.
5. The historical receipt attempted exactly once to the correct creator
   `01a06bc3-f436-73a3-903d-2c9f0cce27f9` and failed with
   `direct app-server input is not allowed for multi-agent v2 sub-agents`. Root supplied the durable
   archive directly. This intake consumes that archive and does not retry the terminal receipt.

The committed archive copies are under
`external/2026-09-04-scdmp-d6-recast-convergence-01/`. The transport facts copy has SHA-256
`b2a30b36417f8e9bff6bd1f45f4ca6387a04ae0997adf76c7374d04e20fec7ad`.

## Observation that bounds the decision

The valid B01 base run selected `PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL`, but its swapped arm
absorbed before a continuation-policy query in every raw cell, so matched-minus-swapped equalled
the matched arm's absolute return rather than a graded comparison. The A/RECON diagnostic found a
fully survivable neighbour, but its mean gap was only `0.00045788` (about `0.73%` of the matched
return), with four positive states, one zero and one negative. Those observations stop the B01
line and do not provide D6 polarity.

They also do not test the distinct D6 proposition: whether a shared duration-conditioned value
model reaches competent native `(z,k)` choices with fewer samples or updates than an untied,
same-information D8 menu. The archived decision identifies a finite native action/return
discriminator for that proposition, so the direction is recast rather than parked or closed.

## Rule applied

The decision ladder says a complete archived Pro response that decides its direction-tier question
at the declared class is final for that node. The DM executes and records it without local
override. Applied here, the archive is complete and decision-forming, so `RECAST_D6` controls. The
failed receipt is historical transport provenance and has no scientific polarity.

## Bounded reading

- B01 `RUN-02A` and `RUN-02B` remain held and are not reopened.
- The graded diagnostic remains A/RECON and carries no algorithm-effect polarity.
- FCEOV `.3` remains a consumed exact-object frozen-resolution nonpass.
- D6 is a new, outcome-informed B/EXPLORE object, not an adapter or continuation of those objects.
- A positive D6 branch can support only the shared duration-conditioned value package on the exact
  host, population, actions, data, seeds and budget in its card. It cannot establish pure duration
  semantics, general superiority, unseen-`k` transfer, D2 interruption value, invariance, safety or
  deployment readiness.

Strongest support is the independent D6/D8 treatment-null pair, a native host where duration can
change consequences, an action-linked regret estimand and a feasible B learner/evaluator route.
Strongest contradiction is that the only graded SCDMP observation is tiny and state-heterogeneous.
The surviving alternative is ordinary lower-dimensional regularization/easier optimization, or
negative transfer from heterogeneous state-by-duration values, rather than meaningful duration
structure.

## Flags for the owner and Root

- Portfolio lifecycle, priority, capacity, ownership, fusion and investment were explicitly outside
  this node. Root retains that boundary.
- The receipt failure exposes a control-plane delivery limitation only. Do not retry it or infer a
  Pro blocker.
- The new object is scientifically frozen but not launch-ready until CM's actual runner emits its
  prospective per-arm cost law and every projected arm is within the `1,800 s` cap.

## Decisions this intake produces

### 1. Direction decision

Options were `RECAST_D6`, `PARK_DIRECTION`, and `CLOSE_DIRECTION`. The archived node selected
`RECAST_D6`.

**Decision: `PRO_FINAL — RECAST_D6`.** The accepted next discriminator is
`SCDMP-D6-CROSS-K-Q-SHARING-B01`, recorded in
`SCDMP_D6_CROSS_K_Q_SHARING_B01_SCIENCE_CARD_20260904.md`.

### 2. Object-tier implementation closure before CM

The Pro answer fixes the mechanism, comparator, host row, finite population, action set, budgets,
estimands and branches but leaves concrete learner tensor widths, optimizer constants and fresh RNG
integers for the card.

Options:

1. **(a), recommended:** close those fields now with the smallest existing-SCDMP-shaped matched
   learner: a common `21→96→96` SiLU encoder, one `97→96→1` D6 head, two independent `96→96→1`
   D8 heads, per-record squared error, the existing SCDMP AdamW constants, fresh fixed integer
   domains, and a treatment-common source law using action `0` on fixed `k=7`/`k=13` clocks.
2. **(b):** leave the architecture and RNG integers to CM, which would permit implementation to
   choose scientific treatment details after the card.
3. **(c):** freeze only the pre-model gate and return for a second object before admitting the
   learner comparison, although the complete Pro decision already admits it conditionally on the
   gate.

Recommendation: (a). It is reversible before launch, keeps D8 at least as capacious as D6, and
prevents CM from silently selecting scientific meaning.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance label:
`OWNER_DELEGATED`. This selection is recorded in the 2026-09-04 audit ledger. No experiment has
run.

### 3. Receipt disposition

Options were to retry the terminal failed receipt, treat it as a decision blocker, or consume the
verified durable archive directly and preserve the failure as history. Root directed the third
option.

**Decision: archive consumed directly; terminal receipt not retried.** This changes no scientific
meaning and creates no fallback route.
