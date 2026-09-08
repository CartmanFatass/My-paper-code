# UCOPE after B03 — P61 Convergence question preparation

**Recommend that Convergence retain one bounded action-conditioned opening-duration
B, compared with retaining no successor to the tested opening family.** This is
a direction-local recommendation awaiting the proper node, not a selected card,
new scientific allocation, family disposition or Portfolio action.

## 1. Assignment and evidence checked

[P61](../../portfolio/handoffs/2026-09-08-p61-ucope-post-b03-direction-choice.md),
commit`392f3724777d6b19cd9365e978cb47d521dc6b55`, authorizes one scoped question
after completed P57. The designated checkout remains
`C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`,
branch`codex/ucope`, initially clean at
`ae7f9afd393a492c2cc7092c8552e9f3c1bfcdc5`. Accepted scientific source is
`70900ac7e7aa3a85b4f4ad6a2a8031ccb346fd44`. P61 and the currently applicable
AGENTS/engineering-scope documents are synchronized from that existing P61
commit as unchanged inputs; this preparation makes no governance or source edit.

I read the current Portfolio row, DIRECTION's current B03 and prior B02/P24
positions, [B03 intake §§2–3,5–6](UCOPE_UAV_MOTION_PREFIX_B03_P57_INTAKE_20260908.md),
[B02 intake §§2–3](UCOPE_UAV_MOTION_PREFIX_B02_P47_INTAKE_20260908.md),
the original P21/P24 result meanings and [family intake §§3–4](UCOPE_UAV_INTERFACE_CONVERGENCE_INTAKE_20260907.md).
The concrete question required reading only `policy.py::sample/joint_terms/arm_copy`,
`learner.py::collect_episode/update/returns_to_go`, the existing configuration and
accepted B03 counts/exposure. No model, environment, checkpoint replay or test was run.

Rule applied verbatim, evidence-spec §11.8.2: “Absence of improvement may also
motivate a specifically justified new B change. A positive result is neither a
universal prerequisite for follow-up nor an entitlement to unlimited further compute.”
Sections11.8.1,11.8.6 and11.9 control the question and its proposed burden;
§11.4 permits only the stated integrity, nonzero learner, resource and exposure
launch conditions. P61 itself requests the direction decision; Pro consultation
is not presented as a universal B prerequisite.

## 2. What survives from the results

| Separate study | Independent matched training pairs | Original T−G reading | Material support and contradiction |
| --- | ---: | --- | --- |
| P21 joint objective |2|+0.0152174206, UP|Both positive endpoints+0.0067140322/+0.0237208090; both G−H positive; above-MEI margin smaller than conditional SE.|
| P24 joint-objective continuation |2|−0.0035067780, WITHIN|+0.0433518665/−0.0503654225;6901 G−H−0.0282038164 and6902 T−H−0.0332644846.|
| B02 common agent-compound clipping |2|−0.026701655118179134, DOWN|T−G−0.0472671044/−0.0061362058; T−H−0.0224883084/−0.0243921875; G−H changes sign.|
| B03 common zero explicit entropy bonus |1|−0.010093085146628955, DOWN|Conditional SE0.008506138301283968; T−H+0.03747487717099439 and G−H+0.04756796231762334;17 positive/15 negative primary evaluation episodes.|

B03 crosses its negative boundary by only0.0000930851466. Its exact declared
reading remains DOWN; n=1 cannot estimate training-population uncertainty or
reliably separate the effect from that boundary. Its positive hover contrasts
establish a narrow competent-feedback comparison on one fitted sample, not tuned
generic control. B02's two T−hover losses remain particularly important contrary
evidence. Original P21 support and P24 harm are not erased or repooled. Different
masters/objectives establish no entropy, clipping or conditioning causality.

Headroom on this host remains absent: fixed hover is untuned and no upper
reference has been established. Larger displacement, changed local-user entries,
duration activation or a parameter change is not native value. The candidate
must still beat the same-information ordinary controller on complete native J.

## 3. Source fact and question-driven literature

The current T sampler first draws each UAV's velocity latent `u`, then evaluates
`actor.duration(recurrent[i])` without that sampled velocity. `joint_terms`
likewise recomputes the duration density from recurrent history alone. Thus its
opening law is `pi(v|h) pi(d|h)`: the duration can respond to local history and
the learned mean intention, but not to the actual noisy command it will repeat.
This is a source fact, not a defect, a measured decision error or the cause of
B02/B03's signs. B03's already logged latent std stays near1; that observation
makes actual sampled-command conditioning a concrete question without proving
that any particular draw was harmful.

I asked the local libraries whether action repetition/termination research
provides a specific, small alternative to repeating another common-learning
amendment. Current My-lib coverage again reports only two synthetic fixtures,
excluded from science. The real Inst-sci catalog has190 records; a bounded
termination/action-repetition/temporal-abstraction query returned3 candidates:
`MARL-0449`, `MARL-0543`, `VS-0005`. The query receipt is in
`temp/directions/ucope/exp/uav-motion-prefix-p61-preparation/local-catalog-query.json`.
This is searched-snapshot coverage, not a novelty census or a fixed division of
scientific purpose between libraries.

The decisive source is **Lee, Park, Tang and Oh, AAAI2024, Learning
Uncertainty-Aware Temporally-Extended Actions (UTE)**. Verified local source
`C:/Projects/Inst-sci/papers/MyLib/json/VS-0005.json`, p3 element144, defines a
decomposed extension policy conditioned on both state and the selected action.
Pages1–2, elements63/69, retain the tradeoff: repeating a poor action can hurt,
while persistence can support exploration. The metadata lacks an official URL;
the [official AAAI record](https://ojs.aaai.org/index.php/AAAI/article/view/29241)
verifies the identity and DOI`10.1609/aaai.v38i12.29241`. Its evidence concerns
Gridworld/Atari with Q-learning and uncertainty ensembles. It does not show a
UAV/MARL gain or validate our PPO transplant. We take only the action-conditioned
extension idea, not its ensemble, search, novelty or benchmark conclusion.

The other inspected source, **Jung et al., ICML2025, Agent-Centric Actor-Critic
for Asynchronous MARL**, local`MARL-0449.json` p1 elements352/382 and
[official record](https://proceedings.mlr.press/v267/jung25a.html), discusses
misaligned macro-action experience. It reinforces preserving true decision
ownership; it supplies no reason to install its encoders, attention or GAE here.
Current full-episode undiscounted return-to-go and primitive critic/observation
rows stay intact. The third catalog candidate was not used as substantive support.

**What this changes:** propose conditioning the existing one opening duration
on the UAV's already sampled command. An interruptible option would change the
accepted event boundary and is not needed for this question. No residual learner,
target normalization, extra entropy/clipping sweep or later option is proposed.

## 4. Concrete alternative to ending the tested family

The proposed question is: can one action-conditioned opening-duration package
improve full native return over the unchanged same-information recurrent PPO
generic at the current real training budget? Minimum evidence class is B/EXPLORE.
Binding MARL structure: **temporal abstraction**, arising here from partial
observation in a fixed jointly moving team and other agents' co-adapting policies.
The proposed action-condition is an owned command, not privileged information.

At t0, each T UAV samples its velocity exactly as now, then its duration1/4 from
its recurrent feature and its actual normalized command `tanh(u)`. A fixed
`67→32→2` tanh head is the concrete proposal; its final layer starts at zero so
initial durations remain uniform. The existing common actor/critic initialization,
velocity streams and separate fitted-arm optimizers remain matched as declared.
All observation, hold, expiry and primitive reward paths are unchanged: d4 holds
through t3, memory still advances, normal feedback resumes by t4, and no later
option opens. The head is evaluated only at actual opening-duration rows.

The action-credit path is opening local observation/history → sampled owned
velocity → its conditional duration → real position/channel/service and later
local observations → ordinary recurrent feedback → complete native rewards →
the same agent-compound PPO update. The compound log density becomes
`log pi(v|h) + log pi(d|h,v)` on the opening row. Recomputing it uses the stored
detached action, not a newly sampled or mean command. Held velocities remain
uncredited as new actions. No intermediate acquisition score or displacement
replaces `J=sum_t sum_i reward_i,t /256`.

G retains the same free local information, recurrent memory, continuous velocity
choices at every step, native objective and current agent-compound clipping/
zero explicit entropy coefficient. It may exploit geometry and persistence
itself. The extra T head makes this a package comparison, not a conditioning-
causal or capacity-matched result. The contrary result is that G still matches
or wins because feedback already uses the opportunity, extra conditioning does
not learn useful durations, or its small extra capacity/optimization is unhelpful.

Prospective budget, **only if the node selects this object**: one fresh matched
pair, candidate master7201, with512 training episodes per learned arm and32
final evaluation episodes for T/G/H. The proposed primary is the mean of32
paired final `J_T−J_G` values, n=1 training pair. Preserve all three means,
T−G/T−H/G−H and conditional paired-episode SE; no training-population SD/CI.
No third learned arm is required for the stated package claim. One pair does
not identify conditioning causality or imply stable superiority.

Proposed absolute MEI remains0.01, one percentage point on the selected native
service scale. Above it would support a bounded package follow-up; inside±0.01
would show no gain at that scale; below−0.01 would be adverse for this new
task/package/budget. All signs return for intake, with no automatic second
pair. The prospective card would freeze those branches and predictions before
implementation/output. It is not frozen by this consultation.

## 5. Decision value, dominant work and exposure

[Machine-generated facts](UCOPE_POST_B03_CONVERGENCE_FACTS_20260908.json)
calculate2×512×256 training and3×32×256 final evaluation =**286720 native
team steps**,2048 Adam calls,512 two-episode rollouts,1120 explicit episodes/
resets and1600 existing frames. There is no nested candidate, trajectory,
ensemble or optimizer sweep. Candidate7201 was absent from the bounded current
UCOPE documentation/source search before proposal; that is not a global census.

The concrete head replaces130 parameters with2242, adding2112 to T for a
total68553; G remains66311. There are15680 named opening-head forward rows:
2560 training samples,2560 stored-density evaluations,10240 four-epoch
recomputations, and160+160 final sample/density evaluations. Its two dense
maps entail34,621,440 forward multiply-adds over those rows, with backward and
Adam work additionally required. These are algorithm operations, not measured
seconds. Evaluating the new head over every masked primitive row would add
unnecessary work and is not the proposed implementation.

Per-arm cost law retains initialization +131072 environment/actor steps
+1024 updates +8192 final steps + publication; G also carries8192 hover
steps. B03's observed143.6449222s T,139.3128413s G including hover and283.51s
whole invocation are the same-loop reference. New head/backward/optimizer time
is unknown. Proposed limits are1800s per arm and3600s for the complete chain,
not an increased cap or a promised runtime. The portable route remains
remote-first, CPU FP32, one Torch thread, exact committed source and fresh
actual-node memory admission. This consultation launches nothing.

Added validation would be the one affected directory suite at most300s and
independent conditional-density/held-action/native-primary review. No separate
smoke, replay, profiling, headroom run, pilot or exact diagnostic is requested.
Existing research source/runner limits remain2000/600 lines. Engineering
scope§4: **none**, for both this preparation and the proposed ordinary head.
Preparation has no new code-budget breach; prior timing/cwd failures remain
their original records and are not repeated.

Ending the tested opening family needs zero further scientific invocation and
is the strongest economical alternative. I narrowly prefer one real B because
the sampled-action dependency is a concrete untested change inside the existing
event boundary, the source and verified literature identify it, and its only
decision is complete native performance against legal feedback. This is not a
claim that poor draws caused prior losses. B02/P24 harm and G's B03 competence
make no successor a serious option. No exact upper or complete causal diagnosis
is necessary to decide between these options, and no unchanged seed is requested.

Machine-generated consultation line:

`P61_consultation: new_models=0; new_training_pairs=0; new_environment_episodes=0; new_native_steps=0; new_optimizer_steps=0; new_evaluation_episodes=0; new_replay_calls=0; new_profiling_calls=0; new_scientific_invocations=0.`

The facts also retain the accepted B03 real learner/exposure line, actual positive
parameter counts and lr0.0003. No nominal zero-learner diagnostic substitutes
for that history or pretends to be a cheap implementation experiment.

## 6. Decisions this preparation produces and return

1. **Object / question selection:** options (a) send this one bounded comparison
   of action-conditioned B versus no successor; (b) send another unchanged B03
   seed/learning sweep; (c) impose exact diagnosis before a choice. Recommendation
   and selected **(a)**. **Owner-delegated decision (unattended, 2026-09-03
   instruction): (a).** P61 already authorizes the one Convergence question.
2. **Direction / pending:** options (a) CONTINUE the concrete one-pair package
   exploration above; (b) END only the tested opening family and retain no
   successor. DM recommends **(a)**, narrowly, and records the contrary evidence.
   Neither is executed locally. The complete conforming Convergence answer
   decides this tier. If the node instead selects a recast, it must name the
   changed native action/information/credit path, smallest sufficient evidence
   and explicit complete budget; a generic wish for more diagnosis is not a card.

Owner-console recommendation: 建议由Convergence选择一对新的B：让每架UAV在开场根据刚采样的自有速度选择持续1或4步，再与同信息逐步反馈控制比较完整原生回报。只提这一对，不重复B03或扫熵/裁剪；保留结束该已测家族且无后继这一有力选项。当前只是提交方向建议，尚未作出Pro决定或分配实验。

At this clean boundary, main owner reviews returned[] and no relevant audit
owner override was found. No new card/result is published, so there is no new
prediction to score or Chinese valid-result brief. The close comparison between
the pending direction options is highlighted by
[owner item20260908-ucope-003](../../portfolio/owner/inbox/2026-09-08/20260908-ucope-003.json);
it does not wait for an owner reply or invent a formed Pro decision.

Publish one fixed GitHub TASK on the existing direction branch and substantive
Issue11, bind its full SHA, then give Root the exact committed HANDOFF and native
return target. The current registry binding is the post-cutover UCOPE node
`6a9c6b1c-1c34-83e8-8ebc-dee64b334240`; the old`6a9642a3-cdd0-83e8-9334-21262386768c`
is explicitly quarantined. The recorded2026-09-05 replacement and2026-09-07
6 Pro/Latest/Pro,5-of-5 observation support reuse; Transport makes its fresh
pre-Send verification. There is no new-conversation selection or reset request.
Root dispatches once to the existing Transport and returns the complete matching
immutable response to this DM. Source/parent/operator routing remains in HANDOFF.

Then park this task at its clean publication boundary. A conforming selected B
continues under P61 through prospective card/full specification, the same CM,
accepted source, selected bounded execution and all-outcome intake. No routine
second Portfolio implementation vote is inserted. A concrete specification
conflict returns to the same node before its affected requirement is executed;
no formed decision or retained successor means return the exhausted route.
DIRECTION's accepted scientific conclusions and the formal UAV-entry count
remain unchanged during preparation.

## 7. Fixed publication and clean return boundary

The scientific input is committed/pushed at
`f3ac3991ff30a603adc111cead2e3bd38f6783ca`. The complete fixed
[TASK](pro_packets/20260908_post_b03_convergence/TASK.md) is committed/pushed at
`6307d2fd9f3911ef1dd7d3b7c7c154bfaa766fa8`; its immutable
[GitHub link](https://github.com/CartmanFatass/My-paper-code/blob/6307d2fd9f3911ef1dd7d3b7c7c154bfaa766fa8/docs/research/candidates/ucope/pro_packets/20260908_post_b03_convergence/TASK.md)
is bound by the Prompt Author renderer in
[HANDOFF.json](pro_packets/20260908_post_b03_convergence/HANDOFF.json).
Request`2026-09-08-ucope-post-b03-convergence-01` is **READY_TO_DISPATCH**;
DM has made no Transport dispatch or provider Send.

The [publication readback](pro_packets/20260908_post_b03_convergence/archive/PUBLICATION_READBACK.json)
records a direct GitHub read of the TASK at its full SHA, equality to the
committed local bytes, and the existing delivery branch/Issue. The TASK
SHA-256 is`527a813bec83f7a046055b3a54712e8ff2378b96074d006be1b7d27ebbefe72b`.
The [Issue publication snapshot](pro_packets/20260908_post_b03_convergence/archive/ISSUE_PUBLICATION_READBACK.json)
retains the current P61 scope and fixed link; the prior body/comment remain in
the earlier input snapshot. The [binding readback](pro_packets/20260908_post_b03_convergence/archive/BINDING_READBACK.json)
retains the current non-retired node and the earlier replacement's provenance.
Fresh browser verification and the one exact Send remain Transport work.

Pro may add only this round's`archive/RESPONSE.md` on the current descendant
HEAD of`codex/ucope` and its delivery-link comment on Issue11. Root receives
the complete committed HANDOFF, fixed TASK URL and native return target
`/root/dm_ucope_p47_resume`, then dispatches via the configured existing
Transport without model overrides. Read the eventual full response directly
from its immutable commit; a chat receipt alone is not the direction decision.
All preparation work is committed at return, no run is active, and no
scientific successor has been selected locally.
