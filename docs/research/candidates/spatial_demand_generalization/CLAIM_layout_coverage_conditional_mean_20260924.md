# Draft C01: conditional program-mean hotspot use

Status: proposal for Pro criticism, not an adopted confirmation or accepted run.
Direction: `spatial_demand_generalization`; lead `Codex DM (independent session)`.

## Claim and selection exposure

At fixed S1/N6/c10, 50 users, LOCAL1 and 360k training steps per arm, the specified
8-uniform/8-cluster lane program has positive mean final45 native J **and** served-user
increments over the specified 16-uniform program on one prospectively fixed hotspot panel.
The intended averaging is over fresh paired training instances of these complete programs,
conditional on the specified environment, implementation and evaluation worlds. This is not
a claim about arbitrary hotspot locations, pure support-coverage causality, all future training
instances, zero uniform cost, new partners, or general MARL robustness.

The comparison was selected after A2 model seed 260925101: hotspot M-minus-U J +.0185689864
and service +.940750, with 12/32 worlds adverse in J or service. Uniform mean service was
-.0000625 with 17/32 adverse worlds; cluster was +.0401648661 J / +2.0878125 service.
U itself learned useful hotspot control. This complete exploratory pair and its worlds are
selection evidence only and will not enter the confirmation estimate or interval.

## Fixed proposed batch

Five new paired blocks, ten fits, ordered block 0..4 and U then M within each block.
Keep the accepted A2 algorithm, physical host, information rights, schedule and final45 rule
at `d22b608e8d063ceac5c944426bd35a2289c5ebf6`; only introduce the declared independent block
seeds and aggregation. CPU/float32, four torch threads, H500, 16 training lanes, 45 updates,
hidden256/8 heads/2 layers, 15 PPO epochs, sequence minibatch32, k10 and entropy .05.
U is all uniform; M uniform iff `(lane+r)%16<8`, zero-based r0..44, otherwise cluster.
World and learner RNG remain separated; evaluation uses frozen targets with no training.

| Block b | Actual model/learner seed | Training reset base |
| --- | --- | --- |
| 0 | 263000101 | 264000000 |
| 1 | 263000102 | 264100000 |
| 2 | 263000103 | 264200000 |
| 3 | 263000104 | 264300000 |
| 4 | 263000105 | 264400000 |

Training world seed is base +1000*r+lane. Configuration-only constructor seed is
269900000+1000*b+lane, followed by the explicit training reset; none of those constructor
worlds supplies transitions. Within a block, both arms start with actually identical model,
normalizer, optimizer, sampler and RNG state. Each block has distinct learner and training
world streams. Technical tests use separate addresses and reduced dimensions.

All blocks share the same fixed, fresh evaluation panels: uniform 265000000..265000031,
cluster 265010000..265010031, hotspot 265020000..265020031. These worlds are unexposed at
proposal time. Per block evaluate the actual common initialization and both final45 policies
on every family, 32 worlds × H500. Verify the physical initial states within family/policy
and across blocks; retain every world and every adverse result. The existing fixed-center
hotspot generator is unchanged. No endpoint, mixture, world or block selection follows results.

## Estimand and proposed fixed decision

For each block b, first average paired M45-minus-U45 J and served users over its 32 hotspot
worlds, yielding dJ_b and dS_b. The five training-block differences are the five units of
analysis. Do not pool world rows as training replication, bootstrap worlds for training
uncertainty, or pool A2 with these blocks.

Report all five differences, their mean, SD, range, signs and each marginal two-sided 95%
Student-t interval, using df=4 and t(0.975,4). The joint directional claim is supported by this
fixed rule only if **both** lower bounds are strictly above zero. Otherwise it is not
established; distinguish adverse direction from imprecision and never infer equivalence.
This is an intersection decision using two marginal intervals, not a simultaneous 95%
confidence region. The t working model and five independent blocks are substantial limits;
neither normality nor adequate power is established by n=5 or by the old 32 worlds.
This does not promise the next training instance will benefit.

Read uniform and cluster J/service effects with the same block summaries, but keep them
secondary; show native quality, height penalty, eligibility, unserved eligibility and all
local losses. There is no predeclared noninferiority margin or claim of harmless replacement.
The zero primary margin tests a positive mean, not a minimum practically useful improvement.
At unchanged training exposure and inference, about one additional served user per step is
a useful reference scale on this 50-user host: two coverage percentage points and about 4%
of the observed U endpoint's service. This is a declared scale for interpreting the estimate,
not a newly claimed success margin; report how the interval compares with zero and one user.
A precise but much smaller gain can satisfy the mean-sign rule while failing to justify use.
Keep each arm's own-learning changes from its real common initialization as diagnostics;
do not remove a block because U learns weakly.

## Cost, failure and stopping

Planned training: 5×2×360k =3.6M team steps / ten fits. Evaluation: 5×144k =720k team steps,
1,440 episodes and no updates. Total 4.32M team steps /25.92M UAV action rows, 450 outer
updates and 1,012,500 calls of each optimizer. Retained native evidence is roughly 5.44 GB
by A2's measured size, plus verified copies. A2's actual admission-to-exit 89.18 minutes per
pair suggests approximately 7.43 hours sequentially on the same node; this is an estimate,
not an entitlement, deadline or measured new cost. Include implementation, review, staging,
collection, verification, reading and any runtime contention separately.

Use the current configured suitable node and native resource admission, within the existing
three-track ceiling. Publish one fixed implementation and all five blocks before any result
run; enter them sequentially without selecting later blocks from earlier scores. No additional
endpoint, sixth block, alternate seed, mixture search, early checkpoint or automatic retry.
A technical failure is retained with actual fit/cost and leaves this fixed confirmation
incomplete; it does not become a negative, substituted endpoint or silently smaller batch.
Any new investment after this batch needs its own reason and prospective decision.

## Result

No confirmation run has been accepted. This draft is being compared against a cheaper
prospective frozen-policy spatial-dependence observation and stopping; Pro advises, then
the DM adopts, revises or rejects the actual next action in NOTES.

## Adoption 2026-09-24

The preceding proposal is now adopted unchanged as the fixed C01 confirmation plan, following
the complete Pro critic pass at `ca77013402426ce5254ab260d688b651e3664178` and the DM decision
in NOTES, "C01 adopted: five fresh paired blocks, one fixed conditional-mean confirmation".
The original proposal/selection record above is preserved. No run has started at adoption.

Two interpretation clarifications are adopted without changing the rule: C01 changes both
training instances and the fixed evaluation panel, so it cannot uniquely attribute A2's sign
to training randomness versus program-by-panel interaction. A zero-margin statistical pass
does not establish an approximately one-user increment or automatically justify replacing U
or further investment in this recipe. The t assumptions, all adverse evidence, exact five
blocks and no-rescue stopping rule remain as written.

## Result 2026-09-25 — complete fixed batch; joint positive mean not established

All five prespecified blocks, seeds 263000101..105, completed both 360k-step arms at
`9e44adde3d54fcd0363a2ebdbc1468494141c27b`. All native outputs were collected, individually
hashed against the executing node and independently retained. Source/protocol, within-pair
initialization, distinct block model/RNG streams, common physical evaluation panels, all
720k evaluation transitions and optimizer/storage isolation passed the recorded checks.
No block, world, endpoint or seed was removed, replaced or extended. A2 was not pooled.

The unchanged precommitted aggregator used five paired training-block means and
t(.975,4)=2.7764451051977987. Independent arithmetic from the verified native readings
matched all reported intervals. Primary hotspot block values are:

| Block / model seed | M-U native J | M-U served users per step |
| --- | ---: | ---: |
| 0 / 263000101 | -.014721197478491 | +.007937500 |
| 1 / 263000102 | +.019314215066089 | +1.482312500 |
| 2 / 263000103 | -.052880403081985 | -1.752812500 |
| 3 / 263000104 | -.015865239350722 | -1.495437500 |
| 4 / 263000105 | -.064009839064661 | -4.197750000 |

| Family / endpoint | Mean M-U | Sample SD | Fixed marginal two-sided t95 interval |
| --- | ---: | ---: | --- |
| **Hotspot J, primary** | **-.025632492782** | .033353903349 | **[-.067046833771, +.015781848207]** |
| **Hotspot service, primary** | **-1.191150000** | 2.123258803 | **[-3.827524015, +1.445224015]** |
| Uniform J, secondary | -.027514606844 | .033268433539 | [-.068822823046, +.013793609359] |
| Uniform service, secondary | -1.263750000 | 1.466641423 | [-3.084825853, +.557325853] |
| Cluster J, secondary | -.029872854046 | .044625486530 | [-.085282714073, +.025537005981] |
| Cluster service, secondary | -1.472137500 | 2.891450216 | [-5.062347136, +2.118072136] |

Primary J has 1 positive/4 negative blocks, range [-.064009839065, +.019314215066]; service
has 2 positive/3 negative, range [-4.197750, +1.4823125]. Neither lower bound is positive,
so the joint claim is **not established**. Both point estimates are adverse, but both
intervals span zero; neither sign is resolved by this working-model interval. The service
interval also includes +1 user/step: no approximately one-user gain is established or ruled
out. This is not equivalence, a confirmed harmful population effect, or technical failure.
No simultaneous-coverage, next-training, arbitrary-panel or causal-coverage claim is made.

All ten fits improve their own mean J/service in every family. Hotspot mean U45/M45 service
is 25.7744625/24.5833125, versus common-initial 12.5125625; ordinary U remains a competent
reference. Local losses survive positive own means: hotspot adverse J-or-service world counts
are 22/9/31/23/27 by block. M also has one own-J and five own-service loss cases across all
families, preserved in NOTES. Uniform and cluster results, all components, five-block own
learning and every paired world remain secondary readings and cannot replace the primary rule.
A2's positive pair and C01 block 1 remain contrary evidence; training-instance and panel
changes between A2/C01 are not separately attributed.

Actual C01 cost is ten fits, 3.6M train +720k evaluation =4.32M team steps /25.92M UAV action
rows, 450 updates, 1,012,500 calls of each optimizer and 1,440 evaluation episodes. Scientific
wall sums to 6.301630h; admission-to-exit sums to 6.569561h; first-admission to final-exit
elapsed is 7.436870h, including gaps. The five native inventories total 680 files /
5,440,071,755 bytes, with verified local and independent copies. Support/reading and
other-process costs are not claimed to be fully measured.

The fixed batch ends with this result and no sixth block. Later route investment is a
separate decision, not a rescue extension or a revision to this claim. The complete prior
Pro advice's failed-rule branch is reused for this reading.
[Full result, exceptions, costs and next decision](NOTES.md#2026-09-25--c01-complete-joint-positive-mean-not-established);
[unchanged five-block aggregation](../../../../runs/spatial_demand_generalization/c01_five_block_confirmation_20260925/summary.json);
[input hashes and cost provenance](../../../../runs/spatial_demand_generalization/c01_five_block_confirmation_20260925/reading.json).
