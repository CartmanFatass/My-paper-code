# Codex Synthesis — F0/F1 Dynamic-Roster Testbed Design

## Controller position before convergence

Both blind reviewers independently returned `MODIFY_TESTBED_DRAFT`. The shared
core is strong enough to converge: one anonymous dynamic-roster dual-duty task,
one terminal graded external utility, one direct ordinary-policy access
instrument, and one fully matched F0/F1 comparison. The remaining disagreement
is launch-contract precision, not a choice among unrelated routes.

This synthesis weights claims by repository evidence and causal relevance, not
reviewer identity. It does not authorize environment implementation, training
or promotion of F1.

## Common causal structure

Both reviews support the same ordered interpretation:

```text
ordinary task access
-> executable skill-conditioned behavior
-> F0 shared-context sufficiency versus F1 applied-prefix value
-> timing diagnosis only after skill and prefix evidence
```

- H0 remains the primary null. F0 already has the active set, owner-local
  recurrence, incumbent commitments and duration-correct credit.
- H1 requires a natural post-initial common-support distribution change, a
  directionally useful composition change and external task gain over F0.
  Structural prefix connectivity alone is insufficient.
- H2 is an upstream competing explanation when a direct policy learns but both
  skill-based arms fail to form executable roles.
- H3 is diagnostic-only unless access, skill execution and directionally
  correct prefix use are already established. This round cannot authorize
  learned event timing.

## Agreement and controller disposition

| Claim | Gemini | Open Pro | Controller disposition |
|---|---|---|---|
| Keep the anonymous `4 -> 2 -> 6 -> 4` episode-internal roster process | accept | accept | accept |
| Use one persistent duty and short reactive duties | accept | accept | accept |
| Use terminal-only graded task utility, not a conjunction or shaping | accept | accept | accept |
| Keep task, membership, opportunity and ordering randomness independent | accept | accept | accept |
| Add a strong direct recurrent ordinary-policy access instrument | accept | accept | accept |
| Preserve exactly one F0/F1 intervention: initial versus applied working summary | accept | accept | accept |
| Interpret H3 only after access, skill and prefix evidence | accept | accept | accept |
| Delete R51--R54 rescue contracts and leave R55 unexecuted | accept | accept | accept |
| No task-specific intrinsic reward, team latent, identity, graph/slot stack or learned timing | accept | accept | accept |

## Disagreements requiring convergence

### 1. Short-duty semantics and action space

Gemini proposes one `SERVE_SHORT` action and short jobs expiring after five
steps. This is smaller, but it does not define how different short jobs compete
or how workload changes with active `N`; a single reactive action may let every
member use the same behavior and leave little natural role-composition signal.

Open Pro proposes `SHORT_A` and `SHORT_B`, eight frozen waves, two consecutive
matching actions per contribution, a four-step deadline and `R_w=N_w-1`
required contributors. This gives the episode-internal roster change real task
semantics and makes redundant composition measurable. It is not a hard role
mask or a reward-defined skill label, but the convergent reviewer must verify
that two short task types are necessary rather than an artificial F1 showcase.

Controller preference: retain Pro's A/B contract unless an equally exact
single-short-action process still creates nontrivial, `N_t`-dependent competing
commitments without identity or hard assignment.

### 2. Direct ordinary-policy strength

Gemini names a shared recurrent MAPPO primitive policy but does not define its
within-step joint factorization. Open Pro specifies a shared recurrent
primitive-action autoregression over the current active set at every primitive
step, with later tokens seeing an applied action-count prefix.

The latter is the strongest ordinary-MARL objection and avoids making F1 look
useful by comparing it with an artificially independent primitive policy. It
is an access instrument, not another algorithm candidate, and has no skill,
KEEP/SET action or high event process.

Controller preference: use the primitive-AR direct arm, while keeping its
parameter scale small and its role limited to task access.

### 3. Evidence budget and execution order

Gemini proposes 500,000 steps, PPO 10, 128 evaluations and three seeds, but it
does not state whether this is per arm and per seed. Interpreted literally, it
is too large for the requested fast local design round and reintroduces broad
seed expansion before access is known.

Open Pro proposes one matched three-arm contract with 16 environments,
320,000 primitive steps per arm, 250 outer updates, PPO 4 and 256 zero/final
evaluations. This is finite and exposure-exact. However, launching all three
arms before the direct access result is known can waste two skill-based runs if
the environment itself is inaccessible.

Controller proposal: register one hierarchical evidence contract but serialize
compute by causal necessity:

1. run the no-learning constructive/random carrier checks;
2. run the direct primitive-AR access arm;
3. only if ordinary access is established, launch the paired F0/F1 arms with
   identical external ledgers and exposure.

This is one evidence source and one testbed decision, not a chain of unrelated
toy gates. A direct failure retires the testbed; it does not generate another
algorithm.

### 4. Attribution metrics versus gate accumulation

Gemini's three metrics are too weak: terminal utility, generic redundancy and
prefix KL cannot distinguish label use from executable persistent/reactive
skills, and its proposed `>0.15` F1 advantage plus immediate UAV integration is
unsupported.

Open Pro's task, forced-skill, natural-role, prefix, lifetime and timing reads
are causally better, but its many numerical thresholds risk recreating the
project's earlier pattern of optimizing isolated gates. Convergence should
retain only thresholds needed to support a branch:

- implementation/probability corruption remains fail-closed M0;
- direct task access must establish a learned external-return carrier;
- skill execution must show between-skill behavioral separation beyond
  within-skill stochastic variation plus natural persistent/reactive use;
- H1 requires common-support prefix distribution change, reduced duplicate
  duty under the same legal support and positive F1-minus-F0 terminal utility;
- timing remains a descriptive conditional split, not an independent PASS.

The result should report all continuous metrics and confidence intervals even
when an upstream branch fails. Upstream failure limits interpretation but
should not erase downstream descriptive evidence already collected.

## Proposed converged environment core

Subject to the convergent review, the controller favors Open Pro's finite
environment contract:

- horizon `H=80`; membership events at `t={0,20,40,60}` implementing genuine
  join, temporary leave, rejoin, genuine join and terminal leave;
- primitive actions `IDLE`, `PERSIST`, `SHORT_A`, `SHORT_B`;
- one lifecycle-continuous persistent owner accumulating at most 64 units,
  with a handoff step contributing no unit;
- eight exogenous A/B reactive waves, four-step deadlines, two-step service
  streaks and workload `R_w=N_w-1`;
- terminal components `P` and `S` and only one shared reward
  `U=0.5*(P+S)` at the final step;
- anonymous current-state observations, self-relative owner/streak/contribution
  relations and no future schedule, lifecycle key, identity or roster index;
- routing-only constructive controller and uniform random policy as cheap
  substrate checks;
- direct primitive-AR, F0 initial-summary and F1 applied-prefix arms.

This terminal utility is the task objective. It is not potential shaping and
does not enter the intrinsic-reward path.

## Outcome-dependent portfolio update

| Evidence | Portfolio update and action |
|---|---|
| Environment mechanics invalid | repair the concrete implementation only |
| Constructive/random carrier invalid | retire this exact testbed before learning |
| Direct primitive-AR cannot learn | retire this exact testbed; H0--H3 remain unidentified |
| Direct learns; F0/F1 lack executable skill behavior | strengthen H2 and stop F1 interpretation |
| Direct and F0 learn; F1 lacks prefix or task gain | strengthen H0, retire H1 and stop at F0 |
| F1 changes common-support composition but has no task gain | H1 not supported; inspect direction and conditional timing without adding a module |
| F1 has prefix response, useful composition and external gain | support H1 only for this testbed; require a separate integration decision |
| Valid but uncategorized mixed result | stop and perform one architecture-level interpretation; do not auto-generate another toy |

## Replacement ledger

Retain:

- schema-3 event runtime, typed membership transaction and survivor continuity;
- active-only reference, exact F0/F1 selector and duration-correct credit;
- the low-policy contract `pi_low(a_i | o_i, z_i)`;
- environment-agnostic intrinsic-reward boundary and terminal external reward.

Delete or keep retired:

- R51--R54 exact contracts and rescue variants;
- R55 as a numbered successor and its uncommitted execution path;
- fixed-N specialists as a universal prerequisite;
- identity, hard roles, field slots, graphs, team latents, new discriminators
  and learned event time.

Add only after a separately authorized implementation boundary:

- one dynamic-roster dual-duty environment/adapter;
- one small direct primitive-AR access instrument;
- the already-implied real event-mode training integration;
- one analyzer covering task access, skill execution, prefix use and lifetime.

## Controller recommendation

Converge on one launch-exact testbed contract rather than reopen substrate
search. Prefer the smaller Pro exposure over Gemini's ambiguous multi-seed
budget, but simplify the result logic so it updates hypotheses instead of
turning every diagnostic into another rescue gate. The convergent response
must end at a design disposition and may authorize only moving that design into
`docs/research/`; it may not authorize implementation or training.
