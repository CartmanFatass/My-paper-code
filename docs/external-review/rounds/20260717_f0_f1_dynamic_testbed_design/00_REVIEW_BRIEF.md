# F0/F1 Dynamic-Roster Testbed Design Review Brief

## Purpose

The shared F0/F1 event runtime has reached its authorized deterministic
implementation boundary. The focused trace establishes lifecycle ownership,
typed membership transactions, active-only recurrent execution, exact token
replay, duration-aware credit, strict resume and a constructive
common-support path from an earlier applied edit to a later F1 distribution.
It does not establish learnability or usefulness.

This round must design one architecture-matched local toy testbed that exposes
both final target properties in the same task:

1. episode-internal anonymous `JOIN`, temporary `LEAVE`, terminal `LEAVE` and
   `REJOIN` with survivor continuity; and
2. naturally different useful member commitment lifetimes.

It must also make the only F0/F1 intervention scientifically observable:

```text
F0 later learned scores = function(initial active commitment set)
F1 later learned scores = function(applied working-prefix commitment set)
```

The round designs the environment and the smallest evidence contract. It does
not authorize implementation or training.

## Frozen implementation and comparison boundary

- F0 and F1 use the same lifecycle store, event schedule, random frontier
  order, model graph, parameter count, low actor, active-set critics, reward,
  credit, collector, optimizer exposure and checkpoint contract.
- The opportunity gaps remain exogenous uniform integers in `[1,19]`, mean
  `10` active primitive steps. Learned event time remains deferred.
- The only F0/F1 difference is initial-set versus applied-working-set summary
  selection in the shared commitment decoder.
- A genuine join has a null incumbent and must `SET`; an existing member uses
  the native K-way `KEEP` / `SET(other skill)` categorical distribution.
- No lifecycle key, member identity, roster slot or membership epoch is
  policy-visible.
- The new environment may define its external task objective. It may not
  create an environment-specific intrinsic reward, potential shaping,
  task-label auxiliary loss or policy-visible future membership schedule.

## Evidence that constrains the design

1. Original HMASD on Alice--Bob is a positive fixed-N source reference, but
   Alice--Bob does not expose dynamic team size and cannot answer this round.
2. R51 and R52 were valid ordinary-access failures: a zero or stochastic-only
   task carrier can make a shared-variable-N comparison uninterpretable.
3. R53 reached deterministic final competence but failed its registered
   learning-gain magnitude. Its exact queue/action/reward/gain contract is
   retired and must not be renamed as the new testbed.
4. R54 showed that a particular full-set reference can fail despite complete
   information. Do not respond by adding attention, graph, field-slot or
   residual stacks to the first F0/F1 comparison.
5. The deterministic F1 trace proves only wiring. A toy designed solely so
   identical agents must break an artificial symmetry would be a weak
   architecture demonstration unless the same dependence is naturally useful
   in the task process.

## Controller starting draft: Anonymous Dynamic Dual-Duty testbed

This is a reviewable starting point, not a selected contract.

### Minimal task process

- Non-spatial discrete environment; horizon `H=80`; designed for fast local
  vectorized execution.
- The active roster follows an exogenous, policy-independent dynamic template
  containing `N=4 -> 2 -> 6 -> 4`: two temporary leaves, their later rejoin
  together with two genuine joins, then two terminal leaves. Lifecycle labels
  and presentation order are randomly permuted. Task-process randomness is
  independent of membership randomness.
- One persistent duty needs uninterrupted service over a long window; changing
  the serving lifecycle resets or delays that duty's progress. Short jobs
  arrive on a separate jittered process and expire after a few primitive steps.
  Thus one useful commitment is naturally long while another is naturally
  short/reactive.
- Every active member uses the same discrete primitive action set, provisionally
  `IDLE`, `SERVE_PERSISTENT`, `SERVE_SHORT`. Duplicate service is legal but
  redundant, so the environment does not encode cooperation through a hard
  assignment mask.
- Each member sees the public duty state and its own local recurrent/task
  state, but no identity, roster index, future event or other member's action.
  The centralized critics see the active-set task state allowed by the existing
  contract. The low actor remains exactly `pi_low(a_i | o_i, z_i)`.
- External reward is terminal-only and shared. The provisional task score is a
  bounded combination of persistent-duty completion and short-job completion;
  no per-step progress reward or potential difference is emitted. The review
  must decide whether a graded terminal score or a terminal conjunction is the
  smallest learnable task objective without becoming reward shaping.

The intended natural F1 opportunity is a concurrent frontier after a roster
shock: once one owner commits to a persistent or reactive skill, a later owner
can change its relative skill ranking on the same legal support. F0 receives
the same active set and can still solve whenever shared context and member
features are sufficient.

## Competing causal hypotheses

### H0 — shared-context sufficiency

The active set, owner features and exogenous opportunities are sufficient.
F0 learns useful dynamic-roster behavior and F1 provides no material benefit.
This is the strongest ordinary-MARL explanation and remains undefeated.

### H1 — irreducible applied-prefix coordination

Concurrent roster shocks create useful later-on-earlier commitment dependence.
F1 learns stable common-support prefix response, reduces redundant role
composition and improves natural task behavior over F0 without changing
lifetime safety.

### H2 — skill-semantic/low-control bottleneck

The task is accessible to a direct ordinary recurrent policy, but both F0 and
F1 fail because the shared latent skill bottleneck or low-policy learning does
not form persistent executable roles. This would identify the next algorithm
problem without blaming the environment or the F1 prefix.

### H3 — exogenous-opportunity timing bottleneck

F1 learns correct prefix-conditioned composition, but useful edits arrive too
late after task or membership shocks. Only evidence of learned composition plus
timing-limited execution may strengthen the deferred point-process family.
Failure alone does not authorize learned event time.

## Required attribution structure

One design must separate three questions without creating a chain of unrelated
numbered gates:

1. **Task access:** can a strong direct ordinary recurrent active-set policy
   learn the external task under the same roster schedule and data scale?
2. **Skill substrate:** do F0/F1 produce persistent, executable skill-conditioned
   behavior rather than label use alone?
3. **Prefix value:** conditional on access and skill execution, does F1 beat
   the fully matched F0 control and exhibit natural common-support prefix
   dependence?

The reviewer may place these reads in one hierarchical experiment or select a
cheaper design-only prerequisite, but must not quarantine every informative
arm behind another arbitrary threshold. At least two terminal outcomes must
change the hypothesis portfolio or cause a real stop/integration decision.

## Final-capability map

| Family / instrument | Dynamic roster | Heterogeneous realized lifetime | Latent skill bottleneck | Learned joint edit dependence | Role in this round |
|---|---:|---:|---:|---:|---|
| Direct ordinary active-set policy | yes | no explicit commitment claim | no | may coordinate primitive actions | task-access instrument only |
| F0 scheduled recurrent MARL | yes | yes via common exogenous opportunities and KEEP/SET | yes | no common-support prefix scores | mechanism-matched null |
| F1 event-frontier editor | yes | yes | yes | applied-prefix conditioned | treatment |
| Learned point process | deferred | potentially native | optional | separate question | excluded |

## Replacement ledger

### Retain

- the shared schema-3 event runtime and active-only sum/count reference;
- F0 as the strongest mechanism-matched ordinary reduction;
- F1's sole applied-prefix selector;
- unchanged sparse external reward separation and environment-agnostic
  intrinsic-reward rule;
- exact runtime, probability, duration-credit and checkpoint evidence.

### Delete or leave retired

- the R51--R54 environment/gate contracts and their rescue variants;
- R55 as a numbered successor and its uncommitted draft;
- fixed-N specialists as a universal prerequisite for an episode-internal
  roster task;
- hard role masks, identity tokens and reward-defined skill labels.

### Add only if the final design requires them

- one dynamic-roster toy environment/adapter;
- the minimum event-mode training integration already implied by the accepted
  architecture;
- one result analyzer that attributes task access, skill execution and prefix
  value without changing the reward.

Do not add a graph, slot stack, team latent, new discriminator, learned event
time, reward shaping or a testbed-specific intrinsic term.

## Requested decision

Decide whether the starting draft can become one coherent, learnable and
causally discriminating F0/F1 testbed. Return exactly one of:

- `ACCEPT_TESTBED_DRAFT`;
- `MODIFY_TESTBED_DRAFT` with a finite launch-exact correction list;
- `REPLACE_TESTBED_SUBSTRATE` with one structurally cleaner substitute;
- `STOP_AT_F0` because no non-artificial task can identify useful prefix
  dependence under the frozen contract.

The result must specify the environment transition/reward/observation contract,
the task-access instrument, F0/F1 comparison, attribution metrics, minimum
evidence budget and outcome branches. It must not authorize implementation or
training.
