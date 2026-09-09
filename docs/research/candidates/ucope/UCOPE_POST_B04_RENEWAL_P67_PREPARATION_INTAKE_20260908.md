# UCOPE after B04 — P67 renewal-at-expiry question

**Recommend one direction-tier Convergence question:** is a bounded native-return
comparison of renewable, action-conditioned commitments worth doing after the
completed opening-only tests, or should there be no ready successor? The DM
narrowly favors the concrete comparison below. This preparation selects the
question; it does not open a family, freeze a card or allocate an experiment.

## 1. Current assignment and preserved evidence

[P67](../../portfolio/handoffs/2026-09-08-research-resume.md), published on main
at `6d0c12153`, records the owner's “阅读handoff 继续开启科研” instruction.
It lifts the global safe pause and asks this DM to identify an appropriate
next decision after B04. The old P61 allocation remains exhausted. The
designated checkout is `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`,
branch `codex/ucope`, initially tracked-clean at
`9745d270010a8e100cfed0d1ee9533878cf70190`. Current AGENTS and ROOT_OPERATIONS
assign Portfolio and execution to Root; this DM returns directly to Root.
The old pause text in the completed P61 intake is dated provenance, not a
current refusal to perform P67. Knowledge integration remains unimplemented
and is not a prerequisite. No governance or scientific source changes here.

Read P67's UCOPE row, the current Portfolio row, DIRECTION's current B04
position and [B04 intake §§2–3,5–6](UCOPE_UAV_MOTION_PREFIX_B04_P61_INTAKE_20260908.md).
The accepted scientific surface still matches
`7693b7af6b7d89cdaa028659d606a37dee9eb68e`. The focused new source reading is
`environment.py::HoldState`, `learner.py::collect_episode` and its primitive
return/credit path, `policy.py::sample/joint_terms`, and `study.py::Config`.
No imports of the learner/environment, checkpoint inference or test execution
were needed. Prior collection and arithmetic are reused, not repeated.

The B04 facts remain **WITHIN**, T−G **−0.003948225944122139**, conditional
evaluation SE **0.010191826216031805**, with G−H **+0.0238187196536019** and
T−H **+0.019870493709479763**. There is **one independent training pair**;
32 final episodes are not 32 trained policies. Both positive hover contrasts
are sampled means against an untuned reference, not tuned competence or
headroom. Neither WITHIN nor its less negative point than B03 establishes
equivalence, a conditioning benefit or a reliable population comparison.

Keep the separate history: original P21 UP mean +0.0152174206; P24 WITHIN
mean −0.0035067780 with a harmful 6902 endpoint; B02 DOWN mean
−0.026701655118179134 with both T−H endpoints negative; B03's one-pair DOWN
−0.010093085146628955 just below its boundary despite positive G−H/T−H.
No pooling, best-result selection or new polarity is applied. B04 completed
286720 native steps and 2048 Adam calls in 277.51s within its caps. Its head
updated and selected 73 four-step holds among 160 final openings; those are
operational exposure facts, not demonstrated useful duration selection.

Rule applied verbatim, evidence-spec §11.8.2:

> Absence of improvement may also motivate a specifically justified new B change. A positive result is neither a universal prerequisite for follow-up nor an entitlement to unlimited further compute.

Sections 11.8.1, 11.8.6 and 11.9 apply to choosing this question; §11.4's
integrity, real-learner, resource and exposure conditions remain the only B
launch conditions. The actual change in the accepted opening-only event
boundary is why direction authority is requested. Pro is not a generic B gate.

## 2. The untested event change and strongest null

The existing duration mask and `sample` opening flag both use `t == 0`.
`HoldState.decide` uses the selected duration only then and assigns one step
to later active agents. Each episode starts the private recurrent hidden
state at zero. Therefore the B04 duration policy sees reset-time information;
it never chooses a new duration from the evolved local history later in that
episode. Later ordinary feedback does use that history. These are source
facts, not bugs or an explanation for the old negative means.

The proposed event is **each UAV's own commitment expiry**. At every expiry,
including t0, that UAV first samples a new velocity and then duration 1 or 4
conditioned on its current private recurrent feature and that actual owned
command. Other UAVs may still be holding their commands. Their different
expiry times require no common decision barrier or additional environment
step. This gives duration selection access to already legal, evolved history
of movement, local service opportunities and other agents' effects. It changes
where the mechanism operates across the task; it does not merely ask the same
opening policy to train longer or repeat master 7201.

The causal path to test is: own expiry while the fixed team continues moving
→ the owning UAV's current local observation/private history and already
sampled command → selected physical persistence versus early feedback
→ positions, channels, service and subsequent local observations
→ subsequent owned decisions and full native rewards → actual masked PPO
learning → final complete native team return. All five entity identities and
private recurrent histories persist through the episode; there is no join,
leave, slot replacement, information purchase, new sensor or charged observation.

**Strongest null:** the ordinary feedback learner already uses the same free
history and can repeat any velocity when useful. Repeated commitment could
reduce adaptation to moving teammates and amplify a poor command. More
duration decisions, successful timer operation or longer motion would not
refute that null. Any gain would be a package performance observation, with
changed decision/optimization exposure, persistence and partner co-adaptation
still intertwined. No pure-information or isolated renewal-causal claim is sought.

## 3. Question-driven local-library check

The question was whether successive option expiry supplies a concrete event
change beyond B04, and which asynchronous observation/credit assumptions
actually apply. The current My-lib CLI coverage returns `synthetic-core`,
two papers/two mechanisms; those fixtures are excluded. This is the verified
published CLI coverage, not a claim that every file in that project is empty.
No unified real-corpus index is claimed or built.

The current Inst-sci catalog has 190 records. Searching titles, abstracts,
algorithm names, settings and mechanism terms for temporal extension,
macro-actions, repetition, asynchronous decisions and termination returned
eight candidates. Only the following two are used substantively; the other
lexical matches are not promoted from metadata to evidence. The
[computed facts](UCOPE_POST_B04_RENEWAL_P67_FACTS_20260908.json) retain the
query, candidate IDs, metadata warnings and exact source pointers. Coverage
is the searched snapshot, not a novelty census or a division of libraries by name.

- **UTE, Lee et al., AAAI 2024.** In local
  `C:/Projects/Inst-sci/papers/MyLib/json/VS-0005.json`, p3 elements 95–96
  define action repetition until its duration terminates; element 144 puts
  action before its conditional extension policy “at every time an option
  initiates”. This supports the proposed initiation/renewal distinction.
  Its single-agent Q-learning and uncertainty ensembles, Gridworld/Atari
  results and counterfactual option-value updates do not establish a PPO,
  MARL or UAV benefit. We adopt none of its ensemble, extra transition reuse
  or search. The metadata's missing official URL/DOI warning is preserved;
  the [official identity](https://ojs.aaai.org/index.php/AAAI/article/view/29241)
  was verified in P61 and is reused.
- **ACAC, Jung et al., ICML 2025.** In local
  `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0449.json`, p1 element 382,
  p2 element 388 and p3 element 410 describe each agent choosing again when
  its macro-action finishes: “This cycle continues until the episode concludes.”
  The [official record](https://proceedings.mlr.press/v267/jung25a.html) is
  verified in the local metadata and prior P61 retrieval. Its p2 element 389
  and p3 elements 415–416 concern missing macro-observations and misleading
  padding. Our actors and critic still receive fresh primitive observations;
  this proposal does not inherit that missing-observation problem or adopt
  ACAC's encoders, attention or modified GAE.

**What the verified evidence changes:** the surviving question is repeated
own-expiry selection using existing private history, not another opening-head
or common-loss amendment. The literature also narrows implementation: retain
true owner/decision masks and all primitive observations and returns. It
supplies no empirical UCOPE gain and no reason to install a new critic framework.

## 4. Concrete minimal B proposed to the node

Working name **UCOPE-UAV-RENEWAL-COMMITMENT-B01**, **B/EXPLORE**, with one
prospective fresh matched training pair (candidate master 7301). The bounded
current UCOPE/source search found no earlier 7301 use across 215 files; this
is not a global RNG census or a scientific allocation. The proposed claim is
that renewable 1/4-step commitments improve complete sampled native return
over ordinary feedback at the fixed real budget. Binding MARL structure is
**(b) temporal abstraction or termination**, in a fixed partially observed,
co-adapting five-UAV team.

Keep the native host, 50 users, 256 one-second steps, reward, action scaling,
local 108 actor inputs and predecision 136 critic inputs of B04. Keep its
67→32→2 conditional duration head and private head initialization, with the
final layer zeroed initially. T/G have 68553/66311 parameters, no additional
parameters over B04. Common actor/critic initialization and separate private
action/reset streams follow the existing law on the fresh master. No new
draw alignment is introduced when T has fewer actual velocity decisions.

At `remaining == 0`, the owning T UAV samples velocity then conditional
duration. It holds that exact command for the selected primitive steps;
after each real environment step its remaining count decrements. At its next
expiry it chooses both again. A UAV already holding gets neither fresh draw
nor fresh actor likelihood. Every UAV still observes and advances recurrence
on every primitive step. There is no learned interruption, deferred teammate
barrier or change to the duration set. G chooses every legal velocity at each
step, with the same observation/history opportunity and real training budget.
H remains same-reset untuned zero velocity and is scored separately.

An option selected near t255 may be administratively truncated by the fixed
256-step horizon. Execute only `min(selected_duration, 256-start)` steps;
retain aggregate selected four-step choices, censored holds and actually
suppressed decisions in the existing counts/summary, without a full renewal
event dump. No post-terminal action, extra reward, bootstrap or carryover
to a new reset is created. A four-step selection near termination cannot
automatically be counted as three suppressed decisions.

Preserve B04's full native undiscounted primitive return-to-go, gamma=1,
predecision critic, scalar advantage normalization, zero explicit entropy
coefficient and agent-compound PPO clipping. At a true renewal the owner's
velocity and duration form one likelihood ratio, with duration conditioned
on the stored detached sampled action. Held rows have no fresh actor credit.
The existing primitive-row denominator and critic rows remain; no extra
decision-normalization multiplier or fabricated held-action sample is added.
Thus elapsed primitive time and its rewards remain explicit despite unequal
decision times; no new semi-Markov discount convention is introduced.

Each learned arm trains 512 complete episodes, 131072 native team steps,
256 two-episode rollouts and 1024 Adam calls at lr 0.0003. Evaluate only each
final checkpoint on 32 sampled matched-reset episodes for T/G/H. Primary is
`mean_e[J_T(e)-J_G(e)]`, with `J=sum_t sum_i native_reward_i,t / 256`.
Keep every T/G/H value, each contrast, signed episodes and conditional
paired-episode SE. Independent training n=1 has no training-population SD.

Proposed absolute **MEI 0.01** retains the current native task scale and
one-percentage-point rationale, not a universal threshold. There is no
upper/tuned same-information headroom record. G/H are reused because the
host, action, information and training budget match; G−H is assessed, not
assumed positive. Above +0.01 would be preliminary favorable package evidence;
inside ±0.01 no demonstrated point gain at that scale; below −0.01 adverse
package evidence. Every outcome ends this one allocation at intake, without
automatic replication, retry, extra H/evaluation or tuning. Those are proposed
reading rules for the new object, not a rewrite of B04 or a frozen card yet.

## 5. Dominant work and decision value

The complete proposed work is **286720 native team steps**:
`2×512×256 + 3×32×256`, **2048 Adam calls**, 512 rollouts, 1120 explicit
episodes/resets, two constructor resets and 96 final evaluations. The existing
1600 t0..4 T/G diagnostic rows need not expand into a full renewal-event dump.
No extra environment/recurrent step, candidate trajectory, ensemble, solver,
checkpoint selection or search is requested.

Duration work does grow materially. T would make 163840–655360 owned duration
decisions during training and 10240–40960 in final evaluation. These are
direct bounds from 64–256 renewals per UAV episode, not predictions of learned
durations. Sampling, stored behavior densities, four PPO recomputations and
final sampling/densities total **1,003,520–4,014,080 head-forward rows**,
**64–256 times B04's duration-head rows**. At 2208 dense multiply-adds per
row this is **2,215,772,160–8,863,088,640 forward multiply-adds**, plus
categorical sampling, activation, backward and optimizer work. T draws
velocity only on renewal; G's 696320 train-plus-final owned velocity draws
remain fixed. No equation here substitutes operation counts for elapsed time.

Per-arm cost remains initialization +131072 native/recurrent steps +1024
updates +8192 final learned-arm steps +publication; G also carries 8192 H
steps. B04's T **137.6704245s**, G including hover **139.2941963s** and whole
**277.51s** are same-loop references. Incremental duration/head seconds are
unknown, so this is not a measured runtime forecast or a claim of a 256-fold
whole-run increase. Proposed caps stay **1800s per complete arm and 3600s
through complete publication/exit**, CPU FP32, one Torch thread, remote-first.
Any selected run needs exact committed source and fresh actual-node physical
and effective memory admission. A cost refusal would reconsider the question
and its necessary work, not install a timing pilot, hidden phase or higher cap.

Added validation is one affected-directory focused suite within 300s and
independent review of asynchronous own-expiry ownership, held-row masks,
terminal truncation and full native primary. Existing unchanged paths are
reused. No standalone smoke, profiling, checkpoint replay or cost experiment
is proposed. Engineering scope §4: **none**; ordinary source/runner budgets
apply. This preparation is not a CM coding assignment. If the node selects
the B, the same CM owns one complete implementation/review/staging/bounded
execution/collection batch under current ROOT_OPERATIONS; DM accepts science
and Root integrates. No chain of per-command Root relays is revived.

The zero-work alternative is serious: ordinary feedback won B04's sampled
mean and broader results do not establish a durable opening benefit. I favor
one comparison narrowly because the reset-only decision never tested using
evolved histories to choose commitment throughout the task, while the native
step/update budget and existing architecture can be retained. This is a
different mechanism opportunity, not a prediction that sparsity caused B04.
An unchanged B04 pair would principally address repeatability of a within-band
negative point, not this event question. An exact policy maximum, exhaustive
counterfactual diagnosis or mechanism attribution arm would ask a stronger,
costlier question. None is a prerequisite to the proposed real performance B.

## 6. Decisions this preparation produces and return

1. **Object / question selection:** options (a) prepare one concrete
   own-expiry renewal versus no-successor question; (b) return no ready
   continuation now; (c) repeat B04 or choose an ungrounded common-learning
   amendment. Recommend and select (a). **Owner-delegated decision
   (unattended, 2026-09-03 instruction): (a).** The source-defined new event
   and verified literature distinction are sufficient to pose the bounded
   investment question, without claiming an observed advantage.
2. **Direction / pending:** options (a) explicitly select the proposed
   renewable-commitment scope and one minimal B; (b) retain no successor to
   the tested opening evidence, with the node stating any narrow family
   disposition. The DM narrowly recommends (a), **close-call**, but neither
   is executed. Only `em:ucope:convergence` or the owner decides this family
   boundary. If the node classifies the change as RECAST, its verdict and
   applicable recast record must be honored; a new name cannot evade it.
   The older retained-policy/root-residual family's PARK is not reopened.

Machine-generated exposure:

`P67_consultation: new_models=0; new_training_pairs=0; new_environment_episodes=0; new_native_steps=0; new_optimizer_steps=0; new_evaluation_episodes=0; new_replay_calls=0; new_profiling_calls=0; new_scientific_invocations=0.`

Current owner review query returned no pending instruction; the owner's
resume is directly applied through P67. There is no new empirical prediction
to score and no valid-result brief to write for this zero-exposure question.
Existing B04 prediction scores and brief remain unchanged. [P2 item 005](../../portfolio/owner/inbox/2026-09-08/20260908-ucope-005.json)
carries the close-call options and full Chinese packet; it is not a wait for
owner approval or an allocation. Neither direction option is auto-applied.

Prepare a new fixed GitHub request on shared `codex/ucope`, using the existing
UCOPE Convergence conversation and substantive Issue 11. The new request has
its own response path and immutable TASK binding; the completed P61 request
and all archives stay untouched. Root receives the exact request ID, full
HANDOFF commit/path, fixed TASK URL and native return target. This DM performs
no Send. After publication, return at a clean boundary for Root→Transport;
the full immutable response returns to this DM for conformity and scientific
intake. No scientific successor exists until that decision and its explicit
card/budget; no independent Portfolio session is contacted.
