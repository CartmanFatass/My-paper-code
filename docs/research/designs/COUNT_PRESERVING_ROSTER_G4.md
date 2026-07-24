# COUNT_PRESERVING_ROSTER_G4

Status: exact formal package completed with `NO_ACCESS_COUNT_ROSTER_G4`; the
package is closed against rerun, tuning, renaming or threshold/budget rescue.

## Independent algorithm boundary

This is not a rerun or rescue of `USEFUL_EFFECT_ROSTER_G3`. G3 remains closed as
`UNDERPOWERED_ACCESS_USEFUL_ROSTER_G3`. G4 preserves the exact G3 source,
observation, external demand-served utility, lifecycle events, profiles,
training/evaluation budget, thresholds and PPO path, while changing one named
algorithmic object: normalized roster aggregation versus count-preserving
roster aggregation. All G4 arms are trained anew under independent registered
seeds and compared only within G4.

## Source and protected semantics

Use the complete G3 demand supports for N=2/3/4, uniform positive deficit,
standing counts `d-one_hot(q)`, anonymous lifecycle-owned records, JOIN/RENEW/
TERMINAL_REPLACE events, temporary leave/rejoin history, nuisance gaps and the
same IID/held-out-cardinality/held-out-gap/held-out-joint profiles.

External reward and episode utility remain:

```text
U = sum_k min(service_count_k, demand_k) / sum_k demand_k
```

No intrinsic reward, diversity reward, uniqueness reward, deficit/count actor
input, identity, named role, future reference or task-specific shaping is added.

## Arms and matched inventory

The three arms are `TEAM_REC`, `ROSTER_ATTN` and `ROSTER_SUM`. Every arm owns an
independent copy of one complete inventory initialized from the same replicate
state: query encoder, token encoder, attention query, team GRU, base head,
roster treatment, team treatment, centralized critic and value head.

- `TEAM_REC`: exact G3 persistent public-history recurrent path.
- `ROSTER_ATTN`: exact G3 query-conditioned softmax attention path.
- `ROSTER_SUM`: masked learned token mean plus the raw four-way effect-count
  skip, zero-padded to hidden width, followed by the same roster treatment.

Only the active path receives actor gradients. The critic remains identical and
receives standing counts only through its frozen centralized input. The count
skip is computed solely from current standing commitment tokens and is
permutation invariant.

## Budget, backend and seeds

Keep the G3 budget unchanged:

```text
backend=cpu
torch_threads=1
replicates=5
updates_per_arm_replicate=120
episodes_per_update=512
ppo_passes=4
evaluation_episodes_per_cell=512
audit_rows_per_replicate=128
bootstrap_repetitions=10000
```

Use an independent G4 seed registry. There is no resume, checkpoint reuse,
backend mixing or CPU/CUDA comparison. Each arm/replicate must close equal
environment and optimizer exposure.

## Estimands and access

Primary:

```text
G_attn = U_ROSTER_SUM - U_ROSTER_ATTN
```

Mission comparator:

```text
G_team = U_ROSTER_SUM - U_TEAM_REC
```

Both use held-out-joint deterministic paired source clusters and hierarchical
bootstrap over replicate and source cluster. Access is specific to ROSTER_SUM;
no other arm can satisfy it on its behalf. The access floor remains 0.90 and the
meaningful gain margin remains 0.10.

## Consequence battery

On 128 held-out-joint ROSTER_SUM snapshots per replicate, retain the exact G3
battery and thresholds:

- natural optimal-action probability LCB >= 0.90;
- natural demand-served utility LCB >= 0.90;
- exact roster intervention action-TV LCB > 0.10;
- adapted-minus-replayed utility LCB > 0.10;
- duplicate-demand natural utility LCB >= 0.90; and
- zero-demand-label natural utility LCB >= 0.90.

The intervention replaces one standing effect from the exact source snapshot,
re-evaluates the same policy without copying a future result, and recomputes
utility from realized service. Lower diagnostics never bypass access.

## First-match result semantics

Apply exactly in this order:

1. `INVALID_OPERATIONAL_COUNT_ROSTER_G4`.
2. `SOURCE_NON_IDENTIFIABLE_COUNT_ROSTER_G4`.
3. `NO_ACCESS_COUNT_ROSTER_G4` when ROSTER_SUM utility UCB < 0.90.
4. `UNDERPOWERED_ACCESS_COUNT_ROSTER_G4` when its LCB < 0.90 <= UCB.
5. `COUNT_PRESERVING_ROSTER_SUPPORTED_G4` when both gain LCBs exceed 0.10
   and the full consequence battery passes.
6. `ROSTER_ATTN_SUFFICIENT_COUNT_ROSTER_G4` when `UCB(G_attn) <= 0.10`.
7. `TEAM_REC_SUFFICIENT_COUNT_ROSTER_G4` when `UCB(G_team) <= 0.10`.
8. `COUNT_ROSTER_REPRESENTATION_ONLY_G4` when both gain LCBs exceed 0.10
   and at least one consequence interval confidently fails.
9. `MIXED_UNDERPOWERED_COUNT_ROSTER_G4` for every other valid pattern.

A consequence confidently fails only when its UCB is at or below its threshold.
No lower-precedence metric relabels an earlier branch.

## Artifact and acceptance contract

The active runner exposes train/evaluate/analyze/exercise. Formal evidence
requires `formal=true`, one exact integrated source commit, token
`AUTHORIZE_COUNT_PRESERVING_ROSTER_G4_FORMAL_CPU_V1`, 15 final checkpoints,
120 evaluation files, 640 causal audits, source controls and 10,000 bootstrap
draws. The analyzer rederives metrics and invokes one pure selector.

A bounded exercise is always `formal=false` and must cover the three arms,
profiles, replay, optimizer/checkpoint restore, count/permutation invariants,
intervention, analyzer and formal rejection. Implementation and exercise cost
zero conclusion-bearing iterations. A valid formal run is iteration 5 and must
produce `docs/report/ITERATION_5.md` in Chinese before any terminal project
disposition.
