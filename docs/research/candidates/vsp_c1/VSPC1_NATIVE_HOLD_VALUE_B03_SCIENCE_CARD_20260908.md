Claim under test: the gated centralized critic retains a native-return advantage over the full MLP when both use the same running value-target normalization rule.
Binding MARL structure: (b) temporal abstraction or termination, with five co-adapting agents retaining separate partial-observation histories.

# VSPC1-NATIVE-HOLD-VALUE-B03 — prospective B/EXPLORE

## 1. Question, authority and evidence boundary

[P60](../../portfolio/handoffs/2026-09-08-p60-vspc1-normalized-value-comparison.md),
published at `300e44011` and delivered by Root, selects one new within-family
comparison after [B02 intake §§2–5](VSPC1_NATIVE_HOLD_VALUE_B02_INTAKE_20260908.md).
Ask whether the local GATED/full-MLP contrast persists under symmetric value-target
normalization, and report each learner's native performance relative to Hover (H).
This is outcome-informed exploration under a changed training regime. It supplies
one new training pair; it is not a third replication of the original regime.

Preserve the original pairs separately:

| Master | GATED−MLP | GATED−H | MLP−H |
| --- | ---: | ---: | ---: |
| 8101 | +.0293656586 | +.0194005494 | −.0099651092 |
| 8102 | +.1157271305 | +.0265020852 | −.0892250453 |

Both package gains and both weak-MLP/H observations survive. Extra gate capacity,
shared gradient clipping, value scale and seed-specific on-policy optimization
remain alternatives to specialized hold-credit improvement. Normalization is a
candidate training change, not a diagnosed repair or a guaranteed improvement.

Reuse the verified local-library coverage and primary-source retrieval in
[B02 intake §3](VSPC1_NATIVE_HOLD_VALUE_B02_INTAKE_20260908.md#3-question-driven-evidence-and-next-discriminator-rationale).
Yu et al., *The Surprising Effectiveness of PPO in Cooperative, Multi-Agent Games*,
arXiv2103.01955v4, [§5.1](https://arxiv.org/html/2103.01955v4#S5.SS1), motivates
normalized value targets with values restored to return units for policy credit.
Its GAE/MPE/SMAC setting differs from this complete gamma1-return-to-go learner.
The cumulative moments and floor below are this card's explicit engineering
choice, not a claim to reproduce that paper's exact implementation. No further
literature search, exact headroom calculation or causal audit precedes this B.

The ceiling is one local normalized-regime package comparison with separate H
qualifications. Historical differences cannot identify a normalization effect
because regime and fresh training/evaluation randomness change together. No stable
superiority, unique mechanism, transfer, optimality, C promotion, family closure,
recast, lifecycle, priority or formal UAV-entry decision follows.

## 2. Preserved learner, host and causal path

Reuse [B02 card §2](VSPC1_NATIVE_HOLD_VALUE_B02_SCIENCE_CARD_20260908.md#2-preserved-algorithm-host-and-measurement)
and accepted source `0ec208899f5e8b4c190ab7bd9806be2cc30b6fda`:
five UAVs/50 users, fixed membership, 256 primitive steps, native observation,
action and reward; 108-input recurrent duration-capable actors and 136 pre-decision
critic inputs; opening duration1/4 at t0 and natural remaining-hold exposure at
t1–3; separate actor histories advancing during holds. The full MLP remains intact;
GATED adds its existing zero-initialized 640-parameter multiplicative gate.
Common parameters start equal, with separate copies, optimizers and generators.

Complete input revision `e5cc7ce67cf9dfa4ebd95324bf5c67423bc9977a` also preserves
the accepted main UCOPE `entropy_coef` argument from `56433ec55`. Its default
and this VSPC1 comparison remain .01; the UCOPE zero-entropy experiment is not
inherited. This is source reconciliation before B03 implementation, not a
scientific change to either historical VSPC1 pair.

Preserve explicit `agent_compound` PPO, complete gamma1 return-to-go, two complete
episodes per rollout, four full-rollout epochs, original optimizer/hyperparameters,
joint actor/critic norm clipping and all-held value/reward/recurrence rows. Only
the specified value units, targets and their running moments change. No actor
information, action density, hold semantics, checkpoint selection or native reward
changes; no duration search or counterfactual target is added.

The path is prior hold/state → scalar critic and shared optimization → local
actor update → motion/service → native team return. The collector converts critic
outputs to native return units for credit. No actor receives central information
or normalization moments; the critic has no action-search consumer.

## 3. Frozen normalization semantics

Each learned arm owns one independent scalar running-moment state. It is outside
autograd and Adam and uses CPU FP32, as do model computation and targets. Count
and update count are integers. Both arms use this exact method on their own
on-policy training returns; they neither share moments nor fit each other's data.

1. Initialize `n=0, mean=0, M2=0, updates=0`; the empty-state scale is exactly1.
   After data, `scale = sqrt(max(M2/n, 1e-8))`, a standard-deviation floor of
   `1e-4` in native return units. This numerical floor is fixed without tuning.
   There is no pseudo-observation, EMA decay, per-agent statistic or reward scaling.
2. Treat raw critic output `f_theta(c)` as normalized value. During both complete
   episodes of a training rollout, use the unchanged pre-update moments to store
   `V_native = mean + scale * f_theta(c)` at every primitive row. Collection does
   not change moments. Initial values therefore have the original units/scale.
3. Build native targets `Y[e,t] = sum(reward[e,t:256])`, without horizon averaging
   or terminal bootstrap. First compute `A_raw = Y - stored_V_native` and the
   original once-normalized, detached advantages over all 512 rows:
   `(A_raw - mean(A_raw)) / (std_population(A_raw) + 1e-8)`. Keep these advantages
   unchanged across four epochs. Never reinterpret stored values using new moments.
4. Update moments exactly once from these 512 native targets, in episode/time
   order, before the first epoch. Use a population-moment merge: for batch size
   `k`, batch mean `m_b` and `M2_b = sum((Y-m_b)^2)`, the first batch sets
   `(n,mean,M2)=(k,m_b,M2_b)`; otherwise with `d=m_b-mean` and `N=n+k`, set
   `mean_new=mean+d*k/N`, `M2_new=M2+M2_b+d*d*n*k/N`, then `n=N`.
   Compute these scalar moments in FP32 and increment `updates` once. Include
   held and active rows once, with no five-agent replication, epoch duplication,
   evaluation input, other-arm input or historical-data input.
5. Freeze those new moments for all four epochs. Detach
   `Y_norm=(Y-mean_new)/scale_new`; value loss is
   `mean((f_theta(c)-Y_norm)^2)` in normalized squared units. Total loss remains
   `policy_loss + .5*value_loss - .01*mean(entropy)` with the existing Adam calls
   and joint norm clip. Policy terms still use the native-credit advantages from
   step3. Do not divide native advantages by the value scale a second time.
6. No output-layer or optimizer-state rescaling accompanies a moment update.
   Consequently updating moments can change decoded native predictions even
   before Adam; that behavior is part of this method. This is not a PopArt
   output-preservation claim. No statistics or value parameter is tuned on eval.
7. Save final `n, mean, M2, scale, updates` with each existing final checkpoint;
   the critic weights alone no longer describe a native-value prediction. Keep
   the moments frozen during all 32 learned evaluations and H. H uses no critic
   or moments. Publish each rollout's post-update scalar state and label value
   loss units; retain the final state and before/after-evaluation counts in the
   normal summary/readback. A complete fit has 256 moment updates and 131072
   target rows. Partial work retains its actual state/counts without completion.

Normalization adds no learned parameters and no critic forward pass. The initial
raw GATED/MLP functions and actor initialization remain matched. The full MLP is
not narrowed, capacity-matched, retuned or replaced. Old B01/B02 runners and their
default unnormalized computation remain unchanged in meaning.

## 4. Fresh key, prediction and independent unit

Freeze **master8201**, `b=820100000`, the first unused key in the declared new
normalization namespace. A bounded HEAD/main search of this direction's committed
documents/code/tests/runners and Portfolio handoffs, plus existing direction temp
filenames, found no prior8201 binding/output. This is not a global seed-use claim.
Python arithmetic at2026-09-08T21:42:17Z found611 distinct integers in these
domains and zero overlap with either8101 or8102's corresponding domains.

| Purpose | Exact domain |
| --- | --- |
| Common initialization | 820100011 |
| Private per-arm training velocity / duration | 820100021 / 820100022 |
| Each constructor reset | 820101000 |
| Training resets,e=0..511 | 820101000..820101511 |
| Final learned/H evaluation resets,e=0..31 | 820102000..820102031 |
| Private learned evaluation velocity / duration | 820103000..820103031 / 820104000..820104031 |

Use private mutable generators with matched seeds, not shared generators. Neither
arm loads an earlier model, optimizer or moment state. Stream consumption may
differ on-policy. The independent unit is **one matched training pair**; 32 eval
rows quantify conditional endpoint variation, not training-population uncertainty.
Do not pool this changed regime with8101/8102 as three identical training pairs.

Working prediction: **WITHIN, probability .55** for `-.01 <= Delta <= .01`.
The two old gains favor GATED, but weak MLP/H and the shared clipping/scale path
make a smaller contrast under common normalization plausible. This is a modest
forecast of the declared event, not a prediction that normalization fixes MLP.
Score its binary-event Brier only after a trustworthy complete primary; UP/DOWN
miss, and no probability split for those two regions is invented. Owner prediction:
**not taken (unattended)**; score an actual reply if one arrives.

## 5. Observable, MEI and all-outcome reading

Each arm trains512 complete episodes and evaluates only its final sampled policy
on32 resets. H executes zero velocity on the same32 resets, reusing the second
environment. `J=sum(native rewards)/256`; rewards and this measurement never use
normalization. Delta is the mean of32 identity-matched `J_GATED-J_MLP` values.
Retain every endpoint and all three contrasts with sample-SD/sqrt(32) conditional
SE. This cannot estimate training-seed uncertainty from one normalized pair.

MEI is **absolute .01** on native J: one continuously served additional user
contributes .7/50=.014 before quality changes. No relative threshold is imposed
on a weak/near-zero comparator. Tuned same-information headroom is **absent**;
H is attained and untuned, not an upper bound. Historical baselines are retained
as context; their training regime does not match this normalized comparison.

| Observation | Selected bounded reading and next implication |
| --- | --- |
| Delta>.01 with trustworthy primary | UP: one local normalized-regime signal for the complete gated package; preserve both H contrasts and every adverse episode before recommending a next discriminator. |
| -.01≤Delta≤.01, including endpoints | WITHIN: no selected-scale benefit in this instance; retain sign/SE without equivalence or automatic extra training/evaluation. |
| Delta<-.01 | DOWN: native counterexample for the gated package under this normalization rule and budget; prefer MLP for this specific comparison, without a K4-wide negative. |
| One/both learners below H | Retain trustworthy Delta but narrow usable-control wording; do not hide H loss or declare normalization a repair. |
| Conditional SE leaves an MEI boundary unclear | Report the point-estimate region and conditional noise separately; no training-population conclusion or automatic extra episodes. |
| A primary dependency is incomplete | No dependent performance judgment; retain independently trustworthy counts/returns. Missing H alone leaves a trustworthy primary pair reportable with H-relative use unresolved. |

Above MEI would retain a local gate-package signal under this common training
change; inside MEI would show no selected-scale benefit here; opposite sign would
add a normalized-regime counterexample beside the old gains. A positive MLP−H
would soften the comparator qualification for this instance only. A negative
MLP−H would retain it. Neither a historical contrast nor either outcome identifies
normalization's causal effect. Report both H contrasts and then recommend the
smallest useful next discriminator. **P60 ends after this one pair and intake
regardless of sign.** No second normalized pair, old-regime pair, tuning, ablation,
extra H/evaluation, alternate seed or retry is allocated.

## 6. Work, exposure and execution

Python-computed work is2×512×256 training steps +3×32×256 final evaluation steps:
**286720 native team steps**,262144 train/24576 eval,2048 Adam calls,512 rollouts,
96 final evaluations,1120 complete scored episodes and two constructor resets.
Moment work is2×256 merges of512 scalar targets (262144 target rows), and the
four-epoch value loss uses1048576 target-row terms. There is no nested search or
extra learner. Focused engineering tests add no native scientific invocation.

Per arm: initialization +131072*c_env_actor +256*c_moment_merge(512)
+1024*c_update +8192*c_eval +publication. MLP also owns8192 H steps and pair
publication/readback/exit. The two old enclosing walls308.63s/304.52s are planning
references, not a cost guarantee; scalar-normalization overhead is unmeasured.
No timing/calibration experiment is selected. Keep serial GATED then MLP and the
complete caps **1800s per learned arm,3600s per pair**, with startup/common
initialization charged to GATED and H/publication/readback/exit charged to MLP.
Retain enclosing terminal wall/internal split and any unknown residual split;
no clock reset, borrowing or premature hard kill substitutes for publication.

Machine-generated exposure line reused from [B02 collection evidence](VSPC1_NATIVE_HOLD_VALUE_B02_COLLECTION_EVIDENCE_20260908.json):
total relative movement GATED .5389322229365768 / MLP .46125991503565106;
gate absolute2.601895809173584 from zero, relative null. The prior learner can
move at this budget; the changed normalized regime has **zero exposure at freeze**.
Report its actual parameter movement/counts. Moment changes are not parameter
displacement; zero-initialized relative ratios remain undefined, with absolute
movement reported. No minimum gate movement or hold fraction is required.

Use configured remote-first `wsl_4070`/`hmasd-wsl-node`, CPU FP32, one process and
one numerical thread; host/device is not the estimand. Fresh actual-node memory
admission precedes scientific roots/models/RNG state. Only evidence-spec §11.4's
four requirements may hold launch. Preserve partial evidence on failure/cap
breach; missing optional telemetry remains `resources_unmeasured`.

Engineering scope §4: **none**. Normalization moments extend the existing final
critic checkpoint's scientific state; no new checkpoint/resume orchestration is
needed. New source≤2000 non-test lines, runner≤600, focused tests≤300s total.
Reuse unchanged acceptance; no standalone synthetic runner fixture or native
smoke/profile/calibration. The three CM comparison batches ended at `a6dbacb36`;
this assignment adds no fourth comparison. [CM spec](VSPC1_NATIVE_HOLD_VALUE_B03_CM_SPEC_20260908.md)
fixes the owned boundaries and original focused acceptance.

## 7. Decisions and preparation state

Options: (a) implement P60's one symmetric normalized comparison with the exact
rule above; (b) add a diagnostic/tuning prerequisite; (c) add an old-regime pair.
Recommend and select (a). Owner-delegated decision (unattended,2026-09-03
instruction): (a), **OWNER_DELEGATED within P60**. P60 supplies the allocation;
the old advice item is not an owner reply. Reviews were empty at preparation.
The owner-console CLI created P2 [20260908-vspc1-006](../../portfolio/owner/inbox/2026-09-08/20260908-vspc1-006.json)
with [this packet](VSPC1_NATIVE_HOLD_VALUE_B03_OWNER_PACKET_20260908.json), auto-applied
accept under the standing delegation. No reply is required or invented.

Freeze master8201, WITHIN(.55), the normalization rule, native MEI and complete
work limits before model construction or output. At this boundary there is no
implementation, test, scientific model, environment call or accepted handle for
B03. Root receives the complete committed CM specification and binding request.
The same CM then implements/reviews; accepted source and exact detached command
will be bound here before Root submits the sole pair. Collection returns to that
CM and scientific intake to this DM, without another Portfolio vote.

## 8. Accepted source and sole Root execution binding

At2026-09-08T22:34:39Z, accept the delivered engineering evidence against §§2–6
without changing the frozen question, master8201, WITHIN(.55), normalization,
native MEI, counts or stop. Accepted source is
**`7a8ed3aa5d25ded71164aa338749d09318124dcf`**. Final technical/command review is
`d945aba70a72d217071f94f45d09c1cf0c4313ca`; Root integrated them as
`7c80750ea`/`9148acf65`. The launch binds the original accepted source SHA,
not a later documentation commit.

Read the complete [independent review](VSPC1_NATIVE_HOLD_VALUE_B03_PRODUCTION_REVIEW_20260908.md),
the [technical acceptance and literal command](VSPC1_NATIVE_HOLD_VALUE_B03_TECHNICAL_ACCEPTANCE_20260908.md#exact-root-command-staged-not-submitted),
retained focused result and launch binding. Inspected actual moment/collector/
update/study/runner changes and relevant tensor/plumbing checks. The saved native
value precedes the single moment merge; detached normalized targets and native
advantages remain fixed for four epochs; each arm owns its moments; evaluation
does not fit them. Entropy remains .01, with full MLP, gate, actor/hold/reward,
RNG and historical-default meaning preserved. No source difference exists between
the accepted SHA and the current direction checkout on code/test surfaces, or
the integrated main normalization surfaces.

The original focused command passed17 checks in2.54s pytest/3.5546191s process
wall. A preceding collection-only module-name collision used3.01197s process wall
and was repaired by a test-package marker; total6.5665891s is within300s. The
independent review has no material unresolved finding. Source adds127/removes13
non-test lines, runner35, with scope §4:none and no budget breach. These facts
establish engineering conformance only. No native fit, standalone fixture,
calibration, resource admission or scientific process ran in that acceptance;
stub counts and tiny no-step gradient checks are not B03 native exposure. The DM
did not repeat tests or execute models during this binding.

Root now stages exact source `7a8ed3aa5d25ded71164aa338749d09318124dcf` at
`/home/wu/hmasd-worktrees/vspc1-native-hold-value-b03-8201-7a8ed3aa5d25`
on configured `hmasd-wsl-node`. CM staged only the script at
`/home/wu/hmasd-inputs/vspc1_hold_value_b03_8201_7a8ed3aa5d25.sh`;
source-checkout existence/staging remains Root's action. The655-byte LF script
and retained remote readback agree; the syntax-only check passed. Its one exact
submission is:

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run vspc1_hold_value_b03_8201_7a8ed3aa5d25 /bin/bash /home/wu/hmasd-inputs/vspc1_hold_value_b03_8201_7a8ed3aa5d25.sh
```

The script joins configured-Python `admit-memory` to the fixed8201 runner in
that exact cwd. Require both actual-node physical/effective available memory
≥4GiB before scientific roots/RNG/models. Output is
`/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b03_8201_7a8ed3aa5d25`;
admission is its sibling `native_hold_value_b03_8201_7a8ed3aa5d25_admission.json`.
Requested handle is `vspc1_hold_value_b03_8201_7a8ed3aa5d25`; **none is accepted
at this binding**. Preserve CPU FP32/one process/one numerical thread and the
continuous1800s/arm,3600s/pair limits. The enclosing time includes admission and
exit; a positive external-minus-internal residual with unknown split is reported
and included fully in each conservative arm upper bound. An overrun remains a
breach; no hard-KILL wrapper, budget reset, extra arm/seed/evaluation or retry.

Options: (a) bind accepted source and this sole P60 command; (b) add a native
probe or calibration before it. Recommend/select (a). Owner-delegated decision
(unattended,2026-09-03 instruction): (a), **OWNER_DELEGATED within P60**. Current
owner reviews and relevant ledger overrides are empty. No new owner item is
needed for this technical decision. Root owns submission/observation; terminal
facts return to the same CM for collection and this DM for all-outcome intake.
Actual native return, movement, moment counts and resource conformance remain
unmeasured until that sole invocation. The preparation's zero-exposure boundary
and original reading rules remain historical and unchanged.

## 9. Pre-admission failure and corrected supervisor identity

The original accepted supervisor handle failed at the missing-cwd `cd` before
admission or scientific execution. The [intake](VSPC1_NATIVE_HOLD_VALUE_B03_INTAKE_20260908.md)
records the full boundary, zero native exposure and object-tier correction;
[CM evidence](VSPC1_NATIVE_HOLD_VALUE_B03_CWD_CORRECTION_EVIDENCE_20260908.json),
commit `698b8aeff26f2b9ae21d4cb8d1bf8a255b161d38`, now establishes the exact
detached cwd exists clean at accepted source `7a8ed3aa5d25ded71164aa338749d09318124dcf`.
The original log and supervisor metadata remain preserved. No source, script,
scientific key, work allowance, prediction or reading rule changes.

Root's corrected submission uses only a fresh supervisor name:

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run vspc1_hold_value_b03_8201_7a8ed3aa5d25_cwd1 /bin/bash /home/wu/hmasd-inputs/vspc1_hold_value_b03_8201_7a8ed3aa5d25.sh
```

This supersedes §8's pending staging and original submission identity. The new
handle is not yet accepted at correction intake. The selected scientific pair
remains unrun, with fresh admission and the original complete limits in the
unchanged script; no duplicate scientific execution or extra retry is authorized.
