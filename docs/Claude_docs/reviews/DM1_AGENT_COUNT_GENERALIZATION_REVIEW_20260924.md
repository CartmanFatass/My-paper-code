# Independent review: DM1 `agent_count_generalization` (B01–B15), 2026-09-24

Reviewer stance: demanding MARL reviewer who reads code. Sources read: `docs/research/RESEARCH.md`
(DM1 rows and plan), the direction `NOTES.md` (all fourteen "complete" sections, the B11 prospective
entry, the B15 adoption, implementation-acceptance and first-admission entries; Pro transcripts skimmed
for criticisms only), `CLAIM_bounded_count_transfer_20260923.md`, run directories under
`runs/agent_count_generalization/`, the direction code on branch `codex/agent-count-generalization`
(`experiments/candidates/agent_count_generalization/…`) and the core learner/env files it calls
(`hmasd/agent.py`, `hmasd/networks.py`, `hmasd/r_mappo_utils.py`, `hmasd/baselines.py`,
`envs/pettingzoo/uav_env.py`, `envs/pettingzoo/scenario1.py`, `envs/pettingzoo/env_adapter.py`,
`configs/config_1.py`). Line numbers refer to that worktree. "Verified" means I recomputed the number
from panel/summary files with my own script; "inferred" means a reading of code or notes.

## Verdict

The record-keeping is exemplary and every headline number I recomputed (B01, B11, B12, B13, B14)
matches NOTES to the printed digits, but the science is much weaker than the volume of documentation
suggests. After 21 training fits and six zero-fit replays, the direction has one prospectively matched
comparison (B14, n = 1 per arm) showing a final N8 gap of +0.0714 J / +5.28 served users, sitting on
top of a development history in which the same nuisance channel (raw-Gaussian entropy / action
saturation) moved comparable gaps by ±0.1 J with a sign that flipped between training seeds
(B04→B05, B11→B12). Two structural problems dominate: (i) SET is not the natural "H6 minus skills"
control, so the package gap cannot be attributed to skills, coordination or intrinsic rewards rather
than to the different actor input architecture; (ii) both arms train with an unbounded raw Gaussian
whose samples are clipped only at execution, with 60–83 % of training coordinates saturated, which is a
non-standard and biased policy-gradient regime that no reviewer will accept as the task's action law.
The gap is also as large at the trained N6 as at N8, so the "count transfer" framing is not what the data
show. B15 (already admitted on the branch at 2026-09-24T02:02Z, first cell `b1_h6`) is correctly
pre-registered and its analyzer is arithmetically right, but with n = 3 and df = 2 its joint rule has
roughly a 30–40 % chance of passing even if the B14 effect is real; the most likely outcome is
"inconclusive". Not publishable as an HMASD result in its current form.

## 1. Evidence chain B01 → B15

J = .7·coverage + .3·quality − height penalty (native, per step); S = served users per step (of 50).
"n" is independent training instances per arm. Numbers marked (v) were recomputed by me from
`summary.json`/`panel_*.json`; others are taken from NOTES.

| Batch | Comparison | n / arm | Panels | Headline (H6 − SET unless stated) | Adverse / contrary | DM conclusion |
|---|---|---|---|---|---|---|
| B01 | H6 vs SET, N6-trained, **raw unclipped execution** (actions ×30 m/s, out of box) | 3 / 3 (independent seeds, not paired) | N4/6/8 × 16 worlds, fresh worlds per stage | J: N4 +0.0217, N6 +0.0440, N8 +0.0452 (v: per-seed N8 H6 .466/.428/.441 vs SET .403/.378/.418); est. SE ≈ .016–.018 | Rollout-0 favours SET; one H6/SET pair negative at rollout 30; both arms decline late; σ grows 1→2.7 (H6) / 4.0 (SET); action law later found false (probe: 60 m move from a=2) | Retain bounded exploratory result; then correct the action-law premise |
| B02 | 6 B01 policies, raw vs clipped deployment | 0 fits | 3 N × 16 new worlds | Clipped gap N4 +0.0299, N6 +0.0416, N8 +0.0547; raw coordinate violations 63.9 % (H6) / 49.4 % (SET) | 86/288 paired worlds worse under clip; N4/N6 gap attenuates | Over-range execution not needed for the gap |
| B03 | 2×2: H6/SET × raw/clip training, clipped deployment | 1 per cell | 3 N × 16 | G_clip: N4 +0.0649, N6 +0.0958, N8 +0.161; clip-training **hurts** SET (B_SET unseen −0.0374), helps H6 (+0.0319) | Interaction I = −0.0693 (prediction failed); σ_clip 3.2 (H6) / 5.0 (SET) | Clip alone does not rescue SET; entropy incentive suspected |
| B04 | λ_l = 0 vs .05 (B03 clip controls), H6 and SET | 1 / 1 | 3 N × 16 | SET λ0: N8 +0.110, N6 +0.0523, N4 +0.0009; H6 λ0: N8 −0.0282. Gap at λ0 only N8 +0.0227, N4 +0.0728 | Stage-30 SET λ0 negative at all N; H6 worse | λ0 useful for this SET instance; not adopted |
| B05 | SET λ0 vs .05, new seed 953201 | 1 / 1 | 3 N × 16 new worlds | E_U = **−0.0456** (N4 −0.0505, N6 −0.0604, N8 −0.0407) | Full sign reversal vs B04 | Do not promote λ0 |
| B06 | Panel exchange, 2 policy pairs × 2 panels | 0 fits | 12 diagonals reproduced exactly | Sign follows the trained pair (R_U +0.0829), panel effect small (C_U +0.0183) | Panel B lowers d for both pairs | Reversal is a training-instance effect |
| B07 | New H6/.05 (952201) vs reused B05 SET/.05 (953201) | 1 / 1 (reused) | 3 N × 16 | N4 +0.0787, N6 +0.141, N8 +0.152, U +0.115 | Adverse N8 world 1545810 −0.0744 J / −7.16 users; H6 already ahead at rollout 0 (U +0.146) | Retain; "initial-policy rival" |
| B08 | Initial vs final of B07/B05 policies | 0 fits | 3 N × 16 | Both learn: I_H +0.216, I_SET +0.245 (U); D0 +0.145 → D45 +0.115 | SET's J increment larger; SET loses in one world | Final lead is not a learning-increment effect |
| B09 | Count scalar clamped to .75 at N4/N8 deployment | 0 fits | 6 panels | SET N8 +0.0150, N4 −0.0045; H6 ≈ 0 (+0.0006) | N4 harm; 1545810 persists | Not a uniform repair |
| B10 | Opening skill labels replayed for the whole episode (H6 B07) | 0 fits | 6 panels | L: N4 +0.0042, N6 +0.0039, N8 +0.0092 (42/48 worlds) | Losses to −0.0666 J / −5.30 users; all team labels = 3, individual mostly = 5 | Ongoing reassignment not needed for these weights |
| B11 | SET T8 (N8-trained) vs T6, seed 963201 | 1 / 1 | N8, N6 × 32 new worlds (1645xxx) | (v) Δ8 = +0.0197 J / +3.02 users (20/32); Δ6 +0.0029 | Height +21 m; 12 N8 loss worlds | Bounded positive |
| B12 | Same design, seed 963401, same panel | 1 / 1 | as B11 | (v) Δ8 = **−0.0421** / −1.13 users (4/32); Δ6 −0.0645 | Full reversal on identical worlds | Drop T8 recipe |
| B13 | Retained H6s (B03 clip = H1, B07 = H2) vs B11 T6 (S1), B12 T6 (S2) | 0 fits | 8 panels on 1645 worlds | (v) N8: H1−S2 +0.0460 / +3.65 users (25/32), H2−S2 +0.0684 / +4.78 (31/32); N6 +0.0236 / +0.0479 | H1−S2 loses J in 7/32; N6 losses to −0.0842 J | Gap survives stronger ordinary control |
| B14 | Fresh H6/.05 vs fresh SET/.05, seed 974201, byte-identical exogenous reset scenes, initial + final panels | 1 / 1 | N8, N6 × 32 (1645 worlds, already read) | (v) N8: D0 −0.0204 → D45 **+0.0714 J / +5.28 users** (31/32); N6 D45 +0.0499 / +2.70 (31/32) | Quality lower in 17/32, height cost higher in 20/32 at N8; 4 J-or-S loss worlds; H6 σ 3.2 vs SET 4.7 | Fresh learning reproduces a bounded benefit → confirmation |
| B15 | 3 blocks × (H6, SET), seeds 994101–3, unread panels 1945800–31 / 1945600–31, initial + final | 3 / 3 (planned) | N8 primary, N6 secondary | Rule: df = 2 t-interval lower J > 0 AND lower S > 1 user | — | Adopted; **first cell admitted 2026-09-24T02:02Z** (branch commit `bf586f17`; main has no B15 run dir yet) |

Aggregate cost so far: 21 training fits (B01 6, B03 4, B04 2, B05 2, B07 1, B11 2, B12 2, B14 2) ≈ 7.56 M
training team steps, six zero-fit replays, ~19 h of scientific command wall; B15 adds 6 fits / ~6.9 h.

Three things stand out from the chain. First, only B14 is a matched fresh pair; B03/B07/B13 reuse
policies and all evaluations from B11 onward use the same 64 development worlds. Second, the N6
(trained-count) gap is consistently as large as the N8 gap (B14 +0.050 vs +0.071; B13 +0.024/+0.048 vs
+0.046/+0.068; B07 +0.141 vs +0.152; B01 unseen−N6 contrast −0.011). Third, the between-instance
spread on the 1645 N8 panel is large: H6 final J = .452 / .474 / .418 (SD .028), SET = .340 / .405 /
.347 (SD .036), giving an implied SD of a block difference ≈ .046 J (v).

## 2. Code and protocol findings

**F1 — SET is not the natural flat control; the "skills" claim is confounded with actor input architecture. Severity: blocker for any mechanism claim, major for the package claim.**
`models.py:84-156` (`SetActorBase`): the SET actor consumes current own obs (104) + held 133-d
count-adapted global state + held joint observations of all agents (n·104) + ego one-hot, pooled with
mean/max and a constant `count = n_agents/8` (line 152), fused through a 721-wide layer. The snapshot is
refreshed every k = 10 steps (`agent.py:1290-1314`, `configuration.py:163-167`). The H6 low-level actor
(`networks.py:1439-1461`) consumes only the 104-d local observation plus a FiLM modulation of a
6-way skill one-hot. So the two arms differ in (a) skill coordinator + discriminators + intrinsic
rewards, and (b) whether the actor sees a stale global snapshot at all. The control that isolates (a) —
the same local-obs actor with `n_Z = n_z = 1`, `λ_D = λ_d = λ_h = 0`, no coordinator/discriminators
(exactly `apply_algorithm_config("mappo")` in `baselines.py:127-148` with
`use_central_snapshot_in_flat_actor = False`) — was never run in fourteen batches (grep of NOTES finds
no local-only/IPPO arm). A local-obs shared actor is also trivially count-invariant, whereas SET's actor
suffers an input-distribution shift at N8 (8 pooled rows, count scalar .75→1.0; B09 showed SET, not H6,
responds to that scalar). The DM's "matched information" argument justifies giving the *coordinator*
route global state; it does not justify handing the *low-level actor* a global snapshot. Every reviewer
will ask for the local-obs flat arm first.

**F2 — Action law: unbounded raw Gaussian, clipped at execution, PPO on raw log-probs, entropy bonus on the raw Normal. Severity: major (protocol validity).**
`r_mappo_utils.py:73-95` (`DiagGaussian`): `logstd` is an unconstrained bias initialised at 0 (σ = 1),
`forward` samples the raw Normal, `evaluate_actions` (lines 97-109) returns raw log-probs and raw
entropy (summed over 3 coordinates). Execution clips to [−1, 1] only in the runner
(`action_law_b03/runner.py:74-78`, inherited by B07–B15). `agent.py:1115` sets the low-level entropy
coefficient to `lambda_l = .05` with annealing/targets off (`config_1.py:166`). Consequence, verified
from `s1_fresh_learning_b14_*/training.jsonl` (last rollout): raw attempted movement per UAV-step 179 m
(H6) / 231 m (SET) versus 48 m executed; mean raw excess beyond the bound 2.09 / 2.93 per coordinate;
final σ = [3.22, 3.16, 3.14] (H6) vs [4.76, 4.71, 4.26] (SET); NOTES B03/B04 record 60–83 % of
training coordinates saturated. The policy gradient of a clipped Gaussian that ignores the clip is
biased and high-variance (Fujita & Maeda, ICML 2018, "Clipped Action Policy Gradient"); the executed
training behaviour is essentially bang-bang while evaluation runs the deterministic mean (fresh
`fresh_learning_b14/runner.py:380-398`, `bounded_confirmation_b15/runner.py:389-400`). Both arms suffer,
but SET's σ is ~50 % larger, so its gradient is more corrupted. The B04/B05/B06 results show that this
channel alone moves the H6−SET gap by ±0.1 J with instance-dependent sign, i.e. by more than the
claimed effect. A squashed policy already exists (`TanhDiagGaussian`, `r_mappo_utils.py:112-164`) and is
unused. The DM correctly documented this and correctly declined to change law mid-stream, but a
confirmation batch that freezes a non-standard, biased action law confirms a result reviewers will
consider an artefact of that law until shown otherwise.

**F3 — The H6 coordinator is not count-invariant; "HMASD at N8" is an untested extrapolation of the coordinator. Severity: major for the framing, minor for the outcome.**
`networks.py:146-166` (`PositionalEncoding`, sinusoidal by token index) is added to the entity sequence
[state, obs_1, …, obs_N] in `SkillCoordinator._build_entity_sequence` (`networks.py:748-753`) and again
over the autoregressive decoder prefix in `SkillDecoder` (`networks.py:533-640`). At N8 the tokens at
positions 7–8 and decoder prefixes of length 7–8 were never seen during N6 training. `models.py:63-81`
(`SharedValueHeads`) and the `StateSetEncoder` substitutions (`models.py:213-225`) only prevent index
errors and give count-invariant *state* features; they do not make the coordinator invariant. That the
result survives anyway is consistent with B10 (replaying the opening labels changes J by +0.009 at N8)
and B07/B10 (that instance used team label 3 and individual label 5 almost exclusively): the coordinator
is doing little. B14's H6 does use two team and four individual labels (verified: `panel_stage45_n8`
team counts [0,0,0,0,817,783], individual [2892,161,4657,119,2848,2123]), so skill usage varies by
instance and was never related to the size of the gap.

**F4 — Neither arm is tuned; SET's only tuning exposure is λ_l ∈ {.05, 0}, which reversed. Severity: major (constitution §8.2 "competent matched-information baseline").**
All hyper-parameters are the HMASD defaults (`config_1.py:146-166`: lr 1e-4 everywhere, 15 PPO
epochs, 4 minibatches, γ .99, clip .2). No learning-rate, entropy, architecture-width or
minibatch search was run for SET (or H6). Declaring exposure satisfies the letter of §8.2; it does
not satisfy a reviewer.

**F5 — Reward scaling R/N: consistent, not arm-specific. Severity: minor.**
`uav_env.py:321` gives each agent `global_reward / n_uavs`; `env_adapter.py:254` averages, so the
learner sees R/N (R/6 in training); `runner.py:164-172, 251` recovers native J = N·return/500 and
asserts the component identity. Correct. It only matters for B11/B12, where T8 trained on R/8 — a
reward-scale confound the DM acknowledged.

**F6 — Evaluation isolation: correct. Severity: none.**
`strict_sync` (`models.py:293-315`) copies modules/normalizers strictly and resets per-lane recurrent
state; `evaluate_panel` (`runner.py:253-254`, `bounded_confirmation_b15/runner.py:363-372`) digests
parameters before/after and hooks optimizers; skills use argmax and actions the mean under
`deterministic=True` (`agent.py:3201-3268`, `networks.py:1310-1316`, `r_mappo_utils.py:91-92`). B06 and
B13 reproduced historical panels bit-exactly. I found no leakage.

**F7 — B15 statistics: arithmetic right, design under-powered. Severity: major (design).**
`bounded_confirmation_b15/analysis.py:64-77`: sample SD with ddof = 1 over the three block means of
D45, half-width 4.3027·SD/√3 = 2.48·SD, strict `lower > threshold`; the AND of two one-sided .025
tests (lines 238-240) is a valid, conservative joint rule. Pairing within a block is only through
common exogenous reset scenes (lines 201-203); initialisations, sampler streams and endogenous
trajectories differ, so little variance is removed. Using the observed between-instance spread on the
1645 panel (SD_diff ≈ .046 J, ≈ 2.36 users), a Monte-Carlo of the rule with true effects equal to
B14 (+.071 J, +5.28 users, ρ = .9) gives P(J passes) ≈ .33, P(S passes) ≈ .41, P(joint) ≈ .27; with the
3×3 grid mean (+.084 J) it is ≈ .4. No effect size or power was pre-registered; the DM's own note that
"three positive values can be inconclusive" is correct and, on these numbers, the modal outcome.

**F8 — Adapter/state width. Severity: minor.** `adapter.py:11-13, 27` fix `MAX_UAVS = 8`, so N > 8
cannot be tested without changing the state contract; `StateSetEncoder` (`models.py:51, 59`) and
`SetActorBase:152` feed a count scalar constant at .75 through all of training.

**F9 — SET carries an unused 3.85 M-parameter coordinator and runs 2,250 coordinator forwards per fit
(`models.py:210`, B14 inference counts). Severity: minor;** harmless for outcomes, but it inflates
"SET compute" and should not appear in any cost comparison.

**F10 — Process. Severity: minor.** The brief calls B15 "proposed"; the branch shows it admitted
(NOTES "B15 first fixed cell admitted", worktree commit `bf586f17`; run dir
`s1_bounded_confirmation_b15_b1_h6_s994101` with manifest, launch SHA `e0a20add`). Main has not been
updated. Any "before launch" change is now an amendment to a running frozen batch and should not be made.

## 3. Scientific assessment

**Is the claim well-posed?** Yes, narrowly: a conditional-mean (over training-program realisations)
difference on a fixed unread 32-world N8 panel between two fully specified packages, with a
pre-registered rule and a practical threshold. The DM has been scrupulous about what it does not claim.
But the *name* of the claim is wrong. The gap is not a count-transfer effect: it is present with the
same magnitude at the trained count (N6) in every batch, and the transfer loss N6→N8 is similar for both
arms (B14: H6 .514→.418 = −.096, SET .464→.347 = −.117). A reviewer reading "bounded count transfer"
will expect an arm-by-N interaction; the data show a main effect of package. The direction's actual
question ("service capability and generalization cost at unseen N") is answered only descriptively:
both packages lose ≈ 0.1 J from N6 to N8 and neither has been compared to an N8-trained reference of
its own kind except SET (B11/B12, which reversed).

**Is the confirmation design adequate given B11/B12?** No. B11→B12 (identical recipe, identical
worlds, one seed change) reversed a +.020 J effect to −.042; B04→B05 reversed +.056 to −.046. Those are
block-to-block swings of .06–.10 J in the same family of learners, i.e. larger than the .05–.07 J
effect B15 must resolve. Three blocks with a df = 2 interval cannot resolve an effect of that size
against that noise; the honest probability that B15 is inconclusive is 60–70 %. The design also freezes
the two things a reviewer will most want changed (action law, control arm), so even a pass leaves the
attribution problem intact. A pass would establish "this H6 package beats this SET package on this
task at 360k steps"; it would not establish that hierarchy, skills, or coordination are responsible.

**What B09 and B10 say about mechanism.** B09: clamping the explicit count scalar changes SET
(+.015 J at N8, −.005 at N4) and barely touches H6 — the H6 actor never sees a count scalar, so count
extrapolation is not where H6's advantage comes from. B10: replaying the opening skill labels for the
entire episode *slightly improves* H6 (+.009 J at N8), with labels that were nearly constant (team 3,
individual 5). Together with B08 (both arms learn; SET's increment is larger) and B14's initial
ordering (SET ahead at rollout 0, H6 ahead at 45), the most parsimonious explanation is not
"hierarchical skill discovery" but: a local-observation recurrent actor with a near-constant FiLM
offset, trained under smaller action noise (σ 3.2 vs 4.7) and with intrinsic-reward shaping,
outperforms a wide central-snapshot actor trained under larger noise in a saturating action regime. The
skills-off control (F1) and the squashed-policy control (F2) would each take one batch to test and
would settle this; neither is scheduled.

**Selection exposure.** The retained H6 recipe (clip, λ = .05, k = 10, 45 rollouts) and the SET recipe
were selected after seeing B01–B13, and the 1645 worlds were read in B11–B14. B15's new worlds address
world selection; they cannot address recipe selection. The DM says this plainly.

## 4. Literature position

HMASD (Yang, Yang, Lu, Zhou & Li, NeurIPS 2023) learns a team skill and per-agent skills with a
transformer coordinator every k steps, a FiLM-conditioned low-level policy, and two discriminators
supplying intrinsic rewards; it was evaluated on sparse-reward cooperative benchmarks and makes no
variable-N claim. The direction's H6 is a faithful-in-spirit re-implementation with count-stable
state encoders bolted on; its coordinator keeps index-based positional encodings, which the
variable-N literature explicitly removes. The standard approach to unseen team sizes is an
entity-based, permutation-invariant policy: UPDeT (Hu et al., ICLR 2021) and REFIL (Iqbal et al.,
ICML 2021) generalise across agent counts by attention over entities with masking and no positional
index; MAT (Wen et al., NeurIPS 2022) and SMACv2 (Ellis et al., 2023) supply standard variable-composition
benchmarks. Against that background: (a) H6's low-level actor is count-invariant only because it is
local; (b) SET is an idiosyncratic central-snapshot actor rather than either the standard local MAPPO or
an entity-attention actor; (c) the task is a bespoke UAV-coverage scenario with an in-house objective J.
A reviewer will ask for a UPDeT-style flat baseline, a local-obs MAPPO/IPPO baseline, ≥ 5 seeds, and
at least one standard variable-N benchmark (MPE spread/tag with variable N, or SMACv2). Without those,
the result does not compete with the variable-N literature; with them, the interesting question
becomes whether skill conditioning adds anything over entity attention, which the present design cannot
answer.

## 5. Recommendations

**Do not amend B15**; it is running and frozen. Let it complete, report it by its rule, and expect
"inconclusive". Pre-register now (in NOTES, before any B15 final panel is read) one secondary analysis
that costs nothing: the between-arm difference of transfer loss (J6 − J8 per block) and the N6 gap, so
that the count-transfer question is at least addressed descriptively with the same six fits.

**Next experiments, in priority order.**

1. *B16 skills-off control (3 fits, ≈ 3.5 h).* H6 architecture with `n_Z = n_z = 1`, λ_D = λ_d = λ_h = 0,
   no coordinator/discriminator updates, local-obs actor, `use_central_snapshot_in_flat_actor = False`
   (i.e. `apply_algorithm_config("mappo")` without the SET base). Run one per B15 block with the same
   learning seeds, exogenous lane bases and the B15 panels so it pairs with both B15 arms. Prediction if
   skills matter: H6 − flat > 0 with the same sign pattern as H6 − SET. Prediction if F1 is right:
   flat ≈ H6 > SET. This single batch decides whether the direction has an HMASD result at all.
2. *Squashed-policy replication (6 fits, ≈ 7 h).* Both B15 arms with `TanhDiagGaussian`
   (`continuous_action_distribution = "tanh_gaussian"`, entropy on the squashed sample), same seeds and
   panels. Prediction if the gap is genuine: it survives with σ no longer saturating. Prediction if
   F2 is right: the gap shrinks toward the B04 λ0 level (+.02 J at N8) or reverses. Run this before
   any mixed-N or N > 8 investment.
3. *Only if 1 and 2 hold:* raise the state contract to MAX_UAVS = 12, test N10/N12 with fresh panels,
   and port the two winning arms plus an entity-attention flat actor to MPE variable-N spread (5 seeds).
   Cost ≈ 15–20 fits; this is the minimum a venue would require.

**Stop.** Zero-fit replays on the 1645 development panel (B06/B08/B09/B10/B13 style) — they cannot
increase n and have now generated more text than evidence. Entropy-coefficient variants (B04/B05 showed
the response is seed-dominated). The N8-trained SET recipe (B11/B12). Per-batch Pro rounds: ~63 % of a
1 MB notebook is adviser transcript, and the material advice (fresh seeds, fixed panels, ordinary
control strength) was available from constitution §8 alone.

**Publishability.** Not publishable as an HMASD/variable-N contribution now: bespoke task, n ≤ 3, an
effect of the same size as documented seed-to-seed reversals, a non-standard biased action law, an
untuned and non-standard control, and no skills-off ablation. The provenance and pre-registration
discipline are genuinely strong and would make a clean negative or bounded result credible, but
credibility of the bookkeeping is not a scientific contribution. If B15 passes *and* recommendations
1–2 both hold, a workshop-length empirical note ("skill-conditioned local actors transfer across team
size in a UAV coverage task") is defensible; a main-track paper would additionally need item 3.
