# MARL exploration guidance for the portfolio (2026-09-04)

Written by Claude Code (Fable 5.1) at the owner's request ("给我一个 general idea 上的指导，后续如何探索
MARL 的算法是合适的", then "同意，写一份文档给 Codex"). It is an alignment draft, not a decision record:
Portfolio-tier items below take effect only when the owner ratifies them into
`docs/research/portfolio/decisions/`, and nothing here changes a frozen scientific object. Codex
Root is the intended executor after ratification. Basis: `PORTFOLIO.md` at
`2026-09-04T13:41:57Z`, repository HEAD `72f798c59`, the evidence spec
`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` (§5.2, §8.1, §11), and `AGENTS.md` §2, §5.

Markers: **[DECIDE]** is a choice only the owner can make; **[ASK]** is a detail the author would
settle by default but wants confirmed; unmarked items are recommendations Root can apply at the
Object tier under the standing delegation.

## 0. What the portfolio snapshot shows (observation)

Twenty-two registered directions, fifty-three implementation directories, four PARKED. Every valid
algorithm observation recorded in the snapshot falls into one of four classes:

| Class of outcome | Directions (from the 2026-09-04 reason lines) |
| --- | --- |
| Verdict `NEITHER` or comparator too weak to give polarity | FSD E2 (15 runs, `NEITHER`); CRTO B01-R1 (`COMPARATOR_WEAK`, REPLAN chosen on 4/8 cells, mean regret 0.0066) |
| Generic comparator wins or effect is scale/calibration ambiguity | EGRCR (generic critic wins every estimation diagnostic; factorized edge 0.012, parked); EOCIV B9R1 (global and every leave-one `Delta_R` negative) |
| Positive but narrow | CBSC (exact protocol value "positive and narrow"); EOCIV A1 alone (small positive) |
| Learner never reached competence | UCOPE B1 (`0/3` competent seeds in each of three arms) |

Three further facts: ACVC's Convergence verdict is literally `RECAST_HEADROOM_FIRST`; SCDMP's only
authorized object is a relevance census with no learner; and almost every ACTIVE direction runs on
a toy host whose evidence is, by the spec, bounded to its declared population.

## 1. Diagnosis (inference)

The pattern is not an execution problem. Integrity, quarantine, and admission are working. The
pattern is a selection problem with three parts:

1. **Mechanisms are proposed before headroom is measured.** A mechanism can only show what the
   competent generic learner leaves on the table. Where that gap is small, every B result will be
   `NEITHER`, "narrow", or "generic wins", however carefully it is run.
2. **Comparators are tuned last.** `COMPARATOR_WEAK` is a recurring verdict because baseline
   tuning is treated as part of each direction's launch rather than as a shared, frozen asset.
3. **Several directions are systems questions in MARL clothing.** Receipt content, refresh
   currency, shadow reads, and similar information-flow questions do not have non-stationarity,
   credit assignment, partial observability, or agent-count scaling as their binding constraint.
   For those, a same-information generic learner is the expected winner, and the negatives are
   consistent with that.

A fourth, economic consequence: with twenty-two toy ladders, usage per valid result is high and
the information per result is low. `AGENTS.md` §5 names usage-per-valid-result as the ranking
currency across directions, but the snapshot does not yet show it retiring anything.

## 2. Five principles for the next phase

Each principle is stated with where it sits in the existing rules, so that nothing below becomes
a new launch gate. §11.4 of the evidence spec permits exactly four B launch conditions; all of the
following are **investment rules** (spec §8.1 items 1–3) or **card content**, never gates.

### P1. Headroom before mechanism

The first rung of any direction is an A/RECON measurement of the gap between a stated upper
reference and the tuned generic learner on the same host with the same information. Upper
references in this repository already exist for the corridor (switching oracle, every fixed-`k`
oracle) and can be a DP/Bayes solution, an oracle with privileged information, or the best arm of
a comparator sweep. The measured gap is compared with a **minimum effect of interest (MEI)**: the
smallest improvement the owner would still care about. Below the MEI, the direction is not
invested in; no B is launched, not because a gate refuses it, but because Portfolio declines to
spend (spec §8.1 item 1). ACVC's `RECAST_HEADROOM_FIRST` is the template.

**[DECIDE] MEI.** Recommendation: two numbers, both relative. (a) Headroom must be at least 5% of
the tuned-baseline return on the host before a mechanism is investigated. (b) A mechanism result
counts as a positive B signal only when it closes at least 25% of the measured headroom. Absolute
edges such as 0.012 are then read against the gap they sit in, not on their own.

### P2. The comparator is a first-class object

For each host family (relay corridor; UAV scenario 1; the small exact panels) there is one
**baseline set**: tuned generic learners (the D0 fixed-`k` sweep, a flat MAPPO-style policy,
HMASD as shipped), fixed seeds, complete curves, the exposure line, stored as ordinary result
documents plus the exact runner configuration. Every direction on that host compares against the
baseline set, and may not weaken it. Two variance controls become defaults: paired seeds across
arms and common random numbers (both arms consume the same environment randomness stream) wherever
the host allows. Under the engineering scope spec this is a directory of frozen results and
configs, not a registry, validator, or guard.

**[ASK]** Location: `docs/research/baselines/<host>/` for the result documents and
`experiments/baselines/<host>/` for the runner configs. Default if unanswered.

### P3. Invest only where a MARL structure is the binding constraint

Before a direction is opened or continued, its card names which one of the following the generic
same-information learner cannot solve on the host: (a) agent-count scaling and roster change, (b)
temporal abstraction and termination, (c) multi-agent credit assignment, (d) non-stationarity or
partial observability caused by other agents. A direction that names none is a systems or
information-flow question; it is legitimate work but is not funded from the MARL portfolio. This
is the owner's own research order (spec §11.1: single-agent or bandit inspiration, then a B ladder)
with one extra question at the entry: *why would the inspiration's single-agent answer not suffice
here?*

The two untying directions each sit on exactly one structure, (b) for FSD and (a) for VNFC, which
is the substantive reason they head the investment wave.

### P4. Fewer directions, deeper ladders, production host sooner

Collapse to four or five ACTIVE directions and PARK the rest at their current clean boundaries.
Use the released capacity to move the head directions from toy hosts to the multi-UAV host on the
remote node, which is what the `REMOTE_FIRST` decision of 2026-09-04 now makes affordable. Toy
evidence stays valid for its declared population, but the portfolio claim is about multi-UAV
control, and only a B on that host can move it.

### P5. Write the three readings before the run

Every B card records, at freeze time, what each of three outcomes means and what it triggers:
effect above the MEI share (next rung), inside it (`NEITHER`, and which of PARK / recast / repeat
is recommended), and opposite in sign (close the object). This is intake text written early, in
the options-and-recommendation form the decision ladder already uses. It is not a pre-registered
failure boundary in the C sense and does not hold a launch; its purpose is that a `NEITHER` result
carries its own recommendation instead of returning to Convergence for interpretation.

## 3. Actions

| # | Action | Tier | Who | Record |
| --- | --- | --- | --- | --- |
| A1 | Portfolio-wide headroom census: for each ACTIVE direction, one A/RECON object measuring (upper reference − tuned baseline) on its current host, no learner. Directions whose current object already is such a measurement (ACVC R01, SCDMP A01) count as done when their result is in. | Object per direction; the census as a whole is Portfolio | DMs execute; Root aggregates | one intake section per direction; one summary table in a new decision record |
| A2 | Build the baseline sets of P2 for the corridor and scenario 1 first, reusing E2's D0 sweep and E0's exposure probes where they already exist. | Object | Root as CM, or one routine implementer | `docs/research/baselines/` (pending [ASK]) |
| A3 | Apply P4: ratify the ACTIVE set of §4 and PARK the rest. | Portfolio | owner ratifies from the record | `docs/research/portfolio/decisions/2026-09-XX-marl-exploration-focus.md` |
| A4 | For FSD and VNFC, freeze the first multi-UAV-host B object as the next rung after E3 / R02 respectively, routed to `wsl_4070`. | Direction | DM proposes; owner decides while present | direction intake and card |
| A5 | Add a usage-per-valid-result column to the PORTFOLIO table and fill it from existing run summaries. | Root bookkeeping | Root | `PORTFOLIO.md` |
| A6 | Add the P3 "binding structure" line and the P5 three-reading block to the card template used by new objects. | Object | Root | the DM skill's card section |

A1 and A2 do not wait on A3; they are reversible, Object-tier work under the standing delegation.
A3 and A4 wait on the owner. A5 and A6 are edits to Root-owned documents.

## 4. Proposed ACTIVE set and dispositions [DECIDE]

Classification is provisional, made from the one-line portfolio reasons, and each DM should
confirm the "binding structure" entry against its own `DIRECTION.md` before A3 is ratified.

| Direction | Binding MARL structure (P3) | Current evidence position | Proposed disposition |
| --- | --- | --- | --- |
| flexible_skill_duration | (b) temporal abstraction | E2 `NEITHER`; E3 running, 3/6 valid | **ACTIVE-CORE**; after E3, A4 |
| variable_n_fleet_churn | (a) roster / N | R02 admitted, awaiting remote preflight | **ACTIVE-CORE**; after R02, A4 |
| finite_resource_relational_inductive_efficiency | (a)/(c) relational bias under finite resources | root 001 live | **ACTIVE**; headroom census after root 001 |
| semigroup_consistent_duration_model_policy | (b) duration model | A01 census only, no B authorized | **ACTIVE-IF-HEADROOM**; A01 is the census |
| acvc | (d) history value under partial observability | R01 headroom object active | **ACTIVE-IF-HEADROOM**; the P1 template |
| ucope | unclear from the snapshot | B1 `0/3` competent in every arm | **HOLD**: competence first, then headroom; no new mechanism object until a competent baseline exists on its host |
| capability_bound_semantic_currentness | information flow; (d) only if the DM shows it | exact value positive and narrow | **ACTIVE-IF-HEADROOM**: read the existing "narrow" value against the MEI; if below, PARK |
| commitment_residual_triggered_options | (b) option termination | `COMPARATOR_WEAK` | **ACTIVE-IF-HEADROOM** after the RAW-only trace |
| degraded_incumbent_shadow_handover | (a) agent replacement | conformance CM, no launch | **ACTIVE-IF-HEADROOM**; fusion candidate with VNFC |
| roster_consistent_latent_exploration | (a) roster churn recovery | B/EXPLORE toy | fusion candidate with VNFC [DECIDE] |
| vsp_03 | (b) event-aware termination | B/EXPLORE toy | fusion candidate with FSD E4 (random-duration events) [DECIDE] |
| vsp_02 | optimizer state across roster ages | B/EXPLORE toy | PARK-CANDIDATE; revisit inside VNFC if optimizer carry becomes its question |
| vsp_c1 | identity-by-period composition | toy, no production host | PARK-CANDIDATE |
| metric_ground_transport_allocation | (c) allocation | two C objects stopped before efficacy | PARK-CANDIDATE unless the census shows headroom |
| eociv_lite | information flow | B9R1 negative, at Convergence | PARK-CANDIDATE |
| ec4g_r1 | information flow (receipt content) | prior B adverse | PARK-CANDIDATE |
| recct_lite | information flow (target intervention) | one-port result closes that host | PARK-CANDIDATE |
| vap_folr_core | information flow (typed/generic/reset) | B3 after writer repair | PARK-CANDIDATE |
| scope_1s | systems (authentication toy) | toy wrapper | PARK-CANDIDATE |
| expressibility_gated_renewal_credit_relay | (c) credit | PARKED 2026-09-04 | unchanged |
| orbit_shadow_read, active_post_churn_population_flow_identification | — | PARKED | unchanged |

Net effect if ratified as proposed: five ACTIVE (FSD, VNFC, FRRIE, SCDMP, ACVC), one HOLD (UCOPE),
three conditional on their own census (CBSC, CRTO, DISH), two fusion questions, and the rest
PARKED at clean boundaries. PARK is reversible and, per spec §7, is not a scientific negative.

## 5. What Codex Root does with this document

Before ratification (now, under the standing delegation):

1. Open A1 as one Object-tier item per ACTIVE direction, using ACVC R01's structure as the pattern
   and logging each in the audit ledger.
2. Open A2 for the corridor and scenario 1.
3. Apply A5 and A6.

After the owner ratifies A3 (and settles the [DECIDE] items in §6):

4. Write the decision record, update the PORTFOLIO table, PARK the named directions at their
   current clean boundaries, and record the two fusion decisions.
5. Route the FSD and VNFC production-host objects (A4) through their DMs, remote-first.

Nothing here authorizes a B launch, changes a frozen object, or alters a comparator, budget,
dtype, device, RNG, or claim meaning of any live run.

## 6. Decisions for the owner

1. **[DECIDE]** The MEI numbers of P1 (recommended 5% headroom floor, 25% closure share).
2. **[DECIDE]** The ACTIVE set and PARK list of §4, as proposed or amended.
3. **[DECIDE]** Fusion: roster_consistent_latent_exploration into VNFC; vsp_03 into FSD E4.
4. **[DECIDE]** UCOPE HOLD: competence repair before any further mechanism object.
5. **[ASK]** Baseline-set location (default `docs/research/baselines/`, `experiments/baselines/`).
6. **[ASK]** Whether A5's usage column is filled retroactively from existing summaries or only
   from the next result onward (default: retroactively where a summary records wall time).

## 7. Out of scope

This document does not touch `AGENTS.md`, `.codex/`, `.agents/`, or `CLAUDE.md`; does not
propose new machinery from the engineering scope spec's default-prohibited list; and does not
reinterpret any recorded result. The classification in §4 is a proposal for a Portfolio-tier
decision and has no effect until ratified.

## 8. Addendum 2026-09-04 07:35 PDT: owner stance after Codex Root's review

Codex Root recommended against approving this draft as a package, on the ground that it mixed
diagnostic method with Portfolio policy that would narrow scope, and that most ACTIVE directions
lack the measurement assets P1 presumes (a same-information upper reference and a tuned generic
baseline), so a hard P1 would stop them for missing assets rather than for small headroom. The
owner agreed and added that the Codex loop is deliberately unbounded in direction count. The
resulting stance, now in `docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md`:

- P1 kept as diagnosis and sequencing, not a threshold; training a baseline is B, not A.
- The 5%/25% numbers withdrawn; each card declares its own MEI.
- P2 kept as reusable evidence packages, never a mandatory comparator.
- P3 kept as a classification field; `systems / information flow` excludes nothing.
- P4 withdrawn: all ACTIVE directions continue in parallel; sequencing is not disposition.
- §4's fusion proposals deferred; hosts and baselines are shared instead.
- UCOPE stays ACTIVE with the order competent baseline, headroom, mechanism.
- A4 becomes "prepare a direction-level proposal", with no pre-authorized B.
- A5 uses two compute measures with node, device and missing values kept.
- A6 adds description fields only.

The author's residual view, for the record: the case for fewer, deeper ladders was a Claude-side
default and does not hold where agent parallelism is free; the binding constraints on the Codex
loop are compute and owner attention, which the sequencing rule and the owner surfaces address.
