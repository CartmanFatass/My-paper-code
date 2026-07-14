# GPT-5.6 Pro correction request: replace the prohibited R35-OCSF route

The first response's R34 audit is accepted, but its proposed R35-OCSF route is
not admissible. This is a correction request, not permission to implement or
run R35-OCSF.

## Accepted from the first response

- R34-BHMD is a valid `FAIL_M1_RETIRE_R34_BHMD` and must not be rerun,
  retuned, expanded, or converted into another reward/classifier target.
- `real > sham` primarily shows damage from wrong label attribution. The
  unchanged source anchor shows that BHMD did not create stronger persistent
  skills.
- The source's high SNR but modest prototype fidelity shows that the registered
  centroid geometry is not equivalent to causal skill quality. The stronger
  continuous/overlapping-manifold explanation is a plausible hypothesis, not
  an established result.
- Skill semantics must be created during learning rather than assigned to
  frozen trajectories afterward.

## Why R35-OCSF is rejected

The proposed objective is:

```text
q_psi(z | phi(o[t:t+W], a[t:t+W]))
R_skill = log q_psi(z | phi(tau)) - log q_psi(z)
R_skill -> low-level PPO/GAE
```

This is exactly a process-level classifier reward for the existing numerical
skill label `z`. Sampling the same old label from the current high policy
rather than a frozen source does not make it a new semantic target. Calling it
"online" also does not change the estimand. It directly violates the original
request's prohibitions against:

- R31 observational effect prediction/reward or another classifier for old
  numerical labels;
- `q_d/q_D`, a new classifier family, or a scorer/reward that merely reweights
  the same old `z` codebook;
- turning another label-recovery score into reward, value target, or critic
  advantage;
- a DIAYN/DADS-style variational label-recovery loop presented as a
  structurally new post-R34 edge.

The proposal also leaves decisive scientific and on-policy defects:

1. The encoder reads actions, while R29 already established natural
   skill-conditioned action information. There is no action-only null, so the
   classifier can recover an instantaneous action signature without stronger
   persistent effects.
2. `P(q(z|tau)=z)` is both the trained classifier target and the proposed M2
   natural-use metric. It is self-referential and cannot establish that frozen
   R30 naturally uses newly controllable processes.
3. `32 x 80` source episodes, `40` low PPO updates, and "same rollout" across
   arms do not define a coherent on-policy data contract. Once intrinsic reward
   changes the actor, the two arms cannot continue using the same realized
   rollout.
4. The timing of the segment reward, rollout truncation, recurrent state,
   discriminator training order, detach boundary, behavior log-probability,
   and bootstrap into low GAE are unspecified.
5. "Control objective OFF" and "q optimizer identical" are ambiguous, and the
   requested unchanged-source anchor is absent.
6. Duration-only and observation-only shortcut probes do not isolate the known
   action-signature shortcut or classifier/reward co-adaptation.

Therefore the controller disposition is:

```text
ACCEPT R34 verdict and reusable negative conclusion
REJECT R35-OCSF as a prohibited retired-family revival
NO IMPLEMENTATION OR COMPUTE AUTHORIZED FOR R35-OCSF
```

## Required corrected decision

Return exactly one corrected post-R34 route. Do not defend, rename, or minimally
modify R35-OCSF. First explicitly acknowledge that supervised recovery of the
existing `z` from a trajectory, and any `log q(z|tau)-log q(z)` reward derived
from it, are outside the allowed search space.

The corrected route must satisfy all of the following:

1. It attacks one upstream object not already closed by R29--R34.
2. It does **not** train any classifier/posterior to recover the existing `z`,
   a clustered replacement label, a team label, or a human/task role label.
3. Its policy reward, advantage, value target, or gradient is not a function of
   label-recovery likelihood, prototype/centroid assignment, the retired
   individual-effect score, a fitted roster score, or action-label decoding.
4. It is not post-hoc clustering plus cloning, direct IFEPG, high-roster
   selection, `q_d/q_D`, a team latent revival, task shaping, or IMOD
   scheduler/hazard/queue machinery.
5. It states whether the discrete `K=4` skill object remains scientifically
   justified. If the evidence instead requires replacing or abandoning that
   object, say so directly; architectural abandonment is preferable to
   relabeling a retired objective.
6. It gives one implementable mathematical objective with exact data or
   intervention semantics, recurrent/tensor flow, gradient recipients, detach
   boundaries, frozen modules, and interaction with R30 KEEP/SET.
7. It follows the promotion ladder instead of jumping directly to intrinsic
   reward-on PPO. The first gate is reward-off heldout evidence plus a causal
   `do(skill)` intervention. Its primary metric is persistent effect under
   shared contexts and independent replicas, not a self-trained classifier;
   natural transport is a separate downstream branch.
8. That gate includes an unchanged-source anchor and one mechanism-matched
   control; real must beat both. Specify exact per-arm on-policy environment
   steps, rollout/minibatch/epoch/optimizer-call counts, CRN/randomization,
   source/policy-version boundary, metrics, bootstrap unit, material
   thresholds, M0 checks, and mutually exclusive outcome branches.
9. There is no UNDERPOWERED, retuning, threshold-revision, encoder-swap, reward
   scale/window sweep, or automatic seed-expansion branch.
10. The mechanism remains outside normal training until the gate passes.

If no scientifically justified route remains under these constraints, the
decisive answer may be to abandon the current discrete-skill reconstruction
program and name exactly one replacement architectural object plus its smallest
falsification gate. Do not fill the gap with a prohibited classifier reward.

## Requested answer structure

1. `CORRECTION ACCEPTED` or one concrete reason the rejection above is wrong.
2. Exact disposition of R35-OCSF.
3. One remaining causal bottleneck after R29--R34.
4. One corrected R35 algorithm, with equations and implementation semantics.
5. One exact source-anchored abandonment gate and its only next action for each
   result branch.
6. Claims the gate would and would not support.

Return one route only.

## Repository files to inspect

- `docs/external-review/gpt5_6_pro/20260715_r34_bhmd_gate_result/GPT5_6_PRO_QUESTION.md`
- `docs/external-review/gpt5_6_pro/20260715_r34_bhmd_gate_result/RESPONSE_RAW.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/CURRENT_WORK.md`
- `memory/LTM/R29_R33_EFFECT_COMPOSITION_FAILURE_REVIEW_20260714.md`
- `memory/ExpRecord.md`

Read the original prohibitions and the complete R29--R34 failure matrix before
answering.
