# Reconciliation — 20260801_variable_k_algorithm_direction

Ruling: `21_PRO_OPEN_RAW.md`, stage commit `4e190f29975f25f308b36d5784c47d3f28197839`.
(The response does not cite the commit textually; its binding to this round is
the transport receipt — operation key, userMessageId, two-snapshot completion.)

## What was decided

**A modified B1: the ordered package V-K0** on `two_timescale_role_free_actions`.

- **V-K0A — exact source-urgency qualification.** No training, no learned
  controller: an exhaustive legal KEEP/SET oracle over the R30 joint edit
  support, five-step external-return window `G_Δ` (Δ = 5 primitive steps =
  one offered check; k0=5, slow period 30, horizon 40), registered estimand
  `U_src = max(0, V_S − V_K)` maximized over the SAME legal joint support on
  both branches (a fixed-teammate contrast cannot carry the verdict on a
  role-free source — legal duty swaps can erase a direct cost). Canonical
  panel: 4 sign combinations × 2 anonymous slot permutations × 7 noninitial
  checks × 2 focals = 112 rows; initial check recorded but excluded (KEEP
  not legal there). Materiality `δ_U = 0.5` (one full target-slot
  improvement for one primitive step; 2.5 is the window maximum and must
  not be the threshold). URGENT > 0.5 < STABLE; exact 0.5 is BOUNDARY.
  Acceptance `TOY_HETEROGENEOUS_RENEWAL_URGENCY_IDENTIFIED` requires the
  structural pattern (one urgent + one stable focal at every fast-only
  change; two urgent at the joint change; permutation invariance of the
  unordered pair; each physical slot in both classes somewhere; no boundary
  row). Validity failure is `INVALID_RENEWAL_URGENCY_SOURCE_AUDIT` (eight
  conditions). A NOT_IDENTIFIED outcome retires this toy as a variable-k
  source and moves to another candidate (Alice–Bob live).
- **V-K0B — unrestricted-R30 natural-access screen**, launched only on a
  V-K0A pass. Existing learned-KEEP toy configuration unchanged apart from
  trace/analyzer hooks: `r30_fixed_clock_ar_edit`, supplied `axis4_xy_v1`
  executor, zero local observations, direct centralized state, six training
  seeds 2026080101–2026080106, 640,000 environment steps per seed, 16
  parallel envs, 1,000 outer updates, high PPO 3 epochs at 1e-3, external
  reward only, final checkpoint only, actual-exposure recording (a
  deviating run is invalid, never rescaled). Held-out evaluation per seed:
  64 episodes × 40 steps from one frozen common seed bank (new frozen
  namespace, never selected after checkpoint inspection), 32 canonical +
  32 reversed agent orders (roster prefix features are identity-indexed;
  the source is anonymous). Registered quantities: `U_opp,π` (n_select=2 /
  n_eval=2, disjoint streams), `U_SET,π` (diagnostic), `U_nat,π`, and the
  hazard propensity contrast `Δλ = E[1−p_KEEP | URGENT] − E[1−p_KEEP |
  STABLE]`. Support floor 192 URGENT + 192 STABLE eligible rows per seed
  (64 per class per order) else `R30_URGENCY_TRACE_SUPPORT_INSUFFICIENT`;
  competence floor LCB95(slow_match) > 0.75 and LCB95(fast_match) > 0.75
  under both orders else `R30_TOY_ACCESS_NOT_ESTABLISHED`. Primary gates at
  the ±0.5 materiality bound under seed-first nested bootstrap (10,000
  iterations, one frozen seed; training seed = top inferential unit).
  Eight-row first-match result system; WRONG_DIRECTION needs a UCB at or
  below the boundary; no expansion, no checkpoint selection, no rerun of a
  valid result.
- **Paired replay semantics** frozen: one immutable snapshot per
  counterfactual family (env + centralized state + skills + ages + mask +
  steps_to_check + agent order + hidden state + env/NumPy/torch RNG +
  checkpoint identity), restore per branch, same base draws, later agents
  respond autoregressively, exactly five primitive steps, no inner check.
- **Minimal bounded trace** (evaluation-only, not a training log):
  `renewal_check_trace.jsonl` (one row per offered check per agent),
  `renewal_counterfactual_units.jsonl` (one row per
  check-agent/base-draw/candidate), `source_oracle_panel.json`,
  `train_and_checkpoint_manifest.json`, `summary.json` reproducible solely
  from the row files. Segment-ending authority must distinguish voluntary
  SET from initial assignment, termination, mask change, team-intent
  boundary and forced renewal.
- **Not selected:** the three-arm comparison, any constrained
  renewal-class design, completing `(3,7,13,24)` as fixed-k evidence, UAV
  execution, delayed-credit infrastructure. Conditional next after a full
  pass (result 8): V-K1, true shared deterministic periods
  k∈{1..8} checks (validation/test bank split) versus unrestricted R30
  under one shared artifact and exposure contract.

## Where I was corrected

1. **R31–R33 are valid FAILs, retired.** RESEARCH_GOAL.md's "anchored
   R31–R33, R33 recording R30 safety PASS" is stale as scientific status —
   the safety PASS was a subordinate observation inside a failed IRSC gate.
   The reusable fact is only that R30 functioned as a carrier.
2. **`(3,7,13,24)` is not an admissible fixed-k arm on this toy** — it is
   the legacy sampled-duration catalogue for long-horizon Scenario 7; 13
   and 24 exceed the toy's eight offered checks; the toy config already
   overrides it. My B3 branch conflated a sampled-duration comparator, a
   true shared period, and an unrestricted policy.
3. **Fact 5 over-asked**: no primitive-step training trace is needed;
   renewal decisions exist only at offered checks, so the check-level
   evaluation trace is the smallest sufficient surface.
4. **The question hid two intervention estimands** (fixed-teammate direct
   vs total effect under autoregressive response); the deployed hook
   implements the second, and only the second can carry the verdict here.
5. **SMDP flags being on is not evidence of access.**
6. Matching obligation recorded for any future arms (identical state,
   roster, age, action support; a slow/fast label input would be an invalid
   positive).
7. A full V-K0 pass stays a toy-carrier result — none of the later claims
   (search efficiency, low-cardinality contribution, transport) attach.

## Next action

Workflow 5 step 2: PM code design of the V-K0 stack (oracle panel driver,
check-level trace hooks, counterfactual replay harness on the existing
forced-token surface, analyzer + result system), decision ledger, then the
touchpoint-2 conformance check. V-K0A runs only after that closes (it is
proof-sized: 112 exhaustive rows, no training).
