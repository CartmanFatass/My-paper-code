Claim to test: one learned common phase for demand-matched joint claims can improve native post-churn service over both greedy joint assignment and attained independent nearest service at a finite training budget.
Binding MARL structure: agent-count change; a population-sized joint decision couples agents' claims when membership and physical demand change.

# RCLE joint quota phase — one B proposal from documentary L

**Propose one distinct B/EXPLORE candidate, not a selected or funded experiment.**
At each ordinary claim clock, a small learned common controller selects one
cyclic alignment between the current physical-agent order and the demanded
beacon positions. Every agent then makes its corresponding ordinary target
claim. The joint action is demand-matched, but actual travel and coverage still
determine reward. The question is whether learning this joint choice improves
service beyond an obvious legal greedy choice and the attained nearest rule.

The selected [Portfolio L mapping](../../portfolio/pro_packets/20260912_cluster_entity_investment/EXECUTION_MAPPING.md)
buys this design and complete return only. The tested
equal-unit/.99-prior/FLEX/final1000 spending **HOLD** remains. RCLE remains
**ACTIVE/MEDIUM**. This candidate changes the joint action generator, learned
state, score law and optimizer; it is not another seed, coefficient change,
renamed FLEX fit or reopening of a historical frozen C object. Future
direction-tier selection and investment return through Root. No Pro, source
implementation, model/RNG, numerical reanalysis, test or experiment runs under L.

## 1. What the observation would decide

The proposed use is a small common allocator for the existing rotating-perimeter
service host, when agents may share its public coordination signal at each
four-tick claim opportunity. It would be an optional service controller beside
attained INDEPENDENT-NEAREST. The next observation decides whether its **learned
choice** is worth further development over fixed public-state dispatch rules.

Existing evidence supplies both reasons and warnings. [B07's complete intake](RCLE_B07_EQUAL_UNIT_INTAKE_20260912.md)
records the attained-reference contrast -0.008841959635417, with both primary paths/all eight U
cells negative, and G_U=-0.000205485026042 supplies no positive aggregate learning
gain. Those facts support its narrow spending hold, not general unlearnability.
Earlier W100/W1 native learning and surviving local B06/B07 gains show that
learned joint behavior can affect this host's service. However, early service
gains occurred alongside all-cell fragmentation harm, and B07 has favorable
recovery observations alongside adverse U/F/tau cells. **Lower claim shortfall
is not a sufficient reason to expect lower physical unmet demand.**

This proposal directly tests the corresponding uncertainty: an explicit joint
allocation rule removes independent claim-count mismatch, yet may send agents
farther, disrupt a useful physical arrangement or restrict needed temporary
over-allocation. The competent greedy joint null prevents crediting learning
for whatever benefit the hand-specified allocation structure supplies. Nearest
prevents choosing a weak new null after seeing its outcome. No exact optimum,
fragmentation census, old gradient cause or positive pilot precedes this B.

## 2. Exact public joint decision

Retain the native 120-sector world, six moving beacons, H=64, tick24 event,
four-tick claim clocks, MOVE-TO-CLAIM dynamics, demand and exogenous law. The
existing target definition has integer demands d_j>=1 and sum_j d_j=N.
This is an existing task fact, not a new capacity constraint on the environment.

At one claim clock, order **current physical agents** by the native public
clockwise rank, including its existing entry tie-break. Let r_i range from
0 to N-1. Make a length-N list b by writing beacon0 d_0 times, then beacon1
d_1 times, through beacon5. Candidate action s is a cyclic phase, 0<=s<N:

    a_i(s) = b[(r_i+s) mod N].

The common controller samples **one** s for the entire team. Agents execute
these target claims simultaneously, before the ordinary primitive movement.
The environment still permits all six target actions for each agent. This new
controller deliberately expresses only N correlated joint allocations from that
legal space; it does not change legality, reject an environment action, add a
shield or edit the old card. It trades flexibility for a finite coordination
inductive bias. Historical public-plan containment and FLEX evidence remain;
there is no claim that this class is more expressive or that persistent private
state is necessary.

By construction the selected claims have exactly d_j entries for each beacon.
Thus the **claim-count definition** of F should be zero for this controller
and its greedy joint null when implemented correctly. This is a design identity,
not measured recovery, optimality, an extra reward or an empirical success
criterion. Proximity c_j and unmet demand u_t are still computed from actual
post-movement positions; agents can travel badly even with matched claim counts.

### Entity, lifetime and information path

Tick24 first applies departures/arrivals and the declared epoch change, then
the new public state is used by this clock's common choice. Departures produce
no action row. Newcomers receive their native physical state/newcomer pulse and
their new current rank; survivor positions and previous physical motion remain
owned by the same physical entities. Rank is recomputed and never becomes a
learned identity embedding or persistent roster slot. A claim belongs to that
physical entity for its four primitive ticks. All claims are replaced at the
next claim clock; the host's membership boundary is itself a claim clock.

There is no policy memory, FLEX plan, per-agent learned hidden state or carry
across a rank change. NEW_EPOCH and ACTIVE_CONTINUATION retain their actual
different physical laws. No rejoin/replacement process is added to this host;
future such tasks would need their own object. No scenario is discarded for
poor recovery, co-location, missing apparent commitment or adverse service.

The common controller consumes only the **existing public sets** already used
by the native manager: positions/newcomer flags, beacon positions/demands, N,
time and the current event flags. It receives no agent ID, future event draw,
private noise, target result or privileged critic state. Execution agents need
only their legal own rank, current demands and the one common phase. Ordinary
public processing is shared; no previous agent's sampled action is secretly
fed to another actor.

This is an explicit change in coordination frequency: one common phase at each
of 16 claim clocks per episode, instead of the held method's epoch/FLEX plan.
For the registered N<=12 it is a choice with at most four bits of label payload,
not a measured network cost. Both learned and greedy joint methods use the same
ideal public-state/common-dispatch facility. Nearest needs no phase message.
No equal-communication, decentralized-without-communication, deployment or
hardware latency claim is proposed.

## 3. One real learner, fixed before outcomes

For candidate phase s and agent rank r, encode these eight legal features:
sin/cos current position; sin/cos its assigned beacon position; assigned
demand/2; signed circular distance to that beacon/60; r/max(N-1,1); newcomer.
A shared 8→32→32 tanh MLP encodes the assignment rows. Mean-pool the N rows,
append N/12, t/64, roster_event and new_epoch, and apply a shared 36→32→1
tanh-hidden scoring head. A softmax across the current N scores defines the
phase law. There are no phase-, roster-size-, entity- or beacon-specific learned
heads. Tool-computed parameter count including biases: **2,561**.

Initialize ordinary affine layers from the existing fresh fan-in uniform rule;
zero only the final scalar score layer so the initial phase law is uniform.
Use one freshly constructed model and its own optimizer, not the old seven-
allocation FLEX initializer or any retained checkpoint. One phase draw per
team/clock is scored once and its deterministic action mapping is used unchanged.
Independent per-agent draws of s would be a different, incorrect candidate.

Train online from the same dense native full-episode reward
Y=1-sum_t u_t/64, with no F reward, teacher, imitation labels, critic, search
target, entropy term or altered termination. For episode e, S_e is the sum
of its 16 sampled phase log probabilities. Use stopped per-cell baselines:

    A_e = stop(Y_e - baseline_cell(e))
    loss = -mean_e(A_e * S_e).

One Adam step follows each 64-episode block: learning rate3e-4,
betas(.9,.999), epsilon1e-8, no weight decay or gradient clipping. Then update
each cell baseline in the order .95*b+(1-.95)*cell_mean_Y, starting at zero.
Reject nonfinite loss/gradient before mutation. The Adam epsilon is its ordinary
optimizer definition; no unit-vector manager/claim normalization, factor100,
second derivative, fixed-norm step or near-cancellation procedure is reused.
This is a new whole learning package, not a component-causal comparison to B07.

Propose **256 nonzero-exposure update opportunities**, 64 episodes each: eight
episodes in each of the existing eight 6/10 training cells. The chosen final
endpoint is update256; no best checkpoint, training-until-positive, seed screen
or conditional extension. Every episode is native. Dense reward supplies a
direct training signal for a small one-choice-per-clock controller. This
16,384-episode starting budget is a credible bounded learning observation, not
a proof that 256 updates suffice. It is not inherited final1000 or a design
search to find an adequate number. A negative finite result keeps that limit.

## 4. Competent nulls, estimands and own interest scale

Use exactly four endpoint roles, each on the same 8 held-out 8/12 cells×64
fresh exogenous scenarios, balanced over the two event modes:

| Role | Purpose and law |
| --- | --- |
| Learned phase, initialization | Evaluate before learning; distinguishes its initial joint restriction from actual improvement. |
| Learned phase, final256 | The one preselected candidate endpoint; sampled common phase as in training. |
| GREEDY-QUOTA-PHASE | Same current ranked joint mappings; choose the phase minimizing sum_i absolute circular distance from x_i to its assigned current beacon; exact ties choose the smallest phase. No model, training, lookahead rollout or later service information. |
| INDEPENDENT-NEAREST | The existing attained native nearest rule, including its tie law; do not replace it with a weakened approximation. |

Greedy is the obvious same-information **algorithmic null for learning the
joint choice**, with its complete candidate/dispatch cost exposed. Its service
has not been measured, so it is not falsely called an attained benchmark.
Nearest supplies that attained competence. Both contrasts are retained; no
post-result selection of the easier comparator. No matching tuned generic
baseline/upper headroom record exists for this new policy interface. Historical
nearest deficits are context, not upper-minus-tuned-baseline headroom or a reason
to block B. No new generic baseline training or oracle retuning is purchased.

Two separate primaries equally weight ACTIVE_CONTINUATION8→12 and12→8:

    D_g = mean_primary(U_greedy - U_final256)
    D_n = mean_primary(U_nearest - U_final256).

Positive favors the learned controller. Also retain G_U=mean_primary
(U_init-U_final256), each path and every cell's U/F/failure-coded tau/40U, learned
Y, absolute endpoint means, curves and actual updates/parameter movement.
Reference Y is not inferred from post-event U where the existing wrapper leaves
it unavailable. Tau40 remains a failure code; it is not an uncensored recovery
time. The all-claim F identity never substitutes for native U or recovery.

**Own MEI: absolute .025 U for each primary**, one normalized unmet-demand tick
over the 40 post-event ticks. That is a concrete service increment worth
examining for this optional dispatch use; it neither presumes cheap execution
nor imports B07's .05. No relative threshold near zero, F/U exchange rate or
equivalence margin is introduced. Conditional precision is unknown at64 scenarios
per cell; it is reported rather than certified by a new power or pilot study.

The independent learning unit is **one fresh fit**, n=1. Share only declared
exogenous scenario addresses between roles; each follows its own physical
trajectory. Initial/final phase uniforms may be paired by the actual protocol;
the deterministic nulls consume no policy uniforms. Use paired scenario
differences only where that coupling is maintained, with conditional dispersion/
SE and every sign. Episodes, cells, checkpoints and historical B03/B06/B07 fits
are not independent repeats of this candidate. No training-population or
larger-N scalability claim follows.

### How the result would change the proposed use

| Observation | Bounded interpretation and recommendation for a later decision |
| --- | --- |
| D_g>=.025 and D_n>=.025, with G_U>0 | Useful one-fit learned-service signal beyond both rules; consider further development/one independent observation only via a later explicit allocation. Retain native harms and real cost. |
| Both contrasts positive, but at least one below .025 | Small observed benefits, with exact sizes, uncertainty and cost; no stable-superiority or automatic continuation claim. |
| Beats nearest but D_g<=0 | The learned choice adds no observed benefit over the obvious coordinated null. Prefer that null on this observed comparison; do not attribute the structural allocator's gain to learning. |
| D_g>0 but D_n<=0 | Local improvement over greedy remains, yet the attained service deficit survives; the proposed learned optional-service use is not supported against nearest here. |
| D_g<=0 and D_n<=0 | No observed endpoint service advantage over either rule. Retain the nulls for this observed use and the finite-training limitation; do not infer whole-direction failure. |
| G_U<=0 or paths/native consequences disagree | Report initial-policy benefit separately and mixed service/recovery facts. No post-hoc endpoint, weighting or scalar tradeoff. |
| Actual information/reward/action-likelihood/primary defect | Limit the affected comparison, retaining independently trustworthy facts and actual work; no dependent polarity or replacement fit. |

These rules describe the proposed B's use question, not a universal positive-
first law. A negative observation does not close RCLE or prove that correlation,
learning or demand matching can never help. No F-positive, recovery-success,
headroom or diagnosis prerequisite is created.

## 5. Finite work and complete future investment request

[WORK_AND_SCOPE.json](l_design_20260912/WORK_AND_SCOPE.json) uses static arithmetic
from this proposal, not a model, simulation or reduction of old outcomes.

| Work | Proposed count / reason |
| --- | --- |
| Training | 1 fit;256×64=16,384 episodes;512 native rollout batches of32;256 Adam steps/one score-gradient traversal per block. |
| Endpoint evaluation | 4×8×64=2,048 episodes; initial/final plus both deterministic nulls. |
| Complete native episodes/ticks | 18,432 episodes /1,179,648 H64 ticks. No extra timing, count, pilot or diagnostic panel. |
| Learned phase draws | 262,144 training and16,384 initial/final; one team draw per clock. |
| Phase-score heads | 2,097,152 training and163,840 initial/final; N choices per clock. |
| Assignment-element encodings | 17,825,792 training and1,703,936 initial/final; N choices×N assignment rows per clock. |
| New greedy null distance rows | 851,968; same N cyclic choices×N direct distances. Nearest uses491,520 six-candidate distance comparisons. |

Balanced training populations have mean N=8 and mean N²=68; evaluation means
are10 and104. The intrinsic learned representation is **O(N²) per claim clock**,
not the held actor's six-candidate-per-agent work. State this growth without
claiming improved scaling, cheapness from fewer parameters, or parallel speedup.
N cyclic actions are the actual policy choices and greedy null's ordinary action
selection. There is no 6^N joint-action enumeration, permutation search,
trajectory tree, solver, best-of-many policy search or search-before-learning
prerequisite. The null performs no prospective native simulation.

**Request for a possible later investment, not an allocation:** one complete
native logical invocation up to900 s, including all four roles; all additional
future invoked support up to900 s; complete invoked work up to1,800 s. These are
new willingness-to-spend ceilings under unknown rates. They are not estimated
runtime, B07's old900 balance or a price inferred from343.43 s. The full
documentary/provider/agent bill is also unknown and must be explicit in the
future investment decision, including any newly selected node question.

The native chain includes enclosed adjacent admission, startup/import/construction,
all learning and panels, checkpoint/required endpoint publication/readback and
exit. Additional support includes final card/identity/source work, necessary
build/staging, focused checks, independent review, Git/Monitor coordination,
collection/reduction/intake, Root integration, retention and assigned cleanup;
required shared work is charged once, not excluded as an outer tail. No prior
known support window, K/E/U funding or current documentary L pays for it.

The known multiplicative work is above; actual CPU rate, peak graph memory,
adapter implementation time and complete support coverage are unmeasured.
No reliable end-to-end projection exists. A later known cap violation would
require a new design/budget decision; unknown rate alone does not commission
a profiling or calibration object. No automatic second fit, retry, exposure
shortening or free publication/cleanup tail is requested.

## 6. Future engineering L0, without implementation now

Proposed future ownership remains this DM/shared checkout, with new
`experiments/candidates/roster_consistent_latent_exploration/joint_quota_phase/`
policy/study helpers, one thin `scripts/run_rcle_joint_quota_phase.py`
entry and corresponding focused tests. Reuse the accepted TBCFV native environment,
public snapshot/entity ordering and batch interface in
`experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_runner.py`
and `native_backend.py`. Add only the scoped joint-decision adapter needed to pass
one phase's mapped physical-agent actions. Do not reuse the held equal-unit update,
FLEX helper constructor or its final1000 invocation. No such source file is added
by this design.

Future checks should falsify the changed contracts: variable roster/rank/action-row
ownership at the event; one shared phase and sampled-phase log probability;
deterministic mapping/greedy tie behavior; graph/baseline/optimizer ordering;
unaltered native Y/U/F/tau and complete four-role primary publication. Preserve
the previous reference-column failure as history; check any actual new dependency,
without requiring its full writer reconstruction. Independent high-risk review
is justified by joint action/likelihood, information and population-row changes.
No universal full-model smoke, all-history replay or separate numerical study.

Propose remote-first Linux CPU FP64, one compute thread, exact published source
and committed command, destination-adjacent physical/effective available memory
at least4 GiB, detached supervisor and actual Monitor goal adoption through the
live primary-control configuration. No source, command, seed, remote root,
admission, code acceptance or launch identity is established now. Ordinary
research-code/runner/test budgets apply; Engineering Scope §4 machinery: **none**.
Unmet future implementation/admission constraints produce their actual bounded
technical return, not scientific polarity or an automatic replacement invocation.

## 7. Reading basis, limits and selection need

Current empirical sources are the [post-B07 intake](RCLE_POST_B07_CONVERGENCE_INTAKE_20260912.md),
its B06/B07 references and the [retained early native-learning comparison](RCLE_SERVICE_COMPARISON_DESIGN_INTAKE_20260910.md).
The host laws above come from the [original target card](RCLE_TARGET_BOUND_COMMITMENT_FRAGMENTATION_VALUE_SCIENCE_CARD.md)'s
task/roster/action/public-information/endpoints sections, not its
historical frozen C burden or budgets. The proposed B explicitly changes the
controller class while retaining the native task and its unrestricted legality.

Scientific reading reuses Foundations §§3–4,6 and reads 02_MARL on legal shared
information and coordination. Concrete assumption: a public common decision may
couple legal actions without carrying privileged state. Its availability/frequency
must be declared; it is not equivalent to independent local action sampling or
evidence for a no-communication Dec-POMDP. Conditional evaluation still does not
replace independent training or identify a component effect.

Question-driven local retrieval read My-lib's registry/collection guidance and
excluded synthetic fixtures; no verified real collection was established in
that limited read. The available Inst-sci formal catalog returned relevant
joint-policy pointers. The verified primary passage is Zhou et al., *Cooperative
Policy Agreement: Learning Diverse Policy for Offline MARL* (AAAI2025),
[official source](https://ojs.aaai.org/index.php/AAAI/article/view/34465), local
`MARL-0069.json` pp1–3/elements87,95,96,152. It distinguishes a compatible joint
choice from independently mixing components of different choices; its method
uses offline autoregression and subsequent policy agreement. **We adopt neither
that method nor its performance claim.** The design consequence is only to draw
one common phase, score that draw and declare the coordination facility. The
online, public-state, restricted-phase host differs. No novelty or corpus-wide
absence claim is made. [LITERATURE_SCOPE.json](l_design_20260912/LITERATURE_SCOPE.json)
preserves identity, source digests, actual passages and these limits.

Recommend submitting this **one** candidate for a direction-tier family/use
selection and the complete new investment decision through Root's existing
route. The alternative is a concrete no-candidate return if the bounded
coordination-use question is not worth the declared new work; it would not
automatically PARK RCLE. L itself is complete at this proposal/intake/publication.
No candidate is silently accepted, no current held recipe is reopened, and no
consultation or numerical work is automatically dispatched.
