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

## Round 22 Two-Clock Objective Unification (planned)

Source plan:

```text
docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md
```

Status: planned / theory-first / no new reward module yet.

Round 22 accepts the GPT-5.5 Pro correction that R21/v6 is the current
algorithmic mainline:

```text
OPT recognition substrate -> sampled slow team intent Z ->
asynchronous individual response skills z_i.
```

R12 is now a recognition substrate/control line, not the primary cooperation
engine.  R19 is a mechanism-negative transition-residual control unless later
complete reward-on evidence contradicts the current negative `team_t_mi` read.

Staged tasks:

```text
R22-0: memory alignment.
  Update cross_validation, principles, implementation plan, and attention
  pointer so R21/v6 is the mainline and R12/R19 are controls.

R22-1: write `memory/R22_TWO_CLOCK_ELBO.md`.
  Derive the objective for slow sampled Z plus fast async z_i; audit
  team-discriminator, individual/coordinator residual, entropy, and possible
  cross-layer terms for double-counting.

R22-2: keep experiment track running.
  Launch/read EXP-20260705-r21-team-intent and
  EXP-20260705-hmasd-currentenv-baseline when compute is available.  These are
  not blocked by the derivation.

R22-3: add only missing diagnostics required by the bound.
  Audit/add `z_decisions_per_update`, `z_advantage_mean/std/var`,
  `combined_intrinsic_env_ratio`, `team_disc_reward_env_ratio`, and
  per-duration Z-boundary truncation fields if not already present.

R22-4: write `memory/R22_TARGET_ENTROPY_DESIGN.md`.
  Recast duration/Z/skill/action entropy as per-head target-entropy
  constraints.  Do not replace the current floors until R21/HMASD reads show
  which head collapses under useful learning.

R22-5: mechanism budget pruning.
  Every new mechanism must retire, absorb, or supersede an existing mechanism.
  Terms absent from the two-clock objective default to deletion candidates.
```

Execution status update (2026-07-05, Codex subagent-driven execution):

```text
R22-0 COMPLETE:
  memory/cross_validation.md, ATTENTION_POINTER.md, ALGORITHM_PRINCIPLES.md,
  and this plan now name R21/v6 as the active mainline and R12/R19 as
  substrate/control lines.

R22-1 COMPLETE:
  memory/R22_TWO_CLOCK_ELBO.md written and reviewed.  Spec review approved.
  Quality review found and fixed five implementation-risk issues:
    - Z vs z_i notation/metric ambiguity,
    - target-temperature sign convention,
    - clock-count normalization across team/individual/primitive clocks,
    - detached/null baseline semantics for p_hat and stored log pi_z,
    - tau/r notation mix.

R22-3 IMPLEMENTED / VALIDATION PENDING:
  Existing diagnostics:
    z_usage_entropy
    team_disc_reward_env_ratio
    z_boundary_trunc_rate
    z_boundary_trunc_rate_dur3/7/13/24
  Added diagnostics:
    z_decisions_per_update
    z_advantage_mean
    z_advantage_std
    z_advantage_var
    combined_intrinsic_env_ratio
    combined_intrinsic_env_ratio_over05_count
    combined_intrinsic_env_ratio_guard_active
    combined_intrinsic_env_ratio_kill_triggered
  Modified locations:
    ha_ctse_process/standalone_agent.py
    ha_ctse_process/team_intent.py
    ha_ctse_process/train.py
    ha_ctse_process/plotting.py
    tests/r21_team_intent_test.py
    train_multiproc_config_1.py
  Notes:
    z_advantage_* is computed on unnormalized high-level advantages and only for
    Z-boundary samples with nonzero team_logp_weight.  combined_intrinsic_env_ratio
    sums the active prototype-disc and team-disc reward/env ratios and uses the
    same reward_ratio_guard_mode semantics as the individual guards.  HMASD eval
    falls back to episode-level parity metrics if light metrics omit per-step
    reward_info, with parity_step_metric_fallback_used logged.

R22-4 COMPLETE:
  memory/R22_TARGET_ENTROPY_DESIGN.md written and reviewed.  It keeps
  auto-temperature design-only until R21/HMASD reads identify which head
  collapses under useful learning.
```

Mechanism budget table:

| Mechanism | Current status | R22 disposition |
| --- | --- | --- |
| R21 sampled team intent `Z` | mainline | keep and test |
| OPT `omega/c/kappa` | substrate | keep as recognition input/control |
| R12 situation hazard | deferred | no expansion until after R21/HMASD read |
| R19 transition residual | control | no new sweep unless complete reward-on contradicts negative probe |
| `g` / team bridge | deprecated | no new mechanism conditions on it |
| target `kappa*` | deferred | revisit only if ELBO or R21 failure points to target commitment |
| topology/communication rewards | diagnostic only | never use as intrinsic objective |

Validation before implementation completion:

```powershell
rg -n "Round 22|two-clock|Mechanism budget" memory\IMPLEMENTATION_PLAN.md
Test-Path docs\superpowers\plans\2026-07-05-r22-two-clock-elbo-mainline.md
```

## Decoupled-K Sanity Gate

The current K-matrix is a sanity/diagnostic gate, not the final objective.  It
answers:

```text
Can the variable-lifetime implementation approach strong fixed/shared controls,
avoid obvious desynchronization failure, and expose whether asynchronous renewal
needs stronger HMASD-style intrinsic pressure?
```

Run this before drawing claims from P1/P2 coefficient work:

```text
A. HMASD original baseline                              external baseline
B. HA-CTSE full-sync fixed-k / candidates=(1,)          reward-pure
C. HA-CTSE shared fixed duration / candidates=(7,)      reward-pure
D1. HA-CTSE decoupled short / candidates=(1,2,3)        reward-pure
D2. HA-CTSE decoupled mixed / candidates=(1,2,4,8)      reward-pure
```

Use `scripts/run_s7s1_k_matrix_32env.sh` for B-D. Run HMASD original separately
through `train_multiproc_config_1.py` with matched S7-S1 settings.

Interpretation rule:

```text
D beats max(B, C):
  evidence that asynchronous lifetime may already be useful.

D ~= max(B, C):
  acceptable engineering sanity only if lifetime metrics remain heterogeneous.
  If the learned policy collapses to one fixed/shared lifetime, it is not a
  successful HA-CTSE mechanism even if short-run reward looks competitive.

D < max(B, C):
  do not conclude "variable lifetime is useless"; conclude that the current
  optimization/intrinsic-credit loop has not learned the useful special case.
```

The stronger scientific claim requires later evidence that variable lifetimes
are used nontrivially and that the HMASD-inspired intrinsic loop makes those
asynchronous skills discovered, differentiated, and useful.

Mechanism metrics now logged by HA-CTSE:

```text
lifetime_heterogeneity
duration_agent_mi
duration_return_range / std
duration_full_disconnect_range / std
duration_recovery_range / std
duration_bh_frac_range / std
renewal_agents_mean / std
renewal_full_sync_rate
renewal_pairwise_corr_mean
```

Only after this reward-pure K-matrix should P2-lite or P3-style semantic pressure
be applied to the best fixed/shared control and the best decoupled control. This
separates credit repair / intrinsic-drive reconstruction from the mechanical
duration implementation.

## Round 12 Substrate Gate (Active Candidate Stage 0)

Round 12 reframes the mainline as OPT-first Situation-Response Skill Discovery.
Before any new reward or hazard mechanism is implemented, the OPT situation
substrate must pass a pre-registered gate.

Purpose:

```text
Prove that omega_tau / c_tau can serve as a learned interaction-situation
substrate rather than an ordinary drifting embedding.
```

Immediate implementation order:

```text
R12-0a: zero-new-run CSV triage.  Tooling implemented 2026-07-02.
  Inspect existing train_updates.csv fields:
    opt_aggregation_entropy
    opt_cd_loss
    opt_cmi_loss
    compact_norm_mean
  Decision: prototype collapse or uniformity means the current substrate is
  already suspect before new instrumentation.
  Command: `python scripts/analyze_r12_csv_triage.py --root logs --output
  logs\r12_substrate_gate_local\csv_triage.json`.

R12-0b: eval-only omega dump.  Tooling implemented 2026-07-02.
  Add a default-off eval/checkpoint flag that dumps, per check interval:
    omega_tau / OPT aggregation weights
    per-entity argmax prototype or membership summary
    delta_omega
    compact norm
    aligned generic credit/role fields already available from evaluation
  The dump must force diagnostic-only topology-role counterfactual computation
  for G-ROLE.  Before reporting any G-ROLE number, the analyzer must assert:
    role-label variance > 0
    max role-label fraction < 0.95
  A G-ROLE read against all-zero `topology_cf_*` labels is invalid, not a clean
  negative result.
  No training-path change and no reward injection.
  Implemented as `python -m ha_ctse_process.export_substrate_gate` plus the
  local runner `scripts/run_r12_substrate_gate_local.ps1`.

R12-0c: offline substrate analysis.  Tooling implemented 2026-07-02.
  Compute:
    G-DWELL   vs block-shuffled null
    G-OUTCOME early-window episode-mode prediction vs shortcut baselines
    G-ROLE    MI/stability against topology-role counterfactual labels

  Use a checkpoint grid, not latest-only:
    frozen encoder x early/mid/late stored policy checkpoints
    best-vs-worst episode contrast

  Pre-registered thresholds:
    G-DWELL passes only if median dwell >= 3 check intervals and transition
      diagonal mass exceeds the block-shuffled null by >= 0.20.
    G-OUTCOME passes only if cross-validated AUC >= max(0.60,
      simple-feature-baseline AUC + 0.05), using the existing zero-throughput /
      coverage-positive episode-mode split.
    G-ROLE is valid only if role-label variance > 0 and max label fraction <
      0.95; it passes only if MI >= permuted-label MI mean + 2 std and
      within-phase membership stability exceeds the permuted baseline by >=
      0.10.
  Implemented as `scripts/analyze_r12_substrate_gate.py`.

R12-0d: HMASD current-env gap re-verification.
  Rerun HMASD-original on current S7-S1 and S7-S3, >=2 seeds, before any long
  Round 12 paradigm run.
```

Pre-registered decision tree:

```text
gate passes:
  implement reward-pure situation-change hazard and compare with fixed-best /
  discrete-duration controls.

omega fails but compact c has structure:
  cluster c instead of raw omega; re-gate.

omega and c both fail:
  do exactly one offline situation-ness encoder retrain on pooled logs; re-gate.

retrain fails:
  validate the Round 12 paradigm using hand-crafted topology situation classes
  before spending more effort on learned omega.
```

Hard boundary:

```text
Do not add SEF/DADS reward, target-situation commitment, co-edit AR, or a new
g-response branch until R12-0 substrate results are read.
```

Implementation status as of 2026-07-02:

```text
R12-0a/0b/0c diagnostic tooling is implemented.  The compact-vector fallback
path is also implemented: exporter writes full compact/omega vectors and the
analyzer compares omega membership against deterministic compact clusters.
Validation:
  - `tests/test_r12_substrate_gate.py`: 59 passed.
  - AST syntax validation passed for substrate gate/export/analyzer modules.
  - tiny checkpoint export/analyze smoke produced substrate_steps.csv,
    substrate_roles.csv, and substrate_gate_report.json.

The full local checkpoint-grid substrate gate has now been run on the available
16env duration-short checkpoints (updates 20/40/60, 600 step rows).  Report:
`logs\r12_substrate_gate_local_duration_short_16env_compact_full\substrate_gate_report.json`.
Result: omega passes G-DWELL/G-OUTCOME/G-ROLE with `fallback_decision=omega_pass`;
compact_cluster also passes and gives stronger G-OUTCOME.  This unblocks
planning the reward-pure situation-change hazard / situation-response Stage 1,
but it is not a final performance claim.  Before any long Round 12 paradigm
run, keep R12-0d HMASD current-env gap re-verification and, if a true 32env
checkpoint grid becomes available, repeat the same substrate gate there.
```

## Round 12 Stage 1 Situation-Hazard Implementation Result

R12-1a implemented on 2026-07-02: default-off situation substrate diagnostics
and reward-pure oracle-change renewal control are in the working tree.  Default
behavior remains off.  No SEF/DADS reward, communication-specific reward,
target-situation commitment, or co-edit reward was added.  The `learned_beta`
mode is inference-only until a real hazard PPO buffer/update is designed.

Validation/handoff:

```text
- Requested basetemp pytest command was attempted, but pytest hit Windows
  PermissionError [WinError 5] while removing .pytest_tmp_r12_stage1_final.
- Same targeted tests without forced basetemp passed: 70 passed.
- AST parse without pycache passed for situation_substrate.py,
  situation_hazard.py, standalone_agent.py, train.py, plotting.py, and smoke.py.
- scripts/run_r12_stage1_local_cuda.ps1 dry-run passed for diag_only and
  oracle_change at 32k / 4 envs.
- Tiny subproc train was attempted and blocked at multiprocessing.Pipe() with
  PermissionError [WinError 5]; no gymnasium dependency blocker was observed.
```

### R12-1a local CUDA readout (2026-07-03)

Clean run:

```text
logs\ha_ctse_r12_stage1_local_cuda\run_20260703_001552
```

Result:

```text
diag_only_reward_pure and oracle_change_reward_pure both completed 40 updates /
320k steps. Reward-path guards stayed clean: process/high/low,
force/effect/topology low rewards remained 0.0.

The oracle-change control was mechanically active:
  forced_renewal_rate last10 ~= 0.041
  situation_segment_change_frac last10 ~= 0.754 vs 0.457 in diag_only
  segment_length_mean last10 ~= 85.5 vs 117.2 in diag_only
  duration and skill entropy stayed high.

But the gate failed:
  320k coverage: 0.100 oracle_change vs 0.137 diag_only
  320k zero-throughput episode fraction: 0.80 vs 0.60
  320k reward_std: 65.8 vs 47.0
  backhaul_connected_frac: 0.200 vs 0.325
  coverage_eq1_step_frac stayed 0.0 in both arms.
```

Decision:

```text
Do not proceed to learned_beta PPO from this read. The first-pass oracle-change
renewal appears to add churn and hurt stability despite clean reward purity and
healthy entropy. Stage 1 needs a conservative renewal hardening pass first.
```

Next engineering stage:

```text
R12-1b Conservative situation-change renewal:
  - add or expose stronger min-age / debounce / dwell-confirmation controls;
  - add a forced-renewal-rate cap or skip-renewal condition for noisy changes;
  - keep reward path pure and SEF/DADS reward disabled;
  - rerun diag_only vs conservative oracle_change before any learned_beta PPO.

If conservative oracle renewal still hurts, return to the substrate
representation / renewal criterion before implementing SEF/DADS reward or
target-situation mechanisms.
```

### R14 Stage 1 spec commissioned (2026-07-03, CC — spec only, no code)

User-approved next design stage from `memory/cross_validation.md` Round 14:
prototype-response selection (J2) + per-step individual discriminator with
active-skill labels and situation-conditioned prior (J5 surviving half),
plus optional compact return-grounding head. Full implementation spec for
Codex, grounded in current code shape (simplified encoder, per-env kappa,
checkpoint-metadata precedent, transition-skill legacy path to avoid):

```text
docs/superpowers/plans/2026-07-03-r14-stage1-prototype-selection.md
```

Everything default-off; reward bootstrap-scale (coef 0.1) behind its own flag
with warmup; pre-registered experiment template
`EXP-2026070X-r14-stage1-prototype-selection` with gates and stop rules in the
spec. Relation to R12-1b: independent code paths; R14 Stage 1 does not touch
hazard/guard code. Ordering note from CC: R14 Stage 1 and the recognition-Z
HMASD control (R14.0) are both cheaper than long R12-1b sweeps and inform
whether R12-1b tests the right layer.

R15 amendment (2026-07-03, user-accepted paper-level idea): the spec now
mandates AR-first selection (the sequential decision is kept HMASD structure
AND the reward's null model) and replaces Part B's learned prior head with
the coordinator-residual reward `log q_d(z_i|o',kappa) - stored log pi_h`.
Derivation sketch + vacuity lemma + falsifiable predictions:
`memory/R15_steering_objective_derivation.md`; digest in
`memory/cross_validation.md` Round 15.

Codex implementation update 2026-07-03: R15 Stage 1 is now implemented in the
working tree.  The default prototype-response discriminator uses the stored
skill-assignment log-prob as the null (`log q_d - stored log pi_h`); the old
learned situation-prior head is opt-in fallback only via
`--prototype_disc_use_learned_prior`.  Prototype-response high-level selection
is AR-first by default, while legacy `control_legacy4` remains non-AR.
`proto_disc_null_logp_mean`, `proto_assignment_logp_mean/std`, and
`proto_ar_parallel_kl` are logged to console/TensorBoard/CSV/plots.  Old R14
`s1_probe/s1_reward` runs are superseded for mainline decisions unless
intentionally labeled as the R15-P1/R14.1 fallback ablation.

Detailed implementation plan (2026-07-03, completed first pass):
`docs/superpowers/plans/2026-07-03-r15-stage1-steering-objective-alignment.md`.
This plan is aligned to `EXP-20260703-r15-stage1-steering`: 16-env local-read
frame, `opt_num_prototypes=4`, A0 `control_legacy4` via `--legacy_n_skills 4`,
A1 probe before A2 reward, and conditional A3 R15-P1 fallback.

Validation:

```text
pytest tests\r14_prototype_response_test.py -q -> 8 passed
AST parse for changed R15 files/tests -> ast_ok 6
R15 runner dry-run default and explicit reward/fallback arms -> passed
tiny local smokes: s1_probe, s1_reward, control_legacy4, r15_p1_ablation -> passed
Subagent spec review: no blocking issues. Follow-up fixes applied:
  - added proto_assignment_logp_mean to prototype diagnostics plot;
  - added batch-level null-logp broadcast test.
```

R15 A0/A1 local read result (2026-07-04):

```text
A0 control_legacy4:
  reached update 40 / 320k; eval-only fill at 320k:
    coverage=0.096667
    zero_throughput_ep_frac=0.750000
  usable as a weak control comparator, not a performance claim.

A1 s1_probe:
  reached update 40 / 320k with clean reward guards:
    proto_reward=0.000000
    proto_steps=0
  final structural read:
    proto_acc=0.270
    proto_null=-1.381176
    proto_ar_kl=0.000000
    proto_resid=0.007863
    proto_skill_ent=0.998
    proto_kappa_ent=0.974
    proto_align=0.012
  320k eval is missing; fill it only for bookkeeping.
```

Initial gate decision: A1 failed the original R15 AR-coordination health gate
because the rollout metric `proto_ar_kl=0.0` showed no difference from parallel
selection.  This was treated as a possible wiring blocker until a direct
intervention test could be run.

Post-CC revision and Codex wiring check (2026-07-04):

```text
Added:
  tests/r14_prototype_response_test.py::
    test_r15_agent_init_forced_prefix_changes_assignment_logits

Validation:
  python -m pytest tests\r14_prototype_response_test.py -q
    -> 9 passed

Result:
  In the full R15 StandaloneProcessAgent configuration, a forced nonzero AR
  prefix changes high-level assignment logits at initialization.  The prefix
  channel is wired.

Revised interpretation:
  A1's `proto_ar_kl=0.0` is not a disconnected-input failure.  It is evidence
  that reward-off rollout does not create pressure for the AR prefix to matter,
  or that asynchronous renewal often presents only one expired agent at a time.
  Under the revised gate, `proto_ar_kl` is demoted from A1 blocker to A2 outcome
  metric.
```

Next implementation/experiment decision:

```text
A2 `s1_reward` may be launched as an explicit coordinator-residual
reward-pressure test if the team accepts the revised gate.  It should not be
described as a strong A1 pass: final A1 `proto_acc=0.270` is only weakly above
chance (0.25), although reward guards and entropy health were clean.

If A2 still leaves `proto_ar_kl` / separation flat and task metrics down, fall
back to the pre-registered R15 path: R15-P1/kappa-prior ablation first, then
Round 11 commitment-first anchor if that also fails.
```

R16 roster-docking amendment (2026-07-04, accepted):

```text
Problem:
  R15 A1 showed `proto_ar_kl=0.0`, but the prefix wiring check passed.  CC then
  read renewal statistics directly from A1:
    renewal_agents_mean ~= 1.44 of 6
    renewal_full_sync_rate = 0.0
    renewal_pairwise_corr < 0

Interpretation:
  same-check AR is structurally starved under decoupled lifetimes.  Most checks
  renew only one or a few agents, so the same-check prefix is often empty.
  This is not a failure of asynchrony; it is a mismatch between synchronized
  HMASD AR and asynchronous HA-CTSE renewal.

New Stage-1.5 implementation task:
  add `ar_prefix_mode = same_check | roster` behind a flag.

same_check:
  current implementation; keep as A2 and control path.

roster:
  a renewing agent conditions on teammates' currently active skills and
  skill ages, ordered by fixed id or renewal recency.  Redefine AR diagnostic as
  KL(selection | true roster || selection | zeroed roster), measurable at every
  renewal.
```

Pre-implementation guards from CC (2026-07-04; mandatory):

```text
G1. Roster snapshot, not live roster.
  Segment must store the exact renewal-time roster snapshot used to sample:
    teammate active skill ids
    teammate active skill ages
    ordering/mask
  PPO update/evaluate must reconstruct high-policy conditioning from the stored
  snapshot, never from current agent state.  Required unit test:
    recomputed logp from Segment snapshot == stored assignment logp.

G2. Full-sync special case.
  When all agents renew in one check, roster mode must reduce exactly to
  same-check / HMASD AR: later renewers see earlier renewers' newly sampled
  skills.  Required unit test:
    forced full-sync roster prefix equals same-check prefix.

G3. Two roster KL diagnostics.
  Log both:
    roster_ar_kl_zeroed   = KL(selection | true roster || zero roster)
    roster_ar_kl_shuffled = KL(selection | true roster || shuffled roster)
  A2r prediction and stop rule use `roster_ar_kl_shuffled`; zeroed KL is only a
  mechanical capability read and can be off-distribution.

G4. Skill ages are required.
  Roster encoding must include active skill ages.  A skill-only roster prefix is
  only allowed as a labeled ablation, not as the main R16 implementation.

G5. Anti-duplication metric must be independence-corrected.
  Do not use raw co-active same-skill duplication as the complementarity metric:
  with 4 skill codes and 6 agents, independent uniform selection already makes
  same-skill overlap likely.  Log:
    selection_independence_deficit =
      observed co-active same-skill rate
      - shuffled-teammate independence null with matched skill-usage marginals
  A2r anti-duplication movement is judged on this deficit, not raw duplication.
  Desired movement is downward/negative relative to A2 or the shuffled null;
  expected effect size may be modest at N=4.
```

Sequencing:

```text
1. A2 `s1_reward` may still run before roster mode, but interpret it narrowly:
   coordinator-residual reward-pressure under a mostly-empty same-check null.
2. Implement roster mode while/after A2 runs.
3. Run A2r = A2 + `ar_prefix_mode=roster` as the one-variable follow-up.
4. If A2r with 2 seeds still has roster_ar_kl_shuffled < 0.01, no negative
   movement in `selection_independence_deficit`, and no task benefit vs A2,
   drop sequential assignment from the mainline and fall back to parallel
   selection with the kappa-conditioned null / Stage-3 complementarity pressure.
```

R16 implementation result (2026-07-04):

```text
Status:
  Stage-1.5 roster-docking is implemented and locally verified.

Changed code:
  ha_ctse_process/standalone_agent.py
    - Added `ar_prefix_mode = same_check | roster`.
    - Added renewal-time roster snapshots to Segment:
        active skill ids, active ages, active mask.
    - Roster mode builds a high-policy prefix from active teammate skills,
      ages, and earlier newly sampled renewers in the same check.
    - PPO high-level update/evaluation rebuilds the AR prefix from the stored
      Segment snapshot, not from live agent state.
    - Added `roster_ar_kl_zeroed`, `roster_ar_kl_shuffled`, and
      `selection_independence_deficit`.
  ha_ctse_process/train.py / config.py / plotting.py /
  prototype_response_discriminator.py
    - Added CLI/config/metadata/logging/CSV/TensorBoard/plot fields for the
      roster mode and diagnostics.
  tests/r14_prototype_response_test.py
    - Added focused tests for roster prefix content, full-sync reduction,
      snapshot logp reconstruction, and independence-corrected anti-duplication.

Validation:
  python -m pytest tests\r14_prototype_response_test.py -q
    -> 13 passed, 1 warning.
  AST parse of touched HA-CTSE files
    -> ast_ok 6.
  SB3-env CLI help
    -> `--ar_prefix_mode {same_check,roster}` is exposed.
  Tiny roster smoke train, 2 env / 16 rollout / 32 steps / CPU
    -> completed one update; log and CSV included `roster_kl_shuf` and
       `selection_independence_deficit`.
  Runner hardening after first overnight attempt
    -> `scripts/run_r16_a2r_overnight_local_cuda.ps1` now writes a per-arm
       `run_command.cmd` and invokes `cmd.exe` so Python stdout/stderr are
       redirected directly to `runner_output.log`; this avoids Windows
       PowerShell 5.1 wrapping harmless matplotlib stderr warnings as
       terminating `NativeCommandError`.

Remote execution support:
  Added `scripts/run_r16_a2r_remote_32env.sh` and packaged the current R16
  working tree for cloud/multi-server execution:
    dist/ha_ctse_r16_a2r_remote_bundle_20260704_163219.zip
  The runner defaults to S7-S1, 6 agents, 32 envs, CUDA, 960k steps, eval every
  160k, and lets each server run one arm via `EXPERIMENTS=...`.
  This is execution infrastructure only; it does not change the R16 algorithm.
  The corresponding experiment ledger entry is
  `EXP-20260704-r16-a2r-remote-parallel`.

Next experiment:
  A2r = A2 `s1_reward` + `--ar_prefix_mode roster`.
  The primary read is not raw task reward at 320k; it is whether the coordinator
  residual reward plus roster context moves:
    roster_ar_kl_shuffled >= 0.02,
    selection_independence_deficit downward/negative relative to A2/null,
    while reward-scale and entropy guards remain healthy.
```

R16.5 closing-plan implementation result (2026-07-04):

```text
Status:
  Implemented; launch is pre-registered as
  `EXP-20260704-r16-5-coef01-entfloor`.

Motivation:
  The local coef=0.1 roster arm reached the best known S7-S1/R16 checkpoint at
  update_60 / 480k, then regressed by update_120 / 960k with high-level
  duration entropy collapse and renewal resynchronization.  R16.5 is a
  one-variable stabilization test, not a new mechanism.

Changed code:
  ha_ctse_process/config.py
    - Added default-off duration entropy floor config.
  ha_ctse_process/standalone_agent.py
    - Added SkillDurationPolicy.entropy_components().
    - Added high-level duration-head floor loss activated only when realized
      duration_usage_entropy falls below the configured threshold.
    - Logged duration_policy_entropy, duration_policy_entropy_norm,
      duration_entropy_floor_active, duration_entropy_floor_gap,
      duration_entropy_floor_loss, and duration_entropy_floor_coef_active.
  ha_ctse_process/train.py
    - Added CLI:
        --enable_duration_entropy_floor
        --duration_entropy_floor_threshold
        --duration_entropy_floor_coef
        --duration_entropy_floor_warmup_steps
        --reward_ratio_guard_mode {kill,warn}
    - Added manifest/start-log/TensorBoard/console support.
    - Added `--eval_action_mode deterministic|stochastic` for R16.5 P2.
    - Added runtime guard:
        instant stop if proto_disc_reward_env_ratio > 1.0 post-warmup;
        sustained stop if proto_disc_reward_env_ratio > 0.5 for 5 consecutive
        post-warmup updates.
      Guard mode amendment from CC final spec:
        kill = export update metrics first, then raise RuntimeError.
        warn = log standalone_runtime_guard_warn and continue.
        proto_disc_reward_env_ratio_over05_count is cumulative over the whole
        run; it no longer resets after a trigger.
        proto_disc_reward_env_ratio_kill_triggered is a cumulative
        would-have-killed update count, not a per-update boolean.
  ha_ctse_process/plotting.py
    - Added CSV/plot fields for floor metrics, guard metrics, and eval
      action_mode_code.
  scripts/run_r16_a2r_overnight_local_cuda.ps1
  scripts/run_r16_a2r_remote_32env.sh
    - Added arm `a2r_roster_coef01_entfloor`; default arm lists unchanged.
    - The entfloor arm hard-passes `--reward_ratio_guard_mode warn` and prints
      `guard_mode: warn` in its banner to prevent the reference-termination
      confound.
  scripts/run_r16_5_p2_eval_modes.ps1
    - Added a four-read deterministic/stochastic eval wrapper for update_60
      and update_120 checkpoints.

Validation:
  In-memory compile of touched Python files:
    config.py / standalone_agent.py / train.py / plotting.py -> ok.
  Tiny CPU train smoke with `--enable_duration_entropy_floor`:
    completed; floor activated when usage entropy fell below threshold.
  Tiny stochastic eval smoke with `--eval_action_mode stochastic`:
    completed; eval logs include action_mode=stochastic.
  R16.5 P2 eval wrapper dry-run:
    expanded update_60/update_120 x deterministic/stochastic commands and
    verified both checkpoints exist.
  Guard-mode final spec validation:
    default config is kill;
    local entfloor runner dry-run prints `guard_mode: warn` and includes
    `--reward_ratio_guard_mode warn`;
    forced-trigger warn smoke continues and accumulates over05/kill counters;
    forced-trigger kill smoke raises only after the update CSV row is written.

Experiment readout 2026-07-05:
  Completed run:
    logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_233759\seed1\a2r_roster_reward_coef01_entfloor
    exit_code=0

  Eval comparison:
    reference 480k peak:
      reward=78.140158, coverage=0.345000, qos=0.271246,
      throughput=22.015988, backhaul_connected_frac=0.387600,
      zero_throughput_ep_frac=0.550000.
    reference 960k collapse:
      reward=20.078933, coverage=0.080000, qos=0.061291,
      throughput=6.547736, backhaul_connected_frac=0.210400,
      zero_throughput_ep_frac=0.750000.
    entfloor 960k:
      reward=67.263427, coverage=0.493333, qos=0.341250,
      throughput=27.252762, backhaul_connected_frac=0.446900,
      zero_throughput_ep_frac=0.200000,
      coverage_eq1_step_frac=0.075700,
      coverage_eq1_ep_frac=0.300000.

  Gate classification:
    PASS-SCAFFOLDED, not PASS-CLEAN.
    The performance side passes: 960k holds >80% of the reference 480k peak
    and strongly beats the reference 960k collapse.  The mechanism side is
    floor-supported: duration_usage_entropy=0.543469,
    duration_usage_max_frac=0.770270, duration_entropy_floor_active=1 at 960k,
    and last10 floor_active=1.0.  Therefore lifetime heterogeneity is not yet
    self-maintaining.

  Guard / AR notes:
    warn mode logged proto_disc_reward_env_ratio_kill_triggered=2 and
    proto_disc_reward_env_ratio_over05_count=25 by 960k; reward-scale pathology
    co-occurred but did not kill the run.  Roster AR remains weak:
    proto_ar_parallel_kl and roster_ar_kl_shuffled stay around 5e-06.

Next experiment:
  Run/read the P2 deterministic/stochastic eval reads on update_60 and
  update_120 checkpoints, then decide whether entfloor is the stabilized R16
  base for R19/a2_plus_t.  Do not claim emergent lifetime heterogeneity from
  this seed-1 result.
```

The spec also contains the sequencing/dependency map for the remaining jobs
(J3 needs the s1_probe READ; J4 needs the full Stage 1 gate; Stage 4 after
J3+J4; hold J3/J4 code until the probe read — the P3-4 lesson) and a
PARALLEL TRACK of four items with no Stage-1 dependency that should start
now: P1 per-agent kappa_i (mechanically needs Part A2 only), P2 recognition-Z
HMASD control (commitment-vs-context decisive experiment), P3 HMASD
current-env gap re-verification (owed since Stage 0), P4 G-ACTIONABILITY
offline gate (adjudicates the pending R12-1b line).

### R14 Stage 1 prototype-response implementation result (2026-07-03)

Implemented from:

```text
docs/superpowers/plans/2026-07-03-r14-stage1-prototype-selection.md
```

Scope completed:

```text
R14-1 Part A: prototype-response selection plumbing
  - `use_prototype_response_skills` default-off.
  - Prototype-response skill space can be tied to `opt_num_prototypes` plus
    optional extra codes.
  - `InteractionCompactEncoder` now returns agent-level prototype relevance,
    tracks an EMA prototype bank, and logs prototype-bank drift.
  - High policy can optionally condition on global omega and per-agent
    prototype relevance.
  - Segment records now store kappa/omega/relevance snapshots for diagnostics.

R14-2 Part B: individual per-step prototype-response discriminator
  - New `ha_ctse_process/prototype_response_discriminator.py`.
  - Trains q(z | o_next, condition) and a condition-only prior p(z | condition).
  - Conditions supported: kappa, omega, or none.
  - Low-only residual reward path is implemented but default-off and warmup-gated.
  - It is independent of legacy process posterior, transition discriminator,
    topology-role reward, and communication-specific reward paths.

R14-3 Metrics / checkpoint / runner wiring
  - Prototype discriminator, prototype selection, per-agent kappa, compact-return
    fields flow to train_updates.csv, TensorBoard, console logs, and plotting.
  - Claude's experiment/readout update is now reflected in code:
      proto_disc_reward_env_ratio is logged;
      proto_rel_row_entropy_mean / proto_rel_argmax_dwell_median /
      proto_rel_stability_cos / proto_rel_drop_event_rate_05/_03/_01 are logged;
      reward-off effect_intervention diagnostics are enabled by the R14 runner
      across control, s1_probe, and s1_reward for forced-z spread comparisons.
      After subagent review, metric semantics were corrected: skill usage entropy
      is grouped by `kappa_start`, skill/relevance alignment is normalized MI
      against relevance argmax, and reward/env ratio is visible before warmup as
      a prospective scale preview.
  - R14 runner now explicitly disables legacy process posterior MI, outcome
    residual, topology-role, transition-skill discriminator, and process reward
    paths in all arms so the control remains reward-pure and matched.
  - Caveat: current forced-z spread readout is the existing
    `effect_intervention_*` proxy (action and predicted-effect intervention),
    not exact rollout trajectory spread at h={10,50}.  Exact rollout spread is
    deferred until the proxy/probe read is promising or ambiguous.
  - Checkpoints save/restore the new modules and structure metadata.
  - Local CUDA runner added:
      scripts/run_r14_stage1_local_cuda.ps1
  - Targeted tests added:
      tests/r14_prototype_response_test.py
```

Validation:

```text
pytest tests\r14_prototype_response_test.py -q
  -> 3 passed

AST parse, no pycache write:
  standalone_agent.py
  prototype_response_discriminator.py
  g_info_objective.py
  situation_substrate.py
  train.py
  plotting.py
  -> ok

Runner dry-run:
  scripts\run_r14_stage1_local_cuda.ps1
  -> commands print correctly for control, s1_probe, s1_reward

Tiny train smokes:
  probe-only: prototype metrics logged; process reward stayed zero.
  reward-on with warmup=0: low-only prototype reward applied; process reward
  stayed zero.
  checkpoint load/eval smoke: passed.

Known validation caveat:
  py_compile hit Windows PermissionError on existing __pycache__ directories;
  AST parse was used as the no-write syntax check.
```

Runtime fix 2026-07-03:

```text
During the first full local `s1_probe_no_reward` arm, `GInfoObjective` crashed
after the control arm completed.  The diagnostic had sub-sampled high-level
samples to `g_info_max_segments=256` but left optional `omega` and
`agent_relevance` at the full segment count.  With R14 high_omega and
agent_proto_rel enabled, this caused:

  expanded size 256 must match existing size 925 at dimension 0

Fix:
  ha_ctse_process/g_info_objective.py
    - sub-sample optional `omega` and `agent_relevance` with the same `chosen`
      rows as high_obs/prev_skills/ages/compact.

Regression test:
  tests/r14_prototype_response_test.py
    - `test_g_info_objective_subsamples_optional_omega_and_relevance`

Validation:
  python -m pytest tests\r14_prototype_response_test.py -q
    -> 4 passed

  no-write AST parse for g_info_objective.py and the R14 test file
    -> AST_OK

Operational note:
  The completed `control_reward_pure` arm can remain the baseline.  Restart
  only `s1_probe,s1_reward` for the next local run.
```

Next experiment:

```text
EXP-20260703-r14-stage1-prototype-selection
```

Preferred local CUDA command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r14_stage1_local_cuda.ps1 `
  -Experiments control,s1_probe,s1_reward `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda
```

Do not implement R14 Stage 2 omega-space commitment, coverage complementarity,
or team transition reward until the `s1_probe` read shows non-vacuous residual
signal and the `s1_reward` arm does not collapse skill/duration usage or regress
basic task metrics.

> SUPERSEDED IN PART (2026-07-04, Round 19): the TEAM TRANSITION term is
> pulled forward out of this blanket hold. Rationale: the individual N=4
> coordinator-residual term is a role-diversity drive bounded by ln 4 and
> cannot supply HMASD-scale exploration (the team identifiability engine was
> killed by the vacuity lemma and needs its structural replacement). The
> team-transition heads are built NOW in parallel with A2; the `a2_plus_t`
> reward arm launches only via the pre-registered OUT-OF-GAS branch of the
> A2 outcome matrix or an explicit user decision after the A2 read. Stage 2
> commitment and coverage remain held as stated. Final implementation
> reference: `docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md`.

Interpretation note from user clarification 2026-07-03:

```text
HMASD normally needs around 1e6 steps on S7-S1 before its stable high-coverage
behavior is the fair comparison point.  The current R14 320k local run is only
a Stage-1 mechanism gate:
  - control establishes a short-run baseline and checks reward purity;
  - s1_probe checks whether prototype-response discrimination has residual
    signal beyond the situation-conditioned prior;
  - s1_reward checks whether the low-only residual reward immediately collapses
    usage or regresses basic task metrics.

Do not treat weak 320k coverage as a final performance verdict against HMASD.
If s1_probe is non-vacuous and s1_reward is not damaging, the next performance
test should be a longer ~1e6-step run under matched settings.
```

### R12-1b conservative renewal implementation (2026-07-03)

Implemented:

```text
Default-off conservative situation-change guard:
  situation_hazard_conservative_guard
  situation_hazard_min_dwell_checks
  situation_hazard_confirm_changes
  situation_hazard_max_force_rate
  situation_hazard_rate_window

The guard carries pending kappa-change pulses through confirmation/dwell checks
via `ConservativeRenewalDecision.renewal_signal`, so a one-step
`SituationState.changed` pulse can still trigger renewal after min-age and
confirmation constraints pass.

The guard is opt-in and baseline `oracle_change` remains unchanged when
`--enable_situation_hazard_conservative_guard` is absent.

New runner arms:
  oracle_conservative
  oracle_strict
```

Validation:

```text
- Spec review: SPEC_PASS.
- Code-quality review: QUALITY_PASS.
- `python -m pytest tests\r12_conservative_renewal_test.py -q`: 7 passed.
- AST parse passed for situation_hazard.py, config.py, train.py,
  standalone_agent.py, plotting.py, and tests/r12_conservative_renewal_test.py.
- `scripts\run_r12_stage1_local_cuda.ps1` dry-run passed for
  diag_only, oracle_conservative, oracle_strict.
- Tiny sync smoke passed at 32 total steps with conservative guard enabled.
  CSV reward guards stayed zero and new guard metrics were written.

Known local artifact:
  The original ignored test migration copy
  `tests\test_r12_conservative_renewal.py` could not be deleted due Windows
  Access denied. The tracked test is `tests\r12_conservative_renewal_test.py`.
```

Round 13 interpretation caveat:

```text
Claude/Codex cross-validation confirmed that current `kappa` is env-global:
`assign_kappa_from_omega` returns one kappa per env, and
`SituationDebouncer` is keyed by env_id.  The renewal loop then feeds the same
`situation_state.changed` pulse to every eligible agent; only skill age and
guard state are per-agent.

Therefore R12-1b does not yet test the intended per-agent situation-validity
hazard `beta_i`.  It tests whether an env-global situation boundary can be used
as a guarded/rate-capped renewal trigger.
```

Next run:

```text
EXP-20260703-r12-1b-conservative-renewal:
  diag_only vs oracle_conservative vs oracle_strict, local CUDA first.

Do not proceed to learned_beta PPO from this read alone.  If a conservative arm
is neutral-to-positive against diag_only without entropy collapse or reward-path
contamination, add `random_matched` and `boundary_gated` controls first.  If
conservative arms are worse, stop guard-constant tuning and run
G-ACTIONABILITY / renewal-criterion analysis before any learned hazard update.
```

## Round 21 Team-Intent Restoration (2026-07-04, USER OVERRIDE — build now, highest priority)

User Architect decision: bring the HMASD autoregressive team skill back
while keeping asynchronous low-level lifetimes. Supersedes Round 20 D2
(ablation DROPPED) and D3 (kappa* deferral DISSOLVED). Spec (source of
truth): `docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md`.

```text
Two-clock hierarchy: sampled Z ~ pi_Z(Z|c,omega) held K_team=12 checks;
ATOMIC full-team AR reassignment at Z boundaries; async individual docking
(z_i | Z, c, o_i, roster) between them. HMASD = K_team=1 special case.
Team discriminator engine ships IN THE SAME BUILD: per-step low-level
lambda_D * (log q_D(Z|s') - log p_hat(Z)), bootstrap scale 0.1 — non-vacuous
because Z is SAMPLED. q_d gains Z conditioning. pi_g/bridge machinery is
refactored into pi_Z; old decorative g wiring deleted in-scope.
Build NOW default-off; LAUNCH on the stabilized entfloor base after its
480k read; a2_plus_t demoted to complementary. Pre-register
EXP-2026070X-r21-team-intent before launch (gates in spec: improvement
required vs stabilized base; z entropy not collapsed; disc acc in healthy
band; z_boundary_trunc_rate << 1).
```

Implementation receipt (2026-07-05, Codex Executor):

```text
Status: IMPLEMENTED default-off; not yet formally launched.

Code delivered:
  - ha_ctse_process/team_intent.py
      TeamIntentDiscriminator, prior-corrected residual reward, metric fields.
  - ha_ctse_process/config.py / train.py
      R21 CLI/config/manifest/checkpoint plumbing; `--enable_team_intent`,
      `--enable_team_disc_probe`, `--enable_team_disc_reward`, `--team_intent_k`,
      team-disc coef/clip/warmup/lr/hidden controls.
  - ha_ctse_process/standalone_agent.py
      two-clock Z lifetime state; atomic full-team AR reassignment at Z
      boundaries; async individual docking against held Z; boundary-only Z
      log-prob weight; no edit/switch penalty at Z boundary; rollout next-state
      capture; team discriminator update/reward path; R21 diagnostics.
  - ha_ctse_process/plotting.py
      CSV/plot fields for `z_*` and `team_disc_*`.
  - tests/r21_team_intent_test.py
      targeted tests for AR override, R21 guardrails, boundary semantics,
      async docking, discriminator reward shapes, and R21+prototype-disc
      conditioning.

Post-review fixes:
  - Added `team_codes` to the prototype-discriminator batch when R21 is active
    so `q_d(z_i | o'_i, kappa, Z)` does not crash in combination runs.
  - R21 now disables low-actor team-code conditioning even if legacy
    `--enable_low_actor_team_code` is supplied.
  - R21 rejects `team_bridge_type=none` at both CLI/config override and agent
    construction layers.
  - Team-intent prior counts are saved/restored in checkpoints as torch tensors
    to keep PyTorch `weights_only=True` loading safe.

Validation performed:
  - `python -m pytest tests\r21_team_intent_test.py -q` -> 6 passed.
  - import check for train/standalone_agent/team_intent/plotting -> import_ok.
  - structure smoke with `--enable_team_intent --enable_team_disc_probe`
    confirmed `ar_selection=True`, `parallel_selection=False`,
    `ar_prefix_mode=roster`, and R21 metrics written.
  - combination smoke with `--enable_team_intent --enable_prototype_disc_probe`
    confirmed the individual/prototype discriminator receives Z conditioning.
  - reward-on smoke with `--enable_team_disc_reward --reward_ratio_guard_mode warn`
    confirmed reward application metrics and warn-mode guard logging without
    stopping the run.
  - tiny checkpoint smoke confirmed `team_intent_prior_counts` is present and
    loadable with default `torch.load`.
  - CLI guard smoke confirmed `--enable_team_intent --team_bridge_type none`
    exits with a ValueError before launch.

Known caveats / launch guard:
  - R21 is default-off; no performance claim exists yet.
  - The formal experiment still requires `EXP-20260705-r21-team-intent` launch
    entry with stabilized-base controls, exact command, and gate thresholds.
  - Current training architecture resets policy state at rollout boundaries, so
    the Team Intent slow clock is guaranteed within rollout; long-run read
    should inspect `z_dwell`, `z_boundary_trunc_rate`, and `z_assignment_itv`.
```

Launch-preflight amendment (2026-07-05, Codex Executor after CC review + user
direct-cloud instruction):

```text
Status: IMPLEMENTED / launch-ready.

Accepted fixes:
  - `team_intent_k` default changed from 12 to 48.  K_team is the effective
    maximum individual lifetime at Z boundaries; 12 structurally truncated
    duration candidates 13 and 24 and would fabricate duration collapse.
  - `team_disc_coef` default changed from 0.1 to 0.05, matching the R16.5
    dose-response result where 0.05 was the cleaner stabilized base.
  - Added default-off Z entropy floor configuration/CLI/manifest/metrics:
    `z_entropy_floor_*`.  It is an insurance/stabilizer flag only, not evidence
    of self-sustained team-intent heterogeneity.
  - Added per-duration Z-boundary truncation diagnostics:
    `z_boundary_trunc_rate_dur3`, `dur7`, `dur13`, `dur24`.
  - Updated R21 runners to use the 64-env cloud direct plan and the coef005
    matched base (prototype-disc coef=0.05, duration floor disabled, guard kill).
  - Added HMASD current-env baseline support: `train_multiproc_config_1.py`
    now accepts `--n_agents`; HMASD eval logs HA-CTSE parity diagnostics
    (`coverage_eq1_*`, `zero_throughput_episode_fraction`,
    `throughput_gt5_step_fraction`) without changing HMASD learning logic.

Validation:
  - AST/compile syntax check passed for modified Python files.
  - HA-CTSE train help exposes `--enable_z_entropy_floor` and R21 controls.
  - HMASD train help exposes `--n_agents`.
  - Local R21 PowerShell dry-run prints K=48, team_disc_coef=0.05, guard kill,
    coef005 base, and duration floor disabled.
  - Linux cloud runner static checks confirm NUM_ENVS=64, K=48, coef=0.05,
    `--n_agents 6`, and parity eval metric labels.  Local bash dry-run was not
    possible because bash is not installed on the Windows host.

Next:
  - Launch `scripts/run_r21_team_intent_cloud_64env.sh` directly on cloud.
  - Launch `scripts/run_hmasd_currentenv_baseline_cloud_64env.sh` if a second
    cloud slot is available.
```

## Round 20 Team-Bridge Disposition (2026-07-04, SUPERSEDED by Round 21 user override)

Per the Codex bridge audit and CC Architect ruling (cross_validation
"Round 20 disposition"): g_tau is DEPRECATED-IN-PLACE. Queued work only:

```text
team_bridge_none ablation (POST-a2_plus_t, on the stabilized base):
  one variable: team_bridge_type=none (config already supports it);
  removes g from high-level input AND low-level critic conditioning;
  read: task metrics vs the stabilized base — no regression expected;
  removal HELPING confirms the bridge was noise.
  Create its ExpRecord entry when scheduled, not before.
kappa* (coordination intent) stays RESERVED per R18.2/R18.3 —
  deceptive-axis trigger only; built clean with its own pressure;
  never refactored from g.
```

## Round 19 Team-Transition Engine (2026-07-04, implemented, trigger-blocked)

Status: IMPLEMENTED and locally validated by Codex after the final
multi-model review pipeline (Gemini plan v1 -> CC six amendments -> Gemini v2
-> CC approval with fold-ins -> CC completion notes -> CC final consolidated
plan).
Implementation reference (single source of truth, wins over all prior docs):

```text
docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md
```

What it is: the DADS-style situation-transition residual
`log q(kappa'|kappa, xi) - log q(kappa'|kappa)` — the structural replacement
for HMASD's team discriminator engine killed by the vacuity lemma. xi = the
active-skill count vector. Self-transitions INCLUDED so stabilization pays
(holding the relay chain is a xi-dependent predictable self-transition).
Injection: HIGH-LEVEL ONLY, per-interval clipped residuals accumulated into
segment returns; coef 0.05, clip 2.0, warmup 20k, probe/reward flag split,
own optimizer, detached inputs, clean module `situation_transition.py`.

Build/launch discipline:

```text
BUILT NOW (parallel to A2): module + config + wiring + tests + a2_plus_t
  runner arm. Everything default-off.
LAUNCH ONLY via the pre-registered OUT-OF-GAS branch of the A2 outcome
  matrix (disc separation healthy but task flat) or explicit user decision
  after the A2 320k read. One variable: a2_plus_t vs A2.
TASK GATE IS IMPROVEMENT, NOT NON-REGRESSION: this arm exists to fix the
  exploration deficit; neutrality vs A2 is a FAIL.
CHURN PRECURSOR: team_transition_reward_renewal_corr logged now,
  informational in a2_plus_t (no live hazard), MANDATORY input to the
  Stage-2 hazard go decision (kappa is dual-use: exploration reward target
  AND termination signal — R19.3).
```

Implementation receipt 2026-07-04:

```text
New module:
  ha_ctse_process/situation_transition.py

Main wiring:
  StandaloneProcessAgent records closed per-env situation intervals, trains
  SituationTransitionPredictor with its own optimizer, and accumulates
  no-grad residual rewards into per-segment high-level rewards only.

Config/CLI/checkpoint/logging:
  enable_team_transition_probe/reward, coef/clip/warmup/lr/hidden;
  checkpoint saves and loads team_transition + team_transition_opt;
  UPDATE_FIELDS/TensorBoard/console/plots include team_transition_* metrics.

Runner:
  scripts/run_r15_stage1_local_cuda.ps1 now exposes a2_plus_t_probe and
  a2_plus_t arms.

Validation:
  pytest tests\r19_team_transition_test.py -q -> 6 passed
  pytest tests\r14_prototype_response_test.py -q -> 13 passed
  AST compile for touched files -> ast_compile_ok
  a2_plus_t runner dry-run -> passed
  tiny reward-on smoke -> completed and logged team_t fields
  checkpoint save/load/eval smoke -> passed
```

## Current Repo Structure

- `hmasd/networks.py`: HMASD neural modules. It contains `OPT`,
  `sparsemax`, `SkillCoordinator`, `SkillDecoder`, `SkillDiscoverer`,
  `R_Actor`, `R_Critic`, `TeamDiscriminator`, and
  `IndividualDiscriminator`.
- `hmasd/agent.py`: training-facing `HMASDAgent`, skill assignment,
  action selection, intrinsic reward computation, discriminator updates,
  coordinator PPO update, low-level PPO update, and checkpoint IO.
- `hmasd/utils.py`: `RolloutBuffer`, `DiscriminatorBuffer`, GAE, PPO helper.
- `hmasd/baselines.py`: command-line algorithm registry and non-learning
  heuristic baselines.
- `config_1.py`: main configuration.
- `config_test.py`: small smoke configuration.
- `train_multiproc_config_1.py`: active training entry point. It exposes
  `--algorithm`, imports `ALGORITHM_CHOICES`, applies
  `apply_algorithm_config`, and creates agents through `create_agent`.
- `tests/`: pytest tests for buffer, intrinsic reward, hidden state arrays,
  sharded env, and scenario 7 checks.
- `new-test-alg/`: documentation and experiment notes for this reconstruction.

## Existing HMASD Modules

- High-level coordinator: `SkillCoordinator` in `hmasd/networks.py`.
- Team skill `Z`: sampled by `SkillCoordinator.assign_and_value_batch`.
- Individual skill `z_i`: sampled autoregressively in
  `SkillCoordinator.assign_and_value_batch`.
- Skill interval `k`: enforced in `HMASDAgent._batched_assign_skills` via
  `env_steps_batch % self.config.k == 0`.
- Low-level actor: `R_Actor.forward(obs, rnn_states, masks, agent_skill, ...)`.
- Low-level critic: `R_Critic.forward(cent_obs, rnn_states, masks, team_skill)`.
- Team discriminator: `TeamDiscriminator.forward(state)`.
- Individual discriminator: `IndividualDiscriminator.forward(observation,
  team_skill)`.
- PPO update path:
  - high level: `HMASDAgent.update_coordinator`;
  - low level: `HMASDAgent.update_discoverer_from_rollout`;
  - discriminator: `HMASDAgent.update_discriminators`.
- Rollout buffer: `RolloutBuffer` in `hmasd/utils.py`.
- Logging: `TensorBoardManager` and `RewardTracker` in
  `train_multiproc_config_1.py`, plus `training_info` in `HMASDAgent`.

## Existing OPT Modules

- `OPT` exists in `hmasd/networks.py`.
- `StateEncoder` can optionally use OPT, but current active
  `SkillCoordinator` bypasses `StateEncoder` and uses its own Transformer
  encoder.
- Existing `use_opt` fields in `config_1.py` do not yet implement the
  requested compact-team bridge separation.

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

## Current Correction Pass (2026-06-28)

- Added `g` intervention-KL diagnostic for the high-level policy:
  force each team code at the same segment start and measure pairwise KL/TV of
  `pi_z(. | o, c, g)`. Near-zero values mean `g` is decorative.
- Damped default SMDP bootstrap coefficient to `0.25` and added high-level value
  normalization so bootstrap value scale does not dominate segment environment
  returns.
- Added semantic shortcut hard-stop metrics:
  `semantic_shortcut_hard_stop_triggered`, `applied`, `score`, and
  `reason_code`.
- Experiment runners now support multi-seed sequential execution and include
  seed in the log directory name.

## Superseded Experimental Gate (2026-06-28 Round 3)

> SUPERSEDED by the Round 5 active gate below. Retained for history. The duration
> one-variable test ran (Arm A short duration): it improved coverage but did NOT
> reduce `credit_full_disconnect_mean` or raise recovery, so duration is not the
> dominant cause and the gate moved to backhaul-recovery credit/coordination.

- Latest reward-pure base-controller run shows the SMDP bootstrap scale issue is
  largely fixed, but stable relay-chain formation is still not solved:
  `credit_full_disconnect` stays high, recovery remains rare, and eval reward is
  bimodal.
- `g` intervention TV is borderline rather than clearly useful. Keep logging it,
  but do not spend new semantic-reward runs until the reward-pure controller
  first reduces relay disconnects.
- Duration commitment is the next one-variable test. Baseline remains
  `skill_lifetime_candidates=(3, 7, 13, 24)`. The new Arm A is
  `duration_short_reward_pure`, which changes only
  `skill_lifetime_candidates=(1, 2, 3)` while keeping process/semantic rewards
  disabled.
- Arm A early read at 160k is positive but inconclusive: coverage improves from
  roughly `0.092` to `0.213`, QoS from `0.077` to `0.130`, throughput from
  about `4.50` to `6.45`, and reward std/mean drops from about `2.24` to
  `1.74`.  However, `credit_full_disconnect_mean` is still noisy/high and
  `credit_recovery_mean` remains near zero.
- Falsification metric: short duration should reduce
  `credit_full_disconnect_mean`, improve recovery/collapse diagnostics, and
  lower eval bimodality (`reward_std / reward_mean` and fraction of zero-service
  episodes). If it does not, duration over-commitment is not the dominant cause.
- Decisive check: continue Arm A to at least 480k-960k and compare against the
  baseline curve, especially whether it avoids the baseline's post-peak
  regression after ~800k.  Add seed 2 before calling the duration hypothesis
  confirmed.
- Relay-aware early renewal is a later Arm B, not yet implemented. Do not run or
  claim it until short-duration reward-pure results are available.

## Active Experimental Gate (2026-06-28 Round 5)

Reframe: short duration improved access/coverage but did NOT move backhaul
recovery. `credit_full_disconnect_mean` (~0.6) and `credit_recovery_rate`
(~0.004) are flat across the long and short arms, and short-arm throughput fell
while coverage rose. The binding failure is relay-chain cooperation credit /
coordination (no recovery after a break), not re-decision frequency. Short-arm
switch_rate 0.80 with recovery ~0 partially falsifies the "needs faster
re-decision" hypothesis. Bimodality implies chains do form in high-mode episodes
-> stability/credit problem, not feasibility.

GATE: do NOT inject any semantic / segment-posterior / residual-MI reward.
Run P0 diagnostics first; P1 credit shaping only behind its hard gate.

P0 (diagnose before building; one variable per run, >=2 seeds):
1. High-mode feasibility/observability check: confirm good eval episodes actually
   hold a backhaul chain and that local obs carries backhaul state.
   STOP RULE: if good episodes never hold a chain -> feasibility/observability
   issue; escalate there before any algorithm change.
2. `low_actor_g_reward_pure` — diagnostic-only bottleneck violation, low-level
   actor FiLMs on `g` (`--enable_low_actor_team_code`). Never shipped (Invariant
   #5). FALSIFY: if `credit_full_disconnect_mean` does not drop AND
   `credit_recovery_rate` does not rise at matched steps -> `g` is not the lever;
   skip the g-coordination loss, go to P1 credit.
   STATUS 2026-06-28: P0.2 cloud seed1 is negative through 416k.  The decisive
   signal is not the confounded eval coverage gap (long durations + 32 envs) and
   not high-level `g_itv` alone; it is that `credit_full_disconnect_mean` stays
   around `0.57` and `credit_recovery_rate` around `0.01` after the low-level
   access bottleneck is removed.  Conclusion: low-level access to the current
   untrained/decorative `g` is not the blocker.  A topology-supervised/trained
   coordination `g` remains a different, untested mechanism, but it is
   deprioritized until cooperative credit is addressed.
3. `fixed_duration_reward_pure` with `skill_lifetime_candidates=(7,)`.
   FALSIFY: if fixed duration matches/beats learned-duration service metrics with
   lower variance -> learned-duration SMDP adds instability; simplify/normalize
   before further semantic work. Do NOT add per-duration advantage normalization
   speculatively; measure first.
   STATUS 2026-06-28: P0.3 done (16 env, reward-pure, 248k). Coverage ladder is
   monotonic in commitment length: long-learned 0.092@160k < fixed-7 0.170 <
   short-learned 0.213. Fixed-7 BEATS long-learned at matched steps, so the
   learned-duration SMDP's drift to long buckets is harmful (gamma^T bias is
   real). DECISION: drop the long learned-candidate set; build P1 on a
   short / fixed-short base. Gate metrics flat again (disc ~0.55, recover ~0.005)
   -> recovery is duration-invariant.

P0 STATUS: COMPLETE -> proceed to P1. Four configs (long-learned, short-learned,
low_actor_g/32env, fixed-7) are all stuck at `(full_disconnect ~0.55,
recovery ~0.01)`. Duration scheme, env count, and low-level g-access all moved;
recovery did not. The lever is cooperative topology credit, not any temporal /
access knob.

Implemented support (validated: py_compile, PowerShell dry-run, 16-step train
with low_actor_team_code=True):
- `low_actor_condition_on_team_code=False` by default;
- `--enable_low_actor_team_code` CLI flag;
- checkpoint metadata restoration for this flag (no eval/resume state_dict
  mismatch);
- `fixed_duration_reward_pure` and `low_actor_g_reward_pure` in both runners.

P1 (ACTIVE — P0 complete): topology potential-based cooperative credit shaping,
`F_i = gamma * Phi_i(s') - Phi_i(s)`, `Phi_i` = agent i marginal backhaul/
connectivity contribution (topology_role.py graph-removal counterfactual, or a
global form from `reward_info` fields). Permitted to revisit intrinsic shaping
because it targets cooperative credit, not skill identity, so the
duration/length/reward shortcut problem does not apply.  Do not over-claim
strict Ng-et-al. policy invariance for the first implementation: the default
`delta` mode and `low_only` segment injection are potential-inspired credit
shaping, not a theorem-guaranteed PBRS transformation.  Strict `smdp` mode is
kept as an ablation for that question.
DURATION BASE: build on short / fixed-short candidates (P0.3 decision), NOT the
long learned set, so the known-harmful duration drift is not stacked under the
credit experiment.
WIRING PREREQUISITE: per-agent `topology_cf_backhaul_*` fields are 0.0 unless
`topology_role_probe` (cf computation) is on. Start with a GLOBAL `Phi(s)` from
the populated credit fields (`credit_delta_uavs_with_backhaul`,
`credit_delta_backhaul_served_users`, `credit_bh_frac`, `credit_bh_thr`); wire
the graph-removal cf on before using per-agent `Phi_i`.
IMPLEMENTATION STATUS 2026-06-28: global-Phi P1 landed behind explicit flags:
`ha_ctse_process/topology_potential.py`, `--enable_topology_potential_shaping`,
`--topology_potential_injection`, `--topology_potential_coef`,
`--topology_potential_clip`, and `--topology_potential_discount_mode`.  The
first runner arm is `topology_potential_low_reward`, logged as
`s7s1_topology_potential_short_low_reward_*`: reward-pure/process-off,
topology role probe off, transition semantic reward off, low-only injection,
short candidates `(1,2,3)`, coef `0.05`, clip `0.08`, discount mode `delta`.
`delta` is the default P1
choice because strict `gamma^T Phi_end - Phi_start` can penalize maintaining a
good long relay state; `smdp` remains available as a stricter ablation.
VALIDATION: py_compile passed; direct function check gives positive reward for
disconnect recovery; `train.py --help` exposes new flags; 8-step sync smoke ran
with `topo_pot_active=1` and no update-path crash. Full pytest was not completed
because this local pytest invocation hung during startup/import.
JUDGE BY: `credit_bh_frac` (up) + `credit_bh_thr` (up) + `credit_full_disconnect_mean`
(down) + `credit_recovery_rate` (up), vs matched-step reward-pure.
HARD GATE: must reduce `credit_full_disconnect_mean` AND raise
`credit_recovery_rate` AND cut `reward_std/reward_mean` vs matched-step
reward-pure within ~300k steps (>=2 seeds), else revert (null result means
topology potential is not the missing signal -> escalate to explicit g
coordination loss or env reward redesign).
INTERPRETATION GUARD: P1 is an auxiliary credit-shaping probe, not a task
objective.  Backhaul/recovery gains are useful only when they also improve the
general task metrics (reward, coverage, QoS, throughput, variance) and do not
collapse the asynchronous skill-lifetime mechanism into a hand-coded relay
heuristic.

P1 CLOUD RESULT 2026-06-29 (`dist/logsoncloud`, 32 env, S7-S1, seed 1, 640k):
P1 improves service/backhaul metrics in some arms but fails the recovery hard
gate.  Last-10 update means keep `credit_recovery_rate` near zero across all
arms: reward-pure `0.0051`, high-only `0.0056`, high+low `0.0049`, signed
low-only `0.0038`, low-positive-only `0.0060`, topology-role-low tail `0.0046`.
At 640k eval, `topopot_low_pos_coef1` is the best P1 service baseline
(`reward=43.40`, `coverage=0.252`, `qos=0.152`, `throughput=9.14`,
`backhaul_connected_frac=0.370`, `std/mean=1.38`), while signed `topopot_low`
is weakest.  `topology_role_low_reward_tail` peaks early at 320k but regresses by
640k; its residual role signal does not move recovery.  Decision: retire signed
low-only, keep low-positive-only as the strongest P1 baseline, and prioritize
P2-lite recovery-window contribution credit rather than further P1 coefficient
sweeps.

## P2-lite Gate (2026-06-28) — Recovery-Window Contribution Credit

STATUS 2026-06-29: IMPLEMENTED (default OFF), validated by py_compile + smoke
tests, and shipped in `dist/ha_ctse_p2lite_bundle_20260629_064151.zip`.
- `ha_ctse_process/recovery_potential.py` — soft per-agent `phi_i` (non-saturating
  `exp(-d/scale)` closeness; saturating sigmoid caused a mid-gap dead zone, see
  principles "IMPLEMENTATION LESSON"), `W_recovery` smooth state weight, SIGNED
  segment shaping `F = gamma^dt Phi(s') - Phi(s)`, per-agent `F_i`, CF-audit +
  Pre-check-2 diagnostics. `test_recovery_potential.py`: 4 tests pass.
- `config.py`: `p2_*` flags, ALL OFF. `train.py`: `--enable_p2_recovery_compute`,
  `--enable_p2_recovery_reward`, `--p2_recovery_reward_level/coef/clip`.
  `standalone_agent.py`: compute/log/inject mirroring the P1 topology_potential
  path; reward injection behind `p2_recovery_credit_reward_on` (off).
- Runner `scripts/run_p2_recovery_experiments.{sh,ps1}`: staged
  precheck -> h0 -> h1 -> l1 on a short-duration reward-pure base.

UPDATE 2026-06-29 (Codex-cross-checked, three Pre-check-2-blocking fixes):
- LOGGING: P2 metrics were computed but dropped by the CSV writer (`UPDATE_FIELDS`
  in `plotting.py` lacked the keys; `append_csv` uses `extrasaction="ignore"`).
  Added all 19 `empty_p2_metrics()` keys to `UPDATE_FIELDS`, a `P2/*` TensorBoard
  group + 7 console fields in `train.py`. The first 320k precheck had run cleanly
  but its gate metrics were UNOBSERVABLE; that run is archived at
  `logs/ha_ctse_process_s7s1_p2_recovery_precheck_8env_seed1_320k_OLD_unlogged_320k`.
- RECOVERY_FLAGS: `aggregate_p2_metrics` was called without `recovery_flags`, so
  `p2_corr_phi_recovery_event` was structurally always 0 (gate unreachable). Now
  built in `standalone_agent.py` (started disconnected `bh_frac < near_thr` AND
  ended reconnected `bh_frac >= bh_threshold`) and passed; `owner_credit`/
  `recovery_flags` aligned to the AVAILABLE shapings so the aggregator's length
  check no longer silently drops them.
- SEGMENT START STATE: segments stored only post-step `state_info`, so
  `compute_segment_shaping` used the post-first-step state as s0 (biased the first
  transition's credit). True pre-step state now captured as `Segment.start_state_info`
  /`start_reward_info` (threaded through `SegmentManager.append` + the rollout loop)
  and preferred as s0; falls back to old behavior when absent (tests unaffected).
- GATE ENFORCED (not advisory): `scripts/p2_gate_check.py` reads the precheck
  `train_updates.csv` (tail-half mean) and the runners abort before h0/h1/l1 unless
  Pre-check 2 is positive. Flags: `--skip-gate`/`-SkipGate`, `--gate-csv`,
  `--gate-min-delta-phi`, `--gate-min-corr`.
- ENV: run under the SB3 conda env (`C:\Users\wu\.conda\envs\SB3\python.exe`); base
  python lacks `gymnasium`. Runners honor `PYTHON_EXE`.
- NEXT ACTION: a FIXED-code 320k `p2_recovery_precheck` is running (seed 1). Read
  the gate at completion; see "Two pre-checks" result note re: event-starved corr.
  Enable a reward variant ONLY after the (refined) Pre-check 2 is satisfied.

P2 is NO LONGER a cooperative-role discriminator and NOT the old P2a/P2b/P2c
suite. The active mechanism is a single lightweight signal: a SOFT recovery
connectivity potential that distributes topology progress to the agents most
likely responsible for recovering/maintaining the relay chain. Full contract:
`ALGORITHM_PRINCIPLES.md` -> `P2-lite: Recovery-Window Contribution Credit`.
INTERPRETATION GUARD: P2-lite is a sparse-reward / credit-assignment repair for
general cooperation.  It must not become "optimize backhaul" as a standalone
objective.  Treat backhaul/recovery fields as probes of whether the cooperative
credit signal is working; require service-task improvement and lower variance
before calling a P2 variant successful.

Why not the naive form. `window * pos(Delta Phi_global) * responsibility_i` fails
three ways: exact CF is heavy; exact CF is ZERO during full disconnect; and
`pos(Delta Phi_global)` is ~0 across a disconnect window (fires only at the
reconnection instant) -> still as sparse as env reward. Fix: a SOFT potential
(from positions/distances/margins) that moves during the approach to recovery,
shaped signed at the high level.

Core reward (high-level default):
```text
Phi_total(s) = Phi_base_service(s) + lambda_rec * W_recovery(s) * sum_i phi_i_recovery(s)
W_recovery(s) = sigmoid((bh_threshold - credit_bh_frac)/temp)     # smooth STATE weight
F_high_team   = gamma^dt * Phi_total(s_end) - Phi_total(s_start)   # SIGNED, telescopes
phi_i_recovery from soft edges: sigmoid((R - dist)/temp), bridge/bs-approach terms
```

Hard requirements:
- soft potential from positions/margins, NOT binary component size / Fiedler;
- compute-gating != reward-gating: gate only the EXPENSIVE exact-CF computation to
  windows/candidates; the main soft reward is defined as a (windowed-by-state)
  potential, never `if not window: reward=0`;
- SIGNED high-level shaping (farm-proof); `positive_only` only for low-level;
- per-agent attribution via `phi_i` (`F_i = gamma^dt phi_i(s_end) - phi_i(s_start)`),
  not `global_progress * static responsibility_i`.

Default flags (all OFF; must not pollute P1 logs):
```text
p2_recovery_credit_compute_on = false   # turn on for the diagnostic run
p2_recovery_credit_reward_on  = false
p2_role_classifier_reward_on  = false   # RETIRED from active gate
p2_g_normative_training_on    = false   # DEFERRED
exact_cf_reward_on            = false
exact_cf_compute_on           = false   # diagnostic/audit only, window+candidate gated
```

Sequencing (one variable per run, >=2 seeds):
```text
PRE: compute-on / reward-OFF; verify Pre-check 2 before injecting any reward.
H0:  high-level shared signed Phi_total            (first mainline reward run)
H1:  + per-agent signed phi_i high-level credit
L0:  no low-level P2 reward                         (default)
L1:  small positive-only low-level phi_i progress   (ablation only)
```

Two pre-checks (HARD gate):
1. Fields — CONFIRMED PASS: `state_info` exposes `uav_positions`,
   `ground_bs_positions`, `user_positions`, `area_size`, connection matrices
   (env_adapter `get_current_state`). No env extension needed for S7.
2. Soft-potential movement (run compute-on/reward-off first):
   `delta_phi_soft_nonzero_rate_when_full_disconnect > 0`,
   `..._when_near_disconnect > 0`, `corr(phi_i_recovery, later_recovery_event) > 0`.
   PASS != "Phi computes"; PASS = "Phi moves during disconnect AND predicts recovery."

   RESULT 2026-06-29 (fixed-code 320k precheck, S7-S1 energy, 8 env, ~62% at read):
   both delta-phi rates ~1.0 (PASS, strong). `corr(phi, recovery_event)` is
   EVENT-STARVED and INCONCLUSIVE — nonzero in only ~13/55 updates, peak ~0.044,
   sign unstable; backhaul recovery (start disconnected -> end `bh_frac>=0.6` within
   one ~20-step segment) is rare so the corr has nothing to bind to. Not a wiring
   bug (synthetic recovery signal -> corr ~0.996). DECISION (finalize at completion):
   keep the two delta-phi rates as the HARD gate; demote corr to INFORMATIONAL
   unless the recovery-event definition is broadened (count PARTIAL recovery: bh_frac
   rises by a margin / ends above a threshold lower than 0.6) so it gains signal. Do
   not let a strict `corr>0` on an event-starved metric block h0/h1/l1 by itself.
   FAIL -> do not inject reward; fix the potential first.

Reward hard gate (after Pre-check 2 passes, judged vs matched-step reward-pure):
`credit_full_disconnect_mean` down AND `credit_recovery_rate` up AND
`credit_bh_frac`/`credit_bh_thr` up AND `reward_std/reward_mean` down within
~300k, else revert.

P1/P2-lite parity-sweep decision tree:

```text
A. P2-lite improves task metrics, variance, and recovery while asynchronous
   lifetimes remain nontrivial:
   -> keep P2-lite as the credit-densification support mechanism;
      then consider P2b normative g / role allocation training.

B. P2-lite improves only backhaul/recovery diagnostics but not reward, QoS,
   throughput, coverage, or variance:
   -> treat as task-specific heuristic risk, not HA-CTSE success.

C. P2-lite remains below HMASD and does not move task metrics enough:
   -> stop P1/P2 coefficient sweeps and move to P3 dense skill-effect semantic
      pressure.  The missing HMASD function is then low-level dense semantic
      pressure, not stronger topology shaping.
```

Required logging:
```text
p2_window_frac, p2_cf_compute_frac, p2_cf_ms_per_update, p2_cf_ms_per_env_step,
p2_cf_nonzero_rate, p2_cf_candidate_frac,
p2_credit_mean/std/p95, p2_credit_by_disconnect_state, p2_credit_by_recovery_event,
delta_phi_soft_nonzero_rate_when_full_disconnect / near_disconnect,
corr(phi_i_recovery, exact_cf_i), topk_precision(phi_i_recovery, exact_cf_i).
```

Retired / deferred:
- P2c role-classifier reward: RETIRED from the active gate. The topology-role
  probe stays an optional diagnostic; it cannot block, justify, or define P2-lite.
  (Skill diversity is not the bottleneck.)
- P2b normative `g` training: DEFERRED until P2-lite moves the recovery metrics.
- `low_actor_g`: information-bypass diagnostic only, never shipped.

Arm B relay-aware early renewal remains a controlled event-vs-periodic test
(predicted to NOT fix recovery alone). Per-duration advantage normalization only
if learned durations are kept. Skill-conditioned `Phi` (skills -> distinct roles)
is the stage-2 re-entry, only after recovery moves.

## P3 Candidate (conditional) — Conditional Skill-Effect Discovery

Trigger: run this only if the current S7-S1 P1/P2-lite sweep fails to approach
HMASD-level behavior or only improves topology diagnostics without task-metric
and variance gains.

Goal: reconstruct HMASD's discriminator/intrinsic-reward function for decoupled
skill lifetimes.  Do not revive raw `q(z | o_next)` or generic segment posterior
reward.  The P3 target is a low-level intrinsic closed loop:

```text
skill sampled -> discoverer executes sustained process
-> skill effect becomes controllable / distinguishable
-> usefulness coupling pulls some effects toward task value
-> high level composes effects across agents and lifetimes
```

The core question is:

```text
Given the same context x_i(t), does knowing z_i improve prediction/control of
the short-horizon effect y_i(t,h)?
```

Implementation sketch:

```text
x_i(t) =
  o_start_i, g_tau, agent_id, phase_bin, skill_age_i, duration_bucket,
  optional local topology / service / battery summaries

y_i(t,h), h in {5, 10, 20} primitive steps =
  delta position / velocity / heading
  delta local service/access
  delta energy / charger progress
  delta soft recovery phi_i
  delta link margin / local graph margin
  delta connected users / access users

Full:
  p_full(y_i | x_i, z_i)

Baseline:
  p_base(y_i | x_i)

Effect gain:
  R_effect_i = log p_full(y_i | x_i, z_i) - log p_base(y_i | x_i)

Intrinsic:
  R_intr_i =
      lambda_ctrl * center_clip(R_effect_i)
    + lambda_use  * stopgrad(U_i) * clip_pos(R_effect_i)
```

First-run constraints:

```text
injection = low_only
lambda_ctrl = 0.02..0.05
lambda_use  = 0.02..0.05
clip = 0.05..0.10
warmup = on
shortcut gate = mandatory
high-level intrinsic gate = closed
on-policy only
```

Success criteria: task metrics and stability must improve, not only classifier
accuracy.  P3 is an attempt to restore HMASD's dense discoverer pressure, not a
new classifier leaderboard.

### P3 implementation stages

P3 execution must be tracked as a staged task ledger, not as a single vague
"implement P3" item.  Each subtask has its own deliverable, smoke test, and
experiment record.  Do not mark a later P3 stage complete just because an
earlier data path compiles.

### P3 staged task ledger

| ID | Task | Code Deliverable | Experiment Gate | Status |
|---|---|---|---|---|
| P3-0 | Freeze objective and stop rules | Principles/plan updated; `ExpRecord.md` entry created before any run | No code run without experiment record | Complete |
| P3-1 | Micro-window effect extraction | `ha_ctse_process/skill_effect_discovery.py::EffectWindowExtractor`; smoke check on Segment windows | Logs `effect_windows > 0`, no reward injection | Complete first pass (2026-06-30 smoke passed) |
| P3-2 | Conditional full/base effect predictors | `ConditionalEffectPredictor`, `ContextBaselinePredictor`, optimizer wiring in `StandaloneProcessAgent` | reward-off probe: `effect_gain_mean`, `effect_gain_positive_frac`, field-wise gains | Complete first pass (2026-06-30 smoke passed) |
| P3-2b | Effect target/model revision after negative probe | group-balanced effect losses, per-horizon gains, action/skill-use diagnostics, field-specific probes | repeat reward-off Stage A; full model must beat context/duration/reward baselines | Probe completed; gate failed (2026-06-30) |
| P3-2c | Controlled skill-use intervention audit | same-observation intervention over z_i; measure action distribution shift and expected effect-head shift | if z does not change action/effect under intervention, fix z->low-level coupling before reward | Experiment completed (2026-06-30): z changes low-level actions, but effect target/model still fails non-shortcut gate |
| P3-2d | Observed effect target/extractor revision | add end-state/window-mean effect targets and observed action-target skill audit | final reward-off free-signal audit; if negative, stop passive probe loop and move to controlled forcing design | Implemented first pass; run reward-off probe next |
| P3-2e | Skill-conditioning capacity audit | measure z-gating/FiLM strength, z-vs-observation actor variance share, and forced-z trajectory spread | short audit only; if z cannot induce persistent behavior modes, fix actor conditioning before stronger reward | Pending, no longer blocking first P3-4 code path |
| P3-3 | Shortcut and usefulness audits | duration/reward/phase/agent shortcut metrics; optional `U_i` estimator as diagnostic only | Do not inject if gain is shortcut-driven | Partial: duration/reward baselines logged; usefulness estimator still pending; blocked behind P3-2d |
| P3-4 | Low-only forcing intrinsic composer | `SkillEffectIntrinsicComposer`; low reward distribution over micro-window rollout indices | primary P3 implementation target: warmup + shortcut residual/kill-switch; judge with-force trajectory, not reward-off gain alone | Implemented first pass 2026-07-01; needs controlled ablation runs |
| P3-4a | Residual skill discriminator forcing | effect-window discriminator plus shortcut heads; residual reward composer | main 3+1 forcing term; discriminator residual must beat duration/reward/context shortcuts | Implemented first pass 2026-07-01 |
| P3-4b | Effect residual auxiliary | reuse full/base effect predictors as a weighted auxiliary forcing term | ablate `w_effect=0` vs positive; do not depend on effect residual alone | Implemented first pass 2026-07-01 |
| P3-5 | P3 + P2-lite coupling | combine P3 low-only with P2-lite high-level shaping, no topology-role reward revival | task metrics improve, not only effect classifier metrics | Pending |
| P3-6 | Variable-lifetime mechanism test | compare fixed/shared vs variable under same P3/P2 condition | variable lifetime improves or matches task metrics and uses nontrivial lifetimes | Pending |

Stage transition rule:

```text
P3-N is complete only when:
  code deliverable exists,
  smoke/py_compile passes,
  metrics are written to train_updates.csv/TensorBoard/console as relevant,
  an ExpRecord entry names the run, location, purpose, and result fields,
  and the previous stage's gate is read rather than assumed.
```

This is intended to prevent task-result discounting: a partial data-path change,
a diagnostic-only probe, and an intrinsic-reward run are separate achievements.

Stage A: reward-off probe.

```text
Add ha_ctse_process/skill_effect_discovery.py:
  EffectWindowExtractor
  ConditionalEffectPredictor
  ContextBaselinePredictor
  SkillEffectDiscoveryModule

Train p_full and p_base from on-policy micro-windows.
Do not inject reward.
```

Probe metrics:

```text
effect_gain_mean
effect_gain_positive_frac
effect_gain_motion
effect_gain_service
effect_gain_energy
effect_gain_topology
effect_gain_minus_duration_baseline
effect_gain_minus_reward_baseline
effect_reward_low_mean = 0
effect_reward_applied_steps = 0
```

2026-06-30 implementation note:

```text
P3 Stage A code landed as a reward-off probe only:
  - ha_ctse_process/skill_effect_discovery.py
  - StandaloneProcessAgent owns an independent SkillEffectDiscoveryModule
  - checkpoint saves skill_effect_discovery + skill_effect_opt separately
  - train CLI adds --enable_skill_effect_probe and related horizons/stride knobs
  - train_updates.csv, TensorBoard, console log, and plotting include effect_* fields
  - smoke passed at logs/ha_ctse_process_smoke_p3_stage_a with effect_windows=3
  - effect_reward_low_mean=0 and effect_reward_applied_steps=0 are explicit guards

No P3 reward path is connected.  P3-4 remains blocked until reward-off cloud/local
probe confirms positive non-shortcut effect gain.
```

2026-06-30 Stage A probe result:

```text
Run:
  logs/ha_ctse_process_s7s1_p3_stage_a_reward_off_16env_seed1_320k
  update=40, total_steps=320000

Gate outcome:
  FAILED.  This was a clean reward-off probe:
    effect_reward_low_mean=0
    effect_reward_applied_steps=0

Aggregate:
  all-update effect_gain_mean=-0.002188
  all-update effect_gain_positive_frac=0.442
  last10 effect_gain_mean=-0.004261
  last10 effect_gain_positive_frac=0.449
  last10 effect_gain_minus_duration_baseline=0.001111
  last10 effect_gain_minus_reward_baseline=-0.001657

Interpretation:
  p_full(y|x,z) does not beat p_base(y|x).  The reward baseline still beats the
  full model, positive fraction is below 0.55, motion dominates the negative
  signal, and service/topology gains are near zero.  Do not enable P3-4.

Next:
  create P3-2b before any intrinsic reward: revise effect targets/model/audits,
  add group-balanced field losses, per-horizon gains, action/skill-use
  diagnostics, and repeat the reward-off probe.
```

2026-06-30 P3-2b implementation note:

```text
Code landed as reward-off probe revision only:
  - skill_effect_discovery.py now trains effect predictors with optional
    group-balanced field loss (default on).
  - Metrics now include balanced/raw losses, group-balanced gain, non-motion
    gain, per-horizon gain/positive fraction/count for up to four horizons,
    field-specific gain for each effect target, skill usage entropy/max frac,
    action~skill eta2, target~skill eta2, gain std by skill, and action scale.
  - train.py exposes --disable_skill_effect_group_balanced_loss and logs the
    group-balanced setting in the run start line/manifest.
  - train_updates.csv, TensorBoard, console log, and plotting include the new
    P3-2b fields.
  - smoke passed at logs/ha_ctse_process_smoke_p3_2b.
  - tiny train passed at logs/ha_ctse_process_p3_2b_tiny_train and produced the
    new CSV fields with effect_reward_low_mean=0 and effect_reward_applied_steps=0.

No P3 reward path is connected.  P3-4 remains blocked until the revised
reward-off probe passes.
```

2026-06-30 P3-2b probe result:

```text
Run:
  logs/ha_ctse_process_s7s1_p3_2b_reward_off_16env_seed1_320k
  update=40, total_steps=320000

Gate outcome:
  FAILED.  Reward-off guards held:
    effect_reward_low_mean=0
    effect_reward_applied_steps=0

Aggregate:
  all-update effect_gain_mean=-0.000162
  all-update effect_gain_group_balanced_mean=-0.000023
  all-update effect_gain_nonmotion=0.000365
  all-update effect_gain_positive_frac=0.478
  all-update effect_gain_minus_duration_baseline=-0.000525
  all-update effect_gain_minus_reward_baseline=-0.000496
  all-update effect_action_skill_eta2=0.022
  all-update effect_target_skill_eta2=0.0069

  last10 effect_gain_mean=-0.000902
  last10 effect_gain_group_balanced_mean=-0.000700
  last10 effect_gain_nonmotion=0.000190
  last10 effect_gain_positive_frac=0.429
  last10 effect_gain_minus_duration_baseline=-0.000147
  last10 effect_gain_minus_reward_baseline=-0.000033

Interpretation:
  P3-2b improved the probe compared with old Stage A by reducing motion
  domination and exposing weak energy/topology signals, but it still does not
  satisfy the non-shortcut gate.  Duration/reward baseline gaps are negative,
  positive fraction is below 0.55, and action/target eta2 remain small.  Do not
  enable P3-4.

Next:
  run/read P3-2c controlled skill-use intervention audit.  Before reward design,
  test whether changing z_i at the same observation changes low-level action
  distributions and predicted short-horizon effects.
```

### P3-2c controlled skill-use intervention audit

P3-2c is the next direction after the P3-2b negative gate.  It is still
diagnostic-only and must not inject reward.

Question:

```text
At the same local observation/context, does changing z_i actually change the
low-level executor's action distribution and the predicted short-horizon effect?
```

Why this comes before P3-4:

```text
P3-2b showed weak non-motion effect structure, but action~skill eta2 and
target~skill eta2 were small.  That leaves two different failure modes:

1. z_i is decorative for the low-level executor.
2. z_i changes actions, but the current effect targets/horizons do not capture
   the consequences.

These must be separated before any intrinsic reward is designed.
```

Implementation deliverable:

```text
Add a reward-off intervention auditor, preferably in a separate module or inside
skill_effect_discovery.py if scoped tightly:

sample completed segment micro-windows or low-level rollout states
for each sampled (obs_i, current g/team context, agent_id):
  run low actor under z = 0..n_z-1 with deterministic/noise-controlled mode
  record action mean/std or sampled action statistics
  optionally pass each forced-z action/context through current effect predictor
  compute pairwise action KL/L2/TV-style distance
  compute predicted effect direction/range across z

Do not alter policy gradients or rewards.
```

Required metrics:

```text
effect_intervention_samples
effect_intervention_action_l2_mean
effect_intervention_action_l2_max
effect_intervention_action_pairwise_std
effect_intervention_pred_effect_l2_mean
effect_intervention_pred_effect_l2_max
effect_intervention_best_skill_gap
effect_intervention_low_entropy_mean
effect_intervention_active
```

Implementation status 2026-06-30:

```text
Implemented first pass in:
  ha_ctse_process/skill_effect_discovery.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/config.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  ha_ctse_process/smoke.py

The auditor is explicit-off by default and enabled by:
  --enable_skill_effect_intervention_probe

It samples micro-windows with update_norm=False, forces z=0..n_z-1 at the same
local observation/team-code context, compares low-actor action distribution
features, and compares the current full effect predictor's forced-z predicted
effect vectors.  It writes metrics only; it does not alter rollout rewards,
policy losses, high-level returns, or low-level returns.

Validation:
  py_compile passed for touched files.
  smoke passed at logs/ha_ctse_process_smoke_p3_2c with
    effect_intervention_active=1 and reward guards still zero.
  tiny S7-S1 train passed at logs/ha_ctse_process_p3_2c_tiny_train and wrote
    effect_intervention_* fields to metrics/train_updates.csv.
```

2026-06-30 P3-2c probe result:

```text
Run:
  logs/ha_ctse_process_s7s1_p3_2c_intervention_16env_seed1_320k
  update=40, total_steps=320000

Gate outcome:
  Diagnostic passed for z->low-level usage, but failed the reward gate.
  Reward-off guards held:
    effect_reward_low_mean=0
    effect_reward_applied_steps=0

Aggregate:
  all-update effect_intervention_action_l2_mean=0.135512
  all-update effect_intervention_pred_effect_l2_mean=0.098471
  all-update effect_gain_group_balanced_mean=-0.000316
  all-update effect_gain_positive_frac=0.501907
  all-update effect_gain_minus_duration_baseline=-0.001415
  all-update effect_gain_minus_reward_baseline=-0.001425

  last10 effect_intervention_action_l2_mean=0.199302
  last10 effect_intervention_pred_effect_l2_mean=0.106000
  last10 effect_gain_group_balanced_mean=-0.000907
  last10 effect_gain_positive_frac=0.525757
  last10 effect_gain_minus_duration_baseline=-0.002242
  last10 effect_gain_minus_reward_baseline=-0.002629

Eval:
  160k reward_mean=23.131215, coverage=0.116667, throughput=3.050000
  320k reward_mean=29.122841, coverage=0.136667, throughput=5.550714
  coverage_gt0_frac and throughput_gt5_frac stayed at 0.35;
  zero_throughput_frac stayed at 0.65.

Interpretation:
  z_i measurably changes low-level actions, and the action distance increases
  during training.  Therefore the next bottleneck is not the simplest
  z->low-level coupling failure.  The current effect target/model/horizons still
  fail to capture a stable non-shortcut useful consequence: group-balanced gain
  is negative by the end, duration/reward gaps remain negative, and task
  episodes remain bimodal.  Keep P3-4 blocked.

Next:
  Revise effect targets/extractor/horizons and observed effect audits before
  any intrinsic reward path.  Do not enable P3-4 from this result.
```

### P3-2d observed effect target/extractor revision

P3-2d is the immediate follow-up to P3-2c.  It remains reward-off.

Question:

```text
Given that forced z_i changes low-level actions, can the effect extractor expose
observable consequences that are not only short delta noise and not explained by
duration/reward shortcuts?
```

Implementation deliverable:

```text
Extend skill-effect targets from delta-only fields to:
  delta fields
  end-state service/access/topology fields
  within-window mean service/link/disconnect fields

Add observed audit metrics:
  effect_observed_target_skill_l2_mean
  effect_observed_target_skill_l2_nonmotion
  effect_observed_action_skill_l2_mean
  effect_observed_action_target_corr
  effect_endstate_available_frac
  effect_window_mean_available_frac

Keep reward injection closed:
  effect_reward_low_mean = 0
  effect_reward_applied_steps = 0
```

Implementation status 2026-06-30:

```text
Implemented first pass in:
  ha_ctse_process/skill_effect_discovery.py
  ha_ctse_process/config.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  ha_ctse_process/smoke.py

Changes:
  - SKILL_EFFECT_FIELDS now include end_* and mean_* observed fields.
  - EffectWindowExtractor computes post-window end-state values and in-window
    means from state_info_seq/reward_info_seq when present.
  - update() logs observed skill centroid distances for targets/actions and
    action-target correlation.
  - train_updates.csv, TensorBoard, console, and plotting include P3-2d fields.
  - default skill_effect_horizons changed from (5,10,20) to (3,5,10,20), while
    CLI can still override it.
  - old extractor normalizer state with mismatched target dimension is skipped
    during load instead of crashing.

Validation:
  - in-memory compile passed for touched files.  Normal py_compile was blocked
    by a Windows __pycache__ permission/lock, not a syntax error.
  - smoke passed at logs/ha_ctse_process_smoke_p3_2d.
  - tiny S7-S1 train passed at logs/ha_ctse_process_p3_2d_tiny_train.
    CSV contained effect_observed_* fields, end/window availability, and reward
    guards stayed zero.
```

Next:

```text
Run a P3-2d reward-off probe on S7-S1, 16 envs, 320k steps.  The gate is not
task reward; it is whether the revised targets produce non-shortcut positive
effect gain and whether observed target skill L2 / action-target correlation
become meaningful.

Round 7 correction:
  P3-2d is the final reward-off free-signal audit, not a permanent blocker for
  HMASD-like forcing.  If P3-2d is positive, proceed through P3-3 before P3-4.
  If P3-2d is negative, stop passive reward-off target tweaking and design P3-4
  as an active low-only forcing loop with warmup, shortcut residual/kill-switch,
  and usefulness coupling.
```

Decision rule:

```text
If action/effect intervention distances are near zero:
  fix z -> low-level behavior coupling before any reward, e.g. stronger skill
  conditioning, skill-conditioned recurrent state reset/gating, or auxiliary
  low-level skill-use objective.

If action intervention is nonzero but predicted/observed effect intervention is
near zero:
  revise effect targets, horizons, and extraction; the policy may use z but the
  probe is measuring the wrong outcome.

If both action and predicted/observed effect intervention are clearly nonzero:
  return to P3-3 shortcut/usefulness audits, then consider P3-4 low-only
  intrinsic.
```

### P3-2e skill-conditioning capacity audit

P3-2e is the cheap architectural check requested by the Round 7 advice.  It
should be done before spending effort on a stronger intrinsic reward.

Question:

```text
Is z_i only a weak one-step action nudge, or can the current low-level actor use
z_i as a persistent behavior-mode gate?
```

Implementation options:

```text
1. Inspect skill-conditioning / FiLM magnitudes in the low actor.
2. Estimate actor-output variance explained by z_i versus observation features
   under matched local observations.
3. Run short forced-z rollout snippets from matched reset states or replayed
   observation histories and measure trajectory-level spread, not only one-step
   action_l2.
```

Decision:

```text
If z-conditioned trajectory spread is weak:
  improve low-level skill conditioning before P3-4, e.g. stronger FiLM/gating,
  skill-conditioned recurrent state, or an auxiliary low-level skill-use loss.

If z-conditioned trajectory spread is present:
  proceed to P3-3/P3-4 with-force design.
```

Scope cap:

```text
P3-2e must not become another long reward-off research branch.  Its purpose is
only to prevent applying a forcing reward to an actor that cannot express
persistent skill-conditioned behavior.  If the audit shows nontrivial
trajectory-level z effect, proceed directly to P3-4 design.
```

### Round 7 forcing-loop correction

The old P3 transition was too conservative:

```text
old: only inject reward after positive reward-off effect gain.
```

The corrected transition is:

```text
reward-off probes verify data plumbing, target availability, shortcut heads,
and z->actor capacity.  They do not have to show stable semantics before any
force exists.

P3-4 should be tested as a controlled with-force loop:
  force = skill-effect control/decodability signal
          - duration/reward/context/agent/phase shortcut signal
  low reward only, micro-window distributed
  warmup before application
  small coefficient and clipped/centered reward
  no direct communication metrics and no direct environment-reward-as-intrinsic
  high-level target may still use skill-period cumulative environment reward
  optional annealed duration-entropy bonus for high-level duration exploration
  kill-switch if shortcut heads dominate or task metrics regress
```

Chosen first implementation: 3+1 forcing reward.

```text
R_force =
    w_disc   * R_disc_residual
  + w_effect * R_effect_residual
  + w_durent * duration_entropy_annealed

R_disc_residual =
    log q_disc(z | effect_window, context-controlled features)
  - max(log q_duration(z | duration/length),
        log q_reward(z | reward_sum),
        log q_phase_agent(z | phase, agent_id),
        log q_context(z | context-only))

R_effect_residual =
    log p_full(y | x, z) - log p_base(y | x)
```

Implementation deliverables:

```text
new or extended module:
  ha_ctse_process/skill_effect_discovery.py
    ResidualSkillDiscriminator
    ShortcutSkillHeads
    SkillEffectIntrinsicComposer

config / CLI:
  enable_skill_forcing_reward = false
  skill_force_disc_coef
  skill_force_effect_coef
  skill_force_duration_entropy_coef
  skill_force_warmup_steps
  skill_force_clip
  skill_force_shortcut_margin
  skill_force_kill_on_shortcut = true

metrics:
  force_reward_low_mean
  force_reward_applied_steps
  force_disc_loss
  force_disc_acc
  force_disc_residual_mean
  force_effect_residual_mean
  force_shortcut_best_acc
  force_shortcut_margin
  force_gate_active
  force_gate_reason
```

Implemented first pass on 2026-07-01:

```text
Code:
  ha_ctse_process/skill_effect_discovery.py
    ResidualSkillDiscriminator
    ShortcutSkillHeads
    SkillEffectIntrinsicComposer
    force_* metrics
    micro-window reward return for low-only injection

  ha_ctse_process/standalone_agent.py
    applies force micro-window rewards over rollout_indices when gate is active

  ha_ctse_process/config.py / train.py
    --enable_skill_forcing_probe
    --enable_skill_forcing_reward
    --skill_force_reward_injection none|low_only
    --skill_force_disc_coef
    --skill_force_effect_coef
    --skill_force_duration_entropy_coef
    --skill_force_warmup_steps
    --skill_force_clip
    --skill_force_shortcut_margin
    --disable_skill_force_shortcut_gate
    --skill_force_use_comm_fields

  ha_ctse_process/plotting.py
    ha_ctse_skill_forcing_reward.png
    eval_success_fractions.png

  ha_ctse_process/smoke.py
    forcing probe reward-off guard

  ha_ctse_process/train.py / eval_checkpoints.py
    eval success diagnostics:
      coverage_eq1_step_fraction
      coverage_eq1_episode_fraction
      coverage_final_eq1_episode_fraction
      zero_throughput_episode_fraction
      throughput_gt5_step_fraction

  scripts/analyze_p3_4_forcing.py
    offline readout for downloaded cloud logs; compares reward_pure,
    force_probe, force_disc_only, force_disc_effect, and optional arms by
    force_* tail means, lifetime collapse diagnostics, and coverage==1.0
    step fraction.  It is analysis-only and does not change training.

Validation:
  syntax compile via in-memory compile: passed
  python -m ha_ctse_process.smoke --log_dir logs\ha_ctse_smoke_p3_force: passed
  1-update sync CLI smoke with --enable_skill_forcing_probe: passed
  2026-07-01 readout support AST parse: passed
  2026-07-01 analyze_p3_4_forcing.py compatibility check on old P3-2d logs: passed

Default behavior:
  reward injection remains off unless --enable_skill_forcing_reward is passed.
  forcing reward uses action + motion/energy effect fields by default;
  communication/topology fields remain diagnostics unless
  --skill_force_use_comm_fields is explicitly passed.
  duration entropy coefficient is currently logged as a force diagnostic entry,
  not incorrectly injected as a low-level constant reward.  A proper high-level
  duration entropy loss/anneal remains a separate follow-up if needed.
```

Ablation knobs:

```text
disc_only:    w_disc > 0, w_effect = 0
effect_only:  w_disc = 0, w_effect > 0
3plus1:       w_disc > 0, w_effect > 0
no_durent:    w_durent = 0
durent_on:    annealed w_durent > 0
```

User priority 2026-07-01:

```text
Forcing reward is the load-bearing mechanism.  Passive reward-off probes can
debug data paths, but the algorithm will not become HMASD-like until a dense
intrinsic force trains skill discovery and differentiation.  Treat P3-4 as the
mainline implementation objective, not an optional later add-on.
```

Duration entropy note:

```text
Use duration entropy only as an annealed exploration bonus, not a permanent
uniform-duration objective.  It should prevent early fixed-duration collapse
while allowing context-dependent duration specialization later.

Required diagnostics:
  duration_entropy trajectory
  duration_usage_entropy
  lifetime_heterogeneity
  renewal_full_sync_rate
  duration_agent_mi
```

### Round 8 hardening response

Round 8 external audit found two decision-relevant issues in the shipped P3-4
first pass:

```text
1. The discriminator reward is shortcut-residualized, but the effect term is
   currently raw `log p_full(y|x,z) - log p_base(y|x)`.  Duration/reward
   baseline gains are computed as diagnostics but not subtracted before reward
   composition.

2. The current P3-4 batch can test whether forcing opens, but it cannot prove
   the decoupled-lifetime claim because it lacks a fixed-duration + same-forcing
   control.
```

Immediate action items before trusting `force_disc_effect` or making an
algorithmic decoupling claim:

```text
P3-4c: Residualize the effect reward input.
  Compose with a duration/reward-residual effect term:
    logp_full - max(logp_base, logp_duration, logp_reward)
  or an equivalent conservative residual that cannot be explained by
  duration/reward shortcuts.

P3-4d: Add fixed-duration forcing control.
  Run the same clean forcing condition, at least `disc_only`, under a
  single-duration candidate set such as (7,).  This separates "forcing helps"
  from "decoupled lifetimes help".
```

Interpretation update:

```text
Already-running pre-fix cloud arms remain useful with caveats:
  reward_pure: valid control
  force_probe: valid reward-off forcing diagnostics
  force_disc_only: valid first clean forcing signal
  force_disc_effect: exploratory only if it used the raw effect term
```

Hazard-SMDP trigger:

```text
If shortcut heads keep matching or exceeding the discriminator across
`disc_only` and a revised residual discriminator/effect path, stop adding
ad-hoc shortcut heads and revisit the hazard-SMDP alternative as a structural
way to remove duration-as-label confounding.
```

### Round 10 / GPT review synthesis: cooperative half before more individual forcing

The updated Claude and GPT reviews agree on a stronger correction:

```text
P3-4 individual residual forcing is necessary but not sufficient.
HMASD's cooperative success also used a live team context, team-level
distinguishability, and complementary high-level assignment.
```

Accepted reordered near-term work:

```text
P3-2e: Forced-z trajectory-spread capacity audit.
  Implement/read a short audit that measures whether z_i induces persistent
  trajectory-level behavior modes, not only one-step action_l2.

P3-4c: Residualize the effect reward input.
  Keep this correctness fix, but do not treat it as the only next direction.

P3-4d: Fixed-duration + same-forcing control.
  Required before any decoupled-lifetime claim.

P4-0: Cooperative diagnostics.
  Add pairwise g-intervention KL/TV on pi_z, co-edit skill redundancy, induced
  effect overlap, and teammate-churn / async-confound metrics.  These are
  diagnostics first, not reward terms.

P4-1: Live-g revival gate.
  A team/joint discriminator or g-conditioned complementarity reward is not
  trustworthy while g remains decorative.  Gate team-conditioned mechanisms on
  g intervention sensitivity moving above the historical decorative band.  This
  is not only a diagnostic: implement or verify an actual g training path.
  Supervised CE/NLL for q_team trains only the discriminator and does not revive
  g.  Valid g-revival paths are:
    1. high-level PPO reward from a generic team/joint discriminator
       (R_team = log q(g | joint_effect) - max(shortcuts)), where the resulting
       advantage updates log pi_g / bridge and joint skill-duration-edit policy;
    2. decision-level differentiable usage loss,
       I(g; joint skill/duration/edit decisions | context);
    3. both.
  If the bridge is deterministic, confirm whether any differentiable auxiliary
  reaches the bridge; otherwise no policy-gradient path exists for g.

P4-2: Complementarity mechanism.
  Start with default-off co-edit non-redundancy / repulsion diagnostics or loss;
  design an autoregressive-over-editing-subset assignment path as the more
  HMASD-faithful target.

P4-3: Team/joint discriminator.
  Design a high-level team/joint distinguishability term using joint-state or
  effect-embedding windows.  Keep communication/backhaul metrics diagnostic by
  default; any topology/role geometry must be an explicit ablation.
```

Immediate P4-1 audit task:

```text
Answer in code before implementation:
  - Does any current loss/reward update pi_g or the bridge because g induced
    joint behavior?
  - Is the bridge stochastic with log pi_g in high-level log-probs, or
    deterministic with no policy-gradient path?
  - If a team/joint discriminator exists, does its output only train q, or does
    log q(g|joint_effect) become a pre-update intrinsic reward for high-level PPO?

If the answer is "no live path", add `ha_ctse_process/g_info_objective.py` with
default-off logging/auxiliary support:
  g_use_mi_skill
  g_use_mi_duration
  g_use_mi_edit
  g_use_loss
  g_itv_kl_skill
  g_itv_kl_duration
  g_itv_kl_edit

The first implementation may use a small warmup-gated, annealed coefficient and
must not feed `g` or `c` directly to the low-level actor.
```

2026-07-01 implementation status:

```text
P4-1 / G2 Stage A implemented.

Audit answer:
  - current stochastic bridge samples g and stores log pi_g shares in high-level
    segment log-probs, so high-level PPO can update pi_g/bridge if g-dependent
    intrinsic or environment advantage exists;
  - prior `g_intervention_*` metrics were no-grad diagnostics and only checked
    skill logits, not duration/edit, so they did not revive g;
  - no current team/joint discriminator reward updates pi_g because of induced
    joint behavior.

Code added:
  - `ha_ctse_process/g_info_objective.py`
  - `use_g_info_diagnostic` default-on diagnostics
  - `enable_g_info_objective` default-off high-level usage loss

Metrics added:
  - g_itv_kl_skill / g_itv_tv_skill
  - g_itv_kl_duration / g_itv_tv_duration
  - g_itv_kl_edit / g_itv_tv_edit (currently zero because edit is not a
    separate stochastic head)
  - g_joint_assignment_distance
  - g_info_skill_mi / g_info_duration_mi / g_info_edit_mi / g_info_total_mi
  - g_info_loss / g_info_objective_active / g_info_coef_scale
  - empirical team_code_duration_mi, team_code_edit_mi, g_usage_entropy,
    g_usage_max_frac

Important boundary:
  - no raw communication reward;
  - no low-level actor g/c input;
  - no team/joint discriminator reward yet.
```

2026-07-02 G2 Stage-A experiment readout.

```text
Experiment: EXP-20260701-g-info-objective-probe
Control: diagnostic-only g-info, 320k, S7-S1, 16 envs.
Treatment: same run plus --enable_g_info_objective with
  g_info_coef_skill=0.01 and g_info_coef_duration=0.01.

Result:
  The small objective failed to revive g.  At 320k the treatment stayed below
  the diagnostic-only band:
    g_info_skill_mi: 0.000458 vs 0.000849
    g_info_duration_mi: 0.000545 vs 0.001216
    g_itv_tv_skill: 0.024752 vs 0.032638
    g_itv_tv_duration: 0.023897 vs 0.034676
    g_joint_assignment_distance: 0.024325 vs 0.033657
  coverage_eq1_step_frac stayed 0.0 in both runs.

Interpretation:
  G2 Stage-A, as currently scaled, is too weak to be a g reviver.  It should not
  unlock P4 team/joint discriminator or team-conditioned P3 forcing.  This is
  not yet a proof that g-revival is impossible: high_opt includes compact,
  bridge, and high parameters, so the likely immediate issue is loss magnitude
  and/or objective formulation.  The logged treatment g_info_loss is only about
  -1e-5 because MI is ~5e-4 and the coefficients are 0.01.

Next stage: P4-1b / G2 hardening.
  - Add diagnostics for raw g-info objective magnitude and its ratio to high
    PPO loss.
  - Add/verify gradient diagnostics for bridge/code embedding and high-policy
    heads under the g-info objective.
  - Run a short controlled gradient probe before another long experiment.
  - Only after that run a coefficient or normalization sweep, e.g. stronger
    coefficients or normalized target scale, while checking skill/duration
    collapse.
```

2026-07-02 P4-1b diagnostics implemented (first pass).

> REVERTED 2026-07-02: the user scoped the CC/Cowork agent to
> cross-validation/advice only, so all code described in this block was removed
> and `scripts/run_p4_1b_grad_probe_local.ps1` deleted; files are back to their
> pre-P4-1b state.  The SCALE AUDIT below still stands (it is a code read, not
> code): g_info_loss ~ 1e-5 vs PPO terms O(0.1-1) at coef=0.01.  The block is
> retained as the reference design if Codex reimplements the probe; the
> experiment design lives in `ExpRecord.md` -> `EXP-20260702-p4-1b-grad-probe`
> (status CODE REVERTED).

```text
Scale audit (code read, standalone_agent.py update_high_from_segments):
  g_info_loss is added directly to policy_loss + 0.5*value_loss + entropy_loss
  + aux_loss.  With coef=0.01 and MI ~5e-4 the term is ~1e-5, i.e. 4-5 orders
  of magnitude below the PPO terms.  The negative Stage-A result is therefore
  consistent with a pure scale failure; the gradient PATH itself (compact ->
  bridge.code_embedding -> high.logits) exists and is now measured directly.

Code added (diagnostic-only; no objective/reward semantics changed):
  - g_info_objective.py: unit-weighted differentiable MI probe
    (last_probe_objective, reset each forward), new metric fields
    g_info_objective_raw (coef-weighted MI before anneal scale) and
    g_info_loss_ratio placeholder.
  - standalone_agent.py: P4-1b gradient probe before backward with
    retain_graph: autograd.grad of the unit-weighted MI on bridge/high/compact
    parameter groups, plus autograd.grad of policy_loss on bridge/high as the
    PPO reference.  New metrics:
      g_info_grad_norm_bridge / _high / _compact
      g_info_ppo_grad_norm_bridge / _high
      g_info_grad_ratio_bridge / _high
      g_info_loss_ratio (|g_info_loss| / sum |PPO loss terms|)
  - config.py: use_g_info_grad_diagnostic=True (default on; two extra grad
    passes per high-level update).
  - train.py: --disable_g_info_grad_diagnostic, manifest field, GInfo/* TB
    scalars, console fields (g_loss_ratio, g_grad_br, g_grad_hi, ratios).
  - plotting.py: fields flow to CSV via G_INFO_METRIC_FIELDS; grad/loss ratio
    lines added to process diagnostics plot.
  - scripts/run_p4_1b_grad_probe_local.ps1: one-key short probe
    (default 32k / 16 env): grad_diag arm (diagnostic-only) and
    grad_obj_strong arm (coef 1.0 skill+duration, warmup 0) to verify the
    loss-ratio metric responds; runs smoke first; decision rule in header.

Validation:
  - syntax compile passed for all five touched files (sandbox);
  - static metric-field consistency check passed (all 9 new fields defined in
    G_INFO_METRIC_FIELDS, produced by module or agent, and logged in train.py);
  - runtime smoke/tiny-train NOT yet run: sandbox lacks torch (proxy-blocked
    pip) and PowerShell; must run locally under the SB3 conda env via
    scripts/run_p4_1b_grad_probe_local.ps1 (-DryRun first).

Pre-committed decision rule for the probe read:
  grad ratios << 1e-2 with nonzero grad norms -> scale failure confirmed; run a
    normalized/stronger coefficient sweep targeting g-info/PPO gradient ratio
    ~1e-2..1e-1 (not a blind coefficient ladder).
  bridge grad norm ~= 0 -> path failure; fix wiring (code_embedding not reached
    by the MI probe) before any sweep.
  grad ratio already ~1e-1 in grad_obj_strong at 32k, and a follow-up 320k
    strong run still shows no MI movement -> objective-form failure; stop
    coefficient work and escalate to the team/joint discriminator intrinsic
    reward path (G2 option (a)).
```

2026-07-02 OPT-specific correction to P4-1b/P4-1c.

```text
External review corrected the framing: OPT already supplies a descriptive
interaction basis, so g must be a controllable prototype-response code, not a
duplicate of c_tau or of OPT aggregation weights.

Current code check:
  - `InteractionCompactEncoder` computes and returns prototype weights
    (`weights`, i.e. omega_tau).
  - High-level update currently discards those weights as `_weights` in several
    places, including the g-info update path.
  - `GInfoObjective` currently conditions on compact c_tau and enumerates g,
    but it does not explicitly log/use omega_tau, prototype memberships, or
    OPT-shortcut baselines.
  - P4-1b gradient diagnostics are useful but only answer scale/path.  They do
    not prove that g is a prototype-response variable rather than an OPT-context
    duplicate.

Revised next stage: P4-1b/P4-1c OPT-conditioned g hardening.

Deliverables:
  1. Expose omega_tau from `self.compact(...)` through high-level segment/update
     code instead of discarding it.
  2. Log omega diagnostics:
       opt_weight_entropy
       opt_weight_max_frac
       opt_weight_usage_mean/std per prototype
       opt_weight_change / membership churn when available
  3. Extend GInfoObjective to accept omega_tau and report that diagnostics are
     conditioned on fixed (c_tau, omega_tau).
  4. Add shortcut baselines before trusting P3/P4 rewards:
       q_opt(z | c, omega)
       q_opt_g_prior(z | c, omega, g)
       q_opt(g | c, omega)
  5. Only after scale/gradient diagnostics and omega-conditioning are verified,
     run a stronger or normalized g-info objective sweep.

Do not proceed to team/joint discriminator while g remains decorative.  Do not
turn g into a direct topology-role classifier or communication metric.  P4 team
effect windows may use future OPT-pattern evolution, joint dynamics, and pooled
effect embeddings, but not default backhaul/coverage/recovery fields.
```

Interpretation rule:

```text
force_disc_acc up + shortcut gap positive + task metrics flat
  => "distinguishable but not cooperative/useful";
     move to P4 cooperative-half mechanisms, not just larger individual
     discriminator coefficients.
```

With-force success criteria:

```text
effect gain / behavioral differentiation rises;
skill selection entropy moves away from inert max-uniform use;
duration/reward shortcut advantage does not widen;
coverage/throughput/reward variance do not regress;
chain-formed fraction improves or remains stable.
```

Stage A fail rule:

```text
If p_full(y|x,z) does not beat p_base(y|x), or gain is explained mainly by
duration/reward/phase shortcuts, do not inject reward. Fix effect target or
context baseline first.
```

Stage B: low-only intrinsic.

```text
process_effect_reward_injection = low_only
P2-lite = off initially
high intrinsic = off
```

Accept only if:

```text
skill-effect gap increases
skill usage does not collapse
duration shortcut does not worsen
coverage/QoS/throughput do not regress
reward variance does not increase
credit_full_disconnect does not worsen
```

Stage C: P3 + P2-lite.

```text
P3 low-only skill-effect intrinsic
+ high-level SMDP target with skill-period cumulative environment reward
+ optional separate intrinsic terms only if they are not raw communication
  indicators and pass shortcut/domain-bias checks
```

Expected interpretation:

```text
P3 creates controllable skill effects.
High-level cumulative environment return selects useful effects over a skill
lifetime.  Intrinsic terms create semantics; environment return supplies task
usefulness without being relabeled as intrinsic reward.
```

Stage D: variable-lifetime ablation.

```text
Under the same P3/P2 condition:
  fixed/shared lifetime
  vs per-agent variable lifetime
```

Claim support requires:

```text
variable lifetime improves task metrics and variance
AND lifetime_heterogeneity / duration_agent_mi / renewal metrics show
nontrivial, context-dependent lifetime use.
```

Directions to stop or demote:

```text
raw q(z | segment) coefficient tuning
transition discriminator shortcut-head escalation
topology-role classifier reward revival
g directly fed to low-level actor
backhaul/recovery-only optimization without task-metric improvement
skill entropy as a proxy for successful skill discovery
```

Metrics (decision-driving + to add):
- primary: `credit_full_disconnect_mean` (down), `credit_recovery_rate` (up),
  fraction of eval episodes with throughput above a backhaul-up threshold
  (chain-formed fraction), `reward_std/reward_mean` (down);
- secondary: coverage, qos, throughput, g_itv, seg_len, switch_rate,
  duration_entropy;
- ADDED: throughput conditioned on backhaul-connected is now logged by eval as
  `backhaul_connected_step_fraction` and
  `throughput_when_backhaul_connected_mbps`; checkpoint sweeps export these as
  `backhaul_connected_fraction` and
  `throughput_when_backhaul_connected_mbps`.  Training updates also export
  `credit_backhaul_connected_step_fraction` and
  `credit_throughput_when_backhaul_connected_mbps`.  These metrics are
  step-conditioned and use actual backhaul-served users, not only the final
  `full_network_disconnect` flag.
- still to add: `return_by_duration` / `full_disconnect_by_duration`; recovery
  latency distribution (steps-to-reconnect).

## Files To Modify

- `config_1.py`: add HA-CTSE config fields and ablation switches.
- `hmasd/baselines.py`: register algorithm and ablation names.
- `hmasd/agent.py`: create optional HA-CTSE high-level module, route
  high-level assignment/update through it when enabled, maintain per-agent
  skill ages, and preserve original path otherwise.
- `hmasd/utils.py`: add rollout fields for compact, team code, edit masks,
  ages, candidate skills, and high-level log-probabilities.
- `tests/`: add focused unit tests for HA-CTSE components and buffer fields.

## New Modules To Add

- `hmasd/ha_ctse.py`: clean implementation of:
  - `OPTCompactExtractor`;
  - `CompactTeamBridge`;
  - `HorizonSkillEditor`;
  - `HACTSEOutput` data container.

## Config Fields

Core:

- `use_opt_compact`
- `opt_compact_dim`
- `opt_num_prototypes`
- `opt_use_sparsemax`
- `opt_use_cd_loss`
- `opt_use_cmi_loss`
- `opt_cd_coef`
- `opt_cmi_coef`
- `use_compact_in_low_level_actor`
- `use_team_bridge`
- `team_bridge_type`
- `team_code_dim`
- `num_team_codes`
- `use_horizon_window`
- `horizon_type`
- `H_min`
- `H_max`
- `force_termination_after_H_max`
- `edit_penalty_alpha`
- `switch_penalty_beta`
- `early_switch_penalty_eta`
- `age_penalty_power`
- `term_entropy_coef`
- `skill_entropy_coef`
- `high_level_assignment_mode`

Discriminator placeholders:

- `use_team_code_discriminator`
- `use_individual_skill_discriminator`
- `discriminator_condition_on_compact`
- `discriminator_condition_on_team_code`
- `use_segment_discriminator`
- `intrinsic_coef_team`
- `intrinsic_coef_skill`
- `intrinsic_warmup_steps`

## Buffer Fields

Add to `RolloutBuffer`:

- `compact`
- `team_code`
- `log_prob_team_code`
- `entropy_team_code`
- `active_skill_prev`
- `active_skill`
- `candidate_skill`
- `skill_age_prev`
- `skill_age`
- `requested_edit_mask`
- `executed_edit_mask`
- `log_prob_term`
- `log_prob_skill`
- `duration_candidate`
- `duration_target`
- `duration_remaining`
- `log_prob_duration`
- `entropy_term`
- `entropy_skill`
- `entropy_duration`
- `initial_assignment_mask`

Add process segment storage outside the PPO tensor buffer:

- `SkillProcessSegmentBuffer`
- active segment key: `(env_id, agent_id)`
- segment label: executed active skill, not candidate skill
- segment context: team code and compact vector at segment start
- segment payload: observation/action/reward/done/next-observation sequences

## Logging Fields

First implementation returns these in `update_info` where available:

- `avg_requested_edits`
- `avg_executed_edits`
- `avg_switched_agents`
- `no_edit_rate`
- `full_sync_rate`
- `suppressed_edit_rate`
- `initial_assignment_rate`
- `skill_age_mean`
- `H_min_masked_edit_rate`
- `H_max_forced_termination_rate`
- `termination_rate`
- `lifetime_heterogeneity`
- `compact_norm_mean`
- `compact_norm_std`
- `opt_cd_loss`
- `opt_cmi_loss`
- `opt_aggregation_entropy`
- `team_code_entropy`
- `duration_policy_entropy`
- `duration_remaining_mean`
- `duration_target_mean`
- `duration_target_histogram`
- `process_segments_open`
- `process_segments_completed`
- `process_segment_length_mean`
- `process_segment_length_max`
- `process_duration_target_histogram`

## Test Checklist

Unit tests:

1. `test_original_hmasd_runs`
2. `test_opt_compact_shape`
3. `test_bridge_shape`
4. `test_initial_skill_assignment`
5. `test_no_edit_preserves_skill`
6. `test_edit_replaces_skill`
7. `test_age_increment_on_no_edit`
8. `test_age_reset_on_edit`
9. `test_H_min_action_masking`
10. `test_H_max_force_or_bias_termination`
11. `test_logprob_matches_executed_mask`
12. `test_candidate_skill_not_used_when_no_edit`
13. `test_discriminator_uses_active_skill`
14. `test_low_level_actor_no_compact_by_default`
15. `test_rollout_buffer_contains_required_fields`
16. `test_high_level_ppo_backward`
17. `test_low_level_ppo_backward`
18. `test_discriminator_backward`
19. `test_one_rollout_one_update`
20. `test_ablation_configs_load`

## Smoke Commands

Use the small smoke config first:

```powershell
python train_multiproc_config_1.py --config config_test --algorithm hmasd_original --num_envs 1 --rollout_length 16 --total_timesteps 16 --disable_eval --console_log_level error
python train_multiproc_config_1.py --config config_test --algorithm horizon_ctb_sse_core --num_envs 1 --rollout_length 16 --total_timesteps 16 --disable_eval --console_log_level error
```

Ablation commands follow the same shape with:

```text
opt_mappo_k
opt_full_sync_skill
ctb_sse_no_horizon
horizon_ctb_sse_no_discriminator
horizon_ctb_sse_compact_low_level_ablation
deterministic_bridge
stochastic_bridge
parallel_editor
autoregressive_editor
```

## Current Documentation Status

As of 2026-06-23:

| Document | Stage | Current role |
| --- | --- | --- |
| `ATTENTION_POINTER.md` | Active pointer | First-read navigation layer. Points to the current principle section, plan stage, advice entries, experiments, and code focus. Update it after every task when focus or next action changes. |
| `ALGORITHM_PRINCIPLES.md` | Stable contract | Defines the scientific and implementation invariants. Use it to decide whether a code change is allowed. |
| `ALGORITHM_KNOWLEDGE_BASE.md` | Stable compact memory | Short reference for what HA-CTSE is and what claims are allowed. Use it before writing experiment text or summaries. |
| `IMPLEMENTATION_PLAN.md` | Active tracker | Tracks code status, partial implementations, next changes, commands, and continuation prompts. Keep this file current after each coding pass. |
| `ExpRecord.md` | Experiment ledger | Record every planned local/cloud experiment before launch: name, time, location, purpose, metrics to read, outcome meanings, and next decision. |
| `C:\Users\wu\.codex\skills\long-task-memo` | Codex workflow skill | General LongTaskMemo workflow for reading/updating attention pointer, principles, plan, ExpRecord, advice, and then aligning code or experiment work with the active stage. |

LongTaskMemo completion rule: after every task, update the affected memory files
and `ATTENTION_POINTER.md` before final response.  If no memory update is needed,
explicitly confirm that the pointer remains accurate.

Update on 2026-06-24: implementation moved beyond the first pass. The core
HA-CTSE path, stochastic bridge, autoregressive editor, compact-conditioned
discriminators, TensorBoard metric routing, and low-level compact ablation path
now have executable code paths and focused tests/smoke checks.

## Standalone Process-Core Separation

Update on 2026-06-24 evening: the active implementation direction has changed.
The new algorithm is no longer to be trained as a mixed `hmasd.agent` variant.
HMASD remains a source of inspiration and a comparison baseline, but its
discriminator/discoverer/coordinator training components must not define the
new algorithm's target.

Current standalone package:

- `ha_ctse_process/config.py`: standalone algorithm defaults. It inherits
  environment/scenario preset machinery from `config_1.py`, but owns all new
  process-core algorithm hyperparameters locally.
- `ha_ctse_process/env_factory.py`: reuses the existing environment adapters
  without importing HMASD agent code.
- `ha_ctse_process/collectors.py`: standalone sync/subproc environment
  collectors. Subprocess workers only execute env `reset/step`; policy
  inference and all learning state remain in the main process.
- `ha_ctse_process/process_outcomes.py`: extracts process-level outcome vectors
  from segment transitions and Scenario 7 reward-info fields.
- `ha_ctse_process/standalone_agent.py`: owns high-level skill-duration policy,
  low-level policy, process encoder, multi-env segment manager, process reward,
  high-level update, and low-level update. It has no discriminator objective.
- `ha_ctse_process/train.py`: owns standalone train/eval/checkpoint flow.
- `ha_ctse_process/smoke.py`: lightweight smoke checks that write
  `smoke_result.json` into a log directory.
- `ha_ctse_process/plotting.py`: standalone CSV/PNG export. Metric selection
  follows HMASD Scenario 7 conventions for UAV plots: coverage, QoS,
  throughput, battery, return safety, charging progress, and process-core
  diagnostics.
- `ha_ctse_process/README.md`: boundary note for future work.

Completed standalone training integration:

- Default training config is now `ha_ctse_process.config`, not `config_1`.
- New algorithm files live under `ha_ctse_process/`. Do not add new
  process-core algorithm modules under `hmasd/`.
- The training log is mirrored to `standalone_train.log` inside `--log_dir`.
- Training updates are exported to `metrics/train_updates.csv` and plotted as
  `ha_ctse_training_rewards.png`, `ha_ctse_losses.png`, and
  `ha_ctse_process_diagnostics.png`.
- Eval episodes are exported to `metrics/eval_episodes.csv` and plotted as
  `eval_reward.png`, `eval_service_quality.png`, `eval_safety_energy.png`, and
  `eval_charging_progress.png`.
- Existing standalone logs can be backfilled with:
  `python -m ha_ctse_process.plotting --log_dir <log_dir> --from_log`.
- Current standalone collection supports `--collector_backend sync` and
  `--collector_backend subproc`. The subproc backend is not a worker-side
  rollout/replay system: workers hold only environments and return one-step
  transitions to the main process.
- On-policy data purity is enforced in the synchronous path: each update builds
  a fresh `Rollout`, flushes active segments at the rollout boundary, consumes
  completed segments through `process_update(...).pop_completed()`, updates
  low/high/process modules once, then calls `reset_all_policy_state()` so active
  skills, duration counters, ages, and segment state cannot cross into the next
  policy version.
- On-policy data purity is also enforced in subproc mode because the main
  process still owns `Rollout`, `SegmentManager`, policy inference, and update
  barriers. Off-policy policy replay is explicitly out of scope for this
  branch.
- The high-level policy now conditions on global state + joint observations
  through `c_tau`, maps `c_tau` through `g_tau`, then chooses skill and discrete
  duration from `(c_tau, g_tau, o_i, z_prev_i, age_i)`.
- Checkpoint payload includes compact encoder and team bridge state dicts.
- Multi-env synchronous collection stores segment rollout indices correctly.
- Segment process reward is written back into the matching low-level rollout
  rewards before low-level PPO update.
- High-level skill/duration policy is trained from completed process segments.
- Checkpoints save and restore `high`, `low`, `process`, and all optimizer
  states.
- `--resume_from` continues standalone training from a saved checkpoint.
- `--mode eval` runs deterministic evaluation from a standalone checkpoint.
- `--eval_interval`, `--eval_episodes`, and `--eval_max_steps` support
  standalone training-time evaluation without invoking HMASD eval code.

Verified smoke commands:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.smoke --log_dir logs\ha_ctse_process_smoke_core_separated
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train --preset S7-S1 --scenario energy --n_agents 6 --num_envs 1 --total_timesteps 16 --rollout_length 16 --skill_interval 4 --device cpu --eval_interval 16 --eval_episodes 1 --eval_max_steps 8 --save_interval 1 --log_dir logs\ha_ctse_process_smoke_s7s1_6agents16
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train --preset S7-S1 --scenario energy --n_agents 6 --num_envs 2 --total_timesteps 16 --rollout_length 8 --skill_interval 4 --device cpu --collector_backend subproc --collector_start_method spawn --eval_interval 0 --plot_interval 0 --log_dir logs\ha_ctse_process_smoke_subproc_collector16
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.plotting --log_dir logs\ha_ctse_process_core_s7_320k --from_log --window 3
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train --config config_1 --scenario energy --preset S7-S3 --num_envs 2 --total_timesteps 32 --rollout_length 16 --skill_interval 10 --device cpu --save_interval 1 --eval_interval 32 --eval_episodes 1 --eval_max_steps 16 --log_dir logs\ha_ctse_process_standalone_resume_eval_smoke
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train --config config_1 --scenario energy --preset S7-S3 --num_envs 1 --total_timesteps 48 --rollout_length 16 --skill_interval 10 --device cpu --resume_from logs\ha_ctse_process_standalone_resume_eval_smoke\standalone_process_core_final.pt --eval_episodes 1 --eval_max_steps 16 --log_dir logs\ha_ctse_process_standalone_resume_eval_smoke_resume
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train --mode eval --config config_1 --scenario energy --preset S7-S3 --device cpu --resume_from logs\ha_ctse_process_standalone_resume_eval_smoke\standalone_process_core_final.pt --eval_episodes 1 --eval_max_steps 16 --log_dir logs\ha_ctse_process_standalone_resume_eval_smoke_eval
```

Next implementation stages:

1. Add standalone tests for full train/eval CLI output and log-file creation.
2. Add process-era ablation configs inside `ha_ctse_process/`, e.g.
   `process_no_reward`, `process_no_contrast`, and `process_no_outcome`.
3. Extend standalone collector profiling and optionally add shared-memory
   transfer if subproc pipe overhead becomes dominant. Do not add worker-side
   rollout replay.
4. Stop expanding `hmasd/ha_ctse.py` and `hmasd/process_exploration.py`; future
   algorithm work belongs in `ha_ctse_process/`.

## Research Operating Principle

User correction on 2026-06-24: this work is algorithm exploration, not a
conservative patch series. Do not default to minimal HMASD-preserving edits when
the stated goal is to reconstruct and test a new algorithm.

Working rules for future coding passes:

1. Treat HA-CTSE design changes as first-class research hypotheses.
2. Preserve old HMASD only as a control/baseline path, not as the default design
   pressure for the new algorithm.
3. When a change modifies HMASD exploration semantics, keep it if it is a
   coherent experimental hypothesis, then expose metrics/ablations to evaluate
   it.
4. Avoid silently "conservative-izing" the core variant. If a conservative
   variant is useful, give it an explicit ablation name or document it as a
   control.
5. For entropy, discoverer exploration, and discriminator intrinsic rewards,
   reason from the new algorithm's mechanism first, then compare against HMASD.
6. Do not keep every old structure as an ablation by default. If the process
   framework makes an old component conceptually obsolete, retire it or keep it
   only as a legacy diagnostic. Ablations should answer live questions about
   the current algorithm, not preserve all historical mechanisms.

Continuation prompt for Codex:

```text
This is algorithm exploration, not conservative maintenance. Before changing
HA-CTSE, state the research hypothesis being tested, the metrics that can
falsify it, and whether the change belongs in the core algorithm or in a named
ablation/control. Do not automatically minimize diffs toward old HMASD behavior.
```

## Principles Alignment Audit

Update on 2026-06-24: the first audit found that the code implemented the
HA-CTSE mechanics but left several exploration objectives inactive or weak.
The follow-up research-core pass now enables those objectives in
`horizon_ctb_sse_core`; long-run scientific validation is still required.

Aligned first-pass mechanics:

- `c_tau`, `g_tau`, `z_i`, and primitive action roles are separated.
- The core low-level actor keeps the HMASD invariant
  `pi_l(a_i | o_i, z_i)`.
- The compact-team bridge, deterministic and stochastic bridge modes, horizon
  skill editor, per-agent keep/edit decisions, skill age tracking, `H_min`
  masking, and `H_max` forcing have executable paths.
- High-level PPO stores and recomputes log-probabilities for executed
  decisions, not for unused candidate skills.
- Compact-conditioned team and individual discriminators are active in
  `horizon_ctb_sse_core`.
- Collapse diagnostics such as edit counts, switch counts, full-sync rate, and
  lifetime heterogeneity are logged.

Research-core corrections implemented on 2026-06-24:

- `horizon_ctb_sse_core` now uses `team_bridge_type = "stochastic"` so the
  compact-team code has a policy-gradient term. `deterministic_bridge` remains
  an explicit ablation.
- HA-CTSE presets now enable nonzero OPT pressure:
  `opt_cd_coef >= 0.02`, `opt_cmi_coef >= 0.005`, and
  `opt_aggregation_entropy_coef >= 0.005`.
- Because the current compact extractor has no recurrent history context, the
  CMI slot includes a batch prototype-usage balance proxy so prototype usage is
  actually optimized instead of silently staying at zero.
- High-level and low-level entropy now support adaptive target tracking for
  team code, keep/edit policy, edit-skill policy, and low-level actions.
- Discriminator intrinsic rewards in HA-CTSE now use prior-corrected,
  optionally normalized MI-style rewards. Uniform discriminator predictions
  produce approximately zero intrinsic reward instead of a negative raw
  log-probability penalty.
- Horizon edit and early-switch penalties are nonzero in the research core.
  Switch penalty is intentionally small and warmup-gated because switching is
  not intrinsically beneficial or harmful; it is only a temporal-abstraction
  regularizer against high-frequency skill churn.
- Scenario 7 HA-CTSE presets raise low-level entropy pressure to at least
  `lambda_l = 0.02`; the old HMASD path is preserved as a baseline path.

Still open:

- Segment-level discrimination for persistent skill windows remains pending.
  Current discriminators are still primarily next-state/next-observation
  classifiers.

Research directions to test next:

1. Compare stochastic core against `deterministic_bridge` using team-code
   entropy, team-code usage, eval return, zero-connected episodes, and full
   connected episodes.
2. Falsify horizon costs using executed edits, switched agents, full-sync rate,
   lifetime heterogeneity, persistence cycles, and eval return.
3. Tune MI reward normalization and coefficients if discriminator components
   become too small or dominate environmental reward.
4. Add a segment discriminator for persistent skill windows if single-step
   discriminators fail to explain long-lived skill behavior.
5. Tune OPT CD/CMI/aggregation entropy pressure if compact diversity or
   prototype usage still collapses.

## Ablation Budget And Retirement Rules

Research update on 2026-06-24: the process-centric redesign is a framework
change. Not every structure from HMASD or the first HA-CTSE pass deserves a
new ablation. Some old structures lose their scientific role once skill is
defined as a behavior process over `T_i`.

Keep only three classes of comparisons:

1. External baselines that answer "does the new family help at all?"
   - `hmasd_original`
   - `opt_mappo_k`
   - possibly MAPPO/heuristics for sanity checks

2. Live mechanism ablations that answer one current process-framework question.
   Examples:
   - process reward on/off;
   - process contrastive objective on/off;
   - outcome objective on/off;
   - discrete lifetime set vs learned termination, if both remain meaningful;
   - stochastic bridge vs deterministic bridge, only while team-code sampling
     is still a live hypothesis.

3. Diagnostics/control references, not full ablations.
   Examples:
   - full-sync skill renewal as collapse reference;
   - legacy discriminator accuracy as a diagnostic;
   - duration-only baseline to catch shortcut learning.

Retire or downgrade:

- `horizon_ctb_sse_no_discriminator`: once legacy MI reward is no longer core,
  this should be replaced by process-era controls such as `process_no_mi` or
  `process_no_contrast`.
- `ctb_sse_no_horizon`: if discrete/process lifetimes become the core temporal
  mechanism, removing horizon no longer asks a meaningful question.
- `opt_full_sync_skill`: keep only as a collapse/control reference, not as a
  serious process-framework alternative.
- compact-low-level actor variants: keep only as explicit bottleneck-violation
  ablations. Success there does not validate HA-CTSE's process skill mechanism.

Before adding a new ablation name, write:

```text
Question:
Expected failure mode if the component matters:
Metrics that falsify the component:
Reason this ablation is still meaningful under the process framework:
```

## Process-Centric Exploration Plan

Research update on 2026-06-24: do not assume the original HMASD discriminator
is the right exploration mechanism for HA-CTSE. Once `k` is only the high-level
check clock and each agent has its own realized skill lifetime `T_i`, the skill
is a variable-duration behavior process. The next implementation should move
from discriminator-centric exploration toward process/outcome-centric
exploration.

Core hypothesis:

```text
An executable skill z_i is useful when it induces a distinguishable and
task-relevant behavior process over its realized lifetime T_i, not merely when
a one-step discriminator can infer z_i from o_next.
```

Switch-cost interpretation:

- Switching does not have intrinsic reward by itself.
- Switch/edit penalties are only anti-churn regularizers to prevent the
  high-level policy from exploiting every check boundary as a label reset.
- They should stay small, warmup-gated, and falsified with metrics; they should
  not replace process-level learning signals.

### Current Execution Order

Updated after ablation-budget correction:

1. Move HA-CTSE process-core training into a standalone algorithm directory.
   The new core may reuse `envs`, config presets, and logging utilities, but
   must not be hosted by `hmasd.agent`.
2. Keep process-core gates disabled for `hmasd` and `hmasd_original`.
3. Implement discrete skill lifetimes as the first temporal process mechanism.
4. Implement a segment data contract and diagnostics, without adding process
   reward yet.
5. Add outcome extraction and process encoder only after segment labels,
   countdowns, masks, and duration diagnostics are verified.
6. Do not implement old-structure ablations during this pass. Retire or
   downgrade legacy variants unless they answer a live process-framework
   question.

### Stage S0: Standalone Algorithm Boundary

Status: Initial implementation complete.

The process-core algorithm now has its own directory:

```text
ha_ctse_process/
```

Current contents:

- `env_factory.py`: constructs Scenario 4/5/6/7 environments through
  `envs.pettingzoo` and `ParallelToArrayAdapter` without importing HMASD agent
  code.
- `standalone_agent.py`: independent process-core learner with skill-lifetime
  segments, process encoder, outcome prediction, contrastive skill/process
  loss, process reward redistribution, low-level PPO, and high-level
  skill/duration PPO.
- `process_outcomes.py`: standalone masked Scenario 7 process-outcome
  extraction with running normalization and environment-agnostic fallbacks.
- `train.py`: standalone training entrypoint. It does not call
  `train_multiproc_config_1.py`, `hmasd.agent`, or `hmasd.baselines`.
- The standalone entrypoint now supports synchronous multi-env collection via
  `--num_envs`, TensorBoard scalar logging, periodic checkpoints, and final
  model save.

Smoke passed:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train `
  --config config_1 `
  --scenario energy `
  --preset S7-S3 `
  --total_timesteps 16 `
  --rollout_length 16 `
  --skill_interval 10 `
  --device cpu `
  --log_dir logs\ha_ctse_process_standalone_smoke
```

Observed output included:

```text
standalone_train_start ... n_agents=8 obs_dim=365 action_dim=4 action_space_type=continuous
standalone_update ... process_segments=11 process_loss=1.823943 process_reward_mean=-0.001609 low_loss=1.685407
```

After high-level PPO integration, the standalone smoke also reports high-level
training metrics:

```text
standalone_update ... process_segments=8 process_loss=1.824659 process_reward_mean=-0.001645 high_loss=-0.029451 high_entropy=3.175052 high_return_mean=-0.120868 low_loss=5.050847
```

After synchronous multi-env/checkpoint integration, a 2-env smoke passed:

```text
standalone_train_start ... num_envs=2 n_agents=8 obs_dim=365 action_dim=4 action_space_type=continuous
standalone_update ... total_steps=32 process_segments=20 process_loss=2.314836 process_reward_mean=-0.026154 high_loss=2.935038 low_loss=3.448448
```

The smoke wrote TensorBoard events plus:

```text
standalone_process_core_update_1.pt
standalone_process_core_final.pt
```

After Scenario 7 process-outcome integration, a 2-env smoke passed with real
masked outcome availability:

```text
standalone_update ... process_segments=18 process_loss=1.836128 process_reward_mean=-0.002218 outcome_available=0.917 outcome_abs_mean=0.680953 high_loss=2.313311 low_loss=2.827643
```

This standalone path is now the implementation target. The previous
`hmasd.agent` HA-CTSE integration is a transition artifact and should not be
used as evidence for the new algorithm.

### Stage P0: Documentation And Gates

Status: Complete.

- Update `ALGORITHM_PRINCIPLES.md` so process/outcome objectives are
  first-class and single-step discriminators are auxiliary/legacy.
- Add config gates:
  - `use_process_exploration`
  - `use_discrete_skill_lifetimes`
  - `skill_lifetime_candidates`
  - `process_segment_mode`: `fixed_k`, `skill_lifetime`
  - `process_reward_coef`
  - `process_contrastive_coef`
  - `process_outcome_coef`
  - `process_reward_distribution`: `mean_over_segment`, `terminal_only`
  - `process_max_segment_len`
  - `process_use_duration_baseline`
- Keep all gates off for `hmasd`, `hmasd_original`, and non-process legacy
  presets. `horizon_ctb_sse_core` enables the process gates and now uses
  process reward in the discoverer path; disabling
  `use_process_reward_for_discoverer` is the explicit control.

### Stage P0D: Discrete Lifetime Set Design

Status: Complete first pass.

Discrete skill lifetimes are a simplifying candidate for process learning. They
turn termination from a repeated keep/edit Bernoulli decision into a duration
choice made when a skill is assigned:

```text
d_i ~ pi_duration(d | c_tau, g_tau, o_i, z_i, age_i)
T_i = d_i * k
```

Recommended first candidate set:

```text
skill_lifetime_candidates = [1, 2, 3, 5]
```

where values count high-level check intervals. For example, with `k=10`, this
means primitive durations `{10, 20, 30, 50}`.

Implementation choices:

- Add a duration head to `HorizonSkillEditor` only when
  `use_discrete_skill_lifetimes=True`.
- Store `duration_candidate`, `duration_remaining`, `log_prob_duration`, and
  `entropy_duration` in the high-level rollout fields.
- During countdown, the agent keeps the active skill without sampling edit,
  unless `allow_early_duration_termination=True`.
- At expiry, force a renewal/edit decision and sample a new skill plus duration.
- Keep the old learned termination path as a named ablation/control.

Why this helps:

- segment lengths come from a finite set, simplifying `SkillProcessSegmentBuffer`;
- process reward can be redistributed over known buckets;
- termination credit assignment is less noisy;
- full-sync churn should drop if duration choices are heterogeneous.

Risks:

- duration may become a shortcut label for skill identity;
- coarse durations may prevent necessary fast reactions;
- long buckets may delay correction in unstable S7 episodes.

Required diagnostics:

- `HA_CTSE/Duration/DurationUsage_*`
- `HA_CTSE/Duration/DurationEntropy`
- `HA_CTSE/Duration/DurationOnlyAccuracy` (pending)
- `HA_CTSE/Duration/ReturnByDuration_*` (pending outcome/reward grouping)
- `HA_CTSE/Duration/ExpiredRenewalRate` (pending)
- `HA_CTSE/Duration/EarlyTerminationRate`, if early termination is enabled
  (pending; early termination currently disabled)

Tests:

1. Duration is sampled only on initial assignment or executed edit.
2. No-edit countdown preserves the active skill and decrements remaining time.
3. Expiry forces renewal.
4. Duration log-prob is stored only for executed duration choices.
5. Duration-only diagnostic can be computed without process features.

Implemented now:

- `HorizonSkillEditor` has a duration head and returns duration candidate,
  target, remaining placeholder, log-prob, entropy, and logits.
- `HMASDAgent` maintains per-agent duration countdowns and suppresses edit
  sampling while a duration is still alive.
- Expired or initial skills are forced into renewal/edit; non-expired skills
  are forced to keep unless early termination is later enabled.
- Duration log-probs participate in the high-level PPO policy ratio only for
  executed duration choices.
- Duration fields are stored in `RolloutBuffer` and routed to TensorBoard.

### Stage P1: Segment Data Contract

Status: Complete first pass, training-ready.

Implement a process segment collection path before adding any new loss.

Files likely touched:

- `hmasd/utils.py`: add `SkillProcessSegmentBuffer` or extend
  `RolloutBuffer` with segment export helpers.
- `hmasd/agent.py`: open a per-env/per-agent segment when a skill becomes
  active; append each primitive transition; close the segment on executed edit,
  episode done, forced boundary, or rollout flush.
- `train_multiproc_config_1.py`: route relevant `reward_info` fields into the
  segment collector when available.

Minimum segment record:

```text
env_id
agent_id
skill z_i
team_code g_tau
compact c_tau at segment start
start_step
end_step
obs_seq
action_seq
reward_seq
done/mask_seq
optional reward_info/outcome_seq
```

The current implementation starts with `skill_lifetime` segments because P0D is
now active in the research core. Closed segments are now used by the process
encoder/update path; incomplete active segments are still discarded or closed
only at safe rollout/update boundaries to avoid off-policy training data.

Tests:

1. Segment opens on initial skill assignment.
2. Segment closes when an edit executes.
3. No-edit extends the active segment.
4. Initial assignment is not counted as a switch.
5. Rollout flush closes or masks incomplete segments without losing labels.
6. Candidate no-edit skills never become segment labels.

Implemented now:

- `SkillProcessSegmentBuffer` opens segments on initial assignment or executed
  edit and closes them on the next executed edit, done/reset, or max length.
- Segment labels use executed active skill and start-context team/compact code.
- Primitive transitions are appended per agent from the low-level rollout path.
- TensorBoard receives open/completed segment counts, segment length stats, and
  completed-duration histograms.
- The high-level PPO pending-sample data flow is process-aware: a k-boundary
  without a new high-level decision no longer opens or closes a PPO sample.
  Rewards keep accumulating until the selected duration is about to expire,
  the episode terminates, or collection is forced.
- `skill_changed` now means a real HA-CTSE high-level decision/done event, not
  merely `env_step % k == 0`.

Remaining inside P1:

- explicit partial-segment bootstrap support if we later decide not to discard
  incomplete active segments at update boundaries;
- return-by-duration diagnostics and `paper_data` export.

### Stage P2: Outcome Extraction

Status: Complete first pass, used by process training.

Create a task-aware but modular outcome vector. For Scenario 7, the first
outcome candidate can include:

```text
delta_coverage_ratio
delta_effective_connected_users
delta_system_throughput_mbps
delta_qos_satisfaction
delta_backhaul_margin
delta_energy_ratio
delta_distance_to_nearest_charger
charging_progress
return_pressure_change
```

Rules:

- Missing fields must be masked, not silently treated as zeros.
- Normalize outcomes with running mean/std.
- Keep an environment-agnostic fallback outcome based on state/observation
  deltas so the algorithm is not hard-coded only to Scenario 7.
- Log per-outcome availability and scale.

Implemented in this pass:

- Added `hmasd/process_exploration.py` with:
  - `SkillProcessOutcomeExtractor`
  - `MaskedRunningMeanStd`
  - stable `PROCESS_OUTCOME_FIELDS`
- `SkillProcessSegmentBuffer` now accepts `reward_info` per transition and
  attaches `outcome_vector`, `outcome_mask`, and `outcome_normalized` when a
  segment closes.
- `HMASDAgent.store_transition_batch` extracts env-level `reward_info` from
  vector-env infos and sends it into process segments.
- TensorBoard receives process outcome availability and normalized scale
  diagnostics under `HA_CTSE/ProcessOutcome/...`.
- Process outcomes feed `SkillOutcomePredictor` through masked regression and
  contribute to the process reward signal used by the discoverer.

Tests:

1. Outcome vector has stable shape with missing fields. Complete.
2. Outcome mask correctly marks unavailable metrics. Complete.
3. Normalization does not update during evaluation. Complete.
4. Scenario-agnostic fallback works for `config_test`. Complete through
   observation-delta and segment-return fallback fields.

### Stage P3: Process Encoder And Contrastive Objective

Status: Training integration first pass complete.

Add a process encoder, preferably in a new module:

- `hmasd/process_exploration.py`
  - `SkillProcessEncoder`
  - `SkillOutcomePredictor`
  - `SkillProcessContrastiveHead`

Inputs:

```text
obs_seq, action_seq, delta_obs_seq, reward_seq, mask_seq, c_tau, g_tau
```

Outputs:

```text
h_segment
predicted_outcome
contrastive logits against skill embeddings
```

Losses:

```text
L_outcome = masked regression/prediction loss for outcome vector
L_nce     = InfoNCE(segment_embedding, executed_skill_embedding)
L_process = process_outcome_coef * L_outcome
          + process_contrastive_coef * L_nce
```

The contrastive objective should use executed active skills as positives and
negatives from other skills, agents, time windows, or environments. Do not use
duration as an explicit positive feature in the first implementation.

Diagnostics:

- process contrastive accuracy
- process NCE loss
- outcome prediction loss by field
- per-skill outcome mean/std
- duration-only baseline accuracy
- segment length distribution

Implemented in this pass:

- `SkillProcessEncoder`: masked per-step MLP plus masked pooling over
  `(obs, action, delta_obs, reward)` segment sequences.
- `SkillOutcomePredictor`: masked outcome regression head.
- `SkillProcessContrastiveHead`: InfoNCE-style segment-to-executed-skill
  alignment.
- `process_positive_skill_labels`: uses executed segment `skill` labels and
  ignores candidate/no-edit fields.
- `duration_only_baseline_accuracy`: diagnostic majority-vote baseline that
  detects duration shortcut risk independently from the encoder.

Training integration implemented:

- `HMASDAgent` owns `SkillProcessEncoder`, `SkillOutcomePredictor`,
  `SkillProcessContrastiveHead`, and `process_optimizer` when process
  exploration is enabled.
- `HMASDAgent.update` trains process modules from closed on-policy process
  segments before the discoverer PPO update.
- `L_process = process_outcome_coef * L_outcome +
  process_contrastive_coef * L_nce` is optimized directly.
- The process reward signal combines contrastive skill/process evidence and
  masked outcome-prediction error, then writes `reward_process` into
  `RolloutBuffer` before discoverer GAE is computed.
- `process_reward_distribution=mean_over_segment` is the default so a
  segment-level signal is spread across primitive discoverer steps instead of
  appearing only at termination.

Tests:

1. Variable-length masks keep padded steps from affecting embeddings. Complete.
2. Gradients flow into process encoder and skill embeddings. Complete.
3. Duration-only baseline can be computed independently. Complete.
4. Positive labels are executed skills only. Complete.

### Stage P3D: Discoverer Process Training Contract

Status: Complete first pass.

During process reward integration, explicitly re-audit the low-level
discoverer. In the process-centric view, the discoverer is not merely the old
HMASD executor trained by discriminator reward. It is the module that realizes:

```text
z_i -> behavior process over T_i
```

Core contract:

- Keep `R_Actor` unchanged in the core path:

  ```text
  pi_l(a_i | o_i, z_i)
  ```

- Do not feed `c_tau`, `g_tau`, outcome vectors, or segment embeddings directly
  into the low-level actor outside explicit ablations.
- Low-level actor entropy should be adaptive and evaluated against process
  diversity, not just instantaneous action randomness.
- Low-level critic conditioning must be reviewed separately from actor inputs.
  A critic may use richer centralized context only if it does not bypass the
  actor-side skill bottleneck and is covered by tests.
- The process reward should train the discoverer to make skills produce
  coherent trajectories over their realized lifetimes.

Implementation tasks:

1. Add an explicit reward-component contract for the discoverer:

   ```text
   low_level_reward =
       env_component
     + legacy_mi_component
     + process_outcome_component
     + process_contrastive_component
     + optional_uncertainty_component
   ```

2. Add config gates:

   - `use_process_reward_for_discoverer`
   - `legacy_mi_reward_coef`
   - `process_reward_warmup_steps`
   - `process_reward_clip`
   - `discoverer_entropy_target_mode`
   - `disable_discriminator_training`
   - `disable_discriminator_rewards`

3. Log discoverer-specific process diagnostics:

   - `HA_CTSE/Discoverer/ProcessReward`
   - `HA_CTSE/Discoverer/LegacyMIReward`
   - `HA_CTSE/Discoverer/ActionEntropyTarget`
   - `HA_CTSE/Discoverer/ActionEntropyCoef`
   - `HA_CTSE/Discoverer/SegmentReturn_Mean`

4. Add tests:

   - core low-level actor signature still has no compact/team/process input;
   - disabling process reward restores current reward path;
   - process reward redistribution affects discoverer returns, not
     high-level labels;
   - compact-low-level ablation remains explicitly gated.

Implemented first pass:

- `RolloutBuffer` now carries a separate `reward_process` channel in addition
  to env/team/individual reward components.
- `add_process_rewards` mutates the low-level discoverer reward tensor and the
  process reward component tensor at the exact primitive step indices belonging
  to a closed process segment.
- Legacy discriminator MI pressure is disabled in `horizon_ctb_sse_core`
  through `disable_discriminator_training=True`,
  `disable_discriminator_rewards=True`, and `legacy_mi_reward_coef=0.0`.
  It may remain only in explicitly named legacy/control variants.
- The low-level actor signature for `horizon_ctb_sse_core` remains
  `pi_l(a_i | o_i, z_i)`. Process information trains it through reward, not by
  bypassing the skill bottleneck as an input.
- Process training metrics and discoverer process reward metrics are routed to
  TensorBoard under `HA_CTSE/ProcessTraining/*` and
  `HA_CTSE/Discoverer/ProcessReward_*`.

### Stage P4: Process Reward Integration

Status: Complete first pass.

Process objectives are now converted into discoverer exploration reward after
closed-segment labels, masks, and outcomes are available and before discoverer
GAE/PPO runs.

Reward design:

```text
r_i =
    lambda_e * r_env
  + process_reward_coef * R_process(segment_i, z_i, c_tau, g_tau)
  + optional legacy_mi_coef * R_mi
```

Initial recommendation:

- distribute process reward as `mean_over_segment` to reduce terminal-only
  variance;
- keep legacy discriminator MI enabled as a small auxiliary or diagnostic, not
  the dominant reward;
- log process reward separately from env, team MI, and individual MI.

Current implementation:

- `update_process_exploration_from_segments` trains process modules first.
- It computes a segment-level process signal from contrastive log-probability
  of the executed skill and masked outcome-prediction error.
- The signal is scaled by `process_reward_coef`, clipped by
  `process_reward_clip`, optionally warmed up, and redistributed to primitive
  low-level steps according to `process_reward_distribution`.
- `reward_process` is added before `update_discoverer_from_rollout`, so the
  discoverer value targets and advantages include the process signal in the
  same on-policy rollout.

Tests:

1. Sum of redistributed process reward equals the segment-level reward.
   First-pass coverage complete for mean-over-segment reward insertion.
2. Terminal-only and mean-over-segment modes are both deterministic. Terminal
   mode still needs a focused test.
3. Disabling process reward restores the previous low-level reward path.
   Covered by config gate behavior; add an explicit regression test if this
   becomes a formal ablation.
4. Process reward components appear in TensorBoard. `paper_data` export is
   still pending.

### Stage P5: Termination-Aware Learning

Status: Pending.

Once process segments exist, termination should be analyzed as a continuation
decision rather than controlled mainly by switch penalties.

Add diagnostics first:

```text
continue_return_estimate
edit_return_estimate
termination_advantage = edit_return_estimate - continue_return_estimate
```

Then consider using `termination_advantage` as an auxiliary target for
`pi_term`. This is a later-stage change because it can destabilize PPO if the
process reward is noisy.

Metrics:

- edit rate conditioned on positive/negative termination advantage
- process reward before and after edit
- average return for continued vs edited segments
- early-edit rate after warmup

### Stage P6: Legacy Discriminator Repositioning

Status: Pending.

After process objectives are wired, reclassify current discriminators:

- keep `horizon_ctb_sse_no_discriminator` as a control;
- add a process-core control where legacy MI reward is disabled but process
  reward remains enabled;
- keep single-step discriminator accuracy as a diagnostic, not as proof of
  skill semantics.

Possible new ablation names:

```text
horizon_ctb_sse_process_core
horizon_ctb_sse_process_no_mi
horizon_ctb_sse_process_no_contrast
horizon_ctb_sse_process_fixed_k
horizon_ctb_sse_process_lifetime
```

Only register new algorithm names after the segment buffer and tests exist.

### Process Implementation Continuation Prompt

```text
Continue HA-CTSE as process-centric exploration, not discriminator-centric
maintenance. Before coding, read ALGORITHM_PRINCIPLES.md and this
Process-Centric Exploration Plan. The implementation target is now the
standalone `ha_ctse_process/` package. Do not continue adding new process-core
training behavior to `hmasd.agent`; keep HMASD as baseline/inspiration only.
The standalone path must own agent, buffers, losses, process reward, trainer,
and checkpoints.
```

## Current Implementation Status

Status legend: Complete means usable in the current code path. Partial means
the switch or module exists but the research version is not fully implemented.
Pending means planned but not implemented.

| Stage | Status | Notes |
| --- | --- | --- |
| Repo inspection and docs | Complete | The live repo was inspected and the new docs were placed under `new-test-alg/`. |
| Standalone algorithm boundary | Initial complete | `ha_ctse_process/` now contains env construction, a standalone process-core agent, and a standalone training entrypoint. It reuses `envs`/config only and does not import `hmasd.agent`. |
| Standalone synchronous collection | Complete first pass | `ha_ctse_process.train` supports `--num_envs` with independent per-env active skill, duration countdown, and process segment state. Segment rewards use explicit rollout indices, so multi-env interleaving does not corrupt process reward redistribution. |
| Standalone high-level PPO | Initial complete | Closed skill-lifetime segments now carry the high-level skill/duration decision observation, old log-prob, value, and entropy. Segment return plus process reward trains the standalone high-level skill/duration policy. |
| Standalone logging/checkpointing | Complete first pass | TensorBoard scalars are written under `Train/`, `Process/`, `High/`, and `Low/`. Periodic and final checkpoints save high, low, process modules and optimizers. |
| Standalone Scenario 7 outcome extraction | Complete first pass | `ha_ctse_process.process_outcomes` extracts masked deltas for coverage, connected users, throughput, QoS, backhaul, energy, charging, return pressure, plus observation/reward fallbacks. The process outcome head now predicts this 12-field normalized vector with masked MSE. |
| Preserve original HMASD | Complete | `hmasd` and `hmasd_original` disable HA-CTSE switches. A smoke run passed. |
| OPT compact extractor | Complete first pass | `OPTCompactExtractor` exists in `hmasd/ha_ctse.py` and produces compact context plus auxiliary losses/metrics. It is representation context, not a team skill. |
| Compact-team bridge | Research core updated | Deterministic and stochastic bridge modes exist. `horizon_ctb_sse_core` now uses stochastic bridge; `deterministic_bridge` is the explicit ablation. |
| Horizon skill editor | Complete first pass | Parallel editing, per-agent active skills, skill ages, `H_min` masking, `H_max` force, candidate skills, executed edit masks, and autoregressive sequential editing are implemented. |
| Discrete skill lifetimes | Complete first pass | `horizon_ctb_sse_core` now samples duration buckets from `skill_lifetime_candidates`, stores duration log-probs/entropy/targets, and suppresses edit sampling until expiry. |
| Rollout buffer fields | Process-aware first pass | HA-CTSE fields plus duration fields are stored and sampled by `RolloutBuffer`. High-level replay entries also store elapsed primitive steps, terminal closure, and close reason. |
| Process segment data contract | Complete first pass | `SkillProcessSegmentBuffer` collects per-agent skill-lifetime segments, reward-info sequences, outcome vectors/masks, and TensorBoard segment stats. Closed on-policy segments feed the process encoder/update path. |
| High-level PPO data flow | Process-aware first pass | Pending high-level samples now stay open across no-decision k-boundaries and close on duration expiry/done/rollout-local closure. High-level GAE uses `gamma ** elapsed_steps` for variable-duration samples. The old warning for missing pending samples at no-decision boundaries should not appear. |
| `strict_hmasd_alignment` | Legacy-only | This flag means fixed-k high-level sample closure for original HMASD. HA-CTSE process/discrete-lifetime presets force it off because it conflicts with duration-aware replay. |
| Legacy high-level contribution monitors | Retired for process mode | Fixed-k checks that expected one high-level sample every `k` steps and set `force_high_level_collection` are disabled for HA-CTSE process/discrete-lifetime mode. They are replaced by diagnostics for closed samples, duration remaining, and process segment stats. |
| On-policy update boundary | Complete first pass | After each update, HA-CTSE process mode clears rollout/discriminator/process buffers, drops pending high-level samples, invalidates active high-level skills, and resets RNN hidden state so the next rollout starts from the current policy instead of continuing decisions sampled by the previous policy version. |
| Process outcome extraction | Complete first pass | Closed process segments now get stable masked outcome vectors with Scenario 7 reward-info deltas and fallback obs-delta/return fields, plus running normalization. Outcomes are used by masked process prediction loss and process reward. |
| Process encoder training | Complete first pass | `SkillProcessEncoder`, `SkillOutcomePredictor`, `SkillProcessContrastiveHead`, executed-skill label extraction, and duration-only shortcut baseline are optimized inside `HMASDAgent.update` before discoverer PPO. |
| Process reward integration | Complete first pass | Segment-level process reward is computed from contrastive executed-skill evidence and outcome-prediction error, then redistributed into low-level rollout rewards before discoverer GAE. `reward_process` is logged separately. |
| High-level PPO update | Complete first pass | The HA-CTSE path recomputes log-probs for executed high-level decisions and updates the editor/bridge through PPO. |
| Low-level actor path | Complete for core and ablation | The core path keeps `R_Actor(obs, skill)` unchanged. `opt_mappo_k` and `horizon_ctb_sse_compact_low_level_ablation` use an explicit compact-context branch outside the core path. |
| Discriminator path | Removed from process core | `horizon_ctb_sse_core` disables discriminator training and discriminator rewards. The old team/individual discriminators remain only for HMASD-compatible baselines or explicit legacy controls, not as part of the process/outcome target. |
| Baselines and ablations | Complete first pass | Registered HA-CTSE variants now have executable code paths and short smoke checks. Long-run scientific validation is still required. |
| Metrics/logging | Complete first pass | HA-CTSE edit/horizon/compact/bridge/duration/process-segment/replay-span/process-training/process-reward metrics are routed explicitly to TensorBoard under `HA_CTSE/...`. |
| Tests | Current pass complete | `py_compile` passed for touched HMASD and standalone modules. Standalone env dry run passed on `config_1`/`S7-S3`; standalone 16-step training smoke passed with continuous Scenario 7 actions. Focused HMASD regression tests should still run after migration cleanup. |
| Scenario 7 standalone command | Ready for smoke | Use `python -m ha_ctse_process.train --scenario energy --preset S7-S3`. The standalone path supports synchronous multi-env training; multiprocessing/sharded collection is pending migration. |

## Implemented Code Map

- `ha_ctse_process/env_factory.py`: standalone env factory using only
  `envs.pettingzoo` and `ParallelToArrayAdapter`.
- `ha_ctse_process/standalone_agent.py`: minimal standalone process-core agent
  with continuous/discrete low-level PPO, skill-lifetime segments, high-level
  skill/duration PPO, process encoder, outcome prediction, contrastive
  skill/process loss, and process reward redistribution.
- `ha_ctse_process/process_outcomes.py`: standalone process outcome extractor
  for Scenario 7 reward-info deltas and fallback process statistics.
- `ha_ctse_process/recovery_potential.py`: P2-lite recovery-window contribution
  credit — soft per-agent `phi_i` from positions (non-saturating `exp(-d/scale)`
  closeness), `W_recovery` smooth state weight, SIGNED segment shaping and
  per-agent `F_i`, plus Pre-check-2 / CF-audit diagnostics. Default OFF; wired
  into `standalone_agent.py` alongside the P1 topology_potential path. Smoke
  test: `ha_ctse_process/test_recovery_potential.py`.
- `ha_ctse_process/train.py`: standalone training entrypoint, independent from
  `train_multiproc_config_1.py` and `hmasd.agent`; supports synchronous
  multi-env collection, TensorBoard, and checkpoint save.
- `hmasd/ha_ctse.py`: new OPT compact extractor, compact-team bridge, and horizon-aware skill editor with optional discrete duration head.
- `hmasd/ha_ctse.py`: also contains compact-conditioned team/individual discriminators and the autoregressive editor path.
- `hmasd/process_exploration.py`: masked process outcome extraction,
  running normalization for closed skill-lifetime segments, process encoder,
  outcome predictor, contrastive head, executed-label helper, and duration-only
  shortcut diagnostic.
- `hmasd/agent.py`: optional HA-CTSE assignment path, per-env skill ages and duration countdowns, process-aware high-level pending sample closure, process segment collection, process encoder/outcome/contrastive training, process reward redistribution into discoverer rollout rewards, HA-CTSE high-level PPO update, compact-conditioned discriminator integration, low-level compact ablation integration, rollout storage integration, checkpointing, and metrics.
- `hmasd/utils.py`: rollout fields for compact context, team code, active/candidate skills, edit masks, ages, duration fields, high-level replay span fields, variable-span high-level GAE, high-level log-probs, OPT aggregation entropy, low-level joint observations for compact-conditioned PPO replay, `reward_process`, low-level process reward insertion, and `SkillProcessSegmentBuffer` with masked outcome records.
- `hmasd/baselines.py`: algorithm names and config switches.
- `config_1.py` and `config_test.py`: HA-CTSE config fields.
- `tests/ha_ctse_test.py`: focused tests for shapes, masks, skill persistence, PPO gradients, discriminator labels, and config loading.

## Legacy Variant Status

These names exist in code from the first implementation pass. Under the
process-centric framework, some are full baselines, some are temporary controls,
and some may be retired instead of expanded into formal ablations.

| Algorithm name | Current state | Process-era role |
| --- | --- | --- |
| `horizon_ctb_sse_core` | Research core updated | Stochastic bridge, horizon editor, discrete lifetime buckets, process segments, process encoder/outcome/contrastive training, process reward, adaptive entropy targets, OPT auxiliary pressure, and TensorBoard metrics are wired. Discriminator training/rewards are disabled in the core. Short smoke passed. |
| `hmasd_original` | Complete baseline | Stable external baseline. Keep. |
| `opt_mappo_k` | Complete baseline/control | External/direct compact-conditioning control. Keep, but do not use success here as proof of process skill learning. |
| `deterministic_bridge` | Complete first pass | Temporary live ablation only while stochastic team-code sampling remains a current hypothesis. |
| `stochastic_bridge` | Complete first pass | Alias-style preset close to the current core; may be removed or repurposed once `horizon_ctb_sse_core` is unambiguously stochastic. |
| `ctb_sse_no_horizon` | Complete first pass | Candidate for retirement if discrete/process lifetimes replace learned keep/edit as the temporal mechanism. |
| `opt_full_sync_skill` | Complete first pass | Collapse/control reference only. Not a serious process-framework alternative. |
| `horizon_ctb_sse_no_discriminator` | Redundant alias/control | Its main behavior is now the core default. Keep only temporarily for command compatibility; future process-era controls should be `process_no_reward`, `process_no_contrast`, or `process_no_outcome`. |
| `horizon_ctb_sse_compact_low_level_ablation` | Complete first pass | Explicit bottleneck-violation ablation only. |
| `autoregressive_editor` | Complete first pass | Keep only if sequential per-agent assignment remains relevant after discrete/process lifetimes are implemented. |

## Next Change Plan

Completed on 2026-06-24:

1. TensorBoard/log routing for HA-CTSE metrics is explicit.
2. Core low-level actor contract remains unchanged; compact context is isolated behind `use_compact_in_low_level_actor`.
3. Compact-conditioned discriminator interfaces were added without modifying old HMASD discriminator classes.
4. `opt_mappo_k` has a separate compact-to-low-level actor/critic branch.
5. `autoregressive_editor` has sequential per-agent sampling and focused tests.
6. All registered HA-CTSE variants passed short config-test smoke runs.
7. Work principle updated: HA-CTSE is an exploratory algorithm reconstruction.
   Future changes should be framed as research hypotheses and ablations, not as
   automatic conservative reductions to old HMASD behavior.
8. Ablation budget corrected: old HMASD structures are not automatically
   expanded into new ablations. Current implementation work follows the
   process-core stages first.
9. Discrete skill lifetime buckets are implemented for the research core.
10. Process outcome extraction, process encoder/contrastive training, and
    process reward redistribution are implemented as the current research core.
    The next work is empirical validation, P5 termination-aware learning, and
    process-era ablation cleanup.

Operational note from the 20260623_231851 long run:

- `Training/Skill_Switches_Total` was an old tracker metric and had no active
  call site in the training loop, so it could stay at 0 even while HA-CTSE high
  level decisions were being made. The training loop now updates it from
  `step_data`; for HA-CTSE it counts real per-agent active-skill changes using
  `active_skill_prev`, `active_skill`, and `initial_assignment_mask`.
- The more diagnostic HA-CTSE metrics are `HA_CTSE/Editing/SwitchedAgents_Mean`,
  `HA_CTSE/Editing/ExecutedEdits_Mean`, `HA_CTSE/Editing/FullSync_Rate`, and
  `HA_CTSE/Horizon/PersistenceCycles_Mean`.
- Evaluation and evaluation images are triggered by `eval_interval`, not by
  reward improvement. For the observed S7-S3 run, `eval_interval=480000`, so a
  run at `304000` steps has not reached its first evaluation.

Open research reminder from 2026-06-24:

- HMASD's exploration pressure comes from multiple places: high-level entropy
  in the target/loss, low-level discoverer action entropy, and discriminator
  intrinsic reward terms. HA-CTSE changes the high-level latent, edit horizon,
  compact-team bridge, and optionally discriminator conditioning, so these
  exploration terms must be reconsidered as part of the new algorithm rather
  than simply copied or removed.
- Compact-conditioned discriminators are currently part of the exploratory
  HA-CTSE implementation. They may help align skill identity with interaction
  structure, or they may weaken the old HMASD skill-discovery pressure by
  letting compact context explain labels. This should be tested, not resolved
  by conservative default.
- Training trajectory images are generated only with `--debug`; normal visual
  outputs are produced during evaluation.

Next:

1. Restart long training for `horizon_ctb_sse_core`; existing runs launched
   before the process training pass are still the old weakened implementation.
2. Inspect `HA_CTSE/ProcessTraining/*`,
   `HA_CTSE/Discoverer/ProcessReward_*`, `HA_CTSE/ProcessOutcome/*`,
   `HA_CTSE/Duration/*`, and the existing edit/horizon/bridge entropy metrics.
3. Verify that `process_segments_trained` is nonzero after updates,
   `process_reward_applied_steps` is nonzero when the gate is enabled, and the
   reward scale is not overwhelming env reward.
4. If process reward is unstable, adjust `process_reward_coef`,
   `process_outcome_coef`, `process_contrastive_coef`, or reward clipping
   before adding more architecture.
5. Do not use legacy discriminator MI in the core. If a later comparison is
   needed, introduce an explicitly named legacy-MI control rather than
   re-enabling it inside `horizon_ctb_sse_core`.
6. Compare `deterministic_bridge` against the stochastic research core only if
   team-code sampling remains a live question after process diagnostics.
7. Treat compact-low-level and OPT-MAPPO-K as baselines/controls, not core
   algorithm evidence.
8. Add segment-level discriminator only if process/outcome objectives are
   insufficient and the hypothesis is explicitly rewritten for the process
   framework.
9. Re-run focused tests after every code pass:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\rollout_buffer_test.py tests\ha_ctse_test.py tests\training_metrics_profiler_test.py -q
```

10. Run a short smoke command before any long experiment:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" train_multiproc_config_1.py `
  --config config_test `
  --algorithm horizon_ctb_sse_core `
  --collector_backend subproc `
  --num_envs 4 `
  --rollout_length 16 `
  --total_timesteps 64 `
  --disable_eval `
  --console_log_level error `
  --log_dir logs\smoke_ha_ctse_core
```

For the long-run collector path, also run:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" train_multiproc_config_1.py `
  --config config_test `
  --algorithm horizon_ctb_sse_core `
  --collector_backend sharded `
  --num_workers 2 `
  --envs_per_worker 2 `
  --rollout_length 16 `
  --total_timesteps 64 `
  --disable_eval `
  --console_log_level error `
  --log_dir logs\smoke_ha_ctse_core_sharded
```

## Recommended Standalone Core Training Command

For a Scenario 7 run with an episode length around 1500, use an energy preset
other than `S7-S1`. The standalone path supports synchronous multi-env
collection; multiprocessing/sharded collection is still pending:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.train `
  --config config_1 `
  --scenario energy `
  --preset S7-S3 `
  --num_envs 8 `
  --rollout_length 500 `
  --skill_interval 10 `
  --total_timesteps 320000 `
  --save_interval 20 `
  --device cuda `
  --log_dir logs\ha_ctse_process_standalone_320k
```

## 2026-06-25 Standalone Eval Result

The most useful checkpoint from the first `S7-S1` 6-agent standalone run is
currently `update_60`, not the final `update_80` checkpoint.

Eval command target:

```text
logs\ha_ctse_process_s7s1_6agent_subproc_320k\standalone_process_core_update_60.pt
```

20-episode eval result:

```text
reward_mean      = 85.424256
reward_std       = 59.354647
length_mean      = 500.0
coverage         = 0.281667
qos              = 0.191187
throughput       = 19.133963
battery_min      = 1.000000
```

Distribution notes from `metrics/eval_episodes.csv`:

- 13 / 20 episodes had nonzero coverage, QoS, and throughput.
- 7 / 20 episodes still collapsed to zero service.
- Reward ranged from about `-3.75` to `219.51`, so the policy is promising but
  still high-variance.
- The 240k/update_60 checkpoint is empirically more credible than the final
  checkpoint from the same run because the final 320k two-episode eval showed
  zero coverage/QoS/throughput despite a positive reward mean.

Decision:

- Do not blindly continue the same long training recipe.
- Treat the current discrete-lifetime process core as a working but unstable
  baseline.
- Next code work should focus on diagnostics and stabilization:
  1. batch-evaluate multiple checkpoints and select by Scenario 7 service
     metrics, not reward alone;
  2. reduce checkpoint IO so training is not slowed by saving every update;
  3. split high/low policy loss, value loss, entropy, and return scales in
     logs;
  4. add duration/skill/g histograms and collapse diagnostics;
  5. add process posterior and coordination diagnostics before moving to a
     hazard-SMDP variant.

Alternative research track:

- `new-test-alg/IC_SPL_HAZARD_SMDP_ALTERNATIVE.md` records the more aggressive
  IC-SPL hazard-SMDP proposal. It is a future named variant, not the current
  implemented core.

Implementation update after this eval:

1. Checkpoint sweep eval is implemented as:

   ```powershell
   & "C:\Users\wu\.conda\envs\SB3\python.exe" -m ha_ctse_process.eval_checkpoints `
     --checkpoint_dir logs\ha_ctse_process_s7s1_6agent_subproc_320k `
     --log_dir logs\ha_ctse_process_s7s1_6agent_checkpoint_sweep `
     --config ha_ctse_process.config `
     --scenario energy `
     --preset S7-S1 `
     --n_agents 6 `
     --seed 1 `
     --device cuda `
     --updates 20,40,60,80,final `
     --eval_episodes 20 `
     --eval_max_steps 1500 `
     --overwrite
   ```

   It writes `metrics/checkpoint_eval_summary.csv`, sorted by a service score
   using coverage, QoS, throughput, and battery safety.

2. Standalone training logs now split total losses into:

   ```text
   process_outcome_loss
   process_contrastive_loss
   high_policy_loss
   high_value_loss
   high_entropy_loss
   high_aux_loss
   low_policy_loss
   low_value_loss
   low_entropy_loss
   ```

   This is intended to diagnose whether the large high-level loss is mostly
   value-scale, policy-ratio, entropy, or OPT auxiliary pressure.

3. Collapse diagnostics are now exported to CSV/TensorBoard:

   ```text
   skill_usage_entropy
   skill_usage_max_frac
   duration_usage_entropy
   duration_usage_max_frac
   skill_duration_mi
   team_code_usage_entropy
   team_code_usage_max_frac
   team_code_skill_mi
   ```

   These directly test skill collapse, duration shortcuts, and whether `g`
   affects skill distribution.

4. Checkpoint IO is reduced:

   - standalone `--save_interval` default is now `10`, not every update;
   - `--checkpoint_keep_last` defaults to `3` periodic checkpoints;
   - `standalone_process_core_final.pt` is still always saved.

5. Lightweight smoke checks passed:

   ```text
   python -m py_compile ha_ctse_process\standalone_agent.py ha_ctse_process\train.py ha_ctse_process\plotting.py ha_ctse_process\eval_checkpoints.py
   python -m ha_ctse_process.train ... --total_timesteps 8 --rollout_length 8
   python -m ha_ctse_process.eval_checkpoints ... --updates 60,final --eval_episodes 1 --eval_max_steps 1
   ```

Follow-up diagnosis on the original 320k `S7-S1` 6-agent run:

```text
updates 1-20:  return=3.60,  duration_acc=0.282, switch=0.665, seg_len=87.0,  high_entropy=4.43, high_loss=84.3
updates 21-40: return=5.20,  duration_acc=0.288, switch=0.657, seg_len=89.2,  high_entropy=4.41, high_loss=120.1
updates 41-60: return=7.31,  duration_acc=0.336, switch=0.619, seg_len=104.2, high_entropy=4.28, high_loss=244.0
updates 61-80: return=10.85, duration_acc=0.487, switch=0.474, seg_len=158.3, high_entropy=3.36, high_loss=620.6
```

Interpretation:

- Reward/return keeps improving, but Scenario 7 service metrics peak around
  update 40 / 160k.
- After update 40, segment length grows and switch rate falls sharply. This is
  not automatically bad, but in this run it coincides with worse coverage/QoS.
- `duration_only_accuracy` rises from about `0.28` to `0.49`, suggesting the
  policy/process encoder may be leaning on duration as a skill identity
  shortcut.
- `team_code_entropy` stays close to `log(5)`, so `g` is still sampled with
  high entropy. This does not prove `g` is useful; new `team_code_skill_mi` and
  intervention diagnostics are needed in the next run.
- `high_loss` grows strongly. Because the old run did not split high policy and
  value losses, the next run must use the new loss decomposition before adding
  architecture changes.

Experiment implication:

- `S7-S1` is still a complex environment; 1M+ steps is a more realistic training
  horizon than 320k.
- Do not interpret 320k instability as failure. Interpret it as evidence that
  longer training must log value-scale, duration shortcut, and `g` usage
  diagnostics.
- Before switching to hazard-SMDP, run a longer discrete-lifetime baseline with
  the new diagnostics and checkpoint sweep. If service metrics still peak early
  and then regress, first try value normalization/loss scaling and duration
  regularization.

## 2026-06-25 Process Posterior MI Upgrade

User hypothesis: a sequence classifier can provide the exploration pressure
that old team/skill discriminator rewards used to provide, but it must operate
on completed process segments rather than single states. This is compatible
with the process-core framework if it is treated as a variational process MI
estimator:

```text
q_phi(z | S, g)      = segment-to-skill posterior
p_phi(z | g)         = coordination-conditioned skill prior
R_process_mi         = log q_phi(z | S, g) - log p_phi(z | g)
```

Implemented standalone module:

- `ha_ctse_process/process_posterior.py`
  - `SegmentSkillPosterior`
  - separate class, not a legacy HMASD discriminator
  - consumes segment encoder embedding and team code `g`
  - outputs posterior logits `q(z | S,g)` and prior logits `p(z | g)`

Config switches:

```text
use_process_posterior_mi = True
process_posterior_condition_on_team = True
process_posterior_team_embed_dim = 0
process_prior_coef = 0.25
```

CLI switch:

```powershell
--disable_process_posterior_mi
```

Training changes:

- The old process reward term `log q(z|S) + log n_z` is replaced by
  `log q(z|S,g) - log p(z|g)` when `use_process_posterior_mi=True`.
- The segment encoder still predicts Scenario 7 process outcomes.
- The old `ProcessEncoder.skill_head` remains available as the legacy fallback
  path when the MI posterior is disabled.
- Checkpoints now save `process_posterior`; loading old checkpoints remains
  compatible because missing posterior weights are initialized from the current
  config.

New metrics:

```text
process_prior_loss
process_posterior_acc
process_mi_estimate_mean
process_log_q_mean
process_log_p_mean
```

Smoke checks passed:

```text
python -m py_compile ha_ctse_process\process_posterior.py ha_ctse_process\standalone_agent.py ha_ctse_process\train.py ha_ctse_process\plotting.py ha_ctse_process\eval_checkpoints.py
python -m ha_ctse_process.train ... --total_timesteps 8 --rollout_length 8
python -m ha_ctse_process.train --mode eval ... new checkpoint
python -m ha_ctse_process.train --mode eval ... old checkpoint
```

Next 1M baseline should keep this enabled by default, while a control run can
disable it with `--disable_process_posterior_mi`.

## Continuation Prompt

Use this prompt when resuming implementation work:

```text
Continue HA-CTSE implementation in C:\project\HMASD. First read
new-test-alg/ALGORITHM_PRINCIPLES.md, new-test-alg/IMPLEMENTATION_PLAN.md, and
new-test-alg/ALGORITHM_KNOWLEDGE_BASE.md. Check git status and do not revert
user changes. The process-core algorithm must live in `ha_ctse_process/`, not
inside `hmasd.agent`. Reuse environment/config infrastructure only when needed.
Do not reintroduce discriminator training/rewards into the process core. Respect
PPO/on-policy boundaries: no rollout, process-segment, active-skill, or hidden
state data should silently cross an update boundary as training data for a new
policy version. Next migration targets are proper evaluation,
resume-from-checkpoint, multiprocessing/sharded collection, and replacing
remaining minimal trainer shortcuts inside `ha_ctse_process/`.
```

## Pre-Change Self Check

Before editing code, answer these questions in the work notes:

1. Which stage or variant is this change advancing?
2. Does it risk changing `hmasd` or `hmasd_original` behavior?
3. Does it let `c_tau` or `g_tau` bypass the skill bottleneck outside an explicit ablation?
4. Are discriminator labels active executed skills, not candidate no-edit skills?
5. Are edit masks applied before sampling so old and new log-probs match executed actions?
6. Does any training sample or hidden state cross an update boundary in a way
   that would make PPO/discriminator/process updates off-policy?
7. Is the change covered by a focused test or smoke run?

## Open Risks And TODOs

- Long-run stability is not proven by short smoke tests.
- Process training is implemented, but its reward scale and stability are not
  proven. Watch for process reward overwhelming environment reward or producing
  high-variance discoverer advantages.
- The first posterior run showed that `q(z|S,g)` starts learning useful segment
  signal, but the old `MI - outcome_error` process reward often becomes
  negative because the outcome prediction error dominates. The next branch
  should treat outcome prediction as an auxiliary representation loss by
  default, not as a direct process reward penalty.
- `paper_data` export for process reward components is still pending; TensorBoard
  logging exists first.
- Segment-level discriminator is no longer the default next step. Reintroduce it
  only as a process-era hypothesis, not as an inherited HMASD obligation.
- Update-boundary closure is intentionally strict: pending process samples are
  discarded unless explicitly closed with valid bootstrap support. If sample
  efficiency becomes a problem, implement rollout-boundary partial closure
  rather than off-policy replay.
- Compact-low-level and OPT-MAPPO-K are ablations only; do not use them to
  redefine the HA-CTSE core.
- Stochastic bridge is now the research core and may add variance; compare it
  against `deterministic_bridge` explicitly instead of treating deterministic
  behavior as the default.
- The method still needs empirical evidence that it avoids full-sync collapse:
  monitor `full_sync_rate`, `avg_executed_edits`, `skill_persistence_cycles_mean`,
  and `lifetime_heterogeneity`.

## 3D Topology Evaluation View

Status: implemented as an optional standalone eval artifact.

Rationale: scalar curves cannot show whether the learned process is producing
meaningful UAV movement, service links, relay routes, charging behavior, and
skill lifetime choices. The most direct inspection tool for Scenario 7 is a
dynamic 3D topology trace.

Implementation:

- New module: `ha_ctse_process/topology_viz.py`.
- Eval switch: `--save_topology`.
- Sampling controls:
  - `--topology_interval`: environment steps between captured frames.
  - `--topology_episodes`: number of eval episodes to capture, default 1.
  - `--topology_max_frames`: cap per captured episode.
- Outputs under `log_dir/topology/`:
  - frame JSON with UAV/user/base-station/charging-station positions,
    connections, routing paths, active skills, remaining durations, batteries,
    reward, and eval metrics.
  - final static 3D PNG.
  - animated GIF when Pillow-backed matplotlib animation is available.

Validation smoke:

```text
python -m py_compile ha_ctse_process\topology_viz.py ha_ctse_process\train.py
python -m ha_ctse_process.train --mode eval ... --eval_max_steps 2 --save_topology
```

The smoke produced non-empty JSON, PNG, and GIF artifacts. Use this for
observation-only eval; do not enable it in high-frequency checkpoint sweeps
unless explicitly needed because GIF generation is extra CPU/IO work.

## Communication Metrics And Run Manifest

Status: implemented for standalone eval/log outputs.

Rationale: reward, coverage, QoS, and battery are not enough to explain Scenario
7 behavior. The communication topology itself is part of the task: a policy can
increase reward while losing backhaul robustness, overusing direct BS links,
breaking relay paths, or producing unstable service drops. Model parameters and
physical environment parameters are equally important for interpreting a run.

Added eval CSV fields:

- Service/user counts: `connected_users`, `access_connected_users`,
  `total_connected_users`, `served_users`.
- Topology: `connectivity_ratio`, `connected_uavs`, `uavs_with_backhaul`,
  `avg_hops`.
- Relay/backhaul robustness: `relay_route_loss_ratio`,
  `relay_route_loss_prev_served_ratio`, `relay_route_lost_uavs`,
  `relay_route_lost_users`, `backhaul_outage_ratio`, `service_drop_ratio`,
  `backhaul_drop_ratio`, `full_network_disconnect`, `coverage_drop_ratio`.
- Capacity and guard behavior: `min_serving_backhaul_bottleneck_mbps`,
  `avg_serving_backhaul_bottleneck_mbps`, `backhaul_margin_penalty_raw`,
  `backhaul_guard_checked_actions`, `backhaul_guard_blocked_actions`,
  `routing_overhead`.

Added plots:

- `eval_communication_topology.png`
- `eval_backhaul_robustness.png`
- `eval_backhaul_capacity_guard.png`

Added metadata:

- `metadata/run_manifest.json`
- Records command-line args, standalone algorithm parameters, training
  parameters, model dimensions, physical/communication/energy environment
  parameters, runtime env dimensions, and runtime agent dimensions.

Topology JSON now also includes `uav_connections`, `uav_bs_connections`, and
`routing_paths`, so the 3D topology view can distinguish physical/reachable
links from actually selected routing paths.

## Checkpoint/Eval Boundary Protection

Status: implemented after the 560k diagnostic interruption.

Observation: the 1M S7-S1 diagnostic run reached `update=140` /
`total_steps=560000`, then started eval. The log directory contains only
18/20 eval episode rows for 560k, no `standalone_eval total_steps=560000`
summary line, and no `standalone_process_core_update_140.pt`. The previous
training loop saved periodic checkpoints after eval, so an interruption during
eval could lose the latest trained weights.

Fix: periodic checkpoints are now saved and pruned before running scheduled
eval. Future eval-boundary interruptions should retain the just-finished update
checkpoint.

Operational note: for the interrupted run, the latest complete checkpoint is
`standalone_process_core_update_130.pt` at 520k steps. Resume or re-evaluate
from that checkpoint unless the original process is still alive and later writes
the update-140 checkpoint.

## Process Posterior Reward Branch

Status: implemented as the next experimental branch after tagging the prior
standalone version as stable.

Observation from the clean S7-S1 6-agent posterior run:

- Early posterior signal is weak before roughly 80k-160k steps.
- After roughly 280k steps, `posterior_acc` and `process_mi` sometimes rise
  meaningfully, so the segment posterior is learning process-level skill
  information.
- The mixed reward `process_reward = MI - outcome_error` often remains negative,
  and service metrics degraded after 160k in the first posterior run. This points
  to reward mixing, not necessarily to the posterior estimator itself, as the
  immediate failure mode.

Implemented change:

- Added `process_reward_mode` to `ha_ctse_process.config.Config` and CLI.
- Default mode is now `mi_only`.
- Supported modes:
  - `mi_outcome`: old mixed reward, `MI - outcome_error`.
  - `mi_only`: direct variational process MI reward.
  - `positive_mi`: only rewards positive process MI.
  - `centered_mi`: batch-centered process MI for advantage-like shaping.
  - `none`: trains process heads without injecting process reward.
- Outcome prediction remains trainable through `process_outcome_coef`, but is no
  longer part of the default reward.
- Added reward diagnostics:
  - `process_reward_mi_component_mean`
  - `process_reward_outcome_penalty_mean`
  - `process_reward_unclipped_mean`
  - `process_mi_positive_frac`

Next experiment priority:

1. Run `mi_only` as the main posterior branch.
2. If MI reward is still too sparse or negative early, run `positive_mi`.
3. Keep `process_outcome_coef` nonzero as auxiliary representation learning
   unless it becomes a speed bottleneck.
4. Compare at 160k, 320k, 480k, and 1M+ steps using reward, coverage, QoS,
   throughput, posterior accuracy, MI positive fraction, and topology traces.

## Correction + Ablation + Diagnostics Pass

Status: implemented as the next branch after the first `mi_only` reward split.

Intent: distinguish algorithm-correctness fixes from real ablation knobs and
from passive diagnostics.

Correctness fixes now enabled by default:

- High-level returns are now SMDP-style segment returns:
  - environment segment reward is discounted inside the variable-length segment.
  - non-terminal segments can bootstrap with `gamma^T V(s_{t+T})`.
  - diagnostics report `high_env_return_mean`,
    `high_bootstrap_value_mean`, and `high_smdp_discount_mean`.
- Process posterior reward is explicitly computed from pre-update posterior
  logits for the current rollout, then the posterior is trained. This keeps the
  reward assignment order clear for on-policy reasoning.
- Checkpoint selection now includes communication robustness in the score, not
  reward/coverage/QoS/throughput alone.

Ablation switches now available:

- `process_reward_mode`:
  - `mi_outcome`
  - `mi_only`
  - `positive_mi`
  - `centered_mi`
  - `none`
- `process_reward_injection`:
  - `high_only` (default)
  - `high_and_low`
  - `low_only`
  - `none`
- SMDP correction toggles:
  - `--disable_smdp_discounted_high_return`
  - `--disable_smdp_bootstrap`

Diagnostics added:

- `process_reward_high_mean`
- `process_reward_low_mean`
- `length_only_accuracy`
- `reward_sum_only_accuracy`

Interpretation:

- If `posterior_acc` rises together with `duration_only_accuracy`,
  `length_only_accuracy`, or `reward_sum_only_accuracy`, the posterior may be
  using shortcuts rather than process semantics.
- If `process_reward_high_mean` improves but service metrics degrade, the
  process reward is shaping high-level choices in the wrong direction.
- If `high_bootstrap_value_mean` dominates `high_env_return_mean`, high critic
  scale or bootstrap use should be audited before trusting long-run results.

First ablation batch:

```text
A0: process_reward_mode=none,        process_reward_injection=none
A1: process_reward_mode=mi_only,     process_reward_injection=high_only
A2: process_reward_mode=mi_only,     process_reward_injection=high_and_low
A3: process_reward_mode=positive_mi, process_reward_injection=high_only
```

Keep duration candidates fixed for this batch:

```text
1,2,4,8,16,32
```

Do not mix duration-set ablations into this first batch.

## Reward-Purity Correction After A1/A1b

Status: active correction pass.

Reason:

- A1 (`mi_only + high_only + bootstrap`) showed low-position eval oscillation
  and declining service metrics by 240k.
- A1b (`mi_only + high_only + no bootstrap`) improved some reward/coverage
  means at 80k, but episode outcomes became strongly all-or-nothing:
  successful episodes had high service, while many episodes had full network
  disconnect and zero coverage.
- This exposed a conceptual issue: high-level and low-level rewards share the
  same environment source, but the high-level target is a segment-level SMDP
  aggregation while the low-level target is per-step reward. Injecting process
  reward into high only creates a second high-level objective that the low-level
  policy does not directly receive.

Correction:

- The default standalone config now keeps the RL task reward pure:
  `process_reward_injection = "none"`.
- The process posterior is still trained and logged by default. Its MI estimate
  is treated first as a diagnostic/auxiliary signal, not as a reward target.
- Explicit reward-injection ablations remain available through
  `--process_reward_injection high_only|high_and_low|low_only|none`.
- Added `smdp_bootstrap_coef` so bootstrap can be damped instead of only on/off.
- Added `high_max_grad_norm` to prevent high-level critic/policy updates from
  being dominated by large value targets.
- Added direct shortcut-gap diagnostics:
  - `posterior_acc_minus_duration_only`
  - `posterior_acc_minus_length_only`
  - `posterior_acc_minus_reward_sum_only`

New near-term experiment order:

```text
P0: reward-pure baseline
    process_reward_mode=mi_only
    process_reward_injection=none
    smdp_bootstrap_coef=0

P1: damped bootstrap baseline
    process_reward_mode=mi_only
    process_reward_injection=none
    smdp_bootstrap_coef=0.1

P2: reward-pure + stronger posterior training diagnostics
    process_reward_mode=centered_mi or mi_only
    process_reward_injection=none
    process_reward_coef can be nonzero, but should not affect RL reward

Only after P0/P1 prove stable:

R1: low-level process shaping
    process_reward_injection=high_and_low
    process_reward_coef=0.5 or 1.0
```

Interpretation rule:

- If `posterior_acc_minus_duration_only <= 0`, do not trust process MI as a
  semantic reward. It is likely reading duration/length shortcuts.
- If reward-pure P0 is still all-or-nothing, the issue is not process reward
  injection; inspect environment reward/communication credit assignment and
  high-level action semantics.
- If P0 is stable but reward-injection runs collapse, the process reward is
  corrupting task credit and must remain auxiliary until debiased.

## Cooperative Relay Failure Interpretation

Status: user-confirmed task interpretation.

The high full-disconnect rate in S7-S1 should not be treated as a logging bug or
as merely an unlucky evaluation artifact.  This cooperative UAV setting has a
real relay-formation requirement: if the policy fails to learn cooperative relay
behavior, the network naturally breaks and service collapses.  Therefore the
P0 all-or-nothing pattern means the current algorithm is not yet reliably
forming and maintaining stable relay chains.

Updated implication:

- Full disconnect is a core task failure mode, not a nuisance metric.
- The next algorithmic work should address cooperative credit assignment: the
  policy must learn which local behaviors enable team connectivity even when an
  individual UAV's immediate reward/output is hard to isolate.
- Reward-pure P0 is still useful because it proves this failure happens without
  process reward contamination.
- The next diagnostics should inspect whether failed episodes correspond to
  agents never forming a backhaul chain, forming it too late, or breaking it
  after initial service.
- Relay/backhaul measurements are diagnostic proxies for cooperation credit,
  not first-class optimization targets.  Do not hard-code "relay-chain output"
  as the algorithm objective.

Candidate directions:

1. Add relay/topology state diagnostics to high-level segment records as
   cooperation-credit probes.
2. Diagnose whether skill/duration choices correlate with later team
   connectivity changes, without using relay-chain output as a direct target.
3. Add counterfactual or baseline-style contribution diagnostics where possible:
   which agent was plausibly bridge-critical, bottleneck-critical, or irrelevant
   during a segment.
4. Keep process posterior reward auxiliary until it proves it captures relay
   semantics beyond duration/length shortcuts and improves downstream task
   behavior.

## HMASD Cooperation Bias Audit

Status: code-audited migration plan.

Purpose: explain why HMASD can learn cooperative relay behavior while the
current standalone HA-CTSE process path still shows persistent all-or-nothing
relay failure.

Audited files:

- `hmasd/agent.py`
- `hmasd/networks.py`
- `hmasd/utils.py`
- `hmasd/process_exploration.py`
- `envs/pettingzoo/scenario_base.py`
- `ha_ctse_process/standalone_agent.py`
- `ha_ctse_process/process_outcomes.py`

### 1. Environment already has relay robustness reward

The environment does provide direct relay/backhaul shaping in `load_balance`
mode:

- `backhaul_outage_ratio`
- `backhaul_drop_ratio`
- `coverage_drop_ratio`
- `backhaul_outage_ema`
- `full_network_disconnect`
- `relay_route_loss_ratio`
- `backhaul_margin_penalty_raw`
- lighthouse/navigation reward when the whole team has no base-station
  connection

The shared reward subtracts a robustness penalty:

```text
w_backhaul_outage * outage
+w_full_disconnect * full disconnect
+w_coverage_drop * coverage drop
+w_outage_memory * outage EMA
+w_relay_break * relay route loss
+w_backhaul_margin * backhaul margin deficit
```

Therefore P0 failure is not because relay failure is absent from the environment
reward.  The reward signal exists, but the current standalone algorithm does not
reliably convert it into stable cooperative relay behavior.

### 2. HMASD low-level discoverer is much stronger than current low-level

HMASD `SkillDiscoverer` uses recurrent MAPPO-style actor/critic modules:

- recurrent actor conditioned on local observation and individual skill;
- recurrent centralized critic conditioned on global state and team skill;
- sequence/chunk sampler with `chunk_length = k`;
- GAE over rollout buffer;
- ValueNorm for discoverer returns;
- actor/critic optimizers separated;
- grad clipping for both actor and critic;
- optional compact context injection.

Current `ha_ctse_process.LowLevelPolicy` is feedforward:

```text
pi_l(a_i | o_i, one_hot(z_i))
V_l(o_i, z_i)
```

It has no recurrent state, no centralized low-level critic, no ValueNorm, and no
sequence update.  In a relay task where each UAV must infer and maintain a
temporal role in a partially observed chain, this is a major capacity and credit
assignment gap.

Migration implication:

- Before adding more process reward, upgrade the standalone low-level path to a
  recurrent MAPPO-style discoverer or an equivalent recurrent low-level actor
  with centralized value.
- Keep it inside `ha_ctse_process`, not by importing HMASD directly.

### 3. HMASD discriminator is not just a classifier; it feeds low-level reward

HMASD computes per-step intrinsic rewards from discriminator log-probabilities:

```text
intrinsic =
    lambda_e * env_reward
  + legacy_mi_coef * lambda_D * team_discriminator_MI
  + legacy_mi_coef * lambda_d * individual_discriminator_MI
  + optional uncertainty
```

The individual discriminator is conditioned on team skill and predicts
individual skill from next observation.  This makes the low-level discoverer
receive a direct skill-semantic shaping signal, not merely a diagnostic.

Current standalone P0 intentionally has:

```text
process_reward_high = 0
process_reward_low  = 0
```

and the process posterior often fails shortcut-gap checks.  Thus it does not
replace HMASD's semantic pressure.

Migration implication:

- Do not reintroduce the old generic discriminator unchanged.
- If adding auxiliary learning, treat relay-related labels as representation and
  credit-assignment probes, not as the main reward target:
  - did team connectivity improve after this segment?
  - did the agent occupy a bridge-critical or bottleneck-critical role?
  - did a local action precede a team service drop or recovery?
  - did skill identity explain cooperation-relevant trajectory differences
    beyond duration/length shortcuts?
- Only use this as reward after the posterior/outcome model beats duration and
  length shortcut baselines.

### 3b. What to distill from HMASD, not copy

User correction: the goal is not to discard HMASD.  HMASD's
discoverer/discriminator system has proven value in this cooperative relay
setting.  The new standalone algorithm should learn from those mechanisms while
keeping its own algorithm directory and process/SMDP framing.

Distill these functions:

- Discoverer as temporal skill executor: recurrent low-level policy, sequence
  update, centralized value, ValueNorm, and separated actor/critic optimization.
- Discriminator as semantic pressure: make executed skills induce distinguishable
  behavior, but move from one-step state labels toward process-level or
  cooperation-credit semantics.
- Update order discipline: policy uses reward from the pre-update estimator;
  estimator updates after the rollout, so reward generation and policy update
  remain on-policy for the collected data.
- Reward decomposition visibility: keep environment reward, semantic/process
  pressure, entropy, and credit diagnostics separately logged.

Do not distill these parts blindly:

- single-step next-observation skill classification as the only semantic test;
- relay-chain output as a hard-coded supervised target;
- off-policy reuse of discriminator/process data across rollout updates;
- direct import of HMASD classes into `ha_ctse_process`.

Implementation implication:

- First migrate discoverer capacity/critic structure, because P0 indicates the
  standalone low-level controller is likely underpowered for cooperation.
- Then add a process-level semantic estimator that can be switched on/off and
  tested against duration/length/reward shortcuts.
- Use relay/backhaul signals to diagnose cooperation credit assignment, not to
  define the core reward target.

Progress after this correction:

- Added standalone cooperation-credit diagnostics in
  `ha_ctse_process/cooperation_credit.py`.
- Wired the diagnostics into `StandaloneProcessAgent.process_update`, update
  CSV export, TensorBoard, train log parsing, and `ha_ctse_cooperation_credit`
  plots.
- These metrics are off the reward path.  They only measure segment-level
  disconnect/recovery/collapse, backhaul served/outage changes, relay loss
  changes, bottleneck, and reward/connectivity correlations.
- Smoke test `ha_ctse_process.smoke` now verifies reward-pure behavior remains
  unchanged while a toy disconnected-to-connected segment reports recovery.

Next discoverer migration slice:

1. Add a standalone recurrent low-level policy option inside
   `ha_ctse_process`, not by importing `hmasd.SkillDiscoverer`.  Done.
2. Store low-level recurrent hidden states and masks in `Rollout`.  Done.
3. Replace flat low-level PPO batches with chunked sequence batches.  Done.
4. Add centralized low-level critic input from global state and team/coordination
   code.  Done.
5. Add low-level ValueNorm and separate actor/critic optimizers.  Done.
6. Keep feedforward low-level as an explicit ablation/control.  Done via
   `--disable_recurrent_low_level`.

Implementation notes:

- `ha_ctse_process.standalone_agent.RecurrentLowLevelPolicy` keeps the low-level
  actor skill-bottlenecked on `(o_i, z_i)`, but gives the critic centralized
  `(state, team_code, z_i, agent_id)` context.
- `Rollout` now stores `env_id`, global `state`, `team_code`, low actor hidden
  state, and low critic hidden state for each transition.
- `update_low` reconstructs per-env sequences, chunks them, masks done resets,
  and runs recurrent PPO without crossing rollout boundaries.
- `low_value_norm` normalizes critic targets while policy advantages use
  denormalized values collected on-policy.
- The recurrent path is now the default in `ha_ctse_process.config`; the old
  feedforward path remains the explicit ablation.
- Smoke and a 4-step S7-S1 tiny train passed.

Network-scale correction:

- User pointed out that comparing against HMASD is unfair if the standalone
  process algorithm uses a smaller low-level network.
- Standalone defaults are now aligned to the main Scenario-7 HMASD scale:
  `n_Z=6`, `n_z=6`, `hidden_size=256` inherited from `config_1`,
  `low_rnn_hidden_size=256`, `low_ppo_epochs=15`, `low_sequence_length=10`,
  `low_value_loss_coef=1.0`, `low_max_grad_norm=0.5`.
- `network_scale_profile="hmasd_s7_256"` is written into the manifest and train
  startup log.
- Train startup now logs parameter counts:
  `params_total`, `params_high_stack`, `params_low`, and
  `params_process_stack`.
- Tiny S7-S1 smoke with this profile reported:
  `params_total=1819422`, `params_high_stack=295879`,
  `params_low=1096201`, `params_process_stack=427342`.
- Future claims about algorithmic improvement should compare runs under the same
  network-scale profile or explicitly label the run as a capacity ablation.

Strict HMASD/MAPPO low-level replica status:

- `ha_ctse_process.standalone_agent.StrictHMASDMAPPOLowLevelPolicy` now reuses
  HMASD's `MLPBase`, `RNNLayer`, and `ACTLayer`.
- Low actor path is:
  `MLPBase(o_i) -> skill FiLM(z_i) -> RNNLayer -> ACTLayer`.
- Low critic path is:
  `MLPBase(global_state) -> team-code FiLM(g) -> RNNLayer -> value`.
- Rollout stores actor/critic hidden states before action selection, global
  state, team code, log-probabilities, denormalized values, and env id.
- Low-level update is now MAPPO-style on-policy sequence PPO:
  per-env GAE(lambda), rollout-end bootstrap, recurrent sequence chunks,
  separate actor/critic optimizers, low-level ValueNorm, normalized target
  clipping, and PPO value prediction clipping.
- The older `RecurrentLowLevelPolicy` remains only as `gru_ctde` ablation; the
  original MLP low-level remains only as `feedforward` ablation.
- Verification on 2026-06-26:
  `py_compile` passed, `ha_ctse_process.smoke` passed, and a 4-step S7-S1
  strict-MAPPO tiny train completed with controlled low value loss.
- Low-level diagnostics added on 2026-06-26:
  `low_value_error_abs_mean`, `low_value_error_rmse`,
  `low_advantage_std`, `low_ratio_mean`, `low_clip_frac`,
  `low_approx_kl`, actor/critic grad norms, actor/critic hidden-state norms,
  skill/team-code usage entropy, skill/team-code return dispersion, and
  skill/team-code value-error dispersion.
- These metrics are exported to `metrics/train_updates.csv`, TensorBoard, the
  `standalone_update` log line, and two plots:
  `ha_ctse_low_level_diagnostics.png` and
  `ha_ctse_low_level_skill_team_diagnostics.png`.

Next structural slice:

1. Add explicit GAE(lambda) for recurrent low-level returns instead of pure
   Monte Carlo returns.  Done for the strict MAPPO path.
2. Add recurrent low-level diagnostics by skill/team-code: action entropy,
   value error, return mean, and hidden-state norm.  Done.
3. Revisit semantic pressure after the stronger discoverer has a short sanity
   run: process posterior can become auxiliary reward only if shortcut gaps and
   cooperation-credit diagnostics improve.

### 4. HMASD uses adaptive/structured exploration pressure

HMASD has separate entropy channels:

- team-code entropy coefficient;
- termination entropy coefficient;
- skill entropy coefficient;
- low-level action entropy coefficient;
- optional target-entropy adaptation.

The current standalone path has simpler fixed entropy pressure.  P0 shows large
high-level grad norms and high value losses, so entropy may be numerically
dominated by value-scale instability.

Migration implication:

- Split skill, duration, team-code, and low-level action entropy coefficients in
  the standalone path.
- Track their loss contribution relative to value loss.
- Consider target-entropy adaptation only after the reward/critic scale is under
  control.

### 5. HMASD high-level editing has keep/edit semantics and horizon masks

HMASD HA-CTSE path tracks requested edits, executed edits, H-min/H-max masking,
skill ages, suppressed edits, termination rate, duration target histogram, and
close reasons.

The standalone path currently samples a skill and a discrete lifetime when a
countdown expires.  This is simpler, but may make recovery from relay failure
too slow: once a poor skill/duration is selected, the agent may remain in a bad
relay role for many primitive steps.

Migration implication:

- Add explicit relay-failure early-renewal diagnostics first.
- Consider a relay-aware emergency termination option:
  if full disconnect or local backhaul loss persists, allow early skill renewal
  even before duration expiry.
- Treat this as a separate ablation, not as the default until diagnostics prove
  it is needed.

### 6. Current process outcomes are too generic

`ha_ctse_process/process_outcomes.py` already extracts coverage, throughput,
QoS, backhaul margin, energy, charging, and fallback reward/observation deltas.
It does not yet provide enough cooperation-credit diagnostics to explain why a
team succeeds or fails at stable connectivity.  The goal is not to make relay
chain output a first-class algorithm target.  The goal is to expose whether
skills, durations, and local actions are being assigned credit for their effect
on later team connectivity.

Useful relay/backhaul diagnostic proxies:

- mean/full-disconnect rate inside segment;
- segment starts disconnected and ends connected;
- segment starts connected and ends disconnected;
- delta `uavs_with_backhaul`;
- delta `connectivity_ratio`;
- delta/current `current_backhaul_served_users`;
- delta `backhaul_outage_ratio`;
- delta `relay_route_loss_ratio`;
- min/mean `min_serving_backhaul_bottleneck_mbps`;
- full-disconnect streak change;
- whether the acting UAV is on a routing path or critical relay path.

These fields should answer credit-assignment questions:

- Is a segment associated with later team service recovery or collapse?
- Does a skill create a stable cooperative role, or only change local movement?
- Are failures caused by never forming a chain, late formation, or chain break?
- Does the posterior/latent model learn cooperation-relevant semantics beyond
  duration, length, and raw return shortcuts?

Migration implication:

- Extend diagnostics before trusting process MI reward.
- Add segment-level relay/backhaul credit probes to train CSV and eval plots.
- Optional auxiliary heads may predict cooperation-relevant outcomes for
  representation learning, but they should remain off the reward path until
  ablation proves they improve task behavior rather than overfitting to relay
  proxies.

### Priority order after P0

Do not tune process reward first.  The audit indicates a larger structural gap:
cooperative credit assignment and low-level temporal control.

Recommended order:

```text
1. Add relay/backhaul cooperation-credit diagnostics, not reward targets.
2. Upgrade low-level policy/training toward recurrent MAPPO-style discoverer.
3. Add centralized low-level value or value normalization.
4. Add contribution-style diagnostics/baselines for agent role credit.
5. Optionally add cooperation-relevant auxiliary prediction heads for
   representation learning only.
6. Re-test reward-pure P0 with the stronger low-level/critic path.
7. Only then test process/semantic reward injection as a controlled ablation.
```

Decision rule:

- If reward-pure recurrent low-level still fails relay formation, inspect
  high-level skill/duration semantics and relay-aware early renewal.
- If recurrent low-level improves full-disconnect rate, the main missing HMASD
  bias was temporal low-level control and centralized value, not discriminator.
- If cooperation-credit diagnostics improve shortcut gaps and correlate with
  better eval behavior, then process reward may be reconsidered as a controlled
  ablation.

## 2026-06-27 Residual Process Posterior Slice

Motivation:

- The strict MAPPO low-level run improved implementation fairness but still
  showed weak cooperation learning and low-level reward oscillation.
- HMASD's discriminator/discoverer pair has useful semantic-pressure value, but
  a one-step discriminator is incompatible with the standalone process-core
  target.
- The new test should pressure the discoverer to produce segment-level skill
  semantics while explicitly rejecting trivial duration/length/reward shortcuts.

Implemented status:

- `ha_ctse_process/process_posterior.py` now trains a full segment posterior
  plus duration, segment-length, and reward-sum shortcut heads.
- `ha_ctse_process/standalone_agent.py` supports residual process reward modes:
  `residual_mi`, `positive_residual_mi`, `centered_residual_mi`, and
  `residual_mi_outcome`.
- `process_reward_injection` can target `none`, `high_only`, `low_only`, or
  `high_and_low`.
- Current preferred experiment is `residual_mi + low_only`, because it mirrors
  HMASD's semantic pressure on the discoverer without making the high-level
  controller chase a noisy auxiliary target first.
- New diagnostics are exported to logs, CSV, TensorBoard, and plots:
  `process_residual_mi_mean`, `process_residual_mi_positive_frac`,
  `process_shortcut_loss`, `process_shortcut_duration_acc`,
  `process_shortcut_length_acc`, `process_shortcut_reward_sum_acc`,
  `process_shortcut_max_acc`, and `posterior_acc_minus_shortcut_max`.
- Checkpoint loading uses non-strict process-posterior loading so old
  checkpoints do not fail because shortcut heads were added.

Verification:

```text
py_compile passed for process_posterior.py, standalone_agent.py, train.py,
eval_checkpoints.py, plotting.py, and smoke.py.

ha_ctse_process.smoke passed.

Tiny S7-S1 residual low-only train passed and logged:
process_resid_mi, process_shortcut_acc, posterior_gap_short, and
process_reward_low.
```

Current full-run command:

```powershell
& C:\Users\wu\.conda\envs\SB3\python.exe -m ha_ctse_process.train `
  --config ha_ctse_process.config `
  --scenario energy `
  --preset S7-S1 `
  --n_agents 6 `
  --collector_backend subproc `
  --num_envs 8 `
  --rollout_length 500 `
  --skill_interval 10 `
  --total_timesteps 1280000 `
  --eval_interval 80000 `
  --eval_episodes 20 `
  --save_interval 20 `
  --plot_interval 20 `
  --process_reward_mode residual_mi `
  --process_reward_injection low_only `
  --process_reward_coef 0.05 `
  --process_shortcut_coef 0.5 `
  --log_dir logs\ha_ctse_process_s7s1_6agent_residual_low_1280k
```

Codex runtime note:

- In the current Codex execution environment on Windows, `subproc` collector
  fails at `multiprocessing.Pipe()` with `PermissionError: [WinError 5]`.
- The user can still run the `subproc` command in a normal local terminal if
  desired.
- The background run launched from Codex on 2026-06-27 therefore uses the same
  algorithm settings with `collector_backend=sync`, `num_envs=8`, and log dir:

```text
logs\ha_ctse_process_s7s1_6agent_residual_low_sync_1280k_full
```

Read this run by comparing:

- eval reward/coverage/qos/throughput trend;
- `posterior_acc_minus_shortcut_max`;
- `process_residual_mi_mean` and positive fraction;
- `credit_full_disconnect_mean`;
- low-level value error, KL, clip fraction, and grad norms.

Decision rule after the run:

- If `posterior_acc_minus_shortcut_max <= 0` for most of training, the segment
  posterior is learning shortcuts rather than useful behavior semantics.
- If shortcut gap improves but eval reward does not, keep it as a diagnostic or
  reduce the reward coefficient.
- If shortcut gap and cooperation-credit metrics improve together, test
  `high_and_low` and `centered_residual_mi` as the next ablations.

## 2026-06-27 Semantic-Pressure Correction

The 1.28M residual low-only run showed that process posterior training was
connected but not yet solving semantic skill separation:

- `process_residual_mi_mean` stayed negative late in training;
- `posterior_acc_minus_shortcut_max` was not stably positive;
- `skill_switch_rate` stayed around 0.75, too high for stable UAV service and
  relay roles;
- low-level PPO clip fraction was high, and high-level bootstrap/grad norms had
  large spikes.

Code changes made after this diagnosis:

- `skill_lifetime_candidates` default changed from short/regular candidates to
  `(3, 7, 13, 24)`, corresponding to 30/70/130/240 primitive steps when
  `skill_interval=10`.
- Low-level PPO now has an independent `low_clip_epsilon`; default is 0.1 while
  the high-level `clip_epsilon` remains 0.2.
- Added `process_reward_warmup_steps`: process posterior and shortcut heads are
  trained during warmup, but process reward is not injected into policy updates.
- Added `process_shortcut_margin` and `process_shortcut_margin_coef`: full
  segment posterior is explicitly penalized unless it beats the best
  prior/duration/length/reward shortcut by a margin.
- Startup logs now print `process_warmup_steps`, `process_shortcut_margin`,
  `process_shortcut_margin_coef`, `clip`, `low_clip`, and
  `duration_candidates`.
- Train CSV/TensorBoard now include `process_shortcut_margin_loss` and
  `process_reward_warmup_active`.

Verification:

```text
py_compile passed.
ha_ctse_process.smoke passed.
Tiny S7-S1 train confirmed:
duration_candidates=(3, 7, 13, 24), low_clip=0.1,
process_warmup_steps, process_shortcut_margin, and process_margin_loss.
```

## 2026-06-27 Dense Transition Semantic Discriminator

Motivation:

- Segment posterior receives one sample per completed skill-lifetime segment.
  In long-horizon UAV service tasks, this is too sparse compared with HMASD's
  discriminator/discoverer pressure.
- The new algorithm should not import the legacy discriminator objective, but
  it should recover the useful idea: dense semantic pressure that pushes skill
  labels to correspond to behavior, not only duration or reward shortcuts.

Implemented status:

- Added `TransitionSkillDiscriminator` in
  `ha_ctse_process/process_posterior.py`.
- It predicts skill identity from primitive transition features:
  `o_t, a_t, delta_o_t, r_t, g`.
- `StandaloneProcessAgent.process_update` now expands completed segments into
  dense transition samples with a configurable cap
  `transition_skill_max_samples`.
- Transition discriminator loss is optimized by `process_opt` together with
  the process encoder/posterior stack.
- Pre-update transition MI,
  `log q(z | o,a,delta_o,r,g) - log p(z | g)`, can inject a small positive
  low-level semantic reward after `transition_skill_reward_warmup_steps`.
- It does not inject high-level rewards and does not redefine relay-chain
  output as a first-class objective.

New config/CLI fields:

- `use_transition_skill_discriminator`
- `transition_skill_condition_on_team`
- `transition_skill_coef`
- `transition_skill_prior_coef`
- `transition_skill_reward_coef`
- `transition_skill_reward_warmup_steps`
- `transition_skill_reward_clip`
- `transition_skill_max_samples`
- `--disable_transition_skill_discriminator`
- `--disable_transition_skill_team_conditioning`

Diagnostics:

- `transition_skill_samples`
- `transition_skill_available_samples`
- `transition_skill_loss`
- `transition_skill_prior_loss`
- `transition_skill_acc`
- `transition_skill_mi_mean`
- `transition_skill_mi_positive_frac`
- `transition_skill_reward_mean`
- `transition_skill_reward_active`
- `transition_skill_log_q_mean`
- `transition_skill_log_p_mean`

Verification:

```text
py_compile passed.
ha_ctse_process.smoke passed.
Tiny S7-S1 train passed and logged:
trans_samples, trans_acc, trans_mi, trans_reward, trans_active.
```

Decision rule:

- If `transition_skill_acc`/`transition_skill_mi_mean` rise but eval reward and
  cooperation-credit metrics do not improve, reduce
  `transition_skill_reward_coef` or keep this component diagnostic-only.
- If transition semantics improve before segment posterior gap improves, keep
  the dense discriminator and delay segment-level reward injection longer.
- If both transition MI and segment residual MI remain weak, revisit skill
  generator/context architecture rather than increasing reward coefficients.

## 2026-06-27 Intrinsic Reward Reconstruction

Motivation:

- HMASD's high-level reward includ