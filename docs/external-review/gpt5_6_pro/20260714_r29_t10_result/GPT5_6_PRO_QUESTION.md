# HMASD R29-T10 Result Review and Next-Route Decision

You previously reviewed pointwise R29 and recommended R29-T10: fixed-candidate
recurrent replay over each complete natural skill lifetime, a uniform four-code
mixture, final-10-action block likelihood, detached coefficient 0.05, clip 0.05,
and one low-level endpoint reward.

Implementation note: the actual-skill raw likelihood is reconstructed from
PPO's stored old-policy squashed log likelihood by restoring the common tanh
Jacobian. Other candidates use full recurrent replay. This avoids measured CUDA
GRU batch-shape drift (`1e-3` scale), which is reported separately rather than
being absorbed into the source likelihood.

We implemented that exact core change and ran the user-authorized preliminary
pair from the same R25 arm0 1M checkpoint: `probe_only` versus `real_reward`,
seed 29031, 16 environments per arm, CUDA, 40 rollout/PPO updates, 320K
additional environment steps per arm, and 15 low PPO epochs. Both arms compute
the same scorer; only the real arm receives its reward. Final natural-process
evidence uses the unchanged R26 64-reset analyzer, and task safety uses 20
deterministic episodes.

The machine summary classified the pair as **PRELIMINARY_FAIL**. Important numbers:

- late R29-T10 real-minus-probe mean `0.031265`, paired-update
  95% interval `[-0.005331, 0.064452]`;
- per-skill late differences `{"0": 0.0407883484354832, "1": 0.08656550445281996, "2": 0.0297151450966745, "3": -0.025269767229889873}`;
- R26 probe/real statuses `PASS` / `MIXED`;
- R26 full-minus-prior real-minus-probe gain `-0.058112`;
- real late skill entropy `0.996980`;
- real maximum reward/env ratio `0.044672`;
- task reward relative degradation `0.315623` and
  zero-throughput step-fraction worsening `0.095300`;
- likelihood parity maximum probe/real
  `0.000e+00` /
  `0.000e+00`;
- unanchored recurrent-source numerical drift maximum probe/real
  `7.246e-03` /
  `7.069e-03`;
- late symmetric KL mean/variance components in the real arm
  `0.432676` /
  `0.000000`.

Read the raw JSON/CSV/R26 reports and code listed in `REVIEW_ENTRY.md` at the
same Git commit before deciding. The single seed and late-update bootstrap are
explicitly not enough for a final efficacy claim. Choose exactly one next
route:

1. **PROMOTE** the unchanged pair to the remaining preregistered seeds 29032 and
   29033;
2. **MODIFY ONCE**, naming one causal defect, one minimal algorithm change, and
   one falsifiable comparator; or
3. **RETIRE** the R29 density-ratio reward family and state the negative
   constraint it establishes.

Also state which conclusions remain prohibited and whether the observed
mean-versus-variance KL split changes your mechanism diagnosis. Do not propose a
coefficient sweep, threshold relaxation, new semantic classifier reward, or
task-specific intrinsic reward.
