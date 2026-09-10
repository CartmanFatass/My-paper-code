# VSPC1 B04 P67 — E0 result evidence

**Valid complete B/EXPLORE: UP at master8202.** The normalized GATED-V−MLP-V
mean is +.02309832638998633, conditional SE .008740309282664975. Both learned
means exceed H in this pair. This is a second local normalized-regime observation;
it does not establish stable superiority or identify specialized hold-credit use.

## Binding and rule applied verbatim

The [B04 card](VSPC1_NATIVE_HOLD_VALUE_B04_SCIENCE_CARD_20260908.md) was frozen
at `0a60f57514709a0eb390253576dc8df8f7d47c21`. Its scientific fields were not
changed after output. The [P67 selection](VSPC1_NATIVE_HOLD_VALUE_B04_P67_RESUME_20260908.md)
at `9e9f705deef548cd4384825bba44eac9d58b9ea1` supplied one new submission
after P66's pre-script failure; the old allowance was not reused.
Launch source is `ec8b7c458b038b3a375ec5639834d0f3527fdf8c`, preserving
the accepted numerical surface `a33a3820fe9d4a46a3231bcf267afc956554b6c5`.

The card §4 primary row applies verbatim:

> Delta>.01 with trustworthy primary
>
> UP: one additional local normalized-regime signal for the complete gated package; retain both normalized pairs, H contrasts and every adverse episode before recommending a next discriminator.

The card's H and uncertainty qualifications also remain verbatim:

> One/both learners below H
>
> Retain trustworthy Delta but narrow usable-control wording; do not hide H loss or declare the comparator repaired.

> Conditional SE leaves an MEI boundary unclear
>
> Report the point-estimate region and conditional noise separately; no training-population conclusion or automatic extra episodes.

Here Delta>.01 and the full primary is trustworthy. Neither learner's mean is
below H in8202; B03's negative MLP−H remains separate contrary evidence against
unqualified comparator competence. UP is the point-estimate region. The SE is
conditional on these trained policies and does not certify the side of an MEI
boundary or measure training-population uncertainty. No extra evaluation follows.

The incomplete-primary branch is not triggered: both learners and H completed
their assigned final evaluations and publication readback. P66 continues to obey
that missing-primary branch in its separate, unchanged failure intake.

## Direct result and independent unit

Native J is the sum of256 native rewards divided by256; it is not the normalized
critic target. Every endpoint comes from the final sampled policy on the frozen
reset panel, without selecting a better checkpoint or metric.

| Endpoint | Mean J | Evaluation episodes |
| --- | ---: | ---: |
| GATED-V | .19726280882081323 | 32 |
| MLP-V | .17416448243082688 | 32 |
| Fixed zero-velocity H | .14136717177746932 | 32 |

| Matched contrast | Mean | Conditional SE | Adverse episodes |
| --- | ---: | ---: | ---: |
| GATED−MLP | +.02309832638998633 | .008740309282664975 | 9/32 |
| GATED−H | +.055895637043343896 | .01402017897123588 | 7/32 |
| MLP−H | +.03279731065335756 | .012954036294274218 | 10/32 |

All32 identities820202000..820202031, endpoints, native reward decompositions
and differences are retained in the [CM machine evidence](VSPC1_NATIVE_HOLD_VALUE_B04_P67_COLLECTION_EVIDENCE_20260908.json).
The [DM analysis](VSPC1_NATIVE_HOLD_VALUE_B04_P67_ANALYSIS_20260908.json) preserves
all adverse identities and descriptive calculations. The independent unit is
one matched training pair; episode differences supply conditional sample-SD/sqrt32
SE, not32 independent training runs.

| Normalized pair | GATED−MLP (conditional SE) | GATED−H | MLP−H |
| --- | ---: | ---: | ---: |
| B03/8201 | +.03980171530455754 (.006008657101475142) | +.03521279747565949 | −.004588917828898052 |
| B04/8202 | +.02309832638998633 (.008740309282664975) | +.055895637043343896 | +.03279731065335756 |

The existing `summarize_runs.py --paired --baseline MLP-V` was run on four
endpoint-mean rows, one per learned arm per independent training pair. Its n=2
GATED−MLP descriptive mean is .03145002084727194, sample SD .011811079570289488.
H is not an additional trained arm in that CSV. Pair dispersion includes training
and evaluation randomness; no population interval is assigned. The difference
between subtracting endpoint means and averaging matched differences is confined
to final floating-point digits and changes no reading. Raw card-primary values
are retained above. Unnormalized8101/8102 remain a separate n=2 regime, never pooled.

## Counts, exposure and moment state

The actual counts match the frozen schedule: two fresh learner fits,512 complete
training episodes per arm,256 two-episode rollouts per arm and four optimizer
epochs per rollout. Total:262144 training and24576 evaluation team steps,
**286720 native steps,2048 Adam calls,512 rollouts,96 final evaluations**,
1120 scored episodes, two constructor resets and zero partial steps.
The recorded1024 training episodes are not1024 independent training seeds.

There are1384561 velocity decisions,5440 duration decisions,2693 duration4
choices and1392640 recurrent observations. No diagnostic frame or native smoke
was added. Both arms' moments receive131072 scalar native targets in256 merges;
evaluation and H do not update them. Across arms this is512 merges/262144 rows
and1048576 four-epoch value-target terms.

| Arm | Moment n / updates | Mean | M2 | Scale |
| --- | ---: | ---: | ---: | ---: |
| GATED-V | 131072 / 256 | 19.78407096862793 | 30108494 | 15.156172752380371 |
| MLP-V | 131072 / 256 | 20.633365631103516 | 29706446 | 15.054640769958496 |

CM checked512-row increments, normalized-squared loss labels, final FP32
checkpoint identities/finiteness and matching frozen moments through learned
evaluation/H/publication. Raw full RTG arrays were not replayed. The unchanged
accepted arithmetic source, original focused checks and observed state transitions
support the dependent boundary without another scientific invocation.

Machine exposure: total relative parameter displacement GATED
.2534176631653249 /MLP .23690194561741526. Gate absolute movement is
.5487287640571594; duration absolute movement is .1657041609287262 /
.11938440799713135. Gate/duration start at zero, so relative displacement is
undefined. Raw epsilon-based duration ratios remain preserved, with an explicit
null interpretation in collection and DM analysis; they are not usable ratios.
Nonzero hold-input rows are1497/131072 (1.1421%) and1488/131072 (1.1353%) in
training,90/8192 in each learned evaluation. Exposure and gate motion are not
evidence of causal attribution.

## Receipts, resources and engineering conformance

Same CM staged, launched once, solely observed and collected handle
`vspc1_hold_value_b04_p67_8202` on `hmasd-wsl-node`, CPU FP32/one numerical thread.
Exact cwd: `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b04-p67-8202`.
Exact script: `/home/wu/hmasd-inputs/vspc1_hold_value_b04_p67_8202.sh`.
Output: `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b04_p67_8202`;
admission is the adjacent `_admission.json`. Full source, thirteen required files
including UCOPE environment/package dependencies and the LF script were checked
before submission. The [staging](VSPC1_NATIVE_HOLD_VALUE_B04_P67_STAGING_EVIDENCE_20260908.json)
and [submission receipt](VSPC1_NATIVE_HOLD_VALUE_B04_P67_SUBMISSION_20260908.json)
preserve the exact accepted argv; no path was reconstructed at submission.

Admission at2026-09-09T02:40:39.232806Z measured both physical/effective available
memory15,639,040,000 bytes, passing4GiB before scientific state. Supervisor start
was02:40:39Z, terminal02:45:51Z, exit0 with inactive tmux. Its integer duration312s
is distinct from the enclosing fractional `/usr/bin/time` wall **312.77s**.
Peak RSS is555844KiB =569184256 bytes =542.81640625MiB.

Internal wall305.7251625119825s, MLP transition159.03897231799783s, residual
7.044837488017492s. Charging the entire nonnegative residual to each arm gives
conservative upper bounds166.08380980601532s GATED /153.73102768200215s MLP,
both below1800s; complete enclosing312.77s is below3600s. These are conservative
bounds, not exact phase-time splits. Serial study critical path and summed
invocation wall are312.77s. `resources_unmeasured`: aggregate CPU and the
normalization-specific runtime increment; measured wall/RSS remain valid.

P67's known staging check4.5818782s and artifact-only collection5.5786043s sum
10.1604825s, reported separately from native wall. No unchanged test or native
fixture was repeated. Its eight-line wrapper plus original35-line B04 runner
add43 non-test lines across this B04 binding/correction; scope §4:none, no §5
budget breach. Existing seven binding tests cost5.3719231s and were reused.

The scoped successful-normalized-pair window is310.79+312.77=623.56s for two
valid pairs,311.78s/valid pair. This excludes separately reported technical work
and historical failed submissions/preparation; full-history cost remains
unaggregated, not zero. P66's failed supervisor submission added no scientific
pair; its absence of native cost is not a measured zero CPU charge.

CM collection commit `4c6572dae1299a724b5b5c9f59c2442993d7acdb` preserves
summary/episodes/rollouts/checkpoints/admission remote-to-local hash agreement,
full log/wrapper and all collection checks. The [scientific intake](VSPC1_NATIVE_HOLD_VALUE_B04_P67_INTAKE_20260908.md)
records the decisions and qualifications. The one P67 allocation is complete;
no second submission or successor was executed.
