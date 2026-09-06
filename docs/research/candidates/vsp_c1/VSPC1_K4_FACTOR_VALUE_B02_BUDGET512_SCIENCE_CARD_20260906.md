Claim tested: Within one fresh training instance (seed 3), does the FACTOR-versus-GENERIC native-return difference observed at the original 128-update budget shrink, persist or reverse when both arms continue the same learning scheme to 512 updates?
Binding structure: (b) temporal abstraction or termination; the same exogenous periods constrain held service actions and their renewal credit.

# VSP-C1 K4 B02 — budget dependence 128→512, one fresh seed

Class: **B/EXPLORE**. Rung label: `VSPC1-K4-FACTOR-VALUE-B02-BUDGET512`. Selected by the
complete Convergence decision of 2026-09-05 (r02, `PRO_FINAL`; archive
`pro_packets/20260905_three_seed_convergence_r02/archive/RESPONSE.md`, intake
`VSPC1_K4_THREE_SEED_CONVERGENCE_R02_INTAKE_20260906.md`). It is a new outcome-informed B
on the unchanged host, not a rerun or rewrite of B01 seeds 0–2, not a C freeze, not a
stability certification and not a gate for later MARL work. Frozen by the hub as DM on
2026-09-06 before any implementation or run.

## 1. Inherited science and the exact change

The [B01 card](VSPC1_K4_FACTOR_VALUE_B01_SCIENCE_CARD_20260905.md) §§1–9 and the
[seed 1/2 card](VSPC1_K4_FACTOR_VALUE_B01_SEED12_SCIENCE_CARD_20260905.md) supply the host,
population, treatment/comparator, RNG, learner, evaluation and engineering meanings, all
unchanged: two fixed roles, focal learner with a public fixed partner, H = 6, p ∈ {2, 6},
τ ∈ {2, 4}, c ∈ {0, 1}, eight contexts at weight 1/8 in training and evaluation, partner
b_t = c for t < τ else 1 − c, focal choice a ∈ {0, 1} at t = 0, p, 2p, … < 6, return
R = (1/6) Σ_t 1[a_t = b_t]. FACTOR: `[s, onehot(a)]` 6→16 tanh→4 dotted with a 2×4 period
embedding, 188 parameters. GENERIC: `[s, onehot(a), onehot(p)]` 8→19 tanh→1, 191
parameters. Common state (2c − 1, τ − 3, t/6, ℓ_t). CPU FP32, Xavier gain 1, zero bias,
embedding std 0.5; no loaded model, label or analytic policy.

The change is the complete training scheme: the original first-128 schedule followed by 384
low-exploration cycles, in one continuous instance. Per cycle 32 real episodes (four per
context, permuted), one full-batch update; lr 0.01, Adam (0.9, 0.999), ε 1e-8, weight decay
0, global clip 5; segment credit g = Σ_segment r_t / 6, target y = g + (1 − done)
max_a Q_old(s_next, a, p) computed before the update under stop-gradient, terminal
continuation 0, γ = 1; loss = mean over 32 episodes of the per-episode mean renewal error,
period weights unchanged; no replay, auxiliary task, extra epoch or hidden update.

**Exploration schedule (frozen).** Cycle j = 1…128: ε_j = 1 − 0.9 (j − 1)/127 (identical to
B01). Cycle j = 129…512: ε_j = 0.1. Exploratory actions uniform; greedy ties to 0. The 127
denominator is not changed to 511; nothing is reset, restarted or selected at cycle 128; the
128 point is a read-out inside the same instance.

**Seed and streams.** Exactly two invocations, serial: FACTOR seed 3, then GENERIC seed 3.
Fresh model and Adam state each. Existing seed formulas at seed 3: NumPy context `[3, 101]`,
exploration `[3, 102]`; torch FACTOR dense/embedding 3201/3202, GENERIC dense 3301. Each arm
follows its own trajectory; fixed [episode, tick, draw] slots keep the pairing of random
slots without letting one arm's outcome shape the other's data. Evaluation is greedy and
deterministic and consumes no training stream.

This treatment cannot separate data volume, optimizer steps, exploration annealing or wall
budget as causes; separating them would be a different object.

## 2. Measurements (all prespecified)

At u = 0, 16, …, 512 (33 fixed states) run eight free legal-policy episodes, one per context,
no learning, no exploration; J_a(u) is the eight-context mean.

| Quantity | Definition |
| --- | --- |
| Primary endpoint | ΔJ_512 = J_FACTOR(512) − J_GENERIC(512); both J_512 reported |
| Full-curve support | AUC_a(0:512) = [0.5 J_a(0) + Σ_{k=1}^{31} J_a(16k) + 0.5 J_a(512)] / 32, both arms and the difference |
| Same-instance original-budget read-out | J_128 and AUC_a(0:128) = [0.5 J_a(0) + Σ_{k=1}^{7} J_a(16k) + 0.5 J_a(128)] / 8 (the seed-3 prefix, not an extra seed) |
| Budget response | D = ΔJ_512 − ΔJ_128, with L_F = J_F(512) − J_F(128) and L_G = J_G(512) − J_G(128), so D = L_F − L_G |
| Late-segment description | AUC_a(128:512) = [0.5 J_a(128) + Σ_{k=9}^{31} J_a(16k) + 0.5 J_a(512)] / 24 |

Also retained: J_0, J_512 − J_0, all 33 points, raw context results by p, τ, c. The three AUC
windows are different estimators and are never pooled. The 128 and 512 points belong to one
training path; their correlation is the nature of this paired observation, not two samples.
The seed-3 0:128 prefix may be listed beside seeds 0–2 with its origin stated; the new
0:512 AUC is not merged with the old 0:128 AUC, and no 512 point enters the old three-seed
mean. B01's readings, initial values and adverse observations stay as they are.

MEI: descriptive absolute 1/12 (half a service step per six-step task); not a launch,
significance, equivalence or continuation threshold. D and the late AUC have no winning line.

## 3. Reading rule (written before the data; Pro section 5, applied in order)

Check dependencies first; then read the primary endpoint, full AUC, initial values and both
arms' changes jointly; never keep only the favourable metric when they conflict.

| Observation | Bounded reading | What it changes next |
| --- | --- | --- |
| A primary dependency (reward, information, legal holds, updates, primary evaluation) is damaged, or an invocation does not complete | Report only independently trustworthy narrower facts; no win/loss or mechanism polarity on the damaged dependency | Keep partial outputs and actual exposure; return the concrete gap. No replacement seed, model change or automatic continuation. |
| Seed 3's positive gap holds or widens at 512, not only through GENERIC regressing, and FACTOR shows visible late absolute improvement | A favourable parameterization signal persists under added learning in this instance; if the full curve disagrees, write "endpoint favourable, whole-curve cost not gone" | Keep this model/optimizer combination as a candidate worth study; the next comparison is "is an independent 512 instance worth repeating" or a named new host question, not running this instance to satisfaction. Nothing is auto-authorized. |
| 128 point adverse, 512 point favourable | The original-budget ordering reverses inside this instance under the scheme; the short budget does not represent this instance's long budget | Drop any budget-independent verdict on the parameterization; the longer-budget signal may enter a later bounded comparison; the historical negative seed is not erased. |
| 128 point favourable, 512 shrinks to zero or negative, or GENERIC improves more late | Limits the case for extending the early advantage; proves neither equivalence nor general negative transfer | Stop extending the unchanged combination for a larger endpoint; keep the short-budget evidence; the automatic-extension path for this model ends. |
| Both arms nearly flat late, or persistent context errors with no new separation | This added budget gave no useful resolution; not convergence, not an upper bound, not "never learns" | Stop the budget path at 512; no automatic 1,024/2,048. A tabular control or new host later needs its own stated decision value. |
| Both arms reach the host's analytic reference with no useful curve difference | The current toy has no remaining room to compare these parameterizations | Stop repeated investment in the public-plan toy; keep positive and negative results; K4 is not closed; no analytic-reference census is needed to describe this. |
| Only a GENERIC decline widens the endpoint, or endpoint / full AUC / late reading conflict | Native relative performance stands as measured, but FACTOR did not "learn faster"; no metric is picked to declare a winner | Do not promote a cross-period sharing-efficiency narrative; a comparator-representation question may motivate the named replacement later; no tuning or extra control becomes a repair prerequisite. |

Small valid values keep their magnitude and sign. One instance does not test the training
population's budget interaction; "four seeds" promotes nothing to C.

## 4. Exposure, cost and stop

Per arm: 16,384 training episodes (2,048 per context), 98,304 training joint native steps,
32,768 renewal samples (24,576 short-period, 8,192 long-period), 512 Adam updates over 64-row
batches, 33 evaluation checkpoints, 264 evaluation episodes, 1,584 evaluation joint steps,
528 legal evaluation decisions; 99,888 joint steps per arm, 199,776 for the pair, 1,024
updates. Against one original-budget pair this is 149,760 more joint steps and 768 more
updates; the pair exceeds the 150,048 steps of all six B01 invocations. Nominal Σ lr = 5.12
(1.28 through cycle 128); record ‖θ0‖, ‖θ128‖, ‖θ512‖ and the displacements θ0→θ128,
θ0→θ512, θ128→θ512 as small in-run readouts; no checkpoint-restore platform, no displacement
gate; seed-3 displacement is unknown, not zero and not copied from B01.

Dominant work per arm: init + 512 × [32 episodes × 6 steps rollout + one 64-row update] +
33 × 8 episodes × 6 steps evaluation + checks and publication; serial arms, own model and
optimizer each; two-action scoring is learner work; no policy candidates, trajectory search,
solver, smoke or generalization set. B01 measured 1.76–3.95 s per complete 128-update
invocation (17.00 s wall, 14.47 CPU-s for six); 7.04–15.8 s per arm is a conditional linear
scenario, not a measurement or bound; init, I/O, start/exit, contention and node state are
unmeasured.

**Cap: 2,700 s per complete arm invocation** (imports, init, training, all evaluations,
checks, publication readback, exit); the 5,400 s cap sum is neither an estimate nor an
elapsed target. Report the sum of complete invocation walls, CPU work and first-to-last
elapsed separately. CPU FP32, one scientific process, one compute thread, in-process batch
32; remote-first on `wsl_4070` at the exact pushed sha in a detached worktree under
`agent-task`; a fresh physical/effective ≥ 4 GiB admission on the executing node immediately
before each invocation. Stop at the cap or an actual technical failure, keep completed
exposure and outputs, never skip evaluation or publication to appear complete, never switch
seed or budget automatically. Budget for this object: the two invocations; nothing carries
over.

## 5. Predictions on record (before any run)

- **Pro (r02, working prediction):** with more same-budget opportunity GENERIC may correct
  part of its short-period errors; a seed-3 gap at 128 is more likely to shrink than reliably
  widen. Refuted if FACTOR's late absolute return and the relative gap rise together.
- **DM (hub):** both arms keep learning under ε = 0.1 (L_F > 0 and L_G > 0); |ΔJ_512| ≤ 1/12;
  D has the opposite sign to ΔJ_128 (regression toward zero), with L_G ≥ L_F; the late AUC
  difference is smaller in magnitude than AUC(0:128)'s difference. Most likely branch: the
  fourth row (shrinks) or the fifth (flat late) rather than the second.
- **Owner:** not taken (unattended).

## 6. Bounded CM objective

Objective document `VSPC1_K4_FACTOR_VALUE_B02_BUDGET512_CM_OBJECTIVE_20260906.md`.
Ordinary research changes only: a new B identity at seed 3, the prefix schedule plus 0.1
tail, the extended loop and 33 evaluation points, the three AUC windows, parameter readouts
and expected counts; reuse the existing host, models, update and publication path; one
focused check for the changes; the accepted seed-0/1/2 path and its tests unchanged, the old
AUC divisor untouched. No engineering-scope §4 addition. Stop condition: two complete arm
invocations at seed 3 with 33-point curves, three AUC windows, parameter readouts, counts and
resource fields published under the direction's results root, plus the CM record with the
frozen remote commands.
