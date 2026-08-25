# R23: Actionable Team Intent — design specification (PR-1)

Author: CC (Claude), Architect role (user-authorized design + diagnostic-only
capacity-gate script; NO training, NO algorithm-code changes yet, NO runs beyond
the diagnostic gate). Sources: `memory/R21_AUTOPSY_REPORT.md` (my autopsy),
`memory/advice_gpt.md` (2026-07-06 R23 design advice), `memory/cross_validation.md`.
Status: **accepted forward design line** (supersedes "R21/v6 sampled-Z mainline",
now negative evidence). This note is a reviewable objective + staged plan, not an
implementation authorization. Codex is the exclusive implementer when authorized.

## 0. Core correction (why R23 exists)

R21 order (wrong): `sample Z → train q_D(Z|s_next) → hope Z becomes meaningful`.
Autopsy proved that fails: forced-Z assignment KL ≈0.002 at random-init AND final
(Z never actionable), team-disc data contract aligned so `q_D≈chance` is genuine
no-signal, and `K_team=48≈episode` degraded the two-clock to ~one Z/episode.

R23 order (correct): **`sample Z → force/verify Z changes joint assignment ξ →
verify ξ changes behavior/effect → only then enable q_D(Z|future effect)`**.

> One-line thesis: **the team discriminator is an amplifier, not an initiator.**
> If the `Z → ξ` chain is not established first, even the strongest `q_D` reads chance.

Vocabulary:
```text
c, ω = OPT recognition context (substrate; NOT a team option)
Z    = sampled slow team intent
ξ    = joint assignment structure: skill logits/probs, duration probs, edit probs,
       edited subset, roster-conditioned AR assignment pattern
z_i  = agent i individual skill (per renewal)
a_i  = low-level primitive action
```

## 1. PR-1 two-clock PGM (Task 1)

Variables: `c_t,ω_t` (OPT substrate) → `Z_m` (slow intent) → `ξ_m` (joint
assignment) → `z_{i,r}` (async individual skill at renewal r) → `a_{i,t}` →
`O_t` (optimality from env reward).

Factorization:
```text
p(τ,Z,ξ,z,a) = p(env)
  · ∏_m π_Z(Z_m | c_m, ω_m)
  · ∏_m π_ξ(ξ_m | Z_m, c_m, ω_m)                              # <-- the missing R21 link
  · ∏_{i,r} π_z(z_{i,r} | ξ_m, Z_m, c_r, ω_r, o_{i,r}, roster_r)
  · ∏_{i,t} π_l(a_{i,t} | o_{i,t}, z_{i,active(t)})           # low level BLIND to Z/c
```
The R21 defect was the absent `Z → ξ` edge, not a missing `q_D`.

Candidate objective (terms to compose/audit for double-counting in PR-1, NOT a
reward stack to ship):
```text
J = E[external return]
  + λ_A · I(Z ; ξ | c,ω)                          # LOAD-BEARING (actionability)
  + λ_D · I(Z ; future_joint_effect | c,ω)        # gated by actionability
  + λ_d · Σ_i I(z_i ; local_effect_i | Z, ξ, c,ω) # individual, Z/ξ-conditioned
  + entropy: H(Z|c,ω), H(ξ|Z,c,ω), H(z_i|ξ,Z,c,ω), H(dur/edit), H(a)
```
PR-1 must decide: is `I(Z;ξ|c,ω)` required (working answer: yes); when is
`I(Z;future|c,ω)` legal (only after actionability); does `I(z_i;local|Z,ξ,c,ω)`
replace the old `q_d` (working answer: it is the process/effect version of HMASD's
`q_d(z_i|o_i,Z)`); which entropies are derived constraints vs stabilizers; how
two-clock credit handles `K_team` and rollout truncation. Do NOT code `I(Z;ξ)` as a
reward before this note + a double-count audit are complete.

## 2. R23-0 static architecture capacity gate (Task 2) — RESULT: FAIL

Script (diagnostic-only, added this task): `scripts/r23_capacity_gate.py`. It
forces Z=0..C-1 on a fixed in-distribution batch (48 real S7-S1 env resets, B=288)
and measures how much Z moves the assignment heads. **No training.**

```text
PYTHONPATH=. python scripts/r23_capacity_gate.py --checkpoint <ckpt|random> \
    [--structure-from <ckpt>] [--gate 0.02]
```

Gate: PASS iff `forced_Z_skill_KL_mean ≥ 0.02` (≈10× the R21 decorative band
~0.002) AND a visible effect in ≥1 assignment head.

Measured (R21 checkpoints + the implemented fix below):
```text
                                  skill_KL_mean  dur_KL_mean  gate(>=0.02)
current arch, R21 final               0.00223       0.00139       FAIL
current arch, random-init             0.00233       0.00104       FAIL
NEW arch flag ON (gain=1.0), rand     0.12053       0.42293       PASS
NEW arch flag OFF (default), rand      0.00142       0.00095       FAIL (S-base kept)
```

Interpretation: the current architecture **FAILS the capacity gate even at
random-init** → the `Z → assignment` structural gain was too weak (an architecture
problem, not only an objective one). The ~0.5 argmax churn at ~0.002 KL is a
flat/under-confident policy nudged by noise, not coordination. The §3 fix below
(default-off `z_assignment_residual_gain`) makes it **PASS** (skill KL 0.12, 60×
the band) while default-off keeps the S-base bit-identical. There is currently
**no categorical edit head** (high policy exposes skill + duration only; "edit"
lives in the AR/roster prefix), so `ξ`'s edit component must be added later if it
is to be a first-class assignment head.

## 3. Architecture correction (Task 3) — IMPLEMENTED (Option C, default-off)

STATUS: implemented + verified 2026-07-06 (CC Executor). Option C (direct residual
logit path) landed default-off behind `z_assignment_residual_gain` (config +
`--z_assignment_residual_gain` CLI). In `SkillDurationPolicy.logits`:
`skill_logits += gain·W_Z(team_vector)`, `duration_logits += gain·U_Z(team_vector)`;
`gain=0.0` (default) creates no residual modules → S-base bit-identical. Wiring:
`ha_ctse_process/config.py` (`z_assignment_residual_gain=0.0`),
`ha_ctse_process/standalone_agent.py` (`SkillDurationPolicy` + agent construction),
`ha_ctse_process/train.py` (CLI + override). Tests:
`tests/r23_actionable_team_intent_test.py` (3 pass: actionability with gain>0,
default-off preservation, config→agent wiring); `tests/r21_team_intent_test.py`
still 7/7. Capacity gate: flag-on random-init PASS (skill KL 0.12). The low-level
actor input is unchanged (still blind to Z/c), and the S-base selection path is
untouched (no policy-path confound). NOTE: `gain=1.0` is strong; training should
use a small warmed/annealed gain per §4.

Menu considered (Option C implemented; A/B/edit-head remain future options if the
residual path proves insufficient; keep init small to avoid Z domination):
```text
A. Z as the true AR first-token: the skill decoder / AR assignment consumes the Z
   embedding as its first token, not a weak team_vector side input.
B. Z-FiLM on assignment heads: Z-conditioned affine/FiLM modulation of the
   skill / duration / (new) edit heads.
C. Direct small residual logit path:
     logits_skill_i    += W_Z e_Z
     logits_duration_i += U_Z e_Z
     logits_edit_i     += V_Z e_Z      (requires adding an edit head)
   small coef / init so Z does not dominate from the start.
D. DO NOT change the low-level actor input: a_i ~ π_l(a_i | o_i, z_i) stays
   blind to Z/c/g.
E. Match the S-base selection path as much as possible: do NOT wholesale-replace
   the assignment path the way R21 did (that caused the policy-path regression
   confound). Re-run R23-0 after the change; require random-init skill_KL clearly
   above the decorative band before proceeding.
```
Re-verification: `scripts/r23_capacity_gate.py --checkpoint random` on the new
architecture must PASS before Stage R23-1.

## 4. Actionability objective (Task 4) — Option A IMPLEMENTED via DRY reuse

STATUS: implemented + smoke-verified 2026-07-06 (CC Executor). KEY FINDING:
Option A already exists as `ha_ctse_process/g_info_objective.py::GInfoObjective`
(the Round-10 "g-info objective"): it enumerates the team codes via
`bridge.code_embedding`, computes normalized `I(Z; skill|c,ω)` and
`I(Z; duration|c,ω)`, has coef/warmup/anneal, is default-off, logs forced-Z
pairwise KL/TV, never touches the low actor, and is already wired into the high
update (`standalone_agent.py:5542`). It FAILED in Round 10 only because Z was
decorative — the exact defect R23-0 fixes. So no new module (mechanism-budget /
DRY rule satisfied).

**R23-1 recipe (no new code):**
```text
--z_assignment_residual_gain <small, e.g. 0.3-0.5>   # R23-0 architecture (Z can move ξ)
--enable_team_intent --enable_team_disc_probe        # Z active, q_D OFF (probe only)
--team_intent_k 8 --skill_lifetime_candidates 1,2,3,4  # Choice-1 timing
--enable_g_info_objective --g_info_coef_skill <small> --g_info_warmup_steps <w>
# g_info_anneal_steps optional; NO --enable_team_disc_reward (gated to R23-3)
```
Tests (`tests/r23_actionable_team_intent_test.py`): actionability is live with the
residual (`g_info_skill_mi > 0.02`, loss < 0) and decorative without it
(`< 0.005`) — this reproduces the Round-10 failure and proves R23-0 is the
precondition. Smoke (128 steps, gain 0.5, coef_skill 0.02): ran clean (exit 0),
`g_info_objective_active=1`, `g_info_skill_mi≈0.023`, forced-Z skill KL
`g_itv_kl_skill≈0.099` (~50× the R21 band), `g_info_loss≈-0.00046`, live-rollout
`z_assignment_itv` rose to 0.03-0.13 (R21 was ~0.002), no guard kills.
CAVEAT: the smoke proves live+non-crashing wiring, NOT the R23-1 verdict. The real
read (does MI/forced-Z-KL RISE under training AND task health hold?) needs a proper
run (GPU) + authorization. Watch: `g_itv_kl_skill`↑, `g_info_skill_mi`↑,
`z_usage_entropy` healthy, coverage/qos not collapsing.

Two candidate forms; A (above) is implemented. B (residual q_A) remains the
ELBO-faithful alternative if A's differentiable MI proves too weak.

**Option A — soft decision-level usage loss** (enumerate Z, high-level only):
```text
L_action = -λ_skill·I(Z;π_z|c,ω) -λ_dur·I(Z;π_dur|c,ω) -λ_edit·I(Z;π_edit|c,ω)
I(Z;π_z|c,ω) ≈ H(mean_Z π_z(·|c,ω,Z)) - mean_Z H(π_z(·|c,ω,Z))   # per head
```
**Option B — assignment residual discriminator** (closer to ELBO):
```text
R_action = log q_A(Z | ξ, c,ω) - log q_prior(Z | c,ω)
```
Guardrails (both): small coef; warmup only; anneal after `forced_Z_KL` passes the
floor; **high-level only**; **no communication fields**; **no low-level actor
input change**. Success criterion is NOT high `q_A` accuracy but:
`forced_Z_assignment_KL ↑`, `ξ` changes with Z, task health does not collapse.

## 5. Team-disc gate (Task 5) — IMPLEMENTED (hard rule)

STATUS: implemented + smoke-verified 2026-07-06 (CC Executor). Default-off
(`team_disc_actionability_floor = 0.0` → no gate → R21-compatible).
```text
R_team = log q_D(Z | s_next, c,ω) - log q_prior(Z | c,ω)
ENABLE iff:  team_disc_actionability_floor <= 0   (gate disabled)
             OR  last measured forced-Z skill KL (g_itv_kl_skill) >= floor
ELSE:        team_disc_reward = 0   (logged: team_disc_reward_gated_off=1)
```
Wiring: `config.team_disc_actionability_floor`; `SkillDurationPolicy` unchanged;
`standalone_agent._team_disc_actionability_gate_open()` gates `reward_active` in
`_team_intent_rollout_update`; the high update caches `_last_forced_z_assignment_kl
= g_itv_kl_skill` (one-update lag, since the team reward is applied earlier in the
step — update 1 reads 0 → safely gated off); `--team_disc_actionability_floor` CLI;
new logged fields `team_disc_reward_gated_off`, `team_disc_forced_z_kl`. Test
(`tests/r23_actionable_team_intent_test.py::test_r23_3_...`): floor 0 → open; floor
0.05 with KL 0.02 → gated off; KL 0.10 → open. Smoke (floor 0.05, warmup 0): update
1 forced-Z KL 0 → gated_off=1 (reward not applied); update 2 forced-Z KL 0.059 ≥
floor → applied (192 steps), then the pre-existing reward-ratio guard killed the
degenerate tiny-smoke ratio (11×) — expected, not a defect; composes correctly.
R21 proved ungated `q_D` is decorative; this gate is non-negotiable. Floor 0.05 is
the current default; tune against the R23-1 forced-Z KL band (~0.1 with gain 0.5).

## 6. Individual skill term

Retain individual discoverer pressure but conditional on Z and ξ (process/effect
version of HMASD's `q_d(z_i|o_i,Z)`):
```text
R_ind_i = log q_d(z_i | local_effect_i, Z, ξ, c,ω) - log q_prior(z_i | Z, ξ, c,ω)
```
First version reward-off probe only: does z_i produce local effect beyond the
Z/ξ/context prior? No low-level reward initially; shortcut-controlled.

## 7. K / duration design (Task 6) — Choice 1 first

```text
Choice 1 (R23 mechanism test):  episode ≈ 50 checks, K_team = 8,
  duration candidates = {1,2,3,4}  ->  K ≈ 2·max_dur, ~6 Z periods/episode,
  within-episode Z variation for q_D, long-duration truncation no longer tautological.
```
**Caveat (state explicitly in every read): Choice 1 tests whether an actionable Z
can be learned; it does NOT prove the asynchronous long-lifetime contribution.**
Choice 2 (true parent-child decoupling: Z boundaries do not truncate active z_i;
each z_i stores birth_Z/birth_context; new renewals dock to current Z) is DEFERRED
until Z actionability is proven.

## 8. Staged experiment matrix

```text
R23-0 static capacity gate  : DONE. Current arch FAIL (skill_KL~0.002); §3 fix
                              (z_assignment_residual_gain=1.0) PASS (skill_KL 0.12).
                              Architecture correction landed default-off + tested.
R23-1 actionability-only     : IMPLEMENTED (DRY reuse of g-info objective) + smoke-
                              verified live/non-crashing (see §4). Recipe in §4.
                              NEEDS a real run (GPU) for the verdict.
   pass: forced_Z_assignment_KL ↑, dur/edit KL ↑, q_A_gain>0, Z-usage healthy,
         task not catastrophic.
   fail: KL unchanged (objective/arch too weak) | KL↑ but task collapse (churn ->
         reduce/anneal coef).
R23-2 team-disc probe        : q_D probe already exists (`--enable_team_disc_probe`,
                              reward OFF); run it on top of R23-1. No new code. Runner
                              arm `r23_1_action` already carries the probe.
   pass: team_disc_acc > chance (not leak-saturating), residual_gain>0.
   fail: forced_Z_KL>0 but disc chance -> ξ changes but joint behavior doesn't.
R23-3 team-disc reward       : IMPLEMENTED — `--enable_team_disc_reward` + hard gate
                              `--team_disc_actionability_floor` (see §5); default-off,
                              smoke-verified. Runner arm `r23_3_reward`. Needs a run.
   pass: reward/coverage/qos/throughput ↑, zero_throughput ↓, cov_eq1_step_frac ↑,
         variance ↓, forced_Z_KL stays nonzero, residual stays positive,
         team_disc_reward_gated_off falls to 0 after actionability passes.

## Runners (for the overnight server run)

```text
scripts/run_r23_actionable_team_intent_cloud_64env.sh   # Linux/CUDA/64env (primary)
  arms: r23_arch_only, r23_1_action, r23_3_reward ; Choice-1 (K=8, durations 1,2,3,4)
  bash scripts/run_r23_actionable_team_intent_cloud_64env.sh --dry-run   # preflight
  EXPERIMENTS=r23_arch_only,r23_1_action,r23_3_reward SEEDS=1 \
    bash scripts/run_r23_actionable_team_intent_cloud_64env.sh
scripts/run_r23_actionable_team_intent_local_cuda.ps1   # local Windows/CUDA mirror
```
Both validated by dry-run 2026-07-06. Read order: 160k forced-Z KL shape, 320k
actionability gate (g_itv_kl_skill↑, g_info_skill_mi↑, Z-usage healthy, task not
collapsing), then 960k task gate; for r23_3_reward also watch
team_disc_reward_gated_off / team_disc_forced_z_kl.
R23-4 individual q_d process : + q_d(z_i|local_effect,Z,ξ,c,ω), prior/shortcut-controlled.
```

## 9. What NOT to do now (accepted stop list)

```text
HMASD current-env rerun (baseline is considered established/sufficiently tested per
  user 2026-07-06 — at most ONE appendix/sanity run for the paper, NOT blocking);
R21 seed2 / R21 sweep / R19 sweep / R12 hazard-DADS / target-kappa* / g-revival;
entropy auto-temperature (SAC) implementation — write derived-vs-stabilizer split first;
new topology-role reward.
```

## 10. Open decisions (need user / implementer)

```text
- Who implements the §3 architecture change + R23-1 objective (Codex, on authorization)?
- Edit head: adding a categorical edit head to π_ξ is an algorithm change (deferred).
- Floor value for §5 gate: fix in PR-1 (candidate ~0.02 or run-calibrated).
- Confirm Choice-1 K=8 / durations {1,2,3,4} for the first mechanism test.
```
Reproduction of the R23-0 result: `PYTHONPATH=. python scripts/r23_capacity_gate.py
--checkpoint <r21_final.pt>` and `--checkpoint random --structure-from <r21_final.pt>`.

## 11. Post-320k-read forward plan (2026-07-06 addendum)

> STATUS 2026-07-06→07 (CC Executor, user-authorized): (a)–(e) IMPLEMENTED default-off,
> TDD. T2 gradient audit verdict = **SCALE/FORM** (g-info grad into the Z path <2% of
> PPO and self-stalling — not a wiring bug), so q_A is the confirmed main line.
> The implementation modules are
> `ha_ctse_process/assignment_actionability.py` (q_A) + `ha_ctse_process/team_effect_targets.py`
> (reward-off q_D audit); runner `scripts/run_r23_next_mechanism_matrix_cloud_64env.sh`.
> Verdict pending a GPU launch of `EXP-20260707-r23-next-mechanism-matrix`.


Source of this section: the R23 320k seed1 read
(`EXP-20260706-r23-actionable-team-intent`, MIXED) + GPT post-read advice
(`memory/advice_gpt.md`), cross-validated in `cross_validation.md`
("2026-07-06 GPT R23-result advice"), disposition ACCEPTED-WITH-MODIFICATIONS.
This is a proposal ledger — nothing here is launched; the new modules need user
authorization + an Executor pass.

Result recap: R23-0 PASS (Z→ξ capacity real, forced-Z KL 0.04–0.08); R23-1
FAIL/null (g-info loss ~-2e-4, MI flat, objective-ON MI < objective-OFF);
R23-2 FAIL (team-disc at chance throughout). Blocker moved from `Z→ξ` (fixed) to
`ξ→recoverable joint effect` (open). g-info behaves as a smooth usage regularizer,
not a force that makes ξ a recoverable code.

Accepted next sequence (in order; do NOT sweep g-info coef, do NOT enable q_D
reward, do NOT run 960k, do NOT open new target-kappa/hazard/DADS branches):

```text
(a) Decision curves — DONE from train_updates.csv (10-pt/arm). Confirmed:
    architecture KL stable from update 1; g-info MI/loss flat; team_disc at
    chance throughout (never briefly-above). Finer tfevents pull optional.
(b) g-info GRADIENT AUDIT (Executor, small backward, no long run). Log:
    grad_norm to {Z-embedding, skill head, duration head, edit head, shared high
    encoder}, ratio_g_info_grad_to_ppo_grad, ratio_g_info_loss_to_policy_loss.
    Branch: grad≈0 → wiring/detach/enumeration bug (fix, don't sweep);
            grad≪PPO → scale issue (record); grad OK but MI won't move → the MI
            form is unsuitable → go to (c).
(c) PR-1 Option-B q_A residual (NEW module, algorithm change, authorization
    required). R_A = log q_A_full(Z|ξ,c,ω) − log q_A_prior(Z|c,ω), instantiating
    the R22 load-bearing I(Z;ξ|c,ω). ξ first version = executed skill ids z_1:n,
    duration/remaining bucket, edit mask, optional soft skill probs, roster/agent
    mask summary. Phase-1 reward-off probe (q_A_full_acc, q_A_prior_acc,
    q_A_residual_gain, best_shortcut_name); Phase-2 small-coef HIGH-LEVEL-only
    reward (coef 0.02/0.05, warmup 20k, clip 1.0, prior-corrected, q_D still off).
    MUST include an I(Z;ξ|c,ω) double-count audit vs the existing g-info term
    (don't silently stack two actionability objectives). Default-off; low-level
    actor input unchanged; no comm fields.
(d) q_D EFFECT-TARGET / TIMESCALE audit, reward-off (NEW targets = algorithm
    change, authorization required). Compare q_D(Z|·) residual signal over targets
    {s_next, joint_action_summary_H, joint_effect_window_H, Δω/Δc compact_H} and
    H∈{10,20,50}. Pick the target with real residual BEFORE any reward. Motivated
    by R23-2 reasons A (ξ differs at logits but executed assignments unstable),
    B (executed ξ doesn't move low-level behavior → discoverer/z_i capacity),
    C (q_D target too weak / single-step for the two-clock horizon). OPT grounding:
    if s_next can't read Z but Δω can, move the disc effect space from raw state to
    interaction-process space.
(e) Small 320k MECHANISM matrix (Experiment Manager, on authorization), NOT 960k:
    Arm0 arch-only (known-pass control) / Arm1 q_A probe reward-off /
    Arm2 q_A reward coef 0.02–0.05 / Arm3 q_D target audit (best of Arm1/2, q_D
    reward off). q_D reward-on is allowed ONLY after Arm3 shows non-chance residual.
```

Principle status: no principle rewrite from a single 320k seed (GPT concurs);
this stays an interim experiment result until (b)–(e) read. The R22 claim that
`I(Z;ξ|c,ω)` is load-bearing and `q_D` is an amplifier-not-starter is reinforced,
not changed.
