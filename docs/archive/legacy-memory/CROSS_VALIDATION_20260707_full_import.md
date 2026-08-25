# Cross-Validation Log — HA-CTSE / HMASD / OPT Review

Canonical file: `memory/cross_validation.md`

Legacy redirect: `memory/advice_cc.md`

This file is the standing cross-validation and decision-dialogue ledger for
Claude, GPT, Codex, the user, and other external reviewers. It records outside
advice, detailed project responses, accepted/rejected plan changes, and the
metadata for modifications that affect principles, implementation plans, code,
scripts, packaging, experiments, or result interpretation.

External Reviewer Quick-Review Standard:

```text
1. Start from the latest "Cross-validation handoff index" round.  As of
   2026-07-03 this is Round 13.
2. Use that round's memory reading order, reference-paper index, code/experiment
   state, and reviewer questions as the required review entry point.
3. Cite indexed memory/design/code files concretely.
4. State whether each recommendation is accepted, modified, rejected, or
   deferred, with evidence and affected files.
5. Avoid treating diagnostic communication metrics as intrinsic objectives.
6. Preserve the current benchmark hierarchy: S7-S1 parity first; S7-S3 later.
7. If a new outside review changes the active problem, add a new Round N
   handoff index or explicitly amend the latest handoff before acting on the
   advice. Do not leave external advice as unanchored chat text.
```

Required metadata for every new review/advice entry:

```text
Source:
  reviewer/model:
  role: architect | reviewer | executor | experiment-manager | packager | mixed
  input artifacts:
  scope: principles | implementation | experiment | result-interpretation | packaging | workflow
  disposition: accepted | modified | rejected | deferred | superseded
  affected files:
```

Required metadata for every accepted modification:

```text
Modification:
  changed_at:
  actor/model:
  active role:
  authority source:
  reason:
  affected files:
  linked plan section:
  linked experiment:
  validation performed:
  follow-up owner:
  status: proposed | accepted | implemented | validated | superseded
```

Use this file for detailed dialogue history and rationale. Use
`ATTENTION_POINTER.md` only for fast routing, `IMPLEMENTATION_PLAN.md` for the
active task ledger, and `ExpRecord.md` for experiment state.

Original created: 2026-06-28
Original reviewer: Claude (Cowork)
Original source: read-only review of `memory/ALGORITHM_KNOWLEDGE_BASE.md`,
`memory/ALGORITHM_PRINCIPLES.md`, `memory/IMPLEMENTATION_PLAN.md`,
`memory/IC_SPL_HAZARD_SMDP_ALTERNATIVE.md`, `memory/antigravity__CO46.md`.

---

## 2026-07-06 GPT R23-result advice (post-320k read) — CC cross-validation

Source:
```text
reviewer/model: GPT (memory/advice_gpt.md, updated after the R23 320k seed1 read) —
  "R23 is real progress, not success" verdict + a 9-section forward plan
  (curves → gradient audit → Option-B q_A → q_D target/timescale audit → small
  320k mechanism matrix, with a stop list).
role: reviewer/architect (forward design + diagnostic prescription)
CC role: Reviewer (routing advice into the ledger). NOT Executor here: no code
  written, no run launched. Option-B q_A and new q_D targets are algorithm
  changes that require explicit user authorization + an Executor pass.
input artifacts: dist\logs_cloud_r23_actionable_team_intent_64env (my read),
  ExpRecord EXP-20260706-r23-actionable-team-intent, R23_ACTIONABLE_TEAM_INTENT.md,
  R22_TWO_CLOCK_ELBO.md, R21_AUTOPSY_REPORT.md
scope: interpretation-agreement + next-experiment design
disposition: ACCEPTED-WITH-MODIFICATIONS (sequencing + authority scoping)
```

CC verdict: ACCEPT. GPT's reading matches my log analysis exactly — R23-0
architecture PASS (forced-Z KL 0.04–0.08 ≈ 20–50× the R21 ~0.002 band, stable
from update 1), R23-1 g-info FAIL/null (loss ~-2e-4, MI flat, objective-ON MI
0.012 < objective-OFF 0.024), R23-2 disc at chance throughout (0.14–0.25 vs 1/6,
prior entropy pinned ln6). The blocker has moved from `Z→ξ` (fixed) to
`ξ→recoverable joint effect` (open). GPT's three confirmation questions answered
from the CSVs: (A) architecture KL exists + stable early = YES; (B) g-info flat =
YES; (C) disc at chance throughout, never briefly-above = YES.

Per-recommendation disposition:
```text
1. Draw only 6 decision curves (forced_Z_KL/z_itv, g_info MI/loss, team_disc_acc,
   team_disc_residual/prior_entropy, task cov/zero_thr): ACCEPT. Already answered
   A/B/C above from train_updates.csv. CAVEAT to feed back: the CSV has only 10
   update rows/arm (plot_interval=10 → one row per 32k steps), so fine-grained
   "stabilizes when / briefly-above-chance" shape is coarse; the tfevents files
   may hold finer series, but the flat verdict already holds at 10-point res.
2. g-info GRADIENT AUDIT before any coef sweep (grad norms to Z-embedding /
   skill / duration / edit heads / shared high encoder; ratio to PPO grad; ratio
   loss-to-policy-loss): ACCEPT — this is the decisive next diagnostic. Small
   backward pass, NO long run. Executor task. Decision tree (grad≈0 → wiring bug,
   fix don't sweep; grad≪PPO → scale; grad OK but MI won't move → switch to
   Option-B) accepted verbatim.
3. Stop treating g-info as the primary actionability objective (it is a smooth
   usage regularizer, doesn't force ξ into recoverable codes): ACCEPT AS
   HYPOTHESIS, conditional on the gradient audit outcome (branch 3 above). Do not
   pre-judge before the audit.
4. Option-B q_A residual as the next main objective — q_A_full(Z|ξ,c,ω) vs
   q_A_prior(Z|c,ω), R_A = log q_A_full − log q_A_prior; Phase-1 reward-off probe
   (q_A_full_acc, prior_acc, residual_gain, shortcut name) then Phase-2 small-coef
   HIGH-LEVEL-only reward (coef 0.02/0.05, warmup 20k, clip 1.0, prior-corrected,
   q_D still off): ACCEPT AS THE FORWARD DESIGN CANDIDATE. MODIFICATIONS: (a) it
   is a NEW module = algorithm change → needs user authorization + Executor, not a
   Reviewer build; (b) must land in PR-1 with an I(Z;ξ|c,ω) double-count audit
   against the existing g-info term (don't stack two actionability terms silently);
   (c) default-off, high-level only, no low-level actor input change, no comm fields
   — same guardrails as every prior mechanism.
5. Don't tune q_D coef; audit q_D EFFECT TARGET/TIMESCALE reward-off — compare
   q_D(Z|s_next) vs q_D(Z|joint_action_summary_H) vs q_D(Z|joint_effect_window_H)
   vs q_D(Z|Δω/Δc compact_H) over H∈{10,20,50}, check which target carries residual
   signal before any reward: ACCEPT. Reasons A/B/C (ξ logits-only-not-executed /
   z_i→low-level unchanged / q_D target too weak or single-step) are the correct
   decomposition of the R23-2 chance reading. The Δω / interaction-process effect
   space is well-grounded in OPT (ω = prototype aggregation weights). This is also
   a new-target algorithm change → authorization + Executor.
6. Next round = small 320k MECHANISM matrix (Arm0 arch-only control / Arm1 q_A
   probe reward-off / Arm2 q_A reward / Arm3 q_D target audit), NOT 960k parity;
   q_D reward-on only after Arm3 shows non-chance residual: ACCEPT. Consistent with
   "q_D is an amplifier, not a starter."
7. Stop list (no g-info coef sweep 0.02→0.1/0.2; no q_D reward-on now; no R23
   960k; no new target-kappa/hazard/R12-DADS branch; no coverage/backhaul/recovery
   as intrinsic): ACCEPT — already consistent with the R23 note §9 and the
   principle that comm metrics are S7-S1 diagnostics, not intrinsic rewards.
8. Record an R23 interim result in ExpRecord, no major principle rewrite: ACCEPT
   — already done (EXP-20260706-r23-actionable-team-intent Result block + dashboard
   row + ATTENTION_POINTER R23 bullet). GPT half-agrees with my "single 320k seed
   isn't enough to rewrite the contract"; kept as interim, not a principle edit.
```

Net sequencing (accepted order, none launched — all pending user authorization):
```text
(a) curves: DONE from CSV (A/B/C answered); optional finer tfevents pull if wanted.
(b) g-info gradient audit  [Executor, small backward, no run]  <-- decides (c) vs g-info-salvage
(c) PR-1: Option-B q_A residual design + I(Z;ξ|c,ω) double-count audit  [Architect→Executor]
(d) q_D target/timescale audit, reward-off  [Executor]
(e) small 320k mechanism matrix Arm0..3  [Experiment Manager, on authorization]
q_D reward-on only after (d) shows non-chance residual.
```

Modification:
```text
changed_at: 2026-07-06
actor/model: Claude (CC)
active role: Reviewer (cross-validation routing)
authority source: user "advice from gpt has been updated. check memory/advice_gpt.md"
reason: route the post-R23-read GPT forward plan into the ledger with dispositions;
  keep it a proposal (no code, no run) pending user authorization for the new modules.
affected files: memory/cross_validation.md, memory/R23_ACTIONABLE_TEAM_INTENT.md
  (§11 forward-plan addendum), memory/ATTENTION_POINTER.md (next-actions)
linked plan section: R23 design note; R22 two-clock ELBO (I(Z;ξ|c,ω))
linked experiment: EXP-20260706-r23-actionable-team-intent (completed, MIXED)
validation performed: cross-checked every GPT claim against the 320k CSVs; no code
  changed; no run launched.
follow-up owner: user (authorize gradient audit + Option-B/q_D-audit implementation);
  then Executor (Codex/CC) for the small backward audit and the new modules.
status: accepted-with-modifications (proposal recorded; awaiting authorization)
```

### 2026-07-06 EXECUTION (CC Executor, user authorized "do all the jobs now")

User authorized full implementation. CC executed the accepted plan
(`docs/superpowers/plans/2026-07-06-r23-next-actionability.md`, T1–T5), TDD, in the
SB3 conda env (gymnasium 1.0.0 / pettingzoo 1.24.3 — the project pins). Nothing
committed (project norm: user decides `git add`).

```text
T1 curves (scripts/plot_r23_decision_curves.py): confirmed GPT A/B/C from the CSVs —
  forced-Z KL flat+elevated (0.08/0.04/0.077), g-info MI flat, team_disc_acc straddles
  chance (range ~0.14–0.25 around 1/6). Figure: dist/r23_extract/.../r23_decision_curves.png.
T2 g-info GRADIENT AUDIT (scripts/r23_ginfo_grad_audit.py) — DECISIVE, NOT a wiring bug:
  random-init: grad(g-info)->code_embedding 2.1e-4, ->W_Z 2.9e-3, ->skill_head 8.8e-4,
    ->trunk 1.5e-3; ratios to a PPO-ref grad on the same batch = 0.6–1.0% (<<1%).
  r23_1_action final ckpt: same picture (ratios 0.2–1.4%), MI still ~0.012.
  VERDICT: SCALE/FORM — g-info backprops but is <2% of PPO and self-stalling (normalized
  MI is near-second-order; grad vanishes at low MI so it cannot bootstrap). Confirms GPT:
  not salvageable by a coef sweep -> switch main line to q_A (cross-entropy = first-order).
T3 q_A residual actionability (ha_ctse_process/assignment_actionability.py + wiring):
  AssignmentActionabilityDiscriminator q_A_full(Z|xi,c,omega) vs q_A_prior(Z|c,omega),
  residual=log q_full-log q_prior; detached inputs, own Adam opt, high-level only. Wired
  into update_high_from_segments: builds executed-xi features (skill/duration one-hot + age
  + optional soft probs) + context (compact, omega), trains reward-off, and folds a
  clipped reward into high returns ONLY when reward_on + warmup + residual_gain>0. Default-off
  (probe/reward flags). CLI in train.py, config flags, 12 UPDATE_FIELDS. Tests 7/7 (held-out
  train/eval split so a noise prior can't overfit). Probe smoke: q_a cols land, active, reward
  off. Reward smoke: gate holds, no crash.
T4 q_D effect-target/timescale audit (ha_ctse_process/team_effect_targets.py + wiring):
  reward-off TeamEffectTargetProbe comparing q_D(Z|.) over {s_next, joint_action, joint_effect,
  delta_omega} x H{10,20,50}. Per-target online head + context-free prior baseline; per-target
  labels (targets have different sample counts); double-count safe (q_D never reads xi — only
  future state/action/effect/omega). Wired into process_update via _team_effect_target_audit
  (window buffering by grouping rollout indices per env; delta_omega recomputes OPT omega,
  guarded). Tests 5/5. Integration smoke: all 4 targets build + log, no crash.
T5 runners: scripts/run_r23_next_mechanism_matrix_cloud_64env.sh (+ local .ps1 mirror),
  arms arm0_arch_only / arm1_qA_probe / arm2_qA_reward / arm3_qD_audit, 320k, Choice-1 K=8
  durations 1,2,3,4, q_D reward OFF everywhere. Both dry-run validated.
Regression: full tests/ = 245 passed, 4 failed; ALL 4 failures verified PRE-EXISTING at HEAD
  via stash (r14 prototype broadcast, two ha_ctse_process_standalone mock-harness tests, one
  r12 hazard mock-signature) — zero new failures from this work.
```

Modification:
```text
changed_at: 2026-07-06
actor/model: Claude (CC)
active role: Executor (user: "you have my authorization and you have to do all the jobs now")
authority source: explicit user authorization this turn
reason: implement the accepted R23-next plan (g-info audit + q_A residual actionability +
  q_D target/timescale audit + mechanism-matrix runners), default-off, TDD.
affected files: docs/superpowers/plans/2026-07-06-r23-next-actionability.md (new),
  scripts/plot_r23_decision_curves.py (new), scripts/r23_ginfo_grad_audit.py (new),
  ha_ctse_process/assignment_actionability.py (new), ha_ctse_process/team_effect_targets.py (new),
  tests/r23_assignment_actionability_test.py (new), tests/r23_team_effect_target_test.py (new),
  scripts/run_r23_next_mechanism_matrix_cloud_64env.sh (new), ...local_cuda.ps1 (new),
  ha_ctse_process/config.py, ha_ctse_process/standalone_agent.py, ha_ctse_process/train.py,
  ha_ctse_process/plotting.py, memory/{ExpRecord,ATTENTION_POINTER,R23_ACTIONABLE_TEAM_INTENT,cross_validation}.md
linked plan: docs/superpowers/plans/2026-07-06-r23-next-actionability.md; R23 note section 11
linked experiment: EXP-20260706-r23-actionable-team-intent (read) → next: EXP-20260707-r23-next-mechanism-matrix (launch-ready)
validation performed: TDD RED→GREEN; module tests 7 (q_A) + 5 (q_D) pass; 31/31 R23/R21/R19 regression;
  full tests/ 245 passed with 4 pre-existing failures (stash-confirmed unrelated); py_compile OK;
  probe/reward/audit integration smokes exit 0 with fields logged; both runners dry-run validated.
  T2 gradient-audit result recorded (SCALE/FORM). No training run launched. Nothing committed.
follow-up owner: user (launch the 320k mechanism matrix on GPU; decide git commit)
status: IMPLEMENTED (default-off); mechanism-matrix verdict pending a GPU run

POST-LAUNCH FIX (2026-07-06, CC Executor): while the local 32-env matrix was running
(user launched `run_r23_next_mechanism_matrix_local_cuda.ps1 -NumEnvs 32`), a CUDA-only
bug was caught by review before arm3 reached it: `TeamEffectTargetProbe` created its Adam
optimizer inside `__init__`, but the agent calls `.to(device)` after construction, so the
optimizer bound to pre-move CPU params (fine on the CPU smokes, broken on CUDA). Fixed to
lazy-create the optimizer on first `update()` (after `.to(device)`). Each arm is a fresh
`python -m ha_ctse_process.train` process, so arm3 (last arm) picks up the fix at its launch;
arm0/arm1/arm2 do not use the probe and q_A's optimizer was already created after `.to(device)`.
Verified: py_compile OK, T4 tests 5/5. `ha_ctse_process/team_effect_targets.py` only.
```

---

## 2026-07-06 GPT R23 design advice + CC Executor implementation

Source:
```text
reviewer/model: GPT (memory/advice_gpt.md, updated 2026-07-06 16:24) — full R23
  "Actionable Team Intent" design + "Next Design Prompt for Claude" (6 tasks)
role: reviewer/architect (design); CC then acted as Architect + EXECUTOR (user
  expanded CC role: "you need to be the code editor ... not just architect but an executor")
input artifacts: R21_AUTOPSY_REPORT.md, R22_TWO_CLOCK_ELBO.md, advice_gpt.md
scope: forward-design + implementation
disposition: accepted; design authored + first architecture increment IMPLEMENTED
affected files: memory/R23_ACTIONABLE_TEAM_INTENT.md (new design note),
  scripts/r23_capacity_gate.py (new diagnostic), ha_ctse_process/config.py,
  ha_ctse_process/standalone_agent.py, ha_ctse_process/train.py,
  tests/r23_actionable_team_intent_test.py (new), + memory sync files
```

CC verdict (R-1..R-8): ACCEPT. GPT's R23 design is the correct actionability-first
inversion and is directly grounded in my autopsy. Confidence high on the
architecture-gate diagnosis (my own measurement); the objective forms remain bets
to be read at R23-1+. HMASD baseline dropped as blocking per user (not GPT).

Work done (user authorized code editing):
```text
1. Wrote the R23 design note (PR-1 PGM/ELBO terms, R23-0 gate, arch menu,
   actionability objective A/B, q_D gate, individual q_d, Choice-1 timing, staged
   matrix R23-0..4, guardrails).
2. Built scripts/r23_capacity_gate.py (diagnostic-only). R23-0 read on current arch:
   FAIL (skill KL ~0.002 at random-init AND final) => architecture, not just objective.
3. IMPLEMENTED §3 architecture correction (Option C) default-off via TDD:
   config.z_assignment_residual_gain=0.0; SkillDurationPolicy residual logit path
   (skill+duration); agent wiring; --z_assignment_residual_gain CLI. Low-level actor
   left blind to Z/c; S-base selection path untouched (no policy-path confound).
   RED->GREEN: tests/r23_actionable_team_intent_test.py 3/3; r21_team_intent 7/7;
   capacity gate flag-on random-init PASS (skill KL 0.12), flag-off S-base identical.
   3 pre-existing unrelated test failures verified present at HEAD (stash check).
```

R23-1 (added same day): implemented via DRY reuse — Option A already exists as
`GInfoObjective` (Round-10 g-info), which failed then only because Z was decorative
(the defect R23-0 fixes). No new module. Tests prove actionability is live with the
residual (`g_info_skill_mi>0.02`, loss<0) and decorative without (`<0.005`,
reproducing the Round-10 failure); 128-step smoke ran clean (skill MI≈0.023,
forced-Z KL≈0.099, negative loss, no guard kills). Recipe in R23 note §4.

R23-2/R23-3 (added same day, user directed "implement R23-2 and R23-3, and write
the scripts"): R23-2 (q_D probe) needs no new code (existing `--enable_team_disc_probe`
on top of R23-1). R23-3 (q_D reward) got a new HARD actionability gate:
`team_disc_actionability_floor` (default 0.0 = no gate, R21-compatible);
`_team_disc_actionability_gate_open()` allows the reward only when the last measured
forced-Z skill KL (`g_itv_kl_skill`, cached by the high update) ≥ floor, else
`team_disc_reward=0` with `team_disc_reward_gated_off`/`team_disc_forced_z_kl` logged.
TDD RED→GREEN; 13/13 R23+R21 tests pass. Smoke: reward gated OFF at update 1 (KL 0),
applied at update 2 (KL 0.059 ≥ 0.05), then the pre-existing reward-ratio guard killed
the degenerate tiny-smoke ratio (expected — the gate and the ratio guard compose).
Runners written + dry-run validated: `scripts/run_r23_actionable_team_intent_cloud_64env.sh`
(primary, Linux/CUDA/64env) and `..._local_cuda.ps1` (mirror), arms
r23_arch_only / r23_1_action / r23_3_reward, Choice-1 K=8 / durations 1,2,3,4.

Not done (needs GPU + user run): the overnight VERDICT reads for R23-1/R23-3 (does
forced-Z KL/MI rise under training + task health hold; does the gated q_D reward help
once actionability passes?). gain=1.0 is a capacity demo; runners use 0.5. All R23
mechanisms default-off. Nothing committed.

Modification:
```text
changed_at: 2026-07-06
actor/model: Claude (CC)
active role: Architect + Executor (user-expanded: code editor)
authority source: user "do the job" + "you need to be the code editor ... an executor"
reason: implement R23 actionability-first architecture correction (default-off) and
  operationalize the R23-0 capacity gate
affected files: memory/R23_ACTIONABLE_TEAM_INTENT.md, scripts/r23_capacity_gate.py,
  ha_ctse_process/config.py, ha_ctse_process/standalone_agent.py, ha_ctse_process/train.py,
  tests/r23_actionable_team_intent_test.py, memory/ExpRecord.md, memory/ATTENTION_POINTER.md,
  memory/ALGORITHM_PRINCIPLES.md, memory/cross_validation.md
linked plan section: R23 design note; R22 two-clock ELBO
linked experiment: EXP-20260706-r23-actionable-team-intent
validation performed: TDD (RED then GREEN); r23 3/3 + r21 7/7; py_compile OK;
  capacity gate flag-on PASS / flag-off S-base preserved; 3 pre-existing failures
  confirmed unrelated via stash-at-HEAD. No training run. Nothing committed.
follow-up owner: user (authorize R23-1 training) + Executor (implement objective)
status: implemented (architecture increment); design accepted
```

---

## 2026-07-06 GPT post-autopsy advice — CC cross-validation

Source:
```text
reviewer/model: GPT (external, memory/advice_gpt.md, updated 2026-07-06 15:59)
role: reviewer (accepts autopsy; proposes principle updates, R23 design, gitignore fix)
input artifacts: memory/R21_AUTOPSY_REPORT.md (my autopsy); prior GPT advice entry below
scope: result-interpretation + principles + workflow(git) + forward-design
disposition: accepted-with-modifications
affected files: memory/ALGORITHM_PRINCIPLES.md, memory/R22_TWO_CLOCK_ELBO.md,
  memory/ATTENTION_POINTER.md, .gitignore, memory/cross_validation.md
```

CC reviewer verdict (R-1..R-8):

VERDICT (R-1): ACCEPT. This round is mostly confirmatory of my autopsy and adds
two genuinely sharp points I endorse. High confidence on the diagnosis (it is my
own autopsy). The forward R23 design is a well-formed bet (evidence class c/d),
not a result. Two NEW substantive additions beyond my autopsy, both accepted:
```text
(A) ARCHITECTURE CAPACITY GATE: because random-init forced-Z KL≈0.002 is ALSO
    weak, the Z->assignment architectural gain (not just the objective) is too
    weak. R23 step 1 is a STATIC test that a re-architected Z (AR first token /
    Z-FiLM on heads) gives random-init forced-Z KL clearly above decorative,
    BEFORE adding any loss. This is the correct reading of my own random-init
    number and I had under-drawn it as an architecture prescription.
(B) CREDIT-TENSION TRIANGLE made empirical: K_team << episode conflicts with
    protecting long lifetimes (K>=2*max_dur is ~impossible at 50 checks / dur24).
    => R23 uses short duration candidates + K≈8-12 (Choice 1) before truly
    decoupled parent-child lifetimes (Choice 2). Accept Choice-1-first.
```

EVIDENCE (R-2): FOR — (b) my measured autopsy underpins the diagnosis and the
architecture-gate point. AGAINST/caveats — the R23 objective form
`log q(Z|xi,c,ω) - log q(Z|c,ω)` and the actionability floor value are (c)/(d);
the "decorative band" threshold for the capacity gate is not yet numerically
defined; and Choice 1 (short durations) tests ACTIONABILITY, not the
decoupled-lifetime contribution — do not later conflate a short-duration parity
read with the async-lifetime thesis.

SOBERING NUMBER (R-3): unchanged and still governing — cov_eq1_step_frac = 0.0
(R21) / ~0.016 (S-base), and HMASD-on-CURRENT-env parity is STILL unverified. No
amount of R23 team-intent design substitutes for that premise check.

UNVERIFIED PREMISES (R-4): P1 (HMASD current-env baseline) remains top and is GPT
Priority C — still not run; owner Experiment Manager/user (GPU). P4 (an I(Z;xi)
term yields task-useful behavior) is still a bet the ELBO + a probe must support.
NEW: P5 = "a re-architected Z can lift random-init forced-Z KL above decorative"
— cheap static test, owner Architect, gates the whole R23 build.

DISSOCIATION / FALSIFICATION (R-5,R-6): the static capacity gate is itself a clean
falsifier: if a re-architected Z still shows random-init forced-Z KL ≈0.002, the
routing is structurally too weak and no objective term will save it. Earliest
metric for R23: random-init forced-Z assignment KL, then trained forced-Z KL,
BEFORE any q_D reward.

OPPORTUNITY COST (R-7): Priority A (principle lock-in) + gitignore fix = zero
compute, done now. Priority B (ELBO) = zero compute, next (Architect). Priority C
(HMASD baseline) = the one GPU item and the highest-value premise. R23 build
deferred until ELBO + capacity gate. Ordering endorsed.

Per-recommendation disposition:
```text
1. Stop all R21/R19/g/target-kappa/hazard sweeps -> ACCEPTED (already recorded).
2. Classify R21 true-objective-failure, not label-bug, not primarily churn,
   K≈episode confound -> ACCEPTED (matches my autopsy; recorded in principles).
3. Update principles: demote v6 sampled-Z to negative evidence; q_D gated behind
   forced-Z-KL floor; I(Z;xi) required; K≈episode invalid -> ACCEPTED. Applied as
   the autopsy-confirmed amendment in ALGORITHM_PRINCIPLES.
4. Fix memory git-tracking via .gitignore negations -> ACCEPTED-MODIFIED. Applied a
   surgical version: `!memory/*.md` + `!docs/superpowers/plans/*.md` only (tracks 19
   canonical memory files + 13 plans; backup_20260706/ stays ignored). Did NOT add
   GPT's broader `!memory/` / `!docs/**` globs (would sweep scratch). NOT committed.
5. R22 ELBO actionability-first with explicit xi; entropy as derived-vs-stabilizer;
   decide q_D composition and double-count -> ACCEPTED as direction; extended the
   R22 note. Theory only, no code (Architect owns; no implementation yet).
6. Static Z-architecture capacity gate before R23; keep low actor blind to Z/c;
   don't change S-base selection path -> ACCEPTED (new premise P5).
7. HMASD current-env S7-S1 (+S7-S3) baseline in parallel -> ACCEPTED and ELEVATED;
   GPU item, NOT launched by CC. Owner: user/Codex.
8. Don't implement SAC target-entropy yet; first write which entropies are derived
   -> ACCEPTED (deferred implementation).
9. Name next version R23 / A-TI -> DEFERRED (cosmetic; defer until ELBO + gate).
10. GPT's Codex instruction block (sec 10) -> NOTED; principle/memory items done by
    CC; the ELBO derivation + R23 design are Architect tasks pending user go-ahead.
    CC did not write training code or launch runs.
```

Delta vs the prior GPT entry: GPT now RETRACTS its earlier "atomic reassignment =
harmful churn" cause (my Audit C) and its "objective trained Z out" framing (my
Audit A) — both corrected to my autopsy read. Consistent.

Modification:
```text
changed_at: 2026-07-06
actor/model: Claude (CC)
active role: Reviewer (cross-validation) + minimal workflow edit (.gitignore)
authority source: user "advice from gpt has been updated" + my prior offer to fix
  memory git-tracking + autopsy evidence
reason: route GPT post-autopsy advice; lock R21 negative into principles; make
  canonical memory git-trackable; queue R22 ELBO + R23 capacity gate (proposals)
affected files: memory/ALGORITHM_PRINCIPLES.md, memory/R22_TWO_CLOCK_ELBO.md,
  memory/ATTENTION_POINTER.md, .gitignore, memory/cross_validation.md
linked plan section: Active R22 Contract; R22 two-clock ELBO (PR-1)
linked experiment: EXP-20260705-r21-team-intent (autopsied);
  EXP-20260705-hmasd-currentenv-baseline (blocking premise P1)
validation performed: .gitignore negation verified surgical (git status/check-ignore);
  no code/run; not committed.
follow-up owner: Architect (PR-1 ELBO + R23 static capacity gate design) + user
  (authorize; launch HMASD baseline; decide whether to commit newly-trackable memory)
status: accepted
```

---

## 2026-07-06 R21 autopsy (read-only) — CC Executor

Source:
```text
reviewer/model: Claude (CC)
role: Executor (user-authorized diagnostic scripts; read-only autopsy)
input artifacts: R21 seed-1 logs + checkpoints (dist/logs_cloud_r21_team_intent_64env);
  frozen source (team_intent.py, standalone_agent.py, train.py, tests/r21_team_intent_test.py);
  GPT advice (advice_gpt.md); plan docs/superpowers/plans/2026-07-06-r21-autopsy.md
scope: result-interpretation (mechanism forensics)
disposition: accepted (findings recorded; no code/principle change beyond memory)
affected files: memory/R21_AUTOPSY_REPORT.md, memory/ExpRecord.md,
  memory/ATTENTION_POINTER.md, memory/R22_TWO_CLOCK_ELBO.md, memory/cross_validation.md
```

Result: R21 classified **true-objective-failure** (primary). Audit B: team-disc
data contract correct (lockstep label/state alignment train.py:3016-3028; no
leakage; prior/reward timing correct) and metric-path held-out control reproduces
chance on no-signal data → `team_disc_acc`≈chance is genuine, NOT a bug
(`aligned-real`). Audit A: forced-Z assignment KL ≈0.00165 (random-init) vs
≈0.00223 (final) → Z near-inert and never made actionable; **refutes GPT's
sub-hypothesis that the objective "trained Z out"** (random-init ≈ final). Audit C:
`truncation-contaminated` — `z_boundary_trunc_rate_durX` sampled only at the single
terminal Z boundary (team_intent_remaining=480 vs episode=500), long-duration
buckets ≈1.0 near-tautologically; duration reads invalid; `team_intent_k=48 ≈
episode=50` intervals collapsed the two-clock to one Z/episode; churn is NOT the
regression cause (probe arm regressed too → policy-path effect).

Disposition vs the GPT advice entry below: Audit A/B/C **executed and accepted**;
GPT item (4) "atomic reassignment = harmful churn" is now **rejected as the primary
regression cause** (Audit C evidence). GPT items 5-7 (PR-1 ELBO with `I(Z;ξ)`,
gate team-disc behind actionability) are **strengthened** by Audit A/B. New finding
not in GPT advice: the `K≈episode` confound must be fixed before any rerun.

Modification:
```text
changed_at: 2026-07-06
actor/model: Claude (CC)
active role: Executor (read-only diagnostics, user-authorized)
authority source: user directive "read-only R21 autopsy + report"
reason: locate the R21 sampled-Z failure on the Z->assignment->discriminator chain
affected files: memory/R21_AUTOPSY_REPORT.md (new), memory/ExpRecord.md,
  memory/ATTENTION_POINTER.md, memory/R22_TWO_CLOCK_ELBO.md, memory/cross_validation.md
linked plan section: docs/superpowers/plans/2026-07-06-r21-autopsy.md; R22 two-clock ELBO
linked experiment: EXP-20260705-r21-team-intent
validation performed: audit_b_control2.py (held-out control), audit_a_forced_z.py
  (forced-Z sweep, CPU) executed successfully; static code trace for Audit B/C.
  No algorithm code modified; no training run; no fix applied (no bug found).
follow-up owner: Architect (PR-1 ELBO with actionability term) + user (authorize)
status: accepted
```

---

## 2026-07-06 GPT review of R21 negative read (advice_gpt.md) — CC cross-validation

Source:
```text
reviewer/model: GPT (external, via memory/advice_gpt.md, updated 2026-07-06 13:00)
role: reviewer (proposes architect-level redesign + executor autopsy tasks)
input artifacts: my 2026-07-06 R21 seed-1 readout (ExpRecord EXP-20260705-r21-team-intent
  Result block); dist/logs_cloud_r21_team_intent_64env
scope: result-interpretation + principles + implementation + experiment
disposition: accepted-with-modifications (see per-item below)
affected files: memory/cross_validation.md (this entry), memory/ATTENTION_POINTER.md,
  memory/ALGORITHM_PRINCIPLES.md (labeled amendment to Active R22 Contract)
```

CC reviewer verdict (Research Insight Duties R-1..R-8 applied):

VERDICT (R-1 calibrated belief): ACCEPT the advice's core direction. High
confidence (~0.85) that R21's sampled Z is decorative because nothing downstream
conditions on it — `z_assignment_itv`≈0 and `team_disc_acc`≈chance are causally
linked (a Z that never changes assignment gives the discriminator nothing to
learn). LOWER confidence (~0.55) that GPT's proposed fix — an explicit
actionability term `I(Z ; xi | c, omega)` — is sufficient: actionability is
necessary but a Z can be made to change assignment `xi` and still be
task-useless. Would NOT bet the R23 objective form is final before the ELBO.

EVIDENCE (R-2):
```text
FOR (strongest): (b) internal measured — itv≈0.0016-0.0051 AND team_disc_acc≈0.17
  (random=1/6) across all 30 updates, in BOTH probe and reward-on arms. Two
  independent signals point at the same "Z has no assignment effect" cause.
FOR: (a) external — HMASD's ablations make Z load-bearing only because Z is the
  first AR token that individual skills explicitly condition on; R21 restored the
  sample but not that conditioning path.
AGAINST / caution: (d) taste — "atomic reassignment = harmful churn" is asserted
  as a cause of the task regression but is NOT isolated in the data; it is a
  hypothesis pending Audit C. And team_disc_acc≈chance could still be a
  label/leakage/pre-update-output bug rather than a true mechanism failure
  (exactly why GPT's Audit B matters). The "mechanism-negative" label is correct
  but should stay conditional on Audit B.
```

SOBERING NUMBER (R-3): `coverage_eq1_step_frac` = 0.0 for R21 and ~0.0164 for the
S-base it is measured against — an order of magnitude under the parity bar (half
of eval primitive steps at coverage==1.0). No team-intent variant has approached
parity, AND we still have not confirmed HMASD itself clears the bar on the
CURRENT env. Any "just add actionability to Z and we reach parity" optimism must
confront that we may be tuning a team channel on top of a base that is far from
the target for reasons unrelated to team intent.

UNVERIFIED PREMISES (R-4):
```text
P1 "HMASD works on the current S7-S1 6-agent env at ~1e6 steps" — load-bearing,
   cheap-ish (one baseline run, already packaged as EXP-20260705-hmasd-currentenv
   -baseline), STILL NOT RUN. This is the highest-value unverified premise and
   GPT correctly lists it as blocking. Owner: Experiment Manager (Codex/user).
P2 "team_disc_acc≈chance is a mechanism failure, not a wiring/label bug" —
   verify via Audit B (read-only). Owner: Executor (Codex).
P3 "atomic Z-boundary reassignment causes the task regression" — verify via
   Audit C truncation-cause audit. Owner: Executor.
P4 "an I(Z;xi) actionability term yields task-useful team behavior" — theory bet;
   only the ELBO derivation (PR-1) + a later probe can support it. Owner: Architect.
```

DISSOCIATION / FALSIFICATION (R-5, R-6): GPT's Audit A (forced-Z assignment KL on
a fixed batch) is a clean three-way dissociation and I endorse it as designed:
```text
trained-policy forced-Z KL ~0 AND random-init KL >0  -> objective trained Z out
random-init forced-Z KL ~0 already                   -> architecture never wired Z
trained-policy KL >0 but team_disc still chance      -> Audit B / discriminator bug
```
Earliest failure metric for the next team-intent design: forced-Z assignment KL.
If a redesign cannot move `xi` under forced Z on a fixed batch, stop before any
reward path — do not repeat R21's "sample-then-hope-q_D-rescues-it."

OPPORTUNITY COST (R-7): the autopsy (A/B/C) and PR-1 ELBO are read-only / zero-
compute and correctly displace new training. BUT the single most information-rich
action available now is arguably P1 (the HMASD current-env baseline) — it is a
training run, but it is the premise the entire S7-S1-parity program rests on and
it keeps being outranked by mechanism builds (this is the R-7 pattern AGENT_ROLES
warns about). I rank: {PR-1 ELBO, Audit A/B/C, HMASD baseline} together as the
now-tier; do NOT start an R23 build until the ELBO + autopsy are read.

SEAM VIGILANCE (R-8): GPT's Audit B is itself a seam check (does q_D input leak Z?
do labels align with executed held Z? does reward-on use pre-update q_D output?).
Endorsed — this is where a "mechanism-negative" claim could be a plumbing artifact.

Per-recommendation disposition:
```text
1. Stop R21; no seed 2; no K_team / team_disc_coef / num_team_codes sweep
   -> ACCEPTED. Already recorded (pre-registered stop rule). No action pending.
2. Classify R21 mechanism-negative
   -> ACCEPTED-MODIFIED. Keep negative, but conditional on Audit B ruling out a
      label/leakage bug. Recorded in ExpRecord.
3. Read-only Autopsy A (forced-Z actionability), B (disc data sanity),
   C (truncation cause)
   -> ACCEPTED as direction. Executor = Codex; CC does not run them. No new
      training. A is the load-bearing one.
4. "Atomic reassignment = harmful churn" as established cause
   -> MODIFIED to hypothesis pending Audit C.
5. PR-1: derive the two-clock ELBO for the actual model (c/omega -> Z -> xi ->
   z_i -> a -> O); decide whether team-disc / coordinator residual double-count
   and whether I(Z;xi|c,omega) is required
   -> ACCEPTED. Already the "next principles task"; advice promotes the
      cross-layer actionability term from "optional" to candidate-necessary.
6. Demote the v6 sampled-Z "commitment layer" mainline claim in principles
   -> ACCEPTED (data-driven). Labeled amendment added to Active R22 Contract.
7. Next design "actionability-first" (working names R23 / A-TI; I / target-
   situation must change xi before any discriminator reward)
   -> DEFERRED-MODIFIED. Accept the PRINCIPLE (actionability before identifiability)
      as the leading hypothesis; DEFER the naming and the specific reward form
      (R_intent_action / R_intent_effect / R_individual) until PR-1 + autopsy.
      Flag failure mode: an actionable-but-task-useless Z.
8. Replace duration/Z entropy floors with per-head target-entropy Lagrangian
   -> ACCEPTED as direction. Consistent with R22_TARGET_ENTROPY_DESIGN; not new.
9. HMASD current-env S7-S1 (and later S7-S3) re-verification is blocking
   -> ACCEPTED and ELEVATED (see R-3/R-4/R-7 above). Highest unverified premise.
10. Do NOT revert to pure recognition-first / R12 as mainline; keep OPT as
    substrate/control
   -> ACCEPTED. Matches existing memory (R12 substrate, R19 negative).
```

Boundary note: CC is Reviewer here and did not write training code or launch
runs. Autopsy A/B/C and PR-1 are Executor/Architect (Codex) tasks pending user
authorization. The forward "R23 actionability-first" objective is a PROPOSAL, not
an accepted contract, until PR-1 ELBO is derived and read.

Modification:
```text
changed_at: 2026-07-06
actor/model: Claude (CC)
active role: Reviewer (cross-validation)
authority source: user request to check advice_gpt.md + pre-registered R21 stop rule
reason: route external GPT R21 review into the ledger; demote v6 sampled-Z
  commitment claim on measured evidence; queue read-only autopsy + PR-1 ELBO
affected files: memory/cross_validation.md, memory/ATTENTION_POINTER.md,
  memory/ALGORITHM_PRINCIPLES.md
linked plan section: Active R22 Contract; R22 two-clock ELBO (PR-1)
linked experiment: EXP-20260705-r21-team-intent (completed negative);
  EXP-20260705-hmasd-currentenv-baseline (blocking premise P1)
validation performed: none (review + memory only; no code/run)
follow-up owner: Codex (autopsy A/B/C, PR-1 ELBO) + user (authorize + HMASD baseline)
status: accepted
```

---

## 2026-07-06 R21/R22 overnight cloud package

Modification:

```text
changed_at: 2026-07-06
actor/model: Codex
active role: Packager / Experiment Manager
authority source: user request to package overnight cloud experiments
reason: package launch-ready R21 team-intent and HMASD current-env baseline
affected files:
  dist/HA_CTSE_P0_MINIMAL_PACKAGE_FILES.md
  dist/HA_CTSE_R21_R22_OVERNIGHT_UPLOAD_README.md
  dist/ha_ctse_r21_r22_overnight_cloud_runtime_20260706_003500.zip
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
linked plan section: R22-2 keep experiment track running
linked experiment:
  EXP-20260705-r21-team-intent
  EXP-20260705-hmasd-currentenv-baseline
validation performed:
  bundle content check: required files present
  zip exclusion check: no __pycache__, .pyc, .pyo, .pt, .pth entries
  bash syntax check not run locally because bash is unavailable on Windows;
  server-side --dry-run is required before launch
follow-up owner: user/server operator
status: packaged
```

Notes:

```text
This is packaging-only.  No algorithm logic was changed.  The maintained dist
package manifest was amended to include the R21/R22 runners and root
`visualization.py`, which is required by the HMASD baseline path.  The runtime
zip intentionally excludes `memory/`; memory is local collaboration state and
should be shared separately only for review/context handoff.
```

---

## 2026-07-06 Claude review of R22/R21 implementation and Codex response

Source:

```text
reviewer/model: Claude, user-pasted external review
role: Reviewer
input artifacts:
  live repo diffs for R21/R22
  memory/R22_TWO_CLOCK_ELBO.md
  memory/R22_TARGET_ENTROPY_DESIGN.md
  R21 tests and runners
scope: implementation / experiment-readiness / result-interpretation
disposition: modified-accepted
affected files:
  ha_ctse_process/team_intent.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  train_multiproc_config_1.py
  tests/r21_team_intent_test.py
  docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md
  memory/ATTENTION_POINTER.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
```

Review summary:

```text
Claude approved R21/HMASD launch structure with no critical blockers, but
identified three interpretation risks:
1. R21 reward arm can stack prototype-disc and team-disc intrinsic rewards while
   existing guards check them independently.
2. Team-disc reward is paid on the primitive-step clock; R22 needs Z-clock
   diagnostics (`z_decisions_per_update`, `z_advantage_mean/std/var`) before the
   reward-on 320k gate is interpreted.
3. HMASD light metrics can omit per-step reward_info, making step-fraction parity
   metrics silently appear as 0.0.
```

Accepted response:

```text
Implemented R22-3 diagnostics and guard support:
- `z_decisions_per_update` aliases Z-boundary decisions.
- `z_advantage_mean/std/var` is computed from unnormalized high-level advantages
  only on Z-boundary samples with nonzero `team_logp_weight`.
- `combined_intrinsic_env_ratio` and cumulative guard counters sum active
  prototype-disc and team-disc reward/env ratios, counting only components with
  actual applied reward steps so reward-off discriminator previews cannot
  contaminate the guard.  The combined guard uses the same
  `reward_ratio_guard_mode` kill/warn semantics as the individual guards.
- Console, TensorBoard, CSV/plotting schema, and log-parser aliases now expose
  these fields.
- HMASD eval now falls back from missing per-step samples to episode-level parity
  metrics and logs `parity_step_metric_fallback_used` plus sample count.
- R22 plan, attention pointer, implementation plan, and ExpRecord were updated
  so future agents treat R22-3 as implemented rather than pending.
```

Validation status:

```text
Validated locally on 2026-07-06:
- `tests/r21_team_intent_test.py -q`: 7 passed.
- AST parse of changed Python files: ok for 6 files.
- `python -m ha_ctse_process.train --help`: imports and lists CLI successfully.
- `py_compile` was attempted but blocked by Windows permission on an existing
  `__pycache__` rename; replaced by read-only AST parse.

Launch interpretation rule: R21 reward-on 320k reads must include
`combined_intrinsic_env_ratio`, `z_decisions_per_update`, and `z_advantage_*`.
HMASD baseline first eval must report whether `parity_step_metric_fallback_used`
is 0 or 1.
```

---

## 2026-07-05 GPT-5.5 Pro R22 review: R21/v6 mainline and two-clock ELBO plan

Source:

```text
reviewer/model: GPT-5.5 Pro, advice provided by user attachment
role: Architect / Reviewer
input artifacts:
  user-provided review text dated 2026-07-05
  memory/ATTENTION_POINTER.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
  memory/cross_validation.md
scope: principles / implementation plan / experiment interpretation
disposition: modified-accepted
affected files:
  docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md
  memory/ALGORITHM_PRINCIPLES.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
```

Verdict:

```text
Accepted the core correction: the project had drifted too far toward the
R12 recognition-first / situation-response line.  The current mainline should
be the post-R21/v6 three-timescale hierarchy:

  OPT recognition substrate -> sampled slow team intent Z -> asynchronous
  individual response skills z_i.

R12 is retained as recognition substrate and control, not as the primary
cooperation engine.  R19 remains a mechanism-negative control unless later
complete reward-on logs contradict the current negative team-transition read.
The next highest-value work is not another reward module; it is a two-clock
ELBO/objective derivation that decides how team discriminator, individual
residual, entropy, and any cross-layer term compose.
```

Modification:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Architect / Planner
authority source: user request to write a plan from GPT-5.5 advice
reason: prevent long-task drift by making R21/v6 the explicit mainline and
  moving objective unification ahead of new reward design.
affected files:
  docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md
  memory/ALGORITHM_PRINCIPLES.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
linked plan section:
  docs/superpowers/plans/2026-07-05-r22-two-clock-elbo-mainline.md
linked experiment:
  EXP-20260705-r21-team-intent
  EXP-20260705-hmasd-currentenv-baseline
validation performed:
  plan written; memory pointers updated; no code changes in this step
follow-up owner:
  Architect for R22 derivation; Executor only after the plan's diagnostic
  audit identifies missing metrics.
status: accepted / planned
```

Accepted plan consequences:

```text
1. R21/v6 is the active algorithmic mainline, not R12/R19.
2. R21 and HMASD baseline experiments remain launch-ready and should run in
   parallel with theory work; they are not blocked by the derivation.
3. Two-clock ELBO is R22-PR1 and should be written before any new reward
   mechanism is added.
4. Entropy/floors should be reframed as derived target-entropy constraints;
   current floors remain stabilizer flags until the design is implemented.
5. Mechanism budget is now explicit: every new mechanism must retire, absorb,
   or supersede one existing mechanism.
```

Execution receipt (same date, subagent-driven):

```text
R22-1 delivered:
  memory/R22_TWO_CLOCK_ELBO.md

R22-4 delivered:
  memory/R22_TARGET_ENTROPY_DESIGN.md

R22-3 audit delivered:
  existing diagnostics: z_usage_entropy, team_disc_reward_env_ratio,
  z_boundary_trunc_rate, z_boundary_trunc_rate_dur3/7/13/24.
  missing diagnostics for future code stage: z_decisions_per_update,
  z_advantage_mean/std/var, combined_intrinsic_env_ratio.

Review:
  Spec reviewer approved both R22 docs.
  Quality reviewer initially flagged five implementation-risk issues:
    Z/z_i metric ambiguity, target-temperature sign, clock-count normalization,
    detached/null baseline semantics, and tau/r notation mix.
  Codex fixed all five issues; re-review approved.

No training code was changed in this R22 execution.  R21 and HMASD baseline
experiments remain launch-ready and should not wait for further R22 theory work.
```

## 2026-07-05 Codex implements R21 launch-preflight fixes and cloud-direct launch support

Source:

```text
reviewer/model: Claude / CC review provided by user, then Codex verification
role: reviewer -> executor
input artifacts:
  docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md
  memory/ATTENTION_POINTER.md
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
  user instruction: direct cloud run, support n_agents, HMASD baseline set to 6-agent
scope: implementation / experiment / runner / baseline logging
disposition: modified-accepted
affected files:
  ha_ctse_process/config.py
  ha_ctse_process/team_intent.py
  ha_ctse_process/train.py
  ha_ctse_process/standalone_agent.py
  train_multiproc_config_1.py
  scripts/run_r21_team_intent_local_cuda.ps1
  scripts/run_r21_team_intent_cloud_64env.sh
  scripts/run_hmasd_currentenv_baseline_cloud_64env.sh
  docs/superpowers/plans/2026-07-05-r21-launch-batch.md
  memory/ExpRecord.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
```

Verdict:

```text
Accepted the launch-preflight critique with one user-driven routing change:
skip the local probe and launch R21 directly on cloud.  The structural fixes
remain mandatory before launch: K_team=48, team_disc_coef=0.05, default-off
Z entropy floor, per-duration truncation diagnostics.  HMASD baseline must be
6-agent and must expose HA-CTSE parity eval metrics before its result can be
used as the current-environment anchor.
```

Implemented changes:

```text
R21:
  - default `team_intent_k`: 12 -> 48.
  - default `team_disc_coef`: 0.1 -> 0.05.
  - added default-off `z_entropy_floor_*` config/CLI/manifest/checkpoint
    metadata, TensorBoard, console, and process metrics.
  - added `active_duration_indices` state and per-duration Z-boundary
    truncation metrics (`z_boundary_trunc_rate_dur3/7/13/24`).
  - updated R21 local runner and added `scripts/run_r21_team_intent_cloud_64env.sh`
    using the coef005 S-base: prototype-disc reward coef=0.05, duration floor
    disabled, guard kill.

HMASD baseline:
  - added `--n_agents` to `train_multiproc_config_1.py`.
  - made Scenario-7 validation respect explicit `--n_agents`.
  - added eval diagnostics/logging/TB for `coverage_eq1_step_fraction`,
    `coverage_eq1_episode_fraction`, `zero_throughput_episode_fraction`, and
    `throughput_gt5_step_fraction`.
  - added `scripts/run_hmasd_currentenv_baseline_cloud_64env.sh`.
```

Validation:

```text
Python AST/compile syntax check passed for modified Python files.
`ha_ctse_process.train --help` exposes `--enable_z_entropy_floor` and R21
controls.
`train_multiproc_config_1.py --help` exposes `--n_agents`.
PowerShell R21 local dry-run prints K=48, team_disc_coef=0.05, guard kill,
coef005 base, and duration floor disabled.
Linux bash runners were statically checked on Windows because local bash is
not installed; cloud must run each script with `--dry-run` before launch.
```

Modification:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Executor / Experiment Manager
authority source: user direct instruction + CC launch-preflight review
reason: prevent K_team/lifetime structural truncation, avoid known 0.1
  intrinsic-pressure pathology, preserve Z entropy diagnostics, and make the
  HMASD 6-agent baseline comparable to HA-CTSE eval metrics.
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: Round 21 Team-Intent Restoration
  docs/superpowers/plans/2026-07-05-r21-launch-batch.md
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
  memory/ExpRecord.md :: EXP-20260705-hmasd-currentenv-baseline
follow-up owner: Experiment Manager
status: implemented / locally syntax-validated / awaiting cloud dry-run and launch
```

## 2026-07-05 Codex reads R19 team-transition cloud logs

Source:

```text
reviewer/model: Codex
role: experiment-manager / reviewer
input artifacts:
  dist\r_19log\logs_cloud_r19_team_transition_64env
  memory/ExpRecord.md :: EXP-20260704-r19-team-transition-64env
scope: experiment / result-interpretation
disposition: modified
affected files:
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
```

Readout:

```text
Arms in downloaded R19 logs:
  a2_baseline_samecheck_reward_coef01:
    finished, exit_code=0, complete to 960k.
  a2_plus_t_probe_reward_off:
    finished, exit_code=0, complete to 960k.
  a2_plus_t_reward_coef005:
    downloaded snapshot says running and includes updates to 224k only.

No Traceback/RuntimeError/NaN/OOM found in the downloaded standalone logs.
```

Key numbers:

```text
Baseline 960k eval:
  reward=54.003165
  coverage=0.333333
  qos=0.178205
  throughput=11.400000
  backhaul_connected_frac=0.365600
  zero_throughput_ep_frac=0.600000
  coverage_eq1_step_frac=0.000000

A2+T probe reward-off 960k eval:
  reward=23.786741
  coverage=0.115000
  qos=0.072848
  throughput=5.700000
  backhaul_connected_frac=0.272800
  zero_throughput_ep_frac=0.600000
  coverage_eq1_step_frac=0.000000

A2+T reward-on downloaded snapshot:
  latest update=7, total_steps=224000
  160k eval reward=22.442625
  coverage=0.100000
  qos=0.061031
  throughput=1.864259
  backhaul_connected_frac=0.234100
  zero_throughput_ep_frac=0.750000
```

Mechanism gate:

```text
Reward-off probe at 960k:
  team_t_samples=3136
  team_t_mi=-0.042034
  team_t_self=0.923
  last-5 mean team_t_mi=-0.064172
  last-5 mean team_t_self=0.9312

Reward-on snapshot at 224k:
  team_t_mi=-0.044873
  team_t_self=0.921
  team_t_rew=-0.018776
  team_t_ratio=0.016
  last-5 mean team_t_mi=-0.052448
  last-5 mean team_t_ratio=0.0142
```

Interpretation:

```text
R19, as currently implemented, does not pass its own reward-off mechanism gate.
The expected sign was sustained positive team-transition MI; the observed
probe signal is consistently negative through 960k.  The self fraction is in
the nominal band but close to the upper edge, suggesting the head mostly sees
self/unchanged transitions and is not providing a useful team residual.

The reward-on arm is not complete in the downloaded snapshot, so this is not a
final reward-arm verdict.  But the early reward-on mechanism metrics follow
the same negative-MI pattern and the 160k task readout is not better than the
matched baseline.  The safe conclusion is mechanism-negative unless a later
complete reward-on log contradicts it with sustained positive team_t_mi and
task gains.
```

Decision:

```text
Do not broaden R19 coefficient sweeps from this evidence.  Treat R19
team-transition residual as not yet the missing HMASD-style team engine.
Compare against the R21 team-intent restoration line, where a sampled team
intent Z ships with an objective/discriminator pressure rather than relying on
the current transition residual target.
```

Modification:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: experiment-manager / reviewer
authority source: downloaded R19 cloud logs in dist and pre-registered
  EXP-20260704-r19-team-transition-64env gates
reason: record the R19 mechanism-negative read and prevent drift into R19
  coefficient sweeps before a valid reward-off signal exists.
affected files:
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
linked plan section: R19 team-transition heads
linked experiment: EXP-20260704-r19-team-transition-64env
validation performed: parsed standalone_train.log lines for eval/update
  metrics and checked runner_status plus traceback/NaN/OOM patterns.
follow-up owner: Experiment Manager / Architect
status: implemented
```

---

## 2026-07-05 Codex reads R16.5 continuation 64env cloud logs

Source:

```text
reviewer/model: Codex
role: experiment-manager / reviewer
input artifacts:
  dist\logs_cloud_r16_5_continuation_64env
  memory/ExpRecord.md :: EXP-20260705-r16-5-continuation
scope: experiment / result-interpretation
disposition: accepted / completed
affected files:
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
```

Readout:

```text
Both downloaded continuation branches finished cleanly with exit_code=0 and no
Traceback/NaN/OOM found.

seed2, floor_coef=0.05, 960k:
  reward_mean=71.713382
  coverage=0.416667
  qos=0.240737
  throughput=13.105124
  backhaul_connected_frac=0.500000
  zero_throughput_ep_frac=0.500000
  coverage_eq1_step_frac=0.016400
  duration_usage_entropy=0.937736 final / 0.958307 last10
  duration_entropy_floor_active=0 final / 0 last10
  proto_disc_reward_env_ratio=0.060781 final / 0.054688 last10
  roster_ar_kl_shuffled~=0.000005 final / 0.000004 last10

seed1, floor_coef=0.1 bounded retry, 960k:
  reward_mean=31.248840
  coverage=0.121667
  qos=0.091398
  throughput=6.778694
  zero_throughput_ep_frac=0.650000
  coverage_eq1_step_frac=0
  duration_usage_entropy=0.917980 final / 0.941544 last10
  duration_entropy_floor_active=0 final / 0 last10
  proto_disc_reward_env_ratio=0.230569 final / 0.235317 last10
  roster_ar_kl_shuffled~=0.000004
```

Interpretation:

```text
The 64env seed2 coef=0.05 run improves the story versus the local scaffolded
read on lifetime stability: duration entropy self-sustains late and the floor
is inactive.  But it remains far from the user-stated S7-S1 parity bar
(`coverage_eq1_step_frac=0.0164` versus the target of at least half of eval
steps at coverage==1.0), and zero-throughput episodes are still 50%.

The one allowed coef=0.1 retry is negative: it keeps duration entropy high but
materially worsens task metrics.  This closes the bounded retry branch.

Roster content remains decorative in both branches (`roster_ar_kl_shuffled`
around 4e-6 to 5e-6), so this read does not justify any further broad R16
roster-only sweep.
```

Decision:

```text
Stop R16.5 floor tuning.  Keep coef=0.05 as a stabilized baseline/control with
the narrow claim that it helps avoid duration collapse / late regression in
some settings.  It does not solve the cooperative parity target.  Move
algorithmic attention to R19/R21 rather than more R16 roster tuning.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Experiment Manager / Reviewer
authority source: user request to inspect downloaded dist logs
reason: completed cloud logs changed experiment status and closed the R16.5
  bounded floor-retry branch.
affected files:
  memory/ExpRecord.md
  memory/ATTENTION_POINTER.md
  memory/cross_validation.md
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: R16.5 / roster-docking stabilization
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r16-5-continuation
validation performed:
  read runner_status.txt, standalone_train.log eval lines, metrics/eval_episodes.csv,
  and metrics/train_updates.csv from both continuation branches.
follow-up owner: Codex / Experiment Manager
status: completed / interpreted
```

---

## 2026-07-05 Codex review of `ALGORITHM_DESCRIPTION_v6.md`

Source:

```text
reviewer/model: Claude / Research Copilot proposal, reviewed by Codex
role: reviewer
input artifacts:
  memory/ALGORITHM_DESCRIPTION_v6.md
  memory/ALGORITHM_PRINCIPLES.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ATTENTION_POINTER.md
scope: principles / algorithm description / reference promotion
disposition: modified / pending user confirmation
affected files:
  memory/cross_validation.md
  memory/ATTENTION_POINTER.md
```

Verdict:

```text
Accept `ALGORITHM_DESCRIPTION_v6.md` as a strong conceptual synthesis of the
current HA-CTSE direction, but do not yet promote it as the sole canonical
reference that principles point to without a status box that separates:
  implemented code,
  locally validated wiring,
  experiment-supported behavior,
  theoretical / intended claims.
```

Strongest-for:

```text
The v6 description correctly captures the current post-R21 algorithm shape:
three timescales, recognition vs sampled commitment distinction, sampled Z as
the non-vacuous team engine, prototype-response skills, held team intent,
atomic Z-boundary reassignment, async docking between boundaries, and the
communication-metrics-as-diagnostics boundary.  It also correctly puts the
vacuity lemma at the center of why recognized kappa and sampled Z need different
intrinsic pressures.
```

Strongest-against / required qualifications:

```text
1. "HMASD is the exact special case" is useful as an architectural limiting
   case, but code-level exact equivalence is not yet proven.  Phrase as
   limiting case unless an explicit full-sync/HMASD-reduction test is added.

2. The substrate-language around OPT prototypes / omega / kappa should not
   overstate validation.  The substrate gate and compact/omega diagnostics are
   evidence for using OPT as a situation basis, but R21 performance and the
   team-intent engine are not yet experimentally validated.

3. The intrinsic system description should label R21 team intent and team-disc
   reward as implemented default-off and locally smoke-validated, not
   performance-validated.  Current R21 has no formal 320k/960k read yet.

4. "Provided by construction" is true for async lifetimes and atomic
   Z-boundary reassignment in the implemented mechanism, but rollout and
   checkpoint boundaries can still truncate held decisions.  The read must
   report `z_boundary_trunc_rate` before making a strong mechanism claim.
```

Sober number / current blocker:

```text
The strongest current performance read is still R16.5 PASS-SCAFFOLDED, not a
clean parity result: 960k `coverage_eq1_step_frac=0.075700`, far below the
near-term HMASD-level target of at least half of primitive eval steps at
coverage == 1.0.  v6 should therefore be framed as the current algorithmic
design contract, not as a solved-behavior description.
```

Decision:

```text
If the user confirms, promote v6 by adding a pointer from
`ALGORITHM_PRINCIPLES.md` to `ALGORITHM_DESCRIPTION_v6.md`, but first add an
"Implementation / Validation Status" section to v6 with the caveats above.
Until then, v6 remains a pending canonical-description candidate.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Reviewer
authority source: user supplied Claude note saying v6 awaits confirmation
reason: prevent a pending external description from being mistaken for an
  already-confirmed reference contract.
affected files:
  memory/cross_validation.md
  memory/ATTENTION_POINTER.md
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: Round 21 Team-Intent Restoration
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
validation performed:
  read-only review of v6 against current principles, plan, pointer, and
  experiment dashboard; no code validation required.
follow-up owner: user / Codex
status: reviewed / modified-acceptance / awaiting user confirmation
```

---

## 2026-07-05 Codex pre-registers R21 local CUDA launch runner

Source:

```text
reviewer/model: user + Codex
role: executor / experiment-manager
input artifacts:
  docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
scope: experiment / runner
disposition: accepted / implemented
affected files:
  scripts/run_r21_team_intent_local_cuda.ps1
  memory/ATTENTION_POINTER.md
  memory/ExpRecord.md
  memory/cross_validation.md
```

Summary:

```text
Created a local CUDA runner for the formal R21 read.  Default experiments are
`r21_z_probe` and `r21_z_reward`, both inheriting the stabilized R16.5 entfloor
and prototype-discriminator reward base.  The runner also offers optional
`entfloor_control` under the same code snapshot.  The first R21 read is a 320k
structural gate; the 960k result is meaningful only if that gate is healthy.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Experiment Manager / Executor
authority source: user "continue" after R21 implementation + R21 spec
reason: R21 code was implemented but not launch-aligned; the experiment needed
  exact commands, controls, and gates before any run.
affected files:
  scripts/run_r21_team_intent_local_cuda.ps1
  memory/ATTENTION_POINTER.md
  memory/ExpRecord.md
  memory/cross_validation.md
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: Round 21 Team-Intent Restoration
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
validation performed:
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_r21_team_intent_local_cuda.ps1 -DryRun` -> exit 0.
  - Dry-run output showed inherited entfloor controls, `--team_bridge_type stochastic`,
    `--reward_ratio_guard_mode warn`, `--enable_team_intent`, and distinct
    probe/reward arms.
follow-up owner: Codex / Experiment Manager
status: implemented / dry-run validated / launch-ready
```

---

## 2026-07-05 Codex post-review fixes for R21 wiring

Source:

```text
reviewer/model: Codex subagent Pascal + Codex
role: reviewer / executor
input artifacts:
  docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md
  current R21 diffs in ha_ctse_process/*
scope: implementation / code review
disposition: accepted / implemented
affected files:
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  tests/r21_team_intent_test.py
  memory/ATTENTION_POINTER.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
  memory/cross_validation.md
```

Summary:

```text
The read-only review found four real R21 wiring risks: missing `team_codes` in
the prototype-discriminator batch, legacy low-actor team-code conditioning still
being possible, `team_bridge_type=none` silently degenerating Z, and missing
checkpoint state for the team-intent empirical prior.  All four were fixed
before handoff.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Executor
authority source: user-authorized subagent review + R21 implementation task
reason: prevent silent or crashing R21 combination experiments before launch.
affected files:
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  tests/r21_team_intent_test.py
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: Round 21 Team-Intent Restoration
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
validation performed:
  - `python -m pytest tests\r21_team_intent_test.py -q` -> 6 passed.
  - R21 + prototype-disc smoke -> exit 0.
  - R21 + reward-on checkpoint smoke -> exit 0.
  - checkpoint readback confirmed tensor-safe `team_intent_prior_counts`.
  - R21 + `team_bridge_type=none` CLI smoke -> expected ValueError.
  - import check -> import_ok.
  - `git diff --check` -> exit 0, with pre-existing pytest-temp permission warnings.
follow-up owner: Codex / Experiment Manager
status: implemented / validated / no formal R21 run launched
```

---

## 2026-07-05 Codex implements R21 Team-Intent Restoration default-off

Source:

```text
reviewer/model: user directive + CC-reviewed R21 plan + Codex
role: executor
input artifacts:
  docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md
  memory/ATTENTION_POINTER.md R21 directive
  memory/IMPLEMENTATION_PLAN.md Round 21 section
scope: implementation / algorithm mechanism / diagnostics
disposition: accepted / implemented
affected files:
  ha_ctse_process/team_intent.py
  ha_ctse_process/config.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  tests/r21_team_intent_test.py
  memory/ATTENTION_POINTER.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
  memory/cross_validation.md
```

Summary:

```text
Implemented the R21 two-clock team-intent mechanism as default-off code:
sampled held team intent Z, atomic full-team AR reassignment at Z boundaries,
async individual docking against held Z between boundaries, boundary-only Z
log-prob charging, skipped edit/switch penalty at Z boundaries, and an optional
team discriminator reward/probe over next-state labels.  Metrics now expose
Z usage/dwell/truncation/intervention and team-disc loss/accuracy/residual/
reward-ratio diagnostics.

No formal R21 performance run has been launched.  The new ExpRecord entry is
planned-only and requires an exact stabilized-base command/gate before launch.
```

Modification metadata:

```text
changed_at: 2026-07-05
actor/model: Codex
active role: Executor
authority source: user explicit implementation request + R21 user override in
  memory pointer and implementation plan
reason: restore HMASD-style team skill/cooperative pressure while preserving
  asynchronous per-agent lifetimes; R21 supersedes Round 20 team-bridge removal
  as the active code task.
affected files:
  ha_ctse_process/team_intent.py
  ha_ctse_process/config.py
  ha_ctse_process/standalone_agent.py
  ha_ctse_process/train.py
  ha_ctse_process/plotting.py
  tests/r21_team_intent_test.py
  memory/ATTENTION_POINTER.md
  memory/IMPLEMENTATION_PLAN.md
  memory/ExpRecord.md
  memory/cross_validation.md
linked plan section:
  memory/IMPLEMENTATION_PLAN.md :: Round 21 Team-Intent Restoration
linked experiment:
  memory/ExpRecord.md :: EXP-20260705-r21-team-intent
validation performed:
  - `python -m pytest tests\r21_team_intent_test.py -q` -> 4 passed.
  - import check for train/standalone_agent/team_intent/plotting -> import_ok.
  - structure smoke with `--enable_team_intent --enable_team_disc_probe` -> exit 0.
  - reward-on smoke with `--enable_team_disc_reward --reward_ratio_guard_mode warn` -> exit 0, warn guard logged without stopping.
  - `git diff --check` -> exit 0; existing `.pytest_tmp_r12_verify` permission warnings remain unrelated to R21.
follow-up owner: Codex / Experiment Manager
status: implemented / locally validated / experiment not launched
```

---

## 2026-07-05 Codex adds HA-CTSE run-result packaging scripts

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.
- scope: packaging / experiment-result transfer
- disposition: accepted

## 2026-07-05 Codex creates `LTM_exp` experimental skill

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.
- scope: workflow / skill-testing
- disposition: accepted

## 2026-07-05 Codex response to collaboration-memory protocol update

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.
- scope: workflow
- disposition: accepted

## 2026-07-05 Codex R16.5 entfloor completed readout

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-04 Codex response to CC FINAL guard-mode spec

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-04 Codex R16.5 closing-plan implementation receipt

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-04 Research Insight Duties added to AGENT_ROLES (user-mandated skill-gap fix)

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-05 CC (Research Copilot) principles-level advice: Round 22 candidates

Modification: actor CC (Research Copilot); authority: user invocation
("advice on the principles level"); affected: this ledger; status: advice
logged, items await user adoption.

```text
THROUGH-LINE: v6 has a unified ARCHITECTURE but a patchwork OBJECTIVE;
the deep issues are symptoms of that.

PR-1 UNIFY THE OBJECTIVE (highest value): derive the two-clock ELBO for
   the ACTUAL current model (hierarchical semi-Markov PGM, slow sampled Z
   + fast sampled z_i). The R15 derivation is STALE post-R21 (it assumed
   recognition-only). Would answer: (i) do coordinator-residual and team-
   disc terms compose or double-count; (ii) principled relative scales
   (the dose-response finding is the empirical signature of unprincipled
   coefficients); (iii) missing cross-layer terms (e.g. I(Z; xi)). Nobody
   has published the two-clock bound — paper theory core. ~75% it yields
   at least one of the three. Zero GPU; parallel to runs.
PR-2 ENTROPY AS DERIVED CONSTRAINT, NOT PATCHED BONUS: per-head
   target-entropy Lagrangian (SAC-style auto-temperature) subsumes floor +
   anneal + z-floor in one principled mechanism; and once entropy terms
   are DERIVED (PR-1 gives them free), the PASS-SCAFFOLDED qualification
   dissolves honestly — HMASD's entropy was never emergent either, it was
   in the objective. Split R10.2-F: keep "never force heterogeneity as a
   reward target"; stop outlawing principled entropy control.
PR-3 THE CREDIT TENSION TRIANGLE (own it before a reviewer does):
   K_team >= max lifetime (protect fast clock) vs pi_Z sample efficiency
   vs Z-advantage variance. At K_team=48: ~1 Z-decision/episode. Intrinsic
   to the two-clock idea; state as principle + diagnostics (Z-decisions
   per update; Z-advantage variance). Graceful degradation note: q_D
   reward shapes the low level even while pi_Z learns slowly.
PR-4 MECHANISM BUDGET (cultural): every new mechanism retires or absorbs
   one; the ELBO doubles as the pruning tool (terms not in the bound are
   deletion candidates, not defense obligations).
```

## 2026-07-05 CC pre-launch amendments to the R21 spec (advice on the R21 decision)

Modification: actor CC (Research Copilot/Architect-advisory); authority:
user request ("advice about my decision in R21"); affected: R21 spec
(amended in place), this ledger; status: accepted (spec is CC-authored);
Codex applies before launch.

```text
A1 BLOCKING FIX: K_team 12 -> 48. Atomic reassignment makes K_team the
   effective max lifetime; K_team=12 truncated candidates 13/24 EVERY
   time -> artificial duration collapse indistinguishable from the R16.5
   pathology in the logs. Rule: K_team >= 2x max candidate. Log truncation
   per duration bucket (also distinguishes the two 160k failure modes:
   flat disc_acc from too-few-Z-samples vs dead differentiation).
A2 EVIDENCE FIX: team_disc_coef 0.1 -> 0.05. The R16.5 dose-response
   (0.1 collapses duration entropy, 0.05 self-sustains) postdates the
   spec; total intrinsic pressure on the S-base must not triple. Watch
   COMBINED reward/env ratio in [0.05, 0.5].
A3 INSURANCE: head-generic entropy-floor flag for pi_Z, default-off,
   Z-usage entropy logged with standard alarms from day one.
A4 OUTCOME MAP (160k team_disc_acc): gradual climb = catching -> 320k;
   flat = check per-bucket truncation + Z-sample count before declaring
   dead; instant ~1.0 = leak audit on q_D inputs first.
DECISION READ: R21 confidence 65% -> ~70% with A1/A2 applied; R19's
   mechanism-negative removed the rival explanation, and the S-base gives
   the engine a non-decaying platform. Asymmetry note: under the
   dissociation structure, even a clean R21 failure is a publishable
   finding about commitment under asynchrony.
```

## 2026-07-05 CC post-batch read: S-base decision, R19 verdict, v6 status box added

Modification: actor CC (Research Copilot/Reviewer); authority: user request
("check memory, give suggestions"); affected: ALGORITHM_DESCRIPTION_v6.md
(status box added per Codex condition), this ledger; status: implemented.

Key reads accepted from Codex's analysis, with CC additions:
```text
1. R16.5 pair = a DOSE-RESPONSE HINT: intrinsic coef 0.1 -> permanent floor
   + ratio pathology (kill_triggered=2); coef 0.05 -> self-sustaining
   entropy (floor_active=0) + higher reward (71.7). The intrinsic scale
   itself drives duration collapse. DECISION PROPOSED: coef005 arm =
   canonical stabilized base (S-base) for R21; resolve the 64env-vs-16env
   matched-control wrinkle BEFORE launch (local coef005 rerun as control,
   or R21 at 64env on the freed cloud slot).
2. coverage_eq1 = 0.0757: first nonzero parity-metric read in project
   history. Meaning unknowable without the HMASD current-env baseline —
   STILL absent from the dashboard after three blocking flags; the cloud
   slot is now free; launch it today (2 seeds).
3. R19 mechanism-negative is DIAGNOSED (R15 data-hunger caveat
   materialized: self_frac 0.93 starves the conditional; posterior learns
   noise). No further spend; negative wing of the dissociation. Caution:
   probe-vs-baseline task gap (0.115 vs 0.333, both reward-off) is
   seed-variance-sized — do not read as "heads hurt".
4. R21 launch today: probe -> reward; earliest tell = team_disc_acc shape
   at 160k (gradual climb = catching; instant ~1.0 = leak; flat = dead).
5. v6 promotion condition fulfilled: implementation/validation status box
   added distinguishing experiment-supported / locally-validated /
   mechanism-negative / theory-only. Awaiting user confirmation to promote.
```

## 2026-07-04 CC response to Gemini roadmap: two-tempo environment ACCEPTED with the design crux

Modification:
  actor/model: CC (Research Copilot); authority source: user-relayed Gemini
  proposal; status: accepted-with-corrections; affected: this ledger +
  future env spec (Codex implements after co-design)

Gemini proposal (roadmap + minimal two-tempo env for C2) ACCEPTED. Three
corrections:
```text
1. Do NOT pre-write the R19 ablation conclusion ("continuous projection
   can never beat discrete sampling") — R19 is a dissociation, not a
   designated loser; either outcome is a finding.
2. "90%" = confidence in WRITING C1/C3 into an architecture paper, not in
   proving C1 (evidence still zero until R21 reads). Keep separate.
3. Draft BOTH contribution sentences (async-headline vs hierarchy-headline);
   the two-tempo result decides which is defensible.
```

DESIGN CRUX (prevents spurious C2 falsification): with no cost to
re-deciding, full-sync k=1 dominates ANY two-tempo env (slow agent just
re-selects). The env must make temporal abstraction itself load-bearing:
DUAL FAILURE PRESSURE — slow agent: charge-and-fire, no intermediate
reward, interruption resets (k=1 fails by exploration collapse: ~10 chained
correct re-selections unrewarded; commitment = one decision); fast agent:
per-step moving target (k=10 fails reactivity); TEAM reward only, on
fire+intercept coincidence. Controls B/C/D + HMASD, capacity-matched,
10+ seeds (~50-step episodes cure the seed-1 disease).

MONEY FIGURE: parameterize tempo ratio (1:1, 1:2, 1:5, 1:10); prediction:
arms tie at 1:1, D - max(B,C) gap GROWS with heterogeneity. Dose-response
beats a single win — the mechanism responds to the exact variable the
thesis names.

Queue impact: none — env is design work (CPU-minutes per seed); entfloor /
HMASD baseline / R21 build proceed unchanged.

## 2026-07-04 CC stance clarification: R21 evidence-ranked ABOVE R19

Prompted by a fair user challenge ("you say R19 is valuable but my
correction seems suspicious"). For the record, by the evidence-hierarchy
rule (R-2):

```text
R21 (user's correction, team-intent restoration): evidence class (a) —
  HMASD published ablations. CC confidence ~65% to beat the stabilized
  base — the highest assigned to anything in this project. If only one of
  R21/R19 could be built, build R21.
R19 (transition residual): evidence class (c)+(d) — derivation + DADS
  analogy. Value is as a CONTROL: dissociation (commitment-specifically vs
  any-team-signal), Stage-2 churn precursor, near-zero marginal cost
  (already running). Not co-equal with R21.
"Override" / honesty-ledger labels on R21 are PROVENANCE (owner judgment
  vs gate-fired), not epistemic distrust — CC's earlier writing conflated
  the axes; corrected here.
Historical note: R21 is structurally Round 11's anchor recommendation
  (faithful cooperative-half transplant first) plus the async fast clock.
  The user's correction closes the loop the R12-R18 recognition-first arc
  opened — that arc yielded real assets (substrate gate, vacuity lemma,
  roster-docking) but its one cost was removing commitment, which R21
  reinstates.
```

## 2026-07-04 Canonical v6 description written (user-requested expansion)

Follow-up to the Research Copilot CHECK: the detailed restatement expanded
into `memory/ALGORITHM_DESCRIPTION_v6.md` (three-timescale hierarchy;
layer-by-layer; layer-matched pressure system; provided-vs-claimed split
with C4 marked evidence-unfunded). Awaiting user confirmation that it
matches intent; on confirmation it becomes the reference description and
the principles' opening should point to it.

## 2026-07-04 CC (Research Copilot) CHECK of the composite idea (v6)

Modification:
  actor/model: CC (Claude, Cowork); active role: Research Copilot
  authority source: user invocation "/research-copilot check my idea"
  affected files: cross_validation.md (this entry only)
  status: verdict logged; framing decision owned by user

Sharpened restatement (pending user confirmation): a THREE-TIMESCALE
HIERARCHY — recognition (continuous) / commitment (slow, synchronized,
sampled) / response (fast, async, sampled) — where each layer's intrinsic
pressure is determined by what the layer IS (vacuity: recognized layers pay
on the future; sampled layers pay on identifiability), interfaced by atomic
reassignment + docking.

Claim decomposition: C1 substrate VERIFIED (16env/N=4/seed1 only);
C2 individual engine WEAK; C3 team engine UNTESTED (external evidence
only); C4 async-lifetime benefit ZERO confirmatory reads in ~15 runs
(best: one seed-1 correlation at the 480k peak); C5 two-clock THEORY ONLY;
C6 parity bar itself UNVERIFIED (P1).

VERDICT: MODIFY — pursue composite; realign thesis emphasis. ~65% R21 stack
beats stabilized base; ~25-30% async-lifetime headline ever confirms on
existing scenes; ~80% the timescale-hierarchy framing is publishable given
the R19/R21 dissociation.
SOBERING: thesis claim C4 has 0 confirmations; coverage_eq1 = 0.0 in every
run ever, peak included.
BLOCKING: P1 (HMASD current-env re-verification, 1-2 GPU-days) is named
BLOCKING from now on — deferred >= 4 times while being load-bearing for
both the parity bar and R21's justification.
UNREQUESTED ALTERNATIVE (ranked ahead of current framing on
publishability today): pivot the paper spine to the timescale hierarchy
(vacuity as organizing theorem, atomic-vs-docked switching, R19/R21
dissociation as empirical centerpiece); demote async lifetimes to a
provided capability pending the two-tempo mechanism scene. User decision.

## Round 21 (2026-07-04) — Team-Intent Restoration: two-clock hierarchy (USER OVERRIDE + CC design)

Modification:
  changed_at: 2026-07-04
  actor/model: CC (Claude, Cowork), design under USER ARCHITECT OVERRIDE
  active role: Architect+Reviewer (authority source: user instruction —
    "bring the autoregressive team skill back, keep async low-level skills;
    highest priority; no ablation")
  reason: user judged HMASD's proven team-skill architecture must return;
    R20 D2 (team_bridge_none ablation) DROPPED, D3 (kappa* deferral)
    DISSOLVED into an immediate build
  affected files: cross_validation.md, IMPLEMENTATION_PLAN.md,
    ATTENTION_POINTER.md, ALGORITHM_PRINCIPLES.md,
    docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md (spec)
  linked principle/plan: R18.1 atomic variation; R18.2 kappa* form;
    R19 dual-engine; R11.3 bootstrap scale; channel-pressure rule
  linked experiment: EXP-2026070X-r21-team-intent (to be created pre-launch)
  validation performed: design-level consistency check against R10-R19;
    no training code touched
  follow-up owner: Codex (build now, default-off, parallel to entfloor)
  status: accepted (user-directed)

### R21.0 The design in one screen

```text
TWO-CLOCK HIERARCHY:
  slow synchronized clock: Z_m ~ pi_Z(Z | c, omega), held K_team=12 checks;
    at each Z boundary, ATOMIC full-team AR reassignment
    z_i | Z, c, o_i, z_{<i}   (R18.1: commitment buys atomic switching)
  fast asynchronous clock (unchanged): individual renewals dock against the
    current Z + standing roster:  z_i | Z, c, o_i, roster
  HMASD = special case (K_team=1, all lifetimes = k).

ENGINE SHIPS IN THE SAME BUILD (channel-pressure rule; three decorative-
channel autopsies say never defer this):
  r_i += lambda_D * clip(log q_D(Z|s_{t+1}) - log p_hat(Z), +-2), low-level,
  per-step, bootstrap scale 0.1, warmup 20k — NON-VACUOUS because Z is
  SAMPLED (the vacuity lemma delimits the layers: recognized substrate vs
  sampled intent). q_d gains Z conditioning: q_d(z_i|o', kappa, Z).

BYPRODUCT: R21 arm vs the recognition-only stabilized base IS the
commitment-vs-recognition decisive experiment (R14.0) on S7-S1 — the
mainline now answers it for free.
```

### R21.1 Honesty ledger

```text
- This reverses the R20 Architect gating (deceptive-axis trigger) by USER
  decision; recorded as an override, not a derived conclusion. The R18.3
  matrix prediction becomes falsifiable through this arm: if Z-restoration
  wins on S7-S1, the win is attributed to the restored EXPLORATION ENGINE
  (consistent with R18.3's "parity comes from the bootstrap"), not to
  symmetry-breaking commitment; the matrix stands unless deceptive-cell
  evidence contradicts it.
- One structural variable (the whole Z system) rather than strict
  single-variable: accepted deviation, justified by the channel-pressure
  rule — intent without pressure would be decorative channel #4.
- a2_plus_t DEMOTED to complementary (heads stay built and available);
  team_bridge_none DROPPED per user.
- Sequencing: build NOW; LAUNCH only on the stabilized entfloor base after
  its 480k read — restoring an engine on a decaying base reads nothing.
```

Spec (single source of truth):
docs/superpowers/plans/2026-07-04-r21-team-intent-restoration.md


## 2026-07-04 CC (Reviewer+Architect) response to Codex Team-bridge assessment: Round 20 disposition

Modification:
  changed_at: 2026-07-04
  actor/model: CC (Claude, Cowork)
  active role: Reviewer + Architect (authority source: user instruction this
    turn; AGENT_ROLES.md boundaries respected — no implementation code touched)
  reason: Codex code-audit of the Team bridge (user-relayed) required a
    binding module-boundary decision
  affected files: cross_validation.md, ALGORITHM_PRINCIPLES.md,
    IMPLEMENTATION_PLAN.md, ATTENTION_POINTER.md
  linked principle/plan: R18.2 kappa* canonical form; R18.3 task matrix;
    channel-pressure rule; R16.5 in-flight cycle
  linked experiment: team_bridge_none ablation (queued, post-a2_plus_t)
  validation performed: ledger consistency check (no contradiction with
    R10-R19); config `team_bridge_type=none` verified to exist
  follow-up owner: Codex (D2 ablation when triggered); Architect (D3 timing)
  status: accepted

REVIEWER VERDICT on Codex's assessment: ACCEPT diagnosis; one context
correction; one recommendation BLOCKED.

```text
ACCEPTED: g_tau ~ pi_g(g|c_tau) sits BESIDE the assignment path, never
  upstream — it was never HMASD's Z. The user's sensed thought/implementation
  deviation is real and now precisely characterized. NEW content = the
  three-role unbundling: (1) discrete bottleneck of c (redundant, possibly
  noise-adding since the high level already sees c); (2) quasi-HMASD team
  skill (unconstrained, hence decorative — matches logged g_itv/g_skill_mi);
  (3) low-level critic conditioning (cheap, untested).
CONTEXT CORRECTION: the "two-layer reorganization" recommendation re-derives
  R18.2 (kappa* is the canonical coordination-intent form) and must inherit
  R18.3's gating (intent layer load-bearing only on the deceptive axis; NOT
  on S7-S1). Codex's three influence tests are correct and map to existing
  machinery (g-intervention KL; R19 transition heads).
BLOCKED: "refactor g into an HMASD-style team intent" NOW = building kappa*
  early, off-axis, and pressure-less -> the fourth decorative channel
  (g -> AR prefix -> roster -> kappa*). Channel-pressure rule forbids it.
```

ARCHITECT DISPOSITION (binding):

```text
D1 FREEZE: g_tau DEPRECATED-IN-PLACE. No new mechanism may condition on g.
   No code change now (one-variable discipline; R16.5 cycle in flight).
D2 ABLATION QUEUED: post-R16.5/a2_plus_t, one-variable `team_bridge_none`
   on the stabilized base (team_bridge_type=none exists in config).
   Tests all three unbundled roles incl. critic conditioning.
   Read: no regression expected; removal HELPING confirms noise (case 1).
D3 RESERVATION: coordination-intent slot belongs to kappa* (R18.2), gated
   on the deceptive axis (R18.3). Build clean when triggered: sampled
   pi(kappa*|kappa,c), UPSTREAM of AR/roster assignment, shipped WITH
   pressure (commitment progress + kappa*-conditioned transition heads),
   judged by Codex's three influence tests. Never refactor g into it;
   delete the bridge when kappa* lands.
D4 VOCABULARY: "situation substrate (c/omega/kappa)" vs "coordination
   intent (kappa*)"; "team bridge / g_tau" is legacy terminology.
```

## 2026-07-04 CC FINAL guard-mode spec issued (supersedes Gemini v1/v2)

Gemini's v2 incorporated both prior additions but left ONE real gap and two
minor ones; per user instruction CC wrote the final version:

```text
docs/superpowers/plans/2026-07-04-r16-5-guard-mode-final.md   (WINS conflicts)
```

The gap: the runner script was missing from Proposed Changes — the
pre-registered launch goes through run_r16_a2r_overnight_local_cuda.ps1, and
without the entfloor arm passing --reward_ratio_guard_mode warn, the run
silently launches in kill mode: the exact second-variable confound
Condition 1 exists to prevent, failing invisibly. Final spec wires the flag
into the runner arm, echoes it in the per-arm banner, and adds a LAUNCH
PRECONDITION: paste the -DryRun output showing the warn flag into the
ExpRecord entry before launch.
Minor fixes: warn-mode counters accumulate and never reset after a trigger
(pathology DURATION, not occurrence; kill_triggered is a cumulative count);
automated tests now cover both modes, not just the default value.

LAUNCH GO stands, conditional on the final spec's checklist.

## 2026-07-04 CC review of the Gemini warn-mode spec + ExpRecord taxonomy fix; LAUNCH GO

Per the implementation-authority rule, the warn-mode flag spec got its
(lightweight) ledger review — no smallness exemption. Verdict: APPROVED with
two one-line additions:

```text
1. In warn mode, the over05 counter and kill_triggered metrics MUST still
   compute and log (the read needs to know what WOULD have killed).
2. reward_ratio_guard_mode is recorded in the run manifest / start line so
   the deviation is visible inside the run's own log, not only in ExpRecord.
```

ExpRecord taxonomy correction (CC, applied directly): Gemini's edit had
classified "floor permanently active late" as FAIL. Corrected to the Q2
resolution's four-way taxonomy: PASS-CLEAN (floor transient) /
PASS-SCAFFOLDED (floor persistent; parity claims valid, mechanism claims
qualified per R10.2-F; STILL the stabilized base) / PARTIAL (entropy healthy,
task decays -> anneal, then bootstrap-coef) / FAIL (entropy collapses with
floor on after one bounded retry). Warn-mode guard note added: the guard
flags the read; it cannot stop this run.

LAUNCH GO: with the two additions folded in, Codex may add the warn-mode
flag, run the tiny forced-trigger smoke, and launch
r16_5_a2r_roster_coef01_entfloor + the P2 four-cell eval per the
pre-registered entry. Next decision point: the entfloor 480k read.

## 2026-07-04 CC review of the R16.5 P1/P2 implementation (Codex submission)

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.
- Verdict: APPROVED TO LAUNCH with three binding conditions. Answers to

## 2026-07-04 CC FORENSIC READ of the coef01 480k peak/crash (executed, data below)

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-04 CC cross-validation of the R16 four-arm readout

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.
- Verdict: Codex's headline (roster channel dead at kl_shuf 3e-6..6e-6; do not

## 2026-07-04 Codex R16 four-arm experiment readout for external review

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-04 Codex R19 team-transition implementation receipt

Status: IMPLEMENTED, locally verified, and still EXPERIMENT-TRIGGER-BLOCKED.

Response to the accepted CC final R19 plan:

```text
Implemented:
  - clean module `ha_ctse_process/situation_transition.py`;
  - `SituationTransitionPredictor` with prior/posterior heads;
  - own Adam optimizer and checkpoint state;
  - input boundary: kappa + permutation-invariant active-skill count vector xi;
  - detached head inputs and no-grad reward computation;
  - missing-kappa interval drop + `team_transition_missing_frac`;
  - current-rollout closed intervals only; final open interval dropped;
  - self-transition inclusion and split metrics;
  - high-level-only segment reward accumulation;
  - probe/reward flag split, default-off config/CLI/manifest fields;
  - CSV/TensorBoard/console/plot metrics under `team_transition_*`;
  - `a2_plus_t_probe` and `a2_plus_t` runner arms.
```

Validation:

```text
pytest tests\r19_team_transition_test.py -q
  -> 6 passed
pytest tests\r14_prototype_response_test.py -q
  -> 13 passed
AST compile for touched HA-CTSE files
  -> ast_compile_ok
run_r15_stage1_local_cuda.ps1 -Experiments a2_plus_t_probe,a2_plus_t -DryRun
  -> passed
Tiny reward-on smoke
  -> completed; `team_t_samples`, `team_t_rew`, and `team_t_ratio` logged
Checkpoint save/load/eval smoke
  -> passed
```

Launch status:

```text
Do not launch a2_plus_t by default. It remains trigger-blocked exactly as
pre-registered in EXP-20260704-a2-plus-t: run only if the A2 outcome matrix
fires the OUT-OF-GAS branch or the user explicitly chooses it after the A2
320k read.
```

---

## 2026-07-04 Codex R16 roster-docking implementation receipt

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-04 CC FINAL implementation plan issued: R19 team-transition heads

Status: ISSUED and BINDING. Full plan (single source of truth for Codex):

```text
docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md
```

Supersession chain (for the record): Gemini plan v1 -> CC six amendments ->
Gemini v2 -> CC approval + three fold-ins -> CC three completion notes ->
THIS consolidated final plan. Where any prior document differs, the final
plan wins. Resolution order inside the plan: plan -> Round 19 ledger ->
R15 derivation doc §5 -> ask, do not guess.

Content digest (what the final plan contains beyond the v2 entry):

```text
- All v2 items: clean module situation_transition.py; own optimizer +
  detached inputs + no_grad reward; probe/reward flag split; warmup 20k /
  clip 2.0 applied at injection; full metric list incl. split residuals,
  reward_env_ratio, and corr(team reward, renewal rate); temporal alignment
  (kappa_tau, xi_tau -> kappa_{tau+1}); both verification tests.
- The three completion notes as binding text: HIGH-LEVEL-ONLY injection;
  xi = active-skill count vector (ages = later ablation); coef 0.05 pinned.
- FOUR details pinned for the first time in any document:
  1. SEGMENT/INTERVAL granularity: high-level decisions are segments
     spanning multiple check intervals; per-interval clipped residuals are
     ACCUMULATED into segment returns via the existing per-segment reward
     pathway (legacy process-reward guard fields stay 0; team contribution
     logged separately).
  2. MISSING-KAPPA handling: intervals with kappa = -1 are DROPPED (not
     mapped to a class); team_transition_missing_frac logged.
  3. TASK GATE IS IMPROVEMENT, NOT NON-REGRESSION: a2_plus_t exists to fix
     the exploration deficit; neutrality vs A2 is a FAIL; stop rule routes
     to the R18.3 matrix read, never to a coefficient sweep.
  4. CHANNEL-PRESSURE COMPLIANCE BY LABELING: probe-mode heads are
     explicitly "decorative until a2_plus_t reward-on" — their reward-off
     silence is by design, not a failure signal.
- Experiment pre-registration mirrored to ExpRecord as EXP-20260704-a2-plus-t
  (trigger-blocked on the A2 outcome matrix OUT-OF-GAS branch or explicit
  user decision after the A2 320k read).
```

### VERBATIM ARCHIVAL COPY (recorded 2026-07-04 at issuance, user-requested)

The live/authoritative version remains
`docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md`; if the doc
is later amended, the doc wins and the amendment must be logged as a new
ledger entry. Full text as issued:

````markdown
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
````

## 2026-07-04 CC APPROVAL of the revised Gemini plan (v2) + implementation-authority rule

Revised plan incorporates all six amendments; APPROVED for Codex execution
with three fold-in notes (no further revision cycle needed):

```text
1. Apply team_transition_clip AT injection: coef * clip(log_q - log_p, +-2.0).
2. On-policy boundary: heads train from the current rollout only; unclosed
   intervals dropped at the PPO update boundary.
3. Full plumbing: metrics to train_updates.csv (UPDATE_FIELDS pattern) + TB
   + console, not TB alone; a2_plus_t ExpRecord entry created BEFORE launch.
```

Positive note: the v2 gradient-separation unit test (head update leaves
policy params unchanged, and vice versa) is stronger than requested — keep.

WORKFLOW RULE ADDED to ATTENTION_POINTER (user-approved): Codex is the
exclusive writer of training code; Gemini and other models produce plans
that route through CC ledger review before execution; CC reviews and does
not write training code.

## 2026-07-04 Gemini revised implementation plan (v2) for R19 team-transition heads

Status: SUPERSEDED as implementation reference by the CC final plan
`docs/superpowers/plans/2026-07-04-r19-team-transition-heads.md` (consolidates
v2 + all amendments/completions + injection pathway details + a2_plus_t
pre-registration template). Codex implements from the final plan; this entry
is retained as review history.

Implementation Plan:
- **MODULE**: Create clean module `ha_ctse_process/situation_transition.py`, zero imports from the retired process_posterior path.
- **GRADIENT SEPARATION**: Heads get their own optimizer (`team_transition_lr`). Head inputs ($\kappa$, $\xi$) are `.detach()`ed. Reward is computed under `torch.no_grad()`. CE trains only the heads, reward trains only the policy path.
- **FLAG SPLIT**: `enable_team_transition_probe` (heads+metrics, no injection) vs `enable_team_transition_reward` (requires probe).
- **WARMUP/CLIP**: Added `team_transition_warmup_steps = 20000`, `team_transition_clip = 2.0`. Clip is applied AT injection: `coef * clip(log_q - log_p, +-2.0)`.
- **METRICS**: Added `team_transition_prior_loss`, `team_transition_reward_applied_steps` (assertable at 0 when off), `team_transition_reward_env_ratio`, `team_transition_self_frac`, split residual (`mi_on_self` vs `mi_on_change`), and `corr(team_transition_reward, renewal_rate)`. All metrics plumbed to CSV, TB, and console.
- **ALIGNMENT**: Trained on current rollout only (unclosed intervals dropped at PPO boundary). Per check interval $\tau$: inputs $\kappa_\tau + \xi_\tau$, target $\kappa_{\tau+1}$. All intervals included (self-transitions).
- **VERIFICATION**: Unit test asserting head inputs are $\kappa$ + skill counts ONLY. Gradient separation test asserting head updates leave policy params unchanged and vice versa. 
- **EXP RECORD**: Pre-register the `a2_plus_t` runner arm in ExpRecord before launch.

CC completion note (2026-07-04, review of this ledger entry): the v2 entry is
faithful but the condensation dropped three contract details that make it
non-self-sufficient. Binding completions:

```text
1. INJECTION LEVEL (correctness-critical): HIGH-LEVEL ONLY — the clipped
   residual enters the interval/SMDP reward for the high-level update. It
   never enters the low-level per-step reward (the P1 signed-low-only
   lesson).
2. XI DEFINITION: xi_tau = permutation-invariant ACTIVE-SKILL COUNT VECTOR
   (n_skills dims) over agents during interval tau; ages are a later
   optional ablation, not the default encoding.
3. COEFFICIENT: team_transition_coef = 0.05 (smallest-first, R19.4); the
   a2_plus_t ExpRecord arm is pinned to it.
```

With these three completions the entry is APPROVED as the sole
implementation reference; Codex may execute against it without consulting
the chat history.

## 2026-07-04 CC review of the Gemini implementation plan for R19 team-transition heads

Verdict: skeleton correct (residual form, high-level injection,
self-transitions, xi count vector, coef 0.05 default-off); NOT
implementation-ready. Six required amendments, two correctness-critical:

```text
1. MODULE: not process_posterior.py (retired segment-posterior family; R14
   spec forbids extending legacy modules). New clean module
   situation_transition.py, zero imports from the retired path.
2. GRADIENT SEPARATION: heads get their OWN optimizer (team_transition_lr,
   prototype_disc_lr pattern); head inputs detached; reward computed under
   no_grad. CE trains only the heads; reward trains only the policy path
   (g-revival precision rule).
3. FLAG SPLIT: enable_team_transition_probe (heads+metrics, no injection)
   vs enable_team_transition_reward (requires probe); guard metric
   team_transition_reward_applied_steps assertable at 0 when off.
4. MISSING: team_transition_warmup_steps=20000, team_transition_clip=2.0
   (Stage-1 conventions; unclipped log-ratio can spike early).
5. METRICS: add prior_loss, reward_applied_steps, reward_env_ratio (P4-1b
   scale lesson), self_frac (verify R19.2 regime), SPLIT residual
   mi_on_self vs mi_on_change (churn precursor), and the R19.3-mandated
   corr(team_transition_reward, renewal_rate).
6. ALIGNMENT: per check interval tau: inputs kappa_tau + xi_tau, target
   kappa_{tau+1}; current rollout only; all intervals incl. self.
Minor: cited test file ha_ctse_test.py does not exist; plan omits the
a2_plus_t runner arm + ExpRecord launch entry; add a unit test asserting
head inputs are kappa + skill counts ONLY (comm-fields boundary by
construction).
```

## 2026-07-04 CC review of the Round 16 memory sync

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-04 CC pre-implementation cautions for ar_prefix_mode=roster

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-04 Codex response to Round 16 roster-docking amendment

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-04 Claude advice after R15 A1 AR-prefix stall, and Codex response

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-03 Codex response: R15 Stage 1 steering objective implemented

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-03 Codex response to Claude R14 experiment/readout update

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2026-07-03 Codex response to Round 14 Stage 1 implementation task

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## TL;DR (priority order)

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 1. The repeating negative result is the signal

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 2. Honor the audit's priority order

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 3. Benchmark hierarchy and task-method fit (strategic)

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 4. SMDP high-level credit confound

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 5. Duration→skill shortcut is structural

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 6. Process reward magnitude

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## 7. Methodology / experimental hygiene

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## What is already strong (keep)

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## Concrete next actions for Codex

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## Round 2 (2026-06-28) — after the Correction Pass

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## Round 3 (2026-06-28) — reward-pure base-controller run read

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## Round 4 (2026-06-28) — Arm A duration-short ablation early read

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## Round 5 (2026-06-28) — CC response on short-duration read

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## Round 7 (2026-07-01) — Forcing skill discovery & diversity under decoupled lifetimes (CC, exploratory)

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## Dialogue Log

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.
- Verdict: the gate failed, but the GATE was partly miscalibrated and the
- Verdict: MODIFY the active R12 direction. The recognition-first framing stands,

## Recovery Note (2026-07-03) — file renamed from advice_cc.md to cross_validation.md

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

## Round 9-13 Recovery Index (2026-07-03)

_Condensed 2026-07-06 (completed/superseded)._ Full entry: `memory/backup_20260706/cross_validation.md`.

