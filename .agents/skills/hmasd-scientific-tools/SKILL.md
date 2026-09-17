---
name: hmasd-scientific-tools
description: Design, run and read HMASD experiments as a DM under docs/project/OPERATING_CONSTITUTION.md - explore an idea within its fit allowance, write a claim note, choose a matched-information comparator, read results by the prewritten rule, record in NOTES.md. Not for Git mechanics or formatting.
---

# Research method

Authority: `docs/project/OPERATING_CONSTITUTION.md` sections 3, 4, 5 and 8. This skill is the
method; it adds no rule. Records are the notebook, the runs folder and the claim note.

## Explore an idea

1. Write the `NOTES.md` entry before running: the idea in one sentence, the MARL structure it
   touches (roster, duration, credit, partial observation, information flow), the strongest
   simpler explanation, the observation that would distinguish them, the arms, the training
   horizon, the total fits (up to six including tuning) and the expected sign.
2. Run on any host that can show the effect; single seed is fine. Commit first, preflight,
   launch detached at that sha (engineering skill). The runner writes `runs/<direction>/<tag>/`.
3. Read curves and `summary.json` directly. Write the observation, keep or kill, and the next
   step. Exploratory conclusions stay exploratory: no effect claim from one seed, no MEI verdict.
4. Kill, revise materially, or move on. A killed idea reopens only for a recorded new reason.
   Do not extend a batch after seeing its scores; do not rename a failed idea to reset its fits.

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

Use `hmasd-pro-research-prompt-author` for a hypothesis batch before an exploration cycle or
one critic pass on a claim note. Read the whole answer; record in `NOTES.md` what you adopt,
modify or reject and why. Pro advises; the DM chooses.

## Tools, only as needed

For an unresolved concept read the relevant section of
`docs/rl-marl-foundations-20260907/FOUNDATIONS.md` ([scientific-reading.md](references/scientific-reading.md)).
For a literature gap use [local-literature.md](references/local-literature.md) and verify primary
passages. For baseline or environment integration use [adapters.md](references/adapters.md).
For an endpoint CSV `task,seed,arm,score` run `scripts/summarize_runs.py` (one score per training
run; `--paired --baseline <arm>` only for justified pairing). Use NumPy for known counts rather
than simulation. Optional packages go in isolated environments, never the live interpreters.
