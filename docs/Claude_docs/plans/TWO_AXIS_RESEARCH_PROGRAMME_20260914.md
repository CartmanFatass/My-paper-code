# Two-axis research programme: revised specification, consolidation, and process

Date: 2026-09-14. Author: Claude Code (Fable 5.1), at the owner's request, following the
critical review of the same day (`../reviews/FOUNDATIONS_AND_METHODOLOGY_CRITICAL_REVIEW_20260914.md`).
Alignment draft for the owner: items marked **[DECIDE]** are the owner's choices; everything else
is a recommendation with its reason. Nothing here is a card, contract or decision record.

The owner's questions, restated: (1) how to revise the research specification to match what the
MARL field expects; (2) how to prioritise, consolidate or discard the 27 directions; (3) how to
use the library and open-source projects for iterative research instead of isolated mechanisms
and bespoke experiments; (4) how to structure disciplined work on the two axes the owner
actually cares about, *flexible skill duration* (untie k) and *flexible team membership*
(untie N).

Jargon used once: **benchmark** = a fixed environment plus a fixed evaluation protocol that other
groups also run; **baseline** = a published method run from maintained code on that benchmark;
**seed** = one independent training run; **IQM** = interquartile mean, the robust aggregate the
field now reports with bootstrap confidence intervals; **option** = a temporally extended action
with its own termination rule; **macro-action** = the Dec-POMDP version of an option, which may
end at different times for different agents; **open team / ad hoc teamwork** = agents enter and
leave during an episode.

---

## A. What the MARL field expects, in one page

The standard is set by four papers, none of which is in the library yet:

| Standard | Source | What it requires |
| --- | --- | --- |
| Evaluation protocol | Gorsane et al. 2022, *Towards a standardised performance evaluation protocol for cooperative MARL* (NeurIPS) | ≥ 10 seeds where affordable (5 minimum), fixed number of evaluation episodes at fixed training-step checkpoints, report per-seed curves and aggregate, sample-efficiency and final-performance both, all hyperparameters disclosed |
| Statistical aggregation | Agarwal et al. 2021, *Deep RL at the edge of the statistical precipice* (NeurIPS), the `rliable` library | IQM with stratified bootstrap CIs, performance profiles, probability of improvement; never mean of best seeds |
| Benchmark and baseline hygiene | Papoudakis et al. 2021, *Benchmarking MARL algorithms in cooperative tasks* (NeurIPS D&B), the EPyMARL codebase | same code path for every algorithm, equal tuning budget per algorithm, tasks from LBF, RWARE, MPE, SMAC; parameter sharing declared |
| Seed variance | Henderson et al. 2018, *Deep RL that matters* (AAAI) | same-hyperparameter seed spread can exceed method differences; report it |

Three field conventions follow from these and are currently violated:

1. A method claim needs a benchmark other people run, a baseline from maintained code tuned
   with the same budget, and ≥ 5 seeds with learning curves. One-seed pairs on a private toy are
   not publishable evidence; they are development signals at best.
2. The minimum effect worth claiming is set by the observed seed spread on that benchmark,
   not by a fixed constant.
3. An ablation is the unit of mechanism evidence: full method, minus the component, on the same
   benchmark, same seeds. "Structured learner vs same-information generic learner on a host
   where the structure is necessary" is an identifiability check, not an ablation.

---

## B. The revised research specification (skeleton to replace the 721-line evidence spec)

Keep the current spec as history. Write a new one of about three pages with exactly these ten
sections. The text in brackets is what to fill in; the rest can be copied.

**B1. Mission (two sentences).** One cooperative MARL learner whose temporal abstraction does not
require a shared fixed skill clock, and whose coordination does not require a fixed roster.
Each property is demonstrated on a benchmark where the fixed version measurably fails.

**B2. The two axes and their canonical questions.**
- Axis K. When and how should an agent's skill end, if not on the shared clock? Sub-questions:
  interruption (end a skill when a better one is available), learned termination, asynchronous
  macro-actions across agents.
- Axis N. How does a coordinator and a shared policy keep return when agents enter or leave
  mid-episode, and when the count at test time differs from training?
- Joint objects are excluded until each axis has one published-grade result. [DECIDE: confirm.]

**B3. Frozen benchmark suite.** One controlled host and one external benchmark per axis, plus
the application host (see §D2 for the candidates). A benchmark enters this list only after the
necessity experiment (§E, ladder rung L0) shows the fixed-k or fixed-N learner loses on it.
No direction may define its own environment. [DECIDE: the four benchmarks.]

**B4. Baseline set.** For each benchmark: MAPPO (from the authors' `on-policy` code or EPyMARL),
the fixed-k HMASD port validated by R41B, and the axis-specific published method (§D1). Tuned
once per benchmark with a declared budget; the tuned configuration is frozen and reused.

**B5. Evaluation protocol.** 5 seeds per arm (10 for a headline claim); evaluation at fixed
training-step checkpoints, 32 episodes each, common random numbers across arms; report IQM and
95% stratified-bootstrap CI, per-seed curves, and the seed SD. A result is a *signal* when the
IQM difference exceeds 2 × seed SD and ≥ 4/5 seeds agree in sign; *null* when inside ±1 seed
SD; *inconclusive* otherwise (then either add seeds or stop, never re-read the same data).

**B6. The ladder** (§E). Every direction sits on exactly one rung; it advances only by passing
the rung's pre-registered rule. Rungs: L0 necessity, L1 baseline reproduction, L2 mechanism,
L3 ablation, L4 generalisation, L5 write-up.

**B7. Pre-registration.** Before a run: hypothesis, predicted sign and size, benchmark, arms,
seeds, checkpoints, decision rule. One page. Predictions are scored.

**B8. Compute accounting.** Environment steps and gradient steps per arm are matched or the
mismatch is declared. Wall time is recorded but never gates.

**B9. Reporting.** One living results table per axis: rung, benchmark, arms, seeds, IQM ± CI,
seed SD, verdict, date. Every run, including failed ones, appears once. No separate intake,
brief, packet, or ledger documents. [DECIDE: retire the audit/inbox/brief surfaces for science.]

**B10. Decision authority.** The owner decides what runs and what stops, on the results table
and the ladder rules. Language-model agents implement, run, collect and draft; external models
review. Nothing is decided unattended except the mechanical next step of an already-approved run.

What this removes from the current spec: object classes A/B/C with consumption; the §11
sub-sections; per-card MEI; headroom as a field; the 30% orchestration ratio; per-direction
hosts; Pro finality. What it keeps: quarantine of incomplete runs, no post-hoc rescue of a
frozen decision rule, predictions on record, common random numbers, resource admission.

---

## C. Consolidating the 27 directions

Rule: a direction survives only if its question is "does X change return under variable k (or
variable N) on a benchmark in B3, against the B4 baselines". Everything else is archived with
its evidence intact (`RESEARCH_MAP.md` marks it historical; no further compute, review or Pro
round).

| Direction | Disposition | Reason |
| --- | --- | --- |
| flexible_skill_duration (FSD) | **Axis K core** | The only replicated signal (4/5 pairs positive on the UAV host); the interruption rule is Sutton–Precup–Singh's interruption theorem applied to HMASD's coordinator, so it has a literature root |
| vsp_03 (event-aware termination) | fold into Axis K as the *learned termination* arm | Same question, toy host; its result (+0.013 at 512) becomes an ablation arm, not a direction |
| semigroup_consistent_duration_model_policy (SCDMP), vsp_c1 | archive | Duration-conditioned value sharing is a modelling choice inside Axis K, not a question; both families ended inside MEI |
| commitment_residual_triggered_options (CRTO) | archive | Three arms made identical decisions; no residual polarity; the trigger question is covered by learned termination |
| ucope (paid acquisition / reactive renewal) | archive | Information-acquisition question, not temporal abstraction; parked on a null |
| variable_n_fleet_churn (VNFC) | **Axis N core** (the application-host instance) | It is the UAV roster question; its two crashes were engineering, not science |
| vap_folr_core (FOLR) | fold into Axis N as the *survivor-state continuity* arm | "Keep vs reset hidden state at roster change" is a real sub-question; move it from Traffic Junction to the Axis N benchmark |
| roster_consistent_latent_exploration (RCLE) | fold into Axis N as an ablation of the coordinator's assignment representation | Exact recomputation showed no information necessity; only the finite-budget question remains and it belongs to the core |
| finite_resource_relational_inductive_efficiency (FRRIE) | fold into Axis N (train-N / test-N′ rung L4) | Its question is exactly the held-out-N protocol of REFIL/UPDeT; run it there, not on the blocked native host |
| degraded_incumbent_shadow_handover (DISH), capability_bound_semantic_currentness (CBSC), eociv_lite, expressibility_gated_renewal_credit_relay (EGRCR), recct_lite, active_post_churn_population_flow_identification (APFI), orbit_shadow_read, scope_1s, ec4g_r1 | archive | Communication, receipt, provenance and identification questions: systems questions in MARL clothing, off both axes |
| metric_ground_transport_allocation (MGTAP), acvc | archive | Allocation geometry and fallback-package questions on the UAV host, off both axes; ACVC's positive is a heuristic over an undertrained learner |
| actuator_conditioned_partial_sharing (ACPS), contention_aware_decentralized_communication (CADC), tail_return_distributional_learning (TRDL), cross_play_compatible_population_learning (CPCP), learned_counterfactual_agent_credit (LCAC) | archive | Registered 2026-09-12 from the library; standard heterogeneity, communication, distributional, population and credit topics with mature literatures, none on the two axes |
| vsp_02 (optimiser-state continuity) | archive | Null at MEI 0.5 on a toy; the practical question (reset Adam at roster change?) can be one arm of the FOLR continuity ablation if it ever matters |

Result: two directions, each with two or three named sub-arms. Twenty-two labels become
historical. The 14 legacy labels stay legacy.

---

## D. Using the library and open-source projects

### D1. What the library holds, and what to add

`docs/new-libs/` holds 27 items: two textbooks, the Dec-POMDP monograph, and 24 papers that are
almost entirely theory (mean-field games, potential games, variational-inequality optimisation,
sample complexity). Only MAVEN, HATRPO, the information-bottleneck communication paper and the
eight deep-dive papers (ACE, ACAC, InforMARL, Sable, ExpoComm, Safe-M3-UCRL, CT-MARL, IARO)
touch the two axes, and the deep dive's own synthesis found none of them solves within-episode
roster change or per-agent skill duration. The library therefore supports background reading
and the mean-field view of large N; it does not support the two axes as research programmes.

Add the following, read in this order, and record for each: the question it answers, the
benchmark it uses, whether code exists, and the one thing it does *not* do. (Verify each citation
against the source before relying on it; these are from memory.)

**Axis K (temporal abstraction, termination, asynchrony).**
1. Sutton, Precup & Singh 1999, *Between MDPs and semi-MDPs* (AIJ). The options framework and
   the **interruption theorem**: interrupting an option whenever another has higher value yields
   a policy at least as good. FSD's policy-gap rule is this theorem with a cost margin; the paper
   gives the axis its theoretical anchor and its first testable prediction.
2. Bacon, Harb & Precup 2017, *The option-critic architecture* (AAAI). Learned termination and
   its collapse; the baseline for "learned termination" arms.
3. Harb et al. 2018, *When waiting is not an option: learning options with a deliberation cost*
   (AAAI). The standard repair for termination collapse; supplies the cost term FSD's margin
   `c` corresponds to.
4. Harutyunyan et al. 2019, *The termination critic* (AISTATS). Termination as an information
   objective; the alternative to value-based termination.
5. Klissarov & Precup 2021, *Flexible option learning* (NeurIPS). Updating every option
   consistent with the observed trajectory; relevant to learning skills whose durations vary.
6. Amato et al. 2019, *Modeling and planning with macro-actions in decentralized POMDPs*
   (JAIR). The MacDec-POMDP formalism: the correct model for asynchronous per-agent durations.
7. Xiao, Hoffman & Amato 2020, *Macro-action-based deep multi-agent RL* (CoRL). Learning with
   asynchronous macro-actions; benchmarks Box Pushing, Overcooked variants, Warehouse Tool
   Delivery; code `yuchen-x/MacDeepMARL` (verify).
8. Xiao, Wei & Amato 2022, *Asynchronous actor-critic for multi-agent RL* (NeurIPS). The
   on-policy version; the natural baseline for "asynchronous" arms.
9. Yang, Borovikov & Zha 2019 (HSD) and Liu et al. 2022 (HSL), both cited by HMASD: individual
   skill hierarchies with local selection; the fixed-k comparators HMASD itself used.
10. ACAC (already in the library): per-agent asynchronous durations with a fixed roster; the
    closest existing method to the axis.

**Axis N (open teams, roster change, N-transfer).**
1. Rahman et al. 2021, *Open ad hoc teamwork using graph-based policy learning* (GPL, ICML),
   and the 2023 JMLR extension. **Agents enter and leave within an episode**; benchmarks are
   open-team Level-Based Foraging and Wolfpack; code `uoe-agents/GPL` (verify). This is the
   single most important addition: it is the axis-N problem with a published benchmark and
   baseline.
2. Mirsky et al. 2022, *A survey of ad hoc teamwork research* (EUMAS). Vocabulary and the map
   of the sub-problems.
3. Ellis et al. 2023, *SMACv2* (NeurIPS D&B). Per-episode random team composition and start
   positions; the standard benchmark for "composition varies".
4. Iqbal et al. 2021, *Randomized entity-wise factorization for multi-agent RL* (REFIL, ICML).
   Variable entity counts, train-N / test-N′ protocol, code available; the L4 protocol.
5. Hu et al. 2021, *UPDeT* (ICLR). Transformer policies transferable across N; a baseline for
   the coordinator's assignment representation.
6. Wang et al. 2020, *From few to more: large-scale dynamic multi-agent curriculum learning*
   (AAAI). Curriculum over N; a baseline for N-transfer.
7. Christianos et al. 2021, *Scaling MARL with selective parameter sharing* (ICML). What
   parameter sharing does and does not give; the honest null for "one shared policy for any N".
8. Papoudakis et al. 2021 (EPyMARL) for LBF and RWARE, which already support variable agent
   counts per task instance.
9. InforMARL, ACE and Sable (already in the library) as the N-scaling references.

**Methodology.** Gorsane 2022, Agarwal 2021, Papoudakis 2021, Henderson 2018 (§A).

### D2. Open-source substrates, and which to adopt

| Substrate | What it gives | Use |
| --- | --- | --- |
| EPyMARL (`uoe-agents/epymarl`) | MAPPO, IPPO, QMIX, MAA2C and others in one code path; LBF, RWARE, MPE, SMAC; parameter-sharing switch | **Baseline runner for both axes.** Reproduce its published LBF/RWARE numbers first (rung L1) |
| MAPPO official (`marlbenchmark/on-policy`) | The reference MAPPO the HMASD paper compared against | Cross-check EPyMARL's MAPPO on one task; otherwise redundant |
| GPL (`uoe-agents/GPL`) | Open-team LBF and Wolfpack with enter/leave events; GPL baseline | **Axis N external benchmark** |
| MacDeepMARL (`yuchen-x/MacDeepMARL`) | Box Pushing, Overcooked-macro, Warehouse Tool Delivery with inherently asynchronous macro-actions; Mac-IAICC baselines | **Axis K external benchmark** |
| SMACv2 (`oxwhirl/smacv2`) | Random composition; heavy (StarCraft II) | Axis N rung L4 only, if compute allows; otherwise REFIL's MPE tasks |
| JaxMARL (`FLAIROx/JaxMARL`) | SMAX, MPE, Overcooked, Hanabi at very high throughput on GPU | Consider once the programme needs 10-seed sweeps; not for the first eight weeks |
| PettingZoo + this repository's scenario 1 | The application host | Headroom experiment and the final demonstration only |
| This repository's `envs/relay_corridor/` | Controlled hazard host with exact oracle margins | Axis K controlled host (already built, already has exact references) |
| This repository's `envs/continuous_roster/` | Controlled roster host | Axis N controlled host, if the L0 necessity test passes; otherwise open LBF alone |

Adoption rule: run the substrate's own published example to its published number before
changing anything. That reproduction is rung L1 and it is a result worth recording even when it
succeeds trivially.

### D3. From library to question: the procedure

For each candidate question, write one page with six fields before any code:

1. **Gap statement.** One sentence: "Existing method M does X but fails when Y." Cite the
   paper that shows or admits the failure.
2. **Where the failure is visible.** A benchmark from B3 and a measurable quantity on it.
3. **Baseline number.** The reproduced M on that benchmark, with seeds. If this number does not
   exist yet, the question is not ready.
4. **Hypothesis.** "Adding Z closes fraction f of the gap because …", with predicted sign and
   size relative to the seed SD.
5. **Minimum experiment.** Arms, seeds, checkpoints, decision rule (B5).
6. **What a null would mean.** The interpretation written before the result.

A question that cannot fill field 3 goes to the reading list, not to the queue. A question whose
field 2 is "a host I would build for it" is rejected.

---

## E. The ladder: disciplined iteration on each axis

Every direction is on one rung. Rules are pre-registered at entry to the rung.

| Rung | Question | Pass rule | Typical cost |
| --- | --- | --- | --- |
| **L0 Necessity** | Does the fixed version lose on this benchmark? | Fixed-k HMASD at its best k (or fixed-N learner) is below the oracle or the flexible published method by > 2 seed SD | 5 seeds × 3–5 arms |
| **L1 Baseline reproduction** | Can we reproduce the published baseline number from its code? | Within the paper's reported CI | 5 seeds × 1–2 arms |
| **L2 Mechanism** | Does our method beat the fixed version and the published flexible baseline? | Signal per B5 against both | 5 seeds × 3 arms |
| **L3 Ablation** | Which component carries the effect? | Removing the component removes the signal; nothing else does | 5 seeds × (components + 1) |
| **L4 Generalisation** | Does it hold on the second benchmark and under held-out k / N′? | Signal on ≥ 1 further benchmark; no reversal on any | 5–10 seeds × 2 arms × benchmarks |
| **L5 Write-up** | Is the claim stated at the evidence's ceiling? | External review by a human or by Pro *as reviewer* | none |

Iteration discipline:
- One experiment cycle per axis per week: pre-register Monday, run, read Friday, decide.
- A failed rung is retried at most once with one declared change; a second failure stops the
  arm, not the axis.
- The results table (B9) is the only status document. Update it every cycle.
- Never move to the next rung on an inconclusive result; add seeds or stop.

### Axis K, concretely

- Controlled host: `relay_corridor` at hazard λ = 0.02 (it already has exact oracle margins
  m_dur, the L0 quantity).
- External benchmark: MacDec-POMDP Warehouse Tool Delivery or Box Pushing (asynchronous
  durations are intrinsic; Mac-IAICC is the baseline).
- Application: scenario 1 with **moving or bursting users** (add a latent hazard; the static
  host has nothing to react to).
- L2 arms: fixed-k HMASD at best k; HMASD + interruption (FSD D2); HMASD + learned termination
  with deliberation cost; Mac-IAICC (external only).
- First prediction to test: the interruption gain grows with hazard λ and vanishes at λ = 0.

### Axis N, concretely

- Controlled host: `continuous_roster` only if L0 passes; otherwise skip to open LBF.
- External benchmark: GPL's open-team LBF (enter/leave mid-episode; GPL baseline).
- Application: scenario 1 with UAV failure and replacement events.
- L2 arms: shared MAPPO with padding/masking (the honest null); GPL; HMASD coordinator with
  composition-based assignment (the N-portable version of the N-tuple, from the trade-off
  ledger N-2); ± survivor-state continuity (FOLR's question) as the L3 ablation.
- L4: train at N ∈ {3,4,5}, test at N = 7 (REFIL protocol).

---

## F. The first eight weeks

| Week | Work | Deliverable |
| --- | --- | --- |
| 1–2 | Headroom on scenario 1: MAPPO (EPyMARL or on-policy), MAT if cheap, fixed-k HMASD; 5 seeds; reference-length training; learning curves | The number that decides whether hierarchy matters on the application host |
| 1–2 (parallel) | Install EPyMARL, GPL, MacDeepMARL; reproduce one published number each (L1) | Three L1 rows in the results table |
| 3–4 | L0 on both axes: relay_corridor hazard sweep with fixed-k best vs oracle; open LBF with fixed-roster MAPPO vs GPL | Whether each benchmark shows the gap; freeze B3 |
| 5–6 | Axis K L2: FSD interruption vs fixed-k on the corridor, 5 seeds; hazard sweep λ ∈ {0, 0.005, 0.02} | First publishable-grade curve |
| 7–8 | Axis N L2: coordinator composition assignment vs padded MAPPO vs GPL on open LBF, 5 seeds | Second curve; decide whether FOLR continuity is the next ablation |

Compute: every cell above is well within the GPU node's capacity at EPyMARL/LBF scale; the
headroom experiment is the only expensive item (about fifteen reference-length runs).

---

## G. How the existing agent loop should change

The Codex/Claude control plane is good at executing, collecting and archiving. Keep it for that.
Change three things: (1) the owner writes or approves every pre-registration page; the loop does
not generate objects; (2) Pro nodes review a completed rung and may recommend, never decide;
(3) retire the audit ledger, inbox, briefs and Pro packets for science, keeping them only for
mechanical execution facts. The `docs/research/candidates/` tree becomes read-only history; the
two axes get two new directories with one results table each.

---

## H. Decisions for the owner

- **[DECIDE 1]** Adopt the two-axis consolidation in §C (22 directions archived, FSD and VNFC
  cores, FOLR/RCLE/FRRIE/vsp_03 folded as arms).
- **[DECIDE 2]** Approve the headroom experiment (§F weeks 1–2) as the first run, before any
  mechanism work.
- **[DECIDE 3]** Choose the external benchmarks: MacDec-POMDP tasks for K, GPL open LBF for N
  (recommended), or name alternatives.
- **[DECIDE 4]** Adopt the B5 inference rule (5 seeds, 2 × seed SD, IQM + CI) and retire the
  per-card MEI.
- **[DECIDE 5]** Replace the evidence spec with the B1–B10 skeleton; keep the old one as
  history.
- **[DECIDE 6]** Restrict the agent loop to execution and review (§G); end unattended
  object-tier science decisions.
- **[DECIDE 7]** Add the D1 reading list to the library and read Axis K items 1–3 and Axis N
  item 1 before week 3.
