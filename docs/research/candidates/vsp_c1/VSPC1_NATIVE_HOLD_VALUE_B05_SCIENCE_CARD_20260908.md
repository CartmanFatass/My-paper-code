Claim under test: the normalized gated critic retains a native-return advantage over a same-information ordinary MLP with approximately matched critic capacity in one fresh training pair.
Binding MARL structure: (b) temporal abstraction or termination, with five co-adapting agents retaining separate partial-observation histories.

# VSPC1-NATIVE-HOLD-VALUE-B05 — B/EXPLORE

Current state: P70 valid complete UP for master8301; §11 records the terminal
result. P68 preparation and P69 source-only history remain in §§1,7–9.

## 1. Question, authority and evidence boundary

Does the local gated-package signal survive a similarly sized ordinary critic,
under the existing normalized native learner and budget? Root's P68 assignment
at 2026-09-09T03:30:40Z authorizes this complete card/source contract and its
object-tier selection, followed by an allocation return. **P68 allocates no
implementation, CM dispatch, scientific invocation or additional executed seed.**
The prospective single pair below defines proposed work for that later allocation.
The [preparation intake](VSPC1_NATIVE_HOLD_VALUE_B05_INTAKE_20260908.md) records
the exact scope and tier. Item009 remains advice without owner ratification.

The [P67 intake §4](VSPC1_NATIVE_HOLD_VALUE_B04_P67_INTAKE_20260908.md#4-scientific-interpretation-and-next-discriminator)
and accepted DIRECTION science supply the question. Normalized masters 8201/8202
gave GATED−MLP +.0398017153/+.0230983264, GATED−H +.0352127975/+.0558956370,
and MLP−H −.0045889178/+.0327973107. Their adverse episode counts were 4/9/19
and 9/7/10 of 32 for those three contrasts. The n=2 descriptive primary mean
.0314500208 is not stable superiority. Preserve the old unnormalized 8101/8102
regime separately, including MLP−H −.0099651092/−.0892250453, and preserve P66's
pre-script failure with zero scientific exposure.

The current full MLP already shares nonlinear features and the gate adds 640
parameters. Reuse the verified local-library/primary-source distinctions in
[B03 intake §9](VSPC1_NATIVE_HOLD_VALUE_B03_INTAKE_20260908.md#9-prediction-retrieved-evidence-and-next-discriminator-rationale)
and P67 intake §4: the searched real-corpus coverage and ACAC/UTE/MVD/PPO source
conditions do not identify this UAV mechanism. No new source finding is claimed.
My inference is to test one fixed generic-capacity alternative with real training;
the source literature does not select its width or promise a gain. Another
unchanged pair would refine a different comparison. Exact capacity matching,
policy-class maxima, a support census, causal localization and baseline tuning
are unnecessary prerequisites for this B question. No search is selected.

## 2. Preserved native learner and information path

Preserve [B03 card §§2–3](VSPC1_NATIVE_HOLD_VALUE_B03_SCIENCE_CARD_20260908.md#2-preserved-learner-host-and-causal-path),
frozen at `72cbee0a82c870bf5a514cfada8970c62652479d`, as exercised by accepted
P67 source and summarized in [B04 card §2](VSPC1_NATIVE_HOLD_VALUE_B04_SCIENCE_CARD_20260908.md#2-preserved-method-and-information-path).
This card changes only the ordinary critic's second hidden width and the new
object/key/publication identity; §3 fixes that complete change.

Keep five UAVs/50 users, fixed membership, 256 primitive steps, 108-input recurrent
actors, all 136 pre-decision critic inputs, CPU FP32, explicit agent-compound PPO,
gamma=1 complete unaveraged return-to-go, two complete episodes per rollout,
four full-rollout epochs, original optimizer/hyperparameters, joint actor/critic
norm clipping and entropy coefficient .01. Opening durations remain 1/4 at t0;
natural remaining-hold inputs at t1–3 belong to the corresponding UAV. Actors
retain their own partial histories during holds. No roster/lifetime change,
replacement, altered time unit, information channel or action-search consumer
is introduced. Evaluation uses final sampled policies and native rewards.

Both arms use the accepted cumulative population FP32 value normalization:
fresh `n=0, mean=0, M2=0, updates=0, scale=1`; after data the scale is
`sqrt(max(M2/n,1e-8))`. Collect native values using the old moments, form the
original detached once-normalized native advantages, merge each of 512 scalar
targets once per rollout, then freeze normalized targets/moments over four
epochs. No agent/epoch replication, evaluation update, output-preserving rescale
or optimizer-state rescale. Final moments remain frozen during learned/H
evaluation; H has neither critic nor moment state. No historical state is loaded.

The proposed path remains opening duration → entity-owned remaining hold and
state → centralized scalar value and shared optimization → decentralized actor
updates → UAV motion/service → native team return. The critic is absent from
final action selection. Approximately 1.14% nonzero-hold training rows in 8202,
joint clipping/value units, FP32, initialization and partner co-adaptation remain
qualifications; this comparison does not uniquely attribute the path's effect.

## 3. Fixed comparator and initialization

GATED-V is unchanged: the source `136→128→128→1` tanh MLP, plus a zero-initialized
`128×5` gate on remaining-hold columns `(119,123,127,131,135)`. The ordinary
comparator is a fully connected `136→128→133→1` tanh MLP, with every input and
every weight trainable. It contains no gate, factorization, hold-specific mask,
extra feature, recurrent state or extra layer.

| Critic | Trainable critic parameters |
| --- | ---: |
| Historical full MLP, 136→128→128→1 | 34,177 |
| Unchanged GATED-V | 34,817 |
| B05 ordinary MLP, 136→128→133→1 | 34,827 |

[Python arithmetic](VSPC1_NATIVE_HOLD_VALUE_B05_PREPARATION_COUNTS_20260908.json)
gives a ten-parameter surplus over GATED, .0287216%; no count search or padding
is needed. The width is selected before B05 output, not tuned against it.

Create the common actor/critic templates by the unchanged `templates(8301)`.
Make separate arm copies and fresh optimizers; actor parameters, including the
zero-initialized duration head, start matched. For the wider MLP:

1. Copy the complete first Linear layer, the first 128 rows/biases of the second
   Linear layer, and the first 128 output weights plus its scalar bias from the
   common critic, without changing those values.
2. Initialize only the five appended second-layer rows using an independent CPU
   FP32 generator seeded `b+12`: draw the contiguous `5×128` incoming weight
   tensor first, then its five biases, uniformly on
   `[-1/sqrt(128), +1/sqrt(128)]`.
3. Set the five appended output weights to zero. All 650 added parameters remain
   trainable and belong to the same ordinary critic optimizer group. Their
   incoming gradients are zero on the first backward pass until outgoing
   weights move; this initialization consequence is explicit, not a freeze.

This preserves the common initial value function mathematically while allowing
generic additional features to learn. Different FP32 matrix shapes and the
existing gated decomposition may differ in rounding; no bit equality or extreme
tolerance is part of the scientific claim. Added construction/initialization
must leave global/common/action RNG states unchanged. No extra draw is made
from an actor, reset or evaluation stream.

Retain existing internal arm keys `GATED-V`, `MLP-V`, `H` and contrast keys to
reuse the accepted analysis. **In B05, `MLP-V` always means the width-133 MLP.**
Summary/checkpoints explicitly identify B05, this critic architecture and actual
parameter counts; the human result labels it `MLP-V (136→128→133→1)`. Never pool
its contrast with the historical width-128 contrast or silently reuse that label
without the B05/architecture identity.

## 4. Prospective key, independent unit and prediction

Nominate exactly one prospective master, **8301**, `b=830100000`. This nomination
allocates no invocation in P68. A bounded search of current direction docs,
code/tests/runners and Portfolio handoffs found no prior whole-token 8301/B05
binding; this is not a global seed-use guarantee. Tool arithmetic yields 612
distinct integer keys, with zero overlap against corresponding 8101/8102/8201/8202
domains. Constructor and first training reset deliberately share their key.

| Purpose | Exact domain |
| --- | --- |
| Common initialization / wider extra initialization | 830100011 / 830100012 |
| Private per-arm training velocity / duration | 830100021 / 830100022 |
| Each constructor reset | 830101000 |
| Training resets, e=0..511 | 830101000..830101511 |
| Final learned/H evaluation resets, e=0..31 | 830102000..830102031 |
| Private learned evaluation velocity / duration | 830103000..830103031 / 830104000..830104031 |

Matched seeds use separate mutable generators per arm. On-policy consumption may
differ; RNG matching is not shared policy data. Both learned policies and H use
the same final reset identities. The independent unit is one matched training
pair; 32 evaluation differences condition on its trained policies. B05 starts
a changed-comparator comparison with n=1 if completed, not a third interchangeable
observation of the old normalized comparison.

Working prediction: **UP, probability .55** for `Delta>.01`. Two prior local
normalized gains make persistence plausible, but the stronger generic-capacity
alternative and optimization/initialization uncertainty reduce confidence from
B04's .60. Score only that binary event after a trustworthy complete primary.
Owner prediction: **not taken (unattended)** unless an actual reply arrives.
No B05 endpoint exists at this definition.

## 5. Observable, MEI, headroom and all-outcome rule

Each learner trains 512 complete episodes, then evaluates its final sampled
policy on 32 resets. H uses zero velocity on those 32 resets in the second
environment. `J=sum(native rewards)/256`, without normalization; `Delta` is
the mean of the 32 identity-matched `J_GATED−J_MLP-WIDE133` differences. Retain
every endpoint, GATED−H/MLP−H contrasts, adverse identities and conditional
sample-SD/sqrt(32) SEs. No checkpoint, episode or seed selection follows output.

MEI is **absolute .01**: one continuously served extra user contributes
`.7/50=.014` before quality changes. A relative threshold against a potentially
weak comparator would be misleading. Tuned same-information headroom remains
**absent**; H is an attained untuned reference, not an upper. The prior baseline
set matches native observation/action/information and episode/update budgets;
the ordinary architecture and prospective randomness now differ, so earlier
endpoints remain contextual evidence and never substitute for B05's comparator.

| Observation | Bounded reading and next implication |
| --- | --- |
| Delta>.01 with trustworthy primary | UP: a local gated-package advantage over this specified similarly sized ordinary critic; retain H and all outcomes, then assess whether one later independent pair is worthwhile. No automatic follow-up allocation. |
| -.01≤Delta≤.01, including endpoints | WITHIN: no selected-scale advantage in this instance; retain sign/noise and prior comparisons, without equivalence or an automatic negative family judgment. |
| Delta<-.01 | DOWN: a native counterexample against this ordinary comparator at the fixed budget; prefer the wider MLP in this instance and retain prior gains. |
| One/both learners below H | Keep trustworthy Delta but narrow usable-control wording; report both H losses and do not declare comparator competence repaired. |
| Conditional SE leaves an MEI boundary unclear | Report the point-estimate region and conditional noise separately; no training-population statement or automatic extra evaluation. |
| A primary dependency is incomplete | No dependent performance judgment; retain independently trustworthy counts/returns. Missing H alone leaves a trustworthy primary reportable with H-relative use unresolved. |

Above MEI would show persistence against this generic-capacity alternative;
inside MEI would remove selected-scale separation in this instance; opposite sign
would favor the wider MLP here. None alone proves or refutes specialized hold
credit, identifies capacity's causal contribution, establishes stable superiority,
or generalizes across seeds/tasks. Equal parameter count is not equal function
class or optimization geometry. B04's original UP forecast and P66's unscored
failure stay intact. Any later result ends its one-pair allocation after intake,
regardless of sign; there is no run-until-positive rule.

## 6. Work, exposure, route and scope

Proposed algorithm work is `2×512×256` training plus `3×32×256` evaluation:
**286,720 native team steps**, 262,144 train/24,576 eval, **2,048 Adam calls**,
512 rollouts, 96 final evaluations, 1,120 scored episodes and two constructor
resets. The same 512 moment merges process 262,144 scalar rows, used in
1,048,576 four-epoch value-target terms. No nested candidates, search trajectories,
extra model-forward invocation, extra H/evaluation or tuning is added; width
changes the arithmetic within the existing critic calls. Added engineering
validation is separate from these counts and unexecuted in P68.

Per GATED arm: initialization +131072*c_env_actor +256*c_moment_merge(512)
+1024*c_update_GATED +8192*c_eval +publication. Per wider-MLP arm: its
initialization +131072*c_env_actor +256*c_moment_merge(512)
+1024*c_update_WIDE133 +8192*c_eval +8192*c_H +pair publication/readback/exit.
The wider second/output layers add 645 dense weights and five hidden biases
relative to the old ordinary MLP; actual width-specific wall is unmeasured.
Prior complete normalized pair walls 310.79/312.77s inform planning, not a
guarantee or a license for a calibration run. No parameter-count ratio is
presented as measured speed.

Retain **1800s per complete learned arm and 3600s per complete pair**, serial
GATED then wider MLP. Charge startup/common initialization to GATED, and
H/publication/readback/process exit to the wider MLP. Preserve continuous clocks,
terminal enclosing wall and internal split; retain/upper-bound unpartitioned
residuals as in P67, without borrowing/resetting clocks or premature hard kill.
Incomplete optional resource telemetry is marked `resources_unmeasured`; primary
and learner instrumentation failures follow their actual dependencies.

Machine-generated preparation exposure: **zero scientific invocations, zero
training pairs/fits, zero native steps, zero Adam/evaluation, zero models created**
in P68. Reused P67 exposure is total relative movement GATED .2534176631653249 /
MLP .23690194561741526, gate absolute .5487287640571594 from zero and relative
undefined/null. This shows movement at the inherited budget; the wider critic
has never trained. A later run reports actual counts/displacement; duration/gate
relative movement from zero remains undefined, with absolute movement retained.
No minimum movement, hold fraction or extra exposure probe is required.

Prospective route: configured remote-first `wsl_4070` / `hmasd-wsl-node`, CPU
FP32, one process and one numerical thread. Host is not the estimand. A later
allocated CM uses committed/pushed source, detached exact-SHA remote checkout,
the existing supervisor, a new run root, and fresh actual-node memory admission
before scientific roots/RNG/models. Preserve reward/RNG/dtype and evidence-spec
§11.4's four launch requirements. Current operations assign the complete
technical batch and default observation to CM; this card creates no new observer
or per-command Root relay. No staging, admission, handle or execution occurs in P68.

Engineering scope §4: **none**. Reuse learner/normalization/checkpoint/summary
machinery; add the ordinary critic, thin B05 binding and narrow existing caller
plumbing only. New non-test source≤2000 lines, runner≤600, focused checks≤300s
total. No general model registry, factory/configuration layer, new orchestration,
manifest/validator or telemetry machinery. No native smoke, timing, calibration,
standalone learner fixture or exhaustive diagnostic. The three CM comparison
batches ended at `a6dbacb36`; this preparation enrolls/dispatches no arm.

## 7. Selection and engineering readiness

Options: (a) select this single fixed width-133 ordinary comparator and complete
the proposed B05 contract; (b) prepare another unchanged width-128 pair;
(c) require capacity/causal search or promote the current evidence. Recommend/select
(a). Owner-delegated decision (unattended, 2026-09-03 instruction): (a),
**OWNER_DELEGATED within P68 preparation**. This is comparator/card wording inside
the accepted mechanism, an object-tier decision. No family open/close/recast,
C promotion, lifecycle, priority or formal UAV-entry decision is made; no Pro
direction question is needed. The CLI created P2
[20260908-vspc1-010](../../portfolio/owner/inbox/2026-09-08/20260908-vspc1-010.json)
from the [packet](VSPC1_NATIVE_HOLD_VALUE_B05_OWNER_PACKET_20260908.json), with
auto-applied accept for this definition only. Item009 receives no fabricated
owner response. Main's unapplied reviews and relevant audit owner cells were
empty at 2026-09-09T03:47:17Z; no review application was needed.

The complete [five-item engineering assignment](VSPC1_NATIVE_HOLD_VALUE_B05_CM_SPEC_20260908.md)
binds starting source `d220ef01c717c3053c2b26528c6f984302ee4aee` in the reused
`C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch
`codex/direction-vsp_c1`. P68 changes documentation only. Root receives the
committed card/spec and original acceptance checks before any CM starts.
**Definition ready for Root allocation; implementation and execution not allocated.**
An actual scope or numerical-integrity gap returns to this DM; routine future
engineering choices/corrections stay with the assigned CM. P68 ends at the
committed, pushed preparation and precise allocation return.

## 8. P69 source engineering allocation

After the completed P68 preparation, Root explicitly accepts this definition
and allocates the exact five-item CM source task frozen at
`c5835e98004daa4b77ac1e82f36eec7171e44972`. This new P69 allocation changes the
current implementation state; it does not rewrite P68's zero-implementation
history or infer an owner ratification of item009/010. Scientific §§2–6,
prospective master8301, prediction, comparator and caps remain unchanged.

Resume the same CM, `/root/dm_vspc1_p49_value_question/cm_am_vspc1_hold_value_b01`,
in the existing direction checkout/branch. Its source starting surface remains
`d220ef01c717c3053c2b26528c6f984302ee4aee` beneath the doc-only descendants.
The CM implements directly by default and reuses the original independent
reviewer. The original ≤300s focused-check allowance and scope bounds apply;
long committed verification follows remote-first when relevant. Source and
checks protect the historical width-128 route, private RNG, normalized native
method and explicit B05 publication identity. No fourth comparison is enrolled.

Options: (a) execute exactly that source engineering and DM technical intake;
(b) widen the task or launch its proposed native pair. Recommend/select (a).
Owner-delegated decision (unattended, 2026-09-03 instruction): (a),
**OWNER_DELEGATED within Root's explicit P69 source allocation**. P69 ends at
accepted/pushed source, DM technical acceptance and one exact prospective
execution binding returned to Root. **Zero scientific invocation; no staging,
admission or submission in this phase.** A binding will be a prospective
declaration, not an observed remote-ready command or an execution allocation.

## 9. P69 accepted source and one prospective execution binding

Accept source **`bda90e1db76a00123ba889ed6c4b05225473f4cb`**, committed and
pushed by the same CM in the designated checkout. I inspected the complete
production diff, relevant tests and retained check evidence, the
[technical acceptance](VSPC1_NATIVE_HOLD_VALUE_B05_TECHNICAL_ACCEPTANCE_20260908.md)
and full [independent review](VSPC1_NATIVE_HOLD_VALUE_B05_PRODUCTION_REVIEW_20260908.md)
against the original contract. No material finding remains. The 25-line ordinary
critic implements §3's copy/draw/zero-output rule; the 35-line runner fixes
8301/width133/normalization. Narrow shared-caller changes preserve width128
defaults and attach actual B05 architecture/count identity to summary/checkpoints
and existing readback. Protected learner/normalization/native/historical-runner
source has no diff. Complete production change is 95 added/9 removed lines;
scope §4 additions:none, with no observed source/runner-budget breach.

Sixteen new checks passed in 13.65 pytest seconds and nine directly affected
default checks passed in 2.69 pytest seconds: sum 16.34s. The second enclosing
process wall was 3.7350489s; the first was not separately retained. Preserve that
measurement limit rather than certify a complete enclosing sum from pytest
durations. No 300s check-budget breach was observed. Deterministic tensor tests
construct critics and exercise gradients, and pipeline stubs verify identities,
counts, moments and rule branches; they supply no native performance, scientific
training pair or forecast outcome. DM/reviewer did not repeat CM execution.

The following is **one prospective binding only**, with no staged inputs,
admission, accepted handle or scientific invocation in P69. Remote path/handle
existence has not been probed in this phase. Exact source is the full SHA above;
the later executor must use its committed scientific bytes, not a moving HEAD.

| Field | Prospective binding |
| --- | --- |
| Node / interpreter | `wsl_4070`, `hmasd-wsl-node`, `/home/wu/.venvs/hmasd/bin/python` |
| Device / process / numerical threads | CPU FP32 / 1 / 1 |
| Detached cwd | `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b05-8301-bda90e1db76a` |
| Requested supervisor handle | `vspc1_hold_value_b05_8301_bda90e1db76a` |
| Prospective staged payload path | `/home/wu/hmasd-inputs/vspc1_hold_value_b05_8301_bda90e1db76a.sh` |
| Output | `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b05_8301_bda90e1db76a` |
| Admission receipt | `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b05_8301_bda90e1db76a_admission.json` |
| Scientific argv | `scripts/run_vspc1_native_hold_value_b05.py --seed 8301 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b05_8301_bda90e1db76a` |
| Counts / complete caps | §6's 286720 steps / 2048 Adam / 96 evaluations; 1800s per learned arm / 3600s complete pair |

Literal prospective LF payload, reusing the accepted P67 enclosing-timer pattern:

```bash
#!/usr/bin/env bash
set -euo pipefail
exec /usr/bin/time -f 'whole_wall_seconds=%e,peak_rss_kib=%M' /bin/bash --noprofile --norc -c '
cd /home/wu/hmasd-worktrees/vspc1-native-hold-value-b05-8301-bda90e1db76a &&
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b05_8301_bda90e1db76a_admission.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_native_hold_value_b05.py --seed 8301 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b05_8301_bda90e1db76a
'
```

This committed text is not a staged/executed script. A later allocated CM batch
stages/verifies the exact detached source and these inputs, performs fresh
actual-node admission before scientific state, and uses the single literal
binding under the existing supervisor. It retains the enclosing wall/internal
split and all H/publication/exit work within the original caps. That later
allocation must explicitly authorize its accepted submission; P69 grants none.

Object-tier technical options: (a) accept conforming source and return this
prospective binding; (b) add a native smoke or treat check success as a B result.
Recommend/select (a). Owner-delegated decision (unattended, 2026-09-03 instruction):
(a), **OWNER_DELEGATED within P69**. Main owner reviews and relevant owner cells
were empty at 2026-09-09T04:15:46Z. Item009 remains unratified; item010's
definition acceptance is unchanged. No UP/WITHIN/DOWN, native-cost or mechanism
decision follows. P69 ends at the pushed technical intake and Root allocation
return; the future B05 sampled native pair remains the next discriminator.

## 10. P70 allocation — one exact technical execution batch

Root accepted the completed P69 source/technical return and now explicitly
allocates **at most one accepted supervisor submission** for B05/master8301.
This is a new P70 allocation after P69 ended, not owner ratification of item009
and not a rewrite of P68/P69's zero-execution history. Scientific source remains
`bda90e1db76a00123ba889ed6c4b05225473f4cb`; §9's exact node/cwd/payload/handle/
output binding and §§2–6's science, UP(.55), MEI and all-outcome rule are unchanged.
The pair remains286720 native steps/2048 Adam/96 evaluations, with1800s per
complete learned arm and3600s through H/publication/readback/process exit.

The same CM owns the whole technical batch: commit/push the literal wrapper if
needed, stage exact scientific bytes and every runtime input including the
canonical admission helper, compare the current source surface, and use the
configured detached supervisor. Stage the science checkout at the bound full
SHA; a separately committed literal wrapper does not change those scientific
bytes or permit a moving checkout. Fresh actual-node admission must report
both physical and effective available memory≥4GiB before scientific state.
CM is sole observer through terminal all-outcome collection and technical
acceptance; DM owns scientific intake/brief/audit. No per-shell Root relay or
additional pre-launch approval step is added.

If an unexpected prior handle/path exists, reconcile its actual state without
launching. An actual input, cap or admission conflict returns its precise
evidence; never silently substitute a path, helper, source, key or cap. No native
smoke/pilot, extra seed/evaluation, retry/resubmit or automatic successor is
allocated. One accepted submission spends this allocation even if the payload
fails before learning; retain the failed identity and every independently
trustworthy fact. This is an allocation boundary, not B-object consumption.

Object-tier options: (a) execute exactly this new P70 one-submission allocation
and take in every outcome; (b) enlarge/retry the pair or require an extra
diagnostic first. Recommend/select(a). Owner-delegated decision (unattended,
2026-09-03 instruction): (a), **OWNER_DELEGATED within explicit Root P70**.
At this record the new allocation has zero accepted submissions and zero new
scientific exposure. The source-test timing qualification in §9 remains intact.
No scientific polarity or owner reply is inferred from this allocation.

## 11. P70 terminal result and allocation stop

The single accepted submission completed exit0 on2026-09-09T04:36:57Z at §9's
exact scientific SHA/cwd/handle/output. [E0](VSPC1_NATIVE_HOLD_VALUE_B05_RESULT_EVIDENCE_20260908.md)
and [scientific intake §9](VSPC1_NATIVE_HOLD_VALUE_B05_INTAKE_20260908.md#9-p70-valid-result--scientific-intake-and-complete-allocation-boundary)
retain source/receipts, all outcomes, the unchanged rule and decisions.
Native GATED−MLP-wide133=+.01659191137627875, conditional SE .008099210958544987:
**UP** at the point estimate, with margin above MEI .0065919114 smaller than SE.
GATED−H=+.0296867693 and MLP-wide133−H=+.0130948580; adverse episodes are13/8/13
of32 across the primary/GATED−H/MLP−H contrasts. One independent training pair
in this new comparator regime supplies no training-population uncertainty or
stable/mechanism attribution claim; previous regimes and their H losses stay separate.

Actual exposure:2 fits,286720 native steps (262144 train/24576 eval),2048 Adam,
512 rollouts/512 moment merges,96 final evaluations and no partial steps.
Fresh actual-node physical/effective admission passed; all publication/identity
checks passed. Complete wall315.20s and conservative per-arm upper bounds
167.9571218310/155.6930584460s satisfy1800/3600s caps. Peak RSS546.4296875MiB;
aggregate CPU/width-specific overhead remain unmeasured. Scope §4 needs none;
no observed §5 breach, with P69's test-wall measurement qualification preserved.

Recorded UP(.55) is a hit, binary Brier .2025; owner prediction not taken.
Owner-delegated decision (unattended,2026-09-03 instruction): accept this bounded
valid UP and finish P70's allocation with every outcome retained. A later one-pair
repeat of this unchanged comparison is direction-local advice only: no new
card/key/run or automatic successor is allocated. This B has no consumption
state; no direction/Portfolio disposition or formal UAV-entry decision is made.
