# EGRCR-T3 balanced identity support and oracle-headroom prerequisite

Cycle: `2026-08-28.10-clean-01a04a02-egrcr-successor-02`

Treatment: `EGRCR-T3-DIRECTED-CYCLE-SUPPORT-ORACLE-HEADROOM-v1`

Status: frozen EM-to-CM discriminator; no result yet

## Decision purpose and ceiling

This is the smallest executable observation that survived the repository
audit, the fresh Innovator consultation, and independent EM scrutiny. It asks
whether one fixed three-agent host first supplies the two prerequisites that
B1 lacked: balanced consequence-distinct waiter identities and
same-information oracle fixed-token allocation plus bounded-utility headroom
over a competent ordinary-GAE comparator. It contains no relay, binding-cut,
learned-estimator, or learned-gate arm.

A positive result may justify only a later, separately frozen identity-only
relay discriminator. A negative support or headroom result stops that branch.
No variable-population, fixed-`k` superiority, multi-update, learned estimator
or gate, UAV or continuous-control, safety, deployment, or general
source-to-target credit claim is available.

## Why a new execution is answer-changing

B1 is decisive for its two-agent host but cannot answer this new prerequisite.
Its bounded world depends on JOINT/SOLO type and lag, not physical waiter
identity; for a fixed joiner there is only one possible waiter; and INTACT and
ordinary GAE made exactly the same fixed-token choices and bounded utility at
all twelve roots. A three-agent balanced crossover is a new scientific object,
not a B1 rerun.

Static construction establishes logical feasibility but cannot establish the
finite-update comparison against competent sampled GAE. Conversely, an oracle
gap without a path-sever test and a source-localized control could be only a
six-cell contextual-bandit denoising effect. The single frozen command therefore
stages support, comparator competence, native headroom, and source-path
specificity in that order and stops at the first invalid prerequisite.

## Exact host

The persistent population is exactly `A = {0, 1, 2}`. Every ten-tick block has
one earlier waiter `w`, one later joiner `j != w`, and the remaining agent as a
matched nonparticipant. All three identities remain present throughout.

At tick 2 the waiter has one live prepared version. At tick 3 the joiner has
the sole learned binary decision, stored with behavior propensity `p = 0.5`.

- `a = 1`: the joiner and true waiter deploy atomically at tick 3.
- `a = 0`: the joiner deploys locally at tick 4 and the waiter deploys at its
  fixed expiry tick 6.

The bounded outcome boundary is tick 8; tick 9 is terminal padding. Both
branches deploy both prepared versions and pay two identical deployment costs
of `0.01`, so request/renewal counts and additive cost cannot explain a
contrast.

All nonidentity pre-action coordinates are fixed: lag 1, positive unit cue,
the same cue sign, readiness, ages, budget, token state, task clock, propensity,
and action support. There is no JOINT/SOLO type. The only varying actor-visible
coordinates are the ordered physical identities `(w, j)`.

### Directed physical compatibility

Agent `i` has output port `(i + 1) mod 3`; joiner `j` accepts input on port
`j`. Favorable ordered pairs are therefore the directed predecessor edges

`(2,0), (0,1), (1,2)`.

Unfavorable pairs are the reverse directed edges

`(1,0), (2,1), (0,2)`.

For every joiner exactly one waiter is favorable and one unfavorable. Across
the two possible joiners, every waiter is favorable once and unfavorable once.
Each identity is also the nonparticipant equally often. Code must derive
service through deployed-version port occupancy and route connectivity; it
must not pay reward from a direct pair label or expose a compatibility bit to
the actor or critic.

### Bounded service law

Service ticks are 4 through 8 inclusive, with two possible slots per tick.
Each active slot succeeds when its counter-keyed uniform is below `q = 0.8`.
The common tape is indexed independently of arm and counterfactual world.

- compatible atomic deployment has capacity 2 at every service tick;
- incompatible atomic deployment locks the shared port and has capacity 0;
- every non-atomic/fallback world has capacity 1.

For a sampled world, bounded utility is

`Y = delivered_slots / 10 - 0.02`,

which lies in `[-0.02, 0.98]`. Expected-world support uses `q` times capacity,
not sampled outcomes. The natural decision maps `a=1` to four-world cell
`Y11` and `a=0` to `Y00`.

The mechanism must preserve the causal chain

`later joiner request -> true waiter deploys now -> deployed waiter port state changes -> bounded route service changes`.

The nonparticipant's recorded activity, all physical ticks, and all exogenous
tapes are identical across worlds and arms.

## Counterfactual support gate

For each of the six ordered pairs, enumerate expected same-snapshot worlds
`Y00`, `Y10`, `Y01`, and `Y11`, where the first bit selects immediate joiner
deployment and the second immediate waiter deployment; missing deployments use
the fixed fallback deadlines.

Freeze

`Delta[w,j] = Y11 - Y00`

and

`kappa[w,j] = (Y11 - Y10) - (Y01 - Y00)`.

For joiner `j`, let `p(j) = (j - 1) mod 3` and `s(j) = (j + 1) mod 3`, and
define

`C[j] = Delta[p(j),j] - Delta[s(j),j]`

and

`K[j] = kappa[p(j),j] - kappa[s(j),j]`.

Support passes only when every item below is true:

1. changing only the later action changes the true waiter's immediate
   deployment and its port/action at the first common post-event service tick
   for all six pairs;
2. every `C[j]` and `K[j]` is at least `0.50`; average-only passing is forbidden;
3. waiter and joiner marginal sums of `Delta` are zero within `1e-12` after
   favorable/unfavorable balance;
4. `Y10-Y00` and `Y01-Y00` are invariant across waiter identity within
   `1e-12`; the identity contrast appears only with joint atomic deployment;
5. replacing immediate waiter deployment with a no-op while preserving IDs,
   action, timing, and generic state collapses every `C[j]` and `K[j]` to at
   most `1e-12` in magnitude;
6. every root has exact equal counts for all six ordered pairs and both actions,
   and the common tapes are crossed with rather than nested under pair status.

Failure is a bounded support null and stops before learning/headroom. Thresholds
must not be repaired after observation.

## Shared actor representation and information contract

Both comparison arms use one common-ancestor linear Bernoulli head with a
generic intercept and six independent off-diagonal ordered-pair one-hot
coordinates. Diagonal pairs are unreachable and masked. An additive waiter
plus joiner identity head, a symmetric pair embedding, or a hidden favorable
bit is forbidden because none can fairly represent the directed cycle.

At decision time, both arms see the same ordered IDs and constant generic
vector. Neither sees compatibility, realized service, a counterfactual,
future state, or a suffix label. The analytic oracle is privileged only in its
prospective training target; its action-time information and policy function
class are identical to GAE.

A pre-result expressibility check must show that the head can rank all three
favorable pairs above their matched unfavorable pairs inside the frozen update
radius. A pair-masked control must remain exactly at chance. Failure is
representational invalidity, not evidence against ordered credit.

## Data, roots, and RNG

All data are generated by this isolated finite host; there is no external
dataset or checkpoint.

Calibration roots are exactly

`(223, 227, 229, 233, 239, 241)`.

Confirmation roots are exactly

`(251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313)`.

At each confirmation root, the common training batch contains exactly 16
observations in each of the twelve `(w,j,a)` cells: six ordered pairs times two
actions, for 192 eligible source records. The scheduled action count is exactly
balanced at stored propensity 0.5. Every block retains the complete three-agent
ten-tick physical trace even though only the tick-3 joiner record is policy
eligible.

Every uniform is derived without ordering dependence from SHA-256 of the UTF-8
string

`EGRCR-T3-DIRECTED-CYCLE-SUPPORT-ORACLE-HEADROOM-v1|root|namespace|pair_index|action|rep|tick|slot`,

taking the first unsigned big-endian 64 bits and dividing by `2**64`. Namespaces
are frozen textual labels for training service, evaluation service, evaluation
token choice, and any calibration panel. Arms and counterfactual worlds reuse
the same applicable key; no seed replacement, restart, sweep, or post-result
enlargement is allowed.

## Competent ordinary-GAE comparator

The behavior ancestor is the uniform policy. `GAE-DP` uses ordinary full-reward
GAE with `gamma = 1` and an exact pair-aware finite-state value function for the
frozen behavior policy. The value state contains only Markov state already
available to the learner: ordered IDs, deployment/port state, clock, and
generic fields. It contains no action at the pre-action record, counterfactual,
future realization, or compatibility flag. Exact Bellman residual must be at
most `1e-12`.

Select lambda prospectively from `(0.0, 0.5, 0.95, 1.0)` using only the six
calibration roots: for each value, take the same one-step GAE update and score
mean held-out native bounded utility; choose the greatest mean, breaking exact
ties in favor of the smaller lambda. Freeze that value before confirmation.
There is no critic learning during confirmation.

The `PAIR-Q-ORACLE` enumerates the frozen host before confirmation and computes
`Q*(w,j,a) = E[Y | w,j,do(a)]`. Its source advantage is

`A*(w,j,a) = Q*(w,j,a) - 0.5 * (Q*(w,j,0) + Q*(w,j,1))`.

It cannot use any confirmation outcome or sampled counterfactual. At the source
record it replaces rather than adds to ordinary GAE; all non-source trace,
bookkeeping, and diagnostics remain identical.

Both arms use full-batch analytic gradients, arm-local advantage centering and
RMS normalization, one update, and a common trust-radius scale frozen from the
calibration oracle direction so the held-out mean Bernoulli KL from 0.5 is at
most `0.02`. Parameter displacement norms must match within `1e-12`; work,
row counts, actor/value calls, token counts, and deployment counts must match
exactly.

### Mandatory noiseless competence gate

Before sampled confirmation, replace slot draws by their exact expectation and
run the otherwise identical one-step comparison. Competence passes only if:

- all six GAE pair-gradient signs match the oracle;
- GAE/oracle gradient cosine is at least `0.999`;
- the maximum favorable-pair held-out allocation-probability difference is at
  most `1e-6`; and
- the pair-aware head, Bellman residual, work, and update-scale checks pass.

Failure stops as an invalid comparator and cannot be called oracle headroom.

## Fixed-token native evaluation

Each confirmation root contains 32 held-out dyads per joiner, for exactly 96
tokens. Within a dyad, the two opportunities have the same joiner and every
generic field but use its favorable and unfavorable waiter. If their updated
logits are `z+` and `z-`, select the favorable opportunity with probability

`sigmoid(z+ - z-)`

using the common counter-keyed token uniform. Exactly one opportunity receives
`a=1`; the other receives `a=0`. Both are executed through the native physical
host on common service tapes. This interior stochastic allocation is frozen to
avoid B1's rank saturation; it may not be replaced by an argmax or repaired tie
rule after results.

For each arm and root report favorable-token fraction `A`, raw bounded utility,
and utility normalized to the prospective expected always-unfavorable versus
always-favorable span. Root is the inferential unit. For both allocation and
normalized utility, report paired oracle-minus-GAE mean, standard deviation,
and Student-t 95% interval using `t_0.975,11 = 2.2009851600916396`.

The native headroom gate requires all of:

- allocation and normalized-utility paired 95% lower bounds greater than zero;
- both paired means at least `0.10` of their full favorable/unfavorable span;
- GAE's favorable-token fraction has a root-level 95% lower bound greater than
  chance `0.50`; and
- common work, displacement, token, renewal, cost, and tape controls pass.

Probability movement alone is not a pass.

## Source-localized identity falsifier

Run one matched panel inside the same result command. Preserve ordered-pair
contexts, propensity, expected `Q*`, conditional slot tape, policy head, batch
size, optimizer geometry, and fixed-token evaluator, but sever the waiter
transition and pay the same pair- and action-conditioned sampled total service
at tick 3. This is explicitly a six-cell identity contextual bandit, not a
second learning mechanism.

Let `D_U_native` and `D_U_local` be normalized oracle-minus-GAE utility gaps.
A source-path-relevant pass additionally requires

`D_U_native - D_U_local >= 0.05`

with a paired root-level 95% lower bound above zero. If the local panel
reproduces the native gap, any oracle advantage is generic expected-Q
supervision/denoising and does not justify delayed waiter-credit investment.

## Frozen predictions and interpretation branches

- **Valid bounded source-path headroom:** support and noiseless competence pass;
  noisy native GAE remains above chance; oracle improves actual favorable-token
  allocation and bounded utility; and native utility headroom exceeds the
  source-localized gap by the frozen margin.
- **GAE sufficiency:** support passes and the noiseless comparator is competent,
  but native allocation or utility headroom fails. The host exposes real pair
  consequences but leaves no decision-relevant room over competent ordinary
  GAE at this update/data budget. Stop before relay.
- **Static identity/denoising:** native headroom passes but the source-localized
  panel reproduces it. The result is an identity contextual-bandit oracle gap,
  not path-specific credit headroom. Stop before relay.
- **Representation/comparator invalid:** ordered-pair expressibility, exact
  value, noiseless competence, support cells, or work/scale equality fails. No
  scientific headroom claim is available; report the exact invalid premise.
- **Evaluator null:** probabilities differ without actual token or utility
  change. Record proximal expression only and stop; no threshold or evaluator
  repair is allowed.

Support or headroom failure is a scientifically valid bounded negative result,
not a command failure. Only a contract anomaly, missing terminal artifact,
resource violation, or invalid comparator prevents scientific interpretation.

## Exact implementation, tests, result command, and artifacts

The conditional CM owns only these new files:

- `experiments/candidates/expressibility_gated_renewal_credit_relay/prerequisite_config.py`
- `experiments/candidates/expressibility_gated_renewal_credit_relay/prerequisite_experiment.py`
- `experiments/candidates/expressibility_gated_renewal_credit_relay/prerequisite_run.py`
- `tests/experiments/candidates/expressibility_gated_renewal_credit_relay/test_prerequisite.py`
- `temp/directions/expressibility_gated_renewal_credit_relay/exp/2026-08-28-10-clean-successor-02/**`

Existing B1 source, configuration, results, and tests are read-only. Shared core,
permissions, checkpoints, another direction, Portfolio files, and EM-owned docs
are out of scope.

The exact non-result verification command is

`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/experiments/candidates/expressibility_gated_renewal_credit_relay/test_prerequisite.py -q`.

The sole result-bearing command is

`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.expressibility_gated_renewal_credit_relay.prerequisite_run --stage all --result-output temp/directions/expressibility_gated_renewal_credit_relay/exp/2026-08-28-10-clean-successor-02/result.json`.

It may be launched exactly once after tests pass. It must write a terminal JSON
containing treatment and artifact identity; frozen constants, roots, lambda
selection, trust scale, pair/world support table, path-sever facts, noiseless
competence facts, per-root native and local arm observations, paired intervals,
criteria and branch, accounting, anomalies, runtime, and cap status. A valid
scientific null exits successfully with a complete artifact; a technical or
comparator-invalid stop is explicit and must not masquerade as a null.

Resource ceiling: one CPU worker, at most 15 wall minutes, 2 GiB peak RSS,
1,500,000 three-agent physical ticks, no restart, sweep, seed replacement,
threshold repair, or post-result enlargement. Stop on terminal artifact, any
resource limit, contract anomaly, or invalid prerequisite. CM interprets only
engineering/observation validity; EM alone interprets scientific meaning.

## Traceable basis

- `docs/research/candidates/expressibility_gated_renewal_credit_relay/evidence/2026-08-28-10-clean-successor-02-scope-and-grounding.md`
- `docs/research/candidates/expressibility_gated_renewal_credit_relay/external/2026-08-28-2026-08-28.10-clean-01a04a02-egrcr-successor-02-pro-innovator-prompt.md`
- `docs/research/candidates/expressibility_gated_renewal_credit_relay/external/2026-08-28-2026-08-28.10-clean-01a04a02-egrcr-successor-02-pro-innovator-response.md`
- `docs/research/candidates/expressibility_gated_renewal_credit_relay/EGRCR_B1_SCIENCE_CARD.md`
- `docs/research/candidates/expressibility_gated_renewal_credit_relay/EGRCR_B1_RESULT.json`
- public scientific commit `2b8f1ae0ea8c514bd333c45fe11275a2fabfbb81`
- direction starting HEAD `43c8208b8e1865536766598aa64f53f207df974d`
