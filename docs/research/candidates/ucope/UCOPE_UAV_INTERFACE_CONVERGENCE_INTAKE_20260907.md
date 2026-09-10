# UCOPE UAV interface Convergence intake — 2026-09-07

## 1. Decision and authority

**PRO_FINAL: accept option (a), opening one narrow fixed-roster UAV movement/observation/control B/EXPLORE family.** The selected first question compares one optional opening velocity commitment with a same-information recurrent PPO controller that can act every primitive step. This is a direction decision, not an observed UAV benefit, implementation acceptance or experiment allocation.

The complete [response](pro_packets/20260907_uav_interface_convergence/archive/RESPONSE.md) is read from immutable commit `426513b18b38b477dd255b3e8524424d8deb8a19`, all 254 lines / 37,900 bytes. Its first paragraph is the verdict; sections III–VI select the prospective design and VIII preserves the P14 execution boundary. The current command is [P14-UCOPE-UAV-INTERFACE-CONVERGENCE-01](../../portfolio/handoffs/2026-09-07-p14-vsp02-code-and-direction-continuations.md#p14-ucope-uav-interface-convergence-01).

Rule applied verbatim, AGENTS §2: “A complete archived Pro response that decides the posed question at its declared evidence class and within current owner instructions and applicable specifications is final for its node.” The response passes the conformity reading below; no specification exception or corrected scientific question is needed. The latest main AGENTS addition inspected at `14a0a4097d20326d41918d04a1721d07b3178217` concerns rolling dispatch, not changed scientific burdens. The fixed evidence remains at its original SHA.

## 2. Delivery reconciliation and checked receipts

The accepted request is `2026-09-07-ucope-uav-interface-convergence-01`, node `em:ucope:convergence`; fixed TASK `26122fd36eede5928be021ee650813b2f5df7998`, input `41ea97afb572971b7768b9ffe6402f708f00f104`, bound HANDOFF `bd3bd9e221d443f9a20891d461de3c366d1d54ed`.

- Direct GitHub reads confirmed delivery commit `426513b18b38b477dd255b3e8524424d8deb8a19`, its parent `bd3bd9e221d443f9a20891d461de3c366d1d54ed`, and exactly one added path: the authorized `archive/RESPONSE.md`. API bytes equal the immutable Git blob, SHA-256 `0f6fc82e735013f49b8a17d79a0407f421325a8d0b670d4de69704704451e6fa`. The local CRLF checkout normalizes to the same blob; it was not rewritten.
- [Issue 11 delivery comment](https://github.com/CartmanFatass/My-paper-code/issues/11#issuecomment-5576651687) links that response, this TASK and the fixed evidence. Commit time is 23:23:28Z; comment time is 23:24:03Z. The [comment snapshot](pro_packets/20260907_uav_interface_convergence/archive/DELIVERY_COMMENT_SNAPSHOT.json) and [fresh reconciliation](pro_packets/20260907_uav_interface_convergence/archive/DELIVERY_RECONCILIATION.json) retain the actual reads.
- Root's [670-byte chat receipt](pro_packets/20260907_uav_interface_convergence/archive/CHAT_RECEIPT.md), captured at 23:35Z, reports unavailable write actions, no attempted write, a response 404 at the earlier branch HEAD and an empty Issue. It is preserved unchanged, SHA-256 `8ee73cfdec7fcb3e3d5235288a25cd69a744ba3dc441a11e3b659aabcf8132e4`. Those delivery statements conflict with the independently readable file/comment; they do not annul their content.
- The copied [Transport facts](pro_packets/20260907_uav_interface_convergence/archive/TRANSPORT_FACTS.json) are Root's historical observation: bound conversation `6a9c6b1c-1c34-83e8-8ebc-dee64b334240`, `6 Pro` / `Latest` / `Pro, 5 of 5.`, one Send, natural completion, tab closed. DM did not observe the provider UI or establish why the receipt contradicts delivery. Root retains that transport reconciliation; no replacement response, comment, Send or app receipt was issued here.

The applicable delivery rule is “Matching response/comment already exists | Read and reuse it without rewriting the response or repeating its scientific decision” ([GitHub collaboration, partial success](../../../project/GITHUB_RESEARCH_COLLABORATION.md#partial-success-and-uncertainty)). The actual full response, rather than the short contradictory chat status, supplies the scientific decision.

## 3. Selected question and source boundaries

The prospective host is base `MultiUAVEnv`: five UAVs, 50 users, 1000 m area, height 50–150 m, velocity components scaled by 30, one-second steps, uniform layout, free-space channel, no shadowing/FDMA, vectorized backend, original local observation limits and default reward. A new common horizon of 256 primitive steps is selected explicitly; it is not the original 5000-step task. Fixed membership means no roster, replacement or lifetime claim.

At t=0 each treatment actor chooses velocity and duration 1 or 4. During a hold, real environment steps, free local observations, recurrent state and reward continue; the actor resumes ordinary feedback at expiry. No subsequent options are opened. The generic comparator retains every legal velocity action, all the same free local information and recurrence, and may itself repeat a velocity or exploit movement-induced observations. This is a fair opportunity boundary, not a proven neural function-class inclusion or observed competence.

Actors receive their own complete local observation, own action history and own remaining commitment. The common training critic may receive the stated global position/time and already selected commitments; global infos are retained without leaking into actors. This is an explicit new decentralized-execution comparison, not a claim to reuse or outperform an uninspected full-state baseline.

The source chain is velocity → physical position/channel/connection → each UAV's legal local observation → recurrent state and later owned velocity decision → actual primitive reward → learner credit and team service. The base `step` and adapter `step` were inspected without imports. Base rewards sum to the team reward; the adapter scalar averages them again. The selected primary therefore uses `sum(info['rewards_dict'].values())`, whose field is present in the adapter. This affects the estimand and must reach the eventual CM spec.

“Paid” denotes actual service opportunity consequences of movement and delay. There is no established independent sensor fee, six-mark count channel, positive movement charge or flight-power cost. Geometry can directly improve service, even without an information benefit. Duration activation, changed observations and predictive information alone establish no effect. The prospective binding MARL structure is partial observability in a jointly moving fixed team; B05 remains systems / information flow without actual MARL exposure.

## 4. Conformity, primary and interpretation

Response III–VI chooses real FP32 recurrent PPO, common encoder/GRU and velocity head, one extra treatment duration head, common centralized critic, matched common initialization streams, on-policy trajectories, full-episode undiscounted return targets and true-decision log probabilities. Held commands are not counted as fresh actor samples; all primitive observations and critic samples remain. Exact architecture and optimization settings stay in the immutable response, rather than being rewritten by this intake.

Primary: the difference between treatment and generic in episode time-average team native reward, averaged first over 32 paired final evaluation episodes and then over two independent training pairs. Final checkpoints only; no outcome-selected checkpoints or extra seeds. The two pair endpoints, their sample SD and conditional episode-level Monte Carlo uncertainty have distinct meanings; agents and steps are not independent training units.

New absolute MEI is 0.01 on the selected default reward scale, with response V's one-percentage-point rationale. Above it supports only preliminary comparative package performance; weak generic competence or an absent information path narrows the dependent interpretation. Inside ±0.01 shows no gain at that scale under this budget. Below −0.01 limits the particular task/prefix/learner budget. Every opposite-sign pair survives. None establishes stable superiority, pure information value, unique architecture, transfer or deployment.

The same-evaluation zero-velocity hover reference records generic competence without becoming a tuned baseline or a prelaunch success gate. There is no headroom record on this UAV task. A nonpositive generic-versus-hover comparison does not erase T−G or establish policy-class incapacity. Missing information diagnostics limit information attribution while an independently trustworthy native primary remains reportable.

This matches evidence-spec §§4, 5.2, 11.4, 11.7–11.9: direct learning and sampled returns, two independent training pairs, no exact maximum, support census, search-before-learning, all-positive-seed or C-class prerequisite. Checks concern actual changed timing, information access, reward scale and primary output. The response selects no extra result-bearing validation call. No new engineering machinery was added; this documentation intake needs no ENGINEERING_SCOPE_SPEC §4 item and breaches no §5 code budget. It is not a new CM coding assignment; a future assignment retains Root's required five-arm capture before coding.

## 5. Computed work and exposure

Python configuration arithmetic is recorded in [PROSPECTIVE_WORK_FACTORS.json](pro_packets/20260907_uav_interface_convergence/archive/PROSPECTIVE_WORK_FACTORS.json), without source imports or environment calls:

| Prospective quantity | Count |
| --- | ---: |
| Training | 2 arms × 2 training pairs × 131,072 = 524,288 team primitive steps |
| Episodes / rollouts per fit | 512 / 256 |
| Optimizer steps | 4 fits × 256 rollouts × 4 epochs = 4,096 |
| Main learned-policy evaluation | 128 episodes / 32,768 team steps |
| Added fixed-hover reference | 64 episodes / 16,384 team steps |
| Complete evaluation | 192 episodes / 49,152 team steps |
| All proposed environment work | 2,240 episodes / 573,440 team steps |
| Nested candidate/trajectory/solver search | none |

The reference work is additional, not free. Per-head decisions differ under holding and must be reported. Wall/CPU coefficients, full invocation caps and compatible runtime remain unknown; B05's caps do not transfer. The proposed route is existing remote-first, one scientific CPU process/thread, with fresh actual-node admission for any later authorized invocation. Cost refusal requires reconsidering question/scale, not automatic cap growth or a new cost pilot.

**New actual exposure: zero training datasets, environment steps, learner updates, evaluation episodes and result-bearing invocations.** B05's prior machine-generated exposure is reused unchanged: 262,144 train episodes, 393,216 scalar updates, 131,072 histogram updates, 196,608 evaluation episodes, 458,752 total episodes and 1,753,088 host events. Prior complete wall is 4.67/4.84 s, sum 9.51 s; 389 s is the wider collection/integration window, not summed invocation wall. Historical missing aggregate CPU/scratch and zero-exposure shell failure remain separate.

## 6. Scientific reading and predictions

Strongest support is B05's fresh joint RM-A, mean 0.002620157877604169, and the source-defined UAV movement/observation/service path. Strongest contradiction is B04's harmful extra purchase and adverse first endpoint, with B01's two zero-gain endpoints and older false probes/unchanged competence. B02/B03 positives remain separate. These motivate a new question; they do not validate its new controller or host.

The surviving simplest explanation is that generic control already uses all useful free information and movement. Any treatment gain could also reflect geometry, temporal smoothing or optimization exposure; this two-arm performance comparison does not isolate them. Reuse of verified local-library evidence in [the prior proposal §5](UCOPE_POST_B01_RETURN_MODEL_QUESTION_PROPOSAL_20260907.md#5-question-driven-source-check) keeps downstream native benefit and actual cost primary. VIL2C/DACOM do not supply this UAV interface, performance, novelty or pure-information attribution. No new corpus coverage or retrieval claim is made.

No new prediction reply exists: **not taken (unattended)**. B05's existing score remains four of six predictions matched; joint RM-B and extra acquisition missed. This Pro decision does not rescore B05 or create another training result.

## 7. Decisions this intake produces

1. **Object / technical:** (a) reuse the complete matching GitHub response and preserve the contradictory receipt; (b) treat the short receipt as continued delivery failure; (c) resend or recreate delivery. Recommendation and execution: (a). **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Direct delivery and full-response checks support it; the cause of the chat mismatch remains a Root transport fact to reconcile.
2. **Direction / selection:** (a) open the narrow movement-mediated B family selected in the response; (b) withhold that family for a missing native paid-sensor input. Recommendation and executed choice: **(a), PRO_FINAL**. A real movement/control package can be studied without inventing the stronger sensor-fee interface. No RECAST verdict was returned and no new recast count is added. The old retained-policy/root-residual numerical-locus family remains paused; lifecycle, priority and capacity are Portfolio's unchanged surfaces.
3. **Object / boundary:** (a) record the accepted question and return the precise remaining task; (b) implement or launch from delivery alone. Recommendation and execution: (a). **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** P14 releases no post-decision implementation or scientific invocation. No UAV science card is frozen here and this is not formal UAV-validation entry.

The direction decision is surfaced as [P2 item 20260907-ucope-008](../../portfolio/owner/inbox/2026-09-07/20260907-ucope-008.json), with its Chinese decision packet and applied PRO_FINAL / OWNER_DELEGATED trace; ordinary technical facts stay in this intake/audit. Owner reviews were empty at intake, with no relevant unapplied ledger override. The [Chinese brief](../../portfolio/owner/briefs/ucope/2026-09-07_uav-interface-convergence.md) carries the bounded meaning. Owner flags: contradictory delivery receipt, unmeasured UAV cost/competence/headroom, and inseparable information/geometry/temporal/optimization explanations; no material critic dissent or second recast.

## 8. Next discriminator and return boundary

The selected discriminator is the two-pair final native-return comparison in response III–VI, with competent-null interpretation recorded inside that B. The next **Portfolio assignment recommendation** is bounded preparation of its one complete science card and CM code spec: bind actual compatible source/runtime, write prospective fresh seed identities and the complete invocation budget, preserve response timing/information/reward/learner semantics, and supply original acceptance checks. Before any CM coding, return that same committed source/spec/check set to Root for the owner's five-arm capture. This recommendation allocates no work itself and asks Root for no scientific choice.

Root integrates the immutable response and this intake, retains the contradictory Transport archive, and routes the exhausted P14 return under the rolling-dispatch rule. No experiment is running or transferred. DIRECTION records the accepted family and its next discriminator; historical evidence and the accepted TASK/HANDOFF remain unchanged.
