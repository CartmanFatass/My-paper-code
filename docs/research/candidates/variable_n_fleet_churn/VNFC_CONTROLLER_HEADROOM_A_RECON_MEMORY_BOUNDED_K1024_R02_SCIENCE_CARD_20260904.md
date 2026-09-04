# VNFC memory-bounded K=1024 controller-headroom A/RECON science card

- Object: `VNFC-CONTROLLER-HEADROOM-A-RECON-MEMORY-BOUNDED-K1024-R02`
- Direction: `variable_n_fleet_churn`
- Frozen: `2026-09-04T11:40:14Z`
- Evidence class: `A/RECON`
- Result-bearing: `true` (sequential measurement fact; A objects have no consumption state)
- Direction authority: `PRO_FINAL / OPEN_MEMORY_BOUNDED_K1024`
- Pro request: `2026-09-04-vnfc-controller-headroom-convergence-01`
- Provider response SHA-256:
  `75f349f07637ab08c41d06e6a9a88ef8a599a729d757d7f34e23382647ea9311`
- Conversation binding: `em:variable_n_fleet_churn:convergence`

The archived response and Transport facts are under
`docs/research/candidates/variable_n_fleet_churn/external/2026-09-04-vnfc-controller-headroom-convergence-01/`.
This card executes that direction decision without a local direction-level substitution.

## 1. Exact question, claim ceiling, and non-goals

On the identical first-primary R02 sixteen-world `heldout-N7` panel, does an exactly
semantics-preserving, memory-bounded full-tape beam at `K=1024` witness failed-zone headroom of at
least `delta_fail=0.10` above unchanged `BCRH-PERSIST` in the aggregate and in both failed-zone
strata, thereby justifying the already named one-seed MAPR 256/1,024-update budget ladder? If it
does not, stop this bounded search family and return to the convergence node to re-pose the host,
population, or estimand without claiming that physical headroom is absent.

**Claim ceiling.** A sequential A/RECON measurement fact about the named sixteen simulator worlds,
native host, BCRH implementation, same-information comparators, and exact `K=1024` bounded search.
A positive result establishes only a witnessed lower bound on physical opportunity. An unresolved
result does not establish BCRH optimality, sufficiency, or absent headroom. This object is
outcome-informed follow-up to accepted R01 and is not independent confirmation or a C object.

**Non-goals.** No MAPR or DIRECT training; no fresh seed or other primary panel; no world selection,
pruning, replacement, or weighting from R01 outcomes; no BCRH or persistent-control retuning; no
new width, second result arm, early-success stop, or wider search; no unknown-optimum, causal-oracle,
learnability, stable-superiority, arbitrary-`N`, repeated-churn, transfer, UAV, safety, flight, or
deployment claim; no Portfolio lifecycle, priority, capacity, ownership, fusion, registration, or
investment decision.

## 2. Frozen population and historical comparator provenance

The population is byte-for-byte the R01 population:

- namespace:
  `VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02/B1-B3-PRIMARY/2026090311`;
- R02 configuration: `B1-B3-PRIMARY`, seed `2026090311`, updates field `64` as namespace only;
- purpose: `heldout-N7`; roster size: `N=7`;
- failed zones: `z in {1,2}`; rows: `0..7`; exactly eight worlds per zone;
- source path: `install_r02()`, inherited `derive_seed_master`, and `_build_world` from the accepted
  R02 path at the eventual launch SHA; and
- no use of primary seeds `2026090321` or `2026090331`.

Before implementation or target execution, the accepted R01 `K=256`, BCRH, and persistent
fractions and the complete `K=256` command-history digests are frozen in
`VNFC_CONTROLLER_HEADROOM_K256_ACCEPTED_WITNESS_20260904.json`. Its source summary has accepted
SHA-256 `5687572b44574f2ab7ff4055b2789e431eef05a6893002625198e2da3e910831`.

That artifact may be used only for a post-execution same-world non-regression check, preservation
of the already valid lower-bound witness, and result-blind finite selector tests on synthetic
inventories. It may not choose a world, width, command, data structure, threshold, stop, or further
invocation. The known positive zone-2 row-3 world may not be isolated or weighted differently.

## 3. Treatment and exact storage change

### Treatment: `ORACLE-BEAM-FAIL60-K1024-MEMBOUND`

The scientific search is the R01 search with width changed to exactly `K=1024`:

1. Receive the complete frozen exogenous tape for one world.
2. Choose legal physical commands only at post-loss epochs `0`, `1`, and `2`.
3. Advance the unchanged native host exactly twenty native ticks per candidate command.
4. Rank candidates by decreasing exact cumulative failed-zone delivered seconds, then
   lexicographically increasing complete physical command prefix.
5. At depths 0 and 1 retain the best 1,024 prefixes. At depth 2 evaluate every legal continuation
   and select the largest exact `fail_delivered / fail_demand`, with the lexicographically smallest
   complete command history on a tie.
6. Freeze every endpoint and headroom quantity after sixty post-loss seconds, then complete epochs
   3--5 with R01's lexicographically smallest legal terminal suffix. Suffix commands are recorded
   separately and never enter ranking or `R_fail_60`.

Only storage discipline changes. Replace each complete expanded depth vector with an exact
fixed-capacity top-K reducer. At every instant retain at most the current frontier of 1,024, the
next selector/frontier of 1,024, one transient child, and explicitly bounded fixed enumerator
scratch. No dynamic container may have capacity proportional to `1961*K`. Use exactly the same
deterministic total-order comparator as materialize-then-sort, and sort each retained frontier by
that total order before the next depth. Candidate enumeration, native stepping, integer endpoint
accounting, float64 operations, world RNG, action legality, tie handling, terminal completion, and
side effects remain unchanged.

Fixed-capacity equivalence is an engineering inference to be tested prospectively. It is not a
scientific observation or a universal proof claim.

## 4. Comparator roles and lower-bound construction

- **Decision comparator: `BCRH-PERSIST`.** The unchanged competent causal controller. Preserve its
  six-command native trajectory, scorer/checker equality, independent enumerator equality, exact
  candidate records and digests, and current-information law.
- **Strongest same-information predecessor: accepted `ORACLE-BEAM-FAIL60-K256`.** It sees the same
  full tape and supplies an already valid same-world lower-bound witness.
- **Exact same-information structural null: `PERSIST-MAX-C60`.** It sees the same full tape and
  exactly maximizes the registered persistent initial-command class.
- **Physical upper bound:** `U_i = 1 - R_i^BCRH`, unchanged from R01.

For each world define

```text
R_i^witness = max(R_i^1024, R_i^256-accepted, R_i^persist, R_i^BCRH)
L_i^1024    = R_i^witness - R_i^BCRH
U_i         = 1 - R_i^BCRH
```

Exact nested top-K semantics require `R_i^1024 >= R_i^256-accepted` in every world. Any violation
is implementation nonconformance and makes the invocation `MB1024-INCOMPLETE`; the `max` must not
be used to conceal it.

## 5. Causal and exposure trace

| Stage | Frozen trace |
| --- | --- |
| Environment event | One unannounced executor loss in one of two failed-zone strata on an already fixed `heldout-N7` world; the native host owns tape, demand, obstruction, state transition, legality, safety, and service accounting. |
| Entity and role ownership | The surviving physical roster remains `N=7`. Search owns only the legal command at epochs 0--2; BCRH owns its unchanged causal path. Entity identity is never replaced by slot identity. |
| Available information | K=1024, accepted K=256, and PERSIST receive the complete frozen tape. BCRH receives only unchanged causal current information. This intentional asymmetry measures opportunity, not deployable control. |
| Action and credit path | Every candidate command enters the real native host for twenty ticks. Ranking is exact cumulative failed-zone delivered seconds, not a critic, shaped reward, prediction, or surrogate. |
| Learner exposure | Zero parameters, initialisations, optimizer steps, training transitions, checkpoints, or checkpoint selections; displacement from initialisation is not applicable. |
| Native consequence | Exact integer `fail_delivered/fail_demand` at sixty seconds supplies endpoints, `L_i`, and `U_i`; terminal suffixes test complete native execution but cannot change the estimand. |

Membership, join/leave/rejoin, survivor state, partial observation, opportunity time, censoring,
replacement, semi-Markov discounting, optimizer exposure, and partner co-adaptation are unchanged
or absent within this single already generated post-loss episode. No statistic is credited unless
it changes the native service endpoint against the named controls.

## 6. Observables, estimands, and validity

For every `(zone,row)`, publish:

- exact numerator/denominator and full command history for BCRH, PERSIST, accepted K=256, and new
  K=1024;
- K=1024 minus accepted K=256 endpoint difference and the non-regression flag;
- `L_i^1024`, unchanged `U_i`, and the individual-world material flag;
- candidate, expansion, and native-tick counts by depth;
- current-frontier, next-frontier, transient-node, and replacement high-water counts;
- maximum capacity and conservatively owned bytes for every dynamic search container;
- a strictly positive OS-backed process peak RSS, conservative fixed-storage allowance, and wall
  time;
- BCRH scorer/checker/enumerator agreement and exact candidate records; and
- measurement-complete, terminal, safety, exclusivity, selector-conformance, resource, and
  non-regression flags.

Primary estimands are arithmetic means of `L_i^1024` over all sixteen worlds, zone 1's eight
worlds, and zone 2's eight worlds. The material threshold is exactly `delta_fail=0.10`. Individual
worlds and unchanged upper bounds remain visible.

Missing any world or required endpoint, nonpositive/unavailable OS RSS, conservative high water at
or above 2 GiB, native disagreement, illegal/unsafe/nonterminal execution, selector nonconformance,
`K=1024 < accepted K=256`, or wall-cap termination is `MB1024-INCOMPLETE`. It produces no
scientific branch or polarity; partial output is quarantined.

## 7. Ordered result branches and decision mapping

After all validity and resource prerequisites pass, apply this rule in order:

1. **`MB1024-A / MATERIAL_PANEL_HEADROOM_WITNESSED`** when aggregate, zone-1, and zone-2
   `L^1024` means are each `>= 0.10`.
   Return to `em:variable_n_fleet_churn:convergence` with support for opening the already named
   one-seed MAPR 256-update then 1,024-update B/EXPLORE ladder. This establishes physical
   opportunity only and does not predict learner success.
2. **`MB1024-D / BOUNDED_SEARCH_REMAINS_UNRESOLVED`** for every other complete valid result.
   Return to the convergence node for `RECAST_HOST_OR_ESTIMAND`. Do not launch another width and do
   not open MAPR. This is a research-allocation mapping after two bounded widths, not evidence that
   BCRH is optimal or headroom absent.

Publish descriptive `ZONE_LOCALIZED_WITNESS=true` when exactly one zone mean crosses `0.10`. It
does not create a third direction decision. R01's search-independent upper bounds are unchanged,
so old CH-B and CH-C conditions cannot newly become true in this successor.

## 8. Predictions on record

- DM prediction: **`MB1024-D / BOUNDED_SEARCH_REMAINS_UNRESOLVED`**. Fourfold width may recover
  delayed-benefit prefixes, but R01 improved only one of sixteen worlds and no zone-1 world; the
  conjunctive aggregate-and-both-zones threshold is therefore unlikely to be crossed. Confidence:
  moderate. A contrary MB1024-A result remains fully admissible.
- Owner prediction: `not taken (unattended)`.

## 9. Budget, per-arm cost, stop, and resource admission

There is exactly one result arm and at most one result invocation: `K=1024`.

```text
beam_expansions_per_world(K) <= 1961 + 2*K*1961
beam_expansions_total(K)     <= 16*(1961 + 2*K*1961)
native_ticks_total(K)        <= 20*beam_expansions_total(K)
```

At `K=1024`, the runner-derived worst case is `4,018,089` expansions per world,
`64,289,424` panel expansions, and `1,285,788,480` beam-native ticks. Persistent adds at most
`1,882,560` native ticks; BCRH adds exactly 96 decision calls and at most 188,256 scored
candidates. The result-blind projection is **723.80 wall seconds**. The per-invocation cap is
**2,700 wall seconds**, checked only between worlds. Stop only after all sixteen worlds and both
baselines complete; there is no partial branch or early-success stop.

Before target execution, CM must complete all of the following without reading or inferring a
target K=1024 endpoint:

1. finite fixed-selector versus materialize-and-sort tests on synthetic inventories covering
   strict ranks, exact ties, prefix ties, rejected candidates, and repeated replacement;
2. one result-blind capacity-saturating pilot using no R02 target world or coordinate. It must use
   the memory-bounded implementation, fill both 1,024-capacity frontiers, exercise replacement
   after saturation, and report capacity coverage, live-node/byte high water, fixed scratch, wall,
   and OS-backed RSS only. It must not publish a service endpoint. The refused expanded-vector
   pilot is not repeated;
3. positive OS-backed peak RSS and a conservative `measured_high_water + unexercised_fixed_bound`
   strictly below 2 GiB; and
4. immediately before the sole result invocation,
   `scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` with physical and effective
   available memory each at least 4,294,967,296 bytes.

Unavailable RSS, a bound at or above 2 GiB, failed central preflight, projected wall above 2,700 s,
or inability to preserve exact selector semantics is `BLOCKED_RESOURCE_ADMISSION`,
`BLOCKED_WALL_CAP`, or `BLOCKED_SEMANTIC_CONFORMANCE`, not a scientific result. A passing pilot
does not waive the fresh result preflight or the result invocation's own positive RSS/bound check.

**Exposure line.** Learner parameters `0`; model initialisations `0`; optimizer steps `0`; training
transitions `0`; checkpoints and checkpoint selections `0`; parameter displacement against
initialisation scale `not applicable`. Search exposure is the exact reported legal-command
expansions, native ticks, retained-frontier counts, replacements, live-node high water, wall, and
peak RSS.

## 10. Protected semantics, side effects, and launch record

Preserve R02 world bytes; native state transition, legality, membership and service laws; integer
endpoint accounting; float64 behavior; seed derivation and RNG; BCRH scoring/tie/release and
current-information law; persistent baseline; candidate enumeration and tie order; terminal
completion; historical files; and all checkpoint/learner nonexistence. No result may be repaired by
reading or salvaging target endpoints.

Permitted side effects are one pilot root and, only after admission, one result root under
`temp/directions/variable_n_fleet_churn/exp/controller_headroom_mb1024_r02/`, their stdout/stderr,
one preflight receipt, a prebuilt analysis binary outside the scientific root, and final evidence.
There is no network, provider, model, optimizer, checkpoint, registry, service, worker, resume, or
retry side effect.

Before every result-bearing invocation, record the exact Git SHA, interpreter, argv, working root,
output root, preflight receipt, and a process-list check proving no duplicate process targets that
root. Commit and push the launch surface first, launch detached from the agent process, and never
reuse an existing root. A failure classification requires reproduction over the recorded bytes.

## 11. Engineering scope, owned paths, and technical ceiling

This object requires **none** of the default-prohibited machinery in
`docs/project/ENGINEERING_SCOPE_SPEC.md` section 4. The exact fixed-capacity top-K reducer and its
scientific allocation counters are part of the declared computation, not orchestration. Required
telemetry is limited to wall time, OS-backed peak RSS, and the scientific live-capacity/byte
counters named above.

Owned implementation surfaces:

- `experiments/candidates/variable_n_fleet_churn_headroom/`;
- `scripts/run_vnfc_controller_headroom.py`;
- `tests/experiments/candidates/variable_n_fleet_churn_headroom/`;
- this card and frozen K=256 witness artifact; and
- the R02 result evidence, intake, DIRECTION update, and unattended audit row after observation.

The attempt remains below 2,000 new non-test research-code lines, the runner below 600 lines, and
orchestration below 30% of the research diff. Run one focused post-edit test pass and one focused
pre-launch pass; do not create a repeated smoke loop.

Technical success establishes only finite selector conformance and resource admission for this
bounded A/RECON execution. It cannot establish mechanism value, the controller optimum, learner
competence, sufficient training budget, stable superiority, transfer, safety, or deployment value.
