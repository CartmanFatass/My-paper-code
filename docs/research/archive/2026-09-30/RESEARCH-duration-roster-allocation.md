# Completed duration/roster allocation review — 2026-09-30

Historical evidence only. This completed review does not select an experiment,
resume a paused direction or change a frozen result. Current allocation belongs
in [RESEARCH.md](../../RESEARCH.md#root-successor-designs-20260930).

Review context: RESEARCH at `855a1e6c1db0fdd493857f84cc2369286df688ef`, the
source identities and original evidence below, constitution sections 2/4/5,
and the scientific-tools, loop-dispatch and portfolio methods. Root asked the
existing independent Astra Max ResearchCritic `/root/deep_report_review` to
assess whether a substantive duration/roster question deserved a new allocation,
using the project record, all three libraries and needed primary web sources.
The reviewer retained its disclosed independent context and earlier N-axis work;
it did not inherit Root/DM conversation or owe a favorable proposal. Claude's
paused ownership and all accepted Codex operations remained outside the choice.

Conversation: native independent review only; no additional Pro consultation.
The full original answer returned at 2026-09-30 20:49 UTC follows. Repository
links have been rebased for this archive; external local-library locators remain
absolute. Root's decision and direct-check scope follow the answer.

## Answer

**Recommendation: decline a new independent duration/roster allocation now.** Retain the broader questions and demonstrated capabilities. I found no sufficiently distinct, costed continuation that improves the current allocation case without substantially repeating completed work or entering Claude’s retained scope.

I continued in a separate reviewer context, retaining my earlier N-axis and temporal-planning advice. This was not a blinded review. Root’s ownership clarification supplied an additional relevant source—the completed persistent-service study—which I checked directly.

The supported diagnosis is that the project has several different phenomena, not one established “variable-duration/roster learning bottleneck”:

| Evidence checked | Consequence for the next investment |
|---|---|
| **Joint duration learning**, source `472af353e`: final fixed/factored/AR J was **.496707/.461076/.480218**. Both variable arms exercised durations 1–10, with about 7.22× as many training events and 5× as many coordinator updates. Each arm had one independent fit. | Active additional choices did not earn their native return/cost increment at this exposure. AR’s advantage over factored remains a useful positive; neither the comparison nor its sample size establishes general duration inferiority. [Complete evidence and frozen reading](https://github.com/CartmanFatass/My-paper-code/blob/855a1e6c1db0fdd493857f84cc2369286df688ef/docs/research/candidates/joint_duration_skill_learning/NOTES.md#L1020) |
| **UCOPE B10**, source `07605eecd`: nine gate fits and 4.9152 million team ticks; paired-credit gating’s mean increment over ordinary G was **−.0000732**, with both positive and negative blocks. | Real alternative suffix credit did not rescue this short velocity-copy package. This constrains another termination-credit repair, while leaving closed-loop macro-actions distinct. [Recorded panels and investment rule](../../../../runs/ucope/paired_branch_credit_b10_reduce/summary.json) |
| **Native fleet loss**, source `33e08f440`: across two training seeds, MAPR’s failed-zone recovery was **.263659/.241849**, DIRECT’s **.248190/.237917**, against BCRH’s **.305482/.302760**. Both learned substantially from initialization. | Learning and consequential recovery choices were present; ordinary recovery competence remains the comparator. B02/B03’s later SIGSEGV failures supplied no final performance comparison and cannot be counted as adverse scientific results. [First native panel](../../candidates/variable_n_fleet_churn/evidence/b01_formal_20260905_02/evaluation_episodes.json), [second panel](../../candidates/variable_n_fleet_churn/evidence/b01_seed02_20260905_01/evaluation_episodes.json) |
| **Availability recovery**, source `b60b71e00`: two constant-dispatch learned endpoints lost to P in all 64 worlds; the constant stage/hold endpoint preserved **QoS=1 in all 64**. | A real leave/rejoin event did not make adaptive reserve deployment necessary on this panel. Without initial evaluations, the successful endpoint also does not establish that training produced its capability. [Native records](../../../../runs/uav_availability_recovery/b01_joint_reserve_a01/perworld.json) |
| **Persistent service B05**, source `b3afc6f3f`: service-aware scheduling removed **441 recorded late zero-service steps**, but S−R mean full/late QoS was **−.018925/−.021515**, and full/late J **−314.403/−214.787**. | This is the strongest constructive positive I found for commitment scheduling, alongside a complete adverse tradeoff. It already tests much of the charging continuation I initially considered. [Complete comparison](../../../../runs/uav_persistent_service/b05_service_shifts_a01/summary.json) |

The strongest candidate was **joint departure and return scheduling that accounts for service lost while teammates replenish energy**. That is a consequential coordination question: one member’s commitment changes another’s charging access and the fleet’s deployed service. But B05 already compared such scheduling with full-R, rather than a weak battery-threshold controller.

Its intervention was active: 398 of 6,400 choices changed relative to R evaluated at S’s state. The positive repair in world `52292806` is real. Conversely, `52292802` lost .283921 full QoS, and `52292804` introduced eight persistent-reserve members. I independently checked those three S/R pairs from native arrays, their manifest hashes, and equality of initial batteries, complete user trajectories and RNG streams. In S’s adverse final 300 steps of `52292804`, eight members consumed **112.327 Wh against 83.333 Wh input**, while delivering positive service. Avoiding a zero-service tail did not make that trajectory energetically adequate.

That evidence supports retaining a scheduling capability and rejecting its proposed replacement use. It does **not** identify a particular repair. The additive service forecast’s frequent ties and release errors suggest limitations, but changing its weights, adding duration labels, or fitting it would still need a distinct prediction against full-R. [Intermediate evidence](../../../../runs/uav_persistent_service/b05_service_shifts_a01/intermediate-reading.json), [native world readings](../../../../runs/uav_persistent_service/b05_service_shifts_a01/perworld.json).

The literature preserves a useful positive case without supplying that missing prediction:

- **Foundations B03, §8.2** explains why variable-length controllers and asynchronous completion can avoid synchronization delays. It also distinguishes free instantaneous event broadcast from decentralized information. This supports a real commitment problem when those constraints exist; it does not establish that the present UAV decision interface has them. The local PDF/chunks were absent here, so I read the [author’s primary PDF](https://www.fransoliehoek.net/docs/OliehoekAmato16book.pdf), using the [B03 library metadata](../../../new-libs/corpus/papers/B03/metadata.json) for identification.
- **Inst-sci MARL-0449, ACAC**, supplies positive five-seed results for clock-aware, per-agent histories when macro-observations arrive asynchronously. Its predefined macro-actions and restricted observation arrivals differ from the joint-duration experiment’s fresh low-level feedback and explicit held-commitment context. That is a promising conditional mechanism, not an established repair here. I read the primary sections in [MARL-0449.json](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0449.json); [official paper](https://proceedings.mlr.press/v267/jung25a.html).
- **My-lib, Li–Poesia–Solar-Lezama, ICML 2024**, distinguishes exploration benefits from learning-from-experience costs of added skills. Its deterministic sparse-reward setting does not establish an HMASD rate or native benefit. It reinforces the need to price extra decisions and optimization. [Primary PDF](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2024/pmlr-v235-li24be/arxiv-2406.07897.pdf).
- Ordinary scheduling is a substantive alternative even with uncertain energy: Asghar et al. formulate recharge coordination using matching, capacity and risk constraints with receding-horizon execution. Their predefined tours and discharge assumptions differ from this radio host, but uncertainty alone does not establish a learning requirement. [Primary formulation and experiment](https://arxiv.org/html/2209.06308).

July’s evidence also prevents an identity-based shortcut. The public commitment history admitted an ordinary TEAM_REC reconstruction; the subsequent learned roster-attention result had a positive utility increment but failed its frozen access requirement. The external review explicitly retained correctly masked fixed-slot recurrence as a competent comparator. Changing lifecycle labels or hiding legitimate identity from only the baseline would manufacture the proposed advantage. July’s failed UAV source screens contained **zero learned fits**, so they remain source/controller limitations, not evidence that roster learning cannot work. [Information gate](../../cdc/EVIDENCE_NOTES/20260723_ASYNC_COMMITMENT_ROSTER_G3_INFORMATION_GATE.md), [external source contract](../../../external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/21_PRO_OPEN_RAW.md).

The closed forecast and adaptation studies further constrain recycling an anticipation proposal. Better peer-motion geometry did not establish complete service benefit; ordinary random perturbation and the S2/T2 radio controllers provide stronger applicable references. In parent-adaptation B05, the inherited learned composition remained below C_S2 in mean J, while C_T2 added a conditional increment over C_S2. These are separate contracts, not scores to pool, but a new compatible proposal must inherit their capabilities and adverse cases. [Forecast outputs](../../../../runs/uav_local_peer_forecast/b01_cv_reversal_a01/summary.json), [composition outputs](../../../../runs/uav_parent_adaptation/b05_radio_composition_a01/summary.json).

The cost comparison favors declining:

- A B05-scale ordinary successor already requires **16 complete H12000 trajectories: 192,000 new native steps, zero fits, and approximately two worker-CPU hours at the measured S rate**. B05’s prospective engineering/review/readback estimate was another **5–8 hours**, not measured actual support time.
- A richer reservation or station-selection contract adds implementation, physical semantics and comparison costs. The ordinary reference must receive the same rights. Any gain supplied by those rights must be separated from a learner’s increment within them.
- A new learning comparison is additional expenditure: the existing joint-duration study consumed **300.13 summed process minutes including its failed attempt**; availability recovery consumed **5.72 process-wall hours**. Neither is a universal runtime estimate, but neither supports treating another fit as inexpensive.
- Declining adds no implementation, fit or native exposure and leaves the selected T/G2/A2 study, other current studies, and Claude’s paused ownership intact.

For the strongest candidate, B05 was already the smallest complete observation that challenged both retained classes of adverse worlds. Its outcomes distinguish useful outage repair from complete service/energy improvement. Another unchanged panel would refine recurrence; it would not by itself supply a new allocation reason. A future named deployment contract could justify direct exploration without a positive pilot or proof of headroom—for example, genuinely unavailable feedback during commitments or independently controlled incoming teammates—but those premises must be real and offered fairly to ordinary alternatives.

My checks covered the consequential configurations, summaries, native endpoint records and selected positive/adverse arrays described above. I did not re-audit every historical trajectory or optimizer. UCOPE’s full raw arrays and July’s old UAV run directories were not re-read; their preserved summaries and source records were checked. No new controller/model/native queries, fitting, publication or code edits occurred.

**Correction: retain the demonstrated capabilities; stop the proposed new allocation at this boundary.** This is a value/cost decision, not closure of variable duration, changing rosters or learning as scientific questions.

**MATERIAL_DISSENT: no.** Root requested an open allocation judgment; no conflicting new investment has been selected.

## Root decision — 2026-09-30

Adopt the recommendation. No new duration/roster, energy-reservation or charging
experiment is selected. The complete positive and adverse records remain; this
declines the proposed purchase, without closing the broader questions or taking
over Claude's paused directions. No extra Pro pass would change this scoped
allocation decision.

Root read the full answer and directly checked the persistent-service B05
complete result, original independent disposition and summary at source
`b3afc6f3fa117f005eeaeaf7f86c7796521bcaa5`. Summary SHA256 is
`4e44c6f91bd77b24da61ee8bbf964ad150edcad968860ce8232b9531af847a42`.
The consequential means, 441-step outage reduction, new eight-member reserve
tail, 398 changed choices and 7110.880326 worker CPU-seconds agree with that
record. Root did not repeat the reviewer's three-world native-array audit or
independently re-audit every other historical result. The review's disclosed
checks and source limitations remain part of the decision.

The fourth DM's next bounded work is a different source-only assessment of
learning to approximate the retained N8 complete-continuation planner. Its
actual estimand is retained native capability versus decision cost, not another
duration or fleet-loss repair. The same independent Oracle supplies detailed
idea design and criticism; the parent-adaptation DM costs the actual interface,
labels, ordinary alternatives and complete comparison. Paid labels span 16
worlds, and a possible exact-reuse ordinary implementation must be considered.
No fit, new acquisition, optimized planner or native panel is selected by this
assignment. The accepted T/G2/A2 operation stays with its existing DM.
