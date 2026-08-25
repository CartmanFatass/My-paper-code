# ASYNC_COMMITMENT_ROSTER_G3 information gate

Date: 2026-07-23

```text
source_commit=b5b67853a2012dd6957e30ad1a6d05d16dff02fe
artifact=logs/nonformal_async_commitment_roster_g3_20260723_pm1/result.json
formal=false
result=PASS_ASYNC_ROSTER_INFORMATION_GATE_G3
iteration_cost=0
iterations_remaining=2
```

## Accepted evidence

The focused test file passed five tests, including direct script execution and
fail-closed rejection of a forged `formal=true` artifact. The fresh CPU gate
closed 18,400 exhaustive cases:

| Active count | Cases | Independent utility | Shuffled-roster utility |
|---:|---:|---:|---:|
| 2 | 400 | 0.875 | 0.875 |
| 3 | 3,600 | 0.8333333333 | 0.8333333333 |
| 4 | 14,400 | 0.8125 | 0.75 |

Each of RENEW, JOIN, REJOIN, same-slot replacement and cross-slot replacement
contributed exactly 3,680 cases. Standing-label and physical-slot permutations
are complete; the editor context is anonymous and slot-invariant. Temporary
leave freezes the lifecycle-owned commitment, rejoin restores it even at a new
physical slot, terminal leave deletes it and a new lifecycle joins uncommitted.

ROSTER_EDITOR and TEAM_REC_ORACLE both attain utility 1.0. TEAM_REC_ORACLE
reconstructs the exact roster from the complete public event history, so the
gate deliberately retains the strongest ordinary persistent-state explanation.

In every case, replacing one retained commitment in the exact pre-edit snapshot
changes the canonical roster-aware choice. The adapted choice retains utility
1.0; replaying the natural choice yields utility 0.5, 2/3 and 0.75 for active
counts 2, 3 and 4. The corresponding utility gains are 0.5, 1/3 and 0.25.

## Disposition and counterexample correction

The source gate passes. It establishes an executable roster-to-edit-to-value
path under anonymous lifecycle transitions and proves that a no-roster editor
cannot match the constructive policies. It does not establish learned access or
an advantage over TEAM_REC.

The gate's uniqueness fraction is intentionally a structural audit quantity.
Using it unchanged as a learned formal objective would create
`CE-DIVERSITY-AS-UTILITY`: different commitment labels could score perfectly
without producing useful, demand-matched behavior. That would conflict with the
project rule that label diversity is not complementary coordination.

Therefore the exact information gate remains nonformal and is not promoted into
a conclusion-bearing G3 comparison. The successor source must make each held
commitment produce a realized effect and score external demand served. Some
demand states must require duplicate effects and some labels must be useless for
the current demand, so uniqueness alone cannot solve the task.

## Portfolio delta and next boundary

- C-EHC gains an executable multi-record lifecycle-owned roster but no learned
  advantage evidence.
- C-REC remains the complete simpler explanation at the gate: exact event
  history can reconstruct the roster.
- C-COORD advances to a concrete asynchronous edit intervention, but useful
  behavior rather than label diversity must carry the formal claim.
- C-BENCH passes structural roster identification and now requires a
  demand-weighted effect source.
- C-MEASURE retains roster-only intervention and exact lifecycle ownership.

```text
next_action=USEFUL_EFFECT_ROSTER_G3_EXECUTABLE_DEFINITION
action_class=zero_compute_design
formal_compute=not_launchable
iteration_cost=0
iterations_remaining=2
external_review_required_now=false
```

The next definition must compare a permutation-equivariant roster-conditioned
editor against matched TEAM_REC and NO_ROSTER controls, use realized service
effects and external demand utility, freeze held-out active-count/lifetime
transport and retain label-invariant natural mediation.
