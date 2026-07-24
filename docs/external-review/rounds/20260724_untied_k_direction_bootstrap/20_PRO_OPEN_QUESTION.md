# Open question: per-agent variable skill period

```text
round=20260724_untied_k_direction_bootstrap
branch=untied-k
semantic_author=project_manager
scientific_authority=external_pro
artifact_scope=reviewer_visible_code_side
repair_owner=fable_orchestrator
```

## Decision authority

You are the external GPT-5.6 Pro scientific authority for this repository.
Scientific decisions are yours: which mechanism is right, which route is
excluded, whether evidence closes, what the next direction is. The Fable
orchestrator owns code design only and will not reopen your scientific choice.

For protected semantics that are simultaneously algorithm and code — reward,
probability factorization, gradients and detach, recurrent state, masks, clocks,
lifecycle ownership, RNG, replay, credit, checkpoint meaning — you decide
**whether** one changes; the orchestrator decides **how**.

## Exact topic

**In scope: the skill period of an individual agent becomes variable.** Today
every agent shares one global skill period. This branch exists to explore
letting each agent hold a skill for its own length of time.

**The team side is in scope too, and nothing about it is fixed.** The team skill
`Z` was originally conceived as an information set compressed out of the OPT
module rather than a state the algorithm must carry — but that origin is itself
**open to redesign** if per-agent variable period calls for something else.
Whether `Z` needs a period, whether it persists, what it is compressed from, and
whether it should exist in this form at all are all live.

**This is an opening exploratory round, not a field-completion continuation.**
Treat every framing below as disposable scaffolding. If the useful answer
requires discarding the structure of the question, discard it and say why. The
project is exploring, not defending an existing design.

**Out of scope for this round — do not answer about these:**

- The **number** of skills. `n_Z = 6` team codes and `n_z = 6` individual codes
  are fixed and are not the subject. This round is about period, not cardinality.
- Variable **agent count** and membership lifetime. Runtime-variable team
  membership is the repository's existing mission, already carried by the
  G-generation line. It is background, not the question.
- Any implementation route, file, or task split.

If you believe the correct scientific move requires touching one of the excluded
items, say so explicitly and stop — do not silently answer a different question.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/ALGORITHM_DESCRIPTION_v6.md`
- `docs/project/CURRENT_WORK.md`
- `docs/project/IMPLEMENTATION_PLAN.md`
- `docs/workflows/research-iteration-cycle.md`
- `docs/workflows/NOTES.md`
- `docs/external-review/rounds/20260724_untied_k_direction_bootstrap/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260724_untied_k_direction_bootstrap/01_SHARED_SOURCE_MANIFEST.md`
- `ha_ctse_process/config.py`
- `ha_ctse_process/train.py`
- `tests/ha_ctse_test.py`

The manifest lists the exact `hmasd/` source anchors. Read them from the remote
at `stage_commit`.

## Repository fact

The tree already holds **two** skill-duration mechanisms at once, and that
coexistence is what this round is about.

The HMASD trunk uses one fixed global integer period. Skill reassignment, the
high-level sample boundary, and recurrent chunk length are all keyed to that same
constant, and episode length is constrained to be divisible by it.

The HA-CTSE path already samples a **per-agent** duration from a discrete
candidate set under bounds, and the process core records the realized segment
length rather than assuming one.

So per-agent variable period is not greenfield. A mechanism for it exists on one
path and not the other, and the question is whether that existing mechanism is
the scientifically right one.

## The question

**A. Is the existing HA-CTSE per-agent duration mechanism the right one?**
It samples a duration from a fixed discrete candidate set at assignment, under
bounds, with termination masked by skill age. State whether that is the correct
form of per-agent variable period, or whether the correct form differs — for
example a learned termination decision, a state-dependent hazard, an
option-style termination condition, or something you name. If the existing
mechanism is right, say what remains unproven about it.

**B. Which couplings to the global period carry scientific content?**
Four things currently share one constant. For each, state whether the identity
is load-bearing or inherited convenience once the period varies per agent:

1. when a skill is reassigned;
2. when the high-level sample closes, i.e. the credit window;
3. the recurrent chunk length;
4. the constraint that episode length divides by the period.

**C. What breaks in credit assignment when agents desynchronize?**
With a shared period, all agents' skill segments start and end together. With
per-agent periods they do not. State what that costs — in the high-level value
estimate, in advantage computation, and in replay.

**C2. What should the team skill `Z` become?**
Once no two agents share a boundary, `Z`'s current form may not survive. Its
origin as an OPT-compressed information set is context, not a requirement — you
may redesign what it is compressed from, when it exists, or whether it exists.

A few directions, offered only to show the range and not as a menu: `Z` keeps a
period of its own; `Z` stops being a periodic state and becomes a function
evaluated when read; `Z` is re-derived at each agent's own boundary so different
agents condition on different vintages; `Z` is unnecessary and its information
travels another way. A better answer that is none of these is preferred over the
best of these.

Whatever you propose, state what it does to the probability factorization and to
the environment-agnostic intrinsic-reward contract.

**D. What is the strongest information-matched reduction?**
Give the ordinary-MARL or simpler-controller comparator that would explain any
gain from per-agent variable period without the mechanism. A useful answer here
may be that the reduction wins and the fixed period should stay.

**E. What single observation would most move your confidence**, and what
evidence semantics must be frozen before it is collected?

## Required response sections

1. **Mechanism verdict.** Your answer to A, with what a wrong form would cost.
2. **Coupling audit.** Your answer to B, one line per coupling: scientific
   content, or convenience.
3. **Desynchronization cost.** Your answer to C.
4. **Team skill disposition.** Your answer to C2, including what it does to the
   probability factorization and the intrinsic-reward contract.
5. **Plural candidates.** Two to four structurally distinct mechanisms for
   per-agent variable period, each with its causal story, what it replaces or
   deletes, the evidence it explains, and its strongest contradiction.
6. **Matched reduction.** Your answer to D.
7. **Separating evidence.** Your answer to E, plus the smallest refuted unit for
   each candidate.
8. **One scheduled evidence action and reactivation conditions.** A
   recommendation only — it authorizes neither implementation nor compute.
9. **Concise Chinese user brief.** What was decided, what was excluded, what
   remains open, and an explicit statement that neither implementation nor
   formal compute is authorized by this response.

## The few real limits

Everything else is open. These are not:

- **Stay on period, not cardinality or membership.** Skill count and agent count
  are different questions with their own evidence.
- **No implementation.** No plan, file list, signature, or task split — that is
  the orchestrator's half of the split, and answering it there wastes your turn.
- **No compute authorization.** A recommendation is not a run.
- **Keep the portfolio plural.** Do not collapse to a single legal successor.
- **No skill claims from weak evidence.** Labels, supplied executors, forced
  branches, entropy, or classifier accuracy alone do not demonstrate a learned
  skill.
