# R22 Two-Clock ELBO Mainline Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the 2026-07-05 GPT-5.5 review into an executable R22 plan: make R21/v6 the active HA-CTSE mainline, demote R12/R19 to substrate/control roles, and derive a two-clock objective for slow sampled team intent `Z` plus fast asynchronous individual skills `z_i`.

**Architecture:** Three time scales: OPT recognition substrate (`omega_t`, compact `c_t`, optional `kappa_t`) -> slow sampled team commitment `Z_m` held for `K_team` checks -> asynchronous per-agent response skills `z_i` docked to current `Z`. The objective work must decide how team discriminator, individual/coordinator residual, entropy, and any cross-layer term compose without double-counting.

**Tech Stack:** Markdown memory files, HA-CTSE Python training code under `ha_ctse_process/`, R21 tests under `tests/r21_team_intent_test.py`, cloud/local runners in `scripts/`, experiment logs and CSVs under `logs*` and `dist/`.

---

## Stage R22-0: Adopt The Review Without Drifting The Live Experiment

Status: COMPLETE on 2026-07-05.  Cross-validation, attention pointer,
principles, and implementation plan were aligned before R22-1/R22-4 docs were
written.

- [x] Record the GPT-5.5 advice as a modified-accepted cross-validation entry in `memory/cross_validation.md`.
  - Source: GPT-5.5 Pro, provided by the user on 2026-07-05.
  - Disposition: modified-accepted.
  - Accepted: R21/v6 becomes mainline; R12 becomes recognition substrate/control; R19 remains mechanism-negative control unless later reward-on logs contradict; derive two-clock ELBO before adding more rewards.
  - Modified: do not block the already launch-ready R21 and HMASD baseline runners on the derivation; run the derivation in parallel.

- [x] Update `memory/ATTENTION_POINTER.md` so the first-read focus says:
  - Active algorithmic focus is R21/v6 two-clock hierarchy.
  - R12/OPT situation remains recognition substrate, not primary engine.
  - R22 plan path is `docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md`.

- [x] Update `memory/ALGORITHM_PRINCIPLES.md` with a top-level active amendment:
  - OPT recognition identifies interaction situation.
  - Sampled `Z` supplies slow team commitment and non-vacuous team discriminator pressure.
  - Asynchronous `z_i` supplies individual response and variable lifetime.
  - Entropy is allowed as a derived objective/constraint, not as a direct heterogeneity reward.

- [x] Update `memory/IMPLEMENTATION_PLAN.md` with a `Round 22 Two-Clock Objective Unification` section and mark the current plan as `planned / theory-first / no new reward yet`.

Validation:

```powershell
rg -n "Round 22|two-clock|R21/v6|recognition substrate" memory\ATTENTION_POINTER.md memory\ALGORITHM_PRINCIPLES.md memory\IMPLEMENTATION_PLAN.md memory\cross_validation.md
```

Expected output: all four files contain the R22 plan or active-contract references.

## Stage R22-1: Write The Two-Clock Derivation Document

Status: COMPLETE on 2026-07-05.  Output:
`memory/R22_TWO_CLOCK_ELBO.md`.  Subagent spec review approved.  Quality review
initially flagged five implementation-risk issues (Z/z_i naming, alpha sign,
clock normalization, detached nulls, tau/r notation); all were fixed and
re-reviewed as approved.

- [x] Create `memory/R22_TWO_CLOCK_ELBO.md`.

- [x] Include the model variables:

```text
s_t, o_{i,t}                       environment and local observations
c_t, omega_t = OPT(s_t, o_{1:n,t})  continuous recognition substrate
Z_m ~ pi_Z(Z | c_t, omega_t)        slow sampled team commitment
z_{i,\tau} ~ pi_z(z_i | Z_m, c_t, omega_t, o_{i,\tau}, roster_\tau)
a_{i,t} ~ pi_l(a_i | o_{i,t}, z_{i,\tau})
T_i                                asynchronous individual skill lifetime
```

- [x] State the clock relation:

```text
Recognition clock: every check interval.
Team commitment clock: every K_team checks or rollout reset.
Individual response clock: each agent renews asynchronously while docking to held Z.
```

- [x] Write the factorization for one rollout block:

```text
p_\theta(\tau, Z, z_{1:n})
= p(env)
  * product_m pi_Z(Z_m | c_m, omega_m)
  * product_i product_{renewals r} pi_z(z_{i,r} | Z_{m(r)}, c_r, omega_r, o_{i,r}, roster_r)
  * product_t product_i pi_l(a_{i,t} | o_{i,t}, z_{i,active(t)})
```

- [x] Derive the candidate objective terms:

```text
J = E[R_env]
  + lambda_team * E[log q_D(Z | joint_future_or_state) - log p_hat(Z | context)]
  + lambda_ind  * E[log q_d(z_i | o'_i, kappa_or_c, Z) - log pi_z_stored(z_i | Z, context, roster)]
  + alpha_Z     * H(pi_Z)
  + alpha_z     * H(pi_z)
  + alpha_T     * H(duration/edit head)
  + alpha_a     * H(pi_l)
  + optional lambda_cross * I(Z ; joint response / roster / xi)
```

- [x] Add a double-count audit table:

| Term | Current code source | What it explains | Possible double count | Decision rule |
| --- | --- | --- | --- | --- |
| team discriminator | `team_intent.py` | team-level commitment semantics | overlaps with cross-layer response term | keep unless team term is fully explained by individual residual |
| individual residual | prototype discriminator path | per-agent skill response semantics | can double-count team if `Z` is directly leakable | keep only with stored assignment/null and leak audit |
| coordinator residual | R15/R16 path | AR/roster assignment pressure | stale if R21 team term dominates | prune/absorb after R21 read |
| entropy/floor | config/train guards | exploration and non-collapse | can become forced heterogeneity | convert to target-entropy constraint |
| R19 transition residual | `outcome_residual`/transition heads | recognition-only transition control | competes with team intent | control only unless positive MI + task gain |

- [x] End the derivation with three falsifiable predictions:
  - R21 team-disc reward should improve `Z` usage and task stability beyond S-base if sampled commitment is the missing engine.
  - If `team_disc_acc` is healthy but task metrics do not improve, the bound is likely missing cross-layer usefulness or has scale/double-count issues.
  - If `Z` collapses or has too few samples, the failure is credit-triangle/sample-efficiency, not proof that recognition substrate is enough.

Validation:

```powershell
Test-Path memory\R22_TWO_CLOCK_ELBO.md
rg -n "double-count|lambda_team|lambda_ind|I\\(Z" memory\R22_TWO_CLOCK_ELBO.md
```

Expected output: the file exists and contains the objective, audit, and cross-layer term.

## Stage R22-2: Preserve R21 And HMASD As The Immediate Experiment Track

- [ ] Keep `EXP-20260705-r21-team-intent` as the active HA-CTSE mechanism read.
  - Do not wait for R22 derivation to launch if cloud capacity is available.
  - R21 command remains the cloud 64-env direct runner:

```bash
bash scripts/run_r21_team_intent_cloud_64env.sh --dry-run

EXPERIMENTS=r21_z_probe,r21_z_reward \
SEEDS=1 \
TOTAL_TIMESTEPS=960000 \
NUM_ENVS=64 \
DEVICE=cuda \
bash scripts/run_r21_team_intent_cloud_64env.sh
```

- [ ] Keep `EXP-20260705-hmasd-currentenv-baseline` as a blocking calibration read.
  - It must use S7-S1, 6 agents, 64 envs, seeds 1 and 2, around `1e6` steps.
  - It must log `coverage_eq1_step_fraction`, `coverage_eq1_episode_fraction`, `zero_throughput_episode_fraction`, and `throughput_gt5_step_fraction`.

- [ ] Do not add new R19 coefficient sweeps.
  - R19 reward-off probe is mechanism-negative unless a complete reward-on log later shows sustained positive `team_t_mi` and task gain.
  - R19 remains a recognition-only control, not the main team engine.

Validation:

```powershell
rg -n "EXP-20260705-r21-team-intent|EXP-20260705-hmasd-currentenv-baseline|EXP-20260704-r19-team-transition" memory\ExpRecord.md
```

Expected output: all three experiment records remain findable, with R21/HMASD launch-ready and R19 not expanded.

## Stage R22-3: Add Only Missing Diagnostics Needed By The Bound

Do this after R22-1 unless a log read shows the metrics are already present.

Status: IMPLEMENTED on 2026-07-06 after external review.  Existing before the
edit: `z_usage_entropy`, `team_disc_reward_env_ratio`, `z_boundary_trunc_rate`,
and `z_boundary_trunc_rate_dur3/7/13/24`.  Added in this stage:
`z_decisions_per_update`, `z_advantage_mean/std/var`, and
`combined_intrinsic_env_ratio` with guard counters.

- [x] Audit existing fields:

```powershell
rg -n "z_decisions|z_advantage|team_disc_reward_env_ratio|combined_intrinsic|z_boundary_trunc_rate_dur|z_usage_entropy" ha_ctse_process memory scripts tests
```

- [x] If missing, add R21 diagnostic fields:
  - `z_decisions_per_update`
  - `z_advantage_mean`
  - `z_advantage_std`
  - `z_advantage_var`
  - `combined_intrinsic_env_ratio`

- [x] Implementation locations:
  - `ha_ctse_process/standalone_agent.py`: compute values in the same metrics dictionary that currently emits `z_usage_entropy`, `team_disc_acc`, and `z_boundary_trunc_rate`.
  - `ha_ctse_process/train.py`: propagate new metrics into console/TensorBoard/CSV.
  - `ha_ctse_process/plotting.py`: include the fields in R21 diagnostic plots.
  - `tests/r21_team_intent_test.py`: add a regression test that R21 metrics include the new keys when team intent is enabled.

- [x] Keep all diagnostics default-on when R21 is enabled and reward-neutral. Do not add a new intrinsic reward in this stage.

Validation:

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r21_team_intent_test.py -q
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile ha_ctse_process\standalone_agent.py ha_ctse_process\train.py ha_ctse_process\plotting.py
```

Expected output: R21 tests pass; compile exits with code 0.

## Stage R22-4: Convert Entropy Policy From Patch To Design

Status: COMPLETE on 2026-07-05.  Output:
`memory/R22_TARGET_ENTROPY_DESIGN.md`.  Subagent spec review approved.  Quality
review initially flagged Z/z_i metric ambiguity and alpha-loss sign; both were
fixed and re-reviewed as approved.

- [x] Create `memory/R22_TARGET_ENTROPY_DESIGN.md`.

- [x] Specify per-head targets:

```text
H_target_Z        for slow team intent pi_Z
H_target_z        for individual skill pi_z
H_target_duration for duration/edit head
H_target_action   for low-level action policy
```

- [x] Specify the target-entropy Lagrangian form:

```text
L_alpha_head = alpha_head * stopgrad(H_target_head - H_observed_head)
```

- [x] State explicitly:
  - This is a design document only in R22.
  - Existing duration/Z entropy floors remain stabilizer flags, not final mechanism claims.
  - Do not implement automatic temperature until R21 and HMASD baseline reads show which head actually collapses under useful learning.

Validation:

```powershell
Test-Path memory\R22_TARGET_ENTROPY_DESIGN.md
rg -n "H_target_Z|L_alpha_head|stabilizer" memory\R22_TARGET_ENTROPY_DESIGN.md
```

Expected output: design doc exists and labels floors as stabilizers, not heterogeneity rewards.

## Stage R22-5: Prune Or Freeze Non-Mainline Mechanisms

- [ ] Add a mechanism-budget table to `memory/IMPLEMENTATION_PLAN.md`:

| Mechanism | Current status | R22 disposition |
| --- | --- | --- |
| R21 sampled team intent Z | mainline | keep and test |
| OPT omega/c/kappa | substrate | keep as recognition input/control |
| R12 situation hazard | deferred | no reward/hazard expansion until after R21/HMASD read |
| R19 transition residual | control | no new sweep unless complete reward-on contradicts negative probe |
| g/team bridge | deprecated | no new mechanism conditions on it |
| target kappa* | deferred | only revisit if two-clock ELBO or R21 failure points to target commitment |
| topology/communication rewards | diagnostic only | never use as intrinsic objective |

- [ ] Put a rule in the plan:

```text
Every new mechanism must retire, absorb, or formally supersede one existing mechanism. Terms absent from the R22 bound default to deletion candidates, not protected modules.
```

Validation:

```powershell
rg -n "Mechanism Budget|deletion candidates|R21 sampled team intent" memory\IMPLEMENTATION_PLAN.md
```

Expected output: the mechanism-budget table is visible.

## Stage R22-6: Decide After First R21/HMASD Reads

- [ ] At R21 160k:
  - Read `team_disc_acc` shape:
    - gradual climb -> continue to 320k.
    - flat -> inspect `z_decisions_per_update`, per-duration truncation, `z_usage_entropy`.
    - instant near 1.0 -> leak audit `q_D` inputs before any interpretation.

- [ ] At R21 320k:
  - If `Z` is healthy and task is not worse, continue to 960k.
  - If `Z` is healthy but task worse, inspect reward ratios and double-count table before changing code.
  - If `Z` is unhealthy, stop and fix credit-triangle/sample-efficiency first.

- [ ] At HMASD 1e6:
  - If HMASD reaches the expected S7-S1 parity, keep HA-CTSE parity gate unchanged.
  - If HMASD does not reach parity under the current env/code, recalibrate the benchmark before judging HA-CTSE failure.

Validation:

```powershell
rg -n "team_disc_acc|coverage_eq1_step_frac|zero_throughput_ep_frac" <run-log-or-train_updates.csv>
```

Expected output: relevant metrics are available for the pre-registered read.

## Out Of Scope For This Plan

- Do not implement new rewards before `memory/R22_TWO_CLOCK_ELBO.md` exists.
- Do not revive `g` or team bridge.
- Do not expand R19 coefficient sweeps.
- Do not use raw communication metrics as intrinsic reward.
- Do not claim HA-CTSE parity from 160k/320k mechanism gates.
- Do not promote `memory/ALGORITHM_DESCRIPTION_v6.md` to canonical without adding an implementation/validation status box.
