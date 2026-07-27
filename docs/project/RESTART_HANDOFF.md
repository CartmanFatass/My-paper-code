# Restart handoff — 2026-07-27, after the first formal D7.S audit

Successor PM: read this, then `docs/project/CURRENT_WORK.md`. Everything below is
committed and pushed on `untied-k`. Nothing is half-applied.

Replaces the earlier 2026-07-27 handoff, whose whole open list — two confirmed
D7.S guards, two verified Scenario-7 guards, five unverified leads — is closed.

## The only boundary

```text
next_boundary = PRO_ROUND_ON_THE_D7S_AUDIT_RESULT
```

The audit ran. It is valid, non-affirmative, and **its recorded branch label is
wrong**. That is the round's question and it is the first thing to do.

## What the run returned

```text
run 30289161086, tag d7s-audit-2, stage_commit 1b17dfb0
8/8 shards success in ONE wave, none near the 355-minute self-stop
artifacts logs/d7s_audit_2_30289161086/
```

Mechanical validation clean: `smoke=False`, conformance ok, zero invalidated
pairs, zero topology-hash failures, `arm_distinct_ok`, support 8/8 both limbs,
`all_seed_controlled=True` — so this run is **not** in ep64's position.

```text
b_stable_lcb  -0.077367     b_flex_lcb    -8.648833
t_stable_ucb  +7.206993     t_stable_lcb  -2.189143
t_flex_lcb   -14.293054     t_flex_ucb    +3.115871
branch = SOURCE_NECESSITY_UNRESOLVED      part_a = NOT_APPLICABLE
```

No affirmative branch could fire: each requires a strictly positive `b_*_lcb`.

### The label dispute, which is the round

`assemble_audit_result` passes `primary_g_degenerate_flag=False` as a **hardcoded
literal** and never calls `primary_g_degenerate`. Branch 3 `PRIMARY_G_DEGENERATE`
is structurally unreachable. Evaluated post hoc with the instrument's own
functions on its own output, the flag is `True` and the branch is
`PRIMARY_G_DEGENERATE`.

Nothing is inflated — both labels are non-affirmative. What changes is the next
experiment. *Unresolved* invites more replicates, topologies, power. *Degenerate*
says B_m established no positive source-control contrast at all, so more
replicates would be a power rescue of a degenerate design. Opposite directions.

**Do not decide this yourself.** Wiring a dead result branch is a change to a
result branch. The mapping from recorded bounds to `b_m_positive_lcb` is PM
**inference** — there is no production derivation, because the function is never
called. Carry that qualifier into the question.

**Do not write `docs/report/ITERATION_30.md` before the round rules.** Step 8 is
Pro-decision-then-report, and 30 is the conclusion-bearing one.

## Guard state

Ten unfailable guards repaired today, each watched red under a mutation the PM
ran itself rather than the implementer's demonstration. Suites:
`tests/audit_d7_s_event_aligned_test.py` **183 passed**,
`tests/scenario7_energy_aware_test.py` **47 passed**.

Evidence notes, all `docs/research/cdc/EVIDENCE_NOTES/20260727_*`:
`S7_THREE_MORE_UNGUARDED_AND_TWO_LEADS_REFUTED`,
`S7_FULL_SWEEP_THE_REWARD_ITSELF_IS_UNGUARDED`,
`D7_S_A_RESULT_BRANCH_THAT_CANNOT_FIRE`,
`D7_S_AUDIT_2_RESULT_AND_A_MISLABELLED_BRANCH`.

### Open, deliberately not repaired

- **Three dead functions**: `primary_g_degenerate` (the round question),
  `qos_component_saturated` (pure dead code), `expansion_allowed`. The last means
  the §9 "one permissible expansion" predicate **is enforced by no code at all** —
  expansion happens by a human passing `--topology-seeds`. `CURRENT_WORK` states
  that rule as though it were mechanized. It is not.
- **Over half of `scripts/audit_d7_s_event_aligned.py` is unswept**, listed
  function by function in `D7_S_A_RESULT_BRANCH_THAT_CANNOT_FIRE`. Neither that
  file nor the Scenario-7 environment may be read as audited.

## Four traps paid for today

- **A worktree does not arrive on your branch.** Three separate `isolation:
  worktree` dispatches landed on `4866eb4e`, an unrelated line. Each child
  noticed and reset — that is the only reason their findings mean anything. Make
  every worktree child report the commit it actually ran at.
- **Prove the mutation took effect before reading the green.** `config_1.py:504`
  looks like the governing `docking_horizontal_speed_mps` and is dead code;
  `_build_profile_overrides` hardcodes twelve such fields and the proxy reads
  them before the base `Config`. A mutation there is inert, and I recorded its
  green as a finding before catching it. The enumeration is in the S7 full-sweep
  note. Read the value back through a constructed env.
- **A guard that fails only when everything fails at once is the same defect one
  level up.** The first branch-boundary repair reddened when all four predicates
  were loosened together and stayed green when only `flex_clears` was. Mutate
  each predicate individually.
- **Push before you commit anything review-bound.** The drift guard blocked a
  commit because an earlier one was unpushed and the review contract requires the
  remote to be readable. It was right; the fix is to push, never `--no-verify`.

## Standing constraints that make a decision wrong if forgotten

```text
branch_scope=untied-k only, never touch another branch
formal_compute=user authority only
intermediate_authorization_prompts=forbidden
same_file_concurrent_writes=forbidden
```

The user granted full permission for the 2026-07-27 overnight session and that is
what authorized the `d7s-audit-2` tag push. **Do not treat that as standing** —
the next formal run needs its own authorization.

The workstation is shared. Check `scripts/check_compute_free.ps1` and read
`heavy_pids` before any local run; the other line's training ran most of today as
pid 4268 and finished. `COMPUTE_BUSY` from our own work is a different case than
from theirs — see `AGENTS.md`, Standing authorization.

**Unresolved and the user's to settle:** ownership of `untied-k`. Another session
committed `d3e0f72` asking that ownership be established first.

## One correction to the cloud vehicle doc

`COMPUTE_ROUTING.md` said only ~5 of 8 matrix shards run at once, so a sharded
run is two waves. Counted on this run: **8 of 8 concurrent, one wave.** Expected
wall clock is per-shard time, not double it. Corrected at `033a2efe`.
