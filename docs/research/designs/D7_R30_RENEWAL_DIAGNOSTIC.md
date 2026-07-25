# D7 — R30 renewal-urgency diagnostic

```text
id=D7
status=ruled 2026-07-25, MODIFY BEFORE EXECUTION -- staged, not one paired run
depends_on=D0_CARRIER_AND_ESTIMAND.md (estimands, clocks, censoring)
rulings=20260725_research_direction_and_ledger, 20260725_d7_design_and_prior_art
```

D7 asks three things: does the **source** contain heterogeneous renewal urgency,
can the **carrier** express it, and does natural R30 behaviour **align** with it.
It does not test the constrained algorithm and does not make the paper's
comparative claim.

## The shape changed

D7 is no longer a single instrumented paired training run. It is a staged
diagnostic that runs the cheapest qualifying stage first:

| Stage | Action | Cost |
|---|---|---|
| **0** | Estimand completion — `U_opp` vs `U_pi`, `Δ`, `H`, continuation, normalization | **done**, zero |
| **1** | **Qualified-checkpoint preflight** — does an eligible learned-keep R30 checkpoint exist? | zero — a repository fact |
| **2A** | Frozen-policy audit on the intended source, *if* an eligible checkpoint exists | evaluation only |
| **2B** | Toy positive control, if no eligible checkpoint or 2A is negative/unresolved | one short training run |
| **3** | Main-scenario urgency audit, unless 2A settled it positively | evaluation or run |

A negative at 2A **cannot** retire the carrier: it fails to separate absent source
heterogeneity from an insufficient checkpoint, a bad skill policy, or
renewal-credit failure. A negative sends the line to 2B, not to the exit.

## Prior art — the corrected lesson

R42–R45 do not retire D7 or the co-adaptive R30 line. R44 was a valid negative
for a *frozen-source K50 renewal-timing route*; R45 retired natural-support
renewal-credit identification on the Alice–Bob K50 substrate. Both decisions are
explicitly local.

**My earlier reading was directionally right and too broad.** "Do not freeze the
controller" is not a durable theorem — R44 never isolated freezing from
next-check credit, its K50 substrate, the frozen source distribution, or the
overlay factorization. The narrower rule:

> Do not reproduce the *combination* of frozen skill policy, renewal-only
> adaptation, and the R44 credit horizon as the proposed mechanism. A frozen
> controller is legitimate as a negative or mechanism-matched control — just not
> as the candidate.

What R44 actually refutes: *a trainable binary renewal factor with a live gradient
path, attached to a frozen source under K50/next-check credit, is sufficient to
produce heterogeneous renewal behaviour.* Its actor moved, every gradient exposure
was finite and nonzero, and behaviour stayed full-sync renewal at zero minimum
marginal.

Consequence for D8: **D8-frozen is dropped; D8-coadaptive is live.** "Primitive
skill policy unchanged" must mean unchanged *architecture and information
contract*, not frozen weights. Read as frozen weights, D8 is R44 again.

The two surviving constraints hold: natural renewal frequency is descriptive and
never causal identification, and nonzero gradients plus parameter drift are not
evidence of behaviour — collapse gates precede interpretation.

## The interventional half is mandatory

Not optional, and descriptive-first cannot authorize D8. Natural hazard, KEEP
frequency and realized lifetime cannot distinguish useful persistence from
controller inertia, thin exploration, bad skill semantics, or a reward-insensitive
gate. At most they support *"the policy produces non-uniform renewal behaviour"* —
which is not *"the behaviour tracks beneficial re-decision"*.

### CRN replay is an acceptable substitute for a snapshot hook

A snapshot hook is not scientifically privileged; what matters is **equality of
the pre-intervention history**. Replay qualifies only with all of:

1. identical reset seed, environment ledger, policy snapshot, recurrent state,
   active skills, ages, masks, team context;
2. every action and random draw before the focal token reproduced exactly;
3. at the focal token, KEEP forced in one branch and SET in the other, with the
   SET skill generated under the frozen registered rule;
4. later autoregressive factors **regenerated** under the modified prefix from the
   same base random variables — *not* held at factual values;
5. matched counter-based or replayable streams for post-intervention environment
   and primitive-policy randomness;
6. an exact equality check, or registered tolerance, on the state immediately
   before the intervention;
7. no optimizer or policy update between paired branches.

R30 helps here: the conditional skill sample is drawn **even when KEEP is
selected** (`r30_fixed_clock.py:288-290`), so RNG consumption need not depend on
the outcome. But the forced path must still consume the same Bernoulli and
categorical base draws in both branches — a teacher-forced route that skips one
draw silently shifts every later random choice.

For the toy this is unusually strong: its only environment randomness is the
seeded initial target signs, and everything after is a deterministic function of
time and actions.

If the main environment holds mutable state or RNG consumption that cannot be
reconstructed and checked from reset plus prefix replay, a snapshot hook becomes
**mandatory** for stage 3.

## Stage 1 — RESULT: no qualified checkpoint exists

**Settled 2026-07-25, zero compute. D7.2A is unavailable; the route is D7.2B.**

| Where | Finding |
|---|---|
| `logs/` in this repository | **3** `.pt` files total, all under `20260723_cpu_natural_branch_typed_contract/formal_path_exercise` — a contract exercise, not R30 |
| `r31`–`r34` runs | Reference `high_controller: r30_fixed_clock_ar_edit` but **saved no checkpoints**; they point at an external source path. All four terminal statuses are `FAIL` / `RETIRE` |
| That external source checkpoint | `C:\project\HMASD\logs\r30_alice_bob_paired_64k_.../standalone_process_core_final.pt` — **absent** |
| The external `C:\project\HMASD` tree | Exists, and contains **zero** `.pt` files anywhere under `logs/` |
| `two_timescale_role_free_actions` run | No such run directory on disk, in either tree |

The R39 toy run and the R30 Alice–Bob checkpoint are cited in `ExpRecord.md` with
full paths, and neither artifact survives. **Recorded results outlived their
artifacts.** Nothing here depends on recovering them — but no result may be
re-derived from those runs, only cited.

Even had the Alice–Bob R30 checkpoint survived, it would likely fail the
source-match criterion below: Alice–Bob K50 is the substrate R45 retired.

Consequence: D7 needs compute after all. The toy positive control is the route,
and it needs a **new config** — the existing `config_r39_native_hmasd_toy.py` runs
native-categorical edit, where KEEP is not a decision, so it cannot exercise the
learned-keep carrier.

## Stage 1 — checkpoint eligibility criteria

A checkpoint qualifies only if the evidence record establishes all of:

- `high_controller = r30_fixed_clock_ar_edit`;
- learned-keep live — **not** native-categorical-edit, **not** force-refresh;
- source matches the D7 source being audited;
- external reward pure;
- entropy floors and forced-renewal interventions disabled or explicitly separated;
- adequate task/skill access;
- exact configuration and policy snapshot known.

Missing commitment state in checkpoints (`active_skills`, `skill_age`,
`has_active_skill`) blocks reconstruction of *past training-time trajectories*
only. It does not block a **fresh** rollout: load weights, reset environment and
commitment state, generate a reproducible prefix, branch at a chosen check.

Frozen evaluation carries the interventional half, because `U_pi` is
policy-conditional — freezing is in fact *desirable*, since both branches then
refer to one snapshot. What it cannot establish: how the behaviour emerged during
training, a search-cost curve, urgency stability across training, or whether D8
learns faster than unrestricted R30.

## Stage 2B — toy positive control

`two_timescale_role_free_actions` is accepted as the default carrier positive
control: identical constant local observations, centralized fast and slow targets
at 5 and 30 steps, a permutation-invariant shared reward, no environment-provided
role identity.

The shared reward is **not** an objection — at a given history the current
assignments break the instantaneous symmetry, so a focal KEEP/SET intervention has
a well-defined team-return effect. The property is per-agent-*time* urgency, not a
permanent identity.

It proves only: *given genuine heterogeneous temporal duties, can the learned-keep
carrier form different renewal behaviour?* It cannot show the main scenario
contains such duties.

Ground truth is used **in the evaluator only**. "Fast" and "slow" are never fed to
the policy. Evaluate primarily at checks where the fast target changes and the
slow one does not.

### Pass conditions, fixed before the run

**A — competence prerequisite**, read before any renewal behaviour:

```text
LCB95(slow-match) >= 0.75      LCB95(fast-match) >= 0.75
```

An exact match scores `1` and a zero action `0.5`, so `0.75` is a halfway access
floor rather than a threshold fitted to the outcome. Failure is
`NO_ACCESS_D7_TOY_POSITIVE_CONTROL` and **does not update R30 renewal capacity**.

**B — interventional urgency separation**, on mixed-urgency checks:

```text
LCB95( E[U~_flex - U~_stable] ) >= 0.20
LCB95( E[U~_flex] )             >= 0.10
UCB95( E[U~_stable] )           <= 0.05
```

**C — natural learned-keep alignment**, same checks:

```text
LCB95( P(SET|flex) - P(SET|stable) ) >= 0.50
LCB95( P(SET|flex) )   >= 0.75        LCB95( P(KEEP|stable) ) >= 0.75
UCB95( P(full-sync SET | mixed urgency) ) <= 0.25
```

Deliberately stronger than "nonzero discordance" — a positive control must
separate carrier access from a weak noisy tendency.

**Reading the combinations**: B passes and C fails → the capability is present but
the policy or credit does not use it. Both pass → proceed to the main source. A
fails → upstream access failure, no renewal conclusion. B fails despite A → the
learned skill support or the source does not expose urgency as registered.

## Stage 3 — source heterogeneity, label-free

On a discovery split, fit a two-regime predictor from permitted decision-time
information only — diagnostic, never updating the policy. On an **untouched**
audit split, episode- or ledger-disjoint:

```text
each predicted regime holds >= 20% of supported opportunities
LCB95( E[U~_high] )              >= 0.10
UCB95( E[U~_low] )               <= 0.05
LCB95( E[U~_high - U~_low] )     >= 0.20
```

If interventional `U` varies but no decision-time predictor transports to held-out
episodes, the result is `HETEROGENEOUS_BUT_NOT_LOW_CARDINALITY_PREDICTABLE` —
heterogeneous opportunity established, D8 **not** supported.

If no source competence or action support exists, report no-access rather than no
heterogeneity.

Natural SET probabilities are read only *after* source urgency is identified, as
aligned / unresolved / anti-aligned. Current-policy alignment is not part of the
source-heterogeneity gate.

## Collapse statistics — transfer, modify, exclude

**Transfer directly**: discordance rate; full-sync SET rate; per-agent KEEP/SET
marginals; normalized entropy of SET targets; actor and critic gradient-exposure
counts; parameter drift.

**Modify** — my earlier plan to reuse R43/R44's M3 *verbatim* was wrong:

- condition discordance and full-sync rates on **mixed-urgency** opportunities.
  Full-sync SET can be correct where every commitment genuinely needs renewal, so
  a pooled average misclassifies legitimate synchronized change as collapse;
- report full-sync **KEEP** as well as full-sync SET;
- add per-urgency-regime marginals, not only per-agent;
- retain branch identity and censoring reason.

**Do not interpret**: *same-label renewal* is **structurally impossible** under
learned-keep R30, because the incumbent is masked out of the SET distribution. A
reported zero is a tautology, not evidence against collapse. Record it as
`NOT_APPLICABLE_STRUCTURALLY_EXCLUDED`. Under native-categorical edit, incumbent
collisions are reported separately as a *categorical collision rate* and never as
KEEP behaviour.

## Comparator — no best-fixed sweep in D7

The full sweep is deferred to D8 or whichever arm makes the paper-level claim.
None of D7's three questions requires identifying the globally best shared fixed
lifetime.

For the toy, two analytically meaningful fixed controls: refresh every check (the
fast-duty extreme) and refresh every six checks (the slow-duty extreme). A
complete sweep over shared lifetimes 1..6 is acceptable **if evaluation-only and
cheap**, as source characterization rather than the paper's comparator.

For stage 3, one pre-existing defensible fixed controller suffices as an
access/context control.

The ledger entry must stop describing D7 as paired against the "strongest shared
fixed-lifetime control" in the paper-level sense.

## Host caution

`export_substrate_gate.py` is a **host, not an acceptable metric path as
written**: it exports completed `SegmentManager` records — the wrong unit for R30
lifetime per D0 §1 — and its role rows carry named `role_label`, `role_name` and
relay/service scores.

D7 must emit its own **event ledger keyed to genuine SET decisions and
`skill_age`**. Named relay/service fields may be retained only as *secondary
post-hoc validation* after label-free urgency is established, and must never
define the primary strata, enter the controller, set the acceptance branch, or
substitute for the paired estimand.

## Build items, unchanged by this ruling

- `sigmoid(keep_logit)` capture — `D7_KEEP_PROB_CAPTURE_SPEC.md`, the one
  unavoidable schema change;
- lifetime from `skill_age` at genuine SET, never from segment records;
- the four-way termination attribution of D0 §6, with the synthetic
  continuation-reopen invariant asserted explicitly;
- right-censored commitments as their own category;
- branch identity recorded per run.
