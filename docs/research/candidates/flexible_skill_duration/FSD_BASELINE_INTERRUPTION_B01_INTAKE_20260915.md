# FSD baseline × interruption B01 — DM intake

DM: the Claude research hub; authoring `C:/Projects/HMASD-worktrees/codex-fsd` / `codex/fsd`.
All twelve original fits are complete and technically accepted, source `dc4dbdfcdb20ca29a47c1187e9ebf6787483d21b`.
Inputs: [full E0](FSD_BASELINE_INTERRUPTION_B01_RESULT_EVIDENCE_20260915.md),
[RESULT_SUMMARY.json](baseline_interruption_b01_20260915/RESULT_SUMMARY.json), the twelve
[fit folders](baseline_interruption_b01_20260915/fits/), the [card](FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md)
§§2–8, the Portfolio S decision and the FLAT `k = 10` correction
([decision](../../portfolio/decisions/2026-09-15-fsd-flat-k-correction.md)).

## What was checked and rule applied

Direct observation: twelve `summary.json` files with `status: complete`, one launch sha
`dc4dbdfcd`, arm and block identity as frozen (FLAT/D1280/I1280 × 772203/772303/772403/772503,
evaluation bases 782203–782503, lane seeds base + rank), counts per fit exactly the card §5
per-fit column (120,000 training transitions, 240 episodes, 15 update stages, 48,000
evaluation steps in three 32-world panels, 2 model constructions), optimizer calls consistent
with the arms (FLAT coordinator and both discriminators 0; actor/critic 33,750 in every arm),
every training row finite, per-element admission passed on the node immediately before the
fit, supervisor exit 0 for all twelve elements, every contrast `complete` after the runner's
comparable-view check. The reduce ran on the control checkout over the committed summaries.

Card rule (§4 as amended by §8) applied verbatim to the primary SI1280_15
= **+.00983744 J**: importance `small_signed` (inclusive ±.05); uncertainty
`interval_includes_zero` (df = 3 interval [−.11564245, +.13531733]); `interval_inside_mei`
false. Block values +.098, +.045, −.083, −.020 J. GAP_D_15 (D1280 − FLAT) mean
**−.04526346 J** [−.13491570, +.04438879]; GAP_I_15 (I1280 − FLAT) mean **−.03542601 J**
[−.18359432, +.11274230]; both untuned package gaps, both intervals include zero, neither
is §11.7 headroom. Rollout-5 accumulation: new four blocks +.04976314 J [−.05531799,
+.15484427]; historical two +.02910478 J; six blocks **+.04287702 J** [−.02320115,
+.10895519], descriptive and outcome-informed by declaration.

## Scientific reading and limits

Inference (narrowed by `em:flexible_skill_duration:convergence`, 20:27Z; see the
[decision intake](pro_packets/20260915_post_baseline_interruption_convergence/INTAKE.md)).
(1) **The renewal simple effect observed at rollouts 5 and 10 is not maintained at fifteen
rollouts on the mean** (a description of the observed means, not a decay law; no cross-panel
interval was computed). At rollouts 5 and 10 the four-block SI1280 means are +.050 and +.052 J; at rollout 15
the mean is +.010 J with two blocks positive and two negative. The per-block curves differ in
direction (772203 rises .055 → .076 → .098; 772303 falls .141 → .105 → .045; 772403 and 772503
change sign between panels), so the endpoint contrast at any single rollout is a snapshot of
a non-converged trajectory. The accepted "limited optional I1280 scheme under five-rollout
conditions" keeps its scope: the six-block rollout-5 accumulation (+.043 J, interval touching
zero from below) is consistent with that bounded description and adds no stable superiority.
(2) **On the observed point estimates, the untuned private-actor flat reduction is not below
the skill package at equal exposure on this host** (intervals include zero: no non-inferiority,
equivalence or stable FLAT advantage is shown, and the private FLAT score gives no monotone
guarantee for an untested central-input flat). Four-block arm means at rollout 15: FLAT .4510, D1280 .4058,
I1280 .4156 J; GAP_D_15 is near zero in two blocks (+.004, +.000) and about −.08 to −.11 J in
the other two. This is the direction's first same-host flat comparison. It is a package gap,
not headroom: FLAT is untuned and carries different information (private recurrent actor,
central-state critic, no coordinator). The card's "negative gap with an interval excluding 0"
branch is not reached; the point estimate is nevertheless adverse for the claim that the D2-D0
package adds over a flat reduction at this budget, and every package claim the direction has
made at this budget is bounded by it. (3) **Large within-trajectory movement is observed, not decomposed.** Panel-to-panel
swings inside one fit reach .1–.2 J (FLAT 772503 .312 → .530 between rollouts 10 and 15;
D1280 772503 .439 → .507 → .452), far above the conditional panel SE (.008–.021 J); these are
readings of different policies of one training process at different update positions and
show that the checkpoints share no stable ordering. The hub's original inference that block
dispersion is "not attributable to training seeds alone" is withdrawn: where each training
instance stands at the common endpoint is part of complete training-instance variation, the
block SD cannot be split into a seed part and a trajectory-phase part from single-panel SEs,
and more independent blocks can still improve the precision of the fixed fifteen-rollout
contrast (correction by the node).

Boundaries: direct observation (counts, values, readings) versus inference (the three points
above); scientific result (small signed primary, adverse-pointing gaps, unresolved
uncertainty) versus engineering conformance (accepted, one launch-quoting defect without
polarity); direction-local advice (below) versus Portfolio action (none; the S allocation ends
here and the card forbids automatic extension); historical provenance (the completed
factorial's two blocks and the five U-scope pairs stand unchanged, no rescoring) versus
current authority (this intake). No equivalence, no tuned headroom, no default change, no
component attribution, no transfer claim follows. Coverage of the df = 3 working model is not
established; four blocks cannot resolve a .03–.05 J effect at the observed SD (card §7 said so
prospectively).

Costs: summed native wall 45,401.07 s for twelve fits (plan 24,000–30,000 s assumed serial
execution; the node ran three to four fits plus the ACVC block-2 fits concurrently); per
valid result about 3,783 s per fit; peak RSS 1.2 / 2.8 / 3.8 GiB by arm. Plans were not caps;
no stop, retry or replacement.

## Predictions scored

Card (hub, on record): GAP_D_15 (then `H_15`) mean in [−.05, +.05] P .55 — **observed −.045,
inside the band, modal branch correct (near its edge)**; SI1280_15 mean in [−.05, +.05] P .60
— **observed +.010, modal branch correct**. Owner slot `not taken (unattended)`; canonical
reviews checked at this boundary, none unapplied.

## Decisions this intake produces

1. **Technical/object acceptance** — options: accept the complete twelve-fit object /
   quarantine a defect / rerun. Recommend and select acceptance; every required count,
   receipt, endpoint and digest is present; the launch-quoting defect produced no duplicate
   or missing original. Owner-delegated decision (unattended, 2026-09-03 instruction): accept;
   preserve every original (committed under `fits/`; the runner writes no checkpoint, so the
   committed set is complete; the Git-ignored supervisor logs are preserved as `task_records/*.txt`).
2. **Scientific conclusion** — options: (a) report the card-fixed readings as above (small
   signed primary, both gaps adverse-pointing with intervals including zero, rollout-5
   accumulation descriptive); (b) read the rollout-5/10 means as the "real" renewal effect and
   the rollout-15 value as noise; (c) read GAP_D as a headroom record. Recommend and select
   (a); (b) selects among panels the card forbids selecting among; (c) contradicts the
   Portfolio label. Owner-delegated decision (unattended): (a).
3. **Continuation** — the S allocation ends with this intake; no further fit, block, arm or
   panel is authorized (card §4, §8). The next choice is direction-tier for
   `em:flexible_skill_duration:convergence`, prepared here and not yet sent (the 09:00 PDT
   check-in scoped this session to collection, intake and report): (A) conclude the
   renewal-versus-flat family at this bounded claim, keep authentic D0 default and the
   five-rollout optional I1280 scope, FSD ACTIVE-idle; (B) select a tuned same-information
   flat baseline as the next object (the direction's first §11.7 headroom record, since the
   untuned FLAT already matches the package), before any further renewal work; (C) another
   tranche of blocks of the unchanged object (a Portfolio investment question under the
   card's no-automatic-extension rule). DM recommendation was (B) over (A). **Answered
   20:27Z: A, `PRO_FINAL`, label `CLOSE_OBJECT`** ([intake](pro_packets/20260915_post_baseline_interruption_convergence/INTAKE.md)):
   the stage closes at the bounded claim; B rejected (a one-fit-per-setting FLAT sweep cannot
   deliver §11.7 headroom and is not the next step); C and D legitimate but not bought now;
   the DM's "more blocks would not help" reason was not accepted. FSD ACTIVE-idle for this
   question with the node's reopening facts in the handoff.
4. **Direction/Portfolio** — no local disposition; no capacity writer held; no peer change;
   FSD stays ACTIVE/HIGH in its slot.

Ledger row in `docs/research/portfolio/audit/2026-09-15.md`; owner item `20260915-fsd-001`
(the S decision) traced to this intake as applied.
[Chinese owner brief](../../portfolio/owner/briefs/flexible_skill_duration/2026-09-15_FSD_BASELINE_INTERRUPTION_B01.md).

## Preservation, boundary and revisit

The twelve originals are committed under
[baseline_interruption_b01_20260915/fits/](baseline_interruption_b01_20260915/fits/) with the
queue records, the reduce output as `RESULT_SUMMARY.json` and the execution record. The twelve supervisor
logs and runner scripts are preserved as tracked text under `task_records/`; the remote
worktree `/home/wu/hmasd-worktrees/fsd-baseline-b01-dc4dbdfcd` and task records were
reclaimed after blob-level verification (`CLEANUP.json`). No
experiment, Pro response or transport effect is pending for FSD. Revisit condition: the
Convergence answer to the question in decision 3 once sent, or an owner instruction.
