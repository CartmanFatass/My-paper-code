# GPT-5.6 Pro Review Request: R34-BHMD Valid Failure and One R35 Route

Please inspect the implementation and the tracked result JSON before answering.
We need a validity audit of the registered R34 failure and exactly one
structurally different R35 causal edge. Do not provide a menu, revive a retired
line, or rescue R34 by retuning it.

## Current decision

The controller's current decision is:

```text
R34-BHMD = VALID SCIENTIFIC FAIL
registered branch = FAIL_M1_RETIRE_R34_BHMD
```

Every registered M0 implementation check passed. R34 strongly outperformed its
label-attribution sham, but it did not clear the unchanged frozen-source anchor:
it produced only a small fidelity increase, reduced persistent forced-mode SNR,
and did not produce material frozen-selector use or exploration transport.

Subject to your audit, permanently retire the fixed R34 balanced-hindsight-mode
distillation family. A claimed implementation invalidity must identify one
concrete defect that changes the registered data distribution, clustering,
recurrent likelihood, gradient, intervention, bootstrap, or result.

## How the two R33 responses were dispositioned

The two archived R33 responses are two manual submissions to the same
GPT-5.6 Pro model. Their agreement is a repeated sample from one model, not two
independent pieces of scientific evidence.

We accepted from both responses:

- R33-IRSC is a valid scientific failure and direct intervention-scored
  role-swap roster selection is permanently retired;
- the next test should change codebook construction rather than add another
  scorer for the old numerical skills;
- balanced post-hoc trajectory modes followed by recurrent behavior
  distillation is structurally different enough to receive one abandonment
  gate;
- the high R30 KEEP/SET controller must remain frozen during that gate.

We accepted response B's full-episode recurrent replay and rejected response
A's stored block-start hidden-state replay. Once `actor_rnn` changes, a source
RNN hidden state is stale. The implemented loss therefore replays each complete
80-step focal episode from zero hidden state, and heldout forced blocks
recompute the modified actor's prefix hidden from episode start.

The controller also made the following required modifications before launch:

1. Added an unchanged `frozen_source` no-update arm. `real > sham` alone can be
   caused by sham damage and is not evidence of codebook creation.
2. Defined each mode from the focal agent's normalized ten-step displacement
   sequence only. Teammate motion cannot be a label target controlled by one
   focal skill.
3. Used a deterministic per-agent maximum-Hamming, no-self permutation of
   complete eight-block label sequences for the sham, preserving the label
   sequence multiset while disrupting trajectory-to-label attribution.
4. Fit normalization, balanced clusters, prototypes, and the Hungarian
   prototype-to-old-skill naming permutation on the train split only.
5. Split the downstream claims: M1 is causal codebook formation; M2a is
   zero-shot natural use by the frozen old R30 selector; M2b is natural coverage
   transport. A downstream miss cannot erase a genuine M1 pass.
6. Shared intervention and natural-run random streams across source, real, and
   sham, and bootstrapped by source episode or paired natural reset.
7. Froze the high R30 parameters and fixed check clock. Realized KEEP/SET paths
   were allowed to diverge because the modified low actor can change visited
   states; they were not described as realized-schedule matched.

Please audit both the accepted BHMD idea and these controller corrections. Do
not treat the original two responses as authority over the tracked
implementation or registered contract.

## Registered R34 mechanism

The causal edge was:

```text
unlabeled focal natural trajectory blocks
-> exact-balanced hindsight displacement modes
-> full recurrent low-policy sequence distillation
-> forced reproduction of the assigned modes
-> zero-shot use by the frozen R30 selector
-> broader natural joint-state exploration
```

The source is the frozen adaptive-R30 Alice--Bob policy used by R32/R33. With
seed `34031`, it collected 32 stochastic 80-step episodes: 24 train and eight
heldout. The 384 train block-agent rows each contributed a focal-only
ten-position displacement sequence, flattened to shape `[20]`. Train-only
standardization was frozen, and exact-balanced `K=4` clustering assigned 96
rows to each mode. A train-only Hungarian permutation named those modes with
the four existing skill IDs; overlap and NMI with old `z` were diagnostic only.

The three arms were:

- `frozen_source`: no parameter update;
- `real_modes`: distill the true hindsight mode sequence;
- `episode_sequence_sham`: distill the maximum-Hamming deranged label sequence.

Real and sham each replayed all 48 train agent-episodes from zero actor hidden
state for ten epochs, batch size eight, exactly 60 Adam calls, `lr=3e-4`, and
gradient clip `0.5`. The objective was detached-action recurrent behavior NLL
conditioned on the assigned skill sequence. Gradient was restricted to:

```text
low.actor_film
low.actor_rnn
low.actor_act.action_out.fc_mean
```

Actor base, action log standard deviation, low critic, complete R30 high
policy/value, OPT/bridge, classifiers/posteriors, reward, GAE, and normal PPO
were frozen and outside the objective.

The heldout intervention used 64 block contexts x two focal agents x four
forced skills x two independent replicas x ten steps = 10,240 primitive steps
per arm. The three arms shared branch seeds; skills used common random numbers
within a context and replica. Natural transport used 64 paired stochastic
80-step episodes per arm. Total exposure was 48,640 environment steps. The
single result source is:

`logs/r34_bhmd_gate_20260715_001706/result/r34_bhmd_gate.json`

## Result

### M0 implementation validity: PASS

All registered validity checks passed, including exact data/branch counts,
train-only fitting, 96 rows per mode, bijective alignment, no-self sham,
matched cross-arm random streams, 60 finite optimizer calls in each trained
arm, nonzero allowed gradients, and zero forbidden gradient/drift. Source
recurrent action-log-probability replay maximum error was
`2.86102294921875e-06`, below the `1e-5` limit. Real/sham label agreement after
the maximum-Hamming derangement was `0.0208333`, so the comparator was not a
degenerate near-identity mapping.

Train-only hindsight modes were not merely the original labels: cluster/old-z
agreement was `0.505208` and normalized mutual information was `0.197420`.
These are diagnostic and not PASS criteria.

### M1 causal codebook formation: FAIL

Forced nearest-prototype fidelity was:

```text
source = 0.509765625
real   = 0.5751953125
sham   = 0.18359375
```

The real per-skill fidelities were:

```text
[0.5234375, 0.4765625, 0.671875, 0.62890625]
```

Real minus sham was large and precise:

```text
gain = 0.3916015625
95% CI = [0.361328125, 0.427734375]
```

But the unchanged-source comparisons failed the registered material gate:

```text
real absolute fidelity = 0.5751953125   required >= 0.60
real - source          = 0.0654296875   required >= 0.15
95% CI                 = [0.0478515625, 0.083984375]
```

Persistent forced-mode SNR was:

```text
source = 1.7607920418
real   = 1.5234849113
sham   = 0.1591238171
```

Real again strongly exceeded sham:

```text
median real - sham = 1.3726406937
95% CI             = [1.2175149246, 1.6233763529]
```

However, real was materially worse than the unchanged source:

```text
median real - source = -0.2962394510
95% CI               = [-0.3518367184, -0.2165278425]
registered requirement = >= 0.20 with CI lower > 0
```

This triggers the registered `FAIL_M1_RETIRE_R34_BHMD` branch. The source
anchor changes the interpretation of the impressive real-versus-sham gaps:
they primarily show that a wrong hindsight-label attribution damages behavior,
not that correct BHMD creates stronger persistent modes than the source.

### M2a frozen-selector natural use: FAIL

Natural old-skill/nearest-prototype agreement was:

```text
source = 0.505859375
real   = 0.5546875
sham   = 0.185546875
```

Real minus source was only `0.048828125`, with 95% CI
`[0.025390625, 0.0732421875]`, below the registered `0.10` material threshold.
This is downstream context only because M1 already failed.

### M2b natural exploration transport: FAIL

Joint-position union cells were:

```text
source = 396
real   = 403
sham   = 297
```

Although `real/sham = 1.356902`, `real/source = 1.017677`, below the registered
`1.05`. The paired-reset real-minus-source coverage-gain 95% CI was
`[-0.003000, -0.000275]`, so the extra union cells did not represent a reliable
per-reset exploration improvement over source.

### M3 R30 safety: PASS

The real arm retained nondegenerate skill supply and lifetime behavior:

```text
full-sync SET rate             = 0.142857
SET-skill entropy / log(4)     = 0.993546
minimum SET-skill share        = 0.194842
long/short lifetime min share  = 0.103261
```

The failure is not an R30 lifetime, synchronized-refresh, or skill-supply
collapse.

## Frozen interpretation

The strongest supported causal conclusion is:

```text
balanced post-hoc focal trajectory labels
-> full recurrent behavior cloning under those labels
-> strong preservation relative to a destructive attribution sham
-/-> material forced-mode strengthening over the unchanged source
-/-> stronger persistent separation over the unchanged source
-/-> material zero-shot frozen-selector use or natural coverage transport
```

The source already had nontrivial forced displacement separation
(`SNR=1.760792`) despite imperfect nearest-prototype fidelity. BHMD made the
actor more consistent with its mined labels but reduced this persistent SNR.
Please explain what this combination implies about the geometry or temporal
structure of the existing behavior modes. Do not assume that higher
nearest-centroid fidelity and higher causal skill quality are equivalent.

If M0 is valid, permanently retire fixed balanced hindsight mode distillation,
including variants that change only `K`, displacement descriptor, clustering,
prototype naming, epochs, learning rate, recurrent/FiLM scope, window, seed, or
threshold. Do not turn the same labels into a reward, critic target, classifier,
or longer normal-training run.

This result does not prove that all possible codebook construction is
impossible, that every continuous behavior manifold is absent, or that every
form of team complementarity is absent. Any R35 proposal must nevertheless be
structurally different from the failed edge and earn its own abandonment gate.

## Retired and prohibited routes

Do not select or reintroduce any of the following as R35:

- R29 action-density/action-information reward or a variant changing only its
  prior, window, aggregation, scale, normalization, or clip;
- R31 observational effect prediction/reward or another classifier for old
  numerical labels;
- R32 direct individual-effect policy gradient, whether expressed as a reward,
  value target, critic advantage, wider parameter scope, or retuned estimator;
- R33 direct intervention-scored roster selection, pair scorer, team reward,
  `q_D`, sampled/deterministic team latent, or longer high-head fitting;
- R34 post-hoc balanced clustering plus behavior cloning, including different
  `K`, descriptor, clustering method, recurrent scope, label mapping, or
  optimization budget;
- a scorer/reward that merely reweights or relabels the same old `z` codebook;
- scheduler, queue, hazard, service priority, atomic commit, mixed-age access,
  teacher mixture, or other IMOD execution mechanics presented as the learning
  contribution;
- completion-value `J`, value-of-revision/request-value, value-ranked
  candidates, the ROSTER production controller, or already-retired pruning
  paths;
- task-specific reward shaping, button/target/contact labels, human-assigned
  roles, or an automatic seed/threshold/tuning rescue.

IMOD may constrain execution semantics, but it is not scientific evidence for
HMASD and no IMOD code or parameter should be migrated in this decision.

## Requested decision

1. Audit whether the registered R34 data split, balanced clustering, recurrent
   replay, sham, source anchor, forced evaluation, bootstrap, parameter scope,
   and M0 evidence make `FAIL_M1_RETIRE_R34_BHMD` a valid scientific failure.
   Identify a concrete estimand-changing implementation defect if and only if
   you reject validity.
2. If valid, state the reusable causal conclusion and explicitly retire R34
   without rerun, retuning, threshold revision, or seed expansion.
3. Reconcile the source's high forced persistent SNR (`1.760792`) with its
   modest prototype fidelity (`0.509766`) and R34's higher fidelity but lower
   SNR. State what this rules in or out for the next mechanism.
4. Select **exactly one** structurally different R35 causal edge. It must attack
   a remaining upstream bottleneck rather than add another objective for the
   old labels, another codebook clustering/distillation variant, another
   roster selector, or asynchronous scheduling mechanics.
5. Specify one implementable R35 algorithm in full: mathematical
   objective/estimator, data or intervention semantics, tensor and recurrent
   state flow, policy inputs, gradient recipients, detach boundaries, frozen
   modules, and exact interaction with the R30 fixed-clock KEEP/SET controller.
6. Give the smallest Alice--Bob abandonment gate with one mechanism-matched
   comparator and an unchanged-source anchor. Specify the exact environment and
   optimizer budgets, randomization/CRN, metrics and material thresholds, M0
   validity rules, and mutually exclusive PASS/FAIL branches. There must be no
   UNDERPOWERED, retuning, threshold-revision, or automatic seed-expansion
   branch.
7. Keep the proposed mechanism outside normal training until that gate passes.
   Do not claim task efficacy, cooperation, HMASD parity, sparse-exploration
   success, or S7 transfer from an Alice--Bob mechanism gate.

Return one decisive route, not a ranked list or parallel program.

## Repository files to inspect

- `docs/external-review/gpt5_6_pro/20260714_r33_irsc_gate_result/RESPONSE_RAW_A.md`
- `docs/external-review/gpt5_6_pro/20260714_r33_irsc_gate_result/RESPONSE_RAW_B.md`
- `docs/external-review/gpt5_6_pro/20260714_r33_irsc_gate_result/DISPOSITION.md`
- `ha_ctse_process/r34_balanced_hindsight_mode_distillation.py`
- `scripts/r34_bhmd_gate.py`
- `logs/r34_bhmd_gate_20260715_001706/result/r34_bhmd_gate.json`
- `memory/ExpRecord.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/LTM/R29_R33_EFFECT_COMPOSITION_FAILURE_REVIEW_20260714.md`

Read the raw responses, controller disposition, exact implementation, and
single result JSON. Then return one audited scientific verdict, one reusable
causal lesson, and one complete falsifiable R35 abandonment gate.
