# D7.S R4 — the formal result is `PART_A_CONTRADICTION`, and one decision follows from it

The R4 measurement you converged has run on the fresh population. It completed
cleanly: every gate upstream of the result passed, and the **Part-A control** is
what stopped it. This is the result submission.

**The decision I need is §5.** Everything before it is evidence, offered as
claims to falsify against the source, not as premises.

Discarding this question's framing is a legitimate answer.

## Frozen inputs — not review surface

- The complete R4 contract and ledger `R4-003`. Not reopened.
- `MATERIALITY_MARGIN = 5.0`, `H_STABLE = 139`, `H_FLEX = 550`,
  `MIN_SUPPORT_TOPOLOGIES = 6`, `MIN_SUPPORT_EPISODES_PER_TOPOLOGY = 4`,
  `BOOTSTRAP_SEED`, `BOOTSTRAP_ITERS`. Unchanged since the freeze.
- `TOPOLOGY_SEEDS_R4 = 20260734..41`. R4 has no expansion path, so a wider
  population is a new contract, not a bigger draw.
- R3's artifact. It may never become R4's confirmatory result and is cited only
  as the reason R4 exists.
- The null arm, deleted in R5. Its deletion is what satisfies "calibration arm
  ordering".

## 1. Provenance of what follows

**Repository fact** unless marked. `[INFERENCE]` marks my own reading;
`[MEASURED]` marks a number produced by the run.

Run `30403322062`, tag `d7s-audit-3`, instrument at commit `a00612ad`, eight
shards of one topology each, pooled by `pool_d7_s_event_aligned_shards.py`.
Wall clock 2h08m; all eight shards succeeded.

## 2. The sentinel passed, so the rest is readable

`[MEASURED]` All six fail-closed conditions on the pooled artifact:

```text
exact_seed_list                            True
no_r3_overlap                              True
identifies_r4_contract_and_namespace       True
per_topology_block_identities              True
registered_episode_counts                  True
every_topology_accounted_for_exactly_once  True
```

Every shard independently carried `r4_population_namespace =
D7_S_R4_ABSOLUTE_FOCAL_MARGIN`, ran the registered 8 + 8 episode volume, and
recorded zero hash failures. Identity is earned by each contributing process,
not asserted once at pooling.

## 3. The result

`[MEASURED]`

```text
branch        PART_A_CONTRADICTION
branch_reason None
limb_states   {stable: AFFIRMATIVE_NONMATERIAL, flex: UNRESOLVED}

part_a.d_a_point           0.4839380477047651
part_a.lower_contrast_lcb  4.318957155049049     LCB95(D_A + 5) > 0
part_a.lower_contrast_ucb  6.685962861943237
part_a.upper_contrast_lcb  3.314037138056763     LCB95(5 - D_A) > 0

support.ok      True
conformance.ok  True   invalidated_pairs 0, hash ok, arms distinct

primary_g.degenerate                      False
primary_g.component_invariance_evaluated  True
primary_g.components_invariant_stable     False
primary_g.components_invariant_flex       False
```

`[INFERENCE]` **This is a positive equivalence finding, not a failure to
resolve.** Both one-sided bounds clear zero with room, so the bootstrap
established `|D_A| < 5` on both sides at 95%. The full-sync arm and the
constructive-mixed arm are equivalent *within the registered margin*.

Note also what did **not** happen: `primary_g` is not degenerate, the component
audit completed, and neither limb is exactly invariant. R3's failure mode did
not recur.

## 4. What was masked, recorded so the mask is auditable

`[MEASURED]` `(AFFIRMATIVE_NONMATERIAL, UNRESOLVED)`, which the nine-row map
sends to `NO_MATERIAL_STABLE_PERSISTENCE_IDENTIFIED`.

**That is not this run's result.** §7 puts `PART_A_CONTRADICTION` above the
combined result and it masks whatever the limbs said. I record the limb states
only because §6 requires them to survive the branch name — the exact information
R3 lost.

`[INFERENCE]` **The development topology predicted this and I did not read the
signal.** Step E, on topology `20260725` alone, measured `D_A ~ 0.46`. At the
time I treated it as an obstacle to the exercise and steered `D_A` to a
separated value so the nine combined results could be reached. The eight-topology
population now returns `0.484`. The dev topology was not an outlier; the
source-control contrast appears systematically near zero at this margin.

Per-topology `D_A` means straddle zero (`-1.91` to `+3.03`), while individual
within-topology contributions run `-7.9` to `+11.5`. `[INFERENCE]` the tight
pooled interval therefore comes from topology-level cancellation rather than
small within-topology variance — which is the claim in this section I would most
like falsified, since it bears on whether §5's answer is about power.

## 5. The decision

**5a. Does the contradiction invalidate the measurement, or is the masked focal
result readable as a diagnostic?**

The contract says the former. I am asking you to confirm it rather than letting
me assume it, because assuming it discards a completed conclusion-bearing
measurement, and because the asymmetry matters: a *mask* and an *invalidation*
imply different things about whether the eight topologies can be reused.

**5b. Is the equivalence itself a finding, or an instrument verdict?**

`PART_A_CONTRADICTION` is named as a contradiction because, if the source were
necessary, full sync should differ from constructive-mixed. It does not. That is
either (i) evidence about the mechanism — the source-control manipulation does
not move the system at this margin — or (ii) evidence that the control arm does
not do what the design assumed, i.e. an instrument verdict carrying no
mechanistic content. These license opposite next steps and I do not think the
choice is mine.

If (i): does the pre-registered equivalence carry publication weight on its own?

If (ii): is the defect in the control arm's construction, or in
`MATERIALITY_MARGIN = 5.0` being the wrong scale for `D_A` specifically? Note
the margin was rederived at an absolute anchor for the *focal* comparison; I do
not know that the same anchor is right for the Part-A contrast, and
`[INFERENCE]` I suspect that is the load-bearing question.

**No threshold moves on my side after this result.** I am not proposing a margin
change; if the anchor is wrong, that is a new contract, pre-registered before any
further run.

## 6. Implementation bindings, disclosed — none reopens a frozen decision

1. **The §4 length gate compares against the registered horizon `h` (139/550),
   not `h+1`.** The `h+1` convention belongs to the cutoff/depletion *latch*
   series, which carries a row-0 baseline the QoS and return-cost series do not.
   Implementing `h+1` would have failed every conforming record, making
   `PRIMARY_G_DEGENERATE` structurally unreachable while `complete` stayed True.
2. **R4 identity is DECLARED (`--population r4`), not inferred from the seed
   list.** A strict subset is admitted so the sharded route can carry identity;
   any seed outside the population is a hard refusal.
3. **The sentinel carries an eighth condition beyond the contract's registered
   seven** — producing topologies plus hash-failed topologies are exactly the
   population, each once. Binding 2 made a duplicated seed reachable *with*
   identity; measured, an artifact with 8 declared seeds and 9 bootstrap slots
   passed all five original conditions with one topology at double weight.
   Conditions 1-7 are not renumbered.

Also disclosed, not decided: `NOT_EVALUATED`, a fifth per-limb state outside the
frozen four-state vocabulary, carried only where no resolver ran.

## 7. Confidence — read this before the numbers

- **Verified by me against source**: the sentinel conditions, the identity
  routing, the branch precedence, and the per-shard provenance above.
- **Re-derived independently from the artifact**, after the run, by an
  implementation sharing no code with the audit module:

  ```text
  point estimate   0.4839380477047651   reproduces BIT FOR BIT (diff 0.0e+00)
  naive unit-pooled mean 0.550812       -- differs, so the topology weighting
                                           is genuinely applied, not assumed
  my hierarchical bootstrap, 3 seeds    LCB95 -0.638 / -0.673 / -0.645
                                        UCB95 +1.702 / +1.656 / +1.657
  reported (inverted from contrasts)    LCB95 -0.681   UCB95 +1.686
  ```

  Differences are Monte-Carlo noise at `BOOTSTRAP_ITERS = 10000`. The
  equivalence conclusion is robust: every re-derivation puts the interval a
  factor of ~3 inside the +/-5 margin. This paragraph previously said the
  bootstrap numerics were verified only by passing tests; that is no longer
  true and the correction is recorded rather than the claim edited away.
- **Not verified by anyone**: what a real episode emits. Every adversarial review
  of this instrument stubbed the environment, so the reviews speak to identity,
  routing, gating and assembly — not to `run_topology_audit`'s numerics. **This
  run is the first time the assembled path carried real R4 data.** Point your
  scepticism here first.

## Evidence to read

- `docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md`
- `docs/research/designs/D7_S_R4_DECISION_LEDGER.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260729_D7_S_R4_THE_CONTROL_SAYS_THE_ARMS_ARE_EQUIVALENT.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260728_D7_S_R4_THE_REPAIR_OPENED_A_HOLE_THE_OLD_CODE_REFUSED.md`
- `scripts/audit_d7_s_event_aligned.py`
- `scripts/pool_d7_s_event_aligned_shards.py`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`

## Required response sections

1. **5a** — invalidation or mask, and what that implies for reusing these eight
   topologies.
2. **5b** — (i) mechanism evidence or (ii) instrument verdict, with the reason.
3. If (ii): where the defect sits — control-arm construction, or the margin
   anchor being wrong for `D_A`.
4. Anything in §1-§4 you judge false, especially the topology-cancellation
   reading in §4.
5. What is next, if anything, and whether `D7.3`/`D8` remain blocked.
