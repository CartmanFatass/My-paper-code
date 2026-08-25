裁决
CONFIRM VALID_FAIL_R47_NSOPM
	​

CONFIRM NO-RESCUE RETIREMENT OF THE EXACT R47 LINE
	​

SELECT R48-SBRS-G0: Skill-Boundary Recurrent State
	​


固定 N 的技能/寿命探索暂不完全停止，但只剩这一条架构层因果边。R48 若有效失败，则当前 fixed-N skill/lifetime 探索正式停止；不得继续发明新的 scorer、mode target、renewal critic 或 intrinsic reward，并且 open-roster/variable-N 仍不能继承任何“技能机制已工作”的主张。

一、R47 validity verdict

没有发现会改变分支的具体 M0 缺陷。

1. 七维 view 与自然窗口日程正确

实现从物理位置除以 world_size=8，构造 focal displacement、teammate-relative mean displacement 和 relative-set covariance displacement；在 N=2 时 covariance singleton 的三个字段严格为零。字段顺序、shape [512,10,7] 和 population covariance 均与注册合同一致。

64 个 reset groups 的自然日程也正确：

偶数组选择 checks {0,2,4,6}；

奇数组选择 {1,3,5,7}；

每个 check 为两个 focal agents各生成一个完整窗口；

总计 64×4×2=512 个自然窗口；

实际环境 reward 被丢弃，R30 时钟只收到字面 0.0。

2. Split-specific normalization、35-D map 与 pooled-lag operator 正确

Primary、half A、half B 都在自己的训练 split 上独立拟合 population mean/std，然后进行 window-initial centering。35 维特征按七个线性项和固定 upper-triangular 二阶项构造。

代码使用 reduced whitening coordinates：

W
0
	​

=D
0
−1/2
	​

U
0
⊤
	​

,
W
1
	​

=U
1
	​

D
1
−1/2
	​

,

而 launch contract用 full projector形式书写：

W
0
	​

=U
0
	​

D
0
−1/2
	​

U
0
⊤
	​

.

两者在 retained covariance subspace 内代数等价：非零 Gram eigenvalues、mode activations及后续 E,X,C,g 完全一致。因此这是实现形式差异，不是 estimand defect。代码也确实使用 lag {1,5}、pooled C
00
	​

/C
11
	​

、lag-specific C
01
	​

、未对 T
ℓ
	​

 做 reversible symmetrization，并按降序冻结 Gram modes。

3. Temporal null、half-fit alignment 与 coherence 正确

每个 temporal-null replicate都在 window 内对已经 initial-centered 的长度 10 序列做非 identity permutation，并重新拟合完整 spectral estimator。Half A/B 通过 exhaustive 4! assignment对齐到 primary，使用 absolute correlation选配并按 primary翻转 sign。

Held-out coherence使用 frozen primary activations，对 lag 1、5分别计算 cosine-style temporal correlation，并与 256 个 frozen-basis temporal permutations的均值比较；随后先在每个 reset group内平均，再以 reset group bootstrap。

4. Nuisance audit 正确

Audit-only nuisance regression使用：

focal/teammate initial positions；

focal indicator；

clipped focal age；

focal和teammate二维 action variances。

它没有把这些字段送入 mode fitting。Split固定为 groups 32..47 训练、48..63 测试，使用解析 multi-output ridge和最大 pooled/per-mode R
2
。

5. Forced snapshot、CRN 与 recurrent flow 正确

每个 causal context保存了：

environment probe snapshot与adapter RNG；

observation/state；

roster、age、mask、team code；

low actor/critic recurrent states；
-全局 RNG状态。

Branch恢复环境快照后，只覆盖 focal actor-visible skill；teammate skill保持自然值，高层被完全抑制，两个低层 recurrent states从自然 snapshot继续传播。四个 skills在同一个 context/replica下使用相同 seed，两个 replicas使用不同 seed。总分支数和步数分别为 512 和 20,480。

捕获但未重新写入的 Python/NumPy/Torch snapshot RNG不是结果缺陷，因为正式 CRN合同明确用：

67041+2c+r

覆盖 policy sampling stream；environment RNG则由 probe snapshot与adapter RNG恢复。各 skill的采样调用次数和batch顺序相同。

6. Support、assigned contrast、SNR 与 branch logic 正确

一个 branch window必须至少有 9/10 个点不超过 held-out natural q95；一个 context只有在四 skills × 两 replicas全部通过时才可进入 M2。代码没有选择性删除某个不利 skill branch。

Assigned-mode contrast、replica averaging、六个 skill-pair的 between distance、同 skill replica distance和 ratio-of-context-means ρ
H
	​

 均符合合同。

Analyzer的终端逻辑也是注册逻辑：

M0 failure       -> INVALID_R47_NSOPM_WIRING
M0/M1/M2 pass    -> PASS_R47_NSOPM_IDENTIFIABILITY
M0 valid and
M1 or M2 failure -> VALID_FAIL_R47_NSOPM

因此：

没有 result-changing M0 defect；R47 是有效科学失败。
	​

二、R47 的可复用因果结论

必须把六个对象分开。

1. Natural low-dimensional repeatability：存在

Primary、half A、half B 都保留了 14 个 nontrivial directions。Half-to-primary correlations为 0.9568–0.9933，aligned A/B stability为 0.8759–0.9610；nuisance最大 test R
2
=−0.0713。因此自然数据中确有跨 split 可重复、且不能由注册 nuisance字段解释的低维动力学结构。

但：

可重复的低维自然动力学

=四个可用 skill modes.
	​

2. Temporal-null significance：只有一个 rank成立

只有 rank 0 超过 matched temporal-null q95。Ranks 1–3均低于各自 null threshold。

因此不能声称自然支持上存在四个独立、非平凡的持续过程方向。

3. Long-lag coherence：没有建立

Lag-1 real-minus-null coherence的 lower bound为正：

0.00433,

但 lag-5 lower bound为：

−0.04475.

所以检测到的结构主要是短时重复性，尚不能解释为一个完整 W=10 过程上的稳定模式。

4. Natural support：H10不足

H10只有：

46/64=0.71875

个 context的八个 branches全部位于注册自然支持中；H40-late为：

53/64=0.828125.

这说明许多 skill intervention在最初 10 步就进入自然 basis没有覆盖的过程区域。

5. Skill-conditioned occupancy：不成立

H10 pooled assigned contrast的95%区间跨零，并且 skills 2、3点估计为负。H40-late pooled contrast虽然为正，但 skill 0仍为：

−0.01542.

所以数字标签与 frozen spectral ranks之间不存在 codebook-wide一一占据关系。

6. Stochastic execution noise：支配 skill差异

Between/within causal-SNR均值仅为：

ρ
10
	​

=0.0343,ρ
40,late
	​

=0.1992.

换言之，同一 skill两个随机 replicas之间的变化远大于不同 skills平均过程向量之间的变化。Persistence ratio 3.696只表示一个很小的早期 contrast在late window被放大，不能覆盖 support、null significance、per-skill sign和SNR失败。

绑定结论为：

	​

自然动力学具有可重复低维结构；
但该结构主要不超过时间置换 null，且缺少长 lag coherence；
冻结数值 skills 不能稳定占据四个 spectral ranks；
skill差异小于 stochastic execution variability。
	​

	​

三、R47 retirement boundary

永久退休以下完整组合：

	​

七维 relative-moment delta view
+window initial centering
+35-D quadratic map
+lags {1,5}
+pooled-lag whitened Gram
+四个 spectral-rank identities
+S(w,z)=g
z
	​

−
4
1
	​

q
∑
	​

g
q
	​

+相应 reward-on pair.
	​

	​


不得通过修改：

window或lag；

mode count；

neural encoder、kernel或feature map；

checkpoint、seed、数据量或null数量；

support、coherence、SNR或assigned-mode threshold；

post-hoc skill/mode alignment；

task字段、action likelihood或reward；

重新打开。正式 disposition与结果 JSON已经绑定这一 no-rescue retirement。

四、fixed-N 是否应停止

不立即停止，但只保留最后一个架构层因果边。

原因不是怀疑R47 estimator，而是R47的forced intervention保留了一个从未单独审计的状态语义：

focal skill被改变，但 focal low actor的 recurrent hidden仍完整继承自此前自然技能历史。

在forced branch中，代码明确执行：

skills[focal] = forced_skill
actor_hxs     = natural_snapshot_actor_hxs

随后两者共同传播。

这符合R47预注册合同，因此不是R47无效原因。但它留下一个结构上不同的问题：

改变 skill label 时不建立 recurrent-state boundary，是否使新 skill 的过程被旧 skill memory 污染？
	​


自然source合同也明确让low recurrent hidden跨high checks和skill SET连续传播，只在episode reset时归零。

因此唯一仍有依据的fixed-N边是：

skill SET→是否应同时形成 focal recurrent-state boundary→是否降低同 skill随机变异并恢复可执行差异
	​


它不改变R47 view、basis、mode count或score，也不增加intrinsic reward。

五、唯一下一路线：R48-SBRS-G0
Skill-Boundary Recurrent State
1. 算法对象

Treatment只改变一条低层状态语义：

KEEP:
    保留当前 skill
    保留 focal actor recurrent hidden

SET(z != incumbent):
    切换到 z
    将 focal actor recurrent hidden 归零

Teammate actor hidden、所有 critic hidden、team code、环境状态和网络参数均不改变。

这不是：

skill-indexed多bank扩容；
-新GRU；
-新encoder；

reward或loss；

entropy调节；

R47 spectral rescue。

它测试的是：

一个新 skill 是否需要一个明确的 recurrent process boundary。
	​

2. Source与contexts

固定使用同一个R47 source checkpoint：

logs/r30_alice_bob_paired_64k_20260714_163908/
runs/adaptive_keep_set/seed30031/
standalone_process_core_final.pt

固定：

source seed             47041
reset groups            64
focal agent             group mod 2
context check           1 + floor(group/2) mod 4
context primitive time  {10,20,30,40}

选择这些时点是为了确保focal hidden已经包含至少一个完整自然skill block；不使用episode初始零hidden作为科学context。

每个context在自然high commit后、该block首个low action前保存snapshot。令自然post-check incumbent为 z
i
−
	​

。只审计三个非incumbent targets：

Z
c
	​

={0,1,2,3}∖{z
i
−
	​

}.
3. 两个mechanism-matched arms
carry_hidden

focal skill强制为target z；

focal actor hidden使用自然snapshot值；
-其余状态不变。

reset_on_set

focal skill强制为同一target z；
-只将focal actor hidden设为零；

teammate actor hidden、所有critic hidden及其余状态与control完全相同。

两臂：

都冻结所有参数；

都抑制high controller；

都持有roster 40步；

都丢弃environment reward；

都执行stochastic tanh-Gaussian low policy。

4. CRN与预算

预生成Gaussian innovation tape：

η
c,r,t,a,d
	​

∼N(0,1),

固定seed：

68041

相同context/replica下，两个arms和三个target skills使用完全相同的innovation tape；replicas独立。

固定规模：

contexts                   64
targets/context            3
replicas/target            2
arms                       2
branch horizon             40
forced branch steps        64*3*2*2*40 = 30,720
natural source steps       64*80 = 5,120
policy/high/critic updates 0
intrinsic reward           0
external reward read       0
bootstrap repetitions      10,000
bootstrap seed             62,048
5. Task-blind process read

令：

p
ˉ
	​

i,t
	​

=p
i,t
	​

/8,
r
i,t
	​

=
p
ˉ
	​

−i,t
	​

−
p
ˉ
	​

i,t
	​

.

每一步的四维过程状态为：

y
i,t
	​

=[
p
ˉ
	​

i,t
	​

−
p
ˉ
	​

i,0
	​

r
i,t
	​

−r
i,0
	​

	​

]∈R
4
.

不使用：

R47七维view；
-quadratic feature；
-spectral basis；
-mode label；
-action likelihood；
-task object、contact、phase、success；
-external reward。

两个horizons固定为：

H10       t = 1..10
H40-late  t = 31..40

轨迹距离：

d
H
	​

(y,y
′
)=
∣T
H
	​

∣
1
	​

t∈T
H
	​

∑
	​

∥y
t
	​

−y
t
′
	​

∥
2
2
	​

.
6. Between/within统计

对arm a、context c：

B
a,c
H
	​

=
(
2
3
	​

)
1
	​

z<z
′
∑
	​

2
1
	​

r=0
∑
1
	​

d
H
	​

(y
a,c,z,r
	​

,y
a,c,z
′
,r
	​

),

其中same-replica target comparison使用CRN。

W
a,c
H
	​

=
3
1
	​

z
∑
	​

d
H
	​

(y
a,c,z,0
	​

,y
a,c,z,1
	​

).
ρ
a
H
	​

=
E
c
	​

[W
a,c
H
	​

]+10
−8
E
c
	​

[B
a,c
H
	​

]
	​

.

每个target skill另计算相应的 ρ
a,z
H
	​

。

六、最小 abandonment gate
M0：implementation validity

必须同时满足：

exact source checkpoint/config；

64 contexts、384 branches/arm、30,720 total branch steps；

每个context恰好三个nonincumbent targets；

无early reset/truncation；

snapshot restore误差为0；

两臂同一context/target/replica的environment、observation、roster、team code和noise tape完全相同；

唯一状态差异为：

reset_on_set focal actor hidden = 0
carry_hidden focal actor hidden = snapshot value

teammate actor hidden、所有critic hidden逐项相同；

所有网络参数和normalizer drift为0；

所有optimizer steps为0；

evidence不含reward或task字段；

target skill support每个skill至少32个contexts；

所有轨迹、distances、B,W,ρ有限。

失败：

INVALID_R48_SBRS_WIRING

唯一动作是修复明确的snapshot、hidden、CRN、count或metric defect，并原合同重跑。

M1：recurrent-boundary causal gate

对H10和H40-late均要求：

LCB
95
	​

[ρ
reset
	​

]>1,
LCB
95
	​

[
ρ
carry
	​

ρ
reset
	​

	​

]>1.25,
UCB
95
	​

[
EW
carry
	​

+10
−8
EW
reset
	​

	​

]<0.80,
LCB
95
	​

[
EB
carry
	​

+10
−8
EB
reset
	​

	​

]>0.90.

此外H40-late必须：

ρ
reset,z
H40
	​

>1∀z∈{0,1,2,3}.

Bootstrap unit是完整natural source context；同一context的两个arms、三个targets、两个replicas和全部trajectory coordinates必须共同重采样。

七、互斥分支
PASS_R48_SBRS_G0

条件：

M0∧M1.

允许结论仅为：

在固定R30 source上，skill SET时清理focal recurrent state能够在不消除target-skill间process difference的情况下，实质降低同skill stochastic variability并恢复codebook-wide persistent separation。

唯一后续动作：

实现一次mechanism-matched、reward-pure R30 pair：原始 carry_on_SET 对 reset_on_SET。两臂网络和外部reward完全相同；无intrinsic；high return仍external-only。

不直接进入S7、open roster或variable-N。

VALID_FAIL_R48_SBRS

条件：

M0∧¬M1.

永久退休：

SET时zero-reset focal actor hidden；

shared-parameter skill-boundary reset路线；

该raw-trajectory between/within gate；

以recurrent contamination解释R47/R31类失败的路线。

并作出绑定决定：

\boxed{ \text{fixed-}N \text{ skill/lifetime algorithm exploration停止。}

之后不得再提出新的fixed-N intrinsic、classifier、effect scorer、mode estimator、renewal critic或actor-noise变体；open-roster只能作为独立架构研究重新立项，不能继承“技能语义已解决”的前提。

不存在 UNDERPOWERED、追加seed、追加context或threshold调整分支。

八、永久关闭的分支

继续永久关闭：

old-z classifier、q
d
	​

/q
D
	​

 reward revival及其变体；

action-density/action-information reward；

observational effect posterior / CFEI；

direct IFEPG与任何effect-gradient改名；

roster complementarity scorer/high-head fitting；

hindsight clustering、prototype、mode distillation；

R35–R40的access/substrate路线；

R42 incumbent-logit residual；

R43 full-stack true-renewal continuation；

R44 frozen-source next-check renewal credit；

R45 Alice–Bob natural-support SDRA；

R46 exact HMRV dynamics/estimand/critic/read；

R47 exact spectral view/basis/score/reward pair；

duration head、duration-category action、KEEP/lifetime reward、switch penalty；

task-specific novelty、distance、contact、phase、progress、success或potential shaping；

通过seed、预算、model size、threshold、reward、environment或best-checkpoint进行任何结果救援。

最终单一决定
	​

R47 = VALID_FAIL;
没有 branch-changing M0 defect；
exact R47 line及reward-on pair永久退休；
自然低维repeatability存在，但四模态null significance、
long-lag coherence、natural support、skill occupancy
和between/within SNR均未共同成立；
fixed-N探索仅保留最后一个未审计边：
R48-SBRS-G0，skill SET的recurrent-state boundary；
R48有效失败后，fixed-N skill/lifetime探索永久停止，
不通过任何调参、扩种子、改奖励或换环境救援。
	​

	​
