# HMASD Research Portfolio

Updated at: 2026-08-30T00:03:05Z

## OMP non-control migration boundary

This OMP portfolio consumes the non-control scientific and direction-state facts from
`../hmasd-main` at commit `d9e4d50be691334b1120b29cbaebd2ee4a713b1f`. The imported source
Portfolio table was updated at `2026-08-29T18:35:33Z`; the later Portfolio-wide PAUSE handoff was
updated at `2026-08-29T20:15:00Z`.

This file is the OMP durable scientific authority after this migration. Codex-native task IDs,
model labels, Windows/Codex worktree details, Browser tab identities, and `.codex`/`.agents`
routing rules recorded in source handoffs are provenance only. OMP execution continues to be
controlled by `.omp/AGENTS.md`, `.omp/RULES.md`, `.omp/WATCHDOG.md`, `.omp/agents/`, and
`.omp/skills/`. Scientific findings, claim ceilings, direction evidence, retained Effects, archive
hashes, and user PAUSE/RESUME boundaries are migrated as non-control facts.

The controlling user state at this boundary is `PAUSE`:

- The authorized advancing capacity remains exactly four.
- No successor, replacement direction, new provider operation, CM task, experiment, lifecycle
  mutation, or capacity refill is authorized while PAUSE remains active.
- `PAUSE` is not cancellation, scientific failure, parking, closure, or permission to interrupt a
  committed Effect.
- Representation migration note: this restores the `PARKED` schema representation only for the
  eight source-known parked rows. It does not activate, close, cancel, launch, send, refill capacity,
  or reinterpret science; `PAUSE` remains controlling. Every preserved reactivation condition and
  every other lifecycle, capacity, and scientific fact is unchanged.

Safe-boundary facts consumed from
`docs/research/portfolio/decisions/2026-08-29-four-slot-user-pause-handoff.md`, with
non-sending Agentify migration recovery at `2026-08-30T00:03:05Z`:

- `dual_epoch_receipt_survival` / DEARS reached terminal R02 science before the PAUSE boundary;
  there is no live Effect. On RESUME, do not reopen R02; Portfolio must consume the terminal result
  and any continuation is fresh WORK.
- `semigroup_consistent_duration_model_policy` / SCDMP is retained at
  `SYNTHESIS_READY / WAITING_REENTRY`. Convergence operation
  `499b71d6-ca35-42d6-9aee-4c1202a7a82d` in conversation
  `https://chatgpt.com/c/6a93307b-6410-83e8-b9e5-1ab428de2fc6` is same-operation Agentify strict
  `NATURAL_COMPLETION_VERIFIED` after `verifyExisting`, with response text SHA-256
  `b8b00486f55499bca574dbbd1a3ee90e23042a0aca76544e024f4d2e6ef0336f` and imported archive
  `docs/external-review/directions/semigroup_consistent_duration_model_policy/9f48f4a6bcace75fddeb/chatgpt/NATURAL_COMPLETION_ARCHIVE.json`
  SHA-256 `299c25b8fb5aa3f48744e6ba42fc5758aa68f89d3669ef8098583f5afb2e58b2`. On RESUME it is
  local archive review and EM disposition only; never resend or replace.
- `voronoi_quadrature_field_policy` / VQFP is retained at `SCOPE_FROZEN / WAITING_REENTRY`.
  Innovator operation `be82f31d-a7cc-4757-9dcb-1393653250fb` in conversation
  `https://chatgpt.com/c/6a933040-034c-83e8-9e8c-9e83eed1c1fa` is same-operation Agentify strict
  `NATURAL_COMPLETION_VERIFIED` after `verifyExisting`, with response text SHA-256
  `c5f6724fc5a656a6a02b968d4d6969b9c87e8bba25d09695d4b73913379fe162` and imported archive
  `docs/external-review/directions/voronoi_quadrature_field_policy/211d583818335dd612c7/chatgpt/NATURAL_COMPLETION_ARCHIVE.json`
  SHA-256 `4df09776b114da27e1e27a8434ebe8125639a3d8ffbae18beae376425e11f47c`. On RESUME it is local
  archive review and EM disposition only; never resend or replace.
- `opportunity_normalized_lease_gated_rebinding` / ONLGR is retained at
  `SYNTHESIS_READY / WAITING_REENTRY`. Its Convergence operation
  `5ab3f06b-1660-457a-a0a7-d153559dd667` is same-operation Agentify strict
  `NATURAL_COMPLETION_VERIFIED` after `verifyExisting`, with response text certified as 16,574 bytes
  and SHA-256 `26e953e72c914a842b7a1904c39e76efd016b405f69462ea55ef4e5e4189fcf7`; imported archive
  `docs/external-review/directions/opportunity_normalized_lease_gated_rebinding/80856894e5a297f1c755/chatgpt/NATURAL_COMPLETION_ARCHIVE.json`
  has SHA-256 `433aa6928f98b47833371a34b25ebf4365066d4646aeb6c02f17bbfd5200f231`. EM had not
  read/dispositioned it after PAUSE. On RESUME, only local archive revalidation and EM objection
  disposition are authorized; no provider operation is permitted.

## Imported 33-direction scientific portfolio

The table below is the current OMP scientific lifecycle, priority, capacity, and direction-owner
authority after consuming the non-control hmasd-main migration evidence. The source Portfolio had
reviewed the complete 33-direction set. Scientific priority and execution readiness are
deliberately separate: engineering effort, missing substrate, or transport availability can change
sequencing and the size of the next discriminator, but cannot by itself lower scientific priority or
produce `PARKED`/`CLOSED` lifecycle.

Scientific priority is globally qualitative: `ADVANCING`, `HIGH`, `MEDIUM`, `LOW`, or `TERMINAL`.
Execution readiness is independently qualitative: `LIVE`, `REVIEW-READY`, `GATE-READY`,
`OBJECT-REQUIRED`, `SUBSTRATE-REQUIRED`, `REENTRY-REQUIRED`, `NO-STANDALONE-WORK`, or
`TERMINAL`. These are not scores, probabilities, or a claim that cheaper science is more valuable.

Portfolio first applies a scientific quality floor: a clear question and non-goals, traceable
evidence, an interpretable discriminator, distinguishable scientific versus execution failure, and a
claim no stronger than the evidence. Directions above that floor are compared by decision relevance,
complementarity or substitution, shared assumptions and common failure risk, reversibility, stop
rule, and whether the next observation can change an investment action. Cost and readiness decide
how to stage a valuable question, not whether that question has value.

| Direction | Lifecycle | Priority | Direction owner | Updated at | Reason/condition |
| --- | --- | --- | --- | --- | --- |
| active_post_churn_population_flow_identification | PARKED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `REENTRY-REQUIRED`. The censored-flow draft remains unaccepted and containing public recurrence may absorb the hand-built order code. Re-open only after constructive and adversarial review identifies value beyond both generic and containing recurrence. |
| acvc | CLOSED | TERMINAL | NONE | 2026-08-29T15:04:58Z | Readiness `TERMINAL`. The learned joint veto lost to deterministic exact matching. Retain authenticated binding as a control in DEARS/RCLE; no independent adaptive-algorithm question remains. |
| commitment_residual_triggered_options | PARKED | MEDIUM | NONE | 2026-08-29T18:32:37Z | Readiness `REENTRY-REQUIRED`. Portfolio consumes terminal cycle `2026-08-29.8-portfolio-crto-probe-cut-01` at `HANDOFF_READY`: only scalar update-1,000 probe results persisted, while the exact probe parameters and Adam continuation state were discarded. The update-10,000 endpoint is therefore unobserved rather than failed, and no representation-versus-optimization polarity follows. PARK releases an operationally nonexecutable slot while preserving the scientific question. Re-open only on a provenance-linked process/VM snapshot or an exact full-state equality witness for the original update-1,000 continuation state; a canonical replay is a materially different object requiring a new Portfolio decision. |
| covariance_calibrated_information_clock | PARKED | MEDIUM | NONE | 2026-08-29T15:19:56Z | Readiness `REENTRY-REQUIRED`. Portfolio consumes terminal WORK `2026-08-28.10-four-01a04a02-ccic-successor-02`: valid bounded synthesis found that a legal arity-three typed-wedge statistic exactly absorbs the apparent covariance information, while mandatory Convergence failed only at transport. PARK is a comparative scientific allocation: re-open only with a new host where the legal wedge fails but covariance changes the native action, or as a separately frozen finite-work inductive-efficiency question against an arity-three-capable invariant learner. |
| degraded_incumbent_shadow_handover | REGISTERED | HIGH | NONE | 2026-08-29T16:57:57Z | Readiness `REENTRY-REQUIRED`. Portfolio consumes terminal preactivity-certificate WORK `2026-08-29.8-portfolio-dish-preactivity-certificate-01` at `SCOPE_FROZEN / TERMINAL_GAP`. Its mandatory Pro stage was `ZERO_SEND_FAILED` and supplies no scientific polarity. Two local audits found no proper subset, symmetry, static timing, containment-only or monotone-envelope certificate sufficient for the full R06 branch family; they did not synthesize direct-handover value. Preserve the unanswered high-value full object. Reentry requires eligible independent consultation (or exact waiver), a named <=8-core substrate/process design with result-blind concurrency/overhead evidence, a current-byte engineering map and fresh proportionality judgment. Cost and transport change staging only; neither PARKS or CLOSES DISH. |
| dual_epoch_receipt_survival | ACTIVE | ADVANCING | EM | 2026-08-29T18:35:33Z | Readiness `LIVE`. Sol/max EM `01a04e94-b3e0-77e2-ae27-6b29df5dad1a` owns fresh cycle `2026-08-29.8-portfolio-dears-semantic-currentness-02`, not R01. In one matched OWNER-lineage live-versus-broken pair the old retained bit is held fixed, while the current bit remains equal when live and becomes conditionally fresh after the break. Exact support and native-action headroom must precede any learning. Compare semantic-currentness-gated retention, equal-content ungated old-bit use, the unrestricted exact raw-history optimum and the competent bit-deleted reset. Stop unless the gated rule matches the raw optimum in both cells, beats reset live and beats ungated old-bit use broken. Any positive claim is deterministic currentness/protocol value only; exact raw containment, no learned-abstraction claim and all R01 nonclaims remain protected. |
| ec4g_r1 | CLOSED | LOW | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. Content, physical-calibration and selectivity gates failed. Portfolio closes standalone EC4G and retains its receipt-content controls as DEARS provenance; no scientific polarity transfers. |
| eociv_lite | PARKED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `OBJECT-REQUIRED`. Payload value at a real receiver opportunity remains scientifically distinct, but no fidelity-valid active episode population is identified. Re-open only with a support-neutral host proving nonzero opportunity prevalence, two-sided action-value headroom and payload sensitivity before learning. |
| event_triggered_budgeted_cooperative_renewal | CLOSED | TERMINAL | NONE | 2026-08-29T15:04:58Z | Readiness `TERMINAL`. Coordinated learned renewal and the stage oracle both lost to fixed-4. Fixed-k and common-rate controls are retained inside ONLGR/SCDMP; the same EBCR object is exhausted. |
| expressibility_gated_renewal_credit_relay | PARKED | LOW | NONE | 2026-08-29T15:04:58Z | Readiness `REENTRY-REQUIRED`. Repeated clean exact-population families had authentic severable association yet competent same-information generic estimation produced exactly zero different scarce decisions, allocation gain, normalized-utility gain and source-localized excess. Re-open only as a distinct finite-resource approximation/denoising question with matched information, work, parameters, optimization and native endpoints; do not rerun the exhausted relay objects. |
| field_slot_coordination | CLOSED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. The slot-plus-critical-member residual is a promising representation primitive but lacks a finite independent scientific object. Portfolio closes the standalone label and retains the primitive as a future SGSP gate; no scientific polarity transfers. |
| finite_semantic_boundary_support | PARKED | MEDIUM | NONE | 2026-08-29T16:26:22Z | Readiness `REENTRY-REQUIRED`. Portfolio consumes terminal R02 at `SCOPE_FROZEN / TERMINAL_GAP`. Its zero-send Pro gap supplies no polarity, but two independent local routes find the normalized AUTHENTIC and PREDICTIVE_INDEX processes pathwise identical and the proposed REASSOCIATED matching tuple internally inconsistent because it conditions on the emitted hint. Stop investing in the same equal-information carrier-access interface. Re-open only with consultation availability and a genuinely new causal edge in which binding changes permitted accessibility, authorization outcome, failure behavior or acquisition cost beyond an ordinary index; do not repair or rerun R01/R02. |
| metric_ground_transport_allocation | CLOSED | TERMINAL | NONE | 2026-08-29T15:04:58Z | Readiness `TERMINAL`. Two matched-support extensions remained nonstationary at the frozen inference boundary, so efficacy was not identifiable. Reusable sample-split and fail-closed infrastructure may transfer, but the direction does not reopen. |
| opportunity_normalized_lease_gated_rebinding | ACTIVE | ADVANCING | PORTFOLIO | 2026-08-29T16:00:05Z | Readiness `WAITING-REENTRY`. Retain the exact seven-tick robustness WORK at `SYNTHESIS_READY`: Innovator is COMPLETE and the sole Convergence operation `5ab3f06b-1660-457a-a0a7-d153559dd667` is same-operation Agentify strict `NATURAL_COMPLETION_VERIFIED`. The verified response text is 16,574 bytes with SHA-256 `26e953e72c914a842b7a1904c39e76efd016b405f69462ea55ef4e5e4189fcf7`; the imported natural-completion archive is `docs/external-review/directions/opportunity_normalized_lease_gated_rebinding/80856894e5a297f1c755/chatgpt/NATURAL_COMPLETION_ARCHIVE.json` with SHA-256 `433aa6928f98b47833371a34b25ebf4365066d4646aeb6c02f17bbfd5200f231`. Earlier exact evidence narrowed the object from exponential/lease/rebinding specificity to a generic physical-rate hypothesis; transport completion changes no science, lifecycle, priority or capacity. |
| optimizer_entropy_exposure_boundary_relay | CLOSED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. Optimizer-history carry changes later learning, but entropy exposure was not independently exposed. Portfolio closes standalone OEER and retains CARRY/FRESH optimizer history as a CRTO/RISP/SCDMP control; no scientific polarity transfers. |
| orbit_shadow_read | CLOSED | LOW | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. Owner-role binding reached the kernel but has no independent return-bearing value. Portfolio closes standalone Orbit and retains the primitive as DEARS provenance. |
| recct_lite | CLOSED | LOW | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. Authentication was exposed but left/right target interventions were identical and target effect was zero. Portfolio closes standalone RECCT and retains the target-expressibility cut as FSBS/EGRCR evidence; no positive credit claim transfers. |
| renewal_indexed_score_plasticity | REGISTERED | MEDIUM | NONE | 2026-08-29T15:19:56Z | Readiness `OBJECT-REQUIRED`. The structured recurrence remains scientifically sharp; incompetent containment and failed measurement do not justify PARK. Retain it as a registered option requiring both a technically accepted grouped-EVAL/FP32 object and a prospective native decision endpoint that can change investment before any learned run. |
| roster_consistent_latent_exploration | PARKED | MEDIUM | NONE | 2026-08-29T15:22:41Z | Readiness `REENTRY-REQUIRED`. Portfolio consumes terminal public-containment WORK `2026-08-29.8-successor-01a04a02-rcle-public-containment-03`. Its transport failure supplies no science, but valid prior CPC/containing-controller evidence already leaves no independent public physical-persistence value when complete stochastic CARRY is a member of competent REPLAN. Re-open only as a materially distinct finite-budget, private-state, partial-observation, changed-objective or decentralized-control question with direct recovery value; do not build another public containing host. |
| roster_smf | CLOSED | TERMINAL | NONE | 2026-08-29T15:04:58Z | Readiness `TERMINAL`. Exact census dominates sampled-mass compression under the current access law. Re-open only if the system makes exact census genuinely unavailable or materially different; no current independent investment remains. |
| scope_1s | CLOSED | LOW | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. Synthetic whole-epoch carrier separation lacks a production authenticated atom. Portfolio closes standalone Scope-1s and retains its ancestry/compatibility controls as FSBS/DEARS provenance. |
| semantic_graphon_shared_policy | REGISTERED | HIGH | NONE | 2026-08-29T17:25:41Z | Readiness `REENTRY-REQUIRED`. Portfolio consumes terminal short-gate WORK `SGSP-RG2Z-RSCF-SHORT-GATE-20260829-01` at `SCOPE_FROZEN / TERMINAL_GAP`. Innovator completed, but mandatory Convergence exhausted its replacement boundary with `SENT_INPUT_MISMATCH`; this supplies no scientific polarity. The strongest provisional observation is that no identified meaning-preserving discriminator fits the complete short-gate ceiling, while the smallest outcome-bearing learned projection-contact arm remains roughly 60-250 CPU core-hours. Preserve SGSP's high-value relational question without purchasing or closing it. Reentry requires the explicit user waiver/override named by the terminal result or a materially new Portfolio question; cost and transport alone cannot PARK or CLOSE it. |
| semigroup_consistent_duration_model_policy | ACTIVE | ADVANCING | EM | 2026-08-29T18:32:37Z | Readiness `LIVE`. Fresh Sol/max EM `01a04ec6-0cd2-74f3-b589-09083ae7670c` owns cycle `2026-08-29.8-portfolio-scdmp-opportunity-law-02`. One prospective law must jointly define the 16-state opportunity draw as a single-valued distribution and separate candidate-action selection from held-out expected-value estimation. It must preserve the noncommuting event/action semantics, require the order-erased foundation competence gate first, and stop before adapter, training or empirical activity if no coherent one-correction law survives. Migration recovery verified same-operation Pro Convergence natural completion: response text SHA-256 `b8b00486f55499bca574dbbd1a3ee90e23042a0aca76544e024f4d2e6ef0336f`, imported archive `docs/external-review/directions/semigroup_consistent_duration_model_policy/9f48f4a6bcace75fddeb/chatgpt/NATURAL_COMPLETION_ARCHIVE.json` SHA-256 `299c25b8fb5aa3f48744e6ba42fc5758aa68f89d3669ef8098583f5afb2e58b2`. PAUSE blocks scientific intake until local archive review and EM disposition. The exhausted native-I/C/O prompt and operations are not reused. |
| ucope | PARKED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `REENTRY-REQUIRED`. The exact R03 fixed-budget object is exhausted after 90/90 learned support failures, but this is nonidentification rather than evidence against acquisition. Re-open only on a genuinely new support-qualified host with prospective acquisition value and adequate learned support. |
| vap_folr_core | CLOSED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. Early typed owner-state reachability survives, but later calibration was nonidentifying and deterministic latches were stronger. Portfolio closes standalone VAP/FOLR and retains its carrier/invalidation primitives as DEARS/RCLE controls. |
| variable_n_fleet_churn | CLOSED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. Exact physical-command commutation is a useful prerequisite, not an independent return question. Portfolio closes standalone VNFC and retains the physical-key/presentation-invariance gate as an RCLE prerequisite; substrate burden does not negate the primitive's value. |
| voronoi_quadrature_field_policy | ACTIVE | ADVANCING | PORTFOLIO | 2026-08-29T17:21:12Z | Readiness `WAITING-REENTRY`. Retain EM `01a04e22-2f5a-7423-8b60-95d35d150109` and cycle `2026-08-29.8-portfolio-vqfp-proof-gate-01`. Three independent routes preserve a proof-sized K1={3/4} candidate with exact held-out headroom and reassociation-loss witnesses, while proving uniform-only geometry is absorbed by MASS; aggregate margins and the selected competent FREE comparison remain unobserved. Migration recovery verified the authorized Innovator operation `be82f31d-a7cc-4757-9dcb-1393653250fb` as same-operation Agentify strict `NATURAL_COMPLETION_VERIFIED`: response text SHA-256 `c5f6724fc5a656a6a02b968d4d6969b9c87e8bba25d09695d4b73913379fe162`, imported archive `docs/external-review/directions/voronoi_quadrature_field_policy/211d583818335dd612c7/chatgpt/NATURAL_COMPLETION_ARCHIVE.json` SHA-256 `4df09776b114da27e1e27a8434ebe8125639a3d8ffbae18beae376425e11f47c`. PAUSE blocks scientific intake until local archive review and EM disposition; this transport completion changes no science, lifecycle, priority or capacity. |
| vsp_02 | CLOSED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. Carry/reset paths differ but exact success sets match. Portfolio closes standalone VSP-02 and retains lifecycle/optimizer-history controls for CRTO/RISP/SCDMP. |
| vsp_03 | CLOSED | LOW | NONE | 2026-08-29T15:04:58Z | Readiness `TERMINAL`. No authenticated causal deployment-event seam or runtime activity exists. Its negative interface census remains provenance; no independent mechanism is actionable. |
| vsp_04 | CLOSED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. The finite-cell certificate is useful only after rows are generated from an authenticated host; declared-row ancestry was circular. Portfolio closes standalone VSP-04 and retains the solver/certificate control for FSBS. |
| vsp_05 | CLOSED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. Exactly-once handoff conformance is reusable infrastructure, but no eligible two-sided proposal truth or value claim exists. Portfolio closes standalone VSP-05 and retains the FSM as DEARS/RCLE/DISH infrastructure. |
| vsp_06_mssr | CLOSED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. Equal-information generic compilation reproduced admissible histories. Portfolio closes standalone VSP-06 and retains the dependency DAG and compiler null as DEARS/RCLE controls. |
| vsp_c1 | CLOSED | MEDIUM | NONE | 2026-08-29T15:04:58Z | Readiness `NO-STANDALONE-WORK`. The fourth-corner statistic is a clean local gate, but its authenticated four-clone production host is absent. Portfolio closes standalone VSP-C1 and retains the statistic and negative census for FSBS. |

Capacity is exactly four by direct user authorization. CRTO probe-cut R01 is terminal and is
independently PARKED because its exact continuation state is unidentified and no executable
decision-changing discriminator remains; this is neither a representation null nor a technical
lifecycle inference. Portfolio immediately refills the released slot with DEARS's materially new
semantic-currentness object. SCDMP, VQFP and ONLGR retain their exact WORKs. The allocated advancing
set is:

- `dual_epoch_receipt_survival`, EM `01a04e94-b3e0-77e2-ae27-6b29df5dad1a`, cycle
  `2026-08-29.8-portfolio-dears-semantic-currentness-02`: does a selected owner or lease-lineage
  break make equal retained content semantically stale in a way that changes the exact return-optimal
  native action, rather than merely triggering a hand-written verifier? Exact static support, the
  unrestricted raw optimum and reset/ungated controls decide whether any learned comparison exists.
- `semigroup_consistent_duration_model_policy`, EM `01a04ec6-0cd2-74f3-b589-09083ae7670c`, cycle
  `2026-08-29.8-portfolio-scdmp-opportunity-law-02`: can one prospective opportunity law, within
  the single-correction bound, both define the aliased opportunity-state draw unambiguously and
  eliminate same-tape action-selection/evaluation bias before any order-aware adapter or training?
- `voronoi_quadrature_field_policy`, EM `01a04e22-2f5a-7423-8b60-95d35d150109`, cycle
  `2026-08-29.8-portfolio-vqfp-proof-gate-01`:
  can a proof-sized exact variable-N field object retain native allocation/return headroom over
  competent FREE and lose value under physical-measure reassociation?
- `opportunity_normalized_lease_gated_rebinding`, EM `01a04a08-33a3-7292-8c21-95d17715ea2f`:
  on the frozen non-divisible clock cell, does any link-specific return survive common executed-rate
  and age-conditioned ceilings?

Operational liveness is separate from allocation and lifecycle. At the `2026-08-29T18:35:33Z`
source boundary, CRTO EM `01a04e91-e1bf-7791-bc1a-2a69c5b4bf39` was terminal and its slot was
released; source-native SCDMP and DEARS EM facts remain provenance only after OMP migration. Current
OMP runtime has no live imported EM/CM session: stale runtime agent rows were retired, and the four
legacy assignment worktrees were archived before exact release. SCDMP, VQFP and ONLGR provider
Effects are terminal same-operation Agentify strict `NATURAL_COMPLETION_VERIFIED` results and now
require only local archive review plus EM disposition after RESUME. DEARS has no retained provider or
run Effect. SGSP has terminalized and does not occupy capacity. Root owns shared transport repair; no
transport, runtime or worktree cleanup fact changes lifecycle or scientific priority.

The scientific reserve order after these activations keeps DISH as the highest raw-value reserve,
but not as a currently dispatchable refill: no materially new bounded EM question can change its
investment before the named substrate/scaling/current-byte premises exist, and repeating its failed
certificate search would not preserve value. SGSP is likewise high-value but presently has no new
meaning-preserving short discriminator. RISP remains object-required. DEARS is selected ahead of
these not because it is cheaper, but because its semantic-currentness counterexample yields a fresh,
exact and reversible decision gate now. Cost stages valuable science; it does not determine its
priority or polarity.

Five consolidated mechanism families now replace 33 independent labels:

1. authenticated semantic carrier and lineage: active DEARS with parked FSBS evidence and exact raw/index controls;
2. roster continuity and relational execution: registered high-value SGSP and DISH, with parked RCLE evidence and VNFC/field-slot/VSP-05 gates;
3. renewal, duration and opportunity: ONLGR, SCDMP, CRTO, RISP and the parked UCOPE alternative;
4. information and optimizer geometry: CCIC, with OEER/VSP-02 retained only as controls; and
5. spatial physical allocation: active VQFP, with MGTAP retained only as terminal methodology evidence.

Cross-family fusions are prospective scientific tests, not code merges or automatic claims. The
highest-value candidates are `CCIC × RCLE` (minimal relational information versus plan persistence),
`SGSP × RCLE` (role structure versus public-plan continuity), and a future requalified `FSBS × ONLGR`
(semantic content versus physical opportunity rate). Each requires a factorial design with both marginal gates and a
competent same-information containing null; neither component may borrow the other's positive claim.
Avoid `CCIC × MGTAP`, current `EGRCR × SGSP`, and ungated `ONLGR × UCOPE` because they duplicate the
same optimizer/representation/support failure or confound information with opportunity.

Shared risks across the advancing set remain bespoke finite hosts, work/information mismatch,
competent generic estimators absorbing proposed structure, evaluator saturation, and spending learned
budget before exact support and headroom. Transport, implementation and measurement facts affect
only evidence availability. They cannot create a lifecycle action, release a slot, or cancel a WORK.
A terminal WORK stops occupying advancing capacity at its terminal fact. Portfolio must consume it,
adopt an independent action, update authority and refill promptly; it cannot keep the old WORK
retroactively live while making that decision.

All source Codex task IDs, model/effort labels, worktree labels, and native-task liveness facts in
this file are provenance after OMP migration. Future execution uses the current OMP authorities in
`.omp/AGENTS.md`, `.omp/agents/`, and `.omp/skills/`; every direction retains separate scientific
ownership, writer history, provider conversations, Effects and terminal return.
