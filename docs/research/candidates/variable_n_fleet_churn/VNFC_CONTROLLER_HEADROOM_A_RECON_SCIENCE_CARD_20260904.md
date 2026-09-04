# VNFC controller-headroom A/RECON science card

- Object: `VNFC-CONTROLLER-HEADROOM-A-RECON-R01`
- Direction: `variable_n_fleet_churn`
- Frozen: `2026-09-04T09:39:49Z`
- Evidence class: `A/RECON`
- Result-bearing: `true` (measurement fact only; A objects have no consumption state)
- Provenance: owner decision F.6(a), 2026-09-03, in
  `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`
- Object-tier design provenance: `OWNER_DELEGATED`

## 1. Question and claim ceiling

On the first valid primary R02 panel's exact sixteen held-out `N=7` worlds, how much
failed-zone service during the first sixty post-loss seconds is physically available above the
causal fixed `BCRH-PERSIST` controller?

For each world the object brackets

```text
H_i = max_policy R_fail_60(i, policy) - R_fail_60(i, BCRH)
```

between (a) a witnessed lower bound supplied by a deterministic full-tape best-of-many search and
(b) the exact physical upper bound `1 - R_fail_60(i, BCRH)`. It asks whether the bracket proves
material headroom at the already derived one-acquisition-interval margin `delta_fail = 0.10`, proves
that material headroom is impossible, separates the two failed-zone strata, or remains unresolved.

**Claim ceiling.** A direct measurement fact about these sixteen simulator worlds, the named
native host, the named BCRH implementation, and the declared search budget. The search lower bound
is not the true optimum unless equality with the physical upper bound is observed. Nothing here is
an algorithm effect, a learner result, a deployable-policy comparator, a causal-information result,
or evidence of arbitrary-`N`, repeated-churn, general MARL, transfer, UAV, safety, flight, or
deployment performance.

## 2. Frozen population and evidence path

The panel is regenerated, not selected after this object's outcome:

- R02 configuration identity: `B1-B3-PRIMARY`, seed `2026090311`, updates field `64` only because
  that field is part of the already recorded R02 namespace;
- R02 installation, seed derivation and world law: first call `install_r02()` from
  `scripts/run_vnfc_bpcr_r02.py`, then use the inherited `derive_seed_master` and `_build_world`
  path from `scripts/run_vnfc_bpcr_b_explore.py` at the launch sha;
- purpose: `conclusion`; roster size: `N=7`;
- cells: failed zone `z in {1,2}`, rows `0..7`, exactly eight worlds per zone;
- namespace: `VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02/B1-B3-PRIMARY/2026090311` under the
  existing R02 canonical-sort adaptation.

**Pre-launch population-identity correction (2026-09-04T09:55:50Z).** The initial card commit
mistakenly printed the inherited R01 namespace even though every surrounding population clause
named the first valid R02 primary panel. The actual historical R02 runner calls `install_r02()`,
which changes `RUN_NAMESPACE` and the valid seed family before world generation. The R02 namespace
above is controlling; generating the corresponding R01 namespace is forbidden and would not
observe this object.

The choice of the first valid primary seed is outcome-blind with respect to controller headroom and
implements the owner's literal sixteen-world instruction. The other two R02 primary panels are not
opened by this object. Historical R02 endpoints may be used only to cross-check the regenerated
BCRH values byte-for-value; they do not select, tune, prune, or stop the search.

## 3. Treatment, comparators, and live explanations

### Treatment: `ORACLE-BEAM-FAIL60-K256`

The treatment is a deterministic, omniscient trajectory search, not a policy:

1. It sees the complete frozen exogenous tape of one world.
2. It acts only at post-loss epochs `0, 1, 2`; later commands cannot change `R_fail_60`.
3. At each retained native state it enumerates every command legal under the existing R09 native
   host law (at most 1,961 at `N=7`), applies one command, and advances exactly twenty native ticks.
4. After epochs 0 and 1 it retains at most 256 prefixes, ordered by decreasing cumulative
   failed-zone delivered seconds and then lexicographically by the complete physical command
   prefix. There is no random tie breaking, model score, return shaping, or outcome-adaptive width.
5. At epoch 2 it evaluates every legal continuation of the retained prefixes and selects the
   largest exact `fail_delivered / fail_demand`, with lexicographically smallest command history on
   a tie.
6. The witnessed lower-bound return is the maximum of the beam result, the exact persistent-command
   maximum below, and the separately replayed BCRH trajectory. It therefore cannot fall below the
   incumbent because of beam pruning.

**Pre-launch terminal-completion clarification (2026-09-04T09:45:04Z).** `R_fail_60` is complete
after the epoch-2 command has advanced the native host to sixty post-loss seconds, while the native
episode's `terminal` flag is reached only after epochs 3–5. For each selected beam or persistent
prefix, the runner sets `measurement_complete=true` at sixty seconds and freezes every selection,
endpoint and headroom quantity. It then completes epochs 3–5 with the lexicographically smallest
command returned by the unchanged current-state legal enumerator. Those commands are recorded
separately as `terminal_completion_commands` and are never inputs to search ranking, `R_fail_60`,
`L_i`, or `U_i`. BCRH retains its own unchanged six-command trajectory. A suffix terminal, safety,
or exclusivity failure conservatively makes the attempt `INCOMPLETE`; it never changes a headroom
value or creates result polarity.

The full tape is deliberately illegal information for BCRH and the learners. It is admissible here
only because the estimand is physical headroom, not attainable causal performance.

### Comparators

- **Decision comparator: `BCRH-PERSIST`.** The unchanged competent causal controller from R02,
  with its scorer/checker agreement, independent legal-command enumeration, and per-decision
  candidate counts recorded. Its six commands and exact endpoint are replayed on the same world.
- **Strongest same-information structural null: `PERSIST-MAX-C60`.** Given the same complete
  exogenous tape as the treatment, enumerate every legal epoch-0 command and persist it under the
  existing release rule through epoch 2. This is the exact best member of the registered persistent
  initial-command class and must agree with the existing native sensitivity maximum.
- **Physical upper bound.** `R_fail_60 <= 1` because delivered service is clamped by demand. Hence
  `U_i = 1 - R_fail_60(i, BCRH)` is an exact, search-independent upper bound on headroom.

Live explanations kept separate:

1. BCRH is already within one material acquisition interval of the physical ceiling, so this host
   cannot discriminate a larger learner budget.
2. Material physical headroom exists but the 64-update learners did not reach it; a budget ladder
   remains informative.
3. Headroom is zone- or world-specific, explaining the R02 reversal and requiring a population
   recast rather than a pooled budget ladder.
4. The beam is too narrow to close the lower/upper bracket; search nonidentification is not host
   saturation and has no scientific polarity.

## 4. Observable, estimand, and result branches

The runner publishes, for every `(zone,row)`:

- exact integer numerator/denominator for BCRH, persistent maximum, and beam best;
- all three physical command trajectories;
- `measurement_complete` at sixty seconds and the separately named three-command terminal suffix
  for the beam and persistent paths;
- BCRH scorer/checker/enumerator agreement and candidate counts;
- beam state, expansion, legal-command and native-tick counts by depth;
- `L_i = max(R_beam,R_persist,R_BCRH) - R_BCRH`;
- `U_i = 1 - R_BCRH`;
- whether `0 <= L_i <= H_i <= U_i` is respected; and
- terminal, safety and exclusivity flags.

The primary estimands are the arithmetic means of `L_i` and `U_i` over all sixteen worlds and over
each eight-world failed-zone stratum. Individual worlds remain visible. The material margin is
frozen as `delta_fail = 0.10`, the six-second acquisition interval divided by the minimum
sixty-second failed-zone demand denominator, transferred from the accepted BPCR definition.

Apply the following rule in order:

1. **`CH-A / MATERIAL_HEADROOM`.** Aggregate and both zone-stratum lower-bound means are each
   `>= 0.10`. The sixteen worlds have material physical headroom despite beam nonoptimality.
   Recommend the already named one-seed MAPR budget ladder (256 then 1,024 updates, exposure line
   reported); this does not predict that MAPR can exploit the headroom.
2. **`CH-B / NO_MATERIAL_HEADROOM`.** Aggregate and both zone-stratum upper-bound means are each
   `< 0.10`. Even a perfect policy cannot clear the material margin. Recommend re-posing the host
   before another learner run and escalate that direction-tier recast to
   `em:variable_n_fleet_churn:convergence`.
3. **`CH-C / ZONE_HETEROGENEOUS_HEADROOM`.** One zone has lower-bound mean `>= 0.10` and the other
   has upper-bound mean `< 0.10`. Recommend a direction-tier population/estimand recast through the
   convergence node; do not pool the zones or launch the budget ladder.
4. **`CH-D / HEADROOM_BRACKET_UNRESOLVED`.** Every other complete valid result. The search budget
   does not decide between saturation and unused headroom. Recommend as the reversible object-tier
   next discriminator one prospectively carded wider/exact search only if its runner-derived
   projection fits the same per-invocation machine-time cap; otherwise escalate a recast. Do not
   infer that BCRH is sufficient.
5. Missing any world, invalid native execution, BCRH disagreement, unsafe/illegal transition,
   missing required endpoint, or machine-time termination is `INCOMPLETE`, not a headroom branch.

## 5. Prediction on record

- DM prediction: `CH-A / MATERIAL_HEADROOM`. The full-tape search should exploit obstruction and
  demand information unavailable to BCRH, while the R02 treatment-blind sensitivity rows already
  establish nontrivial command consequences. Confidence is moderate because BCRH explicitly
  protects the early failed-zone floor.
- Owner prediction: `not taken (unattended)`.

## 6. Budget, cost law, exposure, and stop rule

There is one search arm, `K=256`, and one result-bearing invocation.

The runner's prospective worst-case cost law is

```text
beam_expansions_per_world(K) <= 1961 + 2 * K * 1961
beam_expansions_total(K)     <= 16 * (1961 + 2 * K * 1961)
native_ticks_total(K)        <= 20 * beam_expansions_total(K)
```

At `K=256` this is at most `1,005,993` command expansions per world,
`16,095,888` expansions over the panel, and `321,917,760` native ticks. The separate exact
persistent baseline adds at most `16 * 1961 * 60 = 1,882,560` native ticks. BCRH adds exactly 96
decision calls and at most `96 * 1961 = 188,256` scored current-command candidates. Actual counts
must be recorded from the runner.

- Per-arm machine-time cap: 2,700 wall seconds.
- Resource envelope: one process, no child process or worker pool, one computational thread,
  expected peak RSS below 2 GiB; a fresh repository 4-GiB physical/effective memory admission is
  mandatory immediately before invocation.
- Pre-launch cost admission: CM must evaluate the implemented runner's exact operation projection
  against the formulas above. If it exceeds 2,700 seconds on a result-blind technical calibration,
  the arm is not launched and the object returns an engineering blocker.
- Stop rule: stop after all sixteen worlds and both baselines are complete. The runner checks the
  clock only between worlds and returns `INCOMPLETE` if the cap is reached; it does not publish a
  partial scientific branch. No result-informed width increase, extra seed, or second invocation is
  part of R01.

**Exposure line.** There are zero learner parameters, model initialisations, optimizer steps,
training transitions, checkpoints, or model-selection exposures. Search exposure is exactly the
reported legal-command expansions and native ticks above. Therefore parameter displacement against
initialisation scale is `not applicable (A/RECON, no learner)`.

## 7. Protected semantics and side effects

The implementation must preserve the existing R02 world bytes, native host transition and
legality law, integer endpoint accounting, BCRH scoring/tie/release law, float64/RNG behavior of the
source runner, and all historical artifacts. It must not edit the R01/R02 runner, R09 native host,
or old results merely to make the new search convenient. A new read-only adapter or separately
built analysis backend may reuse those sources without changing them.

Permitted side effects are one new result root under
`temp/directions/variable_n_fleet_churn/exp/controller_headroom_r01/`, one preflight receipt, the
runner's stdout/stderr log, and final JSON/Markdown evidence. A prebuilt analysis binary may be
created during implementation/tests outside the scientific root. The result run creates no model,
optimizer, checkpoint, registry, service, network action, or provider conversation.

Before launch record the exact Git sha, argv, interpreter, output root, preflight receipt, and proof
that no process already targets that root. Launch detached from the agent process. A technical
failure is classified only after reproduction over the recorded bytes.

## 8. Engineering scope and owned paths

This object needs **none** of the default-prohibited machinery in
`docs/project/ENGINEERING_SCOPE_SPEC.md` section 4: no distributed execution, resume/retry/lease,
tamper evidence, provenance guard, incident tree, schema framework, registry, compatibility shim,
telemetry beyond wall time and peak RSS, or repeated smoke loop. The in-memory beam is scientific
computation, not scheduling machinery.

Expected owned surfaces:

- `experiments/candidates/variable_n_fleet_churn_headroom/` (new read-only analysis adapter);
- `scripts/run_vnfc_controller_headroom.py` (single-use runner, at most 600 lines);
- `tests/experiments/candidates/variable_n_fleet_churn_headroom/`;
- this card, its result evidence and intake; and
- the 2026-09-04 unattended audit row.

The change may add at most 2,000 non-test code lines, keeps orchestration under 30% of its diff, and
runs focused tests once after editing and once immediately before launch. Any budget breach is
returned and recorded rather than hidden. Technical success can establish only that the declared
search executed and produced an auditable bracket; it cannot establish mechanism value, learner
competence, or deployable control.

## 9. Non-goals

No MAPR or DIRECT training; no new seed; no use of the other R02 primary panels; no retuning of
BCRH; no causal oracle claim; no proof that the beam found the optimum; no optimization of
`U_total`, `U_intact`, or `J_ext`; no change to presentation, action, RNG, checkpoint, precision, or
native-host semantics; no lifecycle, priority, capacity, fusion, or Portfolio decision.
