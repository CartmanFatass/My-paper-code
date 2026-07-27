# Stage B on the shared-prefix realization -- and the defect it uncovered

Stage B code-science alignment on the diff that implements your R2 ruling. It
carries one disclosure that is larger than the diff, so the standard three
questions come first and the disclosure drives a decision tree after them.

No verification labor is requested. Every fact below is measured and stated with
its provenance; nothing here asks you to confirm an inventory.

## What was implemented (your ruling, realized)

Commits on `untied-k`, all pushed and readable at `stage_commit`:

- `1c0cc9d` -- contract refrozen as `D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md`
  (supersedes, never edits the frozen file): `n_select=2`, `n_eval=2`; the
  shared-prefix realization with your six blocking conditions; the selection
  diagnostic; cost status.
- `bd85d66` -- `EventSnapshot`: one canonical evaluator-certified replay per
  qualifying event, immutable, every continuation on its own clone, discarded
  after use. Same snapshot serves both limbs. `replay_prefix` deliberately
  retained as the reference oracle. Failure semantics changed as your ruling
  requires: one replay per event means its failure, or any clone isolation
  failure, voids the whole event rather than dropping one replicate.
- `454e3c0` -- selection diagnostic: per event, the point-selected candidate,
  bootstrap selection frequency for every legal `z`, legal-set size, and two
  concentration readings.
- `0c165a9` -- the conformance check and the evidence note below.

`CONTRACT_ID` was left unchanged on purpose: it feeds `stream_seed`, which R2
keeps unchanged. 146 focused tests pass.

## Q1 -- the three Stage B questions

Answer for the diff as a whole:

1. Does the code instantiate the frozen R2 contract?
2. Could a test pass through the wrong mechanism?
3. Could an alternate implementation explanation change the registered
   conclusion?

Return `ALIGNED`, `MISMATCH` (naming the frozen assertion and the conflicting
code path), or `SCIENTIFIC_AMBIGUITY` (naming one previously unstated
result-changing choice).

## Q2 -- disclosure: the fixed-history mechanism never held

Full detail and measurements:
`docs/research/cdc/EVIDENCE_NOTES/20260726_D7_S_PREFIX_REPLAY_IS_NOT_FIXED_HISTORY.md`

The superseded contract asserted bit-identical prefix replay including
"user-motion and channel streams", enforced by a state hash before forking.
Measured on the registered environment:

- `reset(seed=S)` twice on one env object -- user positions identical;
- two **freshly constructed** envs with the **same** seed -- user positions
  differ by up to **6547 m**;
- two independent `replay_prefix` calls to the same `t_e` -- **24 attributes**
  differ, including `user_positions` (max delta 4193 m), `sinr_matrix`,
  `connections`, `last_user_rates_mbps`, `cluster_*`.

The user population is fixed by construction-time state that `reset(seed=)` does
not re-derive, and `build_pinned_env` constructs a fresh env per call.
`compute_state_hash` covers UAV positions, battery, charging, station
occupancy/queue, lifecycle mask and duty map -- **no user, cluster or channel
state** -- so the guard was computed over the one surface that stayed identical
and passed on every fork.

Consequence: under the superseded replay-every-prefix realization, KEEP and each
candidate's selection and evaluation replicates each ran against a **different
user world**, so SET and KEEP were not CRN-paired at the prefix level. This is
the same defect class as the topology-provenance issue you ruled on 2026-07-26
(unseeded construction-time layout), which is why section 9 restores BS and
station coordinates after reset. That reasoning was never extended to users.

Your shared-prefix ruling therefore fixes a correctness defect, not only a cost
one -- one snapshot is the first realization in which all arms of an event share
one user world.

### Q2(a) -- condition 1 is unsatisfiable as written

Your condition 1 requires a clone continuation to be exact-numerically identical
to one obtained by the previous independent replay route under the same
continuation seed. The reference route is nondeterministic across calls, so the
condition asks the correct mechanism to reproduce the broken one.

Measured on the real environment: conditions 2, 3, 4 and 5 **pass**; `deepcopy`
of the real env costs 4 ms; condition 1 fails for the reason above.

**Rule one:**

- **(i)** replace condition 1 with: *two continuations cloned from the same
  snapshot under the same `stream_seed` are identical, and two clones under
  different `stream_seed` differ only through the continuation stream*; or
- **(ii)** keep the original condition and name what it should compare against,
  given no deterministic independent route exists; or
- **(iii)** something else you specify.

If you rule (i), also confirm whether clone equivalence must additionally be
demonstrated across a limb boundary (one snapshot serving both stable and flex).

### Q2(b) -- is topology still the comparability unit?

Two Scenario-7 episodes sharing a coordinate hash do **not** share a user
population. Section 9 records topology identity as the coordinate hash and pins
BS/station coordinates; users are neither pinned nor recorded.

**Rule one:**

- **(i)** topology identity stays as-is; the user population is a within-episode
  nuisance the hierarchical bootstrap already absorbs through episode
  resampling -- no contract change; or
- **(ii)** the user layout must be pinned and recorded alongside the coordinate
  hash, making it part of topology identity -- which changes section 9 and
  requires a further refreeze; or
- **(iii)** users need not be pinned, but the artifact must record a user-layout
  fingerprint per episode so comparability is auditable after the fact.

If you rule (ii), say whether the eight registered topology seeds retain their
identity or must be re-registered.

### Q2(c) -- reach into closed results

This touches the meaning of closed results, so it crosses to you rather than
staying with the Project Manager.

Any prior Scenario-7 evidence whose compared arms were built from **separate env
constructions** shares this defect. The first candidate is the ep64
single-topology diagnostic
(`logs/nonformal_d7_s_persistence_margin_20260726_ci_h1500_ep64_single_topology_20260725_branch`),
already scoped to one realized topology, whose arms' user populations have not
been checked.

**Rule one:**

- **(i)** audit-on-reuse only -- no closed result is disturbed until something
  tries to reuse it as a causal comparator, mirroring your 2026-07-26 topology
  ruling; or
- **(ii)** the ep64 diagnostic must be explicitly rescoped or retired now,
  because its `B_H`/`U_stable` numbers are quoted in the portfolio; or
- **(iii)** a named wider set must be audited before D7.S launches.

## Q3 -- does the audit launch?

Given your answers above, and that the measured step rate is **0.061 s/step**
(below the 0.10-0.30 band previously assumed, whole-audit upper end ~4.3 h at
8-way sharding; the user removed the wall-clock cap entirely on 2026-07-26):

does the D7.S event-aligned joint audit launch on the R2 contract as
implemented, or does something above have to close first? Name the blocker if so.

## Evidence to read

- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260726_D7_S_PREFIX_REPLAY_IS_NOT_FIXED_HISTORY.md`
- `scripts/audit_d7_s_event_aligned.py`
- `scripts/d7_s_clone_conformance_check.py`
- `tests/audit_d7_s_event_aligned_test.py`
- `envs/pettingzoo/uav_env.py`
- `envs/pettingzoo/scenario4.py`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
