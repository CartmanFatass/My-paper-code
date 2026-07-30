# Scientific ruling — D7.S R4 rerun disposition

**Stage reviewed:** `45d876b9a78242c52d59373f5a8700ac1330dbfa`

## Overall disposition

# **DO NOT RETRACT THE R4 INVALID-REALIZATION DISPOSITION; DO NOT ACCEPT THE RERUN AS A FORMAL R4 RESULT**

Two narrower updates are supported:

1. The post-repair R4 rerun observed **no environment-generated charging-fall REJOIN on the main prefix trajectories** that led to event certification.
2. The registered episode-world key does **not** reproducibly determine an episode world across machines. That is a claim-blocking population-provenance defect, not merely a documentation issue.

The first update does not rehabilitate H or the earlier artifact, because the `roll_power.rejoin_events` counter does not cover the conclusion-bearing continuation paths. In particular, every focal SET continuation explicitly executes a **virtual REJOIN** after \(\Delta=10\), and the repair lives in that same `constructive_mixed_update(event="REJOIN")` branch. Environmental REJOINs during the subsequent 139- or 550-step continuations are also outside the prefix counter.

The second update prevents the post-repair rerun from carrying the frozen R4 population claim. It remains a valid within-run, realized-world observation, but its registered episode identifiers do not identify a reproducible evidence population.

| Requested decision | Ruling |
|---|---|
| **4a — retract H’s invalid disposition?** | **No** |
| **4b — retract it for the earlier R4 artifact?** | **No** |
| **6a — does the rerun carry R4’s conclusion?** | **No** |
| **6b — missing property** | Reproducible evidence-population identity, not necessarily bit-identical final estimates |
| **6c — replication or insensitivity?** | Neither formally; it is exploratory branch robustness under unregistered world variation |
| **Decision three — severity** | Blocking repair before any formal or published R4 claim |

---

# 1. Decision 4a — H’s disposition

## Ruling: **no retraction**

The wrong-namespace probe and its claim that environment REJOINs occurred in H’s R4 population are correctly withdrawn. That does **not** establish that the source-assignment repair was inert on all paths that generated H’s quantities.

## 1.1 What `rejoin_events = 0` actually measures

`roll_prefix_and_find_event` increments `rejoin_events` only from:

```text
len(step["rejoin_uavs"])
```

while rolling the main source prefix. As soon as a qualifying event is found, it returns that count together with `steps_rolled=t+1`. It does not include the later calibration or focal-audit continuations. fileciteturn113file0L155-L193 fileciteturn130file0L90-L100

Thus the supported statement is:

> No environment charging-fall edge was observed on the main prefix path before event certification or the prefix deadline in the post-repair rerun.

It is not:

> No conclusion-bearing path executed `constructive_mixed_update(..., event="REJOIN")`.

## 1.2 Every focal SET continuation contains a virtual REJOIN

For every focal intervention, `fork_continuation`:

1. invokes a virtual LEAVE before the continuation;
2. forces the focal target for the first \(\Delta\) steps;
3. invokes `constructive_mixed_update(..., event="REJOIN", event_uav=focal_uav)` at \(t=\Delta-1\).

fileciteturn122file0L25-L52

The repaired code’s load-bearing change is precisely an early return inside that REJOIN branch when the rejoining UAV already appears in the duty map. fileciteturn127file0L146-L170

Consequently:

> **The repaired branch is executed by the focal SET machinery even when `roll_power.rejoin_events` is zero.**

Whether its early-return condition changes a particular continuation depends on the intervening assignment state. The current evidence does not measure:

- virtual-REJOIN calls;
- repair early-return hits;
- old-versus-repaired duty maps at the virtual REJOIN;
- or old-versus-repaired \(G\)-component sequences on the exact same event world.

H therefore has not been shown equivalent to the repaired implementation on the focal paths.

## 1.3 Environmental continuation REJOINs are also unmeasured

Each calibration or audit continuation rolls `step_once` for its registered horizon. That means ordinary charging-fall transitions may also occur **after** event certification:

- \(H_{\mathrm{stable}}=139\);
- \(H_{\mathrm{flex}}=550\).

Those transitions are processed by the ordinary lifecycle path but are not included in the prefix-local `roll_power.rejoin_events` count. fileciteturn104file0L99-L115 fileciteturn122file0L33-L50

The absence of a prefix REJOIN therefore does not establish absence of an environmental REJOIN in either conclusion-bearing window.

## 1.4 Equal event records are not equal continuation trajectories

The rerun evidence establishes that H and the post-repair run have identical serialized `audit_events`. But the implementation stores:

- `audit_events`;
- `audit_units_stable`;
- `audit_units_flex`;
- and `calibration_units_d_a`

as distinct result objects. The point estimates are computed from the unit arrays, not from the event metadata. fileciteturn126file0L152-L167

The measured fact that event records agree while the point estimates differ is direct evidence that event identity alone does not establish complete continuation equality. fileciteturn100file0L90-L105 fileciteturn100file0L145-L165

## 1.5 H’s precise status

Preserve H’s emitted JSON and branch verbatim.

The specific historical claim:

> H was contaminated because a correctly namespaced prefix probe observed environment REJOINs

is withdrawn.

The authoritative scientific disposition remains:

```text
INVALID_R4_REALIZATION:
DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED
```

with a sharpened explanation:

> H does not establish that its complete conclusion-bearing assignment paths are equivalent to the repaired realization. The available counter covers only main-prefix environment REJOINs, while virtual and continuation REJOIN paths remain unmeasured.

This is a fail-closed evidentiary ruling. It does not assert that a differing numerical value has now been found in H.

---

# 2. Decision 4b — the earlier R4 artifact

## Ruling: **no retraction**

The proposed structural extension is invalid for two independent reasons.

## 2.1 `T_E_MAX=950` is not the end of R4’s measurement horizon

`T_E_MAX=950` bounds the search for a qualifying event. It does not terminate the conclusion-bearing continuation. Once the event is captured, the measurement continues for 139 or 550 steps. fileciteturn104file0L99-L115

Therefore the inference:

```text
prefix ends by 950
⇒ no R4 path can reach REJOIN
```

does not follow.

## 2.2 The charging arithmetic uses the wrong terminal condition

The source controller releases a charging UAV at the registered `REJOIN_BATTERY_RATIO=0.80`, not at a full battery. fileciteturn104file0L93-L115

The environment first subtracts flight/hover consumption, then applies gross charging; the relevant battery change is therefore not simply \(1000/3600\) Wh per step from 2% to 100%. fileciteturn112file0L30-L76

The “2% to full is about 565 steps” arithmetic can help explain why no prefix falling edge was observed. It does not prove structural unreachability of:

- the 80% controller release point;
- contention-driven selection loss;
- a REJOIN in a 550-step continuation;
- or the explicit virtual REJOIN at \(\Delta\).

## 2.3 A later run cannot lend its zero count to a different world population

The current rerun and H disagree on episode-world fingerprints for three of the eight topologies despite identical registered episode keys. fileciteturn100file0L174-L203

It is therefore not valid to say:

> the rerun saw zero prefix REJOINs, so H necessarily did too.

H itself carries no REJOIN field, and its complete initial worlds cannot be regenerated from the registered keys under the current generator. The later artifact cannot retroactively supply an unrecorded event count for a different realized world.

The earlier R4 artifact is still less capable of establishing this invariant and remains scientifically invalid for the same assignment-realization question.

---

# 3. Decision 6a — can the post-repair rerun carry R4’s conclusion?

# **No**

The rerun is mechanically useful and should be preserved. Within each episode:

- the source-assignment repair is present;
- arms fork from one live event snapshot;
- CRN and clone checks apply;
- support and conformance pass;
- and the branch assembler operates deterministically.

It can support a conditional statement of the form:

> For the exact episode worlds recorded in run `30479940700`, the R4 assembler emitted `PART_A_CONTRADICTION`, stable `AFFIRMATIVE_NONMATERIAL`, and flex `UNRESOLVED`.

It cannot support:

> The frozen R4 evidence population produced that conclusion.

The registered episode-world key is not an actual reproduction key. Identical:

- R4 population namespace;
- topology-coordinate hash;
- block and episode index;
- `user_world_seed`;
- dependency versions;

produced different initial worlds on three topologies. Those changed the selection diagnostic and continuous point estimates. fileciteturn97file0L139-L176

The current code now accurately documents that `seed_controls_generation=True` proves only:

- the named seed was applied;
- a pinned topology hash was present.

It does not inspect whether the resulting world is the one that the same registered key produced elsewhere. fileciteturn105file0L96-L132 The focused test deliberately demonstrates that two different worlds can both report the flag as true. fileciteturn109file0L66-L84

This is a population-provenance failure, not merely final-digit numerical drift.

---

# 4. Decision 6b — what property is actually missing?

## It is not simply bit-identical point estimates

The missing property is:

# **A registered episode key must identify either one reproducible world or one validated probability law**

There are two scientifically admissible designs.

## Route A — fixed-world reconstruction

Under the current fixed-seed interpretation, the tuple

```text
contract / population namespace
topology-coordinate hash
block
episode index
user_world_seed
world-generator version
```

must generate the same canonical initial-world manifest across:

- processes;
- worker counts;
- machines;
- and the registered runtime.

At minimum, all conclusion-bearing user and cluster component digests must match.

After the evidence input is identical, the final floating-point point estimate need not necessarily be bit-identical if a pre-registered numerical tolerance accounts for harmless backend arithmetic. The tolerance must be frozen before a result and must not permit a changed event, candidate selection, component series, or branch.

## Route B — explicitly stochastic cross-machine generation

Alternatively, the project could register machine/runtime variation as part of the sampling process and establish that every runtime draws from the same probability law. That would require:

- a new probability model;
- a registered machine/runtime factor;
- distributional validation;
- and inference that includes that factor.

The present contract does none of these. It fixes episode identifiers and treats their user-world seeds as the mechanism making episode draws reproducible. The `user_world_seed` documentation still says the seed makes the draw reproducible and recorded, even though the later fingerprint documentation has withdrawn that claim. fileciteturn105file0L29-L54

## Why interval overlap is insufficient

A confidence interval describes uncertainty conditional on the sampled data and the registered sampling model. Two intervals overlapping does not prove that:

- both datasets came from the same law;
- the hidden machine factor is benign;
- or the fixed episode population was reproduced.

A distribution shift can produce overlapping confidence intervals, particularly when the registered bounds are broad.

Therefore:

```text
both runs' point estimates lie inside one common interval
```

is not an adequate replacement for evidence-population identity.

---

# 5. Decision 6c — replication or insensitivity?

# **Neither, formally**

The most accurate classification is:

```text
EXPLORATORY_BRANCH_ROBUSTNESS_UNDER_UNREGISTERED_WORLD_VARIATION
```

## Why it is not a formal replication

A replication must either:

- reproduce the registered inputs; or
- draw a new sample under a registered replication design.

Neither condition is established. The same registered episode keys generated different worlds through an unregistered machine-dependent factor.

## Why it is not evidence of inappropriate insensitivity

The continuous outputs are not insensitive:

- \(U^\*_{\mathrm{flex}}\) moved by about \(0.9\);
- stable and Part-A points also moved;
- the flex selection HHI changed materially in at least one reported case.

The branch remained unchanged because:

- the five-unit materiality regions are coarser than these point movements;
- the relevant intervals remain broad;
- and the first-match branch mapping is a thresholded summary.

Branch agreement across two hidden-world realizations modestly raises the plausibility that the current categorical result is robust to some user-world perturbations. It does not establish how broad that robustness is, and it does not cure the missing sampling contract.

The two-run agreement should therefore be retained as a diagnostic sensitivity observation, not added to the confirmatory evidence count.

---

# 6. Decision three — severity and required repair

# **Claim-blocking repair**

Disclosure alone is insufficient for a formal or published R4 claim.

Merely changing the wording of `seed_controls_generation` to “seed applied” is an honest documentation correction, but it leaves the conclusion-bearing evidence population unidentified. Re-scoping the provenance contract to within-run identity after observing the result would change the evidence semantics post hoc.

The project’s durable evidence rule requires provenance and the sampling contract to be frozen before a conclusion-bearing result, and an invalid or non-identifying measurement updates the measurement rather than being rescued by renaming it. fileciteturn98file0L126-L163 fileciteturn98file0L186-L208

## 6.1 Immediate diagnostic scope

First localize the discrepancy using the newly persisted per-component digests:

- user positions;
- velocities;
- waypoints;
- pause times;
- cluster assignments;
- cluster centres/history;
- cluster motion state.

This is an apparatus diagnostic, not an R4 result.

The explanation “`ubuntu-latest` is not one machine” remains plausible but is not established. Pinning package versions rules out one class of drift; the requirements file does not identify the unregistered state that changed the world. fileciteturn115file0L13-L20

## 6.2 Selected repair family — persist and replay the complete world manifest

The strongest and most reversible repair is:

1. Generate the episode world once under a registered generator.
2. Persist the complete initial user/cluster manifest, not only its hash.
3. Make every formal episode load that manifest.
4. Verify its canonical digest before stepping.
5. Separate:
   - manifest identity;
   - episode/continuation RNG;
   - topology identity;
   - and energy permutation.

This removes cross-machine regeneration as a dependency of the scientific result.

## 6.3 Live alternative — deterministic seed-to-world generator

A second valid route is to make world generation a pure, tested function of:

```text
pinned topology
user_world_seed
generator version
```

Every source of randomness and any ordering affecting the generated arrays must derive from that explicit stream.

Before formal use, a cross-process and cross-machine conformance gate must establish equal component digests for a frozen set of episode keys. A test performed on one machine or one process is insufficient because that is precisely where the current generator appears stable.

## 6.4 Parked route — machine as a registered random factor

Treating machine/runtime variation as another random factor is scientifically possible but not selected:

- it needs a new probability model;
- larger independent-machine sampling;
- and different inference.

It would be excessive compared with exact manifest replay and would substantially change R4’s population claim.

## 6.5 Fresh confirmatory evidence

After either repair:

- H and the current rerun remain historical conditional observations;
- their topologies and episode worlds have been repeatedly inspected;
- they must not be re-labelled as the fresh confirmatory result.

Any new formal claim requires a fresh, untouched population under the repaired provenance contract. No such population is selected by this ruling.

The same repair is required before any later conclusion-bearing S7-S3 source audit, not only a paper citation of R4.

Development-only conformance work can continue because it carries no population inference.

---

# 7. Challenges to §§2, 3 and 5

## Challenge 1 — “the repaired branch never executed” is false

The counter establishes zero environment falling-edge REJOINs on the main prefix. It does not count the direct virtual REJOIN invoked by every focal SET continuation. fileciteturn122file0L25-L52

The correct statement is:

> No environment-generated REJOIN was observed on the main event-search prefixes of the post-repair rerun.

## Challenge 2 — `111,433 steps_rolled` is not the complete R4 execution

`steps_rolled` is returned by `roll_prefix_and_find_event` when a qualifying event is found or the prefix search ends. It excludes the many 139- and 550-step continuation forks that produce the actual \(D_A\) and \(U^\*\) samples. fileciteturn130file0L90-L121

Calling it the number of steps over the “whole population” is acceptable only if “population” means all prefix attempts, not all conclusion-bearing execution.

## Challenge 3 — the structural horizon argument fails

Three corrections are required:

1. the controller releases at 80%, not full charge;
2. the prefix deadline is not the continuation deadline;
3. focal SET explicitly creates a virtual REJOIN after ten steps.

The gross 2%-to-full arithmetic cannot establish structural unreachability.

## Challenge 4 — identical event hashes do not establish identical result units

The event record and the calibration/audit units are serialized separately. Identical event metadata can coexist with different continuation results, which is exactly what the measured point differences demonstrate. fileciteturn126file0L152-L167

## Challenge 5 — the current rerun cannot retroactively report H’s zero

The two cloud runs generated different worlds under the same episode keys. A zero event count from the rerun is not a measurement of an unrecorded field in H.

## Challenge 6 — the root cause is not yet isolated

The evidence rules out several candidate explanations, including pooler nondeterminism and declared package-version drift. It does not identify which construction-time input or array first diverges.

Do not freeze “machine-dependent construction state” as the causal conclusion until the component-digest comparison identifies the first differing surface.

## Challenge 7 — two stale reproducibility claims remain in source documentation

The corrected `episode_world_fingerprint` documentation now says the field is only a seed-application witness. But two other listed passages remain inconsistent:

- `user_world_seed` still says the seed makes the draw reproducible; fileciteturn105file0L29-L54
- `full_state_fingerprint` still says `episode_world_fingerprint` reproduces across constructions. fileciteturn114file0L149-L164

These should be corrected as documentation/provenance reconciliation. They do not repair the generator.

---

# 8. Smallest scientific update

## Supported

- The post-repair main-prefix roll on its realized worlds observed 109 LEAVEs and zero environment REJOINs.
- The assignment guard ran extensively and recorded no refusal on those prefix paths.
- Two complete runs emitted the same categorical branch and limb states under different realized user worlds.
- The same registered episode-world keys do not reproduce their worlds across machines.

## Not supported

- That the source-assignment repair was inert on H’s complete continuation paths.
- That no R4 continuation can reach a REJOIN.
- That H or the earlier artifact is rehabilitated.
- That the post-repair rerun represents the frozen R4 evidence population.
- That branch agreement constitutes a formal replication.
- That the machine/runtime root cause is already known.

## Smallest failed unit

```text
episode-world generation
× registered episode key
× cross-machine evidence-population identity
```

This does not retire:

- the focal estimands;
- the five-unit materiality anchor;
- the bootstrap logic;
- R30;
- D7.3;
- D8;
- or the broader variable-lifetime research line.

---

# 9. Retained portfolio

| Route | Status | What would raise or lower it |
|---|---|---|
| **Complete world-manifest persistence and replay** | **Selected repair family** | Raised if exact replay works across machines without changing source semantics |
| Deterministic seed-to-world generation | Live alternative | Raised by exact cross-machine component-digest equality |
| Machine/runtime as an inferential factor | Parked | Raise only if exact replay and deterministic generation are impractical |
| H rehabilitation | **Not supported** | Requires exact-world old/new full-continuation equivalence, including virtual REJOIN paths |
| Current rerun as formal R4 result | **Rejected** | Requires a repaired population contract and fresh evidence |
| Branch agreement as exploratory robustness | Retained diagnostic | May guide later sensitivity analysis; carries no confirmatory weight |

## Scheduled next action

The next scientific artifact should be an **episode-world provenance correction and root-cause localization**, not another R4 result run:

1. compare existing component digests and identify the first differing world array;
2. identify every writer and random source for that array;
3. freeze either manifest replay or deterministic generation;
4. define a cross-machine fail-closed conformance gate;
5. only then design fresh confirmatory evidence.

No threshold, R4 topology, result branch or historical JSON is changed.

**D7.3 and D8 remain blocked. This review authorizes neither a new formal run nor publication of the current R4 branch as a confirmatory result.**