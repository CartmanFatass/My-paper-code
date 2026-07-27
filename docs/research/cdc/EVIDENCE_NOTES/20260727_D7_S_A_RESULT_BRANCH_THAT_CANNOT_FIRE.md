# A registered result branch is unreachable, and three functions are dead code

First systematic mechanical sweep of `scripts/audit_d7_s_event_aligned.py` — the
instrument that produces the project's next published result. Twelve unfailable
guards had been found across partial sweeps; the file had never had one
breadth-first pass.

Swept at `97d73360`, baseline **177 passed**. Every finding below was re-run by
the Project Manager on the main tree. The formal audit (run `30289161086`, tag
`d7s-audit-2`) was executing while this sweep ran.

## The finding: `PRIMARY_G_DEGENERATE` can never fire

`decide_branch` (`:1046-1075`) implements ten registered branches by first-match
precedence. Branch 3:

```python
if primary_g_degenerate_flag:
    return "PRIMARY_G_DEGENERATE"
```

`assemble_audit_result` calls it as (`:3787-3791`):

```python
out["branch"] = decide_branch(
    conformance_ok=conformance_ok, support_ok=support_ok, primary_g_degenerate_flag=False,
    ...
```

**A hardcoded literal `False`.** The function that computes the flag —
`primary_g_degenerate` (`:750-755`) — is defined and **never called anywhere in
the file**. Grepped: its only occurrences are its own definition, the parameter
name, and the `if` that reads it.

So the branch is structurally unreachable regardless of what the data shows, and
mutating the function's own logic (`or` → `and`) leaves **177 passed** because no
test calls it either.

### Severity: this is a diagnostic-precision defect, not a claim-inflating one

The sweep classified this as the worst case named in its brief. **That framing is
wrong, and the correction matters more than the finding.** Tracing every path a
degenerate run can take:

`primary_g_degenerate` fires on `component_sequences_arm_invariant or not
b_m_positive_lcb`. Take each half:

- **Arm-invariant components.** `arm_distinctness_check` over every topology's
  certified-event duty-map pairs already feeds `conformance_ok`
  (`:3701-3706`), and `not conformance_ok` is **branch 1**, which precedes
  branch 3. The two notions are related but not identical — distinct duty maps
  do not by themselves prove the four G component sequences differ — so the
  cover is partial. But if the component sequences *were* exactly arm-invariant,
  every contrast is zero, so `b_stable_lcb > 0` and `b_flex_lcb > 0` both fail
  and no affirmative branch can fire.
- **No positive B_m lower bound.** Every affirmative branch requires
  `b_stable_lcb > 0` or `b_flex_lcb > 0` (`:1060-1063`). A non-positive B_m LCB
  therefore falls through all of them to `SOURCE_NECESSITY_UNRESOLVED`.

**In every path, the failure is conservative.** A degenerate run is reported as
unresolved or invalid, never as an affirmative source-necessity result. The cost
is that a reader cannot distinguish *"the estimator could not resolve this"* from
*"the instrument was degenerate"* — two states with different next actions.

**Consequence for the run finishing now: it is not invalidated.** If its branch
is affirmative, `b_stable_lcb > 0` held, so the flag would have been `False`
anyway and the missing branch could not have changed the answer. If its branch is
`SOURCE_NECESSITY_UNRESOLVED`, the degeneracy question is open and must be
answered post hoc — which the artifacts permit, since `b_stable_lcb`,
`b_flex_lcb`, `arm_distinct_ok` and `arm_distinctness_pairs` are all recorded and
pooled.

Recording the reasoning rather than the alarm, because over-accepting a severe
reading is the same failure as under-checking a test.

## Two more functions are dead code

- **`qos_component_saturated`** (`:744-747`) — never called anywhere, not even
  wired to `component_sequences_arm_invariant`. Mutating `and` → `or` leaves
  **177 passed**.
- **`expansion_allowed`** (`:1095`) and **`TOPOLOGY_SEEDS_EXPANSION`** (`:129`) —
  never called or read in `main()`. Deleting the `already_expanded` re-trigger
  guard leaves **177 passed**.

The second is a governance gap, not a numerical one. `CURRENT_WORK.md` states
expansion to `20260734–20260741` happens **only** under the frozen §9 predicate,
never as a retry or power rescue. **No code enforces that.** Expansion happens by
a human passing `--topology-seeds`, which bypasses the predicate entirely. The
rule is real and the mechanism named to uphold it does not run.

## The result branch has no boundary test

`decide_branch`'s four predicates (`:1060-1063`) use strict inequalities:

```python
stable_clears = (b_stable_lcb > 0) and (t_stable_ucb < 0)
flex_clears   = (b_flex_lcb > 0) and (t_flex_lcb > 0)
```

Loosening every one of them to `>=` / `<=` leaves **177 passed**.

The production code is **correct**; what is missing is any guard on it. All ten
branch-precedence fixtures draw bound values from `{1.0, -1.0, -2.0, 0.5, 2.0}`
and never exactly `0.0` — so the boundary of a one-sided 95% interval, the single
value where strict and non-strict disagree, is untested on the field that decides
the published branch.

## Minimum support: `and` reads as `or` with the suite green

`check_minimum_support` (`:1082-1092`) requires **both** calibration-topology and
audit-topology support at `MIN_SUPPORT_TOPOLOGIES = 6`. Changing `and` to `or`
leaves **177 passed**, and no test calls the function.

Unlike the three above, this one is **live**: called at `:3694`, feeding
`support_ok` → branch 2 (`SOURCE_EVENT_SUPPORT_INSUFFICIENT`). Under the weakened
predicate a run with six well-supported calibration topologies and zero supported
audit topologies would report `support_ok=True` and proceed to a bootstrap and a
branch decision on data the contract says to refuse. The code is right; nothing
would notice if it stopped being right.

## `contract_id` is the ninth field the "any single field" test does not vary

`test_stream_seed_changes_with_any_single_field` varies eight of the nine hashed
fields. `contract_id` appears nowhere in the test file. Dropping
`str(contract_id)` from the hashed tuple leaves **177 passed**.

**Live risk today is nil** — `CONTRACT_ID` is one fixed module constant, never
varied across any production call, so no current seed changes. It matters only if
a future contract revision changes it without redrawing every stream, which is
exactly what the module comment at `:84-88` warns about. Defence-in-depth, and
recorded as such rather than inflated.

It is also the *name-quantifier* pattern again: the test says **any single
field** and covers eight of nine.

## Confirmed clean

- **`compute_G` weights** — deleting `- 2.0 * return_constraint_cost` gives
  `1 failed`, caught by `test_compute_g_hand_worked_weights_exactly_minus2_minus5_minus10`,
  which uses all-nonzero distinguishable components against a hand-worked literal.
- **`REJOIN_BATTERY_RATIO`** `0.80 → 1.2` gives `1 failed`, caught by
  `test_every_registered_constant_matches_the_frozen_contract`. This was the
  headline defect of 2026-07-27; the repair at `5fe1556f` holds, and it holds
  against a frozen-literal table rather than a code-derived restatement.

## Not swept — over half the file

Breadth-first per the brief, and it did not reach the back half. **Everything
beyond roughly `:1743` is unswept**, including `update_duty_map_on_transitions`,
`replay_prefix` and `PrefixReplayError`, `roll_prefix_and_find_event`,
`capture_event_snapshot`, the clone/fork continuation machinery,
`full_state_fingerprint` and all its per-type branches, `run_audit_event`,
`run_calibration_episode`, `accumulate_episode_leave_stats`, `resolve_run_plan`,
`run_topology_audit`, the parallel-workers path, and `main()`'s CLI wiring. These
have named tests; none was independently mutated.

Also unswept: seventeen of the eighteen registered constants (the frozen-contract
mechanism was spot-checked once and assumed to generalize); the constants outside
that pinned set; the CRN pairing internals of
`hierarchical_bootstrap_events`/`_quantity`, where purpose-built tests exist but
the pairing was not independently broken; `dock_trigger_ratio`;
`certify_stable`/`certify_flex`/`check_leave_eligibility`; `arm_distinctness_check`
and `compute_conformance_ok`.

**The file must not be read as audited.** A partial sweep reported as complete
reads as coverage forever after, which is the failure this whole line of work
exists to stop.
