# COUNT_PRESERVING_ROSTER_G4 formal result

Date: 2026-07-23

```text
source_commit=64a04fafd5abd4e2955382063a97bff290548513
run=logs/formal_count_preserving_roster_g4_cpu_20260723_64a04fa_r1
backend=cpu
torch_threads=1
formal=true
result=NO_ACCESS_COUNT_ROSTER_G4
conclusion_bearing_iteration=5
iterations_remaining=0
```

## Evidence closure

The fixed Luna-low experiment operator completed the exact foreground
`train -> evaluate -> analyze` pipeline with exit code zero for every phase and
without restart. Project Manager then ran the formal validator and independently
recomputed the pure first-match selector from serialized predicate inputs.

The evidence closes 15 final update-120 checkpoints, 120 referenced evaluation
files containing 61,440 rows, 640 ROSTER_SUM causal-audit rows, all source
controls and every checkpoint/evaluation reference. Source commit, formal token,
independent G4 seeds, CPU/one-thread identity, equal exposure, optimizer/RNG,
schema, demand ledger, audit arm, realized utilities and temporary-residue
contracts pass. Operational validity and source identifiability are true.

## Registered result

| Quantity | Mean | CI95 |
|---|---:|---:|
| TEAM_REC utility | 0.8484375 | [0.8378906, 0.8583008] |
| ROSTER_ATTN utility | 0.8801758 | [0.8703101, 0.8899414] |
| ROSTER_SUM utility | 0.8738281 | [0.8580078, 0.8875000] |
| `G_attn=U_SUM-U_ATTN` | -0.0063477 | [-0.0243164, 0.0119141] |
| `G_team=U_SUM-U_TEAM_REC` | 0.0253906 | [0.0030273, 0.0411133] |

ROSTER_SUM is the tested arm. Its utility UCB 0.8875 is below the frozen 0.90
access floor, so first-match step 3 returns `NO_ACCESS_COUNT_ROSTER_G4`.
No gain or consequence diagnostic can relabel this branch.

The lower-precedence battery is also incomplete: natural utility mean is
0.85156, exact optimal-action probability is 0.30778, intervention TV is
0.14388, and adapted-minus-replayed utility is 0.06875. A roster perturbation
still changes probabilities, but it does not yield accessible demand matching
or sufficient adapted value.

## Scientific correction

`CE-COUNT-PRESERVATION-AS-SOLUTION` is now accepted: exact current-roster counts
and a linearly sufficient demand-minus-count path do not by themselves make PPO
learn a stable held-out editor. Count preservation is a valid interface
property, not an established algorithmic solution.

`CE-CAUSAL-RESPONSE-WITHOUT-COMPETENCE` is strengthened: both G3 and G4 show
positive roster-intervention response while failing to establish robust access.
Sensitivity to a mechanism input is therefore insufficient evidence of natural
competence or algorithmic advantage.

The same-budget G4 attention comparator reaches 0.88018, below its independent
G3 mean 0.89385. Historical cross-run mean shifts cannot be used as causal arm
effects, but together they reinforce training-seed/optimization instability.
The identified source and constructive oracle remain valid.

## Five-iteration chain disposition

1. G0: valid `NO_ACCESS_THIS_BENCHMARK`; the original pair is closed.
2. G1: valid `ORDINARY_EXPLANATION_G1`; per-member recurrence is sufficient.
3. G2: valid `TEAM_REC_SUFFICIENT_HANDOFF_G2`; the link is causal but team
   recurrence is sufficient for one global bit.
4. G3: valid `UNDERPOWERED_ACCESS_USEFUL_ROSTER_G3`; explicit roster attention
   is responsive and best in mean, but access is unstable and gain unsupported.
5. G4: valid `NO_ACCESS_COUNT_ROSTER_G4`; direct multiplicity preservation does
   not repair access or beat normalized attention.

The chain does not establish an EHC/roster advantage. It does establish a
narrower scientific map: explicit lifecycle-held state can be causal, but the
tested recurrence/attention/count interfaces do not robustly convert it into
held-out demand-matched behavior under the frozen PPO budget. C-BASE/
optimization remains a plausible bottleneck; C-EHC and C-COORD remain
unsupported rather than globally disproved.

```text
terminal_disposition=FIVE_ITERATION_CHAIN_COMPLETE
autonomous_research_grant=EXHAUSTED
conclusion_bearing_iterations_consumed=5
iterations_remaining=0
successor_status=not_authorized
recommended_future_question=representation_fixed_optimization_access_separation
```

Any new diagnostic, implementation or formal run requires a new user-defined
research boundary. No external review is needed to interpret this unambiguous
first-match result.
