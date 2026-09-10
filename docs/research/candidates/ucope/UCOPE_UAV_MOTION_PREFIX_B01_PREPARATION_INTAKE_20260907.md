# UCOPE UAV motion prefix B01 — preparation intake, 2026-09-07

## 1. Assignment, authority and outcome

P15's [UCOPE section](../../portfolio/handoffs/2026-09-07-p15-rolling-refill-after-transport-split.md#ucope--complete-the-selected-uav-cardspec-then-comparison), main input `25b1a88b1`, assigns the actual science card and one complete code spec for the already accepted UAV B family. The complete immutable Pro response at **426513b18b38b477dd255b3e8524424d8deb8a19**, sections III–VI, is the scientific source, with [P14 intake §§3–5,8](UCOPE_UAV_INTERFACE_CONVERGENCE_INTAKE_20260907.md). Its opening of the narrow family remains PRO_FINAL. This intake supplies object details and the common new engineering assignment, without another family decision.

Delivered: [science card](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md), [complete code spec](UCOPE_UAV_MOTION_PREFIX_B01_CODE_SPEC_20260907.md), [original five-item task](UCOPE_UAV_MOTION_PREFIX_B01_CM_TASK_20260907.md), [machine-computed preparation facts](UCOPE_UAV_MOTION_PREFIX_B01_PREPARATION_FACTS_20260907.json), and the new-card owner packet/item cited below. These documents bind the next engineering question; no source was implemented, no CM started, and no UAV construction/reset/step, learner initialization, evaluation, preflight or scientific invocation occurred. **No formal UAV-validation entry is claimed.**

The designated checkout remains `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch `codex/ucope`. Required P15 inputs were merged at `521da9b267b623d7368ff1ed46807ff413dc095b`, pushed immediately; its tree matched the P15 input and there were no starting local changes. The merge preserved both audit histories. This preparation preserves all source bytes, immutable Pro delivery, historical outcomes and unrelated Portfolio content. Root captures the full committed preparation descendant for comparison batch03; that descendant is returned with its full SHA after push.

Before this preparation commit or any UCOPE coding, Root reported that FSD had filled batch02 and assigned UCOPE to **batch03**. The draft dispatch-number references were updated accordingly; scientific spec, source bytes, original checks and the one-new-assignment boundary are unchanged. This is Root execution sequencing under P15, not a DM Portfolio decision or a repeated engineering task.

## 2. Rule applied and conformity checked

The operative evidence-spec §11.4 rule, applied verbatim, is: “Only the following may hold a B launch: the §4 common integrity requirements; the §5.2 requirement that the real learner runs and reports nonzero transition, update, and evaluation counts; the mandatory resource admission; and one machine-generated **exposure line** (parameter displacement budget relative to initialisation scale, or an equivalent statement that the learner can move in its budget).” Sections 11.7–11.9 set this question's description fields, claim-dependent burden and proportional verification. This is preparation for a real B, not an exact diagnostic or C freeze.

I checked the new card/spec against Pro III–VI for all five-agent, 256-step host settings, actual local observations and native reward, one t=0 d=1/d=4 commitment, generic's full legal actions/free information, recurrent PPO/critic permissions, primitive returns and real decision likelihoods, matched initialization, independent pairs, final sampled evaluation, hover reference, MEI .01, negative endpoints and attribution limits. The complete selected path is preserved. No concrete conflict with current owner instructions or the controlling evidence spec was found; no corrective Pro request is needed.

Directly checked source facts and their consequences:

| Source fact | Binding implementation consequence |
| --- | --- |
| Base action is normalized three-component velocity, multiplied by 30 and stepped for one second before position clipping and channel/service update. No distinct velocity sensor is returned. | Last-action history is the normalized velocity command actually sent. Displacement remains available from successive own-position observations for diagnostics; no extra actor sensor is introduced. |
| Current local observations contain 3 own-position values, 20×3 user values, 10×4 UAV values and normalized primitive time. | Keep all 104 components; add only own last command and remaining hold for 108 actor inputs. Sorted slots remain episode-local observations, not persistent entity identity. |
| Adapter reset has `state`; step has `next_state`, per-agent reward and original infos. Base gives each UAV one fifth of its team reward, and adapter averages again. | Sum the five per-agent native values once; do not train on the adapter scalar or recompute reward from a proxy. Use pre-action state/commitments for the 136-component critic. |
| Base constructor calls reset; adapter construction does not produce a scored episode; reset/step expose fixed ordering and the required fields. | Two base constructions per pair, constructor resets counted outside scored episodes but inside whole time; explicit reset for every one of the prescribed episodes. H reuses G's environment. |
| `_local_user_entries`/`_local_uav_entries` sort already computed channel matrices and require no new trajectory. | At most two read-only index calls per selected diagnostic frame, clipped to actual observation limits, excluded from actor inputs. |

These are read-only source observations, not executed API/learner acceptance. The complete mapping appears in CODE_SPEC §§1–3. Existing UAV-related source paths were compared with the fixed Pro input `41ea97afb572971b7768b9ffe6402f708f00f104` and were byte-identical at the preparation baseline. No currentness guard is added to the runner.

## 3. Ordinary design completions and executable arithmetic

The Pro response selected scientific architecture, learning schedule and comparison; this card fixes the previously missing implementation choices before any data: common Torch default initialization copied within each pair; duration's zero logits; own commanded-velocity history; pre-decision critic features; explicit tanh-Gaussian density and pre-tanh entropy regularizer; full-episode gamma=1 reward-to-go; rollout advantage normalization; one joint ratio/clip per team time; collected chunk initial hidden states; exact Adam defaults and streams; complete caps; and the original bounded synthetic checks. These choices do not remove free information, weaken generic's legal action opportunity, require a policy-class exclusion proof, or change the selected algorithm/work budget.

The earlier informal preparation status used “actual-displacement history” while inspecting the interface; that wording was not a frozen card or data-generating instruction. Source inspection resolved it before this published card/spec to **the actual velocity command sent**, matching the base's action semantics and the Pro's own-action-history boundary. No executed or frozen comparison is being revised.

Python arithmetic in PREPARATION_FACTS records:

| Quantity | Prospective amount |
| --- | ---: |
| Independent masters / learned fits | 6801,6802 / four fits |
| Actor common / critic / G / T parameters | 32,134 / 34,177 / 66,311 / 66,441 |
| Training steps / Adam calls per fit | 131,072 / 1,024 |
| All training | 524,288 team steps, 2,048 complete episodes, 4,096 Adam calls |
| Learned-policy final evaluation | 128 episodes / 32,768 team steps |
| Added fixed-hover reference | 64 episodes / 16,384 team steps |
| All scored work | 2,240 episodes / 573,440 team steps |
| Added source-index diagnostics | 3,200 agent frames / at most 6,400 calls |
| Nested candidate/trajectory/controller search | zero |

The seed IDs had no exact match in the bounded current UCOPE scientific/code search before these files were written; this is not a universal namespace proof. Each pair's reset/initialization inputs are matched, with separate real on-policy trajectories and actor/duration RNG domains. Only the two pair masters are independent training units. The original fixture checks additionally use 9001, with 80 synthetic team steps/eight Adam calls; they add no UAV invocation or empirical training unit to this card.

New complete scientific stop limits are 1,800 s per arm-seed, 3,600 s per pair and 7,200 s summed across both prospective pairs. Startup/imports/common initialization belong to T; G includes hover and pair publication. They are bounded allocations selected for the future code path, **not measured UAV runtime forecasts and not present launch authority**. Unit environment/update/evaluation times, a suitable tuned baseline and UAV headroom remain unknown. B05's measured 9.51 s and its caps are not transferred. If actual work cannot fit, return the affected claim/budget fact and reconsider the question rather than adding a pilot, parallelism, hidden phases or cap resets.

Engineering scope §4 needs none. Code is bounded by 2,000 source lines excluding tests, runner by 600, tests by the existing five-minute directory budget plus one <=60 s synthetic CLI smoke. A 30% orchestration share is a review signal. The five-arm 3,600 s administrative limit measures this engineering assignment; it is not a scientific cap or extra experiment allocation.

## 4. Runtime and source reuse evidence

The local and remote runtime inventories were queried using only stdlib interpreter/version and `importlib.metadata` reads. Local is `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20; remote is configured `hmasd-wsl-node`, `/home/wu/.venvs/hmasd/bin/python`, Python 3.10.21. Both report NumPy 1.26.3, Gymnasium 1.0.0, PettingZoo 1.24.3 and Matplotlib 3.10.0; Torch distribution metadata is 2.7.0 locally and 2.7.0+cu118 remotely. These are concrete existing candidate runtimes, not proof that binary imports, the UAV workload or this future learner have executed successfully. No package import, installation or global upgrade was performed.

The scientific-tools adapter route was used question-first: whether an existing accepted recurrent PPO path can be reused without changing this selected architecture, action distribution, masks, finite primitive credit or update exposure. The existing VSP02 learner has explicit Torch generator/optimizer examples but a four-category policy, GAE .95 and a different minibatch update schedule; direct reuse would change selected semantics. After reading the local on-policy index, I inspected fixed upstream source at `C:/Projects/ref-lib/on-policy`, commit `de66d7a4b23fac2513f56f96f73b3f5cb96695ac`, `onpolicy/algorithms/utils/rnn.py` and `distributions.py`: GRU reset/history handling and summed Normal coordinate densities are useful references, while its LayerNorm/initialization and unsquashed action defaults do not directly implement this card. The chosen implementation therefore uses existing Torch Linear/GRU/Adam primitives and a small card-specific collector/loss, without installing or vendoring a framework. These are source facts, not baseline competence evidence.

For the mechanism comparison, [prior question-driven retrieval](UCOPE_POST_B01_RETURN_MODEL_QUESTION_PROPOSAL_20260907.md#5-question-driven-source-check) is reused: verified VIL2C source at MARL-0203 pages 4–5 and DACOM keep downstream control/native service consequences central. That verified evidence supports retaining the native primary and genuine legal generic actions. It does not supply a paid UAV sensor interface, prove this PPO is competent, establish novelty or transfer finite-host gains to UAV. No repeated literature census or new scientific burden follows.

## 5. Decisions this intake produces

### Object selection — publish the complete prospective card

Options: (a) bind the selected two-pair design with the source-supported information/history mapping, explicit RNG/optimizer details, finite complete caps and original synthetic checks; (b) return a specific unresolved design fact before issuing the engineering task. Recommendation: **(a)**. The source and accepted Pro design supply the necessary implementation semantics; unknown runtime remains an explicit cap/interpretation risk, not another prerequisite experiment. All details are fixed before UAV output.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Executed: prospective B card/spec frozen for this new engineering assignment, P2 new-card item published, no scientific invocation or UAV entry. This is reversible object-tier completion within the already opened family, not Portfolio priority/lifecycle action or a new recast. Prediction slot is **not taken (unattended)**; no result exists to score the three predictions.

### Technical acceptance — return the identical handoff to Root

Options: (a) return the complete committed card/spec/task/source and original checks for Root's immediate batch03 capture; (b) return a concrete preparation gap. Recommendation and executed choice: **(a)**. Document/source mapping, arithmetic, frozen scientific semantics and original check definitions are sufficient for the named engineering assignment. They do not accept an implementation or actual runtime.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Root performs the already-authorized five-arm capture before coding, followed by normal independent risk review/production integration. No solo CM, model override, child agent, duplicate scientific invocation or extra Pro request was dispatched. The task/spec are shared in full, not model-specific summaries. No new action is requested from Portfolio by this ordinary P15 completion.

Both decisions are recorded under [the preparation audit section](../../portfolio/audit/2026-09-07.md#ucope-uav-motion-prefix-b01-preparation--2026-09-07). The [Chinese decision packet](UCOPE_UAV_MOTION_PREFIX_B01_OWNER_PACKET_20260907.json) supplies the P2 [new-card item 20260907-ucope-009](../../portfolio/owner/inbox/2026-09-07/20260907-ucope-009.json), created and traced through `item.py` with `auto_applied=accept`; this records existing delegated execution, not an invented owner reply. Relevant unapplied owner reviews were empty at the final live-main check, **2026-09-07 18:06:37 PDT**, with no UCOPE audit owner override. No valid-result brief is due for preparation alone; the last valid-result Chinese briefs remain unchanged.

Preparation validation independently recomputed the parameter/work counts and synthetic uncertainty example, parsed both preparation/owner JSON files and the applied owner trace, checked 25 local links in the four new Markdown documents, and confirmed the seven declared existing source paths were unchanged. Git whitespace/scope checks cover the new files and audit append. No workload imports, implementation tests or fixture execution were used to obtain these document checks; original CM checks remain unexecuted until Root's matched dispatch.

## 6. Bounded reading, risks and next discriminator

Strongest motivation remains B05's two positive native paid-acquisition endpoints in its finite host. Strongest contradiction remains B04's harmful extra acquisition/native negative endpoint together with B01's nulls and the older unchanged-competence/false-probe limits. They stay unpooled and unchanged. The new card asks for sampled native performance of two learned control packages on the actual fixed UAV source; it cannot identify pure information value, unique representation or stable superiority. A local observation/action diagnostic cannot compensate for native loss, and a favorable T−G requires explicit comparator/attribution limits when G's competence or the proposed information path is unestablished.

Outstanding facts are actual binary/UAV/learner execution conformance, achievable work under the selected complete caps, meaningful generic control relative to hover, runtime/headroom, and the two independent sampled endpoints. Source inspection and fixture checks address different dependencies; neither is empirical support for the UAV mechanism. Failed setup/instrumentation/time limits will not acquire scientific negative polarity.

Next discriminator within the current command is **Root's five-arm implementation comparison using this unchanged complete card/spec/task/source**, followed by normal independent review and production integration of an accepted candidate. A later named execution command is still required for the prescribed actual UAV comparison; it must trace the selected card before any formal UAV-validation entry. This return allocates no real run and asks Root for no scientific interpretation or replacement-task selection.
