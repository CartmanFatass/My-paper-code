# Evidence Reconciliation

## Scope and evidence boundary

This reconciliation compares the two immutable blind-review raws for
`20260719_clean_process_access_portfolio`:

- `11_GEMINI_DIVERGENT_RAW.md`
- `21_PRO_OPEN_RAW.md`

The registered evidence boundary is the clean-process result and the exact
paths in `01_SHARED_SOURCE_MANIFEST.md` at the pushed review boundary. This
file records agreements, disagreements, and evidence requirements. It does
not rank candidates, select a successor, authorize code, authorize training,
or change any retired result.

## 1. Claims supported by both reviewers

Both raws treat `PASS_CLEAN_CARRIER_DIRECT_ACCESS` as a valid positive result
within its registered contract. The following facts are repeated or accepted
by both reviewers:

- The run completed 320,000 environment transitions, 1,280,000 active-agent
  rows, 1,000 PPO optimizer steps, and 4,000 training ledgers.
- M0 and schema-3 model/optimizer restore checks passed, including zero
  replay error for token/joint likelihood, value, recurrent hidden state, and
  autoregressive prefix checks.
- Carrier controls passed: constructive minimum `P/S/U=1/1/1`; uniform random
  had positive-utility fraction `1.0` and mean `U=0.32421875`.
- The direct learner passed with deterministic final
  `P/S/U=1.000000/0.998210/0.999105` and stochastic final
  `P/S/U=1.000000/0.973307/0.986654`; the deterministic final-minus-zero
  utility CI95 was `[0.498535,0.499105,0.499593]`.
- The added clean-process state is `actuator_position` and
  `actuator_velocity`. It is owned by the environment/lifecycle, freezes on
  temporary absence, resumes on rejoin, initializes on genuine join, and is
  included in the environment snapshot. It is not read by actor observation,
  critic state, task reward, task transition, GAE, or PPO, and the run has
  zero skill/high/intrinsic counts.
- The clean result is an access-valid dynamic-membership substrate and an
  ordinary direct-control result. It does not prove hierarchy, executable
  skill semantics, heterogeneous learned lifetime, cooperation, transfer, or
  benchmark superiority.
- Iteration 5 remains retired for its exact spatial carrier and exact C1
  objective. The clean positive result changes the interpretation to a
  carrier/substrate-specific no-access failure; it does not rescue, rerun, or
  retune Iteration 5.
- Direct active-set recurrent MARL remains the mandatory information-matched
  ordinary null. A clean direct pass does not establish that a hierarchy is
  never useful for a load-bearing variable-lifetime task.

## 2. Important claim ceilings and constraints

The Open-Pro raw supplies an additional implementation-level constraint that
the Gemini raw does not spell out: the clean velocity update is deterministically
invertible from the primitive action and the starting velocity,

`v[t+1] = 0.75 v[t] + 0.25 F(a[t])`, hence
`F(a[t]) = 4 v[t+1] - 3 v[t]`.

Therefore the clean channel can audit lifecycle-owned physical state and
snapshot behavior, but a posterior of the form `q(z | clean-process
trajectory)` would be vulnerable to being only an action-information signal.
The two raws consequently do not support using this channel directly as a
new intrinsic reward. A process residual would need an independently
registered, action-conditioned null; the current deterministic channel does
not establish such a residual.

Both raws retain the following semantic boundaries:

- No task field, task progress, success/contact, role, identity, external
  reward, or fixed slot may be renamed as environment-agnostic intrinsic
  semantics.
- R29, R31-CFEI, R32-IFEPG, R33-IRSC, and Iteration-5 C1 remain retired in
  their exact forms. Forced or action-derived diagnostics remain audit-only.
- Anonymous JOIN, temporary LEAVE, REJOIN, terminal LEAVE, survivor hidden
  continuity, active-set probability/masks, and stale-row rejection must be
  event-owned. A fixed storage envelope is not evidence of arbitrary open
  roster scaling.
- Future hierarchy evidence must distinguish physical time, membership/event
  time, opportunity time, realized segment lifetime, and credit windows. A
  duration catalogue, scheduler-only override, shared renewal clock, or
  one-step return is not a substitute for variable lifetime semantics.
- The current direct checkpoint evidence is at update/environment snapshot
  boundaries. It does not prove a future mid-segment hierarchy checkpoint;
  that checkpoint would need lifecycle, command/skill, age, event traces,
  RNG, pending transactions, worker snapshot, and policy-version state in a
  joint fail-closed contract.

## 3. Candidate portfolio: factual union, no ranking

The reviewers use different labels and counts. The following union preserves
all live explanations while marking the infrastructure item separately.

### A — clean access-valid substrate (resolved infrastructure)

The clean carrier is a usable access substrate, not an algorithmic successor.
It resolves the question whether the exact Iteration-5 spatial no-access
outcome was universal to ordinary dynamic-roster control. It does not consume
one of the live algorithm slots. Neither reviewer treats it as evidence for
hierarchy or as permission to create another carrier merely to reconfirm
access.

### D — information-matched direct active-set recurrence (mandatory null)

**Mechanism and replacement ledger.** Keep the active-set recurrent direct
policy, ordinary probability/mask contract, environment ledgers, and direct
checkpoint semantics; remove high-level skill, hierarchy, and intrinsic
paths. This is the strongest ordinary-MARL reduction and adds no semantic
module.

**Causal estimand.** On the same carrier with actor-visible information,
communication, critic ability, training exposure, parameter budget, checkpoint
selection, and RNG contracts matched, compare held-out hierarchy utility with
held-out direct utility on unseen membership schedules and active-lifetime
distributions. The null is not established by a fixed-N or training-only
comparison.

**Capability and contradiction.** D tests whether ordinary recurrence can
carry the final capability without explicit hierarchy. It is contradicted by
a material, persistent, nuisance-resistant, naturally used hierarchy that
improves external utility or sample efficiency on unseen roster/lifetime
conditions without shortcuts. The Gemini raw describes the same issue as a
temporally delayed coordination test; the Open-Pro raw keeps D as a mandatory
null rather than a final verdict.

**Separating observations.** Held-out utility/transfer and sample efficiency,
matched direct reduction, survivor continuity, and event/lifetime strata are
load-bearing. Label occupancy, posterior accuracy, forced effects, supplied
primitives, or training-internal utility are not sufficient.

### B — factorized discrete process executor

**Mechanism and replacement ledger.** Replace shared actor plus unstructured
categorical FiLM conditioning with a shared observation trunk followed by
capacity-limited, mutually exclusive recurrent/action adapters selected by
the existing categorical command. Preserve the active-set, `K=3`, KEEP/SET,
external opportunity, event-time credit, and ordinary external task objective;
do not add a posterior or intrinsic reward. The Gemini raw describes this as
factorized categorical process dimensions; the Open-Pro raw specifies the
adapter replacement more concretely.

**Causal estimand.** Primary comparison is
`U_factorized - U_capacity-matched-shared` with a matched direct null. Mechanism
reads may include same-snapshot command-to-action dependence, natural command
usage, and stability across JOIN/REJOIN, active-age, and active-set strata;
clean actuator separation alone is not the semantic estimand.

**Capability and contradiction.** B predicts natural, persistent, executable
factorized behavior and a material held-out task advantage not explained by
parameter count. It is contradicted by nonzero adapter gradient/drift without
natural execution or external utility, equivalence to a capacity-matched
shared arm, or a noninferior direct recurrence. The Gemini raw phrases the
same contradiction as no significant gain over flat recurrence.

**Separating observations.** Natural overlap, stable executable behavior,
held-out external utility/transfer, and capacity-matched comparison separate
B from a shared executor and from D. No action-derived clean-channel
classifier can establish B's semantics.

### C — three-basis simplex process command

**Mechanism and replacement ledger.** Replace one-hot categorical command with
`w_i` on a three-basis simplex and compose `c_i = sum_k w_ik b_k`; KEEP holds the
current command and SET updates it. Retain continuous active KEEP run length,
event ownership, and external task objective. Do not add a duration head,
learned hazard, new posterior, or intrinsic reward.

**Causal estimand.** Compare simplex against one-hot B on held-out membership
and lifetime conditions for controllability and external utility. The Gemini
raw emphasizes gradient-flow stability; the Open-Pro raw requires that any
gain be load-bearing and not merely action-probability mixing.

**Capability and contradiction.** C predicts non-vertex commands with
repeatable intermediate process behavior and a material held-out advantage.
It is contradicted by vertex collapse, non-vertex commands that only mix
primitive action probabilities, or equivalence to B/direct recurrence. C is an
alternative to B, not an additive latent.

**Separating observations.** Non-vertex use, predictable intermediate
consequences, natural overlap, and held-out external utility/transfer are
required. A simplex that only changes entropy or capacity is not a semantic
result.

### E — executable-skill assignment/credit bottleneck

This candidate appears explicitly in the Open-Pro raw and is compatible with
the Gemini raw's concern that a hierarchy must first be shown to be executable.

**Mechanism and replacement ledger.** Treat high-level assignment and
owner-event credit as a separately identifiable causal explanation, not as an
immediate new critic. First supply a small, transparent, frozen executable
primitive set to the existing high/event path; do not claim that supplied
primitives are a learned skill solution. Only a later, separately registered
replacement may address credit if this positive control is valid and the
learned high path still fails.

**Causal estimand.** Compare learned-high plus supplied executor against
frozen/uniform-high plus the identical executor, alongside a routing-only
oracle and the matched direct recurrent arm. Read paired utility, final-minus-
zero high gain, exact high likelihood/event values/gradients, owner-event
return, replay/checkpoint validity, and the direct gap.

**Mutually exclusive interpretations.** If learned high accesses the supplied
executor and exceeds frozen high, assignment/credit is not the primary
bottleneck and B becomes more identifiable. If the oracle and direct pass but
learned high fails, assignment/credit rises. If the oracle fails, the
opportunity contract is invalid for this diagnosis. Any replay, mask, count,
checkpoint, or direct-access failure invalidates the source rather than
authorizing a rescue.

**Boundary.** The supplied low executor has no trainable parameters and no low
optimizer; oracle fields cannot enter policy, reward, or advantage. This is a
diagnostic gate, not an integration experiment.

## 4. Candidate/evidence-source proposals from the blind raws

The two reviewers propose non-identical next-evidence decompositions. Their
differences are recorded here for Convergent Pro; this section deliberately
does not choose an order.

### Gemini proposal: delayed direct null, then factorized executor

1. **Direct temporal-extension evidence.** Evaluate D on a Generic-SHORT
   variant with materially increased temporal delays. Estimand: direct utility
   when temporal spacing exceeds primitive memory. A pass supports the
   sufficiency of ordinary recurrence for that delayed test; a failure opens a
   prerequisite for testing hierarchy. No repeated capacity tuning is a
   permitted rescue. The implementation boundary is limited to registered
   delay parameters in the testbed.
2. **Factorized-versus-direct evidence.** Compare B against D on the delayed
   testbed. A material, statistically supported B gain validates the explicit
   factorized hierarchy; equality or underperformance retires B. No
   task-specific high-level assignment or heuristic mask may be added.

The Gemini raw does not separately propose the supplied-executor E gate or a
clean-channel action-equivalence audit.

### Open-Pro proposal: action-equivalence, supplied high path, then executor
comparison

1. **E1 — clean-channel action-equivalence audit.** Compare observed clean
   actuator position/velocity against deterministic reconstruction from the
   start process state and primitive action tape, plus an action-only null.
   Estimands are exact recurrence residuals, with no tunable statistical
   threshold. Exact equivalence closes clean-channel semantic-intrinsic
   proposals; nontrivial residual would require a separately registered
   action-conditioned null; an invalid ledger permits only an audit fix.
   Boundary: read existing equations/rows only, zero policy update, zero
   optimizer, zero reward read.
2. **E2 — supplied-executor high-path localization.** Compare learned-high,
   frozen/uniform-high, a routing-only oracle, and matched direct recurrence
   with the same supplied executor on the clean carrier. Branches distinguish
   high access, learned-high failure with a valid oracle, opportunity-contract
   failure, and invalid implementation. No opportunity, reward, threshold,
   primitive-table, learned-timing, or intrinsic rescue is allowed.
3. **E3 — factorized-versus-shared executor comparison.** Only after E2 shows
   the high path can use supplied executable skills, compare a
   capacity-matched shared hierarchy, B factorized adapters, and matched
   direct recurrence under shared ledgers, event architecture, reward,
   parameter/transition/optimizer exposure, checkpoint rule, and RNG. Branches
   distinguish factorized task-and-execution gain, diversity without value, no
   factorization effect, both hierarchies failing while direct passes, and
   invalid direct/M0 evidence. No posterior, intrinsic, graph, team latent,
   simplex arm, or post-result parameter/seed rescue is allowed.

## 5. Cross-review unresolved choices for Convergent Pro

- Whether the first separating test should stress D with an explicitly delayed
  task (Gemini) or first audit whether the clean channel has any residual
  beyond an invertible action tape (Open Pro).
- Whether the supplied-executor high-path gate E is necessary before a learned
  factorized executor comparison, or whether B-versus-D on a delayed task is
  the smallest sufficient contrast.
- Whether C remains live as an independent candidate after B/E evidence, while
  retaining the rule that C is merged into B if it collapses to one-hot or
  produces no load-bearing non-vertex behavior.
- The exact task contract that can make heterogeneous lifetime and asynchronous
  ownership load-bearing without task shaping, identity leakage, duration
  catalogues, or module stacking.

These are scientific synthesis questions for Convergent Pro. They are not
resolved by this factual reconciliation.

## 6. Shared stop and integration constraints

Both raws require stopping or refusing integration when apparent success needs
task fields, identity/role, learned scheduler timing, a duration catalogue,
retired effect objectives, or a stack of graph/communication/team-latent/
critic/hazard/semantic-reward modules. A hierarchy may enter a later
integration review only after the same-carrier direct access prerequisite,
genuine JOIN/temporary LEAVE/REJOIN/terminal LEAVE and survivor continuity,
exact probability/mask/credit/replay/checkpoint contracts, learned rather than
supplied semantics, natural nuisance-resistant overlap, and material
information-matched held-out external advantage are all established.

No candidate, evidence source, code change, training run, budget expansion,
threshold change, or autonomous successor is authorized by this file.
