# Portfolio–Operational reconciliation — 2026-08-14

## Purpose and ownership

This is the current, human-readable reconciliation surface requested by the
user.  It joins the dedicated portfolio session's decision record with the
operational Root's direction-stage routing record.  It is not a replacement for
owner-authored science cards, CM technical packets, complete results, or the
direct decision channel.

- **Portfolio owner:** Codex session `019ffc20-5001-7453-a08a-dac783cf4d80`.
  It owns investment, deferral, competition, and claim-boundary decisions.
- **Operational owner:** the current Root.  It owns creation of EM/CM pairs,
  compute leases, unchanged-science execution, technical integration, and
  forwarding only decision-level scientific milestones.
- **Direct channel:** `codex_app__send_message_to_thread`; the older mailbox
  files are historical audit material only.

The rows below intentionally contain no runtime stream, partial metric, seed
value, PID, resource reading, or provider transport detail.

## Reconciled frontier

### Operational pair/stage/lease update — post-result adjudication

This table updates only the operational pair, stage, and lease surface in
response to `ONLGR_B2_SCDMP_B3_POST_RESULT_PORTFOLIO_ADJUDICATION_20260814.md`,
read with `RCLE_B2_POST_RESULT_PORTFOLIO_ADJUDICATION_20260814.md` as base
evidence; the portfolio-decision columns elsewhere remain owner-authored.

| Direction | Current pair | Current stage | Lease state |
| --- | --- | --- | --- |
| RISP | Reused `/root/em_renewal_indexed_score_plasticity` + `/root/cm_renewal_indexed_score_plasticity`. | Definition-only outcome-coupled recurrence composite is frozen and its CM feasibility packet is accepted. The existing-Pro closure request and one mutually blind Gemini innovation request are frozen but unsent; no empirical activity. | No lease. `BEST-REACHABLE-X`, new coordinates, source change, construction, implementation, tests, probes and compute remain unauthorized. |
| SGSP | Reused `/root/em_semantic_graphon_shared_policy` + `/root/cm_semantic_graphon_shared_policy`. | The sole fresh 240-update object is frozen and result-blind. Its already-committed existing-Pro closure is pending the separate transport owner's observe-only recovery; CM has not yet been asked to construct or run it. | No successor lease until the existing closure is observable and CM accepts the exact object; r05 lease is historical. |
| RCLE | Released: `/root/em_roster_consistent_latent_exploration` + `/root/cm_roster_consistent_latent_exploration` completed their B2 envelope. | Exact B2 is complete and immutable. The portfolio ended the four-strategy formulation's current investment; Root schedules no further RCLE activity absent a future Level-1 target-bound decision. | `temp/leases/RCLE_B2_R02_ROOT_PRODUCTION_LEASE_20260814.json` is a completed execution record; r04 lease is historical. |
| ONLGR | Released: `/root/em_opportunity_normalized_lease_gated_rebinding` + `/root/cm_opportunity_normalized_lease_gated_rebinding` completed their B2 envelope. | Exact B2 is complete and immutable; portfolio absorbed this state-blind timing-rate formulation into learned global-rate handling. No current ONLGR activity, rerun, retuning, direct-value, second-surface or UAV work. | `temp/leases/ONLGR_B2_R02_ROOT_PRODUCTION_LEASE_20260814.json` is a completed execution record. |
| SCDMP | Released: `/root/em_semigroup_consistent_duration_model_policy` + `/root/cm_semigroup_consistent_duration_model_policy` completed their B3 envelope. | Exact B3 is complete and immutable under branch-2 nonidentification. No current SCDMP activity, hard-wired probe, direct-value successor, second surface or UAV work. | `temp/leases/SCDMP_B3_R01_ROOT_PRODUCTION_LEASE_20260814.json` is a completed execution record. |

### Final Root scheduling notification rule

For every active direction pair, a complete technically accepted result does
not end in silent owner-local convergence.  When the same-direction EM has
finished its result intake and the required existing-conversation Pro
convergence, the EM must proactively send Root one final scheduling
notification.  It contains only: exact direction/revision, completion fact,
conclusion, strongest alternative, claim ceiling, next discriminator, whether
the pair can be reused, and the exact Root action needed.  It contains no
partial values, runtime stream, receipt, hash, provider mechanics, or automatic
portfolio decision.

Root acknowledges that notification by recording the stage state and then
either (a) executes an already-issued portfolio action, (b) relays a compact
material portfolio packet, or (c) keeps/reuses the pair for an authorized
unchanged-science successor.  A completed child alone is never treated as a
silent release or an implicit direction deferral.

### Main-session completion relay — Root obligation

The EM/CM direct channel is intentionally same-direction and therefore does
not substitute for a user-visible completion report.  Once Root receives an
EM's final scheduling notification, Root must promptly post one concise notice
to this main session: exact direction/revision, whether the full result and
same-Pro convergence are complete, the conclusion and claim ceiling in plain
language, the resulting Root/portfolio routing, and whether any execution
remains.  Root must do this even when no new user decision is needed.  CM-only
technical acceptance is reported as such and is not presented as scientific
completion.  Runtime, partial results, receipts and provider mechanics remain
excluded.

### HISTORICAL_NONOPERATIVE — pre-result current-status snapshot

The block from this heading through the final pre-result active-investment
correction immediately before `Portfolio-owner post-result decision` is a
historical snapshot only. It has no routing force and cannot restart an exact
object. The operative operational surface is the post-result pair/stage/lease
table above; the operative portfolio surface is the post-result owner table
below. The historical block contains no partial results or runtime streams.

| Direction | Current operational fact | Current owner/action boundary |
| --- | --- | --- |
| SGSP-r05 | CM technically accepted full frozen B1; EM completed result intake and existing-Pro convergence. Exact r05 is complete and immutable. | Compact portfolio packet sent. A portfolio decision is required before a new 240-update successor; r05 cannot be rerun or altered. |
| RISP-r07 | CM technically accepted full frozen Lock-2; EM completed result intake and existing-Pro convergence. Exact r07 is complete. | Compact portfolio packet sent. A portfolio decision is required before a `BEST-REACHABLE-X` versus `LEARNED-X` successor. |
| ONLGR-r04 core | CM technically accepted the retained-checkpoint core; EM completed intake and existing-Pro convergence. Exact r04 core is complete. | Compact portfolio packet sent. A portfolio decision is required before RATE-FLEX versus RATE-CONST or simpler-family absorption. |
| RCLE-r04 | CM technically accepted full frozen B1; EM completed result intake and existing-Pro convergence. Exact r04 is complete and immutable. | Compact portfolio packet sent. A portfolio decision is required before a `VALIDITY_ONLY_SEMANTIC_SPECIFICITY_CONTROL` successor; r04 cannot be rerun or altered. |

| Direction / exact object | Portfolio decision in force | Operational stage and CM entry | Next recordable milestone |
| --- | --- | --- | --- |
| **SGSP-r05** | Leading static-variable-`N` investment; preserve its same-conversation Pro-closed, EM-intaken frozen object.  Current claim remains the registered finite toy only. | **Active CM flow expanded.** Pair: `/root/em_semantic_graphon_shared_policy` and `/root/cm_semantic_graphon_shared_policy`.  CM technically accepted static r05 conformance without a science ambiguity.  The full frozen B1 discriminator is now authorized under Root lease `temp/leases/SGSP_B1_R05_ROOT_PRODUCTION_LEASE_20260814.json`; its fresh result root is lease-bound and result-blind. | Complete technically accepted B1 package → EM intake → existing-Pro result convergence.  Return only for a material science/claim/cost change, not a routine continuation decision. |
| **RCLE-r04** | Leading persistent-latent static-variable-`N` investment; preserve its Pro-closed, EM-intaken frozen object and hidden-lock claim boundary. | **Active CM flow expanded.** Pair: `/root/em_roster_consistent_latent_exploration` and `/root/cm_roster_consistent_latent_exploration`.  The prior "construct later or remain unbuilt" gate is removed: CM now owns bounded construction/static conformance, followed after technical acceptance by the frozen B1 discriminator under a Root lease. | Complete technically accepted B1 package → EM intake → existing-Pro result convergence.  Return only for a material science/claim/cost change, not a routine construction or lease decision. |
| **RISP-B1 r07** (`renewal_indexed_score_plasticity`) | Leading direct exogenous-variable-`k` route.  Complete the exact frozen Lock-2 panel on the same blinded coordinates; the former 60-minute slice expiry has no scientific force. | **Entered CM flow.** Pair: `/root/em_renewal_indexed_score_plasticity` and `/root/cm_renewal_indexed_score_plasticity`.  CM owns result-blind, atomic, same-coordinate continuation and technical acceptance under the one-CPU/no-GPU/<1-GiB rolling-slice lease; EM awaits only the complete accepted result. | Complete technically accepted panel → EM frozen intake → reuse the existing RISP Pro conversation for result convergence.  Root forwards a compact packet only if this changes portfolio value, claim ceiling, competition, or the high-information successor. |
| **ONLGR-r04 checkpoint-only core** (`opportunity_normalized_lease_gated_rebinding`) | Invest the exact preserved-checkpoint core.  All 24 sole final checkpoints are retained; complete native/IID/safety/fixed-rate/held-out/KEEP-grid/partition/post-startup-support core without retraining, resampling, or partial-result selection.  Claim ceiling is finite-host, finite-budget eligible-physical-exposure event-link bias versus RAW only. | **Entered CM flow.** Pair: `/root/em_opportunity_normalized_lease_gated_rebinding` and `/root/cm_opportunity_normalized_lease_gated_rebinding`.  CM owns the evaluator-façade repair, blinded checkpoint-only replay, resumable atomic frontier, and technical acceptance under the one-CPU/no-GPU/<1-GiB rolling-slice lease.  EM awaits only a complete accepted result. | Complete technically accepted core → EM frozen intake → reuse the existing ONLGR Pro conversation for result convergence.  Root forwards only a material decision-level change. |
| **SCDMP-B2-r02** | **No current investment in literal r02**, for the scientific reason that its prospectively required auxiliary signal at the frozen wrong-order control/update point is below the required relation-specific scale; completing cells cannot reach its stated deletion branches.  This is not family deletion. | Not entered into a current CM flow.  No remaining-cell completion is authorized by this decision. | Revisit only through a newly frozen stability-first three-arm successor, same-Pro closure, and fresh blinded coordinates if a named portfolio condition occurs (RISP nonqualification/nonidentification, ONLGR inability to yield bounded direct result, a leading compositional-dynamics/reward need, or operationally decision-changing adverse-r02 information). |

## Other directions — no new decision in this record

This reconciliation creates no batch no-current-investment decision and does
not revalidate historical dispositions as a group. MGTAP, CMSP, APFI, BIR-C,
DCPR, LISR, ALACB, ACTRC, VQFP, homogeneous CCIC, CRTO, EBCR, VNFC and other
historical directions remain governed individually by their latest
portfolio-owner decision, its plain scientific/value reason and its concrete
revisit condition. A conditional backup is not a terminal status and is not
automatically equivalent to a no-current-investment direction.

If an older disposition depends only on missing code, a stopped resource slice,
a provider incident, an incomplete panel, an attempt count, or a child label,
that rationale has no current portfolio force under P0 and cannot be preserved
by this reconciliation. Apart from the explicit literal SCDMP-B2-r02 row above,
this file neither adds nor renews a no-current-investment decision.

## Separate operational recovery

The Agentify/Gemini recovery is a non-scientific transport workstream.  It has
an explicit action-time user-confirmation boundary for one bounded synthetic
native-input test.  That boundary is separate from, and cannot pause or alter,
the RISP or ONLGR scientific investments, their compute scheduling, or their
unchanged-science completion.

## Update rule

The operational Root updates this record only when a stage is created/released,
a complete owner-accepted result reaches EM intake, a compact scientific
milestone is sent to the portfolio session, or the portfolio session issues a
new decision.  The dedicated portfolio session may correct or append only the
portfolio-decision portions.  Routine execution/retry/provider status belongs
to the corresponding owner log and is excluded here.

## Portfolio-owner clarification — 2026-08-14

The reconciliation is accurate except for one potentially ambiguous portfolio
word: **RCLE-r04 is a current investment, not a conditional backup.** SGSP-r05,
RCLE-r04, exact RISP-r07 completion, and exact ONLGR-r04 checkpoint-core
completion are all presently invested. RCLE may be lower in current relative
priority than SGSP on the static-`N` axis, but that does not change its admission
or authorize a fixed rank, direction count, or action quota.

For completeness, ONLGR's stated finite-host exposure-link ceiling also excludes
lease causality, `REBIND` causality, event-head-versus-mark-head causality, RAW
incapacity, arbitrary `k`, performance within the already exceeded historical
resource gate, and UAV efficacy. These are claim-boundary clarifications only;
they do not alter the recorded operational stage. The dedicated portfolio
session does not validate or amend the operational-stage/CM-entry columns.

## Portfolio-owner correction — active-investment semantics — 2026-08-14

The earlier SGSP-r05 and RCLE-r04 cells saying that no new pair was opened
described an incomplete Root transition; they were **not** an admissible durable
portfolio state. Both directions are current investments with unfinished,
actionable work. Operational Root has now recorded active stage-paired EM/CM
scopes for both, each ending at a named next decision-level milestone.

This correction removes the implicit two-active-flow cap created when only RISP
and ONLGR entered new flows. It does not impose equal compute concurrency: a
concrete host conflict may sequence heavy commands. It does require all other
in-envelope scientific, construction, optimization, provider, and milestone
work to proceed without waiting for another invested direction to close. If
SGSP or RCLE should cease receiving work, that requires a new portfolio
decision with a plain scientific/value/cost reason and revisit condition; it
cannot be inferred from absence of an EM/CM pair.

The active pairs also must not be empty staging shells. The exact current-
investment decision authorizes SGSP-r05 to move from source/static conformance
to its frozen B1 discriminator on technical acceptance, and RCLE-r04 to move
through bounded construction/static conformance to its frozen B1 discriminator
on technical acceptance. The earlier RCLE milestone phrased as "authorize
future construction or retain an unbuilt backup" is superseded: current
investment selects construction. Operational Root owns the revised envelopes,
technical sequencing and compute leases; the portfolio reopens only for a
science-bearing change or a materially new total/opportunity-cost fact.

## Portfolio-owner post-result decision — 2026-08-14

This section appends only the dedicated portfolio owner's decision. It does not
assert, validate or alter any EM/CM pair, technical stage, lease, runtime or
result-installation fact. Operational Root owns those columns and updates them
separately.

This is the base decision before RCLE-B2 completion. The later
“Portfolio-owner RCLE-B2 result delta” section supersedes its RCLE row and
four-investment count.

| Scientific object | Portfolio decision now in force | Exact portfolio-owned boundary |
| --- | --- | --- |
| RISP-r07 and proposed `BEST-REACHABLE-X` | Exact r07 is complete; **no current investment** in the diagnostic. | The successor only localizes an upstream failure and cannot test structured recurrent value, held-out variable-`k` performance or bridge eligibility. Preserve the four revisit conditions in `CROSS_DIRECTION_POST_RESULT_ADJUDICATION_20260814.md`; do not open a twin, second surface or UAV work. |
| SGSP-r05 | Exact r05 is complete and immutable; **invest** the sole fresh 240-update successor. | Exactly one update-240 checkpoint, complete r05 four-arm/causal structure, fresh disjoint coordinates, no budget/checkpoint/early-stop search, and existing-Pro closure before construction/activity. |
| RCLE-r04 | Exact r04 completed after the earlier reconciliation; do not rerun it. **Invest** the sole `VALIDITY_ONLY_SEMANTIC_SPECIFICITY_CONTROL` successor. | Preserve the r04 object and compare RCLE only with `B_VALID=V` on fresh blinded coordinates. Match maximum positive auxiliary scale while acknowledging unmatched realized score/optimizer geometry. The full value/codebook/fidelity/cuts conjunction makes retention eligible; every other complete result makes no-further-investment in this exact formulation eligible, without rescue or tuning. The complete EM/Pro-converged result must return to the dedicated portfolio owner before either action occurs. |
| Full ONLGR-r04 eligible-exposure/content-conditioned parent | **No current investment.** | The parent mechanism is nonidentified; neither the old surface nor exposure/content/lease/rebind/UAV claims reopen. |
| `ONLGR-B2-STATE-BLIND-EVENT-RATE-FLEXIBILITY` | **Current investment.** | Only task-content-blind `RATE-FLEX` versus `RATE-CONST`, fixed `rho=0.5`, matched conditions, and the original IID gate. Passing makes retention of only the timing-rate family eligible; nonpassing makes fixed-rate absorption eligible. The complete EM/Pro-converged result returns to the dedicated portfolio owner before action. |
| Literal SCDMP-B2-r02 | **No current investment; no family deletion.** | Do not complete literal r02 merely to fill cells. |
| SCDMP stability-first successor | **Current investment.** | Preserve the three arms, one update-zero scale calibration followed by fixed scaling, later gradient decay as outcome, fresh coordinates and the complete registered qualification panels. A positive remains enabling fixed-`N=4` evidence only. |

The resulting current investment set is SGSP-240, RCLE-validity-only,
ONLGR-B2-rate and SCDMP-stability-first. The count is not a quota. There is no
WIP, order, action-count or first-result gate; only conflicting heavy commands
may be sequenced. No SGSP×RCLE, RISP×ONLGR, cross-`N×k` parent, second surface
or UAV production is authorized.

Operational Root should now append its own pair/stage/lease changes and mark its
obsolete sole-action/mailbox/unbuilt-backup handoff language historical. The
full portfolio rationale and return conditions are in
`CROSS_DIRECTION_POST_RESULT_ADJUDICATION_20260814.md`.

## Portfolio-owner RCLE-B2 result delta — 2026-08-14

This appends only the dedicated portfolio owner's new decision. Operational
Root owns the corresponding pair/stage/lease update.

| Scientific object | Portfolio decision now in force | Exact portfolio-owned boundary |
| --- | --- | --- |
| `RCLE-B2-SCIENCE-20260814-02` | Complete and immutable under `UNRESOLVED_VALIDITY`; **no current RCLE investment**. | The value contrast is unresolved and every seed lacks the required four-rotation bijection, although anchored fidelity and both common/persistent functional cuts pass. The protected rule ends the exact four-strategy formulation without rescue. |
| Broader common/persistent-latent exploration | **Not deleted; conditional revisit only.** | A named held-out-variable-`N` task failure plausibly needing shared persistent commitment plus a decision-relevant coarse/learned-cardinality hypothesis may reopen bounded EM definition. Construction/activity requires the later complete prospective object, frozen outcome map and fresh coordinates. Exact-package value may leave optimizer geometry unresolved; semantic or commitment causality requires score/optimizer-matched or containing control. It is not an active direction now. |

At this now-superseded RCLE-B2 base cut, the investments were SGSP-240,
ONLGR-B2-rate and SCDMP-stability-first. Three was not a quota, and RCLE
completion created no automatic replacement,
fusion, second surface or UAV action. Operational Root records exact B2 as
complete, ends the RCLE stage and releases its pair from the current envelope;
all other direction stages continue unchanged. The controlling owner record is
`RCLE_B2_POST_RESULT_PORTFOLIO_ADJUDICATION_20260814.md`.

## Portfolio-owner ONLGR-B2 / SCDMP-B3 result delta — 2026-08-14

This is a portfolio-owner delta only. It does not write Root operational
stage, pair, provider or lease truth. The controlling scientific record is
`ONLGR_B2_SCDMP_B3_POST_RESULT_PORTFOLIO_ADJUDICATION_20260814.md`.

| Scientific object | Portfolio decision now in force | Exact portfolio-owned boundary |
| --- | --- | --- |
| ONLGR-B2 state-blind event-rate flexibility | **No current investment; absorb to global rate.** | The exact package is complete and immutable; mean paired IID gain `+0.0009782886505126948`, 95% CI `[-0.0013577707092971786, 0.0033143480103225683]`. Both registered positive conditions failed: mean `>=0.02` and paired 95% lower bound `>0`. Claim ceiling is supported nonpassage for this exact host/package only; no equivalence, sufficiency, hazard, lease/REBIND, arbitrary-`k`, UAV or general claim. |
| SCDMP-B3 stability-first | **No current investment; no family deletion or automatic successor.** | Branch-2 is complete and immutable, with useful wrong-relation manipulation qualification not passing (`W_SHUF` one-sided upper bound `0.02422161` below useful `0.040`). Claim ceiling is exact fixed-`N=4`, 1,000-update calibrated-package nonidentification; no deletion, equivalence, direct task-value, variable-`k` value, second-surface or UAV claim. |
| SGSP | **Current empirical investment: SGSP-240.** | This is the sole current empirical investment and remains subject to its own frozen object and claim boundary. |
| RISP | **Definition-only investment: value-bearing, outcome-coupled recurrence.** | Root may create or reuse paired RISP EM/CM under a fresh definition envelope only. Reuse the existing RISP Pro conversation for closure after EM freezes the complete composite, and permit one mutually blind RISP-specific Gemini innovation consultation; neither provider owns portfolio action. No construction, new coordinates, source change, tests, probes or compute is authorized until the Pro-closed object and CM feasibility packet support a later portfolio judgment. |

The ONLGR and SCDMP two-level revisit conditions remain exactly those in the
controlling adjudication: ONLGR Level 1 requires independent disjoint-coordinate
evidence of reproducible ex-ante timing/tenure strata with materially different
best rates and headroom over pooled global rate; Level 2 requires frozen strata,
one shared parameterization across external `k`, matched global comparator,
value/robustness endpoint, fresh coordinates, Pro closure and CM acceptance.
SCDMP Level 1 requires a named variable-`k` target/bridge where directional
order is necessary and the assay could choose, delete or modify a learnable
treatment; Level 2 requires the frozen action map to a variable-`k` value test,
shared competent checkpoint, identical hard-wired order paths, wrong-relation
separation as sole primary endpoint, fresh coordinates and ordinary review/
technical boundaries.

CCIC-r08 is not reopened because its unclosed/preactivity homogeneous/
equicorrelation host remains scalar-ESS-reducible with only a weak bridge;
heterogeneous covariance may justify a future revisit. These are scientific
allocation decisions, not resource, provider or engineering stops. There is no
quota, backfill, fusion, UAV study, cross-`N×k` parent, WIP or ordering gate.
Operational Root owns pair release/creation, provider and lease columns and
the corresponding acknowledgement; this delta does not alter those facts.
