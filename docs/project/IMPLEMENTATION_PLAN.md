# HA-CTSE Active Implementation Plan

Updated: 2026-07-20
Status: IMPLEMENTATION_COMPLETE_AWAITING_GIT
Work ID: `read-only-opportunity-authority-use-audit-20260720-retry1`
Base/source commit: `c47f72cb5eb3c455fcccec862bd26c0090d711f1`

## 1. Accepted evidence source and estimand

Implement only `READ_ONLY_OPPORTUNITY_AUTHORITY_AND_USE_AUDIT`. The existing
`INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT` result remains unchanged.
This source reads the frozen G0 result and checkpoints, replays deterministic
learned F1, frozen F1, and current routing-oracle behavior, and computes one
non-causal structural ceiling. It performs no training, sampling, optimizer
step, behavior-path mutation, checkpoint write, or scientific successor launch.

For evaluation episodes `0..255`, let `Y_e` be the exact set of episode outcomes
reachable by changing skills only at the realized event frontiers while retaining
the fixed supplied mapping `0/1/2 = IDLE/PERSIST/SHORT`. Compute jointly across
episodes:

`G_H = max_{y_e in Y_e} min(mean(P), mean(S), mean(U))`.

The registered floor is hindsight-authority feasible iff `G_H >= 0.95`. The
maximization selects one reachable outcome per episode; separate maxima for P
and S may not be combined. Hindsight may read the complete membership, wave,
opportunity, and frontier ledger but cannot change any ledger value and is not a
policy, baseline, oracle repair, or causal comparator.

Every completed SHORT unit is assigned to exactly one of `PREWAVE_SHORT`,
`POSTWAVE_SINGLETON`, `POSTWAVE_MULTIOWNER_FIRST`,
`POSTWAVE_MULTIOWNER_LATER`, or `OTHER_OR_NO_TIMELY_OPPORTUNITY`. For class `c`,
use per-episode excess work `D[e,c] = W_learned[e,c] - W_oracle[e,c]`. It is
decisive only when the paired 10,000-resample episode-bootstrap LCB95 of
`D[:,c] - D[:,d]` is strictly positive for every other class `d`.

## 2. Frozen contract

- Inputs are the formal `update_000_high.pt` and `latest_high_only.pt`, source
  result, evaluation episode IDs `0..255`, and the unchanged clean carrier.
- Seeds remain task/evaluation `97_057`, opportunity/frontier `77_057` with
  streams `0/1`, action `87_057` stream `0`, and bootstrap `107_057`.
- Horizon is 80, gaps are uniform integers `1..19`, waves retain their registered
  candidate windows, window length 4, streak target 2, membership schedule, and
  total short requirement 24.
- Learned and frozen are deterministic F1 reads; frozen is the update-zero state.
  Current oracle is the existing frontier-filtered constructive rule.
- The audit creates no optimizer. Report high and low optimizer steps as zero
  and require byte-identical high tensors before and after every read.
- Existing probability factorization, exact action support, active masks,
  lifecycle epochs, owner credit, physical/opportunity/event/lifetime clocks,
  recurrent state, RNG streams, replay rows, carrier state, and checkpoint
  schema are read-only.

## 3. Files and replacement ledger

Only these paths may change:

- `docs/project/IMPLEMENTATION_PLAN.md` — this active executable design.
- `ha_ctse_process/dynamic_roster_opportunity_audit.py` — new audit library with
  `materialize_exogenous_frontiers`, `solve_frontier_hindsight_pareto`, a tiny
  brute-force reference, deterministic three-arm replay, SHORT classification,
  dominance bootstrap, working/initial reads, validity, and branch selection.
- `scripts/run_clean_process_opportunity_authority_audit.py` — new
  evaluation-only CLI and terminal result/status plumbing.
- `tests/ha_ctse_process_clean_opportunity_authority_audit_test.py` — one focused
  deterministic contract test.

All supplied-executor, event-runtime, testbed, prior runner/test/result, and
checkpoint files remain read-only. No existing file is obsolete or deleted.

## 4. Materialization and hindsight data flow

Replay the three existing arms through `SuppliedExecutorVectorRuntime` under
`torch.no_grad()` and deterministic high evaluation. At each primitive time,
capture audit-owned copies of the exposed transaction frontier, sampled order,
token rows, active skills, primitive actions, membership delta, wave state,
persistent owner, contribution state, and terminal outcome. Require the realized
frontier/order ledger to agree across learned, frozen, and oracle.

`materialize_exogenous_frontiers` converts that agreed trace plus the immutable
clean task ledger into an audit ledger. Behavior replay functions do not accept
this future ledger. Only `solve_frontier_hindsight_pareto` receives it.

The episode DP state contains only future-relevant task state: lifecycle skills
including temporary-absence retention, persistent owner, current wave,
per-owner SHORT streak/contribution flags, and wave completion. Numeric labels
are capped persistent units and total completed SHORT work. At each time it:

1. applies the frozen JOIN/temporary-LEAVE/REJOIN/terminal-LEAVE event;
2. opens the registered wave if due;
3. enumerates all three actions only for owners in the realized frontier;
4. keeps every non-frontier skill unchanged;
5. applies unchanged persistent and SHORT dynamics in presentation order;
6. Pareto-prunes only labels dominated inside the same future-relevant state.

Convolve the 256 episode Pareto outcome sets, pruning dominated aggregate P/S
sums, and maximize the joint minimum. The tiny brute-force solver enumerates
every legal frontier action sequence and must return the same outcome set.

## 5. Behavior-use and probability diagnostics

At each wave arrival, snapshot pre-event active skills. Record every within-wave
`SET` to `SHORT` with frontier size and token position. A counted completion is
`PREWAVE_SHORT` only when its owner was already SHORT at arrival and no
within-wave SET-to-SHORT preceded it. Otherwise use the most recent causally
preceding SET-to-SHORT: singleton, first multi-owner token, or later multi-owner
token. If none exists, use `OTHER_OR_NO_TIMELY_OPPORTUNITY`. Assert exactly one
class per completed unit.

Also report pre-wave SHORT share, owners with opportunity no later than
`t_wave + 2`, within-wave SET-to-SHORT counts, persistent-owner recovery delays,
frontier/token/membership strata, and pre-wave configuration lead-time and
candidate-window concentration. These are descriptive; no threshold is added.

For learned stored rows with `frontier_size > 1` and `token_position > 0`, call
the existing no-state-change `replay_token_distribution` with identical stored
inputs and parameters, changing only `summary_source` between `working` and
`initial`. Report total variation, duplicate-PERSIST probability reduction,
missing-SHORT probability increase, and association with recorded completion or
persistent recovery. This is not an F0 treatment or utility estimate.

## 6. Validity and terminal branches

Validity requires exact frozen-result P/S/U reproduction for all requested IDs;
identical frontiers/orders across arms; frontier-only action change; primitive
action/active-skill identity; future-ledger isolation; tiny DP/brute-force
equivalence; a full-step constructive authority control; unique contribution
classification; zero optimizer steps; zero high-tensor drift; finite values; and
exact registered episode, seed, bootstrap, and checkpoint headers.

Branch in this priority:

1. any validity failure -> `INVALID_OPPORTUNITY_AUTHORITY_AUDIT`;
2. `G_H < 0.95` -> `HINDSIGHT_OPPORTUNITY_FLOOR_UNREACHABLE`;
3. floor feasible, decisive `PREWAVE_SHORT`, no decisive
   `POSTWAVE_MULTIOWNER_LATER`, and no positive completion/recovery-associated
   working-summary direction ->
   `HINDSIGHT_REACHABLE_PREPOSITIONING_REDUCTION`;
4. floor feasible, decisive `POSTWAVE_MULTIOWNER_LATER`, positive directional
   working-summary shift, and completion/recovery association ->
   `HINDSIGHT_REACHABLE_MULTIOWNER_PREFIX_CANDIDATE`;
5. otherwise -> `HINDSIGHT_REACHABLE_MIXED_OR_UNIDENTIFIED`.

The runner records the branch only and never selects or launches a successor.

## 7. Performance and focused evidence

Batch behavior replay through the existing vector runtime and reuse immutable
checkpoint tensors. Keep simulator and DP loops only for causal state evolution.
Use compact immutable DP keys and per-key Pareto pruning; combine episode outcome
frontiers incrementally rather than enumerate cross-episode trajectories.
Accumulate diagnostics in audit-owned Python/NumPy structures and serialize only
at the terminal boundary.

The focused test uses CPU and reduced episode/tiny-ledger counts without changing
formulas. It covers frozen-result episode reproduction, DP/brute-force
equivalence, frontier/action enforcement, future-ledger isolation, unique SHORT
classification, working-versus-initial no-state-change reads, zero optimizer
steps, and zero parameter drift. It does not run the full 256-episode audit.

Accepted focused evidence: the new test passes; a separate read-only one-episode
materialized-ledger check returns a finite exact DP result with 34,582 explored
control states. The registered 256-episode audit has not been launched.

## 8. Non-goals

No training or formal audit launch; no core/testbed/supplied-executor edit; no
oracle tuning; no threshold, gap, wave, deadline, streak, membership, horizon,
reward, utility, seed, episode, bootstrap, model, checkpoint, probability,
credit, mask, RNG, replay, recurrent, lifecycle, or clock change. No F0/F1,
direct, low, oracle, or critic optimization. No intrinsic reward, posterior,
graph, communication, latent, simplex, hazard, scheduler, identity, role, slot,
or future-ledger policy input. No Git operation, external review, integration,
or successor route.
