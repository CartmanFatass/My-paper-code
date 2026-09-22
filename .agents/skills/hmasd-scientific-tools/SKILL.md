---
name: hmasd-scientific-tools
description: Develop cumulative HMASD research understanding - update judgments from evidence, use simple-model prototypes, select a discriminating next action and involve Pro at consequential scientific decisions under constitution section 5. Declare fit cost and read confirmation by its fixed rule in NOTES.md.
---

# Research method

Authority: `docs/project/OPERATING_CONSTITUTION.md` sections 3, 4, 5 and 8. This skill is the
method; it adds no rule. Records are the notebook, the runs folder and the claim note.

## Explore an idea

1. Start from the direction's current explanation and the observation or gap motivating this
   work. In `NOTES.md`, link the relevant prior interpretation and contrary evidence. State the
   question, MARL structure, strongest simpler explanation and discriminating observation.
   For a targeted change predict both an intermediate effect and its native consequence;
   a package screen can instead explicitly forgo mechanism attribution. Declare the arms,
   training horizon, planned fits with their scientific reason and expected sign before running.
2. Run on any host that can show the effect; single seed is fine. Commit first, preflight,
   launch detached at that sha (engineering skill). The runner writes `runs/<direction>/<tag>/`.
3. Read curves and `summary.json` directly. Separate technical execution facts, observations
   and interpretation. Update what is strengthened, weakened, untouched or unresolved before
   choosing the next action. Exploratory conclusions stay exploratory: no effect claim from
   one seed, no MEI verdict. Do not force a new insight from an uninformative result.
4. Choose inspection, diagnosis, replication, targeted revision, a different hypothesis or idle
   for the judgment/use it can change, not a quota of new candidates. A new prospective study
   may continue the same scientific question; explain its new information value and count its
   exposure. A killed idea reopens only for a recorded new reason. Do not extend a batch after
   seeing its scores or rename a failed idea to reset its fits.

For mechanism questions trace environment event -> entity ownership -> available information
-> action/credit -> learning -> native consequence. For changing rosters distinguish entity
from slot, join/leave/rejoin, survivor history, censoring and partner co-adaptation; distinguish
primitive time from decision opportunities. Use the distinctions relevant to the proposed effect,
not a form to fill for every run. A plausible heuristic or suboptimal scheme is a legitimate
empirical candidate; exploration needs no general optimality, invariance or convergence proof.

For learning observations check that the actual environment, policy, learner/trainer and
evaluator ran: read transition, optimizer-update and evaluation counts and learner movement
from the run summary. Claimed training needs actual updates; recurrent-state evolution alone
is not parameter learning. Fixed-policy evaluation reports zero new updates and its conditional
scope, never new learning. Use an informative horizon, without a prerequisite learnability run.

## Update the working explanation

In the existing notebook, connect the prior judgment and prediction to the observation and
the resulting interpretation. Use only distinctions relevant to the question: task opportunity,
representation, finite learnability, and complete-package benefit/cost are not interchangeable.
Identify which competing explanations actually predicted different observations. A negative
package comparison need not identify a bad component; nonactivation and technical failure
cannot count as evidence of an active mechanism's adverse effect.

A working update may be qualitative and conditional. Missing population precision does not
forbid learning from the result, but does forbid fabricated confidence or a stable ranking.
Keep positive and negative evidence, distinguish newly suggested explanations from pre-result
predictions, and revise interpretations by appending rather than rewriting prior entries.
No useful discrimination is a valid conclusion. Do not repeatedly list "optimization, capacity,
seed" as equally surviving excuses without asking what could weaken each explanation.

Prefer a targeted revision when evidence points to a modifiable link and the revision makes a
different prediction. Lower expectations when tested repairs fail their intermediate predictions,
the proposed bottleneck is not material in the target conditions, or remaining rescue stories
make no different feasible prediction. These are research judgments, not automatic failure-count
gates. Stopping because the next information is not worth its cost is distinct from falsification.
An unchanged replication is useful when recurrence itself changes a decision; a new architecture
is not a prerequisite. A cheap direct learner test may beat an elaborate diagnostic.

## Simple-model and literature bridges

Use a bandit, single-agent MDP/POMDP or small joint-action game when it clarifies the disputed
link. Map variables, information rights, objective, intervention and prediction to MARL; name
what the simplification removes, such as endogenous teammate learning, decentralized information,
joint credit or asynchronous commitments. Derive or inspect a counterexample where useful.
A prototype, proof or literature search is not a required preliminary stage. Toy success does
not establish MARL/UAV benefit, and toy failure constrains only assumptions actually shared.

Verify the relevant primary passage; separate its result from our analogy and proposed design.
A return to an older branch inherits its adverse evidence and selection history. Neither model
agreement nor a literature analogy supplies new empirical replication. Examples and selectively
borrowed agent-project ideas are in [cumulative-research.md](references/cumulative-research.md);
read it for a concrete reasoning need, not as a mandatory preload.

## Confirm a claim

Write `CLAIM_<slug>.md` before the confirmation batch: hypothesis, candidate arm, the one
primary matched-information baseline, task population, seeds per arm (three to five, fresh and independent),
training horizon, endpoint and evaluation budget/protocol, checkpoint selection and stopping rule,
selection and tuning exposure with development separated from final evaluation, decision rule,
uncertainty method, and what each outcome branch means. Run the batch once. Append the result
read by that rule with per-seed values; never rewrite the plan. Inconclusive is a legitimate
end; non-significance is not equivalence; a wide interval is not zero effect.

## Comparators and MARL information

State for every arm: actor and critic information, refresh cadence, bandwidth and
representation, communication, action constraints, reward, termination and truncation,
normalisation, recurrent reset, training and update budgets, tuning rights and evaluation
selection. Local-actor MAPPO, central-input flat, fixed-clock or interruption ablations and
privileged uppers are different comparators; the same exogenous information is not the same
representation, bandwidth, optimisation difficulty or compute. A package gain needs an
identifying control before it is attributed to a component; keep native losses beside proxy
gains. Reuse `docs/research/baselines/<host>/` and `experiments/baselines/<host>/` when the
configuration, information conditions and exposure match; state mismatches. K-axis mechanism
questions, jointly trained N-axis churn, train-N to test-N transfer and open ad hoc teamwork are
distinct targets; do not merge K and N into one programme.

When discussing headroom, name the upper reference and the tuned same-information generic
baseline whose gap it measures; an arbitrary favorable score gap is not headroom. A privileged
upper does not establish an achievable gain. Missing tuned headroom is no prerequisite to exploration.

## Statistics

Independent training runs are the inference unit; episodes and checkpoints are nested
observations, not more n. Bootstrap, more episodes or a larger effect cannot fix n = 1. Pair
only when a shared exogenous design and real independent units justify it, never because seed
numbers match. Never fill a missing pair with zero or assume missingness is random. Keep every
run and curve. Outcome-informed redesign is a new exploration, not a fresh confirmation of the
old rule. Report signed effects, per-seed values, the estimand and the small-sample limits.

Separate practical effect importance, training-outcome variation and estimator uncertainty.
For confirmation explain what difference would matter for the task, without a mandatory MEI
verdict for exploration. An equivalence claim needs a prospectively defined equivalence region
and an uncertainty interval sufficiently narrow for that claim; a small point estimate or a
one/two-seed-SD rule does not establish equivalence or importance. State the interval assumptions.

## Cost and exposure

Count fits as arms times seeds per launched attempt at a declared horizon; different horizons
are different compute. Record actual wall time per fit and batch elapsed; unknown time is not
zero. Report selection and tuning exposure alongside any comparison. Prefer the smallest real
learning comparison that decides the question; exhaustive diagnosis, exact maxima and
search-before-learning need a concrete purpose.

At design time count the dominant work from the configuration: arms, fits, steps, evaluation
panels/checkpoints, optimizer epochs and nested candidate/trajectory/solver calls. Separate
algorithm-intrinsic search from verification added to study it. Joint-action or trajectory
branching, subsets and repeated replanning can dominate even a finite, bounded or zero-fit
study; reconsider unnecessary dimensions before accelerating them. Use known counts and
existing measurements; unknown cost stays unknown and creates no mandatory profiling run.

Performance claims account for full work: import/build/init, rollout and learning, replay,
evaluation, synchronization, publication and readback. Separate cold/warm runs, preparation,
queue/support, sum of fit walls, batch elapsed and actual node occupancy. Report user/system
CPU and children without double-counting threads when parallelism matters; name internal
BLAS/OpenMP/native teams and RSS scope. Never omit scientific work to claim speed; unknown
cost is not zero. These are claim-specific measurements, not a mandatory profiling fit.

Transfer claims state the held-out task/population, perturbations and aggregation actually
tested. Simulator results do not establish physical deployment safety. Exact theorem claims
need assumptions matching the implemented scheme. These limits do not create evidence
classes, a C-consumption ladder or a universal held-out requirement for exploration.

## Pro

Apply constitution section 5 proactively before establishing or materially changing the question,
core hypothesis or key comparator; changing a failure explanation or continuing investment after
intermediate predictions keep failing; closing/reopening a research route or broadening a claim;
and confirmation. Do not wait for the owner to request scientific criticism. These are decision
points, not a fixed failure count or a consultation after every result.

Identify the choice that advice can change. Check the relevant prior Pro answer: if it already
covers that choice and its evidence and premises remain materially applicable, reuse it in the
normal notebook reasoning. Confirmation reuse must cover the actual claim, comparison and fixed
plan. Routine implementation, planned verification, execution and collection under the same
reasoning need no repeat. Materially changed questions, premises or evidence at these points
need a focused follow-up through `hmasd-pro-research-prompt-author`: synthesis, failure explanation,
simple-model/source bridge, targeted revision, hypothesis search or criticism as appropriate.

Read the whole answer; in `NOTES.md` record what you adopt, modify or reject, which judgment
changes and why. A local Critic or engineering Reviewer can assist but does not replace Pro's
consultation. The DM chooses; adviser agreement, a fixed idea count and a separate approval
are not required. The DM can complete the authorized Pro browser workflow without Root forwarding
or a per-question owner approval. Continue work independent of the pending scientific decision.
Existing frozen review exceptions remain tied to their original object, not expanded by this method.

## Tools, only as needed

For an unresolved concept read the relevant section of
`docs/rl-marl-foundations-20260907/FOUNDATIONS.md` ([scientific-reading.md](references/scientific-reading.md)).
For a literature gap use [local-literature.md](references/local-literature.md) and verify primary
passages. For baseline or environment integration use [adapters.md](references/adapters.md).
For an endpoint CSV `task,seed,arm,score` run `scripts/summarize_runs.py` (one score per training
run; `--paired --baseline <arm>` only for justified pairing). Use NumPy for known counts rather
than simulation. Optional packages go in isolated environments, never the live interpreters.
