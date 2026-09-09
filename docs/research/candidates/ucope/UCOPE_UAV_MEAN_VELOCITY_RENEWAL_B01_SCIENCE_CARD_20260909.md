Claim under test: fixed short renewal retains an above-MEI native-return gain over legal feedback when both learned velocity policies execute tanh(mu), on one fresh matched training instance.
Binding MARL structure: (b) temporal abstraction or termination; five partially observed, co-adapting UAVs act from private recurrent histories at different renewal opportunities.

# UCOPE UAV mean-velocity renewal B01 — science card, 2026-09-09

## 1. Question and authority

**UCOPE-UAV-MEAN-VELOCITY-RENEWAL-B01**, selector **renewal_mean_velocity_b01**,
**B/EXPLORE**, one fresh matched training instance **8401**. Root's
**2026-09-09 P85 allocation** selects [P84 intake §9(a)](UCOPE_UAV_SHORT_FIXED_RENEWAL_B03_P84_INTAKE_20260909.md#9-decisions-this-completed-intake-produces):
unchanged F/G training followed by **F_mean, G_mean, F_sampled, G_sampled and H**
on those same new fits. **F_mean−G_mean** is prospectively primary. This is
outcome-informed execution-policy exploration within the accepted short-renewal
mechanism. Both modes' hover contrasts and within-fit mode differences remain.
No best-mode, checkpoint or post-outcome primary selection is allowed.

P84's sampled F−G +0.06439366516106426 is UP, while F−H
−0.029184443306665326 and G−H −0.09357810846772958 are losses. P83 is UP
with F−H gain/G−H loss; P82 remains WITHIN. These facts motivate a different
execution measurement without diagnosing sampling as their cause. The chosen
fresh B includes real learning; an old-checkpoint A is neither selected nor a
prerequisite, and no P84 reevaluation or fourth unchanged history is allocated.

## 2. Changed execution and preserved training

Preserve accepted source **6384613b4f8c4204a154427a61ed8012e97af917** and
[P84 card §2](UCOPE_UAV_SHORT_FIXED_RENEWAL_B03_SCIENCE_CARD_20260909.md#2-preserved-package-and-comparison).
F physically holds a velocity for **1 or 2 primitive steps**, half probability
each, drawing duration at its own expiry. Labels remain **0/1** for likelihood,
PPO credit and selected-label horizon censoring. Preserve expiry, suppression,
held action, literal d2/d4 accounting and **remaining/4** actor/critic features.
The **entire initial 2242-parameter F duration head** is fixed, hidden layer
included, final weights/bias zero. F/G velocity actors and critics train with
the unchanged stochastic Gaussian velocity rule. Each has **66311 trainable
parameters**; total F 68553/G 66311. G can decide every primitive step; H is
untuned zero velocity, with no learner or action draws.

In **mean** evaluation only, set the active unsquashed velocity to **u=mu**
and send **tanh(mu)**; consume **zero Gaussian velocity draws**. This is not
E[tanh(u)] for a Gaussian u. In **sampled** evaluation retain
u=mu+exp(clamp(log_std,−5,2))*epsilon and send tanh(u). F draws its fixed
categorical duration in **both** modes, so F_mean is still stochastic. G has
no duration head/draws in either mode. H has no action draws. Evaluation
likelihood bookkeeping, if retained, is not a new training or density claim.

Every evaluation episode starts with the common reset seed, a new zero recurrent
state and fresh hold/previous-action state. Each mode uses the same final fitted
actor/critic parameters and buffers; evaluation must not mutate them or the
optimizer, feed data into training, or select a checkpoint. Report the two
fits' evaluation parameter nonmutation using the existing snapshot/exposure
path or an equally small direct measurement; review any buffer/state path.
Do not share mutable action generators between modes or episodes.

Keep fixed-five membership, 256 primitive steps, native reward, free private
observation and recurrent update every step, compound clipping, primitive
credit, all-row denominator, zero entropy, gamma 1, Adam/normalization and final
checkpoint selection. No join/leave/replacement, reward clock, information or
discount change. Shared VSPC1 value-moments hook stays None. Old selectors keep
their own execution, supports and primary identity, including P80 F−H.

Private observation → owner's recurrent history → mean or sampled velocity at
its opportunity → held motion and later service/local information → masked
training exposure and partner co-adaptation → native return is the measured
path. Within-fit execution differences do not isolate service versus information
value or remove partner interaction. Reuse G/H because observation, action,
information and budget match; H is no tuned upper. Reuse verified
[P84 intake §8 grounding](UCOPE_UAV_SHORT_FIXED_RENEWAL_B03_P84_INTAKE_20260909.md#8-bounded-interpretation-grounding-and-predictions):
the documented mean-action evaluation option motivates measurement, not an
assumed benefit, mandatory norm or claim that P84 was defective.

## 3. Binding, streams, exposure and independent unit

Master **8401**, b=**840100000**. Common actor/critic initialization b+11;
F initial duration head b+12. G private training velocity/duration b+21/b+22;
F b+31/b+32. Common training resets b+1000+e, e=0..511. Common final reset
population **b+2000+e, e=0..31**, for all five outcomes. G_sampled private
velocity/duration b+3000+e/b+4000+e, the latter unused; F_sampled private
velocity/duration b+5000+e/b+6000+e. Each F_mean episode starts a **separate**
duration generator at b+6000+e too; it never shares the sampled generator's
mutable state. This prospectively couples fixed-duration draws across F modes.
F_mean/G_mean consume no velocity draws, G_mean no duration draws, H no action
draws. Common resets and duration seeds do not force identical trajectories.
Scoped master/base and exact object/selector searches found no prior UCOPE match.

Serial order: F training → final F checkpoint → F_sampled 32 → F_mean 32;
G training → final G checkpoint → G_sampled 32 → G_mean 32 → H 32. Private
training streams ensure F evaluation cannot change G fitting randomness.
Two **512-episode fits**, 131072 training steps, 256 two-episode rollouts and
1024 Adam calls each; four epochs per rollout, lr 0.0003. Final **160 episodes**
comprise five 32-episode modes from **two fits**, not five training replicates.
One new matched training instance is the independent unit; conditional final
episodes cannot estimate training-population uncertainty.

[Machine-generated facts](UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_PROSPECTIVE_FACTS_20260909.json):
`matched_training_instances=1; fitted_arms=2; native_steps=303104;
optimizer_steps=2048; final_eval_episodes=160; lr=0.0003; F_parameters=68553;
G_parameters=66311; F_frozen_duration_parameters=2242; trainable_parameters=132622`.
Total 512 rollouts, 1184 explicit/2 constructor resets and 3200 existing
diagnostic frames. Preparation exposure zero; no tuning or checkpoint selection.

## 4. Cost, node and one accepted execution

Algorithm work is **2×512×256 + 5×32×256 = 303104** native steps and
**2×256×4 = 2048** Adam calls. F head work is **6×training renewals +
2×renewals in each F final mode**, **2048000–4096000 rows**, or
**4521984000–9043968000 dense MACs** at 2208 per row. No nested candidate or
trajectory search. The extra two modes are question-relevant measurement work;
focused semantic verification is separate.

Complete F arm: initialization + 131072 training steps + 1024 updates +
16384 final steps + publication. Complete G arm: the same training/update work,
16384 policy final steps plus 8192 H steps and final publication. Startup is
charged F; H/final publication G. Caps **1800 s complete arm / 3600 s complete
invocation**, through publication and exit. P84 measured F
**163.87369038298493 s**, G including H **133.33607813803246 s**, outer
**313.90 s**. New native work is 1.0571428571428572 times P84, F head-bound
work 1.0204081632653061 times; no step/time proportionality is assumed. Future
wall remains unknown, no known term projects over cap, and no cost probe follows.

Use configured remote_first/hmasd-wsl-node, CPU FP32/one Torch thread, committed
and pushed exact source in a detached exact-SHA worktree under agent-task. Host
identity is not part of the estimand. Fresh actual-node canonical admission
must show physical/effective availability ≥4 GiB, joined by `&&` immediately
before the runner and any scientific roots/RNG/models. Original CM alone
observes and collects the accepted invocation.

## 5. Primary, all-outcome reading and predictions

J=sum_t sum(info['rewards_dict'].values())/256. Primary **Delta_mean =
mean_e(F_mean−G_mean)** over the 32 paired final reset episodes. Preserve all
160 J values and eight named contrasts: **F_mean−G_mean**, F_sampled−G_sampled,
F_mean−H, G_mean−H, F_sampled−H, G_sampled−H, F_mean−F_sampled and
G_mean−G_sampled. Publish paired vectors, means and conditional evaluation SE
sample_sd(paired differences)/sqrt(32), with episode IDs and mode identity.
Primary completeness uses F_mean/G_mean; full allocation requires all five
outcomes. Missing modes limit their dependent comparisons under §11.8.7.

**MEI absolute 0.01**: a 0.01 gain in this native task scale is the minimum
point change worth another bounded investment in mean-velocity renewal, while
keeping the local magnitude readable beside prior results. This is a new
prospective choice, not a repository-wide threshold. **Tuned same-information
headroom absent**; no upper or baseline-tuning prerequisite.

| New complete primary | B-level reading |
| --- | --- |
| UP: Delta_mean > +0.01 | Preliminary favorable mean-velocity short-renewal package evidence on this fresh fit; no stable advantage across training histories. |
| WITHIN: −0.01 ≤ Delta_mean ≤ +0.01 | No demonstrated point gain at the selected scale on this fresh fit; no equivalence conclusion. |
| DOWN: Delta_mean < −0.01 | Adverse mean-velocity short-renewal package evidence on this fresh fit; hover gains or sampled-mode results do not rescue this primary. |

Apply unrounded values and report distance. All hover/mode contrasts stay
separate, including opposite signs. Earlier primaries and losses stay visible;
no pooled primary, cross-instance mean/SD, training-population interval or
best-mode score. The approved run-summary tool may describe mode-labelled
endpoints for 8401 with the shared fit explicit; H is not a training replicate.

Prospective predictions: **P(Delta_mean>0.01)=0.50;
P(F_mean−H>0.01)=0.55; P(F_mean−F_sampled>0.01)=0.60;
P(G_mean−G_sampled>0.01)=0.60**. A documented alternative and current hover
losses give weak motivation to test mean velocities, not evidence of their
effect; the uncertainty and interaction change keep forecasts modest. Record
every event and Brier score. Owner prediction **not taken (unattended)**.

Above-MEI adds one favorable mean-velocity fit; inside-MEI shows no selected-
scale point gain; opposite sign counts against the chosen package. Each result
is read with all hover and execution-mode observations before recommending a
next discriminator. Every outcome ends P85. No stable superiority/harm,
equivalence, sampling-cause, causal-shortening, learned-duration, tuned-competence
or deployment conclusion follows.

## 6. Engineering scope and stop

Engineering scope §4: **none**. The bounded change adds explicit evaluation
velocity choice and mode-resolved scientific output to the existing path;
parameter nonmutation is a small measurement of scientific exposure, not a
new guard or telemetry framework. Source ≤2000 new lines, runner ≤600,
focused checks **≤300 s**. Independent review covers changed evaluation/RNG/
reset/nonmutation and paired primary publication; reuse unchanged credible
credit, support, freeze and shared-default checks.

One accepted scientific submission only. Stop on admission refusal, cap,
nonfinite learning or a defect threatening reward/information/credit/training/
comparison/primary; preserve independently trustworthy facts under §11.8.7.
Missing optional resources are resources_unmeasured. No retry/resume/replacement,
pilot/tuning, extra evaluation, second instance, T restoration, support change,
Pro Send or automatic successor. A concrete meaning/scope conflict returns
before dependent execution. Ordinary in-scope repairs remain with the same CM.
Root owns integration, reclamation and any later allocation.

## 7. Binding acceptance and complete CM batch

Real 8401 cites this card §5; any reduced engineering fixture is 9001 and
cites §7, with no real native smoke. Check the actual new CLI/config path,
unchanged stochastic fitting, mean u=mu only during selected evaluation,
no Gaussian draws in mean mode, stochastic private fixed-duration draws,
per-episode recurrence/hold reset, final parameter/buffer nonmutation, and all
five clearly labelled outcomes/eight paired contrasts. Primary selection must
explicitly name **F_mean_minus_G_mean**, independent of sampled/hover signs.
Preserve historical output/selector behavior at affected boundaries. Independent
review checks the actual changed semantics, not merely a completion assertion.

[P85 intake §2](UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_INTAKE_20260909.md#2-five-item-cm-assignment)
assigns the original CM the full source/review/check/payload, one committed
remote invocation, sole observation and technical collection batch in the same
codex/ucope checkout. No intermediate approval handshake.

## 8. Observed completion — 2026-09-09 P85

Frozen §§1–7 remain unchanged. One accepted 8401 execution is **valid complete
WITHIN**: F_mean−G_mean **−0.008350131013904307**, conditional SE
**0.006736648533933545**, **0.0016498689860956935 inside −0.01**.
There is no demonstrated point gain at the selected scale and no equivalence
conclusion. Sampled F−G remains secondary at **−0.02234539578242959**.

All four hover means are negative: F_mean−H **−0.0900967755406669**,
G_mean−H **−0.0817466445267626**, F_sampled−H **−0.04753797201899047**,
G_sampled−H **−0.025192576236560876**. Mean−sampled is
**−0.04255880352167644** for F and **−0.05655406829020172** for G.
Mean extraction did not rescue native return on these fits. Every P82/P83/P84
primary and earlier loss remains unchanged; no pooled or stable claim follows.

Full **303104 native steps / 2048 Adam / 160 final episodes** completed in
**331.58 s**, with fixed F head, real actor/critic learning and zero evaluation
parameter displacement. Eight contrasts are complete. No cap or scope §5
budget breach; aggregate CPU resources_unmeasured. All four forecast gain
events failed, mean Brier **0.318125**; owner prediction not taken.

See [E0 evidence](UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_RESULT_EVIDENCE_20260909.md),
[summary](UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_RESULT_SUMMARY_20260909.json)
and [DM intake §§7–10](UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_INTAKE_20260909.md#7-dm-scientific-intake-against-the-card).
P85 ends. Recommend one separately allocated same-five-mode fresh learning
history to observe recurrence of the full pattern, with the same primary and
all outcomes retained. No next card/master/source/allowance, extra evaluation,
automatic successor or Pro Send is created. Root owns later allocation,
integration and remote reclamation. Automatic approval review blocked deletion
of the completed local test scratch; CM retains that cleanup responsibility.
Root allocates no next pair at this boundary. A separately authorized
consultation-only Convergence question will compare the fresh-pair recommendation
with no further empirical work/ending this package and a concrete training
change; no next empirical card/master or child Send is authorized.
