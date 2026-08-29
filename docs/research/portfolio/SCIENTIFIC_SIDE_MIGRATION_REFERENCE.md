# HMASD scientific-side migration reference

Updated at: 2026-08-29T20:15:00Z

## Purpose and migration boundary

This document is the scientific-side migration reference for HMASD. It is intended for a fresh
Portfolio or EM operator who must recover the current research program without importing retired
workflow machinery, reopening old material cycles, losing claim ceilings, or converting technical
facts into scientific or lifecycle decisions.

This reference is explanatory. It does not itself change lifecycle, priority, capacity, ownership,
dispatch, scientific findings, provider operations, CM work, experiments, or successor selection.
At the migration cut recorded here, the user's Portfolio-wide `PAUSE` remains controlling. The
authorized advancing-capacity limit remains exactly four, but PAUSE forbids refill or new Effects.

The repository facts were reconciled against shared main through
`7555d2a03f39ce05007dc20dea51a14c2ed72881`, which contains the integrated DEARS R02 science and
pause handoff. The Portfolio table itself is the authority at its own recorded update boundary;
later native task results and direction handoffs are reconciliation facts until Portfolio explicitly
consumes them. Never silently rewrite one namespace from another.

## 1. Authority order and import sequence

Migrate in this order. Later entries add narrower scientific or observational facts; they do not
override the ownership of earlier entries.

| Order | File or native object | What it owns | What it does not own |
| ---: | --- | --- | --- |
| 1 | `AGENTS.md` | Shared field meanings, role boundaries, Effect rules, model configuration, Git/writer invariants | A direction's current finding or Portfolio action |
| 2 | `docs/project/WORKFLOW_PROTOCOL.md` | Sole cross-task transport, liveness, fan-out/join, PAUSE/RESUME/CANCEL, handoff and writer-transfer authority | Scientific polarity or lifecycle priority |
| 3 | `.agents/skills/hmasd-portfolio-task/SKILL.md` | Current Portfolio method and decision-loop entry contract | Direction science |
| 4 | `.agents/skills/hmasd-em-task/SKILL.md` | Current EM scientific method and milestone discipline | Portfolio lifecycle action |
| 5 | `.agents/skills/hmasd-cm-task/SKILL.md` and `.agents/skills/hmasd-browser-conversation/SKILL.md` | Current CM execution method and shared Browser Conversation method | EM interpretation or Portfolio action |
| 6 | `.agents/skills/hmasd-root-task/SKILL.md` | Shared-core, protocol, conflict and cross-direction integration method | Direction science or Portfolio investment |
| 7 | `docs/project/ALGORITHM_PRINCIPLES.md` | Cross-direction scientific evidence, comparator, claim and integration principles | Current queue, direction owner or one-off numerical gates |
| 8 | `docs/research/portfolio/PORTFOLIO.md` | The only current lifecycle, scientific priority, execution readiness, capacity and direction-owner table | Native task liveness, transport completion, or a direction's detailed claim |
| 9 | Native Portfolio and EM task history | Exact inbound WORK, current material cycle, task liveness, committed Effects, later controls and unintegrated handoffs | Lifecycle unless Portfolio explicitly records an action |
| 10 | `docs/research/candidates/<direction>/DIRECTION.md` | Accepted direction question, current accepted finding, claim ceiling, next discriminator and evidence map | Lifecycle, priority, capacity or owner |
| 11 | Current-cycle evidence, external and milestone files | Frozen question, observations, objections, archives, transport availability and latest accepted milestone | Broader direction or Portfolio authority by filename alone |
| 12 | `docs/research/RESEARCH_MAP.md` | Navigation across the 33 direction IDs and their code/test locations | Current lifecycle, owner, task status or dispatch |
| 13 | Portfolio decisions, legacy reports, old intakes and old prompts | Provenance and rationale at their historical boundary | Current authority unless explicitly re-adopted by a current owner |

The migration operator should first verify the intended shared-main commit, then read the files in
the order above, then reconcile native task history and exact direction handoffs. Do not infer the
current cycle from the newest-looking filename, timestamp, branch head, browser tab, or process
status.

## 2. State namespaces that must remain separate

The most damaging migration error is collapsing independently owned states into one word such as
"active", "done", "failed" or "waiting". Preserve these namespaces separately.

| Namespace | Owner and values | Correct interpretation |
| --- | --- | --- |
| Top-level `Outcome` | Any top-level task: `DONE`, `WAITING`, `FAILED`, `CANCELLED` | Whether the current inbound WORK was answered, retained, ended without acceptance, or explicitly cancelled. `DONE` does not mean positive science. Only received `CANCEL` can produce `CANCELLED`. |
| Portfolio action | Portfolio: `NONE`, `ACTIVATE`, `CONTINUE`, `NARROW`, `PARK`, `CLOSE`, `FUSE`, `SPINOFF` | Independent investment/lifecycle judgment. An EM recommendation is advice only. |
| Capacity action | Portfolio: `KEEP` or `SET <n>` | Advancing-capacity limit, not a count of browser operations or currently running processes. |
| EM scientific status | EM: `IN_PROGRESS`, `SYNTHESIZED`, `NO_MATERIAL_INSIGHT`, `NOT_REACHED` | Whether the frozen scientific question has a bounded synthesis. It does not encode transport or lifecycle. |
| EM/CM snapshot | `WORKING`, `WAITING_REENTRY`, `TERMINAL_GAP`, `COMPLETE` | Last accepted milestone state for one WORK. `WAITING_REENTRY` retains the same WORK. A terminal snapshot never reopens; only successor WORK opens a fresh cycle. |
| Research milestone | Common sequence such as `SCOPE_FROZEN`, `SYNTHESIS_READY`, `REVIEW_RESOLVED`, `HANDOFF_READY` | Scientific progress actually reached. Missing mandatory review prevents promotion, even if local analysis is strong. |
| Transport state | `PENDING`, `ZERO_SEND_FAILED`, `COMMITMENT_UNKNOWN`, `SENT_WAITING`, `COMPLETE`, `SENT_INPUT_MISMATCH`, `SENT_MODEL_MISMATCH`, `SENT_UNREADABLE`, `CONVERSATION_LOST`, `WAIVED` | Evidence-availability and one strict provider operation only. It never supplies scientific polarity, lifecycle, capacity or successor authority. |
| Native task status | Desktop task active/idle/terminal plus current turn state | Execution/liveness fact. An idle task can retain a live WORK or sent provider Effect; an active task is not automatically an ACTIVE direction. |
| Git/writer state | Baseline, detached/worktree HEAD, writer owner, fast-forward handoff | Provenance and serialization. A commit is not scientific acceptance or Portfolio action by itself. |

Additional invariants:

- `WAITING` retains the exact WORK and names a concrete reentry. It does not release the direction.
- `PAUSE` retains the same WORK, freezes new launch/send, and lets committed Effects reach only the
  minimum safe observable fact. It is not cancellation, parking or capacity release.
- `RESUME` continues the exact retained WORK. It is not a successor and does not reset operation
  budgets.
- `FAILED` may be a workflow/transport failure with `Scientific status: NOT_REACHED`; it cannot be
  read as a negative scientific result.
- A terminal EM WORK releases an operational slot only after Portfolio consumes the result and
  records its own action. A label in a table without a dispatched retained WORK is not advancing
  capacity.
- Engineering cost and readiness may stage or bound a discriminator. They cannot erase scientific
  value or automatically lower priority.

## 3. Portfolio authority and lifecycle method

### 3.1 Sole lifecycle table

`docs/research/portfolio/PORTFOLIO.md` is the sole current table. Its rows separate:

- lifecycle: `ACTIVE`, `REGISTERED`, `PARKED`, or `CLOSED`;
- scientific priority: `ADVANCING`, `HIGH`, `MEDIUM`, `LOW`, or `TERMINAL`;
- execution readiness: `LIVE`, `REVIEW-READY`, `GATE-READY`, `OBJECT-REQUIRED`,
  `SUBSTRATE-REQUIRED`, `REENTRY-REQUIRED`, `NO-STANDALONE-WORK`, or `TERMINAL`;
- direction owner and explicit reason/reentry.

At the audited Portfolio boundary the 33 directions comprise 4 `ACTIVE`, 3 `REGISTERED`, 8
`PARKED`, and 18 `CLOSED` rows. The compact catalog below is for migration checking; the full row
text in `PORTFOLIO.md` remains authoritative.

| Lifecycle | Directions at the audited Portfolio boundary |
| --- | --- |
| `ACTIVE` | `dual_epoch_receipt_survival`, `opportunity_normalized_lease_gated_rebinding`, `semigroup_consistent_duration_model_policy`, `voronoi_quadrature_field_policy` |
| `REGISTERED` | `degraded_incumbent_shadow_handover`, `renewal_indexed_score_plasticity`, `semantic_graphon_shared_policy` |
| `PARKED` | `active_post_churn_population_flow_identification`, `commitment_residual_triggered_options`, `covariance_calibrated_information_clock`, `eociv_lite`, `expressibility_gated_renewal_credit_relay`, `finite_semantic_boundary_support`, `roster_consistent_latent_exploration`, `ucope` |
| `CLOSED` | `acvc`, `ec4g_r1`, `event_triggered_budgeted_cooperative_renewal`, `field_slot_coordination`, `metric_ground_transport_allocation`, `optimizer_entropy_exposure_boundary_relay`, `orbit_shadow_read`, `recct_lite`, `roster_smf`, `scope_1s`, `vap_folr_core`, `variable_n_fleet_churn`, `vsp_02`, `vsp_03`, `vsp_04`, `vsp_05`, `vsp_06_mssr`, `vsp_c1` |

Later native results do not silently edit this catalog. For example, DEARS R02 reached terminal
science before the user PAUSE; that is a result Portfolio must consume after migration, not an
automatic lifecycle mutation.

### 3.2 Meaning of Portfolio actions

| Action | Meaning |
| --- | --- |
| `ACTIVATE` | Begin active investment in a qualified direction and bind a current WORK. |
| `CONTINUE` | Retain the current scientific scope after comparative review. |
| `NARROW` | Retain only an explicitly smaller surviving scope; state what is removed. |
| `PARK` | Preserve the direction without active investment and record exact reentry. It is not a negative theorem. |
| `CLOSE` | End standalone investment because a terminal scientific/investment reason is established. Reuse of controls does not reopen the label. |
| `FUSE` | Move a surviving question into another direction because the mechanisms/decision object are genuinely the same; do not fuse merely because transport or tooling is shared. |
| `SPINOFF` | Create a distinct scientific object whose mechanism, estimand or claim boundary differs materially. |
| `NONE` | No lifecycle decision. Common for WAITING, transport gaps and incomplete reviews. |

### 3.3 Allocation loop

The Portfolio operator should run this loop continuously when not paused:

1. Re-anchor to shared authority and native history; inventory actual WORK, writers and Effects.
2. Consume every terminal EM result immediately. Separate reached science from transport,
   implementation and observation gaps.
3. Validate the claim ceiling, strongest support, strongest contradiction, competent nulls,
   remaining alternatives, common dependencies and next discriminator.
4. Compare directions by decision relevance, complementarity/substitution, common failure risk,
   reversibility, stop rule and whether the next observation can change an investment decision.
5. Make a Portfolio action independently. An EM recommendation is evidence, not an automatic action.
6. Update and commit Portfolio authority before dispatching a new successor or replacement.
7. Recompute live advancing WORK. If below capacity, screen all admissible candidates and refill the
   strongest qualified complementary slot. `WAIT` is valid only when capacity is genuinely full or
   a recorded comparison finds no admissible candidate with a concrete reentry.
8. Join retained nonterminal WORK natively. Do not create an extra direction merely because a
   browser operation is waiting.

Shared transport, substrate and CM failures affect evidence availability and staging only. They
cannot directly produce `PARK`, `CLOSE`, `FUSE`, cancellation, or capacity release.

## 4. Scientific operator topology

### 4.1 Portfolio

Portfolio owns cross-direction quality floor, comparative investment, lifecycle, priority,
capacity, fusion/separation, dispatch and join. It reads all direction science but does not replace
EM synthesis. Portfolio may use only bounded general leaves; it does not call specialist research
or engineering leaves directly.

New top-level Portfolio and EM tasks use `gpt-5.6-sol/max`. CM uses `gpt-5.6-sol/high`. A fresh
operator must verify the actual native configuration rather than trusting a task name.

### 4.2 EM

EM owns one direction's bounded scientific question, evidence interpretation, claim ceiling,
discriminator, Pro prompt authorship, direction authority and terminal recommendation. It may call
read-only research Scout, Innovator, Principles Analyst or Critic leaves and the prescribed Pro
transport path. Leaves return evidence; they never substitute for EM judgment or emit top-level
results.

An EM cycle should preserve:

- exact question, estimand, world, information set and non-goals;
- result-blind controls, competent containing nulls and alternative explanations;
- prospective gates, margins, stopping branches and claim ceiling;
- source, RNG, checkpoint, timing, identity and Effect semantics;
- current milestone and exact reentry when incomplete;
- strongest support and contradiction, not only the preferred story.

### 4.3 Pro Innovator and Pro Convergence

The two mandatory Pro stages are scientific checks, not transport ceremonies:

- **Innovator** challenges the frozen question before EM commits to an expensive or narrow route.
  It searches for mechanism candidates, counterexamples, cheaper meaning-preserving discriminators
  and missing controls.
- **Convergence** receives a fresh conclusion-blind, owner-authored question after EM has a bounded
  synthesis packet. It independently tests whether objections are resolved and the claim ceiling is
  warranted.

Unless explicitly waived, both must be accepted before the corresponding milestone can advance.
Only an exact provider-visible prompt, naturally complete attributable response and archived/reread
response produce `COMPLETE`. EM must read and interpret the archive; transport completion alone is
not `REVIEW_RESOLVED`.

One strict operation sends at most once. `SENT_WAITING`, `COMMITMENT_UNKNOWN` and `SENT_UNREADABLE`
retain the same operation/conversation and allow observation only. A mismatch or lost conversation
isolates it and permits at most the protocol-defined single new-conversation replacement. A
`ZERO_SEND_FAILED` fact proves no provider injection, but it does not by itself authorize an
unbounded series of fresh operations.

Conversation IDs, user/assistant IDs, hashes and response paths are evidence locators. They are not
task identity, WORK identity, direction identity, lifecycle state or a home-grown receipt ledger.

### 4.4 EM to CM and back

CM is opened only when an executable observation is scientifically answer-changing. Exact algebra,
static proof or source audit should end the branch without CM when they already decide it.

Before writer transfer, EM freezes a cohesive CM contract containing:

- scientific question, competing explanations and discriminating predictions;
- exact acceptance, stop rule, non-goals and claim boundary;
- protected numerical, RNG, checkpoint, ordering, identity and Effect semantics;
- baseline commit, owned source/test/result paths and resource/observer requirements;
- exact command or staged run plan, required artifacts and what a technical failure means.

The direction has one Git-visible writer at a time. The normal chain is EM commit, CM starts from the
exact transfer commit, CM writes/verifies and returns its direct-child commit, then EM accepts only
by exact fast-forward and reclaims writer ownership. CM reports engineering, observation and
verification facts; it never authors scientific synthesis. A passing implementation or command is
not a scientific pass, and a launcher/measurement failure is not a scientific null.

## 5. Direction files and evidence semantics

### 5.1 `DIRECTION.md`

Every direction has:

`docs/research/candidates/<direction>/DIRECTION.md`

It is the mechanism-level scientific authority and should state the stable direction ID, accepted
question/finding, claim ceiling, strongest support/contradiction, next discriminator and evidence
set. It never owns lifecycle, priority, capacity or Portfolio owner. If it still describes an older
cycle, use current native history and handoff to recover the live WORK; do not invent a newer finding
or overwrite the accepted older one.

### 5.2 Durable evidence categories

Common patterns are:

```text
docs/research/candidates/<direction>/*SCIENCE_CARD*.md
docs/research/candidates/<direction>/*RESULT*.json
docs/research/candidates/<direction>/*INTAKE*.md
docs/research/candidates/<direction>/*HANDOFF*.md
docs/research/candidates/<direction>/*FREEZE*.md
docs/research/candidates/<direction>/*MAP*.md
docs/research/candidates/<direction>/*CLOSURE*.md
docs/research/candidates/<direction>/evidence/*
docs/research/candidates/<direction>/external/*
docs/research/candidates/<direction>/workflow/research/state.json
docs/research/candidates/<direction>/workflow/engineering/state.json
```

Filename classes do not establish recency or authority. Select the current cycle from Portfolio,
native history and exact handoff, then follow only that cycle's evidence pointers.

`evidence/` normally contains scope freeze, derivation, result packet, synthesis, review disposition,
terminal gap and handoff notes. `external/` normally contains exact owner-authored prompts,
responses and transport facts. A prompt is a frozen scientific request; a response is evidence only
after exact natural completion and archive certification. A transport-fact file records evidence
availability only.

### 5.3 Milestone snapshots

Research snapshots, when material, are stored at:

`docs/research/candidates/<direction>/workflow/research/state.json`

Engineering snapshots, when material, are stored at:

`docs/research/candidates/<direction>/workflow/engineering/state.json`

Validate them with `scripts/hmasd_state.py` against
`scripts/schemas/hmasd_research_state.schema.json` or
`scripts/schemas/hmasd_engineering_state.schema.json`. A snapshot is the last accepted milestone,
not a complete task registry. It may legitimately trail later native history and unintegrated
direction commits. Missing snapshots are not evidence that no work exists.

### 5.4 Code, tests and raw artifacts

Use `docs/research/RESEARCH_MAP.md` to locate:

```text
experiments/candidates/<mapped-code-dir>/
tests/experiments/candidates/<mapped-code-dir>/
temp/directions/<direction-id>/exp/
temp/directions/<direction-id>/test/
```

Candidate code and tests are engineering objects. Raw `temp/` results and provider archives can be
essential evidence, but they are not current authority and may be Git-ignored. Import them only
when an exact current evidence/handoff reference supplies the path, bytes/hash and interpretation
boundary. Never treat an orphan raw result as accepted science.

### 5.5 Scientific role and verification support files

When migrating the repository rather than only its research record, preserve these supporting
contracts as a matched set:

- `.codex/config.toml` and the tracked `.codex/agents/hmasd-*.toml` profiles used by the current
  Portfolio, EM, CM, research-leaf and verification roles;
- `.agents/roles/GENERAL_LEAF.md`, `RESEARCH_SCOUT.md`, `RESEARCH_INNOVATOR.md`,
  `RESEARCH_PRINCIPLES_ANALYST.md`, `RESEARCH_CRITIC.md`, plus the CM-side scout,
  implementer/reviewer/verifier/operator role documents used by a frozen EM-to-CM contract;
- `scripts/hmasd_file_fingerprint.py` for exact UTF-8 prompt/response identity;
- `scripts/hmasd_state.py` and the research/engineering state schemas named above;
- `scripts/hmasd_science_capabilities.py`, `configs/scientific-capabilities-v1.toml`,
  `scripts/hmasd_resource_preflight.py` and `scripts/hmasd_run.py` when a future frozen CM contract
  actually uses them;
- contract tests including `tests/hmasd_native_workflow_contract_test.py`,
  `tests/hmasd_state_contract_test.py`, `tests/hmasd_file_fingerprint_test.py`,
  `tests/hmasd_science_capabilities_test.py`, `tests/hmasd_resource_preflight_test.py` and
  `tests/hmasd_run_test.py`.

These files support method and verification. They do not become scientific evidence simply because
their tests pass, and a historical execution-kernel or local ledger must not be imported as a
replacement for native task history.

## 6. Migration-cut four-direction handoff

The user ordered every direction to pause at the next safe boundary. Capacity remains exactly four
by prior direct user decision, but no refill or new Effect is authorized while PAUSE is active.
The unique shared Browser Transport task is
`01a04dd4-2b91-7bf2-9cfa-beb55dbf8e65`; it multiplexes transport assignments and is not a direction
slot or scientific owner.

### 6.1 Safe-state summary

| Direction | Native EM and cycle | Scientific/milestone state at PAUSE | Provider/Effect fact | Exact reentry |
| --- | --- | --- | --- | --- |
| DEARS | `01a04e94-b3e0-77e2-ae27-6b29df5dad1a`; `2026-08-29.8-portfolio-dears-semantic-currentness-02` | Terminal before PAUSE: `DONE / SYNTHESIZED / HANDOFF_READY`; accepted R02 direction finding | Innovator and Convergence `COMPLETE`; no CM or live Effect | Do not reopen R02. Portfolio must consume the terminal result; any continuation is fresh WORK after RESUME. |
| SCDMP | `01a04ec6-0cd2-74f3-b589-09083ae7670c`; `2026-08-29.8-portfolio-scdmp-opportunity-law-02` | `SYNTHESIS_READY / WAITING_REENTRY`; provisional `NO_COHERENT_ONE_CORRECTION_OPPORTUNITY_LAW`, pending review | Innovator `COMPLETE`; Convergence operation `499b71d6-ca35-42d6-9aee-4c1202a7a82d` in conversation `6a93307b-6410-83e8-b9e5-1ab428de2fc6` is `SENT_WAITING`; sole live provider Effect | Resume same task/WORK, then same-assignment `OBSERVE_ONLY` only. Never resend, replace, continue or edit. If complete, fingerprint/read archive and resolve objections. |
| VQFP | `01a04e22-2f5a-7423-8b60-95d35d150109`; `2026-08-29.8-portfolio-vqfp-proof-gate-01` | `SCOPE_FROZEN / WAITING_REENTRY`; K1 exact candidate survives, aggregate gate and FREE unobserved | Innovator operation `be82f31d-a7cc-4757-9dcb-1393653250fb` in conversation `6a933040-034c-83e8-9e8c-9e83eed1c1fa` is `SENT_WAITING`; one retained provider Effect; no CM or Convergence | Resume same task/WORK and exact Browser assignment; observe this operation/conversation only. Never resend or replace. Complete/waive Innovator before synthesis or CM. |
| ONLGR | `01a04a08-33a3-7292-8c21-95d17715ea2f`; `2026-08-29.4-robustness-01a04a02-onlgr-successor-04` | `SYNTHESIS_READY / WAITING_REENTRY`; accepted pre-review exact synthesis, final objection disposition withheld | Innovator and Convergence `COMPLETE`; no live Effect. PAUSE arrived after Convergence certification but before EM read it. | Resume same task/WORK; helper-revalidate unchanged archive, read it, disposition every objection, then advance review/handoff if supported. No provider operation is permitted. |

An allocated slot, native task state and live Effect are distinct. At this cut DEARS has a terminal
WORK and no Effect; SCDMP and VQFP each retain one paused sent provider Effect; ONLGR has no live
Effect but retains unfinished EM review work. No slot may be refilled until PAUSE is lifted and
Portfolio records an action.

### 6.2 Exact current files

#### DEARS

- `docs/research/candidates/dual_epoch_receipt_survival/DIRECTION.md`
- `docs/research/candidates/dual_epoch_receipt_survival/DEARS_SEMANTIC_CURRENTNESS_GATE_R02.md`
- `docs/research/candidates/dual_epoch_receipt_survival/DEARS_SEMANTIC_CURRENTNESS_R02_PAUSE_HANDOFF.md`
- `docs/research/candidates/dual_epoch_receipt_survival/DEARS_ONLINE_CARRIER_VALUE_GATE_R01.md`
- `docs/research/candidates/dual_epoch_receipt_survival/DUAL_EPOCH_AUTHENTICATED_RECEIPT_SURVIVAL_SCIENCE_CARD.md`
- `docs/research/candidates/dual_epoch_receipt_survival/DEARS_B1_SCIENTIFIC_INTAKE.md`
- `docs/research/candidates/dual_epoch_receipt_survival/DEARS_PROJECT_ALIGNMENT_ADDENDUM.md`
- `docs/research/candidates/dual_epoch_receipt_survival/DEARS_TYPED_LIFECYCLE_ONLINE_CHURN_DISCRIMINATOR.md`

R02 terminal science is commit `45e03908c3d32362c3c28f964637508dd8097f32`; its pause handoff is
commit `d176967027b1ae94c7a7ad9ec0949b63c337c0ca`, integrated to main through `7555d2a0`.
R01/B1/VNFC material is provenance at its original claim ceiling.

#### SCDMP

- `docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_OPPORTUNITY_LAW_CYCLE_FREEZE_20260829.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_OPPORTUNITY_LAW_GPT56_PRO_INNOVATOR_PROMPT_20260829.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_OPPORTUNITY_LAW_SYNTHESIS_READY_20260829.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_OPPORTUNITY_LAW_GPT56_PRO_CONVERGENCE_PROMPT_20260829.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_OPPORTUNITY_LAW_PAUSE_HANDOFF_20260829.md`
- Raw accepted Innovator archive under
  `temp/directions/semigroup_consistent_duration_model_policy/exp/2026-08-29.8-portfolio-scdmp-opportunity-law-02/pro/`

The safe handoff is direction commit `1dc5709d5bda5c60c9de57dc5be95cea65e0188a`. Older
`SCDMP_NATIVE_ICO_*`, B1/B2/B3 and target-bound files are scientific provenance unless cited by
the current cycle; they must not replace the current opportunity-law handoff.

#### VQFP

- `docs/research/candidates/voronoi_quadrature_field_policy/DIRECTION.md`
- `docs/research/candidates/voronoi_quadrature_field_policy/VQFP_PROOF_SIZED_ASSOCIATION_GATE_R01_SCIENCE_CARD_20260829.md`
- `docs/research/candidates/voronoi_quadrature_field_policy/VQFP_PROOF_SIZED_ASSOCIATION_GATE_R01_PRO_INNOVATOR_QUESTION_20260829.md`
- `docs/research/candidates/voronoi_quadrature_field_policy/VQFP_PROOF_SIZED_ASSOCIATION_GATE_R01_PAUSE_HANDOFF_20260829.md`
- `docs/research/candidates/voronoi_quadrature_field_policy/workflow/research/state.json`
- Historical support: `VQFP_VARIABLE_N_PHYSICAL_ASSOCIATION_VALUE_R03_SCIENCE_CARD_20260823.md`
  and its cited construction/cost/feasibility intakes.

The safe handoff is direction commit `ed16a0043952510043eb87947980908bc5d30e3f`. The planned
current Innovator response path does not exist because the response is not certified. Older FERL,
VNPA and R03 files remain provenance and do not authorize R03 execution.

#### ONLGR

- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/DIRECTION.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-scope-and-grounding.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-preliminary-exact-derivation.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-em-synthesis.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-convergence-packet.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-pause-handoff.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/external/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-pro-innovator-prompt.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/external/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-pro-innovator-response.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/external/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-pro-convergence-prompt.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/external/2026-08-29-2026-08-29.4-robustness-01a04a02-onlgr-successor-04-pro-convergence-response.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/workflow/research/state.json`

The safe handoff is direction commit `47a34c885ef60d59f5ef12c6225b7d1f0449d358`. The
Convergence archive is
16,185 bytes with SHA-256
`33143f2857ddc9a4504098c51964093d609b44177f3a1c08a90783be60fb58e3`; it was certified but not
scientifically read after PAUSE.

### 6.3 Portfolio-level pause handoff

The cross-direction safe-boundary record is:

`docs/research/portfolio/decisions/2026-08-29-four-slot-user-pause-handoff.md`

It records the controlling user decision, exact four task/cycle states, Effect boundaries,
comparative reserve context and reentry sequence. It is a handoff/provenance record, not a
replacement lifecycle table.

## 7. Historical and provenance-only material

Preserve historical material, but do not import it as current authority:

- `docs/research/portfolio/decisions/*.md` records past Portfolio reasoning. Every current action
  still belongs in `PORTFOLIO.md`.
- `docs/research/portfolio/legacy/2026-08-29-standalone-direction-closure-report.md` is explicitly
  legacy/provenance-only. It must not occupy advancing capacity or block successor work.
- `docs/research/workflow-runs/**` contains retired/pre-cutover workflow logs.
- `docs/research/cdc/**` preserves longitudinal scientific lineage; queues and current status in
  those files are non-authoritative.
- `docs/research/designs/**` records historical designs/code-science relationships.
- `docs/research/literature/**` is source background, not work authorization.
- Old `*_CHATGPT_*`, `*_GEMINI_*`, `*_PRO_*`, `*_AGENTIFY_*`, prompt, intake, closure and handoff
  files remain provenance unless the current `DIRECTION.md`, state snapshot, Portfolio row or exact
  native WORK cites them.
- Archived Codex tasks are provenance. Do not reuse them as a current top-level target.
- Historical provider conversations, tabs and operations must not be reopened or reused unless the
  exact retained WORK explicitly names same-operation observation as reentry.
- Candidate code, fixtures, tests and raw results do not authorize scientific claims, lifecycle or
  another run.

Closed standalone directions may contribute controls or failure modes to another direction only at
their original claim ceiling. That reuse is not positive evidence for the receiving direction and
does not automatically imply `FUSE`, `SPINOFF` or reactivation.

## 8. Migration reconciliation checklist

### Repository and authority

- [ ] Verify shared-main commit and clean Root checkout; do not switch branches in
  `C:/Projects/HMASD`.
- [ ] Read `AGENTS.md`, protocol, Portfolio/EM skills and `ALGORITHM_PRINCIPLES.md` completely.
- [ ] Read current `PORTFOLIO.md`; record its timestamp and capacity separately from native task
  liveness.
- [ ] Read this migration reference and the Portfolio pause handoff.
- [ ] Confirm all direction-local handoff commits are integrated or preserve their exact commit/path
  for Root integration. Do not cherry-pick a divergent task history wholesale.

### Per retained direction

- [ ] Confirm exact task ID, inbound WORK, material cycle, native model/effort and writer worktree.
- [ ] Read current direction handoff, `DIRECTION.md`, current-cycle evidence and state snapshot.
- [ ] Inventory every leaf, provider operation, process, CM task and Git writer; mark each terminal,
  never launched, or retained nonterminal.
- [ ] Verify prompt/response files with `scripts/hmasd_file_fingerprint.py --require-utf8` when an
  exact archive matters.
- [ ] Keep sent operation reentry observe-only and bound to the exact operation, conversation and
  causal user message.
- [ ] Keep quarantined or mismatched content out of synthesis.

### Portfolio resume

- [ ] Obtain explicit user/Root `RESUME`; PAUSE cannot be inferred lifted from a repair or idle task.
- [ ] Resume SCDMP and VQFP only through their retained operations; resume ONLGR only through local
  archive review; never reopen DEARS R02.
- [ ] Consume terminal DEARS and any newly terminal results; make independent actions from valid
  science.
- [ ] Recompute actual advancing WORK. Refill only after Portfolio authority is updated and PAUSE is
  lifted.

## 9. Failure modes to reject during migration

- Treating an idle/terminal task as `PARKED`, or a running task as an `ACTIVE` lifecycle row.
- Treating `Outcome: DONE` as positive science, implementation success or permission to continue.
- Treating `SENT_WAITING`, zero-send, mismatch, archive failure or model visibility as a scientific
  null or lifecycle reason.
- Treating an EM recommendation as a performed Portfolio action.
- Treating a milestone snapshot, `RESEARCH_MAP` row or old `DIRECTION.md` paragraph as the whole
  current state.
- Releasing capacity because a WORK is `WAITING`, paused, blocked by transport or technically
  failed.
- Reopening a terminal material cycle instead of issuing a fresh Portfolio WORK.
- Resending a prompt into an already committed conversation or inventing a second operation after
  unknown commitment.
- Importing an old prompt, response, archived task, browser tab, fixture, result file or candidate
  implementation as current authority.
- Bypassing EM scientific ownership in CM, or bypassing the exact fast-forward writer chain.
- Ranking valuable directions only by engineering cost, or swallowing scientific value because a
  current substrate/observer is missing.
- Fusing directions because they share Browser Transport, CM infrastructure or one implementation
  primitive rather than because their estimands and decision objects are scientifically the same.

## 10. Minimal handoff message for a new operator

A valid migration handoff should state, in one place:

1. shared-main authority commit and protocol revision;
2. Portfolio table timestamp and capacity;
3. controlling `PAUSE`/`RESUME` state;
4. each retained direction's task ID, WORK/cycle, milestone, scientific status, writer HEAD and exact
   handoff path;
5. every nonterminal Effect with operation/conversation/reentry, and every terminal/no-Effect fact;
6. accepted claim ceiling and unresolved objection;
7. direction-local commits still requiring Root integration;
8. explicit prohibitions against duplicate send, successor creation, lifecycle inference and
   capacity refill.

If any of those facts cannot be established, retain the exact WORK as `WAITING` and request the
missing authority. Do not repair the scientific record by inference.
