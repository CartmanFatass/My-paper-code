Proposed claim: sampled opportunity-return credit may let a finite-budget recurrent currentness policy improve native return beyond same-information RAW recurrence.
Binding structure: systems / information flow.

# CBSC opportunity-credit question: design intake, not a selected card

Date: 2026-09-06 PDT. Status: direction-family question for the existing
Convergence node. No successor is selected, no science card is frozen, and
this preparation adds zero environment, learner or evaluation executions.
The host has one learning controller and two receiver entities; this toy
does not itself measure multi-agent learning or other-agent non-stationarity.
Its history-dependent public currentness is an information-flow inspiration
for those settings, not evidence of transfer to them.

## Authority and what was checked

Root's owner-resume record is
`docs/research/portfolio/decisions/2026-09-06-resume-codex-after-claude-handoff.md`
at `06e3993068d4b5126ccc3cb957f7a582d00234da`. It lifts the scheduling stop
and commissions this next-question preparation; it does not select a successor.
The Portfolio CBSC row remains ACTIVE/HIGH; Root owns that shared snapshot.
This work uses an isolated branch and does not edit another direction or source.
At entry, owner-console `reviews --json` returned `[]`; no reply is invented.

I read the current family intake, the current DIRECTION sections, B02's card,
B03 result evidence and existing run analyses, and the complete prior Pro
response at `pro_packets/20260905_two_seed_family_convergence/archive/RESPONSE.md`
(original delivery `e4cacaccf3e03a6944c9653abeb5e645e46109ec`). Its rule is:

> 最终选择：暂停当前不变的 48 更新 RAW/STRUCT 直接回报比较家族，不再购买第三组同协议训练；本轮也不选择所提 192 更新备选或其他新实验。

I retain that rule. Its next-question boundary permits a specifically justified
symmetric training change, without selecting an entropy value, GAE change or seed.
Evidence-spec §§4, 5.2, 11.4 and 11.7–11.9 govern this proposed B question.
No unique-cause diagnosis, exact upper, support census or prior positive result
is necessary to pose it. Convergence is deciding whether to open a distinct
family after its scoped pause; this is not a new routine B launch gate.

## Observed evidence and the newly useful distinction

B02/21203 and B03/21209 are two independent paired runs, not 64 trained pairs.
At update 48 their respective RAW = STRUCT means are 10.7125 and 10.5875,
with all 32 within-run differences zero. Every trained greedy evaluation
checkpoint chose REFRESH throughout. Each formal arm completed 48 rollouts,
768 Adam steps and nonzero parameter displacement. B03 sampled other training
actions but ended heavily concentrated on REFRESH. This is a behavior plateau,
not proof that exploration was absent or that GAE caused it.

Source inspection establishes a more specific opportunity for a new question:

- `omrc_b01/host.py::build_stochastic` (lines 539–595) constructs every public
  event and state before policy actions. `ledger.py::apply_native_action`
  returns the same state; REFRESH is nonpersistent. There is no action-dependent
  cache repair or later context distribution in this host.
- `engine.py::_rollout_from_panel` (lines 220–268) feeds the public observation
  sequence through the recurrent model before sampling actions. Only each chosen
  action's ledger supplies training rewards, at rows `12+6*q` and `13+6*q`.
  Neither actions nor rewards are fed into later recurrent inputs.
- `ppo.py::compute_gae` (lines 201–233) carries primitive-time TD residuals
  across later opportunities with gamma 1 and lambda 0.95. Actor advantages
  are already normalized only over decisions: there is no discovered all-token
  normalization bug. `_train_minibatch` fits values over all 152 primitive rows.

The resulting hypothesis is that an unnecessary return-prediction horizon and
its shared critic loss may make local context-sensitive choices harder to learn
at this budget. This is an inference, not a measured gradient-variance result,
bug classification or unique explanation of the old zeros. Exact model-based
diagnosis would not answer whether a simpler sampled target improves learning.

A competent cheap null is missing from the earlier displayed context: use the
public `request_active` flag, REFRESH when active and SAFE_FALLBACK otherwise.
Call it REQUEST_ONLY. It needs no owner/epoch history, validity or teacher.
The native ledger implies `R_refresh = active_count - 9.6` and
`R_request_only = 0.6 * active_count` for a 24-opportunity episode.
The existing panel means therefore imply REQUEST_ONLY means 12.1875 (B02)
and 12.1125 (B03), respectively 1.475 and 1.525 above their all-REFRESH policies.
These are newly labelled, outcome-informed arithmetic consequences of existing
means and the fixed reward law, cross-checked against ALWAYS_SAFE, not new
policy evaluations, tuned headroom, or empirical training results. The machine
derivation is in this round's `EXPOSURE_AND_COST.json`.

This matters to interpretation: merely learning the public active flag could
raise return substantially without learning currentness. Preserve REQUEST_ONLY
alongside the strongest trained containing null, full-public-history RAW-GRU.

## Question-driven source retrieval and what it changes

Question: is the credit estimator's time unit an algorithmically meaningful
choice here, and would local sampled rewards retain a fair learning comparison?

The inspected My-lib tracked registry contains two synthetic fixtures; its
default page index reports zero indexed papers/pages. Those are not real
scientific coverage and were excluded. No verified alternative real-collection
index was exposed by its README/collection entry points. I did not import or
rebuild a library. Inst-sci's formal `llm-index/catalog.v2.jsonl` has 190 rows in
this snapshot. Bounded metadata searches found one advantage-estimation match,
one contextual-bandit match, one temporal-credit match and no variance-reduction
or reward-redistribution match. These counts describe that searched snapshot,
not completeness of either library or absence of relevant prior work.

The relevant local match is Jung et al., *Agent-Centric Actor-Critic for
Asynchronous Multi-Agent Reinforcement Learning*, ICML 2025, MARL-0449.
I checked metadata and source JSON page 5 §3.4, elements 623–625, and the
adjacent page 6 discussion. Source:
`C:/Projects/Inst-sci/papers/MyLib/json/MARL-0449.json`; corresponding PDF
digest `f62052093281b72c2137e20a586f8eb964b54601aafd0b8e91ec922297e197f3`.
The paper changes the clock of lambda discounting for asynchronous macro-actions.
It supports considering the action opportunity when choosing a credit estimator;
it does not establish CBSC's cause or the efficacy of this proposal. Here all
opportunities have fixed duration and there is only one learner, so I do not
copy ACAC's architecture, PopArt, multi-agent claims or variable-duration argument.
[Official paper record](https://proceedings.mlr.press/v267/jung25a.html).

The original GAE paper was absent from the matched local metadata. I therefore
read Schulman et al., *High-Dimensional Continuous Control Using Generalized
Advantage Estimation*, arXiv:1506.02438v6, §§2–3, especially equations 1 and
11–16 and the baseline condition around Proposition 1. GAE trades value-error
bias against sampled-return variance; it is not intrinsically a defect. The
paper's setting is continuous-control sequential dynamics, so it does not
promise improvement on CBSC. Combined with this host's action-independent
history, it motivates trying a local reward baseline rather than sweeping
lambda or increasing rollout length. [Primary source](https://arxiv.org/pdf/1506.02438v6).

The host-specific inference is modest: for a fixed policy, later histories and
action distributions do not depend on this action. Its later reward terms add
no expected score-function credit for this action. Using only its own native
decision plus settlement reward is therefore a plausible target choice for
the same episode-return objective. PPO clipping, normalization, shared recurrent
optimization and finite data still prevent a theorem or performance guarantee.
The proposal changes the estimator, not the reward or what the actor observes.

## Concrete preferred B04 design for Convergence selection

Provisional object name: `CBSC-OPPORTUNITY-CREDIT-B04`.
Question: under a sampled opportunity-return actor/critic target, does STRUCT
beat same-information RAW at the fixed 48-update native-return endpoint, and
do the resulting policies improve beyond the public-request-only null?
This is outcome-informed B/EXPLORE, not confirmation of an earlier prediction.

Change one coherent training component in both arms: the credit target and
its matching value regression. For decision row `t=12+6*q`, let
`G_q = rewards[t] + rewards[t+1]` from the one sampled action, and
`A_q = G_q - stop_gradient(old_value[t])`. Normalize these 192 decision
advantages across each eight-episode rollout as before. Use the same clipped
PPO actor loss. Fit the scalar value head to `G_q` only on decision rows; no
value loss on forced-WAIT positions. Keep the complete 152-token recurrent
unroll and full BPTT, so earlier public events can still shape current action
features. No cross-opportunity TD bootstrap enters these targets. This is a
new sampled-credit learner package, not an invocation of unchanged B01 GAE.
It changes both target horizon and the matching critic supervision; a result
will not isolate those two contributions.

Preserve the host, event law, observation/action/mask semantics, existing RAW
FIFO and STRUCT adapters, 121,349-parameter model, FP32 CPU, initialization,
optimizer settings, full-episode minibatches, 4 epochs × 4 minibatches, entropy
0.01 and clipping 0.20. No auxiliary semantic label, full-Q target, imitation,
reward-derived input, teacher, architecture search or arm-specific tuning.
Both arms receive the same public primitive history; all STRUCT outputs remain
a deterministic function of it. RAW is the containing learned comparator, not
an already tuned optimum. No PI/DERANGED or generic-conditioning exclusion is
claimed, so no four-arm mechanism study is added by default.

Propose one fresh paired run, seed **21217**, using the existing B1_RUN RNG
namespace with that new seed and fresh outer object/output identity. Train
48 × 8 fresh episodes per arm, IDs 0–383, with 768 actual Adam steps.
Use the same 32 EVAL_STOCHASTIC roots at updates **0 and 48**, greedy and
adaptation-free, reset recurrence per episode. There is one independent
training pair; repeated checkpoints/episodes are not independent learners.
Do not alter old B02/B03 source behavior or mislabel new target/checkpoint
semantics as the frozen B01 learner. Exact reuse details belong to CM after
selection, with truthful new-object metadata and existing outputs read-only.

Primary: mean of all 32 `STRUCT - RAW` native episode returns at update 48.
Retain both absolute returns, all paired differences, the two fixed checkpoints,
sampled training-action counts and evaluation actions. During RAW's complete
invocation, score ALWAYS_REFRESH, ALWAYS_SAFE and REQUEST_ONLY once on the same
32 tapes. REQUEST_ONLY reads only the public decision flag when choosing an
action; the evaluator then scores that chosen action. It supplies no learner
label and performs no search. Publish each learned arm's paired excess over
REQUEST_ONLY as predeclared context; do not turn it into a launch/validity gate.
No old-learner same-seed arm is bought: this question compares representations
within the new learning package, not a causal effect of replacing GAE.

MEI: **0.25 native episode return**, retained for comparability with the old
budget's practical decision scale (about 1.04% of the maximum 24, not a fraction
of measured headroom). Report every signed effect. A STRUCT advantage above
MEI with credible native performance can justify one or two independent seeds;
these are not pre-authorized. If the gain only closes REQUEST_ONLY's gap, call
it learning the public-request distinction, not currentness value. Inside MEI
or opposite-sign results remain local null/adverse observations at this package
and budget. Both arms improving over REQUEST_ONLY without a representation gap
supports a generic-learning explanation. Unchanged returns or merely more SERVE,
entropy or parameter motion supplies no performance value. No all-seeds-positive
condition, population equivalence or unique-cause conclusion is available.

Provisional DM prediction: weakly expect better public-request handling but a
STRUCT-minus-RAW gap inside MEI; little source evidence establishes that local
credit will unlock owner/epoch conditioning. This is a design expectation,
not a frozen ladder prediction. Owner prediction: not taken (unattended).
Matched tuned-generic/upper headroom remains absent; the exact older host and
LR01 do not match this online observation/action/budget package. REQUEST_ONLY
is a cheap same-information reference, not a tuned upper or full headroom record.

## Dominant work, execution and source implications

Algorithm work: 2 arms × 1 seed × 48 rollouts × 8 episodes, plus
2 × 1 × 2 checkpoints × 32 evaluations; optimizer work is 2 × 48 × 4 × 4.
Each episode has 152 primitive transitions and 24 decisions. Per arm: 384
training episodes, 58,368 training transitions, 9,216 sampled decisions,
768 Adam steps and 64 evaluation executions/9,728 evaluation transitions.
Pair total: **136,192 transitions and 1,536 Adam steps**. The three context
rules add 96 existing-tape ledger scoring passes/2,304 action scores, once
in RAW, with zero extra learners or generated evaluation worlds. No nested
candidate, trajectory or controller search is proposed.

Proposed full cap remains **600 seconds per arm**, at most two formal calls,
including admission/startup, host, training, evaluations, checkpoint/output
writing and readback, pair publication in STRUCT and termination grace. The
old complete walls are B02 79.69/90.78 s and B03 59.53/58.67 s. Reusing the
corresponding B03 complete walls is only a reference scenario; charging twice
the larger old same-arm wall gives 159.38/181.56 s as a conservative planning
scenario, not a guarantee. New target implementation cost is unmeasured.
No calibration experiment or assumed acceleration justifies this question.

Portable execution follows the current `.codex/hmasd-compute.toml` remote-first
route. Propose wsl_4070, `/home/wu/.venvs/hmasd/bin/python`, CPU FP32 and one
Torch compute thread, with exact committed source, detached agent-task, fresh
4 GiB physical/effective memory admission, and independent monitor handoff.
No GPU or parallelism change is part of the estimand or selected here.

After selection, source work can be bounded to a new research module/runner
reusing the existing public projection, real rollout and direct evaluator path.
The changed target, decision-only value loss, sampled-only rewards and published
native primary need one focused integration check and independent scientific
code review. Existing currentness/ledger tests can be reused; the new test must
also catch a dropped REFRESH settlement and a future-opportunity reward leaking
into the local target. No broad replay or repeated per-launch smoke is needed.
Propose engineering seed 21211, one 8-episode update per arm and one eval tape
at updates 0/1: separately charged 32 Adam steps and 3,040 learned transitions.
Pure constructed reward-array checks add no simulation. The current focused
account is **132.15/300 s**, so the proposed complete focused check including
grace is at most 60 s, charged to that same account; no allowance is reset.
This is proposed coverage/cap, not completed acceptance or permission to run it.

Engineering-scope §4 needs: **none**. Reuse existing learner snapshots without
new resume/recovery orchestration. No registry, generic trainer factory, guard,
worker pool, profiler or old publication system. Ordinary 2,000 new source
lines/600 runner lines and proportionate tests remain; the old B1 repair
exception does not transfer. Stop on a primary dependency/coverage gap or
complete cap; retain partial facts without silently changing reward, target,
information or budget. No automatic retry, extra seed or expanded search.

Machine exposure line and count derivation: this round's
`pro_packets/20260906_opportunity_credit_convergence/EXPOSURE_AND_COST.json`.
Existing four formal arms demonstrably moved 18.68%–20.33% of initial L2 after
768 Adam steps. That supports the available budget's ability to move weights;
it does not predict this changed learner's movement or native value. Current
consultation has zero new optimizer, environment or evaluator calls.

## Decisions this intake produces

1. **Direction/family, escalated, not executed.** Options: (a) open the concrete
   opportunity-credit B04 question above; (b) retain the family pause and select
   no new experiment; (c) select a different specifically justified bounded
   learning change. DM recommends (a). It has source-grounded leverage on an
   avoidable prediction horizon and a stronger cheap public-information null,
   while preserving the original currentness-versus-RAW question. Runner-up
   (b) remains credible because the two zeros and easy request-only gains may
   indicate little currentness-learning value here. Only a complete conforming
   decision at the existing Convergence node will select what follows. No
   recast, lifecycle, priority, or Portfolio disposition is locally executed.
2. **Technical preparation, OWNER_DIRECT.** Publish this question, source/ledger
   reasoning, counts, Issue snapshot and scoped GitHub TASK; dispatch once
   through the configured singleton. This executes the owner-resume assignment,
   not a delegated experiment selection. Reuse the current post-cutover
   Convergence conversation; no historical resend or replacement transport.
3. **Owner/Root boundary.** Preserve zero-pair evidence, old B1/r05 quarantine,
   original unresolved SIGSEGV/TypeError causes, and the missing tuned headroom.
   Return the pushed packet and zero-new-exposure facts to Root. If selection
   remains pending, stop at a recoverable committed boundary. The existing
   direction item can carry the accompanying Chinese packet; no owner reply
   is required to send the authorized research question.

Strongest support: verified nonpersistent action/reward structure makes a
shorter sampled-credit target a concrete learning alternative to dose/seed
repetition. Strongest contradiction: two trained zero gaps plus the possibility
that any new improvement merely learns the already-public active flag.
Next discriminator, if selected: fixed-endpoint native performance against RAW
and REQUEST_ONLY under the declared local-credit learner, with all outcomes kept.
