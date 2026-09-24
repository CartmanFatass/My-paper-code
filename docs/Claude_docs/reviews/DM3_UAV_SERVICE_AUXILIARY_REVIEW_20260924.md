# Independent review — DM3 `uav_service_auxiliary` (S7 service benefit and return-risk control), 2026-09-24

Reviewer stance: demanding MARL reviewer who also reads code. Everything marked **[verified]** was recomputed
from `runs/uav_service_auxiliary/*/summary.json` or read directly in the code of branch
`codex/uav-service-predictive-control` (worktree HEAD `61c8a626`); **[inferred]** marks judgment or
reasoning not directly checkable from the repository. Numbers are to 3 significant figures unless a
NOTES value is being matched exactly.

## Verdict

The direction has run five batches (six training pairs, ten training fits, ~1,280 runner-minutes) without
producing a repeated service improvement, and its two "risk" batches rest on a statistic that a heavy-tailed,
32-world paired panel cannot support. Recomputing B04/B05 from the run files reproduces every NOTES headline
exactly, but also shows that (i) the S7 "risk" term is a deterministic geometric return-margin penalty whose
per-step ceiling (2.0) is twice the QoS reward ceiling (1.0); (ii) no cutoff, depletion or charging event
fired in any of the 256 evaluation episodes of B04/B05, and the worst episode-minimum battery over all worlds
is 0.308 against an emergency threshold of 0.05, so the failure mechanism the direction is nominally about is
never exercised; (iii) the B05 "final mean J +242" is a mean over a distribution whose median is −99, whose
sign test gives p = 0.60, and whose net sum is 52 % contributed by the eight worlds in which the R policy
delivers zero service. B04's final panel is genuinely favourable (22/32, Wilcoxon p = 0.004), but it is one
training instance and its development panel points the other way. The coefficient change 2→4 is a linear
re-scalarisation, not a risk-sensitive objective, and the codebase already contains an unused Lagrangian
hook (`safety_dual`) that a reviewer would expect to see instead. B06 is a well-engineered, genuinely
zero-update shield test on frozen policies; it can tell us whether a trivial rule removes the late-episode
penalty without collapsing service, but whichever way it goes it says more about the task than about the
method. My recommendation is to treat B01–B05 as a closed negative/limitations result, let B06 finish and
read it by a median/zero-service rule, and only continue if the direction is re-based on (a) ≥3 seeds per
arm and (b) a formulation in which risk is real (reachable depletion or an explicit CMDP constraint), with a
concrete retirement criterion stated in advance.

## 1. Evidence chain B01 → B06

All J values are undiscounted 1500-step sums of the original S7 shared reward, one deterministic episode per
world. "n" is training instances per arm (constitution §8.1 asks for ≥3). "Events" = cutoff/depletion/charging
in evaluation. **[verified]** unless noted.

| Batch | Comparison | n / arm | Worlds (panel) | Headline effect (final panel) | Service / cost / battery | Adverse worlds | DM conclusion | Reviewer note |
|---|---|---|---|---|---|---|---|---|
| B01 (seed 910021) | detach vs joint W10 factual-QoS auxiliary head | 1 | 8 development (920001–08), fixed endpoint update 30 | joint−detach J **+160** (−485 vs −645) | QoS +0.0388/step, cost −0.0340 | mean J of both arms negative; late decline in both | provisional positive | 8 dev worlds, one seed; both arms worse at update 30 than 10 |
| B02 (seed 910137) | same package, second pair | 1 | 8 development, endpoint 30 | **+404** (−267 vs −670); 7/8 wins; MSE ordering reversed (joint MSE 2.25× detach) | QoS +0.0800, cost −0.0946 | 920008 −64; three worlds lose QoS | "keep bounded package, weaken proxy explanation" | positive recurrence, but the proxy hypothesis (prediction error mediates gain) was falsified in the same batch |
| B03 (seeds 912211, 912347) | D (none) / S (service head) / G (generic next-obs head) | 1 per block (2 blocks) | 8 dev + **32 final** (938001–32) | block 1: S−D +24.6, G−D +118; block 2: S−D −16.8, G−D −24.9 | block-2 final QoS D .234 / S .218 / G .289; zero-service final worlds D 1→4, S 2→3, G 1→2 | −1,829 (S b1), −2,070 (G b2) worst worlds | sign reversals, **recipe closed** | correct call; 32 final worlds already used, so "final" is not held-out afterwards |
| B04 (seed 914021) | N (λ_train 2) vs R (λ_train 4), both evaluated at λ = 2 | 1 | 8 dev ×4 checkpoints + 32 final | final R−N J **+549** (mean), median +460, 22/32 wins, sign p = 0.050, Wilcoxon p = 0.004; dev30 **−218**, 2/6 | QoS +0.109 (22/32 up), capped cost −0.129, min-battery +0.0358 (31/32 up) | −899 (938021), −797, −747; R has 6 zero-service worlds (N 6) | "native final gain with contrary development worlds" | strongest single result in the direction; ΔJ vs N-J Spearman −0.79: R wins where N was catastrophic |
| B05 (seed 914173) | same N/R recipe, fresh seed | 1 (2 cumulative) | same 8 dev + same 32 final | final **+242** mean, **median −99**, 14/32, sign p = 0.60, Wilcoxon p = 0.70, 10 %-trimmed mean +153; dev30 −37.7, 3/5 | QoS **−0.0268** (12/32 up), cost −0.0942, min-battery +0.0073 (18/32) | worst −676; R zero-service worlds **8** vs N 1; 52 % of net ΣΔJ from those 8 worlds | "risk savings recur, service gains do not; no more coefficient-4 fits" | mean-positive/median-negative is exactly the abstention signature (see §2.4) |
| B06 (running, accepted 2026-09-24T01:50Z) | O (original execution) vs F (margin shield: enter m ≤ 0, exit m ≥ 0.05) on the two frozen N checkpoints | 0 fits, 0 updates | 8 dev + 32 final per checkpoint = 160 episodes | pending | pending | pending | prospective branches written | zero-update and lawful-observation claims verified in code (§2.6) |

Cumulative cost **[verified from summaries/NOTES]**: B01/B02 509 min, B03 771 min, B04 287 min, B05 260 min
of runner wall, i.e. ~1,830 min ≈ 30.5 h for ten fits plus replays; B06 ≤ 240k evaluation transitions.

Two structural facts hold across every batch: every evaluation episode truncates at 1500 steps
(`terminal_type == "truncated"`), and cutoff/depletion/charging counts are 0 in every evaluation world of
B01–B05 (training shows 1–3 charging UAV-steps in total). The worst episode-minimum battery in the B04/B05
panels is 0.308 (N, 938021/938032).

## 2. Code and protocol findings

Paths are relative to the direction worktree (`envs/pettingzoo/relay/energy_aware.py` = `EA`;
`experiments/candidates/uav_service_auxiliary/` = `X`). Severity: blocker / major / minor.

### 2.1 The reward: scale, per-step cost, dominance — **major** (design), not a bug

- `EA:855-861` **[verified]**: `r = qos_satisfaction_ratio − λ·min(raw, cap) − 5·new_cutoff − 10·new_depletion + PBRS_delta`,
  with `raw = max_i max(0, −margin_i) / 0.05` (`EA:796-800`), `cap = 1.0`, `λ = 2.0`
  (`config.json`: `return_margin_scale .05`, `return_cost_cap 1.0`, `lambda_return 2.0`). Identity checked on
  world 938001 (B04 N): 399.1 − 2×630.4 − 14.6 = −876.2 = `raw_native_J` ✓; `X/b04/evaluation.py:30-36`
  enforces it every step.
- Consequently the per-step reward lies in [−2 − |PBRS|, +1]; J is the *undiscounted 1500-step sum*, hence
  values in the hundreds to ±2,000. This is simply horizon × per-step scale; the S1 figures quoted as ~0.5
  are per-step or normalised **[inferred]**. Nothing wrong, but J differences of "+549" are ≈ 0.37 per step.
- The cost ceiling is **twice** the QoS ceiling, and realised QoS per step is 0.15–0.30 (max world 0.598),
  while realised capped cost per step reaches 0.55–0.61 in N's bad worlds. J is therefore dominated by the
  cost term: in B05 the accounting of the +242 is −40 (service) + 282 (−2×cost) − 0.4 (PBRS)
  (NOTES, reproduced). The direction's question "convert service into net benefit" is being read on a
  scalar in which service is the minority component.
- The cost is a **max over UAVs** on a **shared** team reward (`EA:798`): one straggler penalises all
  eight agents identically. **[inferred]** This is a hard credit-assignment structure for a shared-reward
  MAPPO-style learner and a plausible reason why the learned "fix" is team-wide retreat rather than
  targeted return.
- PBRS is negligible: `EA:944-952` gives γΦ′−Φ with Φ′=0 at the terminal, episode sum −12 to −15
  **[verified]**.

### 2.2 The "risk" is a deterministic geometric proxy; failure events are unreachable — **blocker** for the risk framing

- `EA:1573-1588` **[verified]**: `margin_i = battery_i − (dist_to_nearest_station / 3 m/s × P(3 m/s)/3600)/160 Wh − 0.10`.
  Battery decreases monotonically in evaluation (no charging ever occurs), so the penalty is a function of
  (time, distance to station) with no stochastic hazard. It becomes active in the last ~third of the
  episode: the six-bin inspection in NOTES shows B05 N mean cost 0/0/.052/.213/.325/.495 per 250-step bin.
- The actual failure mechanisms — limp-home at battery ≤ 0.05 (`EA:1667-1671`, `emergency_return_threshold`),
  service cutoff at ≤ 0.02, depletion at ≤ 0.0, penalties 5 and 10 — are **never reached**: initial
  battery ∈ [0.75, 1.0], observed worst episode-minimum 0.308 over 256 B04/B05 evaluation episodes, mean
  ≈ 0.35–0.39. At the observed drain (≤ 0.69 per 1500 steps) a UAV cannot get within 6× of the emergency
  threshold before truncation. **[verified from data; drain bound inferred]**
- Therefore the "return risk" the direction has been optimising is exclusively the shaped margin penalty;
  "risk reduction" in B04/B05 means "fewer late-episode steps far from a station", nothing about actual
  loss of aircraft or service cutoffs. The NOTES are honest about this ("zero failures do not establish
  catastrophe prevention"), but the direction's framing in RESEARCH ("返航风险") is not.

### 2.3 Coefficient 2→4 in training, 2 in evaluation — **major** (interpretation); implementation correct

- `X/b04/native.py:26,44-46,88` **[verified]**: `r_train(R) = r_native − 2·cost`, i.e. λ_train = 4; the
  scalar enters `store_transition_batch` and therefore both hierarchy levels' GAE. `X/b04/evaluation.py:25,43`
  refuse any evaluation coefficient other than 2. Audit trail (first-rollout identity, advantage deltas) is
  exemplary.
- Scientifically this is **reward re-weighting** — a different point on the linear scalarisation of a
  two-objective problem — evaluated on the original scalarisation. It is not risk-sensitivity in the sense
  the literature uses (variance/CVaR/constraint satisfaction). The hypothesis it can test is "finite PPO
  under-prices the cost term"; it cannot distinguish that from "the λ = 2 optimum on these worlds is itself
  a non-serving policy for many worlds". The B05 zero-service outcome is the textbook symptom of the second.
- The environment already implements the principled alternative: `EA:667-675` `set_scenario7_safety_dual` /
  variant `qos_adaptive_safety_graph_pbrs`, i.e. a rollout-frozen Lagrange multiplier. It was never used in
  this direction. A reviewer will ask why a hand-picked λ was tested when a dual-ascent λ with an explicit
  constraint level was one config flag away.

### 2.4 Statistics on a heavy-tailed paired panel — **major**

- Per-world ΔJ ranges from −899 to +2,075 on 32 worlds. In B05 the three largest worlds carry 72.5 % of the
  net sum, dropping the top three positives moves the mean from +242 to +73, the median is −99 and the
  win count 14/32 (binomial two-sided p = 0.60; Wilcoxon signed-rank p = 0.70). In B04 the same statistics
  are median +460, 22/32, p = 0.050 (sign), p = 0.004 (Wilcoxon) — a real within-instance effect.
  **[verified]**
- The gain is concentrated where N was already catastrophic: Spearman(N J, ΔJ) = −0.79 (B04) and −0.69
  (B05). Restricting to the 24/25 worlds where N's cost/step ≤ 0.4, B04 still gives mean +207 / median
  +124 / 14 of 24 wins, but B05 gives mean **−80** / median **−145** / 8 of 25 wins. **[verified]**
- In B05, 52 % of the net ΣΔJ comes from the eight worlds in which R's QoS sum is exactly 0 (six of them
  are J "wins": 938004/06/07/09/21/23). A policy that parks by the station converts J ≈ −1,600 into
  J ≈ −30 without serving anyone. This is the mechanism that produces "mean positive, median negative"
  trivially, and it is why "final J/cost sign recurs" (NOTES B05) is not a recurrence of anything a user
  of the system would want.
- The NOTES do report medians, win counts and zero-service worlds and refuse pooling, which is to their
  credit. But the RESEARCH standing row leads with "+241.885454" and the working explanation is still
  phrased as "risk savings recur". With one training instance per arm per batch and 2 seeds cumulatively,
  constitution §8.1 ("single-seed observations stay exploratory") applies to every B04/B05 sentence.
- Minor: the same 32 "final" worlds were used by B03, B04 and B05; after B03 they are exposed, and the
  NOTES concede this. Development-vs-final disagreement in both B04 and B05 (dev30 −218 / −38) is not
  a "scope restriction", it is a warning that 8 and 32 worlds are both too few to estimate a mean with
  sd ≈ 770–870 per world (standard error ≈ 140–155 on 32 worlds).

### 2.5 B03 auxiliary heads — **minor / no leakage found**

- `X/b03/auxiliary.py:1-6, 519-586` and `X/b01/auxiliary.py:51-94` **[verified]**: target = mean team QoS
  over the next W = 10 steps (hindsight label, censored at terminals), broadcast to all N agents; G head =
  next normalised observation conditioned on the submitted command. Inputs are actor-legal observations,
  realised skills and GRU hidden; gradients reach the actor only in the S/G arm (`features.detach()` in the
  other). No action-path use of future information. This is a standard UNREAL/auxiliary-task construction.
- Weakness is scientific, not lawful: the target is a *team* scalar predicted by each agent from a
  *local* observation, so much of the target is unpredictable noise for any single agent, and B03's
  common-endpoint replay indeed shows every model losing to the persistence baseline on observation MSE
  and only marginally beating a constant on service MSE.

### 2.6 B06 feedback rule — verified as described; **minor** caveats

- Lawful observability: `EA:2245-2258` puts `uav_return_energy_margins[i]` (raw margin) and battery in every
  agent's own record (13 fields; margin index 12, battery index 3); station records have 8 fields with the
  validity flag at index 7. `X/b06/feedback.py:80-92` decodes exactly those indices from the 120-field
  suffix of the 365-dim observation; scales (8000 m, 150 m height span, 30/5 m/s, 160 m docking radius)
  match `config.json`. **[verified]**
- It is a **controller override**, not a policy: `feedback.py:147-169` replaces the actor's command with a
  full-speed vector to the nearest station plus the dock bit while the mode is active. The policy's GRU and
  skill clock keep running on the modified history (`b06/native.py:403-457`). Zero-update is real:
  `new_optimizer_updates: 0` (`native.py:553,717`) and checkpoint fingerprint/normaliser immutability checks
  (`native.py:374,546`).
- Caveat 1: the rule enters only at margin ≤ 0, i.e. after the penalty is already non-zero, and the cost
  saturates at margin = −0.05; so the shield can at best shorten the saturated tail, not prevent it. **[inferred]**
- Caveat 2: the margin is computed at limp-home power P(3 m/s) (`EA:1576`), while the override flies at
  30 m/s; the energy actually spent returning can differ in either direction from the margin's estimate,
  so "margin recovery" is not guaranteed to be monotone. **[inferred]**
- Caveat 3: exiting at 0.05 and handing control back to a policy that flies away again creates a
  bang-bang oscillation; hysteresis of one scale unit mitigates but does not remove it. The DM's own
  prediction ("might remove critical relays") is the right adverse branch.

### 2.7 Things that are done well (so the reviewer's complaints are proportionate)

Reward identity re-derived every step; first-rollout physical identity across arms; independent float64
recomputation of GAE; per-world tables preserved; sign reversals reported instead of pooled; no checkpoint
selection; admission guard with SHA binding. Engineering hygiene is well above the field's norm.

## 3. Scientific assessment

**Is there a coherent hypothesis left?** The original hypothesis (B01–B03) — a factual service prediction
head improves control — was falsified in its mechanistic form in B02 (gain without proxy improvement) and in
its outcome form in B03 (sign reversal). The replacement hypothesis (B04–B05) — "finite PPO under-prices
the return penalty; a stronger weight buys net original-objective benefit" — has one supportive instance and
one that, read by median or by service, is adverse. What survives is a much weaker, and to my mind
different, statement: *on this task, increasing λ shifts the policy toward abstention in worlds where the
baseline was already penalty-saturated*. That is a property of the scalarisation, not a learning result,
and it does not need RL to demonstrate.

**Are the statistics read appropriately?** Partly. The DM reports medians and win counts, but the
headline, the RESEARCH row and the "recurrence" language are mean-based on 32 draws from a distribution
with sd ≈ 800 and a two-cluster structure (catastrophic vs serving worlds). On such data the right primary
readouts are the paired sign/Wilcoxon test, the median, a trimmed mean, and the count of *new* zero-service
worlds; by those readouts B04 is positive and B05 is null-to-negative, and the honest summary is "one of
two". A reviewer would also want the metric split into "worlds where N served" and "worlds where N did
not", because the two clusters have opposite ΔJ.

**What does B06 discriminate?** Whether a one-line shield removes late-episode margin cost from frozen N
policies without collapsing service. If F wins on J with median > 0 and no new zero-service worlds, the
conclusion is that the risk term is trivially controllable by a rule — good engineering, but it removes
the reason to learn risk at all in this task. If F loses because relay UAVs leave and QoS collapses, the
conclusion is that the geometry couples cost and service so tightly that a per-UAV rule is the wrong
abstraction — informative about the task, still not about the learning method. Either way B06 is a
baseline for the eventual paper, not evidence for the direction's hypothesis.

**Research question or engineering objective?** "Turn service improvement into net benefit including
return risk" is, as posed, a scalarisation-design objective. It becomes a research question only when
one states what is unknown: e.g. *does constrained MARL with a learned multiplier reach a better
service–risk frontier than fixed-λ scalarisation under shared, max-aggregated cost?* or *does a shield in
the loop during training let the policy learn to serve while returns are guaranteed?* Neither has been
posed.

**Does S7 as configured exercise the risk mechanism?** No (§2.2). With no reachable depletion, no
charging, and a penalty that is a smooth function of time and distance, "risk" is a potential-function
proxy. Any conclusions about risk should say "late-episode return-margin penalty".

## 4. Literature position

Citations are from the reviewer's knowledge and were not re-verified online.

- **Constrained / Lagrangian RL.** The standard formulation is a CMDP (Altman 1999) solved by
  primal-dual methods: CPO (Achiam et al. 2017), RCPO (Tessler et al. 2019), PPO-Lagrangian and the
  Safety Gym benchmark (Ray, Achiam, Amodei 2019), PID-Lagrangian (Stooke, Achiam, Abbeel 2020). The
  multi-agent versions are MACPO / MAPPO-Lagrangian (Gu et al. 2021/2023). All of these replace a
  hand-picked λ with a constraint level plus dual ascent, and report the *constraint satisfaction* and the
  *return* separately. The environment's `qos_adaptive_safety_graph_pbrs` variant is exactly this hook.
- **Risk-sensitive objectives.** CVaR policy gradient (Tamar et al. 2015; Chow et al. 2015, 2018),
  distributional RL with risk measures (Dabney et al. 2018). These target tail outcomes explicitly; the
  direction's B04/B05 tail improvements (P10 J −1,393 → −746) are the kind of thing such objectives are
  designed for, but they arise here as a side-effect of abstention.
- **Shielding / safe execution.** Alshiekh et al. 2018 (shielded RL), ElSayed-Aly et al. 2021 (safe MARL
  via shielding). The canonical use is *during training* so the learner explores only safe actions; B06
  applies the shield post hoc on frozen policies, which is the weaker "runtime enforcement" variant.
- **UAV energy-aware coverage.** The P0/Pi rotary-wing power model in `EA:1790` is Zeng, Xu & Zhang
  (TWC 2019). Energy-constrained DRL coverage/relay work (Liu et al. JSAC 2018; Liu et al. TMC 2020;
  Theile et al. IROS 2020; Bayerlein et al. 2021) typically makes battery depletion a *hard* terminal
  event within the horizon or a hard landing constraint, and reports service under that constraint. S7's
  configuration, where depletion is unreachable, is out of step with that practice.
- **What a reviewer would expect instead of coefficient tuning:** a constraint level with a learned
  multiplier; ≥3 seeds per arm with per-seed effects; frontier plots (service vs cost) rather than one J;
  CVaR/median in addition to the mean; a shield baseline reported alongside learned safety; and a task
  in which the failure event is reachable so that "risk" has an operational meaning.

## 5. Recommendations

**What B06 must show to justify continuing.** Read it by a rule fixed now: for each of the two checkpoints,
(a) final-32 F−O median J > 0 and ≥ 20/32 wins, (b) no new zero-service worlds and QoS/step not lower by
more than 0.02, (c) capped cost/step lower and the number of negative-margin UAV-steps lower. Only if
(a)–(c) hold on both checkpoints does the shield become a component worth carrying into training. If (b)
fails while (a) holds, record "cost removable only by service loss" and stop the shield line.

**Retirement criterion (concrete).** Retire the direction from the Active table if, after B06, there is
still no intervention with ≥ 2 independent training instances showing median ΔJ > 0 *and* median ΔQoS ≥ 0
on the held-out panel. That criterion is already unmet by B01–B05.

**The one or two experiments that would actually answer the risk question.**

1. *Constrained learning with the existing hook* (≈ 6 fits ≈ 13–15 h runner wall at the observed
   125–152 min/fit): N (λ = 2) vs L (variant `qos_adaptive_safety_graph_pbrs`, constraint "mean capped
   cost ≤ 0.02/step", dual ascent per rollout), 3 seeds each, fresh 32-world final panel never used
   before, readouts = median/sign of ΔJ, ΔQoS, CVaR10 of J, new zero-service worlds. This asks whether a
   multiplier finds a service-compatible operating point that fixed λ = 4 did not.
2. *Make the risk real, then test shield-in-the-loop* (≈ 6 fits): lower `initial_battery_ratio_range` to
   [0.35, 0.6] or extend the horizon so depletion is reachable, then train N vs N+shield (B06 rule active
   during collection), 3 seeds each. This tests the actual claim of the direction — that a service policy
   can be learned under a guaranteed return — instead of a proxy.
   If budget allows only one, run (1); it reuses the environment unchanged and answers the "coefficient vs
   constraint" question a reviewer will ask first.

**Publishability.** Not publishable standalone: two seeds, a proxy risk, and a mean/median disagreement
at the core. Publishable, and useful, as a *limitations / negative-results* subsection of the main HMASD
paper: "on S7 a fixed-λ re-weighting of a max-aggregated return-margin penalty produced mean-positive but
median-negative paired outcomes, driven by abstention in penalty-saturated worlds; a hindsight
service-prediction auxiliary showed no repeatable gain across two blocks; a lawful margin shield on frozen
policies [B06 result]". That paragraph, with the per-world tables already in NOTES, is honest and would be
cited as a cautionary example. Anything stronger requires experiments (1) or (2).
