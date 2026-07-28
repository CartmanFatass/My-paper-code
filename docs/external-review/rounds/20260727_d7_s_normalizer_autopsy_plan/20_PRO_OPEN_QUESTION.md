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

Bundled into the same implementation because it touches the same file, and
listed here so the plan review sees the whole diff surface:

1. **Wire branch 3 disjunctively.** Replace the hardcoded
   `primary_g_degenerate_flag=False` at `scripts/audit_d7_s_event_aligned.py:3788`
   with your specified form, recording `stable_b_identified` and
   `flex_b_identified` separately and labelling a failed limb
   `NORMALIZER_NOT_IDENTIFIED`.
2. **Record point estimates in the artifact.** Every point in the last round had
   to be reconstructed post hoc, and §9's own predicate is not evaluable from the
   recorded artifact without them.
3. **Enforce §9 in `main()`.** `expansion_allowed` is dead code and
   `--topology-seeds` bypasses the predicate entirely.

Each of the three gets a paired-negative test: the mutation that used to leave
the guard green must drive the new test red, and I watch it fail before calling
it done.

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

Three mutation sweeps ran over the instrument's back half. Findings:
`docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_THE_INSTRUMENT_BACK_HALF_SWEEP.md`.

Three were re-verified by the Project Manager on the main tree, each leaving the
suite at **183 passed**: `B_stable`'s sign can be flipped at its production fold;
`all_seed_controlled` can be hardcoded `True`; and the entire qualifying-event
construction branch can be made unreachable — **no test drives event selection
through to a real qualifying event.**

This is raised as plan context, not as a challenge to the closed disposition. It
does not make the recorded numbers wrong: the production code is correct and the
run executed it. It does mean that the phrase your ruling relied on — *"conformance,
support, topology identity, CRN pairing, and episode-world provenance passed"* —
currently rests on verdicts that no test can drive red.

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

**Q3 — the guard gap.** Given §5, does the D7.S apparatus lemma you retained
("eight-topology support/provenance apparatus — Retained lemma") still hold as
stated, or does it need scoping to what is actually guarded?

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
