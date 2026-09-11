Claim under consideration: conditioning the weighting of visible user geometry on visible other-UAV geometry may improve finite-training native team return over an equally informed, parameter-matched recurrent DENSE actor.
Binding MARL structure: (d) other-agent non-stationarity or partial observability; another UAV's motion changes both local radio observations and the joint service consequence of this UAV's velocity.

# MGTAP conditional-pooling source/design return — 2026-09-10

**Return form: one precise question for the original Convergence node, with the proposed operation specified below. Source/design readiness: yes. Executable readiness: no.** This is the single conditional-fallback document return, not a frozen B card, a family-opening decision or a Pro delivery packet. Implementation and numerical allowance are zero, and the assignment ends at publication of this return.

## 1. Assignment, authority and inspected boundary

Root activated MGTAP once after FSD completed its I1280/D0 source/design return without an allocated continuation and while the same vacancy remained free. The authority is the [fifth-vacancy execution mapping](../../portfolio/pro_packets/20260910_fifth_vacancy_selection/EXECUTION_MAPPING.md), the [conforming Portfolio intake](../../portfolio/decisions/2026-09-10-fifth-vacancy-selection.md), and the complete Portfolio response at immutable commit `f4fce9a4fd9603db66463ad8c81bb9464533e260`. The controlling allowance says:

> One document return; zero implementation and zero numerical invocation.

The [FSD design](../flexible_skill_duration/FSD_UAV_RENEWAL_BATCH_B01_DESIGN_CARD_20260910.md) and [intake](../flexible_skill_duration/FSD_UAV_RENEWAL_BATCH_B01_DESIGN_INTAKE_20260910.md) provide the primary's completed return. Its individual-renewal batching proposal is distinct from this actor operation; its proposed future work supplies no authority here. Root's dispatch establishes the vacancy fact. This DM does not make a Portfolio replacement decision or independently count sibling work.

The existing checkout `C:/Projects/HMASD-worktrees/dm-n5-continue-20260904`, branch `codex/mgtap`, began clean at `cec19bac98eb7eeebaeb841b71869f61734c9113`. Reconciliation merge `0ba2c3537d7d35852585f818f218010f8dfd9312` incorporates the exact assigned main `af7c0c360645d0c3aaf638e731767f2b1cac3bd9` and was pushed immediately. Current control-plane and shared UCOPE source conflicts use those assigned main bytes. Every old audit row was already present on main and was preserved. Four historical native-geometry Convergence packet files remain additional direction-branch provenance; they are not new requests. The merge retains the branch's historical commits. No algorithm source differs from assigned main because of this task.

Read the current Portfolio MGTAP row, DIRECTION's P75/post-B01 sections, B01 card, P75 intake, original post-B01 Convergence response §§5–8 and its intake, applicable AGENTS, evidence-spec §§3–5.2, 11.4, 11.7–11.10, and Engineering Scope §§4–5, 7.1. The native geometry actor family and the older balanced-allocation-coordinate family both remain PARKed. The broad direction remains ACTIVE/MEDIUM; this return changes no lifecycle, priority, recast, C status or formal UAV-entry record.

## 2. The precise original-family-node question

For a **subsequent actual assignment** to `em:metric_ground_transport_allocation:convergence`:

> Does the single UAV-conditioned user-pooling operation COND defined in §3, with the event-to-velocity/credit prediction in §4, justify reopening only the native ground-geometry actor family for one prospective COND/DENSE B comparison at the exposure in §6, or should that family remain PARKed? DENSE retains every raw local input and its recurrent history, all trainable parameter blocks are matched, and the native task and PPO credit are unchanged. Please decide between this concrete package question and retaining the present family boundary, preserving P75's adverse result and all cost unknowns. No baseline qualification, count census, positive pilot, exact policy upper, causal diagnosis or feature search is proposed as a prerequisite.

**Direction-local recommendation:** this now meets the previous decision's requested design yield and is worth considering as one small, separately allocated B. The differentiator is context-dependent relative weighting of user rows when other-UAV geometry changes, rather than a sum rename or merely appending a count. This is a recommendation to the original node, not a local family disposition. A node could reasonably retain PARK because the new interaction is untested and the prior related package lost. No TASK/REQUEST/HANDOFF, Issue, Send or subsequent assignment is created here.

## 3. One actual learned operation and its comparator

Let `x` be the unchanged 108-component actor input. It contains own normalized position, twenty ranked user rows `u_j=(relative x, relative y, normalized SINR)`, ten other-UAV slots `v_k=(relative x, relative y, relative z, normalized SINR)`, primitive time and the existing own last-command/hold fields. Ground-user offsets are divided by area size; UAV vertical offsets use the height range, as in the source. No new normalization or privileged feature is introduced.

Visible-row masks are `mU_j = [u_j[2] > 0]` and `mV_k = [v_k[3] > 0]`. They use only the existing raw rows. The source selects SINR at least 3 dB and then encodes it with `clip((SINR+10)/50,0,1)`, so a selected row has a positive SINR component, including at zero relative offset. Padding has zero in that component. Define `nU=sum mU` and `nV=sum mV`. These are current SINR-eligible, truncated observations: up to twenty visible users and, with fixed five-UAV membership and self excluded, up to four actual other UAVs in ten slots. They are not global demand, served-user counts, persistent identities or partner assignments.

Retain the existing trainable blocks exactly in shape:

```text
U : 20 x 3, no bias       V : 21 x 4, no bias
P : 64 x 41, no bias      W : 64 x 108, b : 64
eU_j = tanh(U u_j)        eV_k = tanh(V v_k)

q = sum_k mV_k * eV_k[0:20] / nV       when nV > 0
q = zero vector of length 20           when nV = 0

score_j = dot(eU_j, q) / sqrt(20)
alpha = softmax(score over visible user rows only)
cU = (nU / 20) * sum_visible_j alpha_j * eU_j   when nU > 0
cU = zero vector of length 20                  when nU = 0
cV = (1 / 10) * sum_k mV_k * eV_k

encoderCOND(x) = W x + b + P concat(cU, cV)
```

Empty user input has the defined zero context; no softmax over an empty set is needed. If no other UAV is visible, `q=0` and the visible-user weights are uniform. The `nU/20` factor then recovers the old fixed-slot user pooling, rather than silently changing the empty/sparse amplitude convention. With one visible user, there is no user-ranking choice for attention to make. The operation's opportunity is multiple visible user relations together with informative other-UAV context. No census of how often that occurs is required or undertaken.

For fixed visible counts and fixed user rows, moving an observed UAV can change `q`, the relative user weights and hence the residual. That cross-type interaction is the selected change. The normalized weights are functions of the current learned row embeddings, so this definition is not the old fixed divisor replaced by a constant sum scale. This is a reading of the proposed computation, not a claim of a strictly larger policy class or an empirical effect. Mean UAV embeddings can cancel or discard useful distinctions; the full raw path remains available for them.

The encoder returns pre-activation features of shape `(...,64)`. The unchanged wrapper applies tanh, then `GRU(64,64)`, then the existing three-coordinate Gaussian mean head and learned log standard deviations. No query is added to the recurrent state, and no entity memory, communication, graph traversal, attention matrix over pairs, assignment solver or candidate-action search is introduced. The full actor is not permutation-invariant because its unchanged raw path retains every ranked component.

**DENSE is the existing intact comparison:**

```text
encoderDENSE(x) = W' x + b' + Q tanh(D x + d)
D : 16 x 108, d : 16, Q : 64 x 16, W' : 64 x 108
```

DENSE receives all 108 raw inputs in both its affine and nonlinear branch and owns the same full recurrent consumer. It can already respond to the described event and derive occupancy from its inputs. No geometry blindness, observation restriction or reduced action support is claimed for it.

The proposed COND keeps the exact existing REL parameter blocks and adds no learned parameters. The recorded B01 counts therefore supply the prospective match: branch 2,768, encoder 9,744, and complete learner 69,079 in each arm. This reuses the existing count record and source shapes; no model or numerical parameter-count check was run. All V outputs still enter `cV`, including its last component. P and Q start at zero, while row/hidden maps use the existing private initialization convention; common raw encoder, GRU, velocity head, log standard deviations and critic are copied from the same fresh template. At that initialization both policies reduce algebraically to the same base actor. The inner branch receives policy gradients through P after P moves, as in B01. Its actual movement is a future learning fact, not established here.

Equal counts control parameter number only. COND has additional masking, query, dot-product, softmax and weighted-reduction work and a different optimization geometry. DENSE remains a valid generic native comparator, not a proved optimal or tuned one. A future COND gain would not establish that attention, geometry, occupancy or parameter sharing alone caused it, nor that COND beats the old REL learners.

## 4. Native event, velocity and credit prediction

Consider a UAV that sees user groups on distinct horizontal bearings. A visible other UAV moves toward one group's bearing while another group remains SINR-eligible. The hypothesis is that conditioning user weights on the other-UAV rows can help the actor learn to shift its horizontal velocity distribution toward the less contested observed group. In the corresponding sparse case with no visible other UAV, the user branch retains uniform pooling and the raw recurrent actor can continue its ordinary reaction. This is a proposed observable situation, not a generated fixture, a measured event frequency or a hard-coded repulsion rule.

The returned UAV link SINR and relative geometry do not reveal that UAV's actual user connections, intended next action or unobserved users. A learned query is not an identified contention estimate. Favoring a different bearing may worsen link quality, enter interference elsewhere, lose existing service or duplicate another UAV's motion. Co-adapting shared actors may also choose the same alternative. Those are real ways the proposed package could lose.

The source-preserving chain is:

```text
own and partner motion / current radio geometry
 -> this UAV's ranked, truncated local rows and own recurrent history
 -> learned UAV-conditioned weighting of visible user geometry
 -> current primitive tanh-Gaussian velocity command
 -> clipped native motion and updated channel/interference/SINR
 -> capacity-limited greedy association and native team reward
 -> ordinary team-advantage PPO gradient through this velocity's density
 -> later user/UAV embeddings, weighting and velocity behavior
```

Each UAV retains its identity and own GRU state through the episode; re-ranking a row does not transfer an entity memory or claim stable user identity. Membership is fixed. There is no join, leave, replacement, termination or semi-Markov change. The actor selects a fresh three-coordinate velocity each primitive second; the source scales each component by 30 m/s and clips positions/altitude. Holding or hovering remains a legal outcome of ordinary velocity selection.

Native host: `MultiUAVEnv`, five UAVs, fifty fixed ground users drawn uniformly on reset, 1000 m square, altitude 50–150 m, 256 steps; free-space vectorized channel, no shadowing/FDMA, capacity ten users per UAV, at most one UAV per user. The greedy ordering and ties remain source-defined. Default team reward is `0.7 * connected_fraction + 0.3 * mean_connected_SINR_quality`; the learner sums the original per-agent reward entries. It does not train on the adapter's averaged scalar or a geometric/occupancy proxy. No base-station metadata or global connection array enters either actor.

The same global critic, per-agent compound velocity log density, clipped PPO ratio, gamma-one return-to-go, scalar standardized team advantage, entropy coefficient, loss weights and optimizer remain. Credit is still team PPO credit, not a new counterfactual decomposition. Through the multiplicative user/query interaction, advantageous velocity samples can train both user and UAV embeddings toward a more useful conditional weighting. DENSE can learn the same useful behavior through its generic computation. The predicted comparison is improved finite-training use of that context, not exclusive information or guaranteed correct credit.

An eventual native gain with the proposed velocity pattern unmeasured supports only the package result. A favorable attention weight or local motion pattern with a native loss does not support performance improvement. This return allocates no event diagnostics to establish either pattern.

## 5. What the inspected source establishes, and what remains unimplemented

All pointers below refer to source read at reconciliation commit `0ba2c3537d7d35852585f818f218010f8dfd9312`.

| Source consumer | Decision-relevant fact |
| --- | --- |
| `experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/geometry.py:29–100` | Exact row slices, trainable blocks, raw residual and pre-GRU insertion exist. Replacing the user pooling computation can implement the proposed operation without changing its public actor interface. COND itself does not exist in this source. |
| Same file, `build_pair` / `geometry_snapshot` / `geometry_exposure` | Fresh common/private initialization and branch exposure records exist; a later new object must bind its own COND label and retain the actual branch measurements. |
| `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py`, `make_real` / `actor_features` / `team_reward` | Exact native constructor, actor-only information and original team reward consumer are available. `local_indices` is diagnostic access and is not a proposed mask source. |
| `envs/pettingzoo/uav_env.py:382`, `:575`, `:947`, `:1421` | Positive-SINR padding convention, ranked eligible rows, greedy capacity/association and default reward are actual source semantics. |
| UCOPE `policy.py`, `Actor.forward` / `joint_terms`; `learner.py`, `collect_episode` / `recurrent_outputs` / `update` | Each UAV retains current observations and recurrence; 32-step chunks replay stored hidden starts; actual team-return PPO and four full-rollout optimizer epochs can be reused. |
| MGTAP B01 `runner.py`, `run_pair` / `_primary` / `aggregate` | The existing command is fixed to REL/DENSE, old masters 8201/8202, H and the old two-master aggregate. It cannot be presented as a runnable COND study merely by relabeling its output. |

A later implementation needs the one conditional-pooling encoder operation and a separately named two-arm, one-master binding/readout. It must preserve the old B01 command/evidence, pair initialization, native paths and final sampled primary. The ordinary focused acceptance would cover that changed operation, raw input/parameter match, its loss connection and the dependent publication path; nothing was implemented or exercised now. Core environment, common actor recurrence, reward and optimizer formulas need no proposed change. Engineering Scope §4 needs **none** for this return or the proposed ordinary actor change.

## 6. Prospective primary, MEI, independent unit and work

If subsequently selected, propose **one fresh matched training pair**, COND and DENSE, with separate per-arm learner/optimizer/history and common initialization/reset inputs under the existing private RNG-domain law. No old checkpoint is loaded or fit reused, and the exact fresh master is left to that actual allocation; this return reserves none. Use one final sampled endpoint, with no checkpoint or seed selection and no intermediate evaluation. Omit optional H from this minimal primary-only question, relinquishing a contemporaneous hover comparison. Historical H remains evidence in its own window.

Per fit, reuse the inherited design: 512 training episodes of 256 native steps, 256 two-episode rollouts, four full-rollout PPO epochs, 1,024 Adam calls, recurrent chunks of 32, then 32 sampled 256-step final episodes. Retain CPU FP32/thread1, ordinary Adam at 3e-4 and the current primitive G path. Training/evaluation reset and velocity streams stay distinct; common seed labels do not make the later trajectories identical. This is a fresh package comparison, explicitly informed by the old results.

The original Convergence §7 already records this exact primary-only scale: **two fits, 1,024 training episodes, 64 learned final evaluations, 278,528 native team steps and 2,048 Adam calls**, with no H. These are reused prospective counts, not newly calculated or executed exposure. Five simultaneous actors, native radio/association work and four optimizer replays of each rollout are dominant multiplicative factors. The same source record gives 3,317,760 logical actor-row evaluations per fit across collection, final evaluation and PPO replay; COND's query/softmax/reduction work occurs on those rows, not just during evaluation. It requires no user×UAV pair table, candidate-controller search, trajectory rollout search or solver calls.

For each full sampled episode retain the source accumulation and define:

```text
J[a,e] = (1/256) * sum_t sum_i r[a,i,t]
d[e] = J[COND,e] - J[DENSE,e]
Delta = mean_e d[e], over the complete 32-episode paired endpoint
```

Report every own-arm return and paired difference, their mean and conditional evaluation SE. The independent learning unit is **one matched training pair**, not 32 episodes, five agents, minibatches or recurrent chunks. One pair cannot estimate training-seed population variability. Do not pool P75's fits, choose favorable worlds or substitute training curves for this final endpoint.

Proposed absolute MEI: **0.01 native time-average team reward**. It retains the interpretable scale of this unchanged host: the existing Convergence record gives a full-episode extra connected user's coverage contribution as 0.014 before the SINR-quality term. That motivates a modest useful margin; it is not a reward guarantee or a repository-wide threshold. A relative margin would obscure changes in the learned baseline level. No historical MEI or result rule is rewritten.

| Complete future primary | Bounded reading and proposed recommendation |
| --- | --- |
| `Delta > +0.01` | One local COND-package benefit at this exposure; consider one separately selected independent training pair if the observation and cost warrant it. No stable superiority or attention-causality claim. |
| `-0.01 <= Delta <= +0.01` | No demonstrated package benefit above the declared scale; retain DENSE as the available generic choice and end this proposed allocation. Positive within-scale effects remain positive; this is not equivalence. |
| `Delta < -0.01` | Adverse evidence for this particular package; retain DENSE and recommend no unchanged COND continuation, preserving any favorable local observations separately. No broad geometry-family impossibility. |
| Primary incomplete or damaged | Record the dependent gap and any independently trustworthy own-arm facts; no paired polarity, automatic retry or replacement seed. |

How the result will be interpreted: an above-MEI native gain supports bounded repeatability work, an inside-MEI result leaves the replacement case unresolved, and a native loss weakens this exact alternative regardless of attention or motion appearances. Every sign and outcome survives intake. DM prospective prediction is inside-MEI, low confidence: conditional weighting supplies a real computation, but its summary may lose useful geometry and DENSE already has the information. Owner prediction is `not taken`; no prediction is scored without a result.

The inherited complete per-arm cost law is:

```text
C_a = C_init,a + 131072*c_env+actor,a + 1024*c_update,a
      + 8192*c_eval,a + C_publication,a
```

COND changes the collection/evaluation forward cost and the full PPO replay/backward cost. Masking, query formation, twenty-dimensional scores, visible-user normalization and weighted pooling are intrinsic algorithm work. No parameter-matching width search is needed because the inherited blocks are unchanged. Activation memory, full candidate wall, aggregate CPU, staging/Monitor/collection support and authoring cost remain unknown. Proposed exposure is bounded above; **no prospective machine-time allowance or runtime forecast is assigned by this document**. A later allocation must price and cap its complete commands and support without treating unknowns as zero. Shared initialization and pair publication must be charged once, with imports, admission, learning, the final evaluation and closed-file readout included in the complete invocation; added verification and Monitor/collection support remain separate from algorithm work. This does not require a new timing probe first.

Historical context remains P75's 353.71/368.12-second native pair commands and 0.81-second offline aggregate, 722.64 seconds for one two-master result, with 899.395665-second study critical path separately. The DENSE/H/publication remainder is not isolated DENSE timing. Those windows do not guarantee a COND runtime or release the old 1,800/3,600-second caps. No new support/runtime measurement, numerical arithmetic program or remote command was used here. A later portable invocation would use the current configured remote node and fresh destination admission under its own allocation.

## 7. Scientific reading, support and limits

Scientific-tools reading used FOUNDATIONS §§2–4 and 6 plus the MARL/empirical topics. The concrete assumptions are that current local observations and an RNN do not reveal a sufficient global state, shared team credit is not individual causal credit, and a representable response is not evidence that a finite learner finds it. These change the design directly: keep DENSE's raw input/history intact, retain common PPO credit, ask for native sampled package return and use one learning pair as the independent unit. They rule out inferring mechanism efficacy from attention values or treating episode variability as training variability.

The bounded literature question was whether spatial relational processing and entity attention supply a plausible computational pattern without authorizing communication, global actor state or a mechanism claim. Inst-sci's current real `llm-index/catalog.v2.jsonl` and relevant metadata identified two papers, whose local source passages were read:

- Utke, Houssineau and Montana, **Investigating Relational State Abstraction in Collaborative MARL**, AAAI 2025: `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0078.json`, pages 1–2, elements 32, 42, 45–46. MARC puts spatial relational abstraction in a critic without direct communication. This supports treating local spatial structure as a plausible bias, but its critic method and task results are not evidence for this decentralized UAV actor.
- Shao et al., **Complementary Attention for Multi-Agent Reinforcement Learning**, ICML 2023: `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0409.json`, pages 1–2, elements 104, 113, 118. The attention-distraction discussion and its added action-prediction/communication modules make clear that weighted entities alone do not guarantee cooperation. This proposal retains the raw path and an intact DENSE comparison and does not import those modules, auxiliary losses, variable-team claim or communication assumptions.

My-lib's README/collections entry and the inspected default registry contain synthetic demonstration records; those were excluded. No verified real-collection search result from that interface was used in this return. This is the actual accessed coverage, not a claim that My-lib has no real corpus or that the Inst-sci snapshot exhausts prior work. No acquisition, library rebuild, novelty claim or separate literature report was commissioned.

Strongest support is source feasibility: the row masks are available from legal input, the current actor has an exact insertion point, and a changing UAV query can change relative user emphasis with the same parameter blocks. The strongest contradictory empirical evidence is P75: REL−DENSE was −0.04468252516448091 and −0.003243683445650989, with aggregate −0.02396310430506595. Its second master was inside the MEI with 14 positive and 18 negative worlds; the first had all adverse worlds. Both branches learned. These facts are accepted prior evidence, not recomputed here, and they do not show that COND improves on either old actor.

The native tuned same-information headroom record remains absent. The scenario1 baseline set uses a different six-UAV/500-step host and E0 exposure-only records; it cannot replace this five-UAV comparison or supply a native headroom claim. Reuse the actual P75 DENSE algorithm/configuration as the future fresh comparator. Do not turn missing tuning or headroom into a prerequisite.

**Claim ceiling now:** a source-grounded operation and a decision-ready family question. There is no new empirical signal or technical acceptance of COND. A future minimal B would support only the realized one-pair package comparison, not stable performance, pure geometry/attention/credit causality, optimal transport, fleet scaling/churn, tuned competence, convergence, safety, deployment or transfer.

## 8. Decisions this return produces and stopping point

1. **Object-tier document selection.** Options: (a) return this one concrete original-family-node question; (b) return no-ready because no credible source-compatible operation can be specified. Recommend and execute (a): the actual operation, information path, intact null, native primary and unresolved costs are specified. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** This selects the form of the authorized document return, not an experiment or family re-entry. The recommendation in §2 remains direction-local advice.
2. **Technical completion.** Options: (a) commit/push this return and its audit row, then end the assignment; (b) extend into implementation, testing, a Pro Send or another screen. Execute (a) under the same standing delegation and exact allocation. No additional fallback or successor is selected.

Current main owner-review queries returned `[]` at preparation (2026-09-10T18:30:02-07:00, main `af7c0c360645d0c3aaf638e731767f2b1cac3bd9`) and again before publication (2026-09-10T18:36:44-07:00, main `9fe021460765777583c6abcc4460b666d39dc53e`); relevant owner ledger cells were empty. No instruction needed applying or marking answered. Owner flag is `none`; no critic override, close-call disposition, recast, card freeze or new direction/Portfolio decision occurred. The ordinary document decision is recorded in the [2026-09-10 audit](../../portfolio/audit/2026-09-10.md). No empirical result evidence or valid-result Chinese brief is fabricated for this source-only return.

Current exposure reuses the allocation's zero-work statement: **scientific invocations=0; model constructions=0; checkpoint loads=0; environments/datasets=0; native/synthetic/training/evaluation steps=0; optimizer calls=0; tests/fixtures=0; replay/profiling/support search=0; Pro Sends=0; parameter displacement=not applicable (no learner).** File retrieval, owner-review reading, document publication and Git reconciliation are administrative work; their effort is not claimed free. No test/execution scratch or remote worktree was created. The shared authoring checkout and historical evidence remain intact.

The concise L0 for this assignment is this one direction-document return and ordinary audit record in the existing checkout; read-only source consumers in §5; preserved native/decision semantics in §§1–4; acceptance by concrete source pointers, comparator/measurement/work definitions and explicit readiness limits; zero implementation/numerical allowance, ending now. Root receives the published commit and this exact readiness boundary. A subsequent assignment may route the §2 question to its original node. The next empirical discriminator, only if later selected and allocated, is the one fresh COND/DENSE native final-return comparison. This return performs neither step.
