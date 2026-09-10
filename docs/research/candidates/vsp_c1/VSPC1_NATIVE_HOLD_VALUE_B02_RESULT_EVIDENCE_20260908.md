# VSPC1 native hold-value B02 — E0 result evidence

**Valid complete B/EXPLORE observation: UP at master8102.** GATED-V−MLP-V is
+.11572713049362449 in final sampled time-average native team reward, above the
unchanged absolute .01 MEI. The second independent pair repeats the local package
gain; it does not establish stable superiority or unique hold-credit causality.

## Identity, selected measurement and rule applied verbatim

Object `VSPC1-NATIVE-HOLD-VALUE-B02`, master8102, source
`0ec208899f5e8b4c190ab7bd9806be2cc30b6fda`;
[card §§2–7](VSPC1_NATIVE_HOLD_VALUE_B02_SCIENCE_CARD_20260908.md).
P55 supplies this one-pair allocation. The key, derived streams, final checkpoint,
comparison, MEI and UP(.55) prediction were frozen before this instance's output.
B02 is an outcome-informed B follow-on after B01, not a confirmatory redesign of it.

The applicable unchanged card row is:

> Delta>.01 with trustworthy primary
>
> UP: one local native signal for the complete gated package; consider, but do not automatically allocate, one or two independent paired fits. Preserve H comparisons and every adverse episode.

The applicable reference qualification is:

> One/both learners below H
>
> Retain trustworthy Delta, but narrow usable-control wording. Even an UP does not automatically justify another pair; do not rescue it by ignoring H.

The allocation stop also applies verbatim:

> **P55 ends after this one pair and intake regardless of sign**.

Both fits and all three32-episode final endpoints are complete. J remains the
complete256-step native team reward sum divided by256. Native return-to-go targets
remain unaveraged; no greedy, intermediate, best-checkpoint or subset endpoint is used.

## Direct B02 observations

| Endpoint | Mean J | Final evaluation episodes |
| --- | ---: | ---: |
| GATED-V | .1889430171129279 | 32 |
| MLP-V | .07321588661930342 | 32 |
| Fixed zero-velocity H | .16244093193733047 | 32 |

| Matched contrast | Mean | Conditional evaluation SE | Adverse episode differences |
| --- | ---: | ---: | ---: |
| GATED-V−MLP-V | +.11572713049362449 | .009472055753507819 | 1/32 |
| GATED-V−H | +.026502085175597434 | .009388482227809858 | 11/32 |
| MLP-V−H | −.08922504531802705 | .010765618591322513 | 29/32 |

The independent unit is **one new matched training pair**, not96 evaluations,
five agents or2048 optimizer calls. The SEs describe evaluation noise conditional
on these trained policies; they do not estimate training-population uncertainty.
All adverse identities remain in the raw rows and [DM analysis](VSPC1_NATIVE_HOLD_VALUE_B02_ANALYSIS_20260908.json).
The primary episode range is−.0029350003 to+.2260103355. GATED−H ranges
−.0683815788 to+.1367042016; MLP−H ranges−.2045261944 to+.0818084648.

Using H as a common anchor gives the arithmetic identity
.1157271305=.0265020852+.0892250453. The H−MLP term is77.10% of B02's primary
gap. This is a decomposition of recorded means, not attribution of learning failure
or gate benefit. GATED's positive H-relative point estimate remains reportable;
its eleven adverse H comparisons also remain visible.

## Both independent pairs, without outcome selection

| Pair | GATED mean J | MLP mean J | H mean J | GATED−MLP | GATED−H | MLP−H |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B01/master8101 | .1648860823 | .1355204237 | .1454855329 | +.0293656586 | +.0194005494 | −.0099651092 |
| B02/master8102 | .1889430171 | .0732158866 | .1624409319 | +.1157271305 | +.0265020852 | −.0892250453 |

B01's full conditional SEs and adverse episodes remain in its immutable
[E0 record](VSPC1_NATIVE_HOLD_VALUE_B01_RESULT_EVIDENCE_20260908.md).
Both individual point estimates are UP. A descriptive run-level summary over the
two matched pairs gives mean Delta+.07254639452699532 and sample SD
.06106678243725866. It applies no new success rule to that mean and provides no
stable population claim or confidence interval. The four learned endpoint rows
were analyzed with the existing scientific-tools `summarize_runs.py --paired
--baseline MLP-V`; H and episode rows were excluded from the independent-run CSV.

The comparison is unchanged apart from fresh master and publication binding.
The larger B02 difference coincides mainly with a lower MLP endpoint relative to
H: across pairs GATED−H rises .0071015358, whereas MLP−H falls .0792599362.
This does not identify why the training trajectories differ. No pair, failed
episode or prior adverse UCOPE result is discarded or pooled into a new best result.

## Learning, exposure and complete counts

Both arms retain the same duration-capable108-input recurrent actor,136 pre-decision
critic inputs and explicit compound PPO. The zero-initialized640-parameter gate
is the treatment. Native reward/information, separate per-arm mutable streams,
joint gradient clipping, final-only sampling and H reuse are unchanged.

| Quantity | B02 observed |
| --- | ---: |
| Logical invocation / independent training pair / learned fits | 1 /1 /2 |
| Training episodes / native team steps | 1024 /262144 |
| Final evaluation episodes / native team steps | 96 /24576 |
| All complete episodes / native team steps | 1120 /286720 |
| Rollouts / recorded epochs / actual Adam calls | 512 /2048 /2048 |
| Explicit resets / constructor resets | 1120 /2 |
| Partial steps / optional diagnostic frames | 0 /0 |

Each learner completes512 episodes and1024 Adam calls. Training velocity decisions
are651679/651655 and duration decisions2560 per learner. The inherited
`scientific_uav_calls=286720` counts environment step calls, not separate experiments
or formal validation entries. Across B01+B02 there are four fits,573440 native team
steps,4096 Adam calls and192 final evaluations, with n=2 independent training pairs.

Machine-generated exposure: GATED/MLP total relative displacement is
.5389322229365768/.46125991503565106; common actor ratios are
.26947635406058623/.3482289499256628. Gate absolute displacement is
2.601895809173584 from zero; its relative displacement is undefined/null.
Duration absolute displacements are .17618238925933838/.19975757598876953;
raw inherited epsilon-ratio fields are preserved, not interpreted as defined ratios.
Natural nonzero-r training rows are1473/131072 and1482/131072
(about1.124%/1.131%); final sampled d4 fractions are .4875/.45625.
Counts and movement are exposure facts, not a causal explanation of native return.

## Receipts, budgets and limitations

The [CM collection](VSPC1_NATIVE_HOLD_VALUE_B02_COLLECTION_20260908.md) and
[unchanged summary/receipts/checks](VSPC1_NATIVE_HOLD_VALUE_B02_COLLECTION_EVIDENCE_20260908.json)
are committed at `bc45c2f48c4072c2565ae5d93c34da2ffe829d25`.
Handle `vspc1_hold_value_b02_8102_0ec208899f5e` finished exit0, PID2784739,
tmux inactive, at2026-09-08T20:26:05Z; the supervisor log uses UTC+08.
It executed the exact accepted source and reviewed655-byte script on
`hmasd-wsl-node`, from the detached cwd and output bound in card §7.
All1120 episode rows,512 rollouts,2048 epoch/Adam records, finite FP32 checkpoints,
identities and32 matched final reset pairs per contrast reconcile. Limits are empty;
publication is complete. No collection rerun or additional scientific exposure occurred.

Fresh admission at2026-09-08T20:21:01.013301Z reports physical and effective
available memory15642329088 bytes, each above4294967296. Enclosing peak RSS is
555072KiB=542.0625MiB. Aggregate CPU, device utilization and a runtime thread census
remain unmeasured; CPU FP32/one process/one numerical thread is the configuration.
Raw `resources_unmeasured` and the internal exit-boundary label remain unchanged.

Enclosing admission-plus-process wall304.52s bounds scientific process wall;
internal wall303.9593814199907s and MLP transition157.64559505297802s leave a
.5606185800093044s residual with unknown admission/startup/exit split. Complete
conservative arm upper bounds158.20621363298733s/146.87440494702196s are each
below1800s, and the enclosing total is below3600s. Do not add these conservative
arm bounds as measured total work. Complete caps conform. Across the two valid
pairs, the sum of enclosing walls is613.15s, or306.575s per valid pair; this is
neither study critical-path time nor aggregate CPU work.

Engineering acceptance remains separate:42 added/6 removed production lines,
35-line runner and six focused cases in2.07s (3.043s observed command wall),
with no new scientific fixture. The unsubmitted hard-KILL wrapper finding was
resolved before launch. Scope §4 additions:none; no §5 breach or runtime cap breach.
The [DM intake](VSPC1_NATIVE_HOLD_VALUE_B02_INTAKE_20260908.md) records the prediction,
bounded two-pair interpretation, allocation stop and unexecuted next-task advice.
