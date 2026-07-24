# Open question: is per-agent variable skill period the way out of the fast/slow credit impasse?

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

## This is an opening exploratory round

Treat every framing below as disposable scaffolding. If the useful answer
requires discarding the structure of the question, discard it and say why. The
project is exploring, not defending an existing design.

## Where the line actually stands

Three consecutive iterations have circled one problem. Read
`docs/report/ITERATION_18.md` and `docs/report/ITERATION_19.md` for the full
accounts; the short version:

**G17 — accepted.** The decisive finding was a misalignment between the credit
window and the task's causal window. Long GAE mixed independently resampled
future demand into the current action's advantage, and the policy collapsed to a
near-constant action. Aligning actor credit to the immediate service target with
`gamma = 0` produced `USABLE_ONE_STEP_CONTINUOUS_ROSTER_G17`, a dynamic-roster
controller that transfers to unseen headcount trajectories.

**G18 — the delayed source is learnable, but not by a shared actor.** Formal
evidence passed every delayed-access, mechanism and replicate-stability
threshold. It also showed that a shared actor update does not reliably preserve
the accepted G17 controller across fresh seeds. Four candidates — exact TD(0),
raw-sum, channel-normalized, and actor/critic-isolated — are **closed without
retry or tuning**. Critic isolation stopped slow-value learning from polluting
the representation but did not stop successor-value actor gradients from
rewriting the immediate policy.

**G19 — the fast anchor did not buy delayed access.** An explicit fast-policy
anchor plus a zero-initialized delayed residual, with a parameter-space conflict
projection, was implemented and screened. Operationally it was clean: every fast
policy tensor including `log_std` stayed bitwise unchanged, every projected
gradient had nonnegative fast-gradient dot product, and all G17 gates held. But
G18 stayed at utility `0.66667` with zero spike service and zero gain over the
anchor. Result `NONFORMAL_NO_DELAYED_ACCESS_FAST_ANCHOR_G19`; retired without
tuning.

**G20 — in flight.** A zero-compute derivation of an active-set-centered
residual exposing per-step anonymous redistribution directions. No compute is
scheduled.

So the standing pattern is: **you can keep the immediate controller or gain
delayed access, but so far not both in one shared actor.** Sharing gets the
delayed source and breaks the fast one; isolating preserves the fast one and
gets nothing delayed.

## The question

This branch exists to explore making the skill period of an **individual agent**
variable, where today every agent shares one global period. The reason to ask it
now is that the impasse above is a **timescale** problem, and the skill period is
the algorithm's existing timescale object.

**A. Is per-agent variable skill period a resolution to this impasse, or is it
orthogonal to it?**
The immediate task has a one-step causal window. The delayed task does not. One
policy with one credit window has failed to serve both three times. If the skill
period is the unit over which credit is assigned, letting it vary per agent
would let each agent's credit window match the causal window it is currently
acting in. Say whether that is the real mechanism, a restatement of the problem,
or a distraction from a different root cause. If you think the root cause is
something else entirely, name it — the framing above is not to be defended.

**B. Which couplings to the global period carry scientific content?**
Four things currently share one constant. For each, say whether the identity is
load-bearing or inherited convenience once the period varies per agent:
when a skill is reassigned; when the high-level sample closes, i.e. the credit
window; the recurrent chunk length; and the constraint that episode length
divides by the period.

**C. What breaks when agents desynchronize?**
With a shared period all agents' segments start and end together, and the
existing high-level value estimate, advantage computation and replay depend on
that. State the cost.

**C2. What should the team skill `Z` become?**
`Z` was conceived as an information set compressed out of the OPT module rather
than a state the algorithm must carry — and that origin is **open to redesign**
if per-agent variable period calls for something else. A few directions, to show
range rather than to choose from: `Z` keeps a period of its own; `Z` becomes a
function evaluated when read rather than a periodic state; `Z` is re-derived at
each agent's own boundary so agents condition on different vintages; `Z` is
unnecessary and its information travels another way. An answer outside these is
preferred over the best of them. State what your proposal does to the
probability factorization and to the environment-agnostic intrinsic-reward
contract.

**D. What is the strongest information-matched reduction?**
The ordinary-MARL or simpler-controller comparator that would explain any gain
from per-agent variable period without the mechanism. A useful answer here may
be that the reduction wins and the fixed period should stay.

**E. What single observation would most move your confidence**, and what
evidence semantics must be frozen before it is collected?

## Required response sections

1. **Verdict on A** — resolution, restatement, or distraction; and if the root
   cause is something else, what.
2. **Coupling audit** — your answer to B, one line per coupling.
3. **Desynchronization cost** — your answer to C.
4. **Team skill disposition** — your answer to C2.
5. **Plural candidates** — two to four structurally distinct mechanisms, each
   with its causal story, what it replaces or deletes, the evidence it explains,
   and its strongest contradiction.
6. **Matched reduction** — your answer to D.
7. **Separating evidence** — your answer to E, plus the smallest refuted unit
   for each candidate.
8. **Relation to G20** — whether the active-set-centered residual derivation now
   in flight should continue, be absorbed, or be dropped in favour of this.
9. **One scheduled evidence action and reactivation conditions** — a
   recommendation only; it authorizes neither implementation nor compute.
10. **Concise Chinese user brief** — what was decided, what was excluded, what
    remains open, and an explicit statement that neither implementation nor
    formal compute is authorized by this response.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/report/ITERATION_18.md`
- `docs/report/ITERATION_19.md`
- `docs/project/IMPLEMENTATION_PLAN.md`
- `docs/project/CURRENT_WORK.md`
- `docs/research/designs/ALGORITHM_DESCRIPTION_v6.md`
- `docs/workflows/research-iteration-cycle.md`
- `docs/external-review/rounds/20260724_untied_k_direction_bootstrap/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260724_untied_k_direction_bootstrap/01_SHARED_SOURCE_MANIFEST.md`
- `ha_ctse_process/continuous_roster_policy.py`
- `ha_ctse_process/continuous_service_roster_proxy_g17.py`
- `ha_ctse_process/delayed_battery_roster_g18.py`
- `ha_ctse_process/separated_credit_g18.py`
- `ha_ctse_process/anchored_residual_g19.py`
- `ha_ctse_process/config.py`
- `tests/ha_ctse_process_anchored_residual_g19_test.py`

The manifest lists the `hmasd/` source anchors for the fixed period and for
where `Z` is produced. Read everything from the remote at `stage_commit`.

## The few real limits

Everything else is open. These are not:

- **Do not reopen the closed candidates.** Exact TD(0), raw-sum,
  channel-normalized, actor/critic-isolated, and the G19 fast anchor are closed
  on evidence. A new mechanism that happens to subsume one is fine; re-tuning,
  reseeding or renaming one is not.
- **Stay on period, not cardinality or membership.** Skill count (`n_Z = 6`,
  `n_z = 6`) and agent count are different questions with their own evidence.
- **No implementation.** No plan, file list, signature, or task split — that is
  the orchestrator's half of the split.
- **No compute authorization.** A recommendation is not a run.
- **Keep the portfolio plural.** Do not collapse to a single legal successor.
- **No skill claims from weak evidence.** Labels, supplied executors, forced
  branches, entropy, or classifier accuracy alone do not demonstrate a learned
  skill.
