# VSPC1 normalized native hold-value B03 — E0 result evidence

**Valid complete B/EXPLORE observation: UP at master8201.** GATED-V−MLP-V is
+.03980171530455754 in final sampled time-average native team reward, above the
frozen absolute .01 MEI. GATED−H is +.03521279747565949; MLP−H remains negative
at −.004588917828898052. This is one local comparison under the new normalized
training regime. The two unnormalized pairs remain a separate regime.

## Identity, measurement and rule applied verbatim

Object `VSPC1-NATIVE-HOLD-VALUE-B03`, master8201, accepted scientific source
`7a8ed3aa5d25ded71164aa338749d09318124dcf`. [P60](../../portfolio/handoffs/2026-09-08-p60-vspc1-normalized-value-comparison.md)
allocates exactly this one pair. The [card §§1–7](VSPC1_NATIVE_HOLD_VALUE_B03_SCIENCE_CARD_20260908.md)
at `72cbee0a82c870bf5a514cfada8970c62652479d` fixed the normalization rule,
derived RNG domains, final-only sampled endpoint, MEI and WITHIN(.55) prediction
before this instance's output. This is outcome-informed B exploration after
B01/B02, with no historical reclassification or confirmatory claim.

The applicable card row is:

> Delta>.01 with trustworthy primary
>
> UP: one local normalized-regime signal for the complete gated package; preserve both H contrasts and every adverse episode before recommending a next discriminator.

Its H qualification is:

> One/both learners below H
>
> Retain trustworthy Delta but narrow usable-control wording; do not hide H loss or declare normalization a repair.

The uncertainty row states:

> Conditional SE leaves an MEI boundary unclear
>
> Report the point-estimate region and conditional noise separately; no training-population conclusion or automatic extra episodes.

The allocation stop remains:

> **P60 ends after this one pair and intake regardless of sign.** No second normalized pair, old-regime pair, tuning, ablation, extra H/evaluation, alternate seed or retry is allocated.

Both fits and all three32-episode endpoints are complete. `J=sum(native
rewards)/256` never uses target normalization. Gamma1 return-to-go remains
unaveraged inside the learner; no greedy, intermediate, best-checkpoint or subset
endpoint replaces the final sampled policies. Card WITHIN/DOWN/dependency rows
were considered; none changes the complete UP primary. The original shell
failure generated no primary and remains separately recorded below.

## Direct normalized-regime observations

| Endpoint | Mean native J | Final evaluation episodes |
| --- | ---: | ---: |
| GATED-V | .18306017943960662 | 32 |
| MLP-V | .14325846413504909 | 32 |
| Fixed zero-velocity H | .14784738196394714 | 32 |

| Matched contrast | Mean | Conditional evaluation SE | Adverse episode differences |
| --- | ---: | ---: | ---: |
| GATED-V−MLP-V | +.03980171530455754 | .006008657101475142 | 4/32 |
| GATED-V−H | +.03521279747565949 | .010408850908328956 | 9/32 |
| MLP-V−H | −.004588917828898052 | .012026063667580491 | 19/32 |

The independent unit is **one matched training pair**, not32 episode pairs,
96 evaluations, five agents or2048 Adam calls. SE is sample SD of32 matched
episode differences divided by sqrt32; it conditions on these trained policies.
There is no training-seed variance estimate. The existing scientific-tools
`summarize_runs.py --paired --baseline MLP-V` receives only two learned endpoint
rows, one per arm at8201. Its paired n=1 and sample SD=null are retained in the
[DM analysis](VSPC1_NATIVE_HOLD_VALUE_B03_ANALYSIS_20260908.json), alongside all32
matched identities, endpoints, differences and adverse rows. H is a fixed native
reference, not another independent training observation in that CSV.

The primary episode range is −.0254680633 to +.1081279286; GATED−H ranges
−.0557147388 to +.1887294177; MLP−H ranges −.1054442195 to +.1969550425.
No adverse outcome is excluded. The H anchor gives the arithmetic identity
.0398017153=.0352127975+.0045889178: H−MLP is11.53% of the primary difference.
This describes the means; it is not a decomposition of causal learning effects.
The small negative MLP−H mean, with conditional SE .0120261, establishes neither
equivalence to H nor dependable superiority over H. GATED's positive H-relative
mean also retains its nine adverse comparisons.

## Original regime retained separately

| Unnormalized pair | GATED−MLP | GATED−H | MLP−H |
| --- | ---: | ---: | ---: |
| B01/master8101 | +.0293656586 | +.0194005494 | −.0099651092 |
| B02/master8102 | +.1157271305 | +.0265020852 | −.0892250453 |

The [B02 E0](VSPC1_NATIVE_HOLD_VALUE_B02_RESULT_EVIDENCE_20260908.md) retains the
old regime's two-pair descriptive mean +.0725463945, sample SD .0610667824,
all conditional SEs, adverse episodes and B01 link. B03 is not a third identical
replication. Fresh training/evaluation randomness and normalization change
together across regimes; apparent changes in MLP/H or the primary gap cannot
identify normalization's causal effect. No cross-regime aggregate is selected.

## Learner, moments and exposure

Both arms keep the same108-input recurrent duration actor,136 pre-decision
critic inputs, full MLP, explicit compound PPO, native information/action/reward,
separate histories/generators and joint gradient clipping. GATED adds the existing
zero-initialized640-parameter gate. Five agents co-adapt at fixed membership;
the host offers only opening duration1/4 and natural remaining hold at t1–3.

Each arm accumulates its own FP32 population moments from512 complete native
return-to-go targets once per rollout. Stored native-value advantages precede
the merge; the normalized value targets and moments stay fixed for four epochs.
Native measurement stays outside that transformation. Final moments are:

| Arm | n | updates | mean | M2 | scale |
| --- | ---: | ---: | ---: | ---: | ---: |
| GATED-V | 131072 | 256 | 17.709501266479492 | 25492082 | 13.945937156677246 |
| MLP-V | 131072 | 256 | 17.751535415649414 | 24964986 | 13.801004409790039 |

The CM reconciles each rollout's512-row count increment, the final checkpoint
and summary, unchanged moments before/after learned evaluation and after H,
and normalized-squared loss labels for every recorded epoch. H uses no moments.
Full raw RTG arrays were not separately archived/replayed; accepted source and
focused arithmetic/gradient checks support the conversion and update semantics.
These state/count checks establish conformance, not why the gate improves return.

Machine-generated total parameter relative displacement is GATED
.2621670954795077 / MLP .25396332210330247; common-actor ratios are
.19655097272541258 / .2020520144491274. Gate absolute movement is
.6060495972633362 from zero, so its relative displacement is undefined/null.
Duration absolute movements are .11403322219848633 / .10539168864488602;
the raw legacy epsilon-denominator ratios are preserved but not interpreted as
defined relative movement. Moment updates are not learned parameter displacement.

Both arms expose1485 nonzero-r training rows out of131072 (about1.133%).
Learned evaluation has90/87 such rows; final sampled d4 fractions are
.49375/.475. Sparsity, duration fractions and gate movement do not establish
specialized hold-credit use or mediate the observed return difference.

## Complete counts, receipts and resource boundaries

| Quantity | B03 observed |
| --- | ---: |
| Scientific logical invocation / independent training pair / learned fits | 1 /1 /2 |
| Training episodes / native team steps | 1024 /262144 |
| Final evaluation episodes / native team steps | 96 /24576 |
| All complete episodes / native team steps | 1120 /286720 |
| Rollouts / epoch records / actual Adam calls | 512 /2048 /2048 |
| Explicit resets / constructor resets | 1120 /2 |
| Moment merges / scalar targets merged | 512 /262144 |
| Four-epoch value-target row terms | 1048576 |
| Partial steps / optional diagnostic frames | 0 /0 |

Each learner completes512 training episodes and1024 Adam calls. Training
velocity decisions are651466/651496; duration decisions2560 per learner.
`scientific_uav_calls=286720` counts environment step calls, not separate
experiments or formal UAV-validation entries.

[CM collection](VSPC1_NATIVE_HOLD_VALUE_B03_COLLECTION_20260908.md) and its
[unchanged evidence](VSPC1_NATIVE_HOLD_VALUE_B03_COLLECTION_EVIDENCE_20260908.json)
are committed at `df899599d4aa474ba252ce32740ec8e7eceddd79`, integrated by Root as
`c927c5f91`. The corrected handle
`vspc1_hold_value_b03_8201_7a8ed3aa5d25_cwd1` finished exit0 with inactive tmux;
the supervisor PID was3010237. Its terminal log spans
2026-09-08T22:53:22Z–22:58:33Z (the raw log uses UTC+08).
Actual detached cwd is
`/home/wu/hmasd-worktrees/vspc1-native-hold-value-b03-8201-7a8ed3aa5d25`;
result root is
`/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b03_8201_7a8ed3aa5d25`.
Remote/local hashes match for summary, episode/rollout rows, both final checkpoints
and admission. The summary digest is
`adef9869d75c1ee7ea8da1561d73a20dd3daacb604cfa18124e6b2855126d60d`;
the full manifest and raw supervisor/script receipts remain in CM evidence.

The original handle without `_cwd1` failed at missing-cwd `cd`, before admission
or scientific state. [Intake §§1–6](VSPC1_NATIVE_HOLD_VALUE_B03_INTAKE_20260908.md)
and [cwd evidence](VSPC1_NATIVE_HOLD_VALUE_B03_CWD_CORRECTION_EVIDENCE_20260908.json)
preserve exit1, displayed wrapper wall0.00s/RSS3200KiB and zero scientific
invocations, steps, updates and evaluations. The rounded wall is not zero work.
Its exact-source staging correction changed only the supervisor name to retain
metadata; the accepted source, script, master, output and scientific allocation
were unchanged. Neither the failure nor this collection launched a second pair.

Fresh actual-node admission at2026-09-08T22:53:22.837261Z reports physical and
effective available memory15634731008 bytes each, above4294967296. The configured
execution is `hmasd-wsl-node`/`wsl_4070`, CPU FP32, one process and one numerical
thread; a runtime thread census is unmeasured. Enclosing peak RSS562504KiB equals
549.3203125MiB. Aggregate CPU, machine-wide use and normalization-specific overhead
remain unmeasured. Raw `resources_unmeasured` and internal exit-boundary labels
are preserved; the external receipts independently supply the observed quantities.

Enclosing admission-plus-process wall is310.79s; internal publication/readback
wall310.41653345897794s and MLP transition160.96011829999043s leave an
unpartitioned .37346654102208277s residual. Charging that entire residual to
each arm gives conservative upper bounds161.3335848410125s GATED /
149.8298817000096s MLP. Each is below1800s, and enclosing total is below3600s.
Startup is charged to GATED and H/publication/readback/exit to MLP. These upper
bounds are not disjoint measured phases and must not be added as actual work.
One serial invocation makes study critical path, summed invocation wall and cost
per valid normalized pair310.79s for this scoped window. The old regime's613.15s
for two valid pairs is separate. Complete caps conform; limits are empty.

Engineering conformance remains separate:127 added/13 removed non-test source
lines,35-line runner,17 focused checks with6.5665891s total process wall including
the resolved collection-only name collision; independent review has no material
unresolved finding. Scope §4 additions:none; no §5 engineering or runtime-cap breach.
DM analysis used stored numbers only (0.395s command wall), with no model,
environment, checkpoint replay, extra evaluation or repeated technical suite.
The [scientific intake §§7–11](VSPC1_NATIVE_HOLD_VALUE_B03_INTAKE_20260908.md#7-completed-pair-what-i-checked)
records interpretation, forecast scoring, P60 exhaustion and unallocated advice.
