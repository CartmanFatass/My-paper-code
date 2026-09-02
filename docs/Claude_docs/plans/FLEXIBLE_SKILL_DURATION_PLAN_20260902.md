# Flexible skill duration: follow-up plan for alignment

Status: alignment draft, 2026-09-02. Written by Claude for the owner after the discussion recorded in
`../research_notes/UNTIED_K_N_TRADEOFF_LEDGER_20260901.md` sections 8 and 9. Nothing here is a
science card, contract, or decision. Items marked **[DECIDE]** need the owner's call before code is
written; items marked **[ASK]** are questions the owner may want to put to me. Evidence classes and
the B-first order follow `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §11.

## 1. Position

This direction unties the skill duration k in HMASD-style hierarchical MARL while holding the agent
count N fixed as a stated parameter. It is one of two parallel programmes (the other unties N) and
does not target a joint algorithm.

The claim being pursued, in two parts:

1. On a host whose volatility differs across states or regions, a scheme that lets duration emerge
   from the value function beats every fixed k, by a gap that a toy bound predicts.
2. On a homogeneous host, the same scheme matches a tuned k* without tuning.

Part 2 alone is a robustness note, not a paper. Part 1 is the paper.

Non-goals: proving duration-independent skill semantics or semigroup consistency; learning an
end-to-end termination function as the first object; any variable-N claim.

## 2. Concern register

Each concern names its mechanism, the mitigation candidates, and the quantity that would show it.

| ID | Concern | Mechanism | Mitigation candidates | Measurable |
| --- | --- | --- | --- | --- |
| C1 | Non-stationarity beyond co-adaptation | Hierarchy-internal (low level moves the high-level SMDP; learned termination moves the kernel) plus an untying-induced layer (age distribution drifts) | Keep termination non-learned at first (interruption rule or fixed scheme); unfreeze one channel at a time | Variance of high-level value targets on a frozen probe set over training |
| C2 | Semantic drift | Skill = what the discriminator currently recognises; variable duration adds age to the label | Age input or fixed-age scoring; slow target copy of the discriminator; effect-defined skills | Discriminator accuracy on frozen probes; label agreement between adjacent checkpoints |
| C3 | Credit unit becomes variable | Segment length varies per agent | Credit (role, segment); per-agent SMDP returns with own τ_i | Advantage variance per agent versus fixed-k baseline |
| C4 | Action-space cost of a menu | n_z·|K| arms need ~|K|× the high-level samples unless values are shared across k | Interruption rule (0 added actions); skill-level hazard (n_z scalars); duration model sharing Q across k | High-level samples to reach a fixed return, versus fixed k |
| C5 | Durations with no pattern | Memoryless or heavy-tailed event durations defeat any pre-committed k | React-after-the-fact rule; check interval δ below dwell time; switching cost c against chattering | Regret versus oracle as a function of Var(D); switch count per episode |
| C6 | Predictable but not yet visible changes | After-the-fact rule reacts late | Optional prediction module feeding the interruption test a predicted state | Delay to switch versus event onset, with and without the module |
| C7 | Weak observation | Model-based durations inherit model error | Value-based rule needs only usable values on observations | Same as C5 under reduced observation |
| C8 | Asynchronous switching versus the autoregressive coordinator | Only a subset S re-decides at a check; Z's status; log-prob bookkeeping; storage | Conditional re-assignment with keep/edit masks; two-level interruption for Z; per-agent ragged segments; policy-based interruption test | Correctness tests on masks and log-probs; team-level switch count |
| C9 | Bookkeeping bias | Undiscounted within-segment reward sum over-credits long segments by τ(1−γ)/(1−γ^τ) | Discount inside segments before any untying | Return difference between the two bookkeepings at fixed policy |
| C10 | When can it win at all | Calm world: tuned k* is optimal | Heterogeneous-hazard host; report min-over-k max-regret bound | Gap to best fixed k as a function of hazard contrast |

## 3. Candidate schemes, least to most invasive

| ID | Scheme | Added actions | Added non-stationarity | Needs | Role in the plan |
| --- | --- | --- | --- | --- | --- |
| D0 | Fixed k (HMASD base) | 0 | none | — | Baseline, swept over k for the k* curve |
| D1 | Bookkeeping only: within-segment discount + age-conditioned discriminator, fixed k | 0 | none | discriminator input change | Control arm; isolates C2 and C9 |
| D2 | Policy-based interruption: at each check, switch agent i's skill if its current log-probability under the coordinator's conditional distribution trails the best by more than c | 0 | moves with the policy | keep/edit masks, per-agent segments | **First B object** |
| D3 | Value-based interruption with a per-skill Q head | 0 | moves with Q | Q(s, z) head | Second, if D2's policy proxy is too noisy |
| D4 | Skill-level hazard: each z carries a renewal probability | n_z scalars | small | one scalar per skill | Fallback for unobservable changes; stacks on D2/D3 |
| D5 | Interruption on a predicted state | 0 | prediction error | a short-horizon predictor | Add-on for C6, ablatable |
| D6 | Duration model sharing Q(s, z, k) across k | 0 | model error | k-step model (SCDMP's place) | Where a model earns its keep: replaces |K|-arm exploration |
| D7 | Learned β with deliberation cost | 0 | reopens the kernel | option-critic machinery | Last, only if D2–D6 leave a gap |
| D8 | (z, k) menu | ×|K| | none | — | Withdrawn as a first object (C4); kept as a comparator |

**[DECIDE]** D2 versus D3 as the first object. D2 needs no new head and reuses the same forward pass
as conditional re-assignment; D3 is the textbook form. Recommendation: D2 first.

## 4. Inspiration models and the single-agent bridge

No host is needed for the first two rungs.

- Drifting bandit with commitment (exists in `../toy_studies/untied_k_n/`): gives k* as a function
  of hazard λ; the min-over-k max-regret across two λ regions is the lower bound for C10.
- Renewal-process toy (to add): gathering events arrive at random intervals with durations D drawn
  from deterministic, exponential, and heavy-tailed laws; compare fixed k, menu, and interruption
  with parameters (δ, c). Prediction: interruption's regret curves nearly coincide across the three
  laws; fixed k's regret rises with Var(D).
- Single-agent bridge (to add): a moving-goal grid with options; compare fixed-k re-selection with
  interruption at δ = 1 and a sweep of c; then add an age input to a skill discriminator on the
  same grid and measure label agreement on a frozen probe set.

**[ASK]** whether to have these two toys built now (Opus, numpy, minutes) before any repository
code changes.

## 5. B-class experiment ladder

Every step: real learner, nonzero counts, resource admission, one exposure line (parameter
displacement relative to initialisation scale). One to three seeds; changes between runs recorded.

| Step | Object | Host | What is compared | Expected signal |
| --- | --- | --- | --- | --- |
| E0 | Exposure and probe set | any | — | Learner moves; probe set fixed for C1/C2 metrics |
| E1 | D1 on HMASD base, k = 10 | existing UAV scenario 1 or corridor | D0 vs D1 | Return change small; label agreement rises with age input (predict first) |
| E2 | D2 at δ = 1, sweep c | homogeneous host | D2 vs D0 swept over k | D2 matches best fixed k near some c; mean segment length monotone in c |
| E3 | D2 on heterogeneous hazard | relay corridor with two λ regions | D2 vs best fixed k | Positive gap of the order the toy bound predicts |
| E4 | D2 on random-duration events | corridor with renewal events, or UAV scenario 7 failures | D2 vs D0 vs D8 | D2 insensitive to the duration law; D0 and D8 degrade with Var(D) |
| E5 | Asynchrony | corridor, N fixed | individual-only vs two-level interruption for Z | Team-level switches rare; no collapse of Z semantics on probes |
| E6 | Add-ons | as E3/E4 | D2 + D4, D2 + D5 | Delay to switch drops with D5 on predictable events; D4 covers unobservable ones |

Promotion to C-BENCH only after E3 or E4 repeats across three to five seeds; the frozen contract,
oracle-retuned k*, and stated failure boundary are written then.

## 6. Hosts

- HMASD base route: already has the global boundary (`hmasd/agent.py:1897`), joint autoregressive
  sampling (`agent.py:1921-1929`), keep/edit masks in the horizon-window path (`agent.py:2010-2031`),
  elapsed-step storage (`agent.py:2797`), the undiscounted segment sum (`agent.py:3026`), per-state
  discriminators (`agent.py:1094-1102`), per-agent value heads (`hmasd/networks.py:727-729`).
- Process-core route: per-agent lifetimes on a shared interval clock, `team_intent_k`, ragged CSR
  packing, `smdp_gae`. Untied duration in interval multiples but not the clock.
- Relay corridor family (proposed in `../environment_design/`): parameters N, K, Z, H, k, λ, ρ, c,
  v, m, time-homogeneity flag; E3 needs two λ regions, E4 needs a renewal event process.
- UAV environment: C-TRANSFER target only; scenario 7's temporary failures and charging contention
  are the natural random-duration events.

**[DECIDE]** first route for E1/E2: HMASD base (smaller change, masks exist) or process-core (ragged
segments exist, but no autoregressive coordinator). Recommendation: HMASD base.

## 7. Theory ceiling for this direction

Bounds for the implemented scheme, no proofs of invariance:

- Interruption regret ≈ δ/2 + c × (number of switches), independent of the duration law, given the
  change is visible in the state within one step.
- Fixed-k regret grows with Var(D) (renewal toy) and with the hazard contrast across regions
  (min-over-k max-regret).
- Within-segment valuation bias of the undiscounted sum: τ(1−γ)/(1−γ^τ).
- Sample-count ratio of a menu to fixed k: about |K| unless values are shared across k.

Each is one page and each has a matching measurement in section 5.

## 8. Repository touch points for D2 (for sizing, not for implementation yet)

1. Interruption check at every step (or every δ steps) for each agent: one conditional forward pass
   of the coordinator with kept skills forced; compare log-probabilities; emit the subset S.
2. Conditional re-assignment for S only, using the existing keep/edit mask path.
3. Per-agent segment storage with own τ_i, log-probabilities summed over sampled agents only,
   SMDP discounting per agent; within-segment discount.
4. Discriminator age input.
5. Two-level interruption for Z on the global state, or Z held (owner's choice).
6. Metrics: switch counts, mean segment length, probe-set label agreement, discriminator probe
   accuracy, high-level target variance.

## 9. Decisions and questions for alignment

**[DECIDE]**
- A. D2 (policy-based) or D3 (value head) as the first object.
- B. Z policy: two-level interruption or Z held on a slow clock.
- C. Check interval δ: every step, or the old k as a coarse grid first.
- D. First route: HMASD base or process-core.
- E. First host: existing UAV scenario 1 for E1/E2, corridor for E3/E4, or corridor throughout.
- F. Whether SCDMP's duration-menu object is recast toward D6 (model shares Q across k) or left as is.
- G. Whether UCOPE's paid-probe period is treated as a D2 special case or stays separate.
- H. Who writes the one-page ADR for D2 and the corridor host (owner, per the tutoring protocol).

**[ASK]**
- Which of the toy predictions in section 4 do you want to commit to before the toys run?
- Q4 and Q5 from the ledger section 9.5.

## 10. What this plan deliberately leaves out

Learned termination (D7), any train-k/test-k′ contract, oracle-retuned comparators, and failure
boundaries are C-time items and appear only when a B signal repeats. No variable-N element enters
this direction; churn-driven termination is the roster direction's concern.

## 11. Decisions taken with the owner, 2026-09-02

Confirmed one by one in session. These replace the [DECIDE] / [ASK] items above.

| Item | Decision |
| --- | --- |
| A. First object | D2, policy-based interruption (no Q head) |
| B. Team code Z | Two-level interruption: Z re-decided only when a team-level interruption fires on the global state |
| C. Check interval | δ = 1, every step; chattering controlled by c |
| D. First route | HMASD base route (`hmasd/agent.py`), aligned with the paper baseline |
| E. Hosts | Existing UAV scenario 1 for E1/E2; relay-corridor family for E3/E4 |
| F. SCDMP | Recast toward D6: the duration model's value is sharing Q(s, z, k) across k in place of |K|-arm exploration; semigroup consistency becomes optional analysis; to be recorded in SCDMP's next intake |
| G. UCOPE | Stays independent; the exposure shortfall is fixed first; its odd/even duration split is a candidate C-time transfer test for this direction later |
| H. ADR | The owner writes the one-page ADR for D2 and the corridor host; Claude reviews it adversarially (tutoring protocol) |
| ASK 1. Toys | Plan mode is kept: Claude designs and reviews, the owner uses Codex as the implementer for the toys and for any repository code; Opus is not used to build them now |

Predictions committed before any run (predict-then-verify):

- Q4, owner's prediction: under the interruption rule the mean segment length versus switching cost c is monotone increasing, concave, and saturates at the episode length H. To be checked against the renewal-process toy when it runs.
- Q5, owner's answer: unclear. Record the question ("after adding age as a discriminator input, does the label-agreement rate between adjacent checkpoints on a frozen probe set rise or fall?") and compare with the E1 result when it exists; both directions and the probe-set-dependence answer stay open.

Implementation ownership from here: Codex implements toys and D2 under the owner's ADR; Claude keeps design, adversarial review, and the bounds in section 7.

ADR round 1 (2026-09-02, later the same day): GPT Pro drafted `ADR_01_D2_POLICY_INTERRUPTION.md`
and `ADR_02_RELAY_CORRIDOR_HOST.md`; both were reviewed in
`../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` and returned as REVISE. Six further decisions
were confirmed with the owner (review §4.1): causal-prefix interruption test in canonical order;
per-agent forced boundary with cap `k_max`; a `Z` switch forces every agent to re-decide; the rule
uses `gap ≥ c`; the owner writes the corridor mechanics; E4's heavy-tailed law is lognormal with
`E[D]` matched across laws. These refine decisions A to C above without reopening them.

ADR rounds 2 and 3 (2026-09-02): revision 2 added a separate team cap `k_Z` (default `k_max`,
`H` for E3/E4), the per-agent segment table, and `M` rows per rollout as the binding resolution
term; ADR 02 must register a duration margin `m_dur` next to `m`, and the ten-segment rule binds
only the fixed-`k` D0 sweep (review §II.10.1). Revision 3 of ADR 01 was accepted for
implementation (review Part III); Codex implements it. ADR 02 stays on hold until the owner's
mechanics page exists.
