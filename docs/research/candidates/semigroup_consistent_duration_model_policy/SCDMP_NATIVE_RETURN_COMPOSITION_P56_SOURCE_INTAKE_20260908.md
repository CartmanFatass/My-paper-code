Question: can a penalty on value differences across an observed opening hold improve native return over the intact Monte Carlo MLP learner at the same finite budget?
Binding MARL structure: (b) temporal abstraction or termination, with five partially observed, co-adapting agents and a centralized training baseline.

# P56 source intake and unselected Convergence candidate

## 1. Assignment, evidence class and reading rule

The [P56 handoff](../../portfolio/handoffs/2026-09-08-p56-scdmp-native-return-composition-question.md)
authorizes source preparation and at most one proper-node question. This is an
A/RECON source finding, not a selected research object, frozen B card, implementation
acceptance or UAV-validation entry. Preparation ran no model, environment, simulation,
training, evaluation, replay, profiling or result-bearing invocation.

The P56 stop rule is applied verbatim:

> If the only available change repeats VSPC1 or ordinary MC targets without a
> decision-relevant distinction, yield immediately rather than manufacture a
> fifth task.

The surviving candidate changes the gradient objective: it couples errors at two
observed endpoints while retaining the complete MC loss. It is an application of
sampled Bellman-residual fitting, not a new semigroup identity. The DM recommends
one Convergence question about that bounded performance intervention. Whether it
merits a new family remains a close call; no local re-entry decision is made.

The current Portfolio row is ACTIVE/HIGH. The accepted
[D6 A02 intake, Exact re-entry condition](SCDMP_D6_A02_POPULATION_CONVERGENCE_INTAKE_20260904.md#exact-re-entry-condition)
and [DIRECTION, D6 action-choice family park](DIRECTION.md#d6-action-choice-family-park--2026-09-04)
control the old family. Evidence-spec §§4,5.1–5.2,11.4,11.7–11.9 control this
class-limited question. No upper reference, full support census, exact policy search,
causal diagnosis or preceding qualification run is proposed.

## 2. What was directly checked

The checkout started clean at e6fa8cc4bf6c0a3167e852dbff81171373ae6438 and was
fast-forwarded to accepted P56 main input 8906f6571ce61a606b3d7da19a5680d8f62a38ae.
The [machine source facts](SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_FACTS_20260908.json)
record source revisions, AST-derived symbol ranges, configuration arithmetic and
zero new exposure. Only standard-library source/JSON/SQLite reads and arithmetic
were executed. No scientific module was imported.

| Source and exact version | Relevant observations |
| --- | --- |
| UCOPE 6374063408208ba67b8cb7c69ebc0babb0f00259, `experiments/candidates/ucope/uav_motion_prefix_b01/learner.py`, `returns_to_go`12–14, `collect_episode`29–155, `update`179–212 | Full primitive rewards are stored; gamma=1 MC returns are reverse cumulative sums. Collection precedes updates. Values and actions are recorded before the next native step. Advantages are formed once, normalized over the entire rollout and detached for four epochs. |
| Same ref, `environment.py`, `actor_features`27–29, `critic_features`32–39, `team_reward`49–50, `HoldState`60–74 | Five fixed identities; an agent's sampled opening velocity can be held for four steps. Only t1–3 can have nonzero remaining hold; all release by t4. Team reward sums native agent rewards. |
| Same ref, `policy.py`, `Actor`10–21, `Critic`24–31, `joint_terms`64–81, `sample`84–94 | Full 136→128→128→1 tanh critic, separate from the recurrent actor. Compound likelihood groups each agent's velocity and opening duration. Held agents receive no action-density term, while recurrence and value loss continue. |
| VSPC1 65c89368ab0fc7402fb0e24254447629e829a12d, `native_hold_value_b01/study.py`, `Config`18–31, `run_pair`84–251; `critic.py`, `GatedCritic`14–27 | Duration-capable actors on both sides; full MLP reference; 512 training episodes/arm, 32 final sampled evaluations/arm, then 32 H episodes. The tested gate adds640 parameters; the proposed residual penalty adds none. |

The UCOPE `environment.py` file is absent at this main-derived input revision,
but present at the explicitly assigned UCOPE commit. It was read directly with
`git show`; the source-facts file retains the relevant feature/hold excerpts.
Other listed learner/policy/critic/study surfaces match their assigned source
versions. The absent file is a future integration dependency, not evidence against
the mechanism. No source repair was performed during this preparation.

Native motion changes bounded UAV positions, then channel/service consequences and
the next local observations. Each actor receives its own104 source observation values,
prior command xyz and remaining hold/4; five GRU histories advance on every primitive
step. The critic receives normalized global state116 plus five ordered prior-command/
remaining-hold blocks. It does not receive a just-chosen action/duration or actors'
GRU histories. Membership stays fixed: no join/leave/rejoin, replacement or slot-identity
claim. Observed user/UAV slots are not persistent entity identifiers.

## 3. The loss distinction, including its containing alternatives

For a complete observed episode define G_t=sum of rewards r_t through r_255, and
R_t:4=sum of r_t through r_3. Let V_t be the current critic prediction on the stored
pre-action critic input, and e_t=V_t−G_t. The following statements are algebra over
the recorded reward path; no trajectory or numerical experiment was generated.

| Proposed construction | What actually changes |
| --- | --- |
| Target R_t:4+G_4 | Equals G_t. Replacing the original target is an MC rewrite; adding it on selected rows only reweights MC. Not the candidate. |
| Target R_t:4+stopgrad(V_4) | Adds ordinary multi-step semi-gradient TD fitting. Not the candidate's gradient. |
| Squared residual (V_t−R_t:4−V_4)^2, gradients through both V endpoints | Equals (e_t−e_4)^2. Its gradient is2(e_t−e_4)(grad V_t−grad V_4); it couples errors and is not a sum of independent MC losses. This is the surviving, known residual-learning intervention. |
| Remaining-hold multiplier in critic hidden units | VSPC1's architectural gate. The candidate keeps every full-MLP parameter/input and adds no gate. |

The candidate takes one scalar pair (t,4) for each t in{1,2,3} with any nonzero
remaining hold in that episode. It never duplicates the same team-value pair for
each held agent. These are actually observed segments; other agents may take fresh
actions during them. No constant joint action, deterministic value target, independent
successor draw or Markov sufficiency of the critic input is asserted.

For the two completed episodes in a source rollout, let m be this pair count.
Use L_seg=mean of those m squared residuals, or zero when m=0. Keep the original
L_MC=mean over every512 primitive rows of(V_t−G_t)^2. The exact candidate loss is:

```text
PPO policy loss + 0.5 * (L_MC + 1.0 * L_seg) - 0.01 * mean entropy
```

The comparator uses the identical full MLP and original `0.5 * L_MC`, without
L_seg. Coefficient1 is a single untuned choice giving each mean loss unit weight;
normalizing L_seg by selected pairs makes its weight explicit despite sparse support.
It is not an exposure correction claimed to preserve the original objective.
Use gamma1 and the collected FP32 rewards; no target network, model rollout, auxiliary
head, imagined transition, forced duration or changed data/RNG budget is introduced.

The full path is actual held motion/service → observed reward and pre-action state/
commitment records → segment residual and MC anchor → critic gradients plus the
existing joint actor/critic norm clip → current actor-step scale and future collected
baselines → normalized advantages and owned compound PPO updates → subsequent sampled
local actions → complete native return. Current advantages stay detached and fixed
within the four epochs. The extra loss does not directly differentiate into actor
parameters, but common gradient clipping is an immediate actor path and must be retained.

**Why it might help:** the observed common future tail cancels in the added error
difference; coupling values on both sides of a real release boundary may be a useful
finite-budget regularizer while MC retains an absolute-return anchor. This is a
hypothesis about optimization, not new information, unique duration causality or an
exact stochastic Bellman equation.

**Strongest alternatives:** the full MLP already learns the useful relation; generic
residual regularization rather than the hold boundary explains any gain; sampled
successor noise or omitted actor history makes this coupling harmful; gradients at
nearby states cancel, or shared norm clipping changes actor learning without better
baselines. Differentiating a single sampled residual is not an unbiased gradient of
the squared *expected* Bellman residual under general stochastic transitions. No
double sampling, cloned successor population or stronger objective is claimed.
Better residual fit cannot rescue native loss. A unique hold-specific attribution
would require a different question and comparisons; it is not a prerequisite for this B.

## 4. Verified literature and what it changes

The concrete retrieval question was whether the endpoint-coupling gradient is MC
algebra, semi-gradient TD, residual learning or a duration-value gate. My-lib's actual
local knowledge index had two synthetic mechanism IDs and its page index had zero
rows; those fixtures provide no scientific coverage. Inst-sci's formal catalog had190
real-paper records. Searches for semigroup/temporal consistency returned no match in
that snapshot, and multi-step returned three candidates. No global absence or novelty
claim follows. The relevant prior VSPC1 retrieval was reused and checked against the
same catalog before source passages.

- Lee et al., *Learning Uncertainty-Aware Temporally-Extended Actions*, AAAI2024,
  local `C:/Projects/Inst-sci/papers/MyLib/json/VS-0005.json`, p3 elements95–100/145–146
  and p4 elements216/221–237: repeated-action skip transitions feed option/action
  Q-learning. This supports the ordinary multi-step-TD containing alternative;
  the present PPO baseline has no option-Q action consumer or extra replay exposure.
  Catalog quality is B; the malformed extracted skip-transition count is not used.
- Li et al., *Revisiting Cooperative Off-Policy Multi-Agent Reinforcement Learning*,
  ICML2025, `MARL-0483.json`, p1 abstract element113: multi-step bootstrapping in an
  off-policy joint-Q setting. This confirms topical overlap only; that result is not
  evidence for this on-policy MC baseline penalty.
- For the specific residual-gradient gap, the primary paper Zhang, Boehmer and
  Whiteson, *Deep Residual Reinforcement Learning*, AAMAS2020, arXiv1905.01072v3,
  [§2 equation1 and §§3–4, PDF pp2–3](https://arxiv.org/pdf/1905.01072), distinguishes
  semi-gradients from two-endpoint gradients and explains stochastic double sampling.
  It also discusses gradient cancellation and reports mixed prior comparisons. These
  facts fix the candidate's label and prohibit importing an expected-residual guarantee.
  Its deterministic-control results do not predict this MARL comparison.

The retrieval changed the initial local assessment: the full residual loss is
nonredundant, but known. Calling every composition loss an MC rewrite would discard
a real gradient difference; calling this new semigroup information would overclaim.
Overlap is not a novelty-based launch gate. The proper node is asked whether the
specific low-burden performance observation is worth selecting.

## 5. Unselected minimal B and its decision value

Proposed name: `SCDMP-NATIVE-HOLD-RESIDUAL-B01`. One fresh matched pair, proposed
master8201, arms RESIDUAL-MC and MLP-MC, then attained hover reference H. A bounded
tracked code/Markdown search over SCDMP/UCOPE/VSPC1 and the source runners found no8201
binding before this proposal; it is not a global seed registry or a selected RNG root.
Use the source b=100000*master domains and private arm generators, common initialization
and reset inputs. On-policy trajectories may diverge. Both actors keep the duration
head, opening-only d1/d4 rule, original partial observation and `agent_compound` PPO.

Population/coordinates come from the existing UCOPE/VSPC1 host recipe, independently
of D6's duration signs: five UAVs,50 uniform users,256 primitive seconds, the unchanged
native motion/channel/service law. No population or duration qualification precedes B.
Keep CPU FP32, one Torch thread and remote-first wsl_4070 execution; this is not a
device-effect estimand. Keep512 training episodes per learned arm,256 two-episode
rollouts, four epochs/rollout,32-step truncated recurrent gradients,1024 Adam calls,
lr3e-4, clip0.2, value coefficient0.5, entropy coefficient0.01 and joint norm clip0.5.
Evaluate final sampled policies only:32 episodes/learner and32 matching H resets.
No initial/best/intermediate checkpoint selection, greedy conversion, extra seed or tuning.

Primary Delta=mean of32 reset-matched J_RESIDUAL−J_MLP values, J=native team reward
sum/256. Retain both J−H comparisons, all episode losses, conditional evaluation SE
and m/actual nonzero-hold exposure. The independent unit is one trained pair, n=1;
32 evaluations do not estimate training-seed variation. Historical VSPC1's gate result
is not a third arm or fresh competitor. Superiority to the gate is outside the claim.

Prospective MEI is absolute0.01 native time-average team reward: one continuously
served user's coverage contribution is0.7/50=0.014 in this host's recorded reward
scale. It is a useful effect scale, not a prerequisite. Tuned same-information
upper-minus-baseline headroom remains absent; H is an attained reference, not an upper.

If Delta>0.01 and the primary is trustworthy, one local package signal would support
considering one independent pair. Inside inclusive±0.01 gives no selected-scale
reason to repeat this unchanged penalty; below−0.01 favors the intact MC learner for
this choice. Neither branch closes SCDMP generally. If either arm is below H, retain
the primary but narrow usable-control language; no positive residual diagnostic or
lower fitting loss compensates native harm. Incomplete dependencies limit their
dependent claim. Those are proposed readings, not a frozen rule or allocated follow-up.
Working prediction for a selected B: WITHIN, probability0.65; owner prediction not
taken (unattended). There is no new empirical outcome to score now.

The next observation would decide whether this specific residual package merits
continued local investment. A finite reward-identity calculation already answers only
target equality; it cannot determine optimizer/native-return effects. An exact upper,
support census or separate diagnosis would not replace this direct learning comparison.

## 6. Work, exposure and bounded acceptance

Source-derived algorithm work is two fits×512×256 plus three×32×256 final evaluation:
286720 native team steps,2048 Adam calls,96 final evaluations and one independent pair.
Each fit has at most1536 nonzero-hold rows of131072 and at most6144 added scalar pair
residual terms across all four epochs. Reusing the existing full-rollout critic output
needs no additional full-network forward or separate backward/optimizer step; indexing,
residual arithmetic and its gradient contributions are extra actual algorithm work.
There is no nested candidate/action/trajectory search, solver or extra training stream.

For each arm, projection is131072*c_collection +1024*c_update +8192*c_eval plus
initialization/publication/exit; the second arm additionally carries8192 H steps and
pair publication. Treatment updates include the sparse penalty work. The accepted
source pair's308.63s enclosing wall is a planning anchor, not a bound for a new loss.
Keep1800s/arm and3600s complete logical pair caps, including required initialization,
evaluation, readback/publication and exit. Incremental wall/CPU cost is unmeasured;
no calibration invocation is proposed. A cap or primary-dependency failure stops the
single invocation, retaining every completed outcome; no automatic retry or extra arm.

Machine-generated prior exposure: the VSPC1 source MLP learner had66441 parameters,
1024 actual Adam calls and total displacement/initial-L2=0.4681669210; its critic
ratio was0.7238134732. This supports that the retained recipe can move, not a new
penalty's gain or movement. The zero-initialized duration head's huge historical ratio
is not meaningful and is not used. P56 itself has zero model/environment/optimizer/
evaluation/replay/profile/result-bearing exposure, as recorded in the facts JSON.

Engineering scope specification§4: needs none. Preparation adds no research code or
§5 budget breach. If selected, CM would add the one research loss/arm binding and
proportionate checks for both endpoint gradients, mask/no-pair behavior, preserved
MC/actor terms, primary/RNG identity and unchanged native comparison. Independent
affected-learning-path review is needed. No large replay or extra empirical arm is
required for acceptance; existing native interface checks may be reused. Before any
result launch, accepted exact source, fresh resource admission and the §11.4 exposure
line remain required. Root owns accepted-handle observation; CM owns collection and
technical acceptance; this DM owns full scientific intake.

## 7. Contrary evidence and exact re-entry assessment

SCDMP A01's six states all materially favored k13 (W2498,R7=0,R13=1). A02 validly
stopped after321 candidate missions because the required late mission docked before
the event; missing K quantities remain unobserved, not zero. No A02 duration contrast,
D6/D8 learning or old-family successor is inferred. FCEOV and other historical
stops remain unchanged. The separate headroom item stays unmeasured.

VSPC1 master8101 gave GATED−MLP +0.0293656586, GATED−H +0.0194005494 and MLP−H
−0.0099651092, with n=1 and adverse episodes retained. It shows a lawful critic-to-native
path, not residual-learning polarity; sparse hold inputs alone cannot decide performance.
Historical UCOPE6902 T−G−0.0503654/T−H−0.0332645 and6901 G−H−0.0282038 remain
contrary context. Comparators differ, so these results are not pooled.

The newer [UCOPE B02 collection](../ucope/UCOPE_UAV_MOTION_PREFIX_B02_P47_7002_AND_JOINT_TECHNICAL_ACCEPTANCE_20260908.md)
also records both T−G means negative:7001−0.0472671044 and7002−0.0061362058,
joint−0.0267016551. Both T−H means are negative (−0.0224883084/−0.0243921875).
These are technically accepted output facts; UCOPE's DM owns that result's direction
decision. They strengthen the adverse prior on useful duration-capable control,
without testing the new penalty or authorizing a change to the held-action law.
Its historical80.578s/60s engineering-smoke breach remains on its own record.

The re-entry condition is met for asking the node, in the DM's judgment: this is a
different loss/gradient question from D6 cross-k Q-sharing or source/countdown searches;
population/coordinates are fixed by a materially newer existing native learner;
the candidate changes an actual actor-learning path and is judged by native return;
its branches distinguish continued local study from stopping this penalty; and the
proposed B exercises a complete real environment/learner/trainer/evaluator. This is
not an assertion that the family has reopened. The node may find the generic residual
question too weak to warrant a successor and choose none.

## 8. Decisions this intake produces

| Tier and options | Recommendation and actual action |
| --- | --- |
| Object-level source/question preparation: (a) publish the precise residual-gradient candidate for the single P56 Convergence question; (b) yield because no worthwhile distinction remains; (c) treat the MC identity as a new loss or copy the VSPC1 gate | (a), selected as preparation only; (b) remains a close runner-up because all gains could be generic regularization. Owner-delegated decision (unattended, 2026-09-03 instruction): (a). |
| Direction: (a) select the bounded residual-MC B; (b) retain no successor; classify any actual recast | Escalated to `em:semigroup_consistent_duration_model_policy:convergence`. Recommend(a), close call. No direction choice is locally executed. Prior RECAST_D6 and subsequent PARK are preserved; no new recast count or sequencing change is recorded here. |
| Portfolio | No lifecycle, priority, capacity, fusion, registration, investment or UAV-entry decision. Root may refill a slot at the clean waiting boundary through its supplied route. |

Owner reviews returned[] at entry. Relevant current owner-ledger cells contain no
override. P2 [item20260908-scdmp-001](../../portfolio/owner/inbox/2026-09-08/20260908-scdmp-001.json)
records the preparation recommendation; its auto-applied
choice means publishing the question, not accepting a B or owner ratification.
[Chinese brief](../../portfolio/owner/briefs/semigroup_consistent_duration_model_policy/2026-09-08_P56-source-question.md).
No empirical prediction is scored; owner prediction remains not taken.

## 9. Return and continuation

The sole new request is `2026-09-08-scdmp-p56-held-residual-convergence-01`, authored
for GitHub delivery on the reusable `codex/scdmp` branch. Root receives the pushed
HANDOFF commit, fixed TASK link and this native DM return target. Transport owns
provider Send/observation; the pre-cutover conversation in old evidence is excluded
and is not rebound. Preserve any current verified binding for the same logical node.

At the clean boundary there is no live experiment or selected card. Await the
complete immutable response through Root. A conforming selection continues through
this same DM's card, CM implementation/review, accepted-source binding, single selected
bounded execution and all-outcome intake; no routine Portfolio implementation vote.
A blocker forms no decision. A no-successor answer ends this assigned source route
without inventing another question. The shared checkout remains only for this named
delivery/intake continuation; Root owns verified reclamation when it ends.
