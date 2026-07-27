# D7.S audit run 2: valid, unresolved — and the branch label is wrong

The first formal D7.S event-aligned source audit completed 2026-07-27.

```text
run          = GitHub Actions 30289161086, tag d7s-audit-2
stage_commit = 1b17dfb0
contract     = D7_S_EVENT_ALIGNED_SOURCE_AUDIT, procedure d7s_event_aligned_v1
shards       = 8/8 success, no timeout, no killed shard
artifacts    = logs/d7s_audit_2_30289161086/
```

## Mechanical validation — clean

| Check | Value |
|---|---|
| `smoke` | `False` |
| `conformance.ok` | `True` |
| invalidated pairs | 0 |
| `topology_hash_ok` | `True`, zero failures |
| `arm_distinct_ok` | `True` |
| `support.ok` | `True` — 8/8 calibration topologies, 8/8 audit topologies |
| `all_seed_controlled` | `True` |
| topology seeds | `20260726`–`20260733`, the frozen initial set |

The pooler accepted the eight shards, which is itself a check: it refuses unless
every shard shares the contract and procedure version, every `smoke` flag is
false, the shards' seed sets are pairwise disjoint, and their union equals a
frozen set.

`all_seed_controlled=True` is the R3 §E provenance the prior Stage B ruling found
missing. Every episode ran in a world that can be regenerated, so this run is not
in the position ep64 was in and its contrasts are matched evidence.

Qualifying episode support, against `N_CALIBRATION_EPISODES = N_AUDIT_EPISODES = 8`
and `MIN_SUPPORT_EPISODES_PER_TOPOLOGY = 4`:

```text
seed      calib  audit
20260726      6      7
20260727      6      6
20260728      6      8
20260729      5      8
20260730      7      7
20260731      8      7
20260732      8      7
20260733      7      4      <- exactly at the per-topology minimum
total        53     54
```

All eight topologies qualify on both limbs. `20260733` sits exactly on the
threshold; support would still have held at seven qualifying topologies against
`MIN_SUPPORT_TOPOLOGIES = 6`.

## The estimator output

```text
b_stable_lcb   -0.077367
b_flex_lcb     -8.648833
t_stable_ucb   +7.206993
t_stable_lcb   -2.189143
t_flex_lcb    -14.293054
t_flex_ucb     +3.115871
part_a          NOT_APPLICABLE
```

Recorded branch: **`SOURCE_NECESSITY_UNRESOLVED`**.

No affirmative branch could fire: every one of `stable_clears`, `flex_clears`,
`flex_affirmative_miss` and `stable_affirmative_miss` requires a strictly
positive `b_*_lcb`, and both are negative.

## The branch label is wrong, and the defect was found hours earlier

`20260727_D7_S_A_RESULT_BRANCH_THAT_CANNOT_FIRE.md` recorded that
`assemble_audit_result` passes `primary_g_degenerate_flag=False` as a hardcoded
literal and never calls `primary_g_degenerate`, making branch 3
`PRIMARY_G_DEGENERATE` structurally unreachable. That note argued the failure is
conservative — a degenerate run reports unresolved or invalid, never an
affirmative result — and that **if this run came back unresolved, the degeneracy
question would be open and answerable post hoc from the recorded bounds.**

It came back unresolved. Answering it, using the instrument's own functions
against its own recorded output:

```text
b_stable_lcb > 0                                  False
b_flex_lcb   > 0                                  False
b_m_positive_lcb                                  False
primary_g_degenerate(arm_invariant=False,
                     b_m_positive_lcb=False)      True

decide_branch(..., primary_g_degenerate_flag=False)  SOURCE_NECESSITY_UNRESOLVED
decide_branch(..., primary_g_degenerate_flag=True)   PRIMARY_G_DEGENERATE
```

**Under the frozen contract's own branch 3, this run is `PRIMARY_G_DEGENERATE`.**
The instrument could not report it because the flag is hardcoded.

### What this does and does not change

- **It does not inflate a claim.** Both labels are non-affirmative. Nothing is
  being reported as source necessity that is not.
- **It does not invalidate the run.** Conformance, support, provenance and
  topology pinning are all clean, and the bounds are what they are.
- **It changes the diagnosis, and therefore the next action.**
  `SOURCE_NECESSITY_UNRESOLVED` says the estimator ran and did not resolve —
  which invites more power, more replicates, more topologies.
  `PRIMARY_G_DEGENERATE` says B_m could not establish a positive source-control
  contrast at all — which says the *instrument or the primary-G construction* is
  the thing to fix, and that adding replicates would be a power rescue of a
  degenerate design.

Those two readings point at opposite next experiments, which is exactly the cost
named when the branch was found unreachable.

### Marked as inference

`b_m_positive_lcb` has **no production derivation** — the function that would
compute it is never called, so there is no frozen mapping from the recorded
bounds to that boolean. Reading it as `b_stable_lcb > 0 and b_flex_lcb > 0` is
the natural reading of "B_m cannot establish a positive source-control contrast"
and both limbs fail it by a wide margin on the flex side, but **it is Project
Manager inference, not repository fact and not an external ruling.**

The disposition — whether this run is read as `PRIMARY_G_DEGENERATE`, and whether
the driver is wired to compute the flag — is a change to a result branch and
belongs to External Pro. It is carried into the result round, not decided here.

## Cost

Eight shards in one wave against a 355-minute per-shard self-stop; none came
close to the ceiling and none was killed, so the recovery rule for an indivisible
topology was not needed.
