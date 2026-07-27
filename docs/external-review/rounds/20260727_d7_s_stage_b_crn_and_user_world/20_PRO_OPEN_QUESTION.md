# Stage B on episode-world provenance — and a frozen clause that was never realized

Stage B code-science alignment on the diff implementing R3 section E. It carries
two disclosures. The first is larger than the diff and is the reason this round
exists before compute rather than after it.

No verification labor is requested. Every number below is measured, with its
provenance named; nothing asks you to confirm an inventory.

Read at `stage_commit` on `untied-k`, pushed.

The science landed at `04f7b0b`. `stage_commit` is later only because this
question and two record corrections are committed after it; `git diff
04f7b0b..stage_commit -- envs scripts tests` is **empty**, so every source and
test file below is byte-identical to the commit that implemented the work.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R3.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md`
- `envs/pettingzoo/scenario_base.py`
- `scripts/audit_d7_s_event_aligned.py`
- `scripts/pool_d7_s_event_aligned_shards.py`
- `tests/audit_d7_s_event_aligned_test.py`
- `tests/env_user_population_determinism_test.py`
- `docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_SET_AND_KEEP_WERE_NEVER_CRN_PAIRED.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_USER_WORLD_IS_A_FUNCTION_OF_BS_QUADRANT.md`

R2 is listed because Q2 turns on its `§Replicates` wording; R3 is the frozen
contract the diff must instantiate.

## What was implemented

- **Task 14 (R3 §E).** The audit's user world now derives from the registered
  `user_world_seed` instead of construction-time OS entropy.
  `envs/pettingzoo/scenario_base.py::regenerate_user_world`;
  `scripts/audit_d7_s_event_aligned.py::build_pinned_env` step 8;
  `episode_world_fingerprint`; `episode_world_provenance` in the artifact,
  carried through `scripts/pool_d7_s_event_aligned_shards.py`.
- **A CRN repair** — see Q2. `_run_replicate` and the calibration fork now pass
  `EVAL_SHARED_CANDIDATE_TOKEN` during `phase="evaluate"`.

175 focused tests pass. Real-environment clone conformance re-verified after the
change: `CLONE_CONFORMANCE_PASS`, all seven conditions, zero reconstruction
replays.

Evidence notes, both under `docs/research/cdc/EVIDENCE_NOTES/`:
`20260727_D7_S_SET_AND_KEEP_WERE_NEVER_CRN_PAIRED.md`,
`20260727_D7_S_USER_WORLD_IS_A_FUNCTION_OF_BS_QUADRANT.md`.

## Q1 — the three Stage B questions

For the diff as a whole: does the code instantiate the frozen R3 contract; could
a test pass through the wrong mechanism; could an alternate implementation
explanation change the registered conclusion?

Return `ALIGNED`, `MISMATCH` (naming the frozen assertion and the conflicting
code path), or `SCIENTIFIC_AMBIGUITY` (naming one previously unstated
result-changing choice).

## Q2 — disclosure: SET and KEEP were never CRN-paired

R2 §Replicates, carried into R3 unchanged, freezes: *"two disjoint evaluation
streams estimate selected SET and KEEP, **sharing continuation base streams
under CRN**"*, and lists CRN pairing as one of five reasons `n_eval=2` is
admissible at all.

`EVAL_SHARED_CANDIDATE_TOKEN` existed at its definition, in `stream_seed`'s
docstring and in three test lines. **No production caller ever passed it.**
`_run_replicate` passed the candidate id, so KEEP and each SET `z` derived
different continuation seeds; calibration passed the schedule, so `B_m` was
unpaired too. Measured at the real audit seeds:

```text
KEEP eval seeds : [3770370200483784479,  2709927185168036796]
SET  eval seeds : [1871084076329113661, 16290645780216242675]
```

The **prefix** was genuinely shared — every arm is a `deepcopy` of one live
snapshot — which is why the R2/R3 review of the shared-prefix realization did
not surface it. The **continuation** was not, and post-`t_e` user RPGM motion
and the UAV-failure Bernoulli both draw from `env.np_random`. So `U* =
mean(eval_set) − mean(eval_keep)` was the difference of two independent noise
streams rather than a paired contrast.

The guarding test called `stream_seed` twice with byte-identical kwargs and
asserted equality — `f(x) == f(x)`, unfailable for any implementation. It is
replaced by one driving `run_audit_event`, verified to fail against unfixed
`HEAD` before being accepted.

We repaired it as *implementing a frozen ruling, not making one*: R2 froze CRN
and the code did not do it. No event-aligned result has ever been published from
this instrument, so nothing is retracted. But every `U*` and `B_m` it ever
produced was unpaired.

**Q2(a).** Is the repair the correct realization of R2 §Replicates, or does your
ruling intend something different by "sharing continuation base streams"?

**Q2(b).** Does `n_eval=2` remain admissible? You listed CRN pairing as one of
five supporting clauses; it is now true for the first time, so the `2/2` floor
is better supported than when frozen, not worse. Confirm, or restate the floor.

- If you rule **`2/2` stands** → answer Q3 and Q4.
- If you rule **the floor must move** → name the volume and whether the
  already-frozen `n_select=2` moves with it; then Q4 only.

## Q3 — disclosure: one variance factor moved a level

Measured, 400 draws each way. The **generator and its parameters are unchanged**:
per-cluster spread `109.59 ± 31.99` old versus `110.09 ± 32.83` new; cluster
count config-fixed at 5.

What changed is where one factor lives. The remote-cluster corner is chosen from
the BS quadrant. Under the old ordering that quadrant came from the
construction-time layout, which `build_pinned_env` then **discarded** and
replaced with the pinned coordinates — so it was an unseeded, roughly uniform,
**per-episode** draw over four corners. Under the new ordering it is a
deterministic function of the pinned topology and is **constant within a
topology**.

R3 §E says user worlds "contribute through within-topology episode variation".
The bootstrap machinery is unchanged, but the variance structure it estimates is
not: within-topology spread compresses and the between-topology term loads.

We judge the new behaviour more faithful — under the old ordering the "remote"
cluster was positioned relative to a base-station layout the episode then threw
away, so in roughly three episodes in four the remote users were not remote from
the base stations actually in use, which is the premise Scenario 7 rests on. We
are not proposing a reversal; we are putting the change on the record before the
run rather than after the within-topology spread comes out small.

**Q3(a).** Does the estimand survive this unchanged?

- If **yes** → is any change needed to the hierarchical bootstrap's level
  structure, given the largest geometric factor is now at the topology level?
- If **no** → name what must change: the estimand, the level structure, or the
  user world's status as a nested episode-level random factor.

**Q3(b).** Should the user world instead be made to vary *within* a topology by
construction — i.e. should the remote corner be drawn per episode from
`user_world_seed` rather than inherited from the pinned quadrant? That would
restore the old variance structure while keeping reproducibility, at the cost of
episodes whose remote cluster is not remote from the pinned base stations. We
have not implemented this; it is a real alternative and it is your call, not
ours.

## Q4 — the audit launch

Cost is measured, not projected. Local rate `0.0615 s/step`; per topology
`2.29 h` at `|Z|=3` to `4.18 h` at `|Z|=8`.

GitHub-hosted compute was benchmarked at `0.0864 s/step` (1.405× slower, run
`30245735762`), putting `|Z|=8` at `5.77 h` against a 6-hour hard job kill. The
legal-set size is data-determined, so which shards run long cannot be known
before launch.

We first read that as excluding the hosted route, on the reasoning that a killed
shard is unrecoverable. **That reasoning was wrong and is withdrawn.** A topology
cannot be *split*, but it can be re-run *whole* and pooled, because the pooler
keys on the seed set rather than on run identity; with `fail-fast: false` every
other shard keeps its artifact. So an overrun costs one shard's wall clock, not
the run. The hosted route is tight, not excluded, and a run is in flight.

This bears on nothing you are asked to rule on — the vehicle does not touch the
estimand — and is stated only because the previous round's cost framing is
otherwise left standing in the record.

**What is in flight, so Q4 is not asked in bad faith.** An 8-shard hosted run is
executing now. It is a *vehicle probe*: we are reading its wall clock, its
conformance, and its `episode_world_provenance` block, and nothing else. No
margin, no `U*`, no `B_m` will be read or pooled until you have ruled — so this
round is not being answered by the compute while you consider it. If you rule
against launch, the artifacts are discarded unread.

**Q4.** Given your answers above, does the audit launch at `stage_commit`?

- If **yes** → confirm `n_select`/`n_eval` and the topology set (8 registered,
  expanding to 16 under §9's conditions).
- If **no** → name the single blocking item.
