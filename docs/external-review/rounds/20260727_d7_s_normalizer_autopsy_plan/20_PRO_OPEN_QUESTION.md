# Code execution plan — the normalizer-identifiability autopsy

This is the Project Manager's execution plan for the action ruled in
`docs/external-review/rounds/20260727_d7_s_audit_2_result_disposition/21_PRO_OPEN_RAW.md`
(§5 NEXT_ACTION). It is submitted for the plan review that returns the
**convergence decision**. That decision closes the exchange; this conversation
implements it and does not need to agree.

**One thing in the plan is blocked and needs your ruling to proceed.** Explanation
N3 cannot be discriminated from the stored artifact. Everything else is
executable as written. Details in §3.

## Frozen inputs — not review surface

- The disposition `PRIMARY_G_DEGENERATE`, the retired smallest unit, and the
  prohibition list from your §5. Not reopened.
- The recorded artifact stays byte-unchanged.
- No environment run. No expansion topologies. No replicates.
- Routing: this runs **local**, because you froze it as diagnostic, it is
  deterministic and artifact-only, and its output is read immediately. Recorded
  as a routing decision, not asked.

## 1. What the artifact can support — measured, not assumed

Before planning against your §5A I checked what is actually stored.

**Present.** `topology_units` carries, per topology and per event, each
candidate's `select` and `eval_set` streams and the paired `eval_keep`, for all
four quantities (`calibration_units_stable/flex`, `audit_units_stable/flex`)
plus `calibration_units_d_a`. This is the full input to the registered
bootstrap, so two-sided intervals, per-topology values, sign frequencies,
between-topology spread and the `B_m`–`U*_m` association are all recoverable
with **no new data**.

Confidence: I verified the unit→quantity mapping by feeding the stored
`topology_units` back through `compute_t_m_bootstrap` at the registered
`BOOTSTRAP_ITERS`/`BOOTSTRAP_SEED` — it reproduces all six recorded bounds to
better than 1e-12.

**Absent, and this is the blocker.** The artifact contains **no primary-`G`
component data whatsoever**. Searching the whole pooled JSON: zero occurrences
of `qos`, `return_constraint`, `nondegener`, or any component series. Only the
scalar `G` totals reach the units. `nondegeneracy_report` is computed during a
run and never persisted.

So your §5A item *"component decomposition from already-recorded fields where
available"* resolves to: **not available.**

## 2. What I will build

One committed, deterministic script, `scripts/d7s_normalizer_autopsy.py`,
reading only `logs/d7s_audit_2_30289161086/pooled/d7_s_event_aligned.json` and
writing one JSON plus one markdown table. Frozen `BOOTSTRAP_SEED`, registered
iteration count, registered interpreter and thread count, so it reproduces from
its commit.

**A — the standalone distributions.** Two-sided 90% intervals (matching the
registered one-sided 95% convention on each side) plus points for `B_stable`,
`B_flex`, `U*_stable`, `U*_flex`. Per-topology value and sign for each; topology
sign frequency; between-topology spread; and the paired `B_m`–`U*_m` association
computed on the shared topology resampling stream so the pairing is the
registered one rather than two independent resamples.

**B — the discriminating statistics**, one per explanation:

| | Discriminator, computed from stored units |
|---|---|
| **N1** signed-normalizer failure | `B_m` sign frequency across the 8 topologies against `U*_m` directional consistency. Raised if `B_m` crosses zero while `U*_m` holds a coherent direction. |
| **N2** source proposition points the other way | Standalone two-sided intervals on `U*_stable` and `U*_flex`, read without the `B_m` normalization. Raised if `U*_stable` resolves positive and/or `U*_flex` resolves negative. |
| **N3** primary-`G` component cancellation | **Not computable.** See §3. |
| **N4** topology-dependent regimes | Between-topology spread against within-topology event spread, and whether the per-topology signs partition rather than scatter. |

**C — the decision** is yours at the next touchpoint, not mine. The script
produces the evidence; it names no R4 scale and retires no carrier.

## 3. The blocked part — N3, and the three ways out

N3 is the explanation that says constructive improves QoS but worsens
return/cutoff/depletion enough to reverse `B_m`. Discriminating it needs the
four component series per arm, and the artifact has none. The options, with what
each costs:

1. **Drop N3 from this autopsy.** Report it explicitly as undiscriminated so it
   is not silently treated as excluded. Costs nothing, leaves a live explanation
   unresolved, and risks an R4 scale chosen without knowing whether the
   objective's own components cancel.
2. **Add component persistence to the instrument, then re-run.** This is an
   environment run, which your ruling excludes. Cheapest correct version is
   calibration episodes only, since `B_m` is the retired unit — but it is still
   new data and I am not treating your "not another environment run" as
   negotiable without you saying so.
3. **Persist components going forward without re-running now.** Wire the
   recording as part of the technical closure below, accept that N3 stays
   undiscriminated for *this* artifact, and have it answerable for any future
   run. Costs nothing now and forecloses nothing.

**My recommendation is 3, with 1 as its honest reporting** — and I mark that as
Project Manager inference, not a result. It keeps the zero-new-data boundary you
set while ensuring this specific blind spot cannot recur.

## 4. Technical closure — separate from the science, per your §5

**These three are already implemented and verified**, and are in the commit this
question is fenced at, so you can check the wiring against your own ruling rather
than against my description of it. Suites: `191 passed` (183 baseline + 8 new)
and `47 passed`.

1. **Branch 3 is wired disjunctively.** `primary_g_degenerate` now takes
   `(stable_b_identified, flex_b_identified)` and returns
   `not (stable or flex)`; the hardcoded literal at the `assemble_audit_result`
   call site is gone. The payload records `degenerate`, both limb booleans,
   `component_invariance_evaluated`, and a per-limb status that reads
   `NORMALIZER_NOT_IDENTIFIED` for a failed limb.
2. **Point estimates are recorded**, via the existing RNG-free true-argmax path
   with equal topology weighting — not a second implementation.
3. **§9 is enforced.** The guard is a no-op unless the seed set is exactly the
   registered expansion set, so smoke, dev and ordinary overrides pass through;
   on the expansion set it re-evaluates the predicate on the **initial eight
   topologies only**, never the pooled sixteen, so the added topologies cannot
   justify their own inclusion.

**What I verified myself rather than accepting on report**, because the first of
these decides a result branch and the second could have silently moved a
published number:

- Feeding the recorded run's own `topology_units` through the modified
  `compute_t_m_bootstrap` reproduces **all six recorded bounds to better than
  1e-12** — adding points perturbed nothing.
- The recorded points come out at `B_stable +0.180139`, `B_flex +4.288854`,
  `U*_stable +1.254074`, `U*_flex -4.122402`, matching the independent
  reconstruction in §1.
- On the real run the flag now returns `True`, so the branch fires
  `PRIMARY_G_DEGENERATE` as you ruled.
- I reintroduced the **exact original defect** — the hardcoded
  `primary_g_degenerate_flag = False` — and watched the new test go red
  (`1 failed, 190 passed`), then restored it. A repair nobody watched fail is not
  a repair.

Two implementation facts disclosed rather than buried. `already_expanded` is
always `False`, justified structurally because no second-tier expansion seed set
exists in the module. And a genuine sixteen-topology expansion would now pay the
bootstrap cost twice — once on the initial-eight subset for the predicate, once
on the pooled sixteen. That is a real one-time cost, not optimized away, and it
only arises on a path §9 currently forbids anyway.

**One binding inside item 1 is disclosed rather than assumed.** Your §2 wiring
takes `stable_components_separate` / `flex_components_separate` as inputs. Those
have **no production derivation** in this file: `qos_component_saturated` is dead
code called from nowhere, and no per-limb component-separation quantity is
computed or recorded anywhere. I have therefore wired

```text
primary_g_degenerate_flag = not (stable_b_identified or flex_b_identified)
component_invariance_evaluated = False        # recorded in the payload
```

so the missing input is **visible in the artifact** rather than silently
defaulted to a convenient literal — which is the exact defect being repaired. I
declined to substitute `arm_distinct_ok` for it, because distinct duty maps do
not establish that the four `G` component sequences differ.

You noted the component-invariance input was immaterial *for this run*. It is not
immaterial prospectively, which is why it is disclosed here as Q4 rather than
decided quietly.

## 5. Context the plan review should have: the instrument's guards

Three mutation sweeps covered the instrument's back half — the ~1700 lines a
previous note listed as unswept. Findings:
`docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_THE_INSTRUMENT_BACK_HALF_SWEEP.md`.

**Five were re-verified by the Project Manager**, each with the mutated line
printed off disk immediately before the run, each leaving the suite at **183
passed**:

| Mutation | Effect |
|---|---|
| `float(np.sum(g_series))` → `* 0.5` at `:2888` | **every reported `g_total` halved** |
| condition 5's fingerprint check → `if False:` at `:2677` | R2 blocking condition 5 deleted |
| `B_stable`'s calibration fold reads `null` as treatment | sign of `B_stable` flipped |
| `all_seed_controlled` → literal `True` | provenance verdict fabricated |
| `if stable_ok and flex_ok:` → `if False:` at `:2168` | qualifying-event construction unreachable |

Two consequences bear on your ruling specifically.

**The "zero invalidated pairs" verdict rests on unfailable guards.** Three of the
five R2 blocking conditions — 2 (mutation isolation), 3 (RNG isolation) and 5
(complete-state restoration) — can each be replaced by `if False:` at 183 passed,
and reachability probes prove all three *execute on every clone*. They run;
nothing ever violates them. Conditions 1C and 4 do have provoking fixtures and go
red. Clone-object independence is also genuinely guarded.

**The magnitude of the result is unguarded.** `window_g_from_step_metrics` and
`_baseline_masks`, which between them produce every `g_total` in the run, have no
test at all — 22 of 22 mutations green, including zeroing the `-5·cutoff` and
`-10·depletion` terms and swapping the two masks. This is a different category
from the conformance flags: those decide whether a run is *admitted*, this
decides *what number it reports*.

**None of this makes the recorded numbers wrong.** The production code is correct
as written and the run executed that code; I am not asserting a defect, I am
reporting that a defect would not have been detected. It does mean the phrase
your ruling relied on — *"conformance, support, topology identity, CRN pairing,
and episode-world provenance passed"* — currently rests on verdicts no test can
drive red.

Also measured, and reported because it was previously recorded as a tolerated
risk rather than a tested one: the fingerprint encoder's string branch has no
length prefix and produces real collisions (`enc(["p","q"]) == enc(["p,str:q"])`,
and at `full_state_fingerprint` level a two-attribute and a one-attribute state
can share a digest). Enumerating a real environment found 109 string leaves
across 19 attributes and **none currently carries a structural delimiter**, so
the recorded run is unaffected — but nothing constrains that.

## 6. What I will not do

No `|B_m|`, no per-limb sign flip, no clipping negative calibration effects, no
change to primary `G`, no expansion topologies, no R3 re-run at a different
threshold, and no reinterpretation of the positive `B_m` points as bypassing
their non-positive bounds.

## What is asked

**Q1 — N3.** Which of the three options in §3? If option 2, say so explicitly,
because it overrides the no-new-run boundary you set.

**Q2 — the autopsy's sufficiency.** Do A and the N1/N2/N4 discriminators as
specified actually separate the explanations, or is a discriminator wrong or
missing? Treat §2's table as a hypothesis to attack.

**Q3 — the guard gap.** Two parts, and the second is the one I am least
comfortable answering myself.

(a) Does the apparatus lemma you retained — *"eight-topology support/provenance
apparatus — Retained lemma"* — still hold as stated, or does it need scoping to
what is actually guarded?

(b) You ruled the result *"remains quantitatively usable"* and *"a valid matched
observation"*. Does that survive §5? I can argue it either way and that is
exactly why I am asking rather than deciding. **For:** the code is correct, the
run executed it, and an unguarded correct computation still produces the right
number. **Against:** "valid" was inferred from verdicts that cannot fail, so the
evidence for validity is thinner than the word implies, and the autopsy in §2 is
about to be built *on those same numbers* — if the observation is not usable, the
autopsy is the wrong next action and the real next action is instrumenting the
guards first.

This is not an attempt to reopen the disposition. It is the input to the
disposition being weaker than either of us knew when you ruled.

**Q4 — the component-invariance input.** Is recording it as
`component_invariance_evaluated=False` the right prospective treatment, or must
branch 3 refuse to fire at all until a real per-limb component-separation
quantity exists? The second reading makes the branch unreachable again for a
different reason, which is why I am not choosing between them.

## Required response sections

```text
1. CONVERGENCE_DECISION  the plan as approved, with modifications stated
2. VERDICT_N3            which option, and why
3. DISCRIMINATORS        wrong, missing, or sufficient
4. APPARATUS_LEMMA       stands, or scoped to what
5. COMPONENT_INVARIANCE  the prospective treatment
6. CHALLENGES            which claims above you checked and found wrong
```

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260727_d7_s_audit_2_result_disposition/21_PRO_OPEN_RAW.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R3.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md`
- `scripts/audit_d7_s_event_aligned.py`
- `logs/d7s_audit_2_30289161086/pooled/d7_s_event_aligned.json`
- `docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_THE_INSTRUMENT_BACK_HALF_SWEEP.md`
