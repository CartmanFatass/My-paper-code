# D7 — instrumented R30 renewal-process diagnostic

```text
id=D7
status=design drafted, open selections pending external review
depends_on=D0_CARRIER_AND_ESTIMAND.md
source_ruling=20260725_research_direction_and_ledger
prior_art=EXP-20260716-r42/r43/r44/r45 -- outside that ruling's evidence fence
```

The ruling's first resource-consuming action. Its purpose is bounded: establish
whether the source exhibits **heterogeneous renewal urgency**, describe natural
R30 hazard and lifetime behaviour, rule out truncation/exposure/reward artefacts,
and decide whether D8 is worth building. It does not test the final constrained
algorithm.

## 1. Prior art the ruling did not see

The direction round's fence was one stage commit, and Pro noted in Q6c that the
earlier R30 ruling's raw scope was not included. A four-experiment lineage from
2026-07-16 bears directly on D7 and D8, and it was outside that fence.

| Run | Status | What it established |
|---|---|---|
| `EXP-20260716-r42-irr` | `VALID_FAIL` | Retired; a zero-output residual on incumbent roster logits |
| `EXP-20260716-r43-nrc-k50` | `INVALID_R43_FIXED_ANCHOR_LOST` | Comparator broke — treatment numbers have no interpretation |
| `EXP-20260716-r44-fsnrc-k50` | `VALID_FAIL_R44_FSNRC` | **A learned KEEP/RENEW gate collapsed to always-RENEW** |
| `EXP-20260716-r45-sdra-g0` | `VALID_FAIL_R45_SDRA_IDENTIFIABILITY` | **Renewal credit was not identifiable from natural support** |

### Why this does not retire D7 or D8

R44's decision line is explicitly scoped: it retires the frozen-source K50
renewal adapter and its next-check credit, and states that *"the result does not
retire a structurally new joint co-adaptive asynchronous-skill route."* The R30
lane is exactly that route — the controller co-adapts rather than carrying a
residual head on a frozen source. R45's retirement is likewise bound to the
Alice–Bob K50 temporal substrate.

Different substrate, different codebase (`hmasd/` original tree versus
`ha_ctse_process/`), different clock (`k0=50` global versus `skill_interval`),
and a different claim — theirs was service-preserving temporal decoupling, ours
is finite-budget search efficiency.

### Three constraints it does impose, which D7 must carry

1. **Do not bolt a renewal head onto a frozen controller.** R44 froze the source
   and trained only a renewal residual. The actor drifted `0.353` across
   3,000/3,000 finite nonzero gradient exposures — a live path, not a
   disconnected one — and behaviour still collapsed to full-sync RENEW `1.0`
   with minimum per-agent marginal `0`. Renewal structure and skill policy have
   to co-adapt, which the R30 carrier does by construction.
2. **Do not identify renewal credit from natural support.** R45 failed exactly
   there — M1 overlap failed. D7's core measurement must therefore be
   **interventional**, forcing KEEP against SET from a shared history, not
   inferred from whatever the natural policy happened to do. This independently
   reproduces the ruling's Q2a preference.
3. **Collapse gates already exist and are reusable.** R43/R44's M3 is a ready
   instrument: discordance, full-sync rate, per-agent KEEP/RENEW marginals,
   target entropy over `log(n)`, same-label renewal. D7 should report these
   rather than invent new ones, so a collapse here is directly comparable to
   the one already on record.

## 2. Two components

D7 is descriptive **and** interventional. The descriptive half alone is what the
ruling called diagnostic-only; the interventional half is what establishes the
primitive.

### 2a. Descriptive — natural renewal process

Under the live learned-keep branch, reward-pure, no entropy floor:

- `sigmoid(keep_logit)` by commitment age and by context;
- realized lifetime from `skill_age` at genuine SET — **never** from segment
  records, which fragment at every policy update (D0 §1);
- age-conditioned renewal hazard, which no current metric emits;
- termination reason resolved to D0's six censoring sources, with forced renewal
  and the policy-update boundary separated;
- right-censored commitments as their own reported category;
- both decision-count and primitive-time weightings for every distribution;
- exposure: environment interactions, high-level samples, and optimizer
  contribution by lifetime stratum, reported separately;
- the R43/R44 M3 quantities, for comparability with the retired route.

### 2b. Interventional — the estimand itself

At a check opportunity with history `h_{i,t}`, for a single agent `i`:

```text
branch A: force KEEP for i        branch B: force SET for i
all other agents identical, same RNG stream, roll forward H steps
U_i(t, Δ) = E[G | B] - E[G | A]     (external return only)
```

Heterogeneous renewal urgency exists if `U_i` separates across agents and
contexts by more than its paired noise band.

**Feasibility, checked rather than assumed.** The pieces exist but are not
assembled for this lane:

| Needed | State |
|---|---|
| Forced KEEP/RENEW with teacher-forced factors | Exists — `scripts/r43_native_renewal.py:258-265, 381`, but on the `hmasd/` tree |
| Torch RNG capture/restore | Exists — `r43_native_renewal.py:47-57`; also `standalone_agent.py:9540,9575` |
| Env state snapshot with RNG | Exists **only** for `alice_bob_asymmetric_cycles` (`:103-151`) |
| Per-agent commitment state in checkpoints | **Absent** — `active_skills`, `skill_age`, `has_active_skill` are not checkpointed; backed up and restored around eval only |

Consequence: a true state-restore counterfactual is available off the shelf only
on Alice–Bob — the substrate R45 retired. On any other scenario the paired branch
must be produced by common-random-number replay from a shared prefix rather than
by snapshot/restore, or by adding a snapshot hook to the target env.

**This is the single largest build item in D7 and the main reason its cost is
`medium` rather than `small`.**

## 3. A cheaper route exists for 2a, and should be checked first

Checkpoints do not carry commitment state, so training-time lifetimes cannot be
reconstructed from one. But a **fresh rollout under a frozen policy** needs no
training: load a qualified R30 checkpoint, roll out, and measure natural hazard,
lifetime and censoring directly.

That answers all of 2a at evaluation cost rather than training cost. The ruling
listed exactly this as an ordering-changing observation — *"if a qualified
checkpoint and reproducible trajectory path can answer D7 without another
training run, that cheaper route moves ahead."*

`export_substrate_gate.py:505` already loads a checkpoint and rolls out eval
episodes deterministically, exporting per-segment rows. It is the natural host,
with two cautions: its per-segment export inherits the fragmentation trap, and
its `role_label` / `role_scores` fields carry named relay/service semantics that
D0 forbids as the primitive.

**Action: identify whether a qualified R31–R33 R30 checkpoint exists before
scoping any training run.**

## 4. Open selections — external review, not derivation

1. **Source.** The toy `two_timescale_role_free_actions` has ground-truth
   timescales (fast `k0=5`, slow `30`), no intrinsic reward and emergent roles —
   but heterogeneity there is true *by construction*, so it tests whether the
   carrier can express it, not whether the source has it. The main scenario is
   what the paper claims about. These answer different questions and the ruling's
   D7 wording ("whether the source exhibits") points at the latter.

   Proposed: run the toy first as a **positive control for the carrier**. If R30
   learned-keep cannot express two timescales that provably exist, a
   main-scenario run measures a controller that cannot represent the answer. Note
   the toy's one completed run (`EXP-20260715-r39-native-hmasd-toy-credit`,
   `0.455/0.465/0.445`) used the native-categorical branch where KEEP is not a
   decision, so it does not speak to the carrier.

2. **Registered utility level** for the search-cost claim, and on which source it
   is registered.

3. **Acceptance criterion** for "heterogeneous renewal urgency established" —
   effect size and separation, fixed before the run.

4. **Whether the paired fixed-lifetime control is a sweep or a single setting.**
   The claim is against the *best* shared fixed lifetime, which implies a sweep
   and therefore a larger compute envelope.

## 5. What is settled and can be built now

Independent of every item in §4, because D0 fixed them:

- the hazard and lifetime computation from `skill_age`, not segment records;
- the six-way termination-reason attribution;
- right-censoring as a reported category;
- dual weighting;
- branch recording (`native_categorical_edit` / `force_refresh` / learned-keep);
- the R43/R44 M3 comparability block.

Build proceeds on these while the review round is outstanding.
