裁决
ACCEPT R46-HMRV-G0 LAUNCH-EXACT CLARIFICATION
	​


R45 的 VALID_FAIL_R45_SDRA_IDENTIFIABILITY、Alice–Bob K=50 natural-support temporal substrate 的退休，以及唯一后继路线 R46-HMRV-G0 均保持不变。本轮只补齐六项可复现合同；不改变环境、预算、模型容量、科学阈值、结果分支或禁止项。

1. Three-block discount

固定：

γ=0.99
	​


三 block estimand 为：

G
τ
(3)
	​

=
r=0
∑
14
	​

0.99
r
r
τk
0
	​

+r
env
	​

,k
0
	​

=5.

它包含：

action 所在的当前 block；

紧随其后的第一个 block；

紧随其后的第二个 block。

折扣按 15 个连续 primitive steps 计算，不在 block 边界重新从 1 开始。只有拥有完整三 block future 的前六个 checks 进入 critic 数据。该定义保持原提案的“当前维护成本 + 后续两段恢复收益”estimand。

2. First-factor prefix encoding

二元动作编码固定为：

KEEP  = 0
RENEW = 1

六维 focal context 的最后两项固定为：

agent 0:
[prefix_valid, b_<i] = [0, 0]

agent 1:
[prefix_valid, b_<i] = [1, actual_b0]

因此，首因子的第二个零只是 sentinel；当 prefix_valid=0 时，不能被解释为“前序 agent 选择 KEEP”。第二因子的 actual_b0 是 agent 0 实际采样并执行的 0/1 renewal action。

3. Critic optimizer 与确定性 schedule

R46 完整复用 R45 critic 合同：

optimizer       Adam
learning rate   5e-4
epsilon         1e-5
betas           (0.9, 0.999)
weight decay    0
amsgrad         False
epochs          15
minibatch       256
drop_last       False

每个 fold 内：

true-Q 与 action-blind sham 从同一个 SDRAQHead base model 深拷贝，初始参数逐位相同；

两者使用完全相同的 15 个 epoch permutation；

input normalization 只由该 fold 的 training environments 拟合；

held-out environments 不参与 normalization、初始化、shuffle、early stopping 或模型选择。

R45 的确定性规则是：fold model seed 为 base_seed + fold_index*10000，shuffle seed 为 model_seed + 1000003。

R46 以 46041 为 base seed，因此固定为：

fold A
  train env ranks        0..7
  held-out env ranks     8..15
  model-init seed        46041
  shuffle seed           1046044

fold B
  train env ranks        8..15
  held-out env ranks     0..7
  model-init seed        56041
  shuffle seed           1056044

SDRAQHead 初始化规则也原样复用：hidden weight orthogonal initialization、hidden bias 为零、output weight 与 bias 为零。

4. Bootstrap unit

科学 bootstrap cluster 固定为：

独立 source episode
	​


cluster key 为：

(env_rank, episode_index)

一个 cluster 包含该 episode 内：

所有六个 usable checks；

两个 focal-agent rows；

同一 check 的两个 agent rows；

该 episode 内全部时序依赖。

选择 episode 而不是 persistent environment rank，是因为 HMRV 每个 episode 都从固定初始 health 独立重置，并重新确定角色分配；同一 episode 内的多 check rows 才是必须共同重采样的相关单元。

固定：

bootstrap repetitions = 10000
bootstrap seed        = 62046

以下全部使用 episode-cluster bootstrap：

M2 true-Q versus sham WMSE ratio-gain；

M2 top-minus-bottom DR score；

两个 agent 的 M3 top/bottom DR intervals；

pooled same-check sign-discordance interval；

两个 role-stratified sign-discordance intervals。

M1 的 maximum_environment_weight_share 仍按 persistent environment rank 分组，不改成 episode grouping。这一指标继续检查某个长期 worker stream 是否垄断特定 agent/action 的有效权重。R45 的旧 analyzer 使用 environment rank 作为其 substrate 的 bootstrap unit；R46 在新独立-episode substrate 上明确改用 episode cluster，但保留 M1 的 environment-rank concentration audit。

5. Evaluation stream

100 个 evaluation episodes 的 action RNG seed 固定为：

56041
	​


在 evaluation 开始前，预生成并保存：

role_assignments [100, 2]
renewal_actions  [100, 8, 2]

其中：

episode index even -> (d_agent0, d_agent1) = (1, 2)
episode index odd  -> (d_agent0, d_agent1) = (2, 1)

renewal_actions 使用 np.random.default_rng(56041) 产生独立 Bernoulli-0.5 draws。

“paired evaluation”只表示：

critic fitting 前运行一次；

critic fitting 后重放完全相同的 100 个 role assignments；

重放完全相同的 Bernoulli action tensor；

比较 action、health、service-output 和 reward traces 是否逐项相同。

它只属于 M0 trace-equality audit。R46 没有 trained policy scientific arm，critic prediction也不参与环境执行。

6. Role-stratified M3

两个 strata 精确定义为有序分配：

stratum A: (d_agent0, d_agent1) = (1, 2)
stratum B: (d_agent0, d_agent1) = (2, 1)

每个 stratum 单独使用 episode-cluster bootstrap，并分别要求：

LCB
95
	​

[P(sign
Δ
^
0
	​


=sign
Δ
^
1
	​

)]>0.10
	​


不增加新的 stratum point-estimate threshold。

原有 pooled M3 条件保持不变：

P(sign discordance)≥0.20,
LCB
95
	​

>0.10.

两个 role-stratified lower bounds 都必须通过；不能由一个角色分配的 PASS 抵消另一个的 FAIL。

可直接写入 memory/ExpRecord.md 的合同块
### EXP-20260716-r46-hmrv-g0

- Status: launch-ready after R46 contract clarification.
- Causal edge:
  native heterogeneous process degradation
  -> balanced natural KEEP/RENEW support
  -> action-specific delayed renewal value
  -> same-check agent/context-specific sign heterogeneity.
- Scope: reward-off fixed-N=2 temporal-substrate positive control. It is not
  skill learning, intrinsic-reward training, benchmark performance, S7,
  open-roster, or variable-N evidence.

- Execution:
  target=local CUDA; cloud prohibited for G0.
  environment_seed=46041.
  behavior_action_seed=46041.
  N=2; k0=5; horizon=40; 8 checks/episode.
  16 environments; 100 episodes/updates per environment.
  64,000 primitive steps.
  policy/low/intrinsic optimizer steps=0.
  behavior policy: independent Bernoulli(0.5) KEEP/RENEW per agent/check.
  KEEP=0; RENEW=1.
  role schedule:
    even episode -> (d_agent0,d_agent1)=(1,2)
    odd episode  -> (d_agent0,d_agent1)=(2,1).

- Three-block outcome:
  gamma=0.99.
  G_tau^(3)=sum_{r=0}^{14} 0.99^r r_env[tau*k0+r].
  It includes the action's current block and following two blocks, with no
  discount restart at block boundaries.
  Only the first 6 checks/episode enter the estimand.
  usable checks=9,600; usable focal rows=19,200.

- Six-value focal context:
  [h_i/4, h_other/4, d_i/2, d_other/2, prefix_valid, b_<i].
  agent0 prefix=[0,0].
  agent1 prefix=[1,actual_b0].
  The sentinel b_<i>=0 is ignored whenever prefix_valid=0.

- Critics:
  folds:
    A train env 0..7, heldout 8..15.
    B train env 8..15, heldout 0..7.
  per fold: one true-Q and one action-blind propensity-mixture sham.
  architecture=6->32 GELU->2.
  true/sham initialization, normalization, minibatch schedule, capacity and
  exposure are identical.
  Adam(lr=5e-4, eps=1e-5, betas=(0.9,0.999),
       weight_decay=0, amsgrad=False).
  epochs=15; minibatch=256; drop_last=False.
  fold-A model-init seed=46041; shuffle seed=1046044.
  fold-B model-init seed=56041; shuffle seed=1056044.
  optimizer steps/model=570; total critic steps=2,280.

- Bootstrap:
  repetitions=10,000; seed=62046.
  scientific cluster=(env_rank,episode_index), i.e. independent source episode.
  All M2/M3 intervals and both role-stratified discordance intervals use
  episode-cluster bootstrap.
  M1 maximum-weight share remains grouped by persistent environment rank.

- Evaluation:
  episodes=100.
  evaluation action RNG seed=56041.
  Pre-generate role_assignments[100,2] and Bernoulli actions[100,8,2].
  Replay the exact same assignments and actions before and after critic fitting.
  Pairing is solely an M0 trace-equality audit; there is no trained-policy arm.

- M0:
  exact registered transition/reward formulas; propensity=0.5; action replay
  error=0; exact counts; zero policy/low/intrinsic updates; four critics each
  570 steps; no fold overlap; finite gradients/predictions/weights/DR scores;
  registered six-field context only; pre/post action/state/reward traces exact;
  at least one zero-reward and one full-service block.

- M1:
  for each agent/action ESS>=64.
  persistent-environment maximum normalized weight share<=0.10.

- M2:
  LCB95(WMSE_sham/WMSE_true - 1)>0.
  LCB95(mean_psi_top - mean_psi_bottom)>0.

- M3:
  for each agent:
    LCB95(mean_psi_top25)>0;
    UCB95(mean_psi_bottom25)<0.
  pooled same-check predicted-sign discordance point>=0.20 and LCB95>0.10.
  ordered role strata are (1,2) and (2,1); each stratum separately requires
  sign-discordance LCB95>0.10.

- Branches:
  INVALID_R46_HMRV_WIRING:
    M0 failure; repair only the explicit implementation defect and rerun the
    unchanged contract.
  PASS_R46_HMRV_IDENTIFIABILITY:
    M0-M3 all pass; authorize only a same-substrate per-agent renewal actor
    versus shared-sync control.
  VALID_FAIL_R46_HMRV_SUBSTRATE:
    M0 valid and any M1-M3 failure; permanently retire the exact HMRV dynamics,
    three-block estimand and positive-control substrate without seed, data,
    capacity, threshold, clipping, reward or environment rescue.
