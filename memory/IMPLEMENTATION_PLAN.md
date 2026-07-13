# HA-CTSE Implementation Plan

This plan is based on inspecting the live repo on 2026-06-23.

## Corrected Research Target

The active objective is S7-S1 parity with HMASD.  The previous "100M steps"
wording should be read as a mistake; for the current stage, `1e6` environment
steps is the more normal long-run budget scale.

S7-S1 is relatively simple and HMASD can nearly solve it.  Therefore HA-CTSE
should first reach HMASD-level behavior on S7-S1 before spending the main effort
on S7-S3.  S7-S1 remains a real performance gate, not only a smoke test.
The clarified parity target is sustained near-100% communication coverage over
a relatively long evaluation window, with low failed/zero-service episode
fraction and stable service metrics.  This is an evaluation gate, not a license
to make communication fields the algorithm's intrinsic reward.
Concrete readout: at least half of evaluation primitive steps should have
`coverage == 1.0`, alongside low zero-service/failure fraction and acceptable
variance.

S7-S3 is temporarily deferred.  It remains the later benchmark where HMASD
performs poorly and the HA-CTSE hypothesis should become more valuable:

```text
per-agent high-level skill lifetimes should be decoupled because different UAVs
and roles naturally need different temporal commitments in difficult topology
and service conditions.
```

Planning consequence:

- P1/P2/P2-lite are not the final scientific claim. They are credit-assignment
  repairs needed to make the asynchronous lifetime design competitive.
- The implementation goal is: decouple each agent's high-level skill
  cycle/lifetime, then reconstruct HMASD's useful sparse-reward machinery under
  that asynchronous structure.  Specifically track and preserve four HMASD
  functions: recurrent low-level discoverer capacity, skill/role semantic
  pressure, entropy/exploration pressure, and dense cooperative credit
  assignment.
- HA-CTSE is a general MARL algorithm.  Backhaul/recovery metrics are diagnostic
  probes for cooperation and sparse-reward credit assignment in Scenario 7, not
  the target to optimize directly.  Do not accept a change merely because it
  raises backhaul metrics if reward, QoS, throughput, coverage, variance, or
  skill-lifetime behavior do not improve.
- P3/P4 intrinsic reward must avoid raw communication-specific indicators and
  must not simply reuse environment reward as an "intrinsic" signal.  Use
  benchmark communication metrics to evaluate whether cooperation emerged.  The
  environment reward remains the external task return, especially in high-level
  skill-lifetime cumulative targets; discoverer/discriminator-style intrinsic
  pressure should be a separate skill-semantics signal.
- Do not skip S7-S1 parity.  A mechanism that cannot approach HMASD on this
  simpler scene is unlikely to be useful for the harder S7-S3 setting.
- Mainline near-term runs should compare HMASD and HA-CTSE on S7-S1 with matched
  scenario settings, matched network scale, and comparable `~1e6`-step budgets.
- Required ablations for the claim: variable per-agent lifetime HA-CTSE,
  fixed/shared lifetime HA-CTSE, and HMASD.  Mechanism diagnostics should report
  duration/lifetime distribution, switch rate, agent-wise lifetime usage,
  backhaul connectivity, recovery, and service metrics.  Run this first on
  S7-S1; transfer the same matrix to S7-S3 later.

Current correction: do not let the plan collapse into duration-set tuning.  A
variable-lifetime policy class can represent fixed lifetime as a special case,
so the important question is not whether a hand-picked variable set beats one
hand-picked fixed duration in a short run.  The important question is whether
HA-CTSE can reconstruct HMASD's skill-discovery, skill-differentiation, and
actually-work intrinsic drive under asynchronous skill lifetimes.

## Round 28 Action-Process Target And Future G1 Reward

Status (2026-07-13): G0 is complete and accepted as `PASS_TARGET_NULLS`.
Cloud run `logs/r28_g0_action_process_target_20260713_175600` validated the
frozen final scorer; final and update30 passed, while update25 failed only the
train-test-gap guard. The scorer may not be refit, retuned, or swept.

The focused G1 implementation review is complete and recorded in Section 6.1
of `docs/research/R28_G1_CAUSAL_SKILL_FORCING_REWARD_DESIGN_20260713.md`. Its
recommended freeze is pending user acceptance. No R28-G1 reward code, topology
execution, or training launch is authorized by the G0 result or this review.

Active causal edge:

```text
distinct z_i -> naturally expressed, behaviorally differentiated skills
```

R27 proves that the frozen executor has persistent forced capacity through H40,
while R26 remains negative on natural windows. R28 therefore tests a
task-generic ten-step deterministic-action process target against
capacity-matched context, pre-intervention, and sham-label diagnostic nulls.
Gate-C observation/communication effects, environment reward, `q_A`, and the
blocked old `q_d/q_D` line are excluded from the target.

The review found the old P3-4 forcing implementation unusable for G1 because it
fits same-rollout heads from sampled actions/effect fields. The recommended
implementation instead uses a separate frozen scorer, exact recurrent
deterministic-action capture, an episode-step phase clock, common real-label
support for all arms, label-marginal-preserving per-update sham derangement,
terminal-ten-step low-only attribution, and explicit OOD/reward-ratio guards.
It also forces the inherited R25 prototype-discriminator reward and every other
non-R28 policy reward path off after checkpoint metadata is restored.

If the review freeze is accepted, the next permitted action is implementation
and focused synthetic/dry-run verification only. A later level-3 launch still
requires a separate user approval and a successful minimum-three-worker CUDA
topology check. The planned arms remain probe-only, sham reward, and real
reward; standing R25/HMASD references are not rerun.

Core MARL impact at this boundary: documentation/review only. Reward,
actor/critic/FiLM/GRU, optimizer/loss/GAE/PPO, collector semantics, environment
dynamics, credit assignment, team intent, and latent-lifetime semantics are
unchanged in the live code.

## Round 27 G2 Forced-z Trajectory/Effect Intervention (completed and accepted)

Status (2026-07-13): **completed**, controller classification
`PASS_BEHAVIOR_EFFECT` accepted. The optimized cloud run
`r27_g2_overnight_20260713_095408` at commit `6c06cde` ended successfully at
16:04:38 +08:00. All 192 registered reset artifacts parsed, all were `OK`, and
the aggregate report validated as `valid=true` / `scientific_status=PASS`.

At each of update25, update30, and final, the analyzer classified
`PERSISTENT_BEHAVIOR_AND_EFFECT`; Gates A, B1, B2, B3, and C all passed. Across
the three checkpoints:

- immediate SKL was 0.04166-0.04740 and standardized mean distance
  0.2701-0.2884, with positive reset-cluster lower bounds;
- late-window SKL was 0.03631-0.04122, deterministic-action distance
  0.5938-0.6875, and hold persistence rho 0.9670-0.9821;
- hold distance was 0.6174-0.7878, hold-minus-pulse lower bound
  0.4644-0.5931, and hold/pulse ratio 4.70-4.95;
- held-out four-label accuracy/macro-F1 was 0.9583-0.9757, with accuracy lower
  bound 0.9132-0.9444 and fake-label accuracy 0.21875-0.22917;
- the separate local-effect hold-minus-pulse lower bound was 0.05504-0.06436
  and ratio 2.81-3.08.

Accepted interpretation: the frozen R25 arm0 low actor supports persistent,
label-conditioned action processes and a separate local effect when the focal
label is forcibly held through the native H40 horizon. Beside R26's natural
observational negative, this is
`FORCED_CAUSAL_CAPACITY_WITH_OBSERVATIONAL_NEGATIVE`.

Not established: natural high-level skill selection or duration, reward
usefulness, cooperation, credit assignment, team complementarity, asynchronous
semi-Markov validity, task improvement, long-run verification, or HMASD parity.
Gate C remains evaluation-only and cannot become intrinsic reward.

The stopped `085445`/commit `5595eee` run's 11 partial shards and the
quarantined pilot are excluded. The accepted decision used exactly 64 reset
groups for each of three checkpoints and 2,124,000 environment steps, with no
policy optimization. Full protocol, thresholds, and status paths remain in
`docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md` and
`memory/LTM/EXPERIMENT_ARCHIVE.md`.

## Round 27 G1 Low-Actor Capacity Autopsy (completed and accepted)

Status (2026-07-12): **completed**, classification `STATIC_USED_OBSERVATIONAL_MISS`
accepted with a strict qualification. The trained strict-HMASD MAPPO low actor has
non-decorative *immediate* `z_i`-conditioned action-distribution separation
(zero-hidden and rollout-hidden static capacity PASS 3/3 arm0 checkpoints;
synthetic active/sham PASS 3/3 seeds). Weak static FiLM capacity, recurrent
washout, `INVALID`, and `UNDERPOWERED` are ruled out.

**Not** verified: persistent executable trajectory modes, distinct downstream
effects, team complementarity, credit assignment, reward usefulness, task
improvement. Synthetic accuracy `1.0` is a disposable architecture-capacity
control, not evidence the source policy learned skill semantics. The open edge
remains `individual skill z_i -> persistent executable behavior`.

The audit was reward-off and frozen: no actor, policy/critic architecture, PPO,
optimizer/loss/advantage, collector success-path, environment-dynamics, source
checkpoint, or reward-path change. Actor/GRU/FiLM redesign, hidden-state reset,
and any intrinsic reward remain prohibited while the persistence gate is open.
No `ALGORITHM_PRINCIPLES.md` change is required at this boundary.

Artifacts: `dist/r27_g1_capacity_autopsy_cloud64_20260712_151313_extracted/`;
`logs/r27_g1_result_read_20260712/reports/{result_gate_read,expmanager_intake}.md`;
design/plan under `docs/superpowers/{specs,plans}/2026-07-1{1,2}-r27-g1-*`.
Implementation/review receipts and the full gate tables: `memory/LTM/EXPERIMENT_ARCHIVE.md`
and `memory/LTM/IMPLEMENTATION_PLAN_ARCHIVE_20260713.md`.

Known unrelated debt: the legacy standalone eval fixture omits `args.log_dir`
(`3 passed, 1 failed` in that bounded subset). R27 did not touch it.

## Round 26 G1a Individual-Skill Behavior Screening (completed precursor gate)

Status (2026-07-12): reward-off six-checkpoint screen run and read. The primary
arm0 family **FAILED** — no arm0 checkpoint (update25/update30/final) passed the
pre-registered held-out behavior gate. Arm2 is contextual contrast only and
cannot rescue arm0.

Disposition: the failed observational screen stands **narrowly**, for its tested
behavior windows. After R27-G1 it may **not** be read as evidence that the actor
lacks immediate `z_i`-conditioned action capacity. Do not retune the R26 gate
after the fact. `q_A`/`q_d`/`q_D` remain blocked/default-off.

## Round 24 Assignment-to-Behavior Bridge (completed gate)

Status: **R24-1 FAIL accepted 2026-07-09** (external review Round 5, GPT-5.5
xhigh, SUPPORTS_WITH_CONDITIONS), with the wording condition "fail under the
tested policies and current diagnostic setup" (3 of 4 policies collapsed) — not
a categorical universal negative. All four 320k cloud runs failed all core gates
(`residual_gain` -0.0319..+0.0153 vs the 0.05 threshold; `positive_frac` < 0.60;
real loses to `behavior_only` in 3 of 4). **q_d/q_D reward paths remain BLOCKED
on this evidence line.**

- **R24-2 / R24-3** (low-only q_d reward, q_D re-probe): BLOCKED/CLOSED on that
  evidence line. No reward-arm execution until a mechanism changes the setting.
- **D2** (frozen-analyzer early-stopping sensitivity re-run): APPROVED-DEFERRED,
  archival solidity only — not confirmatory, not a gate reset. Conditions:
  separate validation split; identical stopping rules across variants; all
  outcomes reported; single all-GPU device class; an unexpected pass reopens
  instrument validity only and does **not** justify reward-on.
- **D3** (pivot to individual-skill behavioral differentiation): ACCEPTED — this
  is the line R26/R27 now execute.

Standing constraints from R23-next: `Z -> xi` (q_A) is learnable and stands;
`xi -> low-level/joint behavior -> recoverable team effect` remains unproven.
`q_d` must exclude focal `z_i` from assignment context (`xi_context_i = xi_-i`);
`q_D` must not read `xi` directly or it double-counts q_A.

## Round 22 Two-Clock Objective Unification (contract; execution log archived)

The active two-clock contract (`OPT substrate -> sampled slow team intent Z ->
asynchronous individual response skills z_i`; R12 = recognition substrate, R19 =
mechanism-negative control) lives in `memory/ALGORITHM_PRINCIPLES.md`
("Active R22 Contract"), with `memory/R22_TWO_CLOCK_ELBO.md` and
`memory/R22_TARGET_ENTROPY_DESIGN.md` as the derivations.

Standing rule from R22-5 (mechanism budget): **every new mechanism must retire,
absorb, or supersede an existing one.** Terms absent from the two-clock objective
are deletion candidates. Topology/communication rewards stay diagnostic-only and
never become an intrinsic objective.

The R22-0..R22-4 execution receipts and the mechanism-budget table are in
`memory/LTM/IMPLEMENTATION_PLAN_ARCHIVE_20260713.md`.

## Legacy Compatibility Boundary

- This branch is for constructing the new HA-CTSE/process algorithm, not for
  conservative HMASD maintenance.
- Keep old `hmasd`/`hmasd_original` runnable only as comparison baselines when
  doing so does not block the new algorithm.
- Do not keep fixed-k HMASD data-flow assumptions inside the HA-CTSE core just
  to preserve old behavior.
- Preserve archived `_server_package_*` folders by not editing them.

## Ruled Out / Stop Rules

- Segment posterior `q(z | S, g)`, context-residual posterior, and
  future-cooperation outcome residual probes repeatedly failed to beat
  shortcut/context baselines as reliable positive intrinsic rewards. Keep them
  diagnostic-only unless a new run pre-commits a falsification metric.
- Topology-role discrimination is the final classifier-style semantic probe in
  this family. If its full classifier does not sustainably beat the
  OPT/context/duration shortcut, stop adding new residual-discriminator heads.
- Duration-only shortcut is now a hard gate for segment-posterior intrinsic
  reward: if duration-only accuracy is not worse than posterior accuracy by the
  configured margin, segment posterior reward is zeroed before it can affect
  either high or low policy updates.
- Process reward with magnitude far below environment reward remains
  diagnostic-only unless explicitly changed to a centered/advantage-style
  shaping mode.


## Archived Plan History

Completed/superseded rounds (Decoupled-K, R12, R19, R20, R21, the June-2026
correction passes, HMASD cooperation-bias audit, repo/module maps, and the
2026-06-25..27 slices) were rotated verbatim to
`memory/LTM/IMPLEMENTATION_PLAN_ARCHIVE_20260713.md` on 2026-07-13. Read it only
when this plan points there or the user asks for history.
