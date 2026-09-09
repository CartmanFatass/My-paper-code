Claim under test: fixed stochastic one- or two-step own-expiry renewal retains a useful sampled native-return advantage over legal feedback when both learn continuously for 2048 episodes.
Binding MARL structure: (b) temporal abstraction or termination; five partially observed, co-adapting UAVs retain private recurrent histories under asynchronous short commitments.

# UCOPE UAV short fixed renewal continuous B01 — science card, 2026-09-09

## 1. Question and authority

**UCOPE-UAV-SHORT-FIXED-RENEWAL-CONTINUOUS-B01**, selector
**renewal_short_fixed_continuous_b01**, **B/EXPLORE**, fresh matched master **8601**.
Does the earlier short-renewal F/G difference persist when ordinary feedback G
has more learning exposure? The primary is **F−G after 2048 training episodes**;
the fixed 512/1024/2048 curves and every F−H/G−H contrast inform its reading.

**OWNER_DIRECT 2026-09-09**, relayed by Root from owner task
`01a087ed-f4c5-71e3-9f72-965da3508dc3`, adopts the
[planning synthesis §§2/5.1 at dae6a74bbf8e402a3ea47256176f5795eb277206](https://github.com/CartmanFatass/My-paper-code/blob/dae6a74bbf8e402a3ea47256176f5795eb277206/docs/research/portfolio/pro_packets/20260909_third_party_planning_comparison/RESEARCH_PLAN_SYNTHESIS_CODEX_20260909.md)
as execution instructions and allocates **one** new matched pair through intake.
The report's earlier advisory wording is historical; this explicit assignment
supplies execution authority. Root accepts/integrates the frozen card and source
before the dependent launch. This is an outcome-informed budget change inside the
accepted renewal family, not a new family, recast, C object or Portfolio decision.
**Recasts: 1**. No Pro round or additional owner reply is needed.

P83/P84 retain their positive sampled F−G points, including P84's **+0.0643936652**
alongside F−H **−0.0291844433** and G−H **−0.0935781085**. P85's mean-execution
WITHIN and all four learned-mode hover losses remain. Normalization8501 remains
WITHIN (**normalized−raw −0.0047834239**) with both hover deficits and no
unchanged normalization successor. None is pooled into this new primary.

## 2. Preserved learners and native comparison

Preserve [short fixed renewal B03 §§2–5](UCOPE_UAV_SHORT_FIXED_RENEWAL_B03_SCIENCE_CARD_20260909.md#2-preserved-package-and-comparison)
and accepted shared source at **52bf50a089d3389d9fada0b531e4f4e56e83f9b8**;
the four relevant source blobs are recorded in the prospective facts.
Only total training exposure, fixed evaluation schedule and new RNG/output
bindings change. There is no value-target normalization, reward shaping,
critic change, mean execution, extra comparator or best-checkpoint selection.

F holds its sampled velocity for physical **{1,2} primitive steps**, half each,
at its own expiry. The entire **2242-parameter duration head stays frozen**:
its hidden layer retains its seeded random initialization; only the final
weights/bias start at zero. Preserve `arm_copy(..., True, duration_head_seed=b+12,
freeze_duration=True)`. Do not zero the hidden layer. Categorical labels remain
0/1 for likelihood and selected-label horizon censoring; retain suppression,
held actions, literal d2/d4 counts and remaining/4 features. G has no duration
head and may choose a legal velocity each step. H is untuned zero velocity,
with no learner or action draws. F/G each have **66311 trainable parameters**;
total F **68553**, G **66311**.

Both real fits retain five UAVs, horizon256, native reward, private actor
information/history, centralized critic information, per-primitive-step GRU
updates, compound clipping, primitive credit, all-row denominator, zero entropy,
gamma1, raw Monte Carlo targets, existing detached advantage normalization,
Adam lr0.0003 and four epochs per two-episode rollout. `value_moments=None`
throughout both arms and all evaluation. Membership is fixed: no join, leave,
rejoin, replacement, survivor-state or discount-clock change. The sampled F/G
evaluators use the corresponding learned velocity policies; F retains its fixed
stochastic duration law.

Private observation → each UAV's recurrent history → velocity at own expiry
and held motion → later service/information → masked actor/critic exposure and
partner co-adaptation → native return is the package being tested. More training
may change any of those learned paths. Equal steps/Adam counts do not isolate a
duration cause or equate compute. Reuse legal G/H because observation, action
and information match, with G's training budget extended to match F. No tuned
same-information baseline/upper headroom record is available; H is not an upper.

## 3. Continuous training, RNG and fixed evaluation worlds

Master **8601**, **b=860100000**. Common actor/critic initialization **b+11**;
F duration-head initialization **b+12**. Persistent G training velocity/duration
generators **b+21/b+22** and F generators **b+31/b+32** retain the accepted draw
rules (G's duration generator is unused). The scoped UCOPE master/base/selector
search found no prior match; this is no global RNG census.

Each arm trains **2048 episodes continuously**, using the same actor, critic,
optimizer and private training generators through **1024 two-episode rollouts**.
Training reset for episode e=0..2047 is **b+10000+e**. After the updates for
rollouts **256/512/1024** (training episodes **512/1024/2048**), evaluate **64**
sampled episodes. No optimizer or recurrent policy is reinitialized at a
checkpoint, and evaluation supplies no update data or checkpoint selection.

Use the **same frozen evaluation panel** at all three checkpoints and for H:
reset **b+20000+e**, e=0..63. It is disjoint from all training resets; the old
1000/2000 blocks would overlap under expanded training and are not reused.
For checkpoint index j=0/1/2, fresh per-episode evaluation generators are:

| Arm | Velocity seed | Duration seed |
| --- | --- | --- |
| F | b+30000+1000*j+e | b+40000+1000*j+e |
| G | b+50000+1000*j+e | b+60000+1000*j+e (unused) |
| H | none | none |

Evaluation never consumes training generators or invokes global reseeding;
the accepted collector creates fresh held-action, previous-action and zero-GRU
episode state at each reset. Reuse one environment per fitted arm: an evaluation
occurs only after a complete rollout, and the next training episode resets the
environment to its declared training seed. Its accepted reset replaces local
environment RNG, positions/users/connections/cache. Evaluation does not change
actor/critic parameters, buffers, optimizer state or normalization. There are
**two constructors/two constructor resets**, not extra evaluation environments.
H runs **once after G's final evaluation**, using that environment and the same
64 reset worlds; its vector is reused for each checkpoint's paired H contrasts.
Common worlds do not align learned trajectories or make checkpoints independent.

## 4. Exposure, work and resource bounds

[Machine-generated prospective facts](UCOPE_UAV_SHORT_FIXED_RENEWAL_CONTINUOUS_B01_8601_PROSPECTIVE_FACTS_20260909.json)
record the selected configuration and executable arithmetic. One new matched
training instance has **2 fits, 4096 training episodes, 1048576 training steps,
2048 rollouts, 8192 Adam calls**, and **448 evaluation episodes/114688 steps**
(2 arms × 3 checkpoints × 64 + 64 H). Total **1163264 native steps** and
**4544 explicit resets**, plus the two constructor resets. All actor/critic
parameters can move during 4096 Adam calls per arm at lr0.0003; F's entire
duration head is excluded/frozen. Preserve ordinary group displacement evidence.
Preparation uses zero scientific invocations, models, environment calls or draws.

F head work is **6×training renewals + 2×all three evaluation-panel renewals**:
**8110080–16220160 rows**, **17907056640–35814113280 dense MACs**, 2208 per row.
There is no nested candidate search, checkpoint search or extra trajectory sweep.
This F-only work is additional to its velocity/critic work, despite equal
trainable parameter counts. Algorithm work and supporting synthetic checks
are reported separately.

The [P84 measured reference](UCOPE_UAV_SHORT_FIXED_RENEWAL_B03_P84_RESULT_SUMMARY_20260909.json)
has F **163.87369038298493 s**, G including H **133.33607813803246 s**, outer
**313.90 s**. Scaling native work gives F **674.7740192240556 s** and G/H
**533.3443125521298 s**, sum **1208.1183317761854 s**. A separate reference-cost
envelope uses the largest component ratio (training/Adam4×, learned evaluation6×,
H2×, initialization1×): F **983.2421422979096 s**, G/H **800.0164688281948 s**.
These are projections from known work, not measurements or runtime guarantees;
trajectory-dependent costs and added curve publication remain unmeasured. No
known projection exceeds the cap, and no cost probe is allocated.

Caps are **1800 s per complete arm / 3600 s per complete invocation**, through
initialization, training, all scheduled evaluation, publication and exit. Run F
then G; charge startup to F and H/final publication to G. Clocks remain continuous
across checkpoints. Supporting engineering/check execution is **≤300 s** total.
Use configured **remote_first/hmasd-wsl-node, CPU FP32, one Torch thread**;
host identity is not the estimand. Commit/push exact source, run detached at its
SHA under agent-task, and require actual-node canonical memory admission with
physical/effective availability ≥4 GiB immediately joined by `&&` to the runner
before scientific roots, RNG or learners. Local fallback follows AGENTS §5;
no unannounced device, dtype, budget or information change is permitted.

## 5. Primary, curve reading and predictions

For every episode, **J=sum_t sum(info['rewards_dict'].values())/256**. At each
checkpoint retain all 64 F and 64 G returns; retain all 64 H returns once.
Publish **F−G, F−H, G−H** paired vectors, means and conditional evaluation SE
`sample_sd(differences)/sqrt(64)` at each checkpoint. Use checkpoint plus
episode identity, so later rows cannot overwrite earlier ones. Main
**Delta_2048=mean_e(F_2048−G_2048)** is fixed prospectively. No best point, pooled
checkpoint mean, replacement primary or training-population interval is selected.

**MEI absolute 0.01 J**, preserving this host's earlier useful-effect scale so
budget growth is assessed on the same native quantity. **Headroom absent**.

| Complete final primary | B-level reading |
| --- | --- |
| UP: Delta_2048 > +0.01 | Preliminary favorable short-renewal package evidence after the allocated training budget on this one fitted pair. |
| WITHIN: −0.01 ≤ Delta_2048 ≤ +0.01 | No demonstrated point gain at the selected scale on this fitted pair; this is not equivalence. |
| DOWN: Delta_2048 < −0.01 | Adverse short-renewal package evidence at the final budget; earlier gains or either hover result do not rescue this primary. |

Apply unrounded points and report their distance from the relevant boundary.
Final F/G completeness governs the primary; full allocation completion also
requires both full training histories, all three scheduled panels and H. A
missing dependent measurement limits its claim; preserve intact partial facts
without imputation or a replacement run. Optional missing resource telemetry is
`resources_unmeasured`.

**How the result will be interpreted:** final above-MEI F−G with beneficial
F−H supports considering a second independent pair. If G improves with budget
and F−G shrinks, disappears or reverses, the curve may indicate an early-budget
effect on this history; do not keep copying the 512-point gain. F beating G while
both lose to H is a valid package contrast with limited native use value. A
WITHIN or mixed curve retains uncertainty; a second pair is recommended only
if it would change the next choice, without an all-positive requirement. A final
opposite-sign result counts against the package at this budget. Every outcome
ends this allocation. Any next pair, changed learner, learned-duration arm or
host condition needs a separately recorded selection/allocation.

One **matched training instance** is the independent unit. The three checkpoints
share its optimizer/data history; the 64 evaluation worlds describe conditional
performance. Use a task-specific curve table/plot, and the existing run-summary
tool only for the single final fitted F/G pair. H is not a training replicate.
No stable superiority/harm, causal duration effect, tuned comparator competence,
headroom, general sample efficiency or deployment claim follows.

Prospective predictions: **P(Delta_2048>0.01)=0.55**;
**P(F_2048−H>0)=0.40**; **P(mean(G_2048)−mean(G_512)>0)=0.65**.
Earlier F/G gains support the first weakly; recurring hover losses temper the
second; extra learning may help G but does not guarantee monotone improvement.
Score these exact events with Brier losses and preserve all three. Owner
prediction **not taken (unattended)** unless an applicable reply arrives.

## 6. Scope, acceptance and stop

**Engineering scope §4: none.** Add one narrow driver and thin CLI reusing the
accepted collector/update/policy/environment. Existing initial/final policy
checkpoints and ordinary logs suffice; fixed intermediate evaluation does not
need new recovery/checkpoint-selection machinery, runtime RNG guards or a new
telemetry framework. New source ≤2000 lines and runner ≤600. No native smoke,
profiling, tuning, scalar diagnostic, second pair or automatic successor.

Focused synthetic checks plus the existing independent reviewer cover the
changed continuous optimizer/training-RNG path, evaluation nonmutation and
disjoint seed laws, frozen whole F head, correct checkpoint/episode labels,
shared H contrasts and honest partial/final-primary completeness. Reuse accepted
reward/information/credit/duration checks; do not rerun unchanged suites.
Fixture master9001 is synthetic only. Source and frozen card go to Root for the
requested acceptance/integration before this already-authorized launch.

One accepted scientific invocation only. Stop on actual failed admission, cap,
nonfinite learning or a defect threatening reward, information, training,
comparison or primary measurement. Pre-science staging/admission rejection may
receive an exact technical repair where no invocation was accepted; reconcile
uncertain acceptance before action. An actually failed scientific attempt has
no retry, resume or replacement allowance.

After launch acceptance, CM sends **MONITOR_ADD directly** to the independent
Monitor in live `C:/Projects/HMASD/.codex/hmasd-monitor.toml`, using current main
`docs/project/EXPERIMENT_MONITOR.md`. CM records dispatch/adoption pending and
stops routine polling. Root confirms adoption and resumes the original CM for
terminal collection; DM performs scientific intake. Root owns integration,
reclamation and subsequent allocation. No parallel status polling or Pro Send.

## 7. Grounding and handoff

Reuse verified local UTE retrieval in [P82 intake §8](UCOPE_UAV_SHORT_FIXED_RENEWAL_B01_P82_INTAKE_20260909.md#8-bounded-interpretation-grounding-and-predictions)
and current primary `FOUNDATIONS.md` §§5–6, topic notes `03_HIERARCHY_ASYNC.md`
(fixed options/primitive clocks) and `04_EMPIRICAL.md` (training units/curves).
Fixed durations can define a valid option; that does not establish value or
Markov sufficiency. Three checkpoints from one optimizer history do not become
three learning replications. These assumptions support the declared endpoint,
all-curve display and conditional uncertainty; they do not establish this
mechanism's effect. No new literature claim or causal localization is needed.
Controlling evidence specification: §§4,5.2,11.4,11.7–11.10.

[Prospective intake §3](UCOPE_UAV_SHORT_FIXED_RENEWAL_CONTINUOUS_B01_8601_INTAKE_20260909.md#3-five-item-cm-assignment)
provides the original CM's five-item assignment in the shared `codex/ucope`
checkout. Frozen §§1–7 remain prospective through intake; later observations
are appended in their own result/intake sections.
