# R19 Team-Transition Residual Heads — FINAL Implementation Plan (for Codex)

Author: CC (Claude, cross-validation) — consolidates the Gemini v2 plan, the
six CC amendments, the three approval fold-ins, and the three completion
notes into one self-sufficient reference. Supersedes the v2 ledger entry as
the implementation source of truth; where any prior document differs, THIS
plan wins.
Date: 2026-07-04
Source contracts: `memory/cross_validation.md` Round 19 (R19.0-R19.4),
Round 18 (R18.3 task matrix), R15 derivation doc §5 (team term).
Implementer: Codex (exclusive writer of training code, per the
implementation-authority rule in ATTENTION_POINTER).

## Purpose

Implement the team engine: DADS-style situation-transition residual
`log q(kappa'|kappa, xi) - log q(kappa'|kappa)`, the structural replacement
for HMASD's team discriminator reward that the vacuity lemma killed. Runs as
the `a2_plus_t` arm. Restores dual-engine intrinsic pressure: individual =
role diversity (A2), team = situation steering INCLUDING stabilization
(this plan).

## Non-goals

- No changes to the A2 path, roster mode, hazard/guard code, or legacy
  process/topology/transition reward paths.
- No commitment layer (kappa*), no coverage bonus — later stages.
- No communication/backhaul/coverage fields anywhere (inputs are kappa and
  skill counts only, enforced by unit test).
- Never low-level injection (see §Injection — correctness-critical).

## Current-code facts to respect

1. kappa is per-env from `situation_substrate.py::assign_kappa_from_omega`,
   argmax over omega -> classes {0..N-1} with `missing_kappa = -1` possible.
   N = opt_num_prototypes = 4 (PINNED; substrate gate validity).
2. High-level decisions are SEGMENTS (skill lifetimes spanning multiple
   check intervals); kappa transitions occur per CHECK INTERVAL. The reward
   therefore accumulates per-interval residuals into segment returns
   (see §Injection).
3. `update_high_from_segments(segments, process_rewards, ...)` already
   accepts a per-segment reward array — the tested injection pathway.
   Legacy process-reward fields must REMAIN 0 in this arm; the team
   contribution gets its own fields.
4. Active skills per (env, agent) are tracked in `self.active_skills`;
   xi is computable at every check from it.
5. Do not import anything from the retired `process_posterior.py` path.

## Module: `ha_ctse_process/situation_transition.py` (NEW, clean)

```text
class SituationTransitionPredictor(nn.Module):
    __init__(num_situations, n_skills, hidden_dim=128)
      kappa_embedding: Embedding(num_situations, hidden_dim)
      prior_head:      MLP(kappa_emb -> num_situations logits)
      posterior_head:  MLP([kappa_emb, xi] -> num_situations logits)

    losses(kappa, xi, kappa_next) -> dict
      # ALL inputs .detach()ed / constructed from data, never from live graph
      CE(posterior) and CE(prior) on kappa_next targets
      per-sample log_q, log_p; mi = log_q - log_p
      split: mi_on_self (kappa_next == kappa), mi_on_change (else)

    reward(kappa, xi, kappa_next, coef, clip) -> per-interval scalar array
      # computed strictly under torch.no_grad()
      r_tau = coef * clamp(log_q - log_p, -clip, +clip)
```

Contract points:
- xi_tau = permutation-invariant ACTIVE-SKILL COUNT VECTOR, n_skills dims,
  raw counts (float), over all agents during interval tau. Ages are a later
  optional ablation, NOT the default encoding.
- Targets: per check interval tau, inputs (kappa_tau, xi_tau), target
  kappa_{tau+1}. ALL intervals count, INCLUDING self-transitions
  (kappa_{tau+1} == kappa_tau) — stabilization must pay (R19.2).
- missing kappa (-1): DROP intervals where kappa_tau or kappa_{tau+1} is
  missing; log `team_transition_missing_frac`. Do not map missing to a class.
- On-policy: heads train on the CURRENT rollout's closed intervals only;
  the final unclosed interval of each env is dropped at the PPO boundary.
- Optimizer: OWN Adam at `team_transition_lr`. Head parameters never enter
  the high-level policy optimizer. CE trains only the heads; the reward
  trains only the policy (g-revival precision rule).

## Config (`config.py`, all default-off/inert)

```text
enable_team_transition_probe = False    # train heads + metrics, NO injection
enable_team_transition_reward = False   # requires probe flag on
team_transition_coef = 0.05             # smallest-first (R19.4); a2_plus_t pinned
team_transition_clip = 2.0              # applied AT injection, before coef? NO:
                                        # r = coef * clip(residual, +-2.0)
team_transition_warmup_steps = 20000    # gates REWARD only; probe trains from 0
team_transition_lr = 5e-4
team_transition_hidden_dim = 128
```

CLI in `train.py`: `--enable_team_transition_probe`,
`--enable_team_transition_reward`, `--team_transition_coef/clip/warmup_steps`.
Manifest + start-line entries per convention.

## Injection (CORRECTNESS-CRITICAL)

```text
LEVEL: HIGH-LEVEL ONLY. Per-interval clipped residuals are accumulated over
each segment's constituent check intervals and added to that segment's
return via the existing per-segment reward pathway (alongside env return).
The residual NEVER enters the low-level per-step reward — the P1
signed-low-only lesson. Gated by: probe flag AND reward flag AND
total_steps >= warmup.
Legacy process-reward guard fields stay 0.0; team contribution is logged
separately (fields below) so reward-purity audits still work per-channel.
```

## Rollout data collection

During rollout, per env per check interval: record (kappa_tau, xi_tau) and
close with kappa_{tau+1} at the next check. Attribute each closed interval
to the enclosing segments per agent for reward accumulation. Buffers cleared
at the update boundary (on-policy contract).

## Metrics (CSV via UPDATE_FIELDS + TensorBoard TeamTransition/* + console)

```text
team_transition_active, team_transition_samples
team_transition_loss (posterior CE), team_transition_prior_loss
team_transition_mi_mean, team_transition_mi_on_self, team_transition_mi_on_change
team_transition_self_frac          # expect high given dwell ~8; verifies R19.2 regime
team_transition_missing_frac
team_transition_reward_high_mean
team_transition_reward_applied_steps   # assertable 0 when reward flag off/warmup
team_transition_reward_env_ratio       # |team reward| / |env return|, P4-1b lesson
team_transition_reward_renewal_corr    # Pearson across envs within the update:
                                       # per-env summed team reward vs per-env
                                       # renewal count. CHURN PRECURSOR (R19.3);
                                       # informational now, MANDATORY gate input
                                       # before Stage-2 hazard goes live.
```

## Experiment pre-registration (create ExpRecord entry BEFORE launch)

`EXP-2026070X-a2-plus-t`, local CUDA, settings identical to A2
(16 env, 320k, S7-S1, seed 1 then 2). ONE variable vs A2.

```text
TRIGGER: the A2 outcome-matrix OUT-OF-GAS branch fires, OR user decision
  after the A2 320k read. Do NOT launch before A2 completes.
ARM: a2_plus_t = A2 config + enable_team_transition_probe
  + enable_team_transition_reward (coef 0.05, clip 2.0, warmup 20k).
PROBE-FIRST OPTION: if A2's read is ambiguous, a probe-only arm
  (heads on, reward off) may run first to verify mi_mean > 0 exists to
  inject; pre-register it as a2_plus_t_probe if used.

GATES (a2_plus_t vs A2, matched steps, last-third means + 320k eval):
  mechanism: team_transition_mi_mean > 0 sustained; self_frac consistent
    with dwell (0.6-0.95); reward_env_ratio in [0.05, 0.5] post-warmup.
  task: coverage and zero_throughput_ep_frac improve vs A2 (this arm exists
    to fix the exploration deficit — neutrality is NOT a pass);
    reward_std/mean not worse than 1.15x A2.
RUNTIME KILLS:
  reward_env_ratio > 1.0 for 5 consecutive post-warmup updates;
  160k eval zero_throughput_ep_frac > A2 + 0.15.
STOP RULE:
  if a2_plus_t fails the task gate on 2 seeds while mechanism metrics are
  healthy, the exploration deficit is not situation-steering-shaped;
  do NOT sweep coef — escalate to the R18.3 matrix read (S7-S1 may require
  kappa*-style atomic commitment even in the coverage-bound corner, or the
  substrate's kappa classes are too coarse at N=4).
CHURN PRECURSOR: team_transition_reward_renewal_corr is logged and reported
  but NOT a gate in this arm (no live hazard); it becomes a hard input to
  the Stage-2 go decision.
```

## Validation checklist (project convention)

```text
py_compile / AST parse on all touched files
unit tests (new file tests/r19_team_transition_test.py):
  - input boundary: heads consume kappa + skill counts ONLY
  - gradient separation BOTH directions (head step leaves policy params
    unchanged; policy step leaves head params unchanged)
  - reward guard: applied_steps == 0 when reward flag off OR warmup unmet
  - clip applied before coef scaling
  - missing-kappa intervals dropped, missing_frac logged
  - self/change split partitions correctly
  - unclosed final interval dropped at boundary
smoke: probe-on run with reward guards zero; CSV fields present
tiny train: reward-on with warmup=0; checkpoint save/load/resume with the
  new module (own optimizer state included in checkpoint)
runner: a2_plus_t arm added to scripts/run_r15_stage1_local_cuda.ps1
  (or sibling), -DryRun passes, timestamped log dirs
memory sync per LongTaskMemo after implementation
```

## Fidelity notes

- The probe-mode heads are observers: this channel is "decorative until
  a2_plus_t reward-on" BY DESIGN and labeled as such (channel-pressure rule
  satisfied via explicit labeling, not via emergence expectations).
- Never add a head predicting kappa from s (vacuity — trivially perfect,
  dead reward).
- If any ambiguity arises during implementation, the resolution order is:
  this plan -> Round 19 ledger -> R15 derivation doc §5 -> ask, do not guess.
