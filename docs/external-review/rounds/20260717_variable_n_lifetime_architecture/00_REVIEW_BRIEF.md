# Variable-N + Variable-Lifetime Architecture Review Brief

## Review purpose

This is an architecture synthesis round, not an experiment-design or tuning
round. Two independent divergent reviewers receive the same Git-visible
evidence. Gemini additionally receives allowlisted local original papers. They
must not read each other's output. Codex will compare both before a separate
GPT-5.6 Pro conversation performs convergence.

No reviewer has predetermined authority over another. Claims are weighted by
evidence, reasoning and compatibility with the research contract.

## Final target

Design one shared skill-based MARL algorithm for UAV cooperation that can
eventually support both:

1. episode-internal join, leave and rejoin with survivor-state continuity and
   anonymous variable team size;
2. heterogeneous per-agent skill lifetime without a combinatorial duration
   action or a shared renewal barrier.

It must preserve or deliberately replace:

- HMASD's behaviorally meaningful individual skills and cooperative joint
  assignment pressure;
- the useful autoregressive/MAT property that later assignments condition on
  earlier assignments;
- exact behavior-policy probability replay, event ownership and duration-aware
  credit;
- bounded computation when maximum roster size is much larger than active N.

Intrinsic reward must remain environment-agnostic. Task identities, goals,
contacts, phases, success predicates, distances and external reward cannot be
used to customize intrinsic reward. Reward shaping is not algorithmic evidence.

## Existing architecture anchors

- Original HMASD uses a high-level joint/team code plus autoregressive
  individual skill assignment, low policies conditioned on individual skills,
  and `q_D/q_d` semantic pressure. The original source archive is the fixed-N,
  fixed-clock positive reference, not an implementation template that may be
  silently rewritten.
- OPT is a representation/execution reference for entity/token processing, not
  evidence that HMASD's variable-N plus variable-lifetime problem is solved.
- R49 established only an interface fact: anonymous roster encoding can be
  permutation/padding invariant and incrementally updated with exact replay and
  prefix-gradient support. It did not train a task policy.

## Evidence accumulated before this round

The following are repository facts, not new interpretations:

| Evidence | Narrow result |
|---|---|
| R41B | Original fixed-N/fixed-clock HMASD source reproduction passed with final win 0.89 and exact replay. |
| R42--R48 | Multiple fixed-N renewal, credit, process-mode and recurrent-boundary mechanisms were implementation-valid but did not establish useful heterogeneous-lifetime transport. Their exact contracts are retired. |
| R49 | Open-roster interface-only architecture checks passed; no learning, reward or optimizer evidence. |
| R50 | Fixed-N specialists narrowly missed one prerequisite while the shared arm looked numerically competent; cross-N sharing remained unidentified. |
| R51--R52 | Two variable-N task substrates failed their fixed-N specialist access prerequisite despite valid implementation; their exact environment/reward contracts are retired. |
| R53 | Executable support and final-policy competence passed, but registered causal learning-gain thresholds failed; shared-versus-specialist transport remained unidentified. |
| R54 | Full-set attention prerequisite degraded severely with N and failed; the hybrid compression arm was quarantined. |
| R55 | A direct-edge fixed-membership/fixed-horizon toy was drafted but never tested. It is paused because it does not currently distinguish final-target hypotheses. |

These failures do not jointly prove that variable N, variable lifetime, HMASD
skills or autoregression are impossible. They do show that another isolated toy
must earn information gain against a shared causal portfolio.

## Current provisional portfolio

- **H0 — ordinary masked/padded MARL:** fixed maximum roster, inactive masks or
  dummy agents, synchronous checks and repeated skills. This is the strongest
  complexity-reduction objection.
- **H1 — autoregressive event-token coordinator:** join, leave, KEEP, SET and
  termination are variable-length policy events with duration-correct credit.
- **H2 — anonymous dynamic relational coordinator:** local member/entity
  relations or a sparse dynamic graph replace a global set summary while an
  exact joint/event probability ledger is retained.
- **H3 — decentralized termination with invariant active-skill context:**
  agents request or terminate independently and coordinate through an anonymous
  active-skill summary, accepting less autoregressive bandwidth if it is not
  empirically necessary.

These are placeholders. A divergent reviewer may merge, replace or retire them
and may introduce a genuinely missing architecture family. Do not preserve them
merely because the controller named them.

## Decision this round must improve

Produce a small architecture portfolio that explains how variable membership,
heterogeneous skill duration, semantic skill preservation, coordination, credit
and scaling fit together without blind module stacking. Identify the smallest
existing analysis or shared testbed observation that would distinguish H0 from
at least one nontrivial architecture family and change a real integrate/stop
decision.

Do not define R56, prescribe hyperparameter changes, launch experiments or
convert every hypothesis into a separate gate.
