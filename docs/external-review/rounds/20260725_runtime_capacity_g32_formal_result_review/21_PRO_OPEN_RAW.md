## 1. `REGISTERED_RESULT_CONFORMANCE`

**Registered branch confirmed without modification:**

```text
USABLE_RUNTIME_CAPACITY_G32
```

The formal package is operationally valid: training, evaluation and analysis completed successfully; all three replicates had finite updates and nonzero actor/parameter drift; evaluation used zero optimizer steps; and the registered branch was reproduced directly from the frozen predicate inputs.

The conclusion-bearing values are:

| Registered quantity                 |                       Formal result |
| ----------------------------------- | ----------------------------------: |
| Capacity-8 utility CI95             | `[0.9502525, 0.9552011, 0.9590951]` |
| Capacity-6 utility CI95             | `[0.9375735, 0.9435536, 0.9480192]` |
| Capacity-12 utility CI95            | `[0.9483213, 0.9498142, 0.9512819]` |
| Held-out final-minus-zero gain CI95 | `[0.3658130, 0.5371965, 0.6471880]` |
| Minimum held-out replicate mean     |                         `0.9428362` |
| Held-out stochastic mean            |                         `0.8759143` |

All registered access, gain and stability gates therefore pass with material margin.

The implementation matches the registered capacity claim:

* training occurs only with `member_capacity=8`;
* final state dictionaries are strict-loaded into newly constructed capacity-6, capacity-8 and capacity-12 policy instances;
* `member_capacity` controls runtime shape validation, loop length and hidden-state packing, but is absent from learned state-dict keys and tensor shapes;
* the actor and critics use active-set aggregates, `log1p(active_count)` and fixed-width critic state rather than a raw padded mask;
* no checkpoint adapter, key remapping or tensor slicing is used.

The exact padding control is also valid. Capacity 8 and capacity 12 execute the same `4→3→6→5` active-lifecycle process, with capacity 12 adding four permanently inactive rows. Common-active observations, values, deterministic actions, rewards, hidden states and lifecycle transitions match exactly, while the added rows remain exactly inactive.

The first-match selector is correctly ordered:

```text
operational invalidity
→ padding/capacity failure
→ train-capacity access failure
→ held-out capacity/count-churn failure
→ instability
→ USABLE_RUNTIME_CAPACITY_G32
```

No later interpretation may relabel that branch.

---

## 2. `SCIENTIFIC_DISPOSITION`

```text
scientific_disposition=
SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_CONTINUOUS_ROSTER_G32
```

### Exact incremental claim beyond G31

G31 established that, under one preallocated runtime width, a continuous recurrent policy can handle within-episode temporary leave, rejoin, fresh join and terminal leave while retaining the paired immediate/delayed toy capabilities.

G32 adds the following supported proposition:

> In the registered 48-step continuous-service toy family, one G31-style checkpoint trained only with runtime packing capacity 8 can be strict-loaded without adaptation into policy instances configured for capacities 6, 8 and 12, retain registered utility and stability under their within-episode roster processes, and remain exactly invariant to additional permanently inactive padding rows.

The capacity-12 held-out profile is not merely padding: it reaches the active-count process `6→3→10→7`, while capacity 6 uses `4→2→6→3`.

### Is this already a usable runtime-variable-membership algorithm test version?

**Yes, with an explicit pre-trajectory capacity boundary.**

G31 and G32 together support a usable **continuous dynamic-roster algorithm test version** when:

1. a finite runtime packing capacity is selected before an episode or trajectory;
2. all active lifecycle events remain within that configured bound;
3. the deployment capacity belongs to the registered capacity-6/8/12 family;
4. the task remains within the registered continuous-service source family.

It would be too narrow to describe G32 as only a state-dictionary compatibility fact. Utility, held-out gain, stochastic stability, mapping and lifecycle gates also pass after the same capacity-8 checkpoint is loaded at capacities 6 and 12. Conversely, it would be too broad to call the result unbounded or fully live runtime-capacity invariance.

The exact distinction is:

```text
supported:
checkpoint and learned-parameter invariance across separately configured
finite runtime capacities 6, 8 and 12, combined with within-episode roster change

not supported:
changing the packing capacity itself while one trajectory is already in flight
```

### Smallest retained units

Retain:

1. **Capacity-generic learned parameterization.** Maximum packing capacity need not appear in learned actor or critic parameter shapes.
2. **Runtime-metadata lemma.** `member_capacity` may remain nonserialized packing metadata without making the checkpoint capacity-specific.
3. **Active-only representation.** Active-set summation, raw `log1p(active_count)` and active-fraction prefixes remain viable in the registered continuous family.
4. **Lifecycle-owned recurrence.** Temporary absence freezes state, rejoin restores it, fresh join starts at zero and terminal leave deletes state.
5. **G31 credit mechanism.** The detached realized future tail and direction-balanced actor update remain retained; G32 does not replace or independently re-establish their causal necessity.

### Smallest retired alternatives

Retire, within the registered capacity-6/8/12 toy family, the exact alternatives that:

* usable continuous roster control requires maximum capacity to enter learned critic or actor tensor shapes;
* capacity-specific retraining, a checkpoint adapter, key remapping or tensor slicing is required when moving the same checkpoint from capacity 8 to 6 or 12;
* adding permanently inactive padding rows necessarily changes common-active policy behavior.

G32 does **not** establish an independent performance improvement over G31. Its contribution is structural capacity unbinding while retaining usability, not a G32-minus-G31 efficacy gain.

---

## 3. `COUNTEREXAMPLES_AND_EXCLUSIONS`

### Strongest remaining scientific counterexample

The strongest scientific counterexample is **distributional capacity dependence beyond the registered family**, not tensor resizing itself.

The G32 source was intentionally constructed so that:

* each member owns independent RNG streams;
* adding inactive padding cannot shift active-member source values;
* no input is divided by configured maximum capacity;
* the cap8/cap12 padding pair has identical active members;
* registered membership events occur at fixed steps 12, 24 and 36.

A broader source could still break the policy if changing operational capacity also changes:

* the distribution of real active capabilities;
* event frequency or horizon;
* demand scale;
* active count beyond the tested range;
* the relationship between count and allocation difficulty.

The policy uses an unnormalized active-member sum and raw `log1p(active_count)`. G32 demonstrates successful transport through active count 10, not an equivalence theorem for arbitrary count or arbitrary process law. That is scientific uncertainty outside the retained claim.

### Strong alternate explanation: direct current-demand mapping

The toy exposes current load and target mix directly to every active actor row, and the registered mapping diagnostic explicitly checks whether mean actions track those quantities. The formal correlations exceed `0.9898`, with MAEs below `0.0166`.

Therefore, G32 does not show that recurrence or delayed credit is uniquely necessary for capacity transport. A largely reactive current-observation mapping can explain much of the task behavior. This does not undermine the registered capacity-unbinding claim; it limits representation and credit attribution.

### Live tensor-width rebinding: engineering coverage, not current scientific uncertainty

The current code fixes `self.member_capacity` on model construction. `forward_step` requires tensors whose second dimension exactly equals that capacity, and collection allocates hidden, action, replay and trajectory tensors at that fixed width. Capacity transport is performed by constructing another policy instance and strict-loading the same state dict.

Thus live in-trajectory width rebinding is not implemented or formally tested.

Under the retained G32 claim, this is primarily a **state-migration and packing implementation gap**. If common lifecycle rows, hidden states and RNG ownership are copied exactly, no new learned mapping or causal mechanism is introduced. It becomes a scientific question only under a new, broader claim that deployment must operate without any capacity bound selected before the trajectory.

Accordingly:

* do not spend a conclusion-bearing iteration merely to prove a tensor-container resize;
* do not claim live rebinding;
* do not treat the missing code path as a counterexample to `USABLE_RUNTIME_CAPACITY_G32`.

### Explicit exclusions

G32 does not establish:

* arbitrary capacities or active counts;
* arbitrary membership processes or stochastic horizons;
* live width change during an active trajectory;
* UAV physics, communication, charging or failure transport;
* source-identifiable UAV access;
* asynchronous skill lifetime;
* environment-agnostic intrinsic-reward benefit;
* comparative superiority over another complete algorithm;
* causal necessity of G31’s credit mechanism;
* stateful lifecycle necessity over a simpler reactive controller.

The two prior UAV sources remain `SOURCE_NOT_IDENTIFIABLE`; G32 cannot retroactively convert either into algorithm evidence.

---

## 4. `CDC_PORTFOLIO_LEDGER_EDITS`

Only the following scientific entries should change. No EHC, skill-lifetime, intrinsic-reward or closed-result wording changes.

### 4.1 Replace the complete `C-CONTINUOUS-ROSTER` block in `CONJECTURES.md`

```markdown
## C-CONTINUOUS-ROSTER — Continuous control under dynamic membership

- Status: supported and retained as a usable configured-capacity continuous
  dynamic-roster algorithm test version for the registered 48-step capacity
  6/8/12 toy family. A finite runtime packing capacity is selected before each
  trajectory.
- Claim: a G31 realized-future-tail and direction-balanced recurrent policy whose
  learned parameter shapes exclude maximum capacity can use one
  capacity-8-trained checkpoint at configured capacities 6, 8 and 12 while
  retaining within-episode temporary leave, rejoin, fresh join and terminal
  leave.
- Formal immediate/delayed evidence: G31 passes the paired G17/G18 utility,
  spike-allocation, rotation, gain and fresh-seed stability gates.
- Formal configured-capacity evidence: G32 strict-loads the same final
  capacity-8 checkpoints at capacities 6, 8 and 12 with zero evaluation
  optimizer steps. Utility LCBs are 0.95025, 0.93757 and 0.94832; held-out gain
  LCB is 0.36581, the minimum held-out replicate is 0.94284 and held-out
  stochastic mean is 0.87591.
- Exact padding lemma: under the registered cap8/cap12 common-active process,
  observations, values, deterministic actions, rewards, hidden state and
  lifecycle transitions are exactly equal and added inactive rows remain zero.
- Retired alternative: within the registered family, usable deployment at a new
  configured capacity does not require capacity-shaped learned parameters,
  retraining, checkpoint adapters, tensor slicing or key remapping.
- Scope: configured packing capacity remains fixed within each trajectory and
  belongs to the registered 6/8/12 family. Runtime metadata may change between
  environment instances without changing the learned state dictionary.
- Strongest scientific counterexample: a capacity change that also changes the
  distribution of real active members, process law, horizon or allocation
  difficulty outside the registered family may still break the policy.
- Code-only boundary: live in-trajectory tensor-width rebinding is unimplemented,
  but under the current claim it is a packing/state-migration coverage gap rather
  than an unresolved learning mechanism. It becomes scientific only if a future
  scope requires no pre-trajectory capacity bound.
- UAV boundary: temporary-service-loss G1 and charge-rotation G2 remain source
  non-identifiable. They neither confirm nor reject G31/G32 transport.
- Exclusions: arbitrary capacity, arbitrary process laws, UAV usability,
  asynchronous skill lifetime, intrinsic-reward advantage, comparative
  superiority and causal necessity of the inherited credit mechanism remain
  unsupported.
```

This replaces the present pending wording at `C-CONTINUOUS-ROSTER`; no other conjecture status changes.

### 4.2 Replace the `C-CONTINUOUS-ROSTER` row in `IDEA_PORTFOLIO.md`

```markdown
| C-CONTINUOUS-ROSTER | supported retained: usable configured-capacity continuous-roster test version | Formal G31 passes the paired immediate/delayed toy contract. Formal G32 adds one-checkpoint strict-loadable capacity-6/8/12 transport, positive held-out gain, exact common-active padding invariance and zero evaluation optimizer steps. The supported claim fixes packing capacity before each trajectory. | The next scientific action is the source-identifiable UAV burst design assertion audit. Arbitrary capacities and process laws remain open. Live in-trajectory width rebinding is code coverage under the current claim and becomes scientific only if future scope removes the pre-trajectory capacity bound. |
```

Replace the terminal fields with:

```text
completed_action=RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32_FORMAL_ITERATION_24
source_family=RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32
formal_disposition=USABLE_RUNTIME_CAPACITY_G32
scientific_disposition=SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_CONTINUOUS_ROSTER_G32
next_action=UAV_LOCALIZED_DEMAND_BURST_G33_DESIGN_ASSERTION_AUDIT
authorization_status=active_twenty_iteration_toy_first_uav_promotion_chain
conclusion_bearing_iterations_consumed=24
iterations_remaining=13
```

The present row and terminal block are still pending this disposition.

### 4.3 Update `RESEARCH_DIRECTION_LEDGER.md`

Add this row under **已支持并保留的方向**:

```markdown
| 连续动态 roster 的跨配置容量复用 | `SUPPORTED_RETAINED` | G31/G32 在已登记 48-step continuous-service toy family 中形成可用测试版：同一 capacity-8 训练 checkpoint 可无适配 strict-load 到配置容量 6/8/12，并保留 episode 内 leave/rejoin/fresh-join/terminal-leave；cap8/cap12 公共 active 过程精确 padding-invariant。容量须在 trajectory 前选定。 | 不能推出 trajectory 中 live tensor-width rebinding、任意容量/过程律/UAV transport、技能生命周期、内在奖励增益、比较优势或 G31 credit 的独立必要性。 | [G32 正式结果](EVIDENCE_NOTES/20260725_RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32_FORMAL_RESULT.md)；[第 24 轮报告](../../report/ITERATION_24.md) |
```

Delete the entire now-resolved subsection:

```markdown
## 正式结果已出、科研裁决待定
```

including its G32 pending row.

Replace the current UAV-transport open row with:

```markdown
| G31/G32 向可识别 UAV source 的 transport | `OPEN_UNTESTED` | 在物理可行、目标行为 load-bearing 且 source-identifiable 的 UAV source 上，已支持的 continuous-roster representation 与 realized-future-tail credit 是否保持可用。 | UAV temporary-loss G1 与 charge-rotation G2 均在 learned training 前因 source 不可识别关闭；尚无可判别的 UAV transport 结果。 |
```

Delete the current separate row:

```markdown
| 单条 trajectory 内的 runtime tensor-capacity rebinding | `OPEN_UNTESTED` | ... |
```

because it is not an active scientific direction under the adopted claim. It may remain in a code-coverage note, but this scientific ledger has no implementation-only state.

Replace longitudinal summary item 5 with:

```markdown
5. G32 正式支持同一 capacity-8 训练 checkpoint 在配置容量 6/8/12 间
   strict-load 复用，并与 G31 合并形成已登记 toy family 中可用的 continuous
   dynamic-roster 测试版。trajectory 内 live width rebinding 属于当前主张之外
   的代码 packing/state-migration 覆盖，不升级为科研方向；下一科研边界是
   先冻结一个可识别的 UAV localized-demand-burst source。
```

The pending, open-rebinding and UAV rows currently appear separately and should not remain inconsistent after adoption.

---

## 5. `ONE_NEXT_ACTION`

```text
UAV_LOCALIZED_DEMAND_BURST_G33_DESIGN_ASSERTION_AUDIT
```

### Why this action

The continuous-roster toy slice is now sufficiently usable for its registered purpose:

* G31 closes the paired immediate/delayed credit contract;
* G32 closes configured-capacity parameter and behavior transport through 6/8/12;
* live width rebinding would mostly test code-side state migration.

The decision-relevant uncertainty is now **transport into UAV physics under an identifiable source**. Both earlier membership-oriented UAV sources stopped before learned training because their positive controls failed source-identification requirements. Another heavy run without a corrected source would repeat benchmark failure rather than test the algorithm.

A localized temporary demand burst is selected for the design audit because:

1. it directly tests continuous spatial reallocation and delayed consequences;
2. it can retain the existing physical fleet and reward;
3. its current demand can be exposed without revealing a desired UAV assignment;
4. it does not require conflating charging or failure masks with service membership;
5. it can establish ordinary UAV access before a later dynamic-roster composition.

This source would not itself establish dynamic membership. That limitation is intentional: a source-identifiable UAV access result is a prerequisite to a meaningful membership-composition claim.

### Preserved unscheduled directions

The following remain legal but unscheduled:

* a new genuinely identifiable UAV service-membership source;
* transport beyond capacities 6/8/12;
* arbitrary process-law or horizon stress;
* a future no-predeclared-capacity claim;
* asynchronous skill lifetime after the current stage;
* comparative advantage under a separate authorization.

### Reactivation condition for live rebinding

Live tensor-width rebinding becomes a scientific action only if the protected claim is expanded to:

> deployment must admit a packing-capacity increase or decrease during an active trajectory without a predeclared bound.

Absent that scope expansion, it remains implementation-only.

---

## 6. `EXECUTABLE_SCIENTIFIC_BOUNDARY`

The next action is a **focused `DESIGN_ASSERTION_AUDIT`**, not a conclusion-bearing experiment.

### Exact audit question

> Under unchanged Scenario-7 S7-S1 physical dynamics and external reward, can one localized temporary per-user QoS-demand-burst source be frozen such that:
>
> 1. future burst onset, duration, spatial center and magnitude are hidden;
> 2. current per-user demand is actor-visible without revealing a UAV assignment;
> 3. a future-blind constructive controller achieves absolute burst and recovery access;
> 4. a ledger-blind no-reallocation controller is materially worse;
> 5. every optimal policy must perform post-onset spatial service reallocation rather than solve the source by a fixed layout, calendar prepositioning or a supplied role;
> 6. G31/G32 and an information-matched ordinary recurrent baseline can later receive identical observations, actions, reward, interactions and optimizer exposure;
> 7. every gate has a positive and negative witness before implementation.

### Source boundary to preserve

```text
base_physics=S7-S1_unchanged
physical_fleet=8
service_roster=constant_8_for_this_source
external_reward=existing_scenario7_task_reward
future_burst_ledger_visibility=forbidden
current_demand_visibility=required
desired_uav_assignment_visibility=forbidden
intrinsic_reward_change=forbidden
learned_training_in_this_action=none
```

The constant roster is deliberate. This audit tests whether the supported continuous policy and credit mechanism can reach a real UAV source. It cannot produce a dynamic-membership claim.

### Required source controls

The audit must define and freeze:

1. **Future-blind constructive control**
   May use current UAV/user/channel state and current demand only. It must not read future onset, duration, center, magnitude or user trajectory.

2. **Ledger-blind no-reallocation control**
   Preserves the pre-burst service layout or action target after burst onset.

3. **Physical reachability oracle**
   May read the complete burst ledger, but is feasibility-only and never a learned comparator.

4. **Matched ordinary recurrent null**
   Later formal comparison must use identical current information, action support, recurrent capacity, interactions and optimizer exposure.

### Target-behavior necessity

The relevant optimal-policy set must be written before source freeze.

The source is invalid for this purpose if any optimal or access-level policy can avoid post-onset UAV service reallocation by:

* remaining in the pre-burst layout;
* exploiting absolute time;
* prepositioning to a fixed known region;
* reading an assignment or future burst field;
* satisfying the metric through ordinary-demand sacrifice not captured by a guardrail.

This necessity check follows the project rule that a positive control is valid only when every relevant optimal solution requires the claimed behavior.

### Result-sensitive choices the audit must freeze

The audit must return exact values—not ranges or PM defaults—for:

* burst onset, duration, magnitude and affected-user law;
* train and held-out distributions;
* current actor and critic demand fields;
* burst/recovery utility and ordinary-service guardrail;
* constructive absolute-access floor;
* constructive-minus-no-reallocation margin;
* matched baseline information and exposure;
* confidence construction and sample unit;
* first-match result order.

### Mutually exclusive audit outcomes

```text
IDENTIFIABLE_UAV_BURST_G33_DESIGN
```

All source fields are exact; physical reachability, future-blind constructive access, target-behavior necessity, load-bearing contrast, leakage boundaries and branch witnesses close. The source becomes eligible for a later code-science alignment audit. This does not authorize implementation or compute.

```text
NON_IDENTIFIABLE_UAV_BURST_G33_DESIGN
```

A relevant optimal policy avoids post-onset reallocation, the constructive controller cannot reach the absolute floor, the no-reallocation contrast is not material, or the source requires future/assignment leakage. Close this exact source design; do not train a learner.

```text
UNRESOLVED_UAV_BURST_G33_DESIGN
```

The proposed source could be identifiable, but one or more result-sensitive scientific fields cannot be uniquely frozen from the available evidence. Preserve the broader UAV-transport question and return only the missing protected choices to External Pro.

### Minimum evidence before any implementation

* explicit optimal-policy-set argument;
* one constructive positive witness;
* one no-reallocation negative witness;
* threshold and zero-denominator arithmetic;
* proof that current demand does not encode the desired assignment;
* proof that future burst fields are absent;
* exact train/held-out support;
* complete first-match truth table.

File layout, tensor packing, telemetry format, vectorization and test organization are implementation-only after scientific freeze.

This disposition does not authorize code, Git, nonformal/formal compute, monitoring or a successor child.

---

## 7. `中文简报`

G32 的正式结果应当接受为：

```text
SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_CONTINUOUS_ROSTER_G32
```

它比 G31 多证明了一件重要事情：

> 只在 capacity 8 上训练得到的同一个 checkpoint，可以不重训、不做评估期优化、也不使用 checkpoint adapter，直接 strict-load 到 capacity 6、8、12 的 policy 实例中，并继续处理 episode 内的离开、重入、新加入和终止离开。

所以，G31 + G32 已经构成一个**可用的 continuous dynamic-roster toy 算法测试版**。但必须加上精确限制：

* 每条 trajectory 开始前仍需选定一个有限 packing capacity；
* 正式证据只覆盖 capacity 6/8/12；
* 不支持运行到一半把 tensor width 从 6 改成 12；
* 不支持任意 N、任意过程、UAV、技能寿命、内在奖励或比较优势。

所谓 live tensor-width rebinding，目前更像是 hidden-state 搬运和 tensor packing 的代码覆盖问题，而不是新的学习机制。它不应仅因为 PM 发现了代码缺口，就自动消耗下一次科研迭代。

下一项科研动作选择：

```text
UAV_LOCALIZED_DEMAND_BURST_G33_DESIGN_ASSERTION_AUDIT
```

原因是两项既有 UAV source 都在训练前因 source 不可识别而关闭。现在最有价值的不是再做一次重型训练，而是先冻结一个真正可达、必须在线重新分配覆盖、又不泄漏未来 burst 或目标 UAV assignment 的局部需求突增源。

这个 audit 只决定 benchmark 是否可判别，不训练算法，也不能证明 dynamic membership。只有 source 的物理可达性、无未来信息的 constructive access、no-reallocation 差距和“所有有效最优解都必须重分配”同时成立，才有资格进入后续实现边界。

本回复只作科学裁决，不授权实现或计算。
