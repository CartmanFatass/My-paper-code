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

## Round 27 G2 Forced-z Trajectory/Effect Intervention (implementation authorized; in progress)

Status (2026-07-12): the pre-implementation design review is complete and the
controller disposition is `ACCEPTED_WITH_MODIFICATIONS_AS_DESIGN_ONLY`. The
user subsequently authorized implementation and focused verification only;
pilot and decision-grade launch remain blocked. The
frozen design is
`docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md`. The raw
user-supplied Claude review is
`docs/external-review/R27_G2_design_review_20260712_Claude.md`; its response is
complete, while exact Claude model/version provenance was not supplied.

The load-bearing review objection is accepted: nonzero deterministic closed-
loop divergence cannot distinguish persistent conditional control from a
one-step action nudge amplified by dynamics. R27-G2 therefore gates on a
matched hold-versus-10-step-pulse contrast, sustained instantaneous label-swap
controllability on hold-induced states, and held-out late-window executed-
action label consistency. Raw trajectory, state, pre-tanh separation, or
local-observation divergence cannot pass the behavior gate alone.

Frozen protocol:

- Three R25 arm0 temporal checkpoints only: update25, update30, and final.
- Exactly 64 reset groups and one stochastic-natural context per reset, with
  prefix lengths 50/150/250 assigned 22/21/21 by `reset_id mod 3`.
- Every branch constructs a fresh environment, replays exact recorded
  `float32` prefix actions, restores the complete policy runtime, and asserts
  observation/state/RNG/hidden/checkpoint parity before intervention.
- Natural stochastic prefixes use isolated per-reset RNG jobs (or sequential
  reseeding); a shared asynchronously interleaved Torch RNG is not valid.
- Stage 1 freezes team code, non-focal skills, clocks, and all high-level
  assignment/renewal calls. A focal-only audit overlay supplies the label to
  the live stateful recurrent low actor; the legacy zero-hidden and all-agent
  forced paths are prohibited. Each branch restores actor/critic hidden once,
  then advances both exactly once per step. The repository does not yet have
  this unified actor-distribution/live-runtime hook, so it is a required
  implementation unit rather than an existing interface.
- Exactly 55 branches per reset: one unforced reference, 24 holds, 18
  non-natural 10-step pulses, and 12 paired inactive-label branches.
- The actual R25 native individual durations are 10/20/30/40 primitive steps,
  not the external review's assumed 30/70/130/240. Gated windows are steps
  1-10, 11-20, and 31-40; H40 is the single primary effect endpoint and H50 is
  descriptive stress only.
- Gate A rechecks the R27 immediate-capacity anchors. Gate B requires all of
  sustained controllability on every hold branch, hold-over-pulse late
  deterministic action (`tanh(mu)`) behavior with an absolute magnitude floor,
  and held-out four-label consistency from fixed 12-feature executed-action
  summaries. Gate C separately requires a benchmark-local hold-over-pulse full
  focal-observation effect at H40. All inferential resampling is by reset
  cluster; pair support counts distinct reset groups, never agent rows, and
  checkpoints are temporal observations, not seeds.
- Same-label or inactive-label leakage, fresh-replay mismatch,
  live/diagnostic mismatch, per-step matched environment-RNG divergence, RNG
  consumption, checkpoint-file or full-`state_dict` mutation, non-finite
  evidence, nondeterministic CUDA, or CPU fallback makes a checkpoint
  `INVALID`. Support loss is `UNDERPOWERED`, not `FAIL`.
- A family behavior pass requires Gate B at at least two of three checkpoints.
  A stable effect pass requires B+C at at least two of three. Partial patterns
  are explicitly `MIXED`. `TRANSIENT_ACTION_NUDGE` requires the exact decay,
  no-hold-advantage, chance-decoding, and effect-fail pattern; other all-
  negative patterns are `NO_PERSISTENT_SEPARATION`. Any invalid or underpowered
  checkpoint makes the family invalid or underpowered before the two-of-three
  rule is considered.

Claim boundary: a pass establishes only persistent conditional control under
forced hold in the frozen R25 executor, for up to the native 40-step maximum.
It does not establish natural skill selection/duration, asynchronous
semi-Markov validity, team complementarity, reward usefulness, or task
improvement. Beside the R26 natural observational negative, a pass is recorded
as `FORCED_CAUSAL_CAPACITY_WITH_OBSERVATIONAL_NEGATIVE`, not automatically as
observational-instrument failure.

Compute boundary: the exact decision-grade Stage-1 workload is 708,000
environment steps per checkpoint and 2,124,000 across all three, plus
diagnostic forwards/decoder fitting. Register 12-20 hours on cloud CUDA. A
separately authorized eight-reset wiring pilot is under 90,000 environment
steps and cannot contribute outcomes to the final gate. CUDA is mandatory and
there is no CPU fallback.

Authorization boundary: R27-G2 code, analyzer, cloud runner/Git workflow, and
focused verification are complete. Pilot and decision-grade
launch each remain separate decisions. Reward, actor/GRU/FiLM changes, natural-renewal
Stage 2, H100, and long task-scale training remain blocked. Even a B+C pass
would require a separate task-generic reward-target design; Gate C's full
Scenario-7 observation/communication fields cannot become reward. No
`memory/ALGORITHM_PRINCIPLES.md` change is needed.

Remote execution boundary (updated 2026-07-13): the reusable SSH lifecycle is
implemented in `scripts/remote/run_hmasd_r27_g2.ps1`, using the same external
private key already authorized for the identical AutoDL `root` endpoint and a
separate repository alias. Its default `prepare` action performs remote CUDA,
tool, separate-data-filesystem/free-space, `screen`, and registered non-empty
checkpoint-path preflight; it stages the three checkpoints under
`/root/autodl-tmp/HMASD/checkpoint_dist`, obtains source through Git, and
performs a zero-write runner dry-run. No application-layer content digest is
part of the workflow. Source, checkpoints, logs, and results remain under the
data disk. Authorized long commands run in a recorded detached GNU `screen`
session. `launch`/`all` are fail-closed behind the exact
experiment authorization, clean committed Git source, and explicit
validation of the selected parallel topology. By user directive on 2026-07-13,
the default is the 64-worker flattened queue and serial launch/fallback is
disabled. Final success and
complete collection revalidate all 192 reset artifacts plus both aggregate
reports rather than trusting status text. Aggregate reports are regenerated
from the current 192 structured reset artifacts rather than using a stale-input
identity layer. On 2026-07-13 the GitHub SSH default and Windows OpenSSH state
serialization were validated, then the non-launching `prepare` passed against
the live server. It rechecked CUDA, the separate data filesystem, free space,
`screen`, and all three cached checkpoints; fast-forwarded the clean data-disk
checkout to commit `60ac83e`; and rendered all 192 reset commands plus the
aggregate command in zero-write dry-run mode. Final read-only validation
confirmed a two-line Bash-readable source pointer, no current-run pointer, no
dry-run directory, and no R27 `screen` session. The old review ZIP is historical
only and is not source or launch authority. No experiment launch has occurred.
A local process audit found no live experiment to migrate; future
compute-bearing work remains cloud CUDA by default.

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
