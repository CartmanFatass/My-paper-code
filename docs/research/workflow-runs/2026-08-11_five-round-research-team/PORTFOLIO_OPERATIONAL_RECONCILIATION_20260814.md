# Portfolio–Operational reconciliation and stable handoff anchor — 2026-08-14

## Active portfolio decision index

```text
current_portfolio_cut=SCDMP_TBOV_R07_STAGE_A_POST_RESULT_PORTFOLIO_ADJUDICATION_20260820.md
current_empirical_investments=RISP-B3-TRG-R03-FULL-PANEL|RCLE-CPC-R04-FULL-PANEL|SGSP-RG2Z-R03-FULL-PANEL
current_enabling_construction=NONE
current_definition_investments=SCDMP-TBOV-SUPPORT-REPRESENTATION-FACTORIAL-CHECKPOINT-DEFINITION
current_no_current_investments=ONLGR-TBH-HOST-CARD-20260815-03|VNFC-TEPR-FULL-GRAPH-REACHABILITY-AND-COST-CERTIFICATE
automatic_backfill=false
no_quota_or_wip_gate=true
```

The active **Portfolio-owner allocation delta** is the current portfolio row
set in this reconciliation. The preceding revisit definition-only delta and
every earlier
section using `current`, `sole`, or `definition-only RISP` is preserved
point-in-time evidence and is superseded for allocation. Operational Root's
separately owned pair/stage/lease facts are not rewritten by this index.

## Purpose and ownership

This is the current, human-readable reconciliation surface requested by the
user.  It joins the dedicated portfolio session's decision record with the
operational Root's direction-stage routing record.  It is not a replacement for
owner-authored science cards, CM technical packets, complete results, or the
portfolio owner's allocation records.

## Root semantic-alignment contract

Every operational row, child packet, and restart handoff separates four
layers: **observed fact** (what the owner directly saw), **local action fence**
(the exact operation/action that must not be repeated), **direction
continuation** (the still-authorized same-science work and its owner), and
**Root decision class** (ordinary continuation, workflow recovery, lease,
science revision, or portfolio decision).  A local transport, runtime, or
provider fence never changes a direction's scientific state by implication.
In particular, a provider `no-resend` applies only to its exact committed or
ambiguous operation/turn identity; it does not prohibit a distinct,
EM-authorized future turn, unchanged-science repair, CM continuation, or an
invested direction.  Only an explicit user instruction, Root lease boundary,
EM activity/science boundary, or portfolio decision can mark direction work
paused, complete, or no-current.
direct decision channel.

This is the sole stable Root↔portfolio progress anchor. Root updates its own
pair/stage/lease/reporting row in the same turn that it receives a direct
direction milestone, then sends any necessary decision-level portfolio relay.
An owner completion cannot remain labelled as pending, awaiting, or reviewing
after its Root packet has arrived.

## Root-to-portfolio durable delivery anchor

```text
ack_id=ROOT_TO_PORTFOLIO_OVERNIGHT_DECISION_APPLIED_20260814
payload_version=1
root_applied_conclusion=SGSP-240 continues; RISP-B2-R02 uses its existing pair for the authorized full frozen empirical chain; VNFC-B4 has a definition-only EM/CM pair; no other family was activated.
direct_delivery=CONFIRMED
confirmation=The target-side dedicated portfolio session explicitly read this stable anchor and acknowledged `ack_id` in `PORTFOLIO_TO_OPERATIONAL_ROOT_RECONCILIATION_READ_ACK_20260814`.
confirmation_rule=Confirmed only from target-side ack_id presence or an explicit portfolio response, never from a caller-side send return.
```

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
| RISP | Frozen retained frontier; `/root/cm_risp_r03_resume` has applied the user stop-at-safe-boundary instruction. | Exactly 403/1072 result-blind packet/commit pairs reconcile intact (zero torn pairs, zero SHA-256 mismatch); one historical slice receipt remains, with no final result, `FINAL_COMPLETE` marker, active matching production process, or partial scientific value opened. No fresh broker, slice, lease, provider, science or Portfolio action follows before later workflow adjustment/testing. | The frozen 16-seed × 5-schedule × 13-cell object and all 403 retained identities remain unchanged. The stop fence applies only to RISP production/runtime advancement; it does not invalidate data, establish a claim, consume a treatment, or reallocate the direction. A later Root follow-up after workflow adjustment/testing is required before continuation. |
| SGSP | Pair `/root/em_sgsp_rg2z_r03` + `/root/cm_sgsp_rg2z_r03` retains exact `SGSP-RG2Z-SCIENCE-20260815-03`; the current user-authority control-plane stop supersedes further use of lease `SGSP-RG2Z-R03-ROOT-CONTINUATION-20260820-04`. | The result-blind safe boundary contains 19 digest-valid COMPLETE seed packets, four disjoint exact-bound non-evaluable frontiers (`830503`, `831023`, `831707`, `832309`), and one unmaterialized registered seed (`831109`). `analysis.json` and temporary entries are absent; zero SGSP seed, wrapper or scheduler processes remain; no scientific value was inspected. | No further SGSP production, analysis, retry, lease action or successor is authorized during the control-plane repair/acceptance scope. This operational stop is not a scientific failure, portfolio pause, retirement or change to the immutable 24-seed update-512 object. Any future continuation requires a fresh explicit Root follow-up consistent with user authority. |
| VNFC | Released after exact `VNFC-TEPR-FIXED-FH-QUOTIENT-AND-COST-CERTIFICATE-Q0`; exact `VNFC-B4-SCIENCE-20260815-05` remains immutable. | Q0 is complete: its required pre-observation record, finite quotient/checker, independent certificate, reduced-domain agreement and analytic full-query bounds are retained. Portfolio makes no current investment in `VNFC-TEPR-FULL-GRAPH-REACHABILITY-AND-COST-CERTIFICATE`. | No full FIXED-FH solver, learned arm or empirical host construction; no coordinates, training, evaluation, empirical panel/lease or value claim. Reopen only on one recorded Portfolio revisit condition; Q0 is not a scientific falsification. |
| RCLE | Frozen retained frontier; `/root/cm_rcle_r04_empirical` applied the user safe-stop instruction to exact `RCLE-CPC-SCIENCE-20260815-04`. | Exactly 13/16 registered blinded atomic seed packets are complete (4109, 4217, 4337, 4441, 4561, 4673, 4787, 4903, 5021, 5147, 5261, 5381, 5503). For every retained unit, COMPLETE metadata, revision/schema/seed identity, packet digest, and checkpoint digest agree; there are zero temporary seed directories, no `analysis.json`, no matching formal-run process, and no scientific values were opened. | No further RCLE scheduling, launch, renewal, or completion may occur before later user authority. The exact object, coordinates, result root, certificate, and 13 retained units remain unchanged; this does not establish a scientific claim, invalidate the data, reallocate the direction, or preclude a future same-envelope lease continuation to all 16 units. |
| ONLGR | Released: `/root/em_opportunity_normalized_lease_gated_rebinding` + `/root/cm_opportunity_normalized_lease_gated_rebinding`; `ONLGR-TBH-HOST-CARD-20260815-03` remains immutable. | Completed target-host definition has **no current empirical investment**. Portfolio's decision rests on the narrow package-specific claim relative to 11–15 engineering weeks and 15.8–315.4 CPU-hours, not on code, provider, wall time, WIP or resource status. | No source/build/probe/coordinates/training/evaluation/compute/lease. Reopen only on one recorded portfolio revisit condition; Gemini's unobserved advisory operation remains operation-local. |
| SCDMP | Reused pair `/root/em_scdmp_r07_stagea` + `/root/cm_scdmp_r07_stagea` for `SCDMP-TBOV-SUPPORT-REPRESENTATION-FACTORIAL-CHECKPOINT-DEFINITION`, exact revision `SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260819-02`. | The immutable r07 Stage A remains consumed under `MODIFY-CHECKPOINT`. The new 2×2 support-allocation × segment-representation checkpoint object is ChatGPT-Pro CLOSED, EM-intaken and CM-statically feasible, observable and comparator-feasible with no definition ambiguity. Its complete prospective cost is 40 checkpoints, 24,000 logical AdamW steps and 224,604,160 model examples; Root has relayed the completed definition/cost packet for the separate Portfolio empirical invest/no-current decision. | Definition-only until that decision: no source, construction, coordinates, checkpoints, training, evaluation, compute lease, empirical factorial, r07 rerun, Stage B, coordinate reuse, more-step repair, threshold relaxation, seed replacement or relation assay. The exact Gemini r01 advisory operation is observe-only/no-resend and non-gating. The complete object remains available for a Portfolio decision; any later action requires a new applied envelope. |

### Portfolio decision application — 2026-08-19

```text
portfolio_packet=PORTFOLIO_TO_ROOT_SGSP_RG2Z_R03_EMPIRICAL_VNFC_POST_Q0_20260819
controlling_record=SGSP_RG2Z_R03_EMPIRICAL_VNFC_TEPR_POST_Q0_PORTFOLIO_ADJUDICATION_20260819.md
root_applied=SGSP r03 pair is active through construction/conformance, fresh coordinates, technical acceptance and a later Root lease for the exact complete panel. VNFC Q0 is complete/released; no full-graph successor, solver, host, coordinates, compute or empirical work opened.
pair_state=SGSP `/root/em_sgsp_rg2z_r03_empirical` + `/root/cm_sgsp_rg2z_r03_empirical`; VNFC Q0 pair released.
portfolio_ack=ROOT_TO_PORTFOLIO_SGSP_RG2Z_R03_VNFC_POST_Q0_APPLIED_20260819 submitted; target-side delivery visibility is being reconciled and is not required for this already received Portfolio decision to take effect.
```

### Portfolio decision application — 2026-08-20

```text
portfolio_packet=PORTFOLIO_TO_ROOT_SCDMP_TBOV_R07_POST_RESULT_DEFINITION_20260820
controlling_record=SCDMP_TBOV_R07_STAGE_A_POST_RESULT_PORTFOLIO_ADJUDICATION_20260820.md
root_applied=Released the consumed immutable r07 Stage-A empirical envelope and reused the SCDMP EM/CM pair only for the newly allocated support-by-representation factorial checkpoint definition, Pro/Gemini/EM intake, CM static feasibility and full prospective cost chain.
portfolio_ack=ROOT_TO_PORTFOLIO_SCDMP_TBOV_R07_POST_RESULT_DEFINITION_APPLIED_20260820 is visibly delivered to the dedicated Portfolio thread.
local_fence=No r07 rerun, Stage B, coordinate reuse, more-step/threshold/seed repair, architecture menu, relation assay or empirical factorial action.
direction_continuation=The fresh definition-only object may proceed independently through its authorized closure and feasibility envelope; no source or empirical activity is implied.
next_decision_event=Complete Pro-closed, EM-intaken, CM-feasible and fully costed definition packet; material object/cost change; or genuine cross-scope conflict.
```

### Root-to-portfolio decision relay — 2026-08-20

```text
packet=ROOT_TO_PORTFOLIO_SCDMP_TBOV_R07_STAGE_A_COMPLETE_20260820
conclusion=Exact SCDMP r07 Stage A is technically accepted, EM-intaken and same-conversation Pro CONCUR. Physical order opportunity qualifies, but five of ten frozen checkpoint competence gates fail, so the sole legal branch is MODIFY-CHECKPOINT and the relation assay is nonidentifying.
requested_portfolio_action=Adjudicate no-current investment versus a distinct checkpoint-only definition discriminator, with a concrete rationale and revisit condition. Stage B, coordinate reuse, threshold relaxation, seed replacement and budget search remain unauthorized.
delivery_state=DELIVERED_VISIBLE_TARGET: the exact packet marker is visible in the dedicated Portfolio thread. This records queue visibility only, not portfolio processing or agreement.
```

### Root-to-portfolio decision relay — 2026-08-20

```text
packet=ROOT_TO_PORTFOLIO_SCDMP_TBOV_SRF_R02_DEFINITION_COMPLETE_20260820
conclusion=Exact SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260819-02 is Pro CLOSED, EM-intaken and CM-statically feasible, observable and comparator-feasible with no definition ambiguity. Its prospective ten-seed support-allocation × segment-representation checkpoint factorial requires 40 checkpoints, 24,000 logical AdamW steps and 224,604,160 model examples; no construction or scientific activity occurred.
requested_portfolio_action=Adjudicate current empirical investment versus no current investment with a scientific-value, identifiability and opportunity-cost rationale plus revisit condition. Do not authorize r07 rerun, Stage B, coordinate reuse, threshold/seed/budget repair, relation assay or factorial activity without a new applied envelope.
delivery_state=SUBMISSION_UNCERTAIN: the local direct-thread sender rejected available message argument shapes before a confirmed submission; no delivery or Portfolio decision is inferred. Reconcile the exact marker against the dedicated Portfolio thread on the next bounded handoff turn.
```

### Root-to-portfolio decision relay — 2026-08-15

```text
packet=ROOT_TO_PORTFOLIO_SCDMP_TBOV_R05_DEFINITION_COMPLETE_20260815
conclusion=SCDMP-TBOV-SCIENCE-20260815-05 completed its definition-only boundary: Pro CLOSED, EM intake and CM static feasibility/full prospective cost. The exact staged Stage A→conditional-Stage B path has no current construction or lease authority.
requested_portfolio_action=Adjudicate current investment in exact construction plus Stage A only, versus no-current investment with a concrete value/identifiability/opportunity-cost reason and revisit condition. Stage B is not authorized by this relay.
delivery_state=DELIVERED_VISIBLE_TARGET: the exact marker is visible as an active turn in the dedicated portfolio task. This records queue visibility, not an allocation decision.
```

```text
packet=ROOT_TO_PORTFOLIO:SGSP-B1-SCIENCE-20260814-06
conclusion=Exact SGSP r06 is complete, EM-intaken, and existing-Pro-converged under CAPACITY_COMPARATOR_DELETION_OR_EQUIVALENCE; no material fixed-center acquisition advantage over matched flexible EDGE was established at 240 updates.
requested_portfolio_action=Adjudicate no-current-investment/revisit handling for the present fixed-center SGSP family.
delivery_state=ACKNOWLEDGED_BY_PORTFOLIO: the combined retry packet `ROOT_TO_PORTFOLIO_COMBINED_RESULT_PACKET_20260815` is visible in the target task, whose current response explicitly confirms that these new milestones trigger independent Portfolio adjudication. The resulting decision remains pending; this does not reopen or pause the completed SGSP stage.

packet=ROOT_TO_PORTFOLIO:RISP-B2-SCIENCE-20260814-02
conclusion=Exact RISP B2 R02 is complete, EM-intaken, and same-Pro-converged as `EXACT_PACKAGE_NONIDENTIFYING_FOR_VALUE_ATTRIBUTION`; its observed contrast cannot be attributed because the containing arm fails registered qualification gates.
requested_portfolio_action=Adjudicate invest/no-current-investment for later bounded definition and feasibility of the prospective `CONTAIN-G-TRANSPLANT` checkpoint-reachability discriminator. No activity is requested or authorized.
delivery_state=ACKNOWLEDGED_BY_PORTFOLIO: the combined retry packet `ROOT_TO_PORTFOLIO_COMBINED_RESULT_PACKET_20260815` is visible in the target task, whose current response explicitly confirms that these new milestones trigger independent Portfolio adjudication. The resulting decision remains pending; this does not reopen or pause the completed RISP stage.
```

### Portfolio decision application — 2026-08-15

```text
controlling_record=SGSP_R06_RISP_B2_POST_RESULT_PORTFOLIO_ADJUDICATION_20260815.md
portfolio_to_root=SGSP r06 fixed-center family and exact RISP R02/standalone transplant diagnostic are no-current; VNFC-B4 remains the sole current definition investment.
root_applied=SGSP and RISP pairs remain released; no successor, definition/feasibility, lease, source, coordinates, second-surface or UAV work was opened. Existing VNFC EM/CM pair is reused through the unchanged definition/Pro/intake/static-feasibility plus prospective-cost milestone.
root_to_portfolio_ack=ROOT_TO_PORTFOLIO_DECISION_APPLIED_20260815
delivery_state=DELIVERED_VISIBLE_TARGET: the target portfolio task contains the exact application acknowledgment. This records delivery, not a new portfolio decision.
```

### Revisit-definition-only application — 2026-08-15

```text
controlling_record=REVISIT_DEFINITION_ONLY_PORTFOLIO_ADJUDICATION_20260815.md
portfolio_to_root=No empirical investment. Six concurrent definition-only investments are VNFC-B4, SGSP two-zone, RISP combined successor, RCLE coarse persistent commitment, ONLGR heterogeneity screen and SCDMP order-to-value.
root_applied=Reused each named existing direction EM/CM pair under its new definition envelope; no exact historical object was reopened, rerun or altered, and no source/build/test/probe/coordinate/training/evaluation/compute lease was issued.
return_boundary=Each pair independently returns only a complete Pro-closed, EM-intaken, CM-static-feasibility plus prospective-cost packet, material scientific ambiguity/change/cost, or genuine cross-scope authority conflict.
root_to_portfolio_ack=ROOT_TO_PORTFOLIO_REVISIT_DEFINITION_APPLIED_20260815
delivery_state=DELIVERED_VISIBLE_TARGET: the exact application acknowledgment is visible in the target portfolio task. This is delivery evidence, not a later empirical allocation decision.

packet=ROOT_TO_PORTFOLIO_ONLGR_TBH_DEFINITION_COMPLETE_20260815
delivery_state=DELIVERED_VISIBLE_TARGET: the complete ONLGR definition/cost packet is visible in the target portfolio task; target-host executable-card investment remains a portfolio decision.

packet=ROOT_TO_PORTFOLIO_RISP_B3_ONLGR_HOST_CARD_COMPLETE_20260815
conclusion=RISP-B3-TRG-SCIENCE-20260815-03 and ONLGR-TBH-HOST-CARD-20260815-03 each completed their definition-only stage: same-direction Pro CLOSED, EM intake and CM static feasibility/cost acceptance. Both named pairs are released, and neither direction has source, coordinate, construction, test, probe, training, evaluation, compute or lease authority.
requested_portfolio_action=Independently adjudicate empirical invest/no-current-investment for the exact RISP R03 and ONLGR HEADLAND-90 target-host cards, including their revisit conditions.
delivery_state=DELIVERED_VISIBLE_TARGET: the exact combined packet is visible in the target portfolio task. This proves target-side queue visibility only; no Portfolio adjudication is yet inferred.

controlling_record=ONLGR_TBH_POST_DEFINITION_PORTFOLIO_ADJUDICATION_20260815.md
root_to_portfolio_ack=ROOT_TO_PORTFOLIO_ONLGR_TBH_EXECUTABLE_DEFINITION_APPLIED_20260815
delivery_state=DELIVERED_VISIBLE_TARGET: the ONLGR target-host executable-card definition application is visible in the target portfolio task; no empirical authorization is implied.
```

### RISP empirical / ONLGR no-current application — 2026-08-15

```text
controlling_record=RISP_B3_ONLGR_HOST_CARD_EMPIRICAL_PORTFOLIO_ADJUDICATION_20260815.md
portfolio_to_root=RISP-B3-TRG-R03-FULL-PANEL is the sole current empirical investment. ONLGR-TBH-HOST-CARD-20260815-03 is no-current for scientific information-per-total-cost reasons, with four independent portfolio revisit conditions.
root_applied=Reused the existing RISP EM/CM pair through unchanged-science construction/conformance, fresh coordinates, a future Root lease, the complete frozen atomic panel, technical acceptance, EM intake and same-Pro convergence. Released ONLGR from empirical action; its completed host card and its operation-local Gemini observation fence remain preserved.
return_boundary=RISP returns only a complete scientific milestone, material science-object/prospective-cost change, or a genuine cross-scope resource conflict. ONLGR returns only a recorded portfolio revisit fact. No direction-count, WIP, backfill, fusion, surface or UAV action was created.
root_to_portfolio_ack=ROOT_TO_PORTFOLIO_RISP_B3_EMPIRICAL_ONLGR_NO_CURRENT_APPLIED_20260815
delivery_state=ACKNOWLEDGED_BY_PORTFOLIO: dedicated portfolio session explicitly received and accepted `ROOT_TO_PORTFOLIO_RISP_B3_EMPIRICAL_ONLGR_NO_CURRENT_APPLIED_20260815` in `PORTFOLIO_TO_ROOT_RISP_B3_APPLIED_ACK_SEEN_20260815`. This records delivery/acknowledgment only; no allocation or science decision changed.
```

### VNFC-B4 definition completion — 2026-08-15

```text
packet=ROOT_TO_PORTFOLIO_VNFC_B4_DEFINITION_COMPLETE_20260815
conclusion=VNFC-B4-SCIENCE-20260815-05 is complete at its authorized definition-only boundary: Pro CLOSED, EM-intaken and CM statically bindable. No construction or question-relevant activity occurred.
root_applied=The completed definition pair is released from this envelope. The portfolio decision requested is whether the exact finite held-out/post-event N=7 RDA discriminator merits the estimated 18-34 experienced engineering weeks and 10^3-10^5 CPU-hour exact-ceiling/certified-inference class before any construction or empirical activity.
delivery_state=DELIVERED_VISIBLE_TARGET: the exact marker is visible in the dedicated portfolio task as a new active turn. This proves target-side queue visibility only, not agreement or an allocation decision; it does not alter VNFC's completed definition stage.
```

### VNFC-B4 post-definition application — 2026-08-15

```text
controlling_record=VNFC_B4_POST_DEFINITION_PORTFOLIO_ADJUDICATION_20260815.md
portfolio_to_root=Exact VNFC-B4 r05 is complete, immutable and no-current for empirical investment. Its consumed definition line is replaced by distinct definition-only VNFC-TARGET-EXCLUSIVE-POST-CHURN-RECOVERY-DEFINITION; RISP empirical and the SGSP/RCLE/SCDMP definition lines continue independently.
root_applied=Released B4 remains unmodified. Reused the named VNFC EM/CM pair only through the new target-exclusive definition, independent same-direction Pro/Gemini, EM intake, CM static feasibility and full prospective cost. No construction, coordinates, lease or compute is issued.
return_boundary=Return only the complete target-exclusive definition/cost packet, material science/object/cost change, a concrete B4 revisit fact, or a genuine cross-scope conflict. No WIP/order/backfill/fusion/surface/UAV action is created.
root_to_portfolio_ack=ROOT_TO_PORTFOLIO_VNFC_B4_POST_DEFINITION_APPLIED_20260815
delivery_state=DELIVERED_VISIBLE_TARGET: the exact applied-acknowledgment marker is visible in the dedicated Portfolio task. This proves queue visibility only; it does not alter the completed B4 or active replacement-definition state.
```

### Final Root scheduling notification rule

### Root-to-portfolio RCLE/VNFC completed-definition relay — 2026-08-15

```text
packet=ROOT_TO_PORTFOLIO_RCLE_CPC_R04_VNFC_TEPR_R04_COMPLETE_20260815
conclusion=Two independent definition-only packets are complete. RCLE-CPC-SCIENCE-20260815-04 is Pro CLOSED, EM-intaken and statically feasible for its finite dual-corridor held-out-roster discriminator; its projected implementation cost is 4-6 focused engineer-days and a 30-45 minute one-core complete panel. VNFC-TEPR-SCIENCE-20260815-04 is Pro CLOSED, EM-intaken and statically bindable, but exact FIXED-FH comparator certification has a material 50-98 engineer-week and 1.1e5-1.01e7 CPU-hour planning range with a >1e8/non-completion tail.
requested_portfolio_action=Independently adjudicate: (1) whether RCLE r04 merits empirical construction and a complete panel; (2) whether VNFC r04 merits only a bounded construction-stage FIXED-FH quotient/replay-certificate feasibility layer, or no current investment. Neither request authorizes empirical activity, and no evidence transfers between the directions.
delivery_state=DELIVERED_VISIBLE_TARGET: the exact marker is visible in the active dedicated Portfolio turn. This records queue visibility, not the later allocation decision.
```

### RCLE empirical / VNFC Q0 application — 2026-08-15

```text
controlling_record=RCLE_CPC_R04_EMPIRICAL_VNFC_TEPR_Q0_PORTFOLIO_ADJUDICATION_20260815.md
portfolio_to_root=RCLE-CPC-R04-FULL-PANEL is a current empirical investment. VNFC-TEPR-FIXED-FH-QUOTIENT-AND-COST-CERTIFICATE-Q0 is a current enabling-construction investment only; it authorizes no empirical VNFC work.
root_applied=The RCLE pair is reused through exact r04 construction/conformance, fresh coordinates, later Root lease and complete atomic panel. The VNFC pair is reused only to freeze Q0's mandated stage-local artifact and perform deterministic quotient/checker/certificate work. RISP, SCDMP Stage A, SGSP definition and ONLGR no-current are unchanged.
root_to_portfolio_ack=ROOT_TO_PORTFOLIO_RCLE_CPC_R04_VNFC_TEPR_Q0_APPLIED_20260815
delivery_state=DELIVERED_VISIBLE_TARGET: the exact applied marker is visible in the active dedicated Portfolio turn; visibility does not add another allocation decision.
```

### Root-to-portfolio SGSP definition / VNFC Q0 completion relay — 2026-08-19

```text
packet=ROOT_TO_PORTFOLIO_SGSP_RG2Z_R03_VNFC_TEPR_Q0_COMPLETE_20260819
conclusion=Two independent current-stage milestones are complete. SGSP-RG2Z-SCIENCE-20260815-03 is Pro CLOSED, EM-intaken and CM-statically feasible for the frozen 24-seed, update-512 variable-N choose/delete panel. VNFC Q0 completed its predeclared exact quotient/checker/cost-certificate stage but does not establish full-graph compression or any empirical value.
key_observation=SGSP projected complete cost is 35-100 CPU core-hours (or optional 6-18 GPU hours) with 4-7 CM workdays. VNFC Q0 verified its reduced rational domain and counterexample law, while the full-graph cost remains parametrically unresolved and potentially prohibitive.
requested_portfolio_action=Independently decide whether to invest in SGSP r03 construction plus its complete panel, and whether to invest in a subsequent VNFC full-graph reachability/certificate stage or hold no-current investment. VNFC Q0 does not authorize solver or empirical work.
delivery_state=DELIVERED_VISIBLE_TARGET: the exact marker is visible in the dedicated Portfolio thread as of 2026-08-19. Delivery visibility is not Portfolio agreement and does not pause either completed milestone.
```

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

## HISTORICAL_NONOPERATIVE — Portfolio-owner clarification — 2026-08-14

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

## HISTORICAL_NONOPERATIVE — Portfolio-owner correction — active-investment semantics — 2026-08-14

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

## HISTORICAL_NONOPERATIVE — Portfolio-owner post-result decision — 2026-08-14

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

## HISTORICAL_NONOPERATIVE — Portfolio-owner RCLE-B2 result delta — 2026-08-14

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

## Superseded portfolio-owner ONLGR-B2 / SCDMP-B3 result delta — 2026-08-14

This is historical base evidence superseded for allocation by the final
overnight delta below. It is a portfolio-owner delta only and does not write Root operational
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

## HISTORICAL_NONOPERATIVE — Portfolio-owner overnight post-result allocation delta — 2026-08-14

This portfolio-only delta consumes the definition/feasibility milestone for
RISP-B2-R02 and the overnight cross-direction synthesis. It does not assert
pair, lease, provider, runtime or construction facts owned by Operational
Root. The then-controlling, now superseded synthesis was
`OVERNIGHT_POST_RESULT_PORTFOLIO_CAMPAIGN_ADJUDICATION_20260814.md`.

| Scientific object | Portfolio decision then in force | Exact portfolio-owned boundary |
| --- | --- | --- |
| `RISP-B2-SCIENCE-20260814-02` | **Current empirical investment: full frozen R02 chain is eligible.** | Same-Pro CLOSED, EM-intaken and CM statically accepted as bindable, observable and comparator-feasible. The treatment and containing control are function-equivalent on the finite domain and differ in initialization/centered-decay prior; any result remains unable to separate outcome semantics from optimization geometry without a later matched discriminator. No BEST-REACHABLE-X, sign-reversed-center follow-up, second surface or UAV action is included. |
| `VNFC-B4-NATURAL-CHURN-SCALABLE-JOINT-ALLOCATION` | **Current definition-only investment.** | Freeze treatment-blind natural prehistories with exogenous join/drop; the base allocator requires no binary KEEP/SWITCH bank. Define reward-trained `L-RDA` bids through an allocator that is reward-input-blind conditional on those bids, against an equal-information containing/matched `DIRECT-SET` learned comparator and the strongest physics/history-aware `FIXED-RDA` control, plus association and reachability ceilings. Continue through object definition, independent Pro/Gemini consultation, EM intake and CM static feasibility; return before empirical activity. B3/v8 history is rationale only and does not transfer thresholds, acceptance or results. |
| `SGSP-240` | **Current empirical investment continues.** | Sole frozen 240-update sample-efficiency successor; its existing claim ceiling and result-blind conditions remain unchanged. |
| RCLE, ONLGR-B2-rate, SCDMP-B3 and RISP BEST-REACHABLE-X | **No current investment.** | RCLE exact formulation remains closed after unresolved validity; ONLGR-B2 is absorbed to global rate; SCDMP-B3 has no automatic successor; RISP BEST-REACHABLE-X remains a lower-value diagnostic. Each retains its stated scientific revisit condition. |

The empirical/definition allocation at that superseded cut was
`SGSP-240|RISP-B2-R02` and
`VNFC-B4-NATURAL-CHURN-SCALABLE-JOINT-ALLOCATION` (definition-only). This was
not a quota, WIP cap or ordering gate. No fusion, second surface, UAV
production or automatic backfill is authorized. Operational Root owns any
subsequent pair/stage/lease columns and receives only decision-level changes.

## Historical — superseded Portfolio-owner SGSP-r06/RISP-B2 post-result allocation delta — 2026-08-15

This portfolio-only delta consumes complete SGSP revision 06 and RISP revision
02. It supersedes the overnight cut for allocation only and does not rewrite
any Root-owned pair, stage, lease, provider or operational row.

| Scientific object | Portfolio decision now in force | Exact portfolio-owned boundary |
| --- | --- | --- |
| `SGSP-B1-SCIENCE-20260814-06` | **Complete and immutable; no current SGSP investment.** | At exact 240 matched updates and held-out `N={6,16}`, the correct narrow center beats one wrong narrow center but is practically equivalent to matched wider EDGE in every registered cell. No fixed-center acquisition advantage, direction-local successor, rerun, provider turn, second surface or UAV action. Revisit only with a named UAV-linked variable-`N` mission, a competent matched EDGE failure a fixed prior could address, and outcomes that choose/delete the prior rather than show one wrong center is harmful; then freeze the stated matched controls, endpoints, fresh coordinates and mismatch conditions. |
| `RISP-B2-SCIENCE-20260814-02` | **Complete and immutable; no current investment in the exact object.** | Exact-package nonidentification: DIRECT-ANCHOR qualified but DIRECT-CONTAIN failed competence, policy-TV and mean-DeltaV gates. No value, harm, attribution, lineage, equivalence, arbitrary-`k`, variable-`N`, bridge, safety or deployment claim. |
| `CONTAIN-LEARNED-E` versus `CONTAIN-G-TRANSPLANT` | **No current investment, including no definition/feasibility stage.** | This tests frozen-policy `G` exploitability, not optimization reachability or project value. Revisit only when a named variable-`k` value successor makes exploitability necessary to choose/delete recurrence and connects to a qualified held-out/switched-`k` value experiment; direct semantic-specificity comparison requires independently competent, value-actuating matched substrates. |
| `VNFC-B4-NATURAL-CHURN-SCALABLE-JOINT-ALLOCATION` | **Sole current definition-only investment continues unchanged.** | Continue only through meaning-complete definition, existing-Pro closure, EM intake and CM static feasibility, then return with prospective total cost before construction or compute. |

Current empirical investments are `NONE`; the sole definition investment is
`VNFC-B4-NATURAL-CHURN-SCALABLE-JOINT-ALLOCATION`. The overnight cut is
superseded for allocation. `automatic_backfill=false` remains in force; no
quota, WIP, order, fusion, second-surface or UAV action is authorized.

## HISTORICAL_NONOPERATIVE — Portfolio-owner revisit definition-only authorization delta — 2026-08-15

This portfolio-owned delta supersedes the preceding allocation pointer for
portfolio routing only. It does not rewrite Root-owned pair, stage, provider or
lease rows. The controlling record is
`REVISIT_DEFINITION_ONLY_PORTFOLIO_ADJUDICATION_20260815.md`.

The current cut has zero empirical investments and six definition-only
investments: VNFC-B4 plus SGSP target-bound two-zone, RISP target-bound
combined successor, RCLE coarse persistent-commitment, ONLGR target-bound
heterogeneity-screen, and SCDMP target-bound order-to-value definitions.
The five revisit families are authorized through meaning-complete EM object,
independent same-direction Pro plus separate mutually blind Gemini consultation
for every line, EM intake,
CM static feasibility/observability/comparator review, and prospective total
cost. This authorization does not authorize source changes, construction,
tests, probes, coordinates, training, evaluation, compute, leases, empirical
activity, fusion, a cross-`N×k` parent, a second surface, UAV production,
quota, WIP, ordering or automatic backfill.

Each complete definition packet must name a physical task, protected variable
axis, one shared algorithm/parameterization across that axis, direct physical-
time task performance or robustness endpoints, the strongest matched
containing comparator, an exhaustive outcome-to-action map, maximum claim and
prospective construction/training/evaluation/wall/memory/implementation cost.
Auxiliary or structural success alone does not complete a value object.

| Definition line | Exact scientific boundary | Return condition |
| --- | --- | --- |
| SGSP target-bound two-zone | Define surveillance/relay, stable public roles and a reward-independent physical kernel, with a held-out-`N` cold-start failure hypothesis; compare against strictly containing, information/parameter/communication/work/optimizer-matched EDGE. | Meaning-complete object, Pro disposition, EM intake, CM static feasibility and prospective cost; no fixed-center rerun or budget sweep. |
| RISP target-bound combined successor | Embed `G` exploitability in a named tracking/relay external-`k` value object; compare function-equivalent containing recurrence, no-lineage control and fixed/global alternatives. | Same definition/Pro/EM/CM/cost packet; no standalone checkpoint transplant or empirical activity. |
| RCLE coarse persistent commitment | Define roster-change hidden-plan commitment fragmentation and coarse/learned-cardinality common persistent latent against a containing learned-latent controller and matched validity/score/optimizer controls. | Same packet; do not inherit four-strategy codebook, thresholds, seeds or checkpoints. |
| ONLGR target-bound heterogeneity screen | Define ex-ante observable timing/tenure strata, frozen stratum-specific responses, best pooled global-rate baseline, a strictly more flexible timing-rate head as structural containing comparator and physical value endpoints. | Screen definition/closure/CM feasibility/cost only; do not restore the old B2 algorithm. |
| SCDMP target-bound order-to-value | Define whether reversed order of the same event multiset changes transition/reward, held action and external-`k` value, with FREE-DIRECT containing comparator. | Meaning-complete Level-2 candidate, Pro/Gemini, EM intake, CM feasibility and cost; no stability probe or empirical run. |

Each line returns independently at its own complete definition milestone; no
line waits for another, and no child/provider/engineering label changes this
allocation. Existing exact objects remain immutable and are not rerun. The
requested Root action is to create or reuse the five same-direction EM/CM
pairs under these definition-only envelopes while retaining VNFC-B4. This
portfolio delta did not itself apply operational state; the Root-owned
`Revisit-definition-only application` section above records the later applied
acknowledgment.

## HISTORICAL_NONOPERATIVE — Portfolio-owner ONLGR target-host definition delta — 2026-08-15

This owner-authored delta consumes `ROOT_TO_PORTFOLIO_ONLGR_TBH_DEFINITION_COMPLETE_20260815` and the complete definition object
`ONLGR-TBH-SCREEN-DEF-20260815-03`. The packet is Pro CLOSED, EM-intaken and
CM statically bindable in principle. No source, build, probe, coordinate,
training, evaluation, compute or lease activity occurred.

| Scientific object | Portfolio decision now in force | Exact portfolio-owned boundary |
| --- | --- | --- |
| `ONLGR-TBH-TARGET-HOST-EXECUTABLE-CARD-DEFINITION` | **Current definition-only investment.** | Bind the target host, physical SHORT/LONG strata and clocks, strict finite nontrivial FLEX-CONTAIN, sample/power/inference rules, paired coordinates/counts and atomic lifecycle, with the exact total-cost model. Obtain same-direction Pro closure and EM intake; Gemini is advisory and non-gating. No empirical/build/probe/coordinate/training/evaluation/compute/lease action is authorized by this delta. |

The scientific reason for stopping at definition is identifiability and the
currently high or unbounded total cost relative to the narrow
package-specific claim, not an engineering stop and not a prerequisite that
observed heterogeneity already exist. The prospective screen may be returned
for a separate empirical decision after the executable card is complete; a
positive result would remain package-specific and would not imply a general
timing-rate, arbitrary-`k`/`N`, lease/rebind, hazard, transfer or UAV claim.
The opposite-sign branch remains explicit: a package-specific fixed two-rate
benefit, or failure of the strict FLEX containment/held-out qualifications,
does not silently become a general adaptive mechanism. No WIP, ordering,
backfill, fusion, second-surface or UAV-production action is introduced.

## Portfolio-owner RISP-B3 / ONLGR host-card empirical decision delta — 2026-08-15

This owner-authored delta consumes the independent complete packets
`RISP-B3-TRG-SCIENCE-20260815-03` and `ONLGR-TBH-HOST-CARD-20260815-03`.
Neither packet transfers evidence, thresholds, coordinates, acceptance or
claims to the other. The operational Root action requested below was not yet
applied when this delta was written; Root-owned pair, stage, provider and
lease facts remain unchanged until its acknowledgment.

| Scientific object | Portfolio decision now in force | Exact portfolio-owned boundary |
| --- | --- | --- |
| `RISP-B3-TRG-R03-FULL-PANEL` | **Current empirical investment; authorize the complete exact panel without a repeat portfolio gate.** | Reuse the same RISP EM/CM pair for the Pro-closed, EM-intaken, statically feasible TRI-SECTOR-DELAYED-ACK-TRACK-RELAY package. Run only the frozen 512-update two-agent panel with equal-function-class anchor/containing recurrence, recipient-lineage control and held-out/switched external-`k` value. No standalone transplant, rerun, sign-reversed center, second surface or UAV action. The maximum claim remains exact finite package evidence; no arbitrary-`k`/`N`, convergence, transfer, safety or deployment claim. |
| `ONLGR-TBH-HOST-CARD-20260815-03` | **No current empirical investment.** | Do not build, bind coordinates, train, evaluate or issue a lease for the HEADLAND-90 screen. The card is complete and immutable. The 11–15 engineer-week, 15.8–315.4 CPU-hour, 16-GiB-RAM cost envelope is large relative to its narrow package-specific two-rate claim and to the cheaper direct RISP external-`k` discriminator. This is an explicit scientific opportunity-cost decision, not an engineering, provider or resource stop. |

ONLGR may be reconsidered if **any one** of these conditions becomes true:

1. independent evidence establishes material, reproducible pre-action
   package-rate heterogeneity or pooled-rate failure;
2. an invested variable-`k` component explicitly needs this screen;
3. a new Pro-closed object separates tenure from geometry or makes a distinct
   FLEX claim-bearing; or
4. a same-semantics reusable host reduces incremental engineering by at least
   half without changing the science.

Any ONLGR revisit must reuse the immutable host card, obtain ordinary
same-direction Pro/EM/CM confirmation if the object changes, and return for a
new portfolio decision before empirical activity. None of these conditions is
an automatic trigger. The current cut has no quota, backfill, WIP or ordering
gate, and introduces no fusion, cross-`N×k` parent, second surface or UAV
production. Other definition lines continue independently.

## Portfolio-owner VNFC-B4 post-definition allocation delta — 2026-08-15

This owner-authored delta consumes the complete
`VNFC-B4-SCIENCE-20260815-05` definition packet. The exact B4 object remains
complete and immutable; this delta does not rewrite Root-owned operational
pair, stage, provider or lease rows. The controlling record is
`VNFC_B4_POST_DEFINITION_PORTFOLIO_ADJUDICATION_20260815.md`.

| Scientific object | Portfolio decision now in force | Exact portfolio-owned boundary |
| --- | --- | --- |
| `VNFC-B4-SCIENCE-20260815-05` | **Complete definition; no current empirical investment.** | The direct variable-`N` object has a narrow panel-specific claim and a compound unresolved risk. Prospective cost is 18–34 experienced engineer-weeks and approximately 10^3–10^5 CPU-hours, from the compact Root relay only; no standalone CM cost breakdown is asserted and this is not a hard stop. |
| `VNFC-TARGET-EXCLUSIVE-POST-CHURN-RECOVERY-DEFINITION` | **Current definition-only investment.** | Root may reuse or create the VNFC pair through target-bound EM definition, independent same-direction Pro/Gemini consultation, EM intake, CM static feasibility and full prospective cost only. No source, build, tests, probes, coordinates, training, evaluation, lease or compute activity is authorized. |

The current RISP empirical investment is unaffected. The other current
definition investments remain distinct: SGSP target-bound two-zone, RCLE
coarse persistent commitment and SCDMP target-bound order-to-value. There is
no WIP, ordering, direction-count, backfill, fusion, second-surface or UAV
gate. A valid target-exclusive B4 definition must specify one executing UAV per
zone, physical natural churn with training `N<=5` and held-out `N=7`, `L-RDA`,
a strictly containing learned `DIRECT-SET`, a strong fixed comparator, the
`L-RDA-PERMUTE` association control and one recovery utility, with an exact
outcome-to-action map. If that object cannot be made scientifically coherent,
Root must return the concrete science reason rather than an engineering label.

Any one of these conditions may reopen empirical B4 allocation, subject to a
new portfolio decision: (1) a material, order-of-magnitude reduction in the
unchanged-panel cost with a direction-owned decomposition; (2) target evidence
that makes the global grammar materially decision-relevant; (3) the exclusive
object cannot be made meaning-complete while broad VNFC is critical; or (4) no
viable lower-cost direct variable-`N` object exists and B4 is the highest-
information remaining route. These are revisit conditions, not automatic
activity triggers.

## Portfolio-owner SCDMP-TBOV-r05 Stage-A empirical decision delta — 2026-08-15

This owner-authored delta consumes the exact complete
`SCDMP-TBOV-SCIENCE-20260815-05` definition packet. The object is same-conversation
ChatGPT-Pro CLOSED, EM-intaken and CM statically feasible, with no science-definition
ambiguity; no source, construction, coordinates, training, evaluation, lease or
compute has occurred. The controlling cut is
`SCDMP_TBOV_R05_STAGE_A_EMPIRICAL_PORTFOLIO_ADJUDICATION_20260815.md`. This delta
does not rewrite Root-owned pair, stage or lease rows; Root updates those columns
after applied acknowledgment.

**Current empirical investment: construction plus complete atomic Stage A only.**
Stage A is the frozen identical-checkpoint correct-versus-reversed assay that may
select `ORDER-TR`, modify to `ORDER-Q`, remove the named treatment, or remain
nonidentified/indeterminate. Stage B is unauthorized. Only `SELECT-ORDER-TR` or
`MODIFY-TO-ORDER-Q` can make a separate Stage-B decision eligible; all other
branches prohibit Stage B locally. The current RISP empirical investment and the
three definition investments `VNFC-TARGET-EXCLUSIVE-POST-CHURN-RECOVERY-DEFINITION`,
`SGSP-TARGET-BOUND-TWO-ZONE-DEFINITION`, and
`RCLE-COARSE-PERSISTENT-COMMITMENT-DEFINITION` are unchanged.

The complete selecting path has prospective lower-bound workload of 36,000 logical
AdamW steps, 34,535,720,960 model-example evaluations, at least 263,649,280
deterministic physics transitions, 25,816,320 oracle held-action word rollouts,
and 23,040 final-value episodes; Stage A alone is comparatively bounded, while
more than 99% of learned-model work is Stage B. Full Stage A→Stage B planning is
approximately 100–420 elapsed host hours (4–18 days), with 4–8 engineering days
plus 1–3 days of technical review/unchanged-science repair. This is an opportunity
cost, not a wall-time or attempt stop.

No partial result, wall/attempt stop, WIP/order/backfill/fusion/cross-`N×k` parent,
second-surface, UAV, safety or real-flight action is introduced. No Stage-B
construction or lease follows Stage A automatically; a legal Stage-A selector
branch must first make a separate Stage-B portfolio decision eligible.

## Portfolio-owner RCLE-CPC / VNFC-TEPR allocation delta — 2026-08-15

This owner-authored delta consumes the two complete definition packets
`RCLE-CPC-SCIENCE-20260815-04` and `VNFC-TEPR-SCIENCE-20260815-04`
independently. Neither packet transfers evidence, thresholds, coordinates,
acceptance or claims to the other. The controlling record is
`RCLE_CPC_R04_EMPIRICAL_VNFC_TEPR_Q0_PORTFOLIO_ADJUDICATION_20260815.md`.

| Scientific object | Portfolio decision now in force | Exact portfolio-owned boundary |
| --- | --- | --- |
| `RCLE-CPC-R04-FULL-PANEL` | **Current empirical investment: construction plus complete panel.** | Reuse the RCLE pair for the exact finite dual-corridor held-out-roster discriminator. First complete unchanged-science construction/static acceptance, then obtain a Root lease and run the complete panel. Prospective cost is 4–6 focused engineering days and 3,727,360 episodes; the point runtime forecast is 15–30 one-core wall minutes and 30–45 minutes is only the prudent lease envelope, under 2 GiB. Maximum claim is exact finite-task package value/robustness only; no arbitrary `N`, transfer, UAV, safety or deployment claim. Strongest alternative is active-subspace/representation-search geometry plus centralized clue aggregation rather than unique binary cardinality. |
| `VNFC-TEPR-FIXED-FH-QUOTIENT-AND-COST-CERTIFICATE-Q0` | **Current enabling construction-only investment.** | Reuse the VNFC pair only for the preactivity quotient/cost-certificate Q0 after CM freezes the stage-local completion artifact, cost record, exact reduced-horizon agreement domain, Bellman-bisimulation obligations and full-query bounds. `PASS` returns an accepted quotient and updated full-solver cost for a new Portfolio decision; `COUNTEREXAMPLE` rejects only this quotient and reports an unchanged-science refinement route; `COST_SEPARATION` reports numerical bounds and the dominant term without scientific inference; `INDETERMINATE` is permitted only after the complete predeclared evidence exists with named unresolved obligations, never from time/attempt/tool/provider exhaustion. No branch authorizes the full solver, empirical panel, coordinates, training, evaluation, empirical lease or value claim. |
| `SGSP-TARGET-BOUND-TWO-ZONE-DEFINITION` | **Current definition-only investment.** | Continue its independent meaning-complete definition, Pro closure, EM intake, CM static feasibility and cost packet. |
| `ONLGR-TBH-HOST-CARD-20260815-03` | **No current investment.** | Preserve the immutable target-host card and its independent revisit conditions; no source, build, probe, coordinates, training, evaluation, lease or compute. |

VNFC Q0 is a preactivity feasibility stage, not an empirical result. Its
stage-local specification and cost record must be frozen before any Q0 source
observation. The Root relay reports a 50–98 engineer-week and
1.1e5–1.01e7 CPU-hour total-path planning range with a >1e8/non-completion
tail; it is not independently source-audited and is not Q0 stage cost. The full
solver and empirical panel remain unauthorized pending a later portfolio
decision.
RCLE's complete panel is not authorized until the unchanged object is
technically accepted and Root issues its direction-scoped lease. Both lines
retain their own claim ceilings and strongest alternatives; no cross-direction
scientific updating occurs.

The Root-owned pair, stage, provider and lease rows are intentionally not
rewritten by this delta. Operational Root must update those rows and return an
applied acknowledgment. This portfolio delta requests no WIP, ordering,
backfill, fusion, cross-`N×k` parent, second-surface or UAV action. The prior
SCDMP Stage-A cut is superseded for allocation only; its exact object, branch
map, claim ceiling and Stage-B prohibition remain immutable historical
evidence.

## Superseded/base Portfolio-owner SGSP RG2Z r03 empirical / VNFC post-Q0 delta — 2026-08-19

This owner-authored delta consumes
`ROOT_TO_PORTFOLIO_SGSP_RG2Z_R03_VNFC_TEPR_Q0_COMPLETE_20260819` and is
controlled by
`SGSP_RG2Z_R03_EMPIRICAL_VNFC_TEPR_POST_Q0_PORTFOLIO_ADJUDICATION_20260819.md`.
It does not rewrite the Root-owned pair, stage, provider or lease rows above;
Operational Root updates those columns after applying the decision.

| Scientific object | Portfolio decision | Exact portfolio-owned boundary |
| --- | --- | --- |
| `SGSP-RG2Z-R03-FULL-PANEL` | **Current empirical investment.** | Reuse the SGSP pair for unchanged-science construction/conformance, fresh disjoint coordinates, technical acceptance, later Root lease, and the complete 24-seed update-512 panel, followed by EM intake and same-Pro result convergence. Keep training `N={9,15}`, held-out `N={6,21}`, one checkpoint, literal strict containment and all frozen gates. No second budget, search, partial interpretation, surface or UAV action. |
| `VNFC-TEPR-FIXED-FH-QUOTIENT-AND-COST-CERTIFICATE-Q0` | **Complete technical evidence; former enabling allocation consumed.** | Preserve the exact horizons-1..3 reduced-domain quotient/checker certificate and its counterexample law. It establishes no full-graph compression, solver feasibility, learned value or empirical authorization. |
| `VNFC-TEPR-FULL-GRAPH-REACHABILITY-AND-COST-CERTIFICATE` | **No current investment.** | Do not open a full-graph census, full solver, host/learned construction, coordinates, training, evaluation or lease. The missing full-horizon `K_h`, compression factor and finite next-stage cost make the proposed enabling step low decision value relative to direct current panels. Revisit only on one of the explicit analytic-factorization, finite-cost, reusable-infrastructure, target-criticality or lower-cost-route conditions in the controlling record. |

At that cut the empirical set was RISP-B3, SCDMP-TBOV Stage A, RCLE-CPC and
SGSP-RG2Z. The later SCDMP r07 delta below consumes that Stage-A line and adds
the definition-only checkpoint factorial. This was not a quota or
vacancy/backfill rule. SGSP cost estimates and VNFC raw
upper bounds are scheduling/opportunity-cost evidence only and never scientific
stops. No evidence, thresholds, coordinates, acceptance or claims transfer
between directions; no WIP/order, fusion, cross-`N×k` parent, second-surface or
UAV action is introduced.

## Portfolio-owner SCDMP r07 Stage-A post-result delta — 2026-08-20

This owner-authored delta consumes
`ROOT_TO_PORTFOLIO_SCDMP_TBOV_R07_STAGE_A_COMPLETE_20260820` and is controlled
by
`SCDMP_TBOV_R07_STAGE_A_POST_RESULT_PORTFOLIO_ADJUDICATION_20260820.md`.
It does not rewrite Root-owned pair, stage, provider or lease rows; Operational
Root updates those columns after applying the decision.

| Scientific object | Portfolio decision | Exact portfolio-owned boundary |
| --- | --- | --- |
| `SCDMP-TBOV-SCIENCE-20260815-07` Stage A | **Complete, immutable and consumed under `MODIFY-CHECKPOINT`.** | All physical opportunity and target/action qualifications passed, but five of ten per-seed untouched fit-support ratios exceeded `0.65`; no order treatment was selected. Do not rerun, add steps, relax thresholds, replace seeds, reuse coordinates or interpret downstream descriptive assay values. Stage B is ineligible and unauthorized. |
| `SCDMP-TBOV-SUPPORT-REPRESENTATION-FACTORIAL-CHECKPOINT-DEFINITION` | **Current definition-only investment.** | Reuse the SCDMP pair only to freeze one fresh 2×2 current/support-stratified equal-row allocation × current/one-improved-segment-representation object, retaining 600 steps, optimizer, ten fresh seeds, the `0.65` competence rule and untouched evaluation. Complete existing-Pro closure, separate Gemini intake, EM intake, CM static feasibility and full cost. No source, construction, tests, probes, coordinates, checkpoints, training, evaluation or lease. |
| Any r07 Stage B | **Ineligible and unauthorized.** | A later factorial can at most identify a checkpoint-package competence effect. A new independent relation assay must still select one treatment before a further Portfolio decision can consider Stage B. |

The current empirical set is RISP-B3, RCLE-CPC and SGSP-RG2Z. SCDMP is the
sole definition-only line; enabling construction remains empty. ONLGR and VNFC
no-current decisions are unchanged. This allocation reflects the target's
qualified physical order opportunity and the successor's ability to separate
support, representation-package, interaction and continued nonidentification;
it is not a direction-count or vacancy-backfill action. No evidence transfer,
WIP/order gate, fusion, cross-`N×k` parent, second surface or UAV action is
introduced.
