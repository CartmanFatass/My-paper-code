# The first variable-k algorithm decision under the algorithm-first course ruling

Touchpoint 1 of workflow 5. One decision is requested (see **Decision
requested**), tree-structured. Discarding the framing of any branch — or the
whole tree — is a legitimate answer.

## Variable-k relevance

This round selects the first conclusion-bearing variable-k experiment itself;
its outcome is the next thing we can say about variable k.

## Frozen inputs (not review surface)

- **User course ruling 2026-08-01: algorithm-first.** The ten-iteration grant
  is spent on variable-k MARL algorithm exploration on the toy surface. The
  entire D7.S/B3-L provenance line is HELD — the B3-L design you froze stays
  frozen, its partial implementation is archived in-tree, the replay gate is
  unrun, and steps N and O are not to be executed. This is a user scope
  ruling, not reviewable here; it changes what work runs next, not the truth
  of any prior ruling of yours.
- A theme-drift guard is installed at the round preflight (every question
  must answer `docs/project/RESEARCH_GOAL.md`'s standing check — this
  section). Disclosure only.
- `docs/project/RESEARCH_GOAL.md` is the user-owned goal statement; the paper
  claim, primitive (per-agent state-dependent renewal urgency) and carrier
  (R30 KEEP/SET as primary and unrestricted comparator; `legacy_duration` as
  frozen comparator) were set by your ruling of 2026-07-25 and stand.
- Toy environments are the default discovery surface; heavy UAV runs need a
  recorded promotion and are not on the table this round.

## Repository facts (verified at stage_commit; scout sweep, PM spot-checks)

1. Carrier code exists and dispatches: `ha_ctse_process/r30_fixed_clock.py`
   (`KEEP_TOKEN`/`SET_TOKEN` at :15-16, `keep_logit` emission at :200);
   controller dispatch at `ha_ctse_process/train.py:2724-2727`; current
   default `high_controller="legacy_duration"`
   (`ha_ctse_process/config.py:25`), R30 selected explicitly — the toy config
   `config_d7_2b_toy_learned_keep.py:52` (repo root) already selects
   `r30_fixed_clock_ar_edit` on `two_timescale_role_free_actions`.
2. `skill_lifetime_candidates = (3, 7, 13, 24)` (`ha_ctse_process/config.py:40`).
   **No completed run exists under this configuration** (the completed legacy
   arm used `(1,2,3,4)` at `k0=10`).
3. SMDP high-level discount and bootstrap default True
   (`ha_ctse_process/config.py:384-385`).
4. The observation/check clock is shared per environment
   (`ha_ctse_process/standalone_agent.py:2802`, decrement at :3149) — R30
   unties realized renewal interval, not the offered-decision clock, exactly
   as the goal document's claim boundary records.
5. **No per-step, per-agent KEEP/SET trace is persisted anywhere.** Metrics
   are aggregated per update (`renewal_agents_mean`,
   `renewal_pairwise_corr_mean`); age-conditioned renewal hazard — the
   primitive's own quantity — is not measurable from any existing artifact.
   [Scout-verified at stage_commit; confirms the goal document's 2026-07-25
   claim.]
6. **No learned renewal-class / regime mechanism exists in
   `ha_ctse_process/`** by token sweep (`renewal_class`, `renewal_regime`,
   `low_cardinality`, `stability_class`, `regime_head`, `urgency_class` — all
   absent). The constrained arm of the paper claim is unimplemented.
   [Negative result; the sweep is named so it can be checked.]
7. Toy surface available: `two_timescale_role_free_actions` (has the R30 toy
   config above), `alice_bob_asymmetric_cycles` (used by R47/R48 gates),
   `continuous_alice_bob`.
8. No cross-arm comparison analyzer or shared artifact schema exists for
   fixed-k vs R30. [Scout sweep.]
9. **Conflicting surface, flagged rather than resolved by me:**
   `RESEARCH_GOAL.md` (checked 2026-07-25) records "adaptive R30 arms
   completed and anchored R31–R33, with R33 recording R30 safety PASS", while
   the run-record/postmortem documents mark R31–R33 FAIL/RETIRE. Both are
   quoted as written; whether those anchors carry any weight for the next
   design is yours to say.

## Decision requested

**Under the user's algorithm-first ruling, what is the first
conclusion-bearing variable-k experiment (or smallest ordered sequence) on
the toy surface, and what is its smallest sufficient evidence design?**

Pre-walked branches — take one, modify one, or replace the structure:

- **B1 — heterogeneity existence first.** Establish that heterogeneous
  renewal urgency exists in a toy source. Name the environment, the
  measurement, and its artifact. Note fact 5: if the measurement needs a
  per-step trace, name the smallest instrumentation permitted so the
  apparatus stays inside the user's algorithm-first scope.
- **B2 — three-arm comparison first.** Fixed-k (candidates) vs unrestricted
  R30 vs a constrained arm on one toy environment under matched exposure.
  Note fact 6: the constrained mechanism does not exist; this branch implies
  designing it now, and the mechanism design is a scientific choice this
  round would need to carry.
- **B3 — anchors first.** Complete the never-run fixed-k `(3,7,13,24)` arm
  and an unrestricted R30 arm on one toy environment as baselines, deferring
  the constrained mechanism one workflow.
- **B4 — none of these.** Name the smallest missing prerequisite.

## Required response sections

1. `RULING` — the selected experiment or sequence, with environment,
   controller arms, and what claim from `RESEARCH_GOAL.md` it advances.
2. `MEASUREMENT` — the registered quantities and the artifact that must
   exist for them (including any per-step trace you order, bounded).
3. `EVIDENCE_DESIGN` — seeds/episodes/exposure matching and the acceptance
   and invalidity branches, at the smallest sufficient size.
4. `CORRECTIONS` — any repository fact above that is wrong, and anything
   this question's structure hides.

## Read boundary declaration

No run is in flight alongside this round. Nothing is read from any
in-flight artifact before this ruling lands.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/RESEARCH_GOAL.md`
- `ha_ctse_process/r30_fixed_clock.py`
- `ha_ctse_process/config.py`
- `ha_ctse_process/train.py`
- `ha_ctse_process/standalone_agent.py`
- `config_d7_2b_toy_learned_keep.py`
- `envs/pettingzoo/two_timescale_role_free_actions.py`
- `envs/pettingzoo/alice_bob_asymmetric_cycles.py`
- `docs/project/ExpRecord.md`
