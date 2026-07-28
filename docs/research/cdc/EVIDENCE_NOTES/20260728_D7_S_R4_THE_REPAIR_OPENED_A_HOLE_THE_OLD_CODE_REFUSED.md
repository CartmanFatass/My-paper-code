# D'' — the gate that was skipped, and what it found

Step F of R4 closure. The Stage B re-review of D' (`28d6933f`) returned
**REJECT on both conformance and semantics**. Two blocking defects, both
reproduced by the Project Manager before any repair was specified.

```text
gate skipped   step D returned REJECT; D' repaired it; the PM verified D'
               personally and went straight to step E. Nothing adversarial
               ever read the repair. CURRENT_WORK said "A-E COMPLETE" while
               both defects below were in the tree.
verdict        conformance=REJECT  semantics=REJECT
repair         D''
```

## B-1 — the repair opened a hole the code it replaced refused

`r4_declared_population_identity`, added by D' to give the sharded production
route a path to R4 identity, checked **membership** and nothing else. A repeated
seed is a member.

```text
r4_declared_population_identity([20260734, 20260734, 20260735, 20260736, 20260737])
    -> EARNED, D7_S_R4_ABSOLUTE_FOCAL_MARGIN
resolve_run_plan(...that list...)   -> returned verbatim, 5 entries, NOT deduped
pooler union / disjointness / union_seeds  -> all set()-based, blind to a repeat
pooled artifact       topology_seeds = 8      topology_records = 9
r4_freshness_sentinel -> ok=True, ALL FIVE conditions True
```

`draw_shared_topology_indices` then ran at `n_topo=9` and one topology carried
double weight in every topology-weighted estimate.

**The part that matters.** `r4_artifact_identity` — the inferred path D'
*replaced* — refuses that same list, measured: `None`/`None`. This is not a
pre-existing hole that D' failed to find. **D' created it.** The artifact did not
merely lack proof of its population; it carried a *passing* proof of a
population it did not have, which is the exact wrong-claim class the gate exists
to prevent.

## B-2 — the lowest-effort command line had no closure at all

```text
resolve_run_plan(no flags) -> TOPOLOGY_SEEDS_R4 at the registered 8/8 episodes
r4_artifact_identity(those) -> EARNED
'r4_freshness_sentinel' inside main(): ONE occurrence, and it is IN A COMMENT
  asserting the check runs
```

Contract §3 says "fail closed unless". Until D'' the sentinel had exactly one
production call site — the pooler — so the default no-flag invocation produced a
fully identified, self-labelled "R4 conclusion-bearing population" artifact with
a branch string and no gate anywhere. Separately, `--population r4` with the
eight seeds **reversed** earned identity and would have failed the sentinel
(`exact_seed_list=False`) had anything run it; topology order is load-bearing
because §8's bootstrap resamples topologies by position.

## One correction from the review that was NOT adopted

The review's minimal fix for B-1 re-points sentinel condition 1 at
`topology_records`. A topology failing the pinned-coordinate hash assert
contributes no record and no unit — `main()` appends to `topology_hash_failures`
and continues — so requiring the records to equal the whole population would
turn a **lawful `INVALID_EVENT_ALIGNED_AUDIT` (branch 1) run** into a refusal
instead of a reportable result.

Condition 1 stays on the declared list. A separate **condition 8** —
subset-and-distinct, never equal-to-the-population — closes the duplicate hole
without touching branch 1. Confirmed by paired negative: substituting the
review's `==` for `<=` reddens `test_condition_8_does_not_fail_a_lawful_hash_failure_run`
and nothing else.

Condition 8 is an **implementation binding beyond the contract's registered
seven**, owed to Pro as disclosure. Contract conditions 1–7 are not renumbered.

## What D'' changed

```text
B-1a  r4_declared_population_identity: third hard SystemExit on a repeated seed
B-1b  sentinel condition 8, no_duplicate_producing_topologies
B-2   main() calls r4_freshness_sentinel, gated on SET coverage of the
        population, refusing BEFORE the stdout JSON and BEFORE the --out write
N-2   window_series_length DELETED (dead; its docstring is what produced the
        wrong h+1 spec constant earlier in this workflow)
N-3   arm_distinctness_check docstring: no longer describes the deleted null arm
N-4   limb_states seeded before the branch split -- section 6's "must always
        remain in the payload" was false on the support-failure path
N-5   the pooler prints D7_S_EVENT_ALIGNED_BRANCH= only for the R4 population;
        a development pool gets an explicit NOT_CONCLUSION_BEARING line
N-1   NOT re-routed. The horizon criterion sits in the wrong predicate but is
        unreachable (`fork_continuation` has no early break). Pinned by a test
        that reddens if anyone adds one, rather than touching precedence.
```

## Set equality, not list equality — the binding that would have half-fixed B-2

`r4_declared_population_identity` is order-insensitive, so under `list(...) ==
list(...)` a reversed whole-population declared run would skip the new gate
entirely and escape with a branch computed under a non-canonical ordering. Set
coverage routes it *into* the sentinel, where `exact_seed_list` refuses it.
Refused rather than silently sorted: a conclusion-bearing run that names its own
population out of order is an operator mistake worth surfacing.

Confirmed by paired negative: reverting to `list` reddens exactly
`test_main_refuses_a_reversed_whole_population_declared_run`, one test, no
residue.

## Verification

Eight paired negatives, each perturbing production and each watched failing.
Two were re-run independently by the Project Manager rather than taken on
report — the `set`/`list` binding and the `<=`/`==` binding, the two the PM
authored against the review's own proposal. Both reddened exactly one test with
no residue.

Two positive halves exist so the new guards cannot be unconditional: a lawful
7-of-8 hash-failure artifact must still pass condition 8, and a single-seed
`--population r4` shard — the planned production route — must still write its
artifact.

## A dead branch, measured and left in place

`assemble_audit_result`'s middle `elif` is unreachable **even under direct
exercise**, not merely in the registered population as its comment claimed:
reaching it needs `len(topology_results) <= 1` *and* `support_ok`, and
`support_ok` comes from `check_minimum_support` over those same results, which
needs six. Measured: `support_ok` is False at n=0, 1, 2 and True at n=6.

The comment is corrected. The branch is left in place because the formal run is
gated and folding it into the `else` would change which branch an unreachable
input reports; deletion belongs in the next round.

## Disposition

R4 closure reopens at F/F'. The formal R4 measurement stays gated behind this
repair landing green. `D7.3`/`D8` remain blocked pending a valid fresh-population
R4 result.
