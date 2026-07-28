# R4's planned production route cannot prove it is R4

Step D of R4 closure — the ten-check realization-conformance review of the
contract's §11, against commits `3de74552` (result layer) and `7fa90070`
(population/Part-A).

```text
verdict        conformance=REJECT   semantics=MODIFY
checks passed  1,2(caveat),3,4,5,7,8,10   -- 6 of 10 clean
checks failed  1(as realized), 6, 9
blocking       B1 B2 B3 B4
reviewer       hmasd-reviewer, read-only, no edit tool
```

Every blocking finding below was **re-verified by the Project Manager** before
being recorded here. A child's report is bound to be honest; that protects the
report, not the archive.

## B1 — the shard route earns no R4 identity, and nothing refuses it

`r4_artifact_identity` grants the R4 contract/namespace fields only when *one
process's whole seed list* equals `TOPOLOGY_SEEDS_R4`. The formal run is planned
one shard per topology.

```text
PM-verified:
  r4_artifact_identity(TOPOLOGY_SEEDS_R4)   -> contract + namespace
  r4_artifact_identity([20260734])          -> {None, None}
  r4_artifact_identity(first four seeds)    -> {None, None}
  r4_artifact_identity(reversed full list)  -> {None, None}
  grep r4_freshness_sentinel scripts/       -> DEFINITION ONLY, no call site
```

So every shard runs under `run_contract_id='D7_S_EVENT_ALIGNED_SOURCE_AUDIT'` —
the R3 namespace — and the pooled artifact is self-labelled "NOT R4
conclusion-bearing" while still emitting `D7_S_EVENT_ALIGNED_BRANCH=…` on stdout.
Contract §3 says "fail closed unless". There is no executable closure: the
sentinel that would enforce it is called by no production code at all.

**Severity, stated honestly.** This is a provenance failure, not a live stream
collision. R3 ran `20260726–20260733` only, so the legacy namespace at
`20260734–41` is in fact disjoint from every R3 draw. The randomness would be
fresh. The artifact's *proof* that it is R4 would not exist — and a result whose
population cannot be demonstrated from its own artifact is not publishable
regardless of whether it happens to be correct.

## B2 — a conclusion-bearing R4 artifact at 2 episodes instead of 8

```text
PM-verified, resolve_run_plan's formal (no-flag) branch:
  n_calibration = episodes_calibration if episodes_calibration is not None
                  else default_calibration
```

`--episodes-calibration 2 --episodes-audit 2` yields `n_cal=2, n_aud=2` **with
full R4 identity**. `N_CALIBRATION_EPISODES`/`N_AUDIT_EPISODES` are referenced
only as defaults; nothing validates against them. Sentinel condition 4 is
presence-not-count by design, so a 2-episode artifact passes all four conditions.
The count is recoverable post hoc from `calibration_report.episodes_attempted` —
so it is detectable, but nothing refuses it and no condition reads it.

## B3 — the completeness gate fails open, toward `PRIMARY_G_DEGENERATE`

`compute_focal_component_invariance` implements completeness as `if not
pairwise` — list non-empty. Contract §4 defines it as every qualifying event and
legal candidate represented, both CRN members present, all four sequences at the
registered horizon, no invalidated pair, and serialized/in-memory pair counts
agreeing.

Measured consequence: dropping the pairs of the one candidate whose sequences
differed leaves `complete=True` and flips both limbs to invariant. Two records
with empty component series compare exactly-equal even when their `total_g`
differ (1.0 vs 999.0); two 1-step records compare equal at a registered horizon
of 139.

The direction is what makes this blocking. A silently-truncated audit reads as
*exactly invariant*, which routes to `PRIMARY_G_DEGENERATE` — the same conclusion
that already closed R3's measurement route. §4's own words: a missing pair is
neither equal nor unequal.

## B4 — §7 first-match precedence is inverted

```text
PM-verified, decide_branch:1840-1845
  conformance -> support -> component_invariance_evaluated -> degenerate
contract §7
  invalid(1)  -> support(2) -> degenerate(3) -> Part-A -> combined
```

Support-fail *plus* missing component audit therefore reports
`SOURCE_EVENT_SUPPORT_INSUFFICIENT`, with `primary_g`, `limb_states` and
`u_star_bootstrap` all absent — an artifact carrying no record that the mandatory
audit never ran. Both labels are non-conclusion-bearing, so this cannot produce a
false positive; what it does is misattribute an **instrument** failure to the
**population**, and §9's disposition for support-insufficient (no substitution,
no expansion) is a scientific reading of the population.

Neither frozen reason code — `MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING`,
`FOCAL_KEEP_SET_COMPONENTS_EXACTLY_INVARIANT` — appears anywhere in `scripts/`.
They survive only in a stale `.pyc`.

## What the green suite was proving, and what it was not

249 tests passed while all four defects were live. The reason is structural, not
incidental:

- **`main()` is invoked by no test in either file.** Every sentinel test
  hand-builds its artifact via `_valid_r4_artifact()`. So no test asserts the
  invariant that actually matters — *an artifact emitted by the route the formal
  run uses satisfies the sentinel*. B1 is exactly that invariant, and it was
  invisible.
- **`compute_u_star_bootstrap` is never called for real.** Its only appearance in
  the suite is the `monkeypatch.setattr` that replaces it. Swapping
  `u_star_flex_lcb: u_flex["hi"]` inverts the flex `MATERIAL` gate and every
  listed test stays green.
- **The only incompleteness fixture is an entirely absent `component_audit`** —
  never a partial one, which is the case B3 turns on.

This is the "satisfied by the fixture" antipattern at suite scale: the tests
verify the hand-built shape, and the production path that builds the real shape
is untested.

## Non-blocking, recorded

- `NOT_EVALUATED` reaches the payload's `limb_states` but can never reach a
  published combined result — `decide_branch` returns branch 1 first, and
  `COMBINED_RESULT_MAP` has no such key, so it would raise `KeyError` rather than
  map it. Contained, but it extends the frozen four-state vocabulary in the
  payload. **Owed to Pro** at the next touchpoint as an implementation binding.
- `--allow-any-seeds` leaves no trace in the artifact. Record it in
  `pooling_provenance`.
- `null_update` and its two dispatch branches survive with no caller. §8 says
  deleted, not retained.
- `assemble_audit_result:4438-4441` re-implements `decide_branch`'s first two rows
  as literals. Agrees today; will not after B4 is fixed.
- `REMOTE_COMPUTE_HANDOFF.md` still describes an expansion set R4 does not have,
  and prescribes the exact shard recipe that produces B1's non-R4 artifacts.

## Disposition

All four are **conformance repairs against an already-frozen contract** — the
code failing to do what the contract says, not a new scientific decision. Project
Manager authority; no Pro round. Repair spec frozen and dispatched.

The R4 formal run stays gated behind these repairs, a re-review, and step E.
