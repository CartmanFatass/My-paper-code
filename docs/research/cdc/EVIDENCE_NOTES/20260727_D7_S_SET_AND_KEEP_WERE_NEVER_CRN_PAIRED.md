# SET and KEEP were never CRN-paired, and the test that guarded it could not fail

Found 2026-07-27 by adversarial review of the task-14 diff. **The defect is
pre-existing in `d3e0f72` and older; task 14 neither caused nor worsened it.** It
is recorded separately because it is the larger finding.

## What was frozen

R2 section "Replicates", carried into R3 unchanged:

> "two disjoint evaluation streams estimate selected SET and KEEP, **sharing
> continuation base streams under CRN**" … "`2/2` may support the frozen
> source-level branch because … **SET and KEEP remain CRN-paired**"

CRN pairing is not decoration. R2 lists it as one of the five clauses that make
`n_eval=2` admissible at all.

## What the code did

`EVAL_SHARED_CANDIDATE_TOKEN` existed at its definition, in `stream_seed`'s
docstring, and in three test lines. **No production caller ever passed it.**

`run_audit_event._run_replicate` passed `candidate_target_id=candidate_id` —
the literal `"KEEP"` for the KEEP batch and `z_id` for each SET candidate — so
the two arms derived different continuation seeds. Measured at the real audit
seeds:

```text
KEEP eval seeds : [3770370200483784479,  2709927185168036796]
SET  eval seeds : [1871084076329113661, 16290645780216242675]
KEEP == SET, as production called them : False
KEEP == SET, under the shared token    : True
```

Calibration had it too (`candidate_target_id=schedule`):
`constructive_mixed` → `16021786621951498903`, `null` → `4764739410229048655`.
So `B_m` was an unpaired contrast as well.

The **prefix** was genuinely shared — every arm is a `deepcopy` of one live
snapshot — which is why this survived the R2/R3 review of the shared-prefix
realization. The **continuation** was not. Post-`t_e` user RPGM motion and the
UAV-failure Bernoulli both draw from `env.np_random`, so at `n_eval=2` the SET
and KEEP arms of one event saw different user trajectories.

Consequence: `U* = mean(eval_set) − mean(eval_keep)` carried the difference of
two independent noise streams instead of a paired contrast. At two replicates
that is the difference between a persistence effect and an artifact — the exact
false claim the review was dispatched to prevent.

## Why no test caught it

`test_evaluate_phase_shares_seed_between_set_and_keep_via_shared_token` called
`stream_seed` twice with byte-identical kwargs and asserted equality:

```python
seed_for_set  = audit.stream_seed(**_seed_kwargs(..., EVAL_SHARED_CANDIDATE_TOKEN, 3))
seed_for_keep = audit.stream_seed(**_seed_kwargs(..., EVAL_SHARED_CANDIDATE_TOKEN, 3))
assert seed_for_set == seed_for_keep
```

That is `f(x) == f(x)`. It cannot fail for any implementation, including one
where no caller passes the token. It named the load-bearing invariant, sat in
the suite as though it covered it, and proved nothing.

The lesson generalizes: **a test that constructs its own inputs to match its own
expectation is testing the constructor.** The replacement drives
`run_audit_event` and records the seeds it actually derives, recovering the
identity from the clone context string. It fails against unfixed HEAD:

```text
AssertionError: SET candidate zA and KEEP must share the evaluate stream at
replicate 0; U* is a paired contrast or it is noise
assert 6089167641916663987 == 13650037090473485643
```

## The repair

`phase="evaluate"` now derives its seed from `EVAL_SHARED_CANDIDATE_TOKEN` in
both the audit and calibration paths; `phase="select"` keeps the per-candidate
id, because selection needs an independent stream per `z`. `phase` is itself
hashed, so the namespaces stay disjoint.

This is implementing a frozen ruling, not making one: R2 froze CRN pairing and
the code did not do it.

## What this changes, and what must go to External Pro

**Every `U*` and `B_m` this instrument has ever produced was computed unpaired.**
No D7.S event-aligned result has been published from it, so nothing in the
portfolio is retracted by this. But:

1. The numbers will move. Pairing reduces the variance of the contrast; it does
   not merely re-label it.
2. `bootstrap_ratio_ci`'s docstring justified resampling episodes rather than
   arms by asserting "arms are CRN-paired inside one episode". That assertion
   was false when written and is true only as of this repair. The prior append
   in `20260726_D7_S_PREFIX_REPLAY_IS_NOT_FIXED_HISTORY.md` flagged the
   docstring as wrong; this locates why.
3. Disclosure, not a decision: the repair makes code match contract, so it does
   not cross the boundary. Pro should be told before the run that the frozen
   CRN clause was unrealized until now, because it bears on whether `2/2`
   remains admissible.
