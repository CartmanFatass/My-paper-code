# Open question: what does unbinding the skill period k actually mean?

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

The tree currently holds **two** skill-duration mechanisms at once.

The HMASD trunk uses a single fixed integer period `k`. Skill reassignment, the
high-level sample boundary, and recurrent chunking are all keyed to that same
constant, and episode length is constrained to be divisible by it.

The HA-CTSE path already samples a per-agent duration from a discrete candidate
set under `H_min`/`H_max` bounds, and the process core records the realized
segment length instead of assuming it.

So "unbinding `k`" is not greenfield work. It is a question about which of these
couplings is load-bearing and which is an inherited assumption.

## The question

The branch `untied-k` was created to explore unbinding the skill period. That
name admits at least three structurally distinct readings, listed here as a
**hypothesis for you to correct or replace**, not a menu to pick from:

1. **Team/individual decoupling.** `K_team` — the team commitment interval — is
   separated from individual skill lifetime, so a team-level commitment and an
   agent's skill duration are no longer the same clock.
2. **Fixed to variable.** The HA-CTSE variable-duration mechanism becomes the
   trunk mechanism and the `% k` boundary disappears entirely.
3. **Period/credit-window decoupling.** The high-level sample stops closing at
   `skill_timer == k - 1` and closes on an event instead, so the credit window
   is no longer forced to equal the skill period.

Answer:

**A. Which reading, or which composition of readings, is the scientifically
correct direction for this branch — and what makes the others wrong or
subsumed?** If none of the three is right, say what the real distinction is.

**B. Is `k` a genuine algorithmic commitment or an inherited artifact?** State
which of the four couplings (reassignment boundary, credit window, recurrent
chunk length, episode-length divisibility) carries scientific content and which
is implementation convenience. They are currently the same constant; say for
each whether that identity is load-bearing.

**C. What is the strongest information-matched ordinary-MARL or
simpler-controller reduction** that would explain any gain from unbinding
without the mechanism? A useful answer here may be that the reduction wins.

**D. What single observation would most raise or lower the plausibility** of
your selected direction, and what evidence semantics must be frozen before it is
collected?

## Required response sections

1. **Direction and its rejection set.** Your answer to A, with what each
   rejected reading gets wrong.
2. **Coupling audit.** Your answer to B, one line per coupling: scientific
   content, or convenience.
3. **Plural candidates.** Two to four structurally distinct mechanisms that
   could deliver the capability, each with its causal story, what it replaces or
   deletes, the evidence it explains, and its strongest contradiction.
4. **Matched reduction.** Your answer to C.
5. **Separating evidence.** Your answer to D, plus the smallest refuted unit for
   each candidate.
6. **One scheduled evidence action and reactivation conditions.** A
   recommendation only — it authorizes neither implementation nor compute.
7. **Concise Chinese user brief.** What direction was chosen, what was excluded,
   what remains open, and an explicit statement that neither implementation nor
   formal compute is authorized by this response.

## Prohibited outcomes

- Do not write an implementation plan, file list, function signature, or task
  decomposition. That is the orchestrator's, not yours.
- Do not authorize nonformal or formal compute, a run, or a successor dispatch.
- Do not propose a workflow, role, or process change.
- Do not reinterpret or reopen a closed G18/G19 result, and do not resurrect a
  retired estimand by renaming it.
- Do not declare a single legal successor that forecloses the portfolio.
- Do not claim learned skills from labels, supplied executors, forced branches,
  entropy, classifier accuracy, or task-specific shaping alone.
