# D7 design, and a prior-art collision outside the last fence

You ruled on 2026-07-25 that R30 KEEP/SET carries the variable-`k` line, that the
primitive is per-agent renewal urgency, that D1 is dropped, and that D7 — an
instrumented reward-pure R30 renewal diagnostic — is the first
resource-consuming action. D0, the zero-compute carrier and estimand derivation,
is complete and is in the evidence below.

Two things have since come out of reading the code, and one of them may bear on
your ordering.

## A. What reading the carrier established

Both are in `D0_CARRIER_AND_ESTIMAND.md` with anchors; stated here so the
questions are self-contained.

1. **Only one of three branches in `act_sequence` contains a renewal decision.**
   Under `native_categorical_edit`, KEEP is a post-hoc *label* applied when the
   sampled skill happens to equal the incumbent, and `keep_head` is bypassed
   entirely. A "KEEP rate" measured there is the collision rate of the skill
   categorical. Both flags default false, so the live lane is the learned-keep
   branch and the carrier is eligible — but the metric name is identical across
   all three branches.

2. **The policy-update boundary opens a fresh segment record while the
   commitment continues** — `segments.renew(..., switched=False)` with
   `skill_age` carried forward. Lifetime counted from segment records is
   therefore fragmented by update cadence, not by policy. Under R30 this is
   currently latent rather than active: `process_update` empties its segment list
   for R30 and returns early, so those metrics are hardcoded zero. The R30 lane
   emits **no lifetime measurement at all**, and the obvious way to add one is
   the fragmented way.

## B. The prior-art collision

Your fence was one stage commit, and you noted in Q6c that the earlier R30
ruling's raw scope was not included. A four-run lineage from 2026-07-16 was
outside it and bears directly on D7 and D8:

| Run | Status | Result |
|---|---|---|
| `EXP-20260716-r42-irr` | `VALID_FAIL` | Retired |
| `EXP-20260716-r43-nrc-k50` | `INVALID_R43_FIXED_ANCHOR_LOST` | Comparator broke; treatment uninterpretable |
| `EXP-20260716-r44-fsnrc-k50` | `VALID_FAIL_R44_FSNRC` | A learned KEEP/RENEW gate collapsed to always-RENEW |
| `EXP-20260716-r45-sdra-g0` | `VALID_FAIL_R45_SDRA_IDENTIFIABILITY` | Renewal credit not identifiable from natural support |

R44 is the sharp one. It froze a service-capable source, trained only a renewal
residual actor and critic, and measured: treatment actor relative drift
`0.353245` across 3,000/3,000 finite nonzero gradient exposures — a live path —
yet deterministic discordance `0`, full-sync RENEW `1.0`, minimum per-agent
KEEP/RENEW marginal `0`. The gate learned something and behaved as fixed refresh.

R45 then tested whether renewal credit was identifiable at all on that substrate
and failed on overlap.

**My reading**, which I want checked rather than accepted: these do not retire
D7 or D8, because R44's own decision line says *"the result does not retire a
structurally new joint co-adaptive asynchronous-skill route"*, and R45's
retirement is bound to the Alice--Bob K50 temporal substrate. The R30 lane is a
different substrate, a different code tree (`hmasd/` versus
`ha_ctse_process/`), a different clock, and a different claim. But they do impose
constraints I have written into D7: do not bolt renewal onto a frozen
controller, do not identify renewal credit from natural support, and reuse
R43/R44's M3 collapse gates so a collapse here is directly comparable.

---

# Questions

## Q1 — does the R42--R45 lineage bind this line?

Rule on my reading in B.

- **If it does not bind**: are the three constraints I extracted the right ones,
  and is any of them wrong or missing? In particular, is "do not freeze the
  controller" the correct lesson from R44, or is the correct lesson narrower —
  that *next-check* credit specifically was the defect?
- **If it does bind D8** but not D7: say so explicitly, because D8 is currently
  ordered second and I would otherwise build it after D7 returns.
- **If it binds both**: what survives? The ledger's portfolio would need a
  structurally different edge, and I would rather learn that now than after a
  run.

## Q2 — which source does D7 run on?

Two candidates, answering different questions.

- **The toy** `two_timescale_role_free_actions`: ground-truth timescales (fast
  target flips every `k0=5`, slow every `30`), emergent roles never named to the
  agent, no intrinsic reward, task-only bounded reward. Heterogeneity is true
  *by construction*, so it cannot establish that the source has it — it tests
  whether the carrier can express it. Cheap. Its one completed run
  (`EXP-20260715-r39-native-hmasd-toy-credit`, match/slow/fast
  `0.455/0.465/0.445`, `VALID_FAIL` on a credit anchor) ran under the
  native-categorical branch where KEEP is not a decision, so it does not speak
  to the carrier.
- **The main scenario**: what the paper claims about, and where heterogeneity is
  genuinely open. Your D7 wording — "whether the source exhibits heterogeneous
  renewal urgency" — points here.

**My proposal**: toy first as a *positive control for the carrier*. If R30
learned-keep cannot express two timescales that provably exist, a main-scenario
run measures a controller that cannot represent the answer, and R44 is precedent
for a live gradient path coexisting with collapsed behaviour.

- **If you accept the positive control**: what is its pass condition? I would
  propose per-agent KEEP-hazard separation tracking the known fast/slow split,
  but I should not set the threshold I will be graded against.
- **If you reject it**: is the objection that the toy's ground truth makes the
  control uninformative, or that its two-agent shared-reward structure cannot
  express per-agent renewal urgency at all? Those imply different substitutes.
- **If neither source is right**: name what the source must contain.

## Q3 — is the interventional half required in D7?

D0 defines the estimand as a counterfactual — force KEEP against force SET from
the same pre-decision history, same RNG, external return only. Your Q2a called a
paired diagnostic the preferred first source-level evidence, and R45 is direct
evidence that natural-support observation fails here.

The cost is asymmetric. Feasibility, checked:

- forced KEEP/RENEW with teacher-forced factors and torch RNG capture exists,
  but on the `hmasd/` tree (`scripts/r43_native_renewal.py`);
- environment snapshot/restore including RNG exists **only** for
  `alice_bob_asymmetric_cycles` — the substrate R45 retired;
- checkpoints do **not** store `active_skills`, `skill_age` or
  `has_active_skill`, so commitment state cannot be restored from one.

So on any non-Alice--Bob source, the paired branch needs either a new snapshot
hook in the environment or common-random-number replay from a shared prefix.
This is the largest build item in D7.

- **If interventional is required in D7**: is CRN replay from a shared prefix an
  acceptable substitute for state restore, given the two branches diverge only
  after the intervention point? If not, adding a snapshot hook is the answer and
  I would like that said plainly.
- **If descriptive-first is acceptable**: what would make the descriptive half
  *sufficient* to decide whether D8 is worth building — since by your own Q2a
  ruling hazard and dwell time are outcomes, not the primitive?

## Q4 — does the cheap route qualify?

Your Q3a listed as ordering-changing: *"if a qualified checkpoint and
reproducible trajectory path can answer D7 without another training run, that
cheaper route moves ahead."*

Checkpoints do not carry commitment state, so training-time lifetimes cannot be
reconstructed. But a **fresh rollout under a frozen policy** needs no training —
load a qualified R30 checkpoint, roll out, measure natural hazard, lifetime and
censoring. `export_substrate_gate.py` already loads a checkpoint and rolls out
eval episodes.

- **If that qualifies for D7's descriptive half**: it changes D7's compute cost
  from a training run to an evaluation, and I would do it first. Does it also
  carry the interventional half, given the policy is frozen and therefore the
  intervention cannot feed back into learning?
- **If it does not qualify**: is the objection that a frozen policy's hazard is
  not the training-time hazard the thesis is about?

Note two cautions on that host: its per-segment export inherits the
fragmentation trap in A2, and it emits `role_label` / `role_scores` fields with
named relay/service semantics that your Q2 ruling forbids as the primitive.

## Q5 — comparator and acceptance

- The claim is against the **best shared fixed lifetime**, which implies a sweep
  and a larger envelope than one paired run. Is a sweep required for D7, or does
  D7 pair against a single defensible fixed setting with the sweep deferred to
  the arm that makes the claim?
- What is the acceptance criterion for "heterogeneous renewal urgency
  established"? I need an effect size and a separation condition fixed before
  the run, and I should not choose the bar I will be graded against.
- Should D7 report the R43/R44 M3 quantities verbatim — discordance, full-sync
  rate, per-agent marginals, target entropy over `log(n)`, same-label renewal —
  for direct comparability with the retired route?

## Q6 — anything above that you would reorder

If any answer above changes the ledger ordering you set, say so and give the
revised order. Nothing has been built; changing it now is free.

## Evidence to read

- `docs/research/designs/D0_CARRIER_AND_ESTIMAND.md`
- `docs/research/designs/D7_R30_RENEWAL_DIAGNOSTIC.md`
- `docs/project/RESEARCH_GOAL.md`
- `docs/project/EXPLORATION_LEDGER.md`
- `docs/project/ExpRecord.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `ha_ctse_process/r30_fixed_clock.py`
- `ha_ctse_process/config.py`
- `scripts/r43_native_renewal.py`
- `envs/pettingzoo/two_timescale_role_free_actions.py`
- `ha_ctse_process/export_substrate_gate.py`
